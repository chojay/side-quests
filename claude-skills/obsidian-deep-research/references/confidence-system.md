# Confidence Rating System (Multi-Dimensional)

Part of the `obsidian-deep-research` skill (Implementation Guidelines). Read this file
during Phases 5-10: confidence levels and calculation formula, uncertainty
quantification, confidence decay and trend tracking, cross-cultural validation,
knowledge graph expansion, research versioning, and quality metrics. For source
credibility base scores, see `research-methodologies.md` (canonical tables).

### Confidence Rating System (Multi-Dimensional)

**Overview**: Instead of a single overall confidence score, report confidence across multiple dimensions to provide nuanced uncertainty quantification.

#### Overall Confidence Levels

- ⭐⭐⭐ **High Confidence (0.80-1.00)**: Multiple authoritative sources agree, large sample sizes, recent data
- ⭐⭐ **Moderate Confidence (0.60-0.79)**: Some agreement, reasonable samples, minor contradictions explained
- ⭐ **Low Confidence (0.40-0.59)**: Limited sources, small samples, significant contradictions, dated information

#### Multi-Dimensional Confidence Breakdown

For major research findings, report confidence across these dimensions:

**1. Source Quality (Credibility)**
- **Score**: Weighted average of source credibility scores
- **Factors**:
  - Percentage of high-credibility sources (>0.85)
  - Mix of expert vs. community sources
  - Peer-reviewed vs. anecdotal evidence
- **Example**: ⭐⭐⭐ (0.90) - "15 high-credibility sources, mix of expert + peer-reviewed"

**2. Source Diversity (Geographic & Type)**
- **Score**: Based on number of regions and source types
- **Calculation**:
  - 3+ regions + 4+ source types = ⭐⭐⭐ (0.85-0.95)
  - 2 regions + 3 source types = ⭐⭐ (0.70-0.84)
  - 1 region + 1-2 source types = ⭐ (0.50-0.69)
- **Example**: ⭐⭐⭐ (0.85) - "3 regions (US/Korea/Japan), 5 source types"

**3. Temporal Relevance (Recency)**
- **Score**: Weighted by publication date
- **Calculation**:
  - >80% sources <1 year old = ⭐⭐⭐ (0.90+)
  - 60-80% sources <2 years old = ⭐⭐ (0.75-0.89)
  - <60% sources <2 years old = ⭐ (0.50-0.74)
- **Decay factor**: Multiply by 1.0 (<1yr), 0.9 (1-2yr), 0.7 (2-5yr), 0.5 (>5yr)
- **Example**: ⭐⭐ (0.75) - "60% <1yr old, 40% 1-2yr old"

**4. Sample Size (Statistical Power)**
- **Score**: Based on aggregate sample across all sources
- **Thresholds** (product research):
  - >1000 reviews/users = ⭐⭐⭐ (0.90+)
  - 100-1000 = ⭐⭐ (0.70-0.89)
  - <100 = ⭐ (0.50-0.69)
- **Thresholds** (academic research):
  - Meta-analysis n>1000 = ⭐⭐⭐
  - RCT n>100 per arm = ⭐⭐⭐
  - Observational n>500 = ⭐⭐
- **Example**: ⭐⭐⭐ (0.95) - "n=2,340 user reviews + 8 expert reviews"

**5. Consistency (Consensus Strength)**
- **Score**: Percentage agreement on key findings
- **Calculation**:
  - >80% consensus = ⭐⭐⭐ (0.85-0.95)
  - 60-80% consensus = ⭐⭐ (0.70-0.84)
  - <60% consensus = ⭐ (0.50-0.69)
- **Example**: ⭐⭐ (0.70) - "75% consensus, 25% contradictory"

**6. Reproducibility (Replication)**
- **Score**: How many independent sources replicated findings
- **Calculation**:
  - Finding replicated in 4+ independent sources = ⭐⭐⭐ (0.90)
  - 2-3 independent sources = ⭐⭐ (0.75)
  - Single source only = ⭐ (0.50)
- **Example**: ⭐⭐⭐ (0.88) - "Findings replicated across 4 sources"

#### Confidence Calculation Formula

**Weighted Overall Confidence**:
```
Overall = (Source Quality × 0.25) +
          (Source Diversity × 0.15) +
          (Temporal Relevance × 0.10) +
          (Sample Size × 0.20) +
          (Consistency × 0.20) +
          (Reproducibility × 0.10)
```

**Example Calculation**:
```
Source Quality: 0.90 × 0.25 = 0.225
Source Diversity: 0.85 × 0.15 = 0.128
Temporal Relevance: 0.75 × 0.10 = 0.075
Sample Size: 0.95 × 0.20 = 0.190
Consistency: 0.70 × 0.20 = 0.140
Reproducibility: 0.88 × 0.10 = 0.088
---
Overall Confidence: 0.846 ≈ 0.85 (⭐⭐⭐)
```

#### Uncertainty Quantification

**Known Unknowns** (factors reducing confidence):
```markdown
## Known Unknowns

- ❓ **Long-term durability**: Limited >2 year user reports (reduces confidence by 10%)
- ❓ **Regional availability**: Not confirmed for EU market (limits generalizability)
- ❓ **Future compatibility**: Unclear if firmware updates will maintain support
- ❓ **Edge cases**: Limited data on use with {specific scenario}
```

**Assumption Dependencies**:
```markdown
> [!warning] Key Assumptions
> Confidence is contingent on:
> - Manufacturer continues product support for >3 years
> - Current pricing remains stable within ±15%
> - HomeKit architecture remains backward compatible
> - No major security vulnerabilities discovered
```

#### Confidence Intervals for Quantitative Claims

For numerical claims, provide confidence intervals:

| Metric | Point Estimate | 95% CI | Certainty |
|--------|----------------|--------|-----------|
| User Satisfaction | 4.2/5.0 | [4.0, 4.4] | High |
| Failure Rate | 8% | [5%, 12%] | Moderate |
| Price Premium | +$35 | [+$20, +$50] | Moderate |
| Battery Life | 18 months | [12, 24] | Low |

#### Temporal Validity & Confidence Decay

**Confidence Decay Model**:
```markdown
## Confidence Over Time

Current confidence: 0.85 (as of 2025-01-15)

Projected confidence decay:
- +3 months (2025-04-15): 0.83 (minor drift - pricing changes)
- +6 months (2025-07-15): 0.78 (moderate drift - new models likely)
- +12 months (2026-01-15): 0.65 (major drift - market evolution)
- +24 months (2027-01-15): 0.40 (research likely obsolete)

**Recommendation**: Review research in 6 months
**Triggers for earlier review**: Product recall, major competitor release, >25% price change
```

**Decay Factors by Domain**:
- **Technology products**: 10-15% decay per 6 months (rapid evolution)
- **Academic research**: 5-10% decay per year (slower evolution)
- **Medical guidelines**: 10% decay per 2 years (periodic updates)
- **Fundamental concepts**: 2-5% decay per 5 years (very stable)

#### Confidence Trend Tracking

Track how confidence evolved during research:

```markdown
## Confidence Evolution

**Phase 4** (After initial gathering): ⭐⭐ (0.65)
- Limited sources (only 8 found)
- Geographic diversity low (US only)

**Phase 6** (After triangulation): ⭐⭐⭐ (0.82)
- Consensus emerged (78% agreement)
- Added Asian sources (18 total)

**Phase 5.5** (After adversarial analysis): ⭐⭐ (0.75)
- Discovered reliability issues (15% failure rate)
- Found publication bias in manufacturer studies

**Final** (After synthesis): ⭐⭐ (0.75)
- Confidence stabilized
- Caveats documented
```

#### Reporting Format in Research Notes

**Standard Confidence Report**:
```markdown
## Confidence Analysis

### Overall Confidence: ⭐⭐⭐ (0.85)

**Confidence Breakdown**:

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Source Quality | ⭐⭐⭐ (0.90) | 15 high-credibility sources, expert + peer-reviewed mix |
| Source Diversity | ⭐⭐⭐ (0.85) | 3 regions, 5 source types |
| Temporal Relevance | ⭐⭐ (0.75) | 60% <1yr, 40% 1-2yr old |
| Sample Size | ⭐⭐⭐ (0.95) | n=2,340 reviews + 8 expert reviews |
| Consistency | ⭐⭐ (0.70) | 75% consensus, 25% contradictory |
| Reproducibility | ⭐⭐⭐ (0.88) | Replicated across 4 independent sources |

**Known Unknowns**:
- ❓ Long-term durability: Limited >2yr reports (-10% confidence)
- ❓ Regional availability: Not confirmed for EU market
- ❓ Future compatibility: Firmware update support unclear

**Confidence Decay**:
- Current: 0.85 (2025-01-15)
- +6 months: 0.78 (moderate drift expected)
- Recommendation: Review in 6 months
```

### Cross-Cultural Validation

For product research, always check:
1. **Western Sources**:
   - Reddit communities (multiple relevant subreddits)
   - Amazon reviews (verified purchases)
   - Wirecutter, Consumer Reports
   - YouTube reviews (subscriber count >10k)

2. **Asian Sources**:
   - Naver blogs (Korean)
   - Coupang reviews (Korean)
   - Rakuten (Japanese)
   - Regional pricing and availability

### Knowledge Graph Expansion

After creating new research notes:
1. Search for all mentions of key entities in existing notes
2. Add wiki links pointing to the new research
3. Update related MOCs with new entry
4. Create or update index notes for the domain
5. Generate "See Also" sections with related research

### Research Versioning

Maintain research versions with:
```yaml
research_version: 1.0
changelog:
  - 1.0: Initial research (YYYY-MM-DD)
  - 1.1: Updated pricing (YYYY-MM-DD)
  - 2.0: Major revision with new sources (YYYY-MM-DD)
```

### Uncertainty Documentation

Explicitly document:
- Known limitations of the research
- Conflicting evidence and interpretations
- Temporal validity (when findings might expire)
- Geographic or demographic limitations
- Sample size constraints

### Quality Metrics

Track research quality with:
- Source count (aim for >10 diverse sources)
- Geographic diversity score (regions represented)
- Temporal coverage (how recent are sources)
- Authority distribution (expert vs community)
- Contradiction resolution rate
- Knowledge graph connectivity (links created)

