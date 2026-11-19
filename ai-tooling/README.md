# AI Tooling

Local AI tools next to the papers I actually work with, built so the library never has to leave the machine, plus guard rails for the AI agents that run on the same machine. The two paper tools sit at opposite ends of the local/cloud tradeoff: one is interactive (ask questions, get a cited answer), one is batch (turn the whole library into a durable summary layer). The guard rails are a queue that runs memory-heavy jobs one at a time and a hook that keeps an agent's email to drafts.

| Project | What it does | Docs |
|---|---|---|
| [zotero-claude-assistant/](zotero-claude-assistant/) | Zotero plugin (7 up to 9.x): one chat box that auto-routes between direct Claude chat and RAG over your own paper library, with retrieval and embeddings running on your machine; only the most relevant passages go to the Claude API. | [README](zotero-claude-assistant/README.md) (install, usage, build) |
| [ollama-paper-summarizer/](ollama-paper-summarizer/) | Batch-summarizes a folder of PDFs into Markdown with a local Ollama model - fully offline, nothing sent anywhere - so the summaries become a searchable idea bank that an Obsidian similarity plugin surfaces while you write. | [README](ollama-paper-summarizer/README.md) |
| [heavy-job-queue/](heavy-job-queue/) | A one-at-a-time queue for memory-heavy jobs on a Mac (admission by free memory, a per-job cap on the whole process tree's phys_footprint, a peak-use history), a Claude Code hook that points agents at it, and an optional watchdog. Built after parallel agent model jobs kernel-panicked a 64 GB Mac. | [README](heavy-job-queue/README.md) |
| [email-send-guard/](email-send-guard/) | A Claude Code `PreToolUse` hook that keeps a coding agent from sending email: a small quoting scanner plus shlex read each shell command the way bash would, then it blocks Gmail CLI sends without `--draft`, raw mail commands, curl to SMTP or a mail API, and mail code handed to an interpreter or a nested shell, and can allow a configured SMTP helper under exact allow rules the owner writes. A tripwire, not a sandbox: two red-team rounds are pinned as tests, and its README lists what a text check cannot see. A draft-only companion tool is in `draft-tool/`. | [README](email-send-guard/README.md) |

For the two paper tools, the contrast is the point: the plugin keeps *retrieval* local and sends only the most relevant snippets to Claude for an interactive answer; the summarizer keeps *everything* local and leaves behind a greppable summary layer. Same corpus, two ends of the local/cloud tradeoff.

## Ollama Paper Summarizer

A batch pipeline: walk a Zotero storage tree, extract each PDF's text with pdfplumber (parallelized across a process pool), and ask a local [Ollama](https://ollama.com/) model for a structured technical summary (key findings, quantitative results and stated limitations) written as one `<paper>_summary.md` per PDF into an Obsidian folder. An Obsidian similarity plugin ([Smart Connections](https://github.com/brianpetro/obsidian-smart-connections)) then embeds those summaries and surfaces the relevant ones next to a fresh note, so the library augments the draft. Fully local (no API key, no upload), idempotent (existing summaries skipped), and steered by one carefully constrained prompt so every note has the same greppable shape rather than a random abstract. Its v1 runs over my Zotero library (on personal time and a personal machine, mid-2024 to early 2025, llama3 -> qwen2 -> phi4) wrote about 3,900 notes, but the v1 script never set a context length, so long papers were most likely cut without notice (inferred from the code and the notes, not re-run); those notes are withdrawn. The current script sets `num_ctx` on every call, cuts or skips an overlong paper on purpose, and checks the server's `prompt_eval_count`, with fake-client tests. Full writeup, prompt, and an example in its [README](ollama-paper-summarizer/README.md).

## Claude Research Assistant for Zotero

### The itch

I wanted to ask questions of my own paper library, in the app where the library already lives, without uploading the library anywhere and without babysitting a Python sidecar. Earlier private versions of this plugin did run an external Python RAG server with a separate vector store; v2.2.0 deleted all of that and replaced it with a pure-TypeScript pipeline that runs inside Zotero itself. No server process, no external vector database, no cloud indexing.

### Architecture in one paragraph

It is a Zotero 7 bootstrapped plugin: `bootstrap.js` registers chrome content programmatically and loads an esbuild IIFE bundle that becomes `Zotero.ClaudeAssistant`. Each query hits an intent router (heuristics plus whether papers are selected) that picks direct chat or research mode. Research mode retrieves from two local engines: a section-aware BM25 index (title weighted 3.0x, abstract 2.0x, references skipped, a materials-science synonym map at half weight, and a stopword tokenizer that deliberately preserves short scientific tokens like Hf, Cu, eV, 2D) and a semantic index built from `e5-base-v2`, a quantized ONNX model of about 110 MB producing 768-dim vectors via Transformers.js inside a ChromeWorker (documents and queries get e5's `passage:` and `query:` prefixes). Vectors persist as Float32 BLOBs in a local SQLite database next to the Zotero data; the BM25 index serializes to JSON. The two rankings merge with Reciprocal Rank Fusion (k=60), and only the most relevant passages are sent to the Claude API as context for the answer, which cites `[Source N]` links that click through to the actual items in Zotero.

### Privacy stance

- Indexing and embedding run on your machine. Paper text reaches Anthropic only at query time, and only the retrieved snippets used as context for that one question.
- This was not true of the published 2.2.0, which made the same claim. Its worker never pinned ONNX Runtime's `wasmPaths`, so the runtime kept a CDN default (read from the code; not observed, because the 2.2.0 embedder never loaded at all). Since 2.3.0 the worker points ONNX Runtime at the wasm files bundled in the `.xpi`, and throws if the wasm backend is missing (not yet run in Zotero with the real weights). One gap is still open: those settings apply only if the worker finds the Transformers.js `env` object in the bundle.
- The only runtime network destination of the plugin's own code is `api.anthropic.com`. No telemetry of any kind.
- Two non-runtime exceptions: Zotero's own plugin updater polls the `updates.json` manifest on GitHub, and the build script fetches the embedding weights from Hugging Face at build time.
- The API key lives in Zotero's preference store, which the plugin's `SECURITY.md` discloses. In practice that means plaintext in the Zotero profile rather than the OS keychain - that blunter framing is mine, and it is the honest tradeoff of using Zotero's built-in prefs. The key is never written to debug logs.
- A `POST /claude-assistant/embed` endpoint on Zotero's built-in server lets other local tools reuse the embedder. It is localhost-only, exposes no key and no library content, and is unregistered on shutdown.

### Engineering highlights

- **ESM in a ChromeWorker, by force.** `importScripts()` cannot load the ESM Transformers.js bundle, so the worker fetches the bundle as text, parses the minified export block to discover internal names, strips it, rewrites `import.meta.url`, and indirect-evals the result into worker scope. Ugly, documented, and it works.
- **Hybrid ranking that degrades, and says so.** BM25 and cosine scores merge via RRF; if the embedding model is unavailable, every path falls back to BM25-only rather than failing. Until 2.3.0 that fallback was silent, and the published 2.2.0 ran keyword-only the whole time without anyone noticing. Since 2.3.0 the build fails without the weights, startup warns, and `GET /claude-assistant/status` reports the reason.
- **Model-change auto-invalidation.** The embedding store records which model and dimension produced its vectors and wipes them all if either changes; since 2.4.0 it also drops any stored vector of the wrong byte length when it reads it.
- **Thinking-block-safe extraction.** Claude Fable 5 always emits thinking blocks; the client filters responses to text blocks and maps a `refusal` stop reason to a readable message instead of showing raw API output.
- **Sampling params by model family.** Newer Claude models return 400 on `temperature`; `supportsSamplingParams()` withholds sampling params for a fixed list of model prefixes. This was discovered the honest way, via actual 400s. The list is a denylist, so a newer model that also rejects `temperature` will 400 until it is added.
- **Clean shutdown.** Disable or upgrade closes both SQLite stores, saves the index, unregisters the endpoint, removes injected DOM nodes, and drops the global. Nothing leaks between plugin versions.

### Honest limitations

- No streaming. `Zotero.HTTP` cannot stream, so the client uses a 5-minute timeout, and a long Opus-tier answer simply takes a while with no progress indicator.
- Encrypted or image-only PDFs have no extractable text and silently do not index; the troubleshooting section documents this rather than hiding it.
- Without the ONNX weights, `npm run build` stops with an error that lists the missing artifacts. A keyword-only .xpi needs an explicit opt-in (`ZCA_ALLOW_DEGRADED=1 npm run package`), and `npm run doctor` reports the same gaps before you build.
- Intent routing is heuristic. Short queries with research intent can land in chat mode; the UI provides a mode override for exactly that reason.
- No test suite, and no CI run yet. The build, lint and packaging steps were run by hand (see the plugin README), but nothing in the repo records 2.4.0 running in Zotero with the real embedding weights, and it has not been tested on Zotero 10.

### Where the plugin lives

The plugin lives in this repo; there is no standalone repo. Its `manifest.json` points Zotero's update check at the `updates.json` in this folder, and `package.json` points at this repo and its issue tracker. No release `.xpi` is published yet, so the working install path is building the `.xpi` yourself (`npm install`, `./scripts/fetch-model.sh`, then `npm run package`, per the plugin's [README](zotero-claude-assistant/README.md)).
