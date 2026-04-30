"""Play engine — the heart of the bot. Expert-grade streaming.

Uses modern pytgcalls API: MediaStream, .play(), stream_ended decorator.
Supports: YouTube, JioSaavn, Spotify, SoundCloud, Radio, Audio files.
"""

import asyncio
import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, CallbackQuery
from pyrogram.errors import UserNotParticipant

from client.client import bot_client
from utils.yt_utils import YTSearch, Downloader
from utils.jiosaavn import JioSaavnAPI
from utils.thumbnails import download_thumb
from utils.queue_manager import queue_manager, Track
from utils.helpers import format_duration, detect_source, truncate
from utils.database import db
from utils.logger import get_logger
from plugins.assistant_handler import assistant_join
import config

log = get_logger("Play")
bot = bot_client.bot
call = bot_client.call

# ═══════════════════════════════════════════════════════════════
# STREAM HELPERS — modern pytgcalls MediaStream API
# ═══════════════════════════════════════════════════════════════

def _build_stream(file_path: str, is_video: bool = False):
    """Build a MediaStream object for pytgcalls.play()."""
    try:
        from pytgcalls.types import MediaStream
        return MediaStream(file_path)
    except ImportError:
        # Fallback for older pytgcalls
        try:
            from pytgcalls.types import AudioPiped, AudioVideoPiped
            return AudioVideoPiped(file_path) if is_video else AudioPiped(file_path)
        except ImportError:
            from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
            return AudioVideoPiped(file_path) if is_video else AudioPiped(file_path)


async def _join_and_stream(chat_id: int, file_path: str, is_video: bool = False):
    """Join VC and start streaming with full error recovery."""
    if not call:
        raise Exception("Assistant not configured")

    stream = _build_stream(file_path, is_video)

    # Try .play() first (modern API), fallback to join_group_call
    try:
        await call.play(chat_id, stream)
        return
    except AttributeError:
        pass  # .play() not available, try legacy
    except Exception as e:
        err = str(e).lower()
        if "already" in err:
            # Already in call — just change stream
            try:
                await call.change_stream(chat_id, stream)
                return
            except Exception:
                pass
        log.warning(f"play() failed: {e}, trying join_group_call")

    # Legacy: join_group_call
    try:
        await call.join_group_call(chat_id, stream)
    except Exception as e:
        err = str(e).lower()
        if "already" in err:
            await call.change_stream(chat_id, stream)
        else:
            raise


async def _leave_vc(chat_id: int):
    """Leave VC safely."""
    if not call:
        return
    try:
        await call.leave_group_call(chat_id)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# ACCESS CHECKS
# ═══════════════════════════════════════════════════════════════

async def check_access(user_id: int) -> bool:
    """Check force-join + block status."""
    if await db.is_blocked(user_id):
        return False
    if not config.MUST_JOIN:
        return True
    try:
        await bot.get_chat_member(config.MUST_JOIN, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True


# ═══════════════════════════════════════════════════════════════
# /play COMMAND — the main entry point
# ═══════════════════════════════════════════════════════════════

@bot.on_message(filters.command(["play", "vplay", "saavn", "splay", "cplay"]))
async def play_handler(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await check_access(user_id):
        try:
            link = await bot.export_chat_invite_link(config.MUST_JOIN)
        except Exception:
            link = f"https://t.me/{config.MUST_JOIN}"
        return await message.reply_text(
            "❌ **ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ!** ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ꜰɪʀsᴛ.",
            reply_markup=IKM([[IKB("📢 ᴊᴏɪɴ", url=link)]]),
        )

    cmd = message.command[0]
    is_video = cmd == "vplay"
    is_saavn = cmd in ("saavn", "splay")
    replied = message.reply_to_message

    # ── Handle audio file reply ──
    if replied and replied.audio:
        m = await message.reply_text("⏳ **ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰɪʟᴇ…**")
        try:
            fp = await replied.download(file_name=f"downloads/{replied.audio.file_id}.mp3")
            track = Track(
                id=replied.audio.file_id,
                title=replied.audio.title or "Audio File",
                duration=replied.audio.duration,
                uploader=replied.audio.performer or "Unknown",
                url="", file_path=fp,
                requested_by=user_id, source="file",
            )
            queue_manager.add(chat_id, track)
            await assistant_join(chat_id)
            state = queue_manager.get(chat_id)
            if not state.is_playing:
                await m.edit("🚀 **sᴛᴀʀᴛɪɴɢ…**")
                await _start_playback(chat_id)
            else:
                await m.edit(f"🎶 **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ #{len(state.queue)}**")
            return
        except Exception as e:
            return await m.edit(f"❌ `{e}`")

    # ── Get search query ──
    query = ""
    if replied and replied.text:
        query = replied.text.strip()
    elif len(message.command) > 1:
        query = " ".join(message.command[1:]).strip()

    if not query:
        return await message.reply_text(f"❗ `/{cmd} <sᴏɴɢ ɴᴀᴍᴇ ᴏʀ ᴜʀʟ>`")

    m = await message.reply_text("🔎 **sᴇᴀʀᴄʜɪɴɢ…**")

    # ── Auto-detect Spotify URLs ──
    source = detect_source(query)
    if source == "spotify_track":
        return await _handle_spotify_track(chat_id, user_id, query, m)
    if source == "spotify_playlist":
        return await _handle_spotify_playlist(chat_id, user_id, query, m)

    # ── Search the right platform ──
    if is_saavn:
        results = await JioSaavnAPI.search(query, limit=8)
    else:
        results = await YTSearch.search(query, limit=8)

    if not results:
        return await m.edit("❌ **ɴᴏ ʀᴇsᴜʟᴛs ꜰᴏᴜɴᴅ.**")

    # ── Build search result buttons ──
    buttons = []
    for i, r in enumerate(results[:5], 1):
        dur = format_duration(r.get("duration"))
        mode = "v" if is_video else "a"
        src = "j" if is_saavn else "y"
        icon = "🎥" if is_video else "🎵"
        buttons.append([IKB(
            f"{icon} {i}. {truncate(r['title'], 28)} ({dur})",
            callback_data=f"ply|{chat_id}|{r['id']}|{mode}|{src}",
        )])
    buttons.append([IKB("🗑 ᴄʟᴏsᴇ", callback_data="cncl")])

    label = "ᴊɪᴏsᴀᴀᴠɴ" if is_saavn else "ʏᴏᴜᴛᴜʙᴇ"
    await m.edit_text(f"🎵 **{label} ʀᴇsᴜʟᴛs:**", reply_markup=IKM(buttons))


# ═══════════════════════════════════════════════════════════════
# SEARCH RESULT CALLBACK — user picks a track
# ═══════════════════════════════════════════════════════════════

@bot.on_callback_query(filters.regex(r"^ply\|(-?\d+)\|(.+)\|(a|v)\|(y|j)$"))
async def play_chosen(_, query: CallbackQuery):
    _, cid, track_id, mode, src = query.data.split("|")
    chat_id = int(cid)
    user_id = query.from_user.id
    is_video = mode == "v"
    is_saavn = src == "j"

    await query.answer("⏳ ᴘʀᴏᴄᴇssɪɴɢ…")
    await query.edit_message_text("⏳ **ᴘʀᴏᴄᴇssɪɴɢ…**")

    try:
        if is_saavn:
            info = await JioSaavnAPI.get_info(track_id)
            if not info:
                return await query.edit_message_text("❌ **ꜰᴀɪʟᴇᴅ.**")
            audio_path = info["url"]
            thumb_path = info.get("image", "")
        else:
            url = f"https://www.youtube.com/watch?v={track_id}"
            info = await YTSearch.get_info(url)
            if not info:
                return await query.edit_message_text("❌ **ꜰᴀɪʟᴇᴅ.**")
            dl_task = asyncio.create_task(Downloader.download(url, video=is_video))
            th_task = asyncio.create_task(download_thumb(info.get("thumbnail", ""), track_id))
            audio_path, thumb_path = await asyncio.gather(dl_task, th_task)

        if not audio_path:
            return await query.edit_message_text("❌ **ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ.**")

        track = Track(
            id=track_id, title=info["title"],
            duration=info.get("duration"), uploader=info.get("uploader"),
            url=info.get("url", ""), file_path=audio_path,
            thumb_path=thumb_path or None, requested_by=user_id,
            is_video=is_video,
            source="jiosaavn" if is_saavn else "youtube",
        )

        queue_manager.add(chat_id, track)
        await assistant_join(chat_id)
        await db.increment_plays()
        await db.add_to_history(user_id, chat_id, {"id": track_id, "title": info["title"]})

        state = queue_manager.get(chat_id)
        if state.is_playing:
            pos = len(state.queue)
            await query.edit_message_text(
                f"🎶 **ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ #{pos}**\n\n"
                f"📌 {truncate(track.title, 40)}\n"
                f"⏱ `{format_duration(track.duration)}`\n"
                f"👤 {query.from_user.mention}",
                disable_web_page_preview=True,
            )
        else:
            await query.edit_message_text("🚀 **sᴛᴀʀᴛɪɴɢ ᴘʟᴀʏʙᴀᴄᴋ…**")
            await _start_playback(chat_id)

    except Exception as e:
        log.error(f"Play error: {e}")
        await query.edit_message_text(f"❌ `{e}`")


@bot.on_callback_query(filters.regex("^cncl$"))
async def cancel_search(_, q: CallbackQuery):
    await q.answer("ᴄᴀɴᴄᴇʟʟᴇᴅ.")
    await q.message.delete()


# ═══════════════════════════════════════════════════════════════
# CORE PLAYBACK ENGINE
# ═══════════════════════════════════════════════════════════════

async def _start_playback(chat_id: int):
    """Pop next track from queue and stream it."""
    from plugins.controls import update_now_playing

    state = queue_manager.get(chat_id)
    track = queue_manager.pop(chat_id)

    if not track:
        state.is_playing = False
        state.is_paused = False
        state.current = None
        await _leave_vc(chat_id)
        return

    state.is_playing = True
    state.is_paused = False
    state.current = track

    if not call:
        return await bot.send_message(chat_id, "❌ **ᴀssɪsᴛᴀɴᴛ ɴᴏᴛ ᴄᴏɴꜰɪɢᴜʀᴇᴅ.**")

    # Ensure assistant is in the chat
    await assistant_join(chat_id)

    # Try streaming with retry
    for attempt in range(3):
        try:
            await _join_and_stream(chat_id, track.file_path, track.is_video)
            log.info(f"Streaming in {chat_id}: {track.title}")
            break
        except Exception as e:
            log.error(f"Stream attempt {attempt+1}/3 for {chat_id}: {e}")
            if attempt < 2:
                await asyncio.sleep(1)
                await assistant_join(chat_id)
            else:
                await bot.send_message(chat_id, f"❌ **sᴛʀᴇᴀᴍ ꜰᴀɪʟᴇᴅ:** `{e}`")
                state.is_playing = False
                return

    await update_now_playing(chat_id, track)


# ═══════════════════════════════════════════════════════════════
# SPOTIFY HELPERS
# ═══════════════════════════════════════════════════════════════

async def _handle_spotify_track(chat_id, user_id, url, status_msg):
    try:
        from utils.spotify import SpotifyAPI
        from utils.helpers import SPOTIFY_TRACK_REGEX
        match = SPOTIFY_TRACK_REGEX.search(url)
        if not match:
            return await status_msg.edit("❌ **ɪɴᴠᴀʟɪᴅ sᴘᴏᴛɪꜰʏ ᴜʀʟ.**")
        info = await SpotifyAPI.get_track(match.group(1))
        if not info:
            return await status_msg.edit("❌ **sᴘᴏᴛɪꜰʏ ᴛʀᴀᴄᴋ ɴᴏᴛ ꜰᴏᴜɴᴅ.**")

        await status_msg.edit(f"🟢 **sᴘᴏᴛɪꜰʏ →** `{truncate(info['title'], 30)}`")
        yt = await YTSearch.search(info["search_query"], limit=1)
        if not yt:
            return await status_msg.edit("❌ **ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏɴ ʏᴛ.**")
        r = yt[0]
        yurl = f"https://www.youtube.com/watch?v={r['id']}"
        path = await Downloader.download(yurl)
        if not path:
            return await status_msg.edit("❌ **ᴅᴏᴡɴʟᴏᴀᴅ ꜰᴀɪʟᴇᴅ.**")
        track = Track(id=r["id"], title=info["title"], duration=info.get("duration"),
                       uploader=info.get("artist", ""), url=yurl, file_path=path,
                       requested_by=user_id, source="spotify")
        queue_manager.add(chat_id, track)
        await assistant_join(chat_id)
        await db.increment_plays()
        state = queue_manager.get(chat_id)
        if not state.is_playing:
            await status_msg.edit("🚀 **sᴛᴀʀᴛɪɴɢ…**")
            await _start_playback(chat_id)
        else:
            await status_msg.edit(f"🎶 **ᴀᴅᴅᴇᴅ #{len(state.queue)}** — {truncate(info['title'], 35)}")
    except Exception as e:
        await status_msg.edit(f"❌ `{e}`")


async def _handle_spotify_playlist(chat_id, user_id, url, status_msg):
    try:
        from utils.spotify import SpotifyAPI
        from utils.helpers import SPOTIFY_PLAYLIST_REGEX
        match = SPOTIFY_PLAYLIST_REGEX.search(url)
        if not match:
            return await status_msg.edit("❌ **ɪɴᴠᴀʟɪᴅ ᴜʀʟ.**")
        tracks = await SpotifyAPI.get_playlist(match.group(1))
        if not tracks:
            return await status_msg.edit("❌ **ᴇᴍᴘᴛʏ ᴘʟᴀʏʟɪsᴛ.**")
        await status_msg.edit(f"📥 **ʟᴏᴀᴅɪɴɢ {len(tracks)} sᴘᴏᴛɪꜰʏ ᴛʀᴀᴄᴋs…**")
        added = 0
        for t in tracks[:config.MAX_PLAYLIST_SIZE]:
            try:
                yt = await YTSearch.search(t["search_query"], limit=1)
                if yt:
                    r = yt[0]
                    yurl = f"https://www.youtube.com/watch?v={r['id']}"
                    path = await Downloader.download(yurl)
                    if path:
                        trk = Track(id=r["id"], title=t["title"], duration=t.get("duration"),
                                     uploader=t.get("artist", ""), url=yurl, file_path=path,
                                     requested_by=user_id, source="spotify")
                        if queue_manager.add(chat_id, trk):
                            added += 1
            except Exception:
                continue
        await assistant_join(chat_id)
        state = queue_manager.get(chat_id)
        if not state.is_playing and added > 0:
            await status_msg.edit(f"✅ **ʟᴏᴀᴅᴇᴅ {added} ᴛʀᴀᴄᴋs! sᴛᴀʀᴛɪɴɢ…**")
            await _start_playback(chat_id)
        else:
            await status_msg.edit(f"✅ **ᴀᴅᴅᴇᴅ {added} ᴛʀᴀᴄᴋs.**")
    except Exception as e:
        await status_msg.edit(f"❌ `{e}`")


# ═══════════════════════════════════════════════════════════════
# STREAM END HANDLER — auto-play next track
# ═══════════════════════════════════════════════════════════════

def _register_stream_handler():
    """Register stream-end callback using whatever API version is available."""
    _call = bot_client.call
    if not _call:
        return

    async def _on_stream_end(client, update):
        chat_id = update.chat_id
        log.info(f"Stream ended in {chat_id}")
        Downloader.clear_old()
        try:
            await _start_playback(chat_id)
        except Exception as e:
            log.error(f"Stream-end handler error: {e}")

    # Try modern API first, then fallbacks
    try:
        _call.on_stream_end()(_on_stream_end)
        log.info("Registered stream handler: on_stream_end()")
        return
    except (AttributeError, TypeError):
        pass

    try:
        from pytgcalls import filters as ptgfilters
        _call.on_update(ptgfilters.stream_end)(_on_stream_end)
        log.info("Registered stream handler: on_update(stream_end)")
        return
    except (ImportError, AttributeError, TypeError):
        pass

    try:
        _call.on_closed_voice_chat()(_on_stream_end)
        log.info("Registered stream handler: on_closed_voice_chat()")
        return
    except (AttributeError, TypeError):
        pass

    log.warning("Could not register stream-end handler — auto-skip disabled")
