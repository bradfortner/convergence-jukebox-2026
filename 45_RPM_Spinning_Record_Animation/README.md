# 45 RPM Spinning Record Animation

A complete pipeline for transforming a vinyl record photograph into an animated spinning 45 RPM record.

## ⚠️ IMPORTANT: Input Requirements

**This script REQUIRES a `record.jpg` file in the same directory to work.**

The master script (0.0) processes a photograph of a vinyl record and creates an animated spinning version. You must provide:
- **Filename**: `record.jpg`
- **Format**: JPG/JPEG image
- **Content**: A photograph of a vinyl record (preferably straight-on, clear view)
- **Location**: Same folder as the script

Without `record.jpg`, the script will not run successfully.

## Quick Start ⭐

**Prerequisites:**
1. Install dependencies: `pip install -r requirements.txt`
2. Place your vinyl record photo as `record.jpg` in this folder
3. Run the pipeline

**Execute:**
```bash
python "0.0 - 45rpm_record_animation_from_real_label.py"
```

The script will automatically:
1. Create a vinyl record template
2. Extract the record label from your photo
3. Fill the center hole
4. Composite everything together
5. Display an animated spinning record

## What You Get

The pipeline generates three output files:
- `45rpm_proportional_template.png` - The vinyl record template (540x540 pixels)
- `transparent_45rpm_record_label.png` - Extracted label with transparency
- `final_record_pressing.png` - Composite final vinyl record

Plus a live animation window showing the record spinning at 15 FPS.

## Pipeline Overview

**v0.0 - 45rpm_record_animation_from_real_label.py** is the master orchestrator that combines five processing stages:

1. **create_vinyl_45_template_module()**
   - Creates a proportionally correct 45 RPM vinyl record template
   - Output: 540x540 pixel template

2. **extract_record_label_module()**
   - Detects circles in your photo using Hough Circle Detection
   - Extracts the vinyl record label with transparent background
   - Handles center hole detection with multiple methods
   - Output: 282x282 pixel label with transparency

3. **fill_and_recut_center_hole_module()**
   - Detects the edge color by sampling around the hole
   - Uses OpenCV floodFill to fill the transparent center hole
   - Recuts a proper 117-pixel diameter transparent center hole (RIAA spec)
   - Trims vinyl record body to circular edge
   - Output: Complete vinyl record with proper dimensions

4. **final_record_pressing_module()**
   - Composites the extracted label onto the vinyl template
   - Preserves all transparency
   - Output: Final vinyl record image (540x540)

5. **display_record_playing_module()**
   - Opens a pygame window
   - Displays the vinyl record spinning at 15 FPS (360° per second)
   - Rotates continuously until you close the window

## Requirements

```
Pillow (PIL) >= 9.0      # Image processing
opencv-python >= 4.5     # Circle detection, floodfill
numpy >= 1.20            # Array operations
scikit-image >= 0.19     # Image I/O
pygame >= 2.0            # Animation display
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Python Usage

You can also use the pipeline programmatically:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from RecordAnimationPipeline import RecordAnimationPipeline

# Create pipeline with your input image
pipeline = RecordAnimationPipeline(input_image_path="record.jpg")

# Run the complete pipeline
pipeline.run_pipeline()
```

## Technical Specifications

### Vinyl Record Proportions (RIAA 45 RPM Spec)
- **Record Diameter**: 6.875 inches (540 pixels in output)
- **Label Diameter**: 3.6 inches (proportional)
- **Center Hole**: 1.5 inches → 117 pixels (proportional)
- **Groove End**: 4.25 inches (proportional)

### Output Formats
- **Image Format**: PNG with RGBA transparency
- **Final Size**: 540x540 pixels
- **Animation**: 15 FPS, 360° rotation per second
- **Background**: Transparent (compositable)
- **Center Hole**: Transparent

## How It Works

### Image Processing Pipeline

1. **Circle Detection** (Hough Circle Detection)
   - Converts input photo to grayscale
   - Applies Gaussian blur
   - Detects circles to find vinyl record in photo
   - Extracts largest circle (the record)

2. **Center Hole Detection** (Multi-method approach)
   - Tries contour-based circularity detection
   - Falls back to Hough Circle Detection
   - Falls back to dark spot detection
   - Creates transparent hole with proper alpha channel

3. **Color Detection** (Ring sampling)
   - Samples 360 points in a ring around the center hole
   - Collects all non-transparent pixels
   - Selects the brightest color
   - Uses this color to fill the transparent hole

4. **FloodFill** (OpenCV cv2.floodFill)
   - Seeds from center point
   - Fills the transparent hole with detected color
   - Ensures contiguous image in memory
   - Validates seed point within bounds

5. **Compositing** (Alpha blending)
   - Applies vinyl record body circular mask (540px diameter)
   - Creates transparent background outside record
   - Merges alpha channels properly
   - Produces final composite image

6. **Animation** (Pygame rotation)
   - Loads final composite image
   - Rotates incrementally (24° per frame at 15 FPS)
   - Displays in centered window
   - Runs until window is closed

## Troubleshooting

### "No circles detected!"
- Ensure `record.jpg` shows a clear vinyl record
- Try a photo with better lighting
- Make sure the record is relatively centered and in focus

### Circle detected but not your record
- The script found a different circular object
- Try taking a closer photo of just the record
- Ensure the record is the largest circular object

### Center hole not detected
- The script tries three detection methods automatically
- If none work, it falls back gracefully
- The script will still complete but may have imperfect hole detection

### Pygame window won't open
- Ensure you have a display/monitor connected
- Check that pygame is installed correctly
- Try running in a different environment

### Process takes a long time
- Processing time depends on image resolution
- High-res photos (4K+) take longer to process
- This is normal; wait for completion

## Directory Structure

```
45rpm_spinning_record/
├── 0.0 - 45rpm_record_animation_from_real_label.py  ⭐ MAIN SCRIPT
├── 1.0 - 45rpm_proportional_template.py              (Reference)
├── 2.0 - Extract_record_transparent.py               (Reference)
├── 3.0-3.5 - centre_hole_fill_and_recut.py          (Reference/Development)
├── 4.0 - Rotate_record.py                            (Reference)
├── depreciated_code/                                  (Processed versions)
├── .gitignore                                         (Ignore generated PNGs)
├── requirements.txt                                   (Dependencies)
└── README.md                                          (This file)
```

## Output Examples

When you run the master script with a vinyl record photo:

```
[ORCHESTRATOR] Step 1: Creating vinyl template...
[THREAD 1] Starting: create_vinyl_45_template_module()
[THREAD 1] Created: 45rpm_proportional_template.png
[THREAD 1] Completed: create_vinyl_45_template_module()

[ORCHESTRATOR] Step 2: Extracting record label...
[THREAD 2] Starting: extract_record_label_module()
[THREAD 2] Completed: extract_record_label_module()

[ORCHESTRATOR] Step 3: Filling and recuting center hole...
[THREAD 3] Starting: fill_and_recut_center_hole_module()
[THREAD 3] Completed: fill_and_recut_center_hole_module()

[ORCHESTRATOR] Step 4: Creating final record pressing...
[THREAD 4] Starting: final_record_pressing_module()
[THREAD 4] Completed: final_record_pressing_module()

[ORCHESTRATOR] Step 5: Starting record animation display...
[THREAD 5] Starting: display_record_playing_module()
Displaying rotating record animation (close window to stop)...
```

## Development History

This project evolved through multiple versions:

- **v0.0**: Master pipeline - unified orchestration ⭐ **USE THIS**
- **v1.0-v5.1**: Individual processing stages (archived in depreciated_code/)

The master script consolidates all stages into a single coherent workflow with proper threading and error handling.

## Tips for Best Results

1. **Photo Quality**: Take a clear, well-lit photo of your vinyl record
2. **Angle**: Shoot straight-on (not at an angle)
3. **Background**: Plain background works best
4. **Resolution**: Decent resolution (1000x1000 minimum) helps with detection
5. **Record Condition**: Visible record details help with label extraction

## License

Part of the Convergence Jukebox 2026 project.

---

**Generated with [Claude Code](https://claude.com/claude-code)**
