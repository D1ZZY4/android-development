# BoardConfig.mk skeleton — fill in per-device values, do not copy verbatim.
# This only covers the fields that most commonly trip people up; a real
# BoardConfig.mk for a modern device is much longer (A/B, dynamic partitions,
# treble, etc.) — extend from a known-working device tree for the same SoC
# rather than starting fully from scratch.

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := generic

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic

# Kernel
TARGET_KERNEL_SOURCE := kernel/<vendor>/<codename>
TARGET_KERNEL_CONFIG := <defconfig_name>
BOARD_KERNEL_IMAGE_NAME := Image.gz-dtb   # match whatever the kernel build actually outputs

# Partitions — get real sizes from `adb shell cat /proc/partitions`
# or `parted`/`fdisk` output on the device, don't guess
BOARD_BOOTIMAGE_PARTITION_SIZE := <size>
BOARD_SYSTEMIMAGE_PARTITION_SIZE := <size>
BOARD_USERDATAIMAGE_PARTITION_SIZE := <size>
BOARD_FLASH_BLOCK_SIZE := 131072

# A/B (if the device uses seamless updates)
# AB_OTA_UPDATER := true
# AB_OTA_PARTITIONS += boot system vendor

# Treble / dynamic partitions (device-dependent, verify against stock config)
# BOARD_USES_DYNAMIC_PARTITIONS := true

# Recovery
TARGET_RECOVERY_FSTAB := device/<vendor>/<codename>/rootdir/etc/recovery.fstab
