#!/usr/bin/env python3
"""
Example 02: Ion energy sweep  -  Rp vs energy curve.

Sweeps N+ ion energy from 10 to 1000 eV on SiO2 target
and generates a log-log projected range plot.

Usage:
    python examples/02_energy_sweep.py
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.pysrim_patches import apply_patches
from src.core.simulation_runner import SRIMSimulation
from src.core.parameter_sweep import ParameterSweep
from src.analysis.visualizer import SRIMVisualizer

logging.basicConfig(level=logging.INFO)
apply_patches()


def main():
    print("=" * 60)
    print("Energy Sweep: N+ → SiO2 (10-1000 eV)")
    print("=" * 60)

    sim = SRIMSimulation(use_docker=True)
    sweep = ParameterSweep(sim)

    # Run energy sweep
    energies = [10, 20, 50, 100, 200, 500, 1000]
    df = sweep.energy_sweep(
        ion_symbol="N",
        target_name="SiO2",
        energies_eV=energies,
        number_ions=2000,  # Reduced for faster sweep
        calculation=1,     # Quick KP for speed
    )

    print("\nResults:")
    print(df[['energy_eV', 'Rp_nm', 'delta_Rp_nm']].to_string(index=False))

    # Plot
    if 'Rp_nm' in df.columns:
        viz = SRIMVisualizer()
        viz.plot_rp_vs_energy(
            df['energy_eV'].tolist(),
            df['Rp_nm'].tolist(),
            df['delta_Rp_nm'].tolist() if 'delta_Rp_nm' in df else None,
            ion_symbol="N",
            target_name="SiO₂",
            save_path="01_rp_vs_energy_N_SiO2.png",
        )
        print("\nFigure saved to output/figures/01_rp_vs_energy_N_SiO2.png")


if __name__ == "__main__":
    main()
