"""
App Settings API

A tool that can be used to retrieve installed apps and manage app notification settings on the user's device.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List
from datetime import datetime, timezone

from device_setting.SimulationEngine.utils import (
    get_device_info, update_app_notification
)
from device_setting.SimulationEngine.utils import generate_card_id, create_action_card
from device_setting.SimulationEngine.models import Action
from device_setting.SimulationEngine.enums import ActionType, Constants, ToggleState
from device_setting.SimulationEngine.custom_errors import AppNotInstalledError


@tool_spec(
    spec={
        'name': 'get_installed_apps',
        'description': 'Retrieves a list of all applications installed on the device, excluding their notification settings.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_installed_apps() -> Dict[str, Any]:
    """
    Retrieves a list of all applications installed on the device, excluding their notification settings.
    
    Returns:
        Dict[str, Any]: Response containing:
            - apps (List[str]): List of installed app names
            - action_card_content_passthrough (str): Action card content for UI display
            - card_id (str): Card identifier for UI components
            
    Example:
        >>> get_installed_apps()
        {
            "apps": ["Messages", "Mail", "Calendar", "Photos"],
            "action_card_content_passthrough": "...",
            "card_id": "uuid-string"
        }
    """
    # Get installed apps from database
    device_data = get_device_info()
    installed_apps_data = device_data.get(Constants.INSTALLED_APPS.value, {}).get(Constants.APPS.value, {})
    
    # Extract just the app names
    installed_apps = list(installed_apps_data.keys())
    
    # Generate response
    card_id = generate_card_id()
    action_card_content = create_action_card(
        ActionType.GET_INSTALLED_APPS,
        message=f"Retrieved {len(installed_apps)} installed applications"
    )
    
    response = {
        Constants.APPS.value: installed_apps,
        "action_card_content_passthrough": action_card_content,
        "card_id": card_id
    }
    
    return response


@tool_spec(
    spec={
        'name': 'get_app_notification_status',
        'description': 'Gets the current notification setting for a specific app.',
        'parameters': {
            'type': 'object',
            'properties': {
                'app_name': {
                    'type': 'string',
                    'description': 'Name of the app to get notification settings for'
                }
            },
            'required': [
                'app_name'
            ]
        }
    }
)
def get_app_notification_status(app_name: str) -> Dict[str, Any]:
    """
    Gets the current notification setting for a specific app.
    
    Args:
        app_name (str): Name of the app to get notification settings for
        
    Returns:
        Dict[str, Any]: Response containing:
            - app_name (str): Name of the app
            - notifications (str): Current notification status ("on" or "off")
            - last_updated (str): ISO timestamp of last update
            - action_card_content_passthrough (str): Action card content for UI display
            - card_id (str): Card identifier for UI components
            
    Raises:
        ValueError: If app_name is not provided or app doesn't exist in installed_apps
        
    Example:
        >>> get_app_notification_status("Messages")
        {
            "app_name": "Messages",
            "notifications": "on",
            "last_updated": "2024-01-15T10:30:00Z",
            "action_card_content_passthrough": "...",
            "card_id": "uuid-string"
        }
    """
    # Validate input
    if not app_name or not isinstance(app_name, str) or not app_name.strip():
        raise ValueError("app_name is required and must be a non-empty string")
    
    app_name = app_name.strip()
    
    # Check if app is installed
    device_data = get_device_info()
    installed_apps_data = device_data.get(Constants.INSTALLED_APPS.value, {}).get(Constants.APPS.value, {})
    
    if app_name not in installed_apps_data:
        raise ValueError(f"App '{app_name}' is not installed on the device")
    
    # Get app notification settings
    app_settings = installed_apps_data.get(app_name, {}).get(Constants.NOTIFICATIONS.value, {})
    
    # Default to "on" if no setting exists
    notifications = app_settings.get(Constants.VALUE.value, ToggleState.ON.value)
    last_updated = app_settings.get(Constants.LAST_UPDATED.value, datetime.now(timezone.utc).isoformat())
    
    # Generate response
    card_id = generate_card_id()
    action_card_content = create_action_card(
        ActionType.GET_APP_NOTIFICATION_STATUS,
        app_name=app_name,
        notifications=notifications,
        message=f"Retrieved notification status for {app_name}: {notifications}"
    )
    
    response = {
        "app_name": app_name,
        "notifications": notifications,
        "last_updated": last_updated,
        "action_card_content_passthrough": action_card_content,
        "card_id": card_id
    }
    
    return response


@tool_spec(
    spec={
        'name': 'set_app_notification_status',
        'description': 'Sets the current notification setting for a specific app.',
        'parameters': {
            'type': 'object',
            'properties': {
                'app_name': {
                    'type': 'string',
                    'description': 'Name of the app to modify (case-insensitive)'
                },
                'notifications': {
                    'type': 'string',
                    'description': '"on" or "off" to set the notification state'
                }
            },
            'required': [
                'app_name',
                'notifications'
            ]
        }
    }
)
def set_app_notification_status(app_name: str, notifications: str) -> Dict[str, Any]:
    """
    Sets the current notification setting for a specific app.
    
    Args:
        app_name (str): Name of the app to modify (case-insensitive)
        notifications (str): "on" or "off" to set the notification state
        
    Returns:
        Dict[str, Any]: Response containing:
            - result (str): Result message of the action
            - action_card_content_passthrough (str): Action card content for UI display
            - card_id (str): Card identifier for UI components
            
    Raises:
        ValueError: If app_name is not provided, app doesn't exist, or notifications value is invalid
        
    Example:
        >>> set_app_notification_status("Messages", "off")
        {
            "result": "Successfully set Messages notifications to off",
            "action_card_content_passthrough": "...",
            "card_id": "uuid-string"
        }
    """
    # Validate inputs
    if not app_name or not isinstance(app_name, str) or not app_name.strip():
        raise ValueError("app_name is required and must be a non-empty string")
    
    if not notifications or not isinstance(notifications, str):
        raise ValueError(f"{Constants.NOTIFICATIONS.value} is required and must be a string")
    
    app_name = app_name.strip()
    notifications_lower = notifications.strip().lower()
    
    # Validate notifications value
    if notifications_lower not in [ToggleState.ON.value, ToggleState.OFF.value]:
        raise ValueError(f"notifications must be either '{ToggleState.ON.value}' or '{ToggleState.OFF.value}'")
    
    notifications_enum = ToggleState(notifications_lower)
    
    # Check if app is installed
    device_data = get_device_info()
    installed_apps_data = device_data.get(Constants.INSTALLED_APPS.value, {}).get(Constants.APPS.value, {})
    
    # Find the app with case-insensitive matching
    app_key = None
    for key in installed_apps_data.keys():
        if key.lower() == app_name.lower():
            app_key = key
            break

    if app_key is None:
        raise AppNotInstalledError(f"App '{app_name}' is not installed on the device")
    
    # Update app notification setting in database
    current_time = datetime.now(timezone.utc).isoformat()
    
    # Update the specific app's notification setting in the database using the correct key
    update_app_notification(app_key, notifications_enum.value, current_time)

    result = f"Successfully set {app_key} notifications to {notifications_enum.value}"
    
    # Generate response
    card_id = generate_card_id()
    action_card_content = create_action_card(
        ActionType.SET_APP_NOTIFICATION_STATUS,
        app_name=app_key,
        notifications=notifications_enum.value,
        message=result
    )
    
    response = {
        "result": result,
        "action_card_content_passthrough": action_card_content,
        "card_id": card_id
    }
    
    return response
