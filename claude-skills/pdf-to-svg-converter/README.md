# pdf-to-svg-converter (a Claude Code skill)

Analyze-then-convert pipeline for graphic-heavy PDFs: classifies pages, picks an extraction method, keeps annotations in page coordinates.

This folder is a **Claude Code skill**: drop it into `~/.claude/skills/` and Claude Code loads it when the trigger conditions in its frontmatter match. The skill itself lives in [`SKILL.md`](SKILL.md) - frontmatter naming it and describing when it activates, followed by the instructions Claude follows - plus whatever scripts, references, and templates the task needs. This is a public-safe copy of a personally used skill; anything that expects private local setup says so in a marked "Adaptation notes" section at the bottom of SKILL.md, and placeholders like `<vault>/` mark what to point at your own system.

Contents:

- `SKILL.md`
- `assets/`
- `references/`
- `scripts/`

Part of the [claude-skills](../README.md) section of the side-quests repo.
