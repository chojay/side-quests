---
name: 3dp-skill
description: >-
  This skill should be used when the user asks to "3D print something",
  "generate an STL", "create a 3MF file", "design a parametric part",
  "make a box/enclosure/organizer", "gridfinity", "vent cover",
  or needs 3D printable models. Generates watertight parametric CAD
  models using build123d, exports STL and 3MF files optimized for
  Bambu H2D printing, and produces interactive 3D HTML viewers.
allowed-tools: Read, Write, Bash, Glob, Grep
---

# 3D Printing - Parametric CAD with build123d

## Overview

Generate 3D printable parametric models using build123d (Python). Export as 3MF (preferred) or STL, validate watertight geometry with trimesh, and produce interactive 3D HTML viewers for inspection. Target printer: Bambu H2D.

## Core Design Principles

### 1. Parametric Design First
Define all dimensions as named constants at the top of the file. Derive dependent dimensions from primary ones (e.g., `INNER_WIDTH = WIDTH - 2 * WALL`). This makes designs adjustable without modifying geometry code.

### 2. Print-Oriented Modeling
Design for FDM from the start: minimize overhangs, orient largest flat surface as the base, ensure walls meet minimum thickness, and add fillets to stress concentration points.

### 3. Validate Before Export
Every model must pass trimesh watertight validation before delivery. Never skip this step: a non-watertight mesh produces unpredictable slicing artifacts.

### 4. 3MF as Default Format
Export 3MF for Bambu Studio (compressed, supports color/metadata/print settings). Export STL alongside for universal compatibility and HTML viewer embedding. See `references/3mf-export.md` for detailed patterns.

**Important for Bambu H2D + AMS**: A generic 3MF from `build123d.Mesher` alone loads with an "old version of Bambu Studio" warning and no preset binding. For one-click ready files, also write Bambu's `Metadata/model_settings.config` and `Metadata/project_settings.config` with filament colours, types, plate type, and (for H2D) `filament_map` to lock dual-nozzle assignment. The reference doc has the schema and a worked example.

### 5. Progressive Complexity
Start with the simplest geometry that satisfies requirements. Add features (fillets, chamfers, patterns) only after the base shape validates correctly.

## Core Workflow

```
1. Gather Requirements → 2. Generate build123d Code → 3. Validate Mesh
→ 4. Export 3MF + STL → 5. Generate Interactive Viewer → 6. Bambu Studio
```

### Step 1: Gather Requirements
- Dimensions in mm (always ask if not specified)
- Wall thickness (1.6-2mm functional, 2-3mm structural)
- Tolerances for fit (0.2-0.4mm press fit, 0.5mm+ clearance)
- Print orientation preferences
- Multi-part assembly needs
- Dual-color/material needs (Bambu H2D dual extruder)

### Step 2: Generate build123d Code

```python
#!/usr/bin/env python3
"""[Part Name] - Parametric design for [purpose]"""
from build123d import *

# === PARAMETERS (modify these) ===
WIDTH = 50.0    # mm
HEIGHT = 30.0   # mm
DEPTH = 20.0    # mm
WALL = 2.0      # mm

# === DERIVED ===
INNER_WIDTH = WIDTH - 2 * WALL

# === GEOMETRY ===
with BuildPart() as part:
    Box(WIDTH, HEIGHT, DEPTH)
    # ... operations ...

# === EXPORT ===
part.part.export_stl("output.stl")
```

For detailed patterns, read `references/build123d-patterns.md`.

### Step 3: Validate

```python
import trimesh
mesh = trimesh.load('output.stl')
assert mesh.is_watertight, "Mesh is not watertight!"
print(f"Volume: {mesh.volume:.2f} mm3")
```

### Step 4: Export 3MF + STL

```python
# STL (universal + viewer)
part.part.export_stl("output.stl")

# 3MF (preferred for Bambu Studio)
from build123d import Mesher
with Mesher() as m:
    m.add_shape(part.part)
    m.write("output.3mf")
```

### Step 5: Generate Interactive Viewer

Run `scripts/export_with_viewer.py` or call the `export_with_viewer()` function to generate a self-contained HTML file with an embedded 3D viewer (three.js). The viewer uses the `assets/viewer_template.html` template.

```python
# As module
from export_with_viewer import export_with_viewer
export_with_viewer(part.part, "my_part", dimensions="50x30x20mm")
```

### Step 6: Bambu Studio
Import the `.3mf` file into Bambu Studio for slicing. Colors auto-map to AMS filament slots for dual-extruder prints.

## build123d Quick Reference

| Task | Code |
|------|------|
| 3D context | `with BuildPart() as part:` |
| 2D sketch | `with BuildSketch():` |
| Box | `Box(w, h, d)` |
| Cylinder | `Cylinder(r, h)` |
| Sphere | `Sphere(r)` |
| Cone | `Cone(r_bottom, r_top, h)` |
| Extrude sketch | `extrude(amount=10)` |
| Cut hole | `extrude(amount=-10, mode=Mode.SUBTRACT)` |
| Top face | `part.faces().sort_by(Axis.Z)[-1]` |
| Bottom face | `part.faces().sort_by(Axis.Z)[0]` |
| Sketch on face | `with BuildSketch(face):` |
| Fillet edges | `fillet(part.edges(), radius=2)` |
| Chamfer edges | `chamfer(part.edges(), length=1)` |
| Union | `solid_a + solid_b` |
| Subtract | `solid_a - solid_b` |
| Intersect | `solid_a & solid_b` |
| Position | `with Locations((x, y)):` |
| Grid pattern | `with Locations(GridLocations(sx, sy, cx, cy)):` |
| Export STL | `part.part.export_stl("file.stl")` |
| Export 3MF | `Mesher().add_shape(part.part); .write("file.3mf")` |
| Validate | `trimesh.load('file.stl').is_watertight` |

## Bambu H2D Printer Specifications

| Spec | Value |
|------|-------|
| Build volume (single nozzle) | 325 x 320 x 325 mm |
| Build volume (dual nozzle) | 300 x 320 x 325 mm |
| Dual extruder | Multi-color / multi-material via 3MF |
| Heated chamber | 65C (ABS, ASA, PC, PA capable) |
| Hotend max | 350C (carbon/glass fiber materials) |
| Speed | Up to 1000 mm/s |
| Slicer | Bambu Studio (3MF preferred) |

Always validate model dimensions against build volume limits. For dual-nozzle prints, X dimension limit reduces to 300mm.

## Print Considerations

### Wall Thickness
| Use Case | Minimum | Recommended |
|----------|---------|-------------|
| Decorative | 0.8mm | 1.2mm |
| Functional | 1.2mm | 2.0mm |
| Structural | 2.0mm | 3.0mm+ |

### Tolerances
| Fit Type | Gap |
|----------|-----|
| Press fit | 0.1-0.2mm |
| Snug fit | 0.2-0.3mm |
| Sliding fit | 0.3-0.5mm |
| Loose fit | 0.5-1.0mm |

### Orientation
- Print with largest flat surface down
- Avoid overhangs >45 degrees without supports
- Holes perpendicular to bed need supports or teardrop shapes
- Thin walls parallel to Z-axis for maximum strength

## Common Mistakes to Avoid

- Forgetting `mode=Mode.SUBTRACT` for cuts (defaults to additive)
- Using `faces()[0]` instead of `faces().sort_by(Axis.Z)[-1]` (arbitrary vs. deterministic)
- Exceeding Bambu H2D build volume (325mm single / 300mm dual nozzle)
- Skipping watertight validation before export
- Exporting only STL when 3MF is preferred for Bambu
- Zero-thickness geometry from coincident faces
- Walls thinner than 0.8mm (unprintable on FDM)
- Boolean operations on non-intersecting bodies

## Tips for Excellence

- Use derived parameters: `INNER_WIDTH = WIDTH - 2 * WALL`
- Validate with trimesh before every delivery
- Generate interactive HTML viewer for every part
- Consider print orientation during design, not after
- Add fillets (2-3mm) to internal corners for strength
- Use `shell()` for uniform wall thickness on complex shapes
- Test multi-part fit with 0.3mm tolerance first, adjust if needed

## Installation

```bash
pip install build123d trimesh
```

No additional dependencies needed for HTML viewer (uses CDN-hosted three.js).

Optional: `pip install ocp-vscode` for VS Code visualization during development.

## Templates

Pre-built parametric templates in `templates/`:

- **`quick_start.py`** - Minimal hello-world showing full workflow
- **`parametric_box.py`** - Hollow box with optional lid
- **`parametric_enclosure.py`** - Electronics enclosure with mounting posts and ventilation
- **`split_assembly.py`** - Two-part assembly with dovetail joints
- **`gridfinity_base.py`** - Gridfinity-compatible storage baseplate
- **`vent_cover.py`** - Parametric vent/grille cover with louvers
- **`preview_helper.py`** - Shared matplotlib preview helper imported by the other templates (not a standalone part template); the equivalent preview workflow is covered in the "Optional: Static Image Previews (matplotlib)" section of `references/rendering-workflow.md`. Copy it alongside any template moved out of this directory.

## Supporting Resources

**References** (loaded as needed):
- `references/build123d-patterns.md` - Comprehensive code patterns, face/edge selection, loft/sweep, shell, text
- `references/3mf-export.md` - 3MF export guide, multi-color, dual extruder, Bambu Studio integration
- `references/validation-workflow.md` - Mesh validation, repair, pre-print checklist
- `references/rendering-workflow.md` - Optional matplotlib static previews

**Scripts** (executable):
- `scripts/export_with_viewer.py` - Export STL + validate + generate interactive HTML viewer
- `scripts/render_stl_preview.py` - Optional static PNG preview renderer

**Assets** (output templates):
- `assets/viewer_template.html` - Parameterized three.js interactive viewer template

---

*Generates parametric 3D models optimized for FDM printing on the Bambu H2D.*

## Adaptation Notes (added for the public copy)

- Build-volume limits, bed-type defaults, and the 3MF preset metadata in this skill target the Bambu Lab H2D specifically. If you print on a different machine, adjust those constants and the `references/3mf-export.md` preset names for your printer and slicer.
- All Python dependencies are pip-installable (build123d, trimesh); no private local setup is required.
- The generated HTML viewers (`assets/viewer_template.html`) load three.js from the jsdelivr CDN at view time, so opening a viewer requires an internet connection. The library is hotlinked, not bundled.
