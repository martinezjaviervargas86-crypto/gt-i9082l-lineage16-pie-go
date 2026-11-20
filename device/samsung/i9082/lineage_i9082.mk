#
# Copyright (C) 2026 Samsung GT-I9082L Pie Go Project
# Target: LineageOS 16.0 (Android 9.0 Pie - Android Go Edition)
# Device: Samsung Galaxy Grand Duos (GT-I9082L / baffin / Broadcom BCM28155)
#

# Inherit AOSP Android Go low-RAM defaults (512MB-1GB RAM profile)
$(call inherit-product, $(SRC_TARGET_DIR)/product/go_defaults.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/aosp_base_telephony.mk)

# Inherit device-specific configuration
$(call inherit-product, device/samsung/i9082/device_i9082.mk)

# Inherit LineageOS 16.0 lightweight phone configuration
$(call inherit-product, vendor/lineage/config/common_mini_phone.mk)

# Keep /system slim to fit cleanly inside 1536 MB eMMC partition
PRODUCT_ENFORCE_RRO_TARGETS := framework-res
TARGET_BOOT_ANIMATION_RES := 480

# Device identifier (must come after all inclusions)
PRODUCT_NAME := lineage_i9082
PRODUCT_DEVICE := i9082
PRODUCT_BRAND := samsung
PRODUCT_MANUFACTURER := Samsung
PRODUCT_MODEL := GT-I9082L

PRODUCT_GMS_CLIENTID_BASE := android-samsung

# Verified physical GT-I9082L (baffinvj / LatAm) identity
PRODUCT_BUILD_PROP_OVERRIDES += \
    PRODUCT_NAME=baffinvj \
    TARGET_DEVICE=baffin \
    BUILD_FINGERPRINT="samsung/baffinvj/baffin:4.2.2/JDQ39/I9082LUBUBNE1:user/release-keys" \
    PRIVATE_BUILD_DESC="baffinvj-user 4.2.2 JDQ39 I9082LUBUBNE1 release-keys"
