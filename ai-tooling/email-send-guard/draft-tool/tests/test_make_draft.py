"""Offline tests for make_draft.py. A fake Gmail CLI stands in for the real one.

Run: python3 -m unittest discover -s tests   (or: pytest tests)
"""
import base64
import contextlib
import email
import io
import json
import os
import shlex
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
FAKE_CLI = os.path.join(HERE, "fake_gmail_cli.py")
sys.path.insert(0, os.path.dirname(HERE))
import make_draft as D  # noqa: E402

with open(os.path.join(FIXTURES, "reply_body.txt"), encoding="utf-8") as _f:
    BODY = _f.read()


class BuildTest(unittest.TestCase):
    """MIME build only; no CLI calls."""

    def setUp(self):
        self.msg = D.build_message("a@example.com", "b@example.com", "Re: Hi",
                                   "<m2@example.com>", "<m1@example.com>", BODY)
        self.parsed = email.message_from_bytes(self.msg.as_bytes())

    def test_multipart_alternative_with_both_parts(self):
        self.assertEqual(self.parsed.get_content_type(), "multipart/alternative")
        self.assertEqual([p.get_content_type() for p in self.parsed.get_payload()],
                         ["text/plain", "text/html"])

    def test_no_quoted_thread(self):
        h = self.parsed.get_payload()[1].get_payload(decode=True).decode()
        self.assertNotIn("blockquote", h)
        self.assertNotIn("gmail_quote", h)

    def test_threading_headers(self):
        self.assertEqual(self.parsed["In-Reply-To"], "<m2@example.com>")
        self.assertEqual(self.parsed["References"], "<m1@example.com> <m2@example.com>")
        self.assertEqual(self.parsed["Cc"], "b@example.com")

    def test_references_not_duplicated(self):
        m = D.build_message("a@example.com", "", "Re: Hi", "<m2@example.com>",
                            "<m1@example.com> <m2@example.com>", BODY)
        self.assertEqual(m["References"], "<m1@example.com> <m2@example.com>")
        self.assertIsNone(m["Cc"])

    def test_html_paragraphs_list_and_escaping(self):
        h = D.body_html(BODY)
        self.assertIn("<p>Hello there,</p>", h)
        self.assertIn("<ul><li>First option</li><li>Second option</li></ul>", h)
        self.assertIn("<p>Ops &amp; Support team<br>Example Office, Suite 100</p>", h)
        self.assertNotIn("<p></p>", h)

    def test_extra_blank_lines_make_no_empty_paragraphs(self):
        self.assertEqual(D.body_html("A\n\n\n\nB\n"), "<div><p>A</p><p>B</p></div>")

    def test_attachment_makes_mixed_with_alternative_first(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.pdf")
            with open(path, "wb") as f:
                f.write(b"%PDF-1.4 test")
            m = D.build_message("a@example.com", "", "Report", "", "", BODY, [path])
            p = email.message_from_bytes(m.as_bytes())
        self.assertEqual(p.get_content_type(), "multipart/mixed")
        parts = p.get_payload()
        self.assertEqual(parts[0].get_content_type(), "multipart/alternative")
        self.assertEqual([x.get_content_type() for x in parts[0].get_payload()],
                         ["text/plain", "text/html"])
        self.assertEqual(parts[1].get_content_type(), "application/pdf")
        self.assertEqual(parts[1].get_filename(), "report.pdf")
        self.assertEqual(parts[1].get_payload(decode=True), b"%PDF-1.4 test")


class FakeCliTest(unittest.TestCase):
    """End to end through the fake CLI: which calls are made, and the read-back check."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, "state")
        os.mkdir(self.state)
        shutil.copy(os.path.join(FIXTURES, "messages.json"), self.state)
        cli = "%s %s" % (shlex.quote(sys.executable), shlex.quote(FAKE_CLI))
        self.env = mock.patch.dict(os.environ, {"FAKE_GMAIL_STATE": self.state, "MAKE_DRAFT_CLI": cli})
        self.env.start()
        for k in ("FAKE_GMAIL_MUTATE", "FAKE_GMAIL_ERROR"):
            os.environ.pop(k, None)
        self.body = os.path.join(FIXTURES, "reply_body.txt")

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp)

    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = D.main(argv)
        return rc, out.getvalue()

    def calls(self):
        p = os.path.join(self.state, "calls.jsonl")
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def methods(self):
        return [" ".join(c[:4]) for c in self.calls()]

    def stored(self, draft_id="draft-001"):
        with open(os.path.join(self.state, "drafts.json"), encoding="utf-8") as f:
            return json.load(f)[draft_id]["message"]

    def stored_headers(self, draft_id="draft-001"):
        return {h["name"]: h["value"] for h in self.stored(draft_id)["payload"]["headers"]}

    def test_reply_draft_in_thread_and_checked(self):
        rc, out = self.run_main(["--reply-to", "msg-001", "--body-file", self.body, "--cc", "cc@example.com"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.methods(), ["gmail users messages get", "gmail users drafts create",
                                          "gmail users drafts get"])
        res = json.loads(out.strip().splitlines()[-1])
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["thread"], "thread-001")
        h = self.stored_headers()
        self.assertEqual(h["To"], "replies@example.com")  # Reply-To wins over From
        self.assertEqual(h["Subject"], "Re: Review notes")
        self.assertEqual(h["In-Reply-To"], "<m2@example.com>")
        self.assertEqual(h["References"], "<m1@example.com> <m2@example.com>")
        self.assertEqual(h["Cc"], "cc@example.com")

    def test_existing_re_prefix_kept_and_from_used(self):
        rc, out = self.run_main(["--reply-to", "msg-002", "--body-file", self.body])
        self.assertEqual(rc, 0, out)
        h = self.stored_headers()
        self.assertEqual(h["Subject"], "RE: Agenda")
        self.assertEqual(h["To"], "second@example.com")
        self.assertEqual(h["References"], "<m5@example.com>")

    def test_new_email_has_no_thread_headers(self):
        rc, out = self.run_main(["--to", "new@example.com", "--subject", "Hello", "--body-file", self.body])
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.methods(), ["gmail users drafts create", "gmail users drafts get"])
        h = self.stored_headers()
        self.assertNotIn("In-Reply-To", h)
        self.assertNotIn("threadId", json.loads(D_opt(self.calls()[0], "--json"))["message"])

    def test_draft_id_updates_in_place(self):
        rc, out = self.run_main(["--to", "new@example.com", "--subject", "Hello", "--body-file", self.body,
                                 "--draft-id", "draft-077"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.methods(), ["gmail users drafts update", "gmail users drafts get"])
        self.assertEqual(json.loads(out.strip().splitlines()[-1])["draft_id"], "draft-077")

    def test_attachment_goes_up_as_rfc822_file(self):
        path = os.path.join(self.tmp, "notes.pdf")
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4 notes")
        rc, out = self.run_main(["--reply-to", "msg-001", "--body-file", self.body, "--attach", path])
        self.assertEqual(rc, 0, out)
        create = self.calls()[1]
        self.assertEqual(D_opt(create, "--upload-content-type"), "message/rfc822")
        self.assertNotIn("raw", json.loads(D_opt(create, "--json"))["message"])
        self.assertFalse(os.path.exists(D_opt(create, "--upload")), "temp .eml not removed")
        self.assertEqual(json.loads(out.strip().splitlines()[-1])["attachments"], ["notes.pdf"])

    def test_dry_run_calls_nothing(self):
        rc, out = self.run_main(["--reply-to", "msg-001", "--body-file", self.body, "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertEqual(self.calls(), [])
        self.assertIn("<ul><li>First option</li>", out)

    def test_read_back_failures_exit_1(self):
        expected = {"nolabel": "not labeled DRAFT", "thread": "thread thread-other",
                    "quote": "quoted thread", "emdash": "em dash in the body"}
        for mutate, problem in expected.items():
            with self.subTest(mutate=mutate):
                for name in ("drafts.json", "calls.jsonl"):
                    p = os.path.join(self.state, name)
                    if os.path.exists(p):
                        os.unlink(p)
                os.environ["FAKE_GMAIL_MUTATE"] = mutate
                rc, out = self.run_main(["--reply-to", "msg-001", "--body-file", self.body])
                res = json.loads(out.strip().splitlines()[-1])
                self.assertEqual(rc, 1)
                self.assertFalse(res["ok"])
                self.assertTrue(any(problem in x for x in res["problems"]), res["problems"])

    def test_em_dash_in_body_refused_before_any_call(self):
        path = os.path.join(self.tmp, "dash.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("One \u2014 two\n")
        with self.assertRaises(SystemExit) as cm:
            self.run_main(["--to", "new@example.com", "--subject", "Hi", "--body-file", path])
        self.assertIn("em dash", str(cm.exception))
        self.assertEqual(self.calls(), [])
        rc, _ = self.run_main(["--to", "new@example.com", "--subject", "Hi", "--body-file", path,
                               "--allow-em-dash"])
        self.assertEqual(rc, 0)

    def test_cli_error_and_login_hint(self):
        os.environ["FAKE_GMAIL_ERROR"] = "invalid_grant: token expired"
        with self.assertRaises(SystemExit) as cm:
            self.run_main(["--reply-to", "msg-001", "--body-file", self.body])
        self.assertIn("auth login", str(cm.exception))

    def test_missing_message_fails(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_main(["--reply-to", "msg-404", "--body-file", self.body])
        self.assertIn("not found", str(cm.exception))


class NoSendPathTest(unittest.TestCase):
    """The tool cannot send: no option for it, and the CLI wrapper refuses any non-draft method."""

    def test_send_methods_refused_before_the_cli_runs(self):
        with mock.patch.object(D.subprocess, "run") as run:
            for args in (["gmail", "users", "messages", "send"], ["gmail", "users", "drafts", "send"],
                         ["gmail", "+send", "--to", "x@example.com"], ["gmail", "+reply"],
                         ["gmail", "users", "messages", "delete"]):
                with self.subTest(args=args):
                    with self.assertRaises(SystemExit) as cm:
                        D.cli_json(args + ["--params", "{}"])
                    self.assertIn("never sends", str(cm.exception))
            run.assert_not_called()

    def test_cli_value_with_method_words_refused(self):
        # The allowlist checks the method path; the CLI value must not carry another one.
        call = ["gmail", "users", "drafts", "create", "--params", "{}"]
        with mock.patch.object(D.subprocess, "run") as run:
            for spec in ("gws gmail users drafts send", "gws +send", "gws --method send", "gws gmail"):
                with self.subTest(cli=spec):
                    with self.assertRaises(SystemExit) as cm:
                        D.cli_json(call, cli=spec)
                    self.assertIn("never sends", str(cm.exception))
                with self.subTest(env=spec), mock.patch.dict(os.environ, {"MAKE_DRAFT_CLI": spec}):
                    with self.assertRaises(SystemExit):
                        D.cli_json(call)
            run.assert_not_called()

    def test_no_send_option_and_no_prefix_matching(self):
        body = os.path.join(FIXTURES, "reply_body.txt")
        for flag in ("--send", "--sen", "--dry"):
            with self.subTest(flag=flag):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as cm:
                        D.parse_args(["--body-file", body, flag])
                self.assertEqual(cm.exception.code, 2)

    def test_allowlist_has_only_read_and_draft_methods(self):
        for method in D.ALLOWED_CALLS:
            self.assertIn(method[2], ("messages", "drafts"))
            self.assertIn(method[3], ("get", "create", "update"))


def D_opt(argv, name):
    return argv[argv.index(name) + 1]


if __name__ == "__main__":
    unittest.main()
