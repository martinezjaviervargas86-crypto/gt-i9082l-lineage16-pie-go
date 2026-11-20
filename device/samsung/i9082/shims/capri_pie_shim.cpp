/*
 * Android 9.0 Pie (LineageOS 16.0) ABI Compatibility Shim for Samsung GT-I9082L (Broadcom BCM28155).
 * Provides legacy JB/KK symbols required by prebuilt Broadcom blobs without patching AOSP core libraries:
 *   - libtvservice_binder.so (IPCThreadState::getCallingPid, Parcel::Flattenable)
 *   - camera.capri.so / libGLES_vc4.so (RefBase::moveReferences, VectorImpl reserved virtuals)
 *   - libbrcm_ril.so / rild (ifc_set_mtu)
 */

#include <errno.h>
#include <net/if.h>
#include <stdint.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

#include <binder/IPCThreadState.h>
#include <binder/Parcel.h>
#include <log/log.h>
#include <utils/RefBase.h>

using namespace android;

extern "C" {

// Legacy non-const IPCThreadState::getCallingPid() required by libtvservice_binder.so
int _ZN7android14IPCThreadState13getCallingPidEv(IPCThreadState *state) {
    return state ? state->getCallingPid() : -1;
}

// Legacy Parcel Flattenable wrappers required by libtvservice_binder.so
status_t _ZN7android6Parcel5writeERKNS0_26FlattenableHelperInterfaceE(void *parcel, void *val);
status_t _ZNK7android6Parcel4readERNS0_26FlattenableHelperInterfaceE(void *parcel, void *val);

status_t _ZN7android6Parcel5writeERKNS_11FlattenableE(void *parcel, void *val) {
    return _ZN7android6Parcel5writeERKNS0_26FlattenableHelperInterfaceE(parcel, val);
}

status_t _ZNK7android6Parcel4readERNS_11FlattenableE(void *parcel, void *val) {
    return _ZNK7android6Parcel4readERNS0_26FlattenableHelperInterfaceE(parcel, val);
}

// Legacy JB MR1 RefBase::moveReferences no-op shim for camera.capri.so / VideoCore IV
void _ZN7android7RefBase14moveReferencesEPvPKvjRKNS_22ReferenceConverterBaseE(
        void * /*dst*/, void const * /*src*/, size_t /*n*/, const void * /*caster*/) {
}

// Legacy netutils ifc_set_mtu required by Broadcom rild / libbrcm_ril.so
int ifc_set_mtu(const char *name, int mtuSz) {
    if (!name || mtuSz <= 0) {
        return -EINVAL;
    }
    int sock = socket(AF_INET, SOCK_DGRAM | SOCK_CLOEXEC, 0);
    if (sock < 0) {
        ALOGE("capri_pie_shim: ifc_set_mtu socket failed: %s", strerror(errno));
        return -errno;
    }
    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, name, IFNAMSIZ - 1);
    ifr.ifr_mtu = mtuSz;
    int ret = ioctl(sock, SIOCSIFMTU, &ifr);
    if (ret < 0) {
        ALOGE("capri_pie_shim: ifc_set_mtu(%s, %d) failed: %s", name, mtuSz, strerror(errno));
    }
    close(sock);
    return ret;
}

} // extern "C"
