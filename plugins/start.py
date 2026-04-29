import config
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client

bot = bot_client.bot

START_IMG = "https://telegra.ph/file/a1c4c5a5d8e1c2f3b4c5d.jpg"

START_TEXT = """✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴡᴏʀʟᴅ's ʙᴇsᴛ ᴍᴜsɪᴄ ʙᴏᴛ** ✨

🎶 **ɪ ᴄᴀɴ ᴘʟᴀʏ ᴍᴜsɪᴄ ɪɴ ʏᴏᴜʀ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs ᴡɪᴛʜ ʜɪɢʜ ǫᴜᴀʟɪᴛʏ ᴀɴᴅ ᴢᴇʀᴏ ʟᴀɢ.**

🚀 **ꜰᴇᴀᴛᴜʀᴇs:**
├ 🔊 **ʜɪɢʜ ǫᴜᴀʟɪᴛʏ ᴀᴜᴅɪᴏ**
├ ⏳ **ᴢᴇʀᴏ ʟᴀɢ sᴛʀᴇᴀᴍɪɴɢ**
├ 📜 **ǫᴜᴇᴜᴇ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ**
├ 🔗 **ᴊɪᴏsᴀᴀᴠɴ sᴜᴘᴘᴏʀᴛ**
└ 🛠 **ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟs**

**ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴇxᴘʟᴏʀᴇ ᴍᴏʀᴇ!**"""

HELP_TEXT = """**📚 ᴀᴅᴠᴀɴᴄᴇᴅ ᴍᴜsɪᴄ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs**

🎵 **ᴘʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs:**
├ `/play <name>` — ᴘʟᴀʏ sᴏɴɢ ꜰʀᴏᴍ ʏᴏᴜᴛᴜʙᴇ
├ `/vplay <name>` — ᴘʟᴀʏ ᴠɪᴅᴇᴏ ꜰʀᴏᴍ ʏᴏᴜᴛᴜʙᴇ
└ `/saavn <name>` — ᴘʟᴀʏ sᴏɴɢ ꜰʀᴏᴍ ᴊɪᴏsᴀᴀᴠɴ

🎮 **ᴄᴏɴᴛʀᴏʟ ᴄᴏᴍᴍᴀɴᴅs:**
├ `/pause` — ᴘᴀᴜsᴇ ᴛʜᴇ sᴛʀᴇᴀᴍ
├ `/resume` — ʀᴇsᴜᴍᴇ ᴛʜᴇ sᴛʀᴇᴀᴍ
├ `/skip` — sᴋɪᴘ ᴛᴏ ɴᴇxᴛ sᴏɴɢ
├ `/stop` — sᴛᴏᴘ ᴀɴᴅ ᴄʟᴇᴀʀ ǫᴜᴇᴜᴇ
└ `/volume <1-200>` — sᴇᴛ ᴛʜᴇ sᴛʀᴇᴀᴍ ᴠᴏʟᴜᴍᴇ

🛠 **ᴏᴛʜᴇʀ ᴄᴏᴍᴍᴀɴᴅs:**
├ `/queue` — ᴠɪᴇᴡ ᴛʜᴇ ǫᴜᴇᴜᴇ
├ `/loop` — ᴇɴᴀʙʟᴇ/ᴅɪsᴀʙʟᴇ ʟᴏᴏᴘ
├ `/ping` — ᴄʜᴇᴄᴋ ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ
└ `/stats` — ᴠɪᴇᴡ sʏsᴛᴇᴍ sᴛᴀᴛs

👮‍♂️ **ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:**
├ `/auth` — ᴀᴜᴛʜᴏʀɪsᴇ ᴀ ᴜsᴇʀ (ʀᴇᴘʟʏ)
├ `/unauth` — ᴜɴᴀᴜᴛʜᴏʀɪsᴇ ᴀ ᴜsᴇʀ (ʀᴇᴘʟʏ)
├ `/addsudo` — ᴀᴅᴅ sᴜᴅᴏ ᴜsᴇʀ (ᴏᴡɴᴇʀ ᴏɴʟʏ)
├ `/delsudo` — ʀᴇᴍᴏᴠᴇ sᴜᴅᴏ ᴜsᴇʀ (ᴏᴡɴᴇʀ ᴏɴʟʏ)
└ `/broadcast` — ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ (sᴜᴅᴏ ᴏɴʟʏ)"""

def start_markup(username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕", url=f"https://t.me/{username}?startgroup=true")],
        [InlineKeyboardButton("📖 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help"),
         InlineKeyboardButton("⚙️ sᴇᴛᴛɪɴɢs", callback_data="settings")],
        [InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇs", url="https://t.me/UpdatesChannel"),
         InlineKeyboardButton("🛠 sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT)],
        [InlineKeyboardButton("👑 ᴏᴡɴᴇʀ 👑", url=f"tg://user?id={config.OWNER_ID}")]
    ])

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(_, message):
    me = await bot.get_me()
    await message.reply_photo(
        START_IMG, 
        caption=START_TEXT, 
        reply_markup=start_markup(me.username)
    )

@bot.on_callback_query(filters.regex("^help$"))
async def help_cb(_, query: CallbackQuery):
    await query.edit_message_caption(
        caption=HELP_TEXT, 
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="start")]]
        )
    )

@bot.on_callback_query(filters.regex("^start$"))
async def back_cb(_, query: CallbackQuery):
    me = await bot.get_me()
    await query.edit_message_caption(
        caption=START_TEXT, 
        reply_markup=start_markup(me.username)
    )

@bot.on_callback_query(filters.regex("^settings$"))
async def settings_cb(_, query: CallbackQuery):
    await query.answer("sᴇᴛᴛɪɴɢs ᴍᴇɴᴜ ɪs ᴜɴᴅᴇʀ ᴅᴇᴠᴇʟᴏᴘᴍᴇɴᴛ!", show_alert=True)