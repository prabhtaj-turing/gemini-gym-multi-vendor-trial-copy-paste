from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Users.py
from typing import Dict, Any, Union
import sys
import os

sys.path.append("APIs")

from canva.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_current_user',
        'description': 'Retrieves the team-related user information for the given user ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'Unique identifier of the user.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def get_current_user(user_id: str) -> Dict[str, Union[str, Dict]]:
    """
    Retrieves the team-related user information for the given user ID.

    Args:
        user_id (str): Unique identifier of the user.

    Returns:
        Dict[str, Union[str, Dict]]: A dictionary with the key 'team_user' containing:
            - user_id (str): The ID of the user.
            - team_id (str): The ID of the user's Canva Team.
        Returns an empty dictionary if the user is not found.
    """
    if user_id in DB["Users"]:
        uid = DB["Users"][user_id]["user_id"]
        team_id = DB["Users"][user_id]["team_id"]

        return {"team_user": {"user_id": uid, "team_id": team_id}}
    else:
        return {}


@tool_spec(
    spec={
        'name': 'get_current_user_profile',
        'description': 'Retrieves the profile data for the given user ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'Unique identifier of the user.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def get_current_user_profile(user_id: str) -> Dict[str, Union[str, Dict]]:
    """
    Retrieves the profile data for the given user ID.

    Args:
        user_id (str): Unique identifier of the user.

    Returns:
        Dict[str, Union[str, Dict]]: A dictionary with the key 'profile' containing:
            - display_name (str, optional): The user's name as shown in the Canva UI.
        Returns an empty dictionary if the user is not found.
    """
    if user_id in DB["Users"]:
        return DB["Users"][user_id]["profile"]
    else:
        return {}
