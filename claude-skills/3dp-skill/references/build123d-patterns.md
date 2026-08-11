# build123d Code Patterns Reference

Comprehensive patterns for LLM-assisted 3D model generation using build123d.

## Contents

- [File Structure Template](#file-structure-template)
- [Context Manager Hierarchy](#context-manager-hierarchy)
- [Face Selection Patterns](#face-selection-patterns)
- [Edge Selection Patterns](#edge-selection-patterns)
- [Primitive Shapes](#primitive-shapes)
- [Extrusion Patterns](#extrusion-patterns)
- [Boolean Operations](#boolean-operations)
- [Positioning and Locations](#positioning-and-locations)
- [Transformations](#transformations)
- [Fillets and Chamfers](#fillets-and-chamfers)
- [Holes and Counterbores](#holes-and-counterbores)
- [Loft and Sweep](#loft-and-sweep)
- [Shell (Hollow Out)](#shell-hollow-out)
- [Text](#text)
- [Multi-Part Assembly Pattern](#multi-part-assembly-pattern)
- [Rounded Rectangle Pattern](#rounded-rectangle-pattern)
- [Slot Pattern](#slot-pattern)
- [Rib/Support Pattern](#ribsupport-pattern)
- [Export Functions](#export-functions)
- [Error Handling](#error-handling)
- [Common Pitfalls](#common-pitfalls)

## File Structure Template

```python
#!/usr/bin/env python3
"""
[Part Name] Generator
[Brief description]
Designed for [printer/use case]
"""
from build123d import *
import math  # if needed

# === DESIGN PARAMETERS ===
# All dimensions in mm
WIDTH = 50.0
HEIGHT = 30.0
DEPTH = 20.0
WALL_THICKNESS = 2.0
CORNER_RADIUS = 3.0

# Derived parameters
INNER_WIDTH = WIDTH - 2 * WALL_THICKNESS
INNER_HEIGHT = HEIGHT - 2 * WALL_THICKNESS

# === MAIN GEOMETRY ===
with BuildPart() as part:
    # ... geometry code ...
    pass

# === EXPORT ===
part.part.export_stl("output.stl")
print(f"✓ Exported: output.stl")
print(f"  Dimensions: {WIDTH} x {HEIGHT} x {DEPTH} mm")
```

## Context Manager Hierarchy

```python
with BuildPart() as part:           # 3D solid context
    with BuildSketch() as sketch:   # 2D sketch on XY plane
        with BuildLine() as line:   # 1D line construction
            pass
```

### Sketch on Specific Plane
```python
# Default planes
with BuildSketch(Plane.XY):   # Default, horizontal
with BuildSketch(Plane.XZ):   # Vertical front
with BuildSketch(Plane.YZ):   # Vertical side

# Offset plane
with BuildSketch(Plane.XY.offset(10)):  # 10mm above XY
```

### Sketch on Part Face
```python
with BuildPart() as part:
    Box(50, 40, 30)

    # Top face
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):
        Circle(10)
    extrude(amount=-15, mode=Mode.SUBTRACT)
```

## Face Selection Patterns

```python
# By axis direction
faces().sort_by(Axis.Z)[-1]    # Top (highest Z)
faces().sort_by(Axis.Z)[0]     # Bottom (lowest Z)
faces().sort_by(Axis.Y)[-1]    # Front (highest Y)
faces().sort_by(Axis.Y)[0]     # Back (lowest Y)
faces().sort_by(Axis.X)[-1]    # Right (highest X)
faces().sort_by(Axis.X)[0]     # Left (lowest X)

# By area
faces().sort_by(SortBy.AREA)[-1]   # Largest face
faces().sort_by(SortBy.AREA)[0]    # Smallest face

# Filter by normal direction
faces().filter_by(Axis.Z)          # Horizontal faces
faces().filter_by(Axis.X)          # Faces perpendicular to X

# Filter by plane
faces().filter_by(Plane.XY)        # Faces parallel to XY
```

## Edge Selection Patterns

```python
# All edges
edges()

# Vertical edges only
edges().filter_by(Axis.Z)

# Edges on specific face
part.faces().sort_by(Axis.Z)[-1].edges()

# By length
edges().sort_by(SortBy.LENGTH)[-1]    # Longest edge
edges().sort_by(SortBy.LENGTH)[0]     # Shortest edge

# Fillet only top edges
fillet(part.faces().sort_by(Axis.Z)[-1].edges(), radius=2)
```

## Primitive Shapes

### Solid Primitives
```python
Box(width, height, depth)
Cylinder(radius, height)
Cone(bottom_radius, top_radius, height)
Sphere(radius)
Torus(major_radius, minor_radius)
Wedge(dx, dy, dz, ltx=None)
```

### Sketch Primitives
```python
# Inside BuildSketch context
Rectangle(width, height)
Circle(radius)
Ellipse(x_radius, y_radius)
RegularPolygon(radius, side_count)
Polygon(points)  # [(x1,y1), (x2,y2), ...]
SlotOverall(width, height)
SlotCenterToCenter(center_separation, height)
```

## Extrusion Patterns

### Basic Extrude
```python
with BuildPart() as part:
    with BuildSketch():
        Rectangle(30, 20)
    extrude(amount=10)  # Extrude up
```

### Subtractive Extrude (Holes/Pockets)
```python
with BuildPart() as part:
    Box(50, 50, 20)
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):
        Circle(5)
    extrude(amount=-15, mode=Mode.SUBTRACT)
```

### Both Directions
```python
extrude(amount=10, both=True)  # 5mm up and down
```

### To Face/Until
```python
extrude(until=Until.NEXT)      # Until next solid
extrude(until=Until.LAST)      # Through all
```

## Boolean Operations

```python
# Union
combined = part_a + part_b

# Subtraction
result = main_part - hole_part

# Intersection
common = part_a & part_b

# Chained operations
result = main + feature_a + feature_b - cutout
```

## Positioning and Locations

### Locations Context
```python
with BuildSketch():
    with Locations((0, 0), (20, 0), (40, 0)):
        Circle(5)  # Creates 3 circles
```

### Grid Pattern
```python
with Locations(GridLocations(x_spacing=20, y_spacing=20, x_count=3, y_count=3)):
    Circle(3)  # 3x3 grid of circles
```

### Polar Pattern
```python
with PolarLocations(radius=30, count=6):
    Circle(5)  # 6 circles around center
```

## Transformations

```python
# Translate
part.translate((x, y, z))

# Rotate
part.rotate(Axis.Z, angle_degrees)

# Mirror
part.mirror(Plane.XZ)

# Scale
part.scale(factor)
```

## Fillets and Chamfers

```python
# Fillet all edges
fillet(part.edges(), radius=2)

# Fillet specific edges
fillet(part.faces().sort_by(Axis.Z)[-1].edges(), radius=3)

# Chamfer
chamfer(part.edges(), length=1)

# Asymmetric chamfer
chamfer(edge, length=1, length2=0.5)
```

## Holes and Counterbores

### Simple Hole
```python
with BuildSketch(top_face):
    Circle(2.5)  # M5 clearance
extrude(amount=-depth, mode=Mode.SUBTRACT)
```

### Counterbore
```python
with BuildPart() as part:
    Box(50, 50, 10)

    # Counterbore pattern
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):
        Circle(4.5)  # Head clearance
    extrude(amount=-3, mode=Mode.SUBTRACT)

    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]):
        Circle(2.5)  # Shaft clearance
    extrude(amount=-7, mode=Mode.SUBTRACT)
```

### Countersink
```python
# Use cone subtraction
with BuildPart() as part:
    Box(50, 50, 10)
    # Countersink
    cone = Cone(5, 2.5, 2.5).translate((0, 0, 7.5))
    part = part.part - cone
```

## Loft and Sweep

### Loft Between Sketches
```python
with BuildPart() as part:
    with BuildSketch(Plane.XY):
        Rectangle(30, 30)
    with BuildSketch(Plane.XY.offset(20)):
        Circle(10)
    loft()
```

### Sweep Along Path
```python
with BuildPart() as part:
    with BuildLine():
        l = Line((0, 0), (50, 0))
        Arc(l @ 1, (50, 50), (0, 50))
    with BuildSketch(Plane.YZ):
        Circle(5)
    sweep()
```

## Shell (Hollow Out)

```python
with BuildPart() as part:
    Box(50, 40, 30)
    shell(part.faces().sort_by(Axis.Z)[-1], amount=-2)
```

## Text

```python
with BuildSketch(top_face):
    Text("Hello", font_size=10, align=(Align.CENTER, Align.CENTER))
extrude(amount=1)  # Raised text
# or
extrude(amount=-0.5, mode=Mode.SUBTRACT)  # Engraved text
```

## Multi-Part Assembly Pattern

```python
# Parameters
TOL = 0.3  # Clearance tolerance

# Part A (male feature)
with BuildPart() as part_a:
    Box(50, 40, 10)
    # Add tongue
    with BuildSketch(part_a.faces().sort_by(Axis.Y)[-1]):
        Rectangle(20, 5)
    extrude(amount=5)

# Part B (female feature)
with BuildPart() as part_b:
    Box(50, 40, 10)
    # Subtract groove
    with BuildSketch(part_b.faces().sort_by(Axis.Y)[0]):
        Rectangle(20 + TOL, 5 + TOL)
    extrude(amount=5 + TOL, mode=Mode.SUBTRACT)

# Export
part_a.part.export_stl("part_a.stl")
part_b.part.export_stl("part_b.stl")
```

## Rounded Rectangle Pattern

```python
with BuildSketch():
    Rectangle(50, 30)
    fillet(vertices(), radius=5)
```

## Slot Pattern

```python
with BuildSketch():
    SlotOverall(30, 10)  # 30mm long, 10mm wide slot
```

## Rib/Support Pattern

```python
# Add vertical rib for support
with BuildPart() as part:
    Box(50, 50, 5)  # Base plate

    # Add rib
    with BuildSketch(Plane.XZ):
        Polygon([(0, 5), (0, 20), (10, 5)])  # Triangle rib
    extrude(amount=2)  # 2mm thick rib
```

## Export Functions

### STL Export
```python
part.part.export_stl("model.stl")
part.part.export_stl("model.stl", tolerance=0.001)  # Higher detail
part.part.export_stl("model.stl", tolerance=0.0005, angular_tolerance=0.05)
```

### 3MF Export (Preferred for Bambu H2D)

3MF is the preferred format for Bambu Lab printers. Supports color, metadata, and print settings.

```python
from build123d import Mesher

# Single part
with Mesher() as exporter:
    exporter.add_shape(part.part)
    exporter.write("model.3mf")

# Multi-part assembly in one file
with Mesher() as exporter:
    exporter.add_shape(body.part)
    exporter.add_shape(lid.part)
    exporter.write("assembly.3mf")

# Multi-color for dual extruder (Bambu H2D)
from build123d import Color
with Mesher() as exporter:
    exporter.add_shape(body.part, color=Color("white"))
    exporter.add_shape(accent.part, color=Color("red"))
    exporter.write("dual_color.3mf")

# With metadata
with Mesher() as exporter:
    exporter.add_shape(part.part)
    exporter.add_meta_data("Application", "build123d")
    exporter.write("model.3mf")
```

For detailed 3MF patterns, see `references/3mf-export.md`.

### STEP Export (Parametric Preservation)
```python
part.part.export_step("model.step")
```

## Error Handling

```python
from build123d import *

try:
    with BuildPart() as part:
        Box(50, 40, 30)
        # ... operations

    if part.part.is_valid():
        part.part.export_stl("output.stl")
        print("✓ Export successful")
    else:
        print("✗ Invalid geometry")
except Exception as e:
    print(f"✗ Error: {e}")
```

## Common Pitfalls

### 1. Forgetting mode=Mode.SUBTRACT
```python
# Wrong - adds instead of subtracts
extrude(amount=-10)

# Correct - explicitly subtract
extrude(amount=-10, mode=Mode.SUBTRACT)
```

### 2. Wrong face selection
```python
# May not get expected face
faces()[0]  # Order is arbitrary

# Better - use explicit sorting
faces().sort_by(Axis.Z)[-1]  # Consistently gets top face
```

### 3. Zero-thickness geometry
```python
# Avoid creating faces with no thickness
# Always ensure extrude amounts create solid volume
```

### 4. Boolean operation failures
```python
# Ensure parts actually intersect/touch for booleans to work
# Check that geometries are valid before combining
```

### 5. Multi-start helical threads produce non-manifold edges

**Symptom**: `mesh.is_watertight == False`. Slicer reports "N non-manifold edges" on import (e.g., Bambu Studio: "9 non-manifold edges. To repair the model, please use a third-party tool"). The defect lives at the trim-cylinder boundary where the swept helical threads are cut to body height. Bambu's Auto-Repair often cannot fix it.

**Cause**: When you sweep one thread profile along a `Helix` and then union N phase-shifted copies to make an N-start thread, OCCT's boolean union leaves micro-gaps where adjacent swept solids meet the trim cylinder. Worsens with higher start counts (3+) and taller rings (more helix revolutions stacked).

**Failing pattern (union-based)**:
```python
base_helix = Helix(pitch=lead, height=h + 2*lead, radius=major_r, center=(0, 0, -lead))
one_thread = sweep(sections=profile.sketch, path=base_helix)
threads = one_thread
for k in range(1, num_starts):
    copy = one_thread.located(Location((0, 0, k*lead/num_starts), (0,0,1), k*360/num_starts))
    threads = threads + copy   # <-- micro-gaps at trim boundary
trim = Cylinder(outer_r + 5, h)
threads_trimmed = threads & trim
result = body.part + threads_trimmed
```

**Fix (subtract-based)**: Start with a solid cylinder bored to **minor** radius, then **subtract** N rectangular helical grooves. Subtraction is far more numerically stable than multi-start union.
```python
with BuildPart() as nut:
    Cylinder(outer_r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(minor_r, h + 2*EPS,                         # tight bore at MINOR (peaks)
             align=(Align.CENTER, Align.CENTER, Align.MIN),
             mode=Mode.SUBTRACT)

valley_half = 0.65 * pitch / 2  # axial half-width of the rectangular groove
groove_pts = [
    (minor_r - EPS, -valley_half), (minor_r - EPS,  valley_half),
    (major_r + EPS,  valley_half), (major_r + EPS, -valley_half),
    (minor_r - EPS, -valley_half),
]
with BuildSketch(Plane.XZ) as groove_profile:
    with BuildLine(): Polyline(*groove_pts)
    make_face()

final = nut.part
for k in range(num_starts):
    z_off = k * (lead / num_starts) - lead
    helix = Helix(pitch=lead, height=h + 2*lead, radius=minor_r, center=(0, 0, z_off))
    helix = helix.located(Location((0, 0, 0), (0, 0, 1), k * 360.0 / num_starts))
    final = final - sweep(sections=groove_profile.sketch, path=helix)
```

**Trade-off**: groove cross-section is rectangular, not buttress / triangle / square. The thread peak is now a flat-topped plateau between rectangular valleys. For test-fit rings and coarse plastic threads this is usually fine and often *more* forgiving (generous flat valleys give the male crest extra axial play). If you need an asymmetric thread flank (load-bearing buttress), prefer the union path with 1-2 starts only.

**Rule of thumb**: use union for 1-2 starts, subtract for 3+ starts or any time you see non-manifold output. Always verify `mesh.is_watertight == True` before declaring success - slicer Auto-Repair masks the issue rather than fixing it.
