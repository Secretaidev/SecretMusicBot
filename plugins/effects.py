"""Audio effects — interactive button panel with bass, nightcore, vaporwave, 8D, speed."""

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from plugins.controls import is_admin
from utils.queue_manager import queue_manager

bot = bot_client.bot


def effects_text_and_markup(chat_id: int):
    """Return (text, markup) for the effects panel — used by controls too."""
    state = queue_manager.get(chat_id)
    text = (
        f"🎛 **ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛs ᴘᴀɴᴇʟ**\n\n"
        f"🔊 ʙᴀss ʙᴏᴏsᴛ: `{'✅ ᴏɴ' if state.bass_boost else '❌ ᴏꜰꜰ'}`\n"
        f"⚡ ɴɪɢʜᴛᴄᴏʀᴇ: `{'✅ ᴏɴ' if state.nightcore else '❌ ᴏꜰꜰ'}`\n"
        f"🌊 ᴠᴀᴘᴏʀᴡᴀᴠᴇ: `{'✅ ᴏɴ' if state.vaporwave else '❌ ᴏꜰꜰ'}`\n"
        f"🎧 8ᴅ ᴀᴜᴅɪᴏ: `{'✅ ᴏɴ' if state.eight_d else '❌ ᴏꜰꜰ'}`\n"
        f"⚡ sᴘᴇᴇᴅ: `{state.speed}x`\n"
        f"🔊 ᴠᴏʟᴜᴍᴇ: `{state.volume}%`\n\n"
        f"💡 ᴇꜰꜰᴇᴄᴛs ᴀᴘᴘʟʏ ᴛᴏ ɴᴇxᴛ ᴛʀᴀᴄᴋ"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔊 ʙᴀss {'✅' if state.bass_boost else '❌'}", callback_data="fx|bass"),
         InlineKeyboardButton(f"⚡ ɴɪɢʜᴛᴄᴏʀᴇ {'✅' if state.nightcore else '❌'}", callback_data="fx|nightcore")],
        [InlineKeyboardButton(f"🌊 ᴠᴀᴘᴏʀᴡᴀᴠᴇ {'✅' if state.vaporwave else '❌'}", callback_data="fx|vaporwave"),
         InlineKeyboardButton(f"🎧 8ᴅ {'✅' if state.eight_d else '❌'}", callback_data="fx|8d")],
        [InlineKeyboardButton("⏪ 0.75x", callback_data="fx|s075"),
         InlineKeyboardButton("⏺ 1.0x", callback_data="fx|s100"),
         InlineKeyboardButton("⏩ 1.25x", callback_data="fx|s125"),
         InlineKeyboardButton("⏩ 1.5x", callback_data="fx|s150"),
         InlineKeyboardButton("⏩ 2.0x", callback_data="fx|s200")],
        [InlineKeyboardButton("🔄 ʀᴇsᴇᴛ ᴀʟʟ", callback_data="fx|reset")],
        [InlineKeyboardButton("🗑 ᴄʟᴏsᴇ", callback_data="fx|close")],
    ])
    return text, markup


@bot.on_message(filters.command(["effects", "eq", "equalizer"]))
async def effects_cmd(_, message):
    txt, mk = effects_text_and_markup(message.chat.id)
    await message.reply_text(txt, reply_markup=mk)


@bot.on_message(filters.command("bass"))
async def bass_cmd(_, m):
    if not await is_admin(m.chat.id, m.from_user.id): return await m.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    s = queue_manager.get(m.chat.id); s.bass_boost = not s.bass_boost
    await m.reply_text(f"🔊 **ʙᴀss ʙᴏᴏsᴛ: {'✅ ᴏɴ' if s.bass_boost else '❌ ᴏꜰꜰ'}**")

@bot.on_message(filters.command("nightcore"))
async def nightcore_cmd(_, m):
    if not await is_admin(m.chat.id, m.from_user.id): return await m.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    s = queue_manager.get(m.chat.id); s.nightcore = not s.nightcore
    if s.nightcore: s.vaporwave = False
    await m.reply_text(f"⚡ **ɴɪɢʜᴛᴄᴏʀᴇ: {'✅ ᴏɴ' if s.nightcore else '❌ ᴏꜰꜰ'}**")

@bot.on_message(filters.command("vaporwave"))
async def vaporwave_cmd(_, m):
    if not await is_admin(m.chat.id, m.from_user.id): return await m.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    s = queue_manager.get(m.chat.id); s.vaporwave = not s.vaporwave
    if s.vaporwave: s.nightcore = False
    await m.reply_text(f"🌊 **ᴠᴀᴘᴏʀᴡᴀᴠᴇ: {'✅ ᴏɴ' if s.vaporwave else '❌ ᴏꜰꜰ'}**")

@bot.on_message(filters.command("8d"))
async def eight_d_cmd(_, m):
    if not await is_admin(m.chat.id, m.from_user.id): return await m.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    s = queue_manager.get(m.chat.id); s.eight_d = not s.eight_d
    await m.reply_text(f"🎧 **8ᴅ ᴀᴜᴅɪᴏ: {'✅ ᴏɴ' if s.eight_d else '❌ ᴏꜰꜰ'}**")

@bot.on_message(filters.command("speed"))
async def speed_cmd(_, m):
    if not await is_admin(m.chat.id, m.from_user.id): return await m.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")
    if len(m.command) < 2:
        return await m.reply_text(f"⚡ **sᴘᴇᴇᴅ:** `{queue_manager.get(m.chat.id).speed}x`\n❗ `/speed <0.5-2.0>`")
    try:
        v = float(m.command[1])
        if not 0.5 <= v <= 2.0: return await m.reply_text("❗ **0.5–2.0**")
        queue_manager.get(m.chat.id).speed = v
        await m.reply_text(f"⚡ **sᴘᴇᴇᴅ: `{v}x`**")
    except ValueError: await m.reply_text("❗ `/speed <0.5-2.0>`")


@bot.on_callback_query(filters.regex(r"^fx\|(.+)$"))
async def fx_cb(_, query: CallbackQuery):
    action = query.data.split("|")[1]
    chat_id = query.message.chat.id

    if action == "close":
        await query.message.delete(); return await query.answer()

    if not await is_admin(chat_id, query.from_user.id):
        return await query.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ.", show_alert=True)

    s = queue_manager.get(chat_id)
    if action == "bass": s.bass_boost = not s.bass_boost; await query.answer(f"🔊 ʙᴀss {'ᴏɴ' if s.bass_boost else 'ᴏꜰꜰ'}")
    elif action == "nightcore":
        s.nightcore = not s.nightcore
        if s.nightcore: s.vaporwave = False
        await query.answer(f"⚡ ɴɪɢʜᴛᴄᴏʀᴇ {'ᴏɴ' if s.nightcore else 'ᴏꜰꜰ'}")
    elif action == "vaporwave":
        s.vaporwave = not s.vaporwave
        if s.vaporwave: s.nightcore = False
        await query.answer(f"🌊 ᴠᴀᴘᴏʀᴡᴀᴠᴇ {'ᴏɴ' if s.vaporwave else 'ᴏꜰꜰ'}")
    elif action == "8d": s.eight_d = not s.eight_d; await query.answer(f"🎧 8ᴅ {'ᴏɴ' if s.eight_d else 'ᴏꜰꜰ'}")
    elif action == "reset":
        s.bass_boost = s.nightcore = s.vaporwave = s.eight_d = False; s.speed = 1.0
        await query.answer("🔄 ᴀʟʟ ᴇꜰꜰᴇᴄᴛs ʀᴇsᴇᴛ!")
    elif action.startswith("s"):
        speeds = {"s075": 0.75, "s100": 1.0, "s125": 1.25, "s150": 1.5, "s200": 2.0}
        s.speed = speeds.get(action, 1.0); await query.answer(f"⚡ {s.speed}x")

    txt, mk = effects_text_and_markup(chat_id)
    try: await query.edit_message_text(txt, reply_markup=mk)
    except: pass
