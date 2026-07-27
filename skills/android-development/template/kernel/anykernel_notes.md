# AnyKernel3 packaging notes

AnyKernel3 (osm0sis/AnyKernel3) packages a compiled kernel into a flashable
zip without needing to rebuild a full boot.img manually. Useful for legacy
(non-GKI) kernel builds distributed to end users.

## Minimal `anykernel.sh` fields to fill in

```bash
properties() { '
kernel.string=<Your Kernel Name> by <you>
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=<codename>
device.name2=<alt_codename_if_any>
supported.versions=
supported.patchlevels=
'; }

## AnyKernel install
boot_patch.sh --header
write_boot
## end install
```

## What actually needs to be true before packaging

1. `Image.gz-dtb` (or whatever `BOARD_KERNEL_IMAGE_NAME` says the ROM expects)
   exists at `out/arch/arm64/boot/`.
2. Device codename(s) in `device.name1`/`device.name2` match what
   `getprop ro.product.device` reports on the actual target — a mismatch
   here causes AnyKernel3 to abort the flash with a device-check failure,
   which is often mistaken for a build problem when it's actually just a
   string mismatch.
3. If the device uses `vendor_boot` (GKI-style split) rather than a single
   `boot.img`, plain AnyKernel3 boot patching may not be sufficient —
   check whether the device needs `vendor_boot` handling before assuming
   the standard template works unmodified.

## Packaging

```bash
cd AnyKernel3
cp <path_to_output>/Image.gz-dtb zImage      # naming inside the zip depends on anykernel.sh's write_boot logic
zip -r9 <kernelname>-<codename>-<date>.zip * -x .git README.md *placeholder
```
