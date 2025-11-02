# Convergence Jukebox 2026

A sophisticated, modular Python-based jukebox application with animated vinyl record visuals, real-time playlist management, and a modern cross-platform GUI. The system combines three specialized components: a music playback engine, a FreeSimpleGUI interface, and a vinyl record animation module.

## 🎵 Project Overview

The Convergence Jukebox 2026 is a complete jukebox solution designed for entertainment venues, events, and personal use. It features a polished user interface with animated 45 RPM vinyl record displays, dual playlist management (standard rotation + paid requests), and comprehensive song statistics tracking.

### Key Features

- **Modern GUI**: FreeSimpleGUI-based interface with 21 selectable songs (A1-C7 grid)
- **Animated Record Display**: Transforms vinyl record photographs into spinning 45 RPM animations
- **Dual Playlist System**: Manages both random rotation and paid song requests
- **Real-time Statistics**: Tracks play counts, listening history, and song preferences
- **Cross-Platform**: Works on Windows, macOS, and Linux with VLC integration
- **Modular Architecture**: 15+ independent function modules for easy maintenance and extension
- **Professional Audio**: VLC-based playback with seamless song transitions

---

## 📁 Project Structure

```
convergence-jukebox-2026/
├── convergence_jukebox_2026_gui_renewal/       (Current GUI - v0.62)
├── convergence_jukebox_2026_player_renewal/    (Current Engine - v0.9)
├── 45_RPM_Spinning_Record_Animation/           (Record animation module)
├── convergence-jukebox-pygame/                 (Alternative pygame implementation)
├── main_jukebox_engine/                        (Legacy reference)
├── pysimple_gui_abandoned/                     (Deprecated PySimpleGUI version)
└── README.md                                   (This file)
```

---

## 🚀 Active Components

### 1. **convergence_jukebox_2026_gui_renewal** (Current: v0.62)

The modern, modular graphical user interface built with FreeSimpleGUI.

#### What's New

- **v0.62**: Fixed PopupAnimated ZeroDivisionError - replaced with static image display using sg.Image() with adjustable duration
- **v0.61**: Improved module naming for better code organization (band name check and upcoming selections modules renamed)
- **v0.48-0.60**: Fixed UI freeze issues by moving file I/O operations to background threads
- **v0.47**: Enhanced responsiveness with asynchronous file handling
- **v0.40+**: Complete modularization - functions split into 15+ independent modules

#### Architecture

The GUI is now fully modular with 15+ independent function files, each handling a specific aspect:

- `info_screen_layout_module.py` - Information display screen
- `jukebox_selection_screen_layout_module.py` - 21-song selection grid (A1-C7)
- `control_button_screen_layout_module.py` - Playback controls
- `search_window_button_layout_module.py` - Search functionality
- `popup_45rpm_song_selection_code_module.py` - Animated record selection popup
- `popup_45rpm_now_playing_code_module.py` - Animated record now-playing display
- `upcoming_selections_update_module.py` - Queue/upcoming songs display
- `the_bands_name_check_module.py` - Intelligent "The" prefix handling
- `font_size_window_updates_module.py` - Dynamic font sizing
- `disable_a/b/c_selection_buttons_module.py` - Button state management
- `enable_all_buttons_module.py` - Reset button states
- And more...

#### Features

- **A/B/C Selection Windows**: Three 7-song windows for intuitive browsing
- **Animated Popups**: Spinning vinyl records when songs are selected or now-playing
- **Real-time Queue Display**: Shows upcoming song selections
- **Smart Band Names**: Automatically handles "The" prefix (e.g., "The Beatles" vs "Beatles, The")
- **Dynamic Typography**: Font sizes adjust based on display length and window size
- **Background Threading**: Non-blocking UI with responsive feedback
- **VLC Integration**: Seamless audio playback control

#### Media Assets

- **Record Labels**: 200+ vinyl record label images (3 color schemes: black, white variants)
- **Fonts**: Custom OpenSans-ExtraBold for professional appearance
- **Icons**: Jukebox logo, search magnifying glass, selection indicators
- **Audio**: Short clips for UI feedback and full songs for playback

#### Configuration

- `jukebox_config.json` - Application settings
- `the_bands.txt` - List of bands requiring "The" prefix
- `the_exempted_bands.txt` - Bands that don't use "The" prefix
- `MusicMasterSongList.txt` - Database of all songs with metadata
- `CurrentSongPlaying.txt` - Real-time now-playing information

#### Dependencies

```
FreeSimpleGUI >= 4.60.1
python-vlc >= 3.0.0
Pillow >= 8.0.0
```

#### Getting Started

1. Ensure Python 3.7+ is installed
2. Install dependencies: `pip install -r convergence_jukebox_2026_gui_renewal/requirements.txt`
3. Place your music files in the `music/` directory
4. Run the GUI: `python "convergence_jukebox_2026_gui_renewal/0.62 - main_jukebox_GUI_2026.py"`

---

### 2. **convergence_jukebox_2026_player_renewal** (Current: v0.9 - STABLE HYBRID)

The sophisticated music playback engine with playlist management and statistics tracking.

#### What's New

- **v0.9**: Production-ready hybrid combining stability (v0.8) with advanced features (v0.91)
- **v0.8**: Introduced logging system, console colors, and JSON configuration
- **v0.7**: Full type hints for better code clarity and IDE support
- **v0.6**: Cross-platform path handling for Windows/macOS/Linux compatibility
- **v0.5+**: Progressive improvements in architecture, error handling, and code quality

#### Architecture

Single, well-designed `JukeboxEngine` class with:

- **No Global State**: All functionality encapsulated in the class
- **Type Hints**: Full Python type annotations throughout
- **OOP Design**: Clean object-oriented architecture
- **Synchronous Polling**: Efficient real-time monitoring without threads
- **Error Handling**: Comprehensive input validation and exception handling
- **Modular I/O**: Extracted file operations for easier testing

#### Features

- **Dual Playlist System**: Manages both random song rotation and paid requests simultaneously
- **Real-time Monitoring**: Continuously polls for new paid requests
- **Song Statistics**: Tracks play counts, listening history, and user preferences
- **VLC Integration**: Cross-platform audio playback
- **JSON Configuration**: Flexible configuration through JSON files
- **Logging System**: Comprehensive application logging with console colors
- **Metadata Extraction**: Reads ID3 tags and other metadata
- **Smart Queuing**: Prioritizes paid requests while maintaining rotation fairness

#### Configuration

The engine is configured via `jukebox_config.json`:

```json
{
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s"
  },
  "console": {
    "headers": true,
    "colors": true,
    "display_format": "detailed"
  },
  "paths": {
    "music_directory": "music/",
    "log_file": "log.txt",
    "statistics_file": "song_statistics.json"
  }
}
```

#### Data Files

- `MusicMasterSongList.txt` - JSON array of all songs (auto-generated)
- `GenreFlagsList.txt` - Genre tags for categorization
- `PaidMusicPlayList.txt` - JSON array of paid song request indices
- `CurrentSongPlaying.txt` - Real-time now-playing track information
- `song_statistics.json` - Complete play history and statistics
- `log.txt` - Application event log with timestamps

#### Dependencies

```
python-vlc >= 3.0.0
tinytag (for metadata)
```

#### Getting Started

1. Install dependencies: `pip install -r convergence_jukebox_2026_player_renewal/requirements.txt`
2. Place your music files in the `music/` directory
3. Run the engine: `python convergence_jukebox_2026_player_renewal/main_jukebox_engine_2026.py`

---

### 3. **45_RPM_Spinning_Record_Animation** (Current: v0.0)

A sophisticated image processing module that transforms vinyl record photographs into animated 45 RPM records.

#### What's New

- **v0.0**: Complete master pipeline with multi-method detection and professional quality output
- Enhanced circle detection using Hough Circle Detection
- Fallback detection methods for robust center hole identification
- Color detection via 360-point ring sampling
- OpenCV floodFill for seamless hole filling
- Alpha blending for professional compositing
- Pygame animation engine (15 FPS spinning animation)

#### Features

- **Vinyl Photo Input**: Accepts real vinyl record photographs
- **Automatic Circle Detection**: Uses Hough Circle Detection to identify record boundaries
- **Center Hole Detection**: Multi-method detection with intelligent fallback options
- **Color Analysis**: Samples 360 points around the record to detect vinyl color
- **Label Extraction**: Isolates and extracts the record label with transparency
- **Professional Compositing**: Overlays label on RIAA-compliant template
- **Animated Playback**: Smooth Pygame animation at 15 FPS
- **RIAA Compliance**: Maintains proper 45 RPM record proportions (540x540px)

#### Pipeline Stages

1. **Input**: Vinyl record photograph (JPG/PNG)
2. **Circle Detection**: Identifies record edge using Hough Transform
3. **Center Detection**: Finds center hole (3+ methods with fallback)
4. **Color Detection**: Analyzes vinyl color via ring sampling
5. **Label Extraction**: Isolates center label region
6. **Alpha Blending**: Creates transparency mask
7. **Compositing**: Overlays on professional template
8. **Animation**: Generates spinning animation sequence

#### Assets

- `45rpm_proportional_template.png` - RIAA 45 RPM record template (540x540px)
- `transparent_45rpm_record_label.png` - Extracted label with alpha channel
- `final_record_pressing.png` - Composite final record image
- Depreciated versions (v1.0-v5.1) in `depreciated_code/` folder for reference

#### Integration

Used by the GUI module for:
- Song selection popup displays
- Now-playing animated record display
- Real-time record visualization with rotation

Integration modules:
- `popup_45rpm_song_selection_code_module.py` (in GUI renewal)
- `popup_45rpm_now_playing_code_module.py` (in GUI renewal)

#### Dependencies

```
Pillow >= 9.0
opencv-python >= 4.5
numpy >= 1.20
scikit-image >= 0.19
pygame >= 2.0
```

#### Getting Started

1. Place a vinyl record photograph in the module directory
2. Install dependencies: `pip install -r 45_RPM_Spinning_Record_Animation/requirements.txt`
3. Run the master pipeline: `python "45_RPM_Spinning_Record_Animation/0.0 - 45rpm_record_animation_from_real_label.py"`

---

## 🔄 System Integration

The three components work together seamlessly:

```
┌─────────────────────────────────────────────────────────────┐
│                    Player Engine (v0.9)                     │
│  - Manages playlists and song rotation                      │
│  - Tracks statistics and play history                       │
│  - Integrates with VLC for audio playback                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Song metadata & now-playing info
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    GUI Interface (v0.62)                    │
│  - Displays song selection grid (A1-C7)                     │
│  - Shows real-time queue and statistics                     │
│  - Communicates user selections back to engine              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Song selection events
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Record Animation Module (v0.0)                      │
│  - Generates animated 45 RPM record displays                │
│  - Displays in popup windows for selections                 │
│  - Provides visual feedback for user interactions           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Active Components** | 3 major modules |
| **GUI Function Modules** | 15+ independent modules |
| **Record Label Images** | 200+ variants (3 color schemes) |
| **Current GUI Version** | 0.62 |
| **Current Player Version** | 0.9 (STABLE HYBRID) |
| **Record Animation Version** | 0.0 (Master Pipeline) |
| **Python Version** | 3.7+ required |
| **Total Project Size** | ~500MB (including media assets) |
| **Audio Backend** | VLC (python-vlc 3.0+) |
| **GUI Framework** | FreeSimpleGUI 4.60+ |

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.7 or higher
- VLC media player (system installation required)
- Git (for version control)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/convergence-jukebox-2026.git
   cd convergence-jukebox-2026
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r convergence_jukebox_2026_gui_renewal/requirements.txt
   pip install -r convergence_jukebox_2026_player_renewal/requirements.txt
   pip install -r 45_RPM_Spinning_Record_Animation/requirements.txt
   ```

3. **Prepare music files**
   - Place MP3 files in `convergence_jukebox_2026_gui_renewal/music/`
   - Organize by artist/album or use flat structure

4. **Run the application**
   ```bash
   # Start the GUI
   python "convergence_jukebox_2026_gui_renewal/0.62 - main_jukebox_GUI_2026.py"
   ```

---

## 📖 Documentation

Each component has detailed documentation:

- **[GUI Module README](convergence_jukebox_2026_gui_renewal/README.md)** - Comprehensive GUI documentation, modular architecture, and customization guide
- **[Player Engine README](convergence_jukebox_2026_player_renewal/README.md)** - Engine architecture, playlist management, and statistics tracking
- **[Record Animation README](45_RPM_Spinning_Record_Animation/README.md)** - Image processing pipeline, integration guide, and customization

---

## 🔧 Configuration

### GUI Configuration (`jukebox_config.json`)

Configure song selections, band names, and UI settings in:
- `convergence_jukebox_2026_gui_renewal/jukebox_config.json`

### Engine Configuration

Configure logging and paths in:
- `convergence_jukebox_2026_player_renewal/jukebox_config.json`

### Band Name Handling

Customize "The" prefix behavior:
- `the_bands.txt` - Bands that use "The" prefix
- `the_exempted_bands.txt` - Bands that don't use "The"

---

## 📝 Recent Changes & Development

### Version 0.62 (Current)
- Fixed PopupAnimated ZeroDivisionError by replacing with static image display
- Replaced sg.PopupAnimated() with sg.Image() element in popup window
- Added adjustable display duration (600ms default) with clear comments for customization

### Version 0.61
- Improved module naming conventions for better code organization
- Enhanced readability with descriptive module names
- Maintained backward compatibility with existing configurations

### Version 0.60
- Fixed UI responsiveness issues
- Improved background threading for file I/O
- Enhanced real-time updates

### Version 0.47-0.59
- Progressive improvements to modularity and responsiveness
- Bug fixes and performance optimizations
- UI refinements based on user feedback

### Previous Versions
- Complete version history available in depreciated_code folder
- Previous implementations (v0.0-v0.46) preserved for reference

---

## 🔄 Git Workflow

This project uses Git for version control. To contribute:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and commit: `git commit -m "Description of changes"`
3. Push to your branch: `git push origin feature/your-feature`
4. Create a pull request for review

---

## 📦 Legacy Components

The following folders contain legacy/reference implementations:

- **main_jukebox_engine/** - Original monolithic engine (reference only)
- **pysimple_gui_abandoned/** - Deprecated PySimpleGUI version (reference only)
- **convergence-jukebox-pygame/** - Alternative pygame-based implementation (reference)
- **45rpm_spinning_record/** - Predecessor to current animation module (reference)

These are preserved for reference and historical context but are not actively maintained.

---

## 🎯 Future Enhancements

Potential improvements for future versions:

- [ ] Mobile app interface
- [ ] Remote control via web dashboard
- [ ] Advanced analytics and reporting
- [ ] Support for additional audio formats
- [ ] Customizable themes and UI skins
- [ ] Multi-user queue management
- [ ] Integration with music streaming services
- [ ] Voice command support

---

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. Code follows existing style conventions
2. All functions include proper documentation
3. Changes are backward compatible
4. Version numbers are incremented appropriately
5. Documentation is updated to reflect changes

---

## 📄 License

This project is provided as-is. Please refer to any LICENSE file in the repository for specific licensing information.

---

## 📧 Contact & Support

For questions, bug reports, or feature requests:

1. Check the detailed README files in each component directory
2. Review the depreciated_code folders for implementation examples
3. Examine version history for previous solutions to similar issues

---

## 🎉 Acknowledgments

- **VLC/libvlc** - Cross-platform media playback
- **FreeSimpleGUI** - Modern Python GUI toolkit
- **Pillow** - Python imaging library
- **OpenCV** - Computer vision processing
- **PyGame** - Animation and game engine
- **NumPy & scikit-image** - Scientific computing

---

**Last Updated**: November 2, 2025
**Current Active Versions**: GUI v0.62 | Player v0.9 | Animation v0.0
**Status**: Production Ready ✅

---

## 🚀 Quick Links

- [GUI Module Documentation](convergence_jukebox_2026_gui_renewal/README.md)
- [Player Engine Documentation](convergence_jukebox_2026_player_renewal/README.md)
- [Record Animation Documentation](45_RPM_Spinning_Record_Animation/README.md)
- [Configuration Guide](#-configuration)
- [Installation Guide](#-installation--setup)
