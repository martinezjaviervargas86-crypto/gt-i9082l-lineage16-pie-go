/*
 * Native macOS IOKit USB Bulk Transport Bridge for Samsung Odin / Loke (0x04e8:0x685d).
 * Compiled with: clang -dynamiclib -O2 -framework IOKit -framework CoreFoundation macos_usb_bridge.c -o libmacos_usb.dylib
 */

#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOCFPlugIn.h>
#include <IOKit/IOKitLib.h>
#include <IOKit/usb/IOUSBLib.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static IOUSBDeviceInterface300 **g_dev = NULL;
static IOUSBInterfaceInterface300 **g_intf = NULL;
static UInt8 g_pipe_in = 0;
static UInt8 g_pipe_out = 0;

void usb_close_device(void) {
    if (g_intf) {
        (*g_intf)->USBInterfaceClose(g_intf);
        (*g_intf)->Release(g_intf);
        g_intf = NULL;
    }
    if (g_dev) {
        (*g_dev)->USBDeviceClose(g_dev);
        (*g_dev)->Release(g_dev);
        g_dev = NULL;
    }
    g_pipe_in = 0;
    g_pipe_out = 0;
}

int usb_open_device(int vid, int pid, int preferred_intf_num) {
    usb_close_device();

    CFMutableDictionaryRef matchingDict = IOServiceMatching(kIOUSBDeviceClassName);
    if (!matchingDict) return -1;

    CFNumberRef vidRef = CFNumberCreate(kCFAllocatorDefault, kCFNumberSInt32Type, &vid);
    CFNumberRef pidRef = CFNumberCreate(kCFAllocatorDefault, kCFNumberSInt32Type, &pid);
    CFDictionarySetValue(matchingDict, CFSTR(kUSBVendorID), vidRef);
    CFDictionarySetValue(matchingDict, CFSTR(kUSBProductID), pidRef);
    CFRelease(vidRef);
    CFRelease(pidRef);

    io_iterator_t iter = 0;
    kern_return_t kr = IOServiceGetMatchingServices(kIOMasterPortDefault, matchingDict, &iter);
    if (kr != KERN_SUCCESS || !iter) return -2;

    io_service_t usbDevice = IOIteratorNext(iter);
    IOObjectRelease(iter);
    if (!usbDevice) return -3;

    IOCFPlugInInterface **plugInInterface = NULL;
    SInt32 score = 0;
    kr = IOCreatePlugInInterfaceForService(
        usbDevice, kIOUSBDeviceUserClientTypeID, kIOCFPlugInInterfaceID, &plugInInterface, &score);
    IOObjectRelease(usbDevice);
    if (kr != KERN_SUCCESS || !plugInInterface) return -4;

    HRESULT res = (*plugInInterface)->QueryInterface(
        plugInInterface, CFUUIDGetUUIDBytes(kIOUSBDeviceInterfaceID300), (LPVOID *)&g_dev);
    (*plugInInterface)->Release(plugInInterface);
    if (res || !g_dev) return -5;

    if ((*g_dev)->USBDeviceOpenSeize(g_dev) != kIOReturnSuccess) {
        (*g_dev)->USBDeviceOpen(g_dev);
    }

    IOUSBFindInterfaceRequest req;
    req.bInterfaceClass = kIOUSBFindInterfaceDontCare;
    req.bInterfaceSubClass = kIOUSBFindInterfaceDontCare;
    req.bInterfaceProtocol = kIOUSBFindInterfaceDontCare;
    req.bAlternateSetting = kIOUSBFindInterfaceDontCare;

    io_iterator_t intfIter = 0;
    kr = (*g_dev)->CreateInterfaceIterator(g_dev, &req, &intfIter);
    if (kr != KERN_SUCCESS) {
        usb_close_device();
        return -6;
    }

    io_service_t usbIntf;
    while ((usbIntf = IOIteratorNext(intfIter))) {
        IOCFPlugInInterface **iPlug = NULL;
        SInt32 iScore = 0;
        kr = IOCreatePlugInInterfaceForService(
            usbIntf, kIOUSBInterfaceUserClientTypeID, kIOCFPlugInInterfaceID, &iPlug, &iScore);
        IOObjectRelease(usbIntf);
        if (kr != KERN_SUCCESS || !iPlug) continue;

        IOUSBInterfaceInterface300 **cand = NULL;
        res = (*iPlug)->QueryInterface(
            iPlug, CFUUIDGetUUIDBytes(kIOUSBInterfaceInterfaceID300), (LPVOID *)&cand);
        (*iPlug)->Release(iPlug);
        if (res || !cand) continue;

        UInt8 intfNum = 0;
        (*cand)->GetInterfaceNumber(cand, &intfNum);
        if (preferred_intf_num >= 0 && intfNum != (UInt8)preferred_intf_num) {
            (*cand)->Release(cand);
            continue;
        }

        IOReturn openRes = (*cand)->USBInterfaceOpenSeize(cand);
        if (openRes != kIOReturnSuccess) {
            openRes = (*cand)->USBInterfaceOpen(cand);
        }
        if (openRes != kIOReturnSuccess) {
            (*cand)->Release(cand);
            continue;
        }

        UInt8 numEp = 0;
        (*cand)->GetNumEndpoints(cand, &numEp);
        UInt8 pIn = 0, pOut = 0;
        for (UInt8 pipeRef = 1; pipeRef <= numEp; pipeRef++) {
            UInt8 dir = 0, num = 0, tType = 0, interval = 0;
            UInt16 maxPkt = 0;
            if ((*cand)->GetPipeProperties(cand, pipeRef, &dir, &num, &tType, &maxPkt, &interval) == kIOReturnSuccess) {
                if (tType == kUSBBulk) {
                    if (dir == kUSBIn && !pIn) pIn = pipeRef;
                    if (dir == kUSBOut && !pOut) pOut = pipeRef;
                }
            }
        }

        if (pIn && pOut) {
            g_intf = cand;
            g_pipe_in = pIn;
            g_pipe_out = pOut;
            break;
        }

        (*cand)->USBInterfaceClose(cand);
        (*cand)->Release(cand);
    }
    IOObjectRelease(intfIter);

    if (!g_intf || !g_pipe_in || !g_pipe_out) {
        usb_close_device();
        return -7;
    }

    return 0;
}

int usb_write_bulk_chunked(const uint8_t *data, int len, int chunk_size, int timeout_ms) {
    if (!g_intf || !g_pipe_out) return -1;
    if (len == 0) {
        IOReturn kr = (*g_intf)->WritePipeTO(g_intf, g_pipe_out, (void *)data, 0, timeout_ms, timeout_ms);
        return (kr == kIOReturnSuccess) ? 0 : -(int)(kr & 0xFFFF);
    }
    int step_max = (chunk_size > 0) ? chunk_size : len;
    int offset = 0;
    while (offset < len) {
        int step = len - offset;
        if (step > step_max) step = step_max;
        IOReturn kr = (*g_intf)->WritePipeTO(
            g_intf, g_pipe_out, (void *)(data + offset), (UInt32)step, timeout_ms, timeout_ms);
        if (kr != kIOReturnSuccess) {
            return -(int)(kr & 0xFFFF);
        }
        offset += step;
    }
    return offset;
}

int usb_write_bulk(const uint8_t *data, int len, int timeout_ms) {
    return usb_write_bulk_chunked(data, len, 0, timeout_ms);
}

int usb_read_bulk(uint8_t *buf, int max_len, int timeout_ms) {
    if (!g_intf || !g_pipe_in) return -1;
    UInt32 actual = (UInt32)max_len;
    IOReturn kr = (*g_intf)->ReadPipeTO(g_intf, g_pipe_in, buf, &actual, timeout_ms, timeout_ms);
    if (kr != kIOReturnSuccess) {
        if (kr == kIOUSBPipeStalled) {
            (*g_intf)->ClearPipeStall(g_intf, g_pipe_in);
        }
        return -(int)(kr & 0xFFFF);
    }
    return (int)actual;
}
