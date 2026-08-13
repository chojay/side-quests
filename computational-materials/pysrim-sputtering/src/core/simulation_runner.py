"""
SRIM/TRIM simulation runner with Docker support.

Wraps pysrim to execute TRIM simulations either locally (if SRIM.exe
is available via Wine) or via Docker container.
"""
import json
import logging
import os
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from ..materials.definitions import (
    make_sio2_layer, make_tio2_layer, make_ito_layer,
    make_multilayer_target, make_target,
)
from ..utils.config_loader import load_simulation_config, PROJECT_ROOT
from ..utils.docker_helper import DockerSRIMRunner

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Container for SRIM/TRIM simulation results."""
    # Input parameters
    ion_symbol: str
    ion_energy_eV: float
    target_name: str
    number_ions: int
    calculation_type: int

    # Output directory
    output_dir: str = ""

    # Metadata
    timestamp: str = ""
    elapsed_seconds: float = 0.0

    # Parsed data (populated after output parsing)
    range_data: Optional[np.ndarray] = None
    ionization_data: Optional[np.ndarray] = None
    vacancy_data: Optional[np.ndarray] = None
    phonon_data: Optional[np.ndarray] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serialize to dict (without numpy arrays)."""
        return {
            'ion_symbol': self.ion_symbol,
            'ion_energy_eV': self.ion_energy_eV,
            'target_name': self.target_name,
            'number_ions': self.number_ions,
            'calculation_type': self.calculation_type,
            'output_dir': self.output_dir,
            'timestamp': self.timestamp,
            'elapsed_seconds': self.elapsed_seconds,
        }


class SRIMSimulation:
    """
    Wrapper around pysrim TRIM with Docker support.

    Parameters
    ----------
    srim_directory : str, optional
        Path to SRIM.exe (local). If None and use_docker=True, uses Docker.
    use_docker : bool
        Whether to run via Docker container.
    config_path : str, optional
        Path to default_config.yaml.
    """

    def __init__(self, srim_directory: Optional[str] = None,
                 use_docker: bool = True,
                 config_path: Optional[str] = None):
        config = load_simulation_config(config_path)
        self.srim_directory = srim_directory or config.srim_directory
        self.use_docker = use_docker if srim_directory is None else False
        self.default_number_ions = config.number_ions
        self.default_calc_type = config.calculation_type
        self._docker = DockerSRIMRunner(image=config.docker_image) if self.use_docker else None
        self._output_base = str(PROJECT_ROOT / "output" / "data")

    def run_single(
        self,
        ion_symbol: str,
        ion_energy_eV: float,
        target: Target,
        target_name: str = "custom",
        number_ions: Optional[int] = None,
        calculation: Optional[int] = None,
    ) -> SimulationResult:
        """
        Run a single TRIM calculation.

        Parameters
        ----------
        ion_symbol : str
            Element symbol (e.g., "N", "Ar", "O", "B").
        ion_energy_eV : float
            Ion kinetic energy in eV.
        target : srim.Target
            Target configuration.
        target_name : str
            Descriptive name for output labeling.
        number_ions : int, optional
            Override default number of ions.
        calculation : int, optional
            Override default calculation type (1=QKP, 2=FC, 3=Sputter).

        Returns
        -------
        SimulationResult
        """
        from srim import Ion

        n_ions = number_ions or self.default_number_ions
        calc = calculation or self.default_calc_type

        ion = Ion(ion_symbol, energy=ion_energy_eV * 1e3)  # pysrim uses eV

        # Create unique output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"{ion_symbol}_{ion_energy_eV:.0f}eV_{target_name}_{timestamp}"
        output_dir = os.path.join(self._output_base, run_name)
        os.makedirs(output_dir, exist_ok=True)

        result = SimulationResult(
            ion_symbol=ion_symbol,
            ion_energy_eV=ion_energy_eV,
            target_name=target_name,
            number_ions=n_ions,
            calculation_type=calc,
            output_dir=output_dir,
        )

        t0 = time.time()

        if self.use_docker and self._docker:
            success = self._run_docker(
                ion_symbol, ion_energy_eV, target, n_ions, calc, output_dir
            )
        else:
            success = self._run_local(
                ion, target, n_ions, calc, output_dir
            )

        result.elapsed_seconds = time.time() - t0

        if success:
            logger.info(
                f"TRIM completed: {ion_symbol} {ion_energy_eV} eV → {target_name} "
                f"({n_ions} ions, {result.elapsed_seconds:.1f}s)"
            )
        else:
            logger.error(f"TRIM failed for {run_name}")

        # Save metadata
        meta_path = os.path.join(output_dir, "simulation_meta.json")
        with open(meta_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        return result

    def run_scenario_a(
        self,
        ion_energy_eV: float,
        ion_symbol: str = "N",
        number_ions: Optional[int] = None,
        calculation: int = 2,
    ) -> SimulationResult:
        """
        Scenario A: Ion bombardment of SiO2 sputter target.

        Parameters
        ----------
        ion_energy_eV : float
            Ion energy in eV.
        ion_symbol : str
            Ion species (default "N").
        number_ions : int, optional
            Number of ions to simulate.
        calculation : int
            Calculation type. Default 2 (Full Cascade).
            Use 3 for sputtering yield.

        Returns
        -------
        SimulationResult
        """
        target = make_target("SiO2")
        return self.run_single(
            ion_symbol, ion_energy_eV, target,
            target_name="SiO2",
            number_ions=number_ions,
            calculation=calculation,
        )

    def run_scenario_b(
        self,
        ion_energy_eV: float,
        ion_symbol: str = "N",
        number_ions: Optional[int] = None,
        calculation: int = 2,
    ) -> SimulationResult:
        """
        Scenario B: Ion bombardment of a growing ITO transparent conductor.

        Parameters
        ----------
        ion_energy_eV : float
            Ion energy in eV.
        ion_symbol : str
            Ion species (default "N").
        number_ions : int, optional
            Number of ions to simulate.
        calculation : int
            Calculation type. Default 2 (Full Cascade).

        Returns
        -------
        SimulationResult
        """
        target = make_target("ITO")
        return self.run_single(
            ion_symbol, ion_energy_eV, target,
            target_name="ITO",
            number_ions=number_ions,
            calculation=calculation,
        )

    def run_multilayer(
        self,
        ion_energy_eV: float,
        ion_symbol: str = "N",
        tio2_thickness_nm: float = 60.0,
        number_ions: Optional[int] = None,
        calculation: int = 2,
    ) -> SimulationResult:
        """
        Ion penetration through a TiO2 optical coating into the ITO conductor.

        Parameters
        ----------
        ion_energy_eV : float
            Ion energy in eV.
        ion_symbol : str
            Ion species.
        tio2_thickness_nm : float
            TiO2 optical-coating thickness in nm.
        number_ions : int, optional
            Number of ions.
        calculation : int
            Calculation type.

        Returns
        -------
        SimulationResult
        """
        tio2_angstrom = int(tio2_thickness_nm * 10)
        target = make_multilayer_target(tio2_width_angstrom=tio2_angstrom)
        target_name = f"TiO2_{tio2_thickness_nm:.0f}nm_ITO"
        return self.run_single(
            ion_symbol, ion_energy_eV, target,
            target_name=target_name,
            number_ions=number_ions,
            calculation=calculation,
        )

    def _run_local(self, ion, target, n_ions, calc, output_dir) -> bool:
        """Run TRIM locally using pysrim + Wine."""
        from srim import TRIM

        if not self.srim_directory:
            logger.error("No SRIM directory specified for local execution")
            return False
        try:
            trim = TRIM(target, ion, number_ions=n_ions, calculation=calc)
            trim.run(self.srim_directory)
            # Copy SRIM outputs to our output directory
            srim_output = os.path.join(self.srim_directory, "SRIM Outputs")
            if os.path.isdir(srim_output):
                for fname in os.listdir(srim_output):
                    src = os.path.join(srim_output, fname)
                    dst = os.path.join(output_dir, fname)
                    if os.path.isfile(src):
                        import shutil
                        shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"Local TRIM execution failed: {e}")
            return False

    def _run_docker(self, ion_symbol, ion_energy_eV, target,
                    n_ions, calc, output_dir) -> bool:
        """Run TRIM via Docker container."""
        # Generate a self-contained Python script for the container
        layers_spec = self._serialize_target(target)
        script = textwrap.dedent(f"""\
            import os, shutil, sys
            sys.path.insert(0, '/app')

            from srim import Ion, Layer, Target, TRIM

            ion = Ion('{ion_symbol}', energy={ion_energy_eV * 1e3})

            layers = []
            for lspec in {layers_spec}:
                layers.append(Layer(
                    lspec['elements'],
                    density=lspec['density'],
                    width=lspec['width']
                ))
            target = Target(layers)

            srim_dir = os.environ.get('SRIM_EXECUTABLE_DIRECTORY', '/opt/SRIM')
            trim = TRIM(target, ion, number_ions={n_ions}, calculation={calc})
            trim.run(srim_dir)

            # Copy outputs
            srim_out = os.path.join(srim_dir, 'SRIM Outputs')
            out_dir = '/app/output'
            if os.path.isdir(srim_out):
                for f in os.listdir(srim_out):
                    src = os.path.join(srim_out, f)
                    if os.path.isfile(src):
                        shutil.copy2(src, os.path.join(out_dir, f))
            print('TRIM completed successfully')
        """)

        return self._docker.run_trim_script(script, output_dir)

    @staticmethod
    def _serialize_target(target: Target) -> str:
        """Serialize Target layers to a Python literal for Docker script."""
        layers = []
        for layer in target.layers:
            elem_dict = {}
            for element in layer.elements:
                sym = element.symbol if hasattr(element, 'symbol') else str(element)
                elem_info = layer.elements[element]
                elem_dict[sym] = {
                    'stoich': elem_info.get('stoich', 1.0),
                    'E_d': elem_info.get('E_d', 25),
                    'lattice': elem_info.get('lattice', 3),
                    'surface': elem_info.get('surface', 3),
                }
            layers.append({
                'elements': elem_dict,
                'density': layer.density,
                'width': layer.width,
            })
        return repr(layers)
