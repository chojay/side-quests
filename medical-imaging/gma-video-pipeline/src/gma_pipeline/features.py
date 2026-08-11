"""Kinematic feature extraction from pose keypoint parquets.

Operates entirely on the parquet output of pose-extract. No video re-reading,
no model inference - pure signal processing on the (x, y, confidence) time
series per keypoint.

Feature families (INSPIRED BY, not a faithful copy of, the GigaScience 2024 open
GMA pipeline - Groos et al., giag003). That pipeline deliberately used position/
velocity/acceleration, bilateral cross-correlation, entropy, and JOINT-ANGLE
features (rotation/scale-robust) and EXCLUDED jerk and frequency/spectral features
to avoid overfitting FM-specific signals. This pipeline diverges: it adds jerk
(normalized jerk index) and a dominant-frequency feature, and uses raw 2D pixel
speed rather than joint angles - the divergent features are also the least
validated (see per-function notes below):
- Per-keypoint position, velocity (1st), acceleration (2nd), jerk (3rd)
- Amplitude statistics (mean, std, IQR, p95)
- Speed statistics (mean, std, p95)
- Smoothness via normalized jerk index (lower = smoother)
- Variability via Shannon entropy of velocity magnitude
- Left/right symmetry indices (paired keypoints)
- Inter-limb cross-correlation (cramped-synchronized signal)
- Frequency content via FFT (dominant frequency, spectral entropy)
- Periodicity via autocorrelation peak prominence

All computations are confidence-weighted where it matters: low-confidence
frames are masked out so noise from missed detections doesn't dominate the
statistics.

The unit of analysis is the *fidgety period as a whole* - we aggregate
across the entire video, not per-frame.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal as sp_signal
from scipy import stats as sp_stats

logger = logging.getLogger(__name__)


# Keypoint pairs for symmetry/cross-correlation analysis
PAIRED_KEYPOINTS = [
    ("left_shoulder", "right_shoulder"),
    ("left_elbow", "right_elbow"),
    ("left_wrist", "right_wrist"),
    ("left_hip", "right_hip"),
    ("left_knee", "right_knee"),
    ("left_ankle", "right_ankle"),
]

# Default minimum confidence to count a keypoint sample
DEFAULT_MIN_CONFIDENCE = 0.30

# Fidgety low-frequency band (Hz). UNVALIDATED HEURISTIC - no primary GMA source
# assigns a Hz value to fidgety movements (they are defined qualitatively as
# small, moderate-speed, VARIABLE-acceleration, multidirectional). Used only as a
# coarse in-band-ENERGY gate, never as a sharp-peak reward. Single shared band.
_FIDGETY_BAND_HZ = (1.0, 4.0)

# Trunk keypoints used for rolling-event detection
TRUNK_KEYPOINTS = ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]

# The 13 real body keypoints (excludes the __nodetection__ sentinel). Used to
# compute a per-frame mean detection confidence for the supine-validity mask.
_REAL_KEYPOINTS = (
    "nose",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
)


def _keypoint_xy_interp(df: pd.DataFrame, keypoint: str, n_frames: int, min_conf: float = DEFAULT_MIN_CONFIDENCE) -> tuple[np.ndarray, np.ndarray]:
    """Per-frame (x, y) for one keypoint, linearly interpolated across NaN gaps."""
    x = np.full(n_frames, np.nan)
    y = np.full(n_frames, np.nan)
    sub = df[(df["keypoint"] == keypoint) & (df["confidence"] >= min_conf)].sort_values("frame_idx")
    for _, r in sub.iterrows():
        i = int(r["frame_idx"])
        if 0 <= i < n_frames:
            x[i] = float(r["x"])
            y[i] = float(r["y"])
    good = np.isfinite(x)
    if good.sum() < 2:
        return x, y
    idxs = np.where(good)[0]
    x = np.interp(np.arange(n_frames), idxs, x[idxs])
    y = np.interp(np.arange(n_frames), idxs, y[idxs])
    return x, y


def trunk_angle_series(df: pd.DataFrame, n_frames: int, smoothing_seconds: float = 1.0, fps: float = 30.0) -> np.ndarray:
    """Trunk principal-axis angle per frame, in degrees from vertical.

    The trunk is defined as the vector from hip midpoint to shoulder midpoint.
    Angle convention: 0 degrees means the trunk points straight up in the
    image (head above hips); positive degrees means tilted clockwise in
    image space; range is (-180, 180].

    Smoothed with a moving-average window so single-frame keypoint jitter
    doesn't dominate.
    """
    ls_x, ls_y = _keypoint_xy_interp(df, "left_shoulder", n_frames)
    rs_x, rs_y = _keypoint_xy_interp(df, "right_shoulder", n_frames)
    lh_x, lh_y = _keypoint_xy_interp(df, "left_hip", n_frames)
    rh_x, rh_y = _keypoint_xy_interp(df, "right_hip", n_frames)
    sh_mx = (ls_x + rs_x) / 2.0
    sh_my = (ls_y + rs_y) / 2.0
    hp_mx = (lh_x + rh_x) / 2.0
    hp_my = (lh_y + rh_y) / 2.0
    # Vector from hip to shoulder. Image y points down, so 'up' = negative y.
    # atan2(vx, -vy) returns 0 when vector points straight up.
    vx = sh_mx - hp_mx
    vy = sh_my - hp_my
    angles = np.degrees(np.arctan2(vx, -vy))
    # Smooth
    window = max(1, int(round(smoothing_seconds * fps)))
    if window > 1:
        # Use a centered moving average; for endpoints, fall back to a shorter window.
        kernel = np.ones(window) / window
        # Mask NaN by filling with last-known value temporarily
        finite_mask = np.isfinite(angles)
        if finite_mask.any():
            angles_filled = pd.Series(angles).ffill().bfill().to_numpy()
            smoothed = np.convolve(angles_filled, kernel, mode="same")
            angles = np.where(finite_mask, smoothed, np.nan)
    return angles


def _angle_diff(a: float, b: float) -> float:
    """Signed minimal angular difference (a - b) wrapped to (-180, 180]."""
    diff = (a - b + 180.0) % 360.0 - 180.0
    return diff


def _trunk_speed_series(df: pd.DataFrame, n_frames: int, fps: float, min_conf: float = DEFAULT_MIN_CONFIDENCE) -> np.ndarray:
    """Mean speed (px/s) across the four trunk keypoints, indexed by frame_idx.

    Linearly interpolates short gaps to keep the speed time series continuous.
    Returns a length-n_frames array; NaN where all trunk keypoints are missing.
    """
    speeds: list[np.ndarray] = []
    for kp in TRUNK_KEYPOINTS:
        sub = df[(df["keypoint"] == kp) & (df["confidence"] >= min_conf)].sort_values("frame_idx")
        if len(sub) < 2:
            continue
        x = np.full(n_frames, np.nan)
        y = np.full(n_frames, np.nan)
        for _, r in sub.iterrows():
            i = int(r["frame_idx"])
            x[i] = float(r["x"])
            y[i] = float(r["y"])
        good = np.isfinite(x)
        if good.sum() < 2:
            continue
        idxs = np.where(good)[0]
        x = np.interp(np.arange(n_frames), idxs, x[idxs])
        y = np.interp(np.arange(n_frames), idxs, y[idxs])
        sp = np.zeros(n_frames)
        sp[1:] = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2) * fps
        speeds.append(sp)
    if not speeds:
        return np.full(n_frames, np.nan)
    return np.nanmean(np.stack(speeds), axis=0)


@dataclass
class RollingEvent:
    """Result of rolling-event detection."""

    detected: bool
    roll_start_frame: int | None  # First frame considered part of the roll. None if not detected.
    median_trunk_speed: float
    threshold_used: float
    safety_margin_frames: int
    analysis_window_end_frame: int  # Frame at which to truncate analysis (exclusive)
    detection_method: str = "none"  # "velocity_spike" | "angle_late_shift" | "none"
    angle_baseline_degrees: float | None = None
    angle_final_degrees: float | None = None


def detect_rolling_event(
    df: pd.DataFrame,
    fps: float,
    n_frames: int | None = None,
    threshold_multiplier: float = 10.0,
    smoothing_window_seconds: float = 0.3,
    min_event_seconds_into_recording: float = 5.0,
    safety_margin_seconds: float = 1.0,
) -> RollingEvent:
    """Detect the rolling (flip) event from trunk keypoint velocities.

    Heuristic: compute mean speed across shoulders and hips, smooth with a
    short rolling window, find the first frame after `min_event_seconds_into_
    recording` where the smoothed speed exceeds `threshold_multiplier` times
    the median trunk speed. Subtract `safety_margin_seconds` worth of frames
    so the analysis window ends a bit BEFORE the actual roll begins (the
    lead-up to a flip already involves whole-body motion that confounds
    fidgety features).

    Returns RollingEvent with analysis_window_end_frame set to either
    (roll_start - safety_margin) when detected, or n_frames when not.
    """
    if n_frames is None:
        n_frames = int(df["frame_idx"].max()) + 1
    trunk_speed = _trunk_speed_series(df, n_frames, fps)
    if not np.isfinite(trunk_speed).any():
        return RollingEvent(False, None, 0.0, 0.0, 0, n_frames)
    median_speed = float(np.nanmedian(trunk_speed))
    if median_speed <= 0:
        return RollingEvent(False, None, 0.0, 0.0, 0, n_frames)
    threshold = threshold_multiplier * median_speed
    safety_margin_frames = int(round(safety_margin_seconds * fps))

    window_frames = max(1, int(round(smoothing_window_seconds * fps)))
    kernel = np.ones(window_frames) / window_frames
    speed_filled = np.where(np.isfinite(trunk_speed), trunk_speed, 0.0)
    smoothed = np.convolve(speed_filled, kernel, mode="same")
    min_idx = int(round(min_event_seconds_into_recording * fps))
    candidates = np.where(smoothed[min_idx:] > threshold)[0]
    if candidates.size == 0:
        return RollingEvent(False, None, median_speed, threshold, safety_margin_frames, n_frames)
    roll_start = int(candidates[0] + min_idx)
    analysis_end = max(0, roll_start - safety_margin_frames)
    return RollingEvent(
        detected=True,
        roll_start_frame=roll_start,
        median_trunk_speed=median_speed,
        threshold_used=threshold,
        safety_margin_frames=safety_margin_frames,
        analysis_window_end_frame=analysis_end,
        detection_method="velocity_spike",
    )


def detect_rolling_event_by_angle(
    df: pd.DataFrame,
    fps: float,
    n_frames: int | None = None,
    angle_deviation_threshold_degrees: float = 15.0,
    baseline_window_seconds: float = 5.0,
    search_start_fraction: float = 0.70,
    min_sustained_seconds: float = 0.3,
    safety_margin_seconds: float = 1.0,
) -> RollingEvent:
    """Detect a slow rolling/tilt event via late-recording trunk angle deviation.

    Complements `detect_rolling_event` (which catches sudden velocity spikes).
    This detector:
      1. Establishes a baseline trunk angle from the first
         `baseline_window_seconds` of the recording.
      2. Scans only the LATE portion (default last 30%) for sustained angular
         deviation above `angle_deviation_threshold_degrees` from baseline.
      3. Returns the first frame in that late window where the smoothed
         deviation exceeds the threshold for `min_sustained_seconds`.

    Restricting the search to the late portion is important: mid-recording
    head turns or body shifts can produce equally large transient angles
    that are not rolling events.
    """
    if n_frames is None:
        n_frames = int(df["frame_idx"].max()) + 1
    safety_margin_frames = int(round(safety_margin_seconds * fps))
    baseline_frames = int(round(baseline_window_seconds * fps))
    sustained_frames = max(1, int(round(min_sustained_seconds * fps)))
    if n_frames < baseline_frames + sustained_frames + int(fps):
        return RollingEvent(False, None, 0.0, 0.0, 0, n_frames)

    angles = trunk_angle_series(df, n_frames, smoothing_seconds=1.0, fps=fps)
    if not np.isfinite(angles).any():
        return RollingEvent(False, None, 0.0, 0.0, 0, n_frames)

    baseline = float(np.nanmedian(angles[:baseline_frames]))
    # Diagnostic: final-window median, just for logging
    final_window_frames = int(round(5.0 * fps))
    final = float(np.nanmedian(angles[max(0, n_frames - final_window_frames):]))

    base = RollingEvent(
        False, None, 0.0, 0.0, safety_margin_frames, n_frames,
        detection_method="none",
        angle_baseline_degrees=baseline,
        angle_final_degrees=final,
    )

    # Per-frame signed deviation from baseline, wrapped to (-180, 180]
    devs = np.array([_angle_diff(a, baseline) if np.isfinite(a) else 0.0 for a in angles])
    abs_devs = np.abs(devs)

    # Restrict search to the late portion of the recording so mid-recording
    # head turns or body shifts don't get mis-flagged as rolling.
    search_start = int(round(n_frames * search_start_fraction))
    if search_start >= n_frames:
        return base

    # Find first frame in the late window where |deviation| stays above the
    # threshold for at least `sustained_frames` consecutive frames.
    above = abs_devs[search_start:] > angle_deviation_threshold_degrees
    if not above.any():
        return base
    # Sustained run detection: cumulative count of consecutive True
    run_len = 0
    sustained_start_in_late: int | None = None
    for i, hit in enumerate(above):
        if hit:
            run_len += 1
            if run_len >= sustained_frames:
                sustained_start_in_late = i - sustained_frames + 1
                break
        else:
            run_len = 0
    if sustained_start_in_late is None:
        return base

    roll_start = int(sustained_start_in_late + search_start)
    analysis_end = max(0, roll_start - safety_margin_frames)
    return RollingEvent(
        detected=True,
        roll_start_frame=roll_start,
        median_trunk_speed=0.0,
        threshold_used=angle_deviation_threshold_degrees,
        safety_margin_frames=safety_margin_frames,
        analysis_window_end_frame=analysis_end,
        detection_method="angle_late_shift",
        angle_baseline_degrees=baseline,
        angle_final_degrees=final,
    )


def detect_rolling_event_combined(df: pd.DataFrame, fps: float, n_frames: int | None = None) -> RollingEvent:
    """Try the velocity-spike detector first. If it fires, use it (more specific
    signal). Only fall back to the angle-late-shift detector when the velocity
    detector misses (captures gradual flips that don't produce a velocity
    spike, like a slow-tilt flip observed in one of the real recordings).
    """
    vel = detect_rolling_event(df, fps=fps, n_frames=n_frames)
    if vel.detected:
        return vel
    ang = detect_rolling_event_by_angle(df, fps=fps, n_frames=n_frames)
    if ang.detected:
        return ang
    # Neither detected - return the velocity result (it has median_trunk_speed populated for diagnostics)
    return vel


# ---------------------------------------------------------------------------
# Per-frame supine-validity masking
#
# GMA fidgety scoring requires the infant SUPINE (on the back), calm. Once the
# baby rolls to side-lying or prone, the pose geometry no longer reflects
# supine limb kinematics and those frames must be excluded. This supersedes the
# single trailing-roll truncation (detect_rolling_event*) with a per-frame vote
# that can carve out MULTIPLE disjoint valid segments (e.g. an early roll-and-
# return followed by a long supine stretch).
# ---------------------------------------------------------------------------


@dataclass
class ValidityMask:
    """Per-frame supine-validity result for a recording."""

    valid: np.ndarray  # bool array, length n_frames; True = usable supine frame
    segments: list[tuple[int, int]]  # disjoint valid [start, end) runs
    n_frames: int
    n_valid: int
    valid_fraction: float
    n_invalid_segments: int
    baseline_biacromial_norm: float  # recording-median shoulder-shoulder width / diag
    supine_shoulder_sign: float  # sign of (left_shoulder_x - right_shoulder_x) when supine


def _mean_confidence_series(df: pd.DataFrame, n_frames: int) -> np.ndarray:
    """Per-frame mean SAM3/MediaPipe confidence across the real keypoints."""
    out = np.full(n_frames, np.nan)
    sub = df[df["keypoint"].isin(_REAL_KEYPOINTS)]
    if sub.empty:
        return out
    means = sub.groupby("frame_idx")["confidence"].mean()
    for fi, val in means.items():
        i = int(fi)
        if 0 <= i < n_frames:
            out[i] = float(val)
    return out


def _bool_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Return [start, end) runs where mask is True."""
    runs: list[tuple[int, int]] = []
    n = len(mask)
    i = 0
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def compute_validity_mask(
    df: pd.DataFrame,
    n_frames: int,
    frame_diag: float,
    fps: float,
    min_conf: float = DEFAULT_MIN_CONFIDENCE,
    width_collapse_frac: float = 0.65,
    strong_collapse_frac: float = 0.5,
    sign_shrink_frac: float = 0.4,
    biiliac_collapse_frac: float = 0.88,
    soft_conf_threshold: float = 0.5,
    tilt_degrees: float = 45.0,
    vote_window_seconds: float = 0.5,
    min_run_seconds: float = 0.5,
) -> ValidityMask:
    """Per-frame supine-validity mask from trunk geometry.

    A frame is voted INVALID if any hard geometric condition fires:
      - no_track: shoulders not both detected,
      - collapse: bi-acromial (shoulder-shoulder) width foreshortens below
        ``width_collapse_frac`` x the recording-median width. A *borderline*
        collapse (between strong_collapse_frac and width_collapse_frac) only
        counts when corroborated by a parallel bi-iliac (hip-hip) collapse or a
        drop in mean keypoint confidence - this rejects a transient arm-over-
        torso occlusion (shoulders only) from a true whole-trunk roll.
      - crossing: the signed shoulder offset flips sign (left/right keypoints
        swap sides as the baby rolls past edge-on) or shrinks toward zero. This
        is the single most specific roll indicator.
      - tilt: trunk angle > ``tilt_degrees`` from vertical (weak contributor).

    The raw votes are then debounced with a centered majority-vote window and
    short-run closing so single-frame jitter cannot fragment the mask. Returns
    a ValidityMask with disjoint valid [start, end) segments.
    """
    ls_x, ls_y, _ = _keypoint_time_series(df, "left_shoulder", n_frames, min_conf)
    rs_x, rs_y, _ = _keypoint_time_series(df, "right_shoulder", n_frames, min_conf)
    lh_x, lh_y, _ = _keypoint_time_series(df, "left_hip", n_frames, min_conf)
    rh_x, rh_y, _ = _keypoint_time_series(df, "right_hip", n_frames, min_conf)

    biacromial = np.hypot(ls_x - rs_x, ls_y - rs_y) / frame_diag
    biiliac = np.hypot(lh_x - rh_x, lh_y - rh_y) / frame_diag
    # Signed horizontal shoulder offset (normalized). Sign encodes which shoulder
    # is on which side of the image; a roll past edge-on flips it.
    shoulder_offset = (ls_x - rs_x) / frame_diag

    angles = trunk_angle_series(df, n_frames, smoothing_seconds=1.0, fps=fps)
    conf = _mean_confidence_series(df, n_frames)

    base_biac = float(np.nanmedian(biacromial)) if np.isfinite(biacromial).any() else float("nan")
    base_biil = float(np.nanmedian(biiliac)) if np.isfinite(biiliac).any() else float("nan")
    base_conf = float(np.nanmedian(conf)) if np.isfinite(conf).any() else float("nan")

    finite_off = shoulder_offset[np.isfinite(shoulder_offset)]
    supine_sign = float(np.sign(np.nanmedian(finite_off))) if finite_off.size else 0.0
    if supine_sign == 0.0:
        supine_sign = 1.0

    invalid = np.zeros(n_frames, dtype=bool)
    for i in range(n_frames):
        w = biacromial[i]
        if not np.isfinite(w):
            invalid[i] = True  # no_track: shoulders not both detected
            continue

        vote = False

        # collapse (hard if strong; borderline needs corroboration)
        if np.isfinite(base_biac) and base_biac > 0:
            if w < strong_collapse_frac * base_biac:
                vote = True
            elif w < width_collapse_frac * base_biac:
                biil_collapse = (
                    np.isfinite(biiliac[i]) and np.isfinite(base_biil) and base_biil > 0
                    and biiliac[i] < biiliac_collapse_frac * base_biil
                )
                conf_drop = (
                    np.isfinite(conf[i]) and np.isfinite(base_conf) and base_conf > 0
                    and conf[i] < soft_conf_threshold * base_conf
                )
                if biil_collapse or conf_drop:
                    vote = True

        # crossing (sign flip or shrink toward zero) - most specific roll signal
        off = shoulder_offset[i]
        if np.isfinite(off):
            if off != 0.0 and np.sign(off) != supine_sign:
                vote = True
            elif np.isfinite(base_biac) and base_biac > 0 and abs(off) < sign_shrink_frac * base_biac:
                vote = True

        # tilt (weak) - trunk far from vertical
        a = angles[i]
        if np.isfinite(a) and abs(_angle_diff(a, 0.0)) > tilt_degrees:
            vote = True

        invalid[i] = vote

    # Debounce: centered majority-vote window over the raw invalid votes.
    vote_win = max(1, int(round(vote_window_seconds * fps)))
    if vote_win > 1:
        kernel = np.ones(vote_win) / vote_win
        frac_invalid = np.convolve(invalid.astype(float), kernel, mode="same")
        invalid = frac_invalid >= 0.5

    valid = ~invalid

    # Short-run closing: drop valid/invalid runs shorter than min_run so single-
    # frame jitter cannot fragment an otherwise-clean segment.
    min_run = max(1, int(round(min_run_seconds * fps)))
    if min_run > 1:
        for a, b in _bool_runs(invalid):
            if b - a < min_run:
                valid[a:b] = True
        invalid = ~valid
        for a, b in _bool_runs(valid):
            if b - a < min_run:
                valid[a:b] = False

    segments = _bool_runs(valid)
    n_valid = int(valid.sum())
    n_invalid_segments = len(_bool_runs(~valid))
    return ValidityMask(
        valid=valid,
        segments=segments,
        n_frames=n_frames,
        n_valid=n_valid,
        valid_fraction=float(n_valid / n_frames) if n_frames else 0.0,
        n_invalid_segments=n_invalid_segments,
        baseline_biacromial_norm=base_biac,
        supine_shoulder_sign=supine_sign,
    )


@dataclass
class KeypointKinematics:
    """Per-keypoint kinematic summary statistics."""

    keypoint: str
    n_valid_frames: int
    fraction_valid: float
    mean_confidence: float
    # Position (normalized by frame diagonal for scale invariance)
    position_std_norm: float
    # Speed (pixels per second, normalized by frame diagonal so it's resolution-invariant)
    speed_mean: float
    speed_std: float
    speed_p95: float
    # Acceleration magnitude
    accel_mean: float
    accel_std: float
    # Smoothness (normalized jerk index; lower = smoother)
    normalized_jerk_index: float
    # Variability
    velocity_entropy: float
    # Frequency content
    dominant_freq_hz: float
    spectral_entropy: float
    # Periodicity strength
    autocorr_peak_prominence: float
    # Trajectory curvature (Kanemaru 2019: the kinematic index that best separated
    # fidgety subtypes - true fidgety is multidirectional/curved). Higher = more
    # directional variability. Defaulted so older constructors stay valid.
    mean_curvature: float = float("nan")
    # Fraction of 2D-velocity spectral energy in the fidgety band (robust replacement
    # for a single dominant-frequency bin; NOT a sharp-peak reward).
    inband_energy_fraction: float = float("nan")


@dataclass
class SymmetryStats:
    """Per-pair symmetry/coordination statistics."""

    pair_left: str
    pair_right: str
    # Symmetry index: ratio of left magnitude to right magnitude (1.0 = symmetric)
    speed_symmetry_index: float
    # Cross-correlation between left and right velocity (high = synchronized)
    velocity_cross_correlation: float
    # Phase relationship (lag of right relative to left, in seconds)
    cross_correlation_lag_seconds: float


@dataclass
class VideoFeatures:
    """All features extracted from a single video's pose parquet."""

    video_id: str
    n_frames: int
    n_detected_frames: int
    detection_rate: float
    duration_seconds: float
    fps: float
    frame_diagonal_pixels: float
    keypoints: dict[str, KeypointKinematics] = field(default_factory=dict)
    symmetry: dict[str, SymmetryStats] = field(default_factory=dict)
    # Global aggregates
    overall_mean_speed: float = 0.0
    overall_mean_jerk: float = 0.0
    rotation_applied_median: float = 0.0
    # Analysis window (frames). end_exclusive == n_frames means full recording used.
    analysis_window_start_frame: int = 0
    analysis_window_end_frame_exclusive: int = 0
    rolling_event_detected: bool = False
    rolling_event_start_frame: int | None = None
    # Per-frame supine-validity mask results. valid_segments are the
    # disjoint [start, end) frame ranges the kinematics were actually computed on.
    valid_segments: list[tuple[int, int]] = field(default_factory=list)
    n_valid_supine_frames: int = 0
    valid_supine_fraction: float = 0.0
    n_invalid_segments: int = 0
    # Whole-body cramped-synchronized index: mean SIGNED zero-lag directional-velocity
    # correlation across all limb pairs (homologous + cross-limb). Near +1 = the
    # in-phase whole-body co-contraction of cramped-synchronized; ~0 or negative =
    # normal independent/reciprocal movement. NaN if not computed.
    cramped_sync_index: float = float("nan")


def _normalized_jerk_index(position: np.ndarray, dt: float) -> float:
    """Log dimensionless jerk (smoothness). Lower (more negative) = smoother.

    FIXED (2026-07-05): normalizes by PATH LENGTH, not net endpoint displacement.
    The Hogan-Sternad dimensionless jerk assumed discrete reaches where net
    displacement ~= path length; for continuous oscillatory fidgety motion the net
    displacement collapses toward 0 and the old metric exploded. Using path length
    (total distance travelled) makes it stable for oscillatory movement. Computed on
    short windows by the caller (see _windowed_smoothness) so the duration term does
    not scale-explode across runs of different length.
    """
    if position.shape[0] < 5:
        return float("nan")
    step = np.diff(position, axis=0)
    path_length = float(np.sum(np.linalg.norm(step, axis=-1))) if step.ndim > 1 else float(np.sum(np.abs(step)))
    if path_length <= 0:
        return float("nan")
    duration = position.shape[0] * dt
    velocity = step / dt
    accel = np.diff(velocity, axis=0) / dt
    jerk = np.diff(accel, axis=0) / dt
    jerk_mag_sq = np.sum(jerk ** 2, axis=-1) if jerk.ndim > 1 else jerk ** 2
    integral = 0.5 * np.trapz(jerk_mag_sq, dx=dt)
    return float(np.sqrt(max(integral, 0.0)) * (duration ** 5) / (path_length ** 2 + 1e-9))


def _windowed_smoothness(position: np.ndarray, dt: float, window_frames: int) -> float:
    """Median normalized-jerk over fixed-length windows, so the duration term stays
    comparable across runs of different length (robust smoothness estimate)."""
    n = position.shape[0]
    if n < max(5, window_frames // 2):
        return _normalized_jerk_index(position, dt)
    vals: list[float] = []
    step = max(1, window_frames)
    for a in range(0, n - 4, step):
        seg = position[a:a + window_frames]
        if seg.shape[0] >= 5:
            nji = _normalized_jerk_index(seg, dt)
            if np.isfinite(nji):
                vals.append(nji)
    return float(np.median(vals)) if vals else float("nan")


def _mean_curvature(position: np.ndarray, dt: float, min_speed: float) -> float:
    """Mean trajectory curvature (Kanemaru 2019). kappa = |x'y'' - y'x''| / (x'^2+y'^2)^1.5.

    Averaged over frames where speed exceeds min_speed (curvature is undefined/noisy
    where the point is nearly still). Higher = more directional/multidirectional
    movement, the hallmark of true fidgety.
    """
    if position.shape[0] < 5:
        return float("nan")
    v = np.gradient(position, dt, axis=0)
    a = np.gradient(v, dt, axis=0)
    speed = np.linalg.norm(v, axis=-1)
    num = np.abs(v[:, 0] * a[:, 1] - v[:, 1] * a[:, 0])
    denom = np.power(speed ** 2, 1.5)
    with np.errstate(divide="ignore", invalid="ignore"):
        kappa = num / denom
    moving = speed > min_speed
    kappa = kappa[moving & np.isfinite(kappa)]
    return float(np.median(kappa)) if kappa.size else float("nan")


def _inband_energy_fraction(vel_xy: np.ndarray, fps: float, band: tuple[float, float]) -> float:
    """Fraction of 2D-velocity spectral energy that lies in `band` (DC excluded).

    Robust replacement for a single dominant-frequency bin: it does NOT reward a
    sharp peak, only how much of the movement energy sits in the low-frequency
    fidgety range across BOTH axes.
    """
    if vel_xy.shape[0] < 16:
        return float("nan")
    total = 0.0
    inband = 0.0
    for axis in range(vel_xy.shape[1]):
        series = vel_xy[:, axis]
        series = series[np.isfinite(series)]
        if series.size < 16:
            continue
        nperseg = min(256, series.size)
        freqs, psd = sp_signal.welch(series, fs=fps, nperseg=nperseg)
        pos = freqs > 0
        total += float(np.sum(psd[pos]))
        sel = pos & (freqs >= band[0]) & (freqs <= band[1])
        inband += float(np.sum(psd[sel]))
    return float(inband / total) if total > 0 else float("nan")


def _zero_lag_corr(a: np.ndarray, b: np.ndarray) -> float:
    """Signed Pearson correlation at ZERO lag between two 1D series (in-phase = +)."""
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if a.size < 16:
        return float("nan")
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt(np.dot(a, a) * np.dot(b, b))
    return float(np.dot(a, b) / denom) if denom > 0 else float("nan")


def _shannon_entropy(values: np.ndarray, n_bins: int = 32) -> float:
    """Shannon entropy of a histogram of `values`. Returns nats."""
    if values.size < 4:
        return float("nan")
    hist, _ = np.histogram(values, bins=n_bins, density=True)
    hist = hist[hist > 0]
    if hist.size == 0:
        return 0.0
    p = hist / hist.sum()
    return float(-np.sum(p * np.log(p)))


def _dominant_frequency(velocity_series: np.ndarray, fps: float) -> tuple[float, float]:
    """Return (dominant_freq_hz, spectral_entropy_nats) for a 1D velocity series.

    Welch's method is used to get a smoother PSD on short noisy series.
    """
    if velocity_series.size < 16 or not np.isfinite(velocity_series).any():
        return float("nan"), float("nan")
    series = velocity_series[np.isfinite(velocity_series)]
    if series.size < 16:
        return float("nan"), float("nan")
    nperseg = min(256, series.size)
    freqs, psd = sp_signal.welch(series, fs=fps, nperseg=nperseg)
    # Skip DC bin
    if freqs.size <= 1:
        return float("nan"), float("nan")
    dom_idx = 1 + int(np.argmax(psd[1:]))
    dom_freq = float(freqs[dom_idx])
    psd_pos = psd[1:]
    psd_pos = psd_pos[psd_pos > 0]
    if psd_pos.size == 0:
        return dom_freq, 0.0
    p = psd_pos / psd_pos.sum()
    spec_entropy = float(-np.sum(p * np.log(p)))
    return dom_freq, spec_entropy


def _autocorr_peak_prominence(series: np.ndarray) -> float:
    """Strength of periodicity via autocorrelation peak prominence.

    Returns the prominence of the highest peak in the autocorrelation
    function for lags > 1 sample. Higher value means stronger periodicity.
    """
    if series.size < 16 or not np.isfinite(series).any():
        return float("nan")
    series = series[np.isfinite(series)]
    series = series - series.mean()
    norm = float(np.dot(series, series))
    if norm == 0:
        return 0.0
    ac = np.correlate(series, series, mode="full")[len(series) - 1 :]
    ac = ac / norm
    if ac.size < 4:
        return 0.0
    peaks, props = sp_signal.find_peaks(ac[1:], prominence=0.0)
    if peaks.size == 0:
        return 0.0
    return float(props["prominences"].max())


def _normalized_cross_correlation(a: np.ndarray, b: np.ndarray, fps: float) -> tuple[float, float]:
    """Return (peak_xcorr, lag_in_seconds) between two 1D series.

    Uses zero-mean unit-variance series so the peak is in [-1, 1]. The peak is
    chosen by argmax(|xc|), i.e. the largest-MAGNITUDE correlation at ANY lag,
    and the sign is preserved in the returned value.

    KNOWN LIMITATION (flagged for follow-up): callers that use this for cramped-
    synchronized detection take abs() of the result, which CANNOT distinguish
    in-phase co-contraction (cramped-synchronized, positive at zero lag) from
    normal ANTI-phase reciprocal movement (negative correlation). It is also fed
    SPEED MAGNITUDES (direction-blind) rather than a signed directional signal. A
    correct CS metric would be signed, restricted to near-zero lag, on a directional
    component (x/y velocity or joint angle), and include cross-limb (arm<->leg) pairs.
    """
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask]
    b = b[mask]
    if a.size < 16 or b.size < 16:
        return float("nan"), float("nan")
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    n = len(a)
    xc = np.correlate(a, b, mode="full") / n
    lags = np.arange(-n + 1, n)
    peak_idx = int(np.argmax(np.abs(xc)))
    return float(xc[peak_idx]), float(lags[peak_idx] / fps)


def _keypoint_time_series(
    df: pd.DataFrame,
    keypoint: str,
    n_frames: int,
    min_conf: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (x, y, confidence) arrays for one keypoint indexed by frame_idx 0..n_frames-1.

    Missing frames are NaN. Frames below min_conf are also set to NaN.
    """
    x = np.full(n_frames, np.nan)
    y = np.full(n_frames, np.nan)
    conf = np.full(n_frames, np.nan)
    rows = df[df["keypoint"] == keypoint]
    for _, r in rows.iterrows():
        fi = int(r["frame_idx"])
        c = float(r["confidence"])
        if c < min_conf:
            continue
        if 0 <= fi < n_frames:
            x[fi] = float(r["x"])
            y[fi] = float(r["y"])
            conf[fi] = c
    return x, y, conf


def _fill_short_gaps(series: np.ndarray, max_gap: int = 5) -> np.ndarray:
    """Linear-interpolate NaN runs up to max_gap consecutive frames."""
    out = series.copy()
    n = out.size
    i = 0
    while i < n:
        if not np.isnan(out[i]):
            i += 1
            continue
        j = i
        while j < n and np.isnan(out[j]):
            j += 1
        gap_len = j - i
        if gap_len <= max_gap and i > 0 and j < n:
            a, b = out[i - 1], out[j]
            for k in range(gap_len):
                out[i + k] = a + (b - a) * (k + 1) / (gap_len + 1)
        i = j
    return out


def _contiguous_finite_runs(finite: np.ndarray, min_len: int = 2) -> list[tuple[int, int]]:
    """[start, end) runs where ``finite`` is True and the run is at least min_len."""
    return [(a, b) for (a, b) in _bool_runs(finite) if (b - a) >= min_len]


def compute_keypoint_kinematics(
    x: np.ndarray,
    y: np.ndarray,
    conf: np.ndarray,
    fps: float,
    frame_diag: float,
    keypoint_name: str,
) -> KeypointKinematics:
    """Compute the kinematic summary for one keypoint.

    Robust to GMA-invalid (rolling/prone) frames that have been masked to NaN:
    derivatives are computed on the full-length series so that any difference
    spanning a NaN gap is itself NaN and is dropped, instead of concatenating
    valid frames across a gap (which would inject a spurious boundary velocity
    each time the baby's masked-out roll is stitched onto resumed supine data).
    Frequency-domain and jerk features, which need a contiguous uniform series,
    are computed on the longest contiguous valid run (jerk is pooled across
    runs by length-weighted mean).
    """
    dt = 1.0 / fps
    n = x.size
    valid_mask = np.isfinite(x) & np.isfinite(y)
    n_valid = int(valid_mask.sum())
    fraction_valid = n_valid / n if n else 0.0
    mean_conf = float(np.nanmean(conf)) if n_valid else 0.0

    def _empty() -> KeypointKinematics:
        nan_stats = float("nan")
        return KeypointKinematics(
            keypoint=keypoint_name,
            n_valid_frames=n_valid,
            fraction_valid=fraction_valid,
            mean_confidence=mean_conf,
            position_std_norm=nan_stats,
            speed_mean=nan_stats,
            speed_std=nan_stats,
            speed_p95=nan_stats,
            accel_mean=nan_stats,
            accel_std=nan_stats,
            normalized_jerk_index=nan_stats,
            velocity_entropy=nan_stats,
            dominant_freq_hz=nan_stats,
            spectral_entropy=nan_stats,
            autocorr_peak_prominence=nan_stats,
        )

    if n_valid < 8:
        return _empty()

    # Fill only SHORT gaps (<=5 frames), so a masked roll (a long NaN run) stays
    # NaN and derivatives spanning it become NaN and drop out.
    xf = _fill_short_gaps(x, max_gap=5)
    yf = _fill_short_gaps(y, max_gap=5)
    pos = np.stack([xf, yf], axis=-1)
    finite = np.isfinite(xf) & np.isfinite(yf)
    if int(finite.sum()) < 8:
        return _empty()

    # Position spread over the finite frames, normalized by frame diagonal.
    position_std_norm = float(
        np.linalg.norm([np.nanstd(np.where(finite, xf, np.nan)), np.nanstd(np.where(finite, yf, np.nan))]) / frame_diag
    )

    # Velocity/acceleration on the FULL series - any diff across a NaN gap is NaN.
    vel = np.diff(pos, axis=0) / dt
    speed = np.linalg.norm(vel, axis=-1)
    speed_valid = speed[np.isfinite(speed)]
    if speed_valid.size == 0:
        return _empty()
    speed_mean = float(speed_valid.mean())
    speed_std = float(speed_valid.std())
    speed_p95 = float(np.percentile(speed_valid, 95))

    accel = np.diff(vel, axis=0) / dt
    accel_mag = np.linalg.norm(accel, axis=-1)
    accel_valid = accel_mag[np.isfinite(accel_mag)]
    accel_mean = float(accel_valid.mean()) if accel_valid.size else float("nan")
    accel_std = float(accel_valid.std()) if accel_valid.size else float("nan")

    velocity_entropy = _shannon_entropy(speed_valid)

    # Frequency + smoothness + curvature on the longest contiguous finite run.
    window_frames = int(round(3.0 * fps))  # ~3 s smoothness windows (stable NJI)
    runs = _contiguous_finite_runs(finite, min_len=17)
    if runs:
        longest = max(runs, key=lambda r: r[1] - r[0])
        seg_pos = pos[longest[0]:longest[1]]
        seg_vel = np.diff(seg_pos, axis=0) / dt
        dom_freq, spec_entropy = _dominant_frequency(seg_vel[:, 0], fps)
        ac_prom = _autocorr_peak_prominence(seg_vel[:, 0])
        inband_frac = _inband_energy_fraction(seg_vel, fps, _FIDGETY_BAND_HZ)
        curvature = _mean_curvature(seg_pos, dt, min_speed=0.02 * frame_diag)
        # Smoothness: median windowed normalized-jerk pooled across runs, length-weighted.
        njis: list[float] = []
        weights: list[int] = []
        for a, b in runs:
            nji = _windowed_smoothness(pos[a:b], dt, window_frames)
            if np.isfinite(nji):
                njis.append(nji)
                weights.append(b - a)
        nji = float(np.average(njis, weights=weights)) if njis else float("nan")
    else:
        dom_freq = spec_entropy = ac_prom = inband_frac = curvature = float("nan")
        nji = _windowed_smoothness(pos[finite], dt, window_frames)

    return KeypointKinematics(
        keypoint=keypoint_name,
        n_valid_frames=n_valid,
        fraction_valid=fraction_valid,
        mean_confidence=mean_conf,
        position_std_norm=position_std_norm,
        speed_mean=speed_mean,
        speed_std=speed_std,
        speed_p95=speed_p95,
        accel_mean=accel_mean,
        accel_std=accel_std,
        normalized_jerk_index=nji,
        velocity_entropy=velocity_entropy,
        dominant_freq_hz=dom_freq,
        spectral_entropy=spec_entropy,
        autocorr_peak_prominence=ac_prom,
        mean_curvature=curvature,
        inband_energy_fraction=inband_frac,
    )


def compute_symmetry(
    series_left: tuple[np.ndarray, np.ndarray, np.ndarray],
    series_right: tuple[np.ndarray, np.ndarray, np.ndarray],
    fps: float,
    pair_left: str,
    pair_right: str,
) -> SymmetryStats:
    xl, yl, _ = series_left
    xr, yr, _ = series_right
    xl = _fill_short_gaps(xl)
    yl = _fill_short_gaps(yl)
    xr = _fill_short_gaps(xr)
    yr = _fill_short_gaps(yr)
    dt = 1.0 / fps
    vel_l = np.linalg.norm(np.stack([np.diff(xl), np.diff(yl)], axis=-1), axis=-1) / dt
    vel_r = np.linalg.norm(np.stack([np.diff(xr), np.diff(yr)], axis=-1), axis=-1) / dt
    # Symmetry index (1.0 = symmetric). We use median speed to be robust.
    med_l = np.nanmedian(vel_l)
    med_r = np.nanmedian(vel_r)
    if med_r > 0 and not np.isnan(med_l):
        si = float(med_l / med_r)
    else:
        si = float("nan")
    xc, lag = _normalized_cross_correlation(vel_l, vel_r, fps)
    return SymmetryStats(
        pair_left=pair_left,
        pair_right=pair_right,
        speed_symmetry_index=si,
        velocity_cross_correlation=xc,
        cross_correlation_lag_seconds=lag,
    )


_SYNC_LIMBS = ("left_wrist", "right_wrist", "left_ankle", "right_ankle",
               "left_elbow", "right_elbow", "left_knee", "right_knee")


def compute_synchrony(series_cache: dict, fps: float) -> float:
    """Whole-body cramped-synchronized index.

    Mean SIGNED, ZERO-LAG correlation of the SPEED envelope across ALL limb pairs
    (homologous + cross-limb, e.g. arm<->leg). This fixes the old |xcorr|-at-any-lag
    metric: cramped-synchronized is near-SIMULTANEOUS whole-body co-activation, so
    the limbs speed up and slow down TOGETHER -> positive zero-lag speed-envelope
    correlation; normal independent/reciprocal movement (limbs active at different
    times) gives ~0 or NEGATIVE correlation. Using the speed envelope (co-timing)
    rather than a directional axis avoids the mirror-limb sign ambiguity while still
    being signed and zero-lag. Near +1 = cramped-synchronized signature; <=0 = normal.
    """
    dt = 1.0 / fps
    speeds: dict[str, np.ndarray] = {}
    for kp in _SYNC_LIMBS:
        if kp not in series_cache:
            continue
        xf = _fill_short_gaps(series_cache[kp][0])
        yf = _fill_short_gaps(series_cache[kp][1])
        vx = np.diff(xf) / dt
        vy = np.diff(yf) / dt
        speeds[kp] = np.sqrt(vx ** 2 + vy ** 2)
    keys = list(speeds.keys())
    corrs: list[float] = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            c = _zero_lag_corr(speeds[keys[i]], speeds[keys[j]])
            if np.isfinite(c):
                corrs.append(c)
    return float(np.mean(corrs)) if corrs else float("nan")


def extract_features_from_parquet(
    parquet_path: Path,
    frame_width: int,
    frame_height: int,
    fps: float = 30.0,
    min_conf: float = DEFAULT_MIN_CONFIDENCE,
    trim_rolling: bool = True,
    analysis_window: tuple[int, int] | None = None,
    use_validity_mask: bool = True,
) -> VideoFeatures:
    """Top-level: read parquet, compute all features for one video.

    Frame selection (in priority order):
      1. ``analysis_window`` (explicit (start, end_exclusive)) - legacy override.
      2. ``use_validity_mask`` (default True) - per-frame supine-validity mask
         that excludes EVERY rolling/side-lying/prone frame, supporting multiple
         disjoint valid segments. This supersedes the single-window roll
         truncation below.
      3. ``trim_rolling`` only (use_validity_mask=False) - legacy single trailing
         roll truncation via detect_rolling_event_combined.

    With the validity mask, all per-keypoint kinematics and symmetry are computed
    on the full-length series with invalid frames set to NaN, so derivatives
    never bridge an excluded roll (see compute_keypoint_kinematics).
    """
    df = pd.read_parquet(parquet_path)
    if df.empty:
        raise ValueError(f"Empty parquet: {parquet_path}")

    video_id = str(df["video_id"].iloc[0])
    frame_indices = df["frame_idx"].unique()
    n_frames = int(frame_indices.max()) + 1
    duration = n_frames / fps if fps else 0.0
    frame_diag = float(np.sqrt(frame_width ** 2 + frame_height ** 2))
    rotation_median = float(df.groupby("frame_idx")["rotation_applied_degrees"].first().median()) if "rotation_applied_degrees" in df.columns else 0.0

    valid = np.ones(n_frames, dtype=bool)
    valid_segments: list[tuple[int, int]] = [(0, n_frames)]
    n_invalid_segments = 0
    rolling = None
    win_start, win_end = 0, n_frames

    if analysis_window is not None:
        win_start, win_end = analysis_window
        win_start = max(0, min(win_start, n_frames))
        win_end = max(win_start + 1, min(win_end, n_frames))
        valid = np.zeros(n_frames, dtype=bool)
        valid[win_start:win_end] = True
        valid_segments = [(win_start, win_end)]
    elif use_validity_mask:
        vm = compute_validity_mask(df, n_frames, frame_diag, fps, min_conf=min_conf)
        valid = vm.valid
        valid_segments = vm.segments
        n_invalid_segments = vm.n_invalid_segments
    elif trim_rolling:
        rolling = detect_rolling_event_combined(df, fps=fps, n_frames=n_frames)
        win_end = rolling.analysis_window_end_frame if rolling.detected else n_frames
        win_end = max(1, min(win_end, n_frames))
        valid = np.zeros(n_frames, dtype=bool)
        valid[0:win_end] = True
        valid_segments = [(0, win_end)]

    n_valid_supine = int(valid.sum())
    detection = df.groupby("frame_idx")["detected"].first()
    n_detected = int(detection.sum())
    detection_rate = float(n_detected / n_frames) if n_frames else 0.0

    features = VideoFeatures(
        video_id=video_id,
        n_frames=n_frames,
        n_detected_frames=n_detected,
        detection_rate=detection_rate,
        duration_seconds=duration,
        fps=fps,
        frame_diagonal_pixels=frame_diag,
        rotation_applied_median=rotation_median,
        analysis_window_start_frame=valid_segments[0][0] if valid_segments else 0,
        analysis_window_end_frame_exclusive=valid_segments[-1][1] if valid_segments else n_frames,
        rolling_event_detected=bool(rolling.detected) if rolling else False,
        rolling_event_start_frame=rolling.roll_start_frame if rolling and rolling.detected else None,
        valid_segments=valid_segments,
        n_valid_supine_frames=n_valid_supine,
        valid_supine_fraction=float(n_valid_supine / n_frames) if n_frames else 0.0,
        n_invalid_segments=n_invalid_segments,
    )

    # Per-keypoint kinematics: build FULL-length series, then NaN-out invalid
    # (non-supine) frames so derivatives never bridge an excluded roll.
    keypoint_names = [kp for kp in df["keypoint"].unique() if kp != "__nodetection__"]
    series_cache: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for kp in keypoint_names:
        x, y, c = _keypoint_time_series(df, kp, n_frames, min_conf)
        x = np.where(valid, x, np.nan)
        y = np.where(valid, y, np.nan)
        c = np.where(valid, c, np.nan)
        series_cache[kp] = (x, y, c)
        features.keypoints[kp] = compute_keypoint_kinematics(x, y, c, fps, frame_diag, kp)

    # Symmetry across paired keypoints
    for left, right in PAIRED_KEYPOINTS:
        if left in series_cache and right in series_cache:
            features.symmetry[f"{left}__vs__{right}"] = compute_symmetry(
                series_cache[left], series_cache[right], fps, left, right
            )

    # Whole-body cramped-synchronized index (signed, zero-lag, all limb pairs).
    features.cramped_sync_index = compute_synchrony(series_cache, fps)

    # Global aggregates
    speeds = [kk.speed_mean for kk in features.keypoints.values() if not np.isnan(kk.speed_mean)]
    jerks = [kk.normalized_jerk_index for kk in features.keypoints.values() if not np.isnan(kk.normalized_jerk_index)]
    features.overall_mean_speed = float(np.mean(speeds)) if speeds else 0.0
    features.overall_mean_jerk = float(np.mean(jerks)) if jerks else 0.0

    return features


def _keypoint_time_series_window(
    df: pd.DataFrame,
    keypoint: str,
    win_start: int,
    win_end: int,
    min_conf: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Same as _keypoint_time_series but indexed by (frame_idx - win_start)
    over a window of size (win_end - win_start).
    """
    n = win_end - win_start
    x = np.full(n, np.nan)
    y = np.full(n, np.nan)
    conf = np.full(n, np.nan)
    rows = df[df["keypoint"] == keypoint]
    for _, r in rows.iterrows():
        fi = int(r["frame_idx"]) - win_start
        c = float(r["confidence"])
        if c < min_conf:
            continue
        if 0 <= fi < n:
            x[fi] = float(r["x"])
            y[fi] = float(r["y"])
            conf[fi] = c
    return x, y, conf


def features_to_dataframe(features: VideoFeatures) -> pd.DataFrame:
    """Flatten VideoFeatures to a long-format DataFrame for parquet output."""
    rows: list[dict] = []
    for kp_name, kk in features.keypoints.items():
        for fname, val in asdict(kk).items():
            if fname == "keypoint":
                continue
            rows.append({
                "video_id": features.video_id,
                "scope": "keypoint",
                "name": kp_name,
                "feature": fname,
                "value": float(val) if isinstance(val, (int, float, np.floating)) else val,
            })
    for pair_name, ss in features.symmetry.items():
        for fname, val in asdict(ss).items():
            if fname in ("pair_left", "pair_right"):
                continue
            rows.append({
                "video_id": features.video_id,
                "scope": "symmetry",
                "name": pair_name,
                "feature": fname,
                "value": float(val) if isinstance(val, (int, float, np.floating)) else val,
            })
    rows.append({
        "video_id": features.video_id, "scope": "global", "name": "video",
        "feature": "detection_rate", "value": features.detection_rate,
    })
    rows.append({
        "video_id": features.video_id, "scope": "global", "name": "video",
        "feature": "overall_mean_speed", "value": features.overall_mean_speed,
    })
    rows.append({
        "video_id": features.video_id, "scope": "global", "name": "video",
        "feature": "overall_mean_jerk", "value": features.overall_mean_jerk,
    })
    return pd.DataFrame(rows)
