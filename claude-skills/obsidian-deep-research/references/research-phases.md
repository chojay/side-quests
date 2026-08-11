# Research Phases (1 through 10.5)

Part of the `obsidian-deep-research` skill. Read this file before executing each phase:
it contains the full prompts, templates, checklists, and worked examples for every phase.

## Contents

- Phase 1: Research Planning with Plan Agent
- Phase 2: Existing Knowledge Mapping with Explore Agent
- Phase 3: Research Planning & Strategy
- Phase 3.5: Research Scope Validation
- Phase 4: Parallel Information Gathering with Multiple Subagents (incl. Domain-Optimized Agent Templates)
- Phase 5: Source Validation & Credibility Assessment
- Phase 5.5: Adversarial Source Mining
- Phase 6: Cross-Referencing & Triangulation
- Phase 7: Synthesis & Analysis
- Phase 8: Critical Review & Fact-Checking
- Phase 9: Advanced Wiki-Link Integration & Knowledge Graph Building
  1. Create Research Note with Enhanced Frontmatter
  2. Semantic Clustering & Hub Notes
  3. Ontological Linking (Relationship Types)
  4. Multi-Dimensional Tagging System
  5. Bidirectional Link Audit & Backlink Creation
  6. MOC (Map of Content) Auto-Generation
  7. Block References for Key Findings
  8. Dynamic Query Blocks for Living MOCs
  9. Knowledge Graph Connectivity Metrics
  10. Graph Visualization Preparation
  (plus Phase 9 Summary Checklist)
- Phase 10: Final Packaging with Confidence Metrics
- Phase 10.5: Research Maintenance & Monitoring Plan

#### Phase 1: Research Planning with Plan Agent

**⚠️ MANDATORY: Use the Plan agent before any research execution**

```
Task(subagent_type="Plan", prompt="Plan a comprehensive research strategy for: [TOPIC]

**Step 1: Select Research Perspective**

Choose the cognitive framework that best matches the research goals:

**Academic Skeptic** - Use when:
- Research requires rigorous scientific validation
- Need to evaluate study quality and methodological soundness
- Important to identify confounders and biases
- Approach: Question everything, demand evidence, identify limitations
- Critical focus: Sample sizes, control groups, replication, peer review
- Example: \"What does the evidence really say about probiotics for gut health?\"

**Practical Optimizer** - Use when:
- Research drives real-world purchasing or implementation decisions
- Need to balance ideal vs. realistic recommendations
- Cost-benefit analysis is critical
- Approach: Focus on usability, total cost of ownership, real user experiences
- Critical focus: Price/value, ease of use, customer support, resale value
- Example: \"Best robot vacuum considering budget, setup complexity, and actual reliability\"

**Cultural Comparativist** - Use when:
- Research spans multiple cultural contexts (Western + Asian sources)
- Regional practices and norms vary significantly
- Need to identify culture-specific recommendations
- Approach: Seek diverse cultural perspectives, identify regional differences
- Critical focus: Cross-cultural validation, localization, cultural assumptions
- Example: \"How do Korean vs. Western skincare routines differ on sunscreen use?\"

**Safety Auditor** - Use when:
- Research involves health, safety, or risk assessment
- Need to prioritize failure modes and worst-case scenarios
- Regulatory compliance and recalls are relevant
- Approach: Assume worst case, prioritize risk mitigation, check recalls
- Critical focus: Safety recalls, failure rates, regulatory warnings, liability
- Example: \"Are space heaters safe? What are the documented failure modes?\"

**Innovation Scout** - Use when:
- Research seeks cutting-edge or emerging solutions
- Interested in future trends and upcoming technologies
- Willing to trade maturity for innovation
- Approach: Seek latest research, emerging standards, forward-looking analysis
- Critical focus: New protocols, upcoming products, research frontiers
- Example: \"What smart thermostats support Matter protocol? What's coming in 2025-2026?\"

**Perspective Integration**:
You may combine perspectives (e.g., Safety Auditor + Practical Optimizer for space heaters).
State chosen perspective(s) and explain how they shape the research strategy.

**Step 2: Analyze with Selected Perspective**

Analyze and provide:
1. **Chosen Research Perspective(s)**: [Name and brief rationale]
2. **Key entities, concepts, and relationships** in the question
3. **Research domain classification** (academic, product, medical, technical)
4. **Decomposed atomic sub-questions** (minimum 5, shaped by perspective)
   - Academic Skeptic: \"What's the quality of evidence?\"
   - Practical Optimizer: \"What's the total cost of ownership?\"
   - Cultural Comparativist: \"How do regional practices differ?\"
   - Safety Auditor: \"What are documented failure modes?\"
   - Innovation Scout: \"What emerging alternatives exist?\"
5. **Perspective-specific assumptions and biases** to watch for
   - Academic: Publication bias, funding bias
   - Product: Survivorship bias, affiliate marketing bias
   - Cultural: Western-centrism, availability bias
   - Safety: Negativity bias, availability heuristic
   - Innovation: Recency bias, hype cycle influence
6. **Research hypothesis and null hypothesis**
7. **Recommended parallel research pathways** (for subagent delegation)
8. **Source types to prioritize** (aligned with perspective)
9. **Perspective-specific validation criteria** and confidence thresholds
10. **Expected deliverables and note structure** (optimized for perspective)

**Step 3: Define Success Criteria by Perspective**

**Academic Skeptic Success**:
- ≥5 peer-reviewed studies analyzed
- Methodological quality scores documented
- Effect sizes with confidence intervals
- Replication evidence assessed

**Practical Optimizer Success**:
- Total cost of ownership calculated (purchase + operating + maintenance)
- Real user reviews (≥100 per major product)
- Setup complexity and learning curve assessed
- Resale value / cost recovery potential documented

**Cultural Comparativist Success**:
- ≥2 cultural perspectives validated (e.g., Western + Korean)
- Regional differences explicitly documented
- Culture-specific recommendations provided
- Translation/localization considerations noted

**Safety Auditor Success**:
- Recall history checked (CPSC, FDA databases)
- Failure mode analysis from negative reviews
- Regulatory compliance verified
- Worst-case scenarios and mitigation strategies documented

**Innovation Scout Success**:
- Emerging technologies identified (≤12 months old)
- Future roadmap from manufacturers researched
- Early adopter experiences gathered
- Competitive landscape forecast (6-12 months ahead)")
```

The Plan agent will return a structured research strategy shaped by the chosen cognitive perspective(s), ensuring domain expertise is embedded from the start.

#### Phase 2: Existing Knowledge Mapping with Explore Agent

**Use the Explore agent to efficiently scan the vault for existing knowledge:**

```
Task(subagent_type="Explore", prompt="Explore the Obsidian vault for existing notes related to: [TOPIC]

Search for:
1. Notes with keywords: [keyword1], [keyword2], [keyword3]
2. Related project directories
3. Existing wiki links mentioning key concepts
4. Previous research notes with similar domains
5. MOCs (Maps of Content) that might include this topic

Return:
- List of related note paths with brief descriptions
- Existing knowledge graph connections
- Identified knowledge gaps
- Previously cited sources and their confidence levels")
```

This isolates the vault exploration context, preventing search noise from cluttering the main conversation.

#### Phase 3: Research Planning & Strategy
1. Select appropriate research methodologies:
   - **Academic**: Systematic review, meta-analysis
   - **Product**: Comparative analysis, user review mining
   - **Medical**: Evidence hierarchy, clinical guidelines
   - **Technical**: Documentation review, implementation analysis
2. Define source diversity requirements:
   - Geographic: Western (Reddit, Amazon) + Asian (Naver, Coupang)
   - Authority: Expert (Wirecutter, Consumer Reports) + Community
   - Temporal: Historical trends + Current consensus
3. Set confidence thresholds and validation criteria
4. Create parallel research pathways

#### Phase 3.5: Research Scope Validation

**Before launching expensive parallel agents, validate research feasibility:**

**Purpose**: Prevent wasted effort from unfeasible research plans and provide early cost/time awareness.

**Validation Checklist**:

**1. Source Accessibility Check**
- Test 2-3 representative URLs from each planned source category
- Identify potential blockers:
  - ❌ Paywalled sources (NYTimes, WSJ, academic journals without access)
  - ❌ Geo-blocked content (region-restricted services)
  - ❌ Defunct sources (404 errors, discontinued sites)
  - ⚠️ Rate-limited APIs (Twitter, Reddit with API restrictions)
- Document fallback strategies for each blocked source type
- Example: "Wirecutter paywall → Use web archive or free Consumer Reports alternative"

**2. Keyword Validation**
- Run preliminary searches with planned keywords
- Verify sufficient results exist:
  - ✅ Good: >10 relevant results per major source
  - ⚠️ Marginal: 3-10 results (may need keyword expansion)
  - ❌ Poor: <3 results (refine search terms or pivot topic)
- Test keyword variations if initial results are weak:
  - Product names: Try brand name, model number, generic category
  - Academic topics: Try synonyms, related terms, broader categories
- Adjust search strategy based on findings

**3. Research Depth Feasibility**
- Validate chosen research depth matches available data:
  - **Deep Research**: Requires ≥20 diverse sources across ≥3 source types
  - **Standard Research**: Requires ≥10 sources across ≥2 source types
  - **Quick Research**: Requires ≥5 sources minimum
- If insufficient sources found:
  - Option A: Downgrade research depth tier
  - Option B: Expand scope (broader topic, longer time range)
  - Option C: Document as research limitation

**4. Cost & Token Estimation**
- Estimate research costs to set expectations:
  ```
  Cost Calculation:
  - WebSearch calls: {n} × ~$0.01 = ${X}
  - WebFetch calls: {n} × ~$0.01 = ${Y}
  - Browser automation: {n} pages × ~$0.03 = ${Z}
  - Subagent overhead: {n} agents × 20k tokens × $0.003/1k = ${W}
  ---
  Estimated Total: ${total}
  Estimated Time: {hours} hours
  ```
- Flag if costs exceed reasonable thresholds:
  - ⚠️ Warning at >$5.00 (might indicate scope creep)
  - 🔴 Critical at >$10.00 (definitely reconsider scope)

**5. Timeline Feasibility**
- Calculate estimated completion time:
  - Phase 1 (Planning): ~5-10 minutes
  - Phase 2 (Vault exploration): ~3-5 minutes
  - Phase 3-3.5 (Strategy + Validation): ~5 minutes
  - Phase 4 (Parallel agents): ~20-40 minutes (varies by agent count)
  - Phases 5-10 (Synthesis + Analysis + Output): ~30-60 minutes
  - **Total**: Quick (~30 min), Standard (~2 hours), Deep (~4+ hours)
- Identify critical path dependencies:
  - Which phases must complete before others?
  - Which agents have dependencies (e.g., price tracking needs product identified first)?
- Warn if research depth doesn't match available time:
  - Example: "Deep Research estimated at 4 hours, but limited sources suggest Standard (2 hours) more appropriate"

**Decision Point**:

After validation, choose one:

1. ✅ **Proceed as Planned** - All checks passed, continue to Phase 4
2. ⚠️ **Refine Scope** - Adjust keywords, expand sources, or modify approach based on findings
3. 🔽 **Downgrade Depth** - Move from Deep → Standard or Standard → Quick based on available sources
4. 🔼 **Upgrade Depth** - If validation reveals topic more complex than expected, upgrade tier
5. ⏸️ **Defer Research** - Insufficient data available, wait for more sources or user input

**Example Validation Output**:
```markdown
## Phase 3.5 Validation Results

**Source Accessibility**: ⚠️ 2 sources paywalled (Wirecutter, Consumer Reports)
- Fallback: Using web archive + Reddit for consumer insights

**Keyword Check**: ✅ Strong results
- Amazon: 450 reviews found
- Reddit r/HomeKit: 23 relevant threads
- YouTube: 15 review videos

**Depth Feasibility**: ✅ Confirmed Standard Research
- Available sources: 18 (exceeds 10 minimum)
- Source types: 4 (expert, community, video, pricing)

**Cost Estimate**: $3.50 (within budget)
- 6 subagents × $0.50 = $3.00
- WebSearch/Fetch: ~$0.50

**Timeline**: ~2 hours (matches Standard tier)

**Decision**: ✅ PROCEED with Standard Research
```

**When to Skip This Phase**:
- Quick Research with well-known topics (e.g., "iPhone 15 reviews")
- Follow-up research expanding existing notes (incremental mode)
- Very narrow scope with pre-identified sources

---

#### Phase 4: Parallel Information Gathering with Multiple Subagents

**⚠️ CRITICAL: Launch ALL research agents in a SINGLE message for true parallelization**

Spawn 4-8 general-purpose agents simultaneously, each with a focused research domain:

```
// Launch all agents in ONE message block for parallel execution:

Task(subagent_type="general-purpose", prompt="PRIMARY SOURCES RESEARCH for [TOPIC]:
Search and analyze:
- Academic databases (Google Scholar, PubMed, arXiv)
- Official documentation and specifications
- Government databases and statistics
- Patent databases (USPTO, Google Patents)
Return: Structured findings with source URLs, publication dates, and credibility scores.")

Task(subagent_type="general-purpose", prompt="EXPERT ANALYSIS RESEARCH for [TOPIC]:
Search and analyze:
- Wirecutter, Consumer Reports reviews
- Industry analyst reports
- Professional forums and communities
- Technical specifications and teardowns
Return: Expert consensus, product rankings, and technical insights with source citations.")

Task(subagent_type="general-purpose", prompt="COMMUNITY CONSENSUS RESEARCH for [TOPIC]:
Search and analyze:
- Reddit discussions (identify relevant subreddits: r/[sub1], r/[sub2])
- Amazon reviews (focus on verified purchases, >100 reviews)
- Stack Exchange communities
- YouTube reviews (channels with >10k subscribers)
Return: Community sentiment, common praise/complaints, and user tips with upvote/review counts.")

Task(subagent_type="general-purpose", prompt="KOREAN/ASIAN SOURCES RESEARCH for [TOPIC]:
Search and analyze:
- Naver blogs and cafes (Korean)
- Coupang reviews and ratings (Korean)
- Rakuten reviews (Japanese)
- Regional pricing comparisons (Korea, Japan)
Return: Cross-cultural perspectives, regional preferences, and price differentials in KRW/JPY/USD.")

Task(subagent_type="general-purpose", prompt="PRICING & AVAILABILITY RESEARCH for [TOPIC]:
Search and analyze:
- Amazon pricing and availability
- Retailer comparisons (Best Buy, Walmart, Target)
- Used/refurbished market (eBay, Facebook Marketplace)
- Historical price tracking if available
Return: Price matrix by retailer, availability status, and best value recommendations.")

Task(subagent_type="general-purpose", prompt="COUNTER-EVIDENCE RESEARCH for [TOPIC]:
Actively seek disconfirming evidence:
- Negative reviews and common complaints
- Failure modes and known issues
- Competitor comparisons
- User regrets and returns data
Return: Critical analysis, potential deal-breakers, and alternative recommendations.")

Task(subagent_type="general-purpose", prompt="YOUTUBE VIDEO RESEARCH for [TOPIC]:
Search and analyze relevant YouTube videos:
- Tutorial and educational videos from expert channels (>10k subscribers)
- Product reviews and demonstrations
- Conference talks and expert presentations
- How-to guides with high engagement (>50k views)

For each relevant video:
1. Use the youtube-transcript MCP server to extract transcript
2. For long videos (>45 min), use chunked retrieval with pagination
3. Summarize key insights with timestamps
4. Note speaker credentials and channel authority
5. Extract actionable recommendations

Return:
- Video summaries with YouTube URLs and timestamps
- Key insights organized by sub-topic
- Speaker/channel credibility assessment
- Recommended videos for further viewing

Note: If MCP server hits token limits, request transcript WITHOUT timestamps to reduce by 20-30%.")
```

---

#### Domain-Optimized Agent Templates

The agents above provide baseline research coverage. **Enhance your research with domain-specific agents** tailored to your research type:

**For Product Research - Add These Specialized Agents:**

```
Task(subagent_type="general-purpose", prompt="PRICE TRACKING & HISTORICAL DATA for [PRODUCT]:
Search and analyze pricing patterns:
- CamelCamelCamel for Amazon price history (6-12 month trends)
- Keepa for price drop alerts and historical charts
- Slickdeals for deal patterns and community-reported sales
- Honey for available coupon codes
- Seasonal pricing analysis (Black Friday, Prime Day patterns)
- Price comparison across retailers (Best Buy, Walmart, direct)

Return:
- Price trends visualization (6-12 month chart description)
- Current price vs. average/lowest (e.g., \"$145 current vs. $148 avg, $138 lowest\")
- Best time to buy recommendation (e.g., \"Wait for Aug-Sep back-to-school sales\")
- Price drop probability and magnitude
- Deal alert setup instructions (CamelCamelCamel, Keepa links)")

Task(subagent_type="general-purpose", prompt="FAILURE MODE ANALYSIS for [PRODUCT]:
Systematically identify common failure patterns:
- Amazon reviews: Filter 1-2 stars, keywords: 'returned', 'broke', 'failed', 'stopped working'
- Reddit search: '[product] problems', '[product] issues', '[product] regret', '[product] broke'
- YouTube: '[product] long-term review', '[product] after 6 months', '[product] after 1 year'
- Forums: Specific issue threads with >50 replies
- Warranty claim data if publicly available
- Product recall databases (CPSC, manufacturer announcements)

Analyze:
- Most common failure modes with frequency (e.g., \"WiFi connectivity issues: 15% of reviews\")
- Time to failure patterns (e.g., \"Motor failure at 8-12 month mark\")
- Warranty coverage and claim success rate
- Manufacturer response quality

Return:
- Failure rate estimates by component
- Mean Time Between Failures (MTBF) if calculable
- Common failure timeline (\"works great for 6 months, then...\")
- Warranty claim insights and success rates
- Deal-breaker issues (failures affecting >20% of users)")

Task(subagent_type="general-purpose", prompt="LONGEVITY & RESALE VALUE RESEARCH for [PRODUCT]:
Assess long-term ownership economics:
- eBay sold listings (not asking prices) for 1-year-old, 2-year-old models
- Facebook Marketplace, Craigslist completed sales
- Trade-in values (Gazelle, Swappa for electronics)
- Replacement part availability and costs
- Software/firmware update history (shows manufacturer support timeline)
- Community lifespan reports (Reddit \"still going strong after X years\")

Calculate:
- Depreciation rate (year 1: -X%, year 2: -Y%)
- Total Cost of Ownership: Purchase + Accessories + Maintenance - Resale
- Cost per use over expected lifespan
- Replacement part ecosystem maturity

Return:
- Resale value retention (\"Retains 60% value after 2 years\")
- TCO calculation with assumptions
- Expected useful lifespan with confidence
- Upgrade cycle recommendations)")
```

**For Academic Research - Add These Specialized Agents:**

```
Task(subagent_type="general-purpose", prompt="GREY LITERATURE SEARCH for [TOPIC]:
Search beyond peer-reviewed journals for cutting-edge and unpublished findings:
- Preprint servers: arXiv, bioRxiv, medRxiv, SSRN, PsyArXiv
- Dissertation databases: ProQuest, Open Access Theses and Dissertations
- Conference proceedings: IEEE Xplore, ACM Digital Library, conference websites
- Technical reports: NASA Technical Reports Server, DOE OSTI, RAND Corporation
- White papers from industry research labs
- Government research portals (grants.gov for funded research)

Return:
- Unpublished findings not yet in peer review
- Dissertation abstracts with novel methodologies
- Conference presentations (especially from top-tier venues)
- Technical reports with implementation details
- Research gaps identified by doctoral candidates
- Credibility assessment (preprint status, institution ranking, author h-index)")

Task(subagent_type="general-purpose", prompt="CITATION NETWORK ANALYSIS for [TOPIC]:
Map the research landscape through citation analysis:
- Google Scholar: Forward citation search on key papers (\"cited by\" feature)
- Semantic Scholar: 'Highly Influential Citations' metric
- Connected Papers: Visual citation graphs showing research clusters
- Papers with Code: Implementation availability for methods
- Citation count trends (rising vs. declining influence)
- Author network analysis (key research groups, collaborations)

Identify:
- Foundational papers (high citation count, older)
- Rising stars (recent papers with rapid citation growth)
- Review papers and meta-analyses
- Replication studies and validation efforts
- Contradictory findings in citation network
- Research evolution timeline (how field has developed)

Return:
- Top 5 most-cited foundational papers with citation counts
- Emerging research directions (papers <3 years with >100 citations/year)
- Citation graph description (clusters, key nodes)
- Replication rate if available
- Research timeline visualization description)")

Task(subagent_type="general-purpose", prompt="METHODOLOGICAL RIGOR ASSESSMENT for [TOPIC]:
Critically evaluate research quality across studies:
- Sample size analysis (n=? across studies, power calculations)
- Study design quality: RCT > cohort > case-control > case series
- Blinding and randomization methods
- Statistical methodology appropriateness
- Conflict of interest disclosures
- Funding source analysis (industry vs. independent)
- Replication attempts and outcomes
- PRISMA compliance for systematic reviews
- Pre-registration status (ClinicalTrials.gov, OSF)

Check for bias:
- Publication bias (funnel plot asymmetry, file drawer problem)
- Selection bias (inclusion/exclusion criteria)
- Measurement bias (validated instruments used?)
- Attrition bias (dropout rates, ITT analysis?)

Return:
- Study quality tiers (High/Medium/Low by standard criteria)
- Common methodological weaknesses
- Most rigorous studies (highlight top 3)
- Bias risk assessment summary
- Meta-analytic heterogeneity (I² statistic if available))")
```

**For Medical/Health Research - Add These Specialized Agents:**

```
Task(subagent_type="general-purpose", prompt="CLINICAL GUIDELINES & EXPERT CONSENSUS for [TOPIC]:
Search authoritative medical guidance:
- Clinical practice guidelines: AAP, ACOG, AHA, WHO, NIH
- Cochrane systematic reviews and meta-analyses
- UpToDate clinical decision support
- Professional society position statements
- FDA approvals, warnings, and safety communications
- Clinical trial registries for ongoing research

Extract:
- Official recommendations with strength of evidence ratings
- Guideline publication dates and update schedules
- Consensus vs. controversial areas
- Patient population applicability
- Implementation barriers noted in guidelines

Return:
- Evidence-based recommendations (Grade A/B/C)
- Clinical guideline summary with update dates
- Areas of consensus vs. ongoing debate
- Real-world implementation challenges
- Gaps between guidelines and practice)")
```

**Selection Guidance:**
- **Product research**: Always include Price Tracking + Failure Mode Analysis
- **Academic research**: Always include Citation Network + Grey Literature
- **Medical research**: Always include Clinical Guidelines + Methodological Rigor
- **Mix and match**: Combine baseline agents (1-6) + domain-specific agents (2-3) = 8-9 total agents

**Benefits of Parallel Execution:**
- 6 agents running simultaneously vs. sequential = ~6x faster
- Each agent has isolated context = no information overload
- Wider source coverage = more comprehensive research
- Independent validation = reduced confirmation bias

#### Phase 5: Source Validation & Credibility Assessment
1. Apply the credibility scoring matrix from `references/research-methodologies.md`
   (canonical source: the "Base Scores by Source Type" table, plus Recency Factors
   and Corroboration Multipliers)
2. Check for:
   - Publication date and relevance decay
   - Author credentials and conflicts of interest
   - Sample size and statistical significance
   - Replication and corroboration
3. Flag contradictory evidence for special analysis
4. Generate source quality report

#### Phase 5.5: Adversarial Source Mining

**After initial source gathering, systematically seek disconfirming evidence to reduce confirmation bias.**

**Purpose**: Transform good research into rigorous research by actively challenging initial findings and surfacing counterarguments.

**Adversarial Research Methodology**:

**1. Inversion Techniques**

Apply negative search patterns to find dissenting views:

**Negative Keyword Search**:
- Add to base search: "why not {product/topic}", "problems with {product/topic}"
- Alternative phrasing: "{product/topic} overrated", "{product/topic} disappointing"
- Failure-focused: "{product/topic} stopped working", "{product/topic} regret"
- Comparative: "alternatives to {product/topic}", "better than {product/topic}"

**Example**:
```
Initial search: "Breville Barista Express review"
Adversarial searches:
- "Breville Barista Express problems"
- "Breville Barista Express not worth it"
- "Breville Barista Express alternatives"
- "Breville Barista Express stopped working"
- "regret buying Barista Express"
```

**Competitor Advocacy**:
- Search from competing product/theory advocacy groups
- Find communities that prefer alternatives
- Example: If researching Product A, search "Product B vs Product A" in Product B community
- Rationale: Competitors' strongest criticisms often reveal genuine weaknesses

**Regulatory & Safety Warnings**:
- FDA warnings, recalls, safety alerts (www.fda.gov, www.cpsc.gov)
- Consumer protection agencies (FTC complaints, BBB)
- Product recall databases (CPSC, manufacturer announcements)
- Class action lawsuits (legal databases, news reports)

**Debunking & Fact-Checking Sources**:
- Snopes, FactCheck.org for viral claims
- Retraction Watch for withdrawn academic papers
- PubPeer for post-publication peer review
- Industry watchdog organizations

**Academic Criticism**:
- Search: "{study/theory} limitations", "{study} criticism"
- Failed replications: "{study} replication failure", "{study} cannot replicate"
- Methodological critiques: "{study} flawed methodology"
- Contradictory meta-analyses

---

**2. Cognitive Bias Checks**

Systematically check for common biases distorting initial findings:

**Survivorship Bias**:
- **What it is**: Only seeing successful products/studies because failures disappeared
- **How to check**:
  - Search for discontinued products in same category
  - Look for failed clinical trials (ClinicalTrials.gov for unpublished results)
  - Find abandoned research directions
  - Check company acquisition/shutdown histories
- **Example**: "Researching smart home hubs? Search for ones that shut down (Revolv, Lowe's Iris)"

**Publication Bias**:
- **What it is**: Positive results published more than negative/null results
- **How to check**:
  - Check trial registries for unpublished studies (ClinicalTrials.gov, WHO ICTRP)
  - Compare registered trial count vs. published paper count
  - Look for funnel plot asymmetry in meta-analyses
  - Search grey literature for negative findings
- **Impact**: May overestimate treatment effects by 10-30%

**Selection Bias**:
- **What it is**: Sample not representative of population
- **How to check**:
  - Who was excluded from studies? (age, health status, geography)
  - Are Amazon reviews from early adopters vs. average users?
  - Do Reddit communities skew toward enthusiasts?
- **Mitigation**: Seek sources from average/casual user populations

**Recency Bias**:
- **What it is**: Overweighting recent information
- **How to check**:
  - Compare current consensus to historical perspectives
  - Look for "pendulum swings" in recommendations
  - Find older long-term reviews (e.g., "Product X after 3 years")
- **Example**: "Low-carb diet effective" (recent) vs. "Low-fat diet effective" (1990s)

**Confirmation Bias** (in your own research):
- **What it is**: Seeking information that confirms initial hypothesis
- **How to check**:
  - Did you search for disconfirming evidence as actively as confirming?
  - Count sources supporting vs. contradicting main conclusion
  - Have you steel-manned the opposing view?
- **Mitigation**: Force yourself to find N sources opposing your conclusion

---

**3. Red Team Exercise**

Apply adversarial thinking to challenge research conclusions:

**Incentive Analysis**:
- **Question**: Who benefits financially if this conclusion is true?
  - Manufacturer if product gets positive review
  - Pharmaceutical company if drug appears effective
  - Author if paper gets citations/press
- **Action**: Weight sources with financial conflicts of interest lower
- **Example**: Industry-funded studies show 20-30% larger effect sizes

**Evidence Reversal**:
- **Question**: What evidence would disprove the leading hypothesis?
  - If claiming "Product X is best for Y", what would make it NOT best?
- **Action**: Actively search for that specific evidence
- **Example**: "If the built-in grinder is the machine's weak point, I should find posts about grinder failures after a few months of use"

**Stakeholder Mapping**:
- **Question**: Which groups benefit vs. are harmed by this being true/false?
  - Manufacturers, retailers, consumers, competitors, regulators
- **Action**: Seek perspectives from each stakeholder group
- **Example**: Smart lock manufacturers want you to buy, but locksmiths may have security concerns

**Strongest Counterargument**:
- **Question**: What's the BEST argument against my conclusion?
  - Not a weak strawman, but steel-manned opposition
- **Action**: Find the most articulate, well-reasoned criticism
- **Example**: Don't just find "Product X sucks", find detailed technical critique

---

**4. Adversarial Search Patterns**

**For Product Research**:
```
Search queries:
- "{product} vs {top competitor}" in competitor subreddit
- "{product} long term problems"
- "{product} firmware issues"
- "{product} customer service nightmare"
- "cheaper alternative to {product}"
- "{product} honeymoon phase" (initial excitement fades)
```

**For Academic Research**:
```
Search queries:
- "{study author} conflict of interest"
- "{topic} null results"
- "{intervention} no effect"
- "{claim} debunked"
- "criticism of {theory}"
- "{method} replication crisis"
```

**For Medical Research**:
```
Search queries:
- "{treatment} side effects long term"
- "{treatment} didn't work for me"
- "{treatment} adverse events"
- "{treatment} contraindications"
- "when {treatment} fails"
```

---

**5. Output & Integration**

**Document Adversarial Findings**:
```markdown
## Adversarial Analysis Results

**Disconfirming Evidence Found**: {count} sources

### Critical Issues Identified:
1. **{Issue 1}** (severity: 🔴 High)
   - Source: {citation}
   - Frequency: {X}% of critical reviews mention this
   - Impact on conclusion: {how this changes recommendation}

2. **{Issue 2}** (severity: 🟡 Moderate)
   - Source: {citation}
   - Frequency: {Y}%
   - Mitigation: {workaround or caveat}

### Bias Checks:
- **Survivorship bias**: {assessment - e.g., "3 competing products discontinued"}
- **Publication bias**: {assessment - e.g., "2 unpublished trials found"}
- **Financial conflicts**: {X}% of positive sources have industry ties

### Red Team Findings:
- **Strongest counterargument**: {steel-manned opposition view}
- **Who benefits from positive conclusion**: {manufacturer, retailer}
- **Overlooked stakeholder perspectives**: {locksmith security concerns}

### Impact on Confidence:
- Initial confidence: ⭐⭐⭐ (0.85)
- After adversarial analysis: ⭐⭐ (0.75)
- Reason for reduction: {discovered reliability issues affecting 15% of users}
```

**Integrate into Main Research**:
- Add critical issues to "Failure Mode Analysis" section
- Update confidence scores based on discovered contradictions
- Add caveats to recommendations
- Create "Not Recommended For" section based on adversarial findings
- Balance "Common Praise" with "Common Criticism" sections

**When to Reduce Confidence**:
- If adversarial search reveals issues affecting >20% of users: -10 to -15% confidence
- If publication bias detected (missing negative studies): -10% confidence
- If strong financial conflicts in majority of positive sources: -10 to -20% confidence
- If replication failures found for key claims: -20 to -30% confidence

---

**Example Adversarial Analysis in Practice**:

**Initial Finding**: "Breville Barista Express highly recommended (⭐⭐⭐ confidence based on 40 positive reviews)"

**After Adversarial Mining**:
- Found: 15 "inconsistent grind size after 6 months" reports
- Found: 8 "grinder motor failure at 3-4 months" complaints
- Found: Manufacturer-sponsored reviews with clear financial conflict
- Found: Cheaper competitors with similar effectiveness

**Updated Finding**: "Breville Barista Express effective but with caveats (⭐⭐ confidence)"
- Pros: Works well during use (strong consensus)
- Cons: Grinder reliability concerns (moderate evidence, ~15% failure reports), high price vs. alternatives
- Recommendation: Budget for a standalone grinder as a fallback, follow the descaling schedule strictly

---

**When to Skip Adversarial Mining**:
- Quick Research on low-stakes topics
- Topics with naturally balanced source availability (e.g., political debates - both sides already vocal)
- Follow-up research where adversarial analysis was already performed

**Effort Allocation**:
- Standard Research: 15-20% of time on adversarial mining
- Deep Research: 25-30% of time on adversarial mining
- Quick Research: 5-10% or skip if time-constrained

#### Phase 6: Cross-Referencing & Triangulation
1. Compare findings across sources
2. Identify consensus points (>80% agreement)
3. Analyze divergent opinions with context
4. Apply weighted averaging based on credibility scores
5. Generate confidence intervals for key claims

#### Phase 7: Synthesis & Analysis
1. Structure findings using domain-appropriate frameworks:
   - **Product Research**: Features × Price × User Reviews matrix
   - **Academic**: Evidence pyramid with systematic reviews at top
   - **Medical**: Clinical applicability and patient populations
   - **Technical**: Implementation complexity vs benefits
2. Generate decision trees for complex choices
3. Create comparison tables with normalized metrics
4. Calculate cost-per-use for products (where applicable)
5. Identify best practices and recommendations

#### Phase 8: Critical Review & Fact-Checking
1. Perform adversarial analysis:
   - Actively seek disconfirming evidence
   - Identify potential selection biases
   - Check for survivorship bias
   - Validate statistical claims
2. Red team the conclusions:
   - What would critics argue?
   - What evidence is missing?
   - What assumptions were made?
3. Quantify uncertainty:
   - Known unknowns with research gaps
   - Confidence intervals for predictions
   - Temporal validity of findings

#### Phase 9: Advanced Wiki-Link Integration & Knowledge Graph Building

**Purpose**: Transform disconnected research into a navigable knowledge network using advanced Obsidian graph techniques.

**Overview**: Go beyond basic wiki links to create semantic relationships, ontological structures, and dynamic connections.

---

### 1. Create Research Note with Enhanced Frontmatter

**Multi-Dimensional Frontmatter Structure**:
```yaml
---
# Core Metadata
title: "Product Name - Deep Research"
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
research_version: 1.0

# Classification Tags
tags:
  - research/deep                    # Research depth tier
  - domain/product/smart-home        # Domain hierarchy
  - confidence/high                  # Overall confidence level
  - geography/cross-cultural         # Geographic scope
  - temporal/evergreen               # vs temporal/time-sensitive
  - lifecycle/active                 # vs lifecycle/archived
  - source-count/comprehensive       # vs source-count/limited

# Aliases (for linking flexibility)
aliases:
  - "Product Model ABC"
  - "ABC Smart Doorbell"
  - "Doorbell ABC"

# Confidence Metrics
confidence_score: 0.85
confidence_breakdown:
  source_quality: 0.90
  source_diversity: 0.85
  temporal_relevance: 0.75
  sample_size: 0.95
  consistency: 0.70
  reproducibility: 0.88

# Related Notes (explicit relationships)
related:
  - "[[Alternative Product 1]]"      # type: alternative
  - "[[Smart Home MOC]]"              # type: parent
  - "[[HomeKit Ecosystem]]"          # type: context

# Research Provenance
sources_count: 47
primary_sources: 15
community_sources: 24
regional_sources: 8

# Monitoring Plan
review_date: YYYY-MM-DD
monitoring: true
---
```

**Frontmatter Best Practices**:
- Use hierarchical tags: `domain/product/smart-home` not just `smart-home`
- Include confidence breakdown for future recalculation
- Set review_date based on temporal classification
- Add all discovered aliases for flexible linking

---

### 2. Semantic Clustering & Hub Notes

**Group related findings into conceptual clusters:**

**Step 1: Identify Semantic Clusters**
After research, identify major concept groupings:
- **Product Research**: Core technology, competing products, use cases, accessories
- **Academic Research**: Methodologies, key researchers, applications, controversies

**Step 2: Create Hub Notes**
For each cluster, create intermediate "hub notes":

```markdown
# Smart Doorbell Technology Hub

## Core Technologies
- [[Video Compression Algorithms]]
- [[Motion Detection Systems]]
- [[Cloud Storage Architecture]]
- [[Local Processing vs Cloud]]

## Related Research
- [[Best Smart Doorbell 2025]] - ⭐⭐⭐ (this research)
- [[Smart Doorbell Security Analysis]] - ⭐⭐
- [[Doorbell Power Options Comparison]] - ⭐⭐⭐

## Key Concepts
- [[PIR Motion Sensors]]
- [[AI Person Detection]]
- [[Two-Way Audio Latency]]
```

**Step 3: Link Research → Hub → Concepts**
```
[Deep Research Note]
    ↓
[Smart Doorbell Technology Hub]
    ↓
[[Motion Detection Systems]], [[Cloud Storage]], [[AI Person Detection]]
```

**Benefits**: Prevents overcrowding research note with 50+ direct links; creates navigable hierarchy

---

### 3. Ontological Linking (Relationship Types)

**Define relationship types between notes:**

#### Part-Whole Relationships (Composition)
```markdown
[[Security Camera]] contains:
- [[Camera Sensor]] (part-of)
- [[Night Vision Module]] (part-of)
- [[Motion Sensor]] (part-of)
- [[Audio System]] (part-of)
```

#### Instance-Of Relationships (Classification)
```markdown
[[Aqara Video Doorbell]] is an instance of:
- [[Smart Doorbell]] (instance-of)
- [[HomeKit Device]] (instance-of)
- [[WiFi-Connected Device]] (instance-of)
```

#### Causal Relationships (Influence)
```markdown
[[Caffeine Intake]] influences:
- [[Sleep Quality]] (decreases)
- [[Alertness]] (increases)
- [[Long-Term Health]] (affects, controversial)
```

#### Temporal Relationships (Succession)
```markdown
[[Research v2.0]] supersedes [[Research v1.0]]
[[Product Gen 2]] replaces [[Product Gen 1]]
[[Updated Guidelines 2025]] obsoletes [[Old Guidelines 2020]]
```

#### Comparative Relationships
```markdown
[[Product A]] compared to [[Product B]]:
- Superior in: [[Video Quality]], [[Battery Life]]
- Inferior in: [[Price]], [[App Interface]]
- Equivalent in: [[Reliability]], [[Customer Support]]
```

**Implementation in Research Notes**:
```markdown
## Relationships

**Part-Whole**:
- This product contains: [[HomeKit Chip]], [[Camera Module]], [[Battery Pack]]

**Instance-Of**:
- This is a: [[Smart Doorbell]], [[HomeKit Device]], [[Battery-Powered Device]]

**Causal**:
- Using this product improves: [[Home Security]], [[Package Theft Prevention]]

**Comparative**:
- Better than: [[Competitor A]] (video quality), [[Competitor B]] (battery life)
- Worse than: [[Competitor C]] (price)
```

---

### 4. Multi-Dimensional Tagging System

**Go beyond simple tags to multi-faceted classification:**

**Hierarchical Tags** (use `/` for hierarchy):
```yaml
tags:
  # Domain Hierarchy
  - domain/product/electronics/smart-home/security/doorbell

  # Research Characteristics
  - research/deep                    # depth
  - research/cross-cultural          # methodology
  - research/comparative             # type

  # Confidence & Quality
  - confidence/high
  - source-count/comprehensive
  - evidence-level/strong

  # Geographic Scope
  - geography/global
  - geography/us
  - geography/korea
  - geography/japan

  # Temporal Classification
  - temporal/evergreen               # vs time-sensitive
  - temporal/stable                  # decay rate: slow

  # Lifecycle Status
  - lifecycle/active                 # vs archived/deprecated
  - lifecycle/monitored              # has active monitoring

  # Content Type
  - content/product-review
  - content/buying-guide
  - content/comparison
```

**Tag Query Examples**:
```markdown
## Find All Active Product Research
```query
tag:#research tag:#domain/product
tag:#lifecycle/active
-tag:#lifecycle/archived
```

## Find High-Confidence Smart Home Research
```query
tag:#domain/product/smart-home
tag:#confidence/high
sort:last_updated desc
limit:10
```
```

---

### 5. Bidirectional Link Audit & Backlink Creation

**Ensure research is discoverable from existing notes:**

**Step 1: Identify Key Entities**
Extract all important entities from research:
- Product names, brand names
- Technologies, protocols (e.g., "HomeKit", "Matter", "Thread")
- Concepts (e.g., "motion detection", "cloud storage")

**Step 2: Search Vault for Mentions**
```
For each key entity:
1. Glob: pattern="**/*{entity}*.md"
2. Grep: pattern="{entity}" (case-insensitive)
3. Identify existing notes mentioning this entity
```

**Step 3: Add Forward Links from Existing Notes**
If existing note mentions "HomeKit" but doesn't link to new research:
```markdown
# Existing Note: Home Automation Setup

When choosing HomeKit devices, consider compatibility...

See also: [[Best Smart Doorbell 2025]] for in-depth HomeKit doorbell analysis  ← ADD THIS
```

**Step 4: Add Backward Links in Research Note**
```markdown
## Related Context

This research builds on:
- [[HomeKit Ecosystem Overview]] - provides HomeKit background
- [[Smart Home Security Principles]] - security framework used here
- [[Previous Doorbell Research v1.0]] - this supersedes that research
```

**Step 5: Generate "See Also" Sections**
```markdown
## See Also

**Related Products**:
- [[Smart Lock Research]] - complementary security device
- [[Security Camera Comparison]] - alternative/additional option

**Related Guides**:
- [[HomeKit Setup Guide]] - implementation context
- [[Smart Home Network Design]] - infrastructure requirements

**Related Concepts**:
- [[Motion Detection Technology]] - core technology explained
- [[Cloud vs Local Storage]] - architecture decision framework
```

---

### 6. MOC (Map of Content) Auto-Generation

**When research creates >5 related notes, generate MOC for navigation:**

**❌ MOC Filename Rule - NEVER use `README.md`:** Always name MOCs after the topic itself (e.g., `Smart-Home-Security-MOC.md`, `Espresso-Gear-MOC.md`, `Thin-Film-Deposition-MOC.md`). Multiple folders all containing `README.md` make searching difficult outside Obsidian (grep, find, Spotlight, file explorers all surface ambiguous matches). The filename must be unique and descriptive enough that a search result without folder context still tells you what the MOC is about.

**MOC Structure**:
```markdown
# [[Smart Home Security]] - MOC

> [!info] Map of Content
> Central hub for all smart home security research, products, and guides.
> Last updated: YYYY-MM-DD

---

## Overview

This MOC organizes {X} notes across {Y} categories related to smart home security.

---

## Core Research Notes

### Smart Doorbells (8 notes)
- [[Best Smart Doorbell 2025]] - ⭐⭐⭐ (updated 2025-01-15)
- [[Smart Doorbell Security Analysis]] - ⭐⭐ (2024-08-10)
- [[Battery vs Wired Doorbells]] - ⭐⭐⭐ (2024-12-01)
- [[Doorbell Cloud Storage Comparison]] - ⭐⭐ (2024-11-15)
- ...

### Smart Locks (12 notes)
- [[Best HomeKit Smart Lock 2025]] - ⭐⭐⭐ (updated 2025-01-10)
- [[Smart Lock Security Vulnerabilities]] - ⭐⭐⭐ (2024-09-20)
- ...

### Security Cameras (15 notes)
- ...

---

## Technologies & Protocols

### Communication Protocols
- [[HomeKit Secure Video]] - How HSV works
- [[Matter Protocol]] - New unified standard
- [[Thread Networking]] - Low-power mesh networking

### Core Technologies
- [[Motion Detection Algorithms]]
- [[AI Person Detection]]
- [[Cloud Storage Encryption]]

---

## Buying Guides & Frameworks

- [[Smart Home Security Buying Framework]] - Decision methodology
- [[Security Device Compatibility Matrix]] - Cross-device compatibility
- [[Smart Home Security Budget Guide]] - Recommendations by price tier

---

## Cross-Cutting Concerns

- [[Smart Home Privacy Principles]]
- [[Network Security Best Practices]]
- [[Power Backup Strategies]]
- [[Multi-Device Integration Patterns]]

---

## Manufacturers & Brands

- [[Logitech Circle View]] - Brand research
- [[Aqara]] - Brand research
- [[Eve Systems]] - Brand research

---

## Dynamic Queries

### Recently Updated Research
```query
path:"Smart-Home-Security/"
tag:#research
sort:last_updated desc
limit:10
```

### High-Confidence Active Research
```query
path:"Smart-Home-Security/"
tag:#confidence/high
tag:#lifecycle/active
```

---

## External Resources

- [HomeKit News](https://homekitnews.com) - Industry updates
- [r/HomeKit](https://reddit.com/r/HomeKit) - Community discussions
- [Matter Specification](https://csa-iot.org/all-solutions/matter/) - Official docs

---

## Maintenance

**Last Review**: YYYY-MM-DD
**Next Review**: YYYY-MM-DD (6 months)
**MOC Version**: 2.1
```

**MOC Generation Triggers**:
- >5 notes in same domain → Create domain MOC
- >10 notes on same product category → Create category MOC
- >15 notes across related domains → Create super-MOC

**MOC Hierarchy**:
```
[[Smart Home MOC]]               ← Super-MOC
    ↓
[[Smart Home Security MOC]]      ← Domain MOC
    ↓
[[Smart Doorbells MOC]]          ← Category MOC
    ↓
[[Best Smart Doorbell 2025]]     ← Research Note
```

---

### 7. Block References for Key Findings

**Use block references to create atomic, reusable insights:**

**Step 1: Add Block IDs to Key Findings**
```markdown
The Logitech Circle View achieved the highest video quality score (9/10) across all tested doorbells, with superior night vision and HDR performance. ^top-video-quality

Battery-powered doorbells showed 15% higher failure rates compared to wired alternatives, primarily due to battery degradation and weather exposure. ^battery-failure-rate

HomeKit Secure Video requires iCloud+ subscription ($0.99/month minimum), adding $12/year to total cost of ownership. ^hsv-cost
```

**Step 2: Reference Blocks from Other Notes**
```markdown
# Home Security Budget Planning

## Ongoing Costs

Smart doorbells with cloud storage require subscriptions:
- ![[Best Smart Doorbell 2025#^hsv-cost]]  ← Embedded

This adds up over a 5-year ownership period.
```

**Step 3: Link to Blocks for Citations**
```markdown
According to [[Best Smart Doorbell 2025#^top-video-quality]], the Logitech Circle View has the best video quality.

Reliability concerns: [[Best Smart Doorbell 2025#^battery-failure-rate]]
```

**Block Reference Best Practices**:
- Add block IDs to: key findings, statistics, recommendations, counterarguments
- Use descriptive block IDs: `^hsv-cost` not `^block-1`
- Embed (`![[]]`) for full content, link (`[[]]`) for citations
- Limit to 5-10 blocks per research note (most important findings only)

---

### 8. Dynamic Query Blocks for Living MOCs

**Create self-updating sections using Obsidian queries:**

**Auto-Update Related Research**:
````markdown
## Related Smart Home Research (Auto-Updated)

```query
tag:#research tag:#domain/smart-home
-tag:#lifecycle/archived
-file:"{{CURRENTFILE}}"
sort:confidence_score desc
limit:10
```
````

**Auto-Update Recent Additions**:
````markdown
## Recently Added (Last 30 Days)

```query
tag:#domain/product/smart-home
created:[now-30d TO now]
sort:created desc
```
````

**Auto-Update Needs Review**:
````markdown
## Research Needing Review

```query
tag:#research tag:#lifecycle/active
WHERE review_date < date(today)
sort:review_date asc
```
````

**Benefits**:
- MOCs stay current without manual updates
- Discover connections automatically
- Surface old research needing review

---

### 9. Knowledge Graph Connectivity Metrics

**Measure and optimize graph connections:**

**Link Density Calculation**:
```
For each research note:
- Count outgoing links (to other notes)
- Count incoming links (backlinks from other notes)
- Calculate: Link Density = (Outgoing + Incoming) / Average for vault

Target: Link Density ≥ 1.5 (well-connected)
Warning: Link Density < 0.5 (isolated note - needs more links)
```

**Connection Quality Assessment**:
```markdown
## Graph Connectivity Report

**Outgoing Links**: 23
- To concepts: 8
- To related research: 12
- To MOCs: 3

**Incoming Links (Backlinks)**: 15
- From related research: 10
- From MOCs: 3
- From guides: 2

**Link Density**: 1.9 (above target ✓)

**Orphan Risk**: Low (well-connected)
```

**Optimization Actions**:
- If Link Density < 0.5: Add more conceptual links, add to MOCs
- If only outgoing links (no backlinks): Update related notes to reference this research
- If only incoming links (few outgoing): Entity-link key concepts mentioned

---

### 10. Graph Visualization Preparation

**Structure notes for Obsidian Graph View:**

**Use Colors for Node Types**:
```yaml
# In .obsidian/graph.json (vault settings)
{
  "colorGroups": [
    {"query": "tag:#research", "color": "blue"},
    {"query": "tag:#concept", "color": "green"},
    {"query": "tag:#MOC", "color": "purple"},
    {"query": "tag:#confidence/high", "color": "gold"}
  ]
}
```

**Structure for Readable Graph**:
- Research notes (blue) link to concepts (green)
- Concepts link to MOCs (purple)
- High-confidence research highlighted (gold)
- Creates visual hierarchy in graph view

---

### Phase 9 Summary Checklist

After completing Phase 9, verify:

- [ ] Enhanced frontmatter with confidence breakdown, tags, aliases
- [ ] Semantic clusters identified, hub notes created
- [ ] Ontological relationships documented (part-of, instance-of, causal)
- [ ] Multi-dimensional tags applied (domain, confidence, temporal, lifecycle)
- [ ] Bidirectional links created (forward + backward)
- [ ] MOC generated if >5 related notes exist
- [ ] Block IDs added to key findings (5-10 blocks)
- [ ] Dynamic query blocks added to MOCs
- [ ] Link density ≥ 1.5 (well-connected)
- [ ] Related notes updated to reference new research

**Result**: Research note is fully integrated into knowledge graph, discoverable from multiple entry points, and contributes to vault-wide knowledge network.

#### Phase 10: Final Packaging with Confidence Metrics
1. Structure the final research note:
   ```markdown
   # {Research Topic}

   ## Executive Summary
   - Key findings with confidence ratings ⭐⭐⭐
   - Consensus recommendations
   - Critical uncertainties

   ## Research Methodology
   - Sources consulted: [count]
   - Confidence score: [0.XX]
   - Last updated: [date]

   ## Detailed Findings
   [Structured by sub-topics with wiki links]

   ## Cross-Cultural Analysis
   - Western consensus: [summary]
   - Asian consensus: [summary]
   - Regional differences: [analysis]

   ## Decision Framework
   [Comparison matrices, decision trees]

   ## Confidence Analysis
   - High confidence (⭐⭐⭐): [claims]
   - Moderate confidence (⭐⭐): [claims]
   - Low confidence (⭐): [claims]
   - Unresolved questions: [list]

   ## Sources & Citations
   [Structured bibliography with credibility scores]

   ## Future Monitoring
   - Evolving aspects to track
   - Recommended review date
   - Alert triggers for updates
   ```

2. Generate supplementary notes:
   - MOC for complex topics
   - Decision matrix as separate note
   - Source evaluation table
   - Glossary for technical terms

#### Phase 10.5: Research Maintenance & Monitoring Plan

After completing the research note, establish a maintenance strategy to ensure long-term value and accuracy.

**1. Temporal Classification**

Classify research based on expected validity duration:

| Classification | Validity Period | Examples | Review Frequency |
|---------------|-----------------|----------|------------------|
| **Evergreen** | 5+ years | Fundamental concepts, proven methodologies, scientific principles | Every 2-3 years |
| **Stable** | 1-2 years | Established product categories, best practices, mature technologies | Every 6-12 months |
| **Dynamic** | 6-12 months | Product recommendations, current models, pricing, emerging tech | Every 3-6 months |
| **Volatile** | 1-3 months | Deals, inventory, rapidly evolving fields, breaking research | Every 1-3 months |

Add temporal classification to frontmatter:
```yaml
temporal_classification: "Dynamic"  # or Evergreen, Stable, Volatile
validity_period: "6-12 months"
next_review_date: "2025-07-15"
```

**2. Update Triggers & Monitoring Plan**

Define specific triggers that should prompt research updates:

```yaml
monitoring_plan:
  review_schedule: "every 6 months"

  alert_triggers:
    critical:  # Immediate review required
      - "Product recall or safety alert"
      - "Major security vulnerability discovered"
      - "Regulatory ban or restriction"
      - "Company bankruptcy or acquisition"

    high_priority:  # Review within 2 weeks
      - "Major new study (>500 citations)"
      - "Price drops >25%"
      - "New category leader (>10% higher rating)"
      - "Significant algorithm/platform change"

    medium_priority:  # Review within 1-2 months
      - "Multiple user reports of issues"
      - "Better alternative released"
      - "Pricing changes >10%"
      - "Feature updates to recommended products"

    low_priority:  # Review at next scheduled interval
      - "Minor updates or improvements"
      - "Small price fluctuations (<10%)"
      - "Incremental research additions"

  monitoring_sources:
    automated:
      - "Google Alerts: [key product names], [key terms]"
      - "Reddit saved searches: r/[relevant subreddit] [keywords]"
      - "Price tracking: CamelCamelCamel / Keepa alerts"
      - "RSS feeds: [relevant blogs/news sites]"

    manual:
      - "Monthly check: Top 3 sources from original research"
      - "Quarterly review: Amazon/Coupang review trends"
      - "Annual deep-dive: Full research update"
```

**3. Research Versioning Strategy**

Implement semantic versioning for research notes:

**Version Format**: `MAJOR.MINOR.PATCH`
- **MAJOR** (1.0 → 2.0): Fundamental change in conclusions, new category emerged, complete re-research
- **MINOR** (1.0 → 1.1): Significant updates (new products, updated pricing, additional sources)
- **PATCH** (1.0.1 → 1.0.2): Minor corrections (typos, small clarifications, link fixes)

Add version tracking to frontmatter:
```yaml
research_version: 2.1
version_history:
  - version: 1.0
    date: 2025-01-15
    changes: "Initial comprehensive research"
    confidence: 0.85
    sources: 47

  - version: 1.1
    date: 2025-03-20
    changes: "Updated pricing, added 8 new sources"
    confidence: 0.85
    sources: 55

  - version: 2.0
    date: 2025-06-10
    changes: "Major revision - new Matter protocol support emerged, re-evaluated all products"
    confidence: 0.90
    sources: 68

  - version: 2.1
    date: 2025-07-05
    changes: "Minor corrections to compatibility matrix"
    confidence: 0.90
    sources: 68
```

Add changelog section to research note:
```markdown
## Version History

### v2.1 (2025-07-05) - Current
- 🔧 Fixed: Compatibility matrix for Thread border routers
- 📝 Clarified: HomeKit Secure Video requirements
- **Confidence**: 0.90 (unchanged)

### v2.0 (2025-06-10) - Major Update
- ✨ New: Matter protocol analysis (8 products added)
- 📊 Updated: All pricing and availability
- 🔄 Re-evaluated: Top 5 recommendations based on Matter support
- 📈 **Confidence**: 0.85 → 0.90 (+0.05)
- **Impact**: Recommendation changes for future-proofing

### v1.1 (2025-03-20)
- 💰 Updated: Pricing across all products
- 📚 Added: 8 new expert sources
- **Confidence**: 0.85 (stable)

### v1.0 (2025-01-15) - Initial Research
- 🎯 Initial comprehensive research
- 📊 47 sources analyzed
- **Confidence**: 0.85
```

**4. Confidence Decay Modeling**

Project how confidence degrades over time based on temporal classification:

```yaml
confidence_decay:
  initial_confidence: 0.85
  initial_date: "2025-01-15"

  projections:
    - date: "2025-04-15"  # +3 months
      projected_confidence: 0.83
      reason: "Minor drift - pricing and availability changes expected"

    - date: "2025-07-15"  # +6 months
      projected_confidence: 0.78
      reason: "Moderate drift - new models likely released, recommendations may be outdated"

    - date: "2026-01-15"  # +12 months
      projected_confidence: 0.65
      reason: "Major drift - product lifecycle changes, significant new research likely available"

  decay_formula: "confidence(t) = initial_confidence × (0.98 ^ months_elapsed)"
  recommended_action: "Review in 6 months (2025-07-15)"
```

Add visual decay indicator to research note:
```markdown
## Confidence Over Time

**Current Confidence**: ⭐⭐⭐ (0.85) as of 2025-01-15

**Projected Decay** (Dynamic research, 6-12 month validity):
```
1.0 |
    |
0.8 | ●───────○───────○
    |          ╲       ╲
0.6 |           ╲       ●
    |            ╲
    |_________________________________
    Now      +3mo    +6mo    +12mo
    0.85     0.83    0.78    0.65
             ↑                ↑
          stable      review recommended
```

⚠️ **Action Required**: Review recommended in 6 months (2025-07-15)
```

**5. Deprecation Workflow**

When research becomes significantly outdated or superseded:

**Step 1: Assess Deprecation**
- Confidence decayed below 0.60
- Major conclusions invalidated (>30% of recommendations no longer apply)
- Better research available
- Topic no longer relevant

**Step 2: Mark as Deprecated**

Update frontmatter:
```yaml
lifecycle: deprecated
deprecated_date: "2025-12-15"
deprecation_reason: "Superseded by v3.0 - new Matter protocol standard fundamentally changed landscape"
replacement_note: "[[Smart Doorbell Research v3.0]]"
```

Add banner to top of note:
```markdown
> [!warning] ⚠️ Deprecated Research
> **This research is outdated as of 2025-12-15**
>
> **Reason**: New Matter protocol standard fundamentally changed product landscape
>
> **See Updated Research**: [[Smart Doorbell Research v3.0]]
>
> This note is preserved for historical reference only. Do not rely on recommendations below.
```

**Step 3: Update Cross-References**
- Remove from active MOCs (move to "Archived Research" section)
- Update all incoming links to point to replacement note
- Add redirection notice to related notes

**Step 4: Preserve for Historical Reference**
- Tag: `lifecycle/deprecated`
- Move to `/Archive/` folder (optional)
- Keep in vault for:
  - Historical context
  - Understanding evolution of topic
  - Version comparison
  - Learning from past analysis

**6. Living Document Indicators**

Add dynamic elements to keep research current:

**Staleness Warning** (auto-calculated):
```markdown
> [!info] Research Age: 6 months
> **Last Updated**: 2025-01-15 (6 months ago)
> **Projected Confidence**: 0.78 (↓ 0.07 from initial)
>
> **Status**: 🟡 Review Recommended
>
> **Suggested Actions**:
> - [ ] Verify top 3 product recommendations still available
> - [ ] Check for new models released in last 6 months
> - [ ] Update pricing for all recommended products
> - [ ] Review recent Amazon/Coupang reviews for issues
> - [ ] Check for safety recalls or alerts
>
> **Next Scheduled Review**: 2025-07-15 (in 2 weeks)
```

**Update Checklist Template**:
```markdown
## Update Checklist (for future reviews)

### Quick Update (15-30 min)
- [ ] Verify all product links still active
- [ ] Update pricing for top 5 recommendations
- [ ] Scan for major recalls or safety alerts
- [ ] Check top 3 sources for significant changes
- [ ] Update "Last Reviewed" date

### Standard Update (1-2 hours)
- [ ] All Quick Update items
- [ ] Review recent Reddit/forum discussions (last 3-6 months)
- [ ] Check for new highly-rated products (>4.5 stars, >500 reviews)
- [ ] Re-analyze top 3 products in detail
- [ ] Update confidence scores
- [ ] Increment version (MINOR)

### Major Update (3-4+ hours)
- [ ] All Standard Update items
- [ ] Launch 2-3 targeted subagents for gap areas
- [ ] Re-evaluate all recommendations
- [ ] Update comparative matrices
- [ ] Refresh cross-cultural analysis
- [ ] Full confidence recalculation
- [ ] Increment version (MAJOR)
```

**7. Maintenance Plan Summary**

Add to research note frontmatter:
```yaml
maintenance_plan:
  temporal_classification: "Dynamic"
  next_review_date: "2025-07-15"
  review_type: "Standard Update"
  estimated_effort: "1-2 hours"
  monitoring_active: true
  alerts_configured: ["Google Alerts", "Price tracking", "Reddit saved search"]
```

Add to research note:
```markdown
## Maintenance Plan

**Classification**: Dynamic Research (6-12 month validity)
**Next Review**: 2025-07-15 (Standard Update, 1-2 hours)

**Active Monitoring**:
- ✅ Google Alerts: "Aqara Video Doorbell", "smart doorbell 2025"
- ✅ Price tracking: CamelCamelCamel alerts for top 5 products
- ✅ Reddit saved: r/HomeKit "video doorbell"

**Confidence Decay**: 0.85 → 0.78 (projected at +6 months)
**Recommendation**: Review in 6 months, major update likely needed at 12 months
```

**Phase 10.5 Complete**: Research now has explicit maintenance strategy ensuring long-term value and accuracy.
