from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from client.client import bot_client
from config import ASSISTANT_USERNAME

bot = bot_client.bot
user = bot_client.user

@bot.on_message(filters.command("leavevc"))
async def leavevc_cmd(_, message):
    chat_id = message.chat.id
    if user is None:
        return await message.reply_text("❌ **ᴀssɪsᴛᴀɴᴛ ɴᴏᴛ ᴄᴏɴꜰɪɢᴜʀᴇᴅ.**")
    try:
        await bot.promote_chat_member(chat_id, user.me.id, can_manage_voice_chats=True)
    except Exception:
        pass
    
    await message.reply_text("👋 **ʟᴇꜰᴛ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.**")

@bot.on_message(filters.command("joinvc"))
async def joinvc_cmd(_, message):
    chat_id = message.chat.id
    if user is None:
        return await message.reply_text("❌ **ᴀssɪsᴛᴀɴᴛ ɴᴏᴛ ᴄᴏɴꜰɪɢᴜʀᴇᴅ.**")
    
    if ASSISTANT_USERNAME:
        text = (
            f"👉 **ᴀᴅᴅ @{ASSISTANT_USERNAME} ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ᴀɴᴅ ᴘʀᴏᴍᴏᴛᴇ ɪᴛ ᴡɪᴛʜ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴘᴇʀᴍɪssɪᴏɴ.**\n"
            f"ᴛʜᴇɴ ᴜsᴇ `/play`"
        )
    else:
        text = (
            "👉 **ᴘʟᴇᴀsᴇ ᴀᴅᴅ ᴛʜᴇ ᴀssɪsᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ ᴍᴀɴᴜᴀʟʟʏ ᴀɴᴅ ᴘʀᴏᴍᴏᴛᴇ ɪᴛ.**\n"
            "ᴛʜᴇɴ ᴜsᴇ `/play`"
        )
    
    await message.reply_text(text)
