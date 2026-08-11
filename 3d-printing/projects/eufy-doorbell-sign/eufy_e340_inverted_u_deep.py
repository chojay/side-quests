#!/usr/bin/env python3
"""
Eufy E340 - INVERTED-U sign, DEEP ANGLED hug (grips doorbell + angled bracket)

Like eufy_e340_inverted_u_walled.py, but the perimeter hug wall is DEEPER and is
extruded ALONG THE DOORBELL'S 15deg TILTED NORMAL (aim-left, matching the Eufy
wedge), so it follows the tilted unit all the way back and also hugs the angled
bracket/wedge behind it - much more stability, and it can't bind (a straight deep
wall would, since the tilt shifts the side ~tan15 per mm of depth).

  - Flat sign header (thin) stays at the wall plane, facing straight out.
  - The ∩ hug wall (L/R/top, OPEN bottom) is a tilted prism, WALL_DEPTH deep along
    the 15deg normal -> tracks the doorbell sides + reaches the angled bracket.
  - Prints LYING FLAT: the wall leans 15deg (a printable overhang), support-free.

NEEDS CONFIRMATION (send a side-profile photo of your mounted unit):
  - WALL_DEPTH (20mm) and the assembly depth: the wedge pushes the doorbell out,
    so the right depth to reach the bracket depends on your wedge's protrusion.
  - TILT_DEG / AIM_LEFT must match how YOUR wedge is oriented.
  - HUG_CLEAR (1.2mm) snugness.

Doorbell 152.4 (H) x 51.6 (W) x 28.2 (D) mm; tilt 15deg aim-left (from your wedge).

Usage: ../../.venv-3dp/bin/python eufy_e340_inverted_u_deep.py
"""
import os, math
from build123d import *

# ─── DOORBELL + TILT ───────────────────────────────────────────
DB_W, DB_H, DB_R = 51.6, 152.4, 9.0
TILT_DEG = 15.0
AIM_LEFT = True
TH = math.radians(TILT_DEG)
SIN, COS = math.sin(TH), math.cos(TH)
NX = -SIN if AIM_LEFT else SIN
NORMAL = Vector(NX, 0, COS)          # doorbell tilted normal = hug direction

# ─── FRAME ─────────────────────────────────────────────────────
CLEAR = 1.5              # flat-frame opening clearance (drop-over)
HUG_CLEAR = 1.2          # hug-wall clearance to the tilted sides (snugger)
BORDER = 8.0
FRAME_THK = 6.0
RAISE = 2.0
OPEN_HW = DB_W / 2 + CLEAR
OUTER_HW = OPEN_HW + BORDER
OUTER_R = 8.0
Yt, Yb = DB_H / 2, -DB_H / 2
LEG_TOP = Yt + 2.0

# ─── DEEP HUG WALL ─────────────────────────────────────────────
WALL_DEPTH = 20.0        # along the tilted normal - reaches back to the bracket
WALL_THK = 2.4
HUG_HW = DB_W / 2 + HUG_CLEAR     # hug-wall inner half-width (snug on the sides)

# ─── SIGN HEADER ───────────────────────────────────────────────
SIGN_W = 2 * OUTER_HW
SIGN_H = 42.0
SIGN_FILLET = 8.0
SIGN_BOT = Yt
SIGN_CY = SIGN_BOT + SIGN_H / 2

# ─── TEXT ──────────────────────────────────────────────────────
LINE1, LINE2 = "PLEASE DON'T RING,", "BABY SLEEPING"
FONT, FONT_STYLE = "Helvetica", FontStyle.BOLD  # any installed sans works; pick one licensed on your system
TEXT_MARGIN, LINE_GAP, MAX_FONT = 3.0, 3.0, 9.0
OUTLINE_INSET, OUTLINE_W = 3.5, 1.4
USABLE_TEXT_W = SIGN_W - 2 * OUTLINE_INSET - 2 * TEXT_MARGIN

WORK = os.path.dirname(os.path.abspath(__file__))
BASE_STL = os.path.join(WORK, "eufy_e340_inverted_u_deep_base.stl")
TEXT_STL = os.path.join(WORK, "eufy_e340_inverted_u_deep_text.stl")
MERGED_STL = os.path.join(WORK, "eufy_e340_inverted_u_deep_merged.stl")


def _span(x0, x1, y0, y1, r=0.0, mode=Mode.ADD):
    w, h = x1 - x0, y1 - y0
    rr = min(r, w / 2 - 0.01, h / 2 - 0.01) if r > 0 else 0
    with Locations(((x0 + x1) / 2, (y0 + y1) / 2)):
        if rr > 0.05:
            RectangleRounded(w, h, rr, mode=mode)
        else:
            Rectangle(w, h, mode=mode)


def measure_text_width(txt, fs):
    with BuildSketch() as s:
        Text(txt, font_size=fs, font=FONT, font_style=FONT_STYLE)
    return s.sketch.bounding_box().size.X


def fit_font_size():
    ref = 10.0
    widest = max(measure_text_width(LINE1, ref), measure_text_width(LINE2, ref))
    return min(ref * (USABLE_TEXT_W / widest), MAX_FONT)


def build_base():
    with BuildPart() as base:
        # flat ∩ frame (header + legs), z 0..FRAME_THK
        with BuildSketch(Plane.XY):
            with Locations((0, SIGN_CY)):
                RectangleRounded(SIGN_W, SIGN_H, SIGN_FILLET)
            _span(-OUTER_HW, -OPEN_HW, Yb, LEG_TOP, r=OUTER_R)
            _span(OPEN_HW, OUTER_HW, Yb, LEG_TOP, r=OUTER_R)
        extrude(amount=FRAME_THK)
        # DEEP hug wall: ∩ ring (L/R/top, open bottom) extruded ALONG THE TILTED
        # NORMAL so it follows the doorbell + angled bracket. Start 1mm inside the
        # frame for a clean union.
        with BuildSketch(Plane.XY.offset(FRAME_THK - 1.0)):
            _span(-HUG_HW - WALL_THK, -HUG_HW, Yb, Yt + WALL_THK)   # left
            _span(HUG_HW, HUG_HW + WALL_THK, Yb, Yt + WALL_THK)     # right
            _span(-HUG_HW, HUG_HW, Yt, Yt + WALL_THK)               # top
        extrude(amount=WALL_DEPTH + 1.0, dir=NORMAL)
    return base.part


def build_text(fs):
    top = Plane.XY.offset(FRAME_THK)
    l1 = SIGN_CY + (fs + LINE_GAP) / 2
    l2 = SIGN_CY - (fs + LINE_GAP) / 2
    with BuildPart() as t:
        with BuildSketch(top):
            with Locations((0, l1)):
                Text(LINE1, font_size=fs, font=FONT, font_style=FONT_STYLE)
        extrude(amount=RAISE)
        with BuildSketch(top):
            with Locations((0, l2)):
                Text(LINE2, font_size=fs, font=FONT, font_style=FONT_STYLE)
        extrude(amount=RAISE)
        with BuildSketch(top):
            ow, oh = SIGN_W - 2 * OUTLINE_INSET, SIGN_H - 2 * OUTLINE_INSET
            orad = max(SIGN_FILLET - OUTLINE_INSET, 1.0)
            with Locations((0, SIGN_CY)):
                RectangleRounded(ow, oh, orad)
                RectangleRounded(ow - 2 * OUTLINE_W, oh - 2 * OUTLINE_W,
                                 max(orad - OUTLINE_W, 0.5), mode=Mode.SUBTRACT)
        extrude(amount=RAISE)
    return t.part


def main():
    if measure_text_width(LINE1, 10) < 1:
        raise SystemExit(f"Font '{FONT}' produced no geometry")
    fs = fit_font_size()
    print("=" * 62)
    print("Eufy E340 - INVERTED-U DEEP ANGLED hug")
    print(f"  Hug wall {WALL_DEPTH}mm deep ALONG the {TILT_DEG}deg normal "
          f"(aim {'LEFT' if AIM_LEFT else 'RIGHT'})")
    print(f"  Follows the tilted doorbell + angled bracket; open bottom; thin sign")
    print(f"  Max depth off wall ~{FRAME_THK + WALL_DEPTH*COS:.1f}mm | PRINT flat, walls lean {TILT_DEG}deg")
    print("=" * 62)
    base = build_base()
    text = build_text(fs)
    merged = base + text
    export_stl(base, BASE_STL)
    export_stl(text, TEXT_STL)
    export_stl(merged, MERGED_STL)
    for p in (BASE_STL, TEXT_STL, MERGED_STL):
        print(f"  {os.path.basename(p):42s} {os.path.getsize(p):>9,} bytes")


if __name__ == "__main__":
    main()
