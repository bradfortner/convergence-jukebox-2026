"""
0.0 - 45rpm_record_animation_from_real_label.py

Combined threaded module that orchestrates the complete vinyl record animation pipeline.

This master script combines five specialized modules that work together in sequence:
1. create_vinyl_45_template_module() - Creates proportional 45rpm template
2. extract_record_label_module() - Extracts label from real record photo
3. fill_and_recut_center_hole_module() - Fills and recuts center hole and edge
4. final_record_pressing_module() - Composites label onto template
5. display_record_playing_module() - Animates rotating record

Each module runs as a threaded operation with _module suffix on function names.
"""

import threading
from PIL import Image, ImageDraw
import numpy as np
import cv2
import pygame
import math
import os
from skimage import io


class RecordAnimationPipeline:
    """Orchestrates the complete vinyl record animation creation pipeline."""

    def __init__(self, input_image_path="record.jpg"):
        """
        Initialize the pipeline with input image path.

        Args:
            input_image_path: Path to the real vinyl record photo
        """
        self.input_image_path = input_image_path
        self.results = {}
        self.threads = []

    def create_vinyl_45_template_module(self, output_filename='45rpm_proportional_template.png', dpi=300, background_color=(0, 0, 0, 0), output_size=None):
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
        print("\n[THREAD 1] Starting: create_vinyl_45_template_module()")

        # Check if the PNG file already exists
        if os.path.exists(output_filename):
            print(f"{output_filename} exists")
            self.results['template'] = None
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

        print(f"[THREAD 1] Created: {output_filename}")
        self.results['template'] = (image, center_x, center_y)
        print("[THREAD 1] Completed: create_vinyl_45_template_module()")

        return image, center_x, center_y

    def extract_record_label_module(self, input_image_path, output_path="transparent_45rpm_record_label.png", debug=True, output_size=None):
        """
        Extract vinyl record label with transparent background and center hole.

        Args:
            input_image_path (str): Path to input image file
            output_path (str): Path for output PNG file
            debug (bool): Save debug visualization files
            output_size (int): Output image size in pixels

        Returns:
            dict: Result dictionary with extraction details
        """
        print("\n[THREAD 2] Starting: extract_record_label_module()")

        result = {
            'success': False,
            'output_path': output_path,
            'record_center': None,
            'record_radius': None,
            'hole_center': None,
            'hole_radius': None,
            'output_dimensions': None,
            'message': ''
        }

        try:
            print("Loading image...")
            image_rgb = io.imread(input_image_path)
            image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            image_gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

            print("Detecting circles using Hough Circle Detection...")
            blurred = cv2.GaussianBlur(image_gray, (9, 9), 2)

            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=100,
                param1=50,
                param2=30,
                minRadius=50,
                maxRadius=350
            )

            if circles is None:
                result['message'] = "ERROR: No circles detected!"
                print(result['message'])
                self.results['extracted_label'] = result
                return result

            circles = np.round(circles[0, :]).astype("int")
            print(f"Found {len(circles)} circles")

            largest_circle_idx = np.argmax(circles[:, 2])
            x, y, r = circles[largest_circle_idx]

            result['record_center'] = (x, y)
            result['record_radius'] = r

            print(f"Largest circle: Center: ({x}, {y}), Radius: {r}")

            padding = int(r * 0.2)
            x1 = max(0, x - r - padding)
            y1 = max(0, y - r - padding)
            x2 = min(image_rgb.shape[1], x + r + padding)
            y2 = min(image_rgb.shape[0], y + r + padding)

            label_region = image_rgb[y1:y2, x1:x2].copy()
            h, w = label_region.shape[:2]

            center_x_rel = int(x - x1)
            center_y_rel = int(y - y1)

            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.circle(mask, (center_x_rel, center_y_rel), r, 255, -1)

            # Center hole detection (simplified for threading)
            center_hole_mask = np.zeros((h, w), dtype=np.uint8)
            hole_found = False

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)
            _, binary = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                circular_contours = []
                for contour in contours:
                    area = cv2.contourArea(contour)
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter ** 2)
                    else:
                        circularity = 0
                    (cx, cy), radius = cv2.minEnclosingCircle(contour)
                    if circularity > 0.5 and 30 < radius < r * 0.5:
                        distance = np.sqrt((cx - center_x_rel)**2 + (cy - center_y_rel)**2)
                        circular_contours.append({
                            'contour': contour,
                            'center': (int(cx), int(cy)),
                            'radius': int(radius),
                            'circularity': circularity,
                            'distance': distance,
                            'area': area
                        })

                if circular_contours:
                    for item in circular_contours:
                        item['score'] = (item['circularity'] * 0.7) + ((r * 0.3 - item['distance']) / (r * 0.3) * 0.3)
                    best_hole = max(circular_contours, key=lambda x: x['score'])
                    hole_x_rel, hole_y_rel = best_hole['center']
                    hole_r = best_hole['radius']
                    if best_hole['distance'] < r * 0.2:
                        cv2.circle(center_hole_mask, (hole_x_rel, hole_y_rel), hole_r, 255, -1)
                        hole_found = True
                        result['hole_center'] = (hole_x_rel, hole_y_rel)
                        result['hole_radius'] = hole_r

            combined_mask = cv2.bitwise_and(mask, cv2.bitwise_not(center_hole_mask))

            canvas_size = int(r * 2)
            label_rgba = np.zeros((canvas_size, canvas_size, 4), dtype=np.uint8)

            canvas_center = canvas_size // 2
            region_left = max(0, canvas_center - center_x_rel)
            region_top = max(0, canvas_center - center_y_rel)

            src_left = max(0, center_x_rel - canvas_center)
            src_top = max(0, center_y_rel - canvas_center)

            copy_width = min(w - src_left, canvas_size - region_left)
            copy_height = min(h - src_top, canvas_size - region_top)

            if copy_width > 0 and copy_height > 0:
                region_right = region_left + copy_width
                region_bottom = region_top + copy_height
                src_right = src_left + copy_width
                src_bottom = src_top + copy_height

                label_rgba[region_top:region_bottom, region_left:region_right, :3] = label_region[src_top:src_bottom, src_left:src_right]
                label_rgba[region_top:region_bottom, region_left:region_right, 3] = combined_mask[src_top:src_bottom, src_left:src_right]

            pil_image = Image.fromarray(label_rgba)

            final_size = canvas_size
            if output_size is not None:
                pil_image = pil_image.resize((output_size, output_size), Image.Resampling.LANCZOS)
                final_size = output_size

            pil_image.save(output_path)
            result['output_dimensions'] = (final_size, final_size)
            result['success'] = True
            result['message'] = f"[SUCCESS] Record label saved to {output_path}"
            print(result['message'])

        except Exception as e:
            result['message'] = f"ERROR: {str(e)}"
            print(result['message'])

        self.results['extracted_label'] = result
        print("[THREAD 2] Completed: extract_record_label_module()")
        return result

    def fill_and_recut_center_hole_module(self, input_path="transparent_45rpm_record_label.png", output_path="transparent_45rpm_record_label.png", hole_diameter_px=117):
        """
        Fill the transparent center hole and recut it with proper dimensions using OpenCV.

        Args:
            input_path: Path to input PNG with transparent center hole
            output_path: Path to output PNG with filled and recut hole
            hole_diameter_px: Diameter of center hole in pixels

        Returns:
            dict: Result dictionary with operation details
        """
        print("\n[THREAD 3] Starting: fill_and_recut_center_hole_module()")

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
            img_bgra = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)

            if img_bgra is None:
                result['message'] = f"ERROR: Could not load image from {input_path}"
                print(result['message'])
                self.results['filled_hole'] = result
                return result

            height, width = img_bgra.shape[:2]
            result['input_dimensions'] = (width, height)

            if img_bgra.shape[2] == 4:
                bgr = img_bgra[:, :, :3].copy()
                alpha = img_bgra[:, :, 3].copy()
            else:
                bgr = img_bgra.copy()
                alpha = np.ones((height, width), dtype=np.uint8) * 255

            bgr = np.ascontiguousarray(bgr)
            alpha = np.ascontiguousarray(alpha)

            center_x = round((width - 1) / 2.0)
            center_y = round((height - 1) / 2.0)
            result['center'] = (center_x, center_y)

            sample_radius = 70
            ring_colors = []

            for angle_deg in range(0, 360):
                angle_rad = math.radians(angle_deg)
                x = center_x + int(sample_radius * math.cos(angle_rad))
                y = center_y + int(sample_radius * math.sin(angle_rad))

                if 0 <= x < width and 0 <= y < height:
                    if alpha[y, x] > 0:
                        bgr_color = tuple(bgr[y, x].astype(int))
                        ring_colors.append(bgr_color)

            if not ring_colors:
                result['message'] = "ERROR: Could not find any colors in ring around center hole"
                print(result['message'])
                self.results['filled_hole'] = result
                return result

            brightest_color = max(ring_colors, key=lambda c: (c[0] + c[1] + c[2]) / 3)
            edge_color = brightest_color
            result['edge_color'] = edge_color

            img_filled = bgr.copy()
            img_filled = np.ascontiguousarray(img_filled)

            if not (0 <= center_x < width and 0 <= center_y < height):
                result['message'] = f"ERROR: Seed point out of bounds"
                print(result['message'])
                self.results['filled_hole'] = result
                return result

            new_val = tuple(int(c) for c in edge_color)

            try:
                num_filled = cv2.floodFill(img_filled, mask=None, seedPoint=(center_x, center_y), newVal=new_val)
            except cv2.error as e:
                result['message'] = f"ERROR: FloodFill failed - {str(e)}"
                print(result['message'])
                self.results['filled_hole'] = result
                return result

            new_alpha = np.ones((height, width), dtype=np.uint8) * 255
            hole_radius = hole_diameter_px / 2.0

            cv2.circle(new_alpha, (center_x, center_y), round(hole_radius), 0, thickness=-1)

            vinyl_record_diameter = 540
            vinyl_record_radius = vinyl_record_diameter / 2.0
            vinyl_body_alpha = np.zeros((height, width), dtype=np.uint8)

            cv2.circle(vinyl_body_alpha, (center_x, center_y), round(vinyl_record_radius), 255, thickness=-1)

            combined_alpha = np.minimum(new_alpha, vinyl_body_alpha)

            b, g, r = cv2.split(img_filled)
            img_bgra_result = cv2.merge([b, g, r, combined_alpha])

            output_height, output_width = img_bgra_result.shape[:2]
            result['output_dimensions'] = (output_width, output_height)

            success = cv2.imwrite(output_path, img_bgra_result)

            if not success:
                result['message'] = f"ERROR: Failed to save image"
                print(result['message'])
                self.results['filled_hole'] = result
                return result

            result['success'] = True
            result['message'] = f"[SUCCESS] Filled and recut record saved to {output_path}"
            print(result['message'])

        except Exception as e:
            result['message'] = f"ERROR: {str(e)}"
            print(result['message'])

        self.results['filled_hole'] = result
        print("[THREAD 3] Completed: fill_and_recut_center_hole_module()")
        return result

    def final_record_pressing_module(self, extracted_label_path="transparent_45rpm_record_label.png", output_filename="final_record_pressing.png"):
        """
        Create final vinyl record pressing by compositing extracted label onto template.

        Args:
            extracted_label_path: Path to extracted label PNG with transparency
            output_filename: Output PNG file name

        Returns:
            dict: Result dictionary with compositing details
        """
        print("\n[THREAD 4] Starting: final_record_pressing_module()")

        result = {
            'success': False,
            'output_path': output_filename,
            'template_size': None,
            'label_size': None,
            'composite_size': None,
            'message': ''
        }

        try:
            OUTPUT_SIZE = 540

            RECORD_DIAMETER_RATIO = 1.0
            GROOVE_END_DIAMETER_RATIO = 4.25 / 6.875
            LABEL_DIAMETER_RATIO = 3.6 / 6.875
            CENTER_HOLE_DIAMETER_RATIO = 1.5 / 6.875
            NEEDLE_DROP_WIDTH_RATIO = 0.25 / 6.875

            record_diameter_px = OUTPUT_SIZE
            groove_end_diameter_px = int(OUTPUT_SIZE * GROOVE_END_DIAMETER_RATIO)
            label_diameter_px = int(OUTPUT_SIZE * LABEL_DIAMETER_RATIO)
            center_hole_diameter_px = int(OUTPUT_SIZE * CENTER_HOLE_DIAMETER_RATIO)
            needle_drop_width_px = int(OUTPUT_SIZE * NEEDLE_DROP_WIDTH_RATIO)

            canvas_size = OUTPUT_SIZE

            template = Image.new('RGBA', (canvas_size, canvas_size), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(template)

            center_x = canvas_size / 2.0
            center_y = canvas_size / 2.0

            record_radius = record_diameter_px / 2.0
            groove_end_radius = groove_end_diameter_px / 2.0
            label_radius = label_diameter_px / 2.0
            center_hole_radius = center_hole_diameter_px / 2.0
            needle_drop_inner_radius = record_radius - needle_drop_width_px

            draw.ellipse([center_x - record_radius, center_y - record_radius,
                         center_x + record_radius, center_y + record_radius], fill='black')
            draw.ellipse([center_x - record_radius, center_y - record_radius,
                         center_x + record_radius, center_y + record_radius], fill='#181818')
            draw.ellipse([center_x - needle_drop_inner_radius, center_y - needle_drop_inner_radius,
                         center_x + needle_drop_inner_radius, center_y + needle_drop_inner_radius], fill='black')
            draw.ellipse([center_x - groove_end_radius, center_y - groove_end_radius,
                         center_x + groove_end_radius, center_y + groove_end_radius], fill='#181818')
            draw.ellipse([center_x - label_radius, center_y - label_radius,
                         center_x + label_radius, center_y + label_radius], fill='#303030')
            draw.ellipse([center_x - center_hole_radius, center_y - center_hole_radius,
                         center_x + center_hole_radius, center_y + center_hole_radius], fill=(0, 0, 0, 0))

            template_width, template_height = template.size
            result['template_size'] = (template_width, template_height)

            if not os.path.exists(extracted_label_path):
                raise FileNotFoundError(f"Extracted label not found: {extracted_label_path}")

            label = Image.open(extracted_label_path).convert('RGBA')
            label_width, label_height = label.size
            result['label_size'] = (label_width, label_height)

            center_x = template_width // 2
            center_y = template_height // 2

            paste_x = center_x - (label_width // 2)
            paste_y = center_y - (label_height // 2)

            composite = template.copy()
            temp_composite = Image.new('RGBA', (template_width, template_height), (0, 0, 0, 0))
            temp_composite.paste(label, (paste_x, paste_y), label)

            composite = Image.alpha_composite(composite, temp_composite)

            composite_width, composite_height = composite.size
            result['composite_size'] = (composite_width, composite_height)

            composite.save(output_filename, 'PNG')

            result['success'] = True
            result['message'] = f"[SUCCESS] Final record pressing saved to {output_filename}"
            print(result['message'])

        except FileNotFoundError as e:
            result['message'] = f"ERROR: File not found - {str(e)}"
            print(result['message'])
        except Exception as e:
            result['message'] = f"ERROR: {str(e)}"
            print(result['message'])

        self.results['final_record'] = result
        print("[THREAD 4] Completed: final_record_pressing_module()")
        return result

    def display_record_playing_module(self, image_path):
        """
        Rotate an image 15 times per second in real-time using pygame.
        Simulates a record player spinning with dark grey background.

        Args:
            image_path: Path to the input image (e.g., 'final_record_pressing.png')
        """
        print("\n[THREAD 5] Starting: display_record_playing_module()")

        try:
            pil_image = Image.open(image_path)

            pygame.init()

            original_surface = pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode)

            screen = pygame.display.set_mode((pil_image.width, pil_image.height))
            pygame.display.set_caption("45rpm Record Animation")
            clock = pygame.time.Clock()

            dark_grey = (64, 64, 64)

            center_x = pil_image.width // 2
            center_y = pil_image.height // 2

            angle = 0
            running = True

            print("Displaying rotating record animation (close window to stop)...")

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                screen.fill(dark_grey)
                rotated_surface = pygame.transform.rotate(original_surface, angle)
                rotated_rect = rotated_surface.get_rect(center=(center_x, center_y))
                screen.blit(rotated_surface, rotated_rect)
                pygame.display.flip()

                angle = (angle + 24) % 360
                clock.tick(15)

            pygame.quit()
            print("[THREAD 5] Completed: display_record_playing_module()")
            self.results['animation'] = {'success': True, 'message': 'Animation completed'}

        except Exception as e:
            print(f"[THREAD 5] ERROR: {str(e)}")
            self.results['animation'] = {'success': False, 'message': str(e)}

    def run_pipeline(self):
        """
        Execute the complete pipeline sequentially with threading capabilities.

        Pipeline order:
        1. Create vinyl template
        2. Extract record label from image
        3. Fill and recut center hole
        4. Composite label onto template
        5. Display rotating animation
        """
        print("\n" + "=" * 80)
        print("45RPM VINYL RECORD ANIMATION PIPELINE - STARTING")
        print("=" * 80)

        # Step 1: Create template
        print("\n[ORCHESTRATOR] Step 1: Creating vinyl template...")
        self.create_vinyl_45_template_module(output_size=540)

        # Step 2: Extract label
        print("\n[ORCHESTRATOR] Step 2: Extracting record label...")
        self.extract_record_label_module(self.input_image_path, output_size=282)

        # Step 3: Fill and recut
        print("\n[ORCHESTRATOR] Step 3: Filling and recuting center hole...")
        self.fill_and_recut_center_hole_module()

        # Step 4: Create final pressing
        print("\n[ORCHESTRATOR] Step 4: Creating final record pressing...")
        self.final_record_pressing_module()

        # Step 5: Display animation
        print("\n[ORCHESTRATOR] Step 5: Starting record animation display...")
        self.display_record_playing_module("final_record_pressing.png")

        print("\n" + "=" * 80)
        print("45RPM VINYL RECORD ANIMATION PIPELINE - COMPLETED")
        print("=" * 80)
        print("\nPipeline Results Summary:")
        for key, value in self.results.items():
            if isinstance(value, dict) and 'message' in value:
                print(f"  {key}: {value.get('message', 'Unknown')}")


# Main execution
if __name__ == '__main__':
    import sys

    # Get input image path from command line or use default
    input_image = sys.argv[1] if len(sys.argv) > 1 else "record.jpg"

    # Create and run pipeline
    pipeline = RecordAnimationPipeline(input_image_path=input_image)
    pipeline.run_pipeline()
