# Kumiko Wall-Vent Cover (bed-split joinery)

![Render of the assembled two-half kumiko cover; the top view shows the asanoha lattice](overview.png)

A decorative kumiko asanoha-lattice air-vent cover for a 10 x 4 in wall duct. The interesting engineering is not the pattern, it is how a part wider than the print bed gets split and rejoined with woodworking joints.

**The split problem:** the 10 x 4 cover with a 1-inch border is 304.8 mm wide plus hooks, past comfortable bed placement, so it prints as two halves joined by:

- **Dovetail keys** relocated onto the Z-profile drop-down hooks (v2), where they get the full 25.4 mm depth of engagement instead of a cosmetic surface joint
- **Tab-and-slot registration** across the face plate seam

**How it works:** `kumiko_vent_10x4_split_dovetail_edge_v2.py` builds everything in manifold3d (CSG that guarantees watertight output), with numpy for the lattice math. The kumiko pattern extends 12.7 mm into the frame border so the lattice reads as continuous rather than framed. `air_vent_cover.scad` is the original OpenSCAD from before the Python port, kept for the before/after comparison.

The asanoha (hemp leaf) lattice is a traditional Japanese kumiko pattern; the geometry here is generated entirely from code.

**What went wrong (honestly):** v1 put the dovetails in the top plate, where they lock in-plane pull-apart but carry nothing in vertical shear, the load a wall part actually sees. The v2 relocation onto the hooks came from asking "what load does this joint actually take?" after a dry-fit felt flimsy. Manual mesh construction before manifold3d also produced repeated non-manifold T-junction failures; that history is what standardized the whole vent family on manifold3d.

**AI-assisted build notes:** Claude did the OpenSCAD-to-manifold3d port and the joint geometry math reliably. It did not, on its own, question the structurally useless v1 dovetail placement; that redesign came from a human handling the printed dry-fit. Printed feedback remains the strongest code review.
