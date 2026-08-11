# Bathroom Toe-Kick Vent Grille - Design Notes

Replacement for the metal toe-kick register under the bathroom vanity (heater/AC blows too hard). Mostly solid plate with a small louvered window that deflects the remaining airflow to the right.

## Reference / measurements

- Original grille: standard **2¼" × 12" toe-kick register**, faceplate ≈ **340 × 85 mm**. User-measured 33.5 × 8.5 cm - the standard size was adopted.
- Screw holes: **9.3 mm** from each end, **45 mm** from bottom (center of bolt). Two holes, one per end.
- Measured from photo (~4 px/mm): original louver banks inset ~20–22 mm from ends, ~14 mm top/bottom (slits ~55 mm tall), ~22 mm solid bridge in middle, slits ~3 mm wide on ~12 mm pitch.

## v3 - adjustable slider (`toekick_vent_340x85_v3_slider_PIP`) - print-in-place

Center-60% slit opening + sliding damper printed as ONE job (2 bodies, slider captured in rails). Works like a metal register lever: slide the center tab **3 mm** to phase-shift slider slits against base slits - **0% (closed, as printed) → ~43% of the opening**.

- Base: same 340 × 85 × 3 plate/holes as v2. **34 straight vertical slits**, 3 mm wide, 6 mm pitch, **x 68–272 (center 60% of width)**, y 14–71.
- Slider: 216 × 65 × 1.8 mm behind rails on the front face (rails x 57–286); slits 2.4 mm on same 6 mm pitch, offset half-pitch when printed (closed). 2.4 < 3.0 solid → 0.3 mm cover overlap per side when closed.
- Print-in-place gaps: **0.4 mm vertical** (2 layers @ 0.2 - PETG fuses at 0.2–0.3, don't shrink), **0.6 mm lateral**. Rails top/bottom with 3.4 mm lips + end stops limit travel to exactly 3 mm.
- Center tab 14 × 18 × 3.5 mm on slider face. Total stack height 8.7 mm.
- Verified: watertight, 2 bodies, boolean collision test = zero intersection across full 0–3 mm travel.
- Print **back face down**; first slider layer bridges the 0.4 gap. Free the slider right off the plate with a firm sideways push on the tab before PETG cold-welds.

## v2 - centered fixed louver (`toekick_vent_340x85_center_louver`)

- Plate: 340 × 85 × **3 mm**, 6 mm corner radius.
- Louver window: **85 × 57 mm, centered** (x 127.5–212.5, y 14–71). Quarter of plate width; vertical inset matches original.
- Fins: 1.6 mm thick, **5.0 mm pitch**, **45° about vertical axis** → deflects exiting air to the RIGHT (viewer facing vent). Fully contained within the 3 mm plate - flat front and back.
- Screw holes: Ø4.2 mm through (#6 / M3.5), 90° countersink Ø8.5 mm on front face.
- v1 (kept in folder): right-quarter window, fins extending 7 mm behind plate - stronger deflection, not flush.

## Process

1. Convert HEIC photo: `pillow-heif` (no heif CLI tools in sandbox).
2. Geometry built in **Python with `manifold3d` + `trimesh`** (`build_vent.py`), exported `.stl` and `.3mf` directly. A matching parametric **`toekick_vent_parametric.scad`** is maintained by hand for future tweaks in OpenSCAD.
3. Verify: check `is_watertight`, volume, extents; render PNG previews (matplotlib `Poly3DCollection`, orthographic front/top/closeup/iso views) and visually inspect.
4. Copy deliverables to this folder; PNGs generated per design revision for quick review.

## Gotchas

- **MakerWorld source unusable**: model 616801 requires login to download and its Standard Digital File License forbids derivatives/remixes. This is an **original design** replicating the style - don't upload it claiming remix, and don't reuse their files.
- **Sandbox has no root** → can't `apt install openscad`. That's why geometry is Python/manifold3d; the `.scad` is untested-by-render, so re-check dimensions if you render it.
- Python deps needed: `manifold3d trimesh numpy matplotlib networkx` (`pip --break-system-packages`). `scipy` is unavailable - avoid `trimesh.fix_normals()` (manifold3d output is already correctly wound). `networkx` is required for 3MF export.
- **No-see-through math**: fin horizontal span = `T·tan(angle) + fin_t/cos(angle)`. At T=3, 45°, fin_t=1.6 → 5.26 mm; pitch must be ≤ this (hence 5.0) or there's straight-through line of sight.
- **Flush louvers deflect weakly**: 45° fins in only 3 mm of depth bias flow right but most air still exits forward. For real deflection, thicken the louver zone to 5–6 mm (or use v1's protruding fins).
- **Window vs. screw hole clearance**: if window is near an end, keep ≥18 mm margin so the countersink (Ø8.5 at 9.3 mm inset) stays in solid material.
- Effective open area is less than the visible slit area - perpendicular gap = `pitch·cos(angle) − fin_t` ≈ 1.9 mm at current settings. Airflow is cut well below the geometric ¼.
- Fins must overlap the plate to fuse in the union: fin boxes run 4 mm past the window top/bottom, then get trimmed by an intersection box spanning the window in x/z.

## Print settings (PETG)

- PETG chosen to withstand direct heater/AC air (fine to ~75–80 °C; PLA would creep).
- Print flat, **front face down** on the plate for the cleanest visible surface.
- 0.2 mm layers, 4 walls, ~30% infill. 1.6 mm fins = 2 perimeters wide.
- Check hole alignment against the old grille before installing; all dimensions adjustable in the `.scad` or `build_vent.py`.
