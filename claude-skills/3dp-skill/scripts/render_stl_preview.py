#!/usr/bin/env python3
"""
STL Preview Renderer
Generates top-down and isometric view images of STL files
No GUI or CAD software required - works headless

Dependencies:
    pip install numpy-stl matplotlib numpy

Usage:
    python render_stl_preview.py model.stl
    python render_stl_preview.py model.stl --output-dir ./previews
    python render_stl_preview.py model.stl --format png --dpi 300
"""

import numpy as np
from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import argparse
from pathlib import Path
import sys


def load_stl(filepath):
    """Load STL file and return mesh data."""
    return mesh.Mesh.from_file(filepath)


def get_mesh_bounds(stl_mesh):
    """Get bounding box of mesh."""
    min_x, max_x = stl_mesh.x.min(), stl_mesh.x.max()
    min_y, max_y = stl_mesh.y.min(), stl_mesh.y.max()
    min_z, max_z = stl_mesh.z.min(), stl_mesh.z.max()
    return {
        'min': (min_x, min_y, min_z),
        'max': (max_x, max_y, max_z),
        'center': ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2),
        'size': (max_x - min_x, max_y - min_y, max_z - min_z)
    }


def create_poly3d_collection(stl_mesh, color='#4A90D9', edge_color='#2C5F8A', alpha=0.9):
    """Create Poly3DCollection from STL mesh for matplotlib."""
    # Get all triangles
    vectors = stl_mesh.vectors

    # Create collection
    collection = Poly3DCollection(vectors, alpha=alpha)
    collection.set_facecolor(color)
    collection.set_edgecolor(edge_color)
    collection.set_linewidth(0.1)

    return collection


def setup_axes(ax, bounds, view_name):
    """Configure axes for consistent appearance."""
    # Set equal aspect ratio
    max_range = max(bounds['size']) / 2
    center = bounds['center']

    ax.set_xlim(center[0] - max_range, center[0] + max_range)
    ax.set_ylim(center[1] - max_range, center[1] + max_range)
    ax.set_zlim(center[2] - max_range, center[2] + max_range)

    # Style
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel('X (mm)', fontsize=8, labelpad=0)
    ax.set_ylabel('Y (mm)', fontsize=8, labelpad=0)
    ax.set_zlabel('Z (mm)', fontsize=8, labelpad=0)

    # Reduce tick label size
    ax.tick_params(labelsize=6)

    # Add title
    ax.set_title(view_name, fontsize=10, fontweight='bold', pad=5)

    # Light gray background
    ax.set_facecolor('#F5F5F5')
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False


def render_top_view(stl_mesh, bounds, output_path, dpi=150, format='png'):
    """Render top-down orthographic view (looking down Z axis)."""
    fig = plt.figure(figsize=(8, 8), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')

    # Add mesh
    collection = create_poly3d_collection(stl_mesh)
    ax.add_collection3d(collection)

    # Set view angle (top-down)
    ax.view_init(elev=90, azim=-90)

    setup_axes(ax, bounds, 'Top View (XY Plane)')

    # Hide Z axis for cleaner top view
    ax.set_zticks([])
    ax.set_zlabel('')

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, format=format, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    return output_path


def render_isometric_view(stl_mesh, bounds, output_path, dpi=150, format='png'):
    """Render isometric view (standard 3D perspective)."""
    fig = plt.figure(figsize=(8, 8), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')

    # Add mesh
    collection = create_poly3d_collection(stl_mesh, color='#5BA3E0', edge_color='#3D7AB8')
    ax.add_collection3d(collection)

    # Isometric view angle (elevation 35°, azimuth 45° is classic isometric)
    ax.view_init(elev=35, azim=45)

    setup_axes(ax, bounds, 'Isometric View')

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, format=format, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    return output_path


def render_front_view(stl_mesh, bounds, output_path, dpi=150, format='png'):
    """Render front view (looking down Y axis toward origin)."""
    fig = plt.figure(figsize=(8, 8), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')

    # Add mesh
    collection = create_poly3d_collection(stl_mesh, color='#6BC06B', edge_color='#4A9A4A')
    ax.add_collection3d(collection)

    # Front view (looking at XZ plane)
    ax.view_init(elev=0, azim=-90)

    setup_axes(ax, bounds, 'Front View (XZ Plane)')

    # Hide Y axis for cleaner front view
    ax.set_yticks([])
    ax.set_ylabel('')

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, format=format, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    return output_path


def render_side_view(stl_mesh, bounds, output_path, dpi=150, format='png'):
    """Render side view (looking down X axis)."""
    fig = plt.figure(figsize=(8, 8), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')

    # Add mesh
    collection = create_poly3d_collection(stl_mesh, color='#E0A35B', edge_color='#B87A3D')
    ax.add_collection3d(collection)

    # Side view (looking at YZ plane)
    ax.view_init(elev=0, azim=0)

    setup_axes(ax, bounds, 'Side View (YZ Plane)')

    # Hide X axis for cleaner side view
    ax.set_xticks([])
    ax.set_xlabel('')

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, format=format, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    return output_path


def render_combined_views(stl_mesh, bounds, output_path, dpi=150, format='png'):
    """Render all four views in a single 2x2 grid image."""
    fig = plt.figure(figsize=(12, 12), facecolor='white')

    views = [
        ('Top View', 90, -90, '#4A90D9', '#2C5F8A'),
        ('Isometric', 35, 45, '#5BA3E0', '#3D7AB8'),
        ('Front View', 0, -90, '#6BC06B', '#4A9A4A'),
        ('Side View', 0, 0, '#E0A35B', '#B87A3D'),
    ]

    for idx, (title, elev, azim, color, edge_color) in enumerate(views):
        ax = fig.add_subplot(2, 2, idx + 1, projection='3d')

        collection = create_poly3d_collection(stl_mesh, color=color, edge_color=edge_color)
        ax.add_collection3d(collection)

        ax.view_init(elev=elev, azim=azim)
        setup_axes(ax, bounds, title)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, format=format, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

    return output_path


def render_stl_previews(stl_path, output_dir=None, dpi=150, format='png', views='all'):
    """
    Generate preview images for an STL file.

    Args:
        stl_path: Path to STL file
        output_dir: Directory for output images (default: same as STL)
        dpi: Image resolution (default: 150)
        format: Image format - 'png' or 'jpeg' (default: 'png')
        views: Which views to generate - 'all', 'basic', or list of views

    Returns:
        Dictionary of generated file paths
    """
    stl_path = Path(stl_path)

    if not stl_path.exists():
        raise FileNotFoundError(f"STL file not found: {stl_path}")

    # Set output directory
    if output_dir is None:
        output_dir = stl_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Base name for output files
    base_name = stl_path.stem

    # Load mesh
    print(f"Loading: {stl_path}")
    stl_mesh = load_stl(str(stl_path))
    bounds = get_mesh_bounds(stl_mesh)

    print(f"  Dimensions: {bounds['size'][0]:.1f} x {bounds['size'][1]:.1f} x {bounds['size'][2]:.1f} mm")
    print(f"  Triangles: {len(stl_mesh.vectors)}")

    # Determine which views to render
    if views == 'basic':
        view_list = ['top', 'isometric']
    elif views == 'all':
        view_list = ['top', 'isometric', 'front', 'side', 'combined']
    elif isinstance(views, list):
        view_list = views
    else:
        view_list = ['top', 'isometric']

    # Render views
    results = {}

    if 'top' in view_list:
        out_path = output_dir / f"{base_name}_top.{format}"
        render_top_view(stl_mesh, bounds, str(out_path), dpi=dpi, format=format)
        results['top'] = out_path
        print(f"  ✓ Top view: {out_path.name}")

    if 'isometric' in view_list:
        out_path = output_dir / f"{base_name}_isometric.{format}"
        render_isometric_view(stl_mesh, bounds, str(out_path), dpi=dpi, format=format)
        results['isometric'] = out_path
        print(f"  ✓ Isometric view: {out_path.name}")

    if 'front' in view_list:
        out_path = output_dir / f"{base_name}_front.{format}"
        render_front_view(stl_mesh, bounds, str(out_path), dpi=dpi, format=format)
        results['front'] = out_path
        print(f"  ✓ Front view: {out_path.name}")

    if 'side' in view_list:
        out_path = output_dir / f"{base_name}_side.{format}"
        render_side_view(stl_mesh, bounds, str(out_path), dpi=dpi, format=format)
        results['side'] = out_path
        print(f"  ✓ Side view: {out_path.name}")

    if 'combined' in view_list:
        out_path = output_dir / f"{base_name}_combined.{format}"
        render_combined_views(stl_mesh, bounds, str(out_path), dpi=dpi, format=format)
        results['combined'] = out_path
        print(f"  ✓ Combined view: {out_path.name}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Generate preview images from STL files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python render_stl_preview.py model.stl
    python render_stl_preview.py model.stl --views basic
    python render_stl_preview.py model.stl --format jpeg --dpi 300
    python render_stl_preview.py model.stl --output-dir ./previews
        """
    )

    parser.add_argument('stl_file', help='Path to STL file')
    parser.add_argument('--output-dir', '-o', help='Output directory (default: same as STL)')
    parser.add_argument('--format', '-f', choices=['png', 'jpeg'], default='png',
                       help='Image format (default: png)')
    parser.add_argument('--dpi', '-d', type=int, default=150,
                       help='Image resolution (default: 150)')
    parser.add_argument('--views', '-v', default='basic',
                       choices=['basic', 'all'],
                       help='Which views to generate: basic (top+isometric) or all')

    args = parser.parse_args()

    try:
        results = render_stl_previews(
            args.stl_file,
            output_dir=args.output_dir,
            dpi=args.dpi,
            format=args.format,
            views=args.views
        )
        print(f"\n✓ Generated {len(results)} preview image(s)")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
