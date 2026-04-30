"""Download songs/videos as files and send to chat."""

import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from utils.yt_utils import YTSearch, Downloader
from utils.thumbnails import download_thumb
from utils.helpers import format_duration, truncate
from utils.logger import get_logger

log = get_logger("Download")
bot = bot_client.bot


@bot.on_message(filters.command("song"))
async def song_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text("❗ `/song <sᴏɴɢ ɴᴀᴍᴇ>`")

    query = " ".join(message.command[1:])
    m = await message.reply_text(f"🔎 **sᴇᴀʀᴄʜɪɴɢ** `{truncate(query, 30)}`…")

    results = await YTSearch.search(query, limit=5)
    if not results:
        return await m.edit("❌ **ɴᴏ ʀᴇsᴜʟᴛs.**")

    buttons = []
    for i, r in enumerate(results[:5], 1):
        dur = format_duration(r.get("duration"))
        callback = f"dl_s|{r['id']}"
        buttons.append([InlineKeyboardButton(
            f"🎵 {i}. {truncate(r['title'], 30)} ({dur})",
            callback_data=callback,
        )])
    buttons.append([InlineKeyboardButton("🗑 ᴄʟᴏsᴇ", callback_data="cncl")])

    await m.edit_text("🎵 **sᴇʟᴇᴄᴛ ᴀ sᴏɴɢ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ:**", reply_markup=InlineKeyboardMarkup(buttons))


@bot.on_message(filters.command("video"))
async def video_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text("❗ `/video <ᴠɪᴅᴇᴏ ɴᴀᴍᴇ>`")

    query = " ".join(message.command[1:])
    m = await message.reply_text(f"🔎 **sᴇᴀʀᴄʜɪɴɢ** `{truncate(query, 30)}`…")

    results = await YTSearch.search(query, limit=5)
    if not results:
        return await m.edit("❌ **ɴᴏ ʀᴇsᴜʟᴛs.**")

    buttons = []
    for i, r in enumerate(results[:5], 1):
        dur = format_duration(r.get("duration"))
        callback = f"dl_v|{r['id']}"
        buttons.append([InlineKeyboardButton(
            f"🎥 {i}. {truncate(r['title'], 30)} ({dur})",
            callback_data=callback,
        )])
    buttons.append([InlineKeyboardButton("🗑 ᴄʟᴏsᴇ", callback_data="cncl")])

    await m.edit_text("🎥 **sᴇʟᴇᴄᴛ ᴀ ᴠɪᴅᴇᴏ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ:**", reply_markup=InlineKeyboardMarkup(buttons))


@bot.on_callback_query(filters.regex(r"^dl_s\|(.+)$"))
async def dl_song_cb(_, query: CallbackQuery):
    track_id = query.data.split("|")[1]
    await query.answer("⏳ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ…")
    await query.edit_message_text("⏳ **ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ sᴏɴɢ… ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.**")

    url = f"https://www.youtube.com/watch?v={track_id}"
    result = await Downloader.download_song_file(url, quality="320")

    if not result:
        return await query.edit_message_text("❌ **ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ.**")

    try:
        thumb = await download_thumb(result.get("thumbnail", ""), track_id)
        thumb_file = thumb if thumb and os.path.exists(thumb) else None

        await bot.send_audio(
            query.message.chat.id,
            audio=result["path"],
            title=result.get("title", "Unknown"),
            performer=result.get("artist", "Unknown"),
            duration=result.get("duration", 0),
            thumb=thumb_file,
            caption=(
                f"🎵 **{truncate(result.get('title', 'Unknown'), 40)}**\n"
                f"🎤 {result.get('artist', 'Unknown')}\n"
                f"⏱ `{format_duration(result.get('duration'))}`\n\n"
                f"📥 ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ ᴠɪᴀ **sᴇᴄʀᴇᴛ ᴍᴜsɪᴄ ʙᴏᴛ**"
            ),
        )
        await query.message.delete()
    except Exception as e:
        log.error(f"Song send error: {e}")
        await query.edit_message_text(f"❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ:** `{e}`")
    finally:
        # Clean up
        try:
            if result.get("path") and os.path.exists(result["path"]):
                os.remove(result["path"])
        except Exception:
            pass


@bot.on_callback_query(filters.regex(r"^dl_v\|(.+)$"))
async def dl_video_cb(_, query: CallbackQuery):
    track_id = query.data.split("|")[1]
    await query.answer("⏳ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ…")
    await query.edit_message_text("⏳ **ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴠɪᴅᴇᴏ… ᴛʜɪs ᴍᴀʏ ᴛᴀᴋᴇ ᴀ ᴍᴏᴍᴇɴᴛ.**")

    url = f"https://www.youtube.com/watch?v={track_id}"
    info = await YTSearch.get_info(url)
    if not info:
        return await query.edit_message_text("❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ ɢᴇᴛ ᴠɪᴅᴇᴏ ɪɴꜰᴏ.**")

    path = await Downloader.download(url, video=True)
    if not path:
        return await query.edit_message_text("❌ **ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ.**")

    try:
        thumb = await download_thumb(info.get("thumbnail", ""), track_id)
        thumb_file = thumb if thumb and os.path.exists(thumb) else None

        await bot.send_video(
            query.message.chat.id,
            video=path,
            duration=info.get("duration", 0),
            thumb=thumb_file,
            caption=(
                f"🎥 **{truncate(info.get('title', 'Unknown'), 40)}**\n"
                f"⏱ `{format_duration(info.get('duration'))}`\n\n"
                f"📥 ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ ᴠɪᴀ **sᴇᴄʀᴇᴛ ᴍᴜsɪᴄ ʙᴏᴛ**"
            ),
            supports_streaming=True,
        )
        await query.message.delete()
    except Exception as e:
        log.error(f"Video send error: {e}")
        await query.edit_message_text(f"❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ:** `{e}`")
    finally:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
