"""Admin commands — auth/unauth users, block/unblock, broadcast, chat info."""

import config
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from client.client import bot_client
from plugins.controls import is_admin
from utils.database import db
from utils.logger import get_logger

log = get_logger("Admin")
bot = bot_client.bot


@bot.on_message(filters.command("auth"))
async def auth_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    if not message.reply_to_message:
        return await message.reply_text("❗ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜᴏʀɪsᴇ.")
    target = message.reply_to_message.from_user
    await db.add_auth_user(chat_id, target.id)
    await message.reply_text(
        f"✅ **{target.mention} ᴀᴜᴛʜᴏʀɪsᴇᴅ** ɪɴ ᴛʜɪs ᴄʜᴀᴛ.\n"
        "ᴛʜᴇʏ ᴄᴀɴ ɴᴏᴡ ᴄᴏɴᴛʀᴏʟ ᴍᴜsɪᴄ ᴘʟᴀʏʙᴀᴄᴋ."
    )


@bot.on_message(filters.command("unauth"))
async def unauth_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    if not message.reply_to_message:
        return await message.reply_text("❗ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴜɴᴀᴜᴛʜᴏʀɪsᴇ.")
    target = message.reply_to_message.from_user
    await db.remove_auth_user(chat_id, target.id)
    await message.reply_text(f"❌ **{target.mention} ᴜɴᴀᴜᴛʜᴏʀɪsᴇᴅ.**")


@bot.on_message(filters.command("authusers"))
async def authusers_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    users = await db.get_auth_users(chat_id)
    if not users:
        return await message.reply_text("📭 **ɴᴏ ᴀᴜᴛʜᴏʀɪsᴇᴅ ᴜsᴇʀs.**")
    text = "👥 **ᴀᴜᴛʜᴏʀɪsᴇᴅ ᴜsᴇʀs:**\n\n"
    for i, uid in enumerate(users, 1):
        text += f"`{i}.` [ᴜsᴇʀ](tg://user?id={uid}) (`{uid}`)\n"
    await message.reply_text(text)


@bot.on_message(filters.command("addsudo") & filters.user(config.OWNER_ID))
async def addsudo_cmd(_, message):
    if not message.reply_to_message:
        if len(message.command) > 1:
            try:
                target = int(message.command[1])
            except ValueError:
                return await message.reply_text("❗ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ.")
        else:
            return await message.reply_text("❗ ʀᴇᴘʟʏ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ ɪᴅ.")
    else:
        target = message.reply_to_message.from_user.id
    await db.add_sudo(target)
    await message.reply_text(f"✅ **ᴜsᴇʀ `{target}` ᴀᴅᴅᴇᴅ ᴛᴏ sᴜᴅᴏ.**")


@bot.on_message(filters.command("delsudo") & filters.user(config.OWNER_ID))
async def delsudo_cmd(_, message):
    if not message.reply_to_message:
        if len(message.command) > 1:
            try:
                target = int(message.command[1])
            except ValueError:
                return await message.reply_text("❗ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ.")
        else:
            return await message.reply_text("❗ ʀᴇᴘʟʏ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ ɪᴅ.")
    else:
        target = message.reply_to_message.from_user.id
    await db.remove_sudo(target)
    await message.reply_text(f"❌ **ᴜsᴇʀ `{target}` ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ sᴜᴅᴏ.**")


@bot.on_message(filters.command("block"))
async def block_cmd(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return await message.reply_text("❌ **sᴜᴅᴏ ᴏɴʟʏ.**")
    if not message.reply_to_message:
        if len(message.command) > 1:
            try:
                target = int(message.command[1])
            except ValueError:
                return await message.reply_text("❗ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ.")
        else:
            return await message.reply_text("❗ ʀᴇᴘʟʏ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ ɪᴅ.")
    else:
        target = message.reply_to_message.from_user.id
    await db.block_user(target)
    await message.reply_text(f"🚫 **ᴜsᴇʀ `{target}` ʙʟᴏᴄᴋᴇᴅ** ꜰʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ.")


@bot.on_message(filters.command("unblock"))
async def unblock_cmd(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return await message.reply_text("❌ **sᴜᴅᴏ ᴏɴʟʏ.**")
    if not message.reply_to_message:
        if len(message.command) > 1:
            try:
                target = int(message.command[1])
            except ValueError:
                return await message.reply_text("❗ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ.")
        else:
            return await message.reply_text("❗ ʀᴇᴘʟʏ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀ ɪᴅ.")
    else:
        target = message.reply_to_message.from_user.id
    await db.unblock_user(target)
    await message.reply_text(f"✅ **ᴜsᴇʀ `{target}` ᴜɴʙʟᴏᴄᴋᴇᴅ.**")


@bot.on_message(filters.command("broadcast"))
async def broadcast_cmd(_, message):
    import asyncio
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return await message.reply_text("❌ **sᴜᴅᴏ ᴏɴʟʏ.**")
    if not message.reply_to_message:
        return await message.reply_text("❗ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.")

    m = await message.reply_text("📢 **ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ…**")
    count, failed = 0, 0
    async for dialog in bot.get_dialogs():
        try:
            await message.reply_to_message.forward(dialog.chat.id)
            count += 1
            await asyncio.sleep(0.3)
        except Exception:
            failed += 1

    await m.edit(
        f"✅ **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ.**\n"
        f"📤 **sᴇɴᴛ:** `{count}` │ ❌ **ꜰᴀɪʟᴇᴅ:** `{failed}`"
    )


@bot.on_message(filters.command("chatinfo"))
async def chatinfo_cmd(_, message):
    if message.chat.type == "private":
        return await message.reply_text("❗ **ᴜsᴇ ɪɴ ᴀ ɢʀᴏᴜᴘ.**")
    chat = message.chat
    settings = await db.get_chat_settings(chat.id)
    auth_users = await db.get_auth_users(chat.id)
    state = queue_manager.get(chat.id) if True else None
    from utils.queue_manager import queue_manager

    text = (
        f"📊 **ᴄʜᴀᴛ ɪɴꜰᴏ**\n\n"
        f"📌 **ɴᴀᴍᴇ:** {chat.title}\n"
        f"🆔 **ɪᴅ:** `{chat.id}`\n"
        f"👥 **ᴀᴜᴛʜ ᴜsᴇʀs:** `{len(auth_users)}`\n\n"
        f"⚙️ **sᴇᴛᴛɪɴɢs:**\n"
        f"├ 🎵 ǫᴜᴀʟɪᴛʏ: `{settings.get('quality', '192')}kbps`\n"
        f"├ 🔄 ᴀᴜᴛᴏᴘʟᴀʏ: `{'ᴏɴ' if settings.get('autoplay') else 'ᴏꜰꜰ'}`\n"
        f"├ 📢 ᴀɴɴᴏᴜɴᴄᴇ: `{'ᴏɴ' if settings.get('announcements') else 'ᴏꜰꜰ'}`\n"
        f"└ 👋 ᴀᴜᴛᴏ-ʟᴇᴀᴠᴇ: `{'ᴏɴ' if settings.get('auto_leave') else 'ᴏꜰꜰ'}`"
    )
    await message.reply_text(text)
