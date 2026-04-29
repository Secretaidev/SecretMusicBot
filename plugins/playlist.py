from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from client.client import bot_client
from utils.yt_utils import YTSearch, Downloader
from utils.thumbnails import download_thumb
from utils.queue_manager import queue_manager, Track
from plugins.play import _start_playback

bot = bot_client.bot

_user_favs = {}

@bot.on_message(filters.command("favourite"))
async def favourite_cmd(_, message):
    user_id = message.from_user.id
    if user_id not in _user_favs or not _user_favs[user_id]:
        return await message.reply_text("📭 **ɴᴏ ꜰᴀᴠᴏᴜʀɪᴛᴇs ʏᴇᴛ.**")
    
    text = "⭐ **ʏᴏᴜʀ ꜰᴀᴠᴏᴜʀɪᴛᴇs**\n\n"
    for i, t in enumerate(_user_favs[user_id][:20], 1):
        text += f"`{i}.` [{t['title']}]({t['url']})\n"
    
    await message.reply_text(text, disable_web_page_preview=True)

@bot.on_message(filters.command("like"))
async def like_cmd(_, message):
    await message.reply_text("🤍 **ʟɪᴋᴇ ꜰᴇᴀᴛᴜʀᴇ ʀᴇǫᴜɪʀᴇs ᴅᴀᴛᴀʙᴀsᴇ ɪɴᴛᴇɢʀᴀᴛɪᴏɴ.**")
