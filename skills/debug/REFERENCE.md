
# Debug -- Reference

Evidence-gathering commands. Use scripts/capture_logs.sh to run all of these at once and save to files, or run individually:

```bash
# Full logcat, all buffers, dump-and-exit (not streaming)
adb logcat -d -b all > logcat_all.txt

# Specific buffers if all is too noisy
adb logcat -d -b radio > logcat_radio.txt
adb logcat -d -b events > logcat_events.txt
adb logcat -d -b crash > logcat_crash.txt

# Kernel log
adb shell dmesg > dmesg.txt

# Tombstones (native crashes)
adb shell ls -l /data/tombstones/
adb shell cat /data/tombstones/<file>   # requires root; read-only, fine
```

## Read-only live verification commands

```bash
adb shell ls -lZ /path/to/file            # SELinux context + perms
adb shell getprop | grep <prop_name>       # system properties
adb shell dumpsys <service>                 # service state
adb shell ps -A                             # process/service liveness
adb shell lshal                             # HAL listing
adb shell cat /sys/...                      # sysfs nodes
adb shell getenforce                        # SELinux mode
```

**Never** run unless the user explicitly asks and confirms: fastboot flash*, adb reboot bootloader/recovery, adb shell setprop, rm, dd, or anything under /data or partitions that isn't a read.

## Boot-time log capture (device stuck at logo / rebooting)

When a device hangs at the boot animation or reboots before reaching the UI:

```bash
# Stuck at logo but ADB accessible — stream from boot
adb logcat > logcat_boot.txt

# Device boots but reboots shortly after — check pstore (kernel panic)
adb pull /sys/fs/pstore/
# Some older kernels use last_kmsg instead
adb pull /proc/last_kmsg
```

Pstore contains the kernel's panic/backtrace from the previous boot. Read `pstore/console-ramoops` first — it often has the exact panic message. If `/sys/fs/pstore` doesn't exist, the kernel may lack `CONFIG_PSTORE`.

## Quick on-device fixes

### Read-only checks

These commands only read state and never modify the device:

```bash
adb shell getprop | grep <prop_name>
adb shell dumpsys <service>
adb shell ps -A
adb shell lshal
adb shell cat /sys/...
adb shell getenforce
```

### Mutating fix (requires root / user consent)

The command below changes global settings. Do not run it without explicit
user confirmation. On Android 14+ it requires `WRITE_SECURE_SETTINGS`,
which `adb root` provides on userdebug/eng builds but not on production
user builds.

```bash
# Fix restricted networking (common on GSIs — no internet)
# Requires root / adb root on Android 14+: WRITE_SECURE_SETTINGS is enforced.
adb shell settings put global restricted_networking_mode 0
```

Making network settings persistent requires root or a Magisk/KSU module (`settings delete global` on boot via `service.sh`).

## Grep patterns for common failure classes

```bash
# FATAL EXCEPTION (Java/Kotlin crash)
grep -n "FATAL EXCEPTION" logcat_all.txt

# Kernel panic
grep -n -i "panic\|Kernel panic" dmesg.txt

# SELinux denial
grep -n "avc:.*denied" logcat_all.txt dmesg.txt

# Native crash signal
grep -n "Fatal signal" logcat_all.txt

# ANR
grep -n "ANR in" logcat_all.txt
```
