---
name: find-and-test-coupons
description: >-
  Find coupon codes for a given retailer or product, then test them live on the
  retailer's website to verify they actually work. Searches multiple coupon
  aggregators (RetailMeNot, CouponFollow, Slickdeals, DontPayFull, Groupon) and
  social media (Reddit, Twitter/X) in parallel, extracts codes, navigates to the
  retailer's cart or checkout in the user's own Chrome browser, applies each coupon, and
  reports which codes work with exact discount amounts. Prioritizes recent
  codes (last 3 months). Use when the user asks to find coupons or promo codes
  for a retailer (e.g., "find me coupons for Target"), wants to verify whether
  a specific coupon code actually works before checkout, wants to compare
  discounts across multiple codes, or has items in a cart and wants to maximize
  savings before making a purchase.
---

# Find and Test Coupons Skill

## Purpose

This skill automates the process of finding, testing, and verifying coupon codes for any retailer. It searches multiple aggregator sites and social media in parallel, then actually tests each code on the retailer's website using the Claude-in-Chrome browser extension to verify which codes work.

**Workflow**: Search → Test → Verify → Report

## When to Use This Skill

Activate this skill when:
- User wants to find working coupon codes for a specific retailer
- User wants to verify if a coupon code actually works before checkout
- User asks "find me coupons for {retailer}"
- User wants to compare discounts across multiple coupon codes
- User has items in cart and wants to maximize savings

## Browser Setup (do this first)

This skill drives the user's real, logged-in Chrome via the Claude-in-Chrome extension. It does **not** use Chrome DevTools MCP or Playwright; all live browsing goes through the extension.

Before any navigation below:

1. Load the tools in ONE `ToolSearch` call:
   ```
   select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__browser_batch,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__find
   ```
2. Call `mcp__claude-in-chrome__tabs_context_mcp{createIfEmpty: true}`.
3. Call `mcp__claude-in-chrome__tabs_create_mcp` to get a fresh tab.

**`tabId=TAB` in every snippet below means the numeric tab ID from step 3.** Substitute the real integer. Each parallel subagent must create and use its **own** tab; sharing one tab ID across concurrent agents causes them to navigate each other's pages out from under one another.

Use `browser_batch` to pair navigate and read in one round trip rather than issuing them separately.

### Checkout safety (mandatory)

Testing coupons means operating a live cart. Hard limits:

- **Never complete a purchase.** Stop at the discount-applied state and report the number. Placing the order is the user's call, made explicitly in chat.
- **Never enter payment details, card numbers, or passwords.** If a step requires them, stop and tell the user.
- **Do not click "Place Order", "Buy Now", "Confirm Purchase", or equivalent** under any circumstances.
- Applying a promo code and reading the updated total is fine. Anything past that is not.

## 4-Phase Workflow

### Phase 1: Coupon Discovery (Parallel Subagents)

**CRITICAL: Launch 6-8 agents in a SINGLE message for parallel execution**

Search all major coupon sources simultaneously:

```
// Launch ALL agents in ONE message block:

Task(subagent_type="general-purpose", prompt="
RETAILMENOT SEARCH for {retailer}:
1. Navigate to https://www.retailmenot.com/{retailer} using the Claude-in-Chrome browser extension
2. mcp__claude-in-chrome__navigate(tabId=TAB, url='https://www.retailmenot.com/{retailer}')
3. mcp__claude-in-chrome__get_page_text(tabId=TAB)
4. Extract all visible coupon codes
5. Note: code, discount type (% or $), amount, expiration, terms
6. Return structured JSON list of codes")

Task(subagent_type="general-purpose", prompt="
COUPONFOLLOW SEARCH for {retailer}:
1. Navigate to https://couponfollow.com/{retailer}
2. mcp__claude-in-chrome__navigate(tabId=TAB, url='https://couponfollow.com/{retailer}')
3. mcp__claude-in-chrome__get_page_text(tabId=TAB)
4. Extract codes with verification status and success rates
5. Return structured JSON list: code, type, verified, success_rate")

Task(subagent_type="general-purpose", prompt="
SLICKDEALS SEARCH for {retailer}:
1. Navigate to https://slickdeals.net/coupons/{retailer}/
2. mcp__claude-in-chrome__navigate(tabId=TAB, url='https://slickdeals.net/coupons/{retailer}/')
3. mcp__claude-in-chrome__get_page_text(tabId=TAB)
4. Extract community-verified codes with upvotes/downvotes
5. Return structured JSON list: code, votes, last_verified")

Task(subagent_type="general-purpose", prompt="
DONTPAYFULL SEARCH for {retailer}:
1. Navigate to https://www.dontpayfull.com/at/{retailer}
2. mcp__claude-in-chrome__navigate(tabId=TAB, url='https://www.dontpayfull.com/at/{retailer}')
3. mcp__claude-in-chrome__get_page_text(tabId=TAB)
4. Extract coupon codes and deals
5. Return structured JSON list: code, type, amount, verified")

Task(subagent_type="general-purpose", prompt="
GROUPON SEARCH for {retailer}:
1. Navigate to https://www.groupon.com/coupons/{retailer}
2. mcp__claude-in-chrome__navigate(tabId=TAB, url='https://www.groupon.com/coupons/{retailer}')
3. mcp__claude-in-chrome__get_page_text(tabId=TAB)
4. Extract coupons and promotional codes
5. Return structured JSON list: code, type, amount, expiration")

Task(subagent_type="general-purpose", prompt="
REDDIT SEARCH for {retailer} (RECENT ONLY - last 3 months):
1. WebSearch: 'site:reddit.com {retailer} promo code {current_month} {current_year}'
2. WebSearch: 'site:reddit.com {retailer} coupon working {current_year}'
3. For each result, extract mentioned codes from post/comments
4. Prioritize posts with high upvotes and recent activity
5. Return structured list: code, source_url, post_date, upvotes")

Task(subagent_type="general-purpose", prompt="
TWITTER/X SEARCH for {retailer} (RECENT ONLY):
1. WebSearch: 'site:twitter.com OR site:x.com {retailer} promo code {current_month}'
2. WebSearch: '{retailer} discount code twitter {current_year}'
3. Extract any mentioned codes
4. Return structured list: code, source_url, tweet_date")

Task(subagent_type="general-purpose", prompt="
GENERAL WEB SEARCH for {retailer}:
1. WebSearch: '{retailer} promo code working {current_month} {current_year}'
2. WebSearch: '{retailer} coupon code verified {current_year}'
3. Visit top 3 non-aggregator results
4. Extract any unique codes not found on major sites
5. Return structured list with source URLs")
```

**Recency Priority**: Weight codes from last 3 months higher

**Code Extraction Patterns**:
- All caps: `[A-Z0-9]{4,20}` (e.g., SAVE20, FREESHIP)
- Mixed case: `[A-Za-z0-9-_]{6,25}` (e.g., Welcome-15Off)
- Retailer-specific: `{RETAILER}-\d{2,4}` (e.g., TARGET2024)

### Phase 2: Coupon Testing (Sequential)

**Before testing**: Check `references/retailer-patterns.md` for known checkout URLs, coupon field selectors, apply-button patterns, and retailer quirks (Amazon, Target, Walmart, Best Buy, Costco, Home Depot, Kohl's, Macy's, Nike, Sephora) to skip field discovery.

**Cart Setup Modes:**

| Mode | Trigger | Behavior |
|------|---------|----------|
| User-provided | User gives cart/checkout URL | Navigate directly to provided URL |
| Auto-add | User says "test on {retailer}" | Find low-cost item, add to cart, proceed |

**Mode 1: User-Provided Cart URL**

```
mcp__claude-in-chrome__navigate(tabId=TAB, url="{user_provided_cart_url}")
mcp__claude-in-chrome__get_page_text(tabId=TAB)
// Proceed to coupon testing
```

**Mode 2: Auto-Add Sample Product**

```
// Step 1: Navigate to retailer
mcp__claude-in-chrome__navigate(tabId=TAB, url="https://www.{retailer}.com")
mcp__claude-in-chrome__get_page_text(tabId=TAB)

// Step 2: Search for low-cost item
// Look for search bar in snapshot
mcp__claude-in-chrome__form_input(tabId=TAB, uid="{search_input_uid}", value="sale items under $20")
mcp__claude-in-chrome__computer(action="left_click", tabId=TAB, ref="{search_button_uid}")
mcp__claude-in-chrome__find(tabId=TAB, text="results")
mcp__claude-in-chrome__get_page_text(tabId=TAB)

// Step 3: Add first affordable item
mcp__claude-in-chrome__computer(action="left_click", tabId=TAB, ref="{first_product_uid}")
mcp__claude-in-chrome__find(tabId=TAB, text="Add to")
mcp__claude-in-chrome__computer(action="left_click", tabId=TAB, ref="{add_to_cart_uid}")

// Step 4: Go to cart/checkout
mcp__claude-in-chrome__computer(action="left_click", tabId=TAB, ref="{cart_icon_uid}")
mcp__claude-in-chrome__find(tabId=TAB, text="Cart")
```

**Coupon Testing Loop:**

```
// For each discovered coupon code:

// 1. Capture original state
mcp__claude-in-chrome__get_page_text(tabId=TAB)
original_total = extract_price_from_snapshot()
mcp__claude-in-chrome__computer(action="screenshot", tabId=TAB, save_to_disk=true, filePath="/tmp/before_{code}.png")

// 2. Find coupon input field
// Look for: promo, coupon, discount, voucher in input names/placeholders
// May need to expand: "Have a promo code?" link

// 3. Enter coupon code
mcp__claude-in-chrome__form_input(tabId=TAB, uid="{coupon_input_uid}", value="{code}")
mcp__claude-in-chrome__computer(action="left_click", tabId=TAB, ref="{apply_button_uid}")

// 4. Wait for response
mcp__claude-in-chrome__find(tabId=TAB, text="applied|invalid|expired|error", timeout=5000)

// 5. Capture result
mcp__claude-in-chrome__get_page_text(tabId=TAB)
mcp__claude-in-chrome__computer(action="screenshot", tabId=TAB, save_to_disk=true, filePath="/tmp/after_{code}.png")

// 6. Analyze result (see Phase 3)

// 7. Remove coupon for next test
mcp__claude-in-chrome__computer(action="left_click", tabId=TAB, ref="{remove_coupon_uid}")
mcp__claude-in-chrome__find(tabId=TAB, text="Enter promo|removed")
```

### Phase 3: Verification

**Success Detection Methods:**

| Method | Implementation | Reliability |
|--------|----------------|-------------|
| Text-based | Search snapshot for "applied", "savings", "discount" | High |
| Price comparison | Compare total before/after applying | High |
| Visual | Screenshot shows green checkmark, strikethrough price | Medium |

**Success Indicators (search in snapshot):**
- "applied"
- "discount applied"
- "savings"
- "you saved"
- "promo code accepted"
- "coupon redeemed"
- Price decrease visible

**Failure Indicators:**
- "invalid"
- "expired"
- "not valid"
- "error"
- "couldn't apply"
- "minimum purchase required"
- "not applicable"
- "code not recognized"

**Verification Algorithm:**

```python
def verify_coupon(snapshot_before, snapshot_after):
    # Check for success text
    success_patterns = ["applied", "savings", "you saved", "discount"]
    for pattern in success_patterns:
        if pattern.lower() in snapshot_after.lower():
            return {"status": "success", "evidence": pattern}

    # Check for price change
    price_before = extract_price(snapshot_before)
    price_after = extract_price(snapshot_after)
    if price_after < price_before:
        savings = price_before - price_after
        return {"status": "success", "savings": savings}

    # Check for error text
    error_patterns = ["invalid", "expired", "not valid", "error"]
    for pattern in error_patterns:
        if pattern.lower() in snapshot_after.lower():
            return {"status": "failed", "reason": pattern}

    return {"status": "unknown", "needs_manual_review": True}
```

### Phase 4: Report Generation

**Markdown Report Template:**

```markdown
# Coupon Test Results: {Retailer}

**Test Date**: {date}
**Cart Contents**: {description}
**Original Total**: ${original_total}

---

## Working Codes (Verified)

### 1. {CODE} - ${savings} off ({percent}%)
- **Type**: {percentage|fixed|free_shipping}
- **Final Total**: ${new_total}
- **Savings**: ${savings} ({percent}%)
- **Source**: {aggregator_name}
- **Terms**: {any_restrictions}
- **Expiration**: {expiration_date}
- **Confidence**: High (tested and verified)

![Before applying](before_{code}.png)
![After applying](after_{code}.png)

---

## Failed Codes

| Code | Error Message | Likely Reason | Source |
|------|---------------|---------------|--------|
| {code} | {error_text} | {expired|minimum_not_met|wrong_category} | {source} |

---

## Codes Not Tested

| Code | Reason |
|------|--------|
| {code} | Requires new account signup |
| {code} | Member/student verification required |

---

## Best Strategy

**Recommended Code**: `{best_code}`
**Maximum Savings**: ${best_savings}
**Stackable with other offers**: {yes|no}

---

## Test Evidence

Screenshots saved to: `/tmp/coupon_test_{retailer}_{date}/`

---

## Sources Searched

| Source | Codes Found | Working | Success Rate |
|--------|-------------|---------|--------------|
| RetailMeNot | X | Y | Z% |
| CouponFollow | X | Y | Z% |
| Slickdeals | X | Y | Z% |
| Reddit | X | Y | Z% |
| Twitter/X | X | Y | Z% |
| Other | X | Y | Z% |
```

---

## Coupon Input Field Detection

For retailers covered in `references/retailer-patterns.md`, use the documented field selectors and apply-button patterns there before falling back to the generic patterns below.

**Common Field Patterns:**

| Label Text | Input Attributes | Placeholder |
|------------|------------------|-------------|
| "Promo Code" | name: promo, promocode | "Enter promo code" |
| "Discount Code" | name: discount, discountCode | "Enter discount code" |
| "Coupon Code" | name: coupon, couponCode | "Enter coupon" |
| "Gift Card" | name: giftcard, gift_card | "Enter gift card" |
| "Voucher" | name: voucher, voucherCode | "Enter voucher" |

**Hidden Field Reveal:**

If coupon field not visible in snapshot, try:

```
// Look for expand triggers
mcp__claude-in-chrome__javascript_tool(action="javascript_exec", tabId=TAB, function="
  () => {
    const triggers = document.querySelectorAll(
      '[class*=\"promo\"], [class*=\"coupon\"], [data-testid*=\"promo\"]'
    );
    triggers.forEach(el => {
      if (el.textContent.toLowerCase().includes('code')) {
        el.click();
      }
    });
    return 'Attempted to reveal coupon field';
  }
")

mcp__claude-in-chrome__get_page_text(tabId=TAB)  // Check if field now visible
```

---

## Apply Button Detection

**Common Patterns:**

| Button Text | Location | CSS Patterns |
|-------------|----------|--------------|
| "Apply" | Right of/below input | apply-btn, promo-apply |
| "Submit" | Form submit | submit-coupon |
| "Add" | Near code field | add-code |
| Arrow icon (→) | Right of input | apply-icon |

---

## Error Handling & Fallbacks

| Failure Mode | Detection | Fallback Strategy |
|--------------|-----------|-------------------|
| WebFetch fails | Error response | Use the Claude-in-Chrome browser extension |
| Coupon field hidden | Not in snapshot | evaluate_script to reveal |
| CAPTCHA/bot detection | "unusual traffic" text | Alert user, provide manual steps |
| Login required | "Sign in" prompt | Skip, note in report |
| Cart empty | "Cart is empty" text | Auto-add sample product |
| Checkout layout changed | Elements not found | Screenshot + alert user |
| Network timeout | No response 30s | Retry once, then skip |
| Anti-bot measures | Cloudflare page | Slower interactions, longer delays |

**WebFetch to browser fallback:**

```
// If WebFetch returns any of:
//   "Prompt is too long", a timeout, empty content,
//   HTTP 403/401/429, or a JS shell with no real text

// Switch to the user's Chrome via the extension:
mcp__claude-in-chrome__navigate(tabId=TAB, url="{target_url}")
mcp__claude-in-chrome__get_page_text(tabId=TAB)
// Parse the page text instead of the WebFetch response
```

Do not retry WebFetch on the same URL hoping for a different result, and never fall back to Playwright.

---

## Subagent Orchestration

| Phase | Parallelizable | Agent Count | Type |
|-------|----------------|-------------|------|
| Planning | N/A | 1 | Plan |
| Discovery | Yes | 6-8 | general-purpose |
| Testing | No (sequential) | 1 | Main agent |
| Reporting | No | 1 | Main agent |

**Why Testing is Sequential:**
- Same browser session required
- Cart state changes with each coupon
- Must remove coupon before testing next
- Evidence capture requires before/after comparison

---

## Rate Limiting & Anti-Bot

To avoid detection:

```
// Add delays between rapid interactions
// Don't: Click → Click → Click → Click
// Do: Click → wait 500ms → Click → wait 500ms

// Simulate human behavior
mcp__claude-in-chrome__find(tabId=TAB, text="...", timeout=2000)  // Natural pause
```

---

## Quick Reference

**Start Testing:**
```
"Find and test coupons for {retailer}"
"Test coupon codes for my {retailer} cart at {cart_url}"
```

**Example Usage:**
```
User: Find and test coupons for Target

Claude:
1. Phase 1: Launches 6-8 discovery agents in parallel (RetailMeNot, CouponFollow,
   Slickdeals, DontPayFull, Groupon, Reddit, Twitter/X, general web search)
2. Phase 2: Sets up a cart via Mode 2 (auto-adds a low-cost sample product),
   then tests each discovered code sequentially in the same browser session
3. Phase 3: Verifies each code using success/failure indicators and price comparison
4. Phase 4: Generates the markdown report with working codes, savings, and evidence
```

---

## Adaptation Notes (added for the public copy)

This section was added when publishing the skill; the rest of the file is the working skill as used privately.

- **Not a standalone script.** This skill is a set of instructions for Claude Code. It hard-depends on:
  - the **Claude-in-Chrome MCP browser extension**, connected to your own logged-in Chrome, with per-site permissions granted in the extension for each retailer and aggregator you want it to visit;
  - **Claude Code subagents** (the Task tool) for the parallel discovery phase;
  - **WebSearch** for the Reddit/Twitter/general-web discovery agents.
- **It operates a live retail cart.** The "Checkout safety (mandatory)" section above is load-bearing: the skill must never place an order, never enter payment details or passwords, and never click "Place Order" or equivalent. Keep those limits intact if you adapt this skill.
- Screenshots are written to generic `/tmp/` paths; adjust for your platform if needed.
