import config
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from client.client import bot_client
from plugins.controls import is_admin
from utils.database import db

bot = bot_client.bot

@bot.on_message(filters.command("auth"))
async def auth_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜᴏʀɪsᴇ ᴛʜᴇᴍ.")
    
    target = message.reply_to_message.from_user.id
    await db.add_auth_user(chat_id, target)
    await message.reply_text(f"✅ **ᴜsᴇʀ `{target}` ᴀᴜᴛʜᴏʀɪsᴇᴅ in this chat.**")

@bot.on_message(filters.command("unauth"))
async def unauth_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴜɴᴀᴜᴛʜᴏʀɪsᴇ ᴛʜᴇᴍ.")
    
    target = message.reply_to_message.from_user.id
    await db.remove_auth_user(chat_id, target)
    await message.reply_text(f"❌ **ᴜsᴇʀ `{target}` ᴜɴᴀᴜᴛʜᴏʀɪsᴇᴅ.**")

@bot.on_message(filters.command("addsudo") & filters.user(config.OWNER_ID))
async def addsudo_cmd(_, message):
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴅᴅ ᴀs sᴜᴅᴏ.")
    target = message.reply_to_message.from_user.id
    await db.add_sudo(target)
    await message.reply_text(f"✅ **ᴜsᴇʀ `{target}` ᴀᴅᴅᴇᴅ ᴛᴏ sᴜᴅᴏᴇʀs.**")

@bot.on_message(filters.command("delsudo") & filters.user(config.OWNER_ID))
async def delsudo_cmd(_, message):
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ʀᴇᴍᴏᴠᴇ ꜰʀᴏᴍ sᴜᴅᴏ.")
    target = message.reply_to_message.from_user.id
    await db.remove_sudo(target)
    await message.reply_text(f"❌ **ᴜsᴇʀ `{target}` ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ sᴜᴅᴏᴇʀs.**")

@bot.on_message(filters.command("broadcast"))
async def broadcast_cmd(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return await message.reply_text("❌ **sᴜᴅᴏ ᴜsᴇʀs ᴏɴʟʏ.**")
    
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.")
    
    m = await message.reply_text("📢 **ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ…**")
    count = 0
    async for dialog in bot.get_dialogs():
        try:
            await message.reply_to_message.forward(dialog.chat.id)
            count += 1
        except Exception:
            pass
    
    await m.edit(f"✅ **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.**\n✨ **sᴇɴᴛ ᴛᴏ `{count}` ᴄʜᴀᴛs.**")
