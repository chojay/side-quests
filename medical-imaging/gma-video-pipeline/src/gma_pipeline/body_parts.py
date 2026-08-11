"""Body-part-level segmentation using SAM 3 multi-prompt + pose-based left/right disambiguation.

SAM 3's open-vocabulary text prompting handles category-level part segmentation
well: prompts like "baby arm" return one mask per detected arm (so two masks
for a typical infant frame). But SAM 3 has no reliable concept of anatomical
left vs right - empirically it interprets "baby's left arm" from the
observer-perspective rather than the subject's perspective, which inverts
laterality for overhead supine videos.

Robust pattern used here:
1. Query SAM 3 with category prompts only ("baby arm", "baby leg", etc.)
2. For each pair of masks returned, look up the corresponding left and right
   pose keypoints (left_wrist + right_wrist for arms; left_ankle + right_ankle
   for legs) - those ARE correctly anatomically labeled by MediaPipe.
3. Assign the mask containing left_wrist as "left arm", etc.
4. Single-instance parts (head, torso) get labeled directly.

Output per sample frame: a labeled-overlay panel with each part tinted a
distinct color, plus a JSON record per part with mask metadata for any
downstream feature work.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# Anatomical category specs:
#   prompt: the SAM 3 text query
#   expected_count: 1 (single-instance) or 2 (paired left/right)
#   pose_anchor: tuple of (left_keypoint, right_keypoint) for disambiguation
#                None for single-instance parts
BODY_PART_SPECS = {
    "head":       {"prompt": "infant head",  "expected_count": 1, "anchor": None},
    "torso":      {"prompt": "baby torso",   "expected_count": 1, "anchor": None},
    "diaper":     {"prompt": "diaper",       "expected_count": 1, "anchor": None},
    "left_arm":   {"prompt": "baby arm",     "expected_count": 2, "anchor": ("left_wrist", "right_wrist"), "side": "left"},
    "right_arm":  {"prompt": "baby arm",     "expected_count": 2, "anchor": ("left_wrist", "right_wrist"), "side": "right"},
    "left_leg":   {"prompt": "baby leg",     "expected_count": 2, "anchor": ("left_ankle", "right_ankle"), "side": "left"},
    "right_leg":  {"prompt": "baby leg",     "expected_count": 2, "anchor": ("left_ankle", "right_ankle"), "side": "right"},
}

# Distinct BGR colors per labeled part for overlay rendering
PART_COLORS_BGR = {
    "head":      (60, 60, 220),    # red
    "torso":     (200, 200, 60),   # cyan
    "diaper":    (60, 220, 220),   # yellow
    "left_arm":  (60, 220, 60),    # green
    "right_arm": (60, 130, 220),   # orange
    "left_leg":  (200, 60, 220),   # magenta
    "right_leg": (220, 100, 60),   # blue
}

# Unique prompts (avoids duplicate SAM 3 calls when both left/right share a prompt)
def _unique_prompts() -> list[str]:
    return sorted({spec["prompt"] for spec in BODY_PART_SPECS.values()})


@dataclass
class PartMaskRecord:
    """Per-part record for a single frame."""

    part: str
    score: float
    bbox: tuple[int, int, int, int]  # xmin, ymin, xmax, ymax
    area_pixels: int
    centroid: tuple[float, float]
    # Note: mask itself is not stored here (would balloon size); render-time
    # functions get the mask separately when needed.


@dataclass
class FrameBodyParts:
    frame_idx: int
    video_id: str
    parts: dict[str, PartMaskRecord] = field(default_factory=dict)
    masks: dict[str, np.ndarray] = field(default_factory=dict)  # part_name -> uint8 mask
    frame_time_seconds: float | None = None  # seconds from video start
    absolute_datetime: str | None = None  # ISO datetime if creation time known


def _mask_metadata(mask_u8: np.ndarray, score: float, part_name: str) -> PartMaskRecord:
    ys, xs = np.where(mask_u8 > 127)
    if xs.size == 0:
        return PartMaskRecord(part=part_name, score=score, bbox=(0, 0, 0, 0), area_pixels=0, centroid=(0.0, 0.0))
    return PartMaskRecord(
        part=part_name,
        score=score,
        bbox=(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
        area_pixels=int(xs.size),
        centroid=(float(xs.mean()), float(ys.mean())),
    )


def _assign_paired_masks(
    masks: list[np.ndarray],
    scores: np.ndarray,
    pose_kp: dict[str, tuple[float, float, float]] | None,
    left_kp_name: str,
    right_kp_name: str,
) -> tuple[np.ndarray | None, float, np.ndarray | None, float]:
    """Disambiguate paired masks (left vs right) using pose keypoints.

    Returns (left_mask, left_score, right_mask, right_score). Either side may
    be None if no suitable mask was found.

    Heuristic: for each mask, sum the soft membership of each keypoint
    (closer keypoint = stronger match). Whichever mask contains the left
    keypoint becomes "left"; same for right. If pose keypoints are missing
    or low confidence, fall back to spatial midline (left half / right half
    of the union bbox).
    """
    if not masks:
        return None, 0.0, None, 0.0
    if len(masks) == 1:
        return masks[0], float(scores[0]), None, 0.0

    # Default: take top 2 by score
    sorted_idx = np.argsort(-scores)[:2]
    a, b = sorted_idx[0], sorted_idx[1]
    mask_a, mask_b = masks[a], masks[b]
    score_a, score_b = float(scores[a]), float(scores[b])

    def mask_contains(mask: np.ndarray, x: float, y: float, radius: int = 25) -> bool:
        h, w = mask.shape[:2]
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= xi < w and 0 <= yi < h):
            return False
        # Sample a small neighborhood (pose keypoints can be a few pixels off the silhouette)
        x_lo, x_hi = max(0, xi - radius), min(w, xi + radius + 1)
        y_lo, y_hi = max(0, yi - radius), min(h, yi + radius + 1)
        return bool((mask[y_lo:y_hi, x_lo:x_hi] > 127).any())

    has_pose = pose_kp is not None and left_kp_name in pose_kp and right_kp_name in pose_kp
    if has_pose:
        lx, ly, l_conf = pose_kp[left_kp_name]
        rx, ry, r_conf = pose_kp[right_kp_name]
        if l_conf >= 0.3 and r_conf >= 0.3:
            a_has_left = mask_contains(mask_a, lx, ly)
            a_has_right = mask_contains(mask_a, rx, ry)
            b_has_left = mask_contains(mask_b, lx, ly)
            b_has_right = mask_contains(mask_b, rx, ry)
            if a_has_left and not a_has_right:
                return mask_a, score_a, mask_b, score_b
            if a_has_right and not a_has_left:
                return mask_b, score_b, mask_a, score_a
            if b_has_left and not b_has_right:
                return mask_b, score_b, mask_a, score_a
            if b_has_right and not b_has_left:
                return mask_a, score_a, mask_b, score_b

    # Fallback: use x-coordinate of mask centroids. Smaller x = left of frame.
    # For overhead supine videos, baby's anatomical left is on the camera's left
    # (no mirror) - so smaller x in the frame corresponds to anatomical left.
    def centroid_x(m: np.ndarray) -> float:
        ys, xs = np.where(m > 127)
        return float(xs.mean()) if xs.size else 0.0

    ax = centroid_x(mask_a)
    bx = centroid_x(mask_b)
    if ax < bx:
        return mask_a, score_a, mask_b, score_b
    return mask_b, score_b, mask_a, score_a


def body_parts_for_frame(
    frame_bgr: np.ndarray,
    processor,
    pose_kp: dict[str, tuple[float, float, float]] | None,
    video_id: str = "unknown",
    frame_idx: int = -1,
    frame_time_seconds: float | None = None,
    absolute_datetime: str | None = None,
) -> FrameBodyParts:
    """Run SAM 3 with all body-part prompts on one frame; produce labeled masks.

    Args:
        frame_bgr: input frame
        processor: a Sam3Processor with set_image already called (or we call it ourselves)
        pose_kp: dict of pose keypoint name -> (x, y, confidence) for left/right disambiguation
        video_id, frame_idx: metadata
    """
    from PIL import Image

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    state = processor.set_image(pil_image)

    result = FrameBodyParts(
        frame_idx=frame_idx,
        video_id=video_id,
        frame_time_seconds=frame_time_seconds,
        absolute_datetime=absolute_datetime,
    )

    # Cache responses per unique prompt so paired specs (left_arm, right_arm) share one call
    response_cache: dict[str, tuple[list[np.ndarray], np.ndarray]] = {}

    def get_response(prompt: str) -> tuple[list[np.ndarray], np.ndarray]:
        if prompt in response_cache:
            return response_cache[prompt]
        output = processor.set_text_prompt(state=state, prompt=prompt)
        masks_raw = output.get("masks")
        scores_raw = output.get("scores")
        scores_np = scores_raw.detach().cpu().numpy() if hasattr(scores_raw, "cpu") else np.asarray(scores_raw)
        masks_list: list[np.ndarray] = []
        for i in range(scores_np.size):
            m = masks_raw[i]
            if hasattr(m, "cpu"):
                m = m.detach().cpu().numpy()
            masks_list.append((np.squeeze(m) > 0.5).astype(np.uint8) * 255)
        response_cache[prompt] = (masks_list, scores_np)
        return masks_list, scores_np

    # Process single-instance parts
    for part_name, spec in BODY_PART_SPECS.items():
        if spec["expected_count"] != 1:
            continue
        masks, scores = get_response(spec["prompt"])
        if not masks:
            continue
        best = int(np.argmax(scores))
        result.masks[part_name] = masks[best]
        result.parts[part_name] = _mask_metadata(masks[best], float(scores[best]), part_name)

    # Process paired parts (left/right disambiguation)
    paired_handled: set[str] = set()
    for part_name, spec in BODY_PART_SPECS.items():
        if spec["expected_count"] != 2 or spec["prompt"] in paired_handled:
            continue
        paired_handled.add(spec["prompt"])
        masks, scores = get_response(spec["prompt"])
        if not masks:
            continue
        left_kp_name, right_kp_name = spec["anchor"]
        left_mask, left_score, right_mask, right_score = _assign_paired_masks(
            masks, scores, pose_kp, left_kp_name, right_kp_name
        )
        # Find the part names for left and right sides sharing this prompt
        for sibling_name, sibling_spec in BODY_PART_SPECS.items():
            if sibling_spec["prompt"] != spec["prompt"]:
                continue
            side = sibling_spec.get("side")
            target_mask = left_mask if side == "left" else right_mask
            target_score = left_score if side == "left" else right_score
            if target_mask is None:
                continue
            result.masks[sibling_name] = target_mask
            result.parts[sibling_name] = _mask_metadata(target_mask, target_score, sibling_name)

    return result


def render_body_parts_panel(frame_bgr: np.ndarray, fbp: FrameBodyParts) -> np.ndarray:
    """Two-panel: ORIGINAL | colored body-part overlay."""
    h, w = frame_bgr.shape[:2]
    overlay = (frame_bgr.astype(np.float32) * 0.4).astype(np.uint8)
    for part_name, mask in fbp.masks.items():
        color = PART_COLORS_BGR.get(part_name, (200, 200, 200))
        binary = (mask > 127).astype(np.uint8)
        tint = np.zeros_like(overlay)
        tint[binary > 0] = color
        overlay = cv2.addWeighted(overlay, 1.0, tint, 0.45, 0)

    # Side-by-side
    panel = np.concatenate([frame_bgr, overlay], axis=1)

    # Legend strip at bottom: color swatch + part name + score
    legend_h = max(30, h // 30) * (len(PART_COLORS_BGR) + 1)
    legend = np.zeros((legend_h, panel.shape[1], 3), dtype=np.uint8)
    row_h = legend_h // (len(PART_COLORS_BGR) + 1)
    y = row_h - 8
    for part_name, color in PART_COLORS_BGR.items():
        cv2.rectangle(legend, (10, y - row_h + 12), (40, y + 5), color, -1)
        score_text = ""
        if part_name in fbp.parts:
            score_text = f" score={fbp.parts[part_name].score:.2f} area={fbp.parts[part_name].area_pixels}px"
        cv2.putText(legend, f"{part_name}{score_text}", (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        y += row_h

    label_h = max(28, h // 30)
    label = np.zeros((label_h, panel.shape[1], 3), dtype=np.uint8)
    cv2.putText(label, "ORIGINAL", (10, label_h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(label, f"SAM 3 body parts (frame {fbp.frame_idx}, {len(fbp.parts)} parts)", (w + 10, label_h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    return np.concatenate([label, panel, legend], axis=0)


def write_body_parts_json(fbp: FrameBodyParts, path: Path) -> None:
    """Serialize the body parts metadata (without masks) to JSON."""
    payload = {
        "video_id": fbp.video_id,
        "frame_idx": fbp.frame_idx,
        "frame_time_seconds": fbp.frame_time_seconds,
        "absolute_datetime": fbp.absolute_datetime,
        "parts": {name: asdict(rec) for name, rec in fbp.parts.items()},
    }
    path.write_text(json.dumps(payload, indent=2))
