#!/usr/bin/env python3
"""heavy: run memory-heavy jobs one at a time, with memory admission and a per-job cap.

    heavy [--name NAME] [--need GB] [--cap GB] [--wait MIN] -- COMMAND [ARGS...]
    heavy --status            memory, the running job, the queue, top processes
    heavy --history [NAME]    past runs with their peak GB (use it to pick --need)

What it does:
  1. Queue: one heavy job at a time (flock on one global lock file). Waiters print
     who they wait for. A heavy job started inside a heavy job runs directly, but
     only when the outer job really is an ancestor of this process.
  2. Admission: waits until --need GB are available and no job process outside the
     queue holds busy_gb or more.
  3. Cap: sums the phys_footprint of the job's whole process tree every poll_s
     seconds; above --cap GB, or after `sustain` checks at critical memory, it stops
     the tree (TERM, then KILL) and exits 137.
  4. History: START and END lines (peak GB, minutes) in <state_dir>/heavy.log. With
     no --need, the next run of the same name asks for 1.2 x its past peak.

macOS only (sysctl kern.memorystatus_level and libproc). Settings: memlib.DEFAULTS,
overridden by the JSON file in $MEMGUARD_CONFIG (default ~/.config/memguard/config.json).
"""
import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import memlib as m  # noqa: E402

EX_GAVE_UP = 75
EX_STOPPED = 137


def say(msg):
    sys.stderr.write("heavy: %s\n" % msg)
    sys.stderr.flush()


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


class Paths(object):
    def __init__(self, cfg):
        self.state = cfg["state_dir"]
        self.log = os.path.join(self.state, "heavy.log")
        self.current = os.path.join(self.state, "current.json")
        self.queue = os.path.join(self.state, "queue")
        self.lock = cfg["lock"]


def history(log_path, name=None, n=15):
    rows = []
    try:
        with open(log_path) as f:
            for line in f:
                if " END " not in line:
                    continue
                if name and (" name=%s " % name) not in line + " ":
                    continue
                rows.append(line.rstrip())
    except OSError:
        pass
    return rows[-n:]


def past_peak(log_path, name):
    peak = None
    for line in history(log_path, name, 50):
        for tok in line.split():
            if tok.startswith("peak_gb="):
                try:
                    v = float(tok.split("=", 1)[1])
                except ValueError:
                    continue
                peak = v if peak is None else max(peak, v)
    return peak


def choose_need(need_arg, peak, default_need):
    """--need if given, else 1.2 x the past peak (at least 2 GB), else the default."""
    if need_arg is not None:
        return need_arg
    if peak:
        return max(2.0, round(peak * 1.2, 1))
    return default_need


# A heavy wrapper in ps: "heavy ..." or "<python> /path/to/heavy[.py] ...".
HEAVY_CMD = re.compile(r"^(\S*[Pp]ython[0-9.]* +)?(\S*/)?heavy(\.py)?( |$)")


def nested_ok(env_value, rows, my_pid):
    """True if HEAVY_ACTIVE names a live ancestor of my_pid whose command runs heavy.

    A bare HEAVY_ACTIVE=1 typed by hand (or a stale value) is not enough to skip
    the queue and the cap.
    """
    if not env_value or ":" not in env_value:
        return False
    try:
        pid = int(env_value.rsplit(":", 1)[1])
    except ValueError:
        return False
    if pid <= 1 or not alive(pid) or pid not in m.ancestors(rows, my_pid):
        return False
    # The ancestor must itself run heavy: any live ancestor (the agent's shell, say)
    # would otherwise reopen the HEAVY_ACTIVE=1 escape in a longer form.
    cmd = next((r["cmd"] for r in rows if r["pid"] == pid), "")
    return bool(HEAVY_CMD.search(cmd))


def outside_jobs(cfg, rows, mine):
    """Job processes of busy_gb or more that are not in this queue's tree."""
    return [r for r in rows
            if r["pid"] not in mine and m.is_job(cfg, r) and r["mem_gb"] >= cfg["heavy"]["busy_gb"]]


def status(cfg, probe):
    p = Paths(cfg)
    s = probe.system()
    rows = probe.processes()
    print("memory: " + m.status_line(s))
    wst = read_json(os.path.join(p.state, "watchdog_state.json"))
    if wst and time.time() - wst.get("time", 0) < 60:
        print("watchdog: running (last check %.0f s ago, %s)" % (time.time() - wst["time"], wst.get("decision")))
    else:
        print("watchdog: not running (see the README, section 'The watchdog')")
    cur = read_json(p.current)
    if cur and alive(cur.get("pid", 0)):
        if cur.get("state"):
            print("running: %s (wrapper pid %d) is %s" % (cur["name"], cur["pid"], cur["state"]))
        else:
            print("running: %s (pid %d) for %d min, %.1f GB now, peak %.1f GB, cap %.0f GB" % (
                cur["name"], cur["pid"], (time.time() - cur["start"]) / 60, cur.get("now_gb", 0),
                cur.get("peak_gb", 0), cur["cap_gb"]))
    else:
        print("running: nothing in the heavy queue")
    waiting = []
    for fn in sorted(os.listdir(p.queue)) if os.path.isdir(p.queue) else []:
        q = read_json(os.path.join(p.queue, fn))
        if q and alive(q.get("pid", 0)):
            waiting.append("%s (pid %d, need %.0f GB, since %s)" % (
                q["name"], q["pid"], q["need_gb"], time.strftime("%H:%M", time.localtime(q["since"]))))
        else:
            try:
                os.remove(os.path.join(p.queue, fn))
            except OSError:
                pass
    print("waiting: " + ("; ".join(waiting) if waiting else "none"))
    big = [r for r in rows if m.is_job(cfg, r) and r["mem_gb"] >= 1]
    print("job processes >= 1 GB (queued or not):")
    print("\n".join("  " + x for x in m.top_lines(big, 8)) if big else "  none")
    print("top memory users:")
    print("\n".join("  " + x for x in m.top_lines(rows, 6)))
    h = history(p.log, None, 5)
    if h:
        print("recent heavy runs:")
        print("\n".join("  " + x for x in h))


def stop_tree(pids, grace_s=8.0, is_alive=alive):
    """TERM, then KILL. is_alive must reap our own child, or its zombie looks alive."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        pids = [pid for pid in pids if is_alive(pid)]
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        deadline = time.time() + grace_s
        while time.time() < deadline and any(is_alive(pid) for pid in pids):
            time.sleep(0.2)


def acquire(lockfd, p, name, need, wait_min, sleep):
    """Take the global lock, waiting up to wait_min minutes. True on success."""
    qfile = os.path.join(p.queue, "%d.json" % os.getpid())
    deadline = time.time() + wait_min * 60
    try:
        fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        pass
    write_json(qfile, {"pid": os.getpid(), "name": name, "need_gb": need, "since": time.time()})
    cur = read_json(p.current) or {}
    say("queued %s behind %s (pid %s); waiting up to %g min" % (
        name, cur.get("name", "?"), cur.get("pid", "?"), wait_min))
    try:
        while True:
            try:
                fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except OSError:
                if time.time() > deadline:
                    say("gave up after %g min in the queue" % wait_min)
                    return False
                sleep(1.0)
    finally:
        try:
            os.remove(qfile)
        except OSError:
            pass


def admit(cfg, probe, need, wait_min, name, sleep):
    """Wait until need GB are available and no big job runs outside the queue."""
    deadline = time.time() + wait_min * 60
    told = False
    while True:
        s = probe.system()
        others = outside_jobs(cfg, probe.processes(), {os.getpid()})
        if s["avail_gb"] >= need and not others:
            return True
        if not told:
            why = "%.1f GB available, need %.1f GB" % (s["avail_gb"], need)
            if others:
                why += "; busy: " + ", ".join("pid %d %.1f GB %s" % (r["pid"], r["mem_gb"], m.short(r["cmd"], 50))
                                             for r in others[:3])
            say("holding %s: %s" % (name, why))
            told = True
        if time.time() > deadline:
            say("gave up: memory never freed up within %g min" % wait_min)
            return False
        sleep(5.0)


def supervise(cfg, probe, cmd, name, cap, lockfd, p, sleep):
    """Start cmd, watch its tree, stop it over the cap. Returns (rc, peak_gb, stopped_msg)."""
    env = dict(os.environ, HEAVY_ACTIVE="%s:%d" % (name, os.getpid()))
    start = time.time()
    # The child keeps the lock fd, so the queue stays held while the job runs even
    # if this wrapper is killed.
    proc = subprocess.Popen(cmd, env=env, start_new_session=True, pass_fds=(lockfd,))
    m.log(p.log, "START name=%s pid=%d cap_gb=%.1f cmd=%s" % (name, proc.pid, cap, m.short(" ".join(cmd), 200)))
    say("started %s (pid %d), cap %.0f GB" % (name, proc.pid, cap))

    def forward(sig, _frame):
        try:
            os.killpg(proc.pid, sig)
        except OSError:
            pass

    old = {}
    for sg in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        old[sg] = signal.signal(sg, forward)

    wd = cfg["watchdog"]
    peak, crit, stopped, last_write = 0.0, 0, None, 0.0
    try:
        while proc.poll() is None:
            rows = probe.processes()
            tree = m.descendants(rows, proc.pid)
            now = sum(r["mem_gb"] for r in rows if r["pid"] in tree)
            peak = max(peak, now)
            s = probe.system()
            is_crit = s["level_pct"] <= wd["crit_level_pct"] or (
                wd.get("crit_on_os_critical") and s.get("pressure") == "critical")
            crit = crit + 1 if is_crit else 0
            if now > cap:
                stopped = "stopped %s: %.1f GB is over its cap of %.1f GB. Split the work or raise --cap." % (
                    name, now, cap)
            elif crit >= wd["sustain"]:
                stopped = "stopped %s at %.1f GB: memory is critical (%s)." % (name, now, m.status_line(s))
            if stopped:
                stop_tree(sorted(tree),
                          is_alive=lambda pid: proc.poll() is None if pid == proc.pid else alive(pid))
                say(stopped)
                m.alert(cfg, "heavy " + stopped)
                break
            if time.time() - last_write > 10:
                write_json(p.current, {"pid": proc.pid, "name": name, "start": start, "cap_gb": cap,
                                       "now_gb": round(now, 2), "peak_gb": round(peak, 2)})
                last_write = time.time()
            sleep(cfg["heavy"]["poll_s"])
        rc = proc.wait()
    finally:
        for sg, h in old.items():
            signal.signal(sg, h)
    if stopped:
        rc = EX_STOPPED
    m.log(p.log, "END name=%s pid=%d rc=%d peak_gb=%.2f min=%.1f%s" % (
        name, proc.pid, rc, peak, (time.time() - start) / 60, " STOPPED" if stopped else ""))
    return rc, peak, stopped


def main(argv=None, probe=None, cfg=None, sleep=time.sleep):
    cfg = cfg or m.load_config()
    probe = probe or m.Probe()
    h = cfg["heavy"]
    ap = argparse.ArgumentParser(prog="heavy", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", help="job name for the log and --history (default: first word)")
    ap.add_argument("--need", type=float, help="GB that must be available before start "
                    "(default: 1.2 x past peak for this name, else %g)" % h["default_need_gb"])
    ap.add_argument("--cap", type=float, help="stop the job above this many GB (default %g)" % h["default_cap_gb"])
    ap.add_argument("--wait", type=float, default=h["wait_min"], help="minutes to wait in the queue")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--history", nargs="?", const="", default=None, metavar="NAME")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    p = Paths(cfg)

    if a.status:
        status(cfg, probe)
        return 0
    if a.history is not None:
        print("\n".join(history(p.log, a.history or None, 30)) or "no runs logged")
        return 0
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        ap.error("give a command after --")
    name = a.name or os.path.basename(cmd[0])
    need = choose_need(a.need, past_peak(p.log, name), h["default_need_gb"])
    cap = a.cap if a.cap is not None else h["default_cap_gb"]

    outer = os.environ.get("HEAVY_ACTIVE")
    if outer:
        if nested_ok(outer, probe.processes(), os.getpid()):
            say("inside heavy job %s, running %s directly" % (outer.rsplit(":", 1)[0], name))
            os.execvp(cmd[0], cmd)
        say("ignoring HEAVY_ACTIVE=%s: it names no live heavy job above this process" % outer)

    os.makedirs(p.queue, exist_ok=True)
    lockfd = os.open(p.lock, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if not acquire(lockfd, p, name, need, a.wait, sleep):
            return EX_GAVE_UP
        write_json(p.current, {"pid": os.getpid(), "name": name, "start": time.time(), "cap_gb": cap,
                               "state": "holding for memory"})
        try:
            if not admit(cfg, probe, need, a.wait, name, sleep):
                return EX_GAVE_UP
            rc, peak, stopped = supervise(cfg, probe, cmd, name, cap, lockfd, p, sleep)
        finally:
            try:
                os.remove(p.current)
            except OSError:
                pass
        if not stopped:
            say("%s finished rc=%d, peak %.1f GB" % (name, rc, peak))
        return rc if rc >= 0 else 128 - rc
    finally:
        os.close(lockfd)


if __name__ == "__main__":
    sys.exit(main())
