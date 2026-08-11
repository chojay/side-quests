"""Tests for rolling-event detection in features.py."""

from __future__ import annotations

import numpy as np
import pandas as pd

from gma_pipeline.features import detect_rolling_event


def _synth_pose_df(
    n_frames: int,
    fps: float,
    roll_start_frame: int | None,
    base_jitter_px: float = 2.0,
    roll_jump_px: float = 200.0,
) -> pd.DataFrame:
    """Build a synthetic pose parquet-shaped DataFrame.

    Trunk keypoints sit at fixed locations with small jitter (the "supine
    fidgety" period). Optionally inject a sudden large displacement
    starting at roll_start_frame for ~30 frames to simulate the roll.
    """
    rng = np.random.default_rng(42)
    rows: list[dict] = []
    for kp_name, center_x, center_y in [
        ("left_shoulder", 800.0, 500.0),
        ("right_shoulder", 1200.0, 500.0),
        ("left_hip", 850.0, 1500.0),
        ("right_hip", 1150.0, 1500.0),
        ("nose", 1000.0, 300.0),
        ("left_wrist", 700.0, 900.0),
        ("right_wrist", 1300.0, 900.0),
    ]:
        for fi in range(n_frames):
            jx = rng.normal(0, base_jitter_px)
            jy = rng.normal(0, base_jitter_px)
            if roll_start_frame is not None and roll_start_frame <= fi < roll_start_frame + 30:
                jx += roll_jump_px * (fi - roll_start_frame + 1)
                jy += roll_jump_px * 0.5
            rows.append(
                {
                    "video_id": "test",
                    "frame_idx": fi,
                    "keypoint": kp_name,
                    "x": center_x + jx,
                    "y": center_y + jy,
                    "confidence": 0.95,
                    "detected": True,
                    "rotation_applied_degrees": 0.0,
                    "frame_time_seconds": fi / fps,
                    "absolute_datetime": None,
                }
            )
    return pd.DataFrame(rows)


def test_detect_rolling_event_calm_baseline_returns_none() -> None:
    df = _synth_pose_df(n_frames=600, fps=30.0, roll_start_frame=None)
    result = detect_rolling_event(df, fps=30.0)
    assert result.detected is False
    assert result.roll_start_frame is None
    assert result.analysis_window_end_frame == 600


def test_detect_rolling_event_late_spike_is_found_and_trims_before() -> None:
    df = _synth_pose_df(n_frames=600, fps=30.0, roll_start_frame=500)
    result = detect_rolling_event(df, fps=30.0, safety_margin_seconds=1.0)
    assert result.detected is True
    assert result.roll_start_frame is not None
    assert 490 <= result.roll_start_frame <= 530
    expected_end = result.roll_start_frame - 30
    assert result.analysis_window_end_frame == expected_end


def test_detect_rolling_event_skips_first_5_seconds() -> None:
    df = _synth_pose_df(n_frames=600, fps=30.0, roll_start_frame=30)
    result = detect_rolling_event(df, fps=30.0, min_event_seconds_into_recording=5.0)
    assert result.detected is False


def test_detect_rolling_event_with_lower_threshold_still_detects() -> None:
    df = _synth_pose_df(n_frames=600, fps=30.0, roll_start_frame=500)
    result = detect_rolling_event(df, fps=30.0, threshold_multiplier=3.0)
    assert result.detected is True


def _synth_pose_df_with_gradual_tilt(
    n_frames: int,
    fps: float,
    tilt_start_frame: int,
    final_tilt_degrees: float = 30.0,
) -> pd.DataFrame:
    """Like _synth_pose_df, but the trunk gradually tilts to one side over the
    second half of the recording (simulating a slow flip that the velocity
    detector misses).
    """
    rng = np.random.default_rng(7)
    rows: list[dict] = []
    base_positions = {
        "left_shoulder": (800.0, 500.0),
        "right_shoulder": (1200.0, 500.0),
        "left_hip": (850.0, 1500.0),
        "right_hip": (1150.0, 1500.0),
        "nose": (1000.0, 300.0),
        "left_wrist": (700.0, 900.0),
        "right_wrist": (1300.0, 900.0),
    }
    center_x, center_y = 1000.0, 1000.0
    n_tilt_frames = max(1, n_frames - tilt_start_frame)
    for kp_name, (px, py) in base_positions.items():
        for fi in range(n_frames):
            jx = rng.normal(0, 1.5)
            jy = rng.normal(0, 1.5)
            # Apply gradual rotation around (center_x, center_y) for frames >= tilt_start_frame
            if fi >= tilt_start_frame:
                progress = (fi - tilt_start_frame) / n_tilt_frames
                angle_rad = np.radians(final_tilt_degrees * progress)
                dx = px - center_x
                dy = py - center_y
                rx = dx * np.cos(angle_rad) - dy * np.sin(angle_rad)
                ry = dx * np.sin(angle_rad) + dy * np.cos(angle_rad)
                kx = center_x + rx + jx
                ky = center_y + ry + jy
            else:
                kx = px + jx
                ky = py + jy
            rows.append(
                {
                    "video_id": "test",
                    "frame_idx": fi,
                    "keypoint": kp_name,
                    "x": kx,
                    "y": ky,
                    "confidence": 0.95,
                    "detected": True,
                    "rotation_applied_degrees": 0.0,
                    "frame_time_seconds": fi / fps,
                    "absolute_datetime": None,
                }
            )
    return pd.DataFrame(rows)


def test_angle_detector_catches_gradual_tilt() -> None:
    from gma_pipeline.features import detect_rolling_event_by_angle

    # 30 deg total tilt starting halfway through the recording
    df = _synth_pose_df_with_gradual_tilt(n_frames=900, fps=30.0, tilt_start_frame=450, final_tilt_degrees=30.0)
    result = detect_rolling_event_by_angle(df, fps=30.0)
    assert result.detected is True
    assert result.detection_method == "angle_late_shift"
    # roll_start should land somewhere in the latter half
    assert result.roll_start_frame is not None
    assert 400 <= result.roll_start_frame <= 850


def test_angle_detector_returns_none_for_calm_recording() -> None:
    from gma_pipeline.features import detect_rolling_event_by_angle

    df = _synth_pose_df(n_frames=600, fps=30.0, roll_start_frame=None)
    result = detect_rolling_event_by_angle(df, fps=30.0)
    assert result.detected is False
    assert result.detection_method == "none"


def test_combined_detector_uses_velocity_when_spike_exists() -> None:
    from gma_pipeline.features import detect_rolling_event_combined

    df = _synth_pose_df(n_frames=600, fps=30.0, roll_start_frame=500)
    result = detect_rolling_event_combined(df, fps=30.0)
    assert result.detected is True
    assert result.detection_method == "velocity_spike"


def test_combined_detector_falls_back_to_angle_for_gradual_tilt() -> None:
    from gma_pipeline.features import detect_rolling_event_combined

    df = _synth_pose_df_with_gradual_tilt(n_frames=900, fps=30.0, tilt_start_frame=450, final_tilt_degrees=30.0)
    result = detect_rolling_event_combined(df, fps=30.0)
    assert result.detected is True
    # No velocity spike, so should use angle path
    assert result.detection_method == "angle_late_shift"
