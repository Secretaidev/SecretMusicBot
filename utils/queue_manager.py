"""Per-chat queue & playback state manager — advanced edition.

Supports shuffle, history, autoplay, seek tracking, speed control,
equalizer presets, move/swap operations, and statistics.
"""

import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import MAX_QUEUE_SIZE
from utils.logger import get_logger

log = get_logger("QueueManager")


@dataclass
class Track:
    id: str
    title: str
    duration: Optional[int]        # seconds
    uploader: Optional[str]
    url: str
    file_path: Optional[str] = None
    thumb_path: Optional[str] = None
    requested_by: Optional[int] = None
    is_video: bool = False
    source: str = "youtube"        # youtube, jiosaavn, spotify, soundcloud, radio, file


@dataclass
class ChatState:
    queue: List[Track] = field(default_factory=list)
    current: Optional[Track] = None
    is_playing: bool = False
    is_paused: bool = False
    loop: bool = False
    loop_all: bool = False         # Loop entire queue
    shuffle: bool = False
    autoplay: bool = False
    volume: int = 100
    speed: float = 1.0             # 0.5 – 2.0
    bass_boost: bool = False
    nightcore: bool = False
    vaporwave: bool = False
    eight_d: bool = False
    message_id: Optional[int] = None  # current now-playing message
    history: List[Track] = field(default_factory=list)
    played_count: int = 0
    total_duration: int = 0        # total seconds played
    is_radio: bool = False         # currently streaming radio


class QueueManager:
    """Manages in-memory state for every chat."""

    def __init__(self):
        self._states: Dict[int, ChatState] = {}

    def get(self, chat_id: int) -> ChatState:
        if chat_id not in self._states:
            self._states[chat_id] = ChatState()
        return self._states[chat_id]

    def add(self, chat_id: int, track: Track) -> bool:
        state = self.get(chat_id)
        if len(state.queue) >= MAX_QUEUE_SIZE:
            return False
        state.queue.append(track)
        return True

    def add_next(self, chat_id: int, track: Track) -> bool:
        """Insert track at position 0 (play next)."""
        state = self.get(chat_id)
        if len(state.queue) >= MAX_QUEUE_SIZE:
            return False
        state.queue.insert(0, track)
        return True

    def pop(self, chat_id: int) -> Optional[Track]:
        state = self.get(chat_id)

        # Loop current track
        if state.loop and state.current:
            return state.current

        # Move current to history
        if state.current:
            state.history.append(state.current)
            state.played_count += 1
            if state.current.duration:
                state.total_duration += state.current.duration
            # Keep history size manageable
            if len(state.history) > 50:
                state.history = state.history[-50:]

        # Loop all: re-add current to end
        if state.loop_all and state.current:
            state.queue.append(state.current)

        if state.queue:
            if state.shuffle:
                idx = random.randint(0, len(state.queue) - 1)
                state.current = state.queue.pop(idx)
            else:
                state.current = state.queue.pop(0)
            return state.current

        state.current = None
        return None

    def remove(self, chat_id: int, index: int) -> Optional[Track]:
        state = self.get(chat_id)
        if 0 <= index < len(state.queue):
            removed = state.queue.pop(index)
            _safe_remove(removed.file_path)
            _safe_remove(removed.thumb_path)
            return removed
        return None

    def move(self, chat_id: int, from_idx: int, to_idx: int) -> bool:
        """Move a track from one position to another."""
        state = self.get(chat_id)
        if 0 <= from_idx < len(state.queue) and 0 <= to_idx < len(state.queue):
            track = state.queue.pop(from_idx)
            state.queue.insert(to_idx, track)
            return True
        return False

    def swap(self, chat_id: int, idx_a: int, idx_b: int) -> bool:
        """Swap two tracks in the queue."""
        state = self.get(chat_id)
        if 0 <= idx_a < len(state.queue) and 0 <= idx_b < len(state.queue):
            state.queue[idx_a], state.queue[idx_b] = state.queue[idx_b], state.queue[idx_a]
            return True
        return False

    def shuffle_queue(self, chat_id: int) -> int:
        """Shuffle the queue. Returns number of tracks shuffled."""
        state = self.get(chat_id)
        count = len(state.queue)
        if count > 1:
            random.shuffle(state.queue)
        return count

    def remove_duplicates(self, chat_id: int) -> int:
        """Remove duplicate tracks from queue. Returns count removed."""
        state = self.get(chat_id)
        seen = set()
        new_queue = []
        removed = 0
        for track in state.queue:
            if track.id not in seen:
                seen.add(track.id)
                new_queue.append(track)
            else:
                _safe_remove(track.file_path)
                _safe_remove(track.thumb_path)
                removed += 1
        state.queue = new_queue
        return removed

    def clear(self, chat_id: int) -> int:
        state = self.get(chat_id)
        count = len(state.queue)
        for t in state.queue:
            _safe_remove(t.file_path)
            _safe_remove(t.thumb_path)
        state.queue.clear()
        state.loop = False
        state.loop_all = False
        state.is_playing = False
        state.is_paused = False
        state.is_radio = False
        state.current = None
        state.bass_boost = False
        state.nightcore = False
        state.vaporwave = False
        state.eight_d = False
        state.speed = 1.0
        return count

    def now_playing(self, chat_id: int) -> Optional[Track]:
        return self.get(chat_id).current

    def get_active_chats(self) -> List[int]:
        """Return list of chat IDs with active playback."""
        return [cid for cid, state in self._states.items() if state.is_playing]

    def get_stats(self) -> dict:
        """Return global bot statistics."""
        active = len(self.get_active_chats())
        total_queued = sum(len(s.queue) for s in self._states.values())
        total_played = sum(s.played_count for s in self._states.values())
        return {
            "active_chats": active,
            "total_chats": len(self._states),
            "total_queued": total_queued,
            "total_played": total_played,
        }


queue_manager = QueueManager()


def _safe_remove(path: Optional[str]) -> None:
    if path and not path.startswith("http") and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
