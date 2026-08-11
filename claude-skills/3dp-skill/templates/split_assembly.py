#!/usr/bin/env python3
"""
Split Assembly Generator with Dovetail Joint
Creates a two-part design that joins with interlocking dovetails
Useful for parts too large for single print or multi-color designs
Designed for FDM 3D printing

Usage:
    python split_assembly.py
    # Modify parameters below then run
"""
from build123d import *
import math

# === DESIGN PARAMETERS ===
# All dimensions in mm

# Total part dimensions
TOTAL_WIDTH = 200.0     # X dimension (split direction)
TOTAL_DEPTH = 80.0      # Y dimension
TOTAL_HEIGHT = 15.0     # Z dimension

# Split configuration
SPLIT_OVERLAP = 10.0    # How much parts overlap at joint

# Dovetail joint parameters
DOVETAIL_COUNT = 3          # Number of dovetails
DOVETAIL_WIDTH = 15.0       # Width of each dovetail
DOVETAIL_DEPTH = 8.0        # How deep dovetail extends
DOVETAIL_ANGLE = 8.0        # Degrees of taper (typical: 7-14°)
DOVETAIL_TOLERANCE = 0.25   # Gap for fit

# Corner radius (0 for sharp)
CORNER_RADIUS = 2.0

# Example: base plate with mounting holes
ADD_MOUNTING_HOLES = True
HOLE_DIAMETER = 4.2     # M4 clearance
HOLE_INSET = 15.0       # Distance from edges

# === DERIVED PARAMETERS ===
HALF_WIDTH = TOTAL_WIDTH / 2
TAPER = math.tan(math.radians(DOVETAIL_ANGLE)) * DOVETAIL_DEPTH


def create_dovetail_profile(is_male=True):
    """
    Create 2D dovetail profile.
    Male: tapered outward (wider at tip)
    Female: tapered inward (wider at base)
    """
    tol = 0 if is_male else DOVETAIL_TOLERANCE

    # Base width and tip width
    base_width = DOVETAIL_WIDTH
    tip_width = DOVETAIL_WIDTH + 2 * TAPER

    if is_male:
        # Male: narrower at base, wider at tip
        half_base = base_width / 2
        half_tip = tip_width / 2
    else:
        # Female: add tolerance
        half_base = (base_width + tol) / 2
        half_tip = (tip_width + tol) / 2

    # Create trapezoid profile
    points = [
        (-half_base, 0),
        (half_base, 0),
        (half_tip, DOVETAIL_DEPTH + (tol if not is_male else 0)),
        (-half_tip, DOVETAIL_DEPTH + (tol if not is_male else 0)),
    ]

    return points


def create_left_half():
    """Create left half with male dovetails."""
    # Adjusted width to account for overlap
    part_width = HALF_WIDTH + SPLIT_OVERLAP / 2

    with BuildPart() as left:
        # Main body
        with BuildSketch():
            Rectangle(part_width, TOTAL_DEPTH)
            if CORNER_RADIUS > 0:
                # Only round left corners
                fillet(
                    [v for v in vertices() if v.X < 0],
                    radius=CORNER_RADIUS
                )
        extrude(amount=TOTAL_HEIGHT)

        # Position at left side
        left.part = left.part.translate((-part_width/2 + SPLIT_OVERLAP/2, 0, 0))

        # Add dovetail tongues on right edge
        dovetail_spacing = TOTAL_DEPTH / (DOVETAIL_COUNT + 1)

        for i in range(DOVETAIL_COUNT):
            y_pos = -TOTAL_DEPTH/2 + dovetail_spacing * (i + 1)

            # Create dovetail extrusion
            with BuildPart() as dove:
                with BuildSketch(Plane.XZ):
                    Polygon(create_dovetail_profile(is_male=True))
                extrude(amount=TOTAL_HEIGHT)

                # Rotate and position
                dove.part = dove.part.rotate(Axis.Z, -90)
                dove.part = dove.part.translate((SPLIT_OVERLAP/2, y_pos, 0))

            left.part = left.part + dove.part

        # Add mounting holes if enabled
        if ADD_MOUNTING_HOLES:
            hole_positions = [
                (-HALF_WIDTH + HOLE_INSET, TOTAL_DEPTH/2 - HOLE_INSET),
                (-HALF_WIDTH + HOLE_INSET, -TOTAL_DEPTH/2 + HOLE_INSET),
            ]
            for x, y in hole_positions:
                with BuildPart() as hole:
                    Cylinder(HOLE_DIAMETER/2, TOTAL_HEIGHT)
                    hole.part = hole.part.translate((x, y, TOTAL_HEIGHT/2))
                left.part = left.part - hole.part

    return left.part


def create_right_half():
    """Create right half with female dovetails (grooves)."""
    # Adjusted width
    part_width = HALF_WIDTH + SPLIT_OVERLAP / 2

    with BuildPart() as right:
        # Main body
        with BuildSketch():
            Rectangle(part_width, TOTAL_DEPTH)
            if CORNER_RADIUS > 0:
                # Only round right corners
                fillet(
                    [v for v in vertices() if v.X > 0],
                    radius=CORNER_RADIUS
                )
        extrude(amount=TOTAL_HEIGHT)

        # Position at right side
        right.part = right.part.translate((part_width/2 - SPLIT_OVERLAP/2, 0, 0))

        # Subtract dovetail grooves on left edge
        dovetail_spacing = TOTAL_DEPTH / (DOVETAIL_COUNT + 1)

        for i in range(DOVETAIL_COUNT):
            y_pos = -TOTAL_DEPTH/2 + dovetail_spacing * (i + 1)

            # Create groove (female dovetail)
            with BuildPart() as groove:
                with BuildSketch(Plane.XZ):
                    Polygon(create_dovetail_profile(is_male=False))
                extrude(amount=TOTAL_HEIGHT + 1)  # Extra for clean cut

                groove.part = groove.part.rotate(Axis.Z, 90)
                groove.part = groove.part.translate((-SPLIT_OVERLAP/2 - 0.5, y_pos, -0.5))

            right.part = right.part - groove.part

        # Add mounting holes if enabled
        if ADD_MOUNTING_HOLES:
            hole_positions = [
                (HALF_WIDTH - HOLE_INSET, TOTAL_DEPTH/2 - HOLE_INSET),
                (HALF_WIDTH - HOLE_INSET, -TOTAL_DEPTH/2 + HOLE_INSET),
            ]
            for x, y in hole_positions:
                with BuildPart() as hole:
                    Cylinder(HOLE_DIAMETER/2, TOTAL_HEIGHT)
                    hole.part = hole.part.translate((x, y, TOTAL_HEIGHT/2))
                right.part = right.part - hole.part

    return right.part


def main():
    print("=" * 60)
    print("Split Assembly Generator (Dovetail Joint)")
    print("=" * 60)
    print(f"Total assembled size: {TOTAL_WIDTH} x {TOTAL_DEPTH} x {TOTAL_HEIGHT} mm")
    print(f"Each half: ~{HALF_WIDTH + SPLIT_OVERLAP/2} x {TOTAL_DEPTH} x {TOTAL_HEIGHT} mm")
    print(f"Dovetails: {DOVETAIL_COUNT} joints, {DOVETAIL_WIDTH}mm wide")
    print(f"Dovetail angle: {DOVETAIL_ANGLE}°")
    print(f"Joint tolerance: {DOVETAIL_TOLERANCE}mm")
    print("=" * 60)

    # Generate parts
    print("\nGenerating left half (male dovetails)...")
    left = create_left_half()
    left.export_stl("split_left.stl")
    print("✓ Exported: split_left.stl")

    print("Generating right half (female grooves)...")
    right = create_right_half()
    right.export_stl("split_right.stl")
    print("✓ Exported: split_right.stl")

    # Export 3MF (preferred for Bambu Studio)
    try:
        from build123d import Mesher
        for name, part in [("split_left", left), ("split_right", right)]:
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
    stl_files = ["split_left.stl", "split_right.stl"]
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
    print("ASSEMBLY INSTRUCTIONS")
    print("=" * 60)
    print("1. Print both halves flat (best surface finish)")
    print("2. Slide dovetails together from the side")
    print("3. Parts should fit snugly - sand if too tight")
    print(f"4. If too loose, reduce DOVETAIL_TOLERANCE (current: {DOVETAIL_TOLERANCE}mm)")
    print("\nOptional: Apply CA glue at joint for permanent assembly")
    print("=" * 60)


if __name__ == "__main__":
    main()
