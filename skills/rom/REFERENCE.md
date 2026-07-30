
# ROM Build -- Reference

Detailed commands and patterns for ROM builds. Read the relevant section only.

## Workspace setup

```bash
# One-time repo tool + git identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Init a manifest (LineageOS example, adjust branch per target Android version)
repo init -u https://github.com/LineageOS/android.git -b lineage-22.1 --git-lfs

# Local manifests for device/vendor/kernel trees not in the main manifest
mkdir -p .repo/local_manifests
# put local_manifest.xml here -- see template/local_manifest.xml

repo sync -c -j$(nproc --all) --force-sync --no-tags
```

- `-c` = current branch only (faster, smaller).
- `-j$(nproc --all)` = parallel jobs, but on constrained bandwidth/RAM drop to a fixed number (e.g. `-j4`) to avoid OOM or throttling.
- If sync fails mid-way with "path already exists" or similar, check for stale locks (`.repo/.repo_fetchtimes.json`, `*.lock` files) first.

## Building

```bash
source build/envsetup.sh

# LineageOS shorthand for device setup + lunch
breakfast <device_codename>

# Or explicit lunch (AOSP-style)
lunch lineage_<device_codename>-userdebug

# Full build
mka bacon          # LineageOS: builds + packages OTA zip
# or brunch for device-codename targeting (LineageOS)
brunch <device_codename>
# or
mka <target>        # AOSP: e.g. `mka droid`
```

Background it and tail:

```bash
nohup mka bacon > /tmp/rom_build.log 2>&1 &
# or
nohup brunch <device_codename> > /tmp/rom_build.log 2>&1 &
tail -f /tmp/rom_build.log
```

## Reading build failures

Find the **first** error, not the last -- a single early failure (missing file, unresolved dependency, bad Makefile syntax) commonly cascades into dozens of downstream `FAILED:` lines that are just noise from the first one.

```bash
grep -n -m1 -E "error:|FAILED:|\*\*\* " /tmp/rom_build.log
```

| Symptom in log | Likely cause | Where to look |
|---|---|---|
| `fatal error: <file>.h: No such file or directory` | Missing dependency repo or wrong manifest branch | `.repo/local_manifests/*.xml`, does the referenced path actually exist under the tree? |
| `Cannot find package '...' for module '...'` (Soong/Android.bp) | `Android.bp` module name typo or missing `PRODUCT_PACKAGES` entry | `device/<vendor>/<codename>/Android.mk` or `.bp`, `device.mk` |
| `undefined reference to '...'` at link time | Missing `LOCAL_SHARED_LIBRARIES`/`LOCAL_STATIC_LIBRARIES` or ABI mismatch | The failing module's `Android.mk`/`.bp` |
| `ninja: build stopped: subcommand failed` with no further detail above | Real error is earlier in the log, ninja just reports the aggregate failure | scroll/grep further up, don't diagnose from this line alone |
| Signing/verity errors during `mka bacon` packaging step | Missing or mismatched keys in `vendor/lineage-priv` (test-keys) | Check `signing` step config, not the OS build itself |

## Device tree skeleton reference

A minimal device tree has, at minimum:
- `AndroidProducts.mk` -- registers the product makefile
- `<codename>.mk` / `device_<vendor>_<codename>.mk` -- product definition, packages, overlays
- `BoardConfig.mk` -- partition layout, kernel config pointer, architecture flags
- `device.mk` -- inherited product config
- `overlay/` -- resource overlays
  (`frameworks/base/core/res/res/values/*.xml` style paths)

See `template/` for skeleton fragments.