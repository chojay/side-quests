# arxiv-pdf (a Claude Code skill)

Markdown with YAML frontmatter to an arXiv-style preprint PDF (or .tex) via pandoc and a bundled LaTeX template, with Chain-of-Evidence citation and claim verification gating the build.

This folder is a **Claude Code skill**: drop it into `~/.claude/skills/` and Claude Code loads it when the trigger conditions in its frontmatter match. The skill itself lives in [`SKILL.md`](SKILL.md) - frontmatter naming it and describing when it activates, followed by the instructions Claude follows - plus whatever scripts, references, and templates the task needs. This is a public-safe copy of a personally used skill; anything that expects private local setup says so in a marked "Adaptation notes" section at the bottom of SKILL.md, and placeholders like `<vault>/` mark what to point at your own system.

## Verification: the interesting part

An AI-drafted paper does not usually fail by getting the LaTeX wrong. It fails by inventing a DOI, attaching a real DOI to a fabricated description, citing a retracted paper, or citing a real paper that does not actually support the sentence citing it. This skill implements the citation-relevant parts of the **Chain-of-Evidence (CoE)** framework to catch each of those:

- Paper: [ScientistOne: Towards Human-Level Autonomous Research via Chain-of-Evidence](https://arxiv.org/abs/2605.26340) (arXiv:2605.26340)
- Blog: [Science One Framework: A verifiable autonomous research framework via Chain-of-Evidence](https://research.google/blog/science-one-framework-a-verifiable-autonomous-research-framework-via-chain-of-evidence/), Google Research

CoE requires **completeness** (every claim carries a recorded evidence chain) and **correctness** (each chain genuinely supports its claim). The reported result is that baseline systems hallucinated up to 21% of their references, while building the chain alongside the claim rather than reconstructing it afterward drove phantom references to zero.

Two scripts, split along the distinction that matters:

**`scripts/verify_citations.py` - does the reference exist and describe the right paper?**
Resolves every bibliography entry against **Crossref, OpenAlex, Semantic Scholar, DataCite, and arXiv** using DOI, arXiv ID, **and title**, so entries with no identifier are checked instead of being silently skipped. Flags `PHANTOM-DOI` (resolves nowhere), `MISMATCH` (real identifier, different paper), `PHANTOM-TITLE`, `RETRACTED` (via OpenAlex `is_retracted`, Crossref `update-to`, and the "RETRACTED:" title prefix), and `NO-ID`. Near-misses in the ambiguous similarity band are not decided by a threshold; they go to a JSONL queue for the model to rule on, which is where citation gaming actually hides. Standard library only, no API keys.

**`scripts/verify_claims.py` - does that paper actually say what the sentence claims?**
Claims carry inline evidence tags binding them to a specific artifact:

```markdown
Interface trap density falls by roughly 40% after the ALD alumina passivation [@wang2023].
<!--ev kind="citation" src="doi:10.1021/acsami.3c01234" zotero="ABCD1234"
        quote="the interface trap density decreased from 2.5e12 to 1.5e12 cm-2 eV-1" -->

The Ti 2p peak sits at 458.6 eV.
<!--ev kind="numeric" src="file:xps_fit_results.csv#row=Ti2p,col=BE" value="458.6" -->
```

Citation claims require the quote to literally occur in the source PDF; numeric claims are re-read from the artifact file so numbers in prose are never retyped from memory. Tags are HTML comments, and `convert.sh` strips them before typesetting.

The quote check is the strongest primitive here and uses **no model at all**: a fabricated supporting quote cannot survive a fuzzy match against the real PDF.

## AI-assisted build notes

Two bugs worth recording, both caught by a deliberately poisoned test bibliography rather than by reading the code:

**A fallback laundered a hard failure into a soft one.** A fabricated DOI correctly 404'd at every resolver, then the title-search fallback found a loosely-related real paper and rescued the entry from `PHANTOM` into the softer `REVIEW` status. Resolution now records *how* it succeeded, and a supplied identifier that resolves nowhere stays a hard failure no matter what a later title search turns up. A related asymmetry: a title search always returns its best effort, so a weak best-effort hit means "no such paper", not "borderline", and title-derived matches are held to a higher floor than identifier-derived ones.

**Quote verification needed contiguity, not overlap.** `difflib.get_matching_blocks()` sums every matching fragment including scattered three-character ones, so a fabricated quote assembled from plausible domain vocabulary ("carbon contamination", "room temperature", "deposition cycle") scored 0.65 against a real paper on confetti alone. Counting only runs of at least 15 characters separated the same test pair cleanly: 1.00 for a genuine verbatim quote, 0.21 for the fabrication.

A third decision that is not a bug but matters more than either: the Zotero index this skill can read holds abstracts, not full text. A quote missing from an abstract proves nothing about the paper body, so that case reports `QUOTE-UNCHECKED`, never `QUOTE-FABRICATED`. `API-BLOCKED` and `NO-ID` are likewise failures rather than skips. A check that could not run is not a check that passed.

Design rationale and the full mapping from the paper's four integrity checks to what is and is not implemented here: [`references/chain-of-evidence.md`](references/chain-of-evidence.md).

Contents:

- `SKILL.md`
- `scripts/` - `verify_citations.py` (does the reference exist?), `verify_claims.py` (does it support the claim?)
- `references/` - including `chain-of-evidence.md`, the verification design notes
- `examples/`
- `templates/`

Part of the [claude-skills](../README.md) section of the side-quests repo.
