"""v0.2 assessment visualizations.

New plots that reflect the v0.2 analysis:
  - validity timeline: bi-acromial width over time with rolling/prone segments
    shaded out (shows exactly which frames the supine-validity mask excluded),
  - segmental concordance scatter: symmetry index vs movement variety per
    keypoint, the figure that explains why the conjunction discriminator
    separates a genuinely impoverished limb from a benignly asymmetric one,
  - MOS-R proxy bars: F + C per video against the computable-16 / upper-bound-28
    reference lines.

All are matplotlib (Agg) PNGs. EVERY NUMBER IS A PROXY (see report.py disclaimer).
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gma_pipeline.features import VideoFeatures

logger = logging.getLogger(__name__)

_ABN = "#dc2626"   # pipeline abnormal
_NORM = "#2563eb"  # pipeline normal
_OK = "#16a34a"    # reference / valid
_GREY = "#9ca3af"


def _shoulder_width_series(parquet_path: Path, n_frames: int, frame_diag: float, min_conf: float = 0.3) -> np.ndarray:
    """Per-frame bi-acromial (shoulder-shoulder) width normalized by frame diagonal."""
    df = pd.read_parquet(parquet_path)
    out = np.full(n_frames, np.nan)
    ls = df[(df["keypoint"] == "left_shoulder") & (df["confidence"] >= min_conf)].set_index("frame_idx")
    rs = df[(df["keypoint"] == "right_shoulder") & (df["confidence"] >= min_conf)].set_index("frame_idx")
    common = ls.index.intersection(rs.index)
    for fi in common:
        i = int(fi)
        if 0 <= i < n_frames:
            out[i] = float(np.hypot(ls.loc[fi, "x"] - rs.loc[fi, "x"], ls.loc[fi, "y"] - rs.loc[fi, "y"])) / frame_diag
    return out


def plot_validity_timeline(parquet_path: Path, features: VideoFeatures, output_path: Path) -> None:
    """Bi-acromial width over time; rolling/prone (excluded) segments shaded red."""
    fps = features.fps or 30.0
    n_frames = features.n_frames
    width = _shoulder_width_series(parquet_path, n_frames, features.frame_diagonal_pixels)
    t = np.arange(n_frames) / fps
    median = float(np.nanmedian(width)) if np.isfinite(width).any() else 0.0

    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.plot(t, width, linewidth=0.7, color="#374151", label="bi-acromial width / frame diagonal")
    ax.axhline(median, color=_OK, linestyle="--", linewidth=1, label=f"supine median {median:.3f}")
    ax.axhline(0.65 * median, color=_ABN, linestyle=":", linewidth=1, label="collapse threshold (0.65x median)")

    # Shade EXCLUDED (invalid) frames red: everything not inside a valid segment.
    valid = np.zeros(n_frames, dtype=bool)
    for a, b in features.valid_segments:
        valid[a:b] = True
    first_excl = True
    for a, b in _invalid_runs(valid):
        ax.axvspan(a / fps, b / fps, color=_ABN, alpha=0.16,
                   label="excluded (roll/prone)" if first_excl else None)
        first_excl = False

    ax.set_xlabel("time (s)")
    ax.set_ylabel("shoulder width (norm)")
    ax.set_title(
        f"{features.video_id} - supine-validity timeline "
        f"({features.valid_supine_fraction * 100:.0f}% valid, {features.n_invalid_segments} excluded segment(s))"
    )
    ax.legend(loc="lower left", fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def _invalid_runs(valid: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    n = len(valid)
    i = 0
    while i < n:
        if not valid[i]:
            j = i
            while j < n and not valid[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def plot_segmental_concordance(analysis, output_path: Path) -> None:
    """Scatter of symmetry index vs movement variety per keypoint - the headline.

    Color = the PIPELINE's own assessment (red = pipeline flags abnormal). Marker
    = the PT assessment (star = PT abnormal). A black edge marks keypoints where
    the two assessments DIFFER. Shows why the pipeline flags the distal right arm
    (high SI = right reduced AND low entropy) but not the benignly-slow legs (low
    SI but NORMAL/high entropy).
    """
    from matplotlib.lines import Line2D

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axvline(1.0, color=_GREY, linestyle="--", linewidth=1)
    ax.axhline(analysis.entropy_threshold, color="#b45309", linestyle=":", linewidth=1.2,
               label=f"low-variety threshold (bottom tertile {analysis.entropy_threshold:.2f} nats)")

    for f in analysis.findings:
        if not (np.isfinite(f.si_median) and np.isfinite(f.mean_velocity_entropy)):
            continue
        color = _ABN if f.pipeline_flag else _NORM
        marker = "*" if f.pt_assessment_provisional == "abnormal" else "o"
        differ = f.pt_agreement_provisional is False
        ax.scatter(
            f.si_median, f.mean_velocity_entropy,
            c=color, marker=marker, s=320 if marker == "*" else 130,
            edgecolors="black" if differ else color, linewidths=1.8 if differ else 0.0,
            zorder=3, alpha=0.9,
        )
        ax.annotate(f.keypoint.replace("_", " "), (f.si_median, f.mean_velocity_entropy),
                    fontsize=7.5, xytext=(4, 4), textcoords="offset points")

    ax.set_xlabel("Symmetry index  (left/right speed;  >1 = right reduced,  <1 = left reduced)")
    ax.set_ylabel("Mean velocity entropy (movement variety, nats)")
    ax.set_title("Independent pipeline flag (color) with provisional clinician reading (marker), per keypoint")
    handles = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor=_ABN, markersize=11, label="pipeline flag: yes"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=_NORM, markersize=11, label="pipeline flag: no"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor=_GREY, markersize=15, label="provisional PT: abnormal"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=_GREY, markersize=11, label="provisional PT: normal"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=_GREY, markeredgecolor="black", markersize=11, label="pipeline / provisional-PT differ"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    s = analysis.pt_provisional_agreement
    ax.text(
        0.02, 0.02,
        "INDEPENDENT: pipeline flag = consistent contralateral speed deficit AND low variety (within-subject).\n"
        f"Provisional-PT coincidence (NOT validation): both-flag={s['both_flag']}, both-clear={s['both_clear']}, "
        f"pipeline-only={s['pipeline_only']}, PT-only={s['pt_only']}.",
        transform=ax.transAxes, fontsize=8, va="bottom",
        bbox=dict(boxstyle="round", facecolor="#f3f4f6", alpha=0.9),
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_mosr_summary(mosr_by_video: dict, output_path: Path) -> None:
    """Grouped bars of MOS-R proxy F+C per video vs computable-16 and upper-bound-28 lines."""
    videos = list(mosr_by_video.keys())
    f_pts = [mosr_by_video[v].subscales["F"].points or 0.0 for v in videos]
    c_pts = [mosr_by_video[v].subscales["C"].points or 0.0 for v in videos]
    x = np.arange(len(videos))

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(x, f_pts, width=0.55, color="#4f46e5", label="Fidgety (F, max 12)")
    ax.bar(x, c_pts, width=0.55, bottom=f_pts, color="#06b6d4", label="Movement Character (C, max 4)")
    ax.axhline(16, color=_OK, linestyle="--", linewidth=1, label="computable max (F+C = 16)")
    ax.axhline(28, color=_GREY, linestyle=":", linewidth=1, label="MOS-R upper bound (P/R/Po at ceiling = 28)")
    for i, (fp, cp) in enumerate(zip(f_pts, c_pts)):
        ax.text(i, fp + cp + 0.4, f"{fp + cp:g}/16", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(videos)
    ax.set_ylim(0, 30)
    ax.set_ylabel("MOS-R PROXY points")
    ax.set_title("MOS-R PROXY (computable F+C only; P/R/Po are clinician-only)")
    ax.legend(loc="upper center", fontsize=8, ncol=2)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
