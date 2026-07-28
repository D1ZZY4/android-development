#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: verify_policy_artifacts.sh <out/target/product/device> [report-dir]

Runs available host-side SELinux checks against built Android policy artifacts.
The script is best-effort: missing host tools are recorded instead of treated as
script failures.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

PRODUCT_OUT="$1"
REPORT_DIR="${2:-selinux-artifact-review/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/report.md"

find_policy() {
  local root="$1"
  for p in \
    "$root/root/sepolicy" \
    "$root/vendor/etc/selinux/precompiled_sepolicy" \
    "$root/system/etc/selinux/precompiled_sepolicy" \
    "$root/obj/ETC/sepolicy_intermediates/sepolicy"; do
    [[ -f "$p" ]] && { echo "$p"; return 0; }
  done
  find "$root" -type f \( -name sepolicy -o -name precompiled_sepolicy \) 2>/dev/null | head -n 1
}

POLICY="$(find_policy "$PRODUCT_OUT")"
{
  echo "# SELinux Artifact Verification"
  echo
  echo "- Product out: \`$PRODUCT_OUT\`"
  echo "- Report dir: \`$REPORT_DIR\`"
  echo "- Policy: \`${POLICY:-not found}\`"
  echo
  echo "## Artifact inventory"
  echo '```text'
  find "$PRODUCT_OUT" -path '*/etc/selinux/*' -o -path '*/obj/ETC/*sepolicy*' 2>/dev/null | sed "s#^$PRODUCT_OUT/##" | sort | head -n 300 || true
  echo '```'
  echo
} > "$REPORT"

run_check() {
  local title="$1"; shift
  local outfile="$REPORT_DIR/$title.txt"
  {
    echo "## $title"
    echo
    echo '```text'
    if "$@" > "$outfile" 2>&1; then
      cat "$outfile"
      echo '```'
      echo
      echo "Status: PASS"
    else
      cat "$outfile"
      echo '```'
      echo
      echo "Status: REVIEW/FAIL"
    fi
    echo
  } >> "$REPORT"
}

if [[ -z "$POLICY" ]]; then
  {
    echo "## sepolicy-analyze"
    echo
    echo "No binary policy found. Build policy artifacts first."
  } >> "$REPORT"
else
  if command -v sepolicy-analyze >/dev/null 2>&1; then
    run_check "sepolicy-analyze-permissive" sepolicy-analyze "$POLICY" permissive
    run_check "sepolicy-analyze-booleans" sepolicy-analyze "$POLICY" booleans
    run_check "sepolicy-analyze-dups" sepolicy-analyze "$POLICY" dups
  else
    {
      echo "## sepolicy-analyze"
      echo
      echo "Host tool \`sepolicy-analyze\` not found in PATH. Build AOSP host tools or add out/host/linux-x86/bin to PATH."
      echo
    } >> "$REPORT"
  fi
fi

if command -v checkfc >/dev/null 2>&1 && [[ -n "$POLICY" ]]; then
  while IFS= read -r ctx; do
    [[ -f "$ctx" ]] || continue
    safe_name="$(echo "$ctx" | sed 's#[^A-Za-z0-9_.-]#_#g')"
    run_check "checkfc-$safe_name" checkfc "$POLICY" "$ctx"
  done < <(find "$PRODUCT_OUT" -path '*/etc/selinux/*_contexts' -type f 2>/dev/null | sort)
else
  {
    echo "## checkfc"
    echo
    echo "Host tool \`checkfc\` or binary policy not available; skipping context validation."
    echo
  } >> "$REPORT"
fi

printf 'REPORT=%s\nPOLICY=%s\n' "$REPORT" "${POLICY:-}"
