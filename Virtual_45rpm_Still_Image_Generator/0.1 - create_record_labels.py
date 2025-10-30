import pickle
from pictex import Canvas, Column, Text, Image
from pathlib import Path

# Load artist and song data
with open('artist_song.pkl', 'rb') as f:
    artist_song = pickle.load(f)

# Create output directory if it doesn't exist
output_dir = Path('record_labels')
output_dir.mkdir(exist_ok=True)

# Create record images with artist and song titles
for i, entry in enumerate(artist_song):
    artist = entry[0]
    song = entry[1]

    # Create the composition using Canvas
    canvas = Canvas()

    # Create the record card with image and text overlay
    record_card = (
        Column(
            Image('test_record_blank_record_small.png'),
            Column(
                Text(artist).font_size(16).color("black"),
                Text(song).font_size(14).color("black")
            ).horizontal_align("center").gap(4)
        ).horizontal_align("center")
    )

    # Render the composition
    result = canvas.render(record_card)

    # Save the result
    # Create a safe filename
    safe_artist = artist.replace('/', '_').replace('\\', '_').replace(':', '_')
    safe_song = song.replace('/', '_').replace('\\', '_').replace(':', '_')
    filename = f'record_labels/record_{i:03d}_{safe_artist}_{safe_song}.png'

    result.save(filename)
    print(f"Created: {filename} - {artist} - {song}")

print(f"\nComplete! Created {len(artist_song)} record label images in the 'record_labels' directory.")
