# ============================================================================
# CONVERGENCE JUKEBOX 2026 - GUI INITIALIZATION MODULE
# ============================================================================
# This module initializes the Jukebox GUI application by:
# - Setting up logging
# - Loading configuration files
# - Building the master song and artist lists
# ============================================================================

# ============================================================================
# IMPORTS
# ============================================================================
from calendar import c
from datetime import datetime, timedelta  # required for logging timestamp
from operator import itemgetter
import json
import os
from token import NUMBER
# from PySimpleGUI.PySimpleGUI import _FindElementWithFocusInSubForm
import random
# import PySimpleGUI as sg
import threading
import time
from gc import disable
from operator import itemgetter
from PIL import Image  # Image processing library
from PIL import ImageDraw  # Drawing on images
from PIL import ImageFont  # Font rendering for images
import textwrap  # Text wrapping utility
import sys
import vlc  # VLC media player library for audio playback

# ============================================================================
# GLOBAL VARIABLES INITIALIZATION
# ============================================================================
# Window management variables
global selection_window_number  # Tracks which selection window is active
global jukebox_selection_window  # Reference to the jukebox selection window
global last_song_check  # Tracks the last song checked/played
last_song_check = ""

# Song and credit tracking
global master_songlist_number  # Total number of songs in master list
global credit_amount  # Current credit amount in the jukebox
credit_amount = 0

# Data storage lists
UpcomingSongPlayList = []  # Queue of upcoming songs to be played
all_songs_list = []  # Complete list of all songs (populated from master list)
all_artists_list = []  # List of all unique artists

# Get the directory path where this script is located
dir_path = os.path.dirname(os.path.realpath(__file__))

# ============================================================================
# LOGGING SETUP - Create/Append to log.txt
# ============================================================================
# Generate current timestamp with rounded-off microseconds
now = datetime.now()
rounded_now = now + timedelta(seconds=0.5)
rounded_now = rounded_now.replace(microsecond=0)  # Remove microseconds
now = rounded_now

# Create log.txt if it doesn't exist, otherwise append to existing log
if not os.path.exists('log.txt'):
    with open('log.txt', 'w') as log:
        log.write(str(now) + ' Jukebox GUI Started - New Log File Created,')
else:
    with open('log.txt', 'a') as log:
        log.write('\n' + str(now) + ', Jukebox GUI Restarted,')

# ============================================================================
# CONFIGURATION FILES SETUP
# ============================================================================
# Create the_bands.txt - contains band names that need special formatting
# These bands will be processed by the application's formatting logic
if not os.path.exists('the_bands.txt'):
    with open('the_bands.txt', 'w') as TheBandsTextOpen:
        # Band names to have special processing applied, stored as comma-separated lowercase
        TheBandsText = "beatles,rolling stones,who,doors,byrds,beachboys"
        json.dump(TheBandsText, TheBandsTextOpen)

# Create the_exempted_bands.txt - contains band names that should NOT be formatted
# These bands are exceptions to the normal formatting rules
if not os.path.exists('the_exempted_bands.txt'):
    with open('the_exempted_bands.txt', 'w') as TheExemptedBandsTextOpen:
        # Band names to be exempted from formatting, stored in proper case on separate lines
        TheExemptedBandsText = "Place Band Names Here In Proper Case With Each Band Placed On Separate Line With No Quotes"
        json.dump(TheExemptedBandsText, TheExemptedBandsTextOpen)

# ============================================================================
# LOAD MASTER SONG LIST FROM JSON FILE
# ============================================================================
# Read MusicMasterSongList.txt which contains all songs in JSON format
# Expected format: List of dictionaries with song metadata (title, artist, path, etc.)
with open('MusicMasterSongList.txt', 'r') as MusicMasterSongListOpen:
    MusicMasterSongList = json.load(MusicMasterSongListOpen)

# Sort the master list by 'artist' key for organizational purposes
MusicMasterSongList = sorted(MusicMasterSongList, key=itemgetter('artist'))

# Reload and sort again (creates a separate sorted dictionary)
with open('MusicMasterSongList.txt', 'r') as MusicMasterSongListOpen:
    MusicMasterSongList = json.load(MusicMasterSongListOpen)

# Create sorted dictionary version (sorted by artist)
MusicMasterSongDict = sorted(MusicMasterSongList, key=itemgetter('artist'))

# ============================================================================
# BUILD ALL SONGS LIST
# ============================================================================
# Get the total count of songs in the master list
master_songlist_number = len(MusicMasterSongDict)

# Iterate through each song in the master list
counter = 0
for counter in range(master_songlist_number):
    # Convert each song dictionary to a list of values and add to all_songs_list
    all_songs_list.append(list(MusicMasterSongDict[counter].values()))

# Clear the sorted dictionary to free memory (multiply by 0 clears it)
MusicMasterSongDict *= 0

# ============================================================================
# BUILD ALL ARTISTS LIST
# ============================================================================
# Get the total count of songs (same as master list count)
artist_songlist_number = len(all_songs_list)

counter = 0
# Extract artist names from each song entry (artist is at index 3)
for counter in range(artist_songlist_number):
    all_artists_list.append(all_songs_list[counter][3])

# Clear all_songs_list to free memory
all_songs_list *= 0

# ============================================================================
# PROCESS AND FINALIZE ARTISTS LIST
# ============================================================================
# Remove duplicate artists by converting to set then back to list
# Reference: https://bit.ly/4cZ7A6R
all_artists_list = list(set(all_artists_list))

# Sort the artists list alphabetically for easier searching/browsing
all_artists_list = sorted(all_artists_list)

# Create a find_list reference to the sorted artists list (used for searching)
find_list = all_artists_list

# ============================================================================
# DEBUG OUTPUT
# ============================================================================
# Print the master song list to console for debugging/verification
print(MusicMasterSongList)
print(all_artists_list)

# ============================================================================
# BACKGROUND THREAD CONFIGURATION CONSTANTS
# ============================================================================
# These constants define the behavior of background monitoring threads
# Modify these values to change thread behavior without editing function code

# Default update interval in seconds (time between each poll/check)
# Increase for less frequent updates (lower CPU usage)
# Decrease for more frequent updates (more responsive UI)
DEFAULT_POLL_INTERVAL = 3

# Event key for song playback lookup thread
# This unique key identifies the event in the GUI window's event queue
EVENT_KEY_SONG_LOOKUP = '--SONG_PLAYING_LOOKUP--'

# Counter value to send with the event
# This can be modified to pass different data to the event handler
DEFAULT_COUNTER_VALUE = 1

# ============================================================================
# GENERIC BACKGROUND POLLING THREAD FUNCTION
# ============================================================================
# Purpose: Reusable background thread that sends periodic update events
#          to a GUI window. Can be used for any polling/monitoring task.
#
# Source: Code developed from Python GUIs - "The Official PySimpleGUI Course"
#         https://www.udemy.com/course/pysimplegui/learn/lecture/30070620
# ============================================================================

def generic_polling_thread(window, event_key, poll_interval=DEFAULT_POLL_INTERVAL, event_data=None):
    """
    Generic background thread function for periodic GUI updates via polling.

    This is a reusable function that can be used to create background threads
    for various monitoring/polling tasks. Each thread periodically sends a custom
    event to the GUI window to trigger updates.

    Args:
        window (PySimpleGUI.Window): The GUI window object that receives events
        event_key (str): Unique identifier for the event (e.g., '--SONG_LOOKUP--')
        poll_interval (int, optional): Seconds to sleep between polls (default: 3)
        event_data (any, optional): Data to pass with the event (default: None)

    Returns:
        None (runs indefinitely until interrupted)

    Example:
        # In main application:
        thread = threading.Thread(
            target=generic_polling_thread,
            args=(main_window, '--CHECK_STATUS--', 5, 'status_check'),
            daemon=True
        )
        thread.start()
    """
    try:
        # Run indefinitely in the background
        while True:
            # Sleep for the specified interval to avoid excessive CPU usage
            # This balances between responsiveness and resource efficiency
            time.sleep(poll_interval)

            # Send a custom event to the GUI window
            # write_event_value() queues an asynchronous event that the main
            # event loop will process when ready
            #
            # Parameters:
            #   - event_key: Unique identifier used by window event handler
            #   - event_data: Data passed with the event (can be any type)
            window.write_event_value(event_key, event_data)

    except KeyboardInterrupt:
        # Gracefully handle user interruption (Ctrl+C)
        # Thread exits cleanly without throwing an error
        pass


# ============================================================================
# SONG LOOKUP THREAD FUNCTION (MODULAR VERSION)
# ============================================================================
# Purpose: Specific implementation that monitors for song playback changes
#          Uses the generic polling thread function for flexibility
# ============================================================================

def file_lookup_thread(song_playing_lookup_window, poll_interval=DEFAULT_POLL_INTERVAL):
    """
    Background thread function that monitors for song playback changes.

    This function runs continuously in a separate thread and periodically sends
    update events to the GUI window to refresh the display with current song
    information. This is a modular wrapper around the generic polling function.

    Args:
        song_playing_lookup_window (PySimpleGUI.Window): The main GUI window object
                                                         that will receive update events
        poll_interval (int, optional): Seconds between polls (default: 3 seconds)

    Returns:
        None (runs until interrupted)

    Usage:
        thread = threading.Thread(
            target=file_lookup_thread,
            args=(main_window,),
            daemon=True
        )
        thread.start()

        # Custom interval example:
        thread = threading.Thread(
            target=file_lookup_thread,
            args=(main_window, 5),  # Check every 5 seconds instead of 3
            daemon=True
        )
        thread.start()
    """
    # Call the generic polling function with song-specific parameters
    # This makes it easy to modify behavior by changing the constants above
    generic_polling_thread(
        window=song_playing_lookup_window,
        event_key=EVENT_KEY_SONG_LOOKUP,
        poll_interval=poll_interval,
        event_data=f'counter = {DEFAULT_COUNTER_VALUE}'
    )
