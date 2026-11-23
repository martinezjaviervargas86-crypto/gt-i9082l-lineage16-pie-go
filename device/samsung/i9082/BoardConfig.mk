#
# Copyright (C) 2026 Samsung GT-I9082L Pie Go Project
# BoardConfig for LineageOS 16.0 (Android 9.0 Pie - Android Go Edition)
# Device: Samsung Galaxy Grand Duos (GT-I9082L / baffin / Broadcom BCM28155)
#

USE_CAMERA_STUB := true

# Inherit from proprietary vendor
-include vendor/samsung/i9082/BoardConfigVendor.mk

# Platform
TARGET_BOARD_PLATFORM := capri

# CPU (Broadcom BCM28155 Dual-Core ARM Cortex-A9 @ 1.2 GHz)
TARGET_ARCH := arm
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_VARIANT := cortex-a9

# Bootloader
TARGET_NO_BOOTLOADER := true
TARGET_BOOTLOADER_BOARD_NAME := capri

# Kernel (Linux 3.0.101 with Android 9.0 Pie backports: hwbinder/vndbinder, zram, qtaguid, SELinux)
TARGET_KERNEL_ARCH := arm
TARGET_KERNEL_HEADER_ARCH := arm
TARGET_KERNEL_SOURCE := kernel/samsung/i9082
TARGET_KERNEL_CONFIG := lineageos_i9082_pie_go_defconfig
BOARD_KERNEL_IMAGE_NAME := zImage
BOARD_KERNEL_CMDLINE := console=ttyS0,115200n8 mem=832M@0xA2000000 androidboot.console=ttyS0 vc-cma-mem=0/176M@0xCB000000 androidboot.hardware=capri androidboot.selinux=permissive
BOARD_KERNEL_BASE := 0xa2000000
BOARD_KERNEL_PAGESIZE := 4096
TARGET_KERNEL_CLANG_COMPILE := false

# File systems & verified GT-I9082L PIT partition sizes (from out/gt_i9082l.pit)
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
BOARD_BOOTIMAGE_PARTITION_SIZE := 8388608
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 8388608
# Verified PIT ID=19 (system) = 3,145,728 blocks * 512B = 1,610,612,736 bytes (1536 MB)
# Reserve 1500 MB (no journal) for Android 9.0 Pie Go + GApps Go headroom
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 1572864000
BOARD_SYSTEMIMAGE_JOURNAL_SIZE := 0
BOARD_CACHEIMAGE_PARTITION_SIZE := 1073741824
BOARD_USERDATAIMAGE_PARTITION_SIZE := 4404019200
BOARD_FLASH_BLOCK_SIZE := 131072

# Full dexpreopt for snappy UI on dual-core Cortex-A9 (fits comfortably inside 1500 MB /system)
WITH_DEXPREOPT := true
DONT_DEXPREOPT_PREBUILTS := true

# Legacy non-Treble VINTF Device Manifest (Pie HIDL wrappers)
DEVICE_MANIFEST_FILE := device/samsung/i9082/manifest.xml
PRODUCT_FULL_TREBLE_OVERRIDE := false
PRODUCT_COMPATIBLE_PROPERTY_OVERRIDE := true

# Recovery & OTA device assertions (strictly GT-I9082 / GT-I9082L / baffin family)
TARGET_RECOVERY_FSTAB := device/samsung/i9082/rootdir/fstab.capri
TARGET_OTA_ASSERT_DEVICE := i9082,i9082l,baffin,baffinvj,GT-I9082,GT-I9082L
LZMA_RAMDISK_TARGETS := recovery
TARGET_USE_CUSTOM_LUN_FILE_PATH := "/sys/class/android_usb/android0/f_mass_storage/lun%d/file"
TARGET_RECOVERY_PIXEL_FORMAT := ABGR_8888
TARGET_RECOVERY_DENSITY := hdpi

# Hardware rendering (Broadcom VideoCore IV - OpenGL ES 2.0, HWC1 via hwc2on1adapter)
BOARD_EGL_WORKAROUND_BUG_10194508 := true
TARGET_USES_HWC2 := false
TARGET_RUNNING_WITHOUT_SYNC_FRAMEWORK := true
TARGET_REQUIRES_SYNCHRONOUS_SETSURFACE := true
USE_OPENGL_RENDERER := true

# Pie ABI Shims for prebuilt Broadcom JB/KK blobs (verified by ELF audit)
TARGET_LD_SHIM_LIBS := \
    /system/vendor/bin/hw/rild|libcapri_pie_shim.so \
    /system/lib/libbrcm_ril.so|libcapri_pie_shim.so \
    /system/lib/libtvservice_binder.so|libcapri_pie_shim.so \
    /system/lib/hw/audio.primary.capri.so|libcapri_pie_shim.so \
    /system/vendor/lib/hw/hwcomposer.capri.vendor.so|libcapri_pie_shim.so \
    /system/vendor/lib/hw/camera.capri.so|libcapri_pie_shim.so \
    /system/vendor/lib/egl/libGLES_vc4.so|libcapri_pie_shim.so \
    /system/bin/glgps|libglgps-compat.so

# Allow legacy JB/KK text relocations in Broadcom/Samsung audio blobs (lib_Samsung_Resampler.so)
TARGET_PROCESS_SDK_VERSION_OVERRIDE += \
    /vendor/bin/hw/android.hardware.audio@2.0-service=22 \
    /system/vendor/bin/hw/android.hardware.audio@2.0-service=22 \
    /system/bin/mediaserver=22

# Lineage Hardware / Samsung LiveDisplay & CABC
BOARD_HARDWARE_CLASS += hardware/samsung/lineagehw

# Audio (use legacy audio_policy.conf cleanly on Pie)
USE_XML_AUDIO_POLICY_CONF := 0

# Legacy prebuilt ELF compatibility on Android 9.0 Pie Soong/Kati
BUILD_BROKEN_DUP_RULES := true
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true

# Bluetooth (Broadcom BCM4334)
BOARD_HAVE_BLUETOOTH := true
BOARD_HAVE_BLUETOOTH_BCM := true
BOARD_CUSTOM_BT_CONFIG := device/samsung/i9082/bluetooth/libbt_vndcfg.txt
BOARD_BLUETOOTH_BDROID_BUILDCFG_INCLUDE_DIR := device/samsung/i9082/bluetooth

# Camera (HAL1 via android.hardware.camera.provider@2.4-service legacy/0)
TARGET_HAS_LEGACY_CAMERA_HAL1 := true
TARGET_USE_AVC_BASELINE_PROFILE := true
TARGET_NEEDS_LEGACY_CAMERA_HAL1_DYN_NATIVE_HANDLE := true

# Wi-Fi (Broadcom BCM4334 bcmdhd)
BOARD_HAVE_SAMSUNG_WIFI             := true
BOARD_WLAN_DEVICE                   := bcmdhd
BOARD_WLAN_DEVICE_REV               := bcm4334
WPA_SUPPLICANT_VERSION              := VER_0_8_X
BOARD_WPA_SUPPLICANT_DRIVER         := NL80211
BOARD_WPA_SUPPLICANT_PRIVATE_LIB    := lib_driver_cmd_bcmdhd
BOARD_HOSTAPD_DRIVER                := NL80211
BOARD_HOSTAPD_PRIVATE_LIB           := lib_driver_cmd_bcmdhd
WIFI_DRIVER_MODULE_NAME             := "dhd"
WIFI_DRIVER_MODULE_PATH             := "/vendor/lib/modules/dhd.ko"
WIFI_DRIVER_FW_PATH_PARAM           := "/sys/module/dhd/parameters/firmware_path"
WIFI_DRIVER_FW_PATH_AP              := "/system/etc/wifi/bcmdhd_apsta.bin_b2"
WIFI_DRIVER_FW_PATH_STA             := "/system/etc/wifi/bcmdhd_sta.bin_b2"
WIFI_DRIVER_MODULE_AP_ARG           := "firmware_path=/system/etc/wifi/bcmdhd_apsta.bin_b2 nvram_path=/system/etc/wifi/nvram_net.txt"
WIFI_DRIVER_MODULE_ARG              := "firmware_path=/system/etc/wifi/bcmdhd_sta.bin_b2 nvram_path=/system/etc/wifi/nvram_net.txt"
WIFI_BAND                           := 802_11_ABG

# Charger & Health (handled by android.hardware.health@2.0-service on Pie)
BOARD_CHARGER_ENABLE_SUSPEND := true
BOARD_CHARGING_MODE_BOOTING_LPM := /sys/class/power_supply/battery/batt_lp_charging

# Bootanimation & Low-RAM malloc optimization (essential for 1 GB RAM)
TARGET_BOOTANIMATION_PRELOAD := true
TARGET_BOOTANIMATION_TEXTURE_CACHE := true
MALLOC_SVELTE := true

# Prebuilt JB/KK Broadcom blobs contain text relocations
TARGET_NEEDS_PLATFORM_TEXT_RELOCATIONS := true

# SELinux (i9082 kernel 3.0.101 natively supports PolicyDB v30 xperms ioctl; permissive for bring-up)
SELINUX_IGNORE_NEVERALLOWS := true
# Legacy CM-14.1 sepolicy disabled for Phase 1 Pie permissive bring-up
# BOARD_SEPOLICY_DIRS += device/samsung/i9082/sepolicy
