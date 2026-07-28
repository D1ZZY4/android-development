
# Property Context Collision Guide

This guide covers build failures from duplicate property exact/prefix slots.

## Symptoms

```text
host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'ro.vendor.audio.'
host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'vendor.streamin.'
host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'ro.vendor.mtk_cam_dualzoom_support'
property_info_serializer: Duplicate exact match detected for 'persist.foo.bar'
```

When this appears under many `FAILED: out/.../vendor/etc/init/*.rc` lines, the rc files are usually not broken. The verifier fails because the merged property trie cannot serialize.

## Correct command

```bash
scripts/selinux-repair/property_context_doctor.py \
  --log build.log \
  --repo . \
  --board-config device/<vendor>/<device>/BoardConfig.mk \
  --format markdown
```

The doctor searches in this order:

1. exact generated `--property-contexts=` files from the failing command,
2. BoardConfig/include-derived policy roots,
3. optional full-tree scan only when `--full-tree` is provided.

## Repair rules

- Same property plus same trie slot is invalid even if both lines use the same context.
- Prefix and exact slots are different slots, but broad prefixes can still hide stale ownership.
- Prefer one common SoC/vendor owner for broad families such as `ro.vendor.audio.`.
- Prefer `exact` entries for singleton device properties.
- Do not add `.te` allow rules for serializer failures.
- Do not patch every init rc shown in the cascade.

## Fix examples

### Duplicate broad prefix

Bad:

```text
device/mediatek/sepolicy_vndr/vendor/property_contexts:
ro.vendor.audio. u:object_r:vendor_audio_prop:s0 prefix string

device/<vendor>/<device>/sepolicy/vendor/property_contexts:
ro.vendor.audio. u:object_r:vendor_audio_prop:s0 prefix string
```

Fix: keep the broad prefix in the common SoC/vendor owner, remove it from the device overlay unless the device truly owns the whole family.

### Singleton property inside a broad family

Better:

```text
ro.vendor.audio.feature_enabled u:object_r:vendor_audio_prop:s0 exact bool
```

Do not add another broad `ro.vendor.audio.` prefix just to cover one property.

### Duplicate exact property

Bad:

```text
ro.vendor.mtk_cam_dualzoom_support u:object_r:vendor_camera_prop:s0 exact bool
ro.vendor.mtk_cam_dualzoom_support u:object_r:vendor_camera_prop:s0 exact bool
```

Fix: keep one line only. If two source trees need to share it, put it in the common inherited policy root and remove local duplicates.

## Clean/rebuild

```bash
rm -rf out/target/product/<device>/obj/ETC/*property_contexts_intermediates \
       out/soong/.intermediates/system/sepolicy/*property_contexts*
m vendor_property_contexts odm_property_contexts product_property_contexts || m vendor_sepolicy.cil
```

If the next build reports another duplicate property, repeat the same flow. Multiple stale properties often exist in vendor bring-up trees.
