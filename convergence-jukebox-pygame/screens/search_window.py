"""
Search Window - Modal search interface with keypad input and result display
"""

import pygame
from typing import Optional, Callable, List, Dict, Any
import config
from components import Button, Keypad, TextDisplay
from .base_screen import BaseScreen


class SearchWindow(BaseScreen):
    """Modal search window overlay for finding songs"""

    def __init__(
        self,
        width: int = config.SCREEN_WIDTH,
        height: int = config.SCREEN_HEIGHT,
        get_all_songs_callback: Optional[Callable] = None,
        get_band_name_callback: Optional[Callable] = None,
        on_song_selected_callback: Optional[Callable] = None
    ):
        """Initialize search window"""
        super().__init__(width, height)

        self.get_all_songs_callback = get_all_songs_callback
        self.get_band_name_callback = get_band_name_callback
        self.on_song_selected_callback = on_song_selected_callback

        # All songs list
        self.all_songs: List[Dict[str, Any]] = []

        # Search state
        self.search_input = ""
        self.search_results: List[Dict[str, Any]] = []
        self.results_per_page = 5
        self.current_result_page = 0
        self.selected_result_index = 0

        # Modal dimensions
        self.modal_width = int(width * 0.8)
        self.modal_height = int(height * 0.8)
        self.modal_x = (width - self.modal_width) // 2
        self.modal_y = (height - self.modal_height) // 2

        # Search input display
        self.search_input_display = TextDisplay(
            self.modal_x + 20, self.modal_y + 20,
            text="Search: ",
            color=config.COLOR_YELLOW,
            font_size=config.FONT_SIZE_MEDIUM
        )

        # Search input box
        self.input_box_rect = pygame.Rect(
            self.modal_x + 20, self.modal_y + 50,
            self.modal_width - 40, 40
        )

        # Keypad (alphanumeric)
        keypad_x = self.modal_x + 20
        keypad_y = self.modal_y + 110
        self.keypad = Keypad(
            keypad_x, keypad_y,
            button_width=50,
            button_height=40,
            spacing=5,
            keypad_type="alphanumeric",
            font_size=config.FONT_SIZE_SMALL
        )

        # Results display area
        results_y = self.modal_y + 300
        self.results_title = TextDisplay(
            self.modal_x + 20, results_y,
            text="Search Results:",
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_MEDIUM
        )

        # Result item displays
        self.result_items: List[TextDisplay] = []
        for i in range(self.results_per_page):
            item_y = results_y + 40 + i * 35
            item = TextDisplay(
                self.modal_x + 30, item_y,
                text="",
                color=config.COLOR_WHITE,
                font_size=config.FONT_SIZE_SMALL,
                max_width=self.modal_width - 80
            )
            self.result_items.append(item)

        # Navigation buttons
        button_y = results_y + 40 + self.results_per_page * 35 + 10
        button_width = 80
        button_height = 40
        button_spacing = 20

        button_x_start = (self.modal_width - (4 * button_width + 3 * button_spacing)) // 2 + self.modal_x

        self.prev_button = Button(
            button_x_start, button_y,
            button_width, button_height,
            text="<< Prev",
            font_size=config.FONT_SIZE_SMALL,
            callback=self._on_prev_results
        )

        self.next_button = Button(
            button_x_start + button_width + button_spacing, button_y,
            button_width, button_height,
            text="Next >>",
            font_size=config.FONT_SIZE_SMALL,
            callback=self._on_next_results
        )

        self.select_button = Button(
            button_x_start + 2 * (button_width + button_spacing), button_y,
            button_width, button_height,
            text="Select",
            font_size=config.FONT_SIZE_SMALL,
            bg_color=(50, 150, 50),
            callback=self._on_select_result
        )

        self.close_button = Button(
            button_x_start + 3 * (button_width + button_spacing), button_y,
            button_width, button_height,
            text="Close",
            font_size=config.FONT_SIZE_SMALL,
            bg_color=(150, 50, 50),
            callback=self._on_close
        )

        # Control buttons
        control_button_width = 100
        control_button_height = 40
        control_y = self.modal_y + self.modal_height - 60

        self.backspace_button = Button(
            self.modal_x + 20, control_y,
            control_button_width, control_button_height,
            text="Backspace",
            font_size=config.FONT_SIZE_SMALL,
            bg_color=(150, 100, 50),
            callback=self._on_backspace
        )

        self.clear_button = Button(
            self.modal_x + 20 + control_button_width + 10, control_y,
            control_button_width, control_button_height,
            text="Clear",
            font_size=config.FONT_SIZE_SMALL,
            bg_color=(150, 100, 50),
            callback=self._on_clear
        )

        # Status info
        self.status_display = TextDisplay(
            self.modal_x + self.modal_width - 200, control_y,
            text="",
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_SMALL
        )

        # Font cache
        self.font_cache: Dict[int, pygame.font.Font] = {}

    def _load_all_songs(self):
        """Load all songs from callback"""
        if self.get_all_songs_callback:
            self.all_songs = self.get_all_songs_callback()

    def _perform_search(self):
        """Perform search based on current input"""
        if not self.search_input:
            self.search_results = []
            self.current_result_page = 0
            self.selected_result_index = 0
            return

        search_term = self.search_input.lower()
        self.search_results = []

        for song in self.all_songs:
            title = song.get('title', '').lower()
            artist = song.get('artist', '').lower()

            # Match if search term is in title or artist
            if search_term in title or search_term in artist:
                self.search_results.append(song)

        # Reset to first page
        self.current_result_page = 0
        self.selected_result_index = 0
        self._update_result_display()

    def _update_result_display(self):
        """Update displayed results"""
        start_idx = self.current_result_page * self.results_per_page
        end_idx = start_idx + self.results_per_page
        page_results = self.search_results[start_idx:end_idx]

        for i, item_display in enumerate(self.result_items):
            if i < len(page_results):
                song = page_results[i]
                artist = song.get('artist', 'Unknown')
                if self.get_band_name_callback:
                    artist = self.get_band_name_callback(artist)

                title = song.get('title', 'Unknown')
                display_text = f"{i+1}. {artist} - {title}"

                # Truncate if too long
                if len(display_text) > 60:
                    display_text = display_text[:57] + "..."

                item_display.update_text(display_text)
                item_display.set_visible(True)
            else:
                item_display.set_visible(False)

        # Update navigation buttons
        total_pages = (len(self.search_results) + self.results_per_page - 1) // self.results_per_page
        self.prev_button.set_enabled(self.current_result_page > 0)
        self.next_button.set_enabled(self.current_result_page < total_pages - 1)
        self.select_button.set_enabled(len(page_results) > 0)

        # Update status
        if self.search_results:
            status = f"{len(self.search_results)} results | Page {self.current_result_page + 1}/{total_pages}"
        else:
            status = "No results"
        self.status_display.update_text(status)

    def _on_prev_results(self, button: Button):
        """Handle previous results page"""
        if self.current_result_page > 0:
            self.current_result_page -= 1
            self._update_result_display()

    def _on_next_results(self, button: Button):
        """Handle next results page"""
        total_pages = (len(self.search_results) + self.results_per_page - 1) // self.results_per_page
        if self.current_result_page < total_pages - 1:
            self.current_result_page += 1
            self._update_result_display()

    def _on_select_result(self, button: Button):
        """Handle selecting a result"""
        start_idx = self.current_result_page * self.results_per_page
        idx = start_idx + self.selected_result_index

        if idx < len(self.search_results):
            song = self.search_results[idx]
            if self.on_song_selected_callback:
                self.on_song_selected_callback(song)

            self.state['song_selected'] = True

    def _on_close(self, button: Button):
        """Handle close button"""
        self.state['close_pressed'] = True

    def _on_backspace(self, button: Button):
        """Handle backspace"""
        self.keypad.backspace()
        self.search_input = self.keypad.get_input()
        self._perform_search()

    def _on_clear(self, button: Button):
        """Handle clear"""
        self.keypad.clear()
        self.search_input = ""
        self.search_results = []
        self.current_result_page = 0
        self._update_result_display()

    def enter(self):
        """Called when window becomes active"""
        super().enter()
        self._load_all_songs()
        self.search_input = ""
        self.search_results = []
        self.keypad.clear()
        self.current_result_page = 0
        self._update_result_display()

    def exit(self):
        """Called when window becomes inactive"""
        super().exit()

    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle pygame events"""
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check keypad buttons
            key_pressed = self.keypad.handle_click(mouse_pos)
            if key_pressed:
                self.search_input = self.keypad.get_input()
                self._perform_search()
                return True

            # Check navigation buttons
            if self.prev_button.handle_click(mouse_pos):
                return True
            if self.next_button.handle_click(mouse_pos):
                return True
            if self.select_button.handle_click(mouse_pos):
                return True
            if self.close_button.handle_click(mouse_pos):
                return True

            # Check control buttons
            if self.backspace_button.handle_click(mouse_pos):
                return True
            if self.clear_button.handle_click(mouse_pos):
                return True

        elif event.type == pygame.MOUSEMOTION:
            self.keypad.handle_hover(mouse_pos)
            self.prev_button.handle_hover(mouse_pos)
            self.next_button.handle_hover(mouse_pos)
            self.select_button.handle_hover(mouse_pos)
            self.close_button.handle_hover(mouse_pos)
            self.backspace_button.handle_hover(mouse_pos)
            self.clear_button.handle_hover(mouse_pos)

        elif event.type == pygame.KEYDOWN:
            # Keyboard shortcuts
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                self.state['close_pressed'] = True
                return True

            if event.key == pygame.K_BACKSPACE:
                self._on_backspace(self.backspace_button)
                return True

            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._on_select_result(self.select_button)
                return True

            if event.key == pygame.K_LEFT:
                self._on_prev_results(self.prev_button)
                return True

            if event.key == pygame.K_RIGHT:
                self._on_next_results(self.next_button)
                return True

            # Try to add character via keypad
            if event.unicode.isalnum():
                self.keypad.add_input(event.unicode.upper())
                self.search_input = self.keypad.get_input()
                self._perform_search()
                return True

        return False

    def update(self, dt: float):
        """Update window state"""
        if not self.active:
            return

    def draw(self, screen: pygame.Surface):
        """Draw modal overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Modal background
        modal_rect = pygame.Rect(self.modal_x, self.modal_y, self.modal_width, self.modal_height)
        pygame.draw.rect(screen, config.COLOR_DARK_GRAY, modal_rect)
        pygame.draw.rect(screen, config.COLOR_SEAGREEN_LIGHT, modal_rect, 3)

        # Get font getter function
        def get_font(size: int) -> pygame.font.Font:
            if size not in self.font_cache:
                try:
                    self.font_cache[size] = pygame.font.Font(config.FONT_PATH, size)
                except:
                    self.font_cache[size] = pygame.font.Font(None, size)
            return self.font_cache[size]

        # Draw title
        title = TextDisplay(
            self.modal_x + self.modal_width // 2, self.modal_y + 10,
            text="SEARCH SONGS",
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_LARGE,
            center=True
        )
        title.draw(screen, get_font)

        # Draw search input display
        self.search_input_display.draw(screen, get_font)

        # Draw search input box content
        pygame.draw.rect(screen, config.COLOR_WHITE, self.input_box_rect, 2)
        if self.search_input:
            input_text = TextDisplay(
                self.input_box_rect.x + 10, self.input_box_rect.y + 8,
                text=self.search_input,
                color=config.COLOR_YELLOW,
                font_size=config.FONT_SIZE_MEDIUM
            )
            input_text.draw(screen, get_font)

        # Draw keypad
        self.keypad.draw(screen, get_font)

        # Draw results
        self.results_title.draw(screen, get_font)
        for item in self.result_items:
            if item.visible:
                item.draw(screen, get_font)

        # Draw navigation buttons
        self.prev_button.draw(screen, get_font)
        self.next_button.draw(screen, get_font)
        self.select_button.draw(screen, get_font)
        self.close_button.draw(screen, get_font)

        # Draw control buttons
        self.backspace_button.draw(screen, get_font)
        self.clear_button.draw(screen, get_font)
        self.status_display.draw(screen, get_font)

    def is_close_pressed(self) -> bool:
        """Check if close button was pressed"""
        return self.state.get('close_pressed', False)

    def reset_close_state(self):
        """Reset close state"""
        self.state['close_pressed'] = False

    def is_song_selected(self) -> bool:
        """Check if a song was selected"""
        return self.state.get('song_selected', False)

    def reset_song_selected_state(self):
        """Reset song selected state"""
        self.state['song_selected'] = False

    def get_search_input(self) -> str:
        """Get current search input"""
        return self.search_input
