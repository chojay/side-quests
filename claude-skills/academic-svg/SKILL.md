---
name: academic-svg
description: >-
  Create publication-quality SVG figures for academic semiconductor process and
  materials science papers including device cross-sections (MOSFET gate stacks,
  high-k dielectrics), wafer process flows (deposition, lithography, plasma
  etch), thin-film and ALD schematics, crystal structures (Si, GaN, SiC),
  energy band diagrams, phase diagrams, interconnect and interface diagrams,
  and scientific data plots (I-V curves, C-V profiles, dopant profiles). Use
  when the user requests scientific figures, academic diagrams, SVG for
  publication, materials science visualizations, semiconductor device
  illustrations, or says phrases like "create academic figure", "gate stack
  schematic", "wafer process flow", or "crystal structure SVG". Generates
  scientifically accurate, professionally styled diagrams suitable for Nature,
  Science, Advanced Materials, and similar high-impact journals.
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Academic SVG - Materials Science Figure Generation

## Overview

This skill enables the creation of publication-quality SVG figures for academic semiconductor process and materials science papers. Generate scientifically accurate, visually professional diagrams including device cross-sections, crystal structures, energy band diagrams, wafer process flows, phase diagrams, and thin-film schematics.

## When to Use This Skill

Use this skill when the user requests:
- Scientific figures for materials science or device publications
- Semiconductor device cross-sections (MOSFET gate stacks, high-k/metal-gate structures)
- Crystal structure or molecular representations (Si, GaN, SiC)
- Energy level/band diagrams
- Process flow diagrams for wafer fabrication (deposition, lithography, etch)
- Phase diagrams
- Thin-film and layered material schematics (ALD stacks, heterostructures)
- Interface characterization diagrams
- Any academic-quality SVG for materials science

**Trigger phrases**: "create academic figure", "SVG for publication", "materials science diagram", "gate stack schematic", "crystal structure SVG", "wafer process flow"

## Core Design Principles

### 1. Clarity and Simplicity
- Prioritize clear communication over decorative elements
- Simplify complex concepts without losing scientific accuracy
- Use visual hierarchy to guide the viewer's eye
- Avoid clutter - every element should serve a purpose

### 2. Professional Aesthetic
- Use muted, professional color schemes suitable for publication
- Maintain high contrast for readability
- Consistent styling throughout the figure
- Publication-ready quality (suitable for Nature, Science, Advanced Materials, etc.)

### 3. Scientific Accuracy
- Accurate representation of materials and processes
- Proper chemical notation and formulas
- Correct scale relationships when applicable
- Scientifically meaningful color choices

### 4. Accessibility
- Sufficient contrast ratios (WCAG AA minimum: 4.5:1 for text)
- Descriptive labels and annotations
- Include `<title>` and `<desc>` elements
- Text as actual text when possible (not paths)

### 5. Scalability
- Vector format ensures quality at any size
- Figures should be legible from thumbnail to poster size
- Appropriate line weights and text sizes
- 300+ DPI equivalent for print publication

## Color Palette

### Primary Colors (Most Frequently Used)

**Blues & Cyans** - For oxide dielectrics, conduction bands, plasma species
- Deep Blue: `#4472C4` - Primary structures, CB, n-doped regions
- Light Blue: `#7CB5E8` - Oxide layers (SiO2), dielectric films
- Cyan: `#4EC9E0` - Plasma and ion species (Ar+), carrier flow

**Yellows & Golds** - For metal gates, contacts, gold pads
- Golden Yellow: `#F4C542` - Gate metal, Au contacts, W fill
- Soft Yellow: `#FFD966` - Metal highlights, lighter metal regions
- Peach: `#F2D7A9` - Si substrates, buffer layers

**Pinks & Magentas** - For high-k films, photoresist, critical features
- Soft Pink: `#FFB6C1` - High-k dielectrics (HfO2, Al2O3)
- Hot Pink: `#FF69B4` - Photoresist masks, interface regions
- Red: `#E83845` - Failure modes, critical points

**Grays & Neutrals** - For structural elements, metal gates, inactive regions
- Dark Gray: `#404040` - Text, outlines, TiN layers
- Medium Gray: `#808080` - Polysilicon, support structures
- Light Gray: `#D3D3D3` - Inactive/background regions

**Greens** - For nitride films, protective layers
- Olive Green: `#6B8E23` - Organic films, anti-reflective coatings
- Sage Green: `#8FBC8F` - Nitride spacers (Si3N4), passivation

**Purples** - For alternative phases, intermediate states
- Medium Purple: `#8B7BB8` - Phase transitions, Ga in III-V materials
- Dark Purple: `#6A5ACD` - Specific material types

### Background Colors
- Cream: `#FFF9E6` - Panel backgrounds
- Off-white: `#FAFAFA` - Overall figure background
- Light Beige: `#FAF0E6` - Substrate backgrounds

### Color Usage Guidelines

1. **Semantic Consistency**: Use the same color for the same material throughout
2. **Contrast**: Ensure sufficient contrast between adjacent elements
3. **Color Blindness**: Consider deuteranopia (red-green) when selecting colors
4. **Gradients**: Use sparingly, typically for depth or concentration
5. **Accent Colors**: Use red/orange for emphasis, warnings, or critical features

## Typography

### Font Specifications

**Primary Font Family**: Sans-serif (Helvetica, Arial, or system-ui)
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
```

### Font Sizes
- **Figure Captions**: 10-11px
- **Panel Labels (a, b, c)**: 14-16px, bold (700 weight)
- **Main Labels**: 11-12px, semi-bold (600 weight)
- **Axis Labels**: 9-10px, regular (400 weight)
- **Chemical Formulas**: 10-11px
- **Annotations**: 8-9px
- **Subscripts/Superscripts**: 0.7x base size

### Text Styling Best Practices

1. **Chemical Notation**:
   - Subscripts: Use `<tspan baseline-shift="sub" font-size="0.7em">2</tspan>` for SiO2
   - Superscripts: Use `<tspan baseline-shift="super" font-size="0.7em">+</tspan>` for Ar+
   - Italics: Use for variables (E, T, P) but not for chemical symbols

2. **Alignment**:
   - Left-align most text
   - Center-align titles and panel labels
   - Right-align axis labels on right side

3. **Spacing**:
   - Line height: 1.2-1.4
   - Letter spacing: Normal (0)
   - Word spacing: Normal

4. **Text Color**:
   - Primary text: `#2E2E2E` (dark gray, not pure black)
   - Secondary text: `#606060` (medium gray)
   - White text on dark: `#FFFFFF` (ensure 4.5:1 contrast)

## Layout & Composition

### Multi-Panel Layouts

**Panel Markers**: Bold lowercase letters (a, b, c, d, e) positioned at top-left
```xml
<text x="10" y="25" font-size="16" font-weight="700" fill="#2E2E2E">a</text>
```

**Panel Spacing**:
- Margins: 20-30px around figure edges
- Gutters: 15-25px between panels
- Internal padding: 10-15px within panels

**Common Layouts**:
1. **Side-by-side comparison**: Two columns (before/after, control/treatment)
2. **Sequential flow**: Left-to-right progression with arrows
3. **Grid**: 2x2 or 3x2 arrangement for multiple conditions
4. **Hierarchical**: Central concept with surrounding details
5. **Circular**: Cyclical processes (e.g., deposition-lithography-etch patterning loops, ALD cycles)

### Visual Hierarchy

**Primary Elements** (Largest, most prominent):
- Main subject of the figure
- Central structures or key processes
- Positioned at optical center

**Secondary Elements** (Medium prominence):
- Supporting structures
- Contextual information
- Process steps

**Tertiary Elements** (Smallest, supporting):
- Labels and annotations
- Arrows and connectors
- Scale bars and legends

### SVG Structure & Organization

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">

  <!-- Accessibility -->
  <title>Brief figure description</title>
  <desc>Detailed explanation of the figure content and significance</desc>

  <!-- Definitions for reusable elements -->
  <defs>
    <!-- Gradients -->
    <linearGradient id="metalGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD966;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#F4C542;stop-opacity:1" />
    </linearGradient>

    <!-- Arrow markers -->
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#2E2E2E" />
    </marker>

    <!-- Reusable symbols -->
    <symbol id="siliconAtom" viewBox="0 0 20 20">
      <circle cx="10" cy="10" r="8" fill="#708090" stroke="#2E2E2E" stroke-width="0.5"/>
    </symbol>
  </defs>

  <!-- Styles -->
  <style>
    .panel-label { font-size: 16px; font-weight: 700; fill: #2E2E2E; }
    .main-label { font-size: 12px; font-weight: 600; fill: #2E2E2E; }
    .annotation { font-size: 9px; font-weight: 400; fill: #404040; }
    .layer-outline { stroke: #2E2E2E; stroke-width: 1; }
  </style>

  <!-- Background (if needed) -->
  <rect width="800" height="600" fill="#FAFAFA"/>

  <!-- Main content groups -->
  <g id="panel-a">
    <!-- Panel content -->
  </g>

  <g id="panel-b">
    <!-- Panel content -->
  </g>

</svg>
```

## Common Figure Types

For detailed examples of each figure type (Layered Material Schematics, Crystal/Molecular Structures, Energy Band Diagrams, Process Flow Diagrams, Phase Diagrams, and Graph/Data Visualization), refer to the templates directory and supporting documentation files.

## Workflow for Creating Academic SVG

### Step 1: Understand the Request
- What type of figure? (crystal structure, band diagram, process flow, etc.)
- What materials/processes are involved?
- How many panels needed?
- Any specific data to visualize?

### Step 2: Plan the Layout
- Determine figure dimensions (800x600 for single, wider for multi-panel)
- Sketch mental layout: panels, labels, legends
- Identify reusable components

### Step 3: Set Up SVG Structure
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 [width] [height]">
  <title>...</title>
  <desc>...</desc>
  <defs>
    <!-- Gradients, markers, symbols -->
  </defs>
  <style>
    /* CSS classes */
  </style>
  <!-- Content groups -->
</svg>
```

### Step 4: Create Content
- Start with backgrounds and major elements
- Add secondary structures
- Include labels and annotations
- Add arrows and connectors
- Insert legends and scale bars

### Step 5: Refine and Validate
- Check color contrast
- Verify all text is legible
- Ensure proper alignment
- Test at different sizes
- Validate SVG syntax

### Step 6: Add Final Touches
- Panel labels (a, b, c)
- Figure caption guidance
- Accessibility elements
- Comments for complex sections

## Tips for Excellence

1. **Start Simple**: Build complexity gradually
2. **Use Grid Alignment**: Align elements to invisible grid for professional appearance
3. **Consistent Spacing**: Use same margins and gutters throughout
4. **Test Scaling**: View at 50%, 100%, 200% to ensure legibility
5. **Color Meaning**: Colors should reinforce scientific meaning
6. **Less is More**: Remove unnecessary elements
7. **Proofread**: Check all chemical formulas and labels
8. **Accessibility First**: Always include title, desc, and proper contrast

## Common Mistakes to Avoid

- ❌ Using pure black (`#000000`) - use dark gray (`#2E2E2E`)
- ❌ Overcrowding with too many labels
- ❌ Inconsistent arrow styles for same meaning
- ❌ Poor contrast (light text on light background)
- ❌ Forgetting subscripts/superscripts in formulas
- ❌ Misaligned elements
- ❌ Omitting units on axes
- ❌ Using decorative rather than semantic colors

## Supporting Resources

**Additional Documentation**:
- `color_palettes.md` - Complete color specifications and usage guidelines
- `style_guidelines.md` - Detailed typography and layout rules
- `SVG_FILES_RUNDOWN.md` - Overview of SVG structure and best practices
- `examples/` - Complete figure examples
- `templates/` - Reusable starting points for common figure types
- `assets/` - Visual references (color swatches, arrow library, typography samples)

---

*This skill generates publication-quality SVG figures suitable for high-impact materials science and device physics journals including Nature, Science, Advanced Materials, IEEE Electron Device Letters, Applied Physics Letters, and similar publications.*
