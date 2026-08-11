# Troubleshooting

Consult this reference when conversion output is wrong, files are too large, or pdftocairo is missing.

### Vector conversion produces garbled output

**Solution:** Use cairo or hybrid method
```bash
python scripts/pdf_to_svg.py file.pdf --method cairo
```

### Missing elements in converted SVG

**Solution:** Use hybrid method for complete visual fidelity
```bash
python scripts/pdf_to_svg.py file.pdf --method hybrid --dpi 300
```

### File sizes too large

**Solutions:**
- Reduce DPI: `--dpi 150` for screen display
- Use JPEG for photos: `--format jpeg`
- Process specific pages only: `--page 1`

### pdftocairo command not found

**Solution:** Install poppler
```bash
# macOS
brew install poppler

# Verify
pdftocairo -v
```

### Poor image quality

**Solutions:**
- Increase DPI: `--dpi 600` or `--dpi 1200`
- Use PNG instead of JPEG: `--format png`
- Check source PDF quality (may be low-res scan)
