import vlc
from datetime import datetime, timedelta
from tinytag import TinyTag
import psutil
import glob
import json
import os
import random
import time
import gc
import sys
from typing import List, Dict, Any, Optional


class JukeboxEngineException(Exception):
    """Custom exception for Jukebox Engine errors"""
    pass


class JukeboxEngine:
    """Main Convergence Jukebox Engine - Manages music playback and playlist management"""

    # Configuration constants
    SLEEP_TIME: float = 0.5
    TIMESTAMP_ROUNDING: float = 0.5

    def __init__(self) -> None:
        """Initialize Jukebox Engine with all required variables and file setup"""
        # Initialize data structures
        self.music_id3_metadata_list: List[tuple] = []
        self.music_master_song_list: List[Dict[str, str]] = []
        self.random_music_playlist: List[int] = []
        self.paid_music_playlist: List[int] = []
        self.final_genre_list: List[str] = []

        # Current song metadata
        self.artist_name: str = ""
        self.song_name: str = ""
        self.album_name: str = ""
        self.song_duration: str = ""
        self.song_year: str = ""
        self.song_genre: str = ""

        # Genre flags
        self.genre0: str = "null"
        self.genre1: str = "null"
        self.genre2: str = "null"
        self.genre3: str = "null"

        # Get directory path for cross-platform compatibility
        self.dir_path: str = os.path.dirname(os.path.realpath(__file__))

        # Define standard file and directory paths using os.path.join for cross-platform compatibility
        self.music_dir: str = os.path.join(self.dir_path, 'music')
        self.log_file: str = os.path.join(self.dir_path, 'log.txt')
        self.genre_flags_file: str = os.path.join(self.dir_path, 'GenreFlagsList.txt')
        self.music_master_song_list_file: str = os.path.join(self.dir_path, 'MusicMasterSongList.txt')
        self.music_master_song_list_check_file: str = os.path.join(self.dir_path, 'MusicMasterSongListCheck.txt')
        self.paid_music_playlist_file: str = os.path.join(self.dir_path, 'PaidMusicPlayList.txt')
        self.current_song_playing_file: str = os.path.join(self.dir_path, 'CurrentSongPlaying.txt')

        # Initialize log file and required data files
        self._setup_files()

    def _get_rounded_timestamp(self) -> datetime:
        """Helper method to get current timestamp rounded to nearest second

        Returns:
            datetime: Current timestamp rounded to nearest second
        """
        try:
            now: datetime = datetime.now()
            rounded_now: datetime = now + timedelta(seconds=self.TIMESTAMP_ROUNDING)
            return rounded_now.replace(microsecond=0)
        except Exception as e:
            print(f"ERROR: Failed to get timestamp: {e}")
            return datetime.now()

    def _log_error(self, error_message: str) -> None:
        """Log error message to both console and log file

        Args:
            error_message (str): The error message to log
        """
        timestamp: datetime = self._get_rounded_timestamp()
        error_log: str = f"\n{timestamp} ERROR: {error_message}"

        try:
            with open(self.log_file, 'a') as log:
                log.write(error_log)
        except Exception as e:
            print(f"CRITICAL: Could not write to log file: {e}")

        print(error_log)

    def _setup_files(self) -> None:
        """Check for files on disk. If they don't exist, create them"""
        # Create date and time stamp for log file
        now: datetime = self._get_rounded_timestamp()

        # Setup log file
        try:
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w') as log:
                    log.write(str(now) + ' Jukebox Engine Started - New Log File Created,')
            else:
                with open(self.log_file, 'a') as log:
                    log.write('\n' + str(now) + ' Jukebox Engine Restarted,')
        except IOError as e:
            self._log_error(f"Failed to setup log.txt: {e}")

        # Setup genre flags file
        try:
            if not os.path.exists(self.genre_flags_file):
                with open(self.genre_flags_file, 'w') as genre_flags_file:
                    genre_flags_list: List[str] = ['null', 'null', 'null', 'null']
                    json.dump(genre_flags_list, genre_flags_file)
        except (IOError, json.JSONDecodeError) as e:
            self._log_error(f"Failed to setup GenreFlagsList.txt: {e}")

        # Setup music master song list check file
        try:
            if not os.path.exists(self.music_master_song_list_check_file):
                with open(self.music_master_song_list_check_file, 'w') as check_file:
                    json.dump([], check_file)
        except (IOError, json.JSONDecodeError) as e:
            self._log_error(f"Failed to setup MusicMasterSongListCheck.txt: {e}")

        # Setup paid music playlist file
        try:
            if not os.path.exists(self.paid_music_playlist_file):
                with open(self.paid_music_playlist_file, 'w') as paid_list_file:
                    json.dump([], paid_list_file)
        except (IOError, json.JSONDecodeError) as e:
            self._log_error(f"Failed to setup PaidMusicPlayList.txt: {e}")

    def assign_song_data(self, playlist_type: str = 'random') -> bool:
        """
        Assign song metadata from specified playlist to instance variables

        Args:
            playlist_type (str): Either 'random' or 'paid' to specify which playlist to use

        Returns:
            bool: True if successful, False otherwise

        REMOVED DUPLICATION: Combined assign_song_data_random() and assign_song_data_paid()
        into a single method to eliminate code duplication.
        """
        try:
            # Determine which playlist to use and validate
            if playlist_type == 'random':
                if not self.random_music_playlist:
                    self._log_error("Random playlist is empty")
                    return False
                song_index: int = self.random_music_playlist[0]
            elif playlist_type == 'paid':
                if not self.paid_music_playlist:
                    self._log_error("Paid playlist is empty")
                    return False
                song_index: int = int(self.paid_music_playlist[0])
            else:
                self._log_error(f"Invalid playlist type: {playlist_type}")
                return False

            # Validate song index
            if song_index >= len(self.music_master_song_list):
                self._log_error(f"Song index {song_index} out of range")
                return False

            # Assign song metadata to instance variables
            self.artist_name = self.music_master_song_list[song_index]['artist']
            self.song_name = self.music_master_song_list[song_index]['title']
            self.album_name = self.music_master_song_list[song_index]['album']
            self.song_duration = self.music_master_song_list[song_index]['duration']
            self.song_year = self.music_master_song_list[song_index]['year']
            self.song_genre = self.music_master_song_list[song_index]['comment']
            return True
        except (KeyError, IndexError, TypeError, ValueError) as e:
            self._log_error(f"Failed to assign {playlist_type} song data: {e}")
            return False

    def generate_mp3_metadata(self) -> bool:
        """Generate MP3 metadata from music directory

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("Convergence Jukebox 2025\nPlease Be Patient Regenerating Your Songlist From Scratch \nMusic Will Start When Finished")
            counter: int = 0

            # Get music files using cross-platform path
            try:
                mp3_music_files: List[str] = glob.glob(os.path.join(self.music_dir, '*.mp3'))
            except Exception as e:
                self._log_error(f"Failed to search for MP3 files: {e}")
                return False

            if not mp3_music_files:
                self._log_error("No MP3 files found in music directory")
                return False

            for file_path in mp3_music_files:
                try:
                    id3tag: Optional[Any] = TinyTag.get(file_path)

                    if id3tag is None:
                        self._log_error(f"Could not read metadata from {file_path}")
                        continue

                    get_song_duration_seconds: str = "%f" % id3tag.duration
                    remove_song_duration_decimals: float = float(get_song_duration_seconds)
                    song_duration_decimals_removed: int = int(remove_song_duration_decimals)
                    song_duration_minutes_seconds: int = int(song_duration_decimals_removed)
                    song_duration: str = time.strftime("%M:%S", time.gmtime(song_duration_minutes_seconds))

                    song_metadata: List[Any] = list((
                        counter,
                        file_path,
                        "%s" % id3tag.title,
                        "%s" % id3tag.artist,
                        "%s" % id3tag.album,
                        "%s" % id3tag.year,
                        "%s" % id3tag.comment,
                        song_duration
                    ))
                    self.music_id3_metadata_list.append(song_metadata)
                    counter += 1
                except Exception as e:
                    self._log_error(f"Failed to extract metadata from {file_path}: {e}")
                    continue

            if not self.music_id3_metadata_list:
                self._log_error("No valid metadata was extracted from MP3 files")
                return False

            return True
        except Exception as e:
            self._log_error(f"Unexpected error in generate_mp3_metadata: {e}")
            return False

    def generate_music_master_song_list_dictionary(self) -> bool:
        """Generate master song list dictionary and save to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Assign keys for MusicMasterSongList Dictionary
            keys: List[str] = ['number', 'location', 'title', 'artist', 'album', 'year', 'comment', 'duration']

            # Build MusicMasterSongList Dictionary
            self.music_master_song_list = [dict(zip(keys, sublst)) for sublst in self.music_id3_metadata_list]

            # Save MusicMasterSongList Dictionary
            try:
                with open(self.music_master_song_list_file, 'w') as master_list_file:
                    json.dump(self.music_master_song_list, master_list_file)
            except (IOError, json.JSONDecodeError) as e:
                self._log_error(f"Failed to save MusicMasterSongList.txt: {e}")
                return False

            # Create and save a file list size value to check if MusicMasterSongList has changed after a reboot
            list_size: int = len(self.music_master_song_list)
            try:
                with open(self.music_master_song_list_check_file, 'w') as check_file:
                    json.dump(list_size, check_file)
            except (IOError, json.JSONDecodeError) as e:
                self._log_error(f"Failed to save MusicMasterSongListCheck.txt: {e}")
                return False

            return True
        except Exception as e:
            self._log_error(f"Unexpected error in generate_music_master_song_list_dictionary: {e}")
            return False

    def play_song(self, song_file_name: str) -> bool:
        """Play a song using VLC media player

        Args:
            song_file_name (str): The full path to the song file to play

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(song_file_name):
                self._log_error(f"Song file not found: {song_file_name}")
                return False

            print(psutil.virtual_memory())
            # Get the current garbage collection state
            print("Garbage collection thresholds:", gc.get_threshold())

            # Perform garbage collection
            collected: int = gc.collect()
            print("Garbage collector: collected", "%d objects." % collected)

            # VLC Song Playback Code Begin
            try:
                p: vlc.MediaPlayer = vlc.MediaPlayer(song_file_name)
                p.play()
                print('is_playing:', p.is_playing())  # 0 = False
                time.sleep(self.SLEEP_TIME)  # sleep because it needs time to start playing
                print('is_playing:', p.is_playing())  # 1 = True

                while p.is_playing():
                    time.sleep(self.SLEEP_TIME)  # sleep to use less CPU
                # VLC Song Playback Code End
                return True
            except Exception as vlc_error:
                self._log_error(f"VLC playback error for {song_file_name}: {vlc_error}")
                return False
        except Exception as e:
            self._log_error(f"Unexpected error in play_song: {e}")
            return False

    def assign_genres_to_random_play(self) -> bool:
        """Load and assign genres from GenreFlagsList file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            extract_original_assigned_genres: List[str] = []
            unfiltered_final_genre_list: List[str] = []

            try:
                with open(self.genre_flags_file, 'r') as genre_flags_file:
                    genre_flags_list: List[str] = json.load(genre_flags_file)
            except (IOError, json.JSONDecodeError) as e:
                self._log_error(f"Failed to load GenreFlagsList.txt: {e}")
                genre_flags_list: List[str] = ['null', 'null', 'null', 'null']

            self.genre0 = genre_flags_list[0] if len(genre_flags_list) > 0 else 'null'
            self.genre1 = genre_flags_list[1] if len(genre_flags_list) > 1 else 'null'
            self.genre2 = genre_flags_list[2] if len(genre_flags_list) > 2 else 'null'
            self.genre3 = genre_flags_list[3] if len(genre_flags_list) > 3 else 'null'

            # Extract genres from all songs
            for song in self.music_master_song_list:
                try:
                    extract_original_assigned_genres.append(song['comment'])
                except KeyError:
                    self._log_error(f"Missing 'comment' field in song: {song}")
                    continue

            # Split multi-genre selections
            for genre_string in extract_original_assigned_genres:
                if ' ' in genre_string:
                    split_genres: List[str] = genre_string.split()
                    extract_original_assigned_genres.extend(split_genres)

            # Filter and create final genre list
            for genre in extract_original_assigned_genres:
                if ' ' not in genre:
                    unfiltered_final_genre_list.append(genre)

            self.final_genre_list = list(set(unfiltered_final_genre_list))  # removes duplicates
            self.final_genre_list.sort()

            # Print genre information
            print('Genres for Random Play are:')
            genres: List[str] = [self.genre0, self.genre1, self.genre2, self.genre3]
            for idx, genre in enumerate(genres):
                if genre == 'null':
                    print(f'No Genre {idx}')
                else:
                    print(genre)
            return True
        except Exception as e:
            self._log_error(f"Unexpected error in assign_genres_to_random_play: {e}")
            return False

    def generate_random_song_list(self) -> bool:
        """Generate random song playlist based on genre filters

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            counter: int = 0
            for song in self.music_master_song_list:
                try:
                    # Skip songs marked with 'norandom'
                    if 'norandom' in song['comment']:
                        counter += 1
                        continue

                    # Add all songs if no genre filters are set
                    if (self.genre0 == "null" and self.genre1 == "null" and
                        self.genre2 == "null" and self.genre3 == "null"):
                        self.random_music_playlist.append(counter)
                    else:
                        # Add songs matching any of the genre filters
                        if self.genre0 != "null" and self.genre0 in song['comment']:
                            self.random_music_playlist.append(counter)
                        elif self.genre1 != "null" and self.genre1 in song['comment']:
                            self.random_music_playlist.append(counter)
                        elif self.genre2 != "null" and self.genre2 in song['comment']:
                            self.random_music_playlist.append(counter)
                        elif self.genre3 != "null" and self.genre3 in song['comment']:
                            self.random_music_playlist.append(counter)

                    counter += 1
                except KeyError as e:
                    self._log_error(f"Missing key in song data: {e}")
                    counter += 1
                    continue

            random.shuffle(self.random_music_playlist)
            return True
        except Exception as e:
            self._log_error(f"Unexpected error in generate_random_song_list: {e}")
            return False

    def _log_song_play(self, artist: str, title: str, play_type: str) -> None:
        """Log a song play event to log file

        Args:
            artist (str): The artist name
            title (str): The song title
            play_type (str): Either 'Paid' or 'Random'
        """
        try:
            with open(self.log_file, 'a') as log:
                now: datetime = self._get_rounded_timestamp()
                log.write('\n' + str(now) + ', ' + str(artist) + ' - ' + str(title) + ', Played ' + play_type + ',')
        except IOError as e:
            self._log_error(f"Failed to log song play: {e}")

    def _write_current_song_playing(self, song_location: str) -> None:
        """Write current playing song location to file

        Args:
            song_location (str): The full path to the currently playing song
        """
        try:
            with open(self.current_song_playing_file, "w") as outfile:
                outfile.write(song_location)
        except IOError as e:
            self._log_error(f"Failed to write CurrentSongPlaying.txt: {e}")

    def jukebox_engine(self) -> bool:
        """
        Main jukebox engine - plays paid songs first, then alternates with random songs

        IMPORTANT: This method uses while loops instead of recursion to prevent
        stack overflow. The paid playlist file is checked after each random song,
        enabling real-time additions of paid songs during playback.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Main loop: continuously check for paid songs, play them, then play one random song
            while True:
                # Play all paid songs - reload file at each iteration to pick up new requests
                while True:
                    # Reload paid music playlist from file at each iteration to enable real-time additions
                    try:
                        with open(self.paid_music_playlist_file, 'r') as paid_list_file:
                            self.paid_music_playlist = json.load(paid_list_file)
                    except (IOError, json.JSONDecodeError) as e:
                        self._log_error(f"Failed to load PaidMusicPlayList.txt: {e}")
                        break

                    # If no more paid songs, exit the inner loop
                    if not self.paid_music_playlist:
                        break
                    try:
                        song_index: int = self.paid_music_playlist[0]

                        if song_index >= len(self.music_master_song_list):
                            self._log_error(f"Invalid song index in paid playlist: {song_index}")
                            del self.paid_music_playlist[0]
                            continue

                        song: Dict[str, str] = self.music_master_song_list[song_index]

                        print('Now Playing: ' + song['title'] + ' - ' + song['artist'] +
                              '  Year:' + song['year'] + ' Length:' + song['duration'] +
                              ' Album:' + song['album'] + '  Genre:' + song['comment'])

                        # Save current playing song to disk
                        self._write_current_song_playing(song['location'])

                        # Log paid song play
                        self._log_song_play(song['artist'], song['title'], 'Paid')

                        print('Playing Paid Song In Jukebox Engine')
                        if not self.play_song(song['location']):
                            self._log_error(f"Failed to play paid song: {song['title']}")

                        # Delete song just played from paid playlist
                        try:
                            del self.paid_music_playlist[0]
                            with open(self.paid_music_playlist_file, 'w') as paid_list_file:
                                json.dump(self.paid_music_playlist, paid_list_file)
                        except (IOError, json.JSONDecodeError) as e:
                            self._log_error(f"Failed to update PaidMusicPlayList.txt: {e}")
                            break
                    except (KeyError, IndexError, TypeError) as e:
                        self._log_error(f"Error processing paid song: {e}")
                        break

                # Play one random song, then loop back to check for paid songs again
                if self.random_music_playlist:
                    try:
                        if not self.assign_song_data('random'):
                            self._log_error("Failed to assign random song data, skipping")
                            break

                        print('Now Playing: ' + self.song_name + ' - ' + self.artist_name +
                              '  Year:' + self.song_year + ' Length:' + self.song_duration +
                              ' Album:' + self.album_name + '  Genre:' + self.song_genre)

                        # Save current playing song to disk
                        song_index: int = self.random_music_playlist[0]
                        self._write_current_song_playing(self.music_master_song_list[song_index]['location'])

                        # Log random song play
                        self._log_song_play(self.artist_name, self.song_name, 'Random')

                        if not self.play_song(self.music_master_song_list[song_index]['location']):
                            self._log_error(f"Failed to play random song: {self.song_name}")

                        # Move song to end of RandomMusicPlaylist
                        move_first_list_element: int = self.random_music_playlist.pop(0)
                        self.random_music_playlist.append(move_first_list_element)
                        # Loop continues, goes back to check for paid songs again
                    except (KeyError, IndexError, TypeError) as e:
                        self._log_error(f"Error processing random song: {e}")
                        break
                else:
                    # If no random songs in playlist, exit the main loop
                    break

            return True
        except Exception as e:
            self._log_error(f"Unexpected error in jukebox_engine: {e}")
            return False

    def run(self) -> None:
        """Main execution method"""
        try:
            # Check to see if MusicMasterSongList exists on disk
            if os.path.exists(self.music_master_song_list_file):
                print('Check to see if MusicMasterSongList exists on disk')

                # Count number of files in music directory
                try:
                    current_file_count: int = len(glob.glob(os.path.join(self.music_dir, '*.mp3')))
                    print(current_file_count)
                except Exception as e:
                    self._log_error(f"Failed to count MP3 files: {e}")
                    current_file_count: int = -1

                # Open MusicMasterSongListCheck generated from previous run
                try:
                    with open(self.music_master_song_list_check_file, 'r') as check_file:
                        stored_file_count: int = json.load(check_file)
                        print(stored_file_count)
                except (IOError, json.JSONDecodeError) as e:
                    self._log_error(f"Failed to load MusicMasterSongListCheck.txt: {e}")
                    stored_file_count: int = -1

                # Check for match
                if current_file_count == stored_file_count and current_file_count != -1:
                    print('Match')
                    # Open MusicMasterSongList dictionary
                    try:
                        with open(self.music_master_song_list_file, 'r') as master_list_file:
                            self.music_master_song_list = json.load(master_list_file)

                        # MusicMasterSongList matches, run required functions
                        if (self.assign_genres_to_random_play() and
                            self.generate_random_song_list()):
                            self.jukebox_engine()
                            return
                    except (IOError, json.JSONDecodeError) as e:
                        self._log_error(f"Failed to load MusicMasterSongList.txt: {e}")

            # If no match or file doesn't exist, regenerate everything
            if (self.generate_mp3_metadata() and
                self.generate_music_master_song_list_dictionary() and
                self.assign_genres_to_random_play() and
                self.generate_random_song_list()):
                self.jukebox_engine()
            else:
                self._log_error("Failed to initialize jukebox engine")
        except Exception as e:
            self._log_error(f"Critical error in run method: {e}")


# Main execution
if __name__ == "__main__":
    try:
        jukebox: JukeboxEngine = JukeboxEngine()
        jukebox.run()
    except Exception as e:
        print(f"CRITICAL: Failed to start Jukebox Engine: {e}")
        sys.exit(1)
