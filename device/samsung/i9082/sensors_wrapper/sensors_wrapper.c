/*
 * Copyright (C) 2026 Samsung GT-I9082L Pie Go Project
 *
 * HAL 0.1 -> 1.3 compatibility wrapper for Broadcom/Samsung sensors.capri.vendor.so.
 * Android 9 Pie android.hardware.sensors@1.0-impl requires >= SENSORS_DEVICE_API_VERSION_1_3
 * (batch + flush). Broadcom's JB/KK sensors.capri.so exposes version 0 (v0 poll device).
 */

#define LOG_TAG "sensors.capri.wrapper"

#include <dlfcn.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include <hardware/hardware.h>
#include <hardware/sensors.h>
#include <log/log.h>

#define VENDOR_SENSORS_PATH "/system/lib/hw/sensors.capri.vendor.so"

static void *g_vendor_lib = NULL;
static struct sensors_module_t *g_vendor_mod = NULL;

struct capri_sensors_device {
    sensors_poll_device_1_t device;
    struct sensors_poll_device_t *vendor_dev;
};

static int load_vendor_module(void) {
    if (g_vendor_mod) {
        return 0;
    }
    g_vendor_lib = dlopen(VENDOR_SENSORS_PATH, RTLD_NOW);
    if (!g_vendor_lib) {
        ALOGE("Failed to dlopen %s: %s", VENDOR_SENSORS_PATH, dlerror());
        return -ENOENT;
    }
    g_vendor_mod = (struct sensors_module_t *)dlsym(g_vendor_lib, HAL_MODULE_INFO_SYM_AS_STR);
    if (!g_vendor_mod || !g_vendor_mod->common.methods || !g_vendor_mod->common.methods->open) {
        ALOGE("Failed to resolve HMI symbol in %s", VENDOR_SENSORS_PATH);
        g_vendor_mod = NULL;
        return -EINVAL;
    }
    return 0;
}

static int wrapper_activate(struct sensors_poll_device_t *dev, int sensor_handle, int enabled) {
    struct capri_sensors_device *ctx = (struct capri_sensors_device *)dev;
    if (!ctx || !ctx->vendor_dev || !ctx->vendor_dev->activate) {
        return -EINVAL;
    }
    return ctx->vendor_dev->activate(ctx->vendor_dev, sensor_handle, enabled);
}

static int wrapper_setDelay(struct sensors_poll_device_t *dev,
                            int sensor_handle, int64_t sampling_period_ns) {
    struct capri_sensors_device *ctx = (struct capri_sensors_device *)dev;
    if (!ctx || !ctx->vendor_dev || !ctx->vendor_dev->setDelay) {
        return -EINVAL;
    }
    return ctx->vendor_dev->setDelay(ctx->vendor_dev, sensor_handle, sampling_period_ns);
}

static int wrapper_poll(struct sensors_poll_device_t *dev, sensors_event_t *data, int count) {
    struct capri_sensors_device *ctx = (struct capri_sensors_device *)dev;
    if (!ctx || !ctx->vendor_dev || !ctx->vendor_dev->poll) {
        return -EINVAL;
    }
    return ctx->vendor_dev->poll(ctx->vendor_dev, data, count);
}

static int wrapper_batch(struct sensors_poll_device_1 *dev,
                         int sensor_handle, int flags,
                         int64_t sampling_period_ns, int64_t max_report_latency_ns) {
    (void)flags;
    (void)max_report_latency_ns;
    return wrapper_setDelay(&dev->v0, sensor_handle, sampling_period_ns);
}

static int wrapper_flush(struct sensors_poll_device_1 *dev, int sensor_handle) {
    (void)dev;
    (void)sensor_handle;
    return -EINVAL;
}

static int wrapper_close(struct hw_device_t *device) {
    struct capri_sensors_device *ctx = (struct capri_sensors_device *)device;
    int ret = 0;
    if (ctx) {
        if (ctx->vendor_dev && ctx->vendor_dev->common.close) {
            ret = ctx->vendor_dev->common.close(&ctx->vendor_dev->common);
        }
        free(ctx);
    }
    return ret;
}

static int wrapper_open(const struct hw_module_t *module,
                        const char *name,
                        struct hw_device_t **device) {
    int err = load_vendor_module();
    if (err != 0) {
        return err;
    }

    struct hw_device_t *vdev = NULL;
    err = g_vendor_mod->common.methods->open(&g_vendor_mod->common, name, &vdev);
    if (err != 0 || !vdev) {
        ALOGE("Vendor sensors open(%s) failed: %d", name ? name : "null", err);
        return err ? err : -EINVAL;
    }

    struct capri_sensors_device *ctx =
        (struct capri_sensors_device *)calloc(1, sizeof(struct capri_sensors_device));
    if (!ctx) {
        if (vdev->close) {
            vdev->close(vdev);
        }
        return -ENOMEM;
    }

    ctx->vendor_dev = (struct sensors_poll_device_t *)vdev;
    ctx->device.common.tag = HARDWARE_DEVICE_TAG;
    ctx->device.common.version = SENSORS_DEVICE_API_VERSION_1_3;
    ctx->device.common.module = (struct hw_module_t *)module;
    ctx->device.common.close = wrapper_close;
    ctx->device.v0.activate = wrapper_activate;
    ctx->device.v0.setDelay = wrapper_setDelay;
    ctx->device.v0.poll = wrapper_poll;
    ctx->device.batch = wrapper_batch;
    ctx->device.flush = wrapper_flush;

    *device = &ctx->device.common;
    ALOGI("Loaded %s via capri Sensors HAL 1.3 wrapper", VENDOR_SENSORS_PATH);
    return 0;
}

static int wrapper_get_sensors_list(struct sensors_module_t *module,
                                    struct sensor_t const **list) {
    (void)module;
    if (load_vendor_module() != 0 || !g_vendor_mod->get_sensors_list) {
        *list = NULL;
        return 0;
    }
    return g_vendor_mod->get_sensors_list(g_vendor_mod, list);
}

static struct hw_module_methods_t wrapper_module_methods = {
    .open = wrapper_open,
};

struct sensors_module_t HAL_MODULE_INFO_SYM = {
    .common = {
        .tag = HARDWARE_MODULE_TAG,
        .module_api_version = SENSORS_MODULE_API_VERSION_0_1,
        .hal_api_version = HARDWARE_HAL_API_VERSION,
        .id = SENSORS_HARDWARE_MODULE_ID,
        .name = "Broadcom Capri Sensors HAL 1.3 Wrapper",
        .author = "GT-I9082L Pie Go Project",
        .methods = &wrapper_module_methods,
    },
    .get_sensors_list = wrapper_get_sensors_list,
    .set_operation_mode = NULL,
};
