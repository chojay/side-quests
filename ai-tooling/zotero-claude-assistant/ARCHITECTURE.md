# Architecture

Structural map of the plugin. See the [section README](../README.md) for the showcase framing and the [plugin README](README.md) for install and usage.

## Query dataflow

```mermaid
flowchart TD
    Q[/"user question in the chat dialog"/] --> ROUTE{intent router <br/>heuristics + selected items}
    ROUTE -->|chat intent| CHAT[direct Claude chat]
    ROUTE -->|research intent| RETRIEVE

    subgraph LOCAL["Retrieval - 100% on-device"]
        RETRIEVE[retrieve from both engines] --> BM25[BM25 index <br/>section-aware weights: title 3.0x, <br/>abstract 2.0x, references skipped, <br/>science-token-preserving stopwords]
        RETRIEVE --> SEM[semantic index <br/>bge-small-en-v1.5 quantized ONNX, <br/>384-dim, Transformers.js <br/>in a ChromeWorker]
        BM25 --> RRF[Reciprocal Rank Fusion <br/>k = 60]
        SEM --> RRF
    end

    RRF --> CTX[winning passages only]
    CTX --> API[Claude API <br/>api.anthropic.com]
    CHAT --> API
    API --> ANS["answer with [Source N] citations <br/>that click through to Zotero items"]

    subgraph STORAGE["Local persistence"]
        VDB[(SQLite: <br/>Float32 BLOB vectors, <br/>model-tagged)]
        JDB[(JSON-serialized <br/>BM25 index)]
    end
    SEM -.reads/writes.-> VDB
    BM25 -.reads/writes.-> JDB
```

## Plugin lifecycle

```mermaid
flowchart LR
    B[bootstrap.js <br/>registers chrome content] --> IIFE[esbuild IIFE bundle <br/>becomes Zotero.ClaudeAssistant]
    IIFE --> EP[localhost-only <br/>POST /claude-assistant/embed <br/>for other local tools]
    IIFE --> UI[chat dialog + preferences]
    SD[disable / upgrade] --> CLEAN[close both stores, save index, <br/>unregister endpoint, remove DOM, <br/>drop the global]
```

## Design decisions worth naming

- **Two engines, one fusion.** BM25 catches exact-term science queries (element symbols, units); the embedding index catches paraphrase. RRF merges them without score calibration, and if the ONNX model is unavailable everything degrades to BM25-only instead of failing.
- **Model-tagged vectors.** The embedding store records which model produced its vectors and wipes them if the configured model changes; a stale 384-dim vector can never be compared against a different model's space.
- **ESM in a ChromeWorker, by force.** `importScripts()` cannot load the ESM Transformers.js bundle, so the worker fetches the bundle text, strips the export block, rewrites `import.meta.url`, and indirect-evals it into scope. Documented ugliness beats undocumented magic.
- **Network surface is one hostname.** Paper text leaves the machine only as the retrieved snippets attached to a query, only to `api.anthropic.com`. Indexing and embedding never touch the network (weights are fetched at build time; Zotero's updater polls the update manifest).
- **Privacy claims are code-checked.** The section README's guarantees were audited against the source before publishing; the one latent contradiction found (a dead API-side `generateEmbedding` method with no call sites) is disclosed there and slated for deletion.
