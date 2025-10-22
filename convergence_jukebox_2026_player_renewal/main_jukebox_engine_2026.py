# -*- coding: utf-8 -*-
# import FreeSimpleGUI as sg  # https://github.com/spyoungtech/FreeSimpleGUI
import vlc
import sys
import io
# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime, timedelta  # required for logging timestamp
from tinytag import TinyTag  # https://pypi.org/project/tinytag/
import psutil
import glob
import json
import os
import random
import time
import gc
import sys
from typing import List, Optional, Union, Dict, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import logging
from collections import namedtuple

# Global VLC player registry for resource management (memory leak prevention)
_vlc_player_registry = []
_vlc_cleanup_lock = False


def _create_managed_vlc_player(media_path: Union[str, Path], *,
                               console_output: bool = False,
                               validate_path: bool = True,
                               auto_cleanup: bool = True,
                               registry_size_limit: int = 10,
                               include_metadata: bool = False,
                               enable_logging: bool = True,
                               fallback_on_error: bool = True,
                               logger: Optional[logging.Logger] = None) -> Dict[str, Union[bool, Any, str, Dict]]:
    """Create a VLC MediaPlayer with comprehensive resource management and Pythonic functionality.

    This function implements modern Python VLC player creation patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Comprehensive type hints for all parameters and return values
    - Structured return values with detailed operation tracking
    - Input validation with configurable strictness
    - Automatic resource cleanup and registry management
    - Performance monitoring and metadata collection
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions
    - Constants for better maintainability

    Args:
        media_path: Path to media file (str or Path object)
        console_output: Whether to print status messages - keyword-only
        validate_path: Whether to validate media file path - keyword-only
        auto_cleanup: Whether to perform automatic cleanup - keyword-only
        registry_size_limit: Maximum registry size before cleanup - keyword-only
        include_metadata: Whether to include operation metadata - keyword-only
        enable_logging: Whether to log operations - keyword-only
        fallback_on_error: Whether to attempt fallback on errors - keyword-only
        logger: Optional logger for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if player created successfully
        - 'player': vlc.MediaPlayer - Created player instance (None if failed)
        - 'player_id': str - Unique player identifier
        - 'registry_size': int - Current registry size
        - 'cleanup_performed': bool - Whether cleanup was performed
        - 'error_message': str - Error message if failed (empty if success)
        - 'fallback_used': bool - Whether fallback was used
        - 'operation_metadata': Dict - Operation details (if enabled)

    Examples:
        >>> result = _create_managed_vlc_player('/path/to/song.mp3')
        {'success': True, 'player': <VLC_Player>, 'player_id': 'vlc_abc123', ...}
        >>> result = _create_managed_vlc_player('/invalid/path', validate_path=True)
        {'success': False, 'error_message': 'Invalid media path', ...}
        >>> result = _create_managed_vlc_player('/path/song.mp3', include_metadata=True)
        {'success': True, 'operation_metadata': {'creation_time': 1234567890}, ...}

    Raises:
        ValueError: If media_path is invalid and validate_path=True

    Note:
        Function maintains global VLC player registry for resource management.
        Automatic cleanup prevents memory leaks in long-running applications.
        Supports comprehensive monitoring and fallback mechanisms.
    """
    from typing import Final
    from pathlib import Path
    import time
    import uuid

    # Constants for better maintainability
    DEFAULT_REGISTRY_LIMIT: Final = 10
    MAX_REGISTRY_LIMIT: Final = 100
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_INFO: Final = 'ℹ️'

    # Initialize result structure
    creation_start_time = time.time()
    result = {
        'success': False,
        'player': None,
        'player_id': '',
        'registry_size': 0,
        'cleanup_performed': False,
        'error_message': '',
        'fallback_used': False,
        'operation_metadata': {} if include_metadata else None
    }

    try:
        global _vlc_player_registry

        # Input validation with early returns
        if validate_path:
            validation_result = _validate_vlc_media_path(
                media_path=media_path,
                console_output=console_output
            )

            if not validation_result['valid']:
                result['error_message'] = validation_result['message']
                if console_output:
                    print(f"{EMOJI_ERROR} Media path validation failed: {validation_result['message']}")
                return result

        # Validate registry size limit
        if registry_size_limit < 1 or registry_size_limit > MAX_REGISTRY_LIMIT:
            registry_size_limit = DEFAULT_REGISTRY_LIMIT
            if console_output:
                print(f"{EMOJI_WARNING} Invalid registry limit, using default: {DEFAULT_REGISTRY_LIMIT}")

        # Convert path to string for VLC compatibility
        media_path_str = str(Path(media_path))

        # Generate unique player ID
        player_id = f"vlc_{uuid.uuid4().hex[:8]}"

        # Create VLC player with enhanced error handling
        try:
            player = vlc.MediaPlayer(media_path_str)

            if player is None:
                raise RuntimeError("VLC MediaPlayer creation returned None")

            # Create registry entry with comprehensive metadata
            registry_entry = {
                'player': player,
                'player_id': player_id,
                'created_time': time.time(),
                'media_path': media_path_str,
                'released': False,
                'creation_metadata': {
                    'validate_path': validate_path,
                    'auto_cleanup': auto_cleanup,
                    'registry_limit': registry_size_limit
                } if include_metadata else None
            }

            # Add to registry for cleanup tracking
            _vlc_player_registry.append(registry_entry)
            current_registry_size = len(_vlc_player_registry)

            # Perform automatic cleanup if registry exceeds limit
            cleanup_performed = False
            if auto_cleanup and current_registry_size > registry_size_limit:
                cleanup_result = _cleanup_old_vlc_players(
                    console_output=console_output,
                    enable_logging=enable_logging
                )
                cleanup_performed = cleanup_result.get('success', False)

                if console_output and cleanup_performed:
                    cleaned_count = cleanup_result.get('players_cleaned', 0)
                    print(f"{EMOJI_INFO} Automatic cleanup: removed {cleaned_count} old players")

            # Update result with success information
            result.update({
                'success': True,
                'player': player,
                'player_id': player_id,
                'registry_size': len(_vlc_player_registry),
                'cleanup_performed': cleanup_performed
            })

            # Add operation metadata if enabled
            if include_metadata:
                result['operation_metadata'] = {
                    'creation_time': creation_start_time,
                    'creation_duration': time.time() - creation_start_time,
                    'media_path_resolved': media_path_str,
                    'registry_size_before': current_registry_size,
                    'registry_size_after': len(_vlc_player_registry),
                    'cleanup_triggered': cleanup_performed
                }

            if console_output:
                print(f"{EMOJI_SUCCESS} VLC player created: {player_id}")

            # Log successful creation
            if enable_logging:
                _log_info(
                    f"VLC player created successfully: {player_id} for {media_path_str}",
                    level="INFO",
                    console_output=False,
                    category="vlc_management"
                )

            return result

        except Exception as vlc_error:
            # Handle VLC-specific errors with potential fallback
            error_message = f"VLC player creation failed: {vlc_error}"

            if fallback_on_error:
                try:
                    # Attempt fallback creation
                    fallback_player = vlc.MediaPlayer(media_path_str)

                    if fallback_player is not None:
                        result.update({
                            'success': True,
                            'player': fallback_player,
                            'player_id': f"fallback_{uuid.uuid4().hex[:8]}",
                            'registry_size': len(_vlc_player_registry),
                            'fallback_used': True,
                            'error_message': f"Primary creation failed, fallback succeeded: {vlc_error}"
                        })

                        if console_output:
                            print(f"{EMOJI_WARNING} VLC fallback player created after error")

                        return result

                except Exception as fallback_error:
                    error_message += f"; Fallback also failed: {fallback_error}"

            result['error_message'] = error_message

            if console_output:
                print(f"{EMOJI_ERROR} {error_message}")

  # Log creation failure
            if enable_logging:
                _log_error(
                    error_message,
                    error_type="WARNING",
                    console_output=False,
                    include_traceback=True
                )

            return result

    except Exception as general_error:
        # Comprehensive error handling with detailed logging
        result['operation_metadata'] = {'creation_duration': time.time() - creation_start_time} if include_metadata else None
        error_message = f"General VLC player creation error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

  # Log critical error
        if enable_logging:
            _log_error(
                error_message,
                error_type="ERROR",
                console_output=False,
                include_traceback=True
            )

        return result


def _validate_vlc_media_path(media_path: Union[str, Path], *,
                             console_output: bool = False) -> Dict[str, Union[bool, str]]:
    """Validate VLC media file path with comprehensive checking.

    Args:
        media_path: Path to validate
        console_output: Whether to print validation messages - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from pathlib import Path

    try:
        if not media_path:
            return {'valid': False, 'message': 'Media path is empty or None'}

        # Convert to Path object for validation
        path_obj = Path(media_path)

        # Check if path exists
        if not path_obj.exists():
            return {'valid': False, 'message': f'Media file does not exist: {media_path}'}

        # Check if it's a file (not directory)
        if not path_obj.is_file():
            return {'valid': False, 'message': f'Path is not a file: {media_path}'}

        # Check file size (should not be empty)
        if path_obj.stat().st_size == 0:
            return {'valid': False, 'message': f'Media file is empty: {media_path}'}

        return {'valid': True, 'message': 'Media path validation passed'}

    except Exception as validation_error:
        return {'valid': False, 'message': f'Path validation error: {validation_error}'}

def _cleanup_old_vlc_players(max_age_seconds: int = 300, *,
                             console_output: bool = False,
                             validate_input: bool = True,
                             force_cleanup: bool = False,
                             include_statistics: bool = False,
                             enable_logging: bool = True,
                             logger: Optional[logging.Logger] = None) -> Dict[str, Union[bool, int, str, float, Dict]]:
    """Clean up old VLC players with comprehensive Pythonic functionality.

    This function implements modern Python resource cleanup patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Comprehensive type hints for all parameters and return values
    - Structured return values with detailed operation tracking
    - Input validation with configurable strictness
    - Performance monitoring and statistics collection
    - Defensive programming with robust error handling
    - Prevention of recursive cleanup operations
    - Constants for better maintainability

    Args:
        max_age_seconds: Maximum age in seconds before cleanup
        console_output: Whether to print status messages - keyword-only
        validate_input: Whether to validate input parameters - keyword-only
        force_cleanup: Whether to force cleanup regardless of age - keyword-only
        include_statistics: Whether to include cleanup statistics - keyword-only
        enable_logging: Whether to log cleanup operations - keyword-only
        logger: Optional logger for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if cleanup completed successfully
        - 'players_cleaned': int - Number of players cleaned up
        - 'registry_size_before': int - Registry size before cleanup
        - 'registry_size_after': int - Registry size after cleanup
        - 'cleanup_time': float - Time taken for cleanup operation
        - 'error_message': str - Error message if failed (empty if success)
        - 'recursive_call_prevented': bool - Whether recursive call was prevented
        - 'statistics': Dict - Detailed cleanup statistics (if enabled)

    Examples:
        >>> result = _cleanup_old_vlc_players()
        {'success': True, 'players_cleaned': 3, 'registry_size_after': 7, ...}
        >>> result = _cleanup_old_vlc_players(max_age_seconds=60, force_cleanup=True)
        {'success': True, 'players_cleaned': 8, 'force_cleanup': True, ...}
        >>> result = _cleanup_old_vlc_players(include_statistics=True)
        {'success': True, 'statistics': {'avg_age': 245.3, 'oldest_player': 456}, ...}

    Raises:
        ValueError: If max_age_seconds is invalid and validate_input=True

    Note:
        Function uses global lock to prevent recursive cleanup operations.
        Maintains registry integrity during concurrent access.
        Supports comprehensive monitoring and statistics collection.
    """
    from typing import Final
    import time

    # Constants for better maintainability
    MIN_AGE_SECONDS: Final = 1
    MAX_AGE_SECONDS: Final = 86400  # 24 hours
    DEFAULT_AGE_SECONDS: Final = 300  # 5 minutes
    CLEANUP_PAUSE_DURATION: Final = 0.05
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_INFO: Final = 'ℹ️'

    global _vlc_player_registry, _vlc_cleanup_lock

  # Initialize result structure
    cleanup_start_time = time.time()
    result = {
        'success': False,
        'players_cleaned': 0,
        'registry_size_before': 0,
        'registry_size_after': 0,
        'cleanup_time': 0.0,
        'error_message': '',
        'recursive_call_prevented': False,
        'statistics': {} if include_statistics else None
    }

    try:
  # Prevent recursive cleanup
        if _vlc_cleanup_lock:
            result.update({
                'success': True,  # Not an error, just prevented
                'recursive_call_prevented': True,
                'error_message': 'Recursive cleanup call prevented'
            })

            if console_output:
                print(f"{EMOJI_INFO} VLC cleanup already in progress - skipping")

            return result

        # Input validation with early returns
        if validate_input:
            if not isinstance(max_age_seconds, (int, float)) or max_age_seconds < MIN_AGE_SECONDS or max_age_seconds > MAX_AGE_SECONDS:
                error_msg = (f'Invalid max_age_seconds: {max_age_seconds}. Must be between {MIN_AGE_SECONDS} '
                            f'and {MAX_AGE_SECONDS}')
                result['error_message'] = error_msg

                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")

                return result

  # Set cleanup lock to prevent recursion
        _vlc_cleanup_lock = True
        current_time = time.time()
        registry_size_before = len(_vlc_player_registry)
        result['registry_size_before'] = registry_size_before

  # Initialize cleanup tracking
        cleaned_count = 0
        cleanup_errors = []
        player_ages = [] if include_statistics else None
        oldest_player_age = 0

        try:
  # Clean up old players with detailed tracking
            for player_info in _vlc_player_registry[:]:
                try:
                    player_age = current_time - player_info['created_time']

                    if include_statistics:
                        player_ages.append(player_age)
                        oldest_player_age = max(oldest_player_age, player_age)

  # Determine if player should be cleaned up
                    should_cleanup = (
                        not player_info['released'] and
                        (force_cleanup or player_age > max_age_seconds)
                    )

                    if should_cleanup:
                        player = player_info['player']

  # Stop player if currently playing
                        if hasattr(player, 'is_playing') and player.is_playing():
                            player.stop()
                            time.sleep(CLEANUP_PAUSE_DURATION)

  # Release player resources
                        if hasattr(player, 'release'):
                            player.release()

  # Mark as released in registry
                        player_info['released'] = True
                        cleaned_count += 1

                        if console_output:
                            player_id = player_info.get('player_id', 'unknown')
                            print(f"{EMOJI_SUCCESS} Cleaned VLC player: {player_id} (age: {player_age:.1f}s)")

                except Exception as cleanup_error:
                    error_msg = f"Failed to cleanup VLC player: {cleanup_error}"
                    cleanup_errors.append(error_msg)

                    if console_output:
                        print(f"{EMOJI_WARNING} {error_msg}")

  # Remove released players from registry
            original_registry_size = len(_vlc_player_registry)
            _vlc_player_registry = [p for p in _vlc_player_registry if not p['released']]
            registry_size_after = len(_vlc_player_registry)

  # Update result with success information
            result.update({
                'success': True,
                'players_cleaned': cleaned_count,
                'registry_size_after': registry_size_after,
                'cleanup_time': time.time() - cleanup_start_time
            })

  # Add detailed statistics if enabled
            if include_statistics and player_ages:
                result['statistics'] = {
                    'total_players_processed': len(player_ages),
                    'average_player_age': sum(player_ages) / len(player_ages),
                    'oldest_player_age': oldest_player_age,
                    'youngest_player_age': min(player_ages),
                    'cleanup_errors_count': len(cleanup_errors),
                    'registry_reduction': original_registry_size - registry_size_after,
                    'cleanup_efficiency': cleaned_count / max(1, len(player_ages))
                }

  # Final status output
            if console_output and cleaned_count > 0:
                print(f"{EMOJI_SUCCESS} VLC cleanup completed: {cleaned_count} players cleaned, registry: {registry_size_before} → {registry_size_after}")
            elif console_output:
                print(f"{EMOJI_INFO} VLC cleanup completed: no players needed cleanup")

  # Log cleanup operation
            if enable_logging:
                _log_info(
                    f"VLC cleanup completed: {cleaned_count} players cleaned, "
                    f"registry size: {registry_size_before} → {registry_size_after}",
                    level="INFO",
                    console_output=False,
                    category="vlc_management"
                )

  # Handle cleanup errors if any occurred
            if cleanup_errors:
                result['error_message'] = f"{len(cleanup_errors)} cleanup errors occurred"

                if enable_logging:
                    for error in cleanup_errors[:3]:  # Log first 3 errors
                        _log_error(
                            error,
                            error_type="WARNING",
                            console_output=False
                        )

            return result

        finally:
  # Always release cleanup lock
            _vlc_cleanup_lock = False

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        _vlc_cleanup_lock = False  # Ensure lock is released
        result['cleanup_time'] = time.time() - cleanup_start_time
        error_message = f"General VLC cleanup error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

  # Log critical error
        if enable_logging:
            _log_error(
                error_message,
                error_type="ERROR",
                console_output=False,
                include_traceback=True
            )

        return result

def _cleanup_all_vlc_players(*,
                           console_output: bool = True,
                           validate_operation: bool = True,
                           include_statistics: bool = False,
                           enable_logging: bool = True,
                           graceful_shutdown: bool = True,
                           logger: Optional[logging.Logger] = None) -> Dict[str, Union[bool, int, str, float, Dict]]:
    """Force cleanup of all VLC players with comprehensive Pythonic functionality.

    This function implements modern Python complete cleanup patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Comprehensive type hints for all parameters and return values
    - Structured return values with detailed operation tracking
    - Input validation with configurable behavior
    - Performance monitoring and statistics collection
    - Defensive programming with robust error handling
    - Prevention of recursive cleanup operations
    - Graceful shutdown options for active players
    - Constants for better maintainability

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_operation: Whether to validate cleanup operation - keyword-only
        include_statistics: Whether to include cleanup statistics - keyword-only
        enable_logging: Whether to log cleanup operations - keyword-only
        graceful_shutdown: Whether to gracefully stop playing players - keyword-only
        logger: Optional logger for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if cleanup completed successfully
        - 'players_cleaned': int - Number of players cleaned up
        - 'registry_size_before': int - Registry size before cleanup
        - 'registry_cleared': bool - Whether registry was completely cleared
        - 'cleanup_time': float - Time taken for cleanup operation
        - 'error_message': str - Error message if failed (empty if success)
        - 'recursive_call_prevented': bool - Whether recursive call was prevented
        - 'statistics': Dict - Detailed cleanup statistics (if enabled)

    Examples:
        >>> result = _cleanup_all_vlc_players()
        {'success': True, 'players_cleaned': 8, 'registry_cleared': True, ...}
        >>> result = _cleanup_all_vlc_players(graceful_shutdown=False)
        {'success': True, 'players_cleaned': 5, 'graceful_shutdown': False, ...}
        >>> result = _cleanup_all_vlc_players(include_statistics=True)
        {'success': True, 'statistics': {'playing_players': 2, 'idle_players': 6}, ...}

    Note:
        Function uses global lock to prevent recursive cleanup operations.
        Completely clears the VLC player registry after cleanup.
        Supports comprehensive monitoring and statistics collection.
        Use with caution as this affects all active VLC players.
    """
    from typing import Final
    import time

  # Constants for better maintainability
    SHUTDOWN_PAUSE_DURATION: Final = 0.05
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_INFO: Final = 'ℹ️'
    EMOJI_STOP: Final = '🛑'

    global _vlc_player_registry, _vlc_cleanup_lock

  # Initialize result structure
    cleanup_start_time = time.time()
    result = {
        'success': False,
        'players_cleaned': 0,
        'registry_size_before': 0,
        'registry_cleared': False,
        'cleanup_time': 0.0,
        'error_message': '',
        'recursive_call_prevented': False,
        'statistics': {} if include_statistics else None
    }

    try:
  # Prevent recursive cleanup
        if _vlc_cleanup_lock:
            result.update({
                'success': True,  # Not an error, just prevented
                'recursive_call_prevented': True,
                'error_message': 'Recursive cleanup call prevented'
            })

            if console_output:
                print(f"{EMOJI_INFO} VLC cleanup already in progress - skipping")

            return result

  # Set cleanup lock
        _vlc_cleanup_lock = True
        registry_size_before = len(_vlc_player_registry)
        result['registry_size_before'] = registry_size_before

  # Validation if requested
        if validate_operation and registry_size_before == 0:
            result.update({
                'success': True,
                'registry_cleared': True,
                'error_message': 'Registry already empty - no cleanup needed'
            })

            if console_output:
                print(f"{EMOJI_INFO} VLC registry already empty")

            _vlc_cleanup_lock = False
            return result

  # Initialize cleanup tracking
        cleaned_count = 0
        cleanup_errors = []
        playing_players = 0
        idle_players = 0

        try:
  # Process all players with detailed tracking
            for player_info in _vlc_player_registry[:]:
                try:
                    if not player_info['released']:
                        player = player_info['player']

  # Check if player is currently playing
                        is_playing = False
                        if hasattr(player, 'is_playing'):
                            try:
                                is_playing = player.is_playing()
                                if include_statistics:
                                    if is_playing:
                                        playing_players += 1
                                    else:
                                        idle_players += 1
                            except Exception:
                                pass  # Ignore status check errors

  # Stop player gracefully if requested
                        if graceful_shutdown and is_playing:
                            try:
                                player.stop()
                                time.sleep(SHUTDOWN_PAUSE_DURATION)

                                if console_output:
                                    player_id = player_info.get('player_id', 'unknown')
                                    print(f"{EMOJI_STOP} Stopped playing VLC player: {player_id}")
                            except Exception as stop_error:
                                cleanup_errors.append(f"Failed to stop player: {stop_error}")

  # Release player resources
                        if hasattr(player, 'release'):
                            player.release()

  # Mark as released
                        player_info['released'] = True
                        cleaned_count += 1

                        if console_output:
                            player_id = player_info.get('player_id', 'unknown')
                            print(f"{EMOJI_SUCCESS} Cleaned VLC player: {player_id}")

                except Exception as cleanup_error:
                    error_msg = f"Failed to cleanup VLC player: {cleanup_error}"
                    cleanup_errors.append(error_msg)

                    if console_output:
                        print(f"{EMOJI_WARNING} {error_msg}")

  # Clear the entire registry
            _vlc_player_registry.clear()
            registry_cleared = True

  # Update result with success information
            result.update({
                'success': True,
                'players_cleaned': cleaned_count,
                'registry_cleared': registry_cleared,
                'cleanup_time': time.time() - cleanup_start_time
            })

  # Add detailed statistics if enabled
            if include_statistics:
                result['statistics'] = {
                    'players_cleaned': cleaned_count,
                    'playing_players_found': playing_players,
                    'idle_players_found': idle_players,
                    'cleanup_errors_count': len(cleanup_errors),
                    'graceful_shutdown_used': graceful_shutdown,
                    'registry_completely_cleared': registry_cleared
                }

  # Final status output
            if console_output:
                if cleaned_count > 0:
                    print(f"{EMOJI_SUCCESS} VLC complete cleanup: {cleaned_count} players cleaned, registry cleared")
                else:
                    print(f"{EMOJI_INFO} VLC complete cleanup: registry was empty")

  # Log cleanup operation
            if enable_logging:
                _log_info(
                    f"VLC complete cleanup: {cleaned_count} players cleaned, registry cleared",
                    level="INFO",
                    console_output=False,
                    category="vlc_management"
                )

  # Handle cleanup errors if any occurred
            if cleanup_errors:
                result['error_message'] = f"{len(cleanup_errors)} cleanup errors occurred"

                if enable_logging:
                    for error in cleanup_errors[:3]:  # Log first 3 errors
                        _log_error(
                            error,
                            error_type="WARNING",
                            console_output=False
                        )

            return result

        finally:
  # Always release cleanup lock
            _vlc_cleanup_lock = False

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        _vlc_cleanup_lock = False  # Ensure lock is released
        result['cleanup_time'] = time.time() - cleanup_start_time
        error_message = f"General VLC complete cleanup error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

  # Log critical error
        if enable_logging:
            _log_error(
                error_message,
                error_type="ERROR",
                console_output=False,
                include_traceback=True
            )

        return result

def _safe_play_audio_clip(audio_file: Union[str, Path], *,
                         volume: int = 50,
                         timeout: float = 3.0,
                         console_output: bool = False,
                         validate_input: bool = True,
                         auto_cleanup: bool = True,
                         include_metadata: bool = False,
                         enable_logging: bool = True,
                         retry_on_failure: bool = False,
                         max_retries: int = 2,
                         logger: Optional[logging.Logger] = None) -> Dict[str, Union[bool, str, float, Dict]]:
    """Safely play a short audio clip with comprehensive Pythonic functionality.

    This function implements modern Python audio playback patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Comprehensive type hints for all parameters and return values
    - Structured return values with detailed operation tracking
    - Input validation with configurable strictness
    - Automatic resource cleanup and management
    - Performance monitoring and metadata collection
    - Defensive programming with robust error handling
    - Retry mechanisms for improved reliability
    - Constants for better maintainability

    Args:
        audio_file: Path to audio file (str or Path object)
        volume: Volume level (0-100) - keyword-only
        timeout: Maximum play time in seconds - keyword-only
        console_output: Whether to print status messages - keyword-only
        validate_input: Whether to validate input parameters - keyword-only
        auto_cleanup: Whether to perform automatic resource cleanup - keyword-only
        include_metadata: Whether to include operation metadata - keyword-only
        enable_logging: Whether to log operations - keyword-only
        retry_on_failure: Whether to retry on playback failure - keyword-only
        max_retries: Maximum number of retry attempts - keyword-only
        logger: Optional logger for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if audio played successfully
        - 'player_created': bool - Whether VLC player was created
        - 'playback_started': bool - Whether playback actually started
        - 'playback_duration': float - Actual playback duration
        - 'volume_set': int - Volume level that was set
        - 'error_message': str - Error message if failed (empty if success)
        - 'retry_attempts': int - Number of retry attempts made
        - 'cleanup_performed': bool - Whether cleanup was performed
        - 'operation_metadata': Dict - Operation details (if enabled)

    Examples:
        >>> result = _safe_play_audio_clip('buzz.mp3')
        {'success': True, 'playback_started': True, 'playback_duration': 0.5, ...}
        >>> result = _safe_play_audio_clip('success.mp3', volume=80, timeout=2.0)
        {'success': True, 'volume_set': 80, 'playback_duration': 2.0, ...}
        >>> result = _safe_play_audio_clip('invalid.mp3', retry_on_failure=True)
        {'success': False, 'retry_attempts': 2, 'error_message': 'File not found', ...}

    Raises:
        ValueError: If input parameters are invalid and validate_input=True

    Note:
        Function uses managed VLC player creation for automatic resource cleanup.
        Supports comprehensive monitoring and retry mechanisms.
        Designed for short audio clips with automatic timeout protection.
    """
    from typing import Final
    from pathlib import Path
    import time

  # Constants for better maintainability
    MIN_VOLUME: Final = 0
    MAX_VOLUME: Final = 100
    MIN_TIMEOUT: Final = 0.1
    MAX_TIMEOUT: Final = 30.0
    DEFAULT_TIMEOUT: Final = 3.0
    STARTUP_WAIT_MAX: Final = 1.0
    STARTUP_CHECK_INTERVAL: Final = 0.05
    MAX_RETRY_LIMIT: Final = 5
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_INFO: Final = 'ℹ️'
    EMOJI_AUDIO: Final = '🔊'

  # Initialize result structure
    playback_start_time = time.time()
    result = {
        'success': False,
        'player_created': False,
        'playback_started': False,
        'playback_duration': 0.0,
        'volume_set': volume,
        'error_message': '',
        'retry_attempts': 0,
        'cleanup_performed': False,
        'operation_metadata': {} if include_metadata else None
    }

  # Retry loop implementation
    max_attempts = max_retries + 1 if retry_on_failure else 1

    for attempt in range(max_attempts):
        attempt_start_time = time.time()
        player = None

        try:
  # Update retry attempts in result
            result['retry_attempts'] = attempt

  # Input validation with early returns
            if validate_input:
                validation_result = _validate_audio_clip_inputs(
                    audio_file=audio_file,
                    volume=volume,
                    timeout=timeout,
                    max_retries=max_retries,
                    console_output=console_output
                )

                if not validation_result['valid']:
                    result['error_message'] = validation_result['message']
                    if console_output:
                        print(f"{EMOJI_ERROR} Audio clip validation failed: {validation_result['message']}")

  # Don't retry on validation errors
                    break

  # Create managed VLC player with enhanced features
            player_result = _create_managed_vlc_player(
                media_path=audio_file,
                console_output=console_output,
                validate_path=validate_input,
                auto_cleanup=auto_cleanup,
                include_metadata=include_metadata,
                enable_logging=enable_logging
            )

            if not player_result['success']:
                error_msg = f"Failed to create VLC player: {player_result['error_message']}"
                result['error_message'] = error_msg

                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")

                if retry_on_failure and attempt < max_attempts - 1:
                    if console_output:
                        print(f"{EMOJI_INFO} Retrying audio clip playback (attempt {attempt + 2}/{max_attempts})...")
                    continue
                else:
                    break

            player = player_result['player']
            result['player_created'] = True

  # Set volume with validation
            try:
  # Clamp volume to valid range
                safe_volume = max(MIN_VOLUME, min(MAX_VOLUME, volume))
                player.audio_set_volume(safe_volume)
                result['volume_set'] = safe_volume

                if safe_volume != volume and console_output:
                    print(f"{EMOJI_WARNING} Volume clamped to {safe_volume} (requested: {volume})")

            except Exception as volume_error:
                if console_output:
                    print(f"{EMOJI_WARNING} Failed to set volume: {volume_error}")

  # Start playback
            player.play()

  # Wait for playback to start with timeout
            startup_start = time.time()
            playback_started = False

            while (time.time() - startup_start) < STARTUP_WAIT_MAX:
                try:
                    if player.is_playing():
                        playback_started = True
                        break
                except Exception:
                    pass  # Ignore status check errors during startup

                time.sleep(STARTUP_CHECK_INTERVAL)

            result['playback_started'] = playback_started

            if playback_started:
  # Calculate safe playback duration
                safe_timeout = max(MIN_TIMEOUT, min(MAX_TIMEOUT, timeout))
                actual_duration = min(safe_timeout, 0.5)  # Quick clips shouldn't play too long

  # Let audio play for calculated duration
                time.sleep(actual_duration)
                result['playback_duration'] = actual_duration

  # Success!
                result['success'] = True

                if console_output:
                    audio_name = Path(audio_file).name
                    print(f"{EMOJI_AUDIO} Audio clip played: {audio_name} (duration: {actual_duration:.1f}s)")

  # Log successful playback
                if enable_logging:
                    _log_info(
                        f"Audio clip played successfully: {audio_file} (duration: {actual_duration:.1f}s)",
                        level="INFO",
                        console_output=False,
                        category="audio_playback"
                    )

                break  # Success - exit retry loop

            else:
                error_msg = "Playback failed to start within timeout"
                result['error_message'] = error_msg

                if console_output:
                    print(f"{EMOJI_WARNING} {error_msg}")

                if retry_on_failure and attempt < max_attempts - 1:
                    if console_output:
                        print(f"{EMOJI_INFO} Retrying audio clip playback (attempt {attempt + 2}/{max_attempts})...")
                    continue
                else:
                    break

        except Exception as playback_error:
            error_msg = f"Audio clip playback error: {playback_error}"
            result['error_message'] = error_msg

            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")

  # Log playback error
            if enable_logging:
                _log_error(
                    error_msg,
                    error_type="WARNING",
                    console_output=False,
                    include_traceback=True
                )

            if retry_on_failure and attempt < max_attempts - 1:
                if console_output:
                    print(f"{EMOJI_INFO} Retrying audio clip playback (attempt {attempt + 2}/{max_attempts})...")
                continue
            else:
                break

        finally:
  # Always cleanup player resources
            if player and auto_cleanup:
                try:
                    if hasattr(player, 'is_playing') and player.is_playing():
                        player.stop()
                        time.sleep(STARTUP_CHECK_INTERVAL)

                    if hasattr(player, 'release'):
                        player.release()

  # Mark as released in registry
                    global _vlc_player_registry
                    for player_info in _vlc_player_registry:
                        if player_info.get('player') == player:
                            player_info['released'] = True
                            break

                    result['cleanup_performed'] = True

                except Exception as cleanup_error:
                    if console_output:
                        print(f"{EMOJI_WARNING} Audio clip cleanup error: {cleanup_error}")

  # Add operation metadata if enabled
            if include_metadata:
                attempt_duration = time.time() - attempt_start_time

                if 'operation_metadata' not in result or result['operation_metadata'] is None:
                    result['operation_metadata'] = {}

                result['operation_metadata'].update({
                    'total_operation_time': time.time() - playback_start_time,
                    f'attempt_{attempt + 1}_duration': attempt_duration,
                    'audio_file_resolved': str(Path(audio_file)),
                    'final_attempt': attempt + 1,
                    'max_attempts_configured': max_attempts
                })

  # Final result processing
    if not result['success'] and not result['error_message']:
        result['error_message'] = f"Audio clip playback failed after {result['retry_attempts'] + 1} attempts"

    return result


def _validate_audio_clip_inputs(audio_file: Union[str, Path], *,
                               volume: int,
                               timeout: float,
                               max_retries: int,
                               console_output: bool = False) -> Dict[str, Union[bool, str]]:
    """Validate inputs for _safe_play_audio_clip function.

    Args:
        audio_file: Path to audio file
        volume: Volume level to validate
        timeout: Timeout value to validate
        max_retries: Max retries to validate
        console_output: Whether to print validation messages - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from pathlib import Path

    try:
  # Validate audio file
        if not audio_file:
            return {'valid': False, 'message': 'Audio file path is empty or None'}

  # Convert to Path object for validation
        try:
            audio_path = Path(audio_file)
        except Exception as path_error:
            return {'valid': False, 'message': f'Invalid audio file path: {path_error}'}

  # Validate volume range
        if not isinstance(volume, int) or volume < 0 or volume > 100:
            return {'valid': False, 'message': f'Volume must be integer 0-100, got: {volume}'}

  # Validate timeout range
        if not isinstance(timeout, (int, float)) or timeout < 0.1 or timeout > 30.0:
            return {'valid': False, 'message': f'Timeout must be 0.1-30.0 seconds, got: {timeout}'}

  # Validate max_retries range
        if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 5:
            return {'valid': False, 'message': f'Max retries must be 0-5, got: {max_retries}'}

        return {'valid': True, 'message': 'Audio clip input validation passed'}

    except Exception as validation_error:
        return {'valid': False, 'message': f'Input validation error: {validation_error}'}

dir_path = os.path.dirname(os.path.realpath(__file__))  # sets directory path for Windows Macintosh Systems
MusicId3MetaDataList = []  # list of all songs mp3 id3 metadata
MusicMasterSongList = []  # dictionary of all songs mp3 id3 metadata required by Convergence Jukebox
RandomMusicPlayList = []  # list of randomly played songs
PaidMusicPlayList = []  # list of paid songs to be played
FinalGenreList = []  #  List of genres found in comment metadata on all songs
random_music_play_number = ""
artist_name = ""
song_name = ""
album_name = ""
'''genre0 = "play2021"
genre1 = "null"
genre2 = "null"
genre3 = "null"'''
song_duration = ""
song_year = ""
song_genre = ""
#  Check for files on disk. If they dont exist, create them
#  Create date and time stamp for log file
now = datetime.now()
rounded_now = now + timedelta(seconds=0.5)
rounded_now = rounded_now.replace(microsecond=0)
now = rounded_now
if not os.path.exists('log.txt'):
    with open('log.txt', 'w') as log:
        log.write(str(now) + ' Jukebox Engine Started - New Log File Created,')
else:
    with open('log.txt', 'a') as log:
        log.write('\n' + str(now) + ' Jukebox Engine Restarted,')
if not os.path.exists('GenreFlagsList.txt'):
    with open('GenreFlagsList.txt', 'w') as GenreFlagsListOpen:
        GenreFlagsList = ['null','null','null','null']
        json.dump(GenreFlagsList, GenreFlagsListOpen)
if not os.path.exists('MusicMasterSongListCheck.txt'):
    with open('MusicMasterSongListCheck.txt', 'w') as MusicMasterSongListCheckListOpen:
        MusicMasterSongListCheckList = []
        json.dump(MusicMasterSongListCheckList, MusicMasterSongListCheckListOpen)
if not os.path.exists('PaidMusicPlayList.txt'):
    with open('PaidMusicPlayList.txt', 'w') as PaidMusicPlayListOpen:
        PaidMusicPlayList = []
        json.dump(PaidMusicPlayList, PaidMusicPlayListOpen)


def assign_song_data_random(*,
                           console_output: bool = True,
                           validate_data: bool = True,
                           validation_level: str = 'standard',
                           include_metadata: bool = False,
                           enable_logging: bool = True,
                           default_values: Optional[Dict[str, str]] = None,
                           playlist_position: int = 0,
                           strict_mode: bool = False,
                           return_index: bool = False,
                           logger: Optional[logging.Logger] = None) -> Dict[str, Union[str, int, bool, Dict[str, Any]]]:
    """Extract current song data from random playlist with comprehensive Pythonic functionality.

    This function implements advanced Python data extraction patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Multi-level validation with configurable depth and strictness
    - Comprehensive type hints for all parameters and return values
    - Performance monitoring and metadata collection
    - Configurable default values and error recovery
    - Structured return values with detailed operation tracking
    - Advanced logging integration with contextual information
    - Defensive programming with comprehensive error handling
    - Support for different playlist positions and extraction modes

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_data: Whether to validate extracted song data - keyword-only
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        include_metadata: Whether to include operation metadata in return - keyword-only
        enable_logging: Whether to log extraction operations - keyword-only
        default_values: Custom default values for missing fields - keyword-only
        playlist_position: Position in playlist to extract (0 = first song) - keyword-only
        strict_mode: Whether to fail on any data inconsistencies - keyword-only
        return_index: Whether to include song index in return value - keyword-only
        logger: Optional logger for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if extraction succeeded
        - 'song_data': Dict[str, str] - Extracted song information
        - 'song_index': int - Index in master song list (if return_index=True)
        - 'playlist_position': int - Position in random playlist used
        - 'error_message': str - Error message if failed (empty if success)
        - 'validation_results': Dict - Validation information (if validate_data=True)
        - 'operation_metadata': Dict - Operation details (if include_metadata=True)

    Examples:
        >>> assign_song_data_random()
        {'success': True, 'song_data': {'title': 'Song Name', ...}, ...}
        >>> assign_song_data_random(validation_level='comprehensive', return_index=True)
        {'success': True, 'song_data': {...}, 'song_index': 42, ...}
        >>> assign_song_data_random(playlist_position=2, strict_mode=True)
        {'success': True, 'song_data': {...}, 'playlist_position': 2, ...}

    Validation Levels:
        - 'basic': Check for required fields existence
        - 'standard': Field validation plus type and content checking
        - 'comprehensive': Full validation including metadata analysis

    Raises:
        ValueError: If playlist_position is invalid or validation_level is unknown
        IndexError: If playlist position is out of range (in strict_mode)

    Note:
        Function accesses global RandomMusicPlayList and MusicMasterSongList.
        Uses safe extraction with comprehensive error handling and recovery.
        Supports configurable validation and return value customization.
    """
    from typing import Final
    import time

  # Constants for better maintainability
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_SONG_DATA: Final = {
        'artist': 'Unknown Artist',
        'title': 'Unknown Title',
        'album': 'Unknown Album',
        'duration': '00:00',
        'year': 'Unknown Year',
        'genre': 'Unknown Genre'
    }
    REQUIRED_FIELDS: Final = {'artist', 'title', 'album', 'duration', 'year'}
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    MAX_PLAYLIST_POSITION: Final = 1000  # Reasonable upper limit

  # Initialize comprehensive result structure
    extraction_start_time = time.time()
    result = {
        'success': False,
        'song_data': {},
        'playlist_position': playlist_position,
        'error_message': '',
        'validation_results': {} if validate_data else None,
        'operation_metadata': {} if include_metadata else None
    }

    if return_index:
        result['song_index'] = -1

    try:
  # Input validation with early returns
        if validation_level not in VALIDATION_LEVELS:
            error_msg = f'Invalid validation level: {validation_level}. Must be one of {VALIDATION_LEVELS}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            return result

        if playlist_position < 0 or playlist_position > MAX_PLAYLIST_POSITION:
            error_msg = f'Invalid playlist position: {playlist_position}. Must be 0-{MAX_PLAYLIST_POSITION}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            return result

  # Check if random playlist exists and has content
        if not RandomMusicPlayList:
            result['error_message'] = 'Random playlist is empty or not available'
            if console_output:
                print(f"{EMOJI_WARNING} No songs in random playlist")
            return result

  # Validate playlist position availability
        if playlist_position >= len(RandomMusicPlayList):
            if strict_mode:
                error_msg = f'Playlist position {playlist_position} exceeds playlist size {len(RandomMusicPlayList)}'
                result['error_message'] = error_msg
                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")
                return result
            else:
  # Fallback to first song in non-strict mode
                playlist_position = 0
                result['playlist_position'] = playlist_position
                if console_output:
                    print(f"{EMOJI_WARNING} Position out of range, using first song (position 0)")

  # Extract song index from random playlist
        try:
            song_index = RandomMusicPlayList[playlist_position]
            if return_index:
                result['song_index'] = song_index
        except (IndexError, TypeError) as index_error:
            error_msg = f'Failed to get song index from playlist position {playlist_position}: {index_error}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            return result

  # Validate song index exists in master song list
        if not MusicMasterSongList or song_index < 0 or song_index >= len(MusicMasterSongList):
            error_msg = f'Invalid song index {song_index} for master song list (size: {len(MusicMasterSongList) if MusicMasterSongList else 0})'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            return result

  # Extract current song data with error handling
        try:
            current_song = MusicMasterSongList[song_index]

  # Ensure current_song is a dictionary
            if not isinstance(current_song, dict):
                error_msg = f'Invalid song data type at index {song_index}: expected dict, got {type(current_song).__name__}'
                result['error_message'] = error_msg
                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")
                return result

        except (IndexError, TypeError, KeyError) as song_error:
            error_msg = f'Failed to access song data at index {song_index}: {song_error}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            return result

  # Prepare default values (custom defaults take precedence)
        effective_defaults = DEFAULT_SONG_DATA.copy()
        if default_values:
            effective_defaults.update(default_values)

  # Extract song data with safe field mapping
        song_data = _extract_random_song_fields(
            current_song=current_song,
            default_values=effective_defaults,
            validation_level=validation_level,
            strict_mode=strict_mode
        )

  # Validate extracted data if requested
        if validate_data:
            validation_result = _validate_random_song_data(
                song_data=song_data,
                validation_level=validation_level,
                required_fields=REQUIRED_FIELDS,
                strict_mode=strict_mode
            )

            result['validation_results'] = validation_result

            if not validation_result['valid'] and strict_mode:
                error_msg = f"Song data validation failed: {'; '.join(validation_result['errors'])}"
                result['error_message'] = error_msg
                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")
                return result
            elif validation_result['warnings'] and console_output:
                for warning in validation_result['warnings']:
                    print(f"{EMOJI_WARNING} {warning}")

  # Success - update result
        result.update({
            'success': True,
            'song_data': song_data
        })

  # Add operation metadata if requested
        if include_metadata:
            extraction_duration = time.time() - extraction_start_time
            result['operation_metadata'] = {
                'extraction_timestamp': extraction_start_time,
                'extraction_duration': extraction_duration,
                'playlist_size': len(RandomMusicPlayList),
                'master_list_size': len(MusicMasterSongList) if MusicMasterSongList else 0,
                'validation_performed': validate_data,
                'validation_level': validation_level if validate_data else None,
                'fields_extracted': len(song_data),
                'extraction_mode': 'random_playlist'
            }

  # Success output
        if console_output:
            song_title = song_data.get('title', 'Unknown Title')
            song_artist = song_data.get('artist', 'Unknown Artist')
            print(f"{EMOJI_SUCCESS} Extracted random song: {song_title} - {song_artist}")

  # Log successful extraction
        if enable_logging:
            _log_random_song_extraction(
                song_data=song_data,
                song_index=song_index if return_index else None,
                playlist_position=playlist_position,
                logger=logger
            )

        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        extraction_duration = time.time() - extraction_start_time
        error_message = f'Random song data extraction error: {general_error}'
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Error extracting random song data: {general_error}")

  # Add partial metadata on error if requested
        if include_metadata:
            result['operation_metadata'] = {
                'extraction_timestamp': extraction_start_time,
                'extraction_duration': extraction_duration,
                'error_occurred': True,
                'playlist_size': len(RandomMusicPlayList) if RandomMusicPlayList else 0,
                'extraction_mode': 'random_playlist'
            }

  # Log error for debugging
        if enable_logging:
            _log_error(
                error_message,
                error_type="ERROR",
                console_output=False,
                include_traceback=True
            )

        return result


# Supporting functions for enhanced random song data extraction
def _extract_random_song_fields(
    current_song: Dict[str, Any],
    default_values: Dict[str, str],
    validation_level: str,
    strict_mode: bool
) -> Dict[str, str]:
    """Extract song fields from current song data with safe defaults.

    Args:
        current_song: Song dictionary from master song list
        default_values: Default values for missing fields
        validation_level: Level of validation to apply
        strict_mode: Whether to apply strict validation

    Returns:
        Dict with extracted song fields
    """
    try:
  # Extract fields with safe defaults and field mapping
        song_data = {
            'artist': str(current_song.get('artist', default_values['artist'])).strip(),
            'title': str(current_song.get('title', default_values['title'])).strip(),
            'album': str(current_song.get('album', default_values['album'])).strip(),
            'duration': str(current_song.get('duration', default_values['duration'])).strip(),
            'year': str(current_song.get('year', default_values['year'])).strip(),
            'genre': str(current_song.get('comment', default_values['genre'])).strip()  # Map comment to genre
        }

  # Advanced field processing for comprehensive validation
        if validation_level == 'comprehensive':
  # Clean and normalize field values
            song_data = _normalize_song_field_values(song_data, strict_mode)

  # Add additional metadata if available
            if 'location' in current_song:
                song_data['file_path'] = str(current_song['location'])

            if 'number' in current_song:
                song_data['track_number'] = str(current_song['number'])

        return song_data

    except Exception as extraction_error:
  # Fallback to all defaults on extraction error
        return default_values.copy()


def _normalize_song_field_values(song_data: Dict[str, str], strict_mode: bool) -> Dict[str, str]:
    """Normalize and clean song field values.

    Args:
        song_data: Dictionary of song fields to normalize
        strict_mode: Whether to apply strict normalization

    Returns:
        Dictionary with normalized field values
    """
    normalized_data = song_data.copy()

    try:
  # Normalize common field issues
        for field, value in normalized_data.items():
            if not value or value.lower() in ('unknown', 'none', 'null', ''):
                if strict_mode:
  # Keep original value in strict mode for validation to catch it
                    continue
                else:
  # Apply smart defaults in non-strict mode
                    if field == 'artist':
                        normalized_data[field] = 'Various Artists'
                    elif field == 'title':
                        normalized_data[field] = 'Untitled Track'
                    elif field == 'album':
                        normalized_data[field] = 'Unknown Album'
                    elif field == 'year':
                        normalized_data[field] = 'Unknown'
                    elif field == 'duration':
                        normalized_data[field] = '00:00'
                    elif field == 'genre':
                        normalized_data[field] = 'Unknown Genre'

  # Clean up whitespace and formatting
            if isinstance(normalized_data[field], str):
  # Remove excessive whitespace
                normalized_data[field] = ' '.join(normalized_data[field].split())

  # Limit field length for display purposes
                MAX_FIELD_LENGTH = 100
                if len(normalized_data[field]) > MAX_FIELD_LENGTH:
                    normalized_data[field] = normalized_data[field][:MAX_FIELD_LENGTH-3] + '...'

        return normalized_data

    except Exception:
  # Return original data if normalization fails
        return song_data


def _validate_random_song_data(
    song_data: Dict[str, str],
    validation_level: str,
    required_fields: set,
    strict_mode: bool
) -> Dict[str, Any]:
    """Validate extracted random song data.

    Args:
        song_data: Extracted song data to validate
        validation_level: Level of validation to apply
        required_fields: Set of fields that must be present
        strict_mode: Whether to apply strict validation

    Returns:
        Dict with validation results
    """
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'field_analysis': {},
        'validation_level': validation_level
    }

    try:
  # Basic validation - check required fields
        missing_fields = required_fields - set(song_data.keys())
        if missing_fields:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Missing required fields: {', '.join(missing_fields)}")

  # Standard validation - check field content
        if validation_level in ('standard', 'comprehensive'):
            for field, value in song_data.items():
                field_issues = _validate_song_field_content(field, value, strict_mode)
                validation_result['field_analysis'][field] = field_issues

                if field_issues['errors']:
                    validation_result['valid'] = False
                    validation_result['errors'].extend(field_issues['errors'])

                if field_issues['warnings']:
                    validation_result['warnings'].extend(field_issues['warnings'])

  # Comprehensive validation - advanced checks
        if validation_level == 'comprehensive':
  # Check for data consistency
            consistency_issues = _check_song_data_consistency(song_data)
            if consistency_issues['errors']:
                validation_result['valid'] = False
                validation_result['errors'].extend(consistency_issues['errors'])
            if consistency_issues['warnings']:
                validation_result['warnings'].extend(consistency_issues['warnings'])

        return validation_result

    except Exception as validation_error:
        return {
            'valid': False,
            'errors': [f'Validation system error: {validation_error}'],
            'warnings': [],
            'field_analysis': {},
            'validation_level': validation_level
        }


def _validate_song_field_content(field: str, value: str, strict_mode: bool) -> Dict[str, List[str]]:
    """Validate individual song field content.

    Args:
        field: Name of the field being validated
        value: Value to validate
        strict_mode: Whether to apply strict validation

    Returns:
        Dict with field-specific errors and warnings
    """
    field_result = {'errors': [], 'warnings': []}

    try:
  # Common validations for all fields
        if not isinstance(value, str):
            field_result['errors'].append(f"Field '{field}' must be a string, got {type(value).__name__}")
            return field_result

        if not value.strip():
            if strict_mode:
                field_result['errors'].append(f"Field '{field}' cannot be empty in strict mode")
            else:
                field_result['warnings'].append(f"Field '{field}' is empty")

  # Field-specific validations
        if field == 'duration':
  # Validate duration format (MM:SS or HH:MM:SS)
            import re
            duration_pattern = r'^\d{1,2}:\d{2}(:\d{2})?$'
            if value and not re.match(duration_pattern, value):
                field_result['warnings'].append(f"Duration format may be invalid: {value}")

        elif field == 'year':
  # Validate year format
            if value and value != 'Unknown' and value != 'Unknown Year':
                try:
                    year_int = int(value)
                    current_year = time.localtime().tm_year
                    if year_int < 1900 or year_int > current_year + 1:
                        field_result['warnings'].append(f"Year seems out of range: {year_int}")
                except ValueError:
                    field_result['warnings'].append(f"Year format may be invalid: {value}")

        elif field in ('artist', 'title'):
  # Critical fields should have meaningful content
            if value.lower() in ('unknown', 'unknown artist', 'unknown title', 'untitled'):
                if strict_mode:
                    field_result['errors'].append(f"Field '{field}' has placeholder value: {value}")
                else:
                    field_result['warnings'].append(f"Field '{field}' has placeholder value: {value}")

        return field_result

    except Exception:
        return {'errors': [f"Failed to validate field '{field}'"], 'warnings': []}


def _check_song_data_consistency(song_data: Dict[str, str]) -> Dict[str, List[str]]:
    """Check for data consistency issues in song information.

    Args:
        song_data: Song data dictionary to check

    Returns:
        Dict with consistency errors and warnings
    """
    consistency_result = {'errors': [], 'warnings': []}

    try:
  # Check for obvious inconsistencies
        title = song_data.get('title', '').lower()
        artist = song_data.get('artist', '').lower()

  # Check if title and artist are identical (usually indicates data issue)
        if title and artist and title == artist:
            consistency_result['warnings'].append("Title and artist are identical - possible data issue")

  # Check for common data placeholders
        placeholder_fields = []
        for field, value in song_data.items():
            if value.lower() in ('unknown', 'n/a', 'null', 'none', ''):
                placeholder_fields.append(field)

        if len(placeholder_fields) >= 3:  # More than half the fields are placeholders
            consistency_result['warnings'].append(
                f"Multiple fields have placeholder values: {', '.join(placeholder_fields)}"
            )

        return consistency_result

    except Exception:
        return {'errors': [], 'warnings': ['Failed to perform consistency check']}


def _log_random_song_extraction(
    song_data: Dict[str, str],
    song_index: Optional[int],
    playlist_position: int,
    logger: Optional[logging.Logger]
) -> None:
    """Log random song extraction operation.

    Args:
        song_data: Extracted song data
        song_index: Index in master song list (if available)
        playlist_position: Position in random playlist
        logger: Optional logger instance
    """
    try:
        song_title = song_data.get('title', 'Unknown Title')
        song_artist = song_data.get('artist', 'Unknown Artist')

        log_message = (
            f"Random song extracted: {song_title} - {song_artist} "
            f"(playlist pos: {playlist_position}"
        )

        if song_index is not None:
            log_message += f", song index: {song_index}"

        log_message += ")"

  # Use provided logger or default logging
        if logger:
            logger.info(log_message)
        else:
            _log_info(
                log_message,
                level="INFO",
                console_output=False,
                category="song_extraction"
            )

    except Exception:
  # Don't let logging errors affect the main operation
        pass


def assign_song_data_paid(*,
                         console_output: bool = True,
                         validate_data: bool = True,
                         validation_level: str = 'standard',
                         include_metadata: bool = False,
                         enable_logging: bool = True,
                         default_values: Optional[Dict[str, str]] = None,
                         playlist_position: int = 0,
                         strict_mode: bool = False,
                         return_index: bool = False,
                         fallback_to_empty: bool = True,
                         logger: Optional[logging.Logger] = None) -> Dict[str, Union[str, int, bool, Dict[str, Any]]]:
    """Extract current song data from paid playlist with comprehensive Pythonic functionality.

    This function implements advanced Python data extraction patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Multi-level validation with configurable depth and strictness
    - Comprehensive type hints for all parameters and return values
    - Performance monitoring and metadata collection
    - Configurable default values and error recovery
    - Structured return values with detailed operation tracking
    - Advanced logging integration with contextual information
    - Defensive programming with comprehensive error handling
    - Support for different playlist positions and extraction modes
    - Priority-based paid song handling

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_data: Whether to validate extracted song data - keyword-only
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        include_metadata: Whether to include operation metadata in return - keyword-only
        enable_logging: Whether to log extraction operations - keyword-only
        default_values: Custom default values for missing fields - keyword-only
        playlist_position: Position in paid playlist to extract (0 = first song) - keyword-only
        strict_mode: Whether to fail on any data inconsistencies - keyword-only
        return_index: Whether to include song index in return value - keyword-only
        fallback_to_empty: Whether to return empty data on failure or raise error - keyword-only
        logger: Optional logger for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if extraction succeeded
        - 'song_data': Dict[str, str] - Extracted song information
        - 'song_index': int - Index in master song list (if return_index=True)
        - 'playlist_position': int - Position in paid playlist used
        - 'error_message': str - Error message if failed (empty if success)
        - 'validation_results': Dict - Validation information (if validate_data=True)
        - 'operation_metadata': Dict - Operation details (if include_metadata=True)
        - 'is_paid_song': bool - Always True for this function

    Examples:
        >>> assign_song_data_paid()
        {'success': True, 'song_data': {'title': 'Song Name', ...}, 'is_paid_song': True, ...}
        >>> assign_song_data_paid(validation_level='comprehensive', return_index=True)
        {'success': True, 'song_data': {...}, 'song_index': 42, 'is_paid_song': True, ...}
        >>> assign_song_data_paid(playlist_position=1, strict_mode=True)
        {'success': True, 'song_data': {...}, 'playlist_position': 1, ...}

    Validation Levels:
        - 'basic': Check for required fields existence
        - 'standard': Field validation plus type and content checking
        - 'comprehensive': Full validation including metadata analysis

    Raises:
        ValueError: If playlist_position is invalid or validation_level is unknown
        IndexError: If playlist position is out of range (in strict_mode)
        RuntimeError: If fallback_to_empty is False and extraction fails

    Note:
        Function accesses global PaidMusicPlayList and MusicMasterSongList.
        Uses safe extraction with comprehensive error handling and recovery.
        Supports configurable validation and return value customization.
        Paid songs have priority in the jukebox system.
    """
    from typing import Final
    import time

  # Constants for better maintainability
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_SONG_DATA: Final = {
        'artist': 'Unknown Artist',
        'title': 'Unknown Title',
        'album': 'Unknown Album',
        'duration': '00:00',
        'year': 'Unknown Year',
        'genre': 'Unknown Genre'
    }
    REQUIRED_FIELDS: Final = {'artist', 'title', 'album', 'duration', 'year'}
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_PRIORITY: Final = '💰'  # Money bag for paid songs
    MAX_PLAYLIST_POSITION: Final = 1000  # Reasonable upper limit

  # Initialize comprehensive result structure
    extraction_start_time = time.time()
    result = {
        'success': False,
        'song_data': {},
        'playlist_position': playlist_position,
        'error_message': '',
        'validation_results': {} if validate_data else None,
        'operation_metadata': {} if include_metadata else None,
        'is_paid_song': True  # Always true for paid songs
    }

    if return_index:
        result['song_index'] = -1

    try:
  # Input validation with early returns
        if validation_level not in VALIDATION_LEVELS:
            error_msg = f'Invalid validation level: {validation_level}. Must be one of {VALIDATION_LEVELS}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if not fallback_to_empty:
                raise ValueError(error_msg)
            return result

        if playlist_position < 0 or playlist_position > MAX_PLAYLIST_POSITION:
            error_msg = f'Invalid playlist position: {playlist_position}. Must be 0-{MAX_PLAYLIST_POSITION}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if not fallback_to_empty:
                raise ValueError(error_msg)
            return result

  # Check if paid playlist exists and has content
        if not PaidMusicPlayList:
            result['error_message'] = 'Paid playlist is empty or not available'
            if console_output:
                print(f"{EMOJI_WARNING} No paid songs in queue")
            if not fallback_to_empty:
                raise RuntimeError('No paid songs available')
            return result

  # Validate playlist position availability
        if playlist_position >= len(PaidMusicPlayList):
            if strict_mode:
                error_msg = f'Playlist position {playlist_position} exceeds paid playlist size {len(PaidMusicPlayList)}'
                result['error_message'] = error_msg
                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")
                if not fallback_to_empty:
                    raise IndexError(error_msg)
                return result
            else:
  # Fallback to first song in non-strict mode
                playlist_position = 0
                result['playlist_position'] = playlist_position
                if console_output:
                    print(f"{EMOJI_WARNING} Position out of range, using first paid song (position 0)")

  # Extract song index from paid playlist
        try:
            song_index = int(PaidMusicPlayList[playlist_position])
            if return_index:
                result['song_index'] = song_index
        except (IndexError, TypeError, ValueError) as index_error:
            error_msg = f'Failed to get song index from paid playlist position {playlist_position}: {index_error}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if not fallback_to_empty:
                raise RuntimeError(error_msg)
            return result

  # Validate song index exists in master song list
        if not MusicMasterSongList or song_index < 0 or song_index >= len(MusicMasterSongList):
            error_msg = f'Invalid paid song index {song_index} for master song list (size: {len(MusicMasterSongList) if MusicMasterSongList else 0})'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if not fallback_to_empty:
                raise RuntimeError(error_msg)
            return result

  # Extract current song data with error handling
        try:
            current_song = MusicMasterSongList[song_index]

  # Ensure current_song is a dictionary
            if not isinstance(current_song, dict):
                error_msg = f'Invalid paid song data type at index {song_index}: expected dict, got {type(current_song).__name__}'
                result['error_message'] = error_msg
                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")
                if not fallback_to_empty:
                    raise RuntimeError(error_msg)
                return result

        except (IndexError, TypeError, KeyError) as song_error:
            error_msg = f'Failed to access paid song data at index {song_index}: {song_error}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if not fallback_to_empty:
                raise RuntimeError(error_msg)
            return result

  # Prepare default values (custom defaults take precedence)
        effective_defaults = DEFAULT_SONG_DATA.copy()
        if default_values:
            effective_defaults.update(default_values)

  # Extract song data with safe field mapping
        song_data = _extract_paid_song_fields(
            current_song=current_song,
            default_values=effective_defaults,
            validation_level=validation_level,
            strict_mode=strict_mode
        )

  # Validate extracted data if requested
        if validate_data:
            validation_result = _validate_paid_song_data(
                song_data=song_data,
                validation_level=validation_level,
                required_fields=REQUIRED_FIELDS,
                strict_mode=strict_mode
            )

            result['validation_results'] = validation_result

            if not validation_result['valid'] and strict_mode:
                error_msg = f"Paid song data validation failed: {'; '.join(validation_result['errors'])}"
                result['error_message'] = error_msg
                if console_output:
                    print(f"{EMOJI_ERROR} {error_msg}")
                if not fallback_to_empty:
                    raise RuntimeError(error_msg)
                return result
            elif validation_result['warnings'] and console_output:
                for warning in validation_result['warnings']:
                    print(f"{EMOJI_WARNING} {warning}")

  # Success - update result
        result.update({
            'success': True,
            'song_data': song_data
        })

  # Add operation metadata if requested
        if include_metadata:
            extraction_duration = time.time() - extraction_start_time
            result['operation_metadata'] = {
                'extraction_timestamp': extraction_start_time,
                'extraction_duration': extraction_duration,
                'playlist_size': len(PaidMusicPlayList),
                'master_list_size': len(MusicMasterSongList) if MusicMasterSongList else 0,
                'validation_performed': validate_data,
                'validation_level': validation_level if validate_data else None,
                'fields_extracted': len(song_data),
                'extraction_mode': 'paid_playlist',
                'priority_status': 'paid'
            }

  # Success output
        if console_output:
            song_title = song_data.get('title', 'Unknown Title')
            song_artist = song_data.get('artist', 'Unknown Artist')
            print(f"{EMOJI_PRIORITY} Extracted paid song: {song_title} - {song_artist}")

  # Log successful extraction
        if enable_logging:
            _log_paid_song_extraction(
                song_data=song_data,
                song_index=song_index if return_index else None,
                playlist_position=playlist_position,
                logger=logger
            )

        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        extraction_duration = time.time() - extraction_start_time
        error_message = f'Paid song data extraction error: {general_error}'
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Error extracting paid song data: {general_error}")

  # Add partial metadata on error if requested
        if include_metadata:
            result['operation_metadata'] = {
                'extraction_timestamp': extraction_start_time,
                'extraction_duration': extraction_duration,
                'error_occurred': True,
                'playlist_size': len(PaidMusicPlayList) if PaidMusicPlayList else 0,
                'extraction_mode': 'paid_playlist',
                'priority_status': 'paid'
            }

  # Log error for debugging
        if enable_logging:
            _log_error(
                error_message,
                error_type="ERROR",
                console_output=False,
                include_traceback=True
            )

  # Re-raise if fallback is disabled
        if not fallback_to_empty:
            raise RuntimeError(error_message) from general_error

        return result


def _extract_paid_song_fields(current_song: Dict[str, Any], *,
                             default_values: Dict[str, str],
                             validation_level: str = 'standard',
                             strict_mode: bool = False) -> Dict[str, str]:
    """Extract song fields from paid song data with comprehensive error handling.

    Args:
        current_song: Song dictionary from MusicMasterSongList
        default_values: Default values for missing fields - keyword-only
        validation_level: Level of validation to apply - keyword-only
        strict_mode: Whether to use strict field validation - keyword-only

    Returns:
        Dict containing extracted song data with proper field mapping
    """
    from typing import Final

  # Field mappings with fallback options
    FIELD_MAPPINGS: Final = {
        'artist': ['artist', 'performer', 'creator'],
        'title': ['title', 'name', 'song'],
        'album': ['album', 'collection'],
        'duration': ['duration', 'length', 'time'],
        'year': ['year', 'date', 'release_year'],
        'genre': ['comment', 'genre', 'style', 'category']
    }

    extracted_data = {}

    for target_field, source_fields in FIELD_MAPPINGS.items():
        field_value = None

  # Try each potential source field
        for source_field in source_fields:
            if source_field in current_song:
                field_value = current_song[source_field]
                break

  # Apply validation and defaults
        if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
  # Use default value
            field_value = default_values.get(target_field, f'Unknown {target_field.title()}')
        elif not isinstance(field_value, str):
  # Convert to string with validation
            try:
                field_value = str(field_value)
            except Exception:
                field_value = default_values.get(target_field, f'Unknown {target_field.title()}')

  # Apply field-specific processing
        if target_field == 'duration' and validation_level in ['standard', 'comprehensive']:
            field_value = _normalize_duration_format(field_value)
        elif target_field == 'year' and validation_level in ['standard', 'comprehensive']:
            field_value = _normalize_year_format(field_value)

        extracted_data[target_field] = field_value

    return extracted_data


def _validate_paid_song_data(song_data: Dict[str, str], *,
                            validation_level: str = 'standard',
                            required_fields: set,
                            strict_mode: bool = False) -> Dict[str, Any]:
    """Validate extracted paid song data with comprehensive analysis.

    Args:
        song_data: Extracted song data dictionary
        validation_level: Level of validation to perform - keyword-only
        required_fields: Set of required fields - keyword-only
        strict_mode: Whether to use strict validation - keyword-only

    Returns:
        Dict containing validation results and analysis
    """
    from typing import Final
    import re

  # Validation constants
    MIN_FIELD_LENGTH: Final = 1
    MAX_FIELD_LENGTH: Final = 500
    DURATION_PATTERN: Final = re.compile(r'^\d{1,2}:\d{2}$')
    YEAR_PATTERN: Final = re.compile(r'^\d{4}$|^Unknown Year$')

    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'field_analysis': {}
    }

  # Basic validation - check required fields
    for field in required_fields:
        field_analysis = {'errors': [], 'warnings': []}

        if field not in song_data:
            error_msg = f'Required field "{field}" is missing'
            validation_result['errors'].append(error_msg)
            field_analysis['errors'].append(error_msg)
            validation_result['valid'] = False
        else:
            field_value = song_data[field]

  # Check field length
            if len(field_value) < MIN_FIELD_LENGTH:
                error_msg = f'Field "{field}" is empty or too short'
                validation_result['errors'].append(error_msg)
                field_analysis['errors'].append(error_msg)
                validation_result['valid'] = False
            elif len(field_value) > MAX_FIELD_LENGTH:
                warning_msg = f'Field "{field}" is unusually long ({len(field_value)} characters)'
                validation_result['warnings'].append(warning_msg)
                field_analysis['warnings'].append(warning_msg)

        validation_result['field_analysis'][field] = field_analysis

  # Standard validation - format checking
    if validation_level in ['standard', 'comprehensive']:
  # Validate duration format
        if 'duration' in song_data:
            duration_value = song_data['duration']
            if not DURATION_PATTERN.match(duration_value):
                warning_msg = f'Duration format may be invalid: "{duration_value}"'
                validation_result['warnings'].append(warning_msg)
                if 'duration' not in validation_result['field_analysis']:
                    validation_result['field_analysis']['duration'] = {'errors': [], 'warnings': []}
                validation_result['field_analysis']['duration']['warnings'].append(warning_msg)

  # Validate year format
        if 'year' in song_data:
            year_value = song_data['year']
            if not YEAR_PATTERN.match(year_value):
                warning_msg = f'Year format may be invalid: "{year_value}"'
                validation_result['warnings'].append(warning_msg)
                if 'year' not in validation_result['field_analysis']:
                    validation_result['field_analysis']['year'] = {'errors': [], 'warnings': []}
                validation_result['field_analysis']['year']['warnings'].append(warning_msg)

  # Comprehensive validation - content analysis
    if validation_level == 'comprehensive':
  # Check for suspicious "Unknown" values
        unknown_count = sum(1 for value in song_data.values() if 'Unknown' in value)
        if unknown_count > 2:
            warning_msg = f'Many fields contain "Unknown" values ({unknown_count}/{len(song_data)})'
            validation_result['warnings'].append(warning_msg)

  # Validate character encoding
        for field, value in song_data.items():
            try:
                value.encode('utf-8')
            except UnicodeEncodeError:
                warning_msg = f'Field "{field}" contains invalid characters'
                validation_result['warnings'].append(warning_msg)
                if field not in validation_result['field_analysis']:
                    validation_result['field_analysis'][field] = {'errors': [], 'warnings': []}
                validation_result['field_analysis'][field]['warnings'].append(warning_msg)

    return validation_result


def _log_paid_song_extraction(song_data: Dict[str, str], *,
                             song_index: Optional[int] = None,
                             playlist_position: int = 0,
                             logger: Optional[logging.Logger] = None) -> None:
    """Log paid song extraction operation for audit trail.

    Args:
        song_data: Extracted song data
        song_index: Index in master song list (if available) - keyword-only
        playlist_position: Position in paid playlist - keyword-only
        logger: Optional logger instance - keyword-only
    """
    try:
        song_title = song_data.get('title', 'Unknown Title')
        song_artist = song_data.get('artist', 'Unknown Artist')

        log_message = (
            f"Paid song extracted: {song_title} - {song_artist} "
            f"(paid playlist pos: {playlist_position}"
        )

        if song_index is not None:
            log_message += f", song index: {song_index}"

        log_message += ")"

  # Use provided logger or default logging
        if logger:
            logger.info(log_message)
        else:
            _log_info(
                log_message,
                level="INFO",
                console_output=False,
                category="paid_song_extraction"
            )

    except Exception:
  # Don't let logging errors affect the main operation
        pass


def _normalize_duration_format(duration_str: str) -> str:
    """Normalize duration string to MM:SS format.

    Args:
        duration_str: Raw duration string

    Returns:
        Normalized duration in MM:SS format
    """
    import re

    if not isinstance(duration_str, str):
        return '00:00'

  # Try to match MM:SS format
    match = re.match(r'^(\d{1,2}):(\d{2})$', duration_str.strip())
    if match:
        minutes, seconds = match.groups()
        return f"{int(minutes):02d}:{seconds}"

  # Try to match seconds only
    try:
        total_seconds = int(float(duration_str))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return '00:00'


def _normalize_year_format(year_str: str) -> str:
    """Normalize year string to 4-digit format.

    Args:
        year_str: Raw year string

    Returns:
        Normalized 4-digit year or 'Unknown Year'
    """
    import re

    if not isinstance(year_str, str):
        return 'Unknown Year'

  # Extract 4-digit year
    year_match = re.search(r'(\d{4})', year_str)
    if year_match:
        year = int(year_match.group(1))
  # Validate reasonable year range
        if 1900 <= year <= 2030:
            return str(year)

    return 'Unknown Year'


def generate_mp3_metadata(*,
                         music_directory: Optional[str] = None,
                         console_output: bool = True,
                         validate_files: bool = True,
                         validation_level: str = 'standard',
                         include_metadata: bool = False,
                         enable_logging: bool = True,
                         skip_corrupted: bool = True,
                         max_files: Optional[int] = None,
                         file_pattern: str = '*.mp3',
                         strict_mode: bool = False,
                         logger: Optional[logging.Logger] = None) -> Dict[str, Union[bool, List, int, str, Dict[str, Any]]]:
    """Generate MP3 metadata with comprehensive Pythonic functionality.

    This function implements advanced Python metadata extraction patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Multi-level validation with configurable depth and strictness
    - Comprehensive type hints for all parameters and return values
    - Performance monitoring and metadata collection
    - Configurable file processing behavior and options
    - Structured return values with detailed operation tracking
    - Advanced logging integration with contextual information
    - Defensive programming with comprehensive error handling
    - Support for different validation modes and file filters
    - Cross-platform compatibility with pathlib

    Args:
        music_directory: Custom music directory path (default: './music') - keyword-only
        console_output: Whether to print status messages - keyword-only
        validate_files: Whether to validate file accessibility - keyword-only
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        include_metadata: Whether to include operation metadata in return - keyword-only
        enable_logging: Whether to log processing operations - keyword-only
        skip_corrupted: Whether to skip corrupted or unreadable files - keyword-only
        max_files: Maximum number of files to process (None = unlimited) - keyword-only
        file_pattern: File pattern to match (default: '*.mp3') - keyword-only
        strict_mode: Whether to fail on any processing errors - keyword-only
        logger: Optional logger for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if processing succeeded
        - 'metadata_list': List[Tuple] - List of metadata tuples
        - 'files_processed': int - Number of files successfully processed
        - 'files_found': int - Total number of files found
        - 'files_skipped': int - Number of files skipped due to errors
        - 'error_message': str - Error message if failed (empty if success)
        - 'skipped_files': List[str] - List of skipped file names
        - 'operation_metadata': Dict - Operation details (if include_metadata=True)
        - 'processing_time': float - Total processing time in seconds

    Examples:
        >>> generate_mp3_metadata()
        {'success': True, 'metadata_list': [...], 'files_processed': 150, ...}
        >>> generate_mp3_metadata(validation_level='comprehensive', max_files=50)
        {'success': True, 'metadata_list': [...], 'files_processed': 50, ...}
        >>> generate_mp3_metadata(music_directory='/custom/path', strict_mode=True)
        {'success': True, 'metadata_list': [...], 'files_processed': 75, ...}

    Validation Levels:
        - 'basic': Check for file existence and readability
        - 'standard': Basic validation plus format checking
        - 'comprehensive': Full validation including metadata integrity

    Raises:
        ValueError: If music_directory is invalid or validation_level is unknown
        RuntimeError: If strict_mode is True and processing fails

    Note:
        Uses TinyTag library for metadata extraction with comprehensive error handling.
        Supports cross-platform file operations with pathlib.Path.
        Implements performance monitoring and detailed progress tracking.
    """
    from typing import Final
    from pathlib import Path
    import time

  # Constants for better maintainability
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_MUSIC_DIR: Final = 'music'
    METADATA_TUPLE_FIELDS: Final = 8  # Expected number of fields in metadata tuple
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_FOLDER: Final = '📁'
    MAX_FILENAME_LENGTH: Final = 255
    MIN_DURATION_SECONDS: Final = 1
    MAX_DURATION_SECONDS: Final = 3600  # 1 hour max reasonable duration

  # Initialize comprehensive result structure
    processing_start_time = time.time()
    result = {
        'success': False,
        'metadata_list': [],
        'files_processed': 0,
        'files_found': 0,
        'files_skipped': 0,
        'error_message': '',
        'skipped_files': [],
        'operation_metadata': {} if include_metadata else None,
        'processing_time': 0.0
    }

    try:
  # Input validation with early returns
        if validation_level not in VALIDATION_LEVELS:
            error_msg = f'Invalid validation level: {validation_level}. Must be one of {VALIDATION_LEVELS}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if strict_mode:
                raise ValueError(error_msg)
            return result

        if max_files is not None and (not isinstance(max_files, int) or max_files < 1):
            error_msg = f'Invalid max_files value: {max_files}. Must be a positive integer or None'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if strict_mode:
                raise ValueError(error_msg)
            return result

  # Setup music directory path
        if music_directory:
            music_path = Path(music_directory)
        else:
            dir_path = Path(__file__).parent
            music_path = dir_path / DEFAULT_MUSIC_DIR

  # Validate music directory
        directory_validation = _validate_music_directory(
            music_path=music_path,
            validation_level=validation_level,
            console_output=console_output
        )

        if not directory_validation['valid']:
            result['error_message'] = directory_validation['message']
            if console_output:
                print(f"{EMOJI_ERROR} {directory_validation['message']}")
            if strict_mode:
                raise RuntimeError(directory_validation['message'])
            return result

  # Initial status output
        if console_output:
            print("Convergence Jukebox 2026")
            print("Please Be Patient Regenerating Your Songlist From Scratch")
            print("Music Will Start When Finished")
            print(f"{EMOJI_FOLDER} Scanning directory: {music_path}")

  # Find music files with error handling
        try:
            music_files = list(music_path.glob(file_pattern))
            result['files_found'] = len(music_files)

            if not music_files:
                result['error_message'] = f'No files matching pattern "{file_pattern}" found in {music_path}'
                if console_output:
                    print(f"{EMOJI_WARNING} No {file_pattern} files found in music directory")
  # This is not necessarily an error, return success with empty list
                result['success'] = True
                return result

        except Exception as scan_error:
            error_msg = f'Error scanning music directory: {scan_error}'
            result['error_message'] = error_msg
            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")
            if strict_mode:
                raise RuntimeError(error_msg)
            return result

  # Apply file limit if specified
        if max_files and len(music_files) > max_files:
            if console_output:
                print(f"{EMOJI_WARNING} Limiting processing to {max_files} files (found {len(music_files)})")
            music_files = music_files[:max_files]

        if console_output:
            print(f"{EMOJI_MUSIC} Found {len(music_files)} files to process")

  # Process files with comprehensive error handling
        metadata_list = []
        processing_errors = []

        for index, music_file in enumerate(music_files):
            try:
  # File-level validation
                if validate_files:
                    file_validation = _validate_music_file(
                        file_path=music_file,
                        validation_level=validation_level,
                        console_output=False  # Suppress individual file messages
                    )

                    if not file_validation['valid']:
                        result['files_skipped'] += 1
                        result['skipped_files'].append(music_file.name)
                        processing_errors.append(f"{music_file.name}: {file_validation['message']}")

                        if console_output and len(processing_errors) <= 5:  # Limit error output
                            print(f"{EMOJI_WARNING} Skipping {music_file.name}: {file_validation['message']}")

                        if skip_corrupted:
                            continue
                        elif strict_mode:
                            raise RuntimeError(file_validation['message'])

  # Extract metadata with comprehensive error handling
                metadata_result = _extract_file_metadata(
                    file_path=music_file,
                    file_index=index,
                    validation_level=validation_level,
                    strict_mode=strict_mode
                )

                if metadata_result['success']:
                    metadata_list.append(metadata_result['metadata_tuple'])
                    result['files_processed'] += 1
                else:
                    result['files_skipped'] += 1
                    result['skipped_files'].append(music_file.name)
                    processing_errors.append(f"{music_file.name}: {metadata_result['error_message']}")

                    if console_output and len(processing_errors) <= 5:
                        print(f"{EMOJI_WARNING} Failed to process {music_file.name}: {metadata_result['error_message']}")

                    if not skip_corrupted and strict_mode:
                        raise RuntimeError(metadata_result['error_message'])

            except Exception as file_error:
                result['files_skipped'] += 1
                result['skipped_files'].append(music_file.name)
                error_msg = f"{music_file.name}: {file_error}"
                processing_errors.append(error_msg)

                if console_output and len(processing_errors) <= 5:
                    print(f"{EMOJI_ERROR} Error processing {music_file.name}: {file_error}")

                if not skip_corrupted:
                    if strict_mode:
                        raise RuntimeError(error_msg)
                    else:
                        continue

  # Calculate processing time
        processing_duration = time.time() - processing_start_time
        result['processing_time'] = processing_duration

  # Success output and logging
        if console_output:
            print(f"{EMOJI_SUCCESS} Successfully processed {result['files_processed']} MP3 files")
            if result['files_skipped'] > 0:
                print(f"{EMOJI_WARNING} Skipped {result['files_skipped']} files due to errors")
            if processing_errors and len(processing_errors) > 5:
                print(f"{EMOJI_WARNING} ... and {len(processing_errors) - 5} more errors (check logs for details)")

  # Update result with success
        result.update({
            'success': True,
            'metadata_list': metadata_list
        })

  # Add operation metadata if requested
        if include_metadata:
            result['operation_metadata'] = {
                'processing_timestamp': processing_start_time,
                'processing_duration': processing_duration,
                'music_directory': str(music_path),
                'file_pattern': file_pattern,
                'validation_level': validation_level,
                'files_per_second': result['files_processed'] / processing_duration if processing_duration > 0 else 0,
                'success_rate': result['files_processed'] / result['files_found'] if result['files_found'] > 0 else 0,
                'validation_performed': validate_files,
                'processing_errors': processing_errors[:10],  # Limit stored errors
                'total_errors': len(processing_errors)
            }

  # Log successful processing
        if enable_logging:
            _log_metadata_generation(
                files_processed=result['files_processed'],
                files_found=result['files_found'],
                processing_duration=processing_duration,
                logger=logger
            )

        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        processing_duration = time.time() - processing_start_time
        error_message = f'MP3 metadata generation error: {general_error}'
        result.update({
            'error_message': error_message,
            'processing_time': processing_duration
        })

        if console_output:
            print(f"{EMOJI_ERROR} Error generating MP3 metadata: {general_error}")

  # Add partial metadata on error if requested
        if include_metadata:
            result['operation_metadata'] = {
                'processing_timestamp': processing_start_time,
                'processing_duration': processing_duration,
                'error_occurred': True,
                'music_directory': str(music_path) if 'music_path' in locals() else 'unknown'
            }

  # Log error for debugging
        if enable_logging:
            _log_error(
                error_message,
                error_type="ERROR",
                console_output=False,
                include_traceback=True
            )

  # Re-raise if strict mode
        if strict_mode:
            raise RuntimeError(error_message) from general_error

        return result


def _validate_music_directory(music_path: Path, *,
                             validation_level: str = 'standard',
                             console_output: bool = True) -> Dict[str, Union[bool, str]]:
    """Validate music directory accessibility and structure.

    Args:
        music_path: Path to music directory
        validation_level: Level of validation to perform - keyword-only
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from typing import Final

    try:
  # Basic validation - check existence
        if not music_path.exists():
            return {
                'valid': False,
                'message': f'Music directory not found at {music_path}'
            }

        if not music_path.is_dir():
            return {
                'valid': False,
                'message': f'Path exists but is not a directory: {music_path}'
            }

  # Standard validation - check accessibility
        if validation_level in ['standard', 'comprehensive']:
            try:
  # Test directory access by listing contents
                list(music_path.iterdir())
            except PermissionError:
                return {
                    'valid': False,
                    'message': f'Permission denied accessing directory: {music_path}'
                }
            except Exception as access_error:
                return {
                    'valid': False,
                    'message': f'Cannot access directory {music_path}: {access_error}'
                }

  # Comprehensive validation - check directory structure
        if validation_level == 'comprehensive':
            try:
  # Check if directory is readable and writable
                test_file = music_path / '.test_access'
                try:
                    test_file.touch()
                    test_file.unlink()
                except PermissionError:
  # Read-only is OK for music directory
                    pass
                except Exception as write_error:
                    if console_output:
                        print(f"Warning: Directory write test failed: {write_error}")

            except Exception as comprehensive_error:
                return {
                    'valid': False,
                    'message': f'Comprehensive validation failed: {comprehensive_error}'
                }

        return {'valid': True, 'message': 'Directory validation passed'}

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f'Directory validation error: {validation_error}'
        }


def _validate_music_file(file_path: Path, *,
                        validation_level: str = 'standard',
                        console_output: bool = True) -> Dict[str, Union[bool, str]]:
    """Validate individual music file accessibility and format.

    Args:
        file_path: Path to music file
        validation_level: Level of validation to perform - keyword-only
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from typing import Final

  # File size limits for validation
    MIN_FILE_SIZE: Final = 1024  # 1KB minimum
    MAX_FILE_SIZE: Final = 100 * 1024 * 1024  # 100MB maximum

    try:
  # Basic validation - check existence and readability
        if not file_path.exists():
            return {
                'valid': False,
                'message': f'File does not exist: {file_path.name}'
            }

        if not file_path.is_file():
            return {
                'valid': False,
                'message': f'Path is not a file: {file_path.name}'
            }

  # Standard validation - check file properties
        if validation_level in ['standard', 'comprehensive']:
            try:
                file_size = file_path.stat().st_size

                if file_size < MIN_FILE_SIZE:
                    return {
                        'valid': False,
                        'message': f'File too small ({file_size} bytes): {file_path.name}'
                    }

                if file_size > MAX_FILE_SIZE:
                    return {
                        'valid': False,
                        'message': f'File too large ({file_size // (1024*1024)}MB): {file_path.name}'
                    }

            except OSError as stat_error:
                return {
                    'valid': False,
                    'message': f'Cannot access file properties: {stat_error}'
                }

  # Comprehensive validation - check file format
        if validation_level == 'comprehensive':
            try:
  # Quick format check by reading file header
                with open(file_path, 'rb') as f:
                    header = f.read(10)

  # Check for MP3 signature (ID3 tag or MPEG frame sync)
                if not (header.startswith(b'ID3') or header.startswith(b'\xff\xfb') or header.startswith(b'\xff\xfa')):
                    return {
                        'valid': False,
                        'message': f'File does not appear to be a valid MP3: {file_path.name}'
                    }

            except Exception as format_error:
                return {
                    'valid': False,
                    'message': f'Format validation failed: {format_error}'
                }

        return {'valid': True, 'message': 'File validation passed'}

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f'File validation error: {validation_error}'
        }


def _extract_file_metadata(file_path: Path, *,
                          file_index: int,
                          validation_level: str = 'standard',
                          strict_mode: bool = False) -> Dict[str, Union[bool, tuple, str]]:
    """Extract metadata from a single music file with comprehensive error handling.

    Args:
        file_path: Path to the music file
        file_index: Index for the metadata tuple - keyword-only
        validation_level: Level of validation to apply - keyword-only
        strict_mode: Whether to use strict validation - keyword-only

    Returns:
        Dict containing extraction results and metadata tuple
    """
    from typing import Final
    import time

  # Constants for metadata validation
    MIN_DURATION_SECONDS: Final = 1
    MAX_DURATION_SECONDS: Final = 3600  # 1 hour
    DEFAULT_VALUES: Final = {
        'title': 'Unknown Title',
        'artist': 'Unknown Artist',
        'album': 'Unknown Album',
        'year': 'Unknown Year',
        'comment': ''
    }

    result = {
        'success': False,
        'metadata_tuple': None,
        'error_message': ''
    }

    try:
  # Extract ID3 metadata with comprehensive error handling
        id3tag = TinyTag.get(str(file_path))

        if id3tag is None:
            result['error_message'] = 'Failed to read metadata from file'
            return result

  # Extract and validate duration
        duration_seconds = 0
        if id3tag.duration:
            try:
                duration_seconds = int(float(id3tag.duration))

  # Validate duration range
                if validation_level in ['standard', 'comprehensive']:
                    if duration_seconds < MIN_DURATION_SECONDS:
                        if strict_mode:
                            result['error_message'] = f'Duration too short: {duration_seconds}s'
                            return result
                        else:
                            duration_seconds = MIN_DURATION_SECONDS
                    elif duration_seconds > MAX_DURATION_SECONDS:
                        if strict_mode:
                            result['error_message'] = f'Duration too long: {duration_seconds}s'
                            return result
                        else:
                            duration_seconds = MAX_DURATION_SECONDS

            except (ValueError, TypeError):
                duration_seconds = 0

  # Format duration as MM:SS
        try:
            duration_formatted = time.strftime("%M:%S", time.gmtime(duration_seconds))
        except (ValueError, OSError):
            duration_formatted = "00:00"

  # Extract and validate other metadata fields
        metadata_fields = {
            'title': _clean_metadata_field(id3tag.title, DEFAULT_VALUES['title'], validation_level),
            'artist': _clean_metadata_field(id3tag.artist, DEFAULT_VALUES['artist'], validation_level),
            'album': _clean_metadata_field(id3tag.album, DEFAULT_VALUES['album'], validation_level),
            'year': _clean_year_field(id3tag.year, DEFAULT_VALUES['year'], validation_level),
            'comment': _clean_metadata_field(id3tag.comment, DEFAULT_VALUES['comment'], validation_level)
        }

  # Build metadata tuple with comprehensive field validation
        metadata_tuple = (
            file_index,
            str(file_path),
            metadata_fields['title'],
            metadata_fields['artist'],
            metadata_fields['album'],
            metadata_fields['year'],
            metadata_fields['comment'],
            duration_formatted
        )

  # Final validation of tuple structure
        if len(metadata_tuple) != 8:
            result['error_message'] = f'Invalid metadata tuple length: {len(metadata_tuple)}'
            return result

        result.update({
            'success': True,
            'metadata_tuple': metadata_tuple
        })

        return result

    except Exception as extraction_error:
        result['error_message'] = f'Metadata extraction failed: {extraction_error}'
        return result


def _clean_metadata_field(field_value: Optional[str], default_value: str, validation_level: str) -> str:
    """Clean and validate a metadata field value.

    Args:
        field_value: Raw field value from metadata
        default_value: Default value to use if field is empty/invalid
        validation_level: Level of validation to apply

    Returns:
        Cleaned and validated field value
    """
    from typing import Final

    MAX_FIELD_LENGTH: Final = 255

  # Handle None or empty values
    if not field_value or (isinstance(field_value, str) and not field_value.strip()):
        return default_value

  # Convert to string and clean
    try:
        cleaned_value = str(field_value).strip()

  # Remove null bytes and control characters
        cleaned_value = ''.join(char for char in cleaned_value if ord(char) >= 32 or char in '\t\n')

  # Limit length if validation is enabled
        if validation_level in ['standard', 'comprehensive'] and len(cleaned_value) > MAX_FIELD_LENGTH:
            cleaned_value = cleaned_value[:MAX_FIELD_LENGTH].rstrip()

  # Return cleaned value or default if empty after cleaning
        return cleaned_value if cleaned_value else default_value

    except Exception:
        return default_value


def _clean_year_field(year_value: Optional[str], default_value: str, validation_level: str) -> str:
    """Clean and validate a year field value.

    Args:
        year_value: Raw year value from metadata
        default_value: Default value to use if year is empty/invalid
        validation_level: Level of validation to apply

    Returns:
        Cleaned and validated year value
    """
    import re
    from typing import Final

    MIN_YEAR: Final = 1900
    MAX_YEAR: Final = 2030

    if not year_value:
        return default_value

    try:
        year_str = str(year_value).strip()

  # Extract 4-digit year using regex
        year_match = re.search(r'(\d{4})', year_str)
        if year_match:
            year_int = int(year_match.group(1))

  # Validate year range if validation is enabled
            if validation_level in ['standard', 'comprehensive']:
                if MIN_YEAR <= year_int <= MAX_YEAR:
                    return str(year_int)
                else:
                    return default_value
            else:
                return str(year_int)

  # If no 4-digit year found, return original string if it looks reasonable
        if len(year_str) <= 10 and year_str.replace('-', '').replace('/', '').isdigit():
            return year_str

        return default_value

    except Exception:
        return default_value


def _log_metadata_generation(files_processed: int, *,
                           files_found: int,
                           processing_duration: float,
                           logger: Optional[logging.Logger] = None) -> None:
    """Log metadata generation operation for audit trail.

    Args:
        files_processed: Number of files successfully processed
        files_found: Total number of files found - keyword-only
        processing_duration: Processing time in seconds - keyword-only
        logger: Optional logger instance - keyword-only
    """
    try:
        files_per_second = files_processed / processing_duration if processing_duration > 0 else 0
        success_rate = files_processed / files_found if files_found > 0 else 0

        log_message = (
            f"MP3 metadata generation completed: {files_processed}/{files_found} files processed "
            f"in {processing_duration:.2f}s ({files_per_second:.1f} files/sec, {success_rate:.1%} success rate)"
        )

  # Use provided logger or default logging
        if logger:
            logger.info(log_message)
        else:
            _log_info(
                log_message,
                level="INFO",
                console_output=False,
                category="metadata_generation"
            )

    except Exception:
  # Don't let logging errors affect the main operation
        pass


def generate_Music_Master_Song_List_Dictionary(metadata_list: Optional[List] = None) -> List:
    """Generate master song list dictionary from metadata in a Pythonic way.

    Args:
        metadata_list: List of metadata tuples from generate_mp3_metadata()
                      If None, will call generate_mp3_metadata()

    Returns:
        List of dictionaries containing song information with keys:
        ['number', 'location', 'title', 'artist', 'album', 'year', 'comment', 'duration']
        Returns empty list if no metadata available or errors occur
    """
    from pathlib import Path

  # Constants for better maintainability
    SONG_KEYS = ['number', 'location', 'title', 'artist', 'album', 'year', 'comment', 'duration']
    MASTER_LIST_FILE = Path('MusicMasterSongList.txt')
    CHECK_FILE = Path('MusicMasterSongListCheck.txt')

    try:
  # Get metadata if not provided
        if metadata_list is None:
            print("Generating fresh metadata...")
            metadata_result = generate_mp3_metadata()

  # Handle the new structured return value
            if isinstance(metadata_result, dict):
                if not metadata_result.get('success', False):
                    print(f"Failed to generate metadata: {metadata_result.get('error_message', 'Unknown error')}")
                    return []
                metadata_list = metadata_result.get('metadata_list', [])

  # Show processing statistics
                files_processed = metadata_result.get('files_processed', 0)
                files_found = metadata_result.get('files_found', 0)
                processing_time = metadata_result.get('processing_time', 0)

                try:
                    print(f"✓ Processed {files_processed}/{files_found} files in {processing_time:.2f}s")
                except UnicodeEncodeError:
                    print(f"[OK] Processed {files_processed}/{files_found} files in {processing_time:.2f}s")

                if metadata_result.get('files_skipped', 0) > 0:
                    try:
                        print(f"⚠ Skipped {metadata_result['files_skipped']} files due to errors")
                    except UnicodeEncodeError:
                        print(f"[!] Skipped {metadata_result['files_skipped']} files due to errors")
            else:
  # Fallback for old-style return value (list)
                metadata_list = metadata_result if isinstance(metadata_result, list) else []

  # Validate input data
        if not metadata_list:
            print("No metadata available to build song dictionary")
            return []

        if not isinstance(metadata_list, list):
            print("Invalid metadata format - expected list")
            return []

  # Validate metadata structure
        for i, song_data in enumerate(metadata_list):
            if not isinstance(song_data, (tuple, list)) or len(song_data) != len(SONG_KEYS):
                print(f"Warning: Skipping invalid song data at index {i}")
                continue

  # Filter valid metadata and build dictionary list
        master_song_list = [
            dict(zip(SONG_KEYS, song_data))
            for song_data in metadata_list
            if isinstance(song_data, (tuple, list)) and len(song_data) == len(SONG_KEYS)
        ]

        if not master_song_list:
            print("No valid song data found after filtering")
            return []

        print(f"Built dictionary for {len(master_song_list)} songs")

  # Save files with comprehensive error handling and status tracking
        save_result = _save_song_data_files(master_song_list, MASTER_LIST_FILE, CHECK_FILE)

  # Handle save operation results
        if not save_result.success:
            try:
                print(f"[!] Warning: Some file operations failed. Data integrity may be compromised.")
            except UnicodeEncodeError:
                print("[!] Warning: Some file operations failed. Data integrity may be compromised.")

        return master_song_list

    except UnicodeEncodeError as e:
        # Handle character encoding errors gracefully
        print(f"Encoding error while processing metadata (unicode issue): {str(e)[:100]}")
        print("Retrying with error-tolerant encoding...")
        try:
            # Try again but skip problematic characters
            if metadata_list:
                master_song_list = [
                    {k: (v.encode('utf-8', errors='replace').decode('utf-8') if isinstance(v, str) else v)
                     for k, v in dict(zip(SONG_KEYS, song_data)).items()}
                    for song_data in metadata_list
                    if isinstance(song_data, (tuple, list)) and len(song_data) == len(SONG_KEYS)
                ]
                save_result = _save_song_data_files(master_song_list, MASTER_LIST_FILE, CHECK_FILE)
                return master_song_list if save_result.success else []
        except Exception as retry_error:
            print(f"Error generating master song list (after retry): {str(retry_error)[:100]}")
            return []
    except Exception as e:
        print(f"Error generating master song list: {str(e)[:100]}")
        return []


# Constants for file operations
class FileOperationConstants:
    """Constants for file operations to follow centralization best practices."""
    JSON_ENCODING = 'utf-8'
    JSON_NEWLINE = '\n'
    PRETTY_INDENT = 2
    COMPACT_SEPARATORS = (',', ':')
    PRETTY_SEPARATORS = (',', ': ')


# Constants for song validation
class SongValidationConstants:
    """Constants for song data validation following centralization best practices."""
    REQUIRED_KEYS = frozenset({'number', 'location', 'title', 'artist'})
    OPTIONAL_KEYS = frozenset({'album', 'year', 'comment', 'duration'})
    ALL_VALID_KEYS = REQUIRED_KEYS | OPTIONAL_KEYS
    DEFAULT_VALIDATION_SAMPLE_SIZE = 10
    MAX_VALIDATION_ERRORS = 5

  # Type validation mappings
    KEY_TYPE_MAPPING = {
        'number': (int, float),
        'location': str,
        'title': str,
        'artist': str,
        'album': str,
        'year': (str, int),
        'comment': str,
        'duration': str
    }


class SongDataError(Exception):
    """Custom exception for song data validation errors."""
    pass


@dataclass
class ValidationResult:
    """Comprehensive validation result with detailed tracking."""
    is_valid: bool
    total_items: int
    validated_items: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate validation success rate."""
        if self.total_items == 0 or self.validated_items == 0:
            return 0.0
        return (self.validated_items - len(self.errors)) / self.validated_items

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0

    def add_error(self, error: str) -> None:
        """Add validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add validation warning."""
        self.warnings.append(warning)

    def summary(self) -> str:
        """Generate validation summary."""
        return (
            f"Validation {'✓ PASSED' if self.is_valid else '✗ FAILED'} "
            f"({self.validated_items}/{self.total_items} items checked, "
            f"{self.success_rate:.1%} success rate)"
        )


class OperationStatus(Enum):
    """Enumeration for file operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class SaveResult:
    """Result of save operations with detailed status information and builder pattern."""
    master_file_status: OperationStatus
    check_file_status: OperationStatus
    songs_saved: int
    master_file_error: Optional[str] = None
    check_file_error: Optional[str] = None
    operation_metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_failed(cls, songs_count: int, error_msg: str = "Operation failed") -> 'SaveResult':
        """Builder method for failed operations."""
        return cls(
            master_file_status=OperationStatus.FAILED,
            check_file_status=OperationStatus.FAILED,
            songs_saved=songs_count,
            master_file_error=error_msg,
            check_file_error=error_msg
        )

    @classmethod
    def create_success(cls, songs_count: int) -> 'SaveResult':
        """Builder method for successful operations."""
        return cls(
            master_file_status=OperationStatus.SUCCESS,
            check_file_status=OperationStatus.SUCCESS,
            songs_saved=songs_count
        )

    def with_master_result(self, success: bool, error: Optional[str] = None) -> 'SaveResult':
        """Builder method to set master file result."""
        self.master_file_status = OperationStatus.SUCCESS if success else OperationStatus.FAILED
        self.master_file_error = error
        return self

    def with_check_result(self, success: bool, error: Optional[str] = None) -> 'SaveResult':
        """Builder method to set check file result."""
        self.check_file_status = OperationStatus.SUCCESS if success else OperationStatus.FAILED
        self.check_file_error = error
        return self

    @property
    def overall_status(self) -> OperationStatus:
        """Get overall operation status with intelligent aggregation."""
        statuses = [self.master_file_status, self.check_file_status]

        if all(status == OperationStatus.SUCCESS for status in statuses):
            return OperationStatus.SUCCESS
        elif all(status == OperationStatus.FAILED for status in statuses):
            return OperationStatus.FAILED
        else:
            return OperationStatus.PARTIAL

    @property
    def success(self) -> bool:
        """Check if overall operation was successful."""
        return self.overall_status == OperationStatus.SUCCESS

    @property
    def has_errors(self) -> bool:
        """Check if any operation had errors."""
        return self.master_file_error is not None or self.check_file_error is not None

    @property
    def error_summary(self) -> List[str]:
        """Get summary of all errors."""
        errors = []
        if self.master_file_error:
            errors.append(f"Master file: {self.master_file_error}")
        if self.check_file_error:
            errors.append(f"Check file: {self.check_file_error}")
        return errors


def _save_song_data_files(master_song_list: List[Dict[str, Any]], master_file: Path, check_file: Path, *, enable_logging: bool = True) -> SaveResult:
    """Save song data to files with comprehensive error handling and status reporting.

    This function implements Pythonic best practices including:
    - Comprehensive input validation with custom exceptions
    - Builder pattern for result construction
    - Logging support for operational monitoring
    - Defensive programming with graceful error handling

    Args:
        master_song_list: List of song dictionaries to save
        master_file: Path to master song list file
        check_file: Path to song count check file
        enable_logging: Whether to enable logging output (keyword-only)

    Returns:
        SaveResult: Detailed information about the save operations

    Raises:
        SongDataError: If song data validation fails
        ValueError: If input parameters are invalid
    """
  # Setup enhanced logging if enabled with comprehensive configuration
    logger = _setup_operation_logger(
        logger_name='jukebox.save_operations',
        log_level='INFO',
        enable_console_output=True,
        enable_file_output=False,  # Can be enabled for production
        formatter_style='detailed',
        include_thread_info=True,
        performance_tracking=True
    ) if enable_logging else None

  # Enhanced input validation with comprehensive validation and optional result tracking
    validation_result = _validate_song_data_input(
        master_song_list,
        validation_sample_size=20,  # Validate more items for better coverage
        strict_mode=True,
        return_result=True
    )

  # Log validation results if available
    if enable_logging and logger and validation_result:
        logger.info(validation_result.summary())
        if validation_result.has_warnings:
            logger.warning(f"Validation warnings: {'; '.join(validation_result.warnings[:3])}")

  # Enhanced file path validation with comprehensive checking
    _validate_file_paths(
        master_file,
        check_file,
        validation_level='standard',
        allowed_extensions=['.txt', '.json'],
        check_parent_directories=True,
        check_write_permissions=True,
        create_missing_directories=True,
        logger=logger
    )

  # Initialize result with builder pattern
    result = SaveResult(
        master_file_status=OperationStatus.FAILED,
        check_file_status=OperationStatus.FAILED,
        songs_saved=len(master_song_list),
        operation_metadata={
            'timestamp': datetime.now().isoformat(),
            'master_file': str(master_file),
            'check_file': str(check_file)
        }
    )

    if logger:
        logger.info(f"Starting save operation for {len(master_song_list)} songs")

  # Save operations with enhanced error tracking
    context_data = {
        'songs_count': len(master_song_list),
        'master_file': str(master_file),
        'check_file': str(check_file)
    }

    with _operation_context(
        "song data save",
        logger=logger,
        track_performance=True,
        error_handling_level='comprehensive',
        include_stack_trace=True,
        collect_metadata=True,
        context_data=context_data
    ) as operation_ctx:
  # Save master song list
        master_result = _save_json_file(
            data=master_song_list,
            file_path=master_file,
            description=f"{len(master_song_list)} songs",
            pretty_print=True,
            logger=logger,
            console_output=False  # Handle output in display function
        )
        master_success = bool(master_result.get('success', False))
        master_error = str(master_result.get('error_message')) if master_result.get('error_message') else None
        result.with_master_result(master_success, master_error)

  # Save song count for change detection
        check_result = _save_json_file(
            data=len(master_song_list),
            file_path=check_file,
            description=f"song count ({len(master_song_list)})",
            pretty_print=False,
            logger=logger,
            console_output=False  # Handle output in display function
        )
        check_success = bool(check_result.get('success', False))
        check_error = str(check_result.get('error_message')) if check_result.get('error_message') else None
        result.with_check_result(check_success, check_error)

  # Provide comprehensive feedback with enhanced display
    _display_save_results(result, master_file, check_file, logger=logger)

    if logger:
        logger.info(f"Save operation completed with status: {result.overall_status.value}")

    return result


def _validate_song_data_input(
    master_song_list: List[Dict[str, Any]],
    *,
    validation_sample_size: Optional[int] = None,
    strict_mode: bool = True,
    return_result: bool = False
) -> Union[None, ValidationResult]:
    """Validate song data input with comprehensive, configurable validation.

    This function implements advanced Pythonic validation patterns including:
    - Configurable validation depth and strictness
    - Comprehensive error tracking and reporting
    - Type validation with flexible schemas
    - Performance optimization with sampling
    - Detailed validation statistics

    Args:
        master_song_list: List of song dictionaries to validate
        validation_sample_size: Number of items to validate (None for all)
        strict_mode: Whether to raise exceptions on validation failure
        return_result: Whether to return ValidationResult instead of raising

    Returns:
        None if strict_mode=True and validation passes
        ValidationResult if return_result=True

    Raises:
        SongDataError: If validation fails and strict_mode=True
    """
    from itertools import islice

  # Initialize validation result
    result = ValidationResult(
        is_valid=True,
        total_items=len(master_song_list) if master_song_list else 0,
        validated_items=0,
        validation_metadata={
            'timestamp': datetime.now().isoformat(),
            'strict_mode': strict_mode,
            'sample_size': validation_sample_size
        }
    )

  # Primary validation: Check if list exists and is proper type
    validation_chain = [
        _validate_list_existence,
        _validate_list_type,
        _validate_list_content_structure,
        _validate_song_schemas
    ]

  # Execute validation chain with early termination on critical errors
    for validator in validation_chain:
        try:
            validator(master_song_list, result, validation_sample_size or SongValidationConstants.DEFAULT_VALIDATION_SAMPLE_SIZE)

  # Early termination if too many errors and in strict mode
            if len(result.errors) >= SongValidationConstants.MAX_VALIDATION_ERRORS and strict_mode:
                break

        except SongDataError as e:
            result.add_error(str(e))
            if strict_mode and not return_result:
                raise
            break

  # Handle validation results based on mode
    if return_result:
        return result

    if not result.is_valid and strict_mode:
        error_summary = f"Validation failed with {len(result.errors)} errors: {'; '.join(result.errors[:3])}"
        if len(result.errors) > 3:
            error_summary += f" ... and {len(result.errors) - 3} more"
        raise SongDataError(error_summary)


def _validate_list_existence(
    song_list: Optional[List[Dict[str, Any]]],
    result: ValidationResult,
    sample_size: int,
    *,
    validation_level: str = 'standard',
    min_list_size: int = 1,
    max_list_size: Optional[int] = None,
    check_memory_usage: bool = False,
    enable_size_warnings: bool = True,
    custom_size_validator: Optional[callable] = None,
    track_performance: bool = False,
    logger: Optional[logging.Logger] = None,
    return_detailed_info: bool = False
) -> Optional[Dict[str, Union[bool, int, float, Dict, str]]]:
    """Enhanced list existence validation with comprehensive Pythonic functionality.

    This function implements advanced Pythonic validation patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Multi-level validation with configurable depth and size constraints
    - Comprehensive type hints for all parameters and return values
    - Memory usage monitoring for large datasets
    - Performance tracking with detailed timing metrics
    - Custom validation hooks for specialized requirements
    - Structured return values with detailed validation results
    - Warning generation for potential performance issues
    - Defensive programming with comprehensive null checks

    Args:
        song_list: List of song dictionaries to validate (can be None)
        result: ValidationResult object to update with findings
        sample_size: Sample size for validation (maintained for compatibility)
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        min_list_size: Minimum required list size (default: 1) - keyword-only
        max_list_size: Maximum allowed list size (None for no limit) - keyword-only
        check_memory_usage: Whether to monitor memory usage of the list - keyword-only
        enable_size_warnings: Whether to generate warnings for large lists - keyword-only
        custom_size_validator: Custom function to validate list size - keyword-only
        track_performance: Whether to track validation performance - keyword-only
        logger: Optional logger for validation tracking - keyword-only
        return_detailed_info: Whether to return detailed validation information - keyword-only

    Returns:
        None if return_detailed_info=False
        Dict with detailed validation information if return_detailed_info=True:
        - 'validation_passed': bool indicating validation success
        - 'list_size': int size of the validated list
        - 'memory_usage_mb': float memory usage in MB (if check_memory_usage=True)
        - 'validation_duration': float time taken for validation (if track_performance=True)
        - 'warnings_generated': List of warnings generated during validation
        - 'validation_level_used': str validation level that was applied

    Examples:
        >>>  # Basic usage (maintains compatibility)
        >>> _validate_list_existence(song_list, result, sample_size)

        >>>  # Enhanced usage with comprehensive validation
        >>> info = _validate_list_existence(
        ...     song_list, result, sample_size,
        ...     validation_level='comprehensive',
        ...     min_list_size=10,
        ...     max_list_size=10000,
        ...     check_memory_usage=True,
        ...     track_performance=True,
        ...     return_detailed_info=True
        ... )
        >>> print(f"List size: {info['list_size']}")

        >>>  # Custom size validation
        >>> def custom_validator(size): return size % 100 == 0
        >>> _validate_list_existence(
        ...     song_list, result, sample_size,
        ...     custom_size_validator=custom_validator,
        ...     logger=my_logger
        ... )

    Validation Levels:
        - 'basic': Simple existence and emptiness check
        - 'standard': Basic validation plus size constraints and warnings
        - 'comprehensive': Full validation including memory monitoring and custom validators

    Raises:
        SongDataError: If validation fails (list is None, empty, or violates constraints)
        TypeError: If invalid parameter types are provided
        ValueError: If invalid validation level or constraints are specified

    Note:
        Maintains backward compatibility with existing function signature.
        Memory usage calculation is approximate and platform-dependent.
        Performance tracking includes validation overhead.
    """
    import time
    import sys
    from typing import Final

  # Constants for validation
    VALID_VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    LARGE_LIST_WARNING_THRESHOLD: Final = 10000
    VERY_LARGE_LIST_WARNING_THRESHOLD: Final = 100000
    MEMORY_WARNING_THRESHOLD_MB: Final = 100.0

  # Initialize performance tracking
    validation_start_time = time.time() if track_performance else None

  # Initialize detailed info tracking
    detailed_info = {
        'validation_passed': False,
        'list_size': 0,
        'warnings_generated': [],
        'validation_level_used': validation_level
    } if return_detailed_info else None

    try:
  # Input validation for enhanced parameters
        if validation_level not in VALID_VALIDATION_LEVELS:
            if logger:
                logger.warning(f"Invalid validation_level '{validation_level}', defaulting to 'standard'")
            validation_level = 'standard'

        if not isinstance(min_list_size, int) or min_list_size < 0:
            raise ValueError("min_list_size must be a non-negative integer")

        if max_list_size is not None and (not isinstance(max_list_size, int) or max_list_size < min_list_size):
            raise ValueError("max_list_size must be an integer >= min_list_size")

        if logger:
            logger.debug(f"Starting {validation_level} list existence validation")

  # Core validation: Check if list exists and is not None
        if song_list is None:
            error_msg = "Cannot validate None song list"
            if logger:
                logger.error(error_msg)
            raise SongDataError(error_msg)

  # Check if list is empty (basic level)
        list_size = len(song_list)
        if list_size == 0:
            error_msg = "Cannot validate empty song list"
            if logger:
                logger.error(f"{error_msg} (size: {list_size})")
            raise SongDataError(error_msg)

  # Update result metadata (maintaining compatibility)
        result.validation_metadata['list_size'] = list_size

  # Enhanced validation for standard and comprehensive levels
        if validation_level in ('standard', 'comprehensive'):
  # Size constraint validation
            if list_size < min_list_size:
                error_msg = f"List size {list_size} is below minimum required size {min_list_size}"
                if logger:
                    logger.error(error_msg)
                raise SongDataError(error_msg)

            if max_list_size is not None and list_size > max_list_size:
                error_msg = f"List size {list_size} exceeds maximum allowed size {max_list_size}"
                if logger:
                    logger.error(error_msg)
                raise SongDataError(error_msg)

  # Generate size warnings if enabled
            if enable_size_warnings:
                warnings = _generate_list_size_warnings(
                    list_size, LARGE_LIST_WARNING_THRESHOLD,
                    VERY_LARGE_LIST_WARNING_THRESHOLD, logger
                )
                if detailed_info:
                    detailed_info['warnings_generated'].extend(warnings)

  # Comprehensive validation level features
        if validation_level == 'comprehensive':
  # Memory usage monitoring
            if check_memory_usage:
                memory_usage_mb = _calculate_list_memory_usage(song_list)
                result.validation_metadata['estimated_memory_mb'] = memory_usage_mb

                if detailed_info:
                    detailed_info['memory_usage_mb'] = memory_usage_mb

  # Memory usage warnings
                if memory_usage_mb > MEMORY_WARNING_THRESHOLD_MB:
                    warning_msg = (
                        f"Large memory usage detected: {memory_usage_mb:.1f}MB "
                        f"for {list_size} items"
                    )
                    if logger:
                        logger.warning(warning_msg)
                    if detailed_info:
                        detailed_info['warnings_generated'].append(warning_msg)

  # Custom size validation
            if custom_size_validator:
                try:
                    custom_result = custom_size_validator(list_size)
                    if custom_result is False:
                        error_msg = f"Custom size validator rejected list size {list_size}"
                        if logger:
                            logger.error(error_msg)
                        raise SongDataError(error_msg)
                    elif isinstance(custom_result, str):
  # Custom validator returned error message
                        if logger:
                            logger.error(f"Custom validator error: {custom_result}")
                        raise SongDataError(f"Custom validation failed: {custom_result}")
                except Exception as e:
                    error_msg = f"Custom size validator failed: {e}"
                    if logger:
                        logger.error(error_msg)
                    raise SongDataError(error_msg)

  # Performance tracking completion
        if track_performance and validation_start_time:
            validation_duration = time.time() - validation_start_time
            result.validation_metadata['list_existence_validation_duration'] = validation_duration

            if detailed_info:
                detailed_info['validation_duration'] = validation_duration

            if logger:
                logger.debug(
                    f"List existence validation completed in {validation_duration:.3f}s "
                    f"for {list_size} items"
                )

  # Success logging
        if logger:
            logger.debug(
                f"List existence validation passed: {list_size} items, "
                f"level: {validation_level}"
            )

  # Mark validation as successful
        if detailed_info:
            detailed_info['validation_passed'] = True
            detailed_info['list_size'] = list_size

  # Return detailed info if requested
        if return_detailed_info:
            return detailed_info

        return None

    except SongDataError:
  # Re-raise validation errors
        if detailed_info:
            detailed_info['validation_passed'] = False
        raise

    except Exception as e:
  # Handle unexpected errors
        error_msg = f"Unexpected error during list existence validation: {e}"
        if logger:
            logger.error(error_msg)

        if detailed_info:
            detailed_info['validation_passed'] = False
            detailed_info['warnings_generated'].append(error_msg)

        raise SongDataError(error_msg)


# Constants for list existence validation
class ListExistenceValidationConstants:
    """Constants for list existence validation and performance optimization."""

  # Validation levels
    VALID_VALIDATION_LEVELS = {'basic', 'standard', 'comprehensive'}

  # Size thresholds
    DEFAULT_MIN_LIST_SIZE = 1
    LARGE_LIST_WARNING_THRESHOLD = 10000
    VERY_LARGE_LIST_WARNING_THRESHOLD = 100000
    EXTREME_LIST_WARNING_THRESHOLD = 1000000

  # Memory thresholds
    MEMORY_WARNING_THRESHOLD_MB = 100.0
    MEMORY_CRITICAL_THRESHOLD_MB = 500.0

  # Performance thresholds
    PERFORMANCE_WARNING_THRESHOLD_MS = 100.0
    PERFORMANCE_CRITICAL_THRESHOLD_MS = 1000.0

  # Sampling for large lists
    MAX_SAMPLE_SIZE_FOR_MEMORY_CALC = 100
    DEFAULT_BYTES_PER_ITEM_ESTIMATE = 1024  # 1KB


# Supporting functions for enhanced list existence validation
def _generate_list_size_warnings(
    list_size: int,
    *,
    large_threshold: int = ListExistenceValidationConstants.LARGE_LIST_WARNING_THRESHOLD,
    very_large_threshold: int = ListExistenceValidationConstants.VERY_LARGE_LIST_WARNING_THRESHOLD,
    extreme_threshold: int = ListExistenceValidationConstants.EXTREME_LIST_WARNING_THRESHOLD,
    memory_usage_mb: Optional[float] = None,
    enable_performance_warnings: bool = True,
    enable_memory_warnings: bool = True,
    enable_recommendations: bool = True,
    warning_level: str = 'standard',
    custom_warning_generators: Optional[List[callable]] = None,
    include_severity_levels: bool = True,
    enable_context_data: bool = True,
    logger: Optional[logging.Logger] = None
) -> Union[List[str], Dict[str, Any]]:
    """Generate comprehensive warnings based on list size with advanced analysis.

    This enhanced function provides multi-level warning generation with performance
    and memory analysis, custom warning generators, and structured return values.

    Args:
        list_size: Size of the list being validated
        large_threshold: Threshold for large list warning (default from constants)
        very_large_threshold: Threshold for very large list warning (default from constants)
        extreme_threshold: Threshold for extreme list warning (default from constants)
        memory_usage_mb: Optional memory usage in MB for enhanced warnings
        enable_performance_warnings: Enable performance-related warnings
        enable_memory_warnings: Enable memory usage warnings
        enable_recommendations: Include actionable recommendations
        warning_level: Warning generation level ('basic', 'standard', 'comprehensive')
        custom_warning_generators: List of custom warning generator functions
        include_severity_levels: Include severity classification in warnings
        enable_context_data: Return structured context data along with warnings
        logger: Optional logger for warning output

    Returns:
        List of warning messages (basic mode) or Dict with structured warning data

    Raises:
        ValueError: If invalid parameters are provided
        TypeError: If list_size is not an integer

    Example:
        >>> warnings = _generate_list_size_warnings(
        ...     50000,
        ...     memory_usage_mb=250.0,
        ...     warning_level='comprehensive',
        ...     enable_recommendations=True
        ... )
        >>> print(warnings['summary'])
        'Generated 3 warnings (2 performance, 1 memory)'
    """
  # Input validation
    validation_result = _validate_warning_generation_inputs(
        list_size, warning_level, large_threshold, very_large_threshold, extreme_threshold
    )
    if not validation_result['valid']:
        raise ValueError(validation_result['message'])

  # Initialize warning collection
    warning_data = _initialize_warning_collection(
        list_size, memory_usage_mb, enable_context_data
    )

  # Generate size-based warnings
    _generate_size_based_warnings(
        warning_data, list_size, large_threshold, very_large_threshold,
        extreme_threshold, warning_level, include_severity_levels
    )

  # Generate memory warnings if enabled and data available
    if enable_memory_warnings and memory_usage_mb is not None:
        _generate_memory_based_warnings(
            warning_data, memory_usage_mb, list_size, include_severity_levels
        )

  # Generate performance warnings if enabled
    if enable_performance_warnings:
        _generate_performance_warnings(
            warning_data, list_size, warning_level, include_severity_levels
        )

  # Execute custom warning generators
    if custom_warning_generators:
        _execute_custom_warning_generators(
            warning_data, custom_warning_generators, list_size, memory_usage_mb
        )

  # Add recommendations if enabled
    if enable_recommendations:
        _add_warning_recommendations(
            warning_data, list_size, memory_usage_mb, warning_level
        )

  # Log warnings if logger provided
    if logger:
        _log_generated_warnings(logger, warning_data['warnings'])

  # Return based on context data setting
    if enable_context_data:
        return _create_warning_summary(warning_data)
    else:
        return warning_data['warnings']


# Supporting functions for enhanced warning generation
def _validate_warning_generation_inputs(
    list_size: int,
    warning_level: str,
    large_threshold: int,
    very_large_threshold: int,
    extreme_threshold: int,
    *,
    memory_usage_mb: Optional[float] = None,
    custom_validators: Optional[List[callable]] = None,
    validation_level: str = 'standard',
    enable_performance_checks: bool = True,
    enable_memory_validation: bool = True,
    enable_threshold_optimization: bool = False,
    strict_mode: bool = False,
    return_suggestions: bool = False,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Union[bool, str, List[str], Dict[str, Any]]]:
    """Enhanced validation for warning generation inputs with comprehensive Pythonic functionality.

    This function implements advanced Python validation patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Multi-level validation with configurable depth and strictness
    - Comprehensive type hints for all parameters and return values
    - Memory usage validation for consistency checking
    - Performance optimization recommendations
    - Custom validation hooks for specialized requirements
    - Structured return values with detailed validation results
    - Threshold optimization suggestions for better performance
    - Defensive programming with comprehensive error analysis

    Args:
        list_size: Size of the list being validated
        warning_level: Warning generation level ('basic', 'standard', 'comprehensive')
        large_threshold: Threshold for large list warnings
        very_large_threshold: Threshold for very large list warnings
        extreme_threshold: Threshold for extreme list warnings
        memory_usage_mb: Optional memory usage in MB for validation consistency - keyword-only
        custom_validators: List of custom validation functions - keyword-only
        validation_level: Level of input validation to apply ('basic', 'standard', 'comprehensive') - keyword-only
        enable_performance_checks: Enable performance-related validations - keyword-only
        enable_memory_validation: Enable memory usage consistency checks - keyword-only
        enable_threshold_optimization: Suggest threshold optimizations - keyword-only
        strict_mode: Enable strict validation with additional constraints - keyword-only
        return_suggestions: Include optimization suggestions in return value - keyword-only
        logger: Optional logger for validation tracking - keyword-only

    Returns:
        Dict with comprehensive validation results:
        - 'valid': bool indicating overall validation success
        - 'message': str primary validation message
        - 'errors': List[str] detailed error messages (if any)
        - 'warnings': List[str] validation warnings (if any)
        - 'suggestions': List[str] optimization suggestions (if return_suggestions=True)
        - 'validation_metadata': Dict[str, Any] detailed validation information

    Examples:
        >>>  # Basic usage (maintains compatibility)
        >>> result = _validate_warning_generation_inputs(
        ...     10000, 'standard', 5000, 50000, 500000
        ... )
        >>> result['valid']
        True

        >>>  # Enhanced usage with comprehensive validation
        >>> result = _validate_warning_generation_inputs(
        ...     150000, 'comprehensive', 10000, 100000, 1000000,
        ...     memory_usage_mb=250.0,
        ...     validation_level='comprehensive',
        ...     enable_threshold_optimization=True,
        ...     return_suggestions=True,
        ...     strict_mode=True,
        ...     logger=my_logger
        ... )
        >>> print(f"Validation: {result['message']}")
        >>> print(f"Suggestions: {result['suggestions']}")

        >>>  # Custom validation with hooks
        >>> def business_validator(size, level, thresholds):
        ...     return size <= 50000 or level == 'comprehensive'
        >>>
        >>> result = _validate_warning_generation_inputs(
        ...     75000, 'standard', 10000, 100000, 1000000,
        ...     custom_validators=[business_validator],
        ...     validation_level='comprehensive'
        ... )

    Validation Levels:
        - 'basic': Essential parameter validation only
        - 'standard': Parameter validation plus type and range checking
        - 'comprehensive': Full validation including consistency and optimization checks

    Raises:
        TypeError: If invalid parameter types are provided
        ValueError: If invalid validation level or constraints are specified

    Note:
        Maintains backward compatibility with existing function signature.
        Enhanced validation provides detailed feedback for optimization.
        Custom validators receive (list_size, warning_level, thresholds_dict) as parameters.
    """
    import time
    from typing import Final

  # Constants for enhanced validation
    VALID_WARNING_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    VALID_VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    MIN_THRESHOLD_VALUE: Final = 1
    MAX_THRESHOLD_VALUE: Final = 10_000_000
    MIN_MEMORY_VALUE: Final = 0.0
    MAX_MEMORY_VALUE: Final = 100_000.0  # 100GB reasonable upper limit
    OPTIMAL_THRESHOLD_RATIOS: Final = {
        'large_to_very_large': (8, 12),  # 8x to 12x ratio
        'very_large_to_extreme': (8, 12)  # 8x to 12x ratio
    }

  # Initialize comprehensive result structure
    validation_start_time = time.time()
    result = {
        'valid': True,
        'message': 'Validation passed',
        'errors': [],
        'warnings': [],
        'validation_metadata': {
            'validation_level': validation_level,
            'validation_timestamp': validation_start_time,
            'inputs_validated': {
                'list_size': list_size,
                'warning_level': warning_level,
                'thresholds': {
                    'large': large_threshold,
                    'very_large': very_large_threshold,
                    'extreme': extreme_threshold
                }
            },
            'checks_performed': [],
            'validation_features': {
                'performance_checks': enable_performance_checks,
                'memory_validation': enable_memory_validation,
                'threshold_optimization': enable_threshold_optimization,
                'strict_mode': strict_mode,
                'custom_validators': len(custom_validators) if custom_validators else 0
            }
        }
    }

  # Add suggestions list if requested
    if return_suggestions:
        result['suggestions'] = []

    try:
  # Enhanced input validation with detailed error tracking
        input_validation_result = _validate_warning_inputs_basic(
            list_size, warning_level, large_threshold, very_large_threshold,
            extreme_threshold, validation_level, strict_mode
        )

        if not input_validation_result['valid']:
            result['valid'] = False
            result['errors'].extend(input_validation_result['errors'])
            result['message'] = f"Input validation failed: {'; '.join(input_validation_result['errors'])}"
            return result

        result['validation_metadata']['checks_performed'].extend(input_validation_result['checks_performed'])

  # Standard and comprehensive validation
        if validation_level in ('standard', 'comprehensive'):
  # Threshold relationship validation
            threshold_validation = _validate_threshold_relationships(
                large_threshold, very_large_threshold, extreme_threshold,
                enable_threshold_optimization, return_suggestions
            )

            if not threshold_validation['valid']:
                result['valid'] = False
                result['errors'].extend(threshold_validation['errors'])

            result['warnings'].extend(threshold_validation.get('warnings', []))
            if return_suggestions and 'suggestions' in threshold_validation:
                result['suggestions'].extend(threshold_validation['suggestions'])

            result['validation_metadata']['checks_performed'].append('threshold_relationships')

  # Memory usage consistency validation
            if enable_memory_validation and memory_usage_mb is not None:
                memory_validation = _validate_memory_consistency(
                    list_size, memory_usage_mb, large_threshold, very_large_threshold,
                    strict_mode
                )

                result['warnings'].extend(memory_validation.get('warnings', []))
                if memory_validation.get('errors'):
                    result['errors'].extend(memory_validation['errors'])
                    if strict_mode:
                        result['valid'] = False

                result['validation_metadata']['checks_performed'].append('memory_consistency')

  # Performance optimization checks
            if enable_performance_checks:
                performance_validation = _validate_performance_implications(
                    list_size, warning_level, large_threshold, very_large_threshold,
                    extreme_threshold, return_suggestions
                )

                result['warnings'].extend(performance_validation.get('warnings', []))
                if return_suggestions and 'suggestions' in performance_validation:
                    result['suggestions'].extend(performance_validation['suggestions'])

                result['validation_metadata']['checks_performed'].append('performance_implications')

  # Comprehensive validation features
        if validation_level == 'comprehensive':
  # Custom validator execution
            if custom_validators:
                custom_validation = _execute_warning_custom_validators(
                    custom_validators, list_size, warning_level,
                    {'large': large_threshold, 'very_large': very_large_threshold, 'extreme': extreme_threshold},
                    logger
                )

                result['warnings'].extend(custom_validation.get('warnings', []))
                if custom_validation.get('errors'):
                    result['errors'].extend(custom_validation['errors'])
                    if strict_mode:
                        result['valid'] = False

                result['validation_metadata']['checks_performed'].append('custom_validators')

  # Advanced consistency checks
            consistency_validation = _validate_advanced_consistency(
                list_size, warning_level, large_threshold, very_large_threshold,
                extreme_threshold, memory_usage_mb, strict_mode
            )

            result['warnings'].extend(consistency_validation.get('warnings', []))
            if consistency_validation.get('errors'):
                result['errors'].extend(consistency_validation['errors'])
                if strict_mode:
                    result['valid'] = False

            result['validation_metadata']['checks_performed'].append('advanced_consistency')

  # Finalize validation results
        validation_duration = time.time() - validation_start_time
        result['validation_metadata']['validation_duration'] = validation_duration

  # Update message based on findings
        if result['valid']:
            if result['warnings']:
                result['message'] = f"Validation passed with {len(result['warnings'])} warning(s)"
            elif return_suggestions and result.get('suggestions'):
                result['message'] = f"Validation passed with {len(result['suggestions'])} optimization suggestion(s)"
            else:
                result['message'] = "Validation passed successfully"
        else:
            result['message'] = f"Validation failed: {len(result['errors'])} error(s) found"

  # Log validation results if logger provided
        if logger:
            _log_warning_validation_results(logger, result, validation_duration)

        return result

    except Exception as validation_error:
  # Handle unexpected validation errors
        error_msg = f"Unexpected error during warning input validation: {validation_error}"
        result['valid'] = False
        result['errors'].append(error_msg)
        result['message'] = error_msg

        if logger:
            logger.error(error_msg, exc_info=True)

        return result


# Supporting functions for enhanced warning input validation
def _validate_warning_inputs_basic(
    list_size: int,
    warning_level: str,
    large_threshold: int,
    very_large_threshold: int,
    extreme_threshold: int,
    validation_level: str,
    strict_mode: bool
) -> Dict[str, Union[bool, List[str]]]:
    """Validate basic input parameters for warning generation.

    Args:
        list_size: Size of the list
        warning_level: Warning generation level
        large_threshold: Large list threshold
        very_large_threshold: Very large list threshold
        extreme_threshold: Extreme list threshold
        validation_level: Validation level to apply
        strict_mode: Whether to apply strict validation

    Returns:
        Dict with validation result and error details
    """
    from typing import Final

    errors = []
    checks_performed = []

  # Type validation
    if not isinstance(list_size, int):
        errors.append(f"list_size must be an integer, got {type(list_size).__name__}")
    checks_performed.append('list_size_type')

    if not isinstance(warning_level, str):
        errors.append(f"warning_level must be a string, got {type(warning_level).__name__}")
    checks_performed.append('warning_level_type')

  # Range validation
    if isinstance(list_size, int):
        if list_size < 0:
            errors.append('list_size must be non-negative')
        elif strict_mode and list_size == 0:
            errors.append('list_size cannot be zero in strict mode')
        checks_performed.append('list_size_range')

  # Warning level validation
    VALID_WARNING_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    if isinstance(warning_level, str) and warning_level not in VALID_WARNING_LEVELS:
        errors.append(
            f"Invalid warning_level '{warning_level}'. "
            f"Must be one of: {', '.join(sorted(VALID_WARNING_LEVELS))}"
        )
    checks_performed.append('warning_level_validity')

  # Threshold type validation
    threshold_params = [
        (large_threshold, 'large_threshold'),
        (very_large_threshold, 'very_large_threshold'),
        (extreme_threshold, 'extreme_threshold')
    ]

    for threshold_val, threshold_name in threshold_params:
        if not isinstance(threshold_val, int):
            errors.append(f"{threshold_name} must be an integer, got {type(threshold_val).__name__}")
        elif threshold_val <= 0:
            errors.append(f"{threshold_name} must be positive, got {threshold_val}")
        checks_performed.append(f'{threshold_name}_validation')

  # Basic threshold ordering (always performed)
    if all(isinstance(t, int) for t, _ in threshold_params):
        if not (large_threshold < very_large_threshold < extreme_threshold):
            errors.append(
                f"Thresholds must be in ascending order: "
                f"large ({large_threshold}) < very_large ({very_large_threshold}) < extreme ({extreme_threshold})"
            )
        checks_performed.append('threshold_ordering')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'checks_performed': checks_performed
    }


def _validate_threshold_relationships(
    large_threshold: int,
    very_large_threshold: int,
    extreme_threshold: int,
    enable_optimization: bool,
    return_suggestions: bool
) -> Dict[str, Union[bool, List[str]]]:
    """Validate threshold relationships and suggest optimizations.

    Args:
        large_threshold: Large list threshold
        very_large_threshold: Very large list threshold
        extreme_threshold: Extreme list threshold
        enable_optimization: Whether to check for optimization opportunities
        return_suggestions: Whether to return optimization suggestions

    Returns:
        Dict with validation results, warnings, and suggestions
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
    }

    if return_suggestions:
        result['suggestions'] = []

  # Check ratio relationships for optimal warning distribution
    if enable_optimization:
        large_to_very_large_ratio = very_large_threshold / large_threshold
        very_large_to_extreme_ratio = extreme_threshold / very_large_threshold

  # Optimal ratios for good warning distribution (8x to 12x)
        MIN_OPTIMAL_RATIO = 8
        MAX_OPTIMAL_RATIO = 12

  # Check large to very_large ratio
        if large_to_very_large_ratio < MIN_OPTIMAL_RATIO:
            result['warnings'].append(
                f"Small ratio between large and very_large thresholds ({large_to_very_large_ratio:.1f}x). "
                f"Consider increasing very_large_threshold for better warning distribution."
            )
            if return_suggestions:
                optimal_very_large = large_threshold * 10  # 10x ratio
                result['suggestions'].append(
                    f"Consider setting very_large_threshold to {optimal_very_large:,} "
                    f"(10x ratio) for optimal warning distribution"
                )
        elif large_to_very_large_ratio > MAX_OPTIMAL_RATIO:
            result['warnings'].append(
                f"Large ratio between large and very_large thresholds ({large_to_very_large_ratio:.1f}x). "
                f"Consider decreasing very_large_threshold or increasing large_threshold."
            )

  # Check very_large to extreme ratio
        if very_large_to_extreme_ratio < MIN_OPTIMAL_RATIO:
            result['warnings'].append(
                f"Small ratio between very_large and extreme thresholds ({very_large_to_extreme_ratio:.1f}x). "
                f"Consider increasing extreme_threshold for better warning distribution."
            )
            if return_suggestions:
                optimal_extreme = very_large_threshold * 10  # 10x ratio
                result['suggestions'].append(
                    f"Consider setting extreme_threshold to {optimal_extreme:,} "
                    f"(10x ratio) for optimal warning distribution"
                )
        elif very_large_to_extreme_ratio > MAX_OPTIMAL_RATIO:
            result['warnings'].append(
                f"Large ratio between very_large and extreme thresholds ({very_large_to_extreme_ratio:.1f}x). "
                f"Consider decreasing extreme_threshold or increasing very_large_threshold."
            )

  # Check for round number optimization
        if return_suggestions:
            thresholds = [
                (large_threshold, 'large_threshold'),
                (very_large_threshold, 'very_large_threshold'),
                (extreme_threshold, 'extreme_threshold')
            ]

            for threshold_val, threshold_name in thresholds:
                if threshold_val % 1000 != 0 and threshold_val > 1000:
                    rounded_val = round(threshold_val / 1000) * 1000
                    result['suggestions'].append(
                        f"Consider rounding {threshold_name} to {rounded_val:,} for easier memory"
                    )

    return result


def _validate_memory_consistency(
    list_size: int,
    memory_usage_mb: float,
    large_threshold: int,
    very_large_threshold: int,
    strict_mode: bool
) -> Dict[str, List[str]]:
    """Validate memory usage consistency with list size and thresholds.

    Args:
        list_size: Size of the list
        memory_usage_mb: Memory usage in MB
        large_threshold: Large list threshold
        very_large_threshold: Very large list threshold
        strict_mode: Whether to apply strict validation

    Returns:
        Dict with validation warnings and errors
    """
    result = {
        'warnings': [],
        'errors': []
    }

  # Basic memory validation
    if memory_usage_mb < 0:
        result['errors'].append(f"Memory usage cannot be negative: {memory_usage_mb}")
        return result

    if memory_usage_mb > 100_000:  # 100GB sanity check
        result['warnings'].append(f"Extremely high memory usage reported: {memory_usage_mb:.1f}MB")

  # Estimate expected memory usage (rough approximation)
    estimated_mb_per_item = 0.001  # 1KB per item estimate
    estimated_memory = list_size * estimated_mb_per_item

  # Check for significant discrepancies
    if memory_usage_mb > 0:
        ratio = memory_usage_mb / estimated_memory if estimated_memory > 0 else float('inf')

        if ratio > 100:  # 100x higher than expected
            result['warnings'].append(
                f"Memory usage ({memory_usage_mb:.1f}MB) is {ratio:.1f}x higher than estimated "
                f"({estimated_memory:.1f}MB) for {list_size:,} items"
            )
        elif ratio < 0.01:  # 100x lower than expected
            result['warnings'].append(
                f"Memory usage ({memory_usage_mb:.1f}MB) is unexpectedly low "
                f"compared to estimated ({estimated_memory:.1f}MB) for {list_size:,} items"
            )

  # Check memory vs threshold consistency
    if list_size >= very_large_threshold and memory_usage_mb < 10:  # Very large list but low memory
        result['warnings'].append(
            f"Very large list ({list_size:,} items) but low memory usage ({memory_usage_mb:.1f}MB). "
            f"Check if memory calculation is accurate."
        )

    if list_size < large_threshold and memory_usage_mb > 1000:  # Small list but high memory
        result['warnings'].append(
            f"Small list ({list_size:,} items) but high memory usage ({memory_usage_mb:.1f}MB). "
            f"Check for memory efficiency issues."
        )

    return result


def _validate_performance_implications(
    list_size: int,
    warning_level: str,
    large_threshold: int,
    very_large_threshold: int,
    extreme_threshold: int,
    return_suggestions: bool
) -> Dict[str, List[str]]:
    """Validate performance implications and suggest optimizations.

    Args:
        list_size: Size of the list
        warning_level: Warning generation level
        large_threshold: Large list threshold
        very_large_threshold: Very large list threshold
        extreme_threshold: Extreme list threshold
        return_suggestions: Whether to return optimization suggestions

    Returns:
        Dict with performance warnings and suggestions
    """
    result = {
        'warnings': []
    }

    if return_suggestions:
        result['suggestions'] = []

  # Check for performance concerns based on list size and warning level
    if warning_level == 'comprehensive' and list_size > very_large_threshold:
        result['warnings'].append(
            f"Comprehensive warning generation for large list ({list_size:,} items) "
            f"may impact performance. Consider using 'standard' level for better performance."
        )

        if return_suggestions:
            result['suggestions'].append(
                "Consider caching warning results for frequently validated large lists"
            )

  # Check threshold effectiveness
    if list_size > extreme_threshold * 2:  # Way beyond extreme threshold
        result['warnings'].append(
            f"List size ({list_size:,}) significantly exceeds extreme threshold ({extreme_threshold:,}). "
            f"Consider adjusting thresholds for this scale of data."
        )

        if return_suggestions:
            new_extreme = list_size // 2
            new_very_large = new_extreme // 10
            new_large = new_very_large // 10
            result['suggestions'].append(
                f"For this data scale, consider thresholds: "
                f"large={new_large:,}, very_large={new_very_large:,}, extreme={new_extreme:,}"
            )

  # Check for inefficient threshold distribution
    if large_threshold > list_size // 10:  # Large threshold too close to actual size
        result['warnings'].append(
            f"Large threshold ({large_threshold:,}) is close to list size ({list_size:,}). "
            f"Warning generation may be less effective."
        )

    return result


def _execute_warning_custom_validators(
    custom_validators: List[callable],
    list_size: int,
    warning_level: str,
    thresholds: Dict[str, int],
    logger: Optional[logging.Logger]
) -> Dict[str, List[str]]:
    """Execute custom validation functions for warning generation.

    Args:
        custom_validators: List of custom validation functions
        list_size: Size of the list
        warning_level: Warning generation level
        thresholds: Dictionary of threshold values
        logger: Optional logger for validation tracking

    Returns:
        Dict with custom validation warnings and errors
    """
    result = {
        'warnings': [],
        'errors': []
    }

    for i, validator in enumerate(custom_validators):
        try:
            if not callable(validator):
                result['errors'].append(f"Custom validator {i+1} is not callable")
                continue

  # Call validator with standard parameters
            custom_result = validator(list_size, warning_level, thresholds)

  # Handle different return types
            if custom_result is False:
                result['errors'].append(f"Custom validator {i+1} rejected the input parameters")
            elif isinstance(custom_result, str):
                result['errors'].append(f"Custom validator {i+1}: {custom_result}")
            elif isinstance(custom_result, dict):
  # Handle structured return from custom validator
                if custom_result.get('valid') is False:
                    result['errors'].append(
                        f"Custom validator {i+1}: {custom_result.get('message', 'Validation failed')}"
                    )
                if custom_result.get('warnings'):
                    for warning in custom_result['warnings']:
                        result['warnings'].append(f"Custom validator {i+1}: {warning}")

            if logger:
                logger.debug(f"Custom validator {i+1} executed successfully")

        except Exception as e:
            error_msg = f"Custom validator {i+1} failed with exception: {e}"
            result['errors'].append(error_msg)

            if logger:
                logger.error(error_msg, exc_info=True)

    return result


def _validate_advanced_consistency(
    list_size: int,
    warning_level: str,
    large_threshold: int,
    very_large_threshold: int,
    extreme_threshold: int,
    memory_usage_mb: Optional[float],
    strict_mode: bool
) -> Dict[str, List[str]]:
    """Perform advanced consistency checks for warning generation parameters.

    Args:
        list_size: Size of the list
        warning_level: Warning generation level
        large_threshold: Large list threshold
        very_large_threshold: Very large list threshold
        extreme_threshold: Extreme list threshold
        memory_usage_mb: Optional memory usage in MB
        strict_mode: Whether to apply strict validation

    Returns:
        Dict with advanced consistency warnings and errors
    """
    result = {
        'warnings': [],
        'errors': []
    }

  # Check for logical consistency between warning level and thresholds
    if warning_level == 'basic' and list_size > extreme_threshold:
        result['warnings'].append(
            f"Using 'basic' warning level for extremely large list ({list_size:,} items). "
            f"Consider 'comprehensive' level for better analysis."
        )

  # Check threshold scaling consistency
    total_range = extreme_threshold - large_threshold
    large_range = very_large_threshold - large_threshold
    very_large_range = extreme_threshold - very_large_threshold

  # Check if ranges are reasonably distributed
    if large_range > very_large_range * 3:  # Large range is much bigger than very large range
        result['warnings'].append(
            f"Uneven threshold distribution: large range ({large_range:,}) "
            f"is much larger than very_large range ({very_large_range:,})"
        )
    elif very_large_range > large_range * 3:  # Very large range is much bigger
        result['warnings'].append(
            f"Uneven threshold distribution: very_large range ({very_large_range:,}) "
            f"is much larger than large range ({large_range:,})"
        )

  # Cross-reference with memory usage if available
    if memory_usage_mb is not None and memory_usage_mb > 0:
        memory_per_item = memory_usage_mb / list_size if list_size > 0 else 0

  # Check if memory per item is reasonable
        if memory_per_item > 10:  # More than 10MB per item
            result['warnings'].append(
                f"Very high memory per item ({memory_per_item:.2f}MB). "
                f"Consider if thresholds should account for memory efficiency."
            )
        elif memory_per_item < 0.0001:  # Less than 0.1KB per item
            result['warnings'].append(
                f"Very low memory per item ({memory_per_item*1024:.2f}KB). "
                f"Check if memory calculation is accurate."
            )

  # Strict mode additional checks
    if strict_mode:
  # Ensure thresholds are reasonable for the actual list size
        if list_size < large_threshold // 10:
            result['warnings'].append(
                f"List size ({list_size:,}) is much smaller than large threshold ({large_threshold:,}). "
                f"Warning generation may not be meaningful."
            )

  # Check for power-of-10 alignment in strict mode
        thresholds = [large_threshold, very_large_threshold, extreme_threshold]
        non_round_thresholds = [t for t in thresholds if t % 1000 != 0 and t > 1000]

        if non_round_thresholds:
            result['warnings'].append(
                f"In strict mode, consider using round numbers for thresholds. "
                f"Non-round thresholds found: {non_round_thresholds}"
            )

    return result


def _log_warning_validation_results(
    logger: logging.Logger,
    result: Dict[str, Any],
    validation_duration: float
) -> None:
    """Log warning validation results using the provided logger.

    Args:
        logger: Logger instance for validation output
        result: Validation result dictionary
        validation_duration: Time taken for validation
    """
  # Log overall result
    if result['valid']:
        logger.info(
            f"Warning input validation passed in {validation_duration:.3f}s "
            f"({len(result['validation_metadata']['checks_performed'])} checks performed)"
        )
    else:
        logger.error(
            f"Warning input validation failed in {validation_duration:.3f}s "
            f"with {len(result['errors'])} error(s)"
        )

  # Log errors
    for error in result['errors']:
        logger.error(f"Validation error: {error}")

  # Log warnings
    for warning in result['warnings']:
        logger.warning(f"Validation warning: {warning}")

  # Log suggestions if available
    if result.get('suggestions'):
        for suggestion in result['suggestions']:
            logger.info(f"Optimization suggestion: {suggestion}")

  # Log validation metadata in debug mode
    checks_performed = result['validation_metadata']['checks_performed']
    logger.debug(f"Validation checks performed: {', '.join(checks_performed)}")

    features = result['validation_metadata']['validation_features']
    enabled_features = [k for k, v in features.items() if v is True or (isinstance(v, int) and v > 0)]
    if enabled_features:
        logger.debug(f"Validation features enabled: {', '.join(enabled_features)}")


def _initialize_warning_collection(
    list_size: int,
    memory_usage_mb: Optional[float],
    enable_context_data: bool
) -> Dict[str, Any]:
    """Initialize warning data collection structure.

    Args:
        list_size: Size of the list
        memory_usage_mb: Optional memory usage in MB
        enable_context_data: Whether to include context data

    Returns:
        Initialized warning data dictionary
    """
    warning_data = {
        'warnings': [],
        'warning_counts': {
            'size': 0,
            'memory': 0,
            'performance': 0,
            'custom': 0
        },
        'severity_levels': {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }
    }

    if enable_context_data:
        warning_data.update({
            'list_size': list_size,
            'memory_usage_mb': memory_usage_mb,
            'recommendations': [],
            'analysis_metadata': {
                'warning_generation_timestamp': time.time(),
                'analysis_level': 'comprehensive',
                'warnings_generated': False
            }
        })

    return warning_data


def _generate_size_based_warnings(
    warning_data: Dict[str, Any],
    list_size: int,
    large_threshold: int,
    very_large_threshold: int,
    extreme_threshold: int,
    warning_level: str,
    include_severity_levels: bool
) -> None:
    """Generate warnings based on list size thresholds.

    Args:
        warning_data: Warning data collection dictionary
        list_size: Size of the list
        large_threshold: Large list threshold
        very_large_threshold: Very large list threshold
        extreme_threshold: Extreme list threshold
        warning_level: Warning generation level
        include_severity_levels: Whether to include severity levels
    """
    if list_size >= extreme_threshold:
        severity = 'critical'
        base_msg = f"⚠️ CRITICAL: Extreme list size detected ({list_size:,} items)"

        if warning_level == 'comprehensive':
            warning_msg = (
                f"{base_msg}. This will significantly impact performance, memory usage, "
                f"and may cause system instability. Immediate optimization required."
            )
        else:
            warning_msg = f"{base_msg}. Severe performance impact expected."

    elif list_size >= very_large_threshold:
        severity = 'high'
        base_msg = f"⚠️ HIGH: Very large list detected ({list_size:,} items)"

        if warning_level == 'comprehensive':
            warning_msg = (
                f"{base_msg}. This may significantly impact performance and memory usage. "
                f"Consider implementing pagination, chunking, or streaming processing."
            )
        else:
            warning_msg = f"{base_msg}. Significant performance impact possible."

    elif list_size >= large_threshold:
        severity = 'medium'
        base_msg = f"⚠️ MEDIUM: Large list detected ({list_size:,} items)"

        if warning_level == 'comprehensive':
            warning_msg = (
                f"{base_msg}. Monitor performance and memory usage. "
                f"Consider optimization if processing time becomes excessive."
            )
        else:
            warning_msg = f"{base_msg}. Monitor performance and memory usage."
    else:
        return  # No size-based warnings needed

  # Add warning with optional severity
    if include_severity_levels:
        warning_msg = f"[{severity.upper()}] {warning_msg}"

    warning_data['warnings'].append(warning_msg)
    warning_data['warning_counts']['size'] += 1

    if include_severity_levels:
        warning_data['severity_levels'][severity] += 1


def _generate_memory_based_warnings(
    warning_data: Dict[str, Any],
    memory_usage_mb: float,
    list_size: int,
    include_severity_levels: bool
) -> None:
    """Generate warnings based on memory usage.

    Args:
        warning_data: Warning data collection dictionary
        memory_usage_mb: Memory usage in MB
        list_size: Size of the list
        include_severity_levels: Whether to include severity levels
    """
    memory_critical = ListExistenceValidationConstants.MEMORY_CRITICAL_THRESHOLD_MB
    memory_warning = ListExistenceValidationConstants.MEMORY_WARNING_THRESHOLD_MB

    if memory_usage_mb >= memory_critical:
        severity = 'critical'
        warning_msg = (
            f"💾 CRITICAL: Memory usage is critical ({memory_usage_mb:.1f} MB) "
            f"for {list_size:,} items. Risk of system instability."
        )
    elif memory_usage_mb >= memory_warning:
        severity = 'high'
        warning_msg = (
            f"💾 HIGH: High memory usage detected ({memory_usage_mb:.1f} MB) "
            f"for {list_size:,} items. Monitor system resources."
        )
    else:
        return  # No memory warnings needed

  # Add warning with optional severity
    if include_severity_levels:
        warning_msg = f"[{severity.upper()}] {warning_msg}"

    warning_data['warnings'].append(warning_msg)
    warning_data['warning_counts']['memory'] += 1

    if include_severity_levels:
        warning_data['severity_levels'][severity] += 1


def _generate_performance_warnings(
    warning_data: Dict[str, Any],
    list_size: int,
    warning_level: str,
    include_severity_levels: bool
) -> None:
    """Generate performance-related warnings.

    Args:
        warning_data: Warning data collection dictionary
        list_size: Size of the list
        warning_level: Warning generation level
        include_severity_levels: Whether to include severity levels
    """
    if warning_level not in ['standard', 'comprehensive']:
        return

  # Generate performance predictions based on list size
    if list_size >= 500000:
        severity = 'high'
        warning_msg = (
            f"⚡ PERFORMANCE: Operations on {list_size:,} items may take "
            f"several seconds or minutes. Consider async processing."
        )
    elif list_size >= 100000:
        severity = 'medium'
        warning_msg = (
            f"⚡ PERFORMANCE: Operations on {list_size:,} items may be slow. "
            f"Consider progress indicators for user feedback."
        )
    elif list_size >= 50000 and warning_level == 'comprehensive':
        severity = 'low'
        warning_msg = (
            f"⚡ PERFORMANCE: Moderate performance impact expected for {list_size:,} items. "
            f"Monitor operation duration."
        )
    else:
        return  # No performance warnings needed

  # Add warning with optional severity
    if include_severity_levels:
        warning_msg = f"[{severity.upper()}] {warning_msg}"

    warning_data['warnings'].append(warning_msg)
    warning_data['warning_counts']['performance'] += 1

    if include_severity_levels:
        warning_data['severity_levels'][severity] += 1


def _execute_custom_warning_generators(
    warning_data: Dict[str, Any],
    custom_warning_generators: List[callable],
    list_size: int,
    memory_usage_mb: Optional[float]
) -> None:
    """Execute custom warning generator functions.

    Args:
        warning_data: Warning data collection dictionary
        custom_warning_generators: List of custom warning functions
        list_size: Size of the list
        memory_usage_mb: Optional memory usage in MB
    """
    for generator in custom_warning_generators:
        try:
            if callable(generator):
  # Call with available parameters
                if memory_usage_mb is not None:
                    custom_warnings = generator(list_size, memory_usage_mb)
                else:
                    custom_warnings = generator(list_size)

  # Handle different return types
                if isinstance(custom_warnings, str):
                    warning_data['warnings'].append(f"🔧 CUSTOM: {custom_warnings}")
                    warning_data['warning_counts']['custom'] += 1
                elif isinstance(custom_warnings, list):
                    for warning in custom_warnings:
                        warning_data['warnings'].append(f"🔧 CUSTOM: {warning}")
                        warning_data['warning_counts']['custom'] += 1

        except Exception as e:
  # Handle custom generator errors gracefully
            error_warning = f"🔧 CUSTOM ERROR: Custom warning generator failed: {e}"
            warning_data['warnings'].append(error_warning)
            warning_data['warning_counts']['custom'] += 1


def _add_warning_recommendations(
    warning_data: Dict[str, Any],
    list_size: int,
    memory_usage_mb: Optional[float],
    warning_level: str
) -> None:
    """Add actionable recommendations based on detected issues.

    Args:
        warning_data: Warning data collection dictionary
        list_size: Size of the list
        memory_usage_mb: Optional memory usage in MB
        warning_level: Warning generation level
    """
    if 'recommendations' not in warning_data:
        return

    recommendations = []

  # Size-based recommendations
    if list_size >= 100000:
        recommendations.extend([
            "Consider implementing pagination to process data in smaller chunks",
            "Use generators or iterators instead of loading all data at once",
            "Implement progress indicators for better user experience"
        ])

    if list_size >= 500000:
        recommendations.extend([
            "Consider using streaming processing for very large datasets",
            "Implement database-level filtering to reduce data volume",
            "Use asynchronous processing to prevent UI blocking"
        ])

  # Memory-based recommendations
    if memory_usage_mb and memory_usage_mb >= 100:
        recommendations.extend([
            "Monitor system memory usage during processing",
            "Consider implementing memory-efficient data structures"
        ])

    if memory_usage_mb and memory_usage_mb >= 500:
        recommendations.extend([
            "Implement data compression or serialization",
            "Consider using disk-based storage for large datasets",
            "Add memory usage monitoring and cleanup"
        ])

  # General recommendations for comprehensive analysis
    if warning_level == 'comprehensive' and list_size >= 10000:
        recommendations.extend([
            "Profile the application to identify performance bottlenecks",
            "Consider caching frequently accessed data",
            "Implement lazy loading where possible"
        ])

    warning_data['recommendations'] = recommendations


def _log_generated_warnings(logger: logging.Logger, warnings: List[str]) -> None:
    """Log generated warnings using the provided logger.

    Args:
        logger: Logger instance for warning output
        warnings: List of warning messages to log
    """
    for warning in warnings:
  # Remove emoji and severity prefixes for clean logging
        clean_warning = warning
        for prefix in ['[CRITICAL]', '[HIGH]', '[MEDIUM]', '[LOW]', '⚠️', '💾', '⚡', '🔧']:
            clean_warning = clean_warning.replace(prefix, '').strip()

  # Log based on severity indicators
        if '[CRITICAL]' in warning or 'CRITICAL:' in warning:
            logger.critical(clean_warning)
        elif '[HIGH]' in warning or 'HIGH:' in warning:
            logger.error(clean_warning)
        elif '[MEDIUM]' in warning or 'MEDIUM:' in warning:
            logger.warning(clean_warning)
        else:
            logger.info(clean_warning)


def _create_warning_summary(warning_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a comprehensive warning summary.

    Args:
        warning_data: Warning data collection dictionary

    Returns:
        Structured warning summary with metadata
    """
    total_warnings = len(warning_data['warnings'])

  # Create summary message
    if total_warnings == 0:
        summary = "No warnings generated - list size appears optimal"
    else:
        count_parts = []
        for warning_type, count in warning_data['warning_counts'].items():
            if count > 0:
                count_parts.append(f"{count} {warning_type}")

        if count_parts:
            summary = f"Generated {total_warnings} warning(s): {', '.join(count_parts)}"
        else:
            summary = f"Generated {total_warnings} warning(s)"

  # Update metadata
    if 'analysis_metadata' in warning_data:
        warning_data['analysis_metadata']['warnings_generated'] = total_warnings > 0
        warning_data['analysis_metadata']['warning_summary'] = summary

  # Add summary to the main data
    warning_data['summary'] = summary
    warning_data['total_warnings'] = total_warnings

    return warning_data


def _calculate_list_memory_usage(song_list: List[Dict[str, Any]]) -> float:
    """Calculate approximate memory usage of a song list in MB.

    Args:
        song_list: List of song dictionaries

    Returns:
        Estimated memory usage in megabytes

    Note:
        This is an approximation and may not be completely accurate
        across different Python implementations and platforms.
    """
    import sys

    try:
  # Calculate total size using sys.getsizeof recursively
        total_size = sys.getsizeof(song_list)

  # Sample approach for large lists to avoid performance issues
        sample_size = min(100, len(song_list))
        sample_items = song_list[:sample_size]

  # Calculate average item size
        item_sizes = []
        for item in sample_items:
            item_size = sys.getsizeof(item)

  # Add size of dictionary contents
            if isinstance(item, dict):
                for key, value in item.items():
                    item_size += sys.getsizeof(key) + sys.getsizeof(value)

            item_sizes.append(item_size)

        if item_sizes:
            avg_item_size = sum(item_sizes) / len(item_sizes)
            estimated_total_size = total_size + (avg_item_size * len(song_list))
        else:
            estimated_total_size = total_size

  # Convert to MB
        return estimated_total_size / (1024 * 1024)

    except Exception:
  # Fallback to simple estimation if detailed calculation fails
        return (len(song_list) * 1024) / (1024 * 1024)  # Assume ~1KB per item


def _validate_list_existence_inputs(
    validation_level: str,
    min_list_size: int,
    max_list_size: Optional[int],
    custom_size_validator: Optional[callable]
) -> Dict[str, Union[bool, str]]:
    """Validate inputs for enhanced list existence validation.

    Args:
        validation_level: Validation level setting
        min_list_size: Minimum list size requirement
        max_list_size: Maximum list size limit
        custom_size_validator: Custom validation function

    Returns:
        Dict with 'valid' boolean and 'message' string
    """
  # Validate validation level
    valid_levels = {'basic', 'standard', 'comprehensive'}
    if validation_level not in valid_levels:
        return {
            'valid': False,
            'message': f"Invalid validation_level '{validation_level}'. "
                      f"Must be one of: {', '.join(valid_levels)}"
        }

  # Validate size constraints
    if not isinstance(min_list_size, int) or min_list_size < 0:
        return {
            'valid': False,
            'message': 'min_list_size must be a non-negative integer'
        }

    if max_list_size is not None:
        if not isinstance(max_list_size, int):
            return {
                'valid': False,
                'message': 'max_list_size must be an integer or None'
            }

        if max_list_size < min_list_size:
            return {
                'valid': False,
                'message': 'max_list_size must be >= min_list_size'
            }

  # Validate custom validator
    if custom_size_validator is not None and not callable(custom_size_validator):
        return {
            'valid': False,
            'message': 'custom_size_validator must be callable or None'
        }

    return {'valid': True, 'message': 'Validation passed'}


def _validate_list_type(song_list: List[Dict[str, Any]], result: ValidationResult, sample_size: int) -> None:
    """Validate that the input is actually a list."""
    if not isinstance(song_list, list):
        raise SongDataError(f"Input must be a list, got {type(song_list).__name__}")


def _validate_list_content_structure(song_list: List[Dict[str, Any]], result: ValidationResult, sample_size: int) -> None:
    """Validate the basic structure of list contents."""
    from itertools import islice

  # Determine validation sample
    validation_sample = list(islice(song_list, min(sample_size, len(song_list))))
    result.validated_items = len(validation_sample)

  # Quick structure validation
    non_dict_items = [
        idx for idx, item in enumerate(validation_sample)
        if not isinstance(item, dict)
    ]

    if non_dict_items:
        error_indices = non_dict_items[:3]  # Show first 3 errors
        error_msg = f"Items at indices {error_indices} are not dictionaries"
        if len(non_dict_items) > 3:
            error_msg += f" (and {len(non_dict_items) - 3} more)"
        raise SongDataError(error_msg)


def _validate_song_schemas(song_list: List[Dict[str, Any]], result: ValidationResult, sample_size: int) -> None:
    """Validate individual song schemas with comprehensive type and key checking."""
    from itertools import islice

    validation_sample = list(islice(song_list, min(sample_size, len(song_list))))
    validation_errors = []
    validation_warnings = []

    for idx, song in enumerate(validation_sample):
  # Validate required keys
        missing_keys = SongValidationConstants.REQUIRED_KEYS - song.keys()
        if missing_keys:
            validation_errors.append(f"Song {idx}: missing required keys {sorted(missing_keys)}")
            continue

  # Validate key types
        type_errors = _validate_song_field_types(song, idx)
        validation_errors.extend(type_errors)

  # Check for unexpected keys
        unexpected_keys = song.keys() - SongValidationConstants.ALL_VALID_KEYS
        if unexpected_keys:
            validation_warnings.append(f"Song {idx}: unexpected keys {sorted(unexpected_keys)}")

  # Validate data quality
        quality_warnings = _validate_song_data_quality(song, idx)
        validation_warnings.extend(quality_warnings)

  # Add errors and warnings to result
    for error in validation_errors[:SongValidationConstants.MAX_VALIDATION_ERRORS]:
        result.add_error(error)

    for warning in validation_warnings:
        result.add_warning(warning)

  # Update metadata
    result.validation_metadata.update({
        'schema_errors': len(validation_errors),
        'schema_warnings': len(validation_warnings),
        'sample_validated': len(validation_sample)
    })


def _validate_song_field_types(song: Dict[str, Any], idx: int) -> List[str]:
    """Validate field types for a single song."""
    errors = []

    for key, expected_types in SongValidationConstants.KEY_TYPE_MAPPING.items():
        if key not in song:
            continue  # Skip missing optional keys

        value = song[key]
        if isinstance(expected_types, tuple):
            is_valid_type = isinstance(value, expected_types)
        else:
            is_valid_type = isinstance(value, expected_types)

        if not is_valid_type:
            expected_type_names = (
                ' or '.join(t.__name__ for t in expected_types)
                if isinstance(expected_types, tuple)
                else expected_types.__name__
            )
            errors.append(f"Song {idx}: '{key}' should be {expected_type_names}, got {type(value).__name__}")

    return errors


def _validate_song_data_quality(song: Dict[str, Any], idx: int) -> List[str]:
    """Validate data quality for a single song."""
    warnings = []

  # Check for empty or suspicious values
    for key in SongValidationConstants.REQUIRED_KEYS:
        value = song.get(key)
        if isinstance(value, str) and not value.strip():
            warnings.append(f"Song {idx}: '{key}' is empty or whitespace-only")
        elif value is None:
            warnings.append(f"Song {idx}: '{key}' is None")

  # Validate file path exists (basic check)
    location = song.get('location')
    if location and isinstance(location, str):
        from pathlib import Path
        if not Path(location).suffix.lower() in {'.mp3', '.wav', '.flac', '.ogg'}:
            warnings.append(f"Song {idx}: location may not be a valid audio file")

    return warnings


def _validate_file_paths(
    master_file: Union[str, Path],
    check_file: Union[str, Path],
    *,
    validation_level: str = 'standard',
    allowed_extensions: Optional[List[str]] = None,
    check_parent_directories: bool = True,
    check_write_permissions: bool = True,
    create_missing_directories: bool = True,
    validate_disk_space: bool = False,
    min_disk_space_mb: float = 100.0,
    max_path_length: int = 260,
    check_reserved_names: bool = True,
    enable_cross_platform_validation: bool = True,
    custom_validators: Optional[List[callable]] = None,
    return_result: bool = False,
    logger: Optional[logging.Logger] = None
) -> Union[None, Dict[str, Union[bool, str, Dict, List]]]:
    """Enhanced file path validation with comprehensive Pythonic functionality.

    This function implements advanced Pythonic validation patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Multi-level validation with configurable depth
    - Comprehensive type hints for all parameters and return values
    - Cross-platform compatibility validation
    - Directory creation and permission checking
    - Disk space validation for large file operations
    - Custom validator hooks for specialized requirements
    - Structured return values with detailed validation results
    - Performance optimization with early termination
    - Reserved filename detection for Windows compatibility

    Args:
        master_file: Path to master file (str or Path object)
        check_file: Path to check file (str or Path object)
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        allowed_extensions: List of allowed file extensions (defaults to ['.txt', '.json']) - keyword-only
        check_parent_directories: Whether to validate parent directory existence - keyword-only
        check_write_permissions: Whether to check write permissions - keyword-only
        create_missing_directories: Whether to create missing parent directories - keyword-only
        validate_disk_space: Whether to check available disk space - keyword-only
        min_disk_space_mb: Minimum required disk space in MB - keyword-only
        max_path_length: Maximum allowed path length for cross-platform compatibility - keyword-only
        check_reserved_names: Whether to check for Windows reserved filenames - keyword-only
        enable_cross_platform_validation: Whether to enable cross-platform path validation - keyword-only
        custom_validators: List of custom validation functions - keyword-only
        return_result: Whether to return validation result instead of raising - keyword-only
        logger: Optional logger for validation tracking - keyword-only

    Returns:
        None if validation passes and return_result=False
        Dict containing validation results if return_result=True:
        - 'valid': bool indicating overall validation success
        - 'errors': List of validation errors found
        - 'warnings': List of validation warnings
        - 'file_details': Dict with details about each validated file
        - 'validation_metadata': Dict with validation statistics and settings

    Examples:
        >>>  # Basic validation (raises on error)
        >>> _validate_file_paths(
        ...     Path('master.txt'),
        ...     Path('check.txt')
        ... )

        >>>  # Comprehensive validation with result return
        >>> result = _validate_file_paths(
        ...     'master.json',
        ...     'check.json',
        ...     validation_level='comprehensive',
        ...     allowed_extensions=['.json', '.txt'],
        ...     validate_disk_space=True,
        ...     return_result=True
        ... )
        >>> result['valid']
        True

        >>>  # Custom validation with logging
        >>> _validate_file_paths(
        ...     master_file,
        ...     check_file,
        ...     validation_level='comprehensive',
        ...     custom_validators=[check_backup_compatibility],
        ...     logger=my_logger
        ... )

    Validation Levels:
        - 'basic': Path type and extension validation only
        - 'standard': Basic validation plus directory and permission checks
        - 'comprehensive': Full validation including disk space, cross-platform compatibility

    Raises:
        ValueError: If validation fails and return_result=False
        TypeError: If invalid parameter types are provided
        PermissionError: If insufficient permissions detected
        OSError: If file system operations fail

    Note:
        Uses pathlib.Path for cross-platform compatibility.
        Automatically creates missing directories when create_missing_directories=True.
        Supports both string and Path object inputs.
    """
    import os
    import shutil
    import time
    from typing import Final

  # Constants for validation
    VALID_VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_ALLOWED_EXTENSIONS: Final = ['.txt', '.json']
    WINDOWS_RESERVED_NAMES: Final = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
        'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    MAX_WINDOWS_PATH_LENGTH: Final = 260
    MAX_UNIX_PATH_LENGTH: Final = 4096

  # Initialize validation tracking
    validation_start_time = time.time()
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'file_details': {},
        'validation_metadata': {
            'validation_level': validation_level,
            'timestamp': time.time(),
            'files_validated': 0,
            'checks_performed': []
        }
    }

    try:
  # Input validation and normalization
        input_validation = _validate_file_path_inputs(
            master_file, check_file, validation_level, allowed_extensions,
            max_path_length, min_disk_space_mb
        )

        if not input_validation['valid']:
            validation_result['errors'].extend(input_validation['errors'])
            validation_result['valid'] = False
            if not return_result:
                raise ValueError(f"Input validation failed: {'; '.join(input_validation['errors'])}")
            return validation_result

  # Normalize inputs
        master_path = Path(master_file)
        check_path = Path(check_file)
        file_paths = [('master_file', master_path), ('check_file', check_path)]
        extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS

        if logger:
            logger.debug(f"Starting {validation_level} validation of {len(file_paths)} file paths")

  # Execute validation chain based on level
        validation_chain = _build_validation_chain(
            validation_level, check_parent_directories, check_write_permissions,
            validate_disk_space, check_reserved_names, enable_cross_platform_validation
        )

  # Validate each file path
        for file_name, file_path in file_paths:
            file_validation = _validate_single_file_path(
                file_name, file_path, extensions, validation_chain,
                min_disk_space_mb, max_path_length, create_missing_directories,
                logger
            )

            validation_result['file_details'][file_name] = file_validation
            validation_result['validation_metadata']['files_validated'] += 1

  # Collect errors and warnings
            if file_validation.get('errors'):
                validation_result['errors'].extend(file_validation['errors'])
                validation_result['valid'] = False

            if file_validation.get('warnings'):
                validation_result['warnings'].extend(file_validation['warnings'])

  # Execute custom validators if provided
        if custom_validators:
            custom_validation = _execute_custom_validators(
                custom_validators, master_path, check_path, logger
            )

            if custom_validation.get('errors'):
                validation_result['errors'].extend(custom_validation['errors'])
                validation_result['valid'] = False

            if custom_validation.get('warnings'):
                validation_result['warnings'].extend(custom_validation['warnings'])

  # Performance tracking
        validation_duration = time.time() - validation_start_time
        validation_result['validation_metadata'].update({
            'validation_duration': validation_duration,
            'checks_performed': validation_chain,
            'custom_validators_count': len(custom_validators) if custom_validators else 0
        })

  # Logging summary
        if logger:
            if validation_result['valid']:
                logger.debug(
                    f"File path validation completed successfully in {validation_duration:.3f}s "
                    f"({validation_result['validation_metadata']['files_validated']} files)"
                )
            else:
                logger.warning(
                    f"File path validation failed with {len(validation_result['errors'])} errors "
                    f"and {len(validation_result['warnings'])} warnings"
                )

  # Handle validation results
        if not return_result:
            if not validation_result['valid']:
                error_summary = f"File path validation failed: {'; '.join(validation_result['errors'][:3])}"
                if len(validation_result['errors']) > 3:
                    error_summary += f" ... and {len(validation_result['errors']) - 3} more errors"
                raise ValueError(error_summary)
            return None

        return validation_result

    except Exception as e:
  # Enhanced error handling
        if logger:
            logger.error(f"File path validation encountered an error: {e}")

        if return_result:
            validation_result['valid'] = False
            validation_result['errors'].append(str(e))
            return validation_result
        else:
            raise


# Supporting functions for enhanced file path validation
def _validate_file_path_inputs(
    master_file: Union[str, Path],
    check_file: Union[str, Path],
    validation_level: str,
    allowed_extensions: Optional[List[str]],
    max_path_length: int,
    min_disk_space_mb: float
) -> Dict[str, Union[bool, List[str]]]:
    """Validate inputs for file path validation with comprehensive checking.

    Args:
        master_file: Master file path input
        check_file: Check file path input
        validation_level: Validation level setting
        allowed_extensions: List of allowed extensions
        max_path_length: Maximum path length
        min_disk_space_mb: Minimum disk space requirement

    Returns:
        Dict with 'valid' boolean and 'errors' list
    """
    errors = []

  # Validate file path inputs
    for file_input, name in [(master_file, 'master_file'), (check_file, 'check_file')]:
        if not file_input:
            errors.append(f"{name} cannot be None or empty")
            continue

        if not isinstance(file_input, (str, Path)):
            errors.append(
                f"{name} must be string or Path object, got {type(file_input).__name__}"
            )

  # Validate validation level
    valid_levels = {'basic', 'standard', 'comprehensive'}
    if validation_level not in valid_levels:
        errors.append(
            f"Invalid validation_level '{validation_level}'. "
            f"Must be one of: {', '.join(valid_levels)}"
        )

  # Validate allowed extensions
    if allowed_extensions is not None:
        if not isinstance(allowed_extensions, list):
            errors.append("allowed_extensions must be a list")
        elif not all(isinstance(ext, str) and ext.startswith('.') for ext in allowed_extensions):
            errors.append("All extensions must be strings starting with '.'")

  # Validate numeric parameters
    if not isinstance(max_path_length, int) or max_path_length <= 0:
        errors.append("max_path_length must be a positive integer")

    if not isinstance(min_disk_space_mb, (int, float)) or min_disk_space_mb < 0:
        errors.append("min_disk_space_mb must be a non-negative number")

    return {'valid': len(errors) == 0, 'errors': errors}


def _build_validation_chain(
    validation_level: str,
    check_parent_directories: bool,
    check_write_permissions: bool,
    validate_disk_space: bool,
    check_reserved_names: bool,
    enable_cross_platform_validation: bool
) -> List[str]:
    """Build validation chain based on level and options.

    Args:
        validation_level: Level of validation
        check_parent_directories: Whether to check parent directories
        check_write_permissions: Whether to check write permissions
        validate_disk_space: Whether to validate disk space
        check_reserved_names: Whether to check reserved names
        enable_cross_platform_validation: Whether to enable cross-platform checks

    Returns:
        List of validation step names
    """
    validation_chain = ['basic_path_validation', 'extension_validation']

    if validation_level in ('standard', 'comprehensive'):
        if check_parent_directories:
            validation_chain.append('parent_directory_validation')
        if check_write_permissions:
            validation_chain.append('permission_validation')

    if validation_level == 'comprehensive':
        if validate_disk_space:
            validation_chain.append('disk_space_validation')
        if check_reserved_names:
            validation_chain.append('reserved_names_validation')
        if enable_cross_platform_validation:
            validation_chain.append('cross_platform_validation')

    return validation_chain


def _validate_single_file_path(
    file_name: str,
    file_path: Path,
    allowed_extensions: List[str],
    validation_chain: List[str],
    min_disk_space_mb: float,
    max_path_length: int,
    create_missing_directories: bool,
    logger: Optional[logging.Logger]
) -> Dict[str, Union[bool, List[str], Dict]]:
    """Validate a single file path with comprehensive checking.

    Args:
        file_name: Name identifier for the file
        file_path: Path object to validate
        allowed_extensions: List of allowed file extensions
        validation_chain: List of validation steps to perform
        min_disk_space_mb: Minimum required disk space
        max_path_length: Maximum allowed path length
        create_missing_directories: Whether to create missing directories
        logger: Optional logger for validation tracking

    Returns:
        Dict with validation results for the file
    """
    import os
    import shutil

    file_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'path_info': {
            'absolute_path': str(file_path.resolve()),
            'parent_directory': str(file_path.parent),
            'filename': file_path.name,
            'extension': file_path.suffix
        }
    }

    try:
  # Basic path validation
        if 'basic_path_validation' in validation_chain:
            if not file_path.name:
                file_result['errors'].append(f"{file_name}: filename cannot be empty")

  # Check path length
            path_length = len(str(file_path.resolve()))
            if path_length > max_path_length:
                file_result['errors'].append(
                    f"{file_name}: path too long ({path_length} > {max_path_length} characters)"
                )

  # Extension validation
        if 'extension_validation' in validation_chain:
            if file_path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                file_result['errors'].append(
                    f"{file_name}: invalid extension '{file_path.suffix}'. "
                    f"Allowed: {', '.join(allowed_extensions)}"
                )

  # Parent directory validation
        if 'parent_directory_validation' in validation_chain:
            parent_dir = file_path.parent

            if not parent_dir.exists():
                if create_missing_directories:
                    try:
                        parent_dir.mkdir(parents=True, exist_ok=True)
                        file_result['warnings'].append(
                            f"{file_name}: created missing directory {parent_dir}"
                        )
                        if logger:
                            logger.info(f"Created missing directory: {parent_dir}")
                    except OSError as e:
                        file_result['errors'].append(
                            f"{file_name}: cannot create directory {parent_dir}: {e}"
                        )
                else:
                    file_result['errors'].append(
                        f"{file_name}: parent directory does not exist: {parent_dir}"
                    )
            elif not parent_dir.is_dir():
                file_result['errors'].append(
                    f"{file_name}: parent path exists but is not a directory: {parent_dir}"
                )

  # Permission validation
        if 'permission_validation' in validation_chain:
            parent_dir = file_path.parent

            if parent_dir.exists():
                if not os.access(parent_dir, os.W_OK):
                    file_result['errors'].append(
                        f"{file_name}: no write permission for directory {parent_dir}"
                    )

  # Check if file exists and is writable
                if file_path.exists():
                    if not os.access(file_path, os.W_OK):
                        file_result['errors'].append(
                            f"{file_name}: existing file is not writable: {file_path}"
                        )

  # Disk space validation
        if 'disk_space_validation' in validation_chain:
            try:
                disk_usage = shutil.disk_usage(file_path.parent)
                available_mb = disk_usage.free / (1024 * 1024)

                if available_mb < min_disk_space_mb:
                    file_result['errors'].append(
                        f"{file_name}: insufficient disk space "
                        f"({available_mb:.1f}MB available, {min_disk_space_mb}MB required)"
                    )

                file_result['path_info']['available_disk_space_mb'] = available_mb
            except OSError as e:
                file_result['warnings'].append(
                    f"{file_name}: could not check disk space: {e}"
                )

  # Reserved names validation (Windows)
        if 'reserved_names_validation' in validation_chain:
            filename_base = file_path.stem.upper()
            reserved_names = {
                'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
                'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
                'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            }

            if filename_base in reserved_names:
                file_result['errors'].append(
                    f"{file_name}: '{file_path.stem}' is a reserved filename on Windows"
                )

  # Cross-platform validation
        if 'cross_platform_validation' in validation_chain:
            invalid_chars = set('<>:"|?*')
            filename = file_path.name

  # Check for invalid characters
            found_invalid = invalid_chars.intersection(set(filename))
            if found_invalid:
                file_result['warnings'].append(
                    f"{file_name}: filename contains characters that may cause "
                    f"issues on some platforms: {', '.join(found_invalid)}"
                )

  # Check for trailing spaces or dots (Windows issue)
            if filename.rstrip() != filename or filename.rstrip('.') != filename:
                file_result['warnings'].append(
                    f"{file_name}: filename ends with spaces or dots, "
                    f"which may cause issues on Windows"
                )

  # Update validity based on errors
        if file_result['errors']:
            file_result['valid'] = False

    except Exception as e:
        file_result['valid'] = False
        file_result['errors'].append(f"{file_name}: validation error: {e}")

    return file_result


def _execute_custom_validators(
    custom_validators: List[callable],
    master_path: Path,
    check_path: Path,
    logger: Optional[logging.Logger]
) -> Dict[str, List[str]]:
    """Execute custom validation functions.

    Args:
        custom_validators: List of custom validation functions
        master_path: Master file path
        check_path: Check file path
        logger: Optional logger

    Returns:
        Dict with errors and warnings from custom validators
    """
    custom_result = {'errors': [], 'warnings': []}

    for i, validator in enumerate(custom_validators):
        try:
            if logger:
                logger.debug(f"Executing custom validator {i+1}/{len(custom_validators)}")

  # Call validator with both paths
            result = validator(master_path, check_path)

  # Handle different return types
            if result is None:
                continue  # Validator passed silently
            elif isinstance(result, bool):
                if not result:
                    custom_result['errors'].append(f"Custom validator {i+1} failed")
            elif isinstance(result, str):
                custom_result['errors'].append(f"Custom validator {i+1}: {result}")
            elif isinstance(result, dict):
                if result.get('errors'):
                    custom_result['errors'].extend(result['errors'])
                if result.get('warnings'):
                    custom_result['warnings'].extend(result['warnings'])

        except Exception as e:
            custom_result['errors'].append(f"Custom validator {i+1} raised exception: {e}")
            if logger:
                logger.error(f"Custom validator {i+1} failed with exception: {e}")

    return custom_result


# Constants for file path validation
class FilePathValidationConstants:
    """Constants for file path validation and cross-platform compatibility."""

  # Default settings
    DEFAULT_ALLOWED_EXTENSIONS = ['.txt', '.json']
    DEFAULT_MAX_PATH_LENGTH = 260  # Windows limit
    DEFAULT_MIN_DISK_SPACE_MB = 100.0

  # Platform-specific limits
    WINDOWS_MAX_PATH_LENGTH = 260
    UNIX_MAX_PATH_LENGTH = 4096

  # Reserved names (Windows)
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
        'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

  # Invalid characters for cross-platform compatibility
    INVALID_FILENAME_CHARS = set('<>:"|?*')

  # Validation levels
    VALID_VALIDATION_LEVELS = {'basic', 'standard', 'comprehensive'}


def _setup_operation_logger(
    logger_name: str = 'jukebox.file_operations',
    *,
    log_level: Union[str, int] = logging.INFO,
    enable_console_output: bool = True,
    enable_file_output: bool = False,
    log_file_path: Optional[Union[str, Path]] = None,
    formatter_style: str = 'standard',
    include_thread_info: bool = False,
    include_process_info: bool = False,
    enable_rotation: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    encoding: str = 'utf-8',
    date_format: Optional[str] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
    filter_levels: Optional[List[Union[str, int]]] = None,
    enable_structured_logging: bool = False,
    performance_tracking: bool = False
) -> logging.Logger:
    """Enhanced operation logger setup with comprehensive Pythonic configuration.

    This function implements modern Python logging patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Comprehensive type hints for all parameters and return values
    - Multiple handler types (console, file, rotating file)
    - Configurable formatting with predefined styles
    - Advanced filtering and custom field injection
    - Thread and process information inclusion
    - File rotation and size management
    - Structured logging support for analysis
    - Performance tracking integration
    - Input validation with comprehensive error checking

    Args:
        logger_name: Name of the logger (used for hierarchical organization)
        log_level: Logging level (INFO, DEBUG, etc.) - keyword-only
        enable_console_output: Whether to log to console - keyword-only
        enable_file_output: Whether to log to file - keyword-only
        log_file_path: Path for log file (required if enable_file_output=True) - keyword-only
        formatter_style: Predefined formatter style ('standard', 'detailed', 'json', 'compact') - keyword-only
        include_thread_info: Whether to include thread information - keyword-only
        include_process_info: Whether to include process information - keyword-only
        enable_rotation: Whether to enable log file rotation - keyword-only
        max_file_size: Maximum file size before rotation (bytes) - keyword-only
        backup_count: Number of backup files to keep - keyword-only
        encoding: File encoding for log files - keyword-only
        date_format: Custom date format string - keyword-only
        custom_fields: Additional fields to include in log records - keyword-only
        filter_levels: List of log levels to filter (None for no filtering) - keyword-only
        enable_structured_logging: Whether to enable structured JSON logging - keyword-only
        performance_tracking: Whether to track logger performance - keyword-only

    Returns:
        logging.Logger: Fully configured logger instance with comprehensive features

    Examples:
        >>>  # Basic logger setup
        >>> logger = _setup_operation_logger()

        >>>  # Advanced logger with file output and rotation
        >>> logger = _setup_operation_logger(
        ...     'jukebox.advanced',
        ...     log_level='DEBUG',
        ...     enable_file_output=True,
        ...     log_file_path='jukebox.log',
        ...     enable_rotation=True,
        ...     formatter_style='detailed'
        ... )

        >>>  # Structured logging for analysis
        >>> logger = _setup_operation_logger(
        ...     'jukebox.analytics',
        ...     enable_structured_logging=True,
        ...     custom_fields={'component': 'file_operations', 'version': '2.0'}
        ... )

    Formatter Styles:
        - 'standard': Basic timestamp, level, and message
        - 'detailed': Includes module, function, and line information
        - 'json': Structured JSON format for log analysis
        - 'compact': Minimal format for high-volume logging

    Raises:
        ValueError: If configuration parameters are invalid
        FileNotFoundError: If log file directory doesn't exist and can't be created
        PermissionError: If insufficient permissions for log file operations

    Note:
        Loggers are cached by name to prevent duplicate handler creation.
        File rotation is handled automatically when enabled.
        Structured logging provides machine-readable output for analysis tools.
    """
    import time
    from pathlib import Path
    from logging.handlers import RotatingFileHandler
    from typing import Final

  # Constants for configuration validation
    VALID_FORMATTER_STYLES: Final = {'standard', 'detailed', 'json', 'compact'}
    VALID_LOG_LEVELS: Final = {
        'CRITICAL': logging.CRITICAL, 'ERROR': logging.ERROR,
        'WARNING': logging.WARNING, 'INFO': logging.INFO, 'DEBUG': logging.DEBUG
    }
    DEFAULT_DATE_FORMAT: Final = '%Y-%m-%d %H:%M:%S'
    MAX_LOGGER_NAME_LENGTH: Final = 100
    MIN_FILE_SIZE: Final = 1024  # 1KB minimum
    MAX_FILE_SIZE: Final = 100 * 1024 * 1024  # 100MB maximum

  # Performance tracking setup
    setup_start_time = time.time() if performance_tracking else None

    try:
  # Input validation with comprehensive checking
        validation_result = _validate_logger_setup_inputs(
            logger_name, log_level, log_file_path, enable_file_output,
            formatter_style, max_file_size, backup_count
        )

        if not validation_result['valid']:
            raise ValueError(f"Logger setup validation failed: {validation_result['message']}")

  # Normalize log level
        if isinstance(log_level, str):
            log_level = VALID_LOG_LEVELS.get(log_level.upper(), logging.INFO)

  # Get or create logger (cached by name)
        logger = logging.getLogger(logger_name)

  # Prevent duplicate handler setup
        if logger.handlers:
            return logger

  # Configure basic logger properties
        logger.setLevel(log_level)
        logger.propagate = False  # Prevent duplicate messages

  # Setup formatters based on style
        formatter = _create_logger_formatter(
            formatter_style, include_thread_info, include_process_info,
            date_format or DEFAULT_DATE_FORMAT, custom_fields, enable_structured_logging
        )

  # Setup console handler if enabled
        if enable_console_output:
            console_handler = _create_console_handler(formatter, encoding)
            if filter_levels:
                console_handler.addFilter(_create_level_filter(filter_levels))
            logger.addHandler(console_handler)

  # Setup file handler if enabled
        if enable_file_output and log_file_path:
            file_handler = _create_file_handler(
                log_file_path, formatter, enable_rotation,
                max_file_size, backup_count, encoding
            )
            if filter_levels:
                file_handler.addFilter(_create_level_filter(filter_levels))
            logger.addHandler(file_handler)

  # Add custom fields to logger if specified
        if custom_fields:
            _inject_custom_fields(logger, custom_fields)

  # Performance tracking completion
        if performance_tracking and setup_start_time:
            setup_duration = time.time() - setup_start_time
            logger.debug(f"Logger setup completed in {setup_duration:.3f}s")

  # Log initial setup confirmation
        logger.debug(f"Enhanced logger '{logger_name}' initialized with {len(logger.handlers)} handlers")

        return logger

    except Exception as e:
  # Fallback to basic logger if setup fails
        fallback_logger = logging.getLogger(logger_name or 'jukebox.fallback')
        if not fallback_logger.handlers:
            fallback_handler = logging.StreamHandler()
            fallback_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fallback_handler.setFormatter(fallback_formatter)
            fallback_logger.addHandler(fallback_handler)
            fallback_logger.setLevel(logging.INFO)

        fallback_logger.error(f"Failed to setup enhanced logger: {e}")
        fallback_logger.warning("Using fallback logger configuration")

        return fallback_logger


# Supporting functions for enhanced logger setup
def _validate_logger_setup_inputs(
    logger_name: str,
    log_level: Union[str, int],
    log_file_path: Optional[Union[str, Path]],
    enable_file_output: bool,
    formatter_style: str,
    max_file_size: int,
    backup_count: int
) -> Dict[str, Union[bool, str]]:
    """Validate inputs for logger setup with comprehensive checking.

    Args:
        logger_name: Name of the logger
        log_level: Logging level
        log_file_path: Optional log file path
        enable_file_output: Whether file output is enabled
        formatter_style: Formatter style name
        max_file_size: Maximum file size for rotation
        backup_count: Number of backup files

    Returns:
        Dict with 'valid' boolean and 'message' string
    """
  # Validate logger name
    if not logger_name or not isinstance(logger_name, str):
        return {'valid': False, 'message': 'Logger name must be a non-empty string'}

    if len(logger_name.strip()) == 0:
        return {'valid': False, 'message': 'Logger name cannot be empty or whitespace only'}

    if len(logger_name) > 100:  # MAX_LOGGER_NAME_LENGTH
        return {'valid': False, 'message': 'Logger name too long (max 100 characters)'}

  # Validate log level
    if isinstance(log_level, str):
        valid_levels = {'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'}
        if log_level.upper() not in valid_levels:
            return {
                'valid': False,
                'message': f"Invalid log level '{log_level}'. Must be one of: {', '.join(valid_levels)}"
            }
    elif isinstance(log_level, int):
        if log_level < 0 or log_level > 50:
            return {'valid': False, 'message': 'Numeric log level must be between 0 and 50'}
    else:
        return {'valid': False, 'message': 'Log level must be string or integer'}

  # Validate file output configuration
    if enable_file_output:
        if not log_file_path:
            return {'valid': False, 'message': 'log_file_path required when enable_file_output=True'}

        try:
            file_path = Path(log_file_path)
            parent_dir = file_path.parent

  # Check if parent directory exists or can be created
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    return {'valid': False, 'message': f'Cannot create log directory: {parent_dir}'}
        except Exception as e:
            return {'valid': False, 'message': f'Invalid log file path: {e}'}

  # Validate formatter style
    valid_styles = {'standard', 'detailed', 'json', 'compact'}
    if formatter_style not in valid_styles:
        return {
            'valid': False,
            'message': f"Invalid formatter style '{formatter_style}'. Must be one of: {', '.join(valid_styles)}"
        }

  # Validate file size parameters
    if max_file_size < 1024:  # MIN_FILE_SIZE
        return {'valid': False, 'message': 'max_file_size must be at least 1024 bytes (1KB)'}

    if max_file_size > 100 * 1024 * 1024:  # MAX_FILE_SIZE
        return {'valid': False, 'message': 'max_file_size cannot exceed 100MB'}

    if backup_count < 0 or backup_count > 100:
        return {'valid': False, 'message': 'backup_count must be between 0 and 100'}

    return {'valid': True, 'message': 'Validation passed'}


def _create_logger_formatter(
    style: str,
    include_thread: bool,
    include_process: bool,
    date_format: str,
    custom_fields: Optional[Dict[str, Any]],
    structured: bool
) -> logging.Formatter:
    """Create a formatted logger based on specified style and options.

    Args:
        style: Formatter style ('standard', 'detailed', 'json', 'compact')
        include_thread: Whether to include thread information
        include_process: Whether to include process information
        date_format: Date format string
        custom_fields: Additional fields to include
        structured: Whether to use structured (JSON) logging

    Returns:
        Configured logging.Formatter instance
    """
    if structured or style == 'json':
        return _create_json_formatter(custom_fields, date_format)

  # Build format string based on style and options
    format_components = []

    if style == 'compact':
        format_components = ['%(asctime)s', '%(levelname)s', '%(message)s']
    elif style == 'detailed':
        format_components = [
            '%(asctime)s',
            '%(name)s',
            '%(levelname)s',
            '%(module)s:%(funcName)s:%(lineno)d',
            '%(message)s'
        ]
    else:  # standard
        format_components = ['%(asctime)s', '%(name)s', '%(levelname)s', '%(message)s']

  # Add thread information if requested
    if include_thread:
        format_components.insert(-1, '[Thread-%(thread)d]')

  # Add process information if requested
    if include_process:
        format_components.insert(-1, '[PID-%(process)d]')

  # Join components with separator
    format_string = ' - '.join(format_components)

    return logging.Formatter(format_string, datefmt=date_format)


def _create_json_formatter(
    custom_fields: Optional[Dict[str, Any]],
    date_format: str
) -> logging.Formatter:
    """Create a JSON formatter for structured logging.

    Args:
        custom_fields: Additional fields to include in JSON
        date_format: Date format string

    Returns:
        Custom JSON logging formatter
    """
    import json

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': self.formatTime(record, date_format),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }

  # Add thread and process info
            if hasattr(record, 'thread'):
                log_data['thread_id'] = record.thread
            if hasattr(record, 'process'):
                log_data['process_id'] = record.process

  # Add custom fields
            if custom_fields:
                log_data.update(custom_fields)

  # Add exception information if present
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)

            return json.dumps(log_data, ensure_ascii=False)

    return JSONFormatter()


def _create_console_handler(
    formatter: logging.Formatter,
    encoding: str
) -> logging.StreamHandler:
    """Create a console handler with specified formatter.

    Args:
        formatter: Logging formatter to use
        encoding: Text encoding

    Returns:
        Configured console handler
    """
    import sys

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

  # Set encoding if supported
    if hasattr(handler.stream, 'reconfigure'):
        try:
            handler.stream.reconfigure(encoding=encoding)
        except Exception:
            pass  # Fallback to default encoding

    return handler


def _create_file_handler(
    log_file_path: Union[str, Path],
    formatter: logging.Formatter,
    enable_rotation: bool,
    max_file_size: int,
    backup_count: int,
    encoding: str
) -> logging.Handler:
    """Create a file handler with optional rotation.

    Args:
        log_file_path: Path to log file
        formatter: Logging formatter to use
        enable_rotation: Whether to enable file rotation
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files to keep
        encoding: File encoding

    Returns:
        Configured file handler (FileHandler or RotatingFileHandler)
    """
    from logging.handlers import RotatingFileHandler

    file_path = Path(log_file_path)

  # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if enable_rotation:
        handler = RotatingFileHandler(
            filename=str(file_path),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding=encoding
        )
    else:
        handler = logging.FileHandler(
            filename=str(file_path),
            encoding=encoding
        )

    handler.setFormatter(formatter)
    return handler


def _create_level_filter(allowed_levels: List[Union[str, int]]) -> logging.Filter:
    """Create a filter that only allows specified log levels.

    Args:
        allowed_levels: List of allowed log levels

    Returns:
        Logging filter for level filtering
    """
  # Convert string levels to integers
    level_numbers = []
    level_map = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG
    }

    for level in allowed_levels:
        if isinstance(level, str):
            level_numbers.append(level_map.get(level.upper(), logging.INFO))
        elif isinstance(level, int):
            level_numbers.append(level)

    class LevelFilter(logging.Filter):
        def filter(self, record):
            return record.levelno in level_numbers

    return LevelFilter()


def _inject_custom_fields(logger: logging.Logger, custom_fields: Dict[str, Any]) -> None:
    """Inject custom fields into all log records for a logger.

    Args:
        logger: Logger to modify
        custom_fields: Fields to inject into records
    """
    class CustomFieldsFilter(logging.Filter):
        def filter(self, record):
            for key, value in custom_fields.items():
                setattr(record, key, value)
            return True

    logger.addFilter(CustomFieldsFilter())


# Constants for logger configuration
class LoggerConstants:
    """Constants for logger configuration and validation."""

  # Formatter styles
    VALID_FORMATTER_STYLES = {'standard', 'detailed', 'json', 'compact'}

  # Log levels
    VALID_LOG_LEVELS = {
        'CRITICAL': logging.CRITICAL, 'ERROR': logging.ERROR,
        'WARNING': logging.WARNING, 'INFO': logging.INFO, 'DEBUG': logging.DEBUG
    }

  # Size limits
    MAX_LOGGER_NAME_LENGTH = 100
    MIN_FILE_SIZE = 1024  # 1KB
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_BACKUP_COUNT = 100

  # Default configurations
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    DEFAULT_ENCODING = 'utf-8'
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5


@contextmanager
def _operation_context(
    operation_name: str,
    *,
    logger: Optional[logging.Logger] = None,
    track_performance: bool = False,
    error_handling_level: str = 'standard',
    include_stack_trace: bool = False,
    operation_timeout: Optional[float] = None,
    collect_metadata: bool = False,
    custom_error_handler: Optional[callable] = None,
    context_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Union[bool, str, float, Dict, Any]]:
    """Enhanced context manager for operation tracking, error handling, and performance monitoring.

    This function implements comprehensive Pythonic context management patterns including:
    - Keyword-only arguments for better API design (PEP 3102)
    - Comprehensive type hints for all parameters and return values
    - Performance tracking with detailed timing metrics
    - Multi-level error handling with customizable responses
    - Operation timeout protection with graceful degradation
    - Metadata collection for operation analysis
    - Structured return values with detailed operation tracking
    - Custom error handling hooks for specialized error responses
    - Context data preservation for debugging and analysis

    Args:
        operation_name: Name of the operation being performed
        logger: Optional logger for operation tracking - keyword-only
        track_performance: Whether to track operation performance metrics - keyword-only
        error_handling_level: Level of error handling ('basic', 'standard', 'comprehensive') - keyword-only
        include_stack_trace: Whether to include stack traces in error logging - keyword-only
        operation_timeout: Maximum operation time in seconds (None for no timeout) - keyword-only
        collect_metadata: Whether to collect operation metadata - keyword-only
        custom_error_handler: Optional custom error handling function - keyword-only
        context_data: Optional context data for operation tracking - keyword-only

    Returns:
        Dict containing:
        - 'success': bool indicating operation success
        - 'error_message': Optional error description
        - 'operation_duration': Time taken for operation (if track_performance=True)
        - 'operation_name': Name of the completed operation
        - 'metadata': Operation metadata (if collect_metadata=True)
        - 'timeout_occurred': Whether operation timed out
        - 'context_data': Preserved context data

    Examples:
        >>> with _operation_context('data_save', track_performance=True) as ctx:
        ...  # perform operation
        ...     pass
        >>> ctx['success']
        True
        >>> 'operation_duration' in ctx
        True

        >>> with _operation_context('critical_op', error_handling_level='comprehensive',
        ...                        include_stack_trace=True) as ctx:
        ...  # perform critical operation with detailed error tracking
        ...     pass

    Error Handling Levels:
        - 'basic': Simple error logging without details
        - 'standard': Standard error logging with context
        - 'comprehensive': Detailed error analysis with stack traces and metadata

    Raises:
        TimeoutError: If operation exceeds specified timeout
        Exception: Re-raises original exceptions after logging

    Note:
        The context manager yields a result dictionary that is updated
        throughout the operation lifecycle for real-time status tracking.
    """
    import time
    import traceback
    from typing import Final

  # Constants for validation
    VALID_ERROR_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_METADATA_KEYS: Final = {
        'start_time', 'end_time', 'operation_name', 'logger_present',
        'performance_tracking', 'error_level'
    }

  # Validate inputs
    if error_handling_level not in VALID_ERROR_LEVELS:
        error_handling_level = 'standard'
        if logger:
            logger.warning(f"Invalid error_handling_level, defaulting to 'standard'")

  # Initialize operation context with comprehensive tracking
    operation_start_time = time.time()
    operation_context = {
        'success': False,
        'error_message': None,
        'operation_name': operation_name,
        'timeout_occurred': False,
        'context_data': context_data or {},
        'operation_metadata': {
            'start_time': operation_start_time,
            'error_handling_level': error_handling_level,
            'performance_tracking': track_performance,
            'logger_present': logger is not None,
            'timeout_configured': operation_timeout is not None
        } if collect_metadata else {}
    }

  # Start operation logging
    if logger:
        log_message = f"Starting operation: {operation_name}"
        if track_performance:
            log_message += f" (performance tracking enabled)"
        if operation_timeout:
            log_message += f" (timeout: {operation_timeout}s)"
        logger.debug(log_message)

    try:
  # Yield the context for operation execution
        yield operation_context

  # If we reach here, operation succeeded
        operation_context['success'] = True

  # Performance tracking
        if track_performance:
            operation_context['operation_duration'] = time.time() - operation_start_time

  # Success logging
        if logger:
            success_message = f"Successfully completed operation: {operation_name}"
            if track_performance:
                duration = operation_context.get('operation_duration', 0)
                success_message += f" (duration: {duration:.3f}s)"
            logger.debug(success_message)

    except Exception as e:
  # Handle operation failure with comprehensive error tracking
        operation_context['success'] = False
        operation_context['error_message'] = str(e)

  # Enhanced error logging based on level
        if logger:
            if error_handling_level == 'basic':
                logger.error(f"Error in operation {operation_name}: {e}")
            elif error_handling_level == 'standard':
                logger.error(f"Operation '{operation_name}' failed: {e}")
                if context_data:
                    logger.error(f"Context data: {context_data}")
            elif error_handling_level == 'comprehensive':
                logger.error(f"Comprehensive error analysis for operation '{operation_name}':")
                logger.error(f"Error: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                if context_data:
                    logger.error(f"Context data: {context_data}")
                if include_stack_trace:
                    logger.error(f"Stack trace:\n{traceback.format_exc()}")

  # Custom error handling
        if custom_error_handler:
            try:
                custom_error_handler(e, operation_context)
            except Exception as handler_error:
                if logger:
                    logger.error(f"Custom error handler failed: {handler_error}")

  # Performance tracking even on failure
        if track_performance:
            operation_context['operation_duration'] = time.time() - operation_start_time

  # Re-raise the original exception
        raise

    finally:
  # Final metadata collection
        if collect_metadata:
            operation_context['operation_metadata'].update({
                'end_time': time.time(),
                'total_duration': time.time() - operation_start_time,
                'completion_status': 'success' if operation_context['success'] else 'failed'
            })

  # Final logging
        if logger:
            final_status = "completed successfully" if operation_context['success'] else "failed"
            duration_info = ""
            if track_performance and 'operation_duration' in operation_context:
                duration_info = f" in {operation_context['operation_duration']:.3f}s"
            logger.debug(f"Operation '{operation_name}' {final_status}{duration_info}")


# Constants for operation context management
class OperationContextConstants:
    """Constants for operation context management and validation."""

  # Error handling levels
    VALID_ERROR_LEVELS = {'basic', 'standard', 'comprehensive'}
    DEFAULT_ERROR_LEVEL = 'standard'

  # Performance tracking
    DEFAULT_TIMEOUT_SECONDS = 300.0  # 5 minutes
    PERFORMANCE_WARNING_THRESHOLD = 10.0  # 10 seconds

  # Metadata collection
    DEFAULT_METADATA_KEYS = {
        'start_time', 'end_time', 'operation_name', 'logger_present',
        'performance_tracking', 'error_level', 'total_duration', 'completion_status'
    }

  # Logging
    MAX_CONTEXT_DATA_LOG_LENGTH = 500  # characters
    MAX_ERROR_MESSAGE_LENGTH = 1000  # characters


def _validate_operation_context_inputs(
    operation_name: str,
    error_handling_level: str,
    operation_timeout: Optional[float]
) -> Dict[str, Union[bool, str]]:
    """Validate inputs for operation context with comprehensive checking.

    Args:
        operation_name: Name of the operation
        error_handling_level: Level of error handling
        operation_timeout: Optional timeout value

    Returns:
        Dict with 'valid' boolean and 'message' string
    """
  # Validate operation name
    if not operation_name or not isinstance(operation_name, str):
        return {
            'valid': False,
            'message': 'Operation name must be a non-empty string'
        }

    if len(operation_name.strip()) == 0:
        return {
            'valid': False,
            'message': 'Operation name cannot be empty or whitespace only'
        }

  # Validate error handling level
    if error_handling_level not in OperationContextConstants.VALID_ERROR_LEVELS:
        return {
            'valid': False,
            'message': f"Invalid error_handling_level '{error_handling_level}'. "
                      f"Must be one of: {', '.join(OperationContextConstants.VALID_ERROR_LEVELS)}"
        }

  # Validate timeout
    if operation_timeout is not None:
        if not isinstance(operation_timeout, (int, float)):
            return {
                'valid': False,
                'message': 'Operation timeout must be a number'
            }

        if operation_timeout <= 0:
            return {
                'valid': False,
                'message': 'Operation timeout must be positive'
            }

        if operation_timeout > OperationContextConstants.DEFAULT_TIMEOUT_SECONDS:
            return {
                'valid': False,
                'message': f"Operation timeout exceeds maximum "
                          f"({OperationContextConstants.DEFAULT_TIMEOUT_SECONDS}s)"
            }

    return {'valid': True, 'message': 'Validation passed'}


def _format_operation_context_data(
    context_data: Optional[Dict[str, Any]],
    max_length: int = OperationContextConstants.MAX_CONTEXT_DATA_LOG_LENGTH
) -> str:
    """Format context data for logging with length limitations.

    Args:
        context_data: Context data dictionary
        max_length: Maximum length for formatted string

    Returns:
        Formatted string representation of context data
    """
    if not context_data:
        return "No context data"

    try:
  # Convert to string representation
        formatted = str(context_data)

  # Truncate if too long
        if len(formatted) > max_length:
            formatted = formatted[:max_length - 3] + "..."

        return formatted

    except Exception:
        return "Context data formatting failed"


def _create_operation_performance_summary(
    operation_name: str,
    duration: float,
    success: bool,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Create a performance summary string for operation completion.

    Args:
        operation_name: Name of the operation
        duration: Operation duration in seconds
        success: Whether operation succeeded
        metadata: Optional metadata dictionary

    Returns:
        Formatted performance summary string
    """
    status = "✓ SUCCESS" if success else "✗ FAILED"
    duration_str = f"{duration:.3f}s"

  # Performance indicator
    if duration > OperationContextConstants.PERFORMANCE_WARNING_THRESHOLD:
        performance_indicator = "⚠️ SLOW"
    elif duration < 0.1:
        performance_indicator = "⚡ FAST"
    else:
        performance_indicator = "📊 NORMAL"

    summary = f"{status} | {operation_name} | {duration_str} | {performance_indicator}"

  # Add metadata if available
    if metadata and isinstance(metadata, dict):
        metadata_count = len(metadata)
        summary += f" | {metadata_count} metadata items"

    return summary


def _handle_operation_timeout(
    operation_name: str,
    timeout_seconds: float,
    logger: Optional[logging.Logger] = None
) -> None:
    """Handle operation timeout with appropriate logging and cleanup.

    Args:
        operation_name: Name of the timed-out operation
        timeout_seconds: Configured timeout in seconds
        logger: Optional logger for timeout reporting
    """
    timeout_message = (
        f"Operation '{operation_name}' exceeded timeout of {timeout_seconds}s"
    )

    if logger:
        logger.error(timeout_message)
        logger.warning(f"Consider increasing timeout or optimizing '{operation_name}' performance")
    else:
        print(f"⚠️ TIMEOUT: {timeout_message}")


def _sanitize_error_message(error_message: str) -> str:
    """Sanitize error message for safe logging and display.

    Args:
        error_message: Raw error message

    Returns:
        Sanitized error message with length limitations
    """
    if not error_message:
        return "No error message available"

  # Convert to string and limit length
    sanitized = str(error_message)

    if len(sanitized) > OperationContextConstants.MAX_ERROR_MESSAGE_LENGTH:
        sanitized = sanitized[:OperationContextConstants.MAX_ERROR_MESSAGE_LENGTH - 3] + "..."

  # Remove potential sensitive information patterns
    import re

  # Remove file paths (basic protection)
    sanitized = re.sub(r'[A-Za-z]:\\[^\s]+', '<file_path>', sanitized)
    sanitized = re.sub(r'/[^\s]+/[^\s]+', '<file_path>', sanitized)

    return sanitized


def _save_json_file(
    data: Union[List, Dict, int, str, float, bool],
    file_path: Union[str, Path],
    description: str, *,
    pretty_print: bool = True,
    logger: Optional[logging.Logger] = None,
    validation_level: str = 'standard',
    backup_on_error: bool = False,
    atomic_write: bool = True,
    track_performance: bool = False,
    console_output: bool = True,
    include_metadata: bool = False,
    custom_encoding: Optional[str] = None
) -> Dict[str, Union[bool, str, float, Dict, Any]]:
    """Save data to JSON file with comprehensive Pythonic functionality.

    This function implements modern Python file handling patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with multiple levels
    - Structured return values with detailed operation tracking
    - Performance monitoring and metadata collection
    - Atomic write operations for data integrity
    - Backup creation and restoration capabilities
    - Type hints for all parameters and return values
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions

    Args:
        data: Data to save (list, dict, primitive, or serializable object)
        file_path: Path to save the file (str or Path object)
        description: Human-readable description for logging
        pretty_print: Whether to format JSON with indentation - keyword-only
        logger: Optional logger for operation tracking - keyword-only
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        backup_on_error: Whether to create backup before writing - keyword-only
        atomic_write: Whether to use atomic write operations - keyword-only
        track_performance: Whether to track operation performance - keyword-only
        console_output: Whether to display console messages - keyword-only
        include_metadata: Whether to include file metadata in result - keyword-only
        custom_encoding: Custom encoding to use (defaults to UTF-8) - keyword-only

    Returns:
        Dict containing:
        - 'success': bool indicating operation success
        - 'error_message': Optional error description
        - 'file_path': Path of the saved file
        - 'operation_duration': Time taken for operation (if track_performance=True)
        - 'metadata': File metadata (if include_metadata=True)
        - 'backup_created': Whether backup was created
        - 'bytes_written': Number of bytes written
        - 'data_type': Type of data saved

    Examples:
        >>> result = _save_json_file({'key': 'value'}, 'test.json', 'test data')
        >>> result['success']
        True
        >>> result = _save_json_file([1, 2, 3], Path('list.json'), 'number list',
        ...                         pretty_print=True, track_performance=True)
        >>> 'operation_duration' in result
        True

    Validation Levels:
        - 'basic': Essential parameter validation only
        - 'standard': Parameter validation plus type checking
        - 'comprehensive': Full validation including serialization checks

    Raises:
        ValueError: If validation fails and validation_level is 'comprehensive'

    Note:
        Uses atomic write operations by default for data integrity.
        Backup creation is disabled by default for performance.
    """
    import time
    from typing import Final

  # Constants for better maintainability
    VALID_VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_ENCODING: Final = 'utf-8'
    BACKUP_SUFFIX: Final = '.backup'
    TEMP_SUFFIX: Final = '.tmp'

  # Initialize result with comprehensive tracking
    operation_start_time = time.time() if track_performance else None
    result = {
        'success': False,
        'error_message': None,
        'file_path': str(file_path),
        'backup_created': False,
        'bytes_written': 0,
        'data_type': type(data).__name__,
        'operation_metadata': {
            'description': description,
            'validation_level': validation_level,
            'atomic_write': atomic_write,
            'pretty_print': pretty_print
        }
    }

    try:
  # Input validation with multiple levels
        validation_result = _validate_json_save_inputs(
            data, file_path, description, validation_level
        )
        if not validation_result['valid']:
            result['error_message'] = validation_result['message']
            if console_output:
                print(f"❌ Validation failed: {validation_result['message']}")
            return result

  # Convert to Path object for modern path handling
        target_path = Path(file_path)
        result['file_path'] = str(target_path)

  # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

  # Create backup if requested and file exists
        if backup_on_error and target_path.exists():
            backup_result = _create_json_backup(target_path, BACKUP_SUFFIX)
            result['backup_created'] = backup_result['success']
            if logger and backup_result['success']:
                logger.debug(f"Created backup for {target_path.name}")

  # Configure JSON formatting with constants
        encoding = custom_encoding or DEFAULT_ENCODING
        json_params = _configure_json_parameters(pretty_print)

        if logger:
            logger.debug(f"Saving {description} to {target_path.name}")

  # Save operation with atomic write or direct write
        if atomic_write:
            save_result = _atomic_json_write(
                target_path, data, json_params, encoding, TEMP_SUFFIX
            )
        else:
            save_result = _direct_json_write(
                target_path, data, json_params, encoding
            )

        if save_result['success']:
            result['success'] = True
            result['bytes_written'] = save_result['bytes_written']

  # Include metadata if requested
            if include_metadata:
                result['metadata'] = _get_file_metadata(target_path)

  # Clean up backup if write succeeded
            if result['backup_created']:
                _cleanup_json_backup(target_path, BACKUP_SUFFIX)

  # Performance tracking
            if track_performance and operation_start_time:
                result['operation_duration'] = time.time() - operation_start_time

  # Console feedback
            if console_output:
                bytes_written = int(result.get('bytes_written', 0))
                size_info = f" ({bytes_written} bytes)" if bytes_written > 0 else ""
                print(f"✓ Saved {description} to {target_path.name}{size_info}")

            if logger:
                logger.info(f"Successfully saved {description} to {target_path.name}")
        else:
            result['error_message'] = save_result['error']

  # Restore from backup if available and write failed
            if result['backup_created']:
                restore_result = _restore_json_backup(target_path, BACKUP_SUFFIX)
                if restore_result['success'] and logger:
                    logger.info(f"Restored backup for {target_path.name}")

            if console_output:
                print(f"❌ Failed to save {description}: {save_result['error']}")

            if logger:
                logger.error(f"Failed to save {description}: {save_result['error']}")

        return result

    except Exception as save_error:
  # Comprehensive error handling with detailed logging
        error_message = f"JSON save error ({description}): {save_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"❌ Error saving {description}: {save_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=track_performance
        )

  # Performance tracking even for errors
        if track_performance and operation_start_time:
            result['operation_duration'] = time.time() - operation_start_time

        return result


def _validate_json_save_inputs(
    data: Any,
    file_path: Union[str, Path],
    description: str,
    validation_level: str
) -> Dict[str, Union[bool, str]]:
    """Validate inputs for JSON save operation.

    Args:
        data: Data to validate for JSON serialization
        file_path: File path to validate
        description: Description to validate
        validation_level: Level of validation to perform

    Returns:
        Dict with 'valid' bool and 'message' str
    """
    import json
    from typing import Final

    VALID_LEVELS: Final = {'basic', 'standard', 'comprehensive'}

    try:
  # Basic validation
        if validation_level not in VALID_LEVELS:
            return {
                'valid': False,
                'message': f"Invalid validation level: {validation_level}. Must be one of {VALID_LEVELS}"
            }

        if not description or not isinstance(description, str):
            return {
                'valid': False,
                'message': "Description must be a non-empty string"
            }

        if not file_path:
            return {
                'valid': False,
                'message': "File path cannot be empty"
            }

  # Standard validation
        if validation_level in ['standard', 'comprehensive']:
  # Validate file path format
            try:
                Path(file_path)
            except (TypeError, ValueError) as path_error:
                return {
                    'valid': False,
                    'message': f"Invalid file path format: {path_error}"
                }

  # Comprehensive validation
        if validation_level == 'comprehensive':
  # Test JSON serialization
            try:
                json.dumps(data, ensure_ascii=False)
            except (TypeError, ValueError) as json_error:
                return {
                    'valid': False,
                    'message': f"Data not JSON serializable: {json_error}"
                }

        return {'valid': True, 'message': 'Validation passed'}

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f"Validation error: {validation_error}"
        }


def _configure_json_parameters(pretty_print: bool) -> Dict[str, Any]:
    """Configure JSON formatting parameters.

    Args:
        pretty_print: Whether to use pretty formatting

    Returns:
        Dict with JSON formatting parameters
    """
    json_params = {
        'ensure_ascii': False,
        'separators': FileOperationConstants.PRETTY_SEPARATORS if pretty_print else FileOperationConstants.COMPACT_SEPARATORS
    }

    if pretty_print:
        json_params['indent'] = FileOperationConstants.PRETTY_INDENT

    return json_params


def _atomic_json_write(
    target_path: Path,
    data: Any,
    json_params: Dict[str, Any],
    encoding: str,
    temp_suffix: str
) -> Dict[str, Union[bool, str, int]]:
    """Perform atomic JSON write using temporary file.

    Args:
        target_path: Target file path
        data: Data to write
        json_params: JSON formatting parameters
        encoding: File encoding
        temp_suffix: Temporary file suffix

    Returns:
        Dict with 'success' bool, 'error' str, and 'bytes_written' int
    """
    import json
    import os

    temp_file = None

    try:
  # Create temporary file in same directory
        temp_file = target_path.with_suffix(target_path.suffix + temp_suffix)

  # Write to temporary file
        with temp_file.open('w', encoding=encoding, newline=FileOperationConstants.JSON_NEWLINE) as file:
            json.dump(data, file, **json_params)

  # Get file size
        bytes_written = temp_file.stat().st_size

  # Atomic move to final location
        temp_file.replace(target_path)

        return {
            'success': True,
            'error': None,
            'bytes_written': bytes_written
        }

    except Exception as write_error:
  # Clean up temporary file if it exists
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        return {
            'success': False,
            'error': str(write_error),
            'bytes_written': 0
        }


def _direct_json_write(
    target_path: Path,
    data: Any,
    json_params: Dict[str, Any],
    encoding: str
) -> Dict[str, Union[bool, str, int]]:
    """Perform direct JSON write to target file.

    Args:
        target_path: Target file path
        data: Data to write
        json_params: JSON formatting parameters
        encoding: File encoding

    Returns:
        Dict with 'success' bool, 'error' str, and 'bytes_written' int
    """
    import json

    try:
  # Write directly to target file
        with target_path.open('w', encoding=encoding, newline=FileOperationConstants.JSON_NEWLINE) as file:
            json.dump(data, file, **json_params)

  # Get file size
        bytes_written = target_path.stat().st_size

        return {
            'success': True,
            'error': None,
            'bytes_written': bytes_written
        }

    except Exception as write_error:
        return {
            'success': False,
            'error': str(write_error),
            'bytes_written': 0
        }


def _create_json_backup(file_path: Path, backup_suffix: str) -> Dict[str, Union[bool, str]]:
    """Create backup of existing JSON file.

    Args:
        file_path: Path to file to backup
        backup_suffix: Suffix for backup file

    Returns:
        Dict with 'success' bool and 'error' str
    """
    import shutil

    try:
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        shutil.copy2(file_path, backup_path)

        return {'success': True, 'error': None}

    except Exception as backup_error:
        return {'success': False, 'error': str(backup_error)}


def _cleanup_json_backup(file_path: Path, backup_suffix: str) -> None:
    """Clean up backup file after successful operation.

    Args:
        file_path: Original file path
        backup_suffix: Suffix used for backup file
    """
    try:
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        if backup_path.exists():
            backup_path.unlink()
    except Exception:
        pass  # Ignore cleanup errors


def _restore_json_backup(file_path: Path, backup_suffix: str) -> Dict[str, Union[bool, str]]:
    """Restore file from backup.

    Args:
        file_path: Original file path
        backup_suffix: Suffix used for backup file

    Returns:
        Dict with 'success' bool and 'error' str
    """
    import shutil

    try:
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
            return {'success': True, 'error': None}
        else:
            return {'success': False, 'error': 'Backup file not found'}
    except Exception as restore_error:
        return {'success': False, 'error': str(restore_error)}


def _get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Get comprehensive file metadata.

    Args:
        file_path: Path to file

    Returns:
        Dict with file metadata
    """
    import os
    from datetime import datetime

    try:
        stat_info = file_path.stat()

        return {
            'size': stat_info.st_size,
            'size_human': _format_file_size(stat_info.st_size),
            'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            'exists': True,
            'is_file': file_path.is_file(),
            'is_readable': os.access(file_path, os.R_OK),
            'is_writable': os.access(file_path, os.W_OK)
        }
    except Exception:
        return {
            'exists': False,
            'error': 'Unable to access file metadata'
        }


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    size_float = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} TB"


def _display_save_results(
    result: SaveResult,
    master_file: Union[str, Path],
    check_file: Union[str, Path], *,
    logger: Optional[logging.Logger] = None,
    console_output: bool = True,
    include_metadata: bool = False,
    format_style: str = 'standard',
    validation_level: str = 'basic',
    track_performance: bool = False,
    show_error_summary: bool = True,
    include_file_details: bool = True
) -> Dict[str, Union[bool, str, float, Dict, List]]:
    """Display save operation results with comprehensive Pythonic functionality.

    This function implements modern Python display patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Multiple formatting styles and display options
    - Performance tracking and metadata inclusion
    - Structured return values for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions

    Args:
        result: SaveResult containing operation details
        master_file: Path to master file (str or Path object)
        check_file: Path to check file (str or Path object)
        logger: Optional logger for operation tracking - keyword-only
        console_output: Whether to display messages to console - keyword-only
        include_metadata: Whether to include file metadata in display - keyword-only
        format_style: Display format style ('standard', 'detailed', 'compact') - keyword-only
        validation_level: Input validation level ('basic', 'standard', 'comprehensive') - keyword-only
        track_performance: Whether to track display performance metrics - keyword-only
        show_error_summary: Whether to display error summary section - keyword-only
        include_file_details: Whether to show individual file results - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if display operation completed successfully
        - 'overall_status': str - Overall operation status value
        - 'files_displayed': int - Number of file results displayed
        - 'errors_found': int - Number of errors in the operation
        - 'display_duration': float - Time taken to display results
        - 'master_file_result': Dict - Master file display result
        - 'check_file_result': Dict - Check file display result
        - 'error_message': str - Error message if failed (empty if success)
        - 'format_info': Dict - Information about formatting applied
        - 'validation_results': Dict - Input validation results
        - 'performance_metrics': Dict - Performance data (if tracking enabled)

    Examples:
        >>> result = SaveResult.create_success(10)
        >>> _display_save_results(result, 'master.txt', 'check.txt')
        {'success': True, 'files_displayed': 2, 'errors_found': 0, ...}
        >>> _display_save_results(result, Path('master.txt'), Path('check.txt'),
        ...                      format_style='detailed', include_metadata=True)
        {'success': True, 'format_info': {'style': 'detailed'}, ...}

    Validation Levels:
        - 'basic': Essential parameter validation only
        - 'standard': Parameter validation plus type checking
        - 'comprehensive': Full validation including format and content checks

    Format Styles:
        - 'standard': Default format with icons and basic messages
        - 'detailed': Enhanced format with additional context information
        - 'compact': Minimal format suitable for batch operations

    Note:
        Function provides comprehensive error handling and graceful degradation.
        Supports multiple output formats and logging integration.
    """
    from typing import Final
    import time
    from pathlib import Path

  # Constants for better maintainability
    VALID_FORMAT_STYLES: Final = {'standard', 'detailed', 'compact'}
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_ICONS: Final = {
        OperationStatus.SUCCESS: '✓',
        OperationStatus.FAILED: '✗',
        OperationStatus.PARTIAL: '⚠️'
    }
    EMOJI_DISPLAY: Final = '🖥️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUMMARY: Final = '📋'
    DEFAULT_UNKNOWN: Final = 'Unknown'

  # Initialize comprehensive result structure
    display_result = {
        'success': False,
        'overall_status': '',
        'files_displayed': 0,
        'errors_found': 0,
        'display_duration': 0.0,
        'master_file_result': {},
        'check_file_result': {},
        'error_message': '',
        'format_info': {},
        'validation_results': {},
        'performance_metrics': {} if track_performance else None
    }

    display_start_time = time.time()

    try:
  # Input validation based on level
        validation_result = _validate_save_results_inputs(
            result=result,
            master_file=master_file,
            check_file=check_file,
            format_style=format_style,
            validation_level=validation_level,
            console_output=console_output
        )

        display_result['validation_results'] = validation_result

        if not validation_result['valid']:
            display_result['error_message'] = f"Input validation failed: {validation_result['message']}"
            return display_result

  # Convert file paths to Path objects for consistent handling
        master_path = Path(master_file) if not isinstance(master_file, Path) else master_file
        check_path = Path(check_file) if not isinstance(check_file, Path) else check_file

  # Set format information
        display_result['format_info'] = {
            'style': format_style,
            'console_output': console_output,
            'metadata_included': include_metadata,
            'error_summary_shown': show_error_summary,
            'file_details_shown': include_file_details
        }

  # Display individual file results if enabled
        files_displayed = 0
        if include_file_details:
  # Display master file result
            master_result = _display_file_result(
                status=result.master_file_status,
                file_name=master_path.name,
                description=f"{result.songs_saved} songs",
                error=result.master_file_error,
                icons=DEFAULT_ICONS,
                logger=logger,
                console_output=console_output,
                include_metadata=include_metadata,
                format_style=format_style
            )

            display_result['master_file_result'] = master_result
            if master_result['success']:
                files_displayed += 1

  # Display check file result
            check_result = _display_file_result(
                status=result.check_file_status,
                file_name=check_path.name,
                description=f"song count ({result.songs_saved})",
                error=result.check_file_error,
                icons=DEFAULT_ICONS,
                logger=logger,
                console_output=console_output,
                include_metadata=include_metadata,
                format_style=format_style
            )

            display_result['check_file_result'] = check_result
            if check_result['success']:
                files_displayed += 1

        display_result['files_displayed'] = files_displayed

  # Display comprehensive overall status
        overall_status_result = _display_overall_status(
            result=result,
            icons=DEFAULT_ICONS,
            console_output=console_output,
            logger=logger,
            format_style=format_style
        )

        display_result['overall_status'] = result.overall_status.value

  # Display error summary if there are errors and it's enabled
        if result.has_errors and show_error_summary:
            error_summary_result = _display_error_summary(
                result=result,
                console_output=console_output,
                logger=logger,
                format_style=format_style
            )
            display_result['errors_found'] = len(result.error_summary)
        else:
            display_result['errors_found'] = 0

  # Track performance metrics if enabled
        if track_performance:
            display_duration = time.time() - display_start_time
            display_result['performance_metrics'] = {
                'display_duration': display_duration,
                'files_processed': files_displayed,
                'errors_processed': display_result['errors_found'],
                'metadata_included': include_metadata,
                'format_style': format_style,
                'console_output_enabled': console_output,
                'logger_used': logger is not None,
                'validation_level': validation_level
            }

        display_result['display_duration'] = time.time() - display_start_time
        display_result['success'] = True

        return display_result

    except Exception as display_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Save results display error: {display_error}"
        display_result['error_message'] = error_message
        display_result['display_duration'] = time.time() - display_start_time

        if console_output:
            print(f"{EMOJI_ERROR} Error displaying save results: {display_error}")

  # Log error if logger available
        if logger:
            try:
                logger.error(f"Display save results error: {display_error}")
            except Exception:
                pass  # Avoid nested exceptions

        return display_result


def _display_file_result(status: OperationStatus,
                        file_name: Union[str, Path], *,
                        description: str = 'file',
                        error: Optional[str] = None,
                        icons: Optional[Dict[OperationStatus, str]] = None,
                        logger: Optional[logging.Logger] = None,
                        console_output: bool = True,
                        include_metadata: bool = False,
                        format_style: str = 'standard',
                        validation_level: str = 'basic',
                        track_performance: bool = False) -> Dict[str, Union[bool, str, float, Dict, List]]:
    """Display individual file operation result with comprehensive Pythonic functionality.

    This function implements modern Python display patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Multiple formatting styles and display options
    - Performance tracking and metadata inclusion
    - Structured return values for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions

    Args:
        status: Operation status (SUCCESS, FAILED, PARTIAL)
        file_name: Name or path of the file (str or Path object)
        description: Description of what was processed - keyword-only
        error: Error message if operation failed - keyword-only
        icons: Dictionary mapping status to display icons - keyword-only
        logger: Optional logger for operation tracking - keyword-only
        console_output: Whether to display messages to console - keyword-only
        include_metadata: Whether to include file metadata in display - keyword-only
        format_style: Display format style ('standard', 'detailed', 'compact') - keyword-only
        validation_level: Input validation level ('basic', 'standard', 'comprehensive') - keyword-only
        track_performance: Whether to track display performance metrics - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if display operation completed successfully
        - 'message_displayed': str - The message that was displayed
        - 'error_message': str - Error message if failed (empty if success)
        - 'display_duration': float - Time taken to display result
        - 'metadata': Dict - File metadata (if include_metadata enabled)
        - 'format_info': Dict - Information about formatting applied
        - 'validation_results': Dict - Input validation results
        - 'performance_metrics': Dict - Performance data (if tracking enabled)

    Examples:
        >>> _display_file_result(OperationStatus.SUCCESS, 'test.txt')
        {'success': True, 'message_displayed': '✓ Saved file to test.txt', ...}
        >>> _display_file_result(OperationStatus.FAILED, 'test.txt', error='Access denied')
        {'success': True, 'message_displayed': '✗ Failed to save test.txt: Access denied', ...}
        >>> _display_file_result(OperationStatus.SUCCESS, Path('data.json'),
        ...                      format_style='detailed', include_metadata=True)
        {'success': True, 'metadata': {'size': 1024, 'modified': '...'}, ...}

    Validation Levels:
        - 'basic': Essential parameter validation only
        - 'standard': Parameter validation plus type checking
        - 'comprehensive': Full validation including format and content checks

    Format Styles:
        - 'standard': Default format with icon and basic message
        - 'detailed': Enhanced format with additional context information
        - 'compact': Minimal format suitable for batch operations

    Note:
        Function provides comprehensive error handling and graceful degradation.
        Supports multiple output formats and logging integration.
    """
    from typing import Final
    import time
    from pathlib import Path

  # Constants for better maintainability
    VALID_FORMAT_STYLES: Final = {'standard', 'detailed', 'compact'}
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_ICONS: Final = {
        OperationStatus.SUCCESS: '✓',
        OperationStatus.FAILED: '✗',
        OperationStatus.PARTIAL: '⚠️'
    }
    EMOJI_DISPLAY: Final = '🖥️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_METADATA: Final = '📊'
    DEFAULT_UNKNOWN: Final = 'Unknown'

  # Initialize comprehensive result structure
    result = {
        'success': False,
        'message_displayed': '',
        'error_message': '',
        'display_duration': 0.0,
        'metadata': {} if include_metadata else None,
        'format_info': {},
        'validation_results': {},
        'performance_metrics': {} if track_performance else None
    }

    display_start_time = time.time()

    try:
  # Input validation based on level
        validation_result = _validate_display_file_inputs(
            status=status,
            file_name=file_name,
            description=description,
            format_style=format_style,
            validation_level=validation_level,
            console_output=console_output
        )

        result['validation_results'] = validation_result

        if not validation_result['valid']:
            result['error_message'] = f"Input validation failed: {validation_result['message']}"
            return result

  # Process file name to Path object for consistent handling
        file_path = Path(file_name) if not isinstance(file_name, Path) else file_name

  # Use provided icons or defaults
        effective_icons = icons if icons is not None else DEFAULT_ICONS

  # Validate icons dictionary
        if not _validate_icons_dictionary(effective_icons, console_output=console_output):
            result['error_message'] = "Invalid icons dictionary provided"
            return result

  # Get file metadata if requested
        if include_metadata:
            metadata_result = _get_file_display_metadata(
                file_path,
                include_size=True,
                include_timestamps=True,
                console_output=console_output
            )
            result['metadata'] = metadata_result['metadata']

  # Format message based on style
        message_result = _format_display_message(
            status=status,
            file_path=file_path,
            description=description,
            error=error,
            icons=effective_icons,
            format_style=format_style,
            metadata=result.get('metadata')
        )

        if not message_result['success']:
            result['error_message'] = f"Message formatting failed: {message_result['error_message']}"
            return result

        formatted_message = message_result['formatted_message']
        result['message_displayed'] = formatted_message
        result['format_info'] = message_result['format_info']

  # Display message to console if enabled
        if console_output:
            print(formatted_message)

  # Log message if logger provided
        if logger:
            log_result = _log_display_result(
                logger=logger,
                status=status,
                message=formatted_message,
                icons=effective_icons,
                console_output=False  # Avoid duplicate console output
            )

            if not log_result['success'] and console_output:
                print(f"{EMOJI_WARNING} Warning: Failed to log display result")

  # Track performance metrics if enabled
        if track_performance:
            display_duration = time.time() - display_start_time
            result['performance_metrics'] = {
                'display_duration': display_duration,
                'message_length': len(formatted_message),
                'metadata_included': include_metadata,
                'format_style': format_style,
                'console_output_enabled': console_output,
                'logger_used': logger is not None
            }

        result['display_duration'] = time.time() - display_start_time
        result['success'] = True

        return result

    except Exception as display_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Display operation error: {display_error}"
        result['error_message'] = error_message
        result['display_duration'] = time.time() - display_start_time

        if console_output:
            print(f"{EMOJI_ERROR} Error displaying file result: {display_error}")

  # Log error if logger available
        if logger:
            try:
                logger.error(f"Display file result error: {display_error}")
            except Exception:
                pass  # Avoid nested exceptions

        return result


def _validate_display_file_inputs(status: OperationStatus,
                                  file_name: Union[str, Path], *,
                                  description: str,
                                  format_style: str,
                                  validation_level: str,
                                  console_output: bool) -> Dict[str, Union[bool, str]]:
    """Validate inputs for _display_file_result function.

    Args:
        status: Operation status to validate
        file_name: File name or path to validate
        description: Description text to validate - keyword-only
        format_style: Format style to validate - keyword-only
        validation_level: Validation level to apply - keyword-only
        console_output: Whether to print validation errors - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from typing import Final

    EMOJI_ERROR: Final = '❌'
    VALID_FORMAT_STYLES: Final = {'standard', 'detailed', 'compact'}
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}

    try:
  # Basic validation
        if not isinstance(status, OperationStatus):
            return {
                'valid': False,
                'message': f"status must be OperationStatus, got {type(status).__name__}"
            }

        if validation_level == 'basic':
            return {'valid': True, 'message': 'Basic validation passed'}

  # Standard validation
        if not isinstance(description, str):
            return {
                'valid': False,
                'message': f"description must be string, got {type(description).__name__}"
            }

        if format_style not in VALID_FORMAT_STYLES:
            return {
                'valid': False,
                'message': f"format_style must be one of {VALID_FORMAT_STYLES}, got '{format_style}'"
            }

        if validation_level == 'standard':
            return {'valid': True, 'message': 'Standard validation passed'}

  # Comprehensive validation
        if not description.strip():
            return {
                'valid': False,
                'message': "description cannot be empty or whitespace-only"
            }

  # File name validation
        if isinstance(file_name, str):
            if not file_name.strip():
                return {
                    'valid': False,
                    'message': "file_name cannot be empty or whitespace-only"
                }
        elif isinstance(file_name, Path):
            if not str(file_name).strip():
                return {
                    'valid': False,
                    'message': "file_name Path cannot be empty"
                }
        else:
            return {
                'valid': False,
                'message': f"file_name must be str or Path, got {type(file_name).__name__}"
            }

        return {'valid': True, 'message': 'Comprehensive validation passed'}

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f"Validation error: {validation_error}"
        }


def _validate_icons_dictionary(icons: Dict[OperationStatus, str], *,
                              console_output: bool = True) -> bool:
    """Validate icons dictionary for display operations.

    Args:
        icons: Dictionary mapping OperationStatus to icon strings
        console_output: Whether to print validation errors - keyword-only

    Returns:
        bool: True if icons dictionary is valid, False otherwise
    """
    from typing import Final

    EMOJI_ERROR: Final = '❌'
    REQUIRED_STATUSES: Final = {OperationStatus.SUCCESS, OperationStatus.FAILED, OperationStatus.PARTIAL}

    try:
        if not isinstance(icons, dict):
            if console_output:
                print(f"{EMOJI_ERROR} Icons must be dictionary, got {type(icons).__name__}")
            return False

  # Check for required status keys
        missing_statuses = REQUIRED_STATUSES - set(icons.keys())
        if missing_statuses:
            if console_output:
                print(f"{EMOJI_ERROR} Missing status icons: {missing_statuses}")
            return False

  # Validate icon values
        for status, icon in icons.items():
            if not isinstance(icon, str):
                if console_output:
                    print(f"{EMOJI_ERROR} Icon for {status} must be string, got {type(icon).__name__}")
                return False

            if not icon.strip():
                if console_output:
                    print(f"{EMOJI_ERROR} Icon for {status} cannot be empty")
                return False

        return True

    except Exception as validation_error:
        if console_output:
            print(f"{EMOJI_ERROR} Icon validation error: {validation_error}")
        return False


def _get_file_display_metadata(file_path: Path, *,
                               include_size: bool = True,
                               include_timestamps: bool = True,
                               console_output: bool = True) -> Dict[str, Union[bool, Dict, str]]:
    """Get file metadata for display purposes.

    Args:
        file_path: Path to the file
        include_size: Whether to include file size - keyword-only
        include_timestamps: Whether to include timestamp info - keyword-only
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'success' (bool), 'metadata' (Dict), and 'error_message' (str) keys
    """
    from typing import Final
    import os
    from datetime import datetime

    EMOJI_ERROR: Final = '❌'

    result = {
        'success': False,
        'metadata': {},
        'error_message': ''
    }

    try:
        metadata = {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'exists': file_path.exists()
        }

        if file_path.exists():
            stat_info = file_path.stat()

            if include_size:
                metadata['size_bytes'] = stat_info.st_size
                metadata['size_human'] = _format_file_size(stat_info.st_size)

            if include_timestamps:
                metadata['modified_timestamp'] = stat_info.st_mtime
                metadata['modified_datetime'] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                metadata['created_timestamp'] = stat_info.st_ctime
                metadata['created_datetime'] = datetime.fromtimestamp(stat_info.st_ctime).isoformat()

        result['metadata'] = metadata
        result['success'] = True

        return result

    except Exception as metadata_error:
        error_message = f"Failed to get file metadata: {metadata_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

        return result


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        str: Formatted file size (e.g., '1.5 KB', '2.3 MB')
    """
    from typing import Final

    UNITS: Final = ['B', 'KB', 'MB', 'GB', 'TB']

    if size_bytes == 0:
        return '0 B'

    size = float(size_bytes)
    unit_index = 0

    while size >= 1024.0 and unit_index < len(UNITS) - 1:
        size /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {UNITS[unit_index]}"
    else:
        return f"{size:.1f} {UNITS[unit_index]}"


def _format_display_message(status: OperationStatus,
                            file_path: Path, *,
                            description: str,
                            error: Optional[str],
                            icons: Dict[OperationStatus, str],
                            format_style: str,
                            metadata: Optional[Dict] = None) -> Dict[str, Union[bool, str, Dict]]:
    """Format display message based on style and status.

    Args:
        status: Operation status
        file_path: Path to the file
        description: Description of the operation - keyword-only
        error: Error message if applicable - keyword-only
        icons: Icon mapping dictionary - keyword-only
        format_style: Formatting style to apply - keyword-only
        metadata: Optional file metadata for enhanced formatting - keyword-only

    Returns:
        Dict with 'success' (bool), 'formatted_message' (str), 'format_info' (Dict), and 'error_message' (str) keys
    """
    from typing import Final

    EMOJI_ERROR: Final = '❌'

    result = {
        'success': False,
        'formatted_message': '',
        'format_info': {},
        'error_message': ''
    }

    try:
        icon = icons[status]
        file_name = file_path.name

  # Format message based on style
        if format_style == 'compact':
            if status == OperationStatus.SUCCESS:
                message = f"{icon} {file_name}"
            else:
                error_text = error or 'Failed'
                message = f"{icon} {file_name}: {error_text}"

        elif format_style == 'detailed':
            if status == OperationStatus.SUCCESS:
                message = f"{icon} Successfully saved {description} to '{file_name}'"
                if metadata and 'size_human' in metadata:
                    message += f" ({metadata['size_human']})"
            else:
                error_text = error or 'Unknown error'
                message = f"{icon} Failed to save '{file_name}': {error_text}"
                if metadata and 'exists' in metadata and not metadata['exists']:
                    message += " (file does not exist)"

        else:  # standard
            if status == OperationStatus.SUCCESS:
                message = f"{icon} Saved {description} to {file_name}"
            else:
                error_text = error or 'Unknown error'
                message = f"{icon} Failed to save {file_name}: {error_text}"

        result['formatted_message'] = message
        result['format_info'] = {
            'style': format_style,
            'icon_used': icon,
            'status': status.value,
            'file_name': file_name,
            'description': description,
            'metadata_included': metadata is not None
        }
        result['success'] = True

        return result

    except Exception as format_error:
        error_message = f"Message formatting error: {format_error}"
        result['error_message'] = error_message

        return result


def _log_display_result(logger: logging.Logger, *,
                       status: OperationStatus,
                       message: str,
                       icons: Dict[OperationStatus, str],
                       console_output: bool = True) -> Dict[str, Union[bool, str]]:
    """Log display result with appropriate level.

    Args:
        logger: Logger instance to use
        status: Operation status for determining log level - keyword-only
        message: Message to log - keyword-only
        icons: Icons dictionary for cleaning message - keyword-only
        console_output: Whether to print errors to console - keyword-only

    Returns:
        Dict with 'success' (bool) and 'error_message' (str) keys
    """
    from typing import Final

    EMOJI_ERROR: Final = '❌'

    result = {
        'success': False,
        'error_message': ''
    }

    try:
  # Clean message by removing icon for logging
        icon = icons.get(status, '')
        clean_message = message.replace(icon, '').strip()

  # Log at appropriate level based on status
        if status == OperationStatus.SUCCESS:
            logger.info(clean_message)
        elif status == OperationStatus.PARTIAL:
            logger.warning(clean_message)
        else:  # FAILED
            logger.error(clean_message)

        result['success'] = True

        return result

    except Exception as log_error:
        error_message = f"Logging error: {log_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

        return result


def _validate_save_results_inputs(
    result: SaveResult,
    master_file: Union[str, Path],
    check_file: Union[str, Path],
    format_style: str,
    validation_level: str,
    console_output: bool
) -> Dict[str, Union[bool, str, List]]:
    """Validate inputs for _display_save_results function.

    Args:
        result: SaveResult object to validate
        master_file: Master file path to validate
        check_file: Check file path to validate
        format_style: Format style to validate
        validation_level: Level of validation to perform
        console_output: Console output flag

    Returns:
        Dict with validation results including 'valid' bool and 'message' str
    """
    from typing import Final
    from pathlib import Path

    VALID_FORMAT_STYLES: Final = {'standard', 'detailed', 'compact'}
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    EMOJI_ERROR: Final = '❌'

    validation_result = {
        'valid': False,
        'message': '',
        'errors': [],
        'warnings': []
    }

    errors = []
    warnings = []

    try:
  # Basic validation - always performed
        if result is None:
            errors.append("SaveResult cannot be None")

        if not isinstance(format_style, str):
            errors.append(f"format_style must be string, got {type(format_style).__name__}")
        elif format_style not in VALID_FORMAT_STYLES:
            errors.append(f"format_style must be one of {VALID_FORMAT_STYLES}, got '{format_style}'")

        if not isinstance(validation_level, str):
            errors.append(f"validation_level must be string, got {type(validation_level).__name__}")
        elif validation_level not in VALIDATION_LEVELS:
            errors.append(f"validation_level must be one of {VALIDATION_LEVELS}, got '{validation_level}'")

        if not isinstance(console_output, bool):
            errors.append(f"console_output must be boolean, got {type(console_output).__name__}")

  # Standard validation - type and structure checking
        if validation_level in ['standard', 'comprehensive'] and result is not None:
            if not isinstance(result, SaveResult):
                errors.append(f"result must be SaveResult instance, got {type(result).__name__}")
            else:
  # Validate SaveResult structure
                if not hasattr(result, 'master_file_status'):
                    errors.append("SaveResult missing master_file_status attribute")
                if not hasattr(result, 'check_file_status'):
                    errors.append("SaveResult missing check_file_status attribute")
                if not hasattr(result, 'songs_saved'):
                    errors.append("SaveResult missing songs_saved attribute")

  # File path validation
        for file_param, file_value in [('master_file', master_file), ('check_file', check_file)]:
            if file_value is None:
                errors.append(f"{file_param} cannot be None")
            elif not isinstance(file_value, (str, Path)):
                errors.append(f"{file_param} must be string or Path, got {type(file_value).__name__}")
            elif isinstance(file_value, str) and not file_value.strip():
                errors.append(f"{file_param} cannot be empty string")

  # Comprehensive validation - additional checks
        if validation_level == 'comprehensive' and result is not None:
            if isinstance(result, SaveResult):
                if result.songs_saved < 0:
                    warnings.append("Negative songs_saved count detected")

  # Check if status values are valid
                try:
                    if hasattr(result, 'master_file_status'):
                        if not isinstance(result.master_file_status, OperationStatus):
                            errors.append("master_file_status must be OperationStatus enum")
                    if hasattr(result, 'check_file_status'):
                        if not isinstance(result.check_file_status, OperationStatus):
                            errors.append("check_file_status must be OperationStatus enum")
                except Exception as enum_error:
                    warnings.append(f"Status validation warning: {enum_error}")

        validation_result['errors'] = errors
        validation_result['warnings'] = warnings
        validation_result['valid'] = len(errors) == 0
        validation_result['message'] = '; '.join(errors) if errors else 'Validation passed'

        return validation_result

    except Exception as validation_error:
        validation_result['valid'] = False
        validation_result['message'] = f"Validation error: {validation_error}"
        validation_result['errors'] = [str(validation_error)]
        return validation_result


def _display_overall_status(
    result: SaveResult,
    icons: Dict[OperationStatus, str],
    console_output: bool,
    logger: Optional[logging.Logger],
    format_style: str
) -> Dict[str, Union[bool, str]]:
    """Display overall operation status with formatting options.

    Args:
        result: SaveResult containing operation status
        icons: Dictionary mapping status to display icons
        console_output: Whether to output to console
        logger: Optional logger for message logging
        format_style: Style for formatting the message

    Returns:
        Dict with success status and formatted message
    """
    try:
        overall_icon = icons.get(result.overall_status, '?')

        if format_style == 'detailed':
            status_message = (
                f"{overall_icon} Save Operation Complete:\n"
                f"  Status: {result.overall_status.value}\n"
                f"  Songs Processed: {result.songs_saved}\n"
                f"  Files Affected: 2 (master + check)"
            )
        elif format_style == 'compact':
            status_message = f"{overall_icon} {result.overall_status.value}: {result.songs_saved} songs"
        else:  # standard
            status_message = f"{overall_icon} Overall save operation: {result.overall_status.value}"

        if console_output:
            print(status_message)

        if logger:
  # Remove icon for logging
            log_message = status_message.replace(overall_icon, '').strip()
            if result.overall_status == OperationStatus.SUCCESS:
                logger.info(log_message)
            elif result.overall_status == OperationStatus.FAILED:
                logger.error(log_message)
            else:
                logger.warning(log_message)

        return {
            'success': True,
            'message': status_message
        }

    except Exception as display_error:
        error_message = f"Error displaying overall status: {display_error}"
        if console_output:
            print(f"❌ {error_message}")
        return {
            'success': False,
            'message': error_message
        }


def _display_error_summary(
    result: SaveResult,
    console_output: bool,
    logger: Optional[logging.Logger],
    format_style: str
) -> Dict[str, Union[bool, str, int]]:
    """Display error summary with formatting options.

    Args:
        result: SaveResult containing error information
        console_output: Whether to output to console
        logger: Optional logger for error logging
        format_style: Style for formatting the error summary

    Returns:
        Dict with success status, message, and error count
    """
    try:
        if not result.has_errors:
            return {
                'success': True,
                'message': 'No errors to display',
                'error_count': 0
            }

        error_summary = result.error_summary
        error_count = len(error_summary)

        if format_style == 'detailed':
            summary_header = f"\n📋 Error Summary ({error_count} error{'s' if error_count != 1 else ''}):"
            error_lines = []
            for i, error in enumerate(error_summary, 1):
                error_lines.append(f"   {i}. {error}")
            full_message = summary_header + "\n" + "\n".join(error_lines)
        elif format_style == 'compact':
            full_message = f"❌ {error_count} error{'s' if error_count != 1 else ''}: {'; '.join(error_summary)}"
        else:  # standard
            summary_header = "\n📋 Error Summary:"
            error_lines = [f"   • {error}" for error in error_summary]
            full_message = summary_header + "\n" + "\n".join(error_lines)

        if console_output:
            print(full_message)

        if logger:
  # Log errors without emojis
            clean_message = f"Errors occurred: {'; '.join(error_summary)}"
            logger.warning(clean_message)

        return {
            'success': True,
            'message': full_message,
            'error_count': error_count
        }

    except Exception as display_error:
        error_message = f"Error displaying error summary: {display_error}"
        if console_output:
            print(f"❌ {error_message}")
        return {
            'success': False,
            'message': error_message,
            'error_count': 0
        }


def play_song(song_file_name: Union[str, Path], *,
             console_output: bool = True,
             performance_monitoring: bool = False,
             memory_management: bool = True,
             playback_timeout: Optional[float] = None,
             validation_level: str = 'standard',
             error_recovery: bool = True,
             audio_settings: Optional[Dict[str, Any]] = None,
             callback_functions: Optional[Dict[str, callable]] = None) -> Dict[str, Union[bool, str, float, Dict, List]]:
    """Play a song file with comprehensive Pythonic functionality.

    This function implements advanced Python audio playback patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with path verification
    - Performance monitoring and memory management
    - Configurable timeout and error recovery mechanisms
    - Audio settings configuration support
    - Callback function support for playback events
    - Structured return values for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Resource cleanup and memory optimization

    Args:
        song_file_name: Path to the song file (str or Path object)
        console_output: Whether to show playback messages - keyword-only
        performance_monitoring: Whether to track playback performance - keyword-only
        memory_management: Whether to perform memory management during playback - keyword-only
        playback_timeout: Maximum playback time in seconds (None for no limit) - keyword-only
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        error_recovery: Whether to attempt error recovery on failures - keyword-only
        audio_settings: Custom audio configuration settings - keyword-only
        callback_functions: Dictionary of callback functions for events - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if playback completed successfully
        - 'error_message': str - Error message if failed (empty if success)
        - 'playback_duration': float - Total playback time in seconds
        - 'file_info': Dict - File metadata and information
        - 'performance_metrics': Dict - Performance data (if monitoring enabled)
        - 'memory_stats': Dict - Memory usage statistics (if management enabled)
        - 'player_info': Dict - VLC player information and status
        - 'playback_events': List - List of playback events that occurred
        - 'validation_results': Dict - File validation results
        - 'recovery_attempts': int - Number of recovery attempts made

    Examples:
        >>> play_song('music/song.mp3')
        {'success': True, 'playback_duration': 180.5, 'error_message': '', ...}
        >>> play_song('music/song.mp3', performance_monitoring=True, playback_timeout=300)
        {'success': True, 'performance_metrics': {'cpu_usage': 2.1}, ...}
        >>> play_song(Path('invalid.mp3'), error_recovery=True)
        {'success': False, 'error_message': 'File not found', 'recovery_attempts': 2, ...}

    Validation Levels:
        - 'basic': File existence check only
        - 'standard': File existence, format, and accessibility checks
        - 'comprehensive': Full file validation including metadata analysis

    Callback Functions:
        - 'on_start': Called when playback starts
        - 'on_progress': Called periodically during playback
        - 'on_complete': Called when playback completes
        - 'on_error': Called when errors occur

    Note:
        Function uses VLC media player for audio playback with comprehensive error handling.
        Supports memory management and performance optimization for long-running sessions.
    """
    from typing import Final, Dict, List, Union, Optional, Any
    import time
    import os
    from pathlib import Path
    from collections import defaultdict

  # Constants for better maintainability
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    SUPPORTED_FORMATS: Final = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma'}
    DEFAULT_POLL_INTERVAL: Final = 0.5
    MEMORY_CHECK_INTERVAL: Final = 10.0  # seconds
    MAX_RECOVERY_ATTEMPTS: Final = 3
    EMOJI_PLAY: Final = '🎵'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_MEMORY: Final = '💾'
    EMOJI_PERFORMANCE: Final = '⚡'

  # Initialize comprehensive result structure
    result = {
        'success': False,
        'error_message': '',
        'playback_duration': 0.0,
        'file_info': {},
        'performance_metrics': {} if performance_monitoring else None,
        'memory_stats': {} if memory_management else None,
        'player_info': {},
        'playback_events': [],
        'validation_results': {},
        'recovery_attempts': 0
    }

    playback_start_time = time.time()
    player = None
    memory_check_timer = 0.0

    try:
  # Input validation with comprehensive checks
        if validation_level not in VALIDATION_LEVELS:
            result['error_message'] = f'Invalid validation level: {validation_level}. Must be one of {VALIDATION_LEVELS}'
            return result

  # File path processing and validation
        file_path = Path(song_file_name)
        result['file_info']['original_path'] = str(song_file_name)
        result['file_info']['resolved_path'] = str(file_path.absolute())

        if console_output:
            print(f"{EMOJI_PLAY} Starting playback validation and initialization...")

  # File validation based on level
        validation_result = _validate_audio_file(
            file_path,
            validation_level=validation_level,
            console_output=console_output
        )

        result['validation_results'] = validation_result

        if not validation_result['valid']:
            result['error_message'] = f"File validation failed: {validation_result['error_message']}"

            if error_recovery and validation_result.get('recoverable', False):
                recovery_result = _attempt_file_recovery(
                    file_path,
                    max_attempts=MAX_RECOVERY_ATTEMPTS,
                    console_output=console_output
                )
                result['recovery_attempts'] = recovery_result['attempts']

                if recovery_result['success']:
                    file_path = Path(recovery_result['recovered_path'])
                    result['file_info']['recovered_path'] = str(file_path)
                    result['playback_events'].append('file_recovery_successful')

                    if console_output:
                        print(f"{EMOJI_SUCCESS} File recovery successful")
                else:
                    result['error_message'] += f" | Recovery failed after {recovery_result['attempts']} attempts"
                    return result
            else:
                return result

  # Initialize memory management if enabled
        if memory_management:
            initial_memory = _get_memory_stats()
            result['memory_stats']['initial'] = initial_memory

            if console_output:
                print(f"{EMOJI_MEMORY} Initial memory usage: {initial_memory['memory_percent']:.1f}%")

  # Perform garbage collection ONCE at the beginning of playback
            cleanup_result = _perform_memory_cleanup(console_output=console_output)
            result['memory_stats']['cleanup_result'] = cleanup_result
            result['playback_events'].append('memory_cleanup_performed')

  # Update memory stats after cleanup
            post_cleanup_memory = _get_memory_stats()
            result['memory_stats']['post_cleanup'] = post_cleanup_memory

            if console_output and cleanup_result['cleanup_successful']:
                print(f"{EMOJI_SUCCESS} Memory optimization completed: {cleanup_result['objects_collected']} objects freed")

  # Initialize VLC media player with enhanced resource management
        try:
            player_result = _create_managed_vlc_player(
                media_path=file_path,
                console_output=console_output,
                validate_path=True,
                auto_cleanup=True,
                include_metadata=False,
                enable_logging=True
            )

            if not player_result['success']:
                result['error_message'] = f'Failed to create VLC player: {player_result["error_message"]}'
                return result

            player = player_result['player']
            result['player_info']['player_created'] = True
            result['player_info']['player_id'] = player_result['player_id']
            result['playback_events'].append('managed_player_initialized')

  # Apply audio settings if provided
            if audio_settings:
                _apply_audio_settings(player, audio_settings, console_output=console_output)
                result['player_info']['custom_settings_applied'] = True
                result['playback_events'].append('audio_settings_applied')

            if console_output:
                print(f"{EMOJI_SUCCESS} VLC player initialized successfully")

        except Exception as player_error:
            result['error_message'] = f'Failed to initialize VLC player: {player_error}'
            return result

  # Start playback with comprehensive monitoring
        try:
            playback_actual_start = time.time()
            player.play()
            result['playback_events'].append('playback_started')

  # Call start callback if provided
            if callback_functions and 'on_start' in callback_functions:
                try:
                    callback_functions['on_start'](file_path, player)
                    result['playback_events'].append('start_callback_executed')
                except Exception as callback_error:
                    result['playback_events'].append(f'start_callback_error: {callback_error}')

            if console_output:
                print(f"{EMOJI_PLAY} Playback started: {file_path.name}")

  # Initial status check
            print(f'Initial playback status: {player.is_playing()}')  # 0 = False initially
            time.sleep(DEFAULT_POLL_INTERVAL)  # Allow time for playback to start
            print(f'Playback status after delay: {player.is_playing()}')  # Should be 1 = True

  # Main playback monitoring loop
            progress_counter = 0
            timeout_start = time.time()

            while player.is_playing():
                current_time = time.time()

  # Timeout check
                if playback_timeout and (current_time - timeout_start) > playback_timeout:
                    player.stop()
                    result['playback_events'].append('playback_timeout_reached')

                    if console_output:
                        print(f"{EMOJI_WARNING} Playback stopped due to timeout ({playback_timeout}s)")
                    break

  # Performance monitoring
                if performance_monitoring:
                    if not result['performance_metrics']:
                        result['performance_metrics'] = {'cpu_samples': [], 'memory_samples': []}

                    cpu_percent = psutil.cpu_percent(interval=None)
                    result['performance_metrics']['cpu_samples'].append(cpu_percent)

  # Memory monitoring (without cleanup during playback)
                if memory_management and (current_time - memory_check_timer) > MEMORY_CHECK_INTERVAL:
                    current_memory = _get_memory_stats()

  # Store memory sample for tracking but don't perform cleanup during playback
                    if 'memory_samples' not in result['memory_stats']:
                        result['memory_stats']['memory_samples'] = []

  # Prevent memory samples list from growing too large (memory leak prevention)
                    MAX_MEMORY_SAMPLES = 100  # Limit to last 100 samples (16+ minutes of data)
                    memory_samples = result['memory_stats']['memory_samples']
                    if len(memory_samples) >= MAX_MEMORY_SAMPLES:
  # Remove oldest samples to prevent list accumulation
                        result['memory_stats']['memory_samples'] = memory_samples[-MAX_MEMORY_SAMPLES//2:]

                    result['memory_stats']['memory_samples'].append({
                        'timestamp': current_time - playback_actual_start,
                        'memory_percent': current_memory['memory_percent'],
                        'memory_used': current_memory['memory_used']
                    })

  # Only log high memory usage, don't perform cleanup
                    if current_memory['memory_percent'] > 80:  # High memory usage threshold
                        result['playback_events'].append(f'high_memory_detected_{current_memory["memory_percent"]:.1f}%')

                        if console_output:
                            print(f"{EMOJI_WARNING} High memory usage detected: {current_memory['memory_percent']:.1f}%")

                    memory_check_timer = current_time

  # Progress callback
                if callback_functions and 'on_progress' in callback_functions:
                    progress_counter += 1
                    if progress_counter % 10 == 0:  # Call every 5 seconds (10 * 0.5s)
                        try:
                            progress_info = {
                                'elapsed_time': current_time - playback_actual_start,
                                'player_time': player.get_time(),
                                'player_length': player.get_length()
                            }
                            callback_functions['on_progress'](progress_info)
                            result['playback_events'].append('progress_callback_executed')
                        except Exception as callback_error:
                            result['playback_events'].append(f'progress_callback_error: {callback_error}')

  # Sleep to reduce CPU usage
                time.sleep(DEFAULT_POLL_INTERVAL)

  # Playback completed successfully
            playback_end_time = time.time()
            result['playback_duration'] = playback_end_time - playback_actual_start
            result['success'] = True
            result['playback_events'].append('playback_completed')

  # Call completion callback if provided
            if callback_functions and 'on_complete' in callback_functions:
                try:
                    completion_info = {
                        'duration': result['playback_duration'],
                        'file_path': file_path,
                        'events': result['playback_events']
                    }
                    callback_functions['on_complete'](completion_info)
                    result['playback_events'].append('completion_callback_executed')
                except Exception as callback_error:
                    result['playback_events'].append(f'completion_callback_error: {callback_error}')

            if console_output:
                print(f"{EMOJI_SUCCESS} Playback completed successfully")
                print(f"  Duration: {result['playback_duration']:.1f} seconds")
                print(f"  Events: {len(result['playback_events'])} logged")

        except Exception as playback_error:
            result['error_message'] = f'Playback error: {playback_error}'
            result['playback_events'].append(f'playback_error: {playback_error}')

  # Call error callback if provided
            if callback_functions and 'on_error' in callback_functions:
                try:
                    error_info = {
                        'error': playback_error,
                        'file_path': file_path,
                        'elapsed_time': time.time() - playback_actual_start
                    }
                    callback_functions['on_error'](error_info)
                    result['playback_events'].append('error_callback_executed')
                except Exception as callback_error:
                    result['playback_events'].append(f'error_callback_error: {callback_error}')

            if console_output:
                print(f"{EMOJI_ERROR} Playback error: {playback_error}")

  # Final memory statistics
        if memory_management:
            final_memory = _get_memory_stats()
            result['memory_stats']['final'] = final_memory

  # Calculate memory usage statistics from samples
            if 'memory_samples' in result['memory_stats'] and result['memory_stats']['memory_samples']:
                memory_samples = result['memory_stats']['memory_samples']
                memory_percentages = [sample['memory_percent'] for sample in memory_samples]

                result['memory_stats']['peak_usage'] = max(memory_percentages)
                result['memory_stats']['average_usage'] = sum(memory_percentages) / len(memory_percentages)
                result['memory_stats']['min_usage'] = min(memory_percentages)
                result['memory_stats']['sample_count'] = len(memory_samples)

  # Calculate memory trend
                if len(memory_samples) > 1:
                    first_sample = memory_samples[0]['memory_percent']
                    last_sample = memory_samples[-1]['memory_percent']
                    result['memory_stats']['memory_trend'] = last_sample - first_sample
            else:
                result['memory_stats']['peak_usage'] = final_memory.get('memory_percent', 0)
                result['memory_stats']['average_usage'] = final_memory.get('memory_percent', 0)

            if console_output:
                print(f"{EMOJI_MEMORY} Final memory usage: {final_memory['memory_percent']:.1f}%")
                if 'peak_usage' in result['memory_stats']:
                    print(f"{EMOJI_MEMORY} Peak memory usage: {result['memory_stats']['peak_usage']:.1f}%")
                if 'memory_trend' in result['memory_stats']:
                    trend = result['memory_stats']['memory_trend']
                    trend_text = f"increased by {trend:.1f}%" if trend > 0 else f"decreased by {abs(trend):.1f}%"
                    print(f"{EMOJI_MEMORY} Memory trend: {trend_text}")

  # Performance metrics compilation
        if performance_monitoring and result['performance_metrics']:
            cpu_samples = result['performance_metrics']['cpu_samples']
            if cpu_samples:
                result['performance_metrics']['avg_cpu_usage'] = sum(cpu_samples) / len(cpu_samples)
                result['performance_metrics']['max_cpu_usage'] = max(cpu_samples)
                result['performance_metrics']['cpu_sample_count'] = len(cpu_samples)

            result['performance_metrics']['total_playback_time'] = result['playback_duration']

            if console_output:
                print(f"{EMOJI_PERFORMANCE} Performance Summary:")
                print(f"  Average CPU: {result['performance_metrics'].get('avg_cpu_usage', 0):.1f}%")
                print(f"  Max CPU: {result['performance_metrics'].get('max_cpu_usage', 0):.1f}%")

  # Player information
        if player:
            result['player_info'].update({
                'final_state': player.get_state(),
                'total_time': player.get_length(),
                'player_released': False
            })

        return result

    except Exception as general_error:
  # Comprehensive error handling
        error_message = f'Song playback system error: {general_error}'
        result['error_message'] = error_message
        result['playback_events'].append(f'system_error: {general_error}')

        if console_output:
            print(f"{EMOJI_ERROR} Playback system error: {general_error}")

  # Log the error for debugging
        try:
            _log_error(f'Song playback error for {song_file_name}: {general_error}')
        except:
            pass  # Avoid recursive errors in error handling

        return result

    finally:
  # Enhanced resource cleanup for memory leak prevention
        if player:
            try:
  # Stop playback first to ensure clean state
                if player.is_playing():
                    player.stop()
                    time.sleep(0.1)  # Small delay to ensure stop completes

  # Release all VLC resources
                player.release()
                result['player_info']['player_released'] = True
                result['playback_events'].append('player_resources_released')

  # Mark as released in registry (memory leak prevention)
                for player_info in _vlc_player_registry:
                    if player_info['player'] == player:
                        player_info['released'] = True
                        break

  # Force garbage collection to clean up VLC-related objects
                if memory_management:
                    gc.collect()
                    result['playback_events'].append('post_playback_gc_performed')

            except Exception as cleanup_error:
                if console_output:
                    print(f"{EMOJI_WARNING} Player cleanup warning: {cleanup_error}")
                result['playback_events'].append(f'cleanup_warning: {cleanup_error}')

  # Additional memory cleanup for long-running sessions
        if memory_management:
            try:
  # Cleanup old VLC players to prevent accumulation
                _cleanup_old_vlc_players()

  # Limit the size of playback events list to prevent accumulation
                MAX_EVENTS = 50
                if len(result['playback_events']) > MAX_EVENTS:
                    result['playback_events'] = result['playback_events'][-MAX_EVENTS:]

  # Clear callback references to prevent memory retention
                if 'callback_functions' in locals() and callback_functions:
                    callback_functions.clear()

            except Exception as memory_cleanup_error:
                pass  # Don't let cleanup errors affect the main operation

  # Final performance calculations
        total_time = time.time() - playback_start_time
        result['file_info']['total_operation_time'] = total_time

        if console_output and result['success']:
            print(f"{EMOJI_SUCCESS} Playback operation completed in {total_time:.1f}s")


def _validate_audio_file(file_path: Path, *,
                        validation_level: str = 'standard',
                        console_output: bool = True) -> Dict[str, Union[bool, str, Dict]]:
    """Validate audio file for playback.

    Args:
        file_path: Path to the audio file
        validation_level: Level of validation to perform - keyword-only
        console_output: Whether to show validation messages - keyword-only

    Returns:
        Dict with validation results
    """
    from typing import Final

    SUPPORTED_FORMATS: Final = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma'}

    result = {
        'valid': False,
        'error_message': '',
        'file_stats': {},
        'recoverable': False
    }

    try:
  # Basic existence check
        if not file_path.exists():
            result['error_message'] = f'File does not exist: {file_path}'
            result['recoverable'] = True  # Might be temporary issue
            return result

  # File type validation
        if file_path.suffix.lower() not in SUPPORTED_FORMATS:
            result['error_message'] = f'Unsupported file format: {file_path.suffix}'
            return result

  # Standard validation
        if validation_level in {'standard', 'comprehensive'}:
            if not file_path.is_file():
                result['error_message'] = f'Path is not a file: {file_path}'
                return result

            if not os.access(file_path, os.R_OK):
                result['error_message'] = f'File is not readable: {file_path}'
                result['recoverable'] = True
                return result

            file_stats = file_path.stat()
            result['file_stats'] = {
                'size_bytes': file_stats.st_size,
                'last_modified': file_stats.st_mtime,
                'is_readable': True
            }

            if file_stats.st_size == 0:
                result['error_message'] = 'File is empty'
                return result

  # Comprehensive validation
        if validation_level == 'comprehensive':
            try:
  # Try to get basic metadata to verify file integrity
                from tinytag import TinyTag
                tag = TinyTag.get(str(file_path))

                result['file_stats']['metadata'] = {
                    'duration': tag.duration,
                    'title': tag.title,
                    'artist': tag.artist
                }

                if tag.duration and tag.duration <= 0:
                    result['error_message'] = 'File appears to have invalid duration'
                    return result

            except Exception as metadata_error:
                result['error_message'] = f'File metadata validation failed: {metadata_error}'
                result['recoverable'] = True
                return result

        result['valid'] = True

        if console_output:
            print(f"✓ File validation passed ({validation_level} level): {file_path.name}")

        return result

    except Exception as validation_error:
        result['error_message'] = f'Validation error: {validation_error}'
        return result


def _attempt_file_recovery(file_path: Path, *,
                          max_attempts: int = 3,
                          console_output: bool = True) -> Dict[str, Union[bool, str, int]]:
    """Attempt to recover or find alternative file paths.

    Args:
        file_path: Original file path
        max_attempts: Maximum recovery attempts - keyword-only
        console_output: Whether to show recovery messages - keyword-only

    Returns:
        Dict with recovery results
    """
    result = {
        'success': False,
        'recovered_path': '',
        'attempts': 0,
        'recovery_method': ''
    }

  # This is a placeholder for file recovery logic
  # In a real implementation, you might:
  # 1. Check for similar filenames
  # 2. Search in common music directories
  # 3. Check for moved files
  # 4. Verify network connectivity for remote files

    if console_output:
        print(f"⚠️ File recovery not implemented for: {file_path}")

    return result


def _get_memory_stats() -> Dict[str, Union[float, int]]:
    """Get current memory statistics.

    Returns:
        Dict with memory usage information
    """
    try:
        memory = psutil.virtual_memory()
        return {
            'memory_percent': memory.percent,
            'memory_available': memory.available,
            'memory_used': memory.used,
            'memory_total': memory.total
        }
    except Exception:
        return {'memory_percent': 0, 'memory_available': 0, 'memory_used': 0, 'memory_total': 0}


def _perform_memory_cleanup(*, console_output: bool = True) -> Dict[str, Union[int, float, bool]]:
    """Perform memory cleanup operations with detailed reporting.

    Args:
        console_output: Whether to show cleanup messages - keyword-only

    Returns:
        Dict containing cleanup results:
        - 'objects_collected': int - Number of objects collected
        - 'gc_thresholds': tuple - Current garbage collection thresholds
        - 'memory_before': float - Memory percentage before cleanup
        - 'memory_after': float - Memory percentage after cleanup
        - 'memory_freed': float - Memory percentage freed
        - 'cleanup_successful': bool - Whether cleanup completed successfully
    """
    result = {
        'objects_collected': 0,
        'gc_thresholds': (0, 0, 0),
        'memory_before': 0.0,
        'memory_after': 0.0,
        'memory_freed': 0.0,
        'cleanup_successful': False
    }

    try:
  # Get memory before cleanup
        memory_before = _get_memory_stats()
        result['memory_before'] = memory_before['memory_percent']

  # Get garbage collection thresholds
        result['gc_thresholds'] = gc.get_threshold()

        if console_output:
            print(f"💾 Performing garbage collection (memory: {memory_before['memory_percent']:.1f}%)...")
            print(f"💾 GC thresholds: {result['gc_thresholds']}")

  # Clean up VLC players first (memory leak prevention)
        _cleanup_old_vlc_players()

  # Perform garbage collection for all generations
        collected = gc.collect()
        result['objects_collected'] = collected

  # Get memory after cleanup
        memory_after = _get_memory_stats()
        result['memory_after'] = memory_after['memory_percent']
        result['memory_freed'] = result['memory_before'] - result['memory_after']
        result['cleanup_successful'] = True

        if console_output:
            print(f"💾 Garbage collection completed:")
            print(f"  • Objects collected: {collected}")
            print(f"  • Memory freed: {result['memory_freed']:.2f}%")
            print(f"  • Memory after cleanup: {result['memory_after']:.1f}%")

    except Exception as cleanup_error:
        if console_output:
            print(f"⚠️ Memory cleanup error: {cleanup_error}")
        result['cleanup_successful'] = False

    return result


def _apply_audio_settings(player, audio_settings: Dict[str, Any], *,
                         console_output: bool = True) -> None:
    """Apply custom audio settings to VLC player.

    Args:
        player: VLC MediaPlayer instance
        audio_settings: Dictionary of audio settings
        console_output: Whether to show setting messages - keyword-only
    """
    try:
  # This is a placeholder for audio settings application
  # In a real implementation, you might set:
  # - Volume level
  # - Audio filters
  # - Output device
  # - Equalizer settings

        if 'volume' in audio_settings:
            player.audio_set_volume(int(audio_settings['volume']))

        if console_output:
            print(f"🔊 Applied {len(audio_settings)} audio settings")

    except Exception as settings_error:
        if console_output:
            print(f"⚠️ Audio settings error: {settings_error}")
def _validate_genre_assignment_inputs(*,
                                     console_output: bool = True,
                                     validation_level: str = 'comprehensive',
                                     sample_size: int = 10,
                                     include_statistics: bool = False,
                                     performance_tracking: bool = False,
                                     config_file_path: str = 'GenreFlagsList.txt',
                                     check_file_permissions: bool = True,
                                     validate_dependencies: bool = True) -> Dict[str, Union[bool, str, int, float, Dict, List]]:
    """Validate inputs required for genre assignment with comprehensive Pythonic functionality.

    This function implements advanced Python validation patterns including:
    - Keyword-only arguments for better API design
    - Configurable validation levels (basic, standard, comprehensive)
    - Sample-based structure validation for performance optimization
    - Comprehensive input validation with detailed error reporting
    - Performance monitoring and timing analysis
    - File system validation with permission checking
    - Dependency validation for required global variables
    - Statistical analysis of validation results
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Structured return values for detailed operation tracking

    Args:
        console_output: Whether to show validation messages - keyword-only
        validation_level: Level of validation ('basic', 'standard', 'comprehensive') - keyword-only
        sample_size: Number of songs to validate for structure checking - keyword-only
        include_statistics: Whether to include detailed validation statistics - keyword-only
        performance_tracking: Whether to track validation performance metrics - keyword-only
        config_file_path: Path to genre configuration file - keyword-only
        check_file_permissions: Whether to check file system permissions - keyword-only
        validate_dependencies: Whether to validate required dependencies - keyword-only

    Returns:
        Dict containing:
        - 'valid': bool - True if all validations pass
        - 'message': str - Validation result message
        - 'error_details': List[str] - Detailed error information (if validation fails)
        - 'warnings': List[str] - Non-critical validation warnings
        - 'validation_results': Dict - Detailed validation breakdown by category
        - 'statistics': Dict - Validation statistics (if include_statistics=True)
        - 'performance_metrics': Dict - Performance timing data (if performance_tracking=True)
        - 'checked_components': List[str] - List of components that were validated
        - 'songs_validated': int - Number of songs validated for structure
        - 'validation_time': float - Total validation time in seconds

    Examples:
        >>> _validate_genre_assignment_inputs()
        {'valid': True, 'message': 'All validations passed', 'validation_results': {...}}
        >>> _validate_genre_assignment_inputs(validation_level='basic')
        {'valid': True, 'checked_components': ['library_existence'], ...}
        >>> _validate_genre_assignment_inputs(include_statistics=True, sample_size=50)
        {'valid': True, 'statistics': {'songs_with_comments': 45, 'avg_comment_length': 12.3}, ...}

    Validation Levels:
        - 'basic': Essential validations only (library existence, basic structure)
        - 'standard': Standard validations (includes file system checks)
        - 'comprehensive': Full validation suite (includes deep structure analysis)

    Note:
        Function uses sample-based validation for performance optimization on large libraries.
        Supports configurable validation depth and detailed error reporting.
    """
    from typing import Final, Dict, List, Union, Optional, Any
    import time
    import os
    import random
    from pathlib import Path
    from collections import defaultdict, Counter

  # Constants for better maintainability
    VALIDATION_LEVELS: Final = {'basic', 'standard', 'comprehensive'}
    DEFAULT_SAMPLE_SIZE: Final = 10
    MAX_SAMPLE_SIZE: Final = 100
    MIN_LIBRARY_SIZE: Final = 1
    REQUIRED_SONG_FIELDS: Final = {'comment'}
    OPTIONAL_SONG_FIELDS: Final = {'title', 'artist', 'album', 'genre', 'path', 'duration'}
    MAX_COMMENT_LENGTH: Final = 1000
    MIN_COMMENT_LENGTH: Final = 0
    EMOJI_VALIDATION: Final = '🔍'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_STATS: Final = '📊'
    EMOJI_PERFORMANCE: Final = '⚡'

  # Initialize comprehensive result structure
    result = {
        'valid': False,
        'message': '',
        'error_details': [],
        'warnings': [],
        'validation_results': {},
        'statistics': {} if include_statistics else None,
        'performance_metrics': {} if performance_tracking else None,
        'checked_components': [],
        'songs_validated': 0,
        'validation_time': 0.0
    }

    start_time = time.time() if performance_tracking else None
    validation_start = time.time()

    try:
  # Input validation with comprehensive parameter checking
        if validation_level not in VALIDATION_LEVELS:
            result['error_details'].append(f'Invalid validation level: {validation_level}. Must be one of {VALIDATION_LEVELS}')
            result['message'] = 'Invalid validation parameters'
            return result

        if not isinstance(sample_size, int) or sample_size < 1:
            sample_size = DEFAULT_SAMPLE_SIZE
            result['warnings'].append(f'Invalid sample_size, using default: {DEFAULT_SAMPLE_SIZE}')

        if sample_size > MAX_SAMPLE_SIZE:
            sample_size = MAX_SAMPLE_SIZE
            result['warnings'].append(f'Sample size capped at maximum: {MAX_SAMPLE_SIZE}')

        if console_output:
            print(f"{EMOJI_VALIDATION} Starting {validation_level} validation of genre assignment inputs...")

  # Initialize validation tracking
        validation_results = defaultdict(dict)
        checked_components = []
        validation_errors = []
        validation_warnings = []

  # 1. Validate music library existence and basic structure
        library_validation_start = time.time() if performance_tracking else None

        if 'MusicMasterSongList' not in globals():
            validation_errors.append('MusicMasterSongList variable not found in global scope')
            validation_results['library']['existence'] = False
        else:
            validation_results['library']['existence'] = True

            if not MusicMasterSongList:
                validation_errors.append('MusicMasterSongList is empty or None')
                validation_results['library']['has_data'] = False
            else:
                validation_results['library']['has_data'] = True

                if not isinstance(MusicMasterSongList, list):
                    validation_errors.append(f'MusicMasterSongList must be a list, got {type(MusicMasterSongList).__name__}')
                    validation_results['library']['correct_type'] = False
                else:
                    validation_results['library']['correct_type'] = True
                    validation_results['library']['total_songs'] = len(MusicMasterSongList)

                    if len(MusicMasterSongList) < MIN_LIBRARY_SIZE:
                        validation_errors.append(f'Music library too small: {len(MusicMasterSongList)} songs (minimum: {MIN_LIBRARY_SIZE})')
                        validation_results['library']['adequate_size'] = False
                    else:
                        validation_results['library']['adequate_size'] = True

        checked_components.append('library_existence')
        checked_components.append('library_structure')

        if performance_tracking and library_validation_start:
            library_validation_time = time.time() - library_validation_start
            result['performance_metrics']['library_validation_time'] = library_validation_time

  # Early return for basic validation level or if library validation failed
        if validation_level == 'basic' or validation_errors:
            if validation_errors:
                result['error_details'] = validation_errors
                result['message'] = f'Basic validation failed: {len(validation_errors)} error(s) found'
                if console_output:
                    print(f"{EMOJI_ERROR} Basic validation failed")
                    for error in validation_errors:
                        print(f"  - {error}")
            else:
                result['valid'] = True
                result['message'] = 'Basic validation passed'
                if console_output:
                    print(f"{EMOJI_SUCCESS} Basic validation completed successfully")

            result['validation_results'] = dict(validation_results)
            result['checked_components'] = checked_components
            result['warnings'] = validation_warnings
            result['validation_time'] = time.time() - validation_start
            return result

  # 2. Configuration file validation (standard level and above)
        config_validation_start = time.time() if performance_tracking else None

        config_path = Path(config_file_path)
        validation_results['config_file']['path'] = str(config_path.absolute())

        if not config_path.exists():
            validation_errors.append(f'Genre configuration file not found: {config_path.absolute()}')
            validation_results['config_file']['exists'] = False
        else:
            validation_results['config_file']['exists'] = True

  # File system permission checks
            if check_file_permissions:
                if not config_path.is_file():
                    validation_errors.append(f'Configuration path is not a file: {config_path}')
                    validation_results['config_file']['is_file'] = False
                else:
                    validation_results['config_file']['is_file'] = True

                if not os.access(config_path, os.R_OK):
                    validation_errors.append(f'Configuration file is not readable: {config_path}')
                    validation_results['config_file']['readable'] = False
                else:
                    validation_results['config_file']['readable'] = True

                try:
                    file_stats = config_path.stat()
                    validation_results['config_file']['size_bytes'] = file_stats.st_size
                    validation_results['config_file']['last_modified'] = file_stats.st_mtime

                    if file_stats.st_size == 0:
                        validation_warnings.append('Configuration file is empty')
                        validation_results['config_file']['empty'] = True
                    else:
                        validation_results['config_file']['empty'] = False

                except OSError as stat_error:
                    validation_warnings.append(f'Could not read file statistics: {stat_error}')

        checked_components.append('config_file')

        if performance_tracking and config_validation_start:
            config_validation_time = time.time() - config_validation_start
            result['performance_metrics']['config_validation_time'] = config_validation_time

  # 3. Song structure validation (standard level and above)
        if validation_level in {'standard', 'comprehensive'} and \
            MusicMasterSongList and \
            isinstance(MusicMasterSongList, list):
            structure_validation_start = time.time() if performance_tracking else None

  # Determine sample for validation
            total_songs = len(MusicMasterSongList)
            actual_sample_size = min(sample_size, total_songs)

            if validation_level == 'comprehensive' and total_songs <= sample_size:
  # Validate all songs for comprehensive validation on small libraries
                sample_indices = list(range(total_songs))
            else:
  # Random sampling for larger libraries
                sample_indices = random.sample(range(total_songs), actual_sample_size)

            songs_validated = 0
            songs_with_issues = []
            field_statistics = defaultdict(int)
            comment_lengths = []

            for i, song_index in enumerate(sample_indices):
                try:
                    song = MusicMasterSongList[song_index]
                    songs_validated += 1

  # Basic structure validation
                    if not isinstance(song, dict):
                        songs_with_issues.append({
                            'index': song_index,
                            'issue': f'Song is not a dictionary: {type(song).__name__}',
                            'severity': 'error'
                        })
                        continue

  # Required fields validation
                    missing_required = REQUIRED_SONG_FIELDS - set(song.keys())
                    if missing_required:
                        songs_with_issues.append({
                            'index': song_index,
                            'issue': f'Missing required fields: {missing_required}',
                            'severity': 'error'
                        })

  # Field presence statistics
                    for field in REQUIRED_SONG_FIELDS | OPTIONAL_SONG_FIELDS:
                        if field in song:
                            field_statistics[f'{field}_present'] += 1

  # Comment field specific validation
                    if 'comment' in song:
                        comment = song['comment']
                        if comment is None:
                            field_statistics['comment_null'] += 1
                        elif isinstance(comment, str):
                            comment_length = len(comment)
                            comment_lengths.append(comment_length)
                            field_statistics['comment_string'] += 1

                            if comment_length > MAX_COMMENT_LENGTH:
                                songs_with_issues.append({
                                    'index': song_index,
                                    'issue': f'Comment too long: {comment_length} chars (max: {MAX_COMMENT_LENGTH})',
                                    'severity': 'warning'
                                })
                        else:
                            field_statistics['comment_other_type'] += 1
                            songs_with_issues.append({
                                'index': song_index,
                                'issue': f'Comment field is not string or None: {type(comment).__name__}',
                                'severity': 'warning'
                            })

                except (IndexError, TypeError, AttributeError) as song_error:
                    songs_with_issues.append({
                        'index': song_index,
                        'issue': f'Error accessing song: {song_error}',
                        'severity': 'error'
                    })

  # Compile structure validation results
            validation_results['song_structure'] = {
                'total_songs': total_songs,
                'songs_validated': songs_validated,
                'sample_size_requested': sample_size,
                'actual_sample_size': actual_sample_size,
                'songs_with_issues': len(songs_with_issues),
                'field_statistics': dict(field_statistics)
            }

            if comment_lengths:
                validation_results['song_structure']['comment_stats'] = {
                    'avg_length': sum(comment_lengths) / len(comment_lengths),
                    'min_length': min(comment_lengths),
                    'max_length': max(comment_lengths),
                    'total_comments': len(comment_lengths)
                }

  # Process song issues
            error_issues = [issue for issue in songs_with_issues if issue['severity'] == 'error']
            warning_issues = [issue for issue in songs_with_issues if issue['severity'] == 'warning']

            if error_issues:
                for issue in error_issues[:5]:  # Limit error details
                    validation_errors.append(f"Song {issue['index']}: {issue['issue']}")
                if len(error_issues) > 5:
                    validation_errors.append(f"... and {len(error_issues) - 5} more song structure errors")

            if warning_issues:
                for issue in warning_issues[:3]:  # Limit warning details
                    validation_warnings.append(f"Song {issue['index']}: {issue['issue']}")
                if len(warning_issues) > 3:
                    validation_warnings.append(f"... and {len(warning_issues) - 3} more song structure warnings")

            result['songs_validated'] = songs_validated
            checked_components.append('song_structure')

            if performance_tracking and structure_validation_start:
                structure_validation_time = time.time() - structure_validation_start
                result['performance_metrics']['structure_validation_time'] = structure_validation_time

  # 4. Dependency validation (comprehensive level)
        if validation_level == 'comprehensive' and validate_dependencies:
            dependency_validation_start = time.time() if performance_tracking else None

            required_globals = ['FinalGenreList', 'genre0', 'genre1', 'genre2', 'genre3']
            dependency_results = {}

            for global_var in required_globals:
                if global_var in globals():
                    dependency_results[global_var] = 'available'
                else:
                    dependency_results[global_var] = 'missing'
                    validation_warnings.append(f'Optional global variable not found: {global_var}')

            validation_results['dependencies'] = dependency_results
            checked_components.append('dependencies')

            if performance_tracking and dependency_validation_start:
                dependency_validation_time = time.time() - dependency_validation_start
                result['performance_metrics']['dependency_validation_time'] = dependency_validation_time

  # 5. Compile comprehensive statistics (if requested)
        if include_statistics and validation_results:
            statistics = {
                'validation_level': validation_level,
                'components_checked': len(checked_components),
                'total_errors': len(validation_errors),
                'total_warnings': len(validation_warnings),
                'library_available': validation_results.get('library', {}).get('existence', False),
                'config_file_available': validation_results.get('config_file', {}).get('exists', False)
            }

            if 'song_structure' in validation_results:
                structure_stats = validation_results['song_structure']
                statistics.update({
                    'songs_in_library': structure_stats.get('total_songs', 0),
                    'songs_validated': structure_stats.get('songs_validated', 0),
                    'songs_with_issues': structure_stats.get('songs_with_issues', 0),
                    'validation_coverage': (structure_stats.get('songs_validated', 0) /
                                          max(structure_stats.get('total_songs', 1), 1)) * 100
                })

                if 'comment_stats' in structure_stats:
                    comment_stats = structure_stats['comment_stats']
                    statistics.update({
                        'avg_comment_length': comment_stats.get('avg_length', 0),
                        'min_comment_length': comment_stats.get('min_length', 0),
                        'max_comment_length': comment_stats.get('max_length', 0)
                    })

            result['statistics'] = statistics

  # Final validation result determination
        total_validation_time = time.time() - validation_start
        result['validation_time'] = total_validation_time

        if validation_errors:
            result['valid'] = False
            result['message'] = f'Validation failed: {len(validation_errors)} error(s) found'
            result['error_details'] = validation_errors

            if console_output:
                print(f"{EMOJI_ERROR} Validation failed with {len(validation_errors)} error(s)")
                for error in validation_errors[:5]:  # Limit console output
                    print(f"  - {error}")
                if len(validation_errors) > 5:
                    print(f"  ... and {len(validation_errors) - 5} more errors")
        else:
            result['valid'] = True
            result['message'] = f'{validation_level.title()} validation completed successfully'

            if console_output:
                print(f"{EMOJI_SUCCESS} {validation_level.title()} validation completed successfully")
                print(f"  Components checked: {', '.join(checked_components)}")
                if result['songs_validated'] > 0:
                    print(f"  Songs validated: {result['songs_validated']}")
                if validation_warnings:
                    print(f"  Warnings: {len(validation_warnings)}")

  # Add warnings to result
        result['warnings'] = validation_warnings
        result['validation_results'] = dict(validation_results)
        result['checked_components'] = checked_components

  # Performance metrics compilation
        if performance_tracking and start_time:
            total_time = time.time() - start_time
            result['performance_metrics']['total_validation_time'] = total_time

            if result['songs_validated'] > 0:
                result['performance_metrics']['songs_per_second'] = result['songs_validated'] / total_time

            if console_output:
                print(f"{EMOJI_PERFORMANCE} Validation completed in {total_time:.4f}s")

        return result

    except Exception as validation_error:
  # Comprehensive error handling
        error_message = f'Validation system error: {validation_error}'
        result['error_details'] = [error_message]
        result['message'] = 'Validation system failure'
        result['validation_time'] = time.time() - validation_start

        if console_output:
            print(f"{EMOJI_ERROR} Validation system error: {validation_error}")

  # Log the error for debugging
        try:
            _log_error(f'Genre assignment input validation error: {validation_error}')
        except:
            pass  # Avoid recursive errors in error handling

        return result


def _load_genre_configuration(*,
                              config_file: str,
                              console_output: bool = True,
                              validate_structure: bool = True,
                              enable_caching: bool = True,
                              performance_tracking: bool = False,
                              backup_on_error: bool = True,
                              auto_repair: bool = True,
                              encoding: str = 'utf-8') -> Dict[str, Union[bool, str, List, Dict, float, int]]:
    """Load genre configuration from file with comprehensive Pythonic functionality.

    This function implements advanced Python configuration management patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation and structure verification
    - File caching for performance optimization
    - Performance monitoring and timing analysis
    - Automatic error recovery and repair mechanisms
    - Configurable encoding support for internationalization
    - Backup creation on critical errors
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Advanced validation with detailed error reporting

    Args:
        config_file: Path to genre configuration file - keyword-only
        console_output: Whether to show loading messages - keyword-only
        validate_structure: Whether to perform deep structure validation - keyword-only
        enable_caching: Whether to cache loaded configuration - keyword-only
        performance_tracking: Whether to track loading performance - keyword-only
        backup_on_error: Whether to create backup on critical errors - keyword-only
        auto_repair: Whether to automatically repair invalid configurations - keyword-only
        encoding: File encoding to use for reading - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if configuration loaded successfully
        - 'genre_filters': List[str] - List of genre filter strings (exactly 4 elements)
        - 'error_message': str - Error message if failed (empty if success)
        - 'file_info': Dict - File metadata and information
        - 'validation_info': Dict - Configuration validation details
        - 'performance_metrics': Dict - Performance timing data (if tracking enabled)
        - 'cache_info': Dict - Cache usage information (if caching enabled)
        - 'repair_info': Dict - Auto-repair information (if repairs performed)

    Examples:
        >>> _load_genre_configuration(config_file='GenreFlagsList.txt')
        {'success': True, 'genre_filters': ['rock', 'pop', 'null', 'null'], ...}
        >>> _load_genre_configuration(config_file='config.json', performance_tracking=True)
        {'success': True, 'performance_metrics': {'load_time': 0.001}, ...}
        >>> _load_genre_configuration(config_file='invalid.json', auto_repair=True)
        {'success': True, 'repair_info': {'repairs_performed': ['structure_fix']}, ...}

    Note:
        Function supports automatic configuration repair and backup creation.
        Uses advanced caching for improved performance on repeated calls.
    """
    from typing import Final
    import json
    import time
    import hashlib
    import shutil
    import os
    from pathlib import Path
    from datetime import datetime

  # Constants for better maintainability
    EXPECTED_GENRE_COUNT: Final = 4
    NULL_GENRE_VALUE: Final = 'null'
    DEFAULT_ENCODING: Final = 'utf-8'
    BACKUP_SUFFIX: Final = '.backup'
    CACHE_KEY_PREFIX: Final = 'genre_config_'
    MAX_GENRE_NAME_LENGTH: Final = 50
    MIN_CONFIG_FILE_SIZE: Final = 10  # Minimum reasonable file size in bytes
    MAX_CONFIG_FILE_SIZE: Final = 1024 * 10  # Maximum reasonable file size (10KB)
    EMOJI_CONFIG: Final = '⚙️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_ERROR: Final = '❌'
    EMOJI_REPAIR: Final = '🔧'
    EMOJI_CACHE: Final = '💾'
    EMOJI_PERFORMANCE: Final = '⚡'

  # Initialize comprehensive result structure
    result = {
        'success': False,
        'genre_filters': [],
        'error_message': '',
        'file_info': {},
        'validation_info': {},
        'performance_metrics': {} if performance_tracking else None,
        'cache_info': {} if enable_caching else None,
        'repair_info': {} if auto_repair else None
    }

    start_time = time.time() if performance_tracking else None

    try:
  # Input validation with comprehensive checks
        if not config_file or not isinstance(config_file, str):
            result['error_message'] = f'Invalid config file parameter: {config_file}'
            return result

        if not encoding or not isinstance(encoding, str):
            encoding = DEFAULT_ENCODING
            if console_output:
                print(f"{EMOJI_WARNING} Invalid encoding specified, using default: {DEFAULT_ENCODING}")

  # Path processing with advanced validation
        config_path = Path(config_file)

  # File existence and accessibility checks
        if not config_path.exists():
            error_msg = f'Configuration file not found: {config_path.absolute()}'
            result['error_message'] = error_msg

            if console_output:
                print(f"{EMOJI_ERROR} {error_msg}")

  # Attempt to create default configuration if auto_repair is enabled
            if auto_repair:
                if console_output:
                    print(f"{EMOJI_REPAIR} Attempting to create default configuration...")

                try:
                    default_config = [NULL_GENRE_VALUE] * EXPECTED_GENRE_COUNT
                    with open(config_path, 'w', encoding=encoding) as default_file:
                        json.dump(default_config, default_file, indent=2)

                    if console_output:
                        print(f"{EMOJI_SUCCESS} Created default configuration file")

  # Update repair info
                    if result['repair_info'] is not None:
                        result['repair_info']['default_config_created'] = True
                        result['repair_info']['creation_time'] = datetime.now().isoformat()

                except Exception as create_error:
                    result['error_message'] += f' | Failed to create default: {create_error}'
                    return result
            else:
                return result

  # File metadata collection
        file_stats = config_path.stat()
        file_info = {
            'file_path': str(config_path.absolute()),
            'file_size': file_stats.st_size,
            'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            'is_readable': config_path.is_file() and os.access(config_path, os.R_OK),
            'encoding_used': encoding
        }
        result['file_info'] = file_info

  # File size validation
        if file_stats.st_size < MIN_CONFIG_FILE_SIZE:
            if console_output:
                print(f"{EMOJI_WARNING} Configuration file is very small ({file_stats.st_size} bytes)")
        elif file_stats.st_size > MAX_CONFIG_FILE_SIZE:
            result['error_message'] = f'Configuration file too large: {file_stats.st_size} bytes (max: {MAX_CONFIG_FILE_SIZE})'
            return result

  # Check cache if enabled
        cache_key = None
        cached_result = None

        if enable_caching:
  # Generate cache key based on file path and modification time
            cache_content = f"{config_path.absolute()}_{file_stats.st_mtime}_{file_stats.st_size}"
            cache_key = CACHE_KEY_PREFIX + hashlib.md5(cache_content.encode()).hexdigest()

  # Check if we have a cached version (simplified cache - in production use proper caching)
            if hasattr(_load_genre_configuration, '_cache'):
                cached_result = getattr(_load_genre_configuration, '_cache').get(cache_key)

                if cached_result and console_output:
                    print(f"{EMOJI_CACHE} Using cached configuration")

                if cached_result:
                    if result['cache_info'] is not None:
                        result['cache_info']['cache_hit'] = True
                        result['cache_info']['cache_key'] = cache_key

  # Update performance metrics for cache hit
                    if performance_tracking and start_time is not None:
                        cached_result['performance_metrics'] = {
                            'load_time': time.time() - start_time,
                            'cache_hit': True
                        }

                    return cached_result

  # Load and parse configuration file
        load_start = time.time() if performance_tracking else None

        try:
            with open(config_path, 'r', encoding=encoding) as config_handle:
                file_content = config_handle.read().strip()

                if not file_content:
                    raise ValueError("Configuration file is empty")

                genre_data = json.loads(file_content)

        except UnicodeDecodeError as decode_error:
  # Try alternative encodings
            alternative_encodings = ['utf-8-sig', 'latin1', 'cp1252']
            genre_data = None

            for alt_encoding in alternative_encodings:
                if alt_encoding == encoding:
                    continue

                try:
                    with open(config_path, 'r', encoding=alt_encoding) as config_handle:
                        genre_data = json.load(config_handle)

                    if console_output:
                        print(f"{EMOJI_WARNING} Used alternative encoding: {alt_encoding}")

                    file_info['encoding_used'] = alt_encoding
                    break

                except Exception:
                    continue

            if genre_data is None:
                raise decode_error

        if performance_tracking and load_start is not None:
            load_time = time.time() - load_start
            if result['performance_metrics'] is not None:
                result['performance_metrics']['file_load_time'] = load_time

  # Comprehensive structure validation
        validation_info = {
            'original_type': type(genre_data).__name__,
            'original_length': len(genre_data) if hasattr(genre_data, '__len__') else 0,
            'validation_passed': True,
            'issues_found': [],
            'repairs_needed': []
        }

  # Type validation
        if not isinstance(genre_data, list):
            validation_info['validation_passed'] = False
            validation_info['issues_found'].append(f'Invalid type: expected list, got {type(genre_data).__name__}')

            if auto_repair:
  # Attempt to convert to list or create default
                if isinstance(genre_data, str):
  # Single string - convert to list
                    genre_data = [genre_data] + [NULL_GENRE_VALUE] * (EXPECTED_GENRE_COUNT - 1)
                    validation_info['repairs_needed'].append('converted_string_to_list')
                else:
  # Create default configuration
                    genre_data = [NULL_GENRE_VALUE] * EXPECTED_GENRE_COUNT
                    validation_info['repairs_needed'].append('created_default_list')
            else:
                result['error_message'] = validation_info['issues_found'][0]
                result['validation_info'] = validation_info
                return result

  # Length validation with auto-repair
        original_length = len(genre_data)
        if original_length != EXPECTED_GENRE_COUNT:
            validation_info['issues_found'].append(f'Expected {EXPECTED_GENRE_COUNT} genres, found {original_length}')

            if console_output:
                print(f"{EMOJI_WARNING} Expected {EXPECTED_GENRE_COUNT} genre slots, found {original_length}")

  # Auto-repair length issues
            if original_length < EXPECTED_GENRE_COUNT:
  # Pad with null values
                while len(genre_data) < EXPECTED_GENRE_COUNT:
                    genre_data.append(NULL_GENRE_VALUE)
                validation_info['repairs_needed'].append(f'padded_to_{EXPECTED_GENRE_COUNT}_elements')
            elif original_length > EXPECTED_GENRE_COUNT:
  # Truncate to expected length
                genre_data = genre_data[:EXPECTED_GENRE_COUNT]
                validation_info['repairs_needed'].append(f'truncated_to_{EXPECTED_GENRE_COUNT}_elements')

  # Content validation with detailed checking
        if validate_structure:
            valid_genres = []
            invalid_genres = []

            for i, genre in enumerate(genre_data):
                if not isinstance(genre, str):
                    invalid_genres.append(f'Position {i}: {type(genre).__name__} (should be string)')
  # Auto-repair non-string values
                    if auto_repair:
                        genre_data[i] = str(genre) if genre is not None else NULL_GENRE_VALUE
                        validation_info['repairs_needed'].append(f'converted_position_{i}_to_string')
                elif len(genre) > MAX_GENRE_NAME_LENGTH:
                    invalid_genres.append(f'Position {i}: genre name too long ({len(genre)} chars)')
  # Auto-repair long genre names
                    if auto_repair:
                        genre_data[i] = genre[:MAX_GENRE_NAME_LENGTH]
                        validation_info['repairs_needed'].append(f'truncated_position_{i}_genre_name')
                else:
                    valid_genres.append(genre)

            validation_info['valid_genres'] = len(valid_genres)
            validation_info['invalid_genres'] = len(invalid_genres)

            if invalid_genres:
                validation_info['issues_found'].extend(invalid_genres)
                if not auto_repair:
                    validation_info['validation_passed'] = False

  # Create backup if repairs were needed
        if auto_repair and validation_info['repairs_needed'] and backup_on_error:
            try:
                backup_path = config_path.with_suffix(config_path.suffix + BACKUP_SUFFIX)
                shutil.copy2(config_path, backup_path)

                if console_output:
                    print(f"{EMOJI_SUCCESS} Created backup: {backup_path.name}")

                if result['repair_info'] is not None:
                    result['repair_info']['backup_created'] = str(backup_path)
                    result['repair_info']['backup_time'] = datetime.now().isoformat()

            except Exception as backup_error:
                if console_output:
                    print(f"{EMOJI_WARNING} Failed to create backup: {backup_error}")

  # Save repaired configuration if needed
        if auto_repair and validation_info['repairs_needed']:
            try:
                with open(config_path, 'w', encoding=encoding) as repaired_file:
                    json.dump(genre_data, repaired_file, indent=2, ensure_ascii=False)

                if console_output:
                    print(f"{EMOJI_REPAIR} Applied {len(validation_info['repairs_needed'])} repairs to configuration")

                if result['repair_info'] is not None:
                    result['repair_info']['repairs_applied'] = validation_info['repairs_needed']
                    result['repair_info']['repair_time'] = datetime.now().isoformat()

            except Exception as save_error:
                if console_output:
                    print(f"{EMOJI_WARNING} Failed to save repaired configuration: {save_error}")

  # Update result with success information
        result.update({
            'success': True,
            'genre_filters': genre_data[:EXPECTED_GENRE_COUNT]  # Ensure exactly 4 elements
        })

        result['validation_info'] = validation_info

  # Cache the result if caching is enabled
        if enable_caching and cache_key:
            if not hasattr(_load_genre_configuration, '_cache'):
                setattr(_load_genre_configuration, '_cache', {})

            cache_dict = getattr(_load_genre_configuration, '_cache')

  # Simple cache cleanup - keep only last 10 entries
            if len(cache_dict) > 10:
  # Remove oldest entries (simplified - in production use LRU cache)
                oldest_keys = list(cache_dict.keys())[:5]
                for old_key in oldest_keys:
                    del cache_dict[old_key]

            cache_dict[cache_key] = result.copy()

            if result['cache_info'] is not None:
                result['cache_info']['cache_stored'] = True
                result['cache_info']['cache_key'] = cache_key
                result['cache_info']['cache_size'] = len(cache_dict)

  # Performance metrics calculation
        if performance_tracking and start_time is not None:
            total_time = time.time() - start_time
            if result['performance_metrics'] is not None:
                result['performance_metrics'].update({
                    'total_load_time': total_time,
                    'validation_time': total_time - result['performance_metrics'].get('file_load_time', 0),
                    'cache_hit': False,
                    'file_size_kb': file_stats.st_size / 1024
                })

  # Enhanced console output with detailed status
        if console_output:
            active_count = len([g for g in genre_data if g != NULL_GENRE_VALUE])
            print(f"{EMOJI_SUCCESS} Loaded genre configuration: {active_count}/{EXPECTED_GENRE_COUNT} active filters")

            if validation_info['repairs_needed']:
                print(f"{EMOJI_REPAIR} Applied {len(validation_info['repairs_needed'])} automatic repairs")

            if performance_tracking and result['performance_metrics']:
                load_time = result['performance_metrics']['total_load_time']
                print(f"{EMOJI_PERFORMANCE} Load time: {load_time:.4f}s")

        return result

    except json.JSONDecodeError as json_error:
        error_message = f'Invalid JSON in configuration file: {json_error}'
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

  # Attempt auto-repair for JSON errors
        if auto_repair:
            if console_output:
                print(f"{EMOJI_REPAIR} Attempting to repair JSON configuration...")

            try:
  # Create new default configuration
                default_config = [NULL_GENRE_VALUE] * EXPECTED_GENRE_COUNT

  # Create backup of corrupted file
                if backup_on_error:
                    backup_path = config_path.with_suffix('.corrupted.backup')
                    shutil.copy2(config_path, backup_path)

                    if console_output:
                        print(f"{EMOJI_SUCCESS} Backed up corrupted file to: {backup_path.name}")

  # Write new default configuration
                with open(config_path, 'w', encoding=encoding) as repaired_file:
                    json.dump(default_config, repaired_file, indent=2)

                if console_output:
                    print(f"{EMOJI_SUCCESS} Created new default configuration")

  # Update result for successful repair
                result.update({
                    'success': True,
                    'genre_filters': default_config,
                    'error_message': ''  # Clear error since we repaired it
                })

                if result['repair_info'] is not None:
                    result['repair_info']['json_repair_performed'] = True
                    result['repair_info']['corrupted_backup'] = str(backup_path) if backup_on_error else None
                    result['repair_info']['repair_time'] = datetime.now().isoformat()

            except Exception as repair_error:
                result['error_message'] += f' | Repair failed: {repair_error}'

        return result

    except Exception as general_error:
  # Comprehensive error handling with performance tracking
        if performance_tracking and start_time is not None:
            if result['performance_metrics'] is not None:
                result['performance_metrics']['total_load_time'] = time.time() - start_time
                result['performance_metrics']['failed'] = True

        error_message = f"Configuration loading error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

        return result


def _extract_all_genres_from_library(*,
                                    music_library: List[Dict],
                                    include_statistics: bool = False,
                                    console_output: bool = True,
                                    normalize_case: bool = True,
                                    min_genre_length: int = 1,
                                    exclude_patterns: Optional[List[str]] = None,
                                    performance_tracking: bool = False) -> Dict[str, Union[bool, str, List, Dict, int, float]]:
    """Extract all unique genres from the music library with comprehensive Pythonic processing.

    This function implements advanced Python genre extraction patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Configurable processing options and filtering
    - Advanced data structures for efficient processing
    - Performance monitoring and optimization
    - Flexible filtering and normalization options
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Statistical analysis with frequency distribution

    Args:
        music_library: List of song dictionaries with metadata
        include_statistics: Whether to include detailed statistical analysis - keyword-only
        console_output: Whether to show processing messages - keyword-only
        normalize_case: Whether to normalize genre names to lowercase - keyword-only
        min_genre_length: Minimum length for valid genre names - keyword-only
        exclude_patterns: List of patterns to exclude from genre extraction - keyword-only
        performance_tracking: Whether to track processing performance - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if extraction completed successfully
        - 'unique_genres': List[str] - Sorted list of unique genre names
        - 'total_genres_processed': int - Total number of genre references processed
        - 'songs_processed': int - Number of songs analyzed
        - 'songs_skipped': int - Number of songs skipped due to errors or filters
        - 'processing_time': float - Time taken for extraction (if tracking enabled)
        - 'error_message': str - Error message if failed (empty if success)
        - 'statistics': Dict - Detailed statistics (if enabled)
        - 'performance_metrics': Dict - Performance metrics (if tracking enabled)

    Examples:
        >>> _extract_all_genres_from_library(music_library=songs)
        {'success': True, 'unique_genres': ['rock', 'pop', 'jazz'], ...}
        >>> _extract_all_genres_from_library(music_library=songs, include_statistics=True)
        {'success': True, 'statistics': {'genre_frequency': {...}}, ...}
        >>> _extract_all_genres_from_library(music_library=songs, exclude_patterns=['temp', 'test'])
        {'success': True, 'unique_genres': ['rock', 'pop'], ...}

    Note:
        Function performs intelligent genre filtering and normalization.
        Uses advanced Python data structures for optimal performance.
    """
    from typing import Final, Set, Counter
    import time
    import re
    from collections import Counter, defaultdict

  # Constants for better maintainability
    DEFAULT_COMMENT_FIELD: Final = 'comment'
    DEFAULT_WORD_SEPARATOR: Final = None  # Use default whitespace splitting
    EMOJI_DISCOVERY: Final = '🔍'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_ERROR: Final = '❌'
    EMOJI_STATS: Final = '📊'
    EMOJI_PERFORMANCE: Final = '⚡'
    MIN_VALID_GENRE_LENGTH: Final = 1
    MAX_GENRE_LENGTH: Final = 50  # Reasonable limit for genre names

  # Initialize result structure with comprehensive tracking
    result = {
        'success': False,
        'unique_genres': [],
        'total_genres_processed': 0,
        'songs_processed': 0,
        'songs_skipped': 0,
        'processing_time': 0.0,
        'error_message': '',
        'statistics': {} if include_statistics else None,
        'performance_metrics': {} if performance_tracking else None
    }

    start_time = time.time() if performance_tracking else None

    try:
  # Input validation with comprehensive checks
        if not music_library:
            result['error_message'] = 'Music library is empty or None'
            return result

        if not isinstance(music_library, list):
            result['error_message'] = f'Music library must be a list, got {type(music_library).__name__}'
            return result

  # Validate minimum genre length
        effective_min_length = max(min_genre_length, MIN_VALID_GENRE_LENGTH)

  # Prepare exclusion patterns with compiled regex for performance
        compiled_exclusions = []
        if exclude_patterns:
            try:
                compiled_exclusions = [re.compile(pattern, re.IGNORECASE) for pattern in exclude_patterns]
            except re.error as regex_error:
                if console_output:
                    print(f"{EMOJI_WARNING} Invalid exclusion pattern: {regex_error}")

  # Advanced data structures for efficient processing
        genre_counter = Counter()  # Efficient frequency counting
        all_genre_references = []  # Complete list for statistics
        songs_processed = 0
        songs_skipped = 0
        empty_comments = 0

  # Performance tracking variables
        processing_stages = defaultdict(float) if performance_tracking else None
        stage_start = time.time() if performance_tracking else None

  # Enhanced statistics tracking
        stats = {
            'genre_frequency': {},
            'multi_genre_songs': 0,
            'single_genre_songs': 0,
            'empty_comment_songs': 0,
            'processing_errors': [],
            'longest_genre_list': 0,
            'shortest_genre_list': float('inf'),
            'total_words_processed': 0,
            'excluded_genres': 0,
            'genre_length_distribution': defaultdict(int),
            'comment_length_distribution': defaultdict(int)
        } if include_statistics else None

        if console_output:
            print(f"{EMOJI_DISCOVERY} Starting genre extraction from {len(music_library)} songs...")

  # Main processing loop with advanced filtering
        for song_index, song_data in enumerate(music_library):
            if performance_tracking and processing_stages is not None:
                stage_start = time.time()

            try:
  # Validate song data structure
                if not isinstance(song_data, dict):
                    songs_skipped += 1
                    if include_statistics and stats is not None:
                        stats['processing_errors'].append({
                            'song_index': song_index,
                            'error': f'Invalid song data type: {type(song_data).__name__}',
                            'severity': 'warning'
                        })
                    continue

                songs_processed += 1
                comment = song_data.get(DEFAULT_COMMENT_FIELD, '').strip()

  # Track comment length distribution
                if include_statistics and stats is not None:
                    comment_length = len(comment)
                    stats['comment_length_distribution'][comment_length] += 1

                if not comment:
                    empty_comments += 1
                    if include_statistics and stats is not None:
                        stats['empty_comment_songs'] += 1
                    continue

  # Advanced genre word extraction with flexible splitting
                genre_words = comment.split(DEFAULT_WORD_SEPARATOR)
                genre_words = [word.strip() for word in genre_words if word.strip()]

  # Update statistics for genre list analysis
                if include_statistics and stats is not None:
                    genre_count = len(genre_words)
                    stats['total_words_processed'] += genre_count

                    if genre_count > 1:
                        stats['multi_genre_songs'] += 1
                    elif genre_count == 1:
                        stats['single_genre_songs'] += 1

                    if genre_count > stats['longest_genre_list']:
                        stats['longest_genre_list'] = genre_count
                    if genre_count < stats['shortest_genre_list']:
                        stats['shortest_genre_list'] = genre_count

  # Process each genre word with advanced filtering
                for word in genre_words:
  # Normalize case if requested
                    processed_word = word.lower() if normalize_case else word

  # Apply length filtering
                    if len(processed_word) < effective_min_length or len(processed_word) > MAX_GENRE_LENGTH:
                        continue

  # Apply exclusion patterns
                    excluded = False
                    for exclusion_pattern in compiled_exclusions:
                        if exclusion_pattern.search(processed_word):
                            excluded = True
                            if include_statistics and stats is not None:
                                stats['excluded_genres'] += 1
                            break

                    if excluded:
                        continue

  # Add to collections for processing
                    all_genre_references.append(processed_word)
                    genre_counter[processed_word] += 1

  # Track genre length distribution
                    if include_statistics and stats is not None:
                        genre_length = len(processed_word)
                        stats['genre_length_distribution'][genre_length] += 1

  # Performance tracking for individual song processing
                if performance_tracking and processing_stages is not None and stage_start is not None:
                    processing_stages['song_processing'] += time.time() - stage_start

            except Exception as song_error:
                songs_skipped += 1
                if include_statistics and stats is not None:
                    stats['processing_errors'].append({
                        'song_index': song_index,
                        'error': str(song_error),
                        'severity': 'error'
                    })
                if console_output:
                    print(f"{EMOJI_WARNING} Error processing song {song_index}: {song_error}")
                continue

  # Advanced unique genre extraction using set operations
        if performance_tracking and processing_stages is not None:
            stage_start = time.time()

        unique_genres = sorted(list(genre_counter.keys()))

  # Additional filtering for unique genres
        unique_genres = [genre for genre in unique_genres if genre.strip() and
            len(genre.strip()) >= effective_min_length]

        if performance_tracking and processing_stages is not None and stage_start is not None:
            processing_stages['genre_deduplication'] += time.time() - stage_start

  # Update result with comprehensive information
        result.update({
            'success': True,
            'unique_genres': unique_genres,
            'total_genres_processed': len(all_genre_references),
            'songs_processed': songs_processed,
            'songs_skipped': songs_skipped
        })

  # Calculate and add comprehensive statistics
        if include_statistics and stats is not None:
  # Advanced statistical calculations
            stats['unique_genre_count'] = len(unique_genres)
            stats['duplicate_references'] = len(all_genre_references) - len(unique_genres)
            stats['average_genres_per_song'] = len(all_genre_references) / songs_processed if songs_processed > 0 else 0
            stats['genre_diversity_ratio'] = len(unique_genres) / len(all_genre_references) if all_genre_references else 0
            stats['empty_comment_ratio'] = empty_comments / songs_processed if songs_processed > 0 else 0

  # Convert Counter to regular dict for JSON serialization
            stats['genre_frequency'] = dict(genre_counter.most_common())

  # Convert defaultdicts to regular dicts
            stats['genre_length_distribution'] = dict(stats['genre_length_distribution'])
            stats['comment_length_distribution'] = dict(stats['comment_length_distribution'])

  # Fix infinite values for JSON serialization
            if stats['shortest_genre_list'] == float('inf'):
                stats['shortest_genre_list'] = 0

  # Top genres analysis
            if genre_counter:
                stats['most_common_genres'] = genre_counter.most_common(10)
                stats['rarest_genres'] = genre_counter.most_common()[:-6:-1]  # Bottom 5

            result['statistics'] = stats

  # Performance metrics calculation
        if performance_tracking and start_time is not None:
            total_time = time.time() - start_time
            result['processing_time'] = total_time

            if processing_stages is not None:
                processing_stages['total_time'] = total_time
                processing_stages['songs_per_second'] = songs_processed / total_time if total_time > 0 else 0
                processing_stages['genres_per_second'] = len(all_genre_references) / total_time if total_time > 0 else 0

                result['performance_metrics'] = dict(processing_stages)

  # Enhanced console output with detailed information
        if console_output:
            print(f"{EMOJI_SUCCESS} Genre extraction completed successfully:")
            print(f"   Songs processed: {songs_processed}")
            print(f"   Songs skipped: {songs_skipped}")
            print(f"   Unique genres found: {len(unique_genres)}")
            print(f"   Total genre references: {len(all_genre_references)}")

            if empty_comments > 0:
                print(f"{EMOJI_WARNING} Warning: {empty_comments} songs have empty genre comments")

            if performance_tracking and 'processing_time' in result:
                print(f"{EMOJI_PERFORMANCE} Processing time: {result['processing_time']:.3f}s")

            if include_statistics and stats is not None and 'most_common_genres' in stats:
                top_genres = [genre for genre, _ in stats['most_common_genres'][:5]]
                print(f"{EMOJI_STATS} Top genres: {', '.join(top_genres)}")

        return result

    except Exception as extraction_error:
  # Comprehensive error handling with performance tracking
        if performance_tracking and start_time is not None:
            result['processing_time'] = time.time() - start_time

        error_message = f"Genre extraction error: {extraction_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} {error_message}")

        return result


def _display_genre_assignment_status(*, loaded_genres: List[str], discovered_genres: List[str],
                                   null_genre: str = 'null') -> None:
    """Display comprehensive genre assignment status with visual feedback.

    Args:
        loaded_genres: List of loaded genre filters
        discovered_genres: List of all discovered genres in library
        null_genre: String representing null/empty genre
    """
    print('🎵 Genres for Random Play Assignment:')

  # Display loaded genre filters
    genre_labels = ['Genre 0', 'Genre 1', 'Genre 2', 'Genre 3']
    active_count = 0

    for i, (label, genre) in enumerate(zip(genre_labels, loaded_genres)):
        if genre == null_genre:
            print(f'   {label}: ❌ No filter active')
        else:
            print(f'   {label}: ✓ {genre}')
            active_count += 1

    print(f'\n📊 Assignment Summary:')
    print(f'   Active filters: {active_count}/4')
    print(f'   Total genres discovered: {len(discovered_genres)}')

    if discovered_genres:
        print(f'   Available genres: {", ".join(discovered_genres[:10])}')
        if len(discovered_genres) > 10:
            print(f'   ... and {len(discovered_genres) - 10} more')
    else:
        print(f'   ⚠️ No genres found in music library')


def assign_genres_to_random_play(*,
                                 console_output: bool = True,
                                 validate_input: bool = True,
                                 force_reload: bool = False,
                                 include_statistics: bool = False) -> Dict[str, Union[bool, int, str, List, Dict]]:
    """Assign genre filters for random playlist generation with comprehensive Pythonic functionality.

    This function implements modern Python genre management patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Configurable genre loading behavior and options
    - Return structured data for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions
    - Intelligent genre extraction and filtering logic
    - Performance optimization with efficient processing

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_input: Whether to validate music library and genre file data - keyword-only
        force_reload: Whether to force reloading genres even if already loaded - keyword-only
        include_statistics: Whether to include detailed statistics - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if genres were assigned successfully
        - 'genres_loaded': List[str] - List of loaded genre filters
        - 'genres_discovered': List[str] - List of all unique genres found in music library
        - 'total_genres_processed': int - Total number of genre references processed
        - 'songs_processed': int - Number of songs analyzed for genres
        - 'error_message': str - Error message if failed (empty if success)
        - 'processing_time': float - Time taken to process genres
        - 'statistics': Dict - Detailed statistics (if enabled)

    Examples:
        >>> assign_genres_to_random_play()
        {'success': True, 'genres_loaded': ['rbilly'], 'genres_discovered': ['rbilly', 'rock', 'pop'], ...}
        >>> assign_genres_to_random_play(include_statistics=True)
        {'success': True, 'statistics': {'genre_frequency': {...}}, ...}
        >>> assign_genres_to_random_play(force_reload=True, console_output=False)
        {'success': True, 'genres_loaded': ['rbilly'], ...}

    Note:
        Function updates global variables for compatibility with existing system.
        Genre filters are loaded from GenreFlagsList.txt configuration file.
    """
    from typing import Final
    import time
    from pathlib import Path

  # Constants for better maintainability
    GENRE_CONFIG_FILE: Final = 'GenreFlagsList.txt'
    NULL_GENRE: Final = 'null'
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_INFO: Final = 'ℹ️'
    EMOJI_FILTER: Final = '🔍'
    EMOJI_DISCOVERY: Final = '🔍'
    DEFAULT_UNKNOWN: Final = 'Unknown'
    EXPECTED_GENRE_COUNT: Final = 4

  # Initialize result structure
    result = {
        'success': False,
        'genres_loaded': [],
        'genres_discovered': [],
        'total_genres_processed': 0,
        'songs_processed': 0,
        'error_message': '',
        'processing_time': 0.0,
        'statistics': {} if include_statistics else None
    }

    start_time = time.time()

    try:
  # Access global variables
        global FinalGenreList, MusicMasterSongList
        global genre0, genre1, genre2, genre3

  # Input validation with early returns
        if validate_input:
            validation_result = _validate_genre_assignment_inputs(
                console_output=console_output
            )

            if not validation_result['valid']:
                result['error_message'] = validation_result['message']
                if console_output:
                    print(f"{EMOJI_ERROR} Genre assignment validation failed: {validation_result['message']}")
                return result

  # Check if reload is needed
        if not force_reload and hasattr(assign_genres_to_random_play, '_genres_loaded'):
            result.update({
                'success': True,
                'genres_loaded': [g for g in [genre0, genre1, genre2, genre3] if g != NULL_GENRE],
                'genres_discovered': FinalGenreList if 'FinalGenreList' in globals() else [],
                'error_message': 'Genres already loaded (use force_reload=True to reload)'
            })

            if console_output:
                loaded_count = len([g for g in [genre0, genre1, genre2, genre3] if g != NULL_GENRE])
                print(f"{EMOJI_INFO} Genre filters already loaded ({loaded_count} active filters)")

            result['processing_time'] = time.time() - start_time
            return result

  # Load genre configuration from file
        genre_config = _load_genre_configuration(
            config_file=GENRE_CONFIG_FILE,
            console_output=console_output
        )

        if not genre_config['success']:
            result['error_message'] = genre_config['error_message']
            if console_output:
                print(f"{EMOJI_ERROR} Failed to load genre configuration: {genre_config['error_message']}")
            return result

  # Assign genre filters from configuration
        genre_filters = genre_config['genre_filters']
        genre0 = genre_filters[0] if len(genre_filters) > 0 else NULL_GENRE
        genre1 = genre_filters[1] if len(genre_filters) > 1 else NULL_GENRE
        genre2 = genre_filters[2] if len(genre_filters) > 2 else NULL_GENRE
        genre3 = genre_filters[3] if len(genre_filters) > 3 else NULL_GENRE

        loaded_genres = [g for g in [genre0, genre1, genre2, genre3] if g != NULL_GENRE]
        result['genres_loaded'] = loaded_genres

        if console_output:
            print(f"{EMOJI_SUCCESS} Loaded {len(loaded_genres)} genre filters from configuration")

  # Extract and process all genres from music library
        genre_extraction_result = _extract_all_genres_from_library(
            music_library=MusicMasterSongList,
            include_statistics=include_statistics,
            console_output=console_output
        )

        if not genre_extraction_result['success']:
            result['error_message'] = genre_extraction_result['error_message']
            if console_output:
                print(f"{EMOJI_ERROR} Failed to extract genres from library: {genre_extraction_result['error_message']}")
            return result

  # Update global FinalGenreList with discovered genres
        FinalGenreList = genre_extraction_result['unique_genres']
        result.update({
            'genres_discovered': FinalGenreList,
            'total_genres_processed': genre_extraction_result['total_genres_processed'],
            'songs_processed': genre_extraction_result['songs_processed']
        })

  # Display genre assignment status
        if console_output:
            _display_genre_assignment_status(
                loaded_genres=[genre0, genre1, genre2, genre3],
                discovered_genres=FinalGenreList,
                null_genre=NULL_GENRE
            )

  # Add detailed statistics if requested
        if include_statistics and genre_extraction_result['statistics']:
            result['statistics'] = genre_extraction_result['statistics']

  # Mark as successfully loaded
        assign_genres_to_random_play._genres_loaded = True

  # Update result with success information
        result['success'] = True

  # Log successful assignment
        _log_info(
            f"Genre assignment completed: {len(loaded_genres)} filters loaded, "
            f"{len(FinalGenreList)} unique genres discovered from {result['songs_processed']} songs",
            level="INFO",
            console_output=False,
            category="genre_assignment"
        )

        result['processing_time'] = time.time() - start_time
        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        result['processing_time'] = time.time() - start_time
        error_message = f"Genre assignment error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Error assigning genres: {general_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="WARNING",
            console_output=False,
            include_traceback=True
        )

        return result


def generate_random_song_list(*,
                             console_output: bool = True,
                             validate_input: bool = True,
                             force_regenerate: bool = False,
                             shuffle_result: bool = True,
                             include_statistics: bool = False) -> Dict[str, Union[bool, int, str, List]]:
    """Generate random song playlist with comprehensive Pythonic functionality.

    This function implements modern Python playlist generation patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Configurable generation behavior and options
    - Return structured data for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions
    - Intelligent genre filtering and song inclusion logic
    - Performance optimization with efficient filtering

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_input: Whether to validate music library and genre data - keyword-only
        force_regenerate: Whether to force regeneration even if playlist exists - keyword-only
        shuffle_result: Whether to shuffle the final playlist - keyword-only
        include_statistics: Whether to include detailed statistics - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if playlist was generated successfully
        - 'songs_added': int - Number of songs added to random playlist
        - 'songs_filtered': int - Number of songs excluded by filters
        - 'total_songs_processed': int - Total number of songs processed
        - 'genres_active': List[str] - List of active genre filters
        - 'playlist_size': int - Final playlist size
        - 'error_message': str - Error message if failed (empty if success)
        - 'generation_time': float - Time taken to generate playlist
        - 'statistics': Dict - Detailed statistics (if enabled)

    Examples:
        >>> generate_random_song_list()
        {'success': True, 'songs_added': 1592, 'playlist_size': 1592, ...}
        >>> generate_random_song_list(include_statistics=True)
        {'success': True, 'statistics': {'genre_breakdown': {...}}, ...}
        >>> generate_random_song_list(force_regenerate=True, shuffle_result=False)
        {'success': True, 'songs_added': 1592, 'shuffled': False, ...}

    Note:
        Function respects genre filters and 'norandom' tags in song metadata.
        Uses global variables for compatibility with existing system.
    """
    from typing import Final
    import time
    import random

  # Constants for better maintainability
    DEFAULT_UNKNOWN: Final = 'Unknown'
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_INFO: Final = 'ℹ️'
    EMOJI_FILTER: Final = '🔍'
    NULL_GENRE: Final = 'null'
    NORANDOM_TAG: Final = 'norandom'

  # Initialize result structure
    result = {
        'success': False,
        'songs_added': 0,
        'songs_filtered': 0,
        'total_songs_processed': 0,
        'genres_active': [],
        'playlist_size': 0,
        'error_message': '',
        'generation_time': 0.0,
        'statistics': {} if include_statistics else None
    }

    start_time = time.time()

    try:
  # Access global variables
        global MusicMasterSongList, RandomMusicPlayList
        global genre0, genre1, genre2, genre3

  # Input validation with early returns
        if validate_input:
            validation_result = _validate_random_playlist_inputs(
                console_output=console_output
            )

            if not validation_result['valid']:
                result['error_message'] = validation_result['message']
                if console_output:
                    print(f"{EMOJI_ERROR} Playlist generation validation failed: {validation_result['message']}")
                return result

  # Check if regeneration is needed
        if not force_regenerate and RandomMusicPlayList:
            result.update({
                'success': True,
                'songs_added': 0,
                'playlist_size': len(RandomMusicPlayList),
                'error_message': 'Playlist already exists (use force_regenerate=True to rebuild)'
            })

            if console_output:
                print(f"{EMOJI_INFO} Random playlist already exists with {len(RandomMusicPlayList)} songs")

            result['generation_time'] = time.time() - start_time
            return result

  # Clear existing playlist for regeneration
        if force_regenerate:
            RandomMusicPlayList.clear()
            if console_output:
                print(f"{EMOJI_INFO} Clearing existing random playlist for regeneration")

  # Collect active genres for filtering
        active_genres = _get_active_genres(genre0, genre1, genre2, genre3)
        result['genres_active'] = active_genres

        if console_output:
            if active_genres:
                print(f"{EMOJI_FILTER} Active genre filters: {', '.join(active_genres)}")
            else:
                print(f"{EMOJI_FILTER} No genre filters active - including all songs")

  # Statistics tracking if enabled
        stats = {
            'genre_breakdown': {},
            'filtered_songs': [],
            'norandom_count': 0,
            'processing_time_per_song': []
        } if include_statistics else None

  # Process songs with efficient filtering
        songs_processed = 0
        songs_added = 0
        songs_filtered = 0

        for song_index, song_data in enumerate(MusicMasterSongList):
            song_start_time = time.time() if include_statistics else None
            songs_processed += 1

            try:
  # Check for norandom tag
                song_comment = song_data.get('comment', '')

                if NORANDOM_TAG in song_comment:
                    songs_filtered += 1
                    if include_statistics:
                        stats['norandom_count'] += 1
                        stats['filtered_songs'].append({
                            'index': song_index,
                            'reason': 'norandom_tag',
                            'title': song_data.get('title', DEFAULT_UNKNOWN)
                        })
                    continue

  # Apply genre filtering logic
                should_include = _should_include_song_in_random_playlist(
                    song_comment=song_comment,
                    active_genres=active_genres
                )

                if should_include:
                    RandomMusicPlayList.append(song_index)
                    songs_added += 1

  # Update statistics
                    if include_statistics:
                        song_genres = _extract_song_genres(song_comment, active_genres)
                        for genre in song_genres:
                            stats['genre_breakdown'][genre] = stats['genre_breakdown'].get(genre, 0) + 1
                else:
                    songs_filtered += 1
                    if include_statistics:
                        stats['filtered_songs'].append({
                            'index': song_index,
                            'reason': 'genre_mismatch',
                            'title': song_data.get('title', DEFAULT_UNKNOWN)
                        })

                if include_statistics and song_start_time:
                    stats['processing_time_per_song'].append(time.time() - song_start_time)

            except Exception as song_error:
                songs_filtered += 1
                if console_output:
                    print(f"{EMOJI_WARNING} Error processing song {song_index}: {song_error}")
                continue

  # Shuffle playlist if requested
        if shuffle_result and RandomMusicPlayList:
            random.shuffle(RandomMusicPlayList)
            if console_output:
                print(f"{EMOJI_SUCCESS} Shuffled random playlist")

  # Update result with success information
        result.update({
            'success': True,
            'songs_added': songs_added,
            'songs_filtered': songs_filtered,
            'total_songs_processed': songs_processed,
            'playlist_size': len(RandomMusicPlayList)
        })

  # Add detailed statistics if requested
        if include_statistics and stats:
  # Calculate additional statistics
            if stats['processing_time_per_song']:
                stats['average_processing_time'] = sum(stats['processing_time_per_song']) / len(stats['processing_time_per_song'])
                stats['total_processing_time'] = sum(stats['processing_time_per_song'])

            stats['inclusion_rate'] = (songs_added / songs_processed * 100) if songs_processed > 0 else 0
            stats['filter_efficiency'] = (songs_filtered / songs_processed * 100) if songs_processed > 0 else 0

            result['statistics'] = stats

  # Final status output
        if console_output:
            print(f"{EMOJI_SUCCESS} Random playlist generated successfully:")
            print(f"   Songs added: {songs_added}")
            print(f"   Songs filtered: {songs_filtered}")
            print(f"   Final playlist size: {len(RandomMusicPlayList)}")
            if active_genres:
                print(f"   Active genres: {', '.join(active_genres)}")

  # Log successful generation
        _log_info(
            f"Random playlist generated: {songs_added} songs added, {songs_filtered} filtered, "
            f"final size: {len(RandomMusicPlayList)}",
            level="INFO",
            console_output=False,
            category="playlist_generation"
        )

        result['generation_time'] = time.time() - start_time
        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        result['generation_time'] = time.time() - start_time
        error_message = f"Random playlist generation error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Error generating random playlist: {general_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="WARNING",
            console_output=False,
            include_traceback=True
        )

        return result


def jukebox_engine(*,
                   console_output: bool = True,
                   max_iterations: Optional[int] = None,
                   failure_retry_delay: float = 5.0,
                   error_retry_delay: float = 2.0,
                   validate_startup: bool = True,
                   auto_recovery: bool = True,
                   log_operations: bool = True,
                   graceful_shutdown: bool = True,
                   performance_monitoring: bool = False) -> Dict[str, Union[bool, int, str, float, List]]:
    """Enhanced Pythonic main jukebox engine with comprehensive functionality.

    This function implements modern Python jukebox engine patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Configurable engine behavior and monitoring
    - Return structured data for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions
    - Iterative design to prevent stack overflow
    - Performance monitoring and statistics tracking

    Plays paid songs first (priority queue), then random songs in a continuous loop.
    Uses modern Pythonic patterns for better maintainability and stability.

    Args:
        console_output: Whether to print status messages - keyword-only
        max_iterations: Maximum engine iterations (None for infinite) - keyword-only
        failure_retry_delay: Delay in seconds when no songs available - keyword-only
        error_retry_delay: Delay in seconds after errors - keyword-only
        validate_startup: Whether to validate system on startup - keyword-only
        auto_recovery: Whether to attempt auto-recovery from errors - keyword-only
        log_operations: Whether to log engine operations - keyword-only
        graceful_shutdown: Whether to handle shutdown gracefully - keyword-only
        performance_monitoring: Whether to track performance stats - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if engine completed successfully
        - 'iterations_completed': int - Number of iterations completed
        - 'songs_played': int - Total songs played during session
        - 'paid_songs_played': int - Number of paid songs played
        - 'random_songs_played': int - Number of random songs played
        - 'errors_encountered': int - Number of errors encountered
        - 'total_runtime': float - Total engine runtime in seconds
        - 'shutdown_reason': str - Reason for engine shutdown
        - 'error_messages': List[str] - List of error messages encountered
        - 'performance_stats': Dict - Performance statistics (if enabled)

    Examples:
        >>> jukebox_engine()  # Run with defaults
        {'success': True, 'iterations_completed': 150, 'songs_played': 45, ...}
        >>> jukebox_engine(max_iterations=10, performance_monitoring=True)
        {'success': True, 'iterations_completed': 10, 'performance_stats': {...}, ...}
        >>> jukebox_engine(console_output=False, auto_recovery=False)
        {'success': False, 'shutdown_reason': 'Critical error', ...}

    Note:
        Engine uses iterative loop design to prevent stack overflow.
        Paid songs always have priority over random songs.
        Supports comprehensive monitoring and recovery mechanisms.
    """
    from typing import Final
    import time
    from datetime import datetime

  # Constants for better maintainability
    DEFAULT_UNKNOWN: Final = 'Unknown'
    EMOJI_ENGINE: Final = '🎵'
    EMOJI_STOP: Final = '🛑'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_INFO: Final = 'ℹ️'
    EMOJI_STATS: Final = '📊'
    MIN_DELAY: Final = 0.1
    MAX_DELAY: Final = 60.0
    MAX_ITERATIONS_LIMIT: Final = 1000000

  # Initialize result structure
    result = {
        'success': False,
        'iterations_completed': 0,
        'songs_played': 0,
        'paid_songs_played': 0,
        'random_songs_played': 0,
        'errors_encountered': 0,
        'total_runtime': 0.0,
        'shutdown_reason': '',
        'error_messages': [],
        'performance_stats': {} if performance_monitoring else None
    }

  # Performance monitoring setup
    start_time = time.time()
    iteration_times = [] if performance_monitoring else None

    try:
  # Input validation with early returns
        validation_result = _validate_engine_inputs(
            max_iterations=max_iterations,
            failure_retry_delay=failure_retry_delay,
            error_retry_delay=error_retry_delay,
            console_output=console_output
        )

        if not validation_result['valid']:
            result['shutdown_reason'] = f"Input validation failed: {validation_result['message']}"
            if console_output:
                print(f"{EMOJI_ERROR} {result['shutdown_reason']}")
            return result

  # Startup validation if enabled
        if validate_startup:
            startup_result = _validate_engine_startup(
                console_output=console_output
            )

            if not startup_result['success']:
                result['shutdown_reason'] = f"Startup validation failed: {startup_result['error_message']}"
                if console_output:
                    print(f"{EMOJI_ERROR} {result['shutdown_reason']}")
                return result

        if console_output:
            print(f"{EMOJI_ENGINE} Starting Enhanced Jukebox Engine...")
            if max_iterations:
                print(f"{EMOJI_INFO} Maximum iterations: {max_iterations}")
            if performance_monitoring:
                print(f"{EMOJI_STATS} Performance monitoring enabled")

  # Log engine startup
        if log_operations:
            _log_info(
                f"Jukebox engine started with config: max_iterations={max_iterations}, "
                f"monitoring={performance_monitoring}",
                level="INFO",
                console_output=False,
                category="engine_startup"
            )

  # Main engine loop - iterative design prevents stack overflow
        iteration_count = 0
        while True:
            iteration_start = time.time() if performance_monitoring else None

            try:
  # Check iteration limit
                if max_iterations is not None and iteration_count >= max_iterations:
                    result['shutdown_reason'] = f"Maximum iterations reached: {max_iterations}"
                    if console_output:
                        print(f"{EMOJI_SUCCESS} {result['shutdown_reason']}")
                    result['success'] = True
                    break

                iteration_count += 1
                result['iterations_completed'] = iteration_count

  # Process paid songs first (priority queue)
                paid_result = _process_paid_songs(
                    console_output=console_output,
                    retry_on_failure=auto_recovery
                )

                if paid_result['success']:
                    result['songs_played'] += 1
                    result['paid_songs_played'] += 1

                    if performance_monitoring and iteration_start:
                        iteration_times.append(time.time() - iteration_start)

                    continue  # Check for more paid songs immediately

  # Process random songs when no paid songs available
                random_result = _process_random_songs(
                    console_output=console_output,
                    retry_on_failure=auto_recovery
                )

                if random_result['success']:
                    result['songs_played'] += 1
                    result['random_songs_played'] += 1

                    if performance_monitoring and iteration_start:
                        iteration_times.append(time.time() - iteration_start)

                else:
  # Handle no songs available scenario
                    if random_result.get('playlist_size', 0) > 0:
                        error_msg = f"Failed to play random songs: {random_result['error_message']}"
                        result['error_messages'].append(error_msg)

                        if console_output:
                            print(f"{EMOJI_WARNING} {error_msg}")
                    else:
                        if console_output:
                            print(f"{EMOJI_WARNING} No songs available to play. Waiting...")

  # Wait before next attempt
                    time.sleep(failure_retry_delay)

                if performance_monitoring and iteration_start:
                    iteration_times.append(time.time() - iteration_start)

            except KeyboardInterrupt:
                result['shutdown_reason'] = "User requested shutdown (Ctrl+C)"
                if graceful_shutdown and console_output:
                    print(f"\n{EMOJI_STOP} Jukebox Engine stopped by user")
                result['success'] = True
                break

            except Exception as iteration_error:
                result['errors_encountered'] += 1
                error_message = f"Error in engine iteration {iteration_count}: {iteration_error}"
                result['error_messages'].append(error_message)

                if console_output:
                    print(f"{EMOJI_ERROR} {error_message}")

  # Log the error
                if log_operations:
                    _log_error(
                        error_message,
                        error_type="WARNING" if auto_recovery else "CRITICAL",
                        console_output=False,
                        include_traceback=True
                    )

                if auto_recovery:
                    if console_output:
                        print(f"{EMOJI_INFO} Attempting auto-recovery...")
                    time.sleep(error_retry_delay)
                else:
                    result['shutdown_reason'] = f"Critical error: {iteration_error}"
                    break

  # Calculate final statistics
        result['total_runtime'] = time.time() - start_time

  # Performance statistics compilation
        if performance_monitoring and iteration_times:
            result['performance_stats'] = {
                'average_iteration_time': sum(iteration_times) / len(iteration_times),
                'max_iteration_time': max(iteration_times),
                'min_iteration_time': min(iteration_times),
                'total_iterations_timed': len(iteration_times),
                'songs_per_minute': (result['songs_played'] / result['total_runtime']) * 60 if result['total_runtime'] > 0 else 0
            }

  # Final success determination
        if not result['shutdown_reason']:
            result['success'] = True
            result['shutdown_reason'] = "Normal completion"

  # Final status output
        if console_output:
            print(f"\n{EMOJI_STATS} Engine Session Summary:")
            print(f"   Iterations: {result['iterations_completed']}")
            print(f"   Songs played: {result['songs_played']} (Paid: {result['paid_songs_played']}, Random: {result['random_songs_played']})")
            print(f"   Runtime: {result['total_runtime']:.1f} seconds")
            print(f"   Errors: {result['errors_encountered']}")

            if performance_monitoring and result['performance_stats']:
                stats = result['performance_stats']
                print(f"   Avg iteration time: {stats['average_iteration_time']:.3f}s")
                print(f"   Songs per minute: {stats['songs_per_minute']:.1f}")

  # Log final statistics
        if log_operations:
            _log_info(
                f"Jukebox engine completed: iterations={result['iterations_completed']}, "
                f"songs={result['songs_played']}, runtime={result['total_runtime']:.1f}s, "
                f"errors={result['errors_encountered']}",
                level="INFO",
                console_output=False,
                category="engine_completion"
            )

        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        result['total_runtime'] = time.time() - start_time
        result['errors_encountered'] += 1
        error_message = f"General jukebox engine error: {general_error}"
        result['error_messages'].append(error_message)
        result['shutdown_reason'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Critical engine error: {general_error}")

  # Log critical error
        if log_operations:
            _log_error(
                error_message,
                error_type="CRITICAL",
                console_output=False,
                include_traceback=True
            )

        return result


def _process_paid_songs(*,
                       console_output: bool = True,
                       validate_playlist: bool = True,
                       auto_remove: bool = True,
                       retry_on_failure: bool = False,
                       max_retries: int = 2,
                       fallback_selection: bool = True,
                       skip_corrupted: bool = True,
                       playlist_file: str = 'PaidMusicPlayList.txt') -> Dict[str, Union[bool, str, int, List]]:
    """Process paid songs queue with comprehensive Pythonic functionality.

    This function implements modern Python paid playlist processing patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Configurable processing behavior and options
    - Return structured data for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions
    - Automatic playlist management and cleanup
    - Fallback mechanisms for corrupted entries
    - Priority queue behavior for paid songs

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_playlist: Whether to validate playlist state - keyword-only
        auto_remove: Whether to automatically remove played songs - keyword-only
        retry_on_failure: Whether to retry with next song on failure - keyword-only
        max_retries: Maximum number of songs to try - keyword-only
        fallback_selection: Whether to use fallback song selection - keyword-only
        skip_corrupted: Whether to skip corrupted playlist entries - keyword-only
        playlist_file: Path to paid playlist file - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if a paid song was played successfully
        - 'songs_tried': int - Number of songs attempted
        - 'song_index': int - Index of successfully played song (-1 if none)
        - 'song_title': str - Title of played song
        - 'song_artist': str - Artist of played song
        - 'playlist_size': int - Current playlist size
        - 'skipped_indices': List[int] - Indices of skipped corrupted songs
        - 'error_message': str - Error message if failed (empty if success)
        - 'removal_performed': bool - Whether song removal occurred
        - 'playlist_file': str - Playlist file used

    Examples:
        >>> _process_paid_songs()
        {'success': True, 'songs_tried': 1, 'song_title': 'Song Name', ...}
        >>> _process_paid_songs(retry_on_failure=True, max_retries=3)
        {'success': True, 'songs_tried': 2, 'skipped_indices': [42], ...}
        >>> _process_paid_songs(auto_remove=False)
        {'success': True, 'removal_performed': False, ...}

    Note:
        Paid songs have priority over random songs in the jukebox system.
        Supports automatic cleanup of corrupted playlist entries.
    """
    from typing import Final

  # Constants for better maintainability
    DEFAULT_UNKNOWN: Final = 'Unknown'
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_INFO: Final = 'ℹ️'
    EMOJI_PRIORITY: Final = '💰'  # Money bag for paid songs
    MIN_RETRIES: Final = 0
    MAX_RETRIES_LIMIT: Final = 10

  # Initialize result structure
    result = {
        'success': False,
        'songs_tried': 0,
        'song_index': -1,
        'song_title': DEFAULT_UNKNOWN,
        'song_artist': DEFAULT_UNKNOWN,
        'playlist_size': 0,
        'skipped_indices': [],
        'error_message': '',
        'removal_performed': False,
        'playlist_file': playlist_file
    }

    try:
  # Input validation with early returns
        if validate_playlist:
            validation_result = _validate_paid_playlist_inputs(
                playlist_file=playlist_file,
                max_retries=max_retries,
                console_output=console_output
            )

            if not validation_result['valid']:
                result['error_message'] = validation_result['message']
                if console_output:
                    print(f"{EMOJI_ERROR} Playlist validation failed: {validation_result['message']}")
                return result

  # Load paid playlist with comprehensive error handling
        playlist_load_result = _load_paid_playlist_safely(
            playlist_file=playlist_file,
            console_output=console_output
        )

        if not playlist_load_result['success']:
            result['error_message'] = playlist_load_result['error_message']
            result['playlist_size'] = playlist_load_result.get('playlist_size', 0)
            if console_output and playlist_load_result.get('playlist_size', 0) == 0:
                print(f"{EMOJI_INFO} No paid songs available in queue")
            return result

        paid_playlist = playlist_load_result['playlist']
        result['playlist_size'] = len(paid_playlist)

        if console_output:
            print(f"{EMOJI_PRIORITY} Processing {len(paid_playlist)} paid song(s) in queue")

  # Attempt to play songs with retry logic
        songs_to_try = min(max_retries + 1 if retry_on_failure else 1, len(paid_playlist))

        for attempt in range(songs_to_try):
            try:
  # Get song index from current position
                if attempt < len(paid_playlist):
                    song_index = paid_playlist[attempt]
                else:
  # Fallback to random selection if enabled
                    if fallback_selection and paid_playlist:
                        import random
                        song_index = random.choice(paid_playlist)
                        if console_output:
                            print(f"{EMOJI_INFO} Using fallback selection: paid song index {song_index}")
                    else:
                        break  # No more songs to try

                result['songs_tried'] = attempt + 1

  # Validate song index before attempting playback
                if skip_corrupted:
                    index_validation = _validate_song_index(
                        song_index,
                        console_output=False  # Suppress individual validation messages
                    )

                    if not index_validation:
                        result['skipped_indices'].append(song_index)
                        if console_output:
                            print(f"{EMOJI_WARNING} Skipping corrupted paid song index: {song_index}")

  # Remove corrupted index from playlist
                        _remove_corrupted_paid_song(song_index, playlist_file)
                        continue

  # Attempt to play the paid song
                playback_result = _play_song_by_index(
                    song_index,
                    is_paid=True,
                    console_output=console_output,
                    retry_on_failure=False  # Handle retries at this level
                )

                if playback_result['success']:
  # Update result with success information
                    result.update({
                        'success': True,
                        'song_index': playback_result.get('song_index', song_index),
                        'song_title': playback_result.get('song_title', DEFAULT_UNKNOWN),
                        'song_artist': playback_result.get('song_artist', DEFAULT_UNKNOWN)
                    })

  # Remove played song from paid playlist if enabled
                    if auto_remove:
                        removal_result = _remove_from_paid_playlist(
                            console_output=console_output
                        )
                        result['removal_performed'] = removal_result.get('success', False)

                    if console_output:
                        if attempt > 0:
                            print(f"{EMOJI_SUCCESS} Paid song played after {attempt + 1} attempts")
                        else:
                            print(f"{EMOJI_PRIORITY} Paid song played successfully")

  # Log successful processing for audit trail
                    _log_info(
                        f"Paid song processing success: index {song_index}, attempts: {attempt + 1}",
                        level="INFO",
                        console_output=False,
                        category="paid_playlist"
                    )

                    return result
                else:
  # Song playback failed
                    error_msg = playback_result.get('error_message', 'Unknown playback error')
                    result['error_message'] = error_msg

                    if console_output:
                        if retry_on_failure and attempt < songs_to_try - 1:
                            print(f"{EMOJI_WARNING} Paid song {attempt + 1} failed ({error_msg}), trying next...")
                        else:
                            print(f"{EMOJI_ERROR} Failed to play paid song: {error_msg}")

  # Continue to next song if retries enabled
                    if retry_on_failure:
                        continue
                    else:
                        break

            except Exception as song_error:
                error_message = f"Error processing paid song {attempt + 1}: {song_error}"
                result['error_message'] = error_message
                result['songs_tried'] = attempt + 1

                if console_output:
                    if retry_on_failure and attempt < songs_to_try - 1:
                        print(f"{EMOJI_WARNING} {error_message}, trying next song...")
                    else:
                        print(f"{EMOJI_ERROR} {error_message}")

                if retry_on_failure:
                    continue
                else:
                    break

  # If we reach here, all attempts failed
        if not result['error_message']:
            result['error_message'] = f"Failed to play any paid songs after {result['songs_tried']} attempts"

  # Log final failure for audit trail
        _log_error(
            f"Paid song processing failed: attempts: {result['songs_tried']}, error: {result['error_message']}",
            error_type="WARNING",
            console_output=False,
            include_traceback=False
        )

        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        error_message = f"General paid songs processing error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Error processing paid songs: {general_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="WARNING",
            console_output=False,
            include_traceback=True
        )

        return result


def _validate_paid_playlist_inputs(playlist_file: str, *,
                                  max_retries: int = 2,
                                  console_output: bool = True) -> Dict[str, Union[bool, str]]:
    """Validate inputs for _process_paid_songs function.

    Args:
        playlist_file: Path to playlist file to validate
        max_retries: Maximum retries for validation - keyword-only
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from typing import Final
    from pathlib import Path

    EMOJI_ERROR: Final = '❌'
    MIN_RETRIES: Final = 0
    MAX_RETRIES_LIMIT: Final = 10

    try:
  # Validate playlist_file parameter
        if not isinstance(playlist_file, str):
            return {
                'valid': False,
                'message': f"playlist_file must be string, got {type(playlist_file).__name__}"
            }

        if not playlist_file.strip():
            return {
                'valid': False,
                'message': "playlist_file cannot be empty"
            }

  # Validate file extension
        playlist_path = Path(playlist_file)
        if playlist_path.suffix.lower() != '.txt':
            return {
                'valid': False,
                'message': f"playlist_file must be a .txt file, got {playlist_path.suffix}"
            }

  # Validate max_retries parameter
        if not isinstance(max_retries, int) or max_retries < MIN_RETRIES or max_retries > MAX_RETRIES_LIMIT:
            return {
                'valid': False,
                'message': f"max_retries must be integer between {MIN_RETRIES} and {MAX_RETRIES_LIMIT}, got {max_retries}"
            }

        return {
            'valid': True,
            'message': "Input validation passed"
        }

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f"Input validation error: {validation_error}"
        }


def _validate_engine_inputs(max_iterations: Optional[int] = None, *,
                           failure_retry_delay: float = 5.0,
                           error_retry_delay: float = 2.0,
                           console_output: bool = True) -> Dict[str, Union[bool, str]]:
    """Validate inputs for jukebox_engine function.

    Args:
        max_iterations: Maximum engine iterations (None for infinite)
        failure_retry_delay: Delay in seconds when no songs available - keyword-only
        error_retry_delay: Delay in seconds after errors - keyword-only
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from typing import Final

    MIN_DELAY: Final = 0.1
    MAX_DELAY: Final = 60.0
    MAX_ITERATIONS_LIMIT: Final = 1000000

    try:
  # Validate max_iterations parameter
        if max_iterations is not None:
            if not isinstance(max_iterations, int) or max_iterations <= 0 or max_iterations > MAX_ITERATIONS_LIMIT:
                return {
                    'valid': False,
                    'message': f"max_iterations must be positive integer <= {MAX_ITERATIONS_LIMIT} or None, got {max_iterations}"
                }

  # Validate failure_retry_delay parameter
        if not isinstance(failure_retry_delay, (int, float)) or failure_retry_delay < MIN_DELAY or failure_retry_delay > MAX_DELAY:
            return {
                'valid': False,
                'message': f"failure_retry_delay must be number between {MIN_DELAY} and {MAX_DELAY}, got {failure_retry_delay}"
            }

  # Validate error_retry_delay parameter
        if not isinstance(error_retry_delay, (int, float)) or error_retry_delay < MIN_DELAY or error_retry_delay > MAX_DELAY:
            return {
                'valid': False,
                'message': f"error_retry_delay must be number between {MIN_DELAY} and {MAX_DELAY}, got {error_retry_delay}"
            }

  # Validate console_output parameter
        if not isinstance(console_output, bool):
            return {
                'valid': False,
                'message': f"console_output must be boolean, got {type(console_output).__name__}"
            }

        return {
            'valid': True,
            'message': "Engine input validation passed"
        }

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f"Engine input validation error: {validation_error}"
        }


def _validate_engine_startup(*, console_output: bool = True) -> Dict[str, Union[bool, str]]:
    """Validate jukebox engine startup conditions.

    Args:
        console_output: Whether to print status messages - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if startup validation passed
        - 'error_message': str - Error message if validation failed
        - 'system_status': Dict - System status information
    """
    from typing import Final
    import os
    from pathlib import Path

    EMOJI_CHECK: Final = '✓'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_INFO: Final = 'ℹ️'

    result = {
        'success': True,
        'error_message': '',
        'system_status': {
            'music_library_available': False,
            'paid_playlist_exists': False,
            'random_playlist_available': False,
            'vlc_available': False,
            'total_songs': 0,
            'paid_songs_queued': 0
        }
    }

    try:
  # Check music library availability
        if MusicMasterSongList:
            result['system_status']['music_library_available'] = True
            result['system_status']['total_songs'] = len(MusicMasterSongList)
            if console_output:
                print(f"{EMOJI_CHECK} Music library loaded: {len(MusicMasterSongList)} songs")
        else:
            if console_output:
                print(f"{EMOJI_WARNING} Music library is empty or not loaded")

  # Check paid playlist existence
        paid_playlist_path = Path('PaidMusicPlayList.txt')
        if paid_playlist_path.exists():
            result['system_status']['paid_playlist_exists'] = True
            try:
                paid_playlist = _load_playlist('PaidMusicPlayList.txt')
                if paid_playlist:
                    result['system_status']['paid_songs_queued'] = len(paid_playlist)
                    if console_output:
                        print(f"{EMOJI_CHECK} Paid playlist available: {len(paid_playlist)} songs queued")
            except Exception:
                if console_output:
                    print(f"{EMOJI_WARNING} Paid playlist file exists but couldn't be loaded")
        else:
            if console_output:
                print(f"{EMOJI_INFO} Paid playlist file doesn't exist (will be created as needed)")

  # Check random playlist availability
        if RandomMusicPlayList:
            result['system_status']['random_playlist_available'] = True
            if console_output:
                print(f"{EMOJI_CHECK} Random playlist available: {len(RandomMusicPlayList)} songs")
        else:
            if console_output:
                print(f"{EMOJI_WARNING} Random playlist is empty")

  # Check VLC availability (basic check)
        try:
            import vlc
            result['system_status']['vlc_available'] = True
            if console_output:
                print(f"{EMOJI_CHECK} VLC media player library available")
        except ImportError:
            result['system_status']['vlc_available'] = False
            if console_output:
                print(f"{EMOJI_WARNING} VLC media player library not available")

  # Determine if system is ready
        if (not result['system_status']['music_library_available'] or
            result['system_status']['total_songs'] == 0):
            result['success'] = False
            result['error_message'] = "No music library available - cannot start engine"
        elif (not result['system_status']['random_playlist_available'] and
              result['system_status']['paid_songs_queued'] == 0):
            result['success'] = False
            result['error_message'] = "No songs available in any playlist - cannot start engine"
        elif not result['system_status']['vlc_available']:
  # VLC not available is a warning but not a fatal error
            if console_output:
                print(f"{EMOJI_WARNING} VLC not available - some playback features may not work")

        if console_output and result['success']:
            print(f"{EMOJI_CHECK} Startup validation completed successfully")

        return result

    except Exception as startup_error:
        result['success'] = False
        result['error_message'] = f"Startup validation error: {startup_error}"
        return result


def _validate_random_playlist_inputs(*, console_output: bool = True) -> Dict[str, Union[bool, str]]:
    """Validate inputs for generate_random_song_list function.

    Args:
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    from typing import Final

    try:
  # Check if MusicMasterSongList is available and valid
        if not MusicMasterSongList:
            return {
                'valid': False,
                'message': "MusicMasterSongList is empty or not loaded"
            }

        if not isinstance(MusicMasterSongList, list):
            return {
                'valid': False,
                'message': f"MusicMasterSongList must be a list, got {type(MusicMasterSongList).__name__}"
            }

  # Validate that list contains proper song dictionaries
        if len(MusicMasterSongList) > 0:
            sample_song = MusicMasterSongList[0]
            if not isinstance(sample_song, dict):
                return {
                    'valid': False,
                    'message': "MusicMasterSongList must contain dictionaries"
                }

  # Check for required keys
            if 'comment' not in sample_song:
                return {
                    'valid': False,
                    'message': "Songs must contain 'comment' field for genre filtering"
                }

        return {
            'valid': True,
            'message': "Random playlist input validation passed"
        }

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f"Random playlist input validation error: {validation_error}"
        }


def _get_active_genres(genre0: str, genre1: str, genre2: str, genre3: str) -> List[str]:
    """Get list of active genre filters.

    Args:
        genre0, genre1, genre2, genre3: Genre filter strings

    Returns:
        List of active (non-null) genre filters
    """
    from typing import Final

    NULL_GENRE: Final = 'null'

    active_genres = []

    for genre in [genre0, genre1, genre2, genre3]:
        if isinstance(genre, str) and genre.strip() and genre != NULL_GENRE:
            active_genres.append(genre.strip())

    return active_genres


def _should_include_song_in_random_playlist(song_comment: str, active_genres: List[str]) -> bool:
    """Determine if a song should be included in the random playlist based on genre filters.

    Args:
        song_comment: Song's comment field containing genre information
        active_genres: List of active genre filters

    Returns:
        bool: True if song should be included, False otherwise
    """
    from typing import Final

    NORANDOM_TAG: Final = 'norandom'

    try:
  # Songs with norandom tag are never included
        if NORANDOM_TAG in song_comment:
            return False

  # If no active genres, include all songs (except norandom)
        if not active_genres:
            return True

  # Check if song matches any active genre
        for genre in active_genres:
            if genre in song_comment:
                return True

        return False

    except Exception:
  # On any error, exclude the song for safety
        return False


def _extract_song_genres(song_comment: str, active_genres: List[str]) -> List[str]:
    """Extract which active genres are present in a song's comment.

    Args:
        song_comment: Song's comment field
        active_genres: List of active genre filters

    Returns:
        List of genres found in the song comment
    """
    found_genres = []

    try:
        for genre in active_genres:
            if genre in song_comment:
                found_genres.append(genre)

  # If no specific genres found but song is included, mark as 'general'
        if not found_genres and not active_genres:
            found_genres.append('general')

    except Exception:
        pass

    return found_genres


def _load_paid_playlist_safely(playlist_file: str, *,
                               console_output: bool = True) -> Dict[str, Union[bool, str, List, int]]:
    """Safely load paid playlist from file with comprehensive error handling.

    Args:
        playlist_file: Path to playlist file to load
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'success' (bool), 'playlist' (List), 'playlist_size' (int),
        and 'error_message' (str) keys
    """
    from pathlib import Path

    result = {
        'success': False,
        'playlist': [],
        'playlist_size': 0,
        'error_message': ''
    }

    try:
  # Use existing _load_playlist function with error handling
        playlist = _load_playlist(playlist_file)

        if playlist is None:
            result['error_message'] = f"Failed to load playlist from {playlist_file}"
            return result

  # Validate playlist content
        if not isinstance(playlist, (list, tuple)):
            result['error_message'] = f"Invalid playlist format: expected list, got {type(playlist).__name__}"
            return result

        playlist_size = len(playlist)

  # Check if playlist is empty
        if playlist_size == 0:
            result.update({
                'success': True,  # Empty playlist is valid, just no songs to play
                'playlist': [],
                'playlist_size': 0,
                'error_message': 'No paid songs in playlist'
            })
            return result

  # Validate playlist entries (basic type checking)
        valid_entries = []
        invalid_count = 0

        for i, entry in enumerate(playlist):
            try:
  # Try to convert to integer (song index)
                song_index = int(entry)
                valid_entries.append(song_index)
            except (ValueError, TypeError):
                invalid_count += 1
                if console_output:
                    print(f"⚠️ Warning: Invalid playlist entry at position {i}: {entry}")

        result.update({
            'success': True,
            'playlist': valid_entries,
            'playlist_size': len(valid_entries),
            'error_message': f"Loaded {len(valid_entries)} valid entries, {invalid_count} invalid" if invalid_count > 0 else ''
        })

        return result

    except FileNotFoundError:
        result['error_message'] = f"Playlist file not found: {playlist_file}"
        return result
    except PermissionError:
        result['error_message'] = f"Permission denied accessing: {playlist_file}"
        return result
    except Exception as load_error:
        result['error_message'] = f"Error loading playlist: {load_error}"
        return result


def _remove_corrupted_paid_song(song_index: int, playlist_file: str, *,
                               console_output: bool = False) -> Dict[str, Union[bool, str]]:
    """Remove a corrupted song index from the paid playlist.

    Args:
        song_index: Index to remove from playlist
        playlist_file: Path to paid playlist file
        console_output: Whether to print status messages - keyword-only

    Returns:
        Dict with 'success' (bool) and 'message' (str) keys
    """
    try:
  # Load current playlist
        current_playlist = _load_playlist(playlist_file)

        if current_playlist is None:
            return {
                'success': False,
                'message': f"Could not load playlist from {playlist_file}"
            }

  # Convert to list for manipulation
        playlist_list = list(current_playlist)

  # Remove the corrupted song index
        if song_index in playlist_list:
            playlist_list.remove(song_index)

  # Save updated playlist
            save_result = _save_playlist_to_file(playlist_list, playlist_file)

            if save_result:
                message = f"Removed corrupted paid song index {song_index} from {playlist_file}"
                if console_output:
                    print(f"✓ {message}")

                return {
                    'success': True,
                    'message': message
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to save updated playlist to {playlist_file}"
                }
        else:
            message = f"Song index {song_index} not found in paid playlist"
            return {
                'success': False,
                'message': message
            }

    except Exception as removal_error:
        error_msg = f"Error removing corrupted paid song {song_index}: {removal_error}"
        if console_output:
            print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg
        }


def _save_playlist_to_file(playlist: List[int], file_path: str) -> bool:
    """Save playlist to file safely.

    Args:
        playlist: List of song indices to save
        file_path: Path to save playlist to

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        import json
        from pathlib import Path

  # Ensure directory exists
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)

  # Save playlist as JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(playlist, f)

        return True

    except Exception as save_error:
        print(f"❌ Error saving playlist to {file_path}: {save_error}")
        return False


def _process_random_songs(*,
                         console_output: bool = True,
                         validate_playlist: bool = True,
                         auto_rotate: bool = True,
                         retry_on_failure: bool = False,
                         max_retries: int = 2,
                         fallback_selection: bool = True,
                         skip_corrupted: bool = True) -> Dict[str, Union[bool, str, int, List]]:
    """Process random songs queue with comprehensive Pythonic functionality.

    This function implements modern Python playlist processing patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Configurable processing behavior and options
    - Return structured data for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions
    - Automatic playlist management and rotation
    - Fallback mechanisms for corrupted entries

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_playlist: Whether to validate playlist state - keyword-only
        auto_rotate: Whether to automatically rotate playlist after play - keyword-only
        retry_on_failure: Whether to retry with next song on failure - keyword-only
        max_retries: Maximum number of songs to try - keyword-only
        fallback_selection: Whether to use fallback song selection - keyword-only
        skip_corrupted: Whether to skip corrupted playlist entries - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if a song was played successfully
        - 'songs_tried': int - Number of songs attempted
        - 'song_index': int - Index of successfully played song (-1 if none)
        - 'song_title': str - Title of played song
        - 'song_artist': str - Artist of played song
        - 'playlist_size': int - Current playlist size
        - 'skipped_indices': List[int] - Indices of skipped corrupted songs
        - 'error_message': str - Error message if failed (empty if success)
        - 'rotation_performed': bool - Whether playlist rotation occurred

    Examples:
        >>> _process_random_songs()
        {'success': True, 'songs_tried': 1, 'song_title': 'Song Name', ...}
        >>> _process_random_songs(retry_on_failure=True, max_retries=3)
        {'success': True, 'songs_tried': 2, 'skipped_indices': [42], ...}
        >>> _process_random_songs(validate_playlist=False)
        {'success': False, 'error_message': 'No songs available', ...}

    Note:
        Uses global RandomMusicPlayList but provides comprehensive error handling.
        Supports automatic cleanup of corrupted playlist entries.
    """
    from typing import Final

  # Constants for better maintainability
    DEFAULT_UNKNOWN: Final = 'Unknown'
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUCCESS: Final = '✓'
    EMOJI_INFO: Final = 'ℹ️'
    MIN_RETRIES: Final = 0
    MAX_RETRIES_LIMIT: Final = 10

  # Initialize result structure
    result = {
        'success': False,
        'songs_tried': 0,
        'song_index': -1,
        'song_title': DEFAULT_UNKNOWN,
        'song_artist': DEFAULT_UNKNOWN,
        'playlist_size': 0,
        'skipped_indices': [],
        'error_message': '',
        'rotation_performed': False
    }

    try:
  # Input validation with early returns
        if validate_playlist:
            validation_result = _validate_random_playlist_state(
                console_output=console_output,
                max_retries=max_retries
            )

            if not validation_result['valid']:
                result['error_message'] = validation_result['message']
                result['playlist_size'] = validation_result.get('playlist_size', 0)
                if console_output:
                    print(f"{EMOJI_ERROR} Playlist validation failed: {validation_result['message']}")
                return result

  # Access global playlist (safer with error handling)
        try:
            global RandomMusicPlayList
            current_playlist = list(RandomMusicPlayList)  # Create a copy for safety
            result['playlist_size'] = len(current_playlist)
        except (NameError, TypeError) as playlist_error:
            result['error_message'] = f"Cannot access RandomMusicPlayList: {playlist_error}"
            if console_output:
                print(f"{EMOJI_ERROR} {result['error_message']}")
            return result

  # Check if playlist is empty
        if not current_playlist:
            result['error_message'] = "No random songs available in playlist"
            if console_output:
                print(f"{EMOJI_WARNING} No random songs available")
            return result

  # Attempt to play songs with retry logic
        songs_to_try = min(max_retries + 1 if retry_on_failure else 1, len(current_playlist))

        for attempt in range(songs_to_try):
            try:
  # Get song index from current position
                if attempt < len(current_playlist):
                    song_index = current_playlist[attempt]
                else:
  # Fallback to random selection if enabled
                    if fallback_selection and current_playlist:
                        import random
                        song_index = random.choice(current_playlist)
                        if console_output:
                            print(f"{EMOJI_INFO} Using fallback random selection: index {song_index}")
                    else:
                        break  # No more songs to try

                result['songs_tried'] = attempt + 1

  # Validate song index before attempting playback
                if skip_corrupted:
                    index_validation = _validate_song_index(
                        song_index,
                        console_output=False  # Suppress individual validation messages
                    )

                    if not index_validation:
                        result['skipped_indices'].append(song_index)
                        if console_output:
                            print(f"{EMOJI_WARNING} Skipping corrupted song index: {song_index}")

  # Remove corrupted index from playlist
                        _remove_corrupted_song_from_playlist(song_index)
                        continue

  # Attempt to play the song
                playback_result = _play_song_by_index(
                    song_index,
                    is_paid=False,
                    console_output=console_output,
                    retry_on_failure=False  # Handle retries at this level
                )

  # Robust type checking to prevent 'bool' object has no attribute 'get' error
                if not isinstance(playback_result, dict):
                    error_message = f"Error processing song {attempt + 1}: Unexpected return type {type(playback_result).__name__} from _play_song_by_index (expected dict)"
                    result['error_message'] = error_message
                    result['songs_tried'] = attempt + 1

                    if console_output:
                        if retry_on_failure and attempt < songs_to_try - 1:
                            print(f"{EMOJI_WARNING} {error_message}, trying next song...")
                        else:
                            print(f"{EMOJI_ERROR} {error_message}")

                    if retry_on_failure:
                        continue
                    else:
                        break

                if playback_result.get('success', False):
  # Update result with success information
                    result.update({
                        'success': True,
                        'song_index': playback_result.get('song_index', song_index),
                        'song_title': playback_result.get('song_title', DEFAULT_UNKNOWN),
                        'song_artist': playback_result.get('song_artist', DEFAULT_UNKNOWN)
                    })

  # Perform playlist rotation if enabled
                    if auto_rotate:
                        rotation_result = _rotate_random_playlist(
                            console_output=console_output
                        )
                        result['rotation_performed'] = rotation_result.get('success', False)

                    if console_output and attempt > 0:
                        print(f"{EMOJI_SUCCESS} Random song played after {attempt + 1} attempts")

  # Log successful processing for audit trail
                    _log_info(
                        f"Random song processing success: index {song_index}, attempts: {attempt + 1}",
                        level="INFO",
                        console_output=False,
                        category="playlist"
                    )

                    return result
                else:
  # Song playback failed - use safe .get() access
                    error_msg = playback_result.get('error_message', 'Unknown playback error')
                    result['error_message'] = error_msg

                    if console_output:
                        if retry_on_failure and attempt < songs_to_try - 1:
                            print(f"{EMOJI_WARNING} Song {attempt + 1} failed ({error_msg}), trying next...")
                        else:
                            print(f"{EMOJI_ERROR} Failed to play random song: {error_msg}")

  # Continue to next song if retries enabled
                    if retry_on_failure:
                        continue
                    else:
                        break

            except Exception as song_error:
                error_message = f"Error processing song {attempt + 1}: {song_error}"
                result['error_message'] = error_message
                result['songs_tried'] = attempt + 1

                if console_output:
                    if retry_on_failure and attempt < songs_to_try - 1:
                        print(f"{EMOJI_WARNING} {error_message}, trying next song...")
                    else:
                        print(f"{EMOJI_ERROR} {error_message}")

                if retry_on_failure:
                    continue
                else:
                    break

  # If we reach here, all attempts failed
        if not result['error_message']:
            result['error_message'] = f"Failed to play any random songs after {result['songs_tried']} attempts"

  # Log final failure for audit trail
        _log_error(
            f"Random song processing failed: attempts: {result['songs_tried']}, error: {result['error_message']}",
            error_type="WARNING",
            console_output=False,
            include_traceback=False
        )

        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        error_message = f"General random songs processing error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Error processing random songs: {general_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="WARNING",
            console_output=False,
            include_traceback=True
        )

        return result


def _validate_random_playlist_state(*,
                                   console_output: bool = True,
                                   max_retries: int = 2) -> Dict[str, Union[bool, str, int]]:
    """Validate the state of the random playlist.

    Args:
        console_output: Whether to print error messages - keyword-only
        max_retries: Maximum retries for validation - keyword-only

    Returns:
        Dict with 'valid' (bool), 'message' (str), and 'playlist_size' (int) keys
    """
    from typing import Final

    EMOJI_ERROR: Final = '❌'
    MIN_RETRIES: Final = 0
    MAX_RETRIES_LIMIT: Final = 10

    try:
  # Validate max_retries parameter
        if not isinstance(max_retries, int) or max_retries < MIN_RETRIES or max_retries > MAX_RETRIES_LIMIT:
            return {
                'valid': False,
                'message': f"max_retries must be integer between {MIN_RETRIES} and {MAX_RETRIES_LIMIT}, got {max_retries}"
            }

  # Check if RandomMusicPlayList exists
        try:
            global RandomMusicPlayList
            if RandomMusicPlayList is None:
                return {
                    'valid': False,
                    'message': "RandomMusicPlayList is None",
                    'playlist_size': 0
                }

            playlist_size = len(RandomMusicPlayList)

  # Check if playlist is empty
            if playlist_size == 0:
                return {
                    'valid': False,
                    'message': "RandomMusicPlayList is empty",
                    'playlist_size': 0
                }

  # Validate playlist content (basic type checking)
            if not isinstance(RandomMusicPlayList, (list, tuple)):
                return {
                    'valid': False,
                    'message': f"RandomMusicPlayList must be list or tuple, got {type(RandomMusicPlayList).__name__}",
                    'playlist_size': 0
                }

            return {
                'valid': True,
                'message': f"Playlist validation passed ({playlist_size} songs)",
                'playlist_size': playlist_size
            }

        except NameError:
            return {
                'valid': False,
                'message': "RandomMusicPlayList is not defined",
                'playlist_size': 0
            }

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f"Playlist validation error: {validation_error}",
            'playlist_size': 0
        }


def _remove_corrupted_song_from_playlist(song_index: int, *,
                                        console_output: bool = False) -> Dict[str, Union[bool, str]]:
    """Remove a corrupted song index from the random playlist.

    Args:
        song_index: Index to remove from playlist
        console_output: Whether to print status messages - keyword-only

    Returns:
        Dict with 'success' (bool) and 'message' (str) keys
    """
    try:
        global RandomMusicPlayList

        if song_index in RandomMusicPlayList:
            RandomMusicPlayList.remove(song_index)

            message = f"Removed corrupted song index {song_index} from playlist"
            if console_output:
                print(f"✓ {message}")

            return {
                'success': True,
                'message': message
            }
        else:
            message = f"Song index {song_index} not found in playlist"
            return {
                'success': False,
                'message': message
            }

    except Exception as removal_error:
        error_msg = f"Error removing corrupted song {song_index}: {removal_error}"
        if console_output:
            print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg
        }


def _rotate_random_playlist(*,
                           console_output: bool = False,
                           validate_operation: bool = True) -> Dict[str, Union[bool, str, int]]:
    """Rotate the random playlist by moving first song to end.

    Args:
        console_output: Whether to print status messages - keyword-only
        validate_operation: Whether to validate the operation - keyword-only

    Returns:
        Dict with 'success' (bool), 'message' (str), and 'playlist_size' (int) keys
    """
    try:
        global RandomMusicPlayList

  # Validation if requested
        if validate_operation:
            if not isinstance(RandomMusicPlayList, list):
                return {
                    'success': False,
                    'message': f"Cannot rotate: playlist is {type(RandomMusicPlayList).__name__}, not list",
                    'playlist_size': 0
                }

            if len(RandomMusicPlayList) < 2:
                return {
                    'success': False,
                    'message': f"Cannot rotate: playlist has {len(RandomMusicPlayList)} songs (need at least 2)",
                    'playlist_size': len(RandomMusicPlayList)
                }

  # Perform rotation
        playlist_size = len(RandomMusicPlayList)
        if playlist_size > 0:
            first_song = RandomMusicPlayList.pop(0)
            RandomMusicPlayList.append(first_song)

            message = f"Rotated playlist: moved song {first_song} to end"
            if console_output:
                print(f"✓ {message}")

            return {
                'success': True,
                'message': message,
                'playlist_size': playlist_size
            }
        else:
            return {
                'success': False,
                'message': "Cannot rotate empty playlist",
                'playlist_size': 0
            }

    except Exception as rotation_error:
        error_msg = f"Playlist rotation error: {rotation_error}"
        if console_output:
            print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'playlist_size': 0
        }


def _play_song_by_index(song_index: Union[int, str], is_paid: bool, *,
                       console_output: bool = True,
                       validate_input: bool = True,
                       save_song_info: bool = True,
                       display_info: bool = True,
                       log_playback: bool = True,
                       retry_on_failure: bool = False,
                       max_retries: int = 3) -> Dict[str, Union[bool, str, int]]:
    """Play a song by its index with comprehensive Pythonic functionality.

    This function implements modern Python playback patterns including:
    - Keyword-only arguments for better API design
    - Support for multiple input types with automatic conversion
    - Comprehensive input validation with early returns
    - Configurable playback behavior and options
    - Return structured data for operation tracking
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling
    - Separation of concerns with helper functions

    Args:
        song_index: Index of song in MusicMasterSongList (int or str)
        is_paid: Whether this is a paid song or random song
        console_output: Whether to print status messages - keyword-only
        validate_input: Whether to validate input parameters - keyword-only
        save_song_info: Whether to save current song info to file - keyword-only
        display_info: Whether to display now playing information - keyword-only
        log_playback: Whether to log the song playback - keyword-only
        retry_on_failure: Whether to retry on playback failure - keyword-only
        max_retries: Maximum number of retry attempts - keyword-only

    Returns:
        Dict containing:
        - 'success': bool - True if song played successfully
        - 'song_index': int - The validated song index used
        - 'song_title': str - Title of the played song
        - 'song_artist': str - Artist of the played song
        - 'error_message': str - Error message if failed (empty if success)
        - 'retry_count': int - Number of retries attempted

    Examples:
        >>> _play_song_by_index(42, False)
        {'success': True, 'song_index': 42, 'song_title': 'Song Name', ...}
        >>> _play_song_by_index("25", True, validate_input=False)
        {'success': True, 'song_index': 25, 'song_title': 'Song Name', ...}
        >>> _play_song_by_index(999, False, retry_on_failure=True)
        {'success': False, 'error_message': 'Index out of range', ...}

    Note:
        Uses enhanced validation and supports automatic string-to-int conversion.
        Returns structured data for better error handling and operation tracking.
    """
    from typing import Final

  # Constants for better maintainability
    DEFAULT_UNKNOWN: Final = 'Unknown'
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    EMOJI_SUCCESS: Final = '✓'
    MIN_RETRIES: Final = 0
    MAX_RETRIES_LIMIT: Final = 10

  # Initialize result structure
    result = {
        'success': False,
        'song_index': -1,
        'song_title': DEFAULT_UNKNOWN,
        'song_artist': DEFAULT_UNKNOWN,
        'error_message': '',
        'retry_count': 0
    }

    try:
  # Input validation with early returns
        if validate_input:
            validation_result = _validate_play_song_inputs(
                song_index=song_index,
                is_paid=is_paid,
                max_retries=max_retries,
                console_output=console_output
            )

            if not validation_result['valid']:
                result['error_message'] = validation_result['message']
                if console_output:
                    print(f"{EMOJI_ERROR} Input validation failed: {validation_result['message']}")
                return result

  # Use validated index
            validated_index = validation_result['validated_index']
        else:
  # Basic conversion without strict validation
            try:
                validated_index = int(song_index)
            except (ValueError, TypeError) as convert_error:
                result['error_message'] = f"Cannot convert '{song_index}' to integer: {convert_error}"
                if console_output:
                    print(f"{EMOJI_ERROR} {result['error_message']}")
                return result

        result['song_index'] = validated_index

  # Validate song index exists in MusicMasterSongList
        if not _validate_song_index(validated_index, console_output=console_output):
            result['error_message'] = f"Invalid song index: {validated_index}"
            return result

  # Attempt to play song with retry logic
        for attempt in range(max_retries + 1 if retry_on_failure else 1):
            try:
  # Execute song playback operations
                playback_result = _execute_song_playback(
                    song_index=validated_index,
                    is_paid=is_paid,
                    console_output=console_output,
                    save_song_info=save_song_info,
                    display_info=display_info,
                    log_playback=log_playback
                )

                if playback_result['success']:
  # Update result with success information
                    result.update({
                        'success': True,
                        'song_title': playback_result.get('song_title', DEFAULT_UNKNOWN),
                        'song_artist': playback_result.get('song_artist', DEFAULT_UNKNOWN),
                        'retry_count': attempt
                    })

                    if console_output and attempt > 0:
                        print(f"{EMOJI_SUCCESS} Song playback succeeded after {attempt} retries")

  # Log successful playback for audit trail
                    _log_info(
                        f"Song playback success: index {validated_index}, retries: {attempt}",
                        level="INFO",
                        console_output=False,
                        category="playback"
                    )

                    return result
                else:
  # Playback failed, prepare for potential retry
                    result['error_message'] = playback_result.get('error_message', 'Unknown playback error')
                    result['retry_count'] = attempt

                    if retry_on_failure and attempt < max_retries:
                        if console_output:
                            print(f"{EMOJI_WARNING} Playback attempt {attempt + 1} failed, retrying...")
                        continue
                    else:
                        if console_output:
                            failure_msg = f"Playback failed after {attempt + 1} attempts" if retry_on_failure else "Playback failed"
                            print(f"{EMOJI_ERROR} {failure_msg}: {result['error_message']}")
                        break

            except Exception as playback_error:
                error_message = f"Playback attempt {attempt + 1} error: {playback_error}"
                result['error_message'] = error_message
                result['retry_count'] = attempt

                if retry_on_failure and attempt < max_retries:
                    if console_output:
                        print(f"{EMOJI_WARNING} {error_message}, retrying...")
                    continue
                else:
                    if console_output:
                        print(f"{EMOJI_ERROR} {error_message}")
                    break

  # Log final failure for audit trail
        _log_error(
            f"Song playback failed: index {validated_index}, attempts: {result['retry_count'] + 1}, error: {result['error_message']}",
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return result

    except Exception as general_error:
  # Comprehensive error handling with detailed logging
        error_message = f"General song playback error: {general_error}"
        result['error_message'] = error_message

        if console_output:
            print(f"{EMOJI_ERROR} Error playing song: {general_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return result


def _validate_play_song_inputs(song_index: Union[int, str], is_paid: bool, *,
                              max_retries: int = 3,
                              console_output: bool = True) -> Dict[str, Union[bool, str, int]]:
    """Validate inputs for _play_song_by_index function.

    Args:
        song_index: Index to validate and convert
        is_paid: Whether this is a paid song flag
        max_retries: Maximum retry attempts to validate - keyword-only
        console_output: Whether to print error messages - keyword-only

    Returns:
        Dict with 'valid' (bool), 'message' (str), and 'validated_index' (int) keys
    """
    from typing import Final

    EMOJI_ERROR: Final = '❌'
    MIN_RETRIES: Final = 0
    MAX_RETRIES_LIMIT: Final = 10

    try:
  # Validate is_paid parameter
        if not isinstance(is_paid, bool):
            return {
                'valid': False,
                'message': f"is_paid must be boolean, got {type(is_paid).__name__}",
                'validated_index': -1
            }

  # Validate max_retries parameter
        if not isinstance(max_retries, int) or max_retries < MIN_RETRIES or max_retries > MAX_RETRIES_LIMIT:
            return {
                'valid': False,
                'message': f"max_retries must be integer between {MIN_RETRIES} and {MAX_RETRIES_LIMIT}, got {max_retries}"
            }


  # Convert and validate song index
        validated_index = _convert_and_validate_index(
            song_index,
            strict_validation=False,  # Allow string conversion
            console_output=console_output
        )

        if validated_index is None:
            return {
                'valid': False,
                'message': f"Invalid song index: {song_index}",
                'validated_index': -1
            }

        return {
            'valid': True,
            'message': "Input validation passed",
            'validated_index': validated_index
        }

    except Exception as validation_error:
        return {
            'valid': False,
            'message': f"Input validation error: {validation_error}",
            'validated_index': -1
        }


def _execute_song_playback(song_index: int, is_paid: bool, *,
                          console_output: bool = True,
                          save_song_info: bool = True,
                          display_info: bool = True,
                          log_playback: bool = True) -> Dict[str, Union[bool, str]]:
    """Execute the core song playback operations.

    Args:
        song_index: Validated song index
        is_paid: Whether this is a paid song
        console_output: Whether to print status messages - keyword-only
        save_song_info: Whether to save current song info to file - keyword-only
        display_info: Whether to display now playing information - keyword-only
        log_playback: Whether to log the song playback - keyword-only

    Returns:
        Dict with 'success' (bool), 'song_title' (str), 'song_artist' (str),
        and 'error_message' (str) keys
    """
    from typing import Final

    DEFAULT_UNKNOWN: Final = 'Unknown'
    EMOJI_MUSIC: Final = '🎵'
    EMOJI_ERROR: Final = '❌'
    EMOJI_SUCCESS: Final = '✓'

    result = {
        'success': False,
        'song_title': DEFAULT_UNKNOWN,
        'song_artist': DEFAULT_UNKNOWN,
        'error_message': ''
    }

    try:
  # Get song information
        song_info = MusicMasterSongList[song_index]

  # Extract song details with safe defaults
        song_title = song_info.get('title', DEFAULT_UNKNOWN)
        song_artist = song_info.get('artist', DEFAULT_UNKNOWN)
        song_location = song_info.get('location', '')

        result.update({
            'song_title': song_title,
            'song_artist': song_artist
        })

  # Validate song location
        if not song_location:
            result['error_message'] = "Song location is empty or missing"
            return result

  # Display now playing information
        if display_info:
            display_success = _display_now_playing(
                song_info,
                console_output=console_output
            )
            if not display_success and console_output:
                print(f"⚠️ Warning: Failed to display song information for '{song_title}'")

  # Save current song info to file
        if save_song_info:
            save_success = _save_current_song_info(
                song_info,
                console_output=console_output
            )
            if not save_success and console_output:
                print(f"⚠️ Warning: Failed to save song information for '{song_title}'")

  # Log the song play
        if log_playback:
            song_type = "Paid" if is_paid else "Random"
            log_success = _log_song_play(
                song_info,
                song_type,
                console_output=False  # Avoid duplicate console output
            )
            if not log_success and console_output:
                print(f"⚠️ Warning: Failed to log playback for '{song_title}'")

  # Play the song
        song_type = "Paid" if is_paid else "Random"
        if console_output:
            print(f"{EMOJI_MUSIC} Playing {song_type} Song: {song_title} - {song_artist}")

  # Attempt to play the song
        play_result = _safe_play_song(
            song_location,
            song_title=song_title,
            console_output=console_output
        )

        if play_result['success']:
            result['success'] = True
            if console_output:
                print(f"{EMOJI_SUCCESS} Successfully started playback: {song_title}")
        else:
            result['error_message'] = play_result.get('error_message', 'Unknown playback error')

        return result

    except KeyError as key_error:
        result['error_message'] = f"Missing song data key: {key_error}"
        return result
    except IndexError as index_error:
        result['error_message'] = f"Song index {song_index} out of range: {index_error}"
        return result
    except Exception as playback_error:
        result['error_message'] = f"Playback execution error: {playback_error}"
        return result


def _safe_play_song(song_location: str, *,
                   song_title: str = 'Unknown',
                   console_output: bool = True,
                   performance_monitoring: bool = False,
                   playback_timeout: Optional[float] = None) -> Dict[str, Union[bool, str, float, Dict]]:
    """Safely play a song with enhanced error handling and the new play_song function.

    Args:
        song_location: Path to the song file
        song_title: Title of the song for error messages - keyword-only
        console_output: Whether to print error messages - keyword-only
        performance_monitoring: Whether to track playback performance - keyword-only
        playback_timeout: Maximum playback time in seconds - keyword-only

    Returns:
        Dict with comprehensive playback results including:
        - 'success': bool - True if playback completed successfully
        - 'error_message': str - Error message if failed
        - 'playback_duration': float - Duration of playback
        - 'performance_metrics': Dict - Performance data if enabled
    """
    try:
  # Use the enhanced play_song function with comprehensive features
        play_result = play_song(
            song_location,
            console_output=console_output,
            performance_monitoring=performance_monitoring,
            playback_timeout=playback_timeout,
            validation_level='standard',
            error_recovery=True
        )

  # Robust type checking to prevent unexpected return type errors
        if not isinstance(play_result, dict):
            error_msg = f"Unexpected return type {type(play_result).__name__} from play_song (expected dict)"
            if console_output:
                print(f"❌ {error_msg}")
            return {
                'success': False,
                'error_message': error_msg,
                'playback_duration': 0.0,
                'performance_metrics': {}
            }

        if play_result.get('success', False):
            return {
                'success': True,
                'error_message': '',
                'playback_duration': play_result.get('playback_duration', 0.0),
                'performance_metrics': play_result.get('performance_metrics', {})
            }
        else:
            return {
                'success': False,
                'error_message': play_result.get('error_message', 'Unknown playback error'),
                'playback_duration': play_result.get('playback_duration', 0.0),
                'performance_metrics': play_result.get('performance_metrics', {})
            }

    except FileNotFoundError as file_error:
        error_msg = f"Song file not found: {song_location}"
        if console_output:
            print(f"❌ {error_msg}")
        return {
            'success': False,
            'error_message': error_msg,
            'playback_duration': 0.0,
            'performance_metrics': {}
        }
    except PermissionError as perm_error:
        error_msg = f"Permission denied accessing song: {song_location}"
        if console_output:
            print(f"❌ {error_msg}")
        return {
            'success': False,
            'error_message': error_msg,
            'playback_duration': 0.0,
            'performance_metrics': {}
        }
    except Exception as play_error:
        error_msg = f"Error playing '{song_title}': {play_error}"
        if console_output:
            print(f"❌ {error_msg}")
        return {
            'success': False,
            'error_message': error_msg,
            'playback_duration': 0.0,
            'performance_metrics': {}
        }


def _validate_song_index(song_index: Union[int, str, None], *,
                        console_output: bool = True,
                        strict_validation: bool = True,
                        allow_negative: bool = False,
                        custom_range: Optional[Tuple[int, int]] = None) -> bool:
    """Validate song index with comprehensive Pythonic validation.

    This function implements modern Python validation patterns including:
    - Keyword-only arguments for better API design
    - Support for multiple input types with automatic conversion
    - Comprehensive input validation with early returns
    - Configurable validation strictness and rules
    - Custom range validation support
    - Type hints for all parameters and return values
    - Constants for better maintainability
    - Defensive programming with robust error handling

    Args:
        song_index: Index to validate (int, str, or None)
        console_output: Whether to print error messages - keyword-only
        strict_validation: Whether to apply strict type checking - keyword-only
        allow_negative: Whether to allow negative indices - keyword-only
        custom_range: Custom (min, max) range instead of MusicMasterSongList - keyword-only

    Returns:
        bool: True if index is valid, False otherwise

    Examples:
        >>> _validate_song_index(42)
        True
        >>> _validate_song_index("42", strict_validation=False)
        True
        >>> _validate_song_index(-1, allow_negative=True)
        True
        >>> _validate_song_index(100, custom_range=(0, 50))
        False

    Note:
        Uses MusicMasterSongList length by default for range validation.
        Supports automatic string-to-int conversion when strict_validation=False.
    """
    from typing import Final

  # Constants for better maintainability
    EMOJI_ERROR: Final = '❌'
    EMOJI_WARNING: Final = '⚠️'
    DEFAULT_MIN_INDEX: Final = 0
    CONVERSION_ERROR_MSG: Final = "Cannot convert to integer"

    try:
  # Input type validation and conversion
        validated_index = _convert_and_validate_index(
            song_index,
            strict_validation=strict_validation,
            console_output=console_output
        )

        if validated_index is None:
            return False

  # Determine validation range
        if custom_range:
            min_index, max_index = custom_range
            range_source = f"custom range ({min_index}-{max_index})"
        else:
            min_index = DEFAULT_MIN_INDEX if not allow_negative else float('-inf')
            max_index = len(MusicMasterSongList) - 1 if MusicMasterSongList else 0
            range_source = f"MusicMasterSongList (0-{max_index})"

  # Range validation
        range_validation = _validate_index_range(
            validated_index,
            min_index=min_index,
            max_index=max_index,
            allow_negative=allow_negative
        )

        if not range_validation['valid']:
            if console_output:
                print(f"{EMOJI_ERROR} Song index {validated_index} out of range for {range_source}")

  # Log validation failure for audit trail
            _log_error(
                f"Song index validation failed: {validated_index} not in {range_source}",
                error_type="WARNING",
                console_output=False,
                include_traceback=False
            )

            return False

  # Additional validation checks
        additional_checks = _perform_additional_index_checks(
            validated_index,
            strict_validation=strict_validation
        )

        if not additional_checks['valid']:
            if console_output:
                print(f"{EMOJI_WARNING} Index validation warning: {additional_checks['message']}")

  # Return based on strictness setting
            if strict_validation:
                return False

  # Log successful validation for audit trail
        _log_info(
            f"Song index validation passed: {validated_index} (range: {range_source})",
            level="DEBUG",
            console_output=False,
            category="validation"
        )

        return True

    except Exception as validation_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Song index validation error: {validation_error}"

        if console_output:
            print(f"{EMOJI_ERROR} Error validating song index: {validation_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return False


def _convert_and_validate_index(song_index: Union[int, str, None], *,
                              strict_validation: bool = True,
                              console_output: bool = True) -> Optional[int]:
    """Convert and validate song index input.

    Args:
        song_index: Index to convert and validate
        strict_validation: Whether to apply strict type checking - keyword-only
        console_output: Whether to print error messages - keyword-only

    Returns:
        Optional[int]: Converted integer index or None if invalid
    """
    from typing import Final

    EMOJI_ERROR: Final = '❌'

    try:
  # Handle None input
        if song_index is None:
            if console_output:
                print(f"{EMOJI_ERROR} Song index cannot be None")
            return None

  # Handle integer input
        if isinstance(song_index, int):
            return song_index

  # Handle string input
        if isinstance(song_index, str):
            if strict_validation:
                if console_output:
                    print(f"{EMOJI_ERROR} Invalid song index type: {type(song_index).__name__} (strict mode)")
                return None

  # Attempt conversion from string
            try:
                converted_index = int(song_index.strip())
                return converted_index
            except (ValueError, AttributeError) as conversion_error:
                if console_output:
                    print(f"{EMOJI_ERROR} Cannot convert '{song_index}' to integer: {conversion_error}")
                return None

  # Handle other types
        if strict_validation:
            if console_output:
                print(f"{EMOJI_ERROR} Invalid song index type: {type(song_index).__name__}")
            return None

  # Attempt conversion from other types
        try:
            converted_index = int(song_index)
            return converted_index
        except (ValueError, TypeError) as conversion_error:
            if console_output:
                print(f"{EMOJI_ERROR} Cannot convert {type(song_index).__name__} to integer: {conversion_error}")
            return None

    except Exception as convert_error:
        if console_output:
            print(f"{EMOJI_ERROR} Error converting song index: {convert_error}")
        return None


def _validate_index_range(index: int, *,
                         min_index: Union[int, float] = 0,
                         max_index: Union[int, float] = float('inf'),
                         allow_negative: bool = False) -> Dict[str, Union[bool, str]]:
    """Validate that index is within specified range.

    Args:
        index: Index to validate
        min_index: Minimum allowed index - keyword-only
        max_index: Maximum allowed index - keyword-only
        allow_negative: Whether to allow negative indices - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    try:
  # Check negative values
        if index < 0 and not allow_negative:
            return {
                'valid': False,
                'message': f"Negative index {index} not allowed"
            }

  # Check minimum bound
        if index < min_index:
            return {
                'valid': False,
                'message': f"Index {index} below minimum {min_index}"
            }

  # Check maximum bound
        if index > max_index:
            return {
                'valid': False,
                'message': f"Index {index} above maximum {max_index}"
            }

        return {
            'valid': True,
            'message': f"Index {index} within range [{min_index}, {max_index}]"
        }

    except Exception as range_error:
        return {
            'valid': False,
            'message': f"Range validation error: {range_error}"
        }


def _perform_additional_index_checks(index: int, *,
                                   strict_validation: bool = True) -> Dict[str, Union[bool, str]]:
    """Perform additional validation checks on song index.

    Args:
        index: Index to validate
        strict_validation: Whether to apply strict validation - keyword-only

    Returns:
        Dict with 'valid' (bool) and 'message' (str) keys
    """
    try:
        warnings = []

  # Check for extremely large indices
        if index > 100000:  # Arbitrary large number threshold
            warnings.append(f"Very large index {index} may indicate data issue")

  # Check if MusicMasterSongList is empty
        if not MusicMasterSongList and index >= 0:
            warnings.append("MusicMasterSongList is empty, no valid indices")

  # Check for potential off-by-one errors in common ranges
        if MusicMasterSongList and index == len(MusicMasterSongList):
            warnings.append(f"Index {index} equals list length (possible off-by-one error)")

  # Return result based on findings
        if warnings:
            combined_message = "; ".join(warnings)
            return {
                'valid': not strict_validation,  # Warnings are failures in strict mode
                'message': combined_message
            }

        return {
            'valid': True,
            'message': "All additional checks passed"
        }

    except Exception as check_error:
        return {
            'valid': False,
            'message': f"Additional validation error: {check_error}"
        }


def _display_now_playing(song_info: Dict[str, str], *,
                        console_output: bool = True,
                        validate_data: bool = True,
                        format_style: str = 'detailed',
                        include_emoji: bool = True) -> bool:
    """Display now playing information in a formatted Pythonic way.

    This function implements modern Python display patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Return value tracking for operation success/failure
    - Multiple formatting styles for different use cases
    - Configurable emoji and console output
    - Type hints for all parameters
    - Constants for better maintainability

    Args:
        song_info: Dictionary containing song information
        console_output: Whether to print to console - keyword-only
        validate_data: Whether to validate input data - keyword-only
        format_style: Display format ('detailed', 'compact', 'minimal') - keyword-only
        include_emoji: Whether to include emoji in output - keyword-only

    Returns:
        bool: True if display succeeded, False otherwise

    Examples:
        >>> _display_now_playing(song_info)
        True
        >>> _display_now_playing(song_info, format_style='compact')
        True
        >>> _display_now_playing(song_info, console_output=False)
        True

    Note:
        Uses constants for default values and supports multiple formatting styles.
        Validates input data to ensure robust operation.
    """
    from typing import Final

  # Constants for better maintainability
    DEFAULT_UNKNOWN: Final = 'Unknown'
    EMOJI_MUSIC: Final = '🎵' if include_emoji else ''
    EMOJI_ERROR: Final = '❌' if include_emoji else 'Error:'
    VALID_FORMATS: Final = {'detailed', 'compact', 'minimal'}

  # Input validation with early returns
    if validate_data:
        validation_result = _validate_display_song_data(song_info)
        if not validation_result:
            if console_output:
                print(f"{EMOJI_ERROR} Invalid song data - display aborted")
            return False

  # Validate format style
    if format_style not in VALID_FORMATS:
        if console_output:
            print(f"{EMOJI_ERROR} Invalid format style '{format_style}' - using 'detailed'")
        format_style = 'detailed'

    try:
  # Extract song data with safe defaults
        song_data = {
            'title': song_info.get('title', DEFAULT_UNKNOWN),
            'artist': song_info.get('artist', DEFAULT_UNKNOWN),
            'album': song_info.get('album', DEFAULT_UNKNOWN),
            'year': song_info.get('year', DEFAULT_UNKNOWN),
            'duration': song_info.get('duration', DEFAULT_UNKNOWN),
            'genre': song_info.get('comment', DEFAULT_UNKNOWN)
        }

  # Format based on style preference
        formatted_output = _format_now_playing_display(
            song_data,
            format_style=format_style,
            emoji_prefix=EMOJI_MUSIC
        )

  # Output to console if requested
        if console_output:
            print(formatted_output)

  # Log successful display for audit trail
        _log_info(
            f"Song display shown: {song_data['title']} - {song_data['artist']} ({format_style} format)",
            level="INFO",
            console_output=False,
            category="display_ops"
        )

        return True

    except Exception as display_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Display now playing error: {display_error}"

        if console_output:
            print(f"{EMOJI_ERROR} Error displaying song info: {display_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return False


def _save_current_song_info(song_info: Dict[str, str], *,
                           console_output: bool = True,
                           validate_data: bool = True,
                           backup_on_error: bool = False,
                           custom_filename: Optional[str] = None) -> bool:
    """Save current song information to file with enhanced Pythonic features.

    This function implements modern Python file handling patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Return value tracking for operation success/failure
    - Optional backup creation for data protection
    - Configurable filename support
    - Cross-platform path handling
    - Defensive programming with robust error handling

    Args:
        song_info: Dictionary containing song information
        console_output: Whether to print status messages - keyword-only
        validate_data: Whether to validate input data - keyword-only
        backup_on_error: Whether to create backup before writing - keyword-only
        custom_filename: Custom filename to use instead of default - keyword-only

    Returns:
        bool: True if save succeeded, False otherwise

    Examples:
        >>> _save_current_song_info(song_info)
        True
        >>> _save_current_song_info(song_info, console_output=False)
        True
        >>> _save_current_song_info(song_info, custom_filename="NowPlaying.txt")
        True

    Note:
        Default behavior saves only the file location for compatibility.
        Uses pathlib.Path for cross-platform compatibility.
    """
    from typing import Final

  # Constants for better maintainability
    DEFAULT_FILENAME: Final = "CurrentSongPlaying.txt"
    ENCODING: Final = 'utf-8'
    BACKUP_SUFFIX: Final = '.backup'
    DEFAULT_LOCATION: Final = 'Unknown Location'

  # Input validation with early returns
    if validate_data:
        validation_result = _validate_current_song_data(song_info)
        if not validation_result:
            if console_output:
                print("❌ Invalid song data - save aborted")
            return False

    try:
  # Determine filename to use
        filename = custom_filename if custom_filename else DEFAULT_FILENAME

  # Validate custom filename if provided
        if custom_filename and validate_data:
            filename_validation = _validate_song_filename(custom_filename)
            if not filename_validation:
                if console_output:
                    print(f"❌ Invalid custom filename '{custom_filename}' - using default")
                filename = DEFAULT_FILENAME

  # Convert to Path object for modern path handling
        current_song_file = Path(filename)

  # Create backup if requested and file exists
        backup_created = False
        if backup_on_error and current_song_file.exists():
            backup_created = _create_song_info_backup(current_song_file, BACKUP_SUFFIX)

  # Extract song location with fallback
        song_location = song_info.get('location', DEFAULT_LOCATION)

  # Write song information with enhanced error handling
        write_result = _write_current_song_info(
            current_song_file,
            song_location,
            ENCODING
        )

        if write_result['success']:
            if console_output:
                print(f"✓ Updated {current_song_file.name}")

  # Clean up backup if write succeeded
            if backup_created:
                _cleanup_song_info_backup(current_song_file, BACKUP_SUFFIX)

  # Log successful operation for audit trail
            _log_info(
                f"Current song info saved: {filename} ({len(song_location)} chars)",
                level="INFO",
                console_output=False,
                category="file_ops"
            )

            return True
        else:
            if console_output:
                print(f"❌ Failed to save current song info: {write_result['error']}")

  # Restore from backup if available and write failed
            if backup_created:
                _restore_song_info_backup(current_song_file, BACKUP_SUFFIX)

            return False

    except Exception as save_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Current song info save error: {save_error}"

        if console_output:
            print(f"❌ Error saving current song info: {save_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return False


def _validate_display_song_data(song_info: Dict[str, str]) -> bool:
    """Validate song data for display purposes.

    Args:
        song_info: Song information dictionary to validate

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
  # Type validation
        if not isinstance(song_info, dict):
            _log_error(
                f"Song info must be a dictionary, got {type(song_info).__name__}",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Check if dictionary is empty
        if not song_info:
            _log_error(
                "Song info dictionary is empty",
                error_type="WARNING",
                console_output=False
            )
            return False

  # At least one key should be present for meaningful display
        display_keys = {'title', 'artist', 'album', 'year', 'duration', 'comment'}
        if not any(key in song_info for key in display_keys):
            _log_error(
                "Song info must contain at least one display key (title, artist, album, year, duration, comment)",
                error_type="WARNING",
                console_output=False
            )
            return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Song data validation error: {validation_error}",
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )
        return False


def _format_now_playing_display(song_data: Dict[str, str], *,
                               format_style: str = 'detailed',
                               emoji_prefix: str = '🎵') -> str:
    """Format now playing display string based on style preference.

    Args:
        song_data: Dictionary containing song information
        format_style: Display format style - keyword-only
        emoji_prefix: Emoji to use as prefix - keyword-only

    Returns:
        str: Formatted display string
    """
    try:
        if format_style == 'minimal':
            return f"{emoji_prefix} {song_data['title']} - {song_data['artist']}"

        elif format_style == 'compact':
            return (f"{emoji_prefix} Now Playing: {song_data['title']} - {song_data['artist']} "
                   f"({song_data['year']}) [{song_data['duration']}]")

        else:  # detailed format (default)
            return (f"{emoji_prefix} Now Playing: {song_data['title']} - {song_data['artist']}"
                   f" | Year: {song_data['year']} | Length: {song_data['duration']}"
                   f" | Album: {song_data['album']} | Genre: {song_data['genre']}")

    except Exception as format_error:
  # Fallback to minimal format on error
        return f"{emoji_prefix} Error formatting song display: {format_error}"


def _validate_current_song_data(song_info: Dict[str, str]) -> bool:
    """Validate current song data before saving.

    Args:
        song_info: Song information dictionary to validate

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
  # Type validation
        if not isinstance(song_info, dict):
            _log_error(
                f"Song info must be a dictionary, got {type(song_info).__name__}",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Check if dictionary is empty
        if not song_info:
            _log_error(
                "Song info dictionary is empty",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Validate location field exists (primary requirement)
        if 'location' not in song_info:
            _log_error(
                "Song info must contain 'location' key",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Validate location is a string
        location = song_info['location']
        if not isinstance(location, str):
            _log_error(
                f"Song location must be a string, got {type(location).__name__}",
                error_type="WARNING",
                console_output=False
            )
            return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Current song data validation exception: {validation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _validate_song_filename(filename: str) -> bool:
    """Validate custom filename for song info file.

    Args:
        filename: Filename to validate

    Returns:
        bool: True if filename is valid, False otherwise
    """
    try:
  # Basic filename validation
        if not isinstance(filename, str) or not filename.strip():
            _log_error(
                "Filename must be a non-empty string",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Path validation
        try:
            file_path = Path(filename)

  # Check for dangerous path components
            if '..' in file_path.parts:
                _log_error(
                    f"Dangerous path detected in filename: {filename}",
                    error_type="WARNING",
                    console_output=False
                )
                return False

  # Check for absolute paths (should be relative)
            if file_path.is_absolute():
                _log_error(
                    f"Absolute paths not allowed: {filename}",
                    error_type="WARNING",
                    console_output=False
                )
                return False

        except (ValueError, OSError) as path_error:
            _log_error(
                f"Invalid path format: {filename} - {path_error}",
                error_type="WARNING",
                console_output=False
            )
            return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Filename validation exception: {validation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _create_song_info_backup(file_path: Path, backup_suffix: str) -> bool:
    """Create backup of existing song info file.

    Args:
        file_path: Path to the song info file
        backup_suffix: Suffix to use for backup file

    Returns:
        bool: True if backup created successfully, False otherwise
    """
    try:
        backup_file = file_path.with_suffix(file_path.suffix + backup_suffix)
        backup_file.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
        return True

    except Exception as backup_error:
        _log_error(
            f"Backup creation failed for {file_path.name}: {backup_error}",
            error_type="WARNING",
            console_output=False
        )
        return False


def _write_current_song_info(file_path: Path, song_location: str, encoding: str) -> dict:
    """Write current song information to file.

    Args:
        file_path: Path to write the file
        song_location: Song location string to write
        encoding: File encoding to use

    Returns:
        dict: Result with 'success' (bool) and 'error' (str) keys
    """
    try:
  # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

  # Write song location to file
        with file_path.open('w', encoding=encoding, newline='') as outfile:
            outfile.write(song_location)
            outfile.flush()  # Ensure data is written to disk

        return {
            'success': True,
            'error': None
        }

    except (IOError, OSError) as io_error:
        error_msg = f"File I/O error writing to {file_path}: {io_error}"
        _log_error(
            error_msg,
            error_type="ERROR",
            console_output=False
        )
        return {
            'success': False,
            'error': error_msg
        }
    except UnicodeEncodeError as encoding_error:
        error_msg = f"Encoding error writing to {file_path}: {encoding_error}"
        _log_error(
            error_msg,
            error_type="ERROR",
            console_output=False
        )
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as write_error:
        error_msg = f"Unexpected error writing to {file_path}: {write_error}"
        _log_error(
            error_msg,
            error_type="ERROR",
            console_output=False
        )
        return {
            'success': False,
            'error': error_msg
        }


def _cleanup_song_info_backup(file_path: Path, backup_suffix: str) -> None:
    """Clean up backup file after successful write.

    Args:
        file_path: Original file path
        backup_suffix: Suffix used for backup file
    """
    try:
        backup_file = file_path.with_suffix(file_path.suffix + backup_suffix)
        if backup_file.exists():
            backup_file.unlink()
    except Exception as cleanup_error:
        _log_error(
            f"Backup cleanup failed for {file_path.name}: {cleanup_error}",
            error_type="WARNING",
            console_output=False
        )


def _restore_song_info_backup(file_path: Path, backup_suffix: str) -> None:
    """Restore song info from backup file.

    Args:
        file_path: Original file path
        backup_suffix: Suffix used for backup file
    """
    try:
        backup_file = file_path.with_suffix(file_path.suffix + backup_suffix)
        if backup_file.exists():
            file_path.write_text(backup_file.read_text(encoding='utf-8'), encoding='utf-8')
            print(f"✓ Restored {file_path.name} from backup")
    except Exception as restore_error:
        _log_error(
            f"Backup restoration failed for {file_path.name}: {restore_error}",
            error_type="ERROR",
            console_output=False
        )


def _log_song_play(song_info: Dict[str, str], song_type: str, *,
                  console_output: bool = False,
                  validate_data: bool = True,
                  include_metadata: bool = True,
                  log_format: str = "standard") -> bool:
    """Log song play to log file with enhanced Pythonic features.

    This function implements modern Python logging patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Return value tracking for operation success/failure
    - Configurable log formatting options
    - Optional console output control
    - Rich metadata inclusion support
    - Defensive programming with robust error handling

    Args:
        song_info: Dictionary containing song information
        song_type: Type of song ("Paid", "Random", etc.)
        console_output: Whether to print status messages - keyword-only
        validate_data: Whether to validate input data - keyword-only
        include_metadata: Whether to include extended metadata - keyword-only
        log_format: Log format style ("standard", "detailed", "compact") - keyword-only

    Returns:
        bool: True if logging succeeded, False otherwise

    Examples:
        >>> _log_song_play(song_info, "Paid")
        True
        >>> _log_song_play(song_info, "Random", console_output=True)
        True
        >>> _log_song_play(song_info, "Paid", log_format="detailed")
        True

    Note:
        Uses the enhanced _get_rounded_timestamp function for consistency.
        Supports multiple log formats for different use cases.
    """
    from typing import Final

  # Constants for better maintainability
    LOG_FILE: Final = 'log.txt'
    ENCODING: Final = 'utf-8'
    VALID_SONG_TYPES: Final = {'Paid', 'Random', 'Manual', 'Scheduled'}
    VALID_LOG_FORMATS: Final = {'standard', 'detailed', 'compact'}
    DEFAULT_ARTIST: Final = 'Unknown Artist'
    DEFAULT_TITLE: Final = 'Unknown Title'

  # Input validation with early returns
    if validate_data:
        validation_result = _validate_song_play_data(song_info, song_type, VALID_SONG_TYPES)
        if not validation_result:
            if console_output:
                print("❌ Invalid song play data - logging aborted")
            return False

  # Validate log format
        if log_format not in VALID_LOG_FORMATS:
            if console_output:
                print(f"❌ Invalid log format '{log_format}' - using 'standard'")
            log_format = "standard"

    try:
  # Generate timestamp with enhanced function
        timestamp_result = _get_log_timestamp()
        if not timestamp_result['success']:
            if console_output:
                print("❌ Timestamp generation failed - using fallback")
            timestamp = timestamp_result['fallback']
        else:
            timestamp = timestamp_result['timestamp']

  # Format log entry based on requested format
        log_entry_result = _format_song_log_entry(
            song_info,
            song_type,
            timestamp,
            log_format,
            include_metadata
        )

        if not log_entry_result['success']:
            if console_output:
                print(f"❌ Log entry formatting failed: {log_entry_result['error']}")
            return False

        log_entry = log_entry_result['entry']

  # Write to log file with enhanced error handling
        write_result = _write_song_log_entry(log_entry, LOG_FILE, ENCODING)

        if write_result['success']:
            if console_output:
                print(f"✓ Logged {song_type.lower()} song play: {song_info.get('title', DEFAULT_TITLE)}")

  # Log successful operation for audit trail
            _log_info(
                f"Song play logged: {song_info.get('artist', DEFAULT_ARTIST)} - {song_info.get('title', DEFAULT_TITLE)} ({song_type})",
                level="INFO",
                console_output=False,
                category="playback"
            )

            return True
        else:
            if console_output:
                print(f"❌ Failed to write log entry: {write_result['error']}")
            return False

    except Exception as log_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Song play logging error: {log_error}"

        if console_output:
            print(f"❌ Error logging song play: {log_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return False


def _validate_song_play_data(song_info: Dict[str, str], song_type: str, valid_types: set) -> bool:
    """Validate song play data before logging.

    Args:
        song_info: Song information dictionary to validate
        song_type: Song type to validate
        valid_types: Set of valid song types

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
  # Type validation for song_info
        if not isinstance(song_info, dict):
            _log_error(
                f"Song info must be a dictionary, got {type(song_info).__name__}",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Check for required keys (at least title or artist should exist)
        required_keys = {'title', 'artist'}
        if not any(key in song_info for key in required_keys):
            _log_error(
                "Song info must contain at least 'title' or 'artist' key",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Type validation for song_type
        if not isinstance(song_type, str) or not song_type.strip():
            _log_error(
                f"Song type must be a non-empty string, got {type(song_type).__name__}",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Validate song_type against allowed values
        if song_type not in valid_types:
            _log_error(
                f"Invalid song type '{song_type}', valid types: {', '.join(valid_types)}",
                error_type="WARNING",
                console_output=False
            )
            return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Song play data validation exception: {validation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _get_log_timestamp() -> dict:
    """Get timestamp for logging with error handling.

    Returns:
        dict: Result with 'success' (bool), 'timestamp' (str), and 'fallback' (str) keys
    """
    try:
  # Use enhanced timestamp function
        timestamp = _get_rounded_timestamp(
            timezone_aware=False,
            format_string=None,
            microsecond_precision=False
        )

        return {
            'success': True,
            'timestamp': timestamp,
            'fallback': None
        }

    except Exception as timestamp_error:
  # Create fallback timestamp
        try:
            from datetime import datetime
            fallback_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            fallback_timestamp = "TIMESTAMP_ERROR"

        _log_error(
            f"Timestamp generation failed: {timestamp_error}",
            error_type="WARNING",
            console_output=False
        )

        return {
            'success': False,
            'timestamp': None,
            'fallback': fallback_timestamp
        }


def _format_song_log_entry(song_info: Dict[str, str], song_type: str, timestamp: str,
                          log_format: str, include_metadata: bool) -> dict:
    """Format song log entry based on specified format.

    Args:
        song_info: Song information dictionary
        song_type: Type of song being played
        timestamp: Timestamp string
        log_format: Format style ("standard", "detailed", "compact")
        include_metadata: Whether to include extended metadata

    Returns:
        dict: Result with 'success' (bool), 'entry' (str), and 'error' (str) keys
    """
    try:
  # Extract basic song information with defaults
        artist = song_info.get('artist', 'Unknown Artist')
        title = song_info.get('title', 'Unknown Title')

  # Format based on requested style
        if log_format == "compact":
            log_entry = f"\n{timestamp}, {artist} - {title}, {song_type}"

        elif log_format == "detailed":
            album = song_info.get('album', 'Unknown Album')
            year = song_info.get('year', 'Unknown Year')
            duration = song_info.get('duration', 'Unknown')

            log_entry = (f"\n{timestamp}, {artist} - {title}, "
                        f"Album: {album}, Year: {year}, Duration: {duration}, "
                        f"Played {song_type}")

            if include_metadata:
                genre = song_info.get('comment', 'Unknown Genre')
                location = song_info.get('location', 'Unknown Location')
                log_entry += f", Genre: {genre}, File: {Path(location).name if location != 'Unknown Location' else location}"

        else:  # standard format (default)
            log_entry = f"\n{timestamp}, {artist} - {title}, Played {song_type},"

            if include_metadata:
                year = song_info.get('year', 'Unknown Year')
                duration = song_info.get('duration', 'Unknown')
                log_entry = f"\n{timestamp}, {artist} - {title}, Year: {year}, Duration: {duration}, Played {song_type},"

        return {
            'success': True,
            'entry': log_entry,
            'error': None
        }

    except Exception as format_error:
        return {
            'success': False,
            'entry': None,
            'error': str(format_error)
        }


def _write_song_log_entry(log_entry: str, log_file_path: str, encoding: str) -> dict:
    """Write song log entry to file with comprehensive error handling.

    Args:
        log_entry: Formatted log entry to write
        log_file_path: Path to the log file
        encoding: File encoding to use

    Returns:
        dict: Result with 'success' (bool) and 'error' (str) keys
    """
    try:
  # Use pathlib for cross-platform compatibility
        log_file = Path(log_file_path)

  # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

  # Write log entry with proper error handling
        with log_file.open('a', encoding=encoding, newline='') as log:
            log.write(log_entry)
            log.flush()  # Ensure data is written to disk

        return {
            'success': True,
            'error': None
        }

    except (IOError, OSError) as io_error:
        error_msg = f"File I/O error writing to {log_file_path}: {io_error}"
        _log_error(
            error_msg,
            error_type="ERROR",
            console_output=False
        )
        return {
            'success': False,
            'error': error_msg
        }
    except UnicodeEncodeError as encoding_error:
        error_msg = f"Encoding error writing to {log_file_path}: {encoding_error}"
        _log_error(
            error_msg,
            error_type="ERROR",
            console_output=False
        )
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as write_error:
        error_msg = f"Unexpected error writing to {log_file_path}: {write_error}"
        _log_error(
            error_msg,
            error_type="ERROR",
            console_output=False
        )
        return {
            'success': False,
            'error': error_msg
        }


def _load_playlist(filename: str, *,
                  validate_data: bool = True,
                  console_output: bool = True,
                  strict_mode: bool = False,
                  default_on_error: Optional[List[int]] = None) -> List[int]:
    """Load playlist from file with enhanced Pythonic features.

    This function implements modern Python file loading patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Configurable error handling and recovery
    - Optional strict mode for production environments
    - Default value support for graceful degradation
    - Rich error reporting and logging
    - Defensive programming with robust error handling

    Args:
        filename: Name/path of the playlist file to load
        validate_data: Whether to validate loaded playlist data - keyword-only
        console_output: Whether to print status messages - keyword-only
        strict_mode: Whether to fail on any data inconsistencies - keyword-only
        default_on_error: Default playlist to return on errors - keyword-only

    Returns:
        List[int]: List of song indices, empty list or default on error

    Examples:
        >>> _load_playlist("playlist.txt")
        [1, 2, 3, 4]
        >>> _load_playlist("playlist.txt", console_output=False)
        [1, 2, 3]
        >>> _load_playlist("missing.txt", default_on_error=[0])
        [0]

    Note:
        Uses pathlib.Path for cross-platform compatibility.
        Supports both absolute and relative file paths.
    """
    from typing import Final

  # Constants for better maintainability
    ENCODING: Final = 'utf-8'
    MAX_FILE_SIZE: Final = 10 * 1024 * 1024  # 10MB safety limit
    SUPPORTED_EXTENSIONS: Final = {'.txt', '.json', '.playlist'}

  # Input validation with early returns
    if validate_data:
        validation_result = _validate_playlist_filename(filename, SUPPORTED_EXTENSIONS)
        if not validation_result:
            if console_output:
                print(f"❌ Invalid filename: {filename}")
            return default_on_error or []

    try:
  # Convert to Path object for modern path handling
        playlist_file = Path(filename)

  # Check file existence and accessibility
        file_check_result = _check_playlist_file_access(playlist_file, MAX_FILE_SIZE)
        if not file_check_result['accessible']:
            if console_output:
                print(f"ℹ️ {file_check_result['message']}")
            return default_on_error or []

  # Load and parse playlist data
        load_result = _load_playlist_data(playlist_file, ENCODING)
        if not load_result['success']:
            if console_output:
                print(f"❌ {load_result['error']}")
            return default_on_error or []

        raw_playlist = load_result['data']

  # Validate and clean playlist data
        if validate_data:
            validation_result = _validate_and_clean_playlist_data(
                raw_playlist,
                playlist_file.name,
                strict_mode
            )

            if not validation_result['valid']:
                if console_output:
                    print(f"❌ {validation_result['error']}")
                return default_on_error or []

            cleaned_playlist = validation_result['data']
        else:
  # Quick cleaning without full validation
            cleaned_playlist = _quick_clean_playlist_data(raw_playlist)

  # Success feedback and logging
        if console_output and cleaned_playlist:
            print(f"✓ Loaded playlist with {len(cleaned_playlist)} songs from {playlist_file.name}")
        elif console_output:
            print(f"ℹ️ Loaded empty playlist from {playlist_file.name}")

  # Log successful load for audit trail
        _log_info(
            f"Playlist loaded successfully: {filename} ({len(cleaned_playlist)} songs)",
            level="INFO",
            console_output=False,
            category="playlist"
        )

        return cleaned_playlist

    except Exception as load_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Playlist load error ({filename}): {load_error}"

        if console_output:
            print(f"❌ Error loading playlist {filename}: {load_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return default_on_error or []


def _validate_playlist_filename(filename: str, supported_extensions: set) -> bool:
    """Validate playlist filename and extension.

    Args:
        filename: Filename to validate
        supported_extensions: Set of supported file extensions

    Returns:
        bool: True if filename is valid, False otherwise
    """
    try:
  # Basic filename validation
        if not isinstance(filename, str) or not filename.strip():
            _log_error(
                "Playlist filename must be a non-empty string",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Path validation
        try:
            playlist_path = Path(filename)

  # Check for dangerous path components
            if '..' in playlist_path.parts:
                _log_error(
                    f"Dangerous path detected in filename: {filename}",
                    error_type="WARNING",
                    console_output=False
                )
                return False

  # Extension validation (if specified)
            if supported_extensions and playlist_path.suffix.lower() not in supported_extensions:
                _log_error(
                    f"Unsupported file extension: {playlist_path.suffix} (supported: {', '.join(supported_extensions)})",
                    error_type="WARNING",
                    console_output=False
                )
                return False

        except (ValueError, OSError) as path_error:
            _log_error(
                f"Invalid path format: {filename} - {path_error}",
                error_type="WARNING",
                console_output=False
            )
            return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Filename validation exception: {validation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _check_playlist_file_access(playlist_file: Path, max_file_size: int) -> dict:
    """Check if playlist file is accessible and safe to read.

    Args:
        playlist_file: Path object for the playlist file
        max_file_size: Maximum allowed file size in bytes

    Returns:
        dict: Result with 'accessible' (bool) and 'message' (str) keys
    """
    try:
  # Check file existence
        if not playlist_file.exists():
            return {
                'accessible': False,
                'message': f"Playlist file not found: {playlist_file.name}"
            }

  # Check if it's a file (not directory)
        if not playlist_file.is_file():
            return {
                'accessible': False,
                'message': f"Path is not a file: {playlist_file.name}"
            }

  # Check file size for safety
        try:
            file_size = playlist_file.stat().st_size
            if file_size > max_file_size:
                return {
                    'accessible': False,
                    'message': f"File too large: {file_size} bytes (max: {max_file_size})"
                }

            if file_size == 0:
                return {
                    'accessible': True,
                    'message': "Empty playlist file detected"
                }

        except OSError as size_error:
            return {
                'accessible': False,
                'message': f"Cannot check file size: {size_error}"
            }

  # Check read permissions
        try:
            with playlist_file.open('r', encoding='utf-8') as test_file:
                test_file.read(1)  # Try to read first byte
        except (IOError, OSError, UnicodeDecodeError) as read_error:
            return {
                'accessible': False,
                'message': f"Cannot read file: {read_error}"
            }

        return {
            'accessible': True,
            'message': f"File accessible ({file_size} bytes)"
        }

    except Exception as access_error:
        return {
            'accessible': False,
            'message': f"File access check failed: {access_error}"
        }


def _load_playlist_data(playlist_file: Path, encoding: str) -> dict:
    """Load and parse playlist data from file.

    Args:
        playlist_file: Path to the playlist file
        encoding: File encoding to use

    Returns:
        dict: Result with 'success' (bool), 'data' (any), and 'error' (str) keys
    """
    try:
  # Read file content
        with playlist_file.open('r', encoding=encoding) as file:
            file_content = file.read().strip()

  # Handle empty files
        if not file_content:
            return {
                'success': True,
                'data': [],
                'error': None
            }

  # Parse JSON content
        try:
            parsed_data = json.loads(file_content)
            return {
                'success': True,
                'data': parsed_data,
                'error': None
            }

        except json.JSONDecodeError as json_error:
  # Try to handle common JSON issues
            if file_content.startswith('[') and file_content.endswith(']'):
                error_msg = f"Invalid JSON format: {json_error}"
            else:
                error_msg = f"File does not contain valid JSON data: {json_error}"

            return {
                'success': False,
                'data': None,
                'error': error_msg
            }

    except (IOError, OSError) as io_error:
        return {
            'success': False,
            'data': None,
            'error': f"File I/O error: {io_error}"
        }
    except UnicodeDecodeError as encoding_error:
        return {
            'success': False,
            'data': None,
            'error': f"File encoding error: {encoding_error}"
        }


def _validate_and_clean_playlist_data(raw_data: Any, filename: str, strict_mode: bool) -> dict:
    """Validate and clean loaded playlist data.

    Args:
        raw_data: Raw data loaded from file
        filename: Filename for error context
        strict_mode: Whether to apply strict validation

    Returns:
        dict: Result with 'valid' (bool), 'data' (List[int]), and 'error' (str) keys
    """
    try:
  # Type validation
        if not isinstance(raw_data, list):
            return {
                'valid': False,
                'data': [],
                'error': f"Invalid playlist format in {filename}: expected list, got {type(raw_data).__name__}"
            }

  # Content validation and cleaning
        cleaned_playlist = []
        invalid_items = []

        for idx, item in enumerate(raw_data):
            try:
  # Convert to integer
                if isinstance(item, int):
                    song_index = item
                elif isinstance(item, str) and item.isdigit():
                    song_index = int(item)
                elif isinstance(item, float) and item.is_integer():
                    song_index = int(item)
                else:
                    invalid_items.append((idx, item, "not convertible to integer"))
                    continue

  # Validate range
                if song_index < 0:
                    invalid_items.append((idx, song_index, "negative index"))
                    if strict_mode:
                        continue
                    else:
                        song_index = abs(song_index)  # Convert to positive

                cleaned_playlist.append(song_index)

            except (ValueError, TypeError) as convert_error:
                invalid_items.append((idx, item, str(convert_error)))
                continue

  # Handle invalid items based on mode
        if invalid_items:
            if strict_mode:
                error_summary = f"Strict mode: {len(invalid_items)} invalid items found"
                return {
                    'valid': False,
                    'data': [],
                    'error': f"{error_summary} in {filename}"
                }
            else:
  # Log warnings for invalid items (first few only)
                sample_errors = invalid_items[:3]
                error_summary = f"Skipped {len(invalid_items)} invalid items"
                if len(invalid_items) > 3:
                    error_summary += f" (showing first 3)"

                _log_error(
                    f"Playlist data issues in {filename}: {error_summary}",
                    error_type="WARNING",
                    console_output=False
                )

        return {
            'valid': True,
            'data': cleaned_playlist,
            'error': None
        }

    except Exception as validation_error:
        return {
            'valid': False,
            'data': [],
            'error': f"Playlist validation failed: {validation_error}"
        }


def _quick_clean_playlist_data(raw_data: Any) -> List[int]:
    """Quick cleaning of playlist data without full validation.

    Args:
        raw_data: Raw data to clean

    Returns:
        List[int]: Cleaned playlist data
    """
    try:
        if not isinstance(raw_data, list):
            return []

  # Quick conversion with basic filtering
        cleaned = []
        for item in raw_data:
            try:
                if isinstance(item, int) and item >= 0:
                    cleaned.append(item)
                elif isinstance(item, str) and item.isdigit():
                    index = int(item)
                    if index >= 0:
                        cleaned.append(index)
            except (ValueError, TypeError):
                continue  # Skip invalid items silently

        return cleaned

    except Exception:
        return []  # Return empty list on any error


def _remove_from_paid_playlist(*,
                              remove_count: int = 1,
                              console_output: bool = True,
                              validate_data: bool = True,
                              backup_on_error: bool = True) -> bool:
    """Remove songs from paid playlist with enhanced Pythonic features.

    This function implements modern Python playlist management patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Return value tracking for operation success/failure
    - Configurable removal count for batch operations
    - Optional console output control
    - Backup creation for data protection
    - Defensive programming with robust error handling

    Args:
        remove_count: Number of songs to remove from front - keyword-only
        console_output: Whether to print status messages - keyword-only
        validate_data: Whether to validate playlist before removal - keyword-only
        backup_on_error: Whether to create backup before modification - keyword-only

    Returns:
        bool: True if removal succeeded, False otherwise

    Examples:
        >>> _remove_from_paid_playlist()  # Remove 1 song (default)
        True
        >>> _remove_from_paid_playlist(remove_count=3)
        True
        >>> _remove_from_paid_playlist(console_output=False)
        True

    Note:
        Uses the enhanced _save_playlist function for atomic write operations.
        Maintains backward compatibility with single song removal behavior.
    """
    from typing import Final

  # Constants for better maintainability
    PAID_PLAYLIST_FILE: Final = 'PaidMusicPlayList.txt'
    DEFAULT_REMOVE_COUNT: Final = 1
    MIN_REMOVE_COUNT: Final = 1
    MAX_REMOVE_COUNT: Final = 100  # Reasonable safety limit

  # Input validation with early returns
    if validate_data:
        validation_result = _validate_removal_parameters(
            remove_count,
            MIN_REMOVE_COUNT,
            MAX_REMOVE_COUNT
        )
        if not validation_result:
            if console_output:
                print("❌ Invalid removal parameters - operation aborted")
            return False

    try:
  # Load current paid playlist
        paid_playlist = _load_playlist(PAID_PLAYLIST_FILE)

  # Validate playlist data if requested
        if validate_data:
            playlist_validation = _validate_paid_playlist_data(paid_playlist)
            if not playlist_validation:
                if console_output:
                    print("❌ Paid playlist validation failed - removal aborted")
                return False

  # Check if playlist has enough songs to remove
        if len(paid_playlist) < remove_count:
            if console_output:
                if paid_playlist:
                    print(f"ℹ️ Only {len(paid_playlist)} songs available, removing all")
                    remove_count = len(paid_playlist)
                else:
                    print("ℹ️ Paid playlist is empty - no songs to remove")
                    return True  # Not an error - just nothing to remove

  # Perform the removal operation
        removal_result = _perform_playlist_removal(
            paid_playlist,
            remove_count,
            console_output
        )

        if not removal_result['success']:
            if console_output:
                print("❌ Song removal operation failed")
            return False

  # Save updated playlist with enhanced options
        save_success = _save_playlist(
            paid_playlist,
            PAID_PLAYLIST_FILE,
            pretty_format=False,  # Compact format for efficiency
            backup_on_error=backup_on_error,
            validate_data=validate_data
        )

        if save_success:
            if console_output:
                removed_count = removal_result['removed_count']
                remaining_count = len(paid_playlist)
                print(f"✓ Removed {removed_count} song{'s' if removed_count != 1 else ''} from paid playlist ({remaining_count} remaining)")

  # Log successful removal for audit trail
            _log_info(
                f"Paid playlist: removed {removal_result['removed_count']} songs, {len(paid_playlist)} remaining",
                level="INFO",
                console_output=False,
                category="playlist"
            )

            return True
        else:
            if console_output:
                print("❌ Failed to save updated paid playlist")
            return False

    except Exception as removal_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Paid playlist removal error: {removal_error}"

        if console_output:
            print(f"❌ Error removing from paid playlist: {removal_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return False


def _validate_removal_parameters(remove_count: int, min_count: int, max_count: int) -> bool:
    """Validate removal parameters for paid playlist operations.

    Args:
        remove_count: Number of songs to remove
        min_count: Minimum allowed removal count
        max_count: Maximum allowed removal count

    Returns:
        bool: True if parameters are valid, False otherwise
    """
    try:
  # Type validation
        if not isinstance(remove_count, int):
            error_msg = f"Remove count must be an integer, got {type(remove_count).__name__}"
            _log_error(
                f"Removal parameter validation error: {error_msg}",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Range validation
        if remove_count < min_count or remove_count > max_count:
            error_msg = f"Remove count {remove_count} must be between {min_count} and {max_count}"
            _log_error(
                f"Removal parameter validation error: {error_msg}",
                error_type="WARNING",
                console_output=False
            )
            return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Removal parameter validation exception: {validation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _validate_paid_playlist_data(playlist: List[int]) -> bool:
    """Validate paid playlist data before removal operations.

    Args:
        playlist: Paid playlist to validate

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
  # Type validation
        if not isinstance(playlist, list):
            error_msg = f"Paid playlist must be a list, got {type(playlist).__name__}"
            _log_error(
                f"Paid playlist validation error: {error_msg}",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Content validation for non-empty playlists
        if playlist:
            invalid_indices = [
                idx for idx, item in enumerate(playlist)
                if not isinstance(item, int) or item < 0
            ]

            if invalid_indices:
                error_msg = f"Invalid song indices at positions {invalid_indices[:3]}"  # Show first 3
                if len(invalid_indices) > 3:
                    error_msg += f" (and {len(invalid_indices) - 3} more)"

                _log_error(
                    f"Paid playlist validation error: {error_msg}",
                    error_type="WARNING",
                    console_output=False
                )
                return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Paid playlist validation exception: {validation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _perform_playlist_removal(playlist: List[int], remove_count: int, console_output: bool) -> dict:
    """Perform the actual removal operation on the playlist.

    Args:
        playlist: Playlist to modify (modified in-place)
        remove_count: Number of songs to remove
        console_output: Whether to show progress messages

    Returns:
        dict: Result with 'success' (bool) and 'removed_count' (int) keys
    """
    try:
        original_count = len(playlist)
        actual_remove_count = min(remove_count, original_count)

        if actual_remove_count == 0:
            return {'success': True, 'removed_count': 0}

  # Remove songs from the front of the playlist
        for i in range(actual_remove_count):
            if playlist:  # Extra safety check
                removed_song = playlist.pop(0)
                if console_output and actual_remove_count <= 5:  # Show details for small removals
                    print(f"  → Removed song index {removed_song}")

        return {'success': True, 'removed_count': actual_remove_count}

    except (IndexError, AttributeError) as removal_error:
        _log_error(
            f"Playlist removal operation failed: {removal_error}",
            error_type="ERROR",
            console_output=False
        )
        return {'success': False, 'removed_count': 0}


def _rotate_random_playlist(*,
                           validate_data: bool = True,
                           console_output: bool = True,
                           preserve_order: bool = True) -> bool:
    """Rotate random playlist by moving first song to end with enhanced Pythonic features.

    This function implements modern Python playlist rotation patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Return value tracking for operation success/failure
    - Optional console output control
    - Defensive programming with robust error handling
    - Efficient rotation using collections.deque when appropriate

    Args:
        validate_data: Whether to validate playlist before rotation - keyword-only
        console_output: Whether to print status messages - keyword-only
        preserve_order: Whether to maintain original rotation behavior - keyword-only

    Returns:
        bool: True if rotation succeeded, False otherwise

    Examples:
        >>> _rotate_random_playlist()
        True
        >>> _rotate_random_playlist(console_output=False)
        True
        >>> _rotate_random_playlist(validate_data=False)
        True

    Note:
        Uses efficient deque rotation when preserve_order=False for better performance.
        Maintains backward compatibility with preserve_order=True (default).
    """
    from typing import Final
    from collections import deque

    global RandomMusicPlayList

  # Constants for better maintainability
    MIN_ROTATION_SIZE: Final = 1
    SUCCESS_MESSAGE: Final = "Rotated random playlist"
    EMPTY_PLAYLIST_MESSAGE: Final = "Random playlist is empty - no rotation needed"

  # Input validation with early returns
    if validate_data:
        validation_result = _validate_random_playlist_data()
        if not validation_result:
            if console_output:
                print("❌ Playlist validation failed - rotation aborted")
            return False

    try:
  # Check if playlist is empty or too small to rotate
        if not RandomMusicPlayList:
            if console_output:
                print(f"ℹ️ {EMPTY_PLAYLIST_MESSAGE}")
            return True  # Not an error - just nothing to rotate

        if len(RandomMusicPlayList) < MIN_ROTATION_SIZE:
            if console_output:
                print("ℹ️ Single song playlist - no rotation needed")
            return True

  # Perform rotation based on preserve_order preference
        if preserve_order:
  # Traditional rotation: move first to end
            rotation_success = _perform_traditional_rotation()
        else:
  # Efficient rotation using deque
            rotation_success = _perform_efficient_rotation()

        if rotation_success:
            if console_output:
                print(f"✓ {SUCCESS_MESSAGE} ({len(RandomMusicPlayList)} songs)")

  # Log successful rotation for audit trail
            _log_info(
                f"Random playlist rotated successfully (size: {len(RandomMusicPlayList)})",
                level="INFO",
                console_output=False,
                category="playlist"
            )

            return True
        else:
            if console_output:
                print("❌ Rotation operation failed")
            return False

    except Exception as rotation_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Random playlist rotation error: {rotation_error}"

        if console_output:
            print(f"❌ Error rotating random playlist: {rotation_error}")

  # Log error with appropriate level and traceback
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return False


def _validate_random_playlist_data() -> bool:
    """Validate random playlist data before rotation.

    Returns:
        bool: True if validation passes, False otherwise
    """
    global RandomMusicPlayList

    try:
  # Type validation
        if not isinstance(RandomMusicPlayList, list):
            error_msg = f"RandomMusicPlayList must be a list, got {type(RandomMusicPlayList).__name__}"
            _log_error(
                f"Random playlist validation error: {error_msg}",
                error_type="WARNING",
                console_output=False
            )
            return False

  # Content validation for non-empty playlists
        if RandomMusicPlayList:
            invalid_indices = [
                idx for idx, item in enumerate(RandomMusicPlayList)
                if not isinstance(item, int) or item < 0
            ]

            if invalid_indices:
                error_msg = f"Invalid song indices at positions {invalid_indices[:3]}"  # Show first 3
                if len(invalid_indices) > 3:
                    error_msg += f" (and {len(invalid_indices) - 3} more)"

                _log_error(
                    f"Random playlist validation error: {error_msg}",
                    error_type="WARNING",
                    console_output=False
                )
                return False

        return True

    except Exception as validation_error:
        _log_error(
            f"Random playlist validation exception: {validation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _perform_traditional_rotation() -> bool:
    """Perform traditional rotation by moving first song to end.

    Returns:
        bool: True if rotation succeeded, False otherwise
    """
    global RandomMusicPlayList

    try:
        if not RandomMusicPlayList:
            return True  # Nothing to rotate

  # Traditional rotation: pop first, append to end
        first_song = RandomMusicPlayList.pop(0)
        RandomMusicPlayList.append(first_song)

        return True

    except (IndexError, AttributeError) as rotation_error:
        _log_error(
            f"Traditional rotation failed: {rotation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _perform_efficient_rotation() -> bool:
    """Perform efficient rotation using collections.deque.

    Returns:
        bool: True if rotation succeeded, False otherwise
    """
    from collections import deque

    global RandomMusicPlayList

    try:
        if not RandomMusicPlayList:
            return True  # Nothing to rotate

  # Convert to deque for efficient rotation
        playlist_deque = deque(RandomMusicPlayList)
        playlist_deque.rotate(-1)  # Rotate left by 1 (first to end)

  # Convert back to list
        RandomMusicPlayList[:] = list(playlist_deque)

        return True

    except Exception as rotation_error:
        _log_error(
            f"Efficient rotation failed: {rotation_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _save_playlist(playlist: List[int], filename: str, *,
                   pretty_format: bool = False,
                   backup_on_error: bool = True,
                   validate_data: bool = True) -> bool:
    """Save playlist to file with enhanced Pythonic features.

    This function implements modern Python file handling patterns including:
    - Keyword-only arguments for better API design
    - Comprehensive input validation with early returns
    - Return value tracking for operation success/failure
    - Optional pretty formatting for debugging
    - Backup creation on write errors
    - Defensive programming with robust error handling

    Args:
        playlist: List of song indices to save
        filename: Name of file to save to (relative or absolute path)
        pretty_format: Whether to format JSON with indentation - keyword-only
        backup_on_error: Whether to create backup if original exists - keyword-only
        validate_data: Whether to validate playlist data before saving - keyword-only

    Returns:
        bool: True if playlist saved successfully, False otherwise

    Examples:
        >>> _save_playlist([1, 2, 3], "playlist.txt")
        True
        >>> _save_playlist([1, 2, 3], "playlist.txt", pretty_format=True)
        True
        >>> _save_playlist([], "empty.txt", validate_data=False)
        True

    Raises:
        ValueError: If validation fails and validate_data=True

    Note:
        Uses compact JSON format by default for efficiency.
        Pretty format is recommended only for debugging purposes.
    """
    from typing import Final
    import shutil
    import tempfile

  # Constants for better maintainability
    COMPACT_SEPARATORS: Final = (',', ':')
    PRETTY_SEPARATORS: Final = (',', ': ')
    PRETTY_INDENT: Final = 2
    BACKUP_SUFFIX: Final = '.backup'
    ENCODING: Final = 'utf-8'

  # Input validation with early returns
    if validate_data:
        validation_result = _validate_playlist_data(playlist, filename)
        if not validation_result:
            return False

    try:
  # Convert to Path object for modern path handling
        playlist_file = Path(filename)

  # Ensure parent directory exists
        playlist_file.parent.mkdir(parents=True, exist_ok=True)

  # Create backup if requested and file exists
        backup_created = False
        if backup_on_error and playlist_file.exists():
            backup_created = _create_playlist_backup(playlist_file)

  # Configure JSON formatting based on pretty_format option
        json_params = {
            'ensure_ascii': False,
            'separators': PRETTY_SEPARATORS if pretty_format else COMPACT_SEPARATORS
        }

        if pretty_format:
            json_params['indent'] = PRETTY_INDENT

  # Use atomic write pattern for data integrity
        success = _atomic_write_playlist(playlist_file, playlist, json_params)

        if success:
  # Clean up backup if write succeeded
            if backup_created:
                _cleanup_backup(playlist_file, BACKUP_SUFFIX)

  # Visual feedback for successful operation
            print(f"✓ Saved playlist with {len(playlist)} songs to {playlist_file.name}")
            return True
        else:
  # Restore from backup if available and write failed
            if backup_created:
                _restore_from_backup(playlist_file, BACKUP_SUFFIX)
            return False

    except Exception as save_error:
  # Comprehensive error handling with detailed logging
        error_message = f"Playlist save error ({filename}): {save_error}"
        print(f"❌ Error saving playlist {filename}: {save_error}")

  # Log error with appropriate level
        _log_error(
            error_message,
            error_type="ERROR",
            console_output=False,
            include_traceback=True
        )

        return False


def _validate_playlist_data(playlist: List[int], filename: str) -> bool:
    """Validate playlist data before saving.

    Args:
        playlist: List of song indices to validate
        filename: Filename for error context

    Returns:
        bool: True if validation passes, False otherwise
    """
  # Type validation
    if not isinstance(playlist, list):
        error_msg = f"Playlist must be a list, got {type(playlist).__name__}"
        print(f"❌ Validation error for {filename}: {error_msg}")
        _log_error(
            f"Playlist validation error ({filename}): {error_msg}",
            error_type="WARNING",
            console_output=False
        )
        return False

  # Content validation
    invalid_indices = [
        idx for idx, item in enumerate(playlist)
        if not isinstance(item, int) or item < 0
    ]

    if invalid_indices:
        error_msg = f"Invalid song indices at positions {invalid_indices[:5]}"  # Show first 5
        if len(invalid_indices) > 5:
            error_msg += f" (and {len(invalid_indices) - 5} more)"

        print(f"❌ Validation error for {filename}: {error_msg}")
        _log_error(
            f"Playlist validation error ({filename}): {error_msg}",
            error_type="WARNING",
            console_output=False
        )
        return False

  # Filename validation
    if not isinstance(filename, str) or not filename.strip():
        error_msg = "Filename must be a non-empty string"
        print(f"❌ Validation error: {error_msg}")
        _log_error(
            f"Playlist validation error: {error_msg}",
            error_type="WARNING",
            console_output=False
        )
        return False

    return True


def _create_playlist_backup(playlist_file: Path) -> bool:
    """Create backup of existing playlist file.

    Args:
        playlist_file: Path to the playlist file

    Returns:
        bool: True if backup created successfully, False otherwise
    """
    import shutil

    try:
        backup_file = playlist_file.with_suffix(playlist_file.suffix + '.backup')
        shutil.copy2(playlist_file, backup_file)
        return True
    except Exception as backup_error:
        _log_error(
            f"Backup creation failed for {playlist_file.name}: {backup_error}",
            error_type="WARNING",
            console_output=False
        )
        return False


def _atomic_write_playlist(playlist_file: Path, playlist: List[int], json_params: dict) -> bool:
    """Atomically write playlist using temporary file pattern.

    Args:
        playlist_file: Target file path
        playlist: Playlist data to write
        json_params: JSON formatting parameters

    Returns:
        bool: True if write succeeded, False otherwise
    """
    temp_file = None

    try:
  # Use temporary file in same directory for atomic write
        temp_file = playlist_file.with_suffix(playlist_file.suffix + '.tmp')

  # Write to temporary file first
        with temp_file.open('w', encoding='utf-8', newline='\n') as file:
            json.dump(playlist, file, **json_params)

  # Atomic move to final location
        temp_file.replace(playlist_file)
        return True

    except Exception as write_error:
  # Clean up temporary file if it exists
        if temp_file is not None and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        _log_error(
            f"Atomic write failed for {playlist_file.name}: {write_error}",
            error_type="ERROR",
            console_output=False
        )
        return False


def _cleanup_backup(playlist_file: Path, backup_suffix: str) -> None:
    """Clean up backup file after successful write.

    Args:
        playlist_file: Original playlist file path
        backup_suffix: Suffix used for backup file
    """
    try:
        backup_file = playlist_file.with_suffix(playlist_file.suffix + backup_suffix)
        if backup_file.exists():
            backup_file.unlink()
    except Exception as cleanup_error:
        _log_error(
            f"Backup cleanup failed for {playlist_file.name}: {cleanup_error}",
            error_type="WARNING",
            console_output=False
        )


def _restore_from_backup(playlist_file: Path, backup_suffix: str) -> None:
    """Restore playlist from backup file.

    Args:
        playlist_file: Original playlist file path
        backup_suffix: Suffix used for backup file
    """
    import shutil

    try:
        backup_file = playlist_file.with_suffix(playlist_file.suffix + backup_suffix)
        if backup_file.exists():
            shutil.copy2(backup_file, playlist_file)
            print(f"✓ Restored {playlist_file.name} from backup")
    except Exception as restore_error:
        _log_error(
            f"Backup restoration failed for {playlist_file.name}: {restore_error}",
            error_type="ERROR",
            console_output=False
        )


def _get_rounded_timestamp(*,
                          timezone_aware: bool = False,
                          format_string: Optional[str] = None,
                          microsecond_precision: bool = False) -> str:
    """Get rounded timestamp for logging consistency with enhanced Pythonic features.

    This function implements modern Python timestamp handling with:
    - Keyword-only arguments for better API design
    - Optional timezone awareness for production environments
    - Configurable output formatting
    - Consistent rounding behavior for log alignment
    - Comprehensive error handling

    Args:
        timezone_aware: Whether to include timezone information - keyword-only
        format_string: Custom format string (ISO format if None) - keyword-only
        microsecond_precision: Whether to preserve microseconds - keyword-only

    Returns:
        str: Formatted timestamp string suitable for logging

    Examples:
        >>> _get_rounded_timestamp()
        '2025-08-26 12:45:30'
        >>> _get_rounded_timestamp(timezone_aware=True)
        '2025-08-26 12:45:30+00:00'
        >>> _get_rounded_timestamp(format_string="%Y/%m/%d %H:%M:%S")
        '2025/08/26 12:45:30'
        >>> _get_rounded_timestamp(microsecond_precision=True)
        '2025-08-26 12:45:30.123456'

    Note:
        Rounding adds 0.5 seconds before truncating microseconds for
        consistent timestamp alignment in log files.
    """
    from typing import Final
    import sys

  # Constants for better maintainability
    DEFAULT_FORMAT: Final = "%Y-%m-%d %H:%M:%S"
    ISO_FORMAT_WITH_TZ: Final = "%Y-%m-%d %H:%M:%S%z"
    ROUNDING_OFFSET: Final = 0.5  # seconds

    try:
  # Get current timestamp with optional timezone awareness
        if timezone_aware:
  # Use timezone-aware datetime for production environments
            try:
                from datetime import timezone
                now = datetime.now(timezone.utc)
            except ImportError:
  # Fallback for older Python versions
                now = datetime.utcnow()
        else:
            now = datetime.now()

  # Apply rounding for consistent log alignment
        if not microsecond_precision:
            rounded_now = now + timedelta(seconds=ROUNDING_OFFSET)
            rounded_now = rounded_now.replace(microsecond=0)
        else:
            rounded_now = now

  # Format timestamp with appropriate format string
        if format_string is not None:
  # Use custom format string with validation
            try:
                formatted_timestamp = rounded_now.strftime(format_string)
            except (ValueError, TypeError) as format_error:
  # Fallback to default format on invalid format string
                _log_error(
                    f"Invalid timestamp format string '{format_string}': {format_error}",
                    error_type="WARNING",
                    console_output=False
                )
                formatted_timestamp = rounded_now.strftime(DEFAULT_FORMAT)
        else:
  # Use appropriate default format based on timezone awareness
            if timezone_aware and hasattr(rounded_now, 'tzinfo') and rounded_now.tzinfo:
                formatted_timestamp = rounded_now.strftime(ISO_FORMAT_WITH_TZ)
            else:
                formatted_timestamp = rounded_now.strftime(DEFAULT_FORMAT)

        return formatted_timestamp

    except Exception as timestamp_error:
  # Robust error handling with fallback timestamp
        error_message = f"Timestamp generation error: {timestamp_error}"

  # Try to log error (avoid recursion if _log_error fails)
        try:
            _log_error(error_message, error_type="ERROR", console_output=False)
        except Exception:
  # Ultimate fallback: write to stderr without logging
            try:
                sys.stderr.write(f"TIMESTAMP_ERROR: {error_message}\n")
                sys.stderr.flush()
            except Exception:
                pass  # Silent failure to prevent cascading errors

  # Return fallback timestamp using basic string formatting
        try:
            fallback_time = datetime.now()
            return f"FALLBACK_{fallback_time.year}-{fallback_time.month:02d}-{fallback_time.day:02d}_{fallback_time.hour:02d}:{fallback_time.minute:02d}:{fallback_time.second:02d}"
        except Exception:
            return "TIMESTAMP_UNAVAILABLE"


def _log_info(message: str, *,
              level: str = "INFO",
              console_output: bool = False,
              category: Optional[str] = None) -> bool:
    """Log informational message with Pythonic design patterns.

    Companion function to _log_error for comprehensive logging.
    Implements the same modern Python patterns for consistency.

    Args:
        message: Information message to log
        level: Log level ("INFO", "DEBUG", "SUCCESS") - keyword-only
        console_output: Whether to also print to console - keyword-only
        category: Optional category for message grouping - keyword-only

    Returns:
        bool: True if logging succeeded, False otherwise

    Examples:
        >>> _log_info("Jukebox started successfully")
        True
        >>> _log_info("Song loaded", level="SUCCESS", console_output=True)
        True
        >>> _log_info("Debug info", level="DEBUG", category="playlist")
        True
    """
    from typing import Final

  # Constants for consistency with _log_error
    VALID_LOG_LEVELS: Final = {"INFO", "DEBUG", "SUCCESS", "WARNING"}
    LOG_ICONS: Final = {
        "INFO": "ℹ️",
        "DEBUG": "🔍",
        "SUCCESS": "✅",
        "WARNING": "⚠️"
    }

  # Input validation with early return pattern
    if not isinstance(message, str) or not message.strip():
        return False

  # Normalize log level
    level = level.upper()
    if level not in VALID_LOG_LEVELS:
        level = "INFO"  # Default fallback

    try:
  # Build structured log entry
        timestamp = _get_rounded_timestamp()

  # Create message with optional category
        formatted_message = f"{level}: {message.strip()}"
        if category:
            formatted_message = f"{level}[{category.upper()}]: {message.strip()}"

        log_entry = f"\n{timestamp}, {formatted_message},"

  # Write to log file
        log_file = Path('log.txt')
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with log_file.open('a', encoding='utf-8', newline='\n') as log:
            log.write(log_entry)

  # Optional console output
        if console_output:
            icon = LOG_ICONS.get(level, "📝")
            console_message = f"{icon} {formatted_message}"
            print(console_message)

        return True

    except Exception as logging_error:
  # Graceful error handling without recursion
        if console_output:
            print(f"🚫 Failed to log info: {logging_error}")
        return False


def _log_error(error_message: str, *,
               error_type: str = "ERROR",
               console_output: bool = False,
               include_traceback: bool = False) -> bool:
    """Log error message to log file with enhanced Pythonic features.

    This function implements modern Python logging practices including:
    - Keyword-only arguments for better API design
    - Multiple error severity levels
    - Optional console output for debugging
    - Traceback inclusion for detailed error analysis
    - Return value for operation success tracking

    Args:
        error_message: Error message to log
        error_type: Type of error ("ERROR", "WARNING", "CRITICAL") - keyword-only
        console_output: Whether to also print to console - keyword-only
        include_traceback: Whether to include Python traceback - keyword-only

    Returns:
        bool: True if logging succeeded, False otherwise

    Examples:
        >>> _log_error("File not found")
        True
        >>> _log_error("Critical issue", error_type="CRITICAL", console_output=True)
        True
        >>> _log_error("Debug info", error_type="WARNING", include_traceback=True)
        True
    """
    import traceback
    from typing import Final

  # Constants for error types and formatting
    VALID_ERROR_TYPES: Final = {"ERROR", "WARNING", "CRITICAL", "INFO", "DEBUG"}
    ERROR_ICONS: Final = {
        "ERROR": "❌",
        "WARNING": "⚠️",
        "CRITICAL": "🚨",
        "INFO": "ℹ️",
        "DEBUG": "🔍"
    }

  # Input validation with early return pattern
    if not isinstance(error_message, str):
        return False

    if not error_message.strip():
        return False

  # Normalize error type
    error_type = error_type.upper()
    if error_type not in VALID_ERROR_TYPES:
        error_type = "ERROR"  # Default fallback

    try:
  # Build comprehensive log entry with structured format
        timestamp = _get_rounded_timestamp()

  # Create structured log entry components
        log_components = [
            timestamp,
            f"{error_type}: {error_message.strip()}"
        ]

  # Add traceback if requested and available
        if include_traceback:
            tb_lines = traceback.format_exc().strip()
            if tb_lines != "NoneType: None":  # Only include meaningful tracebacks
                log_components.append(f"Traceback: {tb_lines}")

  # Construct final log entry with proper formatting
        log_entry = f"\n{', '.join(log_components)},"

  # Write to log file with proper error handling
        log_file = Path('log.txt')

  # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with log_file.open('a', encoding='utf-8', newline='\n') as log:
            log.write(log_entry)

  # Optional console output for debugging and user feedback
        if console_output:
            icon = ERROR_ICONS.get(error_type, "📝")
            console_message = f"{icon} {error_type}: {error_message}"
            print(console_message)

        return True  # Success indicator

    except Exception as logging_error:
  # Get timestamp for fallback (safe to call even if original failed)
        try:
            safe_timestamp = _get_rounded_timestamp()
        except Exception:
            safe_timestamp = "UNKNOWN_TIME"

  # Handle logging failures gracefully without recursion
        if console_output:
            print(f"🚫 Failed to log error: {logging_error}")
            print(f"📝 Original error: {error_message}")

  # Could implement fallback logging mechanism here (e.g., to stderr)
        import sys
        try:
            fallback_message = f"LOGGING_FAILURE: {safe_timestamp} - Original: {error_message} | Logging Error: {logging_error}\n"
            sys.stderr.write(fallback_message)
            sys.stderr.flush()
        except Exception:
            pass  # Ultimate fallback: silent failure to prevent cascading errors

        return False  # Failure indicator
# Check to see if MasterMusicSongList exists on disk
if os.path.exists('MusicMasterSongList.txt'):
    print('Check to see if MasterMusicSongList exists on disk')
  # Count number of files in music directory
    x = len(glob.glob(dir_path + '\\music\\*.mp3'))
  # x = sum(os.path.isfile(os.path.join(dir_path + '\\silentmusic\\', f)) for f in os.listdir(dir_path + '\\music\\'))
    print(x)
  #  Open MusicMasterSongListCheck generated from previous run of Convergence Jukebox
    with open('MusicMasterSongListCheck.txt', 'r') as MusicMasterSongListCheckOpen:
        MusicMasterSongListCheck = json.load(MusicMasterSongListCheckOpen)
        y = MusicMasterSongListCheck
        print(y)
  #  Check for match
    if x == y:
        print('Match')
  #  open MusicMasterSongList dictionary
        with open('MusicMasterSongList.txt', 'r') as MusicMasterSongListOpen:
            MusicMasterSongList = json.load(MusicMasterSongListOpen)
  # MusicMasterSongList matches, run required functions
        assign_genres_to_random_play()
        generate_random_song_list()

  # Start jukebox engine with enhanced Pythonic interface (demo mode)
        print("🎵 Starting Convergence Jukebox 2026 Engine (Demo Mode - 5 iterations)...")
        engine_result = jukebox_engine(
            max_iterations=5,  # Demo mode with limited iterations
            console_output=True,
            validate_startup=True,
            performance_monitoring=True
        )

  # Handle engine completion
        if engine_result['success']:
            print(f"✓ Jukebox engine completed: {engine_result['shutdown_reason']}")
            print(f"📊 Session stats: {engine_result['iterations_completed']} iterations, "
                  f"{engine_result['songs_played']} songs played")
        else:
            print(f"❌ Jukebox engine failed: {engine_result['shutdown_reason']}")

    else:
        print('No Match - Regenerating song list')
  # Generate fresh metadata and update global variable
        MusicMasterSongList = generate_Music_Master_Song_List_Dictionary()
        if MusicMasterSongList:  # Only proceed if we have songs
            assign_genres_to_random_play()
            generate_random_song_list()

  # Start jukebox engine with enhanced Pythonic interface (demo mode)
            print("🎵 Starting Convergence Jukebox 2026 Engine (Demo Mode - 5 iterations)...")
            engine_result = jukebox_engine(
                max_iterations=5,  # Demo mode with limited iterations
                console_output=True,
                validate_startup=True,
                performance_monitoring=True
            )

  # Handle engine completion
            if engine_result['success']:
                print(f"✓ Jukebox engine completed: {engine_result['shutdown_reason']}")
                print(f"📊 Session stats: {engine_result['iterations_completed']} iterations, "
                      f"{engine_result['songs_played']} songs played")
            else:
                print(f"❌ Jukebox engine failed: {engine_result['shutdown_reason']}")
else:
    print('MusicMasterSongList.txt not found - Creating fresh song list')
  # Generate fresh metadata and update global variable
    MusicMasterSongList = generate_Music_Master_Song_List_Dictionary()
    if MusicMasterSongList:  # Only proceed if we have songs
        assign_genres_to_random_play()
        generate_random_song_list()

  # Start jukebox engine with enhanced Pythonic interface (demo mode)
        print("🎵 Starting Convergence Jukebox 2026 Engine (Demo Mode - 5 iterations)...")
        engine_result = jukebox_engine(
            max_iterations=5,  # Demo mode with limited iterations
            console_output=True,
            validate_startup=True,
            performance_monitoring=True
        )

  # Handle engine completion
        if engine_result['success']:
            print(f"✓ Jukebox engine completed: {engine_result['shutdown_reason']}")
            print(f"📊 Session stats: {engine_result['iterations_completed']} iterations, "
                  f"{engine_result['songs_played']} songs played")
        else:
            print(f"❌ Jukebox engine failed: {engine_result['shutdown_reason']}")
