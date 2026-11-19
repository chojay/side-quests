"""Tests for guard.py: feed hook JSON on stdin, check the exit code (0 = allow, 2 = block).

Run from the project folder:
    python3 -m unittest discover -s tests -v

All addresses are on example.com and every helper name is invented. Nothing here sends
mail: guard.py only reads the command text. Standard library only, Python 3.9 or later.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "..", "guard.py")
POLICY = os.path.join(HERE, "..", "send_policy.example.json")

P = "python3 tools/send_files.py"
R = "python3 tools/report_mailer.py"
OK = "reports@example.com"
OWNER = "owner@example.com"
OTHER = "someone@other.example.com"


def run_raw(raw, policy=POLICY, user_policy=True):
    args = [sys.executable, GUARD, "--policy", policy]
    if user_policy:
        args.append("--allow-user-policy")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(args, input=raw, capture_output=True, text=True, env=env)


def run(cmd, **kw):
    return run_raw(json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}), **kw).returncode


# Base cases (19), invented names and example.com addresses.
PORTED = [
    (P + ' --send --subject "Weekly-report: team A" --body-file b.txt a.pdf', 0, "rule 1, default recipient"),
    ("cd tools && " + P + ' --send --subject "weekly-report: X" --body-file b.txt a.pdf | tail -2', 0,
     "rule 1, with cd and pipe"),
    (P + ' --send --cc ' + OWNER + ' --subject "Weekly-report packet" --body-file b.txt a.pdf', 0, "cc owner"),
    (P + ' --send --to ' + OTHER + ' --subject "Weekly-report: X" --body-file b.txt a.pdf', 2, "other recipient"),
    (P + ' --send --cc bob@other.example.com --subject "Weekly-report: X" --body-file b.txt a.pdf', 2, "other cc"),
    (P + ' --send --subject "Dinner plans" --body-file b.txt a.pdf', 2, "subject without a keyword"),
    (P + ' --send --subject "Weekly-report: X" --body-file b.txt a.pdf && ' + P + ' --send --to x@other.example.com'
     ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "second call to someone else"),
    ("gws gmail +send --to a@example.com --subject hi --body x", 2, "Gmail CLI send"),
    ("gws gmail +send --draft --to a@example.com --subject hi --body x", 0, "Gmail CLI draft"),
    (P + ' --draft --subject "Dinner" --body-file b.txt a.pdf', 0, "helper draft"),
    (P + ' --subject "Dinner" --body-file b.txt a.pdf', 0, "helper dry run (no send flag)"),
    (P + ' --send --cc ' + OWNER + ' --subject "Team digest for you (week 3)" --body-file b.txt a.pdf', 0,
     "rule 2, cc owner"),
    (P + ' --send --subject "Digest picks: tools" --body-file b.txt a.pdf', 0, "rule 2, capital letter"),
    (P + ' --send --to ' + OK + ' --subject "New digests for the team" --body-file b.txt a.pdf', 0,
     "rule 2, explicit --to"),
    (P + ' --send --to ' + OTHER + ' --subject "Team digest" --body-file b.txt a.pdf', 2, "rule 2, other recipient"),
    (P + ' --send --cc bob@other.example.com --subject "Team digest" --body-file b.txt a.pdf', 2, "rule 2, other cc"),
    (P + ' --send --subject "Indigestion notes" --body-file b.txt a.pdf', 2, "keyword only inside a word"),
    (P + ' --send --subject "Predigest notes" --body-file b.txt a.pdf', 2, "keyword as a word ending"),
    (P + ' --send --subject "Team digest" --body-file b.txt a.pdf; ' + P + ' --send --subject "Dinner"'
     ' --body-file b.txt a.pdf', 2, "second call without a keyword"),
]

# Probes added for the public version.
PROBES = [
    # argparse prefixes and repeated options on the SMTP helper
    (P + ' --sen --to ' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "--sen is a prefix of --send"),
    (P + ' --sen --subject "weekly-report" --body-file b.txt a.pdf', 0, "--sen resolved, rule matches"),
    (P + ' --send --t ' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "--t is a prefix of --to"),
    (P + ' --send --c ' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "--c is a prefix of --cc"),
    (P + ' --send --to=' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "--to=VALUE form"),
    (P + ' --send --t=' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "--t=VALUE form"),
    (P + ' --send --to ' + OK + ' --to ' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2,
     "repeated --to (argparse keeps the last)"),
    (P + ' --send --cc ' + OWNER + ' --cc ' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2,
     "repeated --cc"),
    (P + ' --send --to ' + OK + ' --to ' + OK + ' --subject "weekly-report" --body-file b.txt a.pdf', 2,
     "repeated --to, both allowed"),
    (P + ' --send --subject "weekly-report" --subject "Dinner" --body-file b.txt a.pdf', 2, "repeated --subject"),
    (P + ' --s --subject "weekly-report" --body-file b.txt a.pdf', 2, "--s is ambiguous (--send, --subject)"),
    (P + ' --send --bcc ' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "unknown option in a send"),
    (P + ' --send --to ' + OK + ',' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2,
     "two recipients in one --to"),
    (P + ' --send=1 --to ' + OTHER + ' --subject "weekly-report" --body-file b.txt a.pdf', 2, "--send=VALUE"),
    # separators: newline, ; and a flag in a different command
    ("cd tools\ngws gmail +send --to a@example.com --body x", 2, "newline before the send"),
    ("gws gmail +send --to a@example.com --body x\necho --draft", 2, "--draft only in the next line's command"),
    ("gws gmail +send --to a@example.com ; gws gmail +send --draft --to a@example.com", 2,
     "--draft only in the second command"),
    (P + ' --draft --subject x --body-file b.txt a.pdf && ' + P + ' --send --to ' + OTHER +
     ' --subject x --body-file b.txt a.pdf', 2, "send flag in a later command"),
    ("gws gmail +send \\\n  --to a@example.com --body x", 2, "line continuation"),
    ("gws gmail +send \\\n  --draft --to a@example.com --body x", 0, "line continuation with --draft"),
    # the draft flag has to be a real flag, not text inside a value
    ('gws gmail +send --to a@example.com --body "--draft"', 2, "--draft as the body text"),
    ('gws gmail +send --to a@example.com --body "please --draft this"', 2, "--draft inside a quoted body"),
    ("gws gmail +send --to a@example.com --subject -h", 2, "-h as the value of --subject"),
    ("gws gmail +send --html --draft --to a@example.com --body x", 0, "--draft after a known boolean flag"),
    ("gws gmail +reply --message-id abc --body x", 2, "reply helper"),
    ("gws gmail +reply-all --message-id abc --draft --body x", 0, "reply-all as a draft"),
    ("gws gmail +forward --message-id abc --to a@example.com", 2, "forward helper"),
    ("gws gmail +send --help", 0, "help"),
    ("G=gws; $G gmail +send --to a@example.com", 2, "CLI name in a variable"),
    ("gws gmail users messages send --params '{}'", 2, "raw API send"),
    ("gws gmail users drafts send --params '{}'", 2, "raw API send of a draft"),
    ("gws gmail users drafts create --params '{}' --json @draft.json", 0, "raw API draft create"),
    # text that only mentions a send command
    ('echo "use gws gmail +send to mail it"', 0, "quoted text that mentions a send"),
    ("cat > note.md <<'EOF'\nRun gws gmail +send --to a@example.com\nsendmail x\nEOF\necho done", 0,
     "note text in a heredoc"),
    ("git commit -m \"$(cat <<'EOF'\nDocument the gws gmail +send block\nEOF\n)\"", 0, "commit message heredoc"),
    ("grep -rn sendmail docs/", 0, "grep for a sender name"),
    ("# gws gmail +send --to a@example.com\necho ok", 0, "comment line"),
    # raw mail commands and wrappers
    ("sendmail -t < mail.txt", 2, "sendmail"),
    ("/usr/sbin/sendmail a@example.com < m.txt", 2, "sendmail by path"),
    ("sudo -u root msmtp a@example.com < m.txt", 2, "msmtp under sudo"),
    ("env FOO=1 swaks --to a@example.com", 2, "swaks under env"),
    ("printf x | mail -s hi a@example.com", 2, "mail in a pipe"),
    ("timeout 30 sendmail a@example.com < m.txt", 2, "sendmail under timeout"),
    ("echo a@example.com | xargs -n1 sendmail", 2, "sendmail under xargs"),
    ("2>/dev/null sendmail a@example.com", 2, "redirection before the command"),
    ("curl --url smtps://smtp.example.com:465 --mail-rcpt a@example.com -T m.txt", 2, "curl to SMTP"),
    ("curl -s https://example.com/api", 0, "plain curl"),
    # code that the shell hands to an interpreter or a nested shell
    ("python3 -c 'import smtplib; smtplib.SMTP(\"smtp.example.com\")'", 2, "python -c with smtplib"),
    ("python3 -c 'print(1 + 1)'", 0, "harmless python -c"),
    ("python3 - <<'EOF'\nimport smtplib\nEOF", 2, "heredoc into python"),
    ("bash <<'EOF'\ngws gmail +send --to a@example.com\nEOF", 2, "heredoc into bash"),
    ("cat <<'EOF' | bash\ngws gmail +send --to a@example.com\nEOF", 2, "heredoc piped into bash"),
    ('bash -c "gws gmail +send --to a@example.com"', 2, "bash -c"),
    ('echo "gws gmail +send --to a@example.com" | bash', 2, "text piped into bash"),
    ('bash <<< "gws gmail +send --to a@example.com"', 2, "here-string into bash"),
    ('eval "gws gmail +send --to a@example.com"', 2, "eval"),
    ('echo "$(gws gmail +send --to a@example.com)"', 2, "command substitution in double quotes"),
    ("echo `sendmail a@example.com < m.txt`", 2, "backticks"),
    ("osascript -e 'tell application \"Mail\" to send (make new outgoing message)'", 2, "Mail app send"),
    ("echo $((1<<2))\ngws gmail +send --to a@example.com", 2, "arithmetic shift is not a heredoc"),
    ("cat <<EOF\ngws gmail +send --to a@example.com", 2, "unterminated heredoc is checked as commands"),
    # a report sender with send subcommands
    (R + " send --tag t1", 2, "report sender: send subcommand"),
    (R + " send --tag t1 --dry-run", 0, "report sender: send --dry-run"),
    (R + " send --tag t1 --dry", 0, "report sender: --dry is a prefix of --dry-run"),
    (R + " --profile ops send --tag t1", 2, "report sender: global option first"),
    (R + " digest --tag t1", 0, "report sender: digest without a send flag"),
    (R + " digest --tag t1 --send", 2, "report sender: digest --send"),
    (R + " digest --tag t1 --send-o", 2, "report sender: --send-o is a prefix of --send-only"),
    (R + " digest --tag t1 --send --dry-run", 0, "report sender: digest --send --dry-run"),
    (R + " status", 0, "report sender: other subcommand"),
    # unparsable input
    ('gws gmail +send --to "a@example.com', 2, "unbalanced quote with a send token"),
    ('echo "hello', 0, "unbalanced quote without a send token"),
]

# Red-team round 1 (2026-11-18): 102 of these passed the first public draft of guard.py;
# it already blocked the other 4, which pin cases the new scanner must keep.
# The scanner (comments, heredoc ends, $'...', brace lists, ${...}, $( ) quoting) and the
# wider command finder (keywords, wrappers, runners, case-insensitive names) block them now.
REDTEAM = [
    # comments, redirections and here-strings around a safe flag
    ("gws gmail +send --to a@example.com --subject hi --body x # --draft", 2, "commented --draft"),
    ("gws gmail +send --to a@example.com --subject hi --body x > --draft", 2, "--draft as a redirect target"),
    ("gws gmail +send --to a@example.com --subject s --body b 2>--draft", 2, "--draft after 2>"),
    ("gws gmail +send --to a@example.com --subject hi --body x <<< --draft", 2, "--draft as here-string text"),
    ("gws gmail users messages send --params '{\"userId\":\"me\"}' --json '{\"raw\":\"x\"}' # -h", 2,
     "commented -h on a raw API send"),
    ("gws gmail users messages send --params '{\"userId\":\"me\"}' --json '{\"raw\":\"x\"}' > -h", 2,
     "-h as a redirect target on a raw API send"),
    (R + " send --tag x > --dry-run", 2, "report sender: --dry-run as a redirect target"),
    (R + " send --tag x # --dry-run", 2, "report sender: commented --dry-run"),
    (R + " send -- --dry-run", 2, "report sender: --dry-run after --"),
    # comment and heredoc boundaries
    ('"#"; gws gmail +send --to a@example.com --subject hi --body x', 2, "a quoted '#' is not a comment"),
    ("\\# 2>/dev/null; sendmail -t < /tmp/msg.txt", 2, "an escaped '#' is not a comment"),
    ("echo $(true)# ; gws gmail +send --to a@example.com", 2, "'#' right after $( ) is part of the word"),
    ("echo a\\ # ; gws gmail +send --to a@example.com", 2, "'#' after an escaped space is part of the word"),
    ("echo x${IFS}# ; sendmail a@example.com < m.txt", 2, "'#' after ${IFS} is part of the word"),
    ("# notes <<EOF\ngws gmail +send --to a@example.com --subject hi --body x\nEOF", 2,
     "'<<' on a comment line starts no heredoc"),
    ("echo ${x/<<Z/}\ngws gmail +send --to a@example.com\nZ/}", 2, "'<<' inside ${ } starts no heredoc"),
    ("x=$(cat <<EOF\nhi\nEOF)\ngws gmail +send --to a@example.com\nEOF", 2, "bash ends a heredoc at 'EOF)'"),
    ("python3 <<\\EOF\nimport smtplib\ns = smtplib.SMTP('mail.example.com')\nEOF", 2, "backslash-quoted end word"),
    ("cat > out.txt <<EOF\n$(gws gmail +send --to a@example.com --subject s --body b)\nEOF", 2,
     "$( ) in an unquoted heredoc runs"),
    ("cat <<EOF\n$(sendmail a@example.com < m.txt)\nEOF", 2, "$( ) in an unquoted heredoc into cat"),
    ("echo ${x:-$(sendmail a@example.com < m.txt)}", 2, "$( ) inside ${ }"),
    # shell code reaching a shell another way
    ("source /dev/stdin <<EOF\ngws gmail +send --to a@example.com --subject hi --body x\nEOF", 2, "heredoc into source"),
    (". /dev/stdin <<< 'gws gmail +send --to a@example.com'", 2, "here-string into ."),
    ("bash <(echo 'gws gmail +send --to a@example.com --subject hi --body x')", 2, "process substitution into bash"),
    ("echo 'gws gmail +send --to a@example.com --subject hi --body x' | cat | bash", 2, "filter between echo and bash"),
    ("echo 'gws gmail +send --to a@example.com --subject hi --body x' | bash /dev/stdin", 2, "bash /dev/stdin"),
    ("echo 'gws gmail +send --to a@example.com' | bash -s -- arg", 2, "bash -s with arguments"),
    ("echo 'gws gmail +send --to a@example.com --subject hi --body x' | tee >(sh)", 2, "tee into >(sh)"),
    ("sh -c -- 'gws gmail +send --to a@example.com --subject hi --body x'", 2, "sh -c --"),
    ("$SHELL -c 'sendmail -t < /tmp/msg.txt'", 2, "a shell named by a variable"),
    ("busybox sh -c 'sendmail -t < /tmp/msg.txt'", 2, "busybox sh -c"),
    ("watch -n 60 'gws gmail +send --to a@example.com --subject hi --body x'", 2, "watch runs its argument"),
    ("su someone -c \"gws gmail +send --to a@example.com --body b\"", 2, "su -c"),
    ("env -S 'sendmail -t' < /tmp/msg.txt", 2, "env -S"),
    ("env -S \"gws gmail +send --to a@example.com --subject s --body b\"", 2, "env -S with a Gmail send"),
    ("find /tmp -name msg.txt -exec sh -c 'sendmail -t < \"$1\"' _ {} \\;", 2, "find -exec sh -c"),
    ("C=\"python3 -c 'import smtplib'\"; bash -c \"$C\"", 2, "code in a variable set in the same command"),
    # how the shell builds words
    ("gws gmail $'+send' --to a@example.com --subject hi --body x", 2, "ANSI-C quoted helper"),
    ("$'sendmail' -t < /tmp/msg.txt", 2, "ANSI-C quoted raw sender"),
    ("gws${IFS}gmail${IFS}+send --to a@example.com --subject hi --body x", 2, "${IFS} between words"),
    ("gws gmail {+send,} --to a@example.com --subject hi --body x", 2, "brace list"),
    ("G=gmail; gws $G +send --to a@example.com --subject hi --body x", 2, "subcommand in a variable"),
    ("gws $G +send --to a@example.com --subject hi --body x", 2, "unknown variable before +send"),
    ("gws gmail $(echo +send) --to a@example.com", 2, "helper from $( )"),
    ("gws $(echo gmail) +send --to a@example.com", 2, "subcommand from $( )"),
    ("echo $'it\\'s'; gws gmail +se\"\"nd --to a@example.com --subject hi --body x", 2,
     "$'...' that shlex cannot read, then an empty quote pair"),
    ('C="gws gmail +send"; $C --to a@example.com', 2, "whole command in a variable set in the same command"),
    ("python3 -c \"$(cat <<'EOF'\nimport smtplib\nEOF\n)\"", 2, "heredoc text handed to python -c through $( )"),
    # keywords and wrappers in front of the command
    ("if true; then sendmail -t < /tmp/msg.txt; fi", 2, "then"),
    ("{ python3 -c 'import smtplib'; }", 2, "brace group"),
    ("for f in x; do msmtp -t < \"$f\"; done", 2, "do"),
    ("! curl smtps://mail.example.com --mail-rcpt b@example.com -T m.txt", 2, "!"),
    ("f(){ sendmail a@example.com < m.txt; }", 2, "function body"),
    ("function f { sendmail a@example.com < m.txt; }", 2, "function keyword"),
    ("sudo -Eu root sendmail -t < /tmp/msg.txt", 2, "sudo -Eu (value of the last letter)"),
    ("sudo --user root sendmail a@example.com < m.txt", 2, "sudo --user"),
    ("xargs --max-args 1 sendmail < list.txt", 2, "xargs --max-args"),
    ("flock /tmp/l sendmail -t < /tmp/msg.txt", 2, "flock"),
    ("setsid sendmail a@example.com < m.txt", 2, "setsid"),
    ("arch -arm64 sendmail -t < m.txt", 2, "arch"),
    ("docker exec mailbox sendmail a@example.com < m.txt", 2, "docker exec"),
    ("uv run python -c \"import smtplib; smtplib.SMTP('smtp.example.com')\"", 2, "uv run"),
    ("lockf /tmp/x.lock python3 -c \"import smtplib\"", 2, "lockf"),
    ("ssh -p 22 box.example.com sendmail -t < /tmp/msg.txt", 2, "ssh option value before the host"),
    ("MAIL -s hi a@example.com < body.txt", 2, "upper-case command name (case-insensitive file system)"),
    ("Python3 -c \"import smtplib; smtplib.SMTP('smtp.example.com')\"", 2, "upper-case interpreter"),
    ("sendEmail -f x@example.com -t a@example.com -u s -m b -s smtp.example.com", 2, "sendEmail"),
    ("msmtpq a@example.com < m.txt", 2, "msmtpq"),
    ("mpack -s subj report.pdf a@example.com", 2, "mpack"),
    ("himalaya message send < m.eml", 2, "himalaya send"),
    # xargs supplies the words
    ("echo +send | xargs gws gmail", 2, "xargs adds +send"),
    ("echo '+send --to a@example.com --subject s --body b' | xargs gws gmail", 2, "xargs adds the whole tail"),
    ("echo --send --to " + OTHER + " | xargs " + P + " --subject hi --body-file b.txt", 2,
     "xargs adds the helper's send flag"),
    # interpreter code
    ("echo 'import smtplib; smtplib.SMTP(\"mail.example.com\")' | python3 -u", 2, "piped into python3 -u"),
    ("echo 'import smtplib' | python3 -u -", 2, "piped into python3 -u -"),
    ("python3 -Ic 'import smtplib; smtplib.SMTP(\"mail.example.com\")'", 2, "python3 -Ic"),
    ("python3 -Bc \"import smtplib\"", 2, "python3 -Bc"),
    ("awk 'BEGIN{system(\"sendmail -t < /tmp/msg.txt\")}'", 2, "awk system()"),
    ("php -r 'mail(\"b@example.com\", \"hi\", \"x\");'", 2, "php -r mail()"),
    ("deno eval 'import nodemailer from \"npm:nodemailer\"'", 2, "deno eval"),
    ("node --eval=\"require('nodemailer').createTransport({}).sendMail({to:'a@example.com'})\"", 2, "node --eval="),
    ("python3 -c \"from googleapiclient.discovery import build; build('gmail','v1',credentials=c)"
     ".users().messages().send(userId='me', body=b).execute()\"", 2, "Gmail API client in Python"),
    ("node -e \"const {google}=require('googleapis'); google.gmail('v1').users.messages.send("
     "{userId:'me', requestBody:{raw:r}})\"", 2, "Gmail API client in Node"),
    ("osascript -e 'tell application \"Mail\"' -e 'set m to make new outgoing message' -e 'send m' -e 'end tell'", 2,
     "osascript with one -e per line"),
    ("osascript -e 'tell app \"Mail\" to send (make new outgoing message)'", 2, "AppleScript 'app'"),
    ("osascript -l JavaScript -e 'var M=Application(\"Mail\"); var m=M.OutgoingMessage().make(); m.send()'", 2,
     "JXA"),
    ("osascript -e 'tell application \"Microsoft Outlook\" to send (make new outgoing message)'", 2, "Outlook"),
    # HTTP and curl config
    ("curl -X POST -H 'Authorization: Bearer T' https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
     " -d @raw.json", 2, "curl to the Gmail API send URL"),
    ("curl -s --user api:KEY https://api.mailgun.net/v3/example.com/messages -F to=a@example.com -F text=hi", 2,
     "curl to a mail API"),
    ("curl -K - <<EOF\nurl = \"smtps://mail.example.com\"\nmail-rcpt = \"b@example.com\"\nEOF", 2,
     "curl config in a heredoc"),
    # the SMTP helper and the report sender
    (P + " --send --subject weekly-report {--to," + OTHER + "} a.pdf", 2, "brace list hides --to"),
    (P + " --send --subject weekly-report $EXTRA a.pdf", 2, "a variable in a send"),
    (P + " --subject $(echo hi --send) --to " + OTHER, 2, "an unquoted $( ) can add --send"),
    ("python3 send_file?.py --send --to " + OTHER + " --subject x a.pdf", 2, "glob in the helper name"),
    ("python3 tools/send_files.p[y] --send --to " + OTHER + " --subject x a.pdf", 2, "bracket glob in the helper name"),
    ("python3 SEND_FILES.py --send --to " + OTHER + " --subject hi --body-file b.txt", 2, "upper-case helper name"),
    (P + " $'--send' --to " + OTHER + " --subject hi --body-file b.txt", 2, "ANSI-C quoted --send"),
    (P + " --send --subject digest $'--cc' " + OTHER + " --body-file b.txt", 2, "ANSI-C quoted --cc"),
    (P + " {--send,} --to " + OTHER + " --subject hi --body-file b.txt", 2, "brace list makes --send"),
    (P + " --send --subject $'digest\\r\\nBcc: " + OTHER + "' --body-file b.txt", 2, "CR LF in the subject"),
    (P + " --send --subject \"digest\nBcc: " + OTHER + "\" --body-file b.txt", 2, "newline in the subject"),
    (P + " --send --subject digest @args.txt", 2, "argparse @file in a send"),
    ("S=--send; " + P + " $S --to " + OTHER + " --subject x --body-file b.txt a.pdf", 2,
     "send flag in a variable set in the same command"),
    (R + " $'send' --tag x", 2, "report sender: ANSI-C quoted subcommand"),
    (R + " -p work send --to a@example.com", 2, "report sender: unknown option before the subcommand"),
    (R + " digest --tag t $FLAG", 2, "report sender: a variable where a send flag could be"),
]

# Red-team round 2 of 2026-11-19: 80 of these passed the version above (with the REDTEAM
# rows fixed); 2 pin shapes it already blocked (a CR inside the helper word, SES SendEmail
# in the body). Grouped by the part of the guard that missed them.
SEND = "gws gmail +send --to a@example.com --subject s --body b"
PASS2 = [
    # git
    ("git send-email --to a@example.com --confirm=never 0001-fix.patch", 2, "git send-email"),
    ("git -c alias.s='!" + SEND + "' s", 2, "git -c alias with a '!' shell command"),
    ("PAGER='sendmail -t < /tmp/m.txt' git log", 2, "a command in PAGER"),
    # words the shell builds
    ("gws ${G:-gmail} +send --to a@example.com --subject s --body b", 2, "${G:-gmail} default"),
    ("gws gm$9ail +send --to a@example.com --subject s --body b", 2, "an empty $9 inside the word"),
    ("S=' '; gws${S}gmail${S}+send --to a@example.com --subject s --body b", 2,
     "a same-command variable inside a word splits"),
    ("IFS=,; X=gws,gmail,+send; $X --to a@example.com --subject s --body b", 2, "a same-command IFS"),
    ("sendmail${IFS:0:1}-t < /tmp/m.txt", 2, "${IFS:0:1}"),
    ("gws gmail +sen{d..d} --to a@example.com --subject s --body b", 2, "a {d..d} sequence"),
    ("touch ./+send && gws gmail +sen? --to a@example.com --subject s --body b", 2, "a glob helper name"),
    ("gws gmail +send\r --to a@example.com --subject s --body b", 2, "a CR inside the helper word"),
    ("gws gmail +send --to a@example.com --subject s --body b\r--draft", 2, "bash does not split on CR"),
    (R + " send --tag x\r--dry-run", 2, "report sender: CR before --dry-run"),
    ("gws gmail +s${x}end --to a@example.com --subject s --body b\\", 2, "a trailing backslash"),
    ("$(echo gws gmail +send) --to a@example.com --subject s --body b", 2, "$(echo ...) as the command"),
    # raw API sends
    ("gws gmail users messages sen${X}d --params '{\"userId\":\"me\"}' --json @raw.json", 2,
     "a variable inside 'send'"),
    ("gws gmail users messages --format json send --params '{\"userId\":\"me\"}' --json @raw.json", 2,
     "a flag between 'messages' and 'send'"),
    # the SMTP helper
    ("touch -- --cc=x@other.example.com && " + P + " --send --subject weekly-report --body-file b.txt *", 2,
     "a glob that can match a file named like an option"),
    # HTTP mail APIs
    ("curl -X POST -H 'Authorization: Bearer T' -d @raw.json https://www.googleapis.com/gmail/v1/users/me/messages/send",
     2, "the Gmail API on www.googleapis.com"),
    ("curl -X POST -H 'Authorization: Bearer T' -d @raw.json"
     " https://www.googleapis.com/upload/gmail/v1/users/me/messages/send", 2, "the Gmail upload host"),
    ("curl -X POST -H 'Authorization: Bearer T' https://graph.microsoft.com/v1.0/me/messages/AAMk123/send", 2,
     "Microsoft Graph draft send"),
    ("curl -X POST -H 'Authorization: Bearer T' https://graph.microsoft.com/v1.0/me/messages/AAMk123/replyAll", 2,
     "Microsoft Graph replyAll"),
    ("curl -X POST -H 'Authorization: Bearer T' -d @raw.json"
     " 'https://gmail.googleapis.com/gmail/v1/users/me/messages/{send}'", 2, "curl URL glob"),
    ("curl -X POST -H 'Authorization: Bearer T' -d @raw.json"
     " 'https://gmail.googleapis.com/gmail/v1/users/me/messages/sen%64'", 2, "a percent escape in the URL"),
    ("curl -X POST -d 'Action=SendEmail&Source=a@example.com' https://email.us-east-1.amazonaws.com/", 2,
     "SES SendEmail in the body"),
    ("aws sesv2 send-email --from-email-address a@example.com --content file://m.json", 2, "aws sesv2 send-email"),
    # heredocs whose reader is not a plain command
    ("<<'EOF' bash\n" + SEND + "\nEOF", 2, "redirect before the command"),
    ("exec 3<<'EOF'\n" + SEND + "\nEOF\nbash <&3", 2, "exec 3<<"),
    ("{ bash; } <<'EOF'\n" + SEND + "\nEOF", 2, "a brace group"),
    ("while read -r l; do eval \"$l\"; done <<'EOF'\n" + SEND + "\nEOF", 2, "a loop"),
    ("cat <<'EOF' | tee >(bash) >/dev/null\n" + SEND + "\nEOF", 2, "tee into >(bash)"),
    ("bash < <(cat <<'EOF'\n" + SEND + "\nEOF\n)", 2, "a heredoc inside <( )"),
    # ssh, at and piped code
    ("ssh box.example.com <<'EOF'\nsendmail -t < /tmp/m.txt\nEOF", 2, "ssh with no remote command"),
    ("echo 'sendmail -t < /tmp/m.txt' | ssh box.example.com", 2, "piped into ssh"),
    ("ssh box.example.com -T sendmail -t < /tmp/m.txt", 2, "an ssh option after the host"),
    ("ssh box.example.com sh <<'EOF'\nsendmail -t < /tmp/m.txt\nEOF", 2, "heredoc into a remote sh"),
    ("echo '" + SEND + "' | bash -c bash", 2, "piped into bash -c bash"),
    ("echo 'import smtplib; smtplib.SMTP(\"mail.example.com\")' | python3 -c 'import sys; exec(sys.stdin.read())'",
     2, "piped into python3 -c exec(stdin)"),
    ("echo '" + SEND + "' | bash -c 'eval \"$(cat)\"'", 2, "piped into eval $(cat)"),
    ("echo 'sendmail -t < /tmp/m.txt' | xargs -0 bash -c", 2, "xargs bash -c takes its input as code"),
    ("echo sendmail | xargs -I{} sh -c '{} -t < /tmp/m.txt'", 2, "xargs -I placeholder in sh -c"),
    ("echo '" + SEND + "' | at now", 2, "piped into at"),
    ("at now <<'EOF'\nsendmail -t < /tmp/m.txt\nEOF", 2, "heredoc into at"),
    ("batch <<< 'sendmail -t < /tmp/m.txt'", 2, "here-string into batch"),
    # code stored for later: trap, alias, hash, arithmetic and prompt expansion
    ("trap '" + SEND + "' EXIT", 2, "trap"),
    ("shopt -s expand_aliases\nalias g='gws gmail +send'\ng --to a@example.com --subject s --body b", 2, "alias"),
    ("hash -p /usr/sbin/sendmail m; m -t < /tmp/m.txt", 2, "hash -p"),
    ("x='a[$(sendmail -t < /tmp/m.txt)]'; echo $((x))", 2, "$( ) in an array subscript, run by $(( ))"),
    ("echo $(( \"$(" + SEND + " >/dev/null; echo 1)\" ))", 2, "$( ) inside $(( ))"),
    ("x='$(" + SEND + ")'; echo \"${x@P}\"", 2, "prompt expansion ${x@P}"),
    ("echo $[1<<2]\n" + SEND + "\n2]", 2, "'<<' inside $[ ] starts no heredoc"),
    ("(( x = 1 +\n 2 << 3 ))\n" + SEND + "\n3", 2, "'<<' inside a multi-line (( ))"),
    # the command word
    ("${X:-sendmail} -t < /tmp/m.txt", 2, "${X:-sendmail} as the command"),
    ("${SHELL:-sh} -c 'sendmail -t < /tmp/m.txt'", 2, "${SHELL:-sh} -c"),
    ("$0 -c 'sendmail -t < /tmp/m.txt'", 2, "$0 -c"),
    ("/usr/sbin/sendmai? -t < /tmp/m.txt", 2, "a glob command word"),
    ("/usr/bin/python[3] -c 'import smtplib; smtplib.SMTP(\"mail.example.com\")'", 2, "a bracket glob interpreter"),
    ("coproc M { sendmail -t < /tmp/m.txt; }", 2, "coproc NAME"),
    ("a[0]=1 sendmail -t < /tmp/m.txt", 2, "an array assignment before the command"),
    ("timeout 1e3 sendmail -t < /tmp/m.txt", 2, "timeout 1e3"),
    ("timeout inf sendmail -t < /tmp/m.txt", 2, "timeout inf"),
    ("eval -- 'sendmail -t < /tmp/m.txt'", 2, "eval --"),
    ("eval \"$(printf '" + SEND + "')\"", 2, "eval of a printf literal"),
    # zsh forms
    ("=sendmail -t < /tmp/m.txt", 2, "zsh =cmd"),
    ("noglob python3 -c 'import smtplib; smtplib.SMTP(\"mail.example.com\")'", 2, "zsh noglob"),
    ("repeat 1 sendmail -t < /tmp/m.txt", 2, "zsh repeat"),
    ("echo /etc/hosts(e:'" + SEND + "':)", 2, "zsh glob qualifier e:...:"),
    ("x='$(sendmail -t < /tmp/m.txt)'; echo ${(e)x}", 2, "zsh ${(e)x}"),
    ("zsh -c 'hash m=/usr/sbin/sendmail; m -t < /tmp/m.txt'", 2, "zsh hash NAME=PATH"),
    # wrappers and shells
    ("env -vS'sendmail -t' < /tmp/m.txt", 2, "env -vS cluster"),
    ("fish --command 'sendmail -t < /tmp/m.txt'", 2, "fish --command"),
    ("fish --command='sendmail -t < /tmp/m.txt'", 2, "fish --command="),
    ("fish -C 'sendmail -t < /tmp/m.txt'", 2, "fish -C"),
    # interpreters
    ("python3 -m smtplib < /tmp/m.txt", 2, "python3 -m smtplib"),
    ("python3 -um smtplib < /tmp/m.txt", 2, "python3 -um smtplib"),
    ("python3 -X dev -m smtplib < /tmp/m.txt", 2, "python3 -X dev -m smtplib"),
    ("C='import smtplib; smtplib.SMTP(\"mail.example.com\")'; python3 -c \"$C\"", 2,
     "python code in a same-command variable"),
    ("python3 -c \"import subprocess; subprocess.run(['gws','gmail','+send','--to','a@example.com',"
     "'--subject','s','--body','b']); print('--draft')\"", 2, "--draft outside the call in inline code"),
    ("python3 -c \"import os; os.system('mail -s hi a@example.com < /tmp/m.txt')\"", 2, "mail in os.system"),
    ("awk 'BEGIN{print \"hi\" | \"mail -s hi a@example.com\"}'", 2, "awk pipe into mail"),
    ("ipython -c \"import smtplib; smtplib.SMTP('mail.example.com')\"", 2, "ipython -c"),
    ("osascript -e 'tell application \"Mail.app\" to send (make new outgoing message)'", 2, "Mail.app"),
]

# Everyday commands checked against the round-2 rules (none of them sends).
EVERYDAY = [
    ("while read -r f; do echo \"$f\"; done <<'EOF'\na.txt\nb.txt\nEOF", 0, "a loop over a heredoc list"),
    ("git -c user.name=x commit -m 'docs: the guard blocks gws gmail +send'", 0, "git -c and a message"),
    ("git log --oneline -5 && git status", 0, "git log"),
    ("docker run --rm alpine echo hi", 0, "docker run"),
    ("timeout 5 ls -la", 0, "timeout"),
    ("ssh box.example.com ls -la /var/log", 0, "ssh with a command"),
    ("alias ll='ls -la'", 0, "alias"),
    ("trap 'rm -f \"$tmp\"' EXIT", 0, "trap"),
    ("curl -s 'https://www.googleapis.com/gmail/v1/users/me/messages?q=from:x'", 0, "Gmail API list"),
    ("aws ses get-send-quota", 0, "aws ses read"),
    ("x='$(date)'; echo \"$x\"", 0, "a harmless $( ) in a value"),
    ("python3 -m pytest -q", 0, "python3 -m pytest"),
    ("npm exec -- eslint .", 0, "npm exec"),
    ("kubectl exec pod-1 -- ls /", 0, "kubectl exec"),
    ("cat <<'EOF' > notes.md\nRun gws gmail +send --to a@example.com to send it.\nEOF\nls | bash -c 'wc -l'", 0,
     "note text, and bash -c in a later command"),
    ("(( n = 1 << 3 )); echo $n", 0, "a shift in (( ))"),
    ("echo $[2*3]", 0, "$[ ] arithmetic"),
    ("ls *.py | xargs -I{} wc -l {}", 0, "xargs -I"),
    ("find . -name '*.md' | xargs grep -l sendmail", 0, "xargs grep for a sender name"),
    (P + " --subject weekly-report --body-file b.txt reports/*.pdf", 0, "helper dry run with a path glob"),
    (P + " --send --subject weekly-report --body-file b.txt ./*.pdf", 0, "helper send with a ./ glob"),
    ("<<'EOF' cat > out.txt\ngws gmail +send --to a@example.com\nEOF", 0, "redirect first into cat"),
    ("uv pip install mail-parser", 0, "uv pip install"),
    ("tmux new-session -d -s build 'make all'", 0, "tmux new-session"),
    ("screen -dmS worker python3 job.py", 0, "screen -dmS"),
    ("osascript -e 'tell application \"Mail\" to get unread count of inbox'", 0, "Mail app read"),
    ("node -e \"console.log('mail sent')\"", 0, "the word mail in code"),
    ("python3 -c \"import email; print(email.message_from_string('x'))\"", 0, "the email module"),
    ("declare -a arr=(1 2 3); arr[0]=5; echo ${arr[@]}", 0, "arrays"),
    ("env -i PATH=/usr/bin ls", 0, "env -i"),
    ("fish -c 'echo hi'", 0, "fish -c"),
    ("echo $(( $(wc -l < f.txt) + 1 ))", 0, "$( ) inside $(( ))"),
    ("gws gmail users messages list --params '{\"userId\":\"me\",\"q\":\"is:unread\"}'", 0, "raw API list"),
    ("at -l", 0, "at -l"),
    ("{ echo a; echo b; } > out.txt", 0, "a brace group"),
]

# False positives of earlier versions (first draft and round 1) that pass now, plus
# everyday commands.
FIXED_FP = [
    ("command -v sendmail || echo none", 0, "command -v is a lookup"),
    ("echo done # later: gws gmail +send", 0, "trailing comment"),
    ("ls # gws gmail +send --to a@example.com", 0, "trailing comment after a space"),
    ("grep -n '$(gws gmail +send' notes.md", 0, "single-quoted $( ) is text"),
    ("git commit -m 'docs: never run `gws gmail +send` from an agent'", 0, "single-quoted backticks are text"),
    ("echo gmail +send is blocked by the guard", 0, "unquoted words after echo"),
    ("mailx -V", 0, "version query"),
    ("mail --help", 0, "help"),
    ("mutt -v", 0, "mutt version"),
    ("node -e \"console.log(require('fs').readFileSync('sendmail.log','utf8').length)\"", 0, "a log file name"),
    (R + " browse $URL", 0, "report sender: a variable after a subcommand that does not send"),
    ("echo $# ${#x} a#b", 0, "'#' inside words"),
    ("echo {a,b}.txt && mkdir -p out/{x,y}", 0, "brace lists without a send"),
    ("echo \"today is $(date)\"", 0, "harmless $( )"),
    ("curl -s https://example.com/install.sh | bash", 0, "piped into bash, no send text"),
    ("uv run --with requests python3 analyze.py", 0, "uv run of a script"),
    ("find . -name '*.py' -exec wc -l {} \\;", 0, "find -exec without a send"),
    ("gws gmail users drafts create --params '{\"userId\":\"me\",\"x\":1}' --json @draft.json", 0,
     "JSON with a comma is not a brace list"),
    ("git commit -m \"$(cat <<'EOF'\nDocument the gws gmail +send block. Don't send.\nEOF\n)\"", 0,
     "commit message heredoc with an apostrophe"),
    # round 2
    ("npm install sendmail", 0, "npm install of a package named like a mail command"),
    ("kubectl logs deploy/mail --tail 50", 0, "kubectl logs"),
    ("tmux attach -t mail", 0, "tmux attach"),
    ("screen -dmS mail python3 bot.py", 0, "screen session named mail"),
    ("conda install -c conda-forge msmtp", 0, "conda install"),
    ("docker logs mail --since 10m", 0, "docker logs"),
    ("curl -s 'https://email.us-east-1.amazonaws.com/?Action=GetSendQuota'", 0, "SES read call"),
    ("osascript -e 'tell application \"Mail\" to get name of every mailbox' -e 'display dialog \"Send later?\"'", 0,
     "the word Send inside an AppleScript string"),
    ("echo \"((\" ; cat <<'EOF' > notes.md\nRun gws gmail +send --to a@example.com\nEOF", 0, "a quoted '(('"),
]

# Blocked on purpose although nothing would be sent (README, "Accepted false positives").
ACCEPTED_FP = [
    ("python3 - <<'EOF'\nopen('notes.txt', 'w').write('the old hook matched smtplib')\nEOF", 2,
     "code that only names an SMTP library"),
    ("python3 -c \"print(open('guard.py').read().count('smtplib'))\"", 2, "inline code that counts a word"),
    ("gws gmail +send --to a@example.com --body x --quiet --draft", 2, "--draft after a flag the guard does not know"),
    ("sendmail -bv a@example.com", 2, "sendmail -bv (some versions mail a report)"),
    ("cat > f.md <<'EOF'\n  gws gmail +send --to a@example.com\n  EOF", 2, "indented end word without <<-"),
    (P + " --subject \"$SUBJ\" --body-file b.txt a.pdf", 2, "a helper dry run with a variable"),
    ("docker run --name mail alpine true", 2, "a runner whose option value is a mail command name"),
    ("tmux new -s mail 'make all'", 2, "a tmux session named like a mail command"),
    ("while read -r l; do echo \"$l\"; done <<'EOF'\ngws gmail +send --to a@example.com\nEOF", 2,
     "a heredoc into a loop is checked as commands"),
    ("curl -s 'https://gmail.googleapis.com/gmail/v1/users/me/messages/abc%3D'", 2,
     "a percent escape in a Gmail API message URL"),
    ("git -c user.name=mail commit -m x", 2, "a git -c value that is a mail command name"),
    (P + " --send --subject weekly-report --body-file b.txt *.pdf", 2, "a helper send with a bare glob"),
]

# What still passes. These tests pin the documented gaps (README, "What it cannot see").
GAPS = [
    ("python3 -c \"__import__('smtp' + 'lib')\"", 0, "obfuscated library name in inline code"),
    ("python3 /tmp/mailer.py", 0, "a script file the agent wrote earlier"),
    ("python3 -m tools.send_files --send --to " + OTHER + " --subject x --body-file b.txt a.pdf", 0,
     "helper run as a module"),
    ("cat > /tmp/run.sh <<'EOF'\ngws gmail +send --to a@example.com\nEOF\nbash /tmp/run.sh", 0,
     "a script written by a heredoc, then run"),
    ("printf 'gws gmail +%s --to a@example.com' send | bash", 0, "code built from pieces at run time"),
    ("ruby -e 'require \"mail\"; Mail.deliver { to \"a@example.com\"; body \"hi\" }'", 0,
     "a mail library the guard does not know"),
    ("python3 -c \"import socket; s=socket.create_connection(('smtp.example.com',25))\"", 0,
     "SMTP spoken over a plain socket"),
    ("cp tools/send_files.py sf.py && python3 sf.py --send --to " + OTHER + " --subject x", 0,
     "a renamed copy of the helper"),
    ("shortcuts run 'Send Email'", 0, "an app automation that sends"),
    ("runjob --name x -- sendmail a@example.com < m.txt", 0, "a wrapper the guard does not know"),
    ("at -f /tmp/job.sh now", 0, "a job file handed to at"),
]

# Audit after round 2: a command variable passed as an argument of env, sudo or timeout was
# skipped without the checks a prefix assignment gets. Each send row here passed then.
AUDIT = [
    ("env GIT_SSH_COMMAND='sendmail -t < /tmp/m.txt' git fetch origin", 2, "GIT_SSH_COMMAND after env"),
    ("env 'GIT_SSH_COMMAND=sendmail -t < /tmp/m.txt' git fetch origin", 2, "quoted assignment after env"),
    ("sudo GIT_SSH_COMMAND='sendmail -t < /tmp/m.txt' git fetch origin", 2, "GIT_SSH_COMMAND after sudo"),
    ("env -i GIT_SSH_COMMAND='sendmail -t < /tmp/m.txt' git fetch origin", 2, "GIT_SSH_COMMAND after env -i"),
    ("timeout 30 env GIT_SSH_COMMAND='sendmail -t < /tmp/m.txt' git fetch origin", 2,
     "GIT_SSH_COMMAND after timeout and env"),
    ("env PAGER='sendmail -t < /tmp/m.txt' git log", 2, "PAGER after env"),
    ("env EDITOR='sendmail -t < /tmp/m.txt' git commit", 2, "EDITOR after env"),
    ("env PAGER=cat git log", 0, "a plain PAGER after env"),
    ("sudo GIT_SSH_COMMAND='ssh -i key' git fetch origin", 0, "a plain GIT_SSH_COMMAND after sudo"),
]


class Cases(unittest.TestCase):
    def check(self, table):
        bad = []
        for cmd, want, label in table:
            got = run(cmd)
            if got != want:
                bad.append("%s: exit %d, want %d\n    %r" % (label, got, want, cmd))
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_ported(self):
        self.assertEqual(len(PORTED), 19)
        self.check(PORTED)

    def test_probes(self):
        self.check(PROBES)

    def test_redteam(self):
        self.check(REDTEAM)

    def test_redteam_round_2(self):
        self.check(PASS2)

    def test_everyday_commands(self):
        self.check(EVERYDAY)

    def test_fixed_false_positives(self):
        self.check(FIXED_FP)

    def test_accepted_false_positives(self):
        self.check(ACCEPTED_FP)

    def test_gaps(self):
        self.check(GAPS)

    def test_audit_after_round_2(self):
        self.check(AUDIT)


class Input(unittest.TestCase):
    def test_empty_stdin(self):
        self.assertEqual(run_raw("").returncode, 0)

    def test_not_json_with_send_token(self):
        self.assertEqual(run_raw("gws gmail +send --to a@example.com").returncode, 2)

    def test_not_json_without_send_token(self):
        self.assertEqual(run_raw("hello there").returncode, 0)

    def test_json_without_command(self):
        self.assertEqual(run_raw(json.dumps({"tool_name": "Bash", "tool_input": {}})).returncode, 0)

    def test_command_not_a_string_with_send_token(self):
        raw = json.dumps({"tool_name": "Bash", "tool_input": {"command": ["gws", "gmail", "+send"]}})
        self.assertEqual(run_raw(raw).returncode, 2)

    def test_connector_send_tool(self):
        raw = json.dumps({"tool_name": "mcp__mail__send_message", "tool_input": {"to": "a@example.com"}})
        res = run_raw(raw)
        self.assertEqual(res.returncode, 2)
        self.assertIn("email-send-guard: blocked", res.stderr)

    def test_block_message_on_stderr(self):
        res = run_raw(json.dumps({"tool_name": "Bash", "tool_input": {"command": "sendmail a@example.com"}}))
        self.assertEqual(res.returncode, 2)
        self.assertIn("Save a draft", res.stderr)


class Policy(unittest.TestCase):
    ALLOWED = P + ' --send --subject "Weekly-report: team A" --body-file b.txt a.pdf'

    def test_user_owned_policy_rules_ignored_by_default(self):
        # The example file is owned by the test user, so without --allow-user-policy its
        # allow rules do not count and the send is blocked.
        res = run_raw(json.dumps({"tool_name": "Bash", "tool_input": {"command": self.ALLOWED}}),
                      user_policy=False)
        self.assertEqual(res.returncode, 2)
        self.assertIn("not root-owned", res.stderr)

    def test_invalid_policy_blocks_send_flags(self):
        d = tempfile.mkdtemp()
        try:
            bad = os.path.join(d, "send_policy.json")
            with open(bad, "w") as f:
                f.write("{not json")
            self.assertEqual(run(self.ALLOWED, policy=bad), 2)
            self.assertEqual(run("ls -la", policy=bad), 0)
            # the helper's name is unknown then, so any spelling argparse reads as --send blocks
            for flag in ("--sen", "--se", "--send-o"):
                self.assertEqual(run(P + " " + flag + " --to " + OTHER + " --subject x --body-file b.txt",
                                     policy=bad), 2, flag)
            self.assertEqual(run("ls -la --sort=size", policy=bad), 0)
        finally:
            shutil.rmtree(d)

    def test_flat_helper_entry_blocks_send_flags(self):
        # One helper entry saved as the whole policy, without its smtp_helpers list: the
        # helper would be unknown and its sends would pass, so the policy counts as invalid.
        with open(POLICY, encoding="utf-8") as f:
            entry = json.load(f)["smtp_helpers"][0]
        d = tempfile.mkdtemp()
        try:
            flat = os.path.join(d, "send_policy.json")
            with open(flat, "w") as f:
                json.dump(entry, f)
            self.assertEqual(run(P + " --send --to " + OTHER + " --subject x --body-file b.txt a.pdf",
                                 policy=flat), 2)
            self.assertEqual(run(self.ALLOWED, policy=flat), 2)
            self.assertEqual(run("ls -la", policy=flat), 0)
        finally:
            shutil.rmtree(d)

    def test_missing_policy_blocks_gmail_and_raw(self):
        missing = os.path.join(tempfile.gettempdir(), "no-such-dir-email-send-guard", "p.json")
        self.assertEqual(run("gws gmail +send --to a@example.com", policy=missing), 2)
        self.assertEqual(run("ls", policy=missing), 0)

    def test_no_unlock_file(self):
        # A flag file next to the guard or in the home folder changes nothing.
        d = tempfile.mkdtemp()
        try:
            for name in (".unlock", "allow_send.flag", "DISABLE_GUARD"):
                open(os.path.join(d, name), "w").close()
            env_home = dict(os.environ, HOME=d, PYTHONDONTWRITEBYTECODE="1")
            raw = json.dumps({"tool_name": "Bash", "tool_input": {"command": "gws gmail +send --to a@example.com"}})
            res = subprocess.run([sys.executable, GUARD, "--policy", POLICY, "--allow-user-policy"],
                                 input=raw, capture_output=True, text=True, env=env_home, cwd=d)
            self.assertEqual(res.returncode, 2)
        finally:
            shutil.rmtree(d)


class Limits(unittest.TestCase):
    """A command past the work limits is blocked when it holds a send-capable token, and the
    check stays well under the 10 s hook timeout of settings.example.json."""

    def timed(self, cmd):
        t = time.time()
        code = run(cmd)
        return code, time.time() - t

    def test_many_xargs_segments(self):
        code, dt = self.timed("echo a" + " | xargs echo" * 3000 + "\n" + SEND)
        self.assertEqual(code, 2)
        self.assertLess(dt, 5)
        code, dt = self.timed("echo a" + " | xargs echo" * 900 + "\n" + SEND)
        self.assertEqual(code, 2)
        self.assertLess(dt, 5)

    def test_many_heredocs(self):
        code, dt = self.timed("cat <<E\nE\n" * 20000 + SEND)
        self.assertEqual(code, 2)
        self.assertLess(dt, 5)
        code, dt = self.timed("cat <<E\nE\n" * 20000)
        self.assertEqual(code, 0)
        self.assertLess(dt, 5)

    def test_many_pipes_into_bash(self):
        code, dt = self.timed("echo x" + " | bash" * 900 + "\n" + SEND)
        self.assertEqual(code, 2)
        self.assertLess(dt, 5)

    # Ways to push a command onto the fail-closed path: past the size cap, past the segment
    # cap, or a later line with an unbalanced quote (bash still runs the lines before it).
    PADS = (
        ("long comment", lambda c: "# " + "x" * 100001 + "\n" + c),
        ("many segments", lambda c: "true; " * 2100 + c),
        ("broken quote after", lambda c: c + "\necho \"unclosed"),
    )
    # Shapes that the first fail-closed token list did not hold.
    FALLBACK_SHAPES = [
        "curl -X POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send -d @m.json",
        "curl -s https://api.mailgun.net/v3/example.com/messages -F to=a@example.com",
        "node -e \"require('nodemailer')\"",
        "gws gmail +sen{d..d} --to a@example.com --subject s --body b",
        "/usr/sbin/sendmai? a@example.com < m.txt",
        "gws gmail users messages sen${X}d --params x",
    ]

    def test_padded_or_broken_send_shapes_still_block(self):
        bad = []
        shapes = [c for c, want, _ in REDTEAM + PASS2 if want == 2] + self.FALLBACK_SHAPES
        for cmd in shapes:
            self.assertEqual(run(cmd), 2, cmd)
            for name, pad in self.PADS:
                if run(pad(cmd)) != 2:
                    bad.append("%s: %r" % (name, cmd))
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_padded_or_broken_plain_commands_pass(self):
        for name, pad in self.PADS:
            self.assertEqual(run(pad("ls -la")), 0, name)


class Settings(unittest.TestCase):
    def test_connector_matcher(self):
        with open(os.path.join(HERE, "..", "settings.example.json")) as f:
            matcher = json.load(f)["hooks"]["PreToolUse"][1]["matcher"]
        for name in ("mcp__claude_ai_Gmail__send_message", "mcp__google_workspace__send_gmail_message",
                     "mcp__gmail__gmail_send_email", "mcp__mail__reply_all", "mcp__outlook__forward_message"):
            self.assertTrue(re.search(matcher, name), name)
        for name in ("mcp__claude_ai_Gmail__create_draft", "mcp__claude_ai_Gmail__search_threads",
                     "mcp__slack__send_message"):
            self.assertFalse(re.search(matcher, name), name)


class CheckMode(unittest.TestCase):
    def test_check_flag(self):
        res = subprocess.run([sys.executable, GUARD, "--policy", POLICY, "--allow-user-policy", "--check",
                              "gws gmail +send --to a@example.com"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        self.assertTrue(res.stdout.startswith("BLOCK"))


if __name__ == "__main__":
    unittest.main()
