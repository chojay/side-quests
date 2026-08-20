#!/usr/bin/env python3
"""Verify that every citation in a paper exists, describes the right paper, and is not retracted.

The failure this guards against: an AI-drafted paper can invent a DOI, pair a
REAL DOI with a fabricated title, cite a paper that has since been retracted, or
supply a reference with no resolvable identifier at all. Every one of those looks
plausible in a .bib file.

This implements the Reference Verification check (I3) of the Chain-of-Evidence
integrity audit described in "ScientistOne: Towards Human-Level Autonomous
Research via Chain-of-Evidence" (arXiv:2605.26340), summarized at
https://research.google/blog/science-one-framework-a-verifiable-autonomous-research-framework-via-chain-of-evidence/
The paper's procedure: "Each bibliography entry is resolved by querying multiple
academic APIs (Semantic Scholar, arXiv, OpenAlex, CrossRef) using arXiv ID, DOI,
and title", followed by an LLM cross-check "to catch near-misses and citation
gaming (e.g., a real DOI attached to a fabricated description)".

This script owns everything cheap and decidable (resolution, exact matching,
thresholding). Entries landing in the ambiguous band are written to an
adjudication queue for the LLM to judge, rather than being decided by a
threshold that cannot tell a subtitle change from a fabricated description.

Pure standard library (urllib/json/re/difflib); no network deps, no API keys.

Usage:
    python3 verify_citations.py refs.bib
    python3 verify_citations.py paper.md
    python3 verify_citations.py --doi 10.1038/nature14539
    python3 verify_citations.py refs.bib --ledger paper.evidence.json
    python3 verify_citations.py refs.bib --adjudicate review.jsonl --json

Set CITEVERIFY_MAILTO to your email to enter the Crossref/OpenAlex polite pools
(faster, higher rate limits, and it is what those APIs ask of you).

Exit code is nonzero if any citation is not clean, so it can gate a build.
"""
import argparse
import difflib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

MAILTO = os.environ.get("CITEVERIFY_MAILTO", "").strip()
UA = "citation-verifier/2.0" + (f" (mailto:{MAILTO})" if MAILTO else "")

# Similarity bands for cited-title vs resolved-title. Between these two, the
# comparison is handed to an LLM instead of being decided by the number.
MATCH_HIGH = 0.85   # >= this: accept without a model call
MATCH_LOW = 0.35    # <= this: reject without a model call
# Title search always returns its best effort, so a weak hit means "no such
# paper" rather than "borderline". Hold title-only resolution to a higher floor.
TITLE_ONLY_LOW = 0.60

BLOCKED = object()  # sentinel: source was unreachable, not "not found"

DOI_RE = re.compile(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', re.I)
ARXIV_RE = re.compile(r'(?:arXiv[:\s]*)?(\d{4}\.\d{4,5})(?:v\d+)?', re.I)
ARXIV_TAGGED_RE = re.compile(r'arXiv[:\s]*(\d{4}\.\d{4,5})(?:v\d+)?', re.I)


# --------------------------------------------------------------------------
# BibTeX parsing (brace-balanced, so nested braces in titles survive)
# --------------------------------------------------------------------------

def split_bib_entries(text):
    """Yield (entry_type, citekey, body) for each @type{key, ...} entry."""
    for m in re.finditer(r'@(\w+)\s*\{', text):
        etype = m.group(1).lower()
        if etype in ("comment", "preamble", "string"):
            continue
        i = m.end()
        depth, start = 1, i
        while i < len(text) and depth:
            c = text[i]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            i += 1
        body = text[start:i - 1]
        key = body.split(',', 1)[0].strip()
        yield etype, key, body


def bib_field(body, name):
    """Extract one field value from a bib entry body, brace-balanced."""
    m = re.search(r'\b' + name + r'\s*=\s*', body, re.I)
    if not m:
        return None
    i = m.end()
    if i >= len(body):
        return None
    if body[i] == '{':
        depth, i, start = 1, i + 1, i + 1
        while i < len(body) and depth:
            if body[i] == '{':
                depth += 1
            elif body[i] == '}':
                depth -= 1
            i += 1
        val = body[start:i - 1]
    elif body[i] == '"':
        i += 1
        start = i
        while i < len(body) and body[i] != '"':
            i += 2 if body[i] == '\\' else 1
        val = body[start:i]
    else:
        val = re.split(r',\s*\n|\n\s*\}', body[i:])[0]
    val = re.sub(r'[{}]', '', val)
    return re.sub(r'\s+', ' ', val).strip() or None


def entries_from_bib(text):
    out = []
    for etype, key, body in split_bib_entries(text):
        doi = bib_field(body, "doi")
        if doi:
            doi = re.sub(r'^(https?://)?(dx\.)?doi\.org/', '', doi, flags=re.I).rstrip(".,;)")
        arx = bib_field(body, "eprint") or bib_field(body, "archiveprefix")
        if not arx:
            m = ARXIV_TAGGED_RE.search(body)
            arx = m.group(1) if m else None
        else:
            m = ARXIV_RE.search(arx)
            arx = m.group(1) if m else None
        if not doi:
            m = DOI_RE.search(body)
            doi = m.group(0).rstrip(".,;)") if m else None
        out.append({
            "key": key, "type": etype, "doi": doi, "arxiv": arx,
            "title": bib_field(body, "title"),
            "authors": bib_field(body, "author"),
            "year": bib_field(body, "year"),
        })
    return out


def entries_from_loose_text(text):
    """Fallback for .md/.tex: identifiers only, no titles to compare against."""
    out, seen = [], set()
    for d in DOI_RE.findall(text):
        d = d.rstrip(".,;)")
        if d.lower() in seen:
            continue
        seen.add(d.lower())
        out.append({"key": None, "type": None, "doi": d, "arxiv": None,
                    "title": None, "authors": None, "year": None})
    for a in ARXIV_TAGGED_RE.findall(text):
        if a in seen:
            continue
        seen.add(a)
        out.append({"key": None, "type": None, "doi": None, "arxiv": a,
                    "title": None, "authors": None, "year": None})
    return out


def extract_entries(text):
    if '@' in text and re.search(r'@\w+\s*\{', text):
        return entries_from_bib(text)
    return entries_from_loose_text(text)


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def get_json(url, timeout=12):
    """Return parsed JSON, None for a clean 404, or BLOCKED if unreachable."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return BLOCKED
    except Exception:
        return BLOCKED


def q(s):
    return urllib.parse.quote(str(s), safe="")


def polite(url):
    if not MAILTO:
        return url
    return url + ("&" if "?" in url else "?") + "mailto=" + q(MAILTO)


# --------------------------------------------------------------------------
# Per-source resolvers. Each returns a normalized record, None, or BLOCKED.
# record = {source, title, authors, year, doi, arxiv, venue, retracted}
# --------------------------------------------------------------------------

RETRACTED_TITLE_RE = re.compile(
    r'^\s*(\[?\s*)?(retracted|withdrawn|retraction of|withdrawal of|'
    r'this article has been retracted)\b', re.I)


def _rec(source, title=None, authors=None, year=None, doi=None,
         arxiv=None, venue=None, retracted=False):
    # Publishers very often signal a retraction only by prefixing the title
    # ("RETRACTED: ..."), which no structured field exposes. Catch that too.
    if not retracted and title and RETRACTED_TITLE_RE.match(title):
        retracted = True
    return {"source": source, "title": title, "authors": authors, "year": year,
            "doi": doi, "arxiv": arxiv, "venue": venue, "retracted": retracted}


def retraction_probe(doi):
    """Ask OpenAlex specifically about retraction status.

    Crossref is authoritative for DOI metadata but records a retraction on the
    retraction NOTICE, not always on the original work, so a first-success
    cascade that stops at Crossref can miss it. OpenAlex exposes is_retracted
    as a first-class boolean, so spend one extra call to ask it directly.
    """
    d = get_json(polite("https://api.openalex.org/works/doi:" + q(doi)
                        + "?select=id,title,is_retracted"))
    if not d or d is BLOCKED:
        return None
    if d.get("is_retracted"):
        return True
    if d.get("title") and RETRACTED_TITLE_RE.match(d["title"]):
        return True
    return False


def crossref_by_doi(doi):
    d = get_json(polite("https://api.crossref.org/works/" + q(doi)))
    if d is None or d is BLOCKED:
        return d
    return _norm_crossref(d.get("message", {}))


def _norm_crossref(m):
    if not m:
        return None
    # Crossref carries Retraction Watch data: update-to entries of type
    # retraction/withdrawal/removal, or the work itself being a retraction notice.
    retracted = any(
        (u.get("type") or "").lower() in ("retraction", "withdrawal", "removal")
        for u in (m.get("update-to") or [])
    ) or (m.get("type") or "").lower() == "retraction"
    authors = ", ".join(
        " ".join(x for x in (a.get("given"), a.get("family")) if x)
        for a in (m.get("author") or [])[:6]
    ) or None
    year = None
    for f in ("published-print", "published-online", "issued", "created"):
        parts = (m.get(f) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            year = str(parts[0][0])
            break
    return _rec("crossref", (m.get("title") or [None])[0], authors, year,
                m.get("DOI"), None, (m.get("container-title") or [None])[0], retracted)


def openalex_by_doi(doi):
    d = get_json(polite("https://api.openalex.org/works/doi:" + q(doi)))
    if d is None or d is BLOCKED:
        return d
    return _norm_openalex(d)


def _norm_openalex(w):
    if not w:
        return None
    ids = w.get("ids") or {}
    arx = None
    for loc in (w.get("locations") or []):
        lid = ((loc.get("source") or {}).get("display_name") or "")
        if "arxiv" in lid.lower():
            m = ARXIV_RE.search(loc.get("landing_page_url") or "")
            if m:
                arx = m.group(1)
    authors = ", ".join(
        (a.get("author") or {}).get("display_name") or ""
        for a in (w.get("authorships") or [])[:6]
    ).strip(", ") or None
    doi = (ids.get("doi") or "").replace("https://doi.org/", "") or None
    venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
    # OpenAlex exposes retraction status as a first-class boolean.
    return _rec("openalex", w.get("title") or w.get("display_name"), authors,
                str(w.get("publication_year") or "") or None, doi, arx,
                venue, bool(w.get("is_retracted")))


S2_FIELDS = "title,externalIds,year,authors,venue,publicationTypes"


def s2_by_doi(doi):
    d = get_json("https://api.semanticscholar.org/graph/v1/paper/DOI:" + q(doi)
                 + "?fields=" + S2_FIELDS)
    if d is None or d is BLOCKED:
        return d
    return _norm_s2(d)


def _norm_s2(p):
    if not p or not p.get("title"):
        return None
    ext = p.get("externalIds") or {}
    authors = ", ".join(a.get("name") or "" for a in (p.get("authors") or [])[:6]).strip(", ") or None
    types = [t.lower() for t in (p.get("publicationTypes") or [])]
    return _rec("semanticscholar", p.get("title"), authors,
                str(p.get("year") or "") or None, ext.get("DOI"),
                ext.get("ArXiv"), p.get("venue"), "retraction" in types)


def datacite_by_doi(doi):
    d = get_json("https://api.datacite.org/dois/" + q(doi))
    if d is None or d is BLOCKED:
        return d
    attr = (d.get("data") or {}).get("attributes") or {}
    titles = attr.get("titles") or []
    return _rec("datacite", titles[0].get("title") if titles else None,
                ", ".join(c.get("name") or "" for c in (attr.get("creators") or [])[:6]) or None,
                str(attr.get("publicationYear") or "") or None,
                attr.get("doi"), None, attr.get("publisher"), False)


def arxiv_by_id(aid):
    req = urllib.request.Request(
        "https://export.arxiv.org/api/query?id_list=" + q(aid),
        headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception:
        return BLOCKED
    if "<entry>" not in body:
        return None
    # arXiv returns an <entry> with an error title when the id is unknown.
    if re.search(r"<title>\s*Error\s*</title>", body, re.I):
        return None
    t = re.search(r"<entry>.*?<title>(.*?)</title>", body, re.S)
    names = re.findall(r"<author>\s*<name>(.*?)</name>", body, re.S)[:6]
    yr = re.search(r"<published>(\d{4})", body)
    doi = re.search(r"<arxiv:doi[^>]*>(.*?)</arxiv:doi>", body, re.S)
    return _rec("arxiv", re.sub(r"\s+", " ", t.group(1)).strip() if t else None,
                ", ".join(n.strip() for n in names) or None,
                yr.group(1) if yr else None,
                doi.group(1).strip() if doi else None, aid, "arXiv", False)


# Ordered by reliability x rate-limit generosity. First success wins, so the
# stricter-limited sources are rarely touched.
DOI_RESOLVERS = [crossref_by_doi, openalex_by_doi, s2_by_doi, datacite_by_doi]


# --------------------------------------------------------------------------
# Title search: the path that makes DOI-less entries visible at all
# --------------------------------------------------------------------------

def title_search(title, year=None):
    """Return (candidates, blocked_count) across every title-search source."""
    cands, blocked = [], 0

    d = get_json(polite("https://api.openalex.org/works?per-page=3&filter=title.search:" + q(title)))
    if d is BLOCKED:
        blocked += 1
    elif d:
        cands += [r for r in (_norm_openalex(w) for w in (d.get("results") or [])) if r]

    d = get_json(polite("https://api.crossref.org/works?rows=3&select=DOI,title,author,"
                        "container-title,issued,type,update-to&query.bibliographic=" + q(title)))
    if d is BLOCKED:
        blocked += 1
    elif d:
        cands += [r for r in (_norm_crossref(m) for m in ((d.get("message") or {}).get("items") or [])) if r]

    if not cands:  # only spend the strict-limit source when nothing else answered
        d = get_json("https://api.semanticscholar.org/graph/v1/paper/search?limit=3&fields="
                     + S2_FIELDS + "&query=" + q(title))
        if d is BLOCKED:
            blocked += 1
        elif d:
            cands += [r for r in (_norm_s2(p) for p in (d.get("data") or [])) if r]

    if year:
        cands.sort(key=lambda r: (r.get("year") != str(year),))
    return cands, blocked


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------

def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()


def title_ratio(cited, resolved):
    if not cited or not resolved:
        return None
    return difflib.SequenceMatcher(None, norm(cited), norm(resolved), autojunk=False).ratio()


def resolve_entry(entry, pause=0.2):
    """Resolve one entry, recording HOW it resolved.

    The 'how' matters: if a DOI was supplied and resolved nowhere, that is a
    hard failure even if a later title search happens to find something. A
    fallback must never launder a dead identifier into a softer status.
    """
    out = {"records": [], "blocked": 0, "how": None,
           "dead_doi": False, "dead_arxiv": False, "suggestions": []}

    if entry.get("doi"):
        answered = False
        for fn in DOI_RESOLVERS:
            r = fn(entry["doi"])
            time.sleep(pause)
            if r is BLOCKED:
                out["blocked"] += 1
                continue
            answered = True
            if r:
                out["records"].append(r)
                out["how"] = "doi"
                break  # first success is enough for the common case
        if not out["records"] and answered:
            out["dead_doi"] = True  # every source that replied said 404

    if not out["records"] and entry.get("arxiv"):
        r = arxiv_by_id(entry["arxiv"])
        time.sleep(pause)
        if r is BLOCKED:
            out["blocked"] += 1
        elif r:
            out["records"].append(r)
            out["how"] = "arxiv"
        else:
            out["dead_arxiv"] = True

    if entry.get("title") and (not out["records"] or out["dead_doi"]):
        cands, b = title_search(entry["title"], entry.get("year"))
        out["blocked"] += b
        time.sleep(pause)
        cands.sort(key=lambda r: -(title_ratio(entry["title"], r["title"]) or 0))
        if out["dead_doi"] or out["dead_arxiv"]:
            # informational only: "did you mean", never a rescue
            out["suggestions"] = cands[:2]
        elif cands:
            out["records"] += cands[:3]
            out["how"] = "title"

    # Crossref can resolve a work without flagging its retraction; ask directly.
    if out["records"] and entry.get("doi") and not any(r["retracted"] for r in out["records"]):
        if retraction_probe(entry["doi"]):
            for r in out["records"]:
                r["retracted"] = True
        time.sleep(pause)

    return out


def corroborate(entry, already, pause=0.2):
    """Pull extra records so an ambiguous case reaches the LLM with alternatives."""
    have = {r["source"] for r in already}
    extra = []
    if entry.get("doi"):
        for fn in DOI_RESOLVERS:
            r = fn(entry["doi"])
            time.sleep(pause)
            if r and r is not BLOCKED and r["source"] not in have:
                extra.append(r)
    if entry.get("title"):
        cands, _ = title_search(entry["title"], entry.get("year"))
        extra += [c for c in cands if c["source"] not in have][:2]
    return extra


def classify(entry, res, deep=True):
    """Return (status, best_record, ratio, all_records)."""
    records, blocked = res["records"], res["blocked"]

    if not entry.get("doi") and not entry.get("arxiv") and not entry.get("title"):
        return "NO-ID", None, None, []

    # A supplied identifier that resolves nowhere is a phantom, full stop.
    if res["dead_doi"]:
        return "PHANTOM-DOI", None, None, res["suggestions"]
    if res["dead_arxiv"] and not entry.get("doi"):
        return "PHANTOM-ARXIV", None, None, res["suggestions"]

    if not records:
        # Distinguish "nothing exists" from "nobody answered".
        return ("API-BLOCKED" if blocked else "PHANTOM"), None, None, []

    best = records[0]
    ratio = title_ratio(entry.get("title"), best.get("title"))

    if any(r.get("retracted") for r in records):
        return "RETRACTED", best, ratio, records

    if ratio is None:
        # Resolved by identifier but the source gave no title to compare, so
        # the gaming case cannot be ruled out. Say so rather than passing it.
        return "RESOLVED-NO-TITLE", best, None, records

    if ratio >= MATCH_HIGH:
        return "VERIFIED", best, ratio, records
    # A title search always returns its best effort, so a weak best-effort hit
    # means the paper does not exist, not that the match is borderline. Judge
    # title-derived resolutions on a stricter floor than identifier-derived ones.
    floor = TITLE_ONLY_LOW if res["how"] == "title" else MATCH_LOW
    if ratio <= floor:
        return ("PHANTOM-TITLE" if res["how"] == "title" else "MISMATCH"), best, ratio, records

    extra = corroborate(entry, records) if deep else []
    allrecs = records + extra
    bestall = max(allrecs, key=lambda r: title_ratio(entry.get("title"), r["title"]) or 0)
    r2 = title_ratio(entry.get("title"), bestall.get("title"))
    if r2 is not None and r2 >= MATCH_HIGH:
        return "VERIFIED", bestall, r2, allrecs
    return "REVIEW", bestall, r2, allrecs


NEEDS_LLM = ("REVIEW", "RESOLVED-NO-TITLE")
HARD_FAIL = ("PHANTOM", "PHANTOM-DOI", "PHANTOM-ARXIV", "PHANTOM-TITLE",
             "MISMATCH", "RETRACTED", "NO-ID", "API-BLOCKED")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="?", help=".bib or .md/.tex file with citations")
    ap.add_argument("--doi", action="append", default=[], help="check a single DOI")
    ap.add_argument("--arxiv", action="append", default=[], help="check a single arXiv ID")
    ap.add_argument("--ledger", help="write resolved records here (the evidence chain cache)")
    ap.add_argument("--adjudicate", help="write ambiguous entries here as JSONL for LLM review")
    ap.add_argument("--json", action="store_true", help="emit machine-readable results on stdout")
    ap.add_argument("--no-deep", action="store_true", help="skip corroborating lookups")
    ap.add_argument("--pause", type=float, default=0.2, help="seconds between API calls")
    args = ap.parse_args()

    entries = []
    if args.path:
        with open(args.path, encoding="utf-8", errors="replace") as f:
            entries += extract_entries(f.read())
    for d in args.doi:
        entries.append({"key": None, "doi": d, "arxiv": None, "title": None,
                        "authors": None, "year": None})
    for a in args.arxiv:
        entries.append({"key": None, "doi": None, "arxiv": a, "title": None,
                        "authors": None, "year": None})
    if not entries:
        sys.exit("no citations found in input (no bib entries, DOIs, or arXiv IDs)")

    if not args.json:
        print(f"Checking {len(entries)} citation(s) against Crossref, OpenAlex, "
              f"Semantic Scholar, DataCite, arXiv...\n")

    results, queue = [], []
    for e in entries:
        res = resolve_entry(e, args.pause)
        status, best, ratio, allrecs = classify(e, res, deep=not args.no_deep)
        results.append({"entry": e, "status": status, "ratio": ratio,
                        "record": best, "records": allrecs})
        if status in NEEDS_LLM:
            queue.append({
                "citekey": e.get("key"), "status": status,
                "cited": {k: e.get(k) for k in ("title", "authors", "year", "doi", "arxiv")},
                "candidates": allrecs,
                "question": ("Is the cited bibliography entry a faithful description of any "
                             "candidate record? Answer FAITHFUL, GAMED (real record, fabricated "
                             "description), or DIFFERENT_PAPER, and name the discriminating field."),
            })

    if args.ledger:
        with open(args.ledger, "w", encoding="utf-8") as f:
            json.dump({"checked": len(results),
                       "entries": [{"citekey": r["entry"].get("key"),
                                    "status": r["status"], "ratio": r["ratio"],
                                    "resolved": r["record"]} for r in results]},
                      f, indent=2, ensure_ascii=False)

    if args.adjudicate:
        # Always rewrite, even when empty: a stale queue from a previous run
        # would otherwise be read back as live work still needing adjudication.
        with open(args.adjudicate, "w", encoding="utf-8") as f:
            for row in queue:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    else:
        labels = [r["entry"].get("key") or r["entry"].get("doi")
                  or r["entry"].get("arxiv") or "(no id)" for r in results]
        w = max(len(x) for x in labels)
        for lab, r in zip(labels, results):
            rt = f" ({r['ratio']:.2f})" if r["ratio"] is not None else ""
            title = ((r["record"] or {}).get("title") or "")[:56]
            src = (r["record"] or {}).get("source", "")
            print(f"  {lab.ljust(w)}  {(r['status'] + rt).ljust(24)}  {title}"
                  + (f"  [{src}]" if src else ""))
        print()

    fails = [r for r in results if r["status"] in HARD_FAIL]
    review = [r for r in results if r["status"] in NEEDS_LLM]

    if not args.json:
        if fails:
            print(f"{len(fails)} citation(s) FAILED.\n"
                  "  PHANTOM-DOI / PHANTOM-ARXIV = the identifier resolves nowhere; it was\n"
                  "    almost certainly invented. Any titles shown are 'did you mean' hints.\n"
                  "  PHANTOM-TITLE = no DOI given, and title search found nothing close.\n"
                  "  MISMATCH = the identifier is real but points at a DIFFERENT paper.\n"
                  "  RETRACTED = the paper exists but has been retracted; do not cite it as\n"
                  "    a live result.\n"
                  "  NO-ID = no DOI, arXiv ID, or title to check at all; unverifiable as written.\n"
                  "  API-BLOCKED = every source was unreachable. Not a pass. Check the network,\n"
                  "    then use the browser fallback in SKILL.md.")
        if review:
            print(f"{len(review)} citation(s) need LLM adjudication"
                  + (f" (written to {args.adjudicate})" if args.adjudicate else
                     " (rerun with --adjudicate review.jsonl to capture them)")
                  + ". These are near-misses: the identifier resolves but the description "
                    "does not clearly match, which is where citation gaming hides.")
        if not fails and not review:
            print("All citations verified.")

    sys.exit(1 if (fails or review) else 0)


if __name__ == "__main__":
    main()
