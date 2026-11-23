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
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

#include <binder/IPCThreadState.h>
#include <binder/Parcel.h>
#include <binder/ProcessState.h>
#include <log/log.h>
#include <utils/RefBase.h>

using namespace android;

/*
 * Broadcom tvserver is a prebuilt JB/KK daemon that registers "broadcom.tvservice"
 * using ProcessState::self() (which defaults to /dev/binder on Android 9 Pie).
 * However, all its Pie HIDL consumers (hwcomposer.capri.so in composer@2.1-service,
 * camera.capri.so in camera.provider@2.4-service, audio.hdmi.capri.so in audio@2.0)
 * run on /dev/vndbinder. Initialize /dev/vndbinder before tvserver::main() runs.
 */
__attribute__((constructor))
static void capri_tvserver_init_vndbinder(void) {
    const char *prog = getprogname();
    if (!prog) {
        return;
    }
    const char *base = strrchr(prog, '/');
    base = base ? base + 1 : prog;
    if (strcmp(base, "tvserver") == 0) {
        ALOGI("capri_pie_shim: redirecting tvserver ProcessState to /dev/vndbinder");
        ProcessState::initWithDriver("/dev/vndbinder");
    }
}

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

// Legacy libutils VectorImpl / SortedVectorImpl reserved virtual slots
// Verified missing via ELF audit on camera.capri.so, audio.primary.capri.so & libtvservice_binder.so
void _ZN7android10VectorImpl19reservedVectorImpl1Ev(void) {}
void _ZN7android10VectorImpl19reservedVectorImpl2Ev(void) {}
void _ZN7android10VectorImpl19reservedVectorImpl3Ev(void) {}
void _ZN7android10VectorImpl19reservedVectorImpl4Ev(void) {}
void _ZN7android10VectorImpl19reservedVectorImpl5Ev(void) {}
void _ZN7android10VectorImpl19reservedVectorImpl6Ev(void) {}
void _ZN7android10VectorImpl19reservedVectorImpl7Ev(void) {}
void _ZN7android10VectorImpl19reservedVectorImpl8Ev(void) {}

void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl1Ev(void) {}
void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl2Ev(void) {}
void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl3Ev(void) {}
void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl4Ev(void) {}
void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl5Ev(void) {}
void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl6Ev(void) {}
void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl7Ev(void) {}
void _ZN7android16SortedVectorImpl25reservedSortedVectorImpl8Ev(void) {}

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
