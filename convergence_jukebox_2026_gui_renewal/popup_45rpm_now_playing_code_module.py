"""
45RPM Now-Playing Record Pop-up Code Module
Handles the display of 45rpm record labels with now-playing song information as animated popups
"""
import threading
from pathlib import Path
import os
import random
import textwrap
import time
from PIL import Image, ImageDraw, ImageFont
import pygame
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
    # Use RGBA tuples (R, G, B, Alpha) where 255 = fully opaque
    font_color = (255, 255, 255, 255) if selected_label.startswith("w_") else (0, 0, 0, 255)
    color_mode = "WHITE" if selected_label.startswith("w_") else "BLACK"
    print(f"Font color mode: {color_mode}")

    # Load the selected record label image
    print("Loading blank record label template...")
    base_img = Image.open(label_path)

    # Get image dimensions for positioning calculations
    width, height = base_img.size

    # Configuration settings
    font_path = "fonts/OpenSans-ExtraBold.ttf"          # Font to use for text
    max_text_width = 300               # Maximum width for wrapped text (pixels)
    song_y = (height // 2) + 90        # Y position for song title (below center)
    artist_y = (height // 2) + 125     # Y position for artist name (below song)
    song_line_height = 25              # Vertical spacing between song title lines
    artist_line_height = 30            # Vertical spacing between artist name lines

    print(f"Creating record label with {color_mode} text...")
    print("-" * 80)

    # Create a working copy of the base image and convert to RGBA
    img = base_img.copy()
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

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

    # Make the background transparent before saving
    # Get the background color from corner pixels
    background_color = img.getpixel((0, 0))

    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Create a transparent version by replacing background color with alpha=0
    # Get all pixels
    pixels = img.getdata()
    new_pixels = []

    # Color tolerance for matching background
    tolerance = 40

    for pixel in pixels:
        # Check if pixel matches background color (with tolerance)
        if (abs(pixel[0] - background_color[0]) < tolerance and
            abs(pixel[1] - background_color[1]) < tolerance and
            abs(pixel[2] - background_color[2]) < tolerance and
            pixel[0:3] != (0, 0, 0)):  # Don't remove black text
            # Make this pixel transparent
            new_pixels.append((255, 255, 255, 0))  # Transparent white
        else:
            # Keep the pixel but ensure it has full alpha
            if len(pixel) == 3:
                new_pixels.append((pixel[0], pixel[1], pixel[2], 255))
            else:
                new_pixels.append(pixel)

    img.putdata(new_pixels)

    # Save as PNG with transparency support
    img.save(filename, 'PNG')
    print(f"  Saved: {filename} (with transparent background)")

    # Final completion message
    print("-" * 80)
    print(f"\nRecord generation complete!")
    print(f"Selected label: {selected_label}")
    print(f"Font color: {color_mode}")
    print(f"Successfully created 1 random record label image")
    print(f"Output location: {filename} in current directory")


    # Display the image as popup
    jukebox_selection_window.Hide()

    # Display the record label using Pygame with color key transparency
    try:
        # Initialize Pygame
        pygame.init()
        pygame.mixer.quit()  # Disable audio to avoid conflicts

        # Load the record label image
        record_image = pygame.image.load('final_record_pressing.png').convert()
        img_width, img_height = record_image.get_size()

        # Create window without frame
        screen = pygame.display.set_mode((img_width, img_height), pygame.NOFRAME | pygame.DOUBLEBUF)
        pygame.display.set_caption('')

        # Set up Windows API for always-on-top and transparency
        try:
            import ctypes
            user32 = ctypes.windll.user32

            # Get Pygame window handle
            hwnd_val = pygame.display.get_wm_info()['window']

            # Set window to always be on top (SetWindowPos with HWND_TOPMOST = -1)
            user32.SetWindowPos(hwnd_val, -1, 0, 0, 0, 0, 0x0001)  # SWP_NOSIZE

            print(f"Popup window handle: {hwnd_val}")
            print("Window set to always-on-top")

        except Exception as e:
            print(f"Note: Could not set always-on-top: {e}")

        # Display the image
        screen.blit(record_image, (0, 0))
        pygame.display.flip()

        # Keep the popup visible for a short duration
        # ADJUST DISPLAY TIME HERE: Change the value (3.0) to control popup duration in seconds
        # Current: 3.0 seconds (3000ms) - change to desired duration (e.g., 1.0 for 1 second, 2.0 for 2 seconds)
        display_duration = 3.0
        end_time = time.time() + display_duration
        clock = pygame.time.Clock()

        print(f"Displaying record label popup for {display_duration} seconds...")

        while time.time() < end_time:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    break

            screen.blit(record_image, (0, 0))
            pygame.display.flip()
            clock.tick(30)  # 30 FPS

        print("Closing popup window...")
        pygame.quit()

    except Exception as e:
        print(f"Error displaying record label popup: {e}")
        import traceback
        traceback.print_exc()
        try:
            pygame.quit()
        except:
            pass

    jukebox_selection_window.UnHide()
    # update upcoming selections on jukebox screens
    upcoming_selections_update()
