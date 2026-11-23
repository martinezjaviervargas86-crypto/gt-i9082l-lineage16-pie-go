LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_SRC_FILES := hwc_wrapper.c
LOCAL_HEADER_LIBRARIES := libhardware_headers
LOCAL_SHARED_LIBRARIES := liblog libdl
LOCAL_MODULE := hwcomposer.capri
LOCAL_MODULE_RELATIVE_PATH := hw
LOCAL_VENDOR_MODULE := true
LOCAL_MODULE_TAGS := optional
LOCAL_CFLAGS := -Wall -Wextra -Wno-unused-parameter
include $(BUILD_SHARED_LIBRARY)
