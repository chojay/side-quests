#!/opt/homebrew/bin/python3.12
"""
Level Lock Awning Cover
Rain-protective awning with angled top and minimal sidewalls for hand access
Based on user sketch requirements
"""
from build123d import *
import numpy as np
import base64

# === PARAMETERS ===
# Outer dimensions from 3MF
OUTER_WIDTH = 88.9         # mm
OUTER_HEIGHT = 122.0       # mm
BACK_PLATE_THICKNESS = 3.0 # mm

# Lock opening (calculate max with clearances)
SIDE_CLEARANCE = 10.0      # mm - 1cm from circle to sidewall
TOP_CLEARANCE = 10.0       # mm - 1cm from circle to top
max_width = OUTER_WIDTH - 2 * SIDE_CLEARANCE
LOCK_DIAMETER = max_width  # ~68.9mm
LOCK_RADIUS = LOCK_DIAMETER / 2

# Awning/hood dimensions
AWNING_DEPTH = 50.8        # mm - how far awning extends forward
AWNING_THICKNESS = 5.0     # mm - thickness of top awning
AWNING_ANGLE = 15.0        # degrees - slope for rain drainage

# Sidewall dimensions (SHORT - only 1cm below top of circle)
SIDEWALL_THICKNESS = 5.0   # mm
# Calculate where circle top is, then add 1cm below it
circle_center_y = -(OUTER_HEIGHT / 2 - TOP_CLEARANCE - LOCK_RADIUS)  # Position from center
circle_top_y = circle_center_y + LOCK_RADIUS  # Top edge of circle
SIDEWALL_CUT_HEIGHT = circle_top_y - 10.0  # 1cm below circle top

print("=== Level Lock Awning Cover ===")
print(f"Back plate: {OUTER_WIDTH:.1f}W x {OUTER_HEIGHT:.1f}H x {BACK_PLATE_THICKNESS:.1f}D mm")
print(f"Lock opening: {LOCK_DIAMETER:.1f}mm diameter")
print(f"Awning: {AWNING_DEPTH:.1f}mm deep, {AWNING_ANGLE:.0f}° angle")
print(f"Sidewalls: Cut at {SIDEWALL_CUT_HEIGHT:.1f}mm (1cm below circle top)")
print(f"Circle center Y: {circle_center_y:.1f}mm, Circle top: {circle_top_y:.1f}mm")
print()

# === BUILD GEOMETRY ===
with BuildPart() as cover:
    # 1. Create back plate
    with BuildSketch(Plane.XY) as back:
        Rectangle(OUTER_WIDTH, OUTER_HEIGHT)
    extrude(amount=BACK_PLATE_THICKNESS)

    # 2. Cut circular opening for lock (centered with clearances)
    with BuildSketch(Plane.XY) as lock_hole:
        with Locations((0, circle_center_y)):
            Circle(LOCK_RADIUS)
    extrude(amount=BACK_PLATE_THICKNESS, mode=Mode.SUBTRACT)

    # 3. Create angled awning/top
    # Start from back plate, create sloped top
    with BuildSketch(Plane.XY.offset(BACK_PLATE_THICKNESS)) as awning_sketch:
        Rectangle(OUTER_WIDTH, AWNING_THICKNESS)
        # Position at top of back plate
        with Locations((0, (OUTER_HEIGHT - AWNING_THICKNESS) / 2)):
            Rectangle(OUTER_WIDTH, AWNING_THICKNESS, mode=Mode.REPLACE)

    # Extrude forward, then we'll angle it
    extrude(amount=AWNING_DEPTH - BACK_PLATE_THICKNESS)

    # Create angled cut to slope the awning
    # The front should be higher than the back for rain drainage
    angle_rad = np.radians(AWNING_ANGLE)
    height_diff = AWNING_DEPTH * np.tan(angle_rad)

    # Cut from bottom-front to top-back to create slope
    with BuildSketch(Plane.YZ.offset(0)) as angle_cut:
        # Create a polygon that cuts the top at an angle
        front_y = (OUTER_HEIGHT - AWNING_THICKNESS) / 2
        back_y = front_y

        # Points for the cutting polygon (in YZ plane at x=0)
        points = [
            (front_y + AWNING_THICKNESS, AWNING_DEPTH),  # Front top
            (front_y + AWNING_THICKNESS + height_diff, BACK_PLATE_THICKNESS),  # Back top (raised)
            (front_y + AWNING_THICKNESS + height_diff + 50, BACK_PLATE_THICKNESS),  # Extend back
            (front_y + AWNING_THICKNESS + 50, AWNING_DEPTH),  # Extend front
        ]

        Polygon(*points)
    extrude(amount=OUTER_WIDTH, both=True, mode=Mode.SUBTRACT)

    # 4. Create SHORT sidewalls with circle cutouts for hand access
    sidewall_height = (OUTER_HEIGHT / 2) - SIDEWALL_CUT_HEIGHT  # From top down to cut line

    # Left sidewall (short) with circle cutout
    with BuildSketch(Plane.XY.offset(BACK_PLATE_THICKNESS)) as left_wall:
        Rectangle(SIDEWALL_THICKNESS, sidewall_height)
        with Locations(((-OUTER_WIDTH + SIDEWALL_THICKNESS) / 2,
                       (OUTER_HEIGHT / 2) - (sidewall_height / 2))):
            Rectangle(SIDEWALL_THICKNESS, sidewall_height, mode=Mode.REPLACE)
    extrude(amount=AWNING_DEPTH - BACK_PLATE_THICKNESS)

    # Cut circle from left sidewall for hand access
    with BuildSketch(Plane.XZ.offset((-OUTER_WIDTH + SIDEWALL_THICKNESS) / 2)) as left_circle_cut:
        with Locations((circle_center_y, BACK_PLATE_THICKNESS + (AWNING_DEPTH - BACK_PLATE_THICKNESS)/2)):
            Circle(LOCK_RADIUS)
    extrude(amount=SIDEWALL_THICKNESS, both=True, mode=Mode.SUBTRACT)

    # Right sidewall (short) with circle cutout
    with BuildSketch(Plane.XY.offset(BACK_PLATE_THICKNESS)) as right_wall:
        Rectangle(SIDEWALL_THICKNESS, sidewall_height)
        with Locations(((OUTER_WIDTH - SIDEWALL_THICKNESS) / 2,
                       (OUTER_HEIGHT / 2) - (sidewall_height / 2))):
            Rectangle(SIDEWALL_THICKNESS, sidewall_height, mode=Mode.REPLACE)
    extrude(amount=AWNING_DEPTH - BACK_PLATE_THICKNESS)

    # Cut circle from right sidewall for hand access
    with BuildSketch(Plane.XZ.offset((OUTER_WIDTH - SIDEWALL_THICKNESS) / 2)) as right_circle_cut:
        with Locations((circle_center_y, BACK_PLATE_THICKNESS + (AWNING_DEPTH - BACK_PLATE_THICKNESS)/2)):
            Circle(LOCK_RADIUS)
    extrude(amount=SIDEWALL_THICKNESS, both=True, mode=Mode.SUBTRACT)

# === EXPORT STL ===
from build123d import export_stl
output_file = "level-lock-awning-cover.stl"
export_stl(cover.part, output_file)
print(f"✓ Exported: {output_file}")

# === VALIDATION ===
import trimesh
mesh = trimesh.load(output_file)
print(f"✓ Watertight: {mesh.is_watertight}")
print(f"✓ Volume: {mesh.volume:.2f} mm³")

pla_density = 1.24
weight_g = (mesh.volume / 1000) * pla_density
print(f"✓ Estimated PLA weight: {weight_g:.1f}g")

# === GENERATE INTERACTIVE HTML ===
print("\n" + "="*60)
print("GENERATING INTERACTIVE 3D HTML VIEWER...")
print("="*60)

with open(output_file, 'rb') as f:
    stl_base64 = base64.b64encode(f.read()).decode('utf-8')

html_file = output_file.replace('.stl', '.html')

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Level Lock Awning Cover - 3D Viewer</title>
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            font-family: Arial, sans-serif;
        }}
        #info {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 15px;
            border-radius: 5px;
            font-size: 14px;
            max-width: 350px;
        }}
        #info h2 {{
            margin: 0 0 10px 0;
            font-size: 18px;
        }}
        #info p {{
            margin: 5px 0;
        }}
        #controls {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div id="info">
        <h2>Level Lock Awning Cover</h2>
        <p><strong>Dimensions:</strong> {OUTER_WIDTH:.1f}W × {OUTER_HEIGHT:.1f}H mm</p>
        <p><strong>Awning:</strong> {AWNING_DEPTH:.1f}mm deep, {AWNING_ANGLE:.0f}° slope</p>
        <p><strong>Lock Opening:</strong> {LOCK_DIAMETER:.1f}mm diameter</p>
        <p><strong>Weight:</strong> ~{weight_g:.1f}g (PLA)</p>
        <p><strong>Features:</strong></p>
        <ul style="margin:5px 0; padding-left:20px;">
            <li>Angled top for rain drainage</li>
            <li>Short sidewalls (1cm below circle)</li>
            <li>Open bottom for hand access</li>
        </ul>
    </div>
    <div id="controls">
        🖱️ Left click + drag: Rotate<br>
        🖱️ Right click + drag: Pan<br>
        🖱️ Scroll: Zoom
    </div>
    <script type="importmap">
    {{
        "imports": {{
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
        }}
    }}
    </script>
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 10000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);

        scene.add(new THREE.AmbientLight(0x404040, 2));
        const light1 = new THREE.DirectionalLight(0xffffff, 1);
        light1.position.set(100, 100, 50);
        scene.add(light1);
        const light2 = new THREE.DirectionalLight(0xffffff, 0.5);
        light2.position.set(-100, -100, -50);
        scene.add(light2);

        scene.add(new THREE.GridHelper(200, 20, 0x888888, 0xcccccc));
        scene.add(new THREE.AxesHelper(100));

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        const loader = new STLLoader();
        const stlData = atob('{stl_base64}');
        const stlArray = new Uint8Array(stlData.length);
        for (let i = 0; i < stlData.length; i++) {{
            stlArray[i] = stlData.charCodeAt(i);
        }}

        const geometry = loader.parse(stlArray.buffer);
        const material = new THREE.MeshPhongMaterial({{
            color: 0x4A90D9,
            specular: 0x111111,
            shininess: 200
        }});
        const mesh = new THREE.Mesh(geometry, material);
        geometry.center();
        scene.add(mesh);

        const box = new THREE.Box3().setFromObject(mesh);
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
        cameraZ *= 2;
        camera.position.set(cameraZ, cameraZ, cameraZ);
        camera.lookAt(0, 0, 0);
        controls.update();

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        window.addEventListener('resize', function() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        animate();
    </script>
</body>
</html>
'''

with open(html_file, 'w') as f:
    f.write(html_content)

print(f"✓ Interactive viewer: {html_file}")

print("\n" + "="*60)
print("SUCCESS!")
print("="*60)
print(f"\n✅ Angled awning for rain drainage ({AWNING_ANGLE}° slope)")
print(f"✅ Short sidewalls (cut 1cm below circle top)")
print(f"✅ Open bottom for hand access to lock")
print(f"✅ Back plate with {LOCK_DIAMETER:.1f}mm opening")
print(f"\n📁 Files: {output_file}, {html_file}")
print(f"\n🖨️  Print with back plate flat on bed")
