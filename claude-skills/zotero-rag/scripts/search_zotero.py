#!/usr/bin/env python3
"""
Zotero RAG Search - BM25 + Semantic hybrid search over indexed Zotero library
Usage: python search_zotero.py "query" [limit] [--mode keyword|semantic|hybrid] [--collection "Name"] [--tag "keyword"] [--field title|abstract|body]
"""

import json
import sys
import math
import os
import re
import pickle
import struct
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

INDEX_PATH = Path.home() / "Zotero" / "claude-assistant-index.json"
PICKLE_CACHE = INDEX_PATH.with_suffix('.pkl')
EMBEDDINGS_DB = Path.home() / "Zotero" / "claude-assistant-embeddings.sqlite"
EMBEDDINGS_PICKLE = EMBEDDINGS_DB.with_suffix('.emb.pkl')

# Zotero HTTP server (loopback only)
ZOTERO_EMBED_URL = "http://127.0.0.1:23119/claude-assistant/embed"

# BM25 parameters (Okapi BM25 standard)
K1 = 1.5
B = 0.75

# RRF parameter
RRF_K = 60

# Embedding dimension (all-MiniLM-L6-v2)
EMBEDDING_DIM = 384

# English stopwords - must match the indexer's implementation exactly
STOPWORDS = {
    'a','an','the','and','or','but','in','on','at','to','for','of','with','by','from','as','is','it',
    'was','are','were','be','been','being','have','has','had','do','does','did','will','would','shall',
    'should','may','might','can','could','not','no','nor','so','if','then','than','that','this','these',
    'those','he','she','we','they','me','him','her','us','them','my','his','its','our','their','your',
    'who','whom','which','what','where','when','how','why','am','about','into','through','during',
    'before','after','above','below','between','out','off','over','under','again','further','once',
    'here','there','all','each','every','both','few','more','most','other','some','such','only','own',
    'same','very','just','because','until','while','also','any','up','down','too','very','much',
    'de','la','le','et','des','du','en','les','une','der','die','und','von','den'
}

# Bidirectional synonym/abbreviation map for semiconductor process/materials science - must match the indexer
SYNONYM_MAP: Dict[str, List[str]] = {
    'hf': ['hafnium'], 'hafnium': ['hf'],
    'cu': ['copper'], 'copper': ['cu'],
    'al': ['aluminum', 'aluminium'], 'aluminum': ['al'], 'aluminium': ['al'],
    'au': ['gold'], 'gold': ['au'],
    'ag': ['silver'], 'silver': ['ag'],
    'zn': ['zinc'], 'zinc': ['zn'],
    'mg': ['magnesium'], 'magnesium': ['mg'],
    'na': ['sodium'], 'sodium': ['na'],
    'k': ['potassium'], 'potassium': ['k'],
    'fe': ['iron'], 'iron': ['fe'],
    'ni': ['nickel'], 'nickel': ['ni'],
    'ti': ['titanium'], 'titanium': ['ti'],
    'zr': ['zirconium'], 'zirconium': ['zr'],
    'si': ['silicon'], 'silicon': ['si'],
    'sn': ['tin'], 'tin': ['sn'],
    'mn': ['manganese'], 'manganese': ['mn'],
    'co': ['cobalt'], 'cobalt': ['co'],
    'cr': ['chromium'], 'chromium': ['cr'],
    'w': ['tungsten'], 'tungsten': ['w'],
    'pt': ['platinum'], 'platinum': ['pt'],
    'hkmg': ['high-k', 'metal', 'gate'], 'high-k metal gate': ['hkmg'],
    'ald': ['atomic', 'layer', 'deposition'], 'atomic layer deposition': ['ald'],
    'sti': ['shallow', 'trench', 'isolation'], 'shallow trench isolation': ['sti'],
    'rie': ['reactive', 'ion', 'etching'], 'reactive ion etching': ['rie'],
    'tsv': ['through', 'silicon', 'via'], 'through silicon via': ['tsv'],
    'cmp': ['chemical', 'mechanical', 'planarization'], 'chemical mechanical planarization': ['cmp'],
    'xrr': ['x-ray', 'reflectivity'], 'x-ray reflectivity': ['xrr'],
    'xrd': ['x-ray', 'diffraction'], 'x-ray diffraction': ['xrd'],
    'xps': ['x-ray', 'photoelectron', 'spectroscopy'],
    'sem': ['scanning', 'electron', 'microscopy'],
    'tem': ['transmission', 'electron', 'microscopy'],
    'afm': ['atomic', 'force', 'microscopy'],
    'cv': ['capacitance', 'voltage'], 'capacitance voltage': ['cv'],
    'pld': ['pulsed', 'laser', 'deposition'],
    'pvd': ['physical', 'vapor', 'deposition'],
    'cvd': ['chemical', 'vapor', 'deposition'],
    'hfo2': ['hafnium', 'oxide', 'high-k', 'dielectric'],
    'pecvd': ['plasma', 'enhanced', 'chemical', 'vapor'],
    'ito': ['indium', 'tin', 'oxide'],
    'finfet': ['fin', 'field', 'effect', 'transistor'],
    'mosfet': ['metal', 'oxide', 'semiconductor', 'transistor'],
}

# Field weight multipliers for section-aware scoring
FIELD_WEIGHTS = {
    'title': 3.0,
    'abstract': 2.0,
    'body': 1.0,
}


def load_index() -> tuple:
    """Load the Zotero index file, using pickle cache when available."""
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Index not found: {INDEX_PATH}\nRun indexing in Zotero first.")

    # Check pickle cache - use if newer than JSON index
    if PICKLE_CACHE.exists():
        json_mtime = INDEX_PATH.stat().st_mtime
        pkl_mtime = PICKLE_CACHE.stat().st_mtime
        if pkl_mtime > json_mtime:
            try:
                with open(PICKLE_CACHE, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                pass  # Fall through to JSON load

    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parse chunks: array of [chunkId, {metadata}]
    chunks = {item[0]: item[1] for item in data.get('chunks', [])}

    # Parse embedded BM25 index
    bm25_raw = json.loads(data.get('bm25Index', '{}'))

    # Convert documents list to dict by id
    documents = {}
    for doc in bm25_raw.get('documents', []):
        documents[doc['id']] = doc

    # Convert documentFreqs list to dict
    document_freqs = {}
    for item in bm25_raw.get('documentFreqs', []):
        if isinstance(item, list) and len(item) == 2:
            document_freqs[item[0]] = item[1]

    bm25_data = {
        'documents': documents,
        'documentFreqs': document_freqs,
        'avgDocLength': bm25_raw.get('avgDocLength', 100),
        'totalDocs': bm25_raw.get('totalDocs', len(documents))
    }

    total_indexed = len(data.get('indexedItemKeys', []))
    result = (chunks, bm25_data, total_indexed)

    # Write pickle cache for faster future loads
    try:
        with open(PICKLE_CACHE, 'wb') as f:
            pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass  # Non-critical

    return result


# ═══════════════════════════════════════════════════════════════
# Embedding / Semantic Search Functions
# ═══════════════════════════════════════════════════════════════

def load_embeddings() -> Optional[Dict[str, List[float]]]:
    """Load embeddings from SQLite database. Returns {chunk_id: embedding_list} or None."""
    if not EMBEDDINGS_DB.exists():
        return None

    # Check pickle cache
    if EMBEDDINGS_PICKLE.exists():
        db_mtime = EMBEDDINGS_DB.stat().st_mtime
        pkl_mtime = EMBEDDINGS_PICKLE.stat().st_mtime
        if pkl_mtime > db_mtime:
            try:
                with open(EMBEDDINGS_PICKLE, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                pass

    try:
        conn = sqlite3.connect(str(EMBEDDINGS_DB))
        cursor = conn.execute("SELECT chunk_id, embedding FROM embeddings")
        embeddings = {}
        for chunk_id, blob in cursor:
            if blob:
                # BLOB is raw bytes of Float32Array (4 bytes per float)
                n_floats = len(blob) // 4
                floats = list(struct.unpack(f'<{n_floats}f', blob))
                embeddings[chunk_id] = floats
        conn.close()

        # Cache for faster subsequent loads
        if embeddings:
            try:
                with open(EMBEDDINGS_PICKLE, 'wb') as f:
                    pickle.dump(embeddings, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception:
                pass

        return embeddings if embeddings else None
    except Exception:
        return None


def get_query_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for query text via Zotero HTTP endpoint. Returns list of floats or None."""
    try:
        data = json.dumps({"text": text}).encode('utf-8')
        req = urllib.request.Request(
            ZOTERO_EMBED_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get('embedding')
    except (urllib.error.URLError, urllib.error.HTTPError, ConnectionRefusedError,
            json.JSONDecodeError, TimeoutError, OSError):
        return None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors. Assumes L2-normalized (dot product only)."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot


def semantic_search(
    query: str,
    chunks: Dict[str, Any],
    limit: int = 10,
) -> List[Tuple[str, float]]:
    """Perform semantic search. Returns list of (chunk_id, score) tuples."""
    embeddings = load_embeddings()
    if not embeddings:
        return []

    query_embedding = get_query_embedding(query)
    if not query_embedding:
        return []

    # Compute similarity for all embeddings
    scores = []
    for chunk_id, embedding in embeddings.items():
        # Only score chunks that exist in the index
        if chunk_id not in chunks:
            continue
        sim = cosine_similarity(query_embedding, embedding)
        if sim > 0.2:  # Threshold to filter noise
            scores.append((chunk_id, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:limit]


def rrf_merge(
    bm25_scores: List[Tuple[str, float]],
    semantic_scores: List[Tuple[str, float]],
    limit: int,
    k: int = RRF_K,
) -> List[Tuple[str, float]]:
    """Reciprocal Rank Fusion merge of BM25 and semantic results."""
    # Build rank maps (chunk_id -> rank, 0-indexed)
    bm25_ranks = {cid: i for i, (cid, _) in enumerate(bm25_scores)}
    semantic_ranks = {cid: i for i, (cid, _) in enumerate(semantic_scores)}

    # Collect all unique chunk IDs
    all_ids = set(bm25_ranks.keys()) | set(semantic_ranks.keys())

    penalty_rank = 1000
    scored = []
    for cid in all_ids:
        bm25_rank = bm25_ranks.get(cid, penalty_rank)
        sem_rank = semantic_ranks.get(cid, penalty_rank)
        rrf_score = 1.0 / (k + bm25_rank + 1) + 1.0 / (k + sem_rank + 1)
        scored.append((cid, rrf_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


# ═══════════════════════════════════════════════════════════════
# BM25 Functions
# ═══════════════════════════════════════════════════════════════

def tokenize(text: str) -> List[str]:
    """Tokenize text into terms (matching the TypeScript implementation).
    Preserves short scientific tokens (Hf, Cu, Al, eV, nm, 2D, D*, pH).
    Uses stopword list instead of length filter.
    """
    text = text.lower()
    # Preserve D* as "d*", keep hyphens in compound terms like solid-state
    text = re.sub(r'[^\w\s*\-]', ' ', text)
    tokens = text.split()
    return [t for t in tokens if t and t not in STOPWORDS]


def expand_query(query_terms: List[str]) -> List[Tuple[str, float]]:
    """Expand query terms with synonyms. Returns list of (term, weight) tuples."""
    expanded = []
    seen = set()

    for term in query_terms:
        if term not in seen:
            expanded.append((term, 1.0))
            seen.add(term)
        synonyms = SYNONYM_MAP.get(term)
        if synonyms:
            for syn in synonyms:
                if syn not in seen:
                    expanded.append((syn, 0.5))
                    seen.add(syn)
    return expanded


def calculate_bm25_score(
    expanded_terms: List[Tuple[str, float]],
    doc_id: str,
    bm25_data: Dict[str, Any]
) -> float:
    """Calculate BM25 score for a document given expanded query terms with weights."""
    documents = bm25_data.get('documents', {})
    document_freqs = bm25_data.get('documentFreqs', {})
    avg_doc_length = bm25_data.get('avgDocLength', 100)
    total_docs = bm25_data.get('totalDocs', 1)

    if doc_id not in documents:
        return 0.0

    doc_data = documents[doc_id]
    doc_length = doc_data.get('length', 0)

    # Convert termFreqs from list of [term, count] to dict
    raw_term_freqs = doc_data.get('termFreqs', [])
    if isinstance(raw_term_freqs, list):
        term_freqs = {item[0]: item[1] for item in raw_term_freqs if isinstance(item, list) and len(item) == 2}
    else:
        term_freqs = raw_term_freqs

    score = 0.0

    for term, weight in expanded_terms:
        if term not in term_freqs:
            continue

        tf = term_freqs[term]
        df = document_freqs.get(term, 0)
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)

        numerator = tf * (K1 + 1)
        denominator = tf + K1 * (1 - B + B * (doc_length / avg_doc_length))

        score += weight * idf * (numerator / denominator)

    return score


def bm25_search(
    query: str,
    chunks: Dict[str, Any],
    bm25_data: Dict[str, Any],
    limit: int = 10,
    collection: Optional[str] = None,
    tag: Optional[str] = None,
    field: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """BM25 keyword search. Returns list of (chunk_id, score) tuples."""
    query_terms = tokenize(query)
    expanded_terms = expand_query(query_terms)

    if not expanded_terms:
        return []

    # Pre-filter chunks by collection/tag/field if requested
    candidate_ids = set(chunks.keys())

    if collection:
        collection_lower = collection.lower()
        candidate_ids = {
            cid for cid in candidate_ids
            if any(collection_lower in c.lower()
                   for c in chunks[cid].get('collections', []))
        }

    if tag:
        tag_lower = tag.lower()
        candidate_ids = {
            cid for cid in candidate_ids
            if any(tag_lower in t.lower()
                   for t in chunks[cid].get('tags', []))
        }

    if field:
        candidate_ids = {
            cid for cid in candidate_ids
            if chunks[cid].get('section', 'body') == field
        }

    # Score all candidate documents
    scores = []
    for doc_id in candidate_ids:
        score = calculate_bm25_score(expanded_terms, doc_id, bm25_data)
        if score > 0:
            # Apply field weight boost if section metadata is available
            section = chunks[doc_id].get('section', 'body')
            field_weight = FIELD_WEIGHTS.get(section, 1.0)
            score *= field_weight
            scores.append((doc_id, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:limit]


# ═══════════════════════════════════════════════════════════════
# Main Search
# ═══════════════════════════════════════════════════════════════

def search(
    query: str,
    limit: int = 10,
    mode: str = 'hybrid',
    collection: Optional[str] = None,
    tag: Optional[str] = None,
    field: Optional[str] = None,
) -> Dict[str, Any]:
    """Search the index and return top results.

    Modes:
      keyword  - BM25 only (same as before)
      semantic - cosine similarity only (requires embeddings + Zotero running)
      hybrid   - RRF merge of BM25 + semantic (default, falls back to keyword)
    """
    chunks, bm25_data, total_indexed = load_index()

    query_terms = tokenize(query)
    expanded_terms = expand_query(query_terms)

    # BM25 search (always available)
    bm25_scores = bm25_search(query, chunks, bm25_data, limit, collection, tag, field)

    # Determine final scores based on mode
    final_scores: List[Tuple[str, float]] = []
    actual_mode = mode

    if mode == 'keyword':
        final_scores = bm25_scores
    elif mode == 'semantic':
        sem_scores = semantic_search(query, chunks, limit)
        if sem_scores:
            final_scores = sem_scores
        else:
            # Fallback to keyword
            final_scores = bm25_scores
            actual_mode = 'keyword (fallback)'
    elif mode == 'hybrid':
        sem_scores = semantic_search(query, chunks, limit)
        if sem_scores:
            final_scores = rrf_merge(bm25_scores, sem_scores, limit)
        else:
            # Fallback to keyword when semantic is unavailable
            final_scores = bm25_scores
            actual_mode = 'keyword (fallback)'
    else:
        final_scores = bm25_scores
        actual_mode = 'keyword'

    if not final_scores and not expanded_terms:
        return {
            "query": query,
            "results": [],
            "total_indexed": total_indexed,
            "error": "No valid search terms after tokenization"
        }

    # Normalize scores relative to max
    max_score = final_scores[0][1] if final_scores else 1.0

    # Build results
    results = []
    for doc_id, score in final_scores[:limit]:
        chunk = chunks.get(doc_id)
        if not chunk:
            continue
        normalized_score = min(score / max_score * 0.99, 0.99) if max_score > 0 else 0

        result = {
            "title": chunk.get('title', 'Untitled'),
            "authors": chunk.get('authors', ''),
            "year": chunk.get('year', ''),
            "text": chunk.get('text', '')[:1000],
            "score": round(normalized_score, 3),
            "chunk_index": chunk.get('chunkIndex', 0),
            "item_key": chunk.get('itemKey', ''),
            "zotero_url": f"zotero://select/library/items/{chunk.get('itemKey', '')}",
        }

        # Include section if available
        if 'section' in chunk:
            result['section'] = chunk['section']

        results.append(result)

    return {
        "query": query,
        "mode": actual_mode,
        "expanded_terms": [{"term": t, "weight": w} for t, w in expanded_terms],
        "results": results,
        "total_indexed": total_indexed,
        "total_matches": len(final_scores)
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python search_zotero.py \"query\" [limit] [--mode keyword|semantic|hybrid] [--collection \"Name\"] [--tag \"keyword\"] [--field title|abstract|body]", file=sys.stderr)
        print("Example: python search_zotero.py \"high-k dielectric\" 10 --mode hybrid", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    limit = 10
    mode = 'hybrid'
    collection = None
    tag = None
    field = None

    # Parse positional and named arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--collection' and i + 1 < len(sys.argv):
            collection = sys.argv[i + 1]
            i += 2
        elif arg == '--tag' and i + 1 < len(sys.argv):
            tag = sys.argv[i + 1]
            i += 2
        elif arg == '--field' and i + 1 < len(sys.argv):
            field = sys.argv[i + 1]
            i += 2
        elif arg == '--mode' and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1]
            if mode not in ('keyword', 'semantic', 'hybrid'):
                print(f"Invalid mode: {mode}. Use keyword, semantic, or hybrid.", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            try:
                limit = int(arg)
            except ValueError:
                pass
            i += 1

    limit = min(limit, 25)  # Cap at 25

    try:
        results = search(query, limit, mode=mode, collection=collection, tag=tag, field=field)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Search failed: {str(e)}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
