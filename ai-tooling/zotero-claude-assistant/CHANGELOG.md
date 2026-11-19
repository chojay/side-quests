# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Repository housekeeping and documentation corrections after the move into the
`side-quests` repository. The plugin version stays 2.4.0.

### Fixed
- `scripts/build.js` and `scripts/doctor.js` could not find `onnxruntime-web` on current Node.
  The 2.3.0 change resolved `onnxruntime-web/package.json`, but the package's `exports` map does
  not export that path, so Node throws `ERR_PACKAGE_PATH_NOT_EXPORTED`. Both scripts now look for
  the package directory on Node's lookup paths, including the copy nested under
  `@huggingface/transformers`.
- `scripts/fetch-model.sh` removes its `.partial` download on every exit path (failure, size
  check, Ctrl-C), and `.gitignore` ignores `*.partial` under the model folder.

### Removed
- The dead `ClaudeClient.generateEmbedding()` method, a leftover of the earlier server design
  that would have sent chunk text to the API. It had no call sites.
- The plugin's own `.github/` folder (CI workflow, issue and pull request templates). GitHub
  runs workflows only from the repository root, so that workflow never ran here.

### Changed
- `package.json`, the manifest `update_url` and `updates.json` now point at this repository.
  There is no standalone `zotero-claude-assistant` repository. No release `.xpi` is published
  yet, so the `update_link` in `updates.json` names a release that does not exist yet.

### Documentation
- README, ARCHITECTURE and SECURITY now say plainly which 2.2.0 claims were false (fully local
  embedding, working hybrid search, correct `[Source N]` links) and which version fixed each.
- The README states the tested scope: the manifest declares Zotero 7 up to 9.x, nothing has
  been tested on Zotero 10, and no CI runs. It lists the build steps that were run by hand.
- Links that pointed at the nonexistent standalone repository now point at this repository.

## [2.4.0]

Switches the embedding model from `BAAI/bge-small-en-v1.5` (384-dim) to
`intfloat/e5-base-v2` (768-dim).

The reason is not benchmark quality, it is data. An external indexer (not in this repo)
had embedded papers with e5-base-v2 when 2.4.0 was written. The plugin's own SQLite store,
meanwhile, was empty, because its embedder had never worked (see 2.3.0). Using the same
model and the same `passage:`/`query:` prefixes makes the query vectors from
`POST /claude-assistant/embed` intended to be comparable with such a store. The plugin uses
the int8-quantized ONNX export and truncates input, so the agreement between the two
producers has not been measured.

> [!WARNING]
> **Breaking for existing embeddings.** The vector dimension changes from 384 to 768. Any embeddings produced by an earlier
> version are invalid and are discarded by the existing model-tag mechanism. Re-run
> **Generate Embeddings** after upgrading. Keyword (BM25) search is unaffected and needs
> no re-indexing.

### Changed
- Embedding model is now `intfloat/e5-base-v2`, 768-dim, MIT licensed. Model config and
  tokenizer files are committed under `addon/content/models/e5-base-v2/`; the quantized ONNX
  weight (roughly 110 MB, up from 32 MB) is fetched by `scripts/fetch-model.sh` from
  `Xenova/e5-base-v2`.
- **e5 is prefix-sensitive**, so `EmbeddingService.embed()` and `embedBatch()` now take a
  required `kind: 'query' | 'passage'` argument and apply the corresponding prefix. It is
  required rather than defaulted on purpose: using the wrong prefix does not raise an error,
  it just silently retrieves worse, which is precisely the failure mode this project has
  already been bitten by. Stored chunks use `passage:`, searches use `query:`, the same
  convention as that external indexer.
- `POST /claude-assistant/embed` accepts an optional `"kind"` field (`"query"` by default,
  since that is what external search tools ask for) and echoes it back alongside `dim`.
- `GET /claude-assistant/status` now reports the embedding `dim`.
- `EMBEDDING_DIM` is exported from `embedding-service` and imported by `embedding-store`.
  It was previously a second independent literal in the store, the classic duplicate
  constant that goes stale on exactly this kind of model change.
- `embedding-store` validates that a decoded BLOB is exactly `EMBEDDING_DIM * 4` bytes and
  drops it otherwise, which catches leftover vectors from a previous model. In 2.3.0 the
  validating decode ran only in the unused single-row `getEmbedding()`; the bulk
  `getAllEmbeddings()` load that search ranks against still used the old one-liner. Since
  2.4.0 both go through the same validating decode, and the bulk load logs how many rows
  it dropped.
- A worker that answers `init` with an error is no longer reported as `init_timeout`.
  `handleWorkerMessage()` resolved `null` for an error reply, the same value as a timeout,
  so in 2.3.0 every worker failure showed the timeout message and the fetch-model.sh remedy.
  It now resolves the error payload, so `runtime_missing` and `model_weights_missing` can be
  reported. Not yet observed in a running Zotero.
- Mean pooling, already what the worker requested, is now also the *correct* pooling: it is
  what e5-base-v2's own `1_Pooling/config.json` specifies. bge-small-en-v1.5 expects CLS
  pooling, so the previous configuration was mismatched with the model it shipped.
- `scripts/build.js`, `scripts/doctor.js`, and `scripts/fetch-model.sh` updated for the new
  model directory, source repository, and roughly 110 MB size threshold.

### Documentation
- README, ARCHITECTURE, and THIRD_PARTY_NOTICES updated for the new model, dimension,
  license attribution (Microsoft rather than BAAI, both MIT), and the prefix convention.

## [2.3.0]

Diagnostic release. An installed copy was found with a dead embedder: the embeddings
table was empty, `POST /claude-assistant/embed` answered
`503 Embedding service not available`, and every "hybrid" search silently returned
keyword-only results without ever saying so. The cause was mundane (the gitignored ONNX
weights were never fetched, and the tree had no `node_modules`, so the build could not
vendor Transformers.js or the ONNX runtime). The reason it went unnoticed was
architectural: four separate layers degraded quietly and the build still exited 0.

This release does not add retrieval features. It makes that class of failure impossible
to ship and impossible to miss.

A follow-up multi-agent audit of the codebase (every finding handed to a separate verifier
told to refute it before it was accepted) surfaced 42 confirmed defects, of which the six most
severe are addressed here. A later re-check showed that one of those six, the "doubled model
path", was wrong for the pinned Transformers.js 3.8.1 (see Changed). The remaining 36 are
lower-severity and are not fixed in this release.

### Added
- `scripts/doctor.js` (`npm run doctor`) preflight and diagnostic tool. Verifies version
  consistency across all five files carrying a version string, confirms committed plugin
  assets are present, and reports exactly which semantic-search artifacts are missing along
  with the command that fixes each one. `npm run doctor -- --check-runtime` additionally
  probes a running Zotero and reports whether the *installed* plugin has a live embedder.
- `GET /claude-assistant/status` endpoint. Returns 200 with the true state whenever the
  plugin is running (500 only on an internal error)
  (`embedding.available`, reason `code`, `remedy`, embedding count, indexed items,
  and whether retrieval is `hybrid-capable` or `keyword-only`), so an external caller can
  tell "plugin not running" apart from "plugin running with a dead embedder". The `/embed`
  503 alone could not express that difference.
- `EmbeddingService.getStatus()` returning a typed `EmbeddingUnavailableCode`
  (`worker_spawn_failed`, `init_timeout`, `runtime_missing`, `model_weights_missing`,
  `worker_error`, `unknown`) with a human-readable remedy for each.
- `src/version.ts` as the single source of truth for the plugin version.
- Startup notification when the embedder is unavailable, stating that retrieval is
  keyword-only and naming the fix, instead of only writing to `Zotero.debug`.

### Changed
- **`npm run build` now fails when semantic-search artifacts are missing.** Previously each
  missing artifact produced a `console.warn` and the build still exited 0, so a normal-looking
  `.xpi` could ship with half of retrieval dead. Set `ZCA_ALLOW_DEGRADED=1`
  (`ZCA_ALLOW_DEGRADED=1 npm run build`) to build a keyword-only plugin deliberately.
  The `--allow-degraded` flag works only on `node scripts/build.js` itself;
  `npm run build -- --allow-degraded` does not pass it through to that script.
- `npm run build` runs `npm run doctor -- --quiet` first, so version drift fails the build.
- `scripts/build.js` now explicitly verifies `model_quantized.onnx` exists and is a plausible
  size. The previous recursive model-directory copy succeeded with only the config and
  tokenizer JSON present, which is exactly the state of a fresh clone.
- `scripts/build.js` resolves `onnxruntime-web` through Node's resolver instead of assuming
  npm hoisted it to the top level of `node_modules`. It arrives transitively via
  `@huggingface/transformers`, so the hardcoded top-level path silently missed the nested layout.
- `scripts/fetch-model.sh` downloads to a `.partial` file and verifies size and leading byte
  before moving it into place, so a truncated download or an HTML error page can no longer
  land on disk looking like a valid model.
- `/claude-assistant/embed` 503 responses now include `code`, `reason`, `remedy`, and `model`.
- The "Embedding service not available. Model files may be missing." notification in
  `generateEmbeddings()` now reports the actual cause and remedy.
- **The init payload now carries `modelRoot` and `modelId` separately.** The audit claimed that the old single path (one URL passed as both
  `env.localModelPath` and the model id) was doubled and could never resolve. That was wrong:
  Transformers.js 3.8.1 joins `localModelPath` only for a valid Hugging Face model id and skips
  the join for a URL id, so the old path already named the right file (checked against the
  library code, not in a running Zotero). This is a clarity change, not a fix.

### Fixed
- **`chunkText()` could loop forever and exhaust memory**, reachable from the preferences pane
  alone. The sentence-boundary adjustment only guarantees `end > start + chunkSize/2`, while
  `start` advances by `end - overlap`. Any overlap above half the chunk size moves `start`
  backwards. The pane allows chunk size down to 500 with overlap up to 1000, and ships a default
  overlap of 400, so setting chunk size to 500 was enough to hang indexing. Overlap is now clamped
  to `floor(chunkSize / 2) - 1` and the loop has a hard progress guard.
- **A transient index read failure permanently destroyed the index.** `initialize()` caught any
  load error, logged to `Zotero.debug`, and set `isLoaded = true` with an empty map; shutdown then
  serialized that empty index over the good file. One cloud-storage placeholder, file lock, or AV
  scan was enough. A `loadFailed` flag now makes `saveIndex()` refuse to write an empty index over
  an existing file, and the write uses `IOUtils.write(..., { tmpPath })` so it is atomic rather
  than a truncate-in-place.
- **`[Source N]` citations could point at the wrong paper.** `answerWithRAGResults` re-sorts chunks
  by year and numbers that order as Source 1..N, but returned only the response, so the caller
  rendered its own relevance-ordered array. Clicking a citation opened a different item than Claude
  cited. The method now returns `{ response, orderedSources }` and both call sites render the
  ordering that was actually numbered.
- **Embedding BLOB decode had a silent fallback that produced garbage vectors.**
  `new Float32Array(row.embedding.buffer || row.embedding)` fell through to the array-like
  constructor when the storage layer returned a plain octet array, yielding a 1536-element vector
  of byte magnitudes 0 to 255 instead of 384 unit-norm floats. Neither branch threw and no length
  was validated, so cosine similarity silently ranked against noise. A validating decode was
  added (byte length a non-zero multiple of 4), but in 2.3.0 only the unused single-row read
  called it; the bulk load used by search was fixed in 2.4.0.
- `VERSION` was referenced in `src/addon.ts` but never imported. Extracting it to
  `src/version.ts` fixes the missing binding and avoids the `index.ts` to `addon.ts` import
  cycle that re-exporting it from `index.ts` would have created.
- `EmbeddingService.initialize()` got separate branches for an init timeout and for a worker
  that answered and reported a failure. In 2.3.0 the second branch was unreachable, because
  worker error replies also resolved `null`; fixed in 2.4.0.
- The `/claude-assistant/status` endpoint is unregistered on shutdown alongside `/embed`.

### Security
- **Corrected a violated privacy claim.** The 2.2.0 README stated "Indexing and embedding are
  100% local" and ARCHITECTURE stated "Indexing and embedding never touch the network". The code
  did not support that. The worker never assigned `env.backends.onnx.wasm.wasmPaths`, so ONNX
  Runtime kept the Transformers.js default, a `jsdelivr.net` CDN URL. The `.wasm` files that
  `scripts/build.js` vendors into the `.xpi` were dead weight, and first-use embedding would have
  needed internet access from inside a ChromeWorker. (This is read from the code, not observed:
  the embedder never loaded in 2.2.0, because the model weights and runtime were missing from
  the build.) The worker now pins
  `wasmPaths` to the vendored directory and throws if the ONNX wasm backend is not present rather
  than silently falling back to a remote fetch. One related gap stays open: these settings are
  applied only when the worker finds the Transformers.js `env` object after evaluating the bundle.

### Documentation
- `ARCHITECTURE.md` gains a "Failure surface and observability" section with a
  layer-by-layer table of what each component used to do and what it does now.
- The design bullet claiming that degrading to BM25-only "instead of failing" was a virtue
  is corrected: falling back is the right runtime behavior, hiding the fallback is a bug.
- `README.md` build instructions include the verification step, and the troubleshooting entry
  for semantic search is rewritten. The old entry said semantic search "returns nothing", but
  the actual symptom is the opposite and far more confusing: it returns perfectly plausible
  keyword results and never indicates that anything is wrong.

## [2.2.0]

> [!WARNING]
> **Known problems in this release, fixed in 2.3.0.** The embedder never loaded (the model weights
> and runtime were missing from the build), so "hybrid" and "semantic" search silently ran keyword-only. The worker did not pin
> ONNX Runtime's `wasmPaths`, so the "indexing and embedding are 100% local" claim did not hold
> in the code. `[Source N]` citations could open a different item than the one Claude cited. The
> entries below are as written at release time; read the hybrid-retrieval and privacy entries
> with that in mind.

### Added
- Public-facing documentation: README, contributing guide, code of conduct, security policy, issue/PR templates, and a CI workflow (all in the plugin's own `.github/` subfolder, where GitHub does not use them; removed later).
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
- Hardened HTML escaping in the chat window: quotes are now escaped, and model-generated follow-up suggestions no longer flow into inline event handlers (prevents attribute injection from paper titles or model output).

---

> Note: versions prior to 2.2.0 predate this public release and are not documented here. The architecture changed substantially (external Python server and separate vector store were removed), so older private notes do not apply to this codebase.

No release tags exist for these versions. 2.2.0 was the first public version; 2.3.0 and 2.4.0
reach the public repository (<https://github.com/chojay/side-quests>) together.
