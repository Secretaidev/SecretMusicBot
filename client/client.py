"""Pyrogram bot + user client initialisation with PyTgCalls."""

import asyncio
import os
from pyrogram import Client
from pytgcalls import PyTgCalls

import config


class BotClient:
    def __init__(self):
        self.bot = Client(
            "music_bot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
        )
        self.user = None
        self.call = None
        if config.SESSION_STRING:
            self.user = Client(
                "music_assistant",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=config.SESSION_STRING,
                in_memory=True,
            )
            self.call = PyTgCalls(self.user)

    async def start(self):
        await self.bot.start()
        print(f"[Bot] @{self.bot.me.username} started.")
        if self.user:
            await self.user.start()
            await self.call.start()
            print(f"[Assistant] @{self.user.me.username or self.user.me.id} started.")

    async def stop(self):
        await self.bot.stop()
        if self.user:
            await self.call.stop()
            await self.user.stop()

    def __call__(self):
        return self.bot


bot_client = BotClient()
