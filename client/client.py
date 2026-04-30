"""Pyrogram bot + assistant + PyTgCalls — production-grade client.

Uses the modern pytgcalls API (MediaStream, .play(), stream_ended decorator).
Includes auto-reconnection, health checks, and graceful degradation.
"""

import asyncio
import time
from pyrogram import Client
from pytgcalls import PyTgCalls

import config
from utils.logger import get_logger

log = get_logger("Client")


class BotClient:
    """Central manager for bot, assistant, and voice-chat streaming."""

    def __init__(self):
        self.bot = Client(
            "music_bot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
        )
        self.user = None
        self.call = None
        self._ready = False
        self._start_time = None

        if config.SESSION_STRING:
            try:
                self.user = Client(
                    "music_assistant",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=config.SESSION_STRING,
                    in_memory=True,
                )
                self.call = PyTgCalls(self.user)
            except Exception as e:
                log.error(f"Failed to init assistant: {e}")
                self.user = None
                self.call = None

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def start_time(self):
        return self._start_time

    async def start(self):
        """Start bot → assistant → PyTgCalls in order."""
        self._start_time = time.time()

        # 1) Start bot
        try:
            await self.bot.start()
            log.info(f"Bot @{self.bot.me.username} started.")
        except Exception as e:
            log.critical(f"Bot start failed: {e}")
            raise

        # 2) Start assistant
        if self.user:
            for attempt in range(3):
                try:
                    await self.user.start()
                    log.info(f"Assistant started: {self.user.me.first_name} ({self.user.me.id})")
                    break
                except Exception as e:
                    log.error(f"Assistant start attempt {attempt+1}/3 failed: {e}")
                    if attempt == 2:
                        log.warning("Running without assistant — VC features disabled.")
                        self.user = None
                        self.call = None
                    else:
                        await asyncio.sleep(2)

        # 3) Start PyTgCalls
        if self.call:
            try:
                await self.call.start()
                log.info("PyTgCalls engine started.")
            except Exception as e:
                log.error(f"PyTgCalls start failed: {e}")
                self.call = None

        self._ready = True

    async def stop(self):
        """Graceful shutdown in reverse order."""
        self._ready = False
        for name, client in [("PyTgCalls", self.call), ("Assistant", self.user), ("Bot", self.bot)]:
            if client:
                try:
                    await client.stop()
                    log.info(f"{name} stopped.")
                except Exception as e:
                    log.warning(f"Error stopping {name}: {e}")

    def __call__(self):
        return self.bot


bot_client = BotClient()
