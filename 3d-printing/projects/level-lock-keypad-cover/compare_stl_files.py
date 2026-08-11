#!/opt/homebrew/bin/python3.12
"""
Detailed STL Comparison using numpy-stl
Compare build123d vs OpenSCAD outputs to diagnose geometry issues
"""
import numpy as np
from stl import mesh
import trimesh

def analyze_stl(filename):
    """Detailed analysis of an STL file."""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {filename}")
    print('='*60)

    # Load with numpy-stl
    stl_mesh = mesh.Mesh.from_file(filename)

    # Basic stats
    print(f"\n📊 BASIC STATISTICS:")
    print(f"  Triangles: {len(stl_mesh.vectors)}")
    print(f"  Vertices: {len(stl_mesh.vectors) * 3}")

    # Bounding box
    vertices = stl_mesh.vectors.reshape(-1, 3)
    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)
    dimensions = max_coords - min_coords

    print(f"\n📐 BOUNDING BOX:")
    print(f"  Min: [{min_coords[0]:.2f}, {min_coords[1]:.2f}, {min_coords[2]:.2f}]")
    print(f"  Max: [{max_coords[0]:.2f}, {max_coords[1]:.2f}, {max_coords[2]:.2f}]")
    print(f"  Dimensions: {dimensions[0]:.2f} × {dimensions[1]:.2f} × {dimensions[2]:.2f} mm")

    # Volume and mass
    volume, cog, inertia = stl_mesh.get_mass_properties()
    print(f"\n📦 VOLUME & MASS:")
    print(f"  Volume: {volume:.2f} mm³")
    print(f"  PLA weight (1.24 g/cm³): {(volume/1000)*1.24:.2f}g")
    print(f"  Center of Gravity: [{cog[0]:.2f}, {cog[1]:.2f}, {cog[2]:.2f}]")

    # Load with trimesh for additional validation
    tm = trimesh.load(filename)
    print(f"\n✅ MESH VALIDATION (trimesh):")
    print(f"  Watertight: {tm.is_watertight}")
    print(f"  Volume: {tm.volume:.2f} mm³")
    print(f"  Surface area: {tm.area:.2f} mm²")

    # Check for specific features
    print(f"\n🔍 GEOMETRY ANALYSIS:")

    # Check Z range to verify backplate
    z_min = vertices[:, 2].min()
    z_max = vertices[:, 2].max()
    print(f"  Z range: {z_min:.2f} to {z_max:.2f} mm (depth: {z_max - z_min:.2f} mm)")

    # Check if backplate exists (vertices near Z=0)
    backplate_vertices = vertices[np.abs(vertices[:, 2]) < 0.1]
    print(f"  Vertices near Z=0 (backplate): {len(backplate_vertices)}")

    # Check if circle cutout exists (look for vertices near circle circumference)
    # Circle at y=-16.55, radius=34.45
    circle_y = -16.55
    circle_r = 34.45

    near_z0 = vertices[np.abs(vertices[:, 2]) < 0.1]
    if len(near_z0) > 0:
        dist_from_circle_center = np.sqrt(near_z0[:, 0]**2 + (near_z0[:, 1] - circle_y)**2)
        near_circle_edge = np.sum(np.abs(dist_from_circle_center - circle_r) < 2.0)
        print(f"  Vertices near circle edge (r={circle_r:.1f}mm): {near_circle_edge}")

    # Normal vector analysis
    normals = stl_mesh.normals
    print(f"\n🧭 NORMAL VECTORS:")
    print(f"  Total normals: {len(normals)}")

    # Count normals pointing in each direction
    z_up = np.sum(normals[:, 2] > 0.9)
    z_down = np.sum(normals[:, 2] < -0.9)
    print(f"  Normals pointing +Z (top faces): {z_up}")
    print(f"  Normals pointing -Z (bottom faces): {z_down}")

    if z_down == 0:
        print(f"  ⚠️  WARNING: No normals pointing -Z! Backplate may be missing!")

    return {
        'filename': filename,
        'triangles': len(stl_mesh.vectors),
        'volume': volume,
        'watertight': tm.is_watertight,
        'dimensions': dimensions,
        'backplate_verts': len(backplate_vertices),
        'z_down_normals': z_down
    }

def compare_meshes(file1, file2):
    """Compare two STL meshes."""
    print(f"\n{'='*60}")
    print("COMPARISON")
    print('='*60)

    result1 = analyze_stl(file1)
    result2 = analyze_stl(file2)

    print(f"\n{'='*60}")
    print("SUMMARY COMPARISON")
    print('='*60)

    print(f"\n{'Metric':<30} {'build123d':<20} {'OpenSCAD':<20}")
    print('-'*70)
    print(f"{'Triangles':<30} {result1['triangles']:<20} {result2['triangles']:<20}")
    print(f"{'Volume (mm³)':<30} {result1['volume']:<20.2f} {result2['volume']:<20.2f}")
    print(f"{'Watertight':<30} {str(result1['watertight']):<20} {str(result2['watertight']):<20}")
    print(f"{'Backplate vertices':<30} {result1['backplate_verts']:<20} {result2['backplate_verts']:<20}")
    print(f"{'Bottom-facing normals':<30} {result1['z_down_normals']:<20} {result2['z_down_normals']:<20}")

    # Highlight differences
    print(f"\n🔍 KEY DIFFERENCES:")

    vol_diff = abs(result1['volume'] - result2['volume'])
    vol_pct = (vol_diff / result2['volume']) * 100
    print(f"  Volume difference: {vol_diff:.2f} mm³ ({vol_pct:.1f}%)")

    if result1['backplate_verts'] < result2['backplate_verts'] / 2:
        print(f"  ⚠️  build123d has significantly fewer backplate vertices!")

    if result1['z_down_normals'] < result2['z_down_normals'] / 2:
        print(f"  ⚠️  build123d missing bottom-facing normals (backplate issue)!")

if __name__ == "__main__":
    compare_meshes(
        "level-lock-simple-awning.stl",
        "level-lock-awning-openscad.stl"
    )
