"""
Factory functions for creating pysrim Layer objects from YAML config.

Each function creates a properly configured Layer for SRIM/TRIM simulation
with validated material parameters from the config/materials.yaml database.

Domain: optical thin films - low-index SiO2, high-index TiO2, and the
ITO transparent conductor they are deposited on.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from srim import Layer, Target

from ..utils.config_loader import load_materials, MaterialConfig


def _material_to_layer(mat: MaterialConfig, width_override: Optional[int] = None):
    """Convert a MaterialConfig to a pysrim Layer."""
    from srim import Layer
    elements = {}
    for symbol, elem in mat.elements.items():
        elements[symbol] = {
            'stoich': elem.stoich,
            'E_d': elem.E_d,
            'lattice': elem.lattice,
            'surface': elem.surface,
        }
    width = width_override if width_override is not None else mat.width_angstrom
    return Layer(elements, density=mat.density, width=width)


def make_sio2_layer(width_angstrom: Optional[int] = None,
                    config_path: Optional[str] = None) -> Layer:
    """
    Create SiO2 low-index optical coating layer.

    Parameters
    ----------
    width_angstrom : int, optional
        Override default width (50000 A = 5 um).
    config_path : str, optional
        Path to materials.yaml. Uses default if None.

    Returns
    -------
    srim.Layer
    """
    materials = load_materials(config_path)
    return _material_to_layer(materials['SiO2'], width_angstrom)


def make_tio2_layer(width_angstrom: Optional[int] = None,
                    density: Optional[float] = None,
                    config_path: Optional[str] = None) -> Layer:
    """
    Create TiO2 high-index optical coating layer.

    Parameters
    ----------
    width_angstrom : int, optional
        Override default width (600 A ~ 60 nm quarter-wave).
    density : float, optional
        Override default density (4.23 g/cm3, rutile). Range: 3.9-4.23
        for anatase-to-rutile films.
    config_path : str, optional
        Path to materials.yaml.

    Returns
    -------
    srim.Layer
    """
    materials = load_materials(config_path)
    mat = materials['TiO2']
    if density is not None:
        mat = mat.copy(update={'density': density})
    return _material_to_layer(mat, width_angstrom)


def make_ito_layer(width_angstrom: Optional[int] = None,
                   config_path: Optional[str] = None) -> Layer:
    """
    Create ITO (indium tin oxide) transparent-conductor layer.

    Parameters
    ----------
    width_angstrom : int, optional
        Override default width (1500 A = 150 nm electrode).
    config_path : str, optional
        Path to materials.yaml.

    Returns
    -------
    srim.Layer
    """
    materials = load_materials(config_path)
    return _material_to_layer(materials['ITO'], width_angstrom)


def make_multilayer_target(tio2_width_angstrom: int = 600,
                           ito_width_angstrom: int = 1500,
                           config_path: Optional[str] = None) -> Target:
    """
    Create a TiO2 / ITO bilayer: an optical coating on a transparent conductor.

    The target is ordered top-to-bottom: TiO2 (surface coating) -> ITO (bulk
    electrode). The ion enters through the TiO2 optical coating first, so this
    target studies how far ions penetrate the coating and into the conductor.

    Parameters
    ----------
    tio2_width_angstrom : int
        TiO2 optical-coating thickness in Angstroms. Default 600 (~60 nm).
    ito_width_angstrom : int
        ITO conductor thickness in Angstroms. Default 1500 (150 nm).
    config_path : str, optional
        Path to materials.yaml.

    Returns
    -------
    srim.Target
    """
    from srim import Target
    tio2 = make_tio2_layer(tio2_width_angstrom, config_path=config_path)
    ito = make_ito_layer(ito_width_angstrom, config_path)
    return Target([tio2, ito])


def make_target(material_name: str, width_angstrom: Optional[int] = None,
                config_path: Optional[str] = None) -> Target:
    """
    Create a single-layer Target from material name.

    Parameters
    ----------
    material_name : str
        Key in materials.yaml (e.g., "SiO2", "TiO2", "ITO").
    width_angstrom : int, optional
        Override default width.
    config_path : str, optional
        Path to materials.yaml.

    Returns
    -------
    srim.Target
    """
    from srim import Target
    materials = load_materials(config_path)
    if material_name not in materials:
        raise ValueError(
            f"Unknown material '{material_name}'. "
            f"Available: {list(materials.keys())}"
        )
    layer = _material_to_layer(materials[material_name], width_angstrom)
    return Target([layer])
