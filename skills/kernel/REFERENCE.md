# Kernel Build (legacy) -- Reference

Detailed commands for non-GKI kernel builds.

## Environment

```bash
export ARCH=arm64
export SUBARCH=arm64
export CROSS_COMPILE=aarch64-linux-android-   # or aarch64-linux-gnu- depending on toolchain
export CC=clang                                # most modern device kernels use clang now
export CLANG_TRIPLE=aarch64-linux-gnu-
```

Toolchain source matters -- check the kernel tree's own build script
(`build.sh`, `Makefile`, or a vendor `build_kernel.sh`) for the exact
toolchain version/path expected before assuming AOSP prebuilts.

## Config and build

```bash
make O=out ARCH=arm64 <defconfig_name>     # e.g. lineageos_<codename>_defconfig
make O=out ARCH=arm64 -j$(nproc --all)
```

Output: `out/arch/arm64/boot/Image.gz-dtb` (or `Image`, `Image.lz4`,
`Image-dtb` depending on device) plus `out/arch/arm64/boot/dts/**/*.dtb` if
DTBs aren't already appended.

## Packaging into a boot image

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

Or use **AnyKernel3** for a flashable zip that doesn't require rebuilding a
full boot.img manually -- see `template/kernel/anykernel_notes.md`.

## Common kernel build failure patterns

| Symptom | Likely cause |
|---|---|
| `error: implicit declaration of function` | Kernel version mismatch with a backported driver/header; check `include/linux/` for the missing prototype |
| `Kbuild:xx: recipe for target ... failed` | Usually a real compile error just above -- scroll up |
| DTB not appended / device doesn't boot but kernel "built successfully" | `BoardConfig.mk` `BOARD_KERNEL_IMAGE_NAME` or DTB concat step mismatch -- kernel binary compiling cleanly doesn't mean it was packaged correctly |
| SELinux-related boot failure after custom kernel | Kernel `.config` disabled `CONFIG_SECURITY_SELINUX` or a related option the ROM's userspace expects | Diff `.config` against a known-working one for the device |
