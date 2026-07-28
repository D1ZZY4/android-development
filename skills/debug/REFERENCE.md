# Debug -- Reference

Evidence-gathering commands. Use scripts/capture_logs.sh to run all of
these at once and save to files, or run individually:

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

**Never** run unless the user explicitly asks and confirms:
fastboot flash*, adb reboot bootloader/recovery, adb shell setprop, rm, dd,
or anything under /data or partitions that isn't a read.

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
