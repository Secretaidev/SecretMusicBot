from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from client.client import bot_client
from plugins.controls import is_admin
from plugins.assistant_handler import assistant_join
import config

bot = bot_client.bot
user = bot_client.user
call = bot_client.call

@bot.on_message(filters.command("leavevc"))
async def leavevc_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    
    try:
        await call.leave_call(chat_id)
        await message.reply_text("👋 **ʟᴇꜰᴛ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.**")
    except Exception as e:
        await message.reply_text(f"❌ **ᴇʀʀᴏʀ:** `{e}`")

@bot.on_message(filters.command("joinvc"))
async def joinvc_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    
    m = await message.reply_text("⏳ **ᴀssɪsᴛᴀɴᴛ ᴊᴏɪɴɪɴɢ…**")
    try:
        await assistant_join(chat_id)
        await m.edit("✅ **ᴀssɪsᴛᴀɴᴛ sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴊᴏɪɴᴇᴅ ᴛʜᴇ ᴄʜᴀᴛ.**")
    except Exception as e:
        await m.edit(f"❌ **ᴇʀʀᴏʀ:** `{e}`")
