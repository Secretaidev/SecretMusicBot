import aiohttp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from client.client import bot_client

bot = bot_client.bot

@bot.on_message(filters.command("lyrics"))
async def lyrics_handler(_, message):
    if len(message.command) < 2:
        return await message.reply_text("❗ **ᴜsᴀɢᴇ:** `/lyrics <sᴏɴɢ ɴᴀᴍᴇ>`")

    query = " ".join(message.command[1:])
    m = await message.reply_text(f"🔎 **sᴇᴀʀᴄʜɪɴɢ ʟʏʀɪᴄs ꜰᴏʀ** `{query}`…")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://some-random-api.ml/lyrics?title={query}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics")
                    title = data.get("title")
                    author = data.get("author")
                    
                    if lyrics:
                        if len(lyrics) > 4000:
                            lyrics = lyrics[:4000] + "..."
                        
                        text = f"📜 **ʟʏʀɪᴄs ꜰᴏʀ {title}** ʙʏ `{author}`\n\n{lyrics}"
                        return await m.edit(text)
    except Exception:
        pass

    await m.edit(
        "❌ **ʟʏʀɪᴄs ɴᴏᴛ ꜰᴏᴜɴᴅ.**\nᴛʀʏ ʙᴇɪɴɢ ᴍᴏʀᴇ sᴘᴇᴄɪꜰɪᴄ ᴡɪᴛʜ ᴛʜᴇ sᴏɴɢ ɴᴀᴍᴇ.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔍 sᴇᴀʀᴄʜ ᴍᴀɴᴜᴀʟʟʏ", url=f"https://www.google.com/search?q={query}+lyrics")]]
        )
    )
