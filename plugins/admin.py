from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from client.client import bot_client

bot = bot_client.bot

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False

@bot.on_message(filters.command("auth"))
async def auth_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜᴏʀɪsᴇ ᴛʜᴇᴍ.")
    
    target = message.reply_to_message.from_user.id
    await message.reply_text(f"✅ **ᴜsᴇʀ `{target}` ᴀᴜᴛʜᴏʀɪsᴇᴅ.**")

@bot.on_message(filters.command("broadcast") & filters.user(123456789)) # Replace with real Owner ID
async def broadcast_cmd(_, message):
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
