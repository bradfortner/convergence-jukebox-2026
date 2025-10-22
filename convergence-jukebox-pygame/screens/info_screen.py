"""
Info Screen - Display Now Playing, Upcoming Queue, and Credits
"""

import pygame
from typing import Optional, Callable, List, Dict, Any
import config
from components import TextDisplay, Button
from .base_screen import BaseScreen


class InfoScreen(BaseScreen):
    """Info screen showing now playing, upcoming queue, and credits"""

    def __init__(
        self,
        width: int = config.SCREEN_WIDTH,
        height: int = config.SCREEN_HEIGHT,
        get_current_song_callback: Optional[Callable] = None,
        get_upcoming_callback: Optional[Callable] = None,
        get_credits_callback: Optional[Callable] = None,
        get_band_name_callback: Optional[Callable] = None
    ):
        """Initialize info screen"""
        super().__init__(width, height)

        self.get_current_song_callback = get_current_song_callback
        self.get_upcoming_callback = get_upcoming_callback
        self.get_credits_callback = get_credits_callback
        self.get_band_name_callback = get_band_name_callback

        # Layout sections
        self.section_width = width // 3
        self.section_height = height - 60

        # NOW PLAYING SECTION (Left)
        self.now_playing_x = 10
        self.now_playing_y = 50
        self.now_playing_width = self.section_width - 20
        self.now_playing_height = self.section_height

        self.now_playing_title = TextDisplay(
            self.now_playing_x, self.now_playing_y,
            text="NOW PLAYING",
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_MEDIUM
        )

        self.now_playing_artist = TextDisplay(
            self.now_playing_x, self.now_playing_y + 50,
            text="",
            color=config.COLOR_YELLOW,
            font_size=config.FONT_SIZE_MEDIUM,
            max_width=self.now_playing_width
        )

        self.now_playing_song = TextDisplay(
            self.now_playing_x, self.now_playing_y + 120,
            text="",
            color=config.COLOR_WHITE,
            font_size=config.FONT_SIZE_SMALL,
            max_width=self.now_playing_width
        )

        self.now_playing_duration = TextDisplay(
            self.now_playing_x, self.now_playing_y + 200,
            text="",
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_TINY
        )

        self.now_playing_album = TextDisplay(
            self.now_playing_x, self.now_playing_y + 230,
            text="",
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_TINY,
            max_width=self.now_playing_width
        )

        # UPCOMING SECTION (Middle)
        self.upcoming_x = self.section_width + 10
        self.upcoming_y = 50
        self.upcoming_width = self.section_width - 20
        self.upcoming_height = self.section_height

        self.upcoming_title = TextDisplay(
            self.upcoming_x, self.upcoming_y,
            text="UPCOMING (Next 10)",
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_MEDIUM
        )

        # Upcoming queue items (text displays)
        self.upcoming_items: List[TextDisplay] = []
        for i in range(10):
            item_y = self.upcoming_y + 50 + i * 35
            item = TextDisplay(
                self.upcoming_x, item_y,
                text="",
                color=config.COLOR_WHITE,
                font_size=config.FONT_SIZE_TINY,
                max_width=self.upcoming_width
            )
            self.upcoming_items.append(item)

        # CREDITS SECTION (Right)
        self.credits_x = 2 * self.section_width + 10
        self.credits_y = 50
        self.credits_width = self.section_width - 20
        self.credits_height = self.section_height

        self.credits_title = TextDisplay(
            self.credits_x, self.credits_y,
            text="CREDITS",
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_MEDIUM
        )

        self.credits_amount = TextDisplay(
            self.credits_x, self.credits_y + 80,
            text="$0.00",
            color=config.COLOR_YELLOW,
            font_size=config.FONT_SIZE_LARGE
        )

        self.credits_info = TextDisplay(
            self.credits_x, self.credits_y + 150,
            text="Cost per song: $0.25",
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_SMALL
        )

        self.credits_queue_count = TextDisplay(
            self.credits_x, self.credits_y + 200,
            text="Queued: 0 songs",
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_SMALL
        )

        # Back button
        self.back_button = Button(
            10, height - 45,
            100, 40,
            text="Back",
            font_size=config.FONT_SIZE_SMALL,
            callback=self._on_back
        )

        # Update timer for real-time updates
        self.last_update_time = 0
        self.update_interval = 500  # milliseconds

        # Font cache
        self.font_cache: Dict[int, pygame.font.Font] = {}

    def _on_back(self, button: Button):
        """Handle back button"""
        self.state['back_pressed'] = True

    def _update_now_playing(self):
        """Update now playing display"""
        if not self.get_current_song_callback:
            return

        song = self.get_current_song_callback()
        if song:
            # Process artist name
            artist = song.get('artist', 'Unknown')
            if self.get_band_name_callback:
                artist = self.get_band_name_callback(artist)

            self.now_playing_artist.update_text(artist)
            self.now_playing_song.update_text(song.get('title', 'Unknown'))
            self.now_playing_duration.update_text(f"Duration: {song.get('duration', 'N/A')}")
            self.now_playing_album.update_text(f"Album: {song.get('album', 'N/A')}")
        else:
            self.now_playing_artist.update_text("No song playing")
            self.now_playing_song.update_text("")
            self.now_playing_duration.update_text("")
            self.now_playing_album.update_text("")

    def _update_upcoming(self):
        """Update upcoming queue display"""
        if not self.get_upcoming_callback:
            return

        upcoming = self.get_upcoming_callback()
        for i, item in enumerate(self.upcoming_items):
            if i < len(upcoming):
                display_name = upcoming[i]
                # Truncate if too long
                if len(display_name) > 40:
                    display_name = display_name[:37] + "..."
                item.update_text(f"{i+1}. {display_name}")
                item.set_visible(True)
            else:
                item.set_visible(False)

    def _update_credits(self):
        """Update credits display"""
        if not self.get_credits_callback:
            return

        credits = self.get_credits_callback()
        self.credits_amount.update_text(f"${credits:.2f}")

        # Calculate queue count (credits / cost per song)
        cost_per_song = config.CREDIT_INCREMENT
        queue_count = int(credits / cost_per_song) if cost_per_song > 0 else 0
        self.credits_queue_count.update_text(f"Can play: {queue_count} songs")

    def enter(self):
        """Called when screen becomes active"""
        super().enter()
        self._update_now_playing()
        self._update_upcoming()
        self._update_credits()

    def exit(self):
        """Called when screen becomes inactive"""
        super().exit()

    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle pygame events"""
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.handle_click(mouse_pos):
                return True

        elif event.type == pygame.MOUSEMOTION:
            self.back_button.handle_hover(mouse_pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                self.state['back_pressed'] = True
                return True

        return False

    def update(self, dt: float):
        """Update screen state with real-time updates"""
        if not self.active:
            return

        # Update every interval milliseconds
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time >= self.update_interval:
            self._update_now_playing()
            self._update_upcoming()
            self._update_credits()
            self.last_update_time = current_time

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

        # Draw section separators
        separator_color = config.COLOR_DARK_GRAY
        pygame.draw.line(
            screen, separator_color,
            (self.section_width, 30),
            (self.section_width, self.height - 50),
            2
        )
        pygame.draw.line(
            screen, separator_color,
            (2 * self.section_width, 30),
            (2 * self.section_width, self.height - 50),
            2
        )

        # Draw NOW PLAYING section
        self.now_playing_title.draw(screen, get_font)
        self.now_playing_artist.draw_multiline(screen, get_font)
        self.now_playing_song.draw_multiline(screen, get_font)
        self.now_playing_duration.draw(screen, get_font)
        self.now_playing_album.draw_multiline(screen, get_font)

        # Draw UPCOMING section
        self.upcoming_title.draw(screen, get_font)
        for item in self.upcoming_items:
            if item.visible:
                item.draw(screen, get_font)

        # Draw CREDITS section
        self.credits_title.draw(screen, get_font)
        self.credits_amount.draw(screen, get_font)
        self.credits_info.draw(screen, get_font)
        self.credits_queue_count.draw(screen, get_font)

        # Draw back button
        self.back_button.draw(screen, get_font)

    def is_back_pressed(self) -> bool:
        """Check if back button was pressed"""
        return self.state.get('back_pressed', False)

    def reset_back_state(self):
        """Reset back button state"""
        self.state['back_pressed'] = False
