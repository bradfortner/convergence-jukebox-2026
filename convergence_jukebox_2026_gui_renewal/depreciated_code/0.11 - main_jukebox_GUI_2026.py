from calendar import c
from datetime import datetime, timedelta # required for logging timestamp
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
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import textwrap
import sys
import vlc

global selection_window_number
global jukebox_selection_window
global last_song_check
global master_songlist_number
last_song_check = ""
global credit_amount
credit_amount = 0
UpcomingSongPlayList = []
all_songs_list = []
all_artists_list = []
dir_path = os.path.dirname(os.path.realpath(__file__))
#  Check for files on disk. If they dont exist, create them
#  Create date and time stamp for log file
now = datetime.now()
rounded_now = now + timedelta(seconds=0.5)
rounded_now = rounded_now.replace(microsecond=0)
now = rounded_now
if not os.path.exists('log.txt'):
    with open('log.txt', 'w') as log:
        log.write(str(now) + ' Jukebox GUI Started - New Log File Created,')
else:
    with open('log.txt', 'a') as log:
        log.write('\n' + str(now) + ', Jukebox GUI Restarted,')
if not os.path.exists('the_bands.txt'):
    with open('the_bands.txt', 'w') as TheBandsTextOpen:
        # Band names to have the added to them, in lower case separated by commas in thebands.txt file
        TheBandsText = "beatles,rolling stones,who,doors,byrds,beachboys"
        json.dump(TheBandsText, TheBandsTextOpen)
#  open MusicMasterSongList dictionary
if not os.path.exists('the_exempted_bands.txt'):
    with open('the_exempted_bands.txt', 'w') as TheExemptedBandsTextOpen:
        # Band names be exempted from having the added to them, in proper case separated by line return in the_exempted_bands.txt file
        TheExemptedBandsText = "Place Band Names Here In Proper Case With Each Band Placed On Separate Line With No Quotes"
        json.dump(TheExemptedBandsText, TheExemptedBandsTextOpen)
#  open MusicMasterSongList dictionary
with open('MusicMasterSongList.txt', 'r') as MusicMasterSongListOpen:
    MusicMasterSongList = json.load(MusicMasterSongListOpen)
#  sort MusicMasterSongList dictionary by artist
MusicMasterSongList = sorted(MusicMasterSongList, key=itemgetter('artist'))
with open('MusicMasterSongList.txt', 'r') as MusicMasterSongListOpen:
    MusicMasterSongList = json.load(MusicMasterSongListOpen)
#  sort MusicMasterSongList dictionary by artist
MusicMasterSongDict = sorted(MusicMasterSongList, key=itemgetter('artist'))
# MusicMasterSongList*=0
master_songlist_number = len(MusicMasterSongDict)
counter = 0
for counter in range(master_songlist_number):
    all_songs_list.append(list(MusicMasterSongDict[counter].values()))
MusicMasterSongDict*=0    
artist_songlist_number = len(all_songs_list)
counter = 0
for counter in range(artist_songlist_number):
    all_artists_list.append(all_songs_list[counter][3])
all_songs_list*=0 
# Important Delete duplicates from all_artists_list
all_artists_list = list(set(all_artists_list)) # https://bit.ly/4cZ7A6R
# Sort all_artists_list
all_artists_list = sorted(all_artists_list)
find_list = all_artists_list

print(MusicMasterSongList)

