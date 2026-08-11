#!/usr/bin/env python3
"""
Quick Start Template
Minimal example showing the full build123d workflow:
design -> validate -> export 3MF + STL -> interactive viewer

Usage:
    python quick_start.py
"""
from build123d import *

# === PARAMETERS ===
WIDTH = 50.0    # mm
DEPTH = 40.0    # mm
HEIGHT = 30.0   # mm
WALL = 2.0      # mm
CORNER_R = 3.0  # mm

# === GEOMETRY ===
with BuildPart() as part:
    # Outer box with rounded vertical edges
    Box(WIDTH, DEPTH, HEIGHT)
    fillet(part.edges().filter_by(Axis.Z), radius=CORNER_R)

    # Hollow out from top
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):
        Rectangle(WIDTH - 2 * WALL, DEPTH - 2 * WALL)
        fillet(vertices(), radius=max(CORNER_R - WALL, 0.5))
    extrude(amount=-(HEIGHT - WALL), mode=Mode.SUBTRACT)

# === EXPORT ===
name = "quick_start_box"

# STL (universal format + viewer)
part.part.export_stl(f"{name}.stl")
print(f"Exported: {name}.stl")

# 3MF (preferred for Bambu Studio)
try:
    from build123d import Mesher
    with Mesher() as m:
        m.add_shape(part.part)
        m.write(f"{name}.3mf")
    print(f"Exported: {name}.3mf (open in Bambu Studio)")
except Exception as e:
    print(f"3MF export unavailable: {e}")

# === VALIDATE ===
try:
    import trimesh
    mesh = trimesh.load(f"{name}.stl")
    print(f"Watertight: {mesh.is_watertight}")
    print(f"Volume: {mesh.volume:.2f} mm3")
    dims = mesh.bounds[1] - mesh.bounds[0]
    print(f"Dimensions: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
except ImportError:
    print("Install trimesh for validation: pip install trimesh")

# === PRINT SETTINGS ===
print("\nPrint settings:")
print("- Layer height: 0.2mm")
print("- Infill: 15-20%")
print("- Supports: Not needed")
