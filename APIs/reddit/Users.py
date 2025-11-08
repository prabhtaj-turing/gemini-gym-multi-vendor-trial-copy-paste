from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any, List, Optional

"""
Simulation of /users endpoints.
Manages user-specific actions and data retrieval.
"""


@tool_spec(
    spec={
        'name': 'block_user',
        'description': 'Blocks a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'account_id': {
                    'type': 'string',
                    'description': 'The account ID of the user to block.'
                }
            },
            'required': [
                'account_id'
            ]
        }
    }
)
def post_api_block_user(account_id: str) -> Dict[str, Any]:
    """
    Blocks a user.

    Args:
        account_id (str): The account ID of the user to block.

    Returns:
        Dict[str, Any]:
        - If the account ID is invalid, returns a dictionary with the key "error" and the value "Invalid account ID.".
        - If the user is already blocked, returns a dictionary with the key "error" and the value "User already blocked.".
        - On successful blocking, returns a dictionary with the following keys:
            - status (str): The status of the operation ("user_blocked")
            - account_id (str): The blocked user's account ID
    """
    return {"status": "user_blocked", "account_id": account_id}


@tool_spec(
    spec={
        'name': 'add_friend',
        'description': 'Adds a user as a friend.',
        'parameters': {
            'type': 'object',
            'properties': {
                'api_type': {
                    'type': 'string',
                    'description': 'Must be "json".'
                },
                'name': {
                    'type': 'string',
                    'description': 'The username to add as a friend.'
                }
            },
            'required': [
                'api_type',
                'name'
            ]
        }
    }
)
def post_api_friend(api_type: str, name: str) -> Dict[str, Any]:
    """
    Adds a user as a friend.

    Args:
        api_type (str): Must be "json".
        name (str): The username to add as a friend.

    Returns:
        Dict[str, Any]:
        - If the API type is invalid, returns a dictionary with the key "error" and the value "Invalid API type.".
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - If the user is already a friend, returns a dictionary with the key "error" and the value "User already a friend.".
        - On successful addition, returns a dictionary with the following keys:
            - status (str): The status of the operation ("friend_added")
            - user (str): The added friend's username
    """
    return {"status": "friend_added", "user": name}


@tool_spec(
    spec={
        'name': 'report_user',
        'description': 'Reports a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user': {
                    'type': 'string',
                    'description': 'The username to report.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'The reason for reporting.'
                }
            },
            'required': [
                'user'
            ]
        }
    }
)
def post_api_report_user(user: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Reports a user.

    Args:
        user (str): The username to report.
        reason (Optional[str]): The reason for reporting.

    Returns:
        Dict[str, Any]:
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - If the user is already reported, returns a dictionary with the key "error" and the value "User already reported.".
        - On successful reporting, returns a dictionary with the following keys:
            - status (str): The status of the operation ("user_reported")
            - user (str): The reported username
            - reason (Optional[str]): The reason for reporting
    """
    return {"status": "user_reported", "user": user, "reason": reason}


@tool_spec(
    spec={
        'name': 'set_user_permissions',
        'description': 'Sets permissions for a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The username for whom to set permissions.'
                },
                'permissions': {
                    'type': 'array',
                    'description': 'A list of permissions to grant.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def post_api_setpermissions(name: str, permissions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Sets permissions for a user.

    Args:
        name (str): The username for whom to set permissions.
        permissions (Optional[List[str]]): A list of permissions to grant.

    Returns:
        Dict[str, Any]:
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - If the permissions are invalid, returns a dictionary with the key "error" and the value "Invalid permissions.".
        - On successful update, returns a dictionary with the following keys:
            - status (str): The status of the operation ("permissions_set")
            - user (str): The username
            - permissions (List[str]): The granted permissions
    """
    return {"status": "permissions_set", "user": name, "permissions": permissions or []}


@tool_spec(
    spec={
        'name': 'remove_friend',
        'description': 'Removes a friend relationship.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The username to unfriend.'
                },
                'type': {
                    'type': 'string',
                    'description': 'The relationship type (e.g., "friend").'
                }
            },
            'required': [
                'name',
                'type'
            ]
        }
    }
)
def post_api_unfriend(name: str, type: str) -> Dict[str, Any]:
    """
    Removes a friend relationship.

    Args:
        name (str): The username to unfriend.
        type (str): The relationship type (e.g., "friend").

    Returns:
        Dict[str, Any]:
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - If the relationship type is invalid, returns a dictionary with the key "error" and the value "Invalid relationship type.".
        - If the user is not a friend, returns a dictionary with the key "error" and the value "User not a friend.".
        - On successful removal, returns a dictionary with the following keys:
            - status (str): The status of the operation ("relationship_removed")
            - user (str): The unfriended username
            - type (str): The relationship type
    """
    return {"status": "relationship_removed", "user": name, "type": type}


@tool_spec(
    spec={
        'name': 'get_user_data_by_account_ids',
        'description': 'Retrieves user data for specified account IDs.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ids': {
                    'type': 'string',
                    'description': 'A comma-separated list of account IDs.'
                }
            },
            'required': [
                'ids'
            ]
        }
    }
)
def get_api_user_data_by_account_ids(ids: str) -> Dict[str, Any]:
    """
    Retrieves user data for specified account IDs.

    Args:
        ids (str): A comma-separated list of account IDs.

    Returns:
        Dict[str, Any]:
        - If the IDs are invalid, returns a dictionary with the key "error" and the value "Invalid account IDs.".
        - On successful retrieval, returns a dictionary with the following keys:
            - ids (List[str]): The list of account IDs
            - user_data (List[Dict[str, Any]]): A list of user data objects, each containing:
                - id (str): The account ID
                - username (str): The username
                - created_utc (int): The creation timestamp
    """
    return {"ids": ids.split(','), "user_data": []}


@tool_spec(
    spec={
        'name': 'check_username_availability',
        'description': 'Checks if a username is available.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user': {
                    'type': 'string',
                    'description': 'The username to check.'
                }
            },
            'required': [
                'user'
            ]
        }
    }
)
def get_api_username_available(user: str) -> Dict[str, Any]:
    """
    Checks if a username is available.

    Args:
        user (str): The username to check.

    Returns:
        Dict[str, Any]:
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - On successful check, returns a dictionary with the following keys:
            - username (str): The checked username
            - available (bool): Whether the username is available
    """
    return {"username": user, "available": True}


@tool_spec(
    spec={
        'name': 'remove_friend_by_username',
        'description': 'Removes a friend relationship.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The username to remove.'
                }
            },
            'required': [
                'username'
            ]
        }
    }
)
def delete_api_v1_me_friends_username(username: str) -> Dict[str, Any]:
    """
    Removes a friend relationship.

    Args:
        username (str): The username to remove.

    Returns:
        Dict[str, Any]:
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - If the user is not a friend, returns a dictionary with the key "error" and the value "User not a friend.".
        - On successful removal, returns a dictionary with the following keys:
            - status (str): The status of the operation ("user_unfriended")
            - username (str): The unfriended username
    """
    return {"status": "user_unfriended", "username": username}


@tool_spec(
    spec={
        'name': 'get_user_trophies',
        'description': 'Retrieves trophies for a specified user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The target username.'
                }
            },
            'required': [
                'username'
            ]
        }
    }
)
def get_api_v1_user_username_trophies(username: str) -> Dict[str, Any]:
    """
    Retrieves trophies for a specified user.

    Args:
        username (str): The target username.

    Returns:
        Dict[str, Any]:
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - On successful retrieval, returns a dictionary with the following keys:
            - username (str): The target username
            - trophies (List[Dict[str, Any]]): A list of trophy objects, each containing:
                - name (str): The trophy name
                - description (str): The trophy description
                - icon_url (str): The trophy icon URL
    """
    return {"username": username, "trophies": []}


@tool_spec(
    spec={
        'name': 'get_user_profile_info',
        'description': 'Retrieves profile information for a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The username.'
                }
            },
            'required': [
                'username'
            ]
        }
    }
)
def get_user_username_about(username: str) -> Dict[str, Any]:
    """
    Retrieves profile information for a user.

    Args:
        username (str): The username.

    Returns:
        Dict[str, Any]:
        - If the username is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - If the user is not found, returns a dictionary with the key "status" and the value "not_found".
        - On successful retrieval, returns a dictionary with the following keys:
            - status (str): The status of the operation ("ok")
            - profile (Dict[str, Any]): A dictionary containing user profile information
    """
    if username in DB.get("users", {}): # Use .get for safety
        return {"status": "ok", "profile": DB["users"][username]}
    return {"status": "not_found"}


@tool_spec(
    spec={
        'name': 'get_user_comments',
        'description': 'Retrieves comments made by a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The username.'
                }
            },
            'required': [
                'username'
            ]
        }
    }
)
def get_user_username_comments(username: str) -> List[Dict[str, Any]]:
    """
    Retrieves comments made by a user.

    Args:
        username (str): The username.

    Returns:
        List[Dict[str, Any]]:
        - If the username is invalid, returns an empty list.
        - If there are no comments, returns an empty list.
        - On successful retrieval, returns a list of comment objects, each containing:
            - id (str): The comment ID
            - body (str): The comment text
            - created_utc (int): The creation timestamp
            - subreddit (str): The subreddit name
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_downvoted_posts',
        'description': 'Retrieves posts downvoted by a user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_user_username_downvoted() -> List[str]:
    """
    Retrieves posts downvoted by a user.

    Returns:
        List[str]:
        - If there are no downvoted posts, returns an empty list.
        - On successful retrieval, returns a list of downvoted post identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_gilded_posts',
        'description': 'Retrieves posts that have been gilded for a user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_user_username_gilded() -> List[str]:
    """
    Retrieves posts that have been gilded for a user.

    Returns:
        List[str]:
        - If there are no gilded posts, returns an empty list.
        - On successful retrieval, returns a list of gilded post identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_hidden_posts',
        'description': 'Retrieves hidden posts of a user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_user_username_hidden() -> List[str]:
    """
    Retrieves hidden posts of a user.

    Returns:
        List[str]:
        - If there are no hidden posts, returns an empty list.
        - On successful retrieval, returns a list of hidden post identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_overview',
        'description': "Retrieves an overview of a user's submissions and comments.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_user_username_overview() -> List[Dict[str, Any]]:
    """
    Retrieves an overview of a user's submissions and comments.

    Returns:
        List[Dict[str, Any]]:
        - If there is no content, returns an empty list.
        - On successful retrieval, returns a combined list of the user's submissions and comments, each containing:
            - id (str): The content ID
            - type (str): Either "submission" or "comment"
            - created_utc (int): The creation timestamp
            - subreddit (str): The subreddit name
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_saved_posts',
        'description': 'Retrieves posts saved by a user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_user_username_saved() -> List[str]:
    """
    Retrieves posts saved by a user.

    Returns:
        List[str]:
        - If there are no saved posts, returns an empty list.
        - On successful retrieval, returns a list of saved post identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_submitted_posts',
        'description': 'Retrieves posts submitted by a user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_user_username_submitted() -> List[str]:
    """
    Retrieves posts submitted by a user.

    Returns:
        List[str]:
        - If there are no submitted posts, returns an empty list.
        - On successful retrieval, returns a list of submitted post identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_upvoted_posts',
        'description': 'Retrieves posts upvoted by a user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_user_username_upvoted() -> List[str]:
    """
    Retrieves posts upvoted by a user.

    Returns:
        List[str]:
        - If there are no upvoted posts, returns an empty list.
        - On successful retrieval, returns a list of upvoted post identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_user_content_by_category',
        'description': 'Retrieves user content for a specified category.',
        'parameters': {
            'type': 'object',
            'properties': {
                'where': {
                    'type': 'string',
                    'description': 'The category (e.g., "overview", "comments").'
                }
            },
            'required': [
                'where'
            ]
        }
    }
)
def get_user_username_where(where: str) -> List[Dict[str, Any]]:
    """
    Retrieves user content for a specified category.

    Args:
        where (str): The category (e.g., "overview", "comments").

    Returns:
        List[Dict[str, Any]]:
        - If the category is invalid, returns an empty list.
        - If there is no content in the category, returns an empty list.
        - On successful retrieval, returns a list of content items for the specified category, each containing:
            - id (str): The content ID
            - type (str): The content type
            - created_utc (int): The creation timestamp
            - subreddit (str): The subreddit name
    """
    return []