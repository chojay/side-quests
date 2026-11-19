"""Fake machine for tests: memory numbers are injected, nothing reads the real system."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import memlib  # noqa: E402

GB_TOTAL = 64.0


def sysinfo(avail_gb=40.0, pressure="normal", swap_gb=0.0):
    level = int(round(avail_gb / GB_TOTAL * 100))
    return {"total_gb": GB_TOTAL, "level_pct": level, "avail_gb": avail_gb,
            "pressure": pressure, "swap_gb": swap_gb}


def row(pid, cmd, mem_gb, ppid=1, mine=True):
    return {"pid": pid, "ppid": ppid, "user": "me" if mine else "other", "cmd": cmd,
            "mem_gb": mem_gb, "mine": mine}


class FakeProbe(object):
    """system() and processes() return whatever the test sets; callables are called."""

    def __init__(self, system=None, rows=None):
        self._system = system if system is not None else sysinfo()
        self._rows = rows if rows is not None else []
        self.calls = 0

    def system(self):
        self.calls += 1
        return self._system() if callable(self._system) else self._system

    def processes(self):
        r = self._rows() if callable(self._rows) else self._rows
        if isinstance(r, Exception):
            raise r
        return r


def make_config(tmpdir, **over):
    cfg = memlib.load_config(os.path.join(tmpdir, "missing.json"))
    cfg["state_dir"] = tmpdir
    cfg["lock"] = os.path.join(tmpdir, "heavy.lock")
    for k, v in over.items():
        cfg[k].update(v)
    return cfg
