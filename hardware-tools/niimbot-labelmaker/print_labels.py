#!/usr/bin/env python3
"""
print_labels.py - rapidly print a list of text labels on a NIIMBOT D110.

Typical use (default label is 40mm x 12mm):

    # 1. See your printer and copy its address (do this once)
    python print_labels.py scan

    # 2. Render a batch to PNG previews WITHOUT printing (no printer needed)
    python print_labels.py preview --file labels.txt

    # 3. Print every line in labels.txt, back to back, on one connection
    python print_labels.py print --file labels.txt

    # ...or pass labels directly
    python print_labels.py print "Salt" "Pepper" "Olive Oil"

Label-text conventions:
  - One label per line in the file. Blank lines and lines starting with # are skipped.
  - Use \\n inside a line for a manual line break, e.g.  Basil\\n06/14

Tip: text comes out upside down? add  --rotate 270  (one-time calibration for your unit).
"""

import argparse
import asyncio
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

from niimbot_d110 import NiimbotPrinter, discover

# Every BLE run writes a full TX/RX trace here, next to this script.
DEBUG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")

# Common macOS TrueType fonts, tried in order. Bold reads best on tiny labels.
DEFAULT_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]

# Named label presets (length_mm, width_mm) matching NIIMBOT's own D110 sizes.
PRESETS = {
    "40x12": (40, 12),
    "30x15": (30, 15),
    "50x14": (50, 14),
    "75x12": (75, 12),
    "109x12.5": (109, 12.5),
}


def mm_to_dots(mm, dpi=203):
    return max(1, round(mm * dpi / 25.4))


def find_font_path(user_path):
    for p in ([user_path] if user_path else []) + DEFAULT_FONTS:
        if p and os.path.exists(p):
            return p
    return None  # falls back to Pillow's bundled bitmap font


def fit_font_size(draw, text, font_path, max_w, max_h, spacing):
    """Binary-search the largest font size whose text block fits the print area."""
    if font_path is None:
        return None  # default bitmap font is not scalable
    lo, hi, best = 6, max_h, 6
    while lo <= hi:
        mid = (lo + hi) // 2
        font = ImageFont.truetype(font_path, mid)
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w <= max_w and h <= max_h:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


def render_label(text, length_mm=40, width_mm=12, dpi=203, rotate=90,
                 margin=8, font_path=None, font_size=None):
    """Render text to a printer-ready 1-bit-friendly image.

    We draw on a landscape canvas (length x width) so text reads naturally, then
    rotate so the short side (12mm = 96 dots) becomes the print-head dimension.
    """
    text = text.replace("\\n", "\n")
    length_px = mm_to_dots(length_mm, dpi)  # 40mm -> 320
    width_px = mm_to_dots(width_mm, dpi)    # 12mm -> 96

    canvas = Image.new("L", (length_px, width_px), 255)  # white
    draw = ImageDraw.Draw(canvas)
    spacing = 2
    resolved_font_path = find_font_path(font_path)

    if font_size is None:
        font_size = fit_font_size(draw, text, resolved_font_path,
                                  length_px - 2 * margin, width_px - 2 * margin, spacing)

    if resolved_font_path and font_size:
        font = ImageFont.truetype(resolved_font_path, font_size)
    else:
        font = ImageFont.load_default()

    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (length_px - w) // 2 - bbox[0]
    y = (width_px - h) // 2 - bbox[1]
    draw.multiline_text((x, y), text, fill=0, font=font, spacing=spacing, align="center")

    return canvas.rotate(rotate, expand=True)


# Optional trailing quantity. Preferred: "--5" (most intuitive). Also accepts
# "x5", "5 pcs", "- 5 pcs", "3 pieces". The marker (--, x, or pcs) means a date
# like "06/13" is never mistaken for a count.
PCS_RE = re.compile(r"^(.*?)\s*(?:--\s*(\d+)|x\s*(\d+)|-?\s*(\d+)\s*(?:pcs?|pieces?))\.?\s*$", re.IGNORECASE)


def parse_label_line(line, default_copies=1):
    """Split a line into (text, copies). No quantity suffix -> default_copies."""
    m = PCS_RE.match(line)
    if m:
        return m.group(1).strip(), int(m.group(2) or m.group(3) or m.group(4))
    return line.strip(), default_copies


def collect_labels(args):
    """Return a list of (text, copies) tuples from --file and/or positional args."""
    labels = []
    default = getattr(args, "copies", 1)
    if args.file:
        stream = sys.stdin if args.file == "-" else open(args.file, encoding="utf-8")
        with stream as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line.strip() and not line.lstrip().startswith("#"):
                    labels.append(parse_label_line(line, default))
    for t in args.text:
        labels.append(parse_label_line(t, default))
    return labels


def label_kwargs(args):
    length_mm, width_mm = PRESETS[args.label]
    if args.length_mm:
        length_mm = args.length_mm
    if args.width_mm:
        width_mm = args.width_mm
    return dict(length_mm=length_mm, width_mm=width_mm, dpi=args.dpi,
               rotate=args.rotate, font_path=args.font, font_size=args.font_size)


async def autodiscover(name):
    print("Scanning for a NIIMBOT printer...")
    found = await discover(name)
    if not found:
        sys.exit("No NIIMBOT printer found. Is it powered on, in range, and NOT "
                 "connected to the phone app? Run: python print_labels.py scan")
    if len(found) > 1:
        msg = "Multiple devices found; pick one with --address:\n"
        for d in found:
            msg += f"  {d.address}   {d.name}\n"
        sys.exit(msg)
    print(f"Using {found[0].name} ({found[0].address})")
    return found[0].address


async def cmd_scan(args):
    found = await discover(args.name)
    if not found:
        print("No NIIMBOT printers found. Make sure it is on and not paired to the phone app.")
        return
    print("Found:")
    for d in found:
        print(f"  address: {d.address}   name: {d.name}")
    print("\nPin the address for faster connects, e.g.:")
    print(f"  python print_labels.py print --address {found[0].address} \"Hello\"")


def cmd_preview(args):
    labels = collect_labels(args)
    if not labels:
        sys.exit("No labels given. Use --file labels.txt or pass text arguments.")
    os.makedirs(args.out, exist_ok=True)
    kw = label_kwargs(args)
    total = 0
    for i, (text, copies) in enumerate(labels, 1):
        img = render_label(text, **kw)
        path = os.path.join(args.out, f"label_{i:03d}.png")
        # Save un-rotated-back for human viewing (rotate to landscape for legibility)
        img.rotate(-args.rotate, expand=True).save(path)
        shown = text.replace("\\n", " / ")
        print(f"  {path}   x{copies}   <- {shown!r}")
        total += copies
    print(f"\nWrote {len(labels)} design(s) to {args.out}/  ({total} label(s) will print)")


async def cmd_print(args):
    labels = collect_labels(args)
    if not labels:
        sys.exit("No labels given. Use --file labels.txt or pass text arguments.")
    kw = label_kwargs(args)
    jobs = [(text, copies, render_label(text, **kw)) for text, copies in labels]

    import traceback
    total = sum(c for _, c in labels)
    address, simulate = _resolve_target(args)
    if not simulate:
        address = address or await autodiscover(args.name)
    tag = "DRY-RUN (no hardware, no labels): " if simulate else ""
    print(f"{tag}Printing {len(labels)} design(s) = {total} label(s), density {args.density}.")
    printer = await _connect_logged(address, simulate=simulate, variant=getattr(args, "variant", "std"))
    try:
        await _settle(printer)
        await _prime(printer, getattr(args, "prime", 0), args)
        for i, (text, copies, img) in enumerate(jobs, 1):
            preview = text.replace("\\n", " / ")
            print(f"  [{i}/{len(jobs)}] {preview!r} x{copies}")
            # Each label is its own full session (start_print..end_print).
            await printer.print_image(img, density=args.density,
                                      quantity=copies, row_delay=args.row_delay)
            if i < len(jobs) and args.gap and not simulate:
                await asyncio.sleep(args.gap)
    except Exception as e:
        printer.log("EXCEPTION: " + repr(e))
        printer.log(traceback.format_exc())
        print(f"\n!! STOPPED: {e}")
    finally:
        await printer.disconnect()
    print(f"(trace: {DEBUG_LOG})")


def final_dims(args):
    """Pixel size of the final (rotated) image: (width=across-head, height=length)."""
    length_mm, width_mm = PRESETS[args.label]
    if args.length_mm:
        length_mm = args.length_mm
    if args.width_mm:
        width_mm = args.width_mm
    return mm_to_dots(width_mm, args.dpi), mm_to_dots(length_mm, args.dpi)


async def _connect_logged(address, simulate=False, variant="std"):
    """Construct a printer that traces everything to DEBUG_LOG, and connect."""
    import traceback
    p = NiimbotPrinter(address, verbose=True, log_path=DEBUG_LOG, simulate=simulate, variant=variant)
    try:
        await p.connect()
    except Exception as e:
        p.log("EXCEPTION during connect: " + repr(e))
        p.log(traceback.format_exc())
        await p.disconnect()
        raise
    return p


def _resolve_target(args):
    """Return (address, simulate). --dry-run uses the in-process simulator and
    skips Bluetooth discovery entirely (no hardware, no labels)."""
    if getattr(args, "dry_run", False):
        return "SIMULATION", True
    return args.address, False


async def _settle(printer, seconds=0.6):
    """Let the BLE link and the print head wake up before the first page."""
    if printer.simulate:
        return
    await asyncio.sleep(seconds)
    try:
        await printer.status()  # a throwaway exchange to confirm the link is live
    except Exception:
        pass
    await asyncio.sleep(0.2)


async def _prime(printer, n, args):
    """Print N sacrificial warm-up labels to flush the cold/misaligned opening
    labels, so the real ones come out clean. These will be blank or faint - peel
    and discard them."""
    if n <= 0:
        return
    print(f"Priming {n} sacrificial warm-up label(s) (peel & discard)...")
    img = render_label("PRIME", **label_kwargs(args))
    for _ in range(n):
        await printer.print_image(img, density=args.density, row_delay=args.row_delay)
        await asyncio.sleep(0.3)


async def cmd_test2(args):
    """Print labels numbered 1..N, each as its own session, to find the warm-up boundary."""
    import traceback
    address, simulate = _resolve_target(args)
    if not simulate:
        address = address or await autodiscover(args.name)
    n = args.count
    p = await _connect_logged(address, simulate=simulate, variant=getattr(args, "variant", "std"))
    try:
        await _settle(p)
        await _prime(p, args.prime, args)
        for k in range(1, n + 1):
            print(f"[{k}/{n}] printing '{k}' ...")
            img = render_label(str(k), **label_kwargs(args))
            await p.print_image(img, density=args.density, quantity=1, row_delay=args.row_delay)
            if k < n and args.gap and not simulate:
                await asyncio.sleep(args.gap)
    except Exception as e:
        p.log("EXCEPTION: " + repr(e))
        p.log(traceback.format_exc())
        print(f"\n!! STOPPED: {e}")
    finally:
        await p.disconnect()
    primed = f" (after {args.prime} PRIME label(s))" if args.prime else ""
    print(f"\nDone. You should have {n} labels numbered 1..{n}{primed}.\n"
          "Tell me which numbers printed and which were blank. If only the first 1-2 were "
          "blank, re-run with --prime 2 and the numbered ones should all be clean.\n"
          f"(trace: {DEBUG_LOG})")


async def cmd_info(args):
    import traceback
    address = args.address or await autodiscover(args.name)
    p = await _connect_logged(address)
    try:
        p.log("=== info ===")
        st = await p.status()
        p.log(f"status: {st}")
        for name, key in [("battery", 10), ("device_type", 8), ("label_type", 3),
                          ("density", 1), ("soft_version", 9), ("serial", 11)]:
            pkt = await p.get_info(key)
            p.log(f"info {name:13s}: {pkt.data.hex() if pkt and pkt.data else None}")
    except Exception as e:
        p.log("EXCEPTION: " + repr(e))
        p.log(traceback.format_exc())
        print(f"\n!! STOPPED: {e}")
    finally:
        await p.disconnect()
    print(f"Done. Full trace written to:\n  {DEBUG_LOG}")


async def cmd_test(args):
    import traceback
    address, simulate = _resolve_target(args)
    if not simulate:
        address = address or await autodiscover(args.name)
    samples = ["TEST 123", "Basil\\n06/14"]
    p = await _connect_logged(address, simulate=simulate, variant=getattr(args, "variant", "std"))
    try:
        await _settle(p)
        for i, text in enumerate(samples, 1):
            print(f"[{i}/{len(samples)}] {text!r} ...")
            img = render_label(text, **label_kwargs(args))
            await p.print_image(img, density=args.density, row_delay=args.row_delay)
            if not simulate:
                await asyncio.sleep(0.4)
    except Exception as e:
        p.log("EXCEPTION: " + repr(e))
        p.log(traceback.format_exc())
        print(f"\n!! STOPPED: {e}")
    finally:
        await p.disconnect()
    print(f"\nDone. (full TX/RX trace in {DEBUG_LOG})\n"
          "Note: this printer cannot render 100%-solid-black labels (a hardware/thermal "
          "limit), so text and barcodes are the right use case. Bump --density for darker output.")


def build_parser():
    p = argparse.ArgumentParser(description="Rapidly print text labels on a NIIMBOT D110.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_label_opts(sp):
        sp.add_argument("--label", choices=sorted(PRESETS), default="40x12",
                        help="label size preset (default 40x12)")
        sp.add_argument("--length-mm", type=float, help="override label length in mm")
        sp.add_argument("--width-mm", type=float, help="override label width (tape height) in mm")
        sp.add_argument("--dpi", type=int, default=203, help="print resolution (203 for D110, 300 for D11_H)")
        sp.add_argument("--rotate", type=int, default=90, choices=[0, 90, 180, 270],
                        help="rotation; use 270 if text prints upside down")
        sp.add_argument("--font", help="path to a .ttf/.ttc font")
        sp.add_argument("--font-size", type=int, help="fixed font size (default: auto-fit)")

    sp = sub.add_parser("scan", help="list nearby NIIMBOT printers and their addresses")
    sp.add_argument("--name", help="substring filter on the advertised name")

    sp = sub.add_parser("preview", help="render labels to PNGs without printing")
    sp.add_argument("text", nargs="*", help="label text(s)")
    sp.add_argument("--file", help="text file, one label per line ('-' for stdin)")
    sp.add_argument("--out", default="previews", help="output folder (default: previews/)")
    add_label_opts(sp)

    sp = sub.add_parser("print", help="render and print labels over Bluetooth")
    sp.add_argument("text", nargs="*", help="label text(s)")
    sp.add_argument("--file", help="text file, one label per line ('-' for stdin)")
    sp.add_argument("--address", help="BLE address/UUID (from `scan`); skips discovery")
    sp.add_argument("--name", help="substring filter on the advertised name")
    sp.add_argument("--density", type=int, default=3, choices=range(1, 6), help="darkness 1-5 (default 3)")
    sp.add_argument("--copies", type=int, default=1, help="copies per label (default 1)")
    sp.add_argument("--row-delay", type=float, default=0.01,
                    help="seconds between image rows; raise if prints are garbled, lower for speed")
    sp.add_argument("--gap", type=float, default=0.3, help="pause between labels in seconds")
    sp.add_argument("--prime", type=int, default=0,
                    help="print N sacrificial warm-up labels first (use 1-2 if the opening labels print blank)")
    sp.add_argument("--dry-run", action="store_true",
                    help="simulate the whole job (no Bluetooth, no labels); writes the byte trace to debug.log")
    sp.add_argument("--variant", choices=["std", "mv4"], default="mv4",
                    help="print sequence: std=D110, mv4=D110_M / v4 firmware")
    sp.add_argument("--verbose", action="store_true")
    add_label_opts(sp)

    sp = sub.add_parser("info", help="show printer state (cover/paper/battery) - diagnostic")
    sp.add_argument("--address", help="BLE address/UUID (from `scan`)")
    sp.add_argument("--name", help="substring filter on the advertised name")

    sp = sub.add_parser("test", help="print two sample text labels (full TX/RX trace)")
    sp.add_argument("--address", help="BLE address/UUID (from `scan`)")
    sp.add_argument("--name", help="substring filter on the advertised name")
    sp.add_argument("--density", type=int, default=3, choices=range(1, 6), help="darkness 1-5 (default 3)")
    sp.add_argument("--row-delay", type=float, default=0.01, help="seconds between image rows")
    sp.add_argument("--dry-run", action="store_true", help="simulate (no Bluetooth, no labels)")
    sp.add_argument("--variant", choices=["std", "mv4"], default="mv4", help="std=D110, mv4=D110_M")
    add_label_opts(sp)

    sp = sub.add_parser("test2", help="print labels numbered 1..N (verifies the first-label fix)")
    sp.add_argument("--address", help="BLE address/UUID (from `scan`)")
    sp.add_argument("--name", help="substring filter on the advertised name")
    sp.add_argument("--count", type=int, default=5, help="how many numbered labels (default 5)")
    sp.add_argument("--prime", type=int, default=0, help="sacrificial warm-up labels before the numbered ones")
    sp.add_argument("--density", type=int, default=3, choices=range(1, 6), help="darkness 1-5 (default 3)")
    sp.add_argument("--row-delay", type=float, default=0.01, help="seconds between image rows")
    sp.add_argument("--gap", type=float, default=0.3, help="pause between labels in seconds")
    sp.add_argument("--dry-run", action="store_true", help="simulate (no Bluetooth, no labels)")
    sp.add_argument("--variant", choices=["std", "mv4"], default="mv4", help="std=D110, mv4=D110_M")
    add_label_opts(sp)

    return p


def main():
    args = build_parser().parse_args()
    if args.cmd == "scan":
        asyncio.run(cmd_scan(args))
    elif args.cmd == "preview":
        cmd_preview(args)
    elif args.cmd == "print":
        asyncio.run(cmd_print(args))
    elif args.cmd == "info":
        asyncio.run(cmd_info(args))
    elif args.cmd == "test":
        asyncio.run(cmd_test(args))
    elif args.cmd == "test2":
        asyncio.run(cmd_test2(args))


if __name__ == "__main__":
    main()
