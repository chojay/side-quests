# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 2.4.x   | Yes       |
| < 2.4   | No        |

Security fixes are applied to the latest version in this folder. Version 2.2.0 had a false
privacy claim (see below); do not use it.

This plugin lives in the [side-quests](https://github.com/chojay/side-quests) repository.
There is no standalone repository for it.

## Reporting a vulnerability

Please report security issues **privately**. Do not open a public issue for an unfixed vulnerability.

- Use GitHub's private vulnerability reporting for the side-quests repository: open its
  **Security** tab and choose **Report a vulnerability**
  (<https://github.com/chojay/side-quests/security/advisories/new>). If that option is not
  shown, private reporting is not turned on for the repository yet; use the next option.
- Open a regular [issue](https://github.com/chojay/side-quests/issues) that contains **no
  sensitive details** and asks the maintainer to set up a private channel.

Please name the plugin (`ai-tooling/zotero-claude-assistant`) in the report, because the
repository holds other projects too.

Please include:

- The plugin version and your Zotero version and operating system
- A description of the issue and its impact
- Steps to reproduce or a proof of concept, if available

We aim to acknowledge reports within a few days and to provide a remediation timeline after triage. Please give us a reasonable opportunity to release a fix before any public disclosure.

## Handling of secrets and data

This plugin is designed to keep your data local by default. A few specifics worth knowing when assessing or reporting issues:

- **API key.** Your Claude API key is stored in Zotero's preference store on your machine. It is never committed to this repository and is not transmitted anywhere except to Anthropic's API as the authorization header for your own requests.
- **Library content.** Indexing and embedding run on your machine. Paper text is sent to Anthropic only at query time, and only the passages selected as context for the question you asked.
- **This claim was wrong in 2.2.0.** The 2.2.0 worker never pinned ONNX Runtime's `wasmPaths`, so the runtime would have loaded its wasm from a CDN (inferred from the code; the 2.2.0 embedder never loaded, so it was not observed). Since 2.3.0 the worker uses the wasm files bundled in the `.xpi`, turns off remote model downloads, and throws instead of fetching remotely. One gap is open: these settings depend on the worker finding the Transformers.js `env` object in the bundle, and a renamed export would skip them without an error.
- **Network destinations.** At run time the plugin calls only `api.anthropic.com`. Zotero's updater polls the plugin's `updates.json` on GitHub; `scripts/fetch-model.sh` downloads the model weights from Hugging Face at build time.
- **Local databases.** Conversation history and the embedding index are stored in local SQLite files. These (`*.sqlite`) are git-ignored and should never be committed.
- **Local HTTP endpoints.** The plugin registers `POST /claude-assistant/embed` (embeddings for other tools on the same machine) and `GET /claude-assistant/status` (health) on Zotero's built-in local server, which listens on localhost. Neither returns library content or key material, and both are unregistered when the plugin is disabled.
- **No telemetry.** The plugin does not collect or transmit usage analytics.

## Good practices for users

- Treat your API key like a password. Rotate it in the [Anthropic Console](https://console.anthropic.com/) if you suspect exposure.
- Never paste your API key, or logs that contain it, into public issues or pull requests.
- Install only a build you made yourself from this folder's source. No release `.xpi` is published yet.
