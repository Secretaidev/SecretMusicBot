"""Voice chat management — join, leave, VC info, auto-leave."""

import asyncio
from pyrogram import filters
from client.client import bot_client
from plugins.controls import is_admin
from plugins.assistant_handler import assistant_join
from plugins.play import _leave_vc
from utils.queue_manager import queue_manager
from utils.helpers import format_duration
from utils.logger import get_logger
import config

log = get_logger("VoiceChat")
bot = bot_client.bot
call = bot_client.call


@bot.on_message(filters.command("leavevc"))
async def leavevc_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    queue_manager.clear(c)
    await _leave_vc(c)
    await message.reply_text("👋 **ʟᴇꜰᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.**")


@bot.on_message(filters.command("joinvc"))
async def joinvc_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    m = await message.reply_text("⏳ **ᴊᴏɪɴɪɴɢ…**")
    try:
        await assistant_join(c)
        await m.edit("✅ **ᴀssɪsᴛᴀɴᴛ ᴊᴏɪɴᴇᴅ!**")
    except Exception as e:
        await m.edit(f"❌ `{e}`")


@bot.on_message(filters.command("vcinfo"))
async def vcinfo_cmd(_, message):
    c = message.chat.id
    s = queue_manager.get(c)
    status = "▶️ ᴘʟᴀʏɪɴɢ" if s.is_playing and not s.is_paused else "⏸ ᴘᴀᴜsᴇᴅ" if s.is_paused else "⏹ ɪᴅʟᴇ"
    current = s.current.title if s.current else "ɴᴏɴᴇ"
    dur = format_duration(s.current.duration) if s.current else "—"
    loop = "🔁 ᴏɴᴇ" if s.loop else ("🔂 ᴀʟʟ" if s.loop_all else "➡️ ᴏꜰꜰ")
    fx = []
    if s.bass_boost: fx.append("🔊ʙᴀss")
    if s.nightcore: fx.append("⚡ɴᴄ")
    if s.vaporwave: fx.append("🌊ᴠᴡ")
    if s.eight_d: fx.append("🎧8ᴅ")

    await message.reply_text(
        f"🎙 **ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪɴꜰᴏ**\n\n"
        f"📡 {status}\n"
        f"🎵 {current}\n"
        f"⏱ `{dur}` │ 🔊 `{s.volume}%`\n"
        f"📜 `{len(s.queue)}` ǫᴜᴇᴜᴇᴅ\n"
        f"🔁 {loop} │ 🔀 {'ᴏɴ' if s.shuffle else 'ᴏꜰꜰ'}\n"
        f"🎛 {' │ '.join(fx) if fx else 'ɴᴏɴᴇ'} │ ⚡ `{s.speed}x`"
    )


async def auto_leave_check(chat_id: int):
    """Auto-leave if idle for too long."""
    await asyncio.sleep(config.AUTO_LEAVE_TIMEOUT)
    s = queue_manager.get(chat_id)
    if not s.is_playing and not s.queue:
        await _leave_vc(chat_id)
        try:
            await bot.send_message(chat_id, "👋 **ᴀᴜᴛᴏ-ʟᴇꜰᴛ ᴅᴜᴇ ᴛᴏ ɪɴᴀᴄᴛɪᴠɪᴛʏ.**")
        except Exception:
            pass
