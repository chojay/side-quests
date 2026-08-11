#!/usr/bin/env python3
"""Render PNG previews for the hall-bath vent.

Run regen_bath_variants.sh first; this reads the exported final-part STL
from the folder this script lives in and writes final_part.png next to it.
"""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
PETG = '#f4f1ec'   # warm white PETG


def draw(ax, mesh, elev, azim, color=PETG, zoom=1.0):
    tri = mesh.triangles
    n = mesh.face_normals
    light = np.array([0.4, -0.3, 0.85])
    light = light / np.linalg.norm(light)
    lum = np.clip(n @ light, 0, 1) * 0.65 + 0.35
    base = np.array(matplotlib.colors.to_rgb(color))
    cols = np.clip(lum[:, None] * base[None, :], 0, 1)
    ax.add_collection3d(Poly3DCollection(tri, facecolors=cols, edgecolors='none'))
    c = mesh.bounds.mean(axis=0)
    r = (mesh.extents.max() / 2) / zoom
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect([1, 1, 1])
    ax.set_proj_type('ortho')
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


final = trimesh.load(os.path.join(
    HERE, 'bath_vent_RMG_ULTRATHIN_SHORTLIP_ROUND_248x95.stl'))
under = final.copy()
under.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))

fig = plt.figure(figsize=(11, 10), dpi=110)
ax = fig.add_subplot(2, 1, 1, projection='3d')
draw(ax, final, elev=30, azim=-55, zoom=1.15)
ax.set_title('Printed variant (ULTRATHIN + SHORTLIP + ROUND) - '
             '282.1 x 129.7 x 26.0 mm, 2.0 mm top plate, r8 corners',
             fontsize=11)
ax = fig.add_subplot(2, 1, 2, projection='3d')
draw(ax, under, elev=32, azim=-60, zoom=1.15)
ax.set_title('Underside - drop-down skirt 247.65 x 95.25, thin face carried '
             'by 9 mm-pitch stringers and cross ribs', fontsize=11)
fig.tight_layout()
out = os.path.join(HERE, 'final_part.png')
fig.savefig(out, bbox_inches='tight', facecolor='white')
print('wrote', out)
