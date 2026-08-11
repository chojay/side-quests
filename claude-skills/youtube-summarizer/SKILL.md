---
name: youtube-summarizer
description: This skill should be used when a user provides a YouTube URL and wants a summarized, content-aware Obsidian note, not just a raw transcript dump. REQUIRES a YouTube URL or explicit YouTube reference to trigger. Trigger phrases include "summarize this YouTube video," "save this YouTube recipe," "extract this YouTube cooking video," "create a note from this YouTube video with summary," or a bare YouTube URL accompanied by "summarize" or "save as recipe." It auto-detects content type (recipe, tutorial, lecture, review) and formats the summary accordingly. Recipes get ingredient tables with bilingual names and step-by-step methods. Includes embedded video and full transcript in a collapsible section. Builds on youtube-obsidian-saver for extraction; adds Claude's analysis layer for structured summarization. If the user only wants a raw transcript without summarization, defer to youtube-obsidian-saver instead.
metadata:
  version: 1.0.0
---

# YouTube Summarizer

## Overview

This skill extracts YouTube video metadata and transcript, then uses Claude's intelligence to produce a **content-aware Obsidian note** with:

1. **Embedded video** (thumbnail + link or iframe)
2. **Structured summary** that auto-detects content type and formats accordingly:
   - **Recipe** → ingredients table, step-by-step method, tips, science insights
   - **Tutorial/How-to** → key steps, tools needed, common mistakes
   - **Lecture/Talk** → key arguments, takeaways, references
   - **General** → bullet-point summary of main points
3. **Full transcript** in a **collapsible section** (folded by default)

**When to use this skill (NOT `youtube-obsidian-saver`):**
- User provides a YouTube URL and says "summarize," "save as recipe," or "extract"
- User says "summarize this YouTube video," "save this YouTube recipe," "extract this YouTube cooking video"
- User pastes a YouTube URL and wants a structured summary, not just a raw transcript
- User wants to understand YouTube video content without watching the full video

**IMPORTANT: This skill requires a YouTube URL or explicit YouTube reference. Do NOT trigger on generic phrases like "save this recipe" without a YouTube context.**

**When to defer to `youtube-obsidian-saver` instead:**
- User only wants the raw transcript saved
- User says "save the transcript" without asking for summarization
- User wants a quick archival note without content analysis

## Workflow

### Step 1: Extract Video Data

Use the existing `youtube-obsidian-saver` scripts to get raw data:

```bash
cd ~/.claude/skills/youtube-obsidian-saver/scripts && \
python youtube_extractor.py "<YOUTUBE_URL>" --json --language <LANG>
```

- Use `--language ko` for Korean videos, `--language en` for English, etc.
- If language is unknown, omit the flag (auto-detects)
- The `--json` flag returns structured data instead of markdown

Parse the JSON output to get:
- `video_info.title`: video title
- `video_info.channel`: channel name
- `video_info.video_id`: for embed URLs
- `video_info.duration`: video length
- `video_info.upload_date`: when published
- `video_info.description`: video description
- `video_info.chapters`: chapter markers (if any)
- `transcript`: full transcript text with timestamps

### Step 2: Determine Content Type

Analyze the transcript and video metadata to classify the content:

| Content Type | Signals |
|---|---|
| **Recipe** | Ingredients with measurements, cooking verbs (cut, boil, sear, fry), temperature references, timing instructions, food items |
| **Tutorial/How-to** | Step-by-step instructions, tools/software mentioned, "how to" in title |
| **Lecture/Talk** | Academic language, thesis/argument structure, citations, conference/university context |
| **Review** | Product comparisons, pros/cons, ratings, "review" in title |
| **General** | Default fallback: summarize main points |

### Step 3: Generate Summary

Based on content type, produce the appropriate summary format.

#### Recipe Format

For cooking/recipe videos, extract and structure:

```markdown
## Ingredients

### [Category 1, e.g., Sauce]

| Ingredient | Amount | Notes |
|---|---|---|
| 간장 (soy sauce) | 50g (6 spoons) | - |
| 설탕 (sugar) | 30g | split: half in sauce, half for caramelizing |

### [Category 2, e.g., Meat]

- **Beef**: 400g, thick cut
  - Preferred: 치마살 (skirt steak)

### [Category 3, e.g., Vegetables]

- 양파 (onion): half
- 파 (green onion): 2 stalks

## Method

### Prep Phase
1. Step one...
2. Step two...

### Cooking Phase
3. Step three...

## Tips
- Important tip 1
- Important tip 2

## Science & Key Insights (if applicable)
- **Maillard Reaction:** explanation...
```

**Recipe extraction rules:**
- For non-English videos, include both the original language term and English translation for ingredients, techniques, and dish names (e.g., `간장 (soy sauce)`, `dashi (出汁)`)
- Include gram measurements AND spoon equivalents when both are given
- Note any substitutions or "skip if unavailable" ingredients
- Capture cooking science explanations (these are often the most valuable part)
- Include timing information (cook times, rest times)
- Note cut sizes, temperatures, and technique details

#### Tutorial/How-to Format

```markdown
## What You'll Need
- Tool/software 1
- Tool/software 2

## Steps

### 1. [Phase Name]
Detailed step...

### 2. [Phase Name]
Detailed step...

## Common Mistakes to Avoid
- Mistake 1 and how to fix it

## Key Takeaways
- Takeaway 1
```

#### Lecture/Talk Format

```markdown
## Key Arguments
1. Main argument 1...
2. Main argument 2...

## Summary
Concise summary of the talk...

## Notable Quotes
- "Quote 1..." (context)

## References Mentioned
- Reference 1
```

#### General Format

```markdown
## Summary
Concise overview of the video content in 3-5 paragraphs.

## Key Points
- Point 1
- Point 2
- Point 3

## Notable Details
- Detail worth remembering
```

### Step 4: Assemble the Obsidian Note

Use this template structure for the final note:

```markdown
---
tags:
  - video/youtube
  - channel/<channel-name-slugified>
  - <content-type-tag>
aliases:
  - <Video Title>
  - <Alternative names if applicable>
created: <YYYY-MM-DD>
video_id: <VIDEO_ID>
source: https://www.youtube.com/watch?v=<VIDEO_ID>
---

# <Video Title>

**Channel:** [<Channel Name>](<channel_url>)
**Duration:** <formatted duration>
**Published:** <upload date>

## Video

![<Video Title>](https://i.ytimg.com/vi/<VIDEO_ID>/maxresdefault.jpg)

[Watch on YouTube](https://www.youtube.com/watch?v=<VIDEO_ID>)

---

<STRUCTURED SUMMARY HERE; format depends on content type>

---

> [!note]- Full Transcript
>
> [00:00] First line of transcript...
>
> [00:15] Second line of transcript...
>
> [00:30] Third line...

---

**Last Updated**: <YYYY-MM-DD>
```

### Important: Transcript Collapsible Section

Use Obsidian's **callout syntax** with the `-` modifier for collapsed-by-default:

```markdown
> [!note]- Full Transcript
>
> [00:00] Line one...
>
> [00:15] Line two...
```

The `-` after `[!note]` makes the callout **collapsed by default** in Obsidian's reading mode. Users can click to expand.

**Every line of the transcript must be prefixed with `> `** to stay inside the callout block.

If the transcript is very long (>500 lines), consider chunking into multiple collapsible sections by chapter or time range:

```markdown
> [!note]- Transcript (00:00 – 15:00)
>
> [00:00] ...

> [!note]- Transcript (15:00 – 30:00)
>
> [15:00] ...
```

### Step 5: Cross-Link and Save

1. **Determine save location** by asking the user or inferring from context:
   - Cooking recipes → `<vault>/Cooking/Recipes/` (or a chef-specific subdirectory)
   - General videos → appropriate project directory

2. **Add wiki links** in the summary to connect to existing notes:
   - Ingredients that have dedicated notes (e.g., `[[연두]]`)
   - Related recipes or topics
   - Chef/channel pages

3. **Add `See Also` section** if related notes exist

4. **Create stub notes** for important entities that don't have notes yet (like `[[연두]]` for a key ingredient)

## Content-Type-Specific Tags

Apply appropriate tags based on detected content type:

| Content Type | Tags to Add |
|---|---|
| Recipe | `recipe/<cuisine>` (e.g., `recipe/korean-food`), `recipe/<dish-type>`, `chef/<chef-name>` |
| Tutorial | `tutorial/<topic>`, `howto` |
| Lecture | `lecture/<subject>`, `talk` |
| Review | `review/<product-category>` |
| General | `video/<topic>` |

## Multi-Language Handling

- For non-English videos, specify the language: `--language ko` (Korean), `--language ja` (Japanese), etc.
- Include both the original language term and English translation in the summary (e.g., `간장 (soy sauce)`, `味噌 (miso)`)
- The summary should be written in English, preserving original-language terms where meaningful (ingredient names, technique names, dish names)

## Error Handling

| Issue | Solution |
|---|---|
| No transcript available | Note this in the output; still save metadata + description as summary basis |
| Transcript in wrong language | Try other available languages; list what's available |
| Very long video (>45 min) | Use `chunked_transcript_retriever.py --json` instead (supports `--json` flag) |
| Age-restricted video | Add `--cookies-browser safari` to extraction command |

## Example Output

See `examples/sample-recipe-note.md` for a complete, realistic example of a recipe note generated by this skill (based on 아미요's 10-Layer Bulgogi video).

Key structural elements in the example:
- Frontmatter with `recipe/korean-food`, `chef/amiyo` tags and aliases
- Video thumbnail + YouTube link
- Ingredients table with Korean + English names, gram + spoon measurements
- Step-by-step method organized by cooking phases (Prep, Cooking, Resting, Finishing)
- Science insights section (Maillard reaction, deglazing, etc.)
- Tips section
- See Also links to related recipes
- Collapsible full transcript at the bottom using `> [!note]- Full Transcript`

---

## Adaptation Notes (added for the public copy)

This section was added when publishing the skill; the rest of the file is the working skill as used privately.

- **This skill has no code of its own.** It hard-depends on the sibling **youtube-obsidian-saver** skill being installed at `~/.claude/skills/youtube-obsidian-saver/` (its `youtube_extractor.py --json` output is the data source). Install that skill and its Python dependencies first.
- **Vault paths are placeholders.** Replace `<vault>/...` examples with folders in your own Obsidian vault.
- **The example note** (`examples/sample-recipe-note.md`) is an illustrative sample of the skill's output based on a public YouTube cooking video; the wiki-style links in it demonstrate Obsidian note syntax the skill produces.

---

**Created**: 2026-02-11
