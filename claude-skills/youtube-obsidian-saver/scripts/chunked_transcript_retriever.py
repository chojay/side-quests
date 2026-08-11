#!/usr/bin/env python3
"""
Chunked YouTube Transcript Retriever

Handles long YouTube videos by retrieving transcripts in chunks,
similar to a sliding window approach for processing large content.

This script solves the MCP 25K token limit problem by:
1. Fetching the complete transcript via youtube-transcript-api
2. Splitting into manageable chunks with configurable overlap
3. Outputting either complete markdown or individual chunks for processing

Use Cases:
- Long lectures (60+ minutes)
- Conference talks
- Podcast episodes on YouTube
- Educational series

Token Estimation:
- ~500 tokens per minute without timestamps
- ~650 tokens per minute with timestamps
- 25K token limit = ~50 minutes without timestamps, ~38 minutes with
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import shared utilities
from utils import (
    extract_video_id,
    format_timestamp,
    estimate_tokens,
)


@dataclass
class TranscriptChunk:
    """Represents a chunk of transcript with metadata."""
    chunk_number: int
    total_chunks: int
    start_time: float
    end_time: float
    start_timestamp: str
    end_timestamp: str
    content: str
    token_estimate: int


def fetch_transcript(video_id: str, languages: List[str] = None) -> List[Dict]:
    """
    Fetch transcript from YouTube.

    Returns list of transcript entries with 'text', 'start', 'duration' keys.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("Error: youtube-transcript-api not installed.", file=sys.stderr)
        print("Install with: pip install youtube-transcript-api", file=sys.stderr)
        sys.exit(1)

    if languages is None:
        languages = ['en', 'en-US', 'en-GB']

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=languages)

        # Convert to list of dicts
        entries = []
        for entry in transcript:
            entries.append({
                'text': entry.text,
                'start': entry.start,
                'duration': entry.duration
            })
        return entries

    except Exception as e:
        print(f"Error fetching transcript: {e}", file=sys.stderr)
        return []


def fetch_video_metadata(video_id: str) -> Dict:
    """Fetch video metadata using yt-dlp."""
    try:
        import yt_dlp
    except ImportError:
        return {
            'title': f'Video {video_id}',
            'channel': 'Unknown',
            'duration': 0,
            'view_count': 0,
            'upload_date': '',
        }

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://youtube.com/watch?v={video_id}', download=False)
            return {
                'title': info.get('title', f'Video {video_id}'),
                'channel': info.get('uploader', 'Unknown'),
                'channel_url': info.get('uploader_url', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', ''),
                'description': info.get('description', ''),
            }
    except Exception as e:
        print(f"Warning: Could not fetch metadata: {e}", file=sys.stderr)
        return {
            'title': f'Video {video_id}',
            'channel': 'Unknown',
            'duration': 0,
            'view_count': 0,
            'upload_date': '',
        }


def chunk_transcript(
    transcript: List[Dict],
    chunk_size: int = 15000,
    overlap_seconds: float = 30.0,
    include_timestamps: bool = True
) -> List[TranscriptChunk]:
    """
    Split transcript into chunks with optional overlap.

    Args:
        transcript: List of transcript entries
        chunk_size: Target token size per chunk
        overlap_seconds: Seconds of overlap between chunks (sliding window)
        include_timestamps: Whether to include timestamps in output

    Returns:
        List of TranscriptChunk objects
    """
    if not transcript:
        return []

    chunks = []
    current_chunk_entries = []
    current_tokens = 0
    chunk_start_time = transcript[0]['start']

    for i, entry in enumerate(transcript):
        # Format entry
        if include_timestamps:
            formatted = f"[{format_timestamp(entry['start'])}] {entry['text']}"
        else:
            formatted = entry['text']

        entry_tokens = estimate_tokens(formatted)

        # Check if adding this entry would exceed chunk size
        if current_tokens + entry_tokens > chunk_size and current_chunk_entries:
            # Save current chunk
            chunk_content = "\n\n".join(current_chunk_entries)
            chunk_end_time = transcript[i-1]['start'] + transcript[i-1].get('duration', 0)

            chunks.append(TranscriptChunk(
                chunk_number=len(chunks) + 1,
                total_chunks=0,  # Will update later
                start_time=chunk_start_time,
                end_time=chunk_end_time,
                start_timestamp=format_timestamp(chunk_start_time),
                end_timestamp=format_timestamp(chunk_end_time),
                content=chunk_content,
                token_estimate=current_tokens
            ))

            # Start new chunk with overlap
            # Find entries within overlap_seconds before current entry
            overlap_entries = []
            overlap_tokens = 0
            for j in range(i-1, -1, -1):
                if transcript[j]['start'] >= entry['start'] - overlap_seconds:
                    if include_timestamps:
                        overlap_formatted = f"[{format_timestamp(transcript[j]['start'])}] {transcript[j]['text']}"
                    else:
                        overlap_formatted = transcript[j]['text']
                    overlap_entries.insert(0, overlap_formatted)
                    overlap_tokens += estimate_tokens(overlap_formatted)
                else:
                    break

            current_chunk_entries = overlap_entries
            current_tokens = overlap_tokens
            chunk_start_time = transcript[max(0, i - len(overlap_entries))]['start']

        current_chunk_entries.append(formatted)
        current_tokens += entry_tokens

    # Don't forget the last chunk
    if current_chunk_entries:
        chunk_content = "\n\n".join(current_chunk_entries)
        chunk_end_time = transcript[-1]['start'] + transcript[-1].get('duration', 0)

        chunks.append(TranscriptChunk(
            chunk_number=len(chunks) + 1,
            total_chunks=0,
            start_time=chunk_start_time,
            end_time=chunk_end_time,
            start_timestamp=format_timestamp(chunk_start_time),
            end_timestamp=format_timestamp(chunk_end_time),
            content=chunk_content,
            token_estimate=current_tokens
        ))

    # Update total_chunks
    for chunk in chunks:
        chunk.total_chunks = len(chunks)

    return chunks


def generate_complete_markdown(
    video_id: str,
    metadata: Dict,
    chunks: List[TranscriptChunk],
    include_chunk_markers: bool = True
) -> str:
    """Generate complete Obsidian markdown with all chunks."""

    title = metadata.get('title', f'Video {video_id}')
    channel = metadata.get('channel', 'Unknown')
    channel_url = metadata.get('channel_url', '')
    duration = metadata.get('duration', 0)
    views = metadata.get('view_count', 0)
    upload_date = metadata.get('upload_date', '')
    thumbnail = metadata.get('thumbnail', '')
    description = metadata.get('description', '')

    # Format duration
    duration_str = format_timestamp(duration) if duration else 'Unknown'

    # Format upload date
    if len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

    # Calculate total tokens
    total_tokens = sum(c.token_estimate for c in chunks)

    md = f"""---
tags:
  - video/youtube
  - channel/{channel.lower().replace(' ', '-')}
  - transcript/chunked
aliases:
  - {title}
created: {datetime.now().strftime('%Y-%m-%d')}
video_id: {video_id}
source: youtube
duration: {duration_str}
total_chunks: {len(chunks)}
total_tokens_estimate: {total_tokens}
---

# {title}

## Video Information

**Channel**: [{channel}]({channel_url})
**Duration**: {duration_str}
**Views**: {views:,}
**Upload Date**: {upload_date}
**YouTube URL**: https://www.youtube.com/watch?v={video_id}

## Chunking Summary

| Metric | Value |
|--------|-------|
| Total Chunks | {len(chunks)} |
| Estimated Tokens | ~{total_tokens:,} |
| Video Duration | {duration_str} |
| Chunk Overlap | 30 seconds |

"""

    if thumbnail:
        md += f"""## Video Thumbnail

![{title}]({thumbnail})

**Watch on YouTube**: [Click here](https://www.youtube.com/watch?v={video_id})

"""

    if description:
        # Truncate long descriptions
        desc_preview = description[:500] + "..." if len(description) > 500 else description
        md += f"""## Description

{desc_preview}

"""

    md += """---

## Full Transcript

"""

    for chunk in chunks:
        if include_chunk_markers and len(chunks) > 1:
            md += f"""### Chunk {chunk.chunk_number}/{chunk.total_chunks} [{chunk.start_timestamp} - {chunk.end_timestamp}]

"""
        md += chunk.content + "\n\n"

    md += f"""---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
**Video ID**: `{video_id}`
**Processing**: Chunked transcript retrieval ({len(chunks)} chunks)
"""

    return md


def generate_chunk_json(
    video_id: str,
    metadata: Dict,
    chunks: List[TranscriptChunk]
) -> str:
    """Generate JSON output for programmatic processing."""

    return json.dumps({
        'video_id': video_id,
        'metadata': metadata,
        'chunking_info': {
            'total_chunks': len(chunks),
            'total_tokens_estimate': sum(c.token_estimate for c in chunks),
        },
        'chunks': [
            {
                'chunk_number': c.chunk_number,
                'total_chunks': c.total_chunks,
                'start_time': c.start_time,
                'end_time': c.end_time,
                'start_timestamp': c.start_timestamp,
                'end_timestamp': c.end_timestamp,
                'token_estimate': c.token_estimate,
                'content': c.content,
            }
            for c in chunks
        ]
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Chunked YouTube Transcript Retriever for long videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - complete markdown
  python chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" -o note.md

  # JSON output for programmatic processing
  python chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" --json

  # Custom chunk size (smaller for MCP compatibility)
  python chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" --chunk-size 10000

  # Without timestamps (reduces tokens by ~20-30%)
  python chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" --no-timestamps

  # Get specific chunk only
  python chunked_transcript_retriever.py "https://youtu.be/VIDEO_ID" --chunk 2 --json
        """
    )

    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument(
        '--output', '-o',
        help='Output file path (prints to stdout if not specified)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=15000,
        help='Target tokens per chunk (default: 15000)'
    )
    parser.add_argument(
        '--overlap',
        type=float,
        default=30.0,
        help='Overlap between chunks in seconds (default: 30)'
    )
    parser.add_argument(
        '--no-timestamps',
        action='store_true',
        help='Exclude timestamps (reduces token count by ~20-30%%)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON instead of Markdown'
    )
    parser.add_argument(
        '--chunk',
        type=int,
        help='Output only specific chunk number (1-indexed)'
    )
    parser.add_argument(
        '--languages',
        nargs='+',
        default=['en', 'en-US', 'en-GB'],
        help='Preferred languages for transcript (default: en en-US en-GB)'
    )
    parser.add_argument(
        '--info-only',
        action='store_true',
        help='Only show chunking info without content'
    )

    args = parser.parse_args()

    # Extract video ID
    try:
        video_id = extract_video_id(args.url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing video: {video_id}", file=sys.stderr)

    # Fetch metadata
    print("Fetching video metadata...", file=sys.stderr)
    metadata = fetch_video_metadata(video_id)

    # Fetch transcript
    print("Fetching transcript...", file=sys.stderr)
    transcript = fetch_transcript(video_id, args.languages)

    if not transcript:
        print("Error: No transcript available for this video", file=sys.stderr)
        sys.exit(1)

    print(f"Transcript entries: {len(transcript)}", file=sys.stderr)

    # Calculate total duration from transcript
    total_duration = transcript[-1]['start'] + transcript[-1].get('duration', 0)
    print(f"Total duration: {format_timestamp(total_duration)}", file=sys.stderr)

    # Chunk the transcript
    print(f"Chunking with size={args.chunk_size}, overlap={args.overlap}s...", file=sys.stderr)
    chunks = chunk_transcript(
        transcript,
        chunk_size=args.chunk_size,
        overlap_seconds=args.overlap,
        include_timestamps=not args.no_timestamps
    )

    print(f"Generated {len(chunks)} chunks", file=sys.stderr)

    # Info only mode
    if args.info_only:
        print("\n=== Chunking Summary ===", file=sys.stderr)
        for chunk in chunks:
            print(f"Chunk {chunk.chunk_number}/{chunk.total_chunks}: "
                  f"[{chunk.start_timestamp} - {chunk.end_timestamp}] "
                  f"~{chunk.token_estimate:,} tokens", file=sys.stderr)
        print(f"\nTotal estimated tokens: {sum(c.token_estimate for c in chunks):,}", file=sys.stderr)
        sys.exit(0)

    # Filter to specific chunk if requested
    if args.chunk:
        if args.chunk < 1 or args.chunk > len(chunks):
            print(f"Error: Chunk {args.chunk} not found (1-{len(chunks)} available)", file=sys.stderr)
            sys.exit(1)
        chunks = [chunks[args.chunk - 1]]

    # Generate output
    if args.json:
        output = generate_chunk_json(video_id, metadata, chunks)
    else:
        output = generate_complete_markdown(
            video_id,
            metadata,
            chunks,
            include_chunk_markers=len(chunks) > 1
        )

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding='utf-8')
        print(f"\n✅ Output saved to: {output_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
