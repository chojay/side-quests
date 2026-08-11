# Academic SVG Skill

A comprehensive Claude Code skill for generating publication-quality SVG figures for semiconductor process and materials science research.

---

## Overview

This skill enables Claude to create scientifically accurate, visually professional SVG diagrams for academic publications, including:

- **Device Cross-Sections**: MOSFET gate stacks, high-k/metal-gate structures, spacers, junctions
- **Crystal Structures**: Si diamond cubic, GaN, SiC, unit cells, atomic arrangements
- **Energy Diagrams**: Band structures, Fermi levels, potential barriers
- **Process Flows**: Deposition, lithography, and etch sequences, ALD cycles, material evolution
- **Phase Diagrams**: Temperature-composition diagrams, state transitions
- **Layered Materials**: Thin films, heterostructures, interfaces
- **Graphs & Data**: I-V curves, C-V profiles, dopant profiles, breakdown characteristics

**Target Publications**: Nature, Science, Advanced Materials, IEEE Electron Device Letters, Applied Physics Letters, Journal of Applied Physics, and similar high-impact journals.

---

## Installation

### For Claude Code

1. **Copy this folder** to your Claude Code skills directory:
   ```bash
   cp -r academic-svg ~/.claude/skills/academic-svg
   ```

2. **Restart Claude Code** or reload skills

3. **Verify installation**:
   - The skill will activate when you request academic figures
   - Test with: "Create an academic SVG figure showing a MOSFET gate-stack cross-section"

### Manual Installation

Place the `academic-svg` folder in:
- **macOS/Linux**: `~/.claude/skills/`
- **Windows**: `%USERPROFILE%\.claude\skills\`

---

## Quick Start

### Basic Usage

```
You: Create an academic SVG figure showing a layered gate stack with Si substrate, gate dielectric, and metal gate

Claude: [Generates professional SVG with proper colors, labels, and styling]
```

### Triggering the Skill

The skill activates automatically when you request:
- "academic SVG figure"
- "publication-quality diagram"
- "materials science schematic"
- "gate stack diagram SVG"
- "crystal structure figure"

---

## File Structure

```
academic-svg/
├── SKILL.md                    # Main skill instructions for Claude
├── color_palettes.md           # Comprehensive color specifications
├── style_guidelines.md         # Typography, spacing, layout rules
├── README.md                   # This file
│
├── examples/                   # Complete example SVG files
│   ├── crystal_structure.svg   # Si diamond cubic unit cell example
│   ├── energy_diagram.svg      # Band diagram example
│   ├── process_flow.svg        # Gate-stack deposition and etch flow
│   ├── layered_material.svg    # Cross-sectional thin-film layers
│   └── gate_stack.svg          # High-k metal gate MOSFET cross-section
│
├── templates/                  # Reusable starting templates
│   ├── figure_template.svg     # Base structure template
│   ├── multi_panel.svg         # Multi-panel layout template
│   └── graph_template.svg      # Graph/chart template
│
└── assets/                     # Supporting visual references
    ├── color_swatches.svg      # Color palette visual reference
    ├── typography_samples.svg  # Font size examples
    └── arrow_library.svg       # Arrow style collection
```

---

## Features

### Professional Color Palette
- **Scientifically Meaningful**: Colors represent materials accurately (gold for metal gates, blue for oxides)
- **Publication-Ready**: Muted, professional tones suitable for print and digital
- **Accessible**: WCAG AA compliant contrast ratios
- **Consistent**: Same material = same color throughout figure

**See**: `color_palettes.md` for complete specifications

### Typography & Layout
- **Clear Hierarchy**: Appropriate font sizes for different element types
- **Proper Notation**: Chemical formulas with subscripts/superscripts
- **Grid-Based Alignment**: Professional, consistent spacing
- **Multi-Panel Layouts**: Side-by-side comparisons, sequential flows

**See**: `style_guidelines.md` for detailed guidelines

### Common Figure Types

1. **Layered Materials**: Gate stacks, thin films, interfaces
2. **Atomic Structures**: Crystal lattices, unit cells
3. **Energy Diagrams**: Band structures, barriers, Fermi levels
4. **Process Flows**: Deposition and etch steps, mechanisms, cycles
5. **Phase Diagrams**: Temperature-composition plots
6. **Data Visualization**: Graphs, device characteristics

**See**: `examples/` folder for templates

### Accessibility
- **Screen Reader Compatible**: Proper `<title>` and `<desc>` elements
- **High Contrast**: Text meets WCAG AA standards
- **Scalable**: Vector format ensures quality at any size
- **Color-Blind Friendly**: Designs consider deuteranopia

---

## Usage Examples

### Example 1: Gate-Stack Cross-Section

**Request**:
```
Create an academic SVG showing a high-k metal gate MOSFET cross-section with p-Si substrate, n+ source/drain, interfacial SiO2, HfO2 high-k layer, TiN metal gate, and nitride spacers. Show the electron channel with an arrow.
```

**Claude generates**:
- Stratified device structure with proper colors
- Tan for the Si substrate, deep blue for doped regions
- Light blue for SiO2, pink for high-k HfO2
- Dark gray for TiN, gold for the W gate fill
- Cyan arrow for the inversion channel
- Clean labels with chemical formulas and layer thicknesses

### Example 2: Crystal Structure

**Request**:
```
Generate an SVG of the silicon diamond cubic crystal structure showing the two interpenetrating fcc sublattices and tetrahedral bonding.
```

**Claude generates**:
- Spheres for Si atoms with 3D gradients
- Unit cell boundaries (dashed)
- Tetrahedral bonds for interior basis atoms
- Proper relative atomic sizes and depth cues
- Crystal axes labeled, lattice parameter annotated (a = 5.43 Å)

### Example 3: Process Flow

**Request**:
```
Create a process flow diagram for a gate-stack deposition and etch sequence, showing surface clean, ALD of the high-k dielectric, metal gate deposition, and plasma etch patterning.
```

**Claude generates**:
- Sequential panels with arrows
- Layer-by-layer buildup across stages
- Plasma ion arrows for the etch step
- Curved return arrow for the next patterning level
- Clear labels for each stage
- Professional layout

---

## Customization

### Modifying Colors

Edit `color_palettes.md` to change the color scheme. Update both the documentation and examples to match.

### Changing Typography

Edit the font-family specifications in `style_guidelines.md`. For best results, use web-safe sans-serif fonts.

### Adding New Templates

Create new SVG files in the `templates/` folder following the structure in `figure_template.svg`. Include:
- Proper `<defs>` section for reusable elements
- `<style>` section for CSS classes
- Comments explaining customization points

---

## Best Practices

### When Using This Skill

1. **Be Specific**: Describe the materials, layers, or processes clearly
2. **Specify Panel Count**: Mention if you need multi-panel (a, b, c, d)
3. **Indicate Data**: If showing graphs, provide data points or general trends
4. **Mention Scale**: Specify if scale bars or dimensions are needed

### For Best Results

- ✅ Request one figure concept at a time
- ✅ Specify materials by chemical formula
- ✅ Mention intended publication (affects style choices)
- ✅ Ask for revisions if colors or layout need adjustment

### Quality Checklist

Before finalizing a figure, verify:
- [ ] All chemical formulas have proper subscripts/superscripts
- [ ] Colors are consistent for same materials
- [ ] Text is legible at publication size
- [ ] Panel labels (a, b, c) are present if multi-panel
- [ ] Scale bars included where appropriate
- [ ] Legend provided if multiple data series
- [ ] Sufficient contrast for all text

---

## Technical Specifications

### SVG Standards
- **Namespace**: `xmlns="http://www.w3.org/2000/svg"`
- **Coordinate System**: Viewbox-based for scalability
- **Color Space**: RGB (sRGB profile)
- **Text**: SVG `<text>` elements (not converted to paths)

### Output Specifications
- **Format**: SVG 1.1 compliant
- **Size**: Scalable (vector), typically 800x600px equivalent
- **Resolution**: Infinite (vector), 300+ DPI when rasterized
- **File Size**: Optimized, typically 10-50 KB

### Export Formats
- **Digital**: SVG (native), PNG (rasterized)
- **Print**: PDF (vector), TIFF (rasterized at 300 DPI)
- **Presentations**: SVG or PNG at appropriate resolution

---

## Troubleshooting

### Common Issues

**Issue**: Colors don't match expected materials
**Solution**: Specify material names explicitly, or reference `color_palettes.md`

**Issue**: Text too small when viewing
**Solution**: SVG scales - zoom in browser or set explicit viewport width

**Issue**: Chemical formulas missing subscripts
**Solution**: Request correction: "Fix subscripts in chemical formulas"

**Issue**: Panels not aligned
**Solution**: Claude uses grid-based alignment; request "realign panels to grid"

---

## Examples Gallery

### Device Structures

- ✅ Gate stacks and high-k/metal-gate interfaces
- ✅ Source/drain junctions and spacers
- ✅ Interconnects and diffusion barriers
- ✅ Shallow trench isolation
- ✅ FinFET and planar cross-sections

### Materials Characterization

- ✅ Crystal structures
- ✅ Phase transitions
- ✅ Grain boundaries
- ✅ Defect sites
- ✅ Surface morphologies

### Energy & Thermodynamics

- ✅ Energy level diagrams
- ✅ Band structure alignments
- ✅ Potential barriers
- ✅ Gibbs free energy plots
- ✅ Activation energy landscapes

### Performance Data

- ✅ I-V transfer and output characteristics
- ✅ C-V profiles
- ✅ Dopant depth profiles (SIMS)
- ✅ Gate leakage vs. EOT
- ✅ Mobility vs. effective field

---

## Contributing

To enhance this skill:

1. **Add Examples**: Create new SVG examples in `examples/` folder
2. **Expand Palette**: Add domain-specific colors to `color_palettes.md`
3. **Document Patterns**: Add new figure types to `SKILL.md`
4. **Share Templates**: Contribute reusable templates

---

## Version History

### v1.0.0 (Current)
- Initial release
- Comprehensive color palette (70+ colors)
- 6 figure type templates
- Full documentation
- Accessibility features
- OmniSVG best practices integration

---

## References

### Color Palette Sources
Extracted from 15 high-quality materials science figures from:
- Nature journals
- Science
- Advanced Materials
- IEEE and AIP journals
- ACS journals

### Design Principles
- OmniSVG methodology (https://github.com/OmniSVG/OmniSVG)
- Academic publishing standards
- WCAG accessibility guidelines
- SVG 1.1 specification

---

## Credits

**Developed for**: Materials science researchers and academic professionals

**Purpose**: Enable rapid creation of publication-quality figures without specialized design software

**License**: MIT (see the repository LICENSE file)

---

## Support & Feedback

### Getting Help

1. **Check Documentation**:
   - `SKILL.md` - Comprehensive usage guide
   - `color_palettes.md` - All color specifications
   - `style_guidelines.md` - Typography and layout rules

2. **Review Examples**: Look at `examples/` folder for similar figure types

3. **Experiment**: Modify templates in `templates/` folder

### Reporting Issues

If Claude generates figures that don't meet expectations:
- Provide specific feedback about what needs adjustment
- Reference examples from publications you want to emulate
- Specify technical requirements (size, format, colors)

---

## Frequently Asked Questions

**Q: Can I use this for other scientific fields?**
A: Yes! While optimized for semiconductor materials science, the principles apply to chemistry, physics, and engineering.

**Q: How do I change the figure size?**
A: SVG scales automatically. For specific dimensions, mention "800 pixels wide" or similar.

**Q: Can Claude include actual data in graphs?**
A: Yes, provide data points or describe trends, and Claude will visualize them.

**Q: What about 3D structures?**
A: Claude can create 2D projections with perspective. For true 3D, use specialized software.

**Q: Can I export to PowerPoint?**
A: Yes, SVG files can be imported into PowerPoint, Keynote, or converted to PNG.

**Q: How do I ensure color consistency across multiple figures?**
A: Reference the color palette explicitly for each figure in a series.

---

## Quick Reference Card

### Color Shortcuts
- Metal gate/contact: `#F4C542` (golden yellow)
- Oxide (SiO₂): `#7CB5E8` (light blue)
- High-k (HfO₂): `#FFB6C1` (soft pink)
- Plasma/ion species: `#4EC9E0` (cyan)
- Text: `#2E2E2E` (dark gray)

### Font Sizes
- Panel labels: 14-16px, bold
- Main labels: 11-12px, semi-bold
- Annotations: 8-9px, regular

### Spacing
- Figure margins: 20-30px
- Panel gutters: 15-25px
- Element spacing: 10-15px

### Arrows
- Standard: 2-3px width
- Bold: 4-6px width
- Ion/plasma movement: cyan with arrowhead

---

*For the most current information and updates, refer to the individual documentation files in this skill package.*
