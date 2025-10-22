"""
Button Component - Reusable button widget for UI
"""

import pygame
from typing import Optional, Tuple, Callable, List
import config


class Button:
    """Reusable button component with hover states and callbacks"""

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
        callback: Optional[Callable] = None,
        key: str = "",
        border_color: Tuple[int, int, int] = config.COLOR_WHITE,
        border_width: int = 2,
        hover_color: Tuple[int, int, int] = (200, 100, 100),
        disabled_color: Tuple[int, int, int] = (100, 100, 100)
    ):
        """Initialize button with position, size, and styling"""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.image_path = image_path
        self.image = None
        self.callback = callback
        self.key = key
        self.border_color = border_color
        self.border_width = border_width
        self.hover_color = hover_color
        self.disabled_color = disabled_color

        self.enabled = True
        self.hovered = False
        self.pressed = False
        self.focused = False
        self.font_cache = None

        if image_path:
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (width, height))
            except Exception as e:
                print(f"Warning: Could not load image {image_path}: {e}")

    def draw(self, screen: pygame.Surface, font_getter: Optional[Callable] = None):
        """Draw button on screen with proper styling"""
        # Determine button color based on state
        if not self.enabled:
            current_color = self.disabled_color
        else:
            current_color = self.hover_color if self.hovered else self.bg_color

        # Draw background
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, current_color, self.rect)
            # Draw focus border if focused
            if self.focused:
                pygame.draw.rect(screen, (0, 255, 0), self.rect, 4)
            else:
                pygame.draw.rect(screen, self.border_color, self.rect, self.border_width)

        # Draw text if provided
        if self.text and font_getter:
            font = font_getter(self.font_size)
            text_surface = font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            screen.blit(text_surface, text_rect)

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click on button"""
        if self.rect.collidepoint(pos) and self.enabled:
            if self.callback:
                self.callback(self)
            self.pressed = True
            return True
        return False

    def handle_release(self):
        """Handle mouse button release"""
        self.pressed = False

    def handle_hover(self, pos: Tuple[int, int]):
        """Update hover state based on mouse position"""
        self.hovered = self.rect.collidepoint(pos) and self.enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable button"""
        self.enabled = enabled

    def update_text(self, text: str):
        """Update button text"""
        self.text = text

    def update_position(self, x: int, y: int):
        """Update button position"""
        self.rect.x = x
        self.rect.y = y

    def update_color(self, bg_color: Tuple[int, int, int], text_color: Optional[Tuple[int, int, int]] = None):
        """Update button colors"""
        self.bg_color = bg_color
        if text_color:
            self.text_color = text_color

    def set_callback(self, callback: Callable):
        """Set button callback function"""
        self.callback = callback

    def get_rect(self) -> pygame.Rect:
        """Get button rectangle"""
        return self.rect

    def is_hovered(self) -> bool:
        """Check if button is currently hovered"""
        return self.hovered

    def is_pressed(self) -> bool:
        """Check if button is currently pressed"""
        return self.pressed

    def set_focused(self, focused: bool):
        """Set button focused state"""
        self.focused = focused

    def is_focused(self) -> bool:
        """Check if button is currently focused"""
        return self.focused


class ButtonGrid:
    """Grid of buttons for layout (e.g., song selection grid)"""

    def __init__(
        self,
        x: int,
        y: int,
        cols: int,
        rows: int,
        button_width: int,
        button_height: int,
        spacing: int = 5,
        bg_color: Tuple[int, int, int] = config.COLOR_DARK_GRAY,
        text_color: Tuple[int, int, int] = config.COLOR_WHITE,
        font_size: int = config.FONT_SIZE_SMALL
    ):
        """Initialize button grid"""
        self.x = x
        self.y = y
        self.cols = cols
        self.rows = rows
        self.button_width = button_width
        self.button_height = button_height
        self.spacing = spacing
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.buttons: List[Button] = []
        self.focused_index = 0  # Track which button has focus

        # Create grid of buttons
        for row in range(rows):
            for col in range(cols):
                bx = x + col * (button_width + spacing)
                by = y + row * (button_height + spacing)
                button = Button(
                    bx, by, button_width, button_height,
                    bg_color=bg_color,
                    text_color=text_color,
                    font_size=font_size
                )
                self.buttons.append(button)

        # Set initial focus on first enabled button
        if self.buttons:
            self.buttons[0].set_focused(True)

    def draw(self, screen: pygame.Surface, font_getter: Optional[Callable] = None):
        """Draw all buttons in grid"""
        for button in self.buttons:
            button.draw(screen, font_getter)

    def handle_click(self, pos: Tuple[int, int]) -> Optional[Button]:
        """Handle click and return clicked button"""
        for button in self.buttons:
            if button.handle_click(pos):
                return button
        return None

    def handle_hover(self, pos: Tuple[int, int]):
        """Update hover state for all buttons"""
        for button in self.buttons:
            button.handle_hover(pos)

    def set_button_text(self, index: int, text: str):
        """Set text for a specific button"""
        if 0 <= index < len(self.buttons):
            self.buttons[index].update_text(text)

    def get_button_text(self, index: int) -> str:
        """Get text for a specific button"""
        if 0 <= index < len(self.buttons):
            return self.buttons[index].text
        return ""

    def enable_buttons(self, indices: List[int]):
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

    def get_all_buttons(self) -> List[Button]:
        """Get all buttons"""
        return self.buttons

    def clear(self):
        """Clear all buttons"""
        self.buttons.clear()

    def get_grid_rect(self) -> pygame.Rect:
        """Get the bounding rectangle of the entire grid"""
        if not self.buttons:
            return pygame.Rect(self.x, self.y, 0, 0)

        min_x = min(btn.rect.x for btn in self.buttons)
        min_y = min(btn.rect.y for btn in self.buttons)
        max_x = max(btn.rect.right for btn in self.buttons)
        max_y = max(btn.rect.bottom for btn in self.buttons)

        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def move_focus_right(self):
        """Move focus to the right"""
        if not self.buttons:
            return

        current_row = self.focused_index // self.cols
        current_col = self.focused_index % self.cols

        # Try to move right
        if current_col < self.cols - 1:
            next_index = self.focused_index + 1
            if next_index < len(self.buttons):
                self._set_focused_index(next_index)

    def move_focus_left(self):
        """Move focus to the left"""
        if not self.buttons:
            return

        current_col = self.focused_index % self.cols

        # Try to move left
        if current_col > 0:
            next_index = self.focused_index - 1
            self._set_focused_index(next_index)

    def move_focus_down(self):
        """Move focus down"""
        if not self.buttons:
            return

        current_row = self.focused_index // self.cols
        current_col = self.focused_index % self.cols

        # Try to move down
        if current_row < self.rows - 1:
            next_index = self.focused_index + self.cols
            if next_index < len(self.buttons):
                self._set_focused_index(next_index)

    def move_focus_up(self):
        """Move focus up"""
        if not self.buttons:
            return

        current_row = self.focused_index // self.cols
        current_col = self.focused_index % self.cols

        # Try to move up
        if current_row > 0:
            next_index = self.focused_index - self.cols
            self._set_focused_index(next_index)

    def _set_focused_index(self, index: int):
        """Set focused button by index"""
        if not self.buttons or index < 0 or index >= len(self.buttons):
            return

        # Clear old focus
        if self.focused_index < len(self.buttons):
            self.buttons[self.focused_index].set_focused(False)

        # Set new focus
        self.focused_index = index
        self.buttons[self.focused_index].set_focused(True)

    def set_focused_index(self, index: int):
        """Publicly set focused button by index"""
        self._set_focused_index(index)

    def get_focused_button(self) -> Optional[Button]:
        """Get the currently focused button"""
        if 0 <= self.focused_index < len(self.buttons):
            return self.buttons[self.focused_index]
        return None

    def get_focused_index(self) -> int:
        """Get the index of the focused button"""
        return self.focused_index

    def activate_focused_button(self):
        """Activate (click) the currently focused button"""
        button = self.get_focused_button()
        if button and button.enabled:
            if button.callback:
                button.callback(button)
            return True
        return False
