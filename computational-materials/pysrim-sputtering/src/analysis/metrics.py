"""
Metrics computed from SRIM/TRIM simulation output.

Dataclasses for projected range, damage, sputtering yield,
and energy partitioning metrics.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd


@dataclass
class RangeMetrics:
    """Projected range statistics for a single simulation."""
    Rp_angstrom: float          # Mean projected range
    Rp_nm: float                # Rp in nm
    delta_Rp_angstrom: float    # Range straggling (std dev)
    delta_Rp_nm: float
    max_depth_angstrom: float   # Maximum penetration depth
    median_depth_angstrom: float
    peak_depth_angstrom: float  # Depth of peak ion concentration

    def __repr__(self):
        return (
            f"RangeMetrics(Rp={self.Rp_nm:.2f} nm ± {self.delta_Rp_nm:.2f} nm, "
            f"max={self.max_depth_angstrom/10:.1f} nm)"
        )


@dataclass
class DamageMetrics:
    """Damage profile metrics."""
    peak_vacancy_density: float     # vacancies/A/ion at peak
    peak_depth_angstrom: float      # depth of peak damage
    total_vacancies_per_ion: float  # integrated vacancies
    damage_extends_to_angstrom: float  # depth where damage drops to 1% of peak

    def __repr__(self):
        return (
            f"DamageMetrics(peak={self.peak_vacancy_density:.4f} vac/A/ion "
            f"at {self.peak_depth_angstrom/10:.1f} nm, "
            f"extends to {self.damage_extends_to_angstrom/10:.1f} nm)"
        )


@dataclass
class SputterMetrics:
    """Sputtering yield metrics."""
    total_yield: float                    # atoms sputtered per incident ion
    yield_by_element: Dict[str, float] = field(default_factory=dict)

    def __repr__(self):
        return f"SputterMetrics(Y={self.total_yield:.3f} atoms/ion)"


@dataclass
class EnergyPartitioning:
    """Energy partitioning between electronic and nuclear stopping."""
    electronic_fraction: float
    nuclear_fraction: float
    phonon_fraction: float
    total_energy_eV: float

    def __repr__(self):
        return (
            f"EnergyPartitioning(electronic={self.electronic_fraction:.1%}, "
            f"nuclear={self.nuclear_fraction:.1%}, "
            f"phonon={self.phonon_fraction:.1%})"
        )


def compute_range_metrics(range_df: pd.DataFrame) -> RangeMetrics:
    """
    Compute projected range metrics from parsed range data.

    Parameters
    ----------
    range_df : pd.DataFrame
        From SRIMOutputParser.parse_range(). Needs columns:
        depth_A, ions_per_A_per_ion.

    Returns
    -------
    RangeMetrics
    """
    depth = range_df['depth_A'].values
    dist = range_df['ions_per_A_per_ion'].values

    # Normalize distribution
    total = np.trapz(dist, depth)
    if total > 0:
        dist_norm = dist / total
    else:
        dist_norm = dist

    # Mean (projected range)
    Rp = np.trapz(depth * dist_norm, depth)

    # Variance → straggling
    variance = np.trapz((depth - Rp) ** 2 * dist_norm, depth)
    delta_Rp = np.sqrt(max(variance, 0))

    # Peak
    peak_idx = np.argmax(dist)
    peak_depth = depth[peak_idx]

    # Max depth (where distribution drops below 1% of peak)
    threshold = 0.01 * dist.max()
    above = np.where(dist > threshold)[0]
    max_depth = depth[above[-1]] if len(above) > 0 else depth[-1]

    # Median
    cumulative = np.cumsum(dist_norm * np.gradient(depth))
    cumulative /= cumulative[-1] if cumulative[-1] > 0 else 1
    median_idx = np.searchsorted(cumulative, 0.5)
    median_depth = depth[min(median_idx, len(depth) - 1)]

    return RangeMetrics(
        Rp_angstrom=Rp,
        Rp_nm=Rp / 10.0,
        delta_Rp_angstrom=delta_Rp,
        delta_Rp_nm=delta_Rp / 10.0,
        max_depth_angstrom=max_depth,
        median_depth_angstrom=median_depth,
        peak_depth_angstrom=peak_depth,
    )


def compute_damage_metrics(vacancy_df: pd.DataFrame) -> DamageMetrics:
    """
    Compute damage metrics from parsed vacancy data.

    Parameters
    ----------
    vacancy_df : pd.DataFrame
        From SRIMOutputParser.parse_vacancies().

    Returns
    -------
    DamageMetrics
    """
    depth = vacancy_df['depth_A'].values

    # Sum all vacancy columns (element-specific + total)
    vac_cols = [c for c in vacancy_df.columns
                if c not in ('depth_A', 'depth_nm') and 'vacancy' in c.lower()]
    if not vac_cols:
        # Use all numeric columns except depth
        vac_cols = [c for c in vacancy_df.columns
                    if c not in ('depth_A', 'depth_nm')]

    if not vac_cols:
        return DamageMetrics(0, 0, 0, 0)

    # Use first vacancy column as total
    vac = vacancy_df[vac_cols[0]].values

    peak_idx = np.argmax(vac)
    peak_val = vac[peak_idx]
    peak_depth = depth[peak_idx]

    total = np.trapz(vac, depth)

    # Damage extent: where it drops to 1% of peak
    threshold = 0.01 * peak_val if peak_val > 0 else 0
    above = np.where(vac > threshold)[0]
    extends_to = depth[above[-1]] if len(above) > 0 else 0

    return DamageMetrics(
        peak_vacancy_density=peak_val,
        peak_depth_angstrom=peak_depth,
        total_vacancies_per_ion=total,
        damage_extends_to_angstrom=extends_to,
    )


def compute_energy_partitioning(
    ionization_df: Optional[pd.DataFrame],
    phonon_df: Optional[pd.DataFrame],
    ion_energy_eV: float,
) -> EnergyPartitioning:
    """
    Compute energy partitioning from ionization and phonon data.

    Parameters
    ----------
    ionization_df : pd.DataFrame or None
        From SRIMOutputParser.parse_ionization().
    phonon_df : pd.DataFrame or None
        From SRIMOutputParser.parse_phonons().
    ion_energy_eV : float
        Initial ion energy.

    Returns
    -------
    EnergyPartitioning
    """
    electronic = 0.0
    nuclear = 0.0
    phonon = 0.0

    if ionization_df is not None and 'depth_A' in ionization_df.columns:
        depth = ionization_df['depth_A'].values
        if 'ions_ionization' in ionization_df.columns:
            electronic = np.trapz(
                ionization_df['ions_ionization'].values, depth
            )
        if 'recoils_ionization' in ionization_df.columns:
            nuclear = np.trapz(
                ionization_df['recoils_ionization'].values, depth
            )

    if phonon_df is not None and 'depth_A' in phonon_df.columns:
        depth = phonon_df['depth_A'].values
        phon_cols = [c for c in phonon_df.columns
                     if c not in ('depth_A', 'depth_nm')]
        if phon_cols:
            phonon = np.trapz(phonon_df[phon_cols[0]].values, depth)

    total = electronic + nuclear + phonon
    if total == 0:
        total = ion_energy_eV  # fallback

    return EnergyPartitioning(
        electronic_fraction=electronic / total if total > 0 else 0,
        nuclear_fraction=nuclear / total if total > 0 else 0,
        phonon_fraction=phonon / total if total > 0 else 0,
        total_energy_eV=ion_energy_eV,
    )
