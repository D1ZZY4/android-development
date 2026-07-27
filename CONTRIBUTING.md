# Contributing

## How to propose changes

Contributions are organized by domain. Each domain has its own subfolder in
`template/`, `scripts/`, and `references/` inside `skills/android-development/`.
Before opening a pull request, identify which domain your change belongs to and
keep it scoped to that domain's files.

- Changes to build or debug commands belong in `REFERENCE.md` and/or the relevant
  `references/<domain>/` playbooks.
- Changes to reusable fill-in-the-blank materials belong in `template/<domain>/`.
- Changes to executable tooling belong in `scripts/<domain>/`.
- Changes to the agent routing logic or workflow steps belong in `AGENTS.md`.

## Required checks before submitting

Every pull request must pass all three checks before review:

```bash
# 1. Shell script syntax check
find skills/android-development/scripts -name "*.sh" -exec bash -n {} \;

# 2. Python syntax check
find skills/android-development/scripts -name "*.py" -exec python3 -m py_compile {} \;

# 3. Integration self-test (runs the SELinux tools against bundled sample fixtures)
bash skills/android-development/scripts/selinux-repair/tests/selftest.sh
```

All three must exit without errors. If selftest.sh fails, fix the tool or fixture
before submitting -- do not disable or skip tests.

## Safety constraints (non-negotiable review criteria)

The following constraints apply to every pull request, without exception. A PR
that weakens any of these will not be merged regardless of other merit.

### No mutating commands on a live device without explicit user confirmation

Scripts, documentation examples, and template files must not add new invocations
of any of the following commands unless they are already present in the file being
changed:

- `fastboot flash`, `fastboot erase`
- `adb reboot bootloader`, `adb reboot recovery`
- `dd` to any device node
- `mkfs` on any partition
- `adb shell setprop`
- `rm` or any write-to-partition command on a physical device

The debug and SELinux capture scripts (scripts/debug/ and
scripts/selinux-repair/capture_selinux_denials.sh) must remain evidence-gathering
tools only. The verify_device.sh script must remain strictly read-only and must
never gain subcommands that write to the device.

### Evidence-first diagnosis

Debug and SELinux repair workflows must produce a diagnosis only after pulling
fresh logs and command output from the current session. Templates must retain
their "INSUFFICIENT DATA" fallback and not be softened to allow guessed
diagnoses.

### No broad or bypass SELinux policy shapes

Any SELinux policy example or fix in any file must not introduce:

- `SELINUX_IGNORE_NEVERALLOWS := true`
- `permissive <domain>;` as a final production fix
- Allow rules targeting generic labels such as `sysfs`, `proc`, `device`,
  `default_prop`, `default_android_service`
- Raw `audit2allow` output presented as a ready-to-apply patch
- `dontaudit` rules used to hide bring-up denials

These patterns must not appear in documentation, template files, or reference
playbooks as recommended practice. If they are shown at all, they must be clearly
labeled as patterns to reject or as development-only tools.

## Versioning and backward compatibility

Changes to `REFERENCE.md` command syntax should note the Android or kernel version
range where the changed form applies. If a command varies by branch (for example,
the switch from `build/build.sh` to Bazel/Kleaf in GKI kernels), document both
forms rather than deleting the older one before it is fully deprecated upstream.
