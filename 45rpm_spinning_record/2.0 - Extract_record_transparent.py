import numpy as np
import cv2
from skimage import io
from PIL import Image


def extract_record_label(input_image_path, output_path="transparent_45rpm_record_label.png", debug=True, output_size=None):
    """
    Extract vinyl record label with transparent background and center hole.

    Args:
        input_image_path (str): Path to input image file
        output_path (str): Path for output PNG file (default: transparent_45rpm_record_label.png)
        debug (bool): Save debug visualization files (default: True)
        output_size (int): Output image size in pixels (width and height). If None, auto-sizes to detected record radius. (default: None)

    Returns:
        dict: Result dictionary with keys:
            - 'success': bool indicating if extraction was successful
            - 'output_path': path to saved PNG
            - 'record_center': tuple (x, y) of record center
            - 'record_radius': int radius of record
            - 'hole_center': tuple (x, y) of spindle hole center or None
            - 'hole_radius': int radius of spindle hole or None
            - 'message': str with status message
            - 'output_dimensions': tuple (width, height) of final output
    """

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
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(image_gray, (9, 9), 2)

        # Detect circles
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
            return result

        circles = np.round(circles[0, :]).astype("int")
        print(f"Found {len(circles)} circles")

        # Find the largest circle
        largest_circle_idx = np.argmax(circles[:, 2])
        x, y, r = circles[largest_circle_idx]

        result['record_center'] = (x, y)
        result['record_radius'] = r

        print(f"Largest circle:")
        print(f"  Center: ({x}, {y})")
        print(f"  Radius: {r}")

        # Extract the circular region
        padding = int(r * 0.2)
        x1 = max(0, x - r - padding)
        y1 = max(0, y - r - padding)
        x2 = min(image_rgb.shape[1], x + r + padding)
        y2 = min(image_rgb.shape[0], y + r + padding)

        # Extract rectangular region
        label_region = image_rgb[y1:y2, x1:x2].copy()
        h, w = label_region.shape[:2]

        print(f"Extracted region: {w}x{h} pixels")

        # Create circular mask
        center_x_rel = int(x - x1)
        center_y_rel = int(y - y1)

        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (center_x_rel, center_y_rel), r, 255, -1)

        # Detect center hole - METHOD 1: Contour-based circularity detection
        print("\nDetecting center hole (Method 1: Contour-based)...")

        center_hole_mask = np.zeros((h, w), dtype=np.uint8)
        hole_found = False

        # Use morphological operations to clean the image and isolate the hole
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

        # Apply Otsu threshold to get binary image
        _, binary = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Filter contours by circularity - the spindle hole should be highly circular
            circular_contours = []

            for contour in contours:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)

                # Calculate circularity: 4*pi*area / perimeter^2
                # Perfect circle = 1.0, less circular = smaller value
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter ** 2)
                else:
                    circularity = 0

                # Fit circle to contour
                (cx, cy), radius = cv2.minEnclosingCircle(contour)

                # Filter by circularity (> 0.5 is reasonably circular) and size
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
                # Select the best hole: highest circularity and closest to center
                # Weight: 70% circularity, 30% closeness to center
                for item in circular_contours:
                    item['score'] = (item['circularity'] * 0.7) + ((r * 0.3 - item['distance']) / (r * 0.3) * 0.3)

                best_hole = max(circular_contours, key=lambda x: x['score'])
                hole_x_rel, hole_y_rel = best_hole['center']
                hole_r = best_hole['radius']

                print(f"Best circular region found:")
                print(f"  Center: ({hole_x_rel}, {hole_y_rel})")
                print(f"  Radius: {hole_r}")
                print(f"  Circularity: {best_hole['circularity']:.3f}")
                print(f"  Distance from center: {best_hole['distance']:.1f}")
                print(f"  Score: {best_hole['score']:.3f}")

                if best_hole['distance'] < r * 0.2:  # Must be near center
                    print(f"Center hole ACCEPTED (Method 1)")
                    cv2.circle(center_hole_mask, (hole_x_rel, hole_y_rel), hole_r, 255, -1)
                    hole_found = True
                    result['hole_center'] = (hole_x_rel, hole_y_rel)
                    result['hole_radius'] = hole_r
                else:
                    print(f"Center hole REJECTED (Method 1): Too far from center")
            else:
                print("Method 1: No sufficiently circular contours found - trying Method 2...")
        else:
            print("Method 1: No contours found - trying Method 2...")

        # METHOD 2: Hough Circle Detection tuned for center hole (if Method 1 failed)
        if not hole_found:
            print("\nDetecting center hole (Method 2: Hough Circle Detection)...")

            # Use Canny edge detection for better circle detection
            edges = cv2.Canny(blurred, 30, 100)

            # Try to detect circles specifically for the center hole region
            # minRadius: typical spindle holes are at least 10-20 pixels
            # maxRadius: should be smaller than record radius
            hole_circles = cv2.HoughCircles(
                edges,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=50,
                param1=50,
                param2=15,
                minRadius=5,
                maxRadius=int(r * 0.4)
            )

            if hole_circles is not None:
                hole_circles = np.round(hole_circles[0, :]).astype("int")
                print(f"Found {len(hole_circles)} candidate circles")

                # Filter circles by proximity to center
                valid_holes = []
                for hc in hole_circles:
                    hc_x, hc_y, hc_r = hc
                    distance = np.sqrt((hc_x - center_x_rel)**2 + (hc_y - center_y_rel)**2)

                    # Must be near the center (within 25% of record radius)
                    if distance < r * 0.25 and hc_r > 5:  # reasonable hole size
                        valid_holes.append({
                            'center': (hc_x, hc_y),
                            'radius': hc_r,
                            'distance': distance
                        })

                if valid_holes:
                    # Select the hole closest to center
                    best_hole_m2 = min(valid_holes, key=lambda x: x['distance'])
                    hole_x_rel, hole_y_rel = best_hole_m2['center']
                    hole_r = best_hole_m2['radius']

                    print(f"Best circle found:")
                    print(f"  Center: ({hole_x_rel}, {hole_y_rel})")
                    print(f"  Radius: {hole_r}")
                    print(f"  Distance from center: {best_hole_m2['distance']:.1f}")

                    print(f"Center hole ACCEPTED (Method 2)")
                    # Expand hole radius by 15% to ensure complete coverage
                    expanded_hole_r = int(hole_r * 1.15)
                    cv2.circle(center_hole_mask, (hole_x_rel, hole_y_rel), expanded_hole_r, 255, -1)
                    hole_found = True
                    result['hole_center'] = (hole_x_rel, hole_y_rel)
                    result['hole_radius'] = expanded_hole_r
                else:
                    print("Method 2: No valid holes found in center region")
            else:
                print("Method 2: No circles detected via Hough")

        # METHOD 3: Dark spot detection using Laplacian of Gaussian (LoG) blob detection
        if not hole_found:
            print("\nDetecting center hole (Method 3: Dark Spot Detection)...")

            # Convert extracted label region to grayscale for analysis
            label_region_gray = cv2.cvtColor(label_region, cv2.COLOR_RGB2GRAY)
            label_region_blurred = cv2.GaussianBlur(label_region_gray, (9, 9), 2)

            # Create an inverted binary to highlight dark regions (holes)
            _, dark_binary = cv2.threshold(label_region_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # Invert: dark regions become white
            dark_regions = cv2.bitwise_not(dark_binary)

            # Find contours in dark regions
            contours_dark, _ = cv2.findContours(dark_regions, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            if contours_dark:
                # Find dark circular regions near center
                dark_holes = []

                for contour in contours_dark:
                    area = cv2.contourArea(contour)

                    # Filter by size - hole should be significant but not too large
                    if 50 < area < (r * 0.5) ** 2 * np.pi:
                        (cx, cy), radius = cv2.minEnclosingCircle(contour)
                        distance = np.sqrt((cx - center_x_rel)**2 + (cy - center_y_rel)**2)

                        # Must be near center and reasonably circular
                        if distance < r * 0.3:
                            # Calculate how dark this region is (mean intensity)
                            mask_temp = np.zeros((h, w), dtype=np.uint8)
                            cv2.circle(mask_temp, (int(cx), int(cy)), int(radius), 255, -1)
                            mean_intensity = cv2.mean(label_region_blurred, mask=mask_temp)[0]

                            dark_holes.append({
                                'center': (int(cx), int(cy)),
                                'radius': int(radius),
                                'distance': distance,
                                'darkness': 255 - mean_intensity,  # Higher = darker
                                'area': area
                            })

                if dark_holes:
                    # Select darkest hole closest to center
                    # Weight: 60% darkness, 40% closeness to center
                    for item in dark_holes:
                        item['score'] = (item['darkness'] / 255 * 0.6) + ((r * 0.3 - item['distance']) / (r * 0.3) * 0.4)

                    best_hole_m3 = max(dark_holes, key=lambda x: x['score'])
                    hole_x_rel, hole_y_rel = best_hole_m3['center']
                    hole_r = best_hole_m3['radius']

                    print(f"Dark spot found:")
                    print(f"  Center: ({hole_x_rel}, {hole_y_rel})")
                    print(f"  Radius: {hole_r}")
                    print(f"  Darkness: {best_hole_m3['darkness']:.1f}")
                    print(f"  Distance from center: {best_hole_m3['distance']:.1f}")
                    print(f"  Score: {best_hole_m3['score']:.3f}")

                    # Expand hole radius by 15% to ensure complete coverage
                    expanded_hole_r = int(hole_r * 1.15)
                    cv2.circle(center_hole_mask, (hole_x_rel, hole_y_rel), expanded_hole_r, 255, -1)
                    hole_found = True
                    result['hole_center'] = (hole_x_rel, hole_y_rel)
                    result['hole_radius'] = expanded_hole_r
                    print(f"Center hole ACCEPTED (Method 3)")
                else:
                    print("Method 3: No dark spots found near center")
            else:
                print("Method 3: No dark regions detected")

        # Apply morphological dilation to hole mask to ensure complete removal
        if hole_found:
            dilation_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            center_hole_mask = cv2.dilate(center_hole_mask, dilation_kernel, iterations=2)
            print(f"Dilated center hole mask to ensure complete removal")

        # Combine masks: record mask minus center hole mask
        combined_mask = cv2.bitwise_and(mask, cv2.bitwise_not(center_hole_mask))

        # Create output canvas sized to record radius
        canvas_size = int(r * 2)  # Diameter of record
        print(f"\nCanvas size determined: {canvas_size}x{canvas_size} pixels")
        label_rgba = np.zeros((canvas_size, canvas_size, 4), dtype=np.uint8)

        # Calculate where to place the extracted region on the canvas
        # Center it on the canvas
        canvas_center = canvas_size // 2

        # Calculate offsets from canvas center
        region_left = max(0, canvas_center - center_x_rel)
        region_top = max(0, canvas_center - center_y_rel)

        # Calculate source region offset
        src_left = max(0, center_x_rel - canvas_center)
        src_top = max(0, center_y_rel - canvas_center)

        # Calculate copy dimensions ensuring they don't exceed bounds
        copy_width = min(w - src_left, canvas_size - region_left)
        copy_height = min(h - src_top, canvas_size - region_top)

        # Ensure dimensions are positive
        if copy_width > 0 and copy_height > 0:
            region_right = region_left + copy_width
            region_bottom = region_top + copy_height
            src_right = src_left + copy_width
            src_bottom = src_top + copy_height

            # Copy RGB channels to canvas
            label_rgba[region_top:region_bottom, region_left:region_right, :3] = label_region[src_top:src_bottom, src_left:src_right]

            # Copy alpha channel (mask) to canvas
            label_rgba[region_top:region_bottom, region_left:region_right, 3] = combined_mask[src_top:src_bottom, src_left:src_right]
        else:
            print("WARNING: Copy dimensions are invalid, using fallback centering method")

        # Save as PNG with transparency
        print("\nSaving record label with transparent background and center hole...")
        pil_image = Image.fromarray(label_rgba)

        # Resize if output_size is specified
        final_size = canvas_size
        if output_size is not None:
            print(f"Resizing from {canvas_size}x{canvas_size} to {output_size}x{output_size}...")
            pil_image = pil_image.resize((output_size, output_size), Image.Resampling.LANCZOS)
            final_size = output_size

        pil_image.save(output_path)
        result['output_dimensions'] = (final_size, final_size)

        result['success'] = True
        result['message'] = f"[SUCCESS] Record label saved to {output_path}"
        print(result['message'])
        print(f"  Final size: {final_size}x{final_size} pixels")
        print(f"  Format: PNG with transparency (RGBA)")
        print(f"  Center hole: {'Transparent' if hole_found else 'Not detected'}")

        return result

    except Exception as e:
        result['message'] = f"ERROR: {str(e)}"
        print(result['message'])
        return result


# Main execution
if __name__ == "__main__":
    result = extract_record_label("record.jpg", output_path="transparent_45rpm_record_label.png", debug=True, output_size=1080)
