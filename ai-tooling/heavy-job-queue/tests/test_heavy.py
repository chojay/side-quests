import fcntl
import os
import subprocess
import sys
import tempfile
import time
import unittest

from fakes import FakeProbe, make_config, row, sysinfo

import heavy  # noqa: E402  (fakes puts the project root on sys.path)


def short_wait(_s):
    time.sleep(0.02)


def child_cmd(pidfile, seconds=30):
    """A child that records its pid, then sleeps (it uses no real memory)."""
    code = "import os,time; open(%r,'w').write(str(os.getpid())); time.sleep(%d)" % (pidfile, seconds)
    return [sys.executable, "-c", code]


def rows_from_pidfile(pidfile, mem_gb):
    def rows():
        try:
            with open(pidfile) as f:
                pid = int(f.read() or 0)
        except (OSError, ValueError):
            return []
        return [row(pid, "python3 fake-job", mem_gb, ppid=os.getpid())] if pid else []
    return rows


class NeedTest(unittest.TestCase):
    def test_explicit_need_wins(self):
        self.assertEqual(heavy.choose_need(5.0, 20.0, 8), 5.0)

    def test_need_from_history(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "heavy.log")
            with open(log, "w") as f:
                f.write("2026-01-01 00:00:00 END name=embed pid=1 rc=0 peak_gb=10.00 min=1.0\n")
                f.write("2026-01-01 00:10:00 END name=embed pid=2 rc=0 peak_gb=12.50 min=1.0\n")
                f.write("2026-01-01 00:20:00 END name=embedder pid=3 rc=0 peak_gb=40.00 min=1.0\n")
            peak = heavy.past_peak(log, "embed")
        self.assertEqual(peak, 12.5)                       # "embedder" is another job
        self.assertEqual(heavy.choose_need(None, peak, 8), 15.0)

    def test_small_peak_asks_at_least_2_gb(self):
        self.assertEqual(heavy.choose_need(None, 0.4, 8), 2.0)

    def test_no_history_uses_default(self):
        self.assertEqual(heavy.choose_need(None, None, 8), 8)


class NestingTest(unittest.TestCase):
    def test_live_ancestor_is_accepted(self):
        me, parent = os.getpid(), os.getppid()
        rows = [row(me, "python3 x", 0, ppid=parent), row(parent, "heavy", 0, ppid=1)]
        self.assertTrue(heavy.nested_ok("job:%d" % parent, rows, me))

    def test_wrapper_run_by_python_is_accepted(self):
        me, parent = os.getpid(), os.getppid()
        rows = [row(me, "python3 x", 0, ppid=parent),
                row(parent, "/usr/bin/python3 /opt/bin/heavy --name job -- python3 x", 0, ppid=1)]
        self.assertTrue(heavy.nested_ok("job:%d" % parent, rows, me))

    def test_live_ancestor_that_is_not_heavy_is_rejected(self):
        # HEAVY_ACTIVE naming the agent's own shell must not skip the queue.
        me, parent = os.getpid(), os.getppid()
        rows = [row(me, "python3 x", 0, ppid=parent), row(parent, "/bin/zsh -c python3 x", 0, ppid=1)]
        self.assertFalse(heavy.nested_ok("x:%d" % parent, rows, me))

    def test_bare_flag_is_rejected(self):
        self.assertFalse(heavy.nested_ok("1", [], os.getpid()))

    def test_unrelated_or_dead_pid_is_rejected(self):
        me, parent = os.getpid(), os.getppid()
        rows = [row(me, "python3 x", 0, ppid=parent), row(parent, "sh", 0, ppid=1)]
        self.assertFalse(heavy.nested_ok("job:%d" % me, rows, parent))   # alive, but not an ancestor
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()
        self.assertFalse(heavy.nested_ok("job:%d" % p.pid, rows, me))    # dead


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.cfg = make_config(self.d, heavy={"poll_s": 0.05})
        self.pidfile = os.path.join(self.d, "child.pid")
        os.environ["MEMGUARD_NO_ALERT"] = "1"
        os.environ.pop("HEAVY_ACTIVE", None)

    def tearDown(self):
        self.tmp.cleanup()

    def log_text(self):
        with open(os.path.join(self.d, "heavy.log")) as f:
            return f.read()

    def test_normal_run_logs_peak(self):
        probe = FakeProbe(sysinfo(40), rows_from_pidfile(self.pidfile, 3.0))
        cmd = child_cmd(self.pidfile, 0)
        rc = heavy.main(["--name", "ok-job", "--need", "4", "--"] + cmd, probe=probe, cfg=self.cfg, sleep=short_wait)
        self.assertEqual(rc, 0)
        log = self.log_text()
        self.assertIn("START name=ok-job", log)
        self.assertIn("END name=ok-job", log)
        self.assertIn("rc=0", log)
        self.assertNotIn("current.json", os.listdir(self.d))

    def test_cap_stop(self):
        probe = FakeProbe(sysinfo(40), rows_from_pidfile(self.pidfile, 26.0))
        t0 = time.time()
        rc = heavy.main(["--name", "big", "--need", "4", "--cap", "24", "--"] + child_cmd(self.pidfile),
                        probe=probe, cfg=self.cfg, sleep=short_wait)
        self.assertEqual(rc, heavy.EX_STOPPED)
        # The 30 s child was stopped, and fast: its zombie must not look alive for the 8 s grace.
        self.assertLess(time.time() - t0, 5)
        with open(self.pidfile) as f:
            pid = int(f.read())
        self.assertFalse(heavy.alive(pid))
        self.assertRegex(self.log_text(), r"END name=big .*peak_gb=26\.00 .*STOPPED")

    def test_critical_memory_stop(self):
        probe = FakeProbe(sysinfo(2.0, pressure="critical"), rows_from_pidfile(self.pidfile, 1.0))
        # Admission needs 1 GB and 2 GB are free, then memory stays critical (3 %).
        rc = heavy.main(["--name", "crit", "--need", "1", "--"] + child_cmd(self.pidfile),
                        probe=probe, cfg=self.cfg, sleep=short_wait)
        self.assertEqual(rc, heavy.EX_STOPPED)

    def test_admission_refused_when_memory_never_frees(self):
        probe = FakeProbe(sysinfo(3.0), [])
        rc = heavy.main(["--name", "wait", "--need", "20", "--wait", "0.002", "--"] + child_cmd(self.pidfile),
                        probe=probe, cfg=self.cfg, sleep=short_wait)
        self.assertEqual(rc, heavy.EX_GAVE_UP)
        self.assertFalse(os.path.exists(self.pidfile))     # the job never started

    def test_admission_refused_while_a_big_job_runs_outside_the_queue(self):
        outsider = row(424242, "/usr/bin/python3 someone_elses_train.py", 20.0, ppid=1)
        probe = FakeProbe(sysinfo(40), [outsider])
        rc = heavy.main(["--name", "wait", "--need", "4", "--wait", "0.002", "--"] + child_cmd(self.pidfile),
                        probe=probe, cfg=self.cfg, sleep=short_wait)
        self.assertEqual(rc, heavy.EX_GAVE_UP)

    def test_second_job_waits_for_the_lock(self):
        fd = os.open(self.cfg["lock"], os.O_RDWR | os.O_CREAT, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            probe = FakeProbe(sysinfo(40), [])
            rc = heavy.main(["--name", "second", "--need", "1", "--wait", "0.002", "--"] + child_cmd(self.pidfile),
                            probe=probe, cfg=self.cfg, sleep=short_wait)
        finally:
            os.close(fd)
        self.assertEqual(rc, heavy.EX_GAVE_UP)
        self.assertEqual(os.listdir(os.path.join(self.d, "queue")), [])   # queue entry cleaned up

    def test_bare_heavy_active_does_not_skip_the_queue(self):
        os.environ["HEAVY_ACTIVE"] = "1"
        try:
            probe = FakeProbe(sysinfo(40), rows_from_pidfile(self.pidfile, 26.0))
            rc = heavy.main(["--name", "sneaky", "--need", "1", "--cap", "10", "--"] + child_cmd(self.pidfile),
                            probe=probe, cfg=self.cfg, sleep=short_wait)
        finally:
            os.environ.pop("HEAVY_ACTIVE", None)
        self.assertEqual(rc, heavy.EX_STOPPED)              # it went through the cap

    def test_history_cli(self):
        probe = FakeProbe(sysinfo(40), [])
        heavy.main(["--name", "h1", "--need", "1", "--"] + child_cmd(self.pidfile, 0),
                   probe=probe, cfg=self.cfg, sleep=short_wait)
        self.assertEqual(len(heavy.history(os.path.join(self.d, "heavy.log"), "h1")), 1)


class StatusTest(unittest.TestCase):
    def test_status_prints_without_a_real_machine(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = make_config(d)
            probe = FakeProbe(sysinfo(30), [row(7, "/usr/bin/python3 train.py", 5.0)])
            heavy.status(cfg, probe)


if __name__ == "__main__":
    unittest.main()
