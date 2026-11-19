import os
import plistlib
import subprocess
import tempfile
import unittest

from fakes import ROOT


class RenderPlistTest(unittest.TestCase):
    def test_render_fills_every_placeholder_and_runs_no_launchctl(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, MEMGUARD_STATE=os.path.join(d, "state"),
                       MEMGUARD_CONFIG=os.path.join(d, "c.json"))
            p = subprocess.run(["sh", os.path.join(ROOT, "launchd", "render_plist.sh"), d],
                               capture_output=True, text=True, env=env, timeout=30)
            self.assertEqual(p.returncode, 0, p.stderr)
            path = os.path.join(d, "local.memguard.watchdog.plist")
            with open(path, "rb") as f:
                raw = f.read()
            self.assertNotIn(b"__", raw)
            pl = plistlib.loads(raw)
            self.assertEqual(pl["Label"], "local.memguard.watchdog")
            self.assertTrue(pl["ProgramArguments"][1].endswith("mem_watchdog.py"))
            self.assertEqual(pl["EnvironmentVariables"]["MEMGUARD_CONFIG"], os.path.join(d, "c.json"))
            self.assertIn("launchctl bootstrap", p.stdout)        # printed for the person, not run
            self.assertFalse(os.path.exists(os.path.join(d, "state")))


if __name__ == "__main__":
    unittest.main()
