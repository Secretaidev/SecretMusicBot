"""Radio streaming — preset stations and custom stream URLs.

Uses modern pytgcalls MediaStream for live radio.
"""

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, CallbackQuery

from client.client import bot_client
from plugins.controls import is_admin
from plugins.assistant_handler import assistant_join
from plugins.play import _join_and_stream, _leave_vc
from utils.queue_manager import queue_manager, Track
from utils.radio import RadioManager
from utils.logger import get_logger

log = get_logger("Radio")
bot = bot_client.bot
call = bot_client.call


@bot.on_message(filters.command("radio"))
async def radio_cmd(_, message):
    chat_id = message.chat.id
    if not await is_admin(chat_id, message.from_user.id):
        return await message.reply_text("❌ **ᴀᴅᴍɪɴs ᴏɴʟʏ.**")

    if len(message.command) < 2:
        text = RadioManager.format_station_list()
        stations = RadioManager.get_station_list()
        buttons = []
        row = []
        for s in stations:
            row.append(IKB(s["name"][:18], callback_data=f"rad|{s['key']}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([IKB("🗑 ᴄʟᴏsᴇ", callback_data="rad|close")])
        return await message.reply_text(text, reply_markup=IKM(buttons))

    key = message.command[1].lower()
    station = RadioManager.get_station(key)
    if station:
        stream_url, name = station["url"], station["name"]
    elif key.startswith("http"):
        stream_url, name = key, "📻 ᴄᴜsᴛᴏᴍ ʀᴀᴅɪᴏ"
    else:
        return await message.reply_text("❌ **sᴛᴀᴛɪᴏɴ ɴᴏᴛ ꜰᴏᴜɴᴅ.** ᴜsᴇ `/radio`")

    await _start_radio(chat_id, message.from_user.id, stream_url, name, message)


@bot.on_callback_query(filters.regex(r"^rad\|(.+)$"))
async def radio_cb(_, query: CallbackQuery):
    key = query.data.split("|")[1]
    chat_id = query.message.chat.id
    if key == "close":
        await query.message.delete()
        return await query.answer()
    if not await is_admin(chat_id, query.from_user.id):
        return await query.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ.", show_alert=True)
    station = RadioManager.get_station(key)
    if not station:
        return await query.answer("❌ ɴᴏᴛ ꜰᴏᴜɴᴅ.", show_alert=True)
    await query.answer(f"📻 {station['name']}…")
    await query.edit_message_text(f"📻 **sᴛᴀʀᴛɪɴɢ {station['name']}…**")
    await _start_radio(chat_id, query.from_user.id, station["url"], station["name"], query.message)


async def _start_radio(chat_id, user_id, stream_url, name, reply_target):
    queue_manager.clear(chat_id)
    await assistant_join(chat_id)

    state = queue_manager.get(chat_id)
    state.is_radio = True
    state.is_playing = True
    state.current = Track(
        id="radio", title=name, duration=None,
        uploader="Live Radio", url=stream_url,
        file_path=stream_url, requested_by=user_id, source="radio",
    )

    if not call:
        state.is_playing = False
        return await reply_target.edit_text("❌ **ᴀssɪsᴛᴀɴᴛ ɴᴏᴛ ᴄᴏɴꜰɪɢᴜʀᴇᴅ.**")

    try:
        await _join_and_stream(chat_id, stream_url)
        try:
            await reply_target.edit_text(
                f"📻 **ɴᴏᴡ sᴛʀᴇᴀᴍɪɴɢ**\n\n🎵 {name}\n🔴 **ʟɪᴠᴇ**\n\n/stop ᴛᴏ sᴛᴏᴘ.",
                reply_markup=IKM([[IKB("⏹ sᴛᴏᴘ", callback_data="ctrl|stop")]]),
            )
        except Exception:
            await bot.send_message(chat_id,
                f"📻 **ɴᴏᴡ sᴛʀᴇᴀᴍɪɴɢ**\n\n🎵 {name}\n🔴 **ʟɪᴠᴇ**",
                reply_markup=IKM([[IKB("⏹ sᴛᴏᴘ", callback_data="ctrl|stop")]]),
            )
    except Exception as e:
        state.is_playing = False
        state.is_radio = False
        try:
            await reply_target.edit_text(f"❌ `{e}`")
        except Exception:
            await bot.send_message(chat_id, f"❌ **ʀᴀᴅɪᴏ ᴇʀʀᴏʀ:** `{e}`")
