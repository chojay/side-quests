#!/usr/bin/env python3
"""
LG WashTower / LG front-load washer -- Pump-Drain Catch Cup  (v2)
=================================================================
Original parametric design.

v2 (2026-07-09): complete rework after user feedback + reference research.
The drain-pump filter on LG front-loaders / WashTower is a ROUND cylinder
cap (~Ø75 mm).  The proven design pattern (cf. Printables #1536585,
"Ø74 drain bowl" class models) is therefore:

  * a CYLINDRICAL cup that sits below the round filter cap, and
  * a THIN spout tongue that slips into the small gap under the filter
    opening and guides the water into the cup.

Two parts, both printed FLAT with no supports:
  1. cup   - cylinder with an angled socket boss; hose C-clip on the rim
  2. spout - thin trough tongue; its root plate slides into the socket
             (snug fit; add a dab of glue if you want it permanent)

Coordinates: cup axis = Z at origin, floor at Z=0, spout points -Y
(toward the machine).  Units: mm.
"""

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

ENGINE = "manifold"

# ----------------------------------------------------------------------
# PARAMETERS (mm) -- FIT-CRITICAL ones marked [F]; verify on your unit
# ----------------------------------------------------------------------
cap_d          = 75.0   # [F] filter cap diameter (typ. 74-76)
filter_center_h= 110.0  # [F] cap CENTER height from floor
                        #     -> cap bottom = filter_center_h - cap_d/2
cup_od         = 80.0   # cup outer diameter
cup_h          = 62.0   # cup height; rim MUST stay below the cap bottom
wall           = 2.4    # cup wall thickness
floor_t        = 3.0    # cup floor thickness

spout_w        = 40.0   # trough inner width (< cap_d so it fits the gap)
spout_len      = 55.0   # total tongue length (incl. 14 mm socket insert)
spout_floor_t  = 1.7    # [F] tongue thickness -- must fit gap under cap
spout_lip_h    = 7.0    # trough side lip height
spout_tilt_deg = 13.0   # downward slope from tip into the cup
clearance      = 0.25   # socket slide-fit clearance per side

hose_d         = 15.0   # [F] emergency drain hose OD
clip_wall      = 3.0
clip_h         = 15.0
clip_gap       = 9.0    # C-mouth opening (< hose_d -> snap retention)

R  = cup_od / 2.0
Ri = R - wall

def diff(a, b):  return trimesh.boolean.difference([a, b], engine=ENGINE)
def union(parts):return trimesh.boolean.union(parts, engine=ENGINE)
def inter(a, b): return trimesh.boolean.intersection([a, b], engine=ENGINE)
def rotX(deg, point=(0,0,0)):
    return trimesh.transformations.rotation_matrix(np.radians(deg), (1,0,0), point=point)

# ----------------------------------------------------------------------
# PART 1 -- CUP
# ----------------------------------------------------------------------
outer = cylinder(radius=R,  height=cup_h, sections=128)
outer.apply_translation((0, 0, cup_h/2.0))
cav   = cylinder(radius=Ri, height=cup_h, sections=128)
cav.apply_translation((0, 0, floor_t + cup_h/2.0))
cup = diff(outer, cav)

# --- socket boss on the -Y (machine) side ---
# Runs from the bed to just below the rim: a full-height buttress, so it
# prints support-free and stiffens the socket.
boss_w, boss_out = 48.0, 13.0
boss_top = cup_h - 4.0
bb = box(extents=(boss_w, boss_out + wall, boss_top))
bb.apply_translation((0, -(R + boss_out/2.0 - wall/2.0), boss_top/2.0))
cup = union([cup, bb])

# --- angled socket slot, cut through boss AND cup wall ---
slot = box(extents=(spout_w + 2*clearance + 4.0, 70.0, spout_floor_t + 2*clearance))
# slot centreline enters the wall at z_slot and rises toward -Y (the tip)
z_slot = boss_top - 6.0
slot.apply_translation((0, -R, z_slot))          # centre on the wall
slot.apply_transform(rotX(-spout_tilt_deg, point=(0, -R, z_slot)))
# NB: rotX(-tilt) about the wall point makes the -Y end (tip side) HIGHER
cup = diff(cup, slot)
# widen the wall opening upward so water pouring off the tongue clears the rim
mouth = box(extents=(spout_w - 4.0, wall + 6.0, cup_h))
mouth.apply_translation((0, -R + wall/2.0 - 1.0, z_slot + cup_h/2.0))
cup = diff(cup, mouth)

# --- hose C-clip: full-height column INSIDE the cup on the +X side ---
# The emergency hose slides down into the C and drains straight into the
# cup.  Column stands on the cup floor -> prints support-free.
col_h  = cup_h - floor_t
ring_R = hose_d/2.0 + clip_wall
clip_cx = Ri - ring_R + 2.0          # overlap the inner wall by 2 mm to bond
ring_o = cylinder(radius=ring_R,     height=col_h, sections=64)
ring_i = cylinder(radius=hose_d/2.0, height=col_h + 8, sections=64)
zmid = floor_t + col_h/2.0
ring_o.apply_translation((clip_cx, 0, zmid))
ring_i.apply_translation((clip_cx, 0, zmid + 4))   # hole open at top only
clip = diff(ring_o, ring_i)
mouth2 = box(extents=(ring_R + 6.0, clip_gap, col_h + 10))
mouth2.apply_translation((clip_cx - (ring_R + 6.0)/2.0, 0, zmid))  # mouth faces cup centre (-X)
clip = diff(clip, mouth2)
cup = union([cup, clip])

# ----------------------------------------------------------------------
# PART 2 -- SPOUT TONGUE (printed flat, floor on bed)
# ----------------------------------------------------------------------
# Built flat along +Y for printing; slides tip-first into the socket.
insert_len = 20.0   # bare-plate section that slides through boss + wall;
                    # long enough to overhang ~4 mm INSIDE the cup as a
                    # clean drip edge (boss+wall depth = 15.4 mm)
plate = box(extents=(spout_w, spout_len, spout_floor_t))
plate.apply_translation((0, spout_len/2.0, spout_floor_t/2.0))
lipL = box(extents=(2.0, spout_len - insert_len, spout_lip_h))
lipL.apply_translation((-(spout_w/2.0 - 1.0), (spout_len - insert_len)/2.0 + insert_len, spout_lip_h/2.0))
lipR = lipL.copy(); lipR.apply_translation((spout_w - 2.0, 0, 0))
# stop shoulder: abuts the boss face so the tongue can't slide through
stop = box(extents=(spout_w, 2.0, spout_lip_h))
stop.apply_translation((0, insert_len + 1.0, spout_lip_h/2.0))
spout = union([plate, lipL, lipR, stop])

# ----------------------------------------------------------------------
# checks + exports
# ----------------------------------------------------------------------
cap_bottom = filter_center_h - cap_d/2.0
tip_rise   = np.tan(np.radians(spout_tilt_deg)) * (spout_len - 7)
print(f"cap bottom height        : {cap_bottom:.1f} mm")
print(f"cup rim height           : {cup_h:.1f} mm  (must be < cap bottom)")
print(f"spout tip height (fitted): {z_slot + tip_rise:.1f} mm (should sit just under cap bottom)")
for name, m in (("cup", cup), ("spout", spout)):
    m.merge_vertices(); m.fix_normals()
    print(f"{name:6s} watertight={m.is_watertight}  winding={m.is_winding_consistent}"
          f"  bbox={np.round(m.extents,1).tolist()}  vol={m.volume/1000:.1f} cm3")

cup.export("lg_washtower_drain_cup.stl")
spout.export("lg_washtower_drain_spout.stl")

# combined plate: cup at origin, spout laid flat beside it
scene_spout = spout.copy(); scene_spout.apply_translation((cup_od/2.0 + 40.0, -20.0, 0))
combo = trimesh.util.concatenate([cup, scene_spout])
combo.export("lg_washtower_drain_bucket.stl")
combo.export("lg_washtower_drain_bucket.3mf")
print("exports written")
