# Ollama Paper Summarizer

Batch-summarize a folder of academic PDFs into Markdown, entirely on your own
machine, so the summaries become a searchable reference layer and an idea bank
for writing.

The itch: a Zotero library grows faster than anyone reads it, and the papers
you half-remember are exactly the ones you want to lean on when drafting a fresh
note. This walks the whole library, extracts each PDF's text, and asks a local
[Ollama](https://ollama.com/) model for a structured technical summary (key
findings, quantitative results, and stated limitations), writing one `<paper>_summary.md` per PDF into
an Obsidian folder. Then an Obsidian similarity plugin -
[Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) -
embeds those summaries and surfaces the relevant ones next to whatever you are
writing, so the library augments the draft instead of sitting unread.

![Workflow: a library of PDFs from a Zotero storage tree is read by pdfplumber across a process pool, summarized by a local model running on the Apple Silicon GPU through Ollama (shown as its llama mark), written as one structured Markdown file per paper, and surfaced by an Obsidian similarity plugin while writing; summarized locally with no cloud and no API key](pipeline-ollama-v2.png)

> **Correction: the v1 notes are withdrawn.** An earlier version of this page
> said the tool had turned about 3,900 papers into a searchable idea bank. It
> did write that many `_summary.md` files from my Zotero library, on personal
> time and on a personal machine, across incremental runs between mid-2024 and
> early 2025. But the v1 script called Ollama's `generate()` with
> no options, so it never set a context length. Every call ran at the default
> context length, and Ollama's FAQ of that period (the v0.3.0 and v0.5.7
> releases) gives that default as 2,048 tokens, unless a model's own Modelfile
> sets more (not checked for the models I used). A journal paper's extracted
> text is usually far longer than that. The calls did not fail (the script logs
> a failed call and writes no note), so for long papers the model most likely saw
> only part of the text, and the script had no way to tell. The cause is inferred from the code and from the notes; I did
> not re-run v1 to watch it happen. Because nothing marks which notes were cut,
> none of the v1 notes for long papers can be trusted, and I no longer use the
> v1 notes as a reference.
>
> The script in this folder is fixed: every call sets `num_ctx`, a paper that
> does not fit is cut on purpose with a visible marker or skipped with a logged
> reason, and the server's `prompt_eval_count` is checked after each call (see
> [Context window](#context-window-set-on-purpose-and-checked) below).

> **Field record.** A later check on my own library took a random 300 of the v1
> notes for papers that also have a checked note, and compared them with the
> notes written for the same papers by a separate pipeline that checks each
> quote against the paper text and the numbers in its findings against the
> quotes or the text (not published here). In the v1 notes, 527 of 991 decimal numbers (53.2%) appear
> nowhere in the paper's extracted full text, references included; in the
> checked notes, 13 of 3,706 (0.4%). And 23.3% of the v1 notes contain fewer than
> 30% of the content words of the paper's own title, against 0.7%. Read these as
> upper bounds: the comparison text came from a different PDF extractor than the
> one v1 used, so some numbers may have been extracted differently rather than
> invented, and the checked notes were written from that same comparison text.
> The figures show the v1 notes are unreliable; they do not separate truncation
> from other model errors.

## Pipeline

```
folder of PDFs (e.g. a Zotero storage tree)
  -> pdfplumber        extract text per PDF (skip >= 70 pages)  [process pool, cores-2]
  -> context check     estimate prompt tokens vs num_ctx; cut with a marker, or skip
  -> Ollama (local)    structured summary, num_ctx set on every call
  -> fit check         prompt_eval_count vs the estimate; discard if the server cut the input
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
    --model phi4 \
    --num-ctx 16384 \
    --on-overflow truncate    # or: skip
```

Tests (no Ollama and no PDFs needed; a fake client stands in for the server):

```bash
python3 -m unittest discover -s tests -v
```

Point `--out` at a folder inside your Obsidian vault and let Smart Connections
index it. See [examples/example-summary.md](examples/example-summary.md) for the
output shape (a synthetic, illustrative summary - no real paper), and
[GOTCHAS.md](GOTCHAS.md) for two lessons: a worked example of the real payoff
(three open-access Nature papers summarized, compared, and distilled into one
recurring theme, and the prompt fix it forced), and the context-window failure
behind the correction above.

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

Stated Limitations and Open Questions (3 points maximum)
[Limitations the paper states and questions it leaves open. Required, even if the
paper claims none.]

Focus on core technical content; omit introductions, license details, and references.
```

Why each constraint earns its place:

- **A fixed three-section format** (findings, quantitative results, limitations)
  means every note has the same shape, so the embeddings compare like with like
  and you can skim a hundred at a glance.
- **Hard caps** (5 paragraphs, 5 points) stop the model from padding a thin paper
  to look substantial; a short summary of a thin paper is the correct output.
- **"Quantitative results with values and units"** forces numbers into the note.
  Numbers are what you actually reach for when writing, and they are what the
  early freeform prompts dropped first. This is also why a cut input is so
  damaging: the model is told to produce numbers, and when the part of the paper
  that holds them is missing, it still produces numbers.
- **"Omit introductions, license details, and references"** strips the
  boilerplate that otherwise dominates a short summary and pollutes similarity
  search with generic phrasing.
- **A required limitations section.** This one was added *after* the fact: a
  findings-and-numbers summary silently drops what a paper cannot do, which makes
  an idea bank uniformly over-optimistic and hides the most useful cross-paper
  signal. See [GOTCHAS.md](GOTCHAS.md) for the worked example that forced it. The
  withdrawn v1 notes predate this line.

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
  in this section: that one keeps *retrieval* local and sends only the most relevant
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
  library of thousands of papers is processed incrementally: adding papers and
  re-running only touches the new ones, and an interrupted overnight run resumes
  where it stopped. The check is *non-empty*, not merely *exists*, so a
  zero-byte file from a killed run is retried rather than treated as done. The
  flip side: an existing note is never rewritten, so to replace notes made by an
  older version, point `--out` at a fresh folder.
- **A hard page cap.** PDFs at or above 70 pages (books, theses) are skipped.
  The page cap alone did not protect anything in v1: a 20-page paper was already
  far past the default context length. The context check below is what does.

### Context window: set on purpose, and checked

- **`num_ctx` on every call** (`--num-ctx`, default 16384), with `num_predict`
  set to the tokens reserved for the answer (`--reserve-tokens`, default 1536).
  Pick a value your model supports and your memory allows; a larger context
  costs memory and time per call.
- **Before the call:** the script estimates the prompt in tokens from its
  length in characters, using a low characters-per-token rate (3.0) so the
  estimate errs high for English prose. Dense text (formulas, tables, CJK
  scripts) can tokenize at fewer characters per token, and then the estimate
  errs low. If the prompt would not fit in `num_ctx` minus the
  reserve, `--on-overflow truncate` (the default) keeps the start of the paper
  and adds a marker the model can see (`[TRUNCATED BY THE SUMMARIZER: only the
  first N of M characters ...]`), and the saved note opens with a line that says
  it covers only part of the paper. `--on-overflow skip` writes nothing and logs
  the reason.
- **After the call:** the script compares the server's `prompt_eval_count` with
  a second, lenient estimate of the prompt size. If the server evaluated far
  fewer tokens than were sent, the input was cut somewhere the script did not
  control, so the summary is discarded with a logged reason. A missing
  `prompt_eval_count`, or an answer that stopped at `num_predict`
  (`done_reason == "length"`), is also discarded. So is a call where the server
  evaluated as many prompt tokens as the budget allows (`num_ctx` minus the
  reserve): the estimate was too low for that text, and the server may have cut
  it. If a paper keeps too little text after the cut (under 2,000 characters),
  it is skipped rather than summarized from almost nothing.
- **Limits of the check.** The character-based estimate is crude; it catches a
  large cut (the v1 case), not a small one. It assumes Latin-script prose; for
  dense or CJK text the budget check above is what catches an overflow, and a
  cut that stays just under the budget can still be missed. If you need a tight
  bound, count tokens with the model's own tokenizer. Ollama reuses its cache
  for a repeated prompt prefix and does not count those tokens again, so a
  duplicate PDF processed right after its twin can be rejected as cut (not
  tested). Truncation keeps the start of a paper,
  so results reported late in a long paper are missing from its note, and the
  note says so.
- The tests in [tests/](tests/) use a fake client that behaves like a server
  with a small context: they check that `num_ctx` is always sent, that the
  truncate and skip paths both work, and that a server-side cut is caught. They
  do not run a model.

## AI-assisted build notes

The extraction/concurrency scaffolding is straightforward and Claude wrote most
of it. The parts that actually mattered were judgment, not code: the prompt went
through several rounds before it stopped writing marketing-flavored abstracts
and started reporting numbers, and the page cap plus the skip-existing logic came
from watching real runs (a thesis that ran for twenty minutes and produced
mush; an interrupted run that left zero-byte files the next pass had to be taught
to retry).

The failure that mattered most was one neither of us looked for. The v1 call to
`generate()` passed no options, and the code read cleanly: one call, one
response, one file. Nothing in the code asked how much of the paper the model
actually received, and the server raised no error. The notes looked fluent and
full of numbers, which is exactly what the prompt asked for. It took a later,
separate pipeline
that checks quotes, and most numbers, against the paper text to show how many
of them were not in the paper. The fix is small (set `num_ctx`, read `prompt_eval_count`), and
this time it came with tests that use a fake server with a small context, so
the check is exercised without a model. The lesson I took: for any model call,
check what the server reports it consumed, not only what it returned.

---

<sub>The llama in the diagram is the [Ollama](https://ollama.com/) logo, used only to identify the tool; Ollama and its logo are trademarks of their owner.</sub>
