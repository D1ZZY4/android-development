#!/usr/bin/env python3
"""Classify Android SELinux build/verifier failures.

The script intentionally focuses on the *first* actionable failure. Parallel
Android builds often emit many cascading errors after the real root cause.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Pattern


@dataclass
class Rule:
    label: str
    pattern: Pattern[str]
    cause: str
    fix: str
    references: list[str]
    severity: str = "error"


@dataclass
class Finding:
    label: str
    severity: str
    detail: str
    line_number: int
    line: str
    cause: str
    fix: str
    references: list[str]


RULES: list[Rule] = [
    Rule(
        "duplicate_property_prefix",
        re.compile(r"Duplicate prefix match detected for ['\"]([^'\"]+)['\"]", re.I),
        "Merged property_contexts contains the same prefix trie slot more than once. Parallel init rc failures are usually cascading symptoms of this one root cause.",
        "Find all property_contexts entries for the reported prefix, keep one owner, remove stale duplicates, or narrow broad prefixes to exact entries. Do not change .te allow rules for this class.",
        ["references/build-error-playbook.md", "references/common-fixes.md", "references/policy-compatibility.md"],
    ),
    Rule(
        "duplicate_property_exact",
        re.compile(r"Duplicate exact match detected for ['\"]([^'\"]+)['\"]", re.I),
        "Merged property_contexts contains the same exact property entry more than once.",
        "Grep the exact property in all source and generated property_contexts, keep one mapping, and remove or de-duplicate inherited overlays.",
        ["references/build-error-playbook.md", "references/common-fixes.md", "references/policy-compatibility.md"],
    ),
    Rule(
        "duplicate_type_declaration",
        re.compile(r"(?:Duplicate declaration of type|duplicate declaration.*?\btype\b|already declared.*?\btype\b)", re.I),
        "A SELinux type is declared twice after the policy sources are merged.",
        "Do not redeclare an existing type such as `vendor_camera_prop`. Reuse the existing type in property_contexts or rename the local type and update every reference.",
        ["references/build-error-playbook.md", "references/policy-compatibility.md", "references/policy-review-gates.md"],
    ),
    Rule(
        "duplicate_attribute_declaration",
        re.compile(r"(?:Duplicate declaration of attribute|duplicate declaration.*?\battribute\b|already declared.*?\battribute\b)", re.I),
        "A SELinux attribute is declared twice after the policy sources are merged.",
        "Remove the local redeclaration or rename the local attribute. Vendor-specific symbols should be namespaced to avoid collisions.",
        ["references/build-error-playbook.md", "references/policy-compatibility.md", "references/policy-review-gates.md"],
    ),
    Rule(
        "duplicate_context_spec",
        re.compile(r"Multiple different specifications for (?:.+?:)?\s*([^\s]+)|Multiple same specifications for\s+([^\s]+)", re.I),
        "A context file has duplicate or conflicting mappings after merge.",
        "Find all context entries for the path/property/service. Keep one owner and remove broad or stale duplicate mappings.",
        ["references/device-tree-remediation-checklist.md", "references/policy-review-gates.md"],
    ),
    Rule(
        "property_info_serializer",
        re.compile(r"property_info_serializer|BuildTrie|property info|Unable to serialize property contexts", re.I),
        "Property context serialization failed, usually due to duplicate exact/prefix entries, bad value type, or invalid exact/prefix form.",
        "Run `property_context_doctor.py` against the build log or generated property_contexts, then fix source property_contexts before changing .te policy.",
        ["references/build-error-playbook.md", "references/common-fixes.md", "references/device-tree-remediation-checklist.md"],
    ),
    Rule(
        "host_init_verifier",
        re.compile(r"host_init_verifier|Failed to parse init|init verifier", re.I),
        "Init rc/property/service verification failed before policy is usable.",
        "Inspect the specific verifier message. If it says duplicate property contexts, fix property_contexts; if it says unknown user/group/service, fix rc/passwd/service labels.",
        ["references/build-error-playbook.md", "references/implement-selinux.md", "references/device-tree-remediation-checklist.md"],
    ),
    Rule(
        "neverallow",
        re.compile(r"neverallow|violated by allow|libsepol\.report_failure", re.I),
        "The policy violates an Android security invariant.",
        "Redesign placement/domain/label. Do not bypass with SELINUX_IGNORE_NEVERALLOWS or copy broad allow rules.",
        ["references/customize-selinux.md", "references/policy-review-gates.md"],
    ),
    Rule(
        "unknown_type_or_attribute",
        re.compile(r"(?:unknown|undefined|Failed to resolve)\s+(?:type|attribute|identifier|typeattributeset)\s+['\"]?([A-Za-z0-9_.$-]+)", re.I),
        "Policy references a symbol that is not declared or not visible from this policy partition.",
        "Check whether the symbol is local or public/exported. Vendor policy must not depend on platform-private types.",
        ["references/policy-compatibility.md", "references/build-selinux-policy.md", "references/research-notes-2026.md"],
    ),
    Rule(
        "duplicate_declaration",
        re.compile(r"(?:duplicate declaration|already declared|Duplicate declaration)", re.I),
        "A type/attribute or context object is declared twice after merged policy ordering.",
        "Remove the local redeclaration or rename the local symbol. Inspect generated *_sepolicy.conf intermediates if ordering is unclear.",
        ["references/build-error-playbook.md", "references/build-selinux-policy.md", "references/policy-review-gates.md"],
    ),
    Rule(
        "checkfc_or_invalid_context",
        re.compile(r"checkfc|invalid context|not a valid context|type .* is not defined|line .*contexts", re.I),
        "A context file refers to an undeclared type or malformed SELinux context.",
        "Declare the object type in the same policy surface that owns the context file, or fix the context syntax/type attributes.",
        ["references/implement-selinux.md", "references/common-fixes.md"],
    ),
    Rule(
        "sepolicy_tests_attribute",
        re.compile(r"sepolicy_tests|must have attribute|does not have attribute|Required attribute", re.I),
        "A type is missing required Android policy attributes such as file_type, sysfs_type, proc_type, dev_type, or partition-specific file type.",
        "Add the correct type attribute or relabel the object to an existing type that already has it.",
        ["references/policy-compatibility.md", "references/common-fixes.md"],
    ),
    Rule(
        "syntax_or_m4",
        re.compile(r"syntax error|unrecognized character|m4:|Error while expanding policy|unterminated|error\(s\) encountered while parsing configuration", re.I),
        "Policy source syntax or macro expansion failed.",
        "Inspect the exact line and generated intermediate policy. Check missing newline, bad macro argument, braces, and comments.",
        ["references/build-selinux-policy.md", "references/policy-review-gates.md"],
    ),
    Rule(
        "runtime_avc_in_build_log",
        re.compile(r"avc:\s*denied", re.I),
        "A runtime denial was found in the log, not necessarily a build blocker.",
        "Run summarize_denials.py and classify actor/object/label before writing policy.",
        ["references/denial-decision-tree.md", "references/write-selinux-policy.md"],
        severity="warning",
    ),
]


def load_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(errors="ignore")
    return sys.stdin.read()


def find_first(text: str) -> Finding | None:
    lines = text.splitlines()
    for idx, line in enumerate(lines, 1):
        for rule in RULES:
            m = rule.pattern.search(line)
            if not m:
                continue
            detail = next((g for g in m.groups() if g), "") if m.groups() else ""
            if not detail and rule.label in {"duplicate_type_declaration", "duplicate_attribute_declaration", "duplicate_declaration"}:
                # checkpolicy often reports "Duplicate declaration of type" on one
                # line and the actual `type foo, ...;` line immediately after it.
                window = line + "\n" + "\n".join(lines[idx: min(len(lines), idx + 4)])
                mm = re.search(r"\b(?:type|attribute)\s+([A-Za-z0-9_.$-]+)\b", window)
                if mm:
                    detail = mm.group(1)
            if not detail:
                detail = line.strip()[:240]
            return Finding(
                label=rule.label,
                severity=rule.severity,
                detail=detail,
                line_number=idx,
                line=line.rstrip(),
                cause=rule.cause,
                fix=rule.fix,
                references=rule.references,
            )
    return None


def emit_text(f: Finding | None) -> None:
    if f is None:
        print("CLASS\tunknown")
        print("SEVERITY\tunknown")
        print("HINT\tNo known SELinux failure pattern matched. Inspect the first failing command and generated intermediates manually.")
        return
    print(f"CLASS\t{f.label}")
    print(f"SEVERITY\t{f.severity}")
    print(f"LINE\t{f.line_number}")
    print(f"DETAIL\t{f.detail}")
    print(f"CAUSE\t{f.cause}")
    print(f"FIX\t{f.fix}")
    print("REFERENCES\t" + ", ".join(f.references))
    print(f"RAW\t{f.line}")


def emit_markdown(f: Finding | None) -> None:
    if f is None:
        print("# SELinux Build Error Triage\n")
        print("No known pattern matched. Inspect the first failing command and generated intermediates manually.")
        return
    print("# SELinux Build Error Triage\n")
    print(f"- **Class:** `{f.label}`")
    print(f"- **Severity:** `{f.severity}`")
    print(f"- **Line:** {f.line_number}")
    print(f"- **Detail:** `{f.detail}`")
    print(f"- **Likely cause:** {f.cause}")
    print(f"- **Safer fix path:** {f.fix}")
    print("- **Read next:**")
    for ref in f.references:
        print(f"  - `{ref}`")
    print("\n```text")
    print(f.line)
    print("```")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", nargs="?", help="Build log path. Reads stdin when omitted.")
    ap.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    args = ap.parse_args()

    finding = find_first(load_text(args.log))
    if args.format == "json":
        print(json.dumps(asdict(finding) if finding else {"label": "unknown"}, indent=2, sort_keys=True))
    elif args.format == "markdown":
        emit_markdown(finding)
    else:
        emit_text(finding)
    return 0 if finding is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
