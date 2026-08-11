#!/usr/bin/env python3
"""
DICOM Series Comparison
=======================
Compares two MRI studies (baseline vs follow-up) exported from a hospital
imaging CD.

For each study this script:
1. Inventories every series folder and reads DICOM headers with pydicom
2. Extracts acquisition metadata (TR/TE/TI, pixel spacing, slice thickness,
   scanning sequence, matrix size, field strength)
3. Classifies each series into a sequence type (T2, FLAIR, DWI, ADC, SWI,
   T1 pre/post contrast) from the series description and pulse parameters
4. Matches corresponding series between the two studies with a parameter
   similarity score (matrix, slice thickness, TR/TE, slice count)
5. Loads matched volumes and reports intensity statistics per pair

Expected layout: each study root contains SER00001, SER00002, ... folders
of DICOM files, as produced by many scanner/PACS CD exports.

Usage:
    python dicom_series_compare.py \
        --baseline PATH/TO/STUDY_A/dicom \
        --followup PATH/TO/STUDY_B/dicom \
        --output   PATH/TO/output_dir
"""

import argparse
import os
from pathlib import Path
from collections import defaultdict
import json
import pydicom
import numpy as np
from datetime import datetime


def get_dicom_files(path):
    """Get all DICOM files from a directory tree."""
    dcm_files = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith('.dcm') or (not '.' in f and Path(root, f).is_file()):
                full_path = Path(root) / f
                # Verify it's a DICOM file
                try:
                    ds = pydicom.dcmread(str(full_path), stop_before_pixels=True, force=True)
                    if hasattr(ds, 'Modality'):
                        dcm_files.append(full_path)
                except Exception:
                    pass
    return sorted(dcm_files)


def extract_series_info(dcm_path):
    """Extract key metadata from a DICOM file."""
    try:
        ds = pydicom.dcmread(str(dcm_path), stop_before_pixels=True)

        info = {
            'file_path': str(dcm_path),
            'series_number': getattr(ds, 'SeriesNumber', None),
            'series_description': getattr(ds, 'SeriesDescription', 'Unknown'),
            'series_uid': getattr(ds, 'SeriesInstanceUID', None),
            'modality': getattr(ds, 'Modality', 'Unknown'),
            'rows': getattr(ds, 'Rows', None),
            'columns': getattr(ds, 'Columns', None),
            'slice_thickness': getattr(ds, 'SliceThickness', None),
            'pixel_spacing': getattr(ds, 'PixelSpacing', None),
            'spacing_between_slices': getattr(ds, 'SpacingBetweenSlices', None),
            'tr': getattr(ds, 'RepetitionTime', None),
            'te': getattr(ds, 'EchoTime', None),
            'ti': getattr(ds, 'InversionTime', None),
            'flip_angle': getattr(ds, 'FlipAngle', None),
            'sequence_name': getattr(ds, 'SequenceName', None),
            'scanning_sequence': getattr(ds, 'ScanningSequence', None),
            'sequence_variant': getattr(ds, 'SequenceVariant', None),
            'image_type': getattr(ds, 'ImageType', None),
            'magnetic_field_strength': getattr(ds, 'MagneticFieldStrength', None),
            'manufacturer': getattr(ds, 'Manufacturer', None),
            'slice_location': getattr(ds, 'SliceLocation', None),
            'instance_number': getattr(ds, 'InstanceNumber', None),
        }
        return info
    except Exception as e:
        print(f"Error reading {dcm_path}: {e}")
        return None


def get_sequence_type(series_desc, scanning_seq=None, te=None, ti=None):
    """Determine the sequence type from description and pulse parameters."""
    desc = str(series_desc).lower() if series_desc else ''

    # Check description-based patterns
    if 'dwi' in desc or 'diffusion' in desc:
        return 'DWI'
    if 'adc' in desc:
        return 'ADC'
    if 'eadc' in desc:
        return 'eADC'
    if 'flair' in desc:
        return 'FLAIR'
    if 'swan' in desc or 'swi' in desc:
        return 'SWI'
    if 'asl' in desc or 'cbf' in desc:
        return 'Perfusion'
    if 't2' in desc and 'flair' not in desc:
        return 'T2'
    if 't1' in desc:
        if 'post' in desc:
            return 'T1_Post'
        return 'T1_Pre'
    if 'local' in desc:
        return 'Localizer'

    # Fall back to scanning sequence + timing heuristics
    if scanning_seq:
        seq_str = str(scanning_seq).lower()
        if 'ir' in seq_str and ti and ti > 1500:
            return 'FLAIR'
        if 'ep' in seq_str:
            return 'DWI'
        if 'se' in seq_str:
            if te and te > 80:
                return 'T2'
            else:
                return 'T1_Pre'
        if 'gr' in seq_str:
            return 'GRE'

    return 'Other'


def analyze_dataset(path, label):
    """Analyze all series in a dataset."""
    print(f"\n{'='*70}")
    print(f"Analyzing {label}")
    print(f"Path: {path}")
    print('='*70)

    if not path.exists():
        print(f"ERROR: Path does not exist: {path}")
        return [], {}

    series_data = defaultdict(list)

    # Find all series folders
    series_folders = sorted([d for d in path.iterdir() if d.is_dir() and d.name.startswith('SER')])
    print(f"Found {len(series_folders)} series folders")

    for series_folder in series_folders:
        dcm_files = list(series_folder.glob('*.dcm'))
        if not dcm_files:
            dcm_files = [f for f in series_folder.iterdir() if f.is_file() and not f.name.startswith('.')]

        if dcm_files:
            # Get info from first file
            info = extract_series_info(dcm_files[0])
            if info:
                info['folder'] = series_folder.name
                info['num_images'] = len(dcm_files)
                info['sequence_type'] = get_sequence_type(
                    info['series_description'],
                    info['scanning_sequence'],
                    info['te'],
                    info.get('ti')
                )
                series_data[series_folder.name] = info

    # Print summary
    series_list = []
    for folder, info in sorted(series_data.items()):
        series_list.append(info)
        print(f"\n{folder}: {info['series_description']}")
        print(f"  Type: {info['sequence_type']} | Images: {info['num_images']}")
        print(f"  Dims: {info['rows']}x{info['columns']} | Slice: {info['slice_thickness']} mm")
        print(f"  TR/TE: {info['tr']}/{info['te']} ms")

    return series_list, series_data


def match_sequences(baseline_series, followup_series):
    """Match sequences between the two studies based on type and parameters."""
    matches = []

    # Group by sequence type
    base_by_type = defaultdict(list)
    followup_by_type = defaultdict(list)

    for s in baseline_series:
        base_by_type[s['sequence_type']].append(s)
    for s in followup_series:
        followup_by_type[s['sequence_type']].append(s)

    # Match by type
    for seq_type in base_by_type:
        if seq_type in followup_by_type and seq_type not in ['Other', 'Localizer']:
            base_list = base_by_type[seq_type]
            followup_list = followup_by_type[seq_type]

            # Try to match based on similar parameters
            for base in base_list:
                best_match = None
                best_score = 0

                for cand in followup_list:
                    score = 0

                    # Check dimensions
                    if base['rows'] == cand['rows'] and base['columns'] == cand['columns']:
                        score += 3

                    # Check slice thickness
                    if base['slice_thickness'] and cand['slice_thickness']:
                        if abs(base['slice_thickness'] - cand['slice_thickness']) < 0.5:
                            score += 2

                    # Check TR/TE
                    if base['tr'] and cand['tr']:
                        if abs(base['tr'] - cand['tr']) / max(base['tr'], 1) < 0.15:
                            score += 1
                    if base['te'] and cand['te']:
                        if abs(base['te'] - cand['te']) / max(base['te'], 1) < 0.15:
                            score += 1

                    # Check similar image counts
                    if base['num_images'] and cand['num_images']:
                        ratio = min(base['num_images'], cand['num_images']) / max(base['num_images'], cand['num_images'])
                        if ratio > 0.7:
                            score += 1

                    if score > best_score:
                        best_score = score
                        best_match = cand

                if best_match and best_score >= 3:
                    matches.append({
                        'sequence_type': seq_type,
                        'baseline': base,
                        'followup': best_match,
                        'match_score': best_score
                    })

    return matches


def load_series_volume(series_path):
    """Load all slices from a series into a 3D volume, sorted by slice location."""
    dcm_files = sorted(series_path.glob('*.dcm'))
    if not dcm_files:
        dcm_files = sorted([f for f in series_path.iterdir() if f.is_file() and not f.name.startswith('.')])

    slices = []
    slice_locations = []

    for f in dcm_files:
        try:
            ds = pydicom.dcmread(str(f))
            if hasattr(ds, 'pixel_array'):
                slices.append(ds.pixel_array.astype(np.float32))
                loc = getattr(ds, 'SliceLocation', getattr(ds, 'InstanceNumber', len(slices)))
                slice_locations.append(float(loc) if loc else len(slices))
        except Exception:
            pass

    if not slices:
        return None, None

    # Sort by slice location
    sorted_pairs = sorted(zip(slice_locations, slices), key=lambda x: x[0])
    slices = [s for _, s in sorted_pairs]

    return np.stack(slices, axis=0), sorted([s for s, _ in sorted_pairs])


def compute_volume_statistics(volume):
    """Compute comprehensive statistics for a 3D volume."""
    if volume is None:
        return {}

    # Basic statistics
    stats = {
        'shape': list(volume.shape),
        'mean': float(np.mean(volume)),
        'std': float(np.std(volume)),
        'min': float(np.min(volume)),
        'max': float(np.max(volume)),
        'median': float(np.median(volume)),
        'p5': float(np.percentile(volume, 5)),
        'p25': float(np.percentile(volume, 25)),
        'p75': float(np.percentile(volume, 75)),
        'p95': float(np.percentile(volume, 95)),
    }

    # Create brain mask (simple thresholding)
    threshold = np.percentile(volume, 15)
    brain_mask = volume > threshold

    if np.any(brain_mask):
        brain_voxels = volume[brain_mask]
        stats['brain_mean'] = float(np.mean(brain_voxels))
        stats['brain_std'] = float(np.std(brain_voxels))
        stats['brain_volume_voxels'] = int(np.sum(brain_mask))

    return stats


def compare_matched_series(match, baseline_root, followup_root):
    """Compare a matched pair of series."""
    base_info = match['baseline']
    followup_info = match['followup']
    seq_type = match['sequence_type']

    print(f"\n--- Comparing {seq_type} ---")
    print(f"  BASELINE:  {base_info['folder']} - {base_info['series_description']} ({base_info['num_images']} slices)")
    print(f"  FOLLOW-UP: {followup_info['folder']} - {followup_info['series_description']} ({followup_info['num_images']} slices)")

    # Load volumes
    base_vol, _ = load_series_volume(baseline_root / base_info['folder'])
    followup_vol, _ = load_series_volume(followup_root / followup_info['folder'])

    comparison = {
        'sequence_type': seq_type,
        'baseline': {
            'folder': base_info['folder'],
            'description': base_info['series_description'],
        },
        'followup': {
            'folder': followup_info['folder'],
            'description': followup_info['series_description'],
        }
    }

    if base_vol is not None:
        comparison['baseline']['statistics'] = compute_volume_statistics(base_vol)
        print(f"  BASELINE volume: {base_vol.shape}, mean={comparison['baseline']['statistics']['mean']:.1f}")

    if followup_vol is not None:
        comparison['followup']['statistics'] = compute_volume_statistics(followup_vol)
        print(f"  FOLLOW-UP volume: {followup_vol.shape}, mean={comparison['followup']['statistics']['mean']:.1f}")

    # Calculate differences if both volumes loaded
    if base_vol is not None and followup_vol is not None:
        base_stats = comparison['baseline']['statistics']
        followup_stats = comparison['followup']['statistics']

        comparison['changes'] = {
            'mean_change': followup_stats['mean'] - base_stats['mean'],
            'mean_change_percent': (followup_stats['mean'] - base_stats['mean']) / base_stats['mean'] * 100 if base_stats['mean'] != 0 else 0,
            'std_change': followup_stats['std'] - base_stats['std'],
            'brain_mean_change': followup_stats.get('brain_mean', 0) - base_stats.get('brain_mean', 0) if 'brain_mean' in followup_stats and 'brain_mean' in base_stats else None,
        }

        print(f"  Change: {comparison['changes']['mean_change_percent']:.1f}% mean intensity change")

    return comparison


def parse_args():
    parser = argparse.ArgumentParser(description="Compare two DICOM MRI studies series-by-series.")
    parser.add_argument('--baseline', required=True, type=Path,
                        help="Baseline study DICOM root (contains SER* series folders)")
    parser.add_argument('--followup', required=True, type=Path,
                        help="Follow-up study DICOM root (contains SER* series folders)")
    parser.add_argument('--output', required=True, type=Path,
                        help="Output directory for JSON results")
    return parser.parse_args()


def main():
    args = parse_args()
    baseline_path = args.baseline
    followup_path = args.followup
    output_path = args.output

    print("="*70)
    print("DICOM SERIES COMPARISON: BASELINE VS FOLLOW-UP")
    print("="*70)
    print(f"Baseline:  {baseline_path}")
    print(f"Follow-up: {followup_path}")

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Analyze both datasets
    baseline_series, _ = analyze_dataset(baseline_path, "BASELINE STUDY")
    followup_series, _ = analyze_dataset(followup_path, "FOLLOW-UP STUDY")

    if not baseline_series:
        print("\nERROR: No baseline series found!")
        return None

    if not followup_series:
        print("\nERROR: No follow-up series found!")
        return None

    # Match sequences
    print(f"\n{'='*70}")
    print("SEQUENCE MATCHING")
    print('='*70)

    matches = match_sequences(baseline_series, followup_series)

    print(f"\nFound {len(matches)} matched sequence pairs:")
    for m in matches:
        print(f"  {m['sequence_type']}: {m['baseline']['folder']} <-> {m['followup']['folder']} (score={m['match_score']})")

    # Compare matched series
    print(f"\n{'='*70}")
    print("DETAILED COMPARISON")
    print('='*70)

    comparisons = []
    for match in matches:
        comp = compare_matched_series(match, baseline_path, followup_path)
        comparisons.append(comp)

    # Generate summary
    results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'baseline': {
            'path': str(baseline_path),
            'series_count': len(baseline_series),
        },
        'followup': {
            'path': str(followup_path),
            'series_count': len(followup_series),
        },
        'matched_pairs': len(matches),
        'comparisons': comparisons,
    }

    # Save results
    results_file = output_path / 'comparison_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")

    # Print final summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    print(f"Baseline series:  {len(baseline_series)}")
    print(f"Follow-up series: {len(followup_series)}")
    print(f"Matched pairs:    {len(matches)}")

    print("\nKey sequence types compared:")
    for comp in comparisons:
        seq = comp['sequence_type']
        if 'changes' in comp and comp['changes'].get('mean_change_percent') is not None:
            change = comp['changes']['mean_change_percent']
            print(f"  {seq}: {change:+.1f}% mean intensity change")
        else:
            print(f"  {seq}: comparison incomplete")

    return results


if __name__ == '__main__':
    main()
