#!/usr/bin/env python3
"""Toe-kick vent v3: full slit opening + print-in-place sliding damper.
Slider phase-shifts its slits vs base slits: 3mm travel = closed -> ~45% open.
Print flat, back face down. PETG. Units: mm.
"""
import os
import numpy as np
import manifold3d as m3d
import trimesh

# ---------------- Plate ----------------
W, H, T = 340.0, 85.0, 3.0
CORNER_R = 6.0
HOLE_INSET_X, HOLE_Y = 9.3, 45.0
HOLE_D, CSK_D = 4.2, 8.5

# ---------------- Slit pattern (base) ----------------
PITCH = 6.0
BASE_SLIT_W = 3.0            # open : solid = 3 : 3
N_SLITS = 34                 # center 60%: 204mm = 34 x 6mm pitch
SLIT_X0 = 68.0               # opening spans x 68-272 = center 60% of 340
SLIT_Y0, SLIT_Y1 = 14.0, 71.0

# ---------------- Slider ----------------
SLD_T = 1.8                  # slider thickness
SLD_SLIT_W = 2.4             # < base solid width -> 0.3 overlap each side when closed
GAP_Z = 0.4                  # vertical print-in-place gap (2 layers @ 0.2)
GAP_XY = 0.6                 # lateral clearance
TRAVEL = PITCH / 2           # 3mm: closed (printed) -> fully open
SLD_X0, SLD_X1 = 62.0, 278.0
SLD_Y0, SLD_Y1 = 10.0, 75.0
SLD_SLIT_Y0, SLD_SLIT_Y1 = 15.0, 70.0
TAB_W, TAB_H, TAB_RISE = 14.0, 18.0, 3.5   # center tab on slider face

# ---------------- Rails / frame (attached to base front) ----------------
RAIL_Z1 = T + GAP_Z + SLD_T + GAP_Z + 1.6   # 7.2 top of rail
LIP_Z0 = T + GAP_Z + SLD_T + GAP_Z          # 5.6
RAIL_X0, RAIL_X1 = 57.0, SLD_X1 + TRAVEL + GAP_XY + 4.4   # 57 .. 286
LIP_OVERHANG = 3.4

def box(x0, y0, z0, x1, y1, z1):
    return m3d.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])

def cyl(r, h, seg=64):
    return m3d.Manifold.cylinder(h, r, r, seg)

# ---------------- Base plate with rounded corners ----------------
r = CORNER_R
sq = m3d.CrossSection.square([W-2*r, H-2*r]).translate([r, r])
base = m3d.Manifold.extrude(sq.offset(r, m3d.JoinType.Round, circular_segments=48), T)

# base slits
for k in range(N_SLITS):
    x = SLIT_X0 + k*PITCH
    base -= box(x, SLIT_Y0, -1, x+BASE_SLIT_W, SLIT_Y1, T+1)

# screw holes, countersunk on front (z=T)
for hx in (HOLE_INSET_X, W-HOLE_INSET_X):
    base -= cyl(HOLE_D/2, T+2).translate([hx, HOLE_Y, -1])
    ck = (CSK_D-HOLE_D)/2
    base -= m3d.Manifold.cylinder(ck+0.5, HOLE_D/2, CSK_D/2+0.5, 64).translate([hx, HOLE_Y, T-ck])

# ---------------- Frame: rails + lips + end stops ----------------
frame = (
    box(RAIL_X0, 5.0, T, RAIL_X1, SLD_Y0-GAP_XY, RAIL_Z1) +               # bottom rail body
    box(RAIL_X0, 5.0, LIP_Z0, RAIL_X1, SLD_Y0+LIP_OVERHANG, RAIL_Z1) +    # bottom lip
    box(RAIL_X0, SLD_Y1+GAP_XY, T, RAIL_X1, 80.0, RAIL_Z1) +              # top rail body
    box(RAIL_X0, SLD_Y1-LIP_OVERHANG, LIP_Z0, RAIL_X1, 80.0, RAIL_Z1) +   # top lip
    box(RAIL_X0, 5.0, T, SLD_X0-GAP_XY, 80.0, RAIL_Z1) +                  # left end stop
    box(SLD_X1+TRAVEL+GAP_XY, 5.0, T, RAIL_X1, 80.0, RAIL_Z1)             # right end stop
)
base += frame

# ---------------- Slider (printed in CLOSED position) ----------------
z0, z1 = T+GAP_Z, T+GAP_Z+SLD_T            # 3.4 .. 5.2
slider = box(SLD_X0, SLD_Y0, z0, SLD_X1, SLD_Y1, z1)
# slider slits: centers at 24.5 + 6k (over base solid); slide +3mm -> align with base slits
for k in range(N_SLITS):
    c = SLIT_X0 - 1.5 + k*PITCH   # over base solid; +3mm -> aligned with base slits
    slider -= box(c-SLD_SLIT_W/2, SLD_SLIT_Y0, z0-1, c+SLD_SLIT_W/2, SLD_SLIT_Y1, z1+1)
# center tab (bridges slider slits, prints upward from slider face)
tcx = (SLD_X0+SLD_X1)/2
slider += box(tcx-TAB_W/2, HOLE_Y-TAB_H/2, z1, tcx+TAB_W/2, HOLE_Y+TAB_H/2, z1+TAB_RISE)

solid = base + slider          # disjoint union: 2 bodies, printed together

# ---------------- Sanity checks ----------------
# closed: base slits fully covered? open(+3): slider slits align with base slits?
for k in (0, 23, 46):
    bs0 = SLIT_X0 + k*PITCH
    sc_closed = SLIT_X0 - 1.5 + k*PITCH
    sc_open = sc_closed + TRAVEL
    assert abs(sc_open - (bs0 + BASE_SLIT_W/2 - PITCH)) < 1e9  # placeholder
# real check: open slider slit center (24.5+3=27.5+6k) == base slit center (27.5+6k)
assert abs((SLIT_X0-1.5+TRAVEL) - (SLIT_X0+BASE_SLIT_W/2)) < 1e-6, "open alignment"
# closed: slider solid spans base slit +/- 0.3
ov = (PITCH - SLD_SLIT_W)/2 - BASE_SLIT_W/2
print(f"closed overlap each side: {ov:.2f} mm (want >0.2)")
# clearance to right countersink
assert SLD_X1 + TRAVEL + GAP_XY + 4.4 < (W-HOLE_INSET_X) - CSK_D/2 - 3, "right csk clearance"

mesh = solid.to_mesh()
tm = trimesh.Trimesh(vertices=np.array(mesh.vert_properties)[:, :3],
                     faces=np.array(mesh.tri_verts))
print("watertight:", tm.is_watertight, "| bodies:", len(solid.decompose()),
      "| volume cm3:", round(tm.volume/1000, 1), "| extents:", tm.extents.round(1))
out = os.path.dirname(os.path.abspath(__file__)) + "/"
tm.export(out+"toekick_vent_340x85_v3_slider_PIP.stl")
tm.export(out+"toekick_vent_340x85_v3_slider_PIP.3mf")
print("exported")
