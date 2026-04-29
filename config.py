"""Centralised configuration for the Music Bot.
Read values from environment variables (recommended) or fill them below.
Never commit real credentials to version control.
"""

import os

# ── Required Telegram credentials ──────────────────────────────
API_ID = int(os.getenv("API_ID", "0"))          # Get from my.telegram.org
API_HASH = os.getenv("API_HASH", "")            # Get from my.telegram.org
BOT_TOKEN = os.getenv("BOT_TOKEN", "")          # Get from @BotFather

# ── User Account (Assistant) ─────────────────────────────────
# A Pyrogram StringSession for the assistant account so it can join VCs.
SESSION_STRING = os.getenv("SESSION_STRING", "")
ASSISTANT_USERNAME = os.getenv("ASSISTANT_USERNAME", "")  # Without @

# ── Misc ─────────────────────────────────────────────────────
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "300"))
MAX_DOWNLOAD_SIZE_MB = int(os.getenv("MAX_DOWNLOAD_SIZE_MB", "500"))
LANGUAGE = os.getenv("LANGUAGE", "en")          # i18n stub
LOG_GROUP = int(os.getenv("LOG_GROUP", "0"))    # optional log channel
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0")) # Private logs channel
MONGO_DB_URI = os.getenv("MONGO_DB_URI", "")     # MongoDB connection string
MUST_JOIN = os.getenv("MUST_JOIN", "")           # Channel username for force join
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/SupportGroup")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789")) # Replace with your real Owner ID
SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split())) if os.getenv("SUDO_USERS") else []
SUDO_USERS.append(OWNER_ID)

# Directories (auto-created at runtime)
DOWNLOADS_DIR = "downloads"
THUMB_DIR = "thumbnails"
