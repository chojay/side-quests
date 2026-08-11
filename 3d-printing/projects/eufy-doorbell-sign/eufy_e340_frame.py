#!/usr/bin/env python3
"""
Eufy Video Doorbell E340 - Frame + Customisable Sign  (build123d generator)

Adapted from sebtobar's "Ring Doorbell Frame - Customisable Sign!"
(MakerWorld model 1139309) for the Eufy E340. The original is a friction-fit
picture frame that wraps the doorbell body, with a separate rounded plaque ABOVE
it carrying two lines of contrasting-colour text ("PLEASE DON'T RING, BABY
SLEEPING"). One commenter already remixed it for a Wyze doorbell by resizing the
opening, which is exactly the adaptation done here.

=== MEASURED / SOURCE DIMENSIONS (record verbatim; do not re-research) ===
Eufy E340 body (eufy official spec, support.nz.eufy.com art. 154000242527):
    138 mm (H) x 50 mm (W) x 27.5 mm (D)      <- PRIMARY, used to size opening
    Retail listings (B&H) quote 6.0x1.9x1.2in / 152x48x30mm; the 152mm "height"
    includes the angled wedge mount / packaging, so the 138mm body spec wins.
Original Ring frame internal opening (designer's description): 127.3 x 62.1 mm
    (Ring 2nd-gen body ~128 x 62 x 28 => essentially a 0-clearance friction fit)
Eufy is NARROWER (50 vs 62) and TALLER (138 vs 127) than the Ring.

=== FIT NOTE ===
FRICTION_CLEAR (1.0 mm total / 0.5 per side) is a snug-but-reliable fit chosen
over the original's near-zero clearance because (a) the eufy spec is rounded to
the mm, (b) the opening must also clear the E340's wall baseplate, and (c) FDM
prints holes slightly undersized. If your calipers show the body at the high end
or it prints tight, raise FRICTION_CLEAR to 1.6-2.0. If it is loose, lower to 0.5.

=== PRINT ORIENTATION ===
Back (wall side) flat on the bed at Z=0; decorative face + raised text point +Z
up. Support-free: the opening is a vertical through-hole, the raised text/outline
overhang nothing. Already in print orientation -> no export rotation.

=== TWO-COLOUR SPLIT (Bambu H2D / AMS) ===
  base STL  (dark  / filament 1): frame ring + sign plaque, Z 0..BODY_HEIGHT
  text STL  (light / filament 2): raised letters + outline, Z BODY_HEIGHT..+RAISE
  merged STL: union of both, for single-colour printing / the HTML viewer.

Usage:  ../../.venv-3dp/bin/python eufy_e340_frame.py
Requires: build123d >= 0.10, trimesh
"""
import os
from build123d import *

# ─── DOORBELL (measured) ───────────────────────────────────────
DEVICE_W = 50.0      # mm  E340 body width
DEVICE_H = 138.0     # mm  E340 body height
DEVICE_D = 27.5      # mm  E340 body depth (reference only)

# ─── FIT ───────────────────────────────────────────────────────
FRICTION_CLEAR = 1.0     # mm total added to each opening dimension (see FIT NOTE)
OPENING_W = DEVICE_W + FRICTION_CLEAR     # 51.0
OPENING_H = DEVICE_H + FRICTION_CLEAR     # 139.0

# ─── FRAME ─────────────────────────────────────────────────────
# BORDER slimmed 11 -> 6 mm so the frame fits the tight gap between the doorbell
# and the door-frame trim. Every 1 mm off BORDER = 1 mm less reach toward the
# trim on each side. Frame outer width is now 63 mm (was 73).
BORDER = 6.0             # mm  visible frame border width (each side)  [SLIM]
BODY_HEIGHT = 6.0        # mm  Z thickness of frame + plaque (also the side-grip depth)
OUTER_FILLET = 7.0       # mm  outer corner radius (proportional to the slim border)
OPENING_FILLET = 6.0     # mm  opening corner radius (matches rounded doorbell body;
                         #     also relieves internal stress corners)
FRAME_OUTER_W = OPENING_W + 2 * BORDER    # 63.0
FRAME_OUTER_H = OPENING_H + 2 * BORDER    # 151.0

# ─── SIGN PLAQUE (above the frame) ─────────────────────────────
# Kept at its original 73 mm width per request ("make the frame thinner, not the
# sign"). Decoupled from the now-slimmer frame, so the plaque overhangs the frame
# by ~5 mm per side at the join (still one solid, watertight union).
SIGN_W = 73.0
SIGN_H = 42.0                     # mm  plaque height
SIGN_FILLET = 8.0                 # mm  plaque corner radius
OVERLAP = 4.0                     # mm  plaque bottom overlaps the frame top border (merges solid)
# plaque bottom sits OVERLAP into the frame's top border:
SIGN_BOTTOM = FRAME_OUTER_H / 2 - OVERLAP
SIGN_CY = SIGN_BOTTOM + SIGN_H / 2

# ─── TEXT + OUTLINE (raised, contrasting colour) ───────────────
LINE1 = "PLEASE DON'T RING,"
LINE2 = "BABY SLEEPING"
FONT = "Helvetica"
FONT_STYLE = FontStyle.BOLD
RAISE = 0.8                       # mm  raised height of text + outline (~4 layers @0.2)
TEXT_MARGIN = 3.0                # mm  gap from outline to text
LINE_GAP = 3.0                   # mm  vertical gap between the two text lines
MAX_FONT = 8.0                   # mm  cap so big short lines do not look silly

OUTLINE_INSET = 3.5              # mm  from plaque edge to outline
OUTLINE_W = 1.2                  # mm  outline stroke width

# Usable text width = plaque width minus outline and margins on both sides
USABLE_TEXT_W = SIGN_W - 2 * OUTLINE_INSET - 2 * TEXT_MARGIN   # ~60mm

# ─── OUTPUT ────────────────────────────────────────────────────
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_STL = os.path.join(WORK_DIR, "eufy_e340_frame_base.stl")
TEXT_STL = os.path.join(WORK_DIR, "eufy_e340_frame_text.stl")
MERGED_STL = os.path.join(WORK_DIR, "eufy_e340_frame_merged.stl")


# ─── helpers ───────────────────────────────────────────────────
def measure_text_width(txt, font_size):
    """Rendered width (mm) of a text line at a given font size."""
    with BuildSketch() as s:
        Text(txt, font_size=font_size, font=FONT, font_style=FONT_STYLE)
    return s.sketch.bounding_box().size.X


def fit_font_size():
    """Largest font size (<= MAX_FONT) so the widest line fits USABLE_TEXT_W."""
    ref = 10.0
    widest_ref = max(measure_text_width(LINE1, ref), measure_text_width(LINE2, ref))
    fs = ref * (USABLE_TEXT_W / widest_ref)
    return min(fs, MAX_FONT)


# ─── geometry ──────────────────────────────────────────────────
def build_base():
    """Frame ring + sign plaque slab (single solid, dark colour)."""
    with BuildPart() as base:
        # Frame outer block
        with BuildSketch():
            RectangleRounded(FRAME_OUTER_W, FRAME_OUTER_H, OUTER_FILLET)
        extrude(amount=BODY_HEIGHT)
        # Sign plaque above (unions on, overlapping the top border)
        with BuildSketch():
            with Locations((0, SIGN_CY)):
                RectangleRounded(SIGN_W, SIGN_H, SIGN_FILLET)
        extrude(amount=BODY_HEIGHT)
        # Doorbell opening: full-height through-hole
        with BuildSketch():
            RectangleRounded(OPENING_W, OPENING_H, OPENING_FILLET)
        extrude(amount=BODY_HEIGHT, mode=Mode.SUBTRACT)
    return base.part


def build_text(font_size):
    """Raised text lines + outline ring on the plaque front face."""
    top = Plane.XY.offset(BODY_HEIGHT)
    line1_y = SIGN_CY + (font_size + LINE_GAP) / 2
    line2_y = SIGN_CY - (font_size + LINE_GAP) / 2

    with BuildPart() as txt:
        # Line 1
        with BuildSketch(top):
            with Locations((0, line1_y)):
                Text(LINE1, font_size=font_size, font=FONT, font_style=FONT_STYLE)
        extrude(amount=RAISE)
        # Line 2
        with BuildSketch(top):
            with Locations((0, line2_y)):
                Text(LINE2, font_size=font_size, font=FONT, font_style=FONT_STYLE)
        extrude(amount=RAISE)
        # Outline ring following the plaque rounded-rect
        out_w = SIGN_W - 2 * OUTLINE_INSET
        out_h = SIGN_H - 2 * OUTLINE_INSET
        out_r = max(SIGN_FILLET - OUTLINE_INSET, 1.0)
        with BuildSketch(top):
            with Locations((0, SIGN_CY)):
                RectangleRounded(out_w, out_h, out_r)
                RectangleRounded(out_w - 2 * OUTLINE_W, out_h - 2 * OUTLINE_W,
                                 max(out_r - OUTLINE_W, 0.5), mode=Mode.SUBTRACT)
        extrude(amount=RAISE)
    return txt.part


def main():
    print("=" * 60)
    print("Eufy E340 Doorbell Frame + Sign")
    print(f"  Opening (friction fit): {OPENING_W:.1f} x {OPENING_H:.1f} mm "
          f"(device {DEVICE_W}x{DEVICE_H} + {FRICTION_CLEAR})")
    print(f"  Frame outer: {FRAME_OUTER_W:.1f} x {FRAME_OUTER_H:.1f} x {BODY_HEIGHT} mm")
    print(f"  Plaque: {SIGN_W:.1f} x {SIGN_H:.1f} mm, center Y={SIGN_CY:.1f}")
    fs = fit_font_size()
    print(f"  Auto-fit font: {FONT} {FONT_STYLE.name} @ {fs:.2f} mm "
          f"(usable width {USABLE_TEXT_W:.1f} mm)")
    print("=" * 60)

    base = build_base()
    text = build_text(fs)
    merged = base + text

    export_stl(base, BASE_STL)
    export_stl(text, TEXT_STL)
    export_stl(merged, MERGED_STL)

    total_h = FRAME_OUTER_H / 2 + (SIGN_H - OVERLAP) + FRAME_OUTER_H / 2  # = FRAME_OUTER_H + SIGN_H - OVERLAP
    print(f"\nExported:")
    for p in (BASE_STL, TEXT_STL, MERGED_STL):
        print(f"  {os.path.basename(p):32s} {os.path.getsize(p):>9,} bytes")
    print(f"\nOverall footprint ~ {FRAME_OUTER_W:.1f} (W) x {total_h:.1f} (H) x "
          f"{BODY_HEIGHT + RAISE:.1f} (Z) mm  -- fits H2D bed easily")


if __name__ == "__main__":
    main()
