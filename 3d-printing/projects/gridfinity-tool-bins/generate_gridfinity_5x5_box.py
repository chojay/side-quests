#!/usr/bin/env python3
"""
Generate a simple 5x5 gridfinity container box STL file.

Specifications:
- 5x5 gridfinity units = 207.5mm x 207.5mm (41.5mm per unit with 0.5mm clearance)
- Height: 2 inches (~50.8mm)
- Wall thickness: 1.5mm
- No gridfinity base pattern - just a simple container
"""

import os
import numpy as np
from stl import mesh

# Gridfinity dimensions (as size reference only)
GRID_SIZE = 42.0        # mm per grid unit
UNITS_X = 5
UNITS_Y = 5

# Box dimensions
TOTAL_WIDTH = UNITS_X * GRID_SIZE     # 210mm
TOTAL_DEPTH = UNITS_Y * GRID_SIZE     # 210mm
TOTAL_HEIGHT = 2.0 * 25.4             # 2 inches = 50.8mm

# Wall/bottom thickness
WALL_THICKNESS = 1.5      # mm
BOTTOM_THICKNESS = 1.5    # mm


def create_hollow_box():
    """
    Create a simple hollow box (container) using solid box primitives.
    """
    W = TOTAL_WIDTH
    D = TOTAL_DEPTH
    H = TOTAL_HEIGHT
    t = WALL_THICKNESS
    bt = BOTTOM_THICKNESS

    all_triangles = []

    def add_solid_box(x1, y1, z1, x2, y2, z2):
        """Create triangles for a solid box with correct winding."""
        v = [
            [x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1],  # bottom
            [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2],  # top
        ]
        # 12 triangles for 6 faces
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

    # Bottom plate (full floor)
    add_solid_box(0, 0, 0, W, D, bt)

    # Left wall
    add_solid_box(0, 0, bt, t, D, H)

    # Right wall
    add_solid_box(W - t, 0, bt, W, D, H)

    # Front wall (between left and right walls)
    add_solid_box(t, 0, bt, W - t, t, H)

    # Back wall (between left and right walls)
    add_solid_box(t, D - t, bt, W - t, D, H)

    # Create mesh
    stl_mesh = mesh.Mesh(np.zeros(len(all_triangles), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_triangles):
        for j in range(3):
            stl_mesh.vectors[i][j] = tri[j]

    return stl_mesh


def main():
    print("=== Gridfinity 5x5 Container Box Generator ===")
    print(f"\nSpecifications:")
    print(f"  Grid Units: {UNITS_X} x {UNITS_Y}")
    print(f"  Grid Size: {GRID_SIZE} mm per unit")
    print(f"  Total Width (X): {TOTAL_WIDTH} mm")
    print(f"  Total Depth (Y): {TOTAL_DEPTH} mm")
    print(f"  Total Height (Z): {TOTAL_HEIGHT:.1f} mm (2 inches)")
    print(f"  Wall Thickness: {WALL_THICKNESS} mm")
    print(f"  Bottom Thickness: {BOTTOM_THICKNESS} mm")

    inner_width = TOTAL_WIDTH - 2 * WALL_THICKNESS
    inner_depth = TOTAL_DEPTH - 2 * WALL_THICKNESS
    inner_height = TOTAL_HEIGHT - BOTTOM_THICKNESS
    print(f"\nInner Dimensions:")
    print(f"  Inner Width: {inner_width:.1f} mm")
    print(f"  Inner Depth: {inner_depth:.1f} mm")
    print(f"  Inner Height: {inner_height:.1f} mm")

    # Create the mesh
    stl_mesh = create_hollow_box()

    print(f"\nMesh Properties:")
    print(f"  Number of triangles: {len(stl_mesh.vectors)}")

    # Verify dimensions
    print(f"\nActual Dimensions from mesh:")
    print(f"  X range: {stl_mesh.x.min():.2f} to {stl_mesh.x.max():.2f} mm")
    print(f"  Y range: {stl_mesh.y.min():.2f} to {stl_mesh.y.max():.2f} mm")
    print(f"  Z range: {stl_mesh.z.min():.2f} to {stl_mesh.z.max():.2f} mm")

    # Save the STL
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gridfinity_5x5_box_210x210x50.8mm.stl")
    stl_mesh.save(output_path)

    print(f"\n✅ STL saved to: {output_path}")

    return stl_mesh


if __name__ == "__main__":
    main()
