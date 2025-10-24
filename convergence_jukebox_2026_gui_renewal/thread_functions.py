# ============================================================================
# CONVERGENCE JUKEBOX 2026 - BACKGROUND THREAD FUNCTIONS MODULE
# ============================================================================
# This module contains all background thread functions used by the GUI
# Purpose: Separate thread logic from main initialization for modularity
# ============================================================================

import time

# ============================================================================
# FILE LOOKUP THREAD FUNCTION
# ============================================================================
# Purpose: Background thread that monitors for file/song changes and sends
#          periodic update events to the GUI window for display refresh
#
# Source: Code developed from Python GUIs - "The Official PySimpleGUI Course"
#         https://www.udemy.com/course/pysimplegui/learn/lecture/30070620
#         Background image code modified from
#         https://www.pysimplegui.org/en/latest/Demos/#demo_window_background_imagepy
# ============================================================================

def file_lookup_thread(song_playing_lookup_window):
    """
    Background thread function that monitors for song playback changes.

    This function runs continuously in a separate thread and periodically sends
    update events to the GUI window to refresh the display with current song
    information.

    Args:
        song_playing_lookup_window (PySimpleGUI.Window): The main GUI window object
                                                         that will receive update events

    Returns:
        None (runs until interrupted)
    """
    try:
        # Run indefinitely until the user interrupts (Ctrl+C)
        while True:
            # Sleep for 3 seconds between each update
            # This prevents excessive CPU usage while still providing responsive UI updates
            # Duration: 3 seconds (adjust this value to change update frequency)
            time.sleep(3)

            # Send a custom event to the GUI window indicating it's time to check for song changes
            # write_event_value() sends an asynchronous event to the window's event queue
            #
            # Parameters:
            #   - Event key: '--SONG_PLAYING_LOOKUP--' (unique identifier for this event)
            #   - Event value: 'counter = 1' (data passed with the event)
            #
            # The main window's event loop will receive this event and can respond by:
            #   - Checking the currently playing song
            #   - Updating the display with new song information
            #   - Refreshing UI elements showing current playback status
            song_playing_lookup_window.write_event_value('--SONG_PLAYING_LOOKUP--', f'counter = {1}')

    except KeyboardInterrupt:
        # Gracefully handle user interruption (Ctrl+C)
        # This allows the thread to exit cleanly without throwing an error
        # The application can then shut down properly
        pass
