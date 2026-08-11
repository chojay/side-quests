#!/usr/bin/env python3
"""
PDF to SVG Converter

Converts PDF pages to SVG format, preserving vector graphics when possible.
Uses multiple strategies for optimal quality:
1. Direct vector extraction from PDF (best for vector-based PDFs)
2. Raster-to-vector tracing (for scanned/rasterized PDFs)
3. Embedded image approach (fallback for complex graphics)
"""

import argparse
import sys
from pathlib import Path
import subprocess

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not found")
    print("Install with: pip3 install PyMuPDF")
    sys.exit(1)


def check_poppler_installed() -> bool:
    """Check if poppler utilities are installed."""
    try:
        subprocess.run(["pdftocairo", "-v"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_pdf_to_svg_vector(
    pdf_path: str,
    output_dir: str = None,
    page_num: int = 1,
    prefix: str = None
) -> Path:
    """
    Convert PDF to SVG using direct vector extraction with PyMuPDF.
    Works best for PDFs that contain actual vector graphics.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to save SVG (defaults to PDF directory)
        page_num: Page number to convert (1-indexed)
        prefix: Output filename prefix

    Returns:
        Path to created SVG file
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

    # Open PDF
    doc = fitz.open(pdf_path)

    if page_num < 1 or page_num > len(doc):
        raise ValueError(f"Invalid page number: {page_num}. PDF has {len(doc)} page(s)")

    # Get the page (0-indexed in PyMuPDF)
    page = doc[page_num - 1]

    # Create output filename
    output_filename = f"{prefix}_page_{page_num}.svg"
    output_path = output_dir / output_filename

    # Convert to SVG
    svg_data = page.get_svg_image()

    # Write SVG file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_data)

    doc.close()

    return output_path


def convert_pdf_to_svg_cairo(
    pdf_path: str,
    output_dir: str = None,
    page_num: int = 1,
    prefix: str = None
) -> Path:
    """
    Convert PDF to SVG using pdftocairo (poppler utility).
    Often produces better quality for complex PDFs.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to save SVG
        page_num: Page number to convert (1-indexed)
        prefix: Output filename prefix

    Returns:
        Path to created SVG file
    """
    if not check_poppler_installed():
        raise RuntimeError(
            "pdftocairo not found. Install poppler-utils:\n"
            "  macOS: brew install poppler\n"
            "  Ubuntu: sudo apt-get install poppler-utils"
        )

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

    # Create output filename
    output_filename = f"{prefix}_page_{page_num}.svg"
    output_path = output_dir / output_filename

    # Run pdftocairo
    try:
        subprocess.run(
            [
                "pdftocairo",
                "-svg",
                "-f", str(page_num),
                "-l", str(page_num),
                str(pdf_path),
                str(output_path.with_suffix(""))  # pdftocairo adds .svg
            ],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"pdftocairo failed: {e.stderr}")

    # pdftocairo appends .svg, so check for the actual output
    actual_output = output_path.with_suffix("") / f"{page_num}.svg"
    if actual_output.exists():
        # Move to expected location
        actual_output.rename(output_path)

    return output_path


def convert_pdf_to_svg_hybrid(
    pdf_path: str,
    output_dir: str = None,
    page_num: int = 1,
    prefix: str = None,
    dpi: int = 300
) -> Path:
    """
    Create SVG with embedded high-resolution raster image.
    Best for graphic-heavy PDFs like land surveying documents.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to save SVG
        page_num: Page number to convert (1-indexed)
        prefix: Output filename prefix
        dpi: Resolution for embedded image

    Returns:
        Path to created SVG file
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

    # Open PDF and get page dimensions
    doc = fitz.open(pdf_path)
    if page_num < 1 or page_num > len(doc):
        raise ValueError(f"Invalid page number: {page_num}. PDF has {len(doc)} page(s)")

    page = doc[page_num - 1]
    rect = page.rect

    # Render page to high-res image
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 DPI is default
    pix = page.get_pixmap(matrix=mat)

    # Save as PNG
    png_filename = f"{prefix}_page_{page_num}_embedded.png"
    png_path = output_dir / png_filename
    pix.save(str(png_path))

    # Create SVG wrapper
    svg_filename = f"{prefix}_page_{page_num}.svg"
    svg_path = output_dir / svg_filename

    # Calculate dimensions in points (1 point = 1/72 inch)
    width_pt = rect.width
    height_pt = rect.height

    svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width_pt}pt" height="{height_pt}pt"
     viewBox="0 0 {width_pt} {height_pt}">
  <title>PDF Page {page_num} - {pdf_path.name}</title>
  <desc>Converted from PDF using hybrid method (embedded {dpi} DPI raster image)</desc>

  <!-- Base layer: High-resolution PDF render -->
  <image x="0" y="0" width="{width_pt}" height="{height_pt}"
         xlink:href="{png_filename}"
         preserveAspectRatio="none"/>

  <!-- Add your annotations and drawings below this line -->
  <g id="annotations">
    <!-- Your custom SVG elements go here -->
  </g>
</svg>'''

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    doc.close()

    return svg_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF pages to SVG format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Conversion Methods:
  vector   - Extract vector graphics directly (best for vector PDFs)
  cairo    - Use pdftocairo for conversion (requires poppler)
  hybrid   - Embed high-res raster image in SVG (best for graphic-heavy PDFs)

Examples:
  # Convert using vector extraction
  python pdf_to_svg.py survey.pdf --method vector

  # Convert using cairo (requires poppler)
  python pdf_to_svg.py survey.pdf --method cairo

  # Create hybrid SVG with embedded 300 DPI image (recommended for land surveys)
  python pdf_to_svg.py survey.pdf --method hybrid --dpi 300

  # Convert specific page with custom output
  python pdf_to_svg.py survey.pdf --page 1 --output-dir ./svg --prefix survey_map
        """
    )

    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument(
        "-m", "--method",
        choices=["vector", "cairo", "hybrid"],
        default="hybrid",
        help="Conversion method (default: hybrid)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory (default: same as PDF)"
    )
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number to convert (default: 1)"
    )
    parser.add_argument(
        "-p", "--prefix",
        help="Output filename prefix (default: PDF filename)"
    )
    parser.add_argument(
        "-d", "--dpi",
        type=int,
        default=300,
        help="DPI for hybrid method (default: 300)"
    )

    args = parser.parse_args()

    try:
        print(f"Converting PDF: {args.pdf_path}")
        print(f"Method: {args.method}")
        print(f"Page: {args.page}")

        if args.method == "vector":
            output_path = convert_pdf_to_svg_vector(
                pdf_path=args.pdf_path,
                output_dir=args.output_dir,
                page_num=args.page,
                prefix=args.prefix
            )
        elif args.method == "cairo":
            output_path = convert_pdf_to_svg_cairo(
                pdf_path=args.pdf_path,
                output_dir=args.output_dir,
                page_num=args.page,
                prefix=args.prefix
            )
        else:  # hybrid
            output_path = convert_pdf_to_svg_hybrid(
                pdf_path=args.pdf_path,
                output_dir=args.output_dir,
                page_num=args.page,
                prefix=args.prefix,
                dpi=args.dpi
            )

        print(f"\n✅ SVG created: {output_path}")
        print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
