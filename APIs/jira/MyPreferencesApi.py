from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/MyPreferencesApi.py
from .SimulationEngine.utils import _check_empty_field
from .SimulationEngine.db import DB
from .SimulationEngine.models import UserPreferencesUpdate
from typing import Dict, Optional, Any
from pydantic import ValidationError


@tool_spec(
    spec={
        'name': 'get_current_user_preferences',
        'description': """ Get the current user's preferences.
        
        This method returns the preferences of the current user from the database. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_my_preferences() -> Dict[str, str]:
    """
    Get the current user's preferences.

    This method returns the preferences of the current user from the database.

    Returns:
        Dict[str, str]: A dictionary containing the current user's preferences with keys:
            - theme (str): The theme preference (e.g., 'dark', 'light', 'auto')
            - notifications (str): The notification preference (e.g., 'enabled', 'disabled', 'email_only')
    """
    return DB.get("my_preferences", {})


@tool_spec(
    spec={
        'name': 'update_current_user_preferences',
        'description': """ Update the current user's preferences.
        
        This method updates the preferences of the current user with the provided values. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'value': {
                    'type': 'object',
                    'description': 'The preferences to update. Must contain one or more of:',
                    'properties': {
                        'theme': {
                            'type': 'string',
                            'description': 'The theme of the current user'
                        },
                        'notifications': {
                            'type': 'string',
                            'description': 'The notifications of the current user'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'value'
            ]
        }
    }
)
def update_my_preferences(value: dict) -> Dict[str, Any]:
    """
    Update the current user's preferences.

    This method updates the preferences of the current user with the provided values.

    Args:
        value (dict): The preferences to update. Must contain one or more of:
            - theme (Optional[str]): The theme of the current user
            - notifications (Optional[str]): The notifications of the current user

    Returns:
        Dict[str, Any]: A dictionary containing the updated preferences:
            - updated (bool): Always True indicating successful update
            - preferences (Dict[str, str]): The updated preferences containing current values with keys:
                - theme (str): The theme preference (e.g., 'dark', 'light')
                - notifications (str): The notification preference (e.g., 'enabled', 'disabled')

    Raises:
        TypeError: If value is not a dictionary
        ValidationError: If value contains invalid data structure or types
        ValueError: If value is empty
    """
    # Type validation
    if not isinstance(value, dict):
        raise TypeError("value must be a dictionary")
    
    # Empty field validation
    err = _check_empty_field("value", value)
    if err:
        raise ValueError(f"Argument '{err}' cannot be empty.")
    
    # Pydantic validation for structure and types
    try:
        validated_preferences = UserPreferencesUpdate(**value)
    except ValidationError as e:
        raise e
    
    # Update preferences with validated data (only non-None values)
    updates = validated_preferences.dict(exclude_none=True)
    DB["my_preferences"].update(updates)
    return {"updated": True, "preferences": DB["my_preferences"]}
