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

    def get_keys_pressed(self) -> pygame.key.ScalarKeyType:
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


class Button:
    """Reusable button component"""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str = "",
        bg_color: Tuple[int, int, int] = config.COLOR_DARK_GRAY,
        text_color: Tuple[int, int, int] = config.COLOR_WHITE,
        font_size: int = config.FONT_SIZE_SMALL,
        image_path: Optional[str] = None,
        callback=None,
        key: str = ""
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.image_path = image_path
        self.image = None
        self.callback = callback
        self.key = key
        self.enabled = True
        self.hovered = False
        self.pressed = False

        if image_path:
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (width, height))
            except:
                pass

    def draw(self, ui_engine: UIEngine):
        """Draw button"""
        if not self.enabled:
            # Draw disabled state
            color = (100, 100, 100)
        else:
            color = (200, 100, 100) if self.hovered else self.bg_color

        if self.image:
            ui_engine.screen.blit(self.image, self.rect)
        else:
            ui_engine.draw_rect(self.rect, color, filled=True)
            pygame.draw.rect(ui_engine.screen, config.COLOR_WHITE, self.rect, 2)

        # Draw text with dynamic sizing
        if self.text:
            font_size = ui_engine.calculate_dynamic_font_size(self.text)
            text = ui_engine.truncate_text(self.text)

            text_rect = ui_engine.draw_text(
                text,
                self.rect.centerx,
                self.rect.centery,
                color=self.text_color,
                font_size=font_size,
                center=True
            )

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click"""
        if self.rect.collidepoint(pos) and self.enabled:
            if self.callback:
                self.callback(self)
            return True
        return False

    def handle_hover(self, pos: Tuple[int, int]):
        """Handle mouse hover"""
        self.hovered = self.rect.collidepoint(pos) and self.enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable button"""
        self.enabled = enabled

    def update_text(self, text: str):
        """Update button text"""
        self.text = text


class ButtonGrid:
    """Grid of buttons (for song display)"""

    def __init__(self, x: int, y: int, cols: int, rows: int, button_width: int, button_height: int, spacing: int = 5):
        self.x = x
        self.y = y
        self.cols = cols
        self.rows = rows
        self.button_width = button_width
        self.button_height = button_height
        self.spacing = spacing
        self.buttons = []

        # Create grid of buttons
        for row in range(rows):
            for col in range(cols):
                bx = x + col * (button_width + spacing)
                by = y + row * (button_height + spacing)
                button = Button(bx, by, button_width, button_height)
                self.buttons.append(button)

    def draw(self, ui_engine: UIEngine):
        """Draw all buttons"""
        for button in self.buttons:
            button.draw(ui_engine)

    def handle_click(self, pos: Tuple[int, int]) -> Optional[Button]:
        """Handle click and return clicked button"""
        for button in self.buttons:
            if button.handle_click(pos):
                return button
        return None

    def handle_hover(self, pos: Tuple[int, int]):
        """Handle hover for all buttons"""
        for button in self.buttons:
            button.handle_hover(pos)

    def set_button_text(self, index: int, text: str):
        """Set text for a specific button"""
        if 0 <= index < len(self.buttons):
            self.buttons[index].update_text(text)

    def enable_buttons(self, indices: list):
        """Enable specific buttons by index"""
        for i, button in enumerate(self.buttons):
            button.set_enabled(i in indices)

    def enable_all(self):
        """Enable all buttons"""
        for button in self.buttons:
            button.set_enabled(True)

    def disable_all(self):
        """Disable all buttons"""
        for button in self.buttons:
            button.set_enabled(False)

    def get_button(self, index: int) -> Optional[Button]:
        """Get button by index"""
        if 0 <= index < len(self.buttons):
            return self.buttons[index]
        return None
