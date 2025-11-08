"""
Channels resource for Google Drive API simulation.

This module provides methods for managing channels in the Google Drive API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Union, Optional
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _ensure_channels
from .SimulationEngine.models import ChannelResourceModel
from .SimulationEngine.custom_errors import ValidationError, ChannelNotFoundError

@tool_spec(
    spec={
        'name': 'stop_channel_watch',
        'description': 'Stops watching resources through this channel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'resource': {
                    'type': 'object',
                    'description': 'Dictionary of channel properties. If None or empty dictionary, no action is taken. Channel properties:',
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': 'The ID of the channel to stop.'
                        },
                        'resourceId': {
                            'type': 'string',
                            'description': 'The ID of the resource being watched.'
                        },
                        'resourceUri': {
                            'type': 'string',
                            'description': 'The URI of the resource being watched.'
                        },
                        'token': {
                            'type': 'string',
                            'description': 'The token used to authenticate the channel.'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'The type of the channel.'
                        },
                        'address': {
                            'type': 'string',
                            'description': 'The address where notifications are delivered.'
                        },
                        'expiration': {
                            'type': 'string',
                            'description': 'The time at which the channel will expire (RFC3339 format).'
                        },
                        'payload': {
                            'type': 'boolean',
                            'description': 'Whether to include the payload in notifications.'
                        },
                        'params': {
                            'type': 'object',
                            'description': """ Additional parameters controlling delivery channel behavior.
                                 An object containing a list of key: value pairs. Example: { "name": "wrench", "mass": "1.3kg", "count": "3" }. """,
                            'properties': {},
                            'required': []
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def stop(resource: Optional[Dict[str, Union[str, bool]]] = None) -> None:
    """Stops watching resources through this channel.
    
    Args:
        resource (Optional[Dict[str, Union[str, bool]]]): Dictionary of channel properties. If None or empty dictionary, no action is taken. Channel properties:
            - 'id' (Optional[str]): The ID of the channel to stop.
            - 'resourceId' (Optional[str]): The ID of the resource being watched.
            - 'resourceUri' (Optional[str]): The URI of the resource being watched.
            - 'token' (Optional[str]): The token used to authenticate the channel.
            - 'type' (Optional[str]): The type of the channel.
            - 'address' (Optional[str]): The address where notifications are delivered.
            - 'expiration' (Optional[str]): The time at which the channel will expire (RFC3339 format).
            - 'payload' (Optional[bool]): Whether to include the payload in notifications.
            - 'params' (Optional[Dict[str, str]]): Additional parameters controlling delivery channel behavior.
                An object containing a list of key: value pairs. Example: { "name": "wrench", "mass": "1.3kg", "count": "3" }.

    Raises:
        ValidationError: If the resource parameter contains invalid data types or formats.
        ChannelNotFoundError: If the specified channel ID does not exist.
    """
    userId = 'me'
    
    # Ensure user and channels structure exists
    _ensure_channels(userId)
    
    # Handle None resource parameter
    if resource is None:
        resource = {}
    
    # Validate resource parameter using Pydantic model
    try:
        validated_resource = ChannelResourceModel(**resource)
    except PydanticValidationError as e:
        error_msg = e.errors()[0]['msg'] if e.errors() else "Invalid channel resource data"
        raise ValidationError(f"Channel validation failed: {error_msg}")
    
    # Get the channel ID from the validated resource
    channel_id = validated_resource.id
    
    # If no channel ID provided, we cannot stop any specific channel
    if not channel_id:
        return
    
    # Check if the channel exists before attempting to stop it
    user_channels = DB['users'][userId]['channels']
    if channel_id not in user_channels:
        raise ChannelNotFoundError(f"Channel '{channel_id}' not found. Cannot stop a non-existent channel.")
    
    # Stop the channel by removing it from the user's active channels
    user_channels.pop(channel_id, None)