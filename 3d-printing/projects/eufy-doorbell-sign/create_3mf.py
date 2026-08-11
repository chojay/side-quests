#!/usr/bin/env python3
"""
Create a Bambu Studio-ready dual-colour 3MF for the Eufy E340 Doorbell Frame.

Pattern reused verbatim from an earlier (unpublished) sign project: a single
3dmodel.model with two inline meshes (base + text) wrapped in an assembly
object, plus Bambu-dialect Metadata/*.config so it loads with AMS slot binding
and no "old version of Bambu Studio" warning.

Filament 1 = Black  PETG  (frame ring + sign plaque)
Filament 2 = White  PETG  (raised text + outline)

PETG (not PLA) because the frame lives outdoors on a front door; PLA sags in
direct sun. Swap to ASA for the best UV resistance (see README).

Usage:  ../../.venv-3dp/bin/python create_3mf.py   (run eufy_e340_frame.py first)
"""
import zipfile, os, struct, json, sys
from datetime import datetime

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
# Optional CLI arg picks the variant prefix:
#   python create_3mf.py                       -> straight version
#   python create_3mf.py eufy_e340_frame_tilted -> tilted wedge version
PREFIX = sys.argv[1] if len(sys.argv) > 1 else "eufy_e340_frame"
BASE_STL = os.path.join(WORK_DIR, f"{PREFIX}_base.stl")
TEXT_STL = os.path.join(WORK_DIR, f"{PREFIX}_text.stl")
OUTPUT_3MF = os.path.join(WORK_DIR, f"{PREFIX}_Bambu.3mf")

# H2D build plate is 350 x 325 mm; place the part at plate center.
CENTER_X, CENTER_Y = 175.0, 162.5

FILAMENT_COLOURS = ["#1C1C1C", "#F5F5F5"]      # black body, white text
FILAMENT_TYPES = ["PETG", "PETG"]
FILAMENT_IDS = ["Bambu PETG HF", "Bambu PETG HF"]
BED_TYPE = "Textured PEI Plate"


def parse_stl(filepath):
    """Parse binary or ASCII STL -> (deduped vertices, triangles)."""
    vertices, triangles, vmap = [], [], {}
    with open(filepath, "rb") as f:
        header = f.read(80)
    is_ascii = header.decode("ascii", errors="ignore").strip().startswith("solid")
    if is_ascii:
        with open(filepath) as f:
            content = f.read()
        current = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("vertex"):
                p = line.split()
                key = (round(float(p[1]), 4), round(float(p[2]), 4), round(float(p[3]), 4))
                if key not in vmap:
                    vmap[key] = len(vertices); vertices.append(key)
                current.append(vmap[key])
            elif line.startswith("endfacet"):
                if len(current) == 3:
                    triangles.append(tuple(current))
                current = []
    else:
        with open(filepath, "rb") as f:
            f.read(80)
            n = struct.unpack("<I", f.read(4))[0]
            for _ in range(n):
                f.read(12)
                tri = []
                for _ in range(3):
                    x, y, z = struct.unpack("<fff", f.read(12))
                    key = (round(x, 4), round(y, 4), round(z, 4))
                    if key not in vmap:
                        vmap[key] = len(vertices); vertices.append(key)
                    tri.append(vmap[key])
                triangles.append(tuple(tri))
                f.read(2)
    return vertices, triangles


def mesh_xml(vertices, triangles, indent="   "):
    lines = [f"{indent}<mesh>", f"{indent} <vertices>"]
    for x, y, z in vertices:
        lines.append(f'{indent}  <vertex x="{x}" y="{y}" z="{z}"/>')
    lines.append(f"{indent} </vertices>")
    lines.append(f"{indent} <triangles>")
    for v1, v2, v3 in triangles:
        lines.append(f'{indent}  <triangle v1="{v1}" v2="{v2}" v3="{v3}"/>')
    lines.append(f"{indent} </triangles>")
    lines.append(f"{indent}</mesh>")
    return "\n".join(lines)


def create_model_xml(bv, bt, tv, tt):
    today = datetime.now().strftime("%Y-%m-%d")
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US"
    xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
    xmlns:BambuStudio="http://schemas.bambulab.com/package/2021"
    requiredextensions="p">
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="CreationDate">{today}</metadata>
 <metadata name="ModificationDate">{today}</metadata>
 <metadata name="Designer">Claude Code (adapted from MakerWorld 1139309)</metadata>
 <resources>
  <object id="1" p:UUID="e3400001-0001-0001-0001-000000000001" type="model">
{mesh_xml(bv, bt)}
  </object>
  <object id="2" p:UUID="e3400001-0001-0001-0001-000000000002" type="model">
{mesh_xml(tv, tt)}
  </object>
  <object id="3" p:UUID="e3400001-0001-0001-0001-000000000003" type="model">
   <components>
    <component objectid="1" p:UUID="e3400001-0001-0001-0001-c00000000001" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
    <component objectid="2" p:UUID="e3400001-0001-0001-0001-c00000000002" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
   </components>
  </object>
 </resources>
 <build p:UUID="e3400001-0001-0001-0001-b00000000001">
  <item objectid="3" p:UUID="e3400001-0001-0001-0001-b00000000002" transform="1 0 0 0 1 0 0 0 1 {CENTER_X} {CENTER_Y} 0" printable="1"/>
 </build>
</model>'''


def create_settings_config():
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="3">
    <metadata key="name" value="Eufy_E340_Doorbell_Frame"/>
    <metadata key="extruder" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="Frame + Plaque (Black PETG)"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="1"/>
      <metadata key="filament_colour" value="{FILAMENT_COLOURS[0]}"/>
    </part>
    <part id="2" subtype="normal_part">
      <metadata key="name" value="Text + Outline (White PETG)"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="2"/>
      <metadata key="filament_colour" value="{FILAMENT_COLOURS[1]}"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="Plate 1"/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Manual"/>
    <metadata key="filament_maps" value="1 2"/>
    <metadata key="filament_volume_maps" value="1 2"/>
    <model_instance>
      <metadata key="object_id" value="3"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="1"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="3" instance_id="0" transform="1 0 0 0 1 0 0 0 1 {CENTER_X} {CENTER_Y} 0" offset="0 0 0"/>
  </assemble>
</config>'''


def create_project_settings():
    settings = {
        "filament_colour": FILAMENT_COLOURS,
        "filament_type": FILAMENT_TYPES,
        "curr_bed_type": BED_TYPE,
        "default_filament_colour": FILAMENT_COLOURS,
        "filament_settings_id": FILAMENT_IDS,
        "filament_map": ["1", "2"],          # H2D: 1=left nozzle, 2=right nozzle
        "filament_map_mode": "Manual",        # lock routing -> no temp-clash warning
    }
    def encode(v):
        raw = json.dumps(v) if isinstance(v, list) else str(v)
        return raw.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    body = "\n".join(f'  <setting key="{k}" value="{encode(v)}"/>' for k, v in settings.items())
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
{body}
</config>'''


def create_content_types():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="config" ContentType="application/vnd.bambulab-package.config+xml"/>
</Types>'''


def create_rels():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>'''


def main():
    print("Eufy E340 Frame - Bambu dual-colour 3MF creator")
    print("=" * 50)
    for path, label in [(BASE_STL, "Base"), (TEXT_STL, "Text")]:
        if not os.path.exists(path):
            print(f"ERROR: {label} STL missing - run eufy_e340_frame.py first")
            return
    bv, bt = parse_stl(BASE_STL)
    tv, tt = parse_stl(TEXT_STL)
    print(f"  Base: {len(bv):,} verts / {len(bt):,} tris")
    print(f"  Text: {len(tv):,} verts / {len(tt):,} tris")

    with zipfile.ZipFile(OUTPUT_3MF, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", create_content_types())
        zf.writestr("_rels/.rels", create_rels())
        zf.writestr("3D/3dmodel.model", create_model_xml(bv, bt, tv, tt))
        zf.writestr("Metadata/model_settings.config", create_settings_config())
        zf.writestr("Metadata/project_settings.config", create_project_settings())

    print(f"\nCreated {os.path.basename(OUTPUT_3MF)} ({os.path.getsize(OUTPUT_3MF):,} bytes)")
    print(f"  Filament 1 -> Black PETG {FILAMENT_COLOURS[0]} (frame + plaque)")
    print(f"  Filament 2 -> White PETG {FILAMENT_COLOURS[1]} (text + outline)")


if __name__ == "__main__":
    main()
