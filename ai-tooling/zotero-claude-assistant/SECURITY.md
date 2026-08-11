# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 2.2.x   | Yes       |
| < 2.2   | No        |

Security fixes are applied to the latest released version.

## Reporting a vulnerability

Please report security issues **privately**. Do not open a public issue for an unfixed vulnerability.

- Use GitHub's [private vulnerability reporting](https://github.com/chojay/zotero-claude-assistant/security/advisories/new) for this repository, or
- Open a regular issue that contains **no sensitive details** asking a maintainer to establish a private channel.

Please include:

- The plugin version and your Zotero version and operating system
- A description of the issue and its impact
- Steps to reproduce or a proof of concept, if available

We aim to acknowledge reports within a few days and to provide a remediation timeline after triage. Please give us a reasonable opportunity to release a fix before any public disclosure.

## Handling of secrets and data

This plugin is designed to keep your data local by default. A few specifics worth knowing when assessing or reporting issues:

- **API key.** Your Claude API key is stored in Zotero's preference store on your machine. It is never committed to this repository and is not transmitted anywhere except to Anthropic's API as the authorization header for your own requests.
- **Library content.** Indexing and embedding run entirely on-device. Paper text is sent to Anthropic only at query time, and only the passages selected as context for the question you asked.
- **Local databases.** Conversation history and the embedding index are stored in local SQLite files. These (`*.sqlite`) are git-ignored and should never be committed.
- **Local HTTP endpoint.** The plugin registers `POST /claude-assistant/embed` on Zotero's built-in local server (localhost only) so other tools on the same machine can request embeddings. It exposes no library content or key material, and it is unregistered when the plugin is disabled.
- **No telemetry.** The plugin does not collect or transmit usage analytics.

## Good practices for users

- Treat your API key like a password. Rotate it in the [Anthropic Console](https://console.anthropic.com/) if you suspect exposure.
- Never paste your API key, or logs that contain it, into public issues or pull requests.
- Install the plugin only from official [releases](https://github.com/chojay/zotero-claude-assistant/releases) or your own build from source.
