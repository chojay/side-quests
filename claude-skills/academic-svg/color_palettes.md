# Academic SVG Color Palettes

Comprehensive color specifications for publication-quality semiconductor process and materials science figures.

## Table of Contents

- [Primary Palette](#primary-palette) - blues/cyans, yellows/golds, pinks/reds, grays, greens, purples, oranges
- [Material-Specific Color Conventions](#material-specific-color-conventions) - standard atomic colors, device stack components
- [Gradient Library](#gradient-library) - depth and concentration gradients
- [Color Accessibility](#color-accessibility) - WCAG contrast ratios, color blindness considerations
- [Color Usage Guidelines](#color-usage-guidelines) - semantic consistency, hierarchy, color count
- [Color Mixing & Opacity](#color-mixing--opacity) - semi-transparent overlays, blending
- [Dark Mode Considerations](#dark-mode-considerations)
- [Export Settings for Different Media](#export-settings-for-different-media) - digital, print, slides
- [Quick Reference: Top 10 Colors](#quick-reference-top-10-colors)
- [Color Swatches SVG](#color-swatches-svg)
- [Alternative: Flexoki Color Palette](#alternative-flexoki-color-palette) - base colors, accents, when to use

---

## Primary Palette

### Blues & Cyans
**Usage**: Oxide dielectrics, conduction bands, electron flow, plasma species

| Color Name | Hex | RGB | SVG | Use Cases |
|------------|-----|-----|-----|-----------|
| Deep Blue | `#4472C4` | 68, 114, 196 | `fill="#4472C4"` | Primary structures, conduction bands (CB), n-doped regions |
| Medium Blue | `#5B9BD5` | 91, 155, 213 | `fill="#5B9BD5"` | Secondary structures, intermediate phases |
| Light Blue | `#7CB5E8` | 124, 181, 232 | `fill="#7CB5E8"` | Oxide layers (SiO2), gate dielectrics, liquid phases |
| Pale Blue | `#B4D7EC` | 180, 215, 236 | `fill="#B4D7EC"` | STI/field oxide, depletion regions, background areas |
| Cyan | `#4EC9E0` | 78, 201, 224 | `fill="#4EC9E0"` | Plasma and ion species (Ar+), implant and diffusion paths |
| Teal | `#00CED1` | 0, 206, 209 | `fill="#00CED1"` | Alternative gas species, wet-clean chemistries |

**Gradients**:
```xml
<linearGradient id="blueDepth" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" style="stop-color:#B4D7EC"/>
  <stop offset="100%" style="stop-color:#4472C4"/>
</linearGradient>
```

---

### Yellows & Golds
**Usage**: Metal gates, gold contact pads, tungsten plugs, active metal regions

| Color Name | Hex | RGB | SVG | Use Cases |
|------------|-----|-----|-----|-----------|
| Bright Yellow | `#FFD966` | 255, 217, 102 | `fill="#FFD966"` | Metal surface highlights |
| Golden Yellow | `#F4C542` | 244, 197, 66 | `fill="#F4C542"` | Gate metal, Au contact pads, W gate fill |
| Deep Gold | `#F0A000` | 240, 160, 0 | `fill="#F0A000"` | Dense metal regions, emphasis |
| Tan/Peach | `#F2D7A9` | 242, 215, 169 | `fill="#F2D7A9"` | Si substrates, buffer layers |
| Cream | `#FFF9E6` | 255, 249, 230 | `fill="#FFF9E6"` | Panel backgrounds, light substrates |
| Beige | `#FAF0E6` | 250, 240, 230 | `fill="#FAF0E6"` | Alternative backgrounds |

**Gradients**:
```xml
<linearGradient id="metalGradient" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" style="stop-color:#FFD966"/>
  <stop offset="100%" style="stop-color:#F4C542"/>
</linearGradient>
```

---

### Pinks & Reds
**Usage**: High-k dielectrics, photoresist, interface regions, critical points, failure modes

| Color Name | Hex | RGB | SVG | Use Cases |
|------------|-----|-----|-----|-----------|
| Light Pink | `#FFB6C1` | 255, 182, 193 | `fill="#FFB6C1"` | High-k films (HfO2, Al2O3), thin film interfaces |
| Hot Pink | `#FF69B4` | 255, 105, 180 | `fill="#FF69B4"` | Photoresist masks, highlighted regions |
| Coral | `#FF7F50` | 255, 127, 80 | `fill="#FF7F50"` | Transition zones, p-doped regions |
| Magenta | `#DC143C` | 220, 20, 60 | `fill="#DC143C"` | Critical defects, failure points |
| Red | `#E83845` | 232, 56, 69 | `fill="#E83845"` | Failure modes, oxygen atoms, warnings |
| Dark Red | `#B22222` | 178, 34, 34 | `fill="#B22222"` | Severe degradation |

**Gradients**:
```xml
<linearGradient id="highkGradient" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" style="stop-color:#FFB6C1"/>
  <stop offset="100%" style="stop-color:#FF69B4"/>
</linearGradient>
```

---

### Grays & Neutrals
**Usage**: Structural supports, metal gates and lines, inactive regions, text

| Color Name | Hex | RGB | SVG | Use Cases |
|------------|-----|-----|-----|-----------|
| Pure White | `#FFFFFF` | 255, 255, 255 | `fill="#FFFFFF"` | Backgrounds, text on dark |
| Off-White | `#FAFAFA` | 250, 250, 250 | `fill="#FAFAFA"` | Figure backgrounds |
| Light Gray | `#D3D3D3` | 211, 211, 211 | `fill="#D3D3D3"` | Inactive regions, Al pads |
| Medium Gray | `#808080` | 128, 128, 128 | `fill="#808080"` | Polysilicon, support structures, voids |
| Dark Gray | `#606060` | 96, 96, 96 | `fill="#606060"` | TiN metal gates, W plugs, metal lines |
| Charcoal | `#404040` | 64, 64, 64 | `fill="#404040"` | Outlines, secondary text |
| Almost Black | `#2E2E2E` | 46, 46, 46 | `fill="#2E2E2E"` | Primary text, main outlines |

**Note**: Avoid pure black (`#000000`) for a more professional, print-friendly appearance.

---

### Greens
**Usage**: Nitride films, protective layers, passivation, organic materials

| Color Name | Hex | RGB | SVG | Use Cases |
|------------|-----|-----|-----|-----------|
| Sage Green | `#8FBC8F` | 143, 188, 143 | `fill="#8FBC8F"` | Nitride spacers (Si3N4), passivation, protective coatings |
| Olive | `#6B8E23` | 107, 142, 35 | `fill="#6B8E23"` | Organic films, anti-reflective coatings |
| Forest Green | `#228B22` | 34, 139, 34 | `fill="#228B22"` | Dense organic phases |
| Mint | `#98FF98` | 152, 255, 152 | `fill="#98FF98"` | Light protective layers |

---

### Purples & Violets
**Usage**: Alternative phases, intermediate states, III-V materials

| Color Name | Hex | RGB | SVG | Use Cases |
|------------|-----|-----|-----|-----------|
| Light Purple | `#9370DB` | 147, 112, 219 | `fill="#9370DB"` | Phase transitions, mixed states |
| Medium Purple | `#8B7BB8` | 139, 123, 184 | `fill="#8B7BB8"` | Alternative phases, Ga atoms |
| Dark Purple | `#6A5ACD` | 106, 90, 205 | `fill="#6A5ACD"` | Specific material types |
| Lavender | `#E6E6FA` | 230, 230, 250 | `fill="#E6E6FA"` | Subtle backgrounds |

---

### Oranges
**Usage**: Accents, highlights, copper interconnects, warnings

| Color Name | Hex | RGB | SVG | Use Cases |
|------------|-----|-----|-----|-----------|
| Orange | `#FF8C00` | 255, 140, 0 | `fill="#FF8C00"` | Highlights, phosphorus dopant atoms |
| Dark Orange | `#FF6600` | 255, 102, 0 | `fill="#FF6600"` | Strong emphasis |
| Burnt Orange | `#CC5500` | 204, 85, 0 | `fill="#CC5500"` | Degradation, heat |
| Peach | `#FFDAB9` | 255, 218, 185 | `fill="#FFDAB9"` | Soft backgrounds |

---

## Material-Specific Color Conventions

### Elements (Standard Atomic Colors)

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| Silicon (Si) | Slate Gray | `#708090` | Si atoms in lattice diagrams |
| Oxygen (O) | Red | `#E83845` | O atoms in oxides |
| Nitrogen (N) | Blue | `#4472C4` | N atoms in nitrides |
| Carbon (C) | Dark Gray | `#2E2E2E` | C atoms, graphene, SiC |
| Hydrogen (H) | Very Light Gray | `#F0F0F0` | H termination, passivation |
| Gallium (Ga) | Medium Purple | `#8B7BB8` | Ga in GaN, GaAs |
| Arsenic (As) | Olive | `#6B8E23` | As in GaAs, n-type dopant |
| Phosphorus (P) | Orange | `#FF8C00` | n-type dopant atoms |
| Boron (B) | Coral | `#FF7F50` | p-type dopant atoms |
| Hafnium (Hf) | Hot Pink | `#FF69B4` | Hf in high-k oxides |
| Titanium (Ti) | Silver-Gray | `#C0C0C0` | Ti adhesion and barrier layers |
| Tungsten (W) | Dark Gray | `#606060` | W plugs, gate fill |
| Copper (Cu) | Orange-Brown | `#B87333` | Cu interconnects |
| Aluminum (Al) | Light Gray | `#D3D3D3` | Al pads and lines |

### Device Stack Components

| Component | Color | Hex | Usage |
|-----------|-------|-----|-------|
| Si substrate | Tan/Peach | `#F2D7A9` | Bulk silicon wafer |
| n+ doped region | Deep Blue | `#4472C4` | Source/drain, n-wells |
| p+ doped region | Coral | `#FF7F50` | p-type source/drain, p-wells |
| Gate oxide (SiO2) | Light Blue | `#7CB5E8` | Thermal and interfacial oxides |
| High-k dielectric (HfO2) | Soft Pink | `#FFB6C1` | ALD high-k films |
| Metal gate (TiN) | Dark Gray | `#606060` | Work-function metals |
| Contact/pad (Au, W) | Golden Yellow | `#F4C542` | Gate fill, contact pads |
| Nitride spacer (Si3N4) | Sage Green | `#8FBC8F` | Spacers, etch-stop liners |
| Photoresist | Hot Pink | `#FF69B4` | Lithographic masks |
| Polysilicon | Medium Gray | `#808080` | Poly gates, local interconnect |
| STI/field oxide | Pale Blue | `#B4D7EC` | Isolation regions |
| Cu interconnect | Orange-Brown | `#B87333` | BEOL metal lines |

---

## Gradient Library

### Depth & Concentration Gradients

**Blue Depth Gradient** (oxide thickness/density):
```xml
<linearGradient id="oxide-depth" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#B4D7EC"/>
  <stop offset="100%" stop-color="#4472C4"/>
</linearGradient>
```

**Dopant Concentration Profile** (falls off away from the implant window):
```xml
<linearGradient id="dopant-profile" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#4472C4"/>
  <stop offset="100%" stop-color="#B4D7EC"/>
</linearGradient>
```

**High-k Film Nucleation** (ALD growth):
```xml
<linearGradient id="highk-growth" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#FFB6C1" stop-opacity="0.8"/>
  <stop offset="100%" stop-color="#FF69B4" stop-opacity="1"/>
</linearGradient>
```

**Temperature Gradient** (cool to hot, e.g. anneal profiles):
```xml
<linearGradient id="temperature" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#4472C4"/>
  <stop offset="50%" stop-color="#FFD966"/>
  <stop offset="100%" stop-color="#E83845"/>
</linearGradient>
```

---

## Color Accessibility

### Contrast Ratios (WCAG Guidelines)

**Minimum Requirements**:
- Normal text: 4.5:1 contrast ratio
- Large text (14pt bold / 18pt): 3:1 contrast ratio
- UI components: 3:1 contrast ratio

### High-Contrast Combinations

✅ **Excellent Contrast** (7:1 or higher):
- `#2E2E2E` (text) on `#FFFFFF` (background): 15.1:1
- `#2E2E2E` (text) on `#FFF9E6` (cream): 13.8:1
- `#FFFFFF` (text) on `#4472C4` (deep blue): 5.9:1

✅ **Good Contrast** (4.5:1 - 7:1):
- `#404040` (text) on `#FAFAFA` (off-white): 9.7:1
- `#FFFFFF` (text) on `#6B8E23` (olive): 4.7:1

⚠️ **Acceptable for Large Text** (3:1 - 4.5:1):
- `#606060` (text) on `#F2D7A9` (peach): 3.8:1

❌ **Insufficient Contrast** (below 3:1):
- `#7CB5E8` (light blue) on `#FFFFFF`: 1.9:1 - DO NOT USE for text

### Color Blindness Considerations

**Deuteranopia (Red-Green)** - Most common:
- Avoid relying solely on red vs. green distinction
- Use blue vs. yellow/orange instead
- Add patterns or labels in addition to color

**Recommended Pairs**:
- Blue (`#4472C4`) + Orange (`#FF8C00`)
- Purple (`#8B7BB8`) + Yellow (`#F4C542`)
- Gray (`#606060`) + Pink (`#FFB6C1`)

**Protanopia & Tritanopia**:
- Maintain high contrast
- Use shape/pattern coding in addition to color

---

## Color Usage Guidelines

### 1. Semantic Consistency
Use the same color for the same material/concept throughout a figure:
```xml
<!-- SiO2 is always light blue -->
<rect fill="#7CB5E8"/> <!-- Gate oxide in panel A -->
<rect fill="#7CB5E8"/> <!-- Gate oxide in panel B -->
```

### 2. Color Hierarchy
- **Primary elements**: Saturated colors (e.g., `#4472C4`, `#F4C542`)
- **Secondary elements**: Desaturated versions (e.g., `#7CB5E8`, `#FFD966`)
- **Background elements**: Very light colors (e.g., `#B4D7EC`, `#F2D7A9`)

### 3. Limit Color Count
- Maximum 5-6 distinct colors per panel
- Use variations (lighter/darker) of same hue rather than new colors
- Monochromatic schemes for single-concept figures

### 4. Background Selection
- **White/Off-white** (`#FAFAFA`): Modern, clean, digital-first
- **Cream** (`#FFF9E6`): Warm, traditional, print-friendly
- **Transparent**: For overlay on other media

### 5. Text Color Selection
- **Dark backgrounds**: White text (`#FFFFFF`)
- **Light backgrounds**: Near-black text (`#2E2E2E`)
- **Colored backgrounds**: Test contrast ratio

---

## Color Mixing & Opacity

### Semi-Transparent Overlays
```xml
<!-- 40% opacity for subtle emphasis -->
<rect fill="#7CB5E8" opacity="0.4"/>

<!-- Alternative: use fill-opacity -->
<rect fill="#7CB5E8" fill-opacity="0.4" stroke="#4472C4" stroke-opacity="1"/>
```

**Recommended Opacity Values**:
- Background regions: 0.1 - 0.3
- Overlapping elements: 0.4 - 0.6
- Active elements: 0.7 - 1.0

### Blending for New Colors
Avoid creating too many colors. Instead, use transparency:
```xml
<!-- Blue + Yellow overlay = Green-ish appearance -->
<rect fill="#4472C4"/>
<rect fill="#F4C542" opacity="0.3"/>
```

---

## Dark Mode Considerations

For dark backgrounds, invert the palette:

| Light Mode | Dark Mode | Hex |
|------------|-----------|-----|
| `#2E2E2E` (text) | `#E0E0E0` (text) | Light gray text |
| `#FAFAFA` (bg) | `#1E1E1E` (bg) | Dark background |
| `#4472C4` (blue) | `#6FA8DC` (lighter blue) | Softer blue |
| `#F4C542` (yellow) | `#FFD966` (lighter yellow) | Softer yellow |

---

## Export Settings for Different Media

### Digital/Screen
- Color space: **RGB**
- Profile: **sRGB IEC61966-2.1**
- Format: **SVG** (vector, scales perfectly)

### Print Publication
- Color space: **CMYK** (convert from RGB)
- Profile: **Coated FOGRA39** (ISO 12647-2:2004)
- Resolution: **300 DPI minimum**
- Black text: Use rich black (`C: 60%, M: 40%, Y: 40%, K: 100%`)

### Presentation/Slides
- High contrast colors
- Avoid subtle color differences
- Test on projector (colors appear duller)
- Larger text sizes

---

## Quick Reference: Top 10 Colors

For quick access, the most frequently used colors:

1. **Deep Blue** - `#4472C4` - Primary structures, n+ regions
2. **Light Blue** - `#7CB5E8` - Oxide (SiO2)
3. **Cyan** - `#4EC9E0` - Plasma and ion species
4. **Golden Yellow** - `#F4C542` - Metal gates and contacts
5. **Soft Pink** - `#FFB6C1` - High-k films
6. **Dark Gray** - `#2E2E2E` - Text/outlines
7. **Medium Gray** - `#808080` - Polysilicon, structures
8. **Red** - `#E83845` - Critical points
9. **Cream** - `#FFF9E6` - Backgrounds
10. **Off-White** - `#FAFAFA` - Figure background

---

## Color Swatches SVG

See `assets/color_swatches.svg` for visual reference of all colors in this palette.

---

## Alternative: Flexoki Color Palette

### Overview

[Flexoki](https://stephango.com/flexoki) is an "inky color scheme for prose and code" designed for digital screens, inspired by analog inks and warm paper tones. It provides an alternative aesthetic for academic figures with a warmer, more organic feel.

### Flexoki Base Colors (Monochromatic)

**For Light Theme Figures**:

| Color Name | Hex | Usage in Academic Figures |
|------------|-----|---------------------------|
| black | `#100F0F` | Primary text, outlines, critical elements |
| base-950 | `#1C1B1A` | Very dark elements, shadows |
| base-900 | `#282726` | Dark structural elements |
| base-600 | `#6F6E69` | Secondary text, annotations |
| base-300 | `#B7B5AC` | Tertiary text, de-emphasized elements |
| base-200 | `#CECDC3` | UI borders, subtle outlines |
| base-150 | `#DAD8CE` | Light UI elements |
| base-100 | `#E6E4D9` | Panel backgrounds |
| base-50 | `#F2F0E5` | Secondary backgrounds |
| paper | `#FFFCF0` | Primary background (warm white) |

**For Dark Theme Figures** (if needed):

| Color Name | Hex | Usage |
|------------|-----|-------|
| black | `#100F0F` | Background |
| base-950 | `#1C1B1A` | Secondary background |
| base-850 | `#343331` | UI elements |
| base-700 | `#575653` | UI borders |
| base-600 | `#6F6E69` | Secondary text |
| base-500 | `#878580` | Primary text |
| paper | `#FFFCF0` | Highlights |

### Flexoki Accent Colors

For semiconductor materials figures, Flexoki accents can be mapped to scientific elements:

| Flexoki Color | Base Hex | Scientific Mapping |
|---------------|----------|-------------------|
| **Red** | `#D14D41` | Oxygen atoms, failure modes, critical warnings |
| **Orange** | `#DA702C` | Copper interconnects, warnings, emphasis |
| **Yellow** | `#D0A215` | Metal gates and contacts (alternative to gold) |
| **Green** | `#879A39` | Nitride spacers, organic films, passivation |
| **Cyan** | `#3AA99F` | Plasma and ion species (alternative) |
| **Blue** | `#4385BE` | Oxide dielectrics, conduction bands |
| **Purple** | `#8B7EC8` | Alternative phases, intermediate states, Ga |
| **Magenta** | `#CE5D97` | High-k films, interface regions |

### When to Use Flexoki

**Advantages**:
- Warmer, more organic aesthetic
- Excellent for presentations (less harsh than pure white)
- Cohesive design system if using Flexoki elsewhere
- Reduced eye strain for extended viewing
- Modern, contemporary feel

**Best For**:
- Presentation slides
- Digital-only publications
- Informal reports or preprints
- Educational materials
- Dark mode figures (excellent dark theme support)

**Consider Primary Palette For**:
- High-impact print journals (Nature, Science)
- Traditional academic publications
- When adhering to strict journal guidelines
- Maximum scientific convention compliance

### Flexoki Usage Example

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <style>
    .flexoki-text { fill: #100F0F; }
    .flexoki-bg { fill: #FFFCF0; }
    .flexoki-metal { fill: #D0A215; }
    .flexoki-oxide { fill: #4385BE; }
    .flexoki-ion { fill: #3AA99F; }
    .flexoki-nitride { fill: #879A39; }
  </style>

  <!-- Warm paper background -->
  <rect width="800" height="600" class="flexoki-bg"/>

  <!-- Content with Flexoki colors -->
  <rect x="100" y="100" width="600" height="50" class="flexoki-metal"/>
  <rect x="100" y="150" width="600" height="80" class="flexoki-oxide"/>

  <text x="400" y="200" class="flexoki-text">Flexoki-styled figure</text>
</svg>
```

### Combining Palettes

You can also combine select Flexoki colors with the primary palette:
- Use Flexoki backgrounds (`paper`, `base-100`) for warmer feel
- Use primary palette for scientific elements (maintains convention)
- Best of both: warm aesthetic + scientific accuracy

---

*Primary color palette derived from analysis of 15 high-quality materials science figures from leading publications (Nature, Science, Advanced Materials, etc.).*

*Flexoki palette: An alternative warm, inky color scheme for modern academic presentations. Source: [stephango.com/flexoki](https://stephango.com/flexoki)*
