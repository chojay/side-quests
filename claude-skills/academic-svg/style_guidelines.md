# Academic SVG Style Guidelines

Typography, spacing, layout, and design principles for publication-quality materials science figures.

## Table of Contents

- [Typography](#typography) - fonts, sizes, weights, chemical notation, alignment, text color
- [Spacing & Layout](#spacing--layout) - margins, multi-panel spacing, grid alignment
- [Line Weights & Strokes](#line-weights--strokes) - stroke widths, styles, caps and joins
- [Shapes & Elements](#shapes--elements) - rounded corners, shadows and depth
- [Arrow Design](#arrow-design) - arrowhead markers, variations, label positioning
- [Panel Layout Patterns](#panel-layout-patterns) - side-by-side, 2×2 grid, sequential flow
- [Legend & Scale Bar Design](#legend--scale-bar-design)
- [Best Practices Summary](#best-practices-summary) - DO and DON'T lists
- [Responsive Sizing](#responsive-sizing) - viewbox strategy
- [Print Considerations](#print-considerations) - resolution, color space, safe areas

---

## Typography

### Font Family Selection

**Primary Recommendation**: System sans-serif stack
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
```

**Alternative Options**:
- **For web**: `font-family: "Inter", "Roboto", sans-serif;`
- **For print**: `font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;`
- **Scientific**: `font-family: "Latin Modern Sans", "Computer Modern Sans", sans-serif;`

**Avoid**:
- ❌ Serif fonts (Times, Georgia) - too formal, harder to read at small sizes
- ❌ Decorative fonts - unprofessional
- ❌ Monospace fonts (except for code snippets)

---

### Font Size Hierarchy

| Element | Size (px) | Weight | Usage |
|---------|-----------|--------|-------|
| **Figure Title** | 18-20 | 700 (Bold) | Main figure title (rarely used in panels) |
| **Panel Labels** | 14-16 | 700 (Bold) | a, b, c, d markers |
| **Main Labels** | 11-12 | 600 (Semi-bold) | Material names, structure labels |
| **Axis Labels** | 9-10 | 400 (Regular) | X and Y axis labels |
| **Tick Labels** | 8-9 | 400 (Regular) | Numeric values on axes |
| **Annotations** | 8-9 | 400 (Regular) | Callouts, notes |
| **Subscripts/Superscripts** | 70% of base | Inherit | Chemical formulas, exponents |
| **Legends** | 9-10 | 400 (Regular) | Legend text |

---

### Font Weights

```xml
<!-- Regular (400) -->
<text font-weight="400">Normal text</text>

<!-- Semi-bold (600) - for emphasis -->
<text font-weight="600">Important label</text>

<!-- Bold (700) - for panel markers and titles -->
<text font-weight="700">a</text>
```

**Guidelines**:
- Use Regular (400) for most text
- Use Semi-bold (600) for main labels
- Use Bold (700) sparingly for panel markers and critical labels
- Avoid Light (300) or Extra-bold (800+)

---

### Chemical Notation

#### Subscripts
```xml
<text x="100" y="100" font-size="12">
  H<tspan baseline-shift="sub" font-size="8.4">2</tspan>O
</text>

<!-- Or using relative sizing -->
<text x="100" y="100" font-size="12">
  Si<tspan baseline-shift="sub" font-size="0.7em">3</tspan>N<tspan baseline-shift="sub" font-size="0.7em">4</tspan>
</text>
```

#### Superscripts
```xml
<text x="100" y="100" font-size="12">
  Ar<tspan baseline-shift="super" font-size="0.7em">+</tspan>
</text>

<text x="100" y="100" font-size="12">
  10<tspan baseline-shift="super" font-size="0.7em">16</tspan> cm<tspan baseline-shift="super" font-size="0.7em">-3</tspan>
</text>
```

#### Italics for Variables (not chemical symbols)
```xml
<!-- Correct: Variables in italics -->
<text font-style="italic">E</text><text font-style="italic">f</text>
<text font-style="italic">T</text> = 298 K

<!-- Incorrect: Chemical symbols should NOT be italic -->
<text>Si</text> <!-- Correct -->
<text font-style="italic">Si</text> <!-- Wrong! -->
```

#### Greek Letters
```xml
<!-- Use Unicode characters -->
<text>α-phase</text> <!-- α = U+03B1 -->
<text>β-transition</text> <!-- β = U+03B2 -->
<text>ΔG</text> <!-- Δ = U+0394 -->
```

Common Greek:
- α (alpha): `&#x03B1;` or `α`
- β (beta): `&#x03B2;` or `β`
- γ (gamma): `&#x03B3;` or `γ`
- δ (delta): `&#x03B4;` or `δ`
- Δ (Delta): `&#x0394;` or `Δ`
- μ (mu): `&#x03BC;` or `μ`
- θ (theta): `&#x03B8;` or `θ`

---

### Text Alignment

```xml
<!-- Left-aligned (default) -->
<text x="100" y="100" text-anchor="start">Left aligned</text>

<!-- Center-aligned (for panel labels, centered labels) -->
<text x="100" y="100" text-anchor="middle">Centered</text>

<!-- Right-aligned (for right-side axis labels) -->
<text x="100" y="100" text-anchor="end">Right aligned</text>
```

**Best Practices**:
- Left-align most descriptive text
- Center-align panel labels (a, b, c)
- Center-align text within boxes/regions
- Right-align axis labels on the right side

---

### Line Height & Spacing

```xml
<!-- Multi-line text with proper spacing -->
<text x="100" y="100" font-size="10">
  <tspan x="100" dy="0">Line 1</tspan>
  <tspan x="100" dy="14">Line 2</tspan> <!-- dy = font-size × 1.4 -->
  <tspan x="100" dy="14">Line 3</tspan>
</text>
```

**Line Height Recommendations**:
- Standard text: 1.4× font size (e.g., 12px font → 16.8px line height)
- Compact text: 1.2× font size
- Annotations: 1.3× font size

---

### Text Color

```css
/* Primary text */
.primary-text {
  fill: #2E2E2E; /* Dark gray, not pure black */
}

/* Secondary text */
.secondary-text {
  fill: #606060; /* Medium gray */
}

/* Tertiary/de-emphasized text */
.tertiary-text {
  fill: #808080; /* Light gray */
}

/* Text on dark backgrounds */
.text-on-dark {
  fill: #FFFFFF; /* White */
}

/* Colored text (use sparingly) */
.ion-label {
  fill: #4EC9E0; /* Cyan for plasma-ion labels (Ar+) */
}
```

**Guidelines**:
- Avoid pure black (`#000000`) - use `#2E2E2E` instead
- Ensure 4.5:1 contrast minimum
- Use colored text only when semantically meaningful

---

## Spacing & Layout

### Margin System

```
Figure Margins:
┌─────────────────────────────────────┐
│  20-30px                            │
│    ┌─────────────────────────┐     │
│    │                         │     │
│    │    Figure Content       │     │
│    │                         │     │
│    └─────────────────────────┘     │
│                                     │
└─────────────────────────────────────┘
```

**Margin Specifications**:
- **Figure edges**: 20-30px
- **Panel internal padding**: 10-15px
- **Between elements**: 8-12px
- **Text padding**: 5-8px around text boxes

---

### Multi-Panel Spacing

```
Multi-Panel Layout (2×2):
┌──────────────┬────┬──────────────┐
│  Panel A     │ 20 │  Panel B     │
│              │    │              │
├──────────────┼────┼──────────────┤
│      15      │    │      15      │
├──────────────┼────┼──────────────┤
│  Panel C     │ 20 │  Panel D     │
│              │    │              │
└──────────────┴────┴──────────────┘
```

**Gutter Specifications**:
- **Horizontal gutter**: 20-25px
- **Vertical gutter**: 15-20px
- **Panel markers**: 10px from top-left corner

---

### Grid Alignment

Use an invisible grid for consistent alignment:

```xml
<!-- Define a 10px grid -->
<!-- Align all elements to multiples of 10 -->
<rect x="50" y="100" width="300" height="200"/> <!-- All values divisible by 10 -->
<text x="60" y="120"/> <!-- 10px padding from rect edge -->
```

**Grid Guidelines**:
- Use 5px or 10px grid
- Align all major elements to grid
- Smaller elements can use half-grid (5px)
- Consistent alignment creates professional appearance

---

### Element Spacing

**Within a Group**:
```xml
<g id="layer-stack">
  <rect y="100" height="20"/> <!-- Layer 1 -->
  <rect y="120" height="30"/> <!-- Layer 2: no gap -->
  <rect y="150" height="25"/> <!-- Layer 3: no gap -->
</g>
```

**Between Groups**:
```xml
<g id="group-1" transform="translate(0, 0)">...</g>
<!-- 20px gap -->
<g id="group-2" transform="translate(0, 220)">...</g>
```

**Around Text**:
```xml
<!-- Text box with padding -->
<rect x="100" y="100" width="120" height="30"/> <!-- Box -->
<text x="160" y="120">Centered text</text> <!-- 10px padding on all sides -->
```

---

## Line Weights & Strokes

### Stroke Width Guidelines

| Element | Width (px) | Usage |
|---------|------------|-------|
| **Outlines** | 0.5-1 | Atom circles, subtle boundaries |
| **Standard** | 1-2 | Layer outlines, boxes, borders |
| **Emphasis** | 2-3 | Important structures, axes |
| **Arrows** | 2-4 | Process flows, ion movement |
| **Bold Arrows** | 4-6 | Major process directions |

```xml
<!-- Subtle outline -->
<rect stroke="#2E2E2E" stroke-width="0.5"/>

<!-- Standard outline -->
<rect stroke="#2E2E2E" stroke-width="1"/>

<!-- Emphasized outline -->
<rect stroke="#2E2E2E" stroke-width="2"/>

<!-- Arrow -->
<line stroke="#2E2E2E" stroke-width="3"/>
```

---

### Stroke Styles

**Solid** (default):
```xml
<line stroke="#2E2E2E" stroke-width="2"/>
```

**Dashed** (for hidden/background elements):
```xml
<line stroke="#808080" stroke-width="1" stroke-dasharray="5,3"/>
<!-- Pattern: 5px dash, 3px gap -->
```

**Dotted** (for guidelines):
```xml
<line stroke="#808080" stroke-width="1" stroke-dasharray="2,2"/>
<!-- Pattern: 2px dot, 2px gap -->
```

**Dash-Dot** (for special boundaries):
```xml
<line stroke="#2E2E2E" stroke-width="1" stroke-dasharray="8,3,2,3"/>
<!-- Pattern: 8px dash, 3px gap, 2px dot, 3px gap -->
```

**Common Patterns**:
- Unit cell boundaries: `stroke-dasharray="5,3"`
- Construction lines: `stroke-dasharray="2,2"`
- Comparison arrows: `stroke-dasharray="5,5"`

---

### Stroke Caps & Joins

```xml
<!-- Line caps -->
<line stroke-linecap="butt"/> <!-- Default, flat ends -->
<line stroke-linecap="round"/> <!-- Rounded ends, good for arrows -->
<line stroke-linecap="square"/> <!-- Square ends, extends beyond endpoint -->

<!-- Line joins (for polylines/polygons) -->
<polyline stroke-linejoin="miter"/> <!-- Default, pointed corners -->
<polyline stroke-linejoin="round"/> <!-- Rounded corners -->
<polyline stroke-linejoin="bevel"/> <!-- Flat corners -->
```

**Recommendations**:
- Arrows: `stroke-linecap="round"`
- Scale bars: `stroke-linecap="square"`
- Polylines: `stroke-linejoin="round"` for smoother appearance

---

## Shapes & Elements

### Rounded Corners

```xml
<!-- Rectangle with rounded corners -->
<rect x="100" y="100" width="200" height="100" rx="5" ry="5"/>
```

**Border Radius Guidelines**:
- Info boxes: `rx="3-5"`
- Panels: `rx="5-8"`
- Buttons/interactive: `rx="8-10"`
- Atoms/circles: Use `<circle>` not rounded rect

---

### Shadows & Depth (Use Sparingly)

```xml
<defs>
  <filter id="subtle-shadow">
    <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
    <feOffset dx="1" dy="1" result="offsetblur"/>
    <feComponentTransfer>
      <feFuncA type="linear" slope="0.3"/>
    </feComponentTransfer>
    <feMerge>
      <feMergeNode/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>

<rect filter="url(#subtle-shadow)" fill="#FFFFFF" stroke="#2E2E2E"/>
```

**When to Use Shadows**:
- ✅ Floating panels or info boxes
- ✅ Layered structures showing depth
- ❌ Flat diagrams (most academic figures)
- ❌ Excessive depth effects

---

## Arrow Design

### Standard Arrowhead Marker

```xml
<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
    <polygon points="0 0, 10 3, 0 6" fill="#2E2E2E"/>
  </marker>
</defs>

<line x1="100" y1="100" x2="200" y2="100"
      stroke="#2E2E2E" stroke-width="2" marker-end="url(#arrowhead)"/>
```

### Arrow Variations

**Large Bold Arrow**:
```xml
<marker id="boldArrow" markerWidth="14" markerHeight="14" refX="13" refY="5" orient="auto">
  <polygon points="0 0, 14 5, 0 10" fill="#2E2E2E"/>
</marker>
```

**Colored Ion Arrow**:
```xml
<marker id="ionArrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
  <polygon points="0 0, 10 3, 0 6" fill="#4EC9E0"/>
</marker>
```

**Double-ended Arrow**:
```xml
<line stroke="#2E2E2E" stroke-width="2"
      marker-start="url(#arrowhead)" marker-end="url(#arrowhead)"/>
```

---

### Arrow Label Positioning

```xml
<!-- Arrow with label -->
<g id="labeled-arrow">
  <line x1="100" y1="150" x2="250" y2="150" stroke="#4EC9E0" stroke-width="2" marker-end="url(#arrowhead)"/>
  <text x="175" y="145" font-size="9" fill="#4EC9E0" text-anchor="middle">
    Ar<tspan baseline-shift="super" font-size="0.7em">+</tspan>
  </text>
</g>
```

**Label Placement**:
- Above horizontal arrows: `y = arrow_y - 5`
- Below horizontal arrows: `y = arrow_y + 15`
- Right of vertical arrows: `x = arrow_x + 10`
- Left of vertical arrows: `x = arrow_x - 10`

---

## Panel Layout Patterns

### Side-by-Side Comparison

```xml
<svg viewBox="0 0 800 400">
  <!-- Panel A -->
  <g id="panel-a" transform="translate(0, 0)">
    <text x="15" y="25" class="panel-label">a</text>
    <rect x="50" y="50" width="350" height="300" fill="#FFF9E6" stroke="#2E2E2E"/>
    <!-- Content -->
  </g>

  <!-- Panel B -->
  <g id="panel-b" transform="translate(400, 0)">
    <text x="15" y="25" class="panel-label">b</text>
    <rect x="50" y="50" width="350" height="300" fill="#FFF9E6" stroke="#2E2E2E"/>
    <!-- Content -->
  </g>
</svg>
```

### 2×2 Grid

```xml
<svg viewBox="0 0 800 800">
  <g id="panel-a" transform="translate(0, 0)">
    <text x="15" y="25" class="panel-label">a</text>
    <!-- Content: 370×370 -->
  </g>

  <g id="panel-b" transform="translate(410, 0)">
    <text x="15" y="25" class="panel-label">b</text>
    <!-- Content: 370×370 -->
  </g>

  <g id="panel-c" transform="translate(0, 410)">
    <text x="15" y="25" class="panel-label">c</text>
    <!-- Content: 370×370 -->
  </g>

  <g id="panel-d" transform="translate(410, 410)">
    <text x="15" y="25" class="panel-label">d</text>
    <!-- Content: 370×370 -->
  </g>
</svg>
```

### Sequential Flow (Horizontal)

```xml
<svg viewBox="0 0 1200 400">
  <g id="step-1" transform="translate(0, 0)">
    <text x="15" y="25" class="panel-label">a</text>
    <!-- Step 1 content -->
  </g>

  <!-- Arrow -->
  <line x1="380" y1="200" x2="420" y2="200" stroke="#2E2E2E" stroke-width="4" marker-end="url(#boldArrow)"/>

  <g id="step-2" transform="translate(440, 0)">
    <text x="15" y="25" class="panel-label">b</text>
    <!-- Step 2 content -->
  </g>

  <!-- Arrow -->
  <line x1="820" y1="200" x2="860" y2="200" stroke="#2E2E2E" stroke-width="4" marker-end="url(#boldArrow)"/>

  <g id="step-3" transform="translate(880, 0)">
    <text x="15" y="25" class="panel-label">c</text>
    <!-- Step 3 content -->
  </g>
</svg>
```

---

## Legend & Scale Bar Design

### Legend Placement

**Typical Positions**:
- Top-right corner (most common)
- Bottom-right corner
- Outside panel boundary (for multi-panel)

```xml
<g id="legend" transform="translate(650, 50)">
  <!-- Legend box -->
  <rect x="0" y="0" width="130" height="80" fill="#FFFFFF" stroke="#2E2E2E" stroke-width="0.5" rx="3"/>

  <!-- Legend items -->
  <line x1="10" y1="20" x2="40" y2="20" stroke="#4472C4" stroke-width="2"/>
  <text x="45" y="24" font-size="10">Pristine</text>

  <line x1="10" y1="40" x2="40" y2="40" stroke="#E83845" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="45" y="44" font-size="10">Modified</text>

  <circle cx="25" cy="60" r="5" fill="#F4C542" stroke="#2E2E2E" stroke-width="0.5"/>
  <text x="45" y="64" font-size="10">Au contact</text>
</g>
```

### Scale Bar

```xml
<g id="scale-bar" transform="translate(650, 550)">
  <!-- Bar -->
  <line x1="0" y1="0" x2="50" y2="0" stroke="#2E2E2E" stroke-width="3" stroke-linecap="square"/>

  <!-- End caps -->
  <line x1="0" y1="-3" x2="0" y2="3" stroke="#2E2E2E" stroke-width="3"/>
  <line x1="50" y1="-3" x2="50" y2="3" stroke="#2E2E2E" stroke-width="3"/>

  <!-- Label -->
  <text x="25" y="15" font-size="9" text-anchor="middle">20 nm</text>
</g>
```

---

## Best Practices Summary

### ✅ DO

- Use consistent spacing (grid-based)
- Maintain visual hierarchy (size, weight, color)
- Use sans-serif fonts
- Ensure sufficient contrast (4.5:1 minimum)
- Align elements precisely
- Use semantic colors
- Include accessibility features (title, desc)
- Test at multiple sizes
- Use proper chemical notation

### ❌ DON'T

- Use pure black (`#000000`)
- Overcrowd with too many elements
- Mix too many font sizes
- Use decorative fonts
- Forget subscripts/superscripts in formulas
- Rely solely on color (add labels/patterns)
- Create inconsistent spacing
- Use low-contrast colors for text
- Forget panel labels (a, b, c)

---

## Responsive Sizing

### Viewbox Strategy

```xml
<!-- Flexible sizing -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <!-- Content scales automatically -->
</svg>

<!-- Fixed aspect ratio -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid meet">
  <!-- Maintains 4:3 aspect ratio -->
</svg>
```

**Standard Aspect Ratios**:
- Single panel: 4:3 (800×600) or 16:9 (800×450)
- Side-by-side: 2:1 (800×400)
- Square: 1:1 (600×600)

---

## Print Considerations

### Resolution
- SVG is vector (infinite resolution)
- Rasterized output: **300 DPI minimum**
- Text size: Minimum 8pt (10.67px at 96 DPI)

### Color Space
- Digital: **RGB** (sRGB profile)
- Print: **CMYK** (convert with care)
- Black text: Rich black in CMYK

### Safe Areas
- Leave 0.125" (3.2mm) bleed if required
- Keep text 0.25" (6.4mm) from trim edge

---

*These guidelines ensure professional, publication-ready SVG figures suitable for Nature, Science, Advanced Materials, and similar high-impact journals.*
