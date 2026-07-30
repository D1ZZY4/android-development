
# Kernel Build (Legacy) -- AI Agent Entry Point

Build legacy/monolithic device kernels (non-GKI) from a single kernel tree with defconfig and make.

Activate on: defconfig, Image.gz-dtb, make ARCH=arm64, kernel won't compile, monolithic kernel tree, arch/arm64/configs/, mkbootimg, AnyKernel3 packaging for non-GKI devices.

Read REFERENCE.md for exact command flags before running any build command. For GKI (split common/vendor module) kernels, use the gki-kernel skill instead.

## Hard Constraints

1. Never run destructive or mutating commands on a connected physical device without the user's explicit confirmation. This includes: fastboot flash, fastboot erase, dd to any device node, or anything that writes to a partition. Building an image in the workspace is fine.

2. Evidence over guessing. Never state a root cause you did not actually see in a log, source file, or command output.

3. Do not assume the toolchain is already set up. Check for existing cross-compiler paths and kernel Makefile before assuming paths.

4. Long-running builds: background the build and tail/grep the log.

## Kernel Build Workflow (legacy / non-GKI)

Full command detail and common failure patterns: REFERENCE.md. Templates: template/ (defconfig_fragment.md, anykernel_notes.md) Script: scripts/build_kernel.sh

1. Identify kernel source layout: legacy (arch/arm64/configs/<defconfig>, single Makefile) vs GKI (split common/ kernel + separate vendor modules, build.config.* or BUILD.bazel).
2. If legacy: set ARCH, CROSS_COMPILE, pick defconfig, make -jN.
3. If GKI: go to the gki-kernel skill. Do not apply legacy bare-make commands to a GKI tree; they will not produce a working boot image on their own.
4. Package: Image.gz-dtb (or Image / Image.lz4) + ramdisk into boot.img via mkbootimg/avbtool, or use AnyKernel3 for a flashable zip. See template/anykernel_notes.md.

## File and Folder Map

```
skills/kernel/
  AGENTS.md   AI agent router and workflow
  README.md   human-readable overview
  REFERENCE.md command reference
  SKILL.md    skills.sh entry point
  template/   defconfig_fragment.md, anykernel_notes.md
  scripts/    build_kernel.sh
  references/ reserved for future guides
```

## Quick Decision Aid

- User mentions defconfig, Image.gz-dtb, make ARCH=arm64, or "kernel won't compile" (single monolithic kernel repo): Kernel Build (legacy) workflow.
- User mentions build.config, tools/bazel, common/, GKI, KMI/ABI, vendor_boot: see gki-kernel skill.
- User mentions module.prop, anykernel.sh, or a flashable kernel ZIP: see module skill.
