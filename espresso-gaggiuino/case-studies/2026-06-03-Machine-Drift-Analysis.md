# Machine Drift Analysis (Gaggiuino, June 2026)

> Case study: shot-history data audit from a single Gaggia Classic Evo Pro + Gaggiuino (GEN3) machine, June 2026. Exported from a personal Obsidian vault; wiki links flattened.

> A 600+ shot history audit on one Gaggia Classic Evo Pro + Gaggiuino machine. Compares early vs recent shots focused on **auxiliary / machine-only** behaviors (water flow, pump fill time, temperature stability), NOT bean- or grind-dependent metrics. Goal: detect mechanical or hydraulic drift in the [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md) rig.

## Methodology

- Source: 639 valid shots pulled from the Gaggiuino `/api/shots/{id}` endpoint on 2026-06-03 (raw JSON archived locally).
- Excluded: 33 water/flush tests (`maxP < 3 bar` or `endWeight = 0`).
- Bucketed by **shot ID** (monotonic counter), not timestamp - many shots had `timestamp=0` from post-reboot NTP-unsynced state.
- Compared only **within the same profile** (apples-to-apples). Beans/grind/dose varied but **time-to-pressure**, **pump flow during low-P**, **temp delta**, and **steady-state temp** are machine-dominant.

## Metrics

| Metric | What it measures | Drift = |
|---|---|---|
| `timeToPressure3bar_s` | Seconds from shot start until measured pressure first reaches 3 bar | Pump fill rate + puck pre-saturation. Longer => slower fill (pump weakening, scale, restriction). |
| `meanFlow_lowP_mlS` | Mean pumpFlow while pressure was < 3 bar (pre-infusion regime) | True pump volumetric output. Higher than expected may indicate the OPV is bleeding off pressure (so pump runs uncapped). |
| `meanTempDelta_C` | Mean of `(targetTemp - actualTemp)/10` across the shot | Boiler thermal lag. More negative (overshoot) is fine if controlled; large positive (undershoot) means recovery problems. |
| `meanTemp_steady_C` | Mean actual temp when within +/- 5C of target | Boiler steady-state setpoint accuracy. |

## Findings - by profile + shot-ID bucket

### Londinium (256 real shots, dominant since shot ~270)

| Bucket | N | TT3bar (s, median) | flow_lowP (ml/s, median) | tempΔ | tempSS |
|---|---:|---:|---:|---:|---:|
| 1-99    | 12 | 3.85 | 2.22 | -0.94 | 92.94 |
| 100-199 | 59 | 3.6  | 2.05 | -0.91 | 92.91 |
| 200-299 | 32 | 3.7  | 2.04 | -0.93 | 92.93 |
| 300-399 | 31 | 3.9  | 2.18 | -0.95 | 92.95 |
| 400-499 | 41 | 4.0  | 2.21 | -0.97 | 92.97 |
| 500-599 | 41 | **3.5**  | **2.02** | -0.91 | 92.91 |
| **600-649** | **23** | **5.0** | **2.82** | -0.86 | 92.86 |

**Reading**: Bucket 500-599 was the best in the series (fastest pressure build, lowest pump flow during PI - both signs of a tight, hydraulically-correct puck path). Then bucket 600-649 shows a clear regression:
- `TT3bar` jumps from **3.5s -> 5.0s** (median, +43%)
- `flow_lowP` jumps from **2.02 -> 2.82 ml/s** (+40%)
- `tempSS` drops 0.05C (negligible)

The "pump pushes more water but takes longer to build pressure" combination strongly suggests **water is escaping the head circuit faster than the puck can swallow it**. Most likely culprits, in priority order:

1. **OPV spring fatigue / OPV bleed**: spring sets the relief threshold; if it has fatigued the OPV opens earlier => water dumps through the bleed return instead of feeding the puck. Matches the symptom of more pump flow at lower pressure. See [Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md) and [Gaggiuino-12-Bar-OPV-Spring-Risk-Assessment](../research-notes/Gaggiuino-12-Bar-OPV-Spring-Risk-Assessment.md).
2. **Puck screen / shower screen scaling**: deposits create channels that release water as a sheet rather than soaking the puck. Less likely to also raise pump flow.
3. **Group gasket leak**: water escapes around the portafilter. Would also be visually obvious during shots.
4. **Pump itself**: vibratory pumps degrade by losing peak flow, not by gaining flow. So the pump is **probably not** the cause (recent flow is higher, not lower).

### Blooming espresso (251 real shots)

| Bucket | N | TT3bar (s, median) | flow_lowP (ml/s, median) | tempΔ | tempSS |
|---|---:|---:|---:|---:|---:|
| 100-199 | 11 | 8.2  | 0.92 | -0.69 | 93.69 |
| 200-299 | 59 | 8.6  | 1.16 | -0.99 | 93.99 |
| 300-399 | 62 | 8.7  | 1.23 | -1.00 | 94.00 |
| 400-499 | 49 | 8.0  | 1.03 | -0.99 | 93.99 |
| 500-599 | 54 | 9.45 | 1.27 | -1.00 | 94.00 |
| **600-649** | **14** | **10.9** | 1.16 | -0.77 | 93.77 |

**Reading**: Same pattern, weaker signal. `TT3bar` drifted from 8.0s (bucket 400-499) to 10.9s (bucket 600-649), but Blooming has a long zero-flow bloom phase that itself adds variability. Worth noting tempSS dropped 0.23C in the latest bucket.

### IUIUIU Classic (108 real shots, dominant in early period)

| Bucket | N | TT3bar (s, median) | flow_lowP (ml/s, median) | tempΔ | tempSS |
|---|---:|---:|---:|---:|---:|
| 1-99    | 80 | 10.95 | 1.87 | -0.95 | 93.95 |
| 100-199 | 20 | 11.05 | 1.08 | -0.99 | 94.00 |
| 200-299 | 7  | 12.30 | 2.34 | -0.68 | 93.68 |
| 300-399 | 1  | 12.50 | 2.73 | -0.99 | 93.99 |

Stable in the early window, then sparse data after this profile fell out of rotation.

## Synthesis

Across all three profiles, the **600-649 bucket shows the largest relative drift** in two metrics that should not depend on coffee:

| Profile | TT3bar drift | flow_lowP drift |
|---|---|---|
| Londinium | **+1.5s (+43%)** | **+0.8 ml/s (+40%)** |
| Blooming espresso | +2.9s (+36%) | +0.0 to -0.1 (flat) |

The Londinium signature is the clearest. Recent test/flush shots corroborate this - the very-recent flushes show `maxFlow = 10+ ml/s` at `maxP = 0.2-1.0 bar`, which is what an underpowered or bleeding hydraulic path looks like at full pump.

## Time-to-first-water analysis (the "why does water take 15s?" question)

Diagnostic flush tests (Londinium profile + empty PF) were run to measure exactly this delay. The data is conclusive.

### Flush-test delays (`pump_on -> water_at_cup`, Londinium profile, empty PF)

| Shot ID Bucket | N flush tests | Delay median (s) | Delay max (s) |
|---|---:|---:|---:|
| 1-199    | 2 | 8.50 | 15.70 |
| 200-399  | 2 | 1.80 | 3.30 |
| 400-499  | 5 | 0.70 | 8.30 |
| 500-599  | 3 | 0.20 | 7.50 |
| **600-649** | **9** | **7.60** | **8.00** |

The last 9 flush tests all show **7-8 second delays**, every single one. This is no longer "occasional" - it is the steady state.

**Volume calc** (per [the volume calculation in the troubleshooting note](../troubleshooting/Gaggiuino-Troubleshooting-Delayed-First-Flow.md)): Ulka pump at full flow ~10 ml/s × 7.6 s = **~76 ml of air to compress and push**. That is larger than the typical 40-60 ml post-3-way-solenoid brew path. Two possibilities:
1. The back-drain is reaching further upstream than the solenoid (boiler-side check valve also leaking).
2. The pump is delivering less than its 10 ml/s nominal in the recent bucket (matches the OPV-bleed hypothesis from the drift analysis above).

### Pre-pressure delay in REAL shots (Londinium)

This is the part that matters for actual espresso (not just flushing).

| Shot ID Bucket | N real shots | `pump_on -> P>=0.5 bar` median (s) | max (s) |
|---|---:|---:|---:|
| 1-199    | 71 | 0.90 | 3.70 |
| 200-399  | 63 | 1.20 | 4.40 |
| 400-499  | 41 | 1.20 | 3.00 |
| 500-599  | 41 | 0.80 | 7.50 |
| **600-649** | **23** | **2.30** | **27.50** |

The median time before pressure even starts to climb on a real shot has jumped from ~1s (stable for the first ~500 shots) to **2.3s** in the latest bucket - 2-3x the baseline. The maximum hit 27.5s (a single real shot that took nearly half a minute to begin pressurizing). The delay is no longer confined to flushes.

## Recommended diagnostics

1. **OPV check**: simplest first test. Pull a single blank-portafilter shot at full pump and read the pressure gauge. If peak < 9 bar with the OPV set to 9 bar, the spring has weakened. References: [Gaggia-OPV-Pressure-Gauge-Installation-Guide](../machine/Gaggia-OPV-Pressure-Gauge-Installation-Guide.md), [Gaggiuino-OPV-Spring-12-Bar-Analysis](../research-notes/Gaggiuino-OPV-Spring-12-Bar-Analysis.md).
2. **Descale**: scale build-up in the boiler line raises hydraulic restriction (would slow flow, not speed it). Less likely given the symptom direction, but overdue if not done in 6+ months. See [Gaggiuino-Descale-Procedure](../troubleshooting/Gaggiuino-Descale-Procedure.md).
3. **Shower / puck screen inspection**: pull, inspect, deep-clean. Cheap to do, hard to evaluate without trying.
4. **Group gasket inspection**: pull the shower screen, look for crushed/torn gasket edges. Replace if doubtful (~$5 part).
5. **Re-run aux metrics in 2 weeks**: if the drift continues to worsen, escalate to OPV replacement.

## Caveats

- Bean batch, grind setting, dose, and puck prep all varied across shots - drift is inferred only from **machine-side** quantities.
- The shot timestamps are mostly unusable (many are uptime seconds from post-reboot states without NTP sync). All sequencing is by ID.
- Bucket 600-649 has only 23 Londinium real shots - sample size is smaller than ideal. Re-check after another 50-100 real shots.
- 11 shots (id 52, 60, 67, 168, 172, 196, 306, 339, 461, 497, 629) were truncated by the Gaggiuino HTTP server at byte boundaries and excluded.

## See also

- [Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md)
- [Gaggiuino-12-Bar-OPV-Spring-Risk-Assessment](../research-notes/Gaggiuino-12-Bar-OPV-Spring-Risk-Assessment.md)
- [Gaggiuino-Descale-Procedure](../troubleshooting/Gaggiuino-Descale-Procedure.md)
- [Gaggiuino-Troubleshooting-Delayed-First-Flow](../troubleshooting/Gaggiuino-Troubleshooting-Delayed-First-Flow.md)
