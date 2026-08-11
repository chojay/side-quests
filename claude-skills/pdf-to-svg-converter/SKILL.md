---
name: pdf-to-svg-converter
description: >-
  Convert graphic-heavy PDF files (technical drawings, land surveying documents,
  blueprints, property maps) to SVG, PNG, or JPEG formats for editing, annotation,
  or use as base layers in vector graphics. Also extracts embedded images from
  PDFs and analyzes PDF content to recommend the best conversion method. This
  skill should be used when working with PDFs that contain diagrams, technical
  drawings, maps, or scanned documents that need to be converted to editable or
  augmentable formats, or when the user says "convert PDF to SVG", "PDF to
  image", "PDF to PNG", "extract graphics from PDF", "convert this land survey",
  or "make this PDF editable". Bundles Python scripts (PyMuPDF, pdftocairo,
  pdf2image) offering vector, cairo, and hybrid conversion methods.
---

# PDF to SVG/Image Converter

## Overview

Convert graphic-heavy PDF documents to SVG, PNG, or JPEG formats with high fidelity. Designed for technical drawings, land surveying documents, blueprints, and other graphical PDFs that need to be edited, annotated, or used as base layers for vector graphics work.

## When to Use This Skill

Use this skill when:
- Converting land surveying documents or property maps to editable formats
- Creating SVG base layers for annotation with tools like the academic-svg skill
- Extracting technical drawings from PDFs for editing
- Converting scanned blueprints to high-resolution images
- Preparing PDFs for use in vector graphics workflows
- Analyzing PDF content to determine optimal conversion strategy

**Trigger phrases:** "convert PDF to SVG", "PDF to image", "extract graphics from PDF", "convert land survey", "PDF to PNG", "make PDF editable"

## Quick Start

**Note:** Script paths in this document are relative to the skill directory (`~/.claude/skills/pdf-to-svg-converter/`). When invoked from a project working directory, use the full path, e.g. `python ~/.claude/skills/pdf-to-svg-converter/scripts/pdf_to_svg.py ...`

### 1. Analyze PDF Content

Before converting, analyze the PDF to determine the best conversion method:

```bash
python scripts/extract_graphics.py survey.pdf --page 1 --analyze
```

This shows:
- Page dimensions
- Vector graphics count
- Embedded images count
- Recommended conversion method

### 2. Choose Conversion Method

Based on analysis results:

**For vector-rich PDFs** (CAD drawings, digital diagrams):
```bash
python scripts/pdf_to_svg.py drawing.pdf --method vector --page 1
```

**For image-heavy PDFs** (scanned documents, photos):
```bash
python scripts/pdf_to_svg.py scan.pdf --method hybrid --page 1 --dpi 300
```

**For maximum compatibility** (works with all PDFs):
```bash
python scripts/pdf_to_svg.py document.pdf --method hybrid --page 1 --dpi 300
```

### 3. Convert to Raster Images (PNG/JPEG)

For non-editable image output:

```bash
# PNG (lossless, best for technical drawings)
python scripts/pdf_to_image.py survey.pdf --format png --dpi 300

# JPEG (smaller files, good for photos)
python scripts/pdf_to_image.py survey.pdf --format jpeg --dpi 150
```

## Conversion Methods

### Vector Extraction

Extract native vector graphics directly from PDF.

**Best for:**
- Digital CAD drawings
- Diagrams created in vector software
- PDFs with clean, simple vector paths

**Advantages:**
- Infinitely scalable
- Small file sizes
- Fully editable paths

**Usage:**
```bash
python scripts/pdf_to_svg.py document.pdf --method vector --page 1
```

### Cairo Method

Use poppler's pdftocairo utility for conversion.

**Best for:**
- Complex vector PDFs
- Documents with advanced PDF features
- When vector method produces incorrect results

**Requirements:** Poppler must be installed
```bash
brew install poppler  # macOS
```

**Usage:**
```bash
python scripts/pdf_to_svg.py document.pdf --method cairo --page 1
```

### Hybrid Method (Recommended for Land Surveys)

Creates SVG with embedded high-resolution raster image and annotation layer.

**Best for:**
- Land surveying documents
- Technical drawings with photos
- Any graphic-heavy PDF
- Documents that will be annotated

**Advantages:**
- Perfect visual fidelity
- Ready for annotation
- Works with any PDF type
- Predictable results

**Usage:**
```bash
python scripts/pdf_to_svg.py survey.pdf --method hybrid --page 1 --dpi 300
```

**Output structure:**
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 612 792">
  <title>PDF Page 1 - survey.pdf</title>

  <!-- Base layer: High-resolution PDF render -->
  <image href="survey_page_1_embedded.png" width="612" height="792"/>

  <!-- Add your annotations below -->
  <g id="annotations">
    <!-- Your custom SVG elements go here -->
  </g>
</svg>
```

### DPI Recommendations

| DPI | Use Case | File Size | Quality |
|-----|----------|-----------|---------|
| 150 | Screen display, drafts | Small | Good |
| 300 | Standard printing, most uses | Medium | Excellent |
| 600 | High-quality prints, fine details | Large | Outstanding |
| 1200| Professional printing | Very Large | Maximum |

## Working with Land Surveying Documents

### Typical Workflow

1. **Analyze the document:**
   ```bash
   python scripts/extract_graphics.py survey.pdf --page 1 --analyze
   ```

2. **Convert to hybrid SVG:**
   ```bash
   python scripts/pdf_to_svg.py survey.pdf \
     --method hybrid \
     --page 1 \
     --dpi 300 \
     --output-dir ./surveying \
     --prefix property_boundary
   ```

3. **Result files:**
   - `property_boundary_page_1.svg` - Editable SVG file
   - `property_boundary_page_1_embedded.png` - High-res base image

4. **Augment with annotations:**
   - Open SVG in vector editor
   - Or use the academic-svg skill to add measurement lines, labels, notes
   - Base image provides reference for accurate overlay

### Integration with Academic SVG Skill

The hybrid SVG output is designed to work seamlessly with annotation workflows:

```xml
<!-- Generated by pdf-to-svg-converter -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 612 792">
  <!-- Original survey document as base layer -->
  <image href="survey_page_1_embedded.png" .../>

  <!-- Add annotations using the academic-svg skill or manual editing -->
  <g id="annotations">
    <!-- Example: Add property boundary markers -->
    <circle cx="150" cy="200" r="5" fill="red"/>
    <text x="160" y="205" font-size="12">Property Corner</text>

    <!-- Example: Add measurement line -->
    <line x1="150" y1="200" x2="450" y2="200"
          stroke="blue" stroke-width="2"/>
    <text x="300" y="195" font-size="10">100.5 ft</text>
  </g>
</svg>
```

## Extracting Graphics

### Extract Embedded Images

Pull out photos and images embedded in PDF:

```bash
python scripts/extract_graphics.py survey.pdf --page 1
```

**Output:**
- Individual image files (PNG, JPEG)
- `metadata.json` with image information

**Options:**
```bash
# Extract from specific page
python scripts/extract_graphics.py survey.pdf --page 1

# Set minimum size threshold
python scripts/extract_graphics.py survey.pdf --min-width 100 --min-height 100

# Custom output directory
python scripts/extract_graphics.py survey.pdf --output-dir ./extracted_images
```

### Analyze PDF Graphics

Understand PDF content before conversion:

```bash
python scripts/extract_graphics.py survey.pdf --page 1 --analyze
```

**Provides:**
- Page dimensions
- Vector graphics count and types
- Text blocks count
- Embedded images count
- Conversion method recommendation

## Common Use Cases and Advanced Features

For worked examples (scanned blueprints, multi-page technical documents, property surveys for annotation, extracting survey photos) plus batch processing, custom output organization, and quality vs file size optimization, read `references/usage_examples.md`.

## Workflow Decision Tree

```
Start: PDF file to convert
  │
  ├─ Need to analyze content?
  │    └─ Yes → Run extract_graphics.py --analyze
  │    └─ No → Continue
  │
  ├─ Output format needed?
  │    │
  │    ├─ PNG/JPEG (raster image)
  │    │    └─ Run pdf_to_image.py
  │    │         ├─ Technical drawing → PNG at 300 DPI
  │    │         ├─ Photo-based → JPEG at 150-300 DPI
  │    │         └─ High detail → PNG at 600 DPI
  │    │
  │    └─ SVG (vector/editable)
  │         └─ Run pdf_to_svg.py
  │              │
  │              ├─ Vector-rich PDF?
  │              │    └─ Try --method vector
  │              │    └─ If issues → Try --method cairo
  │              │
  │              └─ Image-heavy/Mixed content?
  │                   └─ Use --method hybrid (recommended)
  │                        └─ Standard: --dpi 300
  │                        └─ High detail: --dpi 600
  │
  └─ Need to extract images?
       └─ Run extract_graphics.py
            └─ Optionally: --analyze for recommendations
```

## Troubleshooting

When conversion output is garbled or missing elements, files are too large, pdftocairo is not found, or image quality is poor, read `references/troubleshooting.md` for solutions.

## Script Reference

For full CLI flags and options for all three scripts, read `references/script_reference.md`. All scripts also include `--help` for detailed usage information.

## Installation Requirements

### Python Dependencies

```bash
pip3 install PyMuPDF pdf2image pillow
```

### System Dependencies

**For Cairo method (optional):**
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils
```

**For pdf2image:**
Poppler is required (same installation as above)

### Verify Installation

```bash
# Check Python packages
python3 -c "import fitz, pdf2image, PIL; print('✓ All packages installed')"

# Check poppler (optional, for cairo method)
pdftocairo -v
```

## Resources

### references/

- **conversion_methods.md** - Detailed technical documentation on conversion methods, quality considerations, and best practices for different PDF types
- **usage_examples.md** - Worked examples (blueprints, multi-page documents, surveys, photo extraction) and batch/advanced output options
- **troubleshooting.md** - Consult when conversion output is wrong, files are too large, or pdftocairo is missing
- **script_reference.md** - Full CLI flags for all three scripts

### scripts/

- **pdf_to_image.py** - Convert PDF pages to PNG/JPEG with configurable DPI
- **pdf_to_svg.py** - Convert PDF pages to SVG using vector, cairo, or hybrid methods
- **extract_graphics.py** - Extract embedded images and analyze PDF content

All scripts include `--help` for detailed usage information.

### assets/

- **svg_annotation_template.svg** - Starting template for annotating converted PDFs (base image layer plus `<g id="annotations">` layer); see `assets/README.md` for usage

## Best Practices

1. **Always analyze first** - Use `extract_graphics.py --analyze` to understand PDF structure
2. **Choose appropriate method:**
   - Digital vector drawings → `vector` or `cairo`
   - Technical documents with graphics → `hybrid`
   - Simple raster output → `pdf_to_image.py`
3. **DPI selection:**
   - Screen only: 150 DPI
   - Standard printing: 300 DPI
   - High detail: 600 DPI
4. **Format selection:**
   - Technical drawings/text: PNG (lossless)
   - Photos: JPEG (smaller files)
   - Editable/scalable: SVG
5. **Preserve originals** - Keep source PDF files
6. **Document settings** - Note DPI and method used for reproducibility

## Integration with Other Skills

### Academic SVG Skill

Use converted PDFs as base layers for scientific diagrams:

1. Convert PDF to hybrid SVG
2. Load in academic-svg workflow
3. Add annotations, measurements, labels on top of base image
4. Maintain reference to original document

### Obsidian Vault Integration

Store conversions in your vault's attachments folder (replace `<vault>` with your vault path):

```bash
python scripts/pdf_to_svg.py survey.pdf \
  --method hybrid \
  --output-dir "<vault>/attachments" \
  --prefix property_boundary
```

Embed in Obsidian notes with the standard embed syntax:
```markdown
![[property_boundary_page_1.svg]]
```

---

*For detailed technical information, see references/conversion_methods.md*
