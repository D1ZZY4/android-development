# android-development

Agent skill / knowledge base for custom Android ROM, kernel, GKI kernel,
device debugging, and SELinux policy repair work. Built to be used by any
AI coding agent that supports the Agent Skills convention (Claude, Claude
Code, Cursor, Codex, and others) — not tied to a single vendor.

## What this is

A structured set of instructions, command references, fill-in-the-blank
templates, and executable tooling covering five related but distinct
Android platform engineering workflows:

| Domain | Covers |
|---|---|
| **ROM build** | AOSP / LineageOS-derived builds from a device tree + manifest (`repo sync`, `lunch`/`breakfast`, `mka`) |
| **Kernel build** | Legacy/monolithic device kernel builds (`defconfig`, `make`, boot image packaging, AnyKernel3) |
| **GKI kernel build** | Generic Kernel Image builds (`build/build.sh`, Bazel/Kleaf, KMI/ABI awareness) |
| **Debug** | Evidence-first diagnosis of a misbehaving device or failed build — no diagnosis without a log line, source reference, and live ADB output to back it up |
| **SELinux repair** | Build-time policy failures and runtime AVC denials — policy source-map resolution, property-context conflicts, neverallow triage, least-privilege patch shapes |

The core operating principle across all five domains: **evidence before
diagnosis, narrow fixes over broad ones, and never mutate a live device
without explicit confirmation.**

## Structure

```
android-development/
├── SKILL.md                     # entry point — read this first
├── REFERENCE.md                 # command reference, per domain
├── template/
│   ├── rom/
│   ├── kernel/
│   ├── gki-kernel/
│   ├── debug/
│   └── selinux-repair/
├── scripts/
│   ├── rom/
│   ├── kernel/
│   ├── gki-kernel/
│   ├── debug/
│   └── selinux-repair/          # includes scripts/selinux-repair/tests/
└── references/
    └── selinux-repair/          # deep-dive SELinux/AOSP policy playbooks
```

`template/` and `scripts/` share the same five subfolder names by design —
the tooling and the fill-in-the-blank material for a given domain live
side by side.

## Install

### Via [skills.sh](https://skills.sh)

```bash
npx skills add <github-user>/android-development
```

### Manually (Claude Code / Claude.ai)

```bash
# Personal, all projects
mkdir -p ~/.claude/skills
cp -r android-development ~/.claude/skills/

# Project-only
mkdir -p .claude/skills
cp -r android-development .claude/skills/
```

### Other agents

Any agent that reads a project-level instructions file can point at
`android-development/SKILL.md` directly as its entry point, or use the
[agent-skills](https://github.com/vercel-labs/agent-skills) universal
installer if it supports your agent of choice.

## Requirements

- `adb` and (for flashing-adjacent work) `fastboot` on `PATH`
- `repo` tool for ROM builds
- Standard AOSP/kernel host build dependencies for the branch you're
  targeting
- Python 3 for the SELinux repair tooling in `scripts/selinux-repair/`
- Recommended: a documentation-lookup MCP (e.g. Context7) wired into your
  agent, so build/kernel/SELinux commands get verified against current
  upstream docs rather than pulled from the model's training data alone

## Safety notes

- No script in this skill performs a destructive action (`fastboot flash`,
  `dd` to a partition, `adb reboot bootloader`/`recovery`, `adb shell
  setprop`, etc.) without the operator explicitly initiating it. The
  read-only verification and log-capture tooling is intentionally limited
  to read commands.
- The debug and SELinux-repair workflows are evidence-first: a diagnosis is
  expected to cite the exact log line, source file/line, and live command
  output it's based on — see `template/debug/diagnosis_report.md` and
  `template/selinux-repair/patch_output_contract.md` for the expected
  report shape.
- `scripts/selinux-repair/capture_selinux_denials.sh` can optionally run
  `adb root`, `auditctl -r 0`, and UI-event fuzzing (`monkey`) when passed
  `--root`/`--auditctl`/default event count — these are runtime-affecting
  (not partition-destructive) and are opt-in flags for a reason.

## Testing

```bash
bash scripts/selinux-repair/tests/selftest.sh
find scripts -name "*.py" -exec python3 -m py_compile {} \;
find scripts -name "*.sh" -exec bash -n {} \;
```

## Attribution

The SELinux repair domain (`template/selinux-repair/`,
`scripts/selinux-repair/`, `references/selinux-repair/`) is adapted from a
standalone Android SELinux repair skill and folded in here as part of the
broader Android development skill.

## License

Add your preferred license here before publishing.
