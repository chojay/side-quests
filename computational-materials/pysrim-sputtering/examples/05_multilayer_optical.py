#!/usr/bin/env python3
"""
Example 05: Ion penetration through a TiO2 optical coating into ITO.

Tests whether a thin TiO2 optical coating shields the ITO
from ion bombardment.

Usage:
    python examples/05_multilayer_optical.py
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
    energy = 100  # eV

    print("=" * 60)
    print(f"Multilayer Study: N+ {energy} eV → TiO2/ITO")
    print("=" * 60)

    sim = SRIMSimulation(use_docker=True)
    sweep = ParameterSweep(sim)

    summary_df, range_data = sweep.multilayer_sweep(
        tio2_thicknesses_nm=[0, 1, 2, 5, 10],
        ion_energy_eV=energy,
        ion_symbol="N",
        number_ions=2000,
    )

    if 'Rp_nm' in summary_df.columns:
        print("\nResults:")
        cols = ['tio2_thickness_nm', 'Rp_nm', 'delta_Rp_nm']
        print(summary_df[[c for c in cols if c in summary_df.columns]].to_string(index=False))

    # Plot
    if range_data:
        viz = SRIMVisualizer()
        viz.plot_scenario_b_summary(
            energies_eV=[energy],
            rp_nm=[summary_df.iloc[0].get('Rp_nm', 0)],
            straggling_nm=[summary_df.iloc[0].get('delta_Rp_nm', 0)],
            multilayer_dfs=range_data,
            save_path="05_multilayer_optical_shielding.png",
        )
        print("\nFigure saved to output/figures/05_multilayer_optical_shielding.png")


if __name__ == "__main__":
    main()
