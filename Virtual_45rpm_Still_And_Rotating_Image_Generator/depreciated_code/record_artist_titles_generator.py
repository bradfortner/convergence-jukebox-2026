"""
Record Artist Titles Generator

This script reads a log.txt file containing comma-separated jukebox log entries,
parses the data to extract artist and song title information, and generates a
structured list of [artist, song] pairs. The processed data is then saved as a
pickle file for later use.

The log.txt file contains entries in the format:
  timestamp, song_filename.mp3, mode_status, mode_value

This script extracts every 3rd element (the song_filename) starting at index 1,
removes the .mp3 extension, and splits on ' - ' to separate artist from title.

Output:
  - Prints the artist_song list to the terminal
  - Saves the list to artist_song.pkl for serialized storage
"""

import pickle

# Read the log.txt file and store its contents
with open('log.txt', 'r') as file:
    log_content = file.read()

# Parse the log content by splitting on commas and stripping whitespace
# This creates a flat list of all log entries
record_artist_titles = [item.strip() for item in log_content.split(',') if item.strip()]

# Create artist_song list by extracting song entries and splitting on ' - '
# The log structure repeats every 3 entries: [timestamp, song, mode, value, ...]
# We extract every 3rd element starting at index 1 (the song filename)
artist_song = []
for i in range(1, len(record_artist_titles), 3):
    # Remove the .mp3 extension from the song filename
    song = record_artist_titles[i].replace('.mp3', '')
    # Split the song string on ' - ' to separate artist and title
    # Result: ['Artist Name', 'Song Title']
    artist_song.append(song.split(' - '))

# Print the parsed artist_song list to the terminal for verification
print(artist_song)

# Save the artist_song list as a pickle file for later retrieval
# This allows the data to be loaded efficiently in other Python scripts
with open('artist_song.pkl', 'wb') as pkl_file:
    pickle.dump(artist_song, pkl_file)
