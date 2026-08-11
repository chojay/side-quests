#!/usr/bin/env python3
"""
Korean Disposable Glove Box Dispenser (실속크린장갑)
Parametric design - generates STL for 3D printing.

Box dimensions: 19cm W × 15.5cm H × 4cm D
Dispenser: open-top sleeve with U-shaped front cutout and keyhole mounting slots.

To change depth for different glove boxes, modify INNER_D below.
Keyhole slots allow swapping dispensers without removing bolts.
"""
import cadquery as cq
import os

# === PARAMETERS (all in mm) ===
# Internal cavity (slightly larger than glove box for easy fit)
INNER_W = 192.0    # 19cm + 2mm clearance
INNER_H = 157.0    # 15.5cm + 2mm clearance
INNER_D = 46.0     # 4.5cm + 1mm clearance (depth front-to-back)
                    # ^^^ CHANGE THIS for different glove box thicknesses

WALL = 2.5         # wall thickness (mm)
FILLET_R = 3.0     # external edge rounding

# U-shaped cutout on front face
CUTOUT_W = 150.0   # ~15cm wide ellipse
CUTOUT_H = 85.0    # ~8.5cm deep from top edge

# Keyhole mounting slots on back wall
HOLE_INSET = 12.7       # 1/2 inch from each corner
KEY_ENTRY_DIA = 9.5     # large circle for screw head entry (#8 pan head ~8.5mm)
KEY_SLOT_W = 5.0        # narrow slot for screw shank (#8 = 4.17mm + 0.83mm clearance)
KEY_SLOT_L = 8.0        # slot travel distance
KEY_CBORE_DIA = 9.5     # inside counterbore width along slot (screw head channel)
KEY_CBORE_DEPTH = 1.2   # inside counterbore depth (donut recess on inside face)

# Derived outer dimensions
OUTER_W = INNER_W + 2 * WALL
OUTER_H = INNER_H + WALL       # only bottom wall, open top
OUTER_D = INNER_D + 2 * WALL

# === BUILD GEOMETRY ===
# Step 1: Create solid outer box
outer = (
    cq.Workplane("XY")
    .box(OUTER_W, OUTER_D, OUTER_H, centered=(True, True, False))
)

# Step 2: Round the vertical edges for nice look
outer = outer.edges("|Z").fillet(FILLET_R)

# Step 3: Hollow out - cut from top, leaving bottom + all 4 walls
inner = (
    cq.Workplane("XY")
    .workplane(offset=WALL)  # start above the bottom wall
    .box(INNER_W, INNER_D, INNER_H + 10, centered=(True, True, False))
)
result = outer - inner

# Step 4: Create the U-shaped cutout on the front face
cutout = (
    cq.Workplane("XZ")
    .workplane(offset=OUTER_D / 2 + 1)
    .center(0, OUTER_H)
    .ellipse(CUTOUT_W / 2, CUTOUT_H)
    .extrude(-WALL - 2)
)
result = result - cutout

# Step 5: Keyhole mounting slots on back wall
# Layout: 4 keyholes, one near each corner
# All slots extend downward (same direction) so one slide motion locks all 4
# Mount upside-down: slide up to lock; screw heads captured behind wall
hole_x = OUTER_W / 2 - HOLE_INSET
hole_z_top = OUTER_H - HOLE_INSET
hole_z_bot = WALL + HOLE_INSET

# (x_pos, z_pos_of_entry, slot_direction): +1=up, -1=down
keyhole_configs = [
    (+hole_x, hole_z_bot, -1),   # bottom-right, slot extends down
    (-hole_x, hole_z_bot, -1),   # bottom-left, slot extends down
    (+hole_x, hole_z_top, -1),   # top-right, slot extends down
    (-hole_x, hole_z_top, -1),   # top-left, slot extends down
]

back_y_outside = -OUTER_D / 2
thru_y = back_y_outside - 1      # start just outside back wall
thru_d = WALL + 2                # punch through entire wall

cbore_y = back_y_outside + WALL - KEY_CBORE_DEPTH  # start inside the wall
cbore_d = KEY_CBORE_DEPTH + 1    # recess into inside face

for hx, hz, d in keyhole_configs:
    slot_end = hz + d * KEY_SLOT_L
    mid_z = (hz + slot_end) / 2

    # --- Through-holes (full wall thickness) ---
    # Large entry circle (bolt head passes through here)
    result = result - (
        cq.Workplane("XZ").workplane(offset=thru_y)
        .center(hx, hz).circle(KEY_ENTRY_DIA / 2)
        .extrude(thru_d)
    )
    # Narrow slot body (bolt shank slides here)
    result = result - (
        cq.Workplane("XZ").workplane(offset=thru_y)
        .center(hx, mid_z).rect(KEY_SLOT_W, abs(KEY_SLOT_L))
        .extrude(thru_d)
    )
    # Rounded end cap at slot terminus
    result = result - (
        cq.Workplane("XZ").workplane(offset=thru_y)
        .center(hx, slot_end).circle(KEY_SLOT_W / 2)
        .extrude(thru_d)
    )

    # --- Inside counterbore (donut recess on inside face) ---
    # Wider channel so bolt head can slide along the slot from inside
    # Counterbore body (rectangle)
    result = result - (
        cq.Workplane("XZ").workplane(offset=cbore_y)
        .center(hx, mid_z).rect(KEY_CBORE_DIA, abs(KEY_SLOT_L))
        .extrude(cbore_d)
    )
    # Counterbore end cap at slot terminus
    result = result - (
        cq.Workplane("XZ").workplane(offset=cbore_y)
        .center(hx, slot_end).circle(KEY_CBORE_DIA / 2)
        .extrude(cbore_d)
    )
    # Counterbore cap at entry (blends with entry through-hole)
    result = result - (
        cq.Workplane("XZ").workplane(offset=cbore_y)
        .center(hx, hz).circle(KEY_CBORE_DIA / 2)
        .extrude(cbore_d)
    )

# Step 6: Fillet the top edges for comfort and aesthetics
try:
    top_edges = result.edges(
        cq.selectors.BoxSelector(
            (-OUTER_W, -OUTER_D, OUTER_H - 2),
            (OUTER_W, OUTER_D, OUTER_H + 2)
        )
    )
    result = top_edges.fillet(1.0)
except Exception:
    pass  # If fillet fails on complex geometry, skip it

# === EXPORT ===
script_dir = os.path.dirname(os.path.abspath(__file__))
stl_path = os.path.join(script_dir, "glove_dispenser.stl")

cq.exporters.export(result, stl_path, exportType="STL", tolerance=0.01, angularTolerance=0.1)
print(f"✓ Exported STL: {stl_path}")

# Dimensions summary
print(f"\n=== Glove Dispenser Dimensions ===")
print(f"Outer: {OUTER_W:.1f} × {OUTER_D:.1f} × {OUTER_H:.1f} mm")
print(f"Inner: {INNER_W:.1f} × {INNER_D:.1f} × {INNER_H:.1f} mm")
print(f"Wall thickness: {WALL:.1f} mm")
print(f"Front cutout: {CUTOUT_W:.1f}W × {CUTOUT_H:.1f}H mm ellipse")
print(f"Keyhole slots: {KEY_ENTRY_DIA:.0f}mm entry → {KEY_SLOT_W:.0f}mm slot × {KEY_SLOT_L:.0f}mm travel")
print(f"Hole inset: {HOLE_INSET:.1f}mm (1/2\") from each corner")
print(f"Counterbore: {KEY_CBORE_DIA:.0f}mm × {KEY_CBORE_DEPTH:.1f}mm deep (inside face)")
print(f"\nPrint orientation: open-top facing UP (no supports needed)")

# === VALIDATE ===
try:
    import trimesh
    mesh = trimesh.load(stl_path)
    print(f"\n=== Mesh Validation ===")
    print(f"Watertight: {mesh.is_watertight}")
    print(f"Volume: {mesh.volume:.2f} mm³ ({mesh.volume/1000:.2f} cm³)")

    weight_pla = mesh.volume / 1000 * 1.24
    print(f"Est. weight (PLA): {weight_pla:.1f}g")
    print(f"Est. weight (PETG): {mesh.volume / 1000 * 1.27:.1f}g")
except Exception as e:
    print(f"Validation skipped: {e}")

# === GENERATE HTML VIEWER ===
try:
    import base64
    with open(stl_path, 'rb') as f:
        stl_base64 = base64.b64encode(f.read()).decode('utf-8')

    html_content = f'''<!DOCTYPE html>
<html><head><title>Glove Dispenser - 3D Viewer</title>
<style>
body {{ margin:0; overflow:hidden; font-family:Arial,sans-serif; }}
#info {{ position:absolute; top:10px; left:10px; background:rgba(0,0,0,0.75);
         color:white; padding:15px 20px; border-radius:8px; max-width:340px; }}
#info h2 {{ margin:0 0 8px 0; font-size:16px; }}
#info p {{ margin:4px 0; font-size:13px; color:#ccc; }}
#controls {{ position:absolute; bottom:10px; left:10px; background:rgba(0,0,0,0.6);
            color:#aaa; padding:8px 12px; border-radius:5px; font-size:11px; }}
</style></head>
<body>
<div id="info">
  <h2>Glove Box Dispenser (v2 - Keyhole Mount)</h2>
  <p>Outer: {OUTER_W:.0f} x {OUTER_D:.0f} x {OUTER_H:.0f} mm</p>
  <p>Wall: {WALL:.1f}mm | Cutout: {CUTOUT_W:.0f}x{CUTOUT_H:.0f}mm</p>
  <p>Mount: 4x keyhole slots ({KEY_ENTRY_DIA:.0f}mm entry, {KEY_SLOT_W:.0f}mm slot)</p>
  <p>Counterbore on inside face ({KEY_CBORE_DEPTH:.1f}mm deep)</p>
  <p>Print: open-top UP, no supports</p>
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
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0x606060, 1.5));
const dl = new THREE.DirectionalLight(0xffffff, 1.2);
dl.position.set(200, 300, 200); dl.castShadow = true;
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
mesh.castShadow = true; mesh.receiveShadow = true;
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

    html_path = os.path.join(script_dir, "glove_dispenser_viewer.html")
    with open(html_path, 'w') as f:
        f.write(html_content)
    print(f"\n✓ Interactive 3D viewer: {html_path}")
except Exception as e:
    print(f"HTML viewer generation skipped: {e}")
