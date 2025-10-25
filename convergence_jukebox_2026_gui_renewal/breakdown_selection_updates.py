# ============================================================================
# CONVERGENCE JUKEBOX 2026 - SELECTION UPDATE FUNCTIONS MODULE
# ============================================================================
# This module handles all display updates for song selections and upcoming queue
# Purpose: Update UI with song titles/artists and manage navigation controls
# ============================================================================

import vlc
from breakdown_bands_check import the_bands_name_check

# ============================================================================
# SELECTION BUTTONS UPDATE
# ============================================================================

def selection_buttons_update(selection_window_number, MusicMasterSongList, jukebox_selection_window,
                            left_arrow_selection_window, right_arrow_selection_window, dir_path):
    """
    Updates all 21 song display buttons with current selection window songs.

    This function:
    - Manages navigation boundaries (prevents scrolling past list start/end)
    - Displays songs starting from selection_window_number
    - Adjusts font sizes based on text length
    - Applies band name formatting via the_bands_name_check()
    - Plays "buzz.mp3" sound when reaching list boundaries

    Args:
        selection_window_number (int): Starting index in MusicMasterSongList
        MusicMasterSongList (list): Master list of all songs (dict format)
        jukebox_selection_window: PySimpleGUI window for song display
        left_arrow_selection_window: PySimpleGUI window with left arrow control
        right_arrow_selection_window: PySimpleGUI window with right arrow control
        dir_path (str): Directory path for resource files

    Returns:
        int: Valid selection_window_number (may be adjusted if at boundaries)
    """
    # Stop screen progression at end of list
    if selection_window_number + 20 >= len(MusicMasterSongList):
        selection_window_number = len(MusicMasterSongList) - 21
        right_arrow_selection_window['--selection_right--'].update(disabled=True)
        # Play buzz sound to notify user at end of list
        p = vlc.MediaPlayer('buzz.mp3')
        p.play()
    else:
        right_arrow_selection_window['--selection_right--'].update(disabled=False)

    # Stop screen progression at beginning of list
    if selection_window_number + 20 < 0:
        selection_window_number = 0
        left_arrow_selection_window['--selection_left--'].update(disabled=True)
        # Play buzz sound to notify user at beginning of list
        p = vlc.MediaPlayer('buzz.mp3')
        p.play()
    else:
        left_arrow_selection_window['--selection_left--'].update(disabled=False)

    # List of all button elements to update (both title and artist)
    font_size_window_updates = [
        '--button0_top--', '--button0_bottom--', '--button1_top--', '--button1_bottom--',
        '--button2_top--', '--button2_bottom--', '--button3_top--', '--button3_bottom--',
        '--button4_top--', '--button4_bottom--', '--button5_top--', '--button5_bottom--',
        '--button6_top--', '--button6_bottom--', '--button7_top--', '--button7_bottom--',
        '--button8_top--', '--button8_bottom--', '--button9_top--', '--button9_bottom--',
        '--button10_top--', '--button10_bottom--', '--button11_top--', '--button11_bottom--',
        '--button12_top--', '--button12_bottom--', '--button13_top--', '--button13_bottom--',
        '--button14_top--', '--button14_bottom--', '--button15_top--', '--button15_bottom--',
        '--button16_top--', '--button16_bottom--', '--button17_top--', '--button17_bottom--',
        '--button18_top--', '--button18_bottom--', '--button19_top--', '--button19_bottom--',
        '--button20_top--', '--button20_bottom--'
    ]

    # Reset all buttons to standard font size
    for font_size_window in font_size_window_updates:
        jukebox_selection_window[font_size_window].Widget.config(font='Helvetica 12 bold')

    # Update all 21 song button pairs (title and artist)
    # Note: The original code manually updates each button - not Pythonic but functional
    jukebox_selection_window['--button0_top--'].update(text=MusicMasterSongList[selection_window_number]['title'])
    jukebox_selection_window['--button0_bottom--'].update(text=MusicMasterSongList[selection_window_number]['artist'])
    jukebox_selection_window['--button1_top--'].update(text=MusicMasterSongList[selection_window_number + 1]['title'])
    jukebox_selection_window['--button1_bottom--'].update(text=MusicMasterSongList[selection_window_number + 1]['artist'])
    jukebox_selection_window['--button2_top--'].update(text=MusicMasterSongList[selection_window_number + 2]['title'])
    jukebox_selection_window['--button2_bottom--'].update(text=MusicMasterSongList[selection_window_number + 2]['artist'])
    jukebox_selection_window['--button3_top--'].update(text=MusicMasterSongList[selection_window_number + 3]['title'])
    jukebox_selection_window['--button3_bottom--'].update(text=MusicMasterSongList[selection_window_number + 3]['artist'])
    jukebox_selection_window['--button4_top--'].update(text=MusicMasterSongList[selection_window_number + 4]['title'])
    jukebox_selection_window['--button4_bottom--'].update(text=MusicMasterSongList[selection_window_number + 4]['artist'])
    jukebox_selection_window['--button5_top--'].update(text=MusicMasterSongList[selection_window_number + 5]['title'])
    jukebox_selection_window['--button5_bottom--'].update(text=MusicMasterSongList[selection_window_number + 5]['artist'])
    jukebox_selection_window['--button6_top--'].update(text=MusicMasterSongList[selection_window_number + 6]['title'])
    jukebox_selection_window['--button6_bottom--'].update(text=MusicMasterSongList[selection_window_number + 6]['artist'])
    jukebox_selection_window['--button7_top--'].update(text=MusicMasterSongList[selection_window_number + 7]['title'])
    jukebox_selection_window['--button7_bottom--'].update(text=MusicMasterSongList[selection_window_number + 7]['artist'])
    jukebox_selection_window['--button8_top--'].update(text=MusicMasterSongList[selection_window_number + 8]['title'])
    jukebox_selection_window['--button8_bottom--'].update(text=MusicMasterSongList[selection_window_number + 8]['artist'])
    jukebox_selection_window['--button9_top--'].update(text=MusicMasterSongList[selection_window_number + 9]['title'])
    jukebox_selection_window['--button9_bottom--'].update(text=MusicMasterSongList[selection_window_number + 9]['artist'])
    jukebox_selection_window['--button10_top--'].update(text=MusicMasterSongList[selection_window_number + 10]['title'])
    jukebox_selection_window['--button10_bottom--'].update(text=MusicMasterSongList[selection_window_number + 10]['artist'])
    jukebox_selection_window['--button11_top--'].update(text=MusicMasterSongList[selection_window_number + 11]['title'])
    jukebox_selection_window['--button11_bottom--'].update(text=MusicMasterSongList[selection_window_number + 11]['artist'])
    jukebox_selection_window['--button12_top--'].update(text=MusicMasterSongList[selection_window_number + 12]['title'])
    jukebox_selection_window['--button12_bottom--'].update(text=MusicMasterSongList[selection_window_number + 12]['artist'])
    jukebox_selection_window['--button13_top--'].update(text=MusicMasterSongList[selection_window_number + 13]['title'])
    jukebox_selection_window['--button13_bottom--'].update(text=MusicMasterSongList[selection_window_number + 13]['artist'])
    jukebox_selection_window['--button14_top--'].update(text=MusicMasterSongList[selection_window_number + 14]['title'])
    jukebox_selection_window['--button14_bottom--'].update(text=MusicMasterSongList[selection_window_number + 14]['artist'])
    jukebox_selection_window['--button15_top--'].update(text=MusicMasterSongList[selection_window_number + 15]['title'])
    jukebox_selection_window['--button15_bottom--'].update(text=MusicMasterSongList[selection_window_number + 15]['artist'])
    jukebox_selection_window['--button16_top--'].update(text=MusicMasterSongList[selection_window_number + 16]['title'])
    jukebox_selection_window['--button16_bottom--'].update(text=MusicMasterSongList[selection_window_number + 16]['artist'])
    jukebox_selection_window['--button17_top--'].update(text=MusicMasterSongList[selection_window_number + 17]['title'])
    jukebox_selection_window['--button17_bottom--'].update(text=MusicMasterSongList[selection_window_number + 17]['artist'])
    jukebox_selection_window['--button18_top--'].update(text=MusicMasterSongList[selection_window_number + 18]['title'])
    jukebox_selection_window['--button18_bottom--'].update(text=MusicMasterSongList[selection_window_number + 18]['artist'])
    jukebox_selection_window['--button19_top--'].update(text=MusicMasterSongList[selection_window_number + 19]['title'])
    jukebox_selection_window['--button19_bottom--'].update(text=MusicMasterSongList[selection_window_number + 19]['artist'])
    jukebox_selection_window['--button20_top--'].update(text=MusicMasterSongList[selection_window_number + 20]['title'])
    jukebox_selection_window['--button20_bottom--'].update(text=MusicMasterSongList[selection_window_number + 20]['artist'])

    # Adjust font sizes based on text length
    for font_size_window in font_size_window_updates:
        font_length_string = jukebox_selection_window[font_size_window].get_text()
        # Very long text (28+ chars) gets smallest font
        if len(font_length_string) >= 28:
            jukebox_selection_window[font_size_window].Widget.config(font='Helvetica 8 bold')
        # Medium text (22-27 chars) gets medium font
        elif len(font_length_string) > 21 and len(font_length_string) < 28:
            jukebox_selection_window[font_size_window].Widget.config(font='Helvetica 10 bold')

    # Apply band name formatting (add "The" prefix where appropriate)
    the_bands_name_check(jukebox_selection_window, dir_path)

    return selection_window_number


# ============================================================================
# UPCOMING SELECTIONS UPDATE
# ============================================================================

def upcoming_selections_update(info_screen_window, UpcomingSongPlayList):
    """
    Updates the upcoming queue display with next songs to be played.

    Displays up to 10 upcoming songs in the info screen window.
    Clears display if queue is empty.

    Args:
        info_screen_window: PySimpleGUI window for displaying upcoming queue
        UpcomingSongPlayList (list): Queue of upcoming songs to display

    Returns:
        None - Updates window elements directly
    """
    # Clear all upcoming song display slots
    info_screen_window['--upcoming_one--'].Update(' ')
    info_screen_window['--upcoming_two--'].Update(' ')
    info_screen_window['--upcoming_three--'].Update(' ')
    info_screen_window['--upcoming_four--'].Update(' ')
    info_screen_window['--upcoming_five--'].Update(' ')
    info_screen_window['--upcoming_six--'].Update(' ')
    info_screen_window['--upcoming_seven--'].Update(' ')
    info_screen_window['--upcoming_eight--'].Update(' ')
    info_screen_window['--upcoming_nine--'].Update(' ')
    info_screen_window['--upcoming_ten--'].Update(' ')

    # Update each upcoming song slot if available
    # Uses try/except to safely handle shorter queues
    try:
        if UpcomingSongPlayList[0] != []:
            info_screen_window['--upcoming_one--'].Update('  ' + UpcomingSongPlayList[0])
    except Exception:
        info_screen_window['--upcoming_one--'].Update(' ')

    try:
        if UpcomingSongPlayList[1] != []:
            info_screen_window['--upcoming_two--'].Update('  ' + UpcomingSongPlayList[1])
    except Exception:
        info_screen_window['--upcoming_two--'].Update(' ')

    try:
        if UpcomingSongPlayList[2] != []:
            info_screen_window['--upcoming_three--'].Update('  ' + UpcomingSongPlayList[2])
    except Exception:
        info_screen_window['--upcoming_three--'].Update(' ')

    try:
        if UpcomingSongPlayList[3] != []:
            info_screen_window['--upcoming_four--'].Update('  ' + UpcomingSongPlayList[3])
    except Exception:
        info_screen_window['--upcoming_four--'].Update(' ')

    try:
        if UpcomingSongPlayList[4] != []:
            info_screen_window['--upcoming_five--'].Update('  ' + UpcomingSongPlayList[4])
    except Exception:
        info_screen_window['--upcoming_five--'].Update(' ')

    try:
        if UpcomingSongPlayList[5] != []:
            info_screen_window['--upcoming_six--'].Update('  ' + UpcomingSongPlayList[5])
    except Exception:
        info_screen_window['--upcoming_six--'].Update(' ')

    try:
        if UpcomingSongPlayList[6] != []:
            info_screen_window['--upcoming_seven--'].Update('  ' + UpcomingSongPlayList[6])
    except Exception:
        info_screen_window['--upcoming_seven--'].Update(' ')

    try:
        if UpcomingSongPlayList[7] != []:
            info_screen_window['--upcoming_eight--'].Update('  ' + UpcomingSongPlayList[7])
    except Exception:
        info_screen_window['--upcoming_eight--'].Update(' ')

    try:
        if UpcomingSongPlayList[8] != []:
            info_screen_window['--upcoming_nine--'].Update('  ' + UpcomingSongPlayList[8])
    except Exception:
        info_screen_window['--upcoming_nine--'].Update(' ')

    try:
        if UpcomingSongPlayList[9] != []:
            info_screen_window['--upcoming_ten--'].Update('  ' + UpcomingSongPlayList[9])
    except Exception:
        info_screen_window['--upcoming_ten--'].Update(' ')
