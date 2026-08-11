"""Tests for the rotation normalization helpers in pose.py."""

from __future__ import annotations

import cv2
import numpy as np

from gma_pipeline.pose import (
    _head_above_hips,
    invert_keypoints,
    principal_axis_angle_degrees,
    rotate_frame,
    rotation_to_vertical_degrees,
)


def _make_rectangle_mask(h: int, w: int, rect_h: int, rect_w: int) -> np.ndarray:
    """Centered rectangle mask of size rect_h x rect_w inside an h x w canvas."""
    mask = np.zeros((h, w), dtype=np.uint8)
    cy, cx = h // 2, w // 2
    y0 = cy - rect_h // 2
    x0 = cx - rect_w // 2
    mask[y0 : y0 + rect_h, x0 : x0 + rect_w] = 255
    return mask


def test_principal_axis_horizontal_rectangle_is_near_zero() -> None:
    # Wide-and-short rectangle, principal axis horizontal -> angle near 0
    mask = _make_rectangle_mask(200, 600, rect_h=40, rect_w=400)
    angle = principal_axis_angle_degrees(mask)
    assert angle is not None
    assert abs(angle) < 5.0, f"expected near 0, got {angle}"


def test_principal_axis_vertical_rectangle_is_near_ninety() -> None:
    # Tall-and-narrow rectangle, principal axis vertical -> angle near 90 (or -90)
    mask = _make_rectangle_mask(600, 200, rect_h=400, rect_w=40)
    angle = principal_axis_angle_degrees(mask)
    assert angle is not None
    assert abs(abs(angle) - 90.0) < 5.0, f"expected near +/-90, got {angle}"


def test_rotation_to_vertical_zero_for_already_vertical_mask() -> None:
    mask = _make_rectangle_mask(600, 200, rect_h=400, rect_w=40)
    rot = rotation_to_vertical_degrees(mask)
    # Should be small (close to 0). Account for sign convention.
    assert min(abs(rot), abs(rot - 180.0), abs(rot + 180.0)) < 5.0


def test_rotation_to_vertical_ninety_for_horizontal_mask() -> None:
    mask = _make_rectangle_mask(200, 600, rect_h=40, rect_w=400)
    rot = rotation_to_vertical_degrees(mask)
    # Should be close to 90 deg (in either direction)
    assert min(abs(rot - 90.0), abs(rot + 90.0)) < 5.0


def test_rotate_then_inverse_keypoints_roundtrip() -> None:
    frame = np.zeros((400, 600, 3), dtype=np.uint8)
    rotated, M = rotate_frame(frame, 37.0)
    # A point in rotated coords; map back through inverse should land somewhere sensible
    keypoints = {"a": (150.0, 200.0, 0.9)}
    back = invert_keypoints(keypoints, M)
    # Round-trip via forward affine then inverse should land within 1px of (150, 200)
    M_full = np.vstack([M, [0, 0, 1]])
    M_inv = np.linalg.inv(M_full)
    point_h = M_inv @ np.array([150.0, 200.0, 1.0])
    expected = (point_h[0] / point_h[2], point_h[1] / point_h[2])
    assert abs(back["a"][0] - expected[0]) < 0.01
    assert abs(back["a"][1] - expected[1]) < 0.01


def test_rotate_keypoint_at_rotation_zero_is_identity() -> None:
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    _, M = rotate_frame(frame, 0.0)
    keypoints = {"a": (42.0, 17.0, 0.5)}
    back = invert_keypoints(keypoints, M)
    assert abs(back["a"][0] - 42.0) < 1e-6
    assert abs(back["a"][1] - 17.0) < 1e-6


def test_head_above_hips_logic() -> None:
    # Image coords: y increases downward, so nose with smaller y is "above" hips.
    upright = {
        "nose": (100.0, 50.0, 0.9),
        "left_hip": (90.0, 200.0, 0.9),
        "right_hip": (110.0, 200.0, 0.9),
    }
    assert _head_above_hips(upright) is True

    upside_down = {
        "nose": (100.0, 300.0, 0.9),
        "left_hip": (90.0, 200.0, 0.9),
        "right_hip": (110.0, 200.0, 0.9),
    }
    assert _head_above_hips(upside_down) is False
