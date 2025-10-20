#!/usr/bin/env python3
"""
Convergence Jukebox - Pygame Implementation
Main entry point for the application
"""

import sys
import pygame
from typing import Optional
import config
from data_manager import DataManager
from ui_engine import UIEngine


class JukeboxApplication:
    """Main Jukebox application"""

    def __init__(self):
        """Initialize application"""
        self.ui_engine = UIEngine()
        self.data_manager = DataManager()
        self.running = True
        self.current_screen = None

        # Initialize data
        if not self.data_manager.initialize():
            print("Failed to initialize data manager")
            sys.exit(1)

    def run(self):
        """Main application loop"""
        print("Convergence Jukebox - Pygame Edition")
        print(f"Loaded {self.data_manager.get_total_songs()} songs")
        print(f"Screen: {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")

        # TODO: Load initial screen (SelectionScreen)
        # For now, just run a test loop

        while self.running:
            self._handle_events()
            self._update()
            self._render()

        self.shutdown()

    def _handle_events(self):
        """Handle all events"""
        for event in self.ui_engine.get_events():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keypress(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouseclick(event)

    def _handle_keypress(self, event: pygame.event.EventType):
        """Handle keyboard input"""
        if event.key == pygame.K_ESCAPE:
            self.running = False

    def _handle_mouseclick(self, event: pygame.event.EventType):
        """Handle mouse click"""
        pass

    def _update(self):
        """Update application state"""
        # TODO: Update current screen
        pass

    def _render(self):
        """Render frame"""
        self.ui_engine.fill(config.COLOR_BLACK)

        # TODO: Render current screen

        # Draw test info
        self._render_test_info()

        self.ui_engine.update_display()
        self.ui_engine.get_frame_rate()

    def _render_test_info(self):
        """Render test information"""
        stats = self.data_manager.get_stats()

        y = 20
        self.ui_engine.draw_text(
            f"Convergence Jukebox - Pygame",
            20, y,
            color=config.COLOR_SEAGREEN_LIGHT,
            font_size=config.FONT_SIZE_LARGE
        )

        y += 40
        self.ui_engine.draw_text(
            f"Total Songs: {stats['total_songs']}",
            20, y,
            color=config.COLOR_WHITE,
            font_size=config.FONT_SIZE_MEDIUM
        )

        y += 30
        self.ui_engine.draw_text(
            f"Page: {stats['current_page']} / {stats['max_pages']}",
            20, y,
            color=config.COLOR_WHITE,
            font_size=config.FONT_SIZE_MEDIUM
        )

        y += 30
        self.ui_engine.draw_text(
            f"Credits: ${stats['credits']:.2f}",
            20, y,
            color=config.COLOR_YELLOW,
            font_size=config.FONT_SIZE_MEDIUM
        )

        y += 30
        self.ui_engine.draw_text(
            f"Upcoming: {stats['upcoming_count']}",
            20, y,
            color=config.COLOR_WHITE,
            font_size=config.FONT_SIZE_MEDIUM
        )

        # Draw key shortcuts
        y = config.SCREEN_HEIGHT - 40
        self.ui_engine.draw_text(
            "Press ESC to quit | Right-click for menu",
            20, y,
            color=config.COLOR_LIGHT_GRAY,
            font_size=config.FONT_SIZE_SMALL
        )

    def shutdown(self):
        """Clean shutdown"""
        print("Shutting down Jukebox")
        self.ui_engine.quit()
        pygame.quit()


def main():
    """Entry point"""
    try:
        app = JukeboxApplication()
        app.run()
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
