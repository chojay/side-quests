#!/usr/bin/env python3
"""
Example 03: Ion species comparison at 100 eV on ITO.

Compares N+, Ar+, O+, and B+ range distributions.

Usage:
    python examples/03_ion_comparison.py
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.pysrim_patches import apply_patches
from src.core.simulation_runner import SRIMSimulation
from src.core.parameter_sweep import ParameterSweep
from src.analysis.visualizer import SRIMVisualizer
from src.analysis.metrics import compute_range_metrics

logging.basicConfig(level=logging.INFO)
apply_patches()


def main():
    energy = 100  # eV

    print("=" * 60)
    print(f"Ion Species Comparison at {energy} eV on ITO")
    print("=" * 60)

    sim = SRIMSimulation(use_docker=True)
    sweep = ParameterSweep(sim)

    range_data = sweep.species_sweep(
        species=["N", "Ar", "O", "B"],
        energy_eV=energy,
        target_name="ITO",
        number_ions=2000,
    )

    print(f"\nResults ({len(range_data)} species):")
    for ion_sym, rdf in range_data.items():
        metrics = compute_range_metrics(rdf)
        print(f"  {ion_sym:3s}: Rp = {metrics.Rp_nm:.2f} nm "
              f"± {metrics.delta_Rp_nm:.2f} nm")

    # Plot
    if range_data:
        viz = SRIMVisualizer()
        viz.plot_species_comparison(
            range_data, energy,
            save_path="03_species_comparison_100eV_ITO.png",
        )
        print("\nFigure saved to output/figures/03_species_comparison_100eV_ITO.png")


if __name__ == "__main__":
    main()
