#!/usr/bin/env python3
"""Validate the nursery vent meshes (Gotchas Playbook) and export print files.

Design orientation: top surface z=0, part extends -z, centered XY.
Print orientation:  rotated 180deg about X (top face down), z >= 0.
"""
import numpy as np, trimesh

# ---- parameters (mirror of .scad) ----
opening_L, opening_W = 350.0, 147.0
plate_L, plate_W, plate_T = 348.5, 171.0, 4.5
skirt_L, skirt_W, skirt_wall, skirt_depth = 348.5, 145.0, 2.4, 16.0
total_H = plate_T + skirt_depth                     # 20.5
field_L, field_W = 324.5, 122.0
slot_w, slat_w, n_slots, pitch = 5.0, 8.0, 10, 13.0
rib_t, rib_d, n_ribs = 2.4, 9.0, 7
mag_x, mag_d = 60.0, 8.4
bar_w, gap_w, kpitch = 3.4, 5.0, 8.4

def rib_x(i):  # i = 1..7
    return -field_L/2 + i*field_L/(n_ribs+1)

def slot_yc(i):
    return -field_W/2 + slot_w/2 + i*pitch

def check(mesh, name, probes):
    print(f"\n=== {name} ===")
    print(f"watertight={mesh.is_watertight}  vol={mesh.volume/1000:.1f} cm3  "
          f"extents={np.round(mesh.extents,2)}")
    assert mesh.is_watertight, "NOT WATERTIGHT"
    ok = True
    pts = np.array([p for p, _, _ in probes])
    inside = mesh.contains(pts)
    for (p, expect, label), got in zip(probes, inside):
        status = "ok" if got == expect else "** FAIL **"
        if got != expect: ok = False
        print(f"  {'solid' if expect else 'empty':5s} {label:44s} {status}")
    assert ok, f"{name}: containment failures"
    return mesh

# ---------- FITTES ----------
f = trimesh.load('fittes_design.stl')
probes_f = [
    # plate / flange
    (( 0, 84, -2),            True,  "flange over floor, long edge"),
    (( 0, 84, -6),            False, "below flange = open floor gap side"),
    ((170, 0, -2),            True,  "solid end margin (x=170)"),
    # slots and slats
    ((100, slot_yc(5), -2),   True if False else False, "slot 5 open thru plate"),
    ((100, (slot_yc(4)+slot_yc(5))/2, -2), True, "slat between slots 4/5"),
    ((0, 0, -2),              True,  "center slat (y=0)"),
    # slot top chamfer removed material
    ((100, slot_yc(5)+slot_w/2+0.3, -0.2), False, "slot edge chamfer"),
    # perimeter chamfer
    ((0, plate_W/2-0.4, -0.4), False, "perimeter 45deg chamfer"),
    # ribs
    ((rib_x(4), slot_yc(5), -6),  True,  "rib bridges slot (below plate)"),
    ((rib_x(4)+8, slot_yc(5), -6), False, "no rib 8mm away"),
    ((rib_x(4), 0, -13),      True,  "rib full depth (z=-13)"),
    ((rib_x(4), 0, -14.5),    False, "below rib bottom (13.5)"),
    # skirt
    ((0,  skirt_W/2-1.0, -12), True,  "skirt side wall"),
    ((20, skirt_W/2-5.0, -12), False, "inside skirt = open duct (off-rib)"),
    ((skirt_L/2-1.0, 0, -12),  True,  "skirt end wall"),
    ((0,  skirt_W/2+2.0, -12), False, "outside skirt, under flange"),
    # magnet pocket: boss ring solid, pocket empty, 1.2mm cover solid
    ((mag_x+5.3, 0, -5.5),    True,  "magnet boss ring below plate"),
    ((mag_x, 0, -3.0),        False, "magnet pocket cavity"),
    ((mag_x, 0, -0.6),        True,  "1.2mm cover above magnet"),
]
check(f, "FITTES", probes_f)

# ---------- KUMIKO ----------
k = trimesh.load('kumiko_design.stl')
# bar centers: rotated frames a=+/-45, lines at distance m*kpitch from center.
# point ON a +45 bar near center: perpendicular coord v=(y-x)/sqrt2=0 -> bar m=0
# passes through origin. Point on it: (10,10). Diamond center (opening):
# between bars of both families: u=(x+y)/sqrt2 = kpitch/2, v=(y-x)/sqrt2 = kpitch/2
d = kpitch/2/np.sqrt(2)  # x offset for diamond center
probes_k = [
    ((10, 10, -2),            True,  "+45 bar through origin (10,10)"),
    ((0, 2*d, -2),            False, "diamond opening center"),
    ((0, 84, -2),             True,  "flange long edge"),
    ((170, 0, -2),            True,  "solid end margin"),
    ((0, field_W/2+3, -2),    True,  "solid border outside field"),
    ((rib_x(4), 2*d, -6),     True,  "rib below lattice"),
    ((0,  skirt_W/2-1.0, -12), True, "skirt side wall"),
    ((20, skirt_W/2-5.0, -12), False,"inside skirt open (off-rib)"),
    ((mag_x, 0, -3.0),        False, "magnet pocket cavity"),
    ((mag_x, 0, -0.6),        True,  "cover above magnet"),
]
check(k, "KUMIKO", probes_k)

# ---------- LIFT KEY ----------
key = trimesh.load('liftkey_design.stl')
probes_key = [
    ((0, 2.5, 1.5),   True,  "foot"),
    ((11, 2.5, 1.5),  True,  "foot tip (7mm past stem)"),
    ((0, 20, 1.5),    True,  "stem"),
    ((10, 20, 1.5),   False, "beside stem"),
    ((0, 38, 1.5),    False, "handle hole"),
    ((0, 50, 1.5),    True,  "handle top bar"),
]
check(key, "LIFT KEY", probes_key)

# ---------- envelope asserts ----------
for m, nm in [(f, 'fittes'), (k, 'kumiko')]:
    ext = m.extents
    assert ext[0] <= 350 and ext[1] <= 320 and ext[2] <= 325, f"{nm} exceeds H2D bed"
    assert abs(ext[0] - plate_L) < 0.1 and abs(ext[1] - plate_W) < 0.1
    assert abs(ext[2] - total_H) < 0.1
# skirt must clear the opening
assert skirt_L <= opening_L - 1.0 and skirt_W <= opening_W - 1.5
print("\nEnvelope asserts passed.")

# free-area report
fa_f = n_slots*slot_w*field_L/100.0
fa_k = (gap_w**2/kpitch**2)*field_L*field_W/100.0
duct = opening_L*opening_W/100.0
print(f"Free area: fittes {fa_f:.0f} cm2 ({100*fa_f/duct:.0f}% of duct), "
      f"kumiko {fa_k:.0f} cm2 ({100*fa_k/duct:.0f}% of duct)")

# ---------- export print orientation (top face down) ----------
R = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
for m, nm in [(f, 'nursery_vent_FITTES_350x147'), (k, 'nursery_vent_KUMIKO_350x147'),
              (key, 'vent_lift_key')]:
    p = m.copy()
    if nm != 'vent_lift_key':
        p.apply_transform(R)               # top face to bed
    p.apply_translation(-p.bounds[0])      # z=0 at bed, positive octant
    p.export(f'{nm}_PRINT.stl')
    p.export(f'{nm}_PRINT.3mf')
    print(f"exported {nm}_PRINT.stl/.3mf  bounds {np.round(p.extents,1)}")
print("DONE")
