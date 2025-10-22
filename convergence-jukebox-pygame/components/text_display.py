"""
Text Display Component - Advanced text rendering with formatting
"""

import pygame
from typing import Optional, Tuple, Callable, List
import config


class TextDisplay:
    """Component for rendering text with various formatting options"""

    def __init__(
        self,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
        text: str = "",
        color: Tuple[int, int, int] = config.COLOR_WHITE,
        font_size: int = config.FONT_SIZE_MEDIUM,
        bg_color: Optional[Tuple[int, int, int]] = None,
        center: bool = False,
        max_width: Optional[int] = None,
        line_spacing: int = 5
    ):
        """Initialize text display component"""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.font_size = font_size
        self.bg_color = bg_color
        self.center = center
        self.max_width = max_width
        self.line_spacing = line_spacing
        self.visible = True
        self.rect = pygame.Rect(x, y, width or 0, height or 0)

    def draw(self, screen: pygame.Surface, font_getter: Callable):
        """Draw text on screen"""
        if not self.visible or not self.text:
            return

        font = font_getter(self.font_size)
        text_surface = font.render(self.text, True, self.color, self.bg_color)

        if self.center:
            text_rect = text_surface.get_rect(center=(self.x, self.y))
        else:
            text_rect = text_surface.get_rect(topleft=(self.x, self.y))

        self.rect = text_rect
        screen.blit(text_surface, text_rect)

    def draw_multiline(self, screen: pygame.Surface, font_getter: Callable):
        """Draw multi-line text with wrapping"""
        if not self.visible or not self.text:
            return

        font = font_getter(self.font_size)
        lines = self.wrap_text(self.text, font)

        current_y = self.y
        start_rect = None

        for line in lines:
            text_surface = font.render(line, True, self.color, self.bg_color)

            if self.center:
                text_rect = text_surface.get_rect(center=(self.x, current_y))
            else:
                text_rect = text_surface.get_rect(topleft=(self.x, current_y))

            if start_rect is None:
                start_rect = text_rect
            else:
                start_rect = start_rect.union(text_rect)

            screen.blit(text_surface, text_rect)
            current_y += text_surface.get_height() + self.line_spacing

        self.rect = start_rect or pygame.Rect(self.x, self.y, 0, 0)

    def wrap_text(self, text: str, font: pygame.font.Font, max_width: Optional[int] = None) -> List[str]:
        """Wrap text to fit within maximum width"""
        max_w = max_width or self.max_width
        if not max_w:
            return [text]

        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            text_width = font.size(test_line)[0]

            if text_width > max_w:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test_line

        if current_line:
            lines.append(current_line)

        return lines

    def update_text(self, text: str):
        """Update displayed text"""
        self.text = text

    def update_position(self, x: int, y: int):
        """Update text position"""
        self.x = x
        self.y = y

    def update_color(self, color: Tuple[int, int, int]):
        """Update text color"""
        self.color = color

    def update_font_size(self, font_size: int):
        """Update font size"""
        self.font_size = font_size

    def set_visible(self, visible: bool):
        """Set text visibility"""
        self.visible = visible

    def get_text(self) -> str:
        """Get current text"""
        return self.text

    def get_rect(self) -> pygame.Rect:
        """Get text bounding rectangle"""
        return self.rect

    def truncate_text(self, text: str, max_length: int = 22) -> str:
        """Truncate text to maximum length with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def calculate_dynamic_font_size(self, text: str) -> int:
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


class Label(TextDisplay):
    """Simple label component (extends TextDisplay)"""

    def __init__(
        self,
        x: int,
        y: int,
        text: str = "",
        color: Tuple[int, int, int] = config.COLOR_WHITE,
        font_size: int = config.FONT_SIZE_SMALL,
        center: bool = False
    ):
        """Initialize label"""
        super().__init__(x, y, text=text, color=color, font_size=font_size, center=center)


class Title(TextDisplay):
    """Title component with larger font (extends TextDisplay)"""

    def __init__(
        self,
        x: int,
        y: int,
        text: str = "",
        color: Tuple[int, int, int] = config.COLOR_WHITE
    ):
        """Initialize title"""
        super().__init__(x, y, text=text, color=color, font_size=config.FONT_SIZE_LARGE, center=True)
