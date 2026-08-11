#!/usr/bin/env python3
"""
Gridfinity Base Generator
Creates a Gridfinity-compatible baseplate
Based on the Gridfinity specification by Zack Freedman

Gridfinity is a modular storage system with standardized grid dimensions.
Standard grid: 42mm x 42mm cells

Usage:
    python gridfinity_base.py
    # Modify parameters below then run
"""
from build123d import *
import math

# === DESIGN PARAMETERS ===
# All dimensions in mm

# Grid size (number of 42mm cells)
GRID_X = 3      # Number of cells in X
GRID_Y = 2      # Number of cells in Y

# Gridfinity standard dimensions (don't modify unless customizing)
CELL_SIZE = 42.0        # Standard Gridfinity cell size
CELL_CLEARANCE = 0.5    # Gap between cells for bin fit
BASE_HEIGHT = 5.0       # Standard base height

# Magnet holes (optional)
ADD_MAGNETS = True
MAGNET_DIAMETER = 6.5   # 6x2mm magnets with tolerance
MAGNET_DEPTH = 2.4      # Depth for magnets

# Screw holes (optional, for mounting to surface)
ADD_SCREW_HOLES = True
SCREW_DIAMETER = 4.2    # M4 clearance
SCREW_HEAD_DIA = 8.0    # M4 countersink
SCREW_HEAD_DEPTH = 2.5  # Countersink depth

# Base options
SOLID_BASE = False      # True for solid, False for weight-saving pockets
POCKET_DEPTH = 3.0      # Depth of weight-saving pockets

# Corner radius
CORNER_RADIUS = 1.0

# === DERIVED PARAMETERS ===
TOTAL_WIDTH = GRID_X * CELL_SIZE
TOTAL_DEPTH = GRID_Y * CELL_SIZE

# Gridfinity profile dimensions (standard spec)
PROFILE_HEIGHT = 2.2
PROFILE_BOTTOM_WIDTH = 1.6
PROFILE_TOP_WIDTH = 2.4


def create_cell_profile():
    """Create the Gridfinity cell profile (the raised lip around each cell)."""
    # Standard Gridfinity profile is a chamfered edge
    # Bottom: 1.6mm wide, 45° chamfer up 0.8mm, vertical 1.4mm

    inner_size = CELL_SIZE - CELL_CLEARANCE

    with BuildSketch() as profile:
        # Outer rectangle
        Rectangle(inner_size, inner_size)
        fillet(vertices(), radius=CORNER_RADIUS)

        # Inner cutout (creates the rim)
        rim_width = PROFILE_TOP_WIDTH
        Rectangle(inner_size - 2*rim_width, inner_size - 2*rim_width, mode=Mode.SUBTRACT)

    return profile


def create_base():
    """Create the Gridfinity baseplate."""
    with BuildPart() as base:
        # Main base plate
        with BuildSketch():
            Rectangle(TOTAL_WIDTH, TOTAL_DEPTH)
            fillet(vertices(), radius=CORNER_RADIUS * 2)
        extrude(amount=BASE_HEIGHT)

        # Create cell profiles
        for gx in range(GRID_X):
            for gy in range(GRID_Y):
                cell_center_x = -TOTAL_WIDTH/2 + CELL_SIZE/2 + gx * CELL_SIZE
                cell_center_y = -TOTAL_DEPTH/2 + CELL_SIZE/2 + gy * CELL_SIZE

                # Cell lip profile
                with BuildSketch(Plane.XY.offset(BASE_HEIGHT - PROFILE_HEIGHT)):
                    with Locations((cell_center_x, cell_center_y)):
                        cell_size = CELL_SIZE - CELL_CLEARANCE
                        Rectangle(cell_size, cell_size)
                        fillet(vertices(), radius=CORNER_RADIUS)
                extrude(amount=PROFILE_HEIGHT)

                # Chamfer the inner edge
                with BuildSketch(Plane.XY.offset(BASE_HEIGHT - PROFILE_HEIGHT)):
                    with Locations((cell_center_x, cell_center_y)):
                        inner_size = cell_size - 2 * PROFILE_TOP_WIDTH
                        Rectangle(inner_size, inner_size)
                        fillet(vertices(), radius=CORNER_RADIUS)
                extrude(amount=PROFILE_HEIGHT, mode=Mode.SUBTRACT)

                # Add magnet holes if enabled
                if ADD_MAGNETS:
                    magnet_offset = CELL_SIZE / 2 - 4.8  # Standard position

                    magnet_positions = [
                        (cell_center_x - magnet_offset, cell_center_y - magnet_offset),
                        (cell_center_x + magnet_offset, cell_center_y - magnet_offset),
                        (cell_center_x - magnet_offset, cell_center_y + magnet_offset),
                        (cell_center_x + magnet_offset, cell_center_y + magnet_offset),
                    ]

                    for mx, my in magnet_positions:
                        with BuildSketch(base.faces().sort_by(Axis.Z)[0]):
                            with Locations((mx, my)):
                                Circle(MAGNET_DIAMETER / 2)
                        extrude(amount=MAGNET_DEPTH, mode=Mode.SUBTRACT)

        # Weight-saving pockets (optional)
        if not SOLID_BASE:
            pocket_inset = 3.0
            for gx in range(GRID_X):
                for gy in range(GRID_Y):
                    cell_center_x = -TOTAL_WIDTH/2 + CELL_SIZE/2 + gx * CELL_SIZE
                    cell_center_y = -TOTAL_DEPTH/2 + CELL_SIZE/2 + gy * CELL_SIZE

                    pocket_size = CELL_SIZE - 2 * pocket_inset - CELL_CLEARANCE

                    with BuildSketch(base.faces().sort_by(Axis.Z)[0]):
                        with Locations((cell_center_x, cell_center_y)):
                            Rectangle(pocket_size, pocket_size)
                            fillet(vertices(), radius=2)
                    extrude(amount=POCKET_DEPTH, mode=Mode.SUBTRACT)

        # Screw holes for mounting (corners)
        if ADD_SCREW_HOLES:
            screw_inset = 8.0
            screw_positions = [
                (-TOTAL_WIDTH/2 + screw_inset, -TOTAL_DEPTH/2 + screw_inset),
                (TOTAL_WIDTH/2 - screw_inset, -TOTAL_DEPTH/2 + screw_inset),
                (-TOTAL_WIDTH/2 + screw_inset, TOTAL_DEPTH/2 - screw_inset),
                (TOTAL_WIDTH/2 - screw_inset, TOTAL_DEPTH/2 - screw_inset),
            ]

            for sx, sy in screw_positions:
                # Through hole
                with BuildSketch(base.faces().sort_by(Axis.Z)[-1]):
                    with Locations((sx, sy)):
                        Circle(SCREW_DIAMETER / 2)
                extrude(amount=-BASE_HEIGHT, mode=Mode.SUBTRACT)

                # Countersink
                with BuildSketch(base.faces().sort_by(Axis.Z)[0]):
                    with Locations((sx, sy)):
                        Circle(SCREW_HEAD_DIA / 2)
                extrude(amount=SCREW_HEAD_DEPTH, mode=Mode.SUBTRACT)

    return base.part


def main():
    print("=" * 60)
    print("Gridfinity Base Generator")
    print("=" * 60)
    print(f"Grid size: {GRID_X} x {GRID_Y} cells")
    print(f"Total dimensions: {TOTAL_WIDTH} x {TOTAL_DEPTH} x {BASE_HEIGHT} mm")
    print(f"Cell size: {CELL_SIZE}mm (standard Gridfinity)")
    print(f"Magnets: {'Yes' if ADD_MAGNETS else 'No'} ({MAGNET_DIAMETER - 0.5}x{MAGNET_DEPTH - 0.4}mm)")
    print(f"Screw holes: {'Yes' if ADD_SCREW_HOLES else 'No'}")
    print(f"Base type: {'Solid' if SOLID_BASE else 'Weight-saving pockets'}")
    print("=" * 60)

    # Generate base
    print("\nGenerating Gridfinity base...")
    base = create_base()

    filename = f"gridfinity_base_{GRID_X}x{GRID_Y}.stl"
    base.export_stl(filename)
    print(f"✓ Exported: {filename}")

    # Export 3MF (preferred for Bambu Studio)
    try:
        from build123d import Mesher
        mf_name = f"gridfinity_base_{GRID_X}x{GRID_Y}.3mf"
        with Mesher() as m:
            m.add_shape(base)
            m.write(mf_name)
        print(f"✓ Exported: {mf_name} (preferred for Bambu Studio)")
    except Exception as e:
        print(f"  3MF export unavailable: {e}")

    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    try:
        import trimesh
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
        generate_previews(filename)
    except ImportError:
        print("Note: Install numpy-stl matplotlib for preview images")

    print("\n" + "=" * 60)
    print("PRINT SETTINGS")
    print("=" * 60)
    print("- Layer height: 0.2mm")
    print("- Infill: 15-20% (or 0% with 4+ walls for speed)")
    print("- Supports: Not needed")
    print("- First layer: Ensure good adhesion for magnet holes")
    if ADD_MAGNETS:
        print(f"\nMagnets needed: {GRID_X * GRID_Y * 4}x 6x2mm neodymium magnets")
        print("Insert magnets before completing print (pause at magnet layer)")
        print("Or glue magnets after printing")
    if ADD_SCREW_HOLES:
        print(f"\nScrews: 4x M4 countersunk screws")
    print("=" * 60)
    print("\nGridfinity bins are available on Printables, MakerWorld, and Thangs")
    print("Search 'Gridfinity' for compatible storage bins")


if __name__ == "__main__":
    main()
