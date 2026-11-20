#!/usr/bin/env python3
"""
Pure-Python Samsung Odin / Loke Protocol Client for macOS.
Target Device: Samsung Galaxy Grand Duos (GT-I9082L / baffin / Broadcom BCM28155)

Supports:
- ODIN -> LOKE handshake over /dev/cu.usbmodem* (or IOKit USB Bulk 0x04e8:0x685d)
- PIT table download & binary parser (--dump-pit)
- Direct partition flashing (e.g. RECOVERY / KERNEL / SYSTEM) using PIT IDs (--flash <PART_NAME> <IMAGE_PATH>)
- Clean reboot (--reboot)
"""

import argparse
import ctypes
import glob
import os
import select
import struct
import sys
import termios
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


SAMSUNG_VID = 0x04E8
SAMSUNG_ODIN_PID = 0x685D
PIT_MAGIC = 0x12349876
PIT_HEADER_SIZE = 28
PIT_ENTRY_SIZE = 132

# Odin/Loke Protocol Request / Response Types
RESP_SEND_FILE_PART = 0x00
REQ_SESSION = 0x64
REQ_PIT = 0x65
REQ_FILE_TRANSFER = 0x66
REQ_END_SESSION = 0x67

# Session subcommands
SESSION_BEGIN = 0x00
SESSION_DEVICE_TYPE = 0x01
SESSION_TOTAL_BYTES = 0x02
SESSION_FILE_PART_SIZE = 0x05

# PIT subcommands
PIT_GET_SIZE = 0x01
PIT_DUMP_PART = 0x02
PIT_END_TRANSFER = 0x03

# File Transfer subcommands
XFER_FLASH = 0x00
XFER_DUMP = 0x01
XFER_PART = 0x02
XFER_END = 0x03

# End Session subcommands
END_SESSION_ONLY = 0x00
END_SESSION_REBOOT = 0x01


@dataclass
class PitEntry:
    binary_type: int
    device_type: int
    part_id: int
    attributes: int
    update_attributes: int
    block_size_or_offset: int
    block_count: int
    file_offset: int
    file_size: int
    partition_name: str
    flash_filename: str
    fota_filename: str


def parse_pit(data: bytes) -> List[PitEntry]:
    """Parses a Samsung binary PIT table (magic 0x12349876)."""
    if len(data) < PIT_HEADER_SIZE:
        raise ValueError(f"Tabla PIT demasiado corta ({len(data)} bytes)")
    magic, count = struct.unpack_from("<II", data, 0)
    if magic != PIT_MAGIC:
        raise ValueError(f"Magic PIT inválido: 0x{magic:08x} (esperado 0x{PIT_MAGIC:08x})")

    entries: List[PitEntry] = []
    pos = PIT_HEADER_SIZE
    for _ in range(count):
        if pos + PIT_ENTRY_SIZE > len(data):
            break
        fields = struct.unpack_from("<9I", data, pos)
        pname = data[pos + 36 : pos + 68].split(b"\x00", 1)[0].decode("utf-8", errors="replace").strip()
        fname = data[pos + 68 : pos + 100].split(b"\x00", 1)[0].decode("utf-8", errors="replace").strip()
        fota = data[pos + 100 : pos + 132].split(b"\x00", 1)[0].decode("utf-8", errors="replace").strip()
        entries.append(
            PitEntry(
                binary_type=fields[0],
                device_type=fields[1],
                part_id=fields[2],
                attributes=fields[3],
                update_attributes=fields[4],
                block_size_or_offset=fields[5],
                block_count=fields[6],
                file_offset=fields[7],
                file_size=fields[8],
                partition_name=pname,
                flash_filename=fname,
                fota_filename=fota,
            )
        )
        pos += PIT_ENTRY_SIZE
    return entries


def find_samsung_serial_port() -> Optional[str]:
    candidates = sorted(glob.glob("/dev/cu.usbmodem*"))
    return candidates[0] if candidates else None


class OdinSerialTransport:
    """Raw 8N1 POSIX serial transport over macOS /dev/cu.usbmodem*."""

    def __init__(self, port_path: str):
        self.port_path = port_path
        self.fd: Optional[int] = None

    def open(self) -> None:
        fd = os.open(self.port_path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[3] = 0
        attrs[4] = termios.B115200
        attrs[5] = termios.B115200
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        termios.tcflush(fd, termios.TCIOFLUSH)
        self.fd = fd

    def close(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def write_all(self, data: bytes, timeout: float = 10.0) -> None:
        if self.fd is None:
            raise RuntimeError("Puerto Odin no abierto")
        view = memoryview(data)
        sent = 0
        deadline = time.time() + timeout
        while sent < len(data):
            rem = max(0.05, deadline - time.time())
            if rem <= 0:
                raise TimeoutError(f"Timeout escribiendo {len(data)} bytes a Odin (enviados {sent})")
            _, wlist, _ = select.select([], [self.fd], [], rem)
            if not wlist:
                continue
            n = os.write(self.fd, view[sent : sent + 16384])
            if n > 0:
                sent += n

    def read_exact(self, length: int, timeout: float = 5.0) -> bytes:
        if self.fd is None:
            raise RuntimeError("Puerto Odin no abierto")
        buf = bytearray()
        deadline = time.time() + timeout
        while len(buf) < length:
            rem = deadline - time.time()
            if rem <= 0:
                raise TimeoutError(
                    f"Timeout leyendo {length} bytes de Odin (recibidos {len(buf)}: {bytes(buf)!r})"
                )
            rlist, _, _ = select.select([self.fd], [], [], min(0.5, rem))
            if not rlist:
                continue
            chunk = os.read(self.fd, length - len(buf))
            if chunk:
                buf.extend(chunk)
        return bytes(buf)


class OdinIOKitUsbTransport:
    """Native macOS IOKit USB Bulk transport via libmacos_usb.dylib (0x04e8:0x685d, Interface #1)."""

    def __init__(
        self,
        vid: int = SAMSUNG_VID,
        pid: int = SAMSUNG_ODIN_PID,
        intf: int = 1,
        write_chunk_size: int = 64,
    ):
        self.vid = vid
        self.pid = pid
        self.intf = intf
        self.write_chunk_size = write_chunk_size
        self._rx_buf = bytearray()
        dylib_path = Path(__file__).resolve().parent / "libmacos_usb.dylib"
        if not dylib_path.exists():
            raise FileNotFoundError(f"No existe {dylib_path}")
        self.lib = ctypes.CDLL(str(dylib_path))
        self.lib.usb_open_device.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.lib.usb_open_device.restype = ctypes.c_int
        self.lib.usb_write_bulk_chunked.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.lib.usb_write_bulk_chunked.restype = ctypes.c_int
        self.lib.usb_read_bulk.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        self.lib.usb_read_bulk.restype = ctypes.c_int
        self.lib.usb_close_device.argtypes = []
        self.lib.usb_close_device.restype = None

    def open(self) -> None:
        self._rx_buf.clear()
        rc = self.lib.usb_open_device(self.vid, self.pid, self.intf)
        if rc != 0:
            raise RuntimeError(
                f"No se pudo abrir Samsung Odin USB (0x{self.vid:04x}:0x{self.pid:04x}, intf={self.intf}): rc={rc}"
            )

    def close(self) -> None:
        self._rx_buf.clear()
        self.lib.usb_close_device()

    def write_all(self, data: bytes, timeout: float = 10.0) -> None:
        timeout_ms = int(timeout * 1000)
        rc = self.lib.usb_write_bulk_chunked(data, len(data), self.write_chunk_size, timeout_ms)
        if rc < 0:
            raise RuntimeError(f"Error escribiendo bulk Odin ({len(data)} bytes): rc={rc}")

    def read_transfer(self, max_len: int = 512, timeout: float = 5.0) -> bytes:
        """Reads a single USB Bulk IN transfer (up to max_len, aligned to endpoint MPS)."""
        rx_len = max(512, max_len)
        rx = ctypes.create_string_buffer(rx_len)
        deadline = time.time() + timeout
        while True:
            rem = deadline - time.time()
            if rem <= 0:
                raise TimeoutError(f"Timeout leyendo transferencia USB Bulk Odin (max={max_len})")
            rc = self.lib.usb_read_bulk(rx, rx_len, min(2000, int(max(0.1, rem) * 1000)))
            if rc > 0:
                return bytes(rx.raw[:rc])

    def read_exact(self, length: int, timeout: float = 5.0) -> bytes:
        deadline = time.time() + timeout
        while len(self._rx_buf) < length:
            rem = deadline - time.time()
            if rem <= 0:
                raise TimeoutError(
                    f"Timeout leyendo {length} bytes USB Bulk Odin (recibidos {len(self._rx_buf)}: {bytes(self._rx_buf)!r})"
                )
            chunk = self.read_transfer(max(512, length - len(self._rx_buf)), timeout=rem)
            self._rx_buf.extend(chunk)
        out = bytes(self._rx_buf[:length])
        del self._rx_buf[:length]
        return out


class OdinClient:
    """Implements Samsung Odin / Loke protocol v2 & v3."""

    def __init__(self, transport):
        self.tx = transport
        self.protocol_version = 2
        self.file_part_size = 131072  # 128 KiB (Heimdall kFileTransferPacketSizeDefault)
        self.parts_per_sequence = 240  # 30 MiB per sequence (240 * 128 KiB = 30 MiB, Odin v2)

    def _send_packet_1024(self, *ints: int) -> None:
        pkt = bytearray(1024)
        for i, val in enumerate(ints):
            struct.pack_into("<I", pkt, i * 4, val & 0xFFFFFFFF)
        self.tx.write_all(bytes(pkt))

    def _recv_response_8(self, timeout: float = 10.0) -> Tuple[int, int]:
        raw = self.tx.read_exact(8, timeout=timeout)
        return struct.unpack("<II", raw)

    def handshake(self) -> None:
        self.tx.write_all(b"ODIN")
        resp = self.tx.read_exact(4, timeout=5.0)
        if resp != b"LOKE":
            raise RuntimeError(f"Handshake ODIN falló: respuesta={resp!r} (esperado b'LOKE')")

    def begin_session(self) -> int:
        self._send_packet_1024(REQ_SESSION, SESSION_BEGIN)
        resp_id, proto_ver = self._recv_response_8()
        if resp_id != REQ_SESSION:
            raise RuntimeError(f"BeginSession falló: resp_id=0x{resp_id:x}, val=0x{proto_ver:x}")
        self.protocol_version = (proto_ver >> 16) & 0xFFFF
        if self.protocol_version == 0:
            self.protocol_version = proto_ver
        return proto_ver

    def set_file_part_size(self, part_size: int = 131072) -> None:
        self.file_part_size = part_size
        self._send_packet_1024(REQ_SESSION, SESSION_FILE_PART_SIZE, part_size)
        resp_id, val = self._recv_response_8()
        if resp_id != REQ_SESSION:
            raise RuntimeError(f"SetFilePartSize falló: resp_id=0x{resp_id:x}, val=0x{val:x}")

    def set_total_bytes(self, total_bytes: int) -> None:
        self._send_packet_1024(REQ_SESSION, SESSION_TOTAL_BYTES, total_bytes)
        resp_id, val = self._recv_response_8()
        if resp_id != REQ_SESSION:
            raise RuntimeError(f"SetTotalBytes falló: resp_id=0x{resp_id:x}, val=0x{val:x}")

    def dump_pit(self) -> bytes:
        self._send_packet_1024(REQ_PIT, PIT_GET_SIZE)
        resp_id, pit_size = self._recv_response_8()
        if resp_id != REQ_PIT or pit_size == 0 or pit_size > 1024 * 1024:
            raise RuntimeError(f"GetPITSize falló: resp_id=0x{resp_id:x}, pit_size={pit_size}")

        pit_buf = bytearray()
        part_idx = 0
        while len(pit_buf) < pit_size:
            self._send_packet_1024(REQ_PIT, PIT_DUMP_PART, part_idx)
            remaining = pit_size - len(pit_buf)
            if hasattr(self.tx, "read_transfer"):
                chunk = self.tx.read_transfer(512, timeout=5.0)
                pit_buf.extend(chunk[: min(len(chunk), remaining)])
            else:
                chunk_len = min(500, remaining)
                chunk = self.tx.read_exact(chunk_len, timeout=5.0)
                pit_buf.extend(chunk)
            part_idx += 1

        self._send_packet_1024(REQ_PIT, PIT_END_TRANSFER)
        resp_id, _ = self._recv_response_8()
        if resp_id != REQ_PIT:
            raise RuntimeError(f"EndPITTransfer falló: resp_id=0x{resp_id:x}")
        return bytes(pit_buf)

    def flash_partition(self, entry: PitEntry, image_path: Path, resume_seq0_part: int = 0) -> None:
        data = image_path.read_bytes()
        total_len = len(data)
        if total_len == 0:
            raise ValueError(f"La imagen {image_path} está vacía")

        print(
            f"[*] Flasheando '{entry.partition_name}' (PIT ID={entry.part_id}, "
            f"device_type={entry.device_type}) <- {image_path.name} ({total_len / (1024*1024):.2f} MB)...",
            flush=True,
        )
        if resume_seq0_part == 0:
            self.set_total_bytes(total_len)

        seq_max_bytes = self.file_part_size * self.parts_per_sequence
        offset = 0
        seq_idx = 0
        while offset < total_len:
            seq_data = data[offset : offset + seq_max_bytes]
            seq_len = len(seq_data)
            is_last = 1 if (offset + seq_len >= total_len) else 0

            # Pad sequence length up to multiple of file_part_size for packet transmission
            num_parts = (seq_len + self.file_part_size - 1) // self.file_part_size
            padded_seq_len = num_parts * self.file_part_size

            start_part = resume_seq0_part if seq_idx == 0 else 0
            if start_part == 0:
                # 1. Start flash sequence
                self._send_packet_1024(REQ_FILE_TRANSFER, XFER_FLASH)
                resp_id, val = self._recv_response_8(timeout=15.0)
                if resp_id != REQ_FILE_TRANSFER:
                    raise RuntimeError(f"XFER_FLASH falló en seq {seq_idx}: 0x{resp_id:x}/0x{val:x}")

                # 2. Send sequence byte count
                self._send_packet_1024(REQ_FILE_TRANSFER, XFER_PART, padded_seq_len)
                resp_id, val = self._recv_response_8(timeout=15.0)
                if resp_id != REQ_FILE_TRANSFER:
                    raise RuntimeError(f"XFER_PART header falló en seq {seq_idx}: 0x{resp_id:x}/0x{val:x}")

            # 3. Stream parts of file_part_size bytes
            for p in range(start_part, num_parts):
                p_start = p * self.file_part_size
                part_bytes = seq_data[p_start : p_start + self.file_part_size]
                if len(part_bytes) < self.file_part_size:
                    part_bytes = part_bytes + b"\x00" * (self.file_part_size - len(part_bytes))
                self.tx.write_all(part_bytes, timeout=15.0)
                resp_id, part_ack = self._recv_response_8(timeout=15.0)
                if resp_id != RESP_SEND_FILE_PART or part_ack != p:
                    raise RuntimeError(
                        f"Error en parte {p}/{num_parts} de seq {seq_idx}: 0x{resp_id:x}/0x{part_ack:x}"
                    )
                if (p + 1) % 5 == 0 or (p + 1) == num_parts:
                    print(
                        f"    [seq {seq_idx}] parte {p + 1}/{num_parts} ack=0x{part_ack:x}",
                        flush=True,
                    )

            # 4. End sequence & commit to eMMC partition
            # EndFileTransferPacket (Phone/AP): [REQ_FILE_TRANSFER, XFER_END, destination=0 (Phone),
            #   sequence_effective_bytes, unknown1=0, device_type, partition_id, end_of_file]
            self._send_packet_1024(
                REQ_FILE_TRANSFER,
                XFER_END,
                0,  # destination = Phone (AP)
                seq_len,
                0,
                entry.device_type,
                entry.part_id,
                is_last,
            )
            resp_id, val = self._recv_response_8(timeout=60.0)
            if resp_id != REQ_FILE_TRANSFER:
                raise RuntimeError(
                    f"XFER_END falló en seq {seq_idx} (part={entry.partition_name}): 0x{resp_id:x}/0x{val:x}"
                )

            offset += seq_len
            seq_idx += 1
            pct = offset * 100.0 / total_len
            print(f"    -> [{pct:5.1f}%] {offset / (1024*1024):.2f} / {total_len / (1024*1024):.2f} MB escritos")

        print(f"[+] ¡Partición '{entry.partition_name}' flasheada exitosamente!")

    def end_session(self, reboot: bool = False) -> None:
        sub = END_SESSION_REBOOT if reboot else END_SESSION_ONLY
        self._send_packet_1024(REQ_END_SESSION, sub)
        try:
            self._recv_response_8(timeout=3.0)
        except TimeoutError:
            pass


def main(argv: Optional[List[str]] = None) -> int:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Cliente nativo Samsung Odin/Loke para GT-I9082L (baffin) en macOS"
    )
    parser.add_argument("--port", help="Puerto serie (por defecto IOKit USB Bulk 0x04e8:0x685d)")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=64,
        help="Tamaño máximo de chunk USB Bulk OUT en bytes (por defecto 64 para Broadcom BCM28155)",
    )
    parser.add_argument(
        "--dump-pit",
        type=Path,
        nargs="?",
        const=project_root / "out/gt_i9082l.pit",
        help="Descargar y mostrar la tabla PIT real del dispositivo",
    )
    parser.add_argument(
        "--flash",
        nargs=2,
        metavar=("PART_NAME", "IMAGE_PATH"),
        help="Flashear imagen en una partición PIT (ej: --flash RECOVERY out/twrp-i9082.img)",
    )
    parser.add_argument(
        "--reboot",
        action="store_true",
        help="Reiniciar el dispositivo al finalizar la sesión Odin",
    )
    args = parser.parse_args(argv)

    if args.port:
        tx = OdinSerialTransport(args.port)
        conn_label = args.port
    else:
        tx = OdinIOKitUsbTransport(
            SAMSUNG_VID,
            SAMSUNG_ODIN_PID,
            intf=1,
            write_chunk_size=args.chunk_size,
        )
        conn_label = (
            f"IOKit USB Bulk (0x{SAMSUNG_VID:04x}:0x{SAMSUNG_ODIN_PID:04x}, intf=1, "
            f"chunk={args.chunk_size}B)"
        )

    tx.open()
    try:
        client = OdinClient(tx)
        print(f"[*] Conectado a {conn_label}. Enviando handshake ODIN -> LOKE...")
        client.handshake()
        proto = client.begin_session()
        print(f"[+] Handshake LOKE exitoso! Versión de protocolo: 0x{proto:08x} (v{client.protocol_version})")

        if client.protocol_version >= 2:
            client.set_file_part_size(131072)

        pit_bytes = client.dump_pit()
        entries = parse_pit(pit_bytes)
        print(f"[+] Tabla PIT descargada ({len(pit_bytes)} bytes, {len(entries)} particiones):")
        for e in entries:
            size_mb = (e.block_count * 512) / (1024 * 1024)
            print(
                f"  ID={e.part_id:<3} dev={e.device_type} name={e.partition_name:<16} "
                f"file={e.flash_filename:<20} blocks={e.block_count:<10} (~{size_mb:>7.2f} MB)"
            )

        if args.dump_pit:
            args.dump_pit.parent.mkdir(parents=True, exist_ok=True)
            args.dump_pit.write_bytes(pit_bytes)
            print(f"[+] Tabla PIT guardada en: {args.dump_pit}")

        if args.flash:
            target_part, img_str = args.flash
            img_path = Path(img_str)
            if not img_path.exists():
                raise FileNotFoundError(f"No existe la imagen: {img_path}")
            match = next(
                (e for e in entries if e.partition_name.upper() == target_part.upper()),
                None,
            )
            if match is None:
                raise ValueError(f"Partición '{target_part}' no encontrada en la tabla PIT del dispositivo")
            client.flash_partition(match, img_path)

        client.end_session(reboot=args.reboot)
        if args.reboot:
            print("[+] Comando de reinicio Odin enviado.")
    finally:
        tx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
