#!/usr/bin/env python3
"""
Generate a synthetic "broken" holder STL so stl_surgery.py can be demonstrated
without redistributing anyone else's model.

The part is a C-shaped cradle (a slotted tube you clip around a cylindrical body)
that carries a deliberate design flaw: the bottom 5 mm is a SOLID disc instead of
staying open, so the body cannot slide down through it when the holder is mounted
vertically. That solid closure is exactly the pathology stl_surgery.py is built to
find and cut away.

Nothing here is derived from a third-party model; it is generated from primitives.

    python make_broken_part.py --out examples/broken_holder.stl
"""
import argparse
import numpy as np
import trimesh

# part geometry (mm)
R_OUTER = 25.0
R_BORE = 19.0
HEIGHT = 100.0
SLOT_WIDTH = 24.0      # the C opening you clip the body through
CLOSURE_H = 5.0        # height of the solid bottom disc (the flaw)


def build_broken_holder():
    """
    C-shaped cradle with a solid bottom closure blocking the bore.

    Built with differences only, never a union: unioning a closure disc onto a
    cradle leaves two solids sharing a coincident face at the seam, and that seam
    survives export as a handful of unpaired edges (a non-watertight mesh). Cutting
    the bore and slot out of one solid, starting above the closure height, gives
    the same shape with clean topology.
    """
    # one solid body
    body = trimesh.creation.cylinder(radius=R_OUTER, height=HEIGHT, sections=128)
    body.apply_translation([0, 0, HEIGHT / 2])

    # bore, starting ABOVE the closure so the bottom stays solid (the flaw)
    bore_h = HEIGHT
    bore = trimesh.creation.cylinder(radius=R_BORE, height=bore_h, sections=128)
    bore.apply_translation([0, 0, CLOSURE_H + bore_h / 2])

    # side slot that opens the tube into a C, also starting above the closure
    slot = trimesh.creation.box(extents=[SLOT_WIDTH, R_OUTER * 2, bore_h])
    slot.apply_translation([0, R_OUTER, CLOSURE_H + bore_h / 2])

    return body.difference(bore).difference(slot)


def main():
    ap = argparse.ArgumentParser(description="Write a synthetic flawed holder STL.")
    ap.add_argument("--out", default="examples/broken_holder.stl")
    args = ap.parse_args()

    mesh = build_broken_holder()
    mesh.export(args.out)

    print(f"[DONE] wrote {args.out}")
    print(f"       {len(mesh.faces):,} faces, watertight={mesh.is_watertight}")
    print(f"       bbox {np.round(mesh.extents, 2)} mm")
    print(f"[FLAW] bottom {CLOSURE_H:.0f} mm is a solid disc, so the bore is blocked")


if __name__ == "__main__":
    main()
