import vlc
from datetime import datetime, timedelta # required for logging timestamp
from tinytag import TinyTag  # https://pypi.org/project/tinytag/
import psutil
import glob
import json
import os
import random
import time
import gc
import sys


class JukeboxEngine:
    """Main Convergence Jukebox Engine - Manages music playback and playlist management"""

    # Configuration constants
    SLEEP_TIME = 0.5
    TIMESTAMP_ROUNDING = 0.5

    def __init__(self):
        """Initialize Jukebox Engine with all required variables and file setup"""
        # Initialize data structures
        self.music_id3_metadata_list = []  # list of all songs mp3 id3 metadata
        self.music_master_song_list = []  # dictionary of all songs mp3 id3 metadata required by Convergence Jukebox
        self.random_music_playlist = []  # list of randomly played songs
        self.paid_music_playlist = []  # list of paid songs to be played
        self.final_genre_list = []  # List of genres found in comment metadata on all songs

        # Current song metadata
        self.random_music_play_number = ""
        self.artist_name = ""
        self.song_name = ""
        self.album_name = ""
        self.song_duration = ""
        self.song_year = ""
        self.song_genre = ""

        # Genre flags
        self.genre0 = "null"
        self.genre1 = "null"
        self.genre2 = "null"
        self.genre3 = "null"

        # Get directory path for cross-platform compatibility
        self.dir_path = os.path.dirname(os.path.realpath(__file__))

        # Initialize log file and required data files
        self._setup_files()

    def _get_rounded_timestamp(self):
        """Helper method to get current timestamp rounded to nearest second"""
        now = datetime.now()
        rounded_now = now + timedelta(seconds=self.TIMESTAMP_ROUNDING)
        return rounded_now.replace(microsecond=0)

    def _setup_files(self):
        """Check for files on disk. If they don't exist, create them"""
        # Create date and time stamp for log file
        now = self._get_rounded_timestamp()

        # Setup log file
        if not os.path.exists('log.txt'):
            with open('log.txt', 'w') as log:
                log.write(str(now) + ' Jukebox Engine Started - New Log File Created,')
        else:
            with open('log.txt', 'a') as log:
                log.write('\n' + str(now) + ' Jukebox Engine Restarted,')

        # Setup genre flags file
        if not os.path.exists('GenreFlagsList.txt'):
            with open('GenreFlagsList.txt', 'w') as genre_flags_file:
                genre_flags_list = ['null', 'null', 'null', 'null']
                json.dump(genre_flags_list, genre_flags_file)

        # Setup music master song list check file
        if not os.path.exists('MusicMasterSongListCheck.txt'):
            with open('MusicMasterSongListCheck.txt', 'w') as check_file:
                json.dump([], check_file)

        # Setup paid music playlist file
        if not os.path.exists('PaidMusicPlayList.txt'):
            with open('PaidMusicPlayList.txt', 'w') as paid_list_file:
                json.dump([], paid_list_file)

    def assign_song_data_random(self):
        """Assign song metadata from random playlist to instance variables"""
        song_index = self.random_music_playlist[0]
        self.artist_name = self.music_master_song_list[song_index]['artist']
        self.song_name = self.music_master_song_list[song_index]['title']
        self.album_name = self.music_master_song_list[song_index]['album']
        self.song_duration = self.music_master_song_list[song_index]['duration']
        self.song_year = self.music_master_song_list[song_index]['year']
        self.song_genre = self.music_master_song_list[song_index]['comment']

    def assign_song_data_paid(self):
        """Assign song metadata from paid playlist to instance variables"""
        song_index = int(self.paid_music_playlist[0])
        self.artist_name = self.music_master_song_list[song_index]['artist']
        self.song_name = self.music_master_song_list[song_index]['title']
        self.album_name = self.music_master_song_list[song_index]['album']
        self.song_duration = self.music_master_song_list[song_index]['duration']
        self.song_year = self.music_master_song_list[song_index]['year']
        self.song_genre = self.music_master_song_list[song_index]['comment']

    def generate_mp3_metadata(self):
        """Generate MP3 metadata from music directory"""
        print("Convergence Jukebox 2025\nPlease Be Patient Regenerating Your Songlist From Scratch \nMusic Will Start When Finished")
        counter = 0

        # Get music files based on OS (use os.path.join for cross-platform support)
        if sys.platform.startswith('linux'):
            mp3_music_files = glob.glob(os.path.join(self.dir_path, 'music', '*.mp3'))
        elif sys.platform.startswith('win32'):
            mp3_music_files = glob.glob(os.path.join(self.dir_path, 'music', '*.mp3'))

        for file_path in mp3_music_files:
            id3tag = TinyTag.get(file_path)
            get_song_duration_seconds = "%f" % id3tag.duration
            remove_song_duration_decimals = float(get_song_duration_seconds)
            song_duration_decimals_removed = int(remove_song_duration_decimals)
            song_duration_minutes_seconds = int(song_duration_decimals_removed)
            song_duration = time.strftime("%M:%S", time.gmtime(song_duration_minutes_seconds))

            song_metadata = list((
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

    def generate_music_master_song_list_dictionary(self):
        """Generate master song list dictionary and save to file"""
        # Assign keys for MusicMasterSongList Dictionary
        keys = ['number', 'location', 'title', 'artist', 'album', 'year', 'comment', 'duration']

        # Build MusicMasterSongList Dictionary
        self.music_master_song_list = [dict(zip(keys, sublst)) for sublst in self.music_id3_metadata_list]

        # Save MusicMasterSongList Dictionary
        with open('MusicMasterSongList.txt', 'w') as master_list_file:
            json.dump(self.music_master_song_list, master_list_file)

        # Create and save a file list size value to check if MusicMasterSongList has changed after a reboot
        list_size = len(self.music_master_song_list)
        with open('MusicMasterSongListCheck.txt', 'w') as check_file:
            json.dump(list_size, check_file)

    def play_song(self, song_file_name):
        """Play a song using VLC media player"""
        print(psutil.virtual_memory())
        # Get the current garbage collection state
        print("Garbage collection thresholds:", gc.get_threshold())

        # Perform garbage collection
        collected = gc.collect()
        print("Garbage collector: collected", "%d objects." % collected)

        # VLC Song Playback Code Begin
        p = vlc.MediaPlayer(song_file_name)
        p.play()
        print('is_playing:', p.is_playing())  # 0 = False
        time.sleep(self.SLEEP_TIME)  # sleep because it needs time to start playing
        print('is_playing:', p.is_playing())  # 1 = True

        while p.is_playing():
            time.sleep(self.SLEEP_TIME)  # sleep to use less CPU
        # VLC Song Playback Code End

    def assign_genres_to_random_play(self):
        """Load and assign genres from GenreFlagsList file"""
        extract_original_assigned_genres = []
        unfiltered_final_genre_list = []

        with open('GenreFlagsList.txt', 'r') as genre_flags_file:
            genre_flags_list = json.load(genre_flags_file)

        self.genre0 = genre_flags_list[0]
        self.genre1 = genre_flags_list[1]
        self.genre2 = genre_flags_list[2]
        self.genre3 = genre_flags_list[3]

        # Extract genres from all songs
        for song in self.music_master_song_list:
            extract_original_assigned_genres.append(song['comment'])

        # Split multi-genre selections
        for genre_string in extract_original_assigned_genres:
            if ' ' in genre_string:
                split_genres = genre_string.split()
                extract_original_assigned_genres.extend(split_genres)

        # Filter and create final genre list
        for genre in extract_original_assigned_genres:
            if ' ' not in genre:
                unfiltered_final_genre_list.append(genre)

        self.final_genre_list = list(set(unfiltered_final_genre_list))  # removes duplicates
        self.final_genre_list.sort()

        # Print genre information
        print('Genres for Random Play are:')
        genres = [self.genre0, self.genre1, self.genre2, self.genre3]
        for idx, genre in enumerate(genres):
            if genre == 'null':
                print(f'No Genre {idx}')
            else:
                print(genre)

    def generate_random_song_list(self):
        """Generate random song playlist based on genre filters"""
        counter = 0
        for song in self.music_master_song_list:
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

        random.shuffle(self.random_music_playlist)

    def _log_song_play(self, artist, title, play_type):
        """Log a song play event to log file"""
        with open('log.txt', 'a') as log:
            now = self._get_rounded_timestamp()
            log.write('\n' + str(now) + ', ' + str(artist) + ' - ' + str(title) + ', Played ' + play_type + ',')

    def _write_current_song_playing(self, song_location):
        """Write current playing song location to file"""
        with open("CurrentSongPlaying.txt", "w") as outfile:
            outfile.write(song_location)

    def jukebox_engine(self):
        """
        Main jukebox engine - plays paid songs first, then random songs

        IMPORTANT: This method uses while loops instead of recursion to prevent
        stack overflow when processing long playlists. The original version had
        recursive calls at the end of playback loops which could cause crashes
        with large music libraries.
        """
        # Load paid music playlist
        with open('PaidMusicPlayList.txt', 'r') as paid_list_file:
            self.paid_music_playlist = json.load(paid_list_file)

        # Play all paid songs using while loop (not recursion)
        while self.paid_music_playlist:
            song_index = self.paid_music_playlist[0]
            song = self.music_master_song_list[song_index]

            print('Now Playing: ' + song['title'] + ' - ' + song['artist'] +
                  '  Year:' + song['year'] + ' Length:' + song['duration'] +
                  ' Album:' + song['album'] + '  Genre:' + song['comment'])

            # Save current playing song to disk
            self._write_current_song_playing(song['location'])

            # Log paid song play
            self._log_song_play(song['artist'], song['title'], 'Paid')

            print('Playing Paid Song In Jukebox Engine')
            self.play_song(song['location'])

            # Delete song just played from paid playlist
            del self.paid_music_playlist[0]
            with open('PaidMusicPlayList.txt', 'w') as paid_list_file:
                json.dump(self.paid_music_playlist, paid_list_file)

        # Play all random songs using while loop (not recursion)
        while self.random_music_playlist:
            self.assign_song_data_random()
            print('Now Playing: ' + self.song_name + ' - ' + self.artist_name +
                  '  Year:' + self.song_year + ' Length:' + self.song_duration +
                  ' Album:' + self.album_name + '  Genre:' + self.song_genre)

            # Save current playing song to disk
            song_index = self.random_music_playlist[0]
            self._write_current_song_playing(self.music_master_song_list[song_index]['location'])

            # Log random song play
            self._log_song_play(self.artist_name, self.song_name, 'Random')

            self.play_song(self.music_master_song_list[song_index]['location'])

            # Move song to end of RandomMusicPlaylist
            move_first_list_element = self.random_music_playlist.pop(0)
            self.random_music_playlist.append(move_first_list_element)

    def run(self):
        """Main execution method"""
        # Check to see if MusicMasterSongList exists on disk
        if os.path.exists('MusicMasterSongList.txt'):
            print('Check to see if MusicMasterSongList exists on disk')

            # Count number of files in music directory
            x = len(glob.glob(os.path.join(self.dir_path, 'music', '*.mp3')))
            print(x)

            # Open MusicMasterSongListCheck generated from previous run
            with open('MusicMasterSongListCheck.txt', 'r') as check_file:
                music_master_song_list_check = json.load(check_file)
                y = music_master_song_list_check
                print(y)

            # Check for match
            if x == y:
                print('Match')
                # Open MusicMasterSongList dictionary
                with open('MusicMasterSongList.txt', 'r') as master_list_file:
                    self.music_master_song_list = json.load(master_list_file)

                # MusicMasterSongList matches, run required functions
                self.assign_genres_to_random_play()
                self.generate_random_song_list()
                self.jukebox_engine()
                return

        # If no match or file doesn't exist, regenerate everything
        self.generate_mp3_metadata()
        self.generate_music_master_song_list_dictionary()
        self.assign_genres_to_random_play()
        self.generate_random_song_list()
        self.jukebox_engine()


# Main execution
if __name__ == "__main__":
    jukebox = JukeboxEngine()
    jukebox.run()
