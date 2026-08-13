"""
YAML-backed material property database.

Provides centralized access to material definitions with validation
and convenience methods for common queries.
"""
from typing import Dict, List, Optional

from ..utils.config_loader import load_materials, MaterialConfig


class MaterialDatabase:
    """
    Material property database loaded from YAML config.

    Example
    -------
    >>> db = MaterialDatabase()
    >>> db.list_materials()
    ['SiO2', 'TiO2', 'ITO']
    >>> db.get_density('TiO2')
    4.23
    >>> layer = db.get_layer('SiO2', width_override=100000)
    """

    def __init__(self, config_path: Optional[str] = None):
        self._materials = load_materials(config_path)

    def list_materials(self) -> List[str]:
        """Return available material names."""
        return list(self._materials.keys())

    def get_material(self, name: str) -> MaterialConfig:
        """Get validated material configuration."""
        if name not in self._materials:
            raise KeyError(
                f"Material '{name}' not found. "
                f"Available: {self.list_materials()}"
            )
        return self._materials[name]

    def get_density(self, name: str) -> float:
        """Get material density in g/cm3."""
        return self.get_material(name).density

    def get_elements(self, name: str) -> Dict[str, dict]:
        """Get element definitions for a material."""
        mat = self.get_material(name)
        return {
            sym: {
                'stoich': elem.stoich,
                'E_d': elem.E_d,
                'lattice': elem.lattice,
                'surface': elem.surface,
            }
            for sym, elem in mat.elements.items()
        }

    def get_layer(self, name: str, width_override: Optional[int] = None):
        """
        Create a pysrim Layer from material name.

        Parameters
        ----------
        name : str
            Material key (e.g., "SiO2", "TiO2", "ITO").
        width_override : int, optional
            Override default layer width in Angstroms.

        Returns
        -------
        srim.Layer
        """
        from srim import Layer
        mat = self.get_material(name)
        elements = self.get_elements(name)
        width = width_override if width_override is not None else mat.width_angstrom
        return Layer(elements, density=mat.density, width=width)

    def get_composition_string(self, name: str) -> str:
        """Get human-readable composition string (e.g., 'In1.8Sn0.2O3.0')."""
        mat = self.get_material(name)
        parts = []
        for sym, elem in mat.elements.items():
            if elem.stoich == 1.0:
                parts.append(sym)
            else:
                parts.append(f"{sym}{elem.stoich}")
        return "".join(parts)

    def summary(self) -> str:
        """Print summary of all materials."""
        lines = []
        for name, mat in self._materials.items():
            comp = self.get_composition_string(name)
            lines.append(
                f"  {name}: {comp}, ρ={mat.density} g/cm³, "
                f"width={mat.width_angstrom} Å ({mat.width_angstrom/10:.0f} nm)"
            )
        return "Materials Database:\n" + "\n".join(lines)
