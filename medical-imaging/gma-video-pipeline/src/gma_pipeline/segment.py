"""Segmentation backends for the GMA pipeline.

Auto-detection order:
1. SAM 3 (facebookresearch/sam3): ALMOST viable on Apple Silicon as of May 2026.
   The sam3_compat module installs a Triton stub and patches the cv2-equivalent
   EDT operation, getting past all import-time blockers. The remaining wall is
   that the model weights live in the gated `facebook/sam3` HuggingFace repo,
   which requires accepting Meta's license and setting HF_TOKEN.

   To activate SAM 3 on Mac, the user must:
     - Visit https://huggingface.co/facebook/sam3 and accept the license
     - Run `huggingface-cli login` or set `HF_TOKEN` in environment
     - Run with --backend sam3

2. SAM 2.1 (facebookresearch/sam2): default, viable on MPS. Uses Hiera-base-plus
   backbone by default for quality. Bootstraps with a MediaPipe ImageSegmenter
   rough mask to find the infant's bounding box plus center point, then SAM 2.1
   refines to the precise body outline including limbs.

3. MediaPipe alone: fallback if neither SAM is available. NOT recommended for
   production GMA work because the Selfie Segmenter systematically misses
   extended limbs (validated empirically on the real recordings).

What SAM 3 will do differently once auth is configured:
- Native text prompt "baby" or "infant in diaper" instead of MediaPipe bbox
  bootstrap (cleaner, less likely to fail when MediaPipe's rough mask is
  unreliable).
- Better temporal consistency across the rolling-over moment when the infant flips.
- Sharper edges around fingers.
"""

from __future__ import annotations

import logging
import time
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# SAM 2.1 checkpoint variants. base_plus is the default for quality.
SAM21_CHECKPOINTS = {
    "tiny": {
        "url": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt",
        "filename": "sam2.1/sam2.1_hiera_tiny.pt",
        "config": "configs/sam2.1/sam2.1_hiera_t.yaml",
        "size_mb": 149,
    },
    "small": {
        "url": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt",
        "filename": "sam2.1/sam2.1_hiera_small.pt",
        "config": "configs/sam2.1/sam2.1_hiera_s.yaml",
        "size_mb": 175,
    },
    "base_plus": {
        "url": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt",
        "filename": "sam2.1/sam2.1_hiera_base_plus.pt",
        "config": "configs/sam2.1/sam2.1_hiera_b+.yaml",
        "size_mb": 305,
    },
    "large": {
        "url": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt",
        "filename": "sam2.1/sam2.1_hiera_large.pt",
        "config": "configs/sam2.1/sam2.1_hiera_l.yaml",
        "size_mb": 856,
    },
}
SAM21_DEFAULT_VARIANT = "tiny"  # Empirically gives the most coherent whole-body mask on real infant videos. base_plus separates diaper from skin (more "correct" but introduces a hole that breaks downstream pose use).


@dataclass
class SegmentationOutput:
    """Per-frame segmentation result."""

    video_id: str
    frame_idx: int
    mask: np.ndarray  # uint8 (H, W) with values 0 or 255
    bbox: tuple[int, int, int, int]  # (xmin, ymin, xmax, ymax) in pixels
    score: float  # SAM mask confidence (0..1)
    seed_used: tuple[int, int] | None = None  # (x, y) of center seed if any


class Segmenter(ABC):
    """Common interface for SAM 3, SAM 2.1, MediaPipe backends."""

    name: str = "base"

    @abstractmethod
    def segment_frame(self, frame_bgr: np.ndarray, frame_idx: int = -1) -> SegmentationOutput:
        """Segment a single frame. Subclasses must implement."""


def _keep_largest_component(mask_u8: np.ndarray) -> np.ndarray:
    """Drop all connected components except the largest. Returns same dtype."""
    num_labels, labels_img, stats, _ = cv2.connectedComponentsWithStats(
        (mask_u8 > 0).astype(np.uint8), connectivity=8
    )
    if num_labels <= 1:
        return mask_u8
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest = 1 + int(np.argmax(areas))
    return ((labels_img == largest).astype(np.uint8)) * 255


def crop_around_subject(
    frame: np.ndarray,
    rough_mask: np.ndarray,
    pad_fraction: float = 0.20,
) -> tuple[np.ndarray, tuple[int, int], tuple[int, int]] | None:
    """Crop frame to rough_mask bbox plus padding.

    Returns (cropped_frame, (x_offset, y_offset), (crop_w, crop_h)) or None if
    no foreground found.

    Why crop first: SAM (both 2.1 and 3) internally resizes input to 1024x1024.
    If the subject occupies ~20 percent of frame area, the model sees only
    ~500x300 effective pixels of subject. Cropping to the subject means the
    model sees ~1024x1024 of mostly-subject, dramatically more detail per
    inference call. Works at any source resolution.
    """
    h, w = frame.shape[:2]
    if rough_mask.dtype == np.uint8:
        binary = (rough_mask > 127).astype(np.uint8)
    else:
        binary = (rough_mask > 0.5).astype(np.uint8)
    ys, xs = np.where(binary > 0)
    if xs.size == 0:
        return None
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    bw = x_max - x_min + 1
    bh = y_max - y_min + 1
    pad_x = int(pad_fraction * bw)
    pad_y = int(pad_fraction * bh)
    x_lo = max(0, x_min - pad_x)
    y_lo = max(0, y_min - pad_y)
    x_hi = min(w, x_max + pad_x + 1)
    y_hi = min(h, y_max + pad_y + 1)
    crop = frame[y_lo:y_hi, x_lo:x_hi].copy()
    return crop, (x_lo, y_lo), (x_hi - x_lo, y_hi - y_lo)


def paste_mask_into_full_frame(
    crop_mask: np.ndarray,
    offset: tuple[int, int],
    full_size: tuple[int, int],
) -> np.ndarray:
    """Place a crop-sized mask into an empty full-sized canvas.

    full_size: (height, width) of the canvas.
    offset: (x, y) top-left position of the crop within the canvas.
    """
    full_h, full_w = full_size
    full_mask = np.zeros((full_h, full_w), dtype=crop_mask.dtype)
    x_off, y_off = offset
    crop_h, crop_w = crop_mask.shape[:2]
    y_end = min(full_h, y_off + crop_h)
    x_end = min(full_w, x_off + crop_w)
    full_mask[y_off:y_end, x_off:x_end] = crop_mask[: y_end - y_off, : x_end - x_off]
    return full_mask


def _sample_points_in_mask(mask: np.ndarray, n: int = 5, seed: int = 42) -> list[tuple[int, int]]:
    """Sample N evenly-spread points from inside a probability mask (foreground=high).

    Uses a grid plus jitter strategy: divide the mask bounding region into an
    approximate sqrt(n) by sqrt(n) grid, pick the highest-confidence point in
    each cell. This gives well-distributed coverage instead of clustering.
    """
    binary = (mask > 0.5).astype(np.uint8) if mask.dtype != np.uint8 else (mask > 127).astype(np.uint8)
    ys, xs = np.where(binary > 0)
    if xs.size == 0:
        return []
    if xs.size <= n:
        return [(int(x), int(y)) for x, y in zip(xs, ys)]
    rng = np.random.default_rng(seed)
    # Pick n points that are spread across the foreground region by binning.
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    grid_side = max(2, int(np.ceil(np.sqrt(n))))
    points: list[tuple[int, int]] = []
    for gi in range(grid_side):
        for gj in range(grid_side):
            if len(points) >= n:
                break
            x_lo = x_min + gi * (x_max - x_min) // grid_side
            x_hi = x_min + (gi + 1) * (x_max - x_min) // grid_side
            y_lo = y_min + gj * (y_max - y_min) // grid_side
            y_hi = y_min + (gj + 1) * (y_max - y_min) // grid_side
            mask_in_cell = (xs >= x_lo) & (xs < x_hi) & (ys >= y_lo) & (ys < y_hi)
            cell_xs = xs[mask_in_cell]
            cell_ys = ys[mask_in_cell]
            if cell_xs.size == 0:
                continue
            i = rng.integers(0, cell_xs.size)
            points.append((int(cell_xs[i]), int(cell_ys[i])))
    return points[:n]


def _bbox_and_centroid_from_rough_mask(rough_mask: np.ndarray, expand: float = 0.20) -> tuple[tuple[int, int, int, int], tuple[int, int]] | None:
    """Given a rough binary mask, return (expanded_bbox, centroid) of the largest
    connected component. Returns None if no foreground found.
    """
    binary = (rough_mask > 0.5).astype(np.uint8) if rough_mask.dtype != np.uint8 else (rough_mask > 127).astype(np.uint8)
    num_labels, labels_img, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        return None
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest = 1 + int(np.argmax(areas))
    x = int(stats[largest, cv2.CC_STAT_LEFT])
    y = int(stats[largest, cv2.CC_STAT_TOP])
    bw = int(stats[largest, cv2.CC_STAT_WIDTH])
    bh = int(stats[largest, cv2.CC_STAT_HEIGHT])
    cx = int(centroids[largest, 0])
    cy = int(centroids[largest, 1])
    h, w = rough_mask.shape[:2]
    pad_x = int(expand * bw)
    pad_y = int(expand * bh)
    box = (
        max(0, x - pad_x),
        max(0, y - pad_y),
        min(w - 1, x + bw + pad_x),
        min(h - 1, y + bh + pad_y),
    )
    return box, (cx, cy)


# ----- MediaPipe-only segmenter (preview quality, deprecated for production) -----


class MediaPipeSegmenter(Segmenter):
    """Pure MediaPipe ImageSegmenter. Fast but misses extended limbs.

    Useful as a bootstrap for SAM 2.1 (which is how SAM21Segmenter uses it)
    and as a fallback for environments without SAM 2 installed.
    """

    name = "mediapipe"

    SELFIE_MODEL_URL = (
        "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
        "selfie_segmenter/float16/latest/selfie_segmenter.tflite"
    )
    SELFIE_MODEL_FILENAME = "selfie_segmenter.tflite"

    def __init__(self, models_dir: Path, video_id: str | None = None):
        self.models_dir = models_dir
        self.video_id = video_id or "unknown"
        self._segmenter = None

    @classmethod
    def _ensure_model(cls, models_dir: Path) -> Path:
        models_dir.mkdir(parents=True, exist_ok=True)
        model_path = models_dir / cls.SELFIE_MODEL_FILENAME
        if not model_path.exists() or model_path.stat().st_size == 0:
            logger.info("Downloading MediaPipe selfie segmenter to %s", model_path)
            urllib.request.urlretrieve(cls.SELFIE_MODEL_URL, model_path)
        return model_path

    def _ensure_segmenter(self):
        if self._segmenter is not None:
            return
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import ImageSegmenter, ImageSegmenterOptions
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode

        model_path = self._ensure_model(self.models_dir)
        opts = ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=VisionTaskRunningMode.IMAGE,
            output_category_mask=False,
            output_confidence_masks=True,
        )
        self._segmenter = ImageSegmenter.create_from_options(opts)

    def rough_mask(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Return a float32 (H, W) probability mask in [0, 1]."""
        import mediapipe as mp

        self._ensure_segmenter()
        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self._segmenter.segment(mp_image)
        if not result.confidence_masks:
            return np.zeros((h, w), dtype=np.float32)
        mask = np.asarray(result.confidence_masks[0].numpy_view()).squeeze().astype(np.float32)
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
        return mask

    def segment_frame(self, frame_bgr: np.ndarray, frame_idx: int = -1) -> SegmentationOutput:
        mask = self.rough_mask(frame_bgr)
        binary = (mask > 0.5).astype(np.uint8) * 255
        bbox_centroid = _bbox_and_centroid_from_rough_mask(mask)
        if bbox_centroid is None:
            h, w = frame_bgr.shape[:2]
            bbox = (0, 0, w - 1, h - 1)
            centroid = (w // 2, h // 2)
        else:
            bbox, centroid = bbox_centroid
        return SegmentationOutput(
            video_id=self.video_id,
            frame_idx=frame_idx,
            mask=binary,
            bbox=bbox,
            score=float(mask.mean()),  # not a real confidence; cheap proxy
            seed_used=centroid,
        )


# ----- SAM 2.1 with MediaPipe bootstrap (production backend) -----


class SAM21Segmenter(Segmenter):
    """SAM 2.1 image predictor with MediaPipe-bootstrapped box prompt.

    Strategy:
    1. Run MediaPipe to find the infant's rough bounding box and center of mass.
    2. Feed (box, center_point) to SAM 2.1 image predictor.
    3. SAM refines to a precise body outline including limbs.

    Empirically validated to correctly capture thin extended limbs,
    which the MediaPipe-only path misses.

    Per-frame inference time on M4 Pro/Max MPS: roughly 0.5 to 1 second.
    """

    name = "sam2.1"  # overridden per variant in __init__

    def __init__(
        self,
        models_dir: Path,
        video_id: str | None = None,
        device: str = "mps",
        variant: str = SAM21_DEFAULT_VARIANT,
        bbox_expand: float = 0.20,
        crop_first: bool = True,
    ):
        if variant not in SAM21_CHECKPOINTS:
            raise ValueError(f"Unknown SAM 2.1 variant {variant!r}. Choose from {list(SAM21_CHECKPOINTS)}.")
        self.models_dir = models_dir
        self.video_id = video_id or "unknown"
        self.device = device
        self.variant = variant
        spec = SAM21_CHECKPOINTS[variant]
        self.checkpoint_url = spec["url"]
        self.checkpoint_filename = spec["filename"]
        self.config_name = spec["config"]
        self.bbox_expand = bbox_expand
        self.crop_first = crop_first
        self._predictor = None
        self._mp_bootstrap = MediaPipeSegmenter(models_dir, video_id)
        self._last_set_image_frame_id: int | None = None
        suffix = "+crop" if crop_first else ""
        self.name = f"sam2.1-{variant}{suffix}"

    def _ensure_checkpoint(self) -> Path:
        ckpt_path = self.models_dir / self.checkpoint_filename
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        if not ckpt_path.exists() or ckpt_path.stat().st_size == 0:
            logger.info("Downloading SAM 2.1 checkpoint to %s", ckpt_path)
            urllib.request.urlretrieve(self.checkpoint_url, ckpt_path)
            logger.info("Downloaded %d bytes", ckpt_path.stat().st_size)
        return ckpt_path

    def _ensure_predictor(self):
        if self._predictor is not None:
            return
        import torch
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor

        ckpt = self._ensure_checkpoint()
        device = torch.device(self.device)
        logger.info("Building SAM 2.1 on %s with checkpoint %s", device, ckpt)
        t0 = time.time()
        model = build_sam2(self.config_name, str(ckpt), device=device)
        self._predictor = SAM2ImagePredictor(model)
        logger.info("SAM 2.1 model ready in %.2fs", time.time() - t0)

    def segment_frame(self, frame_bgr: np.ndarray, frame_idx: int = -1) -> SegmentationOutput:
        self._ensure_predictor()
        h, w = frame_bgr.shape[:2]

        # 1. MediaPipe bootstrap: rough mask -> tight bbox + centroid on the infant's skin
        rough = self._mp_bootstrap.rough_mask(frame_bgr)
        bbox_centroid = _bbox_and_centroid_from_rough_mask(rough, expand=self.bbox_expand)
        if bbox_centroid is None:
            logger.warning("MediaPipe found no foreground; falling back to full-frame center point")
            return self._segment_full_frame(frame_bgr, frame_idx, w, h)

        bbox, centroid = bbox_centroid

        if self.crop_first:
            return self._segment_with_crop(frame_bgr, rough, bbox, centroid, frame_idx, w, h)
        return self._segment_full_with_box_and_point(frame_bgr, bbox, centroid, frame_idx)

    def _segment_full_frame(self, frame_bgr: np.ndarray, frame_idx: int, w: int, h: int) -> SegmentationOutput:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._predictor.set_image(frame_rgb)
        point_arr = np.array([[w // 2, h // 2]], dtype=np.float32)
        point_labels = np.array([1])
        masks, scores, _ = self._predictor.predict(
            box=None, point_coords=point_arr, point_labels=point_labels, multimask_output=False
        )
        mask = masks[0].squeeze()
        mask_u8 = (mask > 0).astype(np.uint8) * 255
        mask_u8 = _keep_largest_component(mask_u8)
        return SegmentationOutput(
            video_id=self.video_id,
            frame_idx=frame_idx,
            mask=mask_u8,
            bbox=(0, 0, w - 1, h - 1),
            score=float(scores[0]) if len(scores) else 0.0,
            seed_used=(w // 2, h // 2),
        )

    def _segment_full_with_box_and_point(
        self,
        frame_bgr: np.ndarray,
        bbox: tuple[int, int, int, int],
        centroid: tuple[int, int],
        frame_idx: int,
    ) -> SegmentationOutput:
        """Legacy path: feed SAM the full frame plus bbox + centroid prompts."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._predictor.set_image(frame_rgb)
        box_arr = np.array(bbox, dtype=np.float32)[None, :]
        point_arr = np.array([[centroid[0], centroid[1]]], dtype=np.float32)
        point_labels = np.array([1])
        masks, scores, _ = self._predictor.predict(
            box=box_arr, point_coords=point_arr, point_labels=point_labels, multimask_output=False
        )
        mask_u8 = (masks[0].squeeze() > 0).astype(np.uint8) * 255
        mask_u8 = _keep_largest_component(mask_u8)
        return SegmentationOutput(
            video_id=self.video_id,
            frame_idx=frame_idx,
            mask=mask_u8,
            bbox=bbox,
            score=float(scores[0]) if len(scores) else 0.0,
            seed_used=centroid,
        )

    def _segment_with_crop(
        self,
        frame_bgr: np.ndarray,
        rough_mask: np.ndarray,
        bbox: tuple[int, int, int, int],
        centroid: tuple[int, int],
        frame_idx: int,
        full_w: int,
        full_h: int,
    ) -> SegmentationOutput:
        """Crop-first path: crop frame to subject bbox, run SAM on the crop, paste
        the resulting mask back into a full-frame canvas. Lets SAM use its
        internal 1024x1024 resolution budget on mostly-subject pixels.
        """
        crop_result = crop_around_subject(frame_bgr, rough_mask, pad_fraction=self.bbox_expand)
        if crop_result is None:
            return self._segment_full_frame(frame_bgr, frame_idx, full_w, full_h)
        crop_bgr, (x_off, y_off), (crop_w, crop_h) = crop_result

        # Centroid in crop coordinates
        cx_crop = centroid[0] - x_off
        cy_crop = centroid[1] - y_off
        # Guard against the unlikely case where centroid landed outside the crop
        cx_crop = int(np.clip(cx_crop, 1, crop_w - 2))
        cy_crop = int(np.clip(cy_crop, 1, crop_h - 2))

        frame_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        self._predictor.set_image(frame_rgb)
        point_arr = np.array([[cx_crop, cy_crop]], dtype=np.float32)
        point_labels = np.array([1])
        masks, scores, _ = self._predictor.predict(
            box=None, point_coords=point_arr, point_labels=point_labels, multimask_output=False
        )
        crop_mask = (masks[0].squeeze() > 0).astype(np.uint8) * 255
        full_mask = paste_mask_into_full_frame(crop_mask, (x_off, y_off), (full_h, full_w))
        full_mask = _keep_largest_component(full_mask)
        return SegmentationOutput(
            video_id=self.video_id,
            frame_idx=frame_idx,
            mask=full_mask,
            bbox=bbox,
            score=float(scores[0]) if len(scores) else 0.0,
            seed_used=centroid,
        )


# ----- SAM 3 (text prompt, via sam3_compat shim on Mac) -----


class SAM3Segmenter(Segmenter):
    """SAM 3 with text prompts. Requires the sam3_compat triton stub + EDT patch
    plus HuggingFace auth to download facebook/sam3 weights.

    To activate on Mac:
      1. https://huggingface.co/facebook/sam3 - accept the Meta license
      2. `huggingface-cli login` or `export HF_TOKEN=...`
      3. Run with --backend sam3
    """

    name = "sam3"

    def __init__(
        self,
        models_dir: Path,
        video_id: str | None = None,
        device: str = "mps",
        text_prompt: str = "infant in diaper",
    ):
        self.models_dir = models_dir
        self.video_id = video_id or "unknown"
        self.device = device
        self.text_prompt = text_prompt
        self._processor = None

    def _ensure_processor(self):
        if self._processor is not None:
            return
        import os

        # MPS fallback for ops not yet implemented on Apple Silicon (e.g. _addmm_activation,
        # _assert_async). PyTorch will copy tensors to CPU for those ops only.
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

        from gma_pipeline.sam3_compat import install_and_patch

        install_and_patch(target_device=self.device)
        from sam3.model.sam3_image_processor import Sam3Processor
        from sam3.model_builder import build_sam3_image_model

        logger.info("Building SAM 3 image model on %s (downloads weights if not cached)", self.device)
        t0 = time.time()
        model = build_sam3_image_model(device=self.device)
        # SAM 3 keeps some weights in CPU after build; force everything to target device + FP32.
        # Without .float(), inputs end up BF16 and weights FP32 which triggers MPS assertion failures.
        model = model.to(self.device).float()
        self._processor = Sam3Processor(model, device=self.device)
        logger.info("SAM 3 ready in %.2fs", time.time() - t0)

    def segment_frame(self, frame_bgr: np.ndarray, frame_idx: int = -1) -> SegmentationOutput:
        from PIL import Image as PILImage

        self._ensure_processor()
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_image = PILImage.fromarray(frame_rgb)
        state = self._processor.set_image(pil_image)
        output = self._processor.set_text_prompt(state=state, prompt=self.text_prompt)
        # SAM 3 returns masks, boxes, scores; pick highest-score mask
        masks = output["masks"]
        scores = output["scores"]
        boxes = output["boxes"]
        if hasattr(scores, "cpu"):
            scores_np = scores.detach().cpu().numpy()
        else:
            scores_np = np.asarray(scores)
        if scores_np.size == 0:
            h, w = frame_bgr.shape[:2]
            empty = np.zeros((h, w), dtype=np.uint8)
            return SegmentationOutput(self.video_id, frame_idx, empty, (0, 0, w - 1, h - 1), 0.0, None)
        best = int(np.argmax(scores_np))
        mask = masks[best]
        if hasattr(mask, "cpu"):
            mask = mask.detach().cpu().numpy()
        # SAM 3 may return masks as (1, H, W) or (H, W); squeeze to 2D and resize if needed.
        mask = np.asarray(np.squeeze(mask))
        if mask.shape != frame_bgr.shape[:2]:
            mask = cv2.resize(mask.astype(np.float32), (frame_bgr.shape[1], frame_bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
        mask_u8 = (mask > 0.5).astype(np.uint8) * 255
        box = boxes[best]
        if hasattr(box, "cpu"):
            box = box.detach().cpu().numpy()
        box = tuple(int(v) for v in np.asarray(box).reshape(-1))
        return SegmentationOutput(
            video_id=self.video_id,
            frame_idx=frame_idx,
            mask=mask_u8,
            bbox=box,
            score=float(scores_np[best]),
            seed_used=None,
        )


# ----- Factory -----


def make_segmenter(
    backend: str,
    models_dir: Path,
    video_id: str | None = None,
    device: str = "mps",
    sam2_variant: str = SAM21_DEFAULT_VARIANT,
    sam3_prompt: str = "infant in diaper",
) -> Segmenter:
    """Construct a Segmenter by backend name.

    Args:
        backend: "auto" | "sam3" | "sam2" | "sam2.1" | "mediapipe"
        models_dir: directory for caching weights
        video_id: id for naming output artifacts
        device: torch device string
        sam2_variant: SAM 2.1 backbone if used (tiny|small|base_plus|large)
        sam3_prompt: text prompt for SAM 3 segmentation
    """
    backend_lc = backend.lower()
    if backend_lc == "sam3":
        return SAM3Segmenter(models_dir, video_id=video_id, device=device, text_prompt=sam3_prompt)
    if backend_lc in ("auto", "sam2", "sam2.1"):
        try:
            import sam2  # noqa: F401

            logger.info("Using SAM 2.1 segmenter backend (variant=%s)", sam2_variant)
            return SAM21Segmenter(models_dir, video_id=video_id, device=device, variant=sam2_variant)
        except ImportError as exc:
            if backend_lc == "auto":
                logger.warning("SAM 2 not installed, falling back to MediaPipe only: %s", exc)
                return MediaPipeSegmenter(models_dir, video_id=video_id)
            raise
    if backend_lc == "mediapipe":
        return MediaPipeSegmenter(models_dir, video_id=video_id)
    raise ValueError(f"Unknown segmentation backend: {backend!r}")
