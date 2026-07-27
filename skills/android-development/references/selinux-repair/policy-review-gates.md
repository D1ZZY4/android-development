# SELinux Policy Review Gates

Use this before submitting or claiming a final fix.

## Build gates

- The original failing build target now passes.
- The first new build failure, if any, is unrelated or separately explained.
- No `neverallow` is bypassed with `SELINUX_IGNORE_NEVERALLOWS`.
- Context files compile with no duplicate specs or invalid labels.
- `host_init_verifier` passes for target init rc/property files.
- Generated intermediates were inspected when ordering or duplicate types are suspected.

Suggested commands:

```bash
m selinux_policy
m vendor_sepolicy.cil
m sepolicy_tests
scripts/build_error_triage.py build.log
```

Exact target names vary by Android version/ROM tree.

## Static gates

Run:

```bash
scripts/audit_device_tree.py device/<vendor>/<device> --format markdown
```

Block merge if new findings include:

- `permissive` in production policy.
- Broad allows to generic target labels.
- New `dontaudit` hiding unresolved bring-up denials.
- Vendor policy referring to private platform types.
- Broad property prefixes that overlap inherited policy.
- New daemons without domain/executable labels.

## Built artifact gates

Run:

```bash
scripts/verify_policy_artifacts.sh out/target/product/<device>
```

Review:

- `sepolicy-analyze permissive`
- `sepolicy-analyze booleans`
- `sepolicy-analyze dups`
- optional `sepolicy-analyze neverallow`
- final context artifacts under `*/etc/selinux`

## Runtime gates

On a development build:

```bash
adb wait-for-device
adb shell getenforce
adb shell ps -AZ
scripts/capture_selinux_denials.sh --root --auditctl --events 1500 --throttle 150
scripts/summarize_denials.py selinux-captures/<timestamp>/selinux-denials.log --format markdown
```

Pass criteria:

- Final target mode is `Enforcing`.
- No repeated denial remains for the same feature after exercising it.
- No replacement denial appears against a generic target label.
- No required service remains in `init` domain because of a missing transition.

## GSI/Treble-minded gates

- Vendor policy relies only on public policy APIs and local vendor/odm types.
- Product/system_ext public policy changes include compatibility/mapping thinking when vendor consumes them.
- `BOARD_GENFS_LABELS_VERSION` behavior is understood when touching genfs labels across vendor API levels.
- GSI boot assumptions are not broken by depending on OEM-only system_ext/product private types from vendor policy.
