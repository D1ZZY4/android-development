# GSI Port Guide

How to build a Generic System Image (GSI) port using MIO Kitchen. Adapted from Kanagawa Yamada's tutorial.

## Prerequisites

- MIO Kitchen
- Stock super.img from the target device
- GSI image to port
- Placebo.img

> Note: rename the GSI so its filename has no version suffix at the end.
> Example: `RisingOS-99.img` -> `RisingOS.img`. This ensures it can be repacked later.

## Steps

1. Open MIO Kitchen.
2. Unpack `super.img`.
3. Unpack the GSI image.

   You now have 2 folders: one for super, one for GSI.

4. Rename the super folder to a deploy folder in MIO Kitchen.
   Example: `RisingOS deploy`.

5. Modify the GSI contents:
   - Remove `phh` app: `system_ext/app/TrebleApp`
   - Change the device name in build.prop files:
     - `/System/product/etc/build.prop`: `ro.product.product.model=<DEVICE>`
     - `/System_ext/etc/build.prop`: `ro.product.system_ext.model=<DEVICE>`
   - Note: overlay files may override these props. Verify with `grep` after modifying.

6. Repack the GSI.
7. Rename the repacked GSI image to `system.img`.
8. Replace `system.img` in the deploy folder with the GSI-derived `system.img`.
9. Replace `product` and `system_ext` with contents from `placebo.img`:
   - Rename placebo partitions to `product.img` and `system_ext.img`
   - Replace in the deploy folder
10. Leave `vendor` untouched.
11. Repack the super image.

    Note: super repack steps vary by device. Search for the correct method for the target device.

12. Flash and test.

> Recommendation from Yamada: test the GSI with DSU before building the full port.
