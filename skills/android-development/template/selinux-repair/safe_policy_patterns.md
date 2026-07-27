# Safe SELinux policy patterns (templates)

Reusable, least-privilege policy shapes. Fill in `foo`/device-specific names
— never grant broader permissions than the daemon/property/node actually
needs, and never copy these in without checking whether an existing type
already covers the same resource (see policy source map first,
`references/selinux-repair/policy-source-map.md`).

## New vendor init daemon

```m4
type vendor_foo, domain;
type vendor_foo_exec, exec_type, vendor_file_type, file_type;
init_daemon_domain(vendor_foo)
```

```text
/vendor/bin/vendor.foo    u:object_r:vendor_foo_exec:s0
```

Then grant only the daemon-specific resources it actually needs — don't
pre-emptively add sysfs/proc/capability access "just in case."

## Vendor property

```m4
type vendor_foo_prop, property_type;
set_prop(vendor_init, vendor_foo_prop)
get_prop(vendor_foo, vendor_foo_prop)
```

```text
vendor.foo.enabled    u:object_r:vendor_foo_prop:s0 exact bool
```

## Sysfs node

```m4
type sysfs_foo, sysfs_type, fs_type;
allow hal_foo_default sysfs_foo:file r_file_perms;
```

```text
genfscon sysfs /devices/platform/foo u:object_r:sysfs_foo:s0
```

## Device node

```m4
type vendor_foo_device, dev_type;
allow vendor_foo vendor_foo_device:chr_file rw_file_perms;
```

```text
/dev/foo    u:object_r:vendor_foo_device:s0
```

Also check `ueventd*.rc` — SELinux cannot compensate for wrong DAC
ownership/mode on the device node itself.
