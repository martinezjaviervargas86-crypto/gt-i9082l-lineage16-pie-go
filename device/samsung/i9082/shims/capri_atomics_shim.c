/*
 * Legacy libcutils atomic symbol shims for Samsung GT-I9082L (Broadcom BCM28155) on Android 9.0 Pie.
 * Kept in an isolated translation unit without <cutils/atomic.h> so the exported C symbols
 * cannot collide with Android 9's ANDROID_ATOMIC_INLINE header definitions.
 * Verified required by ELF audit on hwcomposer.capri.so and libtvservice_binder.so.
 */

#include <stdint.h>

int32_t android_atomic_inc(volatile int32_t *addr) {
    return __sync_fetch_and_add(addr, 1);
}

int32_t android_atomic_dec(volatile int32_t *addr) {
    return __sync_fetch_and_sub(addr, 1);
}
