"""Assistant handler — manages the assistant user joining/leaving chats."""

from pyrogram import filters, enums
from pyrogram.types import Message, ChatPrivileges
from client.client import bot_client
from utils.database import db
from utils.logger import get_logger
import config

log = get_logger("Assistant")
bot = bot_client.bot
user = bot_client.user


async def promote_assistant(chat_id: int) -> bool:
    if not user:
        return False
    try:
        me = await bot.get_chat_member(chat_id, bot.me.id)
        if me.privileges and me.privileges.can_promote_members:
            await bot.promote_chat_member(
                chat_id, user.me.id,
                privileges=ChatPrivileges(
                    can_change_info=False, can_invite_users=True,
                    can_delete_messages=True, can_restrict_members=False,
                    can_pin_messages=True, can_promote_members=False,
                    can_manage_chat=True, can_manage_video_chats=True,
                ),
            )
            return True
    except Exception as e:
        log.warning(f"Promote error in {chat_id}: {e}")
    return False


async def assistant_join(chat_id: int, invite_link: str = None):
    if not user:
        return
    try:
        await user.get_chat_member(chat_id, user.me.id)
        return
    except Exception:
        pass
    try:
        await user.join_chat(chat_id)
        return
    except Exception:
        pass
    if invite_link:
        try:
            await user.join_chat(invite_link)
            return
        except Exception:
            pass
    try:
        link = await bot.export_chat_invite_link(chat_id)
        await user.join_chat(link)
    except Exception as e:
        log.error(f"All join methods failed for {chat_id}: {e}")


@bot.on_message(filters.new_chat_members)
async def on_bot_added(_, message: Message):
    if not message.new_chat_members:
        return
    for member in message.new_chat_members:
        if member.id == bot.me.id:
            chat_id = message.chat.id
            await db.add_group(chat_id)
            try:
                me = await bot.get_chat_member(chat_id, bot.me.id)
                if not (me.privileges and me.privileges.can_delete_messages):
                    await message.reply_text(
                        "⚠️ **ɪ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs!**\n\n"
                        "• ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs\n• ɪɴᴠɪᴛᴇ ᴜsᴇʀs\n"
                        "• ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs\n• ᴘʀᴏᴍᴏᴛᴇ ᴍᴇᴍʙᴇʀs"
                    )
            except Exception:
                pass
            if user:
                success = await promote_assistant(chat_id)
                if success:
                    await message.reply_text("✅ **ᴀssɪsᴛᴀɴᴛ ᴀᴜᴛᴏ-ᴘʀᴏᴍᴏᴛᴇᴅ!** 🎶 /play ᴛᴏ sᴛᴀʀᴛ!")
            if config.LOG_CHANNEL != 0:
                try:
                    c = await db.get_group_count()
                    await bot.send_message(config.LOG_CHANNEL,
                        f"🆕 **ɴᴇᴡ ɢʀᴏᴜᴘ**\n📌 {message.chat.title}\n"
                        f"🆔 `{chat_id}`\n👤 {message.from_user.mention}\n📊 ᴛᴏᴛᴀʟ: `{c}`")
                except Exception:
                    pass
