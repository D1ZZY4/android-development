#!/usr/bin/env bash
# GKI kernel build wrapper template. Detects whether the tree uses the
# older build/build.sh flow or the newer Bazel/Kleaf flow and builds
# accordingly. Check REFERENCE.md § GKI Kernel Build before assuming
# either path is correct for a given tree — target names and config
# fragment paths vary a lot between branches/vendors.
#
# Usage:
#   ./build_gki_kernel.sh buildsh <BUILD_CONFIG_path>
#   ./build_gki_kernel.sh bazel <bazel_target>

set -euo pipefail

MODE="${1:?Usage: $0 <buildsh|bazel> <build_config_path_or_bazel_target>}"
ARG="${2:?Usage: $0 <buildsh|bazel> <build_config_path_or_bazel_target>}"
LOG_FILE="/tmp/gki_kernel_build_$(date +%Y%m%d_%H%M%S).log"

case "$MODE" in
  buildsh)
    if [ ! -x "build/build.sh" ]; then
      echo "ERROR: build/build.sh not found or not executable — is this actually a build.sh-era GKI tree?" >&2
      exit 1
    fi
    echo "Building with build.sh, BUILD_CONFIG=$ARG, logging to: $LOG_FILE"
    nohup env BUILD_CONFIG="$ARG" build/build.sh > "$LOG_FILE" 2>&1 &
    echo "Build PID: $!"
    echo "Output expected under: out/<branch>/dist/ (Image, System.map, vendor .ko modules)"
    ;;
  bazel)
    if [ ! -x "tools/bazel" ]; then
      echo "ERROR: tools/bazel not found — is this actually a Kleaf/Bazel-era GKI tree?" >&2
      exit 1
    fi
    echo "Building with Bazel target: $ARG, logging to: $LOG_FILE"
    nohup tools/bazel run "$ARG" -- --dist_dir=out/dist > "$LOG_FILE" 2>&1 &
    echo "Build PID: $!"
    echo "Output expected under: out/dist/"
    ;;
  *)
    echo "Unknown mode: $MODE (expected 'buildsh' or 'bazel')" >&2
    exit 1
    ;;
esac

echo "Tail the log with: tail -f $LOG_FILE"
echo "Watch for KMI/ABI mismatch errors — see REFERENCE.md § GKI-specific failure modes"
