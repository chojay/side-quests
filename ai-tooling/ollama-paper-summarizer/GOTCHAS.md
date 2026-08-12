# Gotchas: what the idea bank is actually good for (and where it lies to you)

The per-paper summaries are the boring part. The value shows up in the **compare**
step: read a few papers, summarize each, hold each new summary against the ones
already in the bank, and watch for a theme none of the papers states on its own.
This is a worked example of that loop, and the gotcha it surfaced.

**Honesty note.** The DOIs below were checked with this folder's sibling
citation verifier ([`arxiv-pdf/scripts/verify_citations.py`](../../claude-skills/arxiv-pdf/scripts/verify_citations.py)) - all four resolve to the cited paper.
The per-paper summaries here were written in this session to illustrate the
shape; on your own machine the local Ollama pipeline produces the same kind of
summary offline. All four are open access.

## Three papers, summarized

**1. Scaling deep learning for materials discovery** (Merchant et al., *Nature*,
2023, [10.1038/s41586-023-06735-9](https://doi.org/10.1038/s41586-023-06735-9)).
A graph network (GNoME) trained with active learning predicts **2.2 million**
structures below the convex hull, ~380,000 of them stable - an order-of-magnitude
expansion of known stable inorganic materials. Headline framing: prediction,
scaled by compute, has outrun human chemical intuition.

**2. An autonomous laboratory for the accelerated synthesis of inorganic
materials** (Szymanski et al., *Nature*, 2023,
[10.1038/s41586-023-06734-w](https://doi.org/10.1038/s41586-023-06734-w)). A
closed-loop robotic lab (A-Lab) took DFT-predicted targets, generated recipes
from a literature-trained model, ran syntheses, read XRD with an ML classifier,
and optimized by active learning. Over **17 days** it made **41 of 58** targets
(71%) with little human intervention. Headline framing: synthesis, too, can be
automated end to end.

**3. Machine learning for alloys** (Nat. Rev. Mater., 2021,
[10.1038/s41578-021-00340-w](https://doi.org/10.1038/s41578-021-00340-w)). A
review of ML across alloy design that keeps returning to one constraint: models
are only as good as sparse, biased, hard-won experimental data, and a prediction
is not a validated material.

## The recurring theme (what none of them says alone)

Read in isolation each paper is a triumph. Held against each other, a different
line shows through: **prediction has been scaled by orders of magnitude, but
synthesis and validation have not, and the gap is where the real work now lives.**
GNoME predicts millions; independent labs have so far *synthesized* on the order
of **736** of them. A-Lab automates synthesis but still leans on curated
predicted targets and human interpretation of its failures. The alloys review
names the bottleneck outright: data and validation, not prediction.

The theme is load-bearing enough that both flagship results drew published,
verifiable critiques on exactly this axis - how many of the "new" materials are
genuinely novel and validated (e.g. Cheetham & Seshadri, *Chem. Mater.*, 2024,
[10.1021/acs.chemmater.4c00643](https://doi.org/10.1021/acs.chemmater.4c00643)).
That is not a footnote to the theme; it *is* the theme.

## The gotcha

**A summary tuned for "findings + quantitative results" systematically drops the
limitations - so an idea bank built from those summaries is quietly
over-optimistic, and the most important recurring theme is the one it cannot
see.** The prompt in this pipeline asks for the advertised advance and the
headline numbers. That is exactly what a paper's abstract oversells, and exactly
what makes every summary read like a win. The "validation lags prediction"
theme above is invisible in three upbeat summaries; it only appears when you read
the limitations sections and track the follow-up critiques - neither of which a
findings-and-numbers summary captures.

Two concrete fixes, both now noted against the pipeline:

1. **A limitations line, now added to the prompt.** A required "Stated
   limitations and open questions (up to 3 points)" section costs almost nothing
   and is what lets a cross-paper read find a *recurring weakness* rather than
   only a recurring strength. This has been applied to the shipped prompt; the
   ~3,900 summaries already produced predate it and will pick it up on the
   re-run. A calibrated idea bank has to index what a paper cannot do, not just
   what it claims.
2. **Index the critiques next to the originals.** A comment or perspective paper
   is often where the real recurring theme is stated plainly. Summarize those
   too, and let the similarity search put the critique next to the claim.

The larger lesson is the repo's lesson: a tool that only records advertised wins
produces a confident, wrong picture. The summaries were never the point - the
honest comparison across them is, and it only works if the summaries carry the
caveats.
