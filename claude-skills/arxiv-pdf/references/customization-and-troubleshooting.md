# Template Design Decisions, Customization, and Troubleshooting

## Template Design Decisions

### Visual Signature of arXiv Preprints

The template reproduces these characteristic features:
1. **Single-column layout** - standard for manuscript/preprint format
2. **Latin Modern fonts** - the modern, scalable version of Computer Modern (LaTeX's default)
3. **11pt body text** - slightly larger than journal 10pt for readability
4. **1-inch margins** - clean, generous whitespace
5. **Centered title block** - title in `\LARGE\bfseries`, authors bold, affiliations italic
6. **Indented abstract** - in a `minipage` at 92% text width
7. **Numbered sections** - `\section` bold large, `\subsection` bold normal, `\subsubsection` italic
8. **Page numbers only** - no running headers (arXiv adds its own watermark)
9. **Green citations, blue links** - standard academic hyperlink coloring
10. **`booktabs` tables** - professional rules instead of grid lines

### What the Template Does NOT Do

- Does not add the arXiv watermark (arXiv adds this server-side)
- Does not enforce a specific bibliography style (user's choice)
- Does not restrict to double-column (that's journal format, not preprint)
- Does not require REVTeX (works with any field, not just physics)

## Customization Options

### Switch to Times Roman Font

```yaml
fontfamily: newtxtext
header-includes: |
  \usepackage{newtxmath}
```

### Double-Column Journal Layout

```yaml
header-includes: |
  \usepackage{multicol}
  \begin{multicols}{2}
# And add to the end of your markdown:
```{=latex}
\end{multicols}
```
```

### APS/Physical Review Style

For physics papers targeting APS journals, consider using REVTeX directly:
```yaml
header-includes: |
  % Note: This overrides the article class. For full REVTeX support,
  % write a .tex file directly rather than using this template.
```

### Custom Section Numbering (Roman Numerals)

```yaml
header-includes: |
  \renewcommand{\thesection}{\Roman{section}}
  \renewcommand{\thesubsection}{\Alph{subsection}}
```

### Line Numbers (for review drafts)

```yaml
header-includes: |
  \usepackage{lineno}
  \linenumbers
```

## Troubleshooting

### "Missing $ inserted" or math errors
- Ensure all `$` are paired. In tables, use `\$` for literal dollar signs.
- Special characters in text: `%`, `&`, `#`, `_` need escaping (`\%`, `\&`, `\#`, `\_`) in raw LaTeX, but pandoc handles this in normal markdown.

### Figures not found
- Use relative paths from the `.md` file location
- Set `graphics-path` in frontmatter if figures are in a subdirectory
- Pandoc's `--resource-path` is set by convert.sh to the input file's directory

### Bibliography not rendering
- Ensure `.bib` file path is correct (relative to the .md file)
- Check that `bibliography:` is set in frontmatter
- For pandoc citeproc: citations use `[@key]` syntax
- For natbib: set `natbib: true` and use `\cite{key}` in raw LaTeX

### "File not found: arxiv-preprint.latex"
- Use the full path to the template (the `templates/` directory bundled with this skill):
  ```bash
  --template="$HOME/.claude/skills/arxiv-pdf/templates/arxiv-preprint.latex"
  ```

### PDF looks different from expected
- Run `pdflatex --version` to verify TeX Live is installed
- Check pandoc version: `pandoc --version` (v2.10+ recommended)
- For font issues, ensure `lmodern` package is installed: `kpsewhich lmodern.sty`
