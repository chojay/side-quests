#!/usr/bin/env python3
"""Batch-summarize a folder of academic PDFs into Markdown, fully locally.

Point it at a library of papers (e.g. a Zotero storage tree) and an output
folder inside an Obsidian vault. It walks the tree, extracts text with
pdfplumber, and asks a local Ollama model for a structured technical summary
(key findings + quantitative results), writing one `<paper>_summary.md` per
PDF. Those summaries become a searchable reference layer and idea bank: an
Obsidian similarity plugin (Smart Connections) then surfaces the relevant ones
while you write a fresh note.

Fully local: Ollama runs the model on your machine, so no paper text and no API
key ever leave it. Idempotent: an existing non-empty summary is skipped, so you
can add papers and re-run. PDF text extraction is parallelized across a process
pool (cores - 2); model calls are issued concurrently in batches.

Requirements: `pip install pdfplumber mdutils ollama`, plus a running Ollama
(`ollama serve`) with the chosen model pulled (`ollama pull phi4`).

Usage:
    python3 ollama_paper_summarizer.py --input ~/Zotero/storage \
        --out "<vault>/Imports/paper-summaries" --model phi4
"""
import argparse
import asyncio
import multiprocessing
import os
import random
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

import pdfplumber
from mdutils.mdutils import MdUtils
from ollama import AsyncClient

MAX_PAGES = 70  # skip very long PDFs (books, theses) that blow the context window

# The default prompt is tuned for a materials/hardware research library; edit
# SYSTEM_PROMPT and the format block for your own field.
SYSTEM_PROMPT = (
    "You are an expert research scientist. Analyze and summarize the technical "
    "findings and advancements in a research paper, focusing on concrete details "
    "and quantifiable improvements."
)


def count_pdfs(parent_path):
    return sum(1 for _, _, files in os.walk(parent_path)
               for f in files if f.lower().endswith(".pdf"))


def extract_text_from_pdf(file_path, counter, total):
    with counter["lock"]:
        counter["value"] += 1
        current = counter["value"]
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            n = len(pdf.pages)
            print(f"{current} / {total} : reading '{os.path.basename(file_path)}'")
            if n >= MAX_PAGES:
                print(f"  skipping '{os.path.basename(file_path)}' ({n} pages > {MAX_PAGES})")
                return ""
            for page in pdf.pages:
                pt = page.extract_text()
                if pt:
                    text += pt
    except Exception as e:
        print(f"  skipping '{os.path.basename(file_path)}': {e}")
    return text


async def generate_summary(client, text, model):
    user_prompt = f"""Summarize the main technical findings and advancements in the following text.

{text}

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
    try:
        resp = await client.generate(model=model, system=SYSTEM_PROMPT, prompt=user_prompt)
        return resp.get("response") or None
    except Exception as e:
        print(f"  summary generation failed: {e}")
        return None


def save_summary_as_markdown(summary, file_path):
    md = MdUtils(file_name=file_path)
    md.new_paragraph(summary)
    md.create_md_file()


async def process_pdf(client, pdf_path, save_path, pool, counter, total, model):
    name = os.path.basename(pdf_path)
    md_path = os.path.join(save_path, name.rsplit(".", 1)[0] + "_summary.md")
    if os.path.exists(md_path) and os.path.getsize(md_path) > 0:
        print(f"skipping '{name}' (summary exists)")
        return
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(pool, extract_text_from_pdf, pdf_path, counter, total)
    if not text:
        return
    summary = await generate_summary(client, text, model)
    if summary:
        await loop.run_in_executor(None, save_summary_as_markdown, summary, md_path)
        print(f"  saved '{os.path.basename(md_path)}'")


async def run(parent_path, save_path, model):
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
                process_pdf(client, p, save_path, pool, counter, total, model)
                for p in paths[i:i + batch]))
    pool.shutdown()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="folder of PDFs (walked recursively), e.g. a Zotero storage tree")
    ap.add_argument("--out", required=True, help="output folder for *_summary.md (point it inside your Obsidian vault)")
    ap.add_argument("--model", default="phi4", help="Ollama model tag (default phi4; llama3, qwen2, etc.)")
    args = ap.parse_args()
    asyncio.run(run(os.path.expanduser(args.input), os.path.expanduser(args.out), args.model))


if __name__ == "__main__":
    main()
