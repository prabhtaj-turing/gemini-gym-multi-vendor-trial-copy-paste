"""
Media Control Service Implementation

This module provides the core functionality for managing Android Media Control,
including playback control, seeking, and rating capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, Any
from .SimulationEngine import utils
from .SimulationEngine.db_models import MediaPlayer
from .SimulationEngine.models import PlaybackTargetState

from .SimulationEngine.custom_errors import (
    ValidationError, NoMediaPlayerError, NoMediaPlayingError, 
    NoMediaItemError, InvalidPlaybackStateError, NoPlaylistError
)

@tool_spec(
    spec={
        'name': 'change_playback_state',
        'description': """ Changes the playback state of the media player.
        
        This function can pause, resume, or stop media playback. It works with media
        in any current state (playing, paused, or stopped) and will perform the
        appropriate state transition based on the target_state parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'target_state': {
                    'type': 'string',
                    'description': 'The target playback state (STOP, PAUSE, RESUME)'
                },
                'app_name': {
                    'type': 'string',
                    'description': 'Optional; the name of the media application. Defaults to None, which targets the active media player.'
                }
            },
            'required': [
                'target_state'
            ]
        }
    }
)
def change_playback_state(
    target_state: str,
    app_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Changes the playback state of the media player.
    
    This function can pause, resume, or stop media playback. It works with media
    in any current state (playing, paused, or stopped) and will perform the
    appropriate state transition based on the target_state parameter.
    
    Args:
        target_state (str): The target playback state (STOP, PAUSE, RESUME)
        app_name (Optional[str]): Optional; the name of the media application. Defaults to None, which targets the active media player.
        
    Returns:
        Dict[str, Any]: Dictionary containing action summary on success, error message on failure.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        ValidationError: If target_state or app_name is invalid
        NoMediaPlayerError: If no media player is found for the specified app
        NoMediaItemError: If no media item is currently loaded
        InvalidPlaybackStateError: If the requested state change is not valid for current state
    """
    # Validate input parameters
    if not isinstance(target_state, str):
        raise ValidationError(f"target_state must be a string, got {type(target_state).__name__}")
    if target_state == "":
        raise ValidationError("target_state cannot be an empty string")
    
    # Validate target_state is a valid enum value
    valid_states = [state.value for state in PlaybackTargetState]
    if target_state not in valid_states:
        raise ValidationError(f"target_state must be one of {valid_states}, got '{target_state}'")
    
    if app_name is not None:
        if not isinstance(app_name, str):
            raise ValidationError(f"app_name must be a string, got {type(app_name).__name__}")
        if app_name == "":
            raise ValidationError("app_name cannot be an empty string")
    
    # Convert string to enum
    target_state_enum = PlaybackTargetState(target_state)
    
    # Get the media player
    player_data = utils.get_media_player(app_name) if app_name else utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError(f"No media player found for app: {app_name or 'Unknown'}")
    
    # Check if there's media to control (for PAUSE and RESUME operations)
    if target_state_enum in [PlaybackTargetState.PAUSE, PlaybackTargetState.RESUME]:
        if not player_data.get("current_media"):
            raise NoMediaItemError("No media item is currently loaded")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use the appropriate MediaPlayer method based on target_state
    if target_state_enum == PlaybackTargetState.PAUSE:
        result = player.pause_media()
    elif target_state_enum == PlaybackTargetState.RESUME:
        result = player.resume_media()
    else:  # STOP
        result = player.stop_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    
    # Return as dict
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'pause',
        'description': 'Pause the currently playing media.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def pause() -> Dict[str, Any]:
    """
    Pause the currently playing media.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully changing the state of media playback.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
    
    Raises:
        NoMediaPlayerError: If there is no active media player
        NoMediaItemError: If no media item is currently loaded
        InvalidPlaybackStateError: If media cannot be paused in current state
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method (it handles validation internally)
    result = player.pause_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'stop',
        'description': 'Stop the currently playing media.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def stop() -> Dict[str, Any]:
    """
    Stop the currently playing media.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully changing the state of media playback.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        NoMediaPlayerError: If there is no active media player
        NoMediaItemError: If no media item is currently loaded
        InvalidPlaybackStateError: If media is already stopped
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method (it handles validation internally)
    result = player.stop_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'resume',
        'description': """ Resume playback of the currently paused media from where it was paused.
        
        This function continues playback of media that was previously paused, maintaining
        the exact position where playback was stopped. Unlike play() which starts from
        the beginning, resume() preserves the user's progress through the media.
        
        If the media is already playing, this function will return a success response
        without changing the playback state (no-op behavior). """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def resume() -> Dict[str, Any]:
    """
    Resume playback of the currently paused media from where it was paused.
    
    This function continues playback of media that was previously paused, maintaining
    the exact position where playback was stopped. Unlike play() which starts from
    the beginning, resume() preserves the user's progress through the media.
    
    If the media is already playing, this function will return a success response
    without changing the playback state (no-op behavior).
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully resuming media playback.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        NoMediaPlayerError: If there is no active media player
        InvalidPlaybackStateError: If media cannot be resumed (must be in PAUSED or PLAYING state)
        NoMediaItemError: If no media item is currently loaded
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Store original state to check if it changed
    original_state = player.playback_state
    
    # Use MediaPlayer method
    result = player.resume_media()
    
    # Only save to database if the state actually changed (not a no-op)
    if player.playback_state != original_state:
        utils.save_media_player(player.model_dump())
    
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'next',
        'description': 'Skip to the next media item.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def next() -> Dict[str, Any]:
    """
    Skip to the next media item.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully changing the media playback position.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        NoMediaPlayerError: If there is no active media player
        NoPlaylistError: If no playlist is available in the app
        InvalidPlaybackStateError: If already at the last item in playlist
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Check if there's a playlist available
    if not player_data.get("playlist"):
        raise NoPlaylistError(f"No playlist available in app: {player_data['app_name']}")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method
    result = player.next_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'previous',
        'description': 'Skip to the previous media item.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def previous() -> Dict[str, Any]:
    """
    Skip to the previous media item.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully changing the media playback position.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        NoMediaPlayerError: If there is no active media player
        NoPlaylistError: If no playlist is available in the app
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Check if there's a playlist available
    if not player_data.get("playlist"):
        raise NoPlaylistError(f"No playlist available in app: {player_data['app_name']}")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method
    result = player.previous_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'replay',
        'description': 'Replay the current media item from the beginning.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def replay() -> Dict[str, Any]:
    """
    Replay the current media item from the beginning.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully changing the media playback position.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        NoMediaPlayerError: If there is no active media player
        NoMediaItemError: If no media item is loaded in the app
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method
    result = player.replay_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'seek_relative',
        'description': 'Adjusts media playback by a specified duration relative to the current position, then resumes playing.',
        'parameters': {
            'type': 'object',
            'properties': {
                'offset': {
                    'type': 'integer',
                    'description': """ Relative offset in seconds from the current playback position.
                    Positive values fast forward; negative values rewind. """
                }
            },
            'required': [
                'offset'
            ]
        }
    }
)
def seek_relative(offset: int) -> Dict[str, Any]:
    """
    Adjusts media playback by a specified duration relative to the current position, then resumes playing.
    
    Args:
        offset (int): Relative offset in seconds from the current playback position.
                     Positive values fast forward; negative values rewind.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully changing the media playback position.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        ValidationError: If offset is not an integer
        NoMediaPlayerError: If there is no active media player
        NoMediaItemError: If no media item is loaded in the app
    """
    if not isinstance(offset, int):
        raise ValidationError(f"offset must be an integer, got {type(offset).__name__}")
    
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Check if there's media to seek
    if not player_data.get("current_media"):
        raise NoMediaItemError(f"No media item loaded in app: {player_data['app_name']}")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method (it handles validation and clamping internally)
    result = player.seek_relative(offset)
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'seek_absolute',
        'description': 'Jumps to a specific position in the media, then resumes playing.',
        'parameters': {
            'type': 'object',
            'properties': {
                'position': {
                    'type': 'integer',
                    'description': 'Absolute position in the media in seconds.'
                }
            },
            'required': [
                'position'
            ]
        }
    }
)
def seek_absolute(position: int) -> Dict[str, Any]:
    """
    Jumps to a specific position in the media, then resumes playing.
    
    Args:
        position (int): Absolute position in the media in seconds.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully changing the media playback position.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        ValidationError: If position is not an integer
        NoMediaPlayerError: If there is no active media player
        NoMediaItemError: If no media item is loaded in the app
    """
    if not isinstance(position, int):
        raise ValidationError(f"position must be an integer, got {type(position).__name__}")
    
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Check if there's media to seek
    if not player_data.get("current_media"):
        raise NoMediaItemError(f"No media item loaded in app: {player_data['app_name']}")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method (it handles validation and clamping internally)
    result = player.seek_absolute(position)
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'like',
        'description': 'Like the currently playing media.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def like() -> Dict[str, Any]:
    """
    Like the currently playing media.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully setting the media attribute.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        NoMediaPlayerError: If there is no active media player
        NoMediaItemError: If no media item is loaded in the app
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method
    result = player.like_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result


@tool_spec(
    spec={
        'name': 'dislike',
        'description': 'Dislike the currently playing media.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def dislike() -> Dict[str, Any]:
    """
    Dislike the currently playing media.
    
    Returns:
        Dict[str, Any]: Dictionary containing the result of successfully setting the media attribute.
        The dictionary contains:
        - result (str): Result of the action
        - title (str): Title of the media item
        - app_name (str): App playing the media
        - media_type (str): Type of the media item
        
    Raises:
        NoMediaPlayerError: If there is no active media player
        NoMediaItemError: If no media item is loaded in the app
    """
    player_data = utils.get_active_media_player()
    if not player_data:
        raise NoMediaPlayerError("No active media player found")
    
    # Convert dictionary to MediaPlayer model
    player = MediaPlayer(**player_data)
    
    # Use MediaPlayer method
    result = player.dislike_media()
    
    # Save the updated player state back to database
    utils.save_media_player(player.model_dump())
    return result.model_dump() if hasattr(result, 'model_dump') else result
