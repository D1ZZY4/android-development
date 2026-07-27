#!/usr/bin/env bash
# check_port_images.sh -- verify that required partition images are present and
# non-empty before starting a ROM port.
#
# Usage: ./check_port_images.sh <firmware_dir> [--transsion]
#
#   firmware_dir   Directory containing the extracted .img files.
#   --transsion    Also check for Transsion-specific extra images
#                  (tr_product.img, tr_region.img).
#
# Exit codes:
#   0  All required images present
#   1  One or more required images missing or empty

set -euo pipefail

FIRMWARE_DIR="${1:?Usage: $0 <firmware_dir> [--transsion]}"
CHECK_TRANSSION=0
if [ "${2:-}" = "--transsion" ]; then
    CHECK_TRANSSION=1
fi

if [ ! -d "$FIRMWARE_DIR" ]; then
    echo "ERROR: directory not found: $FIRMWARE_DIR" >&2
    exit 1
fi

REQUIRED_IMAGES=(
    "system.img"
    "vendor.img"
)

OPTIONAL_IMAGES=(
    "system_ext.img"
    "product.img"
    "odm.img"
)

TRANSSION_IMAGES=(
    "tr_product.img"
    "tr_region.img"
)

MISSING=0

check_image() {
    local label="$1"
    local path="$2"
    if [ ! -f "$path" ]; then
        echo "MISSING   [$label] $path"
        MISSING=$((MISSING + 1))
    elif [ ! -s "$path" ]; then
        echo "EMPTY     [$label] $path"
        MISSING=$((MISSING + 1))
    else
        size_kb=$(du -k "$path" | cut -f1)
        echo "OK        [$label] $path  (${size_kb} KB)"
    fi
}

echo "=== Checking partition images in: $FIRMWARE_DIR ==="
echo ""

echo "--- Required ---"
for img in "${REQUIRED_IMAGES[@]}"; do
    check_image "required" "$FIRMWARE_DIR/$img"
done

echo ""
echo "--- Optional (common) ---"
for img in "${OPTIONAL_IMAGES[@]}"; do
    if [ -f "$FIRMWARE_DIR/$img" ]; then
        check_image "optional" "$FIRMWARE_DIR/$img"
    else
        echo "NOT FOUND [optional] $FIRMWARE_DIR/$img"
    fi
done

if [ "$CHECK_TRANSSION" -eq 1 ]; then
    echo ""
    echo "--- Transsion-specific ---"
    for img in "${TRANSSION_IMAGES[@]}"; do
        check_image "transsion" "$FIRMWARE_DIR/$img"
    done
fi

echo ""
if [ "$MISSING" -gt 0 ]; then
    echo "RESULT: $MISSING required/transsion image(s) missing or empty. Fix before proceeding."
    exit 1
else
    echo "RESULT: all checked images present and non-empty."
fi
