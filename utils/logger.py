"""Structured logging for the music bot with file rotation and optional Telegram channel logging."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import LOGS_DIR

os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Root logger configuration ───────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            os.path.join(LOGS_DIR, "bot.log"),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)

# Suppress noisy loggers but keep pyrogram at INFO for debugging
logging.getLogger("pyrogram").setLevel(logging.INFO)
logging.getLogger("pyrogram.session").setLevel(logging.WARNING)
logging.getLogger("pytgcalls").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""
    return logging.getLogger(name)


LOGGER = get_logger("SecretMusic")
