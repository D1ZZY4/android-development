#!/usr/bin/env python3
"""Static audit for Android device-tree SELinux bring-up risks."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {
    ".mk", ".bp", ".te", ".cil", ".rc", ".prop", ".xml", ".conf", ".txt", ".contexts", "",
}
CONTEXT_BASENAMES = {
    "file_contexts",
    "genfs_contexts",
    "property_contexts",
    "service_contexts",
    "hwservice_contexts",
    "vndservice_contexts",
    "seapp_contexts",
    "keystore2_key_contexts",
}

FRAMEWORK_PROP_PREFIXES = (
    "ro.product.", "ro.bootanim.", "ro.setupwizard.", "remote_provisioning.",
    "persist.arm64.memtag.", "persist.sys.", "persist.service.", "dalvik.",
    "debug.hwui.", "ro.system.", "ro.product.", "ro.build.", "ro.config.",
)
VENDOR_PROP_OK_PREFIXES = (
    "ro.vendor.", "persist.vendor.", "vendor.", "ro.odm.", "persist.odm.", "odm.",
)
RISKY_PROP_PREFIXES = (
    "ro.", "persist.", "ctl.", "sys.", "service.", "debug.", "vendor.", "ro.vendor.",
    "persist.vendor.", "ro.vendor.audio.", "vendor.audio.", "vendor.stream", "ro.vendor.mediatek.",
)
GENERIC_TARGETS = {
    "sysfs", "proc", "debugfs", "tracefs", "rootfs", "device", "unlabeled",
    "default_prop", "vendor_default_prop", "default_android_service", "default_android_hwservice",
    "default_android_vndservice", "socket_device", "system_data_file", "vendor_file", "app_data_file",
}
SENSITIVE_CAPS = {
    "sys_admin", "sys_module", "sys_rawio", "dac_override", "dac_read_search", "net_admin",
    "setuid", "setgid", "mknod", "chown", "fowner", "kill", "sys_ptrace",
}
DEPRECATED_VARS = {
    "BOARD_PLAT_PUBLIC_SEPOLICY_DIR": "SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS or PRODUCT_PUBLIC_SEPOLICY_DIRS",
    "BOARD_PLAT_PRIVATE_SEPOLICY_DIR": "SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS or PRODUCT_PRIVATE_SEPOLICY_DIRS",
    "BOARD_SEPOLICY_DIRS": "BOARD_VENDOR_SEPOLICY_DIRS (or BOARD_ODM_SEPOLICY_DIRS for odm policy)",
}
PROPERTY_OVERRIDE_VARS = {
    "PRODUCT_PROPERTY_OVERRIDES",
    "ADDITIONAL_BUILD_PROPERTIES",
    "PRODUCT_DEFAULT_PROPERTY_OVERRIDES",
}


@dataclass
class Finding:
    severity: str
    code: str
    path: str
    line: int
    evidence: str
    recommendation: str


def safe_read(path: Path) -> str:
    try:
        return path.read_text(errors="ignore")
    except Exception:
        return ""


def is_text_file(path: Path) -> bool:
    if path.name in CONTEXT_BASENAMES or path.name.startswith("fstab") or path.name.startswith("ueventd"):
        return True
    return path.suffix in TEXT_SUFFIXES


def iter_files(root: Path) -> Iterable[Path]:
    skip = {".git", "out", ".repo", "node_modules", "prebuilts", "kernel", "vendor_dlkm", "system_dlkm"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip for part in path.parts):
            continue
        if is_text_file(path):
            yield path


def add(findings: list[Finding], severity: str, code: str, path: Path, line: int, evidence: str, rec: str) -> None:
    findings.append(Finding(severity, code, str(path), line, evidence.strip(), rec))


def scan_final_newlines(files: list[Path], findings: list[Finding]) -> None:
    for path in files:
        if path.suffix not in {".te", ".cil"} and path.name not in CONTEXT_BASENAMES:
            continue
        try:
            data = path.read_bytes()
        except Exception:
            continue
        if data and not data.endswith(b"\n"):
            add(findings, "warning", "missing_final_newline", path, 0, path.name, "Add a final newline; Android sepolicy files are concatenated during build and missing newlines make failures harder to debug.")


def scan_makefiles(files: list[Path], findings: list[Finding]) -> None:
    var_pat = re.compile(r"\b([A-Z0-9_]*SEPOLICY[A-Z0-9_]*|PRODUCT_PROPERTY_OVERRIDES|ADDITIONAL_BUILD_PROPERTIES|PRODUCT_DEFAULT_PROPERTY_OVERRIDES)\b")
    for path in files:
        if path.suffix not in {".mk", ".bp"} and path.name not in {"BoardConfig.mk", "device.mk", "product.mk"}:
            continue
        for idx, line in enumerate(safe_read(path).splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for m in var_pat.finditer(line):
                var = m.group(1)
                if var in DEPRECATED_VARS:
                    add(findings, "warning", "deprecated_sepolicy_variable", path, idx, stripped, f"Prefer {DEPRECATED_VARS[var]}; verify this is not relying on pre-Android-8 policy behavior.")
                if var in PROPERTY_OVERRIDE_VARS:
                    add(findings, "warning", "legacy_property_override_variable", path, idx, stripped, "Prefer partition-specific PRODUCT_SYSTEM_PROPERTIES / PRODUCT_PRODUCT_PROPERTIES / PRODUCT_VENDOR_PROPERTIES or TARGET_*_PROP where supported.")
            if "SELINUX_IGNORE_NEVERALLOWS" in stripped:
                add(findings, "critical", "ignore_neverallows", path, idx, stripped, "Do not rely on SELINUX_IGNORE_NEVERALLOWS. It cannot be used for final user policy and does not solve CTS/VTS compatibility.")


def scan_props(files: list[Path], findings: list[Finding]) -> None:
    prop_file_pat = re.compile(r"(^|/)(vendor|odm)\.prop$|/configs/properties/(vendor|odm)\.prop$")
    for path in files:
        if path.suffix != ".prop" and not prop_file_pat.search(str(path)):
            continue
        is_vendor_prop = bool(prop_file_pat.search(str(path))) or "vendor" in path.parts or "odm" in path.parts
        for idx, line in enumerate(safe_read(path).splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key = stripped.split("=", 1)[0].strip()
            if is_vendor_prop and key.startswith(FRAMEWORK_PROP_PREFIXES) and not key.startswith(VENDOR_PROP_OK_PREFIXES):
                add(findings, "error", "framework_property_in_vendor_prop", path, idx, key, "Move framework/product/system properties out of vendor/odm prop files instead of granting vendor_init permission to set them.")
            if key.startswith("ctl."):
                add(findings, "warning", "ctl_property_in_prop_file", path, idx, key, "Control properties are normally runtime init controls; verify this is intentional and correctly labeled.")


def parse_context_type(context: str) -> str:
    parts = context.split(":")
    return parts[2] if len(parts) >= 3 else ""


def scan_property_contexts(files: list[Path], findings: list[Finding]) -> None:
    entries: list[tuple[str, str, Path, int, str]] = []
    for path in files:
        if path.name != "property_contexts":
            continue
        for idx, line in enumerate(safe_read(path).splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                add(findings, "error", "malformed_property_context", path, idx, stripped, "Property context lines need property name/prefix and SELinux context.")
                continue
            key, ctx = parts[0], parts[1]
            typ = parse_context_type(ctx)
            entries.append((key, typ, path, idx, stripped))
            exactness = " ".join(parts[2:])
            if typ in {"default_prop", "vendor_default_prop"}:
                add(findings, "error", "default_property_type", path, idx, stripped, "Use a specific property type instead of default_prop/vendor_default_prop.")
            if key in {"ro.", "persist.", "vendor.", "ro.vendor.", "persist.vendor.", "sys.", "debug."} or (key.endswith(".") and key.startswith(RISKY_PROP_PREFIXES)):
                add(findings, "warning", "broad_property_prefix", path, idx, stripped, "Broad property prefixes often collide with inherited policy. Prefer exact entries unless this tree owns the full family.")
            if "exact" not in exactness and not key.endswith(".") and key.count(".") >= 2:
                add(findings, "info", "property_context_exactness_unspecified", path, idx, stripped, "Consider adding explicit `exact` for singleton properties to avoid accidental prefix behavior on older branches.")

    # Duplicate exact keys and local prefix overlaps.
    by_key: dict[str, list[tuple[str, Path, int, str]]] = defaultdict(list)
    for key, typ, path, idx, stripped in entries:
        by_key[key].append((typ, path, idx, stripped))
    for key, vals in by_key.items():
        types = {v[0] for v in vals}
        if len(vals) > 1 and len(types) > 1:
            for typ, path, idx, stripped in vals:
                add(findings, "error", "duplicate_property_context_key", path, idx, stripped, f"Property `{key}` maps to multiple types after local scan: {', '.join(sorted(types))}.")

    sorted_entries = sorted(entries, key=lambda e: len(e[0]))
    for prefix, prefix_type, ppath, pidx, pstr in sorted_entries:
        if not prefix.endswith("."):
            continue
        for key, typ, path, idx, stripped in entries:
            if key == prefix:
                continue
            if key.startswith(prefix) and typ != prefix_type:
                add(findings, "warning", "property_prefix_overlap", path, idx, stripped, f"Overlaps prefix `{prefix}` at {ppath}:{pidx} with different type `{prefix_type}`. Exact entries may be safer.")


def scan_context_files(files: list[Path], findings: list[Finding]) -> None:
    for path in files:
        if path.name not in CONTEXT_BASENAMES - {"property_contexts"}:
            continue
        for idx, line in enumerate(safe_read(path).splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if path.name == "genfs_contexts":
                ctx = parts[2] if len(parts) >= 3 else ""
            else:
                ctx = parts[1] if len(parts) >= 2 else ""
            typ = parse_context_type(ctx)
            if typ in GENERIC_TARGETS:
                add(findings, "warning", "generic_context_label", path, idx, stripped, f"Context maps object to generic type `{typ}`. Use a narrower type when this is a new object.")
            if path.name == "file_contexts" and re.match(r"^/(sys|proc|dev)(/\.\*)?\??\s", stripped):
                add(findings, "warning", "broad_file_context_regex", path, idx, stripped, "Broad /sys, /proc, or /dev regexes can mask labeling bugs; prefer narrow entries.")


def extract_te_types(line: str) -> tuple[str, str, str] | None:
    m = re.match(r"\s*allow\s+([^\s]+)\s+([^:\s]+):([^\s]+)\s+(.+?);", line)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def scan_te(files: list[Path], findings: list[Finding]) -> None:
    for path in files:
        if path.suffix not in {".te", ".cil"}:
            continue
        for idx, line in enumerate(safe_read(path).splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if re.match(r"permissive\s+[A-Za-z0-9_]+\s*;", stripped):
                add(findings, "critical", "permissive_domain", path, idx, stripped, "Per-domain permissive must be temporary and removed before final/user policy.")
            if stripped.startswith("dontaudit "):
                add(findings, "warning", "dontaudit_rule", path, idx, stripped, "Do not hide bring-up denials with dontaudit unless the denial is understood and intentionally non-actionable.")
            if "unconfineddomain" in stripped:
                add(findings, "critical", "unconfined_domain", path, idx, stripped, "Unconfined domains defeat SELinux compartmentalization and should not be used for device bring-up.")
            if "execute_no_trans" in stripped:
                add(findings, "error", "execute_no_trans", path, idx, stripped, "Fix executable label/domain transition instead of granting execute_no_trans.")
            te = extract_te_types(line)
            if te:
                src, target, klass = te
                if target in GENERIC_TARGETS:
                    add(findings, "error", "generic_allow_target", path, idx, stripped, f"Avoid allowing access to generic target `{target}`; relabel the object to a narrow type first.")
                if klass in {"capability", "capability2"} and any(cap in stripped for cap in SENSITIVE_CAPS):
                    add(findings, "warning", "sensitive_capability", path, idx, stripped, "Capability grants need design review and may violate neverallow rules.")
                if src in {"domain", "appdomain"}:
                    add(findings, "warning", "broad_source_attribute_allow", path, idx, stripped, "Allow rules from broad source attributes should be avoided in device policy unless matching an upstream pattern.")
            if re.search(r"\ballowxperm\b", stripped) and "ioctl" in stripped:
                add(findings, "warning", "ioctl_xperm_rule", path, idx, stripped, "Review ioctl allowxperm carefully; prefer named/narrow ioctl sets and avoid broad ioctl permissions.")


def scan_init_rc(files: list[Path], findings: list[Finding]) -> None:
    service_pat = re.compile(r"^service\s+(\S+)\s+(\S+)")
    setprop_pat = re.compile(r"\bsetprop\s+(\S+)\s+")
    chmod_pat = re.compile(r"\bchmod\s+([0-7]{3,4})\s+(\S+)")
    for path in files:
        if path.suffix != ".rc" and not path.name.endswith(".rc"):
            continue
        current_service: tuple[str, str, int] | None = None
        service_has_seclabel = False
        for idx, line in enumerate(safe_read(path).splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            sm = service_pat.match(stripped)
            if sm:
                if current_service and not service_has_seclabel:
                    name, exe, line_no = current_service
                    if exe.startswith(("/vendor/", "/odm/")):
                        add(findings, "info", "vendor_service_needs_domain_review", path, line_no, f"service {name} {exe}", "Ensure this service executable has a file_contexts `_exec` label and an init_daemon_domain transition; do not let it remain in init domain.")
                current_service = (sm.group(1), sm.group(2), idx)
                service_has_seclabel = False
                continue
            if current_service and stripped.startswith("seclabel "):
                service_has_seclabel = True
            sp = setprop_pat.search(stripped)
            if sp:
                prop = sp.group(1)
                if prop.startswith(FRAMEWORK_PROP_PREFIXES) and not prop.startswith(VENDOR_PROP_OK_PREFIXES):
                    add(findings, "warning", "vendor_init_sets_framework_property", path, idx, stripped, "Verify this rc file belongs to the partition that owns the property; avoid granting vendor_init framework property writes.")
            cm = chmod_pat.search(stripped)
            if cm:
                mode, target = cm.groups()
                if mode[-1] in {"2", "3", "6", "7"}:
                    add(findings, "warning", "world_writable_chmod", path, idx, stripped, "World-writable nodes are a DAC risk. Fix ownership/mode rather than compensating with SELinux.")
        if current_service and not service_has_seclabel:
            name, exe, line_no = current_service
            if exe.startswith(("/vendor/", "/odm/")):
                add(findings, "info", "vendor_service_needs_domain_review", path, line_no, f"service {name} {exe}", "Ensure this service executable has a file_contexts `_exec` label and an init_daemon_domain transition; do not let it remain in init domain.")


def collect_types(paths: Iterable[Path]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    type_pat = re.compile(r"^\s*type\s+([A-Za-z0-9_]+)\s*(?:,([^;]+))?;")
    attr_pat = re.compile(r"^\s*attribute\s+([A-Za-z0-9_]+)\s*;")
    for path in paths:
        for line in safe_read(path).splitlines():
            tm = type_pat.match(line)
            if tm:
                out[tm.group(1)].add(str(path))
            am = attr_pat.match(line)
            if am:
                out[am.group(1)].add(str(path))
    return out


def scan_private_boundary(files: list[Path], findings: list[Finding], aosp: Path | None) -> None:
    if not aosp:
        return
    public_dirs = [aosp / "public", aosp / "system_ext" / "public", aosp / "product" / "public"]
    private_dirs = [aosp / "private", aosp / "system_ext" / "private", aosp / "product" / "private"]
    public_files = [p for d in public_dirs if d.exists() for p in d.rglob("*.te")]
    private_files = [p for d in private_dirs if d.exists() for p in d.rglob("*.te")]
    public = collect_types(public_files)
    private = collect_types(private_files)
    private_only = set(private) - set(public)
    if not private_only:
        return
    token_pat = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
    for path in files:
        if path.suffix != ".te" or "vendor" not in str(path):
            continue
        for idx, line in enumerate(safe_read(path).splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for tok in token_pat.findall(stripped):
                if tok in private_only:
                    add(findings, "error", "vendor_references_platform_private_symbol", path, idx, stripped, f"`{tok}` appears private in the supplied AOSP sepolicy tree. Use public API or local vendor type.")
                    break


def severity_rank(sev: str) -> int:
    return {"critical": 0, "error": 1, "warning": 2, "info": 3}.get(sev, 9)


def emit_text(findings: list[Finding]) -> None:
    print(f"TOTAL_FINDINGS\t{len(findings)}")
    for f in findings:
        print(f"{f.severity.upper()}\t{f.code}\t{f.path}:{f.line}\t{f.evidence}")
        print(f"  FIX\t{f.recommendation}")


def emit_markdown(findings: list[Finding]) -> None:
    print("# Android SELinux Device Tree Audit\n")
    print(f"Total findings: **{len(findings)}**\n")
    if not findings:
        print("No high-confidence risky patterns found by the static audit. This does not prove the policy is correct; still run build and runtime gates.")
        return
    by_sev: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_sev[f.severity].append(f)
    for sev in ["critical", "error", "warning", "info"]:
        items = by_sev.get(sev, [])
        if not items:
            continue
        print(f"## {sev.title()} ({len(items)})\n")
        for f in items:
            loc = f"{f.path}:{f.line}" if f.line else f.path
            print(f"### `{f.code}`")
            print(f"- **Location:** `{loc}`")
            print(f"- **Evidence:** `{f.evidence}`")
            print(f"- **Recommendation:** {f.recommendation}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", default=".", help="Device tree or source subtree root")
    ap.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    ap.add_argument("--aosp-sepolicy", help="Optional path to AOSP system/sepolicy for public/private boundary checks")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Input not found: {root}", file=sys.stderr)
        return 2
    files = list(iter_files(root))
    findings: list[Finding] = []
    scan_final_newlines(files, findings)
    scan_makefiles(files, findings)
    scan_props(files, findings)
    scan_property_contexts(files, findings)
    scan_context_files(files, findings)
    scan_te(files, findings)
    scan_init_rc(files, findings)
    scan_private_boundary(files, findings, Path(args.aosp_sepolicy).resolve() if args.aosp_sepolicy else None)
    findings.sort(key=lambda f: (severity_rank(f.severity), f.path, f.line, f.code))

    if args.format == "json":
        print(json.dumps([asdict(f) for f in findings], indent=2, sort_keys=True))
    elif args.format == "markdown":
        emit_markdown(findings)
    else:
        emit_text(findings)
    return 1 if any(f.severity in {"critical", "error"} for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
