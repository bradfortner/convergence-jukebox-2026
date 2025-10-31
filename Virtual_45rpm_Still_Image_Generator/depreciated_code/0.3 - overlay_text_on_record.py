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

# Load artist and song data
with open('artist_song.pkl', 'rb') as f:
    artist_song = pickle.load(f)

# Create output directory if it doesn't exist
output_dir = Path('record_labels')
output_dir.mkdir(exist_ok=True)

# Process only the second entry for testing
entry = artist_song[1]
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

# Try to use a bold font, fallback to default if not available
try:
    artist_font = ImageFont.truetype("arialbd.ttf", 28)  # 28pt bold for artist
    song_font = ImageFont.truetype("arialbd.ttf", 28)    # 28pt bold for song
except:
    # Fallback to default font
    artist_font = ImageFont.load_default()
    song_font = ImageFont.load_default()

# Maximum width for text wrapping (in pixels)
max_text_width = 300

# Wrap song text
song_lines = wrap_text(song, song_font, max_text_width, draw)
artist_lines = wrap_text(artist, artist_font, max_text_width, draw)

# Calculate starting positions
song_y = (height // 2) + 90
artist_y = (height // 2) + 125

# Line height for wrapped text
song_line_height = 25
artist_line_height = 55

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
print(f"Song lines: {len(song_lines)}")
print(f"Artist lines: {len(artist_lines)}")
print(f"Image saved successfully!")
