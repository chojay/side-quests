# Gaggiuino Bluetooth Scale Recommendations

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-01-25). Wiki links flattened; sources cited inline.

## Context

With [Gaggiuino](Gaggiuino-Modification-Overview.md) installed without load cells or ToFLED, a **Bluetooth scale** provides gravimetric shot profiling - enabling stop-on-weight functionality without opening the machine to add load cells. Non-Bluetooth scales (such as the Maestri House) cannot pair with Gaggiuino. For setup instructions once you have a BLE scale, see [Gaggiuino Post-Install Operation Guide](Gaggiuino-Post-Install-Operation-Guide.md).

Gaggiuino supports Bluetooth scales via the [esp-arduino-ble-scales](https://github.com/Zer0-bit/esp-arduino-ble-scales) library, which currently has 17 confirmed-compatible scales.

> **Important:** When updating Gaggiuino firmware, disable Bluetooth Scales first (Settings → Scales).

---

## Top 3 Recommendations

### 1. Bookoo Themis Ultra - Best Overall ⭐⭐⭐

| Spec | Detail |
|------|--------|
| **Price** | ~$99 (sale) / $134 (regular) |
| **Accuracy** | 0.1g, sub-100ms response |
| **Waterproof** | IP67 (fully sealed) |
| **Battery** | 2000mAh, up to 72 hours use |
| **Charging** | USB-C |
| **Weight** | 380g |
| **Dimensions** | 127 × 112 × 18mm |
| **Gaggiuino Compatible** | ✅ Confirmed |

**Why it's \#1:**
- **Native Gaggiuino integration** - explicitly listed as compatible for hands-free shot control
- **Real-time flow rate display** (numeric, not just LED like Acaia Lunar)
- **IP67 waterproof** - handles espresso spills, steam, and rinsing without worry
- **Best value** at ~$99 for the feature set
- Transparent PC construction (not glass - more durable)
- Works with Beanconqueror app for brew logging

**Considerations:**
- Battery is not user-replaceable (sealed for waterproofing)
- Some users reported BLE disconnection after first shot (firmware-related, may be resolved with updates)

**Links:** [Official Site](https://bookoocoffee.com/products/bookoo-themis-ultra-coffee-scale) · [Home-Barista Thread](https://www.home-barista.com/brewing/new-bookoo-scale-themis-ultra-t99603.html)

---

### 2. DiFluid Microbalance - Best Value ⭐⭐⭐

| Spec | Detail |
|------|--------|
| **Price** | ~$79 |
| **Accuracy** | 0.1g (tested at 100.0g with calibration weight) |
| **Waterproof** | Not rated |
| **Battery** | 1000mAh |
| **Charging** | USB-C |
| **Range** | 0.2g – 3000g |
| **Gaggiuino Compatible** | ✅ Confirmed (standard + Ti) |

**Why it's \#2:**
- **Lowest price** of the three at $79
- **Accuracy rivals Acaia Lunar** - tested head-to-head: DiFluid read 100.0g vs Lunar's 99.83g with calibration weight
- Real-time flow rate tracking via DiFluid Café app
- Auto-timing function for espresso and pour-over
- OTA firmware updates
- Compact and heavy (feels premium)
- Also available as **Microbalance Ti** (~$109) with faster tare, vibration protection, and larger battery

**Considerations:**
- Not usable while charging
- No IP waterproof rating (be careful around espresso splashes)
- Smaller battery than Bookoo (1000 vs 2000mAh)

**Links:** [Official Site](https://digitizefluid.com/products/microbalance) · [Amazon](https://www.amazon.com/DiFluid-Espresso-Tracking-Precision-Function/dp/B0BQ6J8H5W) · [Home-Barista Impressions](https://www.home-barista.com/advice/first-pictures-and-impression-difluid-microbalance-t84379.html)

---

### 3. Felicita Arc - Premium Build ⭐⭐

| Spec | Detail |
|------|--------|
| **Price** | ~$110 |
| **Accuracy** | 0.1g, ultra-fast response |
| **Waterproof** | IPX5 (splash-proof) |
| **Battery** | 1100mAh, 30–40 hours use |
| **Charging** | USB-C |
| **Weight** | 255g |
| **Dimensions** | 135 × 105 × 15.5mm |
| **Gaggiuino Compatible** | ✅ Confirmed |

**Why it's \#3:**
- **Aluminum construction** - most premium feel and thinnest profile (15.5mm)
- **IPX5 splash-proof** - reasonable protection without full submersion rating
- 5 dedicated modes including espresso auto-timing and auto-tare
- Lightest of the three at 255g
- Strong community reputation as a more affordable Acaia Lunar alternative

**Considerations:**
- **Confusing button interface** - mode switching requires memorizing button combos
- IPX5 is less protective than Bookoo's IP67
- Higher price than DiFluid with fewer standout features
- Aesthetically very similar to Acaia Lunar (some consider it a clone)

**Links:** [Amazon](https://www.amazon.com/FELICITA-Electronic-Espresso-Pour-Over-Functions/dp/B0DBLFRVBF) · [Tom's Guide Review](https://www.tomsguide.com/home/coffee-scales/felicita-arc-coffee-scale-review)

---

## Quick Comparison

| Feature | Bookoo Themis Ultra | DiFluid Microbalance | Felicita Arc |
|---------|:------------------:|:-------------------:|:------------:|
| **Price** | ~$99 | ~$79 | ~$110 |
| **Accuracy** | 0.1g | 0.1g | 0.1g |
| **Waterproof** | IP67 ✅ | None ❌ | IPX5 🟡 |
| **Battery** | 2000mAh | 1000mAh | 1100mAh |
| **Flow Rate Display** | Numeric (real-time) | Via app | Via app |
| **Construction** | Transparent PC | Metal/Plastic | Aluminum |
| **Gaggiuino** | ✅ | ✅ | ✅ |
| **Best For** | Overall pick | Budget pick | Build quality |

---

## Other Compatible Scales

The full list of Gaggiuino-compatible BLE scales (via [esp-arduino-ble-scales](https://github.com/Zer0-bit/esp-arduino-ble-scales)):

- Acaia Lunar / Pearl (premium, $200+)
- Decent Scale
- Timemore Black Mirror DUO
- Varia AKU / Mini
- Eureka Precisa
- Eclair
- Solobarista
- WeighMyBrew
- Brainslug DIY scales

---

## Recommendation

For a [Gaggiuino](Gaggiuino-Modification-Overview.md) setup with TOF sensor, the **Bookoo Themis Ultra** is the strongest pick:
- Native Gaggiuino integration at ~$99
- IP67 means zero stress about espresso mess
- Real-time numeric flow rate on the scale itself
- Largest battery of the group

If budget is the priority, the **DiFluid Microbalance** at $79 delivers Lunar-rivaling accuracy. Just be more careful with water around it.

---

*Last updated: 2026-01-25*
*Sources: [Gaggiuino BLE Scales Library](https://github.com/Zer0-bit/esp-arduino-ble-scales), [Home-Barista Forums](https://www.home-barista.com), [Tom's Guide](https://www.tomsguide.com), [CoffeeSnobs](https://coffeesnobs.com.au)*
