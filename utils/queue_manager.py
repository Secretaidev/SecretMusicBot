"""Per-chat queue & playback state manager."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import MAX_QUEUE_SIZE


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


@dataclass
class ChatState:
    queue: List[Track] = field(default_factory=list)
    current: Optional[Track] = None
    is_playing: bool = False
    loop: bool = False
    volume: int = 100                # stub for volume logic
    message_id: Optional[int] = None # current now-playing message


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

    def pop(self, chat_id: int) -> Optional[Track]:
        state = self.get(chat_id)
        if state.loop and state.current:
            return state.current
        if state.queue:
            state.current = state.queue.pop(0)
            return state.current
        state.current = None
        return None

    def remove(self, chat_id: int, index: int) -> bool:
        state = self.get(chat_id)
        if 0 <= index < len(state.queue):
            state.queue.pop(index)
            return True
        return False

    def clear(self, chat_id: int) -> int:
        state = self.get(chat_id)
        count = len(state.queue)
        for t in state.queue:
            _safe_remove(t.file_path)
            _safe_remove(t.thumb_path)
        state.queue.clear()
        state.loop = False
        state.is_playing = False
        state.current = None
        return count

    def now_playing(self, chat_id: int) -> Optional[Track]:
        return self.get(chat_id).current


queue_manager = QueueManager()


def _safe_remove(path: Optional[str]) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
