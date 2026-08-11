# YAML Frontmatter - Complete Field Reference

Every markdown file must start with a YAML frontmatter block. Here is the **complete reference** of supported fields:

```yaml
---
title: "Assert-Driven Parametric Design for FDM-Printed Replacement Parts"
date: "April 2026"

# ── Authors (two formats supported) ──────────────

# Format A: Simple list (no affiliations)
author:
  - Alice Smith
  - Bob Jones

# Format B: Structured (with affiliations and emails)
author:
  - name: Jay Cho
    affiliation: "1"
    email: jay@example.com
  - name: Alice Smith
    affiliation: "1,2"
  - name: Bob Jones
    affiliation: "2"

affiliations:
  - id: "1"
    name: "Company A, Department of Research, City, State"
  - id: "2"
    name: "University B, Department of Materials Science, City, State"

# ── Abstract & Keywords ─────────────────────────
abstract: |
  We describe a code-as-CAD workflow in which every physical
  constraint is an executable assertion and every exported mesh
  passes a validation battery before slicing.

keywords:
  - parametric design
  - 3D printing
  - mesh validation
  - design validation

# ── Optional arXiv header ───────────────────────
arxiv-id: "2604.12345"          # Shows "arXiv:2604.12345" in header
preprint-label: "DRAFT"         # Shows label in left header

# ── Layout options ──────────────────────────────
fontsize: 11pt                  # 10pt, 11pt, or 12pt (default: 11pt)
papersize: letterpaper           # letterpaper or a4paper
geometry:                        # Override margins
  - margin=1in
linespacing: double              # single, onehalf, double

# ── Font ────────────────────────────────────────
# Default: lmodern (Computer Modern). Alternatives:
# fontfamily: newtxtext          # Times Roman
# fontfamily: newpxtext          # Palatino

# ── Bibliography ────────────────────────────────
# Option 1: Pandoc citeproc (default, no natbib needed)
bibliography: refs.bib
# csl: ieee.csl                 # Optional CSL style file

# Option 2: natbib (LaTeX-native, for .bbl files)
# natbib: true
# bibliography: refs
# bibstyle: unsrtnat             # plain, unsrt, unsrtnat, abbrvnat, apsrev4-2

# ── Figure path ─────────────────────────────────
graphics-path: "./figures/"

# ── Extra LaTeX in preamble ─────────────────────
header-includes: |
  \usepackage{siunitx}
  \usepackage{physics}

# ── Toggle optional packages ────────────────────
siunitx: true                    # Load siunitx
physics: true                    # Load physics package
---
```
