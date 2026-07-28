# Research Notes Used for the 2026 Upgrade

These notes summarize external AOSP guidance that this skill encodes. They are intentionally practical and should be treated as a pointer map, not a replacement for reading the local AOSP reference snapshots.

## AOSP branch freshness

AOSP documentation now states that, effective in 2026, source is published to AOSP in Q2 and Q4 under the trunk-stable model, and that `android-latest-release` is recommended over `aosp-main` for building and contributing. For SELinux bring-up, this means public/private policy checks should be aligned with the release branch you actually build, not whatever happens to be at `main`.

Practical rule: when comparing against upstream public/private policy, use the ROM branch or `android-latest-release`, not a random future branch.

Source URL: https://source.android.com/docs/security/features/selinux/build

## Partitioned policy is the baseline

Android 8.0+ builds platform and vendor policy separately. Vendor policy is expected to be independently updateable and compatible with platform policy. Android 11+ also splits system_ext and product policy into public/private surfaces. Vendor policy may rely on exported public policy APIs, but private policy is implementation detail.

Practical rule: before referencing a platform type from device/vendor policy, check whether it is public/exported for the target branch.

Source URLs:
- https://source.android.com/docs/security/features/selinux/build
- https://source.android.com/docs/security/features/selinux/customize
- https://source.android.com/docs/security/features/selinux/compatibility

## Device-specific policy placement

AOSP `system/sepolicy` README says device-specific policy belongs under a separate `device/<vendor>/<board>/sepolicy` subtree and is added through `BOARD_VENDOR_SEPOLICY_DIRS`. It also says ordering matters and recommends inspecting `vendor_sepolicy.conf_intermediates/vendor_sepolicy.conf` when debugging ordering issues. Older variables such as `BOARD_PLAT_PUBLIC_SEPOLICY_DIR` and `BOARD_PLAT_PRIVATE_SEPOLICY_DIR` are deprecated in favor of system_ext/product mechanisms.

Practical rule: audit BoardConfig variables and generated intermediates before assuming a type or context is missing.

Source URL: https://android.googlesource.com/platform/system/sepolicy/

## Validation is not only logcat

AOSP validation guidance recommends checking global mode with `getenforce`, examining per-domain mode with `sepolicy-analyze -p`, reading denials from `dmesg` and `logcat`, inspecting previous boot logs from pstore, and disabling audit rate limiting with `auditctl -r 0` when necessary.

Practical rule: capture `logcat -b all`, `dmesg`, pstore, `getenforce`, and `ps -AZ`; do not rely on a single late logcat snapshot.

Source URL: https://source.android.com/docs/security/features/selinux/validate

## Permissive and audit2allow are development aids only

AOSP implementation guidance describes initial permissive bring-up, but says permissive boot parameters must be removed after bootstrap or CTS fails. The same page notes that AOSP no longer provides `audit2allow`; if used from a host distro, its output must still be reviewed.

Practical rule: use permissive and audit2allow only to discover missing policy shape; never ship them as the fix.

Source URL: https://source.android.com/docs/security/features/selinux/implement

## sepolicy-analyze gates

AOSP `sepolicy-analyze` supports checks for permissive domains, booleans, duplicate allows, attributes, type equivalence/difference, and neverallow validation. Its README notes permissive domains should not exist in final user builds, Android policy booleans are forbidden and fail CTS, and neverallow checks return non-zero on violations.

Practical rule: include `sepolicy-analyze permissive`, `booleans`, `dups`, and targeted `neverallow` checks in final review.

Source URL: https://android.googlesource.com/platform/system/sepolicy/+/main/tools/sepolicy-analyze/README

## Genfs label compatibility matters

AOSP compatibility guidance documents `BOARD_GENFS_LABELS_VERSION` and explains that platform genfs label changes must consider older vendor partitions. Vendor partitions can adopt newer labels by setting an appropriate genfs labels version.

Practical rule: when fixing `/sys` or `/proc` labels, check target vendor API/branch behavior. A label that is correct for one platform branch may be incompatible with another vendor partition.

Source URL: https://source.android.com/docs/security/features/selinux/compatibility

## 2026 generalization and build-error repair notes

The skill is intentionally agent-neutral. It should work as a reusable SELinux repair procedure for humans, CI bots, terminal agents, and AI coding assistants. The critical build-error improvement is to treat SELinux compiler/verifier failures as first-class entry points, not as secondary notes after runtime AVC triage.

Build-error categories now include: neverallow, unknown type/attribute, duplicate declarations, duplicate property prefixes, property_info_serializer, host_init_verifier, checkfc/invalid context, sepolicy_tests attribute failures, syntax/m4/CIL expansion failures, and runtime AVCs accidentally pasted into build logs.

The safe repair principle stays unchanged: fix ownership, partition boundary, and labels before adding permissions.

## 2026 source-map-aware updates

- Treat BoardConfig and included makefiles as the first evidence layer for device-tree SELinux build failures.
- AOSP policy compatibility documentation describes platform-public policy as the exported API for vendor policy and notes split property contexts such as `plat_property_contexts` and `vendor_property_contexts`.
- AOSP build documentation documents Android 11+ `system_ext` and `product` public/private policy surfaces.
- LineageOS inherits the AOSP-style core `system/sepolicy` tree; common ROM overlays such as `vendor/lineage/sepolicy` should be searched only when present in the checkout.
- For duplicate property prefix/exact failures, generated `--property-contexts=` arguments in the failing command are stronger evidence than repo-wide source search.
