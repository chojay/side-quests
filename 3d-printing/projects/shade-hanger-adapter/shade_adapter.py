#!/usr/bin/env python3
"""
Shade Adapter Generator using numpy-stl
Rectangular plate with two oval holes
Origin at top-left corner (when viewed from above)
"""
import numpy as np
from stl import mesh
import trimesh
import base64

# === PARAMETERS ===
PLATE_X = 30.0  # mm
PLATE_Y = 45.0  # mm
PLATE_Z = 4.0   # mm (thickness)
CORNER_RADIUS = 3.0  # mm - radius for rounded corners

# Hole specifications (oval/ellipse)
HOLE_SIZE_X = 4.33  # mm (diameter in X)
HOLE_SIZE_Y = 6.0   # mm (diameter in Y)
HOLE_RADIUS_X = HOLE_SIZE_X / 2  # 2.165mm
HOLE_RADIUS_Y = HOLE_SIZE_Y / 2  # 3.0mm

# Hole positions (from top-left origin)
# Left edge positions given, so center = left_edge + radius_x
HOLE1_LEFT_EDGE = 3.64   # mm from x=0
HOLE2_LEFT_EDGE = 22.14  # mm from x=0
HOLE_Y_FROM_TOP = 18.98  # mm - both holes at same Y (centroid)

# Calculate center positions
HOLE1_X = HOLE1_LEFT_EDGE + HOLE_RADIUS_X  # 3.64 + 2.165 = 5.805mm
HOLE2_X = HOLE2_LEFT_EDGE + HOLE_RADIUS_X  # 22.14 + 2.165 = 24.305mm

SEGMENTS = 32  # smoothness of oval holes

def create_rounded_rectangle_profile(width, height, radius, segments_per_corner=8):
    """Create a 2D rounded rectangle profile as a polygon."""
    points = []

    # Four corners with arcs
    # Corner centers (inset by radius from corners)
    corners = [
        (radius, radius, np.pi, 1.5*np.pi),                    # bottom-left
        (width - radius, radius, 1.5*np.pi, 2*np.pi),          # bottom-right
        (width - radius, height - radius, 0, 0.5*np.pi),       # top-right
        (radius, height - radius, 0.5*np.pi, np.pi),           # top-left
    ]

    for cx, cy, start_angle, end_angle in corners:
        angles = np.linspace(start_angle, end_angle, segments_per_corner, endpoint=False)
        for angle in angles:
            x = cx + radius * np.cos(angle)
            y = cy + radius * np.sin(angle)
            points.append([x, y])

    return np.array(points)

def create_plate_with_oval_holes():
    """Create a rounded rectangular plate with two oval holes."""

    # Create rounded rectangle profile
    profile = create_rounded_rectangle_profile(PLATE_X, PLATE_Y, CORNER_RADIUS)

    # Extrude the profile to create the plate
    plate = trimesh.creation.extrude_polygon(
        trimesh.path.polygons.Polygon(profile),
        height=PLATE_Z
    )

    # Create oval cylinders for the holes
    # Trimesh doesn't have ellipse directly, so we'll create a cylinder and scale it

    def create_oval_cylinder(center_x, center_y, rx, ry, height):
        """Create an oval cylinder at given position."""
        # Create a unit cylinder and scale to oval
        cyl = trimesh.creation.cylinder(radius=1.0, height=height + 2, sections=SEGMENTS)
        # Scale to make it oval
        cyl.apply_scale([rx, ry, 1.0])
        # Move to position (Y from top means Y coordinate directly since origin is at corner)
        cyl.apply_translation([center_x, center_y, height/2])
        return cyl

    # Create hole cylinders
    hole1 = create_oval_cylinder(HOLE1_X, HOLE_Y_FROM_TOP, HOLE_RADIUS_X, HOLE_RADIUS_Y, PLATE_Z)
    hole2 = create_oval_cylinder(HOLE2_X, HOLE_Y_FROM_TOP, HOLE_RADIUS_X, HOLE_RADIUS_Y, PLATE_Z)

    # Boolean subtraction
    result = plate.difference(hole1)
    result = result.difference(hole2)

    return result

# === GENERATE GEOMETRY ===
print("Generating shade adapter geometry...")
adapter = create_plate_with_oval_holes()

# === EXPORT STL ===
stl_file = "shade_adapter.stl"
adapter.export(stl_file)
print(f"✓ Exported: shade_adapter.stl")

# === VALIDATE ===
print(f"✓ Watertight: {adapter.is_watertight}")
print(f"✓ Volume: {adapter.volume:.2f} mm³")

# Print dimensions for verification
bounds = adapter.bounds
print(f"✓ Dimensions: X={bounds[1][0]-bounds[0][0]:.1f}mm, Y={bounds[1][1]-bounds[0][1]:.1f}mm, Z={bounds[1][2]-bounds[0][2]:.1f}mm")
print(f"✓ Corner radius: {CORNER_RADIUS}mm")
print(f"✓ Hole 1: left edge={HOLE1_LEFT_EDGE}mm, center=({HOLE1_X:.3f}, {HOLE_Y_FROM_TOP}) mm")
print(f"✓ Hole 2: left edge={HOLE2_LEFT_EDGE}mm, center=({HOLE2_X:.3f}, {HOLE_Y_FROM_TOP}) mm")
print(f"✓ Hole size: {HOLE_SIZE_X} x {HOLE_SIZE_Y} mm (oval)")

# === GENERATE INTERACTIVE HTML VIEWER ===
with open(stl_file, 'rb') as f:
    stl_base64 = base64.b64encode(f.read()).decode('utf-8')

html_content = f'''<!DOCTYPE html>
<html><head><title>Shade Adapter - 3D Viewer</title>
<style>
body {{ margin:0; overflow:hidden; font-family:Arial,sans-serif; }}
#info {{ position:absolute; top:10px; left:10px; background:rgba(0,0,0,0.75);
         color:white; padding:15px 20px; border-radius:8px; max-width:280px; }}
#info h2 {{ margin:0 0 10px 0; }}
#info p {{ margin:5px 0; font-size:13px; }}
#info .section {{ margin-top:10px; padding-top:8px; border-top:1px solid #555; }}
#controls {{ position:absolute; bottom:10px; left:10px; background:rgba(0,0,0,0.7);
            color:white; padding:10px 15px; border-radius:5px; font-size:12px; }}
</style></head>
<body>
<div id="info">
    <h2>Shade Adapter</h2>
    <p><b>Plate:</b> {PLATE_X:.0f} x {PLATE_Y:.0f} x {PLATE_Z:.0f} mm</p>
    <p><b>Corner radius:</b> {CORNER_RADIUS}mm</p>
    <div class="section">
        <p><b>Oval Holes:</b> {HOLE_SIZE_X} x {HOLE_SIZE_Y} mm</p>
        <p>Hole 1: left edge {HOLE1_LEFT_EDGE}mm, center X={HOLE1_X:.2f}mm</p>
        <p>Hole 2: left edge {HOLE2_LEFT_EDGE}mm, center X={HOLE2_X:.2f}mm</p>
        <p>Y from top: {HOLE_Y_FROM_TOP}mm</p>
    </div>
    <div class="section">
        <p>Volume: {adapter.volume:.1f} mm³</p>
    </div>
</div>
<div id="controls">🖱️ Left drag: Rotate | Right drag: Pan | Scroll: Zoom</div>
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

scene.add(new THREE.AmbientLight(0x404040, 1.5));
const light1 = new THREE.DirectionalLight(0xffffff, 1);
light1.position.set(100, 100, 50);
scene.add(light1);
const light2 = new THREE.DirectionalLight(0xffffff, 0.5);
light2.position.set(-50, 50, -50);
scene.add(light2);

scene.add(new THREE.GridHelper(200, 20, 0x888888, 0xcccccc));

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

const loader = new STLLoader();
const stlData = atob('{stl_base64}');
const arr = new Uint8Array(stlData.length);
for (let i = 0; i < stlData.length; i++) arr[i] = stlData.charCodeAt(i);
const geometry = loader.parse(arr.buffer);
geometry.center();
geometry.computeVertexNormals();

const material = new THREE.MeshPhongMaterial({{ color: 0x4A90D9, specular: 0x222222, shininess: 100 }});
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

const box = new THREE.Box3().setFromObject(mesh);
const size = box.getSize(new THREE.Vector3());
const maxDim = Math.max(size.x, size.y, size.z);
camera.position.set(maxDim * 1.5, maxDim * 1.2, maxDim * 1.5);
controls.target.set(0, 0, 0);

function animate() {{ requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }}
window.addEventListener('resize', () => {{ camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }});
animate();
</script></body></html>'''

html_file = "shade_adapter.html"
with open(html_file, 'w') as f:
    f.write(html_content)
print(f"✓ Interactive viewer: shade_adapter.html")
