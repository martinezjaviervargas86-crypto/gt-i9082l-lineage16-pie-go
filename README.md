# LineageOS 16.0 (Android 9.0 Pie Go) — Samsung Galaxy Grand Duos (`GT-I9082L` / `GT-I9082`)

[![Build LineageOS 16.0 (Android 9.0 Pie Go) - GT-I9082L](https://github.com/martinezjaviervargas86-crypto/gt-i9082l-lineage16-pie-go/actions/workflows/build_lineage16_i9082.yml/badge.svg)](https://github.com/martinezjaviervargas86-crypto/gt-i9082l-lineage16-pie-go/actions/workflows/build_lineage16_i9082.yml)

> **🧪 ESTADO ACTUAL — ALFA FUNCIONAL (ARRANQUE VERIFICADO EN HARDWARE REAL `GT-I9082L`):**  
> Esta ROM **ya arranca hasta el escritorio de LineageOS 16.0 (Android 9.0 Pie Go)** en un **Samsung Galaxy Grand Duos `GT-I9082L`** físico con aceleración gráfica **VideoCore IV OpenGL ES 2.0**, 512 MB de ZRAM y táctil/brillo operativos.  
> Actualmente se encuentra en **Fase 2 de estabilización** (validando Wi-Fi, Audio, Bluetooth, Sensores, Cámara, almacenamiento `/sdcard` por FUSE y suspensión/despertar). **Haz siempre respaldo de `EFS` y `modem` antes de probar.**

### Estado de funciones (pruebas en `GT-I9082L` físico)
- ✅ **Arranque completo a Android 9.0 Pie Go (`sys.boot_completed=1`)**
- ✅ **Pantalla, táctil, brillo, panel de notificaciones y GPU VideoCore IV (OpenGL ES 2.0)**
- ✅ **512 MB ZRAM (LZ4) y perfil Android Go 1 GB RAM**
- 🔄 **En validación (Fase 2):** Wi-Fi (`dhd.ko`), Audio (`audio.primary.capri.so`), Bluetooth (`BCM4334`), Sensores (wrapper HAL 1.3), almacenamiento interno (`/sdcard` FUSE), Cámara, suspensión/despertar y Dual-SIM (`rild`)

---

## Hardware compatible

| Característica | Especificación (`GT-I9082L`) |
| --- | --- |
| **Modelo / Código** | `GT-I9082L` (`baffin` / `baffinvj` / `i9082`, `CAPRI_SS_BAFFIN`) |
| **Procesador (SoC)** | Broadcom `BCM28155` Dual-Core ARM Cortex-A9 @ 1.2 GHz (`armeabi-v7a`) |
| **Gráficos (GPU)** | Broadcom VideoCore IV (OpenGL ES 2.0) |
| **Memoria RAM** | 1 GB (`832 MB` utilizables + `512 MB` de memoria comprimida ZRAM) |
| **Almacenamiento interno** | 8 GB eMMC (`system`: 1.5 GB, `userdata`: ~4.1 GB) |
| **Conectividad** | Dual-SIM, Wi-Fi/Bluetooth Broadcom `BCM4334`, GPS integrado |

---

## Qué incluye esta versión

Esta ROM fue diseñada específicamente para sacar el máximo provecho a un teléfono de 2013 con 1 GB de RAM sin sacrificar estabilidad:

- **Android 9.0 Pie — Edición Go:** perfil ligero oficial para dispositivos de baja memoria, con gestión optimizada de procesos en segundo plano y **512 MB de ZRAM (LZ4)** que amplían la capacidad multitarea.
- **Kernel Linux `3.0.101` modernizado:** adaptado con soporte para las comunicaciones modernas de Android 9, ahorro de memoria y diagnóstico de arranque integrado.
- **Compatibilidad con hardware original:** puente moderno hacia los controladores propietarios del Grand Duos (pantalla/GPU VideoCore IV, audio, cámaras, Dual-SIM, Wi-Fi, Bluetooth, sensores y GPS).
- **Sistema liviano:** optimizado para caber con margen dentro de la partición `/system` original de 1.5 GB del dispositivo.

---

## Hito destacado: Protocolo Odin nativo para macOS (Apple Silicon)

Uno de los mayores logros de este proyecto es la implementación de un **cliente nativo del protocolo Samsung Odin v2 para macOS (Apple Silicon M1/M2/M3/M4)** sin depender de Windows, máquinas virtuales ni herramientas obsoletas:

- Permite comunicarse directamente por USB en **Modo Download** con el bootloader del `GT-I9082L`.
- Resuelve la limitación de hardware del controlador USB del procesador Broadcom `BCM28155` en Macs modernos (donde los envíos mayores a 64 bytes bloqueaban la transferencia).
- Capaz de **leer la tabla de particiones PIT real del equipo** y **flashear particiones críticas como TWRP Recovery** de forma rápida y segura directamente desde macOS.

---

## Guía de instalación y seguridad (obligatorio)

Antes de probar cualquier paquete en tu teléfono, sigue estas precauciones al pie de la letra:

### 1. Respaldos obligatorios antes de empezar
Desde **TWRP Recovery (3.0.2-0)**, guarda una copia segura en tu PC o tarjeta microSD de las particiones críticas de tu equipo:
- **`EFS`** (`/dev/block/mmcblk0p17`): contiene tu **IMEI** y datos únicos de red. **Nunca la compartas públicamente ni la pierdas.**
- **`modem`** (`/dev/block/mmcblk0p7`): banda base y telefonía móvil.
- **`KERNEL`**, **`VC-Firmware`**, **`PARAM`** y **`DTS`**: necesarias para volver al sistema de fábrica en cualquier momento.

### 2. Instalación limpia recomendada
1. Verifica que el paquete corresponda a la familia `GT-I9082` / `GT-I9082L` (`baffin`) y que solo modifique `/boot` y `/system`.
2. Inicia el teléfono en **TWRP 3.0.2-0**.
3. Realiza **Wipe** (limpieza) de `System`, `Data`, `Cache` y `Dalvik / ART Cache`.
4. Instala el archivo `.zip` de la ROM (por tarjeta microSD o `adb sideload`).
5. **Primer arranque sin GApps:** arranca primero únicamente con la ROM limpia para verificar estabilidad antes de instalar paquetes adicionales.

### 3. Si encuentras algún fallo o reinicio
Si el equipo no termina de iniciar o falla alguna función, puedes ayudar al proyecto compartiendo registros desde tu PC:
- Con el sistema arrancado (ADB): `adb logcat -b all -v threadtime` y `adb shell dmesg`.
- Desde TWRP (si no llegó a iniciar): copia de `/proc/last_kmsg` y `/data/tombstones/`.

---

## Créditos y agradecimientos

- **bambij1** — Creador del proyecto, pruebas reales sobre hardware físico `GT-I9082L`, validación de seguridad y dirección general.
- **Antigravity (Google DeepMind)** — Co-desarrollo del port a Android 9.0 Pie Go, adaptación del kernel Linux `3.0.101`, puente HIDL e implementación del cliente Odin nativo para macOS Apple Silicon.
- **LineageOS Team** — Por la base de LineageOS 16.0 (Android 9.0 Pie).
- **ghsr** — Por su trabajo previo en el árbol de dispositivo y kernel del Samsung Galaxy Grand Duos (`i9082`).
- **Mantenedores de `smdk4412`** — Por la referencia de backport de binder para Linux `3.0.101`.
- **TeamWin (TWRP)** y toda la comunidad de entusiastas del Samsung Galaxy Grand Duos.

---

## Participa con la comunidad

Si pruebas esta guía en un `GT-I9082` o `GT-I9082L`, abre un **Issue** indicando tu modelo exacto, versión de TWRP y tus comentarios o logs. ¡Toda experiencia ayuda a mantener vivo a este clásico!
