#!/usr/bin/env python3
"""
PDF Graphics Extractor

Extracts embedded images and graphics from PDF files.
Useful for isolating specific elements from complex technical drawings.
"""

import argparse
import sys
from pathlib import Path
import json
from typing import List, Dict

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Install with: pip3 install PyMuPDF pillow")
    sys.exit(1)


def extract_images_from_pdf(
    pdf_path: str,
    output_dir: str = None,
    page_num: int = None,
    min_width: int = 50,
    min_height: int = 50
) -> List[Dict]:
    """
    Extract all embedded images from PDF.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory to save extracted images
        page_num: Specific page to extract from (None for all pages)
        min_width: Minimum image width to extract
        min_height: Minimum image height to extract

    Returns:
        List of dictionaries with image metadata and paths
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Set up output directory
    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_extracted_images"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Open PDF
    doc = fitz.open(pdf_path)

    # Determine which pages to process
    if page_num is not None:
        if page_num < 1 or page_num > len(doc):
            raise ValueError(f"Invalid page number: {page_num}. PDF has {len(doc)} page(s)")
        pages_to_process = [page_num - 1]  # Convert to 0-indexed
    else:
        pages_to_process = range(len(doc))

    extracted_images = []
    total_images = 0

    print(f"Extracting images from: {pdf_path.name}")
    if page_num:
        print(f"Page: {page_num}")
    else:
        print(f"Pages: all ({len(doc)} pages)")

    for page_idx in pages_to_process:
        page = doc[page_idx]
        image_list = page.get_images()

        print(f"\nPage {page_idx + 1}: Found {len(image_list)} image(s)")

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]  # Image XREF number

            # Extract image
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            width = base_image["width"]
            height = base_image["height"]

            # Skip small images (likely logos, icons)
            if width < min_width or height < min_height:
                print(f"  - Skipped image {img_idx + 1}: {width}x{height} (too small)")
                continue

            # Create filename
            filename = f"page_{page_idx + 1}_img_{img_idx + 1}.{image_ext}"
            output_path = output_dir / filename

            # Save image
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            # Get additional metadata
            colorspace = base_image.get("colorspace", "unknown")
            bpc = base_image.get("bpc", 0)  # Bits per component

            image_info = {
                "filename": filename,
                "path": str(output_path),
                "page": page_idx + 1,
                "width": width,
                "height": height,
                "format": image_ext,
                "colorspace": colorspace,
                "bits_per_component": bpc,
                "size_bytes": len(image_bytes)
            }

            extracted_images.append(image_info)
            total_images += 1

            print(f"  ✓ Extracted: {filename} ({width}x{height}, {image_ext.upper()})")

    doc.close()

    # Save metadata
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump({
            "source_pdf": str(pdf_path),
            "total_images": total_images,
            "images": extracted_images
        }, f, indent=2)

    print(f"\n✅ Extracted {total_images} image(s)")
    print(f"Output directory: {output_dir}")
    print(f"Metadata saved: {metadata_path}")

    return extracted_images


def extract_vector_graphics_info(
    pdf_path: str,
    page_num: int = 1
) -> Dict:
    """
    Analyze vector graphics on a PDF page.

    Args:
        pdf_path: Path to input PDF file
        page_num: Page number to analyze (1-indexed)

    Returns:
        Dictionary with vector graphics information
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(pdf_path)

    if page_num < 1 or page_num > len(doc):
        raise ValueError(f"Invalid page number: {page_num}. PDF has {len(doc)} page(s)")

    page = doc[page_num - 1]

    # Get page dimensions
    rect = page.rect
    width = rect.width
    height = rect.height

    # Get drawing commands
    drawings = page.get_drawings()

    # Analyze paths
    path_types = {
        "lines": 0,
        "curves": 0,
        "rectangles": 0,
        "other": 0
    }

    for drawing in drawings:
        items = drawing.get("items", [])
        for item in items:
            if item[0] == "l":  # Line
                path_types["lines"] += 1
            elif item[0] == "c":  # Curve
                path_types["curves"] += 1
            elif item[0] == "re":  # Rectangle
                path_types["rectangles"] += 1
            else:
                path_types["other"] += 1

    # Get text blocks
    text_blocks = page.get_text("dict")["blocks"]
    text_count = sum(1 for block in text_blocks if block.get("type") == 0)  # Type 0 = text

    # Get image count
    image_count = len(page.get_images())

    info = {
        "page_number": page_num,
        "dimensions": {
            "width": width,
            "height": height,
            "width_inches": width / 72,
            "height_inches": height / 72
        },
        "vector_graphics": {
            "total_drawings": len(drawings),
            "path_types": path_types
        },
        "text_blocks": text_count,
        "embedded_images": image_count,
        "is_vector_rich": len(drawings) > 10,
        "is_image_heavy": image_count > len(drawings)
    }

    doc.close()

    return info


def main():
    parser = argparse.ArgumentParser(
        description="Extract images and analyze graphics in PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all images from all pages
  python extract_graphics.py survey.pdf

  # Extract images from page 1 only
  python extract_graphics.py survey.pdf --page 1

  # Analyze vector graphics on page 1
  python extract_graphics.py survey.pdf --page 1 --analyze

  # Extract with custom size threshold and output directory
  python extract_graphics.py survey.pdf --min-width 100 --min-height 100 --output-dir ./images
        """
    )

    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory for extracted images"
    )
    parser.add_argument(
        "--page",
        type=int,
        help="Extract from specific page only (1-indexed)"
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=50,
        help="Minimum image width to extract (default: 50)"
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=50,
        help="Minimum image height to extract (default: 50)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze vector graphics (requires --page)"
    )

    args = parser.parse_args()

    try:
        if args.analyze:
            if not args.page:
                print("Error: --analyze requires --page argument", file=sys.stderr)
                sys.exit(1)

            print(f"Analyzing vector graphics: {args.pdf_path}")
            info = extract_vector_graphics_info(args.pdf_path, args.page)

            print(f"\n=== Page {info['page_number']} Analysis ===")
            print(f"\nDimensions:")
            print(f"  {info['dimensions']['width']:.1f} x {info['dimensions']['height']:.1f} pt")
            print(f"  {info['dimensions']['width_inches']:.2f} x {info['dimensions']['height_inches']:.2f} inches")

            print(f"\nVector Graphics:")
            print(f"  Total drawings: {info['vector_graphics']['total_drawings']}")
            print(f"  Lines: {info['vector_graphics']['path_types']['lines']}")
            print(f"  Curves: {info['vector_graphics']['path_types']['curves']}")
            print(f"  Rectangles: {info['vector_graphics']['path_types']['rectangles']}")
            print(f"  Other paths: {info['vector_graphics']['path_types']['other']}")

            print(f"\nContent:")
            print(f"  Text blocks: {info['text_blocks']}")
            print(f"  Embedded images: {info['embedded_images']}")

            print(f"\nRecommendation:")
            if info['is_image_heavy']:
                print("  → Use 'hybrid' method for SVG conversion (image-heavy)")
            elif info['is_vector_rich']:
                print("  → Use 'vector' or 'cairo' method for SVG conversion (vector-rich)")
            else:
                print("  → Use 'hybrid' method for SVG conversion (mixed content)")

        else:
            extract_images_from_pdf(
                pdf_path=args.pdf_path,
                output_dir=args.output_dir,
                page_num=args.page,
                min_width=args.min_width,
                min_height=args.min_height
            )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
