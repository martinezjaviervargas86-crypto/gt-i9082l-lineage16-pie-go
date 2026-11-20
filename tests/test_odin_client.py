import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import samsung_odin_client as odin


class FakeOdinTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.writes = []

    def write_all(self, data: bytes, timeout: float = 10.0) -> None:
        self.writes.append(data)

    def read_transfer(self, max_len: int = 512, timeout: float = 5.0) -> bytes:
        if not self.responses:
            raise TimeoutError("Sin respuestas simuladas")
        return self.responses.pop(0)

    def read_exact(self, length: int, timeout: float = 5.0) -> bytes:
        data = self.read_transfer(length, timeout=timeout)
        if len(data) != length:
            raise AssertionError(f"Esperados {length} bytes, recibidos {len(data)}")
        return data


def make_pit_bytes(entries):
    buf = bytearray(odin.PIT_HEADER_SIZE)
    struct.pack_into("<II", buf, 0, odin.PIT_MAGIC, len(entries))
    for part_id, dev_type, blocks, pname, fname in entries:
        entry = bytearray(odin.PIT_ENTRY_SIZE)
        struct.pack_into("<9I", entry, 0, 0, dev_type, part_id, 0, 0, 0, blocks, 0, 0)
        entry[36 : 36 + len(pname)] = pname.encode("utf-8")
        entry[68 : 68 + len(fname)] = fname.encode("utf-8")
        buf.extend(entry)
    return bytes(buf)


class TestSamsungOdinClient(unittest.TestCase):
    def test_parse_pit(self):
        raw = make_pit_bytes(
            [
                (5, 2, 16384, "KERNEL", "boot.img"),
                (6, 2, 16384, "RECOVERY", "recovery.img"),
            ]
        )
        entries = odin.parse_pit(raw)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].partition_name, "KERNEL")
        self.assertEqual(entries[1].partition_name, "RECOVERY")
        self.assertEqual(entries[1].part_id, 6)
        self.assertEqual(entries[1].device_type, 2)
        self.assertEqual(entries[1].block_count, 16384)

    def test_handshake_session_and_dump_pit(self):
        pit_raw = make_pit_bytes([(6, 2, 16384, "RECOVERY", "recovery.img")])
        # Simulate padded 500-byte PIT part transfer from bootloader
        pit_part_padded = pit_raw + b"\x00" * (500 - len(pit_raw))
        tx = FakeOdinTransport(
            [
                b"LOKE",
                struct.pack("<II", odin.REQ_SESSION, 0x00020000),
                struct.pack("<II", odin.REQ_PIT, len(pit_raw)),
                pit_part_padded,
                struct.pack("<II", odin.REQ_PIT, 0),
                struct.pack("<II", odin.REQ_END_SESSION, 0),
            ]
        )
        client = odin.OdinClient(tx)
        client.handshake()
        proto = client.begin_session()
        self.assertEqual(proto, 0x00020000)
        self.assertEqual(client.protocol_version, 2)
        dumped = client.dump_pit()
        self.assertEqual(dumped, pit_raw)
        client.end_session(reboot=False)

        self.assertEqual(tx.writes[0], b"ODIN")
        self.assertEqual(len(tx.writes[1]), 1024)
        self.assertEqual(struct.unpack_from("<II", tx.writes[1], 0), (odin.REQ_SESSION, odin.SESSION_BEGIN))

    def test_flash_partition_framing(self):
        entry = odin.PitEntry(0, 2, 6, 0, 0, 0, 16384, 0, 0, "RECOVERY", "recovery.img", "")
        payload = b"ANDROID!" + b"\xAB" * 1000
        tx = FakeOdinTransport(
            [
                struct.pack("<II", odin.REQ_SESSION, 0),  # SetTotalBytes
                struct.pack("<II", odin.REQ_FILE_TRANSFER, 0),  # XFER_FLASH
                struct.pack("<II", odin.REQ_FILE_TRANSFER, 0),  # XFER_PART header
                struct.pack("<II", odin.RESP_SEND_FILE_PART, 0),  # Part 0 ack
                struct.pack("<II", odin.REQ_FILE_TRANSFER, 0),  # XFER_END
            ]
        )
        client = odin.OdinClient(tx)
        client.file_part_size = 131072
        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "twrp.img"
            img.write_bytes(payload)
            client.flash_partition(entry, img)

        # Verify SetTotalBytes, XFER_FLASH, XFER_PART header, padded part data, XFER_END
        self.assertEqual(len(tx.writes), 5)
        self.assertEqual(
            struct.unpack_from("<III", tx.writes[0], 0),
            (odin.REQ_SESSION, odin.SESSION_TOTAL_BYTES, len(payload)),
        )
        self.assertEqual(len(tx.writes[3]), 131072)
        self.assertTrue(tx.writes[3].startswith(payload))
        self.assertEqual(
            struct.unpack_from("<8I", tx.writes[4], 0),
            (odin.REQ_FILE_TRANSFER, odin.XFER_END, 0, len(payload), 0, 2, 6, 1),
        )


if __name__ == "__main__":
    unittest.main()
