"""Entrypoint – starts the bot + assistant and keeps the event loop alive.

Secret Music Bot v3.0 — The World's Most Advanced Music Bot
"""

import asyncio
import os
import sys

# Ensure working dir is on path so plugins import correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import LOGGER
from client.client import bot_client
from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME, BOT_VERSION

# ── Import all plugins so their handlers register ─────────────
import plugins.start
import plugins.play
import plugins.controls
import plugins.queue
import plugins.playlist
import plugins.admin
import plugins.voice_chat
import plugins.lyrics
import plugins.assistant_handler
import plugins.sudo
import plugins.effects
import plugins.download
import plugins.settings
import plugins.inline
import plugins.radio
import plugins.spotify_handler


BANNER = f"""
╔══════════════════════════════════════════════════╗
║           ✨ {BOT_NAME} v{BOT_VERSION} ✨           ║
║        The World's Most Advanced Music Bot        ║
╠══════════════════════════════════════════════════╣
║  Features:                                        ║
║  🎵 YouTube • Spotify • JioSaavn • SoundCloud     ║
║  📻 Live Radio • 🎛 Audio Effects • 📜 Playlists  ║
║  🔁 Loop • 🔀 Shuffle • ❤️ Favourites • 📊 Stats  ║
║  🎧 8D Audio • ⚡ Nightcore • 🌊 Vaporwave       ║
║  📥 Download Songs • 🔍 Inline Search             ║
╚══════════════════════════════════════════════════╝
"""


async def main():
    if API_ID == 0 or not API_HASH or not BOT_TOKEN:
        LOGGER.critical("API_ID, API_HASH and BOT_TOKEN must be set!")
        sys.exit(1)

    # Ensure required directories exist
    for d in ("downloads", "thumbnails", "logs"):
        os.makedirs(d, exist_ok=True)

    # Start all clients
    await bot_client.start()

    print(BANNER)
    LOGGER.info(f"Bot: @{bot_client.bot.me.username}")
    if bot_client.user:
        LOGGER.info(f"Assistant: @{bot_client.user.me.username or bot_client.user.me.id}")
    if bot_client.call:
        LOGGER.info("PyTgCalls: Ready")
    else:
        LOGGER.warning("PyTgCalls: Not available — voice chat features disabled")

    LOGGER.info(f"{BOT_NAME} v{BOT_VERSION} is fully operational!")

    # Keep running until Ctrl+C
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        LOGGER.info("Shutting down gracefully...")
        await bot_client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Shutdown] Bye!")
