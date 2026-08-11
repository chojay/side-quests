#!/usr/bin/env python3
"""Bathroom toe-kick vent grille - 3/4 solid, right 1/4 angled louvers (deflect right).
Original design (not derived from MakerWorld files). Units: mm.
"""
import os
import numpy as np
import manifold3d as m3d
import trimesh

# ---------------- Parameters ----------------
W, H, T = 340.0, 85.0, 3.0          # plate width, height, thickness (std 2.25"x12" toe-kick faceplate)
HOLE_INSET_X = 9.3                   # hole center from each end
HOLE_Y = 45.0                        # hole center from bottom
HOLE_D = 4.2                         # clearance for #6 / M3.5 screw
CSK_D = 8.5                          # countersink diameter (90 deg)

# louvered window = centered quarter (85mm wide x 57mm tall, 14mm top/bottom margins)
WIN_X0 = W/2 - 42.5                  # 127.5
WIN_X1 = W/2 + 42.5                  # 212.5
WIN_Y0, WIN_Y1 = 14.0, H - 14.0

FIN_T = 1.6                          # fin thickness
FIN_PITCH = 5.0                      # horizontal spacing (fin x-span 5.26mm > pitch -> no see-through)
FIN_ANGLE = 45.0                     # deg, deflects exiting air to +X (right)
FIN_BACK = 0.0                       # louvers contained within plate thickness

CORNER_R = 6.0                       # plate corner radius

# ---------------- Helpers ----------------
def box(x0, y0, z0, x1, y1, z1):
    return m3d.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])

def cyl(r, h, seg=64):
    return m3d.Manifold.cylinder(h, r, r, seg)

# ---------------- Plate with rounded corners ----------------
r = CORNER_R
sq = m3d.CrossSection.square([W - 2*r, H - 2*r]).translate([r, r])
plate2d = sq.offset(r, m3d.JoinType.Round, circular_segments=48)
plate = m3d.Manifold.extrude(plate2d, T)   # z: 0..T, front face z=T

# ---------------- Window cut ----------------
plate -= box(WIN_X0, WIN_Y0, -1, WIN_X1, WIN_Y1, T + 1)

# ---------------- Angled fins ----------------
ang = np.radians(FIN_ANGLE)
fin_len = (T + FIN_BACK) / np.cos(ang) + 4   # long enough to span depth after rotation
fins = None
x = WIN_X0 - fin_len   # start left of window so trimmed fins fill from the left edge
while x < WIN_X1 + fin_len:
    f = m3d.Manifold.cube([FIN_T, WIN_Y1 - WIN_Y0 + 8, fin_len])
    f = f.translate([-FIN_T/2, 0, -fin_len/2])
    f = f.rotate([0, np.degrees(ang), 0])            # rotate about Y: deflect +X as air exits +Z
    f = f.translate([x, WIN_Y0 - 4, (T - FIN_BACK)/2])
    fins = f if fins is None else fins + f
    x += FIN_PITCH
# trim fins to window footprint (slightly taller in Y so they bond to plate)
trim = box(WIN_X0, WIN_Y0 - 4, -FIN_BACK, WIN_X1, WIN_Y1 + 4, T)
fins = fins ^ trim
# but fins must not cover plate front outside window in Y -> remove overlap conflicts is fine (union)
solid = plate + fins

# ---------------- Screw holes (countersunk, front face z=T) ----------------
for hx in (HOLE_INSET_X, W - HOLE_INSET_X):
    hole = cyl(HOLE_D/2, T + FIN_BACK + 2).translate([hx, HOLE_Y, -FIN_BACK - 1])
    csk_depth = (CSK_D - HOLE_D)/2  # 90 deg cone
    cone = m3d.Manifold.cylinder(csk_depth + 0.5, HOLE_D/2, CSK_D/2 + 0.5/1, 64)
    cone = cone.translate([hx, HOLE_Y, T - csk_depth])
    solid = solid - hole - cone

# ---------------- Export ----------------
mesh = solid.to_mesh()
tm = trimesh.Trimesh(vertices=np.array(mesh.vert_properties)[:, :3],
                     faces=np.array(mesh.tri_verts))
print("watertight:", tm.is_watertight, "| volume cm3:", round(tm.volume/1000, 1),
      "| extents:", tm.extents.round(1))
out = os.path.dirname(os.path.abspath(__file__)) + "/"
tm.export(out + "toekick_vent_340x85_center_louver.stl")
try:
    tm.export(out + "toekick_vent_340x85_center_louver.3mf")
    print("3mf ok")
except Exception as e:
    print("3mf failed:", e)
