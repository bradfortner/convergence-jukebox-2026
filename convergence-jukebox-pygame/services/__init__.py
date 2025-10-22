"""
Services Package - External service integrations
"""

from .record_label_service import RecordLabelService
from .vlc_service import VLCService
from .file_service import FileService
from .audio_service import AudioService
from .queue_manager import QueueManager
from .monitor_service import MonitorService

__all__ = [
    'RecordLabelService',
    'VLCService',
    'FileService',
    'AudioService',
    'QueueManager',
    'MonitorService'
]
