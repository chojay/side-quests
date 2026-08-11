#!/usr/bin/env python3
"""Hallway 90deg diverter vent (two-piece) - truth-table validation + print export.

Probes are DERIVED from the same parameter formulas as the .scad
(playbook rule: never eyeball probe coordinates).
"""
import numpy as np, trimesh, sys

# ---- parameters (mirror hallway_vent_90.scad) ----
floor_open_L, floor_open_W = 320.0, 180.0
ledge_depth = 18.0
end_clear, side_clear = 0.75, 1.0
lip_w, plate_T = 10.0, 4.5
skirt_depth, skirt_wall = 15.0, 2.4
slot_L, slot_y0, slot_y1 = 300.0, 40.0, 80.0
n_slot_ribs, slot_rib_t = 3, 2.4
scoop_cap, hood_wall, roof_T = 20.0, 2.4, 2.5
hood_y0, hood_y1, hood_margin_x = 34.0, 96.0, 4.0
groove_depth, groove_clear = 1.2, 0.2
fin_t, fin_gap, fin_y0, fin_z_clear = 1.6, 5.0, 60.0, 0.3

plate_L = floor_open_L + 2*lip_w
plate_W = floor_open_W + 2*lip_w
skirt_L = floor_open_L - 2*end_clear
skirt_W = floor_open_W - 2*side_clear
skirt_in_L, skirt_in_W = skirt_L - 2*skirt_wall, skirt_W - 2*skirt_wall
hood_h = scoop_cap - plate_T
hood_L = slot_L + 2*(hood_wall + hood_margin_x)
hood_D = hood_y1 - hood_y0
fin_pitch = fin_gap + fin_t
fin_H = hood_h - roof_T
n_fins = int(np.floor((hood_L - 2*hood_wall - fin_gap) / fin_pitch))
fins_span = n_fins*fin_pitch + fin_t
fin_x0 = -fins_span/2
defl_d = skirt_in_W/2 - slot_y1

def rib_x(i):  return -slot_L/2 + (i+1)*slot_L/(n_slot_ribs+1)
def fin_xc(k): return fin_x0 + k*fin_pitch + fin_t/2
def gap_xc(k): return fin_x0 + k*fin_pitch + fin_t + fin_gap/2

pan  = trimesh.load('pan_design.stl')
hood = trimesh.load('hood_design.stl')
ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and cond

# ---- watertight + envelope ----
check('pan watertight', pan.is_watertight)
check('hood watertight', hood.is_watertight)
pe, he = pan.extents, hood.extents
check(f'pan extents {np.round(pe,2)} == 340x200x19.5',
      np.allclose(pe, [plate_L, plate_W, plate_T+skirt_depth], atol=0.1))
check(f'hood extents {np.round(he,2)} == 313x62x{hood_h+groove_depth}',
      np.allclose(he, [hood_L, hood_D, hood_h+groove_depth], atol=0.1))
check('pan fits bed 350x320', pe[0] <= 350 and pe[1] <= 320)
check('hood fits bed', he[0] <= 350 and he[1] <= 320)
check('skirt clears ledge', skirt_depth <= ledge_depth - 2)
check('scoop <= 20mm above floor', plate_T + hood_h <= 20.01)
check('child-safe fin gap <= 5', fin_gap <= 5.01)

# ---- pan truth table (design orientation: plate top z=0) ----
P = [
 # (x, y, z, expect_solid, label)
 (0, 0, -plate_T/2,                      True,  'plate solid at center'),
 (plate_L/2-5, 0, -plate_T/2,           True,  'lip solid near edge'),
 ((rib_x(0)+rib_x(1))/2, (slot_y0+slot_y1)/2, -plate_T/2, False, 'slot open between ribs'),
 (rib_x(1), (slot_y0+slot_y1)/2, -plate_T/2, True, 'rib bridges slot'),
 (0, skirt_W/2-skirt_wall/2, -plate_T-skirt_depth/2, True, 'skirt wall solid'),
 (0, 0, -plate_T-skirt_depth/2,          False, 'skirt interior empty'),
 (0, skirt_W/2+ (plate_W/2-skirt_W/2)/2, -plate_T-3, False, 'below lip empty (floor zone)'),
 (0, (slot_y1+skirt_in_W/2)/2, -(plate_T + (slot_y1+skirt_in_W/2)/2 - slot_y1)/1 - 0.0, None, ''),  # placeholder replaced below
 (0, hood_y0+hood_wall/2, -groove_depth/2, False, 'back groove empty'),
 (0, hood_y0+hood_wall/2, -(groove_depth+plate_T)/2 - 0.6, True, 'plate under back groove solid'),
 (hood_L/2-hood_wall/2, (hood_y0+hood_y1)/2, -groove_depth/2, False, 'end groove empty'),
 (hood_L/2-hood_wall/2, (hood_y0+hood_y1)/2, -3.0, True, 'plate under end groove solid'),
 (slot_L/2 + 0.7, (slot_y0+slot_y1)/2, -plate_T/2, True, 'plate sliver between slot end and end-groove solid'),
]
# deflector probe: at y midway on the wedge, solid just below the hypotenuse
ym = (slot_y1 + skirt_in_W/2)/2
depth_here = ym - slot_y1               # 45deg: local wedge depth
P[7] = (0, ym, -plate_T - depth_here/2, True, 'deflector wedge solid')
pts = np.array([[p[0], p[1], p[2]] for p in P])
res = pan.contains(pts)
for (x, y, z, exp, lab), got in zip(P, res):
    check(f'pan: {lab} @({x:.1f},{y:.1f},{z:.1f})', got == exp)

# ---- hood truth table (assembled coords) ----
kmid = n_fins // 2
H = [
 (0, (hood_y0+hood_y1)/2, hood_h - roof_T/2, True,  'roof solid'),
 (0, (hood_y0+hood_y1)/2, hood_h + 1,        False, 'above roof empty'),
 (0, hood_y0 + hood_wall/2, hood_h/2,        True,  'back wall solid'),
 (hood_L/2 - hood_wall/2, (hood_y0+hood_y1)/2, hood_h/2, True, 'end wall solid'),
 (0, hood_y0 + hood_wall/2, -groove_depth/2, True,  'tongue below plate line solid'),
 (fin_xc(kmid), (fin_y0+hood_y1)/2, fin_H/2, True,  'fin solid'),
 (gap_xc(kmid), (fin_y0+hood_y1)/2, fin_H/2, False, 'gap between fins open'),
 (gap_xc(kmid), hood_y1 - 1.0, fin_H/2,      False, 'outlet face open'),
 (0, (hood_y0+hood_wall+fin_y0)/2, fin_H/2,  False, 'plenum chamber empty'),
 (fin_xc(kmid), (fin_y0+hood_y1)/2, fin_z_clear/2, False, 'fin bottom clearance'),
]
pts = np.array([[p[0], p[1], p[2]] for p in H])
res = hood.contains(pts)
for (x, y, z, exp, lab), got in zip(H, res):
    check(f'hood: {lab} @({x:.1f},{y:.1f},{z:.1f})', got == exp)

# ---- derived airflow numbers ----
outlet = (hood_L - 2*hood_wall - (n_fins+1)*fin_t) * fin_H / 100.0
slot_a = (slot_L*(slot_y1-slot_y0) - n_slot_ribs*slot_rib_t*(slot_y1-slot_y0))/100.0
print(f'outlet free area {outlet:.1f} cm2, slot {slot_a:.1f} cm2, duct {300*160/100:.0f} cm2')

if not ok:
    sys.exit('VALIDATION FAILED')

# ---- print-orientation export (flip 180 about X, rest on bed) ----
def export_print(mesh, name):
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    m.apply_translation([0, 0, -m.bounds[0][2]])
    m.apply_translation([-(m.bounds[0][0]+m.bounds[1][0])/2,
                         -(m.bounds[0][1]+m.bounds[1][1])/2, 0])
    m.export(f'{name}.stl'); m.export(f'{name}.3mf')
    print(f'exported {name}: extents {np.round(m.extents,1)}, zmin {m.bounds[0][2]:.2f}')
    return m

pan_p  = export_print(pan,  'hallway_vent90_PAN_340x200_PRINT')
hood_p = export_print(hood, 'hallway_vent90_HOOD_313x62_PRINT')

# bed-contact sanity: what touches z=0 in print orientation
for nm, m in [('pan', pan_p), ('hood', hood_p)]:
    v = m.vertices
    touch = v[np.abs(v[:, 2]) < 0.05]
    print(f'{nm}: {len(touch)} vertices on bed, span x {touch[:,0].min():.0f}..{touch[:,0].max():.0f}, '
          f'y {touch[:,1].min():.0f}..{touch[:,1].max():.0f}')
print('ALL OK')
