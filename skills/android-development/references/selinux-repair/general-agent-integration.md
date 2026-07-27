# General Agent Integration

This skill is platform-neutral. It can be used by any assistant, shell agent, CI bot, IDE extension, or human maintainer.

## Recommended agent loop

1. Capture the first build failure or runtime denial evidence.
2. Run the relevant script.
3. Produce a patch plan before editing.
4. Apply the smallest patch.
5. Re-run the exact failed target.
6. Re-audit for broad policy and permissive domains.
7. Summarize what changed and why.

## Agent guardrails

Agents should never silently apply:

- `SELINUX_IGNORE_NEVERALLOWS`
- global permissive mode as a final fix
- raw `audit2allow` output
- private platform type copies into vendor policy
- generic target-label allows
- `dontaudit` to hide active bring-up denials

## Suggested repository commands

```bash
scripts/selinux-repair/build_error_triage.py build.log --format markdown
scripts/selinux-repair/selinux_build_doctor.py build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
scripts/selinux-repair/context_conflict_finder.py . --format markdown
scripts/selinux-repair/audit_device_tree.py . --format markdown
```


## Policy source map prerequisite

Before applying a build-error fix, resolve the active policy roots from BoardConfig and included makefiles:

```bash
scripts/selinux-repair/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
```

Search the resolved roots before broad repository search. Missing inherited `SEPolicy.mk` or `BoardConfigVendor.mk` files are build-input problems and should be fixed before creating duplicate local policy declarations.
