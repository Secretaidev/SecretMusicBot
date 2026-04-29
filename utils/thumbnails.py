"""Thumbnail downloader & formatter."""

import os
import aiohttp
from PIL import Image
from config import THUMB_DIR

DEFAULT_THUMB = os.path.join(THUMB_DIR, "default.jpg")


async def download_thumb(url: str, video_id: str) -> str:
    """Download a YouTube thumbnail and crop to 1:1. Returns local path."""
    path = os.path.join(THUMB_DIR, f"{video_id}.jpg")
    if os.path.exists(path):
        return path
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(path, "wb") as f:
                        f.write(data)
                    _crop_square(path)
                    return path
    except Exception:
        pass
    return DEFAULT_THUMB if os.path.exists(DEFAULT_THUMB) else ""


def _crop_square(path: str) -> None:
    try:
        with Image.open(path) as im:
            w, h = im.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            im.crop((left, top, left + side, top + side)).save(path)
    except Exception:
        pass
