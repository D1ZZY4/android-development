#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: capture_selinux_denials.sh [options]

Options:
  --events N        Monkey event count (default: 1000)
  --throttle MS     Monkey throttle in ms (default: 200)
  --duration SEC    Capture duration without monkey, or extra capture after monkey (default: 2)
  --out-dir DIR     Output root directory (default: selinux-captures)
  --no-monkey       Do not run monkey; just capture logs for --duration seconds
  --root            Try adb root before capture
  --auditctl        Try adb shell setprop ctl.stop auditd to disable audit rate limiting
  --no-clear        Do not clear logcat before capture
  --bugreport       Capture adb bugreport zip after the run
  -h, --help        Show this help
EOF
}

EVENTS=1000
THROTTLE_MS=200
DURATION=2
OUT_DIR="selinux-captures"
RUN_MONKEY=1
TRY_ROOT=0
TRY_AUDITCTL=0
CLEAR_LOGCAT=1
CAPTURE_BUGREPORT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --events) EVENTS="$2"; shift 2 ;;
    --throttle) THROTTLE_MS="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --no-monkey) RUN_MONKEY=0; shift ;;
    --root) TRY_ROOT=1; shift ;;
    --auditctl) TRY_AUDITCTL=1; shift ;;
    --no-clear) CLEAR_LOGCAT=0; shift ;;
    --bugreport) CAPTURE_BUGREPORT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

TS="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="$OUT_DIR/$TS"
LOG="$RUN_DIR/logcat-all.log"
DEN="$RUN_DIR/selinux-denials.log"
MONKEY="$RUN_DIR/monkey.log"
SUMMARY="$RUN_DIR/summary.md"
DMESG="$RUN_DIR/dmesg.log"
PSTORE_DIR="$RUN_DIR/pstore"
STATE="$RUN_DIR/device-state.txt"

mkdir -p "$RUN_DIR" "$PSTORE_DIR"

run_adb() {
  adb "$@" >>"$RUN_DIR/adb-commands.log" 2>&1 || true
}

adb wait-for-device
if [[ "$TRY_ROOT" -eq 1 ]]; then
  adb root >>"$RUN_DIR/adb-commands.log" 2>&1 || true
  adb wait-for-device || true
fi

{
  echo "timestamp=$TS"
  echo "events=$EVENTS"
  echo "throttle_ms=$THROTTLE_MS"
  echo "duration=$DURATION"
  echo "run_monkey=$RUN_MONKEY"
  echo
  echo "## getenforce"
  adb shell getenforce 2>/dev/null || true
  echo
  echo "## build properties"
  for p in ro.build.fingerprint ro.vendor.build.fingerprint ro.product.device ro.product.vendor.device ro.boot.verifiedbootstate ro.boot.vbmeta.device_state ro.treble.enabled ro.board.api_level ro.vendor.api_level ro.product.first_api_level; do
    printf '%s=' "$p"
    adb shell getprop "$p" 2>/dev/null | tr -d '\r' || true
  done
  echo
  echo "## uname"
  adb shell uname -a 2>/dev/null || true
  echo
  echo "## ps -AZ"
  adb shell ps -AZ 2>/dev/null || adb shell ps -Z 2>/dev/null || true
  echo
  echo "## mount selinux files"
  adb shell 'ls -l /sys/fs/selinux /system/etc/selinux /vendor/etc/selinux /odm/etc/selinux /product/etc/selinux /system_ext/etc/selinux 2>/dev/null' || true
} > "$STATE"

if [[ "$TRY_AUDITCTL" -eq 1 ]]; then
  adb shell setprop ctl.stop auditd >>"$RUN_DIR/adb-commands.log" 2>&1 || true
  adb shell su 0 setprop ctl.stop auditd >>"$RUN_DIR/adb-commands.log" 2>&1 || true
fi

if [[ "$CLEAR_LOGCAT" -eq 1 ]]; then
  adb logcat -c || true
fi

adb logcat -b all -v threadtime > "$LOG" 2>&1 &
LOGCAT_PID=$!
cleanup() {
  kill "$LOGCAT_PID" 2>/dev/null || true
  wait "$LOGCAT_PID" 2>/dev/null || true
}
trap cleanup EXIT
sleep 2

if [[ "$RUN_MONKEY" -eq 1 ]]; then
  adb shell monkey \
    --ignore-crashes \
    --ignore-timeouts \
    --ignore-security-exceptions \
    --throttle "$THROTTLE_MS" \
    "$EVENTS" > "$MONKEY" 2>&1 || true
else
  echo "monkey disabled" > "$MONKEY"
fi

sleep "$DURATION"
cleanup
trap - EXIT

adb shell dmesg > "$DMESG" 2>&1 || adb shell su 0 dmesg > "$DMESG" 2>&1 || true
adb shell 'ls /sys/fs/pstore 2>/dev/null' > "$RUN_DIR/pstore-list.txt" 2>&1 || true
if grep -q . "$RUN_DIR/pstore-list.txt"; then
  while read -r p; do
    [[ -z "$p" ]] && continue
    adb shell "cat /sys/fs/pstore/$p" > "$PSTORE_DIR/$p" 2>/dev/null || true
  done < "$RUN_DIR/pstore-list.txt"
fi

{
  grep -iE 'avc:[[:space:]]*denied|selinux|audit' "$LOG" || true
  grep -iE 'avc:[[:space:]]*denied|selinux|audit' "$DMESG" || true
  if compgen -G "$PSTORE_DIR/*" >/dev/null; then
    grep -ihE 'avc:[[:space:]]*denied|selinux|audit' "$PSTORE_DIR"/* || true
  fi
} > "$DEN"

python3 "$(dirname "$0")/summarize_denials.py" "$DEN" --format markdown > "$SUMMARY" || true

if [[ "$CAPTURE_BUGREPORT" -eq 1 ]]; then
  adb bugreport "$RUN_DIR/bugreport.zip" >>"$RUN_DIR/adb-commands.log" 2>&1 || true
fi

printf 'RUN_DIR=%s\nLOG=%s\nDEN=%s\nDMESG=%s\nSTATE=%s\nMONKEY=%s\nSUMMARY=%s\n' \
  "$RUN_DIR" "$LOG" "$DEN" "$DMESG" "$STATE" "$MONKEY" "$SUMMARY"
