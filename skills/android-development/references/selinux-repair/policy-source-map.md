# Policy Source Map First

Before editing Android SELinux policy, resolve the active source map from the device tree. Most wrong SELinux fixes happen because a maintainer or agent searches the whole tree, patches the nearest `.te` or `property_contexts` file, and misses an inherited SoC/vendor policy directory that the build actually uses.

## First command

```bash
scripts/sepolicy_path_resolver.py \
  --repo . \
  --board-config device/<vendor>/<device>/BoardConfig.mk \
  --format markdown
```

For source-map-aware build planning:

```bash
scripts/selinux_build_doctor.py \
  build.log \
  --repo . \
  --board-config device/<vendor>/<device>/BoardConfig.mk \
  --format markdown
```

For source-map-aware property collisions:

```bash
scripts/property_context_doctor.py \
  --log build.log \
  --repo . \
  --board-config device/<vendor>/<device>/BoardConfig.mk \
  --format markdown
```

## Inputs to inspect first

Start with the product's `BoardConfig.mk` and follow static includes:

- `include device/<soc-or-vendor>/sepolicy*/SEPolicy.mk`
- `include device/<vendor>/<device>/BoardConfigCommon.mk`
- `include vendor/<vendor>/<device>/BoardConfigVendor.mk`
- `$(call inherit-product, ...)` from product makefiles when the policy variable is set there

Then extract these variables:

- `BOARD_VENDOR_SEPOLICY_DIRS`
- `BOARD_ODM_SEPOLICY_DIRS`
- `SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS`
- `SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS`
- `PRODUCT_PUBLIC_SEPOLICY_DIRS`
- `PRODUCT_PRIVATE_SEPOLICY_DIRS`
- `BOARD_SEPOLICY_DIRS` on older or mixed branches
- deprecated `BOARD_PLAT_PUBLIC_SEPOLICY_DIR*` and `BOARD_PLAT_PRIVATE_SEPOLICY_DIR*`
- `BOARD_SEPOLICY_M4DEFS`

## Search order

1. Exact generated files named in the failing command, especially `--property-contexts=...`, generated `.cil`, and generated `vendor_sepolicy.conf`.
2. Device policy roots from BoardConfig.
3. SoC/OEM policy roots included by `SEPolicy.mk`.
4. Proprietary vendor policy roots included by `BoardConfigVendor.mk`.
5. `system/sepolicy/public`, then `system/sepolicy/vendor`.
6. `system/sepolicy/private` only to confirm a private symbol boundary issue; do not make vendor policy depend on private-only symbols.
7. `system/sepolicy/prebuilts/api` and mapping files for compatibility issues.
8. ROM overlays such as `vendor/lineage/sepolicy` when present.
9. Full-tree `rg` only after these roots do not explain the issue.

## AOSP / LineageOS-style core policy roots

- `system/sepolicy/public`: exported platform policy API for vendor policy.
- `system/sepolicy/private`: platform-private policy; vendor policy must not reference private-only types/attributes directly.
- `system/sepolicy/vendor`: vendor-side policy for components in the platform tree.
- `system/sepolicy/prebuilts/api`: versioned public/private snapshots and compatibility mapping data.
- `system/sepolicy/reqd_mask` or mapping directories: compatibility/mask data, branch-dependent.
- `vendor/lineage/sepolicy`: LineageOS common vendor policy overlay when included by the ROM tree.
- `vendor/cm/sepolicy`: legacy CyanogenMod/older Lineage overlay when present.

## Declared roots vs existing roots

The resolver prints both:

- **Declared search roots**: roots implied by makefiles, whether or not present in the checkout.
- **Existing first search roots**: roots that exist and should be searched first.

A declared-but-missing root is a useful finding. It may explain why a device tree copied from another branch/device is now redeclaring types or properties locally.

## Why this matters

For `host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected`, the broken line may be in:

- the device's `sepolicy/vendor/property_contexts`,
- a SoC policy include such as `device/mediatek/sepolicy_vndr/SEPolicy.mk`,
- a proprietary vendor include such as `vendor/<vendor>/<device>/BoardConfigVendor.mk`,
- a ROM common policy overlay,
- or the generated merged property_contexts under `out/target/product/<device>/obj/ETC/*_property_contexts_intermediates`.

Patch the owner that actually contributes the duplicate slot. Do not add `.te` allow rules; duplicate property contexts are serializer conflicts, not permission denials.
