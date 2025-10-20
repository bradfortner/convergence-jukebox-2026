"""
final_record_pressing.py - Session 3.1
Composite extracted vinyl record label onto proportional 45 RPM template.

This module provides a single standalone function that:
1. Creates a proportionally correct 45 RPM vinyl record template
2. Loads the extracted record label with transparency
3. Composites the label onto the template
4. Outputs the final result as final_record_pressing.png

Key changes in 3.1:
- Template background is now transparent instead of black
- Center hole remains transparent
- Output preserves full RGBA transparency for both areas
"""

from PIL import Image, ImageDraw
import numpy as np
import os


def final_record_pressing(
    extracted_label_path="transparent_45rpm_record_label.png",
    output_filename="final_record_pressing.png",
    dpi=300
):
    """
    Create final vinyl record pressing by compositing extracted label onto template.

    Creates a proportionally correct RIAA 45rpm vinyl record with the extracted
    label centered on top. Generates the vinyl template internally and composites
    the extracted label with transparency to create a realistic pressed record.

    Specifications:
    - Record diameter: 6 7/8 inches (6.875")
    - Groove end diameter: 4 1/4 inches (4.25")
    - Label diameter: 3.6 inches
    - Center hole diameter: 1.5 inches
    - Needle drop area: 1/4 inch wide ring at outer edge
    - Background: TRANSPARENT (not black)
    - Center hole: TRANSPARENT

    Args:
        extracted_label_path (str): Path to extracted label PNG with transparency
                                   Default: transparent_45rpm_record_label.png
        output_filename (str): Output PNG file name
                             Default: final_record_pressing.png
        dpi (int): Dots per inch for quality (300 DPI standard for vinyl templates)
                  Default: 300

    Returns:
        dict: Result dictionary with keys:
            - 'success': bool indicating if compositing was successful
            - 'output_path': path to final saved PNG
            - 'template_size': tuple (width, height) of template
            - 'label_size': tuple (width, height) of label
            - 'composite_size': tuple (width, height) of final composite
            - 'message': str with status message

    Raises:
        FileNotFoundError: If extracted label file is not found
        Exception: If image processing fails
    """

    result = {
        'success': False,
        'output_path': output_filename,
        'template_size': None,
        'label_size': None,
        'composite_size': None,
        'message': ''
    }

    try:
        # STEP 1: Create vinyl record template
        print("=" * 60)
        print("STEP 1: Creating vinyl record template")
        print("=" * 60)

        # RIAA 45rpm specifications (in inches)
        RECORD_DIAMETER = 6.875
        GROOVE_END_DIAMETER = 4.25
        LABEL_DIAMETER = 3.6
        CENTER_HOLE_DIAMETER = 1.5
        NEEDLE_DROP_WIDTH = 0.25

        # Convert to pixels
        record_diameter_px = int(RECORD_DIAMETER * dpi)
        groove_end_diameter_px = int(GROOVE_END_DIAMETER * dpi)
        label_diameter_px = int(LABEL_DIAMETER * dpi)
        center_hole_diameter_px = int(CENTER_HOLE_DIAMETER * dpi)
        needle_drop_width_px = int(NEEDLE_DROP_WIDTH * dpi)

        # Canvas size
        canvas_size = record_diameter_px

        # Create template image with TRANSPARENT background
        template = Image.new('RGBA', (canvas_size, canvas_size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(template)

        # Exact center point
        center_x = canvas_size / 2.0
        center_y = canvas_size / 2.0

        # Calculate radii
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

        # Draw label area placeholder (medium gray)
        draw.ellipse(
            [center_x - label_radius, center_y - label_radius,
             center_x + label_radius, center_y + label_radius],
            fill='#303030'
        )

        # Draw transparent center hole (PRESERVED TRANSPARENCY)
        draw.ellipse(
            [center_x - center_hole_radius, center_y - center_hole_radius,
             center_x + center_hole_radius, center_y + center_hole_radius],
            fill=(0, 0, 0, 0)
        )

        template_width, template_height = template.size
        result['template_size'] = (template_width, template_height)

        print(f"Template created: {template_width}x{template_height} pixels")
        print(f"Template DPI: {dpi}")
        print(f"Record diameter: {RECORD_DIAMETER}\"")
        print(f"Label diameter: {LABEL_DIAMETER}\"")
        print(f"Center hole: {CENTER_HOLE_DIAMETER}\"")
        print(f"Template background: TRANSPARENT")

        # STEP 2: Load extracted label with transparency
        print("\n" + "=" * 60)
        print("STEP 2: Loading extracted label")
        print("=" * 60)

        if not os.path.exists(extracted_label_path):
            raise FileNotFoundError(f"Extracted label not found: {extracted_label_path}")

        label = Image.open(extracted_label_path).convert('RGBA')
        label_width, label_height = label.size
        result['label_size'] = (label_width, label_height)

        print(f"Label loaded: {label_width}x{label_height} pixels")
        print(f"Label format: RGBA (with transparency)")

        # STEP 3: Calculate sizing and positioning
        print("\n" + "=" * 60)
        print("STEP 3: Calculating sizing and positioning")
        print("=" * 60)

        # Calculate template dimensions in inches
        LABEL_DIAMETER = 3.6  # inches
        label_diameter_px = int(LABEL_DIAMETER * dpi)

        # Calculate label scaling factor
        # The extracted label should fit within the label area of the template
        label_scale = label_diameter_px / max(label_width, label_height)

        # Resize label to fit template label area
        new_label_size = int(label_width * label_scale)
        label_resized = label.resize(
            (new_label_size, new_label_size),
            Image.Resampling.LANCZOS
        )

        print(f"Label scaled: {new_label_size}x{new_label_size} pixels")
        print(f"Scale factor: {label_scale:.4f}")

        # Calculate center position
        center_x = template_width // 2
        center_y = template_height // 2

        # Calculate paste position (top-left corner)
        paste_x = center_x - (new_label_size // 2)
        paste_y = center_y - (new_label_size // 2)

        print(f"Template center: ({center_x}, {center_y})")
        print(f"Label paste position: ({paste_x}, {paste_y})")

        # STEP 4: Composite label onto template
        print("\n" + "=" * 60)
        print("STEP 4: Compositing label onto template")
        print("=" * 60)

        # Create a copy of the template to composite onto
        composite = template.copy()

        # Composite the resized label onto the template
        # Using alpha_composite for proper transparency handling
        # Create a temporary image with transparent background
        temp_composite = Image.new('RGBA', (template_width, template_height), (0, 0, 0, 0))
        temp_composite.paste(label_resized, (paste_x, paste_y), label_resized)

        # Composite onto template
        composite = Image.alpha_composite(composite, temp_composite)

        composite_width, composite_height = composite.size
        result['composite_size'] = (composite_width, composite_height)

        print(f"Composite created: {composite_width}x{composite_height} pixels")
        print(f"Label composited with full transparency support")

        # STEP 5: Save final result
        print("\n" + "=" * 60)
        print("STEP 5: Saving final result")
        print("=" * 60)

        # Save as PNG with full RGBA transparency preserved
        composite.save(output_filename, 'PNG')

        result['success'] = True
        result['message'] = f"[SUCCESS] Final record pressing saved to {output_filename}"

        print(f"\nFinal image saved: {output_filename}")
        print(f"Final size: {composite_width}x{composite_height} pixels")
        print(f"Format: PNG RGBA (with transparency)")
        print(f"Output areas: Background TRANSPARENT, Center hole TRANSPARENT")

        # Print summary
        print("\n" + "=" * 60)
        print("COMPOSITING SUMMARY")
        print("=" * 60)
        print(f"Template:        {template_width}x{template_height}px @ {dpi} DPI")
        print(f"Extracted Label: {label_width}x{label_height}px (original)")
        print(f"Label Scaled:    {new_label_size}x{new_label_size}px")
        print(f"Final Record:    {composite_width}x{composite_height}px")
        print(f"Output:          {output_filename}")
        print(f"Background:      TRANSPARENT")
        print(f"Center Hole:     TRANSPARENT")
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
    print("VINYL RECORD LABEL PLACEMENT - SESSION 3.1")
    print("=" * 60)

    result = final_record_pressing(
        extracted_label_path="transparent_45rpm_record_label.png",
        output_filename="final_record_pressing.png",
        dpi=300
    )

    if result['success']:
        print("\n[SUCCESS] Final record pressing created!")
    else:
        print(f"\n[FAILED] {result['message']}")
