---
name: arxiv-pdf
description: >-
  Converts Markdown files with YAML frontmatter into publication-quality,
  arXiv-style preprint PDFs (single-column, Latin Modern/Computer Modern
  fonts, centered title block with author affiliations, numbered sections) via
  Pandoc and a bundled LaTeX template, with full support for equations,
  figures, tables, BibTeX citations, and cross-references; can also emit .tex
  source for actual arXiv submission. Use when the user wants to convert a
  markdown file or Obsidian note into an arXiv-style PDF, create an academic
  paper or preprint from markdown, generate a LaTeX PDF from a note, or format
  a research document as an arXiv submission. Trigger phrases include "convert
  to arXiv PDF", "make this a paper", "generate PDF from markdown", "arXiv
  style", "preprint PDF", "academic PDF", "paper from this note", and "LaTeX
  PDF from markdown".
---

# arXiv-Style PDF - Markdown to Preprint Converter

## Overview

This skill converts Markdown files (`.md`) with YAML frontmatter into publication-quality PDFs that match the visual signature of arXiv preprints: single-column layout, Computer Modern / Latin Modern fonts, centered title block with author affiliations, numbered sections, and professional typesetting via LaTeX.

**Toolchain**: Markdown → Pandoc → LaTeX (custom template) → pdflatex → PDF

## When to Use This Skill

Use this skill when the user requests:
- Converting a markdown file to an arXiv-style PDF
- Creating an academic paper / preprint from markdown
- Generating a LaTeX PDF from an Obsidian note
- Formatting a research document as an arXiv submission
- Converting `.md` notes into publication-ready documents

**Trigger phrases**: "convert to arXiv PDF", "make this a paper", "generate PDF from markdown", "arXiv style", "preprint PDF", "academic PDF", "paper from this note", "LaTeX PDF from markdown"

## Prerequisites

The following must be installed on the system (verify before converting):
- **Pandoc** (v2.10+): `which pandoc`
- **pdflatex** (TeX Live): `which pdflatex`
- Required LaTeX packages (all in TeX Live 2025): `lmodern`, `geometry`, `amsmath`, `graphicx`, `booktabs`, `hyperref`, `natbib`, `titlesec`, `caption`, `fancyhdr`, `microtype`, `cleveref`, `enumitem`, `subcaption`, `mathtools`

## Template Location

The template files live in the `templates/` directory bundled with this skill:

```
~/.claude/skills/arxiv-pdf/templates/arxiv-preprint.latex   ← Pandoc LaTeX template
~/.claude/skills/arxiv-pdf/templates/convert.sh             ← Shell wrapper script
```

## Markdown File Format

### Minimal Frontmatter (quick start)

```yaml
---
title: "My Paper Title"
author:
  - Your Name
abstract: |
  Brief summary of the paper.
---
```

For the complete reference of all supported frontmatter fields (authors/affiliations, abstract, arXiv header, layout, fonts, bibliography, figure paths, preamble extras), see [references/frontmatter-reference.md](references/frontmatter-reference.md).

## Markdown Body Syntax

For full markdown-to-LaTeX syntax (equations, figures, tables, citations, cross-references, footnotes, raw LaTeX), see [references/markdown-syntax.md](references/markdown-syntax.md).

## Conversion Workflow

### Step 1: Prepare the Markdown File

Create or identify the `.md` file with proper YAML frontmatter. Ensure:
- All referenced images exist at the specified paths
- Bibliography `.bib` file exists if citations are used
- Paths are relative to the markdown file's location

### Step 1b: Verify every citation exists (anti-hallucination)

An AI-drafted paper can invent a DOI, or pair a **real** DOI with a fabricated
title. Both pass a casual eye and a plain 200-OK check. Before building, resolve
every citation and confirm the DOI maps to the paper you actually cited:

```bash
SCRIPTS="$HOME/.claude/skills/arxiv-pdf/scripts"
python3 "$SCRIPTS/verify_citations.py" refs.bib        # or the .md itself
python3 "$SCRIPTS/verify_citations.py" --doi 10.1038/nature14539   # spot-check one
```

The script (standard library only) queries **Crossref**, falls back to
**DataCite**, resolves **arXiv** IDs, and - when a `.bib` gives a title - checks
that the resolved title matches, catching the "real DOI, wrong paper" case.
Statuses:

- **VERIFIED** - DOI resolves and the title matches. Good.
- **MISMATCH** - the DOI resolves to a *different* paper than cited. Fix the DOI
  or the title; do not ship it.
- **NOT FOUND** - the DOI does not exist anywhere. It was almost certainly
  hallucinated; remove or replace the citation.
- **API-BLOCKED** - the API could not be reached (403, rate limit, offline).
  Not a pass. Verify it in the browser (below).

The script exits nonzero if anything is NOT FOUND / MISMATCH / API-BLOCKED, so it
can gate the build in a script.

**Browser fallback when WebFetch / the API is blocked.** Some publishers and
networks block programmatic access, and title-only citations have no DOI to
resolve. In those cases confirm the reference by hand through the
Claude-in-Chrome browser extension: open
`https://doi.org/<doi>` and confirm it lands on the cited paper, or search the
exact title on Crossref (`search.crossref.org`) or Google Scholar and confirm a
real match. **Never ship a citation that neither the API nor the browser could
verify.** Prefer the browser over `WebFetch` for this - publisher pages routinely
return 403 to `WebFetch` while rendering normally in the logged-in browser.

### Step 2: Run the Conversion

**Using the shell script:**
```bash
SKILL_DIR="$HOME/.claude/skills/arxiv-pdf/templates"
"$SKILL_DIR/convert.sh" paper.md paper.pdf
```

**Using pandoc directly:**
```bash
TEMPLATE="$HOME/.claude/skills/arxiv-pdf/templates/arxiv-preprint.latex"

pandoc paper.md \
  --template="$TEMPLATE" \
  --pdf-engine=pdflatex \
  --number-sections \
  --citeproc \
  -o paper.pdf
```

**With bibliography and cross-references:**
```bash
pandoc paper.md \
  --template="$TEMPLATE" \
  --pdf-engine=pdflatex \
  --number-sections \
  --citeproc \
  --bibliography=refs.bib \
  -o paper.pdf
```

### Step 3: Verify Output

Open the PDF and check:
- Title block renders correctly (title, authors, affiliations)
- Abstract is properly formatted
- Equations render without errors
- Figures appear at correct sizes
- References are numbered and linked
- Page numbers are present

## Customization and Troubleshooting

For template design rationale, customization (fonts, double-column, line numbers), and troubleshooting common LaTeX/pandoc errors, see [references/customization-and-troubleshooting.md](references/customization-and-troubleshooting.md).

## Example Files

See `examples/example_paper.md` for a complete working example demonstrating all features, and `examples/example_paper.pdf` for the rendered output.

---

*This skill produces PDFs matching the visual conventions of arXiv preprints across physics, materials science, mathematics, and computer science. The output is suitable for arXiv submission (upload the generated .tex intermediate file) or for internal distribution as a polished technical document.*
