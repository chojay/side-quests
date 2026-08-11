#!/usr/bin/env python3
"""
Generate a 2-compartment drawer divider with DIAGONAL wall.

Specifications:
- Total width (X): 250mm
- Depth (Y): 220mm
- Height (Z): 50mm
- 2 compartments divided by diagonal wall (corner to corner)
- Wall thickness: 2mm (all walls including diagonal)
- Bottom thickness: 2mm

The diagonal runs from the front-left inner corner to the back-right inner corner,
creating two triangular compartments.
"""

import os
import numpy as np
from stl import mesh
import math

# Dimensions
TOTAL_WIDTH = 250.0   # mm (X axis)
TOTAL_DEPTH = 220.0   # mm (Y axis)
TOTAL_HEIGHT = 50.0   # mm (Z axis)
WALL_THICKNESS = 2.0  # mm
BOTTOM_THICKNESS = 2.0  # mm

def create_diagonal_compartment_box():
    """
    Create a 2-compartment drawer organizer with diagonal divider.
    """
    W = TOTAL_WIDTH
    D = TOTAL_DEPTH
    H = TOTAL_HEIGHT
    t = WALL_THICKNESS
    bt = BOTTOM_THICKNESS

    all_triangles = []

    def add_solid_box(x1, y1, z1, x2, y2, z2):
        """Create triangles for an axis-aligned solid box."""
        v = [
            [x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1],  # bottom
            [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2],  # top
        ]
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

    def add_prism(vertices_bottom, vertices_top):
        """
        Create triangles for a prism defined by bottom and top vertex lists.
        Both lists must have the same number of vertices in corresponding order.
        Vertices should be in CCW order when viewed from outside.
        """
        n = len(vertices_bottom)

        # Bottom face (reverse winding for outward normal)
        for i in range(1, n - 1):
            all_triangles.append([vertices_bottom[0], vertices_bottom[i + 1], vertices_bottom[i]])

        # Top face (CCW for outward normal)
        for i in range(1, n - 1):
            all_triangles.append([vertices_top[0], vertices_top[i], vertices_top[i + 1]])

        # Side faces
        for i in range(n):
            next_i = (i + 1) % n
            # Each side is a quad -> 2 triangles
            b1, b2 = vertices_bottom[i], vertices_bottom[next_i]
            t1, t2 = vertices_top[i], vertices_top[next_i]
            all_triangles.append([b1, b2, t2])
            all_triangles.append([b1, t2, t1])

    # === OUTER BOX ===
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

    # === DIAGONAL DIVIDER ===
    # The diagonal goes from inner front-left corner to inner back-right corner
    # Inner corners: (t, t) to (W-t, D-t)

    # Calculate diagonal direction
    start_x, start_y = t, t
    end_x, end_y = W - t, D - t

    dx = end_x - start_x  # 246mm
    dy = end_y - start_y  # 216mm
    diagonal_length = math.sqrt(dx * dx + dy * dy)

    # Unit vectors
    ux, uy = dx / diagonal_length, dy / diagonal_length  # along diagonal
    px, py = -uy, ux  # perpendicular (90° CCW rotation)

    # Half wall thickness for offset
    half_t = t / 2

    # Four corners of the diagonal wall (in XY plane)
    # The wall is centered on the diagonal line
    c1 = [start_x + px * half_t, start_y + py * half_t]  # start, left side
    c2 = [start_x - px * half_t, start_y - py * half_t]  # start, right side
    c3 = [end_x - px * half_t, end_y - py * half_t]      # end, right side
    c4 = [end_x + px * half_t, end_y + py * half_t]      # end, left side

    # Create 3D prism by extruding from Z=bt to Z=H
    z_bottom = bt
    z_top = H

    # Bottom vertices (CCW when viewed from below)
    vb = [
        [c1[0], c1[1], z_bottom],
        [c2[0], c2[1], z_bottom],
        [c3[0], c3[1], z_bottom],
        [c4[0], c4[1], z_bottom],
    ]

    # Top vertices (same order)
    vt = [
        [c1[0], c1[1], z_top],
        [c2[0], c2[1], z_top],
        [c3[0], c3[1], z_top],
        [c4[0], c4[1], z_top],
    ]

    add_prism(vb, vt)

    # Create mesh
    stl_mesh = mesh.Mesh(np.zeros(len(all_triangles), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_triangles):
        for j in range(3):
            stl_mesh.vectors[i][j] = tri[j]

    return stl_mesh, diagonal_length


def main():
    print("=== 2-Compartment Diagonal Drawer Divider Generator ===")
    print(f"\nSpecifications:")
    print(f"  Total Width (X): {TOTAL_WIDTH} mm")
    print(f"  Total Depth (Y): {TOTAL_DEPTH} mm")
    print(f"  Total Height (Z): {TOTAL_HEIGHT} mm")
    print(f"  Wall Thickness: {WALL_THICKNESS} mm")
    print(f"  Bottom Thickness: {BOTTOM_THICKNESS} mm")
    print(f"  Compartments: 2 (diagonal split)")

    # Create the mesh
    stl_mesh, diagonal_length = create_diagonal_compartment_box()

    # Calculate compartment info
    inner_width = TOTAL_WIDTH - 2 * WALL_THICKNESS
    inner_depth = TOTAL_DEPTH - 2 * WALL_THICKNESS
    inner_area = inner_width * inner_depth
    # Each triangular compartment has roughly half the area (minus the diagonal wall)
    wall_area = diagonal_length * WALL_THICKNESS
    compartment_area = (inner_area - wall_area) / 2

    print(f"\nCalculated Values:")
    print(f"  Inner Width: {inner_width:.2f} mm")
    print(f"  Inner Depth: {inner_depth:.2f} mm")
    print(f"  Diagonal Length: {diagonal_length:.2f} mm")
    print(f"  Each Compartment Area: ~{compartment_area:.0f} mm²")
    print(f"  Inner Height: {TOTAL_HEIGHT - BOTTOM_THICKNESS:.2f} mm")

    print(f"\nMesh Properties:")
    print(f"  Number of triangles: {len(stl_mesh.vectors)}")

    # Verify dimensions
    print(f"\nActual Dimensions from mesh:")
    print(f"  X range: {stl_mesh.x.min():.2f} to {stl_mesh.x.max():.2f} mm")
    print(f"  Y range: {stl_mesh.y.min():.2f} to {stl_mesh.y.max():.2f} mm")
    print(f"  Z range: {stl_mesh.z.min():.2f} to {stl_mesh.z.max():.2f} mm")

    # Save the STL
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "2compartment_diagonal_250x220x50_2mm-walls.stl")
    stl_mesh.save(output_path)

    print(f"\n✅ STL saved to: {output_path}")

    return stl_mesh


if __name__ == "__main__":
    main()
