# Gaggiuino Installation Guide - Gaggia Classic Evo Pro

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2025-12-23). Wiki links flattened; sources cited inline.

> For a general overview of what [Gaggiuino](Gaggiuino-Modification-Overview.md) is, its features, and community resources, see [Gaggiuino-Modification-Overview](Gaggiuino-Modification-Overview.md).

## Machine Information

**Machine**: Gaggia RI9380/49 Classic Evo Pro (Thunder Black)
- **Model Year**: 2023+ (EVO series)
- **Model Code**: SIN035R RI9380 or SIN035UR RI9481
- **Gaggiuino Compatibility**: ✅ **Fully Compatible** (GEN3 V4)
- **Screen Options**: Front Mount, Funnel Mount, Rear Mount

**Related Research**:
- [Gaggiuino-Post-Install-Operation-Guide](Gaggiuino-Post-Install-Operation-Guide.md) - Post-install operation, BLE scale setup, profile progression
- [Gaggia-Classic-Evo-Pro-Best-Practices](Gaggia-Classic-Evo-Pro-Best-Practices.md) - Machine operation best practices

---

## Quick Reference

**Guide Status**: Based on a completed GEN3 V4 installation on a US Evo Pro

**Reference Kit**: GEN3 V4 Complete Kit - Premium + PBT PRO (~$388)

**Typical Timeline**:
- Planning & Parts Ordering: 1-2 weeks
- Kit Shipping: 1-2 weeks
- Order remaining parts (3D prints, OPV spring, hardware): 1 week
- Installation Time: 6-10 hours (first-time install)
- Testing & Calibration: 2-4 hours

**Skill Level Required**: Advanced (electronics, Arduino, mechanical)

**Reversibility**: Moderate (some drilling required for screen mount)

---

## Screen Mount Recommendation

### 🏆 **RECOMMENDED: Funnel Mount** ⭐⭐⭐

**Why Funnel Mount is Best for This Setup:**

✅ **Advantages**:
1. **Optimal screen placement** - Eye-level viewing angle when operating machine
2. **Preserves machine aesthetics** - Clean integration with original design
3. **Adjustable angle** - Uses adjustable plate for perfect viewing
4. **No top panel cutting** - Mounts to water funnel area (non-invasive)
5. **Compatible with future mods** - Works with Rancilio Silvia wand upgrade
6. **Best for touch interaction** - Natural hand position for touchscreen

⚠️ **Trade-offs**:
- Most complex installation (requires precise alignment)
- Uses more parts than front mount
- Requires careful funnel positioning with warming plate

**User Consensus**: "Funnel mount has great screen placement and compatibility" - Most recommended by Gaggiuino community for Gaggia Classic Pro/Evo

---

### 🥈 **ALTERNATIVE: Top Front Mount** ⭐⭐

**When to Choose Front Mount:**
- You want simpler installation (fewer parts)
- You prefer compact, minimal footprint
- You're taller (funnel mount may be low for 6'2"+ users)

❌ **Limitations**:
- Fixed angle (not adjustable)
- Can be low viewing angle for taller users
- Requires cutting top panel (less reversible)

---

### 🥉 **ALTERNATIVE: Rear Mount** ⭐

**When to Choose Rear Mount:**
- You want adjustable viewing angle
- You have space behind machine
- You prefer screen away from steam/water

❌ **Limitations**:
- Takes up most counter space
- Uses most parts (most complex)
- Less convenient for touch interaction during workflow

---

## Screen Mount Specifications

### Funnel Mount - 3D Printed Parts

**Required STL Files**: [Gaggiuino Gen 3 Screen Housing by Loogle](https://www.printables.com/model/280617-gaggiuino-gaggia-classic-pro-touchscreen-housing-a)

**Print Settings**:
- **Material**: PETG (REQUIRED - PLA and ABS won't work due to heat)
- **Nozzle**: 0.4mm
- **Line Width**: 0.4mm
- **Layer Height**: 0.2mm
- **Walls**: 3 wall lines recommended
- **Parts to Print**:
  - `Mount_AdjustablePlate.stl` (for funnel configuration)
  - `Screen_Housing_Funnel.stl`
  - `Funnel_Plate.stl`

**Installation Notes**:
- First put water filling funnel in position
- Then rotate warming plate into place (screen mount slightly obstructs warming plate)
- Adjustable plate allows fine-tuning viewing angle after installation

**Alternative Sources**:
- [MakerWorld - Gaggiuino Gen 3 Screen Housing](https://makerworld.com/en/models/660083-gaggiuino-gen-3-screen-housing)
- [3D Printing Service via Espressio](https://gaggiuino.espressio.nl/) - Official Gaggiuino supplier

---

## Pre-Installation Checklist

### ☑️ **Phase 1: Verify Machine Compatibility**

- [ ] **Confirm machine model**: Gaggia RI9380/49 Classic Evo Pro ✅
- [ ] **Check model year**: 2023+ EVO series ✅
- [ ] **Verify 3-way solenoid valve**: All Classic Pro/Evo have this ✅
- [ ] **Check boiler type**: Single boiler (brass) ✅
- [ ] **Confirm voltage**: 120V (US) or 230V (EU) - verify your model

**Compatibility**: ✅ The Gaggia RI9380/49 Classic Evo Pro is FULLY COMPATIBLE

---

### ☑️ **Phase 2: Choose Gaggiuino Kit & Supplier**

**RECOMMENDED KIT**: GEN3 V4 Complete Kit or PTB Kit (4.3" touchscreen, latest features)

#### **Option A: Peak Coffee (Hong Kong) - RECOMMENDED** ⭐⭐⭐

**Product**: [Gaggiuino GEN3 V4 Complete Kit](https://www.peakcoffee.cc/product/gaggiuino-v4-complete-kit/) OR [PTB Kit](https://www.peakcoffee.cc/product/gaggiuino-v4-kit/)

**Price**: $340-388

**Note**: Both kits include PTB (Pressure Tap Block) - CNC stainless steel 3-way connection for stable pressure readings. Complete Kit includes expedited shipping; PTB Kit has standard shipping (Thursday dispatch). Choose based on shipping preference.

**What's Included**:
- ✅ V4 PCB (U585 microcontroller)
- ✅ 4.3" IoT touchscreen
- ✅ **PTB (Pressure Tap Block)** - CNC stainless steel 3-way connection ⭐
- ✅ ToFLED (water level + RGB LED)
- ✅ DualScale soldered load cells
- ✅ Low voltage wiring kit (plug-and-play connectors)
- ✅ High voltage connection cables
- ✅ Pressure sensor (food-grade, connects to PTB)
- ✅ Thermocouple K (temperature sensor)
- ✅ Ceramic resettable thermofuse
- ✅ Custom screen-to-PCB cable
- ✅ SSR (solid state relay)

**Shipping**: Dispatches every Thursday, expedited shipping included

**Best For**: Latest features, complete kit, fastest shipping

- [ ] **Order GEN3 V4 kit** - $340-388 (the Premium + PBT PRO variant, ~$388, is the reference kit for this guide)

---

#### **Option B: DIY-EFI (UK) - High Quality** ⭐⭐⭐

**Product**: [Gaggiuino V4 PCB Kit for Gaggia Classic Pro](https://diy-efi.co.uk/product/gaggiuino-pro-kit-v4-gen3)

**Price**: £150-200 (~$190-255)

**What's Included**: Same as Peak Coffee (V4 PCB, 4.3" screen, all electronics)

**Shipping**: UK-based, faster for EU buyers

**Best For**: UK/EU location, budget-conscious, proven quality ("MUCH better quality" user reviews)

- [ ] **Alternative: Order from DIY-EFI** - £150-200

---

#### **Option C: Peak Coffee GEN2 - Budget Option** ⭐⭐

**Product**: [Gaggiuino GEN2 Kit Set (Gaggia Classic Pro)](https://www.peakcoffee.cc/product/gaggiuino-v3-kit-set-gaggia-classic-pro/)

**Price**: $278

**What's Included**: Previous generation (all core features, 2.4" screen)

**Trade-offs**:
- ❌ Smaller screen (2.4" vs 4.3")
- ❌ Older microcontroller (fewer future features)
- ✅ All core functionality (pressure profiling, flow control, PID)
- ✅ Proven platform (more community support)

**Best For**: Budget-conscious, all features sufficient, smaller screen acceptable

- [ ] **Budget alternative: GEN2 kit** - $278

---

### ☑️ **Phase 3: NOT Included - Order Separately**

#### **3D Printed Parts** (REQUIRED)

**Official Supplier**: [Espressio - Gaggiuino 3D Parts](https://gaggiuino.espressio.nl/)
- Sold with permission of Gaggiuino team
- PETG material (heat-resistant)
- All mounting hardware designs

**DIY Option**: Download STL files and print yourself
- [Printables - Gaggiuino Gen 3 Screen Housing](https://www.printables.com/model/356026-gaggiuino-gen-3-screen-housing)
- [Printables - Funnel Mount Housing](https://www.printables.com/model/280617-gaggiuino-gaggia-classic-pro-touchscreen-housing-a)
- Requires PETG filament printer or 3D printing service

- [ ] **Order 3D printed parts from Espressio** OR
- [ ] **Download STL files and arrange printing** (requires PETG)

**Estimated Cost**: $30-60 (Espressio) or $15-30 (DIY printing)

---

#### **Hardware & Fasteners** (REQUIRED)

**NOT included in kits - purchase separately**:

- [ ] **Magnets for load cells** (if using scale integration)
  - Size: 6mm x 3mm neodymium magnets (qty: 8)
  - Source: Amazon, hardware store
  - Cost: $5-10

- [ ] **M3/M4 screws assortment**
  - Lengths: 6mm, 8mm, 10mm, 12mm, 16mm
  - Material: Stainless steel
  - Qty: 20-30 assorted
  - Source: Amazon, hardware store
  - Cost: $10-15

- [ ] **Heat shrink tubing assortment**
  - Sizes: 2mm, 3mm, 5mm, 8mm
  - Source: Amazon, electronics supplier
  - Cost: $8-12

- [ ] **High voltage wire** (if kit doesn't include enough)
  - 18 AWG silicone wire (red/black)
  - High temperature rated (200°C+)
  - Length: 2-3 meters
  - Cost: $10-15

**Total Hardware Cost**: $33-52

---

#### **OPV Spring Upgrade** (REQUIRED for Evo Pro)

**IMPORTANT**: 2023 EVO Gaggia Classic Pro requires 12-bar OPV spring for Gaggiuino (higher than standard 9-bar mod). See [Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md) for detailed community research on why 10-12 bar is required.

- [ ] **12-Bar OPV Spring Modification Kit**
  - [Amazon - 12 Bar OPV Spring for Gaggia Classic EVO Pro/Gaggiuino](https://www.amazon.com/Bar-Spring-Modification-Espresso-Machines/dp/B0CZGMW7VB)
  - **Price**: $15-20
  - **Why needed**: Gaggiuino requires increased pressure range for profiling (stock 9 bar OPV cracks open at ~8.2 bar, interfering with Gaggiuino's pressure control)
  - **Note**: This is DIFFERENT from standard 9-bar OPV mod (don't buy 9-bar spring)

**Alternative**: DIY washer trick - add 3-4 M3 stainless washers behind existing 9 bar spring (see [Gaggiuino-OPV-Spring-Research-Community-Findings](../research-notes/Gaggiuino-OPV-Spring-Research-Community-Findings.md))

---

### ☑️ **Phase 4: Tools & Equipment Required**

#### **Electronics Tools** (REQUIRED)

- [ ] **Soldering iron** (adjustable temperature, 60W+)
  - For: Wire connections, heat shrink
  - Cost: $25-50 (if don't own)

- [ ] **Solder** (60/40 or 63/37 rosin core)
  - Cost: $8-12

- [ ] **Digital multimeter**
  - For: Voltage testing, continuity checks, troubleshooting
  - Cost: $15-30 (if don't own)

- [ ] **Wire strippers** (18-24 AWG)
  - Cost: $10-15

- [ ] **Heat gun or lighter** (for heat shrink tubing)
  - Cost: $15-25 (heat gun) or $2 (lighter)

- [ ] **Helping hands** or PCB holder
  - For: Soldering small components
  - Cost: $10-20 (optional but helpful)

**Electronics Tools Total**: $83-152 (if buying all new)

---

#### **Mechanical Tools** (REQUIRED)

- [ ] **Hex key set** (metric, 2mm-6mm)
  - For: Gaggia disassembly
  - Cost: $10-15 (if don't own)

- [ ] **Phillips screwdrivers** (\#1, \#2)
  - Cost: $8-12

- [ ] **Flathead screwdrivers** (small, medium)
  - Cost: $8-12

- [ ] **Drill + drill bits** (2mm, 3mm, 5mm, 8mm)
  - For: Screen mount installation (funnel mount requires drilling)
  - Cost: $40-80 (if don't own drill)

- [ ] **Step drill bit** or **tapered reamer** (optional, for clean holes)
  - Cost: $15-25

- [ ] **Needle-nose pliers**
  - Cost: $8-12

- [ ] **Zip ties** (assorted sizes)
  - For: Cable management
  - Cost: $5-8

**Mechanical Tools Total**: $94-164 (if buying all new)

---

#### **Testing & Calibration Tools** (RECOMMENDED)

- [ ] **Portafilter pressure gauge** (58mm)
  - For: OPV adjustment verification
  - Cost: $15-25

- [ ] **Infrared thermometer** (optional, for initial testing)
  - Cost: $15-25

- [ ] **Shot timer** (or use Gaggiuino built-in timer after install)

**Testing Tools Total**: $15-50

---

### ☑️ **Phase 5: Knowledge & Skills Preparation**

#### **Required Knowledge** (complete BEFORE starting)

- [ ] **Read official Gaggiuino documentation**
  - [Gaggiuino Official Docs](https://gaggiuino.github.io/)
  - [GaggiMate Installation Guide (alternative)](https://docs.gaggimate.eu/docs/installation-gcp/)

- [ ] **Watch installation videos** (search YouTube: "Gaggiuino installation Gaggia Classic Pro")
  - Recommended: 2-3 full installation walkthroughs

- [ ] **Join Gaggiuino community** (for troubleshooting support)
  - [GitHub Discussions](https://github.com/Zer0-bit/gaggiuino/discussions)
  - [Coffee Forums UK - Gaggiuino Thread](https://www.coffeeforums.co.uk/threads/gaggiuino.72426/)
  - Reddit: r/gaggiuino, r/espresso

- [ ] **Understand basic Arduino/microcontroller concepts**
  - If unfamiliar: Complete Arduino basics tutorial (1-2 hours)

- [ ] **Review electrical safety** for 120V/230V AC work
  - **CRITICAL**: Unplug machine before any wiring work
  - Understand live/neutral/ground wire identification
  - Know how to use multimeter for voltage testing

---

#### **Skills Assessment** (be honest)

Rate yourself (1=novice, 5=expert):

**Electronics Skills**:
- [ ] Soldering small wires and connectors: ___/5
- [ ] Reading wiring diagrams: ___/5
- [ ] Using multimeter: ___/5
- [ ] Arduino/microcontroller programming: ___/5

**Mechanical Skills**:
- [ ] Disassembling appliances: ___/5
- [ ] Drilling precise holes: ___/5
- [ ] Cable routing and management: ___/5

**Recommended Minimum**:
- Electronics: 3/5 (or willing to learn)
- Mechanical: 3/5 (or willing to learn)
- **If below 3/5**: Consider practicing on spare electronics before Gaggiuino install

---

### ☑️ **Phase 6: Pre-Installation Espresso Setup**

**COMPLETE BEFORE GAGGIUINO INSTALL** (establishes baseline):

- [ ] **Complete basic accessory setup**
  - Scale (Timemore Nano or Felicita Arc)
  - WDT tool (JKIM or equivalent)
  - Calibrated tamper (Normcore V4)
  - Dosing funnel
  - Precision basket (IMS Baristapro 18g)

- [ ] **Perform standard 9-bar OPV mod FIRST** (before Gaggiuino)
  - **WAIT**: For Evo Pro, you need 12-bar spring (see Phase 3)
  - Install 12-bar spring, verify with pressure gauge
  - Test baseline shots at 12-bar (Gaggiuino will profile down to 9-bar during extraction)

- [ ] **Establish baseline espresso quality**
  - Pull 10-20 shots, document results
  - Dial in your beans: 18g → 36g in 25-30 seconds
  - Taste and photograph shots (for before/after comparison)

- [ ] **Set up water quality system**
  - Third Wave Water or RPavlis recipe
  - TDS meter verification (75-150 ppm)
  - Backflush with Cafiza (clean machine before install)

**Why do this first?**
- Establishes baseline for Gaggiuino comparison
- Ensures grinder (DF64) is dialed in properly
- Verifies machine is functioning correctly before mod
- Gives you espresso during Gaggiuino installation (if it takes multiple days)

---

## Installation Phase Checklist

### 📦 **Phase 7: Parts Arrival & Verification**

- [ ] **Gaggiuino kit in hand** (reference kit: GEN3 V4 Premium + PBT PRO, ~$388 list)
- [ ] **Verify kit contents** against supplier packing list:
  - [ ] PCB board (check for damage)
  - [ ] Touchscreen (test power-on if possible)
  - [ ] Pressure sensor
  - [ ] Thermocouple
  - [ ] SSR relay
  - [ ] Load cells (if DualScale kit)
  - [ ] Wiring harnesses
  - [ ] Thermofuse
  - [ ] All small components (check count)

- [ ] **3D printed parts received** or **printed successfully**:
  - [ ] Screen housing (funnel mount version)
  - [ ] Adjustable plate
  - [ ] Funnel plate
  - [ ] Component housing (for PCB, SSR)
  - [ ] Cable clips/organizers

- [ ] **Hardware received**:
  - [ ] Magnets (if using scales)
  - [ ] Screws (M3/M4 assortment)
  - [ ] Heat shrink tubing
  - [ ] High voltage wire (if needed)

- [ ] **12-bar OPV spring received**

- [ ] **All tools acquired and tested**:
  - [ ] Soldering iron heats up, temperature control works
  - [ ] Multimeter battery fresh, tests voltage correctly
  - [ ] Drill bits fit drill chuck, test on scrap wood
  - [ ] Wire strippers adjusted for 18-22 AWG

---

### 🔧 **Phase 8: Machine Disassembly & Preparation**

**SAFETY FIRST**: ⚠️ **UNPLUG MACHINE** before starting any work

- [ ] **Workspace setup**:
  - [ ] Clear, well-lit workspace (6+ sq ft)
  - [ ] Anti-static mat or clean towel
  - [ ] Parts organizer (egg carton, small bowls, magnetic tray)
  - [ ] Label tape and marker (for wire identification)
  - [ ] Phone/camera for documentation photos

- [ ] **Document original state** (CRITICAL for reversibility):
  - [ ] Photo: Front of machine (before disassembly)
  - [ ] Photo: Rear of machine
  - [ ] Photo: Top (with panels)
  - [ ] Video: Walk around machine (360°)

- [ ] **Remove top panel**:
  - [ ] Remove warming tray
  - [ ] Remove water reservoir
  - [ ] Locate top panel screws (typically 4 screws, check manual)
  - [ ] Photo: Top panel screw locations
  - [ ] Remove screws, keep in labeled container
  - [ ] Lift top panel carefully (may have wire connections)
  - [ ] Photo: Interior before any modifications

- [ ] **Access boiler area**:
  - [ ] Photo: Boiler, thermostat, wiring (original state)
  - [ ] Identify thermostat location (will be replaced by thermocouple)
  - [ ] Identify pressure stat location
  - [ ] Locate SSR relay mounting location

- [ ] **Discharge capacitors** (SAFETY):
  - [ ] Wait 5 minutes after unplugging
  - [ ] Use multimeter to verify 0V across capacitor terminals
  - [ ] Use insulated screwdriver to short capacitor terminals (if voltage present)

---

### ⚡ **Phase 9: Electrical Installation**

**⚠️ HIGH VOLTAGE WARNING**: Some steps involve 120V/230V AC. Follow safety protocols.

#### **Thermocouple Installation** (Temperature Sensor)

- [ ] **Locate original thermostat**:
  - [ ] Photo: Thermostat location and wiring
  - [ ] Label wires (use tape, mark "STAT-1", "STAT-2")
  - [ ] Disconnect thermostat wires

- [ ] **Install thermocouple K**:
  - [ ] Route thermocouple to boiler (kit includes mounting)
  - [ ] Photo: Thermocouple placement
  - [ ] Secure with thermal paste or spring clip
  - [ ] Route wires to PCB location (avoid sharp edges, heat sources)
  - [ ] Use zip ties for cable management

- [ ] **Test thermocouple** (before finalizing):
  - [ ] Connect to multimeter (mV mode)
  - [ ] Apply gentle heat (heat gun, low setting)
  - [ ] Verify voltage change (should increase with temperature)

---

#### **Pressure Sensor Installation**

- [ ] **Locate pressure tap point**:
  - [ ] Gaggia Classic Pro: Near grouphead output
  - [ ] Photo: Tap point location

- [ ] **Install pressure sensor**:
  - [ ] Connect pressure sensor to water line (kit includes fittings)
  - [ ] Photo: Pressure sensor mounted
  - [ ] Ensure food-grade seal (no leaks)
  - [ ] Route sensor wires to PCB location

- [ ] **Test pressure sensor** (before finalizing):
  - [ ] Connect to multimeter (voltage mode)
  - [ ] Manually pressurize (if possible) or test after reassembly
  - [ ] Verify voltage increases with pressure

---

#### **SSR (Solid State Relay) Installation**

- [ ] **Locate original brew relay/switch**:
  - [ ] Photo: Original wiring configuration
  - [ ] Label all wires (AC in, AC out, ground)

- [ ] **Mount SSR**:
  - [ ] Choose mounting location (3D printed housing or machine panel)
  - [ ] Drill mounting holes (if needed)
  - [ ] Secure SSR with screws
  - [ ] Photo: SSR mounted

- [ ] **Wire SSR** (HIGH VOLTAGE):
  - [ ] **VERIFY MACHINE UNPLUGGED**
  - [ ] Connect AC input to SSR (from power switch)
  - [ ] Connect AC output from SSR (to heating element)
  - [ ] Connect control signal from PCB (low voltage side)
  - [ ] Photo: SSR wiring completed
  - [ ] Use heat shrink tubing on all connections
  - [ ] Verify no exposed wire (safety check)

---

#### **PCB & Screen Installation**

- [ ] **Choose PCB mounting location**:
  - [ ] Inside machine (3D printed housing) OR
  - [ ] External (side panel mount)
  - [ ] Photo: Planned PCB location

- [ ] **Mount PCB**:
  - [ ] Install 3D printed component housing (if using)
  - [ ] Secure PCB with screws/standoffs
  - [ ] Ensure ventilation (PCB generates heat)
  - [ ] Photo: PCB mounted

- [ ] **Connect all sensors to PCB**:
  - [ ] Thermocouple → PCB thermocouple input (check polarity)
  - [ ] Pressure sensor → PCB pressure input
  - [ ] SSR control signal → PCB SSR output
  - [ ] Load cells → PCB (if using scale integration)
  - [ ] Power supply → PCB (verify voltage: 5V or 12V per kit specs)
  - [ ] Photo: All PCB connections

- [ ] **Screen mounting** (Funnel Mount):
  - [ ] Position funnel plate on machine
  - [ ] Mark drill holes for funnel mount
  - [ ] **Double-check measurements** (irreversible step)
  - [ ] Drill pilot holes (2mm), then final size (3mm or per STL specs)
  - [ ] Photo: Drilled holes
  - [ ] Mount adjustable plate with screws
  - [ ] Attach screen housing to adjustable plate
  - [ ] Route screen cable to PCB (use provided custom cable)
  - [ ] Connect screen to PCB
  - [ ] Photo: Screen mounted, wiring complete

---

#### **12-Bar OPV Spring Installation** (Evo Pro Specific)

- [ ] **Locate OPV valve**:
  - [ ] Gaggia Classic Evo Pro: Rear right side of machine
  - [ ] Photo: OPV valve location

- [ ] **Remove original OPV spring**:
  - [ ] Unscrew OPV valve body (check manual for tool)
  - [ ] Remove stock spring
  - [ ] Photo: Original spring (for reference)

- [ ] **Install 12-bar spring**:
  - [ ] Insert new 12-bar spring
  - [ ] Reassemble OPV valve
  - [ ] Photo: New spring installed

- [ ] **Set OPV to 12-bar** (Gaggiuino requirement):
  - [ ] Install portafilter pressure gauge
  - [ ] Power on machine (for testing only, disconnect Gaggiuino control first)
  - [ ] Run pump, check static pressure
  - [ ] Adjust OPV screw until gauge reads **12 bar static** (= ~11 bar dynamic)
  - [ ] Photo: Pressure gauge showing 12 bar

**Why 12-bar?** Gaggiuino profiles shots dynamically (e.g., 3 bar → 9 bar → 6 bar decline). Higher OPV ceiling allows pressure profiling flexibility.

---

### 🔌 **Phase 10: Power-Up & Initial Testing**

**⚠️ SAFETY CHECK BEFORE POWER-UP**:

- [ ] **Visual inspection**:
  - [ ] All wire connections secure (no exposed wire)
  - [ ] No wires touching hot surfaces (boiler, heating element)
  - [ ] Heat shrink tubing applied to all solder joints
  - [ ] Pressure sensor connections leak-free
  - [ ] Screen cable not pinched or kinked

- [ ] **Resistance checks** (machine UNPLUGGED):
  - [ ] Multimeter: Check resistance between AC hot and ground (should be >1MΩ)
  - [ ] Check resistance between PCB power and ground (should match specs)

- [ ] **First power-up** (LOW VOLTAGE ONLY):
  - [ ] Connect ONLY PCB power supply (5V/12V DC, NOT AC mains)
  - [ ] Power on PCB
  - [ ] Screen should display Gaggiuino boot screen
  - [ ] Check for smoke, unusual smells (if present, POWER OFF immediately)
  - [ ] Photo: Gaggiuino boot screen

- [ ] **Sensor verification** (PCB powered, machine still unplugged):
  - [ ] Navigate Gaggiuino menu: Check thermocouple reading (should be ~room temp, 20-25°C)
  - [ ] Check pressure sensor reading (should be 0 bar, no pressure)
  - [ ] Test screen touch response (all zones responsive)

---

### ⚙️ **Phase 11: Full System Integration & Testing**

- [ ] **Reassemble machine** (partial, for testing):
  - [ ] Reconnect all original wiring (if temporarily disconnected)
  - [ ] **DOUBLE-CHECK**: All AC wiring correct (hot, neutral, ground)
  - [ ] Replace top panel (loose fit, for easy access if troubleshooting needed)
  - [ ] Reinstall water reservoir
  - [ ] **DO NOT** reinstall warming tray yet (in case need access)

- [ ] **Fill water reservoir**:
  - [ ] Use distilled water + Third Wave Water
  - [ ] Check for leaks around pressure sensor

- [ ] **First AC power-up** (MACHINE + PCB):
  - [ ] **VERIFY**: Machine unplugged
  - [ ] **VERIFY**: All safety checks complete
  - [ ] Plug in machine AC power
  - [ ] Power on machine
  - [ ] Gaggiuino screen should boot fully
  - [ ] Check for error messages on screen

- [ ] **Sensor calibration**:
  - [ ] **Temperature calibration**:
    - [ ] Navigate: Gaggiuino menu → Calibration → Temperature
    - [ ] Follow on-screen instructions (typically: heat to 100°C, verify boiling point)
    - [ ] Record calibration values

  - [ ] **Pressure calibration**:
    - [ ] Navigate: Gaggiuino menu → Calibration → Pressure
    - [ ] Run pump with blind basket (no water flow)
    - [ ] Verify pressure reading matches portafilter gauge (should read ~12 bar)
    - [ ] Adjust calibration if needed (per Gaggiuino manual)

  - [ ] **Scale calibration** (if using load cells):
    - [ ] Navigate: Gaggiuino menu → Calibration → Scale
    - [ ] Place known weight (e.g., 100g, 200g)
    - [ ] Follow calibration procedure

---

### ☕ **Phase 12: First Shot & Dialing In**

- [ ] **Initial flush**:
  - [ ] Run 3-5 blank shots (no coffee, just water)
  - [ ] Verify temperature stability (Gaggiuino displays real-time temp)
  - [ ] Check for leaks (all fittings, pressure sensor)

- [ ] **Load default profile**:
  - [ ] Navigate: Gaggiuino menu → Profiles → Load Profile
  - [ ] Select: "Classic 9-bar" or "Beginner Profile"
  - [ ] Review profile curve (should show 3-bar pre-infusion → 9-bar extraction)

- [ ] **First espresso shot**:
  - [ ] Dose 18g (same as pre-Gaggiuino baseline)
  - [ ] WDT, tamp, insert portafilter
  - [ ] Start shot, observe Gaggiuino screen:
    - [ ] Temperature holds steady (±1°C)
    - [ ] Pressure follows profile (3 bar → 9 bar)
    - [ ] Flow rate displays (if enabled)
    - [ ] Shot timer counts up
  - [ ] Stop at 36g yield (or per profile auto-stop)
  - [ ] Photo: First Gaggiuino shot in cup
  - [ ] Photo: Gaggiuino screen showing shot graph

- [ ] **Taste comparison**:
  - [ ] Pull 2-3 shots with same beans/dose as pre-Gaggiuino baseline
  - [ ] Compare flavor, body, crema
  - [ ] Document tasting notes

---

### 🎨 **Phase 13: Profile Experimentation**

- [ ] **Learn profile editor**:
  - [ ] Navigate: Gaggiuino menu → Profiles → Edit Profile
  - [ ] Understand parameters:
    - [ ] Pre-infusion pressure (bar)
    - [ ] Pre-infusion time (seconds)
    - [ ] Ramp rate (bar/second)
    - [ ] Peak pressure (bar)
    - [ ] Decline profile (flat, declining, etc.)

- [ ] **Try pre-built profiles**:
  - [ ] "Blooming Profile" (6ml/sec → 2ml/sec → 4ml/sec flow)
  - [ ] "Lever Machine" (9 bar → 6 bar → 3 bar decline)
  - [ ] "Turbo Shot" (high flow, 6-bar max, 15-20 second shots)

- [ ] **Create custom profile**:
  - [ ] Based on your beans (light roast, medium, dark)
  - [ ] Document profile settings
  - [ ] Save with descriptive name (e.g., "Ethiopia Light Roast")

---

### 🧪 **Phase 14: Advanced Features Testing**

- [ ] **DreamSteam mode** (if GEN3 V4):
  - [ ] Navigate: Gaggiuino menu → Steam → DreamSteam Enable
  - [ ] Test steam power (should steam 8oz milk in <30 seconds)
  - [ ] Monitor boiler temp (should overdrive to 140°C+)
  - [ ] Verify safety shutoff (temp limits working)

- [ ] **Scale integration** (if installed load cells):
  - [ ] Enable auto-stop at target yield (e.g., 36g)
  - [ ] Test accuracy (±0.5g tolerance)
  - [ ] Verify real-time weight graphing

- [ ] **Shot data logging**:
  - [ ] Navigate: Gaggiuino menu → History → View Shots
  - [ ] Review pressure/temperature/flow graphs
  - [ ] Export data (if feature available, check manual)

---

### 🏁 **Phase 15: Final Assembly & Cleanup**

- [ ] **Cable management**:
  - [ ] Route all wires away from heat sources
  - [ ] Use zip ties to secure bundles
  - [ ] Ensure no pinch points or sharp edges
  - [ ] Photo: Clean cable routing

- [ ] **Final reassembly**:
  - [ ] Reinstall warming tray
  - [ ] Reinstall top panel (all screws tight)
  - [ ] Reinstall water reservoir
  - [ ] Check all external panels secure

- [ ] **Final safety check**:
  - [ ] No exposed wires visible
  - [ ] All panels secure
  - [ ] Pressure sensor connections leak-free
  - [ ] Screen mount stable (no wobble)

- [ ] **Documentation**:
  - [ ] Organize all installation photos into album
  - [ ] Save Gaggiuino calibration values (screenshot or write down)
  - [ ] Create "Gaggiuino Quick Reference" note (key profiles, calibration dates)
  - [ ] Update this checklist with lessons learned

- [ ] **Celebration shot**:
  - [ ] Pull your best shot with custom profile
  - [ ] Photo: Final espresso shot
  - [ ] Photo: Gaggiuino screen showing completed installation

---

## Post-Installation Maintenance

### Daily

- [ ] Check Gaggiuino screen for error messages
- [ ] Verify pressure/temperature readings normal
- [ ] Backflush with water (30 seconds, no Cafiza)

### Weekly

- [ ] Review shot history data (identify trends)
- [ ] Clean portafilter, baskets, screen
- [ ] Chemical backflush with Cafiza

### Monthly

- [ ] Verify sensor calibration (temperature, pressure)
- [ ] Update Gaggiuino firmware (check GitHub releases)
- [ ] Deep clean machine (descale if needed, based on TDS readings)

### Every 3-6 Months

- [ ] Re-calibrate all sensors
- [ ] Check for loose wires or connections
- [ ] Inspect 3D printed parts (PETG degradation from heat)
- [ ] Update custom profiles based on new beans

---

## Troubleshooting Guide

### Screen Issues

**Problem**: Screen won't turn on
- [ ] Check PCB power supply (5V/12V, verify with multimeter)
- [ ] Check screen cable connection (reseat connector)
- [ ] Verify screen not damaged (test with multimeter: backlight should have continuity)

**Problem**: Touch not responsive
- [ ] Recalibrate touchscreen (Gaggiuino menu → Settings → Screen Calibration)
- [ ] Check for moisture on screen (dry thoroughly)

---

### Temperature Issues

**Problem**: Temperature reading incorrect (e.g., shows 200°C at room temp)
- [ ] Check thermocouple polarity (+ and - reversed?)
- [ ] Verify thermocouple type (should be K-type)
- [ ] Re-run temperature calibration

**Problem**: Temperature unstable (±5°C swings)
- [ ] Check thermocouple placement (should be tight against boiler)
- [ ] Verify SSR working correctly (use multimeter to test switching)
- [ ] Check PID tuning (Gaggiuino menu → Settings → PID Tuning)

---

### Pressure Issues

**Problem**: Pressure reading 0 bar during shot
- [ ] Check pressure sensor wiring (verify voltage changes with pressure)
- [ ] Check for leaks (pressure sensor fitting loose?)
- [ ] Re-run pressure calibration

**Problem**: Pressure doesn't follow profile (e.g., stuck at 12 bar)
- [ ] Verify OPV set to 12 bar (not 9 bar)
- [ ] Check SSR controlling pump correctly (test relay switching)
- [ ] Check profile settings (may be set to manual mode)

---

### Pump/Flow Issues

**Problem**: Pump won't start
- [ ] Check Gaggiuino controlling pump (manual override test)
- [ ] Verify wiring to pump relay (AC connections secure?)
- [ ] Check for error messages on screen

**Problem**: Flow rate too fast/slow
- [ ] Verify OPV at 12 bar (affects max flow)
- [ ] Check grind size (too coarse = fast flow, too fine = slow)
- [ ] Review profile flow settings

---

### Software Issues

**Problem**: Gaggiuino firmware not responding
- [ ] Restart PCB (power cycle)
- [ ] Re-flash firmware (via USB, see Gaggiuino GitHub)
- [ ] Check for corrupted SD card (if applicable)

**Problem**: Profiles not saving
- [ ] Check available memory (delete old profiles if full)
- [ ] Verify SD card working (if using external storage)

---

### Emergency Shutdown

**If you smell smoke, see sparks, or suspect electrical fault**:

1. [ ] **UNPLUG MACHINE IMMEDIATELY** (pull plug, don't use switch)
2. [ ] **Let cool** (10 minutes minimum)
3. [ ] **Inspect all wiring** (look for melted insulation, burn marks)
4. [ ] **Test with multimeter** (check for shorts between hot/ground)
5. [ ] **Do NOT power on** until fault identified and resolved
6. [ ] **Ask for help**: Post photos to Gaggiuino community (GitHub Discussions, Coffee Forums)

---

## Cost Summary

### Kit & Parts

| Item | Price Range | Chosen Option |
|------|-------------|---------------|
| Gaggiuino GEN3 V4 Kit | $340-388 | Peak Coffee: $____ |
| 3D Printed Parts | $30-60 | Espressio / DIY: $____ |
| 12-Bar OPV Spring | $15-20 | Amazon: $____ |
| Hardware (magnets, screws) | $33-52 | Amazon: $____ |
| **Subtotal** | **$418-520** | **$____** |

### Tools (if buying new)

| Category | Price Range | Have? |
|----------|-------------|-------|
| Electronics Tools | $83-152 | ☐ Yes / ☐ Buy |
| Mechanical Tools | $94-164 | ☐ Yes / ☐ Buy |
| Testing Tools | $15-50 | ☐ Yes / ☐ Buy |
| **Tools Subtotal** | **$192-366** | **$____** |

### **Grand Total**

- **Kit & Parts Only**: $418-520
- **Kit + Tools (if buying all)**: $610-886

**Estimated Total**: $________

---

## Timeline Estimate

| Phase | Duration | Target Dates |
|-------|----------|--------------|
| Planning & Research | 1-2 weeks | ____ to ____ |
| Parts Ordering | 1-2 weeks (shipping) | Order: ____ / Arrive: ____ |
| Pre-Installation Prep | 1-2 days | ____ |
| Installation Day 1 (Disassembly + Electronics) | 4-6 hours | ____ |
| Installation Day 2 (Testing + Calibration) | 2-4 hours | ____ |
| Dialing In & Profile Tuning | 1-2 weeks | ____ to ____ |

**Target Completion Date**: ____________

---

## Resources & References

### Official Documentation
- [Gaggiuino Official Docs](https://gaggiuino.github.io/) - Complete installation guide, firmware updates
- [Gaggiuino GitHub Repository](https://github.com/Zer0-bit/gaggiuino) - Source code, troubleshooting discussions
- [GaggiMate Installation Guide](https://docs.gaggimate.eu/docs/installation-gcp/) - Alternative installation guide (similar platform)

### Community Support
- [Coffee Forums UK - Gaggiuino Thread](https://www.coffeeforums.co.uk/threads/gaggiuino.72426/) - UK-based community, active troubleshooting
- [Reddit r/gaggiuino](https://www.reddit.com/r/gaggiuino/) - (if exists, check)
- [Reddit r/espresso - Gaggiuino posts](https://www.reddit.com/r/espresso/) - Search "Gaggiuino" for builds and tips
- [GitHub Discussions - Parts List](https://github.com/Zer0-bit/gaggiuino/discussions/316) - BOM discussion thread

### Suppliers
- [Peak Coffee - Gaggiuino Kits](https://www.peakcoffee.cc/product/gaggiuino-v4-complete-kit/) - Hong Kong, GEN3 V4 kits
- [DIY-EFI - Gaggiuino Kits](https://diy-efi.co.uk/product-category/gaggiuino/) - UK, high quality kits
- [Espressio - 3D Printed Parts](https://gaggiuino.espressio.nl/) - Official 3D parts supplier
- [Printables - STL Files](https://www.printables.com/model/280617-gaggiuino-gaggia-classic-pro-touchscreen-housing-a) - Free STL downloads

### Installation Blogs & Videos
- [Kozikow Blog - Gaggiuino Install Experience](https://kozikow.blog/2024/02/22/gaggiuino-build-log/) - Detailed build log with photos
- YouTube: Search "Gaggiuino installation Gaggia Classic Pro" - Multiple walkthroughs available

---

## Notes & Lessons Learned

### Installation Notes

**Date**: ____________

**Issues Encountered**:
-
-
-

**Solutions**:
-
-
-

**Tips for Future Reference**:
-
-
-

---

### Shot Profiles Library

**Profile Name**: _________________________
- **Beans**: _________________________
- **Dose**: ___g
- **Pre-infusion**: ___bar for ___sec
- **Ramp**: ___bar/sec
- **Peak**: ___bar
- **Decline**: Yes / No, rate: ___
- **Total Time**: ___sec
- **Yield**: ___g
- **Tasting Notes**: _________________________

---

**Profile Name**: _________________________
- **Beans**: _________________________
- **Dose**: ___g
- **Pre-infusion**: ___bar for ___sec
- **Ramp**: ___bar/sec
- **Peak**: ___bar
- **Decline**: Yes / No, rate: ___
- **Total Time**: ___sec
- **Yield**: ___g
- **Tasting Notes**: _________________________

---

**Profile Name**: _________________________
- **Beans**: _________________________
- **Dose**: ___g
- **Pre-infusion**: ___bar for ___sec
- **Ramp**: ___bar/sec
- **Peak**: ___bar
- **Decline**: Yes / No, rate: ___
- **Total Time**: ___sec
- **Yield**: ___g
- **Tasting Notes**: _________________________

---

## Changelog

**v1.1**
- Added reference-kit details (GEN3 V4 Premium + PBT PRO) and Phase 7 parts-verification steps

**v1.0** - 2025-12-06
- Initial guide created for Gaggia RI9380/49 Classic Evo Pro
- Funnel mount recommended
- GEN3 V4 kit selected
- Checklist covers 15 phases from planning to completion

**Future Updates**:
- [ ] Add installation photos
- [ ] Document specific Evo Pro quirks discovered
- [ ] Add custom profiles created
- [ ] Update troubleshooting section with real issues encountered

---

*Last Updated: 2025-12-23*
*Machine: Gaggia RI9380/49 Classic Evo Pro (Thunder Black)*
*Gaggiuino Version: GEN3 V4 Premium + PBT PRO*
