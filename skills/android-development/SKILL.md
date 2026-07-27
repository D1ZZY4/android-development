---
name: android-development
description: >-
  Use for ANY custom Android platform engineering work — building a custom
  ROM/AOSP/LineageOS from a device tree, building or porting a kernel
  (including GKI/Generic Kernel Image), debugging a device or ROM build
  (bootloops, crashes, kernel panics, SELinux denials, service deaths, HAL
  issues), or fixing bugs in a device tree, kernel source, or live device
  via ADB. Trigger on: device tree, repo sync/manifest, lunch/breakfast,
  mka/mka bacon, defconfig, Image.gz-dtb, boot.img, AnyKernel3, GKI,
  kernelsu, .rc/.te/.mk/.bp files, adb logcat/dmesg/tombstones, ROM or
  kernel build failures, device bootlooping, avc denied, neverallow,
  sepolicy, property_contexts, checkpolicy/checkfc errors, or any
  connected device with ADB root. Also for build-environment setup,
  BoardConfig.mk/Android.bp fixes, kernel diff review. Read REFERENCE.md
  for exact commands before
  running build/debug commands. Prefer over general coding help whenever
  AOSP, a device tree, or kernel source is involved.
---

# Android Development (ROM / Kernel / Debug)

Covers four related but distinct workflows for custom Android platform work. Identify which one the user is doing first — they need different tools and different guardrails.

| Workflow | When | Go to |
|---|---|---|
| **ROM build** | Building/porting AOSP, LineageOS, or similar from a device tree + manifest | `REFERENCE.md` § ROM Build, `template/rom/`, `scripts/rom/` |
| **Kernel build** | Building a device kernel from source (non-GKI, traditional monolithic kernel) | `REFERENCE.md` § Kernel Build, `template/kernel/`, `scripts/kernel/` |
| **GKI kernel build** | Building a Generic Kernel Image kernel (Android 12+ GKI 1.0/2.0, split kernel/vendor modules) | `REFERENCE.md` § GKI Kernel Build, `template/gki-kernel/`, `scripts/gki-kernel/` |
| **Debug / fix a bug** | Something crashes, bootloops, or misbehaves — on a live device or in logs from a build | § Debug Workflow below, `template/debug/`, `scripts/debug/` |
| **SELinux repair** | SELinux build failures, runtime AVC denials, policy/context conflicts, property-context collisions, neverallow violations | § SELinux Repair Workflow below, `template/selinux-repair/`, `scripts/selinux-repair/`, `references/selinux-repair/` |

If unclear which one applies, ask — a "build" question and a "debug" question need different first commands and the wrong one wastes a full build cycle (ROM/kernel builds can take 30min–several hours). A SELinux build failure specifically (vs. a generic build failure) is a strong signal to go straight to the SELinux Repair Workflow rather than the general ROM/Kernel Build failure tables — it has its own evidence hierarchy and tooling.

## Hard constraints (apply to all four workflows)

1. **Never run destructive/mutating commands on a connected physical device without the user's explicit go-ahead first** — this includes `fastboot flash`, `fastboot erase`, `adb reboot bootloader`, `dd` to any device node, `mkfs`, or anything that writes to a partition. Building an image and writing files inside the *workspace* (device tree / kernel source / out/ directory) is fine and expected. Writing to the *physical device* is not, until the user confirms.
2. **Evidence over guessing.** For debug work especially: never state a root cause you didn't actually see in a log, source file, or command output. See § Debug Workflow.
3. **Don't assume the toolchain/environment is already set up.** Check for `build/envsetup.sh`, `.repo/`, existing `out/` dirs, or a kernel `Makefile` before assuming a repo is initialized. Ask or check rather than guessing paths.
4. **Long-running builds:** repo sync and full ROM/kernel builds can take a long time and produce huge logs. Run them in the background where the environment supports it, and tail/grep the log rather than dumping it all into the response.

## ROM build workflow (brief — full detail in REFERENCE.md)

1. Confirm workspace: is `.repo/` present (already synced) or does this need `repo init` first?
2. Set up manifest (main + local_manifests for device/vendor/kernel trees) — see `template/rom/local_manifest.xml`.
3. `source build/envsetup.sh` → `lunch <target>` (or `breakfast <codename>` for LineageOS).
4. Build with `mka bacon` (LineageOS) or `mka <target>` — background it, monitor for the first error rather than waiting for full completion if something's clearly broken.
5. On build failure: grep the log for the first `error:`/`FAILED:` line, not the last — later errors are often cascades from the first one.

Full command reference, manifest examples, and common build error patterns: `REFERENCE.md` § ROM Build.

## Kernel build workflow (brief)

1. Identify kernel source layout: legacy (`arch/arm64/configs/<defconfig>`, single Makefile) vs GKI (split `common/` kernel + separate vendor modules, uses `build/build.sh` or Bazel `tools/bazel`).
2. If legacy: set `ARCH`, `CROSS_COMPILE`, pick defconfig, `make -jN`.
3. If GKI: this is a different workflow — go to § GKI below, don't apply legacy `make` commands to a GKI tree, they won't produce a working boot image on their own.
4. Package: `Image.gz-dtb` (or `Image`/`Image.lz4`) + ramdisk → `boot.img` via `mkbootimg`/`avbtool`, or AnyKernel3 for a flashable zip.

Full command reference: `REFERENCE.md` § Kernel Build.

## GKI kernel build workflow (brief)

GKI kernels are structurally different — they build a generic `Image` from Google's `common` kernel tree, plus vendor/device-specific modules that load separately. Mixing legacy single-Makefile build habits into a GKI tree is a common source of confusion.

1. Confirm which GKI generation: GKI 1.0 vs GKI 2.0 (module signing, `vendor_boot` vs `boot`, kernelsu/ksu integration if present) — check `BUILD.bazel`/`build.config.*` for hints.
2. Use `build/build.sh` (older) or `tools/bazel build //...` (newer AOSP kernel trees) — don't hand-roll `make` flags for these unless the tree explicitly still supports it.
3. Watch for ABI/symbol issues (`abi_gki_*` files, `KMI` mismatches) — these are GKI-specific failure modes not present in legacy kernels.

Full command reference and KMI/ABI notes: `REFERENCE.md` § GKI Kernel Build.

## Debug workflow (evidence-first — for live device or post-build issues)

This is the strictest part of the skill. Do not skip steps or shortcut to a diagnosis.

### Anti-hallucination rules (non-negotiable)

1. **Zero guesswork.** Every claim in the diagnosis must be backed by a direct quote from a log, device tree/kernel source file, or an adb output actually retrieved in this session.
2. **No generic advice.** Never say "check your manifest" or "make sure permissions are correct" — give the exact file path, exact line/snippet, exact command output.
3. **Self-audit before diagnosing.** Before writing a diagnosis, ask: "Did I actually see this, or am I assuming it based on common issues?" If assumed, don't include it — go get more data.
4. If any part of the final diagnosis can't be backed by hard evidence, don't output a soft/partial diagnosis. Output `INSUFFICIENT DATA. EXECUTING DEEPER EXPLORATION.` and repeat the steps below with different parameters.

### Steps (in order)

1. **Log acquisition** — `scripts/debug/capture_logs.sh` (or run the commands manually, see REFERENCE.md § Debug Commands): `adb logcat -d -b all`, `adb shell dmesg`, tombstones in `/data/tombstones/`. Find the exact error: `FATAL EXCEPTION`, kernel panic, `avc: denied`, service crash, ANR.
2. **Source cross-reference** — locate the failing component in the device tree or kernel source: `.rc` (init), `.te` (SELinux), `.mk`/`.bp` (build), overlay XMLs, or kernel driver source. Use `grep -rn` for the exact name, don't guess the file.
3. **Live verification (read-only only)** — confirm the hypothesis on-device: `adb shell ls -lZ`, `adb shell getprop | grep`, `adb shell dumpsys <service>`, `adb shell ps -A`, `adb shell lshal`, `adb shell cat /sys/...`. Never a mutating command here.
4. **Diagnosis** — only once 1–3 produced real evidence, output:

```
1. Symptom: [exact log line]
2. Root Cause: [explanation grounded in evidence]
3. Evidence from Device: [exact adb output from step 3]
4. Evidence from Source: [exact file path + line/snippet from step 2]
5. Proposed Fix: [specific change — file, line, diff]
```

Full debug command list and read-only verification helper: `REFERENCE.md` § Debug Commands, `scripts/debug/verify_device.sh`.

## SELinux Repair Workflow

A specialized evidence-first workflow for SELinux build failures and runtime AVC denials — sourced from a dedicated policy-repair toolset, folded in here as its own domain. Same evidence discipline as the general Debug Workflow, but with SELinux-specific tooling and an explicit repair-by-cause ordering.

**Operating rule:** collect the first reliable failure, classify it, fix ownership/labeling before permissions, add the smallest policy rule last, verify with build-time and runtime gates. A successful repair is narrow, explainable, partition-correct, and public/private-policy-boundary-compatible — "the build passes" alone is not success.

### Steps (in order)

1. **Resolve the policy source map first** — before broad-searching the tree, find the exact makefile-declared policy roots (`BOARD_VENDOR_SEPOLICY_DIRS`, `SYSTEM_EXT_*_SEPOLICY_DIRS`, `PRODUCT_*_SEPOLICY_DIRS`, `BOARD_ODM_SEPOLICY_DIRS`, inherited `SEPolicy.mk`):
   ```
   scripts/selinux-repair/sepolicy_path_resolver.py --repo . --board-config device/<vendor>/<device>/BoardConfig.mk --format markdown
   ```
2. **Classify from the failure mode:**
   - Build failure → `scripts/selinux-repair/build_error_triage.py build.log --format markdown`, then `scripts/selinux-repair/selinux_build_doctor.py build.log --repo . --board-config <path> --format markdown`.
   - Property-context duplicate/serialize errors → `scripts/selinux-repair/property_context_doctor.py --log build.log --repo . --board-config <path> --format markdown`.
   - Boots but logs denials → `scripts/selinux-repair/capture_selinux_denials.sh --root --auditctl --events 1500 --throttle 150`, then `scripts/selinux-repair/summarize_denials.py <captured-log> --format markdown`. Note: `--root`/`--auditctl` and the monkey-event fuzzing this script runs are runtime-mutating (not destructive to partitions/data, but not passive reads either) — they're gated behind explicit flags for a reason; don't run them without the user's go-ahead the same way any other live-device action needs confirmation.
   - Only the tree is available (no build log) → `scripts/selinux-repair/audit_device_tree.py <path> --format markdown` and `scripts/selinux-repair/context_conflict_finder.py <path> --format markdown`.
   - Artifacts already built → `scripts/selinux-repair/verify_policy_artifacts.sh out/target/product/<device>`.
3. **Fix only the first real blocker** — parallel Android builds cascade; a single root property/type conflict often produces dozens of downstream `FAILED:` lines.
4. **Classify by cause, in this order:** build/verifier failure → labeling failure → domain transition failure → partition ownership failure → missing public API/private-symbol boundary failure → real permission gap → debug-only access that shouldn't ship in production policy.
5. **Repair by cause, not symptom.** For every issue, work out: which domain is acting, which exact object is targeted, which class/permission is requested, whether the target label is still generic (needs relabeling before an allow rule), which partition should own it, and whether vendor policy is referencing only public platform symbols. Safe/dangerous policy shapes: `template/selinux-repair/safe_policy_patterns.md`, `template/selinux-repair/dangerous_patterns_to_reject.md`.
6. **Verify before moving on:** `m sepolicy_tests`, `m vendor_sepolicy.cil plat_sepolicy.cil || true`, then re-run the path resolver and `scripts/selinux-repair/verify_policy_artifacts.sh out/target/product/<device>`. Then boot/test and re-capture denials.

### Output contract

Any proposed SELinux fix must include: failure class, first evidence line, root cause hypothesis, exact files to edit, patch shape, why it's safe (label-first/least-privilege/partition-correct reasoning), exact validation commands, and what NOT to do. Never hand back a raw `audit2allow` blob as the final answer — convert it into a reviewed patch plan. Full template: `template/selinux-repair/patch_output_contract.md`.

### Deeper reference

Start with `references/selinux-repair/policy-source-map.md` and `references/selinux-repair/source-map-command-cookbook.md` for a device-tree build error; `references/selinux-repair/denial-decision-tree.md` for runtime AVC triage; `references/selinux-repair/common-fixes.md` for safe shapes/anti-patterns; `references/selinux-repair/README.md` indexes the rest.

## Scripts and templates

`scripts/` and `template/` are both organized per-domain — same five subfolder names (`rom/`, `kernel/`, `gki-kernel/`, `debug/`, `selinux-repair/`) in each, so the tooling and the fill-in-the-blank material for a given workflow live side by side.

- `scripts/rom/build_rom.sh` — wrapper template for `repo sync` + `lunch`/`breakfast` + `mka`, backgroundable, logs to file.
- `scripts/kernel/build_kernel.sh` — wrapper template for legacy kernel `make` builds.
- `scripts/gki-kernel/build_gki_kernel.sh` — wrapper template for `build/build.sh` / Bazel GKI builds.
- `scripts/debug/capture_logs.sh` — pulls logcat (all buffers) + dmesg + tombstone listing into timestamped files for review.
- `scripts/debug/verify_device.sh` — read-only live-verification helper (getprop/dumpsys/lshal/ls -lZ wrappers).
- `scripts/selinux-repair/` — policy source-map resolver, build-error triage, property-context doctor, denial capture/summarizer, device-tree auditor, context-conflict finder, artifact verifier (`.py`/`.sh`), plus a `tests/` subfolder with sample logs and a `selftest.sh` to sanity-check the tools themselves.
- `template/rom/` — `local_manifest.xml`, `roomservice.xml`, skeleton `BoardConfig.mk`/`Android.bp` fragments.
- `template/kernel/` — defconfig fragment notes, `Makefile` fragment, AnyKernel3 `anykernel.sh` skeleton.
- `template/gki-kernel/` — `build.config` template, Bazel `BUILD.bazel` module skeleton.
- `template/debug/` — log-capture output format template, diagnosis report template matching the § Debug Workflow format.
- `template/selinux-repair/` — safe policy pattern shapes, dangerous-pattern rejection list, patch output contract template.
- `references/selinux-repair/` — deep-dive playbooks (policy source map, build-error playbook, property-context collisions, denial decision tree, common fixes, policy review gates) plus AOSP background docs. Not loaded by default — follow the pointers from § SELinux Repair Workflow or `references/selinux-repair/README.md`.

Always check `REFERENCE.md` for exact flags/paths before running a build or debug command — this skill exists specifically to avoid remembered-but-wrong AOSP/kernel command syntax.
