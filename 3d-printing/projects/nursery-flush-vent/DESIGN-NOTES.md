# Nursery Flush Drop-In Floor Vent - Design Notes

Fittes-inspired flush, minimalist floor register for a nursery, replacing a stamped register whose openings were a finger-entrapment risk for small children. Three visual styles built on one shared body: **Fittes** (lengthwise slots), **Kumiko** (Japandi 45° diamond lattice), and **Luxe frameless** (nested parallel channels, after the Fittes wall-vent look). Original design - inspired by the Fittes Flush Vent and the VentForge parametric concept, no third-party files used (VentForge download is login-gated on MakerWorld; same license lesson as the [toe-kick vent](../toekick-vent-slider/)).

## Measurements (user-supplied)

- Opening: **350 × 147 mm**, near a wall - 50 mm from opening edge to wall on one width edge (up to 5 cm wingspan available there if ever needed; not used).
- Depth unconstrained. Heater supply → **PETG**.

## Core design principles

1. **Drop-in retention, no fasteners.** A 16 mm skirt (2.4 mm walls) drops inside the opening and registers the cover laterally; gravity holds it down. Skirt clearance 0.75 mm/end, 1.0 mm/side; 1.2 mm lead-in chamfer on the skirt's bottom edge for easy insertion.
2. **Child safety drives every opening: ≤ 5 mm.** Slots are 5.0 mm, kumiko gaps 5.0 mm perpendicular - well under toddler finger size (~8-10 mm), nothing to catch. Slot top edges get 0.7 mm chamfers so they're soft to the touch. Enforced with an `assert` in the .scad.
3. **One-piece on the H2D via asymmetric flange.** A flange on all four sides needs ~374 mm - over the 350 mm bed. Instead: **12 mm flanges on the two LONG edges only** (they run the full length, so they alone carry all load), ends sit flush *inside* the opening with a ~0.75 mm hairline gap. Total part: **348.5 × 171 × 20.5 mm** - fits flat.
4. **Furniture-proof:** 4.5 mm top plate + 7 hidden cross-ribs (2.4 × 9 mm, fused into the skirt walls) every ~40.6 mm. A single 8 mm slat between ribs takes ~19 kg point load at PETG flexural strength before yield, and real loads spread across several slats + ribs. Kumiko's lattice is additionally self-bracing.
5. **Print orientation as design input:** printed **top face down** on textured PEI → the visible face gets the uniform plate texture (a lesson from the [toe-kick vent](../toekick-vent-slider/)). Consequence: every top-side decorative edge must be a **45° chamfer**, never a shallow bevel (see mistake #3). Everything else (skirt, ribs, magnet bosses) grows upward - zero supports.
6. **Invisible removal features.** Two options, both invisible from above:
   - **Magnet pockets** (both styles): two Ø8.4 × ~4 mm blind pockets under the plate at x = ±60, opening downward, ceiling only 1.2 mm below the top surface → strong pull for a magnet-on-a-stick. Glue 8×3 discs in.
   - **Lift key** (Fittes style): flat 3 mm printed key; blade slips into a slot beside a cross-rib, its 7 mm foot slides under the rib, lift. (The key can't pass the kumiko diamonds - use magnets or a suction cup there.)
7. **Visual parity for comparison:** both styles share the same pattern field (324.5 × 122 mm), border, flange, and body - only the pattern differs, so the choice is purely aesthetic + airflow.

## The four styles

| | Fittes (slots) | Kumiko (lattice) | Luxe 3-channel | Luxe single |
|---|---|---|---|---|
| Pattern | 10 lengthwise 5 mm slots / 8 mm slats | ±45° bars 3.4 mm, 5 mm gaps | 3 nested 5 mm channels (panel + 2 rings) | ONE floating panel, one 5 mm channel |
| Free area | ~162 cm² (~32% of duct) | ~140 cm² (~27%) | ~114 cm² (~22%) | **~45 cm² (~9%) - most restrictive** |
| Structure | plate + 7 ribs | lattice self-bracing + 7 ribs | hidden spines → deep ribs | hidden spine loop + 3 longitudinals → deep ribs |
| Look | continuous minimal lines | Japandi rhythm, diamond shadows | nested-frame frameless | purest frameless - a single shadow rectangle |
| Removal | lift key or magnets | magnets / suction cup | lift key or magnets | lift key or magnets |

**Luxe single v3 - lowered supports + added structure.** I moved the support connections from 14.5 mm down to a grid whose top is **24 mm below the surface** (deeper 24 mm skirt, total height 28.5): sightline cutoff tightens from ~19° to **atan(5/24) ≈ 12°** - you'd have to stand directly over the channel and look straight down to catch a crossing, and at that depth it's in near-total shadow. The trade of "out of the visible path → add more structure" is taken literally: instead of 9 cross-ribs there is now a **bidirectional grid** - 13 cross members (7 main + 3 mid-span pairs + loop-end pair) × 5 longitudinal stringers, each stringer aligned exactly under a spine wall so every grid line is supported for printing and every spine lands on a grid line for stiffness. Verified: 528-point sweep, channel projection empty from the surface to −23.5. Install note: the skirt now reaches ~24 mm below the floor surface - check the duct for a damper/obstruction at that depth; `l1_skirt_depth` scales it down if needed.

**Luxe single airflow warning:** one 5 mm loop is a quarter of the slot version's free area. Expect higher outlet velocity and possibly audible flow with the heater on full; fine if this register can afford to be partly decorative (door gap / other supply paths), risky if it's the room's only supply. The 3-channel Luxe is the airflow-safe frameless choice. If it whistles, `luxe_gap` can go to 6-7 later (once the child is older) - that alone takes single-channel to ~54-63 cm².

### Luxe frameless - how the mechanism translated

The real Fittes frameless vent is a **floating tray** held in a recessed steel frame, with air exiting around its perimeter. I kept only the *parallel-openings principle*: instead of a removable tray (which a toddler could pry out, and which needed pins + wider 9-12 mm gaps), the panel and rings are **fused into one printed piece**, channels held at the same child-safe 5 mm. Three nested channels recover the airflow a single 5 mm perimeter gap would lose (1 channel ≈ 44 cm² → 3 channels ≈ 114 cm²).

**Hidden understructure (v2).** v1 ran the standard cross-ribs at the plate underside - their tops sat 4.5 mm down inside the channels, visible as bridges from almost any angle (`atan(5/4.5)` ≈ 48° sightline cone). I made the support invisible: the zone directly under every channel is kept **completely empty from the surface down to 14.5 mm**. Each island carries its loads through **spine walls hidden under its own solid face** (loops under the two ring-band centerlines - their end segments landing exactly on the extra ribs - plus 3 longitudinal spines under the panel), which guide down to **deep cross-ribs whose tops are 14.5 mm below the surface**. Sightline into a 5 mm channel is cut off beyond `atan(5/14.5)` ≈ 19° from vertical, so the channels read as continuous dark shadow lines, like the powder-coated original. Verified by a 1,476-point containment sweep along every channel projection at z = −6/−10/−14: zero obstructions. Print note: in the flipped print orientation the deep ribs' first layer bridges up to ~23 mm between spine walls - routine PETG bridging, and the (slightly saggy) bridge underside is the face 14.5 mm down that nobody can see.

Airflow note: both are more restrictive than a stamped register (typical ~50-60%). Fine for a bedroom supply; if the room runs cold or the register whistles, bump `slot_w`→pattern regenerates (but keep ≤ 5 mm while the child is small), or drop `slat_w` to 7 / `bar_w` to 3.0.

## Two-part joinery v2 - four-level interlock (all six two-part variants)

The original two-part joint was surface-level: dovetails in the top plate + glued butt faces. Per the joint analysis done for the 14×20 (from the joint analysis done for the companion 14x20 vent): a plate-level dovetail locks in-plane pull-apart but contributes nothing to vertical shear or bending - the loads a floor part actually sees. v2 interlocks at **every depth level**, all engaging with one vertical drop, all invisible from above:

| Level | Feature | What it carries |
|---|---|---|
| L0 plate | **45° scarf** (1.0 mm lands + 2.5 mm ramp through the 4.5 plate) | vertical step shear in direct *bearing*, +glue area |
| L0 border | full-thickness dovetails at y=±77 (unchanged) | in-plane pull-apart, assembly registration |
| L1 skirt | **vertical dovetail keys** in both skirt side walls (z −7 to bottom; outer face flush so the skirt still fits the opening, head flares *inward* 3 mm) | deep pull-apart + shear lock across the full skirt depth |
| L2 ribs | **interdigitated finger combs** on the doubled seam ribs (fingers at y=−48/+14 on A, −14/+48 on B, 12 mm wide, seating in sockets cut from the mating rib) | shear + torsional coupling at the deepest structural level, 3-sided glue pockets |

Style-aware depths: comb fingers ride at the seam-rib level of each style (−5…−13.5 slot/kumiko, −15.5…−20.5 luxe, −24…−28.5 luxe single); skirt keys always run from 7 mm below the surface to the part bottom. Assembly unchanged: drop together face-down, CA on all mating faces. Dry-fit is now stable enough to handle; glued, the joint engages in bearing before any adhesive is stressed.

Print notes: the scarf faces are 45° (clean both sides); skirt key tabs and comb fingers form small 2.4 mm-wide horizontal shelves at their print-underside where they cross the seam - 3-6 mm micro-overhangs that print acceptably and are fully hidden.

## One-piece vs. two-part (both provided, every style)

The one-piece prints are 348.5 mm on a 350 mm bed - technically fits, but only 0.75 mm margin per end: no brim/skirt room, and a full-bed PETG plate has real warp/adhesion risk. So every style also ships as a **two-part version** (`two-print/` folder):

- Split at mid-length; each half is **187 mm** on the bed (194 with tabs) - comfortable margins, brim allowed.
- Joined by **two full-thickness dovetail keys** (8 mm neck / 12 mm head / 7 mm deep, 0.2 mm clearance) placed at y=±77 in the border zone, which is solid in all three styles. Full-thickness tabs print flat on the bed (a partial-depth "hidden" tab would be a mid-air shelf in top-face-down orientation); the visible dovetail on the border reads as a joinery detail.
- The center rib is replaced by a **doubled seam rib** (one per half, straddling the joint) so the seam edge is supported against furniture loads. 0.1 mm butt clearance at the seam faces.
- Bonus: with the bed constraint gone, the two-part body gets the **full perimeter flange back** - assembled 374 × 171, uniform ~24.5 mm visible border all around, more forgiving of a rough opening.
- Assemble face-down on a flat surface: drop the dovetails together, run CA glue along the seam and tabs (Floor_Vents pattern), then install.

Trade-off summary: one-piece = no seam, flush ends, riskier print; two-part = symmetric full border, easy safe prints, one hairline seam + visible dovetails.

## Approach / workflow (what changed vs. the [toe-kick vent](../toekick-vent-slider/))

- **OpenSCAD is installable in the cloud sandbox** (`apt-get install openscad` worked - unlike the earlier no-root sandbox). So this time the **.scad is the tested source of truth**, rendered headlessly via CLI (`openscad -o out.stl -D 'RENDER_PART="fittes"'`). No more "untested-by-render .scad" caveat.
- Validation stays in Python/trimesh (`validate_and_export.py`): watertight check, **19/10/6-point containment truth tables** (slot open, slat solid, rib bridges slot, chamfers removed, pocket cavity + 1.2 mm cover, skirt walls/duct), envelope asserts (≤ 350×320 bed, skirt ≤ opening −1 mm), then export **pre-rotated print-orientation STL + 3MF**.
- Previews: matplotlib orthographic PNGs incl. a **print-orientation render** (playbook rule: eyeball what touches the bed) + a three.js HTML viewer with both styles dropped into a wood floor with the actual opening.

## Gotchas, mistakes & fixes

1. **The 45° XY-diagonal myth.** Hoped a 374 × 171 part could print diagonally on the 350 × 320 bed. It can't: rotated bounding width = `374·cosθ + 171·sinθ`, which is *minimal at θ=0* and grows with rotation for a part this wide. Diagonal placement only rescues long *thin* parts (e.g. 450 × 20 fits at ~42°). Rule of thumb: if the part is wider than ~`(bed_diag − length)`, rotation won't save you - change the design instead (asymmetric flange did it here).
2. **Z-45° tilt rejected.** Tilting the plate 45° shortens the footprint (374→~264) but puts stair-stepped layer lines across the one surface everyone sees, needs a support forest, and weakens the slats along layer planes. Surface-critical flat parts want to lie flat.
3. **Top-face-down inverts overhang logic for TOP features.** The first flange edge idea was a shallow ~18° trip-safe ramp - printed top-down that becomes a ~72°-from-vertical overhang right at the bed and will droop. Fixed: 2 mm 45° chamfer (and 0.7 mm 45° slot chamfers). When the show face is the first layer, *every* top-side bevel must obey the 45° rule in the flipped orientation.
4. **Validation probes must be derived, not eyeballed.** Two "failures" were probe bugs, not geometry: (a) probed "empty duct" at x=0 - but rib #4 sits *exactly* at x=0 (`i·field_L/8`, i=4); (b) probed the magnet "boss" at r=0, which is the pocket cavity - the boss is a ring. Fix: compute probe coordinates from the same parameter formulas as the geometry (`rib_x(i)`, `slot_yc(i)`, boss at `r ≈ (mag_d+boss_d)/4`). A failing truth table doesn't always mean bad geometry - but check the geometry first before blaming the probe.
5. **Removal vs. child-safety conflict.** Safe 5 mm openings are too small for adult fingers too - the cover would be sealed in. Solved twice over: rib-hooking lift key (needs the straight slot corridor) + magnet pockets with 1.2 mm ceilings (style-agnostic). Don't ship a drop-in cover without an extraction plan.
6. **Fresh-sandbox deps:** `trimesh.contains` needs `rtree` (not pulled in by trimesh). `pip install --break-system-packages manifold3d trimesh numpy matplotlib networkx rtree`. `networkx` still required for 3MF export.
7. **Ribs read as "bridges" through slots - intentional.** Rib tops sit 4.5 mm below the surface, visible only looking straight down, same as commercial registers' hidden webs. In print orientation each rib bridges the 5 mm slot gaps - trivial bridging, no supports.
8. **Kumiko needed thinner bars to keep breathing.** At the safety-fixed 5 mm gap, 4 mm bars gave ~31% field porosity; 3.4 mm bars give ~35.4% (→ ~140 cm²). Bars are 4.5 mm deep and triangulated, so thinner is fine structurally.
9. **OpenSCAD echo/assert as early warning.** Bed-fit and ≤5 mm-opening rules live as `assert()` in the .scad, so future param tweaks (someone sets `slot_w = 8`) fail loudly at render time, not at install time.
10. **Hardcoded support positions rot when dimensions become mode-dependent.** The Luxe extra ribs were first hardcoded at x=134/145 - one actually missed the ring-1 end band's start (145 vs 145.25) and only fused via a 0.95 mm sliver; and when the two-part mode changed the frame opening length, both would have missed entirely. Fix: derive them (`(ring_outer + ring_inner)/4` = band centerline). Any support/feature that must track another feature gets a formula, never a number.
11. **Full-thickness dovetails beat "hidden" partial-depth ones for top-face-down prints.** A tab occupying only the lower plate thickness looks nicer (invisible seam) but becomes an unsupported horizontal shelf starting mid-air in the flipped print orientation. Same lesson as the flange bevel: re-check every feature in PRINT orientation, not design orientation.
12. **HTML viewers must budget memory like embedded targets.** v1 embedded ~4.3 MB of base64 STL and expanded it to unindexed triangle soup (positions + duplicated normals) at load - the app's preview sandbox threw `RangeError: Array buffer allocation failed`. v2: merge vertices → indexed uint16 geometry, gzip the binary payload (Python `gzip` at build, browser `DecompressionStream` at load), `flatShading: true` instead of per-corner normals → 156 KB file, ~30× less peak allocation. Same crisp CAD look.
13. **"Invisible" is a geometric spec you can assert: keep the projection empty, then check the sightline angle.** Hiding the Luxe supports wasn't about making them smaller - it was (a) an empty-box constraint (no material in any channel's vertical projection from the surface to depth D) plus (b) choosing D so `atan(gap/D)` is steeper than any realistic viewing angle (5/14.5 → 19°). Both are checkable: the containment sweep asserts (a), arithmetic gives (b). Since islands must still connect across the channel projections *somewhere*, the crossings go below D (deep ribs), with hidden spine walls under the solid faces guiding loads down to them. Aligning the ring end spines exactly over the derived extra-rib positions made two features one load path.
14. **Split placement must respect the pattern.** The seam lands where every style has solid material for the tabs (border zone y=±77) and gets its own doubled rib; the original center rib (exactly at x=0, i.e., exactly on the seam) is removed in two-part mode rather than sliced lengthwise into two 1.2 mm slivers.

## Print settings (PETG, Bambu H2D)

- Orientation: **as exported in the `*_PRINT` files - top face already down**, z=0 at bed. Textured PEI, glue-stick as release agent, cool before removal (plate-care note).
- 0.2 mm layers, **4 walls**, 25-30% gyroid, no supports, no brim (348.5 mm part → make sure skirt/brim doesn't push past 350; use "skirt: off" if the slicer complains).
- Nozzle 240-250 °C, bed 70-80 °C. Big flat PETG part: dry filament, avoid drafts.
- Filament: ~250 cm³ solid volume → roughly 200-260 g per cover as sliced. Lift key: ~4 g.
- Print the **lift key flat** as exported.

## Install / use

1. Vacuum the duct mouth; test-fit - skirt drops in, flanges rest on the floor along the long edges, ends sit flush inside the opening (hairline gap is by design).
2. Optional: glue two 8×3 mm neodymium discs into the underside pockets (CA or epoxy).
3. Remove for cleaning: lift key into a slot beside a rib → slide to hook → pull; or magnet-on-a-stick over the two pocket positions (x = ±60 mm from center, on the centerline); or a suction cup.
4. If the fit is tight: the opening may be under 350 × 147 - sand skirt ends or reprint with `end_clear`/`side_clear` bumped.

## Files

Only the `.scad`, the Python validation/preview scripts, and the PNG previews are checked in; the STL/3MF print artifacts below are regenerated, not stored. Render each style with `openscad -o <style>_design.stl -D 'RENDER_PART="<style>"' nursery_flush_vent.scad` (producing the `<style>_design.stl` inputs the validate scripts expect), then run `validate_and_export.py` to emit the pre-rotated `*_PRINT.stl/.3mf` files.

| File | What |
|---|---|
| `nursery_flush_vent.scad` | Parametric source of truth (`RENDER_PART` = `fittes`/`kumiko`/`luxe`/`liftkey`; `PART` = `full`/`A`/`B`) |
| `nursery_vent_FITTES_350x147_PRINT.stl/.3mf` | One-piece, print-ready, pre-rotated |
| `nursery_vent_KUMIKO_350x147_PRINT.stl/.3mf` | One-piece, print-ready, pre-rotated |
| `nursery_vent_LUXE_350x147_PRINT.stl/.3mf` | One-piece (3-channel), print-ready, pre-rotated |
| `nursery_vent_LUXE_SINGLE_350x147_PRINT.stl/.3mf` | One-piece (single channel), print-ready |
| `two-print/nursery_vent_{STYLE}_half{A,B}_PRINT.stl/.3mf` | Two-part versions, all 4 styles (16 files) |
| `vent_lift_key_PRINT.stl/.3mf` | Removal tool, 7 mm foot - hooks under fittes cross-ribs |
| `vent_lift_key_LUXE_PRINT.stl/.3mf` | Removal tool, 4.2 mm foot - hooks under a luxe panel/ring edge (rib-hooking can't reach the deep luxe structure; magnets/suction also work) |
| `validate_and_export.py`, `validate_luxe.py`, `validate_halves.py` | Truth-table validation + print-orientation export |
| `make_previews.py`, `make_viewer.py` | PNG preview and HTML viewer generators (the HTML itself is regenerated, not stored) |
| `preview_*.png` | 3-way top comparison, isos, undersides, edge closeup, print orientation, two-part, lift key |
