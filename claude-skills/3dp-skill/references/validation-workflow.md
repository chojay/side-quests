# Mesh Validation Workflow

Guide for validating 3D models before printing.

## Quick Validation

```python
import trimesh

mesh = trimesh.load('model.stl')

# Essential checks
print(f"Watertight: {mesh.is_watertight}")   # MUST be True
print(f"Volume: {mesh.volume:.2f} mm³")       # Should be positive
print(f"Triangles: {len(mesh.faces)}")
print(f"Is valid: {mesh.is_volume}")
```

## Comprehensive Validation Script

```python
#!/usr/bin/env python3
"""
STL Validation Script
Checks mesh integrity before 3D printing
"""
import trimesh
import sys

def validate_stl(filepath):
    """Validate STL file for 3D printing."""
    print(f"Validating: {filepath}")
    print("=" * 50)

    try:
        mesh = trimesh.load(filepath)
    except Exception as e:
        print(f"✗ Failed to load: {e}")
        return False

    issues = []

    # 1. Watertight check (critical)
    if mesh.is_watertight:
        print(f"✓ Watertight: True")
    else:
        print(f"✗ Watertight: False")
        issues.append("Not watertight - has holes or gaps")

    # 2. Volume check
    if mesh.volume > 0:
        print(f"✓ Volume: {mesh.volume:.2f} mm³")
    else:
        print(f"✗ Volume: {mesh.volume:.2f} mm³ (inverted normals?)")
        issues.append("Negative volume - normals may be inverted")

    # 3. Bounds check
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    print(f"✓ Dimensions: {dims[0]:.2f} x {dims[1]:.2f} x {dims[2]:.2f} mm")

    # 4. Triangle count
    print(f"✓ Triangles: {len(mesh.faces)}")

    # 5. Degenerate faces
    degenerate = mesh.degenerate_faces
    if len(degenerate) == 0:
        print(f"✓ Degenerate faces: None")
    else:
        print(f"✗ Degenerate faces: {len(degenerate)}")
        issues.append(f"{len(degenerate)} degenerate triangles")

    # 6. Duplicate faces
    if hasattr(mesh, 'duplicate_faces'):
        duplicates = mesh.duplicate_faces
        if len(duplicates) == 0:
            print(f"✓ Duplicate faces: None")
        else:
            print(f"⚠ Duplicate faces: {len(duplicates)}")

    # 7. Body count
    bodies = mesh.split(only_watertight=False)
    print(f"✓ Bodies: {len(bodies)}")
    if len(bodies) > 1:
        issues.append(f"Multiple bodies ({len(bodies)}) - may need to be combined")

    print("=" * 50)

    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ All checks passed - ready for printing!")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_stl.py model.stl")
        sys.exit(1)

    filepath = sys.argv[1]
    success = validate_stl(filepath)
    sys.exit(0 if success else 1)
```

## Common Issues and Fixes

### Non-Watertight Mesh

**Symptom**: `is_watertight = False`

**Causes**:
- Gaps between faces
- Missing faces
- Coincident edges not properly joined

**Fixes**:
```python
# Auto-repair with trimesh
mesh.fill_holes()
mesh.fix_normals()

# Export repaired mesh
mesh.export('repaired.stl')
```

### Inverted Normals

**Symptom**: Negative volume, inside-out rendering

**Fixes**:
```python
# Fix normals
mesh.fix_normals()

# Or invert all normals
mesh.invert()
```

### Self-Intersections

**Detection**:
```python
# Check for self-intersection (can be slow)
if mesh.is_convex:
    print("Convex - no self-intersection possible")
else:
    # For complex meshes, visual inspection recommended
    pass
```

### Thin Walls

**Detection**:
```python
# Estimate wall thickness (approximate)
# For accurate measurement, use ray casting or voxelization
thickness_estimate = mesh.volume / mesh.area * 2
print(f"Estimated avg wall thickness: {thickness_estimate:.2f} mm")
```

### Multiple Bodies

**Symptom**: Parts not connected

**Fix**:
```python
# Split and recombine
bodies = mesh.split(only_watertight=False)
if len(bodies) > 1:
    combined = trimesh.util.concatenate(bodies)
    # Note: still may not be watertight if bodies don't touch
```

## Bambu H2D Build Volume Validation

```python
# Bambu H2D build volume limits (mm)
H2D_SINGLE_NOZZLE = (325, 320, 325)
H2D_DUAL_NOZZLE = (300, 320, 325)

def check_build_volume(mesh, dual_nozzle=False):
    """Validate model fits within Bambu H2D build volume."""
    limit = H2D_DUAL_NOZZLE if dual_nozzle else H2D_SINGLE_NOZZLE
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    axes = ['X', 'Y', 'Z']
    fits = True
    for i in range(3):
        if dims[i] > limit[i]:
            mode = "dual" if dual_nozzle else "single"
            print(f"WARNING: {axes[i]} = {dims[i]:.1f}mm exceeds H2D {mode} limit {limit[i]}mm")
            fits = False
    if fits:
        print(f"Model fits: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
    return fits
```

## 3MF Validation

trimesh can also load and validate 3MF files:

```python
import trimesh
mesh = trimesh.load("model.3mf")
print(f"Watertight: {mesh.is_watertight}")
print(f"Volume: {mesh.volume:.2f} mm3")
```

## Pre-Print Checklist

- [ ] **Watertight**: `mesh.is_watertight == True`
- [ ] **Positive volume**: `mesh.volume > 0`
- [ ] **No degenerate faces**: `len(mesh.degenerate_faces) == 0`
- [ ] **Single body**: `len(mesh.split()) == 1` (or intentionally multiple)
- [ ] **Fits build volume**: Within Bambu H2D limits (325x320x325mm single, 300x320x325mm dual)
- [ ] **Minimum wall thickness**: > 0.8mm for FDM

## Integration with Bambu Studio

Bambu Studio performs additional validation:
- Auto-repair on import
- Manifold check
- Overhang detection
- Print time estimation

**Best practice**: Even if trimesh validates, do a visual check in Bambu Studio before printing.

## Validation in build123d Workflow

```python
from build123d import *
import trimesh

# Generate part
with BuildPart() as part:
    Box(50, 40, 30)
    # ... more operations

# Export
part.part.export_stl("model.stl")

# Validate
mesh = trimesh.load("model.stl")
if mesh.is_watertight and mesh.volume > 0:
    print("✓ Ready for printing!")
else:
    print("✗ Validation failed - check geometry")
```

## Repair Tools

### trimesh (Python)
```python
mesh.fill_holes()
mesh.fix_normals()
mesh.remove_degenerate_faces()
mesh.remove_duplicate_faces()
```

### Meshmixer (GUI)
- Analysis → Inspector → Auto Repair All
- Best for complex repairs

### Microsoft 3D Builder (Windows)
- Auto-repairs on load
- Simple to use

### MeshLab (Cross-platform)
- Filters → Cleaning and Repairing
- Detailed control over repairs

## Print Settings Impact

| Issue | Print Impact |
|-------|--------------|
| Not watertight | Slicer may fail or produce artifacts |
| Inverted normals | Inside-out infill, wrong surfaces |
| Thin walls | Weak prints, failed layers |
| Self-intersection | Unpredictable slicing |
| Degenerate faces | Slicer warnings, artifacts |
