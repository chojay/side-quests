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

Optional, for citation and claim verification only (both scripts are standard
library and need no API keys):
- **pdftotext** (poppler): `which pdftotext`. Without it `verify_claims.py` falls
  back to `pypdf`, and without either it degrades to abstract-only scope and says
  so rather than passing claims it could not check.
- A **Zotero** library at `~/Zotero` (override with `ZOTERO_DIR`) to resolve
  `zotero=<itemKey>` tags to real PDFs. Not required if tags carry `pdf=` paths.

## Template Location

The template files live in the `templates/` directory bundled with this skill:

```
~/.claude/skills/arxiv-pdf/templates/arxiv-preprint.latex   ← Pandoc LaTeX template
~/.claude/skills/arxiv-pdf/templates/convert.sh             ← Shell wrapper script
~/.claude/skills/arxiv-pdf/scripts/verify_citations.py      ← does the reference exist?
~/.claude/skills/arxiv-pdf/scripts/verify_claims.py         ← does it support the claim?
```

The two verification scripts implement the Chain-of-Evidence design described in
[references/chain-of-evidence.md](references/chain-of-evidence.md).

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

### Step 1b: Ground citations as you write them (Chain-of-Evidence)

The verification steps below implement the Chain-of-Evidence (CoE) framework from
[ScientistOne: Towards Human-Level Autonomous Research via Chain-of-Evidence](https://arxiv.org/abs/2605.26340)
(arXiv:2605.26340), summarized on the
[Google Research blog](https://research.google/blog/science-one-framework-a-verifiable-autonomous-research-framework-via-chain-of-evidence/).
Its two requirements: **completeness** (every claim carries a recorded evidence
chain) and **correctness** (each chain genuinely supports its claim). The
framework's central finding is that verifiability comes from building evidence
chains *by construction*, not reconstructing them afterward: baseline systems
hallucinated up to 21% of their references, while building the chain alongside
the claim drove phantom references to zero.

So the ordering matters more than any single check:

1. **Never write a citation from memory.** Locate the source first, via
   `zotero-rag` for the local library or a real API lookup, then cite what you
   found. A DOI recalled from memory that happens to resolve is still ungrounded.
2. **Tag the claim as you write it** (see Step 1d). Retrofitting evidence tags
   onto a finished draft is exactly the post-hoc reconstruction the paper argues
   against, and it is where over-claiming survives.
3. **Run the audits before building.** They are a backstop, not the first check.

Set `CITEVERIFY_MAILTO` to your email once so Crossref and OpenAlex put you in
their polite pools (faster, higher limits):

```bash
export CITEVERIFY_MAILTO="you@example.com"
```

### Step 1c: Verify the bibliography (Reference Verification)

An AI-drafted paper can invent a DOI, pair a **real** DOI with a fabricated
title, cite a **retracted** paper, or supply a reference with no resolvable
identifier at all. All four pass a casual eye and a plain 200-OK check.

```bash
SCRIPTS="$HOME/.claude/skills/arxiv-pdf/scripts"
python3 "$SCRIPTS/verify_citations.py" refs.bib \
    --ledger paper.evidence.json --adjudicate review.jsonl
python3 "$SCRIPTS/verify_citations.py" --doi 10.1038/nature14539   # spot-check one
```

The script (standard library only, no API keys) mirrors the paper's Reference
Verification check: each entry is resolved against **Crossref, OpenAlex,
Semantic Scholar, DataCite, and arXiv** using DOI, arXiv ID, **and title**.
Statuses:

- **VERIFIED** - resolves, and the resolved title matches what you cited. Good.
- **MISMATCH** - the identifier is real but points at a *different* paper. This
  is citation gaming, deliberate or not. Fix the DOI or the title.
- **PHANTOM-DOI / PHANTOM-ARXIV** - the identifier resolves nowhere. Almost
  certainly invented. Any titles printed alongside are "did you mean" hints from
  a title search, never a pass.
- **PHANTOM-TITLE** - no identifier given, and a title search across three
  indexes found nothing close. Treat as invented.
- **RETRACTED** - the paper exists but has been retracted. Do not cite it as a
  live result. Detected via OpenAlex `is_retracted`, Crossref `update-to`, and
  the "RETRACTED:" title prefix publishers use.
- **NO-ID** - the entry has no DOI, no arXiv ID, and no title. Unverifiable as
  written, so it is a failure rather than a skip.
- **REVIEW** - resolves, but the title similarity is in the ambiguous band. The
  script deliberately does *not* decide these with a threshold; it writes them to
  the `--adjudicate` queue for you to judge. **Read `review.jsonl` and rule on
  each entry**: FAITHFUL, GAMED (real record, fabricated description), or
  DIFFERENT_PAPER, naming the field that decided it.
- **API-BLOCKED** - every source was unreachable. Not a pass. Check the network,
  then use the browser fallback below.

`--ledger paper.evidence.json` caches the resolved record for every reference.
That file *is* the citation half of the evidence chain: it records what each
reference resolved to and when, so the bibliography is traceable to real lookups
rather than to model memory.

The script exits nonzero if anything is not clean, so it can gate the build.

### Step 1d: Verify the claims (Claim Verification)

Reference verification proves a paper **exists**. It says nothing about whether
that paper **supports the sentence citing it**, which is the correctness half of
CoE. Bind each claim to its evidence with an inline `<!--ev ... -->` tag:

```markdown
Interface trap density falls by roughly 40% after the ALD alumina passivation [@wang2023].
<!--ev kind="citation" src="doi:10.1021/acsami.3c01234" zotero="ABCD1234"
        locator="p.4, Fig.3b"
        quote="the interface trap density decreased from 2.5e12 to 1.5e12 cm-2 eV-1" -->

The Ti 2p peak sits at 458.6 eV.
<!--ev kind="numeric" src="file:xps_fit_results.csv#row=Ti2p,col=BE" value="458.6" -->
```

Tags are HTML comments, so pandoc ignores them and `convert.sh` strips them
before typesetting. Then:

```bash
python3 "$SCRIPTS/verify_claims.py" paper.md --require-tags --entail entail.jsonl
```

Dispatch follows the paper's Claim Verifier ("numerical claims against evaluator
logs, citation claims against the bibliography"):

- **`kind="citation"`** - the `quote` must literally occur in the source full
  text. Text comes from an explicit `pdf=` path, or the Zotero PDF for
  `zotero=<itemKey>`, falling back to the Zotero index abstract. This check needs
  no model and is the strongest primitive available: **a fabricated supporting
  quote cannot survive a fuzzy match against the real PDF.**
- **`kind="numeric"`** - the value is re-read from the artifact file and compared
  (`.csv`/`.tsv` by row and column, `.json` by path, text by regex). Tolerance
  defaults to the significant figures of the stated value, so `458.6` implies
  +/- 0.05. Numbers in prose are never retyped from memory.
- **`--require-tags`** - flags any citation with no evidence tag at all. This is
  the completeness half of CoE.

Statuses: **QUOTE-VERIFIED**, **QUOTE-WEAK** (close but not verbatim, confirm the
wording), **QUOTE-FABRICATED** (the quote is not in the source; the claim is
unsupported), **QUOTE-UNCHECKED** (only an abstract was searchable, so nothing is
proven either way and it needs the full PDF or a manual check), **NUMERIC-OK**,
**NUMERIC-MISMATCH**, **ARTIFACT-MISSING**, **UNTAGGED**.

A verbatim quote proves the source *says* it. Only the entailment check proves it
*supports the claim*, so **read `entail.jsonl` and rule on each pair**:
SUPPORTED, OVERSTATED, or UNSUPPORTED.

### Reconciliation: restate conservatively, do not just delete

When a claim exceeds its evidence, the paper's Claim Verifier "reconciles claims
that exceed their evidence through conservative restatement rather than removal",
and removes only what cannot be supported at all. Apply that order:

1. **Source supports something weaker** - weaken the sentence to exactly what the
   evidence supports, and keep the citation. Deleting the citation here would
   turn a checkable overstatement into an unattributed one, which is worse.
2. **Source does not support the claim, but a real source does** - re-ground it
   and update both the sentence and the tag.
3. **Nothing supports it** - remove the claim.

Never silence a failure by deleting the evidence tag; that only removes the check.

**Browser fallback when the APIs are blocked.** Some publishers and networks
block programmatic access. When a reference lands on **API-BLOCKED**, confirm it
by hand through the Claude-in-Chrome browser extension:
open `https://doi.org/<doi>` and confirm it lands on the cited paper, or search
the exact title on Crossref (`search.crossref.org`) or Google Scholar and confirm
a real match. **Never ship a citation that neither the APIs nor the browser could
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

---

## Adaptation notes

Everything above runs as-is except two optional conveniences in the claim
verifier. Nothing here is required for reference verification.

**`verify_citations.py` is fully self-contained.** Standard library only, no API
keys, no local state. It queries public endpoints (Crossref, OpenAlex, Semantic
Scholar, DataCite, arXiv). Set `CITEVERIFY_MAILTO` to your own address to enter
the Crossref and OpenAlex polite pools; without it the script still works, just
under stricter rate limits.

**`verify_claims.py` needs source text from somewhere.** It resolves text in this
order:

1. `pdf="/path/to/paper.pdf"` on the evidence tag. This path is self-contained
   and is the one to use if you have no Zotero library.
2. `zotero="<itemKey>"`, which reads `~/Zotero/zotero.sqlite` (copied to temp
   first, since Zotero locks it while running) to map the item to its PDF in
   `~/Zotero/storage/`. Override the library location with `ZOTERO_DIR`.
3. `~/Zotero/claude-assistant-index.json`, the index built by the sibling
   [zotero-rag](../zotero-rag/) skill. This is **abstract scope only**, so a
   quote missing from it is reported UNCHECKED rather than fabricated.

If none of those exist, every citation tag reports **NO-SOURCE-TEXT**, which is a
failure rather than a silent pass. Text extraction prefers `pdftotext` (poppler)
and falls back to `pypdf`.

**`kind="numeric"` tags** point at whatever artifact files your own project
produces (`.csv`, `.tsv`, `.json`, or text with a regex). The examples reference
XPS fitting output; substitute your own.
