"""
Data Management Layer - Handles persistence, song list, and state
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import config


@dataclass
class Song:
    """Represents a single song in the jukebox"""
    number: int
    location: str
    title: str
    artist: str
    album: str
    year: str
    comment: str  # Genre
    duration: str

    def __post_init__(self):
        """Ensure all fields are strings"""
        self.number = int(self.number)
        self.title = str(self.title).strip()
        self.artist = str(self.artist).strip()
        self.album = str(self.album).strip()
        self.year = str(self.year).strip()
        self.comment = str(self.comment).strip()
        self.duration = str(self.duration).strip()


@dataclass
class JukeboxState:
    """Current state of the jukebox"""
    selection_window_number: int = 0  # Current page in song grid
    credit_amount: float = config.INITIAL_CREDIT
    upcoming_playlist: List[str] = field(default_factory=list)  # Display names
    selected_letter: str = ""  # A, B, or C
    selected_number: str = ""  # 1-7
    last_song_playing: str = ""
    search_results: List[Song] = field(default_factory=list)


class DataManager:
    """Handles all data persistence and state management"""

    def __init__(self):
        self.songs: List[Song] = []
        self.state = JukeboxState()
        self.paid_queue: List[int] = []  # Song indices to play
        self.bands_list: List[str] = []
        self.exempted_bands: List[str] = []
        self.genre_flags: List[str] = []

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def initialize(self) -> bool:
        """Load all data files and initialize state"""
        try:
            self._ensure_files_exist()
            self._load_song_list()
            self._load_configuration()
            self._load_paid_queue()
            self._log_startup()
            return True
        except Exception as e:
            print(f"Error initializing DataManager: {e}")
            return False

    def _ensure_files_exist(self):
        """Create necessary data files if they don't exist"""
        # Ensure log file exists
        if not os.path.exists(config.LOG_FILE):
            with open(config.LOG_FILE, 'w') as f:
                f.write("")

        # Ensure bands file exists
        if not os.path.exists(config.BANDS_FILE):
            default_bands = ["beatles", "rolling stones", "who", "doors", "byrds", "beachboys"]
            with open(config.BANDS_FILE, 'w') as f:
                json.dump(",".join(default_bands), f)

        # Ensure exempted bands file exists
        if not os.path.exists(config.EXEMPTED_BANDS_FILE):
            with open(config.EXEMPTED_BANDS_FILE, 'w') as f:
                f.write("")

        # Ensure genre flags file exists
        if not os.path.exists(config.GENRE_FLAGS_FILE):
            default_genres = ["null", "null", "null", "null"]
            with open(config.GENRE_FLAGS_FILE, 'w') as f:
                json.dump(default_genres, f)

        # Ensure paid playlist file exists
        if not os.path.exists(config.PAID_PLAYLIST_FILE):
            with open(config.PAID_PLAYLIST_FILE, 'w') as f:
                json.dump([], f)

    def _load_song_list(self):
        """Load the master song list from file"""
        if not os.path.exists(config.SONG_LIST_FILE):
            print(f"Warning: {config.SONG_LIST_FILE} not found")
            return

        try:
            with open(config.SONG_LIST_FILE, 'r') as f:
                song_dicts = json.load(f)

            self.songs = [Song(**song_dict) for song_dict in song_dicts]
            print(f"Loaded {len(self.songs)} songs")
        except Exception as e:
            print(f"Error loading song list: {e}")

    def _load_configuration(self):
        """Load bands and genre configuration"""
        try:
            if os.path.exists(config.BANDS_FILE):
                with open(config.BANDS_FILE, 'r') as f:
                    bands_str = json.load(f)
                    self.bands_list = [b.strip() for b in bands_str.split(',')]

            if os.path.exists(config.EXEMPTED_BANDS_FILE):
                with open(config.EXEMPTED_BANDS_FILE, 'r') as f:
                    self.exempted_bands = [line.strip() for line in f.readlines()]

            if os.path.exists(config.GENRE_FLAGS_FILE):
                with open(config.GENRE_FLAGS_FILE, 'r') as f:
                    self.genre_flags = json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def _load_paid_queue(self):
        """Load the paid play queue"""
        try:
            if os.path.exists(config.PAID_PLAYLIST_FILE):
                with open(config.PAID_PLAYLIST_FILE, 'r') as f:
                    self.paid_queue = json.load(f)
        except Exception as e:
            print(f"Error loading paid queue: {e}")

    # ========================================================================
    # SONG LIST OPERATIONS
    # ========================================================================

    def get_song_page(self, page: int) -> List[Song]:
        """Get a page of songs for display (21 songs per page)"""
        start_idx = page * config.SONGS_PER_PAGE
        end_idx = start_idx + config.SONGS_PER_PAGE

        # Clamp to valid range
        if start_idx >= len(self.songs):
            start_idx = max(0, len(self.songs) - config.SONGS_PER_PAGE)
            end_idx = len(self.songs)

        if start_idx < 0:
            start_idx = 0

        return self.songs[start_idx:end_idx]

    def get_song(self, index: int) -> Optional[Song]:
        """Get a song by index"""
        if 0 <= index < len(self.songs):
            return self.songs[index]
        return None

    def get_total_songs(self) -> int:
        """Get total number of songs"""
        return len(self.songs)

    def get_max_pages(self) -> int:
        """Get maximum page number"""
        return (len(self.songs) - 1) // config.SONGS_PER_PAGE

    def find_songs_by_title(self, search_term: str) -> List[Song]:
        """Search songs by title"""
        search_term = search_term.lower()
        return [s for s in self.songs if search_term in s.title.lower()]

    def find_songs_by_artist(self, search_term: str) -> List[Song]:
        """Search songs by artist"""
        search_term = search_term.lower()
        return [s for s in self.songs if search_term in s.artist.lower()]

    def find_song_index(self, song: Song) -> int:
        """Find the index of a song"""
        try:
            return self.songs.index(song)
        except ValueError:
            return -1

    # ========================================================================
    # SELECTION AND STATE
    # ========================================================================

    def set_selected_button(self, letter: str, number: str) -> str:
        """Set the selected button and return the selection code (e.g., 'A1')"""
        self.state.selected_letter = letter.upper()
        self.state.selected_number = str(number)
        return f"{letter.upper()}{number}"

    def get_selected_button(self) -> str:
        """Get the current selection code"""
        return f"{self.state.selected_letter}{self.state.selected_number}"

    def clear_selection(self):
        """Clear the current selection"""
        self.state.selected_letter = ""
        self.state.selected_number = ""

    def get_button_index_on_page(self, letter: str, number: str) -> Optional[int]:
        """
        Get the song index for a button selection (e.g., A3 or B5)
        Returns the index within the current page (0-20) or None
        """
        col_map = {'A': 0, 'B': 1, 'C': 2}
        row = int(number) - 1  # 0-based

        if letter.upper() not in col_map or row < 0 or row >= config.SELECTION_GRID_ROWS:
            return None

        col = col_map[letter.upper()]
        return row * config.SELECTION_GRID_COLS + col

    def get_selected_song_on_page(self) -> Optional[Song]:
        """Get the song at the current selection (A1-C7) on current page"""
        if not self.state.selected_letter or not self.state.selected_number:
            return None

        button_index = self.get_button_index_on_page(
            self.state.selected_letter,
            self.state.selected_number
        )

        if button_index is None:
            return None

        page_songs = self.get_song_page(self.state.selection_window_number)
        if button_index < len(page_songs):
            return page_songs[button_index]

        return None

    # ========================================================================
    # PAGINATION
    # ========================================================================

    def next_page(self) -> bool:
        """Move to next page, return True if successful"""
        if self.state.selection_window_number < self.get_max_pages():
            self.state.selection_window_number += 1
            return True
        return False

    def prev_page(self) -> bool:
        """Move to previous page, return True if successful"""
        if self.state.selection_window_number > 0:
            self.state.selection_window_number -= 1
            return True
        return False

    def set_page(self, page: int):
        """Set to specific page"""
        max_page = self.get_max_pages()
        self.state.selection_window_number = max(0, min(page, max_page))

    # ========================================================================
    # UPCOMING QUEUE
    # ========================================================================

    def add_to_upcoming(self, song: Song):
        """Add a song to the upcoming queue"""
        if len(self.state.upcoming_playlist) < config.MAX_UPCOMING_ITEMS:
            display_name = f"{song.artist} - {song.title}"
            self.state.upcoming_playlist.append(display_name)

    def pop_upcoming(self) -> Optional[str]:
        """Remove and return the first upcoming song"""
        if self.state.upcoming_playlist:
            return self.state.upcoming_playlist.pop(0)
        return None

    def get_upcoming(self) -> List[str]:
        """Get the upcoming queue"""
        return self.state.upcoming_playlist.copy()

    def clear_upcoming(self):
        """Clear the upcoming queue"""
        self.state.upcoming_playlist.clear()

    # ========================================================================
    # CREDITS
    # ========================================================================

    def add_credit(self, amount: float):
        """Add credit amount"""
        self.state.credit_amount += amount

    def subtract_credit(self, amount: float) -> bool:
        """Subtract credit if available"""
        if self.state.credit_amount >= amount:
            self.state.credit_amount -= amount
            return True
        return False

    def get_credits(self) -> float:
        """Get current credit amount"""
        return self.state.credit_amount

    def set_credits(self, amount: float):
        """Set credit amount directly"""
        self.state.credit_amount = max(0, amount)

    # ========================================================================
    # PAID QUEUE PERSISTENCE
    # ========================================================================

    def add_paid_song(self, song: Song) -> bool:
        """Add a song to the paid queue and save"""
        try:
            self.paid_queue.append(song.number)
            self._save_paid_queue()
            self._log_selection(song.artist, song.title, "Paid")
            return True
        except Exception as e:
            print(f"Error adding paid song: {e}")
            return False

    def get_paid_queue(self) -> List[int]:
        """Get the paid queue"""
        return self.paid_queue.copy()

    def clear_paid_queue(self):
        """Clear the paid queue"""
        self.paid_queue.clear()
        self._save_paid_queue()

    def _save_paid_queue(self):
        """Save paid queue to file"""
        try:
            with open(config.PAID_PLAYLIST_FILE, 'w') as f:
                json.dump(self.paid_queue, f)
        except Exception as e:
            print(f"Error saving paid queue: {e}")

    # ========================================================================
    # LOGGING
    # ========================================================================

    def _log_startup(self):
        """Log application startup"""
        now = self._get_timestamp()
        with open(config.LOG_FILE, 'a') as f:
            f.write(f"\n{now}, Jukebox GUI Started,")

    def _log_selection(self, artist: str, title: str, mode: str):
        """Log a song selection"""
        try:
            now = self._get_timestamp()
            with open(config.LOG_FILE, 'a') as f:
                f.write(f"\n{now}, {artist} - {title}, Played {mode},")
        except Exception as e:
            print(f"Error logging selection: {e}")

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp rounded to nearest second"""
        now = datetime.now()
        rounded = now + timedelta(seconds=0.5)
        return rounded.replace(microsecond=0).isoformat(' ')

    # ========================================================================
    # BAND NAME PROCESSING
    # ========================================================================

    def apply_band_name_rules(self, artist_name: str) -> str:
        """Apply 'The' prefix rules to band names"""
        if not artist_name:
            return artist_name

        # Check if in exempted bands
        if artist_name in self.exempted_bands:
            return artist_name

        # Check if should have "The" added
        for band in self.bands_list:
            if artist_name.lower() == band.lower() and not artist_name.startswith("The "):
                return f"The {artist_name}"

        return artist_name

    # ========================================================================
    # CURRENT PLAYING TRACKING
    # ========================================================================

    def get_current_playing_path(self) -> Optional[str]:
        """Get the current playing song file path"""
        try:
            if os.path.exists(config.CURRENT_PLAYING_FILE):
                with open(config.CURRENT_PLAYING_FILE, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error reading current playing: {e}")
        return None

    def find_song_by_path(self, file_path: str) -> Optional[Song]:
        """Find a song by its file path"""
        for song in self.songs:
            if song.location == file_path:
                return song
        return None

    # ========================================================================
    # STATS
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get jukebox statistics"""
        return {
            'total_songs': len(self.songs),
            'current_page': self.state.selection_window_number,
            'max_pages': self.get_max_pages(),
            'credits': self.state.credit_amount,
            'upcoming_count': len(self.state.upcoming_playlist),
            'paid_queue_count': len(self.paid_queue),
        }
