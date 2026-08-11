---
name: zotero-rag
description: >-
  Searches the user's Zotero research library using hybrid BM25 + semantic RAG
  and returns relevant paper chunks with citations for answering research
  questions. Use when the user asks to "search my papers for...", "in my Zotero
  library...", "what do my papers say about...", "find in my research...",
  "check my papers for...", "from my Zotero...", "according to my papers...",
  "in my library...", or otherwise wants an answer grounded in their own paper
  collection. Also use for bulk verification of candidate paper lists ("which
  of these papers are already in my Zotero?") via the bundled
  verify_candidates.py helper. Supports keyword, semantic, and hybrid search
  modes plus collection, tag, and field filters. Do not use for
  general-knowledge or web-search questions that never mention the user's
  papers or library.
---

# Zotero RAG Search

## Overview

This skill searches your indexed Zotero library using **hybrid BM25 + semantic search** with synonym expansion and returns relevant paper chunks for answering research questions. It reads from:
- BM25 index: `~/Zotero/claude-assistant-index.json`
- Embeddings: `~/Zotero/claude-assistant-embeddings.sqlite` (optional, for semantic search)

## Quick Start

```bash
# Hybrid search (default) - combines BM25 + semantic for best results
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "high-k dielectric reliability" 10

# Keyword-only search (BM25)
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "high-k dielectric reliability" 10 --mode keyword
```

## Workflow

1. **Extract search query** from user's request
2. **Run search script** with the query (default mode: hybrid)
3. **Parse JSON results** containing paper chunks and metadata
4. **Answer the question** using the retrieved context
5. **Cite sources** using the format below

## Response Format

When answering based on paper search results, use this format:

```markdown
Based on your papers:

[Your answer synthesizing information from the retrieved chunks]

**Sources:**
1. [Author, Year] - Paper Title
2. [Author, Year] - Paper Title
```

## Search Script Usage

```bash
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "<query>" [limit] [options]
```

### Arguments

- `<query>`: Search terms (required)
- `[limit]`: Number of results (default: 10, max: 25)

### Options

- `--mode keyword|semantic|hybrid`: Search mode (default: hybrid)
  - `keyword`: BM25 only (exact term matching with synonyms)
  - `semantic`: Cosine similarity only (requires embeddings + Zotero running)
  - `hybrid`: RRF merge of BM25 + semantic (best quality, falls back to keyword if semantic unavailable)
- `--collection "Name"`: Filter results to a specific Zotero collection
- `--tag "keyword"`: Filter results to items with a specific tag
- `--field title|abstract|body`: Restrict search to a specific section type

### Examples

```bash
# Hybrid search (default) - finds papers even with vocabulary mismatch
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "dielectric breakdown" 10

# Keyword-only search (BM25)
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "ALD nucleation" 10 --mode keyword

# Semantic-only search (embedding similarity)
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "how gate oxides degrade" --mode semantic

# Search with element symbols (preserved by tokenizer)
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "Cu diffusion barrier"

# Search with abbreviation expansion (HKMG → high-k metal gate)
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "HKMG reliability"

# Filter by field type
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "etch selectivity" --field title

# Filter by collection
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "ALD" --collection "Interface Engineering"

# Filter by tag
python ~/.claude/skills/zotero-rag/scripts/search_zotero.py "dopant profiling" --tag "SIMS"
```

**Output format:**
```json
{
  "query": "dielectric breakdown",
  "mode": "hybrid",
  "expanded_terms": [
    {"term": "dielectric", "weight": 1.0},
    {"term": "breakdown", "weight": 1.0}
  ],
  "results": [
    {
      "title": "Paper Title",
      "authors": "Smith et al.",
      "year": "2024",
      "text": "Chunk text content...",
      "score": 0.85,
      "item_key": "ABC12345",
      "zotero_url": "zotero://select/library/items/ABC12345",
      "section": "body"
    }
  ],
  "total_indexed": 2934,
  "total_matches": 42
}
```

## Features

### Hybrid Search
Combines BM25 keyword search with semantic embedding similarity using Reciprocal Rank Fusion (RRF):
- **BM25**: Finds exact term matches, boosted with synonym expansion
- **Semantic**: Finds conceptually similar content even with different vocabulary (e.g., "film conformality" finds "step coverage" papers)
- **RRF merge**: Rank-based fusion (k=60) that doesn't require score normalization

Semantic search requires:
1. Embeddings generated in Zotero (Settings → Claude Assistant → Generate Embeddings)
2. Zotero running (for query embedding via HTTP endpoint at port 23119)

If either is unavailable, hybrid mode gracefully falls back to keyword-only search.

### Synonym Expansion
Queries are automatically expanded with domain-specific synonyms:
- Element symbols ↔ names: Hf↔hafnium, Cu↔copper, Al↔aluminum, etc.
- Abbreviations ↔ full terms: HKMG↔high-k metal gate, ALD↔atomic layer deposition, RIE↔reactive ion etching, etc.
- Expanded terms are weighted at 0.5× to prioritize exact matches

### Scientific Token Preservation
The tokenizer preserves short but important scientific terms that were previously dropped:
- Element symbols: Hf, Cu, Al, Au, Ag, Zn, Mg, Na, K, Fe, Ni, Ti, Zr, etc.
- Units and notation: eV, nm, mA, 2D, 3D, D*
- Common English stopwords are removed instead of filtering by length

### Field-Weighted Scoring
When section metadata is available (index v2+):
- Title matches: 3.0× boost
- Abstract matches: 2.0× boost
- Body matches: 1.0× (baseline)

### Zotero Deep Links
Each result includes a `zotero_url` field (e.g., `zotero://select/library/items/ITEMKEY`) that can be used to open the paper directly in Zotero.

### Pickle Cache
Parsed index and embeddings are cached as `.pkl` files for faster subsequent loads (~3-5× faster startup).

## Index Information

- **BM25 Index:** `~/Zotero/claude-assistant-index.json`
- **Embeddings:** `~/Zotero/claude-assistant-embeddings.sqlite`
- **Format:** JSON with BM25 data (v2) + SQLite with Float32 BLOB embeddings
- **Embedding model:** all-MiniLM-L6-v2 (384 dimensions)
- **Updates:** Re-index in Zotero extension to update

## Troubleshooting

**"Index file not found"**
- Ensure Zotero Claude Assistant extension has indexed your library
- Check that `~/Zotero/claude-assistant-index.json` exists

**"No results found"**
- Try broader search terms
- Try `--mode semantic` for vocabulary-mismatched queries
- Check the `expanded_terms` in output to see how your query was interpreted
- Check if papers on this topic are in your library
- Re-index if you recently added new papers

**Hybrid mode falls back to keyword**
- Check that `~/Zotero/claude-assistant-embeddings.sqlite` exists
- Ensure Zotero is running (needed for query embedding via HTTP)
- Generate embeddings: Zotero → Settings → Claude Assistant → Generate Embeddings

**Results seem outdated**
- Re-index in Zotero: Settings → Claude Assistant → Re-index Everything
- Delete `~/Zotero/claude-assistant-index.pkl` to force fresh cache rebuild
- Delete `~/Zotero/claude-assistant-embeddings.emb.pkl` to refresh embedding cache

**Stale pickle cache**
- Delete `~/Zotero/claude-assistant-index.pkl` - it will be rebuilt on next search
- Delete `~/Zotero/claude-assistant-embeddings.emb.pkl` - same for embeddings

## Known Gotchas

**Author name searches fail (two causes):**

1. **BM25 does not index the `authors` field.** The BM25 index tokenizes only the `text` field (abstract + body). Searching "Kimura" returns 0 results even though the paper is indexed with `authors: "Kimura et al."`. The author name simply isn't in the searchable text.
   - *Workaround:* Search by distinctive title phrases or unique concepts, not author names.

2. **Unicode diacritics cause false negatives when checking the raw index.** Zotero stores author names with full Unicode (e.g., "Müller", "Gómez", "Mäkinen", "Sønderberg"). Python string comparison treats "Gómez" ≠ "Gomez" and "Sønderberg" ≠ "Sonderberg". This repeatedly causes papers to be falsely reported as "not in the library" when they are actually indexed.
   - *Workaround:* When writing Python scripts to verify papers against the index, always normalize Unicode before comparing: `unicodedata.normalize('NFD', s)` and strip combining marks. Example:
     ```python
     import unicodedata
     def strip_accents(s):
         return ''.join(c for c in unicodedata.normalize('NFD', s)
                        if unicodedata.category(c) != 'Mn').lower()
     ```
   - *Confirmed pattern:* multiple indexed papers whose author names contain diacritics were repeatedly reported as "not in library" until accent-stripped comparison was used. Any library with international author names will hit this.

**Title-phrasing mismatch causes BM25 misses even for papers that are indexed.** The user's mental framing of a paper (their search keywords) often differs from the actual Zotero title, especially for papers they haven't read. BM25 is literal - it can't bridge the gap. Illustrative examples (invented, but matching the observed failure shape):
- User searches "Hf precursor carbon contamination ALD" → actual title phrases it as "Impact of the Coreactant on Carbon Incorporation from a Hafnium Amide Precursor" → MISSED
- User searches "low thermal budget high-k anneal leakage" → actual title phrases it as "Suppressed Gate Leakage in HfO2 Stacks Crystallized below 500 C" → MISSED
- *Workaround:* For bulk-verification workflows (e.g., "does any paper in my 50-item candidate list exist in Zotero?"), prefer **direct index parsing with fuzzy year+keyword+author matching** over live BM25 search. The helper script at `~/.claude/skills/zotero-rag/scripts/verify_candidates.py` implements this pattern.

**Semantic-mode silently falls back to keyword-only when Zotero is not running.** The hybrid (BM25+semantic) mode needs Zotero's local HTTP endpoint (port 23119) to embed queries. In sandboxed agent sessions or when Zotero is closed, the mode falls back to keyword-only **without any error**, just a note in the output's `mode` field: `"keyword (fallback)"`. This compounds the author-field gotcha (#1) and the title-phrasing gotcha above - the semantic layer that would bridge paraphrased titles is silently absent.
- *Workaround:* always inspect `result["mode"]` in the JSON output. If it says `"keyword (fallback)"`, expect elevated false-negative rates and consider using `verify_candidates.py` for anything requiring recall.

**Bottom line:** Never trust author-name-based verification without accent-stripping. Always verify by distinctive title keywords as the primary method. For bulk verification of long candidate lists, use direct index parsing via `verify_candidates.py`, not live BM25 search.

## Helper: Bulk verification against the index

For the common use case "I have a list of candidate papers - which ones are already in my Zotero library?", the main BM25 search is the wrong tool (it's optimized for precision on a query, not recall over a list). Use the companion script instead:

```bash
python3 ~/.claude/skills/zotero-rag/scripts/verify_candidates.py candidates.json
```

`candidates.json` is a list of dicts with `label`, `title_keywords`, optional `year`, optional `author`:

```json
[
  {"label": "Smith 2024 Hf amide ALD",
   "title_keywords": "hafnium amide precursor carbon contamination ALD",
   "year": "2024",
   "author": "Smith"},
  {"label": "Åberg 2020 alkoxide precursor review",
   "title_keywords": "tert butoxide precursors transition metal ALD",
   "year": "2020",
   "author": "Aberg"}
]
```

Note the second entry: pass the author name accent-stripped ("Aberg" for "Åberg") or not - the script normalizes both sides before matching.

Output is tab-separated, one line per candidate, with best-match title, item key, and confidence score. The script handles all three of the gotchas above:
- Reads the raw index directly (no BM25 mediation)
- Unicode-normalizes both sides
- Fuzzy-matches year + keyword overlap + author substring

The script is also importable for programmatic use (`from verify_candidates import verify_batch, load_corpus`).

---

## Adaptation Notes (added for the public copy)

This skill is published as a reference implementation. As-is, it hard-depends on a **custom "Claude Assistant" Zotero extension that is NOT included in this repo**. That private extension is what:

1. Builds the BM25 index at `~/Zotero/claude-assistant-index.json`
2. Generates the embeddings database at `~/Zotero/claude-assistant-embeddings.sqlite`
3. Serves the query-embedding HTTP endpoint at `http://127.0.0.1:23119/claude-assistant/embed`

Without those three inputs, the search scripts have nothing to search. To adapt the skill to your own setup, produce compatible artifacts with any indexer of your choice:

**Index file schema** (`claude-assistant-index.json`):
- `chunks`: array of `[chunkId, metadata]` pairs, where `metadata` includes `title`, `authors`, `year`, `text`, `itemKey`, `chunkIndex`, and optionally `section` (`title` | `abstract` | `body`), `collections` (list of names), `tags` (list of strings)
- `bm25Index`: a JSON **string** containing `{documents: [{id, length, termFreqs: [[term, count], ...]}], documentFreqs: [[term, docCount], ...], avgDocLength, totalDocs}`
- `indexedItemKeys`: array of Zotero item keys (used only for the `total_indexed` count)

**Embeddings database schema** (`claude-assistant-embeddings.sqlite`):
- Table `embeddings(chunk_id TEXT, embedding BLOB)` where the BLOB is a little-endian Float32 array (384 dims for all-MiniLM-L6-v2, L2-normalized so cosine similarity reduces to a dot product)

**Embed endpoint contract**: `POST {"text": "..."}` returns `{"embedding": [float, ...]}` matching the stored embedding space. If you cannot serve one, keyword mode still works; hybrid/semantic modes fall back to keyword automatically.

`verify_candidates.py` needs only the JSON index (no embeddings, no endpoint). Both scripts are Python standard library only - no pip installs required.
