def upcoming_selections_update(info_screen_window, UpcomingSongPlayList):
    """
    Update the upcoming song selections display on the info screen.

    Args:
        info_screen_window: PySimpleGUI window for displaying song info
        UpcomingSongPlayList: List of upcoming songs to display
    """
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
    # update upcoming selections on jukebox screens
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
