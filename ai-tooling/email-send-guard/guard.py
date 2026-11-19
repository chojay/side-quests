#!/usr/bin/env python3
"""email-send-guard: a Claude Code PreToolUse hook that keeps an agent from sending email.

The agent may write drafts. A person reads them and sends them. This hook is a tripwire for
the common ways a coding agent sends mail from a shell; it is not a sandbox (see README.md,
"What it cannot see").

Hook protocol: Claude Code writes the tool call as JSON on stdin. Exit 0 lets the call run.
Exit 2 blocks it, and Claude Code shows the stderr text to the agent.

Before any check, a small scanner reads the command the way the shell would for quoting:
comments are dropped, heredoc bodies are cut out, $'...' strings are decoded, arithmetic
($(( )), $[ ], (( ))) is copied whole, $( ) and backtick spans outside single quotes are
collected, and brace lists such as {a,b} are expanded. Then shlex splits the rest into shell
segments (on newlines, ; && || | & and parentheses; words on space and tab only, as bash
does), and each segment is checked on its argv (redirections removed). The scanner follows
bash, plus a few zsh forms (=cmd, noglob, repeat, ${(e)x}, (e:...:) qualifiers).

What it blocks, per segment:
  - a Gmail CLI's send helpers (gmail +send, +reply, +reply-all, +forward), unless that
    segment's own argv has --draft, --dry-run, --help or -h as a real flag;
  - the Gmail CLI's raw API sends (gmail users messages send, gmail users drafts send);
  - raw mail commands (sendmail, mail, mailx, msmtp, swaks, mutt and similar), also behind
    wrappers and runners, git send-email, aws ses send-*, python -m smtplib, curl to an
    smtp:// URL or a known mail API, and interpreter code (inline, heredoc, here-string or
    piped) that uses an SMTP library, a mail API or one of the commands above;
  - shell code handed to a shell (sh -c, eval, a heredoc, a here-string, text piped or fed
    by process substitution into a shell, ssh with no remote command, at, trap, alias,
    git -c values, $( ) and backticks), checked again as a command; a heredoc whose reader
    cannot be named is checked as commands;
  - a configured SMTP helper script's send flag, unless one rule of the send policy matches
    exactly: one recipient, a cc from an allowlist, a subject keyword, no repeated option,
    no unknown or ambiguous option (argparse-style prefixes are resolved first);
  - a configured report sender's send subcommands, unless a dry-run flag is present;
  - any non-Bash tool that the settings route to this hook (a mail connector's send,
    reply and forward tools).

There is no unlock file. To turn the guard off, the owner removes the hook from the settings.
Rules in a policy file count only when that file (and its folder) is owned by root and not
writable by group or others, unless the hook command passes --allow-user-policy. A policy
file the agent can edit would be an unlock.

Fail closed: when the input cannot be parsed (bad JSON, unbalanced quotes), or is past the
work limits (MAX_INPUT, MAX_SEGMENTS, MAX_CALLS), and it holds a send-capable token, the call
is blocked. Without such a token the hook stays out of the way.

Standard library only. Python 3.9 or later.

Usage
  guard.py [--policy FILE] [--allow-user-policy]            hook mode, JSON on stdin
  guard.py [--policy FILE] [--allow-user-policy] --check CMD  print the verdict for CMD
"""
import fnmatch
import json
import os
import re
import shlex
import stat
import sys
from urllib.parse import unquote

BLOCK = 2
MAX_DEPTH = 6

# Set by a private build to carry the policy inside the hook file itself (then no policy
# file is read). None in the public file.
EMBEDDED_POLICY = None

DEFAULT_MESSAGE = ("This command can send email, and agents in this setup do not send email. "
                   "Save a draft instead and tell the owner it is waiting in Drafts.")

GMAIL_HELPERS = {"+send", "+reply", "+reply-all", "+forward"}
GMAIL_SAFE = {"--draft", "--dry-run", "--help", "-h"}
GMAIL_HELP = {"--help", "-h"}
# Gmail CLI flags known to take no value. A safe flag right after any other option is
# read as that option's value (fail closed), so '--body --draft' does not count as a draft.
GMAIL_BOOL = {"--html", "--draft", "--dry-run", "--help", "-h"}

RAW_SENDERS = {"sendmail", "mail", "mailx", "msmtp", "msmtpq", "msmtp-queue", "swaks", "mutt",
               "neomutt", "s-nail", "ssmtp", "sendemail", "exim", "exim4", "nail", "mpack",
               "mailsend", "mailsend-go", "blat", "sendmail.postfix", "bsd-mailx",
               "heirloom-mailx", "mail.mailutils"}
# Version and help queries of a raw sender that read nothing and send nothing.
RAW_INFO = {"-h", "--help", "-V", "--version"}
RAW_INFO_BY_CMD = {"mutt": {"-v"}, "neomutt": {"-v"}, "sendmail": {"-bp"}}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "mksh", "fish", "ash", "yash"}
SHELL_VALUED = {"-o", "+o", "-O", "+O", "--rcfile", "--init-file"}
SOURCE_CMDS = {"source", "."}
# Commands that read shell code from their input and run it later.
AT_CMDS = {"at", "batch"}
INTERP_RE = re.compile(r"^(python[0-9.]*|pypy[0-9.]*|ipython[0-9.]*|ruby|perl[0-9.]*|node|nodejs|"
                       r"deno|bun|php[0-9.]*|osascript|awk|gawk|mawk|nawk)$")
AWKS = {"awk", "gawk", "mawk", "nawk"}
PY_PREFIXES = ("python", "pypy", "ipython")
# Python modules that send mail when run with -m (smtplib's __main__ reads a message from
# stdin and sends it).
PY_SEND_MODULES = {"smtplib", "aiosmtplib", "yagmail", "redmail", "smtpd"}
# Words that only print or search text: a 'gmail +send' pair or a helper name in their
# arguments is not a command. (git is text-only for its message arguments; its own send
# paths, 'git send-email' and '-c' values that run code, are checked in check_command.)
TEXT_ONLY = {"echo", "printf", "grep", "egrep", "fgrep", "rg", "ag", "ack", "git", "man",
             "which", "type", "whereis", "apropos", "whatis", "tldr", "help", "less", "more",
             "head", "tail", "wc", "cat", "ls"}
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "{", "}", "coproc"}
# Words that end a compound command; a heredoc after them feeds the whole compound.
CLOSERS = {"}", "done", "fi", "esac", ")", "))"}
# Wrapper commands and the options of theirs that take a value (short and long forms).
WRAPPERS = {
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-U", "-r", "-t", "-T", "-R", "--user",
             "--group", "--close-from", "--chdir", "--host", "--prompt", "--other-user",
             "--role", "--type", "--command-timeout", "--chroot"},
    "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-P", "--unset", "--chdir"},
    "nohup": set(), "command": set(), "builtin": set(), "chronic": set(),
    "time": {"-f", "-o", "--format", "--output"},
    "exec": {"-a"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p", "--class", "--classdata"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "gtimeout": {"-s", "-k", "--signal", "--kill-after"},
    "xargs": {"-n", "-I", "-L", "-P", "-s", "-d", "-E", "-a", "-J", "-R", "--max-args",
              "--max-lines", "--max-procs", "--max-chars", "--delimiter", "--eof",
              "--arg-file", "--process-slot-var"},
    "stdbuf": {"-i", "-o", "-e", "--input", "--output", "--error"},
    "caffeinate": {"-t", "-w"},
    "setsid": set(), "unbuffer": set(), "busybox": set(), "toybox": set(), "nocache": set(),
    # zsh precommand modifiers
    "noglob": set(), "nocorrect": set(), "-": set(),
}
# Commands that run another command somewhere in their arguments, in a form that differs
# per tool (uv run, docker exec, flock FILE, find -exec, ...). The guard looks for the
# first word after them that it would check (a mail command, a shell, an interpreter,
# curl, gws, a configured script) and checks from there.
RUNNERS = {"uv", "uvx", "poetry", "pipenv", "conda", "mamba", "micromamba", "pipx", "npx",
           "bunx", "pnpm", "yarn", "npm", "rye", "hatch", "pdm", "arch", "lockf", "flock",
           "script", "heavy", "chrt", "taskset", "firejail", "sandbox-exec", "docker",
           "podman", "kubectl", "parallel", "screen", "tmux", "systemd-run", "launchctl",
           "torsocks", "proxychains", "proxychains4", "op", "doppler", "direnv", "mise",
           "asdf", "devbox", "nix-shell", "xvfb-run", "find", "su", "runuser", "watch",
           "nq", "ts", "dotenv", "foreman", "honcho", "entr", "chroot"}
# Runners that run a command only after one of their own verbs (npm exec, docker run, ...).
# Their other subcommands (npm install sendmail, docker logs mail) run nothing.
RUNNER_VERBS = {
    "uv": {"run", "tool"}, "poetry": {"run"}, "pipenv": {"run"}, "conda": {"run"},
    "mamba": {"run"}, "micromamba": {"run"}, "pipx": {"run"}, "npm": {"exec", "x"},
    "pnpm": {"exec", "dlx", "x"}, "yarn": {"exec", "dlx", "run"}, "rye": {"run"},
    "hatch": {"run"}, "pdm": {"run"}, "docker": {"exec", "run", "container", "compose"},
    "podman": {"exec", "run", "container", "compose"}, "kubectl": {"exec", "run", "debug"},
    "tmux": {"new-session", "new", "new-window", "neww", "split-window", "splitw", "send-keys",
             "send", "respawn-pane", "respawnp", "respawn-window", "respawnw", "run-shell", "run",
             "display-popup", "popup", "pipe-pane", "pipep", "if-shell", "if"},
    "op": {"run"}, "doppler": {"run"}, "direnv": {"exec"}, "mise": {"exec", "x", "run"},
    "asdf": {"exec"}, "devbox": {"run"}, "foreman": {"run"}, "honcho": {"run"},
    "launchctl": {"asuser", "submit", "bsexec"},
}
# Option values of runners that take one (so 'screen -S mail' is a name, not a command).
RUNNER_VALUED = {"screen": {"-S", "-c", "-e", "-h", "-p", "-s", "-t", "-T", "-X", "-l"}}
SSH_VALUED = {"-b", "-c", "-D", "-E", "-e", "-F", "-I", "-i", "-J", "-L", "-l", "-m", "-O",
              "-o", "-p", "-Q", "-R", "-S", "-W", "-w", "-B"}
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^\]=]*\])?\+?=")
# A word that is only a parameter: $NAME, ${NAME}, $0 to $9, $@, $*, ${10}.
VAR_RE = re.compile(r"^\$(\{([A-Za-z_][A-Za-z0-9_]*|[0-9]+|[@*])\}|[A-Za-z_][A-Za-z0-9_]*|[0-9@*])$")
DECLARERS = {"export", "declare", "typeset", "local", "readonly"}
GLOB_CHARS = "*?["
SEQ_RE = re.compile(r"\{[^{},\s]*\.\.[^{},\s]*\}")
# Command names a glob command word (/usr/sbin/sendmai?) is matched against.
GLOB_NAMES = ["python", "python3", "python2", "pypy", "pypy3", "ipython", "ipython3", "ruby",
              "perl", "perl5", "node", "nodejs", "deno", "bun", "php", "osascript", "awk", "gawk",
              "mawk", "nawk", "gws", "curl", "wget", "http", "https", "xh", "git", "ssh", "eval",
              "himalaya", "aws", "trap", "alias", "hash"]
# Same-line options of git that take a value.
GIT_VALUED = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env",
              "--super-prefix", "--list-cmds", "--attr-source"}

# Raw sender names that are also ordinary words; in code they count only in a command
# shape (followed by an option or an address).
_AMBIG_SENDERS = {"mail", "nail", "blat", "exim", "exim4", "mail.mailutils"}


def _alt(names):
    return "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))


# Text in code, heredoc bodies and here-strings that marks a send.
CODE_SEND_RE = re.compile(
    r"smtplib|\bSMTP(_SSL)?\s*\(|nodemailer|Net::SMTP|net/smtp|yagmail|redmail|"
    r"\bsend_(mass_)?mail\s*\(|"
    r"users['\",\s().]+(messages|drafts)['\",\s().]+send\b")
# Raw mail command names in code (os.system, subprocess, awk pipes), built from RAW_SENDERS.
CODE_RAW_RE = re.compile(
    r"(?<![\w.-])(" + _alt(RAW_SENDERS - _AMBIG_SENDERS) + r")(?![\w-])(?!\.(log|conf|cf|mc|txt|md)\b)|"
    r"(?:^|[\s'\"`(\[|;&/,])(" + _alt(_AMBIG_SENDERS) + r")\s+(-|[^\s'\"]*@)", re.I)
# A scriptable mail app (AppleScript 'application "Mail"', 'app "Mail.app"', 'application id
# "com.apple.mail"', JXA 'Application("Mail")'). Its send is checked outside string literals.
CODE_APP_RE = re.compile(
    r"\b(app|application)\b(\s+id)?\s*\(?\s*['\"]([^'\"]*/)?(mail|com\.apple\.mail|microsoft outlook|"
    r"com\.microsoft\.outlook)(\.app)?['\"]", re.I)
# HTTP mail APIs: a URL that sends a message. The Gmail API path is matched on any host
# (gmail.googleapis.com, www.googleapis.com, the upload and batch hosts).
MAIL_API_RE = re.compile(
    r"/gmail/v1/users/[^/\s]+/(messages|drafts)/send|api\.(eu\.)?mailgun\.net/\S*messages|"
    r"api\.(eu\.)?sendgrid\.com/v3/mail/send|api\.postmarkapp\.com/email|"
    r"graph\.microsoft\.com/\S*/sendmail|"
    r"graph\.microsoft\.com/\S*/messages/[^/\s]+/(send|reply|replyall|forward)\b|"
    r"email(-smtp)?\.[a-z0-9-]+\.amazonaws\.com/\S*(action=send|v2/email/outbound)|"
    r"api\.resend\.com/emails|api\.mailjet\.com/v3(\.1)?/send|api\.brevo\.com/v3/smtp/email|"
    r"mandrillapp\.com/api/1\.0/messages/send", re.I)
# A URL into the Gmail API messages or drafts collection whose last part holds a curl glob
# or a percent escape ({send}, [s-s]end, sen%64): fail closed.
GMAIL_URL_GLOB_RE = re.compile(r"/gmail/v1/users/[^/\s]+/(messages|drafts)/[^/\s?#]*[\[{%]", re.I)
SES_HOST_RE = re.compile(r"email(-smtp)?\.[a-z0-9-]+\.amazonaws\.com", re.I)
SES_SEND_RE = re.compile(r"action=send|outbound-(bulk-)?emails", re.I)
PHP_MAIL_RE = re.compile(r"\bmail\s*\(")
CODE_GMAIL_RE = re.compile(r"gmail['\",\s]+\+(send|reply|reply-all|forward)\b")
CURL_SMTP_RE = re.compile(r"smtps?://|mail-rcpt|mail-from", re.I)
# Used only when the input cannot be parsed: any token that could start a send.
SEND_TOKEN_RE = re.compile(
    r"\+(send|reply|reply-all|forward)\b|\b(sendmail|mailx?|msmtpq?|swaks|mutt|neomutt|s-nail|"
    r"ssmtp|sendemail|exim4?)\b|smtplib|smtps?://|--mail-rcpt|users\s+(messages|drafts)\s+send|"
    r"--send\b|\bSMTP|send-email|gmail\s+\S*\$", re.I)
# Work limits. A command past them is not checked in full; it is blocked when it holds a
# send-capable token (the same rule as unparsable input).
MAX_INPUT = 100000
MAX_SEGMENTS = 2000
MAX_CALLS = 4000

SEP_CHARS = set(";|()\n")
PUNCT = set("();<>|&\n")

# Private markers. Input text never holds them (they are removed first).
SUB_MARK = "\x01"
BRACE_SENT = {"{": "\x02", "}": "\x03", ",": "\x04"}
BRACE_BACK = {v: k for k, v in BRACE_SENT.items()}
PLACE_RE = re.compile("\x01S([0-9]+)\x01")
CTRL_RE = re.compile("[\x00-\x04]")


class Verdict(Exception):
    pass


# ----------------------------------------------------------------------------- policy

def _locked(path):
    """True when path and its folder are owned by root and not writable by group or others."""
    real = os.path.realpath(path)
    for p in (real, os.path.dirname(real)):
        try:
            st = os.stat(p)
        except OSError:
            return False
        if st.st_uid != 0 or st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            return False
    return True


def load_policy(path, allow_user_policy):
    """Return (policy dict, note). Rules are dropped when the file is not trusted."""
    if EMBEDDED_POLICY is not None:
        return dict(EMBEDDED_POLICY), ""
    if not path:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.environ.get("EMAIL_SEND_GUARD_POLICY") or os.path.join(here, "send_policy.json")
    if not os.path.exists(path):
        return {}, ""
    try:
        with open(path, encoding="utf-8") as f:
            pol = json.load(f)
        if not isinstance(pol, dict):
            raise ValueError("not an object")
    except (OSError, ValueError) as exc:
        return {"_invalid": True}, "the send policy could not be read (%s)" % exc.__class__.__name__
    if ("script" in pol or "rules" in pol) and "smtp_helpers" not in pol and "report_senders" not in pol:
        # one helper entry saved without its smtp_helpers list: its sends would pass unseen
        return {"_invalid": True}, "the send policy has a helper entry outside an smtp_helpers list"
    note = ""
    if not allow_user_policy and not _locked(path):
        note = ("allow rules were ignored: the policy file is not root-owned and locked "
                "(see README, 'Owner-held policy')")
        for h in pol.get("smtp_helpers", []) or []:
            if isinstance(h, dict):
                h["rules"] = []
    return pol, note


# ----------------------------------------------------------------------------- scanning

_ANSI = {"a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f", "n": "\n", "r": "\r",
         "t": "\t", "v": "\v", "\\": "\\", "'": "'", '"': '"', "?": "?"}


def _ansi(s, i):
    """Decode a $'...' body that starts at s[i]. Return (text, index after the quote)."""
    out, n = [], len(s)
    while i < n:
        c = s[i]
        if c == "'":
            return "".join(out), i + 1
        if c == "\\" and i + 1 < n:
            d = s[i + 1]
            if d in _ANSI:
                out.append(_ANSI[d])
                i += 2
            elif d in "01234567":
                m = re.match(r"[0-7]{1,3}", s[i + 1:])
                out.append(chr(int(m.group(0), 8)))
                i += 1 + len(m.group(0))
            elif d in "xuU":
                width = {"x": 2, "u": 4, "U": 8}[d]
                m = re.match(r"[0-9A-Fa-f]{1,%d}" % width, s[i + 2:])
                if m:
                    try:
                        out.append(chr(int(m.group(0), 16)))
                    except (ValueError, OverflowError):
                        pass
                    i += 2 + len(m.group(0))
                else:
                    out.append("\\" + d)
                    i += 2
            elif d == "c" and i + 2 < n:
                out.append(chr(ord(s[i + 2]) & 31))
                i += 3
            else:
                out.append("\\" + d)
                i += 2
        else:
            out.append(c)
            i += 1
    return None, n


def _protect(text):
    """Mark quoted braces and commas so brace expansion leaves them alone."""
    return "".join(BRACE_SENT.get(c, c) for c in text)


def _single(text):
    """Text as one single-quoted shell word."""
    return "'" + text.replace("'", "'\"'\"'") + "'"


class Scanner:
    """Reads shell text for quoting only (no expansion).

    out:  the command text with comments dropped, heredoc bodies cut out, $'...' decoded
          into plain single quotes, and each $( ) or backtick span replaced by a marker.
    docs: heredocs of this text: (line, start, end, body, quoted delimiter).
    subs: indexes of the $( ) and backtick spans (into the shared list) found outside
          single quotes in this text.
    """

    def __init__(self, text, registry):
        self.s = text
        self.n = len(text)
        self.reg = registry
        self.out = []
        self.olen = 0
        self.docs = []
        self.subs = []
        self.pend = []
        self.line_start = 0
        self.line_chunk = 0

    def emit(self, top, text):
        if top:
            self.out.append(text)
            self.olen += len(text)

    def raw_copy(self, top, i, j):
        """Copy s[i:j] unscanned (arithmetic), and check the $( ) and backticks inside it."""
        text = self.s[i:j]
        if top:
            for sub in substitutions(text):
                self.reg.append(sub)
                self.subs.append(len(self.reg) - 1)
        self.emit(top, text)
        if top and "\n" in text:
            tail = len(text) - text.rfind("\n") - 1
            self.out[-1:] = [text[:len(text) - tail], text[len(text) - tail:]]
            self.line_chunk = len(self.out) - 1
            self.line_start = self.olen - tail
        if self.pend and "\n" in text:
            # A heredoc started before a multi-line arithmetic: fail closed, its body stays code.
            self.pend = []

    def place(self, top, raw):
        if not top:
            return
        self.reg.append(raw)
        idx = len(self.reg) - 1
        self.subs.append(idx)
        self.emit(top, "%sS%d%s" % (SUB_MARK, idx, SUB_MARK))

    def run(self):
        self.code(0, True, False)
        return "".join(self.out)

    def word_start(self, i):
        # Not after ')': in '$(x)#y' the '#' is part of the word, not a comment. Not after
        # an escaped space either: 'a\ #b' is one word.
        if i == 0:
            return True
        if self.s[i - 1] not in " \t\n;&|(<>":
            return False
        k = i - 2
        while k >= 0 and self.s[k] == "\\":
            k -= 1
        return (i - 2 - k) % 2 == 0

    def code(self, i, top, closer):
        """Scan shell code from i. With closer, stop after the ')' that closes $( )."""
        s, n, depth = self.s, self.n, 0
        while i < n:
            c = s[i]
            nx = s[i + 1] if i + 1 < n else ""
            if c == "\n":
                self.emit(top, "\n")
                i += 1
                if self.pend:
                    i = self.bodies(i, top)
                if top:
                    self.line_start = self.olen
                    self.line_chunk = len(self.out)
                continue
            if c == "\\":
                if nx == "\n":
                    self.emit(top, " ")
                elif nx in BRACE_SENT:
                    self.emit(top, BRACE_SENT[nx])
                else:
                    self.emit(top, s[i:i + 2])
                i += 2
                continue
            if c == "'":
                j = s.find("'", i + 1)
                if j < 0:
                    self.emit(top, s[i:])
                    return n
                self.emit(top, "'" + _protect(s[i + 1:j]) + "'")
                i = j + 1
                continue
            if c == "$" and nx == "'":
                text, j = _ansi(s, i + 2)
                if text is None:
                    self.emit(top, s[i:])
                    return n
                self.emit(top, _single(_protect(text)))
                i = j
                continue
            if c == "$" and nx == '"':
                i += 1
                continue
            if c == '"':
                i = self.dquote(i + 1, top)
                continue
            if c == "$" and s.startswith("$((", i):
                j = self.arith(i + 3)
                self.raw_copy(top, i, j)
                i = j
                continue
            if c == "$" and nx == "[":
                # old-style arithmetic $[ ]: '<<' inside is a shift, not a heredoc
                j = self.brackets(i + 2)
                self.raw_copy(top, i, j)
                i = j
                continue
            if c == "(" and nx == "(" and self.word_start(i):
                # arithmetic command (( )): copy it whole, also across lines
                j = self.arith(i + 2)
                self.raw_copy(top, i, j)
                i = j
                continue
            if c == "$" and nx == "(":
                j = self.code(i + 2, False, True)
                self.place(top, s[i + 2:j - 1] if j <= n and s[j - 1:j] == ")" else s[i + 2:j])
                i = j
                continue
            if c == "`":
                j = self.backtick(i + 1)
                self.place(top, s[i + 1:j])
                i = j + 1
                continue
            if c == "$" and nx == "{":
                i = self.param(i, top)
                continue
            if c == "$":
                m = re.match(r"\$(\{IFS\}|IFS(?![A-Za-z0-9_]))", s[i:])
                if m:
                    self.emit(top, " ")
                    i += len(m.group(0))
                    continue
            if c == "#" and self.word_start(i):
                j = s.find("\n", i)
                i = n if j < 0 else j
                continue
            if c == "<" and s.startswith("<<", i) and not s.startswith("<<<", i) and \
                    (i == 0 or s[i - 1] != "<"):
                j = self.heredoc_op(i, top)
                if j is not None:
                    i = j
                    continue
            if closer:
                if c == "(":
                    depth += 1
                elif c == ")":
                    if depth == 0:
                        return i + 1
                    depth -= 1
            self.emit(top, c)
            i += 1
        return n

    def dquote(self, i, top):
        s, n = self.s, self.n
        self.emit(top, '"')
        while i < n:
            c = s[i]
            nx = s[i + 1] if i + 1 < n else ""
            if c == '"':
                self.emit(top, '"')
                return i + 1
            if c == "\\":
                if nx == "\n":
                    i += 2
                    continue
                self.emit(top, s[i:i + 2] if nx not in BRACE_SENT else "\\" + BRACE_SENT[nx])
                i += 2
                continue
            if c == "$" and s.startswith("$((", i):
                j = self.arith(i + 3)
                self.raw_copy(top, i, j)
                i = j
                continue
            if c == "$" and nx == "[":
                j = self.brackets(i + 2)
                self.raw_copy(top, i, j)
                i = j
                continue
            if c == "$" and nx == "(":
                j = self.code(i + 2, False, True)
                self.place(top, s[i + 2:j - 1] if s[j - 1:j] == ")" else s[i + 2:j])
                i = j
                continue
            if c == "$" and nx == "{":
                i = self.param(i, top)
                continue
            if c == "`":
                j = self.backtick(i + 1)
                self.place(top, s[i + 1:j])
                i = j + 1
                continue
            self.emit(top, BRACE_SENT.get(c, c))
            i += 1
        return n

    def param(self, i, top):
        """${...}: copy it whole ('<<' or '#' inside it mean nothing), check $( ) inside."""
        s, depth, j = self.s, 0, i + 1
        while j < self.n:
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            elif s[j] == "\\":
                j += 1
            j += 1
        j = min(j + 1, self.n)
        inner = s[i + 2:j - 1]
        if top:
            for sub in substitutions(inner):
                self.reg.append(sub)
                self.subs.append(len(self.reg) - 1)
        if re.match(r"\$\{IFS([:}\[#%/^,@]|$)", s[i:j]):
            # ${IFS}, ${IFS:0:1}, ${IFS%?} and similar: a word break, as far as this check goes
            self.emit(top, " ")
        else:
            self.emit(top, s[i:j])
        return j

    def arith(self, i):
        depth = 2
        while i < self.n and depth:
            if self.s[i] == "(":
                depth += 1
            elif self.s[i] == ")":
                depth -= 1
            i += 1
        return i

    def brackets(self, i):
        depth = 1
        while i < self.n and depth:
            if self.s[i] == "[":
                depth += 1
            elif self.s[i] == "]":
                depth -= 1
            i += 1
        return i

    def backtick(self, i):
        while i < self.n:
            if self.s[i] == "\\":
                i += 2
                continue
            if self.s[i] == "`":
                return i
            i += 1
        return self.n

    def heredoc_op(self, i, top):
        """Read a '<<' operator and its end word. Return the index after them, or None."""
        s = self.s
        m = re.match(r"<<(-?)[ \t]*", s[i:])
        j = i + len(m.group(0))
        word, quoted = [], False
        while j < self.n and s[j] not in " \t\n;&|()<>":
            c = s[j]
            if c in "'\"":
                k = s.find(c, j + 1)
                if k < 0:
                    return None
                word.append(s[j + 1:k])
                quoted = True
                j = k + 1
            elif c == "\\" and j + 1 < self.n:
                word.append(s[j + 1])
                quoted = True
                j += 2
            else:
                word.append(c)
                j += 1
        if not word:
            return None
        start = self.olen - self.line_start
        self.emit(top, s[i:j])
        self.pend.append(("".join(word), m.group(1) == "-", quoted, start,
                          self.olen - self.line_start, top))
        return j

    def bodies(self, i, top):
        """Cut the bodies of pending heredocs that start at s[i]."""
        s, pend = self.s, self.pend
        self.pend = []
        line_text = "".join(self.out[self.line_chunk:])[:-1] if top else ""
        for word, strip_tabs, quoted, start, end, dtop in pend:
            k, found = i, None
            while k <= self.n:
                e = s.find("\n", k)
                e = self.n if e < 0 else e
                cand = s[k:e]
                cand = cand.lstrip("\t") if strip_tabs else cand
                if cand == word:
                    found = (k, e)
                    break
                if cand.startswith(word + ")"):
                    # bash also ends a heredoc inside $( ) at 'EOF)'; the ')' stays code.
                    found = (k, e)
                    break
                if e >= self.n:
                    break
                k = e + 1
            if found is None:
                continue  # never ends: its lines stay commands (fail closed)
            body = s[i:found[0]]
            if body.endswith("\n"):
                body = body[:-1]
            if dtop and top:
                self.docs.append((line_text, start, end, body, quoted))
            end_line = s[found[0]:found[1]]
            if end_line.lstrip("\t") != word:
                i = found[0] + (len(end_line) - len(end_line.lstrip("\t"))) + len(word)
                break
            i = min(found[1] + 1, self.n)
        return i


def brace_expand(tok, limit=64):
    """Bash brace lists in one word: a{b,c}d gives abd acd. Sequences are not expanded."""
    i = 0
    while True:
        j = tok.find("{", i)
        if j < 0:
            return [tok]
        if j > 0 and tok[j - 1] == "$":
            i = j + 1
            continue
        depth, commas, end = 0, [], None
        for k in range(j, len(tok)):
            if tok[k] == "{":
                depth += 1
            elif tok[k] == "}":
                depth -= 1
                if depth == 0:
                    end = k
                    break
            elif tok[k] == "," and depth == 1:
                commas.append(k)
        if end is None:
            return [tok]
        if not commas:
            i = j + 1
            continue
        pre, post = tok[:j], tok[end + 1:]
        cuts = [j] + commas + [end]
        out = []
        for a, b in zip(cuts, cuts[1:]):
            for e in brace_expand(pre + tok[a + 1:b] + post, limit):
                if e:
                    out.append(e)
                if len(out) >= limit:
                    return out
        return out


def restore(text):
    return "".join(BRACE_BACK.get(c, c) for c in text)


def lex(code):
    """shlex split of scanned code, with brace lists expanded."""
    lx = shlex.shlex(code, posix=True, punctuation_chars="();<>|&\n")
    # bash splits words on space and tab only: a CR stays inside the word ('b<CR>--draft').
    lx.whitespace = " \t"
    lx.whitespace_split = True
    lx.commenters = ""
    out = []
    for tok in lx:
        if tok and all(c in PUNCT for c in tok):
            out.append(tok)
            continue
        out.extend(restore(t) for t in brace_expand(tok))
    return out


def is_sep(tok):
    return bool(tok) and all(c in PUNCT for c in tok) and (
        any(c in SEP_CHARS for c in tok) or tok in ("&", "&&"))


def is_redirect(tok):
    return bool(tok) and all(c in PUNCT for c in tok) and ("<" in tok or ">" in tok) and not is_sep(tok)


def splits_group(tok):
    """True for a separator that ends a pipeline (; newline && || &)."""
    return any(c in ";\n" for c in tok) or "&&" in tok or "||" in tok or tok == "&"


def segments(tokens):
    """Split tokens into (separator before, segment tokens)."""
    segs, cur, before = [], [], ""
    for tok in tokens:
        if is_sep(tok):
            if cur:
                segs.append((before, cur))
            cur, before = [], tok
            continue
        cur.append(tok)
    if cur:
        segs.append((before, cur))
    return segs


def argv(seg):
    """The segment's words without redirections and their targets."""
    out, i = [], 0
    while i < len(seg):
        t = seg[i]
        if is_redirect(t):
            if out and out[-1].isdigit():
                out.pop()
            i += 2
            continue
        out.append(t)
        i += 1
    return out


def base(tok):
    return os.path.basename(tok).lower()


_PARAM_DEFAULT_RE = re.compile(r"\$\{[#!]?[A-Za-z_0-9@*?$!-]+(:?[-=+?])([^{}]*)\}")
_PARAM_ANY_RE = re.compile(r"\$\{[^{}]*\}|\$([A-Za-z_][A-Za-z0-9_]*|[0-9@*#?$!-])")


def norm_word(tok):
    """A guess at the word the shell builds: ${X:-word} gives word, other parameters give
    nothing, {a..b} sequences become a glob, and a leading zsh '=' is dropped."""
    t = tok
    for _ in range(4):
        new = _PARAM_DEFAULT_RE.sub(lambda m: m.group(2) if m.group(1)[-1] in "-=+" else "", t)
        if new == t:
            break
        t = new
    t = _PARAM_ANY_RE.sub("", t)
    t = SEQ_RE.sub("*", t)
    t = PLACE_RE.sub("*", t)
    if t.startswith("=") and len(t) > 1:
        t = t[1:]
    return t


def has_glob(tok):
    return any(c in tok for c in GLOB_CHARS) or bool(SEQ_RE.search(tok))


def word_is(tok, name):
    """True when the word is, or can be built into, name (case-insensitive)."""
    t = norm_word(tok).lower()
    if t == name:
        return True
    return has_glob(t) and fnmatch.fnmatchcase(name, t)


def substitutions(text):
    """Inner text of $( ... ) and backtick spans, quotes ignored (for heredoc bodies)."""
    found, i = [], 0
    while True:
        j = text.find("$(", i)
        if j < 0:
            break
        depth, k = 1, j + 2
        while k < len(text) and depth:
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
            k += 1
        found.append(text[j + 2:k - 1] if depth == 0 else text[j + 2:])
        i = k
    parts = text.split("`")
    found.extend(parts[1::2])
    return [f for f in found if f.strip()]


def skip_options(seg, i, valued):
    """Skip option words from seg[i]. Short clusters like -Eu take the value of their last letter."""
    n = len(seg)
    while i < n and seg[i].startswith("-") and seg[i] != "-":
        t = seg[i]
        i += 1
        if t == "--":
            break
        if t.startswith("--"):
            if "=" not in t and t in valued:
                i += 1
            continue
        for k, ch in enumerate(t[1:], 1):
            if "-" + ch in valued:
                if k == len(t) - 1:
                    i += 1
                break
    return i


def is_info_only(cmd, words):
    info = RAW_INFO | RAW_INFO_BY_CMD.get(cmd, set())
    return bool(words) and all(w in info for w in words)


# ----------------------------------------------------------------------------- options

def resolve(tok, options):
    """Resolve one option token against option names, argparse style.

    Return (names, value). names is a list: one name when the token is exact or a unique
    prefix, several when ambiguous, none when unknown. value is the '=' part or None.
    """
    name, value = (tok.split("=", 1) + [None])[:2] if "=" in tok else (tok, None)
    if name in options:
        return [name], value
    if name.startswith("--") and len(name) > 2:
        return [o for o in options if o.startswith(name)], value
    return [], value


def parse_args(args, value_opts, flag_opts):
    """Walk an argparse-style argv. Return dict with counts, values, unresolved, maybe.

    Options after '--' are still counted (fail closed for sends), but 'safe' lists only the
    options before it: argparse reads a '--dry-run' after '--' as a positional word.
    """
    options = list(value_opts) + list(flag_opts) + ["--help", "-h"]
    counts, values, unresolved, maybe, safe = {}, {}, [], set(), set()
    after_dd = False
    i = 0
    while i < len(args):
        tok = args[i]
        i += 1
        if not tok.startswith("-") or tok == "-" or re.match(r"^-[0-9.]+$", tok):
            continue
        if tok == "--":
            after_dd = True
            continue
        names, value = resolve(tok, options)
        if len(names) != 1:
            unresolved.append(tok)
            maybe.update(names)
            continue
        name = names[0]
        counts[name] = counts.get(name, 0) + 1
        if not after_dd:
            safe.add(name)
        if name in value_opts:
            if value is None:
                if i >= len(args):
                    unresolved.append(tok)
                    continue
                value = args[i]
                i += 1
                if value.startswith("-") and resolve(value, options)[0]:
                    unresolved.append(tok)
                    maybe.update(resolve(value, options)[0])
            values[name] = value
    return {"counts": counts, "values": values, "unresolved": unresolved, "maybe": maybe,
            "safe": safe}


def subject_ok(subject, rule):
    s = subject.lower()
    for w in rule.get("subject_words", []) or []:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(w.lower()) + r"(?![A-Za-z0-9])", s):
            return True
    for w in rule.get("subject_substrings", []) or []:
        if w.lower() in s:
            return True
    return False


def unknown_value(tok):
    """True when the shell fills in part of the word at run time ($VAR, $( ), a glob, a
    {a..b} sequence)."""
    return "$" in tok or SUB_MARK in tok or "\r" in tok or has_glob(tok)


def helper_unknown(tok):
    """unknown_value for the SMTP helper's arguments. A glob counts only when its matches
    could start with '-' (so 'reports/*.pdf' is a file list, '*' or '-*' is not)."""
    if "$" in tok or SUB_MARK in tok or SEQ_RE.search(tok):
        return True
    return has_glob(tok) and (tok[:1] in GLOB_CHARS or tok.startswith("-"))


def check_helper(args, conf, note):
    """Return None when the helper call is allowed, else a reason."""
    to_opt = conf.get("to_option", "--to")
    cc_opt = conf.get("cc_option", "--cc")
    subj_opt = conf.get("subject_option", "--subject")
    send_flags = set(conf.get("send_flags", ["--send"]))
    value_opts = set(conf.get("value_options", [])) | {to_opt, cc_opt, subj_opt}
    flag_opts = set(conf.get("flag_options", [])) | send_flags
    p = parse_args(args, value_opts, flag_opts)
    sending = bool(send_flags & (set(p["counts"]) | p["maybe"]))
    name = conf.get("script", "the SMTP helper")
    if any(helper_unknown(t) for t in args):
        # A word the shell fills in ($VAR, $( ), a glob that can match a file named
        # '--cc=...') could be the send flag or a recipient, and an unquoted one can split
        # into several options. Fail closed, dry runs too.
        return "%s: a word filled in at run time ($VAR, $( ) or a glob) in its arguments" % name
    if not sending:
        return None
    if p["unresolved"]:
        return "%s: unknown or ambiguous option %s in a send" % (name, p["unresolved"][0])
    rep = [k for k, v in p["counts"].items() if v > 1]
    if rep:
        return "%s: option %s given more than once in a send" % (name, rep[0])
    if any(t.startswith("@") for t in args):
        return "%s: an @file argument in a send (argparse can read options from it)" % name
    to = p["values"].get(to_opt, conf.get("default_to", "")).strip().lower()
    cc = p["values"].get(cc_opt, "").strip().lower()
    subject = p["values"].get(subj_opt, "")
    for v in (p["values"].get(to_opt, ""), p["values"].get(cc_opt, ""), subject):
        if "\r" in v or "\n" in v:
            return "%s: a line break inside a header value in a send" % name
    for rule in conf.get("rules", []) or []:
        if to != str(rule.get("to", "")).strip().lower() or not to:
            continue
        if cc not in [str(c).strip().lower() for c in rule.get("cc_allow", [""])]:
            continue
        if subject_ok(subject, rule):
            return None
    reason = "%s: no allow rule matches this recipient, cc and subject" % name
    return reason + ("; " + note if note else "")


def check_reporter(args, conf):
    """A report sender with subcommands. Return None when allowed, else a reason."""
    gvals = set(conf.get("global_value_options", []))
    subs = conf.get("subcommands", {}) or {}
    i, sub, unknown = 0, None, False
    while i < len(args):
        tok = args[i]
        i += 1
        if unknown_value(tok):
            unknown = True
        if tok.startswith("-"):
            names, value = resolve(tok, list(gvals))
            if len(names) == 1 and value is None:
                i += 1
            elif not names:
                unknown = True
            continue
        cands = [s for s in subs if s == tok] or [s for s in subs if s.startswith(tok)]
        if cands:
            sub = cands[0] if len(cands) == 1 else cands
            break
        if not unknown:
            break
    if sub is None:
        if unknown and any(unknown_value(t) for t in args):
            return "%s: a word filled in at run time could be a send subcommand" % conf.get(
                "script", "report sender")
        return None
    for s in (sub if isinstance(sub, list) else [sub]):
        sc = subs[s]
        safe = set(sc.get("safe_flags", []))
        sflags = set(sc.get("send_flags", []))
        p = parse_args(args[i:], set(sc.get("value_options", [])), set(sc.get("flag_options", [])) | safe | sflags)
        if p["safe"] & safe:
            continue
        if sflags and any(unknown_value(t) for t in args[i:]):
            return "%s %s: a word filled in at run time could be a send flag" % (
                conf.get("script", "report sender"), s)
        if sc.get("always_sends") or (sflags & (set(p["counts"]) | p["maybe"])):
            return "%s %s sends email (add %s for a dry run)" % (
                conf.get("script", "report sender"), s, " or ".join(sorted(safe)) or "nothing")
    return None


def script_matches(tok, script):
    """A word names the configured script: same file name (any case), or a glob that fits it."""
    b, want = base(tok), script.lower()
    if b == want:
        return True
    if any(c in b for c in "*?["):
        return fnmatch.fnmatchcase(want, b)
    return False


# ----------------------------------------------------------------------------- analysis

class Budget(Exception):
    """The command is past the work limits (MAX_SEGMENTS, MAX_CALLS)."""


# Variables whose value a program runs as a command (PAGER='...' git log).
CMD_VARS = {"GIT_SSH_COMMAND", "GIT_SSH", "GIT_EDITOR", "GIT_PAGER", "GIT_SEQUENCE_EDITOR",
            "GIT_EXTERNAL_DIFF", "GIT_ASKPASS", "SSH_ASKPASS", "PAGER", "EDITOR", "VISUAL",
            "PROMPT_COMMAND", "LESSOPEN", "LESSCLOSE", "MANPAGER", "SYSTEMD_PAGER"}
ZSH_QUAL_RE = re.compile(r"^[^\s:/|!#]*?[eE]([:/|!#])(.+)\1$", re.S)


def url_forms(t):
    """A URL word as the server or curl may read it: raw, percent-decoded, and with curl's
    {a,b} glob braces removed."""
    try:
        dec = unquote(t)
    except Exception:  # noqa: BLE001 (any decode problem: keep the raw form)
        dec = t
    return [t, dec, dec.replace("{", "").replace("}", "")]


def mail_api(t):
    return any(MAIL_API_RE.search(f) for f in url_forms(t)) or bool(GMAIL_URL_GLOB_RE.search(t))


# Fail-closed check for text the analyzer cannot read in full (unparsable, or past the work
# limits). It is wider than the analyzer on purpose, because the analyzer is not there to
# read the shell's own spelling tricks.
FALLBACK_WORD_RE = re.compile(r"send|mail|smtp", re.I)
GLOB_WORD_RE = re.compile(r"[^\s;|&()<>'\"`]*[?*\[][^\s;|&()<>'\"`]*")
MAX_GLOB_WORDS = 5000


def fallback_hit(text, scripts=()):
    """True when text that cannot be checked in full could hold a send: any analyzer
    pattern; 'send', 'mail' or 'smtp' once quotes, escapes, $, ${...}, braces and glob
    characters are removed (so sen{d..d}, sen${X}d and sendmai? count); or a glob word
    that could match a raw sender, the Gmail CLI or a configured script."""
    if SEND_TOKEN_RE.search(text) or CODE_SEND_RE.search(text) or CODE_RAW_RE.search(text) or \
            CODE_APP_RE.search(text) or CURL_SMTP_RE.search(text) or mail_api(text):
        return True
    nobrace = re.sub(r"\$\{[^{}]*\}", "", text)
    for t in (nobrace, re.sub(r"\$(\w+|[@*#?$!-])", "", nobrace)):
        if FALLBACK_WORD_RE.search(re.sub(r"[^A-Za-z0-9+./_@:\s-]", "", t)):
            return True
    low = text.lower()
    if any(s.lower() in low for s in scripts):
        return True
    names = {n.lower() for n in RAW_SENDERS} | {s.lower().rsplit("/", 1)[-1] for s in scripts} | \
        {"gmail", "+send", "+reply", "+reply-all", "+forward"}
    for n, w in enumerate(GLOB_WORD_RE.finditer(text)):
        if n >= MAX_GLOB_WORDS:
            return True
        base = w.group(0).rsplit("/", 1)[-1].lower()
        if re.search(r"[a-z]", base) and any(fnmatch.fnmatchcase(name, base) for name in names):
            return True
    return False


def app_send(code):
    """A scriptable mail app reference followed by a send command outside string literals."""
    for m in CODE_APP_RE.finditer(code):
        rest = code[m.end():]
        rest = re.sub(r'"(\\.|[^"\\])*"', '""', rest)
        rest = re.sub(r"'(\\.|[^'\\\n])*'", "''", rest)
        if re.search(r"\bsend\b", rest, re.I):
            return True
    return False


class Analyzer:
    def __init__(self, policy, note):
        self.policy = policy
        self.note = note
        self.reg = []
        self.calls = 0

    def unplace(self, text):
        for _ in range(MAX_DEPTH + 2):
            new = PLACE_RE.sub(lambda m: "$(" + self.reg[int(m.group(1))] + ")", text)
            if new == text:
                break
            text = new
        return text

    def literal_output(self, inner):
        """The text a $( ) prints when it only runs echo or printf on literal words, else None."""
        try:
            sc = Scanner(inner, [])
            code = sc.run()
            if sc.subs or sc.docs or sc.pend:
                return None
            toks = lex(code)
        except (ValueError, IndexError):
            return None
        if not toks or any(is_sep(t) or is_redirect(t) for t in toks):
            return None
        name, args = base(toks[0]), toks[1:]
        if name == "echo":
            while args and re.match(r"^-[neE]+$", args[0]):
                args = args[1:]
            return " ".join(args)
        if name == "printf" and args:
            vals = iter(args[1:])
            out = re.sub(r"%[sbqd]", lambda _m: next(vals, ""), args[0])
            return out.replace("\\n", "\n").replace("\\t", "\t")
        return None

    def literal_command(self, seg):
        """An unquoted $(echo gws gmail +send) as the command word: the shell splits its
        output into the command and its first arguments."""
        k = 0
        while k < len(seg) and ASSIGN_RE.match(seg[k]):
            k += 1
        if k < len(seg):
            m = PLACE_RE.fullmatch(seg[k])
            if m:
                lit = self.literal_output(self.reg[int(m.group(1))])
                if lit and len(lit.split()) > 1:
                    return seg[:k] + lit.split() + seg[k + 1:]
        return seg

    def with_literals(self, code):
        """code with each $( ) that only prints literal text replaced by that text."""
        def rep(m):
            lit = self.literal_output(self.reg[int(m.group(1))])
            return lit if lit is not None else m.group(0)
        return PLACE_RE.sub(rep, code)

    def cmd_name(self, tok):
        """The command name a word stands for: file name in lower case, after ${X:-word}
        defaults, a zsh '=cmd', $(echo word), and a glob matched against known names."""
        t = tok
        m = PLACE_RE.fullmatch(t)
        if m:
            lit = self.literal_output(self.reg[int(m.group(1))])
            if lit is not None and len(lit.split()) == 1:
                t = lit.strip()
        b = base(norm_word(t))
        if has_glob(b) and re.sub(r"[*?\[\]]", "", b):
            for name in sorted(RAW_SENDERS | SHELLS | AT_CMDS | set(GLOB_NAMES)):
                if fnmatch.fnmatchcase(name, b):
                    return name
        return b

    def code_scan(self, code, lang=""):
        """Reason when interpreter code (inline, heredoc or piped) looks like it sends mail."""
        code = self.unplace(code)
        if CODE_SEND_RE.search(code) or CODE_RAW_RE.search(code) or app_send(code) or mail_api(code):
            return "inline code that can send email"
        if lang.startswith("php") and PHP_MAIL_RE.search(code):
            return "inline PHP code that calls mail()"
        for m in CODE_GMAIL_RE.finditer(code):
            # --draft counts only inside the same call: up to the list or call end.
            window = code[m.end():]
            cut = re.search(r"[\])\n;]", window)
            window = window[:cut.start()] if cut else window
            if not re.search(r"(?<![\w-])--draft(?![\w-])", window):
                return "inline code that runs a Gmail send helper without --draft in the same call"
        low = code.lower()
        for h in self.policy.get("smtp_helpers", []) or []:
            if isinstance(h, dict) and h.get("script") and h["script"].lower() in low and "--send" in low:
                return "inline code that runs %s with a send flag" % h["script"]
        return None

    def scripts(self):
        out = []
        for key in ("smtp_helpers", "report_senders"):
            for h in self.policy.get(key, []) or []:
                if isinstance(h, dict) and h.get("script"):
                    out.append(h["script"])
        return out

    def value_checks(self, name, value, depth):
        """An assignment's value: $( ) written inside single quotes runs when the value is
        later used in arithmetic or prompt expansion; some variables hold commands."""
        reasons = []
        for sub in substitutions(value):
            reasons += self.analyze(sub, depth + 1)
        if name.split("[")[0].rstrip("+") in CMD_VARS:
            reasons += self.analyze(value, depth + 1)
        return reasons

    def analyze(self, text, depth=0):
        """Return a list of block reasons for one shell command string."""
        self.calls += 1
        if self.calls > MAX_CALLS:
            raise Budget()
        if depth > MAX_DEPTH:
            return ["command nests too deeply to check"]
        text = CTRL_RE.sub("?", self.unplace(text))
        sc = Scanner(text, self.reg)
        code = sc.run()
        reasons = []
        for idx in sc.subs:
            reasons += self.analyze(self.reg[idx], depth + 1)
        for line, start, end, body, quoted in sc.docs:
            for cmd in self.heredoc_consumers(line, start, end):
                if cmd is None or cmd in SHELLS or cmd in SOURCE_CMDS or cmd in AT_CMDS or cmd == "eval":
                    # a shell reads it, or the reader cannot be named: check it as commands
                    reasons += self.analyze(body, depth + 1)
                elif INTERP_RE.match(cmd):
                    r = self.code_scan(body, cmd)
                    if r:
                        reasons.append("heredoc into %s: %s" % (cmd, r))
                elif cmd == "curl" and (CURL_SMTP_RE.search(body) or mail_api(body)):
                    reasons.append("heredoc into curl: a mail server or mail API")
            if not quoted:
                # An unquoted heredoc runs $( ) and backticks in its body, whatever reads it.
                for inner in substitutions(body):
                    reasons += self.analyze(inner, depth + 1)
        try:
            tokens = lex(code)
        except ValueError:
            tokens = None
            if re.search(r"(?<!\\)(\\\\)*\\$", code):
                # bash keeps a trailing backslash as a plain character; shlex refuses it
                try:
                    tokens = lex(code + "\\")
                except ValueError:
                    tokens = None
        if tokens is None:
            # bash runs the complete lines before a broken quote, so the whole text is read
            # with the wide fail-closed check.
            if fallback_hit(text, self.scripts()) or fallback_hit(restore(code), self.scripts()):
                return reasons + ["the command could not be parsed and it holds a send-capable token"]
            return reasons
        segs = segments(tokens)
        if len(segs) > MAX_SEGMENTS:
            raise Budget()
        # Expand variables set earlier in the same command (C=...; $C), as the shell would.
        env, expanded = {}, []
        for before, seg in segs:
            words = [t for t in seg if not (t in DECLARERS and t is seg[0])]
            if words and all(ASSIGN_RE.match(t) for t in words):
                for t in words:
                    name, value = t.split("=", 1)
                    reasons += self.value_checks(name, value, depth)
                    plus = name.endswith("+")
                    name = name.rstrip("+").split("[")[0]
                    if plus:
                        value = env.get(name, "") + value
                    env[name] = value
                if seg[0] in DECLARERS:
                    expanded.append((before, seg))
                continue
            new, values = self.expand(seg, env)
            new = self.literal_command(new)
            for v in values:
                reasons += self.analyze(v, depth + 1)
            if before.endswith("(") and new:
                # zsh glob qualifier (e:code:) runs code
                m = ZSH_QUAL_RE.match(new[0])
                if m:
                    reasons += self.analyze(m.group(2), depth + 1)
            expanded.append((before, new))
        groups, cur = [], []
        for before, seg in expanded:
            if cur and splits_group(before):
                groups.append(cur)
                cur = []
            cur.append((before, seg))
        if cur:
            groups.append(cur)
        for group in groups:
            info = []
            for _b, s in group:
                oav = argv(s)
                op = self.positions(oav) if len(group) > 1 else []
                info.append((oav, op[0][0] + 1 if op else 0))
            for k in range(len(group)):
                others = info[:k] + info[k + 1:]
                reasons += self.check_segment(group[k][1], others, depth)
        return reasons

    @staticmethod
    def expand(seg, env):
        """Return (segment with known variables filled in, values used as whole words).

        Unquoted expansions split into words (on whitespace, and on a same-command IFS); a
        value right after a code flag (-c, -e) is kept as one word, as "$C" would be."""
        if not env:
            return seg, []
        ifs = env.get("IFS")

        def split(v):
            if ifs:
                v = re.sub("[" + re.escape(ifs) + "]", " ", v)
            return v.split()

        out, values = [], []
        for t in seg:
            if VAR_RE.match(t):
                name = t[1:].strip("{}")
                if name in env:
                    prev = out[-1] if out else ""
                    if re.match(r"^-[A-Za-z]*[ceErp]$", prev) or prev in ("--eval", "--command", "--print"):
                        out.append(env[name])
                    else:
                        out.extend(split(env[name]))
                    values.append(env[name])
                    continue
            new = t
            for name, value in env.items():
                new = re.sub(r"\$(\{%s\}|%s(?![A-Za-z0-9_]))" % (re.escape(name), re.escape(name)),
                             lambda _m, v=value: v, new)
            if new != t:
                out.extend(split(new) or [""])
            else:
                out.append(t)
        return out, values

    def heredoc_consumers(self, line, start, end):
        """Commands that read a heredoc: its own command, commands piped from it, and any
        shell or interpreter that reads its input in the same pipeline. None stands for a
        reader that cannot be named (a compound command, 'exec 3<<', a redirect first)."""
        try:
            htoks = lex(line[:start])
            head = segments(htoks)
            tail = segments(lex(line[end:]))
        except ValueError:
            return ["sh"]
        own_head = bool(head) and not (htoks and is_sep(htoks[-1]))
        own = argv(head[-1][1]) if own_head else []
        rest = tail
        if tail and not tail[0][0]:
            own = own + argv(tail[0][1])  # the rest of its own command (redirect first)
            rest = tail[1:]
        names = [self.own_reader(own)]
        for before, seg in rest:
            if not ("|" in before and "||" not in before):
                break
            av = argv(seg)
            pos = self.positions(av)
            if pos:
                names.append(self.cmd_name(av[pos[0][0]]))
        # The same pipeline (no ; && || or newline in between): a shell reading its input
        # there, as in 'bash < <(cat <<EOF ...)' or 'cat <<EOF | tee >(bash)'.
        group = []
        hsegs = head[:-1] if own_head else head
        if (own_head and splits_group(head[-1][0])) or \
                (not own_head and htoks and is_sep(htoks[-1]) and splits_group(htoks[-1])):
            hsegs = []
        for before, seg in reversed(hsegs):
            group.append(seg)
            if splits_group(before):
                break
        for before, seg in rest:
            if splits_group(before):
                break
            group.append(seg)
        for seg in group:
            av = argv(seg)
            for ci, _x in self.positions(av):
                name = self.cmd_name(av[ci])
                if name in SHELLS and self.shell_mode(name, av[ci + 1:])[0] == "stdin":
                    names.append("sh")
                elif name in AT_CMDS:
                    names.append("sh")
                elif INTERP_RE.match(name) and self.interp_mode(name, av[ci + 1:])[0] == "stdin":
                    names.append(name)
        return list(dict.fromkeys(names))

    def own_reader(self, own):
        pos = self.positions(own)
        if not pos:
            return None
        ci = pos[0][0]
        name = self.cmd_name(own[ci])
        if name in CLOSERS or name.isdigit() or not name:
            return None
        if name == "ssh":
            tail = self.ssh_tail(own, ci)
            if not tail:
                return "sh"
            tname = self.cmd_name(tail[0])
            if tname in SHELLS or tname in AT_CMDS or INTERP_RE.match(tname):
                return tname
        return name

    def interesting(self, tok):
        b = self.cmd_name(tok)
        return (b in RAW_SENDERS or b in SHELLS or b in SOURCE_CMDS or b in AT_CMDS or INTERP_RE.match(b)
                or b in ("gws", "curl", "eval", "ssh", "himalaya", "wget", "http", "https", "xh", "git", "aws")
                or any(script_matches(tok, s) for s in self.scripts()))

    def positions(self, av, start=0, xargs=False, out=None, strings=None, assigns=None):
        """Command positions in a segment: [(index, run by xargs)]. Strings that a wrapper
        runs as shell code (env -S, su -c, watch) go into the strings list, and assignments
        skipped on the way (also after env, sudo or timeout) into the assigns list."""
        out = [] if out is None else out
        i, n = start, len(av)
        while i < n:
            t = av[i]
            b = self.cmd_name(t)
            if ASSIGN_RE.match(t) or t in KEYWORDS:
                if assigns is not None and ASSIGN_RE.match(t):
                    assigns.append(t)
                if t == "coproc" and i + 2 < n and av[i + 2] == "{":
                    i += 1  # coproc NAME { ...; }: skip the NAME too
                i += 1
            elif t == "repeat":
                i += 2  # zsh: repeat N command
            elif t == "function":
                i += 2
            elif b in WRAPPERS:
                valued = WRAPPERS[b]
                j = i + 1
                if b == "command" and j < n and av[j] in ("-v", "-V"):
                    return out  # a lookup, not a run
                if b == "env":
                    k = j
                    while k < n and av[k].startswith("-") and av[k] != "-":
                        a = av[k]
                        if a in ("-S", "--split-string") and k + 1 < n:
                            if strings is not None:
                                strings.append(" ".join([av[k + 1]] + [shlex.quote(w) for w in av[k + 2:]]))
                            return out
                        if a.startswith("--split-string="):
                            if strings is not None:
                                strings.append(" ".join([a.split("=", 1)[1]] + [shlex.quote(w) for w in av[k + 1:]]))
                            return out
                        if not a.startswith("--"):
                            for p, ch in enumerate(a[1:], 1):
                                if ch in "uCP":
                                    break  # the rest of the cluster is that option's value
                                if ch == "S":
                                    val = a[p + 1:] if p + 1 < len(a) else (av[k + 1] if k + 1 < n else "")
                                    more = av[k + 1:] if p + 1 < len(a) else av[k + 2:]
                                    if strings is not None:
                                        strings.append(" ".join([val] + [shlex.quote(w) for w in more]))
                                    return out
                        k += 1
                i = skip_options(av, j, valued)
                if b in ("timeout", "gtimeout") and i < n:
                    i += 1  # the duration, whatever its form (30, 1e3, inf)
                if b == "xargs":
                    xargs = True
            elif b in RUNNERS:
                if b in ("su", "runuser"):
                    for k in range(i + 1, n):
                        if av[k] in ("-c", "--command") and k + 1 < n:
                            if strings is not None:
                                strings.append(av[k + 1])
                        elif av[k].startswith("--command="):
                            if strings is not None:
                                strings.append(av[k].split("=", 1)[1])
                    return out
                if b == "watch":
                    k = skip_options(av, i + 1, {"-n", "-d", "--interval", "--differences"})
                    if k < n and strings is not None:
                        strings.append(" ".join(av[k:]))
                    return out
                if b == "find":
                    for k in range(i + 1, n):
                        if av[k] in ("-exec", "-execdir", "-ok", "-okdir") and k + 1 < n:
                            self.positions(av, k + 1, xargs, out, strings, assigns)
                    return out
                for k in range(i + 1, n):
                    if strings is not None and (" " in av[k] or "\n" in av[k]) and not av[k].startswith("-"):
                        strings.append(av[k])
                k0 = i + 1
                verbs = RUNNER_VERBS.get(b)
                if verbs is not None:
                    kv = next((k for k in range(i + 1, n) if av[k] in verbs), None)
                    if kv is None:
                        return out  # npm install sendmail, docker logs mail: nothing runs
                    k0 = kv + 1
                if b in RUNNER_VALUED:
                    k = skip_options(av, i + 1, RUNNER_VALUED[b])
                    return self.positions(av, k, xargs, out, strings, assigns) if k < n else out
                for k in range(k0, n):
                    if self.interesting(av[k]):
                        return self.positions(av, k, xargs, out, strings, assigns)
                return out
            else:
                out.append((i, xargs))
                return out
        return out

    @staticmethod
    def xargs_repl(av):
        """The replace string of xargs -I / -J / -i, or None."""
        for k, t in enumerate(av):
            if base(t) != "xargs":
                continue
            j = k + 1
            while j < len(av) and av[j].startswith("-"):
                a = av[j]
                if a in ("-I", "-J") and j + 1 < len(av):
                    return av[j + 1]
                if a.startswith(("-I", "-J")) and len(a) > 2:
                    return a[2:]
                if a in ("-i", "--replace"):
                    return "{}"
                if a.startswith("--replace="):
                    return a.split("=", 1)[1]
                if a.startswith("-i") and len(a) > 2:
                    return a[2:]
                j += 2 if a in WRAPPERS["xargs"] else 1
            return None
        return None

    def check_segment(self, seg, others, depth):
        reasons = []
        av = argv(seg)
        strings, assigns = [], []
        pos = self.positions(av, strings=strings, assigns=assigns)
        for t in assigns:
            # prefix assignments and those passed through env, sudo or timeout
            name, value = t.split("=", 1)
            reasons += self.value_checks(name, value, depth)
        for s in strings:
            reasons += self.analyze(s, depth + 1)
        first = av[pos[0][0]] if pos else None
        text_only = first is not None and self.cmd_name(first) in TEXT_ONLY
        xargs = any(x for _, x in pos)
        extra = []
        if xargs:
            # xargs appends words from its input: take them from the commands piped into it.
            for oav, start in others:
                for w in oav[start:]:
                    extra.extend(w.split())
        eff = av + extra

        if not text_only:
            reasons += self.gmail_checks(eff, xargs)

        for ci, x in pos:
            reasons += self.check_command(av, ci, seg, others, depth, extra)
            if x and extra:
                joined = " ".join(extra)
                name = self.cmd_name(av[ci])
                if name in SHELLS or name in AT_CMDS or name == "eval":
                    # 'xargs bash -c': the input becomes the code
                    reasons += self.analyze(joined, depth + 1)
                elif INTERP_RE.match(name):
                    r = self.code_scan(joined, name)
                    if r:
                        reasons.append(r)
                repl = self.xargs_repl(av)
                if repl:
                    av_r = av[:ci] + [w.replace(repl, joined) for w in av[ci:]]
                    reasons += self.check_command(av_r, ci, seg, others, depth, extra)
                    if not text_only:
                        reasons += self.gmail_checks(av_r, xargs)

        if not text_only:
            for conf in self.policy.get("smtp_helpers", []) or []:
                if not isinstance(conf, dict) or not conf.get("script"):
                    continue
                for i, t in enumerate(eff):
                    if script_matches(t, conf["script"]):
                        r = check_helper(eff[i + 1:], conf, self.note)
                        if r:
                            reasons.append(r)
                        break
            for conf in self.policy.get("report_senders", []) or []:
                if not isinstance(conf, dict) or not conf.get("script"):
                    continue
                for i, t in enumerate(eff):
                    if script_matches(t, conf["script"]):
                        r = check_reporter(eff[i + 1:], conf)
                        if r:
                            reasons.append(r)
                        break
        if self.policy.get("_invalid"):
            for t in eff:
                name = t.split("=", 1)[0]
                if name.startswith("--send") or (len(name) >= 4 and "--send".startswith(name)):
                    # the helper's name is unknown, so any spelling argparse reads as --send counts
                    reasons.append("a send flag (%s) while the send policy is unreadable" % name)
                    break
        return reasons

    @staticmethod
    def gmail_checks(av, xargs):
        """Gmail CLI helpers and raw API sends, wherever 'gmail' (or a word the shell fills
        in) is followed by them."""
        reasons = []
        for i, t in enumerate(av):
            is_gmail = word_is(t, "gmail")
            if not is_gmail and not unknown_value(t):
                continue
            if i + 1 >= len(av):
                if is_gmail and xargs:
                    reasons.append("gmail as the last word under xargs (its input supplies the subcommand)")
                continue
            nxt = av[i + 1]
            helper = any(word_is(nxt, h) for h in GMAIL_HELPERS)
            if helper or (is_gmail and unknown_value(nxt)):
                safe = False
                for j in range(i + 2, len(av)):
                    if av[j] == "--":
                        break
                    if av[j] in GMAIL_SAFE:
                        pv = av[j - 1]
                        if pv.startswith("-") and "=" not in pv and pv not in GMAIL_BOOL:
                            continue
                        safe = True
                        break
                if not safe:
                    reasons.append("gmail %s without --draft in the same command" % nxt)
            if is_gmail and len(av) > i + 3 and word_is(av[i + 1], "users") and \
                    (word_is(av[i + 2], "messages") or word_is(av[i + 2], "drafts")):
                send = False
                for j in range(i + 3, len(av)):
                    w, prev = av[j], av[j - 1]
                    is_value = prev.startswith("-") and "=" not in prev and prev not in GMAIL_BOOL
                    if is_value:
                        continue
                    if word_is(w, "send") or (unknown_value(w) and not w.startswith(("-", "{", "@"))):
                        send = True
                        break
                help_ = any(av[j] in GMAIL_HELP and not (av[j - 1].startswith("-") and "=" not in av[j - 1])
                            for j in range(i + 3, len(av)))
                if send and not help_:
                    reasons.append("gmail users %s send (a raw API send)" % av[i + 2])
        return reasons

    def stdin_code(self, others, depth):
        """Text piped or fed into a shell is shell code."""
        reasons = []
        for oav, start in others:
            for t in oav[start:]:
                reasons += self.analyze(t, depth + 1)
            reasons += self.analyze(" ".join(shlex.quote(w) for w in oav[start:]), depth + 1)
        return reasons

    def stdin_interp(self, others, cmd):
        parts = []
        for oav, _start in others:
            parts.extend(oav)
        r = self.code_scan(" \n".join(parts), cmd) if parts else None
        return [r] if r else []

    def ssh_tail(self, av, ci):
        """The remote command words of ssh (options may also follow the host)."""
        k = skip_options(av, ci + 1, SSH_VALUED)
        k = skip_options(av, k + 1, SSH_VALUED)
        return av[k:]

    def check_command(self, av, ci, seg, others, depth, extra):
        reasons = []
        tok = av[ci]
        cmd, rest = self.cmd_name(tok), av[ci + 1:]
        stdin_shell = False
        if cmd in RAW_SENDERS:
            if not (is_info_only(cmd, rest) and not any("<" in t for t in seg)):
                reasons.append("%s sends mail directly" % cmd)
        elif cmd == "himalaya" and "send" in rest:
            reasons.append("himalaya send sends mail directly")
        elif cmd in ("curl", "wget", "http", "https", "xh"):
            if cmd == "curl" and any(re.search(r"(^|=)smtps?://", t, re.I) or t.startswith("--mail-rcpt")
                                     or t.startswith("--mail-from") for t in rest):
                reasons.append("curl to an SMTP server")
            elif any(mail_api(t) for t in rest):
                reasons.append("%s to a mail API" % cmd)
            elif any(SES_HOST_RE.search(t) for t in rest) and any(SES_SEND_RE.search(t) for t in rest):
                reasons.append("%s to the SES send API" % cmd)
        elif cmd == "aws":
            words = [w.lower() for w in rest]
            if ("ses" in words or "sesv2" in words) and any(w.startswith("send-") for w in words):
                reasons.append("aws ses send sends mail")
        elif cmd == "git":
            k = ci + 1
            while k < len(av) and av[k].startswith("-"):
                t = av[k]
                if t == "-c" and k + 1 < len(av):
                    reasons += self.git_config(av[k + 1], depth)
                    k += 2
                    continue
                if t.startswith("-c") and len(t) > 2:
                    reasons += self.git_config(t[2:], depth)
                elif t in GIT_VALUED:
                    k += 1
                k += 1
            sub = av[k] if k < len(av) else ""
            if word_is(sub, "send-email") and not all(w in ("--help", "-h") for w in av[k + 1:] or ["x"]):
                reasons.append("git send-email sends mail")
        elif cmd in SHELLS or cmd in SOURCE_CMDS or (VAR_RE.match(tok) and rest[:1] and
                                                    re.match(r"^-[A-Za-z]*c[A-Za-z]*$", rest[0])):
            mode, code = self.shell_mode(cmd, rest)
            if mode == "code":
                reasons += self.analyze(code, depth + 1)
                lit = self.with_literals(code)
                if lit != code:
                    reasons += self.analyze(lit, depth + 1)
                if others:
                    # 'echo CODE | bash -c bash': the code may read and run its input
                    reasons += self.stdin_code(others, depth)
            elif mode == "stdin":
                stdin_shell = True
                reasons += self.stdin_code(others, depth)
        elif cmd in AT_CMDS:
            if "-f" not in rest:
                stdin_shell = True
                reasons += self.stdin_code(others, depth)
        elif cmd == "eval":
            if rest[:1] == ["--"]:
                rest = rest[1:]
            code = " ".join(rest)
            reasons += self.analyze(code, depth + 1)
            lit = self.with_literals(code)
            if lit != code:
                reasons += self.analyze(lit, depth + 1)
        elif cmd == "trap":
            args = list(rest)
            while args and args[0] in ("--", "-p", "-l", "-P"):
                args = args[1:]
            if args and args[0] != "-":
                reasons += self.analyze(args[0], depth + 1)
        elif cmd == "alias":
            for a in rest:
                if "=" in a and not a.startswith("-"):
                    reasons += self.analyze(a.split("=", 1)[1], depth + 1)
        elif cmd == "hash":
            for k, a in enumerate(rest):
                target = rest[k + 1] if a == "-p" and k + 1 < len(rest) else (
                    a.split("=", 1)[1] if "=" in a and not a.startswith("-") else None)
                if target and self.interesting(target):
                    reasons.append("hash gives %s another name" % base(target))
        elif cmd in DECLARERS:
            for a in rest:
                if ASSIGN_RE.match(a):
                    name, value = a.split("=", 1)
                    reasons += self.value_checks(name, value, depth)
        elif cmd == "ssh":
            tail = self.ssh_tail(av, ci)
            if not tail:
                # no remote command: the remote shell runs what comes in on stdin
                stdin_shell = True
                reasons += self.stdin_code(others, depth)
            else:
                reasons += self.analyze(" ".join(tail), depth + 1)
                tname = self.cmd_name(tail[0])
                if (tname in SHELLS and self.shell_mode(tname, tail[1:])[0] == "stdin") or tname in AT_CMDS:
                    stdin_shell = True
                    reasons += self.stdin_code(others, depth)
                elif INTERP_RE.match(tname) and self.interp_mode(tname, tail[1:])[0] == "stdin":
                    reasons += self.stdin_interp(others, tname)
        elif INTERP_RE.match(cmd):
            mode, codes = self.interp_mode(cmd, rest)
            if mode == "module":
                if codes.split(".")[0].lower() in PY_SEND_MODULES:
                    reasons.append("%s -m %s sends mail" % (cmd, codes))
                codes = []
            elif mode == "stdin":
                codes = []
                reasons += self.stdin_interp(others, cmd)
            elif mode == "code" and others:
                # 'echo CODE | python3 -c "exec(sys.stdin.read())"'
                reasons += self.stdin_interp(others, cmd)
            for code in codes or []:
                r = self.code_scan(code, cmd)
                if r:
                    reasons.append(r)
        for j, t in enumerate(seg):
            if t == "<<<" and j + 1 < len(seg):
                word = seg[j + 1]
                if cmd in SHELLS or cmd in SOURCE_CMDS or stdin_shell:
                    reasons += self.analyze(word, depth + 1)
                elif INTERP_RE.match(cmd):
                    r = self.code_scan(word, cmd)
                    if r:
                        reasons.append(r)
                elif cmd == "curl" and (CURL_SMTP_RE.search(word) or mail_api(word)):
                    reasons.append("here-string into curl: a mail server or mail API")
        return reasons

    def git_config(self, kv, depth):
        """git -c key=value: alias values that start with '!' and command settings run code."""
        value = kv.split("=", 1)[1] if "=" in kv else ""
        if value.startswith("!"):
            value = value[1:]
        return self.analyze(value, depth + 1) if value.strip() else []

    @staticmethod
    def shell_mode(cmd, rest):
        """('code', text) for sh -c, ('stdin', None) when the shell reads code from its
        input or a /dev/stdin-like file, ('file', None) for a script file."""
        opts, first, i, after_dd = [], None, 0, False
        while i < len(rest):
            t = rest[i]
            if not after_dd and t == "--":
                after_dd = True
                i += 1
                continue
            if not after_dd and (t in ("--command", "--init-command") or (cmd == "fish" and t == "-C")):
                return ("code", rest[i + 1]) if i + 1 < len(rest) else ("none", None)
            if not after_dd and t.startswith(("--command=", "--init-command=")):
                return "code", t.split("=", 1)[1]
            if not after_dd and t != "-" and t[:1] in "-+" and len(t) > 1:
                opts.append(t)
                if t in SHELL_VALUED:
                    i += 1
                i += 1
                continue
            first = t
            break
        short = "".join(o[1:] for o in opts if not o.startswith("--"))
        if cmd in SOURCE_CMDS:
            short = ""
        if "c" in short:
            return ("code", first or "") if first is not None else ("none", None)
        if "s" in short or first is None or first == "-" or first.startswith("/dev/stdin") or \
                first.startswith("/dev/fd/") or first.startswith("/proc/self/fd/"):
            return "stdin", None
        return "file", None

    @staticmethod
    def interp_mode(cmd, rest):
        """('code', [texts]) for inline code, ('stdin', None) when code comes from input,
        ('module', name) for python -m, ('file', None) for a script file."""
        codes, i = [], 0
        py = cmd.startswith(PY_PREFIXES)
        if cmd in AWKS:
            return "code", [" ".join(rest)]
        if cmd in ("deno", "bun") and rest[:1] == ["eval"]:
            return "code", [" ".join(rest[1:])]
        first = None
        while i < len(rest):
            t = rest[i]
            i += 1
            if t == "--":
                first = rest[i] if i < len(rest) else None
                break
            if t == "-" or not t.startswith("-"):
                first = t
                break
            if py:
                if t.startswith("--"):
                    if t == "--check-hash-based-pycs":
                        i += 1
                    continue
                for k, ch in enumerate(t[1:], 1):
                    if ch == "c":
                        if k < len(t) - 1:
                            codes.append(t[k + 1:])
                        elif i < len(rest):
                            codes.append(rest[i])
                            i += 1
                        return "code", codes
                    if ch == "m":
                        if k < len(t) - 1:
                            return "module", t[k + 1:]
                        return ("module", rest[i]) if i < len(rest) else ("file", None)
                    if ch in "WX":
                        if k == len(t) - 1:
                            i += 1
                        break
                continue
            if t.startswith(("--eval=", "--print=")):
                codes.append(t.split("=", 1)[1])
                continue
            if t in ("--eval", "--print") or (re.match(r"^-[A-Za-z]*[eEp]$", t) and not cmd.startswith("php")) \
                    or (cmd.startswith("php") and t in ("-r", "-B", "-R", "-E")) or \
                    (cmd == "osascript" and t == "-e"):
                if i < len(rest):
                    codes.append(rest[i])
                    i += 1
                continue
            if cmd.startswith("php") and re.match(r"^-r.+", t):
                codes.append(t[2:])
                continue
            if t in ("-r", "--require", "-l", "-I") and not cmd.startswith("php") and cmd != "perl":
                i += 1
        if codes:
            # osascript joins its -e lines into one script; read them together.
            return "code", ["\n".join(codes)]
        if first is None or first == "-" or first.startswith("/dev/stdin") or first.startswith("/dev/fd/"):
            return "stdin", None
        return "file", None


def verdict(data, policy, note):
    """Return (exit code, message) for one parsed hook payload."""
    tool = data.get("tool_name") or "Bash"
    if tool != "Bash":
        return BLOCK, "%s is a send tool for a mail connector" % tool
    inp = data.get("tool_input")
    cmd = inp.get("command") if isinstance(inp, dict) else None
    if not isinstance(cmd, str):
        raw = json.dumps(data)
        if fallback_hit(raw):
            return BLOCK, "the hook input has no command string and holds a send-capable token"
        return 0, ""
    an = Analyzer(policy, note)
    try:
        if len(cmd) > MAX_INPUT:
            raise Budget()
        reasons = an.analyze(cmd)
    except Budget:
        # Too large or too complex to check in full: fail closed on any send-capable token.
        if fallback_hit(cmd, an.scripts()):
            return BLOCK, "the command is too large or complex to check in full and it holds a send-capable token"
        return 0, ""
    if reasons:
        return BLOCK, "; ".join(dict.fromkeys(reasons))
    return 0, ""


def _unescape_json_text(raw):
    """Decode \\uXXXX escapes in text that is not valid JSON (for the token scan only)."""
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), raw)


def main(argv_):
    policy_path, allow_user, check = None, False, None
    i = 0
    while i < len(argv_):
        a = argv_[i]
        if a == "--policy" and i + 1 < len(argv_):
            policy_path = argv_[i + 1]
            i += 1
        elif a == "--allow-user-policy":
            allow_user = True
        elif a == "--check" and i + 1 < len(argv_):
            check = argv_[i + 1]
            i += 1
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        i += 1
    policy, note = load_policy(policy_path, allow_user)
    message = policy.get("message") or DEFAULT_MESSAGE
    if check is not None:
        data = {"tool_name": "Bash", "tool_input": {"command": check}}
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            if fallback_hit(raw) or fallback_hit(_unescape_json_text(raw)):
                print("email-send-guard: blocked: the hook input is not valid JSON and holds a "
                      "send-capable token. " + message, file=sys.stderr)
                return BLOCK
            return 0
    try:
        code, why = verdict(data, policy, note)
    except RecursionError:
        code, why = BLOCK, "the command nests too deeply to check"
    if check is not None:
        print(("BLOCK: " + why) if code else "allow")
        return code
    if code:
        print("email-send-guard: blocked: %s. %s" % (why, message), file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
