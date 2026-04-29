"""Entrypoint – starts the bot + assistant and keeps the event loop alive."""

import asyncio
import os
import sys

# Ensure working dir is on path so plugins import correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.client import bot_client
from config import API_ID, API_HASH, BOT_TOKEN

# Import all plugins so their handlers register
import plugins.start
import plugins.play
import plugins.controls
import plugins.queue
import plugins.playlist
import plugins.admin
import plugins.voice_chat
import plugins.lyrics
import plugins.assistant_handler


async def main():
    if API_ID == 0 or not API_HASH or not BOT_TOKEN:
        print("[Error] API_ID, API_HASH and BOT_TOKEN must be set in config.py or env vars.")
        sys.exit(1)

    # Ensure download dirs exist
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("thumbnails", exist_ok=True)

    await bot_client.start()

    print("=" * 50)
    print("  SongStream is running!")
    print(f"  Bot      : @{bot_client.bot.me.username}")
    if bot_client.user:
        print(f"  Assistant: @{bot_client.user.me.username or bot_client.user.me.id}")
    print("=" * 50)

    # Keep running until Ctrl+C
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await bot_client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Shutdown] Bye!")
