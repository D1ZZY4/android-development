#!/usr/bin/env python3
"""Diagnose Android property_contexts duplicate/exact/prefix build failures.

This tool targets errors such as:
  host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'ro.vendor.audio.'
  property_info_serializer: Duplicate exact match detected for 'persist.foo.bar'

It can scan source trees, generated out/* property_contexts files, or property_context
paths extracted from a build log. It emulates the duplicate slots used by AOSP's
property_info_serializer trie closely enough to find the conflicting lines and
then prints a safe repair plan.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
try:
    from sepolicy_path_resolver import build_report as build_source_map  # type: ignore
except Exception:  # pragma: no cover
    build_source_map = None

SKIP_DIRS_DEFAULT = {".git", ".repo", "prebuilts", "node_modules", ".gradle", "kernel", ".ccache"}
PROP_RE = re.compile(r"(?:Duplicate (?:prefix|exact) match detected for ['\"]([^'\"]+)['\"])", re.I)
PC_ARG_RE = re.compile(r"--property-contexts=([^\s)]+)")
VALID_MATCH = {"exact", "prefix", ""}
VALID_VALUE_TYPES = {"string", "bool", "int", "uint", "double", "size", "enum"}


@dataclass
class PropertyEntry:
    property: str
    context: str
    match: str
    value_type: str
    exact: bool
    source: str
    line: int
    raw: str

    @property
    def kind(self) -> str:
        return "exact" if self.exact else "prefix"

    @property
    def trie_slot(self) -> str:
        # Mirrors property_service/libpropertyinfoserializer/trie_builder.cpp enough
        # for duplicate detection: exact entries and prefix entries occupy separate
        # slots; dotted prefix entries set a child node's context; non-dotted prefix
        # entries use AddPrefixContext at the parent node.
        if self.exact:
            return "exact\0" + self.property
        return "prefix\0" + self.property


@dataclass
class Finding:
    severity: str
    code: str
    property: str
    message: str
    entries: list[PropertyEntry] = field(default_factory=list)


@dataclass
class Report:
    requested_properties: list[str]
    scanned_files: list[str]
    findings: list[Finding]
    advice: list[str]
    search_strategy: list[str] = field(default_factory=list)
    source_map_roots: list[str] = field(default_factory=list)


def parse_property_line(raw: str, source: Path, line_no: int) -> PropertyEntry | None:
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parts = stripped.split()
    if len(parts) < 2:
        return None
    prop, ctx = parts[0], parts[1]
    match = parts[2] if len(parts) >= 3 else ""
    exact = match == "exact"
    value_type = ""
    if match == "prefix" or match == "exact":
        value_type = " ".join(parts[3:])
    elif match in VALID_VALUE_TYPES:
        # Legacy/no explicit match operation; third token is value type. AOSP treats
        # the property name as a prefix unless the branch requires explicit exact/prefix.
        value_type = " ".join(parts[2:])
        match = ""
        exact = False
    else:
        # Older files may omit match/value type entirely. Unknown third fields are
        # left visible in raw output instead of rejected here; the build tool owns
        # branch-specific validation.
        if len(parts) >= 3:
            value_type = " ".join(parts[2:])
        match = ""
        exact = False
    return PropertyEntry(prop, ctx, match, value_type, exact, str(source), line_no, stripped)


def iter_property_context_files(root: Path, include_out: bool = False) -> Iterable[Path]:
    skip = set(SKIP_DIRS_DEFAULT)
    if not include_out:
        skip.add("out")
    for p in root.rglob("*"):
        if not p.is_file() or p.name != "property_contexts":
            continue
        if any(part in skip for part in p.parts):
            continue
        yield p


def parse_file(path: Path) -> list[PropertyEntry]:
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return []
    out: list[PropertyEntry] = []
    for i, raw in enumerate(text.splitlines(), 1):
        ent = parse_property_line(raw, path, i)
        if ent:
            out.append(ent)
    return out


def extract_log_properties(text: str) -> list[str]:
    return sorted(set(m.group(1) for m in PROP_RE.finditer(text)))


def extract_property_context_args(text: str, base: Path) -> list[Path]:
    files: list[Path] = []
    for m in PC_ARG_RE.finditer(text):
        raw = m.group(1).strip('"\'')
        p = Path(raw)
        if not p.is_absolute():
            p = base / p
        if p.exists() and p.is_file():
            files.append(p.resolve())
    # preserve order, dedupe
    return list(dict.fromkeys(files))


def property_files_from_source_map(repo: Path, board_configs: list[str], include_out: bool = False) -> tuple[list[Path], list[str]]:
    if not board_configs or build_source_map is None:
        return [], []
    try:
        report = build_source_map(repo, board_configs)
    except Exception:
        return [], []
    declared = list(getattr(report, "declared_search_roots", []) or [])
    files: list[Path] = []
    for raw in getattr(report, "next_search_roots", []) or []:
        root = Path(raw)
        if root.exists():
            files.extend(iter_property_context_files(root, include_out=include_out))
    return list(dict.fromkeys(files)), declared


def filter_files_for_requested(files: list[Path], requested: list[str]) -> list[Path]:
    # Keep all files when no property was reported. When the log names exact
    # duplicate properties, scan files containing those properties first. If none
    # match, return all files so the report can still explain missing evidence.
    if not requested:
        return files
    matched: list[Path] = []
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except Exception:
            continue
        if any(prop in text for prop in requested):
            matched.append(f)
    return matched or files


def scan_entries(entries: list[PropertyEntry], requested: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    by_slot: dict[str, list[PropertyEntry]] = {}
    by_prop: dict[str, list[PropertyEntry]] = {}
    for e in entries:
        by_slot.setdefault(e.trie_slot, []).append(e)
        by_prop.setdefault(e.property, []).append(e)

    for slot, vals in sorted(by_slot.items()):
        if len(vals) <= 1:
            continue
        prop = vals[0].property
        contexts = {(v.context, v.value_type) for v in vals}
        severity = "error"
        code = "duplicate_exact_property" if vals[0].exact else "duplicate_prefix_property"
        msg = f"{len(vals)} entries occupy the same property_info trie {vals[0].kind} slot for `{prop}`."
        if len(contexts) == 1:
            msg += " They map to the same context/type, but the serializer still rejects duplicate slots. Keep one owner."
        else:
            msg += " They map to different contexts/types; choose the correct owner and remove or narrow the others."
        findings.append(Finding(severity, code, prop, msg, vals))

    # Requested property from log but not found in scanned files: report separately.
    for prop in requested:
        if prop not in by_prop:
            findings.append(Finding(
                "warning",
                "reported_property_not_found",
                prop,
                f"The build log reports `{prop}`, but it was not found in scanned property_contexts. Scan generated out/* files or pass the exact --property-contexts files from the failing command.",
                [],
            ))

    # Potentially confusing source-tree overlaps: not always fatal, but worth surfacing.
    entries_sorted = sorted(entries, key=lambda e: (e.property, e.source, e.line))
    for e in entries_sorted:
        if not e.property.endswith("."):
            continue
        children = [x for x in by_prop if x != e.property and x.startswith(e.property)]
        if children:
            examples = ", ".join(sorted(children)[:4])
            findings.append(Finding(
                "info",
                "prefix_has_children",
                e.property,
                f"Prefix `{e.property}` also has child entries ({examples}). This is legal when ownership is intentional, but broad prefixes like ro.vendor.audio. often hide stale duplicate source policy.",
                [e],
            ))

    order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: (order.get(f.severity, 9), f.property, f.code))
    return findings


def build_report(paths: list[Path], requested: list[str], search_strategy: list[str] | None = None, source_map_roots: list[str] | None = None) -> Report:
    entries: list[PropertyEntry] = []
    for p in paths:
        entries.extend(parse_file(p))
    findings = scan_entries(entries, requested)
    advice = [
        "Fix property_contexts first; this is not solved by adding allow rules in .te files.",
        "For `Duplicate prefix match`, grep the exact reported property/prefix in all property_contexts and keep only one matching prefix slot.",
        "Prefer exact entries for individual properties; keep a broad prefix only when this tree really owns the whole property family.",
        "After editing source property_contexts, rebuild the generated *_property_contexts target or clean affected intermediates before retrying host_init_verifier.",
    ]
    return Report(requested, [str(p) for p in paths], findings, advice, search_strategy or [], source_map_roots or [])


def emit_markdown(r: Report) -> None:
    print("# Android Property Context Doctor\n")
    if r.search_strategy:
        print("## Search strategy\n")
        for item in r.search_strategy:
            print(f"- {item}")
        print()
    if r.source_map_roots:
        print("## Declared BoardConfig/core roots\n")
        for p in r.source_map_roots[:30]:
            print(f"- `{p}`")
        print()
    if r.requested_properties:
        print("## Reported by build log\n")
        for p in r.requested_properties:
            print(f"- `{p}`")
        print()
    print("## Scanned files\n")
    if r.scanned_files:
        for p in r.scanned_files:
            print(f"- `{p}`")
    else:
        print("No property_contexts files were scanned.")
    print()
    print("## Findings\n")
    if not r.findings:
        print("No duplicate property trie slots found in scanned files.")
    for f in r.findings:
        print(f"### {f.severity.upper()} `{f.code}` — `{f.property}`\n")
        print(f.message + "\n")
        for e in f.entries:
            print(f"- `{e.source}:{e.line}` `{e.raw}`")
        print()
    print("## Repair advice\n")
    for a in r.advice:
        print(f"- {a}")


def emit_text(r: Report) -> None:
    for f in r.findings:
        print(f"{f.severity}\t{f.code}\t{f.property}\t{f.message}")
        for e in f.entries:
            print(f"  {e.source}:{e.line}: {e.raw}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="property_contexts files or directories to scan")
    ap.add_argument("--repo", help="Repo root to scan for source property_contexts")
    ap.add_argument("--board-config", action="append", default=[], help="BoardConfig.mk or makefile entry used to resolve SELinux roots before broad search. May be repeated.")
    ap.add_argument("--full-tree", action="store_true", help="With --board-config, also scan the full repo after source-map roots.")
    ap.add_argument("--include-out", action="store_true", help="When scanning a repo/directory, include out/ generated files")
    ap.add_argument("--log", help="Build log to extract reported duplicate property and --property-contexts files")
    ap.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    args = ap.parse_args()

    base = Path.cwd().resolve()
    requested: list[str] = []
    files: list[Path] = []

    search_strategy: list[str] = []
    source_map_roots: list[str] = []

    if args.log:
        log_path = Path(args.log)
        text = log_path.read_text(errors="ignore")
        requested.extend(extract_log_properties(text))
        exact_files = extract_property_context_args(text, base)
        files.extend(exact_files)
        if exact_files:
            search_strategy.append("Scanned exact --property-contexts files extracted from the failing command first.")

    repo_path = Path(args.repo).resolve() if args.repo else None
    if repo_path and args.board_config:
        mapped_files, source_map_roots = property_files_from_source_map(repo_path, args.board_config, include_out=args.include_out)
        mapped_files = filter_files_for_requested(mapped_files, requested)
        files.extend(mapped_files)
        search_strategy.append("Resolved BoardConfig/include chain and scanned source-map policy roots before broad repo search.")
    if repo_path and (not args.board_config or args.full_tree):
        files.extend(iter_property_context_files(repo_path, include_out=args.include_out))
        search_strategy.append("Scanned full repo property_contexts" + (" after source-map roots." if args.board_config else "."))

    for raw in args.paths:
        p = Path(raw).resolve()
        if p.is_dir():
            files.extend(iter_property_context_files(p, include_out=args.include_out))
            search_strategy.append(f"Scanned explicit directory: {p}")
        elif p.is_file():
            files.append(p)
            search_strategy.append(f"Scanned explicit file: {p}")

    files = list(dict.fromkeys(files))
    requested = sorted(set(requested))
    report = build_report(files, requested, search_strategy, source_map_roots)

    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    elif args.format == "markdown":
        emit_markdown(report)
    else:
        emit_text(report)
    return 1 if any(f.severity == "error" for f in report.findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
