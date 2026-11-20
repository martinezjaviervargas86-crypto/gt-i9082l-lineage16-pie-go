import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import samsung_odin_client as odin


class TestLineage16PieGoTree(unittest.TestCase):
    def test_vintf_and_local_manifests_valid_xml(self):
        vintf_path = PROJECT_ROOT / "device/samsung/i9082/manifest.xml"
        vintf_root = ET.parse(vintf_path).getroot()
        self.assertEqual(vintf_root.tag, "manifest")
        hal_names = {hal.findtext("name") for hal in vintf_root.findall("hal")}
        required_hals = {
            "android.hardware.audio",
            "android.hardware.bluetooth",
            "android.hardware.camera.provider",
            "android.hardware.gnss",
            "android.hardware.graphics.allocator",
            "android.hardware.graphics.composer",
            "android.hardware.graphics.mapper",
            "android.hardware.radio",
            "android.hardware.sensors",
            "android.hardware.wifi",
        }
        self.assertTrue(required_hals.issubset(hal_names), f"Faltan HALs: {required_hals - hal_names}")

        local_manifest = PROJECT_ROOT / "build/lineage16_local_manifest.xml"
        lm_root = ET.parse(local_manifest).getroot()
        self.assertEqual(lm_root.tag, "manifest")
        self.assertGreaterEqual(len(lm_root.findall("project")), 4)

    def test_extracted_vendor_blobs_exist_and_nonempty(self):
        vendor_mk = (PROJECT_ROOT / "vendor/samsung/i9082/i9082-vendor.mk").read_text(encoding="utf-8")
        refs = re.findall(r"\$\(LOCAL_PATH\)/(proprietary/[^\s:\\]+):", vendor_mk)
        self.assertGreaterEqual(len(refs), 100, "Se esperaban >= 100 blobs extraídos del GT-I9082L")
        for rel in refs:
            p = PROJECT_ROOT / "vendor/samsung/i9082" / rel
            self.assertTrue(p.exists(), f"Falta blob: {p}")
            self.assertGreater(p.stat().st_size, 0, f"Blob vacío: {p}")

    def test_board_config_sizes_fit_real_device_pit(self):
        pit_bytes = (PROJECT_ROOT / "out/gt_i9082l.pit").read_bytes()
        pit_map = {e.partition_name: e.block_count * 512 for e in odin.parse_pit(pit_bytes)}

        bc = (PROJECT_ROOT / "device/samsung/i9082/BoardConfig.mk").read_text(encoding="utf-8")
        def get_mk_int(name: str) -> int:
            m = re.search(rf"^{name}\s*:=\s*(\d+)", bc, re.MULTILINE)
            self.assertIsNotNone(m, f"No se encontró {name} en BoardConfig.mk")
            return int(m.group(1))

        self.assertLessEqual(get_mk_int("BOARD_BOOTIMAGE_PARTITION_SIZE"), pit_map["KERNEL"])
        self.assertLessEqual(get_mk_int("BOARD_RECOVERYIMAGE_PARTITION_SIZE"), pit_map["RECOVERY"])
        self.assertLessEqual(get_mk_int("BOARD_SYSTEMIMAGE_PARTITION_SIZE"), pit_map["system"])
        self.assertLessEqual(get_mk_int("BOARD_CACHEIMAGE_PARTITION_SIZE"), pit_map["CSC"])

    def test_critical_backups_present(self):
        bdir = PROJECT_ROOT / "out/backups/i9082l_backup"
        for name in ("efs.img", "KERNEL.img", "modem.img", "VC-Firmware.img", "PARAM.img", "DTS.img"):
            p = bdir / name
            self.assertTrue(p.exists(), f"Falta respaldo crítico: {p}")
            self.assertGreater(p.stat().st_size, 0, f"Respaldo vacío: {p}")

    def test_pie_go_optimizations_configured(self):
        props = (PROJECT_ROOT / "device/samsung/i9082/system_prop.mk").read_text(encoding="utf-8")
        self.assertIn("ro.config.low_ram=true", props)
        self.assertIn("debug.hwui.renderer=opengl", props)
        self.assertIn("ro.lmk.use_psi=false", props)
        self.assertIn("persist.radio.multisim.config=dsds", props)

        fstab = (PROJECT_ROOT / "device/samsung/i9082/rootdir/fstab.capri").read_text(encoding="utf-8")
        self.assertIn("zramsize=536870912", fstab)

        init_rc = (PROJECT_ROOT / "device/samsung/i9082/rootdir/init.capri.rc").read_text(encoding="utf-8")
        self.assertIn("swapon_all /fstab.capri", init_rc)

    def test_kernel_pie_patches_valid(self):
        pdir = PROJECT_ROOT / "kernel/samsung/i9082/patches"
        p1 = sorted(pdir.glob("0001-*.patch"))
        p2 = sorted(pdir.glob("0002-*.patch"))
        self.assertEqual(len(p1), 1, "Falta parche 0001 de binder multi-domain")
        self.assertEqual(len(p2), 1, "Falta parche 0002 de defconfig Pie Go")

        binder_patch = p1[0].read_text(encoding="utf-8", errors="ignore")
        for sym in (
            "CONFIG_ANDROID_BINDER_DEVICES",
            "BC_TRANSACTION_SG",
            "BC_REPLY_SG",
            "BINDER_TYPE_PTR",
            "BINDER_TYPE_FDA",
            "fdt->open_fds->fds_bits",
        ):
            self.assertIn(sym, binder_patch, f"Falta {sym} en parche 0001")

        defcfg_patch = p2[0].read_text(encoding="utf-8", errors="ignore")
        self.assertIn('CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"', defcfg_patch)
        self.assertIn("CONFIG_ZRAM_LZ4_COMPRESS=y", defcfg_patch)
        self.assertIn("CONFIG_IP6_NF_MATCH_RPFILTER=y", defcfg_patch)

    def test_github_actions_workflow_and_gitignore_protect_efs(self):
        gi = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("out/", gi)

        wf = PROJECT_ROOT / ".github/workflows/build_lineage16_i9082.yml"
        self.assertTrue(wf.exists(), "Falta workflow de GitHub Actions")
        wf_text = wf.read_text(encoding="utf-8")
        self.assertIn("-g default,-darwin,-mips,-notdefault", wf_text)
        self.assertIn("rm -rf .repo", wf_text)
        self.assertIn("lunch lineage_i9082-userdebug", wf_text)


if __name__ == "__main__":
    unittest.main()
