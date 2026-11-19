"""Shared helpers for the memory guard (Python 3.9+, standard library only).

System numbers come from sysctl (macOS). Per-process memory is phys_footprint from
libproc proc_pid_rusage, which is what Activity Monitor calls "Memory" and includes
compressed pages. It is readable for your own processes only; other users' processes
fall back to ps RSS. On a system without libproc every process falls back to RSS.

Everything that touches the real machine goes through a Probe, so tests can inject
fake memory numbers and never need real memory pressure.
"""
import copy
import ctypes
import json
import os
import re
import subprocess
import time

GB = float(1 << 30)

DEFAULTS = {
    "state_dir": "~/.local/state/memguard",
    "lock": "",  # empty = <state_dir>/heavy.lock
    # Command run for an alert, with the message appended as the last argument.
    # Empty = no alerts. Example: ["/usr/local/bin/notify-me", "--title", "memguard"]
    "alert_cmd": [],
    # Processes the guard must never count as a job or stop.
    "protect_regex": [
        "\\bmcp\\b",
        "(^|/)claude( |$)",
        "^\\S*[Pp]ython[0-9.]* +(\\S*/)?(heavy(\\.py)?|mem_watchdog\\.py|heavy_job_guard\\.py)( |$)",
        "WindowServer",
        "Virtualization",
    ],
    # Your own processes that count as jobs (the watchdog may stop them).
    "job_regex": [
        "(^|/)[Pp]ython[0-9.]*( |$)",
        "(^|/)[Bb]lender( |$)",
        "(^|/)ffmpeg ",
        "(^|/)uv ",
        "(^|/)(julia|Rscript|java) ",
    ],
    "watchdog": {
        "interval_s": 5,
        "sustain": 2,
        "warn_level_pct": 15,
        "crit_level_pct": 8,
        "crit_on_os_critical": True,
        "warn_swap_gb": 12,
        "crit_swap_gb": 24,
        "swap_counts_below_level_pct": 30,
        "single_job_cap_gb": 36,
        "min_victim_gb": 3,
        "kill_cooldown_s": 20,
        "warn_repeat_min": 30,
        "log_every_s": 60,
    },
    "heavy": {
        "default_need_gb": 8,
        "default_cap_gb": 30,
        "busy_gb": 6,
        "wait_min": 180,
        "poll_s": 2,
    },
    "hook": {
        "light_marker": "MEMGUARD_LIGHT=1",
        "wrappers": ["heavy"],
        "patterns": [
            "--device[ =](mps|cuda)",
            "\\b[Bb]lender\\b[^|;&]*\\s(-b|--background)\\b",
            "\\bimport (torch|tensorflow|transformers|mlx_lm)\\b",
            "\\bfrom (torch|tensorflow|transformers|mlx_lm)\\b",
            "\\bmlx_lm\\.generate\\b",
            "\\bpython[0-9.]*\\b[^|;&]*\\b\\w*(train|infer|embed)\\w*\\.py\\b",
        ],
        "readonly_first_words": [
            "grep", "egrep", "rg", "pgrep", "pkill", "kill", "ps", "top", "cat", "head",
            "tail", "less", "sed", "awk", "ls", "find", "echo", "printf", "wc", "sort",
            "uniq", "cut", "tr", "diff", "stat", "file", "du", "df", "which", "type",
            "man", "git", "open", "cp", "mv", "rm", "mkdir", "touch", "chmod", "ln",
            "date", "sleep", "test", "[",
        ],
        "strip_prefix_words": [
            "do", "then", "else", "elif", "until", "while", "if", "time", "nohup", "env",
            "exec", "command", "caffeinate", "nice", "!", "{", "(",
        ],
    },
}


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def config_path():
    return os.path.expanduser(os.environ.get("MEMGUARD_CONFIG", "~/.config/memguard/config.json"))


def load_config(path=None):
    """Defaults, overridden key by key by the JSON file (missing file = defaults)."""
    path = path or config_path()
    data = {}
    try:
        with open(path) as f:
            data = json.load(f)
    except OSError:
        pass
    cfg = _merge(DEFAULTS, data)
    cfg["state_dir"] = os.path.expanduser(cfg["state_dir"])
    cfg["lock"] = os.path.expanduser(cfg["lock"] or os.path.join(cfg["state_dir"], "heavy.lock"))
    return cfg


# ---------------------------------------------------------------- real readers

class _RUsage(ctypes.Structure):
    # struct rusage_info_v0 from <libproc.h>
    _fields_ = [("uuid", ctypes.c_uint8 * 16)] + [
        (k, ctypes.c_uint64)
        for k in ("user", "system", "idle_wkups", "intr_wkups", "pageins",
                  "wired", "resident", "footprint", "start", "exit")
    ]


_LIB = []


def _libproc():
    if not _LIB:
        try:
            _LIB.append(ctypes.CDLL("/usr/lib/libproc.dylib"))
        except OSError:
            _LIB.append(None)
    return _LIB[0]


def footprint(pid):
    """phys_footprint in bytes, or None if it cannot be read."""
    lib = _libproc()
    if lib is None:
        return None
    r = _RUsage()
    if lib.proc_pid_rusage(int(pid), 0, ctypes.byref(r)) != 0:
        return None
    return r.footprint


def parse_sysctl(lines):
    """Parse `sysctl -n hw.memsize kern.memorystatus_level
    kern.memorystatus_vm_pressure_level vm.swapusage` output."""
    total = int(lines[0])
    level = int(lines[1])
    pressure = {1: "normal", 2: "warn", 4: "critical"}.get(int(lines[2]), lines[2])
    mt = re.search(r"used = ([0-9.]+)M", lines[3])
    swap_gb = float(mt.group(1)) / 1024 if mt else 0.0
    return {
        "total_gb": total / GB,
        "level_pct": level,
        "avail_gb": total / GB * level / 100.0,
        "pressure": pressure,
        "swap_gb": swap_gb,
    }


def parse_ps(text, me, fp=footprint):
    """Rows from `ps -axo pid=,ppid=,rss=,user=,command=`."""
    rows = []
    for line in text.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid, ppid, rss, user, cmd = int(parts[0]), int(parts[1]), int(parts[2]), parts[3], parts[4]
        mine = user == me
        f = fp(pid) if mine else None
        mem = f if f is not None else rss * 1024
        rows.append({"pid": pid, "ppid": ppid, "user": user, "cmd": cmd,
                     "mem_gb": mem / GB, "mine": mine})
    return rows


class Probe(object):
    """Reads the real machine. Tests pass an object with the same two methods."""

    def system(self):
        out = subprocess.run(
            ["sysctl", "-n", "hw.memsize", "kern.memorystatus_level",
             "kern.memorystatus_vm_pressure_level", "vm.swapusage"],
            capture_output=True, text=True, timeout=10).stdout.splitlines()
        return parse_sysctl(out)

    def processes(self):
        me = os.environ.get("USER") or ""
        out = subprocess.run(["ps", "-axo", "pid=,ppid=,rss=,user=,command="],
                             capture_output=True, text=True, timeout=10).stdout
        return parse_ps(out, me)


# ---------------------------------------------------------------- pure helpers

def descendants(rows, root):
    kids = {}
    for r in rows:
        kids.setdefault(r["ppid"], []).append(r["pid"])
    out, todo = set(), [root]
    while todo:
        p = todo.pop()
        if p in out:
            continue
        out.add(p)
        todo.extend(kids.get(p, []))
    return out


def ancestors(rows, pid):
    parent = dict((r["pid"], r["ppid"]) for r in rows)
    out = []
    seen = set()
    while pid in parent and pid not in seen and pid > 1:
        seen.add(pid)
        pid = parent[pid]
        out.append(pid)
    return out


def is_protected(cfg, cmd):
    return any(re.search(p, cmd) for p in cfg["protect_regex"])


def is_job(cfg, row, self_pid=None):
    """A process the guard may count or stop: mine, matches job_regex, not protected."""
    if not row["mine"] or row["pid"] == (self_pid if self_pid is not None else os.getpid()):
        return False
    cmd = row["cmd"]
    if is_protected(cfg, cmd):
        return False
    return any(re.search(p, cmd) for p in cfg["job_regex"])


def short(cmd, n=110):
    first, _, rest = cmd.partition(" ")
    if first.startswith("/") and ("/Python" in first or "/python" in first):
        cmd = os.path.basename(first) + (" " + rest if rest else "")
    cmd = cmd.replace(os.path.expanduser("~"), "~")
    return cmd if len(cmd) <= n else cmd[: n - 3] + "..."


def top_lines(rows, n=6):
    rows = sorted(rows, key=lambda r: -r["mem_gb"])[:n]
    return ["%5.1f GB  pid %-6d %s" % (r["mem_gb"], r["pid"], short(r["cmd"], 90)) for r in rows]


def status_line(s):
    return "%.1f GB available (%d %%), pressure %s, swap %.1f GB" % (
        s["avail_gb"], s["level_pct"], s["pressure"], s["swap_gb"])


def log(path, msg, max_bytes=5 * 1024 * 1024):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    try:
        if os.path.getsize(path) > max_bytes:
            os.replace(path, path + ".1")
    except OSError:
        pass
    with open(path, "a") as f:
        f.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))


def alert(cfg, msg):
    """Run alert_cmd with the message as its last argument; never blocks the caller."""
    cmd = cfg.get("alert_cmd") or []
    if not cmd or os.environ.get("MEMGUARD_NO_ALERT"):
        return False
    try:
        subprocess.Popen([os.path.expanduser(cmd[0])] + list(cmd[1:]) + [msg],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        return True
    except OSError:
        return False
