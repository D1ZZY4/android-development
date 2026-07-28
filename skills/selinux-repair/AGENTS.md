
# SELinux Repair -- AI Agent Entry Point

Repair SELinux policy build failures and runtime AVC denials on Android devices. Policy source-map-first, narrowest-fix discipline, evidence-driven at every step.

Activate on: avc: denied, neverallow, sepolicy, property_contexts, checkpolicy/checkfc errors, host_init_verifier, property_info_serializer, policy build failure, runtime denial, type/attribute conflicts, sepolicy_tests failure.

Read REFERENCE.md for the tool index and evidence hierarchy. Use references/ for deep-dive playbooks.

## Hard Constraints

1. Never instruct or run a live-device mutation without explicit user
   confirmation. SELinux capture scripts (capture_selinux_denials.sh) have opt-in flags (--root, --auditctl) that are runtime-affecting -- gate behind user confirmation.

2. Evidence over guessing. Collect the first deterministic failure, classify
   it, and fix the root cause, not a cascade symptom.

3. Never recommend: permissive domains as a final fix,
   SELINUX_IGNORE_NEVERALLOWS := true, generic-label allow rules (sysfs, proc, device, default_prop, default_android_service), dontaudit to hide failures, or raw audit2allow output as a ready-to-apply patch.

## SELinux Repair Workflow

Full command index: REFERENCE.md. Templates: template/ (safe_policy_patterns.md, dangerous_patterns_to_reject.md, patch_output_contract.md) Scripts: scripts/ (see REFERENCE.md for the full list) References: references/ (start with README.md)

Operating rule: collect the first reliable failure, classify it, fix ownership and labeling before permissions, add the smallest policy rule last, and verify with build-time and runtime gates. A successful repair is narrow, explainable, partition-correct, and public/private-policy-boundary-compatible. The build passing alone is not success.

### Steps (in order)

1. Resolve the policy source map first -- before any broad repo search, find
   the exact makefile-declared policy roots:

   scripts/sepolicy_path_resolver.py \ --repo . \ --board-config device/\<vendor\>/\<device\>/BoardConfig.mk \ --format markdown

2. Classify from the failure mode:

   Build failure: scripts/build_error_triage.py build.log --format markdown scripts/selinux_build_doctor.py build.log \ --repo . --board-config \<path\> --format markdown

   Property-context duplicate or serialize errors: scripts/property_context_doctor.py \ --log build.log --repo . --board-config \<path\> --format markdown

   Boots but logs runtime denials: scripts/capture_selinux_denials.sh \ --root --auditctl --events 1500 --throttle 150 scripts/summarize_denials.py \<captured-log\> --format markdown Note: --root and --auditctl are runtime-mutating. Require user confirmation.

   Only the tree is available (no build log): scripts/audit_device_tree.py \<path\> --format markdown scripts/context_conflict_finder.py \<path\> --format markdown

   Artifacts already built: scripts/verify_policy_artifacts.sh out/target/product/\<device\>

3. Fix only the first real blocker. Parallel Android builds cascade; a single
   root property or type conflict often produces dozens of downstream FAILED:.

4. Classify by cause in this order:
   build/verifier failure -> labeling failure -> domain transition failure -> partition ownership failure -> missing public API or private-symbol boundary failure -> real permission gap -> debug-only access that should not ship in production policy.

5. Repair by cause, not symptom. For every issue, determine: which domain is
   acting, which exact object is targeted, which class and permission is requested, whether the target label is still generic (needs relabeling before an allow rule), which partition should own it, and whether vendor policy is referencing only public platform symbols. Safe shapes: template/safe_policy_patterns.md Dangerous shapes: template/dangerous_patterns_to_reject.md

6. Verify before moving on:
   m sepolicy_tests m vendor_sepolicy.cil plat_sepolicy.cil || true Re-run the path resolver and scripts/verify_policy_artifacts.sh out/target/product/\<device\>.

### Output contract

Any proposed SELinux fix must include all 8 fields in template/patch_output_contract.md:
  1. Failure class
  2. First evidence line
  3. Root cause hypothesis
  4. Files to edit
  5. Patch shape
  6. Why this is safe
  7. Validation commands
  8. What not to do

Never output a raw audit2allow blob as the final answer -- convert it into a reviewed patch plan using this contract.

## Evidence Hierarchy

Prefer evidence sources in this order:

1. Policy source map from BoardConfig and product makefiles (narrows search
   before any broad repo scan).
2. First deterministic build failure (checkpolicy, secilc, checkfc,
   host_init_verifier, property_info_serializer, sepolicy_tests, se_neverallow_test).
3. Generated build intermediates (merged policy.conf, merged
   property_contexts, generated .cil files).
4. Runtime boot denials (dmesg, pstore/ramoops, early logcat -b all).
5. Targeted runtime reproduction denials after triggering the failing feature.
6. Static audit of the resolved device/vendor/product/system_ext policy roots.
7. Existing AOSP/ROM public policy patterns and macros.
8. Broad full-tree search -- only after the policy source map is exhausted.
9. audit2allow output -- a hint only, never a patch to apply blindly.

## File and Folder Map

```
skills/selinux-repair/
  AGENTS.md   AI agent router and workflow
  README.md   human-readable overview
  REFERENCE.md command/tool index
  SKILL.md    skills.sh entry point
  template/   safe_policy_patterns.md, dangerous_patterns_to_reject.md, patch_output_contract.md
  scripts/    Python and shell tools (see REFERENCE.md)
    tests/    selftest.sh and sample fixture logs
      fixtures/ BoardConfig.mk, property_contexts, .te files for testing
  references/ deep-dive playbooks (start with README.md)
```
