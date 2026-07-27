# android-development

Agent skill and knowledge base for custom Android ROM, kernel, GKI kernel,
device debugging, and SELinux policy repair work. Compatible with any AI coding
agent that supports the Agent Skills convention -- not tied to a single vendor.

## What this is

A structured set of instructions, command references, fill-in-the-blank
templates, and executable tooling covering five related but distinct
Android platform engineering workflows:

| Domain | Covers |
|---|---|
| ROM build | AOSP/LineageOS-derived builds from a device tree + manifest (repo sync, lunch/breakfast, mka) |
| Kernel build | Legacy/monolithic device kernel builds (defconfig, make, boot image packaging, AnyKernel3) |
| GKI kernel build | Generic Kernel Image builds (build/build.sh, Bazel/Kleaf, KMI/ABI awareness) |
| Debug | Evidence-first diagnosis of a misbehaving device or failed build -- no diagnosis without a log line, source reference, and live ADB output to back it up |
| SELinux repair | Build-time policy failures and runtime AVC denials -- policy source-map resolution, property-context conflicts, neverallow triage, least-privilege patch shapes |
| Port ROM | Adapting stock or OEM firmware (Transsion/XOS and others) to a custom ROM base -- image extraction, extra partition handling, vendor 64-bit conversion, OEM file removals, prop fixes |

The core operating principle across all five domains: evidence before
diagnosis, narrow fixes over broad ones, and never mutate a live device
without explicit confirmation.

## Structure

```
android-development/
  AGENTS.md            AI agent entry point -- domain router, workflows, constraints
  SKILL.md             skills.sh entry point (minimal frontmatter + pointers)
  REFERENCE.md         command reference, one section per domain
  template/
    rom/
    kernel/
    gki-kernel/
    debug/
    selinux-repair/
    port-rom/          port_checklist.md, props_fragment.md
  scripts/
    rom/
    kernel/
    gki-kernel/
    debug/
    selinux-repair/    includes scripts/selinux-repair/tests/
    port-rom/          check_port_images.sh
  references/
    selinux-repair/    deep-dive SELinux/AOSP policy playbooks
    port-rom/          partition strategy, XOS/Transsion boot fix guide
```

`template/` and `scripts/` share the same five subfolder names by design --
the tooling and the fill-in-the-blank material for a given domain live
side by side.

## Install

### Via [skills.sh](https://skills.sh)

```bash
npx skills add D1ZZY4/android-development
```

### Other agents

Any agent that reads a project-level instructions file can use either:

- `android-development/AGENTS.md` as the AI-optimized entry point (recommended
  for AI coding agents -- includes domain routing, workflow steps, constraints,
  and file pointers)
- `android-development/SKILL.md` as the skills.sh entry point (contains the
  minimal YAML frontmatter that skills.sh installers read, then points to AGENTS.md)

## Requirements

- `adb` and (for flashing-adjacent work) `fastboot` on PATH
- `repo` tool for ROM builds
- Standard AOSP/kernel host build dependencies for the branch being targeted
- Python 3.8 or later for the SELinux repair tooling in scripts/selinux-repair/

## Safety notes

- No script in this skill performs a destructive action (fastboot flash, dd to a
  partition, adb reboot bootloader/recovery, adb shell setprop, etc.) without the
  operator explicitly initiating it. The read-only verification and log-capture
  tooling is intentionally limited to read commands.
- The debug and SELinux-repair workflows are evidence-first: a diagnosis is
  expected to cite the exact log line, source file/line, and live command output
  it is based on. See template/debug/diagnosis_report.md and
  template/selinux-repair/patch_output_contract.md for the expected report shape.
- scripts/selinux-repair/capture_selinux_denials.sh can optionally run adb root,
  auditctl -r 0, and UI-event fuzzing (monkey) when passed --root, --auditctl,
  and a non-zero event count. These are runtime-affecting (not partition-
  destructive) and are opt-in flags for a reason. Do not run them without the
  user's explicit confirmation.

## Testing

```bash
bash scripts/selinux-repair/tests/selftest.sh
find scripts -name "*.py" -exec python3 -m py_compile {} \;
find scripts -name "*.sh" -exec bash -n {} \;
```

## Attribution

The SELinux repair domain (template/selinux-repair/, scripts/selinux-repair/,
references/selinux-repair/) is adapted from a standalone Android SELinux repair
skill and folded in here as part of the broader Android development skill.

## License

This project is distributed under the GNU General Public License, version 3.
See the repository root [LICENSE.md](../../LICENSE.md) for the complete text.
