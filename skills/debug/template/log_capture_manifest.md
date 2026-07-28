
# Log capture output manifest

`scripts/debug/capture_logs.sh` writes files in this layout under the output directory it's given (default `./debug_logs_<timestamp>/`):

```
debug_logs_<timestamp>/
├── logcat_all.txt        # adb logcat -d -b all
├── logcat_radio.txt       # adb logcat -d -b radio
├── logcat_events.txt      # adb logcat -d -b events
├── logcat_crash.txt       # adb logcat -d -b crash
├── dmesg.txt               # adb shell dmesg
└── tombstones_list.txt     # adb shell ls -l /data/tombstones/
```

When reviewing these, grep for the failure class first (see REFERENCE.md § Debug Commands for the grep patterns) rather than reading files top to bottom — these can be tens of thousands of lines on a busy system.
