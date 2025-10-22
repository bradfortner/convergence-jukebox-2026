"""
File Service - File I/O operations for managing song files and data
"""

import os
import json
from typing import Optional, List, Dict, Any
import config


class FileService:
    """Service for file I/O operations"""

    def __init__(self):
        """Initialize file service"""
        self.parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def read_song_list(self, filename: str = "MusicMasterSongList.txt") -> Optional[List[Dict[str, Any]]]:
        """Read song list from JSON file"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            if not os.path.exists(file_path):
                print(f"Song list file not found: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]

        except Exception as e:
            print(f"Error reading song list: {e}")
            return None

    def write_song_list(self, songs: List[Dict[str, Any]], filename: str = "MusicMasterSongList.txt") -> bool:
        """Write song list to JSON file"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(songs, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error writing song list: {e}")
            return False

    def read_playlist(self, filename: str = "PaidMusicPlayList.txt") -> Optional[List[str]]:
        """Read playlist from JSON file"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            if not os.path.exists(file_path):
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []

        except Exception as e:
            print(f"Error reading playlist: {e}")
            return []

    def write_playlist(self, playlist: List[str], filename: str = "PaidMusicPlayList.txt") -> bool:
        """Write playlist to JSON file"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(playlist, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error writing playlist: {e}")
            return False

    def read_current_song(self, filename: str = "CurrentSongPlaying.txt") -> Optional[str]:
        """Read current playing song file path"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()

        except Exception as e:
            print(f"Error reading current song: {e}")
            return None

    def write_current_song(self, song_path: str, filename: str = "CurrentSongPlaying.txt") -> bool:
        """Write current playing song file path"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(song_path)

            return True

        except Exception as e:
            print(f"Error writing current song: {e}")
            return False

    def read_bands_list(self, filename: str = "the_bands.txt") -> List[str]:
        """Read bands list that need 'The' prefix"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            if not os.path.exists(file_path):
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Handle both JSON array and comma-separated formats
                if content.startswith('['):
                    return json.loads(content)
                else:
                    return [b.strip() for b in content.split(',') if b.strip()]

        except Exception as e:
            print(f"Error reading bands list: {e}")
            return []

    def write_bands_list(self, bands: List[str], filename: str = "the_bands.txt") -> bool:
        """Write bands list"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(bands, f, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error writing bands list: {e}")
            return False

    def read_exempted_bands(self, filename: str = "the_exempted_bands.txt") -> List[str]:
        """Read exempted bands list"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            if not os.path.exists(file_path):
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.startswith('['):
                    return json.loads(content)
                else:
                    return [b.strip() for b in content.split(',') if b.strip()]

        except Exception as e:
            print(f"Error reading exempted bands: {e}")
            return []

    def append_log(self, message: str, filename: str = "log.txt") -> bool:
        """Append message to log file"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(message + '\n')

            return True

        except Exception as e:
            print(f"Error writing to log: {e}")
            return False

    def read_log(self, filename: str = "log.txt") -> List[str]:
        """Read log file"""
        try:
            file_path = os.path.join(self.parent_dir, filename)

            if not os.path.exists(file_path):
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                return f.readlines()

        except Exception as e:
            print(f"Error reading log: {e}")
            return []

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(file_path)

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            print(f"Error getting file size: {e}")
            return 0

    def list_audio_files(self, directory: str) -> List[str]:
        """List all audio files in directory"""
        audio_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.wma')
        audio_files = []

        try:
            if os.path.isdir(directory):
                for file in os.listdir(directory):
                    if file.lower().endswith(audio_extensions):
                        audio_files.append(os.path.join(directory, file))
        except Exception as e:
            print(f"Error listing audio files: {e}")

        return sorted(audio_files)

    def ensure_file_exists(self, file_path: str, create_if_missing: bool = True) -> bool:
        """Ensure file exists, optionally create if missing"""
        if os.path.exists(file_path):
            return True

        if create_if_missing:
            try:
                # Create parent directories if needed
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Create empty file
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
                return True
            except Exception as e:
                print(f"Error creating file: {e}")
                return False

        return False
