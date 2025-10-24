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
