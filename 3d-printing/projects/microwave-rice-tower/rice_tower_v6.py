#!/usr/bin/env python3
"""Microwave rice tower dispenser v6 - 8 bowls, bottom pull-out, max open area.

v5 with openings enlarged to cut filament ~20%: slots grow to 30 deg
arc x 30mm tall (posts 6 deg / ~8mm, inter-row strips ~8.5mm), a slot
ring is added over bowl 1 (back half), the base disc gets a dia78
center hole (the bowl rests on its outer rim ring, dia ~95+, so it
cannot drop in or snag), and the top band trims to 18mm. Slot chord
~39mm keeps every ceiling a short printable bridge (a single wide
wraparound slot cannot print support-free - curved ceilings cannot
bridge).

Rows over bowls 1-3 exist only on the back half (the mouth arch fascia
must stay solid at the front for retention); bowls 1-3 also show
through the mouth. Rows over bowls 4-8 run full circle.

At 320mm tall this is near the Bambu H2D Z limit (325mm).

Sized for the widest common bowl (Ottogi-bap 210g, dia139 x H38.5);
CJ Hetbahn 210g (dia137 x H35) fits with extra slack.
"""
import math
from build123d import *

# === PARAMETERS ===
BOWL_DIA = 139.0         # Ottogi-bap rim (Hetbahn = 137)
BOWL_H = 38.5            # Ottogi-bap height (Hetbahn = 35)
N_BOWLS = 8
SLACK = 3.5              # radial clearance around the rim

WALL = 2.5
BASE_T = 3.0
BASE_HOLE_R = 39.0       # center hole in the base (bowl rim ring is dia 95+)
HEADROOM = 9.0           # above the 8-bowl stack
TOP_BAND = 18.0          # solid hoop at the top (no slots)

MOUTH_H = 45.0           # clear height of the pull-out mouth
ARCH_APEX_R = 55.0       # broad apex rounding - arch reads round, not pointed
ARCH_SHOULDER_R = 15.0   # rounding where arch meets mouth sides

SLOT_ARC = 30            # slot arc width, deg (10 cells x 36 deg pitch)
SLOT_PITCH = 36          # cell pitch, deg
SLOT_H = 30.0            # slot height within the 38.5 bowl pitch
SLOT_R = 10.0            # slot corner radius
SLOT_BOT_MIN = 12.0      # lowest slot edge (keeps the foundation ring)
BACK_ONLY_BELOW = 120.0  # rows below this keep the front fascia solid

# === DERIVED ===
R_IN = BOWL_DIA / 2 + SLACK              # 73.0
R_OUT = R_IN + WALL                      # 75.5
TOTAL_H = BASE_T + N_BOWLS * BOWL_H + HEADROOM   # 320
MOUTH_TOP = BASE_T + MOUTH_H             # 48
MOUTH_HALF_W = R_IN + 0.5                # 73.5, grazes the side columns
ARCH_PEAK = MOUTH_TOP + MOUTH_HALF_W     # 121.5 (45 deg slopes)
SLOT_TOP_MAX = TOTAL_H - TOP_BAND        # 298
R_MID = (R_IN + R_OUT) / 2
CELLS = list(range(18, 360, SLOT_PITCH))  # slot centers; posts at 0/180
                                          # (side columns) and front 270 open


def slot_cutter(az_deg, z_lo, z_hi, corner_r):
    chord = 2 * R_OUT * math.sin(math.radians(SLOT_ARC / 2))
    with BuildPart(mode=Mode.PRIVATE) as w:
        Box(chord, 20, z_hi - z_lo)
        fillet(w.edges().filter_by(Axis.Y), radius=corner_r)
    az = math.radians(az_deg)
    return w.part.rotate(Axis.Z, az_deg - 90).move(
        Location((R_MID * math.cos(az), R_MID * math.sin(az),
                  (z_lo + z_hi) / 2)))


# === GEOMETRY ===
with BuildPart() as tower:
    Cylinder(R_OUT, TOTAL_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    with Locations((0, 0, BASE_T)):
        Cylinder(R_IN, TOTAL_H, align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)

    # front mouth: rectangle topped by a 45-degree gothic arch (extruded -Y)
    with BuildSketch(Plane.XZ) as mouth:
        with BuildLine():
            Polyline((-MOUTH_HALF_W, BASE_T), (MOUTH_HALF_W, BASE_T),
                     (MOUTH_HALF_W, MOUTH_TOP), (0, ARCH_PEAK),
                     (-MOUTH_HALF_W, MOUTH_TOP), (-MOUTH_HALF_W, BASE_T))
        make_face()
        # NB: inside BuildSketch, vertices are in LOCAL plane coords:
        # local Y = world Z here (selecting on .Z silently matches nothing)
        apex = [v for v in mouth.vertices() if v.Y > ARCH_PEAK - 1]
        assert len(apex) == 1, "arch apex vertex not found"
        fillet(apex, radius=ARCH_APEX_R)
        shoulders = [v for v in mouth.vertices()
                     if abs(v.Y - MOUTH_TOP) < 0.1]
        assert len(shoulders) == 2, "arch shoulder vertices not found"
        fillet(shoulders, radius=ARCH_SHOULDER_R)
    extrude(amount=R_OUT + 15, mode=Mode.SUBTRACT)

    # slot rings, one per bowl level (rows 1-3 clamp to the back half)
    for k in range(1, N_BOWLS + 1):
        mid = BASE_T + (k - 0.5) * BOWL_H
        z_lo = max(mid - SLOT_H / 2, SLOT_BOT_MIN)
        z_hi = min(mid + SLOT_H / 2, SLOT_TOP_MAX)
        r = min(SLOT_R, (z_hi - z_lo) / 2 - 0.5)
        for az in CELLS:
            if z_lo < BACK_ONLY_BELOW and not 15 <= az <= 165:
                continue                         # keep front fascia solid
            add(slot_cutter(az, z_lo, z_hi, r), mode=Mode.SUBTRACT)

    # base lightening hole (bowl bridges it on its outer rim ring)
    Cylinder(BASE_HOLE_R, 3 * BASE_T, mode=Mode.SUBTRACT)

    # finger scallop in the base front edge
    with Locations((0, -(R_OUT + 6.5), 0)):
        Cylinder(18, 3 * BASE_T, mode=Mode.SUBTRACT)

    # hanging hole through the back of the top band
    with Locations((0, R_MID, TOTAL_H - 9)):
        Cylinder(4, 30, rotation=(90, 0, 0), mode=Mode.SUBTRACT)

holder = tower.part.solid()

# === VALIDATE + EXPORT ===
if __name__ == "__main__":
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    stl_path = os.path.join(out_dir, "rice tower v6.stl")
    export_stl(holder, stl_path)

    mesher = Mesher()
    mesher.add_shape(holder)
    mesher.write(os.path.join(out_dir, "rice tower v6.3mf"))

    import trimesh
    m = trimesh.load(stl_path)
    assert m.is_watertight, "Mesh is not watertight!"
    print(f"watertight: {m.is_watertight}")
    print(f"extents: {m.extents}")
    print(f"volume: {m.volume / 1000:.1f} cm3")
    assert m.extents[2] <= 325, "exceeds H2D Z limit"
    print("H2D fit: OK (Z 325 limit)")
