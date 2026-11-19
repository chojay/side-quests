"""Context-window tests with a fake Ollama client (no Ollama, no PDFs needed).

Run from the project folder:
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
(pytest also collects these.) Standard library only; works on Python 3.9+.
"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

import ollama_paper_summarizer as ops  # noqa: E402


class FakeClient(object):
    """Stands in for ollama.AsyncClient.

    It records every call and answers like a server whose real context length is
    `server_ctx` tokens at `chars_per_token`: a longer prompt is cut silently
    and prompt_eval_count reports only what was kept, which is how a server
    with too small a context behaves.
    """

    def __init__(self, server_ctx=None, chars_per_token=4.0, report_eval=True,
                 done_reason="stop", as_object=False):
        self.calls = []
        self.server_ctx = server_ctx
        self.chars_per_token = chars_per_token
        self.report_eval = report_eval
        self.done_reason = done_reason
        self.as_object = as_object

    async def generate(self, model, system, prompt, options=None):
        self.calls.append({"model": model, "system": system, "prompt": prompt,
                           "options": options})
        tokens = int((len(system) + len(prompt)) / self.chars_per_token)
        ctx = self.server_ctx
        if ctx is None and options:
            ctx = options.get("num_ctx")
        if ctx is not None:
            tokens = min(tokens, ctx)
        resp = {"response": "Key Technical Findings\n\nA finding.", "done_reason": self.done_reason}
        if self.report_eval:
            resp["prompt_eval_count"] = tokens
        if self.as_object:
            obj = type("Resp", (), {})()
            for k, v in resp.items():
                setattr(obj, k, v)
            return obj
        return resp


def run(coro):
    return asyncio.run(coro)


def quiet(_msg):
    pass


class ContextFitTests(unittest.TestCase):

    def setUp(self):
        self.settings = ops.ContextSettings(num_ctx=4096, reserve_tokens=512,
                                            on_overflow="truncate")

    def test_num_ctx_is_always_sent(self):
        client = FakeClient()
        summary, info = run(ops.generate_summary(client, "short paper text", "m",
                                                 self.settings, log=quiet))
        self.assertEqual(info["status"], "fit")
        self.assertTrue(summary)
        self.assertEqual(client.calls[0]["options"], {"num_ctx": 4096, "num_predict": 512})

    def test_long_paper_is_cut_on_purpose_with_marker(self):
        text = "x" * 100000
        client = FakeClient()
        summary, info = run(ops.generate_summary(client, text, "m", self.settings, log=quiet))
        self.assertEqual(info["status"], "truncated")
        self.assertLess(info["kept"], len(text))
        sent = client.calls[0]["prompt"]
        self.assertIn("[TRUNCATED BY THE SUMMARIZER", sent)
        self.assertIn("of 100000 characters", sent)
        # the cut prompt fits the budget by the conservative estimate
        est = ops.estimate_tokens(len(ops.SYSTEM_PROMPT) + len(sent), self.settings.chars_per_token)
        self.assertLessEqual(est, self.settings.prompt_budget_tokens)
        # and the saved summary says it is partial
        self.assertTrue(summary.startswith("> Note: this summary covers only the first"))

    def test_long_paper_is_skipped_with_reason(self):
        settings = ops.ContextSettings(num_ctx=4096, reserve_tokens=512, on_overflow="skip")
        logged = []
        client = FakeClient()
        summary, info = run(ops.generate_summary(client, "x" * 100000, "m", settings,
                                                 name="long.pdf", log=logged.append))
        self.assertIsNone(summary)
        self.assertEqual(info["status"], "skip")
        self.assertIn("budget", info["reason"])
        self.assertEqual(client.calls, [])  # the model is never called
        self.assertTrue(any("skipping 'long.pdf'" in m for m in logged))

    def test_server_side_cut_is_detected_and_discarded(self):
        # The server silently keeps only 1,000 tokens, whatever num_ctx says
        # (for example a server that ignores the option).
        client = FakeClient(server_ctx=1000)
        logged = []
        text = "word " * 1500  # fits the 4096 budget by our estimate
        summary, info = run(ops.generate_summary(client, text, "m", self.settings,
                                                 name="p.pdf", log=logged.append))
        self.assertIsNone(summary)
        self.assertEqual(info["status"], "rejected")
        self.assertIn("cut by the server", info["reason"])
        self.assertTrue(any("discarding summary of 'p.pdf'" in m for m in logged))

    def test_missing_eval_count_is_not_trusted(self):
        client = FakeClient(report_eval=False)
        summary, info = run(ops.generate_summary(client, "text", "m", self.settings, log=quiet))
        self.assertIsNone(summary)
        self.assertEqual(info["status"], "rejected")

    def test_answer_cut_by_num_predict_is_discarded(self):
        client = FakeClient(done_reason="length")
        summary, info = run(ops.generate_summary(client, "text", "m", self.settings, log=quiet))
        self.assertIsNone(summary)
        self.assertIn("num_predict", info["reason"])

    def test_response_object_form_is_read(self):
        client = FakeClient(as_object=True)
        summary, info = run(ops.generate_summary(client, "text", "m", self.settings, log=quiet))
        self.assertEqual(info["status"], "fit")
        self.assertTrue(summary)

    def test_v1_style_call_would_have_been_caught(self):
        # Reproduce the v1 failure mode: a long paper, a server context of
        # 2,048 tokens. With truncation the script cuts the text itself; with a
        # budget larger than the server's real context, the after-call check
        # still refuses to save the note.
        settings = ops.ContextSettings(num_ctx=32768, reserve_tokens=1024)
        client = FakeClient(server_ctx=2048)
        summary, info = run(ops.generate_summary(client, "word " * 20000, "m", settings,
                                                 log=quiet))
        self.assertIsNone(summary)
        self.assertEqual(info["status"], "rejected")

    def test_dense_text_cut_by_the_server_is_discarded(self):
        # Text that tokenizes at about 1 character per token (CJK, symbol-heavy
        # extraction): the cut made at 3.0 chars/token still overflows num_ctx,
        # the server keeps num_ctx tokens, and the note must not be saved.
        for cpt in (1.0, 2.0, 2.5):
            client = FakeClient(chars_per_token=cpt)
            summary, info = run(ops.generate_summary(client, "x" * 100000, "m",
                                                     self.settings, log=quiet))
            self.assertIsNone(summary, cpt)
            self.assertEqual(info["status"], "rejected", cpt)
            self.assertIn("prompt budget", info["reason"])

    def test_cut_that_keeps_almost_no_text_is_skipped(self):
        # num_ctx minus the reserve leaves room for the fixed prompt and little else
        settings = ops.ContextSettings(num_ctx=1900, reserve_tokens=1536)
        client = FakeClient()
        summary, info = run(ops.generate_summary(client, "x" * 50000, "m", settings,
                                                 log=quiet))
        self.assertIsNone(summary)
        self.assertEqual(info["status"], "skip")
        self.assertIn("minimum", info["reason"])
        self.assertEqual(client.calls, [])

    def test_cli_bad_settings_are_a_usage_error(self):
        argv = sys.argv
        sys.argv = ["ollama_paper_summarizer.py", "--input", "in", "--out", "out",
                    "--num-ctx", "1024"]
        try:
            with self.assertRaises(SystemExit) as cm:
                stderr = sys.stderr
                sys.stderr = open(os.devnull, "w")
                try:
                    ops.main()
                finally:
                    sys.stderr.close()
                    sys.stderr = stderr
            self.assertEqual(cm.exception.code, 2)
        finally:
            sys.argv = argv

    def test_bad_settings_rejected(self):
        with self.assertRaises(ValueError):
            ops.ContextSettings(on_overflow="ignore")
        with self.assertRaises(ValueError):
            ops.ContextSettings(num_ctx=1024, reserve_tokens=1024)


if __name__ == "__main__":
    unittest.main()
