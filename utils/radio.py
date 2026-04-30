"""Radio streaming support with preset stations and custom URLs."""

from typing import Optional, Dict, List
from config import RADIO_STATIONS
from utils.logger import get_logger

log = get_logger("Radio")


class RadioManager:
    """Manage radio station presets and custom streams."""

    @staticmethod
    def get_stations() -> Dict[str, dict]:
        """Return all available preset radio stations."""
        return RADIO_STATIONS

    @staticmethod
    def get_station(name: str) -> Optional[dict]:
        """Get a preset station by key name."""
        return RADIO_STATIONS.get(name.lower())

    @staticmethod
    def get_station_list() -> List[dict]:
        """Get list of all stations with their keys."""
        return [
            {"key": k, **v} for k, v in RADIO_STATIONS.items()
        ]

    @staticmethod
    def is_valid_stream_url(url: str) -> bool:
        """Basic validation for stream URLs."""
        return url.startswith(("http://", "https://")) and any(
            ext in url.lower() for ext in [".mp3", ".aac", ".ogg", ".m3u", ".pls", "/stream", "/live"]
        ) or url.startswith(("http://", "https://"))  # Allow any URL as radio

    @staticmethod
    def format_station_list() -> str:
        """Format station list for display."""
        text = "📻 **ᴀᴠᴀɪʟᴀʙʟᴇ ʀᴀᴅɪᴏ sᴛᴀᴛɪᴏɴs**\n\n"
        for key, station in RADIO_STATIONS.items():
            text += f"├ {station['name']} — `/radio {key}`\n"
        text += "\n💡 **ᴄᴜsᴛᴏᴍ:** `/radio <stream_url>`"
        return text
