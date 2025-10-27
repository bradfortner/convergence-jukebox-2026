# ============================================================================
# CONVERGENCE JUKEBOX 2026 - GUI INITIALIZATION MODULE
# ============================================================================
# This module initializes the Jukebox GUI application by:
# - Setting up logging
# - Loading configuration files
# - Building the master song and artist lists
# - Importing background thread functions from separate module
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
# IMPORT FUNCTIONS FROM SEPARATE MODULES
# ============================================================================
# Import background thread functions from the dedicated thread_functions module
# This keeps thread logic separate from initialization logic (modular design)
from thread_functions import file_lookup_thread

# Import GUI layout functions from the dedicated gui_layouts module
# This keeps layout/presentation logic separate from initialization logic
from gui_layouts import title_bar

# Import background image data from the dedicated background_image_data module
# This keeps large image data separate from initialization logic
from background_image_data import get_background_image

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
# USAGE EXAMPLE: How to use the imported thread function
# ============================================================================
# To use the file_lookup_thread in your main GUI code:
#
# Example 1: Basic usage
#   thread = threading.Thread(target=file_lookup_thread, args=(main_window,))
#   thread.daemon = True
#   thread.start()
#
# Example 2: With explicit daemon setting
#   lookup_thread = threading.Thread(
#       target=file_lookup_thread,
#       args=(song_playing_lookup_window,),
#       daemon=True
#   )
#   lookup_thread.start()
# ============================================================================

def main():
    # Import FreeSimpleGUI (drop-in replacement for PySimpleGUI)
    import FreeSimpleGUI as sg

    # Import modular functions with aliases to avoid shadowing
    from disable_a_selection_buttons import disable_a_selection_buttons as disable_a_impl
    from disable_b_selection_buttons import disable_b_selection_buttons as disable_b_impl
    from disable_c_selection_buttons import disable_c_selection_buttons as disable_c_impl
    from disable_numbered_selection_buttons import disable_numbered_selection_buttons as disable_numbered_impl
    from enable_numbered_selection_buttons import enable_numbered_selection_buttons as enable_numbered_impl
    from enable_all_buttons import enable_all_buttons as enable_all_impl
    from the_bands_name_check import the_bands_name_check as the_bands_check_impl
    from selection_buttons_update import selection_buttons_update as selection_update_impl
    from selection_entry_complete import selection_entry_complete as selection_complete_impl
    from upcoming_selections_update import upcoming_selections_update as upcoming_update_impl

    selection_window_number = 0  # Used to frame initial selection buttons
    selection_entry = ""  # Used for selection entry

    # Wrapper function for disable_a_selection_buttons (calls imported breakdown module)
    def disable_a_selection_buttons():
        disable_a_impl(jukebox_selection_window, control_button_window)
    def disable_b_selection_buttons():
        disable_b_impl(jukebox_selection_window, control_button_window)
    def disable_c_selection_buttons():
        disable_c_impl(jukebox_selection_window, control_button_window)
    def disable_numbered_selection_buttons():
        disable_numbered_impl(control_button_window)
    def selection_buttons_update(selection_window_number):
        return selection_update_impl(selection_window_number, jukebox_selection_window, right_arrow_selection_window, left_arrow_selection_window, MusicMasterSongList, dir_path)
    def the_bands_name_check():
        the_bands_check_impl(jukebox_selection_window, dir_path)
    def enable_numbered_selection_buttons():
        enable_numbered_impl(control_button_window)
    def enable_all_buttons():
        enable_all_impl(jukebox_selection_window, control_button_window) 
    def selection_entry_complete(selection_entry_letter, selection_entry_number):
        return selection_complete_impl(selection_entry_letter, selection_entry_number, jukebox_selection_window, control_button_window)
    def upcoming_selections_update():
        upcoming_update_impl(info_screen_window, UpcomingSongPlayList)
    #  essential code for background image placement and transparent windows placed overtop from https://www.pysimplegui.org/en/latest/Demos/#demo_window_background_imagepy
    background_layout = [title_bar('This is the titlebar', sg.theme_text_color(), sg.theme_background_color()),
                         [sg.Image(data=background_image)]]
    window_background = sg.Window('Background', background_layout, return_keyboard_events=True, use_default_focus=False,no_titlebar=True, finalize=True, margins=(0, 0),
                                  element_padding=(0, 0), right_click_menu=[[''], ['Exit', ]])
    window_background['--BG--'].expand(True, False,
                                    False)  # expand the titlebar's rightmost column so that it resizes correctly
    song_playing_lookup_layout = [[sg.Text()]]
    info_screen_layout = [
        [sg.Text(text="Now Playing", border_width=0, pad=(0, 0), size=(18, 1), justification="center",
             text_color='SeaGreen3', font='Helvetica 20 bold')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(20, 1), justification="center",
                 text_color='White', font='Helvetica 18 bold', key='--song_title--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(24, 1), justification="center",
                 text_color='White', font='Helvetica 16 bold', key='--song_artist--')],
        [sg.Text(text='  Mode: Playing Song', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3', font='Helvetica 12 bold')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3', font='Helvetica 12 bold', key='--mini_song_title--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3', font='Helvetica 12 bold', key='--mini_song_artist--')],
        [sg.Text(text='  Year:        Length:     ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3', font='Helvetica 12 bold', key='--year--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1),
             justification="left", text_color='SeaGreen3', font='Helvetica 12 bold', key='--album--')],
        [sg.Text(text='Upcoming Selections', border_width=0, pad=(0, 0), size=(20, 1), justification="center",
                 text_color='SeaGreen3', font='Helvetica 18 bold')],
        [sg.Text(text='', border_width=0, pad=(0, 0), size=(28, 1), justification="left", text_color='SeaGreen1',
                  font='Helvetica 2 bold')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3',  font='Helvetica 12 bold', key='--upcoming_one--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3',  font='Helvetica 12 bold', key='--upcoming_two--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3',  font='Helvetica 12 bold',key='--upcoming_three--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1),
                 justification="left", text_color='SeaGreen3', font='Helvetica 12 bold', key='--upcoming_four--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3',  font='Helvetica 12 bold', key='--upcoming_five--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1),
                 justification="left", text_color='SeaGreen3', font='Helvetica 12 bold', key='--upcoming_six--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3',  font='Helvetica 12 bold', key='--upcoming_seven--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3',  font='Helvetica 12 bold', key='--upcoming_eight--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left",
                 text_color='SeaGreen3',  font='Helvetica 12 bold', key='--upcoming_nine--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1),
                 justification="left", text_color='SeaGreen3', font='Helvetica 12 bold', key='--upcoming_ten--')],
        [sg.Text(text=' ', border_width=0, pad=(0, 0), size=(28, 1), justification="left", text_color='SeaGreen1',
                  font='Helvetica 2 bold')],
        [sg.Text(text='CREDITS 0', border_width=0, pad=(0, 0), size=(19, 1), justification="center", text_color='White',
                  font='Helvetica 20 bold', key='--credits--')],
        [sg.Text(text='Twenty-Five Cents Per Selection', border_width=0, pad=(0, 0), size=(30, 1),
                 justification="center", text_color='SeaGreen3', font='Helvetica 12 bold')],
        [sg.Text(text=str(master_songlist_number) + ' Song Selections Available', border_width=0, pad=(0, 0), size=(30, 1),
                 justification="center", text_color='SeaGreen3', font='Helvetica 12 bold')]
                     ]
    jukebox_selection_screen_layout = [
        [sg.Button(button_text="A1", key='--A1--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0), font='Helvetica 16 bold'),
        sg.Button(button_text=MusicMasterSongList[selection_window_number]['title'][:22], size=(22, 1),
                   key='--button0_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
        sg.Button(button_text="B1", key='--B1--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
        sg.Button(button_text=MusicMasterSongList[selection_window_number + 14]['title'][:22], size=(22, 1),
                   key='--button7_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
        sg.Button(button_text="C1", key='--C1--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
        sg.Button(button_text=MusicMasterSongList[selection_window_number + 28]['title'][:22], size=(22, 1),
                   key='--button14_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white',
                   font='Helvetica 12 bold')],
        [sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number]['artist'][:22], size=(22, 1),
                   key='--button0_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)),button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 14]['artist'][:22], size=(22, 1),
                   key='--button7_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 28]['artist'][:22], size=(22, 1),
                   key='--button14_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold')],
        [sg.Button(button_text="A2", key='--A2--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 2]['title'][:22], size=(22, 1),
                   key='--button1_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="B2", key='--B2--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 16]['title'][:22], size=(22, 1),
                   key='--button8_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="C2", key='--C2--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 30]['title'][:22], size=(22, 1),
                   key='--button15_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold')],
        [sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 2]['artist'][:22], size=(22, 1),
                   key='--button1_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 16]['artist'][:22], size=(22, 1),
                   key='--button8_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 30]['artist'][:22], size=(22, 1),
                   key='--button15_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold')],
        [sg.Button(button_text="A3", key='--A3--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 4]['title'][:22], size=(22, 1),
                   key='--button2_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="B3", key='--B3--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 18]['title'][:22], size=(22, 1),
                   key='--button9_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="C3", key='--C3--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 32]['title'][:22], size=(22, 1),
                   key='--button16_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold')],
        [sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 4]['artist'][:22], size=(22, 1),
                   key='--button2_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 18]['artist'][:22], size=(22, 1),
                   key='--button9_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 32]['artist'][:22], size=(22, 1),
                   key='--button16_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold')],
        [sg.Button(button_text="A4", key='--A4--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 6]['title'][:22], size=(22, 1),
                   key='--button3_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="B4", key='--B4--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 20]['title'][:22], size=(22, 1),
                   key='--button10_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="C4", key='--C4--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 34]['title'][:22], size=(22, 1),
                   key='--button17_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold')],
        [sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 6]['artist'][:22], size=(22, 1),
                   key='--button3_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 20]['artist'][:22], size=(22, 1),
                   key='--button10_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 34]['artist'][:22], size=(22, 1),
                   key='--button17_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold')],
        [sg.Button(button_text="A5", key='--A5--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 8]['title'][:22], size=(22, 1),
                   key='--button4_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="B5", key='--B5--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 22]['title'][:22], size=(22, 1),
                   key='--button11_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="C5", key='--C5--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 36]['title'][:22], size=(22, 1),
                   key='--button18_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold')],
        [sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 8]['artist'][:22], size=(22, 1),
                   key='--button4_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 22]['artist'][:22], size=(22, 1),
                   key='--button11_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 36]['artist'][:22], size=(22, 1),
                   key='--button18_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold')],
        [sg.Button(button_text="A6", key='--A6--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 10]['title'][:22], size=(22, 1),
                   key='--button5_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="B6", key='--B6--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number +24]['title'][:22], size=(22, 1),
                   key='--button12_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="C6", key='--C6--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 38]['title'][:22], size=(22, 1),
                   key='--button19_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold')],
        [sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 10]['artist'][:22], size=(22, 1),
                   key='--button5_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 24]['artist'][:22], size=(22, 1),
                   key='--button12_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 38]['artist'][:22], size=(22, 1),
                   key='--button19_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold')],
        [sg.Button(button_text="A7", key='--A7--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 12]['title'][:22], size=(22, 1),
                   key='--button6_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="B7", key='--B7--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 26]['title'][:22], size=(22, 1),
                   key='--button13_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text="C7", key='--C7--', size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_bg.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 40]['title'][:22], size=(22, 1),
                   key='--button20_top--', image_filename=dir_path + '/images/new_selection_top_bg.png', border_width=0,
                   pad=(0, 0), button_color='black on white', font='Helvetica 12 bold')],
        [sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 12]['artist'][:22], size=(22, 1),
                   key='--button6_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, pad=(0, (0, 0)), button_color='black on white', font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 26]['artist'][:22], size=(22, 1),
                   key='--button13_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold'),
         sg.Button(button_text=" ", size=(30, 26), image_size=(30, 26),
                   image_filename=dir_path + '/images/button_id_black_bg.png',
                   border_width=0, pad=(0, 0), font='Helvetica 11 bold'),
         sg.Button(button_text=MusicMasterSongList[selection_window_number + 40]['artist'][:22], size=(22, 1),
                   key='--button20_bottom--', image_filename=dir_path + '/images/new_selection_top_bg.png',
                   border_width=0, button_color='black on white', pad=(0, (0, 0)), font='Helvetica 12 bold')],
        # 22 char Limit
        ]
    right_arrow_screen_layout = [
        [sg.Button(button_text="", key='--selection_right--', size=(100, 47), image_size=(100, 47),
                   image_filename=dir_path + '/images/lg_arrow_right.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold')]]
    left_arrow_screen_layout = [
        [sg.Button(button_text="", key='--selection_left--', size=(100, 47), image_size=(100, 47),
                   image_filename=dir_path + '/images/lg_arrow_left.png', border_width=0, pad=(0, 0),
                   font='Helvetica 16 bold')]]
    control_button_screen_layout = [
        [sg.Button(size=(35, 25), image_size=(35, 25), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--A--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/a_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--B--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/b_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--C--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/c_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--1--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/1_button.png', disabled=True),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--2--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/2_button.png', disabled=True)],
        [sg.Button(size=(50, 25), image_size=(50, 25), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(150, 50), image_size=(150, 50), key='--correct--', pad=(0, 0), border_width=0,
                   font='Helvetica 38', image_filename=dir_path + '/images/correct_button.png'),
         sg.Button(size=(35, 25), image_size=(35, 25), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--3--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/3_button.png', disabled=True),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--4--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/4_button.png', disabled=True),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--5--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/5_button.png', disabled=True),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--6--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/6_button.png', disabled=True),
         sg.Button(size=(50, 50), image_size=(50, 50), key='--7--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/7_button.png', disabled=True),
         sg.Button(size=(35, 25), image_size=(35, 25), key='--blank--', pad=(0, 0), border_width=0, font='Helvetica 38',
                   image_filename=dir_path + '/images/blank_button.png'),
         sg.Button(size=(150, 50), image_size=(150, 50), key='--select--', pad=(0, 0), disabled=True, border_width=0,
                   font='Helvetica 38', image_filename=dir_path + '/images/select_button.png'),
         ]]
    title_search_screen_layout = [[sg.Button('Welcome To Title Search', key = "--TITLE_SEARCH--")]]
    artist_search_screen_layout = [[sg.Button('Welcome To Artist Search', key = "--ARTIST_SEARCH--")]]    
    right_arrow_selection_window = sg.Window('Right Arrow', right_arrow_screen_layout, finalize=True,
        keep_on_top=True, transparent_color=sg.theme_background_color(), no_titlebar=True,
        relative_location=(425, -180),return_keyboard_events=True, use_default_focus=False)
    left_arrow_selection_window = sg.Window('Left Arrow', left_arrow_screen_layout, finalize=True,
        keep_on_top=True, transparent_color=sg.theme_background_color(), no_titlebar=True,
        relative_location=(-85, -180),return_keyboard_events=True, use_default_focus=False)
    jukebox_selection_window = sg.Window('Jukebox Selection Screen', jukebox_selection_screen_layout,
                finalize=True, keep_on_top=True, transparent_color=sg.theme_background_color(),
                no_titlebar=True, relative_location=(162,56),return_keyboard_events=True,
                use_default_focus=False)
    info_screen_window = sg.Window('Info Screen', info_screen_layout, finalize=True, keep_on_top=True,
                transparent_color=sg.theme_background_color(), no_titlebar=True,
                element_padding=((0, 0), (0, 0)), relative_location=(-448, 0),return_keyboard_events=True, use_default_focus=False)
    control_button_window = sg.Window('Control Screen', control_button_screen_layout, finalize=True,
                keep_on_top=True, transparent_color=sg.theme_background_color(), no_titlebar=True,return_keyboard_events=True, use_default_focus=False, element_padding=((0, 0), (0, 0)), relative_location=(150, 306))
    song_playing_lookup_window = sg.Window('Song Playing Lookup Thread', song_playing_lookup_layout, no_titlebar=True, finalize=True,return_keyboard_events=True, use_default_focus=False)
    title_search_window = sg.Window('Title Search Window', title_search_screen_layout, finalize=True,
                keep_on_top=True, transparent_color=sg.theme_background_color(),
                no_titlebar=True, relative_location=(415,280),return_keyboard_events=True, use_default_focus=False)
    artist_search_window = sg.Window('Artist Search Window', artist_search_screen_layout, finalize=True,
                keep_on_top=True, transparent_color=sg.theme_background_color(),
                no_titlebar=True, relative_location=(-60,280),return_keyboard_events=True, use_default_focus=False)
    the_bands_name_check()
    threading.Thread(target=file_lookup_thread, args=(song_playing_lookup_window,), daemon=True).start()
    # Main Jukebox GUI
    while True:        
        window, event, values = sg.read_all_windows()
        print(event, values)
        print(event)  # prints buttons key name
        if (event) == "--selection_right--" or (event) == 'Right:39':
            selection_window_number = selection_window_number + 21
            selection_buttons_update(selection_window_number)
        if (event) == "--selection_left--" or (event) == 'Left:37':
            selection_window_number = selection_window_number - 21
            selection_buttons_update(selection_window_number)
        # Code to initiate search for title or artist
        if (event) == "--TITLE_SEARCH--" or (event) == "T" or (event) == "--ARTIST_SEARCH--" or (event) == "A":
            if (event) == "--TITLE_SEARCH--" or (event) == "T":
                search_flag = "title"
            if (event) == "--ARTIST_SEARCH--" or (event) == "A":
                search_flag = "artist"
            # Hide jukebox interface and bring up title search interface
            right_arrow_selection_window.Hide()
            left_arrow_selection_window.Hide()
            jukebox_selection_window.Hide()
            info_screen_window.Hide()
            control_button_window.Hide()
            song_playing_lookup_window.Hide()
            window_background.Hide()
            # Search Windows Button Layout
            search_window_button_layout = ([[sg.Text("", font="Helvetica 8", s=(55, 1), background_color="black"),
                      sg.Button("", s=(1, 1), disabled=True, image_size=(439, 226), image_filename="jukebox_2025_logo.png",
                      button_color=["black", "white"], font="Helvetica 16 bold",),],
           [sg.Text("", font="Helvetica 8", s=(30, 1), background_color="black")],
           [sg.Text("", font="Helvetica 8", s=(38, 1), background_color="black"),
            sg.Text("Search For Title", p=None, font="Helvetica 16 bold", background_color="white", text_color="black",
                    k="--search_type--",),
            sg.Button("", s=(1, 1), disabled=True, image_size=(25, 25), image_filename="magglass.png",
                      button_color=["black", "white"], font="Helvetica 16 bold", ),
            sg.Text("", font="Helvetica 16 bold", k="--letter_entry--", s=(35, 1), background_color="white", text_color="black",),
            sg.Text("", font="Helvetica 8", s=(30, 1), background_color="black")],
            [sg.Text("", font="Helvetica 8", s=(60, 1), background_color="black")],
            [sg.Text("", font="Helvetica 8", s=(14, 1), background_color="black"),
            sg.Button("1", focus=False, s=(1, 1), border_width=6,),
            sg.Button("2", focus=False, s=(1, 1), border_width=6,),
            sg.Button("3", focus=False, s=(1, 1), border_width=6,),
            sg.Button("4", focus=False, s=(1, 1), border_width=6,),
            sg.Button("5", focus=False, s=(1, 1), border_width=6,),
            sg.Button("6", focus=False, s=(1, 1), border_width=6,),
            sg.Button("7", focus=False, s=(1, 1), border_width=6,),
            sg.Button("8", focus=False, s=(1, 1), border_width=6,),
            sg.Button("9", focus=False, s=(1, 1), border_width=6,),
            sg.Button("0", focus=False, s=(1, 1), border_width=6,),
            sg.Button("-", focus=False, s=(1, 1), border_width=6,),
            sg.Text("", font="Helvetica 8", s=(2, 1), background_color="black"),
            
            sg.Button("", s=(34, 1), visible=False, border_width=6, button_color=["white", "black"], k="--result_one--",
                      disabled_button_color="black",),],
                      
            [sg.Text("", font="Helvetica 8", s=(14, 1), background_color="black"),
            sg.Button("A", focus=False, size=(1, 1), key="--A--", button_color=["firebrick4", "goldenrod1"], border_width=6, font="Helvetica 16 bold",), 
            sg.Button("B", s=(1, 1), border_width=6,),
            sg.Button("C", s=(1, 1), border_width=6,),
            sg.Button("D", s=(1, 1), border_width=6,),
            sg.Button("E", s=(1, 1), border_width=6,),
            sg.Button("F", s=(1, 1), border_width=6,),
            sg.Button("G", s=(1, 1), border_width=6,),
            sg.Button("H", s=(1, 1), border_width=6,),
            sg.Button("I", s=(1, 1), border_width=6,),
            sg.Button("J", s=(1, 1), border_width=6, ),
            sg.Button("K", s=(1, 1), border_width=6,),
            sg.Text("", font="Helvetica 8", s=(2, 1), background_color="black"),
            
            sg.Button("", s=(34, 1), visible=False, border_width=6, button_color=["white", "black"], k="--result_two--",
                      disabled_button_color="black",),],
                      
            [sg.Text("", font="Helvetica 8", s=(14, 1), background_color="black"),
             sg.Button("L", s=(1, 1), border_width=6,),
             sg.Button("M", s=(1, 1), border_width=6,),
             sg.Button("N", s=(1, 1), border_width=6,),
             sg.Button("O", s=(1, 1), border_width=6,),
             sg.Button("P", s=(1, 1), border_width=6,),
             sg.Button("Q", s=(1, 1), border_width=6,),
             sg.Button("R", s=(1, 1), border_width=6,),
             sg.Button("S", s=(1, 1), border_width=6,),
             sg.Button("T", s=(1, 1), border_width=6,),
             sg.Button("U", s=(1, 1), border_width=6,),
             sg.Button("V", s=(1, 1), border_width=6,),
             sg.Text("", font="Helvetica 8", s=(2, 1), background_color="black"),
             sg.Button("", s=(34, 1), visible=False, border_width=6, button_color=["white", "black"], k="--result_three--",
                      disabled_button_color="black", ),],
            [sg.Text("", font="Helvetica 8", s=(14, 1), background_color="black"),
             sg.Button("W", s=(1, 1), border_width=6,),
             sg.Button("X", s=(1, 1), border_width=6, ),
             sg.Button("Y", s=(1, 1), border_width=6,),
             sg.Button("Z", s=(1, 1), border_width=6,),
             sg.Button("'", s=(1, 1), border_width=6,),             
            sg.Button("DELETE LAST ENTRY",  k="--DELETE--", s=(17, 1), border_width=6,),
            sg.Text("", font="Helvetica 8", s=(2, 1), background_color="black"),
            sg.Button("", s=(34, 1), visible=False, border_width=6, button_color=["white", "black"], k="--result_four--",
                      disabled_button_color="black",),],
            [sg.Text("", font="Helvetica 8", s=(14, 1), background_color="black"),
            sg.Button("SPACE",  k="--space--", s=(9, 1), border_width=6,),
            sg.Button("CLEAR",  k="--CLEAR--", s=(9, 1), border_width=6,),
            sg.Button("EXIT",  k="--EXIT--", s=(10, 1), border_width=6,),
            sg.Text("", font="Helvetica 8", s=(1, 1), background_color="black"),
            sg.Button("", s=(34, 1), visible=False, border_width=6, button_color=["white", "black"], k="--result_five--",
                      disabled_button_color="black",),],],)           
            search_window = sg.Window('', search_window_button_layout, modal=True, no_titlebar = True, size = (1280,720),
                default_button_element_size=(5, 2), auto_size_buttons=False, background_color='black', 
                button_color=["firebrick4", "goldenrod1"], font="Helvetica 16 bold", finalize=True)
            search_window['--A--'].set_focus()
            search_window.bind('<Right>', '-NEXT-')
            search_window.bind('<Left>', '-PREV-')
            search_window.bind('<S>', '--SELECTED_LETTER--')
            search_window.bind('<C>', '--DELETE--')
            keys_entered = ''
            search_results = []
            # Set search window to artist if Artist search selected
            if search_flag == "artist":
                search_window["--search_type--"].update("Search For Artist")
            # Keyboard event loop for title search window
            while True:
                event, values = search_window.read()  # read the title_search_window
                print(event, values)
                if event == "-NEXT-" or event == "-PREV-" or event == "--CLEAR--" or event == '--EXIT--':
                    if event == "-NEXT-":
                        next_element = search_window.find_element_with_focus().get_next_focus()
                        next_element.set_focus()
                    if event == "-PREV-":
                        prev_element = search_window.find_element_with_focus().get_previous_focus()
                        prev_element.set_focus()
                    if event == "--CLEAR--":  # clear keys if clear button
                        keys_entered = ""
                        search_results = []
                        search_window["--letter_entry--"].Update(keys_entered)
                        search_window["--result_one--"].update("", visible=False, disabled=False)
                        search_window["--result_two--"].update("", visible=False)
                        search_window["--result_three--"].update("", visible=False)
                        search_window["--result_four--"].update("", visible=False)
                        search_window["--result_five--"].update("", visible=False)
                    if event == "--EXIT--":
                        #  Code to restore main jukebox windows
                        right_arrow_selection_window.UnHide()
                        left_arrow_selection_window.UnHide()
                        jukebox_selection_window.UnHide()
                        info_screen_window.UnHide()
                        control_button_window.UnHide()
                        window_background.UnHide()
                        # Clear search results
                        keys_entered = ""
                        # close title search window                              
                        search_window.close()
                        break
                else:
                    # Code specific to title search
                    if search_flag == "title":
                        if event == "--result_one--" or event == "--result_two--" or event == "--result_three--" or event == "--result_four--" or event == "--result_five--":
                            button_text = search_window[event].get_text()
                            song_search = f'{button_text}'
                            # Code to search for song number
                            for i in range(len(MusicMasterSongList)):                            
                                if song_search == str(MusicMasterSongList[i]['artist'] + ' - ' + str(MusicMasterSongList[i]['title'])):
                                    #Song number found
                                    # Song number assigned to song_selected_number variable
                                    song_selected_number = MusicMasterSongList[i]['number']
                                    # Code to set main jukeox selection window screen for selected song
                                    selection_window_number = song_selected_number
                                    selection_buttons_update(selection_window_number)
                                    # Code to update the main jukebox selection window position A1 to the selected song
                                    jukebox_selection_window['--button0_top--'].update(text = MusicMasterSongList[i]['title'])
                                    jukebox_selection_window['--button0_bottom--'].update(text = MusicMasterSongList[i]['artist'])
                                    # Code to set main main jukebox selection window to selected song
                                    disable_a_selection_buttons()
                                    control_button_window['--A--'].update(disabled=True)
                                    jukebox_selection_window['--button0_top--'].update(disabled = False)
                                    jukebox_selection_window['--button0_bottom--'].update(disabled = False)
                                    control_button_window['--select--'].update(disabled = False)
                                    disable_b_selection_buttons()
                                    disable_c_selection_buttons()
                                    # Requied by the main jukebox selection window
                                    song_selected = "A1" 
                                    # Code to restore main jukebox windows
                                    window_background.UnHide()
                                    right_arrow_selection_window.UnHide()
                                    left_arrow_selection_window.UnHide()
                                    jukebox_selection_window.UnHide()
                                    info_screen_window.UnHide()
                                    control_button_window.UnHide()                                
                                    # Clear search results
                                    keys_entered = ""
                                    # close title search window                              
                                    search_window.close()
                                    break
                            #Skip code that updates main Jukebox windows
                            break                    
                    if search_flag == "artist":
                        if event == "--result_one--" or event == "--result_two--" or event == "--result_three--" or event == "--result_four--" or event == "--result_five--":
                            button_text = search_window[event].get_text()                       
                            song_search = f'{button_text}'
                            #  Locate song number
                            counter = 0   
                            for i in MusicMasterSongList:
                                if song_search in MusicMasterSongList[counter]['artist']:
                                    print('artist looking for is: ' + str(song_search))
                                    print('artist match found')
                                    # Song Number Start Found                                
                                    if len(song_search) == len(MusicMasterSongList[counter]['artist']):
                                        print(MusicMasterSongList[counter]['number'])
                                        # Song number found
                                        #print(find_list[counter])
                                        print("Title Selected is number: " + str(MusicMasterSongList[counter]['number']))
                                        print("Artist Selected is: " + str(MusicMasterSongList[counter]['artist']))
                                        # Song number assigned ot song_selected_number variable
                                        song_selected_number = MusicMasterSongList[counter]['number']
                                        # Code to set main jukeox selection window screen for selected song
                                        selection_window_number = song_selected_number
                                        selection_buttons_update(selection_window_number) 
                                        # Code to restore main jukebox windows
                                        right_arrow_selection_window.UnHide()
                                        left_arrow_selection_window.UnHide()
                                        jukebox_selection_window.UnHide()
                                        info_screen_window.UnHide()
                                        control_button_window.UnHide()
                                        window_background.UnHide()
                                        # Clear search results
                                        keys_entered = ""
                                        # close artist search window                              
                                        search_window.close()
                                        break
                                    else:
                                        pass
                                counter += 1                            
                            #Skip code that updates main Jukebox windows                           
                            break  
                    if event == sg.WIN_CLOSED:  # if the X button clicked, just exit
                        break
                    # Code to update the search results based on the keys entered via the keypad                                         
                    if (event) == "--SELECTED_LETTER--":
                        selected_letter_entry = search_window.find_element_with_focus()
                        selected_letter_entry.Click()
                        # key_entry(keys_entered)
                        if event == "A":
                            keys_entered = keys_entered + "A"
                        if event == "B":
                            keys_entered = keys_entered + "B"
                        if event == "C":
                            keys_entered = keys_entered + "C"
                        if event == "D":
                            keys_entered = keys_entered + "D"
                        if event == "E":
                            keys_entered = keys_entered + "E"
                        if event == "F":
                            keys_entered = keys_entered + "F"
                        if event == "G":
                            keys_entered = keys_entered + "G"
                        if event == "H":
                            keys_entered = keys_entered + "H"
                        if event == "I":
                            keys_entered = keys_entered + "I"
                        if event == "J":
                            keys_entered = keys_entered + "J"
                        if event == "K":
                            keys_entered = keys_entered + "K"
                        if event == "L":
                            keys_entered = keys_entered + "L"
                        if event == "M":
                            keys_entered = keys_entered + "M"
                        if event == "N":
                            keys_entered = keys_entered + "N"
                        if event == "O":
                            keys_entered = keys_entered + "O"
                        if event == "P":
                            keys_entered = keys_entered + "P"
                        if event == "Q":
                            keys_entered = keys_entered + "Q"
                        if event == "R":
                            keys_entered = keys_entered + "R"
                        if event == "S":
                            keys_entered = keys_entered + "S"
                        if event == "T":
                            keys_entered = keys_entered + "T"
                        if event == "U":
                            keys_entered = keys_entered + "U"
                        if event == "V":
                            keys_entered = keys_entered + "V"
                        if event == "W":
                            keys_entered = keys_entered + "W"
                        if event == "X":
                            keys_entered = keys_entered + "X"
                        if event == "Y":
                            keys_entered = keys_entered + "Y"
                        if event == "Z":
                            keys_entered = keys_entered + "Z"
                        if event == "1":
                            keys_entered = keys_entered + "1"
                        if event == "2":
                            keys_entered = keys_entered + "2"
                        if event == "3":
                            keys_entered = keys_entered + "3"
                        if event == "4":
                            keys_entered = keys_entered + "4"
                        if event == "5":
                            keys_entered = keys_entered + "5"
                        if event == "6":
                            keys_entered = keys_entered + "6"
                        if event == "7":
                            keys_entered = keys_entered + "7"
                        if event == "8":
                            keys_entered = keys_entered + "8"
                        if event == "9":
                            keys_entered = keys_entered + "9"
                        if event == "0":
                            keys_entered = keys_entered + "0"
                    if event == "--DELETE--":
                        keys_entered = keys_entered[:-1]
                    if event == "--space--":
                        keys_entered += " "
                    elif event == "-":
                        keys_entered += "-"
                    elif event == "'":
                        keys_entered += "'"
                    # Code to update the search results based on the keys entered via a computer keyboard or mouse
                    elif event in "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                        print(event, values)
                        if event == "B":
                            keys_entered = keys_entered + "B"
                        if event == "C":
                            keys_entered = keys_entered + "C"
                        if event == "D":
                            keys_entered = keys_entered + "D"
                        if event == "E":
                            keys_entered = keys_entered + "E"
                        if event == "F":
                            keys_entered = keys_entered + "F"
                        if event == "G":
                            keys_entered = keys_entered + "G"
                        if event == "H":
                            keys_entered = keys_entered + "H"
                        if event == "I":
                            keys_entered = keys_entered + "I"
                        if event == "J":
                            keys_entered = keys_entered + "J"
                        if event == "K":
                            keys_entered = keys_entered + "K"
                        if event == "L":
                            keys_entered = keys_entered + "L"
                        if event == "M":
                            keys_entered = keys_entered + "M"
                        if event == "N":
                            keys_entered = keys_entered + "N"
                        if event == "O":
                            keys_entered = keys_entered + "O"
                        if event == "P":
                            keys_entered = keys_entered + "P"
                        if event == "Q":
                            keys_entered = keys_entered + "Q"
                        if event == "R":
                            keys_entered = keys_entered + "R"
                        if event == "S":
                            keys_entered = keys_entered + "S"
                        if event == "T":
                            keys_entered = keys_entered + "T"
                        if event == "U":
                            keys_entered = keys_entered + "U"
                        if event == "V":
                            keys_entered = keys_entered + "V"
                        if event == "W":
                            keys_entered = keys_entered + "W"
                        if event == "X":
                            keys_entered = keys_entered + "X"
                        if event == "Y":
                            keys_entered = keys_entered + "Y"
                        if event == "Z":
                            keys_entered = keys_entered + "Z"
                        if event == "1":
                            keys_entered = keys_entered + "1"
                        if event == "2":
                            keys_entered = keys_entered + "2"
                        if event == "3":
                            keys_entered = keys_entered + "3"
                        if event == "4":
                            keys_entered = keys_entered + "4"
                        if event == "5":
                            keys_entered = keys_entered + "5"
                        if event == "6":
                            keys_entered = keys_entered + "6"
                        if event == "7":
                            keys_entered = keys_entered + "7"
                        if event == "8":
                            keys_entered = keys_entered + "8"
                        if event == "9":
                            keys_entered = keys_entered + "9"
                        if event == "0":
                            keys_entered = keys_entered + "0"
                        print(keys_entered)
                    elif event == "Submit":
                        keys_entered = values["input"]
                        search_window["out"].update(keys_entered)  # output the final stringsd
                    if event == "--A--":
                        keys_entered = keys_entered + "A"
                    print(keys_entered)
                    # Code to bring up search results based on keys entered
                    # Code to search for song title based on keys entered
                    if search_flag == "title":                    
                        for i, item in enumerate(MusicMasterSongList):                   
                            find_list_search = MusicMasterSongList[i]['title']
                            match = find_list_search.lower().find(keys_entered.lower())
                            if match == 0:  # ensures match is from left of string
                                search_results.append(str(MusicMasterSongList[i]['artist']) + " - " + str(MusicMasterSongList[i]['title']))
                    # Code to search for artist based on keys entered
                    if search_flag == "artist":                        
                        find_list = all_artists_list
                        print(keys_entered)
                        for i, item in enumerate(find_list):
                            find_list_search = find_list[i]
                            match = find_list_search.lower().find(keys_entered.lower())
                            if match == 0:  # ensures match is from left of string
                                search_results.append(str(find_list[i]))
                    # Code to update search results on search window
                    if len(search_results) <= 5:
                        search_window["--result_one--"].update(visible=True, disabled=False)
                        search_window["--result_two--"].update(visible=True)
                        search_window["--result_three--"].update(visible=True)
                        search_window["--result_four--"].update(visible=True)
                        search_window["--result_five--"].update(visible=True)
                    if len(search_results) <= 4:
                        search_window["--result_one--"].update(visible=True, disabled=False)
                        search_window["--result_two--"].update(visible=True)
                        search_window["--result_three--"].update(visible=True)
                        search_window["--result_four--"].update(visible=True)
                        search_window["--result_five--"].update(visible=False)
                    if len(search_results) <= 3:
                        search_window["--result_one--"].update(visible=True, disabled=False)
                        search_window["--result_two--"].update(visible=True)
                        search_window["--result_three--"].update(visible=True)
                        search_window["--result_four--"].update(visible=False)
                        search_window["--result_five--"].update(visible=False)
                    if len(search_results) <= 2:
                        search_window["--result_one--"].update(visible=True, disabled=False)
                        search_window["--result_two--"].update(visible=True)
                        search_window["--result_three--"].update(visible=False)
                        search_window["--result_four--"].update(visible=False)
                        search_window["--result_five--"].update(visible=False)
                    if len(search_results) <= 1:
                        search_window["--result_one--"].update(visible=True, disabled=False)
                        search_window["--result_two--"].update(visible=False)
                        search_window["--result_three--"].update(visible=False)
                        search_window["--result_four--"].update(visible=False)
                        search_window["--result_five--"].update(visible=False)
                    if len(search_results) == 0:
                        search_window["--result_one--"].update("Song Title Not On Jukebox", disabled=True)
                        search_window["--result_two--"].update(visible=False)
                        search_window["--result_three--"].update(visible=False)
                        search_window["--result_four--"].update(visible=False)
                        search_window["--result_five--"].update(visible=False)
                    for x in range(len(search_results)):
                        if len(search_results) == 0:
                            search_window["--result_one--"].update("", disabled=False)
                            search_window["--result_two--"].update("")
                            search_window["--result_three--"].update("")
                            search_window["--result_four--"].update("")
                            search_window["--result_five--"].update("")
                        if len(search_results) == 1:
                            search_window["--result_one--"].update(search_results[0], disabled=False)
                            search_window["--result_two--"].update("")
                            search_window["--result_three--"].update("")
                            search_window["--result_four--"].update("")
                            search_window["--result_five--"].update("")
                        if len(search_results) == 2:
                            search_window["--result_one--"].update(search_results[0], disabled=False)
                            search_window["--result_two--"].update(search_results[1])
                            search_window["--result_three--"].update("")
                            search_window["--result_four--"].update("")
                            search_window["--result_five--"].update("")
                        if len(search_results) == 3:
                            search_window["--result_one--"].update(search_results[0], disabled=False)
                            search_window["--result_two--"].update(search_results[1])
                            search_window["--result_three--"].update(search_results[2])
                            search_window["--result_four--"].update("")
                            search_window["--result_five--"].update("")
                        if len(search_results) == 4:
                            search_window["--result_one--"].update(search_results[0], disabled=False)
                            search_window["--result_two--"].update(search_results[1])
                            search_window["--result_three--"].update(search_results[2])
                            search_window["--result_four--"].update(search_results[3])
                            search_window["--result_five--"].update("")
                        if len(search_results) == 5:
                            search_window["--result_one--"].update(search_results[0], disabled=False)
                            search_window["--result_two--"].update(search_results[1])
                            search_window["--result_three--"].update(search_results[2])
                            search_window["--result_four--"].update(search_results[3])
                            search_window["--result_five--"].update(search_results[4])
                        if len(search_results) > 5:
                            search_window["--result_one--"].update(keys_entered, disabled=False)
                            search_window["--result_two--"].update(keys_entered)
                            search_window["--result_three--"].update(keys_entered)
                            search_window["--result_four--"].update(keys_entered)
                            search_window["--result_five--"].update(keys_entered)
                search_results = []
                search_window["--letter_entry--"].Update(keys_entered)
                # End of search window event loop code
#  keyboard entry PySimpleGUI
        if event == "--A--" or (event) == "a":
            selection_entry_letter = "A"
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            enable_numbered_selection_buttons()
        if event == "--B--" or (event) == "b":
            selection_entry_letter = "B"
            disable_a_selection_buttons()
            disable_c_selection_buttons()
            enable_numbered_selection_buttons()
        if event == "--C--" or (event) == "c":
            selection_entry_letter = "C"
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            enable_numbered_selection_buttons()
        #if event == "--X--" or (event) == "x":
        if (event) == "x":
            global credit_amount
            credit_amount += 1
            info_screen_window['--credits--'].Update('CREDITS ' + str(credit_amount))            
            # Add credit to log file
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            with open('log.txt', 'a') as log:
                log.write('\n' + str(current_time) + ' Quarter Added,')    
        if event == "--1--" or (event) == "1":
            selection_entry_number = "1"
            disable_numbered_selection_buttons()
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            jukebox_selection_window['--A1--'].update(disabled=False)
            jukebox_selection_window['--button0_top--'].update(disabled=False)
            jukebox_selection_window['--button0_bottom--'].update(disabled=False)
            jukebox_selection_window['--B1--'].update(disabled=False)
            jukebox_selection_window['--button7_top--'].update(disabled=False)
            jukebox_selection_window['--button7_bottom--'].update(disabled=False)
            jukebox_selection_window['--C1--'].update(disabled=False)
            jukebox_selection_window['--button14_top--'].update(disabled=False)
            jukebox_selection_window['--button14_bottom--'].update(disabled=False)
            control_button_window['--A--'].update(disabled=False)
            control_button_window['--B--'].update(disabled=False)
            control_button_window['--C--'].update(disabled=False)
            if selection_entry_letter:
                selection_entry_complete(selection_entry_letter, selection_entry_number)
        if event == "--2--" or (event) == "2":
            selection_entry_number = "2"
            disable_numbered_selection_buttons()
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            jukebox_selection_window['--A2--'].update(disabled=False)
            jukebox_selection_window['--button1_top--'].update(disabled=False)
            jukebox_selection_window['--button1_bottom--'].update(disabled=False)
            jukebox_selection_window['--B2--'].update(disabled=False)
            jukebox_selection_window['--button8_top--'].update(disabled=False)
            jukebox_selection_window['--button8_bottom--'].update(disabled=False)
            jukebox_selection_window['--C2--'].update(disabled=False)
            jukebox_selection_window['--button15_top--'].update(disabled=False)
            jukebox_selection_window['--button15_bottom--'].update(disabled=False)
            control_button_window['--A--'].update(disabled=False)
            control_button_window['--B--'].update(disabled=False)
            control_button_window['--C--'].update(disabled=False)
            if selection_entry_letter:
                selection_entry_complete(selection_entry_letter, selection_entry_number)
        if event == "--3--" or (event) == "3":
            selection_entry_number = "3"
            disable_numbered_selection_buttons()
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            jukebox_selection_window['--A3--'].update(disabled=False)
            jukebox_selection_window['--button2_top--'].update(disabled=False)
            jukebox_selection_window['--button2_bottom--'].update(disabled=False)
            jukebox_selection_window['--B3--'].update(disabled=False)
            jukebox_selection_window['--button9_top--'].update(disabled=False)
            jukebox_selection_window['--button9_bottom--'].update(disabled=False)
            jukebox_selection_window['--C3--'].update(disabled=False)
            jukebox_selection_window['--button16_top--'].update(disabled=False)
            jukebox_selection_window['--button16_bottom--'].update(disabled=False)
            control_button_window['--A--'].update(disabled=False)
            control_button_window['--B--'].update(disabled=False)
            control_button_window['--C--'].update(disabled=False)
            if selection_entry_letter:
                selection_entry_complete(selection_entry_letter, selection_entry_number)
        if event == "--4--" or (event) == "4":
            selection_entry_number = "4"
            disable_numbered_selection_buttons()
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            jukebox_selection_window['--A4--'].update(disabled=False)
            jukebox_selection_window['--button3_top--'].update(disabled=False)
            jukebox_selection_window['--button3_bottom--'].update(disabled=False)
            jukebox_selection_window['--B4--'].update(disabled=False)
            jukebox_selection_window['--button10_top--'].update(disabled=False)
            jukebox_selection_window['--button10_bottom--'].update(disabled=False)
            jukebox_selection_window['--C4--'].update(disabled=False)
            jukebox_selection_window['--button17_top--'].update(disabled=False)
            jukebox_selection_window['--button17_bottom--'].update(disabled=False)
            control_button_window['--A--'].update(disabled=False)
            control_button_window['--B--'].update(disabled=False)
            control_button_window['--C--'].update(disabled=False)
            if selection_entry_letter:
                selection_entry_complete(selection_entry_letter, selection_entry_number)
        if event == "--5--" or (event) == "5":
            selection_entry_number = "5"
            disable_numbered_selection_buttons()
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            jukebox_selection_window['--A5--'].update(disabled=False)
            jukebox_selection_window['--button4_top--'].update(disabled=False)
            jukebox_selection_window['--button4_bottom--'].update(disabled=False)
            jukebox_selection_window['--B5--'].update(disabled=False)
            jukebox_selection_window['--button11_top--'].update(disabled=False)
            jukebox_selection_window['--button11_bottom--'].update(disabled=False)
            jukebox_selection_window['--C5--'].update(disabled=False)
            jukebox_selection_window['--button18_top--'].update(disabled=False)
            jukebox_selection_window['--button18_bottom--'].update(disabled=False)
            control_button_window['--A--'].update(disabled=False)
            control_button_window['--B--'].update(disabled=False)
            control_button_window['--C--'].update(disabled=False)
            if selection_entry_letter:
                selection_entry_complete(selection_entry_letter, selection_entry_number)
        if event == "--6--" or (event) == "6":
            selection_entry_number = "6"
            disable_numbered_selection_buttons()
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            jukebox_selection_window['--A6--'].update(disabled=False)
            jukebox_selection_window['--button5_top--'].update(disabled=False)
            jukebox_selection_window['--button5_bottom--'].update(disabled=False)
            jukebox_selection_window['--B6--'].update(disabled=False)
            jukebox_selection_window['--button12_top--'].update(disabled=False)
            jukebox_selection_window['--button12_bottom--'].update(disabled=False)
            jukebox_selection_window['--C6--'].update(disabled=False)
            jukebox_selection_window['--button19_top--'].update(disabled=False)
            jukebox_selection_window['--button19_bottom--'].update(disabled=False)
            control_button_window['--A--'].update(disabled=False)
            control_button_window['--B--'].update(disabled=False)
            control_button_window['--C--'].update(disabled=False)
            if selection_entry_letter:
                selection_entry_complete(selection_entry_letter, selection_entry_number)
        if event == "--7--" or (event) == "7":
            selection_entry_number = "7"
            disable_numbered_selection_buttons()
            disable_a_selection_buttons()
            disable_b_selection_buttons()
            disable_c_selection_buttons()
            jukebox_selection_window['--A7--'].update(disabled=False)
            jukebox_selection_window['--button6_top--'].update(disabled=False)
            jukebox_selection_window['--button6_bottom--'].update(disabled=False)
            jukebox_selection_window['--B7--'].update(disabled=False)
            jukebox_selection_window['--button13_top--'].update(disabled=False)
            jukebox_selection_window['--button13_bottom--'].update(disabled=False)
            jukebox_selection_window['--C7--'].update(disabled=False)
            jukebox_selection_window['--button20_top--'].update(disabled=False)
            jukebox_selection_window['--button20_bottom--'].update(disabled=False)
            control_button_window['--A--'].update(disabled=False)
            control_button_window['--B--'].update(disabled=False)
            control_button_window['--C--'].update(disabled=False)
            if selection_entry_letter:
                selection_entry_complete(selection_entry_letter, selection_entry_number)
        if event == "--correct--" or (event) == "C":
            enable_all_buttons()
            selection_entry_letter = ""  # Used for selection entry
            selection_entry_number = ""  # Used for selection entry
            selection_entry = ""  # Used for selection entry
            control_button_window['--select--'].update(disabled=True)
        if event == "--select--" or (event) == 'S':
            print("Entering Song Selected")
            if credit_amount == 0:
                #VLC Song Playback Code Begin
                p = vlc.MediaPlayer('buzz.mp3')
                p.play()
                enable_all_buttons()
                selection_entry_letter = ""  # Used for selection entry
                selection_entry_number = ""  # Used for selection entry
                control_button_window['--select--'].update(disabled=True)
            else:                
                try:
                    if song_selected == "":
                        song_selected = selection_entry_letter + selection_entry_number
                except UnboundLocalError:
                        song_selected = selection_entry_letter + selection_entry_number
                # Clear variables no longer needed
                selection_entry_letter = ""
                selection_entry_number = ""
                if song_selected == "A1":
                    paid_song_selected_title = (jukebox_selection_window['--button0_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button0_bottom--'].get_text())
                if song_selected == "A2":
                    paid_song_selected_title = (jukebox_selection_window['--button1_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button1_bottom--'].get_text())
                if song_selected == "A3":
                    paid_song_selected_title = (jukebox_selection_window['--button2_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button2_bottom--'].get_text())
                if song_selected == "A4":
                    paid_song_selected_title = (jukebox_selection_window['--button3_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button3_bottom--'].get_text())
                if song_selected == "A5":
                    paid_song_selected_title = (jukebox_selection_window['--button4_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button4_bottom--'].get_text())
                if song_selected == "A6":
                    paid_song_selected_title = (jukebox_selection_window['--button5_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button5_bottom--'].get_text())
                if song_selected == "A7":
                    paid_song_selected_title = (jukebox_selection_window['--button6_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button6_bottom--'].get_text())
                if song_selected == "B1":
                    paid_song_selected_title = (jukebox_selection_window['--button7_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button7_bottom--'].get_text())
                if song_selected == "B2":
                    paid_song_selected_title = (jukebox_selection_window['--button8_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button8_bottom--'].get_text())
                if song_selected == "B3":
                    paid_song_selected_title = (jukebox_selection_window['--button9_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button9_bottom--'].get_text())
                if song_selected == "B4":
                    paid_song_selected_title = (jukebox_selection_window['--button10_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button10_bottom--'].get_text())
                if song_selected == "B5":
                    paid_song_selected_title = (jukebox_selection_window['--button11_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button11_bottom--'].get_text())
                if song_selected == "B6":
                    paid_song_selected_title = (jukebox_selection_window['--button12_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button12_bottom--'].get_text())
                if song_selected == "B7":
                    paid_song_selected_title = (jukebox_selection_window['--button13_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button13_bottom--'].get_text())
                if song_selected == "C1":
                    paid_song_selected_title = (jukebox_selection_window['--button14_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button14_bottom--'].get_text())
                if song_selected == "C2":
                    paid_song_selected_title = (jukebox_selection_window['--button15_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button15_bottom--'].get_text())
                if song_selected == "C3":
                    paid_song_selected_title = (jukebox_selection_window['--button16_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button16_bottom--'].get_text())
                if song_selected == "C4":
                    paid_song_selected_title = (jukebox_selection_window['--button17_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button17_bottom--'].get_text())
                if song_selected == "C5":
                    paid_song_selected_title = (jukebox_selection_window['--button18_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button18_bottom--'].get_text())
                if song_selected == "C6":
                    paid_song_selected_title = (jukebox_selection_window['--button19_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button19_bottom--'].get_text())
                if song_selected == "C7":
                    paid_song_selected_title = (jukebox_selection_window['--button20_top--'].get_text())
                    paid_song_selected_artist = (jukebox_selection_window['--button20_bottom--'].get_text())
                song_selected = ""
                control_button_window['--select--'].update(disabled=True)
                disable_numbered_selection_buttons()
                # Check and remove The from artist name
                if str(paid_song_selected_artist).startswith('The '):
                    paid_song_selected_artist_no_the = paid_song_selected_artist.replace('The ', '')
                    paid_song_selected_artist = paid_song_selected_artist_no_the
                # add selection to paid song list
                counter = 0
                #  find library number of selected song
                for i in MusicMasterSongList:
                    # search for match of song in MusicMasterSongList
                    if str(paid_song_selected_title) == MusicMasterSongList[counter]['title'][:22] and str(paid_song_selected_artist) == MusicMasterSongList[counter]['artist'][:22]:
                        # add song to upcoming list file
                        # UpcomingSongPlayList
                        UpcomingSongPlayList.append(str(MusicMasterSongList[counter]['title'][:22]) + ' - ' + str(MusicMasterSongList[counter]['artist'][:22]))
                        #  add matched song number to variable
                        song_to_add = (MusicMasterSongList[counter]['number']) 
                        #  open PaidMusicPlaylist text file and append song number to list
                        with open('PaidMusicPlayList.txt', 'r') as PaidMusicPlayListOpen:
                            PaidMusicPlayList = json.load(PaidMusicPlayListOpen)
                            PaidMusicPlayList.append(int(song_to_add))
                            # Check for duplicate song numbers in PaidMusicPlayList
                            # Remove duplicate song numbers from PaidMusicPlayList
                            test_set = set(PaidMusicPlayList)
                            if len(PaidMusicPlayList) != len(test_set):
                                PaidMusicPlayList = list(set(PaidMusicPlayList)) # https://bit.ly/4cZ7A6R
                                UpcomingSongPlayList.pop(-1)
                                print('Duplicate Song Found')
                                #VLC Song Playback Code Begin
                                p = vlc.MediaPlayer('buzz.mp3')
                                p.play()
                                enable_all_buttons()
                                selection_entry_letter = ""  # Used for selection entry
                                selection_entry_number = ""  # Used for selection entry
                                selection_entry = ""  # Used for selection entry
                                control_button_window['--select--'].update(disabled=True)
                                enable_all_buttons()
                                break
                        # write updated PaidMusicPlayList.txt back to disk
                        with open('PaidMusicPlayList.txt', 'w') as PaidMusicPlayListOpen:
                            json.dump(PaidMusicPlayList, PaidMusicPlayListOpen)
                        #  end search
                        enable_all_buttons()
                        credit_amount -= 1
                        info_screen_window['--credits--'].Update('CREDITS ' + str(credit_amount))
                        # Add selection to log file
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        with open('log.txt', 'a') as log:
                            log.write('\n' + str(current_time) + ' ' + (str(MusicMasterSongList[counter]['artist'])
                                            + ' - ' + str(MusicMasterSongList[counter]['title'] + ' Selected For Play,'))) # Add song selected to log file
                        # 45 rpm image popup code goes here                        
                        # https://www.tutorialspoint.com/how-to-add-text-on-an-image-using-pillow-in-python
                        # Center Anchor Lable Position https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
                        center_position = 684
                        # Record Title Name
                        record_title_name = str(MusicMasterSongList[counter]['title'])
                        record_title_name_length = len(record_title_name)
                        # Record Artist Name
                        record_artist_name = str(MusicMasterSongList[counter]['artist'])
                        record_artist_name_length = len(record_artist_name)
                        # Open the desired Image you want to add text on
                        # Create the list of all black print 45rpm record labels
                        path = "record_labels/final_black_sel/"
                        black_print_label_list = os.listdir(path)
                        # Selects a random 45rpm record label requiring black print
                        record_label = Image.open('record_labels/final_black_sel/' + str(random.choice(black_print_label_list)))
                        draw_on_45rpm_image = ImageDraw.Draw(record_label) 
                        # Record Display Generation
                        if record_title_name_length > 37 or record_artist_name_length >= 30:
                            font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 15)
                            wrapper = textwrap.TextWrapper(width=37) # https://www.geeksforgeeks.org/textwrap-text-wrapping-filling-python/
                            record_title_name_wrap = wrapper.wrap(text=record_title_name)
                            draw_on_45rpm_image.text((center_position, 520), record_title_name_wrap[0], fill="black", anchor="mb", font=font)
                            try:
                                draw_on_45rpm_image.text((center_position, 535), record_title_name_wrap[1], fill="black", anchor="mb", font=font)
                            except Exception:
                                pass   
                            wrapper = textwrap.TextWrapper(width=30)  
                            record_artist_name_wrap = wrapper.wrap(text=record_artist_name)
                            draw_on_45rpm_image.text((center_position, 555), record_artist_name_wrap[0], fill="black", anchor="mb", font=font)
                            try:
                                draw_on_45rpm_image.text((center_position, 570), record_artist_name_wrap[1], fill="black", anchor="mb", font=font)
                            except Exception:
                                pass
                        elif record_title_name_length < 37 and record_title_name_length > 17:
                            font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 20)
                            draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                            draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)
                        elif record_artist_name_length < 26 and record_artist_name_length > 13:
                            font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 20)
                            draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                            draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)
                        elif record_title_name_length <= 17:
                            font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 30)
                            draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                            draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)    
                        elif record_artist_name_length <= 13:
                            font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 30)
                            draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                            draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)                        
                        # Save the image on which we have added the text
                        record_label.save("selection_45.jpg")
                        # Save and resize the image on which we have added the text
                        record_label.resize((680,394)).save('selection_45.gif')
                        #VLC Song Playback Code Begin
                        p = vlc.MediaPlayer('success.mp3')
                        p.play()
                        # Display the image as popup
                        jukebox_selection_window.Hide()
                        for i in range(600): # adjust the range to control the time the image runs
                            sg.popup_animated('selection_45.gif', relative_location = (167,45), time_between_frames = 1, no_titlebar = True, keep_on_top = True)
                        sg.popup_animated(None) # close all Animated Popups
                        jukebox_selection_window.UnHide() 
                        break
                    counter += 1
        if event is None or event == 'Cancel' or event == 'Exit':
            print(f'closing window = {window.Title}')
            break
        if event == '--SONG_PLAYING_LOOKUP--':
            global last_song_check
            with open('CurrentSongPlaying.txt', 'r') as CurrentSongPlayingOpen:
                song_currently_playing = CurrentSongPlayingOpen.read()
                #  search MusicMasterSonglist for location string
                counter=0
                for x in MusicMasterSongList:
                    if MusicMasterSongList[counter]['location'] == song_currently_playing:
                        # Update Jukebox Info Screen
                        info_screen_window['--song_title--'].Update(
                            MusicMasterSongList[counter]['title'])
                        info_screen_window['--song_artist--'].Update(
                            MusicMasterSongList[counter]['artist'])
                        info_screen_window['--mini_song_title--'].Update(
                            '  Title: ' + MusicMasterSongList[counter]['title'])
                        info_screen_window['--mini_song_artist--'].Update(
                            '  Artist: ' + MusicMasterSongList[counter]['artist'])
                        info_screen_window['--year--'].Update(
                            '  Year: ' + MusicMasterSongList[counter]['year'] + '   Length: ' +
                            MusicMasterSongList[counter]['duration'])
                        info_screen_window['--album--'].Update(
                            '  Album: ' + MusicMasterSongList[counter]['album'])
                        #  Check to see if curent song playing has changed
                        with open('CurrentSongPlaying.txt', 'r') as CurrentSongPlayingOpen:
                            song_currently_playing = CurrentSongPlayingOpen.read()
                            # Set up first check
                            if last_song_check == "":
                                last_song_check = song_currently_playing
                            #  Check to see if current song has changed
                            if last_song_check != song_currently_playing:
                                last_song_check = song_currently_playing
                                # If song has changed remove first entry on UpcomingSongPlayList
                                try:
                                    UpcomingSongPlayList.pop(0)
                                except IndexError: # Executed if no first entry in list
                                    pass
                                # Create 45 RPM Record Image
                                # https://www.tutorialspoint.com/how-to-add-text-on-an-image-using-pillow-in-python
                                
                                # Center Anchor Label Position https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
                                center_position = 680
                                # https://www.tutorialspoint.com/how-to-add-text-on-an-image-using-pillow-in-python
                                # https://www.geeksforgeeks.org/textwrap-text-wrapping-filling-python/
                                # https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
                                # Open the desired Image you want to add text on
                                # Create the list of all black print 45rpm record labels
                                path = "record_labels/final_black_bg/"
                                black_print_label_list = os.listdir(path)
                                # Selects a random 45rpm record label requiring black print
                                record_selection = str(random.choice(black_print_label_list))
                                print(record_selection)
                                record_label = Image.open('record_labels/final_black_bg/' + record_selection)
                                # To add 2D graphics in an image call draw Method
                                record_text = ImageDraw.Draw(record_label)
                                # Set the default font size and type
                                record_font = ImageFont.truetype('fonts/OpenSans-ExtraBold.ttf', 30) 
                                # New Add Text to an image
                                # Record Title Name
                                record_title_name = str(MusicMasterSongList[counter]['title'])
                                record_title_name_length = len(record_title_name)
                                # Record Artist Name
                                record_artist_name = str(MusicMasterSongList[counter]['artist'])
                                record_artist_name_length = len(record_artist_name)
                                # Add Text to an image
                                draw_on_45rpm_image = ImageDraw.Draw(record_label)
                                # Record Display Generation
                                if record_title_name_length > 37 or record_artist_name_length >= 30:
                                    font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 15)
                                    wrapper = textwrap.TextWrapper(width=37) # https://www.geeksforgeeks.org/textwrap-text-wrapping-filling-python/
                                    record_title_name_wrap = wrapper.wrap(text=record_title_name)
                                    draw_on_45rpm_image.text((center_position, 520), record_title_name_wrap[0], fill="black", anchor="mb", font=font)
                                    try:
                                        draw_on_45rpm_image.text((center_position, 535), record_title_name_wrap[1], fill="black", anchor="mb", font=font)
                                    except Exception:
                                        pass   
                                    wrapper = textwrap.TextWrapper(width=30)  
                                    record_artist_name_wrap = wrapper.wrap(text=record_artist_name)
                                    draw_on_45rpm_image.text((center_position, 555), record_artist_name_wrap[0], fill="black", anchor="mb", font=font)
                                    try:
                                        draw_on_45rpm_image.text((center_position, 570), record_artist_name_wrap[1], fill="black", anchor="mb", font=font)
                                    except Exception:
                                        pass
                                elif record_title_name_length < 37 and record_title_name_length > 17:
                                    font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 20)
                                    draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                                    draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)
                                elif record_artist_name_length < 26 and record_artist_name_length > 13:
                                    font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 20)
                                    draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                                    draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)
                                elif record_title_name_length <= 17:
                                    font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 30)
                                    draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                                    draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)    
                                elif record_artist_name_length <= 13:
                                    font = ImageFont.truetype("fonts/OpenSans-ExtraBold.ttf", 30)
                                    draw_on_45rpm_image.text((center_position, 515), record_title_name, fill="black", anchor="mb", font=font)
                                    draw_on_45rpm_image.text((center_position, 540), record_artist_name, fill="black", anchor="mb", font=font)

                                # Save the image on which we have added the text
                                record_label.save("selection_45.jpg")
                                # Save and resize the image on which we have added the text
                                record_label.resize((680,394)).save('selection_45.gif')
                                # Display the image as popup
                                jukebox_selection_window.Hide()
                                for i in range(600): # adjust the range to control the time the image runs
                                    sg.popup_animated('selection_45.gif', relative_location = (167,45), time_between_frames = 1, no_titlebar = True, keep_on_top = True)
                                sg.popup_animated(None) # close all Animated Popups
                                jukebox_selection_window.UnHide()
                                # update upcoming selections on jukebox screens
                                upcoming_selections_update()
                        if UpcomingSongPlayList != []:
                            # update upcoming selections on jukebox screens
                            upcoming_selections_update()
                        break
                    counter +=1
    right_arrow_selection_window.close()
    left_arrow_selection_window.close()
    info_screen_window.close()
    jukebox_selection_window.close()
    window_background.close()
    control_button_window.close()

if __name__ == '__main__':

    # Base64 encoded image from https://www.base64-image.de/
    background_image = get_background_image()

main()
