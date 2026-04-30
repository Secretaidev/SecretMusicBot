"""YouTube / audio download helpers using yt-dlp — advanced edition.

Supports playlists, quality selection, age-restricted bypass,
download caching, and better error handling.
"""

import asyncio
import os
import re
from typing import Optional, List

import yt_dlp

from config import DOWNLOADS_DIR, MAX_DOWNLOAD_SIZE_MB
from utils.cache import download_cache, search_cache
from utils.logger import get_logger

log = get_logger("YTUtils")


def _get_ytdlp_opts(quality: str = "192") -> dict:
    """Return yt-dlp options — works without cookies or API keys."""
    return {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": f"{DOWNLOADS_DIR}/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "age_limit": 100,
        "extract_flat": False,
        "extractor_args": {
            "youtube": {
                "player_client": ["android_music", "android", "web"],
                "skip": ["dash", "hls"],
            }
        },
        "socket_timeout": 30,
        "retries": 3,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
    }


VIDEO_OPTS = {
    "format": "best[height<=720]/best",
    "outtmpl": f"{DOWNLOADS_DIR}/%(id)s.%(ext)s",
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "age_limit": 100,
    "extractor_args": {
        "youtube": {
            "player_client": ["android_music", "android", "web"],
        }
    },
    "socket_timeout": 30,
    "retries": 3,
}


class YTSearch:
    """Lightweight yt-dlp extractor wrapper with caching."""

    @staticmethod
    async def search(query: str, limit: int = 10) -> List[dict]:
        """Return a list of {id, title, duration, uploader, url, thumbnail} dicts."""
        cache_key = f"yt_search:{query}:{limit}"
        cached = search_cache.get(cache_key)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, YTSearch._sync_search, query, limit)
        if results:
            search_cache.set(cache_key, results)
        return results

    @staticmethod
    def _sync_search(query: str, limit: int) -> List[dict]:
        opts = {**_get_ytdlp_opts(), "playlistend": limit, "extract_flat": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        except Exception as e:
            log.error(f"YouTube search error: {e}")
            return []

        entries = info.get("entries") or []
        results = []
        for e in entries:
            results.append({
                "id": e.get("id"),
                "title": e.get("title", "Unknown"),
                "duration": e.get("duration"),
                "uploader": e.get("uploader", "Unknown"),
                "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
                "thumbnail": e.get("thumbnail") or e.get("thumbnails", [{}])[0].get("url", ""),
                "source": "youtube",
            })
        return results

    @staticmethod
    async def get_info(url: str) -> Optional[dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, YTSearch._sync_info, url)

    @staticmethod
    def _sync_info(url: str) -> Optional[dict]:
        try:
            with yt_dlp.YoutubeDL(_get_ytdlp_opts()) as ydl:
                info = ydl.extract_info(url, download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader", "Unknown"),
                "url": url,
                "thumbnail": info.get("thumbnail", ""),
                "source": "youtube",
            }
        except Exception as e:
            log.error(f"YouTube info error for {url}: {e}")
            return None

    @staticmethod
    async def get_playlist(url: str, limit: int = 50) -> List[dict]:
        """Extract tracks from a YouTube playlist."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, YTSearch._sync_playlist, url, limit)

    @staticmethod
    def _sync_playlist(url: str, limit: int) -> List[dict]:
        opts = {**_get_ytdlp_opts(), "playlistend": limit, "extract_flat": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            log.error(f"YouTube playlist error: {e}")
            return []

        entries = info.get("entries") or []
        results = []
        for e in entries:
            if not e:
                continue
            results.append({
                "id": e.get("id"),
                "title": e.get("title", "Unknown"),
                "duration": e.get("duration"),
                "uploader": e.get("uploader", "Unknown"),
                "url": f"https://www.youtube.com/watch?v={e.get('id')}",
                "thumbnail": e.get("thumbnail", ""),
                "source": "youtube",
            })
        return results


class Downloader:
    """Async facade around yt-dlp downloader with caching and retries."""

    @staticmethod
    async def download(url: str, quality: str = "192", video: bool = False) -> Optional[str]:
        """Download audio/video to DOWNLOADS_DIR. Returns local file path."""
        # Check cache first
        video_id = _extract_id_from_url(url)
        if video_id and not video:
            cached = download_cache.get_path(video_id)
            if cached:
                log.info(f"Cache hit for {video_id}")
                return cached

        loop = asyncio.get_event_loop()

        # Retry up to 2 times
        for attempt in range(2):
            try:
                path = await loop.run_in_executor(
                    None, Downloader._sync_download, url, quality, video
                )
                if path:
                    if video_id:
                        download_cache.set_path(video_id, path)
                    return path
            except Exception as e:
                log.warning(f"Download attempt {attempt + 1} failed for {url}: {e}")
                if attempt < 1:
                    await asyncio.sleep(1)

        return None

    @staticmethod
    def _sync_download(url: str, quality: str, video: bool) -> Optional[str]:
        opts = VIDEO_OPTS if video else _get_ytdlp_opts(quality)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                if not video:
                    base, _ = os.path.splitext(filename)
                    mp3 = base + ".mp3"
                    if os.path.exists(mp3):
                        return mp3

                if os.path.exists(filename):
                    return filename
        except Exception as e:
            log.error(f"Download error for {url}: {e}")
        return None

    @staticmethod
    async def download_song_file(url: str, quality: str = "320") -> Optional[dict]:
        """Download a song and return path + metadata for sending as file."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, Downloader._sync_download_song, url, quality)

    @staticmethod
    def _sync_download_song(url: str, quality: str) -> Optional[dict]:
        opts = _get_ytdlp_opts(quality)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                mp3 = base + ".mp3"
                path = mp3 if os.path.exists(mp3) else filename

                if os.path.exists(path):
                    return {
                        "path": path,
                        "title": info.get("title", "Unknown"),
                        "artist": info.get("uploader", "Unknown"),
                        "duration": info.get("duration", 0),
                        "thumbnail": info.get("thumbnail", ""),
                    }
        except Exception as e:
            log.error(f"Song download error: {e}")
        return None

    @staticmethod
    def clear_old() -> None:
        """Remove files when total size exceeds budget."""
        if not os.path.isdir(DOWNLOADS_DIR):
            return
        files = [
            os.path.join(DOWNLOADS_DIR, f)
            for f in os.listdir(DOWNLOADS_DIR)
            if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
        ]
        files.sort(key=os.path.getmtime)
        total_mb = sum(os.path.getsize(f) for f in files) / (1024 * 1024)
        while total_mb > MAX_DOWNLOAD_SIZE_MB and files:
            try:
                os.remove(files.pop(0))
            except OSError:
                pass
            total_mb = sum(os.path.getsize(f) for f in files) / (1024 * 1024) if files else 0


def _extract_id_from_url(url: str) -> Optional[str]:
    """Extract video ID from a YouTube URL."""
    yt_re = re.compile(
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([^&=%\?\s]{11})"
    )
    m = yt_re.search(url)
    return m.group(1) if m else None
