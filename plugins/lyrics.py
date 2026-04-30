"""Lyrics finder — uses lyrics.ovh API with auto-detect support."""

import aiohttp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from client.client import bot_client
from utils.queue_manager import queue_manager
from utils.logger import get_logger

log = get_logger("Lyrics")
bot = bot_client.bot

LYRICS_APIS = [
    "https://lyrics.ovh/v1/{artist}/{title}",
    "https://api.lyrics.ovh/v1/{artist}/{title}",
]


async def fetch_lyrics(query: str) -> dict:
    """Try multiple APIs to find lyrics."""
    # Try splitting into artist - title
    parts = query.split(" - ", 1) if " - " in query else query.split(" by ", 1)
    if len(parts) == 2:
        artist, title = parts[0].strip(), parts[1].strip()
    else:
        artist, title = "", query.strip()

    # Method 1: lyrics.ovh
    if artist:
        for api in LYRICS_APIS:
            try:
                url = api.format(artist=artist, title=title)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            lyrics = data.get("lyrics")
                            if lyrics:
                                return {"title": title, "artist": artist, "lyrics": lyrics}
            except Exception:
                continue

    # Method 2: Search with full query as title
    for api in LYRICS_APIS:
        try:
            url = api.format(artist="", title=query)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        lyrics = data.get("lyrics")
                        if lyrics:
                            return {"title": query, "artist": "Unknown", "lyrics": lyrics}
        except Exception:
            continue

    return {}


@bot.on_message(filters.command("lyrics"))
async def lyrics_handler(_, message):
    # Auto-detect from current playing song
    if len(message.command) < 2:
        state = queue_manager.get(message.chat.id)
        if state.current:
            query = state.current.title
        else:
            return await message.reply_text("❗ `/lyrics <sᴏɴɢ ɴᴀᴍᴇ>` ᴏʀ ᴘʟᴀʏ ᴀ sᴏɴɢ ꜰɪʀsᴛ.")
    else:
        query = " ".join(message.command[1:])

    m = await message.reply_text(f"🔎 **sᴇᴀʀᴄʜɪɴɢ ʟʏʀɪᴄs ꜰᴏʀ** `{query}`…")

    result = await fetch_lyrics(query)

    if result and result.get("lyrics"):
        lyrics = result["lyrics"]
        title = result.get("title", query)
        artist = result.get("artist", "")

        # Truncate if too long
        if len(lyrics) > 4000:
            lyrics = lyrics[:4000] + "\n\n… _(ᴛʀᴜɴᴄᴀᴛᴇᴅ)_"

        header = f"📜 **{title}**"
        if artist and artist != "Unknown":
            header += f" ʙʏ `{artist}`"

        await m.edit(f"{header}\n\n{lyrics}")
    else:
        await m.edit(
            "❌ **ʟʏʀɪᴄs ɴᴏᴛ ꜰᴏᴜɴᴅ.**\nᴛʀʏ: `ᴀʀᴛɪsᴛ - sᴏɴɢ ɴᴀᴍᴇ`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 sᴇᴀʀᴄʜ ɢᴏᴏɢʟᴇ",
                    url=f"https://www.google.com/search?q={query}+lyrics")]
            ]),
        )
