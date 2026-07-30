
# Port ROM -- AI Agent Entry Point

Adapting stock or OEM firmware (Transsion/XOS and others) to a custom ROM base. Image extraction, partition strategy, vendor 64-bit conversion, OEM file removals, and boot fixes.

Activate on: porting ROM, port from stock, donor ROM, extract partition, system.img, vendor.img, tr_product, tr_region, XOS port, Transsion port, vendor 64-bit conversion, tranwifi, vfy_boot, port checklist.

Read REFERENCE.md for commands. Use references/ for deep-dive playbooks.

## Hard Constraints

1. No flashing or partition writes without explicit user confirmation. Never mount images read-write unless required and confirmed.

2. Evidence over guessing. Verify files exist, check properties against actual firmware, confirm OEM blobs with real file listings.

## Port ROM Workflow

1. Verify required images: scripts/check_port_images.sh <dir>
2. Mount and inspect each image (read-only).
3. Identify OEM-only framework JARs, init services, and property contexts that will break on custom ROMs. Remove or comment out.
4. Handle extra OEM partitions (merge into system or add fstab entries).
5. Apply vendor 64-bit conversion if required.
6. Prepare device tree (BoardConfig.mk, fstab, props).
7. Build, debug, iterate (route build/debug issues to the relevant skill).

## File and Folder Map

```
skills/port-rom/
  AGENTS.md      AI agent router and workflow
  README.md      human-readable overview
  REFERENCE.md   command reference
  SKILL.md       skills.sh entry point
  template/      port_checklist.md, props_fragment.md
  scripts/       check_port_images.sh
  references/    partition-strategy.md, transsion-xos-boot-fixes.md,
                 nfc-oos-post-port.md, dolby-atmos-fix.md,
                 misound-dolby-replacement.md, signing-guide.md,
                 gsi-port-guide.md
  assets/        bundled porting artifacts
    apps/        apk packages
      faceid/    XOS 15 FaceID fix for Flamescian Project on X15
    libs/        .so blobs / HAL libraries (empty by default)
```
