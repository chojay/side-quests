# Contributing to Claude Research Assistant

Thanks for your interest in improving this Zotero plugin. This guide covers how to set up a development build, the conventions we follow, and how to propose changes.

By participating you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- Report bugs and request features through [GitHub Issues](https://github.com/chojay/zotero-claude-assistant/issues).
- Improve documentation (README, this guide, in-code comments).
- Submit code via pull requests.

For anything large or architectural, please open an issue to discuss it before writing code, so we can agree on direction first.

## Development setup

### Prerequisites

- Node.js 18 or later
- A [Zotero 7](https://www.zotero.org/) installation for testing
- A Claude API key from the [Anthropic Console](https://console.anthropic.com/) (only needed to exercise the chat features)

### Build steps

```bash
# Clone your fork
git clone https://github.com/<your-username>/zotero-claude-assistant.git
cd zotero-claude-assistant

# Install dependencies
npm install

# Fetch the embedding model weights (~32 MB ONNX, not committed)
./scripts/fetch-model.sh

# Compile and assemble
npm run build

# Package an installable .xpi
npm run package
```

`npm run watch` recompiles TypeScript as you edit.

> **Why the separate model fetch?** The model config and tokenizer JSON are committed so the architecture is visible, but the quantized ONNX weight is git-ignored to keep the repo small. Without running `fetch-model.sh`, keyword (BM25) search still works, but semantic and hybrid search will not. Run it once before testing retrieval.

### Loading the plugin in Zotero for testing

1. Build a `.xpi` with `npm run package`.
2. In Zotero, go to **Tools → Add-ons → gear icon → Install Plugin From File...** and pick the `.xpi`.
3. Restart Zotero. For faster iteration you can use a separate Zotero [development profile](https://www.zotero.org/support/dev/client_coding/plugin_development) so you do not risk your real library.

## Project layout

A short map (see the README for the full tree):

- `src/addon.ts` - main addon class; `smartChat` is the routing entry point.
- `src/modules/claude-api.ts` - Anthropic client and `detectResearchIntent`.
- `src/modules/local-rag.ts` - BM25 indexing and search over Zotero's SQLite.
- `src/modules/embedding-service.ts` / `embedding-store.ts` - semantic embeddings.
- `src/modules/conversation-store.ts` - chat history persistence.
- `addon/` - manifest, UI (XHTML/JS), worker, icons, model files.
- `scripts/` - build, package, and model-fetch scripts.

## Coding conventions

- **Language:** TypeScript in `src/`, compiled with `tsc`.
- **Formatting:** run `npm run format` (Prettier) before committing.
- **Linting:** run `npm run lint` (ESLint) and resolve warnings you introduce.
- Keep new code consistent with the style of the file you are editing: naming, comment density, and structure.
- Zotero globals (`Zotero`, `Components`, `IOUtils`, `PathUtils`) are declared with `declare const`; follow the existing pattern rather than importing shims.
- Do not commit secrets, API keys, `*.sqlite` runtime databases, or the ONNX model weight. The `.gitignore` already covers these.

## Commit and pull request process

1. Create a topic branch off `main`: `git checkout -b feature/short-description`.
2. Make focused commits with clear messages (imperative mood, e.g. "Add hybrid score weighting option").
3. Run `npm run build`, `npm run lint`, and `npm run format` and confirm the plugin still loads in Zotero.
4. Update `CHANGELOG.md` under `[Unreleased]` describing your change.
5. Open a pull request against `main` using the PR template. Link any related issue and describe how you tested.

Keep pull requests as small as is reasonable. Large, unrelated changes bundled together are harder to review and slower to merge.

## Reporting bugs

Use the bug report template and include:

- Zotero version and operating system
- Plugin version (see `manifest.json` / Add-ons list)
- Steps to reproduce, expected vs actual behavior
- Any relevant output from Zotero's debug log (**Help → Debug Output Logging**)

Please do not paste your API key into issues or logs.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE) that covers this project.
