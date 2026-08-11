# KUMIKO-MAX - Design Log & Principles

Nursery replacement for the Luxe Single, which proved too constricting in service (~45 cm², 9% of duct). Goal: **maximum airflow at a fixed child-safety opening, best structural support, one-piece 45°-tilted print on the H2D.**

## Final spec (v2, current)

| Parameter | Value | Why |
|---|---|---|
| Opening / drop-down | 350 × 147 / **348.5 × 145** (verified) | same as installed Luxe Single - direct swap |
| Plate | 370 × 171 × 20.5 | 10 mm end lips + 12 mm side lips, all floor-resting |
| Lattice | ±45° bars, **2.4 mm wide × 20 mm deep**, 5.0 mm gaps (pitch 7.4) | see principles below |
| Open area | **~181 cm² = 35% of duct** (46% field porosity) | vs 9% Luxe Single, 27% old kumiko, 32% Fittes slots |
| Ribs / magnets | **none** | lattice is the structure; any diamond is a hook point for removal |
| Print | pre-tilted 45° about the width axis: 266 × 171 × 266 on the bed | part exceeds 350 flat; tilt fits with margin |
| Bar section props | S = 160 mm³, I = 1600 mm⁴ per bar | ×20 strength, ×92 stiffness vs the original 4.5 mm lattice skin |
| Material | PETG | heat/creep + layer adhesion matters in the tilted orientation |
| Render | `nursery_flush_vent.scad`: `RENDER_PART="kumiko" bar_w=2.4 kumiko_depth=20 full_end_lip=10` | fully parametric |

## Design principles (the reusable part)

1. **Airflow scales with total open area, not opening size.** The safety constraint fixes the maximum *gap* (5 mm, toddler finger), not the *porosity*. Many small openings can pass as much air as few large ones: porosity = gap²/(gap+bar)², so the only lever left is bar width. Thinning 3.4 → 2.4 mm took porosity 35% → 46% with zero safety change. (Same logic showed the decorative Ribbon Grille's big 10-15 mm apertures buy nothing but risk: ~35-42% of duct, same band as this lattice.)

2. **Depth is the cheapest strength there is: S ∝ h², I ∝ h³.** A lattice bar deepened 4.5 → 12 → 20 mm goes S = 8 → 58 → 160 mm³ and I = 18 → 346 → 1600 mm⁴. v2's 12→20 step alone bought ×2.8 strength and ×4.6 stiffness for ~40% more lattice plastic - and **zero outer-dimension cost**, because the skirt already made the part 20.5 tall. Rule: before adding members, ask whether existing members can simply grow into unused height.

3. **Deep thin walls need bracing - and a lattice braces itself.** The classic failure of a 2.4 × 20 blade is sideways (lateral-torsional) buckling. Here every bar is crossed and fused every ~10.5 mm by the opposing ±45° family, so each segment is a stocky braced web (h/t ≈ 8). The crossing pattern that makes the kumiko *look* is also what makes deep bars *legal* - ornament and structure are the same feature.

4. **Delete the members the geometry made redundant.** Once the lattice is the beam system, the old cross-ribs added weight, print time, and airflow blockage for nothing - removed. Same for magnets: a lattice is grabbable anywhere (bent paperclip through any diamond), and at the finer 7.4 mm pitch a magnet boss would sit visibly under an open diamond. Features must re-justify themselves after every structural rework.

5. **Know where the gains stop.** Beyond ~20-25 mm depth the bars stop being the weak link; failure relocates to the load handoff (lattice → border plate → downstand → skirt), so more depth is dead weight. Strengthen the *next* link or stop.

6. **Design for the tilt, don't just tilt the design.** At 45° about the width axis: the ±45°-in-plan bar walls land at 60° from horizontal (safely printable); plate top/underside become 45° planes (self-supporting from the bed edge up); only horizontal bottom edges (skirt rims) need slicer support - all on hidden faces. Deeper bars just make the printable walls taller. Trade acknowledged: layer planes cross the bars at 45°, so impact strength leans on PETG layer adhesion - dry filament, 0.2 mm layers, and PETG-over-PLA are structural choices here, not just settings. Visible face will carry uniform ~0.3 mm stair texture; the diamond pattern camouflages it far better than a flat panel would.

7. **Deeper channels are nearly free aerodynamically, and collimate.** At register velocities, entry/exit losses dominate over wall friction, so 12→20 mm channel length costs a few percent at most while the open area is untouched. Side effect: flow exits straighter (less sideways spill - the original complaint about the stamped register) and the deeper diamonds read darker from above, closer to real kumiko shadow.

## Version history

- **v0** (comparison-set kumiko): 3.4 mm bars × 4.5 mm skin + 7 hidden ribs + magnets. 140 cm² (27%).
- **v1** (KUMIKO-MAX): bars 2.4 mm, depth 12, ribs and magnets deleted, full lips, 45° tilt print. 181 cm² (35%). Caught during validation: magnet boss landed under an open diamond at the finer pitch → magnets removed rather than moved (principle 4); the 3-channel Luxe's global `panel_W` assert fired on unrelated renders → made style-scoped.
- **v2** (current): depth 12 → 20 after the "would deeper channels help?" analysis (principles 2, 5, 7). Same footprint, same tilted print size, ×2.8 strength / ×4.6 stiffness. All probes re-passed; drop-down re-verified 348.5 × 145.

## Print & install

Tilted file as exported (no re-orientation). Supports ON (normal, hidden faces only), brim, dry PETG, 0.2 mm, 4 walls. Drop-in like the Luxe Single it replaces; remove by hooking any diamond. Airflow should feel like the Fittes-slot class, not the choked Luxe Single.
