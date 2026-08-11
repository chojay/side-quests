#!/usr/bin/env python3
"""
SSIM Slice Matcher
==================
Pairs anatomically matching MRI slices across two timepoints using
structural similarity (SSIM), working on grid-cell PNGs produced by
grid_cell_extractor.py.

For each configured sequence:
1. Computes a full SSIM similarity matrix between all extracted cells
2. Greedily pairs cells above a similarity threshold (0.80) - high SSIM
   means the two slices show the same anatomical level
3. Disambiguates which member of each pair is the earlier scan using the
   expected per-sequence signal evolution over time (e.g., DWI lesion
   signal fades bright-to-dark, ADC recovers dark-to-bright, contrast
   enhancement decreases)
4. Renders side-by-side validation images and saves all matches to JSON

Usage:
    python ssim_slice_matcher.py \
        --cells-dir  PATH/TO/grid_cells \
        --output-dir PATH/TO/matched_pairs
"""

import argparse
from PIL import Image, ImageDraw, ImageFont
from skimage.metrics import structural_similarity as ssim
import numpy as np
import os
import json
import glob

# Sequence type configuration.
# EDIT THESE to match the montages you extracted with grid_cell_extractor.py.
# "evolution" encodes how signal is EXPECTED to change from the earlier to
# the later scan for whatever change you are tracking; it is used to order
# each matched pair in time. The values below are a textbook example for a
# resolving diffusion-restricting finding; substitute the expectations that
# apply to your own comparison.
SEQUENCE_CONFIG = {
    "02_DWI_ADC_comparison": {
        "DWI": {"rows": [1], "evolution": "bright_to_dark"},  # Top row
        "ADC": {"rows": [2], "evolution": "dark_to_bright"}   # Bottom row
    },
    "01_T2_FLAIR_multi": {
        "T2_FLAIR": {"rows": [1, 2, 3], "evolution": "subtle_to_prominent"}
    },
    "03_T1_pre_post_comparison": {
        "T1_pre": {"rows": [1], "evolution": "baseline"},
        "T1_post": {"rows": [2], "evolution": "enhancement_decrease"}
    },
    "04_enhancement_subtraction": {
        "Enhancement": {"rows": [1, 2, 3], "evolution": "high_to_low"}
    },
    "05_SWAN_multi": {
        "SWAN": {"rows": [1, 2, 3], "evolution": "stable"}
    },
    "06_T2_multi": {
        "T2": {"rows": [1, 2, 3], "evolution": "stable"}
    }
}

SSIM_THRESHOLD = 0.80


def compute_ssim_score(img1_path, img2_path):
    """Compute SSIM between two images."""
    try:
        img1 = np.array(Image.open(img1_path).convert('L'))
        img2 = np.array(Image.open(img2_path).convert('L'))

        # Resize if different dimensions
        if img1.shape != img2.shape:
            img2_pil = Image.fromarray(img2)
            img2_pil = img2_pil.resize((img1.shape[1], img1.shape[0]))
            img2 = np.array(img2_pil)

        score = ssim(img1, img2, data_range=img2.max() - img2.min())
        return score
    except Exception as e:
        print(f"Error computing SSIM: {e}")
        return 0.0


def get_mean_intensity(img_path):
    """Get mean pixel intensity."""
    img = np.array(Image.open(img_path).convert('L'))
    return np.mean(img)


def load_cells_for_source(cells_dir, source_prefix):
    """Load all cell images for a source montage."""
    pattern = os.path.join(cells_dir, f"{source_prefix}_cell*_r*c*.png")
    cell_files = sorted(glob.glob(pattern))

    cells = []
    for cell_file in cell_files:
        basename = os.path.basename(cell_file)
        # Parse: 02_DWI_ADC_comparison_cell01_r1c1.png
        parts = basename.split('_cell')
        if len(parts) == 2:
            cell_part = parts[1].replace('.png', '')
            cell_num = int(cell_part.split('_')[0])
            row_col = cell_part.split('_')[-1]  # r1c1
            row = int(row_col[1])
            col = int(row_col[3])

            cells.append({
                'number': cell_num,
                'row': row,
                'col': col,
                'path': cell_file,
                'intensity': get_mean_intensity(cell_file)
            })

    return cells


def find_anatomical_matches(cells, evolution_type):
    """Find anatomically matching pairs and order each pair in time.

    Returns a list of matches:
    [{'early_cell': num, 'late_cell': num, 'similarity': score, ...}, ...]
    """
    n = len(cells)
    if n < 2:
        return []

    # Compute similarity matrix
    sim_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            score = compute_ssim_score(cells[i]['path'], cells[j]['path'])
            sim_matrix[i, j] = score
            sim_matrix[j, i] = score

    # Find pairs with high anatomical similarity
    matches = []
    used = set()

    for i in range(n):
        if i in used:
            continue

        # Find best match for cell i
        best_j = -1
        best_sim = SSIM_THRESHOLD  # Minimum threshold

        for j in range(n):
            if j != i and j not in used and sim_matrix[i, j] > best_sim:
                best_j = j
                best_sim = sim_matrix[i, j]

        if best_j != -1:
            # Determine which member of the pair is the earlier scan,
            # based on the expected signal evolution for this sequence
            cell_i = cells[i]
            cell_j = cells[best_j]

            if evolution_type == "bright_to_dark":  # e.g., DWI signal fades
                early = cell_i if cell_i['intensity'] > cell_j['intensity'] else cell_j
                late = cell_j if cell_i['intensity'] > cell_j['intensity'] else cell_i
            elif evolution_type == "dark_to_bright":  # e.g., ADC recovers
                early = cell_i if cell_i['intensity'] < cell_j['intensity'] else cell_j
                late = cell_j if cell_i['intensity'] < cell_j['intensity'] else cell_i
            elif evolution_type == "high_to_low":  # e.g., enhancement decreases
                early = cell_i if cell_i['intensity'] > cell_j['intensity'] else cell_j
                late = cell_j if cell_i['intensity'] > cell_j['intensity'] else cell_i
            elif evolution_type == "subtle_to_prominent":  # structural changes
                # Less certain - order by intensity as a hint, verify visually
                early = cell_i if cell_i['intensity'] < cell_j['intensity'] else cell_j
                late = cell_j if cell_i['intensity'] < cell_j['intensity'] else cell_i
            else:  # stable / baseline: no reliable ordering signal
                early = cell_i
                late = cell_j

            matches.append({
                'early_cell': early['number'],
                'late_cell': late['number'],
                'similarity': best_sim,
                'anatomical_level': f"row{cell_i['row']}",
                'early_intensity': early['intensity'],
                'late_intensity': late['intensity']
            })

            used.add(i)
            used.add(best_j)

    return matches


def load_font(size):
    """Load a truetype font with a safe fallback."""
    for candidate in ("/System/Library/Fonts/Helvetica.ttc",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_validation_image(match, cells_dir, source_prefix, sequence_name, output_path):
    """Create side-by-side comparison of a matched pair."""
    early_pattern = os.path.join(cells_dir, f"{source_prefix}_cell{match['early_cell']:02d}_*.png")
    late_pattern = os.path.join(cells_dir, f"{source_prefix}_cell{match['late_cell']:02d}_*.png")

    early_file = glob.glob(early_pattern)[0] if glob.glob(early_pattern) else None
    late_file = glob.glob(late_pattern)[0] if glob.glob(late_pattern) else None

    if not early_file or not late_file:
        return

    img1 = Image.open(early_file)
    img2 = Image.open(late_file)

    # Create side-by-side comparison
    width = img1.width + img2.width + 30
    height = max(img1.height, img2.height) + 100

    canvas = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(canvas)

    # Paste images
    canvas.paste(img1, (10, 50))
    canvas.paste(img2, (img1.width + 20, 50))

    # Add labels
    font = load_font(24)
    font_small = load_font(16)

    draw.text((10, 10), f"Timepoint A (Cell #{match['early_cell']})", fill='yellow', font=font)
    draw.text((img1.width + 20, 10), f"Timepoint B (Cell #{match['late_cell']})", fill='cyan', font=font)

    draw.text((10, height-30), f"SSIM: {match['similarity']:.3f} | {sequence_name}", fill='white', font=font_small)

    canvas.save(output_path, 'PNG')


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pair anatomically matching MRI slices across two timepoints using SSIM.")
    parser.add_argument('--cells-dir', required=True,
                        help="Directory of grid-cell PNGs from grid_cell_extractor.py")
    parser.add_argument('--output-dir', required=True,
                        help="Directory for validation images and matches JSON")
    return parser.parse_args()


def main():
    args = parse_args()

    print("\n" + "="*70)
    print("Anatomical Slice Matcher - SSIM-based Temporal Pairing")
    print("="*70 + "\n")

    os.makedirs(args.output_dir, exist_ok=True)

    all_matches = {}

    for source, sequences in SEQUENCE_CONFIG.items():
        print(f"\n{source}.png")
        print("-" * 70)

        source_matches = {}

        for seq_name, seq_config in sequences.items():
            print(f"\n  {seq_name} sequence:")

            # Load cells for this sequence (filter by rows)
            all_cells = load_cells_for_source(args.cells_dir, source)
            seq_cells = [c for c in all_cells if c['row'] in seq_config['rows']]

            print(f"    Total cells: {len(seq_cells)}")

            if len(seq_cells) < 2:
                print("    WARNING: Not enough cells for matching")
                continue

            # Find matches
            matches = find_anatomical_matches(seq_cells, seq_config['evolution'])

            print(f"    Matches found: {len(matches)}")

            for idx, match in enumerate(matches):
                print(f"      Match {idx+1}: Cell #{match['early_cell']} (A) <-> Cell #{match['late_cell']} (B)")
                print(f"               SSIM: {match['similarity']:.3f}, Level: {match['anatomical_level']}")

                # Create validation image
                val_path = os.path.join(args.output_dir, f"{source}_{seq_name}_match{idx+1}.png")
                create_validation_image(match, args.cells_dir, source, seq_name, val_path)

            source_matches[seq_name] = matches

        all_matches[f"{source}.png"] = source_matches

    # Save matches to JSON
    output_json = os.path.join(args.output_dir, 'anatomical_matches.json')
    with open(output_json, 'w') as f:
        json.dump(all_matches, f, indent=2)

    print("\n" + "="*70)
    print("Matching complete.")
    print(f"  Matches saved: {output_json}")
    print(f"  Validation images: {args.output_dir}")
    print("\nNEXT STEPS:")
    print("1. Review the validation images")
    print("2. Verify anatomical landmarks align in matched pairs")
    print("3. Confirm the inferred temporal ordering is plausible")
    print("4. Proceed with ROI extraction if matches are valid")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
