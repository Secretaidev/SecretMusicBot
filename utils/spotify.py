"""Spotify integration — resolve Spotify tracks/playlists/albums to YouTube for download."""

import asyncio
from typing import List, Dict, Optional

from utils.logger import get_logger
from utils.cache import search_cache

log = get_logger("Spotify")

_sp_client = None


def _get_spotify_client():
    """Lazy-init Spotify client."""
    global _sp_client
    if _sp_client:
        return _sp_client
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            return None

        auth = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
        )
        _sp_client = spotipy.Spotify(auth_manager=auth)
        return _sp_client
    except Exception as e:
        log.error(f"Spotify init failed: {e}")
        return None


class SpotifyAPI:
    """Resolve Spotify links to searchable track info."""

    @staticmethod
    def is_available() -> bool:
        return _get_spotify_client() is not None

    @staticmethod
    async def get_track(track_id: str) -> Optional[Dict]:
        """Get track info from Spotify."""
        sp = _get_spotify_client()
        if not sp:
            return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, SpotifyAPI._sync_get_track, sp, track_id)

    @staticmethod
    def _sync_get_track(sp, track_id: str) -> Optional[Dict]:
        try:
            track = sp.track(track_id)
            artists = ", ".join(a["name"] for a in track["artists"])
            return {
                "title": track["name"],
                "artist": artists,
                "album": track.get("album", {}).get("name", ""),
                "duration": track["duration_ms"] // 1000,
                "image": track.get("album", {}).get("images", [{}])[0].get("url", ""),
                "search_query": f"{track['name']} {artists}",
                "spotify_url": track["external_urls"].get("spotify", ""),
                "source": "spotify",
            }
        except Exception as e:
            log.error(f"Spotify track error: {e}")
            return None

    @staticmethod
    async def get_playlist(playlist_id: str, limit: int = 50) -> List[Dict]:
        """Get tracks from a Spotify playlist."""
        sp = _get_spotify_client()
        if not sp:
            return []

        cache_key = f"spotify_pl:{playlist_id}"
        cached = search_cache.get(cache_key)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, SpotifyAPI._sync_get_playlist, sp, playlist_id, limit
        )
        if results:
            search_cache.set(cache_key, results)
        return results

    @staticmethod
    def _sync_get_playlist(sp, playlist_id: str, limit: int) -> List[Dict]:
        results = []
        try:
            playlist = sp.playlist_tracks(playlist_id, limit=limit)
            for item in playlist.get("items", []):
                track = item.get("track")
                if not track:
                    continue
                artists = ", ".join(a["name"] for a in track["artists"])
                results.append({
                    "title": track["name"],
                    "artist": artists,
                    "album": track.get("album", {}).get("name", ""),
                    "duration": track["duration_ms"] // 1000,
                    "image": track.get("album", {}).get("images", [{}])[0].get("url", ""),
                    "search_query": f"{track['name']} {artists}",
                    "spotify_url": track["external_urls"].get("spotify", ""),
                    "source": "spotify",
                })
        except Exception as e:
            log.error(f"Spotify playlist error: {e}")
        return results

    @staticmethod
    async def get_album(album_id: str, limit: int = 50) -> List[Dict]:
        """Get tracks from a Spotify album."""
        sp = _get_spotify_client()
        if not sp:
            return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, SpotifyAPI._sync_get_album, sp, album_id, limit
        )

    @staticmethod
    def _sync_get_album(sp, album_id: str, limit: int) -> List[Dict]:
        results = []
        try:
            album = sp.album(album_id)
            album_name = album.get("name", "")
            album_img = album.get("images", [{}])[0].get("url", "")

            for track in album.get("tracks", {}).get("items", [])[:limit]:
                artists = ", ".join(a["name"] for a in track["artists"])
                results.append({
                    "title": track["name"],
                    "artist": artists,
                    "album": album_name,
                    "duration": track["duration_ms"] // 1000,
                    "image": album_img,
                    "search_query": f"{track['name']} {artists}",
                    "source": "spotify",
                })
        except Exception as e:
            log.error(f"Spotify album error: {e}")
        return results

    @staticmethod
    async def search(query: str, limit: int = 10) -> List[Dict]:
        """Search Spotify for tracks."""
        sp = _get_spotify_client()
        if not sp:
            return []

        cache_key = f"spotify_search:{query}:{limit}"
        cached = search_cache.get(cache_key)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, SpotifyAPI._sync_search, sp, query, limit
        )
        if results:
            search_cache.set(cache_key, results)
        return results

    @staticmethod
    def _sync_search(sp, query: str, limit: int) -> List[Dict]:
        results = []
        try:
            data = sp.search(q=query, type="track", limit=limit)
            for track in data.get("tracks", {}).get("items", []):
                artists = ", ".join(a["name"] for a in track["artists"])
                results.append({
                    "title": track["name"],
                    "artist": artists,
                    "album": track.get("album", {}).get("name", ""),
                    "duration": track["duration_ms"] // 1000,
                    "image": track.get("album", {}).get("images", [{}])[0].get("url", ""),
                    "search_query": f"{track['name']} {artists}",
                    "spotify_url": track["external_urls"].get("spotify", ""),
                    "source": "spotify",
                })
        except Exception as e:
            log.error(f"Spotify search error: {e}")
        return results
