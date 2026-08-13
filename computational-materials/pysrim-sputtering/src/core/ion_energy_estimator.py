"""
Estimate ion energy from RF sputtering process conditions.

Maps experimental parameters (RF power, pressure, bias) to approximate
ion energies for SRIM input. Based on literature heuristics for RF
magnetron sputtering plasma physics.

Physics Background
------------------
In RF magnetron sputtering, ions are accelerated across the plasma sheath:
    E_ion ≈ V_plasma + V_sheath(pressure, power) + |V_bias|

- V_plasma: floating potential of RF plasma (~15-25 V)
- V_sheath: voltage drop across sheath, depends on pressure
  (mean free path vs sheath thickness) and power
- V_bias: externally applied substrate bias

At low pressure (8 mTorr), the ion mean free path is long compared to the
sheath thickness, so ions traverse with few collisions → high energy.
At high pressure (30 mTorr), ions undergo many collisions → thermalized.

For target bombardment (Scenario A), the relevant energy is set by the
target self-bias: V_dc ≈ k * sqrt(P_rf).

References
----------
- Chapman, B. "Glow Discharge Processes" (1980) Ch. 4-5
- Lieberman & Lichtenberg, "Principles of Plasma Discharges" (2005)
- Standard RF magnetron sheath models (literature heuristics)
"""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.config_loader import load_experimental_conditions


@dataclass
class IonEnergyEstimate:
    """Result of ion energy estimation."""
    energy_eV: float
    energy_range_eV: Tuple[float, float]
    components: Dict[str, float]
    confidence: str  # "low", "medium", "high"
    notes: str = ""

    def __repr__(self):
        return (
            f"IonEnergyEstimate(E={self.energy_eV:.1f} eV "
            f"[{self.energy_range_eV[0]:.0f}-{self.energy_range_eV[1]:.0f}], "
            f"confidence={self.confidence})"
        )


class IonEnergyEstimator:
    """
    Estimate ion energies from RF sputtering process parameters.

    Parameters
    ----------
    config_path : str, optional
        Path to experimental_conditions.yaml.
    """

    def __init__(self, config_path: Optional[str] = None):
        config = load_experimental_conditions(config_path)
        self._model = config.get('ion_energy_model', {})
        self._system = config.get('sputter_system', {})

    def estimate_substrate_ion_energy(
        self,
        pressure_mtorr: float,
        bias_V: float = 0.0,
        icp_power_kw: float = 0.0,
    ) -> IonEnergyEstimate:
        """
        Estimate ion energy at the substrate (Scenario B: film bombardment).

        Parameters
        ----------
        pressure_mtorr : float
            Chamber pressure in mTorr.
        bias_V : float
            Substrate bias voltage (negative = attract ions).
        icp_power_kw : float
            ICP power in kW (0 = no ICP assist).

        Returns
        -------
        IonEnergyEstimate
        """
        V_plasma = self._model.get('plasma_potential_V', 20.0)
        V_plasma_range = self._model.get('plasma_potential_range_V', [15, 25])

        # Interpolate sheath voltage from pressure
        V_sheath, V_sheath_range = self._interpolate_sheath(pressure_mtorr)

        # Bias contribution (negative bias accelerates positive ions)
        V_bias = abs(bias_V) if bias_V < 0 else 0.0

        # ICP boost
        icp_boost = 0.0
        icp_boost_range = [0.0, 0.0]
        if icp_power_kw > 0:
            icp_map = self._model.get('icp_energy_boost_eV', {})
            # YAML may load keys as float or str; try both
            for key in [icp_power_kw, str(icp_power_kw), int(icp_power_kw)]:
                if key in icp_map:
                    icp_boost_range = icp_map[key]
                    icp_boost = sum(icp_boost_range) / 2
                    break

        energy = V_plasma + V_sheath + V_bias + icp_boost
        energy_low = V_plasma_range[0] + V_sheath_range[0] + V_bias + icp_boost_range[0]
        energy_high = V_plasma_range[1] + V_sheath_range[1] + V_bias + icp_boost_range[1]

        components = {
            'V_plasma': V_plasma,
            'V_sheath': V_sheath,
            'V_bias': V_bias,
            'ICP_boost': icp_boost,
        }

        confidence = "medium"
        notes_parts = [f"Pressure: {pressure_mtorr} mTorr"]
        if bias_V != 0:
            notes_parts.append(f"Bias: {bias_V} V")
        if icp_power_kw > 0:
            notes_parts.append(f"ICP: {icp_power_kw} kW")
        if pressure_mtorr < 5 or pressure_mtorr > 50:
            confidence = "low"
            notes_parts.append("Outside calibrated pressure range")

        return IonEnergyEstimate(
            energy_eV=energy,
            energy_range_eV=(energy_low, energy_high),
            components=components,
            confidence=confidence,
            notes="; ".join(notes_parts),
        )

    def estimate_target_ion_energy(
        self,
        rf_power_kw: float = 3.5,
        pressure_mtorr: float = 12.0,
    ) -> IonEnergyEstimate:
        """
        Estimate ion energy at the sputter target (Scenario A).

        For the target, the ion energy is dominated by the DC self-bias
        which scales approximately as V_dc ≈ k * sqrt(P_rf).

        Parameters
        ----------
        rf_power_kw : float
            RF power in kW.
        pressure_mtorr : float
            Chamber pressure in mTorr.

        Returns
        -------
        IonEnergyEstimate
        """
        bias_config = self._model.get('target_self_bias', {})
        k = bias_config.get('coefficient', 50)
        typical_range = bias_config.get('typical_range_V', [100, 400])

        V_dc = k * math.sqrt(rf_power_kw)

        # Pressure reduces effective energy via collisions
        pressure_factor = 1.0
        if pressure_mtorr > 15:
            pressure_factor = 0.7  # significant thermalization
        elif pressure_mtorr > 10:
            pressure_factor = 0.85

        energy = V_dc * pressure_factor
        energy_low = typical_range[0] * pressure_factor
        energy_high = typical_range[1] * pressure_factor

        components = {
            'V_dc_self_bias': V_dc,
            'pressure_factor': pressure_factor,
        }

        return IonEnergyEstimate(
            energy_eV=energy,
            energy_range_eV=(energy_low, energy_high),
            components=components,
            confidence="medium",
            notes=f"RF: {rf_power_kw} kW, P: {pressure_mtorr} mTorr, "
                  f"V_dc ≈ {k}*sqrt(P_rf) = {V_dc:.0f} V",
        )

    def _interpolate_sheath(
        self, pressure_mtorr: float
    ) -> Tuple[float, Tuple[float, float]]:
        """Interpolate sheath voltage from pressure using config data."""
        models = self._model.get('sheath_models', [])
        if not models:
            return 50.0, (20.0, 100.0)

        pressures = [m['pressure_mtorr'] for m in models]
        v_lows = [m['sheath_voltage_V'][0] for m in models]
        v_highs = [m['sheath_voltage_V'][1] for m in models]

        # Linear interpolation (or extrapolation with clamp)
        v_low = float(np.interp(pressure_mtorr, pressures, v_lows))
        v_high = float(np.interp(pressure_mtorr, pressures, v_highs))
        v_mid = (v_low + v_high) / 2

        return v_mid, (v_low, v_high)

    def generate_energy_range(
        self,
        pressures_mtorr: Optional[List[float]] = None,
        bias_voltages_V: Optional[List[float]] = None,
    ) -> List[IonEnergyEstimate]:
        """
        Generate energy estimates for all combinations of conditions.

        Parameters
        ----------
        pressures_mtorr : list of float, optional
            Pressures to evaluate. Uses config defaults if None.
        bias_voltages_V : list of float, optional
            Bias voltages. Uses config defaults if None.

        Returns
        -------
        list of IonEnergyEstimate
        """
        if pressures_mtorr is None:
            pressures_mtorr = self._system.get('pressures_mtorr', [8, 12, 30])
        if bias_voltages_V is None:
            bias_voltages_V = [0.0]

        estimates = []
        for p in pressures_mtorr:
            for v in bias_voltages_V:
                estimates.append(
                    self.estimate_substrate_ion_energy(p, bias_V=v)
                )
        return estimates
