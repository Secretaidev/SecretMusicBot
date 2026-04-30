"""Group settings — interactive settings panel with inline buttons."""

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from plugins.controls import is_admin
from utils.database import db
from utils.logger import get_logger

log = get_logger("Settings")
bot = bot_client.bot


def settings_markup(settings: dict) -> InlineKeyboardMarkup:
    quality = settings.get("quality", "192")
    autoplay = settings.get("autoplay", False)
    auto_leave = settings.get("auto_leave", True)
    announcements = settings.get("announcements", True)

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🎵 ǫᴜᴀʟɪᴛʏ: {quality}kbps",
            callback_data="set|quality",
        )],
        [InlineKeyboardButton(
            f"🔄 ᴀᴜᴛᴏᴘʟᴀʏ: {'ᴏɴ ✅' if autoplay else 'ᴏꜰꜰ ❌'}",
            callback_data="set|autoplay",
        )],
        [InlineKeyboardButton(
            f"👋 ᴀᴜᴛᴏ-ʟᴇᴀᴠᴇ: {'ᴏɴ ✅' if auto_leave else 'ᴏꜰꜰ ❌'}",
            callback_data="set|auto_leave",
        )],
        [InlineKeyboardButton(
            f"📢 ᴀɴɴᴏᴜɴᴄᴇ: {'ᴏɴ ✅' if announcements else 'ᴏꜰꜰ ❌'}",
            callback_data="set|announcements",
        )],
        [InlineKeyboardButton("🔙 ᴄʟᴏsᴇ", callback_data="set|close")],
    ])


@bot.on_message(filters.command("settings") & filters.group)
async def settings_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")

    settings = await db.get_chat_settings(chat_id)
    text = (
        f"⚙️ **ɢʀᴏᴜᴘ sᴇᴛᴛɪɴɢs**\n\n"
        f"ᴄᴏɴꜰɪɢᴜʀᴇ ʏᴏᴜʀ ᴍᴜsɪᴄ ʙᴏᴛ sᴇᴛᴛɪɴɢs ʙᴇʟᴏᴡ.\n"
        f"ᴛᴀᴘ ᴀ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴛᴏɢɢʟᴇ."
    )
    await message.reply_text(text, reply_markup=settings_markup(settings))


@bot.on_callback_query(filters.regex(r"^set\|(.+)$"))
async def settings_cb(_, query: CallbackQuery):
    action = query.data.split("|")[1]
    chat_id = query.message.chat.id

    if action == "close":
        await query.message.delete()
        return await query.answer()

    if not await is_admin(chat_id, query.from_user.id):
        return await query.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ.", show_alert=True)

    settings = await db.get_chat_settings(chat_id)

    if action == "quality":
        # Cycle: 128 → 192 → 320 → 128
        current = settings.get("quality", "192")
        cycle = {"128": "192", "192": "320", "320": "128"}
        new_quality = cycle.get(current, "192")
        await db.update_chat_settings(chat_id, quality=new_quality)
        settings["quality"] = new_quality
        await query.answer(f"🎵 ǫᴜᴀʟɪᴛʏ: {new_quality}kbps")

    elif action == "autoplay":
        new_val = not settings.get("autoplay", False)
        await db.update_chat_settings(chat_id, autoplay=new_val)
        settings["autoplay"] = new_val
        await query.answer(f"🔄 ᴀᴜᴛᴏᴘʟᴀʏ: {'ᴏɴ' if new_val else 'ᴏꜰꜰ'}")

    elif action == "auto_leave":
        new_val = not settings.get("auto_leave", True)
        await db.update_chat_settings(chat_id, auto_leave=new_val)
        settings["auto_leave"] = new_val
        await query.answer(f"👋 ᴀᴜᴛᴏ-ʟᴇᴀᴠᴇ: {'ᴏɴ' if new_val else 'ᴏꜰꜰ'}")

    elif action == "announcements":
        new_val = not settings.get("announcements", True)
        await db.update_chat_settings(chat_id, announcements=new_val)
        settings["announcements"] = new_val
        await query.answer(f"📢 ᴀɴɴᴏᴜɴᴄᴇ: {'ᴏɴ' if new_val else 'ᴏꜰꜰ'}")

    try:
        await query.edit_message_reply_markup(reply_markup=settings_markup(settings))
    except Exception:
        pass
