from common_utils.tool_spec_decorator import tool_spec
# APIs/google_calendar/ChannelsResource/__init__.py
from .SimulationEngine.db import DB
from typing import Dict, Any, Optional


@tool_spec(
    spec={
        'name': 'stop_notification_channel',
        'description': """ Stops watching resources through a channel. This operation removes the channel from the
        
        list of active channels and prevents further notifications from being sent. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource': {
                    'type': 'object',
                    'description': 'The resource to stop the channel with.',
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': 'The identifier of the channel.'
                        }
                    },
                    'required': [
                        'id'
                    ]
                }
            },
            'required': []
        }
    }
)
def stop_channel(resource: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Stops watching resources through a channel. This operation removes the channel from the
    list of active channels and prevents further notifications from being sent.

    Args:
        resource (Dict[str, Any]): The resource to stop the channel with.
            - id (str): The identifier of the channel.

    Returns:
        Dict[str, Any]: A dictionary containing the operation result with the following fields:
            - success (bool): Whether the operation was successful.
            - message (str): A message describing the result of the operation.

    Raises:
        TypeError: If resource is not a dictionary or if the id field is not a string.
        ValueError: If the channel resource is not provided, if the id field is missing or empty,
                   or if the specified channel does not exist in the database.
    """
    # Input validation
    if resource is None:
        raise ValueError("Channel resource required to stop channel.")
    
    if not isinstance(resource, dict):
        raise TypeError("resource must be a dictionary")
    
    if "id" not in resource:
        raise ValueError("resource must contain 'id' field")
    
    channel_id = resource["id"]
    
    if not isinstance(channel_id, str):
        raise TypeError("resource 'id' must be a string")
    
    if not channel_id or not channel_id.strip():
        raise ValueError("resource 'id' cannot be empty or whitespace")
    
    # Check if channel exists
    if channel_id not in DB["channels"]:
        raise ValueError(f"Channel '{channel_id}' not found.")
    
    # Remove channel from database
    del DB["channels"][channel_id]
    return {"success": True, "message": f"Channel '{channel_id}' stopped."}
