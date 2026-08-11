#!/usr/bin/env python3
"""Kitchen luxe 3-channel - validation + print export.
Signature luxe check: CONTAINMENT SWEEP of every channel's vertical
projection from the surface down to the grid top - must be EMPTY
(that emptiness IS the 'no visible line' spec). Probe coords derived
from the .scad formulas."""
import numpy as np, trimesh, sys

# ---- parameters (mirror kitchen_luxe_vent.scad) ----
opening_L, opening_W, duct_L, ledge_depth = 300.0, 133.0, 285.0, 25.0
end_clear, side_clear = 0.75, 1.0
lip_w, plate_T, skirt_depth, skirt_wall = 17.0, 4.5, 22.0, 2.4
luxe_gap, luxe_ring_w, grid_top = 5.0, 12.0, 20.0
spine_w, rib_t, n_ribs = 2.4, 2.4, 7
mag_d, mag_boss_d, mag_x = 8.4, 13.0, 60.0

plate_L, plate_W = opening_L + 2*lip_w, opening_W + 2*lip_w
skirt_L, skirt_W = opening_L - 2*end_clear, opening_W - 2*side_clear
skirt_in_L, skirt_in_W = skirt_L - 2*skirt_wall, skirt_W - 2*skirt_wall
total_H = plate_T + skirt_depth
FL, FW = skirt_in_L - 2.7, skirt_in_W - 2.2
r1_oL, r1_oW = FL - 2*luxe_gap, FW - 2*luxe_gap
r1_iL, r1_iW = r1_oL - 2*luxe_ring_w, r1_oW - 2*luxe_ring_w
r2_oL, r2_oW = r1_iL - 2*luxe_gap, r1_iW - 2*luxe_gap
r2_iL, r2_iW = r2_oL - 2*luxe_ring_w, r2_oW - 2*luxe_ring_w
panel_L, panel_W = r2_iL - 2*luxe_gap, r2_iW - 2*luxe_gap
spine_bot = grid_top + 0.5
extra_rib_x = [(r1_oL + r1_iL)/4, (r2_oL + r2_iL)/4]
ring_spine_y = [(r1_oW + r1_iW)/4, (r2_oW + r2_iW)/4]
field_L = FL
def rib_x(i): return -field_L/2 + i*field_L/(n_ribs+1)

m = trimesh.load('kitchen_design.stl')
ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name); ok = ok and cond

check('watertight', m.is_watertight)
e = m.extents
check(f'extents {np.round(e,2)} == 334x167x26.5',
      np.allclose(e, [plate_L, plate_W, total_H], atol=0.1))
check('fits bed 350x320', e[0] <= 350 and e[1] <= 320)
check('lip == 17 max (wall constraint)', lip_w <= 17.0)
check('child-safe channel <= 5', luxe_gap <= 5.01)
check('skirt clears end ledges (22 <= 23)', skirt_depth <= ledge_depth - 2)
check(f'sightline atan(5/{grid_top:.0f}) = {np.degrees(np.arctan(luxe_gap/grid_top)):.1f} deg <= 15',
      np.degrees(np.arctan(luxe_gap/grid_top)) <= 15.01)

# ---- THE LUXE SWEEP: channel projections empty from surface to grid top ----
channels = [('ch1', (FL+r1_oL)/2/2, (FW+r1_oW)/2/2),
            ('ch2', (r1_iL+r2_oL)/2/2, (r1_iW+r2_oW)/2/2),
            ('ch3', (r2_iL+panel_L)/2/2, (r2_iW+panel_W)/2/2)]
depths = [-1.5, -6.0, -12.0, -(grid_top - 0.5)]
bad = 0; total = 0
for name, hx, hy in channels:
    pts = []
    for t in np.linspace(-hx + 4, hx - 4, 40):      # long edges (skip corner arcs)
        pts += [[t, hy, 0], [t, -hy, 0]]
    for t in np.linspace(-hy + 4, hy - 4, 14):      # end edges
        pts += [[hx, t, 0], [-hx, t, 0]]
    pts = np.array(pts)
    for z in depths:
        p = pts.copy(); p[:, 2] = z
        hits = int(m.contains(p).sum()); total += len(p)
        if hits: print(f'  !! {name} z={z}: {hits} obstruction(s)')
        bad += hits
check(f'channel projections EMPTY: {total} pts x 0 hits', bad == 0)

zg = -(grid_top + total_H)/2          # mid-grid
P = [
 (0, 0, -plate_T/2,                     True,  'panel solid center'),
 (0, ring_spine_y[0], -plate_T/2,       True,  'ring1 band solid'),
 (0, ring_spine_y[1], -plate_T/2,       True,  'ring2 band solid'),
 (0, plate_W/2 - 5, -plate_T/2,         True,  'frame lip solid'),
 (30, 15, -12,                          True,  'panel spine solid (y=15)'),
 (30, ring_spine_y[0], -12,             True,  'ring1 spine loop solid'),
 (30, ring_spine_y[1], -12,             True,  'ring2 spine loop solid'),
 (0, FW/2 + 1.2, -12,                   True,  'downstand wall solid'),
 (rib_x(4), 20, zg,                     True,  'grid cross member solid (x=0 rib)'),
 (50, ring_spine_y[0], zg,              True,  'grid stringer solid (ring1 row)'),
 (50, 0, zg,                            True,  'grid panel stringer solid'),
 ((rib_x(3)+rib_x(4))/2, 20, zg,        False, 'grid cell open (between members)'),
 (0, skirt_W/2 - skirt_wall/2, -15,     True,  'skirt wall solid'),
 (0, opening_W/2 + 4, -10,              False, 'below lip empty (floor zone)'),
 (0, plate_W/2 - 0.5, -0.4,             False, 'plate edge chamfered'),
 (mag_x, 0, -5.5,                       False, 'magnet pocket empty'),
 (mag_x + (mag_d + mag_boss_d)/4, 0, -5.5, True, 'magnet boss ring solid'),
 (mag_x, 0, -1.0,                       True,  'pocket ceiling solid (1.2 below top)'),
]
res = m.contains(np.array([[p[0], p[1], p[2]] for p in P]))
for (x, y, z, exp, lab), got in zip(P, res):
    check(f'{lab} @({x:.1f},{y:.1f},{z:.1f})', got == exp)

area = (2*((FL+r1_oL)/2 + (FW+r1_oW)/2) + 2*((r1_iL+r2_oL)/2 + (r1_iW+r2_oW)/2)
        + 2*((r2_iL+panel_L)/2 + (r2_iW+panel_W)/2)) * luxe_gap / 100
print(f'channel free area ~{area:.0f} cm2 ({area/ (duct_L*opening_W/100) *100:.0f}% of duct)')
if not ok: sys.exit('VALIDATION FAILED')

mp = m.copy()
mp.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
mp.apply_translation([0, 0, -mp.bounds[0][2]])
mp.apply_translation([-(mp.bounds[0][0]+mp.bounds[1][0])/2,
                      -(mp.bounds[0][1]+mp.bounds[1][1])/2, 0])
mp.export('kitchen_vent_LUXE3_334x167_PRINT.stl')
mp.export('kitchen_vent_LUXE3_334x167_PRINT.3mf')
v = mp.vertices; touch = v[np.abs(v[:, 2]) < 0.05]
print(f'print export: extents {np.round(mp.extents,1)}, bed contact '
      f'x {touch[:,0].min():.0f}..{touch[:,0].max():.0f}, y {touch[:,1].min():.0f}..{touch[:,1].max():.0f}')
print('ALL OK')
