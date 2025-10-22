"""
Control Panel Screen - Mode selection, number pad, and song selection controls
"""

import pygame
from typing import Optional, Callable, List, Dict, Any, Tuple
import config
from components import Button, RowSelector, TextDisplay
from .base_screen import BaseScreen


class ControlPanel(BaseScreen):
    """Control panel for song selection with A/B/C modes and number pad"""

    def __init__(
        self,
        width: int = config.SCREEN_WIDTH,
        height: int = config.SCREEN_HEIGHT,
        on_song_selected_callback: Optional[Callable] = None,
        on_page_changed_callback: Optional[Callable] = None
    ):
        """Initialize control panel"""
        super().__init__(width, height)

        self.on_song_selected_callback = on_song_selected_callback
        self.on_page_changed_callback = on_page_changed_callback

        # Selection state
        self.selected_column: Optional[str] = None  # A, B, C
        self.selected_row: Optional[int] = None      # 1-7
        self.invalid_selection = False
        self.selection_message = ""
        self.message_timeout = 0

        # Layout
        self.panel_margin = 20
        self.column_width = (width - 3 * self.panel_margin) // 3

        # ========== MODE SELECTION (A/B/C) ==========
        mode_y = 50
        mode_button_width = 80
        mode_button_height = 60
        mode_spacing = 20

        mode_x_start = (width - (3 * mode_button_width + 2 * mode_spacing)) // 2

        self.mode_buttons: Dict[str, Button] = {}
        for i, mode in enumerate(['A', 'B', 'C']):
            x = mode_x_start + i * (mode_button_width + mode_spacing)
            btn = Button(
                x, mode_y,
                mode_button_width, mode_button_height,
                text=mode,
                font_size=config.FONT_SIZE_LARGE,
                bg_color=config.COLOR_DARK_GRAY,
                hover_color=(100, 150, 200),
                callback=self._on_mode_select
            )
            self.mode_buttons[mode] = btn

        # ========== NUMBER PAD (1-7) ==========
        pad_y = 150
        pad_x = (width - (3 * 60 + 2 * 10)) // 2
        pad_button_width = 60
        pad_button_height = 60
        pad_spacing = 10

        self.number_buttons: Dict[int, Button] = {}
        # Layout: 1 2 3
        #         4 5 6
        #         7
        numbers = [
            (1, 0), (2, 1), (3, 2),
            (4, 0), (5, 1), (6, 2),
            (7, 0)
        ]

        for num, col in numbers:
            row = (num - 1) // 3
            x = pad_x + col * (pad_button_width + pad_spacing)
            y = pad_y + row * (pad_button_height + pad_spacing)

            btn = Button(
                x, y,
                pad_button_width, pad_button_height,
                text=str(num),
                font_size=config.FONT_SIZE_MEDIUM,
                bg_color=config.COLOR_DARK_GRAY,
                hover_color=(100, 200, 100),
                callback=self._on_number_select
            )
            self.number_buttons[num] = btn

        # ========== CONTROL BUTTONS ==========
        control_y = pad_y + 250
        control_button_width = 100
        control_button_height = 50
        control_spacing = 30

        control_x_start = (width - (2 * control_button_width + control_spacing)) // 2

        self.select_button = Button(
            control_x_start, control_y,
            control_button_width, control_button_height,
            text="SELECT",
            font_size=config.FONT_SIZE_MEDIUM,
            bg_color=(50, 150, 50),
            hover_color=(100, 200, 100),
            callback=self._on_select
        )

        self.correct_button = Button(
            control_x_start + control_button_width + control_spacing, control_y,
            control_button_width, control_button_height,
            text="CORRECT",
            font_size=config.FONT_SIZE_MEDIUM,
            bg_color=(150, 50, 50),
            hover_color=(200, 100, 100),
            callback=self._on_correct
        )

        # ========== DISPLAY AREA ==========
        display_y = 20
        self.mode_display = TextDisplay(
            20, display_y,
            text="Column: --",
            color=config.COLOR_YELLOW,
            font_size=config.FONT_SIZE_MEDIUM
        )

        self.row_display = TextDisplay(
            150, display_y,
            text="Row: --",
            color=config.COLOR_YELLOW,
            font_size=config.FONT_SIZE_MEDIUM
        )

        self.selection_display = TextDisplay(
            width // 2, display_y,
            text="Ready",
            color=config.COLOR_GREEN,
            font_size=config.FONT_SIZE_SMALL,
            center=True
        )

        # Font cache
        self.font_cache: Dict[int, pygame.font.Font] = {}

    def _on_mode_select(self, button: Button):
        """Handle mode button press"""
        for mode, btn in self.mode_buttons.items():
            if btn == button:
                self.selected_column = mode
                self._update_displays()
                break

    def _on_number_select(self, button: Button):
        """Handle number button press"""
        for num, btn in self.number_buttons.items():
            if btn == button:
                if 1 <= num <= 7:
                    self.selected_row = num
                    self._update_displays()
                break

    def _on_select(self, button: Button):
        """Handle select button press"""
        if self.selected_column and self.selected_row:
            # Calculate song index on current page
            col_map = {'A': 0, 'B': 1, 'C': 2}
            col_idx = col_map[self.selected_column]
            row_idx = self.selected_row - 1

            song_index = row_idx * 3 + col_idx

            # Trigger callback with selection
            if self.on_song_selected_callback:
                self.on_song_selected_callback(self.selected_column, self.selected_row, song_index)

            self.selection_message = f"Selected: {self.selected_column}{self.selected_row}"
            self.message_timeout = pygame.time.get_ticks() + 2000  # 2 second message

            # Clear selection
            self.selected_column = None
            self.selected_row = None
            self._update_displays()
        else:
            # Invalid selection
            self.invalid_selection = True
            self.selection_message = "Invalid selection! Choose Column and Row"
            self.message_timeout = pygame.time.get_ticks() + 2000

    def _on_correct(self, button: Button):
        """Handle correct/backspace button press"""
        if self.selected_row:
            self.selected_row = None
        elif self.selected_column:
            self.selected_column = None

        self.invalid_selection = False
        self.selection_message = "Cleared"
        self.message_timeout = pygame.time.get_ticks() + 1000
        self._update_displays()

    def _update_displays(self):
        """Update display texts"""
        col_text = self.selected_column if self.selected_column else "--"
        row_text = str(self.selected_row) if self.selected_row else "--"

        self.mode_display.update_text(f"Column: {col_text}")
        self.row_display.update_text(f"Row: {row_text}")

        if self.selected_column and self.selected_row:
            selection_text = f"{self.selected_column}{self.selected_row}"
            self.selection_display.update_text(selection_text)
            self.selection_display.update_color(config.COLOR_GREEN)
        else:
            self.selection_display.update_text("Ready")
            self.selection_display.update_color(config.COLOR_LIGHT_GRAY)

    def _update_button_states(self):
        """Update button enabled/disabled states"""
        # Mode buttons are always enabled
        for btn in self.mode_buttons.values():
            btn.set_enabled(True)

        # Number buttons are always enabled
        for btn in self.number_buttons.values():
            btn.set_enabled(True)

        # Select button enabled if both column and row are selected
        select_enabled = self.selected_column is not None and self.selected_row is not None
        self.select_button.set_enabled(select_enabled)

        # Correct button enabled if something is selected
        correct_enabled = self.selected_column is not None or self.selected_row is not None
        self.correct_button.set_enabled(correct_enabled)

    def enter(self):
        """Called when screen becomes active"""
        super().enter()
        self.selected_column = None
        self.selected_row = None
        self.invalid_selection = False
        self.selection_message = "Ready"
        self._update_displays()

    def exit(self):
        """Called when screen becomes inactive"""
        super().exit()

    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle pygame events"""
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check mode buttons
            for btn in self.mode_buttons.values():
                if btn.handle_click(mouse_pos):
                    return True

            # Check number buttons
            for btn in self.number_buttons.values():
                if btn.handle_click(mouse_pos):
                    return True

            # Check control buttons
            if self.select_button.handle_click(mouse_pos):
                return True
            if self.correct_button.handle_click(mouse_pos):
                return True

        elif event.type == pygame.MOUSEMOTION:
            for btn in self.mode_buttons.values():
                btn.handle_hover(mouse_pos)

            for btn in self.number_buttons.values():
                btn.handle_hover(mouse_pos)

            self.select_button.handle_hover(mouse_pos)
            self.correct_button.handle_hover(mouse_pos)

        elif event.type == pygame.KEYDOWN:
            # Keyboard shortcuts for modes
            if event.key == pygame.K_a:
                self.selected_column = 'A'
                self._update_displays()
                return True
            elif event.key == pygame.K_b:
                self.selected_column = 'B'
                self._update_displays()
                return True
            elif event.key == pygame.K_c:
                self.selected_column = 'C'
                self._update_displays()
                return True

            # Keyboard shortcuts for rows
            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                            pygame.K_5, pygame.K_6, pygame.K_7]:
                self.selected_row = event.key - pygame.K_0
                self._update_displays()
                return True

            # Select
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._on_select(self.select_button)
                return True

            # Correct
            if event.key == pygame.K_BACKSPACE:
                self._on_correct(self.correct_button)
                return True

        return False

    def update(self, dt: float):
        """Update screen state"""
        if not self.active:
            return

        self._update_button_states()

        # Clear message after timeout
        if self.message_timeout > 0 and pygame.time.get_ticks() > self.message_timeout:
            self.selection_message = ""
            self.message_timeout = 0
            self.invalid_selection = False

    def draw(self, screen: pygame.Surface):
        """Draw screen"""
        screen.fill(config.COLOR_BLACK)

        # Get font getter function
        def get_font(size: int) -> pygame.font.Font:
            if size not in self.font_cache:
                try:
                    self.font_cache[size] = pygame.font.Font(config.FONT_PATH, size)
                except:
                    self.font_cache[size] = pygame.font.Font(None, size)
            return self.font_cache[size]

        # Draw display area
        self.mode_display.draw(screen, get_font)
        self.row_display.draw(screen, get_font)

        # Draw selection message/status
        if self.selection_message:
            msg_color = config.COLOR_RED if self.invalid_selection else config.COLOR_GREEN
            status_display = TextDisplay(
                self.width // 2, 20,
                text=self.selection_message,
                color=msg_color,
                font_size=config.FONT_SIZE_SMALL,
                center=True
            )
            status_display.draw(screen, get_font)
        else:
            self.selection_display.draw(screen, get_font)

        # Draw mode buttons with title
        title = TextDisplay(
            self.width // 2, 10,
            text="SELECT COLUMN (A/B/C)",
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_SMALL,
            center=True
        )
        title.draw(screen, get_font)

        for btn in self.mode_buttons.values():
            btn.draw(screen, get_font)

        # Draw number pad with title
        pad_title = TextDisplay(
            self.width // 2, 130,
            text="SELECT ROW (1-7)",
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_SMALL,
            center=True
        )
        pad_title.draw(screen, get_font)

        for btn in self.number_buttons.values():
            btn.draw(screen, get_font)

        # Draw control buttons
        self.select_button.draw(screen, get_font)
        self.correct_button.draw(screen, get_font)

        # Draw current selection info at bottom
        if self.selected_column or self.selected_row:
            col_text = self.selected_column if self.selected_column else "?"
            row_text = str(self.selected_row) if self.selected_row else "?"
            info_text = f"Current Selection: {col_text}{row_text}"

            info_display = TextDisplay(
                self.width // 2, self.height - 50,
                text=info_text,
                color=config.COLOR_YELLOW,
                font_size=config.FONT_SIZE_MEDIUM,
                center=True
            )
            info_display.draw(screen, get_font)

    def get_selected_column(self) -> Optional[str]:
        """Get selected column"""
        return self.selected_column

    def get_selected_row(self) -> Optional[int]:
        """Get selected row"""
        return self.selected_row

    def clear_selection(self):
        """Clear selection"""
        self.selected_column = None
        self.selected_row = None
        self._update_displays()
