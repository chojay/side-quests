# Claude Code Skills

Nine of the Claude Code skills I actually run, published as public-safe copies. A skill is a folder with a `SKILL.md` (YAML frontmatter naming it and describing when it triggers, then instructions) plus whatever scripts, templates, and reference docs the task needs. Drop one into `~/.claude/skills/` and Claude Code loads it when its trigger conditions match. Together they are the automation layer of everything else in this repo: the CAD skill built the 3d-printing section, the research skills built the espresso knowledge base, and the paper skills feed the reading that shaped the medical projects.

Skills that expect private local setup (a vault path, a sibling tool, a browser extension) carry a clearly marked "Adaptation notes" section saying exactly what to supply; placeholders like `<vault>/` mark where to point them at your own system. The self-contained ones (academic-svg, arxiv-pdf, pdf-to-svg-converter) need only their declared pip dependencies; arxiv-pdf's citation verifier is standard library and keyless, and its claim verifier reads a Zotero library only if you point it at one. Sanitization for public release is documented in the notes rather than hidden.

| Skill | What it does |
|---|---|
| [3dp-skill](3dp-skill/) | Parametric CAD as code: build123d generation, trimesh validation, STL + Bambu-dialect 3MF export (reverse-engineered AMS preset binding), and a base64-embedded three.js viewer |
| [academic-svg](academic-svg/) | Publication-quality materials-science SVG figures: a 70+ color semantic palette extracted from Nature/Science figures, typography rules, worked examples, and templates |
| [arxiv-pdf](arxiv-pdf/) | Markdown with YAML frontmatter to arXiv-style preprint PDF (or .tex for actual submission) via pandoc and a bundled LaTeX template, with [Chain-of-Evidence](arxiv-pdf/references/chain-of-evidence.md) citation and claim verification gating the build; see the [worked example](arxiv-pdf/examples/) |
| [zotero-rag](zotero-rag/) | Dependency-free hybrid retrieval (BM25 + embeddings + reciprocal rank fusion) over a Zotero library index, with a Unicode-diacritics lesson learned the hard way |
| [obsidian-deep-research](obsidian-deep-research/) | Multi-phase research orchestration that writes findings into an Obsidian vault as interconnected notes with source-credibility scoring and confidence tiers |
| [youtube-obsidian-saver](youtube-obsidian-saver/) | YouTube to frontmattered Obsidian note: yt-dlp with player-client rotation and fallback, plus a token-budgeted chunked transcript retriever with 30-second overlap rebuilding |
| [youtube-summarizer](youtube-summarizer/) | Zero-code layer over the saver: treats its `--json` output as a data API, auto-classifies content type (recipe, tutorial, lecture), and emits structured notes with collapsed transcripts |
| [pdf-to-svg-converter](pdf-to-svg-converter/) | Analyze-then-convert pipeline for graphic-heavy PDFs: classifies pages by vector/raster content, then picks extraction method; hybrid mode keeps annotations in 1:1 page coordinates |
| [find-and-test-coupons](find-and-test-coupons/) | Fans out 6-8 parallel subagents to scrape coupon sources, then live-tests codes sequentially in the user's own browser with hard never-purchase, never-enter-payment guardrails |

## Why publish skills at all

Skills are where "AI-assisted workflow" stops being a slogan and becomes inspectable artifacts: trigger design, guardrails (the coupon tester's checkout-safety block, the CAD skill's mandatory watertight check), failure handling (the YouTube extractor's typed error messages and client rotation), and honest dependency declarations. They are also the most reusable thing here: every one of these is a folder you can adapt in an afternoon.

The one to read if you only read one: arxiv-pdf's [Chain-of-Evidence verification](arxiv-pdf/#verification-the-interesting-part), which implements the citation-relevant parts of Google Research's [Science One framework](https://research.google/blog/science-one-framework-a-verifiable-autonomous-research-framework-via-chain-of-evidence/) ([arXiv:2605.26340](https://arxiv.org/abs/2605.26340)). It separates two questions that are easy to conflate: does this reference exist, and does that paper actually say what the sentence citing it claims. The second one is checked by requiring a verbatim quote to occur in the source PDF, which needs no model at all.

Two engineering details worth clicking into: the 3dp-skill's [3MF export notes](3dp-skill/references/3mf-export.md) document the undocumented Bambu `bbs_3mf` metadata dialect needed for one-click dual-nozzle prints, and the saver's [chunked retriever](youtube-obsidian-saver/scripts/chunked_transcript_retriever.py) walks transcript entries backwards to rebuild time-based overlap at every chunk boundary so long videos summarize without losing spoken content at the seams.
