#!/usr/bin/env python3
"""
Gridfinity 4x1 Bin - KAIWEETS HT100 Voltage Tester Holder
Custom pen-style NCV tester holder with finger scoop
Fits standard 42mm Gridfinity baseplates

Tool: KAIWEETS HT100 Non-Contact Voltage Tester
      ~158mm x 23mm x 20mm pen-style form factor
"""
import cadquery as cq
from cadquery import exporters
import base64

# === GRIDFINITY STANDARD ===
GRID = 42.0              # mm per grid unit
GAP = 0.5                # Total gap between bin and cell (0.25mm per side)
CORNER_R = 3.75          # Standard Gridfinity corner radius
HEIGHT_U = 7.0           # mm per height unit

# === BIN CONFIGURATION ===
UNITS_X = 4              # 4 cells long
UNITS_Y = 1              # 1 cell wide
HEIGHT_UNITS = 4         # 4 height units = 28mm total
WALL = 1.6               # mm wall thickness
FLOOR = 2.0              # mm floor thickness

# === TOOL DIMENSIONS: KAIWEETS HT100 ===
TOOL_L = 158.0           # mm length
TOOL_W = 23.0            # mm width (widest point, clip end)
TOOL_H = 20.0            # mm height/depth
TOL = 1.0                # mm clearance per side

# === DERIVED DIMENSIONS ===
BIN_L = UNITS_X * GRID - GAP    # 167.5mm
BIN_W = UNITS_Y * GRID - GAP    # 41.5mm
BIN_H = HEIGHT_UNITS * HEIGHT_U  # 28.0mm

INNER_L = BIN_L - 2 * WALL      # 164.3mm
INNER_W = BIN_W - 2 * WALL      # 38.3mm
INNER_H = BIN_H - FLOOR         # 26.0mm

# Finger scoop
SCOOP_R = 10.0           # mm radius of scoop cutout

# === PRINT INFO ===
print("=" * 55)
print("  Gridfinity KAIWEETS HT100 Voltage Tester Bin")
print("=" * 55)
print(f"  Grid:     {UNITS_X}x{UNITS_Y}, {HEIGHT_UNITS} height units")
print(f"  Outer:    {BIN_L:.1f} x {BIN_W:.1f} x {BIN_H:.1f} mm")
print(f"  Interior: {INNER_L:.1f} x {INNER_W:.1f} x {INNER_H:.1f} mm")
print(f"  Tool:     {TOOL_L} x {TOOL_W} x {TOOL_H} mm (+{TOL}mm tol)")
print(f"  Wall: {WALL}mm | Floor: {FLOOR}mm")
print("=" * 55)

# === BUILD GEOMETRY ===

# Step 1: Outer body with rounded vertical corners
result = (
    cq.Workplane("XY")
    .rect(BIN_L, BIN_W)
    .extrude(BIN_H)
    .edges("|Z")
    .fillet(CORNER_R)
)

# Step 2: Interior pocket from top face
result = (
    result
    .faces(">Z")
    .workplane()
    .rect(INNER_L, INNER_W)
    .cutBlind(-INNER_H)
)

# Step 3: Finger scoop at +X end
# Horizontal cylinder along Y axis, positioned at inner end wall
# Center Z = floor + radius so bottom of scoop circle touches floor level
scoop_cx = BIN_L / 2 - WALL       # At inner surface of +X end wall
scoop_cz = FLOOR + SCOOP_R        # Bottom of scoop at floor level

scoop_cyl = (
    cq.Workplane("XZ")
    .center(scoop_cx, scoop_cz)
    .circle(SCOOP_R)
    .extrude(BIN_W, both=True)
)

result = result.cut(scoop_cyl)

# Step 4: Bottom chamfer for Gridfinity baseplate interface
# The 45-degree chamfer helps the bin self-center on the baseplate
result = result.edges("<Z").chamfer(0.8)

# === EXPORT STL ===
OUTPUT_STL = "gridfinity_kaiweets_ht100.stl"
exporters.export(result, OUTPUT_STL)
print(f"\n✓ Exported: {OUTPUT_STL}")

# === VALIDATION ===
try:
    import trimesh
    mesh = trimesh.load(OUTPUT_STL)
    is_wt = mesh.is_watertight
    vol = mesh.volume
    status = "✓" if is_wt else "✗"
    print(f"{status} Watertight: {is_wt}")
    print(f"✓ Volume: {vol:.1f} mm³")
    weight_g = vol * 1.24e-3  # PLA density ~1.24 g/cm³
    print(f"✓ Est. weight (PLA): {weight_g:.1f} g")
except ImportError:
    is_wt = None
    vol = 0
    print("  (Install trimesh for mesh validation)")

# === INTERACTIVE 3D VIEWER ===
with open(OUTPUT_STL, 'rb') as f:
    stl_base64 = base64.b64encode(f.read()).decode('utf-8')

dims_text = f"{BIN_L:.1f} x {BIN_W:.1f} x {BIN_H:.1f} mm"
weight_text = f"~{vol * 1.24e-3:.0f}g PLA" if vol > 0 else ""

html_content = f'''<!DOCTYPE html>
<html><head><title>Gridfinity KAIWEETS HT100 Bin - 3D Viewer</title>
<style>
body {{ margin:0; overflow:hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }}
#info {{
    position:absolute; top:10px; left:10px;
    background:rgba(0,0,0,0.75); color:white;
    padding:15px 20px; border-radius:8px;
    max-width: 320px; line-height: 1.5;
}}
#info h2 {{ margin: 0 0 8px 0; font-size: 16px; }}
#info p {{ margin: 2px 0; font-size: 13px; color: #ccc; }}
#info .dim {{ color: #4A90D9; font-weight: bold; }}
#controls {{
    position:absolute; bottom:10px; left:10px;
    background:rgba(0,0,0,0.6); color:#aaa;
    padding:8px 12px; border-radius:5px; font-size:11px;
}}
</style></head>
<body>
<div id="info">
    <h2>Gridfinity KAIWEETS HT100 Bin</h2>
    <p>Grid: <span class="dim">{UNITS_X}x{UNITS_Y}</span>, Height: <span class="dim">{HEIGHT_UNITS}U</span></p>
    <p>Outer: <span class="dim">{dims_text}</span></p>
    <p>Tool: KAIWEETS HT100 ({TOOL_L}x{TOOL_W}x{TOOL_H}mm)</p>
    <p>Wall: {WALL}mm | Floor: {FLOOR}mm | Scoop: R{SCOOP_R}mm</p>
    <p>{weight_text}</p>
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
scene.background = new THREE.Color(0xf0f0f0);
const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 10000);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0x404040, 2));
const light1 = new THREE.DirectionalLight(0xffffff, 1.2);
light1.position.set(150, 200, 100);
light1.castShadow = true;
scene.add(light1);
const light2 = new THREE.DirectionalLight(0xffffff, 0.4);
light2.position.set(-100, 50, -100);
scene.add(light2);

const grid = new THREE.GridHelper(200, 20, 0x888888, 0xdddddd);
scene.add(grid);
scene.add(new THREE.AxesHelper(50));

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

const loader = new STLLoader();
const stlData = atob('{stl_base64}');
const arr = new Uint8Array(stlData.length);
for (let i = 0; i < stlData.length; i++) arr[i] = stlData.charCodeAt(i);
const geometry = loader.parse(arr.buffer);
geometry.center();
geometry.computeVertexNormals();

const material = new THREE.MeshPhongMaterial({{
    color: 0x4A90D9, specular: 0x222222, shininess: 80, flatShading: false
}});
const mesh = new THREE.Mesh(geometry, material);
mesh.castShadow = true;
mesh.receiveShadow = true;
scene.add(mesh);

const box = new THREE.Box3().setFromObject(mesh);
const size = box.getSize(new THREE.Vector3());
const maxDim = Math.max(size.x, size.y, size.z);
const fov = camera.fov * (Math.PI / 180);
let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.8;
camera.position.set(cameraZ * 0.8, cameraZ * 0.6, cameraZ * 0.8);
camera.lookAt(0, 0, 0);
controls.target.set(0, 0, 0);

function animate() {{
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}}
window.addEventListener('resize', () => {{
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
}});
animate();
</script></body></html>'''

OUTPUT_HTML = "gridfinity_kaiweets_ht100.html"
with open(OUTPUT_HTML, 'w') as f:
    f.write(html_content)
print(f"✓ Interactive viewer: {OUTPUT_HTML}")

# === PRINT SETTINGS ===
print(f"\n{'=' * 55}")
print("  RECOMMENDED PRINT SETTINGS")
print(f"{'=' * 55}")
print("  Layer height:  0.2mm")
print("  Walls:         3-4 (for rigidity)")
print("  Infill:        15-20% grid")
print("  Supports:      None needed")
print("  Orientation:   Upright (opening on top)")
print("  Material:      PLA or PETG")
print(f"{'=' * 55}")
