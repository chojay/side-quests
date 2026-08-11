#!/usr/bin/env python3
"""Validate two-part halves (all 3 styles) + assembly fit + export to two-print/."""
import os, numpy as np, trimesh

os.makedirs('two-print', exist_ok=True)
plate_T, total_H = 4.5, 20.5
dt_y = [-77, 77]

results = {}
for style in ['fittes', 'kumiko', 'luxe']:
    for half in ['A', 'B']:
        m = trimesh.load(f'{style}_half{half}_design.stl')
        bodies = len(m.split(only_watertight=False))
        ext = m.extents
        assert m.is_watertight, f"{style} {half} not watertight"
        assert bodies == 1, f"{style} {half} has {bodies} bodies"
        assert ext[0] <= 350 and ext[1] <= 320, f"{style} {half} exceeds bed"
        results[(style, half)] = m
        print(f"{style:7s} {half}: watertight, 1 body, extents {np.round(ext,1)}, "
              f"vol {m.volume/1000:.0f} cm3")

# dovetail probes: tab solid in A, socket empty in B, plate solid next to it
for style in ['fittes', 'kumiko', 'luxe']:
    A, B = results[(style,'A')], results[(style,'B')]
    zr = -16.0 if style == 'luxe' else -8.0   # luxe seam ribs are deep (hidden)
    pts = np.array([(-4.0, 77, -2), (-4.0, 70, -2), (1.7, 0, zr), (-1.7, 0, zr)])
    a = A.contains(pts); b = B.contains(pts)
    #            tab@A  border@A(cut away? x<0 -> no)  seamribA  seamribB(not in A)
    assert a[0] == True,  f"{style}: tab missing on A"
    assert b[0] == False, f"{style}: socket not cut in B"
    assert b[1] == True,  f"{style}: B border plate missing"
    assert a[2] == True and a[3] == False, f"{style}: seam rib A wrong"
    assert b[3] == True and b[2] == False, f"{style}: seam rib B wrong"
    # assembled: A and B in the same coords must not intersect (clearances)
    both = A.contains(B.vertices[::7]).sum()
    assert both == 0, f"{style}: {both} B vertices inside A - halves collide"
    # assembled extents
    comb = trimesh.util.concatenate([A, B])
    print(f"{style:7s} assembled: {np.round(comb.extents,1)} (full perimeter flange)")
    assert abs(comb.extents[0] - 374.0) < 0.2 and abs(comb.extents[1] - 171.0) < 0.1

# export print files (flip top-face-down)
R = trimesh.transformations.rotation_matrix(np.pi, [1,0,0])
for (style, half), m in results.items():
    p = m.copy(); p.apply_transform(R); p.apply_translation(-p.bounds[0])
    base = f'two-print/nursery_vent_{style.upper()}_half{half}_PRINT'
    p.export(base + '.stl'); p.export(base + '.3mf')
print("exported 12 files to two-print/")
