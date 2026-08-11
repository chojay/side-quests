"""Tests for per-frame supine-validity masking, MOS-R proxy, and the
segmental asymmetry discriminator. All data here is synthetic."""

from __future__ import annotations

import numpy as np
import pandas as pd

from gma_pipeline.calibration import analyze_segmental_asymmetry
from gma_pipeline.features import (
    KeypointKinematics,
    SymmetryStats,
    VideoFeatures,
    compute_validity_mask,
)
from gma_pipeline.mos_r import compute_mosr_proxy


_ALL_KEYPOINTS = [
    ("nose", 1000.0, 300.0),
    ("left_shoulder", 800.0, 500.0),
    ("right_shoulder", 1200.0, 500.0),
    ("left_elbow", 700.0, 800.0),
    ("right_elbow", 1300.0, 800.0),
    ("left_wrist", 650.0, 1000.0),
    ("right_wrist", 1350.0, 1000.0),
    ("left_hip", 850.0, 1500.0),
    ("right_hip", 1150.0, 1500.0),
    ("left_knee", 820.0, 1900.0),
    ("right_knee", 1180.0, 1900.0),
    ("left_ankle", 800.0, 2300.0),
    ("right_ankle", 1200.0, 2300.0),
]


def _supine_then_roll_df(n_frames: int, fps: float, roll_start: int | None) -> pd.DataFrame:
    """Supine baseline (left shoulder left of right) then a roll where the
    shoulders collapse together and cross (bi-acromial width collapse + sign flip)."""
    rng = np.random.default_rng(7)
    rows: list[dict] = []
    for name, cx, cy in _ALL_KEYPOINTS:
        for fi in range(n_frames):
            x = cx + rng.normal(0, 3.0)
            y = cy + rng.normal(0, 3.0)
            if roll_start is not None and fi >= roll_start and name in ("left_shoulder", "right_shoulder", "left_hip", "right_hip"):
                # Collapse left/right toward the midline and cross over (rolled to side / prone).
                mid = 1000.0
                if name.startswith("left"):
                    x = mid + 60.0 + rng.normal(0, 3.0)   # left now to the RIGHT of midline (crossed)
                else:
                    x = mid - 60.0 + rng.normal(0, 3.0)
            rows.append({
                "video_id": "test", "frame_idx": fi, "keypoint": name,
                "x": x, "y": y, "confidence": 0.96, "detected": True,
                "rotation_applied_degrees": 0.0, "frame_time_seconds": fi / fps,
                "absolute_datetime": None,
            })
    return pd.DataFrame(rows)


def test_validity_mask_all_supine_is_fully_valid() -> None:
    df = _supine_then_roll_df(n_frames=600, fps=30.0, roll_start=None)
    diag = float(np.hypot(2160, 3840))
    vm = compute_validity_mask(df, n_frames=600, frame_diag=diag, fps=30.0)
    assert vm.valid_fraction > 0.95
    assert vm.n_invalid_segments == 0
    assert vm.segments == [(0, 600)]


def test_validity_mask_excludes_roll_segment() -> None:
    df = _supine_then_roll_df(n_frames=600, fps=30.0, roll_start=400)
    diag = float(np.hypot(2160, 3840))
    vm = compute_validity_mask(df, n_frames=600, frame_diag=diag, fps=30.0)
    # First ~400 frames valid, the rolled tail excluded.
    assert vm.valid_fraction < 0.75
    assert vm.n_invalid_segments >= 1
    # The roll onset (~frame 400) should fall inside an invalid stretch.
    assert not vm.valid[450]
    # Early supine frames stay valid.
    assert vm.valid[100]


def test_validity_mask_excludes_midrecording_roll_and_return() -> None:
    """A roll in the MIDDLE that returns to supine yields two valid segments -
    the case the old single-truncation detector could not represent."""
    rng = np.random.default_rng(11)
    n = 900
    rows: list[dict] = []
    for name, cx, cy in _ALL_KEYPOINTS:
        for fi in range(n):
            x = cx + rng.normal(0, 3.0)
            y = cy + rng.normal(0, 3.0)
            rolled = 300 <= fi < 420
            if rolled and name in ("left_shoulder", "right_shoulder", "left_hip", "right_hip"):
                mid = 1000.0
                x = (mid + 60.0 if name.startswith("left") else mid - 60.0) + rng.normal(0, 3.0)
            rows.append({
                "video_id": "t", "frame_idx": fi, "keypoint": name, "x": x, "y": y,
                "confidence": 0.96, "detected": True, "rotation_applied_degrees": 0.0,
                "frame_time_seconds": fi / 30.0, "absolute_datetime": None,
            })
    df = pd.DataFrame(rows)
    diag = float(np.hypot(2160, 3840))
    vm = compute_validity_mask(df, n_frames=n, frame_diag=diag, fps=30.0)
    assert len(vm.segments) == 2  # supine, [roll excluded], supine again
    assert not vm.valid[360]
    assert vm.valid[100] and vm.valid[800]


# ---------------------------------------------------------------------------
# MOS-R proxy
# ---------------------------------------------------------------------------

def _kk(name: str, speed: float, dom_freq: float, entropy: float, valid: float = 1.0) -> KeypointKinematics:
    return KeypointKinematics(
        keypoint=name, n_valid_frames=1000, fraction_valid=valid, mean_confidence=0.97,
        position_std_norm=0.02, speed_mean=speed, speed_std=speed * 0.5, speed_p95=speed * 2,
        accel_mean=speed * 5, accel_std=speed * 3, normalized_jerk_index=1e9,
        velocity_entropy=entropy, dominant_freq_hz=dom_freq, spectral_entropy=4.0,
        autocorr_peak_prominence=0.1,
    )


def _features_present_fidgety(xcorr: float = 0.45, sync: float = 0.0) -> VideoFeatures:
    diag = 4406.0
    f = VideoFeatures(video_id="t", n_frames=1000, n_detected_frames=1000, detection_rate=1.0,
                      duration_seconds=33.0, fps=30.0, frame_diagonal_pixels=diag)
    f.cramped_sync_index = sync  # whole-body signed synchrony drives the C proxy
    # Non-trivial speed (~0.08-0.13 diag/s), distal markers in the 1-3 Hz band.
    specs = {
        "left_wrist": (0.09 * diag, 2.5, 2.3), "right_wrist": (0.08 * diag, 2.4, 1.8),
        "left_ankle": (0.13 * diag, 2.6, 2.3), "right_ankle": (0.14 * diag, 3.0, 2.3),
        "left_elbow": (0.07 * diag, 13.0, 2.2), "right_elbow": (0.06 * diag, 13.5, 1.9),
        "left_knee": (0.10 * diag, 1.8, 2.2), "right_knee": (0.11 * diag, 1.3, 2.1),
        "left_shoulder": (0.04 * diag, 1.5, 2.5), "right_shoulder": (0.04 * diag, 1.6, 2.4),
        "left_hip": (0.04 * diag, 1.8, 2.3), "right_hip": (0.04 * diag, 1.8, 2.5),
    }
    for name, (sp, fr, en) in specs.items():
        f.keypoints[name] = _kk(name, sp, fr, en)
    for left, right in [("left_shoulder", "right_shoulder"), ("left_elbow", "right_elbow"),
                        ("left_wrist", "right_wrist"), ("left_hip", "right_hip"),
                        ("left_knee", "right_knee"), ("left_ankle", "right_ankle")]:
        f.symmetry[f"{left}__vs__{right}"] = SymmetryStats(left, right, 1.0, xcorr, 0.0)
    return f


def test_mosr_proxy_present_fidgety_gives_F12_C4() -> None:
    proxy = compute_mosr_proxy(_features_present_fidgety(sync=0.0))  # low synchrony -> C=4
    assert proxy.subscales["F"].points == 12.0
    assert proxy.subscales["C"].points == 4.0
    assert proxy.computable_total == 16.0
    assert proxy.computable_max == 16
    assert proxy.upper_bound_28 == 28.0
    # P, R, Po are not computable.
    for code in ("P", "R", "Po"):
        assert proxy.subscales[code].points is None


def test_mosr_character_flags_cramped_synchronized() -> None:
    proxy = compute_mosr_proxy(_features_present_fidgety(sync=0.9))  # high in-phase synchrony
    assert proxy.subscales["C"].points == 1.0  # cramped-synchronized signature


# ---------------------------------------------------------------------------
# Segmental discriminator
# ---------------------------------------------------------------------------

def _features_for_segmental(si_arm: float, si_leg: float, right_arm_low_entropy: bool) -> VideoFeatures:
    """One synthetic video. Arms left-dominant (SI>1, right slower); legs
    left-slow (SI<1). right arm distal entropy low iff right_arm_low_entropy."""
    diag = 4406.0
    f = VideoFeatures(video_id="t", n_frames=1000, n_detected_frames=1000, detection_rate=1.0,
                      duration_seconds=33.0, fps=30.0, frame_diagonal_pixels=diag)
    ra_ent = 1.8 if right_arm_low_entropy else 2.4
    specs = {
        "left_shoulder": 2.5, "right_shoulder": 2.4, "left_elbow": 2.3, "right_elbow": ra_ent,
        "left_wrist": 2.1, "right_wrist": ra_ent - 0.1, "left_hip": 2.3, "right_hip": 2.5,
        "left_knee": 2.2, "right_knee": 2.1, "left_ankle": 2.24, "right_ankle": 2.24,
    }
    for name, en in specs.items():
        f.keypoints[name] = _kk(name, 0.08 * diag, 2.5, en)
    arm_pairs = [("left_shoulder", "right_shoulder"), ("left_elbow", "right_elbow"), ("left_wrist", "right_wrist")]
    leg_pairs = [("left_hip", "right_hip"), ("left_knee", "right_knee"), ("left_ankle", "right_ankle")]
    for left, right in arm_pairs:
        f.symmetry[f"{left}__vs__{right}"] = SymmetryStats(left, right, si_arm, 0.45, 0.0)
    for left, right in leg_pairs:
        f.symmetry[f"{left}__vs__{right}"] = SymmetryStats(left, right, si_leg, 0.45, 0.0)
    return f


def test_segmental_discriminator_flags_right_arm_not_legs() -> None:
    # Arms: SI>1 (right slower) + right-arm low entropy. Legs: SI<1 (left slower) + normal entropy.
    feats = {f"v{i}": _features_for_segmental(si_arm=1.2, si_leg=0.81, right_arm_low_entropy=True) for i in range(3)}
    analysis = analyze_segmental_asymmetry(feats)
    flagged = set(analysis.pipeline_flagged)
    # Distal right arm flagged; NO leg flagged (the key false-positive suppression).
    assert "right_wrist" in flagged
    assert "right_elbow" in flagged
    for leg_kp in ("left_knee", "left_ankle", "right_knee", "right_ankle", "left_hip", "right_hip"):
        assert leg_kp not in flagged
    # With the empty PT_ASSESSMENT placeholder no agreement counts accumulate,
    # so pipeline-only disagreements must stay at zero.
    assert analysis.pt_provisional_agreement["pipeline_only"] == 0


def test_segmental_no_flag_when_speed_deficit_without_variety_loss() -> None:
    # Right arm slow (SI>1) but NORMAL (above-tertile) entropy -> benign speed
    # asymmetry without a variety loss -> the right arm must NOT be flagged.
    # (This is the exact property that suppresses false positives: a consistent
    # contralateral speed deficit alone is insufficient; it must co-occur with a
    # low absolute movement-variety deficit.)
    feats = {f"v{i}": _features_for_segmental(si_arm=1.2, si_leg=0.81, right_arm_low_entropy=False) for i in range(3)}
    analysis = analyze_segmental_asymmetry(feats)
    flagged = set(analysis.pipeline_flagged)
    assert "right_wrist" not in flagged
    assert "right_elbow" not in flagged
    # And a keypoint that is low-variety but NOT a consistent deficit side is never flagged.
    by_kp = {f.keypoint: f for f in analysis.findings}
    assert by_kp["left_wrist"].pipeline_flag is False  # left arm is the FASTER side (not a deficit)
