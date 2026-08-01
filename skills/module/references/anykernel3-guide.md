
# AnyKernel3 Flashable Kernel ZIP Guide

AnyKernel3 packages a kernel image and optional ramdisk modifications into an installable ZIP. Use it for legacy boot images or GKI layouts where the target is `vendor_boot`.

## Safety boundary

An AnyKernel3 ZIP writes a boot-related partition when an operator installs it. Building, inspecting, and validating the ZIP in the workspace is safe; installing it on a physical device requires the operator's explicit confirmation. Do not present a completed ZIP as authorization to install it.

Keep a known-good boot-image recovery path for the exact device and firmware build. Partition names, AVB behavior, and ramdisk contents vary by device.

## Package layout

Start from the upstream AnyKernel3 project, then place release-specific files in the expected locations:

```text
AnyKernel3/
├── anykernel.sh              package configuration and patch logic
├── Image.gz-dtb              example kernel image in ZIP root
├── tools/                    upstream AnyKernel3 helper tools
├── ramdisk/                  optional boot ramdisk overlay files
├── vendor_ramdisk/           optional vendor_boot ramdisk overlay files
├── patch/                    optional partial files for patch methods
├── vendor_patch/             optional vendor_boot patch files
└── LICENSE                   keep in the release ZIP
```

Use the kernel image name and additional partition files expected by the target tree. Do not assume every GKI device needs the same image name or partition.

## `anykernel.sh` essentials

The properties block identifies the release and target devices:

```sh
properties() { '
kernel.string=<KernelName> by <Author>
do.devicecheck=1
do.modules=0
do.cleanup=1
do.cleanuponabort=0
device.name1=<codename>
supported.versions=
supported.patchlevels=
'; }
```

Set partition and slot behavior outside that block:

```sh
BLOCK=vendor_boot;
IS_SLOT_DEVICE=auto;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=auto;
```

- `BLOCK` accepts a partition name such as `boot`, `vendor_boot`, or `auto`.
- `IS_SLOT_DEVICE=auto` detects active-slot suffixes for A/B devices.
- `RAMDISK_COMPRESSION=auto` preserves the detected ramdisk compression.
- `PATCH_VBMETA_FLAG=auto` retains the upstream automatic AVB flag behavior.

Use `template/anykernel.sh.template` as a GKI-oriented starting point. Confirm the actual partition, device names, and boot image layout from the target's known-good configuration before distributing a ZIP.

## GKI `vendor_boot` cmdline patch pattern

The `template/anykernel.sh.template` shows a small, concrete GKI package:

```sh
BLOCK=vendor_boot;
IS_SLOT_DEVICE=auto;
RAMDISK_COMPRESSION=auto;

. tools/ak3-core.sh;

split_boot;
patch_cmdline androidboot.selinux androidboot.selinux=enforcing
flash_boot;
```

`split_boot` separates the image for modification, `patch_cmdline` replaces or adds the named boot parameter, and `flash_boot` rebuilds the image for the configured target when the operator installs the ZIP. This does not fix a policy problem by itself: a boot that runs in enforcing mode still needs correct SELinux policy and labels.

For a different target, change only after verifying the partition and desired parameter. Do not copy a `vendor_boot` setting to a legacy `boot` device, or vice versa.

## Ramdisk and multi-partition changes

AnyKernel3 provides methods to edit a ramdisk rather than replace it wholesale. Prefer targeted additions or substitutions over replacing an OEM ramdisk file.

- Use `split_boot` and `flash_boot` for granular boot-image handling.
- Use `patch_cmdline` for a named kernel command-line entry.
- Use `patch_prop` for a property in a ramdisk property file.
- Put partial files in `patch/` or `vendor_patch/` and overlay files in
  `ramdisk/` or `vendor_ramdisk/`.
- For more than one partition, reset the AnyKernel state between partitions and give each partition its own `*-files` layout.

Keep modifications idempotent and narrow. A full replacement can discard vendor init configuration, verified-boot metadata, or root-manager compatibility that the original image carried.

## Package the release

After reviewing the final layout, package from the AnyKernel3 repository root:

```bash
zip -r9 UPDATE-<kernel-name>.zip * -x .git README.md *placeholder
```

This retains `LICENSE`, which must remain in the final ZIP. The command excludes the repository metadata, upstream README, and placeholder files. A filename ending in `-debugging` enables AnyKernel3 diagnostic archive creation during an operator-initiated install; use it only for controlled troubleshooting.

## Pre-release review

1. Verify `kernel.string`, supported devices, and partition selection against a
   known-good build for the target.
2. Confirm the expected output image and any additional DTB, DTBO, or module
   files are in the ZIP root or their documented directories.
3. Inspect every ramdisk and cmdline change for exact-target scope.
4. Keep `LICENSE` and remove development-only content.
5. Document the intended device, Android version, partition target, and
   recovery path alongside the release.
6. Ask for explicit confirmation before giving any physical-device installation
   instruction.