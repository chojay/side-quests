# AI Tooling

Two tools that put local AI next to the papers I actually work with, built so the library never has to leave the machine. One is interactive (ask questions, get a cited answer); one is batch (turn the whole library into a durable summary layer). They sit at opposite ends of the local/cloud tradeoff.

| Project | What it does | Docs |
|---|---|---|
| [zotero-claude-assistant/](zotero-claude-assistant/) | Zotero 7 plugin: one chat box that auto-routes between direct Claude chat and RAG over your own paper library, with retrieval and embeddings running 100% on-device; only the most relevant passages go to the Claude API. | [README](zotero-claude-assistant/README.md) (install, usage, build) |
| [ollama-paper-summarizer/](ollama-paper-summarizer/) | Batch-summarizes a folder of PDFs into Markdown with a local Ollama model - fully offline, nothing sent anywhere - so the summaries become a searchable idea bank that an Obsidian similarity plugin surfaces while you write. | [README](ollama-paper-summarizer/README.md) |

The contrast is the point: the plugin keeps *retrieval* local and sends only the most relevant snippets to Claude for an interactive answer; the summarizer keeps *everything* local and leaves behind a greppable summary layer. Same corpus, two ends of the local/cloud tradeoff.

## Ollama Paper Summarizer

A batch pipeline: walk a Zotero storage tree, extract each PDF's text with pdfplumber (parallelized across a process pool), and ask a local [Ollama](https://ollama.com/) model for a structured technical summary (key findings + quantitative results) written as one `<paper>_summary.md` per PDF into an Obsidian folder. An Obsidian similarity plugin ([Smart Connections](https://github.com/brianpetro/obsidian-smart-connections)) then embeds those summaries and surfaces the relevant ones next to a fresh note, so the library augments the draft. Fully local (no API key, no upload), idempotent (existing summaries skipped), and steered by one carefully constrained prompt so every note has the same greppable shape rather than a random abstract. In practice it has summarized ~3,900 papers from my Zotero library entirely offline (no tokens billed, nothing uploaded), across incremental runs between mid-2024 and early 2025. A bit old now (llama3 -> qwen2 -> phi4) and due for a re-run on a current model, which is a one-line model-tag change. Full writeup, prompt, and an example in its [README](ollama-paper-summarizer/README.md).

## Claude Research Assistant for Zotero

### The itch

I wanted to ask questions of my own paper library, in the app where the library already lives, without uploading the library anywhere and without babysitting a Python sidecar. Earlier internal versions of this plugin did run an external Python RAG server with a separate vector store; v2.2.0 deleted all of that and replaced it with a pure-TypeScript pipeline that runs inside Zotero itself. No server process, no external vector database, no cloud indexing.

### Architecture in one paragraph

It is a Zotero 7 bootstrapped plugin: `bootstrap.js` registers chrome content programmatically and loads an esbuild IIFE bundle that becomes `Zotero.ClaudeAssistant`. Each query hits an intent router (heuristics plus whether papers are selected) that picks direct chat or research mode. Research mode retrieves from two local engines: a section-aware BM25 index (title weighted 3.0x, abstract 2.0x, references skipped, a materials-science synonym map at half weight, and a stopword tokenizer that deliberately preserves short scientific tokens like Hf, Cu, eV, 2D) and a semantic index built from `bge-small-en-v1.5`, a quantized ~32 MB ONNX model producing 384-dim vectors via Transformers.js inside a ChromeWorker. Vectors persist as Float32 BLOBs in a local SQLite database next to the Zotero data; the BM25 index serializes to JSON. The two rankings merge with Reciprocal Rank Fusion (k=60), and only the most relevant passages are sent to the Claude API as context for the answer, which cites `[Source N]` links that click through to the actual items in Zotero.

### Privacy stance

- Indexing and embedding are entirely offline. Paper text reaches Anthropic only at query time, and only the retrieved snippets used as context for that one question.
- The only runtime network destination is `api.anthropic.com`. No telemetry of any kind.
- Two honest non-runtime exceptions: Zotero's own plugin updater polls the `updates.json` manifest on GitHub, and the build script fetches the embedding weights from Hugging Face at build time.
- The API key lives in Zotero's preference store, which the plugin's `SECURITY.md` discloses. In practice that means plaintext in the Zotero profile rather than the OS keychain - that blunter framing is mine, and it is the honest tradeoff of using Zotero's built-in prefs. The key is never written to debug logs.
- A `POST /claude-assistant/embed` endpoint on Zotero's built-in server lets other local tools reuse the embedder. It is localhost-only, exposes no key and no library content, and is unregistered on shutdown.

### Engineering highlights

- **ESM in a ChromeWorker, by force.** `importScripts()` cannot load the ESM Transformers.js bundle, so the worker fetches the bundle as text, parses the minified export block to discover internal names, strips it, rewrites `import.meta.url`, and indirect-evals the result into worker scope. Ugly, documented, and it works.
- **Hybrid ranking that degrades gracefully.** BM25 and cosine scores merge via RRF; if the embedding model is unavailable for any reason, every path falls back to BM25-only rather than failing.
- **Model-change auto-invalidation.** The embedding store records which model produced its vectors and wipes them all if the configured model changes, so stale-dimension vectors can never poison a search.
- **Thinking-block-safe extraction.** Claude Fable 5 always emits thinking blocks; the client filters responses to text blocks and maps a `refusal` stop reason to a readable message instead of showing raw API output.
- **Sampling params by allowlist.** Newer Claude models return 400 on `temperature`; `supportsSamplingParams()` withholds sampling params per model family. This was discovered the honest way, via actual 400s.
- **Clean shutdown.** Disable or upgrade closes both SQLite stores, saves the index, unregisters the endpoint, removes injected DOM nodes, and drops the global. Nothing leaks between plugin versions.

### Honest limitations

- No streaming. `Zotero.HTTP` cannot stream, so the client uses a 5-minute timeout, and a long Opus-tier answer simply takes a while with no progress indicator.
- Encrypted or image-only PDFs have no extractable text and silently do not index; the troubleshooting section documents this rather than hiding it.
- If the ONNX weights were missing at package time, semantic and hybrid search are silently absent while keyword search keeps working. CI deliberately builds without the weights to keep that path exercised.
- Intent routing is heuristic. Short queries with research intent can land in chat mode; the UI provides a mode override for exactly that reason.
- One dead method remains in `claude-api.ts` (`generateEmbedding`, a leftover from the earlier server-based design that would have summarized chunks via the API). It has no call sites, so every executed indexing path stays fully local, but it is slated for deletion precisely because dead code that contradicts a privacy guarantee should not get a second chance.

### Where the real repo will live

The plugin is built to ship from its own standalone repo (`github.com/chojay/zotero-claude-assistant`), because Zotero's update mechanism needs a stable `updates.json` URL and release `.xpi` assets to point installed copies at. The `manifest.json`, `updates.json`, and `package.json` here intentionally reference that repo and should be read in that light; until it goes live with releases, this folder carries the full source and the working install path is building the `.xpi` yourself (`npm install && npm run build`, per the plugin's [README](zotero-claude-assistant/README.md)).
