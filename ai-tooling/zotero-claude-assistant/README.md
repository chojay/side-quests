<div align="center">

<img src="addon/content/icons/icon-96.png" alt="Claude Research Assistant" width="96" height="96">

# Claude Research Assistant for Zotero

**Chat with Claude or search your own Zotero library with on-device RAG, right inside Zotero 7.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Zotero 7+](https://img.shields.io/badge/Zotero-7%2B-CC2936.svg)](https://www.zotero.org/)
[![Version](https://img.shields.io/badge/version-2.2.0-green.svg)](CHANGELOG.md)

</div>

---

Claude Research Assistant is a [Zotero 7](https://www.zotero.org/) plugin that puts an AI assistant next to your library. Ask a general question and it talks to [Claude](https://www.anthropic.com/claude) directly. Ask a research question and it retrieves the most relevant passages from *your* papers first, then answers with citations back to the source items.

Retrieval runs **entirely on your machine**. There is no Python server, no external vector database, and no cloud indexing service. Your papers are only sent to Anthropic when you actually ask a question that needs them.

## Highlights

- **Dual mode, automatic routing.** One chat box. The plugin detects research intent (or whether you have papers selected) and routes the query to either direct chat or RAG over your library. You can also force a mode.
- **Hybrid retrieval, fully local.** Combines **BM25** keyword scoring with **semantic search** using the [`bge-small-en-v1.5`](https://huggingface.co/Xenova/bge-small-en-v1.5) embedding model running in-browser via [Transformers.js](https://huggingface.co/docs/transformers.js). Choose `keyword`, `semantic`, or `hybrid`.
- **No backend to run.** Storage uses Zotero's own SQLite. Embeddings are computed in a Web Worker. Nothing leaves your machine during indexing.
- **Conversations that persist.** Chat history and the embedding index live in local SQLite databases alongside your Zotero data.
- **Pick your Claude model.** Sonnet, Opus, Haiku, and Fable are all selectable in preferences.
- **Privacy first.** Indexing and embedding are offline. No telemetry. Your API key stays in Zotero's preference store.

## How it works

```
                       ┌──────────────────────────┐
   Your question  ───▶ │   Intent router          │
                       │  (detectResearchIntent /  │
                       │   selected papers / mode) │
                       └─────────┬────────────┬────┘
                       research  │            │  chat
                                 ▼            ▼
                   ┌─────────────────┐   ┌──────────────┐
                   │  Local RAG      │   │  Direct chat │
                   │  BM25 + vector  │   │  with Claude │
                   │  over your libs │   └──────┬───────┘
                   └────────┬────────┘          │
                            │ top passages      │
                            ▼                   ▼
                   ┌──────────────────────────────────┐
                   │     Claude API (Anthropic)        │
                   │  answer + citations to your items │
                   └──────────────────────────────────┘
```

The retrieval half (`src/modules/local-rag.ts`) is a pure-TypeScript implementation: it tokenizes and chunks your items, removes stopwords, applies a domain synonym map, and scores with BM25. The semantic half (`src/modules/embedding-service.ts` plus the worker in `addon/content/scripts/embedding-worker.js`) embeds chunks and the query with `bge-small-en-v1.5` and blends the two signals for the final ranking.

## Installation

### Requirements

- **Zotero 7.0 or later** (the plugin targets `strict_min_version` 6.999)
- A **Claude API key** from the [Anthropic Console](https://console.anthropic.com/)
- Node.js 18+ only if you want to build from source

### Install the released plugin

1. Download the latest `claude-assistant.xpi` from the [Releases](https://github.com/chojay/zotero-claude-assistant/releases) page.
2. In Zotero, open **Tools → Add-ons** (or **Tools → Plugins**).
3. Click the gear icon and choose **Install Plugin From File...**
4. Select the `.xpi` file and restart Zotero.

### Configure

1. Open **Edit → Settings → Claude Assistant** (Zotero → Settings on macOS).
2. Paste your Claude API key (it begins with `sk-ant-`).
3. Choose a model. **Sonnet 4.6** is the recommended default for cost and performance.
4. Optionally enable **query rewriting** under Search Configuration: Claude rephrases your question before retrieval for better recall, at the cost of one extra API call per research question. Chunk size and overlap for indexing are also configurable there.

## Usage

1. Open the assistant from **Tools → Claude Research Assistant** (or its toolbar button).
2. Type a question:
   - General questions go straight to Claude: *"Explain how BM25 differs from cosine similarity."*
   - Research questions search your library first: *"What does my library say about high-k dielectric breakdown?"*
3. To ground a conversation in specific items, select one or more papers in Zotero before asking, or right-click an item to chat about it directly.
4. Answers in research mode include citations pointing back to the source items.

### Retrieval modes

| Mode | What it uses | Best for |
|------|--------------|----------|
| `keyword` | BM25 only | Exact terms, names, formulas, acronyms |
| `semantic` | `bge-small-en-v1.5` embeddings | Paraphrased / conceptual queries |
| `hybrid` (default) | BM25 + embeddings blended | General use; most robust ranking |

### Claude models

Selectable in preferences:

| Model | Notes |
|-------|-------|
| **Sonnet 4.6** | Recommended. Best cost/performance. Default. |
| **Opus 4.8** | Most capable. Higher cost. |
| **Haiku 4.5** | Fastest, lowest cost. |
| **Fable 5** | Frontier, premium pricing. |
| Opus 4.7 / Opus 4.6 / Sonnet 4.5 | Also available (Sonnet 4.5 is legacy). |

## Privacy and data flow

- **Indexing and embedding are 100% local.** BM25 and the embedding model run on your machine; no paper text is uploaded to build the index.
- **Papers reach Anthropic only at query time**, and only the passages selected as context for the specific question you asked.
- **Your API key** is stored in Zotero's preference store, not in this repo or any external service.
- **No telemetry.** The plugin collects no usage data.
- **Local HTTP endpoint.** The plugin registers `POST /claude-assistant/embed` on Zotero's built-in local server so external tools on your machine can reuse the embedder. It is reachable only from localhost and is unregistered when the plugin is disabled.

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities and how key material is handled.

## Build from source

```bash
# 1. Install dependencies
npm install

# 2. Fetch the embedding model weights (~32 MB ONNX, not committed to git)
#    Required if you want semantic / hybrid search to work in your build.
./scripts/fetch-model.sh

# 3. Compile TypeScript and assemble the addon
npm run build

# 4. Package into an installable .xpi (output: dist/claude-assistant.xpi)
npm run package
```

Useful scripts:

| Command | Action |
|---------|--------|
| `npm run build` | `tsc` then assemble the addon (`scripts/build.js`) |
| `npm run watch` | Recompile TypeScript on change |
| `npm run package` | Build, then zip into a `.xpi` (`scripts/package.js`) |
| `npm run lint` | ESLint over `src/**/*.ts` |
| `npm run format` | Prettier over `src` |

> **Note on the embedding model.** The model config and tokenizer JSON *are* committed (so the architecture is visible), but the ~32 MB quantized ONNX weight is intentionally git-ignored and downloaded by `scripts/fetch-model.sh` from [`Xenova/bge-small-en-v1.5`](https://huggingface.co/Xenova/bge-small-en-v1.5). If you package without running that script, the keyword (BM25) search still works but semantic/hybrid search will be unavailable.

## Project structure

```
zotero-claude-assistant/
├── addon/
│   ├── manifest.json                      # Zotero plugin manifest (v2.2.0)
│   ├── bootstrap.js                       # Plugin lifecycle hooks
│   └── content/
│       ├── chat-dialog.xhtml              # Chat window UI
│       ├── preferences.xhtml / .js        # Settings UI (API key, model, mode)
│       ├── scripts/embedding-worker.js    # Web Worker running the embedder
│       ├── models/bge-small-en-v1.5/      # Model config + tokenizer (weights fetched)
│       └── icons/                         # Plugin icons
├── src/
│   ├── index.ts                           # Entry point
│   ├── addon.ts                           # Main addon class + smartChat router
│   ├── prefs.ts                           # Preference accessors and defaults
│   └── modules/
│       ├── claude-api.ts                  # Anthropic client + detectResearchIntent
│       ├── local-rag.ts                   # BM25 indexing/search over Zotero SQLite
│       ├── embedding-service.ts           # Embedding orchestration
│       ├── embedding-store.ts             # Vector persistence (SQLite)
│       └── conversation-store.ts          # Chat history persistence (SQLite)
├── scripts/
│   ├── build.js                           # Build/assemble script
│   ├── package.js                         # .xpi packaging script
│   └── fetch-model.sh                     # Download ONNX embedding weights
├── updates.json                           # Zotero plugin update manifest
├── THIRD_PARTY_NOTICES.md                 # Licenses of redistributed components
└── package.json
```

## Troubleshooting

**"Claude API key not configured."** Open **Settings → Claude Assistant** and paste a key beginning with `sk-ant-`.

**Semantic / hybrid search returns nothing, keyword works.** The ONNX weights were not present when the plugin was packaged. Run `./scripts/fetch-model.sh` and rebuild.

**Research mode finds 0 papers.** Make sure your library has been indexed and that the items have extractable text (encrypted or image-only PDFs will not index).

**API errors.** Confirm the key is valid and funded in the [Anthropic Console](https://console.anthropic.com/), and check your network connection.

## Roadmap

- [ ] Conversation management and export to Zotero notes
- [ ] Integration with Zotero's citation picker
- [ ] Configurable retrieval weights in the UI (chunking is already configurable)
- [ ] Automatic indexing of newly added items
- [ ] Additional embedding model options
- [ ] Localization

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md) before opening an issue or pull request.

## License

[MIT](LICENSE) © chojay

Redistributed third-party components (the BAAI `bge-small-en-v1.5` model, MIT; [Transformers.js](https://github.com/huggingface/transformers.js), Apache-2.0; [ONNX Runtime Web](https://github.com/microsoft/onnxruntime), MIT) remain under their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

This is an independent community plugin, not affiliated with or endorsed by Anthropic or Zotero. "Claude" is a trademark of Anthropic, PBC; "Zotero" is a trademark of the Corporation for Digital Scholarship.

## Acknowledgments

- [Anthropic Claude](https://www.anthropic.com/claude) for the language model
- [Transformers.js](https://huggingface.co/docs/transformers.js) (Apache-2.0) and the [`Xenova/bge-small-en-v1.5`](https://huggingface.co/Xenova/bge-small-en-v1.5) ONNX port of BAAI's MIT-licensed embedding model for on-device embeddings
- The [Zotero](https://www.zotero.org/) team and the Zotero plugin community
