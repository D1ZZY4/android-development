
# defconfig fragment reference

`arch/arm64/configs/<name>_defconfig` is a flat list of `CONFIG_X=y/n/m` lines. Don't hand-write one from scratch — diff against a known-working defconfig for the same or a very similar device/SoC when changing something.

## Common options worth checking when debugging boot/feature issues

```
# SELinux — must be enabled for a stock-userspace-compatible ROM
CONFIG_SECURITY_SELINUX=y
CONFIG_SECURITY_SELINUX_BOOTPARAM=y

# Required for most modern Android userspace (varies by Android version target)
CONFIG_ANDROID_BINDER_IPC=y
CONFIG_ANDROID_BINDERFS=y
CONFIG_ASHMEM=y                  # or CONFIG_ANDROID_SIMPLE_LMK / newer memory mgmt on GKI-adjacent kernels

# f2fs is common on Android data partitions
CONFIG_F2FS_FS=y
CONFIG_F2FS_FS_SECURITY=y

# KernelSU (if the user wants root via KernelSU rather than Magisk)
CONFIG_KSU=y
```

## Applying a fragment on top of an existing defconfig (merge, don't overwrite)

```bash
scripts/kconfig/merge_config.sh -m out/.config arch/arm64/configs/<fragment>.config
make O=out olddefconfig
```

`olddefconfig` resolves any newly-introduced dependent options with their defaults rather than prompting interactively — necessary in a non-interactive agent/CI context.

## Diffing two defconfigs to find what changed (common debug step)

```bash
diff <(sort known_working_defconfig) <(sort broken_defconfig)
```
