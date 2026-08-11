"""
niimbot_d110.py - minimal Bluetooth-LE driver for the NIIMBOT D110 (also D11 / D101 / D11_H).

Dependencies: bleak (BLE on macOS via CoreBluetooth) + Pillow (image encode).
No GUI libs, no Homebrew C libraries.

The wire protocol (packet framing, request codes, image-row encoding and the
print sequence) is reproduced from the proven open-source implementations:
  - https://github.com/AndBondStyle/niimprint
  - https://github.com/labbots/NiimPrintX, with the mv4/_M dialect sequence from MultiMote/niimblue  (the macOS / bleak path)

A NIIMBOT label is just a 1-bit bitmap streamed row by row. There is no "text"
command on the device, so text is rendered to an image first (see print_labels.py).

KEY GOTCHAS (full list + history in GOTCHAS.md):
  1. D110_M needs the "mv4" sequence (printStart 9-byte + setPageSize 13-byte, no
     printClear/pageStart/setQuantity). The std D110 sequence ACKs but prints BLANK
     on an _M unit. self.variant selects it; "mv4" is the default in the CLI.
  2. Copies do NOT work via the copies field - print N copies as N separate full
     start_print..end_print sessions (print_image loops; print_page gets quantity=1).
  3. The 3 per-row "black pixel count" header bytes must be REAL per-third counts;
     zeros make the printer burn nothing (blank).
  4. One full start_print..end_print session PER label. A shared multi-page session
     prints nothing and the page counter just accumulates (1,3,5,...).
  5. Trust `page` (label ejected), not `progress` (data processed).
  6. macOS TCC blocks BLE from non-Terminal processes (SIGABRT). Use --dry-run to
     iterate logic with no hardware/labels.
"""

import asyncio
import enum
import math
import struct
import time

from PIL import Image, ImageOps
from bleak import BleakClient, BleakScanner

# D110 advertises as "D110-XXXXXXXX". We also match its siblings.
NIIMBOT_NAME_PREFIXES = ("D110", "D11", "D101", "NIIMBOT")


class NiimbotPacket:
    """Frame: 0x55 0x55 <type> <len> <data...> <checksum> 0xAA 0xAA"""

    def __init__(self, type_, data):
        self.type = type_
        self.data = bytes(data)

    @classmethod
    def from_bytes(cls, pkt):
        assert pkt[:2] == b"\x55\x55"
        assert pkt[-2:] == b"\xaa\xaa"
        type_ = pkt[2]
        len_ = pkt[3]
        data = pkt[4 : 4 + len_]
        checksum = type_ ^ len_
        for b in data:
            checksum ^= b
        assert checksum == pkt[-3], "checksum mismatch"
        return cls(type_, data)

    def to_bytes(self):
        checksum = self.type ^ len(self.data)
        for b in self.data:
            checksum ^= b
        return bytes(
            (0x55, 0x55, self.type, len(self.data), *self.data, checksum, 0xAA, 0xAA)
        )

    def __repr__(self):
        return f"<NiimbotPacket type={self.type} data={self.data.hex()}>"


class RequestCode(enum.IntEnum):
    GET_INFO = 64  # 0x40
    HEARTBEAT = 220  # 0xDC
    SET_LABEL_TYPE = 35  # 0x23
    SET_LABEL_DENSITY = 33  # 0x21
    START_PRINT = 1  # 0x01
    END_PRINT = 243  # 0xF3
    START_PAGE_PRINT = 3  # 0x03
    END_PAGE_PRINT = 227  # 0xE3
    SET_DIMENSION = 19  # 0x13
    SET_QUANTITY = 21  # 0x15
    GET_PRINT_STATUS = 163  # 0xA3
    PRINT_CLEAR = 32  # 0x20  (D110 requires this before each page)


def parse_heartbeat(data):
    """Decode a heartbeat payload. Field layout varies by firmware/length."""
    closing = power = paper = rfid = None
    n = len(data)
    if n == 20:
        paper, rfid = data[18], data[19]
    elif n == 19:
        closing, power, paper, rfid = data[15], data[16], data[17], data[18]
    elif n == 13:
        closing, power, paper, rfid = data[9], data[10], data[11], data[12]
    elif n == 10:
        closing, power, rfid = data[8], data[9], data[8]
    elif n == 9:
        closing = data[8]
    return {
        "cover_closed": (None if closing is None else bool(closing)),
        "paper_present": (None if paper is None else bool(paper)),
        "battery_level": power,  # 0-4 ish
        "rfid_read": (None if rfid is None else bool(rfid)),
        "raw_len": n,
    }


async def discover(name_filter=None, timeout=8.0):
    """Scan for NIIMBOT printers. Returns a list of bleak BLEDevice objects.

    On macOS, device addresses are system-assigned UUIDs (not MAC addresses),
    so the only stable identifier between runs is this UUID. Print it once with
    the `scan` command and pin it via --address for faster, deterministic connects.
    """
    found = {}
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    for address, (device, adv) in devices.items():
        name = device.name or (adv.local_name if adv else None) or ""
        if name_filter:
            if name_filter.lower() in name.lower():
                found[address] = device
        elif any(name.upper().startswith(p) for p in NIIMBOT_NAME_PREFIXES):
            found[address] = device
    return list(found.values())


# --- Simulation (dry-run) ----------------------------------------------------
# A stand-in for BleakClient that mimics a D110: it records every outgoing packet
# and synthesizes plausible ACKs, so the entire print pipeline can run with NO
# hardware and NO wasted labels. Used by --dry-run for fast, inline iteration.
class _SimChar:
    def __init__(self, uuid, properties):
        self.uuid = uuid
        self.properties = properties


class _SimService:
    def __init__(self, uuid, chars):
        self.uuid = uuid
        self.characteristics = chars


class _SimClient:
    DATA_CHAR = "bef8d6c9-9c21-4c9e-b632-bd58c1009f9f"
    DATA_SVC = "e7810a71-73ae-499d-8c15-faa9aef0c3f2"

    def __init__(self, address):
        self.address = address
        self.is_connected = False
        self._cb = None
        self.writes = []  # recorded outgoing frames (bytes)
        char = _SimChar(self.DATA_CHAR, ["read", "write-without-response", "notify", "write"])
        self.services = [_SimService(self.DATA_SVC, [char])]

    async def connect(self):
        self.is_connected = True

    async def disconnect(self):
        self.is_connected = False

    async def start_notify(self, char, cb):
        self._cb = cb

    async def stop_notify(self, char):
        self._cb = None

    async def write_gatt_char(self, char, data, response=None):
        data = bytes(data)
        self.writes.append(data)
        if len(data) < 4:
            return
        req = data[2]
        if req == 0x85:  # image rows are never acknowledged by the printer
            return
        if self._cb is None:
            return
        if req == RequestCode.GET_PRINT_STATUS:  # report a finished page so polls exit
            frame = NiimbotPacket(0xB3, struct.pack(">HBB", 0xFFFF, 100, 100)).to_bytes()
        else:  # generic ACK with data[0]=1 (transceive returns the first packet)
            frame = NiimbotPacket((req + 1) & 0xFF, b"\x01").to_bytes()
        self._cb(0, bytearray(frame))


class NiimbotPrinter:
    """One BLE connection; reuse it to print a whole batch back-to-back."""

    def __init__(self, address, verbose=False, printhead_pixels=96, log_path=None,
                 simulate=False, variant="std"):
        self.address = address
        self.verbose = verbose
        self.simulate = simulate
        self.variant = variant  # "std" (D110) or "mv4" (D110_M / v4 firmware)
        self.printhead_pixels = printhead_pixels  # D110/D11/D101 = 96
        self.client = _SimClient(address) if simulate else BleakClient(address)
        self.char = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._buf = bytearray()
        self._logf = open(log_path, "w", encoding="utf-8") if log_path else None
        self._t0 = time.monotonic()

    def log(self, msg):
        line = f"{time.monotonic() - self._t0:7.3f}  {msg}"
        if self._logf:
            self._logf.write(line + "\n")
            self._logf.flush()
        if self.verbose:
            print(line)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.disconnect()

    async def connect(self):
        await self.client.connect()
        self.log(f"connected to {self.address}")
        self.log_gatt()
        self.char = self._find_char()
        self.log(f"selected data characteristic = {self.char}")
        await self.client.start_notify(self.char, self._on_notify)

    def log_gatt(self):
        """Dump the full GATT table so we can confirm the right characteristic."""
        self.log("GATT table:")
        for service in self.client.services:
            self.log(f"  service {service.uuid}")
            for ch in service.characteristics:
                props = ",".join(ch.properties)
                self.log(f"    char {ch.uuid}  [{props}]")

    async def disconnect(self):
        try:
            if self.client.is_connected:
                if self.char:
                    await self.client.stop_notify(self.char)
                await self.client.disconnect()
        except Exception:
            pass
        if self._logf:
            self._logf.close()
            self._logf = None

    def _find_char(self):
        """The NIIMBOT data characteristic exposes read + write-without-response + notify."""
        want = {"read", "write-without-response", "notify"}
        for service in self.client.services:
            for ch in service.characteristics:
                if want <= set(ch.properties):
                    return ch.uuid
        # Looser fallback: anything we can both write to and be notified on.
        for service in self.client.services:
            for ch in service.characteristics:
                props = set(ch.properties)
                if "notify" in props and ("write" in props or "write-without-response" in props):
                    return ch.uuid
        raise RuntimeError("Could not locate the NIIMBOT BLE characteristic")

    def _on_notify(self, _sender, data):
        # Notifications can arrive fragmented or batched; reassemble full frames.
        self._buf.extend(data)
        while len(self._buf) >= 7:
            if self._buf[0:2] != b"\x55\x55":
                idx = self._buf.find(b"\x55\x55")
                if idx == -1:
                    self._buf.clear()
                    return
                del self._buf[:idx]
                if len(self._buf) < 7:
                    return
            total = self._buf[3] + 7
            if len(self._buf) < total:
                return
            frame = bytes(self._buf[:total])
            del self._buf[:total]
            try:
                pkt = NiimbotPacket.from_bytes(frame)
                self.log(f"RX  type={pkt.type:#04x} data={pkt.data.hex()}")
                self._queue.put_nowait(pkt)
            except Exception as e:
                self.log(f"RX  unparseable {frame.hex()} ({e})")

    async def _write(self, packet):
        self.log(f"TX  type={packet.type:#04x} data={packet.data.hex()}")
        await self.client.write_gatt_char(self.char, packet.to_bytes(), response=False)

    def _drain(self):
        while not self._queue.empty():
            self._queue.get_nowait()

    async def transceive(self, code, data, timeout=6.0):
        """Send a command and return the first response packet (None on timeout)."""
        self._drain()
        await self._write(NiimbotPacket(code, data))
        try:
            pkt = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        if pkt.type == 219:
            raise RuntimeError("printer returned error packet (0xDB)")
        return pkt

    # --- individual commands -------------------------------------------------
    async def set_label_density(self, n):
        return await self.transceive(RequestCode.SET_LABEL_DENSITY, bytes((n,)))

    async def set_label_type(self, n):
        return await self.transceive(RequestCode.SET_LABEL_TYPE, bytes((n,)))

    async def start_print(self):
        return await self.transceive(RequestCode.START_PRINT, b"\x01")

    async def print_clear(self):
        return await self.transceive(RequestCode.PRINT_CLEAR, b"\x01")

    async def start_page_print(self):
        return await self.transceive(RequestCode.START_PAGE_PRINT, b"\x01")

    async def set_dimension(self, w, h):
        return await self.transceive(RequestCode.SET_DIMENSION, struct.pack(">HH", w, h))

    async def set_quantity(self, n):
        return await self.transceive(RequestCode.SET_QUANTITY, struct.pack(">H", n))

    async def end_page_print(self):
        pkt = await self.transceive(RequestCode.END_PAGE_PRINT, b"\x01")
        return bool(pkt and pkt.data and pkt.data[0])

    async def end_print(self):
        pkt = await self.transceive(RequestCode.END_PRINT, b"\x01")
        return bool(pkt and pkt.data and pkt.data[0])

    async def get_print_status(self):
        pkt = await self.transceive(RequestCode.GET_PRINT_STATUS, b"\x01")
        if pkt and len(pkt.data) >= 4:
            page, p1, p2 = struct.unpack(">HBB", pkt.data[:4])
            return {"page": page, "progress1": p1, "progress2": p2}
        return None

    async def heartbeat(self):
        return await self.transceive(RequestCode.HEARTBEAT, b"\x01")

    async def status(self):
        """Parsed printer state: cover closed?, paper present?, battery level."""
        pkt = await self.heartbeat()
        return parse_heartbeat(pkt.data) if pkt else None

    async def get_info(self, key):
        return await self.transceive(RequestCode.GET_INFO, bytes((key,)))

    # --- image encode + print ------------------------------------------------
    def _encode_image_rows(self, image):
        # White background -> 0 (no heat), black ink -> 1 (heat). invert() flips
        # luminance so black text becomes the printed pixels.
        img = ImageOps.invert(image.convert("L")).convert("1")
        nbytes = math.ceil(img.width / 8)
        # The 3 header bytes after the row index are the count of black pixels in
        # each third of the row. The D110 firmware USES these to decide how much to
        # heat; sending 0,0,0 makes it print blank. (See niimblue D110PrintTask.)
        chunk = max(1, (self.printhead_pixels // 8) // 3)  # 4 bytes for a 96px head
        for y in range(img.height):
            bits = "".join("0" if img.getpixel((x, y)) == 0 else "1" for x in range(img.width))
            row = int(bits, 2).to_bytes(nbytes, "big")
            parts = [0, 0, 0]
            for i, byte in enumerate(row):
                parts[min(i // chunk, 2)] += bin(byte).count("1")
            header = struct.pack(">H3BB", y, parts[0] & 0xFF, parts[1] & 0xFF, parts[2] & 0xFF, 1)
            yield NiimbotPacket(0x85, header + row)

    async def _step(self, name, coro, critical=False):
        """Await a command, log its ACK, and warn (or raise) if the printer is silent."""
        resp = await coro
        ok = resp is not None
        extra = f" resp={resp.data.hex()}" if ok and hasattr(resp, "data") and resp.data else ""
        self.log(f"STEP {name:18s} {'ACK' if ok else 'NO RESPONSE (timeout)'}{extra}")
        if not ok and critical:
            raise RuntimeError(
                f"printer never acknowledged '{name}'. The page was not started, "
                f"so nothing will print. Check cover closed / paper loaded, then retry."
            )
        return resp

    # The D110 print flow is a SESSION: begin_print once, then a page per label,
    # then finish_print once. Doing start_print/end_print per label (powering the
    # head down between each) makes the first labels of a batch drop out blank.
    # (Mirrors niimblue's D110PrintTask: printInit -> printPage* -> printEnd.)
    async def begin_print(self, density=3):
        self.log(f"=== begin_print density={density} variant={self.variant} ===")
        await self._step("set_label_density", self.set_label_density(density))
        await self._step("set_label_type", self.set_label_type(1))
        if self.variant == "mv4":
            # printStart9b: totalPages=1, color=0, speed=1, flag=0
            payload = struct.pack(">H", 1) + bytes((0, 0, 0, 0, 0, 1, 0))
            await self._step("start_print9b", self.transceive(RequestCode.START_PRINT, payload), critical=True)
        else:
            await self._step("start_print", self.start_print(), critical=True)

    async def print_page(self, image, quantity=1, row_delay=0.01):
        """Print one page (one label design, `quantity` physical copies)."""
        self.log(f"--- page {image.width}x{image.height} qty={quantity} variant={self.variant} ---")
        if self.variant == "mv4":
            # D110_M / v4: no printClear, no pageStart, no separate setQuantity.
            # A one-way status ping, then a 13-byte page size with copies inside.
            await self._write(NiimbotPacket(RequestCode.GET_PRINT_STATUS, b"\x01"))
            page13 = struct.pack(">HHHHBBBH", image.height, image.width, quantity, 0, 0, 0, 0, 0)
            await self._step("set_page_size13b", self.transceive(RequestCode.SET_DIMENSION, page13))
        else:
            await self._step("print_clear", self.print_clear())
            await self._step("start_page_print", self.start_page_print(), critical=True)
            await self._step("set_dimension", self.set_dimension(image.height, image.width))
            await self._step("set_quantity", self.set_quantity(quantity))

        rows = list(self._encode_image_rows(image))
        delay = 0 if self.simulate else row_delay
        self.log(f"sending {len(rows)} image rows (row_delay={delay})")
        for pkt in rows:
            await self.client.write_gatt_char(self.char, pkt.to_bytes(), response=False)
            if delay:
                await asyncio.sleep(delay)  # let the BLE buffer drain
        self.log("image rows sent")

        ended = False
        for _ in range(80):
            if await self.end_page_print():
                ended = True
                break
            await asyncio.sleep(0.05)
        self.log(f"STEP {'end_page_print':18s} {'ACK' if ended else 'NO ACK'}")

        # Poll until the printer reports the page(s) ejected. If progress hits 100%
        # but `page` never advances, the printer rasterized the image but could not
        # feed a label - almost always out of labels, cover ajar, or a jam. Bail
        # fast with that diagnosis instead of spinning for 30s.
        last, completed = None, False
        polls = 0 if self.simulate else 80  # ~8s
        for _ in range(max(polls, 1)):
            last = await self.get_print_status()
            if last and last["page"] >= quantity:
                completed = True
                break
            await asyncio.sleep(0 if self.simulate else 0.1)
        self.log(f"STEP {'print_status':18s} {last} completed={completed}")
        if not completed and not self.simulate:
            prog = (last or {}).get("progress1")
            raise RuntimeError(
                f"printer STALLED: progress reached {prog}% but no label advanced "
                f"(page < {quantity}). The data was accepted but nothing fed - most "
                f"likely OUT OF LABELS, cover not fully latched, or a jam. "
                f"Check the roll/cover and retry."
            )

    async def finish_print(self):
        await self.end_print()
        self.log("=== finish_print (end_print) ===")

    async def print_image(self, image, density=3, quantity=1, row_delay=0.01):
        """Print `quantity` copies. Each copy is its OWN full start_print..end_print
        session. The D110_M ignores the copies field in setPageSize13b (it prints 1
        and the page counter stops at 1), and a shared multi-page session prints
        nothing - so repeating the whole session is the only reliable way to get N
        copies."""
        for n in range(max(1, quantity)):
            await self.begin_print(density)
            await self.print_page(image, quantity=1, row_delay=row_delay)
            await self.finish_print()
            if n + 1 < quantity and not self.simulate:
                await asyncio.sleep(0.3)
