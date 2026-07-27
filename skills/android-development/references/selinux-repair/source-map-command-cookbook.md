# Source-Map Command Cookbook

Replace `device/<vendor>/<device>/BoardConfig.mk` with the active BoardConfig for the current lunch target.

## Build-error triage

```bash
scripts/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
scripts/build_error_triage.py build.log --format markdown
scripts/selinux_build_doctor.py build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
```

## Duplicate property context

```bash
scripts/property_context_doctor.py --log build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
```

If the log only contains a truncated tail and not the `--property-contexts=` command, force a full source scan after the source-map scan:

```bash
scripts/property_context_doctor.py --log build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --full-tree --format markdown
```

## Duplicate type declaration

```bash
scripts/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
scripts/selinux_build_doctor.py build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
rg -n "\b<duplicate_type>\b" <resolved-roots> --glob '*.te' --glob '*contexts'
```

For example:

```bash
rg -n "\bvendor_camera_prop\b" \
  device/mediatek/sepolicy_vndr \
  device/<vendor>/<device>/sepolicy \
  vendor/<vendor>/<device>/sepolicy \
  system/sepolicy \
  --glob '*.te' --glob '*property_contexts'
```

## Unknown type or private symbol

```bash
scripts/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
rg -n "\b<symbol>\b" system/sepolicy/public system/sepolicy/private system/sepolicy/vendor <resolved-device-roots>
```

If a vendor `.te` references a symbol found only in `system/sepolicy/private`, redesign the local vendor label. Do not copy the private type into vendor policy.

## Neverallow

```bash
scripts/build_error_triage.py build.log --format markdown
scripts/selinux_build_doctor.py build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
rg -n "neverallow|violated by allow|<source_domain>|<target_type>" system/sepolicy <resolved-device-roots>
```

Treat neverallow as a design/ownership problem first.

## Runtime denials

```bash
scripts/capture_selinux_denials.sh --root --auditctl --events 1500 --throttle 150
scripts/summarize_denials.py selinux-captures/<timestamp>/selinux-denials.log --format markdown
scripts/audit_device_tree.py device/<vendor>/<device> --format markdown
```

Runtime fixes still use the source map when editing build policy.
