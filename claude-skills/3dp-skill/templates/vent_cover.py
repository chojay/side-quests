#!/usr/bin/env python3
"""
Parametric Vent Cover Generator
Creates a vent/grille cover with configurable louver pattern
Designed for FDM 3D printing on Bambu H2D

Usage:
    python vent_cover.py
    # Modify parameters below then run
"""
from build123d import *
import math

# === DESIGN PARAMETERS ===
# All dimensions in mm

# Opening dimensions (measure the vent opening)
OPENING_WIDTH = 200.0       # Width of vent opening
OPENING_HEIGHT = 100.0      # Height of vent opening

# Frame
FRAME_WIDTH = 10.0          # Frame border around opening
FRAME_THICKNESS = 3.0       # How thick the frame is (Z depth)
FRAME_CORNER_RADIUS = 3.0   # Rounded corners on frame

# Louver pattern
LOUVER_COUNT = 8            # Number of horizontal louvers
LOUVER_THICKNESS = 1.5      # Thickness of each louver blade
LOUVER_ANGLE = 30.0         # Angle of louvers (0=flat, 45=max privacy)
LOUVER_GAP = 1.0            # Gap between louver tips for airflow

# Mounting
ADD_SCREW_HOLES = True
SCREW_HOLE_DIA = 3.5        # M3 clearance
SCREW_INSET = 5.0           # Distance from outer edge

# Lip (insert into vent opening)
ADD_LIP = True
LIP_DEPTH = 5.0             # How far lip extends behind frame
LIP_THICKNESS = 1.5         # Wall thickness of lip
LIP_TOLERANCE = 0.5         # Clearance for fit into opening

# === DERIVED PARAMETERS ===
TOTAL_WIDTH = OPENING_WIDTH + 2 * FRAME_WIDTH
TOTAL_HEIGHT = OPENING_HEIGHT + 2 * FRAME_WIDTH

# Louver spacing
LOUVER_SPACING = OPENING_HEIGHT / (LOUVER_COUNT + 1)
LOUVER_DEPTH = LOUVER_SPACING - LOUVER_GAP
LOUVER_Z_EXTENT = LOUVER_DEPTH * math.sin(math.radians(LOUVER_ANGLE))


def create_vent_cover():
    """Create the vent cover with louvers."""
    with BuildPart() as cover:
        # Frame plate
        with BuildSketch():
            Rectangle(TOTAL_WIDTH, TOTAL_HEIGHT)
            if FRAME_CORNER_RADIUS > 0:
                fillet(vertices(), radius=FRAME_CORNER_RADIUS)
        extrude(amount=FRAME_THICKNESS)

        # Cut opening in frame
        with BuildSketch(cover.faces().sort_by(Axis.Z)[-1]):
            Rectangle(OPENING_WIDTH, OPENING_HEIGHT)
        extrude(amount=-FRAME_THICKNESS, mode=Mode.SUBTRACT)

        # Add louver blades
        for i in range(LOUVER_COUNT):
            y_pos = -OPENING_HEIGHT / 2 + LOUVER_SPACING * (i + 1)

            with BuildPart() as blade:
                # Create angled louver blade
                with BuildSketch(Plane.XZ):
                    # Trapezoid profile for the louver cross-section
                    with Locations((0, FRAME_THICKNESS / 2)):
                        Rectangle(OPENING_WIDTH - 2, LOUVER_THICKNESS)
                extrude(amount=LOUVER_DEPTH)

                # Rotate to desired angle
                blade.part = blade.part.rotate(Axis.X, LOUVER_ANGLE)
                # Position
                blade.part = blade.part.translate((0, y_pos, 0))

            cover.part = cover.part + blade.part

        # Add screw holes
        if ADD_SCREW_HOLES:
            hole_positions = [
                (-TOTAL_WIDTH / 2 + SCREW_INSET, TOTAL_HEIGHT / 2 - SCREW_INSET),
                (TOTAL_WIDTH / 2 - SCREW_INSET, TOTAL_HEIGHT / 2 - SCREW_INSET),
                (-TOTAL_WIDTH / 2 + SCREW_INSET, -TOTAL_HEIGHT / 2 + SCREW_INSET),
                (TOTAL_WIDTH / 2 - SCREW_INSET, -TOTAL_HEIGHT / 2 + SCREW_INSET),
            ]
            for x, y in hole_positions:
                with BuildSketch(cover.faces().sort_by(Axis.Z)[-1]):
                    with Locations((x, y)):
                        Circle(SCREW_HOLE_DIA / 2)
                extrude(amount=-FRAME_THICKNESS, mode=Mode.SUBTRACT)

        # Add insertion lip
        if ADD_LIP:
            lip_w = OPENING_WIDTH - LIP_TOLERANCE
            lip_h = OPENING_HEIGHT - LIP_TOLERANCE

            with BuildPart() as lip:
                # Outer lip rectangle
                with BuildSketch(Plane.XY.offset(-LIP_DEPTH)):
                    Rectangle(lip_w, lip_h)
                    # Hollow out
                    Rectangle(lip_w - 2 * LIP_THICKNESS, lip_h - 2 * LIP_THICKNESS,
                              mode=Mode.SUBTRACT)
                extrude(amount=LIP_DEPTH)

            cover.part = cover.part + lip.part

    return cover.part


def main():
    print("=" * 60)
    print("Parametric Vent Cover Generator")
    print("=" * 60)
    print(f"Opening: {OPENING_WIDTH} x {OPENING_HEIGHT} mm")
    print(f"Total size: {TOTAL_WIDTH} x {TOTAL_HEIGHT} x {FRAME_THICKNESS} mm")
    print(f"Louvers: {LOUVER_COUNT} at {LOUVER_ANGLE} degrees")
    print(f"Lip: {'Yes' if ADD_LIP else 'No'} ({LIP_DEPTH}mm depth)")
    print(f"Screw holes: {'Yes' if ADD_SCREW_HOLES else 'No'}")
    print("=" * 60)

    # Generate
    print("\nGenerating vent cover...")
    cover = create_vent_cover()

    # Export STL
    cover.export_stl("vent_cover.stl")
    print("Exported: vent_cover.stl")

    # Export 3MF (preferred for Bambu Studio)
    try:
        from build123d import Mesher
        with Mesher() as m:
            m.add_shape(cover)
            m.write("vent_cover.3mf")
        print("Exported: vent_cover.3mf (preferred for Bambu Studio)")
    except Exception as e:
        print(f"3MF export unavailable: {e}")

    # Validate
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    try:
        import trimesh
        mesh = trimesh.load("vent_cover.stl")
        status = "PASS" if mesh.is_watertight else "FAIL"
        print(f"Watertight: {status}")
        print(f"Volume: {mesh.volume:.2f} mm3")
        dims = mesh.bounds[1] - mesh.bounds[0]
        print(f"Dimensions: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")

        # Bambu H2D build volume check
        limits = (325, 320, 325)
        for i, (d, l) in enumerate(zip(dims, limits)):
            if d > l:
                print(f"WARNING: {'XYZ'[i]} = {d:.1f}mm exceeds H2D limit {l}mm")
    except ImportError:
        print("Install trimesh for validation: pip install trimesh")

    print("\n" + "=" * 60)
    print("PRINT SETTINGS")
    print("=" * 60)
    print("- Layer height: 0.2mm")
    print("- Infill: 20-30% (structural)")
    print("- Supports: May be needed for angled louvers")
    print(f"- Print flat (frame face down)")
    if ADD_SCREW_HOLES:
        print(f"- Hardware: 4x M{int(SCREW_HOLE_DIA - 0.5)} screws")
    print("=" * 60)


if __name__ == "__main__":
    main()
