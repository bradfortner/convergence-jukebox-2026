"""
centre_hole_fill_and_recut.py - Version 3.4
Fill, recut center hole, and trim vinyl record body.

This module provides a function that:
1. Opens a vinyl record label with transparent center hole
2. Detects the color around the center hole perimeter using ring sampling
3. Uses PIL's floodfill to fill the transparent hole with that color
4. Recuts a new 117-pixel diameter transparent center hole (proportional to 1.5" on 6.875" record)
5. Recuts the vinyl record body: trims all area outside 540x540 circular record edge
6. Saves the result with transparent background

New in 3.4:
- Adds vinyl record body trimming (circular mask)
- Creates 270-pixel radius circle (540x540 record body)
- Makes everything outside the vinyl circle transparent
- Maintains center hole transparency
- Perfect for compositing onto backgrounds

This creates a complete vinyl record with proper circular edge,
filled label, and transparent center spindle hole.
"""

from PIL import Image, ImageDraw
import math


def fill_and_recut_center_hole(
    input_path="transparent_45rpm_record_label.png",
    output_path="transparent_45rpm_record_label.png",
    hole_diameter_px=117
):
    """
    Fill the transparent center hole and then recut it with proper dimensions.

    Process:
    1. Detect edge color by sampling outward from center
    2. Fill the transparent hole using PIL's floodfill
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
            - 'edge_color': tuple (R, G, B) color used to fill hole
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
        print("FILL AND RECUT CENTER HOLE AND VINYL BODY - VERSION 3.4")
        print("=" * 60)

        # STEP 1: Load image
        print("\nSTEP 1: Loading image")
        print("-" * 60)

        img = Image.open(input_path).convert('RGBA')
        width, height = img.size
        result['input_dimensions'] = (width, height)

        print(f"Loaded: {input_path}")
        print(f"Dimensions: {width}x{height} pixels")
        print(f"Format: RGBA (with transparency)")

        # STEP 2: Find center and detect edge color
        print("\nSTEP 2: Detecting edge color using ring sampling")
        print("-" * 60)

        center_x = width // 2
        center_y = height // 2
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
                pixel = img.getpixel((x, y))
                # Collect non-transparent colors
                if pixel[3] > 0:  # Not transparent
                    rgb = pixel[:3]
                    ring_colors.append(rgb)

        if not ring_colors:
            result['message'] = "ERROR: Could not find any colors in ring around center hole"
            print(result['message'])
            return result

        # Find brightest color (highest combined RGB value)
        # Brightness = (R + G + B) / 3
        brightest_color = max(ring_colors, key=lambda c: (c[0] + c[1] + c[2]) / 3)
        edge_color = brightest_color

        brightness = (edge_color[0] + edge_color[1] + edge_color[2]) / 3

        print(f"Ring sampling complete: {len(ring_colors)} colors found")
        print(f"Selected brightest color (RGB): {edge_color}")
        print(f"Brightness value: {brightness:.1f}/255")

        result['edge_color'] = edge_color

        # STEP 3: Convert to RGB and fill hole
        print("\nSTEP 3: Filling center hole with floodfill")
        print("-" * 60)

        # Convert RGBA to RGB (floodfill works on RGB)
        img_rgb = img.convert('RGB')

        print(f"Attempting floodfill at center ({center_x}, {center_y})...")
        print(f"Fill color: {edge_color}")

        # Perform floodfill from center point with edge color
        # floodfill is a module-level function in ImageDraw, not a method
        ImageDraw.floodfill(img_rgb, (center_x, center_y), edge_color)

        print(f"Floodfill completed")
        print(f"Center hole filled with color {edge_color}")

        # STEP 4: Recut transparent center hole
        print("\nSTEP 4: Recuting center hole with transparency")
        print("-" * 60)

        # Convert filled RGB back to RGBA
        img_rgba = img_rgb.convert('RGBA')

        # Create a new alpha channel (all opaque initially)
        alpha_channel = Image.new('L', (width, height), 255)
        alpha_draw = ImageDraw.Draw(alpha_channel)

        hole_radius = hole_diameter_px / 2.0

        print(f"Center hole specifications:")
        print(f"  Diameter: {hole_diameter_px} pixels (proportional to 1.5\" on 6.875\" record)")
        print(f"  Radius: {hole_radius} pixels")
        print(f"  Center: ({center_x}, {center_y})")

        # Draw transparent center hole in alpha channel (0 = transparent)
        alpha_draw.ellipse(
            [center_x - hole_radius, center_y - hole_radius,
             center_x + hole_radius, center_y + hole_radius],
            fill=0  # 0 = fully transparent
        )

        print(f"Transparent hole recut: {hole_diameter_px}px diameter")

        # Apply alpha channel to image
        img_rgba.putalpha(alpha_channel)

        # STEP 5: Recut vinyl record body edge (circular mask)
        print("\nSTEP 5: Recuting vinyl record body edge")
        print("-" * 60)

        # Create circular vinyl record mask (540x540 = 270 pixel radius)
        # This trims everything outside the circular record body
        vinyl_record_diameter = 540
        vinyl_record_radius = vinyl_record_diameter / 2.0

        # Create vinyl body mask (opaque for circle, transparent outside)
        vinyl_body_alpha = Image.new('L', (width, height), 0)  # Start fully transparent
        vinyl_draw = ImageDraw.Draw(vinyl_body_alpha)

        print(f"Vinyl record body specifications:")
        print(f"  Diameter: {vinyl_record_diameter} pixels")
        print(f"  Radius: {vinyl_record_radius} pixels")
        print(f"  Center: ({center_x}, {center_y})")

        # Draw opaque circle for the vinyl record (inside the circle = opaque)
        vinyl_draw.ellipse(
            [center_x - vinyl_record_radius, center_y - vinyl_record_radius,
             center_x + vinyl_record_radius, center_y + vinyl_record_radius],
            fill=255  # 255 = fully opaque
        )

        # Combine with existing alpha channel: keep the smaller value
        # This preserves the center hole transparency while adding record edge trim
        current_alpha = img_rgba.split()[3]  # Get current alpha channel
        combined_alpha = Image.new('L', (width, height), 0)

        for y in range(height):
            for x in range(width):
                current_a = current_alpha.getpixel((x, y))
                vinyl_a = vinyl_body_alpha.getpixel((x, y))
                # Keep the pixel only if it's opaque in BOTH masks
                combined_alpha.putpixel((x, y), min(current_a, vinyl_a))

        img_rgba.putalpha(combined_alpha)

        print(f"Vinyl record body edge recut: {vinyl_record_diameter}px diameter circular edge")
        print(f"Area outside circle is now transparent")

        output_width, output_height = img_rgba.size
        result['output_dimensions'] = (output_width, output_height)

        # STEP 6: Save result
        print("\nSTEP 6: Saving result")
        print("-" * 60)

        img_rgba.save(output_path, 'PNG')

        result['success'] = True
        result['message'] = f"[SUCCESS] Filled and recut record label saved to {output_path}"

        print(f"Saved: {output_path}")
        print(f"Output dimensions: {output_width}x{output_height} pixels")
        print(f"Format: PNG RGBA (with transparent center hole)")

        # Print summary
        print("\n" + "=" * 60)
        print("FILL, RECUT CENTER HOLE, AND TRIM VINYL BODY SUMMARY")
        print("=" * 60)
        print(f"Input file:         {input_path}")
        print(f"Input size:         {width}x{height} pixels")
        print(f"Center point:       ({center_x}, {center_y})")
        print(f"Edge color found:   {edge_color}")
        print(f"Fill operation:     Floodfill from center")
        print(f"Center hole:        {hole_diameter_px}px diameter (1.5\" on 6.875\" record)")
        print(f"Vinyl record body:  {vinyl_record_diameter}px diameter circular edge")
        print(f"Output file:        {output_path}")
        print(f"Output size:        {output_width}x{output_height} pixels")
        print(f"Format:             PNG RGBA (circular record, filled label, transparent hole)")
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
    print("VINYL RECORD CENTER HOLE FILL AND RECUT - VERSION 3.4")
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
