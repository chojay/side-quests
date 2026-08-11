#!/usr/bin/env python3
"""
YouTube Video and Transcript Extractor for Obsidian

Downloads YouTube videos locally and extracts transcripts.
Uses yt-dlp for video download and youtube-transcript-api for transcription.

Features:
- Multiple URL format support (youtu.be, youtube.com, shorts)
- Auto-language detection with fallback
- Chapter extraction from video metadata
- Flexible embed modes (link, download, iframe)
- Actionable error messages
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

# Import shared utilities
from utils import (
    extract_video_id,
    format_timestamp,
    format_duration,
    format_upload_date,
    format_number,
    get_available_transcript_languages,
    format_error_message,
    detect_error_type,
)


def download_video_pytubefix(url: str, output_dir: Path, video_id: str, title: str) -> Optional[Path]:
    """
    Download YouTube video using pytubefix (fallback method).

    Args:
        url: YouTube video URL
        output_dir: Directory to save video
        video_id: YouTube video ID
        title: Video title for filename

    Returns:
        Path to downloaded video file, or None if download failed
    """
    try:
        from pytubefix import YouTube
    except ImportError:
        print("Warning: pytubefix not installed. Install with: pip install pytubefix", file=sys.stderr)
        return None

    try:
        print(f"Trying pytubefix download to: {output_dir}", file=sys.stderr)
        yt = YouTube(url)

        # Get highest resolution progressive stream (video+audio combined)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if not stream:
            print("No suitable progressive stream found", file=sys.stderr)
            return None

        # Create safe filename
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title[:100]
        filename = f"{safe_title}-{video_id}.mp4"

        print(f"Downloading with pytubefix: {stream}", file=sys.stderr)
        output_path = stream.download(output_path=str(output_dir), filename=filename)

        if output_path and Path(output_path).exists():
            print(f"pytubefix download successful: {output_path}", file=sys.stderr)
            return Path(output_path)
        else:
            return None

    except Exception as e:
        print(f"pytubefix download failed: {e}", file=sys.stderr)
        return None


def download_video(url: str, output_dir: Path, video_id: str, title: str,
                   cookies_browser: Optional[str] = None) -> Optional[Path]:
    """
    Download YouTube video using yt-dlp (primary) or pytubefix (fallback).

    Args:
        url: YouTube video URL
        output_dir: Directory to save video
        video_id: YouTube video ID
        title: Video title for filename
        cookies_browser: Browser to extract cookies from (safari, chrome, firefox)

    Returns:
        Path to downloaded video file, or None if download failed
    """
    try:
        import yt_dlp
    except ImportError:
        print("Warning: yt-dlp not installed, trying pytubefix...", file=sys.stderr)
        return download_video_pytubefix(url, output_dir, video_id, title)

    # Create safe filename from title
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
    safe_title = safe_title[:100]

    output_template = str(output_dir / f"{safe_title}-{video_id}.%(ext)s")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'ios'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'referer': 'https://www.youtube.com/',
    }

    # Add cookies from browser if specified
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_browser,)

    try:
        print(f"Downloading video to: {output_dir}", file=sys.stderr)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            ext = info.get('ext', 'mp4')
            video_path = output_dir / f"{safe_title}-{video_id}.{ext}"

            if video_path.exists():
                print(f"Video downloaded: {video_path}", file=sys.stderr)
                return video_path
            else:
                for file in output_dir.glob(f"{safe_title}-{video_id}.*"):
                    if file.suffix in ['.mp4', '.webm', '.mkv']:
                        print(f"Video downloaded: {file}", file=sys.stderr)
                        return file

                print("Warning: Video download succeeded but file not found", file=sys.stderr)
                return None

    except Exception as e:
        error_type = detect_error_type(str(e))
        print(format_error_message(error_type, str(e)), file=sys.stderr)
        print("Trying pytubefix as fallback...", file=sys.stderr)
        return download_video_pytubefix(url, output_dir, video_id, title)


def extract_video_info(url: str, cookies_browser: Optional[str] = None) -> Dict:
    """
    Extract video metadata from YouTube URL using yt-dlp.

    Args:
        url: YouTube video URL
        cookies_browser: Browser to extract cookies from

    Returns:
        Dictionary containing video metadata including chapters
    """
    try:
        import yt_dlp
    except ImportError:
        print("Error: yt-dlp not installed. Install with: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android', 'ios'],
            }
        },
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }

    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_browser,)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return {
                'video_id': info.get('id', ''),
                'title': info.get('title', 'Unknown Title'),
                'channel': info.get('uploader', 'Unknown Channel'),
                'channel_url': info.get('uploader_url', ''),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', ''),
                'url': info.get('webpage_url', url),
                'chapters': info.get('chapters', []),  # Extract chapters
            }
    except Exception as e:
        error_type = detect_error_type(str(e))
        print(format_error_message(error_type, str(e)), file=sys.stderr)
        sys.exit(1)


def extract_transcript_markitdown(video_path: Path) -> Optional[str]:
    """
    Extract transcript from video file using markitdown.

    Args:
        video_path: Path to video file

    Returns:
        Transcript text, or None if extraction failed
    """
    try:
        from markitdown import MarkItDown
    except ImportError:
        print("Warning: markitdown not installed. Transcript extraction disabled.", file=sys.stderr)
        print("Install with: pip install markitdown", file=sys.stderr)
        return None

    try:
        print(f"Extracting transcript using markitdown...", file=sys.stderr)
        md = MarkItDown()
        result = md.convert(str(video_path))

        if result and result.text_content:
            print("Transcript extracted successfully", file=sys.stderr)
            return result.text_content.strip()
        else:
            print("Warning: markitdown returned no transcript", file=sys.stderr)
            return None

    except Exception as e:
        print(f"Warning: Error extracting transcript with markitdown: {e}", file=sys.stderr)
        return None


def extract_transcript_youtube_api(video_id: str, language: Optional[str] = None) -> Tuple[Optional[str], List[str]]:
    """
    Extract transcript from YouTube video using youtube-transcript-api.

    Args:
        video_id: YouTube video ID
        language: Preferred language code (e.g., 'en', 'ko'). Auto-detects if None.

    Returns:
        Tuple of (formatted transcript string or None, list of available languages)
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("Warning: youtube-transcript-api not installed.", file=sys.stderr)
        return None, []

    available_languages = []

    try:
        print(f"Fetching available transcript languages...", file=sys.stderr)
        ytt_api = YouTubeTranscriptApi()

        # Get available languages
        try:
            transcript_list = ytt_api.list(video_id)
            available_languages = [t.language_code for t in transcript_list]
            print(f"Available languages: {available_languages}", file=sys.stderr)
        except Exception:
            pass

        # Determine language to use
        if language:
            languages_to_try = [language]
        else:
            # Default fallback chain
            languages_to_try = ['en', 'en-US', 'en-GB']
            # Add first available language as final fallback
            if available_languages:
                languages_to_try.extend(available_languages)

        # Try to fetch transcript
        transcript = None
        for lang in languages_to_try:
            try:
                transcript = ytt_api.fetch(video_id, languages=[lang])
                print(f"Transcript fetched in language: {lang}", file=sys.stderr)
                break
            except Exception:
                continue

        if not transcript:
            print(f"No transcript found in any of: {languages_to_try}", file=sys.stderr)
            return None, available_languages

        # Format transcript with timestamps
        formatted = []
        for entry in transcript:
            timestamp = format_timestamp(entry.start)
            text = entry.text
            formatted.append(f"[{timestamp}] {text}")

        print(f"Transcript extracted successfully ({len(formatted)} lines)", file=sys.stderr)
        return "\n\n".join(formatted), available_languages

    except Exception as e:
        error_type = detect_error_type(str(e))
        if error_type == 'no_transcript':
            print(format_error_message(error_type, str(e), available_languages), file=sys.stderr)
        else:
            print(f"Warning: Transcript extraction failed: {e}", file=sys.stderr)
        return None, available_languages


def format_chapters(chapters: List[Dict], video_id: str) -> str:
    """
    Format video chapters as markdown table with clickable timestamps.

    Args:
        chapters: List of chapter dicts with 'title', 'start_time', 'end_time'
        video_id: YouTube video ID for generating links

    Returns:
        Formatted markdown string with chapters table
    """
    if not chapters:
        return ""

    lines = ["## Chapters", "", "| Time | Title |", "|------|-------|"]

    for chapter in chapters:
        title = chapter.get('title', 'Untitled')
        start_time = chapter.get('start_time', 0)
        timestamp = format_timestamp(start_time)
        # Create clickable timestamp link
        link = f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}"
        lines.append(f"| [{timestamp}]({link}) | {title} |")

    return "\n".join(lines)


def generate_obsidian_markdown(
    video_info: Dict,
    transcript: Optional[str] = None,
    video_path: Optional[Path] = None,
    vault_path: Optional[Path] = None,
    embed_mode: str = 'link'
) -> str:
    """
    Generate Obsidian-formatted markdown from video info and transcript.

    Args:
        video_info: Dictionary containing video metadata
        transcript: Optional transcript text
        video_path: Optional path to downloaded video file
        vault_path: Optional path to vault root (for relative paths)
        embed_mode: 'link' (thumbnail+link), 'download' (local file), or 'iframe'

    Returns:
        Formatted Obsidian markdown string
    """
    title = video_info['title']
    channel = video_info['channel']
    url = video_info['url']
    video_id = video_info['video_id']
    description = video_info['description']
    duration = format_duration(video_info['duration'])
    views = format_number(video_info['view_count'])
    upload_date = format_upload_date(video_info['upload_date'])
    thumbnail = video_info['thumbnail']
    chapters = video_info.get('chapters', [])

    # Generate channel tag (sanitize for obsidian)
    channel_tag = re.sub(r'[^a-zA-Z0-9-]', '-', channel.lower())
    channel_tag = re.sub(r'-+', '-', channel_tag).strip('-')

    markdown = f"""---
tags:
  - video/youtube
  - channel/{channel_tag}
aliases:
  - {title}
created: {datetime.now().strftime('%Y-%m-%d')}
video_id: {video_id}
source: youtube
---

# {title}

## Video Information

**Channel**: [{channel}]({video_info['channel_url']})
**Duration**: {duration}
**Views**: {views}
**Upload Date**: {upload_date}
**YouTube URL**: {url}

"""

    # Add embed based on mode
    if embed_mode == 'download' and video_path:
        if vault_path and video_path.is_relative_to(vault_path):
            video_embed = f"![[{video_path.relative_to(vault_path)}]]"
            video_link_text = f"Local file: `{video_path.relative_to(vault_path)}`"
        else:
            video_embed = f"![[{video_path.name}]]"
            video_link_text = f"Local file: `{video_path}`"

        markdown += f"""## Local Video File

{video_embed}

{video_link_text}

"""
    elif embed_mode == 'iframe':
        markdown += f"""## Embedded Video

<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>

"""
    else:  # default: 'link'
        markdown += f"""## Video Thumbnail

![{title}]({thumbnail})

**Watch on YouTube**: [Click here]({url})

"""

    # Add chapters if available
    chapters_md = format_chapters(chapters, video_id)
    if chapters_md:
        markdown += chapters_md + "\n\n"

    # Add description
    markdown += f"""## Description

{description if description else 'No description available.'}

"""

    # Add transcript
    if transcript:
        markdown += f"""---

## Transcript

{transcript}

"""
    else:
        markdown += """---

## Transcript

*No transcript available for this video.*

"""

    markdown += f"""---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
**Video ID**: `{video_id}`
"""

    return markdown


def main():
    parser = argparse.ArgumentParser(
        description='Extract YouTube video with transcript for Obsidian',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - extract metadata and transcript
  python youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md

  # Download video locally
  python youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md --download

  # Specify transcript language
  python youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md --language ko

  # Use iframe embed instead of thumbnail
  python youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md --embed-mode iframe

  # Handle age-restricted videos with cookies
  python youtube_extractor.py "https://youtu.be/VIDEO_ID" -o note.md --cookies-browser safari
        """
    )
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument(
        '--output', '-o',
        help='Output markdown file path'
    )
    parser.add_argument(
        '--download',
        action='store_true',
        help='Download video file locally'
    )
    parser.add_argument(
        '--video-dir',
        help='Directory to save video file (default: same as output/Media/Videos)'
    )
    parser.add_argument(
        '--vault-path',
        help='Path to Obsidian vault root (for relative path calculation)'
    )
    parser.add_argument(
        '--no-transcript',
        action='store_true',
        help='Skip transcript extraction'
    )
    parser.add_argument(
        '--language', '-l',
        help='Preferred transcript language code (e.g., en, ko, ja). Auto-detects if not specified.'
    )
    parser.add_argument(
        '--transcript-method',
        choices=['markitdown', 'youtube-api', 'both'],
        default='youtube-api',
        help='Transcript extraction method (default: youtube-api)'
    )
    parser.add_argument(
        '--embed-mode',
        choices=['link', 'download', 'iframe'],
        default='link',
        help='How to embed video: link (thumbnail+link), download (local file), iframe'
    )
    parser.add_argument(
        '--cookies-browser',
        choices=['safari', 'chrome', 'firefox', 'edge', 'brave'],
        help='Browser to extract cookies from (for age-restricted videos)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output raw JSON instead of Obsidian markdown'
    )

    args = parser.parse_args()

    # If embed-mode is download, automatically enable --download
    if args.embed_mode == 'download':
        args.download = True

    # Extract video info
    print(f"Extracting video information from: {args.url}", file=sys.stderr)
    video_info = extract_video_info(args.url, args.cookies_browser)
    video_id = video_info['video_id']
    title = video_info['title']

    # Download video if requested
    video_path = None
    if args.download:
        if args.video_dir:
            video_dir = Path(args.video_dir)
        elif args.output:
            video_dir = Path(args.output).parent / "Media" / "Videos"
        else:
            video_dir = Path.cwd() / "Media" / "Videos"

        video_dir.mkdir(parents=True, exist_ok=True)
        video_path = download_video(args.url, video_dir, video_id, title, args.cookies_browser)

    # Extract transcript if requested
    transcript = None
    available_languages = []
    if not args.no_transcript:
        if args.transcript_method in ['markitdown', 'both'] and video_path:
            transcript = extract_transcript_markitdown(video_path)

        if not transcript and args.transcript_method in ['youtube-api', 'both']:
            transcript, available_languages = extract_transcript_youtube_api(video_id, args.language)

    # Determine vault path
    vault_path = Path(args.vault_path) if args.vault_path else None

    # Generate output
    if args.json:
        output = json.dumps({
            'video_info': video_info,
            'transcript': transcript,
            'video_path': str(video_path) if video_path else None,
            'available_languages': available_languages
        }, indent=2)
    else:
        output = generate_obsidian_markdown(
            video_info, transcript, video_path, vault_path, args.embed_mode
        )

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding='utf-8')
        print(f"\n✅ Markdown saved to: {output_path}", file=sys.stderr)
        if video_path:
            print(f"✅ Video saved to: {video_path}", file=sys.stderr)
        if video_info.get('chapters'):
            print(f"✅ Extracted {len(video_info['chapters'])} chapters", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
