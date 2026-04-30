"""Entrypoint – starts the bot + assistant and keeps the event loop alive.

Secret Music Bot v3.0 — The World's Most Advanced Music Bot
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import LOGGER
from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME, BOT_VERSION, LOG_GROUP

# ── Import plugins at module level so handlers register on the Client ──
# This MUST happen before bot.start() — pyrogram registers handlers
# on the Client object, and start() begins polling for updates.
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

# Import client AFTER plugins so all handlers are registered
from client.client import bot_client

BANNER = f"""
╔══════════════════════════════════════════════════╗
║           ✨ {BOT_NAME} v{BOT_VERSION} ✨           ║
║        The World's Most Advanced Music Bot        ║
╠══════════════════════════════════════════════════╣
║  🎵 YouTube • Spotify • JioSaavn • SoundCloud     ║
║  📻 Live Radio • 🎛 Audio Effects • 📜 Playlists  ║
║  🔁 Loop • 🔀 Shuffle • ❤️ Favourites • 📊 Stats  ║
║  📥 Download Songs • 🔍 Inline Search             ║
╚══════════════════════════════════════════════════╝
"""


async def main():
    if API_ID == 0 or not API_HASH or not BOT_TOKEN:
        LOGGER.critical("API_ID, API_HASH and BOT_TOKEN must be set!")
        sys.exit(1)

    for d in ("downloads", "thumbnails", "logs"):
        os.makedirs(d, exist_ok=True)

    # Start all clients — handlers already registered above
    await bot_client.start()

    # Register stream-end handler now that PyTgCalls is started
    from plugins.play import _register_stream_handler
    _register_stream_handler()

    print(BANNER)
    LOGGER.info(f"Bot: @{bot_client.bot.me.username}")

    if bot_client.user:
        LOGGER.info(f"Assistant: {bot_client.user.me.first_name} ({bot_client.user.me.id})")
    if bot_client.call:
        LOGGER.info("PyTgCalls: Ready")
    else:
        LOGGER.warning("PyTgCalls: Not available — voice chat features disabled")

    LOGGER.info(f"{BOT_NAME} v{BOT_VERSION} is fully operational!")

    # Send startup log to LOG_GROUP
    if LOG_GROUP != 0:
        try:
            assistant_status = f"✅ {bot_client.user.me.first_name}" if bot_client.user else "❌ Not Connected"
            vc_status = "✅ Ready" if bot_client.call else "❌ Disabled"
            await bot_client.bot.send_message(
                LOG_GROUP,
                f"🚀 **{BOT_NAME} Started!**\n\n"
                f"🤖 Bot: @{bot_client.bot.me.username}\n"
                f"👤 Assistant: {assistant_status}\n"
                f"🎙 Voice Chat: {vc_status}\n"
                f"📊 Version: `{BOT_VERSION}`\n"
                f"📦 Plugins: `16` loaded",
            )
        except Exception as e:
            LOGGER.warning(f"Log group message failed: {e}")

    # Keep running
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        LOGGER.info("Shutting down...")
        await bot_client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Shutdown] Bye!")
