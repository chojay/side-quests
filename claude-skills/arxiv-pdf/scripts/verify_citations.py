#!/usr/bin/env python3
"""Verify that the DOIs (and arXiv IDs) cited in a paper actually exist.

The failure this guards against: an AI-drafted paper can invent a DOI, or pair
a REAL DOI with a fabricated title/authors. Both look plausible in a .bib file.
This resolves every DOI against Crossref (then DataCite), and when the source
gives a title, checks that the resolved title actually matches - catching the
"real DOI, wrong paper" case that a mere 200-OK check misses.

Pure standard library (urllib/json/re/difflib); no network deps.

Usage:
    python3 verify_citations.py refs.bib
    python3 verify_citations.py paper.md
    python3 verify_citations.py --doi 10.1038/nature14539

Exit code is nonzero if any citation is NOT FOUND or MISMATCH, so it can gate a
build. Entries marked API-BLOCKED could not be checked programmatically and must
be confirmed in the browser (see the skill's citation-verification section).
"""
import argparse
import difflib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DOI_RE = re.compile(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', re.I)
ARXIV_RE = re.compile(r'arXiv:\s*(\d{4}\.\d{4,5})(v\d+)?', re.I)
# .bib field grabbers (best-effort; also works on loose text)
BIB_ENTRY_RE = re.compile(r'@\w+\s*\{(.+?)\n\}', re.S)
TITLE_RE = re.compile(r'title\s*=\s*[{"](.+?)[}"]\s*,?\s*$', re.I | re.M | re.S)

UA = "citation-verifier/1.0 (mailto:noreply@example.com)"  # polite Crossref UA


def _get_json(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def resolve_doi(doi):
    """Return (found: bool, title: str|None, source: str) or ('blocked', ...)."""
    doi = doi.rstrip(".,;)")
    # 1. Crossref
    try:
        data = _get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
        msg = data.get("message", {})
        title = (msg.get("title") or [None])[0]
        return True, title, "crossref"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            pass  # not in Crossref; try DataCite
        elif e.code in (403, 429):
            return "blocked", None, "crossref"
        else:
            pass
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return "blocked", None, "crossref"
    # 2. DataCite (datasets, some publishers)
    try:
        data = _get_json("https://api.datacite.org/dois/" + urllib.parse.quote(doi))
        attr = data.get("data", {}).get("attributes", {})
        titles = attr.get("titles") or []
        title = titles[0].get("title") if titles else None
        return True, title, "datacite"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, None, "none"
        return "blocked", None, "datacite"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return "blocked", None, "datacite"


def resolve_arxiv(arxiv_id):
    try:
        req = urllib.request.Request(
            "http://export.arxiv.org/api/query?id_list=" + arxiv_id,
            headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read().decode("utf-8", "replace")
        m = re.search(r"<entry>.*?<title>(.*?)</title>", body, re.S)
        if "<entry>" in body:
            return True, (m.group(1).strip() if m else None), "arxiv"
        return False, None, "none"
    except Exception:
        return "blocked", None, "arxiv"


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()


def title_match(cited, resolved):
    if not cited or not resolved:
        return None  # can't compare
    return difflib.SequenceMatcher(None, norm(cited), norm(resolved)).ratio()


def extract_citations(text):
    """Return list of dicts: {doi|arxiv, cited_title}."""
    out, seen = [], set()
    # pair titles with the DOI in the same bib entry when possible
    for entry in BIB_ENTRY_RE.findall(text) or [text]:
        tm = TITLE_RE.search(entry)
        cited_title = re.sub(r"\s+", " ", tm.group(1)).strip() if tm else None
        for d in DOI_RE.findall(entry):
            key = ("doi", d.lower().rstrip(".,;)"))
            if key in seen:
                continue
            seen.add(key)
            out.append({"kind": "doi", "id": d.rstrip(".,;)"), "title": cited_title})
        for a in ARXIV_RE.findall(entry):
            key = ("arxiv", a[0])
            if key in seen:
                continue
            seen.add(key)
            out.append({"kind": "arxiv", "id": a[0], "title": cited_title})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="?", help=".bib or .md/.tex file with citations")
    ap.add_argument("--doi", action="append", default=[], help="check a single DOI")
    ap.add_argument("--match-threshold", type=float, default=0.6,
                    help="min title-similarity to count as a match (default 0.6)")
    args = ap.parse_args()

    cites = []
    if args.path:
        cites += extract_citations(open(args.path, encoding="utf-8", errors="replace").read())
    for d in args.doi:
        cites.append({"kind": "doi", "id": d, "title": None})
    if not cites:
        sys.exit("no DOIs or arXiv IDs found in input")

    print(f"Checking {len(cites)} citation(s)...\n")
    bad = 0
    rows = []
    for c in cites:
        if c["kind"] == "doi":
            found, rtitle, src = resolve_doi(c["id"])
        else:
            found, rtitle, src = resolve_arxiv(c["id"])
        time.sleep(0.2)  # be polite to the APIs
        if found == "blocked":
            status = "API-BLOCKED"
            bad += 1
        elif not found:
            status = "NOT FOUND"
            bad += 1
        else:
            ratio = title_match(c["title"], rtitle)
            if ratio is not None and ratio < args.match_threshold:
                status = f"MISMATCH ({ratio:.2f})"
                bad += 1
            else:
                status = "VERIFIED" + (f" ({ratio:.2f})" if ratio is not None else "")
        rows.append((c["id"], status, (rtitle or "")[:60]))

    w = max(len(r[0]) for r in rows)
    for cid, status, rtitle in rows:
        print(f"  {cid.ljust(w)}  {status.ljust(16)}  {rtitle}")
    print()
    if bad:
        print(f"{bad} citation(s) need attention. NOT FOUND / MISMATCH = fix or "
              "remove before building. API-BLOCKED = verify in the browser "
              "(see the skill's citation-verification section).")
        sys.exit(1)
    print("All citations verified.")


if __name__ == "__main__":
    main()
