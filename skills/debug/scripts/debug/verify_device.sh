#!/usr/bin/env bash
# Read-only live-verification helper for the Debug Workflow's Step 3.
# Wraps common adb read commands. NEVER add mutating commands to this
# script (no setprop, no flash, no reboot, no rm/dd) — it exists
# specifically to make the "read-only only" constraint hard to violate
# by accident.
#
# Usage:
#   ./verify_device.sh perms <path>          # ls -lZ
#   ./verify_device.sh prop <name_or_grep>    # getprop | grep
#   ./verify_device.sh service <name>          # dumpsys <name>
#   ./verify_device.sh ps                        # ps -A
#   ./verify_device.sh hal                        # lshal
#   ./verify_device.sh sysfs <path>              # cat /sys/...
#   ./verify_device.sh selinux                    # getenforce

set -euo pipefail

cmd="${1:-}"
arg="${2:-}"

case "$cmd" in
  perms)
    [ -n "$arg" ] || { echo "usage: $0 perms <path>"; exit 1; }
    adb shell ls -lZ "$arg"
    ;;
  prop)
    [ -n "$arg" ] || { echo "usage: $0 prop <name_or_grep>"; exit 1; }
    adb shell getprop | grep -i -- "$arg"
    ;;
  service)
    [ -n "$arg" ] || { echo "usage: $0 service <name>"; exit 1; }
    adb shell dumpsys "$arg"
    ;;
  ps)
    adb shell ps -A
    ;;
  hal)
    adb shell lshal
    ;;
  sysfs)
    [ -n "$arg" ] || { echo "usage: $0 sysfs <path>"; exit 1; }
    adb shell cat "$arg"
    ;;
  selinux)
    adb shell getenforce
    ;;
  *)
    echo "Read-only ADB verification helper. Subcommands:"
    echo "  perms <path>          -> ls -lZ"
    echo "  prop <name_or_grep>   -> getprop | grep"
    echo "  service <name>        -> dumpsys <name>"
    echo "  ps                    -> ps -A"
    echo "  hal                   -> lshal"
    echo "  sysfs <path>          -> cat <path>"
    echo "  selinux               -> getenforce"
    exit 1
    ;;
esac
