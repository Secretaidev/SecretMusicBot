"""Pyrogram bot + assistant + PyTgCalls — production-grade client.

Uses pyrofork (modern pyrogram fork) + py-tgcalls for voice chat streaming.
"""

import asyncio
import time

try:
    from pyrogram import Client
except ImportError:
    from pyrofork import Client

import config
from utils.logger import get_logger

log = get_logger("Client")

# Import PyTgCalls safely
_pytgcalls_available = True
try:
    from pytgcalls import PyTgCalls
except Exception as e:
    _pytgcalls_available = False
    log.warning(f"PyTgCalls import failed: {e}")


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

        if config.SESSION_STRING and _pytgcalls_available:
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
        elif config.SESSION_STRING and not _pytgcalls_available:
            log.warning("SESSION_STRING set but PyTgCalls not available. Install: pip install py-tgcalls[pyrogram]")

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def start_time(self):
        return self._start_time

    async def start(self):
        """Start bot → assistant → PyTgCalls in order."""
        self._start_time = time.time()

        # 1) Start bot — with FloodWait handling
        for attempt in range(5):
            try:
                await self.bot.start()
                log.info(f"Bot @{self.bot.me.username} started.")
                break
            except Exception as e:
                err_str = str(e)
                # Handle FloodWait: wait the required seconds
                if "FLOOD_WAIT" in err_str or "FloodWait" in type(e).__name__:
                    wait = 30
                    try:
                        wait = int(e.value) if hasattr(e, 'value') else int(''.join(filter(str.isdigit, err_str.split('wait of ')[-1][:5])))
                    except Exception:
                        wait = 60
                    log.warning(f"FloodWait: waiting {wait}s before retry (attempt {attempt+1}/5)")
                    await asyncio.sleep(wait + 5)
                else:
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

        # 4) Send startup log to LOG_CHANNEL
        await self._send_startup_log()

    async def _send_startup_log(self):
        """Send startup notification to LOG_CHANNEL."""
        if config.LOG_CHANNEL == 0:
            return
        try:
            bot_info = f"@{self.bot.me.username}"
            assistant_info = f"@{self.user.me.username}" if self.user and self.user.me.username else (f"{self.user.me.first_name} ({self.user.me.id})" if self.user else "❌ Not Connected")
            pytgcalls_info = "✅ Ready" if self.call else "❌ Not Available"

            await self.bot.send_message(
                config.LOG_CHANNEL,
                f"🚀 **ʙᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**\n\n"
                f"🤖 **ʙᴏᴛ:** {bot_info}\n"
                f"👤 **ᴀssɪsᴛᴀɴᴛ:** {assistant_info}\n"
                f"🎙 **ᴘʏᴛɢᴄᴀʟʟs:** {pytgcalls_info}\n"
                f"📊 **ᴠᴇʀsɪᴏɴ:** `{config.BOT_VERSION}`\n"
                f"⏱ **sᴛᴀʀᴛᴇᴅ ᴀᴛ:** `{time.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n\n"
                f"✨ **{config.BOT_NAME}** ɪs ɴᴏᴡ ᴏɴʟɪɴᴇ!",
            )
        except Exception as e:
            log.warning(f"Failed to send startup log: {e}")

    async def stop(self):
        """Graceful shutdown in reverse order."""
        self._ready = False
        # Send shutdown log
        if config.LOG_CHANNEL != 0:
            try:
                await self.bot.send_message(config.LOG_CHANNEL, "🔴 **ʙᴏᴛ sʜᴜᴛᴛɪɴɢ ᴅᴏᴡɴ…**")
            except Exception:
                pass

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
