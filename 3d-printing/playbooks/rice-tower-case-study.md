# Parametric Design Playbook - Microwave Rice Tower Case Study

How a dispenser for an object with **no published dimensions** (CJ 햇반 instant rice bowl) went from idea to a successful print in 6 versions. Each principle below is written to be reused on the next similar project. Case artifacts live in [../projects/microwave-rice-tower/](../projects/microwave-rice-tower/) (v1 and the final v6 script; final print: **rice tower v6**, dia151 x 320 mm, 199 cm3, printed 2026-06 on a Bambu Lab H2D upright with no supports).

---

## TL;DR Workflow Checklist

1. **Research dimensions** you cannot measure: Korean products -> hobbyist hand-measurement posts (communities measure what manufacturers keep private)
2. **Size to the worst-case variant** + explicit clearance, both as named parameters
3. **Map the motion envelope first** (how the object enters/exits) - it dictates where material CANNOT exist
4. **Let print physics shape the form**: 45-degree rule, no floating islands, curved walls cannot bridge
5. **Trust field reports over theory** for ergonomics (someone has usually built the wooden/store version already)
6. **Validate the output mesh, never the code intent**: watertight + numeric envelope checks + measure the result
7. **Iterate with renders/HTML viewer**, version every file, never overwrite
8. **Lighten last**, structural zones untouched, wall thickness as the final lever

---

## 1. Getting dimensions when none are published

CJ does not publish 햇반 container dimensions. Web search failed; a Korean camping community post hand-measured every major brand for backpack packing:

| Product | Measured size |
|---|---|
| CJ 햇반 210g/200g | dia 137 x H35 (200g and 210g containers identical) |
| CJ 햇반 130g | dia 137 x H30 (same diameter as 210g) |
| 오뚜기밥 210g | dia 139 x H38.5 (the widest common bowl) |

**Reusable rules:**
- For Korean consumer products, search in Korean for `{product} 크기 지름 높이` and prefer hand-measured (실측) posts. Camping and packing communities measure everything.
- One blogger measuring 5 brands beats 5 spec sheets: cross-brand context reveals the worst case.
- **Design to the worst-case variant, not the named one.** The "햇반 holder" is actually sized for 오뚜기밥 (139 > 137), so "most microwavable rice" fits. `BOWL_DIA = 139.0` + `SLACK = 3.5` per side, both named parameters with the alternatives in comments.
- Record measured values verbatim in the script docstring AND in project memory; the next session should not re-research.

## 2. Cloning style from an existing artifact (STL reverse-engineering)

The first deliverable (a box-style variant) cloned the style of a downloaded ramen-box STL. Method, reusable for any STL:

- `trimesh.section()` at multiple Z heights -> wall thickness, footprint, openings
- Read section pieces in **world coordinates** (`section.discrete`), not the auto-transformed `to_2D()` frame, or per-slice comparisons silently shift origin
- Vertical sections through walls reveal lattice/pattern metrics (the ramen box decoded to: 2 mm walls, 30 mm flat-to-flat hexes, 32 mm column pitch, 36 mm row pitch, 18 mm stagger)
- matplotlib `Poly3DCollection` renders from 3-4 angles answer "what does it actually look like" in seconds

## 3. Parametric discipline pays off immediately

Every dimension is a named constant; everything else is derived (`R_IN = BOWL_DIA / 2 + SLACK`). Proof of value during this project:

- 6-bowl -> 8-bowl tower: **one line** (`N_BOWLS = 8`), everything (height, slot rows, hang hole) followed
- Printer limit is a hard assert in the export step (`assert m.extents[2] <= 325`), so a future capacity edit fails loudly instead of producing an unprintable file
- Per-row/per-cell geometry generated in loops from the parameters means a style change (gable -> rounded rect -> slot rings) only touches one block

## 4. Motion envelope first (the dispenser corridor rule)

For any bottom-dispense design: the exiting object sweeps an envelope, and **nothing may exist inside it**. Here: bowl radius + slack (|x| < 72.5), entire front half-plane, from floor to bowl height + margin (z < 45).

Consequences that shaped the whole tower:
- No front column can reach the floor -> front retention must start ABOVE the mouth
- The two side columns sit exactly at the corridor edge (they are the "cheeks" guiding the bowl out)
- Verified numerically every version: filter mesh vertices inside the corridor box, assert count == 0

Related lesson from the donor concept (a birch-plywood camping dispenser from a Korean woodworking post): their front slat just floats above the gap because plywood is assembled. A one-piece FDM print cannot do that, which leads to:

## 5. Print physics as the form-giver (upright, support-free)

The signature shapes of the tower are not aesthetic choices, they are the 45-degree rule made visible:

- **Gothic arch mouth**: the mouth spans the full front (147 mm) on a CURVED shell. A flat or semicircular header cannot bridge (a bridge is a straight line; the curved wall departs from it by ~57 mm of sagitta). Only >= 45-degree flanks climbing from the side columns close the opening support-free. Apex rounding r55 makes it read as a dome, not a point.
- **Slot rings instead of one wraparound band**: any opening's ceiling prints in mid-air. On a curved wall, keep each ceiling chord under ~35-40 mm (sagitta < ~wall/2). Hence 10 slots x 36-degree pitch per ring rather than a continuous band; rounded corners (r10-12) further shorten the flat span and self-close progressively.
- **Large "rounded rectangle" windows**: top corner radius near half-width gives a near-semicircular look while keeping the flat bridge ~16 mm (v4 used r48 on a 112 mm window).
- **Circular hole tops** self-close acceptably when the final bridge `2*sqrt(2*r*layer_height)` is small; that math allowed apex/corner radii up to ~55 here.
- No stalactites: a part that begins in mid-air (front column starting at z=45) is an island. If it cannot grow from something at <= 45 degrees, redesign it away.

## 6. Field wisdom beats first-principles ergonomics

The wooden donor design encoded a user-tested finding: their **10-bowl version failed** (stack weight made the bottom bowl too hard to pull) and 6 was the proven count. We shipped 8 with that caveat stated, banking on PP-on-PLA friction being lower than PP-on-plywood. Printed result: works.

Other borrowed/derived ergonomics:
- Bowls taper (rim dia 137-139, base ring dia ~95-100), so the rim overhangs and is naturally grippable through the mouth; a base-edge finger scallop helps the last bowl
- The bowl rests on its outer base ring -> a dia 78 hole in the floor saves 14 cm3 and can never snag or swallow a bowl
- Mouth clear height = bowl height + ~6 mm so a bowl can tilt slightly during extraction

## 7. Validate the output, never the intent (the silent fillet bug)

The most valuable debugging lesson of the project: **the arch apex fillet silently never applied through 5 versions.** In build123d, vertices inside a `BuildSketch` are in LOCAL plane coordinates (Z always 0; local Y = world Z on Plane.XZ). Filtering by world `.Z` matched nothing and `fillet([])` no-opped without raising. The user's screenshot of the "pointy" arch exposed it.

Standing rules:
- After every build, **measure the mesh** for the feature you just changed (the fix was confirmed by `mouth ceiling z = 98.7`, exactly the r55 prediction, vs 121.5 sharp before)
- `assert len(selection) == N` before every fillet/chamfer on filtered geometry
- Pipeline every version: trimesh watertight check -> corridor check -> dimension probes -> multi-view render -> interactive HTML viewer for the human
- Keep the viewer step: both design-changing user requests (open front, rounded windows, fix the point) came from the user orbiting the HTML viewer

## 8. Lighten last, and in the right order

v6 cut filament 23% (258 -> 199 cm3) only after the design was settled and liked. Order of operations:

1. Dead zones first: base disc center (object never touches it)
2. Enlarge existing openings toward their print-physics limits (slots 26->30 mm tall, 28->30 degrees)
3. Add openings in over-solid areas that still satisfy retention (bowl-1 back ring)
4. Trim non-critical bands (top band 22->18 mm)
5. **Do not touch**: mouth cheeks, arch fascia, foundation ring, posts below ~8 mm wide
6. Last lever, not taken: wall 2.5 -> 2.0 mm (~25-30 g more, costs stiffness everywhere)

---

## File map (this repo)

| File | What |
|---|---|
| `../projects/microwave-rice-tower/rice_tower_v6.py` | Final parametric source (printed); running it regenerates the STL + 3MF |
| `../projects/microwave-rice-tower/rice_tower_v1.py` | First version, kept to show the iteration distance |

STL/3MF print files are not checked in; each script regenerates them. The ramen-box style donor STL was a third-party download and is not redistributed here.

## Related

- [parametric-design-gotchas.md](parametric-design-gotchas.md) - consolidated cross-project gotchas (this case study + Coffee Scale Holders + Glove Dispenser + Eufy sign); start there
