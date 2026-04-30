"""Entrypoint – Secret Music Bot v3.0

Uses proven pyrogram pattern: handlers → start → idle
"""

import os
import sys
import logging
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for d in ("downloads", "thumbnails", "logs"):
    os.makedirs(d, exist_ok=True)

from pyrogram import idle, filters
from utils.logger import LOGGER
from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME, BOT_VERSION, LOG_GROUP
from client.client import bot_client

bot = bot_client.bot

# ═══ CATCH-ALL DEBUG HANDLER (register first) ═══
@bot.on_message(filters.command(["alive", "ping"]))
async def alive_handler(client, message):
    """Simple test — if this doesn't work, pyrogram itself is broken."""
    await message.reply_text(f"✅ **{BOT_NAME}** is alive! v{BOT_VERSION}")


# ═══ Load all plugin handlers ═══
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

LOGGER.info("All 16 plugins loaded.")


async def main():
    if API_ID == 0 or not API_HASH or not BOT_TOKEN:
        LOGGER.critical("Set API_ID, API_HASH, BOT_TOKEN!")
        sys.exit(1)

    # Start everything
    await bot_client.start()

    # Register stream handler after PyTgCalls init
    try:
        from plugins.play import _register_stream_handler
        _register_stream_handler()
    except Exception as e:
        LOGGER.warning(f"Stream handler: {e}")

    LOGGER.info(f"Bot: @{bot.me.username}")
    if bot_client.user:
        LOGGER.info(f"Assistant: {bot_client.user.me.first_name}")
    LOGGER.info(f"VC: {'Ready' if bot_client.call else 'Disabled'}")
    LOGGER.info(f"{BOT_NAME} v{BOT_VERSION} — Listening!")

    # Log to group
    if LOG_GROUP != 0:
        try:
            a = f"✅ {bot_client.user.me.first_name}" if bot_client.user else "❌"
            v = "✅" if bot_client.call else "❌"
            await bot.send_message(LOG_GROUP,
                f"🚀 **{BOT_NAME} Online!**\n\n🤖 @{bot.me.username}\n"
                f"👤 {a}\n🎙 {v}\n📊 `{BOT_VERSION}`")
        except Exception as e:
            LOGGER.warning(f"Log: {e}")

    # Use pyrogram's built-in idle — this is the proven way
    await idle()

    await bot_client.stop()


if __name__ == "__main__":
    # Show pyrogram dispatcher activity
    logging.getLogger("pyrogram.dispatcher").setLevel(logging.DEBUG)

    bot.run(main())
