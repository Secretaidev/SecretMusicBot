"""Centralised configuration for the Music Bot.
Read values from environment variables (recommended) or fill them below.
Never commit real credentials to version control.
"""

import os

# ── Bot Identity ──────────────────────────────────────────────
BOT_NAME = os.getenv("BOT_NAME", "Secret Music Bot")
BOT_VERSION = "3.0.0"

# ── Required Telegram credentials ──────────────────────────────
API_ID = int(os.getenv("API_ID", "0"))          # Get from my.telegram.org
API_HASH = os.getenv("API_HASH", "")            # Get from my.telegram.org
BOT_TOKEN = os.getenv("BOT_TOKEN", "")          # Get from @BotFather

# ── User Account (Assistant) ─────────────────────────────────
# A Pyrogram StringSession for the assistant account so it can join VCs.
SESSION_STRING = os.getenv("SESSION_STRING", "")
ASSISTANT_USERNAME = os.getenv("ASSISTANT_USERNAME", "")  # Without @

# ── Spotify Integration ──────────────────────────────────────
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

# ── Queue & Playback ─────────────────────────────────────────
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "300"))
MAX_DOWNLOAD_SIZE_MB = int(os.getenv("MAX_DOWNLOAD_SIZE_MB", "500"))
MAX_PLAYLIST_SIZE = int(os.getenv("MAX_PLAYLIST_SIZE", "50"))
DEFAULT_QUALITY = os.getenv("DEFAULT_QUALITY", "192")  # 128, 192, 320
AUTO_LEAVE_TIMEOUT = int(os.getenv("AUTO_LEAVE_TIMEOUT", "120"))  # seconds

# ── Lyrics ────────────────────────────────────────────────────
LYRICS_API = os.getenv("LYRICS_API", "https://lyrics-api-mu.vercel.app")

# ── Database & Logs ──────────────────────────────────────────
MONGO_DB_URI = os.getenv("MONGO_DB_URI", "")     # MongoDB connection string
LOG_GROUP = int(os.getenv("LOG_GROUP", "0"))      # optional log channel
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))  # Private logs channel

# ── Access Control ───────────────────────────────────────────
MUST_JOIN = os.getenv("MUST_JOIN", "")            # Channel username for force join
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/SupportGroup")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split())) if os.getenv("SUDO_USERS") else []
if OWNER_ID not in SUDO_USERS:
    SUDO_USERS.append(OWNER_ID)

# ── Directories (auto-created at runtime) ─────────────────────
DOWNLOADS_DIR = "downloads"
THUMB_DIR = "thumbnails"
LOGS_DIR = "logs"

# ── Radio Station Presets ────────────────────────────────────
RADIO_STATIONS = {
    "lofi": {
        "name": "🎵 Lofi Hip Hop Radio",
        "url": "https://streams.ilovemusic.de/iloveradio17.mp3",
    },
    "chillhop": {
        "name": "☕ Chillhop Radio",
        "url": "https://streams.fluxfm.de/Chillhop/mp3-320",
    },
    "jazz": {
        "name": "🎷 Smooth Jazz Radio",
        "url": "https://strm112.1.fm/ajazz_mobile_mp3",
    },
    "classical": {
        "name": "🎻 Classical Radio",
        "url": "https://stream.srg-ssr.ch/m/rsc_de/mp3_128",
    },
    "pop": {
        "name": "🎤 Pop Hits Radio",
        "url": "https://strm112.1.fm/top40_mobile_mp3",
    },
    "rock": {
        "name": "🎸 Rock Radio",
        "url": "https://strm112.1.fm/rock_mobile_mp3",
    },
    "bollywood": {
        "name": "🇮🇳 Bollywood Radio",
        "url": "https://strm112.1.fm/hit70_mobile_mp3",
    },
    "edm": {
        "name": "⚡ EDM Radio",
        "url": "https://strm112.1.fm/electronicadance_mobile_mp3",
    },
}
