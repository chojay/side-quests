# Gaggiuino Troubleshooting: Pump Runs But No Water Flows

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-05-16). Wiki links flattened; sources cited inline.

> **TL;DR**: If the pump hums or buzzes but no water comes out at the grouphead AND no water comes out during Flush, **try [Step 1: Force Prime via Steam Wand](#step-1---force-prime-free-2-minutes) first**. Resolves the majority of cases in under 2 minutes with no disassembly.

This guide applies to the [Gaggia Classic Evo Pro](../machine/Gaggia-Classic-Evo-Pro-Best-Practices.md) with the [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md) GEN3 V4 mod installed. The Ulka EX5 vibratory pump is shared with stock Gaggia, so Step 1-3 also apply to unmodded machines. Step 4 covers Gaggiuino-specific electrical paths.

---

## Sound-Based Decision Tree (Start Here)

Trigger **Flush** with no portafilter. What does the pump sound like?

| Pump Sound | Most Likely Cause | Go To |
|---|---|---|
| **Humming / buzzing, no water** | Airlocked Ulka pump (can't push air) | [Step 1: Force Prime](#step-1---force-prime-free-2-minutes) |
| **Normal rattle, water delayed 3-10s then flows normally** (after few-hour idle) | Air gap in brew path downstream of pump (typically 3-way solenoid back-drain or boiler thermal contraction) | See [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) |
| **Normal rattle, no water at grouphead** | 3-way solenoid valve scaled / stuck | [Step 3: Differential Diagnosis](#step-3---differential-diagnosis-if-steps-1-2-fail) |
| **Louder / labored than usual, no water** | Scaled intake screen or failing pump piston | [Step 3: Differential Diagnosis](#step-3---differential-diagnosis-if-steps-1-2-fail) |
| **Total silence** | Electrical fault: SSR, dimmer/PSM, or wiring (Gaggiuino-specific) | [Step 4: Electrical](#step-4---electrical-escalation-gaggiuino-specific) |

**Why the sound matters**: Vibratory pumps (Ulka EX5) can move liquid efficiently but **cannot push air**. A buzzing pump that produces no water means it's getting power and trying to work, but there's a bubble in the intake line breaking suction. A silent pump is an entirely different problem (no power reaching it).

---

## Common Triggers (What Probably Just Happened)

Airlocks usually happen after one of these events:

- **Refilled / changed water tank** - bubble introduced as you re-seated the tank
- **Tank ran near-empty** - air pulled into the intake hose
- **Descaled** - loosened scale clogging the 3-way solenoid downstream
- **Long idle period** (days/weeks) - pump lost prime, water settled in lines
- **Updated Gaggiuino firmware / wiring** - reseated connections, changed PSM/PWM mode, or shifted pin assignments
- **Moved the machine** - shifted internal hoses or loose connections

---

## Step 1 - Force Prime (Free, 2 Minutes)

The single most common fix. Resolves the vast majority of "pump hums but no water" cases. No disassembly, no risk.

1. **Fill the water tank** above the intake hose end (look for the MAX line)
2. **Wiggle the tank** firmly in place to dislodge any bubble at the intake screen
3. **Remove the portafilter** (so the brew path is unrestricted)
4. **Open the steam wand valve FULLY** (this is the key trick - creates a low-resistance escape path for trapped air)
5. **Trigger Flush** on the Gaggiuino touchscreen
6. **Expected**: within 5-30 seconds, water sputters then streams from the steam wand
7. Once water flows steadily from the wand, **close the steam valve**. Flush should now push water through the grouphead normally
8. Run one or two full Flush cycles to fully purge any remaining air

> ⚠️ **If no water at the steam wand within ~30 seconds, STOP the Flush.** Don't run the Ulka EX5 dry continuously. The Ulka has an internal thermal fuse that **fails permanently** if overheated dry. Move to Step 2 (pulsed approach) instead.

---

## Step 2 - Pulse + Gravity Assist (If Step 1 Didn't Take)

1. With steam valve still fully open, trigger Flush in **5-second pulses** with 10-second rests between them
   - Gives the pump short bursts to grab a water column without overheating dry
2. Optionally **gravity-feed the intake**:
   - Pull the water tank out
   - Lift it slightly above the machine top
   - Re-seat firmly to pre-load the intake hose with water
   - Try Flush again with steam valve open
3. If your Gaggiuino profile build includes the **Manual Flow** page, use it to command 100% PWM pump output directly. Useful for priming because no profile is modulating power. (Pre-0.2.3 PWM mode is more reliable for priming than the newer PSM mode that requires zero-crossing detection.)

If pump still buzzes with no water after ~3 minutes of cumulative pulsed effort, move to Step 3.

---

## Step 3 - Differential Diagnosis (If Steps 1-2 Fail)

The fault is no longer simple air. Use what you observe to narrow:

### A. Water exits steam wand but NOT grouphead during Flush

- **Cause**: 3-way solenoid valve is scaled or stuck closed
- **Fix**:
  1. Run a full descale cycle (Gaggia Decalcifier or Dezcal)
  2. **CRITICAL**: Run descaler through the steam wand FIRST, then through the group head (see [Best Practices > Maintenance > Descaling](../machine/Gaggia-Classic-Evo-Pro-Best-Practices.md))
  3. If descaling doesn't free it, the solenoid can be disassembled and soaked in citric acid
- **Reference**: papelespresso.com 3-way solenoid troubleshooting guide

### B. Pump buzzes much louder / labored than usual

- **Cause**: Scaled intake screen or failing pump piston
- **Fix**:
  1. Pull the water tank out
  2. Inspect the intake mesh filter inside the machine (where the tank seats)
  3. Clean if scaled (descale or soak in citric acid)
  4. If clean and pump still labors, the Ulka piston may be failing. Replacement Ulka EX5 is ~$30-40

### C. Pump suddenly goes silent mid-attempt

- **Cause**: Ulka thermal fuse just opened (you ran it dry too long)
- **Fix**:
  1. **Stop everything immediately**
  2. Let it cool 30+ minutes (some report longer, up to a few hours)
  3. Try again - if pump now hums, you got lucky and the fuse reset
  4. If permanently silent after cooldown, the Ulka pump is dead. Replace.

### D. Water leaks somewhere inside the case during Flush

- Loose hose clamp or burst hose. Unplug, open the case, visually inspect every silicone hose connection.

---

## Step 4 - Electrical Escalation (Gaggiuino-Specific)

**Only reach this if the pump is TOTALLY SILENT** during Flush (no hum, no buzz, nothing). The Gaggiuino mod adds three components in series with the original Gaggia pump circuit, each of which can fail.

> ⚠️ **SAFETY**: Unplug from the wall before opening the case. The pump leg carries full mains voltage (120V US). The vibratory pump capacitor can retain charge briefly after power-off. Live AC measurements only with insulated probes, one hand behind back, dry surface.

### Components added by Gaggiuino (in order pump leg passes through them)

1. **SSR (Solid State Relay)** - controls the brew circuit on/off
2. **AC Dimmer / PSM module** - controls pump speed for pressure profiling
3. **Relocated pump wire** at Ulka `Pb` terminal - the spade connector Gaggiuino disturbs

### Diagnostic checks (UNPLUGGED)

- **SSR LED check** (re-plug to do this): trigger Flush, watch the SSR's status LED. If LED activates but pump stays silent, fault is downstream (dimmer, wire, or pump itself).
- **Dimmer N-joint** (well-documented defect): Bad solder joint on the N (neutral) input layer of the AC dimmer breaks zero-crossing detection, so the PSM can't fire its triac. Pump stays silent. See [GitHub Discussion #202](https://github.com/Zer0-bit/gaggiuino/discussions/202).
- **Re-seat every spade** on the pump leg, especially at the Ulka `Pb` terminal. This is a "very frequent cause" per papelespresso.
- **SSR stuck closed (dangerous variant)**: If pump ever runs when it shouldn't (on power-up before you trigger anything, or won't stop) - **UNPLUG IMMEDIATELY**. That's a stuck SSR, and continued operation will burn out the Ulka pump and damage wiring.

### Multimeter checks (UNPLUGGED)

- **Pump coil resistance**: ~200Ω across the two Ulka spade terminals. Open circuit = dead pump coil.
- **Continuity from SSR output -> dimmer input -> pump `Pb` terminal**: no breaks.

### Multimeter checks (LIVE - extreme caution)

- **AC voltage at pump terminals during Flush**: should read 120V (US) or 230V (EU)
  - No voltage at pump terminals = electronics fault upstream (SSR, dimmer, or wiring)
  - Voltage present but pump silent = dead Ulka pump

### Bench bypass test

To isolate "pump vs. electronics" definitively: temporarily wire the Ulka pump directly to mains (with appropriate isolation/fuse) and trigger it. If it runs, Gaggiuino electronics are at fault. If silent, pump is dead.

---

## Verification That It's Fixed

1. Trigger Flush with steam valve closed and no portafilter -> steady water stream from grouphead within 2 seconds
2. Pull a test "shot" with no portafilter -> ~36g water in ~10 seconds at typical pump output (~6-9 bar with no puck restriction)
3. Steam wand produces steam normally after boiler reheats
4. Pump runs quiet at idle (no hum when nothing is triggered)
5. No scorched smell

---

## Incident Log

Track each occurrence here. If airlocks recur frequently after tank refills, the intake hose may have shifted and needs investigation.

| Date | Trigger | Symptom | Resolved at Step | Notes |
|---|---|---|---|---|
| 2026-05-16 | Tank refill | Pump hums, no water on shot or Flush | Step 1 (force prime via steam wand) | First incident since Gaggiuino install |

---

## Prevention

- **Never let the tank run dry** - top off when it hits the MIN line
- **Re-seat the tank firmly** after refilling and give it a gentle wiggle to settle any bubble
- **Descale on schedule** ([Best Practices](../machine/Gaggia-Classic-Evo-Pro-Best-Practices.md) recommends every 2-3 months based on water hardness)
- **Use proper water** - Third Wave Water Espresso Profile or RPavlis recipe. Hard water scales the intake screen, soft water with no minerals can cause prime loss
- **Don't repeatedly trigger the pump dry** when troubleshooting - pulse, don't hold

---

## Safety Summary

- Steps 1-3 are exterior-only operations. **No mains-voltage exposure.**
- Step 4 requires opening the case and exposes you to **full mains voltage on the pump leg**. Unplug first. The pump capacitor can retain charge briefly.
- The Ulka EX5 has an internal thermal fuse. **Running it dry for extended periods opens the fuse permanently** - the pump cannot be repaired and must be replaced (~$30-40).
- If the pump ever runs unprompted (on power-up before you trigger anything, or won't stop when commanded off), **unplug at the wall immediately**. Likely cause is a stuck-closed SSR, and continued operation will damage the pump and wiring.

---

## Sources

### Primary

- **[papelespresso.com - Boiler Fill and Pump Issues in Gaggiuino Systems](https://www.papelespresso.com/troubleshooting-boiler-fill-and-pump-issues-in-gaggiuino-systems/)** - the single best Gaggiuino-specific pump troubleshooting page
- **[papelespresso.com - How to Properly Prime the Pump on a Gaggia Espresso Machine](https://www.papelespresso.com/how-to-properly-prime-the-pump-on-a-gaggia-espresso-machine-2/)** - the force prime procedure
- **[papelespresso.com - Troubleshooting Common Gaggia Classic Solenoid Valve Issues](https://www.papelespresso.com/troubleshooting-common-gaggia-classic-solenoid-valve-issues/)** - 3-way solenoid scaling/sticking

### Gaggiuino-Specific

- **[Gaggiuino GitHub Discussion #202](https://github.com/Zer0-bit/gaggiuino/discussions/202)** - documented AC dimmer N-joint defect
- **[Gaggiuino Stock Wiring Integration Guide](https://gaggiuino.github.io/guides-stm32/3pln-stock-wiring-integration.md)** - official wiring diagram showing SSR + dimmer placement in pump leg
- **r/gaggiuino** - search "no flow", "pump not working", "flush no water", "pump silent", "pump primed"

### Hardware Testing

- **[Whole Latte Love - Force Prime Procedure](https://www.wholelattelove.com/blogs/support-articles/4411050972179)** - vendor-blessed prime procedure
- **[Whole Latte Love - Ulka Pump Replacement](https://www.wholelattelove.com/blogs/support-articles/4411058228243)** - if pump is dead
- **[Home-Barista - How to Test Gaggia Pump and Solenoid Valve](https://www.home-barista.com/repairs/how-to-test-gaggia-pump-and-solenoid-valve-t92405.html)** - multimeter procedures for pump coil and solenoid coil

### General

- **r/espresso** - general Gaggia Classic pump discussions
- **r/gaggiaclassic** - active community for unmodded machine issues

---

## Related Notes

- [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) - Sibling note for the milder "water flows but delayed 3-10s after short idle" case (3-way solenoid back-drain or thermal contraction)
- [Gaggiuino-Modification-Overview](../machine/Gaggiuino-Modification-Overview.md) - Overview of the Gaggiuino mod, features, and components
- [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](../machine/Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) - Installation reference (Pb wire relocation, SSR + dimmer placement)
- [Gaggiuino-Post-Install-Operation-Guide](../machine/Gaggiuino-Post-Install-Operation-Guide.md) - Day-to-day operation
- [Gaggia-Classic-Evo-Pro-Best-Practices](../machine/Gaggia-Classic-Evo-Pro-Best-Practices.md) - Stock machine fundamentals, maintenance schedule

---

*Created: 2026-05-16 in response to first post-install pump airlock incident*
*Symptom: Pump hummed but no water flowed during shot or Flush, after recent tank refill*
*Resolution: Force prime via steam wand (Step 1) resolved within ~15 seconds*
