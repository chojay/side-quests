#!/usr/bin/env python3
"""
Grid Cell Extractor
===================
Splits MRI comparison montage PNGs (grids of slices, as often exported by
radiology viewers) into individual cell images, and renders a labeled
reference image so a human can identify which cells match anatomically
across two timepoints.

Companion to ssim_slice_matcher.py, which pairs the extracted cells
automatically.

Edit GRID_LAYOUTS below to describe your own montage images (filename,
pixel dimensions, rows x columns).

Usage:
    python grid_cell_extractor.py \
        --source-dir PATH/TO/montage_pngs \
        --output-dir PATH/TO/grid_cells
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageFont

# Grid definitions for each source montage image.
# EDIT THESE to match your own exported montages.
GRID_LAYOUTS = {
    "01_T2_FLAIR_multi.png": {
        "grid": (3, 3),  # rows x columns
        "description": "T2 FLAIR multiplanar"
    },
    "02_DWI_ADC_comparison.png": {
        "grid": (2, 4),
        "description": "DWI (top) and ADC (bottom) sequences"
    },
    "03_T1_pre_post_comparison.png": {
        "grid": (2, 3),
        "description": "T1 pre-contrast (top) and post-contrast (bottom)"
    },
    "04_enhancement_subtraction.png": {
        "grid": (3, 3),
        "description": "Enhancement subtraction mapping"
    },
    "05_SWAN_multi.png": {
        "grid": (3, 3),
        "description": "SWI/SWAN multiplanar"
    },
    "06_T2_multi.png": {
        "grid": (3, 3),
        "description": "T2 multiplanar"
    }
}


def load_font(size):
    """Load a truetype font with a safe fallback."""
    for candidate in ("/System/Library/Fonts/Helvetica.ttc",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def extract_grid_cells(source_path, grid_rows, grid_cols, output_prefix, output_dir):
    """Extract individual cells from a grid image."""

    img = Image.open(source_path)
    width, height = img.size

    # Calculate cell dimensions
    cell_width = width // grid_cols
    cell_height = height // grid_rows

    print(f"\n  Grid: {grid_rows}x{grid_cols}, Cell size: {cell_width}x{cell_height}")

    cells = []
    cell_num = 1

    for row in range(grid_rows):
        for col in range(grid_cols):
            # Calculate crop coordinates
            left = col * cell_width
            top = row * cell_height
            right = left + cell_width
            bottom = top + cell_height

            # Crop cell
            cell = img.crop((left, top, right, bottom))

            # Save cell
            cell_filename = f"{output_prefix}_cell{cell_num:02d}_r{row+1}c{col+1}.png"
            cell_path = os.path.join(output_dir, cell_filename)
            cell.save(cell_path, 'PNG', optimize=True)

            cells.append({
                'number': cell_num,
                'row': row + 1,
                'col': col + 1,
                'filename': cell_filename,
                'coords': (left, top, right, bottom)
            })

            print(f"    Cell {cell_num:02d} (Row {row+1}, Col {col+1}): {cell_filename}")
            cell_num += 1

    return cells


def create_labeled_reference(source_path, output_path, cells):
    """Create reference image with cell numbers overlaid."""

    img = Image.open(source_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    font = load_font(40)

    # Draw cell numbers
    for cell in cells:
        left, top, right, bottom = cell['coords']

        # Draw border
        draw.rectangle([left, top, right, bottom], outline='yellow', width=3)

        # Draw cell number
        text = f"#{cell['number']}"
        # Get text bbox for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = left + (right - left - text_width) // 2
        text_y = top + 10

        # Draw text with background
        draw.rectangle([text_x-5, text_y-5, text_x+text_width+5, text_y+text_height+5], fill='black')
        draw.text((text_x, text_y), text, fill='yellow', font=font)

    img.save(output_path, 'PNG')
    print(f"\n  Reference image saved: {os.path.basename(output_path)}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Split MRI montage PNGs into individual grid cell images.")
    parser.add_argument('--source-dir', required=True,
                        help="Directory containing the montage PNGs listed in GRID_LAYOUTS")
    parser.add_argument('--output-dir', required=True,
                        help="Directory to write cell images and labeled references")
    return parser.parse_args()


def main():
    args = parse_args()

    print("\n" + "="*70)
    print("MRI Grid Cell Extractor")
    print("="*70)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    all_extractions = {}

    for filename, layout in GRID_LAYOUTS.items():
        source_path = os.path.join(args.source_dir, filename)

        if not os.path.exists(source_path):
            print(f"\nWARNING: Skipping {filename} (not found)")
            continue

        print(f"\n{filename}")
        print(f"  {layout['description']}")
        print("-" * 70)

        # Extract cells
        prefix = filename.replace('.png', '')
        cells = extract_grid_cells(
            source_path,
            layout['grid'][0],
            layout['grid'][1],
            prefix,
            args.output_dir
        )

        # Create labeled reference
        ref_path = os.path.join(args.output_dir, f"{prefix}_REFERENCE_LABELED.png")
        create_labeled_reference(source_path, ref_path, cells)

        all_extractions[filename] = cells

    # Create summary file
    summary_path = os.path.join(args.output_dir, "CELL_MAPPING_GUIDE.txt")
    with open(summary_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("MRI GRID CELL EXTRACTION SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write("HOW TO USE:\n")
        f.write("1. Open each *_REFERENCE_LABELED.png file\n")
        f.write("2. Identify which cells show matching anatomy across the two timepoints\n")
        f.write("3. Note the cell numbers for matching pairs\n")
        f.write("4. Use these pairs (or ssim_slice_matcher.py) to build comparisons\n\n")
        f.write("="*70 + "\n\n")

        for filename, cells in all_extractions.items():
            layout = GRID_LAYOUTS[filename]
            f.write(f"\n{filename}\n")
            f.write(f"  Description: {layout['description']}\n")
            f.write(f"  Grid: {layout['grid'][0]} rows x {layout['grid'][1]} columns\n")
            f.write(f"  Total cells: {len(cells)}\n")
            f.write(f"  Reference: {filename.replace('.png', '')}_REFERENCE_LABELED.png\n\n")
            f.write("  Cell Mapping:\n")
            for cell in cells:
                f.write(f"    Cell #{cell['number']:02d}: Row {cell['row']}, Col {cell['col']} -> {cell['filename']}\n")
            f.write("\n" + "-"*70 + "\n")

    print("\n" + "="*70)
    print("Extraction complete.")
    print(f"  Output directory: {args.output_dir}")
    print("  Summary file: CELL_MAPPING_GUIDE.txt")
    print("\nNEXT STEPS:")
    print("1. Review the *_REFERENCE_LABELED.png images")
    print("2. Identify matching cell pairs across the two timepoints")
    print("3. Or run ssim_slice_matcher.py to pair them automatically")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
