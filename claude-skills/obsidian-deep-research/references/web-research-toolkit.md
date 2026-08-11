# Web Research Toolkit

Part of the `obsidian-deep-research` skill (Implementation Guidelines). Read this file
during Phases 4-5: subagent orchestration best practices, browser automation patterns
and fallback chain, source citation format, and YouTube video integration.

### Subagent Orchestration Best Practices

**Mandatory Workflow:**
1. **ALWAYS start with Plan agent** - Never skip research planning
2. **Use Explore agent for vault searches** - Isolate file system operations
3. **Launch parallel agents in ONE message** - Critical for true parallelization
4. **Respect 10-agent concurrency limit** - Queue excess tasks automatically

**Agent Selection Guide:**

| Task | Subagent Type | Reason |
|------|---------------|--------|
| Research strategy design | `Plan` | Structured planning with architectural thinking |
| Vault exploration | `Explore` | Fast file pattern matching and code search |
| Web research | `general-purpose` | Autonomous multi-step web operations |
| Source validation | `general-purpose` | Independent fact-checking |
| Cross-cultural research | `general-purpose` | Parallel regional data gathering |

**Prompt Engineering for Subagents:**

Each subagent operates with isolated context. Provide COMPLETE instructions including:
- Specific topic/question to research
- Source types to prioritize
- Output format expected
- Credibility criteria to apply
- Geographic/cultural scope

### Browser Automation & Web Fetching Strategy

**⚠️ IMPORTANT: Use the following fallback chain for web content retrieval:**

#### Fallback Chain

1. **Primary - WebFetch** (fast, low overhead, preferred for simple pages)
2. **Secondary - the Claude-in-Chrome browser extension** (handles JavaScript, dynamic content, interactive elements)
3. **Tertiary - Manual Extraction** (document failure, provide URLs to user for review)

#### When to Use Browser Automation

Use `claude-in-chrome` MCP when:
- ✅ WebFetch fails (timeouts, rate limiting, JavaScript-rendered content)
- ✅ Need to interact with dynamic content (infinite scroll, "load more" buttons, pagination)
- ✅ Scraping review sites with complex layouts (Amazon reviews, Coupang with pagination)
- ✅ Capturing visual content (comparison charts, product images, infographics)
- ✅ Reading sites that block WebFetch but render normally in a logged-in session (Reddit, Dollar Tree, most retailer pages)

**Never** solve or bypass a CAPTCHA or bot-detection challenge. If a page presents one, stop and hand the URL to the user. Driving the user's real Chrome session usually avoids the challenge in the first place, which is the point of using it; defeating a challenge that does appear is out of scope.

#### Browser Automation Patterns

> **Note**: Paths like `/vault/assets/...` in the patterns below are illustrative placeholders. Real screenshot/asset paths must be absolute paths inside your actual vault; vault paths often contain spaces, so always quote paths in bash commands.

> **Note on `tabId=TAB`**: `TAB` is a placeholder for the numeric tab ID. Get a real one by calling `mcp__claude-in-chrome__tabs_context_mcp{createIfEmpty: true}` then `mcp__claude-in-chrome__tabs_create_mcp`, and substitute the integer it returns. Parallel research agents each need their own tab. Load all needed browser tools in a single `ToolSearch` call. See the `browser-access` skill for the full routing rule and troubleshooting.

**Pattern 1: Paginated Review Scraping**

Use for: Amazon reviews, Coupang reviews, Reddit comment threads

```
1. mcp__claude-in-chrome__navigate(tabId=TAB, url="[product page]")
2. mcp__claude-in-chrome__get_page_text(tabId=TAB)  # Get initial content
3. mcp__claude-in-chrome__computer(action="left_click", tabId=TAB, ref="see-all-reviews-button")  # Navigate to full reviews
4. mcp__claude-in-chrome__find(tabId=TAB, text="Customer reviews", timeout=5000)

5. Loop until no more pages:
   a. take_snapshot()  # Capture current page
   b. extract_reviews()  # Parse review data
   c. click(uid="next-page-button")  # Click pagination
   d. wait_for(text="Showing", timeout=3000)  # Wait for load
   e. Break if "next-page-button" is disabled or missing

6. Aggregate all reviews across pages
```

**Pattern 2: Dynamic Content Loading (Infinite Scroll)**

Use for: Reddit feeds, Twitter threads, Pinterest boards

```
1. navigate_page(url="[target URL]")
2. initial_snapshot = take_snapshot()

3. Loop 10 iterations (or until no new content):
   a. scroll(direction="down", scroll_amount=5)
   b. wait(duration=2)  # Allow content to lazy-load
   c. new_snapshot = take_snapshot()
   d. if new_snapshot == previous_snapshot: break  # No new content loaded
   e. previous_snapshot = new_snapshot

4. Aggregate all content from snapshots
```

**Pattern 3: Multi-Tab Comparison Research**

Use for: Parallel product comparison, price checking across retailers

```
1. tab1 = new_page(url="[Product A URL]")
2. tab2 = new_page(url="[Product B URL]")
3. tab3 = new_page(url="[Product C URL]")

4. For each tab in [tab1, tab2, tab3]:
   a. select_page(pageIdx=tab)
   b. take_snapshot(verbose=false)
   c. take_screenshot(filePath=f"/vault/assets/product-{tab}.png")
   d. extract_specs()  # Parse product specifications
   e. extract_price()  # Parse pricing information

5. create_comparison_matrix(all_data)
```

**Pattern 4: Visual Content Extraction**

Use for: Comparison charts, infographics, product images, floor plans

```
1. navigate_page(url="[review site with charts]")
2. find_element(query="comparison chart")  # Locate chart element
3. take_screenshot(
     uid="chart-element",
     filePath="/vault/assets/research-assets/comparison-chart.png"
   )
4. Embed in research note: ![[comparison-chart.png]]
5. Optional: Use OCR or manual description for accessibility
```

**Pattern 5: Form Interaction & Data Extraction**

Use for: Product configurators, price calculators, availability checkers

```
1. navigate_page(url="[product page]")
2. fill_form(elements=[
     {uid: "size-dropdown", value: "Large"},
     {uid: "color-dropdown", value: "Blue"},
     {uid: "quantity-input", value: "1"}
   ])
3. click(uid="calculate-price-button")
4. wait_for(text="Total Price")
5. take_snapshot()
6. extract_calculated_price()
```

#### Error Handling for Browser Automation

```
Try:
  1. WebFetch(url=target_url)

Catch timeout/rate_limit:
  2. Wait 5 seconds
  3. WebFetch(url=target_url) with increased timeout

Catch still_failing:
  4. claude-in-chrome fallback:
     - navigate_page(url=target_url)
     - wait(duration=3)
     - take_snapshot()

Catch browser_failure:
  5. Document unavailable source:
     - Add to research note: "❌ [Source Title] (URL) - Unavailable: {error}"
     - Continue with available sources
     - Reduce confidence score by 5-10%
```

#### Browser Automation Best Practices

**Performance:**
- Use `verbose=false` for snapshots to reduce token usage
- Prefer `take_snapshot()` over `take_screenshot()` for text content (much smaller)
- Close unused tabs with `close_page()` to free resources

**Reliability:**
- Always use `wait_for(text="...")` after navigation/clicks to ensure content loaded
- Set appropriate timeouts (3-5 seconds for fast sites, 10+ for slow international sites)
- Check for error messages in snapshots before proceeding

**Cost Management:**
- Browser automation uses ~2-3x more tokens than WebFetch
- Use judiciously for sources that genuinely require it
- Batch multiple extractions from same page to amortize navigation cost

### Source Citation Format

Use consistent citation formatting:
```markdown
**Reddit** (r/[subreddit], [date], n=[upvotes]): [finding]
**Wirecutter** ([date], [author]): [finding]
**Study** ([Authors, Year], n=[sample_size], p=[p-value]): [finding]
**Amazon** ([product], [# reviews], [avg rating]): [finding]
**YouTube** ([Channel], [views], [duration]): [finding with timestamp link]
```

### YouTube Video Integration

**MCP Server**: The `youtube-transcript` MCP server (jkawamoto) provides transcript extraction with pagination support.

> **Note**: The `youtube-transcript` MCP server is an **optional dependency**: it is not declared by this skill and may not be installed. If it is unavailable, invoke the `youtube-obsidian-saver` skill instead, which handles transcript extraction (including chunked retrieval for long videos).

**Handling Long Videos (>45 minutes)**:

For videos exceeding MCP token limits, use chunked retrieval:

1. **Request without timestamps first** (reduces tokens by 20-30%)
2. **Use pagination** via `next_cursor` parameter
3. **Combine chunks** in post-processing

**Chunked Retrieval Pattern**:
```python
# Use the chunked_transcript_retriever.py script bundled with the
# youtube-obsidian-saver skill (or simply invoke the youtube-obsidian-saver
# skill directly for transcript extraction):
python3 "$HOME/.claude/skills/youtube-obsidian-saver/scripts/chunked_transcript_retriever.py" "https://youtu.be/VIDEO_ID" \
  --output "/path/to/vault/Video-Title.md" \
  --chunk-size 15000
```

**Video Note Structure**:
```yaml
---
tags:
  - video/youtube
  - channel/{channel-slug}
  - research/source
video_id: {VIDEO_ID}
duration: {HH:MM:SS}
source: youtube
---
```

