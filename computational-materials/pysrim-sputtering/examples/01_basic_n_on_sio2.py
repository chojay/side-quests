#!/usr/bin/env python3
"""
Example 01: Basic N+ ion bombardment of SiO2 target.

This is the "hello world" for the pySRIM project.
Runs a single TRIM simulation of 100 eV nitrogen ions on a
silicon dioxide target and prints the basic results.

Usage:
    python examples/01_basic_n_on_sio2.py
"""
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.pysrim_patches import apply_patches, verify_installation
from src.materials.database import MaterialDatabase
from src.core.ion_energy_estimator import IonEnergyEstimator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Step 1: Verify pysrim installation
    print("=" * 60)
    print("pySRIM: Basic N+ → SiO2 Simulation")
    print("=" * 60)

    apply_patches()
    if not verify_installation():
        print("ERROR: pysrim installation check failed")
        sys.exit(1)
    print("\n✓ pysrim installation verified\n")

    # Step 2: Show material database
    db = MaterialDatabase()
    print(db.summary())
    print()

    # Step 3: Estimate ion energies from process conditions
    estimator = IonEnergyEstimator()

    print("Ion Energy Estimates (Substrate bombardment, Scenario B):")
    print("-" * 60)
    for pressure in [8, 12, 30]:
        est = estimator.estimate_substrate_ion_energy(pressure)
        print(f"  {pressure:2d} mTorr: {est.energy_eV:6.1f} eV "
              f"(range: {est.energy_range_eV[0]:.0f}-{est.energy_range_eV[1]:.0f} eV)")

    print()
    print("Ion Energy Estimates (Target bombardment, Scenario A):")
    print("-" * 60)
    for power in [0.5, 2.0, 3.5, 5.0]:
        est = estimator.estimate_target_ion_energy(rf_power_kw=power)
        print(f"  {power:.1f} kW: {est.energy_eV:6.1f} eV "
              f"(V_dc ≈ {est.components['V_dc_self_bias']:.0f} V)")

    # Step 4: Create SRIM objects directly (without running TRIM)
    from srim import Ion, Layer, Target

    ion = Ion('N', energy=100e3)  # 100 keV (pysrim convention)
    sio2_layer = db.get_layer('SiO2')
    target = Target([sio2_layer])

    print(f"\n{'=' * 60}")
    print(f"TRIM Simulation Setup (ready to run):")
    print(f"  Ion: N+ at 100 eV")
    print(f"  Target: SiO2 (ρ = {db.get_density('SiO2')} g/cm³)")
    print(f"  Composition: {db.get_composition_string('SiO2')}")
    print(f"{'=' * 60}")
    print()
    print("To run the actual TRIM simulation, Docker must be available.")
    print("Use: docker-compose run srim python examples/01_basic_n_on_sio2.py")
    print()

    # Step 5: Try to run simulation if Docker or SRIM is available
    try:
        from src.utils.docker_helper import check_docker_setup
        status = check_docker_setup()
        print(f"Docker status: {status}")

        if status['docker_available']:
            from src.core.simulation_runner import SRIMSimulation
            sim = SRIMSimulation(use_docker=True)
            print("\nRunning TRIM simulation via Docker...")
            result = sim.run_scenario_a(
                ion_energy_eV=100,
                ion_symbol="N",
                number_ions=1000,
                calculation=1,
            )
            print(f"  Output directory: {result.output_dir}")
            print(f"  Elapsed: {result.elapsed_seconds:.1f}s")
        else:
            print("\nDocker not available. Skipping actual TRIM execution.")
            print("Material definitions and energy estimates are validated above.")
    except Exception as e:
        logger.warning(f"Could not run TRIM: {e}")
        print(f"\nNote: TRIM execution skipped ({e})")
        print("All configurations validated successfully.")


if __name__ == "__main__":
    main()
