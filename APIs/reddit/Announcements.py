from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List
from .SimulationEngine.db import DB

"""
Simulation of /announcements endpoints.
Manages global announcements and their interaction with users.
"""

@tool_spec(
    spec={
        'name': 'get_global_announcements',
        'description': 'Retrieves a list of global announcements.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_api_announcements_v1() -> List[Dict[str, Any]]:
    """
    Retrieves a list of global announcements.

    Returns:
        List[Dict[str, Any]]: A list of announcement objects, each containing:
            - id (str): Unique identifier of the announcement
            - title (str): Title of the announcement
            - content (str): Content of the announcement
            - created_at (str): Timestamp of when the announcement was created
    """
    return DB["announcements"]

@tool_spec(
    spec={
        'name': 'hide_announcements',
        'description': "Hides one or more announcements from the authenticated user's feed.",
        'parameters': {
            'type': 'object',
            'properties': {
                'announcement_ids': {
                    'type': 'array',
                    'description': 'A list of announcement IDs to hide.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'announcement_ids'
            ]
        }
    }
)
def post_api_announcements_v1_hide(announcement_ids: List[str]) -> Dict[str, Any]:
    """
    Hides one or more announcements from the authenticated user's feed.

    Args:
        announcement_ids (List[str]): A list of announcement IDs to hide.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): The status of the hide operation
            - hidden_ids (List[str]): List of successfully hidden announcement IDs
    """
    # We won't do anything real; just return success
    return {"status": "announcements_hidden", "ids": announcement_ids}

@tool_spec(
    spec={
        'name': 'mark_announcements_as_read',
        'description': 'Marks one or more announcements as read.',
        'parameters': {
            'type': 'object',
            'properties': {
                'announcement_ids': {
                    'type': 'array',
                    'description': 'A list of announcement IDs to mark as read.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'announcement_ids'
            ]
        }
    }
)
def post_api_announcements_v1_read(announcement_ids: List[str]) -> Dict[str, Any]:
    """
    Marks one or more announcements as read.

    Args:
        announcement_ids (List[str]): A list of announcement IDs to mark as read.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): The status of the read operation
            - read_ids (List[str]): List of successfully marked announcement IDs
    """
    return {"status": "announcements_marked_read", "ids": announcement_ids}

@tool_spec(
    spec={
        'name': 'mark_all_announcements_as_read',
        'description': 'Marks all global announcements as read.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_announcements_v1_read_all() -> Dict[str, Any]:
    """
    Marks all global announcements as read.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (str): The status of the operation
            - message (str): Confirmation message
    """
    return {"status": "all_announcements_marked_read"}

@tool_spec(
    spec={
        'name': 'get_unread_announcements',
        'description': 'Retrieves a list of announcements not yet read by the user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_api_announcements_v1_unread() -> List[Dict[str, Any]]:
    """
    Retrieves a list of announcements not yet read by the user.

    Returns:
        List[Dict[str, Any]]: A list of unread announcement objects, each containing:
            - id (str): Unique identifier of the announcement
            - title (str): Title of the announcement
            - content (str): Content of the announcement
            - created_at (str): Timestamp of when the announcement was created
    """
    # In a real scenario, we'd filter unread. Here, just return entire list
    return DB["announcements"]