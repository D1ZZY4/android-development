#!/usr/bin/env bash
# ROM build wrapper template. Backgrounds the build and logs to a file so
# a long build doesn't block the session. Adjust TARGET/BUILD_CMD for the
# specific ROM (LineageOS uses breakfast+mka bacon; other AOSP forks may
# use lunch+mka <target> or a custom brunch-equivalent).
#
# Usage: ./build_rom.sh <codename> [build_type]
#   build_type: userdebug (default) | user | eng

set -euo pipefail

CODENAME="${1:?Usage: $0 <codename> [build_type]}"
BUILD_TYPE="${2:-userdebug}"
LOG_FILE="/tmp/rom_build_${CODENAME}_$(date +%Y%m%d_%H%M%S).log"

if [ ! -d ".repo" ]; then
  echo "ERROR: no .repo/ found — this doesn't look like a synced manifest workspace." >&2
  echo "Run 'repo init' + set up local_manifests first (see template/rom/)." >&2
  exit 1
fi

echo "Syncing sources (this can take a while)..."
repo sync -c -j"$(nproc --all)" --force-sync --no-clone-bundle --no-tags

echo "Setting up build environment..."
source build/envsetup.sh

# Prefer breakfast if available (LineageOS-style), fall back to lunch
if type breakfast >/dev/null 2>&1; then
  breakfast "$CODENAME"
else
  lunch "lineage_${CODENAME}-${BUILD_TYPE}" || lunch "${CODENAME}-${BUILD_TYPE}"
fi

echo "Starting build in background, logging to: $LOG_FILE"
# Prefer brunch (LineageOS modern), fall back to mka bacon
if type brunch >/dev/null 2>&1; then
  nohup brunch "$CODENAME" > "$LOG_FILE" 2>&1 &
else
  nohup mka bacon > "$LOG_FILE" 2>&1 &
fi
BUILD_PID=$!
echo "Build PID: $BUILD_PID"
echo "Tail the log with: tail -f $LOG_FILE"
echo "Check for first error with: grep -n -m1 -E 'error:|FAILED:|\*\*\* ' $LOG_FILE"
