"""
Parse SRIM/TRIM output files into structured DataFrames.

Wraps pysrim's output parsers and normalizes data for analysis.
SRIM writes output files to a 'SRIM Outputs' subdirectory (or the
run output directory when copied by simulation_runner).
"""
import os
import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SRIMOutputParser:
    """
    Parse SRIM/TRIM output files into pandas DataFrames.

    Parameters
    ----------
    output_dir : str
        Directory containing SRIM output files (RANGE.txt, IONIZ.txt, etc.).
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        # Check for 'SRIM Outputs' subdirectory (pysrim convention)
        srim_subdir = os.path.join(output_dir, "SRIM Outputs")
        if os.path.isdir(srim_subdir):
            self.output_dir = srim_subdir

    def parse_range(self) -> Optional[pd.DataFrame]:
        """
        Parse ion range distribution from RANGE.txt.

        Returns
        -------
        pd.DataFrame
            Columns: depth_A (Angstroms), ions_per_A_per_ion
        """
        try:
            from srim.output import Range
            data = Range(self.output_dir)
            df = pd.DataFrame({
                'depth_A': data.dataframe.index.values,
                'ions_per_A_per_ion': data.dataframe.values.flatten(),
            })
            df['depth_nm'] = df['depth_A'] / 10.0
            return df
        except Exception as e:
            logger.warning(f"Could not parse RANGE.txt: {e}")
            return self._parse_range_manual()

    def parse_ionization(self) -> Optional[pd.DataFrame]:
        """
        Parse ionization energy loss profiles from IONIZ.txt.

        Returns
        -------
        pd.DataFrame
            Columns: depth_A, ions_ionization (eV/A/ion),
                     recoils_ionization (eV/A/ion)
        """
        try:
            from srim.output import Ioniz
            data = Ioniz(self.output_dir)
            df = data.dataframe.copy()
            df.columns = ['ions_ionization', 'recoils_ionization']
            df['depth_A'] = df.index.values
            df['depth_nm'] = df['depth_A'] / 10.0
            df = df.reset_index(drop=True)
            return df
        except Exception as e:
            logger.warning(f"Could not parse IONIZ.txt: {e}")
            return None

    def parse_vacancies(self) -> Optional[pd.DataFrame]:
        """
        Parse vacancy depth profiles from VACANCY.txt.

        Returns
        -------
        pd.DataFrame
            Columns: depth_A, target_vacancies (vacancies/A/ion),
                     replacement_collisions
        """
        try:
            from srim.output import Vacancy
            data = Vacancy(self.output_dir)
            df = data.dataframe.copy()
            # Vacancy output has columns per element + total
            df['depth_A'] = df.index.values
            df['depth_nm'] = df['depth_A'] / 10.0
            df = df.reset_index(drop=True)
            return df
        except Exception as e:
            logger.warning(f"Could not parse VACANCY.txt: {e}")
            return None

    def parse_phonons(self) -> Optional[pd.DataFrame]:
        """
        Parse phonon (lattice heating) depth profiles from PHONON.txt.

        Returns
        -------
        pd.DataFrame
            Columns: depth_A, phonons_eV_per_A_per_ion
        """
        try:
            from srim.output import Phonon
            data = Phonon(self.output_dir)
            df = data.dataframe.copy()
            df['depth_A'] = df.index.values
            df['depth_nm'] = df['depth_A'] / 10.0
            df = df.reset_index(drop=True)
            return df
        except ImportError:
            logger.debug("Phonon parser not available in this pysrim version")
            return self._parse_phonon_manual()
        except Exception as e:
            logger.warning(f"Could not parse PHONON.txt: {e}")
            return self._parse_phonon_manual()

    def _parse_phonon_manual(self) -> Optional[pd.DataFrame]:
        """Manual fallback for PHONON.txt parsing."""
        phonon_path = os.path.join(self.output_dir, "PHONON.txt")
        if not os.path.exists(phonon_path):
            return None
        try:
            depths, values = [], []
            data_started = False
            with open(phonon_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if data_started:
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                depths.append(float(parts[0]))
                                values.append(float(parts[1]))
                            except ValueError:
                                continue
                    elif line.startswith("---"):
                        data_started = True
            if depths:
                return pd.DataFrame({
                    'depth_A': depths,
                    'phonons': values,
                    'depth_nm': [d / 10 for d in depths],
                })
        except Exception as e:
            logger.error(f"Manual PHONON.txt parsing failed: {e}")
        return None

    def parse_all(self) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Parse all available SRIM output files.

        Returns
        -------
        dict
            Keys: 'range', 'ionization', 'vacancy', 'phonon'
        """
        return {
            'range': self.parse_range(),
            'ionization': self.parse_ionization(),
            'vacancy': self.parse_vacancies(),
            'phonon': self.parse_phonons(),
        }

    def _parse_range_manual(self) -> Optional[pd.DataFrame]:
        """
        Manually parse RANGE.txt if pysrim parser fails.

        SRIM RANGE.txt format has a header section followed by
        depth (Angstroms) vs distribution data.
        """
        range_path = os.path.join(self.output_dir, "RANGE.txt")
        if not os.path.exists(range_path):
            return None

        try:
            depths = []
            values = []
            data_started = False
            with open(range_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if data_started:
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                depths.append(float(parts[0]))
                                values.append(float(parts[1]))
                            except ValueError:
                                continue
                    elif line.startswith("---"):
                        data_started = True

            if depths:
                df = pd.DataFrame({
                    'depth_A': depths,
                    'ions_per_A_per_ion': values,
                })
                df['depth_nm'] = df['depth_A'] / 10.0
                return df
        except Exception as e:
            logger.error(f"Manual RANGE.txt parsing failed: {e}")

        return None
