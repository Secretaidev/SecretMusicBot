"""Sudo / owner-only commands — restart, logs, global broadcast, maintenance."""

import os
import sys
import asyncio
from pyrogram import filters
from client.client import bot_client
from utils.database import db
from utils.queue_manager import queue_manager
from utils.logger import get_logger
import config

log = get_logger("Sudo")
bot = bot_client.bot

_maintenance_mode = False


@bot.on_message(filters.command("restart"))
async def restart_bot(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return
    await message.reply_text("🔄 **ʀᴇsᴛᴀʀᴛɪɴɢ… ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.**")
    log.info(f"Restart triggered by {message.from_user.id}")
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.on_message(filters.command("logs"))
async def get_logs(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return
    log_file = os.path.join(config.LOGS_DIR, "bot.log")
    if os.path.exists(log_file):
        try:
            await message.reply_document(
                log_file,
                caption="📋 **ʙᴏᴛ ʟᴏɢs**",
            )
        except Exception:
            # If file too big, send last 50 lines
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            last_50 = "".join(lines[-50:])
            if len(last_50) > 4000:
                last_50 = last_50[-4000:]
            await message.reply_text(f"📋 **ʟᴀsᴛ ʟᴏɢs:**\n```\n{last_50}\n```")
    else:
        await message.reply_text("📭 **ɴᴏ ʟᴏɢs ꜰᴏᴜɴᴅ.**")


@bot.on_message(filters.command("gcast"))
async def gcast_cmd(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return
    if not message.reply_to_message:
        return await message.reply_text("❗ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ.")

    m = await message.reply_text("📢 **ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ…**")
    count, failed = 0, 0
    chats = []
    async for dialog in bot.get_dialogs():
        chats.append(dialog.chat.id)

    for chat_id in chats:
        try:
            await message.reply_to_message.forward(chat_id)
            count += 1
            await asyncio.sleep(0.3)
        except Exception:
            failed += 1

    await m.edit(
        f"✅ **ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏɴᴇ.**\n"
        f"📤 sᴇɴᴛ: `{count}` │ ❌ ꜰᴀɪʟᴇᴅ: `{failed}`"
    )


@bot.on_message(filters.command("maintenance") & filters.user(config.OWNER_ID))
async def maintenance_cmd(_, message):
    global _maintenance_mode
    _maintenance_mode = not _maintenance_mode
    status = "ᴇɴᴀʙʟᴇᴅ 🔴" if _maintenance_mode else "ᴅɪsᴀʙʟᴇᴅ 🟢"
    await message.reply_text(f"🛠 **ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ: {status}**")


@bot.on_message(filters.command("globalstats"))
async def global_stats_cmd(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return
    stats = queue_manager.get_stats()
    db_stats = await db.get_global_stats()
    groups = await db.get_group_count()

    await message.reply_text(
        f"📊 **ɢʟᴏʙᴀʟ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
        f"🎵 **ᴀᴄᴛɪᴠᴇ sᴛʀᴇᴀᴍs:** `{stats['active_chats']}`\n"
        f"📜 **ǫᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋs:** `{stats['total_queued']}`\n"
        f"🎶 **sᴇssɪᴏɴ ᴘʟᴀʏs:** `{stats['total_played']}`\n"
        f"🌍 **ᴀʟʟ-ᴛɪᴍᴇ ᴘʟᴀʏs:** `{db_stats.get('total_plays', 0)}`\n"
        f"👥 **ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs:** `{groups}`\n\n"
        f"👑 **ᴅᴇᴠ:** @its_me_secret"
    )


@bot.on_message(filters.command("eval") & filters.user(config.OWNER_ID))
async def eval_cmd(_, message):
    """Execute Python code — OWNER ONLY, use with extreme caution."""
    if len(message.command) < 2:
        return await message.reply_text("❗ `/eval <code>`")
    code = message.text.split(None, 1)[1]
    try:
        result = eval(code)
        await message.reply_text(f"✅ **ʀᴇsᴜʟᴛ:**\n```\n{result}\n```")
    except Exception as e:
        await message.reply_text(f"❌ **ᴇʀʀᴏʀ:**\n```\n{e}\n```")


def is_maintenance():
    """Check if bot is in maintenance mode."""
    return _maintenance_mode
