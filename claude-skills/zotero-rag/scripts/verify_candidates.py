#!/usr/bin/env python3
"""
Verify a list of candidate papers against the local Zotero index.

Use case: "Does any paper in my 50-item download queue already exist in Zotero?"
Live BM25 search (the main `/zotero-rag` skill) is optimized for per-query precision
and suffers from 3 gotchas that cause false negatives in bulk verification:
  1. BM25 does not index the `authors` field
  2. Unicode diacritics in author names (Mäkinen, Sønderberg, Gómez, etc.)
  3. Title-phrasing mismatch (queue description ≠ Zotero title)

This script reads the raw index at `~/Zotero/claude-assistant-index.json`, normalizes
Unicode, and fuzzy-matches each candidate against every indexed paper using
year + title-keyword overlap + author-substring. It avoids all three gotchas.

## Usage

    python3 verify_candidates.py <candidates.json>

where candidates.json is a list of dicts:
    [
      {"label": "Smith 2024 Hf amide ALD",
       "title_keywords": "hafnium amide precursor carbon contamination ALD",
       "year": "2024",
       "author": "Smith"},
      ...
    ]

Output: tab-separated results, one line per candidate:
    <label>\t<best-match-title>\t<itemKey>\t<year>\t<authors>\t<score>

A score >= 0.5 is a candidate; score >= 0.9 is a strong match. Manual review
of the top-5 matches is still recommended because same-year-same-author papers
can collide.

## Programmatic use

    from verify_candidates import verify_batch, load_corpus
    corpus = load_corpus('/Users/<you>/Zotero/claude-assistant-index.json')
    results = verify_batch(corpus, [{"label":"...","title_keywords":"...","year":"...","author":"..."}])
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

DEFAULT_INDEX = Path.home() / 'Zotero' / 'claude-assistant-index.json'


def strip_accents(s: str) -> str:
    """Remove Unicode diacritics and lowercase. Handles Mäkinen → makinen, etc."""
    if not s:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()


def norm(s: str) -> str:
    """Normalize: lowercase, strip accents, collapse whitespace, remove punctuation."""
    s = strip_accents(s)
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def all_words(s: str) -> set:
    return set(norm(s).split())


def load_corpus(index_path=DEFAULT_INDEX):
    """Load Zotero index and deduplicate chunks by itemKey.

    Returns a list of tuples: (itemKey, title, authors, year, wordset)
    where wordset = normalized (title + authors + year) set of words.
    """
    with open(index_path) as f:
        idx = json.load(f)

    papers = {}
    for _, meta in idx['chunks']:
        k = meta['itemKey']
        if k not in papers:
            papers[k] = {
                'title': meta.get('title', ''),
                'authors': meta.get('authors', ''),
                'year': meta.get('year', ''),
            }

    corpus = []
    for key, meta in papers.items():
        combined = f"{meta['title']} {meta['authors']} {meta['year']}"
        corpus.append((key, meta['title'], meta['authors'], meta['year'], all_words(combined)))
    return corpus


def match_one(corpus, title_keywords, year=None, author=None, min_score=0.5):
    """Return (itemKey, title, authors, year, score) for best match, or None if score < min_score.

    Scoring: Jaccard-like overlap between candidate keywords and each indexed paper's wordset,
    plus a +0.5 bonus for accent-stripped author substring match.
    """
    kw_set = all_words(title_keywords)
    if year:
        kw_set.add(str(year))
    if not kw_set:
        return None

    best = None
    best_score = 0.0
    for key, t, a, y, wordset in corpus:
        overlap = len(kw_set & wordset)
        score = overlap / len(kw_set)
        if author and strip_accents(author) in strip_accents(a):
            score += 0.5
        if score > best_score and score >= min_score:
            best_score = score
            best = (key, t, a, y, score)
    return best


def verify_batch(corpus, candidates, min_score=0.5):
    """Verify a list of candidate-dicts against the corpus.

    Each candidate dict should have: label, title_keywords, year (optional), author (optional).
    Returns list of (label, match_tuple_or_None) in input order.
    """
    results = []
    for c in candidates:
        m = match_one(corpus,
                      c.get('title_keywords', ''),
                      c.get('year'),
                      c.get('author'),
                      min_score=min_score)
        results.append((c.get('label', ''), m))
    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        candidates = json.load(f)

    corpus = load_corpus()
    print(f"# Loaded {len(corpus)} unique Zotero papers", file=sys.stderr)

    results = verify_batch(corpus, candidates)
    print("label\ttitle\titemKey\tyear\tauthors\tscore")
    for label, m in results:
        if m:
            key, t, a, y, s = m
            print(f"{label}\t{t[:100]}\t{key}\t{y}\t{a}\t{s:.2f}")
        else:
            print(f"{label}\t-- NOT FOUND --\t\t\t\t")


if __name__ == '__main__':
    main()
