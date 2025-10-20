# Convergence Jukebox - Pygame GUI Rewrite

A complete rewrite of the Convergence Jukebox GUI from the abandoned PySimpleGUI library to Pygame, providing full control over the custom arcade-style interface.

## Project Status

🚀 **Phase 1-2: Complete** (Project Structure & Data Layer)
⚙️ **Phase 3: In Progress** (Core Pygame Shell)
⏳ **Phases 4-11: Pending** (UI Components, Screens, Integration)

## Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. Navigate to the project directory:
```bash
cd convergence-jukebox-pygame
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

The application will:
1. Load `MusicMasterSongList.txt` from the parent directory
2. Display the Convergence Jukebox interface
3. Show the main song selection screen

## Project Structure

```
convergence-jukebox-pygame/
├── main.py                      # Application entry point
├── config.py                    # Configuration constants
├── data_manager.py              # Song list & persistence layer
├── ui_engine.py                 # Pygame rendering engine
├── components/                  # Reusable UI components
│   ├── button.py               # Button widget
│   ├── text_display.py         # Text rendering
│   ├── grid.py                 # Song selection grid
│   └── keypad.py               # Number/letter pad
├── screens/                     # Application screens
│   ├── base_screen.py          # Base screen class
│   ├── selection_screen.py     # Main song selection (21 grid)
│   ├── info_screen.py          # Now playing + upcoming
│   ├── control_screen.py       # A/B/C + numbers + search
│   ├── search_screen.py        # Search modal
│   └── record_label_screen.py  # 45 RPM animation
├── services/                    # External services
│   ├── vlc_service.py          # VLC integration
│   ├── file_service.py         # File I/O
│   ├── image_service.py        # PIL integration
│   └── audio_service.py        # Sound effects
├── assets/                      # Media assets
│   ├── images/                 # Button backgrounds, arrows
│   ├── fonts/                  # TTF font files
│   ├── sounds/                 # buzz.mp3, success.mp3
│   └── record_labels/          # 45 RPM templates
├── tests/                       # Unit tests
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Architecture Overview

### Data Layer (`data_manager.py`)
- **DataManager**: Central hub for all data operations
  - Song list management (load, search, pagination)
  - State management (selection, credits, queue)
  - File persistence (JSON, logging)
  - Band name processing

### UI Engine (`ui_engine.py`)
- **UIEngine**: Pygame rendering abstraction
  - Font management with caching
  - Drawing primitives (rect, text, images)
  - Event handling (mouse, keyboard)

- **Button**: Reusable button component
  - Hover states, enabled/disabled
  - Dynamic font sizing
  - Image backgrounds

- **ButtonGrid**: 2D button grid
  - Song display grid (21 buttons for 3×7 layout)
  - Batch enable/disable operations

### Application Core (`main.py`)
- **JukeboxApplication**: Main application loop
  - Event handling and routing
  - Update cycle
  - Rendering pipeline
  - Lifecycle management

## Key Features

### Song Selection
- **3-Column × 7-Row Grid**: Display 21 songs per page
- **Pagination**: Left/Right arrows to scroll through all songs
- **Dynamic Font Sizing**: Text automatically scales to fit buttons
- **Column Modes**: A/B/C mode buttons for column navigation
- **Row Selection**: Number pad (1-7) for row selection
- **Song Confirmation**: Select button to confirm selection

### Information Display
- **Now Playing**: Large display of current song
- **Upcoming Queue**: Show next 10 selections
- **Credits Display**: Current balance and pricing
- **Song Metadata**: Title, artist, year, album, duration

### Search Functionality
- **Modal Search**: Overlay search interface
- **Title/Artist Search**: Find songs by name
- **Letter/Number Keypad**: Natural input method
- **5-Result Display**: Show matching songs
- **Navigation**: Previous/Next buttons for results

### 45 RPM Record Label Animation
- **Random Template**: Select from record label templates
- **Dynamic Text**: Add song title and artist to label
- **Font Scaling**: Text size based on string length
- **Animation**: 600-frame GIF display (10 seconds)
- **Text Wrapping**: Long names wrap to multiple lines

### Credit System
- **Manual Credits**: Add funds to account
- **Per-Song Cost**: $0.25 per selection
- **Immediate Deduction**: Subtract when song queued
- **Balance Display**: Always visible on screen

## Data Structures

### Song Dictionary
```python
{
    'number': int,              # Unique ID (0-indexed)
    'location': str,            # File path to MP3
    'title': str,               # Song title
    'artist': str,              # Artist name
    'album': str,               # Album name
    'year': str,                # Release year
    'comment': str,             # Genre(s)
    'duration': str             # MM:SS format
}
```

### Jukebox State
```python
{
    'selection_window_number': int,     # Current page (0-N)
    'credit_amount': float,             # in 0.25 increments
    'upcoming_playlist': List[str],     # Queue display names
    'selected_letter': str,             # A, B, or C
    'selected_number': str,             # 1-7
    'last_song_playing': str            # Track for changes
}
```

## Configuration

Edit `config.py` to customize:
- Screen dimensions and colors
- Font sizes and file paths
- Asset locations
- Control mappings
- Timing and animation settings

Key settings:
- `SCREEN_WIDTH`, `SCREEN_HEIGHT`: Display resolution
- `FONT_PATH`: Custom font file
- `SONGS_PER_PAGE`: Page size (default 21)
- `CREDIT_INCREMENT`: Cost per song
- `RECORD_LABEL_DURATION`: Animation length in frames

## File I/O

The application reads from and writes to:
- **MusicMasterSongList.txt**: Complete song database (JSON)
- **PaidMusicPlayList.txt**: Queue of songs to play (JSON)
- **CurrentSongPlaying.txt**: Currently playing file path
- **the_bands.txt**: Band names needing "The" prefix
- **the_exempted_bands.txt**: Excluded band names
- **GenreFlagsList.txt**: Genre filters for random play
- **log.txt**: Audit log of all selections

## Development Roadmap

### Phase 3: Core Pygame Shell ✅
- [x] Project structure
- [x] Configuration system
- [x] Data persistence layer
- [x] Pygame initialization
- [ ] Event loop finalization
- [ ] Screen management system

### Phase 4: UI Components
- [ ] Button widget improvements
- [ ] Text display system
- [ ] Grid layout system
- [ ] Keypad component
- [ ] Component-based architecture

### Phase 5: Selection Screen
- [ ] 21-song grid display
- [ ] Column/row selection
- [ ] Pagination with arrows
- [ ] Band name processing
- [ ] Dynamic font sizing

### Phase 6: Info Screen
- [ ] Now playing display
- [ ] Upcoming queue display
- [ ] Credits display
- [ ] Real-time updates
- [ ] File monitoring thread

### Phase 7: Control Panel
- [ ] Mode selection buttons (A/B/C)
- [ ] Number pad (1-7)
- [ ] Select/Correct buttons
- [ ] State machine
- [ ] Button enable/disable logic

### Phase 8: Search Window
- [ ] Modal overlay
- [ ] Keypad input
- [ ] Result display
- [ ] Search filtering
- [ ] Navigation

### Phase 9: Record Labels
- [ ] PIL integration
- [ ] Template loading
- [ ] Text rendering
- [ ] GIF animation
- [ ] Popup display

### Phase 10: Engine Integration
- [ ] VLC service
- [ ] File I/O service
- [ ] Audio service
- [ ] Queue management
- [ ] Background monitoring

### Phase 11: Testing & Optimization
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance profiling
- [ ] Memory optimization
- [ ] Bug fixes

## Debugging

### Enable Debug Output
```python
# In main.py
DEBUG = True  # Set to True for verbose output
```

### Check Song Loading
```bash
python -c "from data_manager import DataManager; dm = DataManager(); dm.initialize(); print(f'Loaded {len(dm.songs)} songs')"
```

### Test Pygame Installation
```bash
python -m pygame.examples.aliens
```

## Known Issues & Limitations

| Issue | Status | Notes |
|-------|--------|-------|
| VLC integration | TODO | Needs testing with python-vlc |
| Image asset loading | TODO | Requires valid image files |
| Font rendering | TODO | Falls back to system font if custom font missing |
| Threading | TODO | Background monitoring thread not yet implemented |

## Performance Targets

- **FPS**: 60 FPS (60 Hz)
- **Load Time**: < 2 seconds (song list)
- **Screen Transition**: < 0.5 seconds
- **Search Response**: < 100ms
- **Memory Usage**: < 200MB

## Contributing

When adding new features:
1. Create feature branch
2. Update relevant config in `config.py`
3. Add unit tests
4. Update migration plan
5. Document changes in README

## Troubleshooting

### "Module not found: pygame"
```bash
pip install pygame
```

### "Font file not found"
- Place TTF files in `assets/fonts/`
- Or edit `config.py` to use system font

### "No songs loaded"
- Verify `MusicMasterSongList.txt` exists in parent directory
- Check file format (should be valid JSON)
- Run: `python -c "import json; json.load(open('../MusicMasterSongList.txt'))"`

### "Image assets missing"
- Create `assets/images/` directory
- Place button backgrounds, arrows, etc. in it
- Update `config.py` with correct paths

## License

This project is part of the Convergence Jukebox initiative.

## Support

For issues or questions:
1. Check this README
2. Review the migration plan in parent directory
3. Check debug output
4. Review `log.txt` for errors

---

**Last Updated**: October 20, 2025
**Version**: 0.1.0 (Alpha)
**Status**: In Development
