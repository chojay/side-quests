#!/usr/bin/env python3
"""Validate one-piece Luxe (3 nested 5mm channels) + export print files."""
import numpy as np, trimesh

plate_L, plate_W, plate_T = 348.5, 171.0, 4.5
field_L, n_ribs, rib_d = 324.5, 7, 9.0
skirt_W, total_H = 145.0, 20.5
luxe_FL, luxe_FW, g, rw = 324.5, 135.0, 5.0, 12.0
r1_o = (luxe_FL-2*g, luxe_FW-2*g); r1_i = (r1_o[0]-2*rw, r1_o[1]-2*rw)
r2_o = (r1_i[0]-2*g, r1_i[1]-2*g); r2_i = (r2_o[0]-2*rw, r2_o[1]-2*rw)
panel = (r2_i[0]-2*g, r2_i[1]-2*g)
def ribx(i): return -field_L/2 + i*field_L/(n_ribs+1)

m = trimesh.load('luxe_design.stl')
probes = [
    # top-face pattern: border | ch1 | ring1 | ch2 | ring2 | ch3 | panel (walk y at x=0)
    ((0, luxe_FW/2+3, -2),          True,  "frame border face"),
    ((0, (luxe_FW/2+r1_o[1]/2)/2, -2), False, "channel 1 open"),
    ((0, (r1_o[1]+r1_i[1])/4, -2),  True,  "ring 1 face"),
    ((0, (r1_i[1]+r2_o[1])/4, -2),  False, "channel 2 open"),
    ((0, (r2_o[1]+r2_i[1])/4, -2),  True,  "ring 2 face"),
    ((0, (r2_i[1]+panel[1])/4, -2), False, "channel 3 open"),
    ((0, 0, -2),                    True,  "center panel"),
    # ends (walk x at y=0)
    ((panel[0]/2+g/2, 0, -2),       False, "channel 3 open at panel end"),
    (((r2_o[0]+r2_i[0])/4, 0, -2),  True,  "ring 2 end band"),
    (((r1_o[0]+r1_i[0])/4, 0, -2),  True,  "ring 1 end band"),
    ((170, 0, -2),                  True,  "solid end margin"),
    # hidden understructure: NOTHING under channels above z=-14.5
    ((ribx(4), (r1_i[1]+r2_o[1])/4, -6),  False, "ch2: hidden zone clear (was rib)"),
    ((ribx(4), (r1_i[1]+r2_o[1])/4, -13), False, "ch2: hidden zone clear deep"),
    ((ribx(4), (r1_i[1]+r2_o[1])/4, -16), True,  "deep rib crosses ch2 below sightline"),
    ((134.25, 0, -16),              True,  "deep extra rib @134.25 (ring2 ends)"),
    ((151.25, 0, -16),              True,  "deep extra rib @151.25 (ring1 ends)"),
    ((142.5, 30, -8),               False, "open between extra ribs"),
    # spines hidden under solid faces
    ((0, (r1_o[1]+r1_i[1])/4, -10), True,  "ring1 spine under band centerline"),
    ((0, (r2_o[1]+r2_i[1])/4, -10), True,  "ring2 spine under band centerline"),
    ((0, 21, -10),                  True,  "panel spine y=21"),
    ((0, 0, -10),                   True,  "panel spine y=0"),
    ((0, 10, -10),                  False, "no spine at y=10 (under panel, open)"),
    ((151.25, 0, -10),              True,  "ring1 end spine aligned over extra rib"),
    ((0, luxe_FW/2+1.2, -15),       True,  "downstand wall reaches deep ribs"),
    ((0, skirt_W/2-1, -12),         True,  "skirt wall"),
    ((20, 10, -12),                 False, "open duct below panel (off-spine)"),
    # chamfers & magnets
    ((0, plate_W/2-0.4, -0.4),      False, "perimeter 45deg chamfer"),
    ((0, panel[1]/2+0.3, -0.2),     False, "panel edge 0.7 chamfer"),
    ((60+5.3, 0, -5.5),             True,  "magnet boss ring"),
    ((60, 0, -3.0),                 False, "magnet pocket cavity"),
    ((60, 0, -0.6),                 True,  "1.2mm cover above magnet"),
]
print(f"watertight={m.is_watertight}  bodies={len(m.split(only_watertight=False))}  "
      f"vol={m.volume/1000:.1f} cm3  extents={np.round(m.extents,2)}")
assert m.is_watertight and len(m.split(only_watertight=False)) == 1
inside = m.contains(np.array([p for p,_,_ in probes]))
ok = True
for (p, expect, label), got in zip(probes, inside):
    s = "ok" if got == expect else "** FAIL **"
    if got != expect: ok = False
    print(f"  {'solid' if expect else 'empty':5s} {label:40s} {s}")
assert ok
ext = m.extents
assert ext[0] <= 350 and ext[1] <= 320 and abs(ext[2]-total_H) < 0.1

# --- visibility sweep: every channel projection must be EMPTY from the
# --- underside of the plate down to the deep-rib tops (z -4.6 .. -14.4)
sweep = []
runs = [  # (fixed-coord axis, fixed value, span axis limit) per channel loop
    ('y',  65.0, 150), ('y', -65.0, 150), ('x',  159.75, 58), ('x', -159.75, 58),  # ch1
    ('y',  48.0, 135), ('y', -48.0, 135), ('x',  142.75, 42), ('x', -142.75, 42),  # ch2
    ('y',  31.0, 120), ('y', -31.0, 120), ('x',  125.75, 25), ('x', -125.75, 25),  # ch3
]
for ax, val, lim in runs:
    for s in np.linspace(-lim, lim, 41):
        for z in (-6.0, -10.0, -14.0):
            sweep.append((s, val, z) if ax == 'y' else (val, s, z))
vis = m.contains(np.array(sweep))
bad = int(vis.sum())
print(f"visibility sweep: {len(sweep)} points in channel projections, "
      f"{bad} obstructed (must be 0)")
assert bad == 0, "material visible in a channel sightline"

p1 = 2*((luxe_FL-g)+(luxe_FW-g)); p2 = 2*((r1_i[0]-g)+(r1_i[1]-g)); p3 = 2*((r2_i[0]-g)+(r2_i[1]-g))
print(f"\nFree area ~{(p1+p2+p3)*g/100:.0f} cm2 "
      f"({(p1+p2+p3)*g/(350*147):.0%} of duct), 3 channels @ 5mm")

R = trimesh.transformations.rotation_matrix(np.pi, [1,0,0])
p = m.copy(); p.apply_transform(R); p.apply_translation(-p.bounds[0])
p.export('nursery_vent_LUXE_350x147_PRINT.stl'); p.export('nursery_vent_LUXE_350x147_PRINT.3mf')
print("exported nursery_vent_LUXE_350x147_PRINT.stl/.3mf", np.round(p.extents,1))
