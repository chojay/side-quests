# Eufy E340 Doorbell "Baby Sleeping" Sign

A two-color "PLEASE DON'T RING, BABY SLEEPING" sign for the Eufy Video Doorbell E340, built to keep nap time quiet at the front door. Concept adapted from sebtobar's Ring doorbell frame on MakerWorld (model 1139309); that model's license does not allow redistribution, so the geometry here was authored independently in build123d and only the idea is borrowed.

**Four architectures, because the mounting requirement kept changing:**
1. Trapped surround (frame pinned between wall and doorbell)
2. 15-degree tilted wedge surround (for the E340's angle bracket)
3. Removable friction clip-on cover
4. Inverted-U that drops over the doorbell and rests by gravity - the current pick, with a deep variant whose side walls extrude along the doorbell's tilted normal so they track the 15-degree wedge without binding

This folder carries the first architecture (`eufy_e340_frame.py`) and the final one (`eufy_e340_inverted_u_deep.py`), plus `validate.py` (containment truth table) and `create_3mf.py`, a minimal 3MF writer built from zipfile because CadQuery/build123d tooling could not emit the dual-color Bambu 3MF I wanted. A 3MF is just a zip with three XML files; writing one by hand demystified the format.

**The dimension lesson:** eufy's own spec says the E340 is 138 mm tall. Home Depot says 150.1 mm, B&H says 6.0 in = 152.4 mm. The surround built on the official number came out 11 mm short; the cover built on Home Depot's number was still 1 mm short. Take the max across vendors, never average, and treat a single vendor page as one vote.

**What went wrong (honestly):** beyond the height fiasco, text glyphs and an outline ring in one `BuildSketch` erased each other through `Mode.SUBTRACT` (an empty plaque passed the watertight check; only a face render caught it), and two abutting rounded rectangles left a 4-open-edge sliver at their tangent seam until the solids were overlapped where hidden. Print orientation dictates lettering: raised text needs its face up, and a front-down tray forces inlaid and mirrored text.

**AI-assisted build notes:** Claude handled the four rewrites cheaply because everything was parametric, and it wrote the custom 3MF writer in one pass. Its failures were trusting the official spec sheet over retailer disagreement (a judgment error I share) and repeating the sketch-subtract bug it had already hit on an earlier project. Renders caught what tests did not, both times.
