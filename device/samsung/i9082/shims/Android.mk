LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_SRC_FILES := capri_pie_shim.cpp capri_atomics_shim.c
LOCAL_SHARED_LIBRARIES := libbinder libutils liblog libcutils libnetutils
LOCAL_MODULE := libcapri_pie_shim
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_CLASS := SHARED_LIBRARIES
include $(BUILD_SHARED_LIBRARY)
