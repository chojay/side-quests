#!/usr/bin/env python3
"""
stl_surgery.py - find and cut a solid closure out of a mesh you did not author.

You download a holder, print it, and discover it only works in one orientation:
some face is closed that needs to be open. There is no source file, so the fix has
to happen on the mesh.

Rather than eyeballing it in a slicer, this measures the part: it walks the Z axis
computing cross-sectional area at every layer, finds where the area jumps well above
the section's own baseline (that jump IS the unwanted solid material), cuts above it,
and re-caps the mesh so it stays watertight and printable.

    python stl_surgery.py                                  # runs on the bundled synthetic part
    python stl_surgery.py --input part.stl --out fixed.stl
    python stl_surgery.py --input part.stl --z 5           # cut at a height you chose
    python stl_surgery.py --plot profile.png               # save the area profile

Requires: trimesh, numpy (matplotlib only for --plot).
"""
import argparse
import os
import sys

import numpy as np
import trimesh


def _planar_area(section):
    """Cross-section area, tolerating the to_planar -> to_2D rename in trimesh."""
    to_2d = getattr(section, "to_2D", None)
    if to_2d is None:                      # trimesh < 4.x
        to_2d = section.to_planar
    planar, _ = to_2d()
    return float(planar.area)


def area_profile(mesh, dz=0.5):
    """Cross-sectional area at each Z level. Returns (heights, areas)."""
    z0, z1 = mesh.bounds[0][2], mesh.bounds[1][2]
    zs = np.arange(z0 + dz / 2, z1, dz)
    heights, areas = [], []
    for z in zs:
        section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if section is None:
            continue
        try:
            areas.append(_planar_area(section))
            heights.append(float(z))
        except Exception:
            # a degenerate slice (tangent to a face) is not worth failing over
            continue
    return np.array(heights), np.array(areas)


def find_closure(heights, areas, ratio=1.5):
    """
    Locate a solid closure at the bottom of the part.

    The baseline is the median area of the upper half of the part, i.e. what the
    cross-section looks like where the geometry is behaving. Any contiguous run of
    layers at the bottom whose area exceeds `ratio` times that baseline is treated
    as unwanted solid material.

    Returns (cut_height, baseline, peak) or (None, baseline, peak) if nothing found.
    """
    if len(areas) == 0:
        return None, 0.0, 0.0
    upper = areas[len(areas) // 2:]
    baseline = float(np.median(upper))
    peak = float(areas.max())
    if baseline <= 0:
        return None, baseline, peak

    flagged = areas > ratio * baseline
    if not flagged.any() or not flagged[0]:
        # nothing anomalous, or the anomaly is not at the bottom where we cut
        return None, baseline, peak

    # walk up until the first layer that is back to normal
    idx = 0
    while idx < len(flagged) and flagged[idx]:
        idx += 1
    if idx >= len(heights):
        return None, baseline, peak
    return float(heights[idx]), baseline, peak


def cut_above(mesh, z):
    """Keep everything above z, cap the cut, and drop the part back onto the bed."""
    sliced = mesh.slice_plane(
        plane_origin=[0, 0, z],
        plane_normal=[0, 0, 1],   # +Z keeps the geometry ABOVE the plane
        cap=True,                 # seal the cut, or the result is not printable
    )
    if sliced is None or len(sliced.faces) == 0:
        raise ValueError(f"cut at z={z} removed the entire mesh")
    sliced = sliced.copy()
    sliced.vertices[:, 2] -= z    # the slice keeps original coordinates
    return sliced


def plot_profile(heights, areas, baseline, cut_z, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    INK, BLUE, RED = "#2E2E2E", "#4472C4", "#E83845"
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=100)
    ax.plot(areas, heights, color=INK, lw=2.0)
    ax.fill_betweenx(heights, areas, color=BLUE, alpha=0.15)
    ax.axvline(baseline, color=BLUE, lw=1.4, ls=(0, (4, 2)),
               label=f"baseline {baseline:.0f} mm$^2$")
    if cut_z is not None:
        ax.axhline(cut_z, color=RED, lw=1.6, ls=(0, (4, 2)),
                   label=f"cut at z = {cut_z:.1f} mm")
    ax.set_xlabel("cross-section area  (mm$^2$)", fontsize=11, fontweight="bold", color=INK)
    ax.set_ylabel("height z  (mm)", fontsize=11, fontweight="bold", color=INK)
    ax.set_title("Area profile: the step is the unwanted solid",
                 fontsize=12.5, fontweight="bold", color=INK)
    ax.grid(alpha=0.25, lw=0.6)
    ax.legend(fontsize=9.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    print(f"[PLOT] {path}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Find and cut a solid closure out of an STL.")
    ap.add_argument("--input", default=os.path.join(here, "examples", "broken_holder.stl"))
    ap.add_argument("--out", default=None, help="output STL (default: <input>_open.stl)")
    ap.add_argument("--z", type=float, default=None, help="cut height in mm (skips detection)")
    ap.add_argument("--ratio", type=float, default=1.5,
                    help="flag layers whose area exceeds ratio x baseline (default 1.5)")
    ap.add_argument("--dz", type=float, default=0.5, help="sampling step in mm")
    ap.add_argument("--plot", default=None, help="write the area-profile figure here")
    ap.add_argument("--dry-run", action="store_true", help="measure and report, write nothing")
    args = ap.parse_args()

    mesh = trimesh.load(args.input)
    print(f"[IN]   {args.input}")
    print(f"       {len(mesh.faces):,} faces, watertight={mesh.is_watertight}, "
          f"bbox {np.round(mesh.extents, 2)} mm")

    heights, areas = area_profile(mesh, dz=args.dz)
    if len(areas) == 0:
        sys.exit("could not section this mesh along Z")

    detected, baseline, peak = find_closure(heights, areas, ratio=args.ratio)
    print(f"[SCAN] baseline {baseline:.0f} mm2, peak {peak:.0f} mm2 "
          f"({peak / baseline:.1f}x)" if baseline else "[SCAN] no baseline")

    cut_z = args.z if args.z is not None else detected
    if cut_z is None:
        print("[SCAN] no bottom closure found; nothing to cut")
        if args.plot:
            plot_profile(heights, areas, baseline, None, args.plot)
        return
    src = "requested" if args.z is not None else "detected"
    print(f"[CUT]  {src} cut height z = {cut_z:.1f} mm")

    if args.plot:
        plot_profile(heights, areas, baseline, cut_z, args.plot)

    if args.dry_run:
        print("[DRY]  no file written")
        return

    fixed = cut_above(mesh, cut_z)
    out = args.out or os.path.splitext(args.input)[0] + "_open.stl"
    fixed.export(out)
    print(f"[OUT]  {out}")
    print(f"       {len(fixed.faces):,} faces, watertight={fixed.is_watertight}, "
          f"bbox {np.round(fixed.extents, 2)} mm")
    if not fixed.is_watertight:
        print("[WARN] result is NOT watertight; slicers may misbehave. "
              "Check that cap=True sealed every cut loop.")


if __name__ == "__main__":
    main()
