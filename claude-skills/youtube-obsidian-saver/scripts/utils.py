#!/usr/bin/env python3
"""
Shared utilities for YouTube Obsidian Saver scripts.

This module contains common functions used by both youtube_extractor.py
and chunked_transcript_retriever.py to avoid code duplication.
"""

import re
from typing import List, Optional


def extract_video_id(url: str) -> str:
    """
    Extract video ID from various YouTube URL formats.

    Supported formats:
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/embed/VIDEO_ID
    - https://youtube.com/shorts/VIDEO_ID

    Args:
        url: YouTube video URL

    Returns:
        11-character video ID

    Raises:
        ValueError: If video ID cannot be extracted
    """
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to MM:SS or HH:MM:SS format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration (e.g., "1h 23m", "45m 30s", "30s")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def format_upload_date(date_str: str) -> str:
    """
    Convert YYYYMMDD to YYYY-MM-DD format.

    Args:
        date_str: Date in YYYYMMDD format

    Returns:
        Date in YYYY-MM-DD format
    """
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str


def format_number(num: int) -> str:
    """
    Format large numbers with commas.

    Args:
        num: Number to format

    Returns:
        Comma-separated number string
    """
    return f"{num:,}"


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses approximation of ~4 characters per token for English text.
    This is conservative to ensure we stay under limits.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4 + 1


def get_available_transcript_languages(video_id: str) -> List[str]:
    """
    Get list of available transcript languages for a video.

    Args:
        video_id: YouTube video ID

    Returns:
        List of language codes (e.g., ['en', 'ko', 'ja'])
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        return [t.language_code for t in transcript_list]
    except Exception:
        return []


def format_error_message(error_type: str, details: str = "", available_languages: List[str] = None) -> str:
    """
    Format user-friendly error messages with actionable suggestions.

    Args:
        error_type: Type of error (age_restricted, region_blocked, no_transcript, network)
        details: Additional error details
        available_languages: List of available transcript languages (for no_transcript errors)

    Returns:
        Formatted error message with suggestions
    """
    messages = {
        'age_restricted': (
            "Video is age-restricted and requires authentication.\n"
            "Fix: Try using --cookies-browser safari (or chrome/firefox)"
        ),
        'region_blocked': (
            "Video is not available in your region.\n"
            "Fix: Try using a VPN to access from a different country."
        ),
        'no_transcript': (
            "No transcript available in requested language.\n"
            f"Available languages: {available_languages or 'none'}\n"
            "Fix: Try --language <code> with one of the available languages."
        ),
        'network': (
            "Network error occurred while accessing YouTube.\n"
            "Fix: Check your internet connection and try again."
        ),
        'private': (
            "Video is private or has been removed.\n"
            "Fix: Verify the video URL is correct and publicly accessible."
        ),
        'live': (
            "This appears to be a live stream or premiere.\n"
            "Fix: Wait until the stream ends or use --no-transcript flag."
        ),
    }

    base_message = messages.get(error_type, f"Unknown error: {error_type}")
    if details:
        base_message += f"\n\nDetails: {details}"

    return base_message


def detect_error_type(error_message: str) -> str:
    """
    Detect error type from exception message.

    Args:
        error_message: Error message string

    Returns:
        Error type string
    """
    error_lower = error_message.lower()

    if 'age' in error_lower or 'sign in' in error_lower:
        return 'age_restricted'
    elif 'not available' in error_lower and 'country' in error_lower:
        return 'region_blocked'
    elif 'private' in error_lower or 'removed' in error_lower:
        return 'private'
    elif 'live' in error_lower or 'premiere' in error_lower:
        return 'live'
    elif 'network' in error_lower or 'connection' in error_lower or 'timeout' in error_lower:
        return 'network'
    elif 'transcript' in error_lower or 'caption' in error_lower or 'subtitle' in error_lower:
        return 'no_transcript'
    else:
        return 'unknown'
