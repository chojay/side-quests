# PDF Conversion Methods - Technical Reference

## Contents

- [Overview](#overview)
- [Understanding PDF Content Types](#understanding-pdf-content-types)
- [Conversion Methods Detailed](#conversion-methods-detailed)
- [Raster Conversion (PNG/JPEG)](#raster-conversion-pngjpeg)
- [Quality Considerations](#quality-considerations)
- [Workflow for Land Surveying Documents](#workflow-for-land-surveying-documents)
- [Advanced Techniques](#advanced-techniques)
- [Troubleshooting](#troubleshooting)
- [Performance Benchmarks](#performance-benchmarks)
- [Best Practices](#best-practices)
- [Library Dependencies](#library-dependencies)
- [See Also](#see-also)

## Overview

This document provides detailed technical information about PDF conversion methods, quality considerations, and best practices for different types of PDF documents.

## Understanding PDF Content Types

### Vector-Based PDFs

**Characteristics:**
- Created from CAD software, illustration tools, or typesetting programs
- Contain mathematical descriptions of shapes, lines, and curves
- Scale infinitely without quality loss
- Small file sizes relative to visual complexity
- Text is selectable and searchable

**Examples:**
- AutoCAD drawings
- Adobe Illustrator files exported to PDF
- Technical diagrams from vector drawing tools
- Most modern PDF documents from digital sources

**Best Conversion Method:** Vector extraction (PyMuPDF) or cairo

### Raster/Image-Based PDFs

**Characteristics:**
- Scanned documents or PDFs created from images
- Contain pixel-based bitmap data
- Fixed resolution
- Larger file sizes
- Text may not be selectable

**Examples:**
- Scanned blueprints
- Photos embedded in PDF
- Screenshots saved as PDF
- Older scanned technical drawings

**Best Conversion Method:** High-DPI raster conversion or hybrid approach

### Hybrid PDFs

**Characteristics:**
- Mix of vector graphics and embedded raster images
- Common in professional documents
- May have vector text with raster photos/diagrams
- Variable quality depending on content

**Examples:**
- Land surveying documents with photos and vector lines
- Engineering reports with embedded CAD drawings
- Architectural plans with photo references

**Best Conversion Method:** Hybrid SVG with embedded high-res images

## Conversion Methods Detailed

### 1. Vector Extraction (PyMuPDF)

**Technology:** PyMuPDF's `get_svg_image()` method

**How it works:**
- Extracts vector paths directly from PDF internal structure
- Converts PDF graphics operators to SVG equivalents
- Preserves mathematical precision of curves and lines

**Advantages:**
- Scalable output (true vector)
- Small file sizes
- Editable paths in SVG editors
- Maintains original precision

**Disadvantages:**
- May not handle complex gradients well
- Some PDF effects don't translate perfectly to SVG
- Embedded images may have quality issues
- Text handling can be inconsistent

**Best for:**
- Simple technical drawings
- Diagrams with clean vector paths
- Documents without complex effects

**Usage:**
```bash
python scripts/pdf_to_svg.py survey.pdf --method vector --page 1
```

### 2. Cairo Conversion (pdftocairo)

**Technology:** Poppler's pdftocairo utility

**How it works:**
- Uses Cairo graphics library to render PDF
- Converts PDF content to SVG format
- Highly compatible with PDF specification

**Advantages:**
- Excellent PDF compatibility
- Handles complex PDF features well
- Robust text rendering
- Widely used and tested

**Disadvantages:**
- Requires external dependency (poppler)
- May create more complex SVG than necessary
- Some styling may differ from original

**Best for:**
- Complex vector PDFs
- Documents with advanced PDF features
- When PyMuPDF produces incorrect results

**Usage:**
```bash
python scripts/pdf_to_svg.py survey.pdf --method cairo --page 1
```

**Installation:**
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Verify installation
pdftocairo -v
```

### 3. Hybrid Method (Embedded Raster)

**Technology:** PyMuPDF rendering + SVG wrapping

**How it works:**
- Renders PDF page to high-resolution raster image
- Embeds image in SVG wrapper
- Creates editable SVG layer on top

**Advantages:**
- Perfect visual fidelity to original
- Works with any PDF type
- Creates annotation-ready layer
- Predictable results

**Disadvantages:**
- Larger file sizes
- Background is raster (not scalable)
- Not suitable for editing underlying content

**Best for:**
- Graphic-heavy technical documents
- Land surveying documents
- Documents where visual accuracy is critical
- Base layer for annotation

**Usage:**
```bash
python scripts/pdf_to_svg.py survey.pdf --method hybrid --page 1 --dpi 300
```

**DPI Recommendations:**
- 150 DPI: Screen display only
- 300 DPI: Standard print quality (recommended)
- 600 DPI: High-quality prints, detailed technical drawings
- 1200 DPI: Very fine details, professional printing

## Raster Conversion (PNG/JPEG)

**Technology:** pdf2image with poppler

**How it works:**
- Renders PDF pages to raster images
- Outputs standard image formats
- Full control over resolution

**Advantages:**
- Universal compatibility
- Perfect visual reproduction
- Simple to use
- No conversion artifacts

**Disadvantages:**
- Not editable
- Fixed resolution
- Larger file sizes at high DPI

**Best for:**
- Sharing via email or web
- Inclusion in presentations
- When SVG editing is not needed

**Usage:**
```bash
# PNG (lossless, better for technical drawings)
python scripts/pdf_to_image.py survey.pdf --format png --dpi 300

# JPEG (lossy, better for photos)
python scripts/pdf_to_image.py survey.pdf --format jpeg --dpi 150
```

## Quality Considerations

### Resolution vs File Size Trade-offs

| DPI | Print Size (300 PPI) | Screen Display | File Size | Use Case |
|-----|----------------------|----------------|-----------|----------|
| 72  | 1:1 | Excellent | Smallest | Web only |
| 150 | 2:1 | Very Good | Small | Draft prints |
| 300 | 1:1 | Excellent | Medium | Standard printing |
| 600 | 1:2 | Excellent | Large | High-quality prints |
| 1200| 1:4 | Excellent | Very Large | Professional printing |

### Format Selection

**PNG:**
- Lossless compression
- Supports transparency
- Better for: Technical drawings, diagrams, text
- Larger file sizes

**JPEG:**
- Lossy compression
- No transparency
- Better for: Photos, scanned documents
- Smaller file sizes
- Quality setting: 85-95 recommended

**SVG (Vector):**
- Infinitely scalable
- Editable in vector software
- Better for: Clean diagrams, simple technical drawings
- Small file sizes

**SVG (Hybrid):**
- SVG wrapper with embedded raster
- Annotation layer available
- Better for: Complex technical drawings, land surveys
- Medium to large file sizes

## Workflow for Land Surveying Documents

### Recommended Approach

1. **Analyze the PDF:**
   ```bash
   python scripts/extract_graphics.py survey.pdf --page 1 --analyze
   ```

2. **Based on analysis results:**
   - If "vector-rich": Try vector or cairo method first
   - If "image-heavy": Use hybrid method directly

3. **Convert to hybrid SVG:**
   ```bash
   python scripts/pdf_to_svg.py survey.pdf --method hybrid --page 1 --dpi 300
   ```

4. **Result:** SVG with embedded high-res image and annotation layer

### Integration with Academic SVG Skill

The hybrid SVG output is designed to work with annotation and drawing tools:

```xml
<!-- Generated SVG structure -->
<svg xmlns="http://www.w3.org/2000/svg"
     width="612pt" height="792pt"
     viewBox="0 0 612 792">

  <!-- Base layer: Original PDF content -->
  <image href="survey_page_1_embedded.png"
         width="612" height="792"/>

  <!-- Annotation layer: Add your drawings here -->
  <g id="annotations">
    <!-- Add lines, text, shapes, etc. -->
  </g>
</svg>
```

**To augment with academic-svg skill:**
1. Convert PDF to hybrid SVG
2. Open SVG in editor or use academic-svg to add elements
3. Add measurement lines, labels, annotations
4. Keep base image as reference layer

## Advanced Techniques

### Extracting Specific Graphics

Use the extraction script to isolate individual images:

```bash
python scripts/extract_graphics.py survey.pdf --page 1 --min-width 100 --min-height 100
```

This creates:
- Individual image files
- Metadata JSON with positions and sizes
- Useful for analyzing complex documents

### Batch Processing

Process multiple pages:

```bash
# Convert all pages to images
python scripts/pdf_to_image.py survey.pdf --dpi 300

# Convert specific page range
python scripts/pdf_to_image.py survey.pdf --first-page 1 --last-page 5
```

### Custom Output Organization

```bash
# Organized by project
python scripts/pdf_to_svg.py survey.pdf \
  --method hybrid \
  --output-dir ./project/svg \
  --prefix property_survey \
  --dpi 300
```

## Troubleshooting

### Issue: PyMuPDF produces garbled text

**Solution:** Use cairo method instead
```bash
python scripts/pdf_to_svg.py file.pdf --method cairo
```

### Issue: Vector conversion missing elements

**Solution:** Switch to hybrid method
```bash
python scripts/pdf_to_svg.py file.pdf --method hybrid --dpi 300
```

### Issue: File sizes too large

**Solutions:**
- Reduce DPI: `--dpi 150`
- Use JPEG for photos: `--format jpeg`
- Compress PNG: Use external tools like `optipng`

### Issue: pdftocairo not found

**Solution:** Install poppler
```bash
brew install poppler  # macOS
```

### Issue: Poor quality output

**Solutions:**
- Increase DPI: `--dpi 600`
- Try different conversion method
- Check source PDF quality

## Performance Benchmarks

**Typical processing times** (Intel i7, 8GB RAM):

| Method | 1 page | 10 pages | File Size |
|--------|--------|----------|-----------|
| Vector | <1s | ~5s | 100-500 KB |
| Cairo | 1-2s | ~15s | 200KB-1MB |
| Hybrid 300 DPI | 2-3s | ~25s | 500KB-2MB |
| PNG 300 DPI | 2-3s | ~25s | 500KB-3MB |

## Best Practices

1. **Always analyze first** - Use `extract_graphics.py --analyze` to understand PDF structure
2. **Match method to content** - Vector for CAD, hybrid for technical documents
3. **Optimize DPI** - Use 300 for most cases, 150 for drafts, 600 for fine details
4. **Preserve originals** - Keep PDF source files
5. **Test scalability** - Verify SVG renders correctly at different sizes
6. **Document workflow** - Note conversion settings for reproducibility

## Library Dependencies

### Required
- **PyMuPDF (fitz)**: PDF manipulation and rendering
- **pdf2image**: PDF to raster conversion
- **Pillow (PIL)**: Image processing

### Optional
- **poppler-utils**: For pdftocairo (cairo method)

### Installation
```bash
# Core dependencies
pip3 install PyMuPDF pdf2image pillow

# Optional (for cairo method)
brew install poppler  # macOS
```

## See Also

- Main skill documentation: `../SKILL.md`
- Python API reference: `api_reference.md`
- Academic SVG skill for annotation and augmentation
