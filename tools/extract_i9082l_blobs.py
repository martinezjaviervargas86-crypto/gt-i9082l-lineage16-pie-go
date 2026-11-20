#!/usr/bin/env python3
"""
Extracts proprietary blobs listed in device/samsung/i9082/proprietary-files.txt
from a connected GT-I9082L running TWRP (with /system mounted read-only),
and generates LineageOS 16.0 vendor makefiles under vendor/samsung/i9082/.
"""

import subprocess
import sys
from pathlib import Path

ADB_BIN = "/Users/javier/Library/Android/sdk/platform-tools/adb"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROP_LIST = PROJECT_ROOT / "device/samsung/i9082/proprietary-files.txt"
VENDOR_DIR = PROJECT_ROOT / "vendor/samsung/i9082"
PROP_OUT = VENDOR_DIR / "proprietary"


def load_blob_list() -> list[str]:
    blobs: list[str] = []
    for raw in PROP_LIST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        blobs.append(line.lstrip("/"))
    return blobs


def generate_vendor_makefiles(present_blobs: list[str]) -> None:
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)

    (VENDOR_DIR / "BoardConfigVendor.mk").write_text(
        "# Automatically generated from physical GT-I9082L (baffinvj) stock blobs\n"
        "# LineageOS 16.0 (Android 9.0 Pie Go) vendor board configuration\n",
        encoding="utf-8",
    )

    lines = [
        "# Automatically generated from physical GT-I9082L (baffinvj) stock blobs",
        "# Target: LineageOS 16.0 (Android 9.0 Pie - Android Go)",
        "",
        "LOCAL_PATH := vendor/samsung/i9082",
        "",
        "PRODUCT_COPY_FILES += \\",
    ]
    for i, rel in enumerate(sorted(present_blobs)):
        suffix = " \\" if i < len(present_blobs) - 1 else ""
        dest = f"system/{rel}"
        lines.append(f"    $(LOCAL_PATH)/proprietary/{rel}:{dest}{suffix}")
    lines.append("")
    (VENDOR_DIR / "i9082-vendor.mk").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    blobs = load_blob_list()
    print(f"[*] Verificando {len(blobs)} entradas de {PROP_LIST.name} en /system...", flush=True)

    file_args = " ".join(blobs)
    check_cmd = f"cd /system && for f in {file_args}; do if [ -e \"$f\" ]; then echo FOUND:$f; fi; done"
    res = subprocess.run([ADB_BIN, "shell", check_cmd], check=True, text=True, capture_output=True)
    found = [
        line.split("FOUND:", 1)[1].strip()
        for line in res.stdout.splitlines()
        if line.startswith("FOUND:")
    ]
    print(f"[*] Encontrados {len(found)}/{len(blobs)} blobs en el GT-I9082L. Extrayendo...", flush=True)

    extracted: list[str] = []
    for idx, rel in enumerate(found, 1):
        dst = PROP_OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(
            [ADB_BIN, "pull", f"/system/{rel}", str(dst)],
            text=True,
            capture_output=True,
        )
        if r.returncode == 0:
            extracted.append(rel)
        else:
            print(f"[!] Falló pull de {rel}: {r.stderr.strip()}", flush=True)
        if idx % 20 == 0 or idx == len(found):
            print(f"    -> [{idx}/{len(found)}] extraídos", flush=True)

    missing = sorted(set(blobs) - set(extracted))
    generate_vendor_makefiles(extracted)

    print(f"[+] Blobs extraídos del GT-I9082L: {len(extracted)}/{len(blobs)}", flush=True)
    if missing:
        print(f"[!] No presentes en stock 4.2.2 ({len(missing)}):", flush=True)
        for m in missing:
            print(f"    - {m}", flush=True)
    print(f"[+] Makefiles generados en: {VENDOR_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
