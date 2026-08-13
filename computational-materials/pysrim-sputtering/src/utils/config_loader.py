"""
YAML configuration loading with Pydantic validation.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml
from pydantic import BaseModel, validator

# Project root  -  two levels up from this file (src/utils/ → project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


class ElementConfig(BaseModel):
    stoich: float
    E_d: float = 25.0
    lattice: float = 3.0
    surface: float = 3.0

    @validator('stoich')
    def stoich_positive(cls, v):
        if v <= 0:
            raise ValueError(f"Stoichiometry must be positive, got {v}")
        return v

    @validator('E_d', 'lattice', 'surface')
    def energies_positive(cls, v):
        if v < 0:
            raise ValueError(f"Energies must be non-negative, got {v}")
        return v


class MaterialConfig(BaseModel):
    name: str
    density: float
    density_range: Optional[List[float]] = None
    elements: Dict[str, ElementConfig]
    width_angstrom: int = 50000

    @validator('density')
    def density_physical(cls, v):
        if not (0.1 < v < 25.0):
            raise ValueError(f"Density {v} g/cm3 outside physical range")
        return v


class SheathModel(BaseModel):
    pressure_mtorr: float
    label: str = ""
    sheath_voltage_V: List[float]
    notes: str = ""


class IonEnergyModelConfig(BaseModel):
    plasma_potential_V: float = 20.0
    plasma_potential_range_V: List[float] = [15.0, 25.0]
    sheath_models: List[SheathModel] = []
    icp_energy_boost_eV: Dict[str, List[float]] = {}
    target_self_bias: Dict[str, Any] = {}


class SimulationConfig(BaseModel):
    number_ions: int = 5000
    calculation_type: int = 1
    srim_directory: Optional[str] = None
    use_docker: bool = True
    docker_image: str = "pysrim"

    @validator('calculation_type')
    def valid_calc_type(cls, v):
        if v not in (1, 2, 3, 4, 5, 6, 7):
            raise ValueError(f"Invalid calculation type {v}. Must be 1-7.")
        return v

    @validator('number_ions')
    def ions_positive(cls, v):
        if v < 1:
            raise ValueError("number_ions must be >= 1")
        return v


class SweepConfig(BaseModel):
    min_eV: float = 10
    max_eV: float = 1000
    n_points: int = 20
    log_scale: bool = True


def load_yaml(path: str) -> dict:
    """Load a YAML file and return as dict."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_materials(path: Optional[str] = None) -> Dict[str, MaterialConfig]:
    """Load and validate all material definitions."""
    if path is None:
        path = str(CONFIG_DIR / "materials.yaml")
    raw = load_yaml(path)
    materials = {}
    for name, data in raw.items():
        elements = {}
        for sym, params in data['elements'].items():
            elements[sym] = ElementConfig(**params)
        materials[name] = MaterialConfig(
            name=data.get('name', name),
            density=data['density'],
            density_range=data.get('density_range'),
            elements=elements,
            width_angstrom=data.get('width_angstrom', 50000),
        )
    return materials


def load_simulation_config(path: Optional[str] = None) -> SimulationConfig:
    """Load simulation configuration."""
    if path is None:
        path = str(CONFIG_DIR / "default_config.yaml")
    raw = load_yaml(path)
    return SimulationConfig(**raw.get('simulation', {}))


def load_experimental_conditions(path: Optional[str] = None) -> dict:
    """Load experimental conditions as raw dict."""
    if path is None:
        path = str(CONFIG_DIR / "experimental_conditions.yaml")
    return load_yaml(path)


def get_config_path(filename: str) -> str:
    """Get full path to a config file."""
    return str(CONFIG_DIR / filename)
