#!/usr/bin/env python3
"""
Generate a 5-compartment drawer divider STL file for spoons and chopsticks.

Layout: S C S S C (Spoon, Chopstick, Spoon, Spoon, Chopstick)
- S (Spoon) compartments: 53mm wide
- C (Chopstick) compartments: 41mm wide
- Horizontal compartment at back (Y=241.25mm to Y=273mm)

Specifications:
- Total width (X): 253mm (25.3cm / ~10 inches)
- Depth (Y): 273mm (6.5 gridfinity squares)
- Height (Z): 50mm
- Wall thickness: 2mm
- 5 vertical compartments at front (Y=2mm to Y=241.25mm)
- Horizontal compartment at back: 1.25 inches (31.75mm) deep
- Horizontal divider wall: 75% height (37.5mm) with circular hole lattice pattern

MANIFOLD GEOMETRY NOTES:
========================
Non-manifold edges occur when:
1. An edge is shared by more than 2 faces (T-junction)
2. An edge is shared by only 1 face (open edge/hole)
3. Faces overlap or intersect without proper boolean operations

Common causes when manually building triangle meshes:
- Overlapping faces at Z boundaries (e.g., box top at z=10, another box bottom at z=10)
- Degenerate triangles (vertices at same position or collinear)
- Incorrect winding order (normals pointing wrong direction)

Solution: Use manifold3d library for CSG (Constructive Solid Geometry).
- manifold3d guarantees watertight, manifold output
- Boolean union operations properly merge overlapping geometry
- No manual triangle construction needed
"""

import os
import numpy as np
from manifold3d import Manifold
import trimesh

# =============================================================================
# CONFIGURATION
# =============================================================================

# Overall dimensions
TOTAL_WIDTH = 253.0  # mm (X axis) - 25.3cm / ~10 inches
TOTAL_DEPTH = 273.0  # mm (Y axis) - 6.5 gridfinity squares
TOTAL_HEIGHT = 50.0  # mm (Z axis)
WALL_THICKNESS = 2.0  # mm
BOTTOM_THICKNESS = 2.0  # mm (matches successful 2compartment print)

# Horizontal compartment configuration
HORIZONTAL_COMPARTMENT_DEPTH = 31.75  # mm (1.25 inches from top edge)
HORIZONTAL_WALL_HEIGHT_RATIO = 0.75   # ratio of total height for horizontal divider (0.75 = 75%)
HORIZONTAL_WALL_LATTICE_ENABLED = True  # if True, use lattice pattern; if False, solid wall
HORIZONTAL_WALL_HOLE_DIAMETER = 8.0  # mm - diameter of circular ventilation holes
HORIZONTAL_WALL_HOLE_SPACING = 12.0  # mm - center-to-center spacing between holes

# Scallop/pillar settings for inner walls
SCALLOP_ENABLED = True
SCALLOP_RADIUS = 12.0         # mm - determines pillar spacing
SOLID_WALL_RATIO = 0.25       # ratio of wall that is solid (0.25 = bottom quarter solid)

# Compartment widths: S C S S C layout
# Total available: 253mm - 6 walls (12mm) = 241mm
# 3 Spoons (53mm each) + 2 Chopsticks (41mm each) = 159mm + 82mm = 241mm
SPOON_WIDTH = 53.0  # mm
CHOPSTICK_WIDTH = 41.0  # mm

# Layout definition
LAYOUT = [True, False, True, True, False]  # True=Spoon, False=Chopstick
LAYOUT_LABELS = ['S', 'C', 'S', 'S', 'C']

# Output path
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_compartment_widths():
    """Return list of compartment widths based on layout."""
    return [SPOON_WIDTH if is_spoon else CHOPSTICK_WIDTH for is_spoon in LAYOUT]


def create_box(x1, y1, z1, x2, y2, z2):
    """
    Create a manifold box from corner coordinates.

    manifold3d.Manifold.cube() creates a box centered at origin,
    so we translate it to the correct position.
    """
    size_x = abs(x2 - x1)
    size_y = abs(y2 - y1)
    size_z = abs(z2 - z1)

    # Create cube at origin, then translate to position
    box = Manifold.cube([size_x, size_y, size_z])
    box = box.translate([x1, y1, z1])
    return box


def create_scalloped_pillar(x1, x2, y1, y2, z_bottom, z_top, segments=16):
    """
    Create a single pillar with a scalloped (half-cylinder) top.

    The pillar has a rectangular base with a half-cylinder dome on top,
    creating a rounded scallop shape when viewed from the side.

    Args:
        x1, x2: X bounds (wall thickness)
        y1, y2: Y bounds (pillar depth)
        z_bottom, z_top: Z bounds (pillar height)
        segments: Number of segments for cylinder smoothness
    """
    wall_thickness = x2 - x1
    pillar_depth = y2 - y1
    pillar_height = z_top - z_bottom

    # Radius of the half-cylinder (half of pillar depth)
    radius = pillar_depth / 2
    center_y = (y1 + y2) / 2

    # Z position where the dome center sits
    dome_center_z = z_top - radius

    # Create half-cylinder using extrusion of semicircle cross-section
    # Build semicircle points (in Y-Z plane, centered at origin)
    angles = np.linspace(0, np.pi, segments + 1)
    semicircle_points = []
    for angle in angles:
        py = radius * np.cos(angle)  # Y offset from center
        pz = radius * np.sin(angle)  # Z offset (positive = up)
        semicircle_points.append([py, pz])

    # Close the semicircle with a flat bottom
    semicircle_points.append([semicircle_points[-1][0], 0])
    semicircle_points.append([semicircle_points[0][0], 0])

    # Convert to manifold CrossSection
    from manifold3d import CrossSection
    cross_section = CrossSection([semicircle_points])

    # Extrude along X axis
    dome = Manifold.extrude(cross_section, wall_thickness)

    # Rotate to align properly (extrude is along Z, we want X)
    dome = dome.rotate([90, 0, 90])

    # Translate to position
    dome = dome.translate([x1, center_y, dome_center_z])

    # Create rectangular base that extends up to the dome center
    # (slight overlap ensures proper union)
    base = create_box(x1, y1, z_bottom, x2, y2, dome_center_z + 0.1)

    # Union base and dome
    result = base + dome

    return result


def create_pillared_wall(x1, x2, y_start, y_end, z_bottom, z_top, pillar_spacing, solid_ratio=0.5, scalloped=True):
    """
    Create a wall with solid lower section and pillars with gaps on top.

    The gaps between pillars provide finger access for grabbing utensils.

    Args:
        x1, x2: X bounds of the wall (wall thickness direction)
        y_start, y_end: Y bounds of the wall (along depth)
        z_bottom, z_top: Z bounds of the wall (height)
        pillar_spacing: Approximate width of each pillar/gap
        solid_ratio: Fraction of wall height that is solid (0.5 = bottom half)
        scalloped: If True, pillars have half-cylinder tops; if False, rectangular

    Returns:
        Manifold object representing the wall
    """
    inner_depth = y_end - y_start
    wall_height = z_top - z_bottom
    z_mid = z_bottom + (wall_height * solid_ratio)

    parts = []

    # Solid base section (full depth, partial height)
    if solid_ratio > 0:
        base = create_box(x1, y_start, z_bottom, x2, y_end, z_mid)
        parts.append(base)

    # Pillar section on top (alternating pillars with gaps)
    if solid_ratio < 1.0:
        num_sections = max(1, int(inner_depth / (2 * pillar_spacing)))
        section_width = inner_depth / num_sections

        y = y_start
        for i in range(num_sections):
            if i % 2 == 0:  # Pillar on even indices, gap on odd
                if scalloped:
                    pillar = create_scalloped_pillar(
                        x1, x2, y, y + section_width, z_mid, z_top
                    )
                else:
                    pillar = create_box(x1, y, z_mid, x2, y + section_width, z_top)
                parts.append(pillar)
            y += section_width

    # Union all parts into single manifold
    result = parts[0]
    for p in parts[1:]:
        result = result + p  # manifold3d uses + for union

    return result


def create_latticed_horizontal_wall(x_start, x_end, y1, y2, z_bottom, z_top, hole_diameter, hole_spacing):
    """
    Create a horizontal wall with honeycomb lattice pattern (circular holes in a grid).

    The lattice provides visibility and airflow while maintaining separation between compartments.

    Args:
        x_start, x_end: X bounds of the wall (along width)
        y1, y2: Y bounds of the wall (wall thickness direction)
        z_bottom, z_top: Z bounds of the wall (height)
        hole_diameter: Diameter of each circular hole
        hole_spacing: Center-to-center spacing between holes (both X and Z directions)

    Returns:
        Manifold object representing the latticed wall
    """
    # Start with a solid wall
    wall = create_box(x_start, y1, z_bottom, x_end, y2, z_top)

    wall_width = x_end - x_start
    wall_height = z_top - z_bottom
    wall_thickness = y2 - y1

    # Calculate number of holes in each direction
    num_holes_x = max(1, int(wall_width / hole_spacing))
    num_holes_z = max(1, int(wall_height / hole_spacing))

    # Calculate actual spacing to center the pattern
    actual_spacing_x = wall_width / (num_holes_x + 1)
    actual_spacing_z = wall_height / (num_holes_z + 1)

    radius = hole_diameter / 2

    # Create holes and subtract them from the wall
    for row in range(1, num_holes_z + 1):
        z_center = z_bottom + (row * actual_spacing_z)

        for col in range(1, num_holes_x + 1):
            x_center = x_start + (col * actual_spacing_x)

            # Offset every other row for honeycomb pattern (optional)
            # x_offset = actual_spacing_x / 2 if row % 2 == 0 else 0
            # x_center += x_offset

            # Create cylinder for hole (extrude through wall thickness + extra for clean boolean)
            hole = Manifold.cylinder(
                height=wall_thickness + 0.2,  # Slightly longer to ensure clean subtraction
                radius_low=radius,
                radius_high=radius,
                circular_segments=16  # Smooth circles
            )

            # Rotate cylinder to align with Y axis (wall thickness direction)
            hole = hole.rotate([90, 0, 0])

            # Translate to position
            hole = hole.translate([x_center, (y1 + y2) / 2, z_center])

            # Subtract hole from wall
            wall = wall - hole

    return wall


def create_compartment_box():
    """
    Create a 5-compartment drawer organizer with variable widths and horizontal compartment.

    Structure:
    - 5 vertical compartments at front (Y=WALL_THICKNESS to Y=TOTAL_DEPTH-HORIZONTAL_COMPARTMENT_DEPTH)
    - Latticed horizontal divider at Y=TOTAL_DEPTH-HORIZONTAL_COMPARTMENT_DEPTH (75% of total height)
    - Horizontal compartment at back (Y=TOTAL_DEPTH-HORIZONTAL_COMPARTMENT_DEPTH to Y=TOTAL_DEPTH)

    The horizontal divider is 75% height to provide good containment for the back compartment
    while still allowing top-access for placing/removing items. The lattice pattern (circular holes)
    provides visibility into the back compartment, airflow, and reduces material usage.

    Uses manifold3d CSG operations to ensure watertight (manifold) geometry.
    All overlapping/touching faces are properly merged by the boolean union.
    """
    W = TOTAL_WIDTH
    D = TOTAL_DEPTH
    H = TOTAL_HEIGHT
    t = WALL_THICKNESS
    bt = BOTTOM_THICKNESS
    hd = HORIZONTAL_COMPARTMENT_DEPTH
    h_wall_ratio = HORIZONTAL_WALL_HEIGHT_RATIO

    compartment_widths = get_compartment_widths()
    num_compartments = len(compartment_widths)

    # Calculate vertical divider positions (X direction)
    divider_positions = []
    x_pos = t
    for i, width in enumerate(compartment_widths):
        x_pos += width
        if i < num_compartments - 1:
            divider_positions.append((x_pos, x_pos + t))
            x_pos += t

    # Calculate horizontal divider position and height
    horizontal_divider_y = D - hd  # Position from back (Y direction)
    horizontal_wall_height = bt + (H * h_wall_ratio)  # Height (Z direction)

    print("  Creating geometry components...")

    # Start with bottom plate
    result = create_box(0, 0, 0, W, D, bt)

    # Add outer walls (full height)
    result = result + create_box(0, 0, bt, t, D, H)       # Left wall
    result = result + create_box(W - t, 0, bt, W, D, H)   # Right wall
    result = result + create_box(t, 0, bt, W - t, t, H)   # Front wall
    result = result + create_box(t, D - t, bt, W - t, D, H)  # Back wall

    # Add horizontal divider wall (latticed or solid)
    if HORIZONTAL_WALL_LATTICE_ENABLED:
        # Calculate approximate number of holes for user info
        wall_width = W - 2*t
        wall_height = horizontal_wall_height - bt
        num_holes_x = int(wall_width / HORIZONTAL_WALL_HOLE_SPACING)
        num_holes_z = int(wall_height / HORIZONTAL_WALL_HOLE_SPACING)
        total_holes = num_holes_x * num_holes_z

        print(f"  Adding latticed horizontal divider at Y={horizontal_divider_y}mm (height: {horizontal_wall_height}mm / {h_wall_ratio*100:.0f}%)...")
        print(f"    Hole pattern: {HORIZONTAL_WALL_HOLE_DIAMETER}mm diameter, {HORIZONTAL_WALL_HOLE_SPACING}mm spacing (~{total_holes} holes)...")
        horizontal_divider = create_latticed_horizontal_wall(
            t, W - t, horizontal_divider_y, horizontal_divider_y + t, bt, horizontal_wall_height,
            HORIZONTAL_WALL_HOLE_DIAMETER, HORIZONTAL_WALL_HOLE_SPACING
        )
    else:
        print(f"  Adding solid horizontal divider at Y={horizontal_divider_y}mm (height: {horizontal_wall_height}mm / {h_wall_ratio*100:.0f}%)...")
        horizontal_divider = create_box(t, horizontal_divider_y, bt, W - t, horizontal_divider_y + t, horizontal_wall_height)
    result = result + horizontal_divider

    # Add vertical inner dividers (only in the front section, before horizontal compartment)
    vertical_end_y = horizontal_divider_y  # End at the horizontal divider
    print(f"  Adding {len(divider_positions)} vertical dividers (Y={t}mm to Y={vertical_end_y}mm)...")
    for i, (left, right) in enumerate(divider_positions):
        print(f"    Divider {i+1}/{len(divider_positions)}...", end='\r')
        if SCALLOP_ENABLED:
            wall = create_pillared_wall(
                left, right, t, vertical_end_y, bt, H,
                SCALLOP_RADIUS, SOLID_WALL_RATIO
            )
        else:
            wall = create_box(left, t, bt, right, vertical_end_y, H)
        result = result + wall
    print()

    return result


def manifold_to_trimesh(manifold_mesh):
    """Convert a manifold3d Manifold to a trimesh.Trimesh object."""
    mesh_data = manifold_mesh.to_mesh()
    vertices = np.array(mesh_data.vert_properties)[:, :3]  # Get XYZ coordinates
    faces = np.array(mesh_data.tri_verts)
    return trimesh.Trimesh(vertices=vertices, faces=faces)


def validate_mesh(mesh, name="mesh"):
    """
    Validate mesh for 3D printing readiness.

    Checks:
    - Watertight (closed, no holes)
    - Consistent winding (normals point outward)
    - Positive volume
    - Euler characteristic (should be 2 for single closed surface)
    """
    print(f"\n{'='*50}")
    print(f"MESH VALIDATION: {name}")
    print(f"{'='*50}")

    issues = []

    # Basic stats
    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces: {len(mesh.faces)}")
    print(f"  Volume: {mesh.volume:.2f} mm³")

    # Watertight check
    if mesh.is_watertight:
        print(f"  ✅ Watertight: Yes")
    else:
        print(f"  ❌ Watertight: No")
        issues.append("Not watertight (has holes or non-manifold edges)")

    # Winding consistency
    if mesh.is_winding_consistent:
        print(f"  ✅ Consistent winding: Yes")
    else:
        print(f"  ❌ Consistent winding: No")
        issues.append("Inconsistent face winding")

    # Volume check
    if mesh.volume > 0:
        print(f"  ✅ Positive volume: Yes")
    else:
        print(f"  ❌ Positive volume: No")
        issues.append("Negative or zero volume")

    # Euler characteristic
    euler = len(mesh.vertices) - len(mesh.edges_unique) + len(mesh.faces)
    if euler == 2:
        print(f"  ✅ Euler characteristic: {euler} (valid closed surface)")
    else:
        print(f"  ⚠️  Euler characteristic: {euler} (expected 2)")
        issues.append(f"Euler characteristic is {euler}, expected 2")

    # Dimensions
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    print(f"  Dimensions: {dims[0]:.2f} x {dims[1]:.2f} x {dims[2]:.2f} mm")

    if issues:
        print(f"\n  ⚠️  {len(issues)} issue(s) found:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    else:
        print(f"\n  ✅ Mesh is valid for 3D printing!")
        return True


def main():
    print("="*60)
    print("5-Compartment Spoon/Chopstick Drawer Divider Generator")
    print("="*60)
    print("Using manifold3d for guaranteed watertight CSG operations")

    print(f"\nLayout: {' '.join(LAYOUT_LABELS)}")
    print(f"  S = Spoon compartment ({SPOON_WIDTH}mm)")
    print(f"  C = Chopstick compartment ({CHOPSTICK_WIDTH}mm)")

    print(f"\nSpecifications:")
    print(f"  Total Width (X): {TOTAL_WIDTH} mm ({TOTAL_WIDTH/10:.1f} cm)")
    print(f"  Total Depth (Y): {TOTAL_DEPTH} mm")
    print(f"  Total Height (Z): {TOTAL_HEIGHT} mm")
    print(f"  Wall Thickness: {WALL_THICKNESS} mm")
    print(f"  Bottom Thickness: {BOTTOM_THICKNESS} mm")
    horizontal_divider_y = TOTAL_DEPTH - HORIZONTAL_COMPARTMENT_DEPTH
    horizontal_wall_height = BOTTOM_THICKNESS + (TOTAL_HEIGHT * HORIZONTAL_WALL_HEIGHT_RATIO)
    print(f"\nHorizontal Compartment (at back):")
    print(f"  Position: Y={horizontal_divider_y} mm to Y={TOTAL_DEPTH} mm")
    print(f"  Depth: {HORIZONTAL_COMPARTMENT_DEPTH} mm (1.25 inches)")
    print(f"  Spans full width: {TOTAL_WIDTH - 2*WALL_THICKNESS} mm")
    print(f"  Divider wall height: {horizontal_wall_height:.1f} mm ({HORIZONTAL_WALL_HEIGHT_RATIO*100:.0f}% of total height)")
    if HORIZONTAL_WALL_LATTICE_ENABLED:
        wall_width = TOTAL_WIDTH - 2*WALL_THICKNESS
        wall_height = horizontal_wall_height - BOTTOM_THICKNESS
        num_holes_x = int(wall_width / HORIZONTAL_WALL_HOLE_SPACING)
        num_holes_z = int(wall_height / HORIZONTAL_WALL_HOLE_SPACING)
        total_holes = num_holes_x * num_holes_z
        print(f"  Divider type: Latticed with circular holes")
        print(f"    Hole diameter: {HORIZONTAL_WALL_HOLE_DIAMETER}mm, spacing: {HORIZONTAL_WALL_HOLE_SPACING}mm")
        print(f"    Approximate holes: {num_holes_x} wide × {num_holes_z} tall = ~{total_holes} total holes")
    else:
        print(f"  Divider type: Solid wall")
    print(f"  Divider at Y={horizontal_divider_y} mm")

    compartment_widths = get_compartment_widths()
    num_walls = len(compartment_widths) + 1
    total_wall_width = num_walls * WALL_THICKNESS
    total_compartment_width = sum(compartment_widths)

    print(f"\nCompartment Details:")
    x_pos = WALL_THICKNESS
    for i, (label, width) in enumerate(zip(LAYOUT_LABELS, compartment_widths)):
        comp_type = "Spoon" if label == 'S' else "Chopstick"
        print(f"  [{i+1}] {comp_type}: {width}mm (X: {x_pos:.1f} to {x_pos + width:.1f})")
        x_pos += width + WALL_THICKNESS

    print(f"\nVerification:")
    print(f"  Total wall width: {total_wall_width}mm ({num_walls} walls x {WALL_THICKNESS}mm)")
    print(f"  Total compartment width: {total_compartment_width}mm")
    print(f"  Sum: {total_wall_width + total_compartment_width}mm (target: {TOTAL_WIDTH}mm)")

    print(f"\nVertical Compartment Details (at front):")
    print(f"  Start position: Y={WALL_THICKNESS}mm")
    print(f"  End position: Y={horizontal_divider_y}mm")
    vertical_depth = horizontal_divider_y - WALL_THICKNESS
    print(f"  Vertical compartment depth: {vertical_depth:.1f}mm")

    if SCALLOP_ENABLED:
        wall_height = TOTAL_HEIGHT - BOTTOM_THICKNESS
        solid_height = wall_height * SOLID_WALL_RATIO

        num_sections = int(vertical_depth / (2 * SCALLOP_RADIUS))
        num_pillars = (num_sections + 1) // 2

        print(f"\nPillared Vertical Dividers:")
        print(f"  Solid base height: {solid_height:.1f}mm ({SOLID_WALL_RATIO*100:.0f}%)")
        print(f"  Pillared section height: {wall_height - solid_height:.1f}mm")
        print(f"  Pillars per vertical divider: {num_pillars}")

    # Create the mesh using manifold3d
    print(f"\nGenerating mesh with manifold3d...")
    manifold_mesh = create_compartment_box()

    # Convert to trimesh for validation and export
    print("  Converting to trimesh...")
    mesh = manifold_to_trimesh(manifold_mesh)

    # Validate
    validate_mesh(mesh, "Generated Mesh")

    # Save
    output_path = f"{OUTPUT_DIR}/5compartment_253x273x50_SCSSC_horizontal-shelf_2mm-walls.stl"
    mesh.export(output_path)
    print(f"\n✅ STL saved to: {output_path}")
    print(f"   Configuration: {int(TOTAL_WIDTH)}x{int(TOTAL_DEPTH)}x{int(TOTAL_HEIGHT)}mm")
    print(f"   Layout: {' '.join(LAYOUT_LABELS)} with horizontal compartment")
    print(f"   Wall/Base: {int(WALL_THICKNESS)}mm walls, {int(BOTTOM_THICKNESS)}mm base, {SOLID_WALL_RATIO*100:.0f}% solid ratio")

    return mesh


if __name__ == "__main__":
    main()
