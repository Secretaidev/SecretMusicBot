from pyrogram import filters, enums
from pyrogram.types import Message, ChatPrivileges
from client.client import bot_client
import config

bot = bot_client.bot
user = bot_client.user

async def promote_assistant(chat_id: int):
    if not user:
        return
    try:
        # Check if bot has permission to promote
        me = await bot.get_chat_member(chat_id, bot.me.id)
        if me.privileges and me.privileges.can_promote_members:
            await bot.promote_chat_member(
                chat_id,
                user.me.id,
                privileges=ChatPrivileges(
                    can_change_info=False,
                    can_invite_users=True,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_promote_members=False,
                    can_manage_chat=True,
                    can_manage_video_chats=True,
                )
            )
            return True
    except Exception as e:
        print(f"[Assistant Promote Error] {e}")
    return False

@bot.on_message(filters.new_chat_members)
async def on_bot_added(_, message: Message):
    if not message.new_chat_members:
        return
    
    for member in message.new_chat_members:
        if member.id == bot.me.id:
            # Bot was added
            chat_id = message.chat.id
            # Check permissions
            me = await bot.get_chat_member(chat_id, bot.me.id)
            if not (me.privileges and me.privileges.can_delete_messages and me.privileges.can_invite_users):
                await message.reply_text(
                    "❌ **ɪ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ꜰᴜɴᴄᴛɪᴏɴ ᴘʀᴏᴘᴇʀʟʏ!**\n\n"
                    "ᴘʟᴇᴀsᴇ ɢɪᴠᴇ ᴍᴇ:\n"
                    "• ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs\n"
                    "• ɪɴᴠɪᴛᴇ ᴜsᴇʀs\n"
                    "• ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs"
                )
            
            # Try to promote assistant
            success = await promote_assistant(chat_id)
            if success:
                await message.reply_text("✅ **ᴀssɪsᴛᴀɴᴛ ɪᴅ ʜᴀs ʙᴇᴇɴ ᴘʀᴏᴍᴏᴛᴇᴅ ᴛᴏ ᴀᴅᴍɪɴ.**")
            
            # Log to channel
            if config.LOG_CHANNEL != 0:
                try:
                    await bot.send_message(
                        config.LOG_CHANNEL,
                        f"🆕 **ɴᴇᴡ ɢʀᴏᴜᴘ ᴀᴅᴅᴇᴅ**\n\n"
                        f"**ᴄʜᴀᴛ:** {message.chat.title} (`{chat_id}`)\n"
                        f"**ᴀᴅᴅᴇᴅ ʙʏ:** {message.from_user.mention}"
                    )
                except Exception:
                    pass

async def assistant_join(chat_id: int, invite_link: str = None):
    if not user:
        return
    try:
        await user.join_chat(chat_id)
    except Exception:
        if invite_link:
            try:
                await user.join_chat(invite_link)
            except Exception:
                pass
        else:
            # Try to generate invite link if bot is admin
            try:
                link = await bot.export_chat_invite_link(chat_id)
                await user.join_chat(link)
            except Exception:
                pass
