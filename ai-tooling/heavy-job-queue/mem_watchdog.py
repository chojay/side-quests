#!/usr/bin/env python3
"""Memory watchdog: the safety net under the heavy queue (macOS, run it as a LaunchAgent).

Every interval_s seconds it reads kern.memorystatus_level (percent of RAM
available), the macOS pressure level, swap, and every job process's
phys_footprint, then:

  * a job process over single_job_cap_gb -> stop it (TERM, then KILL) and alert;
  * critical for `sustain` checks in a row (available <= crit_level_pct, macOS
    pressure "critical" when crit_on_os_critical is on, or swap >= crit_swap_gb
    while available <= swap_counts_below_level_pct) -> stop the largest job
    process of min_victim_gb or more, alert, then wait kill_cooldown_s;
  * warning (available <= warn_level_pct, or swap >= warn_swap_gb while low) ->
    alert with the top users, at most once per warn_repeat_min.

A job process is one of your own processes that matches job_regex and not
protect_regex (memlib.DEFAULTS, overridden by $MEMGUARD_CONFIG). Other users'
processes and apps are never touched.

If the process list cannot be read (ps timed out), the check still runs on the
system numbers: a sustained critical state then alerts with no victim instead
of being skipped.

    mem_watchdog.py              run the loop
    mem_watchdog.py --once       one decision, printed (add --dry-run to never stop anything)
    mem_watchdog.py --status     last state written by the loop
"""
import json
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import memlib as m  # noqa: E402


def stop(pid):
    for sig, wait in ((signal.SIGTERM, 8), (signal.SIGKILL, 3)):
        try:
            os.kill(pid, sig)
        except OSError:
            return True
        end = time.time() + wait
        while time.time() < end:
            try:
                os.kill(pid, 0)
            except OSError:
                return True
            time.sleep(0.5)
    return False


class Watchdog(object):
    def __init__(self, cfg, probe=None, dry_run=False, stop_fn=stop, alert_fn=None,
                 clock=time.time, write_state=True):
        self.cfg = cfg
        self.w = cfg["watchdog"]
        self.probe = probe or m.Probe()
        self.dry = dry_run
        self.stop_fn = stop_fn
        self.alert_fn = alert_fn or (lambda msg: m.alert(cfg, msg))
        self.clock = clock
        self.write_state = write_state and not dry_run
        self.log_path = os.path.join(cfg["state_dir"], "watchdog.log")
        self.state_path = os.path.join(cfg["state_dir"], "watchdog_state.json")
        self.crit_n = 0
        self.warn_n = 0
        self.last_kill = -1e18
        self.last_warn_alert = -1e18
        self.last_log = -1e18
        self.last_action = None
        self.actions = []

    def _log(self, msg):
        if not self.dry:
            m.log(self.log_path, msg)

    def act(self, row, why, s):
        msg = "stopped pid %d (%.1f GB) %s. Reason: %s. Memory: %s." % (
            row["pid"], row["mem_gb"], m.short(row["cmd"], 120), why, m.status_line(s))
        self.actions.append((row["pid"], why))
        if self.dry:
            print("DRY RUN, would have " + msg)
            return
        if not self.stop_fn(row["pid"]):
            msg = "could NOT stop " + msg[len("stopped "):]
        self._log("ACTION " + msg)
        self.alert_fn("Memory watchdog " + msg + " Heavy jobs should run one at a time: heavy --status")
        self.last_action = {"time": self.clock(), "msg": msg}

    def tick(self, verbose=False):
        w = self.w
        now = self.clock()
        s = self.probe.system()
        ps_ok = True
        try:
            rows = self.probe.processes()
        except Exception as e:  # ps can time out under heavy pressure
            rows, ps_ok = [], False
            self._log("process list failed (%r); deciding on system numbers only" % (e,))
        jobs = sorted([r for r in rows if m.is_job(self.cfg, r)], key=lambda r: -r["mem_gb"])
        lvl, swap = s["level_pct"], s["swap_gb"]
        swap_low = lvl <= w["swap_counts_below_level_pct"]
        os_crit = bool(w.get("crit_on_os_critical")) and s.get("pressure") == "critical"
        crit = lvl <= w["crit_level_pct"] or os_crit or (swap >= w["crit_swap_gb"] and swap_low)
        warn = crit or lvl <= w["warn_level_pct"] or (swap >= w["warn_swap_gb"] and swap_low)
        decision = "ok"

        for r in jobs:
            if r["mem_gb"] >= w["single_job_cap_gb"]:
                self.act(r, "one job over %.0f GB" % w["single_job_cap_gb"], s)
                decision = "single-job cap"

        self.crit_n = self.crit_n + 1 if crit else 0
        self.warn_n = self.warn_n + 1 if warn else 0
        if decision == "ok" and self.crit_n >= w["sustain"]:
            decision = "critical"
            if now - self.last_kill >= w["kill_cooldown_s"]:
                victims = [r for r in jobs if r["mem_gb"] >= w["min_victim_gb"]]
                if victims:
                    self.act(victims[0], "memory critical for %d checks" % self.crit_n, s)
                    self.last_kill = now
                    self.crit_n = 0
                elif now - self.last_warn_alert >= w["warn_repeat_min"] * 60 and not self.dry:
                    why = "no job process to stop" if ps_ok else "the process list could not be read"
                    self.alert_fn("Memory critical (%s) and %s. Top users:\n%s" % (
                        m.status_line(s), why, "\n".join(m.top_lines(rows, 5)) or "  unknown"))
                    self._log("CRITICAL no victim (%s): %s" % (why, m.status_line(s)))
                    self.last_warn_alert = now
        elif decision == "ok" and self.warn_n >= w["sustain"]:
            decision = "warning"
            if now - self.last_warn_alert >= w["warn_repeat_min"] * 60 and not self.dry:
                self.alert_fn("Memory low: %s. Top users:\n%s\nRun heavy jobs one at a time (heavy --status)." % (
                    m.status_line(s), "\n".join(m.top_lines(rows, 5))))
                self._log("WARN " + m.status_line(s))
                self.last_warn_alert = now

        if verbose or now - self.last_log >= w["log_every_s"]:
            top = ("; top job pid %d %.1f GB %s" % (jobs[0]["pid"], jobs[0]["mem_gb"], m.short(jobs[0]["cmd"], 60))
                   if jobs else "")
            line = "%s: %s%s" % (decision, m.status_line(s), top)
            if verbose:
                print(line)
            else:
                self._log(line)
            self.last_log = now
        if self.write_state:
            state = {"time": now, "decision": decision, "system": s,
                     "top_jobs": [{"pid": r["pid"], "gb": round(r["mem_gb"], 2), "cmd": m.short(r["cmd"], 80)}
                                  for r in jobs[:3]],
                     "last_action": self.last_action}
            os.makedirs(self.cfg["state_dir"], exist_ok=True)
            tmp = self.state_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(state, f)
            os.replace(tmp, self.state_path)
        return decision


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    cfg = m.load_config()
    os.makedirs(cfg["state_dir"], exist_ok=True)
    state_path = os.path.join(cfg["state_dir"], "watchdog_state.json")
    if "--status" in args:
        try:
            with open(state_path) as f:
                st = json.load(f)
        except (OSError, ValueError):
            print("no state yet (is the LaunchAgent loaded?)")
            return 1
        age = time.time() - st["time"]
        print("last check %.0f s ago: %s, %s" % (age, st["decision"], m.status_line(st["system"])))
        for j in st["top_jobs"]:
            print("  job pid %d %.1f GB %s" % (j["pid"], j["gb"], j["cmd"]))
        if st.get("last_action"):
            print("last action %s: %s" % (time.strftime("%m-%d %H:%M", time.localtime(st["last_action"]["time"])),
                                          st["last_action"]["msg"]))
        return 0 if age < 60 else 2
    wd = Watchdog(cfg, dry_run="--dry-run" in args)
    if "--once" in args:
        for _ in range(cfg["watchdog"]["sustain"]):  # sustain counts need consecutive checks
            wd.tick(verbose=True)
            time.sleep(0.2)
        return 0
    m.log(wd.log_path, "watchdog start pid %d (interval %ss, crit <= %d %%, warn <= %d %%, single job cap %.0f GB)" % (
        os.getpid(), cfg["watchdog"]["interval_s"], cfg["watchdog"]["crit_level_pct"],
        cfg["watchdog"]["warn_level_pct"], cfg["watchdog"]["single_job_cap_gb"]))
    while True:
        try:
            wd.tick()
        except Exception as e:  # keep the safety net alive
            m.log(wd.log_path, "error: %r" % (e,))
        time.sleep(cfg["watchdog"]["interval_s"])


if __name__ == "__main__":
    sys.exit(main())
