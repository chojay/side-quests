"""Smoke tests for PipelineConfig: config save/load roundtrip."""

from __future__ import annotations

from pathlib import Path

from gma_pipeline.config import PipelineConfig


def test_config_default_run_id_is_timestamp() -> None:
    config = PipelineConfig()
    assert len(config.run_id) >= 13  # YYYYMMDD-HHMMSS minimum
    assert "-" in config.run_id


def test_config_hash_is_stable() -> None:
    config = PipelineConfig(run_id="fixed")
    h1 = config.config_hash()
    h2 = config.config_hash()
    assert h1 == h2
    assert len(h1) == 12


def test_config_save_and_load_roundtrip(tmp_path: Path) -> None:
    config = PipelineConfig(run_id="roundtrip")
    config.preprocess.target_fps = 15
    config.segmentation.text_prompt = "test prompt"
    save_path = tmp_path / "config.yaml"
    config.save(save_path)
    loaded = PipelineConfig.load(save_path)
    assert loaded.run_id == "roundtrip"
    assert loaded.preprocess.target_fps == 15
    assert loaded.segmentation.text_prompt == "test prompt"
