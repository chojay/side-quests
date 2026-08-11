# Obsidian Integration Reference

Part of the `obsidian-deep-research` skill (Implementation Guidelines). Read this file
during Phase 9 and while writing notes: Obsidian syntax, tables, living document
features, and source archiving.

## Contents

- Obsidian Syntax Quick Reference (wiki links, embeds, block IDs, query blocks, callouts)
- Table Formatting
- Living Document Features (dynamic query blocks, version comparison links, staleness
  warnings, living recommendation blocks, embedded update prompts, maintenance triggers
  & update prompts, cross-linking to updates, Dataview integration incl. All Research
  by Confidence Level)
- Source Archiving & Preservation (archiving strategy by source type, source library
  organization, citation export formats, automated archiving workflow, preservation
  priorities)

### Obsidian Syntax Quick Reference

#### Wiki Links
```markdown
[[Note Name]]                    # Basic link
[[Note Name|display text]]       # Aliased link
[[Note Name#Heading]]            # Link to heading
[[Note Name#^block-id]]          # Link to block
[[##search-term]]                # Search for headings
[[^^search-block]]               # Search for blocks
```

#### Embeds
```markdown
![[Note Name]]                   # Embed entire note
![[Note Name#Heading]]           # Embed heading section
![[Note Name#^block-id]]         # Embed specific block
![[image.png|400]]               # Embed image with width
![[audio.mp3]]                   # Embed audio player
![[document.pdf#page=5]]         # Embed PDF page
```

#### Block IDs
```markdown
This is an important finding. ^finding-1
- Key insight here ^insight-1
```
- Add `^block-id` at end of any paragraph or list item
- Reference with `[[Note#^finding-1]]` or embed with `![[Note#^finding-1]]`

#### Query Blocks (Dynamic Embeds)
````markdown
```query
tag:#research tag:#domain/health
```
````
- Embeds live search results that update automatically

#### Callouts (Research-Relevant Types)
```markdown
> [!tip] Key Insight
> Important finding here

> [!warning] Limitation
> Study had small sample size

> [!question] Open Question
> Needs further research

> [!note]- Collapsed Details
> Click to expand methodology details
```
- Use `-` for collapsed, `+` for expanded by default

### Table Formatting

⚠️ **CRITICAL: Tables MUST have a blank line before them to render correctly in Obsidian!**

❌ **Wrong** (table won't render):
```markdown
Price Analysis:
| Retailer | Price |
|----------|-------|
| Amazon   | $50   |
```

✅ **Correct** (blank line before table):
```markdown
Price Analysis:

| Retailer | Price |
|----------|-------|
| Amazon   | $50   |
```

**Table alignment**:
```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| L    |   C    |     R |
```

### Living Document Features

Transform static research notes into dynamic, self-updating knowledge that evolves with new information.

#### Dynamic Query Blocks

Use Obsidian's query blocks to create self-updating sections that automatically surface related content:

```markdown
## Related Research (Auto-Updated)

```query
tag:#research tag:#domain/smart-home
-tag:#lifecycle/archived
sort:created desc
limit:10
```
```

This query block automatically shows the 10 most recent smart home research notes, excluding archived ones.

**Common Query Patterns**:

**Recent Research in Same Domain**:
````markdown
```query
tag:#domain/{current-domain}
-tag:#lifecycle/deprecated
sort:created desc
limit:10
```
````

**High-Confidence Research in Related Area**:
````markdown
```query
tag:#domain/{related-domain}
file:("⭐⭐⭐")
sort:confidence desc
limit:5
```
````

**Research Needing Review**:
````markdown
```query
tag:#temporal/dynamic
-path:Archive
created:>-6months created:<-3months
```
````

**Failed/Blocked Sources to Retry**:
````markdown
```query
file:("❌" OR "geo-blocked" OR "paywall")
sort:modified desc
```
````

#### Version Comparison Links

Create explicit version tracking with links to previous iterations:

```markdown
## Version History & Evolution

**Current Version**: 2.1 (2025-01-15)
**Previous Versions**: [[Research v2.0]] | [[Research v1.1]] | [[Research v1.0]]

### Changes in v2.1

**New in this version**:
- 🆕 Added 15 sources (50 → 65 total)
- 📈 Confidence: 0.78 → 0.85 (+0.07)
- 🔄 Updated all pricing (average -12%)
- ⚠️ Added firmware update warning for Product A

**Compared to v2.0** ([[Research v2.0]]):
- Confidence: 0.85 vs 0.90 (-0.05, explained by new Matter protocol uncertainty)
- Top Recommendation: Still Product A (unchanged)
- New Entrant: Product F (Matter-certified, added 2024-12)

**Compared to v1.0** ([[Research v1.0]]):
- Confidence: 0.85 vs 0.78 (+0.07)
- Top Recommendation: Product A vs Product B (changed due to reliability improvements)
- Price Trend: Average prices -18% (market maturation)
- Source Count: 65 vs 47 (+38% more evidence)
```

#### Staleness Warnings with Action Prompts

Add dynamic staleness indicators that guide users on next steps:

```markdown
> [!info] Research Age Assessment
> **Last Updated**: 2025-01-15 (4 months ago)
> **Temporal Classification**: Dynamic (6-12 month validity)
> **Projected Confidence**: 0.81 (↓ 0.04 from initial 0.85)
>
> **Status**: 🟡 Approaching Review Threshold
>
> **Quick Health Check** (5 min):
> - [ ] Visit top 3 product pages - still available?
> - [ ] Check Amazon review counts - major increase?
> - [ ] Google "[product name] recall 2025" - any safety issues?
>
> **If Quick Check Reveals Issues**:
> → Launch Incremental Research Mode: [[#Expand Existing Research]]
>
> **Next Scheduled Review**: 2025-07-15 (in 2 months)
```

**Auto-Generated Staleness Levels**:
- **🟢 Fresh** (0-3 months): No action needed
- **🟡 Aging** (3-6 months): Quick health check recommended
- **🟠 Stale** (6-9 months): Standard update needed
- **🔴 Outdated** (9+ months): Major re-research required

#### Living Recommendation Blocks

Create recommendation blocks that update based on monitoring data:

```markdown
## Current Recommendations (Updated 2025-05-15)

### Top Pick: Product A ⭐⭐⭐ ($129)

**Status**: ✅ **Still Available** | **Price**: $129 (↓ $10 from last update) | **Reviews**: 4.3★ (↑ from 4.2★)

**Recent Developments** (since last update):
- ✨ Firmware v2.3 released (2025-04-20) - adds Matter support
- 📊 Review count: 2,340 → 3,150 (+810 reviews, +35%)
- 💰 Price trend: $139 → $129 (-7%, good time to buy)
- ⚠️ Minor recall (2025-03-15): Power adapter for units sold Jan-Feb 2024 only
  - **Impact**: Minimal (0.1% of units, free replacement program)
  - **Updated Confidence**: 0.85 → 0.83 (-0.02)

**Recommendation Status**: **UPGRADED** - Matter support addition strengthens future-proofing

---

### Runner-Up: Product G ⭐⭐⭐ ($189)

**Status**: ⚠️ **Limited Stock** | **Price**: $189 (stable) | **Reviews**: 4.5★ (stable)

**Recent Developments**:
- ⚠️ Availability issues reported (out of stock on Amazon for 3+ weeks)
- 📢 Manufacturer announced Product G2 coming Q3 2025
- 💡 **Recommendation**: Consider waiting for G2 or switching to Product C

**Recommendation Status**: **DOWNGRADED** - Availability concerns + imminent replacement

---

**Monitoring Active**:
- ✅ Price alerts configured (CamelCamelCamel)
- ✅ Safety alerts subscribed (CPSC)
- ✅ Reddit saved searches active (r/smarthome, r/homekit)
```

#### Embedded Update Prompts

Include actionable prompts within the research note for future updates:

```markdown
## Maintenance Triggers & Update Prompts

**This research note will automatically flag for update when**:

### Critical Triggers (Immediate Update Required)
```yaml
alerts:
  - type: "safety_recall"
    check: "CPSC database for [product names]"
    frequency: "weekly"
    action: "Add prominent warning banner, downgrade confidence by 0.20"

  - type: "product_discontinuation"
    check: "Manufacturer website availability"
    frequency: "monthly"
    action: "Mark as deprecated, create replacement research"
```

### High-Priority Triggers (Update Within 2 Weeks)
```yaml
alerts:
  - type: "price_drop_major"
    threshold: ">25%"
    check: "CamelCamelCamel API"
    frequency: "daily"
    action: "Update price analysis, notify if changes recommendation"

  - type: "new_category_leader"
    threshold: "Product with >4.5★ and >500 reviews not in current list"
    check: "Amazon search for [category]"
    frequency: "monthly"
    action: "Add to comparison matrix, re-evaluate rankings"
```

### Standard Triggers (Review at Next Scheduled Interval)
```yaml
alerts:
  - type: "review_count_increase"
    threshold: ">30%"
    check: "Amazon review count"
    frequency: "quarterly"
    action: "Re-analyze sentiment, update confidence scores"

  - type: "temporal_decay"
    threshold: "6 months since last update"
    check: "Note frontmatter modified date"
    frequency: "automatic"
    action: "Display staleness warning, suggest standard update"
```

**How to Use These Triggers**:
1. Set up external monitoring tools (Google Alerts, price trackers)
2. When trigger fires, return to this note
3. Follow the specified action
4. Update version number appropriately (see [[#Research Versioning Strategy]])
```

#### Cross-Linking to Updates

Create bidirectional links between old and new research:

```markdown
## Evolution & Related Research

**This Research**:
- [[Research v2.1]] (Current) - You are here
- Supersedes: [[Research v2.0]] (2024-06-10)
- Supersedes: [[Research v1.0]] (2024-01-15)

**Related Topics** (Auto-Generated via Query):

```query
line:(Research v2.1)
-file:"Research v2.1"
```

**Mentions Across Vault**: {auto-populated by backlinks}

**Research That References This**:
- [[Home Setup Guide]] - links to our Product A recommendation
- [[Air Quality Master List]] - uses this for the purifier category
- [[HomeKit Ecosystem]] - references smart home integration analysis

**When This Research Is Updated**:
→ Update references in all linked notes above
→ Add note to [[Research MOC]] with version bump
→ Notify via Obsidian Sync if shared vault
```

#### Dataview Integration (Optional)

If using Dataview plugin, create dynamic tables:

````markdown
## All Research by Confidence Level

```dataview
TABLE
  confidence_overall as "Confidence",
  sources_count as "Sources",
  file.cday as "Created",
  file.mday as "Last Updated"
FROM #research
WHERE !contains(lifecycle, "deprecated")
SORT confidence_overall DESC
LIMIT 20
```
````

**Common Dataview Queries for Living Research**:

**Research Needing Review**:
````markdown
```dataview
TABLE
  temporal_classification,
  file.mday as "Last Updated",
  next_review_date as "Review Due"
FROM #research
WHERE file.mday < date(today) - dur(3 months)
  AND temporal_classification = "Dynamic"
SORT file.mday ASC
```
````

**Highest Confidence Research**:
````markdown
```dataview
TABLE
  confidence_overall as "Confidence",
  sources_count as "Sources",
  tags as "Tags"
FROM #research
WHERE confidence_overall >= 0.85
SORT confidence_overall DESC, sources_count DESC
```
````

**Research Version Timeline**:
````markdown
```dataview
TABLE
  research_version as "Version",
  file.cday as "Date",
  changelog[0].changes as "Changes"
FROM #research
WHERE contains(file.name, "{Topic}")
SORT research_version ASC
```
````

### Source Archiving & Preservation

Research depends on external sources that may break, move, or disappear. Implement archiving to ensure long-term verifiability.

#### Archiving Strategy by Source Type

**For All Sources** (minimum archiving):
1. **Capture Source Metadata**:
```yaml
source_archive:
  url: "https://example.com/article"
  title: "Original Article Title"
  author: "Author Name"
  published: "2024-06-15"
  accessed: "2025-01-15"
  credibility: 0.85
  archive_status: "captured"
```

2. **Markdown Snapshot** (text content only):
   - Save article text via WebFetch to markdown file
   - Store in `/Sources/{Topic}/archive/source-001.md`
   - Include metadata header

**For Critical Sources** (comprehensive archiving):
1. **Web Archive Links** (automatic):
   - Internet Archive: `https://web.archive.org/save/{URL}`
   - Archive.today: `https://archive.today/{URL}`
   - Include both in source citations

2. **PDF Screenshot** (visual preservation):
   ```
   mcp__claude-in-chrome__computer(action="screenshot", tabId=TAB, save_to_disk=true, 
     filePath="vault/Sources/{Topic}/archive/article-20250115.pdf",
     fullPage=true
   )
   ```

3. **Extracted Data** (structured):
   - Key findings as atomic notes with block IDs
   - Tables/charts as separate markdown files or images
   - Quotes with page numbers/timestamps

#### Source Library Organization

```
vault/
├── Research-Sources/
│   ├── {Topic-Name}/
│   │   ├── sources.md              # Master source list
│   │   ├── archive/
│   │   │   ├── source-001.md       # Markdown snapshot
│   │   │   ├── source-001.pdf      # Visual preservation
│   │   │   ├── source-002.md
│   │   │   └── ...
│   │   ├── citations.bib           # BibTeX export
│   │   └── source-metadata.yaml    # Structured metadata
│   └── {Other-Topic}/
```

**Master Source List Template** (`sources.md`):

```markdown
# Sources for [[{Research Topic}]]

## Primary Sources (High Credibility)

### Expert Reviews

1. **Wirecutter - Best Air Purifier (2024)**
   - URL: https://www.nytimes.com/wirecutter/reviews/best-air-purifier/
   - Accessed: 2025-01-15
   - Credibility: 0.90
   - Archive: [Internet Archive](https://web.archive.org/...) | [Archive.today](https://archive.today/...)
   - Status: ⚠️ Paywalled - Used summary from WebSearch
   - Local: [[archive/source-001.md]]

2. **Consumer Reports - Air Purifier Buying Guide**
   - URL: https://www.consumerreports.org/...
   - Accessed: 2025-01-15
   - Credibility: 0.95
   - Archive: [PDF](archive/source-002.pdf)
   - Status: ✅ Full text archived
   - Local: [[archive/source-002.md]]

### Academic Sources

3. **Indoor Air Journal - Portable Air Cleaner Efficacy (2023)**
   - DOI: 10.1111/ina.2023-XXXXX
   - Accessed: 2025-01-15
   - Credibility: 0.95
   - Archive: [Preprint](https://arxiv.org/...) | [PubMed](https://pubmed.ncbi.nlm.nih.gov/...)
   - Status: ✅ Full PDF downloaded
   - Local: [[archive/source-003.pdf]]

## Secondary Sources (Medium Credibility)

### User Reviews

4. **Amazon Product Reviews - Levoit Core 400S**
   - URL: https://www.amazon.com/...
   - Accessed: 2025-01-15
   - Review Count: 2,340 (avg 4.2★)
   - Credibility: 0.70
   - Archive: Snapshot of first 10 pages (representative sample)
   - Local: [[archive/amazon-levoit-reviews-2025-01-15.md]]

## Failed/Blocked Sources

5. **Coupang Reviews - Korean Market Analysis**
   - URL: https://www.coupang.com/...
   - Attempted: 2025-01-15
   - Status: ❌ Geo-blocked (US IP restrictions)
   - Fallback: Used Reddit r/Korea discussions as proxy
   - Retry Strategy: Use VPN or naver-korean-search skill
```

#### Citation Export Formats

**BibTeX Export** (`citations.bib`):

```bibtex
@article{smith2023aircleaner,
  title={Portable Air Cleaner Efficacy in Residential Settings},
  author={Smith, Jane and Johnson, Bob},
  journal={Indoor Air},
  volume={33},
  number={3},
  pages={e2023XXXXX},
  year={2023},
  doi={10.1111/ina.2023-XXXXX},
  url={https://pubmed.ncbi.nlm.nih.gov/...},
  note={Credibility: 0.95, Accessed: 2025-01-15}
}

@misc{wirecutter2024purifier,
  title={The Best Air Purifier},
  author={{Wirecutter Staff}},
  year={2024},
  url={https://www.nytimes.com/wirecutter/reviews/best-air-purifier/},
  note={Credibility: 0.90, Paywalled - Used summary, Accessed: 2025-01-15}
}
```

**APA 7th Format** (for reports):

Smith, J., & Johnson, B. (2023). Portable air cleaner efficacy in residential settings. *Indoor Air*, *33*(3), e2023XXXXX. https://doi.org/10.1111/ina.2023-XXXXX

Wirecutter Staff. (2024). *The best air purifier*. The New York Times. https://www.nytimes.com/wirecutter/reviews/best-air-purifier/ (Note: Paywalled, summary used)

**Chicago Style** (for publications):

Smith, Jane, and Bob Johnson. "Portable Air Cleaner Efficacy in Residential Settings." *Indoor Air* 33, no. 3 (2023): e2023XXXXX. https://doi.org/10.1111/ina.2023-XXXXX.

#### Automated Archiving Workflow

**During Research (Phase 5-6)**:

For each source:
1. Fetch content (WebFetch or claude-in-chrome)
2. Extract to markdown with metadata header
3. Save to `archive/source-{nnn}.md`
4. Add to master source list with status
5. Attempt web archiving (submit to archive.org)

**Example Archived Source** (`archive/source-001.md`):

```markdown
---
source_url: https://www.nytimes.com/wirecutter/reviews/best-air-purifier/
title: The Best Air Purifier
author: Wirecutter Staff
published: 2024-06-15
accessed: 2025-01-15
credibility: 0.90
archive_date: 2025-01-15
archive_method: WebSearch summary (paywall)
---

# The Best Air Purifier

**Source**: Wirecutter (New York Times)
**Archived**: 2025-01-15
**Status**: Paywalled - Summary extracted via WebSearch

## Key Findings

- **Top Pick**: Coway Airmega AP-1512HH - Best overall air purifier
  - CADR performance: Excellent for its class
  - Noise level: Quiet at low speeds
  - Price: $229
  - Standout feature: Compact footprint, low filter cost

- **Budget Pick**: Levoit Core 300 - Best small-room option
  - Price: $99
  - Benefit: Cheap replacement filters, quiet operation
  - Limitation: Small coverage area

[Continue with extracted content...]

## Citation

Wirecutter Staff. (2024). *The best air purifier*. The New York Times. https://www.nytimes.com/wirecutter/reviews/best-air-purifier/

**Archived**: [Internet Archive](https://web.archive.org/...) | Local: vault/Research-Sources/Air-Purifier/archive/source-001.md
```

#### Preservation Priorities

**Archive Everything**:
- Source URLs
- Access dates
- Credibility scores
- Brief summaries

**Archive Full Text For**:
- High credibility sources (>0.85)
- Unique/irreplaceable content
- Sources with known volatility (personal blogs, small sites)
- Non-English sources (may be hard to re-access)

**Create PDF Archives For**:
- Visual content (charts, infographics, comparison matrices)
- Sources that required browser automation
- Academic papers (with DOI backup)

**Skip Archiving** (link only):
- Stable sources (Wikipedia, major news archives)
- Sources with permanent DOIs (academic journals)
- Commercial product pages (Amazon, etc.) - too dynamic

