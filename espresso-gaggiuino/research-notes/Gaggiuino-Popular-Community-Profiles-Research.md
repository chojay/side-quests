# Gaggiuino Popular Community Profiles Research

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod, exported from an Obsidian vault (compiled 2026-01-28). Wiki links flattened to plain text; sources cited inline.

> Comprehensive research on the most popular and recommended espresso profiles in the Gaggiuino community. Covers lever-style profiles, blooming profiles, turbo shots, and roast-specific recommendations based on Discord, Reddit, GitHub, and SproFiler community sources.

---

## Executive Summary

Based on research across the Gaggiuino Discord (21,000+ members), GitHub discussions, GaggiMate documentation, SproFiler, and espresso forums, the most popular profile categories are:

| Profile Type | Best For | Community Popularity |
|-------------|----------|---------------------|
| **Londinium/Lever Style** | Medium roasts, traditional espresso | Highest - comes pre-loaded |
| **Blooming Espresso** | Light to medium-light roasts | Very High - "if you're not blooming, you're not Gaggiuino-ing" |
| **Allonge/Turbo** | Ultra-light roasts | High - filter-like clarity |
| **IUIUIU** | Medium roasts | Medium - Decent/Gaggiuino crossover |
| **Cremina Lever** | Medium-dark to dark roasts | Medium - included in GaggiMate |

---

## 1. Londinium Lever Profile (Most Recommended)

### Why It's Popular

The Londinium profile is arguably the most frequently recommended for Gaggiuino users, especially those with **medium roast Brazilian beans**. It replicates the extraction style of Londinium lever espresso machines ($4,000+) which have a naturally declining pressure curve.

> "For a typical Brazilian medium roast, the Londinium profile ended up working the best."
> - [Kozikow Blog](https://kozikow.blog/2024/02/22/gaggiuino-build-log/)

### Profile Characteristics

| Parameter | Value |
|-----------|-------|
| **Roast Level** | Medium to medium-dark |
| **Pressure Curve** | Declining from ~9 bar to ~6 bar |
| **Total Time** | 25-35 seconds |
| **Target Ratio** | 1:2 |
| **Temperature** | 93-94C |

### How It Works

1. **Pre-infusion** (0-5s): Low pressure puck saturation at ~3 bar
2. **Peak Pressure** (5-15s): Builds to 8-9 bar
3. **Declining Pressure** (15-30s): Gradually drops from ~8.5 to 6 bar

This mimics the spring lever action where pressure naturally decreases as the spring extends.

### Example: Leva 9 LR v0.5

A documented variant targeting 40g output:

| Phase | Time | Pressure | Flow Rate |
|-------|------|----------|-----------|
| Pre-infusion | 0-5s | 0.3-0.6 bar | 6-7 ml/s |
| Pressure Build | 5-15s | Rising to 9 bar | 2-3 ml/s |
| Extraction | 15-20s | 8.9 bar peak | 2.5-3 ml/s |
| Decline | 20-26.5s | 8.5 to 6.4 bar | 2.8 ml/s |

**Total Duration**: ~26.5 seconds

### Availability

- **Pre-loaded**: Comes with Gaggiuino Gen 3 firmware
- **GaggiMate**: Available as downloadable profile
- **Discord**: Multiple community variations

---

## 2. Blooming Espresso Profile

### Why It's Popular

The blooming profile is considered the signature profile for Gaggiuino users extracting **light roasts**. It's frequently cited as the reason to get pressure profiling in the first place.

> "You are not really Gaggiuino-ing if you are not trying to extract light roasts with bloom profile."
> - Gaggiuino community member

### Profile Characteristics

| Parameter | Value |
|-----------|-------|
| **Roast Level** | Light to medium-light |
| **Total Time** | 45-65 seconds |
| **Target Ratio** | 1:2 to 1:3 |
| **Temperature** | 93-96C |
| **Key Feature** | 25-30 second "pause" after pre-infusion |

### How It Works

1. **Fill Phase** (0-5s): Fast fill at 7-8 ml/s until 6-7 bar pressure spike
2. **Bloom/Soak** (5-35s): Valve closed, 25-30 second pause letting CO2 escape
3. **Extraction** (35-65s): Gradual pressure ramp to 5-9 bar, then decline

### Key Benefits

- **Up to 1.5% higher extraction yield** compared to traditional profiles
- **Sweeter, more complex flavors** from light roasts
- **Better puck saturation** - CO2 escape allows water to penetrate evenly
- **Reduced channeling** with proper bloom timing

### Adaptive Bloom Technique

From [Espresso Aficionados](https://espressoaf.com/guides/profiling.html):

> "Close at the desired pressure spike (5-7 bar) and open back up around 2 bar. If you're using a pressure profiler, try starting by ramping to 5-9 bar and then smoothly ramp back to 2 bar."

### Blooming Allonge Variant

For **ultra-light Nordic filter roasts**:

| Parameter | Value |
|-----------|-------|
| Grind | Ultra-fine (Turkish-level) |
| Fill Rate | 7-8 ml/s |
| Soak | Valve closed until pressure returns to 1 bar |
| Percolation | 4.5 ml/s debit |
| Peak Pressure | Should not exceed 6 bar |
| Target Ratio | 1:3 and higher |

**Result**: "Exceptionally high flavor clarity" with high extraction yields.

---

## 3. Allonge/Turbo Profile

### Why It's Popular

Turbo/Allonge profiles gained popularity through the Decent Espresso community and translate well to Gaggiuino. They're designed for **uncooperative light roasts** where blooming doesn't work well.

> "Turbo shots are the best bet for getting to tasty quickly."
> - [Espresso Aficionados](https://espressoaf.com/guides/profiling.html)

### Profile Characteristics

| Parameter | Turbo | Allonge |
|-----------|-------|---------|
| **Roast Level** | Light | Very light |
| **Total Time** | 11-20 seconds | ~30 seconds |
| **Target Ratio** | 1:3 | 1:4 to 1:5 |
| **Pressure** | 4-6 bar | 8-9 bar |
| **Flow Rate** | High (~4.5 ml/s) | High (~4.5 ml/s) |

### Rao Allonge Parameters (from Decent/John Buckman)

- **Ratio**: 1:5 (can do 1:4-6)
- **Time**: 30-40 seconds
- **Flow Rate**: 4.5 ml/s throughout
- **Pressure**: Hit 8-9 bar, finish around 6 bar

### Key Benefits

- **Filter-like clarity** in the cup
- **Reduced channeling** from lower pressure
- **Faster dialing** - less sensitive to grind
- **Eliminates astringency** almost entirely

### "Yeet" Profile Variant

The most extreme turbo approach:

- Full debit open
- 6-9 bar pressure spike
- Very short time (under 15 seconds)
- Higher clarity but less body

---

## 4. GaggiMate Pre-loaded Profiles

These profiles are available directly from [GaggiMate documentation](https://docs.gaggimate.eu/docs/profiles/) and downloadable as JSON files:

### Cremina Lever (by Johnyez)

| Parameter | Value |
|-----------|-------|
| **Best For** | Dark roasts, traditional espresso |
| **Duration** | 40-60 seconds |
| **Ratio** | 1:1.5 to 1:2.2 |
| **Temperature** | 78-90C |
| **Style** | Mimics La Marzocco Leva |

**Character**: Lots of crema, traditional texture, best for medium-dark to very dark roasts.

### Medium 18g 1:2 (by alexr1525)

| Parameter | Value |
|-----------|-------|
| **Dose** | 18g |
| **Yield** | 36g |
| **Style** | Pre-infusion + bloom + 9 bar + decline |

**Structure**: Relatively simple profile good for dialing in new beans.

### Backflush Profile

Not for espresso - designed for machine maintenance with Cafiza cleaning solution.

---

## 5. IUIUIU Profile (Decent/Gaggiuino Crossover)

### Origin

Created by community member **Mor**, documented on [Visualizer.coffee](https://visualizer.coffee/shots/d6c2a292-a45a-48b5-835f-65065260b69f). Used on both Decent Espresso machines and Gaggiuino.

### Profile Characteristics

| Parameter | Light Roast | Medium Roast |
|-----------|-------------|--------------|
| **Dose** | 17.5g | 17.5g |
| **Yield** | 33.6-34.5g | 36g |
| **Ratio** | 1:1.9-1:2.0 | 1:2.1 |
| **Total Time** | 45-116 seconds | 25-45 seconds |
| **Peak Pressure** | 7.5 bar | 7.5 bar |

### Three Phase Structure

1. **Pre-infusion** (0-11s): Steady 4 bar, puck saturation
2. **Ramp-up** (11-18s): 2.3 to 7.5 bar gradual increase
3. **Plateau/Decline** (18-25+s): Stabilizes ~6 bar, then gradual decline

### Notable Features

- **Never reaches 9 bar** - peaks at ~7.5 bar
- **Lever-style declining pressure** in final phase
- **Excellent for light and medium roasts**
- Requires precise puck prep (WDT, paper filters recommended)

---

## 6. Profile Recommendations by Roast Level

Based on community consensus from Discord, Reddit, and espresso forums:

### Light Roasts

| Recommended Profile | Time | Ratio | Temperature |
|--------------------|------|-------|-------------|
| **Blooming Espresso** | 45-65s | 1:2.5-1:3 | 93-96C |
| **Blooming Allonge** | 40-60s | 1:3-1:5 | 94-96C |
| **Turbo/Allonge** | 15-30s | 1:3-1:5 | 93-95C |

**Key technique**: Extended bloom phase, higher ratios, grind finer than traditional.

### Medium Roasts

| Recommended Profile | Time | Ratio | Temperature |
|--------------------|------|-------|-------------|
| **Londinium/Lever** | 25-35s | 1:2 | 93-94C |
| **IUIUIU** | 25-45s | 1:2 | 93C |
| **Modified Dipper** | 30-45s | 1:2 | 92-94C |

**Community favorite**: Londinium profile for medium roast Brazilian beans.

### Medium-Dark Roasts

| Recommended Profile | Time | Ratio | Temperature |
|--------------------|------|-------|-------------|
| **Cremina Lever** | 40-60s | 1:1.5-1:2 | 88-92C |
| **Lever Decline** | 30-40s | 1:1.8-1:2 | 90-93C |

**Key technique**: Lower temperature, declining pressure, shorter ratios.

### Dark Roasts

| Recommended Profile | Time | Ratio | Temperature |
|--------------------|------|-------|-------------|
| **Traditional 9-bar** | 25-30s | 1:1.5-1:2 | 88-91C |
| **Cremina Lever** | 35-45s | 1:1.5-1:2 | 78-88C |

**Key technique**: Low temperature is critical to avoid bitterness.

---

## 7. Extraction Times and Ratios Summary

### Traditional Rules Are Guidelines

> "1:2 in 30s is not a rule to be strictly adhered to."
> - [Espresso Aficionados](https://espressoaf.com/guides/profiling.html)

With pressure profiling, extraction times of **40-60+ seconds** are common and produce superior results for light roasts.

### Modern Parameters by Profile Type

| Profile | Time Range | Ratio | Pressure |
|---------|-----------|-------|----------|
| Traditional 9-bar | 25-30s | 1:2 | Constant 9 bar |
| Lever/Londinium | 25-35s | 1:2 | Declining 9-6 bar |
| Blooming | 45-65s | 1:2-1:3 | Variable 3-9 bar |
| Turbo | 11-20s | 1:3 | Low 4-6 bar |
| Allonge | 30-40s | 1:4-1:5 | 8-9 bar |
| Filter/Sprover | ~100s | 1:10-1:14 | Under 1.5 bar |

### Weight-Based vs Time-Based Stopping

**Community consensus**: Always use **weight-based stop conditions** when possible.

- Set target weight in profile (e.g., 36g for 1:2 ratio with 18g dose)
- Requires Bluetooth scale or built-in load cells
- Time becomes secondary metric
- More consistent results across grind adjustments

---

## 8. About "Zer0" Profiles

### Zer0-bit: The Creator

**Zer0-bit** is the GitHub username of the creator/maintainer of the Gaggiuino project itself. The name appears on:

- [GitHub Repository](https://github.com/Zer0-bit/gaggiuino)
- All Gaggiuino releases
- Firmware commits

### Community-Named Profiles

Research did not find widely documented profiles specifically named "Zer0" or "Zero." However:

1. **Zero flow phase** - Used in blooming profiles (pause with 0 ml/s flow)
2. **Community profiles** - May exist in Discord #profiles channel
3. **Tribute profiles** - Some users name custom profiles after the creator

For specific "Zer0" profiles, check the [Gaggiuino Discord](https://discord.com/invite/gaggiuino-890339612441063494) #profiles channel.

---

## 9. Where to Find Community Profiles

### Primary Sources

| Source | URL | Notes |
|--------|-----|-------|
| **Gaggiuino Discord** | [discord.com/invite/gaggiuino](https://discord.com/invite/gaggiuino-890339612441063494) | 21,000+ members, #profiles channel |
| **SproFiler** | [sprofiler.io](https://sprofiler.io/) | Shot sharing + profile downloads (Early Access) |
| **GaggiMate Docs** | [docs.gaggimate.eu/docs/profiles/](https://docs.gaggimate.eu/docs/profiles/) | Sample profiles with JSON downloads |
| **Visualizer.coffee** | [visualizer.coffee](https://visualizer.coffee/) | Decent Espresso community, profiles work on Gaggiuino |

### Reddit Communities

- **r/gaggiuino** - Dedicated subreddit (smaller community)
- **r/espresso** - General espresso with Gaggiuino discussions
- **r/gaggiaclassic** - Gaggia-specific with Gaggiuino threads

### Import Profiles

See Gaggiuino Custom Profiles Import Guide for step-by-step JSON import instructions.

---

## 10. Community Consensus Highlights

### From Discord/Reddit Discussions

1. **Start with Londinium** for medium roasts - it's proven and comes pre-loaded
2. **Blooming is transformative** for light roasts - worth the longer extraction time
3. **Don't chase 9 bar** - many profiles deliberately stay at 6-8 bar for better results
4. **Paper filters help** - bottom and top paper filters improve puck prep for complex profiles
5. **Weight > Time** - always stop by weight if you have a scale

### Common Beginner Mistakes

| Mistake | Fix |
|---------|-----|
| Using traditional timing expectations | Expect 40-60s for bloom profiles |
| Always targeting 9 bar | Many profiles peak at 6-8 bar |
| Not matching profile to roast | Light = bloom, Medium = lever, Dark = traditional |
| Skipping pre-infusion | Pre-infusion is critical for even extraction |

---

## Related Notes

### Gaggiuino Setup
- Gaggiuino Profile Selection by Bean Origin and Character - Profile selection by origin, processing method, roast level - Ethiopian, Kenyan, Brazilian, Colombian, Gesha; unknown bean decision tree
- Gaggiuino Modification Overview - Features, community, resources
- Gaggiuino Custom Profiles Import Guide - JSON import/export workflow
- Gaggiuino Pressure Profiling Extraction Parameters - IUIUIU details, extraction theory
- Gaggiuino Post Install Operation Guide - Daily operation guide
- Gaggiuino Bluetooth Scale Recommendations - BLE scales for gravimetric stop

### Espresso Fundamentals
- Espresso Extraction Fundamentals Shot Quality Portafilter Science - Extraction science
- Espresso Workflow Quick Reference - Complete workflow
- DF64 Gen2 Comprehensive Best Practices - Grinder settings

---

## Sources

- [Gaggiuino Official Documentation](https://gaggiuino.github.io/)
- [Gaggiuino Discord Community](https://discord.com/invite/gaggiuino-890339612441063494)
- [GaggiMate Profiles Documentation](https://docs.gaggimate.eu/docs/profiles/)
- [Espresso Aficionados Profiling Guide](https://espressoaf.com/guides/profiling.html)
- [SproFiler Platform](https://sprofiler.io/)
- [Kozikow Blog - Gaggiuino Build Log](https://kozikow.blog/2024/02/22/gaggiuino-build-log/)
- [Visualizer.coffee - IUIUIU Profile](https://visualizer.coffee/shots/d6c2a292-a45a-48b5-835f-65065260b69f)
- [Scott Rao - Best Practice Espresso Profile](https://www.scottrao.com/blog/2021/5/18/best-practice-espresso-profile)
- [Coffee Chronicler - Allonge vs Turbo](https://coffeechronicler.com/allonge-vs-lungo-turbo-shot-sprover/)
- [CoffeeGeek - Turbo Shot Exploration](https://coffeegeek.com/opinions/history-technology/turbo-shot-espresso-a-detailed-exploration/)
- [Aftermath - Gaggiuino DIY](https://aftermath.site/gaggiuino-gaggia-classic-pro-mod-open-source-hack/)

---

*Created: 2026-01-28*
*Confidence: High - Based on official documentation, community sources, and multiple independent research sources*
