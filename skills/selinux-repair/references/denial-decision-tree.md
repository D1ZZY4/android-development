
# AVC Denial Decision Tree

Use this reference when `summarize_denials.py` groups a runtime denial.

## Step 1: Normalize the denial

Extract:

- Permission set: `{ read write open getattr ... }`
- Source type: from `scontext=u:r:<source_type>:s0`
- Target type: from `tcontext=u:object_r:<target_type>:s0` or `u:r:<target_type>:s0`
- Target class: `file`, `dir`, `property_service`, `service_manager`, `binder`, `chr_file`, `unix_stream_socket`, etc.
- Object hints: `path=`, `name=`, `property=`, `service=`, `dev=`, `ino=`, `comm=`, `pid=`

Do not write policy until all available fields are understood.

## Step 2: Classify by target class

### `property_service` or property file classes

Ask:

- Is this property framework/product/system_ext/vendor/odm owned?
- Does it live in the correct `PRODUCT_*_PROPERTIES`, `TARGET_*_PROP`, or `*.prop` file?
- Is it labeled in the correct `property_contexts` file?
- Should the actor use `get_prop()` or `set_prop()`?

Common safe fixes:

- Move misplaced keys out of `vendor.prop`.
- Replace broad prefix entries with exact property labels.
- Add a local vendor property type only for vendor-owned keys.

### `service_manager`, `hwservice_manager`, or `vndservice_manager`

Ask:

- Is the service registered in the correct context file?
- Is this a framework Binder service, HIDL/AIDL HAL, or vendor Binder service?
- Is the client supposed to find it directly, or should it go through a framework service?

Common safe fixes:

- Add precise service label.
- Use existing HAL/service macros.
- Avoid `default_android_service` or catch-all service grants.

### `file`, `dir`, `lnk_file`, `chr_file`, `blk_file`, `sock_file`, `fifo_file`

Ask:

- Is the path under `/sys`, `/proc`, `/dev`, `/vendor`, `/odm`, `/data/vendor`, `/mnt/vendor`, `/metadata`, `/product`, or `/system_ext`?
- Does the current target type match the object?
- Should this be a `file_contexts`, `genfs_contexts`, fstab `context=`, ueventd, or restorecon issue?

Common safe fixes:

- Add precise file/genfs label.
- Ensure executable labels end in `_exec` and transition to a daemon domain.
- Use read-only perms unless a write path is justified.

### `process`

Ask:

- Is the denial for transition, dyntransition, ptrace, sigkill/sigchld, or noatsecure?
- Is the source domain trying to execute an unlabeled or wrongly labeled binary?

Common safe fixes:

- Label the executable.
- Use `init_daemon_domain()` or the correct domain transition macro.
- Do not grant generic process permissions to avoid fixing transition bugs.

### `capability` or `capability2`

Ask:

- Why does the daemon need Linux capability power despite already running under MAC policy?
- Can the design avoid root/capability use?
- Is the capability blocked by a neverallow?

Common safe fixes:

- Reduce daemon privilege.
- Move operation to an existing privileged service.
- Add capability only with strong justification and no neverallow conflict.

### Binder/socket classes

Ask:

- Is this framework Binder, vendor Binder, HIDL/AIDL HAL, or a Unix domain socket?
- Is the target service/socket labeled correctly?
- Does an existing macro encode the intended relationship?

Common safe fixes:

- `binder_call(client, server)` for Binder call relationships.
- HAL client/server macros for HAL access.
- `unix_socket_connect()` for intended socket connections.

## Step 3: Red flags

Pause and relabel/redesign when you see:

- target type: `sysfs`, `proc`, `device`, `rootfs`, `debugfs`, `tracefs`, `unlabeled`, `default_prop`, `vendor_default_prop`, `default_android_service`, `default_android_hwservice`, `default_android_vndservice`
- source type: `init` for a vendor daemon action
- broad permission: `write`, `create`, `execute`, `execute_no_trans`, `mounton`, `sys_admin`, `dac_override`, `sys_module`, `sys_rawio`
- build failure: `neverallow`

## Step 4: Write the patch explanation

For every policy edit, record:

```text
Denial: copied log line or grouped pattern
Actor: source domain and process name
Object: path/property/service and target type
Class/permission: tclass + permissions
Decision: ownership / label / domain transition / allow
Patch files: exact paths
Verification: build target + runtime capture command
```
