"""
Custom sputtering yield extraction from SRIM output.

pysrim's built-in Sputter parser is a non-functional stub.
This module parses the raw SRIM output files to extract
sputtering yield data.
"""
import os
import re
import logging
from typing import Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def parse_sputter_output(output_dir: str) -> Optional[Dict]:
    """
    Parse sputtering data from SRIM output files.

    SRIM writes sputtering information to multiple files depending
    on the calculation type. This function tries several approaches.

    Parameters
    ----------
    output_dir : str
        Directory containing SRIM output files.

    Returns
    -------
    dict or None
        Keys: total_yield, yield_by_element, n_ions, energy_eV
    """
    # Check for SRIM Outputs subdirectory
    srim_subdir = os.path.join(output_dir, "SRIM Outputs")
    if os.path.isdir(srim_subdir):
        output_dir = srim_subdir

    # Try parsing SPUTTER.txt (calculation type 3)
    result = _parse_sputter_txt(output_dir)
    if result is not None:
        return result

    # Try parsing from TDATA.txt (TRIM data summary)
    result = _parse_tdata(output_dir)
    if result is not None:
        return result

    # Try parsing from TRIM.OUT summary
    result = _parse_trim_out(output_dir)
    if result is not None:
        return result

    logger.warning("No sputtering data found in output files")
    return None


def calculate_sputter_yield(output_dir: str) -> Optional[float]:
    """
    Extract total sputtering yield (atoms/ion).

    Parameters
    ----------
    output_dir : str
        Directory containing SRIM output files.

    Returns
    -------
    float or None
    """
    data = parse_sputter_output(output_dir)
    if data is not None:
        return data.get('total_yield')
    return None


def _parse_sputter_txt(output_dir: str) -> Optional[Dict]:
    """Parse SPUTTER.txt file from calculation type 3."""
    path = os.path.join(output_dir, "SPUTTER.txt")
    if not os.path.exists(path):
        return None

    try:
        total_sputtered = 0
        n_ions = 0
        yield_by_element = {}

        with open(path, 'r') as f:
            content = f.read()

        # Look for total sputtered atoms
        match = re.search(r'Total\s+Sputtered\s+Atoms\s*=\s*(\d+)', content)
        if match:
            total_sputtered = int(match.group(1))

        # Look for number of ions
        match = re.search(r'Number\s+of\s+Ions\s*=\s*(\d+)', content)
        if match:
            n_ions = int(match.group(1))

        # Look for per-element yields
        element_pattern = re.compile(
            r'(\w+)\s+Sputtered\s*=\s*(\d+\.?\d*)'
        )
        for match in element_pattern.finditer(content):
            elem = match.group(1)
            count = float(match.group(2))
            yield_by_element[elem] = count / max(n_ions, 1)

        if n_ions > 0:
            return {
                'total_yield': total_sputtered / n_ions,
                'yield_by_element': yield_by_element,
                'n_ions': n_ions,
                'total_sputtered': total_sputtered,
            }
    except Exception as e:
        logger.warning(f"Error parsing SPUTTER.txt: {e}")

    return None


def _parse_tdata(output_dir: str) -> Optional[Dict]:
    """Parse TDATA.txt for sputtering information."""
    path = os.path.join(output_dir, "TDATA.txt")
    if not os.path.exists(path):
        return None

    try:
        with open(path, 'r') as f:
            content = f.read()

        match = re.search(
            r'Sputtering\s+Yield\s*=\s*(\d+\.?\d*)\s+atoms/ion',
            content, re.IGNORECASE
        )
        if match:
            return {
                'total_yield': float(match.group(1)),
                'yield_by_element': {},
                'n_ions': 0,
            }
    except Exception as e:
        logger.warning(f"Error parsing TDATA.txt: {e}")

    return None


def _parse_trim_out(output_dir: str) -> Optional[Dict]:
    """Parse TRIM.OUT summary for sputtering data."""
    path = os.path.join(output_dir, "TRIM.OUT")
    if not os.path.exists(path):
        return None

    try:
        with open(path, 'r') as f:
            content = f.read()

        match = re.search(
            r'Total\s+Sputtering\s+Yield\s*=\s*(\d+\.?\d*)',
            content, re.IGNORECASE
        )
        if match:
            return {
                'total_yield': float(match.group(1)),
                'yield_by_element': {},
                'n_ions': 0,
            }
    except Exception as e:
        logger.warning(f"Error parsing TRIM.OUT: {e}")

    return None
