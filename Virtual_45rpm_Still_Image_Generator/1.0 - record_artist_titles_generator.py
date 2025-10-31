"""
================================================================================
RECORD ARTIST TITLES GENERATOR - 1.0
================================================================================

OVERVIEW:
This script generates custom vinyl record label images by overlaying artist and
song titles onto a blank record template. It processes a batch of artist/song
data from a pickle file and creates individual PNG files for each record.

KEY FEATURES:
- Batch processing: Generates labels for multiple records in sequence
- Auto-fit text: Dynamically adjusts font sizes to fit text within defined areas
- Text wrapping: Breaks long titles into multiple lines with proper formatting
- Centered text: All text is horizontally centered on the record label
- Safe filenames: Sanitizes artist/song names to create valid file paths

INPUT:
- artist_song.pkl: Pickle file containing list of [artist, song] tuples
- test_record_blank_record_small.png: Base record image template

OUTPUT:
- record_labels/record_NNN_ARTIST_SONG.png: Generated record label images
  (numbered sequentially from 000-348)

CONFIGURATION:
- Font: Arial Bold (arialbd.ttf)
- Max width: 300 pixels for text
- Start font size: 28pt, minimum: 16pt
- Song text: Up to 2 lines, positioned at vertical center + 90px
- Artist text: Up to 2 lines, positioned at vertical center + 125px

================================================================================
"""

import pickle
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


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


# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Load artist and song data from pickle file
print("Loading artist and song data...")
with open('artist_song.pkl', 'rb') as f:
    artist_song = pickle.load(f)
print(f"Loaded {len(artist_song)} records")

# Create output directory if it doesn't exist
output_dir = Path('record_labels')
output_dir.mkdir(exist_ok=True)

# Load the base record image once (efficiency optimization)
print("Loading base record template...")
base_img = Image.open('test_record_blank_record_small.png')

# Get image dimensions for positioning calculations
width, height = base_img.size

# Configuration settings
font_path = "arialbd.ttf"          # Font to use for text
max_text_width = 300               # Maximum width for wrapped text (pixels)
song_y = (height // 2) + 90        # Y position for song title (below center)
artist_y = (height // 2) + 125     # Y position for artist name (below song)
song_line_height = 25              # Vertical spacing between song title lines
artist_line_height = 30            # Vertical spacing between artist name lines

print(f"Starting batch processing...")
print("-" * 80)

# Process each record in the dataset
for idx, entry in enumerate(artist_song):
    artist = entry[0]
    song = entry[1]

    # Display progress
    print(f"[{idx + 1}/{len(artist_song)}] Creating record for: {artist} - {song}")

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

        # Draw the line at calculated position
        draw.text(
            (song_x, song_y + (i * song_line_height)),
            line,
            font=song_font,
            fill="black"
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

        # Draw the line at calculated position
        draw.text(
            (artist_x, artist_y_adjusted + (i * artist_line_height)),
            line,
            font=artist_font,
            fill="black"
        )

    # Save the record image with sanitized filename
    # Replace special characters that are invalid in filenames
    safe_artist = artist.replace('/', '_').replace('\\', '_').replace(':', '_')
    safe_song = song.replace('/', '_').replace('\\', '_').replace(':', '_')

    # Create filename with sequential numbering (000-348)
    filename = f'record_labels/record_{idx:03d}_{safe_artist}_{safe_song}.png'

    # Save the image file
    img.save(filename)
    print(f"  Saved: {filename}")

# Final completion message
print("-" * 80)
print(f"\nBatch processing complete!")
print(f"Successfully created {len(artist_song)} record label images")
print(f"Output location: record_labels/")
