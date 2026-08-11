#!/usr/bin/env python3
"""
Export 3D models with validation and interactive HTML viewer.

Usage as CLI:
    python export_with_viewer.py model.stl --name "My Part" --dims "50x40x30mm"

Usage as module:
    from export_with_viewer import export_with_viewer
    export_with_viewer(part, "my_part", dimensions="50x40x30mm")
"""
import argparse
import base64
import os
import sys

# Bambu H2D build volume limits (mm)
H2D_SINGLE_NOZZLE = (325, 320, 325)
H2D_DUAL_NOZZLE = (300, 320, 325)


def validate_stl(stl_path, dual_nozzle=False):
    """Validate STL mesh for 3D printing on Bambu H2D."""
    import trimesh

    mesh = trimesh.load(stl_path)
    issues = []

    # Watertight check
    if not mesh.is_watertight:
        issues.append("Not watertight - has holes or gaps")

    # Volume check
    if mesh.volume <= 0:
        issues.append("Negative/zero volume - normals may be inverted")

    # Degenerate faces
    degenerate = mesh.degenerate_faces
    if len(degenerate) > 0:
        issues.append(f"{len(degenerate)} degenerate triangles")

    # Build volume check
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    limit = H2D_DUAL_NOZZLE if dual_nozzle else H2D_SINGLE_NOZZLE
    axes = ['X', 'Y', 'Z']
    for i in range(3):
        if dims[i] > limit[i]:
            issues.append(
                f"{axes[i]} = {dims[i]:.1f}mm exceeds H2D limit {limit[i]}mm"
                f" ({'dual' if dual_nozzle else 'single'} nozzle)"
            )

    # Report
    print(f"  Watertight: {mesh.is_watertight}")
    print(f"  Volume: {mesh.volume:.2f} mm3")
    print(f"  Dimensions: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
    print(f"  Triangles: {len(mesh.faces)}")

    if issues:
        for issue in issues:
            print(f"  WARNING: {issue}")

    return {
        "watertight": mesh.is_watertight,
        "volume": mesh.volume,
        "dimensions": dims,
        "triangles": len(mesh.faces),
        "issues": issues,
        "valid": len(issues) == 0,
    }


def generate_viewer(stl_path, output_html, name="Model", dimensions="", info="",
                    color="0x4A90D9"):
    """Generate interactive HTML viewer with embedded STL data."""
    # Read template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "viewer_template.html"
    )
    with open(template_path, 'r') as f:
        template = f.read()

    # Encode STL as base64
    with open(stl_path, 'rb') as f:
        stl_base64 = base64.b64encode(f.read()).decode('utf-8')

    # Substitute placeholders
    html = template.replace('{{TITLE}}', name)
    html = html.replace('{{STL_BASE64}}', stl_base64)
    html = html.replace('{{DIMENSIONS}}', dimensions)
    html = html.replace('{{INFO}}', info)
    html = html.replace('{{COLOR}}', str(color))

    with open(output_html, 'w') as f:
        f.write(html)

    print(f"  Interactive viewer: {output_html}")


def export_with_viewer(build123d_part, name, dimensions="", info="",
                       output_dir=".", color="0x4A90D9", dual_nozzle=False,
                       export_3mf=True, export_stl=True):
    """
    Export build123d part with validation and interactive HTML viewer.

    Args:
        build123d_part: build123d Part object (e.g., part.part)
        name: Base name for output files
        dimensions: Dimension string for viewer info panel
        info: Additional info for viewer info panel
        output_dir: Output directory
        color: Hex color for 3D viewer (e.g., "0x4A90D9")
        dual_nozzle: Check against dual-nozzle build volume
        export_3mf: Export 3MF file (default: True, preferred for Bambu)
        export_stl: Export STL file (default: True)
    """
    stl_path = os.path.join(output_dir, f"{name}.stl")
    mf_path = os.path.join(output_dir, f"{name}.3mf")
    html_path = os.path.join(output_dir, f"{name}.html")

    # Export STL (always needed for viewer)
    build123d_part.export_stl(stl_path)
    print(f"  Exported: {stl_path}")

    # Export 3MF
    if export_3mf:
        try:
            from build123d import Mesher
            with Mesher() as exporter:
                exporter.add_shape(build123d_part)
                exporter.write(mf_path)
            print(f"  Exported: {mf_path} (preferred for Bambu Studio)")
        except Exception as e:
            print(f"  3MF export failed: {e} (using STL)")

    # Validate
    print("  Validating...")
    result = validate_stl(stl_path, dual_nozzle=dual_nozzle)

    if result["valid"]:
        print("  All checks passed - ready for printing!")
    else:
        print("  Validation issues found - review warnings above")

    # Generate viewer
    generate_viewer(stl_path, html_path, name=name, dimensions=dimensions,
                    info=info, color=color)

    # Clean up STL if only 3MF was requested
    if export_3mf and not export_stl and os.path.exists(mf_path):
        os.remove(stl_path)

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate STL and generate 3D viewer")
    parser.add_argument("stl_file", help="Path to STL file")
    parser.add_argument("--name", default=None, help="Model name for viewer")
    parser.add_argument("--dims", default="", help="Dimensions string")
    parser.add_argument("--info", default="", help="Additional info")
    parser.add_argument("--color", default="0x4A90D9", help="Viewer color (hex)")
    parser.add_argument("--dual-nozzle", action="store_true",
                        help="Check dual-nozzle build volume (300mm X)")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    args = parser.parse_args()

    name = args.name or os.path.splitext(os.path.basename(args.stl_file))[0]

    print(f"Processing: {args.stl_file}")
    result = validate_stl(args.stl_file, dual_nozzle=args.dual_nozzle)

    dims = result["dimensions"]
    dim_str = args.dims or f"{dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm"

    html_path = os.path.join(args.output_dir, f"{name}.html")
    generate_viewer(args.stl_file, html_path, name=name,
                    dimensions=dim_str, info=args.info, color=args.color)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
