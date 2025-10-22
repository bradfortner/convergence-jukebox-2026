"""
Queue Manager - Manages song queue and playback order
"""

from typing import Optional, List, Dict, Any
from collections import deque


class QueueManager:
    """Manages the song queue and playback order"""

    def __init__(self, max_queue_size: int = 100):
        """Initialize queue manager"""
        self.queue: deque = deque(maxlen=max_queue_size)
        self.current_index = 0
        self.repeat_mode = "off"  # off, one, all
        self.shuffle = False
        self.history: deque = deque(maxlen=50)  # Last 50 played songs

    def add_song(self, song: Dict[str, Any]) -> bool:
        """Add song to queue"""
        try:
            self.queue.append(song)
            return True
        except Exception as e:
            print(f"Error adding song to queue: {e}")
            return False

    def add_multiple_songs(self, songs: List[Dict[str, Any]]) -> int:
        """Add multiple songs to queue"""
        count = 0
        for song in songs:
            if self.add_song(song):
                count += 1
        return count

    def remove_song(self, index: int) -> bool:
        """Remove song from queue by index"""
        if not (0 <= index < len(self.queue)):
            return False

        try:
            # Convert deque to list, remove, convert back
            songs = list(self.queue)
            songs.pop(index)
            self.queue.clear()
            self.queue.extend(songs)

            # Adjust current index if needed
            if self.current_index >= len(self.queue):
                self.current_index = max(0, len(self.queue) - 1)

            return True
        except Exception as e:
            print(f"Error removing song: {e}")
            return False

    def get_current_song(self) -> Optional[Dict[str, Any]]:
        """Get currently playing song"""
        if self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    def get_next_song(self) -> Optional[Dict[str, Any]]:
        """Get next song in queue"""
        if self.current_index + 1 < len(self.queue):
            return self.queue[self.current_index + 1]

        # Handle repeat modes
        if self.repeat_mode == "all" and len(self.queue) > 0:
            return self.queue[0]

        return None

    def advance_to_next(self) -> Optional[Dict[str, Any]]:
        """Advance to next song"""
        current = self.get_current_song()
        if current:
            self.history.append(current)

        if self.current_index + 1 < len(self.queue):
            self.current_index += 1
            return self.get_current_song()

        # Handle repeat modes
        if self.repeat_mode == "all" and len(self.queue) > 0:
            self.current_index = 0
            return self.get_current_song()

        return None

    def go_to_previous(self) -> Optional[Dict[str, Any]]:
        """Go to previous song"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.get_current_song()

        return None

    def skip_to_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Skip to song at index"""
        if 0 <= index < len(self.queue):
            self.current_index = index
            return self.get_current_song()
        return None

    def clear_queue(self):
        """Clear the queue"""
        self.queue.clear()
        self.current_index = 0

    def get_queue(self) -> List[Dict[str, Any]]:
        """Get full queue"""
        return list(self.queue)

    def get_queue_size(self) -> int:
        """Get number of songs in queue"""
        return len(self.queue)

    def get_upcoming(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get next N songs"""
        upcoming = []
        for i in range(self.current_index + 1, min(self.current_index + 1 + count, len(self.queue))):
            upcoming.append(self.queue[i])
        return upcoming

    def get_queue_display_names(self, count: int = 10) -> List[str]:
        """Get display names of next N songs"""
        names = []
        for song in self.get_upcoming(count):
            title = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown')
            names.append(f"{artist} - {title}")
        return names

    def set_repeat_mode(self, mode: str):
        """Set repeat mode (off, one, all)"""
        if mode in ["off", "one", "all"]:
            self.repeat_mode = mode

    def get_repeat_mode(self) -> str:
        """Get current repeat mode"""
        return self.repeat_mode

    def toggle_repeat_mode(self) -> str:
        """Toggle repeat mode"""
        modes = ["off", "one", "all"]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        return self.repeat_mode

    def set_shuffle(self, enabled: bool):
        """Enable/disable shuffle"""
        self.shuffle = enabled

    def is_shuffle_enabled(self) -> bool:
        """Check if shuffle is enabled"""
        return self.shuffle

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle"""
        self.shuffle = not self.shuffle
        return self.shuffle

    def get_history(self) -> List[Dict[str, Any]]:
        """Get play history"""
        return list(self.history)

    def get_status(self) -> dict:
        """Get queue status"""
        return {
            'queue_size': len(self.queue),
            'current_index': self.current_index,
            'current_song': self.get_current_song(),
            'repeat_mode': self.repeat_mode,
            'shuffle': self.shuffle,
            'upcoming_count': max(0, len(self.queue) - self.current_index - 1)
        }

    def is_queue_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.queue) == 0

    def is_at_end(self) -> bool:
        """Check if at end of queue"""
        return self.current_index >= len(self.queue) - 1
