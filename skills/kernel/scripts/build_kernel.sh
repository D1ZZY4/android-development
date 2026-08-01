#!/usr/bin/env bash
# Legacy (non-GKI) kernel build wrapper template. Assumes a single
# monolithic kernel tree with arch/arm64/configs/<defconfig>. For GKI
# trees use the gki-kernel skill instead — this script's `make` approach
# will not produce a correct GKI split-module build.
#
# Usage: ./build_kernel.sh <defconfig_name> [jobs]

set -euo pipefail

DEFCONFIG="${1:?Usage: $0 <defconfig_name> [jobs]}"
JOBS="${2:-$(nproc --all)}"
LOG_FILE="/tmp/kernel_build_$(date +%Y%m%d_%H%M%S).log"

if [ ! -f "Makefile" ] || ! grep -q "^VERSION" Makefile 2>/dev/null; then
  echo "ERROR: doesn't look like a kernel source root (no top-level Makefile with VERSION)." >&2
  exit 1
fi

export ARCH=arm64
export SUBARCH=arm64
export CC=clang
: "${CROSS_COMPILE:=aarch64-linux-android-}"
export CROSS_COMPILE

echo "Configuring with $DEFCONFIG..."
make O=out ARCH=arm64 "$DEFCONFIG"

echo "Building with $JOBS jobs, logging to: $LOG_FILE"
nohup make O=out ARCH=arm64 -j"$JOBS" > "$LOG_FILE" 2>&1 &
BUILD_PID=$!
echo "Build PID: $BUILD_PID"
echo "Tail the log with: tail -f $LOG_FILE"
echo "Expected output: out/arch/arm64/boot/Image.gz-dtb (or Image/Image.lz4 depending on device)"
