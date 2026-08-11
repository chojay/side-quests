# Gaggiuino Post-Install Operation Guide

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-01-25). Wiki links flattened; sources cited inline.

> **Setup covered**: A [Gaggiuino](Gaggiuino-Modification-Overview.md) GEN3 V4 installed on the [Gaggia Classic Evo Pro](Gaggia-Classic-Evo-Pro-Best-Practices.md) **without** load cells or ToFLED, with a Maestri House scale (no Bluetooth - manual use only). This guide covers day-to-day operation, fixing the weight prediction gap, and a progression path through profiles.

---

## 1. Fix the Weight Discrepancy (Priority \#1)

### The Problem

Gaggiuino displays ~36g extraction weight but actual yield is 25-30g - a consistent 6-11g gap.

### Why It Happens

Without load cells or a Bluetooth scale, Gaggiuino estimates output weight using **predictive flow calculation** - modeling water volume from pressure sensor data and pump power. This measures *water entering the group head*, not *water in your cup*. The "missing" grams go to:

| Where Water Goes | Approximate Loss |
|-----------------|-----------------|
| **Puck absorption** | 2-4g (grounds soak up water) |
| **3-way solenoid valve dump** | 3-5g (back-pressure water routed to drip tray when shot ends) |
| **Flow model drift** | 1-3g (prediction error varies with grind/dose/temp) |
| **Total gap** | **~6-11g** |

### Option A: Adjust Target Weight to Compensate (Free, Do Now)

A Maestri House scale has no Bluetooth, so it can't pair with Gaggiuino. But you can still use it to calibrate the prediction offset:

1. Pull 5 shots with the Maestri House on the drip tray, noting both:
   - Gaggiuino's displayed weight
   - Actual weight on the Maestri House
2. Calculate average offset (e.g., Gaggiuino shows 36g, cup has 27g → offset is 9g)
3. To get your desired yield, set the Gaggiuino target **higher** by the offset
   - Want 36g in cup? Set Gaggiuino target to ~45g (it will predict 45g, you'll get ~36g)
4. Re-verify over 3-5 shots and fine-tune

> ⚠️ This offset shifts when you change grind size, dose, or beans - re-calibrate when you switch beans.

### Option B: Buy a BLE-Compatible Scale (~$79-99)

A Bluetooth scale gives Gaggiuino real gravimetric data, eliminating the prediction gap entirely and enabling true stop-on-weight. See [Gaggiuino-Bluetooth-Scale-Recommendations](Gaggiuino-Bluetooth-Scale-Recommendations.md) for the full comparison. The cheapest compatible options:

| Scale | Price | Key Advantage |
|-------|-------|---------------|
| **DiFluid Microbalance** | ~$79 | Lowest price, Lunar-rivaling accuracy |
| **Bookoo Themis Ultra** | ~$99 | IP67 waterproof, numeric flow rate display |

**BLE setup steps** (once you have a compatible scale):

1. Turn on the BLE scale and place it on the drip tray under the portafilter spout
2. On the Gaggiuino touchscreen: **Settings → Scales → Bluetooth Scales → Enable**
3. Gaggiuino scans for BLE devices - select your scale when it appears
4. Tare the scale (with your cup on it) before each shot
5. Set your profile's stop-on-weight target (e.g., 36g for 1:2 ratio at 18g dose)

After pairing:
- Real-time weight appears on the shot graph
- Auto-stop triggers at your target yield based on **actual** cup weight
- Flow rate is calculated from real weight change, not pump estimation

> ⚠️ **Firmware updates**: Disable Bluetooth Scales (Settings → Scales) before updating Gaggiuino firmware, then re-enable after.

### Option C: Install Load Cells from the Kit

The Gaggiuino Premium + PBT PRO kit includes **DualScale load cells**. Installing them gives the most integrated solution - no external scale needed. Requires opening the machine, mounting the load cells with magnets, and running the scale calibration. See [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) for the calibration procedure.

---

## 2. Basic Gaggiuino Operation

### What Changes from Stock Gaggia

| Before (Stock) | After (Gaggiuino) |
|----------------|-------------------|
| Temperature surfing (watching ready light) | PID holds exact brew temp - set and forget |
| Fixed ~9 bar pressure | Programmable pressure curves (profiling) |
| Manual shot timing | Auto-stop by weight or time |
| Guess steam readiness | DreamSteam mode with temp display |
| No data | Real-time graphs of pressure, flow, temp |

### Daily Workflow (Gaggiuino Version)

```
□ Turn on machine (portafilter locked in)
□ Gaggiuino boots - wait for PID to reach set temp (~93°C)
  → Screen shows live boiler temp; ready when it stabilizes
  → No more temperature surfing!
□ Place Maestri House on drip tray, cup on scale, tare
□ Dose 18g, WDT, tamp (same puck prep as before)
□ Select profile on touchscreen
□ Lock portafilter, start shot
□ Watch real-time graph (pressure, flow, temp)
□ Watch Maestri House for target yield - stop manually (or let Gaggiuino predictive stop run, adjusted per offset)
□ If using BLE scale in the future: shot auto-stops at target weight
□ Steam: Switch to steam mode (DreamSteam if enabled)
```

### Warm-Up Time

With Gaggiuino's PID, the screen tells you exactly when the boiler reaches target temperature. You no longer need to guess or wait a fixed 25-30 minutes. In practice, **15-20 minutes** is usually sufficient - the PID will show a stable readout. Keep the portafilter locked in during warm-up for group head thermal stability.

### Setting Brew Temperature

Navigate: **Settings → Temperature → Brew Temperature**

| Roast Level | Suggested Brew Temp | Notes |
|-------------|-------------------|-------|
| **Light roast** | 95-96°C | Higher temp extracts harder-to-dissolve compounds |
| **Medium roast** | 93-94°C | Good starting point for most beans |
| **Dark roast** | 90-92°C | Lower temp prevents over-extraction bitterness |

Adjust in 0.5-1°C increments based on taste. One variable at a time.

---

## 3. Profile Progression Guide

Start simple and expand as you understand what each profile does to the cup.

### Phase 1: Classic 9-Bar (Week 1-2)

**Profile**: Classic 9-bar (pre-loaded)

```
Pre-infusion:  3 bar for 5-8 sec
Main extraction: 9 bar (flat)
Decline: None
Target: 18g → 36g in 25-30 sec
```

**Why start here**: This is the same extraction as a well-tuned stock Gaggia, but now with PID temperature stability. Use this to establish your Gaggiuino baseline and compare against your pre-mod shots.

**What to focus on**: Temperature dialing. Try 92°C, 93°C, and 94°C with the same beans and note which tastes best. This is where Gaggiuino's PID precision really shows - small temp changes produce noticeable flavor shifts.

---

### Phase 2: Lever Machine (Week 2-3)

**Profile**: Lever Machine (pre-loaded)

```
Pre-infusion:  ~3 bar for 5-8 sec
Peak:          9 bar
Decline:       9 → 6 → 3 bar (gradual)
Target: 18g → 36g in 28-35 sec
```

**What it does**: Mimics a traditional lever espresso machine (like a Londinium). As extraction progresses, pressure drops naturally. This reduces channeling late in the shot and produces a sweeter, more syrupy body.

**When to use**: Medium to dark roasts. Excellent for chocolate/nutty beans.

---

### Phase 3: Blooming / Filter-Style (Week 3-4)

**Profile**: Blooming (pre-loaded)

```
Pre-infusion:  2-3 bar for 10-15 sec (long bloom)
Main extraction: 6-7 bar
Target: 18g → 40-45g in 35-50 sec
```

**What it does**: Extended low-pressure pre-infusion fully saturates the puck before ramping up. Creates a more even, filter-like extraction with more clarity and less body.

**When to use**: Light roasts, single-origin coffees where you want to taste origin character. May want a slightly coarser grind than normal espresso.

---

### Phase 4: Turbo Shot (Week 4+)

**Profile**: Turbo Shot (pre-loaded or custom)

```
Pre-infusion:  Brief (2-3 sec)
Pressure:      5-6 bar (low)
Flow:          High
Grind:         Coarser than normal espresso
Target: 18g → 40-45g in 15-20 sec
```

**What it does**: Fast, high-flow extraction at lower pressure. Counterintuitive but produces a bright, juicy, tea-like espresso. Requires grinding significantly coarser (like a fine filter grind).

**When to use**: Experimental. Great for light roasts and fruit-forward coffees. Divisive - some love it, some hate it. Worth trying at least once.

---

### Phase 5: Custom Profiles (Ongoing)

Once you understand how pre-infusion time, peak pressure, and declining pressure affect taste, start creating your own or import community profiles. See [Gaggiuino-Custom-Profiles-Import-Guide](../profiles/Gaggiuino-Custom-Profiles-Import-Guide.md) for detailed instructions on importing JSON profiles from the Discord community.

**Profile Editor**: Navigate to **Profiles → Edit Profile** or **Profiles → New Profile**

**Key parameters to experiment with**:

| Parameter | Effect of Increasing | Effect of Decreasing |
|-----------|---------------------|---------------------|
| Pre-infusion pressure | More puck saturation, slower start | Less puck saturation, faster start |
| Pre-infusion time | More even extraction, longer shot | Less saturation, standard timing |
| Peak pressure | More body, more extraction | Lighter body, less extraction |
| Decline rate | More sweetness, less bitterness | Flat profile, standard extraction |

**Naming convention suggestion**: `[Bean Origin] [Roast] [Version]`
- Example: `Ethiopia Yirg Light v3`

---

## 4. DreamSteam Mode

If you make milk drinks, DreamSteam is a significant upgrade over stock steam performance.

**Enable**: **Settings → Steam → DreamSteam → On**

**What it does**: Overdrives the boiler to ~140-155°C (vs stock ~130°C), producing more aggressive steam pressure. The small Gaggia boiler normally loses power quickly; DreamSteam compensates.

**Steaming workflow with DreamSteam**:
1. Finish pulling your shot
2. Switch to steam mode on the touchscreen
3. Wait for the screen to show steam temp reached (~140°C+)
4. Purge steam wand briefly
5. Steam milk - noticeably faster and more powerful than stock
6. Wipe and purge wand immediately after

**Compared to stock steaming**: You no longer need the "steam blip" timing hack from the [stock best practices guide](Gaggia-Classic-Evo-Pro-Best-Practices.md). DreamSteam handles it automatically.

> **For a complete multi-drink workflow and advanced DreamSteam tips**, see [Gaggiuino Steaming Tips & Multi-Drink Workflow](../research-notes/Gaggiuino-Steaming-Tips-Multi-Drink-Workflow.md).

---

## 5. Gaggiuino Settings Checklist

### Essential Settings to Configure

- [ ] **Brew Temperature**: Set for your beans (see table above)
- [ ] **Bluetooth Scale**: Enable + pair BLE scale (requires a [compatible scale](Gaggiuino-Bluetooth-Scale-Recommendations.md) - the Maestri House is not BLE)
- [ ] **Stop-on-Weight**: Enable (requires BLE scale or load cells)
- [ ] **DreamSteam**: Enable if making milk drinks
- [ ] **Shot Graph Display**: Confirm pressure + flow + weight are visible during extraction

### Optional Settings

- [ ] **Web Interface**: Access Gaggiuino settings from phone/laptop on your local network
- [ ] **OTA Updates**: Check for firmware updates periodically
- [ ] **Shot History**: Review past extractions for patterns

---

## 6. Calibration Reminders

### When to Re-Calibrate

| Trigger | What to Calibrate |
|---------|------------------|
| First week of use | Temperature + Pressure |
| Changed beans significantly | Temperature (adjust brew temp) |
| Shots taste inconsistent | Pressure calibration check |
| Bluetooth scale weight drifts | Re-pair or re-calibrate BLE scale |
| After firmware update | Verify all sensor readings |
| Every 2-3 months | Full sensor check (temp, pressure) |

### Pressure Calibration Quick Check

1. Insert blind basket (backflush disc)
2. Run pump - Gaggiuino should show ~12 bar (the 12-bar OPV setting)
3. If off by >0.5 bar, run calibration: **Settings → Calibration → Pressure**

### Temperature Calibration Quick Check

1. At idle, Gaggiuino temp reading should match a kitchen thermometer held against the group head (approximately)
2. If significantly off, run calibration: **Settings → Calibration → Temperature**

---

## 7. Troubleshooting Common Issues

### Pump Hums But No Water Flows (Shot or Flush)

Most common cause is an **airlocked Ulka pump** after refilling the tank. Quick fix: open the steam wand valve fully, no portafilter, trigger Flush. Water should sputter from the steam wand within 30 seconds; once flowing, close the valve and Flush will push through the grouphead normally.

**Do not run the pump dry repeatedly** while troubleshooting. The Ulka has a thermal fuse that fails permanently if overheated dry. Pulse 5 seconds on, 10 seconds rest.

If the pump is **totally silent** instead of humming, the fault is electrical (SSR, dimmer N-joint, or relocated pump wire) - see the dedicated troubleshooting note.

**Full diagnostic flow**: [Gaggiuino-Troubleshooting-Pump-No-Flow](../troubleshooting/Gaggiuino-Troubleshooting-Pump-No-Flow.md) - sound-based decision tree, 4-step procedure, Gaggiuino-specific electrical escalation, incident log.

### BLE Scale Disconnects Mid-Shot (If Using BLE Scale in Future)

- Move scale closer to machine (reduce BLE interference)
- Ensure scale battery is >20%
- Disable other nearby Bluetooth devices if possible
- Check if Gaggiuino firmware update addresses BLE stability

### Pressure Doesn't Follow Profile

- Verify OPV is set to 12 bar (Gaggiuino needs headroom above 9 bar to profile)
- Check that the AC dimmer module is properly connected (controls pump speed)
- Ensure profile isn't set to manual mode

### Temperature Overshoots or Oscillates

- PID may need tuning: **Settings → PID Tuning**
- Gaggiuino typically auto-tunes well, but boiler characteristics vary
- Large oscillations (±5°C+) suggest thermocouple placement issue

### Shot Graph Looks Wrong

- Flat pressure line = pump not being controlled by Gaggiuino (wiring issue)
- No weight data = expected without BLE scale or load cells (Maestri House is manual only)
- Erratic flow reading = expected without BLE scale (flow is estimated from pressure)

---

## 8. What to Add Next (Future Upgrades)

### Priority Order

1. 🔴 **Accurate weight measurement** - Choose one:
   - **Buy a BLE scale** (~$79-99) - Easiest. [DiFluid Microbalance ($79)](Gaggiuino-Bluetooth-Scale-Recommendations.md) or Bookoo Themis Ultra ($99). Pairs wirelessly, no machine disassembly.
   - **Install the load cells from the kit** ($0) - Most integrated. The Premium + PBT PRO kit includes DualScale load cells and magnets. Requires opening the machine.
2. 🟡 **ToFLED sensor** - Monitors water tank level + adds RGB LED indicator. Included in the Premium kit. Install when the machine is next opened for any reason.
3. 🟢 **Rancilio Silvia steam wand** - Compatible with funnel mount. Better steam tip for latte art.

---

## Related Notes

### Gaggiuino
- [Gaggiuino-Modification-Overview](Gaggiuino-Modification-Overview.md) - Features, community, resources
- [Gaggiuino-Custom-Profiles-Import-Guide](../profiles/Gaggiuino-Custom-Profiles-Import-Guide.md) - Import/export profiles, JSON format, community sources
- [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) - Installation checklist
- [Gaggiuino-Bluetooth-Scale-Recommendations](Gaggiuino-Bluetooth-Scale-Recommendations.md) - BLE scale options and compatibility

### Espresso Workflow
- [Gaggia-Classic-Evo-Pro-Best-Practices](Gaggia-Classic-Evo-Pro-Best-Practices.md) - Machine fundamentals

---

*Created: 2026-01-25*
*Setup covered: Gaggiuino GEN3 V4 (no load cells, no ToFLED, Maestri House scale - no BLE)*
*Machine: Gaggia RI9380/49 Classic Evo Pro (Thunder Black)*
