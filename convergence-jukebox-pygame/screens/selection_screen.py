"""
Selection Screen - Main song selection with 3x7 grid display
"""

import pygame
from typing import Optional, Callable, List, Dict, Any
import config
from components import Button, ButtonGrid, TextDisplay, RowSelector
from .base_screen import BaseScreen


class SelectionScreen(BaseScreen):
    """Main song selection screen with 21-button grid (3 columns x 7 rows)"""

    def __init__(
        self,
        width: int = config.SCREEN_WIDTH,
        height: int = config.SCREEN_HEIGHT,
        get_songs_callback: Optional[Callable] = None,
        get_band_name_callback: Optional[Callable] = None
    ):
        """Initialize selection screen"""
        super().__init__(width, height)

        self.get_songs_callback = get_songs_callback
        self.get_band_name_callback = get_band_name_callback

        # Grid configuration
        self.grid_cols = 3
        self.grid_rows = 7
        self.button_width = 200
        self.button_height = 80
        self.button_spacing = 10

        # Calculate grid position (centered)
        grid_total_width = (
            self.grid_cols * self.button_width +
            (self.grid_cols - 1) * self.button_spacing
        )
        self.grid_x = (width - grid_total_width) // 2
        self.grid_y = 120

        # Create button grid
        self.button_grid = ButtonGrid(
            self.grid_x,
            self.grid_y,
            self.grid_cols,
            self.grid_rows,
            self.button_width,
            self.button_height,
            spacing=self.button_spacing,
            bg_color=config.COLOR_DARK_GRAY,
            text_color=config.COLOR_WHITE,
            font_size=config.FONT_SIZE_SMALL
        )

        # Pagination controls
        self.arrow_width = 60
        self.arrow_height = 60
        self.prev_button = Button(
            20, (height - self.arrow_height) // 2,
            self.arrow_width, self.arrow_height,
            text="◄", font_size=config.FONT_SIZE_LARGE,
            callback=self._on_prev_page
        )
        self.next_button = Button(
            width - self.arrow_width - 20, (height - self.arrow_height) // 2,
            self.arrow_width, self.arrow_height,
            text="►", font_size=config.FONT_SIZE_LARGE,
            callback=self._on_next_page
        )

        # Title display
        self.title_display = TextDisplay(
            width // 2, 30,
            text="Song Selection",
            color=config.COLOR_WHITE,
            font_size=config.FONT_SIZE_LARGE,
            center=True
        )

        # Page info display
        self.page_info_display = TextDisplay(
            width // 2, height - 40,
            text="Page 1 of 1",
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_TINY,
            center=True
        )

        # Row selector (1-7)
        self.row_selector = RowSelector(
            self.grid_x - 80, self.grid_y,
            rows=7,
            button_width=40,
            button_height=40,
            spacing=self.button_spacing
        )

        # Column selector (A, B, C)
        self.col_buttons = {}
        col_y = self.grid_y - 70
        col_labels = ["A", "B", "C"]
        for i, label in enumerate(col_labels):
            col_x = self.grid_x + i * (self.button_width + self.button_spacing)
            btn = Button(
                col_x, col_y,
                self.button_width, 50,
                text=label,
                font_size=config.FONT_SIZE_LARGE,
                callback=self._on_column_select
            )
            self.col_buttons[label] = btn

        # State
        self.current_page = 0
        self.total_pages = 1
        self.all_songs: List[Dict[str, Any]] = []
        self.current_page_songs: List[Dict[str, Any]] = []
        self.selected_column: Optional[str] = None
        self.selected_row: Optional[int] = None
        self.font_cache: Dict[int, pygame.font.Font] = {}

    def _get_songs(self):
        """Fetch songs from callback"""
        if self.get_songs_callback:
            self.all_songs = self.get_songs_callback()
            self._update_pagination()

    def _update_pagination(self):
        """Update pagination and current page songs"""
        if not self.all_songs:
            self.total_pages = 1
            self.current_page_songs = []
            return

        songs_per_page = self.grid_cols * self.grid_rows
        self.total_pages = (len(self.all_songs) + songs_per_page - 1) // songs_per_page

        # Clamp current page
        self.current_page = min(self.current_page, self.total_pages - 1)
        self.current_page = max(0, self.current_page)

        # Get songs for current page
        start_idx = self.current_page * songs_per_page
        end_idx = start_idx + songs_per_page
        self.current_page_songs = self.all_songs[start_idx:end_idx]

        # Update button grid with songs
        for idx, button in enumerate(self.button_grid.get_all_buttons()):
            if idx < len(self.current_page_songs):
                song = self.current_page_songs[idx]
                display_name = self._format_song_name(song)
                button.update_text(display_name)
                button.set_enabled(True)
            else:
                button.update_text("")
                button.set_enabled(False)

        # Update page info
        page_text = f"Page {self.current_page + 1} of {self.total_pages}"
        self.page_info_display.update_text(page_text)

        # Update arrow button states
        self.prev_button.set_enabled(self.current_page > 0)
        self.next_button.set_enabled(self.current_page < self.total_pages - 1)

    def _format_song_name(self, song: Dict[str, Any]) -> str:
        """Format song name with band name processing"""
        title = song.get('title', 'Unknown')
        artist = song.get('artist', 'Unknown')

        # Apply band name processing if available
        if self.get_band_name_callback:
            artist = self.get_band_name_callback(artist)

        # Combine and truncate
        display_name = f"{artist}\n{title}"
        return display_name

    def _on_prev_page(self, button: Button):
        """Handle previous page button"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_pagination()

    def _on_next_page(self, button: Button):
        """Handle next page button"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_pagination()

    def _on_column_select(self, button: Button):
        """Handle column selection"""
        for label, btn in self.col_buttons.items():
            if btn == button:
                self.selected_column = label
                break

    def _on_song_select(self, button: Button):
        """Handle song selection from grid"""
        # Find which button was clicked
        button_idx = self.button_grid.get_all_buttons().index(button)
        if button_idx < len(self.current_page_songs):
            song = self.current_page_songs[button_idx]
            self.state['selected_song'] = song
            self.state['selection_time'] = pygame.time.get_ticks()

    def enter(self):
        """Called when screen becomes active"""
        super().enter()
        self._get_songs()

    def exit(self):
        """Called when screen becomes inactive"""
        super().exit()

    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle pygame events"""
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check pagination buttons
            if self.prev_button.handle_click(mouse_pos):
                return True
            if self.next_button.handle_click(mouse_pos):
                return True

            # Check column buttons
            for btn in self.col_buttons.values():
                if btn.handle_click(mouse_pos):
                    return True

            # Check row selector
            if self.row_selector.handle_click(mouse_pos):
                return True

            # Check grid buttons
            clicked_button = self.button_grid.handle_click(mouse_pos)
            if clicked_button:
                self._on_song_select(clicked_button)
                return True

        elif event.type == pygame.MOUSEMOTION:
            # Update hover states
            self.prev_button.handle_hover(mouse_pos)
            self.next_button.handle_hover(mouse_pos)

            for btn in self.col_buttons.values():
                btn.handle_hover(mouse_pos)

            self.button_grid.handle_hover(mouse_pos)
            self.row_selector.handle_hover(mouse_pos)

        elif event.type == pygame.KEYDOWN:
            # Keyboard shortcuts
            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                            pygame.K_5, pygame.K_6, pygame.K_7]:
                row_num = event.key - pygame.K_0
                self.selected_row = row_num
                return True

            if event.key == pygame.K_a:
                self.selected_column = "A"
                self.col_buttons["A"].handle_click((0, 0))
                return True
            elif event.key == pygame.K_b:
                self.selected_column = "B"
                self.col_buttons["B"].handle_click((0, 0))
                return True
            elif event.key == pygame.K_c:
                self.selected_column = "C"
                self.col_buttons["C"].handle_click((0, 0))
                return True

            if event.key == pygame.K_LEFT:
                self.prev_button.handle_click((0, 0))
                return True
            elif event.key == pygame.K_RIGHT:
                self.next_button.handle_click((0, 0))
                return True

        return False

    def update(self, dt: float):
        """Update screen state"""
        if not self.active:
            return

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

        # Draw title
        self.title_display.draw(screen, get_font)

        # Draw column labels
        for btn in self.col_buttons.values():
            btn.draw(screen, get_font)

        # Draw row selector
        self.row_selector.draw(screen, get_font)

        # Draw grid
        self.button_grid.draw(screen, get_font)

        # Draw pagination buttons
        self.prev_button.draw(screen, get_font)
        self.next_button.draw(screen, get_font)

        # Draw page info
        self.page_info_display.draw(screen, get_font)

        # Draw selection info if available
        if self.selected_column and self.selected_row:
            selection_text = f"Selected: {self.selected_column}{self.selected_row}"
            selection_display = TextDisplay(
                20, config.SCREEN_HEIGHT - 70,
                text=selection_text,
                color=config.COLOR_GREEN,
                font_size=config.FONT_SIZE_SMALL
            )
            selection_display.draw(screen, get_font)

    def get_selected_song(self) -> Optional[Dict[str, Any]]:
        """Get currently selected song"""
        return self.state.get('selected_song')

    def set_songs(self, songs: List[Dict[str, Any]]):
        """Directly set songs"""
        self.all_songs = songs
        self._update_pagination()

    def get_current_page(self) -> int:
        """Get current page number (0-indexed)"""
        return self.current_page

    def get_total_pages(self) -> int:
        """Get total number of pages"""
        return self.total_pages

    def go_to_page(self, page: int):
        """Go to specific page"""
        if 0 <= page < self.total_pages:
            self.current_page = page
            self._update_pagination()

    def get_selected_column(self) -> Optional[str]:
        """Get selected column (A, B, or C)"""
        return self.selected_column

    def get_selected_row(self) -> Optional[int]:
        """Get selected row (1-7)"""
        return self.selected_row
