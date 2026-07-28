
# Skills

All installable skill packages in this repository live here. Each subdirectory is an independent skill installable via `npx skills add`.

## Available skills

| Skill | Description |
|---|---|
| [rom](rom/README.md) | Build custom AOSP/LineageOS ROMs from a device tree and manifest (repo sync, lunch/breakfast, mka, build failure reading) |
| [kernel](kernel/README.md) | Build legacy/monolithic device kernels (defconfig, make, boot image packaging, AnyKernel3 for non-GKI) |
| [gki-kernel](gki-kernel/README.md) | Build Generic Kernel Image (GKI) kernels with build.sh or Bazel/Kleaf, including KernelSU-Next integration |
| [debug](debug/README.md) | Evidence-first diagnosis of Android devices -- bootloops, crashes, ANRs, kernel panics, HAL issues, service deaths |
| [selinux-repair](selinux-repair/README.md) | Repair SELinux policy build failures and runtime AVC denials -- build error triage, property context collision, least-privilege patch shapes |
| [port-rom](port-rom/README.md) | Adapt stock/OEM firmware (Transsion/XOS) to a custom ROM base -- image extraction, partition strategy, vendor 64-bit conversion, boot fixes |
| [module](module/README.md) | Build Magisk, KernelSU/KSU-Next modules and AnyKernel3 flashable ZIPs -- system overlays, lifecycle hooks, Zygisk, WebUI, SELinux rules |

## Install

### Install one skill

```bash
npx skills add D1ZZY4/android-development-skills --skill rom
npx skills add D1ZZY4/android-development-skills --skill kernel
npx skills add D1ZZY4/android-development-skills --skill gki-kernel
# etc.
```

### Install multiple specific skills at once

```bash
npx skills add D1ZZY4/android-development-skills --skill rom --skill kernel --skill gki-kernel
```

### Install all skills from this repo

```bash
npx skills add D1ZZY4/android-development-skills --all
```

### List available skills before installing

```bash
npx skills add D1ZZY4/android-development-skills --list
```

### Cross-skill relationships

These skills are designed as independent packages. When a task crosses domains (e.g. a SELinux denial found during debugging), the agent should route to the appropriate skill. Each skill's AGENTS.md includes cross-references to related skills in its Quick Decision Aid.
