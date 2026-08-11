# Gaggiuino Profile Selection by Bean Origin and Character

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-03-03). Wiki links flattened; sources cited inline.

Practical guide for matching [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md) pressure profiles to coffee bean origin, processing method, and roast level. Covers all four primary community profiles - [Londinium](Gaggiuino-Profile-Comparison-Guide.md), Blooming, IUIUIU, and Cremina - with specific parameter recommendations for each origin-profile combination.

---

## The Core Framework: What Determines Profile Selection

Profile selection follows a hierarchy. Each factor narrows down your options:

```
1. ROAST LEVEL (most important)
   ↓
2. PROCESSING METHOD (second most important)
   ↓
3. ALTITUDE / BEAN DENSITY (affects pre-infusion and temperature)
   ↓
4. ORIGIN (fine-tunes temperature and ratio)
```

**The single most important rule:**
- Light roast = Blooming or IUIUIU
- Medium roast = Londinium or IUIUIU
- Medium-dark to dark = Londinium or Cremina

Processing method and origin refine *which variant* of that profile to use and which parameters to dial.

---

## Profile Quick Reference

| Profile | Roast Range | Peak Pressure | Total Time | Ratio | Temperature |
|---------|------------|---------------|------------|-------|-------------|
| **Blooming** | Light to medium-light | 6-9.5 bar | 45-65s | 1:2.5-1:3 | 93-96C |
| **IUIUIU** | Light to medium | 7.5 bar | 25-45s (med) / 45-116s (light) | 1:2-1:2.1 | 93-94C |
| **Londinium** | Medium to medium-dark | 8-9 bar, declining | 25-35s | 1:2 | 91-94C |
| **Cremina** | Medium-dark to dark | Spring-lever curve | 40-60s | 1:1.5-1:2.2 | 78-90C |

---

## Origin-by-Origin Guide

### Ethiopia

Ethiopia produces the most diverse coffee in the world. The processing method determines the profile more than origin alone - washed and natural Ethiopian are essentially different beasts.

#### Washed Ethiopian (Yirgacheffe, Sidamo Washed, Gedeo)

**Flavor character:** Clean floral aromatics, jasmine, bergamot, lemon zest, light tea-like body, bright citrus acidity. Very high clarity.

**Profile: Blooming Espresso (primary)**

Washed Ethiopians are the canonical use case for the blooming profile. Scott Rao himself cites washed Kenyan and Ethiopian as the beans that made him develop the blooming approach, achieving extraction yields of 29%. The dense cellular structure of high-altitude washed beans (Yirgacheffe grows at 1700-2200 MASL) requires longer contact time to extract evenly. The bloom pause also allows CO2 trapped in freshly roasted dense beans to escape before main extraction begins.

Without blooming, washed Ethiopian tends to taste bright but thin - under-extracted sourness dominates. With blooming, the same bean produces sweetness, florals, and a clean juicy finish.

| Parameter | Value |
|-----------|-------|
| Profile | Blooming |
| Temperature | 93-94C |
| Ratio | 1:2.5 (18g in, 45g out) |
| Bloom Duration | 25-30s |
| Total Time | 50-65s |
| Pre-infusion | 5s at 4 ml/s to 5-7 bar |
| Extraction Phase | 2 ml/s, declining pressure |
| Grind | Fine - denser than medium roast setting |

**Alternate profile: Blooming Allonge**

For Yirgacheffe roasted extremely light (Nordic-style), the allonge variant gives filter-like clarity:
- Ratio: 1:3-1:4
- Temperature: 94-95C
- Debit: 4.5 ml/s
- Pressure: Should not exceed 6 bar
- Time: 45-60s

**Why not Londinium for washed Ethiopian?**
Londinium at 1:2 ratio with 25-35s total time under-extracts washed Ethiopian light roasts. The result is sour, thin, and highlights acidity without sweetness. Londinium extracts 19-22% - washed light roasts need 25-29% to taste balanced.

**Temperature note:** Washed Ethiopians generate more fines than most origins, which means the puck compacts easily. If shots run too slow, grind coarser rather than lowering temperature. Start at 93C rather than 95C for medium-light roasts.

---

#### Natural Ethiopian (Harrar, Sidamo Natural, Guji Natural, Jimma Natural)

**Flavor character:** Big berry jam, wine-like sweetness, blueberry, dark fruit, heavier body, syrupy texture. Less clarity than washed but more intensity.

**Profile: IUIUIU (primary) or Blooming**

Natural Ethiopians have a different extraction challenge than washed. The dried fruit sugars coating the bean during the natural process create a sweeter, heavier bean that extracts body easily - but that heavy fruit character can become cloying or fermented-tasting if over-extracted. IUIUIU's moderate peak pressure (7.5 bar) and staged extraction allows the fruit to come through without turning muddy.

Blooming also works well, but natural Ethiopians often taste better at slightly lower extraction yields than washed varieties. If using Blooming, stay closer to 1:2.5 than 1:3.

| Parameter | IUIUIU | Blooming |
|-----------|--------|---------|
| Temperature | 91-92C | 91-93C |
| Ratio | 1:2-1:2.1 (18g/36g) | 1:2.5 (18g/45g) |
| Peak Pressure | 7.5 bar | 6-9 bar |
| Pre-infusion | 11s at 4 bar | 5s at 4 ml/s |
| Bloom/Pause | None | 25-30s |
| Total Time | 35-50s | 50-65s |

**Why slightly lower temperature for natural?**
Natural processed beans are less dense than washed (the drying process with fruit intact creates a slightly different cellular structure) and already contain more accessible sugars. A degree or two lower temperature (91-92C vs 93-94C) reduces the risk of the heavy fruit notes turning bitter or over-extracted.

**Flavor target:** Milk chocolate, blueberry jam, winey body - not fermented sourness or muddy fruit.

---

### Kenya (SL28, SL34)

**Flavor character:** Bold, wine-forward acidity (blackcurrant, raspberry, tomato, citrus), full velvety body, black tea finish. Kenya SL28 tends toward sharper citrus; SL34 adds caramel sweetness and rounder body. Both are almost exclusively washed.

**Profile: Blooming (primary), IUIUIU (alternate)**

Kenyan coffees are Scott Rao's cited example of why he developed the blooming profile - he achieved 29% extraction yields and calls them "some of the most memorable espresso shots of my life." The high acidity of SL28/SL34 benefits from the high extraction the bloom provides, which converts brightness into sweetness and rounds sharp edges.

The important principle: Kenyan acidity at low extraction (19-21%, Londinium range) tastes jagged and overwhelming. At high extraction (25-29%, Blooming range), that same acidity becomes complex, sweet, and wine-like.

| Parameter | Value |
|-----------|-------|
| Profile | Blooming |
| Temperature | 93-94C |
| Ratio | 1:2.5 (18g in, 45g out) |
| Bloom Duration | 25-30s |
| Total Time | 55-65s |
| Extraction Phase | 2 ml/s |

**Ratio note for Kenyan:** Some baristas push toward 1:3 with Kenyan to tame the bold acidity. Aim for sweetness and juiciness without sharpness - if the shot tastes acidic and aggressive, increase ratio by 5g at a time until it rounds out.

**IUIUIU as alternate:** For Kenyan roasted to medium (rather than light), IUIUIU at 93C and 1:2 ratio extracts the fruit-forward character with more body. Use IUIUIU when you want a thicker, more espresso-like texture with the Kenyan fruit notes rather than the juicy blooming clarity.

---

### Colombia

Colombia's versatility makes it the most forgiving single origin for espresso. Colombian beans span a wide roast range and respond well to multiple profiles. The washed processing and varied altitude (1200-2300 MASL) means Colombia accommodates both Londinium and Blooming depending on roast level.

#### Washed Colombian Medium (Huila, Nariño, Antioquia)

**Flavor character:** Brown sugar, orange peel, caramel, mild apple acidity, silky body. Clean and balanced without being complex.

**Profile: Londinium (primary)**

Medium-roast Colombian washed is the classic Londinium daily driver material. The declining pressure curve extracts the brown sugar sweetness and caramel body that makes medium Colombian so satisfying without pulling bitter compounds. Community consensus (per Kozikow blog and Gaggiuino Discord) places Brazilian and Colombian medium roasts as the primary use case for Londinium.

| Parameter | Value |
|-----------|-------|
| Profile | Londinium |
| Temperature | 92-93C |
| Ratio | 1:2 (18g in, 36g out) |
| Pre-infusion | 3-5s at 0.3-3 bar |
| Peak Pressure | 8-9 bar, declining to 6 |
| Total Time | 25-35s |

---

#### Washed Colombian Medium-Light (Light side of medium)

**Flavor character:** More fruit expression - nectarine, lime, grape, with milk chocolate notes still present. Depending on the specific micro-lot, can approach washed Ethiopian character.

**Profile: IUIUIU (primary) or Blooming**

At medium-light roast levels, Colombian responds better to IUIUIU than Londinium. IUIUIU's 11s pre-infusion at 4 bar and 7.5 bar peak pressure gives the denser light-side-of-medium beans more time to hydrate and extract evenly. The result is balanced fruit clarity plus enough body to feel like espresso rather than coffee.

Blooming is valid for the lighter end of this range - if the bag says "light" rather than "medium-light," default to Blooming.

| Parameter | Value |
|-----------|-------|
| Profile | IUIUIU |
| Temperature | 93-94C |
| Ratio | 1:2-1:2.1 (18g in, 36-38g) |
| Pre-infusion | 11s at 4 bar |
| Peak Pressure | 7.5 bar |
| Total Time | 35-50s |

---

### Brazil

Brazil is the world's largest coffee producer. Most Brazilian specialty espresso beans are natural or pulped-natural (honey) process, medium roast, lower altitude (600-1200 MASL) compared to East Africa. This makes Brazil the most forgiving espresso origin and the ideal Londinium daily driver.

**Flavor character:** Milk chocolate, hazelnut, brown sugar, low-to-medium acidity, syrupy body. Excellent crema. Very little fruit expression.

**Profile: Londinium (primary)**

Brazilian medium natural is the textbook Londinium profile bean. The community quote "For a typical Brazilian medium roast, the Londinium profile ended up working the best" sums up the consensus. The lower density of natural-process beans (dried fruit creates a different cellular structure than washed) means shorter pre-infusion times are needed and lower peak temperature works well.

| Parameter | Value |
|-----------|-------|
| Profile | Londinium |
| Temperature | 90-92C |
| Ratio | 1:2 (18g in, 36g out) |
| Pre-infusion | 3-5s (shorter - beans are softer) |
| Peak Pressure | 8-9 bar, declining |
| Total Time | 25-30s |

**Why lower temperature for Brazilian?**
Lower altitude = lower density beans. The cellular structure is less compact than high-altitude East African beans, which means less heat is needed to extract properly. Brazilian natural at 93-94C risks over-extraction and bitterness. 90-92C extracts the chocolate and sweetness without turning harsh.

**Brazil as blend component:** Brazilian naturals are the backbone of most espresso blends (Italian-style blends) because they provide body and crema with low acidity. Blends with Brazilian + Ethiopian component (like Onyx Delta Spirit) work well at 92-93C with Londinium.

---

### Central America (Guatemala, Costa Rica, Honduras)

Central American coffees bridge the fruit clarity of East Africa and the chocolate body of South America. Profile selection depends heavily on processing method, which varies more in Central America than anywhere else.

#### Guatemala Washed (Huehuetenango, Antigua, Acatenango)

**Flavor character:** Stone fruit (peach, nectarine), caramel, milk chocolate, medium acidity. Huehuetenango tends toward floral/fruity; Antigua toward chocolate/nut.

**Profile: IUIUIU (primary) or Londinium (medium-dark roast)**

Guatemala washed is the documented bean for the original IUIUIU Classic profile from Mor's Visualizer shots (Guatemala Huehuetenango La Bolsa, medium roast: vanilla, carob, nutmeg, milk chocolate, caramel, berry). IUIUIU at 1:2 ratio, 93C produces smooth syrupy shots with balanced fruit and body.

For Guatemala roasted to true medium-dark, Londinium works well at 91-92C.

| Parameter | IUIUIU (Medium) | Londinium (Med-Dark) |
|-----------|-----------------|----------------------|
| Temperature | 93C | 91-92C |
| Ratio | 1:2 (18g/36g) | 1:2 (18g/36g) |
| Total Time | 30-45s | 25-35s |
| Peak Pressure | 7.5 bar | 8-9 bar declining |

---

#### Costa Rica / Central America Honey Process

**Flavor character:** Yellow honey = floral, sweet, light. Red honey = caramel, stone fruit, round. Black honey = fermented fruit, heavy body.

**Profile: Processing determines profile**

The key insight for honey process: the more mucilage left on the bean (yellow < red < black), the closer the bean behaves to a natural-process bean for profile purposes.

| Honey Level | Behaves Like | Profile |
|-------------|-------------|---------|
| Yellow Honey | Washed but sweeter | IUIUIU or Blooming |
| Red Honey | Middle ground | IUIUIU |
| Black Honey | Natural-process | IUIUIU or Londinium |

For any honey process at medium roast, IUIUIU is the universal safe choice. Its 11s pre-infusion handles the variable density of honey-process beans, and 7.5 bar peak pressure avoids over-extracting the fruit sugars into bitterness.

| Parameter | Value |
|-----------|-------|
| Profile | IUIUIU |
| Temperature | 92-93C (yellow/red honey) / 91-92C (black honey) |
| Ratio | 1:2-1:2.1 |
| Total Time | 30-45s |

---

### Indonesia and Sumatra

**Flavor character:** Heavy body, thick oily texture, earthy, mushroom, cedar, cedar, low acidity. Often described as "love it or hate it." Wet-hulled processing (Giling Basah) creates a distinctive high-moisture bean that dries differently from washed or natural.

**Profile: Londinium (primary) or Cremina**

Indonesian and Sumatran beans are soft, low-density, and easily over-extracted. High pressure (9 bar constant) and long extraction times produce bitterness and harsh earthy notes rather than the smooth richness Sumatra is known for. The declining pressure of Londinium suits these beans - high initial pressure builds body, declining pressure avoids late bitter extraction.

Community experience with Sumatra Mandheling specifically indicates 88C brew temperature is optimal, which aligns with softer beans needing less heat.

| Parameter | Value |
|-----------|-------|
| Profile | Londinium |
| Temperature | 88-90C (lower than most origins) |
| Ratio | 1:1.8-1:2 (18g in, 32-36g out) |
| Pre-infusion | 2-4s (very short - beans are very soft/porous) |
| Peak Pressure | 8-9 bar, declining to 6 |
| Total Time | 25-30s |

**Warning about pre-infusion:** Sumatra's wet-hulled beans are extremely porous and soft. Long pre-infusion (as in IUIUIU's 11s) risks over-saturating the puck and causing channeling. Keep pre-infusion short and rely on the declining pressure curve to do the work.

**Cremina as alternative:** For a more traditional heavy-bodied extraction, Cremina Lever at 88-90C replicates the old Italian lever-style shot that suits dark-roast Indonesian coffees well.

**Do not use Blooming for Sumatra.** High extraction (25-29%) with earthy, low-acid beans produces intensely bitter, muddy shots. Blooming is designed for bright acidic beans that need higher extraction to balance.

---

### Gesha / Geisha (Panama, Colombia, Ethiopia)

**Flavor character:** Tea-like delicacy, jasmine florals, bergamot, tropical fruit, bright stone fruit acidity, extremely light body. Considered the world's most complex coffee variety. High altitude (1500-1900 MASL), dense beans, typically washed processing.

**Profile: Blooming (required)**

Gesha is the case where Blooming is essentially non-negotiable. The delicacy of the flavor profile means under-extraction (which any lower-extraction profile risks with this dense bean) produces thin, flat shots. The blooming profile's 25-29% extraction yield unlocks complexity that would otherwise remain locked in the bean.

At lower extraction, Gesha often tastes like diluted tea - pleasant but not representative of what the variety offers. At blooming extraction levels, you get the full floral-tropical-jasmine expression.

| Parameter | Value |
|-----------|-------|
| Profile | Blooming |
| Temperature | 92-93C (slightly lower than standard light - delicate florals are heat-sensitive) |
| Ratio | 1:2.5 (18g in, 45g out) |
| Bloom Duration | 30s |
| Total Time | 55-65s |
| Pre-infusion | 5s at 4 ml/s |
| Extraction | 2 ml/s flow, declining pressure |

**Why 92-93C rather than 95-96C for Gesha?**
Unlike other light roasts where higher temperature helps extract dense beans, Gesha's floral compounds (jasmine, bergamot) are temperature-sensitive aromatics. Brewing at 95-96C mutes these florals and shifts the profile toward generic brightness. 92-93C preserves the complex aromatics while still achieving the extraction needed.

**Ratio note:** Do not pull Gesha at 1:2. The thin body at 1:2 combined with high acidity produces an unbalanced shot. 1:2.5 minimum; 1:3 if the shot still tastes sharp or acidic.

---

## Processing Method Mapping

When you don't know origin or have minimal information, processing method is a reliable shortcut to profile selection:

### Washed Process

**Bean characteristics:** Higher density, lower body, cleaner acidity, brighter flavor clarity. Needs more extraction to reveal sweetness. Pre-infusion benefits from more time due to density.

| Roast | Profile | Temperature | Ratio | Pre-Infusion |
|-------|---------|-------------|-------|--------------|
| Light | Blooming | 93-95C | 1:2.5-1:3 | 5s at 4 ml/s |
| Medium-Light | IUIUIU | 93-94C | 1:2-1:2.5 | 11s at 4 bar |
| Medium | Londinium | 92-93C | 1:2 | 4-6s |
| Medium-Dark | Londinium | 91-92C | 1:2 | 3-5s |

---

### Natural Process

**Bean characteristics:** Lower density than washed (fruit sugars already accessible), heavier body, fruit-forward sweetness, less clarity. Extracts quickly - shorter pre-infusion, lower temperature to avoid bitterness.

| Roast | Profile | Temperature | Ratio | Pre-Infusion |
|-------|---------|-------------|-------|--------------|
| Light | IUIUIU or Blooming | 91-92C | 1:2-1:2.5 | 8-11s at 4 bar |
| Medium | Londinium | 90-92C | 1:2 | 3-5s |
| Medium-Dark | Londinium | 88-91C | 1:1.8-1:2 | 3-4s |
| Dark | Cremina | 88-90C | 1:1.5-1:2 | 2-4s |

---

### Honey Process

**Bean characteristics:** Intermediate between washed and natural. Yellow honey behaves closer to washed; black honey closer to natural. Consistent sweetness, medium body, reduced acidity vs washed.

| Honey Level | Profile | Temperature | Ratio | Notes |
|-------------|---------|-------------|-------|-------|
| Yellow Honey | Blooming or IUIUIU | 92-94C | 1:2-1:2.5 | Treat like medium-light washed |
| Red Honey | IUIUIU | 92-93C | 1:2-1:2.1 | Universal safe choice |
| Black Honey | IUIUIU or Londinium | 91-92C | 1:2 | More like natural; watch temperature |

---

### Anaerobic Process

**Flavor character:** Intense tropical fruit, heavy fermentation notes, wine-like sweetness, unique acidity. Can taste like rum or tropical punch when well-roasted.

**Profile: IUIUIU (primary)**

Anaerobic coffees have intense fermentation-derived esters that can easily tip into harsh or overwhelming territory. IUIUIU's moderate peak pressure (7.5 bar) and controlled staged extraction prevents over-extraction of these intense compounds while still achieving high enough extraction (22-26%) to balance the intensity.

Avoid Blooming with anaerobic coffees at full 1:2.5-1:3 ratios - the very high extraction can make the fermentation character taste medicinal or harsh. If using Blooming, stay at 1:2.5 maximum and lower temperature to 91-92C.

| Parameter | Value |
|-----------|-------|
| Profile | IUIUIU |
| Temperature | 91-92C (lower than standard to prevent harsh fermentation notes) |
| Ratio | 1:2-1:2.1 |
| Total Time | 30-45s |
| Peak Pressure | 7.5 bar |

---

## Bean Density and the Physics of Extraction

Understanding why density matters explains everything about profile selection:

### The Density Spectrum

```
DENSER beans ←--------------------→ SOFTER beans

High altitude    Low altitude
Washed           Natural
Light roast      Dark roast
Ethiopia/Kenya   Brazil/Indonesia
```

**Dense beans:** Compact cellular structure resists water penetration. Need more energy: higher temperature, longer pre-infusion, and sometimes higher pressure.

**Soft beans:** Porous structure allows water to penetrate easily. Too much energy causes over-extraction: lower temperature, shorter pre-infusion, lower pressure.

### Pre-infusion Time by Bean Density

From Papel Espresso's bean hardness research:

| Bean Type | Examples | Pre-infusion Time |
|-----------|---------|-------------------|
| Very hard / dense | High-altitude washed (Ethiopia, Kenya) | 10-14 seconds |
| Medium-hard | Mid-altitude washed (Colombia, Guatemala) | 6-9 seconds |
| Softer | Natural processed, lower-altitude (Brazil) | 4-7 seconds |
| Very soft / porous | Italian-style dark blends, Sumatra | 2-5 seconds |

### Temperature by Density

| Bean Characteristic | Temperature Range |
|--------------------|------------------|
| Very dense, high-altitude washed light roast | 94-96C |
| Dense, washed medium-light | 93-94C |
| Medium density, washed medium | 92-93C |
| Natural medium | 90-92C |
| Soft, dark roast | 88-91C |
| Indonesian / Sumatra | 88-90C |

**The physics:** Dense beans require more heat because their intact cellular structure has lower solubility - compounds that would dissolve easily in softer beans need more thermal energy to release. Conversely, dark-roasted brittle beans are extremely porous; high heat just burns them.

---

## The "Unknown Bean" Decision Tree

When you get a new bag with no profile guidance, work through these steps:

### Step 1: Assess Roast Level (Visual)

Look at the beans under good light:
- **Light:** No oils, tan-to-light brown, obvious roast cracking detail, 1-21 days from roast date
- **Medium:** Dry surface, medium brown, minimal oils, some surface texture
- **Medium-dark:** Slight oil sheen starting, darker brown, smoother surface
- **Dark:** Visible oils, dark brown to nearly black, very smooth surface

The roast date is equally important. Most specialty light roasts are consumed 7-21 days off roast. A "light" roast 45 days off roast has already off-gassed significantly - reduce bloom time.

### Step 2: Check Processing on the Bag

Look for: Washed / Fully Washed / Wet Process = washed; Natural / Dry Process / Sun-dried = natural; Honey / Pulped Natural = honey; Anaerobic = anaerobic.

If no processing information is given, assume washed for East African beans (Ethiopia, Kenya, Rwanda) and natural or pulped natural for Brazilian beans.

### Step 3: Select Starting Profile

```
Roast Level Assessment
│
├── LIGHT
│   ├── Washed → Blooming (93-94C, 1:2.5, 50-65s)
│   ├── Natural → IUIUIU (91-92C, 1:2, 35-50s)
│   └── Honey → Blooming or IUIUIU (92-93C, 1:2-1:2.5)
│
├── MEDIUM-LIGHT
│   ├── Washed → IUIUIU (93-94C, 1:2-1:2.5, 35-50s)
│   ├── Natural → IUIUIU (91-93C, 1:2, 30-45s)
│   └── Honey → IUIUIU (92-93C, 1:2, 30-45s)
│
├── MEDIUM
│   ├── Washed → Londinium (92-93C, 1:2, 25-35s)
│   ├── Natural → Londinium (90-92C, 1:2, 25-30s)
│   └── Honey → IUIUIU (91-93C, 1:2, 25-40s)
│
├── MEDIUM-DARK
│   └── Any process → Londinium (90-92C, 1:2, 25-35s)
│
└── DARK
    └── Any process → Cremina (88-90C, 1:1.5-1:2, 30-45s)
```

### Step 4: Dial In Parameters

Start with grind as the primary variable. Target ratio by weight (not time). Adjust in this order:

1. **Grind size** (primary) - too slow = too fine; too fast = too coarse
2. **Ratio** - if bitter, increase yield by 5g; if sour, decrease yield or check grind
3. **Temperature** - adjust last; ±1C has real impact on flavor

For Blooming specifically: if the shot tastes flat despite correct grind, extend bloom duration to 30s. If it tastes over-extracted (bitter), reduce ratio from 1:2.5 toward 1:2.

### Step 5: Adjust Based on Taste

| Taste Problem | Diagnosis | Fix |
|--------------|-----------|-----|
| Sour / sharp | Under-extracted | Finer grind, or increase ratio (more yield), or extend bloom |
| Bitter / harsh | Over-extracted | Coarser grind, or lower temperature (1-2C), or reduce pre-infusion time |
| Flat / thin | Under-extracted | Finer grind, or switch from Londinium to Blooming/IUIUIU |
| Muddy / heavy fruit | Over-extracted natural | Lower temperature (1-2C), coarser grind |
| Too fruity / fermented | Anaerobic over-extracted | Lower temperature, coarser grind, reduce ratio |
| Tea-like but too thin | Gesha under-extracted | More Blooming extraction - increase ratio to 1:3 |

---

## Master Parameters Table

Consolidated reference for all origin-profile combinations:

| Origin | Process | Roast | Profile | Temp | Ratio | Time | Notes |
|--------|---------|-------|---------|------|-------|------|-------|
| Ethiopian Yirgacheffe | Washed | Light | Blooming | 93-94C | 1:2.5 | 50-65s | Classic Blooming use case |
| Ethiopian Harrar | Natural | Light | IUIUIU | 91-92C | 1:2 | 35-50s | Lower temp for fruit density |
| Ethiopian (any) | Natural | Medium-light | IUIUIU | 92C | 1:2 | 30-40s | |
| Kenyan SL28/SL34 | Washed | Light | Blooming | 93-94C | 1:2.5-1:3 | 55-65s | Bold acidity needs high EY |
| Kenyan | Washed | Medium | IUIUIU | 93C | 1:2 | 30-45s | When you want more body |
| Colombian | Washed | Medium-Light | IUIUIU | 93-94C | 1:2 | 35-50s | |
| Colombian | Washed | Medium | Londinium | 92-93C | 1:2 | 25-35s | Daily driver friendly |
| Brazilian | Natural | Medium | Londinium | 90-92C | 1:2 | 25-30s | Lower temp, shorter PI |
| Brazilian | Pulped Natural | Medium | Londinium | 90-92C | 1:2 | 25-30s | Same as natural |
| Guatemalan Huehue | Washed | Medium | IUIUIU | 93C | 1:2 | 30-45s | Documented IUIUIU origin |
| Guatemala | Washed | Medium-Dark | Londinium | 91-92C | 1:2 | 25-35s | |
| Costa Rica | Yellow Honey | Medium | IUIUIU | 92-93C | 1:2 | 30-40s | |
| Costa Rica | Black Honey | Medium | Londinium | 91-92C | 1:2 | 25-35s | More like natural |
| Sumatran | Wet-Hulled | Medium | Londinium | 88-90C | 1:1.8-1:2 | 25-30s | Short PI, lower temp |
| Sumatran | Wet-Hulled | Med-Dark | Cremina | 88-90C | 1:1.5-1:2 | 30-45s | |
| Gesha (Panama/Colombia) | Washed | Light | Blooming | 92-93C | 1:2.5 | 55-65s | Lower temp than other lights |
| Anaerobic (any origin) | Anaerobic | Medium | IUIUIU | 91-92C | 1:2 | 30-40s | Avoid Blooming with anaerobics |
| Italian Blend | Blend | Dark | Cremina | 88-90C | 1:1.5-1:2 | 30-45s | |

---

## Altitude Reference

Altitude is a shortcut for density. If you know altitude from the bag:

| Altitude | Bean Density | Pre-infusion | Temperature Tendency |
|---------|-------------|--------------|---------------------|
| 1400+ MASL (very high) | Hard / dense | 10-14s | Higher (93-96C) |
| 1000-1400 MASL (high) | Medium-hard | 6-9s | Mid (92-94C) |
| 600-1000 MASL (medium) | Medium | 4-7s | Lower (90-93C) |
| Below 600 MASL (low) | Soft | 2-5s | Lower (88-91C) |

Most East African beans (Ethiopia, Kenya, Rwanda) grow at 1400-2200 MASL - the hardest category. Most Central American specialty coffee grows at 1200-1800 MASL. Brazilian and Indonesian beans are typically 600-1200 MASL.

---

## Cremina Profile Notes

The Cremina Lever (by Johnyez, available in GaggiMate) mimics the Olympia Cremina lever machine's spring-lever curve. The wide temperature range (78-90C) allows significant tuning:

- **78-82C:** Very dark Italian blends, espresso Robusta blends
- **83-87C:** Dark single origins, French-roast level Arabica
- **88-90C:** Medium-dark, Indonesian, dark natural process

For medium-dark beans, start at 89-90C with Cremina. Lower if the shot tastes harsh or over-extracted. The 1:1.5-1:2.2 ratio range accommodates both traditional ristretto-style (1:1.5) and modern single-origin dark (1:2.2) approaches.

---

## Sources

- [Espresso Aficionados - Profiling Guide](https://espressoaf.com/guides/profiling.html)
- [Scott Rao - Best Practice Espresso Profile](https://www.scottrao.com/blog/2021/5/18/best-practice-espresso-profile)
- [Decent Espresso - Scott Rao Blooming Masterclass](https://decentespresso.com/blog/scott_rao_masterclass_on_blooming_espresso_filter_3_and_what_about_quakers)
- [Decent Espresso - 5 Profiles for Light Roasted Beans](https://decentespresso.com/blog/5_espresso_profiles_for_light_roasted_coffee_beans)
- [Decent Espresso - 5 Profiles for Medium Roasted Beans](https://decentespresso.com/blog/5_profiles_for_medium_roasted_beans)
- [Papel Espresso - Pre-Infusion Times by Bean Hardness](https://www.papelespresso.com/how-pre-infusion-times-change-based-on-coffee-bean-hardness/)
- [Papel Espresso - Bean Origin and Espresso Body](https://www.papelespresso.com/the-role-of-coffee-bean-origin-in-espresso-body-and-texture/)
- [Papel Espresso - Gaggiuino Programmed Profiles](https://www.papelespresso.com/maximizing-workflow-efficiency-with-gaggiuinos-programmed-profiles/)
- [Visualizer.coffee - IUIUIU Classic (Mor)](https://visualizer.coffee/shots/5f387d8f-9141-4c31-93b4-2a1db7058a77)
- [Home-Barista - Espresso Brewing Parameters Sumatra](https://www.home-barista.com/coffees/espresso-brewing-parameters-for-sumatra-mandheling-t91572.html)
- [Home-Barista - Suggested Espresso Parameters for Gesha](https://www.home-barista.com/tips/suggested-espresso-parameters-for-gesha-t35397.html)
- [Espresso Outlet - Best Temperature for Light/Medium/Dark Roasts](https://espressooutlet.com/blogs/news/best-extraction-temperature-range-for-light-medium-and-dark-roasts)
- [BrewClan Coffee - Mastering Pressure Profiling](https://brewclancoffee.com/blogs/specialty-coffee-guide/mastering-pressure-profiling-in-espresso-extraction)
- [Sipn Coffee - Why Pressure Profiles Transform Extraction](https://sipncoffee.com/pressure-variations-espresso-extraction-technique/)
- [Kozikow Blog - Gaggiuino Build Log](https://kozikow.blog/2024/02/22/gaggiuino-build-log/)
- [GaggiMate Profiles Documentation](https://docs.gaggimate.eu/docs/profiles/)
- [Via Guatemala - Honey Process Explained](https://viaguatemalacoffee.com/blogs/articles/honey-process-coffee-levels-explained)
- [1Zpresso - Anaerobic Coffee Guide](https://1zpresso.coffee/a-guide-to-anaerobic-coffee/)

---

## Related Notes

- [Gaggiuino-Profile-Comparison-Guide](Gaggiuino-Profile-Comparison-Guide.md) - Londinium vs Blooming vs IUIUIU deep dive
- [Gaggiuino-Popular-Community-Profiles-Research](../research-notes/Gaggiuino-Popular-Community-Profiles-Research.md) - Full community profile catalog with all variants
- [Gaggiuino-Pressure-Profiling-Extraction-Parameters](Gaggiuino-Pressure-Profiling-Extraction-Parameters.md) - IUIUIU and Blooming technical parameters
- [Bloom-Profile-Troubleshooting-Fast-Extraction](../troubleshooting/Bloom-Profile-Troubleshooting-Fast-Extraction.md) - Diagnostic guide for Blooming issues
- [Gaggiuino-Modification-Overview](../machine/Gaggiuino-Modification-Overview.md) - Gaggiuino features and capabilities

---

*Created: 2026-03-03*
*Confidence: High - Based on Espresso Aficionados guide, Scott Rao documentation, GaggiMate profiles, community research, Papel Espresso technical guides, and vault synthesis*
