# Hetbahn Rice-Bowl Tower Dispenser

![Render of the v6 tower: slotted cylindrical cage with gothic-arch dispensing mouth](overview.png)

A gravity dispenser for round microwave rice bowls: bowls stack inside a cylindrical cage, the bottom bowl pulls out through a gothic-arch mouth, and the stack drops down. Printed and verified at dia 151 x 320 mm, 5 mm under my printer's Z limit.

**Compatibility:** sized for the round Korean-style bowl format, so it takes most of what US warehouse and H-Mart shelves carry: CJ Hetbahn (햇반, the 137 mm bowl it is named after), Ottogi-bap, and Bibigo including the [Costco 7.4 oz twelve-count](https://www.costco.com/p/-/bibigo-cooked-sticky-white-rice-bowls-medium-grain-74-oz-12-count/4000040390). It does **not** take rectangular trays, the format many Japanese brands use - square corners cannot ride a round cage, and a rectangular version would need a different retention geometry, not a resize.

**Why:** CJ publishes no container dimensions. The sizing came from a Naver camping blogger who hand-measured five brands; the tower is deliberately sized to the widest bowl of the set (139 mm Ottogi-bap), which is what buys the multi-brand fit above. Full story in [../../playbooks/hetbahn-tower-case-study.md](../../playbooks/hetbahn-tower-case-study.md).

**How it works:** build123d, every dimension a named constant with derived values (`R_IN = BOWL_DIA/2 + SLACK`). The mouth is a 45-degree gothic arch because a flat header on a curved shell cannot bridge; ventilation is slot rings (10 slots per bowl level) instead of a wraparound band because a curved ceiling is unprintable past ~40 mm of chord. Scaling 6 bowls to 8 was a one-line change. A hard `assert m.extents[2] <= 325` guards the printer limit.

**Files:** `hetbahn_tower_v1.py` (first version) and `hetbahn_tower_v6.py` (final, printed). Run either with build123d + trimesh installed; STL and 3MF are regenerated next to the script, so no meshes are checked in. v6 cut filament 23% (258 to 199 cm3) through an ordered lightening pass done only after the design was liked.

**What went wrong (honestly):** the arch apex fillet silently no-opped for five straight versions. build123d `BuildSketch` vertices are in local plane coordinates, so filtering by world `.Z` matched nothing and `fillet([])` does not raise. A human looking at the render caught the pointy arch; the fix in v6 carries `assert len(selection) == N` before every filtered fillet. That rule is now in every script I write.

**AI-assisted build notes:** Claude wrote the CAD code and the validation pipeline, and the parametric discipline made its iteration loop genuinely fast (six versions in a few sessions). But it also confidently shipped the silent-fillet bug five times, and its containment tests could not catch it because they tested intent, not output. The catches came from me orbiting the HTML viewer and from print-orientation renders. The division of labor that worked: AI writes geometry and asserts, human reviews renders.
