---
name: youtube-obsidian-saver
description: >-
  Extract YouTube videos with transcripts and save them as properly formatted
  Obsidian markdown notes. Use whenever the user provides a YouTube URL
  (youtu.be or youtube.com) and wants the video saved to their Obsidian vault.
  Trigger phrases include "save this YouTube video," "save this video to my
  vault," "get the transcript of this video," "extract this YouTube video," or
  a bare YouTube URL with save or transcript intent. Creates notes with
  frontmatter, video metadata, embedded video reference, description, chapters,
  and full transcript with timestamps. Handles Korean and other transcript
  languages, age-restricted videos via browser cookies, and long videos (over
  45 minutes) via chunked transcript retrieval. If the user wants a summarized,
  content-aware note rather than a raw transcript, use the sibling
  youtube-summarizer skill instead, which builds on this skill for extraction.
---

# YouTube Obsidian Saver

## Overview

This skill extracts comprehensive information from YouTube videos (including metadata, descriptions, chapters, and transcripts) and saves them as properly formatted Obsidian markdown notes with wiki links, frontmatter, and timestamps.

**When to use this skill:**
- User provides a YouTube URL (youtu.be/* or youtube.com/watch?v=*)
- User wants to save video content to their Obsidian vault
- User wants video transcripts for research or note-taking
- User wants to create wiki-linked video references in Obsidian

**Related skill:** If the user wants a summarized, content-aware note (recipe, tutorial, lecture, review) rather than a raw transcript, hand off to the **youtube-summarizer** skill instead. It builds on this skill's extraction scripts and adds a structured summarization layer.

## Open Generated Note in Obsidian for Parallel Review (Always Do This)

**After successfully saving a YouTube video note to the vault, open it in Obsidian using the `obsidian://` URI scheme** so the user can review the rendered output (embedded video, transcript, metadata) in parallel without manually navigating to the note.

### How to open

```bash
python3 -c "import urllib.parse,subprocess; p='/ABSOLUTE/PATH/TO/note.md'; subprocess.run(['open', '-g', 'obsidian://open?path='+urllib.parse.quote(p)])"
```

This opens the file in Obsidian **in the background** without stealing focus. If Obsidian isn't running, it launches Obsidian first.

### When to open

✅ **Do open:**
- After the YouTube extraction script completes successfully
- After any follow-up edits to the generated note

❌ **Don't open:**
- If the script fails or produces an error
- When the user has said they don't want the note opened

## Quick Start

To save a YouTube video to Obsidian:

```bash
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py <youtube-url> --output <output-path.md>
```

**Examples:**
```bash
# Basic - metadata + transcript
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md

# Korean video with Korean transcript
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md --language ko

# Download video locally
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md --embed-mode download

# Age-restricted video (use browser cookies)
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md --cookies-browser safari
```

## Installation

### Required Dependencies

```bash
pip install -r ~/.claude/skills/youtube-obsidian-saver/scripts/requirements.txt
```

### Optional Dependencies (for video download)

```bash
pip install markitdown pytubefix
```

## Command Line Options

### youtube_extractor.py

| Flag | Description |
|------|-------------|
| `--output`, `-o` | Output markdown file path |
| `--language`, `-l` | Transcript language code (e.g., `en`, `ko`, `ja`). Auto-detects if not specified |
| `--embed-mode` | How to embed video: `link` (default), `download`, `iframe` |
| `--cookies-browser` | Browser for cookies: `safari`, `chrome`, `firefox`, `edge`, `brave` |
| `--download` | Download video file locally |
| `--no-transcript` | Skip transcript extraction |
| `--json` | Output raw JSON instead of markdown |

### Embed Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| `link` | Thumbnail image + YouTube link | Default, works everywhere |
| `download` | Local video file with `![[file.mp4]]` | Offline access, archival |
| `iframe` | YouTube iframe embed | Obsidian with iframe plugin |

## Features

### Auto-Language Detection

The script automatically:
1. Fetches available transcript languages
2. Tries your preferred language (if specified)
3. Falls back to English variants (en, en-US, en-GB)
4. Uses first available language as last resort

```bash
# Specify Korean transcript
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md -l ko

# Auto-detect (tries English first, then any available)
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md
```

### Chapter Extraction

If a video has chapters (timestamps in description), they're extracted as a clickable table:

```markdown
## Chapters

| Time | Title |
|------|-------|
| [00:00](https://youtube.com/watch?v=XXX&t=0) | Introduction |
| [02:30](https://youtube.com/watch?v=XXX&t=150) | Main Topic |
| [15:00](https://youtube.com/watch?v=XXX&t=900) | Conclusion |
```

### Actionable Error Messages

When errors occur, you get specific fixes:

| Error | Message |
|-------|---------|
| Age-restricted | "Try: --cookies-browser safari" |
| Region-blocked | "Try using a VPN" |
| No transcript | "Available languages: [ko, ja]. Try: --language ko" |
| Network error | "Check internet connection and retry" |

## Generated Markdown Format

```markdown
---
tags:
  - video/youtube
  - channel/channel-name
aliases:
  - Video Title
created: 2025-12-31
video_id: VIDEO_ID
source: youtube
---

# Video Title

## Video Information

**Channel**: [Channel Name](https://youtube.com/@channel)
**Duration**: 12m 34s
**Views**: 125,432
**Upload Date**: 2024-08-15
**YouTube URL**: https://www.youtube.com/watch?v=VIDEO_ID

## Video Thumbnail

![Video Title](https://i.ytimg.com/vi/VIDEO_ID/maxresdefault.jpg)

**Watch on YouTube**: [Click here](https://www.youtube.com/watch?v=VIDEO_ID)

## Chapters

| Time | Title |
|------|-------|
| [00:00](https://youtube.com/watch?v=VIDEO_ID&t=0) | Introduction |
| [05:00](https://youtube.com/watch?v=VIDEO_ID&t=300) | Main Content |

## Description

Video description here...

---

## Transcript

[00:00] Welcome to today's video...

[00:15] Let's dive into the topic...

---

**Last Updated**: 2025-12-31
**Video ID**: `VIDEO_ID`
```

## Long Video Handling (Chunked Retriever)

For videos >45 minutes, use the chunked transcript retriever:

```bash
# Complete markdown with chunk markers
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" -o note.md

# Preview chunking without content
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" --info-only

# Smaller chunks for processing
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" --chunk-size 10000

# Get specific chunk only
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" --chunk 2 --json
```

### Chunked Retriever Options

| Flag | Description |
|------|-------------|
| `--chunk-size` | Target tokens per chunk (default: 15000) |
| `--overlap` | Overlap between chunks in seconds (default: 30) |
| `--no-timestamps` | Exclude timestamps (reduces tokens ~20-30%) |
| `--info-only` | Show chunking summary without content |
| `--chunk N` | Output only chunk N (1-indexed) |

### Token Estimation

| Video Length | Without Timestamps | With Timestamps |
|--------------|-------------------|-----------------|
| 30 minutes | ~15,000 tokens | ~19,500 tokens |
| 45 minutes | ~22,500 tokens | ~29,250 tokens |
| 60 minutes | ~30,000 tokens | ~39,000 tokens |
| 90 minutes | ~45,000 tokens | ~58,500 tokens |

## Troubleshooting

### Video is Age-Restricted

```bash
# Use browser cookies for authentication
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "URL" -o note.md --cookies-browser safari
```

### No Transcript Available

```
Error: No English transcript. Available: [ko, ja]
Fix: Try --language ko
```

```bash
# Specify the available language
python3 ~/.claude/skills/youtube-obsidian-saver/scripts/youtube_extractor.py "URL" -o note.md --language ko
```

### Network/Connection Errors

1. Check internet connection
2. Try again (may be temporary)
3. If YouTube is blocking, wait and retry later

### Video Not Found

1. Verify URL is correct
2. Check if video is private or deleted
3. Try accessing video in browser first

## Integration with Obsidian

### Folder Organization

Determine output location based on:
1. **Project context**: `<vault>/Projects/Tutorials/`
2. **Topic category**: `<vault>/Research/Videos/`
3. **User preferences**: Ask if unsure

### Bidirectional Linking

After saving, create links from related notes:

```markdown
## Resources
- [[Video Title]] - Helpful video on topic
- [[Another Video|related video]]
```

### Tag Conventions

Generated notes include:
- `video/youtube` - All YouTube videos
- `channel/channel-name` - By channel

Add custom tags based on content:
- `project/project-name`
- `category/topic`

## Script Reference

### youtube_extractor.py

Main extraction script for single videos.

**Dependencies:** yt-dlp, youtube-transcript-api
**Optional:** markitdown, pytubefix (for --download)

### chunked_transcript_retriever.py

Handles long videos (>45 min) by chunking transcripts.

**Dependencies:** yt-dlp, youtube-transcript-api

### utils.py

Shared utilities used by both scripts:
- `extract_video_id()` - Parse video ID from URL
- `format_timestamp()` - Convert seconds to MM:SS
- `format_duration()` - Human-readable duration
- `estimate_tokens()` - Token estimation
- `format_error_message()` - Actionable error messages

---

## Adaptation Notes (added for the public copy)

This section was added when publishing the skill; the rest of the file is the working skill as used privately.

- **Vault paths are placeholders.** Replace `<vault>/...` examples with folders in your own Obsidian vault.
- **"Open in Obsidian" is macOS-only.** The `open -g obsidian://open?path=...` step requires macOS and an installed Obsidian app. Everything else in the skill works anywhere Python runs; on other platforms, skip that step or substitute your OS's URI opener.
- **`--cookies-browser` reads your own local browser cookies.** The flag tells yt-dlp to pull YouTube session cookies from your installed browser at runtime (needed for age-restricted videos). No cookies or credentials are bundled with this skill.
- **Dependencies:** `pip install -r scripts/requirements.txt` (yt-dlp, youtube-transcript-api); optionally `markitdown` and `pytubefix` for `--download` mode. Install the skill at `~/.claude/skills/youtube-obsidian-saver/` so the documented command paths work as written.

---

**Created**: 2025-11-02
**Last Updated**: 2026-07-03
