"""
Unit Tests - Services Testing
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import FileService, AudioService, QueueManager


class TestFileService(unittest.TestCase):
    """Test FileService"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_service = FileService()

    def test_file_exists(self):
        """Test file exists check"""
        # Test with a known existing file
        result = self.file_service.file_exists(__file__)
        self.assertTrue(result, "Test file should exist")

    def test_file_not_exists(self):
        """Test file not exists check"""
        result = self.file_service.file_exists("/nonexistent/path/file.txt")
        self.assertFalse(result, "Nonexistent file should return False")

    def test_read_nonexistent_song_list(self):
        """Test reading nonexistent song list"""
        result = self.file_service.read_song_list("nonexistent.txt")
        self.assertIsNone(result, "Nonexistent file should return None")

    def test_read_empty_playlist(self):
        """Test reading nonexistent playlist"""
        result = self.file_service.read_playlist("nonexistent.txt")
        self.assertEqual(result, [], "Nonexistent playlist should return empty list")

    def test_read_bands_list(self):
        """Test reading bands list"""
        result = self.file_service.read_bands_list("nonexistent.txt")
        self.assertEqual(result, [], "Nonexistent bands file should return empty list")


class TestAudioService(unittest.TestCase):
    """Test AudioService"""

    def setUp(self):
        """Set up test fixtures"""
        self.audio_service = AudioService()

    def test_initialization(self):
        """Test audio service initialization"""
        self.assertIsNotNone(self.audio_service)
        self.assertFalse(self.audio_service.is_muted())

    def test_volume_control(self):
        """Test volume control"""
        self.audio_service.set_volume(50)
        self.assertEqual(self.audio_service.get_volume(), 50)

    def test_volume_bounds(self):
        """Test volume bounds"""
        self.audio_service.set_volume(150)  # Over 100
        self.assertEqual(self.audio_service.get_volume(), 100)

        self.audio_service.set_volume(-50)  # Under 0
        self.assertEqual(self.audio_service.get_volume(), 0)

    def test_mute_unmute(self):
        """Test mute/unmute"""
        self.audio_service.mute()
        self.assertTrue(self.audio_service.is_muted())

        self.audio_service.unmute()
        self.assertFalse(self.audio_service.is_muted())

    def test_is_sound_loaded(self):
        """Test sound loaded check"""
        # Default sounds may or may not be loaded depending on assets
        result = self.audio_service.is_sound_loaded('nonexistent')
        self.assertFalse(result)


class TestQueueManager(unittest.TestCase):
    """Test QueueManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.queue_manager = QueueManager()
        self.sample_song = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'duration': '3:45'
        }

    def test_initialization(self):
        """Test queue manager initialization"""
        self.assertTrue(self.queue_manager.is_queue_empty())
        self.assertEqual(self.queue_manager.get_queue_size(), 0)

    def test_add_song(self):
        """Test adding song to queue"""
        result = self.queue_manager.add_song(self.sample_song)
        self.assertTrue(result)
        self.assertEqual(self.queue_manager.get_queue_size(), 1)

    def test_get_current_song(self):
        """Test getting current song"""
        self.queue_manager.add_song(self.sample_song)
        current = self.queue_manager.get_current_song()
        self.assertIsNotNone(current)
        self.assertEqual(current['title'], 'Test Song')

    def test_advance_to_next(self):
        """Test advancing to next song"""
        song1 = {'title': 'Song 1', 'artist': 'Artist'}
        song2 = {'title': 'Song 2', 'artist': 'Artist'}

        self.queue_manager.add_song(song1)
        self.queue_manager.add_song(song2)

        self.assertEqual(self.queue_manager.get_current_song()['title'], 'Song 1')

        next_song = self.queue_manager.advance_to_next()
        self.assertEqual(next_song['title'], 'Song 2')

    def test_repeat_modes(self):
        """Test repeat mode switching"""
        self.queue_manager.set_repeat_mode('off')
        self.assertEqual(self.queue_manager.get_repeat_mode(), 'off')

        mode = self.queue_manager.toggle_repeat_mode()
        self.assertEqual(mode, 'one')

        mode = self.queue_manager.toggle_repeat_mode()
        self.assertEqual(mode, 'all')

    def test_shuffle(self):
        """Test shuffle mode"""
        self.assertFalse(self.queue_manager.is_shuffle_enabled())

        self.queue_manager.set_shuffle(True)
        self.assertTrue(self.queue_manager.is_shuffle_enabled())

        self.queue_manager.toggle_shuffle()
        self.assertFalse(self.queue_manager.is_shuffle_enabled())

    def test_clear_queue(self):
        """Test clearing queue"""
        self.queue_manager.add_song(self.sample_song)
        self.assertFalse(self.queue_manager.is_queue_empty())

        self.queue_manager.clear_queue()
        self.assertTrue(self.queue_manager.is_queue_empty())

    def test_remove_song(self):
        """Test removing song from queue"""
        self.queue_manager.add_song({'title': 'Song 1'})
        self.queue_manager.add_song({'title': 'Song 2'})

        result = self.queue_manager.remove_song(0)
        self.assertTrue(result)
        self.assertEqual(self.queue_manager.get_queue_size(), 1)

    def test_queue_status(self):
        """Test queue status"""
        self.queue_manager.add_song(self.sample_song)

        status = self.queue_manager.get_status()
        self.assertIn('queue_size', status)
        self.assertIn('current_index', status)
        self.assertIn('repeat_mode', status)
        self.assertEqual(status['queue_size'], 1)


if __name__ == '__main__':
    unittest.main()
