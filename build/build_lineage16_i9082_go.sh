#!/usr/bin/env bash
#
# Automated Linux x86_64 Build Script for LineageOS 16.0 (Android 9.0 Pie - Android Go)
# Target: Samsung Galaxy Grand Duos (GT-I9082L / baffin / Broadcom BCM28155)
#
# Requirements on build host (Linux PC, VPS, or Docker container):
#   - Ubuntu 18.04 / 20.04 / 22.04 x86_64
#   - >= 16 GB RAM (or 8 GB RAM + 16 GB swap)
#   - >= 140 GB free disk space
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOS_DIR="${LOS_DIR:-$HOME/lineage-16.0}"
JOBS="${JOBS:-$(nproc)}"

echo "=== [1/5] Inicializando LineageOS 16.0 en $LOS_DIR ==="
mkdir -p "$LOS_DIR/.repo/local_manifests"
cd "$LOS_DIR"

if [ ! -d ".repo/manifests" ]; then
    repo init -u https://github.com/LineageOS/android.git -b lineage-16.0 --depth=1
fi

cp "$PROJECT_DIR/build/lineage16_local_manifest.xml" "$LOS_DIR/.repo/local_manifests/i9082_pie_go.xml"

echo "=== [2/5] Sincronizando fuentes (esto puede tomar 20-45 min la primera vez) ==="
repo sync -c --force-sync --no-clone-bundle --no-tags -j"$JOBS"

echo "=== [3/5] Instalando device tree y blobs extraídos de tu GT-I9082L ==="
rm -rf "$LOS_DIR/device/samsung/i9082" "$LOS_DIR/vendor/samsung/i9082"
mkdir -p "$LOS_DIR/device/samsung" "$LOS_DIR/vendor/samsung"
cp -a "$PROJECT_DIR/device/samsung/i9082" "$LOS_DIR/device/samsung/i9082"
cp -a "$PROJECT_DIR/vendor/samsung/i9082" "$LOS_DIR/vendor/samsung/i9082"

echo "=== [4/5] Aplicando parches Android 9.0 Pie Go al kernel Linux 3.0.101 ==="
cd "$LOS_DIR/kernel/samsung/i9082"
if [ ! -f "arch/arm/configs/lineageos_i9082_pie_go_defconfig" ]; then
    git apply "$PROJECT_DIR"/kernel/samsung/i9082/patches/0001-*.patch
    git apply "$PROJECT_DIR"/kernel/samsung/i9082/patches/0002-*.patch
fi
cd "$LOS_DIR"

echo "=== [5/5] Compilando LineageOS 16.0 (Android 9.0 Pie Go) para GT-I9082L ==="
export USE_CCACHE=1
export CCACHE_EXEC="$(which ccache || true)"
export LC_ALL=C

set +u
source build/envsetup.sh
lunch lineage_i9082-userdebug
mka bacon -j"$JOBS"
set -u

echo ""
echo "[+] ¡Compilación completada! Tu ROM flasheable por TWRP está en:"
ls -lh "$LOS_DIR"/out/target/product/i9082/lineage-16.0-*.zip
