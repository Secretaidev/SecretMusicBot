"""Inline mode — search and share songs directly from any chat."""

from pyrogram import filters
from pyrogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from client.client import bot_client
from utils.yt_utils import YTSearch
from utils.helpers import format_duration, truncate
from utils.logger import get_logger

log = get_logger("Inline")
bot = bot_client.bot


@bot.on_inline_query()
async def inline_search(_, query: InlineQuery):
    search_query = query.query.strip()
    if not search_query or len(search_query) < 3:
        return await query.answer(
            results=[],
            switch_pm_text="🎵 ᴛʏᴘᴇ ᴀ sᴏɴɢ ɴᴀᴍᴇ ᴛᴏ sᴇᴀʀᴄʜ",
            switch_pm_parameter="start",
            cache_time=5,
        )

    try:
        results = await YTSearch.search(search_query, limit=10)
    except Exception as e:
        log.error(f"Inline search error: {e}")
        results = []

    if not results:
        return await query.answer(
            results=[],
            switch_pm_text="❌ ɴᴏ ʀᴇsᴜʟᴛs ꜰᴏᴜɴᴅ",
            switch_pm_parameter="start",
            cache_time=10,
        )

    articles = []
    for r in results[:10]:
        dur = format_duration(r.get("duration"))
        title = r.get("title", "Unknown")
        uploader = r.get("uploader", "Unknown")
        url = r.get("url", f"https://www.youtube.com/watch?v={r['id']}")

        text = (
            f"🎵 **{title}**\n\n"
            f"🎤 **ᴀʀᴛɪsᴛ:** {uploader}\n"
            f"⏱ **ᴅᴜʀᴀᴛɪᴏɴ:** `{dur}`\n\n"
            f"🔗 [ᴡᴀᴛᴄʜ ᴏɴ ʏᴏᴜᴛᴜʙᴇ]({url})\n\n"
            f"💡 **ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴜsᴇ** `/play {title[:30]}` **ᴛᴏ ᴘʟᴀʏ!**"
        )

        articles.append(
            InlineQueryResultArticle(
                title=truncate(title, 50),
                description=f"🎤 {uploader} • ⏱ {dur}",
                input_message_content=InputTextMessageContent(
                    text, disable_web_page_preview=True,
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("▶️ ᴘʟᴀʏ ɪɴ ɢʀᴏᴜᴘ", url=f"https://t.me/{bot.me.username}?startgroup=true")],
                ]),
                thumb_url=r.get("thumbnail", ""),
            )
        )

    await query.answer(results=articles, cache_time=30)
