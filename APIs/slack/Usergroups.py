"""
Usergroups resource for Slack API simulation.

This module provides functionality for managing user groups in Slack.
It simulates the usergroups-related endpoints of the Slack API.
"""
from common_utils.tool_spec_decorator import tool_spec
import time
import uuid
from typing import Dict, Any, List, Optional

from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import UserGroupIdInvalidError, UserGroupNotFoundError, UserGroupAlreadyDisabledError

@tool_spec(
    spec={
        'name': 'create_user_group',
        'description': 'Creates a new User Group.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Name of the User Group. Must be a non-empty string.'
                },
                'handle': {
                    'type': 'string',
                    'description': 'A mention handle for the User Group. Must be a string if provided.'
                },
                'team_id': {
                    'type': 'string',
                    'description': 'ID of the team the User Group belongs to. Must be a string if provided.'
                },
                'description': {
                    'type': 'string',
                    'description': 'Description of the User Group. Must be a string if provided.'
                },
                'channel_ids': {
                    'type': 'array',
                    'description': """ List of existing channel IDs to include in the User Group (e.g., ["C1234567890", "C0987654321"]).
                    If provided, must be a list of strings. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'created_at': {
                    'type': 'string',
                    'description': """ Timestamp when the User Group was created.
                    Defaults to current time as a string. """
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def create(
    name: str,
    handle: Optional[str] = None,
    team_id: Optional[str] = None,
    description: Optional[str] = None,
    channel_ids: Optional[List[str]] = None,
    created_at: str = str(time.time())
) -> Dict[str, Any]:
    """
    Creates a new User Group.

    Args:
        name (str): Name of the User Group. Must be a non-empty string.
        handle (Optional[str]): A mention handle for the User Group. Must be a string if provided.
        team_id (Optional[str]): ID of the team the User Group belongs to. Must be a string if provided.
        description (Optional[str]): Description of the User Group. Must be a string if provided.
        channel_ids (Optional[List[str]]): List of existing channel IDs to include in the User Group (e.g., ["C1234567890", "C0987654321"]).
                                           If provided, must be a list of strings.
        created_at (str): Timestamp when the User Group was created.
                          Defaults to current time as a string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Always True if successful.
            - usergroup (Dict[str, Any]): The created user group.

    Raises:
        TypeError: If any argument has an invalid type.
        ValueError: If any argument has an invalid value.
    """
    # --- Input Validation ---
    if not isinstance(name, str):
        raise TypeError("User Group 'name' must be a string.")
    if not name:
        raise ValueError("'name' cannot be empty.")

    if handle and not isinstance(handle, str):
        raise TypeError("User Group 'handle' must be a string if provided.")

    if team_id and not isinstance(team_id, str):
        raise TypeError("User Group 'team_id' must be a string if provided.")

    if description and not isinstance(description, str):
        raise TypeError("User Group 'description' must be a string if provided.")

    if channel_ids:
        if not isinstance(channel_ids, type([])):  # Use built-in list type
            raise TypeError("User Group 'channel_ids' must be a list if provided.")
        if not all(isinstance(cid, str) for cid in channel_ids):
            raise TypeError("All elements in 'channel_ids' must be strings.")

    if not isinstance(created_at, str):
        raise TypeError("User Group 'created_at' must be a string if provided.")

    # --- End of Input Validation ---


    if channel_ids:
        for channel_id in channel_ids:
            if channel_id not in DB["channels"]:
                raise ValueError(f"Invalid channel ID: '{channel_id}'")

    # Check for duplicate usergroup name (case-insensitive)
    for usergroup_data in DB.get("usergroups", {}).values():
        if usergroup_data["name"].lower() == name.lower():
            raise ValueError(f"A user group with the name '{name}' already exists.")
        # Check for duplicate usergroup handle (case-insensitive)
        if handle:
            if usergroup_data["handle"] and usergroup_data['handle'].lower() == handle.lower():
                raise ValueError(f"A user group with the handle '{handle}' already exists.")

    usergroup_id = str(uuid.uuid4())
    new_usergroup = {
        "id": usergroup_id,
        "team_id": team_id,
        "is_usergroup": True,
        "name": name,
        "handle": handle,
        "description": description,
        "date_create": created_at,
        "date_update": "",
        "date_delete": 0,
        "auto_type": None,
        "created_by": "",
        "updated_by": "",
        "deleted_by": None,
        "prefs": {
            "channels": channel_ids or [],
            "groups": []
        },
        "users": [],
        "user_count": 0,
        "disabled": False,
    }

    # Assuming DB is accessible here.
    if "usergroups" not in DB:
        DB["usergroups"] = {}
    DB["usergroups"][usergroup_id] = new_usergroup

    return {"ok": True, "usergroup": new_usergroup}


@tool_spec(
    spec={
        'name': 'list_user_groups',
        'description': 'Lists all User Groups for a team.',
        'parameters': {
            'type': 'object',
            'properties': {
                'team_id': {
                    'type': 'string',
                    'description': 'ID of the team to list User Groups for.'
                },
                'include_disabled': {
                    'type': 'boolean',
                    'description': 'Include disabled User Groups. Defaults to False.'
                },
                'include_count': {
                    'type': 'boolean',
                    'description': 'Include the number of users. Defaults to False.'
                },
                'include_users': {
                    'type': 'boolean',
                    'description': 'Include the list of user IDs. Defaults to False.'
                }
            },
            'required': []
        }
    }
)
def list(
    team_id: Optional[str] = None,
    include_disabled: bool = False,
    include_count: bool = False,
    include_users: bool = False,
) -> Dict[str, Any]:
    """
    Lists all User Groups for a team.

    Args:
        team_id (Optional[str]): ID of the team to list User Groups for.
        include_disabled (bool): Include disabled User Groups. Defaults to False.
        include_count (bool): Include the number of users. Defaults to False.
        include_users (bool): Include the list of user IDs. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the request was successful
            - usergroups (List[Dict[str, Any]]): List of user groups, where each group contains:
                - id (str): User Group ID
                - team_id (Optional[str]): Team ID
                - is_usergroup (bool): Indicates this is a user group
                - name (str): User Group name
                - description (Optional[str]): User Group description
                - handle (Optional[str]): User Group handle
                - date_create (int): Creation timestamp (Unix timestamp)
                - date_update (int): Last update timestamp (Unix timestamp)
                - date_delete (int): Deletion timestamp (Unix timestamp, 0 if not deleted)
                - auto_type (Optional[str]): Auto type (e.g., 'admin', 'owner', or None)
                - created_by (str): User ID of creator
                - updated_by (str): User ID of last updater
                - deleted_by (Optional[str]): User ID of deleter (None if not deleted)
                - prefs (Dict[str, List[str]]): Preferences containing:
                    - channels (List[str]): List of channel IDs
                    - groups (List[str]): List of group IDs
                - users (Optional[List[str]]): List of user IDs (if include_users=True)
                - user_count (Optional[str]): Number of users as string (if include_count=True)
                - disabled (bool): Whether the group is disabled

    Raises:
        TypeError: If any argument is of an incorrect type.
    """
    # Input Validation
    if team_id is not None and not isinstance(team_id, str):
        raise TypeError(f"Argument 'team_id' must be a string or None, but got {type(team_id).__name__}.")
    if not isinstance(include_disabled, bool):
        raise TypeError(f"Argument 'include_disabled' must be a boolean, but got {type(include_disabled).__name__}.")
    if not isinstance(include_count, bool):
        raise TypeError(f"Argument 'include_count' must be a boolean, but got {type(include_count).__name__}.")
    if not isinstance(include_users, bool):
        raise TypeError(f"Argument 'include_users' must be a boolean, but got {type(include_users).__name__}.")

    results = []
    all_usergroups = DB.get("usergroups", {}).values()

    # Filter by team_id first if provided
    if team_id:
        all_usergroups = [
            ug for ug in all_usergroups if ug.get("team_id") == team_id
        ]

    for usergroup_data in all_usergroups:
        # Filter by disabled status
        if not include_disabled and usergroup_data.get("disabled", False):
            continue

        # Create a copy to avoid modifying the original in the DB
        usergroup_info = usergroup_data.copy()

        # Convert user_count to string as per Slack API
        if "user_count" in usergroup_info:
            usergroup_info["user_count"] = str(usergroup_info["user_count"])

        # Conditionally remove fields
        if not include_count:
            usergroup_info.pop("user_count", None)
        if not include_users:
            usergroup_info.pop("users", None)

        results.append(usergroup_info)

    return {"ok": True, "usergroups": results}


@tool_spec(
    spec={
        'name': 'update_user_group',
        'description': 'Updates an existing User Group.',
        'parameters': {
            'type': 'object',
            'properties': {
                'usergroup_id': {
                    'type': 'string',
                    'description': 'The ID of the User Group to update.'
                },
                'name': {
                    'type': 'string',
                    'description': 'New name for the User Group. Must be a non-empty string if provided.'
                },
                'handle': {
                    'type': 'string',
                    'description': 'New handle for the User Group. Must be a non-empty string if provided.'
                },
                'description': {
                    'type': 'string',
                    'description': 'New description for the User Group. Must be a string if provided.'
                },
                'channel_ids': {
                    'type': 'array',
                    'description': 'New list of channel IDs. Must be a list of strings if provided.',
                    'items': {
                        'type': 'string'
                    }
                },
                'date_update': {
                    'type': 'string',
                    'description': 'Timestamp when the User Group was last updated. Must be a string if provided.'
                }
            },
            'required': [
                'usergroup_id'
            ]
        }
    }
)
def update(
    usergroup_id: str,
    name: Optional[str] = None,
    handle: Optional[str] = None,
    description: Optional[str] = None,
    channel_ids: Optional[List[str]] = None,
    date_update: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates an existing User Group.

    Args:
        usergroup_id (str): The ID of the User Group to update.
        name (Optional[str]): New name for the User Group. Must be a non-empty string if provided.
        handle (Optional[str]): New handle for the User Group. Must be a non-empty string if provided.
        description (Optional[str]): New description for the User Group. Must be a string if provided.
        channel_ids (Optional[List[str]]): New list of channel IDs. Must be a list of strings if provided.
        date_update (Optional[str]): Timestamp when the User Group was last updated. Must be a string if provided.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the request was successful
            - usergroup (Dict[str, Any]): The updated user group if successful

    Raises:
        UserGroupIdInvalidError: If usergroup_id is invalid or empty.
        UserGroupNotFoundError: If the usergroup_id does not exist.
        ValueError: If name or handle already exists, or if channel_ids contains invalid channel IDs.
        TypeError: If any parameter has an invalid type.
    """
    # --- Input Validation ---
    
    # Validate usergroup_id
    if not usergroup_id or not isinstance(usergroup_id, str):
        raise UserGroupIdInvalidError("usergroup_id must be a non-empty string")

    # Validate name parameter
    if name is not None:
        if not isinstance(name, str):
            raise TypeError("name must be a string if provided")
        if not name.strip():  # Reject empty or whitespace-only strings
            raise ValueError("name cannot be empty or whitespace-only")

    # Validate handle parameter
    if handle is not None:
        if not isinstance(handle, str):
            raise TypeError("handle must be a string if provided")
        if not handle.strip():  # Reject empty or whitespace-only strings
            raise ValueError("handle cannot be empty or whitespace-only")

    # Validate description parameter
    if description is not None:
        if not isinstance(description, str):
            raise TypeError("description must be a string if provided")

    # Validate channel_ids parameter
    if channel_ids is not None:
        if not isinstance(channel_ids, type([])):  # Use built-in list type
            raise TypeError("channel_ids must be a list if provided")
        # Validate that all elements in channel_ids are strings
        for channel_id in channel_ids:
            if not isinstance(channel_id, str):
                raise TypeError("all elements in channel_ids must be strings")

    # Validate date_update parameter
    if date_update is not None:
        if not isinstance(date_update, str):
            raise TypeError("date_update must be a string if provided")

    # --- End Input Validation ---

    if usergroup_id not in DB.get("usergroups", {}):
        raise UserGroupNotFoundError(f"User group {usergroup_id} not found")

    usergroup = DB["usergroups"][usergroup_id]

    # Check for duplicate usergroup name (case-insensitive) if name is updated
    if name:
        for id, data in DB.get("usergroups", {}).items():
            if id != usergroup_id and data["name"].lower() == name.lower():
                raise ValueError(f"A user group with the name '{name}' already exists")
    
    # Check for duplicate usergroup handle (case-insensitive) if handle is updated
    if handle:
        for id, data in DB.get("usergroups", {}).items():
            if id != usergroup_id and data["handle"] and data["handle"].lower() == handle.lower():
                raise ValueError(f"A user group with the handle '{handle}' already exists")
    
    # Validate channel_ids exist in database
    if channel_ids is not None:
        for channel_id in channel_ids:
            if channel_id not in DB["channels"]:
                raise ValueError(f"Invalid channel ID: '{channel_id}'")
        usergroup["prefs"]["channels"] = channel_ids

    # Update fields if provided
    if name is not None:
        usergroup["name"] = name
    if handle is not None:
        usergroup["handle"] = handle
    if description is not None:
        usergroup["description"] = description

    usergroup["date_update"] = date_update if date_update else str(time.time())
    usergroup["updated_by"] = ""

    return {"ok": True, "usergroup": usergroup}


@tool_spec(
    spec={
        'name': 'disable_user_group',
        'description': 'Disables a User Group.',
        'parameters': {
            'type': 'object',
            'properties': {
                'usergroup_id': {
                    'type': 'string',
                    'description': 'The ID of the User Group to disable.'
                },
                'date_delete': {
                    'type': 'string',
                    'description': """ Timestamp string when the User Group was deleted.
                    If None, current time will be used. """
                }
            },
            'required': [
                'usergroup_id'
            ]
        }
    }
)
def disable(usergroup_id: str, date_delete: Optional[str] = None) -> Dict[str, Any]:
    """
    Disables a User Group.

    Args:
        usergroup_id (str): The ID of the User Group to disable.
        date_delete (Optional[str]): Timestamp string when the User Group was deleted.
                                     If None, current time will be used.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): True if the request was successful.

    Raises:
        TypeError: If `usergroup_id` is not a string, or if `date_delete`
                   is provided and is not a string.
        UserGroupIdInvalidError: If `usergroup_id` is an empty string.
        UserGroupNotFoundError: If the `usergroup_id` does not exist.
        UserGroupAlreadyDisabledError: If the user group is already disabled.
    """
    # --- Input Validation ---
    if not isinstance(usergroup_id, str):
        raise TypeError("usergroup_id must be a string.")
    
    if not usergroup_id:
        raise UserGroupIdInvalidError("usergroup_id cannot be empty.")
    
    if date_delete and not isinstance(date_delete, str):
        raise TypeError("date_delete must be a string if provided.")
    # --- End Input Validation ---

    usergroups_data = DB.get("usergroups")
    if usergroup_id not in DB.get("usergroups", {}):
        raise UserGroupNotFoundError(f"User group {usergroup_id} not found.")

    usergroup_entry = usergroups_data[usergroup_id]

    if DB["usergroups"][usergroup_id]["disabled"]:
        raise UserGroupAlreadyDisabledError(f"User group {usergroup_id} is already disabled.")

    usergroup_entry["disabled"] = True
    usergroup_entry["date_delete"] = date_delete if date_delete else str(time.time())
    usergroup_entry["deleted_by"] = "" # As per original logic

    return {"ok": True}

@tool_spec(
    spec={
        'name': 'enable_user_group',
        'description': """ Enables a User Group.
        
        This method enables a user group that has been disabled.
        It resets the disabled flag and the deleted timestamp.
        It also resets the user who deleted it. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'usergroup_id': {
                    'type': 'string',
                    'description': 'The ID of the User Group to enable.'
                }
            },
            'required': [
                'usergroup_id'
            ]
        }
    }
)
def enable(usergroup_id: str) -> Dict[str, Any]:
    """
    Enables a User Group.

    This method enables a user group that has been disabled.
    It resets the disabled flag and the deleted timestamp.
    It also resets the user who deleted it.

    Args:
        usergroup_id (str): The ID of the User Group to enable.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the request was successful

    Raises:
        TypeError: If `usergroup_id` is not a string.
        UserGroupIdInvalidError: If `usergroup_id` is an empty string.
        UserGroupNotFoundError: If the `usergroup_id` does not exist.
    """
    if not isinstance(usergroup_id, str):
        raise TypeError("usergroup_id must be a string.")

    if not usergroup_id:
        raise UserGroupIdInvalidError("usergroup_id cannot be empty.")

    if usergroup_id not in DB.get("usergroups", {}):
        raise UserGroupNotFoundError(f"User group {usergroup_id} not found.")

    DB["usergroups"][usergroup_id]["disabled"] = False
    DB["usergroups"][usergroup_id]["date_delete"] = 0  # Reset deleted timestamp
    DB["usergroups"][usergroup_id]["deleted_by"] = None # Reset the user who deleted it
    return {"ok": True}