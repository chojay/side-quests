#!/usr/bin/env python3
"""
Render STL files to SVG for documentation.
Creates isometric-style views of both original and new compartment designs.
"""

import numpy as np
from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def render_stl_to_svg(stl_path, output_svg_path, title="STL Model"):
    """Render an STL file to SVG using matplotlib."""
    # Load the mesh
    stl_mesh = mesh.Mesh.from_file(stl_path)

    # Create figure
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Create collection of polygons
    polygons = []
    for vector in stl_mesh.vectors:
        polygons.append(vector)

    # Add polygons to plot
    collection = Poly3DCollection(polygons, alpha=0.8, linewidths=0.5, edgecolors='darkblue')
    collection.set_facecolor('lightsteelblue')
    ax.add_collection3d(collection)

    # Set axis limits based on mesh bounds
    scale = stl_mesh.points.flatten()
    ax.auto_scale_xyz(scale, scale, scale)

    # Set proper limits
    x_range = [stl_mesh.x.min(), stl_mesh.x.max()]
    y_range = [stl_mesh.y.min(), stl_mesh.y.max()]
    z_range = [stl_mesh.z.min(), stl_mesh.z.max()]

    # Pad ranges
    x_pad = (x_range[1] - x_range[0]) * 0.1
    y_pad = (y_range[1] - y_range[0]) * 0.1
    z_pad = (z_range[1] - z_range[0]) * 0.2

    ax.set_xlim(x_range[0] - x_pad, x_range[1] + x_pad)
    ax.set_ylim(y_range[0] - y_pad, y_range[1] + y_pad)
    ax.set_zlim(z_range[0], z_range[1] + z_pad)

    # Set viewing angle (isometric-ish)
    ax.view_init(elev=25, azim=-60)

    # Labels
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_title(title)

    # Add dimension annotations
    width = stl_mesh.x.max() - stl_mesh.x.min()
    depth = stl_mesh.y.max() - stl_mesh.y.min()
    height = stl_mesh.z.max() - stl_mesh.z.min()

    dim_text = f"Dimensions: {width:.1f} × {depth:.1f} × {height:.1f} mm"
    ax.text2D(0.02, 0.02, dim_text, transform=ax.transAxes, fontsize=10,
              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Save as SVG
    plt.tight_layout()
    plt.savefig(output_svg_path, format='svg', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Saved: {output_svg_path}")
    return True


def create_comparison_svg(original_path, new_path, output_svg_path):
    """Create a side-by-side comparison SVG."""
    # Load meshes
    original = mesh.Mesh.from_file(original_path)
    new = mesh.Mesh.from_file(new_path)

    fig = plt.figure(figsize=(16, 8))

    # Original
    ax1 = fig.add_subplot(121, projection='3d')
    polygons1 = [v for v in original.vectors]
    collection1 = Poly3DCollection(polygons1, alpha=0.8, linewidths=0.5, edgecolors='darkgreen')
    collection1.set_facecolor('lightgreen')
    ax1.add_collection3d(collection1)

    # Set limits for original
    scale1 = original.points.flatten()
    ax1.auto_scale_xyz(scale1, scale1, scale1)
    ax1.view_init(elev=25, azim=-60)
    ax1.set_xlabel('X (mm)')
    ax1.set_ylabel('Y (mm)')
    ax1.set_zlabel('Z (mm)')
    ax1.set_title('Original: 2+compartment.stl')

    width1 = original.x.max() - original.x.min()
    depth1 = original.y.max() - original.y.min()
    height1 = original.z.max() - original.z.min()
    ax1.text2D(0.02, 0.02, f"{width1:.1f} × {depth1:.1f} × {height1:.1f} mm",
               transform=ax1.transAxes, fontsize=9,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # New
    ax2 = fig.add_subplot(122, projection='3d')
    polygons2 = [v for v in new.vectors]
    collection2 = Poly3DCollection(polygons2, alpha=0.8, linewidths=0.5, edgecolors='darkblue')
    collection2.set_facecolor('lightsteelblue')
    ax2.add_collection3d(collection2)

    # Set limits for new - need to handle different scale
    ax2.set_xlim(new.x.min() - 10, new.x.max() + 10)
    ax2.set_ylim(new.y.min() - 10, new.y.max() + 10)
    ax2.set_zlim(new.z.min(), new.z.max() + 10)
    ax2.view_init(elev=25, azim=-60)
    ax2.set_xlabel('X (mm)')
    ax2.set_ylabel('Y (mm)')
    ax2.set_zlabel('Z (mm)')
    ax2.set_title('New: 3compartment_175x273x30.stl')

    width2 = new.x.max() - new.x.min()
    depth2 = new.y.max() - new.y.min()
    height2 = new.z.max() - new.z.min()
    ax2.text2D(0.02, 0.02, f"{width2:.1f} × {depth2:.1f} × {height2:.1f} mm",
               transform=ax2.transAxes, fontsize=9,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_svg_path, format='svg', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Saved comparison: {output_svg_path}")
    return True


def main():
    original_stl = os.path.join(BASE_PATH, "2+compartment.stl")
    new_stl = os.path.join(BASE_PATH, "3compartment_175x273x30.stl")

    # Render individual SVGs
    render_stl_to_svg(
        original_stl,
        os.path.join(BASE_PATH, "original_2compartment.svg"),
        "Original: 2-Compartment Drawer Divider"
    )

    render_stl_to_svg(
        new_stl,
        os.path.join(BASE_PATH, "new_3compartment.svg"),
        "New: 3-Compartment Drawer Divider (Gridfinity 6.5)"
    )

    # Create comparison SVG
    create_comparison_svg(
        original_stl,
        new_stl,
        os.path.join(BASE_PATH, "comparison.svg")
    )

    print("\n✅ All SVG renders complete!")


if __name__ == "__main__":
    main()
