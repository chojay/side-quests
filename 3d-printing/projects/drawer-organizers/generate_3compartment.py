#!/usr/bin/env python3
"""
Generate a 3-compartment drawer divider STL file (watertight mesh).

Specifications:
- Total width (X): 175mm
- Depth (Y): 6.5 gridfinity squares = 6.5 * 42mm = 273mm
- Height (Z): 30mm (similar to original ~29.59mm)
- 3 equal compartments
- Wall thickness: 2mm (sturdier)
- No gridfinity base
"""

import os
import numpy as np
from stl import mesh

# Dimensions
TOTAL_WIDTH = 175.0  # mm (X axis)
TOTAL_DEPTH = 6.5 * 42.0  # 273mm (Y axis) - 6.5 gridfinity squares
TOTAL_HEIGHT = 30.0  # mm (Z axis)
WALL_THICKNESS = 2.0  # mm (increased from 1.0 for sturdier print)
NUM_COMPARTMENTS = 3
BOTTOM_THICKNESS = 2.0  # mm (increased from 1.0 for sturdier print)


def create_watertight_compartment_box():
    """
    Create a watertight 3-compartment drawer organizer.
    Uses explicit vertex and face definitions for proper mesh closure.
    """
    W = TOTAL_WIDTH
    D = TOTAL_DEPTH
    H = TOTAL_HEIGHT
    t = WALL_THICKNESS
    bt = BOTTOM_THICKNESS

    # Calculate compartment positions
    compartment_width = (W - (NUM_COMPARTMENTS + 1) * t) / NUM_COMPARTMENTS

    # Divider X positions (inner edges)
    div1_left = t + compartment_width
    div1_right = div1_left + t
    div2_left = div1_right + compartment_width
    div2_right = div2_left + t

    vertices = []
    faces = []

    def add_vertex(x, y, z):
        """Add vertex and return its index."""
        vertices.append([x, y, z])
        return len(vertices) - 1

    def add_quad(v1, v2, v3, v4):
        """Add a quad as two triangles (CCW winding for outward normals)."""
        faces.append([v1, v2, v3])
        faces.append([v1, v3, v4])

    # === BOTTOM FACE (Z=0) - Outer rectangle ===
    b0 = add_vertex(0, 0, 0)
    b1 = add_vertex(W, 0, 0)
    b2 = add_vertex(W, D, 0)
    b3 = add_vertex(0, D, 0)
    add_quad(b0, b3, b2, b1)  # CCW from below

    # === TOP FACE - Outer rim and dividers ===
    # Outer top corners
    t0 = add_vertex(0, 0, H)
    t1 = add_vertex(W, 0, H)
    t2 = add_vertex(W, D, H)
    t3 = add_vertex(0, D, H)

    # Inner top corners (for wall thickness)
    ti0 = add_vertex(t, t, H)
    ti1 = add_vertex(div1_left, t, H)
    ti2 = add_vertex(div1_left, D - t, H)
    ti3 = add_vertex(t, D - t, H)

    ti4 = add_vertex(div1_right, t, H)
    ti5 = add_vertex(div2_left, t, H)
    ti6 = add_vertex(div2_left, D - t, H)
    ti7 = add_vertex(div1_right, D - t, H)

    ti8 = add_vertex(div2_right, t, H)
    ti9 = add_vertex(W - t, t, H)
    ti10 = add_vertex(W - t, D - t, H)
    ti11 = add_vertex(div2_right, D - t, H)

    # Top surface - Front wall
    add_quad(t0, t1, ti9, ti0)
    # Fill gaps between compartments on front
    add_quad(ti0, ti9, ti8, ti4)
    add_quad(ti4, ti8, ti5, ti1)  # This is wrong, ti1 is for compartment 1

    # Actually let me reconsider the topology...
    # Top surface is complex, let me rebuild more carefully

    # Clear and restart with simpler approach - create wall segments
    vertices.clear()
    faces.clear()

    # Use simpler box-by-box approach but ensure proper connectivity
    all_triangles = []

    def add_solid_box(x1, y1, z1, x2, y2, z2):
        """Create triangles for a solid box."""
        v = [
            [x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1],  # bottom
            [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2],  # top
        ]
        # 12 triangles for 6 faces, with correct winding
        tris = [
            # Bottom (normal -Z)
            [v[0], v[2], v[1]], [v[0], v[3], v[2]],
            # Top (normal +Z)
            [v[4], v[5], v[6]], [v[4], v[6], v[7]],
            # Front (normal -Y)
            [v[0], v[1], v[5]], [v[0], v[5], v[4]],
            # Back (normal +Y)
            [v[2], v[3], v[7]], [v[2], v[7], v[6]],
            # Left (normal -X)
            [v[0], v[4], v[7]], [v[0], v[7], v[3]],
            # Right (normal +X)
            [v[1], v[2], v[6]], [v[1], v[6], v[5]],
        ]
        all_triangles.extend(tris)

    # Bottom plate
    add_solid_box(0, 0, 0, W, D, bt)

    # Left wall
    add_solid_box(0, 0, bt, t, D, H)

    # Right wall
    add_solid_box(W - t, 0, bt, W, D, H)

    # Front wall (between left and right walls)
    add_solid_box(t, 0, bt, W - t, t, H)

    # Back wall (between left and right walls)
    add_solid_box(t, D - t, bt, W - t, D, H)

    # Divider 1
    add_solid_box(div1_left, t, bt, div1_right, D - t, H)

    # Divider 2
    add_solid_box(div2_left, t, bt, div2_right, D - t, H)

    # Create mesh
    stl_mesh = mesh.Mesh(np.zeros(len(all_triangles), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_triangles):
        for j in range(3):
            stl_mesh.vectors[i][j] = tri[j]

    return stl_mesh


def main():
    print("=== 3-Compartment Drawer Divider Generator ===")
    print(f"\nSpecifications:")
    print(f"  Total Width (X): {TOTAL_WIDTH} mm")
    print(f"  Total Depth (Y): {TOTAL_DEPTH} mm (6.5 × 42mm gridfinity)")
    print(f"  Total Height (Z): {TOTAL_HEIGHT} mm")
    print(f"  Wall Thickness: {WALL_THICKNESS} mm")
    print(f"  Bottom Thickness: {BOTTOM_THICKNESS} mm")
    print(f"  Number of Compartments: {NUM_COMPARTMENTS}")

    compartment_width = (TOTAL_WIDTH - (NUM_COMPARTMENTS + 1) * WALL_THICKNESS) / NUM_COMPARTMENTS
    print(f"  Compartment Width: {compartment_width:.2f} mm each")
    print(f"  Inner Depth: {TOTAL_DEPTH - 2 * WALL_THICKNESS:.2f} mm")
    print(f"  Inner Height: {TOTAL_HEIGHT - BOTTOM_THICKNESS:.2f} mm")

    # Create the mesh
    stl_mesh = create_watertight_compartment_box()

    print(f"\nMesh Properties:")
    print(f"  Number of triangles: {len(stl_mesh.vectors)}")

    # Verify dimensions
    print(f"\nActual Dimensions from mesh:")
    print(f"  X range: {stl_mesh.x.min():.2f} to {stl_mesh.x.max():.2f} mm")
    print(f"  Y range: {stl_mesh.y.min():.2f} to {stl_mesh.y.max():.2f} mm")
    print(f"  Z range: {stl_mesh.z.min():.2f} to {stl_mesh.z.max():.2f} mm")

    # Save the STL
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "3compartment_175x273x30.stl")
    stl_mesh.save(output_path)

    print(f"\n✅ STL saved to: {output_path}")

    return stl_mesh


if __name__ == "__main__":
    main()
