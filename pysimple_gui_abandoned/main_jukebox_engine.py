import PySimpleGUI as sg
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

dir_path = os.path.dirname(os.path.realpath(__file__))  # sets directory path for Windows Macintosh Systems
MusicId3MetaDataList = []  # list of all songs mp3 id3 metadata
MusicMasterSongList = []  # dictionary of all songs mp3 id3 metadata required by Convergence Jukebox
RandomMusicPlayList = []  # list of randomly played songs
PaidMusicPlayList = [] # list of paid songs to be played
FinalGenreList = []  #  List of genres found in comment metadata on all songs
random_music_play_number = ""
artist_name = ""
song_name = ""
album_name = ""
'''genre0 = "play2021"
genre1 = "null"
genre2 = "null"
genre3 = "null"'''
song_duration = ""
song_year = ""
song_genre = ""
#  Check for files on disk. If they dont exist, create them
#  Create date and time stamp for log file
now = datetime.now()
rounded_now = now + timedelta(seconds=0.5)
rounded_now = rounded_now.replace(microsecond=0)
now = rounded_now
if not os.path.exists('log.txt'):
    with open('log.txt', 'w') as log:
        log.write(str(now) + ' Jukebox Engine Started - New Log File Created,')
else:
    with open('log.txt', 'a') as log:
        log.write('\n' + str(now) + ' Jukebox Engine Restarted,')
if not os.path.exists('GenreFlagsList.txt'):
    with open('GenreFlagsList.txt', 'w') as GenreFlagsListOpen:
        GenreFlagsList = ['null','null','null','null']
        json.dump(GenreFlagsList, GenreFlagsListOpen)        
if not os.path.exists('MusicMasterSongListCheck.txt'):
    with open('MusicMasterSongListCheck.txt', 'w') as MusicMasterSongListCheckListOpen:
        MusicMasterSongListCheckList = []
        json.dump(MusicMasterSongListCheckList, MusicMasterSongListCheckListOpen)
if not os.path.exists('PaidMusicPlayList.txt'):
    with open('PaidMusicPlayList.txt', 'w') as PaidMusicPlayListOpen:
        PaidMusicPlayList = []
        json.dump(PaidMusicPlayList, PaidMusicPlayListOpen) 
def assign_song_data_random():
    global artist_name
    global song_name
    global album_name
    global song_duration
    global song_year
    global song_genre
    global MusicMasterSongList
    artist_name = MusicMasterSongList[RandomMusicPlayList[0]]['artist']
    song_name = MusicMasterSongList[RandomMusicPlayList[0]]['title']
    album_name = MusicMasterSongList[RandomMusicPlayList[0]]['album']
    song_duration = MusicMasterSongList[RandomMusicPlayList[0]]['duration']
    song_year = MusicMasterSongList[RandomMusicPlayList[0]]['year']
    song_genre = MusicMasterSongList[RandomMusicPlayList[0]]['comment']
def assign_song_data_paid():
    global artist_name
    global song_name
    global album_name
    global song_duration
    global song_year
    global song_genre
    global MusicMasterSongList
    artist_name = MusicMasterSongList[int(PaidMusicPlayList[0])]['artist']
    song_name = MusicMasterSongList[int(PaidMusicPlayList[0])]['title']
    album_name = MusicMasterSongList[int(PaidMusicPlayList[0])]['album']
    song_duration = MusicMasterSongList[int(PaidMusicPlayList[0])]['duration']
    song_year = MusicMasterSongList[int(PaidMusicPlayList[0])]['year']
    song_genre = MusicMasterSongList[int(PaidMusicPlayList[0])]['comment']
def generate_mp3_metadata():
    global MusicMasterSongList
    global MusicMasterSongListCheck
    global MusicId3MetaDataList
    print("Convergence Jukebox 2025\nPlease Be Patient Regenerating Your Songlist From Scratch \nMusic Will Start When Finished")
    counter = 0
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if sys.platform.startswith('linux'):
        mp3_music_files = glob.glob(dir_path + '/music/*.mp3') # Linux Code
    elif sys.platform.startswith('win32'):
        mp3_music_files = glob.glob(dir_path + '\music\*.mp3') # Windows Code
    for i in mp3_music_files:
        id3tag = TinyTag.get(i)
        get_song_duration_seconds = "%f" % id3tag.duration
        remove_song_duration_decimals = float(get_song_duration_seconds)
        song_duration_decimals_removed = int(remove_song_duration_decimals)
        song_duration_minutes_seconds = int(song_duration_decimals_removed)
        song_duration = time.strftime("%M:%S", time.gmtime(song_duration_minutes_seconds))
        song_metadata = list((counter,mp3_music_files[counter],"%s" % id3tag.title, "%s" % id3tag.artist,
                              "%s" % id3tag.album, "%s" % id3tag.year, "%s" % id3tag.comment,
                            song_duration)) # Gets MP3 Metadata (ID3)
        MusicId3MetaDataList.append(song_metadata)
        counter += 1
def generate_Music_Master_Song_List_Dictionary():
    global MusicMasterSongList
    #  Assign keys for MusicMasterSongList Dictionary
    keys = ['number', 'location', 'title', 'artist','album','year','comment','duration'] # https://bit.ly/48bYWPY
    #  Build MusicMasterSongList Dictionary
    MusicMasterSongList = [dict(zip(keys, sublst)) for sublst in MusicId3MetaDataList] # https://bit.ly/48bYWPY
    # Save MusicMasterSongList Dictionary
    with open('MusicMasterSongList.txt', 'w') as MusicMasterSongListOpen:
        json.dump(MusicMasterSongList, MusicMasterSongListOpen)
    #  Create and save a file list size value to check if MusicMasterSongList has changed after a reboot
    x = (len(MusicMasterSongList))
    with open('MusicMasterSongListCheck.txt', 'w') as MusicMasterSongListCheckOpen:
        json.dump(x, MusicMasterSongListCheckOpen)
def play_song(song_file_name):
    print(psutil.virtual_memory())
    # get the current collection
    # thresholds as a tuple
    print("Garbage collection thresholds:",gc.get_threshold())
    # Returns the number of
    # objects it has collected
    # and deallocated
    collected = gc.collect()
    # Prints Garbage collector
    # as 0 object
    print("Garbage collector: collected","%d objects." % collected)
    #VLC Song Playback Code Begin
    p = vlc.MediaPlayer(song_file_name)
    p.play()
    print('is_playing:', p.is_playing())  # 0 = False
    time.sleep(0.5)  # sleep because it needs time to start playing
    print('is_playing:', p.is_playing())  # 1 = True
    while p.is_playing():
        time.sleep(0.5)  # sleep to use less CPU
    #VLC Song Playback Code End
def assign_genres_to_random_play():
    global FinalGenreList
    extract_original_assigned_genres = []
    unfiltered_FinalGenreList = []
    global genre0, genre1, genre2, genre3
    with open('GenreFlagsList.txt', 'r') as GenreFlagsListOpen:
        GenreFlagsList = json.load(GenreFlagsListOpen)
    genre0 = GenreFlagsList[0]
    genre1 = GenreFlagsList[1]
    genre2 = GenreFlagsList[2]
    genre3 = GenreFlagsList[3]
    counter = 0
    for i in MusicMasterSongList:
        extract_original_assigned_genres.append(MusicMasterSongList[counter]['comment'])
        counter += 1
    counter = 0
    for i in extract_original_assigned_genres:
        if ' ' in extract_original_assigned_genres[counter]:
            extract_split_original_assigned_genres = extract_original_assigned_genres[counter].split()  # splits multi genre selections
            extract_original_assigned_genres.extend(extract_split_original_assigned_genres) # adds split genres to end of list
        counter += 1
    length_list = len(extract_original_assigned_genres)
    ll = length_list - 1
    for x in range(0,ll):
        if not ' ' in extract_original_assigned_genres[x]:
            unfiltered_FinalGenreList.append(extract_original_assigned_genres[x])
    FinalGenreList = list(set(unfiltered_FinalGenreList))  # removes duplicates
    FinalGenreList.sort()

    print('Genres for Random Play are:')
    if genre0 == 'null':
        print('No Genre 0')
    else:
        print(genre0)
    if genre1 == 'null':
        print('No Genre 1')
    else:
        print(genre1)
    if genre2 == 'null':
        print('No Genre 2')
    else:
        print(genre2)
    if genre3 == 'null':
        print('No Genre 3')
    else:
        print(genre3)
def generate_random_song_list():
    global MusicMasterSongList
    global RandomMusicPlayList
    global genre0,genre1,genre2,genre3
    counter = 0
    for i in MusicMasterSongList:
        if 'norandom' in MusicMasterSongList[counter]['comment']: # Filters norandom tagged songs
            pass
        else:
            pass
        if genre0 == "null" and genre1 == "null" and genre2 == "null" and genre3 == "null" and not 'norandom' in MusicMasterSongList[counter]['comment']: # Adds all songs to Random playlist
            RandomMusicPlayList.append(counter)
        if genre0 != "null" and genre0 in MusicMasterSongList[counter]['comment']: # Adds genre to Random playlist
            RandomMusicPlayList.append(counter)
        else:
            pass
        if genre1 != "null" and genre1 in MusicMasterSongList[counter]['comment']: # Adds genre to Random playlist
            RandomMusicPlayList.append(counter)
        else:
            pass
        if genre2 != "null" and genre2 in MusicMasterSongList[counter]['comment']: # Adds genre to Random playlist
            RandomMusicPlayList.append(counter)
        else:
            pass
        if genre3 != "null" and genre3 in MusicMasterSongList[counter]['comment']: # Adds genre to Random playlist
            RandomMusicPlayList.append(counter)
        else:
            pass
        counter += 1
    random.shuffle(RandomMusicPlayList)
def jukebox_engine():
    with open('PaidMusicPlayList.txt', 'r') as PaidMusicPlayListOpen:
        PaidMusicPlayList = json.load(PaidMusicPlayListOpen)
    NowPlayingPlayList = PaidMusicPlayList    
    if NowPlayingPlayList != []:
        for i in NowPlayingPlayList:
            print('Now Playing: '  + MusicMasterSongList[i]['title']
                  + ' - ' + MusicMasterSongList[i]['artist']
                  + '  Year:' + MusicMasterSongList[i]['year'] + ' Length:'
                  + MusicMasterSongList[i]['duration']
                  + ' Album:' + MusicMasterSongList[i]['album']
                  + '  Genre:' + MusicMasterSongList[i]['comment'])
            # Save playsong number to disk
            song_currently_playing = (str(MusicMasterSongList[i]['number']))
            with open("CurrentSongPlaying.txt", "w") as outfile:
                print('Writing CurrentSongPlaying.txt')
                outfile.write(MusicMasterSongList[PaidMusicPlayList[0]]['location'])
            #  Logging paid song to log file
            with open('log.txt', 'a') as log:
                now = datetime.now()
                rounded_now = now + timedelta(seconds=0.5)
                rounded_now = rounded_now.replace(microsecond=0)
                now = rounded_now                
                log.write('\n' + str(now) + ', ' + str(MusicMasterSongList[i]['artist'])
                          + ' - ' + str(MusicMasterSongList[i]['title']) + ', Played Paid,')                          
            print('Playing Paid Song In Jukebox Engine')
            play_song(MusicMasterSongList[PaidMusicPlayList[0]]['location'])
            #  delete song just played from PaidMusicPlaylist
            with open('PaidMusicPlayList.txt', 'r') as PaidMusicPlayListOpen:
                PaidMusicPlayList = json.load(PaidMusicPlayListOpen)
            for i in NowPlayingPlayList:
                print('Deleting Song')
                del PaidMusicPlayList[0]
            with open('PaidMusicPlayList.txt', 'w') as PaidMusicPlayListOpen:
                json.dump(PaidMusicPlayList, PaidMusicPlayListOpen)
            jukebox_engine()
    for i in RandomMusicPlayList:
        assign_song_data_random()
        print('Now Playing: ' + song_name + ' - ' + artist_name
                + '  Year:' + song_year + ' Length:' + song_duration
                + ' Album:' + album_name + '  Genre:' + song_genre)
        # Save playsong number to disk
        song_currently_playing = (str(MusicMasterSongList[RandomMusicPlayList[0]]['number']))
        with open("CurrentSongPlaying.txt", "w") as outfile:
            outfile.write(MusicMasterSongList[RandomMusicPlayList[0]]['location'])        
        #  Logging random song to log file
        with open('log.txt', 'a') as log:
            now = datetime.now()
            rounded_now = now + timedelta(seconds=0.5)
            rounded_now = rounded_now.replace(microsecond=0)
            now = rounded_now                
            log.write('\n' + str(now) + ', ' + str(MusicMasterSongList[i]['artist'])
                        + ' - ' + str(MusicMasterSongList[i]['title']) + ', Played Random,') 
        play_song(MusicMasterSongList[RandomMusicPlayList[0]]['location'])
        #  Move song to end of RandomMusicPlaylist
        move_first_list_element = RandomMusicPlayList.pop(0)
        RandomMusicPlayList.append(move_first_list_element)
        jukebox_engine()
# Check to see if MasterMusicSongList exists on disk
if os.path.exists('MusicMasterSongList.txt'):
    print('Check to see if MasterMusicSongList exists on disk')
    # Count number of files in music directory
    x = len(glob.glob(dir_path + '\\music\\*.mp3'))
    #x = sum(os.path.isfile(os.path.join(dir_path + '\\silentmusic\\', f)) for f in os.listdir(dir_path + '\\music\\'))
    print(x)
    #  Open MusicMasterSongListCheck generated from previous run of Convergence Jukebox
    with open('MusicMasterSongListCheck.txt', 'r') as MusicMasterSongListCheckOpen:
        MusicMasterSongListCheck = json.load(MusicMasterSongListCheckOpen)
        y = MusicMasterSongListCheck
        print(y)
    #  Check for match
    if x == y:
        print('Match')
        #  open MusicMasterSongList dictionary
        with open('MusicMasterSongList.txt', 'r') as MusicMasterSongListOpen:
            MusicMasterSongList = json.load(MusicMasterSongListOpen)
        # MusicMasterSongList matches, run required functions
        assign_genres_to_random_play()
        generate_random_song_list()
    jukebox_engine()
generate_mp3_metadata()
generate_Music_Master_Song_List_Dictionary()
assign_genres_to_random_play()
generate_random_song_list()
jukebox_engine()
