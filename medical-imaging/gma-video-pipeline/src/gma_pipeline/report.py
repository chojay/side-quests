"""Markdown report generation from features + scoring.

Produces a self-contained .md document with the run config hash, hardware,
disclaimer, per-keypoint kinematic summary table, MOS-R proxy subscale
scores, asymmetry findings, plain-language interpretation, and inline
PNG plots.
"""

from __future__ import annotations

import logging
import platform
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gma_pipeline.features import VideoFeatures
from gma_pipeline.scoring import ScoringResult
from gma_pipeline.mos_r import MOSRProxy, POPULATION_CUTOFFS

logger = logging.getLogger(__name__)


DISCLAIMER_HEADER = """
> **NOT A MEDICAL DEVICE.** This report is a personal-reference exploration of
> pose-derived kinematic features. It is not a GMA score. It is not validated.
> Clinical interpretation rests entirely with the infant's clinical care team.
> See `DISCLAIMER.md` for the full disclaimer.
""".strip()


def _plot_velocity_time_series(parquet_path: Path, output_path: Path, fps: float) -> None:
    """Plot velocity magnitude over time for left vs right wrists and ankles."""
    df = pd.read_parquet(parquet_path)
    keypoints = ["left_wrist", "right_wrist", "left_ankle", "right_ankle"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 6), sharex=True)
    axes_flat = axes.flatten()
    for ax, kp in zip(axes_flat, keypoints):
        sub = df[df["keypoint"] == kp].sort_values("frame_idx")
        if sub.empty:
            ax.set_title(f"{kp} (no data)")
            continue
        valid = sub[sub["confidence"] >= 0.3]
        if valid.empty:
            ax.set_title(f"{kp} (no valid frames)")
            continue
        # Compute speed via finite difference
        x = valid["x"].values
        y = valid["y"].values
        frames = valid["frame_idx"].values
        if len(x) < 3:
            ax.set_title(f"{kp} (too few frames)")
            continue
        dt = np.diff(frames) / fps
        dt[dt == 0] = 1 / fps
        dx = np.diff(x)
        dy = np.diff(y)
        speed = np.sqrt(dx ** 2 + dy ** 2) / dt
        t = frames[1:] / fps
        ax.plot(t, speed, linewidth=0.6)
        ax.set_title(kp)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("speed (px/s)")
        ax.grid(True, alpha=0.3)
    fig.suptitle("Keypoint speed over time")
    fig.tight_layout()
    fig.savefig(output_path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def _plot_symmetry(features: VideoFeatures, output_path: Path) -> None:
    """Bar chart of per-pair symmetry indices."""
    items = list(features.symmetry.items())
    if not items:
        return
    pairs = [k.replace("__vs__", " vs ") for k, _ in items]
    si_values = [v.speed_symmetry_index if np.isfinite(v.speed_symmetry_index) else 0.0 for _, v in items]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ["#3b82f6" if 0.8 <= si <= 1.25 else "#ef4444" for si in si_values]
    ax.barh(pairs, si_values, color=colors)
    ax.axvline(1.0, color="#6b7280", linestyle="--", linewidth=1)
    ax.axvspan(0.8, 1.25, alpha=0.10, color="#9ca3af", label="literature casual-movement band (NOT diagnostic)")
    ax.set_xlabel("Symmetry index (left / right speed) - magnitude alone is NOT diagnostic")
    ax.set_title("Left-vs-right symmetry per keypoint pair")
    ax.legend(loc="lower right")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def _plot_fft(parquet_path: Path, output_path: Path, fps: float) -> None:
    """FFT magnitude for left vs right wrist x-velocity."""
    df = pd.read_parquet(parquet_path)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for kp, color in [("left_wrist", "#16a34a"), ("right_wrist", "#ea580c")]:
        sub = df[df["keypoint"] == kp].sort_values("frame_idx")
        valid = sub[sub["confidence"] >= 0.3]
        if len(valid) < 64:
            continue
        x = valid["x"].values
        frames = valid["frame_idx"].values
        if len(np.unique(frames)) < 64:
            continue
        # Reindex to a uniform grid
        n_full = int(frames.max()) + 1
        x_full = np.full(n_full, np.nan)
        for fi, xv in zip(frames, x):
            x_full[fi] = xv
        # Interpolate NaNs
        good = np.isfinite(x_full)
        x_full = np.interp(np.arange(n_full), np.where(good)[0], x_full[good])
        vel = np.diff(x_full) * fps
        n = len(vel)
        spec = np.abs(np.fft.rfft(vel - vel.mean()))
        freqs = np.fft.rfftfreq(n, 1 / fps)
        ax.plot(freqs, spec, label=kp, color=color, linewidth=0.9)
    ax.set_xlim(0, 6)
    ax.axvspan(1.0, 3.0, alpha=0.10, color="#16a34a", label="fidgety band 1 to 3 Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("FFT magnitude")
    ax.set_title("Wrist x-velocity FFT")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def _confidence_emoji(label: str) -> str:
    return {
        "HIGH": "[HIGH]",
        "MODERATE": "[MOD]",
        "LOW": "[LOW]",
        "NOT_IMPLEMENTED": "[N/A]",
    }.get(label, label)


def build_report(
    features: VideoFeatures,
    scoring: ScoringResult,
    parquet_path: Path,
    output_dir: Path,
    clinician_reading_pending: bool = False,
    mosr: MOSRProxy | None = None,
) -> Path:
    """Render the full markdown report. Returns the report path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    try:
        _plot_velocity_time_series(parquet_path, plots_dir / "velocity_time_series.png", features.fps)
    except Exception as exc:
        logger.warning("velocity plot failed: %s", exc)
    try:
        _plot_symmetry(features, plots_dir / "symmetry.png")
    except Exception as exc:
        logger.warning("symmetry plot failed: %s", exc)
    try:
        _plot_fft(parquet_path, plots_dir / "wrist_fft.png", features.fps)
    except Exception as exc:
        logger.warning("FFT plot failed: %s", exc)

    lines: list[str] = []
    lines.append(f"# GMA Evaluation Report - {features.video_id}")
    lines.append("")
    lines.append(DISCLAIMER_HEADER)
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"**Scoring version:** `{scoring.scoring_version}`")
    lines.append(f"**Hardware:** {platform.machine()} / Python {sys.version.split()[0]}")
    lines.append("")

    # Pose extract summary
    lines.append("## Pose extraction summary")
    lines.append("")
    lines.append(f"- **Frames:** {features.n_frames} ({features.duration_seconds:.1f} s at {features.fps:g} fps)")
    lines.append(f"- **Detected frames in analysis window:** {features.n_detected_frames} ({features.detection_rate*100:.1f}%)")
    lines.append(f"- **Median rotation applied:** {features.rotation_applied_median:.1f} deg")
    lines.append(f"- **Frame diagonal:** {features.frame_diagonal_pixels:.0f} px")
    fps = features.fps or 30.0
    if features.valid_segments:
        seg_str = ", ".join(f"{a/fps:.1f}-{b/fps:.1f}s" for a, b in features.valid_segments)
        lines.append(
            f"- **Valid supine frames:** {features.n_valid_supine_frames}/{features.n_frames} "
            f"({features.valid_supine_fraction*100:.1f}%) across {len(features.valid_segments)} segment(s): {seg_str}."
        )
        if features.n_invalid_segments:
            lines.append(
                f"- **Excluded (rolling/side-lying/prone):** {features.n_invalid_segments} segment(s); per-frame "
                "supine-validity mask (bi-acromial width collapse + signed shoulder-offset sign-flip, bi-iliac "
                "corroboration). Every rolling/prone frame is excluded, not just a trailing truncation, so kinematics "
                "are computed only on genuine supine activity."
            )
    else:
        lines.append(f"- **Analysis window:** full recording (frames 0..{features.n_frames}).")
    lines.append("")

    # Per-keypoint kinematics table
    lines.append("## Per-keypoint kinematics")
    lines.append("")
    lines.append("| Keypoint | valid % | mean conf | mean speed (px/s) | dom freq (Hz) | NJI | vel entropy |")
    lines.append("|----------|---------|-----------|-------------------|---------------|------|-------------|")
    for kp_name, kk in features.keypoints.items():
        nji_str = f"{kk.normalized_jerk_index:.2e}" if np.isfinite(kk.normalized_jerk_index) else "nan"
        lines.append(
            f"| {kp_name} | {kk.fraction_valid*100:.1f}% | {kk.mean_confidence:.3f} | "
            f"{kk.speed_mean:.1f} | {kk.dominant_freq_hz:.2f} | {nji_str} | {kk.velocity_entropy:.2f} |"
        )
    lines.append("")

    # MOS-R PROXY (honest: only F and C are computable from 2D pose)
    if mosr is not None:
        lines.append("## MOS-R PROXY (exploratory, non-clinical)")
        lines.append("")
        lines.append(
            "> The real MOS-R sums 5 subscales to 5-28. Only **Fidgety (F, 12/4/1)** and **Movement Character "
            "(C, 4/2/1)** are even partially derivable from a 13-keypoint 2D skeleton (max 16 of 28). Observed "
            "Patterns (P), Age-adequate Repertoire (R) and Postural (Po) require human Gestalt and are NOT computable here."
        )
        lines.append("")
        lines.append("| MOS-R subscale | Max | Proxy points | Computable | Confidence |")
        lines.append("|----------------|-----|--------------|------------|------------|")
        for code in ("F", "P", "R", "Po", "C"):
            s = mosr.subscales[code]
            pts = "clinician-only" if s.points is None else f"{s.points:g}"
            lines.append(f"| {s.code} - {s.name} | {s.max_points} | {pts} | {s.computable} | {_confidence_emoji(s.confidence)} |")
        lines.append("")
        lines.append(
            f"- **Computable proxy (F+C):** {mosr.computable_total:g} of {mosr.computable_max} "
            f"(the rest of the 28 needs a certified assessor)."
        )
        lines.append(
            f"- **Upper bound on full MOS-R:** {mosr.upper_bound_28:g}/28 (P/R/Po imputed at ceiling 4/4/4). "
            "The true MOS-R is **<= this number** by an unknown margin - never a point estimate."
        )
        lines.append(
            f"- **Repertoire-richness descriptor (NOT a P/R score):** mean velocity entropy "
            f"{mosr.repertoire_richness_descriptor:.2f} nats."
        )
        lines.append("")
        lines.append("> Read the **independent segmental asymmetry** analysis as the headline, not this total. A "
                     "near-normal whole-body proxy total is NOT reassurance - it can reflect the proxy's blindness to "
                     "the character/posture/repertoire channels, and a focal deficit can herald a unilateral lesion. "
                     "See `segmental-asymmetry-independent.md`.")
        lines.append("")

    # Kinematic descriptor subscales (the original 0-5 heuristics; NOT MOS-R points)
    lines.append("## Kinematic descriptor subscales (0 to 5; internal, NOT MOS-R points)")
    lines.append("")
    lines.append("| Descriptor | Score (0 to 5) | Confidence | Rationale |")
    lines.append("|----------|----------------|------------|-----------|")
    for name, s in scoring.subscales.items():
        score_str = "n/a" if not np.isfinite(s.score_0_to_5) else f"{s.score_0_to_5:.2f}"
        lines.append(
            f"| {name} | {score_str} | {_confidence_emoji(s.confidence)} | {s.rationale} |"
        )
    operational = [v for v in (s.score_0_to_5 for s in scoring.subscales.values()) if np.isfinite(v)]
    if operational:
        lines.append("")
        lines.append(f"**Kinematic descriptor sum:** {scoring.global_proxy_score:.2f} (sum of {len(operational)} 0-5 descriptors; max {len(operational)*5}). This is an internal kinematic summary, NOT a MOS-R total.")
    lines.append("")

    # Asymmetry findings
    lines.append("## Asymmetry findings")
    lines.append("")
    lines.append("| Pair | Symmetry index | Direction | Severity | Flagged |")
    lines.append("|------|----------------|-----------|----------|---------|")
    for a in scoring.asymmetry_findings:
        si_str = "nan" if not np.isfinite(a.symmetry_index) else f"{a.symmetry_index:.2f}"
        lines.append(
            f"| {a.pair} | {si_str} | {a.direction} | {a.severity} | {'YES' if a.flagged else 'no'} |"
        )
    lines.append("")

    # Interpretation
    lines.append("## Interpretation")
    lines.append("")
    lines.append(scoring.interpretation)
    lines.append("")

    # Plots
    lines.append("## Plots")
    lines.append("")
    if (plots_dir / "velocity_time_series.png").exists():
        lines.append("### Velocity time series (wrists and ankles)")
        lines.append("")
        lines.append("![velocity](plots/velocity_time_series.png)")
        lines.append("")
    if (plots_dir / "symmetry.png").exists():
        lines.append("### Symmetry per paired keypoint")
        lines.append("")
        lines.append("![symmetry](plots/symmetry.png)")
        lines.append("")
    if (plots_dir / "wrist_fft.png").exists():
        lines.append("### Wrist FFT (left vs right)")
        lines.append("")
        lines.append("![fft](plots/wrist_fft.png)")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "> **Independent assessment.** This pipeline produces its OWN independent, within-subject relative per-limb "
        "assessment from pose kinematics - a ranking of how much each limb stands out as slower-than-its-pair AND "
        "lower-variety-than-peers, plus a conservative caveated flag. It is NOT calibrated to any external reading. "
        "Any transcribed clinician reading is carried "
        "only as a clearly-labeled PROVISIONAL side-note, not a reference standard. See "
        "`segmental-asymmetry-independent.md`. Every number remains a PROXY; final clinical interpretation rests with "
        "the care team."
    )
    lines.append("")

    out = output_dir / f"{features.video_id}-gma-report.md"
    out.write_text("\n".join(lines))
    return out


def build_segmental_report(analysis, output_dir: Path) -> Path:
    """Render the cross-video INDEPENDENT relative segmental assessment (+ provisional PT side-note)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    L: list[str] = []
    L.append("# Segmental Asymmetry - Independent Relative Assessment")
    L.append("")
    L.append(DISCLAIMER_HEADER)
    L.append("")
    L.append(f"**Generated:** {datetime.now().isoformat(timespec='seconds')}")
    L.append(f"**Version:** `{analysis.version}`")
    L.append(f"**Videos analyzed:** {', '.join(analysis.videos)}")
    L.append("")
    L.append("> " + analysis.independence_note)
    L.append("")
    L.append("## 1. Independent relative ranking (headline)")
    L.append("")
    L.append(analysis.ranking_summary)
    L.append("")
    L.append(
        "Each of this infant's 12 paired keypoints is compared to (a) its contralateral pair and (b) the other limbs. "
        "`% vs pair` = how much slower this keypoint is than its partner (positive = slower); `slower in` = the videos "
        "in which it is the slower side; `variety pct` = its movement-variety rank among the 12 (low = moves less "
        "variably than peers); `standout` combines the two (1.0 = stands out most as slow AND low-variety). No external "
        "reference is used."
    )
    L.append("")
    L.append("| Rank | Keypoint | % vs pair (median) | slower in | variety pct | low-variety | standout | flag |")
    L.append("|------|----------|--------------------|-----------|-------------|-------------|----------|------|")
    for f in analysis.findings:  # already sorted by standout_rank
        dpct = "nan" if not np.isfinite(f.contralateral_deficit_pct) else f"{f.contralateral_deficit_pct:+.0f}%"
        vpct = "nan" if not np.isfinite(f.entropy_percentile) else f"{f.entropy_percentile*100:.0f}th"
        so = "nan" if not np.isfinite(f.standout_score) else f"{f.standout_score:.2f}"
        L.append(
            f"| {f.standout_rank} | {f.keypoint} | {dpct} | {f.deficit_consistent_videos}/{f.n_videos_with_si} vids | "
            f"{vpct} | {'yes' if f.low_variety else 'no'} | {so} | {'**FLAG**' if f.pipeline_flag else '-'} |"
        )
    L.append("")
    L.append("## 2. Conservative binary flag (caveated)")
    L.append("")
    L.append(analysis.flag_summary)
    L.append("")
    L.append("## 3. External clinician reading (side-note only - NOT ground truth)")
    L.append("")
    L.append("> " + analysis.pt_provisional_summary)
    L.append("")
    L.append(
        "- **Window note:** the fidgety period is optimal at 12-16 weeks and valid to ~20 weeks; FMs normally fade at "
        "18-20 weeks (Ferrari 2016). Validity is keyed to corrected age AT RECORDING, not any later scoring date. "
        "\"Poor repertoire\" is formally a writhing-stage whole-body category, not a fidgety-stage or per-limb label."
    )
    L.append("")
    s = analysis.pt_provisional_agreement
    L.append(
        f"- **Provisional coincidence (NOT validation):** both-flagged={s['both_flag']}, both-clear={s['both_clear']}, "
        f"pipeline-only={s['pipeline_only']}, PT-only={s['pt_only']}. The pipeline is NOT calibrated to this reading and "
        "the reading is NOT confirmed, so this is not evidence for either the pipeline or the reading."
    )
    L.append("")
    L.append("## Interpretation and limitations")
    L.append("")
    L.append(analysis.notes)
    L.append("")
    L.append("## Population MOS-R cutoffs (context only - this pipeline does not produce a MOS-R)")
    L.append("")
    L.append("| Population | Threshold | Note | Source |")
    L.append("|-----------|-----------|------|--------|")
    for co in POPULATION_CUTOFFS:
        L.append(f"| {co['population']} | {co['threshold']} | {co['note']} | {co['source']} |")
    L.append("")
    out = output_dir / "segmental-asymmetry-independent.md"
    out.write_text("\n".join(L))
    return out
