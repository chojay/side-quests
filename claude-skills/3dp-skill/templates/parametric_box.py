#!/usr/bin/env python3
"""
Parametric Box Generator
Creates a hollow box with optional lid
Designed for FDM 3D printing

Usage:
    python parametric_box.py
    # Modify parameters below then run
"""
from build123d import *

# === DESIGN PARAMETERS ===
# Modify these values for your needs
# All dimensions in mm

# Outer dimensions
WIDTH = 80.0        # X dimension
DEPTH = 60.0        # Y dimension
HEIGHT = 40.0       # Z dimension (box body, not including lid)

# Wall and floor
WALL_THICKNESS = 2.0    # Side walls
FLOOR_THICKNESS = 2.0   # Bottom

# Corner radius (0 for sharp corners)
CORNER_RADIUS = 3.0

# Lid options
MAKE_LID = True
LID_HEIGHT = 5.0        # Total lid thickness
LID_LIP = 3.0           # How far lid inserts into box
LID_TOLERANCE = 0.3     # Gap for fit (0.2-0.4 typical)

# === DERIVED PARAMETERS ===
INNER_WIDTH = WIDTH - 2 * WALL_THICKNESS
INNER_DEPTH = DEPTH - 2 * WALL_THICKNESS
INNER_HEIGHT = HEIGHT - FLOOR_THICKNESS


def create_box_body():
    """Create the main box body."""
    with BuildPart() as body:
        # Outer shell
        with BuildSketch():
            Rectangle(WIDTH, DEPTH)
            if CORNER_RADIUS > 0:
                fillet(vertices(), radius=CORNER_RADIUS)
        extrude(amount=HEIGHT)

        # Hollow out interior
        with BuildSketch(body.faces().sort_by(Axis.Z)[-1]):
            Rectangle(INNER_WIDTH, INNER_DEPTH)
            if CORNER_RADIUS > 0:
                inner_radius = max(CORNER_RADIUS - WALL_THICKNESS, 0.5)
                fillet(vertices(), radius=inner_radius)
        extrude(amount=-INNER_HEIGHT, mode=Mode.SUBTRACT)

        # Optional: fillet top edges for comfort
        top_face = body.faces().sort_by(Axis.Z)[-1]
        outer_edges = top_face.edges().filter_by(lambda e: e.length > INNER_WIDTH - 1)
        if CORNER_RADIUS > 0 and len(outer_edges) > 0:
            try:
                fillet(outer_edges, radius=0.5)
            except:
                pass  # Skip if fillet fails

    return body.part


def create_lid():
    """Create the lid with lip that fits into box."""
    with BuildPart() as lid:
        # Main lid plate
        with BuildSketch():
            Rectangle(WIDTH, DEPTH)
            if CORNER_RADIUS > 0:
                fillet(vertices(), radius=CORNER_RADIUS)
        extrude(amount=LID_HEIGHT - LID_LIP)

        # Lip that goes into box
        lip_width = INNER_WIDTH - LID_TOLERANCE
        lip_depth = INNER_DEPTH - LID_TOLERANCE
        with BuildSketch(lid.faces().sort_by(Axis.Z)[0]):
            Rectangle(lip_width, lip_depth)
            if CORNER_RADIUS > 0:
                inner_radius = max(CORNER_RADIUS - WALL_THICKNESS - LID_TOLERANCE/2, 0.5)
                fillet(vertices(), radius=inner_radius)
        extrude(amount=-LID_LIP)

    return lid.part


def main():
    print("=" * 60)
    print("Parametric Box Generator")
    print("=" * 60)
    print(f"Outer dimensions: {WIDTH} x {DEPTH} x {HEIGHT} mm")
    print(f"Inner dimensions: {INNER_WIDTH} x {INNER_DEPTH} x {INNER_HEIGHT} mm")
    print(f"Wall thickness: {WALL_THICKNESS} mm")
    print(f"Floor thickness: {FLOOR_THICKNESS} mm")
    print(f"Corner radius: {CORNER_RADIUS} mm")
    if MAKE_LID:
        print(f"Lid: Yes (lip: {LID_LIP} mm, tolerance: {LID_TOLERANCE} mm)")
    print("=" * 60)

    # Generate box body
    print("\nGenerating box body...")
    box = create_box_body()
    box.export_stl("parametric_box_body.stl")
    print("✓ Exported: parametric_box_body.stl")

    # Generate lid if requested
    if MAKE_LID:
        print("Generating lid...")
        lid = create_lid()
        lid.export_stl("parametric_box_lid.stl")
        print("✓ Exported: parametric_box_lid.stl")

    # Export 3MF (preferred for Bambu Studio)
    try:
        from build123d import Mesher
        parts = [("parametric_box_body", box)]
        if MAKE_LID:
            parts.append(("parametric_box_lid", lid))
        for name, part in parts:
            with Mesher() as m:
                m.add_shape(part)
                m.write(f"{name}.3mf")
            print(f"✓ Exported: {name}.3mf (preferred for Bambu Studio)")
    except Exception as e:
        print(f"  3MF export unavailable: {e}")

    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    stl_files = ["parametric_box_body.stl"] + (["parametric_box_lid.stl"] if MAKE_LID else [])
    try:
        import trimesh
        for filename in stl_files:
            mesh = trimesh.load(filename)
            status = "✓" if mesh.is_watertight else "✗"
            print(f"{status} {filename}: watertight={mesh.is_watertight}, volume={mesh.volume:.1f} mm³")
    except ImportError:
        print("Install trimesh for validation: pip install trimesh")

    # Generate preview images
    print("\n" + "=" * 60)
    print("PREVIEW IMAGES")
    print("=" * 60)
    try:
        from preview_helper import generate_previews
        generate_previews(stl_files)
    except ImportError:
        print("Note: Install numpy-stl matplotlib for preview images")

    print("\n" + "=" * 60)
    print("PRINT SETTINGS")
    print("=" * 60)
    print("- Layer height: 0.2mm")
    print("- Infill: 15-20%")
    print("- Supports: Not needed (design optimized)")
    print("- Print lid upside down (lip facing up)")
    print("=" * 60)


if __name__ == "__main__":
    main()
