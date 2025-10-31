import pickle

# Load the artist_song.pkl file
with open('artist_song.pkl', 'rb') as f:
    artist_song = pickle.load(f)

# Print the list
print(artist_song)
