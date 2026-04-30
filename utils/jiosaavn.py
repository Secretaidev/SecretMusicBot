"""JioSaavn API wrapper with retry logic and playlist/album support."""

import asyncio
import aiohttp
from typing import List, Dict, Optional

from utils.logger import get_logger
from utils.cache import search_cache

log = get_logger("JioSaavn")


class JioSaavnAPI:
    BASE_URL = "https://saavn.dev/api"

    @staticmethod
    async def _request(endpoint: str, params: dict, retries: int = 2) -> Optional[dict]:
        """Make API request with retry logic."""
        for attempt in range(retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{JioSaavnAPI.BASE_URL}/{endpoint}",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success"):
                                return data.get("data")
            except asyncio.TimeoutError:
                log.warning(f"JioSaavn timeout (attempt {attempt + 1})")
            except Exception as e:
                log.error(f"JioSaavn error: {e}")
            if attempt < retries:
                await asyncio.sleep(1)
        return None

    @staticmethod
    async def search(query: str, limit: int = 10) -> List[Dict]:
        cache_key = f"jiosaavn_search:{query}:{limit}"
        cached = search_cache.get(cache_key)
        if cached:
            return cached

        data = await JioSaavnAPI._request("search/songs", {"query": query, "limit": limit})
        if not data or "results" not in data:
            return []

        results = []
        for song in data["results"][:limit]:
            try:
                download_urls = song.get("downloadUrl", [])
                url = download_urls[-1]["url"] if download_urls else ""
                images = song.get("image", [])
                image = images[-1]["url"] if images else None

                results.append({
                    "id": song.get("id", ""),
                    "title": song.get("name", "Unknown"),
                    "duration": int(song.get("duration", 0)),
                    "uploader": song.get("artists", {}).get("primary", [{}])[0].get("name", "Unknown") if song.get("artists") else song.get("primaryArtists", "Unknown"),
                    "url": url,
                    "image": image,
                    "source": "jiosaavn",
                    "album": song.get("album", {}).get("name", ""),
                    "year": song.get("year", ""),
                    "language": song.get("language", ""),
                })
            except (IndexError, KeyError, TypeError) as e:
                log.warning(f"Error parsing JioSaavn result: {e}")
                continue

        if results:
            search_cache.set(cache_key, results)
        return results

    @staticmethod
    async def get_info(song_id: str) -> Optional[Dict]:
        data = await JioSaavnAPI._request("songs", {"id": song_id})
        if not data:
            return None

        try:
            song = data[0] if isinstance(data, list) else data
            download_urls = song.get("downloadUrl", [])
            url = download_urls[-1]["url"] if download_urls else ""
            images = song.get("image", [])
            image = images[-1]["url"] if images else None

            return {
                "id": song.get("id", ""),
                "title": song.get("name", "Unknown"),
                "duration": int(song.get("duration", 0)),
                "uploader": song.get("artists", {}).get("primary", [{}])[0].get("name", "Unknown") if song.get("artists") else song.get("primaryArtists", "Unknown"),
                "url": url,
                "image": image,
                "source": "jiosaavn",
            }
        except (IndexError, KeyError, TypeError) as e:
            log.error(f"Error parsing JioSaavn info: {e}")
        return None

    @staticmethod
    async def get_lyrics(song_id: str) -> Optional[str]:
        """Fetch lyrics for a JioSaavn song."""
        data = await JioSaavnAPI._request(f"songs/{song_id}/lyrics", {})
        if data:
            return data.get("lyrics", "")
        return None

    @staticmethod
    async def get_playlist(playlist_id: str, limit: int = 50) -> List[Dict]:
        """Fetch tracks from a JioSaavn playlist."""
        data = await JioSaavnAPI._request("playlists", {"id": playlist_id, "limit": limit})
        if not data or "songs" not in data:
            return []

        results = []
        for song in data["songs"][:limit]:
            try:
                download_urls = song.get("downloadUrl", [])
                url = download_urls[-1]["url"] if download_urls else ""
                images = song.get("image", [])
                image = images[-1]["url"] if images else None

                results.append({
                    "id": song.get("id", ""),
                    "title": song.get("name", "Unknown"),
                    "duration": int(song.get("duration", 0)),
                    "uploader": song.get("primaryArtists", "Unknown"),
                    "url": url,
                    "image": image,
                    "source": "jiosaavn",
                })
            except (IndexError, KeyError, TypeError):
                continue
        return results
