# Incremental Research Modes

Part of the `obsidian-deep-research` skill. Read this file when updating, expanding,
or following up on existing research instead of running a full research cycle.

### Incremental Research Modes

**Purpose**: Enable research updates, expansions, and follow-ups without full re-research cycles.

**When to Use**: Research maintenance, quick questions, adding alternatives to comparisons, or updating based on monitoring alerts.

#### Mode 1: Expand Existing Research

**Use Case**: Update research note with new information without full re-research.

**When to Use**:
- Research is >6 months old and needs refresh
- New products/studies have emerged since initial research
- Confidence scores are low (⭐⭐ or ⭐) and need strengthening
- Unresolved questions from initial research now have answers

**Workflow**:
1. **Read existing research note**
   - Extract current confidence scores
   - Identify sections tagged with low confidence (⭐)
   - Note "Known Unknowns" and unresolved questions
   - Check last_updated date

2. **Identify expansion areas**:
   - **Low confidence claims** (⭐) → Prioritize for additional sources
   - **Unresolved questions** → Launch targeted research
   - **Outdated sections** (>6 months in fast-changing domains) → Refresh
   - **New developments** → Add recent findings

3. **Launch targeted agents** (2-3 focused agents, not full 6-8):
   ```
   Example for updating smart doorbell research:

   Task(subagent_type="general-purpose", prompt="UPDATE: New HomeKit doorbell models released since 2024-06:
   - Search for models released in last 6 months
   - Compare specs to existing recommendations
   - Check if any outperform current top picks
   - Update pricing for all existing models
   Return: New models to add, pricing updates, recommendation changes")

   Task(subagent_type="general-purpose", prompt="UPDATE: Long-term reliability data for [[Logitech Circle View]]:
   - Search for 2+ year reviews
   - Look for common failure modes after extended use
   - Update MTBF estimates
   Return: Long-term reliability assessment")
   ```

4. **Merge new findings**:
   - Add new sections for major discoveries
   - Update confidence scores based on new evidence
   - Revise recommendations if better options emerged
   - Update "Last Updated" date

5. **Increment research version**:
   ```yaml
   research_version: 1.1  # Was 1.0
   changelog:
     - 1.0: Initial research (2024-06-15) - confidence: 0.75
     - 1.1: Updated pricing, added 2 new models (2025-01-15) - confidence: 0.82
   ```

**Effort**: ~30-45 minutes (vs. 2 hours for full Standard Research)

---

#### Mode 2: Quick Follow-Up Questions

**Use Case**: Answer specific sub-questions without full research cycle.

**When to Use**:
- User asks follow-up: "What about waterproof rating?"
- Exploring a specific aspect not covered initially
- Validating a single claim or specification

**Workflow**:
1. **Check existing research** for related information
2. **If gap found**:
   - Launch single targeted agent (1 agent only)
   - Narrow search scope: "{product} IP rating waterproof"
   - Extract answer from 3-5 sources minimum
3. **Add to existing note** as new subsection:
   ```markdown
   ## Waterproof Rating (Added 2025-01-20)

   **Rating**: IP67 (⭐⭐ confidence)
   - Survives submersion in 1m water for 30 minutes
   - Sources: Manufacturer spec sheet, 3 YouTube teardown videos
   - Caveat: Rating applies to unit only, not mounting hardware
   ```
4. **Update last_modified** date (not research version - minor addition)

**Effort**: ~10-15 minutes

---

#### Mode 3: Comparative Addition

**Use Case**: Add new product/option to existing comparison without re-researching everything.

**When to Use**:
- New competitor released
- User asks "How does Product X compare to your recommendation?"
- Expanding comparison matrix

**Workflow**:
1. **Read existing comparison matrix**:
   - Extract evaluation criteria used
   - Note scoring methodology
   - Understand what dimensions were compared

2. **Research new item using same criteria**:
   ```
   Task(subagent_type="general-purpose", prompt="COMPARATIVE ANALYSIS: [[New Product Y]] using existing evaluation framework:

   Evaluate on same dimensions as [[Product A]], [[Product B]], [[Product C]]:
   - Video quality (1-10 scale)
   - Smart home integration (HomeKit compatibility)
   - Price value (cost-per-feature analysis)
   - Reliability (failure rate from reviews)
   - User satisfaction (avg rating, recommend %)

   Use same sources types:
   - Reddit r/HomeKit
   - Amazon reviews
   - YouTube reviews
   - Wirecutter/Consumer Reports if available

   Return: Scores for each dimension, direct comparisons to existing recommendations")
   ```

3. **Add new row/column** to comparison matrix:
   | Product | Video Quality | Integration | Price Value | Reliability | Overall |
   |---------|---------------|-------------|-------------|-------------|---------|
   | Product A | 8/10 | ⭐⭐⭐ | $$ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
   | Product B | 7/10 | ⭐⭐ | $ | ⭐⭐ | ⭐⭐⭐ |
   | **Product Y (NEW)** | **9/10** | **⭐⭐⭐** | **$$$** | **⭐⭐** | **⭐⭐⭐⭐** |

4. **Update recommendations** if new item changes hierarchy:
   ```markdown
   > [!info] Update 2025-01-20
   > **New Top Pick**: Product Y now recommended for users prioritizing video quality
   > **Previous Top Pick** (Product A) remains best overall value
   ```

5. **Increment version** (1.0 → 1.1 for additions, 1.0 → 2.0 if top recommendation changes)

**Effort**: ~30-40 minutes

---

#### Mode 4: Monitoring Update

**Use Case**: Automated update triggered by monitoring alert.

**When to Use**:
- Price tracking alert: "Price dropped >25%"
- Product recall or safety alert
- New major study published
- Regulatory change affecting recommendations

**Workflow**:
1. **Receive alert trigger**:
   ```
   Google Alert: "Barista Express recall 2025"
   CamelCamelCamel: "Barista Express price: $749 → $562 (-25%)"
   ```

2. **Read research note** monitoring plan:
   ```yaml
   monitoring_plan:
     alert_triggers:
       - "Price drops below $600" ← TRIGGERED
       - "Product recall or safety alert"
   ```

3. **Verify trigger** condition:
   - Confirm price actually dropped (check source)
   - Verify recall is legitimate (FDA, CPSC)
   - Assess impact severity

4. **Update affected sections only**:
   ```markdown
   ## Price Analysis

   ### Current Pricing (Updated 2025-01-20)

   ⚠️ **Price Drop Alert**: Barista Express now $562 (was $749, -25%)

   | Retailer | Price | Notes |
   |----------|-------|-------|
   | Amazon | $562 | **Best Deal** (was $749) |
   | Direct | $749 | No sale |

   **Impact on Recommendation**: Now competitive with alternatives, cost-per-use improved significantly
   ```

5. **Add changelog entry**:
   ```yaml
   research_version: 1.2
   changelog:
     - 1.0: Initial research (2024-06-15)
     - 1.1: Updated models (2025-01-15)
     - 1.2: Price drop alert integrated (2025-01-20) ← NEW
   ```

6. **Notify user** (if monitoring is automated):
   - Send alert: "Barista Express research updated - price dropped to $562"
   - Link to updated section

**Effort**: ~5-10 minutes for simple updates (pricing), ~30 minutes for complex updates (recalls requiring safety analysis)

---

#### Mode Selection Guide

| Research Need | Mode | Effort | When to Use Instead of Full Research |
|---------------|------|--------|--------------------------------------|
| Refresh outdated note | Expand Existing | 30-45 min | Research >6 months old, <50% needs updating |
| Answer one question | Quick Follow-Up | 10-15 min | Single missing datapoint, minor addition |
| Add competitor | Comparative Addition | 30-40 min | Comparison framework already established |
| Respond to alert | Monitoring Update | 5-30 min | Specific trigger event, narrow scope |

**When to Do Full Re-Research Instead**:
- >50% of existing research is outdated
- Fundamental assumptions have changed (e.g., new technology paradigm)
- Original research was low confidence (⭐) across the board
- Topic scope has expanded significantly

---

#### Incremental Research Best Practices

**Version Management**:
- **Minor updates** (pricing, small additions): 1.0 → 1.1
- **Moderate updates** (new competitors, expanded sections): 1.0 → 1.5
- **Major updates** (recommendation changes, significant new data): 1.0 → 2.0

**Confidence Recalculation**:
- After incremental research, recalculate confidence:
  - Added high-quality sources → +5 to +10% confidence
  - Filled knowledge gaps → +10 to +15% confidence
  - Found contradictory evidence → -10 to -15% confidence

**Documentation**:
- Always note what changed and why
- Timestamp updates clearly
- Preserve historical context (use strikethrough for old info, not deletion)

**Example Update Notation**:
```markdown
## Recommendation

~~Best Overall: Product A ($150)~~ **Updated 2025-01-20**

**Best Overall**: Product Y ($180)
- Reason for change: Better video quality (9/10 vs 8/10), improved reliability data
- Product A remains "Best Value" at lower price point
```

---
