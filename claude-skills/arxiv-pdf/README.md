# arxiv-pdf (a Claude Code skill)

Markdown with YAML frontmatter to an arXiv-style preprint PDF (or .tex) via pandoc and a bundled LaTeX template.

This folder is a **Claude Code skill**: drop it into `~/.claude/skills/` and Claude Code loads it when the trigger conditions in its frontmatter match. The skill itself lives in [`SKILL.md`](SKILL.md) - frontmatter naming it and describing when it activates, followed by the instructions Claude follows - plus whatever scripts, references, and templates the task needs. This is a public-safe copy of a personally used skill; anything that expects private local setup says so in a marked "Adaptation notes" section at the bottom of SKILL.md, and placeholders like `<vault>/` mark what to point at your own system.

It also verifies citations before building: `scripts/verify_citations.py` resolves every DOI against Crossref and DataCite (and arXiv IDs against the arXiv API), and when the `.bib` gives a title it checks the resolved title matches - catching both invented DOIs and the "real DOI, wrong paper" case an AI draft can produce. Blocked or title-only references fall back to a manual browser check.

Contents:

- `SKILL.md`
- `scripts/` - `verify_citations.py` (citation existence check)
- `examples/`
- `references/`
- `templates/`

Part of the [claude-skills](../README.md) section of the side-quests repo.
