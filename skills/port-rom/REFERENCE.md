# Port ROM -- Reference

Workflow and file reference for porting an existing Android ROM or adapting
stock firmware (e.g. Transsion/XOS) to a custom ROM base.

## Verify required images before starting

```bash
# Check standard images
bash scripts/check_port_images.sh <firmware_dir>

# Also check Transsion-specific extra partitions (tr_product, tr_region)
bash scripts/check_port_images.sh <firmware_dir> --transsion
```

## Mount a partition image (read-only inspection)

```bash
# ext4
mkdir -p /tmp/mnt_part
sudo mount -o ro,loop <image>.img /tmp/mnt_part

# erofs (Android 12+, requires erofsfuse or kernel erofs support)
erofsfuse <image>.img /tmp/mnt_part

# Unmount when done
sudo umount /tmp/mnt_part   # ext4
fusermount -u /tmp/mnt_part # erofs
```

## Common OEM removal steps (Transsion/XOS)

```bash
# Identify OEM-only JARs
diff <(grep -r "library name=" system_ext/etc/permissions/ | grep -o '"[^"]*\.jar"') \
     <(ls system_ext/framework/*.jar | xargs -n1 basename | sed 's/^/"/;s/$/"/')

# Find OEM init services referencing absent binaries
grep -n "vfy_boot\|<oem_binary>" system/system/etc/init/hw/init.rc

# Find OEM property context entries that break property_info_serializer
grep -n "ro.vendor.trancare\|<oem_prop>" vendor/etc/selinux/vendor_property_contexts
```

## Key files

| File | Purpose |
|---|---|
| `template/port_checklist.md` | Porting checklist template |
| `template/props_fragment.md` | Build.prop additions template |
| `references/partition-strategy.md` | Image extraction strategy |
| `references/transsion-xos-boot-fixes.md` | XOS 16 specific boot blockers |
