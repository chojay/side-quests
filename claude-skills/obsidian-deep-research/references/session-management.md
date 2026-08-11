# Checkpointing & Session Management

Part of the `obsidian-deep-research` skill (Implementation Guidelines). Read this file
for long research sessions: checkpoint strategy, the Research Session Checkpoint YAML
template, and the session recovery/resume workflow.

### Checkpointing & Session Management

Long research sessions (2-4+ hours) risk context loss, interruption, and wasted effort. Implement checkpointing to enable pause/resume.

#### Checkpoint Strategy

**When to Create Checkpoints**:
1. **After Phase 1** (Research Plan): ~5 minutes in
2. **After Phase 4** (Parallel Agents Launch): ~30-60 minutes in (CRITICAL)
3. **After Phase 6** (Triangulation): ~90-120 minutes in
4. **After Phase 10** (Final Note): Before session end

**Checkpoint File Format**:

`.research-checkpoint-{timestamp}.yaml`:

```yaml
# Research Session Checkpoint
session_id: "research-20250115-143022"
topic: "Best smart doorbell for HomeKit 2025"
checkpoint_phase: 4
checkpoint_time: "2025-01-15T15:45:00Z"
elapsed_time_minutes: 62

# Research Configuration
research_depth: "Standard"  # Quick / Standard / Deep
research_perspective: "Practical Optimizer + Safety Auditor"
target_confidence: 0.85

# Completed Phases
completed_phases:
  phase_1:
    status: "completed"
    output_file: "plan-20250115-143022.md"
    timestamp: "2025-01-15T14:35:00Z"

  phase_2:
    status: "completed"
    existing_notes_found: 3
    related_notes:
      - "Smart-Doorbell-Research-v1.md"
      - "HomeKit-Ecosystem-Overview.md"
      - "Smart-Home-MOC.md"

  phase_3:
    status: "completed"
    validation_passed: true
    estimated_cost: "$4.50"
    estimated_tokens: 85000

  phase_4:
    status: "completed"
    agents_launched: 6
    agents_completed: 6
    agents_failed: 0
    sources_collected: 47

# Sources Collected
sources:
  - url: "https://www.reddit.com/r/HomeKit/comments/..."
    credibility: 0.75
    type: "community_expert"
    collected_at: "2025-01-15T15:12:00Z"

  - url: "https://www.nytimes.com/wirecutter/reviews/best-video-doorbell/"
    credibility: 0.90
    type: "expert_review"
    status: "paywalled"
    fallback: "summary_via_websearch"
    collected_at: "2025-01-15T15:23:00Z"

  # [... total 47 sources ...]

# Current State
current_phase: 5  # About to start Phase 5 (Fact-Checking)
next_action: "Launch adversarial source mining"

# Cost Tracking
tokens_used: 67500
api_calls:
  webfetch: 18
  websearch: 12
  claude-in-chrome: 3
estimated_cost_usd: 3.25

# Confidence Metrics (Preliminary)
confidence_projections:
  source_quality: 0.85
  source_diversity: 0.80
  sample_size: 0.92
  estimated_overall: 0.83  # May change after triangulation

# Notes & Warnings
notes:
  - "Wirecutter paywalled - using summary"
  - "Korean sources (Coupang) geo-blocked - using Reddit proxy"
  - "1 agent timeout on Naver search - acceptable loss"

# Recovery Information
resume_instructions: |
  To resume from this checkpoint:
  1. Read plan file: plan-20250115-143022.md
  2. Review 47 collected sources (URLs above)
  3. Continue with Phase 5: Adversarial Source Mining
  4. Target: Find counter-evidence for current leading recommendations
```

#### Checkpoint Creation Workflow

**Automatically Create Checkpoints After**:

**Phase 1** (Research Plan):
```yaml
checkpoint-phase1-{timestamp}.yaml:
  session_id: {unique_id}
  topic: {research_topic}
  completed: [phase_1]
  plan_file: {path_to_plan}
  research_config: {depth, perspective, target_confidence}
  next_action: "Phase 2: Vault exploration"
```

**Phase 4** (Post-Agent Execution) - **MOST CRITICAL**:
```yaml
checkpoint-phase4-{timestamp}.yaml:
  session_id: {unique_id}
  topic: {research_topic}
  completed: [phase_1, phase_2, phase_3, phase_4]
  sources_collected: [{url, credibility, type}...]  # Complete list
  agents_summary:
    launched: 6
    completed: 6
    failed: 0
  cost_so_far: {tokens, api_calls, estimated_usd}
  next_action: "Phase 5: Fact-checking & adversarial mining"
```

This checkpoint prevents catastrophic loss if context is exhausted after expensive parallel agent execution.

**Phase 6** (Post-Triangulation):
```yaml
checkpoint-phase6-{timestamp}.yaml:
  # ... all previous data ...
  triangulation_results:
    consensus_claims: [{claim, supporting_sources}...]
    contradictions: [{issue, conflicting_sources}...]
    confidence_preliminary: 0.83
  next_action: "Phase 7: Consensus synthesis"
```

**Phase 10** (Final Note):
```yaml
checkpoint-complete-{timestamp}.yaml:
  session_id: {unique_id}
  status: "completed"
  final_note: {path_to_research_note}
  final_confidence: 0.85
  total_cost: {tokens, api_calls, usd}
  session_duration_minutes: 147
```

#### Session Recovery & Resume

**When Resuming from Checkpoint**:

1. **Load Checkpoint File**:
   ```
   Read: .research-checkpoint-{timestamp}.yaml
   ```

2. **Display Resume Summary**:
   ```markdown
   ## Resuming Research Session

   **Session ID**: research-20250115-143022
   **Topic**: Best smart doorbell for HomeKit 2025
   **Last Checkpoint**: Phase 4 complete (62 minutes ago)

   **Progress**:
   - ✅ Phase 1: Research Planning (completed)
   - ✅ Phase 2: Vault Exploration (3 related notes found)
   - ✅ Phase 3: Scope Validation (passed, $4.50 estimated)
   - ✅ Phase 4: Parallel Agents (6/6 completed, 47 sources collected)
   - ⏸️ Phase 5: Fact-Checking & Adversarial Mining (ready to start)

   **Costs So Far**: $3.25 (67,500 tokens, 33 API calls)

   **Sources Collected**: 47
   - Expert Reviews: 8 (e.g., Wirecutter, Consumer Reports)
   - Community: 23 (Reddit, forums)
   - User Reviews: 12 (Amazon, Best Buy)
   - Academic: 2
   - Other: 2

   **Known Issues**:
   - Wirecutter paywalled (using summary)
   - Coupang geo-blocked (using Reddit proxy)
   ```

3. **Ask User**:
   ```
   Resume from Phase 5 (fact-checking)?
   OR
   Restart from beginning?
   OR
   Jump to specific phase?
   ```

4. **If Resuming**:
   - Load all sources from checkpoint
   - Load plan from Phase 1
   - Continue with next scheduled phase
   - Append to existing checkpoint (don't create new session ID)

5. **If Restarting**:
   - Archive old checkpoint
   - Start fresh session
   - May reference old checkpoint for comparison

#### Checkpoint Best Practices

**Do**:
- ✅ Create checkpoint after expensive operations (agents, large scrapes)
- ✅ Include complete source URLs (enable resume without re-fetch)
- ✅ Track costs accurately (prevent budget overruns)
- ✅ Store plan/config (ensure consistency across resume)
- ✅ Use unique session IDs (prevent confusion between sessions)

**Don't**:
- ❌ Checkpoint after every single phase (too granular, wastes context)
- ❌ Store full source content in checkpoint (use URLs + metadata)
- ❌ Skip Phase 4 checkpoint (most expensive phase to re-run)
- ❌ Lose checkpoint files (defeats purpose)

**Checkpoint Retention**:
- Keep active session checkpoint until research complete
- Keep final checkpoint permanently (research provenance)
- Delete intermediate checkpoints after successful completion
- Archive checkpoints for failed/abandoned research (learning)

**Cost Recovery**:
If session interrupted after Phase 4:
- ✅ **With checkpoint**: Resume from Phase 5, only pay for remaining phases
- ❌ **Without checkpoint**: Re-run all 6 agents, pay full cost again (~$3-5 wasted)

**Estimated Time Savings**:
- Phase 1-3: ~15 minutes saved
- Phase 4: ~60 minutes + $3-5 saved (6 parallel agents)
- Phase 5-6: ~30 minutes saved
- **Total**: ~90-105 minutes + $3-5 saved per resume

