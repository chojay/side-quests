#!/usr/bin/env python3
"""
Kumiko-Style Air Vent Cover - SPLIT VERSION with DOVETAIL EDGE JOINTS
For 10" x 4" duct opening - divided along width for printability
Design converted from OpenSCAD to Python using manifold3d

VERSION 2.1 CHANGES (2025-12-01):
=================================
1. Z-PROFILE (DROP-DOWN) SHRUNK BY 1mm ON EACH EDGE
2. OUTER FRAME EXPANDED TO 1-INCH (25.4mm) BORDER
3. HOOK DEPTH (DROP-DOWN) INCREASED TO 1 INCH (25.4mm)
4. KUMIKO PATTERN EXPANDED to cover half the frame width
   - Pattern now extends 12.7mm into frame border on each side
   - Solid frame border reduced from 25.4mm to 12.7mm
5. DOVETAILS MOVED TO Z-PROFILE HOOK LOCATIONS
   - Dovetails now at Y positions where Z-profile hooks exist
   - Hooks widened at split position to accommodate dovetails (10mm pads)
   - Full 25.4mm depth engagement for strong joints
   - Left pads end AT split_position, keys protrude beyond
   - Solid face plate backing at dovetail locations prevents pattern overlap
   - Right face plate has dovetail sockets cut through

Usage:
    python3 kumiko_vent_10x4_split_DOVETAIL_EDGE_v2.py --piece left
    python3 kumiko_vent_10x4_split_DOVETAIL_EDGE_v2.py --piece right
    python3 kumiko_vent_10x4_split_DOVETAIL_EDGE_v2.py --piece both

Output: STL files in the same directory
"""

import argparse
import math
from pathlib import Path
import manifold3d as mf
import numpy as np

# ====================
# PARAMETERS
# ====================

# Duct Opening Dimensions
duct_width = 254  # 10 inches in mm
duct_height = 101.6  # 4 inches in mm

# Frame Parameters
overhang = 25.4  # 1 inch frame border beyond duct
face_thickness = 2.5  # mm

# Pattern extension into frame (half of overhang = 12.7mm)
pattern_extension = overhang / 2  # 12.7mm - pattern extends into frame
solid_frame_width = overhang - pattern_extension  # 12.7mm solid border remains

# Kumiko Pattern Parameters - Asanoha Style
hex_radius = 4  # mm
bar_width = 1.0  # mm

# Z-Profile Mount Parameters
lip_depth = 4  # mm
hook_depth = 25.4  # 1 inch drop-down depth
hook_thickness = 2  # mm
fit_clearance = 0.5  # mm
z_profile_inset = 1  # Additional inset to shrink drop-down perimeter (mm)

# Dovetail pad dimensions (widened area on hooks for dovetail joints)
dovetail_pad_width = 10  # Width of widened pad on hooks (mm)

# Tab-and-Slot Joint Parameters (Center)
split_position = 152.4  # Center of outer_width (304.8 / 2)
tab_count = 5
tab_width = 8  # mm
tab_depth = 2  # mm
barb_height = 0.3  # mm
barb_position = 1.5  # mm
slot_clearance = 0.1  # mm
chamfer_size = 0.5  # mm

# Dovetail Joint Parameters
dovetail_length = 4  # How far dovetail protrudes in X (mm)
dovetail_narrow = 3  # Width at narrow end (mm)
dovetail_wide = 5  # Width at wide end (mm)
dovetail_clearance = 0.15  # mm

# Explode distance
explode_distance = 15  # mm

# ====================
# CALCULATED DIMENSIONS
# ====================

outer_width = duct_width + (2 * overhang)
outer_height = duct_height + (2 * overhang)

# Extended pattern dimensions (pattern now extends into frame)
extended_pattern_width = duct_width + (2 * pattern_extension)
extended_pattern_height = duct_height + (2 * pattern_extension)

# Z-profile mount dimensions
mount_width = duct_width - (2 * fit_clearance) - (2 * z_profile_inset)
mount_height = duct_height - (2 * fit_clearance) - (2 * z_profile_inset)

# Hook offset from outer edge
hook_offset = overhang - lip_depth + z_profile_inset

# Dovetail Y positions - AT THE Z-PROFILE HOOKS (where deep material exists)
dovetail_top_y = hook_offset + dovetail_pad_width / 2  # Center of widened pad
dovetail_bottom_y = outer_height - hook_offset - dovetail_pad_width / 2

# Dovetail taper
dovetail_taper = (dovetail_wide - dovetail_narrow) / 2

# Tab positions along height
tab_positions = [
    outer_height * 0.20,
    outer_height * 0.35,
    outer_height * 0.50,
    outer_height * 0.65,
    outer_height * 0.80
]

# Connector width
connector_width = 4  # mm


def cube(size_x, size_y, size_z):
    """Create a box at origin."""
    return mf.Manifold.cube([size_x, size_y, size_z])


def translate(manifold, x, y, z):
    """Translate a manifold."""
    return manifold.translate([x, y, z])


def rotate_z(manifold, angle_deg):
    """Rotate around Z axis."""
    return manifold.rotate([0, 0, angle_deg])


# ====================
# KUMIKO PATTERN (EXTENDED)
# ====================

def asanoha_star():
    """Create a single asanoha star pattern element."""
    bars = []
    for angle in range(0, 360, 60):
        bar = cube(hex_radius, bar_width, face_thickness)
        bar = translate(bar, -hex_radius/2, -bar_width/2, 0)
        bar = translate(bar, hex_radius/2, 0, 0)
        bar = rotate_z(bar, angle)
        bars.append(bar)

    result = bars[0]
    for bar in bars[1:]:
        result = result + bar
    return result


def asanoha_pattern_extended():
    """Create the full asanoha pattern for extended area."""
    h_spacing = hex_radius * math.sqrt(3)
    v_spacing = hex_radius * 1.5

    stars = []
    for row in range(-2, int(extended_pattern_height / v_spacing) + 5):
        for col in range(-2, int(extended_pattern_width / h_spacing) + 5):
            x_offset = 0 if row % 2 == 0 else h_spacing / 2
            x_pos = col * h_spacing + x_offset - h_spacing
            y_pos = row * v_spacing - v_spacing

            star = asanoha_star()
            star = translate(star, x_pos, y_pos, 0)
            stars.append(star)

    # Batch union for performance
    result = mf.Manifold.batch_boolean(stars, mf.OpType.Add)
    return result


def extended_kumiko_pattern():
    """Create kumiko pattern clipped to extended opening."""
    pattern = asanoha_pattern_extended()
    clip_box = cube(extended_pattern_width, extended_pattern_height, face_thickness)
    return pattern ^ clip_box  # Intersection


# ====================
# FRAME CONNECTORS
# ====================

def frame_connector_left_piece():
    """Frame-to-pattern connectors for left piece at new boundary."""
    boundary = solid_frame_width
    parts = []

    # LEFT edge vertical bar
    bar1 = cube(connector_width, extended_pattern_height + connector_width, face_thickness)
    bar1 = translate(bar1, boundary - connector_width/2, boundary - connector_width/2, 0)
    parts.append(bar1)

    # BOTTOM edge horizontal bar (left portion)
    bar2 = cube(split_position - boundary + connector_width, connector_width, face_thickness)
    bar2 = translate(bar2, boundary - connector_width/2, boundary - connector_width/2, 0)
    parts.append(bar2)

    # TOP edge horizontal bar (left portion)
    bar3 = cube(split_position - boundary + connector_width, connector_width, face_thickness)
    bar3 = translate(bar3, boundary - connector_width/2, boundary + extended_pattern_height - connector_width/2, 0)
    parts.append(bar3)

    result = parts[0]
    for p in parts[1:]:
        result = result + p
    return result


def frame_connector_right_piece():
    """Frame-to-pattern connectors for right piece."""
    boundary = solid_frame_width
    parts = []

    # RIGHT edge vertical bar
    bar1 = cube(connector_width, extended_pattern_height + connector_width, face_thickness)
    bar1 = translate(bar1, outer_width - boundary - connector_width/2, boundary - connector_width/2, 0)
    parts.append(bar1)

    # BOTTOM edge horizontal bar (right portion)
    bar2 = cube(outer_width - split_position - boundary + connector_width, connector_width, face_thickness)
    bar2 = translate(bar2, split_position - connector_width/2, boundary - connector_width/2, 0)
    parts.append(bar2)

    # TOP edge horizontal bar (right portion)
    bar3 = cube(outer_width - split_position - boundary + connector_width, connector_width, face_thickness)
    bar3 = translate(bar3, split_position - connector_width/2, boundary + extended_pattern_height - connector_width/2, 0)
    parts.append(bar3)

    result = parts[0]
    for p in parts[1:]:
        result = result + p
    return result


# ====================
# DOVETAIL JOINTS (at Z-profile hook locations)
# ====================

def dovetail_key_3d():
    """Create a 3D dovetail key (male) - extends through full Z-profile depth."""
    points = np.array([
        [0, 0],
        [dovetail_length, -dovetail_taper],
        [dovetail_length, dovetail_narrow + dovetail_taper],
        [0, dovetail_narrow]
    ], dtype=np.float64)

    cross_section = mf.CrossSection([points])
    return mf.Manifold.extrude(cross_section, hook_depth + face_thickness)


def dovetail_socket_3d():
    """Create a 3D dovetail socket (female) with clearance."""
    offset = dovetail_clearance
    points = np.array([
        [-0.1, -offset],
        [dovetail_length + 0.1, -dovetail_taper - offset],
        [dovetail_length + 0.1, dovetail_narrow + dovetail_taper + offset],
        [-0.1, dovetail_narrow + offset]
    ], dtype=np.float64)

    cross_section = mf.CrossSection([points])
    return mf.Manifold.extrude(cross_section, hook_depth + face_thickness + 0.2)


def top_dovetail_key():
    """Dovetail key at TOP hook location."""
    key = dovetail_key_3d()
    return translate(key, split_position, dovetail_top_y - dovetail_narrow/2, -hook_depth)


def bottom_dovetail_key():
    """Dovetail key at BOTTOM hook location."""
    key = dovetail_key_3d()
    return translate(key, split_position, dovetail_bottom_y - dovetail_narrow/2, -hook_depth)


def top_dovetail_socket():
    """Dovetail socket at TOP hook location."""
    socket = dovetail_socket_3d()
    return translate(socket, split_position, dovetail_top_y - dovetail_narrow/2, -hook_depth - 0.1)


def bottom_dovetail_socket():
    """Dovetail socket at BOTTOM hook location."""
    socket = dovetail_socket_3d()
    return translate(socket, split_position, dovetail_bottom_y - dovetail_narrow/2, -hook_depth - 0.1)


# ====================
# TAB-AND-SLOT JOINTS
# ====================

def single_tab():
    """Create a single tab with barb."""
    tab = cube(tab_depth, tab_width, face_thickness)
    tab = translate(tab, 0, -tab_width/2, 0)

    barb = cube(barb_height, tab_width, face_thickness)
    barb = translate(barb, barb_position, -tab_width/2, 0)

    result = tab + barb

    chamfer1 = cube(chamfer_size * 2, chamfer_size * 2, face_thickness + 0.2)
    chamfer1 = rotate_z(chamfer1, 45)
    chamfer1 = translate(chamfer1, tab_depth - chamfer_size/2, -tab_width/2 - chamfer_size, -0.1)

    chamfer2 = cube(chamfer_size * 2, chamfer_size * 2, face_thickness + 0.2)
    chamfer2 = rotate_z(chamfer2, 45)
    chamfer2 = translate(chamfer2, tab_depth - chamfer_size/2, tab_width/2 + chamfer_size, -0.1)

    result = result - chamfer1 - chamfer2
    return result


def all_tabs():
    """Create all tabs at split position."""
    tabs = []
    for pos in tab_positions:
        tab = single_tab()
        tab = translate(tab, split_position, pos, 0)
        tabs.append(tab)
    return mf.Manifold.batch_boolean(tabs, mf.OpType.Add)


def single_slot():
    """Create a single slot for tab."""
    slot_width_total = tab_width + (2 * slot_clearance)
    slot_depth_total = tab_depth + 0.2

    slot = cube(slot_depth_total, slot_width_total, face_thickness + 0.1)
    slot = translate(slot, 0, -slot_width_total/2, -0.05)

    barb_slot = cube(barb_height + 0.05, slot_width_total, face_thickness + 0.1)
    barb_slot = translate(barb_slot, barb_position, -slot_width_total/2, -0.05)

    entry = cube(chamfer_size + 0.1, slot_width_total + 2*chamfer_size, face_thickness + 2*chamfer_size)
    entry = translate(entry, -0.1, -slot_width_total/2 - chamfer_size, -chamfer_size)

    return slot + barb_slot + entry


def all_slots():
    """Create all slots at split position."""
    slots = []
    for pos in tab_positions:
        slot = single_slot()
        slot = translate(slot, split_position, pos, 0)
        slots.append(slot)
    return mf.Manifold.batch_boolean(slots, mf.OpType.Add)


# ====================
# FACE PLATES
# ====================

def left_face_plate():
    """Create the left half face plate with extended pattern."""
    print("  Creating left frame...")
    boundary = solid_frame_width

    # Solid left frame
    frame = cube(split_position, outer_height, face_thickness)

    # Subtract extended inner opening (where pattern goes)
    opening = cube(split_position - boundary, extended_pattern_height, face_thickness + 0.2)
    opening = translate(opening, boundary, boundary, -0.1)
    frame = frame - opening

    print("  Creating extended kumiko pattern...")
    # Add extended kumiko pattern in the opening
    pattern = extended_kumiko_pattern()
    clip = cube(split_position - boundary, extended_pattern_height, face_thickness)
    pattern = pattern ^ clip
    pattern = translate(pattern, boundary, boundary, 0)

    # Add SOLID face plate regions at dovetail pad locations (prevents pattern overlap)
    print("  Adding solid backing at dovetail locations...")
    top_backing = cube(dovetail_length * 2 + 4, dovetail_pad_width, face_thickness)
    top_backing = translate(top_backing, split_position - dovetail_length * 2 - 2, hook_offset, 0)

    bottom_backing = cube(dovetail_length * 2 + 4, dovetail_pad_width, face_thickness)
    bottom_backing = translate(bottom_backing, split_position - dovetail_length * 2 - 2,
                               outer_height - hook_offset - dovetail_pad_width, 0)

    print("  Adding connectors...")
    connectors = frame_connector_left_piece()

    print("  Adding tabs...")
    tabs = all_tabs()

    return frame + pattern + top_backing + bottom_backing + connectors + tabs


def right_face_plate():
    """Create the right half face plate with extended pattern and socket cutouts."""
    print("  Creating right frame...")
    boundary = solid_frame_width

    # Solid right frame
    frame = cube(outer_width - split_position, outer_height, face_thickness)
    frame = translate(frame, split_position, 0, 0)

    # Subtract extended inner opening
    opening = cube(outer_width - split_position - boundary, extended_pattern_height, face_thickness + 0.2)
    opening = translate(opening, split_position, boundary, -0.1)
    frame = frame - opening

    # Subtract center slots
    print("  Subtracting slots...")
    slots = all_slots()
    frame = frame - slots

    print("  Creating extended kumiko pattern...")
    # Add extended kumiko pattern
    pattern = extended_kumiko_pattern()
    clip = cube(outer_width - split_position, extended_pattern_height, face_thickness)
    clip = translate(clip, split_position - boundary, 0, 0)
    pattern = pattern ^ clip
    pattern = translate(pattern, boundary, boundary, 0)

    # Add SOLID face plate regions at dovetail pad locations
    print("  Adding solid backing at dovetail locations...")
    top_backing = cube(dovetail_length * 2 + 2, dovetail_pad_width, face_thickness)
    top_backing = translate(top_backing, split_position, hook_offset, 0)

    bottom_backing = cube(dovetail_length * 2 + 2, dovetail_pad_width, face_thickness)
    bottom_backing = translate(bottom_backing, split_position,
                               outer_height - hook_offset - dovetail_pad_width, 0)

    print("  Adding connectors...")
    connectors = frame_connector_right_piece()

    # Combine everything
    result = frame + pattern + top_backing + bottom_backing + connectors

    # Cut dovetail socket shapes through the face plate so keys can slide in
    print("  Cutting dovetail sockets through face plate...")
    result = result - top_dovetail_socket()
    result = result - bottom_dovetail_socket()

    return result


# ====================
# Z-PROFILE MOUNTS
# ====================

def left_z_profile():
    """Create Z-profile mount for left piece with widened pads."""
    parts = []

    # Left edge hook (FULL height)
    hook1 = cube(hook_thickness, mount_height + (2 * lip_depth), hook_depth)
    hook1 = translate(hook1, hook_offset, hook_offset, -hook_depth + face_thickness)
    parts.append(hook1)

    # Top edge hook (goes to split_position, key protrudes beyond)
    hook2 = cube(split_position - hook_offset, hook_thickness, hook_depth)
    hook2 = translate(hook2, hook_offset, hook_offset, -hook_depth + face_thickness)
    parts.append(hook2)

    # Widened pad at split position for TOP dovetail (ends AT split_position)
    pad_top = cube(dovetail_length * 2, dovetail_pad_width, hook_depth)
    pad_top = translate(pad_top, split_position - dovetail_length * 2, hook_offset, -hook_depth + face_thickness)
    parts.append(pad_top)

    # Bottom edge hook
    hook3 = cube(split_position - hook_offset, hook_thickness, hook_depth)
    hook3 = translate(hook3, hook_offset, outer_height - hook_offset - hook_thickness, -hook_depth + face_thickness)
    parts.append(hook3)

    # Widened pad at split position for BOTTOM dovetail (ends AT split_position)
    pad_bottom = cube(dovetail_length * 2, dovetail_pad_width, hook_depth)
    pad_bottom = translate(pad_bottom, split_position - dovetail_length * 2,
                           outer_height - hook_offset - dovetail_pad_width, -hook_depth + face_thickness)
    parts.append(pad_bottom)

    result = mf.Manifold.batch_boolean(parts, mf.OpType.Add)

    # Add dovetail keys (they protrude beyond split_position)
    result = result + top_dovetail_key()
    result = result + bottom_dovetail_key()

    return result


def right_z_profile():
    """Create Z-profile mount for right piece with dovetail sockets."""
    parts = []

    # Right edge hook (FULL height)
    hook1 = cube(hook_thickness, mount_height + (2 * lip_depth), hook_depth)
    hook1 = translate(hook1, outer_width - hook_offset - hook_thickness, hook_offset, -hook_depth + face_thickness)
    parts.append(hook1)

    # Top edge hook (regular thin portion starts after pad area)
    hook2 = cube(outer_width - split_position - dovetail_length * 2 - hook_offset, hook_thickness, hook_depth)
    hook2 = translate(hook2, split_position + dovetail_length * 2, hook_offset, -hook_depth + face_thickness)
    parts.append(hook2)

    # Widened pad at split position for TOP socket
    pad_top = cube(dovetail_length * 2, dovetail_pad_width, hook_depth)
    pad_top = translate(pad_top, split_position, hook_offset, -hook_depth + face_thickness)
    parts.append(pad_top)

    # Bottom edge hook (regular thin portion)
    hook3 = cube(outer_width - split_position - dovetail_length * 2 - hook_offset, hook_thickness, hook_depth)
    hook3 = translate(hook3, split_position + dovetail_length * 2, outer_height - hook_offset - hook_thickness,
                      -hook_depth + face_thickness)
    parts.append(hook3)

    # Widened pad at split position for BOTTOM socket
    pad_bottom = cube(dovetail_length * 2, dovetail_pad_width, hook_depth)
    pad_bottom = translate(pad_bottom, split_position, outer_height - hook_offset - dovetail_pad_width,
                           -hook_depth + face_thickness)
    parts.append(pad_bottom)

    result = mf.Manifold.batch_boolean(parts, mf.OpType.Add)

    # Subtract dovetail sockets from the widened pads
    result = result - top_dovetail_socket()
    result = result - bottom_dovetail_socket()

    return result


# ====================
# COMPLETE ASSEMBLIES
# ====================

def kumiko_vent_left_half():
    """Complete left half assembly."""
    print("Building left face plate...")
    face = left_face_plate()
    print("Building left Z-profile...")
    z_profile = left_z_profile()
    return face + z_profile


def kumiko_vent_right_half():
    """Complete right half assembly."""
    print("Building right face plate...")
    face = right_face_plate()
    print("Building right Z-profile...")
    z_profile = right_z_profile()
    return face + z_profile


def export_stl(manifold, filename):
    """Export manifold to STL file."""
    mesh = manifold.to_mesh()
    verts = mesh.vert_properties
    tris = mesh.tri_verts

    import trimesh
    trimesh_mesh = trimesh.Trimesh(vertices=verts[:, :3], faces=tris)
    trimesh_mesh.export(filename)
    print(f"Exported: {filename}")


def main():
    parser = argparse.ArgumentParser(description='Generate Kumiko vent cover STL files (v2.1)')
    parser.add_argument('--piece', choices=['left', 'right', 'both', 'exploded'],
                        default='both', help='Which piece(s) to generate')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: same as script)')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    output_dir = Path(args.output_dir) if args.output_dir else script_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== Kumiko Vent Cover v2.1 ===")
    print(f"Outer dimensions: {outer_width:.1f}mm × {outer_height:.1f}mm")
    print(f"Frame border: {overhang:.1f}mm (1 inch)")
    print(f"Solid frame: {solid_frame_width:.1f}mm")
    print(f"Pattern extension: {pattern_extension:.1f}mm into frame")
    print(f"Hook depth (drop-down): {hook_depth:.1f}mm (1 inch)")
    print(f"Dovetail positions: Y={dovetail_top_y:.1f}mm (top), Y={dovetail_bottom_y:.1f}mm (bottom)")

    if args.piece == 'left':
        print("\n=== Generating LEFT half ===")
        left = kumiko_vent_left_half()
        export_stl(left, output_dir / "kumiko_vent_10x4_DOVETAIL_EDGE_v2_LEFT.stl")

    elif args.piece == 'right':
        print("\n=== Generating RIGHT half ===")
        right = kumiko_vent_right_half()
        export_stl(right, output_dir / "kumiko_vent_10x4_DOVETAIL_EDGE_v2_RIGHT.stl")

    elif args.piece == 'both':
        print("\n=== Generating BOTH halves ===")
        print("\n--- Left half ---")
        left = kumiko_vent_left_half()
        export_stl(left, output_dir / "kumiko_vent_10x4_DOVETAIL_EDGE_v2_LEFT.stl")

        print("\n--- Right half ---")
        right = kumiko_vent_right_half()
        export_stl(right, output_dir / "kumiko_vent_10x4_DOVETAIL_EDGE_v2_RIGHT.stl")

        # Also export combined for visualization
        print("\n--- Combined assembly ---")
        combined = left + right
        export_stl(combined, output_dir / "kumiko_vent_10x4_DOVETAIL_EDGE_v2_COMBINED.stl")

    elif args.piece == 'exploded':
        print("\n=== Generating EXPLODED view ===")
        left = kumiko_vent_left_half()
        left = translate(left, -explode_distance, 0, 0)

        right = kumiko_vent_right_half()
        right = translate(right, explode_distance, 0, 0)

        exploded = left + right
        export_stl(exploded, output_dir / "kumiko_vent_10x4_DOVETAIL_EDGE_v2_EXPLODED.stl")

    print("\nDone!")


if __name__ == "__main__":
    main()
