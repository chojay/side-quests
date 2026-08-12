#!/usr/bin/env python3
"""Construction-noise monitor: camera video/audio -> acoustic timeline report.

Months of construction next door meant one question kept coming up: how loud,
how often, and inside or outside working hours? This tool answers it with
data. It takes a folder of home-camera clips (video or audio), extracts the
audio track, and produces:

  - a windowed RMS level timeline (dBFS) per clip
  - noise-event detection (adaptive baseline + hysteresis + min duration)
  - a spectrogram per clip (band character: machinery vs broadband)
  - an hour-bucketed summary across all clips, with events and loud minutes
    inside vs outside a configurable permitted-hours window

DELIBERATELY OUT OF SCOPE: speech. No transcription, no speech-to-text, no
voice content of any kind is processed or stored. The point is noise levels
and timing, not what anyone said.

CALIBRATION HONESTY: a camera microphone is uncalibrated, has AGC, and sits
wherever the camera sits. Every level here is relative dBFS (decibels below
the recording's own full scale), NOT sound-pressure dB(A). The output is
evidence of patterns and timing, not a legal noise measurement.

Timestamps come from the clip filename via --ts-regex (default matches
YYYYMMDD_HHMMSS anywhere in the name), falling back to file mtime.

Usage:
    python3 noise_monitor.py --input ./clips --out ./report
    python3 noise_monitor.py --input ./clips --out ./report \
        --permitted 08:00-18:00 --weekdays-only --threshold-db 12
"""
import argparse
import datetime as dt
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

AUDIO_EXTS = {".wav"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi"}
SR = 16000                # analysis sample rate
WIN_S = 1.0               # RMS window (seconds)
EPS = 1e-10


# ----------------------------------------------------------------- extraction
def extract_audio(path: Path, tmp_dir: Path) -> Path:
    """Extract mono 16 kHz WAV from a video container via ffmpeg."""
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH; needed to read video containers. "
                 "brew install ffmpeg, or feed .wav files directly.")
    out = tmp_dir / (path.stem + ".wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(path),
           "-vn", "-ac", "1", "-ar", str(SR), str(out)]
    subprocess.run(cmd, check=True)
    return out


def load_wav(path: Path):
    """Load a WAV as float32 mono at SR (naive resample if needed)."""
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        sw = w.getsampwidth()
        ch = w.getnchannels()
        raw = w.readframes(n)
    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sw]
    x = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    x /= float(np.iinfo(dtype).max)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        idx = np.linspace(0, len(x) - 1, int(len(x) * SR / sr))
        x = np.interp(idx, np.arange(len(x)), x).astype(np.float32)
    return x


# ------------------------------------------------------------------- analysis
def dbfs_timeline(x: np.ndarray):
    """Windowed RMS level in dBFS. Returns (times_s, levels_db)."""
    win = int(SR * WIN_S)
    n = len(x) // win
    if n == 0:
        return np.array([]), np.array([])
    seg = x[: n * win].reshape(n, win)
    rms = np.sqrt((seg ** 2).mean(axis=1))
    db = 20 * np.log10(rms + EPS)
    t = (np.arange(n) + 0.5) * WIN_S
    return t, db


def detect_events(t, db, rise_db=12.0, fall_db=6.0, min_dur_s=3.0, merge_gap_s=5.0):
    """Adaptive noise-event detection.

    Baseline = rolling median (5 min). An event opens when level exceeds
    baseline + rise_db, closes when it drops under baseline + fall_db
    (hysteresis), must last min_dur_s, and events closer than merge_gap_s
    are merged. Returns list of (t_start, t_end, peak_db, mean_db).
    """
    if len(db) == 0:
        return []
    k = max(1, int(300 / WIN_S))
    pad = np.concatenate([db[:k][::-1], db, db[-k:][::-1]])
    baseline = np.array([np.median(pad[i: i + 2 * k + 1]) for i in range(len(db))])
    hi, lo = baseline + rise_db, baseline + fall_db
    events, open_i = [], None
    for i in range(len(db)):
        if open_i is None and db[i] >= hi[i]:
            open_i = i
        elif open_i is not None and db[i] < lo[i]:
            events.append((open_i, i))
            open_i = None
    if open_i is not None:
        events.append((open_i, len(db) - 1))
    merged = []
    for s, e in events:
        if merged and t[s] - t[merged[-1][1]] <= merge_gap_s:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    out = []
    for s, e in merged:
        if t[e] - t[s] >= min_dur_s:
            out.append((float(t[s]), float(t[e]),
                        float(db[s:e + 1].max()), float(db[s:e + 1].mean())))
    return out


def spectrogram_arrays(x: np.ndarray, nfft=1024, hop=512):
    """Magnitude spectrogram in dB via numpy STFT. Returns (t, f, S_db)."""
    if len(x) < nfft:
        return np.array([]), np.array([]), np.zeros((0, 0))
    win = np.hanning(nfft)
    n = 1 + (len(x) - nfft) // hop
    frames = np.stack([x[i * hop: i * hop + nfft] * win for i in range(n)])
    spec = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    s_db = 10 * np.log10(spec.T + EPS)
    t = (np.arange(n) * hop + nfft / 2) / SR
    f = np.fft.rfftfreq(nfft, 1 / SR)
    return t, f, s_db


# ----------------------------------------------------------------- timestamps
def clip_start_time(path: Path, ts_regex: str):
    m = re.search(ts_regex, path.name)
    if m:
        try:
            return dt.datetime.strptime(m.group(0), "%Y%m%d_%H%M%S")
        except ValueError:
            pass
    return dt.datetime.fromtimestamp(path.stat().st_mtime)


def parse_window(spec: str):
    a, b = spec.split("-")
    h0, m0 = map(int, a.split(":"))
    h1, m1 = map(int, b.split(":"))
    return dt.time(h0, m0), dt.time(h1, m1)


def is_permitted(ts: dt.datetime, win, weekdays_only: bool) -> bool:
    if weekdays_only and ts.weekday() >= 5:
        return False
    return win[0] <= ts.time() <= win[1]


# -------------------------------------------------------------------- reports
def plot_clip(t, db, events, spec, out_png: Path, title: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 3]})
    ax1.plot(t, db, lw=0.8, color="#1a1a19")
    for s, e, pk, _ in events:
        ax1.axvspan(s, e, color="#d55e00", alpha=0.25)
    ax1.set_ylabel("level (dBFS)")
    ax1.set_title(title)
    st, f, s_db = spec
    if s_db.size:
        ax2.imshow(s_db, origin="lower", aspect="auto",
                   extent=[st[0], st[-1], f[0], f[-1]],
                   cmap="magma", vmin=np.percentile(s_db, 20),
                   vmax=np.percentile(s_db, 99.5))
    ax2.set_ylabel("frequency (Hz)")
    ax2.set_xlabel("time (s)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=110)
    plt.close(fig)


def run(args):
    inp, out = Path(args.input), Path(args.out)
    tmp = out / "tmp"
    plots = out / "plots"
    for p in (out, tmp, plots):
        p.mkdir(parents=True, exist_ok=True)
    win = parse_window(args.permitted)

    clips = sorted(p for p in inp.iterdir()
                   if p.suffix.lower() in AUDIO_EXTS | VIDEO_EXTS)
    if not clips:
        sys.exit(f"no audio/video clips found in {inp}")

    rows, hour_stats = [], {}
    for clip in clips:
        wav = clip if clip.suffix.lower() in AUDIO_EXTS else extract_audio(clip, tmp)
        x = load_wav(wav)
        t, db = dbfs_timeline(x)
        events = detect_events(t, db, rise_db=args.threshold_db)
        spec = spectrogram_arrays(x)
        start = clip_start_time(clip, args.ts_regex)
        plot_clip(t, db, events, spec, plots / (clip.stem + ".png"),
                  f"{clip.name}  ({start:%Y-%m-%d %H:%M})")
        loud_s = sum(e - s for s, e, _, _ in events)
        rows.append((clip.name, start, len(t) * WIN_S, events, loud_s))
        for s, e, pk, _ in events:
            ev_ts = start + dt.timedelta(seconds=s)
            key = (ev_ts.date(), ev_ts.hour)
            ok = is_permitted(ev_ts, win, args.weekdays_only)
            n_ev, secs, out_secs, peak = hour_stats.get(key, (0, 0.0, 0.0, -120.0))
            hour_stats[key] = (n_ev + 1, secs + (e - s),
                               out_secs + (0.0 if ok else e - s), max(peak, pk))
        print(f"  {clip.name}: {len(events)} events, "
              f"{loud_s / 60:.1f} loud min / {len(t) * WIN_S / 60:.1f} min")

    md = ["# Construction-noise report", "",
          f"Clips analyzed: {len(rows)}. Levels are relative dBFS from an "
          "uncalibrated camera microphone: patterns and timing, not dB(A).",
          "", f"Permitted-hours window: {args.permitted}"
          + (" (weekdays only)" if args.weekdays_only else ""), "",
          "## Per clip", "",
          "| clip | start | length (min) | events | loud minutes |",
          "|---|---|---:|---:|---:|"]
    for name, start, dur, events, loud_s in rows:
        md.append(f"| {name} | {start:%Y-%m-%d %H:%M} | {dur / 60:.1f} "
                  f"| {len(events)} | {loud_s / 60:.1f} |")
    md += ["", "## By hour", "",
           "| date | hour | events | loud minutes | outside permitted | peak (dBFS) |",
           "|---|---:|---:|---:|---:|---:|"]
    for (day, hour), (n_ev, secs, out_secs, peak) in sorted(hour_stats.items()):
        flag = f"{out_secs / 60:.1f}" if out_secs else "-"
        md.append(f"| {day} | {hour:02d} | {n_ev} | {secs / 60:.1f} | {flag} | {peak:.1f} |")
    md += ["", "Plots per clip are in `plots/`.", ""]
    (out / "report.md").write_text("\n".join(md))
    print(f"report: {out / 'report.md'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="folder of camera clips (.mp4/.mov/.wav)")
    ap.add_argument("--out", required=True, help="output folder for report + plots")
    ap.add_argument("--permitted", default="08:00-18:00",
                    help="permitted work window, HH:MM-HH:MM (default 08:00-18:00)")
    ap.add_argument("--weekdays-only", action="store_true",
                    help="treat weekend events as outside the permitted window")
    ap.add_argument("--threshold-db", type=float, default=12.0,
                    help="event opens this many dB above the rolling baseline (default 12)")
    ap.add_argument("--ts-regex", default=r"\d{8}_\d{6}",
                    help="regex matching YYYYMMDD_HHMMSS in clip filenames")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
