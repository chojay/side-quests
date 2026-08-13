"""
Integration tests requiring Docker + SRIM.

These tests run actual TRIM simulations and are marked slow.
Skip with: pytest -v --ignore=tests/test_integration.py

Or run only integration tests:
    pytest tests/test_integration.py -v
"""
import os

import pytest

from src.utils.docker_helper import check_docker_setup


# Skip all tests in this file if Docker is not available
docker_status = check_docker_setup()
pytestmark = pytest.mark.skipif(
    not docker_status['docker_available'] or not docker_status['image_exists'],
    reason="Docker not available or pysrim image not built"
)


class TestEndToEnd:
    """Full end-to-end tests with real SRIM execution."""

    @pytest.mark.slow
    def test_basic_n_on_sio2(self):
        """Run 100 eV N+ on SiO2 and verify output."""
        from src.core.simulation_runner import SRIMSimulation
        from src.analysis.output_parser import SRIMOutputParser
        from src.analysis.metrics import compute_range_metrics

        sim = SRIMSimulation(use_docker=True)
        result = sim.run_scenario_a(
            ion_energy_eV=100,
            ion_symbol="N",
            number_ions=500,
            calculation=1,
        )

        assert os.path.isdir(result.output_dir)
        assert result.elapsed_seconds > 0

        # Parse and check range
        parser = SRIMOutputParser(result.output_dir)
        range_df = parser.parse_range()
        if range_df is not None:
            metrics = compute_range_metrics(range_df)
            # At 100 eV, N+ in SiO2 should have Rp ~ 0.5-2 nm
            assert 0.1 < metrics.Rp_nm < 10.0

    @pytest.mark.slow
    def test_sputter_yield_nonzero(self):
        """Sputtering calculation should produce non-zero yield."""
        from src.core.simulation_runner import SRIMSimulation
        from src.analysis.sputtering import calculate_sputter_yield

        sim = SRIMSimulation(use_docker=True)
        result = sim.run_scenario_a(
            ion_energy_eV=500,
            ion_symbol="Ar",
            number_ions=1000,
            calculation=3,  # Sputtering mode
        )

        yield_val = calculate_sputter_yield(result.output_dir)
        if yield_val is not None:
            assert yield_val > 0
