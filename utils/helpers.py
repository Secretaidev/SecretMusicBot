"""Shared helper functions used across the bot — eliminates code duplication."""

import re
from typing import Optional


def format_duration(seconds: Optional[int]) -> str:
    """Convert seconds to human-readable duration string."""
    if not seconds or seconds <= 0:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_number(num: int) -> str:
    """Format large numbers for display (1.2K, 3.4M, etc.)."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def truncate(text: str, max_len: int = 40, suffix: str = "…") -> str:
    """Safely truncate a string with suffix."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def progress_bar(
    current: int,
    total: int,
    length: int = 15,
    filled: str = "▰",
    empty: str = "▱",
) -> str:
    """Generate a text-based progress bar."""
    if total <= 0:
        return empty * length
    pct = min(current / total, 1.0)
    filled_len = int(pct * length)
    return filled * filled_len + empty * (length - filled_len)


def is_url(text: str) -> bool:
    """Check if text is a valid URL."""
    return bool(re.match(r"https?://\S+", text.strip()))


YT_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/"
    r"(watch\?v=|embed/|v/|shorts/|\?v=)?([^&=%\?]{11})"
)

YT_PLAYLIST_REGEX = re.compile(
    r"(https?://)?(www\.)?youtube\.com/playlist\?list=([^&\s]+)"
)

SPOTIFY_TRACK_REGEX = re.compile(
    r"https?://open\.spotify\.com/track/([\w]+)"
)

SPOTIFY_PLAYLIST_REGEX = re.compile(
    r"https?://open\.spotify\.com/playlist/([\w]+)"
)

SPOTIFY_ALBUM_REGEX = re.compile(
    r"https?://open\.spotify\.com/album/([\w]+)"
)

SOUNDCLOUD_REGEX = re.compile(
    r"https?://soundcloud\.com/[\w-]+/[\w-]+"
)


def extract_yt_id(text: str) -> Optional[str]:
    """Extract YouTube video ID from URL."""
    m = YT_REGEX.search(text)
    return m.group(6) if m else None


def extract_yt_playlist_id(text: str) -> Optional[str]:
    """Extract YouTube playlist ID from URL."""
    m = YT_PLAYLIST_REGEX.search(text)
    return m.group(3) if m else None


def detect_source(query: str) -> str:
    """Detect the music source from a query/URL.
    Returns: 'youtube', 'youtube_playlist', 'spotify_track', 'spotify_playlist',
             'spotify_album', 'soundcloud', 'jiosaavn', 'url', or 'search'
    """
    query = query.strip()
    if YT_PLAYLIST_REGEX.match(query):
        return "youtube_playlist"
    if YT_REGEX.match(query):
        return "youtube"
    if SPOTIFY_TRACK_REGEX.match(query):
        return "spotify_track"
    if SPOTIFY_PLAYLIST_REGEX.match(query):
        return "spotify_playlist"
    if SPOTIFY_ALBUM_REGEX.match(query):
        return "spotify_album"
    if SOUNDCLOUD_REGEX.match(query):
        return "soundcloud"
    if "jiosaavn.com" in query:
        return "jiosaavn"
    if is_url(query):
        return "url"
    return "search"


def get_readable_time(seconds: int) -> str:
    """Convert seconds to a human-readable time string like '2h 15m 30s'."""
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs:
        parts.append(f"{secs}s")
    return " ".join(parts)
