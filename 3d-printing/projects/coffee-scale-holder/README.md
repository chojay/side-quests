# Coffee Scale Under-Beam Garages

Two "garage" docks that glue under a horizontal beam next to the espresso machine, one per scale: a Maestri House K112 (105 x 105 x 22 mm) and a BOOKOO Themis Mini (80 x 80 x 15 mm). The scale slides in flat, display up, and rests on silicone-feet friction. No screws anywhere; the top plane prints as a smooth vertical wall and takes VHB tape.

**Why it took four architectures in one session:** v1 was a combined drop-in tray, v2 split with a back-wall mount, v3 a flat cradle, v4 the under-beam garage. Each pivot cost minutes, not hours, because one CadQuery script with named constants (`CLEAR_XY = 2.0`, `CLEAR_Z = 4.0`) emits both holders from a `SCALES` table.

**The research story I keep retelling:** seven written sources confirmed the K112 charges over USB-C without one of them saying which edge the port is on. The answer was buried in the manual's product render (port mid-right-edge, power switch ~28 mm from the front corner). And since both scales are square, the design hedges the remaining uncertainty with symmetric cable windows in both side walls: whatever edge the port is on, rotate the scale 90 degrees while charging. Designing around uncertainty beat more research.

**Access design:** the top plate is set back 20-25 mm from the mouth so the scale's front strip stays pinchable, paired with an elliptical scoop in the floor edge (thumb below, finger above). Both features are inherited from the glove dispenser in this repo; the design DNA transfer is documented in the gotchas playbook.

**Files:** `coffee_scale_holder.py` (generates both holders, validates watertightness with trimesh, writes a minimal 3MF by hand, and emits HTML viewers), `preview.png`.

**What went wrong (honestly):** a rotation-direction coin flip (`rotate -90` vs `+90`) once stood the part on the wrong face, turning the top plate into a 107 mm unsupported bridge. Every containment test passed, because the test transform came from the same wrong rotation. Only the print-orientation render caught it. That bug is the reason the playbook's "THE BIG ONE" rule exists.

**AI-assisted build notes:** Claude's pivot speed across four architectures was the standout win, and it found the port location in the manual render after text search failed. The flipped-export bug was its miss and also its tests' miss; the lesson generalized into the pipeline (numeric truth table AND render, always both).
