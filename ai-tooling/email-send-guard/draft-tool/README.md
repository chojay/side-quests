# draft-tool: the path an agent takes when the send guard says no

The send guard in the parent folder blocks an agent's email sends. A block
alone leaves the agent with nothing useful to do, and an agent with nothing
useful to do tends to look for another way out. This tool is the useful thing:
it writes the message as a Gmail **draft**, reads the draft back to check it,
and stops. A human reads the draft and presses Send.

`make_draft.py` has no send path. There is no `--send` option, the wrapper
around the Gmail CLI refuses every method that is not on a four-entry
allowlist, and the CLI command itself may not carry a method word (so
`--cli "gws gmail users drafts send"` is refused before anything runs):

| Allowed call | Used for |
|---|---|
| `gmail users messages get` | read the headers of the email being answered |
| `gmail users drafts create` | save a new draft |
| `gmail users drafts update` | replace a draft in place (`--draft-id`) |
| `gmail users drafts get` | read the draft back for the checks |

## Why a separate tool

Two draft paths the author tried first made drafts that looked wrong in the
Gmail compose window:

- A reply draft saved as HTML only, with the whole earlier thread appended as
  nested `gmail_quote` blockquotes, opened as blocks of white space.
- A single-part `text/html` draft could open with an empty body.

So the tool builds the message the way that worked:

- `multipart/alternative` with a `text/plain` part and a `text/html` part;
  `multipart/mixed` around it when there are attachments.
- No quoted thread. For a reply it sets `In-Reply-To` and `References` and
  saves the draft with the original `threadId`, so Gmail still shows the
  earlier messages in the thread view.
- Body as plain text: paragraphs split on blank lines become `<p>`, a
  paragraph whose lines all start with `- ` becomes a `<ul>`. One line per
  paragraph; the mail client wraps it.
- Attachments go up as one `message/rfc822` file (`--upload`), not as base64
  inside a JSON argument, which can pass the OS argument length limit.

After saving, it fetches the draft and checks: `DRAFT` label, same thread,
both text parts present, no `blockquote` or `gmail_quote` in the HTML, no em
dash (a house style rule; `--allow-em-dash` turns it off), every attachment
present. It prints one JSON line and exits 1 if any check fails.

## Usage

```bash
# reply in the thread of message MSG_ID (To defaults to Reply-To, then From)
python3 make_draft.py --reply-to MSG_ID --body-file body.txt --cc someone@example.com

# new email
python3 make_draft.py --to someone@example.com --subject "Weekly notes" --body-file body.txt

# options: --draft-id ID (update in place), --attach FILE (repeatable),
#          --dry-run (print the message and HTML, call nothing; for a reply,
#          To, Subject and threading headers come from the original only in
#          a real run), --cli CMD
```

The Gmail CLI is `gws` (Google Workspace CLI) by default, or whatever
`$MAKE_DRAFT_CLI` or `--cli` names: one executable, optionally after its
interpreter (`python3 my_cli.py`). A value with a Gmail method word (`gmail`,
`users`, `messages`, `drafts`, `threads`), a word that starts with `+`, or
`send`, `reply` or `forward` in a word is refused. The tool passes the Gmail REST method path
as the first four words, then `--params JSON` and `--json JSON`, which is the
`gws` argument shape. Another CLI needs a thin wrapper with that shape.

Python 3.9 or newer, standard library only.

## Tests

```bash
python3 -m unittest discover -s tests     # or: pytest tests
```

21 tests, no network and no real account. `tests/fake_gmail_cli.py` plays the
Gmail CLI: it answers the four allowed methods from `tests/fixtures/`, stores
each draft as a Gmail API payload, logs every call, and can be told to return
a wrong draft (no `DRAFT` label, another thread, a quoted block, an em dash)
so the read-back check is tested too. All addresses are `example.com`.

- 7 MIME build tests (parts, no quoted thread, threading headers, no
  duplicate `References`, HTML paragraphs and lists, attachments).
- 10 end-to-end tests through the fake CLI: the exact call sequence for a
  reply, a new email, an update and a dry run (zero calls), attachments sent
  as an uploaded file with the temp file removed, the four read-back failures,
  the em dash refusal, a login error hint and a missing message.
- 4 no-send tests: send, `+send`, `+reply` and delete methods are refused
  before any process starts; a `--cli` or `$MAKE_DRAFT_CLI` value that holds a
  method word is refused the same way; `--send` and argparse prefixes such as
  `--sen` are rejected; the allowlist holds only get, create and update.

Passed on Python 3.9.6 and 3.11.16 (unittest), and under pytest on 3.11.

## Limits

- This public port was tested only against the fake CLI. The argument shape
  matches the private tool it was ported from, but a `gws` release that
  changes its flags would break it, and only a live run would show that.
- The tool does not stop an agent from calling the Gmail CLI directly. That
  is the guard's job; this tool only gives the agent a safe thing to do
  instead.
- The read-back trusts what the API returns. It checks structure, not
  wording: a draft with the wrong recipient passes if it is well formed.

## AI-assisted build notes

Claude Code wrote this port from the author's private draft tool and wrote
the tests and fixtures from scratch with invented data. The port uses an
allowlist of four methods instead of a denylist on the word `send`, which
would not catch the CLI's `+send` or `+reply` helpers, and a test that tries
the helpers. An audit then found that the allowlist checked only the method
words the tool builds, while a multi-word `--cli` value is placed in front of
them; the CLI value is now checked too. The
parser also sets `allow_abbrev=False`, so no prefix of a future option can be
matched by accident.
