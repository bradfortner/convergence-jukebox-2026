# Convergence Jukebox 2026 - GUI Renewal

A modern, modular implementation of the Convergence Jukebox 2026 graphical user interface using **FreeSimpleGUI** (drop-in replacement for deprecated PySimpleGUI).

## Overview

The Convergence Jukebox 2026 is a comprehensive jukebox application that displays and plays music with an interactive GUI. This GUI renewal project implements a clean, modular architecture that separates concerns and improves maintainability.

**Current Version:** 0.2 - main_jukebox_GUI_2026.py

## Features

✅ **Full FreeSimpleGUI Integration**
- Modern, responsive GUI built with FreeSimpleGUI
- Cross-platform support (Windows & Linux)
- Custom title bar and transparent windows
- Background image support (embedded as base64)

✅ **Modular Architecture**
- 10 separate, independent function modules
- Clean separation of concerns
- Easy to test and maintain
- Parameter-based function design (no closure dependencies)

✅ **Rich Media Support**
- 200+ record label images with variants
- Selection animations and UI icons
- Embedded background image (623KB)
- Custom fonts (OpenSans-ExtraBold)

✅ **Advanced Features**
- Song selection system (A1-C7 grid)
- Band name auto-detection with exemptions
- Dynamic font sizing based on text length
- Upcoming songs queue display
- VLC media player integration for audio playback
- Background thread for real-time UI updates

## Architecture

### File Structure

```
convergence_jukebox_2026_gui_renewal/
├── 0.2 - main_jukebox_GUI_2026.py      # Production main file
├── background_image_data.py             # Background image module (623KB)
├── gui_layouts.py                       # GUI layout definitions
├── thread_functions.py                  # Background thread functions
│
├── Modular Function Files:
├── disable_a_selection_buttons.py       # Disable A window buttons
├── disable_b_selection_buttons.py       # Disable B window buttons
├── disable_c_selection_buttons.py       # Disable C window buttons
├── disable_numbered_selection_buttons.py
├── enable_numbered_selection_buttons.py
├── enable_all_buttons.py                # Re-enable all buttons
├── selection_buttons_update.py          # Update song buttons display
├── selection_entry_complete.py          # Process song selection
├── the_bands_name_check.py             # Add "The" to band names
├── upcoming_selections_update.py        # Update queue display
│
├── Media Assets:
├── fonts/                               # Custom fonts
│   └── OpenSans-ExtraBold.ttf
├── record_labels/                       # 200+ record label images
│   ├── final_black/                     # Black background variants
│   ├── final_black_bg/
│   ├── final_black_sel/
│   ├── final_white/                     # White background variants
│   ├── final_white_bg/
│   └── final_white_sel/
├── jukebox_2025_logo.png                # Application logo
├── magglass.png                         # Magnifying glass icon
├── selection_45.gif                     # Selection animation
├── selection_45.jpg
│
├── Configuration:
├── .gitignore                           # Git ignore patterns
└── README.md                            # This file
```

### Modular Functions

Each function module is independent and self-contained:

| Module | Purpose |
|--------|---------|
| `disable_a_selection_buttons.py` | Disables A window song buttons and controls |
| `disable_b_selection_buttons.py` | Disables B window song buttons and controls |
| `disable_c_selection_buttons.py` | Disables C window song buttons and controls |
| `disable_numbered_selection_buttons.py` | Disables numbered control buttons (1-7) |
| `enable_numbered_selection_buttons.py` | Enables numbered control buttons |
| `enable_all_buttons.py` | Re-enables all 21 song buttons and controls |
| `selection_buttons_update.py` | Updates display with current song selection |
| `selection_entry_complete.py` | Processes A1-C7 song selection entry |
| `the_bands_name_check.py` | Adds "The" prefix to band names |
| `upcoming_selections_update.py` | Updates upcoming songs queue display |

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
python "0.2 - main_jukebox_GUI_2026.py"
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
   - Selected song is disabled, next song queued
   - Upcoming songs display updated

4. **Playback**
   - VLC plays selected song
   - Playback controls available in main window
   - Queue system for multiple song selection

## Configuration

### Music Directories

The application looks for music in these directories (excluded from git):
- `music/` - Main music collection
- `musicshort/` - Short clip versions
- `smusicshort/` - Short music clips
- `smusiclong/` - Long music clips

### Band Name Configuration

Two configuration files control band name display:
- `the_bands.txt` - List of bands that should have "The" prefix
- `the_exempted_bands.txt` - Bands exempt from "The" prefix

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

## Git Workflow

### Version History

- **0.2** - Production FreeSimpleGUI migration (current)
- **0.191** - Background image extracted to module
- **0.19** - Initial FreeSimpleGUI migration
- Earlier versions tracked in git history

### Excluded Directories

The following are excluded from version control (.gitignore):
- `music/` - Large music files
- `smusicshort/` - Short clips
- `smusiclong/` - Long clips
- Python cache (`__pycache__/`)
- IDE files (`.vscode/`, `.idea/`)

## Performance Notes

- **File Size:** Main file ~270KB (reduced from 609KB)
- **Memory:** Minimal footprint with modular architecture
- **CPU:** Background thread uses ~1% CPU for updates
- **Storage:** Total project ~500MB (including media assets)

## Known Issues

None currently. Please report issues on GitHub.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
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

## Version Information

- **GUI Framework:** FreeSimpleGUI 4.60+
- **Media Backend:** VLC (python-vlc 3.0+)
- **Image Support:** Pillow 8.0+
- **Python:** 3.7+
- **Updated:** 2025-10-25

---

**Convergence Jukebox 2026 - GUI Renewal**
A modular, maintainable approach to jukebox software.
