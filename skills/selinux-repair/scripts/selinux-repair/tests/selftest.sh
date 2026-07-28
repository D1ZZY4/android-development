#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE="$ROOT/tests/fixtures/p13001l"

python3 "$ROOT/build_error_triage.py" "$ROOT/tests/sample_build_error.log" --format markdown >/tmp/selinux-build-triage.md
python3 "$ROOT/selinux_build_doctor.py" "$ROOT/tests/sample_build_error.log" --repo "$ROOT" --format markdown >/tmp/selinux-build-doctor.md
python3 "$ROOT/selinux_build_doctor.py" "$ROOT/tests/sample_property_error.log" --repo "$ROOT" --format json >/tmp/selinux-property-doctor.json

python3 "$ROOT/sepolicy_path_resolver.py" --repo "$FIXTURE" --board-config BoardConfig.mk --format markdown >/tmp/sepolicy-source-map.md
grep -q "device/mediatek/sepolicy_vndr/SEPolicy.mk" /tmp/sepolicy-source-map.md
grep -q "BOARD_VENDOR_SEPOLICY_DIRS" /tmp/sepolicy-source-map.md
grep -q "Declared search roots" /tmp/sepolicy-source-map.md
grep -q "device/itel/P13001L/sepolicy/vendor" /tmp/sepolicy-source-map.md

python3 "$ROOT/property_context_doctor.py" --log "$ROOT/tests/sample_host_init_duplicate_prefix.log" --repo "$FIXTURE" --board-config BoardConfig.mk --format markdown >/tmp/property-context-doctor.md || true
grep -q "Resolved BoardConfig/include chain" /tmp/property-context-doctor.md
grep -q "duplicate_prefix_property.*ro.vendor.audio" /tmp/property-context-doctor.md
grep -q "duplicate_prefix_property.*vendor.streamin" /tmp/property-context-doctor.md
grep -q "duplicate_exact_property.*ro.vendor.mtk_cam_dualzoom_support" /tmp/property-context-doctor.md

python3 "$ROOT/selinux_build_doctor.py" "$ROOT/tests/sample_host_init_duplicate_prefix.log" --repo "$FIXTURE" --board-config BoardConfig.mk --format markdown >/tmp/source-map-aware-build-doctor.md
grep -q "Source-map search scope" /tmp/source-map-aware-build-doctor.md
grep -q "ro.vendor.audio" /tmp/source-map-aware-build-doctor.md
! grep -q "init.connfem.rc.*properties" /tmp/source-map-aware-build-doctor.md

python3 "$ROOT/build_error_triage.py" "$ROOT/tests/sample_duplicate_type_declaration.log" --format json >/tmp/duplicate-type-triage.json
python3 "$ROOT/context_conflict_finder.py" "$ROOT" --format markdown >/tmp/selinux-context-conflicts.md || true
python3 "$ROOT/summarize_denials.py" "$ROOT/tests/sample_denials.log" --format markdown >/tmp/selinux-denial-summary.md
python3 "$ROOT/audit_device_tree.py" "$ROOT" --format text >/tmp/selinux-tree-audit.txt || true
python3 -m py_compile "$ROOT"/*.py
bash -n "$ROOT"/*.sh
printf 'selftest ok\n'
