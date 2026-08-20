# Chain-of-Evidence citation verification

The two verification scripts in this skill implement the citation-relevant parts
of the Chain-of-Evidence (CoE) framework from:

- **Paper**: [ScientistOne: Towards Human-Level Autonomous Research via Chain-of-Evidence](https://arxiv.org/abs/2605.26340) (arXiv:2605.26340, May 2026)
- **Blog**: [Science One Framework: A verifiable autonomous research framework via Chain-of-Evidence](https://research.google/blog/science-one-framework-a-verifiable-autonomous-research-framework-via-chain-of-evidence/), Google Research

CoE states two requirements: **completeness**, every claim carries a recorded
evidence chain, and **correctness**, each chain genuinely supports its claim.
The reported result is that baseline systems hallucinated up to 21% of their
references while a system that builds evidence chains *by construction* reached
zero phantom references.

## What was ported, and what was not

The paper's CoE Integrity Audit has four checks. Only some map onto a
Markdown-to-PDF pipeline:

| Paper check | Ported | How |
|---|---|---|
| I3 Reference Verification | Yes, fully | `verify_citations.py` |
| Claim Verifier (drafting-time) | Yes, adapted | `verify_claims.py` evidence tags |
| I1 Score Verification | Yes, reduced | `kind="numeric"` tags re-read local artifact files instead of re-running experiment code |
| I2 Specification Violation | No | Concerns ML agents gaming benchmarks; no analogue here |
| I4 Method-Code Alignment | No | Same reason |

The paper's Problem Investigator builds a citation graph from the Semantic
Scholar API and reads up to 100 full-text PDFs per topic, so that "every
reference originates from a Semantic Scholar API call whose result is cached in
the evidence chain". The local analogue is the user's own Zotero library, which
supplies exactly the thing that makes support-checking possible: full text on
disk. `--ledger paper.evidence.json` is the cache half of that idea.

## Design decisions worth knowing

### Existence checking and support checking are different problems

The original version of this skill only asked "does this DOI resolve, and does
its title match?". That is necessary and not close to sufficient. A reference can
resolve perfectly and still fail to support the sentence citing it. Splitting the
work into two scripts keeps the distinction visible:

- `verify_citations.py` answers **does this reference exist and describe the right paper**
- `verify_claims.py` answers **does that paper actually say what the sentence claims**

### The script decides what is decidable; the LLM gets the rest

Resolution, exact matching, and thresholding are cheap and deterministic, so the
scripts own them and stay standard-library only. Genuinely ambiguous cases are
written to a JSONL queue (`--adjudicate`, `--entail`) as structured data for the
model to rule on. This is how the paper's "An LLM cross-checks the full bib entry
against returned records to catch near-misses and citation gaming" is realized
without adding an API key or a dependency: the judgment happens where the model
already is.

The ambiguous band is deliberate. Deciding a 0.6 title similarity with a constant
cannot distinguish a subtitle change from a fabricated description, and that is
precisely where citation gaming hides.

### A fallback must never launder a hard failure

First implementation bug, caught by a poisoned test bib. A fabricated DOI
correctly failed at every resolver, then the title-search fallback found a
loosely-related real paper and the entry was rescued from PHANTOM into the softer
REVIEW status. Resolution now records **how** it succeeded, and a supplied
identifier that resolves nowhere is a hard failure regardless of what a later
title search turns up. Title-search results in that case are printed only as
"did you mean" hints.

A related asymmetry: a title search always returns its best effort, so a weak
best-effort hit means "no such paper", not "borderline match". Title-derived
resolution is held to a higher floor (0.60) than identifier-derived resolution
(0.35).

### Quote verification depends on contiguity, not overlap

Second implementation bug. `difflib.get_matching_blocks()` sums every matching
fragment including scattered 3-character ones, so a fabricated quote assembled
from plausible domain vocabulary ("carbon contamination", "room temperature",
"deposition cycle") scored 0.65 against a real paper on the strength of confetti
alone. Only matching runs of at least 15 characters now count toward coverage. On
the same test pair the scores separated cleanly: 1.00 for a genuine verbatim
quote, 0.21 for the fabrication.

This check is the strongest primitive in the skill and it uses no model at all. A
fabricated supporting quote cannot survive a fuzzy match against the real PDF.

### Absence of evidence is not evidence of absence

The Zotero index at `~/Zotero/claude-assistant-index.json` holds titles and
abstracts, not full text (median chunk 858 characters). A quote missing from an
abstract proves nothing about the paper body, so that case reports
**QUOTE-UNCHECKED**, never QUOTE-FABRICATED. Full text comes from the actual PDF
via the `itemAttachments` table in `zotero.sqlite` (copied first, since Zotero
holds a lock while running) and `pdftotext`, cached under
`~/.cache/arxiv-pdf-claims/`.

Similarly, **API-BLOCKED** and **NO-ID** are failures rather than skips. A check
that could not run is not a check that passed.

### Restate conservatively rather than delete

The paper "reconciles claims that exceed their evidence through conservative
restatement rather than removal". The earlier version of this skill said to
"remove or replace" a bad citation, which is the wrong default: deleting a
citation whose source is real but oversold converts a checkable overstatement
into an unattributed one. Weaken the sentence to what the evidence supports and
keep the citation; remove only what nothing supports.

### Ordering is the actual mechanism

The paper's own framing is that its system "instantiates the CoE framework by
construction" rather than reconstructing evidence chains afterward. Running these
scripts as a pre-build gate is a backstop. The behavior that matters is grounding
each citation before writing it and tagging each claim as it is written.
Retrofitting tags onto a finished draft reproduces the failure mode the framework
was designed to prevent.
