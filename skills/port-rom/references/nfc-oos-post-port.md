# OOS/ColorOS NFC Post-Port Fixes

Fixes for NFC broken after porting OOS (OxygenOS) or ColorOS firmware to a custom ROM base. Apply after the ROM is booting and SELinux is enforcing.

---

## NFC HAL file contexts

After porting, the OOS NFC HAL services may have lost their correct SELinux labels. Check and fix:

```text
/vendor/odm/bin/hw/vendor\.oplus\.hardware\.nfcExtns-service u:object_r:hal_allocator_default_exec:s0
/vendor/odm/bin/hw/vendor\.oplus\.hardware\.nfc_aidl-service u:object_r:hal_allocator_default_exec:s0
```

Add these entries to `file_contexts` in the relevant policy root (likely under `sepolicy/vendor/` or `sepolicy/odm/`).

## NFC libraries and manifest

Copy the following from the original OOS ODM into the port's overlay:

- `libpnscr2_aidl.so` → `odm/lib/` and `odm/lib64/`
- `manifest_nfc_sn100t_tee.xml` → `odm/etc/vintf/`

Set their context:

```text
/vendor/odm/lib/libpnscr2_aidl\.so u:object_r:vendor_file:s0
/vendor/odm/lib64/libpnscr2_aidl\.so u:object_r:vendor_file:s0
```

The `manifest_nfc_sn100t_tee.xml` does not need a special label — `vendor_file:s0` is sufficient.

## Debugging

If NFC still fails after applying the labels and files, capture logs.
Most developer/engineering builds are rooted; use `su -c` when available:

```bash
adb shell su -c "dmesg | grep -i nfc" > nfc_dmesg.txt
adb shell su -c "logcat -d -b all | grep -i nfc" > nfc_logcat.txt
```

On non-root builds, drop `su -c` and run the same commands directly:

```bash
adb shell dmesg | grep -i nfc > nfc_dmesg.txt
adb shell logcat -d -b all | grep -i nfc > nfc_logcat.txt
```

Common post-port NFC issues visible in these logs:

- Missing `/dev/` node or wrong permissions (check `ueventd*.rc`)
- HAL service crashing due to missing library dependency (check linker denials)
- SELinux avc denials for the NFC HAL domains