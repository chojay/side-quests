#!/usr/bin/env python3
"""Preview PNGs: assembly views, section with airflow path, print orientations."""
import numpy as np, trimesh, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def draw(ax, mesh, color, alpha=1.0):
    tris = mesh.vertices[mesh.faces]
    n = mesh.face_normals
    light = np.array([0.4, -0.5, 0.77])
    shade = 0.55 + 0.45*np.clip(tris[:, 0, 2]*0 + n @ light, 0, 1)
    base = np.array(matplotlib.colors.to_rgb(color))
    cols = np.clip(base[None, :]*shade[:, None], 0, 1)
    pc = Poly3DCollection(tris, facecolors=np.hstack([cols, alpha*np.ones((len(cols), 1))]),
                          edgecolor='none')
    ax.add_collection3d(pc)

def setup(ax, xs, ys, zs, elev, azim, title):
    ax.set_box_aspect((xs[1]-xs[0], ys[1]-ys[0], zs[1]-zs[0]))
    ax.set_xlim(xs); ax.set_ylim(ys); ax.set_zlim(zs)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off(); ax.set_title(title, fontsize=11)

pan  = trimesh.load('pan_design.stl')
hood = trimesh.load('hood_design.stl')
pan_p  = trimesh.load('hallway_vent90_PAN_340x200_PRINT.stl')
hood_p = trimesh.load('hallway_vent90_HOOD_313x62_PRINT.stl')

# ---- 1. assembly iso + front ----
fig = plt.figure(figsize=(14, 6), dpi=110)
for i, (el, az, t) in enumerate([(28, -60, 'assembly - iso (outlet faces +Y room side)'),
                                 (8, -90, 'assembly - room-side view (outlet fins)')]):
    ax = fig.add_subplot(1, 2, i+1, projection='3d')
    draw(ax, pan, '#b0b7c0'); draw(ax, hood, '#7f97ad')
    setup(ax, (-175, 175), (-105, 105), (-30, 25), el, az, t)
plt.tight_layout(); plt.savefig('preview_assembly.png', bbox_inches='tight'); plt.close()

# ---- 2. section at x=0 with airflow arrows ----
fig, ax = plt.subplots(figsize=(11, 5.5), dpi=110)
for mesh, color in [(pan, '#8a93a0'), (hood, '#5c7893')]:
    sec = mesh.section(plane_origin=[10, 0, 0], plane_normal=[1, 0, 0])
    if sec is None: continue
    for ent, verts in [(e, sec.vertices) for e in sec.entities]:
        pts = verts[ent.points][:, 1:]  # (y, z)
        ax.plot(pts[:, 0], pts[:, 1], color=color, lw=1.6)
# floor / recess / duct outline
floor_y = -4.5
ax.plot([-160, -90], [floor_y, floor_y], color='#a07850', lw=3)
ax.plot([160, 90], [floor_y, floor_y], color='#a07850', lw=3)
ax.plot([-90, -90], [floor_y, floor_y-25.4], color='#a07850', lw=3)
ax.plot([90, 90], [floor_y, floor_y-25.4], color='#a07850', lw=3)
ax.plot([-90, -80], [floor_y-25.4, floor_y-25.4], color='#a07850', lw=3)
ax.plot([90, 80], [floor_y-25.4, floor_y-25.4], color='#a07850', lw=3)
ax.plot([-80, -80], [floor_y-25.4, floor_y-45], color='#a07850', lw=3)
ax.plot([80, 80], [floor_y-25.4, floor_y-45], color='#a07850', lw=3)
# airflow path: up the duct, right through plenum, up slot, out of hood
path = [(0, -40), (0, -18), (30, -14), (55, -12), (62, -3), (62, 6), (85, 6.5), (125, 6.5)]
py, pz = zip(*path)
ax.plot(py, pz, color='#c04a3a', lw=2.2, alpha=0.85)
ax.annotate('', xy=(138, 6.5), xytext=(120, 6.5),
            arrowprops=dict(arrowstyle='-|>', color='#c04a3a', lw=2.2))
ax.text(5, -35, 'from duct', color='#c04a3a', fontsize=10, rotation=90)
ax.text(96, 10.5, 'to open room', color='#c04a3a', fontsize=10)
ax.text(-150, 1, 'cabinet side / closet: sealed plate', fontsize=9, color='#555')
ax.text(40, -22, '45° deflector', fontsize=8, color='#555')
ax.set_aspect('equal'); ax.set_xlim(-185, 185); ax.set_ylim(-52, 30)
ax.set_title('section at x=0 - 90° bend: duct → plenum → slot → scoop outlet (total 20 mm above floor)')
ax.set_xlabel('y (mm), +y = room'); ax.set_ylabel('z (mm)')
plt.tight_layout(); plt.savefig('preview_section_airflow.png', bbox_inches='tight'); plt.close()

# ---- 3. print orientations ----
fig = plt.figure(figsize=(14, 6), dpi=110)
ax = fig.add_subplot(1, 2, 1, projection='3d')
draw(ax, pan_p, '#b0b7c0')
setup(ax, (-180, 180), (-110, 110), (0, 40), 25, -55, 'PAN print orientation - top face down, flat on bed')
ax = fig.add_subplot(1, 2, 2, projection='3d')
draw(ax, hood_p, '#7f97ad')
setup(ax, (-170, 170), (-45, 45), (0, 25), 25, -55, 'HOOD print orientation - roof face down, fins up')
plt.tight_layout(); plt.savefig('preview_print_orientation.png', bbox_inches='tight'); plt.close()

# ---- 4. hood closeup: fins/outlet ----
fig = plt.figure(figsize=(10, 6), dpi=110)
ax = fig.add_subplot(projection='3d')
draw(ax, hood, '#7f97ad')
setup(ax, (-170, 170), (-40, 170), (-60, 75), 15, -72,
      'hood - outlet face with 46 vertical straightening fins (5 mm gaps)')
plt.tight_layout(); plt.savefig('preview_hood_closeup.png', bbox_inches='tight'); plt.close()
print('previews done')
