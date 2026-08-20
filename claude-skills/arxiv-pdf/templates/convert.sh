#!/usr/bin/env bash
#
# convert.sh - Convert Markdown to arXiv-style PDF (or .tex) via Pandoc
#
# Usage:
#   ./convert.sh input.md [output.pdf]     # Markdown → PDF
#   ./convert.sh input.md output.tex       # Markdown → LaTeX source (for arXiv upload)
#
# If output is omitted, produces input.pdf in the same directory.
# If output ends in .tex, generates LaTeX source instead of PDF.
# Reads YAML frontmatter from the .md file for all metadata.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${SCRIPT_DIR}/arxiv-preprint.latex"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 input.md [output.pdf|output.tex]"
  echo ""
  echo "  .pdf output  - compile to PDF (default)"
  echo "  .tex output  - generate LaTeX source for arXiv submission"
  exit 1
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.md}.pdf}"
INPUT_DIR="$(cd "$(dirname "$INPUT")" && pwd)"

if [[ ! -f "$INPUT" ]]; then
  echo "Error: $INPUT not found"
  exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Error: Template not found at $TEMPLATE"
  exit 1
fi

# Detect bibliography file from YAML frontmatter
BIB_FLAG=""
if grep -q '^bibliography:' "$INPUT" 2>/dev/null; then
  BIB_FLAG="--citeproc"
fi

# Detect natbib mode (skip citeproc if natbib is used, let LaTeX handle it)
if grep -q '^natbib: true' "$INPUT" 2>/dev/null; then
  BIB_FLAG="--natbib"
fi

# Detect pandoc-crossref
CROSSREF_FLAG=""
if command -v pandoc-crossref &>/dev/null; then
  CROSSREF_FLAG="--filter pandoc-crossref"
fi

# Strip Chain-of-Evidence annotations before typesetting.
# Evidence tags (<!--ev ... -->) bind each claim to the artifact that supports
# it. They are HTML comments, so pandoc already ignores them, but the paper's
# Claim Verifier "strips all inline evidence annotations" from the final draft
# and doing it explicitly keeps them out of any HTML or Markdown target too.
SOURCE="$INPUT"
if grep -q '<!--[[:space:]]*ev[[:space:]]' "$INPUT" 2>/dev/null; then
  NTAGS=$(grep -c '<!--[[:space:]]*ev[[:space:]]' "$INPUT" || true)
  STRIPPED="${INPUT_DIR}/.$(basename "${INPUT%.md}").stripped.md"
  perl -0pe 's/<!--\s*ev\s.*?-->\s*//gs' "$INPUT" > "$STRIPPED"
  trap 'rm -f "$STRIPPED"' EXIT
  SOURCE="$STRIPPED"
  echo "Evidence:   stripped $NTAGS inline evidence tag(s) before typesetting"
  echo "            (verify them first: scripts/verify_claims.py \"$INPUT\")"
fi

echo "Converting: $INPUT -> $OUTPUT"
echo "Template:   $TEMPLATE"

if [[ "$OUTPUT" == *.tex ]]; then
  # Generate .tex source (for arXiv submission)
  # Use --natbib so \cite{} commands appear in the .tex (arXiv recompiles)
  if grep -q '^bibliography:' "$INPUT" 2>/dev/null; then
    BIB_FLAG="--natbib"
  fi
  pandoc "$SOURCE" \
    --template="$TEMPLATE" \
    --resource-path="$INPUT_DIR" \
    $CROSSREF_FLAG \
    $BIB_FLAG \
    --number-sections \
    -V colorlinks=true \
    -o "$OUTPUT"
  echo "Done: $OUTPUT"
  echo ""
  echo "For arXiv submission, upload:"
  echo "  - $OUTPUT"
  echo "  - Any .bib files referenced in frontmatter"
  echo "  - All figure files"
  echo "  - Compile locally first: pdflatex $OUTPUT && bibtex ${OUTPUT%.tex} && pdflatex $OUTPUT && pdflatex $OUTPUT"
else
  # Generate PDF directly
  pandoc "$SOURCE" \
    --template="$TEMPLATE" \
    --pdf-engine=pdflatex \
    --resource-path="$INPUT_DIR" \
    $CROSSREF_FLAG \
    $BIB_FLAG \
    --number-sections \
    -V colorlinks=true \
    -o "$OUTPUT"
  echo "Done: $OUTPUT"
fi
