"""Player controls — the ultimate button-driven music panel."""

import os, time
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from utils.queue_manager import queue_manager
from utils.helpers import format_duration, progress_bar, get_readable_time
from utils.thumbnails import generate_now_playing_card
from utils.database import db
from utils.logger import get_logger
import config

log = get_logger("Controls")
bot = bot_client.bot
call = bot_client.call


def player_markup(state) -> InlineKeyboardMarkup:
    """Clean, premium inline player panel."""
    is_playing = state.is_playing and not state.is_paused
    loop_icon = "🔁" if state.loop else ("🔂" if state.loop_all else "➡️")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏮", callback_data="ctrl|prev"),
         InlineKeyboardButton("⏸" if is_playing else "▶️", callback_data="ctrl|pause" if is_playing else "ctrl|resume"),
         InlineKeyboardButton("⏭", callback_data="ctrl|skip"),
         InlineKeyboardButton("⏹", callback_data="ctrl|stop")],
        [InlineKeyboardButton("🔉", callback_data="ctrl|vol_down"),
         InlineKeyboardButton(f"{'▪' * (state.volume // 20)}{'▫' * (5 - state.volume // 20)} {state.volume}%", callback_data="ctrl|vol_info"),
         InlineKeyboardButton("🔊", callback_data="ctrl|vol_up")],
        [InlineKeyboardButton(f"{loop_icon} Loop", callback_data="ctrl|loop"),
         InlineKeyboardButton(f"🔀 {'On' if state.shuffle else 'Off'}", callback_data="ctrl|shuffle"),
         InlineKeyboardButton("🎛 FX", callback_data="ctrl|effects")],
        [InlineKeyboardButton("❤️", callback_data="ctrl|like"),
         InlineKeyboardButton(f"📜 Queue ({len(state.queue)})", callback_data="ctrl|queue"),
         InlineKeyboardButton("✖️", callback_data="ctrl|close")],
    ])


async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id == config.OWNER_ID:
        return True
    sudoers = await db.get_sudoers()
    if user_id in sudoers:
        return True
    if await db.is_auth_user(chat_id, user_id):
        return True
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


async def update_now_playing(chat_id: int, track):
    state = queue_manager.get(chat_id)
    src = {"jiosaavn": "🟣 ᴊɪᴏsᴀᴀᴠɴ", "youtube": "🔴 ʏᴏᴜᴛᴜʙᴇ", "spotify": "🟢 sᴘᴏᴛɪꜰʏ", "soundcloud": "🟠 sᴏᴜɴᴅᴄʟᴏᴜᴅ", "radio": "📻 ʀᴀᴅɪᴏ", "file": "📁 ꜰɪʟᴇ"}.get(track.source, f"🎵 {track.source}")
    bar = progress_bar(0, track.duration or 1)
    fx = []
    if state.bass_boost: fx.append("🔊ʙᴀss")
    if state.nightcore: fx.append("⚡ɴᴄ")
    if state.vaporwave: fx.append("🌊ᴠᴡ")
    if state.eight_d: fx.append("🎧8ᴅ")
    fx_str = " │ ".join(fx) if fx else "ɴᴏɴᴇ"
    loop_str = "🔁 ᴏɴᴇ" if state.loop else ("🔂 ᴀʟʟ" if state.loop_all else "➡️ ᴏꜰꜰ")

    text = (
        f"🎧 **ɴᴏᴡ ᴘʟᴀʏɪɴɢ**\n\n"
        f"📌 **{track.title}**\n"
        f"🎤 {track.uploader or 'Unknown'}\n"
        f"⏱ `{format_duration(track.duration)}` │ {src}\n"
        f"👤 [ᴜsᴇʀ](tg://user?id={track.requested_by})\n\n"
        f"`0:00` {bar} `{format_duration(track.duration)}`\n\n"
        f"🔁 {loop_str} │ 🔀 {'ᴏɴ' if state.shuffle else 'ᴏꜰꜰ'} │ 🔊 `{state.volume}%`\n"
        f"🎛 ᴇꜰꜰᴇᴄᴛs: {fx_str}\n"
        f"📜 `{len(state.queue)}` ᴛʀᴀᴄᴋs ɪɴ ǫᴜᴇᴜᴇ"
    )
    try:
        card = generate_now_playing_card(
            title=track.title, artist=track.uploader or "Unknown",
            duration_str=format_duration(track.duration),
            thumb_path=track.thumb_path if track.thumb_path and not track.thumb_path.startswith("http") else None,
            requested_by=str(track.requested_by), source=track.source.title(),
        )
        if card and os.path.exists(card):
            msg = await bot.send_photo(chat_id, photo=card, caption=text, reply_markup=player_markup(state))
        elif track.thumb_path and (os.path.exists(track.thumb_path) if not track.thumb_path.startswith("http") else True):
            msg = await bot.send_photo(chat_id, photo=track.thumb_path, caption=text, reply_markup=player_markup(state))
        else:
            msg = await bot.send_message(chat_id, text, reply_markup=player_markup(state), disable_web_page_preview=True)
        state.message_id = msg.id
    except Exception as e:
        log.error(f"NP error: {e}")

# ═══ Commands ═══

@bot.on_message(filters.command("skip"))
async def skip_cmd(_, message):
    from plugins.play import _start_playback
    c = message.chat.id
    if not await is_admin(c, message.from_user.id): return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    s = queue_manager.get(c)
    if not s.is_playing: return await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ᴘʟᴀʏɪɴɢ.**")
    await message.reply_text("⏭ **sᴋɪᴘᴘᴇᴅ!**")
    await _start_playback(c)

@bot.on_message(filters.command("pause"))
async def pause_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id): return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    s = queue_manager.get(c)
    if not s.is_playing: return await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ᴘʟᴀʏɪɴɢ.**")
    try:
        await call.pause_stream(c); s.is_paused = True
        await message.reply_text("⏸ **ᴘᴀᴜsᴇᴅ.**")
    except Exception as e: await message.reply_text(f"❌ `{e}`")

@bot.on_message(filters.command("resume"))
async def resume_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id): return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    try:
        await call.resume_stream(c); s = queue_manager.get(c); s.is_paused = False; s.is_playing = True
        await message.reply_text("▶️ **ʀᴇsᴜᴍᴇᴅ.**")
    except Exception as e: await message.reply_text(f"❌ `{e}`")

@bot.on_message(filters.command("stop"))
async def stop_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id): return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    queue_manager.clear(c)
    try: await call.leave_group_call(c)
    except Exception: pass
    await message.reply_text("⏹ **sᴛᴏᴘᴘᴇᴅ & ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ.**")

@bot.on_message(filters.command("loop"))
async def loop_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id): return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    s = queue_manager.get(c)
    if not s.loop and not s.loop_all: s.loop = True; await message.reply_text("🔁 **ʟᴏᴏᴘ: ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ**")
    elif s.loop: s.loop = False; s.loop_all = True; await message.reply_text("🔂 **ʟᴏᴏᴘ: ᴇɴᴛɪʀᴇ ǫᴜᴇᴜᴇ**")
    else: s.loop_all = False; await message.reply_text("➡️ **ʟᴏᴏᴘ: ᴅɪsᴀʙʟᴇᴅ**")

@bot.on_message(filters.command("shuffle"))
async def shuffle_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id): return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    n = queue_manager.shuffle_queue(c)
    await message.reply_text(f"🔀 **sʜᴜꜰꜰʟᴇᴅ {n} ᴛʀᴀᴄᴋs!**")

@bot.on_message(filters.command("volume"))
async def volume_cmd(_, message):
    c = message.chat.id
    if not await is_admin(c, message.from_user.id): return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    if len(message.command) < 2: return await message.reply_text("❗ `/volume <1-200>`")
    try:
        v = int(message.command[1])
        if not 1 <= v <= 200: return await message.reply_text("❗ **1–200 ᴏɴʟʏ.**")
        await call.change_volume_call(c, v); queue_manager.get(c).volume = v
        await message.reply_text(f"🔊 **ᴠᴏʟᴜᴍᴇ: {v}%**")
    except Exception as e: await message.reply_text(f"❌ `{e}`")

@bot.on_message(filters.command("ping"))
async def ping_cmd(_, message):
    t = time.time(); m = await message.reply_text("📡 **ᴘɪɴɢɪɴɢ…**")
    ping = round((time.time() - t) * 1000, 2)
    up = get_readable_time(int(time.time() - bot_client.start_time)) if bot_client.start_time else "N/A"
    st = queue_manager.get_stats()
    await m.edit(f"🚀 **ᴘᴏɴɢ!** `{ping}ms`\n⏱ **ᴜᴘᴛɪᴍᴇ:** `{up}`\n🎵 **ᴀᴄᴛɪᴠᴇ:** `{st['active_chats']}` │ 🎶 **ᴘʟᴀʏᴇᴅ:** `{st['total_played']}`")

@bot.on_message(filters.command("stats"))
async def stats_cmd(_, message):
    import psutil, platform
    st = queue_manager.get_stats(); up = get_readable_time(int(time.time() - bot_client.start_time)) if bot_client.start_time else "N/A"
    g = await db.get_group_count()
    await message.reply_text(
        f"📊 **sᴇᴄʀᴇᴛ ᴍᴜsɪᴄ ʙᴏᴛ sᴛᴀᴛs**\n\n🖥 `{platform.system()}` │ ⚙️ `{psutil.cpu_percent()}%` │ 🧠 `{psutil.virtual_memory().percent}%`\n⏱ `{up}`\n\n🎵 sᴛʀᴇᴀᴍs: `{st['active_chats']}` │ 📜 ǫᴜᴇᴜᴇᴅ: `{st['total_queued']}`\n🎶 ᴘʟᴀʏᴇᴅ: `{st['total_played']}` │ 👥 ɢʀᴏᴜᴘs: `{g}`\n\n👑 @its_me_secret")

@bot.on_message(filters.command("nowplaying"))
async def np_cmd(_, message):
    t = queue_manager.now_playing(message.chat.id)
    if not t: return await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ᴘʟᴀʏɪɴɢ.**")
    await update_now_playing(message.chat.id, t)

# ═══ Callback Handler ═══

@bot.on_callback_query(filters.regex(r"^ctrl\|(.+)$"))
async def ctrl_cb(_, query: CallbackQuery):
    from plugins.play import _start_playback
    action = query.data.split("|")[1]
    chat_id = query.message.chat.id
    uid = query.from_user.id
    state = queue_manager.get(chat_id)

    if action in ("queue", "like", "effects"):
        pass
    elif not await is_admin(chat_id, uid):
        return await query.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ.", show_alert=True)

    if action == "skip":
        await query.answer("⏭"); await _start_playback(chat_id)
    elif action == "prev":
        if state.history:
            state.queue.insert(0, state.history.pop())
            await query.answer("⏮"); await _start_playback(chat_id)
        else: await query.answer("❌ ɴᴏ ᴘʀᴇᴠɪᴏᴜs.", show_alert=True)
    elif action == "pause":
        try: await call.pause_stream(chat_id); state.is_paused = True; await query.answer("⏸")
        except: await query.answer("ᴇʀʀᴏʀ", show_alert=True)
    elif action == "resume":
        try: await call.resume_stream(chat_id); state.is_paused = False; state.is_playing = True; await query.answer("▶️")
        except: await query.answer("ᴇʀʀᴏʀ", show_alert=True)
    elif action == "loop":
        if not state.loop and not state.loop_all: state.loop = True; await query.answer("🔁 ʟᴏᴏᴘ: ᴏɴᴇ")
        elif state.loop: state.loop = False; state.loop_all = True; await query.answer("🔂 ʟᴏᴏᴘ: ᴀʟʟ")
        else: state.loop_all = False; await query.answer("➡️ ʟᴏᴏᴘ: ᴏꜰꜰ")
    elif action == "shuffle":
        state.shuffle = not state.shuffle; await query.answer(f"🔀 {'ᴏɴ' if state.shuffle else 'ᴏꜰꜰ'}")
    elif action == "stop":
        queue_manager.clear(chat_id)
        try: await call.leave_group_call(chat_id)
        except: pass
        await query.answer("⏹"); await query.message.edit_reply_markup(None)
        await query.message.reply_text("⏹ **ᴘʟᴀʏʙᴀᴄᴋ sᴛᴏᴘᴘᴇᴅ.**"); return
    elif action == "vol_up":
        v = min(state.volume + 10, 200)
        try: await call.change_volume_call(chat_id, v); state.volume = v; await query.answer(f"🔊 {v}%")
        except: await query.answer("ᴇʀʀᴏʀ", show_alert=True)
    elif action == "vol_down":
        v = max(state.volume - 10, 10)
        try: await call.change_volume_call(chat_id, v); state.volume = v; await query.answer(f"🔉 {v}%")
        except: await query.answer("ᴇʀʀᴏʀ", show_alert=True)
    elif action == "vol_info":
        await query.answer(f"🔊 ᴠᴏʟᴜᴍᴇ: {state.volume}%", show_alert=True); return
    elif action == "queue":
        from plugins.queue import build_queue_text, queue_markup
        await query.answer(); await query.message.reply_text(build_queue_text(chat_id), reply_markup=queue_markup(chat_id), disable_web_page_preview=True); return
    elif action == "like":
        t = state.current
        if t:
            await db.add_favourite(uid, {"id": t.id, "title": t.title, "url": t.url, "duration": t.duration})
            await query.answer("❤️ ᴀᴅᴅᴇᴅ ᴛᴏ ꜰᴀᴠs!", show_alert=True)
        else: await query.answer("❌ ɴᴏᴛʜɪɴɢ ᴘʟᴀʏɪɴɢ.", show_alert=True)
        return
    elif action == "effects":
        await query.answer()
        from plugins.effects import effects_text_and_markup
        txt, mk = effects_text_and_markup(chat_id)
        await query.message.reply_text(txt, reply_markup=mk); return
    elif action == "close":
        await query.message.delete(); await query.answer(); return

    # Refresh player buttons
    try: await query.edit_message_reply_markup(reply_markup=player_markup(state))
    except: pass