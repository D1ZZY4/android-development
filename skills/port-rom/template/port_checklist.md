
# ROM Port Checklist

Fill this in for each port attempt. Every item must be confirmed with a real file check, build output, or device log -- not a guess.

Device codename: [fill in] Donor ROM / source firmware: [fill in] Target ROM base (e.g. LineageOS 21, crDroid 14): [fill in] Date started: [fill in]

---

## Phase 1 -- Image extraction and audit

- [ ] All required partition images verified present and non-empty
      (`check_port_images.sh <dir>`)
- [ ] system.img mounted and inspected
- [ ] system_ext.img mounted and inspected (if present)
- [ ] product.img mounted and inspected (if present)
- [ ] vendor.img mounted and inspected
- [ ] Extra OEM partitions identified and handling decision made
      (merge into system/product OR add fstab entry): [list partitions and chosen approach]
- [ ] OEM-only framework JARs in system_ext/framework/ identified:
      [list files to remove]
- [ ] init.rc services referencing absent binaries identified:
      [list service names to comment out]
- [ ] vendor/etc/selinux/vendor_property_contexts checked for
      non-AOSP property entries that will break property_info_serializer: [list entries to remove]

## Phase 2 -- Device tree preparation

- [ ] device/<vendor>/<codename>/ tree created or forked from a close reference
- [ ] BoardConfig.mk: partition sizes, kernel image name, AVB config verified
- [ ] fstab entries match physical partition layout of target device
- [ ] vendor 64-bit conversion applied if required (see partition-strategy.md)
- [ ] local_manifest.xml created at .repo/local_manifests/ with device, vendor,
      and kernel repos pointing to correct branches

## Phase 3 -- First build

- [ ] repo sync completed without errors
- [ ] source build/envsetup.sh + lunch/breakfast succeeded
- [ ] Build started: `mka bacon` (or equivalent) backgrounded to log file
- [ ] First build error identified (grep -n -m1 -E "error:|FAILED:" <logfile>):
      [paste first error]
- [ ] First build error resolved:
      [brief description of fix]
- [ ] Build completed without errors

## Phase 4 -- First boot

- [ ] Output image flashed to test device (user confirmed the flash)
- [ ] Boot log captured: `adb logcat -d -b all > logcat_first_boot.txt`
      and `adb shell dmesg > dmesg_first_boot.txt`
- [ ] Boot result: [boots to UI / bootloop / stuck at splash / other]
- [ ] First failure identified from log:
      [paste exact log line]
- [ ] Failure domain routed to: [ROM Build / Kernel / SELinux Repair / Debug]

## Phase 5 -- Runtime verification

- [ ] Wi-Fi: [working / not tested / broken -- log line]
- [ ] Telephony / SIM: [working / not tested / broken -- log line]
- [ ] Camera: [working / not tested / broken -- log line]
- [ ] Audio (earpiece, speaker, microphone): [working / not tested / broken]
- [ ] Sensors (accelerometer, proximity, fingerprint): [working / not tested / broken]
- [ ] Bluetooth: [working / not tested / broken]
- [ ] Infrared blaster (if applicable): [working / not tested / broken]
- [ ] dt2w / gestures (if applicable): [working / not tested / broken]
- [ ] All SELinux denials triaged (no unresolved runtime AVCs blocking features)

## Open issues

[List anything not yet resolved, with the exact log evidence for each]
