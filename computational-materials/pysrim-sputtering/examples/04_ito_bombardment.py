#!/usr/bin/env python3
"""
Example 04: N+ bombardment of a growing ITO transparent conductor (Scenario B).

Estimates ion energies from RF sputtering process conditions and runs
SRIM for each pressure regime.

Usage:
    python examples/04_ito_bombardment.py
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.pysrim_patches import apply_patches
from src.core.ion_energy_estimator import IonEnergyEstimator
from src.core.simulation_runner import SRIMSimulation
from src.core.parameter_sweep import ParameterSweep

logging.basicConfig(level=logging.INFO)
apply_patches()


def main():
    print("=" * 60)
    print("Scenario B: N+ → ITO Film Bombardment")
    print("=" * 60)

    # Step 1: Estimate energies from process conditions
    estimator = IonEnergyEstimator()

    print("\nEstimated ion energies at substrate:")
    print("-" * 50)
    for pressure in [8, 12, 30]:
        est = estimator.estimate_substrate_ion_energy(pressure)
        print(f"  {pressure:2d} mTorr: {est.energy_eV:.1f} eV "
              f"({est.energy_range_eV[0]:.0f}-{est.energy_range_eV[1]:.0f})")

    # Step 2: Run pressure sweep
    sim = SRIMSimulation(use_docker=True)
    sweep = ParameterSweep(sim)

    print("\nRunning pressure sweep...")
    df = sweep.pressure_sweep(
        pressures_mtorr=[8, 12, 30],
        ion_symbol="N",
        target_name="ITO",
        number_ions=2000,
    )

    if 'Rp_nm' in df.columns:
        print("\nResults:")
        cols = ['pressure_mtorr', 'energy_eV', 'Rp_nm', 'delta_Rp_nm']
        print(df[[c for c in cols if c in df.columns]].to_string(index=False))

    # Step 3: Run bias sweep at 12 mTorr
    print("\nRunning bias sweep at 12 mTorr...")
    bias_df = sweep.bias_sweep(
        bias_voltages_V=[-20, -5, 0, 5, 20],
        pressure_mtorr=12.0,
        ion_symbol="N",
        number_ions=2000,
    )

    if 'Rp_nm' in bias_df.columns:
        print("\nBias sweep results:")
        cols = ['bias_V', 'energy_eV', 'Rp_nm']
        print(bias_df[[c for c in cols if c in bias_df.columns]].to_string(index=False))


if __name__ == "__main__":
    main()
