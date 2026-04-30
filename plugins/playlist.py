"""Playlist management — create, view, add, play, delete personal playlists.
Also handles favourites and play history.
"""

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from utils.database import db
from utils.queue_manager import queue_manager, Track
from utils.helpers import format_duration, truncate

bot = bot_client.bot


@bot.on_message(filters.command("playlist"))
async def playlist_cmd(_, message):
    user_id = message.from_user.id
    args = message.command[1:]

    if not args:
        playlists = await db.get_playlists(user_id)
        if not playlists:
            return await message.reply_text(
                "📭 **ɴᴏ ᴘʟᴀʏʟɪsᴛs ʏᴇᴛ.**\n\n"
                "`/playlist create <name>` — ᴄʀᴇᴀᴛᴇ ᴏɴᴇ"
            )
        text = "📋 **ʏᴏᴜʀ ᴘʟᴀʏʟɪsᴛs:**\n\n"
        for i, pl in enumerate(playlists, 1):
            count = len(pl.get("tracks", []))
            text += f"`{i}.` **{pl['name']}** — `{count}` ᴛʀᴀᴄᴋs\n"
        text += "\n`/playlist play <name>` — ᴘʟᴀʏ ᴀ ᴘʟᴀʏʟɪsᴛ"
        return await message.reply_text(text)

    action = args[0].lower()

    if action == "create" and len(args) > 1:
        name = " ".join(args[1:])
        success = await db.create_playlist(user_id, name)
        if success:
            await message.reply_text(f"✅ **ᴘʟᴀʏʟɪsᴛ `{name}` ᴄʀᴇᴀᴛᴇᴅ!**")
        else:
            await message.reply_text(f"❌ **ᴘʟᴀʏʟɪsᴛ `{name}` ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs.**")

    elif action == "delete" and len(args) > 1:
        name = " ".join(args[1:])
        success = await db.delete_playlist(user_id, name)
        if success:
            await message.reply_text(f"✅ **ᴅᴇʟᴇᴛᴇᴅ ᴘʟᴀʏʟɪsᴛ `{name}`.**")
        else:
            await message.reply_text(f"❌ **ᴘʟᴀʏʟɪsᴛ ɴᴏᴛ ꜰᴏᴜɴᴅ.**")

    elif action == "add" and len(args) > 1:
        name = " ".join(args[1:])
        state = queue_manager.get(message.chat.id)
        if not state.current:
            return await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ᴘʟᴀʏɪɴɢ ᴛᴏ ᴀᴅᴅ.**")
        track = state.current
        success = await db.add_to_playlist(user_id, name, {
            "id": track.id, "title": track.title, "url": track.url,
            "duration": track.duration, "uploader": track.uploader,
        })
        if success:
            await message.reply_text(f"✅ **ᴀᴅᴅᴇᴅ ᴛᴏ `{name}`!**")
        else:
            await message.reply_text(f"❌ **ᴘʟᴀʏʟɪsᴛ `{name}` ɴᴏᴛ ꜰᴏᴜɴᴅ.**")

    elif action == "play" and len(args) > 1:
        name = " ".join(args[1:])
        playlist = await db.get_playlist(user_id, name)
        if not playlist or not playlist.get("tracks"):
            return await message.reply_text(f"❌ **ᴘʟᴀʏʟɪsᴛ `{name}` ɪs ᴇᴍᴘᴛʏ/ɴᴏᴛ ꜰᴏᴜɴᴅ.**")

        m = await message.reply_text(f"📥 **ʟᴏᴀᴅɪɴɢ ᴘʟᴀʏʟɪsᴛ `{name}`…**")
        chat_id = message.chat.id
        added = 0
        for t in playlist["tracks"]:
            try:
                from utils.yt_utils import YTSearch, Downloader
                results = await YTSearch.search(t["title"], limit=1)
                if results:
                    r = results[0]
                    url = f"https://www.youtube.com/watch?v={r['id']}"
                    path = await Downloader.download(url)
                    if path:
                        track = Track(
                            id=r["id"], title=t["title"], duration=t.get("duration"),
                            uploader=t.get("uploader", "Unknown"), url=url,
                            file_path=path, requested_by=user_id,
                        )
                        if queue_manager.add(chat_id, track):
                            added += 1
            except Exception:
                continue

        if added > 0:
            state = queue_manager.get(chat_id)
            if not state.is_playing:
                from plugins.play import _start_playback
                from plugins.assistant_handler import assistant_join
                await assistant_join(chat_id)
                await m.edit(f"✅ **ʟᴏᴀᴅᴇᴅ {added} ᴛʀᴀᴄᴋs! sᴛᴀʀᴛɪɴɢ…**")
                await _start_playback(chat_id)
            else:
                await m.edit(f"✅ **ᴀᴅᴅᴇᴅ {added} ᴛʀᴀᴄᴋs ᴛᴏ ǫᴜᴇᴜᴇ.**")
        else:
            await m.edit("❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ ʟᴏᴀᴅ ᴛʀᴀᴄᴋs.**")
    else:
        await message.reply_text(
            "📋 **ᴘʟᴀʏʟɪsᴛ ᴄᴏᴍᴍᴀɴᴅs:**\n\n"
            "├ `/playlist` — ᴠɪᴇᴡ ᴀʟʟ\n"
            "├ `/playlist create <name>`\n"
            "├ `/playlist add <name>`\n"
            "├ `/playlist play <name>`\n"
            "└ `/playlist delete <name>`"
        )


@bot.on_message(filters.command("like"))
async def like_cmd(_, message):
    user_id = message.from_user.id
    state = queue_manager.get(message.chat.id)
    if not state.current:
        return await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ᴘʟᴀʏɪɴɢ ᴛᴏ ʟɪᴋᴇ.**")
    track = state.current
    await db.add_favourite(user_id, {
        "id": track.id, "title": track.title, "url": track.url, "duration": track.duration,
    })
    await message.reply_text(f"❤️ **ʟɪᴋᴇᴅ:** {truncate(track.title, 40)}")


@bot.on_message(filters.command("favourite"))
async def favourite_cmd(_, message):
    favs = await db.get_favourites(message.from_user.id)
    if not favs:
        return await message.reply_text("📭 **ɴᴏ ꜰᴀᴠᴏᴜʀɪᴛᴇs ʏᴇᴛ.** ᴜsᴇ /like!")
    text = "❤️ **ʏᴏᴜʀ ꜰᴀᴠᴏᴜʀɪᴛᴇs:**\n\n"
    for i, t in enumerate(favs[:20], 1):
        dur = format_duration(t.get("duration"))
        text += f"`{i}.` {truncate(t['title'], 35)} │ `{dur}`\n"
    await message.reply_text(text, disable_web_page_preview=True)


@bot.on_message(filters.command("history"))
async def history_cmd(_, message):
    hist = await db.get_history(message.from_user.id, limit=20)
    if not hist:
        return await message.reply_text("📭 **ɴᴏ ʜɪsᴛᴏʀʏ ʏᴇᴛ.**")
    text = "📜 **ᴘʟᴀʏ ʜɪsᴛᴏʀʏ:**\n\n"
    for i, t in enumerate(hist[:20], 1):
        text += f"`{i}.` {truncate(t.get('title', 'Unknown'), 35)}\n"
    await message.reply_text(text, disable_web_page_preview=True)
