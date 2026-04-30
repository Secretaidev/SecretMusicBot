"""Secret Music Bot — Entry Point"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for d in ("downloads", "thumbnails", "logs"):
    os.makedirs(d, exist_ok=True)

from utils.logger import LOGGER
from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME, LOG_GROUP
from client.client import bot_client

bot = bot_client.bot

# Load all plugins
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

LOGGER.info("16 plugins loaded.")


async def start_bot():
    if API_ID == 0 or not API_HASH or not BOT_TOKEN:
        LOGGER.critical("Set API_ID, API_HASH, BOT_TOKEN!")
        sys.exit(1)

    await bot_client.start()

    # Register stream handler after PyTgCalls started
    try:
        from plugins.play import _register_stream_handler
        _register_stream_handler()
    except Exception as e:
        LOGGER.warning(f"Stream handler: {e}")

    LOGGER.info(f"Bot @{bot.me.username} is running!")

    if LOG_GROUP != 0:
        try:
            a = f"✅ {bot_client.user.me.first_name}" if bot_client.user else "❌"
            v = "✅" if bot_client.call else "❌"
            await bot.send_message(LOG_GROUP,
                f"🚀 **{BOT_NAME} Started!**\n\n"
                f"🤖 @{bot.me.username}\n👤 {a}\n🎙 {v}")
        except Exception as e:
            LOGGER.warning(f"Log: {e}")

    LOGGER.info("Listening for messages...")

    # Keep alive forever
    from pyrogram import idle
    await idle()


# CRITICAL: Use bot.run() — NOT asyncio.run()
# bot.run() uses the SAME event loop that pyrogram's Client was initialized on.
# asyncio.run() creates a NEW loop, breaking pyrogram's internal dispatcher.
bot.run(start_bot())
