# Gaggiuino Partial Teardown: Reverse-of-Install Access to the OPV, Pump, and 3-Way Solenoid

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-07-11). Wiki links flattened; sources cited inline.

> **TL;DR**: The official Gaggiuino docs have no uninstall page - this guide is the installation sequence **run in reverse**, stopping at the shallowest level that exposes each suspect part. You do NOT need to uninstall the Gaggiuino to reach any of the three parts implicated in the no-flow/fizzing issue diagnosed in the companion note. The OPV needs only the top panel opened (Level 2); the pump and 3-way solenoid need a handful of Gaggiuino connections temporarily unplugged (Levels 3-4). Nothing here requires desoldering, re-flashing, or touching the drilled screen mount.

**Companion note**: [Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis](Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis.md) - run its Checks 1-4 BEFORE opening anything; they will tell you which level you actually need.

**Install references being reversed**: [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](../machine/Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) (Phases 8-9, 15) and the official [stock wiring integration guide](https://gaggiuino.github.io/guides-stm32/3pln-stock-wiring-integration.md).

---

## Access Levels - Go Only as Deep as the Diagnosis Requires

| Level | Exposes | Gaggiuino parts disturbed | Time (down + back up) |
|---|---|---|---|
| 0 | Tank, drip tray, intake mesh, OPV return line | None | 5 min |
| 1 | Screen/funnel assembly moved aside | Screen cable strain only | 10 min |
| 2 | **OPV** (rear right), top of boiler, hoses, wiring overview | None (visual only) | 30-45 min |
| 3 | **Ulka EX5 pump** and intake/outlet hoses | Pump-leg wiring (dimmer/PSM output, neutral pigtail) | 1-2 h |
| 4 | **3-way solenoid** (and PTB pressure tap) | Solenoid wiring (relocated Pb wire), pressure sensor line | 2-3 h |

---

## Before You Start (every level ≥ 2)

1. **UNPLUG the machine at the wall.** Not just the power switch - the Gaggiuino SSR and dimmer sit in mains wiring.
2. **Let it cool fully** (60+ min after last heat). The boiler and solenoid coil retain heat.
3. **Depressurize**: open the steam knob briefly, trigger nothing; leave the knob open.
4. **Empty the tank and drip tray.** Have towels ready - the boiler stays full and will weep from any opened fitting.
5. **Photograph everything before each disconnection.** The install checklist (Phase 8) called for install photos - have that album open side-by-side as the reassembly reference.
6. **Label with tape + marker** every wire and hose the moment it comes off (the Evo Pro's combined connector shield blocks were already separated and labeled during install - keep using those labels).
7. Capacitor caution: the Ulka pump capacitor can hold charge briefly. Wait 5 minutes; verify 0 V with a multimeter before handling pump spades.

---

## Level 0 - No Tools: Tank Bay

*Reverse of: nothing - this was never assembled.*

1. Lift off the tank lid, remove the water tank.
2. You now see: the **pump intake hose + mesh screen** (tank seat) and the **OPV return line outlet** into the tank bay.
3. This is enough for Diagnosis Checks 1 (return-line watch), 3 (intake mesh inspection), and 4 (tank level audit).

## Level 1 - Move the Funnel-Mount Screen Aside

*Reverse of: Phase 9 "Screen mounting (Funnel Mount)" - partially.*

The funnel-mount screen housing sits over the water-fill funnel area and slightly obstructs the warming plate, so it comes off before the top panel can lift.

1. Remove the **warming tray/plate** (rotates/lifts out - it was installed *after* the funnel plate, so it comes off *first*).
2. Unscrew the **screen housing from the adjustable plate** (leave the drilled adjustable/funnel plates mounted - no need to disturb the drilled holes).
3. **Do NOT unplug the screen cable yet.** Rest the screen housing on a towel next to the machine with generous cable slack. Only disconnect the custom screen-to-PCB cable (at the screen end, noting orientation) if it prevents panel removal.

## Level 2 - Top Panel Off → OPV Access

*Reverse of: Phase 8 "Remove top panel" (which still applies post-install, plus Gaggiuino cable routing).*

1. Complete Levels 0-1.
2. Remove the top panel screws (4×, same as install day - the labeled-container photo from install shows locations).
3. Lift the panel **slowly and only a few cm**: Gaggiuino added cable runs that may be zip-tied to or routed near the panel - **ToFLED water-level sensor wire, thermocouple lead, screen cable**. Cut zip ties only where necessary (bring replacements), unhook the panel, and set it aside or rest it hinged open.
4. Orient yourself against photos taken during the original install, if available. You should identify, without touching: boiler + thermocouple (replaced the brew thermostat), SSR on the rear wall, dimmer/PSM module, V4 PCB in its printed housing, PTB block with pressure sensor, 3-way solenoid on the boiler front, pump at the front-right, and the **OPV at the rear right**.

### OPV service (the most likely repair - no Gaggiuino parts touched)

1. The OPV sits on the boiler rear-right with its return line running to the tank bay.
2. Photograph, then hold the valve body with one wrench and crack the **top cap** with another (avoid twisting the valve off the boiler port).
3. Inside, in order: cap → (any shim washers you added) → **spring** → piston/pin with seal → seat.
4. Inspect: compare spring free-length to a new spring; look for debris or scale on the seat (unlikely on RO water, but a machining particle from the original install is possible); check the seal for nicks.
5. Replace spring / add 1-2 M3 washers / clean seat per the diagnosis note §4, reassemble, torque snug (brass - do not gorilla it).
6. **Recalibrate afterward**: blind-basket test targeting 12+ bar; confirm the Gaggiuino gauge reads ~12-13 bar static ([Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md)).

## Level 3 - Pump Access (Gaggiuino pump-leg wiring involved)

*Reverse of: official stock-wiring-integration "Pump Area Modifications" + Phase 9 SSR/dimmer wiring.*

Remember what the install changed at the pump (this is the part that differs from every stock-Gaggia YouTube teardown):

- The **original Gaggia pump wire (Pb)** was moved OFF the pump and now feeds the **3-way solenoid**.
- The pump's hot terminal is now fed by a **new wire from the dimmer/PSM module**.
- A **neutral pigtail** was added at the pump connector.

### Steps

1. Complete Level 2. Machine unplugged, capacitor verified discharged.
2. Photograph the pump terminals close-up.
3. Disconnect at the pump: the **dimmer-fed hot spade**, the **neutral pigtail spade**, and (if present) ground. Label each ("PUMP-HOT/dimmer", "PUMP-N").
4. Disconnect hoses: **intake hose from tank bay** (usually push-fit or spring clamp) and **outlet hose to boiler/check-valve fitting** (Oetiker pinch clamp - needs pliers; have a spare 9.5 mm clamp, they don't re-crimp well).
5. The pump sits in **rubber isolation mounts** on a bracket - flex the mounts and lift it out. No screws into the pump body itself.
6. Service/inspect: intake side for scale or a cracked hose end (prime suspect for progressive cavitation/fizzing), outlet check-valve fitting for weeping, coil resistance ~200 Ω across terminals if you suspect the pump itself.
7. If replacing: transfer the outlet fitting/check valve to the new Ulka EX5 with a new clamp; new pump drops into the same rubber mounts.

### Reassembly deltas (vs. stock guides)

Hot spade back to the **dimmer wire** (NOT the old Gaggia Pb wire - that now belongs to the solenoid), neutral pigtail back on, hoses clamped, then a **wet test before closing**: tank in, plug in, hands clear, trigger a 5s Flush and look for leaks at both pump fittings.

## Level 4 - 3-Way Solenoid Access (touches the PTB / pressure sensor)

*Reverse of: Phase 9 pressure-sensor installation (partially) + stock solenoid mounting.*

On this setup the **PTB (Pressure Tap Block)** is plumbed into the solenoid-to-group path with the pressure sensor attached - the one part of this job with no stock-Gaggia tutorial equivalent. Work from photos taken during the original install, if available.

### Steps

1. Complete Level 2 (Level 3 not required - the pump can stay in).
2. Photograph the solenoid, its hoses, the PTB, and the sensor cable routing.
3. Disconnect the **solenoid electrical connector** - note this is now fed by the **relocated original pump wire (Pb)**; label it "SOL/was-Pb".
4. Unplug or unscrew the **pressure sensor** from the PTB only if the hose routing forces it; otherwise leave the sensor + PTB attached to their hose and set the assembly aside gently. **Do not kink the sensor cable or stress the PTB fittings** - that's your pressure signal calibration at stake.
5. Mark hose orientation with a Sharpie, then remove the **two hose fittings** on the solenoid (towels down - the post-solenoid path holds ~50 ml).
6. Remove the **3 mounting bolts** holding the solenoid body to the boiler. Expect the old **boiler O-ring/gasket** to be compressed - have a new one on hand (diagnosis note §4).
7. Disassemble the valve (coil nut → coil → armature tube → plunger + rubber seat). Inspect the seat: glossy/indented/cracked rubber = replace seal kit; scale = overnight citric soak (1 tbsp / 500 ml) per [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md).
8. Reassemble with the new boiler gasket, bolts snug in a cross pattern, hoses per your Sharpie marks, "SOL/was-Pb" wire back on, PTB/sensor exactly as photographed.
9. **Wet test before closing** (as in Level 3), then confirm on-screen pressure readings look sane during a blind-basket run (validates the PTB/sensor survived the surgery).

---

## Closing Up (reverse of this guide = install Phase 15)

1. Re-zip-tie every cable run you cut, away from the boiler and heating element.
2. Top panel on (all screws), screen housing back onto the adjustable plate, screen cable seated, warming tray last.
3. Safety pass: no exposed conductors, no pinched wires under the panel, no hose contacting hot metal.
4. Functional pass: boot screen OK → temperature reads ~room temp → Flush (watch for leaks) → blind-basket pressure ~12-13 bar → one sink shot → verification criteria in the diagnosis note §5.
5. Update the Incident Log in [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) and, if the OPV was the fix, note the spring brand/date so spring lifetime is tracked.

---

## Safety Summary

- Mains voltage lives at the SSR, dimmer, switches, pump, and solenoid - **wall-unplug before every level ≥ 2**, verify with a multimeter if in doubt.
- The boiler stays full of water even with the tank out; opened fittings will weep.
- Pump capacitor: 5-minute wait + 0 V check.
- Brass fittings (OPV, boiler ports) strip easily - two wrenches, moderate torque.
- If anything smells scorched or arcs on the post-work power-up: **unplug immediately** and re-inspect (Emergency Shutdown procedure in [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](../machine/Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md)).

---

## Sources

- [Gaggiuino official docs - stock wiring integration (what the install moved: Pb wire → solenoid, dimmer → pump, thermostat jumpers, SSR)](https://gaggiuino.github.io/guides-stm32/3pln-stock-wiring-integration.md)
- [Gaggiuino official docs - machine-specific guide (Evo Pro connector insulation/labeling, OPV)](https://gaggiuino.github.io/guides/machine-specific-guide.md)
- [Whole Latte Love - Gaggia Classic Pro pump replacement (stock-machine pump steps + video)](https://www.wholelattelove.com/blogs/support-articles/4411058228243)
- Install records: [Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro](../machine/Gaggiuino-Installation-Guide-Gaggia-Classic-Evo-Pro.md) (Phases 8, 9, 15 and the install photo album)
- [Gaggiuino-Troubleshooting-Delayed-First-Flow](Gaggiuino-Troubleshooting-Delayed-First-Flow.md) Step 3 (solenoid disassembly + citric soak)

---

*Created 2026-07-11 as the access companion to [Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis](Gaggiuino-Troubleshooting-No-Flow-15-30s-Fizzing-Diagnosis.md).*
*Machine: Gaggia RI9380/49 Classic Evo Pro, Gaggiuino GEN3 V4 Premium + PTB PRO, funnel-mount screen.*
*Caveat: GEN3 V4 plug-and-play kits vary slightly from the DIY 3PLN wiring the official guide documents - where this guide and photos of the actual install disagree, trust the photos.*
