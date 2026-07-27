# Device-Tree Remediation Checklist

Use this checklist before patching an Android device tree.

## Property ownership and placement

- Check whether `vendor.prop` contains framework-owned keys such as:
  - `ro.product.*`
  - `ro.bootanim.*`
  - `ro.setupwizard.*`
  - `remote_provisioning.*`
  - `persist.arm64.memtag.*`
- Check whether `.mk` files use `PRODUCT_PROPERTY_OVERRIDES` where `PRODUCT_SYSTEM_PROPERTIES`, `PRODUCT_PRODUCT_PROPERTIES`, `PRODUCT_VENDOR_PROPERTIES`, or `TARGET_*_PROP` are more appropriate.

## Property-context safety

- Search for overlapping broad prefixes in local `property_contexts`.
- Assume merged inherited policy may already define broad `ro.vendor.*`, media, or audio families.
- If a broad family collides, replace local prefixes with exact property entries for the actual keys used by the tree.
- Avoid creating local catch-all entries for `ro.vendor.audio.`, `vendor.stream*`, or similar families unless you have confirmed no inherited definition exists.

## Label-first SELinux fixes

- For `sysfs` or `proc` denials, search for an existing narrow core or local type first.
- Add `genfs_contexts` or `file_contexts` mappings before adding new `allow` rules.
- Avoid granting access to generic targets such as `sysfs`, `default_prop`, `vendor_default_prop`, or `default_service`.

## Public/private boundary checks

- Verify that any platform type referenced from vendor policy is part of the exported public policy surface.
- If a needed type is private or unavailable, create a local vendor label instead of referencing the private symbol.

## Build verifier mindset

- Fix the first build error only.
- If the build says duplicate prefix, stop and remove the collision before touching runtime policy.
- If the build says unknown type, check symbol visibility before inventing workarounds.
- If the build says `neverallow`, revisit design and placement, not just the rule text.


## Policy source map prerequisite

Before applying a build-error fix, resolve the active policy roots from BoardConfig and included makefiles:

```bash
scripts/selinux-repair/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
```

Search the resolved roots before broad repository search. Missing inherited `SEPolicy.mk` or `BoardConfigVendor.mk` files are build-input problems and should be fixed before creating duplicate local policy declarations.
