import vlc
from the_bands_name_check import the_bands_name_check


def selection_buttons_update(selection_window_number, jukebox_selection_window, right_arrow_selection_window,
                             left_arrow_selection_window, MusicMasterSongList, dir_path):
    """
    Update song selection buttons with songs from the current window position.
    Handles boundary checking, font sizing, and band name formatting.

    Args:
        selection_window_number: Current position in the song list
        jukebox_selection_window: PySimpleGUI window for song selection
        right_arrow_selection_window: PySimpleGUI window with right scroll arrow
        left_arrow_selection_window: PySimpleGUI window with left scroll arrow
        MusicMasterSongList: List of all available songs with metadata
        dir_path: Directory path for accessing band name files

    Returns:
        int: Updated selection_window_number (adjusted for boundaries)
    """
    # stop screen progression at end of list
    if selection_window_number + 20 >= len(MusicMasterSongList):
        selection_window_number = len(MusicMasterSongList) - 21
        right_arrow_selection_window['--selection_right--'].update(disabled=True)
        # VLC Song Playback Code Begin
        p = vlc.MediaPlayer('buzz.mp3')
        p.play()
    else:
        right_arrow_selection_window['--selection_right--'].update(disabled=False)

    # Stop screen progression at beginning of list
    if selection_window_number + 20 < 0:
        selection_window_number = 0
        left_arrow_selection_window['--selection_left--'].update(disabled=True)
        # VLC Song Playback Code Begin
        p = vlc.MediaPlayer('buzz.mp3')
        p.play()
    else:
        left_arrow_selection_window['--selection_left--'].update(disabled=False)

    # update window buttons
    font_size_window_updates = ['--button0_top--', '--button0_bottom--', '--button1_top--', '--button1_bottom--',
                                        '--button2_top--', '--button2_bottom--', '--button3_top--', '--button3_bottom--',
                                        '--button4_top--', '--button4_bottom--', '--button5_top--', '--button5_bottom--',
                                        '--button6_top--', '--button6_bottom--', '--button7_top--', '--button7_bottom--',
                                        '--button8_top--', '--button8_bottom--', '--button9_top--', '--button9_bottom--',
                                        '--button10_top--', '--button10_bottom--', '--button11_top--', '--button11_bottom--',
                                        '--button12_top--', '--button12_bottom--', '--button13_top--', '--button13_bottom--',
                                        '--button14_top--', '--button14_bottom--', '--button15_top--', '--button15_bottom--',
                                        '--button16_top--', '--button16_bottom--', '--button17_top--', '--button17_bottom--',
                                        '--button18_top--', '--button18_bottom--', '--button19_top--', '--button19_bottom--',
                                        '--button20_top--', '--button20_bottom--']

    # Loop through all buttons to update and restore them to standard font size in the selection window
    for font_size_window in font_size_window_updates:
        jukebox_selection_window[font_size_window].Widget.config(font='Helvetica 12 bold')

    # Cant figure out a way to make this code more pythonic
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

    # Check text length and adjust font size
    for font_size_window in font_size_window_updates:
        font_length_string = jukebox_selection_window[font_size_window].get_text()
        if len(font_length_string) >= 28:
            jukebox_selection_window[font_size_window].Widget.config(font='Helvetica 8 bold')
        if len(font_length_string) > 21 and len(font_length_string) < 28:
            jukebox_selection_window[font_size_window].Widget.config(font='Helvetica 10 bold')

    the_bands_name_check(jukebox_selection_window, dir_path)

    return selection_window_number
