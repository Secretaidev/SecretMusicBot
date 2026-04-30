"""Queue display — paginated, interactive, with remove/swap support."""

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from utils.queue_manager import queue_manager
from utils.helpers import format_duration, truncate

bot = bot_client.bot
PAGE_SIZE = 10


def build_queue_text(chat_id: int, page: int = 0) -> str:
    state = queue_manager.get(chat_id)
    if not state.current and not state.queue:
        return "📭 **ǫᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ.** ᴜsᴇ /play ᴛᴏ ᴀᴅᴅ ᴍᴜsɪᴄ!"

    text = f"📜 **ǫᴜᴇᴜᴇ** │ `{len(state.queue)}` ᴛʀᴀᴄᴋs\n{'▬' * 20}\n\n"

    if state.current:
        dur = format_duration(state.current.duration)
        text += f"▶️ **ɴᴏᴡ ᴘʟᴀʏɪɴɢ:**\n└ 🎵 {truncate(state.current.title, 45)} │ `{dur}`\n\n"

    if state.queue:
        start = page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_tracks = state.queue[start:end]

        text += "**⏳ ᴜᴘ ɴᴇxᴛ:**\n"
        for i, t in enumerate(page_tracks, start + 1):
            dur = format_duration(t.duration)
            text += f"├ `{i}.` {truncate(t.title, 35)} │ `{dur}`\n"

        total_pages = (len(state.queue) + PAGE_SIZE - 1) // PAGE_SIZE
        if total_pages > 1:
            text += f"\n📄 ᴘᴀɢᴇ `{page + 1}/{total_pages}`"
    else:
        text += "*ɴᴏ ᴜᴘᴄᴏᴍɪɴɢ ᴛʀᴀᴄᴋs.*"

    # Stats
    loop_status = "🔁 ʟᴏᴏᴘ" if state.loop else "🔂 ʟᴏᴏᴘ ᴀʟʟ" if state.loop_all else "➡️ ɴᴏʀᴍᴀʟ"
    text += f"\n\n{loop_status} │ {'🔀 sʜᴜꜰꜰʟᴇ' if state.shuffle else ''} │ 🔊 `{state.volume}%`"
    return text


def queue_markup(chat_id: int, page: int = 0) -> InlineKeyboardMarkup:
    state = queue_manager.get(chat_id)
    total_pages = max(1, (len(state.queue) + PAGE_SIZE - 1) // PAGE_SIZE)
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ ᴘʀᴇᴠ", callback_data=f"qp|{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("ɴᴇxᴛ ▶️", callback_data=f"qp|{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([
        InlineKeyboardButton("🔀 sʜᴜꜰꜰʟᴇ", callback_data="qshuf"),
        InlineKeyboardButton("🗑 ᴄʟᴇᴀʀ", callback_data="qclr"),
    ])
    buttons.append([InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="qcls")])
    return InlineKeyboardMarkup(buttons)


@bot.on_message(filters.command("queue"))
async def queue_cmd(_, message):
    args = message.command[1:]
    chat_id = message.chat.id

    if args and args[0] == "remove" and len(args) > 1:
        try:
            idx = int(args[1]) - 1
            removed = queue_manager.remove(chat_id, idx)
            if removed:
                return await message.reply_text(f"✅ **ʀᴇᴍᴏᴠᴇᴅ:** {truncate(removed.title, 40)}")
            return await message.reply_text("❌ **ɪɴᴠᴀʟɪᴅ ᴘᴏsɪᴛɪᴏɴ.**")
        except ValueError:
            return await message.reply_text("❗ `/queue remove <number>`")

    if args and args[0] == "swap" and len(args) > 2:
        try:
            a, b = int(args[1]) - 1, int(args[2]) - 1
            if queue_manager.swap(chat_id, a, b):
                return await message.reply_text(f"🔄 **sᴡᴀᴘᴘᴇᴅ #{a + 1} ↔ #{b + 1}**")
            return await message.reply_text("❌ **ɪɴᴠᴀʟɪᴅ ᴘᴏsɪᴛɪᴏɴs.**")
        except ValueError:
            return await message.reply_text("❗ `/queue swap <a> <b>`")

    text = build_queue_text(chat_id)
    await message.reply_text(text, reply_markup=queue_markup(chat_id), disable_web_page_preview=True)


@bot.on_callback_query(filters.regex(r"^qp\|(\d+)$"))
async def queue_page_cb(_, query: CallbackQuery):
    page = int(query.data.split("|")[1])
    chat_id = query.message.chat.id
    text = build_queue_text(chat_id, page)
    await query.edit_message_text(text, reply_markup=queue_markup(chat_id, page), disable_web_page_preview=True)


@bot.on_callback_query(filters.regex("^qshuf$"))
async def shuffle_queue_cb(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    count = queue_manager.shuffle_queue(chat_id)
    await query.answer(f"🔀 sʜᴜꜰꜰʟᴇᴅ {count} ᴛʀᴀᴄᴋs!")
    text = build_queue_text(chat_id)
    await query.edit_message_text(text, reply_markup=queue_markup(chat_id), disable_web_page_preview=True)


@bot.on_callback_query(filters.regex("^qclr$"))
async def clear_queue_cb(_, query: CallbackQuery):
    count = queue_manager.clear(query.message.chat.id)
    await query.answer(f"🗑 ᴄʟᴇᴀʀᴇᴅ {count} ᴛʀᴀᴄᴋs.", show_alert=True)
    await query.edit_message_text("📭 **ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ.**")


@bot.on_callback_query(filters.regex("^qcls$"))
async def close_queue_cb(_, query: CallbackQuery):
    await query.answer()
    await query.message.delete()