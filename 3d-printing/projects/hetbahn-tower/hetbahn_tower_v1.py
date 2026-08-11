#!/usr/bin/env python3
"""Hetbahn tower dispenser v1 - 6 bowls, bottom pull-out.

Tower-style holder modeled after the Design IVY birch-plywood camping
dispenser (blog.naver.com/kang7293/223941241626): bowls stack flat
inside a slat cage, the bottom bowl pulls straight out the front mouth
and the stack drops down. Their 10-bowl prototype was too heavy to pull
from; 6 is the proven count.

Sized for the widest common bowl (Ottogi-bap 210g, dia139 x H38.5);
CJ Hetbahn 210g (dia137 x H35) fits with extra slack.

Print upright, no supports: the mouth is a 45-degree gothic arch so the
front fascia grows from the side columns instead of floating.
"""
import math
from build123d import *

# === PARAMETERS ===
BOWL_DIA = 139.0         # Ottogi-bap rim (Hetbahn = 137)
BOWL_H = 38.5            # Ottogi-bap height (Hetbahn = 35)
N_BOWLS = 6
SLACK = 3.5              # radial clearance around the rim

WALL = 2.5
BASE_T = 3.0
HEADROOM = 9.0           # above the 6-bowl stack
TOP_BAND = 22.0          # solid hoop at the top (no windows)

MOUTH_H = 45.0           # clear height of the pull-out mouth
ARCH_APEX_R = 18.0       # rounding of the gothic arch peak
ARCH_SHOULDER_R = 8.0    # rounding where arch meets mouth sides

WIN_BACK = [45, 90, 135]     # window azimuths, deg (front = 270)
WIN_BACK_ARC = 32            # arc width, deg
WIN_FRONT = [218, 322]       # upper front-diagonal windows
WIN_FRONT_ARC = 20
WIN_R = 12                   # window corner radius

# === DERIVED ===
R_IN = BOWL_DIA / 2 + SLACK              # 73.0
R_OUT = R_IN + WALL                      # 75.5
TOTAL_H = BASE_T + N_BOWLS * BOWL_H + HEADROOM   # 243
MOUTH_TOP = BASE_T + MOUTH_H             # 48
MOUTH_HALF_W = R_IN + 0.5                # 73.5, grazes the side columns
ARCH_PEAK = MOUTH_TOP + MOUTH_HALF_W     # 121.5 (45 deg slopes)
WIN_Z_LO, WIN_Z_HI = 25.0, TOTAL_H - TOP_BAND
R_MID = (R_IN + R_OUT) / 2


def window_cutter(az_deg, arc_deg, z_lo, z_hi):
    chord = 2 * R_OUT * math.sin(math.radians(arc_deg / 2))
    with BuildPart(mode=Mode.PRIVATE) as w:
        Box(chord, 20, z_hi - z_lo)
        fillet(w.edges().filter_by(Axis.Y), radius=WIN_R)
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
        apex = [v for v in mouth.vertices() if v.Z > ARCH_PEAK - 1]
        fillet(apex, radius=ARCH_APEX_R)
        shoulders = [v for v in mouth.vertices()
                     if abs(v.Z - MOUTH_TOP) < 0.1]
        fillet(shoulders, radius=ARCH_SHOULDER_R)
    extrude(amount=R_OUT + 15, mode=Mode.SUBTRACT)

    # slat windows
    for az in WIN_BACK:
        add(window_cutter(az, WIN_BACK_ARC, WIN_Z_LO, WIN_Z_HI),
            mode=Mode.SUBTRACT)
    for az in WIN_FRONT:
        add(window_cutter(az, WIN_FRONT_ARC, 80.0, WIN_Z_HI),
            mode=Mode.SUBTRACT)

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
    stl_path = os.path.join(out_dir, "hetbahn tower v1.stl")
    export_stl(holder, stl_path)

    mesher = Mesher()
    mesher.add_shape(holder)
    mesher.write(os.path.join(out_dir, "hetbahn tower v1.3mf"))

    import trimesh
    m = trimesh.load(stl_path)
    assert m.is_watertight, "Mesh is not watertight!"
    print(f"watertight: {m.is_watertight}")
    print(f"extents: {m.extents}")
    print(f"volume: {m.volume / 1000:.1f} cm3")
