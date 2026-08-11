"""Pose estimation backends for the GMA pipeline.

Default backend: MediaPipe Pose (Tasks API, BlazePose Full). Adult-tuned, runs
natively on M-series via TFLite. Known limitation: keypoint placement on
infants is biased because the model was trained mostly on adult images. We
document this with a confidence-weighted average flag so downstream feature
extraction can filter low-confidence detections.

Optional infant-specific backend (Ostadabbas SyRIP) is a TODO; the package
requires GPU at install time and has fragile dependencies. The current
MediaPipe baseline is the practical starting point.

Keypoint schema we persist (13 joints for GMA-relevant kinematics):

    nose, left_shoulder, right_shoulder, left_elbow, right_elbow,
    left_wrist, right_wrist, left_hip, right_hip,
    left_knee, right_knee, left_ankle, right_ankle

MediaPipe Pose returns 33 landmarks; we project to these 13.

Mask-guided inference: if a segmentation mask is provided, we darken the
background before sending the frame to MediaPipe. This avoids false positives
from caregiver legs and sheet creases that the adult-trained model is prone
to detecting.
"""

from __future__ import annotations

import logging
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# MediaPipe BlazePose Full variant - balance of accuracy and speed.
POSE_MODELS = {
    "lite": {
        "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
        "filename": "pose_landmarker_lite.task",
    },
    "full": {
        "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
        "filename": "pose_landmarker_full.task",
    },
    "heavy": {
        "url": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
        "filename": "pose_landmarker_heavy.task",
    },
}
POSE_DEFAULT_VARIANT = "full"

# Mapping from MediaPipe's 33-keypoint schema to our 13 GMA-relevant keypoints.
# Indices per https://google.github.io/mediapipe/solutions/pose#pose_landmark_model_blazepose_ghum_3d
MEDIAPIPE_KEYPOINT_INDICES = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
}
GMA_KEYPOINT_NAMES = list(MEDIAPIPE_KEYPOINT_INDICES.keys())

# Skeleton edges for visualization (pairs of keypoint names)
SKELETON_EDGES = [
    ("nose", "left_shoulder"),
    ("nose", "right_shoulder"),
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
]


@dataclass
class PoseOutput:
    """Per-frame pose estimation result."""

    video_id: str
    frame_idx: int
    keypoints: dict[str, tuple[float, float, float]] = field(default_factory=dict)
    # keypoints[name] = (x_pixel, y_pixel, confidence in [0, 1])
    mean_confidence: float = 0.0
    detected: bool = False  # False if model returned no pose
    rotation_applied_degrees: float = 0.0  # signed degrees, counterclockwise positive


class PoseEstimator(ABC):
    name: str = "base"

    @abstractmethod
    def estimate_frame(
        self,
        frame_bgr: np.ndarray,
        mask: np.ndarray | None = None,
        frame_idx: int = -1,
    ) -> PoseOutput:
        ...


# ----- Rotation normalization helpers -----


def principal_axis_angle_degrees(mask: np.ndarray) -> float | None:
    """Compute the principal axis angle (from horizontal) of a binary mask.

    Uses second-order image moments via OpenCV. Angle is in degrees in
    [-90, 90), measured counterclockwise from horizontal (so 0 means body
    is horizontal, 90 means body is vertical).

    Returns None if the mask is empty.
    """
    if mask.ndim != 2:
        raise ValueError(f"mask must be 2D, got shape {mask.shape}")
    binary = (mask > 127).astype(np.uint8) if mask.dtype == np.uint8 else (mask > 0.5).astype(np.uint8)
    M = cv2.moments(binary)
    if M["m00"] < 1.0:
        return None
    # Central second-order moments
    mu20 = M["mu20"] / M["m00"]
    mu02 = M["mu02"] / M["m00"]
    mu11 = M["mu11"] / M["m00"]
    # Principal axis angle relative to horizontal (image x-axis), CCW positive.
    # Note: image y increases downward, so the sign convention puts the angle
    # in screen-space (mathematical angle would be flipped).
    angle_rad = 0.5 * np.arctan2(2.0 * mu11, mu20 - mu02)
    return float(np.degrees(angle_rad))


def rotation_to_vertical_degrees(mask: np.ndarray) -> float:
    """Return the counterclockwise rotation (degrees) needed to make the mask's
    principal axis vertical. Returns 0 if the mask is empty or unparseable.
    """
    angle = principal_axis_angle_degrees(mask)
    if angle is None:
        return 0.0
    # Principal axis 90 deg from horizontal = already vertical -> 0 rotation
    return 90.0 - angle


def rotate_frame(frame: np.ndarray, angle_deg: float, center: tuple[int, int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Rotate a frame around its center (or given center). Returns (rotated, M)
    where M is the 2x3 affine matrix used (so callers can invert it to map
    keypoints back to original coordinates).

    Note: positive angle means counterclockwise in math convention. OpenCV
    interprets cv2.getRotationMatrix2D's angle the same way.
    """
    h, w = frame.shape[:2]
    if center is None:
        center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    rotated = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    return rotated, M


def _head_above_hips(keypoints: dict[str, tuple[float, float, float]]) -> bool:
    """Check whether the head (nose) appears above the hips in image coordinates.

    Image y increases downward, so 'above' means smaller y. Falls back to True
    if either nose or hips are missing.
    """
    nose = keypoints.get("nose")
    lhip = keypoints.get("left_hip")
    rhip = keypoints.get("right_hip")
    if nose is None or (lhip is None and rhip is None):
        return True
    hip_y_candidates = [p[1] for p in (lhip, rhip) if p is not None]
    if not hip_y_candidates:
        return True
    hip_y = sum(hip_y_candidates) / len(hip_y_candidates)
    return nose[1] < hip_y


def invert_keypoints(keypoints: dict[str, tuple[float, float, float]], M: np.ndarray) -> dict[str, tuple[float, float, float]]:
    """Map keypoints from rotated frame coordinates back to the original frame
    using the inverse of the affine matrix M.
    """
    M_inv = cv2.invertAffineTransform(M)
    out: dict[str, tuple[float, float, float]] = {}
    for name, (x, y, conf) in keypoints.items():
        x_orig = float(M_inv[0, 0] * x + M_inv[0, 1] * y + M_inv[0, 2])
        y_orig = float(M_inv[1, 0] * x + M_inv[1, 1] * y + M_inv[1, 2])
        out[name] = (x_orig, y_orig, conf)
    return out


class MediaPipePoseEstimator(PoseEstimator):
    """MediaPipe Pose Landmarker (Tasks API). Adult-trained but practical baseline."""

    def __init__(
        self,
        models_dir: Path,
        video_id: str | None = None,
        variant: str = POSE_DEFAULT_VARIANT,
        min_pose_confidence: float = 0.3,
        rotation_normalize: bool = True,
        rotation_confidence_threshold: float = 0.85,
    ):
        if variant not in POSE_MODELS:
            raise ValueError(f"Unknown pose variant {variant!r}. Choose from {list(POSE_MODELS)}.")
        self.models_dir = models_dir
        self.video_id = video_id or "unknown"
        self.variant = variant
        self.min_pose_confidence = min_pose_confidence
        self.rotation_normalize = rotation_normalize
        self.rotation_confidence_threshold = rotation_confidence_threshold
        suffix = "+rot" if rotation_normalize else ""
        self.name = f"mediapipe-{variant}{suffix}"
        self._landmarker = None

    def _ensure_model(self) -> Path:
        spec = POSE_MODELS[self.variant]
        path = self.models_dir / spec["filename"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.stat().st_size == 0:
            logger.info("Downloading MediaPipe pose model (%s) to %s", self.variant, path)
            urllib.request.urlretrieve(spec["url"], path)
            logger.info("Downloaded %d bytes", path.stat().st_size)
        return path

    def _ensure_landmarker(self):
        if self._landmarker is not None:
            return
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

        model_path = self._ensure_model()
        opts = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=VisionTaskRunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=self.min_pose_confidence,
            min_pose_presence_confidence=self.min_pose_confidence,
            min_tracking_confidence=self.min_pose_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = PoseLandmarker.create_from_options(opts)
        logger.info("MediaPipe Pose Landmarker (%s) ready", self.variant)

    def _mask_background(self, frame_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Darken background pixels (where mask == 0). Keeps frame color in
        foreground but pushes background toward black to suppress detections there.
        """
        if mask.shape[:2] != frame_bgr.shape[:2]:
            mask = cv2.resize(mask, (frame_bgr.shape[1], frame_bgr.shape[0]), interpolation=cv2.INTER_NEAREST)
        binary = (mask > 127).astype(np.uint8)
        out = frame_bgr.copy()
        bg = binary == 0
        out[bg] = (out[bg].astype(np.float32) * 0.15).astype(np.uint8)
        return out

    def _run_pose_on_frame(self, frame_bgr: np.ndarray, frame_idx: int) -> PoseOutput:
        """Single MediaPipe pose pass on a (already-prepared) frame."""
        import mediapipe as mp

        h, w = frame_bgr.shape[:2]
        input_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=input_rgb)
        result = self._landmarker.detect(mp_image)
        if not result.pose_landmarks:
            return PoseOutput(self.video_id, frame_idx, detected=False)
        landmarks = result.pose_landmarks[0]
        kp: dict[str, tuple[float, float, float]] = {}
        confidences = []
        for name, idx in MEDIAPIPE_KEYPOINT_INDICES.items():
            lm = landmarks[idx]
            x = float(lm.x) * w
            y = float(lm.y) * h
            conf = float(getattr(lm, "visibility", 0.0))
            kp[name] = (x, y, conf)
            confidences.append(conf)
        return PoseOutput(
            video_id=self.video_id,
            frame_idx=frame_idx,
            keypoints=kp,
            mean_confidence=float(np.mean(confidences)) if confidences else 0.0,
            detected=True,
        )

    def estimate_frame(
        self,
        frame_bgr: np.ndarray,
        mask: np.ndarray | None = None,
        frame_idx: int = -1,
    ) -> PoseOutput:
        self._ensure_landmarker()
        input_bgr = self._mask_background(frame_bgr, mask) if mask is not None else frame_bgr

        # Fast path: no rotation requested, or no mask available to compute rotation
        if not self.rotation_normalize or mask is None:
            return self._run_pose_on_frame(input_bgr, frame_idx)

        # Rotation-aware path: align body's principal axis with the image vertical,
        # then try both head-up and head-down orientations, pick higher confidence.
        rotation_deg = rotation_to_vertical_degrees(mask)
        if abs(rotation_deg) < 2.0:
            # Already close to vertical; skip the rotation overhead
            result = self._run_pose_on_frame(input_bgr, frame_idx)
            result.rotation_applied_degrees = 0.0
            return result

        # Orientation A: rotate by rotation_deg
        rotated_a, M_a = rotate_frame(input_bgr, rotation_deg)
        pose_a = self._run_pose_on_frame(rotated_a, frame_idx)

        # Short-circuit: if A is high confidence and head appears above hips in
        # rotated frame, accept it without running B.
        if pose_a.detected and pose_a.mean_confidence >= self.rotation_confidence_threshold:
            if _head_above_hips(pose_a.keypoints):
                result = self._inverse_rotate_result(pose_a, M_a)
                result.rotation_applied_degrees = rotation_deg
                return result

        # Orientation B: flip 180 degrees
        rotated_b, M_b = rotate_frame(input_bgr, rotation_deg + 180.0)
        pose_b = self._run_pose_on_frame(rotated_b, frame_idx)

        # Pick the better one. Prefer the orientation where head is above hips;
        # tiebreak by mean confidence.
        a_score = pose_a.mean_confidence if pose_a.detected else 0.0
        b_score = pose_b.mean_confidence if pose_b.detected else 0.0
        a_anatomical = pose_a.detected and _head_above_hips(pose_a.keypoints)
        b_anatomical = pose_b.detected and _head_above_hips(pose_b.keypoints)
        if a_anatomical and not b_anatomical:
            best, best_M, best_angle = pose_a, M_a, rotation_deg
        elif b_anatomical and not a_anatomical:
            best, best_M, best_angle = pose_b, M_b, rotation_deg + 180.0
        elif a_score >= b_score:
            best, best_M, best_angle = pose_a, M_a, rotation_deg
        else:
            best, best_M, best_angle = pose_b, M_b, rotation_deg + 180.0

        if not best.detected:
            best.rotation_applied_degrees = best_angle
            return best
        result = self._inverse_rotate_result(best, best_M)
        result.rotation_applied_degrees = best_angle
        return result

    @staticmethod
    def _inverse_rotate_result(pose: PoseOutput, M: np.ndarray) -> PoseOutput:
        return PoseOutput(
            video_id=pose.video_id,
            frame_idx=pose.frame_idx,
            keypoints=invert_keypoints(pose.keypoints, M),
            mean_confidence=pose.mean_confidence,
            detected=pose.detected,
        )


def make_pose_estimator(
    backend: str,
    models_dir: Path,
    video_id: str | None = None,
    mediapipe_variant: str = POSE_DEFAULT_VARIANT,
) -> PoseEstimator:
    """Construct a PoseEstimator. Currently only MediaPipe is implemented."""
    backend_lc = backend.lower()
    if backend_lc in ("auto", "mediapipe"):
        return MediaPipePoseEstimator(models_dir, video_id=video_id, variant=mediapipe_variant)
    if backend_lc == "ostadabbas":
        raise NotImplementedError(
            "Ostadabbas SyRIP infant pose backend is not yet implemented. "
            "Install the upstream repo and add a wrapper here."
        )
    raise ValueError(f"Unknown pose backend: {backend!r}")


def keypoints_to_records(pose: PoseOutput) -> list[dict]:
    """Flatten a PoseOutput into rows suitable for parquet writing."""
    rows = []
    for name, (x, y, conf) in pose.keypoints.items():
        rows.append(
            {
                "video_id": pose.video_id,
                "frame_idx": pose.frame_idx,
                "keypoint": name,
                "x": x,
                "y": y,
                "confidence": conf,
            }
        )
    return rows


def draw_skeleton(
    frame_bgr: np.ndarray,
    pose: PoseOutput,
    keypoint_color: tuple[int, int, int] = (0, 255, 0),
    edge_color: tuple[int, int, int] = (255, 200, 0),
    confidence_threshold: float = 0.3,
) -> np.ndarray:
    """Draw the 13-keypoint GMA skeleton on a frame. Returns a copy."""
    out = frame_bgr.copy()
    if not pose.detected:
        return out
    h, w = frame_bgr.shape[:2]
    radius = max(4, h // 200)
    thickness = max(2, h // 360)
    for a, b in SKELETON_EDGES:
        if a not in pose.keypoints or b not in pose.keypoints:
            continue
        xa, ya, ca = pose.keypoints[a]
        xb, yb, cb = pose.keypoints[b]
        if ca < confidence_threshold or cb < confidence_threshold:
            continue
        cv2.line(out, (int(xa), int(ya)), (int(xb), int(yb)), edge_color, thickness, cv2.LINE_AA)
    for name, (x, y, conf) in pose.keypoints.items():
        if conf < confidence_threshold:
            continue
        cv2.circle(out, (int(x), int(y)), radius, keypoint_color, -1, cv2.LINE_AA)
        cv2.circle(out, (int(x), int(y)), radius, (0, 0, 0), 1, cv2.LINE_AA)
    return out
