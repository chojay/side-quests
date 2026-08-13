"""
Shared pytest fixtures for pySRIM tests.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Apply patches BEFORE any srim import
from src.utils.pysrim_patches import apply_patches
apply_patches()  # Must happen before `import srim` anywhere


@pytest.fixture
def materials_config_path():
    """Path to the materials.yaml config file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "materials.yaml"
    )


@pytest.fixture
def experimental_config_path():
    """Path to experimental_conditions.yaml."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "experimental_conditions.yaml"
    )


@pytest.fixture
def sample_range_df():
    """Synthetic range distribution data mimicking SRIM output."""
    np.random.seed(42)
    depths = np.linspace(0, 100, 200)  # 0 to 100 Angstroms
    # Gaussian-like distribution peaked at 30 A with sigma 10 A
    dist = np.exp(-0.5 * ((depths - 30) / 10) ** 2)
    dist /= np.trapz(dist, depths)  # Normalize

    return pd.DataFrame({
        'depth_A': depths,
        'ions_per_A_per_ion': dist,
        'depth_nm': depths / 10.0,
    })


@pytest.fixture
def sample_vacancy_df():
    """Synthetic vacancy profile data."""
    depths = np.linspace(0, 100, 200)
    # Broader distribution than range, peaked at 25 A
    vac = 0.005 * np.exp(-0.5 * ((depths - 25) / 15) ** 2)

    return pd.DataFrame({
        'depth_A': depths,
        'target_vacancies': vac,
        'depth_nm': depths / 10.0,
    })


@pytest.fixture
def sample_ionization_df():
    """Synthetic ionization energy loss data."""
    depths = np.linspace(0, 100, 200)
    ions_ioniz = 0.1 * np.exp(-depths / 40)  # Exponential decay
    recoils_ioniz = 0.02 * np.exp(-0.5 * ((depths - 20) / 12) ** 2)

    return pd.DataFrame({
        'depth_A': depths,
        'ions_ionization': ions_ioniz,
        'recoils_ionization': recoils_ioniz,
        'depth_nm': depths / 10.0,
    })


@pytest.fixture
def sample_phonon_df():
    """Synthetic phonon data."""
    depths = np.linspace(0, 100, 200)
    phonons = 0.01 * np.exp(-0.5 * ((depths - 20) / 15) ** 2)

    return pd.DataFrame({
        'depth_A': depths,
        'phonons': phonons,
        'depth_nm': depths / 10.0,
    })


@pytest.fixture
def mock_srim_output(tmp_path):
    """Create mock SRIM output directory with fake data files."""
    output_dir = tmp_path / "SRIM Outputs"
    output_dir.mkdir()

    # Write a minimal RANGE.txt
    range_file = output_dir / "RANGE.txt"
    lines = [
        "  SRIM Output File",
        "  Ion = N, Energy = 100 eV",
        "  ---",
    ]
    for d in range(0, 100, 5):
        val = 0.01 * np.exp(-0.5 * ((d - 30) / 10) ** 2)
        lines.append(f"  {d:.1f}  {val:.6f}")
    range_file.write_text("\n".join(lines))

    return str(tmp_path)
