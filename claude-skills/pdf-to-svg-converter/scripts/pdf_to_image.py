#!/usr/bin/env python3
"""
PDF to Image Converter

Converts PDF pages to high-quality PNG or JPEG images.
Optimized for graphic-heavy PDFs like technical drawings and land surveying documents.
"""

import argparse
import sys
from pathlib import Path
from typing import List

try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Install with: pip3 install pdf2image pillow")
    print("Also requires poppler. On macOS: brew install poppler")
    sys.exit(1)


def convert_pdf_to_images(
    pdf_path: str,
    output_dir: str = None,
    dpi: int = 300,
    format: str = "png",
    first_page: int = None,
    last_page: int = None,
    prefix: str = None
) -> List[Path]:
    """
    Convert PDF pages to images.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to save images (defaults to PDF directory)
        dpi: Resolution in dots per inch (300 recommended for technical drawings)
        format: Output format ('png' or 'jpeg')
        first_page: First page to convert (1-indexed, None for all)
        last_page: Last page to convert (1-indexed, None for all)
        prefix: Output filename prefix (defaults to PDF filename)

    Returns:
        List of paths to created image files
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Set up output directory
    if output_dir is None:
        output_dir = pdf_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up filename prefix
    if prefix is None:
        prefix = pdf_path.stem

    # Validate format
    format = format.lower()
    if format not in ["png", "jpeg", "jpg"]:
        raise ValueError(f"Invalid format: {format}. Must be 'png' or 'jpeg'")

    # Normalize jpeg format
    if format == "jpg":
        format = "jpeg"

    print(f"Converting PDF: {pdf_path.name}")
    print(f"Output format: {format.upper()}")
    print(f"Resolution: {dpi} DPI")

    # Convert PDF to images
    try:
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=first_page,
            last_page=last_page,
            fmt=format
        )
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF: {e}")

    # Save images
    output_paths = []
    num_digits = len(str(len(images)))

    for i, image in enumerate(images, start=1):
        # Calculate actual page number
        page_num = (first_page or 1) + i - 1

        # Create output filename
        output_filename = f"{prefix}_page_{page_num:0{num_digits}d}.{format}"
        output_path = output_dir / output_filename

        # Save image
        if format == "jpeg":
            # Convert RGBA to RGB for JPEG
            if image.mode == "RGBA":
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3])
                image = rgb_image
            image.save(output_path, "JPEG", quality=95, optimize=True)
        else:
            image.save(output_path, "PNG", optimize=True)

        output_paths.append(output_path)
        print(f"  ✓ Saved: {output_filename}")

    print(f"\n✅ Converted {len(images)} page(s)")
    print(f"Output directory: {output_dir}")

    return output_paths


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF pages to high-quality images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all pages to PNG at 300 DPI
  python pdf_to_image.py survey.pdf

  # Convert to JPEG at 150 DPI
  python pdf_to_image.py survey.pdf --format jpeg --dpi 150

  # Convert only pages 1-3
  python pdf_to_image.py survey.pdf --first-page 1 --last-page 3

  # Specify output directory and prefix
  python pdf_to_image.py survey.pdf --output-dir ./images --prefix survey_map
        """
    )

    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory (default: same as PDF)"
    )
    parser.add_argument(
        "-d", "--dpi",
        type=int,
        default=300,
        help="Resolution in DPI (default: 300)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["png", "jpeg", "jpg"],
        default="png",
        help="Output format (default: png)"
    )
    parser.add_argument(
        "--first-page",
        type=int,
        help="First page to convert (1-indexed)"
    )
    parser.add_argument(
        "--last-page",
        type=int,
        help="Last page to convert (1-indexed)"
    )
    parser.add_argument(
        "-p", "--prefix",
        help="Output filename prefix (default: PDF filename)"
    )

    args = parser.parse_args()

    try:
        convert_pdf_to_images(
            pdf_path=args.pdf_path,
            output_dir=args.output_dir,
            dpi=args.dpi,
            format=args.format,
            first_page=args.first_page,
            last_page=args.last_page,
            prefix=args.prefix
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
