#!/usr/bin/env python3
"""
Honeywell QuietSet Tower Fan (HYF260/HYF290) - Replacement Locking Nut v3

v3 changelog: First print fit ID/OD but threads did not catch. Diagnosis:
the housing almost certainly uses a MULTI-START coarse thread (typical of
plastic quick-tighten fan nuts; consistent with the manual's "audible
ratcheting" - i.e. one or two turns to fully seat). Switched from single
helix to N-start helix sweep and added a thread-profile selector.

PRINT ORIENTATION: bore axis vertical (as modeled).

DIMENSIONS ARE STILL ESTIMATES for THREAD_PITCH and NUM_STARTS. ID/OD looked
correct from the previous print, so those are unchanged.
"""

from build123d import (
    BuildPart, BuildSketch, BuildLine, Cylinder, Cone, Align, Mode,
    Locations, Plane, Polyline, make_face, sweep, Helix, Axis, Compound,
    Mesher, export_stl, Location, Rotation,
)
import trimesh
from math import pi, sin, cos, tan, radians
from pathlib import Path

# ============================================================================
# PARAMETERS - tweak these to fit your fan
# ============================================================================

# ID/OD (these matched the original on the v2 print)
OUTER_DIAMETER         = 100.0  # mm  outer rim diameter (the part you grip)
THREAD_INNER_DIAMETER  = 60.0   # mm  thread peaks (the tight ID)
HEIGHT                 = 22.0   # mm  total height

# Thread geometry - measured from user's housing
# Caliper measurements: thread crest width = 1.61mm, gap = 1.23mm
# -> Pitch = 1.61 + 1.23 = 2.84mm; 2 spiral lines reached the bottom edge
NUM_STARTS             = 2      # measured: 2 thread starts visible on housing
THREAD_PITCH           = 2.84   # mm  measured (crest 1.61 + gap 1.23)
# Lead = NUM_STARTS * THREAD_PITCH = 5.68mm per turn
THREAD_PROFILE         = "buttress"   # "triangle" / "square" / "buttress"
THREAD_DEPTH_FRAC      = 0.40   # 0.40 * 2.84 = 1.14mm depth (reasonable for buttress)

# Cosmetic
NUM_GRIP_RIBS          = 24     # vertical teeth around outer rim
RIB_DEPTH              = 2.5    # mm

# ============================================================================
# DERIVED
# ============================================================================

OUTER_RADIUS    = OUTER_DIAMETER / 2
THREAD_DEPTH    = THREAD_DEPTH_FRAC * THREAD_PITCH
MINOR_RADIUS    = THREAD_INNER_DIAMETER / 2                 # thread peak radius
MAJOR_RADIUS    = MINOR_RADIUS + THREAD_DEPTH               # smooth-bore radius
LEAD            = NUM_STARTS * THREAD_PITCH
HALF_BASE_TRI   = THREAD_DEPTH / tan(radians(60))
EPS             = 0.02


def thread_profile_polyline(profile_name, major_r, minor_r, pitch):
    """Build a 2D thread cross-section centred at Z=0, on the XZ plane.
    The profile sits at X = major_r and protrudes inward to X = minor_r.

    CRITICAL CONSTRAINT: total axial extent of the profile at base_x must be
    LESS than the male thread's gap width (here ~1.23 mm) so the male thread
    crests can pass between adjacent female threads when screwing on. We
    therefore cap profile axial extent at ~0.35 * pitch (about 1.0 mm at
    pitch 2.84), which leaves ~0.2 mm clearance for FDM print tolerance.
    """
    base_x = major_r + EPS  # slight overlap with bore for clean boolean
    peak_x = minor_r

    # Target female thread axial extent: 0.35 * pitch (~1.0 mm for P=2.84mm)
    # Male gap is ~0.43 * pitch (~1.23 mm), so this leaves ~0.08 * pitch
    # (~0.23 mm) of axial clearance.
    half_axial = 0.175 * pitch  # so total axial extent = 0.35 * pitch

    if profile_name == "triangle":
        # Symmetric ISO-style: peak at axial midpoint
        return [
            (base_x, -half_axial),
            (base_x,  half_axial),
            (peak_x, 0),
            (base_x, -half_axial),
        ]
    if profile_name == "square":
        # Trapezoidal: flat top occupies ~50% of profile axial width
        peak_half = half_axial * 0.5
        return [
            (base_x, -half_axial),
            (base_x,  half_axial),
            (peak_x,  peak_half),
            (peak_x, -peak_half),
            (base_x, -half_axial),
        ]
    if profile_name == "buttress":
        # Asymmetric scalene triangle, peak biased toward top (load face down)
        return [
            (base_x, -half_axial),                # bottom-left
            (base_x,  half_axial),                # top-left
            (peak_x,  half_axial * 0.4),          # peak, biased upward
            (base_x, -half_axial),                # close
        ]
    raise ValueError(f"Unknown thread profile: {profile_name}")


def build_nut_subtract(
    outer_diameter=OUTER_DIAMETER,
    thread_inner_diameter=THREAD_INNER_DIAMETER,
    height=HEIGHT,
    num_starts=NUM_STARTS,
    thread_pitch=THREAD_PITCH,
    thread_depth_frac=THREAD_DEPTH_FRAC,
    num_grip_ribs=NUM_GRIP_RIBS,
    rib_depth=RIB_DEPTH,
):
    """Alternate build strategy: start with a tight bore (at minor) then SUBTRACT
    helical grooves to create the valleys. Avoids the multi-start boolean union
    of swept solids that produces non-manifold geometry in OCCT."""
    outer_r = outer_diameter / 2
    depth = thread_depth_frac * thread_pitch
    minor_r = thread_inner_diameter / 2
    major_r = minor_r + depth
    lead = num_starts * thread_pitch

    with BuildPart() as nut:
        Cylinder(outer_r, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Tight bore at minor (peaks)
        Cylinder(minor_r, height + 2 * EPS,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)
        if num_grip_ribs > 0:
            rib_step = 360.0 / num_grip_ribs
            for i in range(num_grip_ribs):
                angle = i * rib_step
                x = outer_r * cos(angle * pi / 180.0)
                y = outer_r * sin(angle * pi / 180.0)
                with Locations((x, y, -EPS)):
                    Cylinder(rib_depth, height + 2 * EPS,
                             align=(Align.CENTER, Align.CENTER, Align.MIN),
                             mode=Mode.SUBTRACT)

    # Groove profile: rectangular cross-section extending OUTWARD from minor.
    # Axial width = pitch - (pitch * 0.35) = 0.65 * pitch (fits male crest with
    # 0.24mm clearance for the measured 1.61mm male crest at pitch 2.84).
    valley_half = 0.65 * thread_pitch / 2
    groove_pts = [
        (minor_r - EPS, -valley_half),
        (minor_r - EPS,  valley_half),
        (major_r + EPS,  valley_half),
        (major_r + EPS, -valley_half),
        (minor_r - EPS, -valley_half),
    ]
    with BuildSketch(Plane.XZ) as groove_profile:
        with BuildLine():
            Polyline(*groove_pts)
        make_face()

    final = nut.part
    for k in range(num_starts):
        z_off = k * (lead / num_starts) - lead
        helix = Helix(
            pitch=lead,
            height=height + 2 * lead,
            radius=minor_r,
            center=(0, 0, z_off),
        )
        helix = helix.located(Location((0, 0, 0), (0, 0, 1), k * 360.0 / num_starts))
        groove = sweep(sections=groove_profile.sketch, path=helix)
        final = final - groove

    return final


def build_nut(
    outer_diameter=OUTER_DIAMETER,
    thread_inner_diameter=THREAD_INNER_DIAMETER,
    height=HEIGHT,
    num_starts=NUM_STARTS,
    thread_pitch=THREAD_PITCH,
    thread_profile=THREAD_PROFILE,
    thread_depth_frac=THREAD_DEPTH_FRAC,
    num_grip_ribs=NUM_GRIP_RIBS,
    rib_depth=RIB_DEPTH,
):
    outer_r = outer_diameter / 2
    depth = thread_depth_frac * thread_pitch
    minor_r = thread_inner_diameter / 2
    major_r = minor_r + depth
    lead = num_starts * thread_pitch

    with BuildPart() as nut:
        # Outer cylinder
        Cylinder(outer_r, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Bore
        Cylinder(major_r, height + 2 * EPS,
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 mode=Mode.SUBTRACT)
        # Grip ribs around the outer rim
        if num_grip_ribs > 0:
            rib_step = 360.0 / num_grip_ribs
        else:
            rib_step = 0
        for i in range(num_grip_ribs):
            angle = i * rib_step
            x = outer_r * cos(angle * pi / 180.0)
            y = outer_r * sin(angle * pi / 180.0)
            with Locations((x, y, -EPS)):
                Cylinder(rib_depth, height + 2 * EPS,
                         align=(Align.CENTER, Align.CENTER, Align.MIN),
                         mode=Mode.SUBTRACT)

    # Build the thread profile sketch
    pts = thread_profile_polyline(thread_profile, major_r, minor_r, thread_pitch)
    with BuildSketch(Plane.XZ) as profile:
        with BuildLine():
            Polyline(*pts)
        make_face()

    # Build N-start threads: sweep one helix, then create N rotated/offset copies.
    # Sweep ONCE, then use Location to position copies (cheaper + more robust
    # than rotating the helix wire, which sometimes confuses OCCT booleans).
    base_helix = Helix(
        pitch=lead,
        height=height + 2 * lead,
        radius=major_r,
        center=(0, 0, -lead),
    )
    one_thread = sweep(sections=profile.sketch, path=base_helix)

    threads_combined = one_thread
    for k in range(1, num_starts):
        phase_deg = k * (360.0 / num_starts)
        z_off = k * (lead / num_starts)
        copy = one_thread.located(Location((0, 0, z_off), (0, 0, 1), phase_deg))
        threads_combined = threads_combined + copy

    # Trim threads to body height with a bounding cylinder
    trim = Cylinder(outer_r + 5, height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN))
    threads_trimmed = threads_combined & trim

    return nut.part + threads_trimmed


def repair_mesh(mesh):
    """Aggressive cleanup for non-manifold meshes produced by OCCT multi-start
    boolean unions. Merges near-duplicate vertices, removes duplicate and
    degenerate faces, fixes winding/normals, then fills holes."""
    mesh.merge_vertices(merge_tex=False, merge_norm=False)
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    try:
        trimesh.repair.fix_winding(mesh)
        trimesh.repair.fix_normals(mesh)
        trimesh.repair.fill_holes(mesh)
    except Exception:
        pass
    mesh.process()
    return mesh


def manifold_clean(mesh):
    """Round-trip through manifold3d (Google's guaranteed-manifold geometry
    engine). Returns input mesh unchanged if manifold3d can't construct a
    valid Manifold from the input (e.g. when there are non-manifold edges
    that can't be auto-resolved)."""
    import manifold3d as m3d
    import numpy as np
    # Pre-clean to give manifold3d the best shot at acceptance
    mesh = mesh.copy()
    mesh.merge_vertices(merge_tex=False, merge_norm=False, digits_vertex=4)
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()

    try:
        mfd_mesh = m3d.Mesh(
            vert_properties=np.array(mesh.vertices, dtype=np.float32),
            tri_verts=np.array(mesh.faces, dtype=np.uint32),
        )
        mfd = m3d.Manifold(mfd_mesh)
        if mfd.is_empty():
            return mesh  # manifold3d rejected; return pre-cleaned input
        # No-op transform forces re-verification
        mfd = mfd.transform([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]])
        out = mfd.to_mesh()
        result = trimesh.Trimesh(
            vertices=np.array(out.vert_properties),
            faces=np.array(out.tri_verts),
        )
        if len(result.faces) == 0:
            return mesh
        return result
    except Exception:
        return mesh


def export_one(part, basename, out_dir):
    stl_path = out_dir / f"{basename}.stl"
    threemf_path = out_dir / f"{basename}.3mf"
    try:
        export_stl(part, str(stl_path))
    except Exception as e:
        print(f"  {basename}: STL export FAILED ({e})")
        return None, None

    # Load and repair the STL via trimesh (handles multi-start watertight quirks)
    mesh = trimesh.load(str(stl_path), force='mesh')
    needed_repair = ""
    if not mesh.is_watertight:
        cleaned = repair_mesh(mesh.copy())
        if cleaned.is_watertight and len(cleaned.faces) > 0:
            cleaned.export(str(stl_path))
            mesh = cleaned
            needed_repair = " (repaired)"
        else:
            # Try manifold3d roundtrip
            try:
                mfd_cleaned = manifold_clean(cleaned)
                if mfd_cleaned.is_watertight and len(mfd_cleaned.faces) > 0:
                    mfd_cleaned.export(str(stl_path))
                    mesh = mfd_cleaned
                    needed_repair = " (manifold3d)"
                else:
                    needed_repair = " (non-manifold; slicer auto-repair on import)"
            except Exception:
                needed_repair = " (non-manifold; slicer auto-repair on import)"

    # 3MF export: try build123d Mesher first, fall back to trimesh
    try:
        mesher = Mesher()
        mesher.add_shape(part)
        mesher.write(str(threemf_path))
    except Exception:
        try:
            mesh.export(str(threemf_path))
        except Exception as e2:
            print(f"  {basename}: 3MF export failed ({e2}); STL only")
            threemf_path = None

    try:
        verify = trimesh.load(str(stl_path))
        print(f"  {basename}: watertight={verify.is_watertight}{needed_repair}, "
              f"vol={verify.volume:.0f}mm^3, tris={len(verify.faces)}")
    except Exception as e:
        print(f"  {basename}: validation failed ({e})")
    return stl_path, threemf_path


# ============================================================================
# MAIN: build default + a test-fit series
# ============================================================================
if __name__ == "__main__":
    OUT_DIR = Path(__file__).parent

    print("Building default nut (v3 settings)...")
    default_nut = build_nut()
    export_one(default_nut, "locking_nut", OUT_DIR)

    # Generate a thread-tester series: short rings (8mm tall) so each prints
    # in <10 minutes. Print all 6, see which screws on the housing, then
    # update the defaults above to that combo and reprint the full nut.
    print("\nBuilding test-fit series (8mm tall trial rings)...")
    test_dir = OUT_DIR / "test_rings"
    test_dir.mkdir(exist_ok=True)
    # v7 follow-up: T3 (2-start p=3.0) and T4 (3-start p=2.84) both ENGAGED
    # the housing threads but bound before the first turn (too tight).
    # Fix: ID 60 -> 62 (1mm radial clearance) and height 5 -> 12mm so >=2 full
    # helix turns are visible per start, confirming the thread profile reads
    # correctly under sustained rotation.
    # Method "swept" uses build_nut (buttress profile, swept helical thread).
    # Method "subtract" uses build_nut_subtract (rectangular groove subtracted
    # from a solid bore). Use "subtract" for 3-start tall rings where the
    # swept-union path produces non-manifold edges at the trim boundary.
    # Spec: (num_starts, pitch, profile, depth_frac, inner_diameter, height, method, label)
    test_specs = [
        # v6 (already printed; left here for reproducibility)
        (2, 2.84, "buttress", 0.40, 56.0, 5.0,  "swept",    "T1_ID56_deeperpeaks"),
        (2, 2.84, "buttress", 0.40, 58.0, 5.0,  "swept",    "T2_ID58_deeperpeaks"),
        (2, 3.00, "buttress", 0.40, 60.0, 5.0,  "swept",    "T3_pitch3p0"),
        (3, 2.84, "buttress", 0.40, 60.0, 5.0,  "swept",    "T4_3start"),
        # v7: bigger opening + taller, narrows pitch ambiguity between T3/T4
        (2, 3.00, "buttress", 0.40, 62.0, 12.0, "swept",    "T5_pitch3p0_ID62_h12"),
        (3, 2.84, "buttress", 0.40, 62.0, 12.0, "subtract", "T6_3start_ID62_h12"),
    ]
    for ns, p, prof, depth, idia, h, method, label in test_specs:
        if method == "subtract":
            nut = build_nut_subtract(
                height=h,
                num_starts=ns,
                thread_pitch=p,
                thread_depth_frac=depth,
                thread_inner_diameter=idia,
            )
        else:
            nut = build_nut(
                height=h,
                num_starts=ns,
                thread_pitch=p,
                thread_profile=prof,
                thread_depth_frac=depth,
                thread_inner_diameter=idia,
            )
        export_one(nut, label, test_dir)

    print("\nDone. Print plan:")
    print("  1. Print everything in test_rings/ in ONE plate job (each ring")
    print("     is small; should all fit on the H2D bed simultaneously).")
    print("  2. Try each on the fan housing. The one that screws on cleanly")
    print("     wins. Note its num_starts/pitch/profile.")
    print("  3. Update the PARAMETERS block above with the winning combo.")
    print("  4. Rerun this script (without --tests) and print locking_nut.3mf")
