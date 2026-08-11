# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [2.2.0]

### Added
- Public-facing documentation: README, contributing guide, code of conduct, security policy, issue/PR templates, and CI workflow.
- `updates.json` plugin update manifest and a permanent plugin ID (`claude-assistant@chojay.github.io`) so installed copies receive update notifications.
- `THIRD_PARTY_NOTICES.md` with the licenses of redistributed components (BAAI `bge-small-en-v1.5`, Transformers.js, ONNX Runtime Web), bundled into the packaged `.xpi` together with the project `LICENSE`.
- Query rewriting toggle in Search Configuration (previously only reachable by hand-editing the hidden preference).
- **Dual-mode assistant** with automatic intent routing (`smartChat`): general questions go to Claude directly, research questions trigger retrieval over your Zotero library. Mode can also be forced.
- **Hybrid retrieval** combining BM25 keyword scoring with semantic search via the `bge-small-en-v1.5` model running on-device through Transformers.js. Modes: `keyword`, `semantic`, `hybrid`.
- **Persistent conversation history** stored in local SQLite (`conversation-store.ts`).
- **Local embedding store** in SQLite (`embedding-store.ts`), with embeddings computed in a Web Worker.
- Model selection in preferences: Sonnet 4.6 (default), Opus 4.8, Haiku 4.5, Fable 5, plus Opus 4.7 / 4.6 and legacy Sonnet 4.5.
- `scripts/fetch-model.sh` to download the quantized ONNX embedding weights, which are kept out of git.

### Changed
- Retrieval is now a **pure-TypeScript, fully local pipeline**. The previous external Python RAG server is no longer required.
- Storage moved to Zotero's built-in SQLite rather than a separate vector database.
- Chunk size and chunk overlap preferences are now actually applied during indexing (defaults 2000/400, matching previous behavior). The unimplemented "Automatically index new items" checkbox was removed and moved to the roadmap.
- Packaging (`scripts/package.js`) uses the cross-platform `archiver` library instead of the system `zip` binary, so `npm run package` works on Windows.

### Fixed
- Version strings unified at 2.2.0 across `manifest.json`, `package.json`, `src/index.ts`, and the settings pane.
- Plugin shutdown now closes the conversation database, unregisters the `/claude-assistant/embed` endpoint from Zotero's local server, and drops the `Zotero.ClaudeAssistant` global, so disable/upgrade no longer leaks resources.

### Security
- Indexing and embedding run entirely offline; paper content is only sent to Anthropic at query time, limited to the passages used as context.
- Hardened HTML escaping in the chat window: quotes are now escaped, and model-generated follow-up suggestions no longer flow into inline event handlers (prevents attribute injection from paper titles or model output).

---

> Note: versions prior to 2.2.0 predate this public release and are not documented here. The architecture changed substantially (external Python server and separate vector store were removed), so older internal notes do not apply to this codebase.

[Unreleased]: https://github.com/chojay/zotero-claude-assistant/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/chojay/zotero-claude-assistant/releases/tag/v2.2.0
