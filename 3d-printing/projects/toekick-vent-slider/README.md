# Toe-Kick Vent with Print-in-Place Sliding Damper

![Overview render: iso and top views of the v3 slider vent](overview.png)

A replacement for the metal toe-kick register under a bathroom vanity where the heater blew too hard. v2 is a fixed 45-degree louver plate that deflects the remaining airflow sideways; v3 is the interesting one: a **print-in-place adjustable damper**. The base plate and a sliding shutter print as one job, the slider captured in rails at 0.4 mm vertical gaps (two 0.2 mm layers - PETG fuses below that, do not shrink it). Slide the center tab 3 mm and the slider's 2.4 mm slits phase-shift against the base's 3.0 mm slits: fully closed as printed, up to ~43% open at the end stop, exactly like the lever on a metal register but with zero assembly.

**The verification is the design:** the generator checks the printed-closed state has 0.3 mm of overlap per slit side, confirms the export is watertight with exactly 2 bodies, and runs a boolean collision test between slider and base across the full 0-3 mm travel (zero intersection required). The no-see-through louver math for v2 (fin span `T*tan(angle) + fin_t/cos(angle)` must exceed pitch) and the countersink-clearance rule are in [DESIGN-NOTES.md](DESIGN-NOTES.md), the fullest set of design notes in this collection.

**Provenance note:** the closest MakerWorld model requires login and its license forbids derivatives, so this is an original design replicating the standard 2.25 x 12 in register format from measurements of the old grille. This project is also the origin of several house rules the later vents inherit - print the show face down on textured PEI, and the license lesson itself.

**Files:** `build_vent.py` (v2 fixed louver, manifold3d + trimesh), `build_vent_v3_slider.py` (v3 print-in-place slider), `toekick_vent_parametric.scad` (hand-maintained OpenSCAD twin), `DESIGN-NOTES.md`, `overview.png`. STLs and 3MFs regenerate by running the scripts.

**What went wrong (honestly):** flush 45-degree fins in only 3 mm of plate deflect weakly - most air still exits forward, which is why v1 kept protruding fins and v3 abandoned deflection for flow control. And the effective open area math bites: perpendicular gap is `pitch*cos(45) - fin_t`, about 1.9 mm at these settings, so airflow is cut well below what the visible slit area suggests.

**AI-assisted build notes:** Claude wrote the manifold3d geometry, the phase-shift slit math, and the collision sweep; the print-in-place clearances (0.4 mm vertical, 0.6 mm lateral, free the slider before PETG cold-welds) came from print experience, not generation. The original script also hardcoded its sandbox output path, which survived until this export - generated code inherits its birth environment unless someone evicts it.
