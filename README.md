# LineageOS 16.0 (Android 9.0 Pie — Android Go Edition) para Samsung Galaxy Grand Duos (`GT-I9082L` / `GT-I9082`)

[![Build LineageOS 16.0 (Android 9.0 Pie Go) - GT-I9082L](https://github.com/martinezjaviervargas86-crypto/gt-i9082l-lineage16-pie-go/actions/workflows/build_lineage16_i9082.yml/badge.svg)](https://github.com/martinezjaviervargas86-crypto/gt-i9082l-lineage16-pie-go/actions/workflows/build_lineage16_i9082.yml)

> **Estado: Experimental / Bring-Up activo.**  
> Este proyecto lleva **Android 9.0 Pie (LineageOS 16.0)** en perfil **Android Go Edition** al **Samsung Galaxy Grand Duos (`GT-I9082L` / `baffin` / Broadcom `BCM28155`)**, un dispositivo de 2013 con 1 GB de RAM y kernel Linux `3.0.101`.  
> **Haz siempre un respaldo completo de `EFS` y `modem` antes de flashear cualquier compilación experimental.**

---

## Hardware objetivo (verificado en dispositivo físico)

| Característica | Especificación (`GT-I9082L`) |
| --- | --- |
| **Modelo / Código** | `GT-I9082L` (`baffin` / `baffinvj` / `i9082`, `CAPRI_SS_BAFFIN`) |
| **SoC / CPU** | Broadcom `BCM28155` Dual-Core ARM Cortex-A9 @ 1.2 GHz (`armeabi-v7a`, NEON) |
| **GPU** | Broadcom VideoCore IV (OpenGL ES 2.0, `176 MB` CMA) |
| **Memoria RAM** | 1 GB (`832 MB` Linux utilizable + `512 MB` ZRAM LZ4) |
| **Almacenamiento eMMC** | 8 GB (`system`: 1536 MB, `userdata`: ~4.10 GB, `KERNEL`/`RECOVERY`: 8 MB) |
| **Conectividad** | Dual-SIM DSDS (`slot1`/`slot2`), Wi-Fi/BT Broadcom `BCM4334` (`bcmdhd`), GPS Broadcom `glgps` |

---

## Arquitectura del port

Este repositorio reúne todo lo necesario para construir LineageOS 16.0 sobre hardware Broadcom Capri de 2013:

1. **Perfil Android Go optimizado para 1 GB RAM (`device/samsung/i9082/`):**
   - Hereda `go_defaults.mk` + `common_mini_phone.mk` con `ro.config.low_ram=true`, `ro.lmk.use_psi=false`, `MALLOC_SVELTE=true` y `debug.hwui.renderer=opengl`.
   - Swap comprimido **ZRAM de 512 MB (LZ4)** con `vm.swappiness=100` y `vm.page-cluster=0` en `rootdir/fstab.capri` e `init.capri.rc`.
   - `WITH_DEXPREOPT_BOOT_IMG_AND_SYSTEM_SERVER_ONLY=true` y `/system` sin journal (`1500 MB`) para caber holgadamente en la partición eMMC de `1536 MB`.

2. **Backport del Kernel Linux `3.0.101` a Android 9 Pie (`kernel/samsung/i9082/patches/`):**
   - `0001-staging-android-binder-backport-multi-domain-scatter.patch`: soporte multi-dominio (`binder`, `hwbinder`, `vndbinder`) y transacciones *scatter-gather* (`BC_TRANSACTION_SG` / `BINDER_TYPE_PTR` / `BINDER_TYPE_FDA`), adaptado a la estructura `fd_set*` del kernel `i9082`.
   - `0002-ARM-configs-add-lineageos_i9082_pie_go_defconfig-for.patch`: `defconfig` con ZRAM LZ4, SELinux PolicyDB v30 (`POLICYDB_VERSION_XPERMS_IOCTL`), `CONFIG_ANDROID_RAM_CONSOLE=y`, `qtaguid`, `F2FS` y `cgroups`.
   - `0003-Makefile-add-fcommon-to-HOSTCFLAGS-for-GCC10.patch`: compatibilidad de `scripts/dtc` con compiladores modernos (GCC 10+).
   - `0004-staging-android-binder-compat-macros-for-linux-3.0.patch`: macros `SIZE_MAX` y `wait_event_freezable_exclusive` para Linux 3.0.

3. **Puente HIDL VINTF + Shims ABI para blobs de 2013:**
   - `device/samsung/i9082/manifest.xml` declara 17 servicios HIDL (Audio 2.0, Bluetooth 1.0, Camera Provider 2.4 `legacy/0`, GNSS 1.0, Graphics Allocator/Mapper 2.0 + Composer 2.1 vía `hwc2on1adapter`, Radio 1.0 `slot1`/`slot2`, Sensors, Wi-Fi, etc.).
   - `shims/capri_pie_shim.cpp` (`libcapri_pie_shim.so`) y `glgps-compat/glgps-compat.cpp` (`libglgps-compat.so`) para compatibilidad ABI con `rild`, `libbrcm_ril.so`, `camera.capri.so`, `libGLES_vc4.so` y `glgps`.
   - 101 blobs propietarios reales extraídos de un `GT-I9082L` en `vendor/samsung/i9082/proprietary/` (con auditoría `DT_NEEDED` de los 8 blobs críticos).

4. **Herramientas propias para macOS Apple Silicon y extracción (`tools/`):**
   - `tools/macos_usb_bridge.c` + `tools/samsung_odin_client.py`: cliente nativo Samsung Odin/Loke v2 sobre IOKit para Macs Apple Silicon que fragmenta las escrituras Bulk OUT en bloques de **64 bytes** (evitando el timeout del FIFO USB del `BCM28155` en controladores XHCI modernos).
   - `tools/extract_i9082l_blobs.py`: extractor de blobs propietarios vía ADB en TWRP.

---

## Estado actual del proyecto

- [x] Cliente Odin nativo en macOS Apple Silicon, volcado de tabla PIT real y flasheo de **TWRP 3.0.2-0**
- [x] Respaldo de particiones críticas (`efs`, `modem`, `KERNEL`, `VC-Firmware`, `PARAM`, `DTS`, etc.)
- [x] Extracción de blobs propietarios reales del `GT-I9082L` y auditoría de dependencias ELF (`DT_NEEDED`)
- [x] Árbol de dispositivo portado de `cm-14.1` a **LineageOS 16.0 (Android 9.0 Pie Go)**
- [x] Compilación limpia del kernel Linux `3.0.101` + `boot.img` (`bootimage` 100% verde en CI)
- [x] Pipeline de compilación gratuito en GitHub Actions con **Git LFS** habilitado para `chromium-webview`
- [ ] Compilación completa del paquete flasheable `bacon` (`.zip`) finalizada y auditada
- [ ] Bring-up físico del primer arranque (kernel, init/USB, VideoCore IV / SurfaceFlinger, RIL Dual-SIM, Wi-Fi/BT, Audio, Cámara, GPS)
- [ ] Endurecimiento de políticas SELinux (`permissive` → `enforcing` revisando cada `avc: denied`)

---

## Estructura del repositorio

```text
.
├── .github/workflows/
│   └── build_lineage16_i9082.yml   # Pipeline gratuito en GitHub Actions (bootimage / bacon)
├── build/
│   ├── Dockerfile.lineage16        # Entorno reproducible en Docker
│   ├── build_lineage16_i9082_go.sh # Script de compilación local
│   ├── lineage16_local_manifest.xml# Manifiesto local (kernel i9082, stlport, hardware/samsung)
│   └── COMPILAR_SIN_OTRO_PC.md     # Guía rápida de compilación en la nube
├── device/samsung/i9082/           # Device tree LineageOS 16.0 Pie Go (BoardConfig, HIDL, shims, overlays)
├── kernel/samsung/i9082/patches/   # 4 parches git format-patch para backportar Linux 3.0.101 a Pie
├── vendor/samsung/i9082/           # Blobs propietarios extraídos de GT-I9082L + makefiles
├── tools/                          # Cliente Odin nativo macOS (C/IOKit + Python) y extractor de blobs
└── tests/                          # Suite de pruebas unitarias (Odin + validaciones del árbol ROM)
```

---

## Cómo compilar

### Opción A: Gratis en la nube con GitHub Actions (recomendada)

No necesitas una PC con 16 GB de RAM ni 200 GB de disco libre:

1. Haz un **Fork** de este repositorio en tu cuenta de GitHub.
2. Ve a la pestaña **Actions** y habilita los workflows si GitHub lo solicita.
3. Selecciona **Build LineageOS 16.0 (Android 9.0 Pie Go) - GT-I9082L** → **Run workflow**.
4. Elige el objetivo:
   - `bootimage`: compila solo el kernel Linux `3.0.101` con los 4 parches + `boot.img` (~20 min).
   - `bacon`: compila la ROM completa `lineage-16.0-*-UNOFFICIAL-i9082.zip` (~3–3.5 horas).
5. Al terminar, descarga el paquete desde la sección **Artifacts** de la ejecución.

> El workflow libera automáticamente ~75–80 GB en el runner gratuito, sincroniza en dieta ARM32 (`-g default,-darwin,-mips,-notdefault --depth=1 --git-lfs`), descarga el `webview.apk` real desde el servidor LFS de LineageOS (`review.lineageos.org`) y verifica el APK con `zipinfo -t` antes de compilar.

### Opción B: Compilación local (Linux x86_64 / Docker)

Requiere Ubuntu 20.04/22.04 (o el `build/Dockerfile.lineage16`), `git-lfs`, ≥16 GB RAM (o swap) y ≥120 GB libres:

```bash
# Instalar git-lfs y preparar repo
git lfs install --skip-repo
repo init -u https://github.com/LineageOS/android.git \
  -b lineage-16.0 \
  -g default,-darwin,-mips,-notdefault \
  --depth=1 --no-clone-bundle --git-lfs

mkdir -p .repo/local_manifests
cp /ruta/al/repo/build/lineage16_local_manifest.xml .repo/local_manifests/i9082_pie_go.xml
repo sync -c --force-sync --no-clone-bundle --no-tags -j"$(nproc)"

# Copiar device/vendor y aplicar parches del kernel
cp -a /ruta/al/repo/device/samsung/i9082 device/samsung/i9082
cp -a /ruta/al/repo/vendor/samsung/i9082 vendor/samsung/i9082
(cd kernel/samsung/i9082 && for p in /ruta/al/repo/kernel/samsung/i9082/patches/*.patch; do git apply "$p"; done)

# Compilar
source build/envsetup.sh
lunch lineage_i9082-userdebug
mka bacon -j"$(nproc)"
```

---

## Pruebas automatizadas locales

Antes de subir cambios al árbol de dispositivo, parches del kernel o herramientas Odin, ejecuta la suite local:

```bash
python3 -m unittest discover -s tests -v
```

Verifica automáticamente:
- Framing del protocolo Samsung Odin v2 y parser de tabla PIT.
- Coincidencia de tamaños en `BoardConfig.mk` contra el PIT real del `GT-I9082L`.
- Integridad y existencia real (sensible a mayúsculas/minúsculas en Git) de los 101 blobs propietarios.
- Validez XML de `manifest.xml` y `lineage16_local_manifest.xml`, parches del kernel y protección de `out/` en `.gitignore`.

---

## Seguridad antes de flashear (obligatorio)

1. **Respalda tus particiones críticas en TWRP antes de flashear:** especialmente `efs` (`/dev/block/mmcblk0p17`, contiene tu IMEI), `modem` (`mmcblk0p7`), `KERNEL` (`mmcblk0p5`), `VC-Firmware` (`mmcblk0p15`), `PARAM` (`mmcblk0p11`) y `DTS` (`mmcblk0p13`).  
   *(El directorio `out/` está excluido en `.gitignore` para evitar subir respaldos privados o tu IMEI por accidente).*
2. **Audita el `.zip` antes de instalar:** revisa `META-INF/com/google/android/updater-script`, `update-binary` y scripts auxiliares para confirmar que solo escribe sobre `/boot` (`mmcblk0p5`) y `/system` (`mmcblk0p19`).
3. **Primer flasheo limpio sin GApps:** realiza *Wipe* de `System`, `Data`, `Cache` y `Dalvik/ART Cache` en TWRP 3.0.2-0 e instala únicamente el `.zip` de la ROM vía `adb sideload` para diagnosticar el primer arranque de forma aislada.
4. **Diagnóstico si hay bootloop:** recopila `adb logcat -b all -v threadtime`, `adb shell dmesg` o, desde TWRP, `/proc/last_kmsg` y `/data/tombstones/*`.

---

## Créditos y agradecimientos

- **LineageOS Team** por la base de LineageOS 16.0 (Android 9.0 Pie).
- **ghsr (`android_device_samsung_i9082` / `android_kernel_samsung_i9082`)** por el excelente trabajo histórico en `cm-14.1` y el kernel Linux `3.0.101` del Galaxy Grand Duos.
- **Mantenedores de `smdk4412` (LineageOS 16.0)** por el backport de referencia de `binder`/`hwbinder`/`vndbinder` en Linux `3.0.101`.
- **TeamWin (TWRP)** y la comunidad de desarrollo del Samsung Galaxy Grand Duos.

---

## Contribuciones

¡Issues, logs de arranque (`logcat` / `dmesg` / `last_kmsg`) y Pull Requests son bienvenidos! Si pruebas una compilación en un `GT-I9082` o `GT-I9082L`, comparte el modelo exacto, versión de TWRP y los registros obtenidos para acelerar el bring-up.
