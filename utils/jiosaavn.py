import aiohttp
from typing import List, Dict, Optional

class JioSaavnAPI:
    BASE_URL = "https://jiosaavn-api-beta.vercel.app"

    @staticmethod
    async def search(query: str, limit: int = 5) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            try:
                params = {"query": query}
                async with session.get(f"{JioSaavnAPI.BASE_URL}/search/songs", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "SUCCESS":
                            results = []
                            for song in data["data"]["results"][:limit]:
                                results.append({
                                    "id": song["id"],
                                    "title": song["name"],
                                    "duration": int(song["duration"]) if song.get("duration") else 0,
                                    "uploader": song["primaryArtists"],
                                    "url": song["downloadUrl"][-1]["link"], # Highest quality
                                    "image": song["image"][-1]["link"] if song.get("image") else None,
                                    "source": "jiosaavn"
                                })
                            return results
            except Exception as e:
                print(f"[JioSaavn Error] {e}")
        return []

    @staticmethod
    async def get_info(song_id: str) -> Optional[Dict]:
        async with aiohttp.ClientSession() as session:
            try:
                params = {"id": song_id}
                async with session.get(f"{JioSaavnAPI.BASE_URL}/songs", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "SUCCESS":
                            song = data["data"][0]
                            return {
                                "id": song["id"],
                                "title": song["name"],
                                "duration": int(song["duration"]) if song.get("duration") else 0,
                                "uploader": song["primaryArtists"],
                                "url": song["downloadUrl"][-1]["link"],
                                "image": song["image"][-1]["link"] if song.get("image") else None,
                                "source": "jiosaavn"
                            }
            except Exception as e:
                print(f"[JioSaavn Error] {e}")
        return None
