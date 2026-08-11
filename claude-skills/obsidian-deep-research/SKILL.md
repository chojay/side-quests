---
name: obsidian-deep-research
description: >-
  Advanced multi-phase deep research system that saves findings directly INTO the user's
  Obsidian vault as interconnected notes with automatic wiki-links, bidirectional backlinks, MOC
  generation, source credibility scoring, and confidence metrics. Use when conducting
  comprehensive research on any topic requiring multiple sources, fact-checking, and integration
  into an Obsidian knowledge base. Triggers: 'deep research X and add it to my vault', 'create a
  research note on X', 'update or expand existing vault research', building interconnected
  knowledge bases, product analysis with cross-cultural (Western and Korean) validation,
  academic or medical literature review, decision frameworks with confidence ratings, and
  generating Maps of Content (MOCs). Distinct from the generic deep-research skill, which
  produces standalone web reports: choose this skill whenever the output belongs in the Obsidian
  vault and its knowledge graph rather than a one-off report.
---

# Obsidian Deep Research System

## Purpose

This skill enables comprehensive, multi-phase research with automatic integration into Obsidian vaults. It orchestrates parallel research agents, validates sources, generates confidence metrics, and creates interconnected knowledge graphs using wiki links. The system surpasses traditional linear research by employing Graph-of-Thoughts reasoning, adversarial validation, and automatic cross-referencing with existing vault content.

## When to Use This Skill

Activate this skill when:
- Conducting deep research on complex topics requiring multiple sources
- Building comprehensive knowledge bases with interconnected notes
- Analyzing products with cross-cultural validation (Western and Asian sources)
- Performing academic literature reviews with citation tracking
- Creating decision frameworks with confidence metrics
- Researching topics that require fact-checking and source triangulation
- Expanding existing vault knowledge with new research domains
- Generating Maps of Content (MOCs) for research topics

## Open Generated Notes in Obsidian for Parallel Review (Always Do This)

**After creating or significantly editing any `.md` file in the vault, open it in Obsidian using the `obsidian://` URI scheme** so the user can review the rendered output in parallel without manually navigating to the note.

This is especially important for deep research workflows where the final output is a multi-layered knowledge graph - the user should be able to verify wiki links, backlinks, MOC structure, and rendered content while Claude continues working on adjacent notes.

### How to open a note in Obsidian

Use the Bash tool with Obsidian's URL protocol. The absolute path must be URL-encoded:

```bash
python3 -c "import urllib.parse,subprocess; p='/ABSOLUTE/PATH/TO/file.md'; subprocess.run(['open', '-g', 'obsidian://open?path='+urllib.parse.quote(p)])"
```

This opens the file in Obsidian **in the background** without stealing focus. If Obsidian isn't running, it launches Obsidian first and then navigates to the note.

### When to open (Deep Research context)

✅ **Do open:**
- After creating the primary research output (MOC, summary note, synthesis note)
- After significant multi-section updates
- When presenting findings for user review
- After generating the final deliverable of a research phase

❌ **Don't open:**
- After every intermediate subagent note (batch these)
- For raw source-capture notes (user only needs to see the synthesis)
- When the user has said they don't want notes opened

### URL Format Reference

| URI | Purpose |
|---|---|
| `obsidian://open?path=/absolute/path/to/file.md` | Open by absolute path (preferred - works across vaults) |
| `obsidian://open?vault=VAULT_NAME&file=relative/path` | Open by vault name + relative path (requires knowing vault name) |

**Always URL-encode** path parameters (spaces → `%20`, special characters handled by `urllib.parse.quote`).

### Multi-Note Opening Strategy

For deep research outputs that generate many notes, prioritize opening:

1. **Primary synthesis note / final report** (always open)
2. **Top-level MOC** (if newly created)
3. **Key decision framework notes** (if they're the user's action items)

Don't open all generated notes - that overwhelms the user. One well-placed open at the synthesis layer lets them navigate into sub-notes via the wiki links.

## Subagent Orchestration Strategy

### CRITICAL: Leverage Subagents for Parallel Processing

This skill MUST utilize Claude Code subagents to maximize research efficiency and data collection breadth. Subagents enable:
- **Parallel data gathering** across multiple sources simultaneously
- **Context isolation** preventing information overload in main conversation
- **Specialized focus** with different agents handling different domains
- **Wider data collection** by spawning multiple agents to cover more ground

### Available Subagent Types

| Subagent Type | Purpose | When to Use |
|---------------|---------|-------------|
| `Plan` | Design research strategy and implementation steps | **ALWAYS use first** to plan the research phases before execution |
| `Explore` | Fast codebase/vault exploration | Finding existing notes, searching vault structure, locating related content |
| `general-purpose` | Multi-step autonomous research tasks | Web searches, source validation, cross-cultural research, parallel data gathering |

### Subagent Invocation Syntax

```
Task tool with subagent_type="Plan" | "Explore" | "general-purpose"
```

**Example - Planning Research:**
```
Task(subagent_type="Plan", prompt="Plan the research strategy for [topic] including:
1. Key sub-questions to investigate
2. Source types to consult
3. Parallel research pathways
4. Validation criteria")
```

**Example - Parallel Data Gathering (launch in single message):**
```
Task(subagent_type="general-purpose", prompt="Research [topic] from Western sources: Reddit, Wirecutter, Consumer Reports...")
Task(subagent_type="general-purpose", prompt="Research [topic] from Korean sources: Naver blogs, Coupang reviews...")
Task(subagent_type="general-purpose", prompt="Research [topic] from academic sources: PubMed, Google Scholar...")
Task(subagent_type="general-purpose", prompt="Research [topic] pricing across retailers...")
```

### Parallelization Rules

1. **Maximum 10 concurrent subagents** - additional tasks queue automatically
2. **Launch independent agents in a SINGLE message** with multiple Task tool calls
3. **Each agent has isolated context** - provide complete instructions per agent
4. **20k token overhead per agent** - use judiciously for substantial tasks

---

## Core Research Framework

### 10-Phase Enhanced Research Model

Execute research through these sequential phases, using parallel agents where indicated:

### Research Depth Selection

**Choose research depth based on scope and time constraints:**

#### Quick Research (⏱️ 20-30 min)
- **Use Cases**: Simple questions with clear answers, single product/concept evaluation, existing knowledge validation
- **Execution**: Phases 1, 4 (2-3 agents), 7, 10
- **Output**: Concise summary with key findings and confidence ratings
- **Example**: "What's the best budget smart doorbell?" → Quick comparison of 2-3 top-rated options

#### Standard Research (⏱️ 1-2 hours) - DEFAULT
- **Use Cases**: Comprehensive product analysis, cross-cultural validation required, decision framework creation
- **Execution**: All 10 phases with 4-6 parallel agents
- **Output**: Full research note with detailed analysis, sources, and confidence metrics
- **Example**: "Best robot vacuum for HomeKit ecosystem" → Complete analysis with Western/Asian sources, pricing, failure modes

#### Deep Research (⏱️ 2-4+ hours)
- **Use Cases**: Complex multi-faceted topics, academic literature synthesis, novel topics requiring extensive exploration
- **Execution**: Extended workflow with Phases 0-12 including iterative refinement loops
- **Output**: Comprehensive research with meta-analysis, systematic review, extensive cross-referencing
- **Example**: "Efficacy of spaced-repetition learning methods" → Academic systematic review with evidence hierarchy, bias analysis, research gaps

**Selection Guidance:**
- Start with **Standard** if unsure
- Downgrade to **Quick** if initial scope validation (Phase 3.5) reveals limited sources
- Upgrade to **Deep** if topic reveals unexpected complexity during execution

---

## 10-Phase Workflow Overview

**Read `references/research-phases.md` before executing each phase.** It contains the full
prompts, templates, checklists, and worked examples for every phase below.

| Phase | Name | One-Line Summary |
|-------|------|------------------|
| 1 | Research Planning with Plan Agent | MANDATORY first step: Plan agent selects a research perspective and designs strategy, sub-questions, and parallel pathways |
| 2 | Existing Knowledge Mapping with Explore Agent | Explore agent scans the vault for related notes, existing wiki links, MOCs, and knowledge gaps |
| 3 | Research Planning & Strategy | Select methodologies, define source diversity (geographic, authority, temporal), set confidence thresholds |
| 3.5 | Research Scope Validation | Validate feasibility (source accessibility, scope, cost/time) before launching expensive parallel agents |
| 4 | Parallel Information Gathering | Launch 4-8 general-purpose agents in a SINGLE message using the domain-optimized agent templates |
| 5 | Source Validation & Credibility Assessment | Score sources with the credibility matrix in `references/research-methodologies.md`; flag contradictions |
| 5.5 | Adversarial Source Mining | Systematically seek disconfirming evidence to reduce confirmation bias |
| 6 | Cross-Referencing & Triangulation | Triangulate claims across independent sources |
| 7 | Synthesis & Analysis | Structure findings with domain-appropriate frameworks, decision trees, and comparison tables |
| 8 | Critical Review & Fact-Checking | Adversarial analysis, red-teaming of conclusions, uncertainty quantification |
| 9 | Advanced Wiki-Link Integration & Knowledge Graph Building | Ten-step process: enhanced frontmatter, hub notes, ontological links, tagging, backlink audit, MOC auto-generation, block references, query blocks, connectivity metrics, graph visualization |
| 10 | Final Packaging with Confidence Metrics | Assemble the final research note with executive summary and confidence ratings |
| 10.5 | Research Maintenance & Monitoring Plan | Temporal classification, update triggers, and a monitoring strategy for long-term accuracy |

---

## Incremental Research Modes

For updates, follow-ups, additions, or monitoring-triggered changes to existing research,
do NOT re-run the full workflow. Read `references/incremental-research-modes.md` for the
complete workflows (Mode 1: Expand Existing Research, Mode 2: Quick Follow-Up Questions,
Mode 3: Comparative Addition, Mode 4: Monitoring Update) plus version-management and
confidence-recalculation best practices.

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

## Reference Files

Read these files on demand at the point in the workflow where they apply; do not load them
all at once. The Implementation Guidelines that previously lived in this file are split
across the web-research-toolkit, obsidian-integration, session-management, and
confidence-system references.

| File | When to Read |
|------|--------------|
| `references/research-phases.md` | Before executing each phase: full prompts, templates, checklists, and examples for Phases 1-10.5 |
| `references/incremental-research-modes.md` | When updating or expanding existing research (Modes 1-4) instead of running a full cycle |
| `references/research-methodologies.md` | Canonical credibility base-score tables with recency/corroboration factors, domain-specific approaches (academic, product, medical, technical), cross-cultural source checklists, adversarial/bias framework, research quality metrics |
| `references/web-research-toolkit.md` | During Phases 4-5: subagent orchestration best practices, browser automation patterns and fallback chain, source citation format, YouTube video integration |
| `references/obsidian-integration.md` | During Phase 9 and note writing: Obsidian syntax quick reference, table formatting, living document features, source archiving and preservation |
| `references/session-management.md` | For long research sessions: checkpointing strategy, checkpoint YAML template, session recovery and resume |
| `references/confidence-system.md` | During Phases 5-10: multi-dimensional confidence ratings, calculation formula, uncertainty quantification, confidence decay, quality metrics |
| `references/output-templates.md` | During Phase 10: full product research and academic research templates, interactive decision frameworks, visual data presentation |
| `references/error-handling.md` | When any source, agent, or phase fails: error classification levels 1-4, fallback chains, abort criteria, recovery checklist |

## Bundled Scripts

- `scripts/research_orchestrator.py` is a conceptual data model of the 10-phase workflow
  (phases, agent allocation, confidence structures). It is a schema/skeleton for future
  automation, not an executable orchestrator; do not attempt to run it to conduct research.

---

## Future Enhancement Hooks

This skill is designed to support future additions:
- API integrations for academic databases
- Real-time price tracking webhooks
- Automated research updates via scheduled tasks
- Integration with reference managers (Zotero, Mendeley)
- Custom domain-specific research templates
- Machine learning for source credibility scoring

---

## Adaptation Notes (added for the public copy)

This workflow was written for a specific Claude Code environment and references tooling you may not have:

- **Claude Code Task subagents** (`Plan`, `Explore`, `general-purpose`): the parallel-agent phases assume Claude Code's Task tool. Other agent harnesses need equivalent orchestration primitives.
- **Browser automation**: the `claude-in-chrome` MCP browser extension is used as the WebFetch fallback in `references/web-research-toolkit.md`. Substitute your own browser tooling or drop those patterns.
- **Sibling skills**: `youtube-obsidian-saver` (transcripts) is published alongside this skill in the same claude-skills folder. `naver-korean-search` (Korean sources) and the tool-routing skill remain private; treat those calls as optional integration points.
- **Vault paths**: examples use placeholder paths (`/vault/...`, `/path/to/vault`; equivalent to the `<vault>/` convention used by the other published skills). Point them at your own Obsidian vault.

None of these change the core method (phased research, credibility scoring, adversarial mining, confidence decay, knowledge-graph integration), which is tool-agnostic.
