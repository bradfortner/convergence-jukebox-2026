# Convergence Jukebox 2026 - Player Renewal

A sophisticated Python-based jukebox engine with real-time playlist management, comprehensive statistics tracking, and professional code architecture. This application provides an intelligent music playback system with support for both random and paid song requests.

## Overview

The Convergence Jukebox is a feature-rich music player that combines random song selection with a priority-based paid request system. It monitors multiple playlist files in real-time, automatically transitions between song types, and maintains detailed playback statistics for analytics.

**Current Version**: 0.91

## Features

### Core Functionality
- **Dual Playlist System**: Manage both random and paid music selections
- **Real-Time Playlist Monitoring**: Automatically detects and responds to paid song requests added during playback
- **VLC Integration**: Uses python-vlc for reliable cross-platform audio playback
- **Nested Loop Architecture**: Intelligently prioritizes paid songs while ensuring random selections continue

### Code Quality & Architecture
- **Type Hints**: Comprehensive Python type annotations for all methods and variables
- **Class-Based Design**: Eliminated global variables through object-oriented architecture
- **No Code Duplication**: Unified song handling methods for consistent behavior
- **Cross-Platform Paths**: Automatic path resolution for Windows, macOS, and Linux
- **Enhanced Error Handling**: Robust exception handling with detailed logging

### Advanced Features
- **Input Validation**: Comprehensive data integrity checking for all inputs
- **Refactored for Testability**: Extracted I/O operations enable easy unit testing
- **Memory Optimization**: Automatic garbage collection and memory monitoring
- **Background Threading**: Non-blocking real-time paid song detection during playback
- **Song Statistics**: Persistent tracking of play counts, history, and preferences
- **Configurable Logging**: Enable/disable logging with customizable formats and levels
- **Console Output**: Color-coded messages with professional formatting
- **Configuration Management**: JSON-based configuration with sensible defaults

## Installation

### Requirements
- Python 3.7+
- VLC media player (system installation required)
- Python packages: `python-vlc`, `psutil`

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/bradfortner/convergence-jukebox-2026.git
   cd convergence-jukebox-2026/convergence_jukebox_2026_player_renewal
   ```

2. **Install VLC** (if not already installed)
   - Windows: Download from https://www.videolan.org/vlc/
   - macOS: `brew install vlc`
   - Linux: `sudo apt-get install vlc`

3. **Install Python dependencies**
   ```bash
   pip install python-vlc psutil
   ```

4. **Organize your music**
   - Create a `music/` directory in the project folder
   - Add your MP3 files to the `music/` directory
   - Subdirectories are not scanned; keep songs in the root `music/` folder

5. **Run the jukebox**
   ```bash
   python "0.91 - main_jukebox_engine.py"
   ```

## Configuration

The jukebox creates a `jukebox_config.json` file on first run. You can customize these settings:

### Configuration File Structure

```json
{
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s"
  },
  "console": {
    "show_headers": true,
    "color_enabled": true,
    "song_display_format": "detailed"
  },
  "paths": {
    "music_directory": "music",
    "log_file": "log.txt",
    "statistics_file": "song_statistics.json"
  }
}
```

### Configuration Options

**Logging**
- `enabled`: Enable/disable file logging (bool)
- `level`: Log level - DEBUG, INFO, WARNING, ERROR (string)
- `format`: Python logging format string (string)

**Console Output**
- `show_headers`: Display section headers in console (bool)
- `color_enabled`: Use colored output in console (bool)
- `song_display_format`: Set to "detailed" or "simple" (string)

**Paths**
- `music_directory`: Relative or absolute path to music folder (string)
- `log_file`: Filename for logging output (string)
- `statistics_file`: Filename for song statistics JSON (string)

## Usage Guide

### File Structure

Your project directory should contain:

```
convergence_jukebox_2026_player_renewal/
├── 0.91 - main_jukebox_engine.py
├── jukebox_config.json
├── MusicMasterSongList.txt
├── GenreFlagsList.txt
├── PaidMusicPlayList.txt
├── CurrentSongPlaying.txt
├── song_statistics.json
├── log.txt
├── music/
│   ├── song1.mp3
│   ├── song2.mp3
│   └── ...
└── README.md
```

### Playlist Files

**MusicMasterSongList.txt**
- JSON array of all available songs
- Auto-generated on first run
- Format: `[{"title": "Song Name", "artist": "Artist Name", ...}, ...]`

**GenreFlagsList.txt**
- JSON array of genre tags
- Auto-generated during metadata generation
- Used for categorizing songs

**PaidMusicPlayList.txt**
- JSON array of song indices for paid requests
- Real-time monitored - add indices while jukebox is running
- Format: `[0, 5, 12]` (song indices from MusicMasterSongList)
- Example: If you want song at index 3 to play next, add `3` to this file

**CurrentSongPlaying.txt**
- Tracks currently playing song information
- Updated in real-time during playback
- Useful for external displays or monitoring

### Running the Jukebox

```bash
python "0.91 - main_jukebox_engine.py"
```

The jukebox will:
1. Load configuration from `jukebox_config.json`
2. Generate metadata for all MP3 files in `music/` directory
3. Load song statistics from previous sessions
4. Start monitoring for paid song requests
5. Enter playback loop:
   - Check for paid songs in `PaidMusicPlayList.txt`
   - Play all requested paid songs in queue
   - Play one random song
   - Return to step 1

### Adding Paid Song Requests

1. Find the song index in `MusicMasterSongList.txt` (first song is index 0)
2. Add the index to `PaidMusicPlayList.txt`
3. The jukebox will detect it during the next playlist check and play it

Example:
```json
// MusicMasterSongList.txt shows:
[
  {"title": "Song A", ...},
  {"title": "Song B", ...},
  {"title": "Song C", ...}
]

// Add to PaidMusicPlayList.txt:
[1, 2]  // Will play Song B and Song C next
```

## Statistics & Reporting

The jukebox tracks detailed statistics for every song played:

### What Gets Tracked

- **Play Count**: Total times each song has been played
- **Last Played**: Timestamp of most recent playback
- **Play History**: Last 100 playback instances with timestamps and play type (paid/random)
- **Song Metadata**: Title and artist information

### Accessing Statistics

Statistics are automatically displayed when the jukebox shuts down:

```
╔════════════════════════════════════════╗
║       PLAYBACK STATISTICS REPORT       ║
╚════════════════════════════════════════╝
Total Songs Played: 47
Unique Songs: 23

Top 10 Most Played Songs:
1. Song Title (Play Count: 5)
2. Another Song (Play Count: 4)
...
```

### Statistics File

Statistics are saved to `song_statistics.json` after each session:

```json
{
  "0": {
    "title": "Song Name",
    "artist": "Artist Name",
    "play_count": 5,
    "last_played": "2025-10-24 14:30:45",
    "play_history": [
      {
        "timestamp": "2025-10-24 14:30:45",
        "type": "random"
      },
      {
        "timestamp": "2025-10-24 14:25:20",
        "type": "paid"
      }
    ]
  }
}
```

### Using Statistics

- View top played songs to understand listener preferences
- Analyze play patterns across time
- Identify underplayed songs for promotion
- Track paid vs. random play distribution

## Logging

### Console Output

The jukebox provides color-coded console output:

- **HEADER**: Purple - Section headers and dividers
- **INFO**: Blue - General information messages
- **SUCCESS**: Dark Green - Successful operations
- **WARNING**: Yellow - Non-critical issues
- **ERROR**: Red - Error conditions

### Log File

Logs are written to `log.txt` by default with timestamps and log levels:

```
2025-10-24 14:25:30 - INFO - Starting jukebox engine
2025-10-24 14:25:35 - INFO - Generated metadata for 150 songs
2025-10-24 14:25:40 - INFO - Now Playing: Song Title by Artist Name
2025-10-24 14:30:45 - WARNING - High memory usage: 215.3MB
```

Configure logging behavior in `jukebox_config.json` under the `logging` section.

## Architecture Highlights

### Object-Oriented Design
- Single `JukeboxEngine` class encapsulates all functionality
- Instance variables replace global state
- Clean separation of concerns with dedicated methods

### Input Validation
- All song indices validated before use
- File path accessibility checked before operations
- JSON data structure validation for data integrity
- Graceful error handling with informative messages

### Testability
- I/O operations extracted into separate methods
- File reading/writing centralized for easy mocking
- Validation logic isolated from business logic
- Method signatures designed for unit testing

### Performance
- Garbage collection triggered every 500 songs processed
- Memory monitoring with warnings at 200MB+ usage
- Background thread for non-blocking paid song detection
- Efficient playlist searches and validations

### Threading
- Daemon thread monitors `PaidMusicPlayList.txt` during playback
- Thread-safe access using `threading.Lock()`
- Non-blocking detection of new paid requests
- Graceful shutdown of background threads

## Version History

- **0.91**: Added input validation, testability refactoring, and song statistics
- **0.9**: Memory optimization, threading support, enhanced docstrings
- **0.8**: Console colors, logging configuration, config file support
- **0.7**: Comprehensive type hints throughout codebase
- **0.6**: Cross-platform path handling
- **0.5**: Removed dead code
- **0.4**: Eliminated code duplication
- **0.3**: Error handling and logging
- **0.2**: Recursive call fixes
- **0.1**: Eliminated global variables
- **0.0**: Initial baseline

## Troubleshooting

### VLC Not Found
- Ensure VLC is installed on your system
- On Windows, add VLC to your PATH environment variable
- Restart your terminal/command prompt after installing VLC

### No Songs Detected
- Verify MP3 files are in the `music/` directory (not subdirectories)
- Check that filenames are valid and readable
- Run the jukebox - it will generate `MusicMasterSongList.txt` with found songs

### Paid Songs Not Playing
- Check that indices in `PaidMusicPlayList.txt` are valid (0 to max song index)
- Verify JSON format is correct: `[0, 1, 2]` or `[0]`
- Check console output for validation errors

### Memory Issues
- Long sessions may accumulate memory; consider periodic restarts
- Check `log.txt` for memory warning messages
- Reduce music library size if needed

### High CPU Usage
- Normal during playback and file scanning
- Background thread uses minimal resources (checks every 1 second)
- Consider closing other applications for better performance

## Contributing

This is an actively developed project. For bug reports or feature requests, please open an issue on GitHub.

## License

This project is part of the Convergence Jukebox suite.

## Support

For issues, questions, or suggestions, visit the project repository:
https://github.com/bradfortner/convergence-jukebox-2026
