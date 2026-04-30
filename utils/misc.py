"""Miscellaneous utility functions."""

import asyncio
from pyrogram.types import Message


async def auto_delete(message: Message, delay: int = 60):
    """Delete a message after a delay."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


async def edit_or_reply(message: Message, text: str, **kwargs):
    """Edit the message if possible, otherwise reply."""
    try:
        return await message.edit_text(text, **kwargs)
    except Exception:
        try:
            return await message.reply_text(text, **kwargs)
        except Exception:
            pass
