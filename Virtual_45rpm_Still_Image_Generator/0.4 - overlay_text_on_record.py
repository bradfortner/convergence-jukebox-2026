import pickle
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    return lines

def fit_text_to_width(text, base_font_path, start_size, max_width, max_lines, draw):
    """
    Auto-fit text by reducing font size until it fits on 1 line or within max_lines
    Returns: list of lines, the font size used, and the font object
    """
    font_size = start_size
    min_font_size = 16  # Don't go smaller than 16pt

    while font_size >= min_font_size:
        font = ImageFont.truetype(base_font_path, font_size)
        lines = wrap_text(text, font, max_width, draw)

        # Prefer single line, but allow up to max_lines
        if len(lines) == 1:
            return lines, font_size, font

        # If 2 lines and within max_lines, but text is still long, try smaller
        if len(lines) <= max_lines:
            # Check if reducing size would help (try next size down)
            test_font = ImageFont.truetype(base_font_path, font_size - 2)
            test_lines = wrap_text(text, test_font, max_width, draw)
            if len(test_lines) <= max_lines:
                font_size -= 2
                continue
            else:
                return lines, font_size, font

        font_size -= 2  # Reduce by 2pt and try again

    # Last resort - use minimum font size
    font = ImageFont.truetype(base_font_path, min_font_size)
    return wrap_text(text, font, max_width, draw), min_font_size, font

# Load artist and song data
with open('artist_song.pkl', 'rb') as f:
    artist_song = pickle.load(f)

# Create output directory if it doesn't exist
output_dir = Path('record_labels')
output_dir.mkdir(exist_ok=True)

# Process only the third entry for testing
entry = artist_song[2]
artist = entry[0]
song = entry[1]

print(f"Creating record for: {artist} - {song}")

# Open the base record image
base_img = Image.open('test_record_blank_record_small.png')

# Create a copy to draw on
img = base_img.copy()
draw = ImageDraw.Draw(img)

# Get image dimensions
width, height = img.size

# Font path
font_path = "arialbd.ttf"

# Maximum width for text wrapping (in pixels)
max_text_width = 300

# Calculate starting positions
song_y = (height // 2) + 90
artist_y = (height // 2) + 125

# Line height for wrapped text
song_line_height = 25
artist_line_height = 30

# Auto-fit song text (start at 28pt, max 2 lines)
song_lines, song_font_size, song_font = fit_text_to_width(song, font_path, 28, max_text_width, 2, draw)
print(f"Song font size: {song_font_size}pt, lines: {len(song_lines)}")

# Auto-fit artist text (start at 28pt, max 2 lines)
artist_lines, artist_font_size, artist_font = fit_text_to_width(artist, font_path, 28, max_text_width, 2, draw)
print(f"Artist font size: {artist_font_size}pt, lines: {len(artist_lines)}")

# Draw song lines
for i, line in enumerate(song_lines):
    song_bbox = draw.textbbox((0, 0), line, font=song_font)
    song_width = song_bbox[2] - song_bbox[0]
    song_x = (width - song_width) // 2
    draw.text((song_x, song_y + (i * song_line_height)), line, font=song_font, fill="black")

# Adjust artist Y position based on number of song lines
artist_y_adjusted = artist_y + ((len(song_lines) - 1) * song_line_height)

# Draw artist lines
for i, line in enumerate(artist_lines):
    artist_bbox = draw.textbbox((0, 0), line, font=artist_font)
    artist_width = artist_bbox[2] - artist_bbox[0]
    artist_x = (width - artist_width) // 2
    draw.text((artist_x, artist_y_adjusted + (i * artist_line_height)), line, font=artist_font, fill="black")

# Save the result
safe_artist = artist.replace('/', '_').replace('\\', '_').replace(':', '_')
safe_song = song.replace('/', '_').replace('\\', '_').replace(':', '_')
filename = f'record_labels/record_test_{safe_artist}_{safe_song}.png'

img.save(filename)
print(f"Saved: {filename}")
print(f"Image saved successfully!")
