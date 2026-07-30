# Dolby Atmos Fix for XOS / HyperOS Ports

Fix Dolby on HyperOS 2 and other ROMs when the donor firmware ships MiSound instead of Dolby.

## Steps

1. Add Dolby HAL properties to `vendor.prop`:
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

2. Remove the MiSound APK from `product/`.
3. Add Dolby APKs and vendor HAL blobs.
4. Delete all post-process effects in `audio_effects.xml`, leave only voice.
5. Verify HAL execution:
   - `dumpsys media.audio_flinger > /sdcard/audiodump.log`
   - If you see `(null)` path for the DAP library, check `audio_effects.xml`.
6. Ensure `/dolby/dax-default.xml` exists in `vendor`.
7. If needed, import Dolby C2 media to `vendor/c2media`.
8. Ensure all HAL binaries have `hal_dms_default_exec` context.
9. Check nacelle dependencies with `readelf -d <path_to_lib> | grep -i need`.
10. If bootloop occurs, check logcat for `CANNOT LINK` and add missing dependencies.

## Notes

- Ensure HAL libs have `u:object_r:vendor_file:s0` so dms can load them.
- If Dolby HAL manifest is missing from `vendor/etc/vintf`, add it to `manifest.xml`:
  ```xml
  <hal format="hidl">
      <name>vendor.dolby.hardware.dms</name>
      <transport>hwbinder</transport>
      <fqname>@2.0::IDms/default</fqname>
  </hal>
  ```
- Common Dolby libs: `libdlbdsservice`, `libdlbpreg`, `vendor.dolby.hardware.dms@2.0`, `vendor.dolby.hardware.dms@2.0-impl`, `libdapparamstorage`, `libdeccfg`.
- Always debug `CANNOT LINK` from logcat if Dolby HAL is not loading.
