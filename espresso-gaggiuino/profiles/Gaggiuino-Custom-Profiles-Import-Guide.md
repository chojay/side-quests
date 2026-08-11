# Gaggiuino Custom Profiles Import Guide

> Personal research notes on the [Gaggiuino](https://gaggiuino.github.io/) espresso machine mod on a Gaggia Classic Evo Pro (RI9380/49), exported from an Obsidian vault (compiled 2026-01-28). Wiki links flattened; sources cited inline.

> Complete guide to loading, importing, exporting, and managing custom espresso profiles on your [Gaggiuino](../machine/Gaggiuino-Modification-Overview.md)-equipped machine. Covers the web UI, GaggiMate, file formats, community profile sources, and management tips.

---

## 1. Profile File Format

### JSON Format

Gaggiuino and GaggiMate profiles use **`.json`** (JavaScript Object Notation) files. This is a plain text format that can be opened and edited with any text editor.

### Profile Structure Overview

A profile JSON contains two main sections: **phases** and **globalStopConditions**.

```json
{
  "label": "Profile Name",
  "type": "pro",
  "description": "Description of the profile",
  "temperature": 93,
  "phases": [
    {
      "name": "Pre-infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": {
        "type": "instant",
        "duration": 0,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 3,
        "flow": 0
      }
    },
    {
      "name": "Main Extraction",
      "phase": "extraction",
      "valve": 1,
      "duration": 30,
      "pump": {
        "target": "pressure",
        "pressure": 9,
        "flow": 0
      }
    }
  ],
  "globalStopConditions": {
    "time": 45000,
    "weight": 36,
    "waterPumped": 50
  }
}
```

### Key Profile Parameters

| Field | Description |
|-------|-------------|
| `label` | Profile name displayed on screen |
| `type` | "simple" or "pro" (pro enables advanced features) |
| `temperature` | Global brew temperature in Celsius |
| `phases` | Array of extraction phases |
| `globalStopConditions` | When to end the shot |

### Phase Parameters

| Field | Options | Description |
|-------|---------|-------------|
| `phase` | "preinfusion", "extraction", "decline" | Phase type |
| `duration` | Number (seconds) | Maximum phase duration |
| `valve` | 0 or 1 | 3-way valve open (1) or closed (0) |
| `pump.target` | "pressure" or "flow" | Control mode |
| `pump.pressure` | 0-12 | Target pressure in bar |
| `pump.flow` | 0-10 | Target flow rate in ml/s |
| `transition.type` | "instant", "linear", "ease_in", "ease_out", "ease_in_out" | How to ramp to target |

### Stop Conditions

| Field | Unit | Description |
|-------|------|-------------|
| `time` | milliseconds | Maximum shot time |
| `weight` | grams | Stop at this yield (requires scale) |
| `waterPumped` | milliliters | Stop at this volume |

---

## 2. Step-by-Step: Import Profiles via Web UI

### Prerequisites

- Gaggiuino Gen 3 with web interface enabled
- Device (phone/laptop) on same WiFi network as Gaggiuino
- Profile `.json` file saved on your device

### Import Process

1. **Connect to Gaggiuino Web Interface**
   - Find your Gaggiuino's IP address on the touchscreen: **Settings > Network > IP Address**
   - Open a web browser and navigate to that IP (e.g., `http://192.168.1.100`)

2. **Navigate to Profiles Page**
   - Click "Profiles" in the web UI navigation

3. **Import the Profile**
   - Click the **import button** at the top right of the Profiles page
   - Select your `.json` profile file from your device
   - The profile uploads and appears in your profile list

4. **Favorite the Profile for Use**
   - Imported profiles aren't active by default
   - Click the **star icon** on the left side of the profile card to "favorite" it
   - Favorited profiles become selectable on the machine touchscreen

5. **Verify on Machine**
   - The profile should now appear in your profile selection list on the Gaggiuino touchscreen

---

## 3. Step-by-Step: Export Profiles

### Export from Web UI

1. Go to the **Profiles** page in the web UI
2. Find the profile you want to export
3. Click the **export symbol** on the right side of the profile card
4. The `.json` file downloads to your device
5. Share the file via Discord, email, or any file sharing service

### Why Export?

- **Backup** your custom profiles before firmware updates
- **Share** with the community on Discord
- **Transfer** to another Gaggiuino machine
- **Edit** profiles manually in a text editor

---

## 4. GaggiMate Profile Management

[GaggiMate](https://docs.gaggimate.eu/docs/profiles/) is a related firmware project with excellent profile management documentation. Many concepts apply to Gaggiuino as well.

### GaggiMate Profile Types

| Type | Description | Best For |
|------|-------------|----------|
| **Simple Profile** | Basic three-phase structure | Beginners, standard espresso |
| **Pro Profile** | Advanced features: pressure targeting, flow control, temp overrides, multiple stop conditions | Experienced users, complex recipes |

### Creating a New Profile in GaggiMate

1. Navigate to **Profiles** page in web UI
2. Click **"Add new"** at the bottom of the page
3. Select **"Simple profile"** or **"Pro profile"**
4. Configure your phases and parameters
5. Save and favorite the profile

### Manual JSON Editing

You can also write profiles as JSON files directly and import them:

1. Copy an existing profile JSON as a template
2. Edit in any text editor (VS Code, Notepad++, etc.)
3. Modify parameters as needed
4. Import via the web UI

---

## 5. Where to Download Community Profiles

### Primary Sources

| Source | URL | Notes |
|--------|-----|-------|
| **Gaggiuino Discord** | [discord.com/invite/gaggiuino](https://discord.com/invite/gaggiuino-890339612441063494) | **#profiles channel** - Primary community source, 21,000+ members |
| **GaggiMate Docs** | [docs.gaggimate.eu/docs/profiles/](https://docs.gaggimate.eu/docs/profiles/) | Sample profiles with download links |
| **SproFiler** | [sprofiler.io](https://sprofiler.io/) | Shot analysis + profile downloads (Early Access) |
| **GitHub Discussions** | [github.com/Zer0-bit/gaggiuino/discussions](https://github.com/Zer0-bit/gaggiuino/discussions) | Community discussions with profile sharing |

### Discord Profile Channel

The **#profiles** channel on the Gaggiuino Discord is the most active source for community profiles. Users share:
- Lever machine profiles (Londinium style)
- Blooming/filter-style profiles
- Turbo shot profiles
- Bean-specific profiles
- Milk drink profiles

### GaggiMate Sample Profiles

Available from the [GaggiMate documentation](https://docs.gaggimate.eu/docs/profiles/):

| Profile | Use Case |
|---------|----------|
| **Cremina Lever** | Medium-dark to very dark roasts |
| **Medium 18g 1:2** | Simple pre-infusion design |
| **Backflush** | Machine maintenance (use with Cafiza) |

### SproFiler Platform

[SproFiler](https://sprofiler.io/) is a community platform for Gaggiuino users (currently in Early Access):

- **Record** shot data from your Gaggiuino
- **Analyze** extraction metrics
- **Download** profiles from other enthusiasts
- **Share** your shot history

To use SproFiler:
1. Install the Gaggiuino mod on your machine
2. Connect Gaggiuino to SproFiler via the integration
3. Start tracking and sharing shots

---

## 6. Profile Management Tips

### Organization

- **Naming convention**: Use descriptive names with bean info
  - Example: `Ethiopia Yirg Light Bloom v2`
  - Example: `Brazil Medium Lever 18g`
- **Version numbers**: Append `v1`, `v2`, etc. as you iterate
- **Delete unused profiles**: Keep your list manageable

### Backup Strategy

1. **Before firmware updates**: Export all custom profiles
2. **Weekly backup**: Export favorites to a folder on your computer
3. **Cloud sync**: Store profile JSONs in Google Drive/Dropbox

### Testing New Profiles

1. **Read the description**: Understand what the profile is designed for
2. **Match the beans**: Profiles are often roast-specific
3. **Start with suggested dose**: Most profiles assume 18g dose
4. **Adjust grind first**: Before modifying the profile itself
5. **Pull 3-5 shots**: Before judging a new profile

### Common Profile Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Shot runs too fast | Grind too coarse for profile | Grind finer |
| Shot chokes/stalls | Grind too fine for profile | Grind coarser |
| Profile won't import | Invalid JSON syntax | Check for missing commas, brackets |
| Profile not appearing | Not favorited | Click star icon in web UI |
| Weight stop not working | No scale connected | Connect BLE scale or install load cells |

### Editing Existing Profiles

Rather than modifying community profiles directly:

1. **Import** the original profile
2. **Duplicate** it (export, rename JSON, re-import)
3. **Edit** your copy
4. Keep the original for reference

---

## 7. Advanced: Profile JSON Editing

### Useful Modifications

**Change target yield:**
```json
"globalStopConditions": {
  "weight": 40  // Changed from 36g to 40g
}
```

**Adjust pre-infusion pressure:**
```json
{
  "name": "Pre-infusion",
  "pump": {
    "target": "pressure",
    "pressure": 2  // Lowered from 3 bar
  }
}
```

**Extend pre-infusion time:**
```json
{
  "name": "Pre-infusion",
  "duration": 10  // Extended from 5 seconds
}
```

### JSON Validation

Before importing edited JSON:
1. Use [jsonlint.com](https://jsonlint.com/) to validate syntax
2. Ensure all brackets and commas are correct
3. Check that values are appropriate types (numbers vs strings)

---

## 8. API for Advanced Users

For programmatic profile management, the [gaggiuino_api](https://github.com/ALERTua/gaggiuino_api) Python library provides:

- **Retrieve** brewing profiles
- **Select** active profile
- **Access** shot history
- **Control** machine settings

### Example Usage

```python
from gaggiuino_api import GaggiuinoClient

client = GaggiuinoClient("http://192.168.1.100")
profiles = await client.get_profiles()
await client.select_profile("Lever Machine")
```

This is useful for:
- Automating profile backups
- Building custom dashboards
- Integration with home automation

---

## 9. Quick Reference

### Import Workflow
```
1. Download .json profile → 2. Open web UI → 3. Profiles page →
4. Click import (top right) → 5. Select file → 6. Click star to favorite
```

### Export Workflow
```
1. Open web UI → 2. Profiles page → 3. Click export icon on profile card →
4. Save .json file
```

### Key URLs

| Resource | URL |
|----------|-----|
| **Gaggiuino Discord** | [discord.com/invite/gaggiuino](https://discord.com/invite/gaggiuino-890339612441063494) |
| **GaggiMate Profiles Docs** | [docs.gaggimate.eu/docs/profiles/](https://docs.gaggimate.eu/docs/profiles/) |
| **SproFiler** | [sprofiler.io](https://sprofiler.io/) |
| **GitHub API** | [github.com/ALERTua/gaggiuino_api](https://github.com/ALERTua/gaggiuino_api) |
| **Profile Format Discussion** | [GitHub Discussion \#350](https://github.com/Zer0-bit/gaggiuino/discussions/350) |

---

## Related Notes

### Gaggiuino Setup
- [Gaggiuino-Modification-Overview](../machine/Gaggiuino-Modification-Overview.md) - Features, community, resources
- [Gaggiuino-Popular-Community-Profiles-Research](../research-notes/Gaggiuino-Popular-Community-Profiles-Research.md) - Best profiles by roast level
- [Gaggiuino-Post-Install-Operation-Guide](../machine/Gaggiuino-Post-Install-Operation-Guide.md) - Daily operation, profile progression guide
- [Gaggiuino-Bluetooth-Scale-Recommendations](../machine/Gaggiuino-Bluetooth-Scale-Recommendations.md) - BLE scales for gravimetric stop
- [Gaggiuino-Pressure-Profiling-Extraction-Parameters](Gaggiuino-Pressure-Profiling-Extraction-Parameters.md) - Extraction theory for profiling

---

## Sources

- [GaggiMate Profiles Documentation](https://docs.gaggimate.eu/docs/profiles/)
- [Gaggiuino GitHub Discussion \#350 - Profile Format](https://github.com/Zer0-bit/gaggiuino/discussions/350)
- [Gaggiuino API Documentation](https://github.com/ALERTua/gaggiuino_api)
- [SproFiler Platform](https://sprofiler.io/)
- [Gaggiuino Discord Community](https://discord.com/invite/gaggiuino-890339612441063494)

---

*Created: 2026-01-28*
*Confidence: High - Based on official GaggiMate documentation, GitHub discussions, and community sources*
