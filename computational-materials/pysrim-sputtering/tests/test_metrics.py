"""
Tests for metrics computation from synthetic data.
"""
import numpy as np
import pytest

from src.analysis.metrics import (
    compute_range_metrics,
    compute_damage_metrics,
    compute_energy_partitioning,
    RangeMetrics,
    DamageMetrics,
    EnergyPartitioning,
)


class TestRangeMetrics:
    def test_gaussian_range(self, sample_range_df):
        """Test range metrics on a known Gaussian distribution."""
        metrics = compute_range_metrics(sample_range_df)

        # The synthetic data has peak at 30 A (3 nm) with sigma 10 A (1 nm)
        assert isinstance(metrics, RangeMetrics)
        assert metrics.Rp_angstrom == pytest.approx(30, abs=5)
        assert metrics.Rp_nm == pytest.approx(3.0, abs=0.5)
        assert metrics.delta_Rp_angstrom == pytest.approx(10, abs=3)
        assert metrics.peak_depth_angstrom == pytest.approx(30, abs=5)

    def test_rp_nm_consistent(self, sample_range_df):
        """Rp_nm should be Rp_angstrom / 10."""
        metrics = compute_range_metrics(sample_range_df)
        assert metrics.Rp_nm == pytest.approx(metrics.Rp_angstrom / 10, abs=0.01)

    def test_straggling_nm_consistent(self, sample_range_df):
        metrics = compute_range_metrics(sample_range_df)
        assert metrics.delta_Rp_nm == pytest.approx(metrics.delta_Rp_angstrom / 10, abs=0.01)

    def test_max_depth_greater_than_rp(self, sample_range_df):
        metrics = compute_range_metrics(sample_range_df)
        assert metrics.max_depth_angstrom >= metrics.Rp_angstrom

    def test_repr(self, sample_range_df):
        metrics = compute_range_metrics(sample_range_df)
        s = repr(metrics)
        assert 'Rp=' in s
        assert 'nm' in s


class TestDamageMetrics:
    def test_damage_from_synthetic(self, sample_vacancy_df):
        metrics = compute_damage_metrics(sample_vacancy_df)
        assert isinstance(metrics, DamageMetrics)
        assert metrics.peak_vacancy_density > 0
        assert metrics.peak_depth_angstrom == pytest.approx(25, abs=5)
        assert metrics.total_vacancies_per_ion > 0
        assert metrics.damage_extends_to_angstrom > 0

    def test_repr(self, sample_vacancy_df):
        metrics = compute_damage_metrics(sample_vacancy_df)
        s = repr(metrics)
        assert 'vac/A/ion' in s


class TestEnergyPartitioning:
    def test_fractions_sum_to_one(self, sample_ionization_df, sample_phonon_df):
        ep = compute_energy_partitioning(
            sample_ionization_df, sample_phonon_df, ion_energy_eV=100
        )
        total = ep.electronic_fraction + ep.nuclear_fraction + ep.phonon_fraction
        assert total == pytest.approx(1.0, abs=0.01)

    def test_electronic_dominates_at_high_energy(self, sample_ionization_df, sample_phonon_df):
        """Electronic stopping typically dominates in our synthetic data."""
        ep = compute_energy_partitioning(
            sample_ionization_df, sample_phonon_df, ion_energy_eV=100
        )
        assert isinstance(ep, EnergyPartitioning)
        # Electronic (ion ionization) should be largest in our test data
        assert ep.electronic_fraction > ep.phonon_fraction

    def test_handles_none_inputs(self):
        ep = compute_energy_partitioning(None, None, 100)
        assert ep.electronic_fraction == 0
        assert ep.nuclear_fraction == 0
        assert ep.phonon_fraction == 0
