# GKI Kernel Build -- Reference

Detailed commands for GKI kernel builds.

GKI (Generic Kernel Image) splits the kernel into a generic core (`Image`)
built by Google's `common` tree, and vendor modules built separately and
loaded at runtime. This means:

- You usually do **not** hand-edit `arch/arm64/configs/*_defconfig` and run
  bare `make` -- the build is driven by `build.config.*` files and either
  `build/build.sh` (GKI kernels up to ~5.10/5.15 era) or Bazel
  (`tools/bazel`, newer trees, "Kleaf" build system).

## build.sh-based GKI build

```bash
BUILD_CONFIG=common/build.config.gki.aarch64 build/build.sh
```

Output lands in `out/<branch>/dist/` -- look for `Image`, `Image.lz4`,
`System.map`, `vmlinux`, and vendor `.ko` modules separately.

## Bazel/Kleaf-based GKI build (newer AOSP kernel trees)

```bash
tools/bazel run //common:kernel_aarch64_dist
tools/bazel run //common:kernel_aarch64_dist -- --dist_dir=out/dist
```

Target names vary per tree -- check `common/BUILD.bazel` for the actual target
rather than assuming `kernel_aarch64` is universal.

## GKI-specific failure modes

| Symptom | Meaning |
|---|---|
| `ABI DIFF` / KMI mismatch errors | A change touched a symbol tracked by `abi_gki_*.xml`/`.stg` files -- either update the ABI definition (if intentional) or the change broke module compatibility |
| Vendor module fails to load ("invalid module format") | Vendor `.ko` built against different KMI version than boot kernel -- version/branch mismatch between `common` and vendor kernel trees |
| `vendor_boot` vs `boot` partition confusion | GKI 2.0 devices split ramdisk into `vendor_boot` (vendor init/DTB/ramdisk) and `boot` (generic kernel) -- flashing/packaging logic differs |
| KernelSU / Magisk-patched GKI boot fails signature check | AVB verification on `boot`/`vendor_boot` -- check verified boot state before assuming the patch itself is broken |

## KernelSU-Next integration (build.sh-era trees)

```bash
# 1. Set up workspace
mkdir -p android-kernel && cd android-kernel
repo init -u https://android.googlesource.com/kernel/manifest \
  -b common-android12-5.10 --depth=1
repo sync -c --no-tags --no-clone-bundle --optimized-fetch -j"$(nproc)"

# 2. Apply KernelSU-Next patches
curl -LSs "https://raw.githubusercontent.com/KernelSU-Next/KernelSU-Next/refs/heads/dev/kernel/setup.sh" | bash -

# 3. Commit the changes (required -- build computes version from git describe)
cd common && git add -A && git commit -m "kernel: add KernelSU-Next" && cd ..

# 4. Build with full LTO
LTO=full BUILD_CONFIG=common/build.config.gki.aarch64 ./build/build.sh
```

Or use the helper script:

```bash
bash scripts/gki-kernel/build_gki_ksun.sh \
  common-android12-5.10 \
  common/build.config.gki.aarch64 \
  full
```

LTO values: `full` (production, slower link), `thin` (faster iterations),
omit for no LTO.
Deep-dive: `references/gki-kernel/kernelsu-next-build.md`.

## Quick reference

- **build.sh trees**: android12-5.10, android13-5.10, android13-5.15
- **Bazel/Kleaf trees**: android13-5.15+, android14-5.15, android14-6.1
- **KSU-Next supported**: all build.sh branches; Kleaf branches need manual
  patch application
