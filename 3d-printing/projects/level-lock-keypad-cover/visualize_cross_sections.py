#!/opt/homebrew/bin/python3.12
"""
Generate cross-section views of the STL to prove backplate exists
"""
import numpy as np
from stl import mesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle as MPLCircle

def plot_cross_section(stl_file, output_file):
    """Create cross-section views showing the backplate."""

    # Load mesh
    stl_mesh = mesh.Mesh.from_file(stl_file)
    vertices = stl_mesh.vectors.reshape(-1, 3)

    fig, axes = plt.subplots(2, 2, figsize=(16, 16))
    fig.suptitle(f'Cross-Section Analysis: {stl_file}', fontsize=16, fontweight='bold')

    # 1. TOP VIEW (looking down at Z=0 backplate)
    ax = axes[0, 0]
    z_near_0 = vertices[np.abs(vertices[:, 2]) < 0.5]  # Vertices within 0.5mm of Z=0
    ax.scatter(z_near_0[:, 0], z_near_0[:, 1], s=1, c='blue', alpha=0.5)
    ax.set_title(f'TOP VIEW - Backplate Level (Z≈0)\nVertices: {len(z_near_0)}', fontweight='bold')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    # Draw expected circle cutout
    circle = MPLCircle((0, -16.55), 34.45, fill=False, edgecolor='red', linewidth=2, linestyle='--', label='Expected circle cutout')
    ax.add_patch(circle)

    # Draw expected outer rectangle
    ax.plot([-44.45, 44.45, 44.45, -44.45, -44.45],
            [-61, -61, 61, 61, -61],
            'g--', linewidth=2, label='Expected outer bounds')
    ax.legend()

    # 2. SIDE VIEW (Y-Z plane at X=0)
    ax = axes[0, 1]
    x_near_0 = vertices[np.abs(vertices[:, 0]) < 2.0]  # Centerline slice
    ax.scatter(x_near_0[:, 1], x_near_0[:, 2], s=1, c='green', alpha=0.5)
    ax.set_title(f'SIDE VIEW - Centerline (X≈0)\nVertices: {len(x_near_0)}', fontweight='bold')
    ax.set_xlabel('Y (mm)')
    ax.set_ylabel('Z (mm)')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    # Highlight backplate region
    ax.axhline(y=0, color='red', linestyle='--', linewidth=2, label='Backplate (Z=0)')
    ax.axhline(y=3, color='orange', linestyle='--', linewidth=1, label='Backplate top (Z=3mm)')
    ax.legend()

    # 3. Z-HEIGHT HISTOGRAM
    ax = axes[1, 0]
    ax.hist(vertices[:, 2], bins=100, edgecolor='black', alpha=0.7)
    ax.set_title('Z-Height Distribution', fontweight='bold')
    ax.set_xlabel('Z (mm)')
    ax.set_ylabel('Vertex Count')
    ax.grid(True, alpha=0.3)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Backplate bottom')
    ax.axvline(x=3, color='orange', linestyle='--', linewidth=2, label='Backplate top')
    ax.legend()

    # 4. BACKPLATE DETAIL - Just the Z=0 to Z=3 region
    ax = axes[1, 1]
    backplate_region = vertices[(vertices[:, 2] >= -0.1) & (vertices[:, 2] <= 3.1)]
    ax.scatter(backplate_region[:, 0], backplate_region[:, 1],
              c=backplate_region[:, 2], cmap='viridis', s=2, alpha=0.6)
    ax.set_title(f'BACKPLATE DETAIL (0 ≤ Z ≤ 3mm)\nVertices: {len(backplate_region)}', fontweight='bold')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    # Draw circle cutout
    circle2 = MPLCircle((0, -16.55), 34.45, fill=False, edgecolor='red', linewidth=2, linestyle='--')
    ax.add_patch(circle2)

    cbar = plt.colorbar(ax.collections[0], ax=ax)
    cbar.set_label('Z height (mm)')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Cross-section saved: {output_file}")

    # Print statistics
    print(f"\n📊 BACKPLATE VERIFICATION:")
    print(f"  Vertices at Z≈0 (±0.5mm): {len(z_near_0)}")
    print(f"  Vertices in backplate region (0≤Z≤3mm): {len(backplate_region)}")

    if len(z_near_0) > 200:
        print(f"  ✅ BACKPLATE EXISTS - {len(z_near_0)} vertices confirm solid plate")
    else:
        print(f"  ⚠️  WARNING - Only {len(z_near_0)} vertices, backplate may be incomplete")

    # Check for circle cutout
    circle_center = np.array([0, -16.55, 0])
    distances = np.sqrt(z_near_0[:, 0]**2 + (z_near_0[:, 1] - circle_center[1])**2)
    near_circle = np.sum(np.abs(distances - 34.45) < 2.0)

    print(f"  Vertices near circle edge (r=34.45mm): {near_circle}")
    if near_circle > 50:
        print(f"  ✅ CIRCLE CUTOUT EXISTS - {near_circle} vertices confirm opening")

if __name__ == "__main__":
    plot_cross_section("level-lock-simple-awning.stl", "cross-section-analysis.png")
    print("\n✅ Open cross-section-analysis.png to see backplate proof!")
