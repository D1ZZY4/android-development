#!/usr/bin/env python3
"""Summarize Android SELinux AVC denials with label-first guidance."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

AVC_PAT = re.compile(r"avc:\s+denied\s+\{\s*([^}]+?)\s*\}(.+)", re.I)
KV_PAT = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)=(\"[^\"]*\"|[^\s]+)")
CONTEXT_PAT = re.compile(r"([^:]+):([^:]+):([^:]+)(?::(.+))?")

GENERIC_TYPES = {
    "sysfs",
    "proc",
    "debugfs",
    "tracefs",
    "rootfs",
    "device",
    "unlabeled",
    "default_prop",
    "vendor_default_prop",
    "default_android_service",
    "default_android_hwservice",
    "default_android_vndservice",
    "socket_device",
    "system_data_file",
    "vendor_file",
}

SENSITIVE_PERMS = {
    "write",
    "create",
    "add_name",
    "remove_name",
    "execute",
    "execute_no_trans",
    "mounton",
    "set",
    "add",
    "ioctl",
    "sys_admin",
    "dac_override",
    "dac_read_search",
    "sys_module",
    "sys_rawio",
}


@dataclass(frozen=True)
class Denial:
    perms: str
    scontext: str
    tcontext: str
    tclass: str
    source_type: str
    target_type: str
    comm: str = ""
    path: str = ""
    name: str = ""
    property: str = ""
    service: str = ""
    pid: str = ""
    raw: str = ""


@dataclass
class PatternSummary:
    count: int
    perms: str
    source_type: str
    target_type: str
    tclass: str
    examples: list[str]
    comms: dict[str, int]
    paths: dict[str, int]
    names: dict[str, int]
    properties: dict[str, int]
    services: dict[str, int]
    classification: str
    guidance: list[str]


def split_context_type(ctx: str) -> str:
    m = CONTEXT_PAT.match(ctx)
    return m.group(3) if m else ctx


def parse_kv(rest: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, val in KV_PAT.findall(rest):
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        out[key] = val
    return out


def parse_denials(lines: Iterable[str]) -> list[Denial]:
    denials: list[Denial] = []
    for line in lines:
        m = AVC_PAT.search(line)
        if not m:
            continue
        perms = " ".join(m.group(1).split())
        rest = m.group(2)
        kv = parse_kv(rest)
        scontext = kv.get("scontext", "")
        tcontext = kv.get("tcontext", "")
        tclass = kv.get("tclass", "")
        denials.append(
            Denial(
                perms=perms,
                scontext=scontext,
                tcontext=tcontext,
                tclass=tclass,
                source_type=split_context_type(scontext),
                target_type=split_context_type(tcontext),
                comm=kv.get("comm", ""),
                path=kv.get("path", ""),
                name=kv.get("name", ""),
                property=kv.get("property", ""),
                service=kv.get("service", kv.get("name", "")) if "service" in rest else kv.get("service", ""),
                pid=kv.get("pid", ""),
                raw=line.rstrip(),
            )
        )
    return denials


def classify(perms: str, source_type: str, target_type: str, tclass: str, sample: Denial) -> tuple[str, list[str]]:
    perm_set = set(perms.split())
    guidance: list[str] = []

    if target_type in GENERIC_TYPES:
        guidance.append(f"Target type `{target_type}` is generic/catch-all; prefer relabeling the object before adding an allow rule.")

    if source_type == "init":
        guidance.append("Source is `init`; confirm the service has its own executable label and daemon domain before granting init access.")

    if tclass == "property_service" or sample.property:
        guidance.extend(
            [
                "Classify the property owner: system/product/system_ext/vendor/odm.",
                "Fix `property_contexts` and property placement first; use `get_prop()`/`set_prop()` only after ownership is correct.",
                "Avoid granting access to `default_prop` or `vendor_default_prop`.",
            ]
        )
        return "property ownership/label", guidance

    if tclass in {"service_manager", "hwservice_manager", "vndservice_manager"}:
        guidance.extend(
            [
                "Add or correct the specific service context entry.",
                "Use the correct service/HAL client/server pattern; avoid default service labels.",
            ]
        )
        return "service label/client-server relationship", guidance

    if tclass in {"file", "dir", "lnk_file", "chr_file", "blk_file", "sock_file", "fifo_file"}:
        if sample.path.startswith("/sys") or target_type.startswith("sysfs"):
            guidance.extend(
                [
                    "Treat this as a sysfs labeling problem first.",
                    "Search for an existing `sysfs_*` type; otherwise add a narrow `genfscon` and grant access to that type only.",
                ]
            )
            return "sysfs label", guidance
        if sample.path.startswith("/proc") or target_type.startswith("proc"):
            guidance.extend(
                [
                    "Treat this as a procfs labeling problem first.",
                    "Use a narrow `proc_*` type in `genfs_contexts` where possible.",
                ]
            )
            return "proc label", guidance
        if sample.path.startswith("/dev") or tclass in {"chr_file", "blk_file"}:
            guidance.extend(
                [
                    "Check `ueventd*.rc` DAC permissions and `file_contexts` label for the device node.",
                    "Prefer a narrow `dev_type` label over generic `device` access.",
                ]
            )
            return "device node label", guidance
        if "execute" in perm_set or "execute_no_trans" in perm_set:
            guidance.extend(
                [
                    "Check executable file label and domain transition.",
                    "For init services, use an `_exec` type plus `init_daemon_domain()` instead of `execute_no_trans`.",
                ]
            )
            return "executable/domain transition", guidance
        guidance.append("Confirm the object label is precise, then grant the narrowest read/write/create permission needed.")
        return "file access", guidance

    if tclass == "process":
        guidance.extend(
            [
                "Process denials often indicate a wrong domain transition or an over-privileged debug interaction.",
                "Avoid broad process permissions until executable labels and transitions are correct.",
            ]
        )
        return "process/domain transition", guidance

    if tclass in {"capability", "capability2"} or perm_set & {"sys_admin", "dac_override", "sys_module", "sys_rawio"}:
        guidance.extend(
            [
                "Capability grants need design review; check whether the operation can move to an existing privileged service.",
                "Check neverallow rules before adding capability access.",
            ]
        )
        return "capability/design review", guidance

    if "binder" in tclass:
        guidance.append("Use Binder/HAL relationship macros where appropriate; verify service labels and intended client/server boundary.")
        return "binder relationship", guidance

    if "socket" in tclass:
        guidance.append("Check socket label and intended owner; prefer `unix_socket_connect()` or existing socket macros when applicable.")
        return "socket relationship", guidance

    if perm_set & SENSITIVE_PERMS:
        guidance.append("Sensitive permission present; verify ownership and label before granting.")

    if not guidance:
        guidance.append("No strong classification. Inspect actor, object, label, and existing AOSP policy before adding rules.")
    return "unclassified", guidance


def summarize(denials: list[Denial], top: int) -> tuple[list[PatternSummary], dict[str, dict[str, int]]]:
    grouped: dict[tuple[str, str, str, str], list[Denial]] = defaultdict(list)
    for d in denials:
        grouped[(d.perms, d.source_type, d.target_type, d.tclass)].append(d)

    summaries: list[PatternSummary] = []
    for (perms, source_type, target_type, tclass), items in grouped.items():
        sample = items[0]
        classification, guidance = classify(perms, source_type, target_type, tclass, sample)
        summaries.append(
            PatternSummary(
                count=len(items),
                perms=perms,
                source_type=source_type,
                target_type=target_type,
                tclass=tclass,
                examples=[d.raw for d in items[:3]],
                comms=dict(Counter(d.comm for d in items if d.comm).most_common(10)),
                paths=dict(Counter(d.path for d in items if d.path).most_common(10)),
                names=dict(Counter(d.name for d in items if d.name).most_common(10)),
                properties=dict(Counter(d.property for d in items if d.property).most_common(10)),
                services=dict(Counter(d.service for d in items if d.service).most_common(10)),
                classification=classification,
                guidance=guidance,
            )
        )

    summaries.sort(key=lambda s: (-s.count, s.source_type, s.target_type, s.tclass))
    totals = {
        "comms": dict(Counter(d.comm for d in denials if d.comm).most_common(top)),
        "paths": dict(Counter(d.path for d in denials if d.path).most_common(top)),
        "names": dict(Counter(d.name for d in denials if d.name).most_common(top)),
        "properties": dict(Counter(d.property for d in denials if d.property).most_common(top)),
        "services": dict(Counter(d.service for d in denials if d.service).most_common(top)),
        "source_types": dict(Counter(d.source_type for d in denials if d.source_type).most_common(top)),
        "target_types": dict(Counter(d.target_type for d in denials if d.target_type).most_common(top)),
        "classes": dict(Counter(d.tclass for d in denials if d.tclass).most_common(top)),
    }
    return summaries[:top], totals


def emit_text(total: int, summaries: list[PatternSummary], totals: dict[str, dict[str, int]]) -> None:
    print(f"TOTAL_DENIAL_LINES\t{total}")
    print("TOP_PATTERNS")
    for s in summaries:
        print(f"{s.count}\t{{{s.perms}}}\t{s.source_type}\t{s.target_type}\t{s.tclass}\t{s.classification}")
        for g in s.guidance[:3]:
            print(f"  HINT\t{g}")
    for section, data in totals.items():
        print(section.upper())
        for key, n in data.items():
            print(f"{n}\t{key}")


def emit_markdown(total: int, summaries: list[PatternSummary], totals: dict[str, dict[str, int]]) -> None:
    print("# SELinux Denial Summary\n")
    print(f"Total parsed AVC denial lines: **{total}**\n")
    if total == 0:
        print("No AVC denials matched. Check whether the input contains `avc: denied` lines or use full `logcat -b all`/`dmesg` capture.")
        return
    print("## Top denial patterns\n")
    for idx, s in enumerate(summaries, 1):
        print(f"### {idx}. `{s.source_type}` → `{s.target_type}` `{s.tclass}` ({s.count}x)\n")
        print(f"- **Perms:** `{{ {s.perms} }}`")
        print(f"- **Classification:** {s.classification}")
        if s.comms:
            print(f"- **Commands:** {', '.join(f'`{k}` ({v})' for k, v in s.comms.items())}")
        if s.paths:
            print(f"- **Paths:** {', '.join(f'`{k}` ({v})' for k, v in s.paths.items())}")
        if s.properties:
            print(f"- **Properties:** {', '.join(f'`{k}` ({v})' for k, v in s.properties.items())}")
        if s.services:
            print(f"- **Services:** {', '.join(f'`{k}` ({v})' for k, v in s.services.items())}")
        print("- **Guidance:**")
        for g in s.guidance:
            print(f"  - {g}")
        print("- **Example:**")
        print("```text")
        print(s.examples[0])
        print("```\n")

    print("## Hotspots\n")
    for section, data in totals.items():
        if not data:
            continue
        print(f"### {section.replace('_', ' ').title()}")
        for key, n in data.items():
            print(f"- `{key}`: {n}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", nargs="?", help="Log or denial file. Reads stdin if omitted.")
    ap.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    if args.input:
        lines = Path(args.input).read_text(errors="ignore").splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    denials = parse_denials(lines)
    summaries, totals = summarize(denials, args.top)

    if args.format == "json":
        print(json.dumps({"total": len(denials), "patterns": [asdict(s) for s in summaries], "totals": totals}, indent=2, sort_keys=True))
    elif args.format == "markdown":
        emit_markdown(len(denials), summaries, totals)
    else:
        emit_text(len(denials), summaries, totals)
    return 0 if denials else 1


if __name__ == "__main__":
    raise SystemExit(main())
