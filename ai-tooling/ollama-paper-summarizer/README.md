# Ollama Paper Summarizer

Batch-summarize a folder of academic PDFs into Markdown, entirely on your own
machine, so the summaries become a searchable reference layer and an idea bank
for writing.

The itch: a Zotero library grows faster than anyone reads it, and the papers
you half-remember are exactly the ones you want to lean on when drafting a fresh
note. This walks the whole library, extracts each PDF's text, and asks a local
[Ollama](https://ollama.com/) model for a structured technical summary (key
findings + quantitative results), writing one `<paper>_summary.md` per PDF into
an Obsidian folder. Then an Obsidian similarity plugin -
[Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) -
embeds those summaries and surfaces the relevant ones next to whatever you are
writing, so the library augments the draft instead of sitting unread.

![Workflow: a library of PDFs from a Zotero storage tree is read by pdfplumber across a process pool, summarized by a local model running on the Apple Silicon GPU through Ollama, written as one structured Markdown file per paper, and surfaced by an Obsidian similarity plugin while writing; about 3,900 papers summarized locally with no cloud and no API key](workflow.png)

> **Scale so far: ~3,900 papers summarized, entirely offline.** Across
> incremental runs between mid-2024 and early 2025 it produced ~3,900
> `_summary.md` files from my Zotero library on a personal machine - no tokens
> billed, nothing uploaded, the model running locally the whole time. Because
> the run is idempotent, each pass only touches papers added since the last one,
> so it ran unattended and grew with the library rather than as one marathon.
>
> **Status: a bit old (2024-2025), and I plan to re-run it soon.** It was built
> against llama3, moved to qwen2, and last ran on phi4; the model tag is a flag,
> so re-running the whole library on a current local model is a one-line change.
> The summaries it already produced still serve as the idea bank; this note is
> the code, cleaned up for reuse.

## Pipeline

```
folder of PDFs (e.g. a Zotero storage tree)
  -> pdfplumber        extract text per PDF (skip > 70 pages)   [process pool, cores-2]
  -> Ollama (local)    structured summary: findings + quantitative results
  -> <paper>_summary.md written into an Obsidian folder          [idempotent: skip existing]
  -> Smart Connections embeds the summaries; surfaces related ones while you write
```

Run:

```bash
# one-time: install a local model and the deps
ollama pull phi4
pip install pdfplumber mdutils ollama

python3 ollama_paper_summarizer.py \
    --input ~/Zotero/storage \
    --out "<vault>/Imports/paper-summaries" \
    --model phi4
```

Point `--out` at a folder inside your Obsidian vault and let Smart Connections
index it. See [examples/example-summary.md](examples/example-summary.md) for the
output shape (a synthetic, illustrative summary - no real paper).

## The prompt (why the summaries are consistent, not random)

The whole tool is a loop around one carefully shaped prompt. A bare "summarize
this paper" gives a different, marketing-flavored abstract every time; a rigid
format with explicit constraints gives comparable, greppable notes that Smart
Connections can actually match against. The prompt is two parts.

System prompt (sets the role, once):

```
You are an expert research scientist. Analyze and summarize the technical
findings and advancements in a research paper, focusing on concrete details
and quantifiable improvements.
```

User prompt (the extracted PDF text, then a fixed format):

```
Summarize the main technical findings and advancements in the following text.

<paper text>

Format:
Key Technical Findings (5 paragraphs maximum)
[The most significant technical findings and advancements. Focus on novel
materials, methods, or processes and their quantifiable improvements.]

Quantitative Results (5 points maximum)
[Key quantitative results - property improvements, performance gains, efficiency
- with specific values and units where available.]

Focus on core technical content; omit introductions, license details, and references.
```

Why each constraint earns its place:

- **A fixed two-section format** (findings, then quantitative results) means every
  note has the same shape, so the embeddings compare like with like and you can
  skim a hundred at a glance.
- **Hard caps** (5 paragraphs, 5 points) stop the model from padding a thin paper
  to look substantial; a short summary of a thin paper is the correct output.
- **"Quantitative results with values and units"** forces numbers into the note.
  Numbers are what you actually reach for when writing, and they are what the
  early freeform prompts dropped first.
- **"Omit introductions, license details, and references"** strips the
  boilerplate that otherwise dominates a short summary and pollutes similarity
  search with generic phrasing.

The default wording is tuned for a materials/hardware library; both prompts are
constants at the top of the script - edit them for your field, keep the
structural constraints.

## Why local

- **Nothing leaves the machine.** Ollama runs the model locally; no paper text
  and no API key are ever sent anywhere. A personal library is exactly the kind
  of corpus you do not want to upload page by page.
- **Cost is time, not tokens.** Summarizing a few hundred PDFs on a cloud API
  adds up; locally it is just an overnight run.
- This is the offline sibling of the [Zotero plugin](../zotero-claude-assistant/)
  in this section: that one keeps *retrieval* local and sends only the winning
  passages to Claude for an interactive answer; this one keeps *everything*
  local and produces a durable, greppable summary layer.

## Engineering notes

- **Inference runs on-device, on the GPU.** The model runs entirely locally
  through Ollama, which executes on the Apple Silicon GPU via its **Metal**
  backend - no PyTorch, no CUDA, no remote endpoint. Nothing about a personal
  library leaves the machine, and there is no API key or token budget in the
  loop; the only cost is wall-clock. Swapping the model is a `--model` flag, so
  the same pipeline rides whatever local model is strongest that month (this ran
  llama3 -> qwen2 -> phi4).
- **CPU/GPU pipelining via async + a process pool.** PDF text extraction is
  CPU-bound and embarrassingly parallel, so it runs across a
  `ProcessPoolExecutor` sized to `cores - 2` (headroom for the system and the
  model server), while summary generation is issued concurrently against the
  **async** Ollama client. Extraction of the next batch overlaps inference on the
  current one, so the GPU is not left idle waiting on pdfplumber. Work is
  submitted in batches of `pool_size * 2` rather than all at once - deliberate
  **backpressure** that keeps thousands of queued PDFs from swamping the model
  server. The file list is shuffled so a run does not stall on a cluster of long
  PDFs landing on the same worker.
- **Idempotent, resumable runs.** A non-empty `_summary.md` is skipped, so a
  ~3,900-paper library is processed incrementally: adding papers and re-running
  only touches the new ones, and an interrupted overnight run resumes where it
  stopped. The check is *non-empty*, not merely *exists*, so a zero-byte file
  from a killed run is retried rather than treated as done.
- **A hard page cap, honestly.** PDFs at or above 70 pages are skipped rather
  than truncated: books and theses blow the context window, and a silently
  truncated summary is worse than none. Raising the cap means shortening the
  text some other way first.

## AI-assisted build notes

The extraction/concurrency scaffolding is straightforward and Claude wrote most
of it. The parts that actually mattered were judgment, not code: the prompt went
through several rounds before it stopped writing marketing-flavored abstracts
and started reporting numbers, and the page cap plus the skip-existing logic came
from watching real runs (a thesis that ran for twenty minutes and produced
mush; an interrupted run that left zero-byte files the next pass had to be taught
to retry). The output quality is only as good as the local model of the day,
which is the honest reason this is worth re-running now rather than trusting a
2024 summary.
