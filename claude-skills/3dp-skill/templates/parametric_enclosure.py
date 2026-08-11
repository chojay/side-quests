#!/usr/bin/env python3
"""
Parametric Electronics Enclosure Generator
Creates a two-part enclosure with mounting posts and ventilation
Designed for FDM 3D printing

Usage:
    python parametric_enclosure.py
    # Modify parameters below then run
"""
from build123d import *
import math

# === DESIGN PARAMETERS ===
# All dimensions in mm

# Outer dimensions
WIDTH = 100.0       # X dimension
DEPTH = 80.0        # Y dimension
HEIGHT = 35.0       # Total height (both halves combined)

# Wall specifications
WALL_THICKNESS = 2.5
FLOOR_THICKNESS = 2.5

# Split configuration
BOTTOM_HEIGHT = 25.0    # Height of bottom half
TOP_HEIGHT = HEIGHT - BOTTOM_HEIGHT

# Screw/mounting specifications
SCREW_HOLE_DIA = 3.2        # M3 clearance
SCREW_POST_DIA = 8.0        # Diameter of screw posts
SCREW_POST_INSET = 5.0      # Distance from corner

# Lip for lid alignment
LIP_WIDTH = 2.0
LIP_HEIGHT = 2.0
LIP_TOLERANCE = 0.3

# Corner radius
CORNER_RADIUS = 4.0

# Ventilation slots (set to 0 to disable)
VENT_SLOT_WIDTH = 2.0
VENT_SLOT_LENGTH = 15.0
VENT_SLOT_SPACING = 5.0
VENT_SLOT_COUNT = 5

# Cable entry hole (set diameter to 0 to disable)
CABLE_HOLE_DIA = 8.0
CABLE_HOLE_Y_POS = DEPTH / 2 - 15  # Position from center

# === DERIVED PARAMETERS ===
INNER_WIDTH = WIDTH - 2 * WALL_THICKNESS
INNER_DEPTH = DEPTH - 2 * WALL_THICKNESS


def create_bottom_half():
    """Create the bottom enclosure half with screw posts."""
    inner_height = BOTTOM_HEIGHT - FLOOR_THICKNESS

    with BuildPart() as bottom:
        # Outer shell
        with BuildSketch():
            Rectangle(WIDTH, DEPTH)
            if CORNER_RADIUS > 0:
                fillet(vertices(), radius=CORNER_RADIUS)
        extrude(amount=BOTTOM_HEIGHT)

        # Hollow out
        with BuildSketch(bottom.faces().sort_by(Axis.Z)[-1]):
            Rectangle(INNER_WIDTH, INNER_DEPTH)
            if CORNER_RADIUS > 0:
                inner_radius = max(CORNER_RADIUS - WALL_THICKNESS, 1)
                fillet(vertices(), radius=inner_radius)
        extrude(amount=-inner_height, mode=Mode.SUBTRACT)

        # Screw posts at corners
        post_positions = [
            (WIDTH/2 - SCREW_POST_INSET - WALL_THICKNESS, DEPTH/2 - SCREW_POST_INSET - WALL_THICKNESS),
            (-WIDTH/2 + SCREW_POST_INSET + WALL_THICKNESS, DEPTH/2 - SCREW_POST_INSET - WALL_THICKNESS),
            (WIDTH/2 - SCREW_POST_INSET - WALL_THICKNESS, -DEPTH/2 + SCREW_POST_INSET + WALL_THICKNESS),
            (-WIDTH/2 + SCREW_POST_INSET + WALL_THICKNESS, -DEPTH/2 + SCREW_POST_INSET + WALL_THICKNESS),
        ]

        for x, y in post_positions:
            with BuildSketch(Plane.XY.offset(FLOOR_THICKNESS)):
                with Locations((x, y)):
                    Circle(SCREW_POST_DIA / 2)
            extrude(amount=inner_height)

        # Screw holes through posts
        for x, y in post_positions:
            with BuildSketch(bottom.faces().sort_by(Axis.Z)[-1]):
                with Locations((x, y)):
                    Circle(SCREW_HOLE_DIA / 2)
            extrude(amount=-BOTTOM_HEIGHT, mode=Mode.SUBTRACT)

        # Alignment lip around top edge
        with BuildSketch(bottom.faces().sort_by(Axis.Z)[-1]):
            Rectangle(INNER_WIDTH, INNER_DEPTH)
            if CORNER_RADIUS > 0:
                inner_radius = max(CORNER_RADIUS - WALL_THICKNESS, 1)
                fillet(vertices(), radius=inner_radius)
            # Subtract inner rectangle for lip
            Rectangle(INNER_WIDTH - 2*LIP_WIDTH, INNER_DEPTH - 2*LIP_WIDTH, mode=Mode.SUBTRACT)
            if CORNER_RADIUS > 0:
                # Can't easily fillet the subtracted shape, skip
                pass
        extrude(amount=LIP_HEIGHT)

        # Cable entry hole (on front face)
        if CABLE_HOLE_DIA > 0:
            with BuildSketch(Plane.XZ.offset(-DEPTH/2)):
                with Locations((0, BOTTOM_HEIGHT/2)):
                    Circle(CABLE_HOLE_DIA / 2)
            extrude(amount=-WALL_THICKNESS - 1, mode=Mode.SUBTRACT)

    return bottom.part


def create_top_half():
    """Create the top enclosure half."""
    with BuildPart() as top:
        # Outer shell
        with BuildSketch():
            Rectangle(WIDTH, DEPTH)
            if CORNER_RADIUS > 0:
                fillet(vertices(), radius=CORNER_RADIUS)
        extrude(amount=TOP_HEIGHT)

        # Hollow out (from bottom for top piece)
        inner_height = TOP_HEIGHT - FLOOR_THICKNESS
        with BuildSketch(top.faces().sort_by(Axis.Z)[0]):
            Rectangle(INNER_WIDTH, INNER_DEPTH)
            if CORNER_RADIUS > 0:
                inner_radius = max(CORNER_RADIUS - WALL_THICKNESS, 1)
                fillet(vertices(), radius=inner_radius)
        extrude(amount=inner_height, mode=Mode.SUBTRACT)

        # Screw holes for assembly
        post_positions = [
            (WIDTH/2 - SCREW_POST_INSET - WALL_THICKNESS, DEPTH/2 - SCREW_POST_INSET - WALL_THICKNESS),
            (-WIDTH/2 + SCREW_POST_INSET + WALL_THICKNESS, DEPTH/2 - SCREW_POST_INSET - WALL_THICKNESS),
            (WIDTH/2 - SCREW_POST_INSET - WALL_THICKNESS, -DEPTH/2 + SCREW_POST_INSET + WALL_THICKNESS),
            (-WIDTH/2 + SCREW_POST_INSET + WALL_THICKNESS, -DEPTH/2 + SCREW_POST_INSET + WALL_THICKNESS),
        ]

        for x, y in post_positions:
            with BuildSketch(top.faces().sort_by(Axis.Z)[-1]):
                with Locations((x, y)):
                    Circle(SCREW_HOLE_DIA / 2)
            extrude(amount=-TOP_HEIGHT, mode=Mode.SUBTRACT)

        # Ventilation slots on top
        if VENT_SLOT_COUNT > 0 and VENT_SLOT_WIDTH > 0:
            total_vent_width = VENT_SLOT_COUNT * VENT_SLOT_WIDTH + (VENT_SLOT_COUNT - 1) * VENT_SLOT_SPACING
            start_x = -total_vent_width / 2 + VENT_SLOT_WIDTH / 2

            with BuildSketch(top.faces().sort_by(Axis.Z)[-1]):
                for i in range(VENT_SLOT_COUNT):
                    x = start_x + i * (VENT_SLOT_WIDTH + VENT_SLOT_SPACING)
                    with Locations((x, 0)):
                        SlotOverall(VENT_SLOT_LENGTH, VENT_SLOT_WIDTH)
            extrude(amount=-FLOOR_THICKNESS, mode=Mode.SUBTRACT)

    return top.part


def main():
    print("=" * 60)
    print("Parametric Electronics Enclosure Generator")
    print("=" * 60)
    print(f"Outer dimensions: {WIDTH} x {DEPTH} x {HEIGHT} mm")
    print(f"Inner dimensions: {INNER_WIDTH} x {INNER_DEPTH} mm")
    print(f"Bottom half height: {BOTTOM_HEIGHT} mm")
    print(f"Top half height: {TOP_HEIGHT} mm")
    print(f"Wall thickness: {WALL_THICKNESS} mm")
    print(f"Screw size: M{int(SCREW_HOLE_DIA)} clearance")
    print("=" * 60)

    # Generate parts
    print("\nGenerating bottom half...")
    bottom = create_bottom_half()
    bottom.export_stl("enclosure_bottom.stl")
    print("✓ Exported: enclosure_bottom.stl")

    print("Generating top half...")
    top = create_top_half()
    top.export_stl("enclosure_top.stl")
    print("✓ Exported: enclosure_top.stl")

    # Export 3MF (preferred for Bambu Studio)
    try:
        from build123d import Mesher
        for name, part in [("enclosure_bottom", bottom), ("enclosure_top", top)]:
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
    stl_files = ["enclosure_bottom.stl", "enclosure_top.stl"]
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
    print("ASSEMBLY")
    print("=" * 60)
    print("Hardware needed:")
    print(f"- 4x M{int(SCREW_HOLE_DIA)} screws (length: {BOTTOM_HEIGHT - FLOOR_THICKNESS + 5}mm)")
    print(f"- Optional: M{int(SCREW_HOLE_DIA)} heat-set inserts for bottom posts")
    print("\nPrint settings:")
    print("- Layer height: 0.2mm")
    print("- Infill: 20%")
    print("- Top needs supports for screw holes")
    print("- Bottom prints flat, no supports needed")
    print("=" * 60)


if __name__ == "__main__":
    main()
