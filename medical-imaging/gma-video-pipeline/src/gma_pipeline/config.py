"""Central config for the GMA pipeline.

Run configs are dataclasses so they can be hashed for reproducibility stamps
and serialized to outputs/<run>/config.yaml.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import yaml


@dataclass
class PreprocessConfig:
    target_fps: int = 30
    auto_rotate: bool = True
    crop: tuple[int, int, int, int] | None = None  # (x, y, w, h) or None for full frame
    image_format: str = "jpg"  # jpg keeps output size under control; png for max fidelity
    image_quality: int = 92


@dataclass
class SegmentationConfig:
    backend: str = "auto"  # auto | sam3 | sam2 | none
    text_prompt: str = "infant in diaper"  # SAM 3 only
    seed_point_strategy: str = "center"  # SAM 2 fallback: center | manual
    mask_format: str = "png"


@dataclass
class PoseConfig:
    backend: str = "auto"  # auto | ostadabbas | mediapipe | ensemble
    min_confidence: float = 0.5
    use_mask: bool = True  # multiply input frame by mask before pose inference


@dataclass
class FeaturesConfig:
    window_seconds: float = 30.0
    window_overlap: float = 0.5  # 50 percent overlap
    smoothing_sigma_frames: float = 2.0  # gaussian smoothing on keypoint trajectories


@dataclass
class ScoringConfig:
    threshold_version: str = "v0.1-2026-05-24"
    fidgety_quality_jerk_threshold: float = 0.5  # placeholder; calibrate in Phase H
    movement_repertoire_entropy_threshold: float = 1.0
    symmetry_index_normal_range: tuple[float, float] = (0.8, 1.2)


@dataclass
class PipelineConfig:
    """Top-level config for a single pipeline run."""

    run_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d-%H%M%S"))
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    segmentation: SegmentationConfig = field(default_factory=SegmentationConfig)
    pose: PoseConfig = field(default_factory=PoseConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    publish_to_vault: bool = False

    @property
    def output_dir(self) -> Path:
        return self.project_root / "outputs" / self.run_id

    @property
    def inputs_dir(self) -> Path:
        return self.project_root / "inputs"

    @property
    def models_dir(self) -> Path:
        return self.project_root / "models"

    def config_hash(self) -> str:
        """Stable hash of the config for reproducibility stamping."""
        payload = json.dumps(self._serialize(), sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()[:12]

    def _serialize(self) -> dict:
        data = asdict(self)
        data["project_root"] = str(self.project_root)
        return data

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fh:
            yaml.safe_dump(self._serialize(), fh, sort_keys=False)

    @classmethod
    def load(cls, path: Path) -> PipelineConfig:
        with path.open() as fh:
            data = yaml.safe_load(fh)
        data["project_root"] = Path(data["project_root"])
        sub_configs = {
            "preprocess": PreprocessConfig(**data.pop("preprocess")),
            "segmentation": SegmentationConfig(**data.pop("segmentation")),
            "pose": PoseConfig(**data.pop("pose")),
            "features": FeaturesConfig(**data.pop("features")),
            "scoring": ScoringConfig(**data.pop("scoring")),
        }
        return cls(**data, **sub_configs)
