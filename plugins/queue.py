from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from client.client import bot_client
from utils.queue_manager import queue_manager

bot = bot_client.bot

def build_queue_text(chat_id: int) -> str:
    state = queue_manager.get(chat_id)
    if not state.current and not state.queue:
        return "📭 **ᴛʜᴇ ǫᴜᴇᴜᴇ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴇᴍᴘᴛʏ.**\nᴜsᴇ /play ᴛᴏ ᴀᴅᴅ sᴏᴍᴇ ᴍᴜsɪᴄ!"
    
    text = f"📜 **ᴜᴘᴄᴏᴍɪɴɢ ᴛʀᴀᴄᴋs** | `{len(state.queue)}` ᴛʀᴀᴄᴋs\n"
    text += "▬" * 15 + "\n\n"
    
    if state.current:
        text += f"**▶️ ɴᴏᴡ ᴘʟᴀʏɪɴɢ:**\n└ [{state.current.title[:50]}]({state.current.url})\n\n"
    
    if state.queue:
        text += "**⏳ ɴᴇxᴛ ɪɴ ǫᴜᴇᴜᴇ:**\n"
        for i, t in enumerate(state.queue[:15], 1):
            dur = _fmt(t.duration)
            text += f"├ `{i}.` [{t.title[:35]}]({t.url}) | `{dur}`\n"
        
        if len(state.queue) > 15:
            text += f"└ *...ᴀɴᴅ {len(state.queue) - 15} ᴍᴏʀᴇ ᴛʀᴀᴄᴋs.*\n"
    else:
        text += "*ɴᴏ ᴜᴘᴄᴏᴍɪɴɢ ᴛʀᴀᴄᴋs.*"
        
    return text

@bot.on_message(filters.command("queue"))
async def queue_cmd(_, message):
    text = build_queue_text(message.chat.id)
    buttons = [
        [
            InlineKeyboardButton("🗑 ᴄʟᴇᴀʀ ǫᴜᴇᴜᴇ", callback_data="qclr"),
            InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="qcls"),
        ],
        [
            InlineKeyboardButton("👑 ᴅᴇᴠ:- @its_me_secret 👑", url="https://t.me/its_me_secret"),
        ],
    ]
    await message.reply_text(
        text, 
        reply_markup=InlineKeyboardMarkup(buttons), 
        disable_web_page_preview=True
    )

@bot.on_callback_query(filters.regex("^qclr$"))
async def clear_queue_cb(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    count = queue_manager.clear(chat_id)
    await query.answer(f"ᴄʟᴇᴀʀᴇᴅ {count} ᴛʀᴀᴄᴋs.", show_alert=True)
    await query.edit_message_text("📭 **ǫᴜᴇᴜᴇ ʜᴀs ʙᴇᴇɴ ᴄʟᴇᴀʀᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ.**")

@bot.on_callback_query(filters.regex("^qcls$"))
async def close_queue_cb(_, query: CallbackQuery):
    await query.answer()
    await query.message.delete()

def _fmt(seconds):
    if not seconds:
        return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"