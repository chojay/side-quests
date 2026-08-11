# 3MF Export Guide

3MF (3D Manufacturing Format) is the preferred export format for Bambu Lab printers. It is an ISO/IEC 25422:2025 standard that supersedes STL for modern 3D printing workflows.

> **Critical for Bambu Lab printers (2025-2026 research):** A *generic* 3MF from `build123d.Mesher`, `lib3mf`, Fusion 360, or trimesh **loads into Bambu Studio with an "old version of Bambu Studio" warning** and no AMS slot binding, no plate type, no preset suggestion. To produce a fully Bambu-ready 3MF you must also write the **`bbs_3mf` dialect** files: `Metadata/model_settings.config` and `Metadata/project_settings.config`. See [Bambu Lab 3MF Dialect](#bambu-lab-3mf-dialect-required-for-h2d-and-ams) below.

## Contents

- [Why 3MF Over STL](#why-3mf-over-stl)
- [build123d 3MF Export](#build123d-3mf-export)
- [Dual-Format Export Pattern](#dual-format-export-pattern)
- [Bambu Lab 3MF Dialect (required for H2D and AMS)](#bambu-lab-3mf-dialect-required-for-h2d-and-ams)
- [Python library landscape (2025-2026)](#python-library-landscape-2025-2026)
- [3MF Validation](#3mf-validation)
- [Bambu Studio Integration](#bambu-studio-integration)
- [Format Comparison](#format-comparison)

## Why 3MF Over STL

| Feature | STL | 3MF |
|---------|-----|-----|
| File size | Large (binary) / Very large (ASCII) | Compressed ZIP (50-90% smaller) |
| Color support | No | Yes (per-vertex, per-material) |
| Multi-material | No | Yes (multiple objects in one file) |
| Metadata | No | Yes (units, designer, print settings) |
| Units | Ambiguous | Explicit (XML specifies mm) |
| Print settings | No | Yes (embeddable) |
| ISO standard | No | Yes (ISO/IEC 25422:2025) |

**When to use STL instead**: Universal compatibility with legacy slicers, sharing with users who don't have 3MF-capable software, or when file format doesn't matter.

## build123d 3MF Export

### Single-Part Export

```python
from build123d import Mesher

with BuildPart() as part:
    Box(50, 40, 30)

# Export as 3MF
with Mesher() as exporter:
    exporter.add_shape(part.part)
    exporter.write("output.3mf")
print("Exported: output.3mf")
```

### Multi-Part Export (Single File)

Export multiple parts as separate objects in one 3MF file:

```python
from build123d import Mesher

with BuildPart() as body:
    Box(50, 40, 30)

with BuildPart() as lid:
    Box(50, 40, 5)

# Both parts in one file
with Mesher() as exporter:
    exporter.add_shape(body.part)
    exporter.add_shape(lid.part)
    exporter.write("box_assembly.3mf")
```

### Multi-Color Export (Bambu H2D Dual Extruder)

Assign colors to parts for automatic AMS slot mapping in Bambu Studio:

```python
from build123d import Mesher, Color

with BuildPart() as body:
    Box(50, 40, 30)

with BuildPart() as accent:
    # Logo or decorative element
    with BuildSketch(Plane.XY.offset(15)):
        Text("LOGO", font_size=8)
    extrude(amount=1)

# Color-coded for dual extruder
with Mesher() as exporter:
    exporter.add_shape(body.part, color=Color("white"))
    exporter.add_shape(accent.part, color=Color("red"))
    exporter.write("dual_color.3mf")
```

Bambu Studio automatically maps colors to AMS filament slots when importing multi-color 3MF files.

### Export with Metadata

```python
from build123d import Mesher

with Mesher() as exporter:
    exporter.add_shape(part.part)
    # Add metadata (accessible in Bambu Studio)
    exporter.add_meta_data("Application", "build123d")
    exporter.add_meta_data("Designer", "Claude Code")
    exporter.write("output.3mf")
```

### Export with Custom Tolerance

Control mesh resolution for curved surfaces:

```python
from build123d import Mesher

with Mesher() as exporter:
    exporter.add_shape(part.part)
    # Lower tolerance = more triangles = smoother curves
    # Default is fine for most prints
    exporter.write("output.3mf", tolerance=0.001, angular_tolerance=0.1)
```

## Dual-Format Export Pattern

Standard pattern to export both 3MF (preferred) and STL (fallback):

```python
def export_model(part, name):
    """Export part as 3MF and STL with validation."""
    import trimesh

    # Always export STL (universal compatibility + viewer)
    stl_path = f"{name}.stl"
    part.export_stl(stl_path)

    # Export 3MF (preferred for Bambu Studio)
    try:
        from build123d import Mesher
        mf_path = f"{name}.3mf"
        with Mesher() as exporter:
            exporter.add_shape(part)
            exporter.write(mf_path)
        print(f"Exported: {mf_path} (open in Bambu Studio)")
    except Exception as e:
        print(f"3MF export failed: {e}")

    print(f"Exported: {stl_path}")

    # Validate
    mesh = trimesh.load(stl_path)
    print(f"Watertight: {mesh.is_watertight}")
    print(f"Volume: {mesh.volume:.2f} mm3")
```

## Bambu Lab 3MF Dialect (required for H2D and AMS)

Bambu Studio and Orca Slicer use an extended 3MF dialect (`bbs_3mf`). The authoritative schema is in OrcaSlicer's source at [`src/libslic3r/Format/bbs_3mf.cpp`](https://github.com/SoftFever/OrcaSlicer/blob/main/src/libslic3r/Format/bbs_3mf.cpp). Bambu does not publish a public spec.

### Bambu-specific files inside the .3mf ZIP

```
Bambu .3mf contents:
  [Content_Types].xml
  _rels/.rels
  3D/3dmodel.model               (standard 3MF: vertices, triangles, objects)
  Metadata/model_settings.config (BAMBU: per-part extruder + filament binding)
  Metadata/project_settings.config (BAMBU: filament colours, plate type, presets)
  Metadata/slice_info.config     (optional: plate-level info, post-slice)
  Metadata/thumbnail.png         (optional: thumbnail)
```

### Key metadata keys

In `Metadata/project_settings.config`:

| Key | Value | Effect |
|-----|-------|--------|
| `filament_colour` | `["#FFFFFF", "#DC143C"]` (JSON array as XML attr) | Per-slot color swatch in parts panel |
| `filament_type` | `["PETG", "PETG"]` | Filament type hint |
| `filament_settings_id` | `["Bambu PETG HF", "Bambu PETG HF"]` | Profile to bind on load |
| `curr_bed_type` | `"Textured PEI Plate"` | Plate type preselected |
| `filament_map` | `["1", "2"]` | H2D nozzle assignment (1=left, 2=right) |
| `filament_map_mode` | `"Manual"` | Locks H2D assignment; prevents Bambu Studio from re-routing at slice time |
| `printer_settings_id` | `"Bambu Lab H2D 0.4 nozzle"` | (Optional) preset printer profile |

Valid `curr_bed_type` values: `"Textured PEI Plate"`, `"Cool Plate"`, `"Engineering Plate"`, `"High Temp Plate"`, `"Smooth PEI Plate"`.

In `Metadata/model_settings.config`:

```xml
<config>
  <object id="3">
    <metadata key="name" value="MyAssembly"/>
    <metadata key="extruder" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="Body (White PETG)"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="1"/>
      <metadata key="filament_colour" value="#FFFFFF"/>
    </part>
    <part id="2" subtype="normal_part">
      <metadata key="extruder" value="2"/>
      <metadata key="filament_colour" value="#DC143C"/>
    </part>
  </object>
  <plate>
    <metadata key="filament_map_mode" value="Manual"/>
    <metadata key="filament_maps" value="1 2"/>
    ...
  </plate>
</config>
```

### H2D dual-nozzle "high-temp/low-temp filaments together" warning

Triggers when filaments with incompatible `nozzle_temperature_range_low/high` share an extruder. Fix:

1. Set `filament_map_mode = "Manual"` (locks routing, prevents Auto from re-assigning)
2. Set `filament_map = ["1", "2"]` to assign filaments to separate nozzles
3. Ensure both filaments in `filament_type` are compatible with their assigned nozzle (e.g., PA-CF needs hardened steel = right nozzle on H2D)

### Recommended workflow

The most reliable way to author Bambu-dialect 3MFs:

1. **Generate a reference 3MF manually** in Bambu Studio with the exact AMS/plate/printer config you want.
2. **Unzip it**, copy `Metadata/model_settings.config` and `Metadata/project_settings.config` as templates.
3. **Use `build123d.Mesher` (or `lib3mf`) for the geometry portion**, writing only `3D/3dmodel.model`.
4. **Post-process the resulting ZIP** with `zipfile` to inject the templated Metadata config files.

### Worked example: build123d geometry + manual Bambu metadata

```python
import zipfile, json
from build123d import BuildPart, Box, Mesher, Color

# 1. Generate geometry with build123d
with BuildPart() as body:
    Box(50, 40, 30)

with Mesher() as exporter:
    exporter.add_shape(body.part, color=Color("white"))
    exporter.write("dual_color.3mf")

# 2. Inject Bambu-dialect Metadata
def encode_xml_attr(v):
    raw = json.dumps(v) if isinstance(v, list) else str(v)
    return raw.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")

project_cfg = f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <setting key="filament_colour" value="{encode_xml_attr(["#FFFFFF","#DC143C"])}"/>
  <setting key="filament_type" value="{encode_xml_attr(["PETG","PETG"])}"/>
  <setting key="filament_settings_id" value="{encode_xml_attr(["Bambu PETG HF","Bambu PETG HF"])}"/>
  <setting key="curr_bed_type" value="Textured PEI Plate"/>
  <setting key="filament_map" value="{encode_xml_attr(["1","2"])}"/>
  <setting key="filament_map_mode" value="Manual"/>
</config>'''

with zipfile.ZipFile("dual_color.3mf", "a") as zf:
    zf.writestr("Metadata/project_settings.config", project_cfg)
```

### Pitfalls

- **JSON values in XML attributes**: `filament_colour='["#FFFFFF"]'` must escape `"` to `&quot;`. Some parsers tolerate raw `"` but strict ones reject it.
- **Transform matrices**: lib3mf and build123d use column-major affine. The build123d exporter has had transform bugs ([gumyr/build123d#432](https://github.com/gumyr/build123d/issues/432)).
- **trimesh 3MF export** flattens multi-mesh: Bambu Studio sees separate parts but not as a multi-color assembly. Avoid for color work.
- **AMS slot binding is runtime** (via RFID `tag_uid`/`ams_id`/`slot_id`). You can pre-assign filament *indices* in the 3MF, but physical AMS slot assignment happens on the printer.
- **`filament_settings_id` must match the user's local profile library** to bind successfully. If they don't have "Bambu PETG HF" loaded, the binding silently no-ops and they see the default profile.
- **CadQuery `.center(x, y)` accumulates** when chained in a loop. For repeated operations (holes, pockets, embosses), prefer `pushPoints([...])` with absolute coordinates to avoid cumulative offset bugs.

## Python library landscape (2025-2026)

| Library | Status for Bambu 3MF |
|---------|---------------------|
| `build123d.Mesher` | Solid geometry export. **No Bambu metadata** in output, produces generic 3MF that loads with "old version" warning. Combine with manual `Metadata/*.config` injection. |
| `lib3mf` (official, v2.5.0) | Read/write C++/Python binding. Handles Production Extension, Beam Lattice, Materials. **No Bambu config awareness**, same caveat. |
| `trimesh` | 3MF export is flat (no proper object hierarchy). **Avoid for multi-color.** |
| `bambustudio-python` | Does not exist as a mature library. Closest: `gcode-to-bambu-preset`, `3mf_bambu2prusa`, `3mfUtility`. |

## 3MF Validation

trimesh can load and validate 3MF files:

```python
import trimesh

mesh = trimesh.load("output.3mf")
print(f"Watertight: {mesh.is_watertight}")
print(f"Volume: {mesh.volume:.2f} mm3")
```

For the Bambu metadata, validate the XML directly:

```python
import xml.etree.ElementTree as ET, zipfile

with zipfile.ZipFile("output.3mf") as z:
    for name in ["3D/3dmodel.model", "Metadata/model_settings.config", "Metadata/project_settings.config"]:
        try:
            with z.open(name) as f:
                ET.parse(f)
            print(f"OK: {name}")
        except (KeyError, ET.ParseError) as e:
            print(f"FAIL: {name}: {e}")
```

## Bambu Studio Integration

### Import Workflow
1. Export `.3mf` from build123d
2. Open Bambu Studio -> File -> Import 3MF
3. Colors auto-map to AMS slots
4. Adjust print settings (already embedded if added)
5. Slice and send to printer

### Multi-Plate Workflow
Bambu Studio supports multiple plates in a single 3MF project. Export each part separately, then arrange in Bambu Studio for batch printing.

### Supported Formats
Bambu Studio accepts: 3MF, STL, STEP, OBJ, AMF. Prefer 3MF for the richest metadata support.

## Format Comparison

| Use Case | Recommended Format |
|----------|-------------------|
| Bambu H2D printing | 3MF |
| Multi-color/material | 3MF (with colors) |
| Sharing with others | STL (universal) |
| Editing in other CAD | STEP |
| Interactive HTML viewer | STL (base64 embedded) |
| Maximum compatibility | STL |
