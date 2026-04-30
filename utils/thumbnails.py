"""Beautiful thumbnail & now-playing card generation using Pillow.

Generates premium-looking player cards with:
- Album art with blur overlay
- Gradient backgrounds
- Song title, artist, and duration overlay
- Progress bar rendered on image
"""

import os
import aiohttp
from io import BytesIO
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from config import THUMB_DIR
from utils.logger import get_logger

log = get_logger("Thumbnails")

DEFAULT_THUMB = os.path.join(THUMB_DIR, "default.jpg")

# Attempt to load a font — fallback to default
_font_cache = {}


def _get_font(size: int = 20) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if none available."""
    if size in _font_cache:
        return _font_cache[size]
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size)
                _font_cache[size] = font
                return font
            except Exception:
                continue
    font = ImageFont.load_default()
    _font_cache[size] = font
    return font


async def download_thumb(url: str, video_id: str) -> str:
    """Download a thumbnail and crop to square. Returns local path."""
    if not url:
        return DEFAULT_THUMB if os.path.exists(DEFAULT_THUMB) else ""

    path = os.path.join(THUMB_DIR, f"{video_id}.jpg")
    if os.path.exists(path):
        return path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(path, "wb") as f:
                        f.write(data)
                    _crop_square(path)
                    return path
    except Exception as e:
        log.warning(f"Thumbnail download failed: {e}")
    return DEFAULT_THUMB if os.path.exists(DEFAULT_THUMB) else ""


def _crop_square(path: str) -> None:
    """Crop image to square aspect ratio."""
    try:
        with Image.open(path) as im:
            w, h = im.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            im.crop((left, top, left + side, top + side)).save(path)
    except Exception:
        pass


def generate_now_playing_card(
    title: str,
    artist: str,
    duration_str: str,
    thumb_path: Optional[str] = None,
    progress: float = 0.0,
    requested_by: str = "Unknown",
    source: str = "YouTube",
) -> Optional[str]:
    """Generate a beautiful now-playing card image.
    
    Returns path to the generated image or None on failure.
    """
    try:
        width, height = 800, 400

        # ── Create base with gradient ─────────────────────────
        card = Image.new("RGB", (width, height), (15, 15, 25))
        draw = ImageDraw.Draw(card)

        # Draw gradient background
        for y in range(height):
            r = int(15 + (25 - 15) * y / height)
            g = int(5 + (15 - 5) * y / height)
            b = int(35 + (55 - 35) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # ── Add blurred album art as background ──────────────
        if thumb_path and os.path.exists(thumb_path):
            try:
                album_art = Image.open(thumb_path).convert("RGB")
                # Blurred background
                bg = album_art.resize((width, height))
                bg = bg.filter(ImageFilter.GaussianBlur(radius=25))
                enhancer = ImageEnhance.Brightness(bg)
                bg = enhancer.enhance(0.3)
                card.paste(bg, (0, 0))

                # Sharp album art on left
                art_size = 280
                album_art = album_art.resize((art_size, art_size), Image.LANCZOS)
                # Add rounded corners effect
                card.paste(album_art, (30, 60))

                # Add subtle border around album art
                draw = ImageDraw.Draw(card)
                draw.rectangle(
                    [(28, 58), (312, 342)],
                    outline=(255, 255, 255, 80),
                    width=2,
                )
            except Exception:
                draw = ImageDraw.Draw(card)

        # ── Text overlay ─────────────────────────────────────
        text_x = 350 if thumb_path and os.path.exists(thumb_path) else 40

        # Title
        title_font = _get_font(28)
        display_title = title[:35] + "…" if len(title) > 35 else title
        draw.text((text_x, 80), display_title, fill=(255, 255, 255), font=title_font)

        # Artist
        artist_font = _get_font(18)
        draw.text((text_x, 125), f"🎤 {artist[:30]}", fill=(180, 180, 200), font=artist_font)

        # Source & Duration
        info_font = _get_font(15)
        draw.text((text_x, 165), f"🎵 {source}  •  ⏱ {duration_str}", fill=(140, 140, 170), font=info_font)

        # Requested by
        draw.text((text_x, 195), f"👤 {requested_by[:25]}", fill=(140, 140, 170), font=info_font)

        # ── Progress bar ─────────────────────────────────────
        bar_x = text_x
        bar_y = 250
        bar_width = width - text_x - 50
        bar_height = 8

        # Background bar
        draw.rounded_rectangle(
            [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
            radius=4,
            fill=(50, 50, 70),
        )

        # Filled bar with gradient effect
        filled_width = int(bar_width * min(progress, 1.0))
        if filled_width > 0:
            draw.rounded_rectangle(
                [(bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height)],
                radius=4,
                fill=(0, 200, 255),
            )
            # Glow dot at end
            draw.ellipse(
                [
                    (bar_x + filled_width - 6, bar_y - 4),
                    (bar_x + filled_width + 6, bar_y + bar_height + 4),
                ],
                fill=(0, 230, 255),
            )

        # ── Now Playing label ─────────────────────────────────
        label_font = _get_font(13)
        draw.text((text_x, 30), "♪ NOW PLAYING", fill=(0, 200, 255), font=label_font)

        # ── Bottom bar ────────────────────────────────────────
        draw.rectangle([(0, height - 40), (width, height)], fill=(10, 10, 20))
        bottom_font = _get_font(12)
        draw.text(
            (20, height - 30),
            "✨ Secret Music Bot v3.0 — The Most Advanced Music Bot",
            fill=(100, 100, 130),
            font=bottom_font,
        )

        # ── Save ──────────────────────────────────────────────
        out_path = os.path.join(THUMB_DIR, "now_playing_card.jpg")
        card.save(out_path, "JPEG", quality=95)
        return out_path

    except Exception as e:
        log.error(f"Error generating now-playing card: {e}")
        return None
