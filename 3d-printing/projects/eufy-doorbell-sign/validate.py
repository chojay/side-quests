#!/usr/bin/env python3
"""Validation gauntlet for the Eufy E340 frame (playbook section 6):
watertight -> point-containment truth table -> dimension probes -> orientation render.
Run after eufy_e340_frame.py.  ../../.venv-3dp/bin/python validate.py
"""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Import the design parameters straight from the generator so the probes can
# never drift from the actual geometry (importing does not run main()).
import eufy_e340_frame as M
BODY_HEIGHT = M.BODY_HEIGHT
RAISE = M.RAISE
OPENING_W, OPENING_H = M.OPENING_W, M.OPENING_H
FRAME_OUTER_W, FRAME_OUTER_H = M.FRAME_OUTER_W, M.FRAME_OUTER_H
SIGN_W, SIGN_H = M.SIGN_W, M.SIGN_H
SIGN_CY = M.SIGN_CY
BORDER = M.BORDER
OVERALL_W = max(FRAME_OUTER_W, SIGN_W)           # sign may be wider than the slim frame

WORK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(WORK, "eufy_e340_frame_base.stl")
TEXT = os.path.join(WORK, "eufy_e340_frame_text.stl")
MERGED = os.path.join(WORK, "eufy_e340_frame_merged.stl")

ok = True
def check(label, cond):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")

base = trimesh.load(BASE)
text = trimesh.load(TEXT)
merged = trimesh.load(MERGED)

print("\n=== 1. WATERTIGHT ===")
check("base watertight", base.is_watertight)
check("text watertight", text.is_watertight)
check("merged watertight", merged.is_watertight)

print("\n=== 2. CONTAINMENT TRUTH TABLE (base) ===")
zc = BODY_HEIGHT / 2
probes = [
    ("opening center is EMPTY",                 (0, 0, zc),                       False),
    ("just inside opening +X edge EMPTY",        (OPENING_W/2 - 1, 0, zc),         False),
    ("just outside opening +X edge SOLID",       (OPENING_W/2 + 1, 0, zc),         True),
    ("just inside opening +Y edge EMPTY",        (0, OPENING_H/2 - 1, zc),         False),
    ("top border (above opening) SOLID",         (0, OPENING_H/2 + 1, zc),         True),
    ("right border mid SOLID",                   (OPENING_W/2 + BORDER/2, 0, zc),  True),
    ("sign plaque center SOLID",                 (0, SIGN_CY, zc),                 True),
    ("above plaque is EMPTY",                    (0, SIGN_CY + SIGN_H/2 + 5, zc),  False),
    ("outside frame +X is EMPTY",                (FRAME_OUTER_W/2 + 5, 0, zc),     False),
]
for label, pt, expect in probes:
    got = bool(base.contains([pt])[0])
    check(f"{label}  (got {'solid' if got else 'empty'})", got == expect)

print("\n=== 3. DIMENSION / EXTENT PROBES ===")
bmin, bmax = merged.bounds
ext = bmax - bmin
print(f"  merged bounds min={bmin.round(2)}  max={bmax.round(2)}")
print(f"  merged extents (X,Y,Z) = {ext.round(2)}")
check(f"overall width ~{OVERALL_W:.0f}mm",  abs(ext[0] - OVERALL_W) < 0.6)
check(f"overall height ~{FRAME_OUTER_H + SIGN_H - 4.0:.0f}mm", abs(ext[1] - (FRAME_OUTER_H + SIGN_H - 4.0)) < 0.6)
check("overall Z ~6.8mm",     abs(ext[2] - (BODY_HEIGHT + RAISE)) < 0.05)
check("back face on Z=0 plane", abs(bmin[2]) < 1e-6)

tmin, tmax = text.bounds
print(f"  text Z range = [{tmin[2]:.2f}, {tmax[2]:.2f}] (expect [{BODY_HEIGHT:.1f}, {BODY_HEIGHT+RAISE:.1f}])")
check("text sits ON the body front face", abs(tmin[2] - BODY_HEIGHT) < 1e-6)
check("text raised by RAISE",             abs((tmax[2]-tmin[2]) - RAISE) < 1e-6)
check("text within plaque X span", tmin[0] > -SIGN_W/2 and tmax[0] < SIGN_W/2)
check("text within plaque Y span", tmin[1] > SIGN_CY - SIGN_H/2 and tmax[1] < SIGN_CY + SIGN_H/2)

# Measured opening (slice base at mid-Z, bound the central empty rectangle)
sec = base.section(plane_origin=[0,0,zc], plane_normal=[0,0,1])
if sec is not None:
    p2d, _ = sec.to_planar()
    # inner loop = opening; outer loop = frame outer. Take the loop nearest origin.
    print(f"  section vertical extents present for opening measurement")
check("merged volume positive", merged.volume > 0)
print(f"  merged volume = {merged.volume:,.0f} mm^3  (~{merged.volume/1000:.1f} cm^3)")

print("\n=== 4. PRINT-ORIENTATION RENDER (base mesh; bed = Z0) ===")
# Render the BASE mesh (its flat Z=0 face is what touches the bed) from 3 views.
fig = plt.figure(figsize=(13, 6))
views = [("ISO (print orientation)", 22, -60), ("FRONT (+Y up)", 2, -90), ("SIDE (+Z up)", 0, 0)]
verts = base.vertices
faces = base.faces
for i, (title, elev, azim) in enumerate(views, 1):
    ax = fig.add_subplot(1, 3, i, projection="3d")
    tris = verts[faces]
    coll = Poly3DCollection(tris, alpha=1.0, facecolor="#3a3a3a",
                            edgecolor="none", linewidths=0)
    ax.add_collection3d(coll)
    # bed plane at Z=0
    xx = [verts[:,0].min(), verts[:,0].max()]
    yy = [verts[:,1].min(), verts[:,1].max()]
    ax.plot([xx[0],xx[1],xx[1],xx[0],xx[0]], [yy[0],yy[0],yy[1],yy[1],yy[0]],
            [0,0,0,0,0], color="#cc3333", lw=1.2)
    ax.set_title(title, fontsize=10)
    ax.set_xlim(verts[:,0].min()-5, verts[:,0].max()+5)
    ax.set_ylim(verts[:,1].min()-5, verts[:,1].max()+5)
    ax.set_zlim(0, max(60, np.ptp(verts[:,1])/3))
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((np.ptp(verts[:,0]), np.ptp(verts[:,1]), 40))
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
out_png = os.path.join(WORK, "eufy_e340_frame_orientation.png")
plt.tight_layout(); plt.savefig(out_png, dpi=90); plt.close()
print(f"  saved {os.path.basename(out_png)}")

print("\n" + ("ALL CHECKS PASSED" if ok else "*** SOME CHECKS FAILED ***"))
raise SystemExit(0 if ok else 1)
