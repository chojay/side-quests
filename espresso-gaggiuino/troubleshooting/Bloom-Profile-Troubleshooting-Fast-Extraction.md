# Bloom Profile Troubleshooting - Fast Extraction & Low Complexity

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-03-03). Wiki links flattened; sources cited inline.

> Diagnosing and fixing bloom profiles on [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md) that extract too fast with thin, simple flavor. Covers why adjusting your [Bluetooth scale](../machine/Gaggiuino-Bluetooth-Scale-Recommendations.md) weight target alone won't fix the issue, and which profile phase parameters to change instead.

---

## The Problem

- Shot runs fast (under 35s total)
- Flavor is thin, simple, lacking sweetness and complexity
- Using a bloom profile but results feel closer to a flat 9-bar shot

---

## Key Concept: Scale Weight vs. Profile Phases

**These are two independent variables:**

| Control | What It Does | Where to Change |
|---------|-------------|-----------------|
| **Bluetooth scale weight** | Sets the *end point* - when the shot stops (yield target) | Scale app or [Gaggiuino global stop condition](../machine/Gaggiuino-Post-Install-Operation-Guide.md) |
| **Profile phases** | Controls *how water is delivered* - pressure curves, bloom pause, ramp rates | Gaggiuino touchscreen or web UI profile editor |

**Changing the weight on the scale only changes your brew ratio** (e.g., 1:2 → 1:2.5). It does **not** change the bloom behavior that causes fast, uneven extraction. To fix bloom issues, you must edit the profile phases.

For profile editing basics, see [Gaggiuino-Custom-Profiles-Import-Guide](../profiles/Gaggiuino-Custom-Profiles-Import-Guide.md).

---

## Bloom Profile Anatomy

A typical bloom profile has 4 phases (see [Profile Comparison Guide](../profiles/Gaggiuino-Profile-Comparison-Guide.md) and [Blooming deep dive](../profiles/Gaggiuino-Pressure-Profiling-Extraction-Parameters.md)):

```
Phase 1: Pre-infusion (wet the puck)
  └─ Flow mode ~4 ml/s → stop when pressure reaches ~3 bar

Phase 2: Bloom/Soak (CO2 degassing)    ← MOST IMPORTANT PHASE
  └─ Flow = 0 (pump off) → stop after time (e.g., 25-30s)

Phase 3: Ramp to extraction pressure
  └─ Pressure ramp 0→9 bar over ~5s

Phase 4: Main extraction
  └─ Pressure hold or gentle decline → stop on weight (scale)
```

---

## What to Adjust (In Priority Order)

### 1. Extend the Bloom Pause (Phase 2)

This is the single biggest lever for improving complexity.

| Parameter | Likely Current Value | Recommended |
|-----------|---------------------|-------------|
| Stop condition: `time` | 5–10 seconds | **20–30 seconds** |
| Flow target | 0 ml/s (pump off) | Keep at 0 |

**Why it matters:** The bloom pause lets CO2 trapped in fresh coffee escape. Short pauses (under 10s) mean the puck is still degassing when full pressure hits, creating channeling and uneven extraction. Scott Rao's original blooming profile specifies **25–30 seconds** of bloom pause.

### 2. Check Pre-Infusion Saturation (Phase 1)

| Parameter | What to Check | Adjustment |
|-----------|--------------|------------|
| Flow target | ~4 ml/s | Lower to 2–3 ml/s for gentler saturation |
| Stop: `pressureAbove` | 2–3 bar | Try 3–4 bar for fuller puck saturation before bloom |
| Restriction (pressure ceiling) | Check value | Ensure ~3 bar to prevent premature channeling |

### 3. Soften the Pressure Ramp (Phase 3)

| Parameter | Too Aggressive | Recommended |
|-----------|---------------|-------------|
| Transition time | Under 3 seconds | **5–8 seconds** |
| End pressure | 9 bar | Try **7–8 bar** - bloom profiles often taste better at lower peak pressure |
| Transition curve | INSTANT or LINEAR | Try EASE_IN_OUT for gentler ramp |

### 4. Consider a Declining Extraction (Phase 4)

Instead of flat pressure, try a gentle decline:

| Parameter | Flat (current) | Declining (try this) |
|-----------|---------------|---------------------|
| Start pressure | 9 bar | 8–9 bar |
| End pressure | 9 bar | **6 bar** |
| Transition time | - | ~20 seconds |

This mimics the tail end of a [Londinium lever profile](../profiles/Gaggiuino-Profile-Comparison-Guide.md) and increases body and sweetness.

### 5. Grind Adjustment (Secondary)

After changing profile parameters, adjust grind on the DF64 if needed:

- Grind **1–2 clicks finer** - longer bloom time means the puck flows slightly faster once pressure hits
- Bloom profiles generally need **coarser grinds** than flat 9-bar
- If the shot chokes after extending bloom, go 1 click coarser

---

## Diagnostic Checklist

Use the Gaggiuino real-time graph during your shot to diagnose:

- [ ] **Total shot time**: Should be 45–65s for bloom profiles (not 25–35s)
- [ ] **Bloom phase duration**: Verify the soak phase actually lasts 20–30s on the graph
- [ ] **Pressure during bloom**: Should drop near 0 bar (pump fully off)
- [ ] **Flow spike after bloom**: A sudden flow spike when pressure ramps = puck not fully saturated → increase pre-infusion pressure ceiling
- [ ] **Channeling visible**: If using a bottomless portafilter, look for spritzers during early extraction

---

## Expected Results After Adjustment

| Metric | Before (too fast) | After (dialed in) |
|--------|-------------------|-------------------|
| Total time | 25–35s | 45–65s |
| Bloom pause | 5–10s | 20–30s |
| Peak pressure | 9 bar | 7–8 bar |
| Flavor | Thin, simple, acidic | Sweet, complex, layered |
| Extraction yield | ~19–21% | ~25–29% |

See [extraction yield comparison](../profiles/Gaggiuino-Pressure-Profiling-Extraction-Parameters.md) for how blooming compares to other profiles.

---

## Related Notes

- [Gaggiuino-Profile-Comparison-Guide](../profiles/Gaggiuino-Profile-Comparison-Guide.md) - Side-by-side: Londinium vs Blooming vs IUIUIU
- [Gaggiuino-Top-10-Profiles-Community-Ranked](../profiles/Gaggiuino-Top-10-Profiles-Community-Ranked.md) - Community-ranked profiles (Blooming is #2)
- [Gaggiuino-Pressure-Profiling-Extraction-Parameters](../profiles/Gaggiuino-Pressure-Profiling-Extraction-Parameters.md) - Deep dive on blooming mechanics and parameters
- [Gaggiuino-Custom-Profiles-Import-Guide](../profiles/Gaggiuino-Custom-Profiles-Import-Guide.md) - How to edit and import profiles
- [Gaggiuino-Bluetooth-Scale-Recommendations](../machine/Gaggiuino-Bluetooth-Scale-Recommendations.md) - BLE scale setup and predictive stop-on-weight
- [Gaggiuino-Post-Install-Operation-Guide](../machine/Gaggiuino-Post-Install-Operation-Guide.md) - Day-to-day operation and scale configuration
