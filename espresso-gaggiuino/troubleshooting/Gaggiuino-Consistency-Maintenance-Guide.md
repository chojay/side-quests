# Gaggiuino Consistency & Maintenance Playbook

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-07-04). Wiki links flattened; sources cited inline.

> The single guide to check before troubleshooting a bad shot. Consolidates the maintenance schedule, shower screen cleaning cadence, and RO-water descale interval for this rig, and lays out the fix path for the drift already found in [2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md).

## TL;DR

This setup runs RO water at <10 ppm TDS, so scale is nearly a non-issue - maintenance here is dominated by **coffee oil buildup** and **mechanical wear (OPV spring, solenoid seat)**, not mineral deposits. Three things keep shots consistent over time:

1. **Weekly Cafiza backflush + monthly shower screen strip-clean** - removes oil buildup, which is the actual dirt source on RO water.
2. **Descale once a year, or skip a cycle if you've done a boiler/O-ring service** - RO water leaves nothing to precipitate. Don't over-descale; citric acid on a scale-free machine just wastes descaler and time.
3. **Inspect the OPV spring annually, sooner if shots drift** - springs fatigue mechanically regardless of water quality. This machine's own shot-history audit ([2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md)) already shows the signature of a fatiguing OPV (+43% time-to-pressure, +40% pump flow at low pressure over the last ~50 shots). **This is the open action item right now - see [Live Issue](#live-issue-suspected-opv-fatigue-on-this-machine) below.**

## Maintenance Schedule (tuned for RO <10 ppm TDS)

| Frequency | Task | Why |
|---|---|---|
| **Daily** | Water backflush (5 on / 5 off × 3-5), wipe + purge steam wand, brush group head | Coffee oils and grounds, not scale, are the daily dirt on this water |
| **Weekly** | Cafiza backflush (3g, 10 on / 10 off × 5), rinse, sink shot | Oil buildup in the brew path is the dominant contaminant with mineral-free water |
| **Monthly** | Remove shower screen, soak 30 min in Cafiza, scrub, reinstall. Inspect group gasket. | Standard cadence for home use regardless of water type - this is about oil/coffee fines clogging the screen holes, which happens on any water |
| **Annually** | Full Gaggiuino `Descale` cycle (steam + brew paths) per [Gaggiuino-Descale-Procedure](Gaggiuino-Descale-Procedure.md) | RO water forms effectively zero scale - annual is precautionary, not corrective. Skip a year if you did boiler service instead. |
| **Annually** | **OPV spring inspection** (blank-basket + pressure gauge test, see below) | Mechanical fatigue is independent of water quality - a spring weakens from cycling, not from scale |
| **Every 2-3 months** | Full sensor check: pressure calibration (blank basket, confirm ~12 bar) + temperature calibration | Per [Gaggiuino-Post-Install-Operation-Guide](../machine/Gaggiuino-Post-Install-Operation-Guide.md) - catches drift in the sensors themselves, separate from mechanical drift |
| **As symptoms appear** | Run the relevant troubleshooting note (see below) rather than guessing | Consistency problems on this rig have distinct signatures - matching symptom to note is faster than trial-and-error |

Water-hardness-based descale intervals (2-3 months hard tap, 4-6 months soft tap) do not apply to this setup - see [Gaggiuino-Descale-Procedure](Gaggiuino-Descale-Procedure.md) for the full reasoning and procedure.

## Shower Head / Shower Screen Cleaning

**Monthly deep clean, regardless of RO water use.** The screen's job is distributing water evenly over the puck; oil and fine coffee particles clog its holes the same way on RO water as on tap water. Scale is not the mechanism here, so RO water doesn't extend this interval the way it extends the descale interval.

- Unscrew and remove the shower screen
- Soak in Cafiza solution 30 minutes
- Scrub with a soft brush, rinse thoroughly
- Reinstall and pull a sink shot before real use
- While it's off: inspect the group gasket for cracking or flattening

A screen that's overdue shows up as: slower and more channel-prone shots, visible dry spots on the spent puck, or water exiting unevenly when you look up into the group head with the basket removed.

## Descaling on RO Water (<10 ppm TDS)

Full procedure lives in [Gaggiuino-Descale-Procedure](Gaggiuino-Descale-Procedure.md) - this section is the summary.

- **Interval: 12+ months**, or skip entirely the year you do an annual boiler/O-ring service
- Scale requires dissolved minerals to precipitate at brew temperature; RO water at <10 ppm has almost none, so there's nothing to build up
- Still run it through **both** the brew and steam paths - the Gaggiuino `Descale` menu automates this - because trace scale from any pre-RO water history, or from the steam side (which the brew-only path never reaches), can still exist
- Descale sooner if: you switch water sources, service the boiler, off-flavors persist after a Cafiza backflush, or the machine sits idle 3+ weeks
- **Do not use Cafiza as a substitute for descaling.** Cafiza removes oils, not calcium carbonate. If your only recent "descale" was a Cafiza backflush, true descaling is still overdue (this exact confusion caused a [delayed-first-flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) misdiagnosis on this machine in May 2026).

## Live Issue: Suspected OPV Fatigue on This Machine

This machine's own 606-shot drift audit ([2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md)) found the following, comparing the most recent ~50 shots against the prior several hundred:

- Time to reach 3 bar: **+43%** (3.5s → 5.0s median, Londinium profile)
- Pump flow while under 3 bar: **+40%** (2.02 → 2.82 ml/s)
- Real-shot pre-pressure delay: median jumped from ~1s (stable for ~500 shots) to **2.3s**, with one shot taking 27.5s to begin pressurizing

The combination - pump pushing *more* water while taking *longer* to build pressure - points to water escaping the brew circuit before it reaches the puck, not a weakening pump (pumps lose flow as they degrade, they don't gain it). Ranked by likelihood:

1. **OPV spring fatigue** (most likely): a tired spring cracks open earlier than its rated pressure, silently bleeding pump output back to the tank instead of into the puck. This directly matches "more flow, slower pressure build." See [Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md) for why Gaggiuino needs the OPV cracking pressure comfortably above 9 bar in the first place - a fatigued spring erodes that margin over time even if it was correctly set at install.
2. Shower/puck screen scaling (less likely given RO water, but cheap to rule out - see monthly cleaning above)
3. Group gasket leak (would be visually obvious during a shot)
4. Pump wear (ruled least likely - a degrading pump loses flow, this data shows flow increasing)

### Corroborating Data Point (2026-07-04)

Observed: water taking **up to 15 seconds** to reach the shower screen. That's beyond the 3-10s range that ordinary 3-way solenoid back-drain explains, and too large for benign boiler thermal contraction (which caps out under 1 second of delay). Volume math puts it at ~120-150 ml of air at the Ulka's full-flow rate - roughly 2-3x the ~40-60 ml normal post-solenoid brew-path volume. This is consistent with the same OPV-bleed signature already found in the drift audit (real shots there hit pre-pressure delays up to 27.5s in the most recent bucket). Full escalation writeup: [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md).

### Action Item (Not Yet Done)

1. **Blank-basket pressure test**: lock in the blind basket, run the pump at full output, and read the gauge. If peak pressure reads meaningfully below the ~12 bar the OPV is set for, the spring has weakened. This is a 5-minute test, no disassembly required. **Do this first** - it's the fastest check and matches both the drift-audit signature and the 15s shower-head delay.
2. If confirmed: replace the OPV spring (~$15-20, same 12-bar part used at install - see [Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md) for sourcing) rather than adding washers, since the existing spring is already known to have fatigued once.
3. Re-run the shot-history drift comparison after 50-100 new shots on the replaced spring to confirm the metrics return to baseline (TT3bar ~3.5s, flow_lowP ~2.0 ml/s on Londinium).
4. Log the outcome in the incident log pattern used elsewhere in these notes (see [Gaggiuino-Troubleshooting-Pump-No-Flow](Gaggiuino-Troubleshooting-Pump-No-Flow.md) for the format).

This is the highest-value single fix available right now for restoring shot-to-shot consistency - everything else in this guide is preventive maintenance, but this is an active, already-diagnosed issue.

## Symptom → Note Quick Index

| Symptom | Note |
|---|---|
| Pressure builds slower / more pump flow at low pressure than it used to | You're reading it - see [Live Issue](#live-issue-suspected-opv-fatigue-on-this-machine) above and [2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md) |
| Pump hums/buzzes, no water at all | [Gaggiuino-Troubleshooting-Pump-No-Flow](Gaggiuino-Troubleshooting-Pump-No-Flow.md) |
| Water delayed 3-10s after a few hours idle, then flows normally | [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) |
| Water delayed **10-15s or more** before reaching the shower screen | Escalation, not routine back-drain - check the OPV first ([Live Issue](#live-issue-suspected-opv-fatigue-on-this-machine) above), then see [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) |
| Shot tastes off despite normal flow/pressure | Weekly Cafiza backflush overdue, or true descale overdue (Cafiza ≠ descaler) |
| Bloom/pre-infusion phase extracting too fast | [Bloom-Profile-Troubleshooting-Fast-Extraction](Bloom-Profile-Troubleshooting-Fast-Extraction.md) |
| Steam power or milk texture degraded | [Gaggia-Gaggiuino-Steaming-Problems-Adversarial-Research](Gaggia-Gaggiuino-Steaming-Problems-Adversarial-Research.md) |
| Pressure won't follow the profile at all | Verify OPV is actually at 12 bar (see Live Issue above) and that the AC dimmer module is wired correctly |

## Related Notes

- [2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md) - the shot-history audit this guide's live issue is drawn from
- [Gaggiuino-Descale-Procedure](Gaggiuino-Descale-Procedure.md) - full descale procedure and RO-water cadence reasoning
- [Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md) - why Gaggiuino needs 10-12 bar OPV, sourcing for replacement springs
- [Gaggia-Classic-Evo-Pro-Best-Practices](../machine/Gaggia-Classic-Evo-Pro-Best-Practices.md) - stock machine maintenance schedule and daily/weekly backflush steps
- [Gaggiuino-Troubleshooting-Pump-No-Flow](Gaggiuino-Troubleshooting-Pump-No-Flow.md) / [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) - sibling diagnostic notes for flow problems
- [Gaggiuino-Post-Install-Operation-Guide](../machine/Gaggiuino-Post-Install-Operation-Guide.md) - sensor calibration reminders

## Sources

- [Papel Espresso - Troubleshooting Boiler Fill and Pump Issues in Gaggiuino Systems](https://www.papelespresso.com/troubleshooting-boiler-fill-and-pump-issues-in-gaggiuino-systems/)
- [Papel Espresso - Gaggia Classic OPV Spring Replacement Guide](https://www.papelespresso.com/replacing-opv-spring-gaggia/)
- [Whole Latte Love - Semi-Automatic Espresso Machine Cleaning: How & How Often](https://www.wholelattelove.com/blogs/how-to/semi-automatic-espresso-machine-cleaning-how-how-often)
- [Espresso Outlet - How to Clean Espresso Machine Shower Screens](https://espressooutlet.com/blogs/news/how-to-clean-espresso-machine-shower-screens)
- [Home-Barista - Cleaning Routine and Frequency Thread](https://www.home-barista.com/espresso-machines/cleaning-routine-and-frequency-t72216.html)
- Internal: this machine's own shot-history data (639 shots, [2026-06-03-Machine-Drift-Analysis](../case-studies/2026-06-03-Machine-Drift-Analysis.md))
