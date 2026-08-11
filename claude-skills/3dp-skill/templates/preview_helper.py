#!/usr/bin/env python3
"""
Preview Image Helper (Optional - Static PNG Previews)
Shared utility for generating STL preview images using matplotlib.
Requires: pip install numpy-stl matplotlib numpy

Primary visualization: Use scripts/export_with_viewer.py for interactive HTML viewers.
This helper is for static PNG/JPEG images useful in documentation or README files.
"""

import sys
from pathlib import Path


def generate_previews(stl_files, views=('isometric', 'top')):
    """
    Generate preview images for STL files.

    Args:
        stl_files: Single filename or list of filenames
        views: Tuple of views to generate ('isometric', 'top', 'front', 'side')

    Returns:
        List of generated image paths
    """
    if isinstance(stl_files, str):
        stl_files = [stl_files]

    generated = []

    try:
        import numpy as np
        from stl import mesh
        import matplotlib
        matplotlib.use('Agg')  # Headless rendering
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except ImportError as e:
        print(f"  Note: Preview generation requires: pip install numpy-stl matplotlib")
        return generated

    view_angles = {
        'isometric': (35, 45),
        'top': (90, -90),
        'front': (0, -90),
        'side': (0, 0),
    }

    view_colors = {
        'isometric': ('#4A90D9', '#2C5F8A'),
        'top': ('#5BA3E0', '#3D7AB8'),
        'front': ('#6BC06B', '#4A9A4A'),
        'side': ('#E0A35B', '#B87A3D'),
    }

    for stl_file in stl_files:
        stl_path = Path(stl_file)
        if not stl_path.exists():
            print(f"  ✗ File not found: {stl_file}")
            continue

        # Load mesh
        try:
            m = mesh.Mesh.from_file(str(stl_path))
        except Exception as e:
            print(f"  ✗ Failed to load {stl_file}: {e}")
            continue

        # Calculate bounds
        pts = m.vectors.reshape(-1, 3)
        center = (pts.max(axis=0) + pts.min(axis=0)) / 2
        scale = (pts.max(axis=0) - pts.min(axis=0)).max() / 2

        # Generate each view
        base_name = stl_path.stem

        for view_name in views:
            if view_name not in view_angles:
                continue

            elev, azim = view_angles[view_name]
            face_color, edge_color = view_colors.get(view_name, ('#4A90D9', '#2C5F8A'))

            fig = plt.figure(figsize=(8, 8), facecolor='white')
            ax = fig.add_subplot(111, projection='3d')

            # Add mesh
            collection = Poly3DCollection(m.vectors, alpha=0.9)
            collection.set_facecolor(face_color)
            collection.set_edgecolor(edge_color)
            collection.set_linewidth(0.1)
            ax.add_collection3d(collection)

            # Set view
            ax.view_init(elev=elev, azim=azim)

            # Set limits for equal aspect ratio
            ax.set_xlim(center[0] - scale, center[0] + scale)
            ax.set_ylim(center[1] - scale, center[1] + scale)
            ax.set_zlim(center[2] - scale, center[2] + scale)
            ax.set_box_aspect([1, 1, 1])

            # Labels
            ax.set_xlabel('X (mm)', fontsize=8)
            ax.set_ylabel('Y (mm)', fontsize=8)
            ax.set_zlabel('Z (mm)', fontsize=8)
            ax.tick_params(labelsize=6)
            ax.set_title(f'{view_name.title()} View', fontsize=10, fontweight='bold')

            # Save
            output_path = stl_path.parent / f"{base_name}_{view_name}.png"
            plt.savefig(str(output_path), dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()

            generated.append(str(output_path))
            print(f"  ✓ Preview: {output_path.name}")

    return generated


def generate_combined_preview(stl_file, output_path=None):
    """
    Generate a 2x2 grid with all four views.

    Args:
        stl_file: Path to STL file
        output_path: Output image path (default: <name>_combined.png)

    Returns:
        Output path if successful, None otherwise
    """
    try:
        import numpy as np
        from stl import mesh
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except ImportError:
        print("  Note: Combined preview requires: pip install numpy-stl matplotlib")
        return None

    stl_path = Path(stl_file)
    if not stl_path.exists():
        print(f"  ✗ File not found: {stl_file}")
        return None

    # Load mesh
    m = mesh.Mesh.from_file(str(stl_path))
    pts = m.vectors.reshape(-1, 3)
    center = (pts.max(axis=0) + pts.min(axis=0)) / 2
    scale = (pts.max(axis=0) - pts.min(axis=0)).max() / 2

    # Views config
    views = [
        ('Top', 90, -90, '#4A90D9', '#2C5F8A'),
        ('Isometric', 35, 45, '#5BA3E0', '#3D7AB8'),
        ('Front', 0, -90, '#6BC06B', '#4A9A4A'),
        ('Side', 0, 0, '#E0A35B', '#B87A3D'),
    ]

    fig = plt.figure(figsize=(12, 12), facecolor='white')

    for idx, (title, elev, azim, face_color, edge_color) in enumerate(views):
        ax = fig.add_subplot(2, 2, idx + 1, projection='3d')

        collection = Poly3DCollection(m.vectors, alpha=0.9)
        collection.set_facecolor(face_color)
        collection.set_edgecolor(edge_color)
        collection.set_linewidth(0.1)
        ax.add_collection3d(collection)

        ax.view_init(elev=elev, azim=azim)

        ax.set_xlim(center[0] - scale, center[0] + scale)
        ax.set_ylim(center[1] - scale, center[1] + scale)
        ax.set_zlim(center[2] - scale, center[2] + scale)
        ax.set_box_aspect([1, 1, 1])

        ax.set_xlabel('X', fontsize=7)
        ax.set_ylabel('Y', fontsize=7)
        ax.set_zlabel('Z', fontsize=7)
        ax.tick_params(labelsize=5)
        ax.set_title(f'{title} View', fontsize=9, fontweight='bold')

    plt.tight_layout()

    if output_path is None:
        output_path = stl_path.parent / f"{stl_path.stem}_combined.png"

    plt.savefig(str(output_path), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  ✓ Combined preview: {Path(output_path).name}")
    return str(output_path)


if __name__ == "__main__":
    # CLI usage
    if len(sys.argv) < 2:
        print("Usage: python preview_helper.py <stl_file> [--all]")
        print("  --all: Generate all views including combined")
        sys.exit(1)

    stl_file = sys.argv[1]
    all_views = '--all' in sys.argv

    if all_views:
        generate_previews(stl_file, views=('isometric', 'top', 'front', 'side'))
        generate_combined_preview(stl_file)
    else:
        generate_previews(stl_file, views=('isometric', 'top'))
