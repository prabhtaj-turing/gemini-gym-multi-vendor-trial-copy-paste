from common_utils.tool_spec_decorator import tool_spec
# instagram/Media.py

from .SimulationEngine.custom_errors import InvalidMediaIDError, MediaNotFoundError
from .SimulationEngine.custom_errors import UserNotFoundError
from .SimulationEngine.db import DB
from .SimulationEngine.models import MediaCreateModel
from .SimulationEngine.utils import validate_user_id_format
from typing import Dict, Any, List
from pydantic import ValidationError
import datetime
import uuid

# ------------------------------------------------------------------------------
# Media
# ------------------------------------------------------------------------------

"""Handles media-related operations."""


@tool_spec(
    spec={
  'name': 'create_media_post',
  'description': 'Creates a new media post associated with a user',
  'parameters': {
    'type': 'object',
    'properties': {
      'user_id': {
        'type': 'string',
        'description': 'The ID of the user who owns the media. Must be a non-empty string. Can only contain letters, numbers, periods, and underscores.'
      },
      'image_url': {
        'type': 'string',
        'description': 'URL of the media image. Must be a valid URL format.'
      },
      'caption': {
        'type': 'string',
        'description': 'Caption or description for the media. Must be a string. Defaults to "".'
      }
    },
    'required': [
      'user_id',
      'image_url'
    ]
  }
}
)

def create_media(user_id: str, image_url: str, caption: str = "") -> Dict[str, str]:
    """
    Creates a new media post associated with a user.

    Args:
        user_id (str): The ID of the user who owns the media. Must be a non-empty string. Can only contain letters, numbers, periods, and underscores.
        image_url (str): URL of the media image. Must be a valid URL format.
        caption (str): Caption or description for the media. Must be a string. Defaults to "".

    Returns:
        Dict[str, str]:
        - On successful creation, returns a dictionary with the following keys and value types:
            - id (str): The media's unique identifier
            - user_id (str): The ID of the user who owns the media
            - image_url (str): URL of the media image
            - caption (str): Caption or description for the media
            - timestamp (str): ISO format timestamp of when the media was created

    Raises:
        ValidationError: If input validation fails (invalid types, empty strings, invalid URL format).
        ValueError: If user_id contains invalid characters (only letters, numbers, periods, and underscores are allowed).
        UserNotFoundError: If the 'user_id' does not correspond to an existing user.
    """
    # Add character format validation for user_id before Pydantic validation
    validated_data = MediaCreateModel(
        user_id=user_id,
        image_url=image_url,
        caption=caption
    )
    
    user_id = validated_data.user_id
    image_url = str(validated_data.image_url)  # Convert HttpUrl to string
    caption = validated_data.caption

    validate_user_id_format(user_id)

    # Core logic (assuming DB and datetime are available in the scope)
    if user_id not in DB["users"]:
        raise UserNotFoundError(f"User with ID '{user_id}' does not exist.")

    # Generate unique media ID by finding the next available sequential ID
    # This ensures we never reuse IDs even after deletions
    message_counter = 1
    media_id = f"media_{len(DB['media']) + message_counter}"
    while media_id in DB["media"]:
        message_counter += 1
        media_id = f"media_{len(DB['media']) + message_counter}"
    
    timestamp = datetime.datetime.now().isoformat()  # type: ignore

    DB["media"][media_id] = {
        "user_id": user_id,
        "image_url": image_url,
        "caption": caption,
        "timestamp": timestamp,
    }
    return {
        "id": media_id,
        "user_id": user_id,
        "image_url": image_url,
        "caption": caption,
        "timestamp": timestamp,
    }


@tool_spec(
    spec={
        'name': 'list_all_media_posts',
        'description': 'Lists all media posts in the system.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_media() -> List[Dict[str, str]]:
    """
    Lists all media posts in the system.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, where each dictionary contains:
            - id (str): The media's unique identifier
            - user_id (str): The ID of the user who owns the media
            - image_url (str): URL of the media image
            - caption (str): Caption or description for the media
            - timestamp (Optional[str]): ISO format timestamp of when the media was created. Will be None if timestamp information is not available or was not recorded.
        
        Returns an empty list if no media posts exist in the system.

    """
    
    media_list = []
    for media_id, info in DB["media"].items():
        media_list.append({
            "id": media_id,
            "user_id": info.get("user_id"),
            "image_url": info.get("image_url"),
            "caption": info.get("caption"),
            "timestamp": info.get("timestamp"),
        })
    return media_list


@tool_spec(
    spec={
        'name': 'delete_media_post',
        'description': 'Deletes a specified media post from the system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'media_id': {
                    'type': 'string',
                    'description': """ The unique identifier of the media post to delete.
                    Must be a non-empty string. """
                }
            },
            'required': [
                'media_id'
            ]
        }
    }
)
def delete_media(media_id: str) -> Dict[str, str]:
    """
    Deletes a specified media post from the system.

    Args:
        media_id (str): The unique identifier of the media post to delete.
                        Must be a non-empty string.

    Returns:
        Dict[str, str]: A dictionary with the key "success" and the value True.

    Raises:
        TypeError: If media_id is not a string.
        InvalidMediaIDError: If media_id is an empty string.
        MediaNotFoundError: If media_id does not correspond to an existing media post.
    """
    # --- Input Validation ---
    if not isinstance(media_id, str):
        raise TypeError("Field media_id must be a string.")
    if not media_id:  # Checks for empty string, e.g., ""
        raise InvalidMediaIDError("Field media_id cannot be empty.")
    # --- End of Input Validation ---

    # Original core functionality
    # DB is assumed to be globally available or otherwise accessible here.
    if media_id in DB["media"]:
        del DB["media"][media_id]
        return {"success": True}
    raise MediaNotFoundError(f"Media with ID '{media_id}' not found.")
