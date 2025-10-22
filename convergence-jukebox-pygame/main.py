#!/usr/bin/env python3
"""
Convergence Jukebox - Pygame Implementation
Main entry point for the application
"""

import sys
import pygame
from typing import Optional, List, Dict, Any
import config
from data_manager import DataManager
from ui_engine import UIEngine
from screens import SelectionScreen, InfoScreen, ControlPanel, SearchWindow, RecordLabelPopup
from services import VLCService, FileService, AudioService, QueueManager, MonitorService


class JukeboxApplication:
    """Main Jukebox application"""

    def __init__(self):
        """Initialize application"""
        self.ui_engine = UIEngine()
        self.data_manager = DataManager()
        self.running = True
        self.current_screen = None
        self.current_song: Optional[Dict[str, Any]] = None

        # Initialize data
        if not self.data_manager.initialize():
            print("Failed to initialize data manager")
            sys.exit(1)

        # Create screens with callbacks
        self.selection_screen = SelectionScreen(
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            get_songs_callback=self._get_songs,
            get_band_name_callback=self._process_band_name
        )

        self.info_screen = InfoScreen(
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            get_current_song_callback=self._get_current_song,
            get_upcoming_callback=self._get_upcoming_songs,
            get_credits_callback=self._get_credits,
            get_band_name_callback=self._process_band_name
        )

        self.control_panel = ControlPanel(
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            on_song_selected_callback=self._on_song_selected_from_control,
            on_page_changed_callback=self._on_page_changed
        )

        self.search_window = SearchWindow(
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            get_all_songs_callback=self._get_songs,
            get_band_name_callback=self._process_band_name,
            on_song_selected_callback=self._on_song_selected_from_search
        )

        self.record_label_popup = RecordLabelPopup(
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            on_animation_complete_callback=self._on_label_animation_complete
        )

        # Popup states
        self.search_open = False
        self.label_popup_open = False

        # Initialize services
        print("Initializing services...")
        self.vlc_service = VLCService()
        self.file_service = FileService()
        self.audio_service = AudioService()
        self.queue_manager = QueueManager()
        self.monitor_service = MonitorService()

        # Set up callbacks
        self.monitor_service.set_current_song_callback(self._on_current_song_file_changed)
        self.monitor_service.set_playlist_callback(self._on_playlist_file_changed)

        # Start background monitoring
        parent_dir = self.data_manager.parent_dir if hasattr(self.data_manager, 'parent_dir') else '.'
        self.monitor_service.start_monitoring(parent_dir)

        # Start with selection screen
        self.current_screen = self.selection_screen
        self.current_screen.enter()

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
                # Global keypress handling
                if event.key == pygame.K_ESCAPE:
                    if self.search_open:
                        # Close search window
                        self._toggle_search()
                    else:
                        self.running = False
                elif event.key == pygame.K_f or event.key == pygame.K_SLASH:
                    # Toggle search window
                    self._toggle_search()
                elif event.key == pygame.K_i and not self.search_open:
                    # Toggle to info screen (only if search not open)
                    self._switch_screen("info")
                elif event.key == pygame.K_s and not self.search_open:
                    # Toggle to selection screen (only if search not open)
                    self._switch_screen("selection")
                elif event.key == pygame.K_p and not self.search_open:
                    # Toggle to control panel (only if search not open)
                    self._switch_screen("control")
                elif event.key == pygame.K_r and not self.search_open and not self.label_popup_open:
                    # Toggle record label (only if neither search nor label open)
                    self._show_record_label()
                else:
                    # Pass to search window or current screen
                    if self.search_open:
                        self.search_window.handle_event(event)
                    elif self.current_screen:
                        self.current_screen.handle_event(event)
            else:
                # Pass event to search window or current screen
                if self.search_open:
                    self.search_window.handle_event(event)
                elif self.current_screen:
                    self.current_screen.handle_event(event)

        # Check for popup state changes
        if self.search_open and self.search_window.is_close_pressed():
            self._toggle_search()
            self.search_window.reset_close_state()

        if self.label_popup_open and self.record_label_popup.is_close_pressed():
            self._hide_record_label()
            self.record_label_popup.reset_close_state()

        # Check for screen-specific state changes
        if self.current_screen == self.info_screen and self.info_screen.is_back_pressed():
            self._switch_screen("selection")
            self.info_screen.reset_back_state()

    def _handle_keypress(self, event: pygame.event.EventType) -> bool:
        """Handle keyboard input - return True if handled"""
        # Pass to current screen first
        if self.current_screen:
            return self.current_screen.handle_event(event)
        return False

    def _update(self):
        """Update application state"""
        if self.current_screen:
            dt = self.ui_engine.get_delta_time()
            self.current_screen.update(dt)

        if self.search_open:
            dt = self.ui_engine.get_delta_time()
            self.search_window.update(dt)

        if self.label_popup_open:
            dt = self.ui_engine.get_delta_time()
            self.record_label_popup.update(dt)

    def _render(self):
        """Render frame"""
        self.ui_engine.fill(config.COLOR_BLACK)

        # Render current screen
        if self.current_screen:
            self.current_screen.draw(self.ui_engine.screen)

        # Render search window on top if open
        if self.search_open:
            self.search_window.draw(self.ui_engine.screen)

        # Render label popup on top if open
        if self.label_popup_open:
            self.record_label_popup.draw(self.ui_engine.screen)

        self.ui_engine.update_display()
        self.ui_engine.get_frame_rate()

    def _get_songs(self) -> List[Dict[str, Any]]:
        """Get songs from data manager"""
        songs = []
        for song in self.data_manager.songs:
            songs.append({
                'number': song.number,
                'location': song.location,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'year': song.year,
                'comment': song.comment,
                'duration': song.duration
            })
        return songs

    def _process_band_name(self, artist: str) -> str:
        """Process band name to add 'The' prefix if needed"""
        # Check if artist is in bands list
        if artist.lower() in self.data_manager.bands_list:
            # Check if it's not exempted
            if artist.lower() not in self.data_manager.exempted_bands:
                return f"The {artist}"
        return artist

    def _get_current_song(self) -> Optional[Dict[str, Any]]:
        """Get currently playing song"""
        return self.current_song

    def _get_upcoming_songs(self) -> List[str]:
        """Get list of upcoming songs"""
        upcoming = self.data_manager.get_upcoming()
        return upcoming if upcoming else []

    def _get_credits(self) -> float:
        """Get current credits"""
        return self.data_manager.get_credits()

    def _on_song_selected_from_control(self, column: str, row: int, song_index: int):
        """Handle song selection from control panel"""
        # This callback is triggered when a song is selected via the control panel
        # You can add logic here to queue the song, play it, etc.
        print(f"Song selected: {column}{row} (Index: {song_index})")

        # Optional: Switch back to selection screen after selection
        self._switch_screen("selection")

    def _on_page_changed(self, new_page: int):
        """Handle page change from control panel"""
        print(f"Page changed to: {new_page}")
        if self.selection_screen:
            self.selection_screen.go_to_page(new_page)

    def _switch_screen(self, screen_name: str):
        """Switch to different screen"""
        if self.current_screen:
            self.current_screen.exit()

        if screen_name == "info":
            self.current_screen = self.info_screen
        elif screen_name == "selection":
            self.current_screen = self.selection_screen
        elif screen_name == "control":
            self.current_screen = self.control_panel
        else:
            self.current_screen = self.selection_screen

        if self.current_screen:
            self.current_screen.enter()

    def _toggle_search(self):
        """Toggle search window open/closed"""
        if self.search_open:
            self.search_window.exit()
            self.search_open = False
        else:
            self.search_window.enter()
            self.search_open = True

    def _on_song_selected_from_search(self, song: Dict[str, Any]):
        """Handle song selection from search window"""
        # This callback is triggered when a song is selected via the search window
        print(f"Song selected from search: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}")

        # Optional: Switch back to selection or info screen after selection
        # You can add logic here to queue the song, play it, etc.

    def _show_record_label(self):
        """Show record label popup with current or sample song"""
        # Use current song if available, otherwise use a sample song
        song = self.current_song
        if not song and self.data_manager.songs:
            # Use first song as sample
            first_song = self.data_manager.songs[0]
            song = {
                'title': first_song.title,
                'artist': first_song.artist,
                'album': first_song.album,
                'duration': first_song.duration
            }

        if song:
            self.record_label_popup.show(song)
            self.label_popup_open = True

    def _hide_record_label(self):
        """Hide record label popup"""
        self.label_popup_open = False

    def _on_label_animation_complete(self):
        """Handle record label animation completion"""
        print("Record label animation completed")

    def _on_current_song_file_changed(self, file_path: str):
        """Handle current song file change"""
        print(f"Current song file changed: {file_path}")
        # Read and update current song
        try:
            current_song_path = self.file_service.read_current_song()
            if current_song_path:
                print(f"Now playing: {current_song_path}")
                # Update UI if needed
        except Exception as e:
            print(f"Error handling current song change: {e}")

    def _on_playlist_file_changed(self, file_path: str):
        """Handle playlist file change"""
        print(f"Playlist file changed: {file_path}")
        # Read and update playlist
        try:
            playlist = self.file_service.read_playlist()
            print(f"Playlist updated: {len(playlist) if playlist else 0} songs")
        except Exception as e:
            print(f"Error handling playlist change: {e}")

    def shutdown(self):
        """Clean shutdown"""
        print("Shutting down Jukebox")

        # Stop background monitoring
        try:
            self.monitor_service.stop_monitoring()
        except Exception as e:
            print(f"Error stopping monitor: {e}")

        # Stop audio playback
        try:
            if self.vlc_service and self.vlc_service.is_playing:
                self.vlc_service.stop()
        except Exception as e:
            print(f"Error stopping VLC: {e}")

        # Clean up UI
        self.ui_engine.quit()
        pygame.quit()

        print("Jukebox shutdown complete")


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
