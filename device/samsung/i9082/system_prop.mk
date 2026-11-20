#
# System Properties for Samsung GT-I9082L (baffin / BCM28155)
# Target: LineageOS 16.0 (Android 9.0 Pie - Android Go Edition)
#

# === Android Go / Extreme 1 GB RAM Optimization ===
PRODUCT_PROPERTY_OVERRIDES += \
    ro.config.low_ram=true \
    ro.config.avoid_gfx_accel=false \
    ro.lmk.use_psi=false \
    ro.lmk.low=1001 \
    ro.lmk.medium=800 \
    ro.lmk.critical=0 \
    ro.lmk.critical_upgrade=true \
    ro.lmk.upgrade_pressure=40 \
    ro.lmk.downgrade_pressure=60 \
    ro.lmk.kill_heaviest_task=true \
    ro.sys.fw.bg_apps_limit=12 \
    ro.config.max_starting_bg=3 \
    pm.dexopt.install=quicken \
    pm.dexopt.bg-dexopt=speed-profile \
    dalvik.vm.dex2oat-threads=2 \
    dalvik.vm.boot-dex2oat-threads=2 \
    dalvik.vm.heapstartsize=5m \
    dalvik.vm.heapgrowthlimit=64m \
    dalvik.vm.heapsize=128m \
    dalvik.vm.heaptargetutilization=0.75 \
    dalvik.vm.heapminfree=512k \
    dalvik.vm.heapmaxfree=2m \
    ro.zygote.disable_gl_preload=1 \
    config.disable_atlas=true

# === Broadcom VideoCore IV (OpenGL ES 2.0) Pie Graphics Tuning ===
# Force legacy OpenGL HWUI renderer (SkiaGL causes glitches/overhead on VC4 GLES 2.0)
PRODUCT_PROPERTY_OVERRIDES += \
    ro.opengles.version=131072 \
    debug.hwui.renderer=opengl \
    debug.hwui.render_dirty_regions=false \
    debug.sf.latch_unsignaled=1 \
    debug.sf.disable_backpressure=1 \
    ro.sf.lcd_density=240 \
    ro.surface_flinger.max_frame_buffer_acquired_buffers=2 \
    persist.sys.ui.hw=1

# === Camera (HAL1 Legacy) ===
PRODUCT_PROPERTY_OVERRIDES += \
    camera2.portability.force_api=1 \
    persist.camera.HAL3.enabled=0

# === Media (VideoCore IV OMX) ===
PRODUCT_PROPERTY_OVERRIDES += \
    media.stagefright.legacyencoder=true \
    media.stagefright.less-secure=true \
    media.stagefright.thumbnail.prefer_hw_codecs=false

# === Radio (Dual-SIM DSDS Broadcom RIL) ===
PRODUCT_PROPERTY_OVERRIDES += \
    rild.libpath=/system/lib/libbrcm_ril.so \
    persist.radio.multisim.config=dsds \
    ro.multisim.simslotcount=2 \
    ro.telephony.call_ring.multiple=0 \
    ro.telephony.call_ring=0 \
    ro.telephony.default_network=0,0

# === Connectivity & Broadcom Platform ===
PRODUCT_PROPERTY_OVERRIDES += \
    persist.brcm.log=none \
    persist.brcm.ap_crash=none \
    persist.brcm.cp_crash=none \
    wifi.interface=wlan0 \
    ro.lineage.hardware.cabc=/sys/class/mdnie/mdnie/cabc \
    persist.sys.timezone=America/Santiago

# === Bring-up ADB Debugging (userdebug) ===
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += \
    ro.adb.secure=0 \
    ro.secure=0 \
    persist.service.adb.enable=1
