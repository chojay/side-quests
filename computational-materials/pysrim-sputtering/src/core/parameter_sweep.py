"""
Parameter sweep orchestration for systematic SRIM/TRIM studies.

Runs simulations across ranges of energy, ion species, pressure,
bias voltage, and interlayer thickness.
"""
import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from .simulation_runner import SRIMSimulation, SimulationResult
from .ion_energy_estimator import IonEnergyEstimator
from ..analysis.output_parser import SRIMOutputParser
from ..analysis.metrics import (
    RangeMetrics, DamageMetrics, SputterMetrics, EnergyPartitioning,
    compute_range_metrics, compute_damage_metrics, compute_energy_partitioning,
)
from ..analysis.sputtering import calculate_sputter_yield
from ..utils.config_loader import load_simulation_config, PROJECT_ROOT

logger = logging.getLogger(__name__)


class ParameterSweep:
    """
    Run SRIM simulations across parameter ranges.

    Parameters
    ----------
    sim : SRIMSimulation, optional
        Simulation runner. Creates default if None.
    """

    def __init__(self, sim: Optional[SRIMSimulation] = None):
        self.sim = sim or SRIMSimulation()
        self._results_dir = str(PROJECT_ROOT / "output" / "data")

    def energy_sweep(
        self,
        ion_symbol: str = "N",
        target_name: str = "SiO2",
        energies_eV: Optional[List[float]] = None,
        number_ions: int = 5000,
        calculation: int = 2,
    ) -> pd.DataFrame:
        """
        Sweep ion energy and collect range/damage metrics.

        Parameters
        ----------
        ion_symbol : str
            Ion species.
        target_name : str
            Target material name from materials.yaml.
        energies_eV : list of float, optional
            Energies to simulate. Default: 20 log-spaced points 10-1000 eV.
        number_ions : int
            Ions per simulation.
        calculation : int
            TRIM calculation type.

        Returns
        -------
        pd.DataFrame
            One row per energy with columns: energy_eV, Rp_nm, delta_Rp_nm,
            max_depth_nm, peak_vac_density, total_vac, sputter_yield, etc.
        """
        if energies_eV is None:
            energies_eV = np.logspace(np.log10(10), np.log10(1000), 20).tolist()

        results = []
        for energy in tqdm(energies_eV, desc=f"{ion_symbol} → {target_name}"):
            try:
                if target_name == "SiO2":
                    sim_result = self.sim.run_scenario_a(
                        energy, ion_symbol, number_ions, calculation
                    )
                elif target_name == "ITO":
                    sim_result = self.sim.run_scenario_b(
                        energy, ion_symbol, number_ions, calculation
                    )
                else:
                    from ..materials.definitions import make_target
                    target = make_target(target_name)
                    sim_result = self.sim.run_single(
                        ion_symbol, energy, target, target_name,
                        number_ions, calculation
                    )

                row = self._extract_metrics(sim_result, energy)
                results.append(row)
            except Exception as e:
                logger.error(f"Failed at {energy:.1f} eV: {e}")
                results.append({'energy_eV': energy, 'error': str(e)})

        df = pd.DataFrame(results)
        self._save_sweep_csv(df, f"energy_sweep_{ion_symbol}_{target_name}.csv")
        return df

    def species_sweep(
        self,
        species: Optional[List[str]] = None,
        energy_eV: float = 100,
        target_name: str = "ITO",
        number_ions: int = 5000,
    ) -> Dict[str, pd.DataFrame]:
        """
        Compare different ion species at the same energy.

        Returns
        -------
        dict
            {ion_symbol: range_DataFrame}
        """
        if species is None:
            species = ["N", "Ar", "O", "B"]

        range_data = {}
        for ion_sym in tqdm(species, desc=f"Species comparison at {energy_eV} eV"):
            try:
                sim_result = self.sim.run_scenario_b(
                    energy_eV, ion_sym, number_ions
                )
                parser = SRIMOutputParser(sim_result.output_dir)
                rdf = parser.parse_range()
                if rdf is not None:
                    range_data[ion_sym] = rdf
            except Exception as e:
                logger.error(f"Failed for {ion_sym}: {e}")

        return range_data

    def pressure_sweep(
        self,
        pressures_mtorr: Optional[List[float]] = None,
        ion_symbol: str = "N",
        target_name: str = "ITO",
        number_ions: int = 5000,
    ) -> pd.DataFrame:
        """
        Map pressure → estimated energy → SRIM result.

        Returns
        -------
        pd.DataFrame
            Columns: pressure_mtorr, estimated_energy_eV, Rp_nm, etc.
        """
        if pressures_mtorr is None:
            pressures_mtorr = [8, 12, 30]

        estimator = IonEnergyEstimator()
        results = []

        for pressure in tqdm(pressures_mtorr, desc="Pressure sweep"):
            est = estimator.estimate_substrate_ion_energy(pressure)
            energy = est.energy_eV

            try:
                sim_result = self.sim.run_scenario_b(
                    energy, ion_symbol, number_ions
                )
                row = self._extract_metrics(sim_result, energy)
                row['pressure_mtorr'] = pressure
                row['energy_range_low'] = est.energy_range_eV[0]
                row['energy_range_high'] = est.energy_range_eV[1]
                row['confidence'] = est.confidence
                results.append(row)
            except Exception as e:
                logger.error(f"Failed at {pressure} mTorr: {e}")

        df = pd.DataFrame(results)
        self._save_sweep_csv(df, f"pressure_sweep_{ion_symbol}_{target_name}.csv")
        return df

    def bias_sweep(
        self,
        bias_voltages_V: Optional[List[float]] = None,
        pressure_mtorr: float = 12.0,
        ion_symbol: str = "N",
        number_ions: int = 5000,
    ) -> pd.DataFrame:
        """
        Sweep substrate bias voltage.

        Returns
        -------
        pd.DataFrame
        """
        if bias_voltages_V is None:
            bias_voltages_V = [-20, -5, 0, 5, 20]

        estimator = IonEnergyEstimator()
        results = []

        for bias in tqdm(bias_voltages_V, desc="Bias sweep"):
            est = estimator.estimate_substrate_ion_energy(pressure_mtorr, bias_V=bias)
            energy = est.energy_eV

            try:
                sim_result = self.sim.run_scenario_b(
                    energy, ion_symbol, number_ions
                )
                row = self._extract_metrics(sim_result, energy)
                row['bias_V'] = bias
                row['pressure_mtorr'] = pressure_mtorr
                results.append(row)
            except Exception as e:
                logger.error(f"Failed at bias={bias}V: {e}")

        df = pd.DataFrame(results)
        self._save_sweep_csv(df, f"bias_sweep_{ion_symbol}.csv")
        return df

    def multilayer_sweep(
        self,
        tio2_thicknesses_nm: Optional[List[float]] = None,
        ion_energy_eV: float = 100,
        ion_symbol: str = "N",
        number_ions: int = 5000,
    ) -> Tuple[pd.DataFrame, Dict[float, pd.DataFrame]]:
        """
        Sweep TiO2 optical-coating thickness.

        Returns
        -------
        (summary_df, range_data_dict)
        """
        if tio2_thicknesses_nm is None:
            tio2_thicknesses_nm = [0, 1, 2, 5, 10]

        results = []
        range_data = {}

        for thickness in tqdm(tio2_thicknesses_nm, desc="Multilayer sweep"):
            try:
                if thickness == 0:
                    sim_result = self.sim.run_scenario_b(
                        ion_energy_eV, ion_symbol, number_ions
                    )
                else:
                    sim_result = self.sim.run_multilayer(
                        ion_energy_eV, ion_symbol, thickness, number_ions
                    )

                row = self._extract_metrics(sim_result, ion_energy_eV)
                row['tio2_thickness_nm'] = thickness
                results.append(row)

                parser = SRIMOutputParser(sim_result.output_dir)
                rdf = parser.parse_range()
                if rdf is not None:
                    range_data[thickness] = rdf
            except Exception as e:
                logger.error(f"Failed at TiO2={thickness}nm: {e}")

        df = pd.DataFrame(results)
        self._save_sweep_csv(df, f"multilayer_sweep_{ion_symbol}.csv")
        return df, range_data

    def _extract_metrics(self, sim_result: SimulationResult,
                         energy_eV: float) -> dict:
        """Extract all metrics from a simulation result."""
        row = {'energy_eV': energy_eV, 'output_dir': sim_result.output_dir}

        parser = SRIMOutputParser(sim_result.output_dir)
        outputs = parser.parse_all()

        if outputs['range'] is not None:
            rm = compute_range_metrics(outputs['range'])
            row.update({
                'Rp_nm': rm.Rp_nm,
                'delta_Rp_nm': rm.delta_Rp_nm,
                'max_depth_nm': rm.max_depth_angstrom / 10,
                'peak_depth_nm': rm.peak_depth_angstrom / 10,
            })

        if outputs['vacancy'] is not None:
            dm = compute_damage_metrics(outputs['vacancy'])
            row.update({
                'peak_vac_density': dm.peak_vacancy_density,
                'peak_vac_depth_nm': dm.peak_depth_angstrom / 10,
                'total_vac_per_ion': dm.total_vacancies_per_ion,
                'damage_extent_nm': dm.damage_extends_to_angstrom / 10,
            })

        if outputs['ionization'] is not None or outputs['phonon'] is not None:
            ep = compute_energy_partitioning(
                outputs['ionization'], outputs['phonon'], energy_eV
            )
            row.update({
                'electronic_fraction': ep.electronic_fraction,
                'nuclear_fraction': ep.nuclear_fraction,
                'phonon_fraction': ep.phonon_fraction,
            })

        sputter_yield = calculate_sputter_yield(sim_result.output_dir)
        if sputter_yield is not None:
            row['sputter_yield'] = sputter_yield

        return row

    def _save_sweep_csv(self, df: pd.DataFrame, filename: str):
        """Save sweep results to CSV."""
        os.makedirs(self._results_dir, exist_ok=True)
        path = os.path.join(self._results_dir, filename)
        df.to_csv(path, index=False)
        logger.info(f"Saved sweep results to {path}")
