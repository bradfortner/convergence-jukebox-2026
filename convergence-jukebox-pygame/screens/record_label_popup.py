"""
Record Label Popup - Modal display for 45 RPM record label animation
"""

import pygame
from typing import Optional, Callable, List, Dict, Any
import config
from components import TextDisplay, Button
from services.record_label_service import RecordLabelService
from .base_screen import BaseScreen


class RecordLabelPopup(BaseScreen):
    """Modal popup displaying rotating 45 RPM record label animation"""

    def __init__(
        self,
        width: int = config.SCREEN_WIDTH,
        height: int = config.SCREEN_HEIGHT,
        on_animation_complete_callback: Optional[Callable] = None
    ):
        """Initialize record label popup"""
        super().__init__(width, height)

        self.on_animation_complete_callback = on_animation_complete_callback

        # Record label service
        self.label_service = RecordLabelService()

        # Animation state
        self.animation_frames: List[pygame.Surface] = []
        self.current_frame_index = 0
        self.frame_time = 0
        self.frame_duration = 1000 // 60  # milliseconds per frame (60 FPS)
        self.song: Optional[Dict[str, Any]] = None

        # Popup layout
        self.popup_width = min(width - 100, 600)
        self.popup_height = min(height - 100, 700)
        self.popup_x = (width - self.popup_width) // 2
        self.popup_y = (height - self.popup_height) // 2

        # Label display area
        self.label_width = 500
        self.label_height = 500
        self.label_x = (width - self.label_width) // 2
        self.label_y = (height - self.label_height) // 2 - 50

        # Current frame surface
        self.current_frame_surface: Optional[pygame.Surface] = None

        # Song info display
        self.song_title_display = TextDisplay(
            width // 2, self.label_y + self.label_height + 20,
            text="",
            color=config.COLOR_YELLOW,
            font_size=config.FONT_SIZE_MEDIUM,
            center=True,
            max_width=self.popup_width - 40
        )

        self.song_artist_display = TextDisplay(
            width // 2, self.label_y + self.label_height + 60,
            text="",
            color=config.COLOR_WHITE,
            font_size=config.FONT_SIZE_SMALL,
            center=True,
            max_width=self.popup_width - 40
        )

        # Close button
        self.close_button = Button(
            (width - 100) // 2, height - 60,
            100, 40,
            text="Close",
            font_size=config.FONT_SIZE_SMALL,
            bg_color=(150, 50, 50),
            callback=self._on_close
        )

        # Frame counter
        self.frame_counter_display = TextDisplay(
            width - 100, 10,
            text="Frame: 0/0",
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_TINY
        )

        # Font cache
        self.font_cache: Dict[int, pygame.font.Font] = {}

    def show(self, song: Dict[str, Any]):
        """Show popup with song animation"""
        self.song = song
        self.enter()

    def _generate_animation(self):
        """Generate record label animation"""
        if not self.song:
            return

        print(f"Generating animation for: {self.song.get('title', 'Unknown')}")

        # Create animation frames using PIL
        try:
            from PIL import Image
            pil_frames = self.label_service.create_label_animation(self.song)

            if pil_frames:
                # Convert PIL images to pygame surfaces
                self.animation_frames = []
                for pil_img in pil_frames:
                    # Convert PIL Image to pygame Surface
                    pygame_img = pygame.image.fromstring(
                        pil_img.tobytes(),
                        pil_img.size,
                        pil_img.mode
                    )
                    self.animation_frames.append(pygame_img)

                print(f"Generated {len(self.animation_frames)} animation frames")
                self.current_frame_index = 0
                self.frame_time = 0

        except ImportError:
            print("PIL not available, using static label")
            self._create_static_label()

    def _create_static_label(self):
        """Create static label if animation generation fails"""
        # Create a simple static label surface
        surface = pygame.Surface((self.label_width, self.label_height))
        surface.fill(config.COLOR_BLACK)

        # Draw simple label representation
        pygame.draw.circle(surface, (100, 100, 100), (self.label_width // 2, self.label_height // 2), 240)
        pygame.draw.circle(surface, (200, 20, 20), (self.label_width // 2, self.label_height // 2), 180)
        pygame.draw.circle(surface, (50, 50, 50), (self.label_width // 2, self.label_height // 2), 50)

        self.animation_frames = [surface]

    def _on_close(self, button: Button):
        """Handle close button"""
        self.state['close_pressed'] = True

    def enter(self):
        """Called when popup becomes active"""
        super().enter()
        self._generate_animation()

        if self.song:
            title = self.song.get('title', 'Unknown')
            artist = self.song.get('artist', 'Unknown')

            # Truncate if too long
            if len(title) > 40:
                title = title[:37] + "..."
            if len(artist) > 40:
                artist = artist[:37] + "..."

            self.song_title_display.update_text(title)
            self.song_artist_display.update_text(artist)

    def exit(self):
        """Called when popup becomes inactive"""
        super().exit()
        self.animation_frames.clear()

    def handle_event(self, event: pygame.event.EventType) -> bool:
        """Handle pygame events"""
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.close_button.handle_click(mouse_pos):
                return True

        elif event.type == pygame.MOUSEMOTION:
            self.close_button.handle_hover(mouse_pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                self.state['close_pressed'] = True
                return True

        return False

    def update(self, dt: float):
        """Update animation state"""
        if not self.active or not self.animation_frames:
            return

        # Update frame timing
        self.frame_time += dt * 1000  # Convert to milliseconds

        if self.frame_time >= self.frame_duration:
            self.frame_time = 0
            self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)

            # Check if animation complete
            if self.current_frame_index == 0 and len(self.animation_frames) > 1:
                if self.on_animation_complete_callback:
                    self.on_animation_complete_callback()

            # Update frame counter
            self.frame_counter_display.update_text(
                f"Frame: {self.current_frame_index + 1}/{len(self.animation_frames)}"
            )

    def draw(self, screen: pygame.Surface):
        """Draw popup"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Get font getter function
        def get_font(size: int):
            if size not in self.font_cache:
                try:
                    self.font_cache[size] = pygame.font.Font(config.FONT_PATH, size)
                except:
                    self.font_cache[size] = pygame.font.Font(None, size)
            return self.font_cache[size]

        # Draw current animation frame
        if self.animation_frames and 0 <= self.current_frame_index < len(self.animation_frames):
            frame = self.animation_frames[self.current_frame_index]
            screen.blit(frame, (self.label_x, self.label_y))

        # Draw song info
        self.song_title_display.draw(screen, get_font)
        self.song_artist_display.draw(screen, get_font)

        # Draw frame counter
        self.frame_counter_display.draw(screen, get_font)

        # Draw close button
        self.close_button.draw(screen, get_font)

    def is_close_pressed(self) -> bool:
        """Check if close button was pressed"""
        return self.state.get('close_pressed', False)

    def reset_close_state(self):
        """Reset close state"""
        self.state['close_pressed'] = False
