"""
UsergroupUsers resource for Slack API simulation.

This module provides functionality for managing user group users in Slack.
It simulates the usergroup.users-related endpoints of the Slack API.
"""
from common_utils.tool_spec_decorator import tool_spec
import time
from typing import Dict, Any, Optional

from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    UserGroupIdInvalidError,
    UserGroupNotFoundError,
    UserNotFoundError,
    InvalidUsersError
)
from .SimulationEngine import custom_errors


@tool_spec(
    spec={
        'name': 'update_user_group_members',
        'description': 'Update the list of users for a User Group.',
        'parameters': {
            'type': 'object',
            'properties': {
                'usergroup': {
                    'type': 'string',
                    'description': 'The encoded ID of the User Group to update.'
                },
                'users': {
                    'type': 'string',
                    'description': 'A comma separated string of encoded user IDs that represent the entire list of users for the User Group.'
                },
                'include_count': {
                    'type': 'boolean',
                    'description': 'Include the number of users in the User Group. Defaults to False.'
                },
                'date_update': {
                    'type': 'string',
                    'description': """ Timestamp when the User Group was last updated. If None or empty, 
                    the current timestamp will be used. """
                }
            },
            'required': [
                'usergroup',
                'users'
            ]
        }
    }
)
def update(
    usergroup: str,
    users: str,
    include_count: bool = False,
    date_update: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update the list of users for a User Group.

    Args:
        usergroup (str): The encoded ID of the User Group to update.
        users (str): A comma separated string of encoded user IDs that represent the entire list of users for the User Group.
        include_count (bool): Include the number of users in the User Group. Defaults to False.
        date_update (Optional[str]): Timestamp when the User Group was last updated. If None or empty, 
            the current timestamp will be used.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - usergroup (Dict[str, Any]): The updated User Group object containing:
                - users (List[str]): List of user IDs in the group
                - user_count (int): Number of users in the group (only included if include_count is True)
                - updated_by (str): ID of user who last updated the group
                - date_update (str): Timestamp of last update

    Raises:
        UserGroupIdInvalidError: If the usergroup ID is empty or invalid
        InvalidUsersError: If the users string is empty or invalid
        UserGroupNotFoundError: If the specified usergroup does not exist
        UserNotFoundError: If any of the provided user IDs do not exist in the database
    """

    if not usergroup or not isinstance(usergroup, str):
        raise UserGroupIdInvalidError(f"Invalid property usergroup {usergroup}")
    if not users or not isinstance(users, str):
        raise InvalidUsersError(f"Invalid property users {users}")

    if usergroup not in DB.get("usergroups", {}):
        raise UserGroupNotFoundError(f"User group {usergroup} not found")

    # Validate that all provided user_ids exist
    user_ids = users.split(",")
    for user_id in user_ids:
        if user_id not in DB["users"]:
            raise UserNotFoundError(f"User {user_id} not found")

    # Update the usergroup with new users
    usergroup_data = DB["usergroups"][usergroup]
    usergroup_data["users"] = user_ids
    
    # Only include user_count if include_count is True
    if include_count:
        usergroup_data["user_count"] = len(user_ids)
    elif "user_count" in usergroup_data:
        del usergroup_data["user_count"]

    # Set the updated_by field to the first user in the list (simulating the user who made the update)
    usergroup_data["updated_by"] = user_ids[0] if user_ids else ""
    usergroup_data["date_update"] = date_update if date_update else str(time.time())

    return {"ok": True, "usergroup": usergroup_data}


@tool_spec(
    spec={
        'name': 'list_user_group_members',
        'description': 'Lists all users in a User Group.',
        'parameters': {
            'type': 'object',
            'properties': {
                'usergroup_id': {
                    'type': 'string',
                    'description': 'The ID of the User Group.'
                },
                'include_disabled': {
                    'type': 'boolean',
                    'description': 'Include disabled users. Defaults to False.'
                }
            },
            'required': [
                'usergroup_id'
            ]
        }
    }
)
def list(usergroup_id: str, include_disabled: bool = False) -> Dict[str, Any]:
    """
    Lists all users in a User Group.

    Args:
        usergroup_id (str): The ID of the User Group.
        include_disabled (bool): Include disabled users. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - users (List[Dict[str, Any]]): List of user objects, where each user contains:
                - id (str): User ID
                - name (str): User name
                - real_name (str): User's real name
                - team_id (str): Team ID
                - is_admin (bool): Whether user is an admin
                - is_owner (bool): Whether user is an owner
                - is_primary_owner (bool): Whether user is primary owner
                - is_restricted (bool): Whether user is restricted
                - is_ultra_restricted (bool): Whether user is ultra restricted
                - is_bot (bool): Whether user is a bot
                - is_app_user (bool): Whether user is an app user
                - updated (int): Last update timestamp

    Raises:
        UserGroupIdInvalidError: If usergroup_id is empty or not a string
        UserGroupNotFoundError: If the specified usergroup_id does not exist
        InconsistentDataError: If a user in the usergroup is not found in the users database
        IncludeDisabledInvalidError: If include_disabled is not a boolean
    """
    if not usergroup_id or not isinstance(usergroup_id, str):
        raise custom_errors.UserGroupIdInvalidError("Invalid property usergroup_id")
    
    if not isinstance(include_disabled, bool):
        raise custom_errors.IncludeDisabledInvalidError("Invalid property include_disabled")

    if usergroup_id not in DB.get("usergroups", {}):
        raise custom_errors.UserGroupNotFoundError("User group not found")

    # Get the list of user IDs
    user_ids = DB["usergroups"][usergroup_id]["users"]

    # Retrieve user details for each user ID
    users = []

    for user_id in user_ids:
        if user_id not in DB["users"]:
            raise custom_errors.InconsistentDataError(f"User {user_id} in usergroup but not in users DB.")
        
        users.append(DB["users"][user_id])

    return {"ok": True, "users": users}