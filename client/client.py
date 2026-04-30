"""Bot + Assistant + PyTgCalls client."""

import asyncio
import time

from pyrogram import Client
import config
from utils.logger import get_logger

log = get_logger("Client")

_pytgcalls_available = True
try:
    from pytgcalls import PyTgCalls
except Exception as e:
    _pytgcalls_available = False
    log.warning(f"PyTgCalls not available: {e}")


class BotClient:
    def __init__(self):
        self.bot = Client(
            "SecretMusicBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
        )
        self.user = None
        self.call = None
        self._ready = False
        self._start_time = None

        if config.SESSION_STRING and _pytgcalls_available:
            try:
                self.user = Client(
                    "SecretAssistant",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=config.SESSION_STRING,
                )
                self.call = PyTgCalls(self.user)
            except Exception as e:
                log.error(f"Assistant init failed: {e}")
                self.user = None
                self.call = None

    @property
    def is_ready(self):
        return self._ready

    @property
    def start_time(self):
        return self._start_time

    async def start(self):
        self._start_time = time.time()

        # Start bot with FloodWait handling
        for attempt in range(3):
            try:
                await self.bot.start()
                log.info(f"Bot @{self.bot.me.username} started.")
                break
            except Exception as e:
                if "FLOOD_WAIT" in str(e) or "FloodWait" in type(e).__name__:
                    wait = getattr(e, 'value', 60)
                    log.warning(f"FloodWait {wait}s (attempt {attempt+1}/3)")
                    await asyncio.sleep(int(wait) + 5)
                else:
                    log.critical(f"Bot start failed: {e}")
                    raise

        # Start assistant
        if self.user:
            for attempt in range(3):
                try:
                    await self.user.start()
                    log.info(f"Assistant: {self.user.me.first_name} ({self.user.me.id})")
                    break
                except Exception as e:
                    log.error(f"Assistant attempt {attempt+1}/3: {e}")
                    if attempt == 2:
                        self.user = None
                        self.call = None
                    else:
                        await asyncio.sleep(3)

        # Start PyTgCalls
        if self.call:
            try:
                await self.call.start()
                log.info("PyTgCalls started.")
            except Exception as e:
                log.error(f"PyTgCalls failed: {e}")
                self.call = None

        self._ready = True

        # Log to channel
        if config.LOG_CHANNEL != 0:
            try:
                a = f"✅ {self.user.me.first_name}" if self.user else "❌"
                v = "✅" if self.call else "❌"
                await self.bot.send_message(config.LOG_CHANNEL,
                    f"🚀 **Bot Started!**\n\n🤖 @{self.bot.me.username}\n👤 {a}\n🎙 {v}")
            except Exception:
                pass

    async def stop(self):
        self._ready = False
        if config.LOG_CHANNEL != 0:
            try:
                await self.bot.send_message(config.LOG_CHANNEL, "🔴 **Bot stopping...**")
            except Exception:
                pass
        for name, client in [("PyTgCalls", self.call), ("Assistant", self.user), ("Bot", self.bot)]:
            if client:
                try:
                    await client.stop()
                    log.info(f"{name} stopped.")
                except Exception as e:
                    log.warning(f"{name} stop error: {e}")


bot_client = BotClient()
