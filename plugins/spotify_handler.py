"""Spotify command handler — play from Spotify URLs and search."""

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from utils.helpers import truncate, format_duration, SPOTIFY_TRACK_REGEX, SPOTIFY_PLAYLIST_REGEX, SPOTIFY_ALBUM_REGEX
from utils.logger import get_logger

log = get_logger("Spotify")
bot = bot_client.bot


@bot.on_message(filters.command("spotify"))
async def spotify_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "🎵 **sᴘᴏᴛɪꜰʏ ᴄᴏᴍᴍᴀɴᴅs:**\n\n"
            "├ `/spotify <song name>` — sᴇᴀʀᴄʜ sᴘᴏᴛɪꜰʏ\n"
            "├ `/play <spotify_track_url>` — ᴘʟᴀʏ ᴛʀᴀᴄᴋ\n"
            "└ `/play <spotify_playlist_url>` — ʟᴏᴀᴅ ᴘʟᴀʏʟɪsᴛ"
        )

    try:
        from utils.spotify import SpotifyAPI
        if not SpotifyAPI.is_available():
            return await message.reply_text(
                "❌ **sᴘᴏᴛɪꜰʏ ɴᴏᴛ ᴄᴏɴꜰɪɢᴜʀᴇᴅ.**\n\n"
                "sᴇᴛ `SPOTIFY_CLIENT_ID` ᴀɴᴅ `SPOTIFY_CLIENT_SECRET` ɪɴ ᴇɴᴠ."
            )
    except ImportError:
        return await message.reply_text("❌ **sᴘᴏᴛɪꜰʏ ᴍᴏᴅᴜʟᴇ ɴᴏᴛ ɪɴsᴛᴀʟʟᴇᴅ.**")

    query = " ".join(message.command[1:])
    m = await message.reply_text("🔎 **sᴇᴀʀᴄʜɪɴɢ sᴘᴏᴛɪꜰʏ…**")

    results = await SpotifyAPI.search(query, limit=5)
    if not results:
        return await m.edit("❌ **ɴᴏ ʀᴇsᴜʟᴛs ꜰᴏᴜɴᴅ.**")

    buttons = []
    for i, r in enumerate(results[:5], 1):
        dur = format_duration(r.get("duration"))
        title = truncate(r.get("title", "Unknown"), 25)
        artist = truncate(r.get("artist", ""), 15)
        # Use search_query to play via YouTube
        callback = f"spfy|{i - 1}"
        buttons.append([InlineKeyboardButton(
            f"🎵 {i}. {title} - {artist} ({dur})",
            callback_data=callback,
        )])
    buttons.append([InlineKeyboardButton("🗑 ᴄʟᴏsᴇ", callback_data="cncl")])

    # Store results in a temporary way via message
    _spotify_results[message.chat.id] = results

    await m.edit_text(
        "🎵 **sᴘᴏᴛɪꜰʏ sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs:**",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# Temporary storage for search results
_spotify_results = {}


@bot.on_callback_query(filters.regex(r"^spfy\|(\d+)$"))
async def spotify_play_cb(_, query: CallbackQuery):
    idx = int(query.data.split("|")[1])
    chat_id = query.message.chat.id

    results = _spotify_results.get(chat_id, [])
    if idx >= len(results):
        return await query.answer("❌ ᴇxᴘɪʀᴇᴅ. sᴇᴀʀᴄʜ ᴀɢᴀɪɴ.", show_alert=True)

    track = results[idx]
    search_query = track.get("search_query", track.get("title", ""))

    await query.answer("⏳ ᴘʀᴏᴄᴇssɪɴɢ…")
    await query.edit_message_text(f"⏳ **ꜰɪɴᴅɪɴɢ** `{truncate(track['title'], 30)}`**…**")

    # Search YouTube for this Spotify track
    from utils.yt_utils import YTSearch, Downloader
    from utils.queue_manager import queue_manager, Track as QTrack
    from plugins.assistant_handler import assistant_join
    from plugins.play import _start_playback
    from utils.database import db

    yt_results = await YTSearch.search(search_query, limit=1)
    if not yt_results:
        return await query.edit_message_text("❌ **ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏɴ ʏᴏᴜᴛᴜʙᴇ.**")

    r = yt_results[0]
    url = f"https://www.youtube.com/watch?v={r['id']}"
    audio_path = await Downloader.download(url)
    if not audio_path:
        return await query.edit_message_text("❌ **ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ.**")

    q_track = QTrack(
        id=r["id"], title=track["title"],
        duration=track.get("duration"), uploader=track.get("artist", "Unknown"),
        url=url, file_path=audio_path,
        requested_by=query.from_user.id, source="spotify",
    )

    queue_manager.add(chat_id, q_track)
    await assistant_join(chat_id)
    await db.increment_plays()

    state = queue_manager.get(chat_id)
    if state.is_playing:
        await query.edit_message_text(
            f"🎶 **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ #{len(state.queue)}**\n\n"
            f"📌 {truncate(track['title'], 40)}\n"
            f"🎤 {track.get('artist', 'Unknown')}\n"
            f"📀 sᴏᴜʀᴄᴇ: sᴘᴏᴛɪꜰʏ → ʏᴏᴜᴛᴜʙᴇ"
        )
    else:
        await query.edit_message_text("🚀 **sᴛᴀʀᴛɪɴɢ ᴘʟᴀʏʙᴀᴄᴋ…**")
        await _start_playback(chat_id)

    # Clean up
    if chat_id in _spotify_results:
        del _spotify_results[chat_id]
