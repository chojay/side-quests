#!/usr/bin/env python3
"""
Braun MultiQuick 9 (MQ9187XL / HB901AI) Food-Processor Accessory Caddy
======================================================================

Holds the loose Group-11 "Food Processor Accessory XL with Dicer (fpl)"
tools that have no home in the US kit (the OEM "Stand for storing", item
12, ships only on some non-US versions). Other groups (ActiveBlade shaft,
beaker, whisk, puree, mc chopper) already have holders.

TWO ZONES (matches the owner's "everything vertical-slot except b,c,k,i"):
  ZONE 1 - SLOT RACK (dish-rack of vertical edge-slots), flat parts:
     l  Kneading hook (FP)
     m  Dicer blade
     o  Cleaning pusher
     p  Insert holder (carrier)
     q  French fries disc
     (i)   Slicing inserts  x2 (fine, coarse)
     (ii)  Shredding inserts x2 (fine, coarse)
     (iii) Julienne insert  x1
  ZONE 2 - ROUND POCKETS / PEGS (bulky 3-D parts):
     b  Coupling for motor part   -> open ring cup
     c  Pusher                    -> open ring cup
     k  Dough Tool (FP)           -> hub cup (paddle rises above rim)
     i  Chopping blade (S-blade)  -> SHROUDED well + center post (safety)
  r  Disc axle -> deep round socket (lives in Zone 2)

VARIANTS (both emitted):
  A  single integrated caddy (slot rack behind pocket block, one print)
  B  two-part: slot-rack piece + pocket-block piece (side by side)

!!! DIMENSIONS ARE ESTIMATES !!!
No part dimensions are published anywhere (verified: Braun, eReplacement,
Amazon spare listings carry electrical specs only). Everything below is
scaled from the known 2 L bowl + typical Braun FP geometry, with GENEROUS
clearances so a v1 test-fit is forgiving. Every number is a named constant;
tighten with the caliper worksheet in the design-spec note, then re-run.

Print orientation: AS MODELLED. Base flat on the bed, every fin/ring/post
grows straight up off layer 1. Open tops -> no bridging -> NO SUPPORTS.

Pipeline (per design-gotchas playbook): build -> watertight ->
point-containment truth table -> envelope assert (<= bed) -> multi-view
render -> interactive HTML viewer.
"""
import os
import base64
import zipfile
import math

from build123d import (
    Box, Cylinder, Compound, Pos, Rot, export_stl,
)
import trimesh

script_dir = os.path.dirname(os.path.abspath(__file__))

# =====================================================================
# ESTIMATED PART DIMENSIONS (mm)  --  REPLACE WITH CALIPER MEASUREMENTS
# =====================================================================
# SLOT_PARTS: (key, label, edge_thickness, stand_height)
#   edge_thickness = part thickness where it sits in the slot (sets gap)
#   stand_height   = how tall it stands (info / viewer only)
SLOT_PARTS = [
    ("q",   "French fries disc",        16.0, 112.0),
    ("p",   "Insert holder (carrier)",  16.0, 112.0),
    ("m",   "Dicer blade",              12.0, 105.0),
    ("l",   "Kneading hook (FP)",       12.0, 100.0),
    ("o",   "Cleaning pusher",          10.0,  95.0),
    ("i1",  "Slicing insert (fine)",    10.0,  90.0),
    ("i2",  "Slicing insert (coarse)",  10.0,  90.0),
    ("ii1", "Shredding insert (fine)",  10.0,  90.0),
    ("ii2", "Shredding insert (coarse)",10.0,  90.0),
    ("iii", "Julienne insert",          10.0,  90.0),
]

# PEG_PARTS: (key, label, peg_dia, peg_h, boss_dia, boss_h, swing_dia)
#   The part's center bore drops over a vertical peg and rests on the base.
#   peg_dia  = peg to fit the part's bore/socket (slip fit)
#   peg_h    = peg height (engage the bore enough to stay upright)
#   boss_dia/h = short wider base boss under the peg for strength
#   swing_dia = blade/paddle swing; reserved as floor keep-clear in packing
#   (i is stored WITH its cover j clipped on -> edges covered, peg is safe)
PEG_PARTS = [
    ("i", "Chopping blade (S) on peg, cover j on", 10.0, 70.0, 18.0, 10.0, 112.0),
    ("k", "Dough tool on peg",                     10.0, 58.0, 18.0,  8.0,  95.0),
]

# CUP_PARTS: (key, label, part_dia, well_depth) - open ring cups, bore = dia + clear
CUP_PARTS = [
    ("b", "Motor coupling", 62.0, 32.0),
    ("c", "Pusher",         58.0, 45.0),
    ("r", "Disc axle",      32.0, 50.0),
]

# === FIT CLEARANCES (loose, because v1 is estimate-based) ===
CLEAR_SLOT   = 3.0   # added to edge_thickness for each slot gap
CLEAR_POCKET = 4.0   # added to part_dia for each bore

# === SHELL / FEATURE GEOMETRY ===
WALL      = 2.5      # ring-wall / fin thickness
BASE_T    = 3.0      # shared base-plate thickness (also = cup floor)
OVERLAP   = 0.6      # features sink this far into the base so unions fuse
FIN_H     = 42.0     # slot-fin height (kept < disc radius so hubs clear)
SLOT_DEPTH = 58.0    # front-back depth of the slot rack
LOWER_H   = 94.0     # 2-story rack: lower-story height (clears 90 mm inserts)
DECK_T    = 3.0      # 2-story rack: deck plate thickness
BACKWALL_T = 3.0     # back wall thickness (backstop + ties the fins together)
BACKWALL_H = 70.0    # back wall height (gives tall discs a face to lean on)
ANTITIP_FOOT = 0.0   # base extension behind the wall; 0 = base ends at the wall
MIDGAP    = 8.0      # gap between pocket block and slot rack (variant A)
PACK_GAP  = 6.0      # gap between pockets when packing

# === VARIANT B SLOT RACK -- v3 (5 disc slots + 2 deep disc slots) ===
# The v2 2x3 insert grid was too small (parts did not fit), so it is removed.
# The rack is now TWO groups of vertical disc slots on one open-front base:
#   GROUP A : 5 disc slots, 90 mm deep,  for the ~163 mm (16.3 cm) discs
#   GROUP B : 2 disc slots, 160 mm deep, for a ~156 mm (15.6 cm) disc
# Group B is made as deep as the disc (16 cm) so the disc's WHOLE footprint
# lands on the base -- no front/back overhang, so a 15.6 cm disc on edge stays
# stable. The base steps to match (deeper behind group B). Both groups use the
# disc treatment: tall back wall + short fins (hub rides above) for hub clearance.
DISC_THICK      = 16.0    # disc rim thickness in the slot (gap = +CLEAR_SLOT = 19)
ZONE_GAP        = 8.0     # gap between group A and group B on the shared base
DISC_BACKWALL_H = 75.0    # tall solid backstop the disc leans on (both groups)
# --- group A: 5 disc slots (~163 mm discs) ---
DISC_DIA_A      = 163.0   # group-A disc diameter to clear (~16.3 cm class)
N_DISC_SLOTS_A  = 5       # group A: 5 slots
DISC_DEPTH      = 90.0    # group-A slot length (Y)
# --- group B: 2 deep slots that fully cradle a 15.6 cm disc ---
DISC_DIA_B      = 156.0   # group-B disc diameter (15.6 cm, corrected from "mm")
N_DISC_SLOTS_B  = 2       # group B: 2 slots
DISC_DEPTH_B    = 160.0   # group-B slot length (Y) = 16 cm, so the 156 mm disc's
                          # whole footprint sits on the base (no overhang)

# --- AUX BOX: a separate open-top bin that fills the L-notch behind group A
#     (the empty corner left because group A is shallower than group B). It
#     stores loose auxiliary items; same Z height as the rack. Footprint is
#     DERIVED from the rack so it always fits the notch. ---
AUX_BOX     = True        # also emit the aux box
AUX_CLEAR   = 1.0         # gap per side so the bin drops into the notch
AUX_WALL    = WALL        # bin wall thickness (2.5 mm)

# --- FRONT RETAINING WALL (so discs cannot roll or tip out the open front). A
#     CONTINUOUS wall, tall enough to retain but low enough to still lift each
#     disc straight UP and out over it. Height is a fraction of FIN_H, set per
#     group: group A's tall discs get a higher lip than group B's cradled disc. ---
FRONT_WALL        = True
FRONT_WALL_FRAC_A = 0.75   # group-A front lip = this x FIN_H ("75% coverage") -> 31.5 mm
FRONT_WALL_FRAC_B = 0.5    # group-B front lip = this x FIN_H ("50% Z")        -> 21 mm

# === LIGHTENING (perforate the solid thin walls to save filament) ===
# Variant-A fins get a ~50%-open MESH of small holes (a big window would let a
# loose blade shift into it). Back walls stay SOLID (backstop). Cups stay caged.
LIGHTEN    = True
WIN_BORDER = 4.0     # solid frame kept around the perforated/caged region
MESH_PITCH = 15.0    # fin mesh hole spacing
MESH_DIA   = 12.0    # fin mesh hole diameter (~50% open at this pitch)
CUP_WIN_N  = 6       # windows (= posts) around each cup wall

# The variant-B DISC rack holds only big discs (>> any opening), so its dividers
# can be opened up FAR more than the blade-safe mesh -> big tall windows (frame +
# vertical struts), ~70% open. Saves filament / print time; fins stay rigid
# (tied at base + front lip + back wall).
DISC_FIN_WINDOWS = True   # use tall windows on the disc-rack dividers
DISC_FIN_BORDER  = 4.0    # solid frame kept around each divider's windows
DISC_FIN_STRUT   = 3.0    # vertical strut between windows (mid bearing for the disc)
# Windows run the FULL fin height (big material saving) but are kept narrow so
# each window's 4 mm top border bridges only ~DISC_FIN_WIN_MAX mm -> prints with
# NO supports. 15 mm is a trivially-bridgeable span on FDM.
DISC_FIN_WIN_MAX = 15.0   # max single-window width (Y) = the top-border bridge span

# === PRINTER ===
# H2D working area: 325 x 320 (single nozzle) / 300 x 320 (dual). This is a
# single-material print, so 300 mm is a safe, real, conservative guard.
BED = 300.0


# =====================================================================
# HELPERS
# =====================================================================
def shelf_pack(items, max_w, gap):
    """Row/shelf packer for circles. items: [(id, dia)] -> sorted desc.
    Returns ({id: (cx, cy, dia)}, total_w, total_d)."""
    items = sorted(items, key=lambda t: -t[1])
    x = y = row_h = total_w = 0.0
    placed = {}
    for cid, dia in items:
        if x > 0 and x + dia > max_w:
            y += row_h + gap
            x = 0.0
            row_h = 0.0
        placed[cid] = (x + dia / 2, y + dia / 2, dia)
        x += dia + gap
        row_h = max(row_h, dia)
        total_w = max(total_w, x - gap)
    return placed, total_w, y + row_h


def mesh_holes_fin(cx, cy_mid, z_lo, depth, height):
    """Grid of round through-holes for a fin (thin in X). ~50% open inside a
    WIN_BORDER frame, so a leaning blade still bears on the lattice 'lands'
    everywhere (no big window for it to shift into). Returns a cutter list."""
    cutters = []
    y0, y1 = cy_mid - depth / 2 + WIN_BORDER, cy_mid + depth / 2 - WIN_BORDER
    z0, z1 = z_lo + WIN_BORDER, z_lo + height - WIN_BORDER
    if y1 - y0 < MESH_DIA or z1 - z0 < MESH_DIA:
        return cutters
    ny = max(1, round((y1 - y0) / MESH_PITCH))
    nz = max(1, round((z1 - z0) / MESH_PITCH))
    for i in range(ny):
        yy = y0 + (y1 - y0) * (i + 0.5) / ny
        for j in range(nz):
            zz = z0 + (z1 - z0) * (j + 0.5) / nz
            cutters.append(Pos(cx, yy, zz) * Rot(0, 90, 0)
                           * Cylinder(MESH_DIA / 2, WALL + 2))
    return cutters


def window_cutters_fin(cx, cy_mid, z_lo, depth, height):
    """Big tall windows for a DISC-rack divider (thin in X): a solid border
    frame + vertical struts, the rest open (~70%). Discs are far larger than any
    window so nothing can shift through -> we open the divider much more than the
    blade-safe mesh. The struts give the disc a mid-span bearing land and keep
    the frame rigid. Returns a cutter list (each cut goes through X)."""
    cutters = []
    y0 = cy_mid - depth / 2 + DISC_FIN_BORDER
    y1 = cy_mid + depth / 2 - DISC_FIN_BORDER
    z0 = z_lo + DISC_FIN_BORDER
    z1 = z_lo + height - DISC_FIN_BORDER
    if y1 - y0 < 12 or z1 - z0 < 8:
        return cutters
    span = y1 - y0
    n_win = max(1, math.ceil((span + DISC_FIN_STRUT) /
                             (DISC_FIN_WIN_MAX + DISC_FIN_STRUT)))
    win_w = (span - (n_win - 1) * DISC_FIN_STRUT) / n_win
    zc, zh = (z0 + z1) / 2, z1 - z0
    for i in range(n_win):
        wy = y0 + i * (win_w + DISC_FIN_STRUT) + win_w / 2
        cutters.append(Pos(cx, wy, zc) * Box(WALL + 2, win_w, zh))
    return cutters


def cup_window_cutters(px, py, bore_r, outer_r, well_depth):
    """Vertical windows around a cup wall -> a cage (top/bottom rim + posts)."""
    cutters = []
    win_h = well_depth - 2 * WIN_BORDER
    if win_h < 8.0:
        return cutters
    R = (bore_r + outer_r) / 2
    radial = (outer_r - bore_r) + 2
    arc = (2 * math.pi * R / CUP_WIN_N) * 0.5     # ~50% open
    for i in range(CUP_WIN_N):
        a = 360.0 / CUP_WIN_N * i
        cx = px + R * math.cos(math.radians(a))
        cy = py + R * math.sin(math.radians(a))
        cutters.append(
            Pos(cx, cy, BASE_T + well_depth / 2) * Rot(0, 0, a)
            * Box(radial, arc, win_h))
    return cutters


def slot_positions(parts):
    """Fin x-edges and per-part gap-center x for a parts subset.
    Returns (fins, centers, width). fin, gap0, fin, gap1 ... (N+1 fins)."""
    fins = []     # (x_start) of each fin
    centers = []  # (key, label, x_center, stand_h) of each gap
    x = 0.0
    for (key, label, thick, stand_h) in parts:
        fins.append(x)             # fin before this gap
        x += WALL
        gap = thick + CLEAR_SLOT
        centers.append((key, label, x + gap / 2, stand_h))
        x += gap
    fins.append(x)                 # closing fin
    x += WALL
    return fins, centers, x


def slot_x_positions():
    """All SLOT_PARTS in one band (single-story rack)."""
    return slot_positions(SLOT_PARTS)


def backwall_h(stand_h):
    """Per-slot back-wall height: taller behind tall discs, shorter behind
    short inserts (the owner OK'd different Z per part). Clamped 45-75 mm."""
    return max(45.0, min(75.0, 0.62 * stand_h))


def build_slot_fins(x_off, y_off, with_backwall=True):
    """Comb of fins + a STEPPED back wall (backstop that also ties the fins
    together). No base; caller supplies it. Everything sinks OVERLAP into the
    base to fuse. Back wall sits just behind the fins (max-Y side).
    Returns (solid, width, centers)."""
    fins, centers, width = slot_x_positions()
    h = FIN_H + OVERLAP
    solid = None
    holes = []
    for fx in fins:
        cx = x_off + fx + WALL / 2
        fin = Pos(cx, y_off + SLOT_DEPTH / 2,
                  BASE_T - OVERLAP + h / 2) * Box(WALL, SLOT_DEPTH, h)
        solid = fin if solid is None else solid + fin
        if LIGHTEN:
            holes += mesh_holes_fin(cx, y_off + SLOT_DEPTH / 2, BASE_T,
                                    SLOT_DEPTH, FIN_H)
    if with_backwall:                            # back wall stays SOLID (backstop)
        wy = y_off + SLOT_DEPTH - OVERLAP
        for i, (_key, _label, _xc, stand_h) in enumerate(centers):
            ww = backwall_h(stand_h) + OVERLAP
            seg_x0, seg_x1 = fins[i], fins[i + 1] + WALL
            solid = solid + Pos(x_off + (seg_x0 + seg_x1) / 2,
                                wy + BACKWALL_T / 2,
                                BASE_T - OVERLAP + ww / 2) * Box(
                                    seg_x1 - seg_x0, BACKWALL_T, ww)
    if holes:
        solid = solid - Compound(children=holes)
    return solid, width, centers


def build_two_story_rack(x_off, y_off):
    """2-story rack: lower level = vertical front-load slots for the 5 inserts
    (blades); upper level = a deck carrying vertical slots for the 5 plates
    (q,p,m,l,o) + a stepped back wall. The deck is carried by the lower
    dividers (it only bridges ~13 mm between them) so the whole thing prints
    support-free. A full-height back wall is the spine + backstop for both.
    Returns (solid, width, depth, lower_centers, upper_centers, deck_z, top_z)."""
    UPPER = [p for p in SLOT_PARTS if p[0] in ("q", "p", "m", "l", "o")]
    LOWER = [p for p in SLOT_PARTS if p[0] in ("i1", "i2", "ii1", "ii2", "iii")]
    u_fins, u_centers, u_w = slot_positions(UPPER)

    deck_z = BASE_T + LOWER_H               # deck underside height
    ins_thick = LOWER[0][2]
    gap = ins_thick + CLEAR_SLOT
    pitch = WALL + gap
    n_ch = max(len(LOWER), int(u_w // pitch))   # channels fill width + carry deck

    solid = None
    holes = []

    def add(s):
        nonlocal solid
        solid = s if solid is None else solid + s

    # --- lower dividers (full LOWER_H) + record insert-slot centers ---
    lower_centers = []
    x = 0.0
    lh = LOWER_H + OVERLAP
    for i in range(n_ch):
        cx = x_off + x + WALL / 2
        add(Pos(cx, y_off + SLOT_DEPTH / 2,
                BASE_T - OVERLAP + lh / 2) * Box(WALL, SLOT_DEPTH, lh))
        if LIGHTEN:
            holes += mesh_holes_fin(cx, y_off + SLOT_DEPTH / 2, BASE_T,
                                    SLOT_DEPTH, LOWER_H)
        if i < len(LOWER):
            lower_centers.append((LOWER[i][0], LOWER[i][1], x + WALL + gap / 2))
        x += pitch
    add(Pos(x_off + x + WALL / 2, y_off + SLOT_DEPTH / 2,
            BASE_T - OVERLAP + lh / 2) * Box(WALL, SLOT_DEPTH, lh))
    lower_w = x + WALL
    width = max(lower_w, u_w)

    # --- deck plate across the full width (sinks into divider tops) ---
    add(Pos(x_off + width / 2, y_off + SLOT_DEPTH / 2,
            deck_z - OVERLAP + (DECK_T + OVERLAP) / 2) * Box(width, SLOT_DEPTH,
                                                             DECK_T + OVERLAP))

    # --- upper disc fins on the deck (band centered in width) ---
    u_base = deck_z + DECK_T
    u_x0 = (width - u_w) / 2
    fh = FIN_H + OVERLAP
    for fx in u_fins:
        cx = x_off + u_x0 + fx + WALL / 2
        add(Pos(cx, y_off + SLOT_DEPTH / 2,
                u_base - OVERLAP + fh / 2) * Box(WALL, SLOT_DEPTH, fh))
        if LIGHTEN:
            holes += mesh_holes_fin(cx, y_off + SLOT_DEPTH / 2, u_base,
                                    SLOT_DEPTH, FIN_H)

    # --- upper stepped back wall + lower spine, both SOLID (backstops) ---
    wy = y_off + SLOT_DEPTH - OVERLAP
    for i, (_k, _l, _xc, sh) in enumerate(u_centers):
        ww = backwall_h(sh) + OVERLAP
        sx0, sx1 = u_fins[i], u_fins[i + 1] + WALL
        add(Pos(x_off + u_x0 + (sx0 + sx1) / 2, wy + BACKWALL_T / 2,
                u_base - OVERLAP + ww / 2) * Box(sx1 - sx0, BACKWALL_T, ww))
    lwh = LOWER_H + DECK_T + OVERLAP        # lower spine (solid = insert backstop)
    add(Pos(x_off + width / 2, wy + BACKWALL_T / 2,
            BASE_T - OVERLAP + lwh / 2) * Box(width, BACKWALL_T, lwh))

    if holes:
        solid = solid - Compound(children=holes)

    top_z = u_base + max(backwall_h(sh) for _, _, _, sh in u_centers)
    return solid, width, SLOT_DEPTH, lower_centers, u_centers, deck_z, top_z


def build_disc_zone(x_off, y_off, n_slots, depth=DISC_DEPTH, fin_h=FIN_H,
                    backwall_h=DISC_BACKWALL_H):
    """A group of n_slots vertical slots (n+1 fins) + one SOLID back wall.
    `depth` is the open-facing (Y) length, `fin_h` the side-fin height,
    `backwall_h` the backstop height -- so the same builder makes group A's
    tall full-depth disc slots AND group B's short low pockets. Fins kept short
    (< disc radius) so a disc's hub rides above them. Everything sinks OVERLAP
    into the base (caller supplies it) so booleans fuse. Returns (solid, width,
    gap_centers_x)."""
    gap = DISC_THICK + CLEAR_SLOT                 # 16 + 3 = 19 mm
    width = n_slots * gap + (n_slots + 1) * WALL
    h = fin_h + OVERLAP
    solid = None
    holes = []
    fin_xs = []
    x = 0.0
    for _ in range(n_slots + 1):
        fin_xs.append(x)
        cx = x_off + x + WALL / 2
        fin = Pos(cx, y_off + depth / 2,
                  BASE_T - OVERLAP + h / 2) * Box(WALL, depth, h)
        solid = fin if solid is None else solid + fin
        if LIGHTEN:
            if DISC_FIN_WINDOWS:
                holes += window_cutters_fin(cx, y_off + depth / 2, BASE_T,
                                            depth, fin_h)
            else:
                holes += mesh_holes_fin(cx, y_off + depth / 2, BASE_T,
                                        depth, fin_h)
        x += WALL + gap
    wy = y_off + depth - OVERLAP                  # back wall stays SOLID (backstop)
    ww = backwall_h + OVERLAP
    solid = solid + Pos(x_off + width / 2, wy + BACKWALL_T / 2,
                        BASE_T - OVERLAP + ww / 2) * Box(width, BACKWALL_T, ww)
    if holes:
        solid = solid - Compound(children=holes)
    centers = [x_off + fin_xs[i] + WALL + gap / 2 for i in range(n_slots)]
    return solid, width, centers


def build_front_wall(x_off, width, y_front, frac):
    """Continuous retaining wall along the open front edge of a group, height =
    frac x FIN_H. Low enough to lift each disc straight up over it, tall enough
    to stop the disc rolling/tipping out the front. Ties the fin-fronts into one
    rigid edge. Returns a solid (or None if disabled)."""
    if not FRONT_WALL:
        return None
    h = frac * FIN_H + OVERLAP
    return Pos(x_off + width / 2, y_front + BACKWALL_T / 2,
               BASE_T - OVERLAP + h / 2) * Box(width, BACKWALL_T, h)


def pocket_pack_items():
    """Items for the shelf packer: pegs reserve their swing dia, cups reserve
    their outer dia. Returns [(key, dia)]."""
    items = [(k[0], k[6]) for k in PEG_PARTS]            # swing_dia
    items += [(k[0], (k[2] + CLEAR_POCKET) + 2 * WALL)   # bore + walls
              for k in CUP_PARTS]
    return items


def build_cups(placed, x_off, y_off):
    """Ring-wall cups for CUP_PARTS on the shared base. Walls sink OVERLAP
    into the base; bores stop at base top (plate is the cup floor).
    Returns (walls, bores, meta)."""
    walls = bores = None
    meta = []
    info = {k[0]: k for k in CUP_PARTS}
    for key in [k[0] for k in CUP_PARTS]:
        if key not in placed:
            continue
        cx, cy, _ = placed[key]
        _, label, part_dia, well_depth = info[key]
        bore_r = (part_dia + CLEAR_POCKET) / 2
        outer_r = bore_r + WALL
        px, py = x_off + cx, y_off + cy
        wh = well_depth + OVERLAP
        wall = Pos(px, py, BASE_T - OVERLAP + wh / 2) * Cylinder(outer_r, wh)
        bore = Pos(px, py, BASE_T + (well_depth + 1.0) / 2) * Cylinder(
            bore_r, well_depth + 1.0)
        walls = wall if walls is None else walls + wall
        bores = bore if bores is None else bores + bore
        if LIGHTEN:
            for c in cup_window_cutters(px, py, bore_r, outer_r, well_depth):
                bores = bores + c
        meta.append((key, label, px, py, bore_r, outer_r, well_depth))
    return walls, bores, meta


def build_pegs(placed, x_off, y_off):
    """Vertical pegs (base boss + post) for PEG_PARTS. The part's bore drops
    over the post and rests on the base plate. Returns (posts, meta)."""
    posts = None
    meta = []
    info = {k[0]: k for k in PEG_PARTS}
    for key in [k[0] for k in PEG_PARTS]:
        if key not in placed:
            continue
        cx, cy, swing = placed[key]
        _, label, peg_dia, peg_h, boss_dia, boss_h, swing_dia = info[key]
        px, py = x_off + cx, y_off + cy
        boss = Pos(px, py, BASE_T - OVERLAP + (boss_h + OVERLAP) / 2) * Cylinder(
            boss_dia / 2, boss_h + OVERLAP)
        peg = Pos(px, py, BASE_T - OVERLAP + (peg_h + OVERLAP) / 2) * Cylinder(
            peg_dia / 2, peg_h + OVERLAP)
        posts = boss if posts is None else posts + boss
        posts = posts + peg
        meta.append((key, label, px, py, peg_dia, swing_dia, peg_h))
    return posts, meta


def export_3mf(mesh, path):
    """Minimal generic 3MF (zip) for Bambu Studio (proven in repo)."""
    verts = "".join(f'<vertex x="{v[0]:.4f}" y="{v[1]:.4f}" z="{v[2]:.4f}"/>'
                    for v in mesh.vertices)
    tris = "".join(f'<triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>'
                   for f in mesh.faces)
    model_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        '<resources><object id="1" type="model"><mesh>'
        f'<vertices>{verts}</vertices><triangles>{tris}</triangles>'
        '</mesh></object></resources>'
        '<build><item objectid="1"/></build></model>')
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType='
        '"application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType='
        '"application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type='
        '"http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model_xml)


def render_multiview(mesh, path, title):
    """Two-view (iso + top) matplotlib render to eyeball the bed contact."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tris = mesh.vertices[mesh.faces]
    fig = plt.figure(figsize=(14, 7))
    for n, (elev, azim, sub, label) in enumerate([
            (28, -55, 121, "ISO (print orientation, base on bed)"),
            (89, -90, 122, "TOP")]):
        ax = fig.add_subplot(sub, projection="3d")
        coll = Poly3DCollection(tris, alpha=1.0)
        coll.set_facecolor((0.29, 0.56, 0.85))
        coll.set_edgecolor((0.15, 0.27, 0.42))
        coll.set_linewidth(0.05)
        ax.add_collection3d(coll)
        mn = mesh.vertices.min(axis=0)
        mx = mesh.vertices.max(axis=0)
        ctr = (mn + mx) / 2
        r = (mx - mn).max() / 2
        ax.set_xlim(ctr[0] - r, ctr[0] + r)
        ax.set_ylim(ctr[1] - r, ctr[1] + r)
        ax.set_zlim(min(0, ctr[2] - r), ctr[2] + r)
        ax.view_init(elev=elev, azim=azim)
        ax.set_box_aspect((1, 1, 1))
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=90)
    plt.close(fig)


def export_viewer(stem, name, stl_path, lines):
    with open(stl_path, "rb") as f:
        stl_b64 = base64.b64encode(f.read()).decode("utf-8")
    info = "".join(f"<p>{ln}</p>" for ln in lines)
    html = '''<!DOCTYPE html><html><head><title>''' + name + ''' - 3D Viewer</title>
<style>body{margin:0;overflow:hidden;font-family:Arial,sans-serif}
#info{position:absolute;top:10px;left:10px;background:rgba(0,0,0,.78);color:#fff;
padding:14px 18px;border-radius:8px;max-width:380px}
#info h2{margin:0 0 8px;font-size:15px}#info p{margin:3px 0;font-size:12px;color:#cfcfcf}
#c{position:absolute;bottom:10px;left:10px;background:rgba(0,0,0,.6);color:#aaa;
padding:8px 12px;border-radius:5px;font-size:11px}</style></head><body>
<div id="info"><h2>''' + name + '''</h2>''' + info + '''</div>
<div id="c">Left: rotate | Right: pan | Scroll: zoom</div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
const scene=new THREE.Scene();scene.background=new THREE.Color(0xf2f2f2);
const camera=new THREE.PerspectiveCamera(45,innerWidth/innerHeight,0.1,10000);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth,innerHeight);document.body.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0x606060,1.6));
const dl=new THREE.DirectionalLight(0xffffff,1.2);dl.position.set(200,300,200);scene.add(dl);
const dl2=new THREE.DirectionalLight(0xffffff,.5);dl2.position.set(-100,200,-100);scene.add(dl2);
scene.add(new THREE.GridHelper(320,32,0x999999,0xdddddd));scene.add(new THREE.AxesHelper(90));
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
const raw=atob("''' + stl_b64 + '''");const arr=new Uint8Array(raw.length);
for(let i=0;i<raw.length;i++)arr[i]=raw.charCodeAt(i);
const g=new STLLoader().parse(arr.buffer);g.center();g.computeVertexNormals();
const m=new THREE.Mesh(g,new THREE.MeshPhongMaterial({color:0x4A90D9,specular:0x222222,shininess:120}));
scene.add(m);const b=new THREE.Box3().setFromObject(m);const s=b.getSize(new THREE.Vector3());
const d=Math.max(s.x,s.y,s.z);camera.position.set(d*1.2,d*.9,d*1.2);camera.lookAt(0,0,0);
function loop(){requestAnimationFrame(loop);controls.update();renderer.render(scene,camera);}
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
renderer.setSize(innerWidth,innerHeight);});loop();
</script></body></html>'''
    p = os.path.join(script_dir, f"{stem}_viewer.html")
    with open(p, "w") as f:
        f.write(html)
    return p


def finalize(part, stem, name, viewer_lines, checks):
    """Export STL/3MF, validate watertight + containment + envelope, render."""
    stl_path = os.path.join(script_dir, f"{stem}.stl")
    export_stl(part, stl_path)
    mesh = trimesh.load(stl_path)
    bb = mesh.bounds
    ext = bb[1] - bb[0]
    print(f"\n=== {name} ===")
    print(f"  bbox  : {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm")
    print(f"  water : {mesh.is_watertight}  | vol {mesh.volume/1000:.1f} cm3 "
          f"| ~{mesh.volume/1000*1.24:.0f} g PLA")
    assert mesh.is_watertight, f"{stem} NOT watertight"
    assert ext[0] <= BED and ext[1] <= BED and ext[2] <= BED, \
        f"{stem} exceeds {BED} mm bed: {ext}"
    if max(ext[0], ext[1]) > BED - 12:
        print(f"  NOTE  : within {BED} mm but near the limit "
              f"(<12 mm margin) -- watch if measurements grow.")
    # point-containment truth table (signed_distance: >0 == inside solid;
    # avoids the rtree dependency of mesh.contains' ray backend)
    from trimesh.proximity import signed_distance
    pts = [c[0] for c in checks]
    want = [c[1] for c in checks]
    sd = signed_distance(mesh, pts)
    got = [bool(d > 0) for d in sd]
    bad = [(checks[i][2], want[i], got[i])
           for i in range(len(checks)) if got[i] != want[i]]
    if bad:
        for nm, w, g in bad:
            print(f"  FAIL containment: {nm} want {w} got {g}")
        raise SystemExit(f"{stem} failed containment truth table")
    print(f"  contain: {len(checks)}/{len(checks)} assertions pass")
    export_3mf(mesh, os.path.join(script_dir, f"{stem}.3mf"))
    render_multiview(mesh, os.path.join(script_dir, f"{stem}.png"), name)
    export_viewer(stem, name, stl_path, viewer_lines)
    print(f"  files : {stem}.stl / .3mf / .png / _viewer.html")
    return ext


# =====================================================================
# VARIANT A  --  single integrated caddy
# =====================================================================
def variant_a():
    placed, pw, pd = shelf_pack(pocket_pack_items(), max_w=230, gap=PACK_GAP)
    fins, centers, sw = slot_x_positions()
    caddy_w = max(pw, sw)
    # ACCESS: slot rack at the FRONT so discs lift straight up into open
    # space; the tall tools (blade/pusher) move to the BACK where their tops
    # stay reachable. The rack's back wall sits between the two zones.
    sy_off = 0.0
    pocket_y0 = SLOT_DEPTH - OVERLAP + BACKWALL_T + MIDGAP
    caddy_d = pocket_y0 + pd

    base = Pos(caddy_w / 2, caddy_d / 2, BASE_T / 2) * Box(caddy_w, caddy_d, BASE_T)

    # slot rack at front, centered in width
    sx_off = (caddy_w - sw) / 2
    fins_solid, _, scenters = build_slot_fins(sx_off, sy_off)

    # pegs (i,k) + cups (b,c,r) at back, centered in width
    px_off = (caddy_w - pw) / 2
    walls, bores, cmeta = build_cups(placed, px_off, pocket_y0)
    pegs, gmeta = build_pegs(placed, px_off, pocket_y0)

    part = ((base + walls + fins_solid) - bores) + pegs

    # containment truth table
    air_z = BASE_T + 90.0
    checks = [
        ((caddy_w / 2, pd / 2, BASE_T / 2), True, "base solid"),
        ((caddy_w / 2, pd / 2, air_z), False, "air above is empty"),
        ((caddy_w / 2, sy_off + SLOT_DEPTH - OVERLAP + BACKWALL_T / 2, BASE_T + 2),
         True, "back wall frame solid"),
    ]
    # peg (i): post solid, swing area beside it empty (covered blade hangs here)
    gk, glabel, gx, gy, gpd, gsw, _ = gmeta[0]
    checks += [
        ((gx, gy, BASE_T + 30), True, f"{gk} peg solid"),
        ((gx + gsw / 2 - 4, gy, BASE_T + 30), False, f"{gk} swing area empty"),
    ]
    # cup (b): bore empty, wall post solid (probe a post angle, between windows)
    ck, clabel, cx, cy, cbr, cor, cwd = cmeta[0]
    rmid = (cbr + cor) / 2
    pa = math.radians(180.0 / CUP_WIN_N)        # halfway between windows
    checks += [
        ((cx, cy, BASE_T + cwd / 2), False, f"{ck} bore empty"),
        ((cx + rmid * math.cos(pa), cy + rmid * math.sin(pa), BASE_T + cwd / 2),
         True, f"{ck} cup wall post solid"),
    ]
    # slot rack: fin frame solid, gap empty, base under slot solid
    fxc = scenters[0][2]
    checks += [
        ((sx_off + WALL / 2, sy_off + SLOT_DEPTH / 2, BASE_T + 2),
         True, "slot fin frame solid"),
        ((sx_off + fxc, sy_off + SLOT_DEPTH / 2, BASE_T + FIN_H - 2),
         False, "slot gap empty"),
        ((sx_off + fxc, sy_off + SLOT_DEPTH / 2, BASE_T / 2),
         True, "base under slot solid"),
    ]

    lines = [
        "Variant A - single integrated caddy (ESTIMATED dims, v1)",
        f"Footprint {caddy_w:.0f} x {caddy_d:.0f} mm, fits H2D bed",
        "FRONT: slot rack l,m,o,p,q + inserts (lift up out of open front)",
        "BACK: pegs i (blade+cover j) & k (dough) + cups b,c + axle r",
        "Print as shown - base on bed, NO supports",
        "All sizes ESTIMATED - refine with caliper worksheet",
    ]
    finalize(part, "braun_mq9_caddy_A_integrated",
             "Braun MQ9 Caddy - Variant A (integrated)", lines, checks)


# =====================================================================
# VARIANT B  --  two pieces
# =====================================================================
def variant_b():
    # --- piece 1: v3 slot rack = GROUP A (5 disc slots, 90 mm deep) beside
    #     GROUP B (2 disc slots, 160 mm deep, to fully cradle a 15.6 cm disc).
    #     Open front, continuous half-height retaining wall, support-free. The
    #     base steps to match group B's greater depth. ---
    margin = WALL
    gA_solid, gA_w, gA_centers = build_disc_zone(margin, 0.0, N_DISC_SLOTS_A)
    gB_x0 = margin + gA_w + ZONE_GAP
    gB_solid, gB_w, gB_centers = build_disc_zone(
        gB_x0, 0.0, N_DISC_SLOTS_B, depth=DISC_DEPTH_B)
    total_w = gA_w + ZONE_GAP + gB_w
    W = total_w + 2 * margin
    base_dA = DISC_DEPTH - OVERLAP + BACKWALL_T        # base depth under group A
    base_dB = DISC_DEPTH_B - OVERLAP + BACKWALL_T      # base depth under group B (deeper)
    xsplit = margin + gA_w + ZONE_GAP / 2             # base step at the gap midline
    # stepped base: shallower left of the split (group A), deeper right (group B)
    base_A = Pos(xsplit / 2, base_dA / 2, BASE_T / 2) * Box(xsplit, base_dA, BASE_T)
    base_B = Pos((xsplit - OVERLAP + W) / 2, base_dB / 2, BASE_T / 2) * Box(
        W - xsplit + OVERLAP, base_dB, BASE_T)
    piece1 = base_A + base_B + gA_solid + gB_solid
    # continuous retaining wall on each group's open front (A taller than B)
    for fw in (build_front_wall(margin, gA_w, 0.0, FRONT_WALL_FRAC_A),
               build_front_wall(gB_x0, gB_w, 0.0, FRONT_WALL_FRAC_B)):
        if fw is not None:
            piece1 = piece1 + fw
    top_z = BASE_T + max(DISC_BACKWALL_H, FIN_H)
    base_dmax = max(base_dA, base_dB)

    acx = gA_centers[0]                         # a group-A slot gap center-x
    bcx = gB_centers[0]                         # a group-B slot gap center-x
    checks1 = [
        ((margin + gA_w / 2, base_dA / 2, BASE_T / 2), True, "base under A solid"),
        ((gB_x0 + gB_w / 2, base_dB / 2, BASE_T / 2), True, "base under B solid"),
        # group A (5 slots, 90 mm deep)
        ((margin + WALL / 2, DISC_DEPTH / 2, BASE_T + 2), True, "A fin frame solid"),
        ((acx, DISC_DEPTH / 2, BASE_T + FIN_H - 2), False, "A slot empty"),
        ((margin + gA_w / 2, DISC_DEPTH - OVERLAP + BACKWALL_T / 2, BASE_T + 20),
         True, "A back wall solid"),
        # group B (2 slots, 160 mm deep)
        ((gB_x0 + WALL / 2, DISC_DEPTH_B / 2, BASE_T + 2), True, "B fin frame solid"),
        ((bcx, DISC_DEPTH_B / 2, BASE_T + FIN_H - 2), False, "B slot empty"),
        ((gB_x0 + gB_w / 2, DISC_DEPTH_B - OVERLAP + BACKWALL_T / 2, BASE_T + 20),
         True, "B back wall solid"),
        # the gap between groups, and the air above, are open
        ((xsplit, DISC_DEPTH / 2, BASE_T + 12), False, "group gap empty"),
        ((margin + total_w / 2, base_dmax / 2, top_z + 15), False, "air above empty"),
    ]
    if FRONT_WALL:
        checks1 += [
            ((acx, BACKWALL_T / 2, BASE_T + 3), True, "A front wall solid"),
            ((acx, BACKWALL_T / 2, BASE_T + FRONT_WALL_FRAC_A * FIN_H + 5),
             False, "A front clears for lift-out"),
        ]
    lines1 = [
        "Variant B - slot rack v3 (5 + 2 disc slots)",
        f"Footprint {W:.0f} x {base_dmax:.0f} mm, ~{top_z:.0f} mm tall",
        f"GROUP A: {N_DISC_SLOTS_A} slots {DISC_DEPTH:.0f} mm deep, "
        f"discs to {DISC_DIA_A:.0f} mm",
        f"GROUP B: {N_DISC_SLOTS_B} slots {DISC_DEPTH_B:.0f} mm deep, "
        f"fully cradles a {DISC_DIA_B:.0f} mm disc",
        f"FRONT: continuous lip, A {FRONT_WALL_FRAC_A*FIN_H:.0f} mm "
        f"(75%) / B {FRONT_WALL_FRAC_B*FIN_H:.0f} mm (50%)",
        "Lift each disc straight up. NO supports.",
        "All sizes ESTIMATED - refine with caliper worksheet",
    ]
    finalize(piece1, "braun_mq9_caddy_B_slotrack",
             "Braun MQ9 Caddy - Variant B (slot rack v3)", lines1, checks1)

    # --- piece 2: peg + cup block ---
    placed, pw, pd = shelf_pack(pocket_pack_items(), max_w=230, gap=PACK_GAP)
    m2 = WALL
    base2 = Pos(m2 + pw / 2, m2 + pd / 2, BASE_T / 2) * Box(
        pw + 2 * m2, pd + 2 * m2, BASE_T)
    walls, bores, cmeta = build_cups(placed, m2, m2)
    pegs, gmeta = build_pegs(placed, m2, m2)
    piece2 = ((base2 + walls) - bores) + pegs
    gk, glabel, gx, gy, gpd, gsw, _ = gmeta[0]
    ck, clabel, cx, cy, cbr, cor, cwd = cmeta[0]
    rmid = (cbr + cor) / 2
    pa = math.radians(180.0 / CUP_WIN_N)        # halfway between windows
    checks2 = [
        ((m2 + pw / 2, m2 + pd / 2, BASE_T / 2), True, "base solid"),
        ((gx, gy, BASE_T + 30), True, f"{gk} peg solid"),
        ((gx + gsw / 2 - 4, gy, BASE_T + 30), False, f"{gk} swing area empty"),
        ((cx, cy, BASE_T + cwd / 2), False, f"{ck} bore empty"),
        ((cx + rmid * math.cos(pa), cy + rmid * math.sin(pa), BASE_T + cwd / 2),
         True, f"{ck} cup wall post solid"),
    ]
    lines2 = [
        "Variant B - peg + cup block (ESTIMATED dims, v1)",
        f"Footprint {pw + 2 * m2:.0f} x {pd + 2 * m2:.0f} mm",
        "Pegs i (blade + cover j) & k (dough); cups b,c + axle socket r",
        "Drop the bore over the peg; blade rests on base, cover j on",
        "Print as shown - base on bed, NO supports",
    ]
    finalize(piece2, "braun_mq9_caddy_B_pocketblock",
             "Braun MQ9 Caddy - Variant B (pocket block)", lines2, checks2)


def variant_b_auxbox():
    """Open-top storage bin that fills the L-notch behind group A of the v3 slot
    rack. The free pocket = group A's base width (X) by the depth group B sticks
    out past group A (Y), at the rack's full height (Z). Footprint is derived
    from the rack constants minus AUX_CLEAR so it drops in. Simple shell: a
    BASE_T floor + AUX_WALL walls, open top, prints support-free."""
    margin = WALL
    gA_w = N_DISC_SLOTS_A * (DISC_THICK + CLEAR_SLOT) + (N_DISC_SLOTS_A + 1) * WALL
    base_dA = DISC_DEPTH - OVERLAP + BACKWALL_T
    base_dB = DISC_DEPTH_B - OVERLAP + BACKWALL_T
    xsplit = margin + gA_w + ZONE_GAP / 2
    notch_w = xsplit - OVERLAP             # free width up to group B's base
    notch_d = base_dB - base_dA           # free depth behind group A
    box_w = notch_w - 2 * AUX_CLEAR
    box_d = notch_d - 2 * AUX_CLEAR
    box_h = BASE_T + DISC_BACKWALL_H      # same Z as the rack (kept per request)

    outer = Pos(box_w / 2, box_d / 2, box_h / 2) * Box(box_w, box_d, box_h)
    cav = Pos(box_w / 2, box_d / 2, (BASE_T + box_h + 1) / 2) * Box(
        box_w - 2 * AUX_WALL, box_d - 2 * AUX_WALL, box_h - BASE_T + 1)
    box = outer - cav

    checks = [
        ((box_w / 2, box_d / 2, BASE_T / 2), True, "floor solid"),
        ((box_w / 2, box_d / 2, (BASE_T + box_h) / 2), False, "cavity empty"),
        ((AUX_WALL / 2, box_d / 2, box_h / 2), True, "wall solid"),
        ((box_w / 2, box_d / 2, box_h + 10), False, "air above empty"),
    ]
    lines = [
        "Variant B - aux box (fills the L-notch behind group A)",
        f"Footprint {box_w:.0f} x {box_d:.0f} mm, {box_h:.0f} mm tall (= rack Z)",
        "Open-top bin for loose auxiliary items",
        "Sits in the corner: group A in front, group B to the side",
        "Print as shown - base on bed, NO supports",
    ]
    finalize(box, "braun_mq9_caddy_B_auxbox",
             "Braun MQ9 Caddy - Variant B (aux box)", lines, checks)


if __name__ == "__main__":
    print("Braun MQ9 accessory caddy  --  ESTIMATED v1 (refine with calipers)")
    variant_a()
    variant_b()
    if AUX_BOX:
        variant_b_auxbox()
    print("\nDONE. Print every file AS EXPORTED (base on bed), no supports.")
