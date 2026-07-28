
# SELinux Repair -- Reference

Tool index and evidence hierarchy. Full workflow lives in AGENTS.md.

## Tools (scripts/)

| Script | Purpose |
|---|---|
| `sepolicy_path_resolver.py` | Resolve makefile-declared policy roots (BOARD_*/PRODUCT_*/SYSTEM_EXT_* SEPOLICY_DIRS) before broad search |
| `build_error_triage.py` | First-failure classifier from a build log |
| `selinux_build_doctor.py` | Build-log + repo-aware repair plan generator |
| `property_context_doctor.py` | Diagnoses property_contexts duplicate/serialize failures |
| `context_conflict_finder.py` | Focused duplicate/overlap scanner for context files |
| `audit_device_tree.py` | Static device-tree policy audit (no build log needed) |
| `capture_selinux_denials.sh` | Captures runtime AVC denials from a connected device |
| `summarize_denials.py` | Groups/prioritizes captured runtime denials |
| `verify_policy_artifacts.sh` | Runs sepolicy-analyze/checkfc against already-built policy artifacts |

## Evidence hierarchy (prefer in this order)

1. Policy source map from BoardConfig/product makefiles
2. First deterministic build failure (checkpolicy, secilc, checkfc, etc.)
3. Generated build intermediates (merged policy.conf, property_contexts, .cil)
4. Runtime boot denials (dmesg, pstore/ramoops, early logcat -b all)
5. Targeted runtime reproduction denials
6. Static audit of resolved policy roots
7. Existing AOSP/ROM public policy patterns and macros
8. Broad full-tree search -- only after the policy source map is exhausted
9. audit2allow output -- a hint only, never a patch to apply blindly

## Common failure signatures

| Log contains | Likely cause | First tool |
|---|---|---|
| `neverallow` violation | New rule collides with platform neverallow assertion | build_error_triage.py |
| `unknown type`/`unknown attribute` | Referenced type not declared or not visible | sepolicy_path_resolver.py |
| `duplicate declaration` | Same type/property declared in two roots | context_conflict_finder.py |
| `Unable to serialize property contexts` | Property-context trie conflict | property_context_doctor.py |
| `checkfc` invalid context | Undeclared/mistyped type | context_conflict_finder.py |
| `host_init_verifier` error | .rc file references label policy doesn't grant | sepolicy_path_resolver.py |
| Runtime `avc: denied` with generic tcontext | Object needs its own label before allow rule | summarize_denials.py |
