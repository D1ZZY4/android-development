# Building GKI with KernelSU-Next

How to set up a GKI kernel workspace, integrate KernelSU-Next (KSU-Next) using
the official setup script, and build with full LTO. This covers the build.sh-era
GKI flow (android12-5.10, android13-5.10). For Kleaf/Bazel trees see
REFERENCE.md section GKI Kernel Build.

---

## What KernelSU-Next is

KernelSU-Next (github.com/KernelSU-Next/KernelSU-Next) is a community fork of
KernelSU that tracks the upstream dev branch more closely and adds support for
additional GKI branches. It integrates into the kernel source tree by cloning
the KSU-Next source, creating a `kernelsu` symlink inside `drivers/`, and
patching `drivers/Makefile` and `drivers/Kconfig` to include the module.

The `setup.sh` approach applies these changes without requiring a manual git
merge, which is the recommended method for CI-style builds.

---

## Workspace setup (build.sh-era trees)

```bash
mkdir -p android-kernel
cd android-kernel

# Init the kernel manifest -- adjust the branch for the target device
# Common branches:
#   common-android12-5.10   (Android 12, kernel 5.10)
#   common-android13-5.10   (Android 13, kernel 5.10 LTS)
#   common-android13-5.15   (Android 13, kernel 5.15)
#   common-android14-5.15   (Android 14, kernel 5.15)
repo init \
  -u https://android.googlesource.com/kernel/manifest \
  -b common-android12-5.10 \
  --depth=1

repo sync -c --no-tags --no-clone-bundle --optimized-fetch -j"$(nproc)"
```

`--depth=1` and `--optimized-fetch` keep the checkout shallow and fast. Do not
use these on a tree where you need full git history (e.g. for cherry-picks from
older commits).

---

## KernelSU-Next integration

Run the official setup script from inside the workspace root (the directory
containing `build/`, `common/`, etc. -- not inside `common/` itself):

```bash
curl -LSs \
  "https://raw.githubusercontent.com/KernelSU-Next/KernelSU-Next/refs/heads/dev/kernel/setup.sh" \
  | bash -
```

The script:
1. Clones or updates the `KernelSU-Next` source into the workspace root.
2. Creates a `kernelsu` symlink inside `drivers/` (resolves to `common/drivers/`
   on build.sh-era trees) pointing to the KSU-Next kernel source.
3. Patches `drivers/Makefile` and `drivers/Kconfig` to include the KSU module.

After the script completes, commit the changes so the build system picks them up:

```bash
cd common
git status --short    # verify only KSU-related files are modified/added
git add -A
git commit -m "kernel: add KernelSU-Next"
cd ..
```

Committing is important: some GKI build scripts compute a `LOCALVERSION` or
kernel version string from `git describe`. An un-committed dirty tree can produce
a version mismatch that breaks module loading later.

---

## Build

```bash
LTO=full \
BUILD_CONFIG=common/build.config.gki.aarch64 \
./build/build.sh
```

Or use the helper script:

```bash
bash scripts/gki-kernel/build_gki_ksun.sh \
  common-android12-5.10 \
  common/build.config.gki.aarch64
```

### LTO options

| Value | Meaning | Use when |
|---|---|---|
| `full` | Full link-time optimisation -- one single IR pass across all compilation units | Production/release builds; produces smaller, faster code but takes significantly longer to link |
| `thin` | ThinLTO -- faster, parallelised LTO approximation | Development iterations where build time matters more than peak optimisation |
| (unset) | No LTO | Fastest build; do not ship |

`LTO=full` is required for shipping a GKI-compliant kernel to end users. Use
`LTO=thin` locally while iterating on the KSU integration, then switch to `full`
for the release build.

### Output

Output lands in `out/<branch>/dist/`:

| File | Description |
|---|---|
| `Image` | Uncompressed kernel image |
| `Image.lz4` | LZ4-compressed kernel image (common on arm64 GKI devices) |
| `System.map` | Kernel symbol map (for crash analysis) |
| `vmlinux` | Unstripped kernel ELF (for debugging) |
| `*.ko` | Vendor kernel modules (if the tree builds them) |

---

## Branch compatibility

| Manifest branch | Android version | build.sh | Bazel/Kleaf | KSU-Next support |
|---|---|---|---|---|
| `common-android12-5.10` | Android 12 | Yes | No | Yes |
| `common-android13-5.10` | Android 13 (LTS) | Yes | Partial | Yes |
| `common-android13-5.15` | Android 13 | Yes | Yes | Yes |
| `common-android14-5.15` | Android 14 | Partial | Yes | Yes |
| `common-android14-6.1` | Android 14 | No | Yes | Check upstream |

For Bazel/Kleaf trees, KSU-Next integration requires applying patches manually
and registering the KSU module in the relevant `BUILD.bazel`. The setup.sh script
targets build.sh-era trees; check the KSU-Next repository for Kleaf-specific
instructions.

---

## Common issues after integration

| Symptom | Likely cause | Check |
|---|---|---|
| Module not loading: "version magic mismatch" | Dirty tree when building -- KSU files not committed before build | Commit the KSU changes in `common/` before running build.sh |
| `undefined reference to 'ksu_*'` at module link | KSU-Next not integrated or symlink broken | Re-run setup.sh from the workspace root; verify `common/drivers/kernelsu` symlink exists and points to the cloned KernelSU-Next source |
| AVB verification failure on first boot | Verified boot enabled and the patched kernel is unsigned | Disable verified boot (`fastboot flashing unlock`) before testing, or sign with the device's test key |
| KSU app shows "Unsupported" | Running on a non-GKI device or the kernel was built without the KSU module entry | Confirm the device boots a GKI kernel; check `uname -r` for `-android` suffix |
| `avc: denied` for `ksu` domain | SELinux policy missing `ksu.te` or it was not included in the build | SELinux Repair domain: run `sepolicy_path_resolver.py` to find policy roots, add KSU policy |
