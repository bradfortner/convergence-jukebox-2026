"""
UI Engine - Pygame rendering and event management
"""

import pygame
from typing import Optional, Tuple
import config


class UIEngine:
    """Manages Pygame display and rendering"""

    def __init__(self, width: int = config.SCREEN_WIDTH, height: int = config.SCREEN_HEIGHT):
        """Initialize Pygame and display"""
        pygame.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Convergence Jukebox")

        self.clock = pygame.time.Clock()
        self.running = True
        self.font_cache = {}

    # ========================================================================
    # FONT MANAGEMENT
    # ========================================================================

    def get_font(self, size: int) -> pygame.font.Font:
        """Get cached font or create new one"""
        if size not in self.font_cache:
            try:
                self.font_cache[size] = pygame.font.Font(config.FONT_PATH, size)
            except:
                self.font_cache[size] = pygame.font.Font(None, size)
        return self.font_cache[size]

    # ========================================================================
    # RENDERING PRIMITIVES
    # ========================================================================

    def fill(self, color: Tuple[int, int, int]):
        """Fill screen with color"""
        self.screen.fill(color)

    def draw_rect(self, rect: pygame.Rect, color: Tuple[int, int, int], filled: bool = True, width: int = 0):
        """Draw a rectangle"""
        if filled:
            pygame.draw.rect(self.screen, color, rect)
        else:
            pygame.draw.rect(self.screen, color, rect, width)

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: Tuple[int, int, int] = config.COLOR_WHITE,
        font_size: int = config.FONT_SIZE_SMALL,
        center: bool = False,
        bg_color: Optional[Tuple[int, int, int]] = None
    ) -> pygame.Rect:
        """Draw text and return its rect"""
        font = self.get_font(font_size)
        text_surface = font.render(text, True, color, bg_color)
        text_rect = text_surface.get_rect()

        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)

        self.screen.blit(text_surface, text_rect)
        return text_rect

    def draw_image(
        self,
        image_path: str,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Optional[pygame.Rect]:
        """Load and draw an image"""
        try:
            image = pygame.image.load(image_path)
            if width and height:
                image = pygame.transform.scale(image, (width, height))
            elif width:
                aspect = image.get_height() / image.get_width()
                image = pygame.transform.scale(image, (width, int(width * aspect)))
            elif height:
                aspect = image.get_width() / image.get_height()
                image = pygame.transform.scale(image, (int(height * aspect), height))

            image_rect = image.get_rect(topleft=(x, y))
            self.screen.blit(image, image_rect)
            return image_rect
        except Exception as e:
            print(f"Error drawing image {image_path}: {e}")
            return None

    # ========================================================================
    # TEXT FORMATTING UTILITIES
    # ========================================================================

    @staticmethod
    def calculate_dynamic_font_size(text: str) -> int:
        """Calculate appropriate font size based on text length"""
        text_len = len(text)

        if text_len >= config.TEXT_LENGTH_THRESHOLD_LARGE:
            return config.FONT_SIZE_TINY
        elif text_len >= config.TEXT_LENGTH_THRESHOLD_MEDIUM:
            return config.FONT_SIZE_SMALL
        elif text_len >= config.TEXT_LENGTH_THRESHOLD_SMALL:
            return config.FONT_SIZE_MEDIUM
        elif text_len >= config.TEXT_LENGTH_THRESHOLD_TINY:
            return config.FONT_SIZE_MEDIUM
        else:
            return config.FONT_SIZE_LARGE

    @staticmethod
    def truncate_text(text: str, max_length: int = 22) -> str:
        """Truncate text to maximum length with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    # ========================================================================
    # DISPLAY UPDATE
    # ========================================================================

    def update_display(self):
        """Update the display"""
        pygame.display.flip()

    def get_frame_rate(self) -> int:
        """Get and maintain frame rate"""
        return self.clock.tick(config.FPS)

    def get_delta_time(self) -> float:
        """Get time since last frame in seconds"""
        return self.clock.get_time() / 1000.0

    # ========================================================================
    # EVENT HANDLING
    # ========================================================================

    def get_events(self) -> list:
        """Get all pending events"""
        return pygame.event.get()

    def get_mouse_pos(self) -> Tuple[int, int]:
        """Get mouse position"""
        return pygame.mouse.get_pos()

    def is_mouse_button_pressed(self, button: int = 1) -> bool:
        """Check if mouse button is pressed"""
        return pygame.mouse.get_pressed()[button - 1]

    # ========================================================================
    # KEYBOARD HANDLING
    # ========================================================================

    def get_keys_pressed(self) -> list:
        """Get all currently pressed keys"""
        return pygame.key.get_pressed()

    # ========================================================================
    # UTILITY
    # ========================================================================

    def quit(self):
        """Quit Pygame"""
        pygame.quit()

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions"""
        return (self.width, self.height)

    def get_screen_rect(self) -> pygame.Rect:
        """Get screen rect"""
        return self.screen.get_rect()
