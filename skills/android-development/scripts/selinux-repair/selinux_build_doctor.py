#!/usr/bin/env python3
"""Repo-aware Android SELinux build-error repair planner.

This tool does not blindly edit policy. It classifies the first SELinux build
failure, extracts likely symbols/properties/paths, searches the repository for
related context/policy files, and emits a concrete repair plan that a human or
coding agent can apply.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

# Import local triage rules when invoked from the scripts directory or package root.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
try:
    from build_error_triage import find_first  # type: ignore
except Exception:  # pragma: no cover
    find_first = None
try:
    from sepolicy_path_resolver import build_report as build_source_map  # type: ignore
except Exception:  # pragma: no cover
    build_source_map = None

TEXT_SUFFIXES = {".te", ".cil", ".fc", ".contexts", ".rc", ".mk", ".bp", ".prop", ".txt", ".log", ".conf", ".xml"}
CONTEXT_NAMES = {
    "file_contexts", "genfs_contexts", "property_contexts", "service_contexts",
    "hwservice_contexts", "vndservice_contexts", "seapp_contexts", "mac_permissions.xml",
}
SKIP_DIRS = {".git", ".repo", "out", "prebuilts", "node_modules", ".gradle", "kernel", ".ccache"}


@dataclass
class SearchHit:
    path: str
    line: int
    text: str


@dataclass
class DoctorReport:
    klass: str
    severity: str
    first_line: int
    evidence: str
    detail: str
    root_cause: str
    safe_fix_path: str
    extracted_tokens: dict[str, list[str]] = field(default_factory=dict)
    repo_hits: dict[str, list[SearchHit]] = field(default_factory=dict)
    source_map_roots: list[str] = field(default_factory=list)
    searched_roots: list[str] = field(default_factory=list)
    patch_targets: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    do_not_do: list[str] = field(default_factory=list)
    confidence: str = "medium"


def read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(errors="ignore")
    return sys.stdin.read()


def iter_text_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in CONTEXT_NAMES or p.suffix in TEXT_SUFFIXES:
            yield p


def grep_roots(roots: Iterable[Path], needles: Iterable[str], max_hits: int) -> dict[str, list[SearchHit]]:
    needles = [n for n in dict.fromkeys(needles) if n and len(n) >= 2]
    results: dict[str, list[SearchHit]] = {n: [] for n in needles}
    if not needles:
        return {}
    lowered = [(n, n.lower()) for n in needles]
    seen_files: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in iter_text_files(root):
            rp = path.resolve()
            if rp in seen_files:
                continue
            seen_files.add(rp)
            try:
                lines = path.read_text(errors="ignore").splitlines()
            except Exception:
                continue
            for idx, line in enumerate(lines, 1):
                low = line.lower()
                for needle, needle_low in lowered:
                    if len(results[needle]) >= max_hits:
                        continue
                    if needle_low in low:
                        results[needle].append(SearchHit(str(path), idx, line.strip()[:240]))
    return {k: v for k, v in results.items() if v}


def resolve_source_map_roots(repo: Path | None, board_configs: list[str]) -> tuple[list[Path], list[str]]:
    if not repo or not board_configs or build_source_map is None:
        return ([repo] if repo else []), []
    try:
        report = build_source_map(repo, board_configs)
    except Exception:
        return [repo], []
    declared = list(getattr(report, "declared_search_roots", []) or [])
    existing = [Path(x) for x in (getattr(report, "next_search_roots", []) or []) if Path(x).exists()]
    return (existing or [repo]), declared


def extract_tokens(text: str, evidence: str) -> dict[str, list[str]]:
    joined = evidence + "\n" + text[:20000]
    out: dict[str, set[str]] = {"symbols": set(), "properties": set(), "paths": set(), "contexts": set(), "classes": set()}

    for pat in [
        r"(?:unknown|undefined|resolve)\s+(?:type|attribute|identifier|typeattributeset)\s+['\"]?([A-Za-z0-9_.$-]+)",
        r"type\s+([A-Za-z0-9_.$-]+)\s+is not defined",
        r"attribute\s+([A-Za-z0-9_.$-]+)\s+is not declared",
        r"Duplicate declaration[^\n]*(?:\n[^\n]*){0,4}?\btype\s+([A-Za-z0-9_.$-]+)\b",
        r"Duplicate declaration[^\n]*(?:\n[^\n]*){0,4}?\battribute\s+([A-Za-z0-9_.$-]+)\b",
    ]:
        for m in re.finditer(pat, joined, re.I):
            out["symbols"].add(m.group(1))

    for m in re.finditer(r"\b(?:u:object_r:|u:r:)([A-Za-z0-9_.$-]+):s0\b", joined):
        out["contexts"].add(m.group(1))
        out["symbols"].add(m.group(1))

    # Property extraction is intentionally conservative. Do not treat every dotted
    # token as a property, because build logs contain dotted rc/service filenames.
    for m in re.finditer(r"Duplicate (?:prefix|exact) match detected for ['\"]([^'\"]+)['\"]", joined, re.I):
        out["properties"].add(m.group(1))
    for m in re.finditer(r"\b(?:setprop|getprop|property=|property:)\s+['\"]?([A-Za-z0-9_.-]+)", joined):
        token = m.group(1).rstrip("':,;)")
        if "." in token and not token.endswith(".rc"):
            out["properties"].add(token)
    for line in joined.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2 and parts[1].startswith("u:object_r:") and "." in parts[0] and not parts[0].endswith(".rc"):
            out["properties"].add(parts[0])
    for m in re.finditer(r"(?:^|\s)(/[A-Za-z0-9_./*?+(){}\[\]^-]+)", joined):
        p = m.group(1).rstrip(":;,)")
        if len(p) > 1:
            out["paths"].add(p)
    for m in re.finditer(r":([A-Za-z0-9_]+)\s+\{?\s*([A-Za-z0-9_ ]+)\}?", evidence):
        out["classes"].add(m.group(1))

    return {k: sorted(v)[:25] for k, v in out.items() if v}


def classify_without_import(text: str):
    pats = [
        ("duplicate_property_prefix", r"Duplicate prefix match detected"),
        ("duplicate_property_exact", r"Duplicate exact match detected"),
        ("property_info_serializer", r"property_info_serializer|BuildTrie|property info|Unable to serialize property contexts"),
        ("host_init_verifier", r"host_init_verifier|Failed to parse init|init verifier"),
        ("neverallow", r"neverallow|violated by allow|libsepol\.report_failure"),
        ("duplicate_type_declaration", r"Duplicate declaration of type"),
        ("duplicate_attribute_declaration", r"Duplicate declaration of attribute"),
        ("unknown_type_or_attribute", r"unknown|undefined|Failed to resolve"),
        ("checkfc_or_invalid_context", r"checkfc|invalid context|not a valid context|type .* is not defined"),
        ("syntax_or_m4", r"syntax error|m4:|secilc|error\(s\) encountered while parsing configuration"),
        ("runtime_avc_in_build_log", r"avc:\s*denied"),
    ]
    for i, line in enumerate(text.splitlines(), 1):
        for label, pat in pats:
            if re.search(pat, line, re.I):
                return {"label": label, "severity": "error", "line_number": i, "line": line, "detail": line[:160], "cause": "Pattern-based SELinux build failure.", "fix": "Inspect first failure and repair by class."}
    return {"label": "unknown", "severity": "unknown", "line_number": 0, "line": "", "detail": "", "cause": "No known SELinux pattern matched.", "fix": "Capture a fuller build log and inspect the first failing command."}


def make_report(text: str, repo: Path | None, max_hits: int, board_configs: list[str] | None = None) -> DoctorReport:
    if find_first:
        f = find_first(text)
        if f is not None:
            triage = asdict(f)
        else:
            triage = classify_without_import(text)
    else:
        triage = classify_without_import(text)

    klass = triage.get("label", "unknown")
    evidence = triage.get("line", "") or "No matched line"
    tokens = extract_tokens(text, evidence)
    needles: list[str] = []
    for values in tokens.values():
        needles.extend(values)
    # Search the exact reported property/prefix only; parent-prefix expansion is
    # intentionally avoided because it creates noisy hits such as `ro.` or `vendor.`.
    search_roots, source_map_roots = resolve_source_map_roots(repo, board_configs or [])
    hits = grep_roots(search_roots, needles, max_hits=max_hits) if search_roots else {}

    patch_targets, commands, dont, confidence = plan_for(klass, tokens, bool(repo), hits, bool(board_configs))
    return DoctorReport(
        klass=klass,
        severity=triage.get("severity", "error"),
        first_line=int(triage.get("line_number", 0) or 0),
        evidence=evidence,
        detail=triage.get("detail", ""),
        root_cause=triage.get("cause", ""),
        safe_fix_path=triage.get("fix", ""),
        extracted_tokens=tokens,
        repo_hits=hits,
        source_map_roots=source_map_roots,
        searched_roots=[str(p) for p in search_roots],
        patch_targets=patch_targets,
        commands=commands,
        do_not_do=dont,
        confidence=confidence,
    )


def plan_for(klass: str, tokens: dict[str, list[str]], has_repo: bool, hits: dict[str, list[SearchHit]], used_source_map: bool = False):
    patch_targets: list[str] = []
    commands = [
        "scripts/build_error_triage.py build.log --format markdown",
        "scripts/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown",
    ]
    dont = [
        "Do not set SELINUX_IGNORE_NEVERALLOWS as a fix.",
        "Do not copy platform-private types into vendor policy.",
        "Do not add broad allows to generic labels such as sysfs, proc, device, default_prop, or default_android_service.",
    ]
    confidence = "medium" if has_repo else "low_without_repo"

    if klass in {"duplicate_property_prefix", "duplicate_property_exact", "property_info_serializer"}:
        patch_targets = ["*/property_contexts", "generated out/*_property_contexts", "BoardConfig.mk / device.mk sepolicy dirs"]
        commands += [
            "scripts/property_context_doctor.py --log build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown",
            "scripts/context_conflict_finder.py . --format markdown",
            "rg -n \"<property-or-prefix>\" . --glob '*property_contexts' --glob '*.prop' --glob '*.mk'",
            "rm -rf out/target/product/<device>/obj/ETC/*property_contexts_intermediates out/soong/.intermediates/system/sepolicy/*property_contexts*",
            "m vendor_property_contexts odm_property_contexts product_property_contexts || m vendor_sepolicy.cil",
        ]
        dont += ["Do not add a .te allow rule for a property serialization failure.", "Do not patch every init rc that appears in the cascade; fix the single property_contexts root cause."]
    elif klass == "host_init_verifier":
        patch_targets = ["init*.rc", "file_contexts", "property_contexts", "service_contexts", "*.te for service domains"]
        commands += [
            "rg -n \"<service-or-property>\" . --glob '*.rc' --glob '*contexts' --glob '*.te'",
            "m host_init_verifier || m vendor_sepolicy.cil",
        ]
    elif klass == "neverallow":
        patch_targets = ["the violating .te file", "file_contexts/genfs_contexts if label is generic", "partition placement / PRODUCT_PACKAGES if executable location is wrong"]
        commands += [
            "rg -n \"neverallow|violated by allow|<source-domain>|<target-type>\" system/sepolicy device vendor hardware",
            "m sepolicy_neverallows || m sepolicy_tests",
        ]
        confidence = "medium" if has_repo and hits else "low_needs_full_violation_block"
    elif klass in {"duplicate_type_declaration", "duplicate_attribute_declaration", "duplicate_declaration"}:
        patch_targets = ["the reported .te declaration", "other .te files declaring the same symbol", "inherited vendor/common sepolicy dirs"]
        commands += [
            "rg -n \"\\b<symbol>\\b\" . --glob '*.te' --glob '*.cil' --glob '*property_contexts'",
            "rg -n \"BOARD.*SEPOLICY|PRODUCT_.*SEPOLICY|SYSTEM_EXT_.*SEPOLICY|BOARD_ODM_SEPOLICY\" .",
            "m vendor_sepolicy.cil sepolicy_neverallows",
        ]
        dont += ["Do not declare a property type twice. If the type already exists, reuse it in property_contexts or rename your new one everywhere."]
    elif klass == "unknown_type_or_attribute":
        patch_targets = ["declaration .te file", "BoardConfig.mk sepolicy dirs", "public/private policy boundary", "compat mapping for exported public policy when relevant"]
        commands += [
            "rg -n \"\\b<symbol>\\b\" system/sepolicy device vendor hardware",
            "rg -n \"BOARD.*SEPOLICY|PRODUCT_.*SEPOLICY|SYSTEM_EXT_.*SEPOLICY|BOARD_ODM_SEPOLICY\" .",
            "m vendor_sepolicy.cil plat_sepolicy.cil || m sepolicy_tests",
        ]
    elif klass == "checkfc_or_invalid_context":
        patch_targets = ["file_contexts/property_contexts/service_contexts/hwservice_contexts", "type declaration .te", "required type attributes"]
        commands += [
            "scripts/context_conflict_finder.py . --format markdown",
            "rg -n \"<undefined-type>|<bad-context>\" . --glob '*contexts' --glob '*.te'",
            "m checkfc || m sepolicy_tests",
        ]
    elif klass == "sepolicy_tests_attribute":
        patch_targets = ["type declaration .te", "context file causing the type requirement"]
        commands += [
            "rg -n \"<type>\" . --glob '*.te' --glob '*contexts'",
            "m sepolicy_tests",
        ]
    elif klass == "syntax_or_m4":
        patch_targets = ["source .te/.cil file reported by generated policy line marker", "macro call", "missing final newline"]
        commands += [
            "sed -n '<start>,<end>p' <reported-source-or-generated-policy>",
            "python3 -m py_compile scripts/*.py || true",
            "m vendor_sepolicy.cil plat_sepolicy.cil",
        ]
    elif klass == "runtime_avc_in_build_log":
        patch_targets = ["runtime denial triage, not build patch yet"]
        commands += [
            "scripts/summarize_denials.py build.log --format markdown",
            "scripts/capture_selinux_denials.sh --root --events 1500",
        ]
    else:
        patch_targets = ["first failing command output", "generated *_intermediates policy files"]
        commands += [
            "m <failed-target> SHOW_COMMANDS=true 2>&1 | tee build.log",
            "rg -n \"FAILED:|neverallow|checkpolicy|secilc|checkfc|host_init_verifier|property_info_serializer|avc: denied\" build.log",
        ]
        confidence = "low"

    # Add concrete hit-derived patch targets.
    if hits:
        for hit_list in hits.values():
            for h in hit_list[:2]:
                if h.path not in patch_targets:
                    patch_targets.append(h.path)

    return patch_targets[:25], commands, dont, confidence


def emit_markdown(r: DoctorReport) -> None:
    print("# Android SELinux Build Doctor\n")
    print(f"- **Class:** `{r.klass}`")
    print(f"- **Severity:** `{r.severity}`")
    print(f"- **Confidence:** `{r.confidence}`")
    if r.first_line:
        print(f"- **First matched line:** {r.first_line}")
    print(f"- **Likely root cause:** {r.root_cause}")
    print(f"- **Safe fix path:** {r.safe_fix_path}\n")
    print("## First evidence\n")
    print("```text")
    print(r.evidence)
    print("```\n")

    if r.extracted_tokens:
        print("## Extracted tokens\n")
        for k, vals in r.extracted_tokens.items():
            print(f"- **{k}:** " + ", ".join(f"`{v}`" for v in vals[:12]))
        print()

    if r.source_map_roots or r.searched_roots:
        print("## Source-map search scope\n")
        if r.source_map_roots:
            print("Declared BoardConfig/core roots:")
            for t in r.source_map_roots[:20]:
                print(f"- `{t}`")
        if r.searched_roots:
            print("\nActually searched roots:")
            for t in r.searched_roots[:20]:
                print(f"- `{t}`")
        print()

    if r.patch_targets:
        print("## Confirmed hits / suggested patch targets\n")
        for t in r.patch_targets:
            print(f"- `{t}`")
        print()

    if r.repo_hits:
        print("## Repository hits\n")
        for token, hits in r.repo_hits.items():
            print(f"### `{token}`")
            for h in hits[:8]:
                print(f"- `{h.path}:{h.line}` — {h.text}")
            print()

    print("## Validation commands\n")
    for c in r.commands:
        print(f"```bash\n{c}\n```")
    print("## Do not do\n")
    for d in r.do_not_do:
        print(f"- {d}")


def emit_text(r: DoctorReport) -> None:
    print(f"CLASS\t{r.klass}")
    print(f"SEVERITY\t{r.severity}")
    print(f"CONFIDENCE\t{r.confidence}")
    print(f"LINE\t{r.first_line}")
    print(f"CAUSE\t{r.root_cause}")
    print(f"FIX\t{r.safe_fix_path}")
    print(f"EVIDENCE\t{r.evidence}")
    for target in r.patch_targets:
        print(f"PATCH_TARGET\t{target}")
    for c in r.commands:
        print(f"COMMAND\t{c}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", nargs="?", help="Build log path. Reads stdin when omitted.")
    ap.add_argument("--repo", help="Android repo/device-tree root for symbol/context search")
    ap.add_argument("--board-config", action="append", default=[], help="BoardConfig.mk or makefile entry to resolve SELinux roots before broad search. May be repeated.")
    ap.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    ap.add_argument("--max-hits", type=int, default=12)
    args = ap.parse_args()

    text = read_text(args.log)
    repo = Path(args.repo).resolve() if args.repo else None
    report = make_report(text, repo, args.max_hits, args.board_config)
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    elif args.format == "markdown":
        emit_markdown(report)
    else:
        emit_text(report)
    return 0 if report.klass != "unknown" else 2


if __name__ == "__main__":
    raise SystemExit(main())
