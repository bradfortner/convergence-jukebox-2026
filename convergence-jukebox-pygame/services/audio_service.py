"""
Audio Service - Sound effects and audio management
"""

import os
from typing import Optional, Dict
import pygame
import config


class AudioService:
    """Service for playing sound effects"""

    def __init__(self):
        """Initialize audio service"""
        pygame.mixer.init()
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.volume = 100
        self.muted = False
        self._load_default_sounds()

    def _load_default_sounds(self):
        """Load default sound effects"""
        # Try to load sounds from assets directory
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'sounds')

        sound_files = {
            'buzz': 'buzz.mp3',
            'success': 'success.mp3',
            'error': 'error.mp3',
            'select': 'select.mp3'
        }

        for sound_name, sound_file in sound_files.items():
            sound_path = os.path.join(assets_dir, sound_file)
            if os.path.exists(sound_path):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                except Exception as e:
                    print(f"Error loading sound {sound_name}: {e}")

    def load_sound(self, sound_name: str, file_path: str) -> bool:
        """Load a sound effect from file"""
        if not os.path.exists(file_path):
            print(f"Sound file not found: {file_path}")
            return False

        try:
            self.sounds[sound_name] = pygame.mixer.Sound(file_path)
            return True
        except Exception as e:
            print(f"Error loading sound: {e}")
            return False

    def play_sound(self, sound_name: str, loops: int = 0) -> bool:
        """Play a sound effect"""
        if sound_name not in self.sounds:
            return False

        if self.muted:
            return True

        try:
            sound = self.sounds[sound_name]
            sound.set_volume(self.volume / 100.0)
            sound.play(loops)
            return True
        except Exception as e:
            print(f"Error playing sound: {e}")
            return False

    def stop_sound(self, sound_name: str) -> bool:
        """Stop a sound effect"""
        if sound_name not in self.sounds:
            return False

        try:
            self.sounds[sound_name].stop()
            return True
        except Exception as e:
            print(f"Error stopping sound: {e}")
            return False

    def stop_all_sounds(self):
        """Stop all sound effects"""
        try:
            pygame.mixer.stop()
        except Exception as e:
            print(f"Error stopping all sounds: {e}")

    def set_volume(self, volume: int):
        """Set sound volume (0-100)"""
        self.volume = max(0, min(100, volume))
        # Apply volume to all loaded sounds
        for sound in self.sounds.values():
            sound.set_volume(self.volume / 100.0)

    def get_volume(self) -> int:
        """Get current volume"""
        return self.volume

    def mute(self):
        """Mute all sounds"""
        self.muted = True
        # Stop all currently playing sounds
        pygame.mixer.stop()

    def unmute(self):
        """Unmute all sounds"""
        self.muted = False
        # Volume will be applied when sounds are played next

    def is_muted(self) -> bool:
        """Check if audio is muted"""
        return self.muted

    def play_buzz(self):
        """Play buzz sound"""
        self.play_sound('buzz')

    def play_success(self):
        """Play success sound"""
        self.play_sound('success')

    def play_error(self):
        """Play error sound"""
        self.play_sound('error')

    def play_select(self):
        """Play select sound"""
        self.play_sound('select')

    def get_loaded_sounds(self) -> list:
        """Get list of loaded sounds"""
        return list(self.sounds.keys())

    def is_sound_loaded(self, sound_name: str) -> bool:
        """Check if sound is loaded"""
        return sound_name in self.sounds
