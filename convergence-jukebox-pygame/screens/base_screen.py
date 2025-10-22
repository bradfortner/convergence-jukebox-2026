"""
Base Screen - Abstract base class for all screens
"""

import pygame
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import config


class BaseScreen(ABC):
    """Abstract base class for all application screens"""

    def __init__(self, width: int = config.SCREEN_WIDTH, height: int = config.SCREEN_HEIGHT):
        """Initialize base screen"""
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, width, height)
        self.active = False
        self.state: Dict[str, Any] = {}

    @abstractmethod
    def enter(self):
        """Called when screen becomes active"""
        self.active = True

    @abstractmethod
    def exit(self):
        """Called when screen becomes inactive"""
        self.active = False

    @abstractmethod
    def handle_event(self, event: pygame.event.EventType) -> bool:
        """
        Handle pygame event

        Returns:
            True if event was handled, False otherwise
        """
        pass

    @abstractmethod
    def update(self, dt: float):
        """Update screen state - dt is delta time in seconds"""
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface):
        """Draw screen on surface"""
        pass

    def get_state(self) -> Dict[str, Any]:
        """Get screen state"""
        return self.state

    def set_state(self, key: str, value: Any):
        """Set state value"""
        self.state[key] = value

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """Get state value with optional default"""
        return self.state.get(key, default)

    def clear_state(self):
        """Clear all state"""
        self.state.clear()

    def is_active(self) -> bool:
        """Check if screen is active"""
        return self.active
