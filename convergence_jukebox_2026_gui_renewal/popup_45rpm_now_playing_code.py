"""
45RPM Now-Playing Record Pop-up Code Module
Handles the display of 45rpm record labels with now-playing song information as animated popups
"""

import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
import FreeSimpleGUI as sg


def display_45rpm_now_playing_popup(MusicMasterSongList, counter, jukebox_selection_window, upcoming_selections_update):
    """
    Display an animated 45rpm record popup with now-playing song title and artist information.

    This function creates a visual representation of a 45rpm record label with the
    currently playing song's title and artist, then displays it as an animated popup.
    This is triggered when the currently playing track changes during playback.

    Args:
        MusicMasterSongList (list): List containing song information dictionaries
        counter (int): Index of the current song in MusicMasterSongList
        jukebox_selection_window: The FreeSimpleGUI window object to hide/unhide
        upcoming_selections_update: Function to call to update the upcoming selections display

    Returns:
        None
    """

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
        sg.PopupAnimated('selection_45.gif', relative_location = (167,45), time_between_frames = 1, no_titlebar = True, keep_on_top = True)
    sg.PopupAnimated(None) # close all Animated Popups
    jukebox_selection_window.UnHide()
    # update upcoming selections on jukebox screens
    upcoming_selections_update()
