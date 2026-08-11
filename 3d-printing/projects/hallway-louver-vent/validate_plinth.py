#!/usr/bin/env python3
"""Plinth ONE-PIECE variant - truth-table validation + print export.
Probe coordinates derived from the same formulas as the .scad."""
import numpy as np, trimesh, sys

# ---- parameters (mirror hallway_vent_90.scad) ----
floor_open_L, floor_open_W = 320.0, 180.0
ledge_depth = 18.0
end_clear, side_clear = 0.75, 1.0
lip_w = 10.0
skirt_depth, skirt_wall = 15.0, 2.4
scoop_cap = 20.0
fin_t, fin_gap = 1.6, 5.0
slot_rib_t = 2.4
p_roof_T, p_wall_t = 2.5, 2.4
p_fin_field, p_fin_d, p_floor_clear = 300.0, 30.0, 0.5
p_rib_d, p_n_ribs, p_stub_len = 12.0, 7, 8.0

plate_L = floor_open_L + 2*lip_w                 # 340
plate_W = floor_open_W + 2*lip_w                 # 200
skirt_L = floor_open_L - 2*end_clear             # 318.5
skirt_W = floor_open_W - 2*side_clear            # 178
skirt_in_L, skirt_in_W = skirt_L - 2*skirt_wall, skirt_W - 2*skirt_wall
fin_pitch = fin_gap + fin_t
p_H = scoop_cap
p_floor_z, p_skirt_bot = -p_H, -p_H - skirt_depth
p_fin_H = p_H - p_roof_T
p_n_fins = int(np.floor((p_fin_field - fin_gap) / fin_pitch))
p_fins_span = p_n_fins*fin_pitch + fin_t
fx0 = -p_fins_span/2
def fin_xc(k): return fx0 + k*fin_pitch + fin_t/2
def gap_xc(k): return fx0 + k*fin_pitch + fin_t + fin_gap/2
def rib_x(i):  return -skirt_in_L/2 + i*skirt_in_L/(p_n_ribs+1)

m = trimesh.load('plinth_design.stl')
ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name); ok = ok and cond

check('watertight', m.is_watertight)
e = m.extents
check(f'extents {np.round(e,2)} == 340x200x35',
      np.allclose(e, [plate_L, plate_W, -p_skirt_bot], atol=0.1))
check('fits bed 350x320', e[0] <= 350 and e[1] <= 320)
check('skirt clears ledge', skirt_depth <= ledge_depth - 2)
check('height above floor == 20 cap', abs(p_H - 20) < 0.01)
check('child-safe fin gap <= 5', fin_gap <= 5.01)
check('stubs outside fin field', skirt_L/2 - skirt_wall - p_stub_len >= p_fins_span/2)

kmid = p_n_fins//2
fin_ym = plate_W/2 - p_fin_d/2                       # mid-depth of fins
P = [
 (0, 0, -p_roof_T/2,                          True,  'roof solid center'),
 ((rib_x(3)+rib_x(4))/2, 0, -p_roof_T - 2,    False, 'interior plenum empty (between ribs - rib 4 is AT x=0)'),
 (0, -(plate_W/2 - p_wall_t/2), -p_H/2,       True,  'closet long wall solid'),
 (plate_L/2 - p_wall_t/2, 0, -p_H/2,          True,  'end wall solid'),
 ((p_fin_field/2 + plate_L/2 - p_wall_t)/2, plate_W/2 - p_wall_t/2, -p_H/2,
                                              True,  'room-face corner wall solid'),
 (gap_xc(kmid), plate_W/2 - p_wall_t/2, -p_H/2, False, 'outlet face open at gap'),
 (fin_xc(kmid), fin_ym, -p_H/2,               True,  'fin solid'),
 (gap_xc(kmid), fin_ym, -p_H/2,               False, 'fin channel open'),
 (fin_xc(kmid), fin_ym, p_floor_z + p_floor_clear/2, False, 'fin floor clearance'),
 (0, -(skirt_W/2 - skirt_wall/2), p_floor_z - skirt_depth/2, True, 'closet skirt wall (below floor) solid'),
 (0,  (skirt_W/2 - skirt_wall/2), p_floor_z - skirt_depth/2, False, 'room skirt line OPEN mid (flow path)'),
 (skirt_L/2 - skirt_wall - p_stub_len/2, skirt_W/2 - skirt_wall/2, p_floor_z - skirt_depth/2,
                                              True,  'room skirt stub solid'),
 (skirt_L/2 - skirt_wall/2, 0, p_floor_z - skirt_depth/2, True, 'end skirt wall solid'),
 (rib_x(4), 0, -p_roof_T - p_rib_d/2,         True,  'roof rib solid'),
 (rib_x(4), 0, -p_roof_T - p_rib_d - 2,       False, 'below rib open (flow)'),
 ((rib_x(3)+rib_x(4))/2, 0, -p_roof_T - p_rib_d/2, False, 'between ribs open'),
 (gap_xc(kmid), skirt_W/2 + 2, -p_H + 1,      False, 'above-floor channel over lip open (fin 22 is AT x=0)'),
 (0, 0, p_floor_z - skirt_depth/2,            False, 'inside skirt (duct zone) empty'),
]
res = m.contains(np.array([[p[0], p[1], p[2]] for p in P]))
for (x, y, z, exp, lab), got in zip(P, res):
    check(f'{lab} @({x:.1f},{y:.1f},{z:.1f})', got == exp)

outlet = (p_fin_field - (p_n_fins+1)*fin_t) * p_fin_H / 100
print(f'outlet free area {outlet:.1f} cm2 ({p_n_fins+1} fins), duct 480 cm2')
if not ok: sys.exit('VALIDATION FAILED')

mp = m.copy()
mp.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
mp.apply_translation([0, 0, -mp.bounds[0][2]])
mp.apply_translation([-(mp.bounds[0][0]+mp.bounds[1][0])/2,
                      -(mp.bounds[0][1]+mp.bounds[1][1])/2, 0])
mp.export('hallway_vent90_PLINTH_ONEPIECE_340x200_PRINT.stl')
mp.export('hallway_vent90_PLINTH_ONEPIECE_340x200_PRINT.3mf')
v = mp.vertices; touch = v[np.abs(v[:, 2]) < 0.05]
print(f'print export: extents {np.round(mp.extents,1)}, bed contact span '
      f'x {touch[:,0].min():.0f}..{touch[:,0].max():.0f}, y {touch[:,1].min():.0f}..{touch[:,1].max():.0f}')
print('ALL OK')
