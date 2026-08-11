# Script Reference

Full CLI options for all three bundled scripts. All scripts also include `--help` for detailed usage information.

### pdf_to_image.py

Convert PDF pages to PNG or JPEG images.

```bash
python scripts/pdf_to_image.py PDF_FILE [OPTIONS]

Options:
  -o, --output-dir DIR      Output directory
  -d, --dpi DPI            Resolution (default: 300)
  -f, --format FORMAT      png or jpeg (default: png)
  --first-page N           First page to convert
  --last-page N            Last page to convert
  -p, --prefix PREFIX      Output filename prefix
```

### pdf_to_svg.py

Convert PDF pages to SVG format.

```bash
python scripts/pdf_to_svg.py PDF_FILE [OPTIONS]

Options:
  -m, --method METHOD      vector, cairo, or hybrid (default: hybrid)
  -o, --output-dir DIR     Output directory
  --page N                 Page number (default: 1)
  -p, --prefix PREFIX      Output filename prefix
  -d, --dpi DPI           DPI for hybrid method (default: 300)
```

### extract_graphics.py

Extract images and analyze PDF graphics.

```bash
python scripts/extract_graphics.py PDF_FILE [OPTIONS]

Options:
  -o, --output-dir DIR     Output directory
  --page N                 Extract from specific page
  --min-width N           Minimum image width (default: 50)
  --min-height N          Minimum image height (default: 50)
  --analyze               Analyze vector graphics (requires --page)
```
