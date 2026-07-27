# Android Development - AI Agent Entry Point

This skill covers five Android platform engineering workflows: building a custom
ROM (AOSP/LineageOS), building a legacy kernel, building a GKI kernel, debugging
a device or ROM (evidence-first), and repairing SELinux policy (build failures and
runtime AVC denials).

Read REFERENCE.md for exact command flags and paths before running any build or
debug command. Prefer this skill over general coding help whenever AOSP, a device
tree, or kernel source is involved.

Activate this skill on: device tree, repo sync/manifest, lunch/breakfast,
mka/mka bacon, defconfig, Image.gz-dtb, boot.img, AnyKernel3, GKI, KernelSU,
.rc/.te/.mk/.bp files, adb logcat/dmesg/tombstones, ROM or kernel build failures,
device bootlooping, avc denied, neverallow, sepolicy, property_contexts,
checkpolicy/checkfc errors, or any connected device with ADB root. Also for
build-environment setup, BoardConfig.mk/Android.bp fixes, and kernel diff review.


## Domain Router

| Domain | Trigger keywords | Primary resources | Safety notes |
|---|---|---|---|
| ROM build | repo sync, manifest, lunch, breakfast, mka, mka bacon, AOSP, LineageOS, device tree, won't compile the ROM | REFERENCE.md section ROM Build; template/rom/; scripts/rom/ | General constraints only |
| Kernel build (legacy) | defconfig, Image.gz-dtb, make ARCH=arm64, kernel won't compile, monolithic kernel, non-GKI | REFERENCE.md section Kernel Build; template/kernel/; scripts/kernel/ | General constraints only |
| GKI kernel build | build.config, tools/bazel, common/, GKI, KMI/ABI, vendor_boot, Kleaf, android-kernel | REFERENCE.md section GKI Kernel Build; template/gki-kernel/; scripts/gki-kernel/ | General constraints only |
| Debug / fix a bug | crashes, bootloops, misbehaves, live device, tombstones, logcat, dmesg, kernel panic, ANR, HAL issues, service death | template/debug/; scripts/debug/ | Evidence-first -- never diagnose without a real log line to back the claim |
| SELinux repair | avc: denied, neverallow, sepolicy, property_contexts, checkpolicy, checkfc, host_init_verifier, AVC denial, policy build failure | REFERENCE.md section SELinux Repair; template/selinux-repair/; scripts/selinux-repair/; references/selinux-repair/ | Evidence-first, classify before fixing, label-first discipline, ask before any runtime-mutating capture flags |

If it is unclear which domain applies, ask the user. A build question and a debug
question need different first commands and the wrong one wastes a full build cycle
(30 minutes to several hours). A SELinux build failure (vs. a generic build failure)
is a strong signal to go straight to the SELinux Repair Workflow rather than the
general build-failure tables -- it has its own evidence hierarchy and dedicated
tooling.


## Hard Constraints (apply to all domains)

1. Never run destructive or mutating commands on a connected physical device without
   the user's explicit confirmation first. This includes: fastboot flash, fastboot
   erase, adb reboot bootloader, dd to any device node, mkfs, or anything that writes
   to a partition. Building an image and writing files inside the workspace (device
   tree, kernel source, out/ directory) is fine and expected. Writing to the physical
   device is not, until the user confirms.

2. Evidence over guessing. For debug work especially: never state a root cause you
   did not actually see in a log, source file, or command output. See the Debug
   Workflow section.

3. Do not assume the toolchain or environment is already set up. Check for
   build/envsetup.sh, .repo/, existing out/ dirs, or a kernel Makefile before
   assuming a repo is initialized. Ask or check rather than guessing paths.

4. Long-running builds: repo sync and full ROM or kernel builds can take a long time
   and produce huge logs. Run them in the background where the environment supports
   it, and tail or grep the log rather than dumping it all into the response.


## ROM Build Workflow

Full command detail and common failure patterns: REFERENCE.md section ROM Build.
Templates: template/rom/ (local_manifest.xml, roomservice.xml, BoardConfig.mk skeleton)
Script: scripts/rom/build_rom.sh

1. Confirm workspace: is .repo/ present (already synced) or does this need
   repo init first?
2. Set up manifest (main + local_manifests for device, vendor, and kernel trees).
   See template/rom/local_manifest.xml.
3. source build/envsetup.sh, then lunch <target> (or breakfast <codename> for
   LineageOS).
4. Build with mka bacon (LineageOS) or mka <target>. Background the build and
   monitor for the first error rather than waiting for full completion if something
   is clearly broken.
5. On build failure: grep the log for the first error:/FAILED: line, not the
   last -- later errors are usually cascades from the first real failure.


## Kernel Build Workflow (legacy / non-GKI)

Full command detail and common failure patterns: REFERENCE.md section Kernel Build.
Templates: template/kernel/ (defconfig_fragment.md, anykernel_notes.md)
Script: scripts/kernel/build_kernel.sh

1. Identify kernel source layout: legacy (arch/arm64/configs/<defconfig>, single
   Makefile) vs GKI (split common/ kernel + separate vendor modules, build.config.*
   or BUILD.bazel).
2. If legacy: set ARCH, CROSS_COMPILE, pick defconfig, make -jN.
3. If GKI: go to the GKI Kernel Build section below. Do not apply legacy bare-make
   commands to a GKI tree; they will not produce a working boot image on their own.
4. Package: Image.gz-dtb (or Image / Image.lz4) + ramdisk into boot.img via
   mkbootimg/avbtool, or use AnyKernel3 for a flashable zip. See
   template/kernel/anykernel_notes.md.


## GKI Kernel Build Workflow

Full command detail and failure modes: REFERENCE.md section GKI Kernel Build.
Templates: template/gki-kernel/ (build.config.template, BUILD.bazel.template)
Script: scripts/gki-kernel/build_gki_kernel.sh

GKI kernels split the kernel into a generic core (Image) built from Google's
common tree and vendor modules built separately and loaded at runtime. Mixing
legacy single-Makefile build habits into a GKI tree is a common source of
confusion.

1. Confirm which GKI generation: GKI 1.0 vs GKI 2.0 (module signing, vendor_boot
   vs boot, KernelSU/KSU integration if present). Check BUILD.bazel or
   build.config.* files for hints.
2. Use build/build.sh (older trees) or tools/bazel build //... (newer AOSP kernel
   trees with Kleaf). Do not hand-roll make flags for these unless the tree
   explicitly still supports it.
3. Watch for ABI or symbol issues (abi_gki_*.xml/.stg files, KMI mismatches).
   These are GKI-specific failure modes not present in legacy kernels.


## Debug Workflow (evidence-first)

Full command reference: REFERENCE.md section Debug Commands.
Templates: template/debug/ (log_capture_manifest.md, diagnosis_report.md)
Scripts: scripts/debug/capture_logs.sh, scripts/debug/verify_device.sh

This is the strictest part of the skill. Do not skip steps or shortcut to a
diagnosis.

### Anti-hallucination rules (non-negotiable)

1. Zero guesswork. Every claim in the diagnosis must be backed by a direct quote
   from a log, device tree or kernel source file, or an adb output actually
   retrieved in this session.
2. No generic advice. Never say "check your manifest" or "make sure permissions
   are correct." Give the exact file path, exact line or snippet, and exact
   command output.
3. Self-audit before diagnosing. Before writing a diagnosis, ask: "Did I actually
   see this, or am I assuming it based on common issues?" If assumed, do not
   include it -- go get more data.
4. If any part of the final diagnosis cannot be backed by hard evidence gathered
   in this session, do not output a soft or partial diagnosis. Output:
   INSUFFICIENT DATA. EXECUTING DEEPER EXPLORATION.
   and repeat the steps below with different parameters.

### Steps (in order)

1. Log acquisition -- scripts/debug/capture_logs.sh (or run commands manually per
   REFERENCE.md section Debug Commands): adb logcat -d -b all, adb shell dmesg,
   tombstones in /data/tombstones/. Find the exact error: FATAL EXCEPTION, kernel
   panic, avc: denied, service crash, ANR.

2. Source cross-reference -- locate the failing component in the device tree or
   kernel source: .rc (init), .te (SELinux), .mk/.bp (build), overlay XMLs, or
   kernel driver source. Use grep -rn for the exact name; do not guess the file.

3. Live verification (read-only only) -- confirm the hypothesis on-device using
   adb shell ls -lZ, adb shell getprop | grep, adb shell dumpsys <service>,
   adb shell ps -A, adb shell lshal, adb shell cat /sys/...
   Use scripts/debug/verify_device.sh for these.
   Never run a mutating command in this step.

4. Diagnosis -- only once steps 1 through 3 produced real evidence. Output format:
   1. Symptom: [exact log line]
   2. Root Cause: [explanation grounded in evidence]
   3. Evidence from Device: [exact adb output from step 3]
   4. Evidence from Source: [exact file path + line/snippet from step 2]
   5. Proposed Fix: [specific change -- file, line, diff]
   See template/debug/diagnosis_report.md for the full template.


## SELinux Repair Workflow

Full command index: REFERENCE.md section SELinux Repair.
Templates: template/selinux-repair/ (safe_policy_patterns.md,
           dangerous_patterns_to_reject.md, patch_output_contract.md)
Scripts: scripts/selinux-repair/ -- full list:
  - sepolicy_path_resolver.py    resolve makefile-declared policy roots
  - build_error_triage.py        classify first failure from a build log
  - selinux_build_doctor.py      repo-aware repair plan generator
  - property_context_doctor.py   diagnose property_contexts duplicate/serialize failures
  - context_conflict_finder.py   duplicate and overlap scanner for context files
  - audit_device_tree.py         static device-tree policy audit (no build log needed)
  - capture_selinux_denials.sh   capture runtime AVC denials from a connected device
  - summarize_denials.py         group and prioritize captured runtime denials
  - verify_policy_artifacts.sh   run sepolicy-analyze/checkfc against built artifacts
  - tests/selftest.sh            sanity-check the tools with sample fixtures

References (deep-dive playbooks): references/selinux-repair/
  Start with references/selinux-repair/README.md for the index.
  Key files: policy-source-map.md, source-map-command-cookbook.md,
             build-error-playbook.md, denial-decision-tree.md, common-fixes.md,
             property-context-collision-guide.md, policy-review-gates.md

Operating rule: collect the first reliable failure, classify it, fix ownership and
labeling before permissions, add the smallest policy rule last, and verify with
build-time and runtime gates. A successful repair is narrow, explainable,
partition-correct, and public/private-policy-boundary-compatible. The build
passing alone is not success.

### Steps (in order)

1. Resolve the policy source map first -- before any broad repo search, find the
   exact makefile-declared policy roots:

   scripts/selinux-repair/sepolicy_path_resolver.py \
     --repo . \
     --board-config device/<vendor>/<device>/BoardConfig.mk \
     --format markdown

2. Classify from the failure mode:

   Build failure:
     scripts/selinux-repair/build_error_triage.py build.log --format markdown
     scripts/selinux-repair/selinux_build_doctor.py build.log \
       --repo . --board-config <path> --format markdown

   Property-context duplicate or serialize errors:
     scripts/selinux-repair/property_context_doctor.py \
       --log build.log --repo . --board-config <path> --format markdown

   Boots but logs runtime denials:
     scripts/selinux-repair/capture_selinux_denials.sh \
       --root --auditctl --events 1500 --throttle 150
     scripts/selinux-repair/summarize_denials.py <captured-log> --format markdown
     Note: --root, --auditctl, and the monkey-event fuzzing this script runs are
     runtime-mutating (not partition-destructive, but not passive reads either).
     They are gated behind explicit flags for this reason. Do not run them without
     the user's explicit go-ahead, the same way any other live-device action
     requires confirmation.

   Only the tree is available (no build log):
     scripts/selinux-repair/audit_device_tree.py <path> --format markdown
     scripts/selinux-repair/context_conflict_finder.py <path> --format markdown

   Artifacts already built:
     scripts/selinux-repair/verify_policy_artifacts.sh out/target/product/<device>

3. Fix only the first real blocker. Parallel Android builds cascade; a single root
   property or type conflict often produces dozens of downstream FAILED: lines.

4. Classify by cause in this order:
   build/verifier failure -> labeling failure -> domain transition failure ->
   partition ownership failure -> missing public API or private-symbol boundary
   failure -> real permission gap -> debug-only access that should not ship in
   production policy.

5. Repair by cause, not symptom. For every issue, determine: which domain is
   acting, which exact object is targeted, which class and permission is requested,
   whether the target label is still generic (needs relabeling before an allow rule),
   which partition should own it, and whether vendor policy is referencing only
   public platform symbols.
   Safe shapes: template/selinux-repair/safe_policy_patterns.md
   Dangerous shapes: template/selinux-repair/dangerous_patterns_to_reject.md

6. Verify before moving on:
   m sepolicy_tests
   m vendor_sepolicy.cil plat_sepolicy.cil || true
   Re-run the path resolver and scripts/selinux-repair/verify_policy_artifacts.sh
   out/target/product/<device>. Then boot, test, and re-capture denials.

### Output contract

Any proposed SELinux fix must include all 8 fields in
template/selinux-repair/patch_output_contract.md:
  1. Failure class
  2. First evidence line
  3. Root cause hypothesis
  4. Files to edit
  5. Patch shape
  6. Why this is safe
  7. Validation commands
  8. What not to do

Never output a raw audit2allow blob as the final answer -- convert it into a
reviewed patch plan using this contract.


## File and Folder Map

```
skills/android-development/
  AGENTS.md              this file -- AI agent router and domain workflows
  README.md              human-readable overview, install instructions, testing
  REFERENCE.md           command reference indexed by domain
  SKILL.md               skills.sh entry point (minimal frontmatter + pointers)
  template/
    rom/                 local_manifest.xml, roomservice.xml, BoardConfig.mk skeleton
    kernel/              defconfig_fragment.md, anykernel_notes.md
    gki-kernel/          build.config.template, BUILD.bazel.template
    debug/               diagnosis_report.md, log_capture_manifest.md
    selinux-repair/      safe_policy_patterns.md, dangerous_patterns_to_reject.md,
                         patch_output_contract.md
  scripts/
    rom/                 build_rom.sh
    kernel/              build_kernel.sh
    gki-kernel/          build_gki_kernel.sh
    debug/               capture_logs.sh, verify_device.sh (read-only ADB helper)
    selinux-repair/      Python and shell tools listed above
                         tests/ -- selftest.sh and sample fixture logs
  references/
    selinux-repair/      deep-dive playbooks (see README.md in that folder for index)
    debug/               (reserved, currently empty)
    gki-kernel/          (reserved, currently empty)
    kernel/              (reserved, currently empty)
    rom/                 (reserved, currently empty)
```


## Evidence Hierarchy for SELinux Repair

Prefer evidence sources in this order:

1. Policy source map from BoardConfig and product makefiles (narrows search before
   any broad repo scan).
2. First deterministic build failure (checkpolicy, secilc, checkfc,
   host_init_verifier, property_info_serializer, sepolicy_tests,
   se_neverallow_test).
3. Generated build intermediates (merged policy.conf, merged property_contexts,
   generated .cil files).
4. Runtime boot denials (dmesg, pstore/ramoops, early logcat -b all).
5. Targeted runtime reproduction denials after triggering the failing feature.
6. Static audit of the resolved device/vendor/product/system_ext policy roots.
7. Existing AOSP/ROM public policy patterns and macros.
8. Broad full-tree search -- only after the policy source map is exhausted.
9. audit2allow output -- a hint only, never a patch to apply blindly.


## Quick Decision Aid

- User mentions repo sync, lunch, breakfast, mka, or "ROM won't compile":
  ROM Build workflow.
- User mentions defconfig, Image.gz-dtb, make ARCH=arm64, or "kernel won't compile"
  (single monolithic kernel repo): Kernel Build (legacy) workflow.
- User mentions build.config, tools/bazel, common/, GKI, KMI/ABI, or vendor_boot:
  GKI Kernel Build workflow.
- User mentions avc: denied, neverallow, sepolicy, property_contexts,
  checkpolicy/checkfc errors, or a SELinux-specific build or runtime failure:
  SELinux Repair workflow (its own tooling and evidence hierarchy, not the general
  build-failure tables).
- User mentions a device that is already flashed and misbehaving (bootloop, crash,
  "doesn't boot", "app keeps crashing", "X isn't working"):
  Debug Workflow -- do not jump to rebuilding until evidence points there.
