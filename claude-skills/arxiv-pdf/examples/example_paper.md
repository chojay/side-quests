---
title: "Assert-Driven Parametric Design for FDM-Printed Replacement Parts: A Formatting Demonstration"
date: "August 2026"
author:
  - name: Jay Cho
    affiliation: "1"
affiliations:
  - id: "1"
    name: "Independent maker (this document is a formatting demonstration for the arxiv-pdf skill, not a real preprint)"
abstract: |
  Consumer fused-deposition-modeling (FDM) printers make one-off replacement
  parts practical, but the dominant failure mode is not printing, it is
  specification: parts fail at install time because a dimension was measured
  once, trusted, and wrong. We describe a code-as-CAD workflow in which every
  part is a parametric program, every physical constraint is an executable
  assertion, and every exported mesh passes a validation battery before a
  slicer ever sees it. Constraints such as printer build volume, child-safety
  opening limits, and motion-envelope clearances are encoded as asserts that
  fail at build time rather than at install time. We illustrate the workflow
  with dimension-sourcing rules, a containment-probe validation scheme, and a
  tolerance-bracketing test-print protocol. This document is a worked example
  for a Markdown-to-arXiv-PDF conversion skill; the methods are real, the
  paper framing is illustrative.
---

# Introduction

A replacement part has a harder specification problem than an original
design: the geometry it must match already exists, is often undocumented,
and was manufactured to tolerances unknown to the person holding the
calipers. The workflow described here treats that uncertainty as the
central design input.

The core rule is that no dimension is drawn; every dimension is a named
constant, and everything else derives from it. When a caliper reading is
revised after a test fit, the revision is a one-line change and a re-run,
not a remodel.

## Constraints as assertions

Physical constraints are encoded as executable assertions evaluated at
mesh-generation time. A bed-size constraint takes the form

$$
\max(W_{\text{part}}, D_{\text{part}}) \le B - 2m,
$$

where $B$ is the printable bed dimension and $m$ is a margin reserved for
brims and skirts. A child-safety constraint on opening width $g$ is simply
$g \le 5\ \text{mm}$, asserted over every generated aperture. A violated
constraint fails the build loudly; a printed part cannot violate it quietly.

## Rotated-footprint analysis

A recurring question is whether a part wider than the bed can be printed
diagonally. For a part of length $L$ and width $W$ rotated by angle
$\theta$, the bounding width is

$$
W_{\text{bb}}(\theta) = L\cos\theta + W\sin\theta,
$$

which is minimized at $\theta = 0$ for wide parts. Rotation rescues long
thin parts only; for wide parts the design must change instead. Encoding
this as a check prevents a class of optimistic slicing attempts.

# Validation battery

Every exported mesh passes four checks before slicing, summarized in
Table 1.

| Check | Method | Catches |
|---|---|---|
| Watertightness | manifold analysis of the exported mesh | non-manifold booleans |
| Containment truth table | 12 to 17 point probes per part | inverted or missing volumes |
| Envelope assert | bounding box vs. printer limits | bed and height violations |
| Orientation render | image of what touches the bed | flipped exports |

The fourth check exists because the first three share the part's own
coordinate transforms: a wrongly rotated export once passed every
containment probe, since the probes were derived from the same wrong
transform. Only rendering "what touches the bed" made the error visible.
Validation derived from intent validates the intent, not the artifact.

# Tolerance bracketing

Where a mating dimension is uncertain, the workflow prints a bracket: a
small matrix of test rings or tabs spanning the plausible range in fixed
increments, printed overnight, test-fitted in the morning. The surviving
increment becomes a named constant with a comment recording the date and
the mating part. This is cheaper than precision measurement and more
honest than optimism.

# Conclusion

Treating parts as programs moves failure from install time to build time,
where it costs seconds. The asserts, probes, and brackets described here
are not sophisticated; their value is that they run every time, which is
precisely what manual checking does not do.

*This document demonstrates the arxiv-pdf skill's output format: YAML
frontmatter to a titled, numbered, single-column preprint with display
mathematics and tables. It is not a submitted or planned publication.*
