# BoardConfig-first SELinux Workflow

Device-tree SELinux repair should begin from the build inputs, not from a broad grep. Android makefiles tell you which policy directories are active for the product. A wrong search root leads to wrong fixes: duplicate declarations, stale local property entries, private platform symbol copies, and broad rules added to the nearest file instead of the contributing file.

## Required first step

```bash
scripts/selinux-repair/sepolicy_path_resolver.py \
  --repo . \
  --board-config device/<vendor>/<device>/BoardConfig.mk \
  --format markdown
```

Read these sections before editing:

- Resolved SELinux policy variables.
- Include chain.
- Declared search roots.
- Existing first search roots.
- Warnings about missing included makefiles.

## What the resolver follows

The resolver statically follows simple makefile constructs:

- `include ...`
- `-include ...`
- `$(call inherit-product,...)`
- `$(call inherit-product-if-exists,...)`
- simple variable assignments such as `DEVICE_PATH := device/foo/bar`
- append assignments such as `BOARD_VENDOR_SEPOLICY_DIRS += ...`

It intentionally does not execute arbitrary shell or full make. If a path remains unresolved, inspect it under the actual `lunch` environment.

## Policy variables to trust first

- `BOARD_VENDOR_SEPOLICY_DIRS`
- `BOARD_ODM_SEPOLICY_DIRS`
- `SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS`
- `SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS`
- `PRODUCT_PUBLIC_SEPOLICY_DIRS`
- `PRODUCT_PRIVATE_SEPOLICY_DIRS`
- `BOARD_SEPOLICY_DIRS` on older or mixed branches
- `BOARD_SEPOLICY_M4DEFS`

Deprecated platform override variables should be treated as migration signals, not as good modern patterns.

## Search order after resolution

1. Exact generated files from the failing command, such as `--property-contexts=out/.../vendor_property_contexts`.
2. Existing roots resolved from BoardConfig/include chain.
3. AOSP/ROM public roots such as `system/sepolicy/public` and `system/sepolicy/vendor`.
4. `system/sepolicy/private` only to confirm a public/private boundary problem.
5. Versioned prebuilts and mapping files for compatibility issues.
6. ROM overlays such as `vendor/lineage/sepolicy` if present.
7. Full-tree `rg` only after the source map does not explain the error.

## Missing roots are evidence

A missing root is not useless output. It can mean:

- the repo checkout is incomplete,
- a proprietary vendor tree was not synced,
- the BoardConfig path is wrong,
- an inherited common tree moved,
- the tree was copied from another branch/device.

Fix missing build inputs before creating duplicate local policy declarations.

## Agent rule

When `--board-config` is available, scripts should use it. A repair report that says “grep the whole repo” without showing the source map is incomplete.
