"""
centre_hole_fill_and_recut.py - Version 3.0
Fill the transparent center hole in vinyl record label with edge color.

This module provides a function that:
1. Opens a vinyl record label with transparent center hole
2. Detects the color around the center hole perimeter
3. Uses PIL's floodfill to fill the transparent hole with that color
4. Saves the result as a filled PNG

The "recut" aspect allows the filled image to be used as a complete,
solid record label without the transparent hole.
"""

from PIL import Image, ImageDraw


def fill_center_hole(
    input_path="transparent_45rpm_record_label.png",
    output_path="transparent_45rpm_record_label_filled.png"
):
    """
    Fill the transparent center hole with the color from its edge.

    Uses edge color detection by sampling pixels outward from the center
    until finding the first non-transparent pixel. Then uses PIL's
    floodfill to fill the transparent center hole with that color.

    Args:
        input_path (str): Path to input PNG with transparent center hole
                         Default: transparent_45rpm_record_label.png
        output_path (str): Path to output PNG with filled center hole
                          Default: transparent_45rpm_record_label_filled.png

    Returns:
        dict: Result dictionary with keys:
            - 'success': bool indicating if fill was successful
            - 'output_path': path to saved PNG
            - 'input_dimensions': tuple (width, height) of input image
            - 'output_dimensions': tuple (width, height) of output image
            - 'edge_color': tuple (R, G, B) color used to fill hole
            - 'center': tuple (x, y) of image center
            - 'message': str with status message
    """

    result = {
        'success': False,
        'output_path': output_path,
        'input_dimensions': None,
        'output_dimensions': None,
        'edge_color': None,
        'center': None,
        'message': ''
    }

    try:
        print("=" * 60)
        print("FILLING CENTER HOLE - VERSION 3.0")
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
        print("\nSTEP 2: Detecting edge color")
        print("-" * 60)

        center_x = width // 2
        center_y = height // 2
        result['center'] = (center_x, center_y)

        print(f"Image center: ({center_x}, {center_y})")
        print(f"Searching outward from center for edge color...")

        edge_color = None

        # Search outward from center in concentric circles
        max_search_radius = min(center_x, center_y)
        for radius in range(1, max_search_radius):
            # Sample 4 points around center at this radius (cardinal directions)
            sample_points = [
                (center_x + radius, center_y),      # Right
                (center_x - radius, center_y),      # Left
                (center_x, center_y + radius),      # Down
                (center_x, center_y - radius),      # Up
            ]

            for x, y in sample_points:
                # Ensure point is within bounds
                if 0 <= x < width and 0 <= y < height:
                    pixel = img.getpixel((x, y))
                    # Check if pixel is not transparent (alpha > 0)
                    if pixel[3] > 0:
                        edge_color = pixel[:3]  # Extract RGB only
                        print(f"Found edge color at distance {radius} pixels")
                        print(f"Edge color (RGB): {edge_color}")
                        break

            if edge_color:
                break

        if not edge_color:
            result['message'] = "ERROR: Could not find edge color around center hole"
            print(result['message'])
            return result

        result['edge_color'] = edge_color

        # STEP 3: Convert to RGB and fill hole
        print("\nSTEP 3: Filling center hole with floodfill")
        print("-" * 60)

        # Convert RGBA to RGB (floodfill works on RGB)
        img_rgb = img.convert('RGB')
        draw = ImageDraw.Draw(img_rgb)

        print(f"Attempting floodfill at center ({center_x}, {center_y})...")
        print(f"Fill color: {edge_color}")

        # Perform floodfill from center point with edge color
        draw.floodfill((center_x, center_y), fill=edge_color)

        output_width, output_height = img_rgb.size
        result['output_dimensions'] = (output_width, output_height)

        print(f"Floodfill completed")
        print(f"Center hole filled with color {edge_color}")

        # STEP 4: Save result
        print("\nSTEP 4: Saving result")
        print("-" * 60)

        img_rgb.save(output_path)

        result['success'] = True
        result['message'] = f"[SUCCESS] Filled record label saved to {output_path}"

        print(f"Saved: {output_path}")
        print(f"Output dimensions: {output_width}x{output_height} pixels")
        print(f"Format: PNG RGB")

        # Print summary
        print("\n" + "=" * 60)
        print("FILL SUMMARY")
        print("=" * 60)
        print(f"Input file:       {input_path}")
        print(f"Input size:       {width}x{height} pixels")
        print(f"Center point:     ({center_x}, {center_y})")
        print(f"Edge color found: {edge_color}")
        print(f"Output file:      {output_path}")
        print(f"Output size:      {output_width}x{output_height} pixels")
        print(f"Format:           PNG RGB (center hole filled)")
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
    print("VINYL RECORD CENTER HOLE FILL - VERSION 3.0")
    print("=" * 60)

    result = fill_center_hole(
        input_path="transparent_45rpm_record_label.png",
        output_path="transparent_45rpm_record_label_filled.png"
    )

    if result['success']:
        print("\n[SUCCESS] Center hole filled!")
    else:
        print(f"\n[FAILED] {result['message']}")
