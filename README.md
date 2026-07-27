# android-development skill

A [skills.sh](https://skills.sh)-compatible skill package covering five Android
platform engineering workflows. Install it into any AI coding agent that supports
the Agent Skills convention and it will gain structured, evidence-first guidance
for custom Android ROM, kernel, GKI kernel, device debugging, and SELinux policy
repair work.

## Install

```bash
npx skills add D1ZZY4/android-development
```

### Install options

```bash
# Install all skills from this repo
npx skills add D1ZZY4/android-development --all

# Install a specific skill by name
npx skills add D1ZZY4/android-development --skill android-development

# Install multiple specific skills at once
npx skills add owner/repo --skill skill-a --skill skill-b

# List available skills in a repo before installing
npx skills add D1ZZY4/android-development --list
```

## Domains covered

| Domain | What it covers |
|---|---|
| ROM build | AOSP/LineageOS-derived builds from a device tree and manifest (repo sync, lunch/breakfast, mka) |
| Kernel build | Legacy/monolithic device kernel builds (defconfig, make, boot image packaging, AnyKernel3) |
| GKI kernel build | Generic Kernel Image builds (build/build.sh, Bazel/Kleaf, KMI/ABI awareness) |
| Debug | Evidence-first diagnosis of a misbehaving device or failed build -- no diagnosis without a log line, source reference, and live ADB output to back it up |
| SELinux repair | Build-time policy failures and runtime AVC denials -- policy source-map resolution, property-context conflicts, neverallow triage, least-privilege patch shapes |
| Port ROM | Adapting stock or OEM firmware to a custom ROM base -- image extraction, extra partition handling (tr_product/tr_region), vendor 64-bit conversion, OEM file removals, prop fixes |

## Requirements

- `adb` and (for flashing-adjacent work) `fastboot` on PATH
- `repo` tool for ROM builds
- Standard AOSP/kernel host build dependencies for the branch being targeted
- Python 3.8 or later for the SELinux repair tooling

## Detailed documentation

See [skills/android-development/README.md](skills/android-development/README.md)
for domain structure, safety notes, and instructions for running the test suite.
