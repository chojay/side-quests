# Gaggiuino OPV 12-Bar Spring - Complete Guide (Mechanism, Consensus, Risks, Sourcing)

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-07-11). Wiki links flattened; sources cited inline.

> **Current status (June-July 2026)**
> The machine's shot-history drift analysis suspects the installed aftermarket 12-bar spring (~650 shots of service) has **fatigued** - see [2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md) and [Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis](../troubleshooting/Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis.md).

## TL;DR Verdict

**A 10-12 bar OPV spring is required for Gaggiuino. This is settled, unanimous guidance - not a debate.**

Every authoritative source agrees: the official Gaggiuino documentation, project creator Zer0-bit, the 21,000+ member Discord, build-log blogs, forum threads, and vendor listings. A 9 bar spring begins cracking open at ~8.2 bar and silently diverts water back to the tank, which Gaggiuino cannot detect - the software "fights" the OPV and cannot reliably hold a 9 bar profile. Across all sources searched (Reddit, Home-Barista, Coffee Forums UK, GitHub, Amazon reviews, blogs), **no user was found reporting successful Gaggiuino operation with a 9 bar spring**, and no user reported damage or extraction problems from a 12 bar spring.

For the US Gaggia Classic Evo Pro (RI9380/49), which ships from the factory with a 9 bar OPV, this means installing a 12 bar spring (or washer pre-loading) is a **required** step of the [Gaggiuino install](Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md).

---

## How the OPV Mechanism Works

### Spring-loaded poppet valve

The OPV (Over Pressure Valve) is a spring-loaded poppet valve - the simplest form of pressure relief valve. A spring presses a poppet/ball against a seat, blocking a bypass path from the pump outlet back to the water tank. Water pressure exerts an opening force (Pressure × Area); when it exceeds the spring's preload force, the poppet lifts and excess flow diverts to the tank.

`P_crack = F_spring / A_poppet`

An adjustment screw (or the spring choice itself) sets the preload. The OPV sits entirely **outside** Gaggiuino's control loop - it is passive and mechanical, and Gaggiuino has no input from or awareness of it.

### The valve opens gradually, not like a switch

This is the most commonly misunderstood point. A relief valve lifts progressively, roughly proportional to overpressure:

| Pressure point | Definition |
|---|---|
| **Cracking pressure** | First trickle of flow bypasses through the valve |
| **Full-flow pressure** | Valve fully open = the rated/set pressure |
| **Reseat pressure** | Valve closes again on falling pressure, slightly below cracking |

For direct-acting spring-poppet valves, cracking occurs at 50-80% of full-flow pressure in industrial contexts; espresso OPVs are small low-pressure devices, so the cracking-to-full-flow band is narrower - about **1-2 bar**. Per the official Gaggiuino guide:

> "OPVs don't open all at once. For example, a 9 bar spring might initially open a bit at 8.2 bar, slightly increasing flow until fully open around 9 bar. When the OPV opens, water is diverted and Gaggiuino control can't determine if or when that happens."

**Cracking pressure is roughly 0.8 bar below the spring rating** (~7.5-8.2 bar for a 9 bar spring, depending on manufacturing tolerance), and it - not the rating - is the effective ceiling for Gaggiuino.

### Rating vs. static vs. dynamic vs. cracking

| Spring rating | Static test (blank basket, no flow) | During extraction (flow) | Cracking pressure (begins opening) |
|:---:|:---:|:---:|:---:|
| 9 bar | ~10 bar | ~8-9 bar | ~7.5-8.2 bar |
| 12 bar | ~13 bar | ~11-12 bar | ~10.5-11.2 bar |

This is the "+/- 1 bar" phenomenon: a static (dead-headed) gauge reads ~1 bar above the rating, dynamic brew pressure runs ~1 bar below the static reading. Shades of Coffee documents the same behavior for their kits (9 bar spring shows 10 static, 6.5 shows 7.5, 5 shows 6).

### Ceiling, not floor

The OPV sets only the **upper bound** of pressure. Below the cracking point the valve is fully closed and completely inert - it has zero effect on 2-3 bar pre-infusion or any low-pressure segment. The low end is limited by the vibratory pump's minimum stable output under dimmer control (~0-2 bar), not the OPV. Actual brew pressure is determined by pump output, puck resistance, and flow; the OPV only intervenes when those would push pressure past its cracking point.

---

## Why Gaggiuino Needs 10-12 Bar

### The control loop, and how a low OPV breaks it

Gaggiuino controls pressure electronically:

1. **Ulka vibratory pump** (EX5/EAX5, 120V US / EP5, 230V EU) produces up to ~15 bar unregulated
2. **AC dimmer module** modulates pump power (phase-angle / PSM control)
3. **Pressure transducer** (0-12 bar, food-grade) reads real-time brew pressure
4. **Closed-loop PID** compares reading to the profile target and adjusts the dimmer

Gaggiuino cannot override the OPV - it controls pump *input*, while the OPV acts on pump *output*. Crucially, the pressure sensor **cannot distinguish** water flowing through the puck from water escaping through the OPV. With a 9 bar spring and a 9 bar target:

```
1. Gaggiuino ramps pump toward 9 bar
2. At ~8.2 bar the OPV cracks open
3. Water silently diverts back to the tank
4. Sensor reads below target → Gaggiuino increases pump power
5. OPV opens further, diverting more water
6. System oscillates or settles at ~8-8.5 bar
7. The 9 bar target is never reached
```

Coffee Forums UK members describe this exactly as the software "fighting against the OPV when modulating pressure." Practical consequences: unstable/erratic pressure near the cracking point, degraded profiling accuracy for 8-9 bar segments, and wasted water cycled to the tank.

```
With 9-bar OPV:                          With 12-bar OPV:
 0   2   4   6   8  10  12  14 bar        0   2   4   6   8  10  12  14 bar
 [== Gaggiuino control range ==]          [===== Gaggiuino control range =====]
                 ↑ cracks ~8.2                            ↑ 9 bar target: reachable
                  ↑ full open ~9                                ↑ cracks ~10.5
                 ✗ can't hold 9 bar                              ↑ full open ~12 (safety ceiling)
```

### The official rule

Project creator **Zer0-bit** ([GitHub Discussion #387](https://github.com/Zer0-bit/gaggiuino/discussions/387)):

> **OPV = maximum desired shot pressure + 2 bar**

The official machine-specific guide states the OPV should be **10-12 bar**, at least 1 bar above the highest desired shot pressure, and never below 10 bar. For standard 9 bar profiles that means 11 bar minimum, with 12 bar giving comfortable headroom (cracking ~10.5-11 bar, safely above the entire 6-9 bar extraction range).

Note: the **older Gaggiuino wiki** (samirkouider on GitHub) said to tune the OPV to 9 bar - that guidance is **obsolete**. Current docs at gaggiuino.github.io say 10-12 bar.

The only theoretical case for keeping 9 bar: if you *never* profile above 7-8 bar (exclusively low-pressure filter-style profiles). This needlessly limits flexibility and contradicts official docs.

### US Evo Pro ships with 9 bar - the ironic special case

- **EU Gaggia machines**: ~12 bar OPV from the factory, for 30+ years
- **Pre-2023 Gaggia Classic Pro (all markets)**: ~12 bar stock
- **US Gaggia Classic Evo Pro (RI9380/49) and E24**: ship with a **9 bar OPV** - Gaggia lowered it for the US market because the community had been doing the 9-bar mod manually

The ironic result: US Evo Pro owners installing Gaggiuino must put the OPV **back up** to 12 bar - the opposite of the classic OPV mod - while pre-2023 GCP and most EU owners can keep their stock spring. The official guide explicitly calls this out for US Evo Pro and E24 models. Both machines use the same pump-mounted plastic OPV, so the spring swap procedure is identical and there are no Evo-specific compatibility issues.

### Achievable range comparison

| Configuration | Lower limit | Upper limit | Can hit 9 bar? | Notes |
|---|---|---|---|---|
| **9 bar OPV** (US Evo Pro stock) | ~0-2 bar | ~8 bar | No - OPV interferes | Limited profiling |
| **12 bar OPV** | ~0-2 bar | ~11 bar | Yes, with headroom | Full profiling |
| **No OPV** | ~0-2 bar | ~15 bar | Yes | Never do this - no safety ceiling |

---

## Risk Assessment Summary

**Overall risk level: LOW.** The 12 bar spring returns the machine to its original design parameters - Gaggia Classics shipped at 12-15 bar from the factory since 1991, millions of units, with zero documented cases of structural failure from that pressure. The OPV is lowered to 9 bar for espresso *quality* reasons, never safety reasons.

### Fail-safe behavior if Gaggiuino fails mid-brew

| Failure mode | Pump state | Max pressure | Protection | Duration |
|---|---|---|---|---|
| MCU software crash | OFF (fail-safe) | 0 bar | Triac needs active gate pulses; stops at next zero-crossing | ~1-2 s watchdog reboot |
| Triac hardware short (typical triac failure) | FULL power | ~15 bar unregulated | **OPV caps at ~12 bar** | Until power off |
| GPIO stuck high | FULL power | ~15 bar unregulated | OPV caps at ~12 bar; watchdog eventually reboots | Transient |
| Power loss | OFF | 0 bar | N/A | Immediate |

The most significant scenario is the triac short: the pump runs unregulated and the OPV becomes the sole pressure limiter - bounded at 12 bar, which is within the machine's design envelope. Firmware safety layers (from the last public `release/stm32-blackpill` code) include the watchdog timer, `sysHealthCheck()` (pump/boiler/steam off on bad temperature reads), a pressure-release routine, steam-forgotten shutdown (10 min), and a pump click-rate cap. There is **no software maximum-pressure cutoff** - the OPV is the hard mechanical cap. Gen 3 firmware is closed-source and may add features not visible publicly. Hardware protections (boiler and pump thermal fuses, boiler safety relief valve) remain in circuit independent of the OPV.

### No damage reports

Extensive searching (Home-Barista, Coffee Forums UK, CoffeeSnobs, Reddit, GitHub) found **zero reports** of leaks, seal failures, component damage, over-extraction, or taste problems attributed to a 12 bar spring with Gaggiuino:

- **Portafilter/group head/boiler**: all rated for the factory 12-15 bar setting. During normal shots Gaggiuino holds 6-9 bar; the gasket and boiler only see ~12 bar during brief dead-head scenarios (backflushing, blind-basket tests).
- **Ulka pump**: rated 15 bar max; respect the 2 min on / 1 min off duty cycle regardless of spring.
- OPV issues that do occur are mechanism problems, not spring-pressure problems: defective rubber seals, limescale seizing the valve (fix: citric acid soak), poorly seated adjustable OPVs.
- Paradoxically, **lower** springs cause more trouble: a 5 bar spring lets ~8 bar steam pressure blow the OPV open and loudly dump boiler contents to the tank.

### Steaming and the one quirk

The 12 bar spring is **better** for steaming: steam pressure peaks ~8 bar, well below the ceiling, so the OPV never opens during steaming (and DreamSteam works optimally). One build log noted a minor quirk: with the ~11-12 bar ceiling, steam temperature can occasionally get stuck around 120-130°C with pressure reading ~11 bar - briefly opening and closing the steam wand clears it. Operational annoyance, not a safety issue.

### If you ever remove Gaggiuino

Brewing on a stock machine at 12 bar with unpressurized baskets produces poor espresso (channeling, over-extraction). **Keep the original 9 bar spring in a labeled bag** so you can swap back.

### Other mitigations

- Verify the OPV pressure after installation (see the Verification Procedure section below)
- Periodically inspect the dimmer module for overheating (discoloration, melted plastic) - triac short is the most consequential failure mode; consider an 800V-rated triac and/or RC snubber for inductive pump loads
- Retain all thermal fuses; replace the group gasket annually (8.5 mm)
- Minor sensor caveat: the 0-12 bar transducer's full scale matches the OPV ceiling, so readings at exactly 12 bar sit at the sensor's maximum with reduced accuracy

---

## Options & Sourcing

| Product | Price | Source | Notes |
|---|---|---|---|
| **Distro Coffee Labs 12 Bar OPV Spring** | ~$15-20 | [Amazon US](https://www.amazon.com/Bar-Spring-Modification-Espresso-Machines/dp/B0CZGMW7VB) | 304 SS, marketed specifically for Gaggiuino. Most accessible US option. **This is the spring type involved in the June 2026 drift case study.** |
| **Barista Gadgets 12 Bar Spring** | ~$10-15 | [Etsy](https://www.etsy.com/listing/1556589768/12-bar-opv-spring-for-gaggia-classic-pro) | Same spec as stock Gaggia Classic Pro spring |
| **Shades of Coffee 12 Bar Spring** | ~$5-10 | [Shades of Coffee (UK)](https://www.shadesofcoffee.co.uk/115bar-opv-spring) | From MrShades, the original OPV-mod developer. Ships from UK. |
| **M3 washers (DIY)** | ~$3-5 | Any hardware store | Pre-load the stock 9 bar spring - see below |

(An equivalent generic 12 bar spring was also available from HuBB Hardware on Amazon at $9.97.) One Amazon reviewer who installed the 12 bar spring for Gaggiuino called it "less of a hassle than hunting down washers."

## The Washer Trick

The official Gaggiuino guide documents washer pre-loading as a legitimate budget alternative to buying a 12 bar spring:

- Place **3-4 M3 stainless steel washers** behind the existing 9 bar spring inside the OPV, increasing preload and raising the cracking pressure
- Specs: **300-series stainless, 6.9-7.1 mm outer diameter**
- Start with **4 washers if 0.5 mm thick**, or **3 washers if 0.8 mm thick**
- Adjustable: add a washer if the verified pressure is below 10 bar, remove one if above 12 bar
- Costs almost nothing and is fine-tunable, at the price of some trial and error

## Verification Procedure

After installing the 12 bar spring (or washers):

1. Insert a **blank/blind basket** in the portafilter (no coffee) - or run a backflush cycle
2. Set the Gaggiuino target to **12+ bar** and run a shot
3. Confirm the pressure reading is **10-12 bar** (static)
4. Below 10 bar → wrong/weak spring, or add a washer
5. Above 12 bar → remove a washer (washer method)

An analog gauge per [Gaggia-OPV-Pressure-Gauge-Installation-Guide](Gaggia-OPV-Pressure-Gauge-Installation-Guide.md) can cross-check Gaggiuino's transducer. Re-running this test periodically is the definitive check for spring fatigue - relevant given the current drift suspicion ([2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md)).

---

## Decision Matrix

| Your situation | OPV recommendation |
|---|---|
| US Evo Pro + Gaggiuino | **Install 12 bar spring** (or washer trick to reach 10-12 bar) |
| Pre-2023 GCP + Gaggiuino | **Keep stock 12 bar spring** (do nothing) |
| EU Evo + Gaggiuino | **Likely keep stock** (verify with blind basket test first) |
| Any Gaggia WITHOUT Gaggiuino | **Install 9 bar spring** (the classic mod) |
| Have 9 bar spring, adding Gaggiuino later | **Must change to 12 bar** or add washers |

| OPV spring | Cracks at | Gaggiuino can reach 9 bar? | Verdict |
|---|---|---|---|
| 9 bar | ~8.2 bar | No - capped ~8 bar | Inadequate |
| 10 bar | ~9.2 bar | Barely - unstable at ceiling | Marginal |
| **12 bar** | ~10.5 bar | **Yes - comfortable headroom** | **Recommended** |
| No OPV | N/A | Yes | Unsafe - never |

---

## Confidence Assessment

Overall confidence: **High (0.92)** - 47+ sources; unanimous consensus, zero dissenting opinions found.

| Finding | Confidence | Basis |
|---|---|---|
| Gaggiuino needs 10-12 bar OPV | Very High | Official docs + Zer0-bit + unanimous community |
| 9 bar spring limits pressure profiling | Very High | Hydraulic fundamentals + official docs |
| No problems with 12 bar + Gaggiuino | High | No negative reports found; limited sample |
| US Evo Pro ships with 9 bar OPV | Very High | Official docs + multiple sources |
| Washer trick is a valid alternative | High | Official docs endorse it |
| Cracking pressure ~0.8 bar below rating | Moderate | Official docs cite 8.2 bar for a 9 bar spring; could be 7.5-8.5 bar with manufacturing tolerance; less data for other ratings |
| 120V vs 240V pump dimmer behavior | Moderate-High | Spec sheets confirm equal ~15 bar max; 120V shows more fluctuation under heater voltage dips (community-reported) |

Known unknowns: exact cracking pressures across spring tolerances; Gen 3 closed-source firmware may include undocumented safety features.

---

## Sources

### Official / primary authority
- [Gaggiuino Machine-Specific Guide](https://gaggiuino.github.io/guides/machine-specific-guide.md) - official OPV instructions
- [GitHub Discussion #387 - OPV Valve Pressure](https://github.com/Zer0-bit/gaggiuino/discussions/387) - Zer0-bit's "+2 bar" rule
- [GitHub Discussion #366 - Pressure Sensing](https://github.com/Zer0-bit/gaggiuino/discussions/366)
- [GitHub Discussion #557 - Releasing Pressure](https://github.com/Zer0-bit/gaggiuino/discussions/557)
- [GitHub Discussion #202 - Dimmer Troubleshooting](https://github.com/Zer0-bit/gaggiuino/discussions/202)
- [Gaggiuino source - gaggiuino.ino (safety functions)](https://github.com/Zer0-bit/gaggiuino/blob/release/stm32-blackpill/src/gaggiuino.ino)
- [Gaggiuino source - pump.cpp](https://github.com/Zer0-bit/gaggiuino/blob/release/stm32-blackpill/src/peripherals/pump.cpp)
- [Older Gaggiuino wiki (obsolete 9-bar guidance)](https://github.com/samirkouider/gaggiuino/wiki/)
- Gaggiuino Discord (21,000+ members): https://discord.com/invite/gaggiuino-890339612441063494

### Community validation & build logs
- [Kozikow - Pimp My Gaggia](https://kozikow.blog/2024/02/28/pimp-my-gaggia/) and [Gaggiuino Build Log](https://kozikow.blog/2024/02/22/gaggiuino-build-log/)
- [Coffee Forums UK - Pressure Gauge Accuracy](https://www.coffeeforums.co.uk/threads/gaggia-classic-with-soc-top-box-pressure-gauge-accuracy.72554/)
- [Coffee Forums UK - Adjustable OPV Mod](https://www.coffeeforums.co.uk/threads/adjustable-opv-mod-for-gaggia-classic-2018-2019-is-this-worth-it.47816/)
- [Coffee Forums UK - Dimmer Switch Low Pressure Pour](https://www.coffeeforums.co.uk/threads/gaggia-dimmer-switch-low-pressure-pour.19103/page-10)
- [Home-Barista - Pump Pressure Control on GCP 2019](https://www.home-barista.com/repairs/pump-pressure-control-on-gaggia-classic-pro-2019-t70735.html)
- [Home-Barista - 12 Bar Spring into Newest Gaggia Classic](https://www.home-barista.com/espresso-machines/putting-12-bar-spring-into-newest-gaggia-classic-t91178.html)
- [Home-Barista - Is 9 Bar Ever Not Ideal?](https://www.home-barista.com/espresso-machines/is-9-bar-ever-not-ideal-gaggia-classic-opv-adjustment-t44384.html)
- [Home-Barista - Vibe Pump Profiling / PWM](https://www.home-barista.com/espresso-machines/vibe-pump-profiling-understanding-pwm-controller-t43402.html)
- [CoffeeSnobs - Gaggia Classic OPV Internals](https://coffeesnobs.com.au/forum/equipment/brewing-equipment-midrange-500-1500/909567-gaggia-classic-opv-internals)

### Vendors & products
- [Amazon - Distro Coffee Labs 12 Bar OPV Spring](https://www.amazon.com/Bar-Spring-Modification-Espresso-Machines/dp/B0CZGMW7VB)
- [Etsy - Barista Gadgets 12 Bar Spring](https://www.etsy.com/listing/1556589768/12-bar-opv-spring-for-gaggia-classic-pro)
- [Shades of Coffee - OPV Spring Mod Kit](https://www.shadesofcoffee.co.uk/gaggia-classic-opv-spring-mod-kit---standard-version-just-springs), [11.5 Bar Spring](https://www.shadesofcoffee.co.uk/115bar-opv-spring), [OPV Mod & Steam Power FAQ](https://www.shadesofcoffee.co.uk/ive-installed-the-opv-mod-and-now-i-dont-have-much-steam-power---whats-up)

### Engineering & technical references
- [Beswick Engineering - Basics of Pressure Relief Valves](https://www.beswick.com/resources/the-basics-of-pressure-relief-valves/)
- [Power & Motion Tech - Pressure-Control Valves](https://www.powermotiontech.com/hydraulics/hydraulic-valves/article/21884995/engineering-essentials-pressure-control-valves)
- [ScienceDirect - Relief Valve Overview](https://www.sciencedirect.com/topics/engineering/relief-valve)
- [Hydraulic Supermarket - Relief-Valve Pressure Override](https://www.hydraulicsupermarket.com/blog/all/relief-valve-pressure-override/)
- [Ulka Pumps - E-Series Specifications](https://ulkapumps.com/en-us/collections/ulka-pump-e-series)
- [iDrinkCoffee - 120V Ulka EAX5 Pump](https://idrinkcoffee.com/en-us/products/120v-ulka-vibratory-pump-brass-piston)
- [Espresso AF - Understanding Pressure and Flow](https://espressoaf.com/info/flow_and_pressure.html)
- [Espresso Outlet - OPV Overview](https://espressooutlet.com/blogs/blog-articles/overview-of-overpressure-valve-opv-in-espresso-machines-functionality-benefits-and-importance)
- [Espresso Hackers - Flow and Pressure Control with the Dimmer Mod](https://espressohackers.com/flow-and-pressure-control-with-the-dimmer-mod/)
- [Blackout Coffee - Gaggia Classic Feeling the Pressure](https://www.blackoutcoffee.com/blogs/the-reading-room/gaggia-classic-feeling-the-pressure)
- [Electro-Tech-Online - Triac Failure Modes](https://www.electro-tech-online.com/threads/reason-of-frequently-triac-failure-in-the-dimmer.149433/), [EEVBlog - Triac Failure Modes](https://www.eevblog.com/forum/repair/triac-failure-modes/)

### Machine information
- [Coffeedant - Gaggia Classic Evo Pro Review](https://coffeedant.com/espresso-machine/gaggia-classic-evo-pro/)
- [Stark Insider - Gaggia Classic Evo Pro (9-bar US spec)](https://www.starkinsider.com/2023/06/2023-gaggia-classic-evo-pro-features-9-bar-extraction-updated-components.html)
- [CoffeeBlog - Gaggia Classic Pro Review](https://coffeeblog.co.uk/gaggia-classic-2019-review/)

---

## Related Notes

- [Gaggia-OPV-Pressure-Gauge-Installation-Guide](Gaggia-OPV-Pressure-Gauge-Installation-Guide.md) - how to measure OPV pressure with an analog gauge
- [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) - installation guide (OPV swap is Phase 9)
- [Gaggiuino-Consistency-Maintenance-Guide](../troubleshooting/Gaggiuino-Consistency-Maintenance-Guide.md) - ongoing maintenance and consistency checks
- [Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis](../troubleshooting/Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis.md) - current symptom diagnosis implicating this spring
- [2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md) - shot-history drift analysis (June 2026)
- [Gaggiuino-Modification-Overview](Gaggiuino-Modification-Overview.md) - what Gaggiuino is and how it works
- [Gaggiuino-Post-Install-Operation-Guide](Gaggiuino-Post-Install-Operation-Guide.md) - daily operation and calibration
- [Gaggia-Classic-Evo-Pro-Best-Practices](Gaggia-Classic-Evo-Pro-Best-Practices.md) - machine best practices

---

*Consolidated 2026-07-11 from four notes created 2026-01-26; the original research notes are preserved under research-notes/.*
