# Replace MiSound with Dolby on HyperOS 2

How to swap MiSound for Dolby Atmos on HyperOS 2-based ROMs.

## Steps

1. Add Dolby properties to `vendor.prop`:
   - `vendor.audio.dolby.control.support=true`
   - `vendor.audio.dolby.control.tunning.by.volume.support=false`
   - `persist.vendor.audio.hwdap=false`
   - `ro.vendor.dolby.dax.version=DAX3_3.12.0.8_r1`
   - `ro.vendor.audio.dolby.dax.support=true`
   - `persist.vendor.audio.misound.disable=true`
   - `ro.vendor.audio.device.dbcom=dolby_common`
   - `ro.vendor.audio.device.db=DB_XM`
   - `persist.vendor.audio.auto.scenario=true`
   - `ro.vendor.audio.game.effect=true`
   - `ro.vendor.audio.voice.change.support=true`
   - `ro.vendor.audio.odmvolume=true`
   - `ro.vendor.composer_version=3.3`

   Note: exact values may differ. Compare against the original HyperOS 2 vendor prop set for the target device.

2. Delete the MiSound APK (usually on `product`).
3. Add Dolby APK and vendor HAL blobs as in `dolby-atmos-fix.md`.

Reference: https://t.me/KanagawaYamadaCH/3579 for the Dolby pack and patching steps.
