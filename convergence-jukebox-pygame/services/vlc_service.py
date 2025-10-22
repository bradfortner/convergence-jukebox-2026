"""
VLC Service - Audio playback using VLC media player
"""

import os
from typing import Optional, Callable
import config

# Try to import python-vlc, fall back to None if not available
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False


class VLCService:
    """Service for audio playback using VLC"""

    def __init__(self):
        """Initialize VLC service"""
        self.vlc_available = VLC_AVAILABLE
        self.instance: Optional[vlc.Instance] = None
        self.media_list_player: Optional[vlc.MediaListPlayer] = None
        self.current_media_player: Optional[vlc.MediaPlayer] = None
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.on_song_end_callback: Optional[Callable] = None

        if self.vlc_available:
            self._initialize_vlc()

    def _initialize_vlc(self):
        """Initialize VLC instance"""
        try:
            # Create VLC instance
            self.instance = vlc.Instance()
            print("VLC initialized successfully")
        except Exception as e:
            print(f"Error initializing VLC: {e}")
            self.vlc_available = False

    def add_to_playlist(self, file_path: str) -> bool:
        """Add file to playlist"""
        if not file_path or not os.path.exists(file_path):
            return False

        self.playlist.append(file_path)
        return True

    def add_multiple_to_playlist(self, file_paths: list) -> int:
        """Add multiple files to playlist"""
        count = 0
        for file_path in file_paths:
            if self.add_to_playlist(file_path):
                count += 1
        return count

    def play_song(self, file_path: str) -> bool:
        """Play a specific song"""
        if not self.vlc_available or not self.instance:
            print("VLC not available")
            return False

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        try:
            # Stop current playback
            self.stop()

            # Create and play media
            media = self.instance.media_list_new()
            media.add_media(self.instance.media_new(file_path))

            self.media_list_player = self.instance.media_list_player_new()
            self.media_list_player.set_media_list(media)

            self.is_playing = True
            self.is_paused = False

            self.media_list_player.play()
            print(f"Playing: {file_path}")
            return True

        except Exception as e:
            print(f"Error playing song: {e}")
            return False

    def play_playlist(self, start_index: int = 0) -> bool:
        """Play playlist starting from index"""
        if not self.playlist or start_index >= len(self.playlist):
            return False

        if not self.vlc_available or not self.instance:
            return False

        try:
            self.current_index = start_index
            media = self.instance.media_list_new()

            # Add all songs from start_index
            for i in range(start_index, len(self.playlist)):
                media.add_media(self.instance.media_new(self.playlist[i]))

            self.media_list_player = self.instance.media_list_player_new()
            self.media_list_player.set_media_list(media)

            self.is_playing = True
            self.is_paused = False

            self.media_list_player.play()
            print(f"Playing playlist from index {start_index}")
            return True

        except Exception as e:
            print(f"Error playing playlist: {e}")
            return False

    def pause(self) -> bool:
        """Pause playback"""
        if not self.vlc_available or not self.media_list_player:
            return False

        try:
            self.media_list_player.pause()
            self.is_paused = True
            self.is_playing = False
            return True
        except Exception as e:
            print(f"Error pausing: {e}")
            return False

    def resume(self) -> bool:
        """Resume playback"""
        if not self.vlc_available or not self.media_list_player:
            return False

        try:
            self.media_list_player.play()
            self.is_paused = False
            self.is_playing = True
            return True
        except Exception as e:
            print(f"Error resuming: {e}")
            return False

    def stop(self) -> bool:
        """Stop playback"""
        if not self.vlc_available or not self.media_list_player:
            return False

        try:
            self.media_list_player.stop()
            self.is_playing = False
            self.is_paused = False
            return True
        except Exception as e:
            print(f"Error stopping: {e}")
            return False

    def next(self) -> bool:
        """Skip to next song"""
        if not self.vlc_available or not self.media_list_player:
            return False

        try:
            self.media_list_player.next()
            self.current_index = min(self.current_index + 1, len(self.playlist) - 1)
            return True
        except Exception as e:
            print(f"Error skipping: {e}")
            return False

    def previous(self) -> bool:
        """Go to previous song"""
        if not self.vlc_available or not self.media_list_player:
            return False

        try:
            self.media_list_player.previous()
            self.current_index = max(self.current_index - 1, 0)
            return True
        except Exception as e:
            print(f"Error going to previous: {e}")
            return False

    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)"""
        if not self.vlc_available or not self.media_list_player:
            return False

        volume = max(0, min(100, volume))

        try:
            self.media_list_player.get_media_player().audio_set_volume(volume)
            return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False

    def get_current_time(self) -> int:
        """Get current playback time in milliseconds"""
        if not self.vlc_available or not self.media_list_player:
            return 0

        try:
            return self.media_list_player.get_media_player().get_time()
        except Exception as e:
            print(f"Error getting time: {e}")
            return 0

    def get_duration(self) -> int:
        """Get current media duration in milliseconds"""
        if not self.vlc_available or not self.media_list_player:
            return 0

        try:
            return self.media_list_player.get_media_player().get_length()
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0

    def set_on_song_end_callback(self, callback: Callable):
        """Set callback for when song ends"""
        self.on_song_end_callback = callback

    def clear_playlist(self):
        """Clear playlist"""
        self.playlist.clear()
        self.current_index = 0

    def get_current_song(self) -> Optional[str]:
        """Get currently playing song"""
        if self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def is_vlc_available(self) -> bool:
        """Check if VLC is available"""
        return self.vlc_available

    def get_playlist_status(self) -> dict:
        """Get playlist status"""
        return {
            'playing': self.is_playing,
            'paused': self.is_paused,
            'current_index': self.current_index,
            'playlist_size': len(self.playlist),
            'current_song': self.get_current_song()
        }
