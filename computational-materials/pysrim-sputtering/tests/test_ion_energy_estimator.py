"""
Tests for ion energy estimation from process conditions.
"""
import pytest
from src.core.ion_energy_estimator import IonEnergyEstimator, IonEnergyEstimate


class TestIonEnergyEstimator:
    @pytest.fixture
    def estimator(self):
        return IonEnergyEstimator()

    def test_higher_pressure_lower_energy(self, estimator):
        """Core physics: higher pressure → more thermalization → lower energy."""
        e_low_p = estimator.estimate_substrate_ion_energy(8)
        e_high_p = estimator.estimate_substrate_ion_energy(30)
        assert e_low_p.energy_eV > e_high_p.energy_eV

    def test_negative_bias_increases_energy(self, estimator):
        """Negative substrate bias accelerates positive ions."""
        e_no_bias = estimator.estimate_substrate_ion_energy(12, bias_V=0)
        e_neg_bias = estimator.estimate_substrate_ion_energy(12, bias_V=-20)
        assert e_neg_bias.energy_eV > e_no_bias.energy_eV
        # The increase should be approximately |V_bias| = 20 eV
        delta = e_neg_bias.energy_eV - e_no_bias.energy_eV
        assert delta == pytest.approx(20, abs=1)

    def test_positive_bias_no_effect(self, estimator):
        """Positive bias repels ions, should not increase energy."""
        e_no_bias = estimator.estimate_substrate_ion_energy(12, bias_V=0)
        e_pos_bias = estimator.estimate_substrate_ion_energy(12, bias_V=20)
        assert e_pos_bias.energy_eV == pytest.approx(e_no_bias.energy_eV, abs=1)

    def test_icp_increases_energy(self, estimator):
        """ICP assist should boost ion energy."""
        e_no_icp = estimator.estimate_substrate_ion_energy(12, icp_power_kw=0)
        e_with_icp = estimator.estimate_substrate_ion_energy(12, icp_power_kw=2.0)
        assert e_with_icp.energy_eV > e_no_icp.energy_eV

    def test_energy_range_reasonable(self, estimator):
        """Estimated energies should be in physically reasonable range."""
        for pressure in [8, 12, 30]:
            est = estimator.estimate_substrate_ion_energy(pressure)
            assert 5 < est.energy_eV < 500, f"Energy {est.energy_eV} at {pressure} mTorr unreasonable"
            assert est.energy_range_eV[0] < est.energy_eV < est.energy_range_eV[1]

    def test_target_energy_scales_with_power(self, estimator):
        """Target bombardment energy should increase with RF power."""
        e_low = estimator.estimate_target_ion_energy(rf_power_kw=0.5)
        e_high = estimator.estimate_target_ion_energy(rf_power_kw=5.0)
        assert e_high.energy_eV > e_low.energy_eV

    def test_target_energy_has_self_bias(self, estimator):
        """Target energy should reflect V_dc self-bias component."""
        est = estimator.estimate_target_ion_energy(rf_power_kw=3.5)
        assert 'V_dc_self_bias' in est.components
        assert est.components['V_dc_self_bias'] > 0

    def test_generate_energy_range(self, estimator):
        """Generate estimates for all pressure conditions."""
        estimates = estimator.generate_energy_range()
        assert len(estimates) >= 3  # At least one per pressure
        for est in estimates:
            assert isinstance(est, IonEnergyEstimate)

    def test_estimate_has_confidence(self, estimator):
        """All estimates should have a confidence level."""
        est = estimator.estimate_substrate_ion_energy(12)
        assert est.confidence in ("low", "medium", "high")

    def test_out_of_range_pressure_low_confidence(self, estimator):
        """Extreme pressures should have low confidence."""
        est = estimator.estimate_substrate_ion_energy(1)  # Very low
        assert est.confidence == "low"
