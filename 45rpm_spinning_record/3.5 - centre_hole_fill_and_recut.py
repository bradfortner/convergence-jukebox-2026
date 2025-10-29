"""
centre_hole_fill_and_recut.py - Version 3.5
Fill, recut center hole, and trim vinyl record body using OpenCV.

This module provides a function that:
1. Opens a vinyl record label with transparent center hole
2. Detects the color around the center hole perimeter using ring sampling
3. Uses OpenCV's floodFill to fill the transparent hole with that color
4. Recuts a new 117-pixel diameter transparent center hole (proportional to 1.5" on 6.875" record)
5. Recuts the vinyl record body: trims all area outside 540x540 circular record edge
6. Saves the result with transparent background

New in 3.5:
- Converts from PIL/Pillow to OpenCV (cv2) for image processing
- Uses cv2.floodFill instead of PIL's floodfill
- Implements circular masks using OpenCV's circle drawing
- More efficient alpha channel manipulation with numpy arrays
- Maintains all functionality from version 3.4

This creates a complete vinyl record with proper circular edge,
filled label, and transparent center spindle hole using OpenCV.
"""

import cv2
import numpy as np
import math


def fill_and_recut_center_hole(
    input_path="transparent_45rpm_record_label.png",
    output_path="transparent_45rpm_record_label.png",
    hole_diameter_px=117
):
    """
    Fill the transparent center hole and then recut it with proper dimensions using OpenCV.

    Process:
    1. Detect edge color by sampling outward from center
    2. Fill the transparent hole using OpenCV's floodFill
    3. Recut a new transparent center hole (117 pixels = 1.5" on 6.875" record)
    4. Save as RGBA PNG with transparent background

    Args:
        input_path (str): Path to input PNG with transparent center hole
                         Default: transparent_45rpm_record_label.png
        output_path (str): Path to output PNG with filled and recut hole
                          Default: transparent_45rpm_record_label.png
        hole_diameter_px (int): Diameter of center hole in pixels
                               Default: 117 pixels (proportional RIAA spec)

    Returns:
        dict: Result dictionary with keys:
            - 'success': bool indicating if operation was successful
            - 'output_path': path to saved PNG
            - 'input_dimensions': tuple (width, height) of input image
            - 'output_dimensions': tuple (width, height) of output image
            - 'edge_color': tuple (B, G, R) color used to fill hole (OpenCV BGR format)
            - 'center': tuple (x, y) of image center
            - 'hole_diameter': int diameter of recut hole in pixels
            - 'hole_radius': int radius of recut hole in pixels
            - 'message': str with status message
    """

    result = {
        'success': False,
        'output_path': output_path,
        'input_dimensions': None,
        'output_dimensions': None,
        'edge_color': None,
        'center': None,
        'hole_diameter': hole_diameter_px,
        'hole_radius': hole_diameter_px // 2,
        'message': ''
    }

    try:
        print("=" * 60)
        print("FILL AND RECUT CENTER HOLE AND VINYL BODY - VERSION 3.5 (OpenCV)")
        print("=" * 60)

        # STEP 1: Load image
        print("\nSTEP 1: Loading image")
        print("-" * 60)

        # Load image with alpha channel (BGRA format)
        img_bgra = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)

        if img_bgra is None:
            result['message'] = f"ERROR: Could not load image from {input_path}"
            print(result['message'])
            return result

        height, width = img_bgra.shape[:2]
        result['input_dimensions'] = (width, height)

        print(f"Loaded: {input_path}")
        print(f"Dimensions: {width}x{height} pixels")
        print(f"Format: BGRA (with transparency)")

        # Check if image has alpha channel
        if img_bgra.shape[2] == 4:
            bgr = img_bgra[:, :, :3]
            alpha = img_bgra[:, :, 3]
        else:
            bgr = img_bgra
            alpha = np.ones((height, width), dtype=np.uint8) * 255

        # STEP 2: Find center and detect edge color
        print("\nSTEP 2: Detecting edge color using ring sampling")
        print("-" * 60)

        # Calculate center with subpixel precision, then round to nearest integer
        center_x = round((width - 1) / 2.0)
        center_y = round((height - 1) / 2.0)
        result['center'] = (center_x, center_y)

        print(f"Image center: ({center_x}, {center_y})")
        print(f"Sampling ring around hole edge to find brightest color...")

        edge_color = None

        # Sample a ring of pixels around the hole edge
        # Hole diameter is 117, so radius is ~58.5
        # Sample at radius ~70 pixels (just beyond the hole edge)
        sample_radius = 70

        ring_colors = []

        # Sample 360 points around the ring (every degree)
        for angle_deg in range(0, 360):
            angle_rad = math.radians(angle_deg)

            # Calculate point on ring at this angle
            x = center_x + int(sample_radius * math.cos(angle_rad))
            y = center_y + int(sample_radius * math.sin(angle_rad))

            # Ensure point is within bounds
            if 0 <= x < width and 0 <= y < height:
                # Check alpha channel to see if pixel is not transparent
                if alpha[y, x] > 0:  # Not transparent
                    # Get BGR color (OpenCV uses BGR, not RGB)
                    bgr_color = tuple(bgr[y, x])
                    ring_colors.append(bgr_color)

        if not ring_colors:
            result['message'] = "ERROR: Could not find any colors in ring around center hole"
            print(result['message'])
            return result

        # Find brightest color (highest combined BGR value)
        # Brightness = (B + G + R) / 3
        brightest_color = max(ring_colors, key=lambda c: (c[0] + c[1] + c[2]) / 3)
        edge_color = brightest_color

        brightness = (edge_color[0] + edge_color[1] + edge_color[2]) / 3

        print(f"Ring sampling complete: {len(ring_colors)} colors found")
        print(f"Selected brightest color (BGR): {edge_color}")
        print(f"Brightness value: {brightness:.1f}/255")

        result['edge_color'] = edge_color

        # STEP 3: Convert to BGR (not RGB) and fill hole
        print("\nSTEP 3: Filling center hole with floodFill")
        print("-" * 60)

        # Create a copy for floodfill operation (operates on BGR image)
        img_filled = bgr.copy()

        print(f"Attempting floodFill at center ({center_x}, {center_y})...")
        print(f"Fill color (BGR): {edge_color}")

        # Perform floodfill from center point with edge color
        # cv2.floodFill modifies the image in-place
        # Returns the number of pixels filled
        seed_point = (center_x, center_y)
        new_val = edge_color

        # floodFill parameters: image, mask (None), seedPoint, newVal
        num_filled, _, _, _, _ = cv2.floodFill(
            img_filled,
            mask=None,
            seedPoint=seed_point,
            newVal=new_val
        )

        print(f"Floodfill completed: {num_filled} pixels filled")
        print(f"Center hole filled with color {edge_color}")

        # STEP 4: Recut transparent center hole
        print("\nSTEP 4: Recuting center hole with transparency")
        print("-" * 60)

        # Create a new alpha channel (all opaque initially)
        new_alpha = np.ones((height, width), dtype=np.uint8) * 255

        hole_radius = hole_diameter_px / 2.0

        print(f"Center hole specifications:")
        print(f"  Diameter: {hole_diameter_px} pixels (proportional to 1.5\" on 6.875\" record)")
        print(f"  Radius: {hole_radius} pixels")
        print(f"  Center: ({center_x}, {center_y})")

        # Draw transparent center hole in alpha channel (0 = transparent)
        # Use round() instead of int() for better centering precision
        cv2.circle(
            new_alpha,
            (center_x, center_y),
            round(hole_radius),
            0,  # 0 = fully transparent
            thickness=-1  # -1 means filled circle
        )

        print(f"Transparent hole recut: {hole_diameter_px}px diameter")

        # STEP 5: Recut vinyl record body edge (circular mask)
        print("\nSTEP 5: Recuting vinyl record body edge")
        print("-" * 60)

        # Create circular vinyl record mask (540x540 = 270 pixel radius)
        # This trims everything outside the circular record body
        vinyl_record_diameter = 540
        vinyl_record_radius = vinyl_record_diameter / 2.0

        # Create vinyl body mask (opaque for circle, transparent outside)
        vinyl_body_alpha = np.zeros((height, width), dtype=np.uint8)  # Start fully transparent

        print(f"Vinyl record body specifications:")
        print(f"  Diameter: {vinyl_record_diameter} pixels")
        print(f"  Radius: {vinyl_record_radius} pixels")
        print(f"  Center: ({center_x}, {center_y})")

        # Draw opaque circle for the vinyl record (inside the circle = opaque)
        # Use round() for consistent centering with hole
        cv2.circle(
            vinyl_body_alpha,
            (center_x, center_y),
            round(vinyl_record_radius),
            255,  # 255 = fully opaque
            thickness=-1  # -1 means filled circle
        )

        print(f"Vinyl record body edge recut: {vinyl_record_diameter}px diameter circular edge")
        print(f"Area outside circle is now transparent")

        # STEP 6: Combine alpha channels
        print("\nSTEP 6: Combining alpha channels")
        print("-" * 60)

        # Combine masks: keep pixel only if opaque in BOTH masks
        # Use element-wise minimum to combine (stricter transparency)
        combined_alpha = np.minimum(new_alpha, vinyl_body_alpha)

        # STEP 7: Create final BGRA image
        print("\nSTEP 7: Creating final BGRA image")
        print("-" * 60)

        # Merge BGR and alpha channel
        img_bgra_result = cv2.merge([img_filled, img_filled, img_filled[:, :], combined_alpha])

        # Actually, let's do this correctly - keep the filled BGR and add combined alpha
        b, g, r = cv2.split(img_filled)
        img_bgra_result = cv2.merge([b, g, r, combined_alpha])

        output_height, output_width = img_bgra_result.shape[:2]
        result['output_dimensions'] = (output_width, output_height)

        # STEP 8: Save result
        print("\nSTEP 8: Saving result")
        print("-" * 60)

        # Save as PNG with alpha channel
        success = cv2.imwrite(output_path, img_bgra_result)

        if not success:
            result['message'] = f"ERROR: Failed to save image to {output_path}"
            print(result['message'])
            return result

        result['success'] = True
        result['message'] = f"[SUCCESS] Filled and recut record label saved to {output_path}"

        print(f"Saved: {output_path}")
        print(f"Output dimensions: {output_width}x{output_height} pixels")
        print(f"Format: PNG BGRA (with transparent center hole)")

        # Print summary
        print("\n" + "=" * 60)
        print("FILL, RECUT CENTER HOLE, AND TRIM VINYL BODY SUMMARY")
        print("=" * 60)
        print(f"Input file:         {input_path}")
        print(f"Input size:         {width}x{height} pixels")
        print(f"Center point:       ({center_x}, {center_y})")
        print(f"Edge color found:   {edge_color} (BGR format)")
        print(f"Fill operation:     FloodFill from center")
        print(f"Center hole:        {hole_diameter_px}px diameter (1.5\" on 6.875\" record)")
        print(f"Vinyl record body:  {vinyl_record_diameter}px diameter circular edge")
        print(f"Output file:        {output_path}")
        print(f"Output size:        {output_width}x{output_height} pixels")
        print(f"Format:             PNG BGRA (circular record, filled label, transparent hole)")
        print("=" * 60)

        return result

    except FileNotFoundError as e:
        result['message'] = f"ERROR: File not found - {str(e)}"
        print(result['message'])
        return result
    except Exception as e:
        result['message'] = f"ERROR: {str(e)}"
        print(result['message'])
        import traceback
        traceback.print_exc()
        return result


# Main execution
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("VINYL RECORD CENTER HOLE FILL AND RECUT - VERSION 3.5 (OpenCV)")
    print("=" * 60)

    result = fill_and_recut_center_hole(
        input_path="transparent_45rpm_record_label.png",
        output_path="transparent_45rpm_record_label.png",
        hole_diameter_px=117
    )

    if result['success']:
        print("\n[SUCCESS] Center hole filled and recut!")
    else:
        print(f"\n[FAILED] {result['message']}")
