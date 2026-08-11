# Gaggiuino Descale Procedure - Gaggia Classic Evo Pro

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-05-27). Wiki links flattened; sources cited inline.

## TL;DR for this setup

With RO water at <10 ppm TDS, scale formation is effectively zero. There are no dissolved minerals to precipitate at brewing temperature. The Gaggiuino `Descale` menu is still worth running as a **precautionary annual rinse**, but the 3-6 month cadence that generic Gaggia guides recommend does not apply.

**Realistic interval for this rig: 12+ months, or skip entirely if doing annual boiler O-ring service.**

See [Gaggiuino-Modification-Overview](../machine/Gaggiuino-Modification-Overview.md) for the Gaggiuino feature set this note assumes.

## What the Gaggiuino "Descale" menu does

The `Descale` option (Settings -> Descale on the Gen 3 V4 touchscreen) launches a built-in firmware routine introduced/refined in [PR #527 "Descale, fixes and improvements"](https://github.com/Zer0-bit/gaggiuino/pull/527).

It runs an automated state machine that:

- Holds the boiler at a moderate temperature (heat accelerates descaler action without boiling the solution)
- **Pulses the pump in short bursts** followed by idle soak intervals
- Cycles through alternating phases for the brew path and the steam path
- Tracks progress and prompts the user when to manually open/close the steam knob

It **automates** the choreography of a manual descale ("pump 100 ml, wait 5 min, repeat"), but it does **not** replace:

- Prep (blind basket, descaler-loaded tank)
- The post-descale clean-water flush
- The "sink shot" purge before brewing again

## Why both brew AND steam paths matter

The Gaggia Classic single-boiler geometry:

- **Steam wand outlet** is at the **top** of the boiler
- **Brew path** draws from the **bottom**

If solution only exits through the group head, the upper interior of the boiler (and the steam wand internals) never contact descaler. Scale that forms in the steam side survives. This is why the Gaggiuino routine cycles through both paths, and why the official Gaggia procedure explicitly calls for descaler through the steam wand first.

## Procedure

### Prep

1. Confirm machine is off and cool
2. Empty water tank
3. Mix descaling solution per product directions:
   - **Gaggia Official Decalcifier** (250 ml bottle, 1:8 dilution): only descaler officially approved by Gaggia
   - **OR Dezcal** (1 oz per 32 oz water): third-party citric-acid based, widely used
   - Never use straight vinegar (leaves residue and odor)
4. Fill tank with the mixed solution
5. Insert **blind basket** into portafilter, lock into group head
6. Place heat-safe catch containers (~500 ml each) under both the group head and the steam wand
7. Empty the drip tray

### Run

1. Power on, let machine reach standby
2. On the Gaggiuino touchscreen: **Menu -> Settings -> Descale**
3. Confirm/start the cycle
4. When the screen indicates the steam-flow phase, **open the steam knob ~1/4 turn** so solution exits the wand into the catch container
5. Close the steam knob when the program transitions back to the brew-flow phase
6. Let the cycle run to completion (~20-40 min depending on firmware version)
7. Power down when prompted

### Rinse (critical, do NOT skip)

1. Remove tank, rinse thoroughly with clean water
2. Refill with **fresh water only**: use your RO water
3. Power back on
4. Flush a **full tank** through both outlets:
   - Long manual flush through the group head (blind basket out)
   - Open steam knob and let ~200 ml flush through the wand
   - Continue alternating until tank is nearly empty
5. Repeat with a **second full tank** of clean water
6. Pull and discard 2-3 espresso shots ("sink shots") before brewing for real

## Cadence

| Water source | Recommended interval |
|---|---|
| Tap, hard (>150 ppm) | 2-3 months |
| Tap, soft (50-100 ppm) | 4-6 months |
| **RO at <10 ppm (this setup)** | **12+ months, or skip with annual service** |

### Why so infrequent

Scale forms when dissolved minerals exceed solubility at high temperature. RO water at <10 ppm has nearly zero dissolved minerals; there is nothing to precipitate.

**If you ever start remineralizing** (RPavlis recipe, Third Wave Water, BWT filter), recompute the cadence from that day forward. The "no scale" assumption no longer holds.

## When to descale anyway

- After switching water sources
- After any boiler service or O-ring replacement (purges residue)
- If off-flavors persist after backflushing with Cafiza
- Before extended storage (3+ weeks)

## Related Notes

- [Gaggia-Classic-Evo-Pro-Best-Practices](../machine/Gaggia-Classic-Evo-Pro-Best-Practices.md): machine-specific best practices
- [Gaggiuino-Modification-Overview](../machine/Gaggiuino-Modification-Overview.md): Gaggiuino features overview
- [Gaggiuino-Post-Install-Operation-Guide](../machine/Gaggiuino-Post-Install-Operation-Guide.md): daily operation reference

## Sources

- [Gaggiuino PR #527 - Descale, fixes and improvements](https://github.com/Zer0-bit/gaggiuino/pull/527)
- [Official Gaggiuino docs](https://gaggiuino.github.io/)
- [Whole Latte Love - Gaggia Classic Pro descale procedure](https://www.wholelattelove.com/blogs/support-articles/360061291754)
- [Pure Earth - Gaggia Classic Pro descale & maintenance](https://pureearthcoffee.com/blogs/equipment-gear/gaggia-classic-pro-descale-maintenance-guide)
