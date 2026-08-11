#!/usr/bin/env python3
"""
Ventricle 3D Analysis
=====================
Shape-based detection of nodular protrusions along the lateral ventricle
walls, with an interactive 3D reconstruction.

Pipeline:
1. Loads baseline and follow-up T2 volumes from NIfTI
2. Segments the lateral ventricles using multi-Otsu thresholding inside an
   eroded brain mask, with spatial constraints and a volume sanity check
3. Fits B-splines to ventricular wall contours per slice and computes
   signed curvature analytically from the spline derivatives
4. Detects nodule candidates as curvature peaks with calibrated
   prominence/height thresholds, grouped by cross-slice persistence
5. Generates annotated inspection montages per timepoint
6. Reconstructs ventricle and brain-surface meshes with marching cubes and
   renders an interactive Plotly 3D HTML with toggleable timepoint layers

Design note: detection is shape-based (wall curvature) rather than
intensity-based because gray-white intensity contrast was unreliable in
the dataset this was developed on. Curvature only depends on the wall
geometry, not on which tissue is bright.

Usage:
    python ventricle_3d_analysis.py \
        --baseline PATH/TO/baseline_T2.nii.gz \
        --followup PATH/TO/followup_T2.nii.gz \
        --output-dir PATH/TO/output_dir
"""

import argparse
import nibabel as nib
import numpy as np
from scipy import ndimage, interpolate, signal
from skimage import measure, morphology, filters
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import plotly.graph_objects as go
import json
import os


def load_and_normalize(path, label=""):
    """Load NIfTI and normalize to 0-1 range."""
    print(f"  Loading {label}: {os.path.basename(path)}")
    img = nib.load(path)
    data = img.get_fdata().astype(np.float32)
    voxel = img.header.get_zooms()[:3]
    # Normalize
    p1, p99 = np.percentile(data[data > 0], [1, 99])
    data = np.clip((data - p1) / (p99 - p1 + 1e-8), 0, 1)
    return data, voxel, img.affine


def segment_ventricles(data, voxel_size):
    """Segment lateral ventricles using brain masking + multi-Otsu + spatial constraints.

    Strategy:
    1. Create a brain mask by thresholding away background
    2. Erode brain mask to exclude subarachnoid CSF and surface
    3. Apply multi-Otsu within the eroded brain to find CSF
    4. Keep only central components (ventricles)
    5. Restrict to the middle slice range (ventricles don't extend to top/bottom)
    """
    # Step 1: Brain mask (tissue > low threshold)
    brain_mask = data > 0.05
    brain_mask = morphology.binary_closing(brain_mask, morphology.ball(3))
    brain_mask = ndimage.binary_fill_holes(brain_mask)

    # Step 2: Erode to exclude cortical surface and subarachnoid CSF
    # Erosion depth is computed in physical units (~8mm from surface)
    erode_voxels = max(3, int(8.0 / min(voxel_size[:2])))
    brain_interior = morphology.binary_erosion(brain_mask, morphology.ball(erode_voxels))

    # Step 3: Multi-Otsu within brain interior only
    interior_data = data[brain_interior]
    if len(interior_data) < 100:
        return np.zeros_like(brain_mask)

    thresholds = filters.threshold_multiotsu(interior_data[interior_data > 0.01], classes=4)
    csf_mask = (data > thresholds[-1]) & brain_interior

    # Step 4: Morphological cleanup
    csf_mask = morphology.binary_opening(csf_mask, morphology.ball(1))
    csf_mask = morphology.binary_closing(csf_mask, morphology.ball(1))

    # Step 5: Restrict to middle slice range (ventricles sit in ~30-75% of brain height)
    z_nonzero = np.where(np.any(brain_mask, axis=(0, 1)))[0]
    if len(z_nonzero) > 0:
        z_min, z_max = z_nonzero[0], z_nonzero[-1]
        z_brain_range = z_max - z_min
        z_vent_low = z_min + int(0.30 * z_brain_range)
        z_vent_high = z_min + int(0.75 * z_brain_range)
        csf_mask[:, :, :z_vent_low] = False
        csf_mask[:, :, z_vent_high:] = False

    # Step 6: Connected components - keep only the largest central components
    labeled = measure.label(csf_mask)
    regions = measure.regionprops(labeled)

    if not regions:
        return csf_mask

    center = np.array(data.shape) / 2
    ventricle_mask = np.zeros_like(csf_mask)

    # Score regions by centrality and size
    scored = []
    for region in regions:
        centroid = np.array(region.centroid)
        dist_xy = np.linalg.norm(centroid[:2] - center[:2])
        # Ventricles must be near center
        max_dist = center[0] * 0.25
        if dist_xy < max_dist and region.area > 100:
            # Score = area / (1 + distance_from_center)
            score = region.area / (1 + dist_xy)
            scored.append((score, region.label))

    # Keep the top 1-2 components (left and right ventricles may be separate)
    scored.sort(reverse=True)
    for score, label_id in scored[:2]:
        ventricle_mask[labeled == label_id] = True

    # Final volume sanity check: > 25 mL is likely over-segmentation
    vol_mm3 = np.sum(ventricle_mask) * np.prod(voxel_size)
    if vol_mm3 > 25000:
        # Apply additional erosion
        ventricle_mask = morphology.binary_erosion(ventricle_mask, morphology.ball(2))
        vol_mm3 = np.sum(ventricle_mask) * np.prod(voxel_size)
        print(f"    Volume after correction: {vol_mm3:.0f} mm^3")

    return ventricle_mask


def extract_ventricular_contours(ventricle_mask_2d):
    """Extract ventricular wall contours from a 2D slice."""
    contours = measure.find_contours(ventricle_mask_2d.astype(float), 0.5)
    # Filter to meaningful contours (not tiny fragments)
    contours = [c for c in contours if len(c) > 20]
    return contours


def compute_curvature_bspline(contour, smoothing=25.0):
    """Fit B-spline to contour and compute signed curvature."""
    if len(contour) < 10:
        return np.zeros(len(contour)), contour

    # Parameterize by arc length
    diffs = np.diff(contour, axis=0)
    ds = np.sqrt(np.sum(diffs**2, axis=1))
    s = np.concatenate([[0], np.cumsum(ds)])
    s_norm = s / s[-1]

    try:
        # Fit B-splines
        tck_x, _ = interpolate.splprep([contour[:, 0]], u=s_norm, s=smoothing, k=3)
        tck_y, _ = interpolate.splprep([contour[:, 1]], u=s_norm, s=smoothing, k=3)

        # Evaluate at fine resolution
        u_fine = np.linspace(0, 1, len(contour))
        x_smooth = interpolate.splev(u_fine, tck_x)[0]
        y_smooth = interpolate.splev(u_fine, tck_y)[0]

        # First and second derivatives
        dx = interpolate.splev(u_fine, tck_x, der=1)[0]
        dy = interpolate.splev(u_fine, tck_y, der=1)[0]
        ddx = interpolate.splev(u_fine, tck_x, der=2)[0]
        ddy = interpolate.splev(u_fine, tck_y, der=2)[0]

        # Signed curvature: kappa = (x'y'' - y'x'') / (x'^2 + y'^2)^(3/2)
        numerator = dx * ddy - dy * ddx
        denominator = (dx**2 + dy**2)**1.5 + 1e-10
        curvature = numerator / denominator

        smooth_contour = np.column_stack([x_smooth, y_smooth])
        return curvature, smooth_contour

    except Exception:
        return np.zeros(len(contour)), contour


def detect_nodule_candidates(curvature, contour, min_prominence=0.05):
    """Detect nodule candidates from curvature peaks.

    Thresholds calibrated iteratively to cut false positives from normal
    wall undulations:
    - prominence >= 0.05 (was 0.02 - flagged too many normal wall bumps)
    - height >= 0.15 (was 0.05 - true nodules show strong curvature)
    - distance >= 10 (was 5 - prevents double-counting single bumps)
    """
    abs_curv = np.abs(curvature)
    peaks, properties = signal.find_peaks(
        abs_curv,
        prominence=min_prominence,
        distance=10,
        height=0.15
    )

    candidates = []
    for i, peak_idx in enumerate(peaks):
        candidates.append({
            'position': contour[peak_idx].tolist(),
            'curvature': float(abs_curv[peak_idx]),
            'prominence': float(properties['prominences'][i]),
            'contour_index': int(peak_idx),
        })

    return candidates


def classify_anterior_posterior(candidate, image_center_y):
    """Classify a candidate as anterior or posterior based on position."""
    y = candidate['position'][1]
    return 'anterior' if y < image_center_y else 'posterior'


def analyze_single_volume(data, voxel_size, label):
    """Run the full candidate analysis on a single volume."""
    print(f"\n{'='*60}")
    print(f"Analyzing: {label}")
    print(f"Volume shape: {data.shape}, Voxel: {voxel_size}")
    print(f"{'='*60}")

    # Segment ventricles
    print("  Segmenting ventricles...")
    vent_mask = segment_ventricles(data, voxel_size)
    vent_volume_mm3 = np.sum(vent_mask) * np.prod(voxel_size)
    print(f"  Ventricle volume: {vent_volume_mm3:.0f} mm^3")

    # Analyze ventricular-level slices
    z_range = np.where(np.any(vent_mask, axis=(0, 1)))[0]
    if len(z_range) == 0:
        print("  WARNING: No ventricles detected!")
        return None, None

    print(f"  Ventricular slices: {z_range[0]}-{z_range[-1]} ({len(z_range)} slices)")

    all_candidates = []
    slice_results = []

    for z in z_range:
        mask_slice = vent_mask[:, :, z]

        contours = extract_ventricular_contours(mask_slice)
        slice_candidates = []

        for contour in contours:
            curvature, smooth_contour = compute_curvature_bspline(contour, smoothing=25.0)
            candidates = detect_nodule_candidates(curvature, smooth_contour)

            for cand in candidates:
                cand['slice'] = int(z)
                cand['side'] = 'left' if cand['position'][1] > data.shape[1] / 2 else 'right'
                cand['region'] = classify_anterior_posterior(cand, data.shape[0] / 2)
                slice_candidates.append(cand)

        slice_results.append({
            'slice': int(z),
            'contour_count': len(contours),
            'candidate_count': len(slice_candidates),
            'candidates': slice_candidates,
        })
        all_candidates.extend(slice_candidates)

    print(f"  Total raw candidates: {len(all_candidates)}")

    # Group by persistence (candidates at similar positions across slices)
    persistent = group_persistent_candidates(all_candidates, tolerance=10)

    # Final filter: keep only top candidates by combined score
    # (span * mean_curvature) - mimics a reader focusing on the most obvious nodules
    for p in persistent:
        p['score'] = p['span'] * p['mean_curvature']
    persistent.sort(key=lambda x: x['score'], reverse=True)
    # Keep top 10 at most
    persistent = persistent[:10]
    print(f"  Persistent candidates (multi-slice, top-10): {len(persistent)}")

    return {
        'label': label,
        'shape': list(data.shape),
        'voxel_size': list(voxel_size),
        'ventricle_volume_mm3': float(vent_volume_mm3),
        'slice_range': [int(z_range[0]), int(z_range[-1])],
        'total_candidates': len(all_candidates),
        'persistent_candidates': persistent,
        'slice_results': slice_results,
    }, vent_mask


def group_persistent_candidates(candidates, tolerance=15):
    """Group candidates that appear at similar positions across consecutive slices."""
    if not candidates:
        return []

    # Sort by slice
    sorted_cands = sorted(candidates, key=lambda c: c['slice'])
    groups = []
    used = set()

    for i, cand in enumerate(sorted_cands):
        if i in used:
            continue
        group = [cand]
        used.add(i)

        for j, other in enumerate(sorted_cands):
            if j in used:
                continue
            # Check spatial proximity and slice adjacency
            pos_dist = np.linalg.norm(
                np.array(cand['position']) - np.array(other['position'])
            )
            slice_dist = abs(cand['slice'] - other['slice'])

            if pos_dist < tolerance and slice_dist <= 3:
                group.append(other)
                used.add(j)

        if len(group) >= 2:  # Persistent = appears in 2+ slices
            avg_pos = np.mean([c['position'] for c in group], axis=0).tolist()
            avg_curv = float(np.mean([c['curvature'] for c in group]))
            slices = sorted(set(c['slice'] for c in group))
            groups.append({
                'position': avg_pos,
                'mean_curvature': avg_curv,
                'max_curvature': float(max(c['curvature'] for c in group)),
                'slices': slices,
                'span': len(slices),
                'side': group[0]['side'],
                'region': group[0]['region'],
                'confidence': 'high' if len(slices) >= 3 else 'moderate',
            })

    return sorted(groups, key=lambda g: g['span'], reverse=True)


def generate_inspection_montage(data, vent_mask, results, output_path, title):
    """Generate annotated montage of candidate slices."""
    print(f"  Generating montage: {os.path.basename(output_path)}")

    slice_range = results['slice_range']
    # Select representative slices (evenly spaced through ventricles)
    n_slices = min(16, slice_range[1] - slice_range[0] + 1)
    selected_slices = np.linspace(slice_range[0], slice_range[1], n_slices, dtype=int)

    ncols = 4
    nrows = (n_slices + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(20, 5 * nrows))
    axes = axes.flatten()
    fig.suptitle(title, fontsize=16, fontweight='bold')

    # Collect all candidates for quick lookup
    cand_by_slice = {}
    for sr in results['slice_results']:
        if sr['candidates']:
            cand_by_slice[sr['slice']] = sr['candidates']

    for idx, z in enumerate(selected_slices):
        ax = axes[idx]
        ax.imshow(data[:, :, z].T, cmap='gray', origin='lower', aspect='equal')

        # Overlay ventricle contours in cyan
        contours = extract_ventricular_contours(vent_mask[:, :, z])
        for contour in contours:
            ax.plot(contour[:, 0], contour[:, 1], 'c-', linewidth=0.8, alpha=0.7)

        # Mark candidates with red circles (only top 3 per slice by curvature)
        if z in cand_by_slice:
            top_cands = sorted(cand_by_slice[z], key=lambda c: c['curvature'], reverse=True)[:3]
            for cand in top_cands:
                pos = cand['position']
                ax.add_patch(Circle(
                    (pos[0], pos[1]), radius=5,
                    fill=False, edgecolor='red', linewidth=1.5
                ))
                ax.annotate(
                    f"k={cand['curvature']:.2f}",
                    (pos[0] + 7, pos[1] + 7),
                    color='yellow', fontsize=6,
                    bbox=dict(boxstyle='round,pad=0.1', fc='black', alpha=0.6)
                )

        # Check if this slice has persistent candidates
        cand_flag = ""
        for pc in results['persistent_candidates']:
            if z in pc['slices']:
                cand_flag = " *cand"
                break

        ax.set_title(f"Slice {z}{cand_flag}", fontsize=10,
                     color='red' if cand_flag else 'white')
        ax.axis('off')

    # Hide unused axes
    for idx in range(len(selected_slices), len(axes)):
        axes[idx].axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()


def generate_comparison_montage(baseline_data, followup_data, baseline_mask, followup_mask,
                                baseline_results, followup_results, output_path):
    """Generate side-by-side comparison of both timepoints at matched ventricular levels."""
    print("  Generating baseline/follow-up comparison montage...")

    # Find overlapping ventricular level range (percentage-based matching)
    base_range = baseline_results['slice_range']
    followup_range = followup_results['slice_range']

    # Use 6 matched levels
    n_levels = 6
    fracs = np.linspace(0.15, 0.85, n_levels)

    fig, axes = plt.subplots(n_levels, 2, figsize=(12, 4 * n_levels))
    fig.suptitle("Candidate Inspection: Baseline vs Follow-up (Matched Ventricular Levels)",
                 fontsize=14, fontweight='bold', color='white')

    for i, frac in enumerate(fracs):
        base_z = int(base_range[0] + frac * (base_range[1] - base_range[0]))
        followup_z = int(followup_range[0] + frac * (followup_range[1] - followup_range[0]))

        # Baseline
        ax_base = axes[i, 0]
        ax_base.imshow(baseline_data[:, :, base_z].T, cmap='gray', origin='lower')
        contours = extract_ventricular_contours(baseline_mask[:, :, base_z])
        for c in contours:
            ax_base.plot(c[:, 0], c[:, 1], 'c-', linewidth=0.8, alpha=0.5)
        # Mark top candidates only
        for sr in baseline_results['slice_results']:
            if sr['slice'] == base_z:
                top = sorted(sr['candidates'], key=lambda c: c['curvature'], reverse=True)[:3]
                for cand in top:
                    ax_base.add_patch(Circle(
                        (cand['position'][0], cand['position'][1]),
                        radius=5, fill=False, edgecolor='red', linewidth=1.5
                    ))
        ax_base.set_title(f"Baseline - Slice {base_z} ({frac*100:.0f}%)", color='white', fontsize=10)
        ax_base.axis('off')

        # Follow-up
        ax_followup = axes[i, 1]
        ax_followup.imshow(followup_data[:, :, followup_z].T, cmap='gray', origin='lower')
        contours = extract_ventricular_contours(followup_mask[:, :, followup_z])
        for c in contours:
            ax_followup.plot(c[:, 0], c[:, 1], 'c-', linewidth=0.8, alpha=0.5)
        for sr in followup_results['slice_results']:
            if sr['slice'] == followup_z:
                top = sorted(sr['candidates'], key=lambda c: c['curvature'], reverse=True)[:3]
                for cand in top:
                    ax_followup.add_patch(Circle(
                        (cand['position'][0], cand['position'][1]),
                        radius=5, fill=False, edgecolor='red', linewidth=1.5
                    ))
        ax_followup.set_title(f"Follow-up - Slice {followup_z} ({frac*100:.0f}%)", color='white', fontsize=10)
        ax_followup.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close()


def build_3d_ventricle_mesh(vent_mask, voxel_size, label):
    """Build 3D mesh of ventricles using marching cubes."""
    print(f"  Building 3D mesh: {label}...")

    # Smooth the mask slightly for better mesh quality
    smooth_mask = ndimage.gaussian_filter(vent_mask.astype(float), sigma=1.0)

    try:
        verts, faces, normals, values = measure.marching_cubes(
            smooth_mask, level=0.5, spacing=voxel_size
        )
    except Exception as e:
        print(f"    WARNING: Marching cubes failed: {e}")
        return None, None, None

    print(f"    Mesh: {len(verts)} vertices, {len(faces)} faces")
    return verts, faces, normals


def build_brain_surface_mesh(data, voxel_size, label):
    """Build 3D mesh of outer brain surface for anatomical context.

    Uses volume downsampling before marching cubes to produce a
    topologically complete mesh at manageable size, rather than
    post-hoc face skipping which creates holes.
    """
    print(f"  Building brain surface: {label}...")

    # Brain mask: tissue above low threshold
    brain_mask = data > 0.08
    brain_mask = morphology.binary_closing(brain_mask, morphology.ball(3))
    brain_mask = ndimage.binary_fill_holes(brain_mask)

    # Downsample volume by factor of 2 to reduce mesh complexity
    # This produces ~4x fewer faces while keeping topology intact
    ds = 2
    downsampled = brain_mask[::ds, ::ds, ::ds]
    adjusted_voxel = tuple(v * ds for v in voxel_size)

    # Smooth for cleaner surface
    smooth_brain = ndimage.gaussian_filter(downsampled.astype(float), sigma=1.5)

    try:
        verts, faces, normals, values = measure.marching_cubes(
            smooth_brain, level=0.5, spacing=adjusted_voxel
        )
    except Exception as e:
        print(f"    WARNING: Brain surface extraction failed: {e}")
        return None, None

    # Further reduce if still too large
    if len(faces) > 40000:
        step = max(1, len(faces) // 40000)
        faces = faces[::step]
        used_verts = np.unique(faces)
        vert_map = np.full(len(verts), -1, dtype=int)
        vert_map[used_verts] = np.arange(len(used_verts))
        verts = verts[used_verts]
        faces = vert_map[faces]

    print(f"    Brain surface: {len(verts)} vertices, {len(faces)} faces")
    return verts, faces


def extract_mesh_wireframe(verts, faces, step=2):
    """Extract mesh edges for wireframe rendering as Scatter3d lines.

    Returns x, y, z arrays with None separators for Plotly line segments.
    'step' controls edge density (higher = fewer edges = lighter render).
    """
    edges = set()
    for face in faces[::step]:
        for i in range(3):
            edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
            edges.add(edge)

    x_lines, y_lines, z_lines = [], [], []
    for v1, v2 in edges:
        x_lines.extend([verts[v1, 0], verts[v2, 0], None])
        y_lines.extend([verts[v1, 1], verts[v2, 1], None])
        z_lines.extend([verts[v1, 2], verts[v2, 2], None])

    return x_lines, y_lines, z_lines


def generate_3d_html(baseline_verts, baseline_faces, followup_verts, followup_faces,
                     baseline_candidates, followup_candidates,
                     baseline_voxel, followup_voxel, output_path,
                     brain_verts=None, brain_faces=None):
    """Generate interactive 3D HTML visualization using Plotly.

    Includes:
    - Transparent brain surface for anatomical context
    - Ventricle meshes for both timepoints (toggleable)
    - Nodule candidate markers
    """
    print("  Generating interactive 3D HTML...")

    fig = go.Figure()

    # -- Brain surface (transparent outer shell for context) --
    if brain_verts is not None and brain_faces is not None:
        # Semi-transparent surface mesh
        fig.add_trace(go.Mesh3d(
            x=brain_verts[:, 0],
            y=brain_verts[:, 1],
            z=brain_verts[:, 2],
            i=brain_faces[:, 0],
            j=brain_faces[:, 1],
            k=brain_faces[:, 2],
            color='rgba(200, 210, 225, 0.18)',
            name='Brain Surface',
            opacity=0.18,
            hoverinfo='name',
            flatshading=True,
            lighting=dict(ambient=0.7, diffuse=0.6, specular=0.3, roughness=0.5),
            lightposition=dict(x=100, y=200, z=300),
        ))

        # Wireframe edge overlay for fine contour lines
        wx, wy, wz = extract_mesh_wireframe(brain_verts, brain_faces, step=3)
        fig.add_trace(go.Scatter3d(
            x=wx, y=wy, z=wz,
            mode='lines',
            line=dict(color='rgba(180, 200, 220, 0.25)', width=1),
            name='Brain Wireframe',
            hoverinfo='skip',
        ))

    # -- Baseline ventricle mesh --
    if baseline_verts is not None and baseline_faces is not None:
        fig.add_trace(go.Mesh3d(
            x=baseline_verts[:, 0], y=baseline_verts[:, 1], z=baseline_verts[:, 2],
            i=baseline_faces[:, 0], j=baseline_faces[:, 1], k=baseline_faces[:, 2],
            color='rgba(100, 180, 255, 0.3)',
            name='Baseline Ventricles',
            opacity=0.3,
            visible='legendonly',  # Hidden by default to reduce clutter
            hoverinfo='name',
        ))

    # -- Follow-up ventricle mesh --
    if followup_verts is not None and followup_faces is not None:
        fig.add_trace(go.Mesh3d(
            x=followup_verts[:, 0], y=followup_verts[:, 1], z=followup_verts[:, 2],
            i=followup_faces[:, 0], j=followup_faces[:, 1], k=followup_faces[:, 2],
            color='rgba(100, 255, 180, 0.4)',
            name='Follow-up Ventricles',
            opacity=0.4,
            hoverinfo='name',
        ))

    # -- Candidate markers (follow-up - primary) --
    if followup_candidates:
        for i, cand in enumerate(followup_candidates):
            pos = cand['position']
            # Convert 2D position + slice to 3D using voxel size
            slices = cand['slices']
            avg_z = np.mean(slices) * followup_voxel[2]
            x_mm = pos[0] * followup_voxel[0]
            y_mm = pos[1] * followup_voxel[1]

            color = 'red' if cand['confidence'] == 'high' else 'orange'
            fig.add_trace(go.Scatter3d(
                x=[x_mm], y=[y_mm], z=[avg_z],
                mode='markers+text',
                marker=dict(
                    size=10 + cand['span'] * 3,
                    color=color,
                    symbol='diamond',
                    opacity=0.9,
                    line=dict(width=2, color='white'),
                ),
                text=f"Candidate #{i+1}: {cand['side']} {cand['region']}",
                textposition='top center',
                textfont=dict(size=10, color=color),
                name=f"Candidate #{i+1} ({cand['side']} {cand['region']})",
                hovertext=(
                    f"Candidate #{i+1}<br>"
                    f"Side: {cand['side']}<br>"
                    f"Region: {cand['region']}<br>"
                    f"Slices: {cand['slices']}<br>"
                    f"Span: {cand['span']} slices<br>"
                    f"Mean Curvature: {cand['mean_curvature']:.3f}<br>"
                    f"Confidence: {cand['confidence']}"
                ),
                hoverinfo='text',
            ))

    # -- Candidate markers (baseline) --
    if baseline_candidates:
        for i, cand in enumerate(baseline_candidates):
            pos = cand['position']
            slices = cand['slices']
            avg_z = np.mean(slices) * baseline_voxel[2]
            x_mm = pos[0] * baseline_voxel[0]
            y_mm = pos[1] * baseline_voxel[1]

            fig.add_trace(go.Scatter3d(
                x=[x_mm], y=[y_mm], z=[avg_z],
                mode='markers',
                marker=dict(
                    size=8,
                    color='yellow',
                    symbol='circle',
                    opacity=0.7,
                    line=dict(width=1, color='white'),
                ),
                name=f"Baseline Candidate #{i+1} ({cand['side']} {cand['region']})",
                visible='legendonly',
                hovertext=(
                    f"Baseline Candidate #{i+1}<br>"
                    f"Side: {cand['side']}<br>"
                    f"Region: {cand['region']}<br>"
                    f"Slices: {cand['slices']}<br>"
                    f"Mean Curvature: {cand['mean_curvature']:.3f}"
                ),
                hoverinfo='text',
            ))

    # -- Layout --
    fig.update_layout(
        title=dict(
            text=(
                "3D Ventricle Reconstruction with Nodule Candidates<br>"
                "<sub>Red/Orange diamonds = curvature-detected candidates | "
                "Toggle layers in legend</sub>"
            ),
            font=dict(size=16),
        ),
        scene=dict(
            xaxis_title="Left <-> Right (mm)",
            yaxis_title="Posterior <-> Anterior (mm)",
            zaxis_title="Inferior <-> Superior (mm)",
            aspectmode='data',
            bgcolor='rgb(20, 20, 30)',
            xaxis=dict(backgroundcolor='rgb(20, 20, 30)', gridcolor='rgb(50, 50, 70)'),
            yaxis=dict(backgroundcolor='rgb(20, 20, 30)', gridcolor='rgb(50, 50, 70)'),
            zaxis=dict(backgroundcolor='rgb(20, 20, 30)', gridcolor='rgb(50, 50, 70)'),
        ),
        paper_bgcolor='rgb(10, 10, 20)',
        font=dict(color='white'),
        legend=dict(
            bgcolor='rgba(30, 30, 50, 0.8)',
            font=dict(color='white', size=11),
        ),
        width=1200,
        height=800,
    )

    fig.write_html(output_path, include_plotlyjs=True)
    print(f"    Saved: {output_path}")


def generate_summary_report(baseline_results, followup_results, output_path):
    """Generate a plain-markdown summary report of the analysis."""
    report = []
    report.append("# Ventricle 3D Analysis Report")
    report.append("")
    report.append("## Analysis Parameters")
    report.append("")
    report.append("| Parameter | Baseline | Follow-up |")
    report.append("|-----------|----------|-----------|")
    report.append(f"| Volume Shape | {baseline_results['shape']} | {followup_results['shape']} |")
    report.append(f"| Voxel Size (mm) | {[round(v,3) for v in baseline_results['voxel_size']]} | {[round(v,3) for v in followup_results['voxel_size']]} |")
    report.append(f"| Ventricle Volume | {baseline_results['ventricle_volume_mm3']:.0f} mm^3 | {followup_results['ventricle_volume_mm3']:.0f} mm^3 |")
    report.append(f"| Ventricular Slices | {baseline_results['slice_range']} | {followup_results['slice_range']} |")
    report.append(f"| Total Candidates | {baseline_results['total_candidates']} | {followup_results['total_candidates']} |")
    report.append(f"| Persistent (multi-slice) | {len(baseline_results['persistent_candidates'])} | {len(followup_results['persistent_candidates'])} |")
    report.append("")

    report.append("## Spatial Alignment Strategy")
    report.append("")
    report.append("The two scans may have different voxel sizes, FOV, and slice counts.")
    report.append("Alignment used percentage-based ventricular level matching:")
    report.append("- Identified the ventricular slice range in each volume independently")
    report.append("- Matched corresponding fractional positions (e.g., 15%, 30%, ... 85%)")
    report.append("- This accounts for different head positioning and FOV without rigid registration")
    report.append("")

    # Candidate tables
    for label, results in [("Follow-up", followup_results), ("Baseline", baseline_results)]:
        report.append(f"## Nodule Candidates - {label}")
        report.append("")
        if results['persistent_candidates']:
            report.append("| # | Side | Region | Slices | Span | Mean k | Max k | Confidence |")
            report.append("|---|------|--------|--------|------|--------|-------|------------|")
            for i, cand in enumerate(results['persistent_candidates'], 1):
                report.append(
                    f"| {i} | {cand['side']} | {cand['region']} | "
                    f"{cand['slices']} | {cand['span']} | "
                    f"{cand['mean_curvature']:.3f} | {cand['max_curvature']:.3f} | "
                    f"{cand['confidence']} |"
                )
        else:
            report.append("*No persistent (multi-slice) candidates detected.*")
        report.append("")

    # Temporal stability
    report.append("## Temporal Stability Assessment")
    report.append("")
    report.append("Stable anatomical structures should appear on both scans.")
    base_n = len(baseline_results['persistent_candidates'])
    followup_n = len(followup_results['persistent_candidates'])
    report.append(f"- Baseline persistent candidates: **{base_n}**")
    report.append(f"- Follow-up persistent candidates: **{followup_n}**")

    if base_n > 0 and followup_n > 0:
        report.append("- Candidates detected on BOTH timepoints - consistent with stable anatomy")
    elif followup_n > 0 and base_n == 0:
        report.append("- Candidates only on follow-up - may reflect better image quality or")
        report.append("  contrast on the follow-up scan rather than a true change")
    report.append("")

    report.append("## Generated Outputs")
    report.append("")
    report.append("| File | Description |")
    report.append("|------|-------------|")
    report.append("| `candidate_inspection_baseline.png` | Baseline montage with ventricular contours and candidates |")
    report.append("| `candidate_inspection_followup.png` | Follow-up montage with ventricular contours and candidates |")
    report.append("| `candidate_comparison_matched.png` | Side-by-side timepoints at matched ventricular levels |")
    report.append("| `ventricles_3d.html` | Interactive 3D Plotly visualization (open in browser) |")
    report.append("| `candidate_analysis_results.json` | Machine-readable analysis results |")
    report.append("")

    report.append("## Methodology")
    report.append("")
    report.append("### Ventricle Segmentation")
    report.append("- Multi-Otsu thresholding (4 classes) inside an eroded brain mask to isolate CSF")
    report.append("- Morphological opening/closing for cleanup")
    report.append("- Connected component analysis retaining central structures")
    report.append("- Volume plausibility check with corrective re-erosion")
    report.append("")
    report.append("### Candidate Detection")
    report.append("- B-spline contour fitting (smoothing s=25.0) of ventricular walls")
    report.append("- Signed curvature computed analytically from spline derivatives")
    report.append("- Peak detection (prominence >= 0.05, height >= 0.15, min distance 10)")
    report.append("- Cross-slice persistence grouping (10px Euclidean tolerance, <=3 slice gap)")
    report.append("- Anterior/posterior classification by contour position")
    report.append("")
    report.append("### 3D Reconstruction")
    report.append("- Marching cubes (scikit-image) on the smoothed ventricle mask")
    report.append("- Downsampled semi-transparent brain surface for context")
    report.append("- Plotly interactive mesh rendering with candidate markers")
    report.append("- Toggleable baseline vs follow-up layers")
    report.append("")
    report.append("### Spatial Matching")
    report.append("- Percentage-based slice matching through the ventricular range")
    report.append("- Accounts for different voxel sizes, FOV, and slice counts between scans")
    report.append("")

    report.append("## Limitations")
    report.append("")
    report.append("1. **No rigid/affine registration** - scanner coordinate frames were not preserved")
    report.append("2. **Low tissue contrast** - reduced gray-white contrast limits intensity-based checks")
    report.append("3. **CSF-based segmentation** - ventricle segmentation may include cisterns")
    report.append("4. **Interval growth** - anatomy can change between scans, complicating slice matching")
    report.append("5. **Smoothing tradeoff** - B-spline s=25 may smooth away small (<2mm) nodules")
    report.append("6. **Not diagnostic** - exploratory tooling only; does not replace radiology")
    report.append("")
    report.append("*Pipeline: ventricle_3d_analysis.py (nibabel + scikit-image + plotly)*")

    with open(output_path, 'w') as f:
        f.write('\n'.join(report))
    print(f"  Report saved: {os.path.basename(output_path)}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="3D ventricle segmentation and curvature-based nodule candidate detection.")
    parser.add_argument('--baseline', required=True,
                        help="Baseline T2 NIfTI volume (.nii.gz)")
    parser.add_argument('--followup', required=True,
                        help="Follow-up T2 NIfTI volume (.nii.gz)")
    parser.add_argument('--output-dir', required=True,
                        help="Output directory for montages, HTML, JSON, and report")
    return parser.parse_args()


# ======================================================================
# MAIN PIPELINE
# ======================================================================
def main():
    args = parse_args()
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("Ventricle 3D Analysis Pipeline")
    print("=" * 70)

    # -- Load T2 volumes --
    print("\n[1/7] Loading T2 volumes...")
    baseline_data, baseline_voxel, _ = load_and_normalize(args.baseline, "Baseline T2")
    followup_data, followup_voxel, _ = load_and_normalize(args.followup, "Follow-up T2")

    # -- Analyze each volume independently --
    print("\n[2/7] Analyzing baseline...")
    baseline_results, baseline_mask = analyze_single_volume(
        baseline_data, baseline_voxel, "Baseline"
    )

    print("\n[3/7] Analyzing follow-up...")
    followup_results, followup_mask = analyze_single_volume(
        followup_data, followup_voxel, "Follow-up"
    )

    if baseline_results is None or followup_results is None:
        print("ERROR: Ventricle segmentation failed. Aborting.")
        return

    # -- Generate inspection montages --
    print("\n[4/7] Generating inspection montages...")
    generate_inspection_montage(
        baseline_data, baseline_mask, baseline_results,
        os.path.join(output_dir, "candidate_inspection_baseline.png"),
        "Candidate Inspection - Baseline"
    )
    generate_inspection_montage(
        followup_data, followup_mask, followup_results,
        os.path.join(output_dir, "candidate_inspection_followup.png"),
        "Candidate Inspection - Follow-up"
    )

    # -- Generate comparison montage --
    print("\n[5/7] Generating baseline/follow-up comparison...")
    generate_comparison_montage(
        baseline_data, followup_data, baseline_mask, followup_mask,
        baseline_results, followup_results,
        os.path.join(output_dir, "candidate_comparison_matched.png")
    )

    # -- Build 3D meshes --
    print("\n[6/7] Building 3D reconstruction...")
    baseline_verts, baseline_faces, _ = build_3d_ventricle_mesh(
        baseline_mask, baseline_voxel, "Baseline"
    )
    followup_verts, followup_faces, _ = build_3d_ventricle_mesh(
        followup_mask, followup_voxel, "Follow-up"
    )

    # Build transparent brain surface from follow-up T2 (anatomical context)
    brain_verts, brain_faces = build_brain_surface_mesh(
        followup_data, followup_voxel, "Follow-up Brain"
    )

    generate_3d_html(
        baseline_verts, baseline_faces, followup_verts, followup_faces,
        baseline_results['persistent_candidates'],
        followup_results['persistent_candidates'],
        baseline_voxel, followup_voxel,
        os.path.join(output_dir, "ventricles_3d.html"),
        brain_verts=brain_verts,
        brain_faces=brain_faces,
    )

    # -- Save results and report --
    print("\n[7/7] Saving results...")
    combined_results = {
        'baseline': baseline_results,
        'followup': followup_results,
        'methodology': 'B-spline curvature + multi-Otsu ventricle segmentation',
        'alignment': 'Percentage-based ventricular level matching (no rigid registration)',
    }

    # Save JSON
    json_path = os.path.join(output_dir, "candidate_analysis_results.json")
    with open(json_path, 'w') as f:
        json.dump(combined_results, f, indent=2, default=str)
    print(f"  JSON saved: {json_path}")

    # Save markdown report
    generate_summary_report(
        baseline_results, followup_results,
        os.path.join(output_dir, "analysis_report.md")
    )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print(f"Output directory: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()
