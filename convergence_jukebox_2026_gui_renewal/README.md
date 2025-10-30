# Convergence Jukebox 2026 - GUI Renewal

A modern, modular implementation of the Convergence Jukebox 2026 graphical user interface using **FreeSimpleGUI** (drop-in replacement for deprecated PySimpleGUI).

## Overview

The Convergence Jukebox 2026 is a comprehensive jukebox application that displays and plays music with an interactive GUI. This GUI renewal project implements a clean, modular architecture that separates concerns and improves maintainability by extracting functional components into independent modules.

**Current Version:** 0.61 - main_jukebox_GUI_2026.py

## Features

✅ **Full FreeSimpleGUI Integration**
- Modern, responsive GUI built with FreeSimpleGUI
- Cross-platform support (Windows & Linux)
- Custom title bar and transparent windows
- Background image support (embedded as base64)
- Animated popup displays for visual feedback

✅ **Modular Architecture**
- 15+ separate, independent function modules
- Continuous refactoring to extract functionality
- Clean separation of concerns
- Easy to test and maintain
- Parameter-based function design (no closure dependencies)

✅ **Rich Media Support**
- 200+ record label images with variants
- Selection animations and UI icons
- 45RPM record label generator with dynamic text
- Embedded background image (623KB)
- Custom fonts (OpenSans-ExtraBold)

✅ **Advanced Features**
- Song selection system (A1-C7 grid)
- Band name auto-detection with exemptions
- Dynamic font sizing based on text length
- Upcoming songs queue display
- VLC media player integration for audio playback
- Background thread for real-time UI updates
- Animated 45RPM record popup with customizable display duration

## Architecture

### File Structure

```
convergence_jukebox_2026_gui_renewal/
├── 0.61 - main_jukebox_GUI_2026.py      # Production main file (current) - the_bands_name_check & upcoming_selections_update module rename
├── 0.60 - main_jukebox_GUI_2026.py      # Previous version - search_window_button_layout module rename
│
├── Modular Function Files:
├── info_screen_layout_module.py          # Info screen layout module
├── jukebox_selection_screen_layout_module.py # Selection screen layout
├── control_button_screen_layout_module.py # Control button layout
├── search_window_button_layout_module.py # Search window buttons
├── font_size_window_updates_module.py    # Font sizing logic
├── font_size_window_updates_1.py         # Extended font sizing (archived)
├── upcoming_selections_update_module.py  # Queue display updates
├── the_bands_name_check_module.py        # Band name "The" prefix
├── disable_a_selection_buttons_module.py # Disable A window buttons
├── disable_a_selection_buttons_1.py      # Disable A window buttons (archived)
├── disable_b_selection_buttons_module.py # Disable B window buttons
├── disable_b_selection_buttons_1.py      # Disable B window buttons (archived)
├── disable_c_selection_buttons_module.py # Disable C window buttons
├── disable_c_selection_buttons_1.py      # Disable C window buttons (archived)
├── enable_all_buttons_module.py          # Re-enable all buttons
├── enable_all_buttons_1.py               # Re-enable all buttons (archived)
├── popup_45rpm_song_selection_code_module.py # 45RPM song selection popup (v0.42+)
├── popup_45rpm_now_playing_code_module.py # 45RPM now-playing popup (v0.40+)
│
├── Media Assets:
├── fonts/                                # Custom fonts
│   └── OpenSans-ExtraBold.ttf
├── record_labels/                        # 200+ record label images
│   ├── final_black/                      # Black background variants
│   ├── final_black_bg/
│   ├── final_black_sel/
│   ├── final_white/                      # White background variants
│   ├── final_white_bg/
│   └── final_white_sel/
├── images/                               # Centralized image assets (v0.43+)
│   ├── jukebox_2025_logo.png             # Application logo
│   ├── magglass.png                      # Magnifying glass icon
│   └── [other image files]
├── selection_45.gif                      # Selection animation
├── selection_45.jpg                      # Selection animation
├── success.mp3                           # Selection confirmation sound
│
├── depreciated_code/                     # Archived modules (v0.43+)
│   ├── 0.0-0.39/                         # Old version files
│   ├── thread_functions.py
│   ├── main_jukebox_GUI.py
│   ├── background_image_data.py
│   └── [other deprecated modules]
│
├── Configuration:
├── CurrentSongPlaying.txt                # Currently playing track info
├── log.txt                               # Application log file
├── .gitignore                            # Git ignore patterns
└── README.md                             # This file
```

### Modular Functions

Each function module is independent and self-contained:

| Module | Purpose |
|--------|---------|
| `info_screen_layout_module.py` | Creates info display screen layout |
| `jukebox_selection_screen_layout_module.py` | Creates song selection grid layout |
| `control_button_screen_layout_module.py` | Creates control button layout |
| `search_window_button_layout_module.py` | Creates search window buttons |
| `font_size_window_updates_module.py` | Calculates and applies font sizes |
| `font_size_window_updates_1.py` | Extended font sizing functionality |
| `upcoming_selections_update_module.py` | Updates upcoming songs queue |
| `the_bands_name_check_module.py` | Auto-adds "The" to band names |
| `disable_a_selection_buttons_module.py` | Disables A window buttons |
| `disable_b_selection_buttons_module.py` | Disables B window buttons |
| `disable_c_selection_buttons_module.py` | Disables C window buttons |
| `enable_all_buttons_module.py` | Enables all 21 song buttons |
| `popup_45rpm_song_selection_code_module.py` | Generates & displays 45RPM song selection record popup |
| `popup_45rpm_now_playing_code_module.py` | Generates & displays 45RPM now-playing record popup |

## 45RPM Song Selection Popup Feature (v0.42+)

The 45RPM song selection popup display has been extracted into its own module for modularity and reusability.

### `popup_45rpm_song_selection_code_module.py` Module

**Function:** `display_45rpm_popup(MusicMasterSongList, counter, jukebox_selection_window)`

**Parameters:**
- `MusicMasterSongList` (list): Song database with title and artist info
- `counter` (int): Index of currently selected song
- `jukebox_selection_window`: PySimpleGUI window object

**Functionality:**
1. Extracts song title and artist from song list
2. Loads random 45RPM record label image from `record_labels/final_black_sel/`
3. Generates text overlay with:
   - Dynamic font sizing (15-30pt based on text length)
   - Text wrapping for long titles/artists
   - Centered positioning on record label
4. Saves generated image as `selection_45.jpg` and `selection_45.gif`
5. Plays success sound via VLC
6. Displays animated 600-frame popup showing record label
7. Maintains UI state (hides/unhides main window)

### Example Usage

```python
from popup_45rpm_song_selection_code_module import display_45rpm_popup

# When song is selected:
display_45rpm_popup(MusicMasterSongList, selected_index, jukebox_selection_window)
```

## 45RPM Now-Playing Popup Feature (v0.40+)

The now-playing 45RPM popup display has been extracted into its own module for modularity and reusability.

### `popup_45rpm_now_playing_code.py` Module

**Function:** `display_45rpm_now_playing_popup(MusicMasterSongList, counter, jukebox_selection_window, upcoming_selections_update)`

**Parameters:**
- `MusicMasterSongList` (list): Song database with title and artist info
- `counter` (int): Index of currently playing song
- `jukebox_selection_window`: PySimpleGUI window object
- `upcoming_selections_update` (function): Callback to update upcoming songs display

**Functionality:**
1. Extracts currently playing song title and artist from song list
2. Loads random 45RPM record label image from `record_labels/final_black_bg/`
3. Generates text overlay with dynamic font sizing (15-30pt based on text length)
4. Saves generated image as `selection_45.jpg` and `selection_45.gif`
5. Displays animated 600-frame popup showing record label
6. Triggers on song change in the background playback thread
7. Calls `upcoming_selections_update()` to refresh queue display
8. Maintains UI state (hides/unhides main window)

### Key Differences from Selection Popup

| Feature | Selection Popup | Now-Playing Popup |
|---------|-----------------|-------------------|
| **Trigger** | Song selected by user | Currently playing song changes |
| **Record Label** | `final_black_sel/` | `final_black_bg/` |
| **Audio** | Plays success.mp3 | No audio (song already playing) |
| **Event** | Immediate response | Background thread update |

### Example Usage

```python
from popup_45rpm_now_playing_code import display_45rpm_now_playing_popup

# When currently playing song changes:
display_45rpm_now_playing_popup(MusicMasterSongList, current_index, jukebox_selection_window, upcoming_selections_update)
```

## Requirements

### Python 3.7+

### Dependencies

```
FreeSimpleGUI>=4.60.1
python-vlc>=3.0.0
Pillow>=8.0.0
```

### System Requirements

- Windows or Linux
- Python 3.7 or higher
- VLC libraries installed (for audio playback)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bradfortner/convergence-jukebox-2026.git
cd convergence-jukebox-2026/convergence_jukebox_2026_gui_renewal
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install FreeSimpleGUI
pip install python-vlc
pip install Pillow
```

### 4. Install VLC Libraries

**Windows:**
```bash
pip install python-vlc
# Also install VLC from: https://www.videolan.org/vlc/
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install vlc
pip install python-vlc
```

## Usage

### Running the Application

```bash
python "0.48 - main_jukebox_GUI_2026.py"
```

### Application Flow

1. **Main Window Opens**
   - Displays Convergence Jukebox 2026 logo
   - Shows background image
   - Ready for user interaction

2. **Song Selection**
   - User selects from 3 song selection windows (A, B, C)
   - Each window displays 21 songs
   - Scroll using arrow buttons to navigate
   - Font size automatically adjusts based on song name length

3. **Selection Confirmation**
   - Select grid position (A1-C7) using control buttons
   - Triggers 45RPM popup display
   - Success sound plays
   - Animated record label shown for ~10 seconds
   - Song queued for playback
   - Upcoming songs display updated

4. **Playback**
   - VLC plays selected song
   - Playback controls available in main window
   - Queue system for multiple song selection
   - Real-time display of currently playing track

## Configuration

### Music Directories

The application looks for music in these directories (excluded from git):
- `music/` - Main music collection

### Band Name Configuration

Two configuration files control band name display:
- `the_bands.txt` - List of bands that should have "The" prefix
- `the_exempted_bands.txt` - Bands exempt from "The" prefix

### 45RPM Popup Configuration

The popup display duration is controlled in `45rpm_pop_up_code.py`:
```python
for i in range(600):  # 600 frames at ~60ms per frame ≈ 36 seconds
    sg.PopupAnimated('selection_45.gif', ...)
```

Adjust the range value to control how long the popup displays.

## Technical Details

### FreeSimpleGUI Migration

This project was migrated from deprecated PySimpleGUI to FreeSimpleGUI:

- **FreeSimpleGUI** is a community-maintained drop-in replacement
- 100% compatible API with PySimpleGUI
- Active development and maintenance
- Better long-term support

### Design Patterns

**Parameter-Based Architecture**
- Functions receive all needed data as parameters
- No closure dependencies or global state
- Easy to test and understand
- Reduces coupling between modules

**Modular Layout**
- Separate GUI layout definitions
- Easy to modify UI without touching logic
- Reusable layout components

**Background Threading**
- Non-blocking UI updates
- Real-time song information display
- Smooth user experience

**Continuous Refactoring**
- Regular extraction of functionality to modules
- Improves code organization
- Reduces main file size and complexity

### Image Handling

**Background Image**
- 623KB base64-encoded PNG
- Stored in separate `background_image_data.py` module
- Lazy-loaded via `get_background_image()` function
- Allows transparent window overlays

**Record Labels**
- 200+ unique label images
- Three variants per label:
  - Normal display
  - Background (for buttons)
  - Selected state
- Two color schemes: Black & White
- Dynamically selected from `record_labels/final_black_sel/` during playback

### Text Rendering

The `popup_45rpm_code.py` module implements intelligent text rendering:
- **Long Text Handling**: Wraps titles/artists > 37/30 characters using 15pt font
- **Medium Text**: 17-37 character titles use 20pt font
- **Short Text**: ≤17 character titles use 30pt font
- **Text Positioning**: Center-anchored text at fixed Y coordinates
- **Font**: OpenSans-ExtraBold for consistent, bold appearance

## Development

### Code Style

- Clear, descriptive function names
- Comprehensive docstrings
- Inline comments for complex logic
- Type hints where beneficial

### Adding New Features

1. Create new module file in project root
2. Define function with clear parameters
3. Import in main file
4. Call from event loop or other functions
5. Commit with descriptive message

### Recent Refactoring (v0.42)

**Renamed Selection Popup Module for Clarity**
- `popup_45rpm_selection_code.py` renamed to `popup_45rpm_song_selection_code.py`
- Updated import in main file to reference new module name
- Improved naming clarity: distinguishes "song selection" from general "selection"
- Maintains 100% backward compatibility

### Previous Refactoring (v0.41)

**Renamed Selection Popup Module**
- `popup_45rpm_code.py` renamed to `popup_45rpm_selection_code.py`
- Updated import in main file to reference new module name
- Improved clarity by distinguishing selection popup from now-playing popup
- Maintains 100% backward compatibility

### Earlier Refactoring (v0.40)

**Extracted Now-Playing 45RPM Popup Code**
- Lines 1094-1169 from v0.39 moved to `popup_45rpm_now_playing_code.py`
- Created `display_45rpm_now_playing_popup()` function
- Improved code organization and reusability
- Maintains 100% backward compatibility

### Earlier Refactoring (v0.39)

**Extracted Selection 45RPM Popup Code**
- Lines 1050-1111 from v0.38 moved to `popup_45rpm_code.py`
- Created `display_45rpm_popup()` function
- Improved code organization and reusability
- Maintains 100% backward compatibility

### Testing

All modules include:
- Input validation
- Error handling
- Return value documentation

## Troubleshooting

### FreeSimpleGUI Not Found

```bash
pip install --upgrade FreeSimpleGUI
```

### VLC Playback Not Working

1. Ensure VLC is installed on your system
2. Verify `python-vlc` module: `pip list | grep vlc`
3. Restart Python interpreter after installing VLC

### Song Files Not Found

1. Ensure music directories exist in project root
2. Check file permissions
3. Verify file formats are supported by VLC

### GUI Not Displaying

1. Check FreeSimpleGUI installation
2. Ensure X11 forwarding (if using SSH)
3. Verify screen resolution supports window size

### 45RPM Song Selection Popup Not Showing

1. Verify `record_labels/final_black_sel/` directory exists and contains images
2. Check `success.mp3` file exists
3. Ensure `popup_45rpm_song_selection_code.py` is in project root
4. Verify Pillow is installed: `pip install --upgrade Pillow`

### 45RPM Now-Playing Popup Not Showing

1. Verify `record_labels/final_black_bg/` directory exists and contains images
2. Ensure `popup_45rpm_now_playing_code.py` is in project root
3. Check song is actually playing (verify CurrentSongPlaying.txt updates)
4. Verify Pillow is installed: `pip install --upgrade Pillow`

## Git Workflow

### Version History

- **0.48** - Suppressed VLC plugin cache error messages using OS-level file descriptor redirection (current)
- **0.47** - Fixed song selection freeze when adding credits by moving file I/O to background thread
- **0.46** - Bug discovery version (freezing issue identified)
- **0.45** - Previous stable version
- **0.43** - Codebase reorganization with `depreciated_code/` folder for archived versions; image files moved to `images/` directory
- **0.42** - Renamed selection popup module to popup_45rpm_song_selection_code.py
- **0.41** - Renamed selection popup module to popup_45rpm_selection_code.py
- **0.40** - Now-playing 45RPM popup code extracted to module
- **0.39** - Selection 45RPM popup code extracted to module
- **0.38** - Compacted search_window_button_layout extracted
- **0.35-0.37** - Layout module extraction improvements
- **0.2** - Production FreeSimpleGUI migration
- **0.191** - Background image extracted to module
- **0.0-0.39** - Original development versions (archived in `depreciated_code/`)
- Earlier versions tracked in git history

### Deprecated Code Archive (v0.43+)

Starting with version 0.43, older versions and unused modules have been archived in the `depreciated_code/` folder:

**Contents:**
- Versions 0.0-0.39 - Earlier development versions
- Unused modules:
  - `thread_functions.py` - Duplicated in main file
  - `main_jukebox_GUI.py` - Older GUI implementation
  - `background_image_data.py` - Large data module
  - `gui_layouts.py` - Replaced by modular layout files
  - `selection_*.py` modules - Replaced by newer versions

**Why archived?** To keep the main directory clean and focused on current production code while preserving history in case it's needed for reference.

### Excluded Directories

The following are excluded from version control (.gitignore):
- `music/` - Large music files
- `smusicshort/` - Short clips
- `smusiclong/` - Long clips
- Python cache (`__pycache__/`)
- IDE files (`.vscode/`, `.idea/`)

### Commit Message Format

Commits follow this format:
```
Create version X.XX with [feature description]

[Detailed description of changes]

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Performance Notes

- **File Size:** Main file refactored to improve modularity
- **Memory:** Minimal footprint with modular architecture
- **CPU:** Background thread uses ~1% CPU for updates
- **Storage:** Total project ~500MB (including media assets)
- **Popup Display:** Smooth 600-frame animation at 60ms intervals

## Known Issues

None currently. Please report issues on GitHub.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes with descriptive messages
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

[Specify your license here - e.g., MIT, GPL, etc.]

## Contact

For questions or issues, please open a GitHub issue or contact the maintainers.

## Acknowledgments

- FreeSimpleGUI community for maintaining the PySimpleGUI replacement
- VLC for the powerful media player backend
- OpenSans font by Google Fonts
- Pillow library for image manipulation

## Version Information

- **Current Version:** 0.48
- **GUI Framework:** FreeSimpleGUI 4.60+
- **Media Backend:** VLC (python-vlc 3.0+)
- **Image Support:** Pillow 8.0+
- **Python:** 3.7+
- **Last Updated:** 2025-10-28

## Recent Bug Fixes (v0.47-0.48)

### v0.48 - VLC Error Message Suppression
**Issue:** VLC was printing hundreds of error messages about stale plugins cache when the screen advance arrow hit the end of available songs, slowing down I/O performance.
**Solution:** Implemented OS-level file descriptor redirection using `os.dup()` and `os.dup2()` to suppress C-level library output during VLC MediaPlayer instantiation.

### v0.47 - Song Selection Freeze Fix
**Issue:** Selecting a song after adding credits caused the GUI to freeze completely.
**Root Cause:** Blocking file I/O operations (reading/writing PaidMusicPlayList.txt and logging) were executing synchronously in the main event loop.
**Solution:** Moved all file I/O operations to a background worker thread using Python's `Queue` module for thread-safe communication.

---

**Convergence Jukebox 2026 - GUI Renewal**
A modular, maintainable approach to jukebox software with continuous refactoring for improved code organization.
