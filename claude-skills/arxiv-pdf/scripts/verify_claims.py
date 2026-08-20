#!/usr/bin/env python3
"""Verify that each claim in a draft is actually supported by the source it cites.

verify_citations.py answers "does this reference exist and describe the right
paper?". This answers the harder question: "does that paper actually say what
the sentence citing it claims?" Those are the two halves of Chain-of-Evidence in
"ScientistOne: Towards Human-Level Autonomous Research via Chain-of-Evidence"
(arXiv:2605.26340): completeness (every claim carries an evidence chain) and
correctness (each chain genuinely supports its claim). A reference can resolve
perfectly and still not support the sentence attached to it.

Claims are marked with inline evidence tags, which are HTML comments so pandoc
ignores them and convert.sh strips them before the build:

    Interfacial resistance falls by roughly 40% after coating [@wang2023].
    <!--ev kind="citation" src="doi:10.1021/acsami.3c01234" zotero="ABCD1234"
            locator="p.4, Fig.3b"
            quote="the interface trap density decreased from 2.5e12 to 1.5e12 cm-2 eV-1" -->

    The Ti 2p peak sits at 458.6 eV.
    <!--ev kind="numeric" src="file:xps_fit_results.csv#row=Ti2p,col=BE" value="458.6" -->

Dispatch follows the paper's Claim Verifier: "numerical claims against evaluator
logs, citation claims against the bibliography".

  kind="citation"  the quote must literally occur in the source full text, then
                   the (sentence, quote) pair goes to an LLM entailment check.
                   The quote-presence test needs no model and is the strongest
                   primitive here: a fabricated supporting quote cannot survive
                   a fuzzy match against the real PDF.
  kind="numeric"   the value is re-read from the artifact file and compared,
                   so numbers in prose are never retyped from memory.

Source text is resolved, in order: an explicit pdf= path, the Zotero PDF for
zotero=<itemKey>, then the Zotero index abstract. The abstract is a REDUCED
scope: a quote missing from an abstract is reported UNCHECKED, never fabricated,
because absence from an abstract proves nothing about the paper.

Standard library only. pdftotext (poppler) is used when present; without it the
check degrades to abstract scope and says so.

Usage:
    python3 verify_claims.py paper.md
    python3 verify_claims.py paper.md --require-tags        # completeness check
    python3 verify_claims.py paper.md --entail entail.jsonl --json
"""
import argparse
import csv
import difflib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ZOTERO_DIR = os.path.expanduser(os.environ.get("ZOTERO_DIR", "~/Zotero"))
ZOTERO_DB = os.path.join(ZOTERO_DIR, "zotero.sqlite")
ZOTERO_INDEX = os.path.join(ZOTERO_DIR, "claude-assistant-index.json")
CACHE_DIR = os.path.expanduser("~/.cache/arxiv-pdf-claims")

EV_RE = re.compile(r'<!--\s*ev\s+(.*?)-->', re.S)
ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"', re.S)
PANDOC_CITE_RE = re.compile(r'\[(-?@[\w:.#$%&+?<>~/-]+.*?)\]')

QUOTE_STRONG = 0.85   # coverage at or above this: the quote is really there
QUOTE_WEAK = 0.60     # below this: the quote is not in the source
# Only contiguous runs count toward coverage. Summing every matching fragment
# lets a fabricated quote built from plausible domain vocabulary score well on
# confetti alone; a genuine verbatim quote produces one long run.
MIN_BLOCK = 15


# --------------------------------------------------------------------------
# Tag parsing
# --------------------------------------------------------------------------

def parse_tags(text):
    """Return [{attrs..., _sentence, _line}] for every evidence tag."""
    out = []
    for m in EV_RE.finditer(text):
        attrs = {k.lower(): re.sub(r'\s+', ' ', v).strip()
                 for k, v in ATTR_RE.findall(m.group(1))}
        attrs["_sentence"] = preceding_sentence(text[:m.start()])
        attrs["_line"] = text.count("\n", 0, m.start()) + 1
        out.append(attrs)
    return out


def preceding_sentence(before):
    """The claim a tag attaches to: the sentence immediately preceding it."""
    chunk = before.rstrip()
    chunk = EV_RE.sub("", chunk).rstrip()          # ignore an earlier tag
    chunk = chunk.split("\n\n")[-1].strip()        # stay inside the paragraph
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z(\[])', chunk)
    return re.sub(r'\s+', ' ', parts[-1]).strip() if parts else ""


def untagged_after_context(text):
    """Pandoc citations with no evidence tag nearby: the completeness half of CoE."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        if not PANDOC_CITE_RE.search(line):
            continue
        window = "\n".join(lines[i:i + 3])
        if not EV_RE.search(window):
            out.append((i + 1, re.sub(r'\s+', ' ', line).strip()[:110]))
    return out


# --------------------------------------------------------------------------
# Source text resolution
# --------------------------------------------------------------------------

_zotero_map = None


def zotero_pdf_path(item_key):
    """Map a Zotero parent itemKey to its PDF on disk, via a copy of the DB."""
    global _zotero_map
    if _zotero_map is None:
        _zotero_map = {}
        if os.path.exists(ZOTERO_DB):
            tmp = os.path.join(tempfile.gettempdir(), "arxivpdf_zotero_probe.sqlite")
            try:
                shutil.copy2(ZOTERO_DB, tmp)   # Zotero holds a lock while running
                con = sqlite3.connect(tmp)
                rows = con.execute("""
                    SELECT p.key, a.key, ia.path
                    FROM itemAttachments ia
                    JOIN items a ON a.itemID = ia.itemID
                    JOIN items p ON p.itemID = ia.parentItemID
                    WHERE ia.contentType = 'application/pdf' AND ia.path IS NOT NULL
                """).fetchall()
                con.close()
                for parent, att, path in rows:
                    if path.startswith("storage:"):
                        _zotero_map.setdefault(parent, os.path.join(
                            ZOTERO_DIR, "storage", att, path[len("storage:"):]))
            except Exception:
                pass
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
    return _zotero_map.get(item_key)


def pdf_text(path):
    """Extract text once and cache it. Returns None if extraction is unavailable."""
    if not path or not os.path.exists(path):
        return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = re.sub(r'\W+', '_', os.path.abspath(path))[-150:] + ".txt"
    cached = os.path.join(CACHE_DIR, key)
    if os.path.exists(cached) and os.path.getmtime(cached) >= os.path.getmtime(path):
        return open(cached, encoding="utf-8", errors="replace").read()
    txt = None
    if shutil.which("pdftotext"):
        try:
            txt = subprocess.run(["pdftotext", "-q", path, "-"], capture_output=True,
                                 timeout=120).stdout.decode("utf-8", "replace")
        except Exception:
            txt = None
    if txt is None:
        try:
            import pypdf
            txt = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(path).pages)
        except Exception:
            return None
    with open(cached, "w", encoding="utf-8") as f:
        f.write(txt)
    return txt


_index_cache = None


def zotero_abstract(item_key):
    global _index_cache
    if _index_cache is None:
        _index_cache = {}
        if os.path.exists(ZOTERO_INDEX):
            try:
                data = json.load(open(ZOTERO_INDEX, encoding="utf-8"))
                for entry in data.get("chunks", []):
                    meta = entry[1] if isinstance(entry, list) and len(entry) > 1 else entry
                    k = meta.get("itemKey")
                    if k:
                        _index_cache.setdefault(k, []).append(meta.get("text", ""))
            except Exception:
                pass
    parts = _index_cache.get(item_key)
    return "\n".join(parts) if parts else None


def source_text(tag):
    """Return (text, scope) where scope is 'fulltext', 'abstract', or None."""
    if tag.get("pdf"):
        t = pdf_text(os.path.expanduser(tag["pdf"]))
        if t:
            return t, "fulltext"
    if tag.get("zotero"):
        t = pdf_text(zotero_pdf_path(tag["zotero"]))
        if t:
            return t, "fulltext"
        t = zotero_abstract(tag["zotero"])
        if t:
            return t, "abstract"
    return None, None


# --------------------------------------------------------------------------
# Quote location
# --------------------------------------------------------------------------

def normalize(s):
    s = (s or "").replace("­", "")
    s = re.sub(r'-\s*\n\s*', '', s)                       # de-hyphenate line breaks
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl")  # common PDF ligatures
    s = re.sub(r'[^a-z0-9 ]', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()


def locate_quote(quote, text):
    """Return (coverage 0..1, excerpt). Anchored windows keep this fast on big PDFs."""
    qn, tn = normalize(quote), normalize(text)
    if not qn or not tn:
        return 0.0, ""
    if qn in tn:
        i = tn.index(qn)
        return 1.0, tn[max(0, i - 40):i + len(qn) + 40]

    words = sorted({w for w in qn.split() if len(w) >= 6}, key=len, reverse=True)
    spans, seen = [], 0
    for w in words[:4]:
        for m in re.finditer(re.escape(w), tn):
            lo = max(0, m.start() - len(qn))
            spans.append((lo, lo + 2 * len(qn) + len(w)))
            seen += 1
            if seen >= 40:
                break
        if seen >= 40:
            break
    if not spans:
        # no rare anchor: compare against a bounded prefix rather than nothing
        spans = [(0, min(len(tn), 200000))]

    best, excerpt = 0.0, ""
    for lo, hi in spans:
        window = tn[lo:hi]
        sm = difflib.SequenceMatcher(None, qn, window, autojunk=False)
        blocks = [b for b in sm.get_matching_blocks() if b.size >= MIN_BLOCK]
        cov = sum(b.size for b in blocks) / max(1, len(qn))
        if cov > best:
            best = cov
            longest = max(blocks, key=lambda b: b.size, default=None)
            excerpt = (window[max(0, longest.b - 30):longest.b + longest.size + 30]
                       if longest else window[:200])
    return min(best, 1.0), excerpt


# --------------------------------------------------------------------------
# Numeric claims
# --------------------------------------------------------------------------

def implied_tolerance(value_str):
    """Tolerance from significant figures: '458.6' implies +/- 0.05."""
    if "." in value_str:
        return 0.5 * 10 ** -len(value_str.split(".")[1].rstrip())
    return 0.5


def read_artifact_value(spec, base_dir):
    """spec: 'file:path#row=X,col=Y' | 'file:path#path=a.b.c' | 'file:path#re=<pat>'."""
    if not spec.startswith("file:"):
        return None, f"unsupported src scheme: {spec.split(':', 1)[0]}"
    body = spec[len("file:"):]
    path, _, frag = body.partition("#")
    path = os.path.join(base_dir, os.path.expanduser(path))
    if not os.path.exists(path):
        return None, f"artifact not found: {path}"
    frag_kv = dict(kv.split("=", 1) for kv in frag.split(",") if "=" in kv)

    if path.endswith((".csv", ".tsv")):
        delim = "\t" if path.endswith(".tsv") else ","
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            rows = list(csv.reader(f, delimiter=delim))
        if not rows:
            return None, "empty csv"
        header = [h.strip() for h in rows[0]]
        want_row, want_col = frag_kv.get("row"), frag_kv.get("col")
        for r in rows[1:]:
            if want_row and not any(c.strip() == want_row for c in r):
                continue
            if want_col:
                if want_col not in header:
                    return None, f"no column '{want_col}' in {header}"
                return r[header.index(want_col)].strip(), None
            return r[-1].strip(), None
        return None, f"no row matching '{want_row}'"

    if path.endswith(".json"):
        data = json.load(open(path, encoding="utf-8"))
        cur = data
        for part in (frag_kv.get("path") or "").split("."):
            if not part:
                continue
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        return str(cur), None

    body_txt = open(path, encoding="utf-8", errors="replace").read()
    pat = frag_kv.get("re")
    if not pat:
        return None, "text artifact needs #re=<pattern with one capture group>"
    m = re.search(pat, body_txt)
    return (m.group(1).strip(), None) if m else (None, f"pattern not found: {pat}")


# --------------------------------------------------------------------------
# Checking
# --------------------------------------------------------------------------

def check_citation(tag):
    if not tag.get("quote"):
        return {"status": "NO-QUOTE", "detail":
                "citation tag carries no quote= to check the claim against"}
    text, scope = source_text(tag)
    if not text:
        return {"status": "NO-SOURCE-TEXT", "detail":
                "no pdf= path and no readable Zotero PDF or abstract for "
                f"zotero={tag.get('zotero') or '(unset)'}"}
    cov, excerpt = locate_quote(tag["quote"], text)
    if cov >= QUOTE_STRONG:
        return {"status": "QUOTE-VERIFIED", "coverage": round(cov, 2),
                "scope": scope, "excerpt": excerpt}
    if cov >= QUOTE_WEAK:
        return {"status": "QUOTE-WEAK", "coverage": round(cov, 2),
                "scope": scope, "excerpt": excerpt,
                "detail": "quote is close but not verbatim; confirm the wording"}
    if scope == "abstract":
        # Absence from an abstract proves nothing about the paper body.
        return {"status": "QUOTE-UNCHECKED", "coverage": round(cov, 2), "scope": scope,
                "detail": "only the abstract was available; check the full PDF"}
    return {"status": "QUOTE-FABRICATED", "coverage": round(cov, 2), "scope": scope,
            "detail": "quote does not occur in the source full text"}


def check_numeric(tag, base_dir):
    if not tag.get("value"):
        return {"status": "NO-VALUE", "detail": "numeric tag carries no value="}
    got, err = read_artifact_value(tag.get("src", ""), base_dir)
    if err:
        return {"status": "ARTIFACT-MISSING", "detail": err}
    try:
        a, b = float(tag["value"]), float(got)
    except ValueError:
        ok = str(got).strip() == tag["value"].strip()
        return {"status": "NUMERIC-OK" if ok else "NUMERIC-MISMATCH",
                "claimed": tag["value"], "artifact": got}
    tol = float(tag["tol"]) if tag.get("tol") else implied_tolerance(tag["value"])
    ok = abs(a - b) <= tol
    return {"status": "NUMERIC-OK" if ok else "NUMERIC-MISMATCH",
            "claimed": tag["value"], "artifact": got, "tolerance": tol}


NEEDS_LLM = ("QUOTE-WEAK",)
HARD_FAIL = ("QUOTE-FABRICATED", "NUMERIC-MISMATCH", "ARTIFACT-MISSING",
             "NO-QUOTE", "NO-VALUE", "NO-SOURCE-TEXT", "QUOTE-UNCHECKED", "UNTAGGED")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", help="the markdown draft carrying evidence tags")
    ap.add_argument("--require-tags", action="store_true",
                    help="also fail on citations that carry no evidence tag (completeness)")
    ap.add_argument("--entail", help="write (claim, quote) pairs here as JSONL for LLM review")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    text = open(args.path, encoding="utf-8", errors="replace").read()
    base_dir = os.path.dirname(os.path.abspath(args.path))
    tags = parse_tags(text)

    results = []
    for t in tags:
        kind = t.get("kind", "citation")
        r = check_citation(t) if kind == "citation" else check_numeric(t, base_dir)
        r.update({"line": t["_line"], "kind": kind, "claim": t["_sentence"],
                  "src": t.get("src", ""), "quote": t.get("quote", "")})
        results.append(r)

    if args.require_tags:
        for line_no, snippet in untagged_after_context(text):
            results.append({"status": "UNTAGGED", "line": line_no, "kind": "citation",
                            "claim": snippet, "src": "", "quote": "",
                            "detail": "citation with no evidence tag within 3 lines"})

    entail = [{"line": r["line"], "claim": r["claim"], "quote": r["quote"],
               "source": r["src"], "excerpt": r.get("excerpt", ""),
               "question": "Does the quoted evidence support the claim as written? Answer "
                           "SUPPORTED, OVERSTATED (source supports something weaker), or "
                           "UNSUPPORTED, and if OVERSTATED give a conservative restatement."}
              for r in results if r["status"] in ("QUOTE-VERIFIED",) + NEEDS_LLM]

    if args.entail:
        with open(args.entail, "w", encoding="utf-8") as f:
            for row in entail:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        if not results:
            print("No evidence tags found. Add <!--ev ... --> tags, or run with "
                  "--require-tags to list citations that need them.")
        for r in sorted(results, key=lambda x: x["line"]):
            cov = f" cov={r['coverage']}" if "coverage" in r else ""
            scope = f" [{r['scope']}]" if r.get("scope") else ""
            print(f"  L{str(r['line']).rjust(4)}  {r['status'].ljust(17)}{cov}{scope}")
            print(f"        claim: {r['claim'][:96]}")
            if r.get("detail"):
                print(f"        note:  {r['detail']}")
        print()

    fails = [r for r in results if r["status"] in HARD_FAIL]
    weak = [r for r in results if r["status"] in NEEDS_LLM]

    if not args.json:
        if fails:
            print(f"{len(fails)} claim(s) FAILED.\n"
                  "  QUOTE-FABRICATED = the quote is not in the source. The claim is not\n"
                  "    supported; do not ship it.\n"
                  "  NUMERIC-MISMATCH = the prose disagrees with the artifact it cites.\n"
                  "  QUOTE-UNCHECKED = only the abstract was searchable, so nothing is proven\n"
                  "    either way. Attach the PDF with pdf= or check it by hand.\n"
                  "  UNTAGGED = a citation with no evidence chain at all (completeness).")
        if entail:
            print(f"{len(entail)} claim(s) need an LLM entailment check"
                  + (f" (written to {args.entail})" if args.entail else
                     " (rerun with --entail entail.jsonl to capture them)")
                  + ". A verbatim quote proves the source SAYS it; only the entailment "
                    "check proves it SUPPORTS the claim.")
        if not fails and not entail:
            print("All tagged claims verified.")

    sys.exit(1 if (fails or weak) else 0)


if __name__ == "__main__":
    main()
