
# Module Reference Index

Reference guides for creating and deploying Android system modification packages: Magisk modules, KernelSU/KSU-Next modules, and AnyKernel3 flashable kernel zips.

## Docs

- `magisk-ksu-module-guide.md` -- module structure, module.prop format, boot-stage scripts (post-fs-data, service, post-mount, boot-completed), system overlay, sepolicy rules, Zygisk, and KSU-specific extras (WebUI/webroot/)
- `anykernel3-guide.md` -- AnyKernel3 flashable zip structure, anykernel.sh properties and variables, ramdisk and cmdline patching, GKI vendor_boot support, multi-partition and multi-slot zips
- `flashable-zip-guide.md` -- upstream tools and repos for building flashable ZIPs, including `osmosim/AnyKernel3`, `ramabondanp/AnyKernel3`, and `ramabondanp/android_tools`

## How the module domain relates to other domains

- **ROM / Port ROM**: system overlay modules are an alternative to modifying the ROM source directly -- NFC library replacements (e.g. replacing OEM NfcNci with AOSP stock), prop overrides, and init.rc service stubs can all be shipped as modules rather than baked into the build.
- **GKI kernel build**: AnyKernel3 is the standard packaging tool for distributing a GKI kernel as a flashable zip -- it handles Image placement, vendor_boot ramdisk patching, and cmdline modification in one script.
- **SELinux repair**: if a module's service or binary triggers AVC denials, add minimal rules to sepolicy.rule inside the module. Derive the correct shape using the SELinux Repair domain workflow first; never use broad labels or audit2allow output directly.
- **Debug**: module scripts that fail silently show up in adb logcat or dmesg. Use the Debug domain workflow to collect and parse evidence before concluding a module script is broken.
