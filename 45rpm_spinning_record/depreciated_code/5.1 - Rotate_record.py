import pygame
from PIL import Image
import math

def display_record_playing(image_path):
    """
    Rotate an image 15 times per second in real-time using pygame.
    Simulates a record player spinning with dark grey background.

    Args:
        image_path: Path to the input image (e.g., 'final_record_pressing.png')
    """
    # Load image with PIL
    pil_image = Image.open(image_path)

    # Initialize pygame
    pygame.init()

    # Convert PIL image to pygame surface
    original_surface = pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode)

    # Set up display
    screen = pygame.display.set_mode((pil_image.width, pil_image.height))
    pygame.display.set_caption("Record Playing")
    clock = pygame.time.Clock()

    # Dark grey color
    dark_grey = (64, 64, 64)

    # Get center for rotation
    center_x = pil_image.width // 2
    center_y = pil_image.height // 2

    angle = 0
    running = True

    print("Starting endless animation (close window to stop)...")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fill background with dark grey
        screen.fill(dark_grey)

        # Rotate the surface by the current angle
        rotated_surface = pygame.transform.rotate(original_surface, angle)

        # Get the rect of rotated surface and center it
        rotated_rect = rotated_surface.get_rect(center=(center_x, center_y))

        # Display rotated image
        screen.blit(rotated_surface, rotated_rect)
        pygame.display.flip()

        # Increment angle: 360° per second at 15 fps = 24° per frame
        angle = (angle + 24) % 360

        # 15 fps = 1000ms / 15 = ~66.67ms per frame
        clock.tick(15)

    pygame.quit()

# Usage example
if __name__ == "__main__":
    display_record_playing('final_record_pressing.png')
