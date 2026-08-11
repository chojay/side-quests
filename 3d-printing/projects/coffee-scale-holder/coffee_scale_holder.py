#!/usr/bin/env python3
"""
Coffee Scale Holders (v4): one under-beam garage dock per scale.
  - Maestri House K112 digital coffee scale (105 x 105 x 22 mm)
  - BOOKOO Themis Mini espresso scale (80 x 80 x 15 mm)

Mounting: the flat TOP PLANE is the adhesive surface, glued to the
underside of the horizontal beam (VHB tape). No screws, no nail holes.

Loading: the front (center) face is open. The scale slides in flat,
top/display side facing UP, and rests on the floor. Silicone feet on
the floor provide friction retention.

Access while docked:
  - Top plane is set back from the front edge, exposing the scale's
    front strip for a pinch grip (finger on top, thumb under the
    elliptical floor scoop).
  - USB cable windows through BOTH side walls. Official manuals do not
    document which edge carries the USB-C port; both scales are square,
    so rotate the scale until the port lines up with a window.

Design principles inherited from glove_dispenser.py:
  - parametric pocket with named clearances
  - elliptical scoop for one-handed grab (relocated to the floor edge)
  - gravity/friction retention, no latches
  - support-free print orientation

Print orientation: AS EXPORTED, standing on the back wall. Every major
plane prints vertical; the only bridges are the window tops and the
plate's front edge (under 30 mm). The adhesive top face prints as a
vertical exterior surface, flat and smooth.
"""
import cadquery as cq
import os

# === SCALES (mm) ===
# window_w / window_shift: USB window width and its offset toward the open
# mouth. K112 manual render shows the Type-C port mid-right-edge and the
# OFF/ON slide switch ~28 mm from the front-right corner, so its windows
# are wider and biased frontward to expose both. Themis Mini port edge is
# undocumented (likely rear edge per owner observation): load it rotated
# 90 degrees when charging.
SCALES = [
    # (stem, name, footprint, thickness, scoop_w, scoop_d,
    #  window_w, window_shift, setback)
    ("maestri_k112_holder", "Maestri House K112",
     105.0, 22.0, 60.0, 45.0, 50.0, 5.0, 25.0),
    ("themis_mini_holder", "BOOKOO Themis Mini",
     80.0, 15.0, 50.0, 32.0, 35.0, 0.0, 20.0),
]

# === FIT CLEARANCES ===
CLEAR_XY = 2.0     # slack on footprint, both axes (same as glove dispenser)
CLEAR_Z = 4.0      # headroom above the scale inside the pocket

# === SHELL ===
WALL = 2.5         # side / back wall thickness
FLOOR_T = 3.0      # floor thickness
PLATE_T = 3.0      # top plane thickness (adhesive face)
FILLET_R = 3.0     # vertical corner rounding
RIM_CHAMFER = 0.8  # comfort chamfer on exposed edges

script_dir = os.path.dirname(os.path.abspath(__file__))


def cbox(x0, y0, z0, x1, y1, z1):
    """Axis-aligned box from two corners."""
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=(False, False, False))
            .translate((x0, y0, z0)))


def build_holder(footprint, scale_t, scoop_w, scoop_d, window_w,
                 window_shift, setback):
    """Under-beam garage: floor + side/back walls + top plane, open front.

    Origin: left-back-bottom corner. Back wall at y 0..WALL, open front
    at y = total_d. Scale slides in display-up.
    """
    in_xy = footprint + CLEAR_XY
    in_h = scale_t + CLEAR_Z
    total_w = in_xy + 2 * WALL          # X
    total_d = in_xy + 2 * WALL          # Y (front wall removed below)
    total_h = FLOOR_T + in_h + PLATE_T  # Z
    z0, z1 = FLOOR_T, FLOOR_T + in_h    # interior height band
    mid_y = WALL + in_xy / 2

    # solid block, rounded corners
    result = cbox(0, 0, 0, total_w, total_d, total_h)
    try:
        result = result.edges("|Z").fillet(FILLET_R)
    except Exception:
        pass

    # pocket, extended through the front face (the removed center face)
    result = result - cbox(WALL, WALL, z0, total_w - WALL, total_d + 5, z1)

    # set the top plane back from the front edge so the scale's front
    # strip stays visible and pinch-able from above
    result = result - cbox(-5, total_d - setback, z1,
                           total_w + 5, total_d + 5, total_h + 5)

    # elliptical finger scoop in the floor's front edge (grab from below)
    el = cq.Workplane("XY").ellipse(scoop_w / 2, scoop_d).extrude(FLOOR_T + 2)
    bb = el.val().BoundingBox()
    el = el.translate((total_w / 2 - (bb.xmin + bb.xmax) / 2,
                       total_d - (bb.ymin + bb.ymax) / 2,
                       -1 - bb.zmin))
    result = result - el

    # USB cable windows through BOTH side walls, centered front-to-back,
    # spanning the full interior height
    wc = mid_y + window_shift
    n0, n1 = wc - window_w / 2, wc + window_w / 2
    result = result - cbox(-2, n0, z0, WALL + 2, n1, z1)
    result = result - cbox(total_w - WALL - 2, n0, z0,
                           total_w + 2, n1, z1)

    # comfort chamfer on the top faces' edges (plate top and step)
    for z in (total_h, z1):
        try:
            sel = cq.selectors.BoxSelector(
                (-5, -5, z - 1.2), (total_w + 5, total_d + 5, z + 1.2))
            result = result.edges(sel).chamfer(RIM_CHAMFER)
        except Exception:
            pass

    # print orientation: stand on the closed end wall (y=0 face down on
    # bed), loading mouth and floor scoop facing up
    result = (result.rotate((0, 0, 0), (1, 0, 0), 90)
                    .translate((0, total_h, 0)))

    return result, total_w, total_d, total_h, in_xy, in_h


def export_3mf(mesh, path):
    """Minimal generic 3MF container for Bambu Studio."""
    import zipfile
    verts = "".join(
        f'<vertex x="{v[0]:.4f}" y="{v[1]:.4f}" z="{v[2]:.4f}"/>'
        for v in mesh.vertices)
    tris = "".join(
        f'<triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>'
        for f in mesh.faces)
    model_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        '<resources><object id="1" type="model"><mesh>'
        f'<vertices>{verts}</vertices>'
        f'<triangles>{tris}</triangles>'
        '</mesh></object></resources>'
        '<build><item objectid="1"/></build></model>')
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType='
        '"application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType='
        '"application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type='
        '"http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model_xml)


def export_viewer(stem, name, stl_path, total_w, total_d, total_h, in_xy, in_h):
    import base64
    with open(stl_path, "rb") as f:
        stl_base64 = base64.b64encode(f.read()).decode("utf-8")
    html_content = f'''<!DOCTYPE html>
<html><head><title>{name} Holder - 3D Viewer</title>
<style>
body {{ margin:0; overflow:hidden; font-family:Arial,sans-serif; }}
#info {{ position:absolute; top:10px; left:10px; background:rgba(0,0,0,0.75);
         color:white; padding:15px 20px; border-radius:8px; max-width:360px; }}
#info h2 {{ margin:0 0 8px 0; font-size:16px; }}
#info p {{ margin:4px 0; font-size:13px; color:#ccc; }}
#controls {{ position:absolute; bottom:10px; left:10px; background:rgba(0,0,0,0.6);
            color:#aaa; padding:8px 12px; border-radius:5px; font-size:11px; }}
</style></head>
<body>
<div id="info">
  <h2>{name} Holder (v4, under-beam garage)</h2>
  <p>Pocket: {in_xy:.0f} x {in_xy:.0f} x {in_h:.0f} mm, scale slides in display-up</p>
  <p>Overall: {total_w:.1f} x {total_d:.1f} x {total_h:.1f} mm (use orientation)</p>
  <p>Mount: VHB adhesive on flat top plane, open front for loading</p>
  <p>USB windows in both side walls (rotate scale to expose port)</p>
  <p>Print: as shown (standing on back wall), no supports</p>
</div>
<div id="controls">Left drag: Rotate | Right drag: Pan | Scroll: Zoom</div>
<script type="importmap">{{
  "imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
  }}
}}</script>
<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf5f5f5);
const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 10000);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0x606060, 1.5));
const dl = new THREE.DirectionalLight(0xffffff, 1.2);
dl.position.set(200, 300, 200);
scene.add(dl);
const dl2 = new THREE.DirectionalLight(0xffffff, 0.5);
dl2.position.set(-100, 200, -100);
scene.add(dl2);

scene.add(new THREE.GridHelper(300, 30, 0x999999, 0xdddddd));
scene.add(new THREE.AxesHelper(80));

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

const loader = new STLLoader();
const raw = atob('{stl_base64}');
const arr = new Uint8Array(raw.length);
for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
const geometry = loader.parse(arr.buffer);
geometry.center();
geometry.computeVertexNormals();
const material = new THREE.MeshPhongMaterial({{
  color: 0x4A90D9, specular: 0x222222, shininess: 120, flatShading: false
}});
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

const box = new THREE.Box3().setFromObject(mesh);
const sz = box.getSize(new THREE.Vector3());
const maxD = Math.max(sz.x, sz.y, sz.z);
camera.position.set(maxD*1.2, maxD*0.9, maxD*1.2);
camera.lookAt(0, 0, 0);

function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
addEventListener('resize', () => {{
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
}});
animate();
</script></body></html>'''
    html_path = os.path.join(script_dir, f"{stem}_viewer.html")
    with open(html_path, "w") as f:
        f.write(html_content)
    return html_path


# === BUILD, EXPORT, VALIDATE each holder ===
for (stem, name, footprint, scale_t, scoop_w, scoop_d,
     window_w, window_shift, setback) in SCALES:
    result, total_w, total_d, total_h, in_xy, in_h = build_holder(
        footprint, scale_t, scoop_w, scoop_d, window_w, window_shift, setback)

    stl_path = os.path.join(script_dir, f"{stem}.stl")
    cq.exporters.export(result, stl_path, exportType="STL",
                        tolerance=0.01, angularTolerance=0.1)

    print(f"\n=== {name} Holder (v4, under-beam garage) ===")
    print(f"Scale: {footprint:.0f} x {footprint:.0f} x {scale_t:.0f} mm, display up")
    print(f"Pocket: {in_xy:.0f} x {in_xy:.0f} x {in_h:.0f} mm, open front")
    print(f"Overall: {total_w:.1f} W x {total_d:.1f} D x {total_h:.1f} H mm (use)")
    print(f"Top plane: {total_w:.0f} x {total_d - setback:.0f} mm "
          f"(adhesive area ~{total_w * (total_d - setback) / 100:.0f} cm2), "
          f"{setback:.0f} mm front setback")
    print(f"USB windows: {window_w:.0f} mm wide x {in_h:.0f} mm, both side walls")
    print(f"Floor scoop: {scoop_w:.0f} x {scoop_d:.0f} mm ellipse")
    print(f"STL: {stl_path}")

    try:
        import trimesh
        mesh = trimesh.load(stl_path)
        print(f"Watertight: {mesh.is_watertight} | "
              f"Volume: {mesh.volume / 1000:.1f} cm3 | "
              f"Weight: ~{mesh.volume / 1000 * 1.24:.0f}g PLA")
        if not mesh.is_watertight:
            raise SystemExit(f"ERROR: {stem} mesh is not watertight")
        threemf_path = os.path.join(script_dir, f"{stem}.3mf")
        export_3mf(mesh, threemf_path)
        print(f"3MF: {threemf_path}")
    except ImportError:
        print("trimesh not available, validation/3MF skipped")

    html_path = export_viewer(stem, name, stl_path, total_w, total_d,
                              total_h, in_xy, in_h)
    print(f"Viewer: {html_path}")

print("\nPrint both as exported: standing on the back wall, NO supports.")
