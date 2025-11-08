import re
from common_utils.tool_spec_decorator import tool_spec
# instagram/Comment.py

from .SimulationEngine.custom_errors import MediaNotFoundError, UserNotFoundError
from .SimulationEngine.db import DB
from .SimulationEngine.utils import validate_user_id_format
from typing import Dict, Any, List
import datetime
import uuid
import re

"""Handles comment-related operations."""


@tool_spec(
    spec={
        'name': 'add_comment_to_media',
        'description': 'Adds a comment to a media post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'media_id': {
                    'type': 'string',
                    'description': 'The ID of the media post being commented on.'
                },
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user making the comment. Can only contain letters, numbers, periods, and underscores.'
                },
                'message': {
                    'type': 'string',
                    'description': 'The comment text.'
                }
            },
            'required': [
                'media_id',
                'user_id',
                'message'
            ]
        }
    }
)
def add_comment(media_id: str, user_id: str, message: str) -> Dict[str, str]:
    """
    Adds a comment to a media post.
    Args:
        media_id (str): The ID of the media post being commented on.
        user_id (str): The ID of the user making the comment. Can only contain letters, numbers, periods, and underscores.
        message (str): The comment text.
    Returns:
        Dict[str, str]: On successful creation, a dictionary with the following keys and value types:
            - id (str): The comment's unique identifier (format: "comment_N", e.g., "comment_1", "comment_2", "comment_3")
            - media_id (str): The ID of the media post being commented on
            - user_id (str): The ID of the user making the comment
            - message (str): The comment text
            - timestamp (str): ISO format timestamp of when the comment was created
    Raises:
        TypeError: If 'media_id', 'user_id', or 'message' is not a string.
        ValueError: If 'media_id', 'user_id', or 'message' is an empty string.
        ValueError: If user_id contains invalid characters (only letters, numbers, periods, and underscores are allowed).
        MediaNotFoundError: If the media post specified by 'media_id' does not exist.
        UserNotFoundError: If the user specified by 'user_id' does not exist.
    """
    # Input Validation for argument types and values
    if not isinstance(media_id, str):
        raise TypeError("Argument 'media_id' must be a string.")
    if not media_id.strip():
        raise ValueError("Field media_id cannot be empty.")
    if not isinstance(user_id, str):
        raise TypeError("Argument 'user_id' must be a string.")
    if not user_id.strip():
        raise ValueError("Field user_id cannot be empty.")
    
    # Add character format validation for user_id
    validate_user_id_format(user_id)
    
    if not isinstance(message, str):
        raise TypeError("Argument 'message' must be a string.")
    
    # Strip leading/trailing whitespace from the message
    stripped_message = message.strip()
    
    # Check for empty message after stripping
    if not stripped_message:
        raise ValueError("Field message cannot be empty.")
    
    # Check message length after stripping
    if len(stripped_message) > 300:
        raise ValueError("Message exceeds maximum length of 300 characters.")
    
    # Core Logic (with modification for MediaNotFoundError)
    if media_id not in DB["media"]:
        raise MediaNotFoundError("Media does not exist.")
    if user_id not in DB["users"]:
        raise UserNotFoundError("User does not exist.")
    
    # Generate a new comment ID ensuring no duplicates
    counter = 1
    while f"comment_{counter}" in DB["comments"]:
        counter += 1
    comment_id = f"comment_{counter}"
    timestamp = datetime.datetime.now().isoformat()
    
    DB["comments"][comment_id] = {
        "media_id": media_id,
        "user_id": user_id,
        "message": stripped_message,
        "timestamp": timestamp,
    }
    
    return {
        "id": comment_id,
        "media_id": media_id,
        "user_id": user_id,
        "message": stripped_message,
        "timestamp": timestamp,
    }

@tool_spec(
    spec={
        'name': 'list_media_comments',
        'description': 'Lists all comments on a specific media post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'media_id': {
                    'type': 'string',
                    'description': 'The ID of the media post to retrieve comments for.'
                }
            },
            'required': [
                'media_id'
            ]
        }
    }
)

def list_comments(media_id: str) -> List[Dict[str, str]]:
    """
    Lists all comments on a specific media post.
    Args:
        media_id (str): The ID of the media post to retrieve comments for.
    Returns:
        List[Dict[str, str]]: A list of dictionaries, where each dictionary contains:
            - id (str): The comment's unique identifier
            - media_id (str): The ID of the media post being commented on
            - user_id (str): The ID of the user who made the comment
            - message (str): The comment text
            - timestamp (Optional[str]): ISO format timestamp of when the comment was created. Will be None if timestamp information is not available or was not recorded.
            
        Returns an empty list if no comments exist for the specified media post.
    Raises:
        TypeError: If media_id is not a string.
        ValueError: If media_id is an empty string.
        MediaNotFoundError: If the media post specified by 'media_id' does not exist.
    """
    # Input validation for media_id
    if not isinstance(media_id, str):
        raise TypeError("media_id must be a string.")
    if not media_id.strip():  # Check for empty string
        raise ValueError("media_id cannot be an empty string.")
    if media_id not in DB["media"]:
        raise MediaNotFoundError(f"Media with id '{media_id}' not found.")
    
    # Original function logic
    comments = []
    for comment_id, info in DB["comments"].items():
        if info.get("media_id") == media_id:
            comments.append({
                "id": comment_id,
                "media_id": info.get("media_id"),
                "user_id": info.get("user_id"),
                "message": info.get("message"),
                "timestamp": info.get("timestamp"),
            })
    return comments
