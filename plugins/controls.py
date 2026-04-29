import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from client.client import bot_client
from utils.queue_manager import queue_manager

bot = bot_client.bot
user = bot_client.user
call = bot_client.call

def player_controls_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸ ᴘᴀᴜsᴇ", callback_data="ctrl|pause"),
                InlineKeyboardButton("▶️ ʀᴇsᴜᴍᴇ", callback_data="ctrl|resume"),
                InlineKeyboardButton("⏭ sᴋɪᴘ", callback_data="ctrl|skip"),
            ],
            [
                InlineKeyboardButton("🔁 ʟᴏᴏᴘ", callback_data="ctrl|loop"),
                InlineKeyboardButton("⏹ sᴛᴏᴘ", callback_data="ctrl|stop"),
            ],
            [
                InlineKeyboardButton("📜 ǫᴜᴇᴜᴇ", callback_data="ctrl|queue"),
                InlineKeyboardButton("🛠 sᴜᴘᴘᴏʀᴛ", url="https://t.me/SupportGroup"),
            ],
            [
                InlineKeyboardButton("👑 ᴅᴇᴠ:- @its_me_secret 👑", url="https://t.me/its_me_secret"),
            ],
        ]
    )

def _get_progress_bar(percentage: int) -> str:
    filled = "▰"
    empty = "▱"
    size = 12
    progress = int(percentage / 100 * size)
    return filled * progress + empty * (size - progress)

async def update_now_playing(chat_id: int, track):
    state = queue_manager.get(chat_id)
    bar = _get_progress_bar(0) 
    
    text = (
        f"🎵 **ɴᴏᴡ ᴘʟᴀʏɪɴɢ**\n\n"
        f"**📌 ᴛɪᴛʟᴇ:** [{track.title}]({track.url})\n"
        f"**⏱ ᴅᴜʀᴀᴛɪᴏɴ:** `{_fmt(track.duration)}`\n"
        f"**👤 ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:** [ᴜsᴇʀ](tg://user?id={track.requested_by})\n\n"
        f"0:00 {bar} {_fmt(track.duration)}\n\n"
        f"**sᴛᴀᴛᴜs:** {'🔄 ʟᴏᴏᴘɪɴɢ' if state.loop else '▶️ ᴘʟᴀʏɪɴɢ'}\n"
        f"**ǫᴜᴇᴜᴇ:** `{len(state.queue)}` ᴛʀᴀᴄᴋs ʟᴇꜰᴛ"
    )
    
    if track.thumb_path and os.path.exists(track.thumb_path):
        msg = await bot.send_photo(
            chat_id, 
            photo=track.thumb_path, 
            caption=text, 
            reply_markup=player_controls_markup()
        )
    else:
        msg = await bot.send_message(
            chat_id, 
            text, 
            reply_markup=player_controls_markup(), 
            disable_web_page_preview=True
        )
    
    state.message_id = msg.id

@bot.on_message(filters.command("skip"))
async def skip_cmd(_, message):
    from plugins.play import _start_playback
    chat_id = message.chat.id
    state = queue_manager.get(chat_id)
    if not state.is_playing:
        return await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ ʀɪɢʜᴛ ɴᴏᴡ.**")
    await message.reply_text("⏭ **sᴋɪᴘᴘᴇᴅ ᴛᴏ ᴛʜᴇ ɴᴇxᴛ ᴛʀᴀᴄᴋ.**")
    await _start_playback(chat_id)

@bot.on_message(filters.command("pause"))
async def pause_cmd(_, message):
    chat_id = message.chat.id
    state = queue_manager.get(chat_id)
    if not state.is_playing:
        return await message.reply_text("❌ **ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.**")
    try:
        await call.pause_stream(chat_id)
        state.is_playing = False
        await message.reply_text("⏸ **ᴘᴀᴜsᴇᴅ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ.**")
    except Exception as e:
        await message.reply_text(f"❌ **ᴇʀʀᴏʀ:** `{e}`")

@bot.on_message(filters.command("resume"))
async def resume_cmd(_, message):
    chat_id = message.chat.id
    state = queue_manager.get(chat_id)
    try:
        await call.resume_stream(chat_id)
        state.is_playing = True
        await message.reply_text("▶️ **ʀᴇsᴜᴍᴇᴅ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ.**")
    except Exception as e:
        await message.reply_text(f"❌ **ᴇʀʀᴏʀ:** `{e}`")

@bot.on_message(filters.command("stop"))
async def stop_cmd(_, message):
    chat_id = message.chat.id
    queue_manager.clear(chat_id)
    try:
        await call.leave_call(chat_id)
    except Exception:
        pass
    await message.reply_text("⏹ **sᴛᴏᴘᴘᴇᴅ ᴘʟᴀʏʙᴀᴄᴋ ᴀɴᴅ ᴄʟᴇᴀʀᴇᴅ ᴛʜᴇ ǫᴜᴇᴜᴇ.**")

@bot.on_message(filters.command("loop"))
async def loop_cmd(_, message):
    chat_id = message.chat.id
    state = queue_manager.get(chat_id)
    state.loop = not state.loop
    await message.reply_text(f"🔁 **ʟᴏᴏᴘ ɪs ɴᴏᴡ {'ᴇɴᴀʙʟᴇᴅ' if state.loop else 'ᴅɪsᴀʙʟᴇᴅ'}.**")

@bot.on_message(filters.command("volume"))
async def volume_cmd(_, message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply_text("❗ **ᴜsᴀɢᴇ:** `/volume <1-200>`")
    try:
        vol = int(message.command[1])
        if not 1 <= vol <= 200:
            return await message.reply_text("❗ **ᴠᴏʟᴜᴍᴇ ᴍᴜsᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ 1 ᴀɴᴅ 200.**")
        await call.change_volume_call(chat_id, vol)
        await message.reply_text(f"🔊 **ᴠᴏʟᴜᴍᴇ sᴇᴛ ᴛᴏ {vol}%.**")
    except Exception as e:
        await message.reply_text(f"❌ **ᴇʀʀᴏʀ ᴄʜᴀɴɢɪɴɢ ᴠᴏʟᴜᴍᴇ:** `{e}`")

@bot.on_message(filters.command("ping"))
async def ping_cmd(_, message):
    start_time = time.time()
    m = await message.reply_text("📡 **ᴘɪɴɢɪɴɢ…**")
    end_time = time.time()
    ping = round((end_time - start_time) * 1000, 2)
    await m.edit(f"🚀 **ᴘᴏɴɢ!** `{ping}ᴍs`\n✨ **sᴛᴀᴛᴜs:** `sᴍᴏᴏᴛʜ ᴀs ʙᴜᴛᴛᴇʀ`")

@bot.on_message(filters.command("stats"))
async def stats_cmd(_, message):
    import psutil
    import platform
    from datetime import datetime
    
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    uptime = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    
    text = (
        f"📊 **sʏsᴛᴇᴍ sᴛᴀᴛɪsᴛɪᴄs**\n\n"
        f"🖥 **ᴏs:** `{platform.system()}`\n"
        f"⚙️ **ᴄᴘᴜ ᴜsᴀɢᴇ:** `{cpu}%`\n"
        f"🧠 **ʀᴀᴍ ᴜsᴀɢᴇ:** `{mem}%`\n"
        f"💾 **ᴅɪsᴋ ᴜsᴀɢᴇ:** `{disk}%`\n"
        f"⏱ **sʏsᴛᴇᴍ ᴜᴘᴛɪᴍᴇ:** `{uptime}`\n\n"
        f"👑 **ᴅᴇᴠ:- @its_me_secret**"
    )
    await message.reply_text(text)

@bot.on_callback_query(filters.regex(r"^ctrl\|(skip|pause|resume|loop|stop|queue)$"))
async def ctrl_cb(_, query: CallbackQuery):
    from plugins.play import _start_playback
    action = query.data.split("|")[1]
    chat_id = query.message.chat.id
    state = queue_manager.get(chat_id)

    if action == "skip":
        await query.answer("sᴋɪᴘᴘɪɴɢ…")
        await _start_playback(chat_id)

    elif action == "pause":
        try:
            await call.pause_stream(chat_id)
            state.is_playing = False
            await query.answer("ᴘᴀᴜsᴇᴅ.")
        except Exception:
            await query.answer("ᴇʀʀᴏʀ ᴘᴀᴜsɪɴɢ.", show_alert=True)

    elif action == "resume":
        try:
            await call.resume_stream(chat_id)
            state.is_playing = True
            await query.answer("ʀᴇsᴜᴍᴇᴅ.")
        except Exception:
            await query.answer("ᴇʀʀᴏʀ ʀᴇsᴜᴍɪɴɢ.", show_alert=True)

    elif action == "loop":
        state.loop = not state.loop
        await query.answer(f"ʟᴏᴏᴘ {'ᴏɴ' if state.loop else 'ᴏꜰꜰ'}")

    elif action == "stop":
        queue_manager.clear(chat_id)
        try:
            await call.leave_call(chat_id)
        except Exception:
            pass
        await query.answer("sᴛᴏᴘᴘᴇᴅ.")
        await query.message.edit_reply_markup(None)
        await query.message.reply_text("⏹ **ᴘʟᴀʏʙᴀᴄᴋ sᴛᴏᴘᴘᴇᴅ & ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ.**")

    elif action == "queue":
        from plugins.queue import build_queue_text
        await query.answer()
        text = build_queue_text(chat_id)
        await query.message.reply_text(text, disable_web_page_preview=True)

def _fmt(seconds: int | None) -> str:
    if not seconds:
        return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"