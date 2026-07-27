# Android Development -- Reference

Detailed commands and patterns for each workflow. Read the relevant section only -- do not load this whole file into a response.

---

## ROM Build

### Workspace setup

```bash
# One-time repo tool + git identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Init a manifest (LineageOS example, adjust branch per target Android version)
repo init -u https://github.com/LineageOS/android.git -b lineage-21.0 --git-lfs

# Local manifests for device/vendor/kernel trees not in the main manifest
mkdir -p .repo/local_manifests
# put local_manifest.xml here — see template/rom/local_manifest.xml

repo sync -c -j$(nproc --all) --force-sync --no-clone-bundle --no-tags
```

- `-c` = current branch only (faster, smaller).
- `-j$(nproc --all)` = parallel jobs, but on constrained bandwidth/RAM drop this to a fixed number (e.g. `-j4`) to avoid OOM or throttling.
- If sync fails mid-way with "path already exists" or similar, don't `rm -rf` blindly — check whether it's a stale lock (`.repo/.repo_fetchtimes.json`, `*.lock` files) first.

### Building

```bash
source build/envsetup.sh

# LineageOS shorthand for device setup + lunch
breakfast <device_codename>

# Or explicit lunch (AOSP-style)
lunch lineage_<device_codename>-userdebug

# Full build
mka bacon          # LineageOS: builds + packages OTA zip
# or
mka <target>        # AOSP: e.g. `mka droid`
```

Background it and tail:

```bash
nohup mka bacon > /tmp/rom_build.log 2>&1 &
tail -f /tmp/rom_build.log
```

### Reading build failures

Find the **first** error, not the last — a single early failure (missing file, unresolved dependency, bad Makefile syntax) commonly cascades into dozens of downstream `FAILED:` lines that are just noise from the first one.

```bash
grep -n -m1 -E "error:|FAILED:|\*\*\* " /tmp/rom_build.log
```

Common ROM build failure patterns:

| Symptom in log | Likely cause | Where to look |
|---|---|---|
| `fatal error: <file>.h: No such file or directory` | Missing dependency repo or wrong manifest branch | `.repo/local_manifests/*.xml`, does the referenced path actually exist under the tree? |
| `Cannot find package '...' for module '...'` (Soong/Android.bp) | `Android.bp` module name typo or missing `PRODUCT_PACKAGES` entry | `device/<vendor>/<codename>/Android.mk` or `.bp`, `device.mk` |
| `undefined reference to '...'` at link time | Missing `LOCAL_SHARED_LIBRARIES`/`LOCAL_STATIC_LIBRARIES` or ABI mismatch | The failing module's `Android.mk`/`.bp` |
| `ninja: build stopped: subcommand failed` with no further detail above | Real error is earlier in the log, ninja just reports the aggregate failure | scroll/grep further up, don't diagnose from this line alone |
| Signing/verity errors during `mka bacon` packaging step | Missing or mismatched keys in `vendor/lineage-priv` (test-keys) | Check `signing` step config, not the OS build itself |

### Device tree skeleton reference

A minimal device tree has, at minimum:
- `AndroidProducts.mk` — registers the product makefile
- `<codename>.mk` / `device_<vendor>_<codename>.mk` — product definition, packages, overlays
- `BoardConfig.mk` — partition layout, kernel config pointer, architecture flags
- `device.mk` — inherited product config
- `overlay/` — resource overlays (`frameworks/base/core/res/res/values/*.xml` style paths)

See `template/rom/` for skeleton fragments of `BoardConfig.mk` and a minimal `Android.bp`.

---

## Kernel Build (legacy / non-GKI)

### Environment

```bash
export ARCH=arm64
export SUBARCH=arm64
export CROSS_COMPILE=aarch64-linux-android-   # or aarch64-linux-gnu- depending on toolchain
export CC=clang                                # most modern device kernels use clang now
export CLANG_TRIPLE=aarch64-linux-gnu-
```

Toolchain source matters — check the kernel tree's own build script (`build.sh`, `Makefile`, or a vendor `build_kernel.sh`) for the exact toolchain version/path expected before assuming AOSP prebuilts.

### Config and build

```bash
make O=out ARCH=arm64 <defconfig_name>     # e.g. lineageos_<codename>_defconfig
make O=out ARCH=arm64 -j$(nproc --all)
```

Output: `out/arch/arm64/boot/Image.gz-dtb` (or `Image`, `Image.lz4`, `Image-dtb` depending on device) plus `out/arch/arm64/boot/dts/**/*.dtb` if DTBs aren't already appended.

### Packaging into a boot image

```bash
mkbootimg \
  --kernel out/arch/arm64/boot/Image.gz-dtb \
  --ramdisk ramdisk.img \
  --cmdline "$(cat cmdline.txt)" \
  --base 0x00000000 --pagesize 2048 \
  --output boot.img

# AVB signing if the device requires it
avbtool add_hash_footer --image boot.img --partition_size <size> --partition_name boot
```

Or use **AnyKernel3** for a flashable zip that doesn't require rebuilding a full boot.img manually — see `template/kernel/anykernel_notes.md`.

### Common kernel build failure patterns

| Symptom | Likely cause |
|---|---|
| `error: implicit declaration of function` | Kernel version mismatch with a backported driver/header; check `include/linux/` for the missing prototype |
| `Kbuild:xx: recipe for target ... failed` | Usually a real compile error just above — scroll up |
| DTB not appended / device doesn't boot but kernel "built successfully" | `BoardConfig.mk` `BOARD_KERNEL_IMAGE_NAME` or DTB concat step mismatch — the kernel binary compiling cleanly doesn't mean it was packaged correctly |
| SELinux-related boot failure after custom kernel | Kernel `.config` disabled `CONFIG_SECURITY_SELINUX` or a related option the ROM's userspace expects | Diff `.config` against a known-working one for the device |

---

## GKI Kernel Build

GKI (Generic Kernel Image) splits the kernel into a generic core (`Image`) built by Google's `common` tree, and vendor modules built separately and loaded at runtime. This means:

- You usually do **not** hand-edit `arch/arm64/configs/*_defconfig` and run bare `make` — the build is driven by `build.config.*` files and either `build/build.sh` (GKI kernels up to ~5.10/5.15 era) or Bazel (`tools/bazel`, newer trees, "Kleaf" build system).

### build.sh-based GKI build

```bash
BUILD_CONFIG=common/build.config.gki.aarch64 build/build.sh
```

Output lands in `out/<branch>/dist/` — look for `Image`, `Image.lz4`, `System.map`, `vmlinux`, and vendor `.ko` modules separately.

### Bazel/Kleaf-based GKI build (newer AOSP kernel trees, e.g. android13-5.15+ using Kleaf)

```bash
tools/bazel build //common:kernel_aarch64_dist
tools/bazel run //common:kernel_aarch64_dist -- --dist_dir=out/dist
```

Target names vary per tree — check `common/BUILD.bazel` for the actual target rather than assuming `kernel_aarch64` is universal.

### GKI-specific failure modes

| Symptom | Meaning |
|---|---|
| `ABI DIFF` / KMI (Kernel Module Interface) mismatch errors | A change touched a symbol tracked by `abi_gki_*.xml`/`.stg` files — either update the ABI definition (if intentional) or the change broke module compatibility |
| Vendor module fails to load (`insmod`/`modprobe` error, "invalid module format") | Vendor `.ko` built against a different KMI version than the boot kernel — version/branch mismatch between `common` and vendor kernel trees |
| `vendor_boot` vs `boot` partition confusion | GKI 2.0 devices split ramdisk into `vendor_boot` (vendor init/DTB/ramdisk) and `boot` (generic kernel) — flashing/packaging logic differs from legacy single `boot.img` devices |
| KernelSU / Magisk-patched GKI boot fails signature check | AVB verification on `boot`/`vendor_boot` — check whether verified boot is disabled (`fastboot flashing unlock` state) before assuming the patch itself is broken |

See `template/gki-kernel/` for a `build.config` template and a minimal Bazel module skeleton.

### KernelSU-Next integration (build.sh-era trees)

KernelSU-Next integrates into a GKI tree via an official setup script that patches
`common/fs/`, `drivers/input/`, and related subsystems automatically.

```bash
# 1. Set up the workspace (example branch: android12-5.10)
mkdir -p android-kernel && cd android-kernel
repo init \
  -u https://android.googlesource.com/kernel/manifest \
  -b common-android12-5.10 \
  --depth=1
repo sync -c --no-tags --no-clone-bundle --optimized-fetch -j"$(nproc)"

# 2. Apply KernelSU-Next patches
curl -LSs \
  "https://raw.githubusercontent.com/KernelSU-Next/KernelSU-Next/refs/heads/dev/kernel/setup.sh" \
  | bash -

# 3. Commit the changes (required -- build computes version from git describe)
cd common
git add -A
git commit -m "kernel: add KernelSU-Next"
cd ..

# 4. Build with full LTO
LTO=full BUILD_CONFIG=common/build.config.gki.aarch64 ./build/build.sh
```

Or use the helper script (handles repo sync, KSU-Next setup, and build in one run):

```bash
bash scripts/gki-kernel/build_gki_ksun.sh \
  common-android12-5.10 \
  common/build.config.gki.aarch64 \
  full
```

LTO values: `full` (production, slower link), `thin` (faster iterations), omit for no LTO.
Deep-dive: `references/gki-kernel/kernelsu-next-build.md` (branch compatibility table,
common post-integration failures, Kleaf notes).

---

## SELinux Repair

Full workflow lives in `AGENTS.md` under **SELinux Repair Workflow**. This section
is just the tool and command index.

### Tools (`scripts/selinux-repair/`)

| Script | Purpose |
|---|---|
| `sepolicy_path_resolver.py` | Resolve makefile-declared policy roots (BOARD_*/PRODUCT_*/SYSTEM_EXT_* SEPOLICY_DIRS) before broad search |
| `build_error_triage.py` | First-failure classifier from a build log |
| `selinux_build_doctor.py` | Build-log + repo-aware repair plan generator |
| `property_context_doctor.py` | Diagnoses `property_contexts` duplicate/serialize failures |
| `context_conflict_finder.py` | Focused duplicate/overlap scanner for context files |
| `audit_device_tree.py` | Static device-tree policy audit (no build log needed) |
| `capture_selinux_denials.sh` | Captures runtime AVC denials from a connected device (logcat/dmesg/pstore + optional monkey fuzzing) |
| `summarize_denials.py` | Groups/prioritizes captured runtime denials |
| `verify_policy_artifacts.sh` | Runs `sepolicy-analyze`/`checkfc` against already-built policy artifacts |

Sample logs and a `selftest.sh` to sanity-check these tools live in `scripts/selinux-repair/tests/`.

### Evidence hierarchy (prefer in this order)

1. Policy source map from BoardConfig/product makefiles — narrows the search space before any broad repo scan.
2. First deterministic build failure (`checkpolicy`, `secilc`, `checkfc`, `host_init_verifier`, `property_info_serializer`, `sepolicy_tests`, `se_neverallow_test`).
3. Generated build intermediates (merged `policy.conf`, merged `property_contexts`, generated `.cil`).
4. Runtime boot denials (`dmesg`, pstore/ramoops, early `logcat -b all`).
5. Targeted runtime reproduction denials after triggering the failing feature.
6. Static audit of the resolved device/vendor/product/system_ext policy roots.
7. Existing AOSP/ROM public policy patterns and macros.
8. Broad full-tree search — only after the policy source map is exhausted.
9. `audit2allow` output — a hint only, never a patch to apply blindly.

### Common failure signatures

| Log contains | Likely cause | First tool to run |
|---|---|---|
| `neverallow` violation | New rule collides with a platform neverallow assertion | `build_error_triage.py`, then check the violated rule's public policy source |
| `unknown type`/`unknown attribute`/failed `typeattributeset` | Referenced type not declared or not visible from this policy root | `sepolicy_path_resolver.py` first — often a missing include, not a missing declaration |
| `duplicate declaration` / duplicate type or property prefix | Same type/property declared in two inherited policy roots | `context_conflict_finder.py` |
| `Unable to serialize property contexts` / `Duplicate prefix match` / `Duplicate exact match` | Property-context trie conflict | `property_context_doctor.py` |
| `checkfc` invalid context error | Context file references an undeclared/mistyped type | `context_conflict_finder.py`, cross-check `checkpolicy` output |
| `host_init_verifier` error | `.rc` file references a service/property/ctl label the policy doesn't grant | Locate the `.rc` line, then `sepolicy_path_resolver.py` to find where the label should be declared |
| Repeated `FAILED: .../etc/init/*.rc` after a duplicate property message | Cascading symptom — fix the root property_contexts conflict first, ignore the rest until then | — |
| Runtime `avc: denied` with a generic `tcontext` (`sysfs`, `proc`, `default_prop`, `unlabeled`, etc.) | Object needs its own label before an allow rule is even considered | `summarize_denials.py`, then `template/selinux-repair/dangerous_patterns_to_reject.md` for what NOT to do |

Deep-dive playbooks: `references/selinux-repair/` (start with `README.md`, `policy-source-map.md`, `build-error-playbook.md`, `denial-decision-tree.md`, `common-fixes.md`).

---

## Debug Commands (evidence-gathering reference)

Use `scripts/debug/capture_logs.sh` to run all of these at once and save to files, or run individually:

```bash
# Full logcat, all buffers, dump-and-exit (not streaming)
adb logcat -d -b all > logcat_all.txt

# Specific buffers if `all` is too noisy
adb logcat -d -b radio > logcat_radio.txt
adb logcat -d -b events > logcat_events.txt
adb logcat -d -b crash > logcat_crash.txt

# Kernel log
adb shell dmesg > dmesg.txt

# Tombstones (native crashes)
adb shell ls -l /data/tombstones/
adb shell cat /data/tombstones/<file>   # requires root; read-only, fine
```

### Read-only live verification commands

```bash
adb shell ls -lZ /path/to/file            # SELinux context + perms
adb shell getprop | grep <prop_name>       # system properties
adb shell dumpsys <service>                 # service state (e.g. dumpsys activity, dumpsys package)
adb shell ps -A                             # process/service liveness
adb shell lshal                             # HAL listing
adb shell cat /sys/...                      # sysfs nodes (kernel-exposed state)
adb shell getenforce                        # SELinux mode (Enforcing/Permissive)
```

**Never** run from a debug session unless the user explicitly asks and confirms: `fastboot flash*`, `adb reboot bootloader`/`recovery` (unless just to observe, and even then confirm first), `adb shell setprop` (mutates runtime state), `rm`, `dd`, or anything under `/data` or partitions that isn't a read.

### Grep patterns for common failure classes

```bash
# FATAL EXCEPTION (Java/Kotlin crash)
grep -n "FATAL EXCEPTION" logcat_all.txt

# Kernel panic
grep -n -i "panic\|Kernel panic" dmesg.txt

# SELinux denial
grep -n "avc:.*denied" logcat_all.txt dmesg.txt

# Native crash signal
grep -n "Fatal signal" logcat_all.txt

# ANR
grep -n "ANR in" logcat_all.txt
```

---

## Port ROM

Workflow and file reference for porting an existing Android ROM or adapting stock
firmware (e.g. Transsion/XOS) to a custom ROM base. Deep-dive playbooks live in
`references/port-rom/` (start with `README.md`). Templates are in `template/port-rom/`.

### Verify required images before starting

```bash
# Check standard images
bash scripts/port-rom/check_port_images.sh <firmware_dir>

# Also check Transsion-specific extra partitions (tr_product, tr_region)
bash scripts/port-rom/check_port_images.sh <firmware_dir> --transsion
```

### Mount a partition image (read-only inspection)

```bash
# ext4
mkdir -p /tmp/mnt_part
sudo mount -o ro,loop <image>.img /tmp/mnt_part

# erofs (Android 12+, requires erofsfuse or kernel erofs support)
erofsfuse <image>.img /tmp/mnt_part

# Unmount when done
sudo umount /tmp/mnt_part   # ext4
fusermount -u /tmp/mnt_part # erofs
```

### Common OEM removal steps (Transsion/XOS)

Remove framework JARs that exist only in the OEM build:

```bash
# Identify OEM-only JARs declared in permissions but absent from the custom ROM
diff <(grep -r "library name=" system_ext/etc/permissions/ | grep -o '"[^"]*\.jar"') \
     <(ls system_ext/framework/*.jar | xargs -n1 basename | sed 's/^/"/;s/$/"/')
```

Comment out OEM init services that reference absent binaries:

```bash
grep -n "vfy_boot\|<oem_binary>" system/system/etc/init/hw/init.rc
# Then edit the file -- comment out the service block, do not delete
```

Remove OEM-only property context entries that break `property_info_serializer`:

```bash
grep -n "ro.vendor.trancare\|<oem_prop>" vendor/etc/selinux/vendor_property_contexts
# Remove the matching line(s) from the file
```

### Key files for a port

| File | Purpose |
|---|---|
| `template/port-rom/port_checklist.md` | Porting checklist template (fill in per device) |
| `template/port-rom/props_fragment.md` | Build.prop additions template with per-prop notes |
| `references/port-rom/partition-strategy.md` | Image extraction strategy, extra partitions, vendor 64-bit conversion |
| `references/port-rom/transsion-xos-boot-fixes.md` | XOS 16 specific boot blockers and prop fixes |

---

## Quick decision aid

- User mentions `repo sync`, `lunch`, `breakfast`, `mka`, "won't compile the ROM" → **ROM Build**
- User mentions `defconfig`, `Image.gz-dtb`, `make ARCH=arm64`, "kernel won't compile" (and tree looks like a single monolithic kernel repo) → **Kernel Build (legacy)**
- User mentions `build.config`, `tools/bazel`, `common/`, GKI, KMI/ABI, `vendor_boot` → **GKI Kernel Build**
- User mentions `avc: denied`, `neverallow`, `sepolicy`, `property_contexts`, `checkpolicy`/`checkfc` errors, or a SELinux-specific build/runtime failure → **SELinux Repair** (its own tooling/evidence hierarchy, not the general build-failure tables above)
- User mentions a device that's already flashed/running and misbehaving (bootloop, crash, "doesn't boot", "app keeps crashing", "X isn't working") → **Debug Workflow**, don't jump to rebuilding anything until evidence points there
- User mentions porting a ROM, extracting images from stock firmware, tr_product/tr_region, XOS/Transsion port, or vendor 64-bit conversion → **Port ROM**
