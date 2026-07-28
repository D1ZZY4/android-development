
# Dangerous SELinux patterns to reject

Reject or redesign these unless a strong upstream pattern proves otherwise. If a proposed fix matches any of these shapes, stop and find the narrower alternative in `safe_policy_patterns.md` instead.

```m4
allow vendor_foo sysfs:file rw_file_perms;
allow vendor_foo proc:file rw_file_perms;
allow vendor_foo default_prop:property_service set;
allow vendor_foo default_android_service:service_manager find;
allow vendor_foo self:capability { sys_admin sys_module sys_rawio sys_ptrace dac_override };
permissive vendor_foo;   # final/user build
```

Also reject:

- Copying platform-private types into vendor policy (crosses the public/private policy boundary that OTA compatibility depends on).
- Adding `SELINUX_IGNORE_NEVERALLOWS := true` as a "fix" — this hides a real policy violation instead of resolving it.
- Silencing logs with `dontaudit` during bring-up — this hides denials that still block functionality, it just stops you from seeing why.
- Granting production policy access to `shell`, `su`, debug daemons, or test-only helpers.
- Using `unlabeled`, `default_*`, `sysfs`, `proc`, or `device` as the final target label for a *new* resource — these are meant to be transitional/ generic, not permanent homes for something that should have its own type.

## Generic target labels that should trigger "relabel first" instead of "allow"

If a denial's `tcontext` is one of these, the real fix is almost always to give the object its own specific label before considering an allow rule:

- `sysfs`, `proc`, `debugfs`, `tracefs`, `device`, `rootfs`, `unlabeled`
- `default_prop`, `vendor_default_prop`
- `default_android_service`, `default_android_hwservice`, `default_android_vndservice`
- broad data labels: `system_data_file`, `vendor_file`, `app_data_file`
