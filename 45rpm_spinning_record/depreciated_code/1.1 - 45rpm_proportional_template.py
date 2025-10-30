from PIL import Image, ImageDraw
import os

def create_vinyl_45_template(output_filename='45rpm_proportional_template.png', dpi=300, background_color=(0, 0, 0, 0), output_size=None):
    """
    Create a proportionally correct RIAA 45rpm vinyl record template.

    Specifications:
    - Record diameter: 6 7/8 inches (6.875")
    - Groove end diameter: 4 1/4 inches (4.25")
    - Label diameter: 3.6 inches
    - Center hole diameter: 1.5 inches
    - Needle drop area: 1/4 inch wide ring at outer edge

    Args:
        output_filename: Output PNG file name
        dpi: Dots per inch for quality (higher = larger file)
        background_color: Canvas background color
        output_size: Optional output image size in pixels (resizes final image if specified)
    """

    # Check if the PNG file already exists
    if os.path.exists(output_filename):
        print(f"{output_filename} exists")
        return None, None, None

    # RIAA 45rpm specifications (in inches)
    RECORD_DIAMETER = 6.875
    GROOVE_END_DIAMETER = 4.25
    LABEL_DIAMETER = 3.6
    CENTER_HOLE_DIAMETER = 1.5
    NEEDLE_DROP_WIDTH = 0.25  # Quarter inch needle drop area
    PADDING = 0.5  # Half inch padding around record

    # Convert to pixels
    record_diameter_px = int(RECORD_DIAMETER * dpi)
    groove_end_diameter_px = int(GROOVE_END_DIAMETER * dpi)
    label_diameter_px = int(LABEL_DIAMETER * dpi)
    center_hole_diameter_px = int(CENTER_HOLE_DIAMETER * dpi)
    needle_drop_width_px = int(NEEDLE_DROP_WIDTH * dpi)
    padding_px = int(PADDING * dpi)

    # Canvas size
    canvas_size = record_diameter_px

    # Create image with grey canvas (RGBA for transparency)
    image = Image.new('RGBA', (canvas_size, canvas_size), color=background_color)
    draw = ImageDraw.Draw(image)

    # Exact center point
    center_x = canvas_size / 2.0
    center_y = canvas_size / 2.0

    # Calculate radii (using exact center for precision)
    record_radius = record_diameter_px / 2.0
    groove_end_radius = groove_end_diameter_px / 2.0
    label_radius = label_diameter_px / 2.0
    center_hole_radius = center_hole_diameter_px / 2.0
    needle_drop_inner_radius = record_radius - needle_drop_width_px

    # Draw black vinyl (outer circle)
    draw.ellipse(
        [center_x - record_radius, center_y - record_radius,
         center_x + record_radius, center_y + record_radius],
        fill='black'
    )

    # Draw needle drop area (dark gray ring at outer edge)
    draw.ellipse(
        [center_x - record_radius, center_y - record_radius,
         center_x + record_radius, center_y + record_radius],
        fill='#181818'
    )

    # Draw inner black vinyl to create the needle drop ring
    draw.ellipse(
        [center_x - needle_drop_inner_radius, center_y - needle_drop_inner_radius,
         center_x + needle_drop_inner_radius, center_y + needle_drop_inner_radius],
        fill='black'
    )

    # Draw groove end circle (dark gray)
    draw.ellipse(
        [center_x - groove_end_radius, center_y - groove_end_radius,
         center_x + groove_end_radius, center_y + groove_end_radius],
        fill='#181818'
    )

    # Draw label area
    draw.ellipse(
        [center_x - label_radius, center_y - label_radius,
         center_x + label_radius, center_y + label_radius],
        fill='#303030'
    )

    # Draw transparent center hole
    draw.ellipse(
        [center_x - center_hole_radius, center_y - center_hole_radius,
         center_x + center_hole_radius, center_y + center_hole_radius],
        fill=(0, 0, 0, 0)
    )

    # Resize if output_size is specified
    if output_size is not None:
        print(f"Resizing from {canvas_size}x{canvas_size} to {output_size}x{output_size}...")
        image = image.resize((output_size, output_size), Image.Resampling.LANCZOS)
        canvas_size = output_size

    # Save as PNG
    image.save(output_filename)

    print(f"Created: {output_filename}")
    print(f"  Canvas: {canvas_size}x{canvas_size} px")
    print(f"  Center point: ({center_x}, {center_y})")
    print(f"  Record: {RECORD_DIAMETER}\" ({record_diameter_px}px diameter)")
    print(f"  Groove end: {GROOVE_END_DIAMETER}\" ({groove_end_diameter_px}px diameter)")
    print(f"  Label: {LABEL_DIAMETER}\" ({label_diameter_px}px diameter)")
    print(f"  Needle drop area: {NEEDLE_DROP_WIDTH}\" wide ({needle_drop_width_px}px)")
    print(f"  Center hole: {CENTER_HOLE_DIAMETER}\" ({center_hole_diameter_px}px diameter)")

    return image, center_x, center_y

def create_label_width_view(vinyl_image, center_x, center_y, label_diameter_px, output_filename='label_width.png'):
    """
    Extract and save a view of the label area from outer edge to center.

    Args:
        vinyl_image: PIL Image of the vinyl record
        center_x: X coordinate of center
        center_y: Y coordinate of center
        label_diameter_px: Label diameter in pixels
        output_filename: Output PNG file name
    """

    label_radius = label_diameter_px / 2.0

    # Define crop box: full label width (both sides of center) horizontally
    # Full height vertically
    left = int(center_x - label_radius)
    top = 0
    right = int(center_x + label_radius)
    bottom = int(vinyl_image.height)

    # Crop the image
    label_width_image = vinyl_image.crop((left, top, right, bottom))

    print(f"\nLabel width calculation:")
    print(f"  Size: {label_width_image.width}x{label_width_image.height} px")
    print(f"  Crop region: from label edge to center (horizontal)")
    print(f"  Label width: {label_width_image.width} px")

    return label_width_image

# Run the function
if __name__ == '__main__':
    # Create 540 x 540 pixel version
    image_540, center_x_540, center_y_540 = create_vinyl_45_template(
        output_filename='45rpm_proportional_template.png',
        dpi=300,
        output_size=540
    )

    # Create label width view for 540 version (only if image was created)
    if image_540 is not None:
        label_diameter_px_540 = int(540 * (3.6 / 6.875))  # Scale label size to match 540px output
        create_label_width_view(image_540, center_x_540, center_y_540, label_diameter_px_540,
                               output_filename='label_width_540.png')
