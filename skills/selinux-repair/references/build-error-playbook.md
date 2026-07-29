
# Android SELinux Build Error Playbook

Use this when the Android build fails before boot testing.

## First-failure rule

Parallel builds often emit multiple failures. Fix the earliest concrete SELinux tool failure, not the final `ninja failed` line.

Search patterns:

```bash
rg -n "FAILED:|neverallow|violated by allow|checkpolicy|secilc|checkfc|host_init_verifier|property_info_serializer|BuildTrie|Unable to serialize property contexts|Duplicate prefix|Duplicate exact|Duplicate declaration|unknown type|unknown attribute|avc: denied" build.log
```

## Class matrix

| Class | Usually means | First repair move |
|---|---|---|
| `neverallow` | Android security invariant violated | Redesign domain/label/partition; don't bypass |
| `unknown_type_or_attribute` | Missing declaration or private/public policy boundary issue | Locate symbol and move to correct policy surface |
| `duplicate_property_prefix` | Merged property_contexts contains the same prefix trie slot twice | Run `property_context_doctor.py`; remove one owner or narrow to exact |
| `duplicate_property_exact` | Merged property_contexts contains the same exact property twice | Keep one exact mapping; remove stale duplicate overlay |
| `property_info_serializer` | Invalid/duplicate property context trie | Fix property_contexts/property ownership |
| `host_init_verifier` | init rc, property, service, or partition mismatch | Read the verifier message; if duplicate property, fix property_contexts first |
| `duplicate_type_declaration` | `.te` declares a type already declared by inherited/common policy | Remove the redeclaration or rename the local type everywhere |
| `duplicate_attribute_declaration` | `.te` declares an attribute already declared by inherited/common policy | Remove the redeclaration or namespace the local attribute |
| `checkfc_or_invalid_context` | Context file points at bad/undeclared type | Declare correct type/attribute or relabel |
| `sepolicy_tests_attribute` | Type lacks required Android attribute | Add correct semantic attribute |
| `syntax_or_m4` | Bad policy syntax or macro expansion | Inspect source marker and generated policy |

## Case: `host_init_verifier` duplicate property prefix

Example:

```text
FAILED: out/target/product/P13001L/vendor/etc/init/wlan_assistant.rc
host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'vendor.streamin.'
FAILED: out/target/product/P13001L/vendor/etc/init/init.connfem.rc
host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'ro.vendor.audio.'
FAILED: out/target/product/P13001L/vendor/etc/init/vendor.mediatek.hardware.mms@1.6-service.rc
host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'ro.vendor.mtk_cam_dualzoom_support'
```

Interpretation:

- The many `FAILED: .../vendor/etc/init/*.rc` lines are a cascade.
- The root cause is the property trie failing before the rc copy/verifier step can complete.
- The failing rc file usually does not contain the bug.
- Adding `allow` rules in `.te` cannot fix this.

Workflow:

```bash
scripts/build_error_triage.py build.log --format markdown
scripts/property_context_doctor.py --log build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
rg -n "vendor.streamin\.|ro.vendor.audio\.|ro.vendor.mtk_cam_dualzoom_support" . --glob '*property_contexts'
```

Fix patterns:

1. If the same prefix/exact property appears in both a common SoC policy and a device policy, keep the common owner and remove the duplicate device entry.
2. If two different labels claim the same property key, decide the real owner from the code that sets/reads the property, then update the other side.
3. If a broad prefix such as `ro.vendor.audio.` exists only to cover a few singleton properties, replace it with exact entries for those singleton keys.
4. Clean/rebuild affected intermediates:

```bash
rm -rf out/target/product/<device>/obj/ETC/*property_contexts_intermediates \
       out/soong/.intermediates/system/sepolicy/*property_contexts*
m vendor_property_contexts odm_property_contexts product_property_contexts || m vendor_sepolicy.cil
```

## Case: duplicate property type declaration

Example:

```text
device/itel/P661N/sepolicy/vendor/property.te:2:ERROR 'Duplicate declaration of type' at token ';'
type vendor_camera_prop, property_type, vendor_property_type, vendor_restricted_property_type;
```

Interpretation:

- `vendor_camera_prop` already exists in another included `.te` file.
- This is not an unknown-type problem; it is the opposite: the type exists too many times.
- For property types, the usual fix is to reuse the existing type in `property_contexts`, not redeclare it.

Workflow:

```bash
rg -n "\bvendor_camera_prop\b" . --glob '*.te' --glob '*property_contexts'
rg -n "BOARD.*SEPOLICY|PRODUCT_.*SEPOLICY|SYSTEM_EXT_.*SEPOLICY|BOARD_ODM_SEPOLICY" device vendor product system_ext
```

Fix patterns:

1. Remove `type vendor_camera_prop, ...;` from the local file if inherited policy already declares it.
2. Keep `property_contexts` entries pointing to the existing `u:object_r:vendor_camera_prop:s0` type.
3. If the local camera property really must be separate, rename to a unique type such as `vendor_<device>_camera_prop`, declare it once, and update every `property_contexts` reference.
4. Rebuild:

```bash
m vendor_sepolicy.cil sepolicy_neverallows
```

## Minimum repair output

Every repair should answer:

1. What exact first line failed?
2. Which source file generated it?
3. Which partition owns the actor and object?
4. Is the object correctly labeled?
5. Is the symbol public/exported if vendor uses it?
6. What minimal file(s) must change?
7. What command proves the fix?

## Do not use as fixes

- `SELINUX_IGNORE_NEVERALLOWS := true`
- broad `allow domain ...`
- broad generic labels like `sysfs`, `proc`, `device`, `default_prop`, `default_android_service`
- copying private platform policy symbols into vendor policy
- declaring the same type in multiple inherited `.te` files
- adding `.te` allow rules for property serialization failures
- `dontaudit` during bring-up
- final `permissive` domains for user builds

## Policy source map prerequisite

Before applying a build-error fix, resolve the active policy roots from BoardConfig and included makefiles:

```bash
scripts/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
```

Search the resolved roots before broad repository search. Missing inherited `SEPolicy.mk` or `BoardConfigVendor.mk` files are build-input problems and should be fixed before creating duplicate local policy declarations.
