
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

Do not ship these props in a release build.

---

## Prop fixes (add to tr_region build.prop or device build.prop)

Apply these after a successful first boot if the relevant feature misbehaves. Do not apply all of them blindly -- confirm the symptom first.

```
# DPI -- adjust to match physical display density of the target device
ro.sf.lcd_density=440

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

---

## Size reduction tips

- Remove apps from `tr_region/operator/app/` -- these are carrier-bundled apps that serve no purpose on a custom ROM and can be several hundred MB combined.
- Only carry the Transsion HAL blobs that the target device actually uses. Audit
  `tr_product/` against the device's hardware feature list before including files wholesale.
