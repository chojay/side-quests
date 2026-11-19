import json
import os
import tempfile
import unittest

from fakes import FakeProbe, make_config, row, sysinfo

import mem_watchdog  # noqa: E402


class Clock(object):
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class WatchdogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = make_config(self.tmp.name)
        self.stopped, self.alerts = [], []
        self.clock = Clock()

    def tearDown(self):
        self.tmp.cleanup()

    def dog(self, probe, dry=False):
        return mem_watchdog.Watchdog(self.cfg, probe=probe, dry_run=dry,
                                     stop_fn=lambda pid: self.stopped.append(pid) or True,
                                     alert_fn=self.alerts.append, clock=self.clock)

    def ticks(self, wd, n):
        out = []
        for _ in range(n):
            out.append(wd.tick())
            self.clock.t += 5
        return out

    def test_calm_machine_does_nothing(self):
        wd = self.dog(FakeProbe(sysinfo(40), [row(10, "python3 train.py", 20)]))
        self.assertEqual(self.ticks(wd, 3), ["ok"] * 3)
        self.assertEqual(self.stopped, [])
        self.assertEqual(self.alerts, [])

    def test_single_job_cap_stops_at_once(self):
        wd = self.dog(FakeProbe(sysinfo(40), [row(10, "python3 train.py", 40), row(11, "python3 small.py", 2)]))
        self.assertEqual(wd.tick(), "single-job cap")
        self.assertEqual(self.stopped, [10])
        self.assertEqual(len(self.alerts), 1)

    def test_sustained_critical_stops_the_largest_job(self):
        rows = [row(10, "python3 a.py", 4), row(11, "python3 b.py", 12), row(12, "Some.app", 30)]
        wd = self.dog(FakeProbe(sysinfo(3), rows))
        d = self.ticks(wd, 2)
        self.assertEqual(d, ["ok", "critical"])      # one critical check is not enough
        self.assertEqual(self.stopped, [11])              # the app is not a job

    def test_cooldown_between_kills(self):
        rows = [row(10, "python3 a.py", 4), row(11, "python3 b.py", 12)]
        wd = self.dog(FakeProbe(sysinfo(3), rows))
        self.ticks(wd, 4)                                  # 20 s: kill at t=5, next allowed at t>=25
        self.assertEqual(self.stopped, [11])
        self.ticks(wd, 2)
        self.assertEqual(self.stopped, [11, 11])

    def test_os_critical_pressure_counts_as_critical(self):
        wd = self.dog(FakeProbe(sysinfo(16, pressure="critical"), [row(10, "python3 a.py", 8)]))
        self.ticks(wd, 2)
        self.assertEqual(self.stopped, [10])

    def test_os_critical_can_be_switched_off(self):
        self.cfg["watchdog"]["crit_on_os_critical"] = False
        wd = self.dog(FakeProbe(sysinfo(16, pressure="critical"), [row(10, "python3 a.py", 8)]))
        self.assertEqual(self.ticks(wd, 2), ["ok", "ok"])

    def test_critical_with_no_victim_alerts(self):
        wd = self.dog(FakeProbe(sysinfo(3), [row(10, "python3 tiny.py", 1)]))
        self.ticks(wd, 2)
        self.assertEqual(self.stopped, [])
        self.assertEqual(len(self.alerts), 1)
        self.assertIn("no job process to stop", self.alerts[0])

    def test_ps_failure_still_decides(self):
        wd = self.dog(FakeProbe(sysinfo(3), lambda: OSError("ps timed out")))
        self.assertEqual(self.ticks(wd, 2), ["ok", "critical"])
        self.assertIn("could not be read", self.alerts[0])

    def test_warning_alert_repeats_only_after_warn_repeat_min(self):
        wd = self.dog(FakeProbe(sysinfo(8.5), [row(10, "python3 a.py", 2)]))   # 13 %, warn not crit
        self.ticks(wd, 10)
        self.assertEqual(len(self.alerts), 1)
        self.clock.t += 31 * 60
        self.ticks(wd, 1)
        self.assertEqual(len(self.alerts), 2)

    def test_dry_run_never_stops(self):
        wd = self.dog(FakeProbe(sysinfo(40), [row(10, "python3 train.py", 40)]), dry=True)
        wd.tick()
        self.assertEqual(self.stopped, [])
        self.assertEqual(wd.actions, [(10, "one job over 36 GB")])

    def test_state_file_written(self):
        wd = self.dog(FakeProbe(sysinfo(40), []))
        wd.tick()
        with open(os.path.join(self.tmp.name, "watchdog_state.json")) as f:
            st = json.load(f)
        self.assertEqual(st["decision"], "ok")


if __name__ == "__main__":
    unittest.main()
