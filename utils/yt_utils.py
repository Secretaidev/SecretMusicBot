"""YouTube / audio download helpers using yt-dlp."""

import asyncio
import os
import re
import shutil
from typing import Optional
import yt_dlp
from config import DOWNLOADS_DIR, MAX_DOWNLOAD_SIZE_MB

YTDLP_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": f"{DOWNLOADS_DIR}/%(id)s.%(ext)s",
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


class YTSearch:
    """Lightweight yt-dlp extractor wrapper."""

    @staticmethod
    async def search(query: str, limit: int = 5) -> list[dict]:
        """Return a list of {id, title, duration, uploader, url} dicts."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, YTSearch._sync_search, query, limit)

    @staticmethod
    def _sync_search(query: str, limit: int) -> list[dict]:
        opts = {**YTDLP_OPTS, "playlistend": limit, "extract_flat": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            except Exception:
                return []
        entries = info.get("entries") or []
        results = []
        for e in entries:
            results.append(
                {
                    "id": e.get("id"),
                    "title": e.get("title"),
                    "duration": e.get("duration"),
                    "uploader": e.get("uploader"),
                    "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
                }
            )
        return results

    @staticmethod
    async def get_info(url: str) -> Optional[dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, YTSearch._sync_info, url)

    @staticmethod
    def _sync_info(url: str) -> Optional[dict]:
        try:
            with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
                info = ydl.extract_info(url, download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "url": info.get("url"),
                "thumbnail": info.get("thumbnail"),
            }
        except Exception:
            return None


class Downloader:
    """Async facade around yt-dlp downloader."""

    @staticmethod
    async def download(url: str) -> Optional[str]:
        """Download audio to DOWNLOADS_DIR and return local file path."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, Downloader._sync_download, url)

    @staticmethod
    def _sync_download(url: str) -> Optional[str]:
        try:
            with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # postprocessors change extension
                base, _ = os.path.splitext(filename)
                mp3 = base + ".mp3"
                if os.path.exists(mp3):
                    return mp3
                # fallback if ext stayed same
                if os.path.exists(filename):
                    return filename
        except Exception:
            return None
        return None

    @staticmethod
    def clear_old() -> None:
        """Remove files older than a threshold or exceeding size budget."""
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
            os.remove(files.pop(0))
            total_mb = sum(os.path.getsize(f) for f in files) / (1024 * 1024)


# Simple URL validator ---------------------------------------------------------
YT_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/"
    r"(watch\?v=|embed/|v/|\?v=)?([^&=%\?]{11})"
)
SPOTIFY_REGEX = re.compile(r"https?://open\.spotify\.com/track/[\w]+")


def extract_yt_id(text: str) -> Optional[str]:
    m = YT_REGEX.search(text)
    return m.group(6) if m else None
