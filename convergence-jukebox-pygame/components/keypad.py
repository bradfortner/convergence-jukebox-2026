"""
Keypad Component - Number and letter keypad for input
"""

import pygame
from typing import Optional, Tuple, Callable, List, Dict
import config
from .button import Button


class Keypad:
    """Keypad component for numeric and alphanumeric input"""

    def __init__(
        self,
        x: int,
        y: int,
        button_width: int = 60,
        button_height: int = 60,
        spacing: int = 5,
        keypad_type: str = "numeric",
        bg_color: Tuple[int, int, int] = config.COLOR_DARK_GRAY,
        text_color: Tuple[int, int, int] = config.COLOR_WHITE,
        font_size: int = config.FONT_SIZE_MEDIUM
    ):
        """
        Initialize keypad

        Args:
            x, y: Position of keypad
            button_width, button_height: Size of each button
            spacing: Spacing between buttons
            keypad_type: 'numeric' (0-9), 'alpha' (A-Z), or 'alphanumeric'
            bg_color: Button background color
            text_color: Text color
            font_size: Font size for buttons
        """
        self.x = x
        self.y = y
        self.button_width = button_width
        self.button_height = button_height
        self.spacing = spacing
        self.keypad_type = keypad_type
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.buttons: Dict[str, Button] = {}
        self.input_buffer = ""

        # Create keypad layout
        self._create_keypad()

    def _create_keypad(self):
        """Create keypad buttons based on type"""
        if self.keypad_type == "numeric":
            self._create_numeric_keypad()
        elif self.keypad_type == "alpha":
            self._create_alpha_keypad()
        elif self.keypad_type == "alphanumeric":
            self._create_alphanumeric_keypad()

    def _create_numeric_keypad(self):
        """Create 0-9 numeric keypad"""
        layout = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["0"]
        ]

        row_idx = 0
        for row in layout:
            col_idx = 0
            for key in row:
                x = self.x + col_idx * (self.button_width + self.spacing)
                y = self.y + row_idx * (self.button_height + self.spacing)

                button = Button(
                    x, y, self.button_width, self.button_height,
                    text=key,
                    bg_color=self.bg_color,
                    text_color=self.text_color,
                    font_size=self.font_size
                )
                self.buttons[key] = button
                col_idx += 1

            row_idx += 1

    def _create_alpha_keypad(self):
        """Create A-Z alphabetic keypad"""
        layout = [
            ["A", "B", "C", "D"],
            ["E", "F", "G", "H"],
            ["I", "J", "K", "L"],
            ["M", "N", "O", "P"],
            ["Q", "R", "S", "T"],
            ["U", "V", "W", "X"],
            ["Y", "Z"]
        ]

        row_idx = 0
        for row in layout:
            col_idx = 0
            for key in row:
                x = self.x + col_idx * (self.button_width + self.spacing)
                y = self.y + row_idx * (self.button_height + self.spacing)

                button = Button(
                    x, y, self.button_width, self.button_height,
                    text=key,
                    bg_color=self.bg_color,
                    text_color=self.text_color,
                    font_size=self.font_size
                )
                self.buttons[key] = button
                col_idx += 1

            row_idx += 1

    def _create_alphanumeric_keypad(self):
        """Create combined 0-9 and A-Z keypad"""
        layout = [
            ["1", "2", "3", "A", "B", "C"],
            ["4", "5", "6", "D", "E", "F"],
            ["7", "8", "9", "G", "H", "I"],
            ["0", "*", "#", "J", "K", "L"]
        ]

        row_idx = 0
        for row in layout:
            col_idx = 0
            for key in row:
                x = self.x + col_idx * (self.button_width + self.spacing)
                y = self.y + row_idx * (self.button_height + self.spacing)

                button = Button(
                    x, y, self.button_width, self.button_height,
                    text=key,
                    bg_color=self.bg_color,
                    text_color=self.text_color,
                    font_size=self.font_size
                )
                self.buttons[key] = button
                col_idx += 1

            row_idx += 1

    def draw(self, screen: pygame.Surface, font_getter: Callable):
        """Draw all keypad buttons"""
        for button in self.buttons.values():
            button.draw(screen, font_getter)

    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle mouse click on keypad

        Returns:
            The key pressed, or None
        """
        for key, button in self.buttons.items():
            if button.handle_click(pos):
                self.input_buffer += key
                return key

        return None

    def handle_hover(self, pos: Tuple[int, int]):
        """Update hover state for all buttons"""
        for button in self.buttons.values():
            button.handle_hover(pos)

    def add_input(self, char: str):
        """Add character to input buffer"""
        if char in self.buttons:
            self.input_buffer += char

    def backspace(self):
        """Remove last character from input buffer"""
        if self.input_buffer:
            self.input_buffer = self.input_buffer[:-1]

    def clear(self):
        """Clear input buffer"""
        self.input_buffer = ""

    def get_input(self) -> str:
        """Get current input buffer"""
        return self.input_buffer

    def set_input(self, text: str):
        """Set input buffer"""
        self.input_buffer = text

    def get_button(self, key: str) -> Optional[Button]:
        """Get button by key"""
        return self.buttons.get(key)

    def get_all_buttons(self) -> List[Button]:
        """Get all buttons"""
        return list(self.buttons.values())

    def enable_key(self, key: str):
        """Enable specific key"""
        if key in self.buttons:
            self.buttons[key].set_enabled(True)

    def disable_key(self, key: str):
        """Disable specific key"""
        if key in self.buttons:
            self.buttons[key].set_enabled(False)

    def enable_all(self):
        """Enable all keys"""
        for button in self.buttons.values():
            button.set_enabled(True)

    def disable_all(self):
        """Disable all keys"""
        for button in self.buttons.values():
            button.set_enabled(False)


class RowSelector:
    """Simple row selector keypad (1-7)"""

    def __init__(
        self,
        x: int,
        y: int,
        rows: int = 7,
        button_width: int = 50,
        button_height: int = 50,
        spacing: int = 5,
        bg_color: Tuple[int, int, int] = config.COLOR_DARK_GRAY,
        text_color: Tuple[int, int, int] = config.COLOR_WHITE,
        font_size: int = config.FONT_SIZE_MEDIUM
    ):
        """Initialize row selector"""
        self.x = x
        self.y = y
        self.rows = rows
        self.button_width = button_width
        self.button_height = button_height
        self.spacing = spacing
        self.bg_color = bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.buttons: Dict[int, Button] = {}
        self.selected_row: Optional[int] = None

        # Create row buttons
        for i in range(1, rows + 1):
            x_pos = x + (i - 1) * (button_width + spacing)
            button = Button(
                x_pos, y, button_width, button_height,
                text=str(i),
                bg_color=bg_color,
                text_color=text_color,
                font_size=font_size
            )
            self.buttons[i] = button

    def draw(self, screen: pygame.Surface, font_getter: Callable):
        """Draw all row selector buttons"""
        for button in self.buttons.values():
            button.draw(screen, font_getter)

    def handle_click(self, pos: Tuple[int, int]) -> Optional[int]:
        """Handle click and return selected row (1-based)"""
        for row_num, button in self.buttons.items():
            if button.handle_click(pos):
                self.selected_row = row_num
                return row_num

        return None

    def handle_hover(self, pos: Tuple[int, int]):
        """Update hover state"""
        for button in self.buttons.values():
            button.handle_hover(pos)

    def get_selected_row(self) -> Optional[int]:
        """Get currently selected row"""
        return self.selected_row

    def set_selected_row(self, row: int):
        """Set selected row"""
        if 1 <= row <= self.rows:
            self.selected_row = row

    def clear_selection(self):
        """Clear selection"""
        self.selected_row = None
