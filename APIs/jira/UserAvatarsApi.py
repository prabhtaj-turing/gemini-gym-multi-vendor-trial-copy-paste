from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/UserAvatarsApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _check_empty_field
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'get_user_avatars_by_username',
        'description': 'Get all avatars that are visible to the current user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The username of the user to get avatars for.'
                }
            },
            'required': [
                'username'
            ]
        }
    }
)
def get_user_avatars(username: str) -> Dict[str, Any]:
    """
    Get all avatars that are visible to the current user.

    Args:
        username (str): The username of the user to get avatars for.

    Returns:
        Dict[str, Any]: A dictionary containing the user's avatars.
            - username (str): The username of the user.
            - avatars (List[Dict[str, Any]]): The list of avatars. Currently lists all user avatars.
                - type (str): The type of avatar.
                - filename (str): The filename of the avatar.
                - id (str): The id of the avatar.

    Raises:
        ValueError: If the username is not provided.
    """
    err = _check_empty_field("username", username)
    if err:
        return {"error": err}
    # Return all avatars that might relate to a user, or all if not tracked specifically
    user_avatars = [a for a in DB["avatars"] if a["type"] == "user"]
    return {"username": username, "avatars": user_avatars}
