# Reference Docs Index

Use these references as the skill's playbooks. Start with the source map docs when working on a device-tree build error.

## First-read docs

1. `policy-source-map.md` — resolve BoardConfig/include-derived SELinux roots before broad search.
2. `source-map-command-cookbook.md` — copy-paste commands for AOSP/Lineage/OEM trees.
3. `build-error-playbook.md` — classify and repair build-time SELinux failures.
4. `property-context-collision-guide.md` — repair duplicate exact/prefix property trie failures.
5. `common-fixes.md` — safe policy shapes and anti-patterns.
6. `policy-review-gates.md` — final review gates before declaring a fix done.

## Background snapshots

The bundled converted AOSP snapshots are useful for offline work, but prefer the live AOSP docs when internet access is available because policy split, compatibility, and release guidance change over time.

- `customize-selinux.md`
- `build-selinux-policy.md`
- `implement-selinux.md`
- `write-selinux-policy.md`
- `policy-compatibility.md`

## Specialist docs

- `boardconfig-first-workflow.md` — how the tools use BoardConfig and inherited `SEPolicy.mk` / `BoardConfigVendor.mk`.
- `device-tree-remediation-checklist.md` — review checklist for tree maintainers.
- `denial-decision-tree.md` — runtime AVC repair flow.
- `general-agent-integration.md` — how an AI/CI/IDE agent should use the skill.
