import json
import os
import tempfile
import unittest

from fakes import row, memlib


class ConfigTest(unittest.TestCase):
    def test_defaults_when_file_missing(self):
        cfg = memlib.load_config("/nonexistent/memguard.json")
        self.assertEqual(cfg["heavy"]["default_cap_gb"], 30)
        self.assertTrue(cfg["lock"].endswith("heavy.lock"))
        self.assertEqual(cfg["alert_cmd"], [])

    def test_file_overrides_one_key_and_keeps_the_rest(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.json")
            with open(p, "w") as f:
                json.dump({"_about": "ignored", "heavy": {"default_cap_gb": 12},
                           "state_dir": d}, f)
            cfg = memlib.load_config(p)
        self.assertEqual(cfg["heavy"]["default_cap_gb"], 12)
        self.assertEqual(cfg["heavy"]["busy_gb"], 6)
        self.assertNotIn("_about", cfg)
        self.assertEqual(cfg["lock"], os.path.join(d, "heavy.lock"))

    def test_example_config_parses(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg = memlib.load_config(os.path.join(here, "config.example.json"))
        self.assertIn("patterns", cfg["hook"])


class ParseTest(unittest.TestCase):
    def test_sysctl(self):
        s = memlib.parse_sysctl(["68719476736", "25", "2",
                                 "total = 2048.00M  used = 1536.00M  free = 512.00M  (encrypted)"])
        self.assertAlmostEqual(s["total_gb"], 64.0)
        self.assertAlmostEqual(s["avail_gb"], 16.0)
        self.assertEqual(s["pressure"], "warn")
        self.assertAlmostEqual(s["swap_gb"], 1.5)

    def test_ps_uses_footprint_for_own_processes_and_rss_for_others(self):
        text = ("  101     1  1024 me      python3 job.py\n"
                "  102     1  2048 other   python3 theirs.py\n"
                "garbage line\n")
        rows = memlib.parse_ps(text, "me", fp=lambda pid: 26 * (1 << 30))
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0]["mem_gb"], 26.0)          # footprint, not 1 MB RSS
        self.assertAlmostEqual(rows[1]["mem_gb"], 2048 * 1024 / float(1 << 30))
        self.assertFalse(rows[1]["mine"])

    def test_footprint_missing_falls_back_to_rss(self):
        rows = memlib.parse_ps("  5  1  1048576 me  python3 x.py\n", "me", fp=lambda pid: None)
        self.assertAlmostEqual(rows[0]["mem_gb"], 1.0)


class TreeTest(unittest.TestCase):
    rows = [row(10, "a", 1, ppid=1), row(11, "b", 1, ppid=10), row(12, "c", 1, ppid=11),
            row(20, "d", 1, ppid=1)]

    def test_descendants(self):
        self.assertEqual(memlib.descendants(self.rows, 10), {10, 11, 12})

    def test_ancestors(self):
        self.assertEqual(memlib.ancestors(self.rows, 12), [11, 10, 1])

    def test_is_job(self):
        cfg = memlib.load_config("/nonexistent")
        self.assertTrue(memlib.is_job(cfg, row(5, "/usr/bin/python3 train.py", 9), self_pid=1))
        self.assertFalse(memlib.is_job(cfg, row(5, "python3 -m some_mcp_server mcp", 9), self_pid=1))
        self.assertFalse(memlib.is_job(cfg, row(5, "python3 x.py", 9, mine=False), self_pid=1))
        self.assertFalse(memlib.is_job(cfg, row(5, "/Applications/Some.app/Contents/MacOS/Some", 9), self_pid=1))
        # A job under a path that contains "claude" is still a job; the guard's own scripts are not.
        self.assertTrue(memlib.is_job(cfg, row(5, "python3 /tmp/claude-scratch/run_model.py", 9), self_pid=1))
        self.assertFalse(memlib.is_job(cfg, row(5, "/usr/bin/python3 /opt/bin/heavy --name x -- y", 9), self_pid=1))
        self.assertFalse(memlib.is_job(cfg, row(5, "python3 /opt/q/mem_watchdog.py", 9), self_pid=1))


class AlertTest(unittest.TestCase):
    def test_no_alert_cmd_means_no_alert(self):
        self.assertFalse(memlib.alert({"alert_cmd": []}, "hi"))

    def test_alert_cmd_gets_message_as_last_argument(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "msg")
            script = os.path.join(d, "a.sh")
            with open(script, "w") as f:
                f.write('#!/bin/sh\nprintf "%s" "$2" > "$1"\n')
            os.chmod(script, 0o755)
            env = os.environ.pop("MEMGUARD_NO_ALERT", None)
            try:
                self.assertTrue(memlib.alert({"alert_cmd": [script, out]}, "hello world"))
            finally:
                if env is not None:
                    os.environ["MEMGUARD_NO_ALERT"] = env
            import time
            for _ in range(50):
                if os.path.exists(out) and os.path.getsize(out):
                    break
                time.sleep(0.05)
            with open(out) as f:
                self.assertEqual(f.read(), "hello world")


if __name__ == "__main__":
    unittest.main()
