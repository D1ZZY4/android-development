
# android-development-skills

A collection of [skills.sh](https://skills.sh)-compatible skill packages for custom Android platform engineering. Installable individually or together into any AI coding agent that supports the Agent Skills convention.

## Skills available

| Skill | What it covers | Install |
|---|---|---|
| [rom-build](skills/rom/README.md) | AOSP/LineageOS ROM builds (repo sync, lunch, mka, build failures) | `npx skills add D1ZZY4/android-development-skills --skill rom` |
| [kernel-build](skills/kernel/README.md) | Legacy/monolithic device kernel builds (defconfig, make, boot.img) | `npx skills add D1ZZY4/android-development-skills --skill kernel` |
| [gki-kernel](skills/gki-kernel/README.md) | GKI kernel builds (build.sh, Bazel/Kleaf, KernelSU-Next) | `npx skills add D1ZZY4/android-development-skills --skill gki-kernel` |
| [debug](skills/debug/README.md) | Evidence-first device/boot diagnosis (logcat, dmesg, tombstones) | `npx skills add D1ZZY4/android-development-skills --skill debug` |
| [selinux-repair](skills/selinux-repair/README.md) | SELinux policy repair (build failures, AVC denials, property collisions) | `npx skills add D1ZZY4/android-development-skills --skill selinux-repair` |
| [port-rom](skills/port-rom/README.md) | Stock/OEM firmware porting (Transsion/XOS, partition strategy) | `npx skills add D1ZZY4/android-development-skills --skill port-rom` |
| [module](skills/module/README.md) | Magisk/KernelSU modules, AnyKernel3 ZIPs (overlays, hooks, WebUI) | `npx skills add D1ZZY4/android-development-skills --skill module` |

### Install all skills

```bash
npx skills add D1ZZY4/android-development-skills --all
```

### List available skills

```bash
npx skills add D1ZZY4/android-development-skills --list
```

## Cloning this repository

This repository uses **Git LFS** to store binary assets (APK files, `.so` blobs, etc.). Clone with:

```bash
# Preferred -- with LFS (recommended)
git clone https://github.com/D1ZZY4/android-development-skills.git --recurse-submodules

# Or if you already have git-lfs installed:
git lfs clone https://github.com/D1ZZY4/android-development-skills.git
```

Without Git LFS, binary asset files will appear as pointer files (`.gitattributes` references). The skill documentation is fully usable without the binary assets; only the port-rom FaceID APK and similar bundled artifacts are affected. Install Git LFS at any time and run `git lfs pull` to fetch them.

## Requirements

- `adb` and (for flashing-adjacent work) `fastboot` on PATH
- `repo` tool for ROM/build source management
- Standard AOSP/kernel host build dependencies
- Python 3.8+ for the SELinux repair tooling

## Repository structure

```
skills/
  rom/             AGENTS.md, SKILL.md, README.md, REFERENCE.md, template/, scripts/, references/
  kernel/          AGENTS.md, SKILL.md, README.md, REFERENCE.md, template/, scripts/, references/
  gki-kernel/      AGENTS.md, SKILL.md, README.md, REFERENCE.md, template/, scripts/, references/
  debug/           AGENTS.md, SKILL.md, README.md, REFERENCE.md, template/, scripts/, references/
  selinux-repair/  AGENTS.md, SKILL.md, README.md, REFERENCE.md, template/, scripts/, references/
  port-rom/        AGENTS.md, SKILL.md, README.md, REFERENCE.md, template/, scripts/, references/
  module/          AGENTS.md, SKILL.md, README.md, REFERENCE.md, template/, scripts/, references/
```

## Detailed documentation

Each skill has its own AGENTS.md (for AI agents), SKILL.md (skills.sh entry point), README.md (human overview), REFERENCE.md (command reference), template/, scripts/, and references/.

## License

GPL v3. See LICENSE.
