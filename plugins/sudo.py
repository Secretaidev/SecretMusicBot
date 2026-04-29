import os
import sys
import asyncio
from pyrogram import filters
from client.client import bot_client
from utils.database import db
import config

bot = bot_client.bot

@bot.on_message(filters.command("restart"))
async def restart_bot(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return
    
    await message.reply_text("🔄 **ʀᴇsᴛᴀʀᴛɪɴɢ ʙᴏᴛ… ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("logs"))
async def get_logs(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return
    
    # This is a simplified log retrieval. In a real environment, you'd read from a file.
    # For now, we'll just acknowledge the command.
    await message.reply_text("📋 **ʟᴏɢs feature is under optimization.**")

@bot.on_message(filters.command("gcast"))
async def gcast_cmd(_, message):
    sudoers = await db.get_sudoers()
    if message.from_user.id not in sudoers:
        return
    
    if not message.reply_to_message:
        return await message.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀsᴛ.")
    
    m = await message.reply_text("📢 **ɢʟᴏʙᴀʟ ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ…**")
    count = 0
    chats = []
    async for dialog in bot.get_dialogs():
        chats.append(dialog.chat.id)
    
    for chat_id in chats:
        try:
            await message.reply_to_message.forward(chat_id)
            count += 1
            await asyncio.sleep(0.3) # Avoid flood
        except Exception:
            pass
    
    await m.edit(f"✅ **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ.**\n✨ **sᴇɴᴛ ᴛᴏ `{count}` ᴄʜᴀᴛs.**")
