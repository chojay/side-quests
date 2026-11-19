#!/usr/bin/env python3
"""Save a clean Gmail DRAFT through a Gmail CLI. This tool has no send path.

It is the path an agent takes when the send guard blocks a send: write the
message as a draft, read it back, and leave the final read and the send to
the human.

What it builds: a multipart/alternative message (text/plain + text/html), with
no quoted earlier thread. For a reply it sets In-Reply-To and References and
saves the draft in the original thread, so the mail client still shows the
earlier messages in the thread view. With attachments the message becomes
multipart/mixed around the alternative part.

After it saves the draft it reads the draft back and checks: DRAFT label, same
thread, text/plain and text/html parts, no blockquote or gmail_quote in the
HTML, no em dash, every attachment present. Exit 1 if a check fails.

Usage:
  make_draft.py --reply-to MSG_ID --body-file BODY.txt [--cc a@x,b@y] [--to addr] [--subject S]
  make_draft.py --to addr --subject S --body-file BODY.txt [--cc ...]   (new email, no thread)
                [--draft-id ID]   update that draft in place
                [--attach FILE]   repeatable
                [--dry-run]       print headers and HTML, call nothing
                [--allow-em-dash] skip the em dash checks
                [--cli CMD]       Gmail CLI command (default: $MAKE_DRAFT_CLI or "gws")

Body file: plain text, paragraphs separated by a blank line. A paragraph whose
lines all start with "- " becomes a bullet list. Write each paragraph on one
line and let the mail client wrap it.

The CLI is called with the Gmail REST method path as its first four words
(for example "gmail users drafts create --params JSON --json JSON"), which is
the shape of the Google Workspace CLI (gws). Only four methods are on the
allowlist: messages get, drafts create, drafts update, drafts get.

Python 3.9 or newer, standard library only.
"""
import argparse
import base64
import html
import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import getaddresses

EM_DASH = "\u2014"

# The only Gmail API methods this tool may call. There is no send method here,
# and nothing in this file builds one.
ALLOWED_CALLS = {
    ("gmail", "users", "messages", "get"),
    ("gmail", "users", "drafts", "create"),
    ("gmail", "users", "drafts", "update"),
    ("gmail", "users", "drafts", "get"),
}


# Words that may not appear in the --cli / $MAKE_DRAFT_CLI value. The method path comes
# only from ALLOWED_CALLS, so a CLI value such as "gws gmail users drafts send" cannot put
# a send in front of an allowed call.
CLI_METHOD_WORDS = {"gmail", "users", "messages", "drafts", "threads"}
CLI_SEND_RE = re.compile(r"send|reply|forward", re.I)


def cli_command(cli=None):
    """Return the Gmail CLI as an argv list (from --cli, $MAKE_DRAFT_CLI or "gws"): the
    executable, optionally after its interpreter, with no Gmail method words."""
    spec = cli or os.environ.get("MAKE_DRAFT_CLI") or "gws"
    argv = shlex.split(spec)
    for w in argv:
        b = os.path.basename(w)
        if b.lower() in CLI_METHOD_WORDS or b.startswith("+") or CLI_SEND_RE.search(b):
            raise SystemExit("refusing: the Gmail CLI command %r holds a method word; this tool "
                             "never sends and takes only the executable (and its interpreter)" % spec)
    if len(argv) == 1 and os.sep not in argv[0]:
        found = shutil.which(argv[0])
        if found:
            argv = [found]
    return argv


def cli_json(args, cli=None, timeout=60):
    """Run one allowlisted Gmail CLI call and return its JSON answer."""
    if tuple(args[:4]) not in ALLOWED_CALLS:
        raise SystemExit("refusing: %r is not a draft-only call; this tool never sends" % " ".join(args[:4]))
    r = subprocess.run(cli_command(cli) + list(args), capture_output=True, text=True, timeout=timeout)
    out = r.stdout
    i = out.find("{")  # some CLIs print a status line before the JSON
    if i < 0:
        raise SystemExit("%s failed: %s" % (" ".join(args[:4]), (r.stderr or out).strip()[-300:]))
    d = json.loads(out[i:])
    if isinstance(d, dict) and d.get("error"):
        err = d["error"]
        msg = str(err.get("message", err)) if isinstance(err, dict) else str(err)
        hint = ""
        if "invalid_grant" in msg or "uthentication" in msg:
            hint = " (the CLI login may have expired: run its auth login)"
        raise SystemExit("%s: %s%s" % (" ".join(args[:4]), msg[:300], hint))
    return d


def para_html(p):
    lines = p.split("\n")
    if all(line.startswith("- ") for line in lines):
        return "<ul>" + "".join("<li>%s</li>" % html.escape(line[2:]) for line in lines) + "</ul>"
    return "<p>" + "<br>".join(html.escape(line) for line in lines) + "</p>"


def body_html(text):
    paras = [p.strip("\n") for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return "<div>" + "".join(para_html(p) for p in paras) + "</div>"


def attachment_part(path):
    ctype, _ = mimetypes.guess_type(path)
    maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
    with open(path, "rb") as f:
        data = f.read()
    if maintype == "application":
        part = MIMEApplication(data, _subtype=subtype)
    else:
        part = MIMEBase(maintype, subtype)
        part.set_payload(data)
        encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=os.path.basename(path))
    return part


def build_message(to, cc, subject, in_reply_to, references, text, attachments=None):
    """multipart/alternative with no quoted thread; multipart/mixed around it with attachments."""
    text = text.strip() + "\n"
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(text, "plain", "utf-8"))
    alt.attach(MIMEText(body_html(text), "html", "utf-8"))
    if attachments:
        msg = MIMEMultipart("mixed")
        msg.attach(alt)
        for a in attachments:
            msg.attach(attachment_part(a))
    else:
        msg = alt
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        if in_reply_to in references.split():
            msg["References"] = references
        else:
            msg["References"] = (references + " " + in_reply_to).strip()
    return msg


def reply_headers(msg_id, cli=None):
    d = cli_json(["gmail", "users", "messages", "get", "--params", json.dumps(
        {"userId": "me", "id": msg_id, "format": "metadata",
         "metadataHeaders": ["From", "Reply-To", "Subject", "Message-ID", "References"]})], cli)
    h = {x["name"].lower(): x["value"] for x in d.get("payload", {}).get("headers", [])}
    sender = getaddresses([h.get("reply-to") or h.get("from", "")])
    subj = h.get("subject", "")
    if not re.match(r"(?i)re:", subj):
        subj = "Re: " + subj
    return {"thread": d.get("threadId"), "to": sender[0][1] if sender else "", "subject": subj,
            "message_id": h.get("message-id", ""), "references": h.get("references", "")}


def check_draft(draft_id, thread, attachments=None, cli=None, allow_em_dash=False):
    d = cli_json(["gmail", "users", "drafts", "get", "--params",
                  json.dumps({"userId": "me", "id": draft_id, "format": "full"})], cli)
    m = d.get("message", {})
    problems, types, htmls, names = [], [], [], []

    def walk(p):
        types.append(p.get("mimeType"))
        if p.get("filename"):
            names.append(p["filename"])
        if p.get("mimeType") == "text/html" and p.get("body", {}).get("data"):
            htmls.append(base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8", "replace"))
        for c in p.get("parts", []) or []:
            walk(c)

    walk(m.get("payload", {}))
    if "DRAFT" not in (m.get("labelIds") or []):
        problems.append("not labeled DRAFT")
    if thread and m.get("threadId") != thread:
        problems.append("thread %s, expected %s" % (m.get("threadId"), thread))
    if "text/plain" not in types or "text/html" not in types:
        problems.append("parts %s (need text/plain and text/html)" % types)
    if any(re.search(r"blockquote|gmail_quote", x, re.I) for x in htmls):
        problems.append("quoted thread (blockquote) in the HTML")
    if not allow_em_dash and any(EM_DASH in x for x in htmls):
        problems.append("em dash in the body")
    for a in attachments or []:
        if os.path.basename(a) not in names:
            problems.append("attachment %s missing" % os.path.basename(a))
    return {"draft_id": draft_id, "message_id": m.get("id"), "thread": m.get("threadId"),
            "parts": types, "attachments": names, "ok": not problems, "problems": problems}


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], allow_abbrev=False)
    ap.add_argument("--reply-to", help="message id of the email being answered (omit for a new email)")
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--to", help="default: Reply-To or From of that email")
    ap.add_argument("--cc", default="", help="comma-separated")
    ap.add_argument("--subject")
    ap.add_argument("--draft-id", help="update this draft instead of creating one")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--attach", action="append", default=[], help="file to attach (repeatable)")
    ap.add_argument("--allow-em-dash", action="store_true")
    ap.add_argument("--cli", help='Gmail CLI command, default $MAKE_DRAFT_CLI or "gws"')
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    for f in a.attach:
        if not os.path.isfile(f):
            raise SystemExit("attachment not found: %s" % f)
    with open(a.body_file, encoding="utf-8") as f:
        text = f.read()
    if EM_DASH in text and not a.allow_em_dash:
        raise SystemExit("body has an em dash (pass --allow-em-dash to keep it)")
    if a.reply_to:
        if a.dry_run:
            r = {"thread": None, "to": a.to or "", "subject": a.subject or "Re: (from message %s)" % a.reply_to,
                 "message_id": "", "references": ""}
        else:
            r = reply_headers(a.reply_to, a.cli)
    elif a.to and a.subject:
        r = {"thread": None, "to": a.to, "subject": a.subject, "message_id": "", "references": ""}
    else:
        raise SystemExit("need --reply-to, or --to and --subject for a new email")
    to = a.to or r["to"]
    msg = build_message(to, a.cc, a.subject or r["subject"], r["message_id"], r["references"], text, a.attach)
    if a.dry_run:
        print(json.dumps({"to": to, "cc": a.cc, "subject": msg["Subject"], "thread": r["thread"],
                          "in_reply_to": msg["In-Reply-To"], "references": msg["References"],
                          "attachments": [os.path.basename(x) for x in a.attach],
                          "size_bytes": len(msg.as_bytes())}, ensure_ascii=False, indent=1))
        print(body_html(text))
        return 0
    m = {}
    if r["thread"]:
        m["threadId"] = r["thread"]
    tmp = None
    if a.attach:
        # Upload the RFC 822 message as media: a base64 PDF inside --json can pass
        # the OS argument length limit.
        tmp = tempfile.NamedTemporaryFile(suffix=".eml", delete=False)
        tmp.write(msg.as_bytes())
        tmp.close()
        extra = ["--json", json.dumps({"message": m}), "--upload", tmp.name,
                 "--upload-content-type", "message/rfc822"]
    else:
        m["raw"] = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        extra = ["--json", json.dumps({"message": m})]
    try:
        if a.draft_id:
            d = cli_json(["gmail", "users", "drafts", "update", "--params",
                          json.dumps({"userId": "me", "id": a.draft_id})] + extra, a.cli, timeout=180)
        else:
            d = cli_json(["gmail", "users", "drafts", "create", "--params",
                          json.dumps({"userId": "me"})] + extra, a.cli, timeout=180)
    finally:
        if tmp:
            os.unlink(tmp.name)
    res = check_draft(d.get("id"), r["thread"], a.attach, a.cli, a.allow_em_dash)
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
