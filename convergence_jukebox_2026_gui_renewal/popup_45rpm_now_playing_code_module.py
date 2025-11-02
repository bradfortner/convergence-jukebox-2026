"""
45RPM Now-Playing Record Pop-up Code Module
Handles the display of 45rpm record labels with now-playing song information as animated popups
"""
import pickle # -Should Not Be Required
import threading
from pathlib import Path
import os
import random
import textwrap
import time
from PIL import Image, ImageDraw, ImageFont
import FreeSimpleGUI as sg
from rotate_record_module import display_record_playing



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

    def wrap_text(text, font, max_width, draw):
        """
        Wrap text to fit within a specified pixel width.

        Breaks text into lines by word boundaries to ensure no line exceeds
        the maximum width. Uses the font metrics to calculate actual pixel widths.

        Args:
            text (str): The text to wrap
            font (ImageFont): Pillow font object for measuring text width
            max_width (int): Maximum width in pixels for each line
            draw (ImageDraw): Pillow draw object for text metrics

        Returns:
            list: List of wrapped text lines, each within max_width
        """
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            # Test if adding the next word would exceed max width
            test_line = current_line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                # Word fits on current line
                current_line = test_line
            else:
                # Word doesn't fit, save current line and start new one
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        # Append any remaining text
        if current_line:
            lines.append(current_line.strip())

        return lines


    def fit_text_to_width(text, base_font_path, start_size, max_width, max_lines, draw):
        """
        Auto-fit text by reducing font size until it fits within constraints.

        Iteratively reduces font size by 2pt increments until text fits within
        the specified width and line limits. Prefers single-line text, but allows
        up to max_lines if necessary.

        Args:
            text (str): The text to fit
            base_font_path (str): Path to the TTF font file
            start_size (int): Starting font size in points
            max_width (int): Maximum width in pixels
            max_lines (int): Maximum number of lines allowed
            draw (ImageDraw): Pillow draw object for text metrics

        Returns:
            tuple: (list of wrapped lines, font size used, font object)
        """
        font_size = start_size
        min_font_size = 16  # Don't go smaller than 16pt

        while font_size >= min_font_size:
            # Create font at current size
            font = ImageFont.truetype(base_font_path, font_size)
            lines = wrap_text(text, font, max_width, draw)

            # Prefer single line - return immediately if text fits on one line
            if len(lines) == 1:
                return lines, font_size, font

            # If text fits within max_lines, check if we should try smaller font
            if len(lines) <= max_lines:
                # Test if reducing font size would still fit
                test_font = ImageFont.truetype(base_font_path, font_size - 2)
                test_lines = wrap_text(text, test_font, max_width, draw)
                if len(test_lines) <= max_lines:
                    # Can fit with smaller font, so keep reducing
                    font_size -= 2
                    continue
                else:
                    # Current size is good, smaller size would break max_lines
                    return lines, font_size, font

            # Text doesn't fit, reduce size and try again
            font_size -= 2

        # Last resort - use minimum font size
        font = ImageFont.truetype(base_font_path, min_font_size)
        return wrap_text(text, font, max_width, draw), min_font_size, font

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
    """

    # Record Title Name
    song = str(MusicMasterSongList[counter]['title'])
    # Record Artist Name
    artist = str(MusicMasterSongList[counter]['artist'])
    
    # Path to blank record labels directory
    blank_records_dir = "record_labels/blank_record_labels"

    # Get all .png files from the blank_record_labels directory
    print("\nScanning for available record labels...")
    png_files = [f for f in os.listdir(blank_records_dir) if f.endswith('.png')]

    if not png_files:
        raise FileNotFoundError(f"No .png files found in {blank_records_dir}")

    print(f"Found {len(png_files)} available record labels")
    
    # Randomly select one blank record label
    selected_label = random.choice(png_files)
    label_path = os.path.join(blank_records_dir, selected_label)

    print(f"Randomly selected label: {selected_label}")

    # Determine font color based on filename
    # If filename starts with "w_", use white font; otherwise use black
    font_color = "white" if selected_label.startswith("w_") else "black"
    print(f"Font color mode: {font_color.upper()}")

    # Load the selected record label image
    print("Loading blank record label template...")
    base_img = Image.open(label_path)


    """
    # Save the image on which we have added the text
    # Convert RGBA to RGB for JPEG compatibility (JPEG doesn't support alpha channel)
    if record_label.mode == 'RGBA':
        record_label = record_label.convert('RGB')
    record_label.save("images/selection_45.jpg")
    # Save and resize the image on which we have added the text
    record_label.resize((394,394)).save('images/selection_45.gif')
    """ 

    # Get image dimensions for positioning calculations
    width, height = base_img.size

    # Configuration settings
    font_path = "fonts/OpenSans-ExtraBold.ttf"          # Font to use for text
    max_text_width = 300               # Maximum width for wrapped text (pixels)
    song_y = (height // 2) + 90        # Y position for song title (below center)
    artist_y = (height // 2) + 125     # Y position for artist name (below song)
    song_line_height = 25              # Vertical spacing between song title lines
    artist_line_height = 30            # Vertical spacing between artist name lines

    print(f"Creating record label...")
    print("-" * 80)

    # Create a working copy of the base image
    img = base_img.copy()
    draw = ImageDraw.Draw(img)

    # Auto-fit song title text
    # Start at 28pt, allow max 2 lines
    song_lines, song_font_size, song_font = fit_text_to_width(
        song, font_path, 28, max_text_width, 2, draw
    )

    # Auto-fit artist name text
    # Start at 28pt, allow max 2 lines
    artist_lines, artist_font_size, artist_font = fit_text_to_width(
        artist, font_path, 28, max_text_width, 2, draw
    )

    # Draw song title lines, centered horizontally
    for i, line in enumerate(song_lines):
        # Calculate width of this line to center it
        song_bbox = draw.textbbox((0, 0), line, font=song_font)
        song_width = song_bbox[2] - song_bbox[0]
        song_x = (width - song_width) // 2  # Center horizontally

        # Draw the line at calculated position with determined font color
        draw.text(
            (song_x, song_y + (i * song_line_height)),
            line,
            font=song_font,
            fill=font_color
        )

    # Adjust artist Y position based on number of song lines
    # This prevents overlap if song title wraps to multiple lines
    artist_y_adjusted = artist_y + ((len(song_lines) - 1) * song_line_height)

    # Draw artist name lines, centered horizontally
    for i, line in enumerate(artist_lines):
        # Calculate width of this line to center it
        artist_bbox = draw.textbbox((0, 0), line, font=artist_font)
        artist_width = artist_bbox[2] - artist_bbox[0]
        artist_x = (width - artist_width) // 2  # Center horizontally

        # Draw the line at calculated position with determined font color
        draw.text(
            (artist_x, artist_y_adjusted + (i * artist_line_height)),
            line,
            font=artist_font,
            fill=font_color
        )

    # Save the record image with fixed filename
    filename = 'final_record_pressing.png'

    # Save with optimization and compression to maintain quality antialiased fonts
    img.save(filename, optimize=True, compress_level=9)
    print(f"  Saved: {filename}")

    # Final completion message
    print("-" * 80)
    print(f"\nRecord generation complete!")
    print(f"Selected label: {selected_label}")
    print(f"Font color: {font_color.upper()}")
    print(f"Successfully created 1 random record label image")
    print(f"Output location: {filename} in current directory")





    # Display the image as popup
    jukebox_selection_window.Hide()

    # Create a simple popup window with the record image
    layout = [[sg.Image(filename='final_record_pressing.png')]]
    popup_window = sg.Window('', layout, no_titlebar=True, keep_on_top=True, finalize=True)

    # Keep the popup visible for a short duration
    # ADJUST DISPLAY TIME HERE: Change the value (0.6) to control popup duration in seconds
    # Current: 0.6 seconds (600ms) - change to desired duration (e.g., 1.0 for 1 second, 2.0 for 2 seconds)
    end_time = time.time() + 0.6
    while True:
        event, values = popup_window.read(timeout=100)
        if event == sg.WINDOW_CLOSED or time.time() > end_time:
            break

    popup_window.close()
    jukebox_selection_window.UnHide()
    # update upcoming selections on jukebox screens
    upcoming_selections_update()
