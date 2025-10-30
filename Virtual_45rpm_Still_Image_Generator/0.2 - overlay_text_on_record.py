import pickle
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Load artist and song data
with open('artist_song.pkl', 'rb') as f:
    artist_song = pickle.load(f)

# Create output directory if it doesn't exist
output_dir = Path('record_labels')
output_dir.mkdir(exist_ok=True)

# Process only the first entry for testing
entry = artist_song[0]
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
    artist_font = ImageFont.truetype("arialbd.ttf", 48)  # 48pt bold for artist
    song_font = ImageFont.truetype("arialbd.ttf", 32)    # 32pt bold for song
except:
    # Fallback to default font
    artist_font = ImageFont.load_default()
    song_font = ImageFont.load_default()

# Calculate text positions to center them
# Text will be placed in the center of the record (approximately center of image)
song_bbox = draw.textbbox((0, 0), song, font=song_font)
song_width = song_bbox[2] - song_bbox[0]
song_x = (width - song_width) // 2
song_y = (height // 2) + 90  # Song on top, moved 5 pixels lower

artist_bbox = draw.textbbox((0, 0), artist, font=artist_font)
artist_width = artist_bbox[2] - artist_bbox[0]
artist_x = (width - artist_width) // 2
artist_y = (height // 2) + 190   # Artist below

# Draw the song text first
draw.text((song_x, song_y), song, font=song_font, fill="black")
# Draw the artist text second (underneath)
draw.text((artist_x, artist_y), artist, font=artist_font, fill="black")

# Save the result
safe_artist = artist.replace('/', '_').replace('\\', '_').replace(':', '_')
safe_song = song.replace('/', '_').replace('\\', '_').replace(':', '_')
filename = f'record_labels/record_test_{safe_artist}_{safe_song}.png'

img.save(filename)
print(f"Saved: {filename}")
print(f"Image saved successfully!")
