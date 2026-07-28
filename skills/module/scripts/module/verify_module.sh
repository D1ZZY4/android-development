#!/usr/bin/env bash
# verify_module.sh -- validate a Magisk/KernelSU module directory before packaging
#
# Usage:
#   bash scripts/module/verify_module.sh <module_dir>
#
# Checks:
#   - module.prop exists and has all required fields filled in
#   - id contains only allowed characters
#   - versionCode is an integer
#   - Any shell scripts present pass bash -n syntax check and have a shebang
#
# Exit code 0 = no errors (warnings may still be printed).
# Exit code 1 = one or more errors found.

set -euo pipefail

MODULE_DIR="${1:?Usage: $0 <module_dir>}"

ERRORS=0
WARNINGS=0

err()  { echo "ERROR: $*" >&2; ERRORS=$((ERRORS + 1)); }
warn() { echo "WARN:  $*";     WARNINGS=$((WARNINGS + 1)); }
info() { echo "INFO:  $*"; }

[ -d "$MODULE_DIR" ] || { echo "ERROR: '$MODULE_DIR' is not a directory" >&2; exit 1; }

prop_value() {
    # Return the first exact key match. awk exits successfully when absent so
    # set -e and pipefail do not stop validation before all errors are reported.
    awk -F= -v key="$1" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' "$PROP"
}

echo "=== Module validation: $MODULE_DIR ==="
echo ""

# --- module.prop ---
PROP="$MODULE_DIR/module.prop"

if [ ! -f "$PROP" ]; then
    err "module.prop is missing"
else
    info "module.prop found"

    for field in id name version versionCode author description; do
        raw=$(prop_value "$field")
        val=$(echo "$raw" | tr -d '[:space:]')
        if [ -z "$val" ]; then
            err "module.prop: '$field' is empty"
        elif echo "$val" | grep -q '<'; then
            err "module.prop: '$field' still contains a placeholder (got: $raw)"
        fi
    done

    id_val=$(prop_value id | tr -d '[:space:]')
    if [ -n "$id_val" ] && echo "$id_val" | grep -qE '[[:space:]]|[^a-z0-9._-]'; then
        err "module.prop: 'id' must use lowercase letters, digits, dots, hyphens, underscores (got: $id_val)"
    fi

    vc_val=$(prop_value versionCode | tr -d '[:space:]')
    if [ -n "$vc_val" ] && ! echo "$vc_val" | grep -qE '^[0-9]+$'; then
        err "module.prop: 'versionCode' must be an integer (got: $vc_val)"
    fi

    if grep -q "^updateJson=<" "$PROP" 2>/dev/null; then
        warn "module.prop: 'updateJson' still a placeholder -- remove or fill in a real URL"
    fi
fi

# --- shell scripts ---
for script in post-fs-data.sh service.sh boot-completed.sh post-mount.sh uninstall.sh action.sh; do
    f="$MODULE_DIR/$script"
    [ -f "$f" ] || continue
    first=$(head -1 "$f")
    if ! echo "$first" | grep -q '^#!'; then
        warn "$script: missing shebang on line 1"
    fi
    if ! bash -n "$f" 2>/dev/null; then
        err "$script: shell syntax error (run 'bash -n $f' for details)"
    else
        info "$script: syntax OK"
    fi
done

# --- system overlay ---
if [ -d "$MODULE_DIR/system" ]; then
    count=$(find "$MODULE_DIR/system" -type f | wc -l)
    info "system/ overlay: $count file(s)"
    if [ "$count" -eq 0 ]; then
        warn "system/ directory exists but contains no files"
    fi
fi

# --- sepolicy.rule ---
if [ -f "$MODULE_DIR/sepolicy.rule" ]; then
    lines=$(grep -c . "$MODULE_DIR/sepolicy.rule" 2>/dev/null || echo 0)
    info "sepolicy.rule: $lines rule(s) -- verify each is minimal and tested"
fi

# --- Zygisk ---
if [ -d "$MODULE_DIR/zygisk" ]; then
    info "zygisk/ present -- ensure .so files are provided for all required ABIs"
fi

# --- webroot (KernelSU/KSU-Next WebUI) ---
if [ -d "$MODULE_DIR/webroot" ]; then
    if [ ! -f "$MODULE_DIR/webroot/index.html" ]; then
        warn "webroot/ present but index.html is missing"
    else
        info "webroot/index.html found"
    fi
fi

echo ""
echo "Result: $ERRORS error(s), $WARNINGS warning(s)"

if [ "$ERRORS" -eq 0 ]; then
    echo "Module structure OK -- ready for package review."
    exit 0
else
    echo "Fix the errors above before packaging." >&2
    exit 1
fi
