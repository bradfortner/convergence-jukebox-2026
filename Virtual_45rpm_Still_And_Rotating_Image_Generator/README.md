# Virtual 45rpm Still And Rotating Image Generator

Generate custom vinyl record label images with randomly selected templates and automatically adjusted typography, then view them with an animated rotating record visualization.

## Overview

This project creates beautiful vinyl record label images by overlaying artist and song titles onto randomly selected blank record templates, and displays them with an animated rotating record visualization. Perfect for creating retro vinyl record-themed designs with authentic record label aesthetics that can be viewed in motion.

## Features

- **Random Label Selection**: Automatically selects a random blank record label template from the available collection
- **Intelligent Font Color Detection**: Automatically applies white text for dark labels (prefix `w_`) and black text for light labels
- **Dynamic Typography**: Auto-fits text to available space by adjusting font sizes intelligently
- **Text Wrapping**: Breaks long titles into multiple lines while maintaining readability
- **Centered Layout**: All text is horizontally centered on the record label
- **Animated Visualization**: Displays rotating record animation after generation at 45 fps
- **High Quality Output**: Saves optimized PNG with antialiased fonts

## Requirements

- Python 3.7+
- PIL/Pillow
- pygame
- Font: OpenSans ExtraBold (included in `fonts/` directory)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install pillow pygame
   ```

## Usage

1. Prepare your data:
   - Create a pickle file named `artist_song.pkl` containing a list of `[artist, song]` tuples
   - Place it in the project root directory

2. Run the generator:
   ```bash
   python "1.6 - record_artist_titles_generator.py"
   ```

3. The script will:
   - Randomly select one record from your data
   - Randomly choose a label template from `record_labels/blank_record_labels/`
   - Determine font color based on label filename
   - Generate `final_record_pressing.png`
   - Display an animated rotating vinyl record visualization

## File Structure

```
Virtual_45rpm_Still_And_Rotating_Image_Generator/
├── 1.6 - record_artist_titles_generator.py  # Main generator script (ACTIVE)
├── rotate_record_module.py                   # Animation module
├── record_labels/
│   └── blank_record_labels/                  # Record label templates
│       ├── atco_records_bg.png
│       ├── barry_records_bg.png
│       ├── w_decca_records_bg.png           # (w_ prefix = white text)
│       └── ... (40+ templates)
├── fonts/
│   └── OpenSans-ExtraBold.ttf                # Font file
├── depreciated_code/                         # Previous versions
│   ├── 1.4 - record_artist_titles_generator.py
│   └── 1.5 - record_artist_titles_generator.py
├── artist_song.pkl                           # Input data (required)
├── final_record_pressing.png                 # Output file
└── README.md                                 # This file
```

## Configuration

Edit these settings in `1.6 - record_artist_titles_generator.py` to customize:

```python
font_path = "fonts/OpenSans-ExtraBold.ttf"   # Font file path
max_text_width = 300                          # Max text width (pixels)
song_y = (height // 2) + 90                   # Song title vertical position
artist_y = (height // 2) + 125                # Artist name vertical position
song_line_height = 25                         # Line spacing for song
artist_line_height = 30                       # Line spacing for artist
```

## Font Color Logic

The generator automatically selects text color based on the selected label filename:

- **White Text**: Labels starting with `w_` (e.g., `w_decca_records_bg.png`)
- **Black Text**: All other labels

This ensures optimal contrast between text and background.

## Animation Details

After generating the record label, an animated visualization is displayed:

- **Frame Rate**: 45 fps
- **Rotation Speed**: 360° per second (8° per frame)
- **Background**: Dark grey (RGB: 64, 64, 64)
- **Close the window** to stop the animation and end the script

## Output

**Filename**: `final_record_pressing.png` (overwrites previous output)

The generated image shows:
- Randomly selected record label design
- Song title (centered, up to 2 lines)
- Artist name (centered, up to 2 lines)
- Appropriate font color (white or black based on label)

## Available Labels

The project includes 40+ authentic record label designs including:

- ATCO Records
- Barry Records
- Bearsville Records
- Blue Note Records
- Chateau Records
- Coral Records
- Del-Fi Records
- Deram Records
- End Records
- Fantasy Records
- Jive Records
- Kent Records
- Roulette Records
- And many more...

Labels with `w_` prefix include:
- Decca
- Eight-Ball
- Federal
- King
- Police
- RPM
- Vee-Jay
- Vivid

## Version History

- **1.6** (Current): Random label selection with automatic font color detection
- **1.5**: Manual label selection (deprecated)
- **1.4**: Initial version (deprecated)

See `depreciated_code/` folder for previous versions.

## How It Works

1. Load artist/song data from pickle file
2. Randomly select one record from the dataset
3. List all available .png files from blank_record_labels directory
4. Randomly select one label template
5. Determine font color based on filename prefix:
   - `w_*.png` → white font
   - Others → black font
6. Auto-fit text to available space:
   - Start with 28pt font
   - Reduce size incrementally until text fits
   - Minimum size: 16pt
   - Support up to 2 lines per text block
7. Draw centered text on label image
8. Save output as `final_record_pressing.png`
9. Display rotating record animation at 45 fps

## Example Data Format

Your `artist_song.pkl` should contain a list like:

```python
[
    ["The Beatles", "Let It Be"],
    ["Aretha Franklin", "Respect"],
    ["David Bowie", "Changes"],
    # ... more records
]
```

Create it with:

```python
import pickle
data = [["Artist Name", "Song Title"], ...]
with open('artist_song.pkl', 'wb') as f:
    pickle.dump(data, f)
```

## Troubleshooting

**No .png files found error**: Ensure `record_labels/blank_record_labels/` directory exists and contains .png files

**Font not found error**: Verify `fonts/OpenSans-ExtraBold.ttf` exists in the fonts directory

**Text rendering issues**: Check that font size is not below 16pt; increase `start_size` parameter if needed

**Animation window won't close**: Press `Ctrl+C` in terminal or close the window directly

## Future Enhancements

- Support for additional fonts
- Configurable text positioning
- Multiple record layouts
- Batch processing for multiple records
- Custom background colors
- Text shadow/outline effects

## License

Part of the Convergence Jukebox 2026 project.

## Contact

For questions or suggestions, visit the project repository.
