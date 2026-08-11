# Gaggiuino Profile Comparison Guide

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-02-13). Wiki links flattened; sources cited inline.

Side-by-side comparison of the core [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md) extraction profiles: **Londinium (Lever)**, **Blooming**, and **IUIUIU**. Explains what each profile does, why it works, and when to use which.

---

## At a Glance

| | Londinium (Lever) | Blooming | IUIUIU |
|---|---|---|---|
| **Inventor/Origin** | Replicates Londinium lever machines ($4,000+) | Scott Rao for Decent Espresso | Community member **Mor** (Decent/Gaggiuino) |
| **Best Roast Level** | Medium to medium-dark | Light to medium-light | Medium (sweet spot), light (ok) |
| **Total Time** | 25-35s | 45-65s | 25-45s (medium), 45-116s (light) |
| **Ratio** | 1:2 | 1:2 to 1:3 | 1:1.9-1:2.1 |
| **Peak Pressure** | 8-9 bar | 6-9.5 bar | 7.5 bar |
| **Temperature** | 93-94C | 93-96C | 93-94C |
| **Key Feature** | Declining pressure curve | 25-30s bloom pause | Three-phase staged extraction |
| **Extraction Yield** | 19-22% | 25-29% | 22-26% |
| **Complexity to Dial In** | Low | Medium | Medium |
| **GaggiMate Pre-loaded** | Yes | Yes | Via SproFiler/Discord |

---

## How Each Profile Works

### Londinium (Lever) Profile

The Londinium profile mimics spring-lever espresso machines where a spring mechanically pushes water through the puck. Pressure naturally declines as the spring extends - the machine cannot maintain constant pressure.

```
Pressure (bar)
 9 ┤         ╭──╮
 8 ┤        ╭╯  ╰──╮
 7 ┤       ╱       ╰──╮
 6 ┤      ╱            ╰──╮
 5 ┤     ╱                 ╰──
 4 ┤    ╱
 3 ┤───╯
 2 ┤
 1 ┤
   └────────────────────────────
   0    5   10   15   20   25  sec

   ├─ PI ─┤─ Ramp ─┤─ Decline ─┤
```

**Phase breakdown:**

| Phase | Time | Pressure | What Happens |
|-------|------|----------|--------------|
| **Pre-infusion** | 0-5s | 0.3-3 bar | Low-pressure puck saturation |
| **Peak/Ramp** | 5-15s | Rising to 8-9 bar | Main extraction begins, builds body |
| **Decline** | 15-30s | 8.5 → 6 bar | Gradual pressure drop, sweetness develops |

**Why the decline matters:** As pressure drops, extraction slows. Early in the shot (high pressure), you extract bright acids and fruity compounds. Late in the shot (lower pressure), you extract sweetness and body without pulling bitter compounds. The natural deceleration acts as a built-in "don't over-extract" mechanism.

**Result in the cup:** Thick body, balanced sweetness, traditional espresso character with good crema. The shot has a rounded, full-bodied quality without the harshness of constant 9-bar extraction.

---

### Blooming Profile

Developed by **Scott Rao**, blooming introduces a radical idea: **stop water flow entirely** in the middle of extraction to let CO2 escape from the coffee puck.

```
Pressure (bar)                          Flow (ml/s)
 9 ┤                                     4 ┤──╮
 8 ┤                     ╭──╮            3 ┤  │
 7 ┤                    ╱    ╰──╮        2 ┤  │               ╭───────
 6 ┤──╮               ╱         ╰──╮     1 ┤  ╰╮              │
 5 ┤  ╰╮             ╱              ╰──  0 ┤   ╰──────────────╯
 4 ┤   │            ╱                        0  5  10 ···30 35 ···60
 3 ┤   │           ╱
 2 ┤   ╰──╮      ╱
 1 ┤      ╰─────╯
   └────────────────────────────────────
   0  5  10 ···  30  35  40  50  60  sec

   ├PI┤── BLOOM (0 flow) ──┤─ Extract ─┤
```

**Phase breakdown:**

| Phase | Time | Pressure/Flow | What Happens |
|-------|------|---------------|--------------|
| **Pre-infusion** | 0-5s | 4 ml/s to 5-7 bar | Fast fill, puck saturates |
| **Bloom pause** | 5-35s | Pressure declines to ~1-2 bar, **0 flow** | Water flow STOPS. CO2 trapped in freshly roasted coffee escapes. Puck fully hydrates. |
| **Extraction** | 35-65s | Gradual ramp to 5-9 bar, then decline at ~2 ml/s | Main extraction at controlled flow |

**Why the bloom pause matters:** Freshly roasted coffee (7-21 days) contains significant CO2. In a traditional shot, this gas creates uneven channels - water finds paths of least resistance, leaving dry spots under-extracted. The 25-30 second pause lets gas escape, so when extraction resumes the water contacts the puck evenly across its entire surface.

**Result in the cup:** Dramatically higher extraction yields (25-29% vs 19-21% traditional). More sweetness and clarity from light roasts. Flavors that would be thin and sour with traditional extraction become complex and juicy. The trade-off is a longer total shot time and the requirement for very fresh beans (stale beans have already off-gassed, so bloom adds nothing).

---

### IUIUIU Profile

Created by community member **Mor**, IUIUIU takes a middle path - it doesn't pause like blooming, but it doesn't ramp aggressively like lever profiles. Instead, it uses **three deliberate phases** with lower-than-traditional peak pressure.

```
Pressure (bar)
 9 ┤
 8 ┤
 7 ┤                 ╭───╮
 6 ┤                ╱     ╰──╮
 5 ┤               ╱          ╰──╮
 4 ┤──────────────╯               ╰──
 3 ┤
 2 ┤             ╭╯
 1 ┤
   └────────────────────────────────────
   0    5   10   15   20   25   30  sec

   ├─── PI (4 bar) ──┤ Ramp ┤ Decline ┤
```

**Phase breakdown:**

| Phase | Time | Pressure | What Happens |
|-------|------|----------|--------------|
| **Pre-infusion** | 0-11s | Steady 4 bar | Extended low-pressure saturation. Flow ~3 ml/s. Puck hydrates thoroughly. |
| **Ramp-up** | 11-18s | 2.3 → 7.5 bar | Gradual increase. Flow maintained at ~3 ml/s with deliberate mid-extraction reduction. |
| **Plateau/Decline** | 18-25+s | Stabilizes ~6 bar, then gradual decline | Similar to lever-style ending. Sweetness develops. |

**Why 7.5 bar (not 9) matters:** Traditional 9-bar extraction was optimized for medium-dark Italian roasts. Lighter, more soluble specialty coffees extract too aggressively at 9 bar, pulling bitter and astringent compounds. By capping at 7.5 bar, IUIUIU extracts at a gentler pace - achieving higher total yields without the harshness.

**Why the long pre-infusion matters:** 11 seconds at 4 bar (vs 3-5 seconds in traditional shots) ensures the puck is fully saturated before main extraction begins. This reduces channeling and produces a more even extraction without needing a full bloom pause.

**Result in the cup:** Clean, balanced shots with good body and clarity. Less dramatic than blooming but more forgiving to dial in. Works across a wider range of roast levels than either Londinium (too aggressive for light) or Blooming (overkill for medium).

---

## The Core Differences Explained

### 1. Pressure Strategy

Each profile has a fundamentally different philosophy about how pressure should behave:

| Profile | Pressure Philosophy |
|---------|---------------------|
| **Londinium** | "Start high, let gravity do the work" - mimics a spring lever naturally losing force |
| **Blooming** | "Pause and reset" - interrupt extraction to improve puck conditions before the real pull |
| **IUIUIU** | "Build gradually, never push too hard" - extended gentle start, moderate peak, gentle decline |

### 2. Pre-infusion Approach

Pre-infusion is where the biggest philosophical divergence occurs:

| | Londinium | Blooming | IUIUIU |
|---|---|---|---|
| **Duration** | 3-5s (short) | 5s fill + 25-30s pause | 11s (extended) |
| **Pressure** | 0.3-3 bar | 5-7 bar spike then 0 | Steady 4 bar |
| **Flow** | Low, continuous | Fill then **STOP** | Low, continuous |
| **Purpose** | Quick wet, get to work | Degassing + full saturation | Thorough saturation |

### 3. Extraction Yield

The profiles achieve fundamentally different extraction levels:

| Profile | Typical Yield | Why |
|---------|---------------|-----|
| **Londinium** | 19-22% | Traditional extraction, efficient but not maximal |
| **IUIUIU** | 22-26% | Extended pre-infusion + moderate pressure = more complete extraction |
| **Blooming** | 25-29% | Bloom pause + extended time = highest possible extraction |

Higher yield isn't always better - dark roasts at 27% extraction taste bitter. But light roasts at 19% extraction taste sour. The profile must match the bean.

### 4. Channeling Resistance

Channeling (water finding paths of least resistance through the puck) is the enemy of good espresso:

| Profile | Channeling Resistance | Why |
|---------|----------------------|-----|
| **Londinium** | Moderate | Short pre-infusion means puck may have dry spots |
| **IUIUIU** | High | 11s pre-infusion saturates puck thoroughly |
| **Blooming** | Highest | Bloom pause allows complete, even hydration |

### 5. Forgiveness Factor

How much room for error in your puck prep and grind:

| Profile | Forgiveness | Notes |
|---------|-------------|-------|
| **Londinium** | Most forgiving | Works well even with imperfect puck prep. Declining pressure naturally compensates. |
| **IUIUIU** | Moderate | Longer pre-infusion helps, but still sensitive to grind size |
| **Blooming** | Least forgiving | Requires excellent puck prep (WDT, paper filters recommended). Bad prep = channeling after bloom. |

---

## Decision Tree: Which Profile to Use

```
What roast level?
│
├── Dark (Italian, French)
│   └── Use: Londinium or Cremina Lever
│       Temp: 88-91C | Ratio: 1:1.5-1:2 | Time: 25-35s
│
├── Medium-Dark
│   └── Use: Londinium
│       Temp: 91-93C | Ratio: 1:2 | Time: 25-35s
│
├── Medium
│   ├── Want body + chocolate? → Londinium (93-94C)
│   └── Want clarity + fruit?  → IUIUIU (93C)
│       Both at 1:2 ratio
│
├── Medium-Light
│   ├── Easy dial-in? → IUIUIU (93-94C, 1:2)
│   └── Maximum flavor? → Blooming (93-95C, 1:2.5)
│
└── Light / Nordic
    ├── Standard light → Blooming (94-96C, 1:2.5-1:3)
    └── Ultra-light filter roast → Turbo/Allonge (93-95C, 1:3-1:5)
```

---

## Profile Parameters Reference Table

### For 18g dose (standard)

| Parameter | Londinium | Blooming | IUIUIU |
|-----------|-----------|----------|--------|
| **Dose** | 18g | 18g | 17.5-18g |
| **Yield** | 36g | 45-54g | 35-36g |
| **Ratio** | 1:2 | 1:2.5-1:3 | 1:2 |
| **Temperature** | 93-94C | 93-96C | 93-94C |
| **Peak Pressure** | 8-9 bar | 6-9.5 bar | 7.5 bar |
| **Pre-infusion** | 3-5s at 0.3-3 bar | 5s at 4 ml/s | 11s at 4 bar |
| **Bloom/Pause** | None | 25-30s (0 flow) | None |
| **Extraction Phase** | Declining 9→6 bar | 2 ml/s flow, declining | Ramp to 7.5, decline to 4 bar |
| **Total Time** | 25-35s | 45-65s | 25-45s |
| **Stop Condition** | Weight (36g) | Weight (45-54g) | Weight (35-36g) |

### Equipment Recommendations by Profile

| | Londinium | Blooming | IUIUIU |
|---|---|---|---|
| **WDT** | Recommended | Required | Required |
| **Bottom Paper Filter** | Optional | Highly recommended | Recommended |
| **Top Paper Filter** | Optional | Optional | Recommended |
| **Bluetooth Scale** | Recommended | Highly recommended | Recommended |
| **Basket** | Standard 18g | Precision (IMS/VST) | Precision (IMS/VST) |

---

## Onyx Coffee Lab Profile Pairings

| Onyx Blend | Recommended Profile | Why |
|------------|---------------------|-----|
| **Geometry** (Expressive Light) | Blooming or IUIUIU | Light enough for bloom benefit, IUIUIU for easier dial-in |
| **Monarch** (Expressive Dark) | Londinium | Dark roast + declining pressure = traditional body without bitterness |
| **Tropical Weather** (Expressive Light) | Blooming | Dual-process Ethiopian benefits most from bloom degassing |
| **Southern Weather** (Light) | IUIUIU | Chocolate notes preserved at moderate extraction |

---

## Common Mistakes by Profile

### Londinium Mistakes
| Mistake | Symptom | Fix |
|---------|---------|-----|
| Using on light roasts | Sour, thin shots | Switch to Blooming or IUIUIU |
| Temperature too high | Bitter, ashy | Lower to 91-93C for darker beans |
| Grind too fine | Pressure spikes >10 bar | Coarsen grind; profile needs flow |

### Blooming Mistakes

For a full diagnostic guide, see [Bloom-Profile-Troubleshooting-Fast-Extraction](../troubleshooting/Bloom-Profile-Troubleshooting-Fast-Extraction.md).

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Stale beans (>30 days) | No benefit from bloom | Use beans 7-21 days off roast |
| Bad puck prep | Channeling after bloom pause | WDT + bottom paper filter |
| Using on dark roasts | Bitter, over-extracted | Switch to Londinium or Cremina |
| Bloom too short (<20s) | Incomplete degassing | Extend bloom to 25-30s |
| Ratio too low (1:2) | Sour with light roasts | Increase to 1:2.5 or 1:3 |

### IUIUIU Mistakes
| Mistake | Symptom | Fix |
|---------|---------|-----|
| Expecting 9 bar | Adjusting profile upward | Trust 7.5 bar peak - it's intentional |
| Grind too coarse | Fast, weak shot | Grind finer; extended PI needs resistance |
| Skipping pre-infusion | Uneven extraction | The 11s PI is the key differentiator |

---

## Historical Context

### Why 9 Bar Became "Standard"

In the 1940s, Achille Gaggia's lever machines produced ~8-9 bar through spring pressure. This worked well with the medium-dark Italian roasts of the era. As pump machines replaced levers, manufacturers locked in 9 bar as a constant. For 60 years, espresso recipes were built around this single pressure point.

### Why Profiling Changes Everything

Pressure profiling (via [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md), Decent, La Marzocco Linea Mini) decouples pressure from the pump's fixed output. This means:

1. **Roast-matched extraction** - dark roasts don't need (and suffer from) 9 bar; light roasts need different pressure curves entirely
2. **Time as a variable, not a rule** - "25-30 seconds" was for constant 9-bar machines. With profiling, 12-116 seconds are all valid depending on the profile
3. **Weight over time** - stop by target weight, not by the clock

> "1:2 in 30s is not a rule to be strictly adhered to."
> - [Espresso Aficionados](https://espressoaf.com/guides/profiling.html)

---

## Sources

- [GaggiMate Profiles Documentation](https://docs.gaggimate.eu/docs/profiles/)
- [Espresso Aficionados Profiling Guide](https://espressoaf.com/guides/profiling.html)
- [Scott Rao - Best Practice Espresso Profile](https://www.scottrao.com/blog/2021/5/18/best-practice-espresso-profile)
- [Kozikow Blog - Gaggiuino Build Log](https://kozikow.blog/2024/02/22/gaggiuino-build-log/)
- [Visualizer.coffee - IUIUIU Classic Shot](https://visualizer.coffee/shots/d6c2a292-a45a-48b5-835f-65065260b69f)
- [SproFiler - IUIUIU Gaggiuino Profile](https://sprofiler.io/shot/9df583a5-ae90-41d1-9904-02fc185701f3)
- [Decent Espresso - Blooming Espresso Masterclass](https://decentespresso.com/blog/scott_rao_masterclass_on_blooming_espresso_filter_3_and_what_about_quakers)
- [Coffee Ad Astra - Adaptive Profile](https://coffeeadastra.com/2020/12/31/an-espresso-profile-that-adapts-to-your-grind-size/)

---

## Related Notes

- [Gaggiuino-Default-Profile-Curves-Reference](Gaggiuino-Default-Profile-Curves-Reference.md) - Visual pressure/flow curves with exact phase parameters from JSON source
- [Gaggiuino-Profile-Selection-by-Bean-Origin-and-Character](Gaggiuino-Profile-Selection-by-Bean-Origin-and-Character.md) - Profile selection by origin, processing method, roast level - Ethiopian, Kenyan, Brazilian, Colombian, Gesha, and more; unknown bean decision tree
- [Gaggiuino-Modification-Overview](../machine/Gaggiuino-Modification-Overview.md) - What Gaggiuino is and its features
- [Gaggiuino-Popular-Community-Profiles-Research](../research-notes/Gaggiuino-Popular-Community-Profiles-Research.md) - Full community profile catalog
- [Gaggiuino-Pressure-Profiling-Extraction-Parameters](Gaggiuino-Pressure-Profiling-Extraction-Parameters.md) - IUIUIU and blooming deep dive
- [Gaggiuino-Custom-Profiles-Import-Guide](Gaggiuino-Custom-Profiles-Import-Guide.md) - How to import/export JSON profiles
- [Gaggiuino-Post-Install-Operation-Guide](../machine/Gaggiuino-Post-Install-Operation-Guide.md) - Daily operation guide
