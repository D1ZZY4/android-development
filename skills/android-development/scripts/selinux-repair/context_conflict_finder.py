#!/usr/bin/env python3
"""Find common Android SELinux context conflicts before build tools do.

Scans file_contexts, genfs_contexts, property_contexts, service_contexts,
hwservice_contexts, and vndservice_contexts for duplicates, broad prefixes,
default labels, malformed contexts, and likely partition/context mismatches.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CONTEXT_NAMES = {"file_contexts", "genfs_contexts", "property_contexts", "service_contexts", "hwservice_contexts", "vndservice_contexts"}
SKIP_DIRS = {".git", ".repo", "out", "prebuilts", "node_modules", ".gradle", "kernel", ".ccache"}
GENERIC_TYPES = {
    "sysfs", "proc", "debugfs", "tracefs", "rootfs", "device", "unlabeled",
    "default_prop", "vendor_default_prop", "default_android_service",
    "default_android_hwservice", "default_android_vndservice", "system_data_file",
    "vendor_file", "app_data_file",
}
BROAD_PROP_PREFIXES = {"ro.", "persist.", "vendor.", "ro.vendor.", "persist.vendor.", "sys.", "debug.", "ctl.", "service."}


@dataclass
class Finding:
    severity: str
    code: str
    path: str
    line: int
    key: str
    context: str
    message: str


def iter_context_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if not p.is_file() or p.name not in CONTEXT_NAMES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def parse_type(ctx: str) -> str:
    parts = ctx.split(":")
    return parts[2] if len(parts) >= 3 else ""


def add(findings: list[Finding], severity: str, code: str, path: Path, line: int, key: str, ctx: str, msg: str) -> None:
    findings.append(Finding(severity, code, str(path), line, key, ctx, msg))


def scan(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    entries: dict[str, list[tuple[str, str, Path, int, str]]] = {}

    for path in iter_context_files(root):
        for idx, raw in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if path.name == "genfs_contexts":
                if len(parts) < 3:
                    add(findings, "error", "malformed_genfs_context", path, idx, line, "", "genfs_contexts needs filesystem, path, and context.")
                    continue
                key = parts[0] + " " + parts[1]
                ctx = parts[2]
            else:
                if len(parts) < 2:
                    add(findings, "error", "malformed_context", path, idx, line, "", f"{path.name} needs key and SELinux context.")
                    continue
                key, ctx = parts[0], parts[1]
            typ = parse_type(ctx)
            entries.setdefault(path.name + "\0" + key, []).append((ctx, typ, path, idx, line))

            if not ctx.startswith("u:object_r:") and path.name != "seapp_contexts":
                add(findings, "error", "invalid_context_shape", path, idx, key, ctx, "Expected object context like u:object_r:<type>:s0.")
            if typ in GENERIC_TYPES:
                add(findings, "warning", "generic_type_mapping", path, idx, key, ctx, f"Maps to generic type `{typ}`. Prefer a narrow resource-specific type.")
            if path.name == "property_contexts":
                if key in BROAD_PROP_PREFIXES or (key.endswith(".") and any(key.startswith(p) for p in BROAD_PROP_PREFIXES)):
                    add(findings, "warning", "broad_property_prefix", path, idx, key, ctx, "Broad prefixes are prone to property_info_serializer conflicts. Prefer exact entries unless this tree owns the family.")
                if len(parts) >= 3 and parts[2] not in {"exact", "prefix", "bool", "int", "uint", "double", "string", "enum"}:
                    add(findings, "info", "property_context_extra_fields", path, idx, key, ctx, "Review property_contexts exact/prefix/type fields for branch compatibility.")
            if path.name == "file_contexts":
                if re.match(r"^/(sys|proc|dev)(/\.\*)?\??$", key):
                    add(findings, "warning", "broad_file_context", path, idx, key, ctx, "Broad /sys, /proc, or /dev mapping can hide resource-specific labels.")
                if key.startswith("/vendor") and typ and "vendor" not in typ and typ.endswith("_exec"):
                    add(findings, "info", "vendor_exec_naming", path, idx, key, ctx, "Vendor executables usually use vendor-owned exec types; verify partition ownership.")

    for combo, vals in entries.items():
        name, key = combo.split("\0", 1)
        contexts = {v[0] for v in vals}
        if len(vals) > 1 and len(contexts) > 1:
            for ctx, typ, path, idx, line in vals:
                add(findings, "error", "duplicate_conflicting_context", path, idx, key, ctx, f"`{name}` maps `{key}` to multiple contexts after local scan.")
        elif len(vals) > 1:
            for ctx, typ, path, idx, line in vals[1:]:
                add(findings, "warning", "duplicate_same_context", path, idx, key, ctx, f"Duplicate `{name}` entry for `{key}`; remove stale duplicates if inherited policy already owns it.")

    # Property prefix overlap.
    prop_entries = []
    for combo, vals in entries.items():
        name, key = combo.split("\0", 1)
        if name != "property_contexts":
            continue
        for ctx, typ, path, idx, line in vals:
            prop_entries.append((key, ctx, typ, path, idx))
    for prefix, pctx, ptyp, ppath, pidx in prop_entries:
        if not prefix.endswith("."):
            continue
        for key, ctx, typ, path, idx in prop_entries:
            if key == prefix:
                continue
            if key.startswith(prefix) and ctx != pctx:
                add(findings, "warning", "property_prefix_overlap", path, idx, key, ctx, f"Overlaps prefix `{prefix}` at {ppath}:{pidx}; this can trigger duplicate-prefix or ownership failures.")

    sev_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    findings.sort(key=lambda f: (sev_order.get(f.severity, 9), f.path, f.line, f.code))
    return findings


def emit_markdown(findings: list[Finding]) -> None:
    print("# SELinux Context Conflict Report\n")
    if not findings:
        print("No obvious context conflicts found by static scan.")
        return
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    print("## Summary\n")
    for sev in ["critical", "error", "warning", "info"]:
        if sev in counts:
            print(f"- **{sev}:** {counts[sev]}")
    print("\n## Findings\n")
    for f in findings:
        print(f"- **{f.severity} `{f.code}`** `{f.path}:{f.line}` `{f.key}` → `{f.context}`  ")
        print(f"  {f.message}")


def emit_text(findings: list[Finding]) -> None:
    for f in findings:
        print(f"{f.severity}\t{f.code}\t{f.path}:{f.line}\t{f.key}\t{f.context}\t{f.message}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    args = ap.parse_args()
    findings = scan(Path(args.root).resolve())
    if args.format == "json":
        print(json.dumps([asdict(f) for f in findings], indent=2, sort_keys=True))
    elif args.format == "markdown":
        emit_markdown(findings)
    else:
        emit_text(findings)
    return 1 if any(f.severity in {"critical", "error"} for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
