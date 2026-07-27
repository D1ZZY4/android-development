#!/usr/bin/env python3
"""Resolve Android SELinux policy inputs from BoardConfig-style makefiles.

The Android build tells you where policy comes from through Make variables such as
BOARD_VENDOR_SEPOLICY_DIRS, SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS, and included makefiles.
This tool follows BoardConfig.mk/include chains first, expands simple make variables,
and prints the policy source map before any broader repo-wide scan is attempted.

It intentionally does not execute shell commands or arbitrary make. It performs a
safe static approximation that is good enough for device-tree triage and build-log
repair planning.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

LINE_CONT_RE = re.compile(r"\\\s*$")
ASSIGN_RE = re.compile(r"^([A-Za-z0-9_.$(){}-]+)\s*(:=|\+=|\?=|=)\s*(.*)$")
INCLUDE_RE = re.compile(r"^-?include\s+(.+)$")
INHERIT_RE = re.compile(r"^\$\(call\s+inherit-product(?:-if-exists)?\s*,\s*([^,)]+)\)")
VAR_RE = re.compile(r"\$\(([^()]+)\)|\$\{([^{}]+)\}")

SEPOLICY_VARS = {
    "BOARD_VENDOR_SEPOLICY_DIRS": "vendor policy dirs",
    "BOARD_ODM_SEPOLICY_DIRS": "odm policy dirs",
    "BOARD_PRODUCT_SEPOLICY_DIRS": "product policy dirs (legacy/variant)",
    "BOARD_SYSTEM_EXT_SEPOLICY_DIRS": "system_ext policy dirs (legacy/variant)",
    "SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS": "system_ext public policy dirs",
    "SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS": "system_ext private policy dirs",
    "PRODUCT_PUBLIC_SEPOLICY_DIRS": "product public policy dirs",
    "PRODUCT_PRIVATE_SEPOLICY_DIRS": "product private policy dirs",
    "BOARD_SEPOLICY_DIRS": "legacy extra policy dirs; vendor-only on Android 8+",
    "BOARD_PLAT_PUBLIC_SEPOLICY_DIR": "deprecated platform public override",
    "BOARD_PLAT_PRIVATE_SEPOLICY_DIR": "deprecated platform private override",
    "BOARD_PLAT_PUBLIC_SEPOLICY_DIRS": "deprecated platform public dirs",
    "BOARD_PLAT_PRIVATE_SEPOLICY_DIRS": "deprecated platform private dirs",
    "BOARD_REQD_MASK_POLICY": "required policy mask override",
    "BOARD_SEPOLICY_M4DEFS": "policy m4 definitions",
}

CORE_POLICY_DIRS = {
    "system/sepolicy/public": "AOSP/ROM exported platform policy API for vendor use",
    "system/sepolicy/private": "AOSP/ROM private platform policy; vendor policy must not reference private-only symbols",
    "system/sepolicy/vendor": "AOSP/ROM vendor-side policy for platform-owned vendor components",
    "system/sepolicy/prebuilts/api": "versioned public/private policy snapshots and mapping compatibility data",
    "system/sepolicy/mapping": "compatibility mapping files, present in some branches",
    "system/sepolicy/reqd_mask": "required mask policy used by compatibility filtering",
    "vendor/lineage/sepolicy": "LineageOS vendor/common policy overlay when present in the checkout",
    "vendor/cm/sepolicy": "legacy CyanogenMod/older Lineage policy overlay when present",
}

POLICY_FILE_NAMES = {
    "*.te", "file_contexts", "genfs_contexts", "property_contexts",
    "service_contexts", "hwservice_contexts", "vndservice_contexts",
    "seapp_contexts", "mac_permissions.xml", "keys.conf", "bug_map",
}

@dataclass
class Assignment:
    var: str
    op: str
    raw_value: str
    expanded_value: str
    source: str
    line: int

@dataclass
class IncludeEdge:
    source: str
    line: int
    raw: str
    resolved: str | None
    exists: bool
    kind: str = "include"

@dataclass
class PolicyDir:
    var: str
    meaning: str
    raw: str
    expanded: str
    path: str
    exists: bool
    source: str
    line: int
    warning: str = ""

@dataclass
class CoreDir:
    path: str
    meaning: str
    exists: bool

@dataclass
class Report:
    root: str
    entry_files: list[str]
    parsed_files: list[str]
    include_edges: list[IncludeEdge]
    policy_dirs: list[PolicyDir]
    core_dirs: list[CoreDir]
    warnings: list[str]
    declared_search_roots: list[str]
    existing_search_roots: list[str]
    next_search_roots: list[str]
    assignments: list[Assignment] = field(default_factory=list)


def strip_comment(line: str) -> str:
    # Good enough for makefiles used here: do not treat escaped # specially.
    return line.split("#", 1)[0].rstrip()


def join_lines(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    buf = ""
    start = 0
    for idx, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not buf:
            start = idx
        if LINE_CONT_RE.search(line):
            buf += LINE_CONT_RE.sub("", line) + " "
            continue
        buf += line
        if buf.strip():
            out.append((start, buf.strip()))
        buf = ""
    if buf.strip():
        out.append((start, buf.strip()))
    return out


def split_words(value: str) -> list[str]:
    return [x for x in value.replace("\\", " ").split() if x]


def resolve_vars(value: str, vars_map: dict[str, str], depth: int = 0) -> str:
    if depth > 20:
        return value

    def repl(m: re.Match[str]) -> str:
        name = (m.group(1) or m.group(2) or "").strip()
        # Avoid expanding complex make functions. Keep them visible.
        if name.startswith("call ") or " " in name or "," in name or name.startswith("shell "):
            return "$({})".format(name)
        return vars_map.get(name, os.environ.get(name, "$({})".format(name)))

    new = VAR_RE.sub(repl, value)
    if new == value:
        return new
    return resolve_vars(new, vars_map, depth + 1)


def normalize_path(token: str, root: Path, current_dir: Path) -> Path | None:
    token = token.strip().strip('"\'')
    if not token or token.startswith("$(") or token.startswith("${"):
        return None
    p = Path(token)
    if p.is_absolute():
        return p
    # Android make paths are normally repo-root relative. If the root-relative path
    # does not exist but a current-file-relative one does, prefer the existing path.
    root_rel = root / p
    cur_rel = current_dir / p
    if root_rel.exists() or not cur_rel.exists():
        return root_rel
    return cur_rel


def find_entry_files(root: Path, requested: list[str]) -> list[Path]:
    if requested:
        return [(root / p if not Path(p).is_absolute() else Path(p)).resolve() for p in requested]
    candidates = [
        root / "BoardConfig.mk",
        *sorted(root.glob("device/*/*/BoardConfig.mk")),
        *sorted(root.glob("device/*/*/*/BoardConfig.mk")),
    ]
    return [p.resolve() for p in candidates if p.exists()]


def parse_makefiles(root: Path, entries: list[Path], max_depth: int = 30) -> tuple[list[Assignment], list[IncludeEdge], list[Path], dict[str, str]]:
    vars_map: dict[str, str] = {}
    assignments: list[Assignment] = []
    includes: list[IncludeEdge] = []
    parsed: list[Path] = []
    seen: set[Path] = set()

    def parse_file(path: Path, depth: int) -> None:
        if depth > max_depth:
            includes.append(IncludeEdge(str(path), 0, "max include depth reached", None, False, "warning"))
            return
        path = path.resolve()
        if path in seen or not path.exists() or not path.is_file():
            return
        seen.add(path)
        parsed.append(path)
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            return
        for line_no, line in join_lines(text):
            inc = INCLUDE_RE.match(line)
            if inc:
                raw_target = inc.group(1).strip()
                expanded = resolve_vars(raw_target, vars_map)
                # include may contain multiple files; keep unresolved make funcs visible.
                for tok in split_words(expanded):
                    rp = normalize_path(tok, root, path.parent)
                    exists = bool(rp and rp.exists())
                    includes.append(IncludeEdge(str(path), line_no, raw_target, str(rp) if rp else None, exists, "include"))
                    if rp and exists:
                        parse_file(rp, depth + 1)
                continue
            inh = INHERIT_RE.match(line)
            if inh:
                raw_target = inh.group(1).strip()
                expanded = resolve_vars(raw_target, vars_map)
                rp = normalize_path(expanded, root, path.parent)
                exists = bool(rp and rp.exists())
                includes.append(IncludeEdge(str(path), line_no, raw_target, str(rp) if rp else None, exists, "inherit-product"))
                if rp and exists:
                    parse_file(rp, depth + 1)
                continue
            m = ASSIGN_RE.match(line)
            if not m:
                continue
            var, op, raw_val = m.groups()
            expanded = resolve_vars(raw_val.strip(), vars_map)
            old = vars_map.get(var, "")
            if op == "+=":
                vars_map[var] = (old + " " + expanded).strip()
            elif op == "?=":
                vars_map.setdefault(var, expanded)
            else:
                vars_map[var] = expanded
            assignments.append(Assignment(var, op, raw_val.strip(), vars_map.get(var, expanded), str(path), line_no))

    for e in entries:
        parse_file(e, 0)
    return assignments, includes, parsed, vars_map


def build_report(root: Path, requested: list[str]) -> Report:
    root = root.resolve()
    entries = find_entry_files(root, requested)
    assignments, includes, parsed, vars_map = parse_makefiles(root, entries)
    policy_dirs: list[PolicyDir] = []
    warnings: list[str] = []

    for a in assignments:
        if a.var not in SEPOLICY_VARS:
            continue
        for tok in split_words(a.expanded_value):
            if "=" in tok and a.var == "BOARD_SEPOLICY_M4DEFS":
                continue
            rp = normalize_path(tok, root, Path(a.source).parent)
            exists = bool(rp and rp.exists())
            warning = ""
            if a.var.startswith("BOARD_PLAT_"):
                warning = "deprecated variable; prefer SYSTEM_EXT_* on modern Android branches"
            elif a.var == "BOARD_SEPOLICY_DIRS":
                warning = "legacy variable; on Android 8+ this contributes vendor policy, not broad platform policy"
            elif rp is None:
                warning = "unresolved make expression; inspect with full lunch/make context"
            elif not exists:
                warning = "path not found from static repo root; check inherited makefile, missing repo, or generated path"
            policy_dirs.append(PolicyDir(
                var=a.var,
                meaning=SEPOLICY_VARS[a.var],
                raw=a.raw_value,
                expanded=a.expanded_value,
                path=str(rp) if rp else tok,
                exists=exists,
                source=a.source,
                line=a.line,
                warning=warning,
            ))
            if warning:
                warnings.append(f"{a.var}: {warning}: {tok}")

    core_dirs: list[CoreDir] = []
    for rel, meaning in CORE_POLICY_DIRS.items():
        core_dirs.append(CoreDir(str(root / rel), meaning, (root / rel).exists()))

    declared_policy_roots = [p.path for p in policy_dirs]
    declared_core_roots = [c.path for c in core_dirs]
    declared_roots = list(dict.fromkeys(declared_policy_roots + declared_core_roots))
    existing_policy_roots = [p.path for p in policy_dirs if p.exists]
    existing_core = [c.path for c in core_dirs if c.exists]
    existing_roots = list(dict.fromkeys(existing_policy_roots + existing_core))
    next_roots = existing_roots

    # Highlight likely missing include roots.
    for inc in includes:
        if not inc.exists and inc.raw and ("sepolicy" in inc.raw.lower() or "BoardConfigVendor" in inc.raw):
            warnings.append(f"Missing included policy/vendor makefile: {inc.raw} from {inc.source}:{inc.line}")

    if not policy_dirs:
        warnings.append("No SEPolicy directory variables were found in parsed BoardConfig/include chain. Do not do broad policy edits until the actual lunch BoardConfig path is known.")

    return Report(
        root=str(root),
        entry_files=[str(p) for p in entries],
        parsed_files=[str(p) for p in parsed],
        include_edges=includes,
        policy_dirs=policy_dirs,
        core_dirs=core_dirs,
        warnings=sorted(set(warnings)),
        declared_search_roots=declared_roots,
        existing_search_roots=existing_roots,
        next_search_roots=next_roots,
        assignments=assignments,
    )


def rel(path: str, root: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except Exception:
        return path


def emit_markdown(r: Report) -> None:
    print("# Android SEPolicy Source Map\n")
    print(f"- **Repo root:** `{r.root}`")
    if r.entry_files:
        print("- **Entry makefiles:**")
        for p in r.entry_files:
            print(f"  - `{rel(p, r.root)}`")
    if r.parsed_files:
        print("- **Parsed makefiles:**")
        for p in r.parsed_files:
            print(f"  - `{rel(p, r.root)}`")
    print()

    print("## Resolved SELinux policy variables\n")
    if not r.policy_dirs:
        print("No SEPolicy directory variables were resolved.\n")
    else:
        print("| Variable | Path | Exists | Source | Meaning |")
        print("|---|---|---:|---|---|")
        for d in r.policy_dirs:
            src = f"{rel(d.source, r.root)}:{d.line}"
            exists = "yes" if d.exists else "no"
            path = rel(d.path, r.root)
            note = d.meaning + (f"; {d.warning}" if d.warning else "")
            print(f"| `{d.var}` | `{path}` | {exists} | `{src}` | {note} |")
        print()

    print("## Include chain\n")
    if not r.include_edges:
        print("No include/inherit edges found.\n")
    else:
        print("| Kind | From | Raw target | Resolved | Exists |")
        print("|---|---|---|---|---:|")
        for e in r.include_edges:
            src = f"{rel(e.source, r.root)}:{e.line}"
            resolved = rel(e.resolved, r.root) if e.resolved else "unresolved"
            print(f"| {e.kind} | `{src}` | `{e.raw}` | `{resolved}` | {'yes' if e.exists else 'no'} |")
        print()

    print("## AOSP / ROM core policy directories\n")
    print("| Path | Exists | Meaning |")
    print("|---|---:|---|")
    for c in r.core_dirs:
        print(f"| `{rel(c.path, r.root)}` | {'yes' if c.exists else 'no'} | {c.meaning} |")
    print()

    print("## Declared search roots\n")
    if r.declared_search_roots:
        for p in r.declared_search_roots:
            exists = "exists" if Path(p).exists() else "missing"
            print(f"- `{rel(p, r.root)}` ({exists})")
    else:
        print("- No declared policy/core roots were resolved.")
    print()

    print("## Existing first search roots\n")
    if r.next_search_roots:
        for p in r.next_search_roots:
            print(f"- `{rel(p, r.root)}`")
    else:
        print("- No existing policy roots resolved; use the declared roots above to identify missing inherited repositories or wrong lunch/device path.")
    print()

    if r.warnings:
        print("## Warnings\n")
        for w in r.warnings:
            print(f"- {w}")
        print()

    print("## Next commands\n")
    print("```bash")
    print("# Search only resolved policy roots before a full-tree scan")
    if r.next_search_roots:
        roots = " ".join(repr(rel(p, r.root)) for p in r.next_search_roots)
        print(f"rg -n \"<type_or_property_or_context>\" {roots}")
    else:
        print("rg -n \"BOARD_.*SEPOLICY|SYSTEM_EXT_.*SEPOLICY|PRODUCT_.*SEPOLICY|include .*sepolicy\" device vendor hardware system")
    print("```")


def emit_text(r: Report) -> None:
    print("ROOT\t" + r.root)
    for d in r.policy_dirs:
        print(f"POLICY_DIR\t{d.var}\t{d.path}\t{'exists' if d.exists else 'missing'}\t{d.source}:{d.line}\t{d.warning}")
    for c in r.core_dirs:
        print(f"CORE_DIR\t{c.path}\t{'exists' if c.exists else 'missing'}\t{c.meaning}")
    for e in r.include_edges:
        print(f"INCLUDE\t{e.kind}\t{e.source}:{e.line}\t{e.raw}\t{e.resolved}\t{'exists' if e.exists else 'missing'}")
    for w in r.warnings:
        print("WARNING\t" + w)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".", help="Android repo root or directory containing BoardConfig.mk")
    ap.add_argument("--board-config", action="append", default=[], help="BoardConfig.mk or makefile entry path, repo-relative or absolute. May be repeated.")
    ap.add_argument("--format", choices=("markdown", "json", "text"), default="markdown")
    args = ap.parse_args()

    report = build_report(Path(args.repo), args.board_config)
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    elif args.format == "text":
        emit_text(report)
    else:
        emit_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
