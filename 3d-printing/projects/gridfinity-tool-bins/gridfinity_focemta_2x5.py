#!/usr/bin/env python3
"""
Gridfinity 2×5 Bin for FOCEMTA Circuit Breaker Finder Kit
=========================================================
Stores: Non-contact voltage tester pen + GFCI outlet tester + accessories
Grid:   2 wide × 5 long (83.5mm × 209.5mm footprint)
Height: 5 units (35mm internal depth)

Layout (top view):
    ┌──────────┬───────────────┐
    │          │  GFCI TESTER  │
    │   PEN    │    POCKET     │
    │ CHANNEL  ├───────────────┤
    │  (30mm)  │  ACCESSORY    │
    │          │    AREA       │
    │  cradle  │   (48.8mm)    │
    │  ridges  │               │
    └──────────┴───────────────┘
"""
import cadquery as cq
import os

# ============================================================
# GRIDFINITY STANDARD PARAMETERS
# ============================================================
GRID = 42.0           # Grid pitch (mm)
GX = 2                # Grid units wide
GY = 5                # Grid units long
HU = 5                # Height units (7mm each)
CLEARANCE = 0.25      # Clearance per side from grid
WALL = 1.6            # Wall thickness (mm)
FLOOR = 2.5           # Floor thickness (mm)
CORNER_R = 3.75       # Outer corner radius (mm)

# Derived dimensions
BIN_W = GX * GRID - 2 * CLEARANCE    # 83.5mm
BIN_L = GY * GRID - 2 * CLEARANCE    # 209.5mm
INTERNAL_H = HU * 7.0                 # 35.0mm
TOTAL_H = FLOOR + INTERNAL_H          # 37.5mm
INNER_W = BIN_W - 2 * WALL            # 80.3mm
INNER_L = BIN_L - 2 * WALL            # 206.3mm

# ============================================================
# TOOL DIMENSIONS (with ~1mm tolerance per side)
# ============================================================
# Voltage tester pen: ~178mm long × 28mm diameter
PEN_CH_W = 30.0        # Channel width (28mm + 2mm tolerance)

# GFCI outlet tester: ~55mm × 45mm face, ~25mm deep body
# Prongs (~19mm) extend above bin rim for easy grabbing
TESTER_PK_L = 62.0     # Pocket length along bin Y

# Divider
DIVIDER = 1.5           # Center divider thickness (mm)

# ============================================================
# LAYOUT CALCULATIONS
# ============================================================
# Cross section: [WALL | PEN_CHANNEL | DIVIDER | RIGHT_SECTION | WALL]
RIGHT_W = INNER_W - PEN_CH_W - DIVIDER   # ~48.8mm

# X centers (relative to bin center)
PEN_CX = -INNER_W / 2 + PEN_CH_W / 2
RIGHT_CX = INNER_W / 2 - RIGHT_W / 2

# Tester pocket in right section (near front end)
TESTER_CY = INNER_L / 2 - TESTER_PK_L / 2 - 3  # 3mm from front wall

# Shelf divider Y position (separates tester from accessory area)
SHELF_Y = TESTER_CY - TESTER_PK_L / 2 - DIVIDER / 2

# Pen cradle ridges
RIDGE_W = 4.0           # Ridge width (mm)
RIDGE_H = 6.0           # Ridge height (mm)
RIDGE_OFFSET = 8.0      # Distance from channel center (mm)
RIDGE_L = INNER_L - 8   # Slightly shorter than channel for clearance

# ============================================================
# BUILD GEOMETRY
# ============================================================
print("=" * 60)
print("Gridfinity 2×5 Bin - FOCEMTA Circuit Breaker Finder Kit")
print("=" * 60)
print(f"Bin outer:       {BIN_W:.1f} × {BIN_L:.1f} × {TOTAL_H:.1f} mm")
print(f"Pen channel:     {PEN_CH_W:.1f}mm wide × {INNER_L:.1f}mm long")
print(f"Right section:   {RIGHT_W:.1f}mm wide × {INNER_L:.1f}mm long")
print(f"Tester pocket:   {RIGHT_W:.1f} × {TESTER_PK_L:.1f}mm")
print(f"Internal height: {INTERNAL_H:.1f}mm")
print(f"Pen cradle:      2 ridges at ±{RIDGE_OFFSET}mm, {RIDGE_H}mm tall")
print("=" * 60)

# --- Step 1: Outer body with rounded vertical corners ---
print("\n[1/5] Creating outer body...")
outer = (
    cq.Workplane("XY")
    .box(BIN_W, BIN_L, TOTAL_H, centered=(True, True, False))
    .edges("|Z")
    .fillet(CORNER_R)
)

# --- Step 2: Create pocket volumes ---
print("[2/5] Creating interior pockets...")

# Pen channel (full length, left side)
pen_pocket = (
    cq.Workplane("XY")
    .workplane(offset=FLOOR)
    .center(PEN_CX, 0)
    .rect(PEN_CH_W, INNER_L)
    .extrude(INTERNAL_H)
)

# Right section (full length, right side)
right_pocket = (
    cq.Workplane("XY")
    .workplane(offset=FLOOR)
    .center(RIGHT_CX, 0)
    .rect(RIGHT_W, INNER_L)
    .extrude(INTERNAL_H)
)

# Subtract both pockets
result = outer.cut(pen_pocket).cut(right_pocket)

# --- Step 3: Add pen cradle ridges ---
print("[3/5] Adding pen cradle ridges...")
for dx in [-RIDGE_OFFSET, RIDGE_OFFSET]:
    ridge = (
        cq.Workplane("XY")
        .workplane(offset=FLOOR)
        .center(PEN_CX + dx, 0)
        .rect(RIDGE_W, RIDGE_L)
        .extrude(RIDGE_H)
    )
    result = result.union(ridge)

# --- Step 4: Add shelf divider in right section ---
print("[4/5] Adding shelf divider...")
shelf = (
    cq.Workplane("XY")
    .workplane(offset=FLOOR)
    .center(RIGHT_CX, SHELF_Y)
    .rect(RIGHT_W, DIVIDER)
    .extrude(INTERNAL_H)
)
result = result.union(shelf)

# --- Step 5: Add bottom chamfer for clean look ---
print("[5/5] Adding bottom chamfer...")
try:
    result = result.faces("<Z").chamfer(0.6)
except Exception:
    print("  (skipping bottom chamfer - non-critical)")

# ============================================================
# EXPORT STL
# ============================================================
output_dir = os.path.dirname(os.path.abspath(__file__))
stl_path = os.path.join(output_dir, "gridfinity_focemta_2x5.stl")

print(f"\nExporting STL...")
cq.exporters.export(result, stl_path)
print(f"✓ Exported: {stl_path}")

# ============================================================
# VALIDATE MESH
# ============================================================
print("\nValidating mesh...")
try:
    import trimesh
    mesh = trimesh.load(stl_path)
    print(f"  Watertight: {mesh.is_watertight}")
    print(f"  Volume:     {mesh.volume:.0f} mm³")
    bb = mesh.bounds
    dims = bb[1] - bb[0]
    print(f"  Dimensions: {dims[0]:.1f} × {dims[1]:.1f} × {dims[2]:.1f} mm")
    print(f"  Triangles:  {len(mesh.faces)}")
except ImportError:
    print("  (trimesh not installed, skipping validation)")

# ============================================================
# GENERATE INTERACTIVE 3D VIEWER
# ============================================================
print("\nGenerating interactive 3D viewer...")
import base64

with open(stl_path, 'rb') as f:
    stl_base64 = base64.b64encode(f.read()).decode('utf-8')

html_content = f'''<!DOCTYPE html>
<html><head>
<title>Gridfinity FOCEMTA Kit - 3D Viewer</title>
<style>
body {{ margin:0; overflow:hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; }}
#info {{
    position:absolute; top:15px; left:15px;
    background: rgba(0,0,0,0.75); backdrop-filter: blur(10px);
    color:white; padding:20px; border-radius:12px;
    max-width: 320px; border: 1px solid rgba(255,255,255,0.1);
}}
#info h2 {{ margin:0 0 8px 0; font-size:16px; color: #64b5f6; }}
#info p {{ margin:4px 0; font-size:12px; color: #b0b0b0; line-height: 1.5; }}
#info .dim {{ color: #81c784; font-weight: 500; }}
#controls {{
    position:absolute; bottom:15px; left:50%; transform:translateX(-50%);
    background: rgba(0,0,0,0.6); backdrop-filter: blur(10px);
    color: #888; padding:8px 16px; border-radius:20px;
    font-size:11px; border: 1px solid rgba(255,255,255,0.05);
}}
</style>
</head><body>
<div id="info">
    <h2>Gridfinity 2x5 - FOCEMTA Kit</h2>
    <p>Bin: <span class="dim">{BIN_W:.1f} x {BIN_L:.1f} x {TOTAL_H:.1f} mm</span></p>
    <p>Left: Voltage tester pen channel ({PEN_CH_W:.0f}mm)</p>
    <p>Right: GFCI tester pocket + accessory area</p>
    <p>Height: {HU}u ({INTERNAL_H:.0f}mm internal)</p>
</div>
<div id="controls">Drag: Rotate &nbsp;|&nbsp; Right-drag: Pan &nbsp;|&nbsp; Scroll: Zoom</div>
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
scene.background = new THREE.Color(0x1a1a2e);
const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 10000);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

// Lighting
const ambient = new THREE.AmbientLight(0x404060, 2);
scene.add(ambient);
const key = new THREE.DirectionalLight(0xffffff, 1.2);
key.position.set(150, 200, 100);
key.castShadow = true;
scene.add(key);
const fill = new THREE.DirectionalLight(0x8888ff, 0.4);
fill.position.set(-100, 50, -50);
scene.add(fill);

// Grid
const grid = new THREE.GridHelper(300, 30, 0x333355, 0x222244);
scene.add(grid);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

// Load embedded STL
const loader = new STLLoader();
const raw = atob('{stl_base64}');
const arr = new Uint8Array(raw.length);
for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
const geometry = loader.parse(arr.buffer);
geometry.center();

const material = new THREE.MeshPhysicalMaterial({{
    color: 0x4A90D9,
    metalness: 0.1,
    roughness: 0.35,
    clearcoat: 0.3,
    clearcoatRoughness: 0.2,
}});
const mesh = new THREE.Mesh(geometry, material);
mesh.castShadow = true;
mesh.receiveShadow = true;
scene.add(mesh);

// Auto-fit camera
const box = new THREE.Box3().setFromObject(mesh);
const size = box.getSize(new THREE.Vector3());
const maxDim = Math.max(size.x, size.y, size.z);
camera.position.set(maxDim * 1.0, maxDim * 0.8, maxDim * 1.2);
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
</script>
</body></html>'''

html_path = os.path.join(output_dir, "gridfinity_focemta_2x5.html")
with open(html_path, 'w') as f:
    f.write(html_content)
print(f"✓ Interactive viewer: {html_path}")

# ============================================================
# PRINT SETTINGS
# ============================================================
print("\n" + "=" * 60)
print("RECOMMENDED PRINT SETTINGS")
print("=" * 60)
print("  Material:     PLA or PETG")
print("  Layer height: 0.2mm")
print("  Infill:       15-20% grid")
print("  Walls:        3-4 perimeters")
print("  Supports:     None needed")
print("  Orientation:  Print upright (opening facing up)")
print("  Bed adhesion: Brim recommended for long bin")
print("=" * 60)
