import pickle
from pictex import Canvas, Column, Text, Image, Box
from pathlib import Path

# Load artist and song data
with open('artist_song.pkl', 'rb') as f:
    artist_song = pickle.load(f)

# Create output directory if it doesn't exist
output_dir = Path('record_labels')
output_dir.mkdir(exist_ok=True)

# Process only the first entry
entry = artist_song[0]
artist = entry[0]
song = entry[1]

print(f"Creating record for: {artist} - {song}")

# Create the composition using Canvas
canvas = Canvas()

# Create the record with centered text overlay using Column and padding
record_with_text = (
    Column(
        Image('test_record_blank_record_small.png'),
        Column(
            Text(artist).font_size(18).font_weight(700).color("black"),
            Text(song).font_size(16).color("black")
        ).horizontal_align("center").gap(8)
    ).horizontal_align("center")
)

# Render the composition
result = canvas.render(record_with_text)

# Save the result
safe_artist = artist.replace('/', '_').replace('\\', '_').replace(':', '_')
safe_song = song.replace('/', '_').replace('\\', '_').replace(':', '_')
filename = f'record_labels/record_001_{safe_artist}_{safe_song}.png'

result.save(filename)
print(f"Saved: {filename}")
print(f"Image saved successfully!")
