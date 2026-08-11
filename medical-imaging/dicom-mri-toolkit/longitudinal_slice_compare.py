#!/usr/bin/env python3
"""
Longitudinal Slice Comparison
=============================
Creates intensity-normalized, slice-by-slice comparisons between two MRI
studies of the same subject (baseline vs follow-up).

For each configured sequence pair this script:
1. Loads DICOM slices sorted by slice location
2. Builds a morphological brain mask per slice
3. Normalizes intensity with percentile scaling inside the mask
4. Matches slices between studies by fractional position through the stack
   (robust to different slice counts)
5. Renders side-by-side panels with an RdBu difference map and an overlay
   flagging voxels that changed by more than 15%
6. Writes regional statistics (quadrants, hemispheres, central region) to JSON

Run dicom_series_compare.py first to discover which series folders pair up,
then edit KEY_SERIES below to match your own export.

Usage:
    python longitudinal_slice_compare.py \
        --baseline PATH/TO/STUDY_A/dicom \
        --followup PATH/TO/STUDY_B/dicom \
        --output   PATH/TO/output_dir
"""

import argparse
from pathlib import Path
import json
import pydicom
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import ndimage

# Key series pairs for comparison.
# EDIT THESE to match your own DICOM export (folder names differ per scanner).
# Use the matched pairs reported by dicom_series_compare.py.
KEY_SERIES = {
    'Axial_T2': {'baseline': 'SER000XX', 'followup': 'SER000XX', 'desc': 'Axial T2'},
    'Axial_FLAIR': {'baseline': 'SER000XX', 'followup': 'SER000XX', 'desc': 'Axial FLAIR'},
    'Axial_DWI': {'baseline': 'SER000XX', 'followup': 'SER000XX', 'desc': 'Axial DWI'},
    'Axial_ADC': {'baseline': 'SER000XX', 'followup': 'SER000XX', 'desc': 'ADC map'},
    'Axial_T1_Pre': {'baseline': 'SER000XX', 'followup': 'SER000XX', 'desc': 'Axial T1 pre-contrast'},
    'Axial_T1_Post': {'baseline': 'SER000XX', 'followup': 'SER000XX', 'desc': 'Axial T1 post-contrast'},
    'Axial_SWI': {'baseline': 'SER000XX', 'followup': 'SER000XX', 'desc': 'SWI'},
}


def load_series_slices(series_path):
    """Load DICOM slices sorted by position."""
    dcm_files = sorted(series_path.glob('*.dcm'))
    if not dcm_files:
        dcm_files = sorted([f for f in series_path.iterdir()
                          if f.is_file() and not f.name.startswith('.')])

    slices = []
    for f in dcm_files:
        try:
            ds = pydicom.dcmread(str(f))
            if hasattr(ds, 'pixel_array'):
                loc = getattr(ds, 'SliceLocation', getattr(ds, 'InstanceNumber', len(slices)))
                slices.append({
                    'data': ds.pixel_array.astype(np.float32),
                    'location': float(loc) if loc else len(slices),
                    'instance': getattr(ds, 'InstanceNumber', len(slices)),
                })
        except Exception:
            pass

    slices.sort(key=lambda x: x['location'])
    return slices


def create_brain_mask(image, threshold_percentile=12):
    """Create a simple brain mask using intensity thresholding."""
    threshold = np.percentile(image, threshold_percentile)
    mask = image > threshold

    # Clean up mask with morphological operations
    mask = ndimage.binary_fill_holes(mask)
    mask = ndimage.binary_erosion(mask, iterations=2)
    mask = ndimage.binary_dilation(mask, iterations=2)

    return mask


def normalize_intensity(image, mask=None):
    """Normalize image intensity using percentile scaling."""
    if mask is None:
        mask = image > np.percentile(image, 10)

    brain_values = image[mask]
    if len(brain_values) == 0:
        return image

    p5 = np.percentile(brain_values, 5)
    p95 = np.percentile(brain_values, 95)

    normalized = (image - p5) / (p95 - p5 + 1e-6)
    normalized = np.clip(normalized, 0, 1)

    return normalized


def compute_regional_statistics(image, mask):
    """Compute statistics for different brain regions."""
    if not np.any(mask):
        return {}

    h, w = image.shape
    stats = {}

    # Overall brain
    brain_vals = image[mask]
    stats['whole_brain'] = {
        'mean': float(np.mean(brain_vals)),
        'std': float(np.std(brain_vals)),
        'median': float(np.median(brain_vals)),
    }

    # Approximate regional masks (quadrants)
    center_y, center_x = h // 2, w // 2

    # Anterior (frontal)
    anterior_mask = np.zeros_like(mask)
    anterior_mask[:center_y, :] = True
    anterior_mask = anterior_mask & mask
    if np.any(anterior_mask):
        vals = image[anterior_mask]
        stats['anterior'] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))}

    # Posterior (occipital)
    posterior_mask = np.zeros_like(mask)
    posterior_mask[center_y:, :] = True
    posterior_mask = posterior_mask & mask
    if np.any(posterior_mask):
        vals = image[posterior_mask]
        stats['posterior'] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))}

    # Left hemisphere
    left_mask = np.zeros_like(mask)
    left_mask[:, :center_x] = True
    left_mask = left_mask & mask
    if np.any(left_mask):
        vals = image[left_mask]
        stats['left'] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))}

    # Right hemisphere
    right_mask = np.zeros_like(mask)
    right_mask[:, center_x:] = True
    right_mask = right_mask & mask
    if np.any(right_mask):
        vals = image[right_mask]
        stats['right'] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))}

    # Central (periventricular area)
    margin_y = h // 4
    margin_x = w // 4
    central_mask = np.zeros_like(mask)
    central_mask[margin_y:h-margin_y, margin_x:w-margin_x] = True
    central_mask = central_mask & mask
    if np.any(central_mask):
        vals = image[central_mask]
        stats['central'] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))}

    return stats


def create_comparison_image(base_img, followup_img, base_mask, followup_mask, title, output_path):
    """Create a side-by-side comparison figure."""
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))

    # Normalize both images
    base_norm = normalize_intensity(base_img, base_mask)
    followup_norm = normalize_intensity(followup_img, followup_mask)

    # Baseline
    axes[0].imshow(base_norm, cmap='gray', vmin=0, vmax=1)
    axes[0].set_title('BASELINE', fontsize=12, fontweight='bold')
    axes[0].axis('off')

    # Follow-up
    axes[1].imshow(followup_norm, cmap='gray', vmin=0, vmax=1)
    axes[1].set_title('FOLLOW-UP', fontsize=12, fontweight='bold')
    axes[1].axis('off')

    # Difference map (follow-up - baseline)
    diff = followup_norm - base_norm
    diff_display = np.clip(diff + 0.5, 0, 1)  # Shift to 0.5 = no change
    im = axes[2].imshow(diff_display, cmap='RdBu_r', vmin=0, vmax=1)
    axes[2].set_title('DIFFERENCE\n(blue=decrease, red=increase)', fontsize=10)
    axes[2].axis('off')
    plt.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04)

    # Overlay showing significant changes
    combined_mask = base_mask | followup_mask
    threshold = 0.15  # 15% change threshold
    significant_increase = (diff > threshold) & combined_mask
    significant_decrease = (diff < -threshold) & combined_mask

    overlay = np.stack([base_norm, base_norm, base_norm], axis=-1)
    overlay[significant_increase] = [1, 0.2, 0.2]  # Red for increase
    overlay[significant_decrease] = [0.2, 0.2, 1]  # Blue for decrease

    axes[3].imshow(overlay)
    axes[3].set_title('SIGNIFICANT CHANGES\n(>15% difference)', fontsize=10)
    axes[3].axis('off')

    plt.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    return {
        'significant_increase_voxels': int(np.sum(significant_increase)),
        'significant_decrease_voxels': int(np.sum(significant_decrease)),
        'brain_voxels': int(np.sum(combined_mask)),
    }


def analyze_sequence_pair(seq_name, baseline_root, followup_root, output_dir):
    """Perform detailed analysis of a matched sequence pair."""
    config = KEY_SERIES[seq_name]

    print(f"\n{'='*60}")
    print(f"Analyzing {seq_name}: {config['desc']}")
    print('='*60)

    base_series_path = baseline_root / config['baseline']
    followup_series_path = followup_root / config['followup']

    if not base_series_path.exists():
        print(f"  ERROR: Baseline path not found: {base_series_path}")
        return None
    if not followup_series_path.exists():
        print(f"  ERROR: Follow-up path not found: {followup_series_path}")
        return None

    # Load slices
    base_slices = load_series_slices(base_series_path)
    followup_slices = load_series_slices(followup_series_path)

    print(f"  BASELINE slices:  {len(base_slices)}")
    print(f"  FOLLOW-UP slices: {len(followup_slices)}")

    # Create output directory for this sequence
    seq_output = output_dir / seq_name
    seq_output.mkdir(parents=True, exist_ok=True)

    results = {
        'sequence': seq_name,
        'description': config['desc'],
        'baseline_slices': len(base_slices),
        'followup_slices': len(followup_slices),
        'slice_analyses': [],
    }

    # Match slices by fractional position since slice counts differ
    min_slices = min(len(base_slices), len(followup_slices))
    if min_slices == 0:
        return results
    step_base = len(base_slices) / min_slices
    step_followup = len(followup_slices) / min_slices

    # Analyze middle 60% of slices (most diagnostic content)
    start_pct = 20
    end_pct = 80
    start_idx = int(min_slices * start_pct / 100)
    end_idx = int(min_slices * end_pct / 100)

    for i in range(start_idx, end_idx, max(1, (end_idx - start_idx) // 10)):  # Sample ~10 slices
        base_idx = int(i * step_base)
        followup_idx = int(i * step_followup)

        if base_idx >= len(base_slices) or followup_idx >= len(followup_slices):
            continue

        base_img = base_slices[base_idx]['data']
        followup_img = followup_slices[followup_idx]['data']

        # Handle dimension mismatch
        if base_img.shape != followup_img.shape:
            # Resize to match
            from scipy.ndimage import zoom
            scale_y = followup_img.shape[0] / base_img.shape[0]
            scale_x = followup_img.shape[1] / base_img.shape[1]
            base_img = zoom(base_img, (scale_y, scale_x), order=1)

        # Create brain masks
        base_mask = create_brain_mask(base_img)
        followup_mask = create_brain_mask(followup_img)

        # Regional statistics
        base_stats = compute_regional_statistics(base_img, base_mask)
        followup_stats = compute_regional_statistics(followup_img, followup_mask)

        # Create comparison image
        slice_pct = int(i / min_slices * 100)
        img_path = seq_output / f"comparison_slice_{slice_pct:02d}pct.png"
        change_info = create_comparison_image(
            base_img, followup_img, base_mask, followup_mask,
            f"{seq_name} - Slice {slice_pct}%",
            img_path
        )

        slice_analysis = {
            'slice_percent': slice_pct,
            'baseline_index': base_idx,
            'followup_index': followup_idx,
            'baseline_stats': base_stats,
            'followup_stats': followup_stats,
            'change_info': change_info,
            'image_path': str(img_path),
        }

        # Calculate normalized differences
        if 'whole_brain' in base_stats and 'whole_brain' in followup_stats:
            base_mean = base_stats['whole_brain']['mean']
            followup_mean = followup_stats['whole_brain']['mean']
            # Use ratio for intensity-normalized comparison
            if base_mean > 0:
                slice_analysis['intensity_ratio'] = followup_mean / base_mean
            else:
                slice_analysis['intensity_ratio'] = 1.0

        results['slice_analyses'].append(slice_analysis)

        print(f"  Slice {slice_pct}%: {change_info['significant_increase_voxels']} increased, "
              f"{change_info['significant_decrease_voxels']} decreased voxels")

    # Summary statistics
    if results['slice_analyses']:
        total_increased = sum(s['change_info']['significant_increase_voxels']
                            for s in results['slice_analyses'])
        total_decreased = sum(s['change_info']['significant_decrease_voxels']
                            for s in results['slice_analyses'])
        total_brain = sum(s['change_info']['brain_voxels']
                         for s in results['slice_analyses'])

        results['summary'] = {
            'total_significant_increase': total_increased,
            'total_significant_decrease': total_decreased,
            'total_brain_voxels': total_brain,
            'increase_percent': total_increased / total_brain * 100 if total_brain > 0 else 0,
            'decrease_percent': total_decreased / total_brain * 100 if total_brain > 0 else 0,
        }

        print(f"\n  Summary: {results['summary']['increase_percent']:.1f}% increased, "
              f"{results['summary']['decrease_percent']:.1f}% decreased")

    # Save results
    results_path = seq_output / 'analysis_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    return results


def parse_args():
    parser = argparse.ArgumentParser(description="Slice-by-slice longitudinal MRI comparison.")
    parser.add_argument('--baseline', required=True, type=Path,
                        help="Baseline study DICOM root (contains SER* series folders)")
    parser.add_argument('--followup', required=True, type=Path,
                        help="Follow-up study DICOM root (contains SER* series folders)")
    parser.add_argument('--output', required=True, type=Path,
                        help="Output directory for figures and JSON results")
    return parser.parse_args()


def main():
    args = parse_args()

    print("="*70)
    print("LONGITUDINAL SLICE COMPARISON: BASELINE VS FOLLOW-UP")
    print("="*70)
    print()
    print("This analysis performs:")
    print("  1. Intensity-normalized comparisons")
    print("  2. Regional brain statistics")
    print("  3. Visual difference maps")
    print("  4. Significant change detection (>15% threshold)")

    args.output.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for seq_name in KEY_SERIES:
        try:
            results = analyze_sequence_pair(seq_name, args.baseline, args.followup, args.output)
            if results:
                all_results[seq_name] = results
        except Exception as e:
            print(f"  ERROR analyzing {seq_name}: {e}")
            import traceback
            traceback.print_exc()

    # Save combined results
    combined_path = args.output / 'all_sequence_analysis.json'
    with open(combined_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print('='*70)
    print(f"Results saved to: {args.output}")
    print(f"Sequences analyzed: {len(all_results)}")

    # Print summary table
    print("\nSUMMARY OF CHANGES:")
    print("-"*60)
    print(f"{'Sequence':<20} {'Increased':<15} {'Decreased':<15}")
    print("-"*60)

    for seq_name, results in all_results.items():
        if 'summary' in results:
            inc = results['summary']['increase_percent']
            dec = results['summary']['decrease_percent']
            print(f"{seq_name:<20} {inc:>6.1f}%         {dec:>6.1f}%")

    return all_results


if __name__ == '__main__':
    main()
