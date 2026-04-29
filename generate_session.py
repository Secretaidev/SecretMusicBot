"""Utility to generate a Pyrogram StringSession for the assistant."""

import asyncio
from pyrogram import Client


def ask(prompt: str) -> str:
    return input(prompt)


async def generate():
    print("=" * 50)
    print("   Pyrogram Session String Generator")
    print("=" * 50)
    api_id = int(ask("Enter API_ID: "))
    api_hash = ask("Enter API_HASH: ")

    client = Client("gen_session", api_id=api_id, api_hash=api_hash, in_memory=True)
    await client.start()
    session = await client.export_session_string()
    print("\n" + "=" * 50)
    print("Your SESSION_STRING:\n")
    print(session)
    print("=" * 50)
    print("\nCopy the string above into your .env or config.py")
    await client.stop()


if __name__ == "__main__":
    asyncio.run(generate())
