# Read log.txt and parse comma-separated values into a list
import pickle

with open('log.txt', 'r') as file:
    log_content = file.read()

# Split by comma and strip whitespace from each entry
record_artist_titles = [item.strip() for item in log_content.split(',') if item.strip()]

# Create artist_song list by splitting on ' - ' separator
artist_song = []
for i in range(1, len(record_artist_titles), 3):
    song = record_artist_titles[i].replace('.mp3', '')
    artist_song.append(song.split(' - '))

# Print the artist_song list
print(artist_song)

# Save the artist_song list as a pickle file
with open('artist_song.pkl', 'wb') as pkl_file:
    pickle.dump(artist_song, pkl_file)
