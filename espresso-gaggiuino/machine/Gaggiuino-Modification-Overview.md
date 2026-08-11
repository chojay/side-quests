# Gaggiuino Modification Overview

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2025-12-21). Wiki links flattened; sources cited inline.

## What is Gaggiuino?

**Gaggiuino** is an open-source, community-driven project that transforms budget espresso machines (primarily [Gaggia Classic](Gaggia-Classic-Evo-Pro-Best-Practices.md) variants) into professional-grade machines with features comparable to high-end equipment costing $3,000+.

> "The Gaggiuino is **far and away the best** for me. The level of control and adaptability is a **quantum leap** over what a PID provides."
> - Community member

The project was created by **Zer0-bit** and is maintained by a dedicated community of developers and coffee enthusiasts on Discord.

---

## Key Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Pressure Profiling** | Control extraction pressure throughout the shot (e.g., 3 bar → 9 bar → 6 bar). Requires [12 bar OPV spring](../research-notes/Gaggiuino-OPV-Spring-12-Bar-Analysis.md) for full 0-11 bar range. |
| **Flow Control** | Manual or automatic flow rate adjustment |
| **PID Temperature Control** | ±1°C temperature stability, eliminates temperature surfing |
| **Shot Graphing** | Real-time visualization of pressure, flow, and temperature |
| **Auto-Stop by Weight** | Integrated scale support for precise yield control |
| **DreamSteam Mode** | Enhanced steam power that rivals $1,000+ machines |
| **OTA Updates** | Over-the-air firmware updates |
| **Web Interface** | Configure settings from any device |
| **Shot History** | Log and analyze past extractions |
| **Bluetooth Scales** | Native support for [wireless scale integration](Gaggiuino-Bluetooth-Scale-Recommendations.md) |

### Pre-Built Shot Profiles

Gaggiuino includes several factory profiles:

- **Classic 9-bar** - Traditional espresso extraction
- **Lever Machine** - Mimics Londinium R pressure decline (9 → 6 → 3 bar)
- **Blooming/Filter** - Long pre-infusion for filter-style espresso
- **Turbo Shot** - High flow, low pressure, short extraction time
- **Custom Profiles** - Create, import, and export your own (see [Gaggiuino-Custom-Profiles-Import-Guide](../profiles/Gaggiuino-Custom-Profiles-Import-Guide.md))

---

## Hardware Components

### Gen 3 V4 Kit Contents (Typical)

| Component | Purpose |
|-----------|---------|
| **STM32 U585 PCB** | Main microcontroller (ultra-capable CPU) |
| **4.3" Touchscreen** | User interface and shot visualization |
| **PTB (Pressure Tap Block)** | CNC stainless steel 3-way pressure connection |
| **Pressure Sensor** | Food-grade XDB401 (0-1.2 MPa / 12 bar range) |
| **K-Type Thermocouple** | Boiler temperature sensing |
| **SSR (Solid State Relay)** | Controls heating element |
| **ToFLED** | Water level sensor + RGB LED indicator |
| **DualScale Load Cells** | Integrated scale functionality |
| **AC Dimmer Module** | Controls pump for pressure/flow profiling |
| **Wiring Harnesses** | Pre-crimped low/high voltage cables |

---

## Generations Comparison

| Feature | Gen 2 (V3 PCB) | Gen 3 (V4 PCB) |
|---------|----------------|----------------|
| **Microcontroller** | Arduino/STM32 | STM32 U585 + ESP32 |
| **Screen** | 2.4" Nextion | 4.3" IoT Touchscreen |
| **Profile Phases** | Up to 10 | Unlimited |
| **Source Code** | Open source | Closed (quality control) |
| **Cost** | ~$280 | ~$340-400 |
| **Status** | Stable, legacy | Active development |
| **Recommendation** | Non-standard machines | Gaggia/Silvia owners |

**Gen 3 is recommended** for Gaggia Classic and Rancilio Silvia - it's newest, has more features, and receives active updates.

---

## Machine Compatibility

### Officially Supported

- ✅ **Gaggia Classic Pro** (all years)
- ✅ **Gaggia Classic Evo Pro** (2023+)
- ✅ **Gaggia Classic** (various generations with 3-way valve)
- ✅ **Rancilio Silvia** (community documentation available)

### NOT Compatible

- ❌ Heat exchanger machines (E61 group)
- ❌ Thermoblock/thermocoil machines
- ❌ Machines with rotary pumps
- ❌ Gaggia Classic V2 (SIN035U RI9403) - no 3-way valve
- ❌ Machines with group/check valve design

---

## Cost Analysis

### Total Investment

| Category | Cost Range |
|----------|------------|
| **Gaggiuino Kit (Gen 3 V4)** | $340-400 |
| **3D Printed Parts** | $30-60 |
| **12-bar OPV Spring** (Evo Pro) | $15-20 |
| **Hardware** (screws, magnets, wire) | $35-55 |
| **Tools** (if buying new) | $200-370 |
| **TOTAL** | $420-520 (kit + parts) |
| | $620-900 (including tools) |

### Value Proposition

> "For less than $700 total, **best machine on the market** with Gaggiuino. Pressure profiling comparable only to **Decent for $3,000**."
> - Reddit community

**Compare to alternatives:**
- Decent DE1 with profiling: $3,000-4,000
- La Marzocco Linea Mini: $5,500
- Lelit Bianca with flow control: $2,400-3,000

---

## YouTube Resources

### Essential Videos

| Video | Creator | Content |
|-------|---------|---------|
| **[Ultimate Budget Espresso Machine: The Gaggiuino UPDATED](https://www.youtube.com/watch?v=V4pTFCGVlmQ)** | Lance Hedrick | Comprehensive overview, $500 machine with $5,000 capabilities (~89k views) |
| **[Gaggiuino 2024 Version Overview](https://www.youtube.com/watch?v=J4AyUoflVUU)** | Various | Gen 3 V4 features and improvements |
| **[JST Connector Assembly Tutorial](https://www.youtube.com/watch?v=nRVhPhfdawg)** | Various | Critical wiring technique |

### What to Learn From Videos

1. **Overview videos** (Lance Hedrick) - Understand capabilities and value proposition
2. **Installation walkthroughs** - Follow along during your build
3. **Profile tutorials** - Learn to create custom extraction curves
4. **Troubleshooting** - Common issues and solutions

---

## Official Resources

### Documentation & Code

| Resource | URL | Purpose |
|----------|-----|---------|
| **Official Docs** | [gaggiuino.github.io](https://gaggiuino.github.io/) | Installation guides, configuration |
| **GitHub Repository** | [github.com/Zer0-bit/gaggiuino](https://github.com/Zer0-bit/gaggiuino) | Project home, discussions |
| **GaggiMate Docs** | [docs.gaggimate.eu](https://docs.gaggimate.eu/docs/installation-gcp/) | Alternative installation guide |
| **Machine-Specific Guides** | [Machine Guide](https://gaggiuino.github.io/guides/machine-specific-guide.md) | Model-specific instructions |

### Suppliers (Official)

| Supplier | Location | Notes |
|----------|----------|-------|
| **[Peak Coffee](https://www.peakcoffee.cc/product/gaggiuino-v4-complete-kit/)** | Hong Kong | Complete kits, expedited shipping |
| **[DIY-EFI](https://diy-efi.co.uk/product-category/gaggiuino/)** | UK | "MUCH better quality" parts (user reviews) |
| **[Espressio](https://gaggiuino.espressio.nl/)** | Netherlands | Official 3D printed parts |

⚠️ **Avoid**: Matter Replicator (USA) - "Uses substandard parts, lots of problems" - Community reports

---

## Community & Support

### Discord (Primary Support)

**[Gaggiuino Discord Server](https://discord.com/invite/gaggiuino-890339612441063494)**

- **~21,000 members**
- **#mod-3d-design-ideas** - Custom 3D printed parts
- **#support threads** - Installation help
- **Profile sharing** - Community extraction curves
- **Active moderators** including original creator (Zer0-bit)

### Reddit Communities

| Subreddit | Gaggiuino Discussion % |
|-----------|------------------------|
| [r/gaggiaclassic](https://www.reddit.com/r/gaggiaclassic/) | 52.5% |
| [r/espresso](https://www.reddit.com/r/espresso/) | 40.7% |
| [r/ranciliosilvia](https://www.reddit.com/r/ranciliosilvia/) | 1.8% |
| [r/coffee](https://www.reddit.com/r/coffee/) | 1.3% |

### Forums

- **[Home-Barista.com - Gaggiuino Thread](https://www.home-barista.com/repairs/gaggiuino-project-t91138.html)** - Professional-level discussion
- **[Coffee Forums UK](https://www.coffeeforums.co.uk/threads/gaggiuino.72426/)** - Active UK community
- **[CoffeeSnobs Australia](https://coffeesnobs.com.au/forum/equipment/brewing-equipment-midrange-500-1500/997977-gaggiuino-build-gaggia-classic-pro)** - Build logs

---

## Installation Overview

### Skill Level Required

| Skill | Level (1-5) | Notes |
|-------|-------------|-------|
| **Soldering** | 3/5 | Wire connections, JST connectors |
| **Electronics** | 3/5 | Understanding wiring diagrams |
| **Mechanical** | 2/5 | Disassembly, drilling for screen mount |
| **Arduino/Coding** | 1/5 | Minimal - firmware is pre-compiled |

### Time Investment

| Phase | Duration |
|-------|----------|
| Research & learning | 1-2 weeks |
| Parts ordering & shipping | 1-2 weeks |
| Installation | 6-10 hours |
| Calibration & testing | 2-4 hours |
| Profile experimentation | 1-2 weeks |

### Critical Installation Tips

From [kozikow.blog build log](https://kozikow.blog/2024/02/22/gaggiuino-build-log/):

1. **Mark all connectors** with a marker before disconnection
2. **Use proper crimper** - "boiler terminal" crimper only works for uninsulated connectors
3. **Ignore wire colors** when connecting JST - follow diagram instead
4. **Wrap pressure sensor in foam** rated 80°C+ (standard foam degrades)
5. **Both thermal fuses remain** as safety features
6. **Budget 3+ days** if you lack prior experience

---

## 3D Printed Parts

### Material Requirement

**PETG ONLY** - PLA and ABS will degrade from machine heat

### Print Settings

```
Nozzle:       0.4mm
Layer Height: 0.2mm
Wall Lines:   3
Infill:       20-30%
Material:     PETG (REQUIRED)
```

### Sources

| Source | Type | Cost |
|--------|------|------|
| **[Espressio](https://gaggiuino.espressio.nl/)** | Pre-printed (official) | $30-60 |
| **[Printables STLs](https://www.printables.com/model/280617-gaggiuino-gaggia-classic-pro-touchscreen-housing-a)** | Download for DIY | Free |
| **[MakerWorld STLs](https://makerworld.com/en/models/660083-gaggiuino-gen-3-screen-housing)** | Download for DIY | Free |

### Screen Mount Options

| Mount Type | Pros | Cons |
|------------|------|------|
| **Funnel Mount** ⭐ | Optimal viewing angle, adjustable | Most complex install |
| **Front Mount** | Simple installation, compact | Fixed angle, requires cutting |
| **Rear Mount** | Adjustable, away from steam | Takes most space |

---

## Gaggiuino vs. Other Mods

### Gaggiuino vs. PID Controller

| Aspect | PID Only | Gaggiuino |
|--------|----------|-----------|
| **Cost** | $100-200 | $340-400 |
| **Temperature Control** | ✅ Yes | ✅ Yes |
| **Pressure Profiling** | ❌ No | ✅ Yes |
| **Flow Control** | ❌ No | ✅ Yes |
| **Shot Graphing** | ❌ No | ✅ Yes |
| **Auto-Stop by Weight** | ❌ No | ✅ Yes |
| **Install Complexity** | Medium | High |

**Community consensus**: "Skip PID, go straight to Gaggiuino... PID would just be waste of time/money/effort"

### Gaggiuino vs. Upgrade Machine

| Option | Cost | Outcome |
|--------|------|---------|
| **Gaggiuino mod** | ~$500 | Gaggia + $3,000 capabilities |
| **Buy used Decent** | $2,000-2,500 | Dedicated profiling machine |
| **Buy Lelit Bianca** | $2,400-3,000 | Manual paddle flow control |

For hobby espresso enthusiasts who enjoy DIY, Gaggiuino provides exceptional value.

---

## Related Notes

### Setup

- [Gaggiuino-Post-Install-Operation-Guide](Gaggiuino-Post-Install-Operation-Guide.md) - Daily operation, BLE scale setup, profile progression
- [Gaggiuino-Custom-Profiles-Import-Guide](../profiles/Gaggiuino-Custom-Profiles-Import-Guide.md) - Import/export profiles, JSON format, community sources
- [Gaggiuino-Bluetooth-Scale-Recommendations](Gaggiuino-Bluetooth-Scale-Recommendations.md) - Bluetooth scale options for TOF-only install
- [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) - Machine-specific installation guide
- [Gaggia-Classic-Evo-Pro-Best-Practices](Gaggia-Classic-Evo-Pro-Best-Practices.md) - Machine best practices
- [OPV-Spring-Mechanism-Technical-Deep-Dive](../research-notes/OPV-Spring-Mechanism-Technical-Deep-Dive.md) - Why Gaggiuino needs a 12-bar OPV spring (engineering deep dive)

### Maintenance

- [Gaggiuino-Descale-Procedure](../troubleshooting/Gaggiuino-Descale-Procedure.md) - What the Descale menu does + procedure for Evo Pro

---

## Quick Reference

### Official Links

- **Docs**: [gaggiuino.github.io](https://gaggiuino.github.io/)
- **Discord**: [discord.com/invite/gaggiuino](https://discord.com/invite/gaggiuino-890339612441063494)
- **GitHub**: [github.com/Zer0-bit/gaggiuino](https://github.com/Zer0-bit/gaggiuino)

### YouTube Essentials

- **Lance Hedrick**: [Gaggiuino Overview](https://www.youtube.com/watch?v=V4pTFCGVlmQ)
- **2024 Version**: [New Features](https://www.youtube.com/watch?v=J4AyUoflVUU)

### Buy Kits

- **Peak Coffee**: [peakcoffee.cc](https://www.peakcoffee.cc/product/gaggiuino-v4-complete-kit/)
- **DIY-EFI**: [diy-efi.co.uk](https://diy-efi.co.uk/product-category/gaggiuino/)
- **3D Parts**: [gaggiuino.espressio.nl](https://gaggiuino.espressio.nl/)

---

## Sources

### Articles & Blogs
- [The Best Espresso Machine Is One You Hack Yourself](https://aftermath.site/gaggiuino-gaggia-classic-pro-mod-open-source-hack/) - Aftermath
- [Homebrew Espresso Maker Modding With Gaggiuino](https://hackaday.com/2022/11/20/homebrew-espresso-maker-modding-with-gaggiuino/) - Hackaday
- [My Gaggiuino Install Experience](https://kozikow.blog/2024/02/22/gaggiuino-build-log/) - Kozikow Blog (detailed build log)
- [Gaggiuino Case Study](https://www.gregoriogangala.com/gaggiuino-case-study) - Design analysis

### Community Sources
- Reddit: r/gaggiaclassic, r/espresso
- Discord: 21,000+ member community
- Home-Barista.com forum threads
- Coffee Forums UK

---

*Research compiled: 2025-12-21*
*Sources: Official documentation, community forums, YouTube creators, build logs*
*Confidence: ⭐⭐⭐ High*
