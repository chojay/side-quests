"""GMA pipeline CLI.

Usage:
    uv run gma-pipeline preprocess inputs/IMG_0001.mov
    uv run gma-pipeline run inputs/IMG_0001.mov
    uv run gma-pipeline doctor          # env diagnostic

Each subcommand operates on one or more videos and writes to outputs/<run>/.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

import time

import cv2
import numpy as np

from gma_pipeline import __version__
from gma_pipeline.config import PipelineConfig
from gma_pipeline.preprocess import preprocess_many
from gma_pipeline.spot_check import spot_check_video

app = typer.Typer(
    help="Personal-reference GMA assessment pipeline (NOT a medical device).",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )


@app.command()
def version() -> None:
    """Print the pipeline version."""
    console.print(f"gma-pipeline {__version__}")


@app.command()
def doctor() -> None:
    """Diagnose environment: Python, PyTorch, MPS, OpenCV, MediaPipe."""
    _setup_logging()
    table = Table(title="GMA pipeline environment")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Detail")

    import sys

    table.add_row("Python", "OK", sys.version.split()[0])

    try:
        import torch

        mps_avail = torch.backends.mps.is_available()
        mps_built = torch.backends.mps.is_built()
        table.add_row(
            "PyTorch",
            "OK" if torch.__version__ else "FAIL",
            f"{torch.__version__}, MPS available={mps_avail}, built={mps_built}",
        )
    except Exception as exc:
        table.add_row("PyTorch", "FAIL", repr(exc))

    try:
        import cv2

        table.add_row("OpenCV", "OK", cv2.__version__)
    except Exception as exc:
        table.add_row("OpenCV", "FAIL", repr(exc))

    try:
        import mediapipe as mp

        table.add_row("MediaPipe", "OK", getattr(mp, "__version__", "unknown"))
    except Exception as exc:
        table.add_row("MediaPipe", "FAIL", repr(exc))

    # SAM 3 availability check (informational, no failure)
    try:
        import sam3  # noqa: F401

        table.add_row("SAM 3", "OK", "Installed; will attempt MPS at run start")
    except Exception:
        table.add_row("SAM 3", "MISSING", "Will fall back to SAM 2.1 (expected on Mac)")

    try:
        import sam2  # noqa: F401

        table.add_row("SAM 2.1", "OK", "Installed")
    except Exception:
        table.add_row("SAM 2.1", "MISSING", "Install via pip install sam2 before Phase C")

    console.print(table)


@app.command()
def preprocess(
    videos: Annotated[list[Path], typer.Argument(help="One or more video paths to preprocess")],
    run_id: Annotated[str | None, typer.Option("--run", help="Custom run ID; default is timestamp")] = None,
    target_fps: Annotated[int, typer.Option(help="Output framerate target")] = 30,
    image_format: Annotated[str, typer.Option(help="jpg (smaller, lossy) or png (lossless, large)")] = "jpg",
    image_quality: Annotated[int, typer.Option(help="JPEG quality 1-100 (ignored for png)")] = 92,
    spot_check: Annotated[bool, typer.Option("--spot-check/--no-spot-check", help="Save preview-quality segmentation panels for visual spot check (MediaPipe SelfieSegmentation; not production segmentation)")] = True,
    spot_check_samples: Annotated[int, typer.Option(help="Number of evenly spaced sample frames per video for the spot check")] = 6,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Extract frames from videos at normalized framerate."""
    _setup_logging(verbose)
    config = PipelineConfig()
    if run_id:
        config.run_id = run_id
    config.preprocess.target_fps = target_fps
    config.preprocess.image_format = image_format
    config.preprocess.image_quality = image_quality
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.save(config.output_dir / "config.yaml")

    metadatas = preprocess_many(videos, config)

    table = Table(title=f"Preprocessing complete: run {config.run_id}")
    table.add_column("Video")
    table.add_column("Input fps")
    table.add_column("Input frames")
    table.add_column("Output fps")
    table.add_column("Output frames")
    table.add_column("Rotation")
    for m in metadatas:
        table.add_row(
            m.video_id,
            f"{m.input_fps:.1f}",
            str(m.input_frame_count),
            str(m.output_fps),
            str(m.output_frame_count),
            f"{m.input_rotation} deg",
        )
    console.print(table)
    console.print(f"\nFrames at: {config.output_dir / 'frames'}")
    console.print(f"Config at: {config.output_dir / 'config.yaml'}")

    if spot_check:
        from gma_pipeline.segment import make_segmenter

        models_dir = config.project_root / "models"
        segmenter = make_segmenter(config.segmentation.backend, models_dir)
        console.print(f"\n[bold yellow]Spot check using {segmenter.name} backend[/bold yellow]")
        for m in metadatas:
            frames_dir = config.output_dir / "frames" / m.video_id
            result = spot_check_video(m.video_id, frames_dir, config.output_dir, n_samples=spot_check_samples, segmenter=segmenter)
            console.print(f"  {m.video_id}: {len(result.sample_frames_saved)} panels (mean cov={result.mean_mask_coverage*100:.1f}%, score={result.mean_score:.2f})")


@app.command("spot-check")
def spot_check_cmd(
    run_id: Annotated[str, typer.Argument(help="Existing run id whose frames you want to spot-check")],
    n_samples: Annotated[int, typer.Option(help="Number of evenly spaced sample frames per video")] = 6,
    backend: Annotated[str, typer.Option(help="Segmenter backend: auto | sam3 | sam2 | mediapipe")] = "auto",
    sam2_variant: Annotated[str, typer.Option(help="SAM 2.1 backbone: tiny | small | base_plus | large. tiny gives coherent whole-body; base_plus/large split diaper from skin.")] = "tiny",
    sam3_prompt: Annotated[str, typer.Option(help="SAM 3 text prompt (only used when --backend sam3)")] = "infant in diaper",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Re-run the spot check on an existing run's already-extracted frames."""
    _setup_logging(verbose)
    config = PipelineConfig(run_id=run_id)
    frames_root = config.output_dir / "frames"
    if not frames_root.exists():
        console.print(f"[red]No frames found at {frames_root}. Run preprocess first.[/red]")
        raise typer.Exit(code=1)

    # Build segmenter once, reuse across videos (avoids reloading the SAM model 3x)
    from gma_pipeline.segment import make_segmenter

    models_dir = config.project_root / "models"
    segmenter = make_segmenter(backend, models_dir, sam2_variant=sam2_variant, sam3_prompt=sam3_prompt)
    console.print(f"[bold yellow]Spot-check using {segmenter.name} backend[/bold yellow]")

    summary_table = Table(title="Spot-check summary")
    summary_table.add_column("Video")
    summary_table.add_column("Backend")
    summary_table.add_column("Panels")
    summary_table.add_column("Mean coverage")
    summary_table.add_column("Mean score")

    for video_dir in sorted(frames_root.iterdir()):
        if not video_dir.is_dir():
            continue
        video_id = video_dir.name
        result = spot_check_video(video_id, video_dir, config.output_dir, n_samples=n_samples, segmenter=segmenter)
        summary_table.add_row(
            result.video_id,
            result.backend,
            str(len(result.sample_frames_saved)),
            f"{result.mean_mask_coverage * 100:.1f}%",
            f"{result.mean_score:.2f}",
        )
    console.print(summary_table)


@app.command("pose-check")
def pose_check_cmd(
    run_id: Annotated[str, typer.Argument(help="Existing run id whose frames you want to pose-check")],
    n_samples: Annotated[int, typer.Option(help="Number of evenly spaced sample frames per video")] = 6,
    seg_backend: Annotated[str, typer.Option(help="Segmenter backend for mask guidance: auto | sam3 | sam2 | mediapipe")] = "auto",
    sam2_variant: Annotated[str, typer.Option(help="SAM 2.1 backbone: tiny | small | base_plus | large")] = "tiny",
    sam3_prompt: Annotated[str, typer.Option(help="SAM 3 text prompt (only used when --backend sam3)")] = "infant in diaper",
    pose_variant: Annotated[str, typer.Option(help="MediaPipe pose variant: lite | full | heavy")] = "full",
    use_mask: Annotated[bool, typer.Option("--use-mask/--no-mask", help="Darken background with SAM mask before pose inference")] = True,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Run pose estimation on a few sample frames per video.

    Pipeline per sample frame:
      1. Read extracted frame from disk
      2. Run segmenter to get a mask (used to suppress background detections)
      3. Run pose estimator on the mask-guided frame
      4. Render a 2-panel image: mask-overlay + pose-skeleton-on-original
    """
    _setup_logging(verbose)
    config = PipelineConfig(run_id=run_id)
    frames_root = config.output_dir / "frames"
    if not frames_root.exists():
        console.print(f"[red]No frames found at {frames_root}. Run preprocess first.[/red]")
        raise typer.Exit(code=1)

    from gma_pipeline.pose import draw_skeleton, make_pose_estimator
    from gma_pipeline.segment import make_segmenter
    from gma_pipeline.spot_check import _pick_sample_indices

    models_dir = config.project_root / "models"
    segmenter = make_segmenter(seg_backend, models_dir, sam2_variant=sam2_variant, sam3_prompt=sam3_prompt)
    pose = make_pose_estimator("mediapipe", models_dir, mediapipe_variant=pose_variant)
    console.print(f"[bold yellow]pose-check using seg={segmenter.name}, pose={pose.name}, use_mask={use_mask}[/bold yellow]")

    summary = Table(title="pose-check summary")
    summary.add_column("Video")
    summary.add_column("Panels")
    summary.add_column("Mean pose conf")
    summary.add_column("Detected/Total")

    for video_dir in sorted(frames_root.iterdir()):
        if not video_dir.is_dir():
            continue
        video_id = video_dir.name
        segmenter.video_id = video_id
        pose.video_id = video_id
        out_dir = config.output_dir / "spot_check" / video_id / "pose"
        out_dir.mkdir(parents=True, exist_ok=True)
        frame_files = sorted([p for p in video_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
        indices = _pick_sample_indices(len(frame_files), n_samples)
        confs = []
        detected = 0
        for idx in indices:
            frame_path = frame_files[idx]
            frame_bgr = cv2.imread(str(frame_path))
            if frame_bgr is None:
                continue
            seg_res = segmenter.segment_frame(frame_bgr, frame_idx=idx)
            mask = seg_res.mask if use_mask else None
            pose_res = pose.estimate_frame(frame_bgr, mask=mask, frame_idx=idx)
            if pose_res.detected:
                detected += 1
                confs.append(pose_res.mean_confidence)
            # Render 2-panel: SAM mask overlay + pose skeleton on original
            seg_overlay = frame_bgr.copy()
            binary = (seg_res.mask > 127).astype(np.uint8)
            seg_overlay[binary == 0] = (seg_overlay[binary == 0].astype(np.float32) * 0.3).astype(np.uint8)
            green = np.zeros_like(seg_overlay); green[:, :, 1] = 60
            seg_overlay = cv2.addWeighted(seg_overlay, 1.0, green * binary[:, :, None], 1.0, 0)
            pose_overlay = draw_skeleton(frame_bgr, pose_res)
            panel = np.concatenate([seg_overlay, pose_overlay], axis=1)
            h = frame_bgr.shape[0]
            label_h = max(28, h // 30)
            label = np.zeros((label_h, panel.shape[1], 3), dtype=np.uint8)
            cv2.putText(label, f"SEG overlay ({segmenter.name})", (10, label_h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(label, f"POSE ({pose.name}) detected={pose_res.detected} conf={pose_res.mean_confidence:.2f}", (frame_bgr.shape[1] + 10, label_h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            panel = np.concatenate([label, panel], axis=0)
            out_path = out_dir / f"sample_{idx:06d}_pose.jpg"
            cv2.imwrite(str(out_path), panel, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
        summary.add_row(
            video_id,
            str(len(indices)),
            f"{(np.mean(confs)*100 if confs else 0):.1f}%",
            f"{detected}/{len(indices)}",
        )
    console.print(summary)


@app.command("overlays")
def overlays_cmd(
    run_id: Annotated[str, typer.Argument(help="Existing run id to generate overlays for")],
    every: Annotated[int, typer.Option(help="Sample every Nth frame (default 100 -> roughly one overlay every 3-4 seconds of 30 fps video)")] = 100,
    only_video: Annotated[str | None, typer.Option(help="Only process this video_id")] = None,
    pose_variant: Annotated[str, typer.Option(help="MediaPipe pose variant for left/right disambiguation")] = "full",
    skip_existing: Annotated[bool, typer.Option("--skip-existing/--overwrite", help="Skip overlay files that already exist on disk")] = True,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Generate body-parts colored overlays at every-Nth-frame for a finished run.

    Produces a visual record of the segmentation + body-part labeling at
    regular intervals across each video, matching the
    sample_<frame_idx>_parts.jpg format produced by body-parts-check. This
    command runs that pipeline retroactively on an existing run id, sampling
    every Nth frame. Alternatively, pose-extract can be invoked with
    --save-overlays-every N, which runs the same logic inline.
    """
    _setup_logging(verbose)
    import json as _json
    from datetime import datetime, timedelta

    from gma_pipeline.body_parts import body_parts_for_frame, render_body_parts_panel, write_body_parts_json
    from gma_pipeline.pose import make_pose_estimator
    from gma_pipeline.segment import SAM3Segmenter
    from tqdm import tqdm

    config = PipelineConfig(run_id=run_id)
    frames_root = config.output_dir / "frames"
    if not frames_root.exists():
        console.print(f"[red]No frames at {frames_root}.[/red]")
        raise typer.Exit(code=1)

    models_dir = config.project_root / "models"
    sam3 = SAM3Segmenter(models_dir, device="mps", text_prompt="infant in diaper")
    sam3._ensure_processor()
    processor = sam3._processor
    pose = make_pose_estimator("mediapipe", models_dir, mediapipe_variant=pose_variant)
    console.print(f"[bold yellow]overlays: SAM 3 + {pose.name}, every {every} frames[/bold yellow]")

    summary = Table(title=f"overlays summary: run {run_id}")
    summary.add_column("Video")
    summary.add_column("Sampled")
    summary.add_column("Saved")
    summary.add_column("Skipped (exist)")

    for video_dir in sorted(frames_root.iterdir()):
        if not video_dir.is_dir():
            continue
        video_id = video_dir.name
        if only_video and video_id != only_video:
            continue
        pose.video_id = video_id
        sam3.video_id = video_id

        # Load metadata for timestamps
        meta_path = video_dir / "metadata.json"
        output_fps = 30
        creation_local_dt: datetime | None = None
        if meta_path.exists():
            meta = _json.loads(meta_path.read_text())
            output_fps = int(meta.get("output_fps", 30)) or 30
            iso = meta.get("creation_datetime_local_iso")
            if iso:
                try:
                    if len(iso) >= 5 and (iso[-5] in "+-") and iso[-3] != ":":
                        iso = iso[:-2] + ":" + iso[-2:]
                    creation_local_dt = datetime.fromisoformat(iso)
                except Exception:
                    pass

        out_dir = config.output_dir / "body_parts" / video_id
        out_dir.mkdir(parents=True, exist_ok=True)
        frame_files = sorted([p for p in video_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
        indices = list(range(0, len(frame_files), max(1, every)))
        saved = 0
        skipped = 0
        for idx in tqdm(indices, desc=f"overlays {video_id}", unit="frame"):
            out_path = out_dir / f"sample_{idx:06d}_parts.jpg"
            json_path = out_dir / f"sample_{idx:06d}_parts.json"
            if skip_existing and out_path.exists() and json_path.exists():
                skipped += 1
                continue
            frame_path = frame_files[idx]
            frame_bgr = cv2.imread(str(frame_path))
            if frame_bgr is None:
                continue
            pose_res = pose.estimate_frame(frame_bgr, mask=None, frame_idx=idx)
            pose_kp = pose_res.keypoints if pose_res.detected else None
            frame_time_s = float(idx) / float(output_fps) if output_fps else 0.0
            absolute_iso = (
                (creation_local_dt + timedelta(seconds=frame_time_s)).isoformat()
                if creation_local_dt
                else None
            )
            fbp = body_parts_for_frame(
                frame_bgr=frame_bgr,
                processor=processor,
                pose_kp=pose_kp,
                video_id=video_id,
                frame_idx=idx,
                frame_time_seconds=frame_time_s,
                absolute_datetime=absolute_iso,
            )
            panel = render_body_parts_panel(frame_bgr, fbp)
            cv2.imwrite(str(out_path), panel, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
            write_body_parts_json(fbp, json_path)
            saved += 1
        summary.add_row(video_id, str(len(indices)), str(saved), str(skipped))
    console.print(summary)


@app.command("body-parts-check")
def body_parts_check_cmd(
    run_id: Annotated[str, typer.Argument(help="Existing run id whose frames to label")],
    n_samples: Annotated[int, typer.Option(help="Number of evenly spaced sample frames per video")] = 6,
    pose_variant: Annotated[str, typer.Option(help="MediaPipe pose variant: lite | full | heavy")] = "full",
    only_video: Annotated[str | None, typer.Option(help="Only process this video_id")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Run SAM 3 with body-part text prompts on sample frames and produce
    color-labeled overlays (head, torso, diaper, left/right arm, left/right leg).

    Pose keypoints disambiguate left vs right anatomically (SAM 3's directional
    text understanding uses observer-perspective, which inverts for overhead
    supine videos).
    """
    _setup_logging(verbose)
    config = PipelineConfig(run_id=run_id)
    frames_root = config.output_dir / "frames"
    if not frames_root.exists():
        console.print(f"[red]No frames found at {frames_root}. Run preprocess first.[/red]")
        raise typer.Exit(code=1)

    from gma_pipeline.body_parts import body_parts_for_frame, render_body_parts_panel, write_body_parts_json
    from gma_pipeline.pose import make_pose_estimator
    from gma_pipeline.segment import SAM3Segmenter
    from gma_pipeline.spot_check import _pick_sample_indices

    models_dir = config.project_root / "models"
    # SAM 3 only - body-part labeling depends on text prompts
    sam3 = SAM3Segmenter(models_dir, device="mps", text_prompt="infant in diaper")
    sam3._ensure_processor()
    processor = sam3._processor
    pose = make_pose_estimator("mediapipe", models_dir, mediapipe_variant=pose_variant)
    console.print(f"[bold yellow]body-parts-check using SAM 3 + {pose.name}[/bold yellow]")

    summary = Table(title=f"body-parts summary: run {run_id}")
    summary.add_column("Video")
    summary.add_column("Samples")
    summary.add_column("Avg parts/frame")

    import json
    from datetime import datetime, timedelta

    for video_dir in sorted(frames_root.iterdir()):
        if not video_dir.is_dir():
            continue
        video_id = video_dir.name
        if only_video and video_id != only_video:
            continue
        pose.video_id = video_id
        sam3.video_id = video_id
        out_dir = config.output_dir / "body_parts" / video_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Load metadata for timestamps
        meta_path = video_dir / "metadata.json"
        output_fps = 30
        creation_local_dt: datetime | None = None
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            output_fps = int(meta.get("output_fps", 30)) or 30
            iso = meta.get("creation_datetime_local_iso")
            if iso:
                try:
                    if len(iso) >= 5 and (iso[-5] in "+-") and iso[-3] != ":":
                        iso = iso[:-2] + ":" + iso[-2:]
                    creation_local_dt = datetime.fromisoformat(iso)
                except Exception:
                    pass

        frame_files = sorted([p for p in video_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
        if not frame_files:
            continue
        indices = _pick_sample_indices(len(frame_files), n_samples)
        n_parts_list: list[int] = []
        for idx in indices:
            frame_path = frame_files[idx]
            frame_bgr = cv2.imread(str(frame_path))
            if frame_bgr is None:
                continue
            # Get pose keypoints (no mask guidance needed - the pose is just for left/right)
            pose_res = pose.estimate_frame(frame_bgr, mask=None, frame_idx=idx)
            pose_kp = pose_res.keypoints if pose_res.detected else None
            frame_time_s = float(idx) / float(output_fps) if output_fps else 0.0
            absolute_iso = (
                (creation_local_dt + timedelta(seconds=frame_time_s)).isoformat()
                if creation_local_dt
                else None
            )
            fbp = body_parts_for_frame(
                frame_bgr=frame_bgr,
                processor=processor,
                pose_kp=pose_kp,
                video_id=video_id,
                frame_idx=idx,
                frame_time_seconds=frame_time_s,
                absolute_datetime=absolute_iso,
            )
            panel = render_body_parts_panel(frame_bgr, fbp)
            out_path = out_dir / f"sample_{idx:06d}_parts.jpg"
            cv2.imwrite(str(out_path), panel, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
            write_body_parts_json(fbp, out_dir / f"sample_{idx:06d}_parts.json")
            n_parts_list.append(len(fbp.parts))
        avg = float(np.mean(n_parts_list)) if n_parts_list else 0.0
        summary.add_row(video_id, str(len(n_parts_list)), f"{avg:.1f}")
        console.print(f"  {video_id}: panels at {out_dir}")
    console.print(summary)


@app.command("pose-extract")
def pose_extract_cmd(
    run_id: Annotated[str, typer.Argument(help="Run id whose frames to process")],
    seg_backend: Annotated[str, typer.Option(help="Segmenter backend: auto | sam3 | sam2 | mediapipe")] = "auto",
    sam2_variant: Annotated[str, typer.Option(help="SAM 2.1 backbone: tiny | small | base_plus | large")] = "tiny",
    sam3_prompt: Annotated[str, typer.Option(help="SAM 3 text prompt (only used when --backend sam3)")] = "infant in diaper",
    pose_variant: Annotated[str, typer.Option(help="MediaPipe pose variant: lite | full | heavy")] = "full",
    use_mask: Annotated[bool, typer.Option("--use-mask/--no-mask", help="Darken background with SAM mask before pose inference")] = True,
    rotation_normalize: Annotated[bool, typer.Option("--rotate/--no-rotate", help="Apply principal-axis rotation normalization")] = True,
    save_overlays_every: Annotated[int, typer.Option(help="Save a body-parts colored overlay every Nth frame (0 = disabled). Adds roughly 2-3s per overlay frame for the multi-prompt SAM 3 calls.")] = 0,
    max_frames: Annotated[int | None, typer.Option(help="Cap the number of frames per video (smoke test mode)")] = None,
    only_video: Annotated[str | None, typer.Option(help="Only process this video_id (e.g. IMG_0001)")] = None,
    skip_existing: Annotated[bool, typer.Option("--skip-existing/--overwrite", help="Skip videos that already have a parquet")] = True,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Extract pose keypoints for every frame of every video in a run.

    Output: outputs/<run>/poses/<video_id>.parquet with columns video_id,
    frame_idx, keypoint, x, y, confidence, detected, rotation_applied_degrees.
    """
    _setup_logging(verbose)
    from tqdm import tqdm

    from gma_pipeline.pose import keypoints_to_records, make_pose_estimator
    from gma_pipeline.segment import make_segmenter

    config = PipelineConfig(run_id=run_id)
    frames_root = config.output_dir / "frames"
    if not frames_root.exists():
        console.print(f"[red]No frames at {frames_root}. Run preprocess first.[/red]")
        raise typer.Exit(code=1)

    poses_root = config.output_dir / "poses"
    poses_root.mkdir(parents=True, exist_ok=True)

    models_dir = config.project_root / "models"
    segmenter = make_segmenter(seg_backend, models_dir, sam2_variant=sam2_variant, sam3_prompt=sam3_prompt)
    pose = make_pose_estimator("mediapipe", models_dir, mediapipe_variant=pose_variant)
    pose.rotation_normalize = rotation_normalize
    # Rebuild the name suffix to reflect rotation choice
    pose.name = f"mediapipe-{pose_variant}{'+rot' if rotation_normalize else ''}"
    console.print(f"[bold yellow]pose-extract: seg={segmenter.name}, pose={pose.name}, use_mask={use_mask}[/bold yellow]")

    summary = Table(title=f"pose-extract summary: run {config.run_id}")
    summary.add_column("Video")
    summary.add_column("Frames processed")
    summary.add_column("Detected")
    summary.add_column("Mean conf")
    summary.add_column("Runtime")
    summary.add_column("Output")

    import pandas as pd

    import json
    from datetime import datetime, timedelta

    for video_dir in sorted(frames_root.iterdir()):
        if not video_dir.is_dir():
            continue
        video_id = video_dir.name
        if only_video and video_id != only_video:
            continue
        out_path = poses_root / f"{video_id}.parquet"
        if out_path.exists() and skip_existing:
            console.print(f"[dim]Skipping {video_id} (parquet exists). Use --overwrite to redo.[/dim]")
            continue
        segmenter.video_id = video_id
        pose.video_id = video_id

        # Optional inline body-parts overlay generation. Built lazily because it
        # requires the SAM 3 processor (not the same as the seg_backend that may
        # be SAM 2.1). If --save-overlays-every > 0, every Nth frame also runs
        # the multi-prompt body-parts pipeline and writes a colored overlay
        # alongside the pose parquet.
        overlay_processor = None
        overlay_dir = None
        if save_overlays_every > 0:
            from gma_pipeline.body_parts import body_parts_for_frame, render_body_parts_panel, write_body_parts_json
            from gma_pipeline.segment import SAM3Segmenter

            if isinstance(segmenter, SAM3Segmenter):
                overlay_processor = segmenter._processor
            else:
                sam3_for_overlay = SAM3Segmenter(models_dir, device="mps", text_prompt=sam3_prompt, video_id=video_id)
                sam3_for_overlay._ensure_processor()
                overlay_processor = sam3_for_overlay._processor
            overlay_dir = config.output_dir / "body_parts" / video_id
            overlay_dir.mkdir(parents=True, exist_ok=True)

        # Load per-video metadata.json for fps and creation timestamp
        meta_path = video_dir / "metadata.json"
        output_fps = 30
        creation_local_iso: str | None = None
        creation_local_dt: datetime | None = None
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            output_fps = int(meta.get("output_fps", 30)) or 30
            creation_local_iso = meta.get("creation_datetime_local_iso")
            if creation_local_iso:
                try:
                    # Normalize ffprobe-style offset like '-0700' -> '-07:00'
                    iso = creation_local_iso
                    if len(iso) >= 5 and (iso[-5] in "+-") and iso[-3] != ":":
                        iso = iso[:-2] + ":" + iso[-2:]
                    creation_local_dt = datetime.fromisoformat(iso)
                except Exception as exc:
                    logger.warning("Failed to parse %s creation_datetime: %s", video_id, exc)

        frame_files = sorted([p for p in video_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
        if max_frames is not None:
            frame_files = frame_files[:max_frames]
        all_rows: list[dict] = []
        n_detected = 0
        confs: list[float] = []
        t0 = time.time()
        for i, frame_path in enumerate(tqdm(frame_files, desc=f"pose {video_id}", unit="frame")):
            frame_bgr = cv2.imread(str(frame_path))
            if frame_bgr is None:
                continue
            seg_res = segmenter.segment_frame(frame_bgr, frame_idx=i)
            mask = seg_res.mask if use_mask else None
            pose_res = pose.estimate_frame(frame_bgr, mask=mask, frame_idx=i)
            if pose_res.detected:
                n_detected += 1
                confs.append(pose_res.mean_confidence)
            # Per-frame timestamps
            frame_time_s = float(i) / float(output_fps) if output_fps else 0.0
            absolute_iso: str | None = None
            if creation_local_dt is not None:
                absolute_iso = (creation_local_dt + timedelta(seconds=frame_time_s)).isoformat()

            rows = keypoints_to_records(pose_res)
            for r in rows:
                r["detected"] = pose_res.detected
                r["rotation_applied_degrees"] = pose_res.rotation_applied_degrees
                r["frame_time_seconds"] = frame_time_s
                r["absolute_datetime"] = absolute_iso
            if not rows:
                all_rows.append(
                    {
                        "video_id": video_id,
                        "frame_idx": i,
                        "keypoint": "__nodetection__",
                        "x": float("nan"),
                        "y": float("nan"),
                        "confidence": 0.0,
                        "detected": False,
                        "rotation_applied_degrees": pose_res.rotation_applied_degrees,
                        "frame_time_seconds": frame_time_s,
                        "absolute_datetime": absolute_iso,
                    }
                )
            else:
                all_rows.extend(rows)

            # Save overlay every Nth frame if requested
            if overlay_processor is not None and overlay_dir is not None and (i % save_overlays_every) == 0:
                from gma_pipeline.body_parts import body_parts_for_frame, render_body_parts_panel, write_body_parts_json

                fbp = body_parts_for_frame(
                    frame_bgr=frame_bgr,
                    processor=overlay_processor,
                    pose_kp=pose_res.keypoints if pose_res.detected else None,
                    video_id=video_id,
                    frame_idx=i,
                    frame_time_seconds=frame_time_s,
                    absolute_datetime=absolute_iso,
                )
                panel = render_body_parts_panel(frame_bgr, fbp)
                cv2.imwrite(str(overlay_dir / f"sample_{i:06d}_parts.jpg"), panel, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
                write_body_parts_json(fbp, overlay_dir / f"sample_{i:06d}_parts.json")
        runtime = time.time() - t0
        df = pd.DataFrame(all_rows)
        df.to_parquet(out_path, index=False)
        mean_conf = float(np.mean(confs)) * 100 if confs else 0.0
        summary.add_row(
            video_id,
            str(len(frame_files)),
            f"{n_detected}/{len(frame_files)}",
            f"{mean_conf:.1f}%",
            f"{runtime:.1f}s",
            str(out_path.relative_to(config.project_root)),
        )
    console.print(summary)


@app.command("gma-evaluate")
def gma_evaluate_cmd(
    run_id: Annotated[str, typer.Argument(help="Run id whose pose parquets to evaluate")],
    only_video: Annotated[str | None, typer.Option(help="Only evaluate this video_id (e.g. IMG_0001)")] = None,
    trim_rolling: Annotated[bool, typer.Option("--trim-rolling/--no-trim-rolling", help="Legacy single trailing-roll truncation (only used with --no-validity-mask). Default ON.")] = True,
    use_validity_mask: Annotated[bool, typer.Option("--validity-mask/--no-validity-mask", help="Per-frame supine-validity masking: exclude EVERY rolling/side-lying/prone frame (multiple valid segments supported). Default ON; supersedes --trim-rolling.")] = True,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Read pose parquets, compute kinematic features, MOS-R proxy scores, and render markdown + HTML reports."""
    _setup_logging(verbose)
    import json as _json

    from gma_pipeline.calibration import analyze_segmental_asymmetry, segmental_analysis_to_dict
    from gma_pipeline.features import extract_features_from_parquet, features_to_dataframe
    from gma_pipeline.html_report import build_dashboard_html, build_video_html
    from gma_pipeline.mos_r import compute_mosr_proxy, mosr_proxy_to_dict
    from gma_pipeline.report import build_report, build_segmental_report
    from gma_pipeline.scoring import score_video, write_scoring_json
    from gma_pipeline.viz import plot_mosr_summary, plot_segmental_concordance, plot_validity_timeline

    config = PipelineConfig(run_id=run_id)
    poses_root = config.output_dir / "poses"
    if not poses_root.exists():
        console.print(f"[red]No poses directory at {poses_root}. Run pose-extract first.[/red]")
        raise typer.Exit(code=1)
    reports_root = config.output_dir / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)
    plots_dir = reports_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    parquets = sorted(poses_root.glob("*.parquet"))
    if not parquets:
        console.print(f"[red]No parquet files in {poses_root}.[/red]")
        raise typer.Exit(code=1)

    summary = Table(title=f"gma-evaluate summary: run {run_id}")
    summary.add_column("Video")
    summary.add_column("Frames")
    summary.add_column("Valid supine")
    summary.add_column("MOS-R F+C/16")
    summary.add_column("MOS-R UB/28")
    summary.add_column("Mvmt char")

    features_by_video: dict = {}
    mosr_by_video: dict = {}
    scoring_by_video: dict = {}

    for parquet in parquets:
        video_id = parquet.stem
        if only_video and video_id != only_video:
            continue
        # Read frame dimensions from metadata.json
        meta_path = config.output_dir / "frames" / video_id / "metadata.json"
        if not meta_path.exists():
            console.print(f"[yellow]Skipping {video_id}: no metadata.json[/yellow]")
            continue
        meta = _json.loads(meta_path.read_text())
        frame_w = int(meta["output_width"])
        frame_h = int(meta["output_height"])
        fps = float(meta["output_fps"]) or 30.0
        console.print(f"[bold yellow]Evaluating {video_id} ({frame_w}x{frame_h} at {fps:g} fps)[/bold yellow]")

        features = extract_features_from_parquet(
            parquet, frame_w, frame_h, fps=fps, trim_rolling=trim_rolling, use_validity_mask=use_validity_mask
        )
        seg_str = ", ".join(f"{a/fps:.1f}-{b/fps:.1f}s" for a, b in features.valid_segments)
        console.print(
            f"  [dim]supine-validity mask: {features.valid_supine_fraction*100:.1f}% valid across "
            f"{len(features.valid_segments)} segment(s) [{seg_str}]; {features.n_invalid_segments} "
            f"rolling/prone segment(s) excluded[/dim]"
        )
        features_df = features_to_dataframe(features)
        features_df.to_parquet(reports_root / f"{video_id}-features.parquet", index=False)

        scoring = score_video(features)
        write_scoring_json(scoring, reports_root / f"{video_id}-scoring.json")

        mosr = compute_mosr_proxy(features)
        (reports_root / f"{video_id}-mos-r-proxy.json").write_text(_json.dumps(mosr_proxy_to_dict(mosr), indent=2))

        try:
            plot_validity_timeline(parquet, features, plots_dir / f"{video_id}-validity-timeline.png")
        except Exception as exc:
            console.print(f"  [yellow]validity-timeline plot failed: {exc}[/yellow]")

        report_path = build_report(
            features=features,
            scoring=scoring,
            parquet_path=parquet,
            output_dir=reports_root,
            mosr=mosr,
        )
        features_by_video[video_id] = features
        mosr_by_video[video_id] = mosr
        scoring_by_video[video_id] = scoring

        mc = scoring.subscales["movement_character"].score_0_to_5
        summary.add_row(
            video_id,
            str(features.n_frames),
            f"{features.valid_supine_fraction*100:.0f}% ({features.n_invalid_segments} seg)",
            f"{mosr.computable_total:g}/{mosr.computable_max}",
            f"{mosr.upper_bound_28:g}/28",
            f"{mc:.2f}" if not (mc != mc) else "n/a",
        )
        console.print(f"  report: {report_path.relative_to(config.project_root)}")

    # Cross-video: the pipeline's own segmental assessment, plots, HTML dashboard.
    if features_by_video:
        analysis = analyze_segmental_asymmetry(features_by_video)
        (reports_root / "segmental-asymmetry-independent.json").write_text(
            _json.dumps(segmental_analysis_to_dict(analysis), indent=2, default=str)
        )
        s = analysis.pt_provisional_agreement
        top3 = [f.keypoint for f in analysis.findings[:3]]
        console.print(
            f"[bold green]Independent assessment:[/bold green] top standouts {', '.join(top3)}; "
            f"conservative flag: {', '.join(analysis.pipeline_flagged) or 'none'}. "
            f"[dim]Provisional-PT coincidence (NOT validation): both-flag={s['both_flag']} "
            f"both-clear={s['both_clear']} pipeline-only={s['pipeline_only']} PT-only={s['pt_only']}[/dim]"
        )
        seg_report = build_segmental_report(analysis, reports_root)
        console.print(f"  segmental report: {seg_report.relative_to(config.project_root)}")

        try:
            plot_segmental_concordance(analysis, plots_dir / "segmental-concordance.png")
            plot_mosr_summary(mosr_by_video, plots_dir / "mosr-summary.png")
        except Exception as exc:
            console.print(f"  [yellow]cross-video plot failed: {exc}[/yellow]")

        try:
            for vid, feats in features_by_video.items():
                build_video_html(feats, scoring_by_video[vid], mosr_by_video[vid], plots_dir, reports_root)
            dash = build_dashboard_html(features_by_video, mosr_by_video, analysis, plots_dir, reports_root)
            console.print(f"  [bold green]HTML dashboard:[/bold green] {dash.relative_to(config.project_root)}")
        except Exception as exc:
            console.print(f"  [yellow]HTML generation failed: {exc}[/yellow]")

    console.print(summary)


@app.command()
def run(
    videos: Annotated[list[Path], typer.Argument(help="One or more video paths")],
    run_id: Annotated[str | None, typer.Option("--run", help="Custom run ID; default is timestamp")] = None,
    aggregate: Annotated[bool, typer.Option(help="Aggregate scoring across all videos")] = False,
    publish_to_vault: Annotated[bool, typer.Option("--publish-to-vault", help="Copy report to Research/ folder in vault")] = False,
    segmenter: Annotated[str, typer.Option(help="auto | sam3 | sam2 | none")] = "auto",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Run full pipeline: preprocess -> segment -> pose -> features -> score -> report.

    Currently only preprocess is implemented. Other phases are stubs.
    """
    _setup_logging(verbose)
    config = PipelineConfig()
    if run_id:
        config.run_id = run_id
    config.segmentation.backend = segmenter
    config.publish_to_vault = publish_to_vault
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.save(config.output_dir / "config.yaml")

    console.print("[bold yellow]Phase B (preprocess)[/bold yellow]")
    metadatas = preprocess_many(videos, config)
    for m in metadatas:
        console.print(f"  preprocessed {m.video_id}: {m.output_frame_count} frames")

    console.print("[dim]Phase C (segment), D (pose), E (features), F (score), G (report) are stubs in this session.[/dim]")
    console.print(f"\nOutputs: {config.output_dir}")


if __name__ == "__main__":
    app()
