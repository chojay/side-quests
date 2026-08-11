# Gaggiuino Top 10 Profiles - Community Ranked

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-02-16). Wiki links flattened; sources cited inline.

The most recommended espresso profiles for the [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md) mod, drawn from Reddit (r/espresso, r/gaggiaclassic), Home-Barista, the Gaggiuino Discord, Decent Espresso community, and Espresso Aficionados. Each profile includes community rationale, reviews, and limitations.

For profile mechanics (how Londinium/Blooming/IUIUIU work), see [Gaggiuino-Profile-Comparison-Guide](Gaggiuino-Profile-Comparison-Guide.md).
For importing profiles, see [Gaggiuino-Custom-Profiles-Import-Guide](Gaggiuino-Custom-Profiles-Import-Guide.md).

---

## At a Glance - All 10 Profiles

| # | Profile | Best Roast | Difficulty | Body | Clarity | EY% | Time | Best For |
|---|---------|-----------|------------|------|---------|-----|------|----------|
| 1 | **Londinium** | Medium-dark | Easy | High | Medium | 19-22% | 25-35s | Daily driver, milk drinks |
| 2 | **Blooming** | Light | Hard | Medium | High | 25-29% | 45-65s | Max extraction, light roasts |
| 3 | **IUIUIU** | Medium | Medium | Med-High | Med-High | 22-26% | 25-45s | Versatile sweet spot |
| 4 | **Turbo** | Any (best light) | Easy | Low | Highest | 22-25% | 15-20s | Quick, clean, forgiving |
| 5 | **Allonge** | Ultra-light | Easy | Low | Very High | 21-23% | 30-40s | Filter-like fruit bomb |
| 6 | **Slayer-Style** | Medium | Medium | High | Medium | 20-24% | 30-45s | Sweet, syrupy shots |
| 7 | **Cremina Lever** | Dark | Medium | Very High | Low | 18-21% | 25-45s | Traditional Italian |
| 8 | **Adaptive v2** | Med-light | Advanced | Medium | Med-High | 22-26% | 26-40s | Minimizing bean waste |
| 9 | **Extractamundo Dos** | Light | Medium | Low-Med | High | 23-27% | 17-53s | Forgiving turbo+bloom hybrid |
| 10 | **Flat 9-Bar** | Dark | Easiest | Highest | Low | 18-21% | 25-30s | Baseline, milk drinks, beginners |

---

## 1. Londinium (Lever)

> *Replicates a $4,000+ Londinium lever machine's spring-driven declining pressure.*

**Creator:** Decent Espresso "4 Mothers" framework
**Pre-loaded:** Yes (GaggiMate)

| Parameter | Value |
|-----------|-------|
| Temperature | 93-94C |
| Ratio | 1:2 |
| Time | 25-35s |
| Peak Pressure | 8-9 bar → declining to 6 bar |
| Pre-infusion | 3-5s at 0.3-3 bar |

**How it works:** Pressure peaks at 8-9 bar then naturally declines - mimicking a spring lever losing force. Early extraction pulls bright acids; later extraction at lower pressure develops sweetness without bitterness.

**Community says:**
- The most recommended starting profile for Gaggiuino
- "Master this before you venture to more complicated profile programming" - Decent docs
- Thick body, balanced sweetness, traditional espresso character
- Most forgiving of imperfect puck prep - declining pressure naturally compensates

**Limitations:** Light roasts taste sour/thin. Not enough extraction power for Nordic-style coffees.

**Bean pairings:** Delta Spirit, Sermon, Intelligentsia Black Cat, any medium blend

---

## 2. Blooming (Scott Rao)

> *Stops water flow entirely mid-shot to let CO2 escape, then resumes for dramatically higher extraction.*

**Creator:** Scott Rao for Decent Espresso
**Pre-loaded:** Yes (GaggiMate)

| Parameter | Value |
|-----------|-------|
| Temperature | 93-96C |
| Ratio | 1:2.5-1:3 |
| Time | 45-65s |
| Peak Pressure | 6-9.5 bar |
| Bloom Pause | 25-30s at 0 flow |

**How it works:** Fast fill → 25-30s pause (zero flow, CO2 escapes) → controlled extraction at ~2 ml/s. The pause eliminates channeling caused by trapped gas, allowing water to contact the puck evenly.

**Latest evolution - Best Practice Profile (BPP):** Rao's refinement adds pressurized bloom (maintains puck integrity) and flow-profiled extraction (automatic channel healing). Recipe: 4.0 ml/s fill at 98C for 25s until 4.0 bar → 30s pause at 0 ml/s → ramp to 2.2 ml/s → hold until target weight. 20g in, 50-55g out, 60-65s.

**Community says:**
- "You are not really Gaggiuino-ing if you are not trying to extract light roasts with bloom profile"
- 25-29% extraction yields - far beyond traditional espresso
- Transforms sour, thin light-roast shots into sweet, complex, juicy ones
- Requires excellent puck prep (WDT + paper filter recommended)

**Limitations:** Least forgiving profile. Stale beans (>30 days) gain nothing from bloom. Dark roasts over-extract. Long shot time.

**Bean pairings:** Geometry, Anasora Natural Espresso, any light SO

---

## 3. IUIUIU

> *Three-phase staged extraction with lower peak pressure - the versatile middle ground.*

**Creator:** Community member **Mor** (Decent/Gaggiuino)
**Pre-loaded:** Via SproFiler/Discord

| Parameter | Value |
|-----------|-------|
| Temperature | 93-94C |
| Ratio | 1:2 |
| Time | 25-45s |
| Peak Pressure | 7.5 bar |
| Pre-infusion | 11s at steady 4 bar |

**How it works:** Extended pre-infusion at 4 bar (11s) → gradual ramp to 7.5 bar → plateau → gentle decline. Never hits 9 bar. The long pre-infusion saturates the puck thoroughly without needing a full bloom pause.

**Community says:**
- Clean, balanced shots with good body and clarity
- More forgiving than Blooming, more extractive than Londinium
- Works across the widest range of roast levels
- The 7.5 bar cap prevents the over-extraction harshness of constant 9-bar

**Limitations:** Less dramatic results than Blooming for light roasts. Less body than Londinium for dark roasts. Jack of all trades, master of none.

**Bean pairings:** Kenya Thuti Espresso, Southern Weather, medium-light SOs

---

## 4. Turbo Shot

> *Coarse grind, low pressure, fast shot - maximum clarity in minimum time.*

**Creator:** Popularized by Decent/Rao/Gagne communities
**Pre-loaded:** Build manually or Discord

| Parameter | Value |
|-----------|-------|
| Temperature | 90-95C |
| Ratio | 1:2.5-1:3 (15g in, 40-45g out) |
| Time | 15-20s |
| Pressure | 6 bar target |
| Flow | 7-8 ml/s (full open) |
| Grind | Coarse - closer to fine drip/Aeropress |
| Dose | 15g (lower than typical 18g) |

**How it works:** Full-open flow at coarse grind. Pressure spikes to ~6 bar briefly then naturally sags as the coarse puck offers less resistance. Shot completes in 15-20 seconds. The philosophy: high flow + low pressure + coarse grind = fast extraction of desirable solubles without harsh over-extraction.

**Community says:**
- "Repeatable, forgiving, and very high flavor clarity"
- Espresso Aficionados calls it the "best bet for getting to tasty quickly"
- Less bitterness by extracting fewer bitter compounds at lower pressure
- Most forgiving of imperfect puck prep
- Less coffee waste (15g vs 18g dose)

**Limitations:** Body feels thin to traditional espresso drinkers. Not ideal for milk drinks (lacks intensity). Some find it more like concentrated filter coffee. Grinder quality matters more - needs even particle distribution at coarser settings.

**Bean pairings:** Works across all roasts. Particularly good with light SOs where you want transparency.

---

## 5. Allonge (Rao Allonge)

> *Constant flow, long pull, filter-like clarity - the fruit bomb profile.*

**Creator:** Scott Rao, documented with Decent Espresso
**Pre-loaded:** Build manually or Discord

| Parameter | Value |
|-----------|-------|
| Temperature | 93-96C |
| Ratio | 1:4-1:5 (18g in, 72-90g out) |
| Time | 30-40s |
| Pressure | 4-6 bar (naturally achieved) |
| Flow | 4.5 ml/s constant |
| Grind | Slightly coarser than standard espresso |

**How it works:** Set constant flow at 4.5 ml/s. Pressure settles naturally at 4-6 bar. Pull until 1:4 or 1:5 ratio. The long pull at moderate pressure produces tea-like clarity with espresso sweetness.

**Community says:**
- Decent docs: "best for ultralight roasts, fruity or natural beans, and easiest to dial in"
- "A fruit bomb espresso" with filter-like sweetness
- Great gateway for filter coffee drinkers trying espresso
- Easiest profile to dial in for light roasts

**Limitations:** Large drink volume (72-90g) - not a small concentrated shot. Not suitable for milk drinks. Medium/dark roasts taste flat. Some find the drink "too big."

**Bean pairings:** Ultra-light Nordics, fruity naturals, Tropical Weather (Allonge variant)

---

## 6. Slayer-Style

> *Ultra-slow pre-infusion replicating the $10,000+ Slayer machine's signature sweetness.*

**Creator:** Adapted from Slayer Espresso commercial machines. Papel Espresso documented the Gaggiuino implementation.
**Pre-loaded:** Build manually or Discord

| Parameter | Value |
|-----------|-------|
| Temperature | 92-95C |
| Ratio | 1:2-1:2.5 |
| Time | 30-45s |
| Pre-infusion Flow | 1-2 ml/s (very slow) for 10-15s |
| Main Pressure | 9 bar (or variant: 3 bar hold → ramp to 9 bar) |
| Optional Decline | Taper to 6 bar at end |

**How it works:** The signature is the *very slow* pre-infusion (1-2 ml/s vs the typical 3-4 ml/s). This gentle soaking saturates the puck more thoroughly than standard pre-infusion. After puck saturation (detected by back-pressure rise), optional brief soak at zero flow, then ramp to 9 bar for main extraction.

**Community says:**
- "Exceptionally sweet, balanced, and syrupy espresso"
- Papel Espresso: "one of the most coveted techniques now accessible through this modification"
- Noticeably sweeter than flat 9-bar or standard lever profiles
- Makes your Gaggia taste like a $10,000 Slayer

**Limitations:** Pre-infusion is "not as efficient at soaking the puck evenly" as Blooming (per Espresso Aficionados). Less effective with very light roasts. Requires careful flow calibration - too fast and you lose the Slayer effect.

**Bean pairings:** Medium single-origins, traditional blends. Great for showcasing Streetlevel or Little Brother.

---

## 7. Cremina Lever

> *Emulates the Olympia Cremina spring lever - maximum syrupy body.*

**Creator:** Adapted by community member **Johnyez**
**Pre-loaded:** GaggiMate docs sample download

| Parameter | Value |
|-----------|-------|
| Temperature | 88-92C |
| Ratio | 1:1.5-1:2 |
| Time | 25-45s |
| Pressure | Spring lever curve, calibrated to ~6 bar peak |

**How it works:** Replicates the Olympia Cremina spring lever variant - spring calibrated to 6 bar max (vs Londinium's 9 bar peak). Lower peak pressure with a longer, gentler decline produces thick, syrupy shots with minimal bitterness from dark roasts.

**Community says:**
- Best profile for dark roasts and traditional Italian blends
- Very high body, thick crema
- The lower 6 bar peak (vs Londinium's 9) is gentler on dark roasts

**Limitations:** Light/medium roasts under-extract. Lowest clarity of any profile. Niche use case.

**Bean pairings:** Friar Minor, Buena Vista, Bronson

---

## 8. Adaptive v2 (Gagne)

> *Automatically adjusts to your grind size - minimizes bean waste while dialing in.*

**Creator:** Jonathan Gagne (astrophysicist, coffeeadastra.com)
**Pre-loaded:** Needs adaptation from Decent format

| Parameter | Value |
|-----------|-------|
| Temperature | 92-95C |
| Ratio | 1:2-1:3 |
| Time | 26-40s (user-stopped) |
| Peak Pressure | 8-9 bar |
| Flow | Maintains ~2.0-2.7 ml/s (auto-adapts) |

**How it works:** After preinfusion and initial 8.6 bar peak, it scans through sequential flow-rate steps (3.5 ml/s → 0.5 ml/s) with exit triggers, finding the step matching current extraction flow rate. Effectively maintains constant flow regardless of grind adjustments. Grind changes shift extraction along "a family of good-tasting recipes" rather than producing defective shots.

**Community says:**
- "Solves the \#1 frustration in espresso: wasting beans while dialing in"
- "Best espresso when well-dialed in" - Decent light roast guide
- The most technically sophisticated common profile
- Hard to build, easy to use (once configured)

**Limitations:** Complex to implement on Gaggiuino - the 20-step sequential flow approach is Decent-native and needs simplification. Not beginner-friendly conceptually. "Coarser grinds seem to do better" which may produce thinner shots.

**Bean pairings:** Medium-light SOs where you don't want to waste 3-4 shots dialing in.

---

## 9. Extractamundo Dos

> *Turbo + bloom hybrid - "so forgiving it has become a North Star" for the Decent community.*

**Creator:** JoeD (Southern California), documented at Pocket Science Coffee
**Pre-loaded:** Needs adaptation from Decent format

| Parameter | Value |
|-----------|-------|
| Temperature | ~85C starting, declining 4-6C during shot |
| Ratio | 1:3 (18g in, 54g out) |
| Time | 17-53s |
| Peak Pressure | 5 bar |
| Flow | Fill at 8 ml/s, then limited to ~3.8 ml/s |
| Bloom | 2 seconds at zero flow (mini-bloom) |
| Grind | Coarse (turbo regime) |

**How it works:** Combines three techniques: coarse grind (turbo), mini-bloom (2s pause for CO2 escape), and flow restriction (~3.8 ml/s cap that mimics a gicleur). Starts at unusually low 85C with temperature declining 4-6C during the shot. The flow limiter prevents increasing flow as solubles diminish.

**Community says:**
- Pocket Science Coffee: "so forgiving it has become kind of a North Star" for DE1 users
- Eliminated over 1% harshness in extraction compared to non-bloom turbo versions
- Enhanced flavor separation noted by multiple users
- Combines the best of turbo (speed, clarity) with bloom (evenness)

**Limitations:** Developed for SSP 98HU high-extraction burrs - may need ratio adjustment for DF64 stock burrs. The large temperature drop is unusual. Flow-limiting may not translate perfectly to Gaggiuino. Water chemistry matters more (high alkalinity + low general hardness optimal).

**Bean pairings:** Light roasts, beans with slight off-flavors you want to minimize.

---

## 10. Flat 9-Bar (Classic)

> *The original espresso profile - what every non-profiling machine does. Your baseline reference.*

**Creator:** Achille Gaggia (1948), replicated in every pump machine since
**Pre-loaded:** Yes (default/stock)

| Parameter | Value |
|-----------|-------|
| Temperature | 88-92C |
| Ratio | 1:1.5-1:2 |
| Time | 25-30s |
| Pressure | Constant 9 bar |
| Pre-infusion | 2-3s |

**How it works:** Brief pre-infusion → constant 9 bar throughout. No decline, no taper, no flow profiling. This is what your Gaggia did before the Gaggiuino mod.

**Community says:**
- "Master this before you venture to more complicated profile programming" - Decent
- Classified as "a simplified (and less good) version of the Lever profile"
- Some beans (Italian blends, dark roasts) genuinely taste best at flat 9 bar
- Good for milk drinks where body and intensity need to punch through

**Limitations:** Light roasts "fall apart quickly and channel." Lowest extraction yield. Constant high pressure over-extracts bitter compounds late in the shot. No mechanism to compensate for channeling. This is the profile Gaggiuino was built to move beyond.

**Bean pairings:** Dark Italian blends, Lavazza, Illy. Use when you want maximum body for lattes.

---

## Bonus: Honorable Mentions

### Modified Dipper
A middle ground between flat 9-bar and Blooming. Quick fill → hold at 2-3 bar for 5-20 seconds → ramp to 7-8 bar. Espresso Aficionados recommends it when Blooming "falls apart" for certain beans. More body than Turbo, more texture than Allonge.

### Gentle & Sweet
Decent DE1 beginner profile. Never exceeds 6 bar. Slow decline from 6→4 bar. Produces smooth, sweet, safe shots but lacks complexity. Good introduction to "why 9 bar isn't always best."

### Sprover / Filter 2.0
Makes filter coffee from your espresso machine. Paper filter in the portafilter, 1.5 bar pressure, 1:10-1:16 ratio, 2-minute bloom. Scott Rao rates it "9 out of 10." Replaces a pour-over setup entirely. Not espresso, but worth knowing your Gaggiuino can do this.

---

## Decision Tree: Which Profile for What?

```
What kind of shot do you want today?
│
├── Quick & clean (15-20s)
│   └── TURBO - coarse grind, 6 bar, 1:2.5-1:3
│
├── Classic espresso (25-35s)
│   ├── Medium roast → LONDINIUM (declining 9→6 bar)
│   ├── Dark roast → CREMINA (declining 6→4 bar) or FLAT 9-BAR
│   └── Sweet & syrupy → SLAYER-STYLE (slow pre-infusion)
│
├── Light roast showcase (40-65s)
│   ├── Maximum extraction → BLOOMING (25-29% EY)
│   ├── Balanced sweet spot → IUIUIU (22-26% EY)
│   └── Forgiving turbo hybrid → EXTRACTAMUNDO DOS
│
├── Filter-like clarity
│   ├── Espresso volume (30-40ml) → TURBO
│   ├── Long pull (72-90ml) → ALLONGE (1:4-1:5)
│   └── Full cup of filter → SPROVER / FILTER 2.0
│
└── Minimize waste while dialing in
    └── ADAPTIVE v2 (auto-adjusts to grind)
```

---

## Profile Progression Path

```
Start here:
  FLAT 9-BAR → Learn workflow, puck prep, basic dialing in

Then:
  LONDINIUM → Your daily driver. Learn declining pressure.

Explore:
  IUIUIU → Versatile. Try medium-light beans.
  TURBO → Quick, clean. Try coarser grind + lower dose.

Advanced:
  BLOOMING → Light roasts. This is why you built the Gaggiuino.
  ALLONGE → Ultra-light/Nordic. Filter-like clarity.
  SLAYER → Sweet, syrupy medium roasts.

Expert:
  ADAPTIVE v2 → Auto-adjusting extraction.
  EXTRACTAMUNDO DOS → Turbo+bloom hybrid for maximum forgiveness.
```

---

## Where to Download Profiles

| Source | URL | Notes |
|--------|-----|-------|
| **Gaggiuino Discord** | [discord.gg/gaggiuino](https://discord.com/invite/gaggiuino-890339612441063494) | #profiles channel - primary source, 21,000+ members |
| **ShotProfiles.com** | [shotprofiles.com](https://shotprofiles.com/) | Profile database for GaggiMate/Gaggiuino |
| **GaggiMate Docs** | [docs.gaggimate.eu/docs/profiles/](https://docs.gaggimate.eu/docs/profiles/) | Sample profiles with downloads |
| **SproFiler** | [sprofiler.io](https://sprofiler.io/) | Shot recording + profile sharing (Early Access) |
| **Visualizer.coffee** | [visualizer.coffee](https://visualizer.coffee/) | Decent community, cross-compatible |

For import instructions, see [Gaggiuino-Custom-Profiles-Import-Guide](Gaggiuino-Custom-Profiles-Import-Guide.md).

---

## Sources

### Frameworks & Theory
- [Espresso Aficionados Profiling Guide](https://espressoaf.com/guides/profiling.html)
- [Decent Espresso - 4 Mothers Theory](https://decentespresso.com/docs/the_4_mothers_a_unified_theory_of_espresso_making_recipes)
- [Decent - 5 Profiles for Light Roasts](https://decentespresso.com/blog/5_espresso_profiles_for_light_roasted_coffee_beans)
- [Decent - 5 Profiles for Medium Roasts](https://decentespresso.com/blog/5_profiles_for_medium_roasted_beans)

### Profile Creators
- [Scott Rao - Best Practice Espresso Profile](https://www.scottrao.com/blog/2021/5/18/best-practice-espresso-profile)
- [Scott Rao - Decent Coffee Shots / Filter 2.0](https://www.scottrao.com/blog/2021/9/28/decent-coffee-shots)
- [Scott Rao Masterclass - Blooming & Filter 3](https://decentespresso.com/blog/scott_rao_masterclass_on_blooming_espresso_filter_3_and_what_about_quakers)
- [Coffee ad Astra - Adaptive Profile (Gagne)](https://coffeeadastra.com/2020/12/31/an-espresso-profile-that-adapts-to-your-grind-size/)
- [Pocket Science Coffee - Extractamundo (JoeD)](https://pocketsciencecoffee.com/2022/05/31/birth-of-turbobloom-and-extractamundo/)
- [Papel Espresso - Slayer-Style on Gaggiuino](https://www.papelespresso.com/understanding-the-slayer-style-profile-on-gaggiuino-modified-machines/)

### Community
- [Coffee Chronicler - Allonge vs Lungo vs Turbo](https://coffeechronicler.com/allonge-vs-lungo-turbo-shot-sprover/)
- [Home-Barista - Filter 2.1 Discussion](https://www.home-barista.com/brewing/filter-2-1-brewing-decent-de1-t92630.html)
- [D-Flow Editor for Londinium Family](https://decentespresso.com/blog/dflow_an_easy_editor_for_the_londinium_family_of_espresso_profiles)
- [Gaggiuino GitHub - Profile Format Discussion](https://github.com/Zer0-bit/gaggiuino/discussions/350)
- Reddit r/espresso, r/gaggiaclassic (100+ posts surveyed)
- Gaggiuino Discord #profiles channel

---

## Related Notes

- [Gaggiuino-Profile-Comparison-Guide](Gaggiuino-Profile-Comparison-Guide.md) - How Londinium, Blooming, IUIUIU work mechanically
- [Gaggiuino-Custom-Profiles-Import-Guide](Gaggiuino-Custom-Profiles-Import-Guide.md) - Loading profiles onto your Gaggiuino
- [Gaggiuino-Pressure-Profiling-Extraction-Parameters](Gaggiuino-Pressure-Profiling-Extraction-Parameters.md) - Extraction science deep dive
- [Gaggiuino-Popular-Community-Profiles-Research](../research-notes/Gaggiuino-Popular-Community-Profiles-Research.md) - Earlier community profiles research

---

*Last updated: February 16, 2026*
*Research Version: 1.0*
*Next review: August 2026*
