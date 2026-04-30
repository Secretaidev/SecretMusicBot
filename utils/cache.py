"""In-memory caching utilities to avoid redundant API calls and downloads."""

import time
from typing import Any, Optional
from cachetools import TTLCache, LRUCache


class SearchCache:
    """TTL-based cache for search results — avoids hammering YouTube/Spotify APIs."""

    def __init__(self, maxsize: int = 200, ttl: int = 300):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()


class DownloadCache:
    """Track which files have been downloaded to avoid duplicates."""

    def __init__(self, maxsize: int = 500):
        self._cache = LRUCache(maxsize=maxsize)

    def get_path(self, track_id: str) -> Optional[str]:
        entry = self._cache.get(track_id)
        if entry:
            import os
            if os.path.exists(entry["path"]):
                return entry["path"]
            # File was deleted, remove from cache
            try:
                del self._cache[track_id]
            except KeyError:
                pass
        return None

    def set_path(self, track_id: str, path: str) -> None:
        self._cache[track_id] = {"path": path, "time": time.time()}

    def clear(self) -> None:
        self._cache.clear()


# ── Global cache instances ────────────────────────────────────
search_cache = SearchCache()
download_cache = DownloadCache()
