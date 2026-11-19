#!/usr/bin/env python3
"""Fake Gmail CLI for the make_draft.py tests. No network, no real account.

It answers the four draft-only methods from a state folder and logs every
call, so a test can assert exactly which calls were made.

Environment:
  FAKE_GMAIL_STATE   folder with messages.json; calls.jsonl and drafts.json are written there
  FAKE_GMAIL_MUTATE  optional: "nolabel", "quote", "thread" or "emdash" makes the
                     stored draft come back wrong, to test the read-back check
  FAKE_GMAIL_ERROR   optional: an error message every call returns
"""
import base64
import email
import json
import os
import sys

STATE = os.environ["FAKE_GMAIL_STATE"]


def opt(argv, name):
    if name in argv:
        return argv[argv.index(name) + 1]
    return None


def load(name, default):
    p = os.path.join(STATE, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(name, data):
    with open(os.path.join(STATE, name), "w", encoding="utf-8") as f:
        json.dump(data, f)


def to_payload(part):
    """Turn a parsed email part into the Gmail API payload shape."""
    p = {"mimeType": part.get_content_type(), "filename": part.get_filename() or "", "body": {}}
    if part.is_multipart():
        p["parts"] = [to_payload(c) for c in part.get_payload()]
    else:
        data = part.get_payload(decode=True) or b""
        p["body"] = {"data": base64.urlsafe_b64encode(data).decode(), "size": len(data)}
    return p


def html_inject(payload, text):
    if payload.get("mimeType") == "text/html":
        old = base64.urlsafe_b64decode(payload["body"]["data"]).decode()
        payload["body"]["data"] = base64.urlsafe_b64encode((old + text).encode()).decode()
    for c in payload.get("parts", []):
        html_inject(c, text)


def store_draft(argv, draft_id):
    body = json.loads(opt(argv, "--json"))["message"]
    upload = opt(argv, "--upload")
    if upload:
        with open(upload, "rb") as f:
            raw = f.read()
    else:
        raw = base64.urlsafe_b64decode(body["raw"])
    parsed = email.message_from_bytes(raw)
    payload = to_payload(parsed)
    payload["headers"] = [{"name": k, "value": v} for k, v in parsed.items()]
    thread = body.get("threadId") or "thread-new-%s" % draft_id
    labels = ["DRAFT"]
    mutate = os.environ.get("FAKE_GMAIL_MUTATE", "")
    if mutate == "nolabel":
        labels = []
    elif mutate == "thread":
        thread = "thread-other"
    elif mutate == "quote":
        html_inject(payload, '<div class="gmail_quote"><blockquote>old</blockquote></div>')
    elif mutate == "emdash":
        html_inject(payload, "a \u2014 b")
    draft = {"id": draft_id, "message": {"id": "m-" + draft_id, "threadId": thread,
                                         "labelIds": labels, "payload": payload}}
    drafts = load("drafts.json", {})
    drafts[draft_id] = draft
    save("drafts.json", drafts)
    return {"id": draft_id, "message": {"id": "m-" + draft_id, "threadId": thread}}


def main():
    argv = sys.argv[1:]
    with open(os.path.join(STATE, "calls.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(argv) + "\n")
    print("Using fake keyring backend")  # status line before the JSON, as some CLIs print
    if os.environ.get("FAKE_GMAIL_ERROR"):
        print(json.dumps({"error": {"message": os.environ["FAKE_GMAIL_ERROR"]}}))
        return 1
    method = tuple(argv[:4])
    params = json.loads(opt(argv, "--params") or "{}")
    if method == ("gmail", "users", "messages", "get"):
        msgs = load("messages.json", {})
        if params.get("id") not in msgs:
            print(json.dumps({"error": {"message": "Requested entity was not found."}}))
            return 1
        print(json.dumps(msgs[params["id"]]))
    elif method == ("gmail", "users", "drafts", "create"):
        n = len(load("drafts.json", {})) + 1
        print(json.dumps(store_draft(argv, "draft-%03d" % n)))
    elif method == ("gmail", "users", "drafts", "update"):
        print(json.dumps(store_draft(argv, params["id"])))
    elif method == ("gmail", "users", "drafts", "get"):
        drafts = load("drafts.json", {})
        print(json.dumps(drafts[params["id"]]))
    else:
        print(json.dumps({"error": {"message": "fake CLI: method not supported: %s" % " ".join(argv[:4])}}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
