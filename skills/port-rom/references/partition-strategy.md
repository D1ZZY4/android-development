
# Partition Strategy for ROM Porting

How to decide which partition images to extract from a donor ROM, how to handle vendor-specific extra partitions, and how to approach the vendor 64-bit conversion when it is required.

---

## Required partition images

At minimum, extract and inspect the following images from the donor ROM before starting a port:

| Image | Contains | Notes |
|---|---|---|
| `system.img` | Core Android framework, services, apps | Almost always required |
| `system_ext.img` | OEM system extensions, framework jars | Required when present; may contain OEM-only JARs that break AOSP builds |
| `product.img` | Product-tier apps and configs | Required when present |
| `vendor.img` | SoC and device-specific HALs, blobs | Required; this is usually the most port-critical image |
| `odm.img` | ODM-layer overrides for the specific board variant | Required when present |

Mount each image (read-only) to inspect before copying files:

```bash
# ext4 images
mkdir -p /tmp/mnt_system
sudo mount -o ro,loop system.img /tmp/mnt_system

# erofs images (common on Android 12+)
# requires erofs-utils (erofsfuse or kernel erofs support)
erofsfuse system.img /tmp/mnt_system
```

---

## Extra vendor-tier partitions (Transsion / XOS example)

Some OEM builds ship additional partitions that do not exist in AOSP or LineageOS. The Transsion (TECNO/Infinix/itel) platform uses:

| Image | Content | Port handling |
|---|---|---|
| `tr_product.img` | Transsion-specific product apps and configs | Extract needed blobs; strip unwanted apps to reduce size |
| `tr_region.img` | Region/operator-tier apps and build.prop overrides | Merge needed props into device build.prop; strip operator apps |

Two approaches for handling extra OEM partitions:

**Option A -- merge into system**: Copy the relevant files from the extra partition into the system or product layer in the device tree. Edit `fstab.*` to remove the mount entry for the original partition name so the bootloader does not try to mount a partition that no longer exists as a separate physical block device.

**Option B -- add a new fstab entry**: If the physical partition is present on the target device, add an fstab entry in `vendor/etc/fstab.<codename>` (and in the recovery fstab) pointing to the correct block device path. Ensure the partition is declared in `BoardConfig.mk` (`BOARD_*_PARTITION_SIZE`, `BOARD_*_FILE_SYSTEM_TYPE`).

---

## Vendor 64-bit conversion

Some Transsion/MediaTek devices ship a mixed 32/64 vendor (64-bit kernel, mixed lib and lib64 directories, 32-bit-only HALs for certain subsystems). Porting to a custom ROM that enforces 64-bit vendor ABIs requires converting the vendor blob set.

Reference implementation: https://github.com/ramabondanp/Transsion-vendor64_32-to-vendor64-only-fix

High-level steps:

1. Identify which HALs/libraries exist only as 32-bit (`lib/` only, no `lib64/`
   counterpart). These need either a 64-bit alternative or a `LOCAL_MULTILIB := 32` declaration in their `Android.bp`/`Android.mk`.
2. Update `BoardConfig.mk`: remove or change any `TARGET_PREFER_32_BIT_EXECUTABLES`
   or `TARGET_PREFER_32_BIT_APPS` flags.
3. Re-extract 64-bit blobs from a source that has them, or build thin 64-bit
   shim wrappers where a direct 64-bit blob is not available.
4. Verify with a test build: `m vendor_snapshot` or equivalent, then check for
   linker errors at boot.

---

## File removal checklist (apply after extraction)

Some OEM-specific files must be removed or the ROM will fail to boot or will crash on the custom-ROM framework. Check these in the extracted system and system_ext layers:

- `system_ext/framework/<oem_jar>.jar` -- OEM-only framework JARs that the custom ROM's framework does not know about cause ClassNotFoundExceptions at boot. Identify them by diffing the `system_ext/etc/permissions/*.xml` manifests against AOSP and removing any JAR declared there that is not in the custom ROM's framework.
- `system/system/etc/init/hw/init.rc` or similar -- OEM init services that reference blobs not present in the ported system will crash init and prevent boot. Comment out or remove the offending service stanzas (see
  `transsion-xos-boot-fixes.md` for a specific example).
- `vendor/etc/selinux/vendor_property_contexts` -- OEM-specific property context entries that reference types not declared in the custom ROM's policy will cause
  `property_info_serializer` to fail at build time. Remove the offending lines.
