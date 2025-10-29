# 45 RPM Spinning Record - Vinyl Record Processing Suite

A comprehensive Python-based image processing pipeline for creating professional 45 RPM vinyl record graphics with transparent center holes and circular edges.

## Overview

This directory contains a series of interconnected scripts that work together to:
1. Generate vinyl record templates
2. Extract and prepare record labels with transparency
3. Fill transparent center holes with edge colors
4. Create properly cut vinyl records with circular edges
5. Rotate and animate spinning records

The project demonstrates iterative development from PIL/Pillow-based image processing to modern OpenCV implementations.

## Directory Structure

```
45rpm_spinning_record/
├── 1.0 - 45rpm_proportional_template.py          # Original vinyl template generator
├── 1.1 - 45rpm_proportional_template.py          # Updated: 540x540 pixel output
├── 2.0 - Extract_record_transparent.py           # Original label extraction
├── 2.1 - Extract_record_transparent.py           # Updated: 282x282 pixel output
├── 3.0 - centre_hole_fill_and_recut.py           # PIL: Fill center hole (Option 1)
├── 3.1 - centre_hole_fill_and_recut.py           # PIL: Fill + recut center hole
├── 3.2 - centre_hole_fill_and_recut.py           # PIL: Improved edge sampling (8 directions)
├── 3.3 - centre_hole_fill_and_recut.py           # PIL: Ring sampling + brightest color
├── 3.4 - centre_hole_fill_and_recut.py           # PIL: Add vinyl body circular edge trim
├── 3.5 - centre_hole_fill_and_recut.py           # OpenCV: Initial conversion (with centering fixes)
├── 3.6 - centre_hole_fill_and_recut.py           # OpenCV: FloodFill error fixes + robustness
├── 4.0 Rotate_record.py                          # Original record rotation
├── 4.1 - Final_record_pressing.py                # Final pressing/composition
├── 5.1 - Rotate_record.py                        # Optimized spinning animation
├── requirements.txt                              # Python dependencies
└── README.md                                     # This file
```

## Script Versions Overview

### Generation & Extraction (Versions 1.0-2.1)

#### 1.0 / 1.1 - 45rpm_proportional_template.py
Creates a vinyl record template with proper proportions for a 45 RPM record.
- **Input**: None (generates from scratch)
- **Output**: `45rpm_proportional_template.png` (540x540 pixels)
- **Key Features**: Draws vinyl record grooves, label area, center hole
- **1.1 Updates**: Precise 540x540 pixel output

#### 2.0 / 2.1 - Extract_record_transparent.py
Extracts a transparent record label from the composite image.
- **Input**: `45rpm_proportional_template.png`
- **Output**: `transparent_45rpm_record_label.png` (282x282 pixels with transparency)
- **Key Features**: Uses color detection to isolate record label, preserves transparency
- **2.1 Updates**: Optimized for 282x282 pixel output

### Center Hole Filling & Vinyl Body Processing (Versions 3.0-3.6)

This is the core module with iterative improvements:

#### 3.0 - centre_hole_fill_and_recut.py (PIL)
**First implementation of center hole filling**
- **Method**: Fill center hole with edge color
- **Approach**: Sample outward from center, detect edge color, use floodfill
- **Library**: PIL/Pillow
- **Output**: Filled center hole

#### 3.1 - centre_hole_fill_and_recut.py (PIL)
**Add center hole recutting**
- **Improvements**: After filling, recuts a transparent 117px diameter center hole
- **Key Addition**: Alpha channel manipulation for transparency
- **Proportions**: 117px = 1.5" on 6.875" record (RIAA spec)

#### 3.2 - centre_hole_fill_and_recut.py (PIL)
**Enhanced edge color detection**
- **Improvements**: Wider edge sampling using 8 directions (up, down, left, right, diagonals)
- **Benefit**: More robust color detection from various record label designs
- **Sampling Radius**: Multiple points at different angles

#### 3.3 - centre_hole_fill_and_recut.py (PIL)
**Ring sampling with brightest color selection**
- **Improvements**: Complete ring sampling (360 degrees) around center hole
- **Algorithm**: Samples all non-transparent colors in ring, selects brightest
- **Benefit**: Most robust color detection method for varied label designs
- **Output**: Brightest color used for consistent fill

#### 3.4 - centre_hole_fill_and_recut.py (PIL)
**Add vinyl record body circular edge trimming**
- **Major Feature**: Adds circular mask for vinyl record body
- **Circle Dimensions**: 540px diameter (270px radius)
- **Result**: Makes area outside record edge transparent
- **Final Output**: Complete vinyl record with:
  - Filled label
  - Transparent 117px center hole
  - Circular vinyl edge trim
  - Transparent background for compositing

#### 3.5 - centre_hole_fill_and_recut.py (OpenCV)
**Conversion from PIL to OpenCV**
- **Improvements**:
  - Uses `cv2.floodFill` instead of PIL's floodfill
  - Uses numpy arrays for faster alpha channel operations
  - Uses `cv2.circle` for circular drawing
- **Library**: OpenCV (cv2)
- **Fixes in version**: Better center calculation and rounding

#### 3.6 - centre_hole_fill_and_recut.py (OpenCV) ⭐ **CURRENT STABLE VERSION**
**OpenCV implementation with error handling & robustness**
- **Bug Fixes**:
  - Fixed `cv2.floodFill()` return value handling (returns int, not tuple)
  - Ensures image arrays are contiguous in memory
  - Validates seed point is within bounds
  - Proper data type conversion for BGR colors
- **Improvements**:
  - Better error messages
  - Try-catch for floodFill operations
  - Memory optimization with explicit copies
  - Pixel fill count in output
- **Status**: Production-ready

### Post-Processing (Versions 4.0-5.1)

#### 4.0 / 4.1 - Final_record_pressing.py
Final record pressing and composition.
- **Purpose**: Composite record onto background
- **Features**: Proper layering and sizing

#### 5.1 - Rotate_record.py
Spinning record animation.
- **Purpose**: Create rotating vinyl animation
- **Features**: Multiple rotation speeds, frame generation

## Usage

### Basic Usage

```python
from centre_hole_fill_and_recut import fill_and_recut_center_hole

# Use version 3.6 (OpenCV - recommended)
result = fill_and_recut_center_hole(
    input_path="transparent_45rpm_record_label.png",
    output_path="transparent_45rpm_record_label.png",
    hole_diameter_px=117
)

if result['success']:
    print("Record processing successful!")
    print(f"Output: {result['output_path']}")
else:
    print(f"Error: {result['message']}")
```

### Complete Pipeline

```bash
# 1. Generate vinyl template
python "1.1 - 45rpm_proportional_template.py"

# 2. Extract transparent label
python "2.1 - Extract_record_transparent.py"

# 3. Fill hole and trim edges (using OpenCV v3.6)
python "3.6 - centre_hole_fill_and_recut.py"

# 4. Final pressing
python "4.1 - Final_record_pressing.py"

# 5. Spinning animation
python "5.1 - Rotate_record.py"
```

## Requirements

```
Pillow (PIL)      - For image processing (versions 1.0-4.1)
opencv-python     - For advanced processing (versions 3.5-3.6)
numpy             - For array operations
```

Install requirements:
```bash
pip install -r requirements.txt
```

## Technical Details

### Center Hole Specifications
- **Diameter**: 117 pixels (at 282x282 base size)
- **Proportions**: 1.5" hole on 6.875" record (RIAA specification)
- **Final Position**: Centered in image

### Vinyl Record Body
- **Output Size**: 540x540 pixels
- **Diameter**: 540 pixels
- **Radius**: 270 pixels
- **Format**: PNG with RGBA (transparency support)

### Processing Steps (Version 3.6)

1. **Load Image**: Read transparent record label PNG
2. **Detect Edge Color**: Sample 360° ring around center hole
3. **Select Brightest Color**: Choose color with highest brightness value
4. **Floodfill**: Fill transparent center hole with detected color
5. **Recut Center Hole**: Create new 117px transparent hole
6. **Recut Vinyl Body**: Apply circular mask for record edge
7. **Combine Masks**: Merge alpha channels
8. **Save Result**: Output as PNG RGBA

## Version Evolution

### PIL to OpenCV Migration

**Why OpenCV?**
- Better performance with large images
- Native support for advanced image operations
- More efficient memory usage with numpy arrays
- Vectorized operations for faster processing

**Key Changes**
- `PIL.Image.open()` → `cv2.imread(IMREAD_UNCHANGED)`
- `PIL.ImageDraw.floodfill()` → `cv2.floodFill()`
- `PIL.ImageDraw.ellipse()` → `cv2.circle()`
- PIL alpha manipulation → numpy array operations

## Color Detection Algorithm

**Ring Sampling Method (v3.3+)**
1. Calculate center point of image
2. Sample 360 points in a ring around center hole (70px radius)
3. Collect all non-transparent pixels from ring
4. Calculate brightness for each: (B + G + R) / 3
5. Select color with highest brightness
6. Use selected color for floodfill

**Advantages**:
- Works with any record label design
- Automatically adapts to label colors
- Robust against slight image variations

## Output Specifications

### Final Image Format
- **Format**: PNG (Portable Network Graphics)
- **Color Space**: BGRA (Blue, Green, Red, Alpha)
- **Dimensions**: 282x282 pixels (or configurable)
- **Transparency**: Full support for compositing
- **Center Hole**: Fully transparent
- **Record Edge**: Circular with transparency outside

## Troubleshooting

### Issue: Center hole not centered (v3.5)
**Solution**: Update to v3.6 or later
- Fixed center calculation: `round((width-1)/2.0)`
- Uses proper rounding for pixel coordinates

### Issue: FloodFill error - "Bad argument" (v3.5)
**Solution**: Use v3.6
- Fixed return value handling
- Added memory contiguity checks
- Validates seed point bounds

### Issue: Color not detected
**Check**:
- Ensure input has transparent center hole
- Check that label has non-transparent pixels at radius 70px
- Verify image format supports transparency

## Contributing

When creating new versions:
1. Copy latest version
2. Update version number in docstring
3. Document changes in docstring "New in X.X" section
4. Test thoroughly before committing
5. Include detailed commit message
6. Update this README with version description

## License

Part of the Convergence Jukebox 2026 project.

## History

- **v1.0-2.1**: Initial PIL-based template and extraction
- **v3.0-3.1**: PIL center hole fill and recut
- **v3.2-3.3**: Enhanced edge detection with ring sampling
- **v3.4**: Vinyl body circular edge trimming
- **v3.5**: OpenCV conversion (initial)
- **v3.6**: OpenCV with robust error handling ⭐ **RECOMMENDED**
- **v4.0-5.1**: Post-processing and animation

## Contact

Generated with [Claude Code](https://claude.com/claude-code)
