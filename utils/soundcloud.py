"""SoundCloud support via yt-dlp."""

import asyncio
from typing import Optional, List

from utils.yt_utils import Downloader
from utils.cache import search_cache
from utils.logger import get_logger

log = get_logger("SoundCloud")


class SoundCloudAPI:
    """SoundCloud search and download using yt-dlp as backend."""

    @staticmethod
    async def search(query: str, limit: int = 5) -> List[dict]:
        """Search SoundCloud for tracks."""
        cache_key = f"sc_search:{query}:{limit}"
        cached = search_cache.get(cache_key)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, SoundCloudAPI._sync_search, query, limit)
        if results:
            search_cache.set(cache_key, results)
        return results

    @staticmethod
    def _sync_search(query: str, limit: int) -> List[dict]:
        import yt_dlp
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlistend": limit,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"scsearch{limit}:{query}", download=False)
        except Exception as e:
            log.error(f"SoundCloud search error: {e}")
            return []

        entries = info.get("entries") or []
        results = []
        for e in entries:
            results.append({
                "id": e.get("id", ""),
                "title": e.get("title", "Unknown"),
                "duration": e.get("duration"),
                "uploader": e.get("uploader", "Unknown"),
                "url": e.get("url", ""),
                "thumbnail": e.get("thumbnail", ""),
                "source": "soundcloud",
            })
        return results

    @staticmethod
    async def download(url: str) -> Optional[str]:
        """Download a SoundCloud track."""
        return await Downloader.download(url)
