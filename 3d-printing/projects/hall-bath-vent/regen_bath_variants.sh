#!/bin/bash
# Regenerate all eight hall-bath vent variants from the shared generator.
# There is no bath fork of the CAD: every variant is a -D override set on
# ../nursery-flush-vent/nursery_flush_vent.scad (RENDER_PART="luxe1").
#
# Each override set below was reconstructed from the originally exported
# meshes and re-verified against them with OpenSCAD 2021.01 + trimesh:
# six of the eight regenerate with identical bounding box, triangle count,
# and volume (to 1 mm^3). Exception: the two ROUND parts additionally had
# their edge chamfer continued around the four r8 plate corners by a one-off
# post-process script that was not retained; the meshes from this file
# differ only there (corner arcs unchamfered, +21 mm^3 of 255,626 on the
# printed part).
#
# Exports land next to this script in design orientation (top face at z=0,
# body extending -z). Print top-face-down on textured PEI, PETG.
set -e
cd "$(dirname "$0")"
SCAD="../nursery-flush-vent/nursery_flush_vent.scad"

gen () { out="$1"; shift; openscad -o "$out" -D 'RENDER_PART="luxe1"' "$@" "$SCAD"; echo "wrote $out"; }

# ---- v1 (day 1): drop-in for the measured opening, 8 mm lips -------------
# plate 276 x 128 x 28.5 mm, drop-down skirt exactly 260 x 110
gen bath_vent_260x110.stl -D opening_L=261.5 -D opening_W=112 \
    -D flange_w=8 -D full_end_lip=7.25

# ---- v2 (day 2 am): opening width re-measured, drop-down narrowed 7 mm ---
gen bath_vent_260x103.stl -D opening_L=261.5 -D opening_W=105 \
    -D flange_w=8 -D full_end_lip=7.25

# ---- RMG (day 2 pm): footprint cloned from a commercial flush register ---
# 11.5 x 5.5 in faceplate, 9.75 x 3.75 in drop-down, so 22.2 mm lips.
# The wide lip is what exposed the unchecked-width bug (see README):
# luxe_side_border must cover lip + channel, hence 22.225 + 5.
RMG='-D opening_L=247.65 -D opening_W=95.25 -D end_clear=0 -D side_clear=0'
gen bath_vent_RMG_248x95.stl $RMG \
    -D flange_w=22.225 -D full_end_lip=22.225 -D luxe_side_border=27.225

# ---- thickness ladder (day 3): thinner skin, denser under-spine grid -----
# Stringer pitch retuned per thickness (28 / 9 / 6 mm for 4.5 / 2.0 / 1.6);
# edge chamfers scale down so the rim keeps a 0.8 mm vertical land; magnet
# pockets deleted below 2.8 mm (mag_*=0). Full study with strength table:
# bath_thickness_comparison.html.
GRID20='-D plate_T=2 -D l1_spine_y=[-27,-18,-9,0,9,18,27] -D edge_ch=1.2 -D slot_ch=0.5'
GRID16='-D plate_T=1.6 -D l1_spine_y=[-30,-24,-18,-12,-6,0,6,12,18,24,30] -D edge_ch=0.8 -D slot_ch=0.4'
NOMAG='-D mag_d=0 -D mag_boss_d=0'

gen bath_vent_RMG_ULTRATHIN_248x95.stl $RMG \
    -D flange_w=22.225 -D full_end_lip=22.225 -D luxe_side_border=27.225 $GRID20 $NOMAG

gen bath_vent_RMG_1P6_248x95.stl $RMG \
    -D flange_w=22.225 -D full_end_lip=22.225 -D luxe_side_border=27.225 $GRID16 $NOMAG

# ---- SHORTLIP: faceplate trimmed 5 mm per side (lips 22.2 -> 17.2) -------
# The channel layout is anchored to the duct, not the plate, so it is
# untouched; luxe_side_border shrinks by the same 5.
gen bath_vent_RMG_1P6_SHORTLIP_248x95.stl $RMG \
    -D flange_w=17.225 -D full_end_lip=17.225 -D luxe_side_border=22.225 $GRID16 $NOMAG

# ---- ROUND: outer plate corners r1.5 -> r8 (bbox unchanged) --------------
gen bath_vent_RMG_1P6_SHORTLIP_ROUND_248x95.stl $RMG \
    -D flange_w=17.225 -D full_end_lip=17.225 -D luxe_side_border=22.225 $GRID16 $NOMAG \
    -D corner_r=8

# ---- FINAL (the printed part): ULTRATHIN + SHORTLIP + ROUND --------------
gen bath_vent_RMG_ULTRATHIN_SHORTLIP_ROUND_248x95.stl $RMG \
    -D flange_w=17.225 -D full_end_lip=17.225 -D luxe_side_border=22.225 $GRID20 $NOMAG \
    -D corner_r=8
