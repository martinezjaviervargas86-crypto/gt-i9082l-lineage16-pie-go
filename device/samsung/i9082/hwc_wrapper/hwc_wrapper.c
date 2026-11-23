/*
 * Copyright (C) 2026 Samsung GT-I9082L Pie Go Project
 *
 * Lightweight HWC1 wrapper for Broadcom VideoCore IV (hwcomposer.capri.vendor.so).
 * Keeps full 60 FPS WFC hardware overlays active while sanitizing Android 9 Pie
 * HWC_BACKGROUND / SolidColor / Dim layers (whose union backgroundColor 0xff000000
 * otherwise causes Broadcom's JB/KK hwc worker to SIGSEGV dereferencing 0xff000000).
 */

#define LOG_TAG "hwcomposer.capri.wrapper"

#include <dlfcn.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include <hardware/hardware.h>
#include <hardware/hwcomposer.h>
#include <log/log.h>

#define VENDOR_HWC_PATH "/vendor/lib/hw/hwcomposer.capri.vendor.so"

static void *g_vendor_lib = NULL;
static int (*g_orig_prepare)(struct hwc_composer_device_1 *dev,
                             size_t numDisplays,
                             hwc_display_contents_1_t **displays) = NULL;
static int (*g_orig_set)(struct hwc_composer_device_1 *dev,
                         size_t numDisplays,
                         hwc_display_contents_1_t **displays) = NULL;
static int (*g_orig_close)(struct hw_device_t *device) = NULL;

static void sanitize_displays(size_t numDisplays, hwc_display_contents_1_t **displays) {
    if (!displays) {
        return;
    }
    for (size_t d = 0; d < numDisplays; d++) {
        hwc_display_contents_1_t *list = displays[d];
        if (!list) {
            continue;
        }
        for (size_t i = 0; i < list->numHwLayers; i++) {
            hwc_layer_1_t *layer = &list->hwLayers[i];
            if (layer->compositionType == HWC_FRAMEBUFFER_TARGET) {
                continue;
            }
            /*
             * HWC_BACKGROUND shares a union with layer->handle (e.g. ARGB 0xff000000
             * for Dim Layer). Convert HWC_BACKGROUND or NULL-handle layers to
             * HWC_FRAMEBUFFER + HWC_SKIP_LAYER so SurfaceFlinger composes them on
             * VideoCore IV GLES2 while normal layers keep full hardware WFC overlays.
             */
            if (layer->compositionType == HWC_BACKGROUND || layer->handle == NULL) {
                layer->compositionType = HWC_FRAMEBUFFER;
                layer->flags |= HWC_SKIP_LAYER;
                layer->handle = NULL;
            }
        }
    }
}

static int wrapper_prepare(struct hwc_composer_device_1 *dev,
                           size_t numDisplays,
                           hwc_display_contents_1_t **displays) {
    sanitize_displays(numDisplays, displays);
    return g_orig_prepare ? g_orig_prepare(dev, numDisplays, displays) : -EINVAL;
}

static int wrapper_set(struct hwc_composer_device_1 *dev,
                       size_t numDisplays,
                       hwc_display_contents_1_t **displays) {
    sanitize_displays(numDisplays, displays);
    return g_orig_set ? g_orig_set(dev, numDisplays, displays) : -EINVAL;
}

static int wrapper_close(struct hw_device_t *device) {
    int ret = g_orig_close ? g_orig_close(device) : 0;
    g_orig_prepare = NULL;
    g_orig_set = NULL;
    g_orig_close = NULL;
    return ret;
}

static int wrapper_open(const struct hw_module_t *module,
                        const char *name,
                        struct hw_device_t **device) {
    (void)module;

    if (!g_vendor_lib) {
        g_vendor_lib = dlopen(VENDOR_HWC_PATH, RTLD_NOW);
        if (!g_vendor_lib) {
            ALOGE("Failed to dlopen %s: %s", VENDOR_HWC_PATH, dlerror());
            return -ENOENT;
        }
    }

    struct hw_module_t *vendor_hmi =
        (struct hw_module_t *)dlsym(g_vendor_lib, HAL_MODULE_INFO_SYM_AS_STR);
    if (!vendor_hmi || !vendor_hmi->methods || !vendor_hmi->methods->open) {
        ALOGE("Failed to resolve HMI symbol in %s", VENDOR_HWC_PATH);
        return -EINVAL;
    }

    int ret = vendor_hmi->methods->open(vendor_hmi, name, device);
    if (ret != 0 || !device || !*device) {
        ALOGE("Vendor HWC open(%s) failed: %d", name ? name : "null", ret);
        return ret;
    }

    hwc_composer_device_1_t *hwc_dev = (hwc_composer_device_1_t *)(*device);
    g_orig_prepare = hwc_dev->prepare;
    g_orig_set = hwc_dev->set;
    g_orig_close = hwc_dev->common.close;

    hwc_dev->prepare = wrapper_prepare;
    hwc_dev->set = wrapper_set;
    hwc_dev->common.close = wrapper_close;

    ALOGI("Loaded %s via capri HWC1 Dim-Layer safety wrapper (API 0x%x)",
          VENDOR_HWC_PATH, hwc_dev->common.version);
    return 0;
}

static struct hw_module_methods_t wrapper_module_methods = {
    .open = wrapper_open,
};

struct hw_module_t HAL_MODULE_INFO_SYM = {
    .tag = HARDWARE_MODULE_TAG,
    .module_api_version = HWC_MODULE_API_VERSION_0_1,
    .hal_api_version = HARDWARE_HAL_API_VERSION,
    .id = HWC_HARDWARE_MODULE_ID,
    .name = "Broadcom Capri HWC1 Pie Wrapper",
    .author = "GT-I9082L Pie Go Project",
    .methods = &wrapper_module_methods,
};
