#!/usr/bin/env python3
"""Batch-summarize a folder of academic PDFs into Markdown, fully locally.

Point it at a library of papers (e.g. a Zotero storage tree) and an output
folder inside an Obsidian vault. It walks the tree, extracts text with
pdfplumber, and asks a local Ollama model for a structured technical summary
(key findings, quantitative results, stated limitations), writing one
`<paper>_summary.md` per PDF.

Context window (fixed after v1): every call sets `num_ctx` explicitly. Before
the call, the script estimates the prompt size in tokens; a paper that does not
fit is either cut on purpose, with a visible marker in the text the model sees
and a note at the top of the summary (`--on-overflow truncate`, the default),
or skipped with a logged reason (`--on-overflow skip`). After the call, the
server's `prompt_eval_count` is compared with the estimate; if the server
evaluated far fewer tokens than were sent, the input was cut somewhere else and
the summary is discarded with a logged reason instead of being saved.

Fully local: Ollama runs the model on your machine, so no paper text and no API
key ever leave it. Idempotent: an existing non-empty summary is skipped, so you
can add papers and re-run. PDF text extraction is parallelized across a process
pool (cores - 2); model calls are issued concurrently in batches.

Requirements: `pip install pdfplumber mdutils ollama`, plus a running Ollama
(`ollama serve`) with the chosen model pulled (`ollama pull phi4`).

Usage:
    python3 ollama_paper_summarizer.py --input ~/Zotero/storage \
        --out "<vault>/Imports/paper-summaries" --model phi4 --num-ctx 16384
"""
import argparse
import asyncio
import multiprocessing
import os
import random
from concurrent.futures import ProcessPoolExecutor

MAX_PAGES = 70  # skip very long PDFs (books, theses)
MIN_KEPT_CHARS = 2000  # a cut that keeps less paper text than this is skipped instead

# The default prompt is tuned for a materials/hardware research library; edit
# SYSTEM_PROMPT and FORMAT_BLOCK for your own field.
SYSTEM_PROMPT = (
    "You are an expert research scientist. Analyze and summarize the technical "
    "findings and advancements in a research paper, focusing on concrete details "
    "and quantifiable improvements."
)

PROMPT_HEAD = "Summarize the main technical findings and advancements in the following text.\n\n"

FORMAT_BLOCK = """

Format:
Key Technical Findings (5 paragraphs maximum)
[The most significant technical findings and advancements. Focus on novel
materials, methods, or processes and their quantifiable improvements.]

Quantitative Results (5 points maximum)
[Key quantitative results - property improvements, performance gains, efficiency
- with specific values and units where available.]

Stated Limitations and Open Questions (3 points maximum)
[Limitations the paper itself states, and questions it leaves open. If the paper
claims none, say so. This section is required - it is what lets a later
cross-paper read find a recurring weakness, not only a recurring strength.]

Focus on core technical content; omit introductions, license details, and references."""

TRUNCATION_MARKER = (
    "\n\n[TRUNCATED BY THE SUMMARIZER: only the first {kept} of {total} characters "
    "of this paper fit the context window. Do not describe results from the "
    "missing part.]\n"
)


class ContextSettings(object):
    """How much text one call may carry, and how to tell that it fit.

    num_ctx            context length sent to Ollama on every call.
    reserve_tokens     tokens kept free for the answer (also sent as num_predict).
    chars_per_token    low chars-per-token rate used to estimate the prompt size
                       before the call. For English prose it overestimates
                       tokens, so a paper is cut a little early rather than late;
                       dense text (formulas, tables, CJK) can tokenize at fewer
                       characters per token, and then it underestimates. The
                       after-call budget check covers that case.
    min_eval_fraction  after the call, the server must report a prompt_eval_count
                       of at least this fraction of the estimate (with the
                       estimate made at `check_chars_per_token`); fewer means the
                       server dropped part of the input.
    check_chars_per_token  a HIGH chars-per-token rate for that after-call check,
                       so dense text does not raise false alarms.
    on_overflow        'truncate' (cut with a marker) or 'skip' (log and skip).
    """

    def __init__(self, num_ctx=16384, reserve_tokens=1536, chars_per_token=3.0,
                 min_eval_fraction=0.8, check_chars_per_token=5.0,
                 on_overflow="truncate"):
        if on_overflow not in ("truncate", "skip"):
            raise ValueError("on_overflow must be 'truncate' or 'skip'")
        if reserve_tokens >= num_ctx:
            raise ValueError("reserve_tokens must be smaller than num_ctx")
        self.num_ctx = num_ctx
        self.reserve_tokens = reserve_tokens
        self.chars_per_token = chars_per_token
        self.min_eval_fraction = min_eval_fraction
        self.check_chars_per_token = check_chars_per_token
        self.on_overflow = on_overflow

    @property
    def prompt_budget_tokens(self):
        return self.num_ctx - self.reserve_tokens

    def options(self):
        return {"num_ctx": self.num_ctx, "num_predict": self.reserve_tokens}


def estimate_tokens(chars, chars_per_token):
    return int(chars / float(chars_per_token)) + 1


def build_prompt(text):
    return PROMPT_HEAD + text + FORMAT_BLOCK


def fit_text(text, settings):
    """Return (text_to_send, info) where info describes what happened.

    info = {"status": "fit" | "truncated" | "skip", "kept": int, "total": int,
            "reason": str}
    """
    total = len(text)
    fixed_chars = len(SYSTEM_PROMPT) + len(build_prompt(""))
    budget_chars = int(settings.prompt_budget_tokens * settings.chars_per_token)
    if estimate_tokens(fixed_chars + total, settings.chars_per_token) <= settings.prompt_budget_tokens:
        return text, {"status": "fit", "kept": total, "total": total, "reason": ""}
    reason = ("estimated %d prompt tokens > budget %d (num_ctx %d - reserve %d)" % (
        estimate_tokens(fixed_chars + total, settings.chars_per_token),
        settings.prompt_budget_tokens, settings.num_ctx, settings.reserve_tokens))
    if settings.on_overflow == "skip":
        return None, {"status": "skip", "kept": 0, "total": total, "reason": reason}
    marker_room = len(TRUNCATION_MARKER.format(kept=total, total=total)) + 8
    kept = max(0, budget_chars - fixed_chars - marker_room)
    if kept < MIN_KEPT_CHARS:
        reason += "; only %d characters of paper text would fit (minimum %d)" % (kept, MIN_KEPT_CHARS)
        return None, {"status": "skip", "kept": 0, "total": total, "reason": reason}
    cut = text[:kept] + TRUNCATION_MARKER.format(kept=kept, total=total)
    return cut, {"status": "truncated", "kept": kept, "total": total, "reason": reason}


def _field(resp, name):
    """Read a field from an Ollama response (dict, or the newer response object)."""
    if resp is None:
        return None
    if isinstance(resp, dict):
        return resp.get(name)
    value = getattr(resp, name, None)
    if value is None:
        try:
            value = resp[name]
        except Exception:
            value = None
    return value


def check_fit(prompt_chars, resp, settings):
    """Return '' if the server evaluated about as many tokens as were sent, else a reason."""
    evaluated = _field(resp, "prompt_eval_count")
    if evaluated is None:
        return "server reported no prompt_eval_count; cannot confirm the input fit"
    expected_min = int(estimate_tokens(prompt_chars, settings.check_chars_per_token)
                       * settings.min_eval_fraction)
    if evaluated >= settings.prompt_budget_tokens:
        return ("server evaluated %d prompt tokens, at or above the prompt budget %d; the "
                "estimate was too low for this text, so the input was probably cut by the "
                "server" % (evaluated, settings.prompt_budget_tokens))
    if evaluated < expected_min:
        return ("server evaluated %d prompt tokens, expected at least %d for %d characters; "
                "the input was probably cut by the server" % (evaluated, expected_min, prompt_chars))
    if _field(resp, "done_reason") == "length":
        return "the answer hit num_predict (%d tokens) and is cut off" % settings.reserve_tokens
    return ""


def count_pdfs(parent_path):
    return sum(1 for _, _, files in os.walk(parent_path)
               for f in files if f.lower().endswith(".pdf"))


def extract_text_from_pdf(file_path, counter, total):
    import pdfplumber
    with counter["lock"]:
        counter["value"] += 1
        current = counter["value"]
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            n = len(pdf.pages)
            print(f"{current} / {total} : reading '{os.path.basename(file_path)}'")
            if n >= MAX_PAGES:
                print(f"  skipping '{os.path.basename(file_path)}' ({n} pages >= {MAX_PAGES})")
                return ""
            for page in pdf.pages:
                pt = page.extract_text()
                if pt:
                    text += pt
    except Exception as e:
        print(f"  skipping '{os.path.basename(file_path)}': {e}")
    return text


async def generate_summary(client, text, model, settings, name="paper", log=print):
    """Return (summary_or_None, info). Never sends a prompt without num_ctx."""
    sent, info = fit_text(text, settings)
    if info["status"] == "skip":
        log(f"  skipping '{name}': {info['reason']}")
        return None, info
    if info["status"] == "truncated":
        log(f"  cutting '{name}' to {info['kept']} of {info['total']} characters: {info['reason']}")
    prompt = build_prompt(sent)
    try:
        resp = await client.generate(model=model, system=SYSTEM_PROMPT, prompt=prompt,
                                     options=settings.options())
    except Exception as e:
        log(f"  summary generation failed for '{name}': {e}")
        info = dict(info, status="error", reason=str(e))
        return None, info
    problem = check_fit(len(SYSTEM_PROMPT) + len(prompt), resp, settings)
    if problem:
        log(f"  discarding summary of '{name}': {problem}")
        return None, dict(info, status="rejected", reason=problem)
    summary = _field(resp, "response") or None
    if summary and info["status"] == "truncated":
        summary = ("> Note: this summary covers only the first %d of %d characters of the "
                   "paper; the rest did not fit the context window (num_ctx %d).\n\n%s"
                   % (info["kept"], info["total"], settings.num_ctx, summary))
    return summary, info


def save_summary_as_markdown(summary, file_path):
    from mdutils.mdutils import MdUtils
    md = MdUtils(file_name=file_path)
    md.new_paragraph(summary)
    md.create_md_file()


async def process_pdf(client, pdf_path, save_path, pool, counter, total, model, settings):
    name = os.path.basename(pdf_path)
    md_path = os.path.join(save_path, name.rsplit(".", 1)[0] + "_summary.md")
    if os.path.exists(md_path) and os.path.getsize(md_path) > 0:
        print(f"skipping '{name}' (summary exists)")
        return
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(pool, extract_text_from_pdf, pdf_path, counter, total)
    if not text:
        return
    summary, _info = await generate_summary(client, text, model, settings, name=name)
    if summary:
        await loop.run_in_executor(None, save_summary_as_markdown, summary, md_path)
        print(f"  saved '{os.path.basename(md_path)}'")


async def run(parent_path, save_path, model, settings):
    from multiprocessing import Manager
    from ollama import AsyncClient
    total = count_pdfs(parent_path)
    print(f"Total PDFs found: {total}")
    os.makedirs(save_path, exist_ok=True)
    paths = [os.path.join(dp, f) for dp, _, files in os.walk(parent_path)
             for f in files if f.lower().endswith(".pdf")]
    random.shuffle(paths)  # spread long/short PDFs across the run

    pool_size = max(1, multiprocessing.cpu_count() - 2)
    pool = ProcessPoolExecutor(max_workers=pool_size)
    client = AsyncClient()
    with Manager() as mgr:
        counter = mgr.dict(value=0, lock=mgr.Lock())
        batch = pool_size * 2
        for i in range(0, len(paths), batch):
            await asyncio.gather(*(
                process_pdf(client, p, save_path, pool, counter, total, model, settings)
                for p in paths[i:i + batch]))
    pool.shutdown()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="folder of PDFs (walked recursively), e.g. a Zotero storage tree")
    ap.add_argument("--out", required=True, help="output folder for *_summary.md (point it inside your Obsidian vault)")
    ap.add_argument("--model", default="phi4", help="Ollama model tag (default phi4; llama3, qwen2, etc.)")
    ap.add_argument("--num-ctx", type=int, default=16384,
                    help="context length sent to Ollama on every call (default 16384; "
                         "keep it within what the model supports and your memory allows)")
    ap.add_argument("--reserve-tokens", type=int, default=1536,
                    help="tokens kept free for the answer, also sent as num_predict (default 1536)")
    ap.add_argument("--on-overflow", choices=("truncate", "skip"), default="truncate",
                    help="a paper that does not fit: cut it with a visible marker (default), or skip it")
    args = ap.parse_args()
    try:
        settings = ContextSettings(num_ctx=args.num_ctx, reserve_tokens=args.reserve_tokens,
                                   on_overflow=args.on_overflow)
    except ValueError as e:
        ap.error(str(e))
    asyncio.run(run(os.path.expanduser(args.input), os.path.expanduser(args.out),
                    args.model, settings))


if __name__ == "__main__":
    main()
