#!/usr/bin/env python3
"""Render PNG previews (matplotlib, orthographic-ish) for the nursery vent."""
import numpy as np, trimesh, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

FLOOR = '#c9a876'   # oak-ish floor color
PETG  = '#f4f1ec'   # warm white PETG
PETG2 = '#e8e4dc'

def draw(ax, mesh, elev, azim, color=PETG, zoom=1.0, center=None):
    tri = mesh.triangles
    # lambert shading
    n = mesh.face_normals
    light = np.array([0.4, -0.3, 0.85]); light = light/np.linalg.norm(light)
    lum = np.clip(n @ light, 0, 1)*0.65 + 0.35
    base = np.array(matplotlib.colors.to_rgb(color))
    cols = np.clip(lum[:, None]*base[None, :], 0, 1)
    pc = Poly3DCollection(tri, facecolors=cols, edgecolors='none')
    ax.add_collection3d(pc)
    c = mesh.bounds.mean(axis=0) if center is None else np.array(center)
    r = (mesh.extents.max()/2)/zoom
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.set_box_aspect([1, 1, 1]); ax.set_proj_type('ortho')
    ax.view_init(elev=elev, azim=azim); ax.set_axis_off()

def fig_single(mesh, elev, azim, fname, title, zoom=1.0, center=None, color=PETG):
    fig = plt.figure(figsize=(11, 7), dpi=110)
    ax = fig.add_subplot(111, projection='3d')
    draw(ax, mesh, elev, azim, zoom=zoom, center=center, color=color)
    ax.set_title(title, fontsize=11, pad=4)
    fig.tight_layout(); fig.savefig(fname, bbox_inches='tight', facecolor='white')
    plt.close(fig); print('wrote', fname)

f = trimesh.load('fittes_design.stl')
k = trimesh.load('kumiko_design.stl')
key = trimesh.load('vent_lift_key_PRINT.stl')

# 1) top-view comparison, side by side
fig = plt.figure(figsize=(13, 9), dpi=110)
for i, (m, t) in enumerate([(f, 'FITTES-style - 10 lengthwise 5 mm slots'),
                            (k, 'KUMIKO-style - 45° diamond lattice (5 mm gaps)')]):
    ax = fig.add_subplot(2, 1, i+1, projection='3d')
    draw(ax, m, elev=90, azim=-90, zoom=1.35)
    ax.set_title(t, fontsize=12)
fig.suptitle("Nursery flush drop-in vent - 350 × 147 mm opening (one-piece, PETG)",
             fontsize=13, y=0.99)
fig.tight_layout(); fig.savefig('preview_comparison_top.png', bbox_inches='tight',
                                facecolor='white')
plt.close(fig); print('wrote preview_comparison_top.png')

# 2) iso views
fig_single(f, 28, -55, 'preview_fittes_iso.png',
           'Fittes-style - iso (12 mm flanges on long edges, ends flush in opening)')
fig_single(k, 28, -55, 'preview_kumiko_iso.png',
           'Kumiko-style - iso')

# 3) underside (skirt, ribs, magnet bosses)
fu = f.copy(); fu.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1,0,0]))
fig_single(fu, 32, -60, 'preview_underside.png',
           'Underside - drop-in skirt (16 mm), 7 cross-ribs, 2 magnet bosses')

# 4) closeup of slot chamfers + flange edge (fittes)
fig_single(f, 35, -35, 'preview_closeup_edge.png',
           'Closeup - 45° flange chamfer, 0.7 mm slot edge chamfers',
           zoom=4.2, center=[150, 75, -3])

# 5) print orientation check (playbook rule 7): what touches the bed
fp = trimesh.load('nursery_vent_FITTES_350x147_PRINT.stl')
fig_single(fp, 22, -60, 'preview_print_orientation.png',
           'PRINT orientation - top face down on bed; skirt+ribs grow upward (no supports)')

# 6) lift key
fig_single(key, 90, -90, 'preview_lift_key.png',
           'Lift key - blade drops in a slot beside a rib, 7 mm foot hooks under rib',
           zoom=1.1)
print('previews done')
