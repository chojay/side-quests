# Output Templates

Part of the `obsidian-deep-research` skill. Read this file during Phase 10 when
assembling the final research note.

## Contents

- Product Research Template (Comprehensive)
- Academic Research Template (Comprehensive)
- Interactive Decision Frameworks (Mermaid decision trees, risk assessment heatmap,
  feature priority matrix, progressive disclosure recommendation flow, comparison
  scenario tables, visual confidence indicators)
- Visual Data Presentation (ASCII price charts, source credibility distribution,
  review sentiment analysis, confidence decay model, cross-cultural comparison
  charts, comparison matrix heatmaps)

## Output Templates

### Product Research Template (Comprehensive)

```markdown
# [[Product Name]] - Deep Research

> [!summary] Quick Verdict
> **Best For**: {ideal user profile with specific use cases}
> **Avoid If**: {deal-breakers and constraints}
> **Overall Confidence**: ⭐⭐⭐ (0.85)
> **Last Updated**: YYYY-MM-DD
> **Research Version**: 1.0

---

## TL;DR - Executive Summary

| Aspect | Finding | Confidence |
|--------|---------|------------|
| **Overall Quality** | {1-2 sentence summary of quality/performance} | ⭐⭐⭐ |
| **Value for Money** | {Price/performance ratio assessment} | ⭐⭐ |
| **Reliability** | {Failure rates, MTBF estimates} | ⭐⭐⭐ |
| **User Satisfaction** | {Average rating, recommend percentage} | ⭐⭐ |
| **Best Alternative** | [[Alternative Product]] - {key differentiator} | ⭐⭐⭐ |

**Bottom Line**: {2-3 sentence decisive recommendation with confidence caveats}

---

## Cross-Cultural Consensus Analysis

### Western Sources (n={count})

**Primary Sources**: Reddit (r/[subreddit1], r/[subreddit2]), Wirecutter, Consumer Reports, YouTube ({channel names})

**Key Findings**:
- {Finding 1} (mentioned in {X}% of sources, n={count})
- {Finding 2} (mentioned in {Y}% of sources, n={count})
- {Finding 3} (mentioned in {Z}% of sources, n={count})

**Common Praise** (>50% of sources):
- ✅ {Strength 1} - {elaboration with examples}
- ✅ {Strength 2} - {elaboration with examples}
- ✅ {Strength 3} - {elaboration with examples}

**Common Complaints** (>20% of sources):
- ⚠️ {Weakness 1} - {elaboration with workarounds}
- ⚠️ {Weakness 2} - {elaboration with severity}

### Asian Sources (n={count})

**Primary Sources**: Naver blogs, Coupang reviews ({avg rating}★, {review count} reviews), Rakuten

**Key Findings**:
- {Finding 1 specific to Asian markets}
- {Finding 2 specific to Asian markets}

**Regional Differences**:
- {Cultural preference difference}
- {Feature availability difference}
- {Pricing difference}: ₩{KRW price} (≈ ${USD equivalent})

**Convergence vs. Divergence**:
- **Consensus**: {What Western + Asian sources agree on}
- **Divergence**: {Where opinions differ by region and why}

---

## Specifications & Features

| Feature Category | Specification | Competitive Ranking | Notes |
|------------------|---------------|---------------------|-------|
| {Feature 1} | {Value} | #{rank} of {total} | {why it matters} |
| {Feature 2} | {Value} | #{rank} of {total} | {comparison context} |
| {Feature 3} | {Value} | #{rank} of {total} | {standout aspect} |
| {Feature 4} | {Value} | Best in class ⭐ | {key differentiator} |

**Standout Features**:
- {Feature} - {Why this matters and real-world impact}

**Missing Features** (vs. competition):
- {Feature} - {Impact of absence}

---

## Price Analysis

### Current Pricing (as of YYYY-MM-DD)

| Retailer | Price | Availability | Shipping | Notes |
|----------|-------|--------------|----------|-------|
| Amazon US | ${X} | In stock | Prime 2-day | {coupon/deal info} |
| Coupang KR | ₩{X} (~${Y}) | In stock | Rocket delivery | {regional availability} |
| Best Buy | ${X} | Online/In-store | {shipping} | Price match available |
| Direct | ${X} | {availability} | {shipping} | {warranty benefits} |

**Best Current Deal**: {Retailer} at ${X} with {offer details}

### Historical Price Trends (6-12 months)

**Price History**:
```
$250 |                    *
     |                 *
$225 |              *
     |           *
$200 |        *
     |     *
$175 |  *                    * ← Current ($179)
     |_________________________________
     Jul  Aug  Sep  Oct  Nov  Dec  Jan
```

- **Average Price**: ${X} (current vs. avg: {comparison})
- **Lowest Price Ever**: ${X} on {date} ({event, e.g., "Prime Day"})
- **Price Volatility**: {Low/Medium/High} - {explanation}
- **Typical Sales Events**: {Black Friday -30%, Prime Day -25%, etc.}

**Best Time to Buy**: {Recommendation with rationale, e.g., "Wait for August back-to-school sales for 20-25% off"}

### Value Assessment & Total Cost of Ownership

**Purchase Analysis**:
```
Base Price: ${X}
Essential Accessories: ${Y} ({list items})
Optional Add-ons: ${Z} ({list items})
---
Initial Investment: ${total}

Expected Lifespan: {X} years
Estimated Uses: {Y} per {timeframe}
Cost per Use: ${Z}

Resale Value (2 years): ${X} (based on eBay sold listings)
---
Total Cost of Ownership (3 years): ${TCO}
```

**Value Tier**: {Budget/Mid-range/Premium} - {justification}

---

## Comparative Analysis

### Direct Competitors

| Product | Price | Key Advantage | Key Disadvantage | Overall |
|---------|-------|---------------|------------------|---------|
| **{This Product}** | ${X} | {standout strength} | {main weakness} | ⭐⭐⭐⭐ |
| {Competitor 1} | ${X} | {their strength} | {their weakness} | ⭐⭐⭐ |
| {Competitor 2} | ${X} | {their strength} | {their weakness} | ⭐⭐⭐⭐ |
| {Competitor 3} | ${X} | {their strength} | {their weakness} | ⭐⭐ |

### Decision Matrix

**If you prioritize:**
- **Best Overall**: {Product A} - {balanced recommendation}
- **Best Value**: {Product B} - {lowest cost-per-use}
- **Best Premium**: {Product C} - {highest quality, price secondary}
- **Best for {Use Case 1}**: {Product D} - {specialized strength}
- **Best for {Use Case 2}**: {Product E} - {specialized strength}

**Head-to-Head**: {This Product} vs. {Main Competitor}
- **{This Product} wins**: {categories where it's superior}
- **{Competitor} wins**: {categories where competitor is superior}
- **Verdict**: Choose {This Product} if {condition}, choose {Competitor} if {condition}

---

## Failure Mode & Reliability Analysis

### Common Issues (from 1-2 star reviews, n={count})

| Issue | Frequency | Severity | Workaround Available? |
|-------|-----------|----------|-----------------------|
| {Issue 1} | {X}% of users | 🔴 Critical | {Yes/No} - {details} |
| {Issue 2} | {Y}% of users | 🟡 Moderate | {Yes/No} - {details} |
| {Issue 3} | {Z}% of users | 🟢 Minor | {Yes/No} - {details} |

**Mean Time Between Failures**: {estimate based on review data, e.g., "~18 months for motor, ~3 years for electronics"}

**Warranty Analysis**:
- **Standard Warranty**: {duration and coverage}
- **Extended Warranty**: {cost and value assessment}
- **Warranty Claim Success Rate**: {X}% based on user reports
- **Manufacturer Responsiveness**: {assessment from community feedback}

**Long-Term Reliability** (from multi-year reviews):
- {Insight from "still working after X years" reports}
- {Common age-related degradation patterns}

**Deal-Breaker Issues** (affecting >20% of users):
- {Critical issue if any, or "None identified"}

---

## Use Case Recommendations

| Use Case | Recommended? | Confidence | Rationale |
|----------|--------------|------------|-----------|
| {Use Case 1} | ✅ Highly Recommended | ⭐⭐⭐ | {why it excels for this} |
| {Use Case 2} | ⚠️ Conditional | ⭐⭐ | {conditions that must be met} |
| {Use Case 3} | ⚠️ Possible | ⭐⭐ | {works but not ideal, alternatives} |
| {Use Case 4} | ❌ Not Recommended | ⭐⭐⭐ | {why it fails for this case} |

**Ideal User Profile**:
- {Characteristic 1} (e.g., "Lives in apartment with WiFi coverage <1500 sq ft")
- {Characteristic 2} (e.g., "Values ease of use over advanced features")
- {Characteristic 3} (e.g., "Budget-conscious but willing to pay for quality")

**Poor Fit For**:
- {Anti-profile 1} (e.g., "Large homes >2500 sq ft")
- {Anti-profile 2} (e.g., "Power users needing advanced customization")

---

## Research Methodology & Confidence

**Sources Consulted**: {total count}

**Source Breakdown**:
- Western expert reviews: {count} (Wirecutter, Consumer Reports, CNET)
- Western community sources: {count} (Reddit, Amazon reviews, forums)
- Asian regional sources: {count} (Naver, Coupang, Rakuten)
- YouTube video reviews: {count} (total views: {X}M+)
- Price tracking databases: {count} (historical data: {months} months)
- Academic/technical sources: {count} (patents, tear downs, specs)

**Confidence Calculation**:

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Source Quality | ⭐⭐⭐ (0.90) | {X} high-credibility sources, expert + peer-reviewed mix |
| Source Diversity | ⭐⭐⭐ (0.85) | {X} regions, {Y} source types |
| Temporal Relevance | ⭐⭐ (0.75) | {X}% <1yr old, {Y}% 1-2yr old |
| Sample Size | ⭐⭐⭐ (0.95) | Aggregate n={X} user reviews + {Y} expert reviews |
| Consensus Strength | ⭐⭐ (0.70) | {X}% agreement on key findings |

**Overall Research Quality Score**: {0.XX} ({methodology calculation})

**Research Limitations**:
- {Limitation 1, e.g., "Limited long-term reliability data (product <1 year old)"}
- {Limitation 2, e.g., "No direct testing performed, reliant on secondary sources"}
- {Limitation 3, e.g., "Regional pricing data limited to US/Korea"}

**Known Unknowns**:
- ❓ {Unresolved question 1}
- ❓ {Unresolved question 2}

---

## Detailed Source Citations

### High Credibility Sources (0.85-0.95)

1. **{Title}** - {Author/Source} ({Date})
   - **URL**: {link} ([Web Archive](archive-link))
   - **Key Findings**: {bullet points}
   - **Credibility Score**: {0.XX}
   - **Sample/Methodology**: {n=X, methodology note}

### Community Consensus Sources (0.70-0.80)

{Similar format for community sources}

### Regional Sources (Asian Markets)

{Similar format for Naver, Coupang, etc.}

---

## Monitoring & Update Plan

**Research Lifespan**: {Stable - review in 6-12 months}

**Update Triggers**:
```yaml
monitoring_plan:
  review_schedule: "every 6 months"
  alert_triggers:
    - "Product recall or safety alert"
    - "Price drops below ${threshold}"
    - "New model released"
    - "Major firmware/software update"
    - "Competitor landscape shift (new product rated >4.5★)"

  monitoring_sources:
    - "Google Alerts: '{product name} recall', '{product name} problems'"
    - "CamelCamelCamel: Price alert for ${threshold}"
    - "Reddit saved search: r/{subreddit} '{product}'"
```

**Recommended Review Date**: {YYYY-MM-DD}

---

## Version History

```yaml
research_version: 1.0
changelog:
  - version: 1.0
    date: YYYY-MM-DD
    changes: "Initial comprehensive research"
    sources_count: {X}
    confidence: 0.XX
```

---

## Related Research

**Related Products**:
- [[Alternative Product 1]] - {relationship}
- [[Alternative Product 2]] - {relationship}

**Related Guides**:
- [[Product Category Buying Guide]]
- [[Brand Name Analysis]]
- [[Use Case Setup Guide]]

**MOC**: [[{Category} MOC]]
```

### Academic Research Template (Comprehensive)

```markdown
# [[Research Topic]] - Systematic Review

> [!abstract] Research Summary
> **Conclusion**: {1-2 sentence main finding}
> **Evidence Level**: {I-V using Oxford CEBM hierarchy}
> **Overall Confidence**: ⭐⭐⭐ (0.85)
> **Last Updated**: YYYY-MM-DD
> **Research Version**: 1.0

---

## Key Findings at a Glance

| Research Question | Answer | Evidence Level | Confidence |
|------------------|--------|----------------|------------|
| {Q1 from PICO} | {A1 summary} | Level {I-V} | ⭐⭐⭐ |
| {Q2 from PICO} | {A2 summary} | Level {I-V} | ⭐⭐ |
| {Q3 from PICO} | {A3 summary} | Level {I-V} | ⭐⭐ |

**Clinical/Practical Implications**: {2-3 sentence actionable summary}

---

## Systematic Review Methodology

### Research Question (PICO Format)

**For Medical/Clinical Research**:
- **Population**: {clearly defined population}
- **Intervention**: {specific intervention/exposure}
- **Comparison**: {control or comparator}
- **Outcome**: {primary and secondary outcomes}

**For Non-Medical Research**:
- **Research Aim**: {clear statement of purpose}
- **Scope**: {boundaries and limitations}
- **Key Variables**: {independent and dependent variables}

### Search Strategy

**Databases Searched**:
- PubMed/MEDLINE ({date range})
- Google Scholar ({date range})
- Cochrane Library ({date range})
- {Domain-specific databases, e.g., arXiv, SSRN, IEEE Xplore}
- Grey literature: Preprints, dissertations, conference proceedings

**Search Keywords**:
- Primary terms: {term1}, {term2}, {term3}
- Boolean operators: {example search string}
- MeSH terms (if medical): {MeSH terms used}

**Date Range**: {start date} to {end date}

### Inclusion & Exclusion Criteria

**Inclusion Criteria**:
- {Criterion 1, e.g., "RCTs with n>50"}
- {Criterion 2, e.g., "Published in peer-reviewed journals"}
- {Criterion 3, e.g., "English language or translated"}
- {Criterion 4, e.g., "Human subjects (if medical)"}

**Exclusion Criteria**:
- {Criterion 1, e.g., "Case reports and case series"}
- {Criterion 2, e.g., "Conflicts of interest not disclosed"}
- {Criterion 3, e.g., "Insufficient statistical data"}

### Search Results & Selection

**PRISMA Flow**:
```
Papers Identified: {n} (from all databases)
  ↓
Papers Screened: {n} (after duplicates removed)
  ↓ (excluded: {n} - reasons: title/abstract irrelevant)
Full-Text Assessed: {n}
  ↓ (excluded: {n} - reasons: {list})
Papers Included: {n}
```

**Quality of Included Studies**:
- High quality: {n} studies
- Moderate quality: {n} studies
- Low quality: {n} studies (flagged for sensitivity analysis)

---

## Evidence Hierarchy

### Level I Evidence (Systematic Reviews & Meta-Analyses)

**Study 1**: {Authors et al. (Year)} - {Title}
- **Citation**: {Full citation}
- **URL**: {link} ([Archive](archive-link))
- **Studies Included**: n={count} studies
- **Total Participants**: N={total across all studies}
- **Effect Size**: {Cohen's d / OR / RR / MD} = {value}, 95% CI [{lower}, {upper}]
- **Heterogeneity**: I² = {value}% ({low/moderate/high})
- **Publication Bias**: {Egger's test p-value, funnel plot assessment}
- **Conclusion**: {finding with confidence}
- **Limitations**: {key limitations}
- **Credibility Score**: 0.95

### Level II Evidence (Randomized Controlled Trials)

**Study 1**: {Authors et al. (Year)} - {Title}
- **Citation**: {Full citation}
- **Sample Size**: n={intervention}, n={control}
- **Study Design**: {e.g., "Double-blind RCT"}
- **Primary Outcome**: {outcome and measurement}
- **Results**: {intervention group} vs. {control group}, p={value}
- **Effect Size**: {standardized effect} with 95% CI
- **Risk of Bias**: {low/moderate/high} - {assessment basis}
- **Funding Source**: {independent/industry/mixed}
- **Credibility Score**: 0.90

{Repeat for additional Level II studies}

### Level III Evidence (Cohort Studies)

{Similar structure for observational studies}

### Level IV Evidence (Case-Control Studies)

{Similar structure}

### Level V Evidence (Expert Opinion, Case Series)

{Similar structure}

---

## Meta-Analytic Findings

**Primary Outcome**: {outcome name}

### Effect Size Summary

| Outcome Measure | Studies (n) | Participants (N) | Effect Size | 95% CI | p-value | Heterogeneity (I²) |
|-----------------|-------------|------------------|-------------|--------|---------|-------------------|
| {Outcome 1} | {n} | {N} | {ES} | [{l}, {u}] | {p} | {I²}% |
| {Outcome 2} | {n} | {N} | {ES} | [{l}, {u}] | {p} | {I²}% |
| {Outcome 3} | {n} | {N} | {ES} | [{l}, {u}] | {p} | {I²}% |

**Forest Plot Verbal Description**: {Description of effect direction, magnitude, and consistency across studies}

**Subgroup Analyses**:
- **By {variable}**: {finding, e.g., "Effect larger in children (d=0.8) vs adults (d=0.4)"}
- **By {variable}**: {finding}

**Sensitivity Analysis**:
- Excluding low-quality studies: Effect {increases/decreases/unchanged} to {value}
- Excluding industry-funded studies: Effect {comparison}

---

## Synthesis of Findings

### Theme 1: {Major Finding Category}

**Consensus ({X}% of studies agree)**:
- {Finding 1 with supporting evidence count}
- {Finding 2 with supporting evidence count}

**Supporting Evidence**:
- {Study 1}: {brief finding} (n={X}, p={value})
- {Study 2}: {brief finding} (n={X}, p={value})

**Confidence**: ⭐⭐⭐ ({rationale})

### Theme 2: {Major Finding Category}

{Similar structure}

### Theme 3: {Major Finding Category}

{Similar structure}

---

## Critical Appraisal

### Strengths of Evidence Base

1. **Methodological Rigor**: {X}% of studies were RCTs with low risk of bias
2. **Sample Size**: Aggregate N={total} provides adequate statistical power
3. **Consistency**: Low heterogeneity (I²<{value}%) suggests consistent findings
4. **Replication**: Key findings replicated across {n} independent research groups
5. **Recent**: {X}% of evidence published within last {n} years

### Limitations & Potential Biases

**Publication Bias**:
- **Assessment**: {Egger's test p={value}, Funnel plot {symmetric/asymmetric}}
- **Impact**: {Likely overestimate/underestimate effect by ~X%}

**Selection Bias**:
- {Assessment of inclusion/exclusion criteria impact}
- {Generalizability concerns}

**Measurement Bias**:
- {Concerns about outcome measurement validity}
- {Heterogeneity in measurement methods}

**Attrition Bias**:
- Average dropout rate: {X}%
- {ITT analysis vs. per-protocol impact}

**Funding Bias**:
- {X}% industry-funded studies
- Effect size comparison: Industry {higher/lower/similar} by {amount}

**Heterogeneity Explanation**:
- I²={value}% suggests {low/moderate/high} heterogeneity
- Likely sources: {study design differences, population differences, intervention variations}

### Contradictory Findings

| Finding | Supporting Studies | Contradicting Studies | Resolution Attempt |
|---------|-------------------|----------------------|-------------------|
| {Finding} | [{n} studies] | [{n} studies] | {Explanation of divergence, e.g., "Contradictions explained by dosage differences"} |

**Unresolved Contradictions**:
- {Contradiction 1} - {Confidence in either direction: LOW}
- {Contradiction 2} - {Further research needed}

---

## Research Gaps & Future Directions

### Identified Knowledge Gaps

1. **Gap 1**: {description}
   - **Why it matters**: {clinical/practical significance}
   - **Suggested research**: {specific study design or question}

2. **Gap 2**: {description}
   - **Why it matters**: {significance}
   - **Suggested research**: {recommendation}

### Methodological Improvements Needed

- {Weakness in current research, e.g., "Longer follow-up periods needed (current max: X months)"}
- {Methodological improvement, e.g., "Standardized outcome measures required"}

### Emerging Research Directions

- {Recent development not yet in systematic reviews}
- {Novel interventions in early trials}

---

## Clinical/Practical Implications

### Recommendations (with Strength of Evidence)

**Strong Recommendations** (High confidence, Level I-II evidence):
1. {Recommendation 1} - Evidence Level: {I/II}, Confidence: ⭐⭐⭐
2. {Recommendation 2} - Evidence Level: {I/II}, Confidence: ⭐⭐⭐

**Conditional Recommendations** (Moderate confidence, Level II-III evidence):
1. {Recommendation 1} - Evidence Level: {II/III}, Confidence: ⭐⭐
   - **Conditions**: {when this applies}

**Not Recommended** (Insufficient evidence or evidence of harm):
1. {Action} - **Reason**: {insufficient evidence / evidence of harm}

### Implementation Considerations

**Facilitators**:
- {Factor that supports implementation}

**Barriers**:
- {Factor that impedes implementation}

**Patient/Population Applicability**:
- **Generalizable to**: {populations}
- **May not apply to**: {excluded populations}

---

## Detailed References

### Systematic Reviews & Meta-Analyses (Level I)

1. **{Authors et al. (Year)}**. {Title}. *{Journal}*, {Volume}({Issue}), {Pages}. DOI: {doi}
   - URL: {link} ([Archive](archive))
   - Key Finding: {summary}
   - Credibility: 0.95

### Randomized Controlled Trials (Level II)

{Similar format for RCTs}

### Observational Studies (Level III-IV)

{Similar format}

### Grey Literature & Preprints

{Similar format with caveat about peer-review status}

---

## Research Metadata & Quality Metrics

**Total Evidence Base**:
- Systematic reviews: {n}
- RCTs: {n}
- Cohort studies: {n}
- Other: {n}
- **Total papers reviewed**: {N}

**Evidence Quality Distribution**:
```
High Quality    ████████████████░░░░ {n} studies ({X}%)
Moderate Quality████████░░░░░░░░░░░░ {n} studies ({Y}%)
Low Quality     ███░░░░░░░░░░░░░░░░░ {n} studies ({Z}%)
```

**Geographic Distribution**:
- North America: {n} studies
- Europe: {n} studies
- Asia: {n} studies
- Other: {n} studies

**Temporal Distribution**:
- Last 2 years: {n} studies ({X}%)
- 2-5 years: {n} studies ({Y}%)
- >5 years: {n} studies ({Z}%)

**Funding Sources**:
- Independent/Government: {X}%
- Industry: {Y}%
- Mixed: {Z}%

**Overall Confidence Assessment**:

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Study Quality | ⭐⭐⭐ (0.90) | Majority high-quality RCTs |
| Consistency | ⭐⭐ (0.75) | Moderate heterogeneity, mostly explained |
| Directness | ⭐⭐⭐ (0.85) | Studies directly address PICO question |
| Precision | ⭐⭐⭐ (0.90) | Narrow confidence intervals, adequate power |
| Publication Bias | ⭐⭐ (0.70) | Some evidence of bias, adjusted estimates provided |

**Overall GRADE Assessment**: {High/Moderate/Low/Very Low}

---

## Version History

```yaml
research_version: 1.0
changelog:
  - version: 1.0
    date: YYYY-MM-DD
    changes: "Initial systematic review"
    papers_reviewed: {N}
    confidence: 0.XX
```

---

## Related Research

**Related Topics**:
- [[Related Topic 1]]
- [[Related Topic 2]]

**Foundational Papers**:
- [[Seminal Study 1 (Year)]]
- [[Seminal Study 2 (Year)]]

**MOC**: [[Research Domain MOC]]
```

### Interactive Decision Frameworks

Transform static research into interactive decision-making tools using decision trees, risk matrices, and flow charts.

#### Decision Tree (Mermaid Diagrams)

Use Mermaid to create visual decision paths that guide users through choices:

```markdown
## Decision Guide: Choosing the Right {Product Category}

### Interactive Decision Tree

```mermaid
graph TD
    Start[Need {Product}] --> Budget{Budget?}

    Budget -->|<$150| PriorityLow{Top Priority?}
    Budget -->|$150-$250| PriorityMid{Top Priority?}
    Budget -->|>$250| PriorityHigh{Top Priority?}

    PriorityLow -->|Features| ProductA[Product A ⭐⭐⭐<br/>$129 - Best Features/Price]
    PriorityLow -->|Reliability| ProductB[Product B ⭐⭐<br/>$139 - Rock Solid]
    PriorityLow -->|Brand Trust| ProductC[Product C ⭐⭐<br/>$145 - Samsung Ecosystem]

    PriorityMid -->|Video Quality| ProductD[Product D ⭐⭐⭐<br/>$199 - 4K HDR]
    PriorityMid -->|Smart Home| ProductE[Product E ⭐⭐⭐<br/>$179 - HomeKit Native]
    PriorityMid -->|All-Around| ProductF[Product F ⭐⭐⭐<br/>$189 - Best Overall]

    PriorityHigh -->|Premium| ProductG[Product G ⭐⭐⭐<br/>$299 - Top Tier]
    PriorityHigh -->|Future-Proof| ProductH[Product H ⭐⭐⭐<br/>$279 - Matter + Thread]

    style ProductA fill:#90EE90
    style ProductD fill:#90EE90
    style ProductE fill:#90EE90
    style ProductF fill:#87CEEB
    style ProductG fill:#FFD700
    style ProductH fill:#FFD700
```
```

**How to Use This Tree**:
1. Start at top with your budget constraint
2. Identify your top priority (features vs. reliability vs. ecosystem)
3. Follow the path to recommended product
4. Green = Best value, Blue = Best overall, Gold = Premium tier

#### Risk Assessment Heatmap

Visualize risks across multiple products/options using color-coded matrices:

```markdown
## Risk Assessment Matrix

Compare products across key risk dimensions:

| Risk Factor | Product A | Product B | Product C | Product D |
|-------------|-----------|-----------|-----------|-----------|
| **Compatibility Issues** | 🟢 Low<br/>(Works with all systems) | 🟡 Medium<br/>(HomeKit only) | 🟢 Low<br/>(Matter certified) | 🔴 High<br/>(Proprietary hub) |
| **Reliability** | 🟡 Medium<br/>(5% failure <1yr) | 🟢 Low<br/>(2% failure <1yr) | 🟡 Medium<br/>(6% failure <1yr) | 🔴 High<br/>(12% failure <1yr) |
| **Support Quality** | 🟢 Low<br/>(Excellent 24/7) | 🟢 Low<br/>(Great community) | 🟡 Medium<br/>(Email only) | 🔴 High<br/>(Poor reviews) |
| **Future-Proofing** | 🟡 Medium<br/>(WiFi only) | 🟢 Low<br/>(Matter upgrade path) | 🟢 Low<br/>(Matter native) | 🔴 High<br/>(Discontinued) |
| **Privacy Concerns** | 🟢 Low<br/>(Local storage) | 🟢 Low<br/>(E2E encrypted) | 🟡 Medium<br/>(Cloud optional) | 🔴 High<br/>(Cloud required) |
| **Price Volatility** | 🟡 Medium<br/>(±15% swings) | 🟢 Low<br/>(Stable pricing) | 🟡 Medium<br/>(Sales frequent) | 🟢 Low<br/>(Fixed MSRP) |

**Legend**:
- 🟢 **Low Risk**: Minimal concern, safe choice
- 🟡 **Medium Risk**: Manageable with awareness, consider mitigations
- 🔴 **High Risk**: Significant concern, avoid unless acceptable trade-off

**Risk Profile Summary**:
- **Product A**: Balanced (3 🟢, 3 🟡) - Best all-around risk profile
- **Product B**: Low-risk (5 🟢, 1 🟡) - Safest choice, premium price justified
- **Product C**: Moderate-risk (3 🟢, 3 🟡) - Good future-proofing, some trade-offs
- **Product D**: High-risk (2 🟢, 1 🟡, 3 🔴) - Avoid unless specific needs justify
```

#### Feature Priority Matrix

Help users make decisions based on weighted priorities:

```markdown
## Feature Priority Decision Matrix

### Step 1: Rank Your Priorities

Assign weights to what matters most (total must = 100%):

| Feature Category | Your Weight | Notes |
|------------------|-------------|-------|
| **Video Quality** | ___% | How important is 4K vs 1080p? Night vision? |
| **Smart Home Integration** | ___% | Do you need HomeKit, Alexa, Google? |
| **Reliability** | ___% | How critical is zero downtime? |
| **Price** | ___% | Is budget a hard constraint? |
| **Privacy/Security** | ___% | Local vs cloud storage importance? |
| **Future-Proofing** | ___% | Matter/Thread support value? |
| **TOTAL** | 100% | |

### Step 2: Calculate Weighted Scores

| Product | Video (×{your %}) | Smart Home (×{your %}) | Reliability (×{your %}) | Price (×{your %}) | Privacy (×{your %}) | Future (×{your %}) | **Weighted Score** |
|---------|----------|------------|------------|-------|---------|--------|------------|
| **A** | 8.5 × ___% = ___ | 9.0 × ___% = ___ | 7.5 × ___% = ___ | 9.0 × ___% = ___ | 8.0 × ___% = ___ | 7.0 × ___% = ___ | **___** |
| **B** | 9.0 × ___% = ___ | 7.0 × ___% = ___ | 9.5 × ___% = ___ | 6.0 × ___% = ___ | 9.5 × ___% = ___ | 6.5 × ___% = ___ | **___** |
| **C** | 7.5 × ___% = ___ | 9.5 × ___% = ___ | 8.0 × ___% = ___ | 8.0 × ___% = ___ | 7.5 × ___% = ___ | 9.5 × ___% = ___ | **___** |

**Example Scenarios**:

**Scenario 1: Budget-Conscious Buyer**
- Price: 40%, Reliability: 30%, Smart Home: 20%, Video: 10%
- **Winner**: Product A (weighted score: 8.7)

**Scenario 2: Privacy-First Tech Enthusiast**
- Privacy: 35%, Future-Proofing: 25%, Smart Home: 20%, Video: 15%, Reliability: 5%
- **Winner**: Product B (weighted score: 8.9)

**Scenario 3: Smart Home Power User**
- Smart Home: 40%, Future-Proofing: 25%, Video: 20%, Privacy: 10%, Reliability: 5%
- **Winner**: Product C (weighted score: 9.1)
```

#### Progressive Disclosure Recommendation Flow

Guide users through narrowing down choices with progressive questions:

```markdown
## Smart Recommendation Flow

Answer these questions to find your ideal product:

### Question 1: What's your budget?
- [ ] **Under $150** → Continue to Q2A
- [ ] **$150-$250** → Continue to Q2B
- [ ] **Over $250** → Continue to Q2C

### Question 2A: Under $150 - What's most important?
- [ ] **Best value overall** → **Recommendation: Product A** (⭐⭐⭐, $129)
- [ ] **Brand trust** → **Recommendation: Product B** (⭐⭐, $139)
- [ ] **Simplest setup** → **Recommendation: Product C** (⭐⭐, $145)

### Question 2B: $150-$250 - What's your priority?
- [ ] **Video quality** → Go to Q3A
- [ ] **Smart home integration** → Go to Q3B
- [ ] **Reliability** → **Recommendation: Product D** (⭐⭐⭐, $199)

### Question 3A: Video Quality Focus
- [ ] **Need 4K HDR** → **Recommendation: Product E** (⭐⭐⭐, $229)
- [ ] **1080p is fine, want wide-angle** → **Recommendation: Product F** (⭐⭐⭐, $179)

### Question 3B: Smart Home Integration
- [ ] **HomeKit user** → **Recommendation: Product G** (⭐⭐⭐, $189)
- [ ] **Alexa/Google** → **Recommendation: Product H** (⭐⭐, $169)
- [ ] **Want all platforms (Matter)** → **Recommendation: Product I** (⭐⭐⭐, $219)
```

#### Comparison Scenario Tables

Provide decision support through realistic use-case scenarios:

```markdown
## Which Product for Your Situation?

| Your Situation | Best Product | Why? | Alternative |
|----------------|--------------|------|-------------|
| **First-time buyer, budget-conscious, needs reliability** | Product A ⭐⭐⭐<br/>($129) | Best value, proven track record, 24/7 support | Product D ($199) if budget allows |
| **Tech-savvy, HomeKit user, privacy-focused** | Product G ⭐⭐⭐<br/>($189) | Native HomeKit, local storage, E2E encryption | Product B ($229) for 4K |
| **Multi-room setup (3+ cameras needed)** | Product C ⭐⭐<br/>($145 each) | Best bulk pricing ($399 for 3), unified app | Product F ($169 each) for better video |
| **Apartment renter, moving in 1-2 years** | Product A ⭐⭐⭐<br/>($129) | Easy setup/takedown, high resale value (70%) | Product E ($179) if want premium features |
| **Smart home power user, future-proofing** | Product I ⭐⭐⭐<br/>($219) | Matter + Thread native, all platforms, 5yr outlook | Product G ($189) if HomeKit-only |
| **Concerned about privacy, no cloud** | Product B ⭐⭐⭐<br/>($229) | 100% local storage, no internet required | Product G ($189) with cloud disabled |
```

#### Visual Confidence Indicators

Show confidence levels visually for each recommendation:

```markdown
## Recommendation Confidence Levels

| Recommendation | Confidence Visualization | Confidence Score | Why This Level? |
|----------------|-------------------------|------------------|-----------------|
| **Product A for budget buyers** | ████████████████████ 95% | ⭐⭐⭐ (0.95) | 47 sources, 2,340 reviews, strong consensus |
| **Product G for HomeKit users** | ██████████████████░░ 90% | ⭐⭐⭐ (0.90) | 32 sources, some HomeKit-specific limitations noted |
| **Product I for future-proofing** | █████████████░░░░░░░ 65% | ⭐⭐ (0.65) | Matter is new (2023), limited long-term data |
| **Avoid Product D** | ████████████████░░░░ 85% | ⭐⭐⭐ (0.85) | Strong consensus on reliability issues, 12% failure rate |

**Confidence Key**:
- **>90% (⭐⭐⭐)**: High confidence, strong evidence, safe to recommend
- **75-89% (⭐⭐⭐)**: Good confidence, some minor uncertainties
- **60-74% (⭐⭐)**: Moderate confidence, notable limitations or gaps
- **<60% (⭐)**: Low confidence, insufficient evidence or contradictions
```

**When to Use Interactive Frameworks**:
- **Decision Trees**: When users need guided decision process with multiple branching paths
- **Risk Heatmaps**: When comparing safety, reliability, or risk factors across options
- **Priority Matrices**: When trade-offs are complex and user priorities vary
- **Progressive Disclosure**: When recommendation space is large (5+ options) and needs filtering
- **Scenario Tables**: When context-dependent recommendations are critical
- **Visual Confidence**: When research has variable confidence across claims

### Visual Data Presentation

Use visual representations to make complex data immediately comprehensible. Prefer ASCII art and text-based visualizations that work in Markdown.

#### ASCII Price Charts

Show pricing trends, historical data, and projections visually:

```markdown
## Price History & Trends

### 12-Month Price History: Product Name

```
$250 |                                    *  ← All-time high (Prime Day fail)
     |                                 *
$225 |                              *
     |                           *
$200 |                        *
     |              *     *
$175 |           *     *
     |        *                                   * ← Current ($179)
$150 |     *                                   *
     |  *                                   *
$125 |__________________________________________________
     Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec Jan

     ▼         ▼                               ▼
   Launch   Prime Day                    Black Friday
   ($149)   (missed, $249)                   ($159)
```

**Key Insights**:
- **Average Price**: $187 (current is 4% below average - **GOOD TIME TO BUY**)
- **Lowest Ever**: $149 (launch promo, unlikely to repeat)
- **Typical Sale Price**: $159 (Black Friday, expect again Nov 2025)
- **Volatility**: Medium (±18% range over 12 months)
- **Trend**: Gradual decline (-8% from launch)
- **Next Expected Sale**: Back-to-school (Aug 2025), projected $165-$175

**Recommendation**: Current price ($179) is fair. If not urgent, wait for August sale for potential $10-15 savings.
```

#### Source Credibility Distribution

Visualize the quality of your evidence base:

```markdown
## Source Quality Assessment

### Credibility Score Distribution (n=47 sources)

```
High (0.85-0.95)    ████████████████████░░░░░░  15 sources (32%)
Medium (0.70-0.84)  ███████████████████████████  24 sources (51%)
Low (0.60-0.69)     ████░░░░░░░░░░░░░░░░░░░░░░   8 sources (17%)
```

**Source Breakdown**:
- **Expert Reviews** (0.90): Wirecutter, Consumer Reports, RTINGS (n=3)
- **Academic** (0.85): Peer-reviewed journals, safety studies (n=2)
- **Tech Media** (0.80): The Verge, Ars Technica, CNET (n=8)
- **Community Expert** (0.75): Reddit power users (>10k karma), YouTube reviewers (>100k subs) (n=12)
- **User Reviews** (0.70): Amazon verified purchase, Coupang (n=18)
- **Forums** (0.65): Reddit general, niche forums (n=4)

**Weighted Credibility**: 0.77 (good - majority from reliable sources)
```

#### Review Sentiment Analysis

Show sentiment trends visually:

```markdown
## User Review Sentiment Analysis (n=2,340 reviews)

### Overall Rating Distribution

```
5★ ████████████████████░░░░░░░░░░  1,170 reviews (50%)  ← Majority
4★ ██████████████░░░░░░░░░░░░░░░░    702 reviews (30%)
3★ ████░░░░░░░░░░░░░░░░░░░░░░░░░░    234 reviews (10%)
2★ ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░    117 reviews (5%)
1★ ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░    117 reviews (5%)
```

**Aggregate Score**: 4.2/5.0 ★ (Amazon), 4.3/5.0 ★ (Coupang)

### Sentiment by Topic

| Topic | Positive | Neutral | Negative | Net Sentiment |
|-------|----------|---------|----------|---------------|
| **Video Quality** | ████████████████░░░░ 80% | ████░ 15% | █░ 5% | **+75%** 👍 |
| **Setup Ease** | ██████████████░░░░░░ 70% | ██████░ 20% | ██░ 10% | **+60%** 👍 |
| **Reliability** | ████████████░░░░░░░░ 60% | ████░ 15% | █████░ 25% | **+35%** ⚠️ |
| **Customer Support** | ████████████████████ 90% | ██░ 8% | ░ 2% | **+88%** 🎯 |
| **Value for Money** | ████████████░░░░░░░░ 65% | ██████░ 20% | ███░ 15% | **+50%** 👍 |

**Sentiment Legend**:
- **>70%**: Strong positive (🎯)
- **50-69%**: Generally positive (👍)
- **30-49%**: Mixed/Concerning (⚠️)
- **<30%**: Generally negative (❌)
```

#### Confidence Over Time (Decay Model)

Visualize how research confidence degrades:

```markdown
## Research Confidence Trajectory

### Confidence Decay Projection (Dynamic Research, 6-12mo validity)

```
1.0 |
    | ● ← Research completed (0.85)
0.9 |  ────
    |       ╲
0.8 |        ●───── Current confidence holding
    |         ╲
0.7 |          ╲
    |           ○ ← Review recommended (0.78)
0.6 |            ╲
    |             ● ← Major update needed (0.65)
0.5 |__________________________________________
    Now    +3mo    +6mo    +9mo    +12mo
   (Jan)  (Apr)   (Jul)   (Oct)   (Jan)
```

**Decay Milestones**:
- **Now (Jan 2025)**: 0.85 ⭐⭐⭐ - Fresh research, high confidence
- **+3 months (Apr)**: 0.83 ⭐⭐⭐ - Minor drift expected (pricing changes)
- **+6 months (Jul)**: 0.78 ⭐⭐⭐ - **REVIEW RECOMMENDED** (new models likely)
- **+9 months (Oct)**: 0.72 ⭐⭐ - Moderate confidence (dated recommendations)
- **+12 months (Jan 2026)**: 0.65 ⭐⭐ - **MAJOR UPDATE NEEDED** (product lifecycle changes)

**Decay Formula**: `confidence(t) = 0.85 × (0.98 ^ months_elapsed)`

**Action Triggers**:
- ✅ **No action needed**: 0-3 months
- ⚠️ **Light review**: 3-6 months (quick update, pricing check)
- 🔄 **Standard update**: 6-9 months (add new sources, verify recs)
- 🔴 **Major re-research**: 9-12+ months (potentially outdated, full refresh)
```

#### Cross-Cultural Comparison Charts

Compare regional differences visually:

```markdown
## Cross-Cultural Analysis: Western vs. Korean Preferences

### Feature Importance by Region

```
                    Western (n=1,500)          Korean (n=840)
Video Quality       ████████████████ 85%       ████████████ 65%
Night Vision        ████████████ 70%           ███████████████ 80%
Two-Way Audio       ████████ 45%               ████████████████ 85%
Motion Analytics    ███████████████ 80%        ████████ 45%
Air Quality         ████ 20%                   ████████████████ 90%
Temperature Mon.    ████████████ 65%           ███████████████████ 95%
```

**Regional Insights**:
- **Western priorities**: Video quality, motion-alert analytics (data-driven monitoring)
- **Korean priorities**: Environmental monitoring (air quality, temp), two-way communication
- **Convergence**: Both value night vision highly (70-80%)
- **Divergence**: Air quality monitoring (20% West vs 90% Korea) - Korean air quality concerns

**Recommendation Impact**:
- **For Western buyers**: Prioritize products with motion analytics (Eufy, Aqara)
- **For Korean buyers**: Prioritize models with air quality sensors (Samsung, LG)
- **Universal**: All recommendations must have strong night vision
```

#### Comparison Matrix Heatmaps

Visual product comparison across dimensions:

```markdown
## Multi-Dimensional Product Comparison

### Feature Comparison Heatmap

Legend: 🟢 Excellent (9-10) | 🔵 Good (7-8) | 🟡 Fair (5-6) | 🔴 Poor (1-4)

|  | Product A | Product B | Product C | Product D | Product E |
|--|-----------|-----------|-----------|-----------|-----------|
| **Video Quality** | 🔵 7.5 | 🟢 9.5 | 🔵 8.0 | 🟡 6.0 | 🟢 9.0 |
| **Night Vision** | 🟢 9.0 | 🔵 8.5 | 🟢 9.5 | 🟡 6.5 | 🟢 9.0 |
| **Audio Quality** | 🔵 8.0 | 🔵 7.5 | 🔵 8.5 | 🟡 5.5 | 🔵 8.0 |
| **Smart Features** | 🔵 7.0 | 🟢 9.0 | 🟢 9.5 | 🟡 6.0 | 🔵 8.5 |
| **Reliability** | 🟢 9.0 | 🟢 9.5 | 🔵 8.0 | 🔴 4.5 | 🔵 8.5 |
| **Setup Ease** | 🟢 9.5 | 🔵 7.0 | 🔵 8.5 | 🟢 9.0 | 🔵 7.5 |
| **Value** | 🟢 9.5 | 🟡 6.0 | 🔵 8.0 | 🔵 7.5 | 🟡 6.5 |
| **Support** | 🟢 9.0 | 🟢 9.5 | 🔵 7.5 | 🔴 4.0 | 🔵 8.0 |
| **Privacy** | 🔵 8.0 | 🟢 10.0 | 🔵 7.5 | 🟡 5.0 | 🔵 8.5 |

**At-a-Glance Summary**:
- **Product A**: Best all-around value, consistent 7-9 scores, no major weaknesses
- **Product B**: Premium quality (most 🟢), expensive (🟡 value)
- **Product C**: Smart home leader (🟢 9.5), solid all-around
- **Product D**: Avoid - multiple red flags (reliability 🔴, support 🔴)
- **Product E**: Strong performer, premium price tier
```

**When to Use Visual Data Presentation**:
- **ASCII Charts**: Price trends, sentiment, distributions, timelines
- **Heatmaps**: Multi-dimensional comparisons, risk assessment, feature matrices
- **Bar Charts**: Percentages, distributions, category breakdowns
- **Scatter/Line**: Trends over time, confidence decay, projections
- **Tables with Indicators**: When combining numbers with qualitative assessments

**Visual Design Principles**:
1. **Keep it simple**: ASCII art should be scannable in <5 seconds
2. **Use color sparingly**: Emoji/symbols for categories, not decoration
3. **Label clearly**: Every axis, every bar, every data point
4. **Provide context**: Always explain what the visualization means
5. **Show uncertainty**: Don't hide confidence intervals or data gaps

