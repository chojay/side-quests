#!/usr/bin/env python3
"""Claude Code PreToolUse hook for Bash: point memory-heavy commands at the `heavy` queue.

This is a nudge, not enforcement. It denies a Bash command that looks like it
starts a memory-heavy job (model inference, --device mps|cuda, background Blender
renders, *train/infer/embed*.py scripts; patterns in the config "hook" section)
unless the command runs through a wrapper named in hook.wrappers (default: heavy).
The deny message shows current memory and running jobs, so the agent can queue the
job or plan around it. The real limits live in heavy.py (admission and the cap).

Only real commands count: the first word of each command segment, plus the code of
`python -c`, `bash -c` and heredocs. Read-only first words (grep, ps, cat, ...)
and quoted arguments do not count. Escape for a light job: put the light marker
(default MEMGUARD_LIGHT=1) anywhere in the command. The agent can set that marker
itself, which is why this is a nudge.

Known gaps (by design or not yet handled):
  * command substitution `$(...)` and backticks are scanned as plain text, so a
    queued command inside them may still be denied;
  * a heavy job started by a script whose name and contents the hook never sees
    (./run.sh) passes;
  * any error inside the hook lets the command through (it never blocks by accident).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def split_heredocs(cmd):
    """Return [(line, heredoc_body)]; heredoc bodies stay with the line that opened them."""
    lines = cmd.replace("\\\n", " ").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        i += 1
        body = []
        for _q, tag in HEREDOC.findall(line):
            while i < len(lines) and lines[i].strip() != tag:
                body.append(lines[i])
                i += 1
            i += 1
        out.append((line, "\n".join(body)))
    return out


def segments(line):
    """Split on ; & | outside quotes. Returns [(text_with_quotes, text_without_quoted_parts)]."""
    segs, cur, bare, q = [], [], [], None
    j = 0
    while j < len(line):
        ch = line[j]
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            elif ch == "\\" and q == '"' and j + 1 < len(line):
                cur.append(line[j + 1])
                j += 1
        elif ch in "'\"":
            q = ch
            cur.append(ch)
            bare.append(" ")
        elif ch in ";&|":
            segs.append(("".join(cur), "".join(bare)))
            cur, bare = [], []
        else:
            cur.append(ch)
            bare.append(ch)
        j += 1
    segs.append(("".join(cur), "".join(bare)))
    return [(a.strip(), b.strip()) for a, b in segs if a.strip()]


def unquote_words(text):
    """Very small shell word splitter (quotes removed) for finding -c arguments."""
    words, cur, q, j = [], [], None, 0
    while j < len(text):
        ch = text[j]
        if q:
            if ch == q:
                q = None
            elif ch == "\\" and q == '"' and j + 1 < len(text):
                cur.append(text[j + 1])
                j += 1
            else:
                cur.append(ch)
        elif ch in "'\"":
            q = ch
        elif ch.isspace():
            if cur:
                words.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
        j += 1
    if cur:
        words.append("".join(cur))
    return words


def first_word(words, strip_words):
    """Index of the command word: skips assignments, prefix words (time, nohup, env,
    a subshell's '('), the options of a prefix word (time -p) and `cd DIR`."""
    k = 0
    after_prefix = False
    while k < len(words):
        w = words[k].lstrip("({")
        if not w:
            k += 1
            continue
        if ASSIGN.match(w) or w in strip_words:
            after_prefix = w in strip_words
            k += 1
            continue
        if after_prefix and (w.startswith("-") or w.isdigit()):
            k += 1
            continue
        if w == "cd":
            k += 2
            continue
        words[k] = w
        return k
    return None


def heavy_hits(cmd, cfg, depth=0):
    h = cfg["hook"]
    pats = [re.compile(p) for p in h["patterns"]]
    ro = set(h["readonly_first_words"])
    wrappers = set(h.get("wrappers", ["heavy"]))
    strip_words = set(h.get("strip_prefix_words", []))
    hits = []
    for line, body in split_heredocs(cmd):
        for seg, bare in segments(line):
            words = unquote_words(seg)
            k = first_word(words, strip_words)
            if k is None:
                continue
            exe = os.path.basename(words[k])
            if exe in wrappers or exe in ro:
                continue
            text = bare
            if "<<" in seg and body:
                text += "\n" + body
            if "-c" in words[k + 1:]:
                ci = words.index("-c", k + 1)
                arg = words[ci + 1] if ci + 1 < len(words) else ""
                if exe in ("bash", "sh", "zsh") and depth < 3:
                    hits.extend(heavy_hits(arg, cfg, depth + 1))
                    continue
                if exe.lower().startswith("python"):
                    text += "\n" + arg
            for p in pats:
                if p.search(text):
                    hits.append((p.pattern, seg[:160]))
                    break
    return hits


def status_text(cfg):
    if os.environ.get("MEMGUARD_NO_STATUS"):
        return ""
    try:
        import memlib as m
        probe = m.Probe()
        s = probe.system()
        rows = probe.processes()
        jobs = sorted([r for r in rows if m.is_job(cfg, r) and r["mem_gb"] >= 1], key=lambda r: -r["mem_gb"])
        cur = None
        try:
            with open(os.path.join(cfg["state_dir"], "current.json")) as f:
                cur = json.load(f)
        except (OSError, ValueError):
            pass
        txt = "Now: " + m.status_line(s) + "."
        if cur:
            txt += " Heavy queue: %s is running." % cur.get("name")
        if jobs:
            txt += " Job processes >= 1 GB: " + "; ".join(
                "pid %d %.1f GB %s" % (r["pid"], r["mem_gb"], m.short(r["cmd"], 60)) for r in jobs[:4]) + "."
        return txt
    except Exception:
        return ""


def decide(data, cfg):
    """None to allow, or the deny reason."""
    if data.get("tool_name") != "Bash":
        return None
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if cfg["hook"]["light_marker"] in cmd:
        return None
    hits = heavy_hits(cmd, cfg)
    if not hits:
        return None
    pat, seg = hits[0]
    return (
        "Memory guard: this looks like a heavy job (pattern %r in: %s). Heavy jobs run one at a time "
        "on this machine. Run it through the queue: heavy --name <job> --need <GB> [--cap <GB>] -- <command> "
        "(run long jobs in the background and poll; heavy --history <job> shows past peak GB; "
        "heavy --status shows the queue). Split big batches into chunks. If it is really light "
        "(under 2 GB), put %s at the start of the command. %s" % (
            pat, seg, cfg["hook"]["light_marker"], status_text(cfg))).strip()


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    try:
        import memlib as m
        reason = decide(data, m.load_config())
    except Exception:
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
