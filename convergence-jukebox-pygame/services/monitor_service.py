"""
Monitor Service - Background monitoring for file changes and playback status
"""

import os
import threading
import time
from typing import Optional, Callable, Dict, Any

# Try to import watchdog, fall back if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    Observer = None
    FileSystemEventHandler = object
    FileModifiedEvent = None
    WATCHDOG_AVAILABLE = False


if WATCHDOG_AVAILABLE:
    class FileChangeHandler(FileSystemEventHandler):
        """Handler for file system events"""

        def __init__(self, on_modified_callback: Optional[Callable] = None):
            """Initialize handler"""
            super().__init__()
            self.on_modified_callback = on_modified_callback

        def on_modified(self, event):
            """Handle file modification"""
            if not event.is_directory and self.on_modified_callback:
                self.on_modified_callback(event.src_path)
else:
    class FileChangeHandler:
        """Dummy handler for when watchdog is not available"""

        def __init__(self, on_modified_callback: Optional[Callable] = None):
            """Initialize handler"""
            self.on_modified_callback = on_modified_callback


class MonitorService:
    """Background monitoring service for file changes and status updates"""

    def __init__(self):
        """Initialize monitor service"""
        self.observer: Optional[Observer] = None
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_current_song_changed_callback: Optional[Callable] = None
        self.on_playlist_changed_callback: Optional[Callable] = None
        self.on_file_change_callback: Optional[Callable] = None

        # Watch files
        self.watched_files: Dict[str, float] = {}  # filename -> last_modified_time

    def start_monitoring(self, parent_dir: str):
        """Start monitoring directory for changes"""
        if self.monitoring:
            return

        try:
            # Try using watchdog for file monitoring
            if WATCHDOG_AVAILABLE and Observer is not None:
                try:
                    self.observer = Observer()
                    handler = FileChangeHandler(self._on_file_modified)
                    self.observer.schedule(handler, parent_dir, recursive=False)
                    self.observer.start()
                    self.monitoring = True
                    print("File monitoring started (using watchdog)")
                except Exception as e:
                    print(f"Error starting watchdog observer: {e}")
                    # Fall back to polling
                    self._start_polling(parent_dir)
            else:
                # Fall back to polling if watchdog not available
                self._start_polling(parent_dir)

        except Exception as e:
            print(f"Error starting file monitoring: {e}")

    def _start_polling(self, parent_dir: str):
        """Start polling for file changes"""
        print("Using polling for file monitoring")
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._poll_files,
            args=(parent_dir,),
            daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring directory"""
        if not self.monitoring:
            return

        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()

            self.monitoring = False
            print("File monitoring stopped")

        except Exception as e:
            print(f"Error stopping file monitoring: {e}")

    def _on_file_modified(self, file_path: str):
        """Handle file modification"""
        filename = os.path.basename(file_path)

        # Check which file was modified
        if filename == "CurrentSongPlaying.txt":
            if self.on_current_song_changed_callback:
                self.on_current_song_changed_callback(file_path)

        elif filename == "PaidMusicPlayList.txt":
            if self.on_playlist_changed_callback:
                self.on_playlist_changed_callback(file_path)

        if self.on_file_change_callback:
            self.on_file_change_callback(filename, file_path)

    def _poll_files(self, parent_dir: str):
        """Poll files for changes (fallback method)"""
        files_to_watch = [
            "CurrentSongPlaying.txt",
            "PaidMusicPlayList.txt"
        ]

        # Initialize watched files
        for filename in files_to_watch:
            file_path = os.path.join(parent_dir, filename)
            if os.path.exists(file_path):
                self.watched_files[filename] = os.path.getmtime(file_path)

        # Poll for changes
        while self.monitoring:
            try:
                for filename in files_to_watch:
                    file_path = os.path.join(parent_dir, filename)
                    if os.path.exists(file_path):
                        current_mtime = os.path.getmtime(file_path)
                        last_mtime = self.watched_files.get(filename, 0)

                        if current_mtime > last_mtime:
                            self.watched_files[filename] = current_mtime
                            self._on_file_modified(file_path)

                time.sleep(1)  # Check every second

            except Exception as e:
                print(f"Error polling files: {e}")

    def set_current_song_callback(self, callback: Callable):
        """Set callback for current song changes"""
        self.on_current_song_changed_callback = callback

    def set_playlist_callback(self, callback: Callable):
        """Set callback for playlist changes"""
        self.on_playlist_changed_callback = callback

    def set_file_change_callback(self, callback: Callable):
        """Set callback for any file change"""
        self.on_file_change_callback = callback

    def is_monitoring(self) -> bool:
        """Check if monitoring is active"""
        return self.monitoring

    def get_status(self) -> dict:
        """Get monitor status"""
        return {
            'monitoring': self.monitoring,
            'watched_files': len(self.watched_files),
            'using_watchdog': self.observer is not None
        }
