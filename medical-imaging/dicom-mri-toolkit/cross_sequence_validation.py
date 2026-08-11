#!/usr/bin/env python3
"""
Cross-Sequence Candidate Validation
===================================
Validates nodule candidates (from ventricle_3d_analysis.py) against the
same anatomy on multiple MRI sequences: T2, FLAIR, T1 pre-contrast,
T1 post-contrast, and SWI/SWAN.

Per candidate, three generic tissue-characterization checks (thresholds are
constants in the code; adjust them to the question you are asking):
- Signal ratio against a cortical gray-matter reference on T2, FLAIR, and T1
- Contrast enhancement (T1 post / T1 pre signal ratio)
- Susceptibility effects on SWI/SWAN

The hard part is spatial: each sequence has its own voxel size, FOV
center, and slice grid. The alignment stack here evolved over several
iterations (see README) and works as follows:
1. Z alignment: cross-correlate the brain cross-sectional-area profile of
   each sequence against T2 over a +/-150mm physical search range
2. XY alignment: median brain-centroid offset at several matched Z levels
3. Local fine-tuning: normalized cross-correlation on Sobel edge maps
   (edges are contrast-invariant across sequences)
4. Tissue-shifted ROI: measurement points are pushed a few pixels along
   the outward mask-gradient normal, off the ventricular wall and into
   parenchyma, to avoid CSF partial-volume contamination

Also generates per-candidate validation panels (full slice + zoomed ROI
with curvature-colored contours) and a cross-sequence summary grid.

Usage:
    python cross_sequence_validation.py \
        --data-dir PATH/TO/NIFTI_DIR \
        --candidates PATH/TO/candidate_analysis_results.json \
        --output-dir PATH/TO/output_dir
"""

import argparse
import nibabel as nib
import numpy as np
from scipy import ndimage, interpolate
from skimage import measure, morphology, filters
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import Normalize
import json
import os

# Sequence NIfTI filenames, relative to --data-dir.
# EDIT THESE to match your own export (names come from the scanner).
SEQUENCE_FILES = {
    'T2': "SER000XX_Ax_T2.nii.gz",
    'FLAIR': "SER000XX_Ax_FLAIR.nii.gz",
    'T1_pre': "SER000XX_Ax_T1.nii.gz",
    'T1_post': "SER000XX_Ax_T1_post.nii.gz",
    'SWAN': "SER000XX_Ax_SWI.nii.gz",
}


def nifti_slice_to_dicom(slice_idx, series_name):
    """Map a NIfTI slice index back to the DICOM filename it came from.

    Assumes the common dcm2niix-style ordering: NIfTI slice N corresponds
    to IMG{N+1:05d}.dcm in the source series folder. Verify this mapping
    on your own export before trusting the labels.
    """
    return f"{series_name}/IMG{slice_idx + 1:05d}.dcm"


def load_and_normalize(path, label=""):
    """Load NIfTI and normalize to 0-1 range."""
    if label:
        print(f"  Loading {label}: {os.path.basename(path)}")
    img = nib.load(path)
    data = img.get_fdata().astype(np.float32)
    voxel = img.header.get_zooms()[:3]
    nonzero = data[data > 0]
    if len(nonzero) > 0:
        p1, p99 = np.percentile(nonzero, [1, 99])
        data = np.clip((data - p1) / (p99 - p1 + 1e-8), 0, 1)
    if label:
        print(f"    Shape: {data.shape}, Voxel: {[round(v, 3) for v in voxel]}")
    return data, voxel


def segment_ventricles(data, voxel_size):
    """Ventricle segmentation (same approach as ventricle_3d_analysis.py)."""
    brain_mask = data > 0.05
    brain_mask = morphology.binary_closing(brain_mask, morphology.ball(3))
    brain_mask = ndimage.binary_fill_holes(brain_mask)

    erode_voxels = max(3, int(8.0 / min(voxel_size[:2])))
    brain_interior = morphology.binary_erosion(brain_mask, morphology.ball(erode_voxels))

    interior_data = data[brain_interior]
    if len(interior_data) < 100:
        return np.zeros_like(brain_mask)

    thresholds = filters.threshold_multiotsu(interior_data[interior_data > 0.01], classes=4)
    csf_mask = (data > thresholds[-1]) & brain_interior

    csf_mask = morphology.binary_opening(csf_mask, morphology.ball(1))
    csf_mask = morphology.binary_closing(csf_mask, morphology.ball(1))

    z_nonzero = np.where(np.any(brain_mask, axis=(0, 1)))[0]
    if len(z_nonzero) > 0:
        z_min, z_max = z_nonzero[0], z_nonzero[-1]
        z_brain_range = z_max - z_min
        z_vent_low = z_min + int(0.30 * z_brain_range)
        z_vent_high = z_min + int(0.75 * z_brain_range)
        csf_mask[:, :, :z_vent_low] = False
        csf_mask[:, :, z_vent_high:] = False

    labeled = measure.label(csf_mask)
    regions = measure.regionprops(labeled)

    if not regions:
        return csf_mask

    center = np.array(data.shape) / 2
    ventricle_mask = np.zeros_like(csf_mask)

    scored = []
    for region in regions:
        centroid = np.array(region.centroid)
        dist_xy = np.linalg.norm(centroid[:2] - center[:2])
        max_dist = center[0] * 0.25
        if dist_xy < max_dist and region.area > 100:
            score = region.area / (1 + dist_xy)
            scored.append((score, region.label))

    scored.sort(reverse=True)
    for score, label_id in scored[:2]:
        ventricle_mask[labeled == label_id] = True

    vol_mm3 = np.sum(ventricle_mask) * np.prod(voxel_size)
    if vol_mm3 > 25000:
        ventricle_mask = morphology.binary_erosion(ventricle_mask, morphology.ball(2))

    return ventricle_mask


def get_main_ventricle_contours(vent_mask_slice, min_length=100):
    """Extract only the main ventricular wall contours from a mask slice.

    Returns only the 2 largest contours (left and right ventricle walls),
    filtering out small fragments, disconnected loops, and artifacts.
    """
    contours = measure.find_contours(vent_mask_slice.astype(float), 0.5)
    if not contours:
        return []

    # Sort by length descending
    contours_sorted = sorted(contours, key=len, reverse=True)

    # Keep at most the 2 largest contours, only if they have >= min_length points
    main_contours = []
    for c in contours_sorted[:2]:
        if len(c) >= min_length:
            main_contours.append(c)

    return main_contours


def compute_curvature_bspline(contour, smoothing=25.0):
    """Fit B-spline to contour and compute signed curvature."""
    if len(contour) < 10:
        return np.zeros(len(contour)), contour

    diffs = np.diff(contour, axis=0)
    ds = np.sqrt(np.sum(diffs**2, axis=1))
    s = np.concatenate([[0], np.cumsum(ds)])
    s_norm = s / s[-1]

    try:
        tck_x, _ = interpolate.splprep([contour[:, 0]], u=s_norm, s=smoothing, k=3)
        tck_y, _ = interpolate.splprep([contour[:, 1]], u=s_norm, s=smoothing, k=3)

        u_fine = np.linspace(0, 1, len(contour))
        x_smooth = interpolate.splev(u_fine, tck_x)[0]
        y_smooth = interpolate.splev(u_fine, tck_y)[0]

        dx = interpolate.splev(u_fine, tck_x, der=1)[0]
        dy = interpolate.splev(u_fine, tck_y, der=1)[0]
        ddx = interpolate.splev(u_fine, tck_x, der=2)[0]
        ddy = interpolate.splev(u_fine, tck_y, der=2)[0]

        numerator = dx * ddy - dy * ddx
        denominator = (dx**2 + dy**2)**1.5 + 1e-10
        curvature = numerator / denominator

        smooth_contour = np.column_stack([x_smooth, y_smooth])
        return curvature, smooth_contour

    except Exception:
        return np.zeros(len(contour)), contour


# -- Cross-Sequence Alignment ------------------------------------------

def compute_brain_area_profile(data, threshold=0.05):
    """Compute brain cross-sectional area per axial slice."""
    brain = data > threshold
    return np.sum(brain, axis=(0, 1)).astype(float)


def find_z_offset(t2_data, t2_voxel, seq_data, seq_voxel):
    """Find the physical Z-offset between T2 and another sequence
    using brain cross-sectional area cross-correlation.

    Returns offset_mm such that:
        seq_z = (T2_slice * t2_voxel[2] - offset_mm) / seq_voxel[2]
    """
    t2_profile = compute_brain_area_profile(t2_data)
    seq_profile = compute_brain_area_profile(seq_data)

    t2_z_phys = np.arange(t2_data.shape[2]) * t2_voxel[2]
    seq_z_thick = seq_voxel[2]

    best_corr = -1
    best_offset = 0.0

    for offset_mm in np.arange(-150, 150, seq_z_thick):
        seq_slices = (t2_z_phys - offset_mm) / seq_z_thick
        valid = (seq_slices >= 0) & (seq_slices < seq_data.shape[2])
        if np.sum(valid) < 10:
            continue

        t2_vals = t2_profile[valid]
        seq_indices = seq_slices[valid].astype(int)
        seq_vals = seq_profile[seq_indices]

        t2_n = (t2_vals - t2_vals.mean()) / (t2_vals.std() + 1e-10)
        seq_n = (seq_vals - seq_vals.mean()) / (seq_vals.std() + 1e-10)
        corr = np.mean(t2_n * seq_n)

        if corr > best_corr:
            best_corr = corr
            best_offset = offset_mm

    return best_offset, best_corr


def pick_test_slices(t2_data, n_samples=6, threshold=0.05):
    """Pick sample Z slices in the ventricular band of the brain.

    Samples evenly between 35% and 60% of the brain's Z extent, which is
    where the lateral ventricles sit, instead of hardcoding slice indices.
    """
    brain = t2_data > threshold
    z_nonzero = np.where(np.any(brain, axis=(0, 1)))[0]
    if len(z_nonzero) == 0:
        mid = t2_data.shape[2] // 2
        return [mid]
    z_min, z_max = z_nonzero[0], z_nonzero[-1]
    z_range = z_max - z_min
    lo = z_min + int(0.35 * z_range)
    hi = z_min + int(0.60 * z_range)
    return sorted(set(np.linspace(lo, hi, n_samples, dtype=int).tolist()))


def compute_xy_offsets(t2_data, t2_voxel, volumes, voxels, z_offsets):
    """Compute in-plane XY offsets between T2 and other sequences.

    Different sequences may have different FOV centers, causing the brain
    to appear shifted in-plane even though voxel sizes are identical.
    Uses brain centroid comparison at multiple matched Z-levels.

    Returns dict: seq_name -> (dx_voxels, dy_voxels) to ADD to T2 position.
    """
    xy_offsets = {'T2': (0.0, 0.0)}

    # Sample at multiple ventricular Z-levels
    test_slices = pick_test_slices(t2_data)

    for seq_name in volumes:
        if seq_name == 'T2':
            continue
        seq_data = volumes[seq_name]
        seq_voxel = voxels[seq_name]
        z_off = z_offsets[seq_name]

        dx_samples = []
        dy_samples = []

        for t2_sl in test_slices:
            t2_z_mm = t2_sl * t2_voxel[2]
            t2_brain = t2_data[:, :, t2_sl] > 0.08
            if np.sum(t2_brain) < 100:
                continue

            seq_z = int((t2_z_mm - z_off) / seq_voxel[2])
            if seq_z < 0 or seq_z >= seq_data.shape[2]:
                continue
            seq_brain = seq_data[:, :, seq_z] > 0.08
            if np.sum(seq_brain) < 100:
                continue

            t2_com = ndimage.center_of_mass(t2_brain)
            seq_com = ndimage.center_of_mass(seq_brain)

            dx_samples.append(seq_com[0] - t2_com[0])
            dy_samples.append(seq_com[1] - t2_com[1])

        if dx_samples:
            xy_offsets[seq_name] = (np.median(dx_samples), np.median(dy_samples))
        else:
            xy_offsets[seq_name] = (0.0, 0.0)

    return xy_offsets


def _gradient_magnitude(image_2d):
    """Compute gradient magnitude using Sobel filters - edge map for alignment."""
    gx = ndimage.sobel(image_2d.astype(float), axis=0)
    gy = ndimage.sobel(image_2d.astype(float), axis=1)
    return np.sqrt(gx**2 + gy**2)


def local_edge_alignment(t2_slice, seq_slice, init_x, init_y,
                         patch_half=20, search_radius=12):
    """Fine-tune XY position using edge-based normalized cross-correlation.

    Uses gradient magnitude (Sobel edge) maps instead of raw intensity.
    Edges are contrast-invariant - ventricle boundaries show up as edges
    in T2, FLAIR, T1, and SWI regardless of which tissue is bright/dark.

    Returns (best_x, best_y, correlation_score).
    """
    # Compute edge maps
    t2_edges = _gradient_magnitude(t2_slice)
    seq_edges = _gradient_magnitude(seq_slice)

    # Extract T2 edge template
    t2_x = int(np.clip(init_x, patch_half, t2_edges.shape[0] - patch_half))
    t2_y = int(np.clip(init_y, patch_half, t2_edges.shape[1] - patch_half))
    template = t2_edges[t2_x - patch_half:t2_x + patch_half,
                        t2_y - patch_half:t2_y + patch_half]

    # Normalize template
    t_mean = template.mean()
    t_std = template.std()
    if t_std < 1e-6:
        return init_x, init_y, 0.0
    t_norm = (template - t_mean) / t_std

    best_corr = -1
    best_dx, best_dy = 0, 0

    for dx in range(-search_radius, search_radius + 1):
        for dy in range(-search_radius, search_radius + 1):
            cx = init_x + dx
            cy = init_y + dy

            x0 = cx - patch_half
            x1 = cx + patch_half
            y0 = cy - patch_half
            y1 = cy + patch_half

            if x0 < 0 or y0 < 0 or x1 > seq_edges.shape[0] or y1 > seq_edges.shape[1]:
                continue

            s_patch = seq_edges[x0:x1, y0:y1]
            if s_patch.shape != template.shape:
                continue

            s_mean = s_patch.mean()
            s_std = s_patch.std()
            if s_std < 1e-6:
                continue

            corr = np.mean(t_norm * (s_patch - s_mean) / s_std)
            if corr > best_corr:
                best_corr = corr
                best_dx, best_dy = dx, dy

    return init_x + best_dx, init_y + best_dy, best_corr


def map_t2_to_sequence(pos_x, pos_y, t2_slice, t2_voxel, seq_voxel,
                       z_offset_mm, seq_shape, xy_offset=(0.0, 0.0)):
    """Map a T2 (x, y, slice) position to another sequence.

    Uses:
    - Z: physical coordinate mapping with cross-correlated offset
    - XY: brain centroid-based in-plane offset correction (global)

    For local fine-tuning, use local_edge_alignment() after this.

    Args:
        seq_shape: shape of the target volume (used for clipping; no
            fixed matrix size is assumed)
        xy_offset: (dx, dy) in voxels to add to T2 position for this sequence.
    """
    # In-plane: apply XY correction for FOV center difference
    seq_x = int(np.clip(round(pos_x + xy_offset[0]), 0, seq_shape[0] - 1))
    seq_y = int(np.clip(round(pos_y + xy_offset[1]), 0, seq_shape[1] - 1))

    # Z mapping
    t2_z_mm = t2_slice * t2_voxel[2]
    seq_z = (t2_z_mm - z_offset_mm) / seq_voxel[2]
    seq_z = int(np.clip(round(seq_z), 0, seq_shape[2] - 1))

    return seq_x, seq_y, seq_z


# -- Validation Panel Generation ---------------------------------------

def generate_candidate_validation_panel(data, vent_mask, candidate, cand_idx,
                                        dicom_series, output_dir):
    """Generate a validation panel: full slices + zoomed curvature-colored ROI."""
    slices = candidate['slices']
    pos = candidate['position']
    side = candidate['side']
    region = candidate['region']
    mean_k = candidate['mean_curvature']

    roi_half = 35
    n_slices = len(slices)

    if n_slices == 1:
        z = slices[0]
        display_slices = [max(0, z - 1), z, min(data.shape[2] - 1, z + 1)]
    else:
        display_slices = slices

    n_cols = max(len(display_slices), 2)
    fig, axes = plt.subplots(2, n_cols, figsize=(6 * n_cols, 12))

    fig.suptitle(
        f"Candidate #{cand_idx + 1} - {side} {region}\n"
        f"Mean k = {mean_k:.3f} | Slices {slices}",
        fontsize=14, fontweight='bold', color='white'
    )

    for col_idx, z in enumerate(display_slices):
        if col_idx >= axes.shape[1]:
            break
        z = int(z)

        # -- Top row: Full slice with candidate marked --
        ax_full = axes[0, col_idx]
        ax_full.imshow(data[:, :, z].T, cmap='gray', origin='lower', aspect='equal')

        # Ventricle contour - only main contours
        main_contours = get_main_ventricle_contours(vent_mask[:, :, z])
        for c in main_contours:
            ax_full.plot(c[:, 0], c[:, 1], 'c-', linewidth=0.8, alpha=0.6)

        # Mark candidate position
        ax_full.add_patch(Circle(
            (pos[0], pos[1]), radius=8,
            fill=False, edgecolor='red', linewidth=2
        ))
        ax_full.add_patch(Circle(
            (pos[0], pos[1]), radius=15,
            fill=False, edgecolor='yellow', linewidth=1, linestyle='--'
        ))

        # ROI box
        r0 = max(0, int(pos[0] - roi_half))
        r1 = min(data.shape[0], int(pos[0] + roi_half))
        c0 = max(0, int(pos[1] - roi_half))
        c1 = min(data.shape[1], int(pos[1] + roi_half))
        rect = plt.Rectangle((r0, c0), r1 - r0, c1 - c0,
                             fill=False, edgecolor='lime', linewidth=1.5, linestyle='--')
        ax_full.add_patch(rect)

        is_primary = z in slices
        ax_full.set_title(
            f"Slice {z}" + (" *" if is_primary else " (context)") +
            f"\n{nifti_slice_to_dicom(z, dicom_series)}",
            color='yellow' if is_primary else 'gray', fontsize=11
        )
        ax_full.axis('off')

        # -- Bottom row: Zoomed ROI with curvature-colored contours --
        ax_zoom = axes[1, col_idx]
        roi_data = data[r0:r1, c0:c1, z].T
        ax_zoom.imshow(roi_data, cmap='gray', origin='lower', aspect='equal',
                       extent=[r0, r1, c0, c1])

        # Curvature-colored contour - only main contours
        for c in main_contours:
            curvature, smooth_c = compute_curvature_bspline(c, smoothing=25.0)
            abs_k = np.abs(curvature)
            norm = Normalize(vmin=0, vmax=max(0.3, np.percentile(abs_k, 95)))
            colors = plt.cm.coolwarm(norm(abs_k))
            for pt_idx in range(len(smooth_c) - 1):
                ax_zoom.plot(
                    smooth_c[pt_idx:pt_idx + 2, 0],
                    smooth_c[pt_idx:pt_idx + 2, 1],
                    color=colors[pt_idx], linewidth=2
                )

        # Candidate crosshair
        ax_zoom.axhline(y=pos[1], color='yellow', linewidth=0.5, alpha=0.5, linestyle=':')
        ax_zoom.axvline(x=pos[0], color='yellow', linewidth=0.5, alpha=0.5, linestyle=':')
        ax_zoom.add_patch(Circle(
            (pos[0], pos[1]), radius=3,
            fill=False, edgecolor='red', linewidth=2
        ))

        ax_zoom.set_xlim(r0, r1)
        ax_zoom.set_ylim(c0, c1)
        ax_zoom.set_title(
            f"Zoomed ROI - Slice {z}\nBlue=smooth, Red=high curvature",
            color='white', fontsize=10
        )
        ax_zoom.axis('off')

    # Hide unused columns
    for col_idx in range(len(display_slices), axes.shape[1]):
        axes[0, col_idx].axis('off')
        axes[1, col_idx].axis('off')

    plt.tight_layout()
    out_path = os.path.join(output_dir, f"validation_candidate_{cand_idx + 1:02d}.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"    Saved: {os.path.basename(out_path)}")
    return out_path


def generate_validation_summary(candidates, data, vent_mask, dicom_series, output_dir):
    """Generate summary composite of all candidates."""
    n = len(candidates)
    cols = min(n, 5)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 6 * rows))
    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)

    fig.suptitle("Candidate Validation Summary - Follow-up Scan",
                 fontsize=16, fontweight='bold', color='white')

    for i, cand in enumerate(candidates):
        row, col = i // cols, i % cols
        ax = axes[row, col]

        z = cand['slices'][len(cand['slices']) // 2]
        pos = cand['position']

        roi_half = 30
        x0 = max(0, int(pos[0] - roi_half))
        x1 = min(data.shape[0], int(pos[0] + roi_half))
        y0 = max(0, int(pos[1] - roi_half))
        y1 = min(data.shape[1], int(pos[1] + roi_half))

        ax.imshow(data[x0:x1, y0:y1, z].T, cmap='gray', origin='lower',
                  extent=[x0, x1, y0, y1])

        # Only main contours
        main_contours = get_main_ventricle_contours(vent_mask[:, :, z])
        for c in main_contours:
            curvature, smooth_c = compute_curvature_bspline(c, smoothing=25.0)
            abs_k = np.abs(curvature)
            norm_v = Normalize(vmin=0, vmax=max(0.3, np.percentile(abs_k, 95)))
            colors = plt.cm.coolwarm(norm_v(abs_k))
            for pt_idx in range(len(smooth_c) - 1):
                ax.plot(smooth_c[pt_idx:pt_idx + 2, 0],
                        smooth_c[pt_idx:pt_idx + 2, 1],
                        color=colors[pt_idx], linewidth=1.5)

        ax.add_patch(Circle((pos[0], pos[1]), radius=3,
                            fill=False, edgecolor='red', linewidth=2))
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)

        ax.set_title(
            f"#{i+1} {cand['side']} {cand['region']}\n"
            f"k={cand['mean_curvature']:.1f} | {cand['span']}sl | sl{z}\n"
            f"{nifti_slice_to_dicom(z, dicom_series)}",
            color='lime', fontsize=9, fontweight='bold'
        )
        ax.axis('off')

    # Hide unused cells
    for i in range(n, rows * cols):
        row, col = i // cols, i % cols
        axes[row, col].axis('off')

    plt.tight_layout()
    out_path = os.path.join(output_dir, "validation_summary.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"  Summary saved: {os.path.basename(out_path)}")


# -- Cross-Sequence Validation -----------------------------------------

def compute_tissue_position(pos_x, pos_y, z, vent_mask, shift=4):
    """Shift candidate position outward from the ventricle wall into tissue.

    Uses the gradient of the ventricle mask to find the outward direction
    (from ventricle interior toward surrounding tissue), then shifts the
    position by `shift` pixels in that direction.

    This avoids CSF partial-volume contamination in ROI measurements at
    the ventricular margin where wall-based candidates sit.
    """
    x = int(np.clip(pos_x, 0, vent_mask.shape[0] - 1))
    y = int(np.clip(pos_y, 0, vent_mask.shape[1] - 1))
    z = int(np.clip(z, 0, vent_mask.shape[2] - 1))

    slice_mask = vent_mask[:, :, z].astype(float)
    gx = ndimage.sobel(slice_mask, axis=0)
    gy = ndimage.sobel(slice_mask, axis=1)

    gx_at = gx[x, y]
    gy_at = gy[x, y]
    mag = np.sqrt(gx_at**2 + gy_at**2) + 1e-10

    # Outward normal (away from ventricle) = negative gradient direction
    nx = -gx_at / mag
    ny = -gy_at / mag

    tissue_x = int(np.clip(round(x + nx * shift), 0, vent_mask.shape[0] - 1))
    tissue_y = int(np.clip(round(y + ny * shift), 0, vent_mask.shape[1] - 1))

    return tissue_x, tissue_y


def measure_roi_signal(data, x, y, z, radius=6):
    """Measure mean signal in a square ROI centered at (x, y) on slice z."""
    x = int(np.clip(x, 0, data.shape[0] - 1))
    y = int(np.clip(y, 0, data.shape[1] - 1))
    z = int(np.clip(z, 0, data.shape[2] - 1))
    x0 = max(0, x - radius)
    x1 = min(data.shape[0], x + radius + 1)
    y0 = max(0, y - radius)
    y1 = min(data.shape[1], y + radius + 1)
    patch = data[x0:x1, y0:y1, z]
    if patch.size == 0:
        return 0.0
    return float(np.mean(patch))


def measure_cortex_signal(data, z, voxel_size):
    """Measure mean cortical gray matter signal at a given slice.

    Approximates cortex as the rim of the brain mask (mask minus its
    erosion, erosion depth ~8mm in physical units).
    """
    z = int(np.clip(z, 0, data.shape[2] - 1))
    brain_mask = data[:, :, z] > 0.08
    if np.sum(brain_mask) < 100:
        return 0.5

    eroded = morphology.binary_erosion(brain_mask, morphology.disk(
        max(3, int(8.0 / min(voxel_size[:2])))))
    cortex_mask = brain_mask & ~eroded

    if np.sum(cortex_mask) < 20:
        return float(np.mean(data[:, :, z][brain_mask]))

    return float(np.mean(data[:, :, z][cortex_mask]))


def generate_cross_sequence_panel(candidate, cand_idx, volumes, voxels,
                                  t2_voxel, z_offsets, xy_offsets, vent_mask,
                                  dicom_series, output_dir):
    """Generate cross-sequence panel with Z+XY alignment, tissue-shifted ROI,
    and visual alignment verification."""
    pos = candidate['position']
    slices = candidate['slices']
    mid_slice = slices[len(slices) // 2]
    roi_half = 30

    # Compute tissue-side position on T2 (shift away from ventricle lumen)
    tissue_x, tissue_y = compute_tissue_position(
        pos[0], pos[1], mid_slice, vent_mask, shift=4
    )

    seq_order = ['T2', 'FLAIR', 'T1_pre', 'T1_post', 'SWAN']
    seq_labels = ['T2', 'FLAIR', 'T1 Pre', 'T1 Post-Gad', 'SWI/SWAN']

    # 2 rows: top = zoomed ROI at candidate, bottom = full slice for alignment check
    fig, axes = plt.subplots(2, len(seq_order), figsize=(5 * len(seq_order), 10))
    fig.suptitle(
        f"Cross-Sequence Validation - Candidate #{cand_idx + 1} "
        f"({candidate['side']} {candidate['region']})\n"
        f"T2 Slices {slices} | Mean k = {candidate['mean_curvature']:.3f} | "
        f"XY+Z aligned, tissue-shifted 4px",
        fontsize=13, fontweight='bold', color='white'
    )

    xseq_results = {}

    for col, (seq_name, seq_label) in enumerate(zip(seq_order, seq_labels)):
        seq_data = volumes[seq_name]
        seq_voxel = voxels[seq_name]
        z_off = z_offsets[seq_name]
        xy_off = xy_offsets.get(seq_name, (0.0, 0.0))

        # Step 1: Global alignment (brain centroid + Z cross-corr)
        sx, sy, sz = map_t2_to_sequence(
            tissue_x, tissue_y, mid_slice, t2_voxel, seq_voxel, z_off,
            seq_data.shape, xy_off
        )

        # Step 2: Local fine-tuning via edge-based cross-correlation
        # Uses gradient magnitude (Sobel edges) - contrast-invariant across sequences
        local_corr = 0.0
        if seq_name != 'T2':
            sx_refined, sy_refined, local_corr = local_edge_alignment(
                volumes['T2'][:, :, mid_slice], seq_data[:, :, sz],
                sx, sy, patch_half=20, search_radius=12
            )
            sx, sy = sx_refined, sy_refined

        # Also map original wall position for visualization (with same local offset)
        wx, wy, wz = map_t2_to_sequence(
            pos[0], pos[1], mid_slice, t2_voxel, seq_voxel, z_off,
            seq_data.shape, xy_off
        )
        if seq_name != 'T2':
            # Apply same local correction offset
            local_dx = sx - int(np.clip(round(tissue_x + xy_off[0]), 0, seq_data.shape[0] - 1))
            local_dy = sy - int(np.clip(round(tissue_y + xy_off[1]), 0, seq_data.shape[1] - 1))
            wx = int(np.clip(wx + local_dx, 0, seq_data.shape[0] - 1))
            wy = int(np.clip(wy + local_dy, 0, seq_data.shape[1] - 1))

        # -- Top row: Zoomed ROI centered on tissue position --
        ax_zoom = axes[0, col]
        x0 = max(0, sx - roi_half)
        x1 = min(seq_data.shape[0], sx + roi_half)
        y0 = max(0, sy - roi_half)
        y1 = min(seq_data.shape[1], sy + roi_half)

        roi = seq_data[x0:x1, y0:y1, sz].T
        ax_zoom.imshow(roi, cmap='gray', origin='lower', aspect='equal')

        # Show tissue ROI center (green) and original wall position (red)
        tcx = sx - x0
        tcy = sy - y0
        wcx = int(wx) - x0
        wcy = int(wy) - y0
        ax_zoom.axhline(y=tcy, color='lime', linewidth=0.5, alpha=0.3, linestyle=':')
        ax_zoom.axvline(x=tcx, color='lime', linewidth=0.5, alpha=0.3, linestyle=':')
        ax_zoom.add_patch(Circle((tcx, tcy), radius=4, fill=False,
                                 edgecolor='lime', linewidth=1.5))  # tissue ROI
        ax_zoom.add_patch(Circle((wcx, wcy), radius=3, fill=False,
                                 edgecolor='red', linewidth=1, linestyle='--'))  # wall position

        # Measure signals at TISSUE position
        roi_signal = measure_roi_signal(seq_data, sx, sy, sz, radius=5)
        # Also measure at wall for comparison
        wall_signal = measure_roi_signal(seq_data, int(wx), int(wy), sz, radius=5)
        cortex_signal = measure_cortex_signal(seq_data, sz, seq_voxel)
        ratio = roi_signal / (cortex_signal + 1e-8)
        wall_ratio = wall_signal / (cortex_signal + 1e-8)

        xseq_results[seq_name] = {
            'mapped_tissue_pos': [sx, sy, sz],
            'mapped_wall_pos': [int(wx), int(wy), int(wz)],
            'tissue_signal': round(roi_signal, 4),
            'wall_signal': round(wall_signal, 4),
            'cortex_signal': round(cortex_signal, 4),
            'candidate_cortex_ratio': round(ratio, 3),
            'wall_cortex_ratio': round(wall_ratio, 3),
        }

        ratio_color = 'lime' if 0.7 <= ratio <= 1.3 else ('yellow' if 0.6 <= ratio <= 1.5 else 'red')
        slice_name = nifti_slice_to_dicom(sz, dicom_series) if seq_name == 'T2' else f"sl {sz}"

        corr_str = f" | align={local_corr:.2f}" if seq_name != 'T2' and local_corr > 0 else ""
        subtitle = (f"{seq_label} ({slice_name}){corr_str}\n"
                    f"Tissue/Cortex = {ratio:.2f}  (wall = {wall_ratio:.2f})")

        # Enhancement for T1_post
        if seq_name == 'T1_post' and 'T1_pre' in xseq_results:
            t1_pre_sig = xseq_results['T1_pre']['tissue_signal']
            enh = roi_signal / (t1_pre_sig + 1e-8)
            xseq_results['enhancement_ratio'] = round(enh, 3)
            subtitle += f"\nEnh = {enh:.2f}"
            enh_color = 'lime' if enh < 1.15 else ('yellow' if enh < 1.3 else 'red')
            ratio_color = enh_color

        ax_zoom.set_title(subtitle, color=ratio_color, fontsize=9)
        ax_zoom.axis('off')

        # -- Bottom row: Full slice for alignment verification --
        ax_full = axes[1, col]
        cx_img = seq_data.shape[0] // 2
        cy_img = seq_data.shape[1] // 2
        half_view = 140
        full_roi = seq_data[max(0, cx_img-half_view):cx_img+half_view,
                            max(0, cy_img-half_view):cy_img+half_view, sz].T
        ax_full.imshow(full_roi, cmap='gray', origin='lower', aspect='equal')

        cand_x = sx - max(0, cx_img - half_view)
        cand_y = sy - max(0, cy_img - half_view)
        ax_full.add_patch(Circle((cand_x, cand_y), radius=5, fill=False,
                                 edgecolor='lime', linewidth=1.5))

        if seq_name != 'T2':
            offset_label = f"Z:{z_off:+.0f}mm  XY:({xy_off[0]:+.1f},{xy_off[1]:+.1f})px"
        else:
            offset_label = "Reference"
        ax_full.set_title(
            f"Alignment check - sl {sz}\n{offset_label}",
            color='cyan', fontsize=9
        )
        ax_full.axis('off')

    plt.tight_layout()
    out_path = os.path.join(output_dir, f"xseq_candidate_{cand_idx + 1:02d}.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"    Saved: {os.path.basename(out_path)}")

    if 'enhancement_ratio' not in xseq_results:
        xseq_results['enhancement_ratio'] = None

    return xseq_results


def assess_cross_sequence(candidate, cand_idx, xseq_results):
    """Generate cross-sequence verdict using tissue-shifted ROI measurements.

    Uses the tissue-side ROI (shifted 4px from wall into parenchyma) for
    all ratio calculations. Also reports wall-position ratios for reference.

    Criteria: a candidate that is real tissue rather than a segmentation
    artifact should show tissue-like (not CSF-like) signal against the
    cortical reference across T2/FLAIR/T1, no post-contrast enhancement,
    and no susceptibility blooming on SWI.
    """
    issues = []
    strengths = []
    notes = []

    # T2: tissue-side ratio should be closer to 1.0 than wall ratio
    t2_r = xseq_results['T2']['candidate_cortex_ratio']
    t2_wall = xseq_results['T2'].get('wall_cortex_ratio', t2_r)
    if 0.7 <= t2_r <= 1.4:
        strengths.append(f"T2: isointense to cortex (tissue ratio {t2_r:.2f})")
    elif 0.5 <= t2_r <= 1.6:
        notes.append(f"T2: near-isointense (tissue={t2_r:.2f}, wall={t2_wall:.2f}) - residual partial volume")
        strengths.append(f"T2: near-isointense tissue signal ({t2_r:.2f})")
    else:
        issues.append(f"T2: discordant signal (tissue={t2_r:.2f}, wall={t2_wall:.2f})")

    # FLAIR: tissue side should be GM-like (ratio ~1.0), not dark like CSF
    flair_r = xseq_results['FLAIR']['candidate_cortex_ratio']
    flair_wall = xseq_results['FLAIR'].get('wall_cortex_ratio', flair_r)
    if 0.5 <= flair_r <= 1.5:
        strengths.append(f"FLAIR: tissue isointense to cortex ({flair_r:.2f})")
    elif flair_r < 0.3:
        issues.append(f"FLAIR: tissue very dark ({flair_r:.2f}) - CSF-like even at tissue position")
    else:
        issues.append(f"FLAIR: discordant tissue signal ({flair_r:.2f}, wall={flair_wall:.2f})")

    # T1 pre-contrast: candidate should be near-isointense to cortex
    t1_r = xseq_results['T1_pre']['candidate_cortex_ratio']
    if 0.6 <= t1_r <= 1.4:
        strengths.append(f"T1 pre: isointense to cortex ({t1_r:.2f})")
    elif t1_r > 1.4:
        issues.append(f"T1 pre: brighter than cortex ({t1_r:.2f})")
    else:
        issues.append(f"T1 pre: darker than cortex ({t1_r:.2f}) - not gray-matter-like")

    # Enhancement: gray-matter-isointense tissue should NOT enhance
    enh = xseq_results.get('enhancement_ratio')
    if enh is not None:
        if enh < 1.15:
            strengths.append(f"No gadolinium enhancement ({enh:.2f}) - meets no-enhancement criterion")
        elif enh < 1.3:
            notes.append(f"Borderline enhancement ({enh:.2f}) - could be partial volume or normal variation")
        else:
            issues.append(f"Significant enhancement ({enh:.2f}) - fails no-enhancement criterion")

    # SWI: no blooming
    swan_r = xseq_results['SWAN']['candidate_cortex_ratio']
    if swan_r > 0.5:
        strengths.append(f"SWI: no susceptibility blooming ({swan_r:.2f})")
    else:
        issues.append(f"SWI: dark signal ({swan_r:.2f}) - possible blooming")

    # Overall verdict
    n_s = len(strengths)
    n_i = len(issues)
    if n_s >= 4:
        verdict = "CONFIRMED - concordant across sequences"
    elif n_s >= 3 and n_i <= 1:
        verdict = "LIKELY - mostly concordant"
    elif n_i >= 3:
        verdict = "REJECTED - discordant signal across sequences"
    else:
        verdict = "UNCERTAIN - mixed cross-sequence evidence"

    return {
        'candidate_num': cand_idx + 1,
        'side': candidate['side'],
        'region': candidate['region'],
        'slices': candidate['slices'],
        'strengths': strengths,
        'issues': issues,
        'notes': notes,
        'cross_seq_verdict': verdict,
        'sequence_ratios': {
            'T2_tissue': t2_r,
            'T2_wall': t2_wall,
            'FLAIR_tissue': flair_r,
            'FLAIR_wall': flair_wall,
            'T1_pre': t1_r,
            'T1_post_enhancement': enh,
            'SWI': swan_r,
        }
    }


def generate_cross_sequence_summary(candidates, volumes, voxels, t2_voxel,
                                    z_offsets, xy_offsets, vent_mask, assessments,
                                    output_dir):
    """Generate summary grid using tissue-shifted positions with XY+Z alignment."""
    n_cands = len(candidates)
    seq_order = ['T2', 'FLAIR', 'T1_pre', 'T1_post', 'SWAN']
    seq_labels = ['T2', 'FLAIR', 'T1 Pre', 'T1 Post-Gad', 'SWI/SWAN']
    roi_half = 25

    fig, axes = plt.subplots(n_cands, 5, figsize=(25, 5 * n_cands))
    if n_cands == 1:
        axes = axes.reshape(1, -1)

    fig.suptitle(
        "Cross-Sequence Validation Summary (XY+Z aligned, tissue-shifted ROI)",
        fontsize=16, fontweight='bold', color='white'
    )

    for row, (cand, assess) in enumerate(zip(candidates, assessments)):
        pos = cand['position']
        mid_slice = cand['slices'][len(cand['slices']) // 2]

        # Tissue-shifted position
        tissue_x, tissue_y = compute_tissue_position(
            pos[0], pos[1], mid_slice, vent_mask, shift=4
        )

        for col, (seq_name, seq_label) in enumerate(zip(seq_order, seq_labels)):
            ax = axes[row, col]
            seq_data = volumes[seq_name]
            seq_voxel = voxels[seq_name]
            z_off = z_offsets[seq_name]
            xy_off = xy_offsets.get(seq_name, (0.0, 0.0))

            sx, sy, sz = map_t2_to_sequence(
                tissue_x, tissue_y, mid_slice, t2_voxel, seq_voxel, z_off,
                seq_data.shape, xy_off
            )

            # Local fine-tuning via edge-based alignment
            if seq_name != 'T2':
                sx, sy, _ = local_edge_alignment(
                    volumes['T2'][:, :, mid_slice], seq_data[:, :, sz],
                    sx, sy, patch_half=20, search_radius=12
                )

            x0 = max(0, sx - roi_half)
            x1 = min(seq_data.shape[0], sx + roi_half)
            y0 = max(0, sy - roi_half)
            y1 = min(seq_data.shape[1], sy + roi_half)

            roi = seq_data[x0:x1, y0:y1, sz].T
            ax.imshow(roi, cmap='gray', origin='lower', aspect='equal')

            cx, cy = sx - x0, sy - y0
            ax.add_patch(Circle((cx, cy), radius=3, fill=False,
                                edgecolor='lime', linewidth=1.5))
            ax.set_xlim(0, x1 - x0)
            ax.set_ylim(0, y1 - y0)

            if col == 0:
                verdict = assess['cross_seq_verdict'].split('-')[0].strip()
                v_color = ('lime' if 'CONFIRMED' in verdict
                           else ('yellow' if 'LIKELY' in verdict
                                 else ('orange' if 'UNCERTAIN' in verdict else 'red')))
                ax.set_ylabel(
                    f"#{row+1} {cand['side']} {cand['region']}\n{verdict}",
                    color=v_color, fontsize=10, fontweight='bold'
                )
            if row == 0:
                ax.set_title(f"{seq_label}\n(off={z_offsets[seq_name]:+.0f}mm)",
                             color='white', fontsize=11, fontweight='bold')
            ax.set_xticks([])
            ax.set_yticks([])

    plt.tight_layout()
    out_path = os.path.join(output_dir, "cross_sequence_summary.png")
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()
    print(f"  Cross-seq summary saved: {os.path.basename(out_path)}")


# -- Main --------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate nodule candidates across multiple MRI sequences.")
    parser.add_argument('--data-dir', required=True,
                        help="Directory containing the NIfTI sequence files (see SEQUENCE_FILES)")
    parser.add_argument('--candidates', required=True,
                        help="Candidate JSON from ventricle_3d_analysis.py")
    parser.add_argument('--timepoint', default='followup', choices=['baseline', 'followup'],
                        help="Which timepoint's candidates to validate (default: followup)")
    parser.add_argument('--dicom-series', default='SER000XX',
                        help="Source DICOM series folder name for slice labels (default: SER000XX)")
    parser.add_argument('--output-dir', required=True,
                        help="Output directory for panels and JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    sequences = {name: os.path.join(args.data_dir, fname)
                 for name, fname in SEQUENCE_FILES.items()}

    print("=" * 70)
    print("Cross-Sequence Candidate Validation")
    print("  - Main ventricle wall contours only")
    print("  - DICOM filenames on slice labels")
    print("  - Brain-area cross-correlation Z-alignment")
    print("  - Centroid XY offsets + edge-based local fine-tuning")
    print("=" * 70)

    # Load candidates
    with open(args.candidates) as f:
        results = json.load(f)
    candidates = results[args.timepoint]['persistent_candidates']
    print(f"\n{len(candidates)} candidates to validate ({args.timepoint})")

    # Load T2
    print("\n[1/5] Loading T2 volume...")
    t2_data, t2_voxel = load_and_normalize(sequences['T2'], "T2")

    # Segment ventricles
    print("\n[2/5] Segmenting ventricles...")
    vent_mask = segment_ventricles(t2_data, t2_voxel)
    vol = np.sum(vent_mask) * np.prod(t2_voxel)
    print(f"  Ventricle volume: {vol:.0f} mm^3")

    # Generate validation panels
    print("\n[3/5] Generating validation panels...")
    for i, cand in enumerate(candidates):
        print(f"\n  Candidate #{i + 1}: {cand['side']} {cand['region']}, "
              f"slices {cand['slices']}")
        generate_candidate_validation_panel(
            t2_data, vent_mask, cand, i, args.dicom_series, output_dir
        )

    generate_validation_summary(candidates, t2_data, vent_mask, args.dicom_series, output_dir)

    # Load all sequences for cross-validation
    print("\n[4/5] Loading MRI sequences and computing Z-alignment...")
    volumes = {}
    voxels = {}
    z_offsets = {'T2': 0.0}

    for name, path in sequences.items():
        if os.path.exists(path):
            data, voxel = load_and_normalize(path, name)
            volumes[name] = data
            voxels[name] = voxel

            if name != 'T2':
                offset, corr = find_z_offset(t2_data, t2_voxel, data, voxel)
                z_offsets[name] = offset
                print(f"    Z-offset: {offset:+.1f}mm (corr={corr:.3f})")
        else:
            print(f"  WARNING: {name} not found at {path}")

    # Compute in-plane XY offsets
    print("\n  Computing in-plane XY offsets (brain centroid matching)...")
    xy_offsets = compute_xy_offsets(t2_data, t2_voxel, volumes, voxels, z_offsets)
    for name, (dx, dy) in xy_offsets.items():
        if name != 'T2':
            print(f"    {name}: dx={dx:+.1f}, dy={dy:+.1f} voxels "
                  f"({dx*t2_voxel[0]:+.1f}, {dy*t2_voxel[1]:+.1f} mm)")

    # Cross-sequence validation
    print("\n[5/5] Cross-sequence validation with XY+Z aligned positions...")
    xseq_assessments = []
    for i, cand in enumerate(candidates):
        print(f"\n  Candidate #{i+1}: {cand['side']} {cand['region']}, "
              f"slices {cand['slices']}")

        xseq = generate_cross_sequence_panel(
            cand, i, volumes, voxels, t2_voxel, z_offsets, xy_offsets,
            vent_mask, args.dicom_series, output_dir
        )

        assessment = assess_cross_sequence(cand, i, xseq)
        xseq_assessments.append(assessment)

        print(f"    Cross-seq verdict: {assessment['cross_seq_verdict']}")
        for s in assessment['strengths']:
            print(f"      + {s}")
        for issue in assessment['issues']:
            print(f"      - {issue}")

    # Generate cross-seq summary
    generate_cross_sequence_summary(
        candidates, volumes, voxels, t2_voxel, z_offsets, xy_offsets, vent_mask,
        xseq_assessments, output_dir
    )

    # Save results
    out_json = os.path.join(output_dir, "cross_sequence_validation.json")
    save_data = {
        'z_offsets_mm': z_offsets,
        'xy_offsets_voxels': {k: list(v) for k, v in xy_offsets.items()},
        'alignment_method': 'brain_centroid_XY + brain_area_cross_correlation_Z + local_edge_NCC',
        'candidates': xseq_assessments,
    }
    with open(out_json, 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"\n  Saved: {os.path.basename(out_json)}")

    # Summary
    print(f"\n{'=' * 70}")
    print("CROSS-SEQUENCE VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Z-offsets: {z_offsets}")
    confirmed = sum(1 for a in xseq_assessments if 'CONFIRMED' in a['cross_seq_verdict'])
    likely = sum(1 for a in xseq_assessments if a['cross_seq_verdict'].startswith('LIKELY'))
    uncertain = sum(1 for a in xseq_assessments if 'UNCERTAIN' in a['cross_seq_verdict'])
    rejected = sum(1 for a in xseq_assessments if 'REJECTED' in a['cross_seq_verdict'])
    print(f"  CONFIRMED:  {confirmed}/{len(xseq_assessments)}")
    print(f"  LIKELY:     {likely}/{len(xseq_assessments)}")
    print(f"  UNCERTAIN:  {uncertain}/{len(xseq_assessments)}")
    print(f"  REJECTED:   {rejected}/{len(xseq_assessments)}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
