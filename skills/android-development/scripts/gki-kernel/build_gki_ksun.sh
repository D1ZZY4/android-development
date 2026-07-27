#!/usr/bin/env bash
# build_gki_ksun.sh -- Set up a GKI kernel workspace, integrate KernelSU-Next
# via the official setup.sh script, and kick off a build.sh-based build.
#
# This script targets build.sh-era GKI trees (android12-5.10, android13-5.10,
# android13-5.15). For Bazel/Kleaf trees, apply KSU-Next patches manually and
# register the module in BUILD.bazel instead.
#
# Usage:
#   ./build_gki_ksun.sh <manifest_branch> <build_config> [lto]
#
#   manifest_branch  e.g. common-android12-5.10
#   build_config     path to build.config relative to workspace root,
#                    e.g. common/build.config.gki.aarch64
#   lto              full (default) | thin | none
#
# The script creates an android-kernel/ subdirectory in the current directory
# and builds there. Run from an empty working directory.

set -euo pipefail

MANIFEST_BRANCH="${1:?Usage: $0 <manifest_branch> <build_config> [lto]}"
BUILD_CONFIG="${2:?Usage: $0 <manifest_branch> <build_config> [lto]}"
LTO_MODE="${3:-full}"

WORKSPACE="android-kernel"
LOG_FILE="/tmp/gki_ksun_build_$(date +%Y%m%d_%H%M%S).log"
KSUN_SETUP_URL="https://raw.githubusercontent.com/KernelSU-Next/KernelSU-Next/refs/heads/dev/kernel/setup.sh"

case "$LTO_MODE" in
  full|thin|none) ;;
  *)
    echo "ERROR: lto must be 'full', 'thin', or 'none' (got: $LTO_MODE)" >&2
    exit 1
    ;;
esac

echo "=== GKI + KernelSU-Next build ==="
echo "Branch      : $MANIFEST_BRANCH"
echo "Build config: $BUILD_CONFIG"
echo "LTO         : $LTO_MODE"
echo "Workspace   : $(pwd)/$WORKSPACE"
echo ""

# --- Step 1: workspace ---
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"

if [ -d ".repo" ]; then
  echo "[1/4] .repo already exists -- skipping repo init"
else
  echo "[1/4] Initialising repo manifest: $MANIFEST_BRANCH"
  repo init \
    -u https://android.googlesource.com/kernel/manifest \
    -b "$MANIFEST_BRANCH" \
    --depth=1
fi

echo "[2/4] Syncing sources..."
repo sync -c --no-tags --no-clone-bundle --optimized-fetch -j"$(nproc)"

# --- Step 2: KernelSU-Next ---
if [ ! -d "common/KernelSU" ] && [ ! -f "common/fs/ksu.h" ]; then
  echo "[3/4] Applying KernelSU-Next via setup.sh..."
  curl -LSs "$KSUN_SETUP_URL" | bash -
else
  echo "[3/4] KernelSU-Next patches already present -- skipping setup.sh"
fi

# Commit any uncommitted KSU changes so the build gets a clean git describe
cd common
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "      Committing KernelSU-Next changes in common/..."
  git add -A
  git commit -m "kernel: add KernelSU-Next" || echo "      Nothing to commit"
else
  echo "      common/ is clean, no commit needed"
fi
cd ..

# --- Step 3: build ---
if [ ! -x "build/build.sh" ]; then
  echo "ERROR: build/build.sh not found -- is this actually a build.sh-era GKI tree?" >&2
  echo "       For Bazel/Kleaf trees, use scripts/gki-kernel/build_gki_kernel.sh bazel <target>" >&2
  exit 1
fi

echo "[4/4] Starting build in background -- log: $LOG_FILE"

BUILD_ENV=(
  "BUILD_CONFIG=$BUILD_CONFIG"
)
if [ "$LTO_MODE" != "none" ]; then
  BUILD_ENV+=("LTO=$LTO_MODE")
fi

nohup env "${BUILD_ENV[@]}" ./build/build.sh > "$LOG_FILE" 2>&1 &
BUILD_PID=$!

echo "Build PID : $BUILD_PID"
echo "Log       : $LOG_FILE"
echo ""
echo "Tail the log  : tail -f $LOG_FILE"
echo "First error   : grep -n -m1 -E 'error:|FAILED:' $LOG_FILE"
echo "Output dir    : $(pwd)/out/*/dist/"
echo ""
echo "When the build finishes, look for Image, Image.lz4, and System.map"
echo "under out/<branch>/dist/."
