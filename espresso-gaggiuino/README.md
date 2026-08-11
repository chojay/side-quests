# Gaggiuino Build Research: Gaggia Classic Evo Pro

A hardware and software side quest. In December 2025 I replaced the controls of a US **Gaggia Classic Evo Pro (RI9380/49)** with [Gaggiuino](https://gaggiuino.github.io/), an open-source espresso machine controller created by Zer0-bit: a GEN3 V4 kit built around an STM32 U585 board plus an ESP32, with a 4.3 inch touchscreen, dual load cells, and an AC dimmer driving the pump. For roughly $420-520 in kit and parts, the mod gives a budget espresso machine pressure and flow profiling, PID temperature control, real-time shot graphing, auto-stop by weight over a Bluetooth scale, and a local HTTP API that serves its full shot history. Then I ran it daily for about eight months with a DF64 Gen2 grinder and wrote down what happened.

This folder is that documentation, compiled December 2025 to July 2026: 36 docs, 8 pressure-curve charts, and pointers to five community profiles worth installing first.

## What I actually did

- **Installed the mod.** Documented the full process as a [15-phase installation checklist](machine/Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md): kit options, tools, mains wiring, the OPV spring swap, and calibration.
- **Did the OPV spring homework first.** US Evo Pro machines ship with a 9 bar OPV, and Gaggiuino needs it raised to 12 bar, the opposite of the classic 9-bar Gaggia mod. The [complete guide](machine/Gaggiuino-OPV-12-Bar-Spring-Complete-Guide.md) covers the valve mechanism, why the control loop fights a 9 bar spring, and a failure-mode table (MCU crash, triac hardware short, GPIO stuck high, power loss) checked against the actual `release/stm32-blackpill` firmware source. 47+ sources, overall confidence 0.92, zero dissenting reports found.
- **Built a shot telemetry corpus.** Pulled 639 valid shots from the machine's `/api/shots/{id}` endpoint: parallel pressure, pump-flow, weight-flow, and temperature channels plus their targets, per shot. 33 water/flush tests were excluded by rule (leaving the 606 espresso shots the drift analysis below uses), and 11 further shots were dropped because the Gaggiuino HTTP server truncated them at byte boundaries.
- **Caught the machine drifting.** Most shot timestamps were unusable (NTP-unsynced after reboots, `timestamp=0`), so the [drift analysis](case-studies/2026-06-03-Machine-Drift-Analysis.md) sequences by monotonic shot ID instead. On the Londinium profile, machine-only metrics regressed in the newest bucket: median time-to-3-bar went 3.5 s to 5.0 s (+43%) and pre-infusion pump flow 2.02 to 2.82 ml/s (+40%). Together they isolate OPV spring fatigue, not grinder or coffee changes.
- **Troubleshot like a differential diagnosis.** The [no-flow fizzing doc](troubleshooting/Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis.md) tracks a symptom that escalated May to July 2026 (first-flow delay of 5-6 s, then 7-8 s, then 15 s, then 15-30 s with a new fizzing sound), assigns explicit priors (OPV bleed ~50-60%), and orders tests cheapest and most discriminating first. Check 1 is a free two-minute tank-lid listening test.

## AI-assisted research notes

These docs came out of AI-assisted deep-research workflows (Claude), and I have tried to keep the calibration honest:

- **What it genuinely accelerated:** coverage and synthesis. Aggregating the Gaggiuino Discord (21,000+ members), Reddit (r/gaggiaclassic, r/espresso), Home-Barista, Coffee Forums UK, YouTube practitioners, and vendor docs into single cited documents would have taken weeks by hand. Inline citations and confidence ratings (star tiers, or numeric where estimated) are preserved so claims stay traceable.
- **Where it needed correction:** mod-community sources skew optimistic. One doc, the [adversarial steaming research](troubleshooting/Gaggia-Gaggiuino-Steaming-Problems-Adversarial-Research.md), exists specifically to collect disconfirming evidence and failure modes as a counterweight. Safety claims were checked against the firmware source rather than forum consensus; that check found there is no software maximum-pressure cutoff, so the OPV is the only hard mechanical cap.
- **Where research alone was not enough:** the drift and troubleshooting findings come from this machine's own telemetry, not from what the community said should happen. Single-machine data (shot counts, drift signatures) may not generalize, and the docs say so where it applies.

These files were exported from a personal Obsidian vault: frontmatter removed, wiki links converted to relative links (or flattened where the target stays private), and personal purchase details stripped. Source citations and confidence ratings are preserved inline.

## Start Here

- **New to Gaggiuino?** Read [What the mod is](machine/Gaggiuino-Modification-Overview.md), then the [OPV spring guide](machine/Gaggiuino-OPV-12-Bar-Spring-Complete-Guide.md) for the one hardware change US Evo Pro owners must understand.
- **Installing?** Follow the [15-phase installation checklist](machine/Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md), then the [post-install operation guide](machine/Gaggiuino-Post-Install-Operation-Guide.md).
- **Choosing profiles?** Start with the [community top 10](profiles/Gaggiuino-Top-10-Profiles-Community-Ranked.md) and the [selection-by-bean guide](profiles/Gaggiuino-Profile-Selection-by-Bean-Origin-and-Character.md).
- **Machine misbehaving?** The [consistency and maintenance guide](troubleshooting/Gaggiuino-Consistency-Maintenance-Guide.md) has a symptom index into the troubleshooting notes.

## machine/

| File | What it covers |
|---|---|
| [Gaggiuino-Modification-Overview.md](machine/Gaggiuino-Modification-Overview.md) | What the Gaggiuino mod is: features, Gen 2 vs Gen 3 kits, machine compatibility, cost analysis (~$420-520 kit+parts), suppliers, and community resources |
| [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md](machine/Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) | 15-phase GEN3 V4 install checklist for the Gaggia Classic Evo Pro: kit options, tools, wiring, 12-bar OPV, calibration, troubleshooting |
| [Gaggiuino-Post-Install-Operation-Guide.md](machine/Gaggiuino-Post-Install-Operation-Guide.md) | Day-to-day operation after installing Gaggiuino GEN3 V4: fixing the predicted-vs-actual weight gap, profile progression, DreamSteam, calibration |
| [Gaggia-Classic-Evo-Pro-Best-Practices.md](machine/Gaggia-Classic-Evo-Pro-Best-Practices.md) | Stock-machine fundamentals for the RI9380/49: warm-up, temperature surfing, steam timing, maintenance schedule, troubleshooting, and mod tiers |
| [Gaggiuino-OPV-12-Bar-Spring-Complete-Guide.md](machine/Gaggiuino-OPV-12-Bar-Spring-Complete-Guide.md) | Why Gaggiuino requires a 10-12 bar OPV: valve mechanism, control-loop conflict, risk assessment, sourcing options, and verification procedure |
| [Gaggia-OPV-Pressure-Gauge-Installation-Guide.md](machine/Gaggia-OPV-Pressure-Gauge-Installation-Guide.md) | How to verify brew pressure with a portafilter-mounted gauge, interpret static vs dynamic readings, and adjust the OPV to target |
| [Gaggiuino-Bluetooth-Scale-Recommendations.md](machine/Gaggiuino-Bluetooth-Scale-Recommendations.md) | Top 3 Gaggiuino-compatible BLE scales compared (Bookoo Themis Ultra, DiFluid Microbalance, Felicita Arc) plus the full esp-arduino-ble-scales list |

## profiles/

| File | What it covers |
|---|---|
| [Gaggiuino-Top-10-Profiles-Community-Ranked.md](profiles/Gaggiuino-Top-10-Profiles-Community-Ranked.md) | Ten community-ranked Gaggiuino profiles (Londinium, Blooming, IUIUIU, Turbo, Allonge, more) with parameters, reviews, decision tree, sources |
| [Gaggiuino-Profile-Comparison-Guide.md](profiles/Gaggiuino-Profile-Comparison-Guide.md) | Side-by-side mechanics of Londinium, Blooming, and IUIUIU: pressure curves, phase tables, yields, common mistakes, roast-level decision tree |
| [Gaggiuino-Default-Profile-Curves-Reference.md](profiles/Gaggiuino-Default-Profile-Curves-Reference.md) | Phase-by-phase pressure/flow tables for all six default Gaggiuino profiles, with SVG curve charts for the five profiled defaults, sourced from the community-branch JSON files |
| [Gaggiuino-Profile-Selection-by-Bean-Origin-and-Character.md](profiles/Gaggiuino-Profile-Selection-by-Bean-Origin-and-Character.md) | Matches Londinium, Blooming, IUIUIU, and Cremina profiles to bean origin, processing, roast, and density, with per-origin parameter tables |
| [Gaggiuino-Pressure-Profiling-Extraction-Parameters.md](profiles/Gaggiuino-Pressure-Profiling-Extraction-Parameters.md) | IUIUIU, blooming, and turbo/allonge profile parameters, extraction yield and timing science, and BLE scale integration on Gen3 |
| [Gaggiuino-Custom-Profiles-Import-Guide.md](profiles/Gaggiuino-Custom-Profiles-Import-Guide.md) | Profile JSON format reference plus web UI import/export steps, community profile sources, and the gaggiuino_api Python library |

### profiles/community-profiles/

Pointers to five community profiles from the official [Gaggiuino community profiles branch](https://github.com/Zer0-bit/gaggiuino/tree/community/profiles). The JSONs are community-authored and not redistributed here; each note links to the branch for download and import:

| Profile | What it is |
|---|---|
| [Allonge](profiles/community-profiles/Allonge.md) | Blooming allonge: long high-flow shot for light roasts |
| [Extractamundo Dos!](profiles/community-profiles/Extractamundo%20Dos!.md) | Turbo shot for light roasts (~15-20 s): fast fill, soak, then 3 ml/s at a 6 bar limit |
| [LMD 9-8 v1.5](profiles/community-profiles/LMD%209-8%20v1.5.md) | Pressure-to-flow profile for medium/medium-dark beans with save-the-shot transitions |
| [Phiynic v1.1](profiles/community-profiles/Phiynic%20v1.1.md) | Guided-adjustment base profile: saturation peak, pressurized extraction, taper, with per-parameter tuning notes |
| [Salami Shot v0.1](profiles/community-profiles/Salami%20Shot%20v0.1.md) | Training profile mimicking a stock fixed-flow Gaggia for the salami-shot tasting exercise |

## troubleshooting/

| File | What it covers |
|---|---|
| [Gaggiuino-Consistency-Maintenance-Guide.md](troubleshooting/Gaggiuino-Consistency-Maintenance-Guide.md) | Maintenance schedule tuned for RO water (<10 ppm TDS): backflush and screen-clean cadence, descale interval, OPV fatigue diagnosis, symptom index |
| [Gaggiuino-Descale-Procedure.md](troubleshooting/Gaggiuino-Descale-Procedure.md) | Firmware Descale routine walkthrough plus prep/run/rinse steps and why RO water pushes the interval past 12 months |
| [Gaggiuino-Partial-Teardown-Access-Guide.md](troubleshooting/Gaggiuino-Partial-Teardown-Access-Guide.md) | Five graded access levels (tank bay to 3-way solenoid) for servicing an installed GEN3 V4 without uninstalling it |
| [Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis.md](troubleshooting/Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis.md) | Ranked-cause diagnosis of a 15-30 s no-flow-then-fizzing symptom (OPV bleed as top suspect), with ordered free checks and parts tables |
| [Gaggiuino-Troubleshooting-Delayed-First-Flow.md](troubleshooting/Gaggiuino-Troubleshooting-Delayed-First-Flow.md) | 3-10 s delayed first flow after idle: solenoid back-drain vs boiler thermal contraction, targeted descale with dwell, escalation path |
| [Gaggiuino-Troubleshooting-Pump-No-Flow.md](troubleshooting/Gaggiuino-Troubleshooting-Pump-No-Flow.md) | Sound-based decision tree for pump-hums-no-water: force prime, pulse/gravity assist, differential diagnosis, electrical escalation |
| [Bloom-Profile-Troubleshooting-Fast-Extraction.md](troubleshooting/Bloom-Profile-Troubleshooting-Fast-Extraction.md) | Fixing bloom profiles that run under 35 s with thin flavor: bloom pause, pre-infusion, ramp, and decline parameters plus grind adjustment |
| [Gaggia-Gaggiuino-Steaming-Problems-Adversarial-Research.md](troubleshooting/Gaggia-Gaggiuino-Steaming-Problems-Adversarial-Research.md) | Disconfirming evidence on Gaggia steaming: 8 ranked failure modes, DreamSteam caveats, OPV-steam interaction, wiring pitfalls, Boilergate |

## case-studies/

| File | What it covers |
|---|---|
| [2026-06-03-Machine-Drift-Analysis.md](case-studies/2026-06-03-Machine-Drift-Analysis.md) | A 606-shot history audit on this machine: shot-ID bucketed drift analysis that isolates OPV spring fatigue using machine-only metrics |

## research-notes/

The original December 2025 to February 2026 research notes written while planning the build, kept for their fuller sourcing detail; several were later consolidated into the guides above. See the [research-notes index](research-notes/README.md).

## assets/

SVG pressure/flow curve charts (Matplotlib-generated) embedded by the profile references, one per default profile plus combined-overlay and extraction-comparison charts.

## Caveats

- This is personal research, not official Gaggiuino documentation. Verify anything safety-critical against the [official docs](https://gaggiuino.github.io/) before acting on it.
- The Gaggiuino mod involves mains-voltage wiring and a pressurized boiler. Build and modify at your own risk.
- Findings reflect the state of the project and community consensus as of mid-2026; the single-machine data (shot counts, drift signatures) comes from one Gaggia Classic Evo Pro and may not generalize.
