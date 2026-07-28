
# android-development Skill Maintainer Guide

This repository ships `skills/android-development/`, a [skills.sh](https://skills.sh)-compatible package for Android platform engineering. It is also usable by AI coding agents that read `AGENTS.md`.

## Working conventions

- Write repository and skill content in English without emojis.
- Communicate with the user in Indonesian unless they choose another language.
- Inspect the current repository before editing. This document is an orientation aid, not a substitute for the working tree.
- Use Context7 through `npx ctx7@latest` to verify each new or changed external Android, kernel, GKI, SELinux, Magisk, KernelSU, or AnyKernel3 command.
- Keep internal agent progress, tool logs, and verification tallies out of the installable skill package.

## Scope

The skill currently covers seven distinct domains:

| Domain | Folder | Purpose |
|---|---|---|
| ROM build | `rom/` | AOSP and LineageOS device-tree builds, manifests, lunch/breakfast, and `mka` |
| Kernel build | `kernel/` | Legacy or monolithic kernel configuration, compilation, and boot-image packaging |
| GKI kernel build | `gki-kernel/` | GKI/Kleaf builds, KMI/ABI concerns, and KernelSU-Next integration |
| Debug | `debug/` | Evidence-first diagnosis with logs, source inspection, and read-only ADB checks |
| SELinux repair | `selinux-repair/` | Policy build failures, runtime AVC denials, source-map resolution, and least-privilege repair |
| Port ROM | `port-rom/` | Stock/OEM firmware adaptation, partition strategy, and Transsion/XOS porting issues |
| Module | `module/` | Magisk, KernelSU/KSU-Next, and AnyKernel3 system-modification packages |

## Current package structure

```text
skills/android-development/
├── AGENTS.md
├── README.md
├── REFERENCE.md
├── SKILL.md
├── .gitignore
├── template/
│   ├── debug/
│   ├── gki-kernel/
│   ├── kernel/
│   ├── module/
│   │   ├── anykernel.sh.template
│   │   ├── boot-completed.sh.template
│   │   ├── module.prop.template
│   │   ├── post-fs-data.sh.template
│   │   ├── post-mount.sh.template
│   │   ├── sepolicy.rule.template
│   │   ├── service.sh.template
│   │   └── webroot-index.html.template
│   ├── port-rom/
│   ├── rom/
│   └── selinux-repair/
├── scripts/
│   ├── debug/
│   ├── gki-kernel/
│   ├── kernel/
│   ├── module/
│   │   └── verify_module.sh
│   ├── port-rom/
│   ├── rom/
│   └── selinux-repair/
│       └── tests/
└── references/
    ├── debug/                reserved for future guides
    ├── gki-kernel/
    ├── kernel/               reserved for future guides
    ├── module/
    │   ├── README.md
    │   ├── anykernel3-guide.md
    │   └── magisk-ksu-module-guide.md
    ├── port-rom/
    ├── rom/                  reserved for future guides
    └── selinux-repair/
```

Each domain has one matching folder in `template/`, `scripts/`, and `references/`. Reserved reference folders are intentional and must remain.

## Source material outside the package

`prompt/EnforcerGKI/` and `prompt/Fix NFC Transsion/` are workspace reference material, not distributable skill content. They demonstrate two module-domain use cases:

- An AnyKernel3 ZIP that targets GKI `vendor_boot` and patches
  `androidboot.selinux=enforcing`.
- A `system_ext` NFC-stack replacement containing app, library, and privileged app content.

Extract general, safe patterns from these examples. Do not copy their archives, binary payloads, or workspace-only material into `skills/android-development/`.

## Standing rules

### 1. Keep the public entry points synchronized

When a domain, packaged file, script, or user-facing command changes, update the relevant information in all four primary entry points:

| File | Keep current |
|---|---|
| `skills/android-development/AGENTS.md` | Domain router, workflow, file map, and Quick Decision Aid |
| `skills/android-development/REFERENCE.md` | The applicable command/reference section and decision aid |
| `skills/android-development/README.md` | Domain table, structure tree, safety notes, and test instructions |
| `README.md` | Repository overview and domain table |

Also update `skills/android-development/SKILL.md` when activation triggers, domain count, or its pointers change. It is intentionally a compact skills.sh entry point; do not duplicate workflows there.

### 2. Preserve domain boundaries

Do not flatten, rename, or merge domain folders. Keep AI routing and operating rules in `AGENTS.md`, exact commands and lookups in `REFERENCE.md`, human overview in the READMEs, and detailed topic material in `references/`.

### 3. Protect physical devices and policy integrity

- Never instruct or run a live-device mutation without the user's explicit confirmation. This includes flashing, erasing, rebooting to a special mode, writing a partition, enabling/disabling/removing a module, or applying an AnyKernel3 ZIP.
- Read-only inspection and workspace builds are allowed. When a device is relevant, discover it with read-only commands before assuming its state.
- Keep debug and SELinux conclusions evidence-first. Cite fresh logs, source, and read-only device evidence; use the existing insufficient-data fallback when evidence is missing.
- Never recommend permissive domains, `SELINUX_IGNORE_NEVERALLOWS := true`, generic-label allow rules, `dontaudit` to hide failures, or raw
  `audit2allow` output as a final fix.

### 4. Validate scripts before committing

Any change that touches `skills/android-development/scripts/` must pass all three checks:

```bash
find skills/android-development/scripts -name "*.sh" -exec bash -n {} \;
find skills/android-development/scripts -name "*.py" -exec python3 -m py_compile {} \;
bash skills/android-development/scripts/selinux-repair/tests/selftest.sh
```

Test new shell templates with `bash -n` too. Do not alter fixtures or test logic to manufacture a pass.

### 5. Keep the standalone `.gitignore` focused

`skills/android-development/.gitignore` is necessary because users can install the skill outside this workspace. It should ignore only skill-relevant generated artifacts: Python bytecode, Android build output, local repo metadata, captured diagnostics, package output, and non-fixture logs.

The exception below is mandatory so SELinux test fixtures stay tracked:

```gitignore
*.log
!scripts/**/tests/**/*.log
```

### 6. Commit discipline

Make one logical concern per Conventional Commit. Before every commit, read `.agents/rules/commit-discipline.md`, inspect the exact staged diff, and ensure the commit author is:

```text
D1ZZY4 <176969112+D1ZZY4@users.noreply.github.com>
```

Do not rewrite commits already published to `origin/main` without explicit user approval.

## Completion checklist

Before reporting a maintenance task as complete:

1. Re-read the user request and verify every named file and behavior.
2. Search for stale domain counts and outdated structure references.
3. Run the required script quality gates when scripts changed.
4. Check the working tree and review the final diff.
5. Keep the installable package free of internal tool notes and session
   metadata.
