
# Build Props Fragment -- ROM Port

A structured template for the build.prop additions needed during a ROM port. Copy only the sections relevant to the target device. Every prop included must be confirmed to have the stated effect on this specific device -- do not add props blindly.

Fill in the target file for each section:
- Device-tier props go in `device/<vendor>/<codename>/<codename>.mk` as
  `PRODUCT_PROPERTY_OVERRIDES` or directly in a `build.prop` overlay.
- Vendor-tier props go in the device's `vendor/build.prop` or in a
  `vendor/default.prop` overlay.
- System-ext-tier props go in `system_ext/etc/build.prop`.

---

## Display

```
# Physical display density -- verify with: adb shell wm density
ro.sf.lcd_density=<value>
```

## Debug (engineering builds only -- remove before release)

```
# Enable ADB on boot for logcat access without a working UI
ro.adb.secure=0
ro.secure=0
ro.debuggable=1
persist.service.debuggable=1
persist.service.adb.enable=1
```

## OEM feature toggles (Transsion / XOS platform)

Include only the props for features that exist on the target hardware. Each prop is listed with the observed symptom it fixes.

```
# TNE (Transsion Native Experience) fatal crash in system_server on custom ROMs
ro.transsion.tne.support=false

# AMOLED backlight HAL producing incorrect levels
ro.tr_light.backlight.hal.optimization.feature.support=1
ro.tr_light.backlight.level=255
ro.tr_light.xdr.support=0
ro.tr_light.xdr.v2.support=0

# Infrared blaster not detected
ro.vendor.tran.ir.support=1

# Animation jank / stuttering
ro.tr_animation.platform_level=3
ro.tr_perf.launch_start_exit.model=3
ro.tr_perf.power_keyguard_animation.model=3
ro.tr_perf.recent_animation.model=3
ro.tr_perf.unlock_mode.model=3

# Device reported as uncertified in Play Store
ro.transsion.enable_gms_secondary_dex2oat=true

# Brightness capped to less than 100% inside apps (display HAL override)
ro.tran_app_brightness_limit_v2.support=0
ro.tran_app_brightness_limit_V2.support=0
ro.tran_app_brightness_limit.support=0
ro.tr_light.app_brightness_limit_v2.feature.support=0
ro.tr_light.app_brightness_limit.feature.support=0

# Elliptic ultrasound proximity sensor (devices that have the hardware)
ro.tr_audio.ultrasound.support=1

# NPU audio crash on devices without an NPU audio DSP
ro.tr_audio.esport_npu.feature.support=0
```

---

## Notes

- Source for each prop: [fill in which firmware image / file it came from]
- Confirmed working on: [device codename, ROM base version, date tested]
- Props not yet tested: [list]
- Props confirmed not needed for this device: [list, with reason]
