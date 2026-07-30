
# Transsion XOS 16 -- ROM Port Boot Fixes

Known boot blockers and required modifications when porting XOS 16 (Transsion stock ROM) to a custom ROM base (AOSP/LineageOS). Every fix listed here has been observed to cause a boot failure or runtime misbehavior when omitted.

Credit: ramabondanp

---

## Required partition images

Extract these from the XOS 16 donor firmware before starting:

- `product.img`
- `system.img`
- `system_ext.img`
- `tr_product.img`
- `tr_region.img`

For `tr_region` and `tr_product`: either merge their contents into the system or product layers, or add new fstab entries in vendor and recovery. See `partition-strategy.md` for both approaches.

---

## Boot blockers (must fix before first boot)

### 1. Remove tranwifi.jar from system_ext

`system_ext/framework/tranwifi.jar` is an OEM-only framework JAR. The custom ROM's framework does not declare it, which causes a ClassNotFoundException crash during framework boot.

```bash
rm system_ext/framework/tranwifi.jar
# Also remove its permissions declaration if present:
grep -rl "tranwifi" system_ext/etc/permissions/ | xargs rm -f
```

### 2. Disable vfy_boot service in init.rc

The `vfy_boot` service references a Transsion-specific binary that is not present after porting. A failed exec() in init causes a boot hang.

In `system/system/etc/init/hw/init.rc` (or any init file that references it), find the service block and comment it out:

```
# service vfy_boot /vendor/bin/vfy_boot
#     class core
#     ...
```

Do not delete the line if other service dependencies reference this service by name -- comment it out so init skips it without propagating a dependency failure.

### 3. Remove unsupported property context entry from vendor SELinux

`ro.vendor.trancare.uxdetectorrest` is a Transsion-specific property that is not declared in the custom ROM's SELinux policy. Its presence in `vendor/etc/selinux/vendor_property_contexts` causes `property_info_serializer` to fail at build time.

```bash
grep -n "ro.vendor.trancare.uxdetectorrest" \
  vendor/etc/selinux/vendor_property_contexts
# Remove the matching line(s).
```

---

## Debug setup (add to system_ext/etc/build.prop for engineering builds only)

Enable ADB on boot so you can pull logcat without a working UI:

```
# ADB on boot -- engineering/debug builds only; remove before production
ro.adb.secure=0
ro.secure=0
ro.debuggable=1
persist.service.debuggable=1
persist.service.adb.enable=1
```

Do not ship these props in a release build. These disable verified boot and replace system properties, which breaks CTS, SafetyNet, and Play Integrity attestation on Android 10+. Revert all of them for production images.

---

## Prop fixes (add to tr_region build.prop or device build.prop)

Apply these after a successful first boot if the relevant feature misbehaves. Do not apply all of them blindly -- confirm the symptom first.

```
# DPI -- adjust to match physical display density of the target device
ro.sf.lcd_density=440

# Multi-slot / hardware SKU config for 3-slot or tri-SIM devices
ro.boot.product.hardware.sku=tsts
persist.radio.multisim.config=tsts
ro.telephony.sim.count=3
telephony.active_modems.max_count=3
persist.vendor.radio.msimmode=tsts
ro.vendor.radio.max.multisim=tsts
persist.vendor.radio.tsd.multisimmode=2

# Touch and rendering toggles
ro.tran.touch.ctl=1
ro.transsion.fling_render_boost_support=1
ro.tran_sounds_V3.9_support=1

# Brightness fix
ro.vendor.transsion.backlight_hal.optimization=1
ro.transsion.backlight.level=-1
ro.transsion.physical.backlight.optimization=1

# Effect engine / blur disable
ro.tran.effectengine.dynamicblur.support=0
ro.surface_flinger.supports_background_blur=0

# AOD disable
ro.tran_aod_v3_support=0

# 5G switches
ro.tran_smart_5g_3nd_support=0
ro.tran_5g_switch_support=0

# Fingerprint mode
ro.optical_fingerprint_support=0
ro.side_fingerprint_support=1
ro.os_fingerprint_incallrecord_support=1
ro.os_fingerprint_answer_call_support=1

# Vibrator fix
ro.tran_vibrate_ontouch2.0.support=0

# Game mode toggles
ro.os_game_tp_optimization.support=1
ro.os_game_hot.support=1
ro.os_game_changer.support=1
ro.os_game_reverse_color.support=1
ro.os_game_enhancement_support=1
ro.os_game_space_user_center.support=1
ro.os_game_xunyou_accelerate.support=1

# Flashlight
ro.os_alldegree_flashlight_support=1

# Dolby / DTS audio
ro.dolby.atmos.support=false
ro.dolby.atmos.game.support=false
ro.tran_dts.support=1

# Charge behavior
ro.tran_multi_level_charge_count=0
os.charging_animation_type=33
ro.os_charge_animation_support=1

# HBM disable
ro.tran_high_brightness_mode.support=0
ro.vendor.transsion.hbm_mode_hal.support=0

# Disable TNE fatal crash reporting (crashes the system_server on custom ROMs)
ro.transsion.tne.support=false

# AMOLED backlight fix -- prevents backlight HAL from producing incorrect levels
ro.tr_light.backlight.hal.optimization.feature.support=1
ro.tr_light.backlight.level=255
ro.tr_light.xdr.support=0
ro.tr_light.xdr.v2.support=0

# Infrared blaster
ro.vendor.tran.ir.support=1

# Animation smoothness
ro.tr_animation.platform_level=3
ro.tr_perf.launch_start_exit.model=3
ro.tr_perf.power_keyguard_animation.model=3
ro.tr_perf.recent_animation.model=3
ro.tr_perf.unlock_mode.model=3

# Fix device showing as uncertified in Play Store
ro.transsion.enable_gms_secondary_dex2oat=true

# Remove app brightness cap imposed by Transsion display HAL
ro.tran_app_brightness_limit_v2.support=0
ro.tran_app_brightness_limit_V2.support=0
ro.tran_app_brightness_limit.support=0
ro.tr_light.app_brightness_limit_v2.feature.support=0
ro.tr_light.app_brightness_limit.feature.support=0

# Elliptic ultrasound proximity sensor (devices that have it)
ro.tr_audio.ultrasound.support=1

# Disable NPU-based audio processing (devices without an NPU audio DSP)
ro.tr_audio.esport_npu.feature.support=0
```

---

## Double-tap-to-wake (dt2w) key layout fix

XOS uses key 183 mapped to `F13` for the dt2w gesture event. Custom ROMs expect key 183 to be `WAKEUP` for the power manager to act on it.

Edit `system/usr/keylayout/generic.kl`:

```
# Change:
key 183   F13
# To:
key 183   WAKEUP
```

### Alternative: property-based dt2w trigger

Some XOS builds expose dt2w through a sysfs node that can be written from a boot script. If the keylayout fix alone does not enable dt2w, try this trigger:

```
on property:sys.boot_completed=1
    write /proc/gesture_function cc1
```

Add it to a custom `init.rc` snippet included from the device's init rc, or run it once from `service.sh` after boot.

---

## FaceID fix (XOS 15 / Flamescion Project on X15)

If FaceID is broken after porting, a patched FaceID package is included in this skill's assets.

Use the packaged files from `skills/port-rom/assets/apps/faceid/`:
- `FaceID/FaceID.apk`
- `FaceID/oat/arm64/FaceID.odex`
- `FaceID/oat/arm64/FaceID.vdex`

Place the APK in the system overlay and preserve the `oat/arm64/` artifacts under the same package path in the ported `system` layer. The `.odex` and `.vdex` files belong beside the APK in the runtime ART cache path for the target partition.

---

## Size reduction tips

- Remove apps from `tr_region/operator/app/` -- these are carrier-bundled apps that serve no purpose on a custom ROM and can be several hundred MB combined.
- Only carry the Transsion HAL blobs that the target device actually uses. Audit
  `tr_product/` against the device's hardware feature list before including files wholesale.
