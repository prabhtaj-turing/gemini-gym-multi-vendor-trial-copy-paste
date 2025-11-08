from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/SettingsApi.py
from typing import Dict, Any, List
from .SimulationEngine.db import DB

@tool_spec(
    spec={
        'name': 'get_all_settings',
        'description': """ Get all settings.
        
        This method returns all settings in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_settings() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all settings.

    This method returns all settings in the system.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing all the unique settings as a list of dictionaries 
        where each dictionary contains one setting key-value pair with setting as the key and its value as the value.
        
        - settings (List[Dict[str, Any]]): A list of dictionaries containing all the unique settings

    """
    settings = []
    users = DB.get("users", {})
    for key, value in users.items():
        user_settings = value.get("settings", {})
        for setting, setting_value in user_settings.items():
            if {setting: setting_value} not in settings:
                settings.append({setting: setting_value})

    return {"settings": settings}
