"""Video preprocessing: .mov to per-frame PNG sequence at normalized framerate.

The fidgety-stage GMA videos are typically iPhone .mov files at 30 or 60 fps,
1080p, with orientation metadata. We normalize to 30 fps for consistent
downstream feature timing (the 30 fps choice matches the GigaScience 2024
open pipeline default).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
from tqdm import tqdm

from gma_pipeline.config import PipelineConfig

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Per-input-video metadata. Saved as metadata.json next to extracted frames."""

    video_path: str
    video_id: str  # filename stem, e.g., "IMG_0001"
    input_fps: float
    input_frame_count: int
    input_duration_seconds: float
    input_width: int
    input_height: int
    input_rotation: int  # 0, 90, 180, 270
    output_fps: int
    output_frame_count: int
    output_width: int
    output_height: int
    frame_format: str
    extracted_at_iso: str
    # Recording timestamps from container EXIF. None if not present (rare for iPhone .mov).
    creation_datetime_local_iso: str | None = None  # e.g. "2001-01-01T12:00:00-05:00"
    creation_datetime_utc_iso: str | None = None  # e.g. "2001-01-01T17:00:00+00:00"


def _extract_creation_times(video_path: Path) -> tuple[str | None, str | None]:
    """Extract recording timestamps from container EXIF via ffprobe.

    Returns (local_iso, utc_iso). Both may be None if the file lacks the tags.
    Prefers `com.apple.quicktime.creationdate` for local (includes tz offset)
    and `creation_time` for UTC. Falls back to filesystem mtime if EXIF missing.
    """
    import subprocess

    local_iso: str | None = None
    utc_iso: str | None = None
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format_tags=creation_time,com.apple.quicktime.creationdate",
                "-of", "default=noprint_wrappers=1",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            if line.startswith("TAG:creation_time="):
                utc_iso = line.split("=", 1)[1].strip() or None
            elif line.startswith("TAG:com.apple.quicktime.creationdate="):
                local_iso = line.split("=", 1)[1].strip() or None
    except Exception as exc:
        logger.warning("ffprobe creation_time extraction failed for %s: %s", video_path, exc)

    # Filesystem fallback (less reliable but better than nothing)
    if local_iso is None:
        try:
            import datetime as _dt

            mtime = video_path.stat().st_mtime
            local_dt = _dt.datetime.fromtimestamp(mtime).astimezone()
            local_iso = local_dt.isoformat()
        except Exception:
            pass
    return local_iso, utc_iso


def _get_rotation(cap: cv2.VideoCapture) -> int:
    """OpenCV does not always honor rotation metadata. Read it explicitly.

    Returns degrees (0, 90, 180, 270). Falls back to 0 if unavailable.
    """
    rotation = 0
    try:
        rotation = int(cap.get(cv2.CAP_PROP_ORIENTATION_META))  # OpenCV 4.5+
    except Exception:
        rotation = 0
    if rotation not in (0, 90, 180, 270):
        rotation = 0
    return rotation


def _apply_rotation(frame, rotation: int):
    """Rotate frame by 0, 90, 180, or 270 degrees clockwise."""
    if rotation == 0:
        return frame
    if rotation == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if rotation == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotation == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame


def preprocess_video(video_path: Path, config: PipelineConfig) -> VideoMetadata:
    """Extract frames from a single video into the run's frames/<video_id>/ folder.

    Returns VideoMetadata describing what was extracted. Also writes metadata.json
    alongside the frames.
    """
    from datetime import datetime

    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    video_id = video_path.stem
    out_frames_dir = config.output_dir / "frames" / video_id
    out_frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open: {video_path}")

    input_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    input_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    input_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    input_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    input_duration = input_frame_count / input_fps if input_fps > 0 else 0.0
    rotation = _get_rotation(cap) if config.preprocess.auto_rotate else 0

    target_fps = config.preprocess.target_fps
    # Stride to downsample: keep every Nth frame so output fps approximates target_fps.
    if input_fps > target_fps:
        stride = max(1, round(input_fps / target_fps))
    else:
        stride = 1
    actual_output_fps = input_fps / stride

    logger.info(
        "Preprocessing %s: %dx%d @ %.2f fps, %d frames, rotation=%d, stride=%d -> output fps=%.2f",
        video_id,
        input_width,
        input_height,
        input_fps,
        input_frame_count,
        rotation,
        stride,
        actual_output_fps,
    )

    output_count = 0
    output_w, output_h = input_width, input_height
    with tqdm(total=input_frame_count, desc=f"frames {video_id}", unit="frame") as pbar:
        for frame_idx in range(input_frame_count):
            ok, frame = cap.read()
            if not ok:
                break
            pbar.update(1)
            if frame_idx % stride != 0:
                continue
            if rotation:
                frame = _apply_rotation(frame, rotation)
            if config.preprocess.crop is not None:
                x, y, w, h = config.preprocess.crop
                frame = frame[y : y + h, x : x + w]
            if frame_idx == 0:
                output_h, output_w = frame.shape[:2]
            ext = config.preprocess.image_format.lower().lstrip(".")
            out_path = out_frames_dir / f"frame_{output_count:06d}.{ext}"
            write_params: list[int] = []
            if ext in ("jpg", "jpeg"):
                write_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(config.preprocess.image_quality)]
            elif ext == "png":
                # PNG compression level 0 to 9 (default 3). Higher = smaller but slower.
                write_params = [int(cv2.IMWRITE_PNG_COMPRESSION), 3]
            cv2.imwrite(str(out_path), frame, write_params)
            output_count += 1
    cap.release()

    creation_local, creation_utc = _extract_creation_times(video_path)
    metadata = VideoMetadata(
        video_path=str(video_path),
        video_id=video_id,
        input_fps=float(input_fps),
        input_frame_count=int(input_frame_count),
        input_duration_seconds=float(input_duration),
        input_width=int(input_width),
        input_height=int(input_height),
        input_rotation=int(rotation),
        output_fps=int(round(actual_output_fps)),
        output_frame_count=int(output_count),
        output_width=int(output_w),
        output_height=int(output_h),
        frame_format=config.preprocess.image_format,
        extracted_at_iso=datetime.now().isoformat(timespec="seconds"),
        creation_datetime_local_iso=creation_local,
        creation_datetime_utc_iso=creation_utc,
    )
    meta_path = out_frames_dir / "metadata.json"
    with meta_path.open("w") as fh:
        json.dump(asdict(metadata), fh, indent=2)
    logger.info("Wrote %d frames to %s", output_count, out_frames_dir)
    return metadata


def preprocess_many(video_paths: list[Path], config: PipelineConfig) -> list[VideoMetadata]:
    return [preprocess_video(p, config) for p in video_paths]
