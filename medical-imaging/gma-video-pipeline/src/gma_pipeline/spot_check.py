"""Spot-check visualizations using the configured segmentation backend.

Picks N evenly spaced frames per video, runs the chosen Segmenter on each,
and saves a 3-panel image (original | mask | overlay) plus draws the SAM
bounding box + center seed on the original for context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from gma_pipeline.segment import Segmenter, make_segmenter

logger = logging.getLogger(__name__)


@dataclass
class SpotCheckResult:
    video_id: str
    backend: str
    sample_frames_saved: list[Path]
    output_dir: Path
    mean_mask_coverage: float  # fraction of frame covered by mask, averaged
    mean_score: float  # mean SAM mask confidence (or proxy for MediaPipe)


def _pick_sample_indices(total_frames: int, n: int = 6) -> list[int]:
    if total_frames <= 0:
        return []
    if total_frames <= n:
        return list(range(total_frames))
    fractions = np.linspace(0.05, 0.95, n)
    return [int(round(f * (total_frames - 1))) for f in fractions]


def _make_panel(
    frame_bgr: np.ndarray,
    mask_u8: np.ndarray,
    bbox: tuple[int, int, int, int] | None,
    seed: tuple[int, int] | None,
    backend_label: str,
) -> np.ndarray:
    h, w = frame_bgr.shape[:2]
    orig_viz = frame_bgr.copy()
    if bbox is not None:
        cv2.rectangle(orig_viz, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 255), max(2, h // 360))
    if seed is not None:
        cv2.circle(orig_viz, (int(seed[0]), int(seed[1])), max(8, h // 100), (0, 255, 0), max(2, h // 540))

    mask_bgr = cv2.cvtColor(mask_u8, cv2.COLOR_GRAY2BGR)
    binary = (mask_u8 > 127).astype(np.uint8)
    overlay_dark = frame_bgr.copy()
    overlay_dark[binary == 0] = (overlay_dark[binary == 0].astype(np.float32) * 0.3).astype(np.uint8)
    green_tint = np.zeros_like(overlay_dark)
    green_tint[:, :, 1] = 60
    overlay_tinted = cv2.addWeighted(overlay_dark, 1.0, green_tint * binary[:, :, None], 1.0, 0)

    panel = np.concatenate([orig_viz, mask_bgr, overlay_tinted], axis=1)
    label_height = max(28, h // 30)
    label = np.zeros((label_height, panel.shape[1], 3), dtype=np.uint8)
    cv2.putText(label, "ORIGINAL (yellow=bbox, green=seed)", (10, label_height - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(label, f"MASK ({backend_label})", (w + 10, label_height - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(label, "OVERLAY", (2 * w + 10, label_height - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return np.concatenate([label, panel], axis=0)


def spot_check_video(
    video_id: str,
    frames_dir: Path,
    output_root: Path,
    n_samples: int = 6,
    backend: str = "auto",
    models_dir: Path | None = None,
    segmenter: Segmenter | None = None,
) -> SpotCheckResult:
    """Sample frames and save segmentation panels.

    Args:
        video_id: id used for naming output subdir
        frames_dir: directory of extracted frames (from preprocess)
        output_root: parent dir; outputs land at <output_root>/spot_check/<video_id>/
        n_samples: evenly spaced sample count
        backend: segmenter backend (auto | sam2 | mediapipe)
        models_dir: where model weights live (defaults to project_root/models)
        segmenter: optional pre-built segmenter (reuses model load across videos)
    """
    if models_dir is None:
        models_dir = output_root.parent.parent / "models"
    if segmenter is None:
        segmenter = make_segmenter(backend, models_dir, video_id=video_id)
    backend_label = segmenter.name
    spot_dir = output_root / "spot_check" / video_id
    spot_dir.mkdir(parents=True, exist_ok=True)

    frame_files = sorted([p for p in frames_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
    if not frame_files:
        logger.warning("No frames in %s; skipping spot check", frames_dir)
        return SpotCheckResult(video_id=video_id, backend=backend_label, sample_frames_saved=[], output_dir=spot_dir, mean_mask_coverage=0.0, mean_score=0.0)

    indices = _pick_sample_indices(len(frame_files), n_samples)
    logger.info("Spot-check %s (%s): %d sample frames out of %d total", video_id, backend_label, len(indices), len(frame_files))

    # Set video_id on the segmenter so output records are tagged correctly
    segmenter.video_id = video_id

    saved: list[Path] = []
    coverages = []
    scores = []
    for idx in indices:
        frame_path = frame_files[idx]
        frame_bgr = cv2.imread(str(frame_path))
        if frame_bgr is None:
            logger.warning("Could not read frame %s", frame_path)
            continue
        result = segmenter.segment_frame(frame_bgr, frame_idx=idx)
        coverages.append(float((result.mask > 127).mean()))
        scores.append(float(result.score))
        panel = _make_panel(frame_bgr, result.mask, result.bbox, result.seed_used, backend_label)
        out_path = spot_dir / f"sample_{idx:06d}_{backend_label}.jpg"
        cv2.imwrite(str(out_path), panel, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
        saved.append(out_path)
        logger.debug("Wrote %s (coverage=%.1f%%, score=%.2f)", out_path, coverages[-1] * 100, scores[-1])

    mean_cov = float(np.mean(coverages)) if coverages else 0.0
    mean_sc = float(np.mean(scores)) if scores else 0.0
    logger.info(
        "Wrote %d spot-check panels to %s (mean coverage=%.1f%%, mean score=%.2f)",
        len(saved), spot_dir, mean_cov * 100, mean_sc,
    )
    return SpotCheckResult(
        video_id=video_id,
        backend=backend_label,
        sample_frames_saved=saved,
        output_dir=spot_dir,
        mean_mask_coverage=mean_cov,
        mean_score=mean_sc,
    )
