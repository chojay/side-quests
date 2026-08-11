# Error Handling & Recovery

Part of the `obsidian-deep-research` skill. Read this file when any source, agent, or
phase fails during research.

## Contents

- Error Classification & Response Strategy
  - Level 1: Transient Errors (Automatic Retry)
  - Level 2: Source-Specific Errors (Fallback Chain)
  - Level 3: Structural Errors (Graceful Degradation), incl. Conflicting Evidence and
    Cross-Cultural Analysis fallbacks
  - Level 4: Critical Errors (Abort with Partial Results), incl. Research Infeasible
    template
- Error Reporting in Research Notes (Research Limitations section, Error Summary
  Dashboard / Research Quality Dashboard)
- Error Prevention Best Practices
- When to Abort vs. Continue
- Error Recovery Checklist

## Error Handling & Recovery

Research sessions will encounter various failures. Handle them systematically using this 4-level error classification framework.

### Error Classification & Response Strategy

#### Level 1: Transient Errors (Automatic Retry)

**Definition**: Temporary failures likely to succeed on retry.

**Examples**:
- Network timeouts (connection drops, DNS failures)
- Rate limiting (429 errors, "too many requests")
- Server errors (503 Service Unavailable, 502 Bad Gateway)
- Temporary bot detection (soft CAPTCHAs)

**Response Strategy**:
```
Retry with exponential backoff:
  Attempt 1: Immediate
  Attempt 2: Wait 2 seconds
  Attempt 3: Wait 4 seconds
  Attempt 4: Wait 8 seconds

If all retries fail: Escalate to Level 2 (Source-Specific fallback)
```

**Implementation Example**:
```markdown
Attempting WebFetch for Reddit post...
❌ Timeout after 10s
⏱️ Retry 1 (after 2s): ❌ Timeout
⏱️ Retry 2 (after 4s): ✅ Success

Source retrieved successfully after 2 retries.
```

#### Level 2: Source-Specific Errors (Fallback Chain)

**Definition**: Failures specific to a source type or platform requiring alternative access methods.

**Examples**:
- JavaScript-rendered content (WebFetch fails, needs browser)
- Paywalls (NYTimes, WSJ, academic journals)
- Geo-blocking (content restricted by region)
- Anti-bot measures (Cloudflare, reCAPTCHA)
- Login-required content

**Response Strategy - Fallback Chains by Source Type**:

**Reddit**:
```
1. WebFetch (direct API-style access)
   ↓ fails
2. claude-in-chrome (browser automation with full rendering)
   ↓ fails
3. WebSearch for cached/archived version (Google Cache, Archive.today)
   ↓ fails
4. Document as unavailable, use alternative sources
```

**Amazon/Coupang Product Pages**:
```
1. WebFetch (direct page fetch)
   ↓ fails (bot detection, dynamic pricing)
2. claude-in-chrome with pagination pattern for reviews
   ↓ fails (CAPTCHA, login required)
3. Use Amazon API alternatives (Keepa, CamelCamelCamel for pricing)
   ↓ fails
4. Document limitation, use available data with reduced confidence
```

**Naver (Korean sources)**:
```
1. WebFetch (direct access)
   ↓ fails (encoding issues, dynamic content)
2. naver-korean-search skill (specialized Naver API)
   ↓ fails
3. claude-in-chrome with Korean language support
   ↓ fails
4. Document as inaccessible, note in cross-cultural analysis limitations
```

**Academic Papers**:
```
1. WebFetch (direct journal access)
   ↓ fails (paywall)
2. Search for preprint (arXiv, bioRxiv, ResearchGate)
   ↓ fails
3. Search for author-posted or institutional-repository copies (Google Scholar "All versions", university sites)
   ↓ fails
4. Use abstract + citations only, flag as "full text unavailable"
```

**YouTube Videos**:
```
1. WebFetch (metadata + transcript)
   ↓ fails (geo-blocked, deleted)
2. youtube-obsidian-saver skill (specialized extraction)
   ↓ fails
3. Search for mirrors, re-uploads
   ↓ fails
4. Document as unavailable, find alternative video sources
```

**General Paywalled Content**:
```
1. WebFetch (attempt direct access)
   ↓ fails (paywall)
2. Check Internet Archive Wayback Machine
   ↓ fails (not archived)
3. Search for author's personal site / preprint version
   ↓ fails
4. Use article summary from WebSearch results, cite properly with limitation
```

**Implementation Example**:
```markdown
Attempting to access NYTimes article on smart thermostats...

WebFetch: ❌ Paywall detected
Fallback 1: Internet Archive → ❌ Not archived
Fallback 2: Author's site search → ❌ Not found
Fallback 3: Google News summary → ✅ Partial content available

**Result**: Using summarized content from Google News. Full article unavailable due to paywall.
**Impact**: Confidence reduced by 5% for this source cluster.
```

#### Level 3: Structural Errors (Graceful Degradation)

**Definition**: Failures affecting research structure or quality, but partial results are salvageable.

**Examples**:
- Insufficient sources found (<5 quality sources)
- Contradictory evidence without resolution
- Specific research category failed (e.g., academic sources unavailable but product reviews abundant)
- Cross-cultural validation impossible (Korean sources inaccessible)
- Key expert source unavailable

**Response Strategy - Graceful Degradation**:

**Insufficient Sources (<5 quality sources)**:
```
1. Expand search keywords (add synonyms, related terms)
2. Broaden source types (if focused on academic, add expert blogs)
3. Extend geographic scope (add European, Asian sources)
4. Lower credibility threshold slightly (0.80 → 0.70)

If still insufficient:
- Proceed with available sources
- Reduce overall confidence by 15-20%
- Document limitation prominently
- Tag research as "limited-sources"
```

**Contradictory Evidence**:
```
1. Document all conflicting viewpoints
2. Attempt triangulation with additional neutral sources
3. Present both sides with confidence scores for each

Research note structure:
## Conflicting Evidence

**Claim A** (⭐⭐ - 60% of sources):
[Evidence for A]

**Claim B** (⭐⭐ - 40% of sources):
[Evidence for B]

**Analysis**: Unable to definitively resolve. Recommend [approach based on use case].
**Confidence**: Reduced to ⭐⭐ due to unresolved contradiction.
```

**Research Category Failed**:
```
Example: Academic research unavailable, but product research abundant

1. Acknowledge gap prominently
2. Continue with available categories
3. Adjust research depth classification (Deep → Standard)
4. Reduce confidence for affected claims

Research note:
> [!warning] Limited Academic Validation
> **Gap**: No peer-reviewed studies found on long-term air purifier health effects.
> **Alternative Evidence**: 2,340 user reviews + 8 expert recommendations analyzed instead.
> **Confidence Impact**: Claims about safety reduced to ⭐⭐ (moderate) pending academic research.
```

**Cross-Cultural Validation Failed**:
```
Example: Korean sources inaccessible due to geo-blocking

1. Document limitation
2. Continue with Western sources
3. Note cultural bias risk
4. Reduce cross-cultural confidence dimension to 0.00

Research note:
## Cross-Cultural Analysis

**Western Consensus**: [detailed analysis]
**Korean/Asian Consensus**: ❌ Unavailable (geo-blocking prevented access to Naver, Coupang)

**Limitation**: Recommendations may have Western bias. Korean usage patterns not validated.
**Confidence Impact**: Source Diversity: 0.85 → 0.60 (-0.25)
```

**Implementation Example**:
```markdown
Research on "Best air purifier" encountered structural issues:

1. ❌ Academic sources: Only 2 studies found (need 5+)
   → Expanded to specialist blogs, HVAC-professional recommendations
   → Found 8 additional expert sources

2. ⚠️ Korean sources: Naver geo-blocked
   → Used Coupang (accessible) + Korean Reddit
   → Partial cross-cultural validation achieved

**Final Status**:
- Sources: 47 (target: 40+) ✅
- Cross-cultural: Partial (Western + limited Korean) ⚠️
- Overall confidence: 0.85 → 0.78 (-0.07 due to Korean gap)
- Proceeding with graceful degradation
```

#### Level 4: Critical Errors (Abort with Partial Results)

**Definition**: Fundamental failures preventing meaningful research completion.

**Examples**:
- All web access failed (network completely down)
- Zero usable sources found (topic too niche, all sources inaccessible)
- All subagents failed or timed out
- Vault access failed (Obsidian vault inaccessible)
- Research question fundamentally unanswerable with available tools

**Response Strategy - Abort Gracefully**:

**Zero Usable Sources**:
```
After exhausting all fallbacks:

1. Document comprehensive search attempts
2. Provide "Research Infeasible" report
3. Suggest alternative approaches
4. Offer to help reformulate question

Research note (minimal):
# {Topic} - Research Infeasible

## Attempted Research (2025-01-15)

**Goal**: Find best smart air purifier supporting Thread protocol

**Search Attempts**:
- WebSearch: "air purifier Thread protocol" → 0 results
- WebSearch: "air purifier Matter protocol" → 3 results (none relevant)
- Amazon: "Thread air purifier" → 0 matching products
- Reddit r/HomeKit search: 0 discussions found
- Expert sources (Wirecutter, Consumer Reports): Topic not covered

**Conclusion**: As of Jan 2025, no air purifiers support Thread protocol.

**Alternative Recommendations**:
1. Research air purifiers with Matter support (emerging standard)
2. Research air purifiers with HomeKit support (established)
3. Wait 6-12 months for Thread adoption in the air purifier category

**Status**: ❌ Research aborted - insufficient data available
```

**All Web Access Failed**:
```
1. Verify network connectivity
2. Attempt basic connectivity test (WebFetch to google.com)
3. If network confirmed down:
   - Document error
   - Suggest user check network/firewall
   - Offer to retry when connectivity restored

Error message:
❌ **Critical Error**: All web access failed

**Diagnosis**: Network connectivity issue detected.
- WebFetch: All attempts timed out
- claude-in-chrome: Unable to load pages
- Basic connectivity test: Failed

**Action Required**:
1. Check internet connection
2. Verify firewall/proxy settings not blocking access
3. Retry research session when connectivity restored

**Session Status**: Aborted (no sources retrievable)
```

**Implementation Example**:
```markdown
Attempting research on "Best quantum air purifier"...

Search 1: WebSearch "quantum air purifier" → 0 results
Search 2: WebSearch "air purifier quantum computing" → 0 relevant results
Search 3: Amazon "quantum air purifier" → 0 products
Search 4: Reddit search → 0 discussions
Search 5: Expert sources → Topic not covered

**Critical Assessment**:
Topic appears to be based on misunderstanding. Quantum technology not applicable to air purifiers.

**Recommendation**:
Did you mean "best air purifier with advanced sensors"? I can research:
1. Air purifiers with high-accuracy particulate sensors
2. Air purifiers with AI-powered air quality detection
3. Smart air purifiers with air-quality history tracking

Would you like to reformulate the research question?

**Status**: ❌ Research aborted - topic not viable
```

### Error Reporting in Research Notes

When errors affect final research quality, document transparently:

#### Research Limitations Section

Add to every research note that encountered errors:

```markdown
## Research Limitations

### Sources Unavailable

**Paywalled Content**:
- ❌ Wirecutter full review (paywall) - Used preview + summary from WebSearch
- ❌ Consumer Reports detailed testing (paywall) - Cited aggregate scores only

**Geo-Restricted**:
- ❌ Coupang Korean reviews (geo-blocked) - Used Reddit r/Korea discussions as proxy
- ❌ Japanese Amazon.co.jp (region locked) - Cross-cultural validation limited to Western + limited Korean sources

**Technical Failures**:
- ❌ YouTube teardown video (deleted by creator) - Used cached transcript from Internet Archive
- ⚠️ Reddit thread (503 errors during scraping) - Retrieved partial content (80% of comments)

### Methodology Adjustments

**Confidence Reductions**:
- ⚠️ Reduced Source Diversity: 0.90 → 0.75 (-0.15) due to Korean source gap
- ⚠️ Reduced Temporal Relevance: 0.85 → 0.70 (-0.15) due to using 18-month-old cached content

**Scope Changes**:
- 🔄 Originally planned: 6 parallel agents → Actually launched: 4 agents (2 failed due to rate limiting)
- 🔄 Originally planned: Academic + Product research → Actually delivered: Product research only (academic sources unavailable)

**Impact Assessment**:
- **Overall Confidence**: 0.85 → 0.72 (-0.13)
- **Recommendation Strength**: High → Moderate
- **Cross-Cultural Validity**: Full → Partial (Western-centric bias possible)
```

#### Error Summary Dashboard

For research with significant errors, add dashboard:

```markdown
## Research Quality Dashboard

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| **Sources** | 40+ | 47 | ✅ Exceeded |
| **Source Quality** | >0.85 | 0.82 | ⚠️ Below target |
| **Cross-Cultural** | Full validation | Partial | ⚠️ Limited |
| **Temporal** | <6 months old | 60% <6mo, 40% >6mo | ⚠️ Mixed |
| **Confidence** | >0.85 | 0.72 | ❌ Below target |

**Overall Grade**: B (Good with limitations)

**Key Limitations**:
1. Korean sources inaccessible (geo-blocking)
2. Academic research unavailable (paywall + topic not studied)
3. Some sources outdated (18 months old)

**Recommendation**: Use with awareness of Western bias. Consider re-research in 6 months when:
- Geo-blocking may be resolved
- More recent sources available
- Academic research may emerge
```

### Error Prevention Best Practices

**Proactive Strategies**:

1. **Pre-flight Source Testing** (Phase 3.5):
   - Test 2-3 representative URLs before launching full research
   - Identify common failure modes early
   - Adjust strategy before expensive subagent orchestration

2. **Diverse Source Portfolios**:
   - Never rely on single source type
   - Spread risk across: Expert reviews, user reviews, academic, forums, videos
   - If one category fails, others provide fallback

3. **Geographic Redundancy**:
   - Plan for both US and international sources
   - If geo-blocking suspected, include VPN-friendly sources
   - Document regional access limitations early

4. **Tiered Credibility Sourcing**:
   - Always include mix of high (0.90+), medium (0.75-0.89), lower (0.60-0.74) credibility
   - If high-credibility sources fail, medium sources provide backup
   - Adjust confidence scores accordingly

5. **Checkpoint Early, Checkpoint Often**:
   - Save progress after each major phase
   - If session interrupted, partial results preserved
   - Enable resume from last checkpoint

### When to Abort vs. Continue

**Decision Matrix**:

| Sources Found | Source Quality | Cross-Cultural | Academic | Decision |
|---------------|----------------|----------------|----------|----------|
| 40+ | High (0.85+) | Full | Available | ✅ Continue (ideal) |
| 40+ | High | Partial | Unavailable | ✅ Continue (good) |
| 20-39 | Medium (0.70+) | Partial | Unavailable | ⚠️ Continue with reduced confidence |
| 10-19 | Medium | None | Unavailable | ⚠️ Continue, flag as "limited research" |
| <10 | Any | Any | Any | ❌ Abort - insufficient data |
| Any | Low (<0.60) | Any | Any | ❌ Abort - unreliable sources |
| 0 | N/A | N/A | N/A | ❌ Abort - no sources |

**Abort Checklist**:

Abort research if ANY of these conditions are true:
- [ ] Zero usable sources found after exhaustive search
- [ ] All sources below 0.60 credibility threshold
- [ ] Fundamental network/tool failure preventing access
- [ ] Research question unanswerable with available tools
- [ ] Estimated confidence would be <0.50 (unreliable)

**Continue with Degradation** if:
- [ ] At least 10 sources with 0.60+ credibility
- [ ] Projected confidence >0.60 (acceptable with limitations)
- [ ] Partial results still valuable to user
- [ ] Errors documented and limitations clear

### Error Recovery Checklist

After encountering errors, verify recovery:

```markdown
## Error Recovery Verification

- [ ] All error types classified (Level 1-4)
- [ ] Appropriate fallback strategies attempted
- [ ] Unavailable sources documented with reason
- [ ] Alternative sources used where possible
- [ ] Confidence scores adjusted for limitations
- [ ] Research Limitations section added to note
- [ ] Error impact quantified (confidence reduction calculated)
- [ ] User informed of research quality grade
- [ ] Recommendations adjusted for reduced confidence
- [ ] Monitoring plan includes re-check for failed sources
```

**Result**: Systematic error handling ensures partial results are salvaged, failures are documented transparently, and users understand research quality limitations.

