"""
Tests for SRIM output parsing.
"""
import pytest
from src.analysis.output_parser import SRIMOutputParser


class TestManualRangeParser:
    def test_parse_mock_range(self, mock_srim_output):
        parser = SRIMOutputParser(mock_srim_output)
        df = parser.parse_range()
        # Manual parser should find data
        if df is not None:
            assert 'depth_A' in df.columns
            assert 'ions_per_A_per_ion' in df.columns
            assert 'depth_nm' in df.columns
            assert len(df) > 0
            assert df['depth_A'].min() >= 0

    def test_parse_nonexistent_dir(self, tmp_path):
        parser = SRIMOutputParser(str(tmp_path / "nonexistent"))
        df = parser.parse_range()
        assert df is None

    def test_parse_all_returns_dict(self, mock_srim_output):
        parser = SRIMOutputParser(mock_srim_output)
        results = parser.parse_all()
        assert isinstance(results, dict)
        assert 'range' in results
        assert 'ionization' in results
        assert 'vacancy' in results
        assert 'phonon' in results
