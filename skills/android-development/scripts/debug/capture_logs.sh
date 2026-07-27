#!/usr/bin/env bash
# Capture logcat (all buffers) + dmesg + tombstone listing from a connected
# ADB device into timestamped files. Read-only — pulls data only, never
# writes to or mutates the device.
#
# Usage: ./capture_logs.sh [output_dir]
#   output_dir defaults to ./debug_logs_<timestamp>/

set -euo pipefail

OUT_DIR="${1:-./debug_logs_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUT_DIR"

if ! command -v adb >/dev/null 2>&1; then
  echo "ERROR: adb not found in PATH." >&2
  exit 1
fi

DEVICE_COUNT=$(adb devices | grep -c -w "device" || true)
if [ "$DEVICE_COUNT" -lt 1 ]; then
  echo "ERROR: no ADB device connected (check 'adb devices')." >&2
  exit 1
fi

echo "Capturing logs to: $OUT_DIR"

adb logcat -d -b all    > "$OUT_DIR/logcat_all.txt"    2>&1 || echo "warn: logcat -b all failed"
adb logcat -d -b radio  > "$OUT_DIR/logcat_radio.txt"  2>&1 || echo "warn: logcat -b radio failed"
adb logcat -d -b events > "$OUT_DIR/logcat_events.txt" 2>&1 || echo "warn: logcat -b events failed"
adb logcat -d -b crash  > "$OUT_DIR/logcat_crash.txt"  2>&1 || echo "warn: logcat -b crash failed"
adb shell dmesg         > "$OUT_DIR/dmesg.txt"         2>&1 || echo "warn: dmesg failed (may need root)"
adb shell ls -l /data/tombstones/ > "$OUT_DIR/tombstones_list.txt" 2>&1 || echo "warn: tombstones listing failed (may need root)"

echo "Done. Files:"
ls -la "$OUT_DIR"

echo ""
echo "Quick triage — first hits per failure class:"
for pattern in "FATAL EXCEPTION" "panic" "avc:.*denied" "Fatal signal" "ANR in"; do
  hit=$(grep -m1 -inE "$pattern" "$OUT_DIR"/*.txt 2>/dev/null || true)
  if [ -n "$hit" ]; then
    echo "  [$pattern] -> $hit"
  fi
done
