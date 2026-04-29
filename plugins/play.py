import asyncio
import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls.types import AudioPiped, VideoPiped
from pytgcalls.exceptions import AlreadyJoinedError

from client.client import bot_client
from utils.yt_utils import YTSearch, Downloader
from utils.jiosaavn import JioSaavnAPI
from utils.thumbnails import download_thumb
from utils.queue_manager import queue_manager, Track
from plugins.controls import update_now_playing
from plugins.assistant_handler import assistant_join
import config

bot = bot_client.bot
user = bot_client.user
call = bot_client.call

_vc_locks = {}

@bot.on_message(filters.command(["play", "vplay", "saavn"]))
async def play_handler(_, message):
    chat_id = message.chat.id
    cmd = message.command[0]
    is_video = cmd == "vplay"
    is_saavn = cmd == "saavn"
    replied = message.reply_to_message

    query = ""
    if replied and replied.text:
        query = replied.text.strip()
    elif len(message.command) > 1:
        query = " ".join(message.command[1:]).strip()

    if not query:
        return await message.reply_text(
            f"❗ **ᴜsᴀɢᴇ:** `/{cmd} <sᴏɴɢ ɴᴀᴍᴇ>` ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴛᴇxᴛ ᴍᴇssᴀɢᴇ."
        )

    m = await message.reply_text("🔎 **sᴇᴀʀᴄʜɪɴɢ…**")
    
    if is_saavn:
        results = await JioSaavnAPI.search(query)
    else:
        results = await YTSearch.search(query, limit=10)
    
    if not results:
        return await m.edit("❌ **ɴᴏ ʀᴇsᴜʟᴛs ꜰᴏᴜɴᴅ.**")

    buttons = []
    for i, r in enumerate(results[:5], 1):
        dur = _fmt_duration(r.get("duration"))
        mode = "v" if is_video else "a"
        source = "j" if is_saavn or r.get("source") == "jiosaavn" else "y"
        callback = f"ply|{chat_id}|{r['id']}|{mode}|{source}"
        buttons.append(
            [InlineKeyboardButton(f"{i}. {r['title'][:35]} | {dur}", callback_data=callback)]
        )
    buttons.append([InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="cncl")])
    
    await m.edit_text(
        f"🎵 **{'ᴊɪᴏsᴀᴀᴠɴ' if is_saavn else 'ʏᴏᴜᴛᴜʙᴇ'} sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs:**", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_callback_query(filters.regex(r"^ply\|(-?\d+)\|(.+)\|(a|v)\|(y|j)$"))
async def play_chosen(_, query: CallbackQuery):
    _, chat_id_str, track_id, mode, source = query.data.split("|")
    chat_id = int(chat_id_str)
    user_id = query.from_user.id
    is_video = mode == "v"
    is_saavn = source == "j"

    if query.message.chat.type != "private" and query.message.chat.id != chat_id:
        return await query.answer("ɴᴏᴛ ʏᴏᴜʀ ᴄʜᴀᴛ.", show_alert=True)

    await query.answer("ᴀᴅᴅɪɴɢ ᴛᴏ ǫᴜᴇᴜᴇ…")
    await query.edit_message_text("⏳ **ᴘʀᴏᴄᴇssɪɴɢ ᴛʀᴀᴄᴋ… ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.**")

    if is_saavn:
        info = await JioSaavnAPI.get_info(track_id)
        if not info:
            return await query.edit_message_text("❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ ꜰᴇᴛᴄʜ ᴊɪᴏsᴀᴀᴠɴ ɪɴꜰᴏ.**")
        audio_path = info["url"] # Direct link
        thumb_path = info["image"]
    else:
        url = f"https://www.youtube.com/watch?v={track_id}"
        info = await YTSearch.get_info(url)
        if not info:
            return await query.edit_message_text("❌ **ꜰᴀɪʟᴇᴅ ᴛᴏ ꜰᴇᴛᴄʜ ʏᴏᴜᴛᴜʙᴇ ɪɴꜰᴏ.**")
        
        audio_task = asyncio.create_task(Downloader.download(url))
        thumb_task = asyncio.create_task(download_thumb(info.get("thumbnail", ""), track_id))
        audio_path, thumb_path = await asyncio.gather(audio_task, thumb_task)

    if not audio_path:
        return await query.edit_message_text("❌ **ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ.**")

    track = Track(
        id=track_id,
        title=info["title"],
        duration=info.get("duration"),
        uploader=info.get("uploader"),
        url=info.get("url") if not is_saavn else f"https://www.jiosaavn.com/song/{track_id}",
        file_path=audio_path,
        thumb_path=thumb_path if thumb_path and (os.path.exists(thumb_path) if not is_saavn else True) else None,
        requested_by=user_id,
        is_video=is_video
    )

    added = queue_manager.add(chat_id, track)
    if not added:
        return await query.edit_message_text("❌ **ǫᴜᴇᴜᴇ ɪs ꜰᴜʟʟ.**")

    # Ensure assistant is in chat
    await assistant_join(chat_id)

    state = queue_manager.get(chat_id)
    pos = len(state.queue)

    if state.is_playing:
        text = (
            f"🎶 **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ ᴀᴛ #{pos}**\n\n"
            f"**📌 ᴛɪᴛʟᴇ:** [{track.title}]({track.url})\n"
            f"**⏱ ᴅᴜʀᴀᴛɪᴏɴ:** `{_fmt_duration(track.duration)}`\n"
            f"**👤 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:** {query.from_user.mention}"
        )
        await query.edit_message_text(text, disable_web_page_preview=True)
    else:
        await query.edit_message_text("🚀 **sᴛᴀʀᴛɪɴɢ ᴘʟᴀʏʙᴀᴄᴋ…**")
        await _start_playback(chat_id)

    # Log to channel
    if config.LOG_CHANNEL != 0:
        try:
            await bot.send_message(
                config.LOG_CHANNEL,
                f"🎵 **ᴛʀᴀᴄᴋ ʀᴇǫᴜᴇsᴛᴇᴅ**\n\n"
                f"**ᴛɪᴛʟᴇ:** {track.title}\n"
                f"**ᴄʜᴀᴛ:** {query.message.chat.title} (`{chat_id}`)\n"
                f"**ᴜsᴇʀ:** {query.from_user.mention} (`{user_id}`)\n"
                f"**sᴏᴜʀᴄᴇ:** {'ᴊɪᴏsᴀᴀᴠɴ' if is_saavn else 'ʏᴏᴜᴛᴜʙᴇ'}"
            )
        except Exception:
            pass

@bot.on_callback_query(filters.regex("^cncl$"))
async def cancel_search(_, query: CallbackQuery):
    await query.answer("ᴄᴀɴᴄᴇʟʟᴇᴅ.")
    await query.message.delete()

async def _start_playback(chat_id: int):
    state = queue_manager.get(chat_id)
    track = queue_manager.pop(chat_id)
    
    if not track:
        state.is_playing = False
        try:
            await call.leave_call(chat_id)
        except Exception:
            pass
        return

    state.is_playing = True
    state.current = track

    if user is None:
        return await bot.send_message(chat_id, "❌ ᴀssɪsᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ᴄᴏɴꜰɪɢᴜʀᴇᴅ.")

    try:
        stream = VideoPiped(track.file_path) if track.is_video else AudioPiped(track.file_path)
        await call.join_call(chat_id, stream)
    except AlreadyJoinedError:
        stream = VideoPiped(track.file_path) if track.is_video else AudioPiped(track.file_path)
        await call.change_stream(chat_id, stream)
    except Exception as e:
        print(f"[PyTgCalls Error] {e}")
        # Try joining again after ensuring assistant is in chat
        await assistant_join(chat_id)
        try:
            stream = VideoPiped(track.file_path) if track.is_video else AudioPiped(track.file_path)
            await call.join_call(chat_id, stream)
        except Exception as e2:
            await bot.send_message(chat_id, f"❌ **ᴇʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ᴘʟᴀʏʙᴀᴄᴋ:** `{e2}`")
            return

    await update_now_playing(chat_id, track)

from pytgcalls.types import Update

@call.on_stream_end()
async def stream_end_handler(client, update: Update):
    chat_id = update.chat_id
    try:
        from utils.yt_utils import Downloader
        Downloader.clear_old()
        await _start_playback(chat_id)
    except Exception as e:
        print(f"[Auto-Play Error] {e}")

def _fmt_duration(seconds: int | None) -> str:
    if not seconds:
        return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
