# android-development skill

A [skills.sh](https://skills.sh)-compatible skill package covering five Android
platform engineering workflows. Install it into any AI coding agent that supports
the Agent Skills convention and it will gain structured, evidence-first guidance
for custom Android ROM, kernel, GKI kernel, device debugging, and SELinux policy
repair work.

## Install

```bash
npx skills add <owner>/android-development
```

Replace `<owner>` with the GitHub user or organization that hosts this repository.

## Domains covered

| Domain | What it covers |
|---|---|
| ROM build | AOSP/LineageOS-derived builds from a device tree and manifest (repo sync, lunch/breakfast, mka) |
| Kernel build | Legacy/monolithic device kernel builds (defconfig, make, boot image packaging, AnyKernel3) |
| GKI kernel build | Generic Kernel Image builds (build/build.sh, Bazel/Kleaf, KMI/ABI awareness) |
| Debug | Evidence-first diagnosis of a misbehaving device or failed build -- no diagnosis without a log line, source reference, and live ADB output to back it up |
| SELinux repair | Build-time policy failures and runtime AVC denials -- policy source-map resolution, property-context conflicts, neverallow triage, least-privilege patch shapes |

## Requirements

- `adb` and (for flashing-adjacent work) `fastboot` on PATH
- `repo` tool for ROM builds
- Standard AOSP/kernel host build dependencies for the branch being targeted
- Python 3.8 or later for the SELinux repair tooling
- Recommended: a documentation-lookup MCP (such as Context7) wired into the agent,
  so build/kernel/SELinux commands get verified against current upstream docs

## Detailed documentation

See [skills/android-development/README.md](skills/android-development/README.md)
for domain structure, safety notes, and instructions for running the test suite.
