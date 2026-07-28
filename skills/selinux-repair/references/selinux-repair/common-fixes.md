# Common Android SELinux Fix Patterns

These are safe patterns, not copy-paste guarantees. Always adapt to the target branch and existing policy style.

## New init daemon under `/vendor/bin`

Files usually involved:

- `sepolicy/vendor/<daemon>.te`
- `sepolicy/vendor/file_contexts`
- `init.<device>.rc` or vendor rc file

Policy shape:

```m4
type vendor_foo, domain;
type vendor_foo_exec, exec_type, vendor_file_type, file_type;
init_daemon_domain(vendor_foo)
```

Context shape:

```text
/vendor/bin/vendor.foo    u:object_r:vendor_foo_exec:s0
```

Then add only the resource-specific accesses the daemon needs.

## Vendor property set by vendor init

Files usually involved:

- `sepolicy/vendor/property_contexts`
- `sepolicy/vendor/property.te` or local property policy file
- `vendor.prop` / `PRODUCT_VENDOR_PROPERTIES` / init rc `setprop`

Policy shape:

```m4
type vendor_foo_prop, property_type;
set_prop(vendor_init, vendor_foo_prop)
get_prop(vendor_foo, vendor_foo_prop)
```

Context shape:

```text
vendor.foo.enabled    u:object_r:vendor_foo_prop:s0 exact bool
```

Prefer exact entries when inherited policy already owns the surrounding prefix family.

## Sysfs node for a vendor HAL

Files usually involved:

- `sepolicy/vendor/genfs_contexts`
- `sepolicy/vendor/<hal_or_daemon>.te`

Policy shape:

```m4
type sysfs_foo, sysfs_type, fs_type;
allow hal_foo_default sysfs_foo:file r_file_perms;
```

Context shape:

```text
genfscon sysfs /devices/platform/foo u:object_r:sysfs_foo:s0
```

Avoid granting to generic `sysfs` unless upstream policy already intends that exact label.

## Vendor Binder service

Files usually involved:

- `sepolicy/vendor/service_contexts` or `vndservice_contexts`
- `sepolicy/vendor/<server>.te`
- client domain policy

Policy shape depends on service kind. The safe review questions are:

- Is it a framework, vendor, hwservice, or vndservice service?
- Is the server the only domain allowed to add/register it?
- Are clients allowed to find/call only the specific service type?

Avoid catch-all `default_android_service` grants.

## Device node under `/dev`

Files usually involved:

- `ueventd*.rc` for ownership/mode
- `file_contexts` for label
- daemon/HAL `.te`

Policy shape:

```m4
type vendor_foo_device, dev_type;
allow vendor_foo vendor_foo_device:chr_file rw_file_perms;
```

Context shape:

```text
/dev/foo    u:object_r:vendor_foo_device:s0
```

Check DAC permissions too. SELinux should not be used to compensate for world-writable device nodes.

## Replacing a dangerous broad allow

Bad shape:

```m4
allow vendor_foo sysfs:file rw_file_perms;
allow vendor_foo default_prop:property_service set;
allow vendor_foo default_android_service:service_manager find;
```

Safer workflow:

1. Identify exact path/property/service.
2. Add precise label/type.
3. Grant only the needed permission to the precise type.
4. Remove the broad rule.
5. Re-test and ensure no generic-label denial remains.

## Duplicate property prefix / exact match

Symptom:

```text
host_init_verifier: Unable to serialize property contexts: Duplicate prefix match detected for 'ro.vendor.audio.'
host_init_verifier: Unable to serialize property contexts: Duplicate exact match detected for 'persist.foo.bar'
```

Safe pattern:

1. Run `scripts/selinux-repair/property_context_doctor.py --log build.log --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown`.
2. Keep only one property_contexts owner for the exact/prefix slot.
3. Prefer exact singleton entries when the tree does not own the whole prefix family.
4. Do not add `.te` allows; property trie serialization happens before permissions are useful.

Bad pattern:

```text
ro.vendor.audio.    u:object_r:vendor_audio_prop:s0 prefix string
# another inherited file repeats the same slot
ro.vendor.audio.    u:object_r:vendor_audio_prop:s0 prefix string
```

Better pattern when both files are inherited:

```text
# keep in one common owner only, remove from the duplicate local overlay
ro.vendor.audio.    u:object_r:vendor_audio_prop:s0 prefix string
```

Better pattern for singleton properties:

```text
ro.vendor.audio.feature_enabled    u:object_r:vendor_audio_prop:s0 exact bool
```

## Duplicate property type declaration

Symptom:

```text
ERROR 'Duplicate declaration of type'
type vendor_camera_prop, property_type, vendor_property_type, vendor_restricted_property_type;
```

Safe pattern:

1. `rg -n "\bvendor_camera_prop\b" . --glob '*.te' --glob '*property_contexts'`
2. Keep one declaration only.
3. Reuse the already-declared property type in `property_contexts`.
4. Rename only when a truly distinct property type is needed.

Bad pattern:

```m4
# common vendor policy already declares this
type vendor_camera_prop, property_type, vendor_property_type;

# device policy redeclares it
type vendor_camera_prop, property_type, vendor_property_type, vendor_restricted_property_type;
```


## Policy source map prerequisite

Before applying a build-error fix, resolve the active policy roots from BoardConfig and included makefiles:

```bash
scripts/selinux-repair/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
```

Search the resolved roots before broad repository search. Missing inherited `SEPolicy.mk` or `BoardConfigVendor.mk` files are build-input problems and should be fixed before creating duplicate local policy declarations.
