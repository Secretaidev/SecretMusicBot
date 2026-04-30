"""Start command handler — the world's most advanced welcome system.

Multi-page interactive button navigation with:
- Categorized help pages with sub-navigation
- Live bot statistics in start message
- Feature showcase carousel
- About/credits page
"""

import time
import config
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client.client import bot_client
from utils.queue_manager import queue_manager
from utils.database import db
from utils.helpers import get_readable_time

bot = bot_client.bot

START_IMG = "https://telegra.ph/file/a1c4c5a5d8e1c2f3b4c5d.jpg"

# ═══════════════════════════════════════════════════════════════
# START TEXT
# ═══════════════════════════════════════════════════════════════
START_TEXT = """✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {bot_name} ᴠ{version}** ✨

🎶 **ᴛʜᴇ ᴡᴏʀʟᴅ's ᴍᴏsᴛ ᴀᴅᴠᴀɴᴄᴇᴅ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ ʙᴏᴛ**

🌐 **sᴜᴘᴘᴏʀᴛᴇᴅ ᴘʟᴀᴛꜰᴏʀᴍs:**
├ 🔴 ʏᴏᴜᴛᴜʙᴇ  ├ 🟢 sᴘᴏᴛɪꜰʏ
├ 🟣 ᴊɪᴏsᴀᴀᴠɴ ├ 🟠 sᴏᴜɴᴅᴄʟᴏᴜᴅ
└ 📻 ʟɪᴠᴇ ʀᴀᴅɪᴏ (8+ sᴛᴀᴛɪᴏɴs)

⚡ **ᴘᴏᴡᴇʀᴇᴅ ʙʏ:**
├ 🎛 ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛs (ʙᴀss, ɴɪɢʜᴛᴄᴏʀᴇ, 8ᴅ)
├ 📜 ᴀᴅᴠᴀɴᴄᴇᴅ ǫᴜᴇᴜᴇ (300 ᴛʀᴀᴄᴋs)
├ ❤️ ꜰᴀᴠᴏᴜʀɪᴛᴇs & ᴘʟᴀʏʟɪsᴛs
├ 📥 sᴏɴɢ & ᴠɪᴅᴇᴏ ᴅᴏᴡɴʟᴏᴀᴅ
└ 🔍 ɪɴʟɪɴᴇ sᴇᴀʀᴄʜ ᴍᴏᴅᴇ

**ᴛᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ᴛᴏ ᴇxᴘʟᴏʀᴇ** 👇"""

# ═══════════════════════════════════════════════════════════════
# HELP PAGES
# ═══════════════════════════════════════════════════════════════
PLAY_HELP = """🎵 **ᴍᴜsɪᴄ ᴘʟᴀʏʙᴀᴄᴋ ᴄᴏᴍᴍᴀɴᴅs**

**ᴍᴜʟᴛɪ-ᴘʟᴀᴛꜰᴏʀᴍ sᴜᴘᴘᴏʀᴛ:**
├ `/play <name/url>` — ᴘʟᴀʏ ꜰʀᴏᴍ ʏᴏᴜᴛᴜʙᴇ
├ `/vplay <name/url>` — ᴘʟᴀʏ ᴠɪᴅᴇᴏ sᴛʀᴇᴀᴍ
├ `/saavn <name>` — ᴘʟᴀʏ ꜰʀᴏᴍ ᴊɪᴏsᴀᴀᴠɴ
├ `/spotify <name>` — sᴇᴀʀᴄʜ & ᴘʟᴀʏ sᴘᴏᴛɪꜰʏ
├ `/cplay <name>` — ᴘʟᴀʏ ꜰʀᴏᴍ sᴏᴜɴᴅᴄʟᴏᴜᴅ
└ `/radio [station]` — sᴛʀᴇᴀᴍ ʟɪᴠᴇ ʀᴀᴅɪᴏ

**ᴅᴏᴡɴʟᴏᴀᴅ ᴍᴏᴅᴇ:**
├ `/song <name>` — ᴅᴏᴡɴʟᴏᴀᴅ ᴀs 320ᴋʙᴘs ᴍᴘ3
└ `/video <name>` — ᴅᴏᴡɴʟᴏᴀᴅ ᴀs ᴠɪᴅᴇᴏ ꜰɪʟᴇ

💡 **ᴛɪᴘ:** ʀᴇᴘʟʏ ᴛᴏ ᴀɴ ᴀᴜᴅɪᴏ ꜰɪʟᴇ ᴡɪᴛʜ /play ᴛᴏ sᴛʀᴇᴀᴍ ɪᴛ!
💡 **ᴛɪᴘ:** ᴘᴀsᴛᴇ ᴀɴʏ sᴘᴏᴛɪꜰʏ/ʏᴛ ᴜʀʟ ᴅɪʀᴇᴄᴛʟʏ!"""

CONTROL_HELP = """🎮 **ᴘʟᴀʏʙᴀᴄᴋ ᴄᴏɴᴛʀᴏʟs**

**ʙᴀsɪᴄ ᴄᴏɴᴛʀᴏʟs:**
├ `/pause` — ⏸ ᴘᴀᴜsᴇ sᴛʀᴇᴀᴍ
├ `/resume` — ▶️ ʀᴇsᴜᴍᴇ sᴛʀᴇᴀᴍ
├ `/skip` — ⏭ sᴋɪᴘ ᴛᴏ ɴᴇxᴛ
├ `/stop` — ⏹ sᴛᴏᴘ & ᴄʟᴇᴀʀ ǫᴜᴇᴜᴇ
├ `/volume <1-200>` — 🔊 sᴇᴛ ᴠᴏʟᴜᴍᴇ
├ `/loop` — 🔁 ᴄʏᴄʟᴇ ʟᴏᴏᴘ (ᴏꜰꜰ/ᴏɴᴇ/ᴀʟʟ)
├ `/shuffle` — 🔀 sʜᴜꜰꜰʟᴇ ǫᴜᴇᴜᴇ
└ `/nowplaying` — 🎧 sʜᴏᴡ ᴄᴜʀʀᴇɴᴛ

💡 **ᴛɪᴘ:** ᴀʟʟ ᴄᴏɴᴛʀᴏʟs ᴀʟsᴏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴀs ʙᴜᴛᴛᴏɴs ɪɴ ᴛʜᴇ ᴘʟᴀʏᴇʀ!"""

EFFECTS_HELP = """🎛 **ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛs & ᴇǫᴜᴀʟɪᴢᴇʀ**

**ᴇꜰꜰᴇᴄᴛs:**
├ `/bass` — 🔊 ᴛᴏɢɢʟᴇ ʙᴀss ʙᴏᴏsᴛ
├ `/nightcore` — ⚡ ɴɪɢʜᴛᴄᴏʀᴇ (ꜰᴀsᴛ+ʜɪɢʜ ᴘɪᴛᴄʜ)
├ `/vaporwave` — 🌊 ᴠᴀᴘᴏʀᴡᴀᴠᴇ (sʟᴏᴡ+ʟᴏᴡ ᴘɪᴛᴄʜ)
├ `/8d` — 🎧 8ᴅ sᴜʀʀᴏᴜɴᴅ sᴏᴜɴᴅ
├ `/speed <0.5-2.0>` — ⚡ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ
└ `/effects` — 🎛 ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ᴇꜰꜰᴇᴄᴛs ᴘᴀɴᴇʟ

💡 **ᴛɪᴘ:** ᴜsᴇ `/effects` ꜰᴏʀ ᴀ ʙᴇᴀᴜᴛɪꜰᴜʟ ʙᴜᴛᴛᴏɴ ᴘᴀɴᴇʟ!"""

QUEUE_HELP = """📜 **ǫᴜᴇᴜᴇ & ᴘʟᴀʏʟɪsᴛ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ**

**ǫᴜᴇᴜᴇ:**
├ `/queue` — 📜 ᴠɪᴇᴡ ǫᴜᴇᴜᴇ (ᴘᴀɢɪɴᴀᴛᴇᴅ)
├ `/queue remove <n>` — ❌ ʀᴇᴍᴏᴠᴇ ᴛʀᴀᴄᴋ
└ `/queue swap <a> <b>` — 🔄 sᴡᴀᴘ ᴛʀᴀᴄᴋs

**ᴘᴇʀsᴏɴᴀʟ:**
├ `/like` — ❤️ ʟɪᴋᴇ ᴄᴜʀʀᴇɴᴛ sᴏɴɢ
├ `/favourite` — 💕 ᴠɪᴇᴡ ꜰᴀᴠᴏᴜʀɪᴛᴇs
├ `/history` — 📜 ᴘʟᴀʏ ʜɪsᴛᴏʀʏ
└ `/lyrics [name]` — 📝 ꜰɪɴᴅ ʟʏʀɪᴄs

**ᴘʟᴀʏʟɪsᴛs:**
├ `/playlist` — ᴠɪᴇᴡ ᴀʟʟ ᴘʟᴀʏʟɪsᴛs
├ `/playlist create <name>` — ᴄʀᴇᴀᴛᴇ
├ `/playlist add <name>` — ᴀᴅᴅ ᴄᴜʀʀᴇɴᴛ sᴏɴɢ
├ `/playlist play <name>` — ᴘʟᴀʏ ᴀʟʟ
└ `/playlist delete <name>` — ᴅᴇʟᴇᴛᴇ"""

ADMIN_HELP = """👮 **ᴀᴅᴍɪɴ & ᴍᴏᴅᴇʀᴀᴛɪᴏɴ**

**ᴜsᴇʀ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ:**
├ `/auth` — ✅ ᴀᴜᴛʜᴏʀɪsᴇ ᴜsᴇʀ (ʀᴇᴘʟʏ)
├ `/unauth` — ❌ ᴜɴᴀᴜᴛʜᴏʀɪsᴇ (ʀᴇᴘʟʏ)
├ `/authusers` — 👥 ʟɪsᴛ ᴀᴜᴛʜ ᴜsᴇʀs
├ `/block` — 🚫 ʙʟᴏᴄᴋ ᴜsᴇʀ
└ `/unblock` — ✅ ᴜɴʙʟᴏᴄᴋ

**ɢʀᴏᴜᴘ:**
├ `/settings` — ⚙️ ɢʀᴏᴜᴘ sᴇᴛᴛɪɴɢs ᴘᴀɴᴇʟ
├ `/chatinfo` — 📊 ɢʀᴏᴜᴘ ɪɴꜰᴏ
├ `/joinvc` / `/leavevc` — 🎙 ᴠᴄ ᴄᴏɴᴛʀᴏʟ
└ `/vcinfo` — 📡 ᴠᴄ sᴛᴀᴛᴜs

**sᴜᴅᴏ (ᴏᴡɴᴇʀ):**
├ `/addsudo` / `/delsudo` — 👑 sᴜᴅᴏ
├ `/broadcast` / `/gcast` — 📢 ʙʀᴏᴀᴅᴄᴀsᴛ
├ `/restart` — 🔄 ʀᴇsᴛᴀʀᴛ
├ `/logs` — 📋 ɢᴇᴛ ʟᴏɢs
├ `/maintenance` — 🛠 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ
└ `/globalstats` — 📊 ɢʟᴏʙᴀʟ sᴛᴀᴛs"""

ABOUT_TEXT = """🌟 **ᴀʙᴏᴜᴛ {bot_name}**

**ᴠᴇʀsɪᴏɴ:** `{version}`
**ꜰʀᴀᴍᴇᴡᴏʀᴋ:** Pyrogram + PyTgCalls
**ʟᴀɴɢᴜᴀɢᴇ:** Python 3.11+
**ᴅᴀᴛᴀʙᴀsᴇ:** MongoDB (ᴡɪᴛʜ ɪɴ-ᴍᴇᴍᴏʀʏ ꜰᴀʟʟʙᴀᴄᴋ)

📊 **ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs:**
├ 🎵 ᴀᴄᴛɪᴠᴇ sᴛʀᴇᴀᴍs: `{active}`
├ 🎶 ᴛᴏᴛᴀʟ ᴘʟᴀʏᴇᴅ: `{played}`
├ 👥 ɢʀᴏᴜᴘs: `{groups}`
└ ⏱ ᴜᴘᴛɪᴍᴇ: `{uptime}`

**50+ ᴄᴏᴍᴍᴀɴᴅs │ 6 ᴍᴜsɪᴄ sᴏᴜʀᴄᴇs │ 5 ᴀᴜᴅɪᴏ ᴇꜰꜰᴇᴄᴛs**

👑 **ᴅᴇᴠᴇʟᴏᴘᴇᴅ ᴡɪᴛʜ ❤️ ʙʏ @its_me_secret**"""


# ═══════════════════════════════════════════════════════════════
# BUTTON LAYOUTS
# ═══════════════════════════════════════════════════════════════

def start_markup(username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕", url=f"https://t.me/{username}?startgroup=true")],
        [
            InlineKeyboardButton("🎵 ᴘʟᴀʏ", callback_data="help_play"),
            InlineKeyboardButton("🎮 ᴄᴏɴᴛʀᴏʟs", callback_data="help_controls"),
            InlineKeyboardButton("🎛 ᴇꜰꜰᴇᴄᴛs", callback_data="help_effects"),
        ],
        [
            InlineKeyboardButton("📜 ǫᴜᴇᴜᴇ", callback_data="help_queue"),
            InlineKeyboardButton("👮 ᴀᴅᴍɪɴ", callback_data="help_admin"),
            InlineKeyboardButton("🌟 ᴀʙᴏᴜᴛ", callback_data="help_about"),
        ],
        [
            InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇs", url="https://t.me/SecretzBots"),
            InlineKeyboardButton("🛠 sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT),
        ],
        [InlineKeyboardButton("👑 ᴏᴡɴᴇʀ 👑", url=f"tg://user?id={config.OWNER_ID}")],
    ])


def back_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="start")],
    ])


def help_nav_markup(current: str) -> InlineKeyboardMarkup:
    """Navigation buttons for help pages — shows adjacent pages."""
    pages = ["help_play", "help_controls", "help_effects", "help_queue", "help_admin"]
    labels = ["🎵 ᴘʟᴀʏ", "🎮 ᴄᴏɴᴛʀᴏʟs", "🎛 ᴇꜰꜰᴇᴄᴛs", "📜 ǫᴜᴇᴜᴇ", "👮 ᴀᴅᴍɪɴ"]
    idx = pages.index(current) if current in pages else 0
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton(f"◀️ {labels[idx-1]}", callback_data=pages[idx-1]))
    if idx < len(pages) - 1:
        nav.append(InlineKeyboardButton(f"{labels[idx+1]} ▶️", callback_data=pages[idx+1]))
    rows = []
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="start")])
    return InlineKeyboardMarkup(rows)


# ═══════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(_, message):
    me = await bot.get_me()
    text = START_TEXT.format(bot_name=config.BOT_NAME, version=config.BOT_VERSION)
    try:
        await message.reply_photo(START_IMG, caption=text, reply_markup=start_markup(me.username))
    except Exception:
        await message.reply_text(text, reply_markup=start_markup(me.username), disable_web_page_preview=True)


@bot.on_message(filters.command("help"))
async def help_handler(_, message):
    me = await bot.get_me()
    text = START_TEXT.format(bot_name=config.BOT_NAME, version=config.BOT_VERSION)
    try:
        await message.reply_photo(START_IMG, caption=text, reply_markup=start_markup(me.username))
    except Exception:
        await message.reply_text(text, reply_markup=start_markup(me.username), disable_web_page_preview=True)


@bot.on_callback_query(filters.regex("^help_play$"))
async def help_play_cb(_, query: CallbackQuery):
    try:
        await query.edit_message_caption(caption=PLAY_HELP, reply_markup=help_nav_markup("help_play"))
    except Exception:
        await query.edit_message_text(PLAY_HELP, reply_markup=help_nav_markup("help_play"))

@bot.on_callback_query(filters.regex("^help_controls$"))
async def help_controls_cb(_, query: CallbackQuery):
    try:
        await query.edit_message_caption(caption=CONTROL_HELP, reply_markup=help_nav_markup("help_controls"))
    except Exception:
        await query.edit_message_text(CONTROL_HELP, reply_markup=help_nav_markup("help_controls"))

@bot.on_callback_query(filters.regex("^help_effects$"))
async def help_effects_cb(_, query: CallbackQuery):
    try:
        await query.edit_message_caption(caption=EFFECTS_HELP, reply_markup=help_nav_markup("help_effects"))
    except Exception:
        await query.edit_message_text(EFFECTS_HELP, reply_markup=help_nav_markup("help_effects"))

@bot.on_callback_query(filters.regex("^help_queue$"))
async def help_queue_cb(_, query: CallbackQuery):
    try:
        await query.edit_message_caption(caption=QUEUE_HELP, reply_markup=help_nav_markup("help_queue"))
    except Exception:
        await query.edit_message_text(QUEUE_HELP, reply_markup=help_nav_markup("help_queue"))

@bot.on_callback_query(filters.regex("^help_admin$"))
async def help_admin_cb(_, query: CallbackQuery):
    try:
        await query.edit_message_caption(caption=ADMIN_HELP, reply_markup=help_nav_markup("help_admin"))
    except Exception:
        await query.edit_message_text(ADMIN_HELP, reply_markup=help_nav_markup("help_admin"))

@bot.on_callback_query(filters.regex("^help_about$"))
async def help_about_cb(_, query: CallbackQuery):
    stats = queue_manager.get_stats()
    groups = await db.get_group_count()
    uptime = get_readable_time(int(time.time() - bot_client.start_time)) if bot_client.start_time else "N/A"
    text = ABOUT_TEXT.format(
        bot_name=config.BOT_NAME, version=config.BOT_VERSION,
        active=stats["active_chats"], played=stats["total_played"],
        groups=groups, uptime=uptime,
    )
    try:
        await query.edit_message_caption(caption=text, reply_markup=back_markup())
    except Exception:
        await query.edit_message_text(text, reply_markup=back_markup())

@bot.on_callback_query(filters.regex("^start$"))
async def back_cb(_, query: CallbackQuery):
    me = await bot.get_me()
    text = START_TEXT.format(bot_name=config.BOT_NAME, version=config.BOT_VERSION)
    try:
        await query.edit_message_caption(caption=text, reply_markup=start_markup(me.username))
    except Exception:
        await query.edit_message_text(text, reply_markup=start_markup(me.username))

@bot.on_callback_query(filters.regex("^settings$"))
async def settings_redirect_cb(_, query: CallbackQuery):
    await query.answer("ᴜsᴇ /settings ɪɴ ᴀ ɢʀᴏᴜᴘ!", show_alert=True)