"""
Users resource for Slack API simulation.

This module provides functionality for managing users in Slack.
It simulates the users-related endpoints of the Slack API.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional
import base64
import binascii
import builtins
from pydantic import ValidationError

from .SimulationEngine.custom_errors import (
    InvalidEmailFormatError, 
    UserNotFoundError, 
    EmptyEmailError, 
    InvalidCursorValueError, 
    MissingUserIDError, 
    InvalidProfileError
)
from common_utils.custom_errors import InvalidEmailError
from .SimulationEngine.db import DB
from .SimulationEngine.models import UserProfile
from .SimulationEngine.utils import infer_channel_type, get_channel_members
from common_utils.utils import validate_email_util


@tool_spec(
    spec={
        'name': 'list_user_conversations',
        'description': 'Lists conversations the specified user may access.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user whose conversations to list.'
                },
                'cursor': {
                    'type': 'string',
                    'description': "Paginate through collections of data by setting the cursor parameter to the next_cursor attribute returned by a previous request's response. Default value fetches the first page."
                },
                'exclude_archived': {
                    'type': 'boolean',
                    'description': 'Set to true to exclude archived channels from the list. Defaults to False.'
                },
                'limit': {
                    'type': 'integer',
                    'description': "The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the list hasn't been reached. Must be an integer no larger than 1000. Default is 100."
                },
                'types': {
                    'type': 'string',
                    'description': 'Mix and match channel types by providing a comma-separated list of any combination of public_channel, private_channel, mpim, im.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def conversations(
    user_id: str,
    cursor: Optional[str] = None,
    exclude_archived: bool = False,
    limit: int = 100,
    types: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lists conversations the specified user may access.

    Args:
        user_id (str): The ID of the user whose conversations to list.
        cursor (Optional[str]): Paginate through collections of data by setting the cursor parameter to the next_cursor attribute returned by a previous request's response. Default value fetches the first page.
        exclude_archived (bool): Set to true to exclude archived channels from the list. Defaults to False.
        limit (int): The maximum number of items to return. Fewer than the requested number of items may be returned, even if the end of the list hasn't been reached. Must be an integer no larger than 1000. Default is 100.
        types (Optional[str]): Mix and match channel types by providing a comma-separated list of any combination of public_channel, private_channel, mpim, im.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - channels (List[Dict[str, Any]]): List of conversation objects
            - next_cursor (Optional[str]): Cursor for the next page of results

    Raises:
        TypeError: If user_id is not a string or is empty, exclude_archived is not a boolean,
                  or types is not a string when provided.
        ValueError: If limit is not between 1 and 1000, or if types contains invalid values,
                   or if cursor is not a valid integer string.
    """
    # Input validation
    if not isinstance(user_id, str) or not user_id.strip():
        raise TypeError("user_id must be a non-empty string")

    if not isinstance(exclude_archived, bool):
        raise TypeError("exclude_archived must be a boolean")

    if type(limit) is not int:
        raise TypeError("limit must be an integer")
    if limit <= 0 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")

    # Validate cursor early
    start = 0
    if cursor is not None:
        if not isinstance(cursor, str):
            raise TypeError("cursor must be a string if provided")
        try:
            start = int(cursor)
        except ValueError:
            raise ValueError("cursor must be a valid integer string")

    if types is not None:
        if not isinstance(types, str):
            raise TypeError("types must be a string")
        valid_types = ["public_channel", "private_channel", "mpim", "im"]  # Use list for consistent order
        allowed_types_set = set(valid_types)
        provided_types = {t.strip() for t in types.split(",") if t.strip()}
        if not provided_types or not provided_types.issubset(allowed_types_set):
            raise ValueError(f"types must be a comma-separated list of valid types: {', '.join(valid_types)}")
        allowed_types = provided_types
    else:
        allowed_types = {"public_channel", "private_channel", "mpim", "im"}

    if "channels" not in DB:
        DB["channels"] = {}
    if "users" not in DB:
        DB["users"] = {}

    # Filter channels based on criteria
    all_channels = DB["channels"].values()
    filtered_channels = []
    
    for channel in all_channels:
        # Infer channel type from channel properties
        channel_type = infer_channel_type(channel)
        
        # Check if this channel type is allowed
        if channel_type not in allowed_types:
            continue
            
        # Check if archived channels should be excluded
        if exclude_archived and channel.get("is_archived", False):
            continue
            
        # Check membership by inferring from messages and reactions
        # Only include channels where the user has some activity (posted or reacted)
        channel_members = get_channel_members(channel)
        if not channel_members or user_id not in channel_members:
            continue
            
        filtered_channels.append(channel)

    # Apply pagination
    end = min(start + limit, len(filtered_channels))
    paginated_channels = filtered_channels[start:end]

    # Determine next cursor
    next_cursor = str(end) if end < len(filtered_channels) else None

    return {"ok": True, "channels": paginated_channels, "next_cursor": next_cursor}


@tool_spec(
    spec={
        'name': 'set_user_presence',
        'description': """ Manually sets a user's presence.
        
        This function updates the presence status for a specified user, setting it
        to either 'active' or 'away'. It directly modifies the user's record in
        the database. Upon successful execution, it confirms the operation was
        successful. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user to update. Cannot be an empty string.'
                },
                'presence': {
                    'type': 'string',
                    'description': "The new presence status. Must be either 'active' or 'away'."
                }
            },
            'required': [
                'user_id',
                'presence'
            ]
        }
    }
)
def setPresence(user_id: str, presence: str) -> Dict[str, Any]:
    """
    Manually sets a user's presence.

    This function updates the presence status for a specified user, setting it
    to either 'active' or 'away'. It directly modifies the user's record in
    the database. Upon successful execution, it confirms the operation was
    successful.

    Args:
        user_id (str): The ID of the user to update. Cannot be an empty string.
        presence (str): The new presence status. Must be either 'active' or 'away'.

    Returns:
        Dict[str, Any]: A dictionary confirming the success of the operation.
            - ok (bool): Always True if the presence was set successfully.

    Raises:
        TypeError: If `user_id` or `presence` is not a string.
        ValueError: If `user_id` is an empty string or if `presence` is not
                    'active' or 'away'.
        UserNotFoundError: If the user with the specified `user_id` is not found.
    """
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    if not user_id:
        raise ValueError("user_id cannot be an empty string.")

    if not isinstance(presence, str):
        raise TypeError("presence must be a string.")
    if presence not in ("active", "away"):
        raise ValueError("presence must be 'active' or 'away'.")

    if user_id not in DB.get("users", {}):
        raise UserNotFoundError(f"User '{user_id}' not found.")

    DB["users"][user_id]["presence"] = presence
    return {"ok": True}


@tool_spec(
    spec={
        'name': 'set_user_photo',
        'description': """ Sets a user's profile photo.
        
        This function updates the profile photo for a specified user. It takes a
        user ID and a base64-encoded string representing the new image.
        Optionally, cropping parameters can be provided to specify how the image
        should be cropped. The function updates the user's record in the
        database with the new image and cropping information. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user to update. Cannot be an empty string.'
                },
                'image': {
                    'type': 'string',
                    'description': 'A base64-encoded string of the image data. Cannot be empty.'
                },
                'crop_x': {
                    'type': 'integer',
                    'description': """ The x-coordinate for the top-left corner of the crop.
                    Must be a non-negative integer if provided. """
                },
                'crop_y': {
                    'type': 'integer',
                    'description': """ The y-coordinate for the top-left corner of the crop.
                    Must be a non-negative integer if provided. """
                },
                'crop_w': {
                    'type': 'integer',
                    'description': """ The width of the crop box.
                    Must be a non-negative integer if provided. """
                }
            },
            'required': [
                'user_id',
                'image'
            ]
        }
    }
)
def setPhoto(
    user_id: str,
    image: str,
    crop_x: Optional[int] = None,
    crop_y: Optional[int] = None,
    crop_w: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sets a user's profile photo.

    This function updates the profile photo for a specified user. It takes a
    user ID and a base64-encoded string representing the new image.
    Optionally, cropping parameters can be provided to specify how the image
    should be cropped. The function updates the user's record in the
    database with the new image and cropping information.

    Args:
        user_id (str): The ID of the user to update. Cannot be an empty string.
        image (str): A base64-encoded string of the image data. Cannot be empty.
        crop_x (Optional[int]): The x-coordinate for the top-left corner of the crop.
            Must be a non-negative integer if provided.
        crop_y (Optional[int]): The y-coordinate for the top-left corner of the crop.
            Must be a non-negative integer if provided.
        crop_w (Optional[int]): The width of the crop box.
            Must be a non-negative integer if provided.

    Returns:
        Dict[str, Any]: A dictionary confirming the success of the operation.
            - ok (bool): Always True if the photo was set successfully.

    Raises:
        TypeError: If `user_id` or `image` is not a string, or if any of the
                   cropping parameters are not integers.
        ValueError: If `user_id` or `image` is an empty string, or if any of
                    the cropping parameters are negative.
        UserNotFoundError: If the user with the specified `user_id` is not found.
    """
    # Input Validation
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    if not user_id:
        raise ValueError("user_id cannot be an empty string.")

    if not isinstance(image, str):
        raise TypeError("image must be a string.")
    if not image:
        raise ValueError("image cannot be an empty string.")
    try:
        base64.b64decode(image, validate=True)
    except binascii.Error:
        raise ValueError("image must be a valid base64-encoded string.")

    if user_id not in DB.get("users", {}):
        raise UserNotFoundError(f"User '{user_id}' not found.")

    if "profile" not in DB["users"][user_id]:
        DB["users"][user_id]["profile"] = {}

    crop_params = [crop_x, crop_y, crop_w]
    if any(p is not None and not isinstance(p, int) for p in crop_params):
        raise TypeError("Cropping parameters (crop_x, crop_y, crop_w) must be integers.")
    if any(p is not None and p < 0 for p in crop_params):
        raise ValueError("Cropping parameters must be non-negative.")

    # Update profile with new image
    DB["users"][user_id]["profile"]["image"] = image

    # Store crop data if all three parameters are provided
    if all(p is not None for p in crop_params):
        DB["users"][user_id]["profile"]["image_crop_x"] = crop_x
        DB["users"][user_id]["profile"]["image_crop_y"] = crop_y
        DB["users"][user_id]["profile"]["image_crop_w"] = crop_w

    return {"ok": True}


@tool_spec(
    spec={
        'name': 'delete_user_photo',
        'description': """ Deletes the profile photo for a user.
        
        This function removes the profile picture for a specified user. It
        identifies the user by their ID and deletes the associated image data,
        including any cropping information, from their profile. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user whose photo should be deleted.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def deletePhoto(user_id: str) -> Dict[str, Any]:
    """Deletes the profile photo for a user.

    This function removes the profile picture for a specified user. It
    identifies the user by their ID and deletes the associated image data,
    including any cropping information, from their profile.

    Args:
        user_id (str): The ID of the user whose photo should be deleted.

    Returns:
        Dict[str, Any]: A dictionary confirming the success of the operation,
            in the format `{'ok': True}`.

    Raises:
        TypeError: If `user_id` is not a string.
        ValueError: If `user_id` is an empty string or if the user does not have a profile photo to delete.
        UserNotFoundError: If a user with the specified `user_id` cannot be found.
    """
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    if not user_id:
        raise ValueError("user_id must not be empty.")

    user_profile = DB["users"].get(user_id)
    if not user_profile:
        raise UserNotFoundError(f"User with ID '{user_id}' not found.")

    if "image" not in user_profile["profile"]:
        raise ValueError("User has no profile photo to delete.")

    del user_profile["profile"]["image"]

    # Remove crop info if it exists.
    crop_keys = ["image_crop_x", "image_crop_y", "image_crop_w"]
    for key in crop_keys:
        user_profile["profile"].pop(key, None)
        
    return {"ok": True}


@tool_spec(
    spec={
        'name': 'get_user_info',
        'description': 'Gets information about a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID to get info on.'
                },
                'include_locale': {
                    'type': 'boolean',
                    'description': 'Whether to include locale. Defaults to False.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def info(user_id: str, include_locale: bool = False) -> Dict[str, Any]:
    """
    Gets information about a user.

    Args:
        user_id (str): User ID to get info on.
        include_locale (bool): Whether to include locale. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - user (Dict[str, Any]): User information if successful

    Raises:
        ValueError: If user_id is invalid or not a string
        TypeError: If include_locale is not a boolean
        SlackError: If user is not found in the database
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("Invalid user ID")

    if not isinstance(include_locale, bool):
        raise TypeError("include_locale must be a boolean")

    user_data = DB.get("users", {}).get(user_id)
    if not user_data:
        raise UserNotFoundError("User not found")

    result = {"ok": True, "user": user_data}
    if include_locale:
        result["user"]["locale"] = "en-US"  # Example. Could get from user data if stored.
    return result


@tool_spec(
    spec={
        'name': 'get_user_presence',
        'description': 'Gets user presence information.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID to get presence info on. Defaults to the authed user.'
                }
            },
            'required': []
        }
    }
)
def getPresence(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Gets user presence information.

    Args:
        user_id (Optional[str]): User ID to get presence info on. Defaults to the authed user.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - presence (str): User's presence status

    Raises:
        TypeError: If user_id is provided but not a string
        MissingUserIDError: If no user_id is provided and there is no authenticated user
        UserNotFoundError: If the specified user_id does not exist in the database
    """
    # Validate user_id type if provided
    if user_id is not None and not isinstance(user_id, str):
        raise TypeError("user_id must be a string or None")

    # If no user_id provided, use the current user
    if not user_id:
        if "current_user" not in DB or not DB["current_user"]:
            raise MissingUserIDError("No user_id provided and no authenticated user found")
        user_id = DB["current_user"]["id"]

    if user_id not in DB["users"]:
        raise UserNotFoundError(f"User with ID {user_id} not found")

    #Return the user's presence, or offline if it's not been set.
    presence = DB["users"][user_id].get("presence", "away")
    return {"ok": True, "presence": presence}


@tool_spec(
    spec={
        'name': 'set_user_profile',
        'description': "Set a user's profile information.",
        'parameters': {
            'type': 'object',
            'properties': {
                'profile': {
                    'type': 'object',
                    'description': 'A collection of user profile attributes to be updated. Must contain valid profile fields:',
                    'properties': {
                        'display_name': {
                            'type': 'string',
                            'description': "The user's display name"
                        },
                        'real_name': {
                            'type': 'string',
                            'description': "The user's real name"
                        },
                        'email': {
                            'type': 'string',
                            'description': "The user's email address. Must contain '@' character if provided"
                        },
                        'phone': {
                            'type': 'string',
                            'description': "The user's phone number. Must contain only digits, spaces, hyphens, and '+' if provided"
                        },
                        'status_emoji': {
                            'type': 'string',
                            'description': "The user's status emoji"
                        },
                        'status_text': {
                            'type': 'string',
                            'description': "The user's status text"
                        },
                        'title': {
                            'type': 'string',
                            'description': "The user's title"
                        },
                        'team': {
                            'type': 'string',
                            'description': "The user's team"
                        },
                        'skype': {
                            'type': 'string',
                            'description': "The user's Skype handle"
                        },
                        'first_name': {
                            'type': 'string',
                            'description': "The user's first name"
                        },
                        'last_name': {
                            'type': 'string',
                            'description': "The user's last name"
                        }
                    },
                    'required': []
                },
                'user_id': {
                    'type': 'string',
                    'description': 'ID of user to change. Must be a non-empty string.'
                }
            },
            'required': [
                'profile',
                'user_id'
            ]
        }
    }
)
def set_user_profile(profile: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Set a user's profile information.

    Args:
        profile (Dict[str, Any]): A collection of user profile attributes to be updated. Must contain valid profile fields:
            - display_name (Optional[str]): The user's display name
            - real_name (Optional[str]): The user's real name
            - email (Optional[str]): The user's email address. Must contain '@' character if provided
            - phone (Optional[str]): The user's phone number. Must contain only digits, spaces, hyphens, and '+' if provided
            - status_emoji (Optional[str]): The user's status emoji
            - status_text (Optional[str]): The user's status text
            - title (Optional[str]): The user's title
            - team (Optional[str]): The user's team
            - skype (Optional[str]): The user's Skype handle
            - first_name (Optional[str]): The user's first name
            - last_name (Optional[str]): The user's last name
        user_id (str): ID of user to change. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - profile (Dict[str, Any]): Updated profile information if successful, containing:
                - display_name (Optional[str]): The user's display name
                - real_name (Optional[str]): The user's real name
                - email (Optional[str]): The user's email address
                - phone (Optional[str]): The user's phone number
                - status_emoji (Optional[str]): The user's status emoji
                - status_text (Optional[str]): The user's status text
                - title (Optional[str]): The user's title
                - team (Optional[str]): The user's team
                - skype (Optional[str]): The user's Skype handle
                - first_name (Optional[str]): The user's first name
                - last_name (Optional[str]): The user's last name

    Raises:
        TypeError: If user_id is not a string
        MissingUserIDError: If user_id is empty or None
        UserNotFoundError: If the specified user_id does not exist
        InvalidProfileError: If the profile data is invalid
        ValidationError: If any profile field fails validation
    """
    # Validate user_id type
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string")

    # Validate user_id is not empty
    if not user_id:
        raise MissingUserIDError("user_id cannot be empty")

    # Validate user exists
    if user_id not in DB["users"]:
        raise UserNotFoundError(f"User with ID {user_id} not found")

    # Validate profile is a dictionary
    if not isinstance(profile, dict):
        raise InvalidProfileError("profile must be a dictionary")

    try:
        # Validate profile data using Pydantic model
        validated_profile = UserProfile(**profile)
        
        # Initialize profile if it doesn't exist
        if "profile" not in DB["users"][user_id]:
            DB["users"][user_id]["profile"] = {}

        # Update profile with validated data
        profile_dict = validated_profile.model_dump(exclude_none=True)  # Use model_dump instead of dict
        DB["users"][user_id]["profile"].update(profile_dict)

        return {"ok": True, "profile": DB["users"][user_id]["profile"]}
    except ValidationError as e:
        # Format error message to match expected format
        error_msg = str(e)
        if "Extra inputs are not permitted" in error_msg:
            # Extract the field name from the error message
            field_name = error_msg.split('\n')[1].strip()
            raise InvalidProfileError(f"Invalid profile data: 1 validation error for UserProfile\n{field_name}\n  extra fields not permitted (type=value_error.extra)\n")
        elif "Invalid email format" in error_msg:
            raise InvalidProfileError("Invalid profile data: 1 validation error for UserProfile\nemail\n  Invalid email format (type=value_error)")
        elif "Invalid phone number format" in error_msg:
            raise InvalidProfileError("Invalid profile data: 1 validation error for UserProfile\nphone\n  Invalid phone number format (type=value_error)")
        else:
            raise InvalidProfileError(f"Invalid profile data: {error_msg}")


@tool_spec(
    spec={
        'name': 'list_users',
        'description': 'Lists all users in a Slack team.',
        'parameters': {
            'type': 'object',
            'properties': {
                'cursor': {
                    'type': 'string',
                    'description': 'Pagination cursor encoded in base64 in format "user:{user_id}". Must be a valid base64 string if provided.'
                },
                'include_locale': {
                    'type': 'boolean',
                    'description': 'Include locale information. Defaults to False.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of items to return. Must be positive and no larger than 1000. Defaults to 100.'
                },
                'team_id': {
                    'type': 'string',
                    'description': 'Team ID to filter users by. Must be a non-empty string if provided.'
                }
            },
            'required': []
        }
    }
)
def list_users(
    cursor: Optional[str] = None,
    include_locale: Optional[bool] = False,
    limit: Optional[int] = 100,
    team_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lists all users in a Slack team.

    Args:
        cursor (Optional[str]): Pagination cursor encoded in base64 in format "user:{user_id}". Must be a valid base64 string if provided.
        include_locale (Optional[bool]): Include locale information. Defaults to False.
        limit (Optional[int]): Maximum number of items to return. Must be positive and no larger than 1000. Defaults to 100.
        team_id (Optional[str]): Team ID to filter users by. Must be a non-empty string if provided.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - members (List[Dict[str, Any]]): List of user objects (when successful), each containing:
                - id (str): User ID
                - team_id (str): Team ID the user belongs to
                - name (str): Username
                - real_name (str): User's real name
                - profile (Dict[str, Any]): User profile information containing:
                    - email (str): User's email address
                    - display_name (str): Display name
                    - image (str): Profile image data
                    - image_crop_x (int): X coordinate for image crop
                    - image_crop_y (int): Y coordinate for image crop
                    - image_crop_w (int): Width for image crop
                    - title (str): Job title
                - is_admin (bool): Whether user is an admin
                - is_bot (bool): Whether user is a bot
                - deleted (bool): Whether user is deleted
                - presence (str): User's presence status
                - locale (str): User's locale (only if include_locale is True)
            - response_metadata (Dict[str, Any]): Pagination metadata containing:
                - next_cursor (Optional[str]): Base64 encoded cursor for next page of results in format "user:{user_id}"

    Raises:
        TypeError: If input types are invalid:
            - 'cursor' is not a string (and not None).
            - 'include_locale' is not a boolean.
            - 'limit' is not an integer.
            - 'team_id' is not a string (and not None).
        ValueError: If 'limit' is not a positive integer or exceeds 1000.
        InvalidCursorValueError: If 'cursor' cannot be decoded properly or user ID not found.
    """
    # --- Input Validation ---
    if cursor is not None and not isinstance(cursor, str):
        raise TypeError("cursor must be a string or None.")
    
    # Handle None values for optional parameters with defaults
    if include_locale is None:
        include_locale = False
    if limit is None:
        limit = 100
    
    if not isinstance(include_locale, bool):
        raise TypeError("include_locale must be a boolean.")
    if type(limit) is not int:
        raise TypeError("limit must be an integer.")
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")
    if limit > 1000:
        raise ValueError("limit must be no larger than 1000.")
    if team_id is not None and not isinstance(team_id, str):
        raise TypeError("team_id must be a string or None.")

    # --- Original Core Logic ---

    # Filter users by team_id, if provided.
    # Assuming DB is accessible in this scope.
    if team_id:
        filtered_users = [user for user_id, user in DB.get("users", {}).items() if user.get("team_id") == team_id]
    else:
        filtered_users = builtins.list(DB.get("users", {}).values())
    
    # Sort users by user ID to ensure consistent pagination order
    # Handle None values by converting them to empty strings for consistent sorting
    filtered_users.sort(key=lambda user: user.get("id") or "")

    # Pagination
    start_index = 0
    if cursor:
        try:
            # Decode base64 cursor and extract user ID
            decoded_cursor = base64.b64decode(cursor).decode('utf-8')
            if not decoded_cursor.startswith("user:"):
                raise InvalidCursorValueError("Invalid cursor format")
            cursor_user_id = decoded_cursor[5:]  # Remove "user:" prefix
            
            # Find the index after the cursor user
            try:
                user_ids = [user.get("id") for user in filtered_users]
                start_index = user_ids.index(cursor_user_id) + 1
            except ValueError:
                raise InvalidCursorValueError(f"User ID {cursor_user_id} not found in users list")
                
        except binascii.Error:
            raise InvalidCursorValueError("Invalid base64 cursor format")
        except (UnicodeDecodeError):
            raise InvalidCursorValueError("Invalid cursor encoding")

    end_index = min(start_index + limit, len(filtered_users))
    # Ensure start_index is not out of bounds after cursor conversion
    if start_index > len(filtered_users) and len(filtered_users) > 0:
         # This case could be an empty page or an error depending on desired behavior for out-of-bounds cursors
         # For now, return empty list, consistent with start_index >= end_index
         paginated_users = []
    elif start_index >= end_index:
        paginated_users = []
    else:
        paginated_users = filtered_users[start_index:end_index]

    # Include locale if requested.
    if include_locale:
        for user in paginated_users:
            user["locale"] = "en-US"  # Example - would get from user data if available

    # Generate next cursor - using base64 encoding of "user:userId"
    next_cursor = None
    if end_index < len(filtered_users):
        # Get the last user ID from the current page to create the cursor
        last_user_id = paginated_users[-1].get("id") if paginated_users else None
        if last_user_id:
            cursor_string = f"user:{last_user_id}"
            next_cursor = base64.b64encode(cursor_string.encode('utf-8')).decode('utf-8')

    return {
        "ok": True,
        "members": paginated_users,
        "response_metadata": {"next_cursor": next_cursor},
    }


@tool_spec(
    spec={
        'name': 'get_user_identity',
        'description': "Get a user's identity information.",
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID. Must be a non-empty string.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def identity(user_id: str) -> dict:
    """
    Get a user's identity information.

    Args:
        user_id (str): User ID. Must be a non-empty string.

    Returns:
        dict: A dictionary containing the user's identity information with the following structure:
            - ok (bool): Whether the operation was successful
            - user (dict): User identity information containing:
                - name (str): User's username
                - id (str): User's ID
            - team (dict): Team information containing:
                - id (str): Team ID the user belongs to

    Raises:
        TypeError: If user_id is not a string.
        MissingUserIDError: If user_id is empty or None.
        UserNotFoundError: If the specified user_id does not exist in the database.
    """
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    
    if not user_id:
        raise MissingUserIDError("user_id cannot be empty.")

    if user_id not in DB["users"]:
        raise UserNotFoundError(f"User with ID '{user_id}' not found.")

    user_data = DB["users"][user_id]
    identity_data = {
        "ok": True,
        "user": {
            "name": user_data["name"],
            "id": user_data["id"],
        },
        "team": {
                "id": user_data["team_id"]
        }

    }
    return identity_data


@tool_spec(
    spec={
        'name': 'lookup_user_by_email',
        'description': 'Find a user with an email address.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email': {
                    'type': 'string',
                    'description': 'An email address belonging to a user. Must be a non-empty string.'
                }
            },
            'required': [
                'email'
            ]
        }
    }
)
def lookupByEmail(email: str) -> Dict[str, Any]:
    """
    Find a user with an email address.

    Args:
        email (str): An email address belonging to a user. Must be a non-empty string.

    Returns:
        Dict[str, Any]: User data if found (e.g., {"ok": True, "user": user_data}).

    Raises:
        TypeError: If `email` is not a string.
        EmptyEmailError: If `email` is an empty string.
        InvalidEmailFormatError: If email format is invalid (missing '@', empty local/domain parts, missing TLD, etc.).
        InvalidEmailError: If email format is invalid according to validate_email_util (more comprehensive validation).
        UserNotFoundError: If no user is found with the specified email address.
    """
    # --- Input Validation ---
    if not isinstance(email, str):
        raise TypeError("email must be a string.")
    if not email:  # Check for empty string after type check
        raise EmptyEmailError("email cannot be empty.")

    parts = email.split('@')
    if len(parts) != 2 or not parts[0] or not parts[1]:  # Checks for 'local@domain' structure and non-empty parts
        raise InvalidEmailFormatError(
            "Argument 'email' has an invalid format. It must contain a local part and a domain part separated by '@'.")

    domain_part = parts[1]
    if '.' not in domain_part:
        raise InvalidEmailFormatError("Argument 'email' has an invalid format. The domain part must contain '.'.")

    if not domain_part.split('.')[-1]:  # Check if TLD is empty (e.g., "user@domain.")
        raise InvalidEmailFormatError(
            "Argument 'email' has an invalid format. The top-level domain cannot be empty.")

    validate_email_util(email, "email")

    # --- End of Input Validation ---

    # Original core functionality (preserved)
    for user_id, user_data in DB.get("users", {}).items():
        if user_data.get("profile", {}).get("email") == email:
            return {"ok": True, "user": user_data}

    raise UserNotFoundError("User with email not found")


@tool_spec(
    spec={
        'name': 'get_current_user_id',
        'description': """ Helper endpoint that returns the ID of the user who is currently authenticated""",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def current_user_id() -> Dict[str, Any]:
    """
    Helper endpoint that returns the ID of the user who is currently authenticated).

    Returns:
        Dict[str, Any]:
            - ok (bool): Always ``True`` when the current user is set.
            - user_id (str): ID of the current user.

    Errors:
        If the implementation has not set a current user yet, returns ``{"ok": False, "error": "current_user_not_set"}``.
    """
    current_user = DB.get("current_user")
    if not current_user or "id" not in current_user:
        return {"ok": False, "error": "current_user_not_set"}

    return {"ok": True, "user_id": current_user["id"]}
