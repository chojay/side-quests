# Usage Examples and Advanced Features

## Contents

- [Common Use Cases](#common-use-cases) - Worked examples: blueprints, multi-page documents, property surveys, photo extraction
- [Advanced Features](#advanced-features)
  - [Batch Processing](#batch-processing)
  - [Custom Output Organization](#custom-output-organization)
  - [Quality vs File Size Optimization](#quality-vs-file-size-optimization)

## Common Use Cases

### 1. Convert Scanned Blueprint

```bash
# Analyze first
python scripts/extract_graphics.py blueprint.pdf --page 1 --analyze

# Convert to high-res PNG
python scripts/pdf_to_image.py blueprint.pdf --format png --dpi 600

# Or create annotatable SVG
python scripts/pdf_to_svg.py blueprint.pdf --method hybrid --dpi 600
```

### 2. Multi-Page Technical Document

```bash
# Convert all pages to PNG
python scripts/pdf_to_image.py technical_doc.pdf --dpi 300

# Convert specific page range
python scripts/pdf_to_image.py technical_doc.pdf \
  --first-page 1 \
  --last-page 10 \
  --format png
```

### 3. Property Survey for Annotation

```bash
# Create SVG with annotation layer
python scripts/pdf_to_svg.py property_survey.pdf \
  --method hybrid \
  --page 1 \
  --dpi 300 \
  --output-dir ./property_survey \
  --prefix boundary_survey

# Result: boundary_survey_page_1.svg ready for annotation
```

### 4. Extract Survey Photos

```bash
# Extract all embedded photos from survey
python scripts/extract_graphics.py survey.pdf \
  --page 1 \
  --min-width 200 \
  --min-height 200 \
  --output-dir ./survey_photos
```

## Advanced Features

### Batch Processing

Process multiple files or pages:

```bash
# Process all PDFs in directory
for pdf in *.pdf; do
  python scripts/pdf_to_svg.py "$pdf" --method hybrid --page 1
done

# Convert all pages of one PDF
python scripts/pdf_to_image.py document.pdf --dpi 300
# Creates: document_page_01.png, document_page_02.png, ...
```

### Custom Output Organization

```bash
# Organized output with custom naming
python scripts/pdf_to_svg.py survey.pdf \
  --method hybrid \
  --page 1 \
  --output-dir ./projects/my_property/surveying \
  --prefix 2025_boundary_survey \
  --dpi 300

# Result:
# ./projects/my_property/surveying/2025_boundary_survey_page_1.svg
# ./projects/my_property/surveying/2025_boundary_survey_page_1_embedded.png
```

### Quality vs File Size Optimization

```bash
# Maximum quality (large files)
python scripts/pdf_to_image.py drawing.pdf --format png --dpi 600

# Balanced (recommended)
python scripts/pdf_to_image.py drawing.pdf --format png --dpi 300

# Smaller files (screen only)
python scripts/pdf_to_image.py drawing.pdf --format jpeg --dpi 150
```
