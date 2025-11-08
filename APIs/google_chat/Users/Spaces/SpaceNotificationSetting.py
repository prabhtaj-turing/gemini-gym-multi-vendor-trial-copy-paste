from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
# APIs/google_chat/Users/Spaces/SpaceNotificationSetting.py

import sys
import os
import re
from typing import Dict, Any, Union

sys.path.append("APIs")

from google_chat.SimulationEngine.db import DB
from google_chat.SimulationEngine.models import SpaceNotificationSettingPatchModel
from google_chat.SimulationEngine.custom_errors import SpaceNotificationSettingNotFoundError
from pydantic import ValidationError


@tool_spec(
    spec={
        'name': 'get_space_notification_settings_for_user',
        'description': 'Retrieves the space notification setting for a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. Resource name of the space notification setting to retrieve.
                    Only supports the calling user's identifier.
                    Format:
                    - users/me/spaces/{space}/spaceNotificationSetting
                    - users/user@example.com/spaces/{space}/spaceNotificationSetting
                    - users/123456789/spaces/{space}/spaceNotificationSetting """
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def get(name: str) -> Dict[str, Any]:
    """
    Retrieves the space notification setting for a user.

    Args:
        name (str): Required. Resource name of the space notification setting to retrieve.
            Only supports the calling user's identifier.
            Format:
            - users/me/spaces/{space}/spaceNotificationSetting
            - users/user@example.com/spaces/{space}/spaceNotificationSetting
            - users/123456789/spaces/{space}/spaceNotificationSetting

    Returns:
        Dict[str, Any]: A dictionary containing the space notification setting with the following keys:
            - 'name' (str): Resource name of the space notification setting.
            - 'notificationSetting' (str): The notification level. One of:
                - 'NOTIFICATION_SETTING_UNSPECIFIED'
                - 'ALL'
                - 'MAIN_CONVERSATIONS'
                - 'FOR_YOU'
                - 'OFF'
            - 'muteSetting' (str): The mute configuration. One of:
                - 'MUTE_SETTING_UNSPECIFIED'
                - 'UNMUTED'
                - 'MUTED'

    Raises:
        TypeError: If 'name' is not a string.
        ValueError: If 'name' is empty or invalid format.
        SpaceNotificationSettingNotFoundError: If no matching space notification setting is found.
    """
    # Input validation
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name.strip():
        raise ValueError("Argument 'name' cannot be empty.")
    
    # Validate the input name format using regex
    pattern = r"^users/[^/]+/spaces/[^/]+/spaceNotificationSetting$"
    if not re.match(pattern, name):
        raise ValueError(f"Invalid name format: '{name}'. Expected format: 'users/{{user}}/spaces/{{space}}/spaceNotificationSetting'.")

    print_log(f"SpaceNotificationSetting.get called with name={name}")
    for setting in DB["SpaceNotificationSetting"]:
        if setting.get("name") == name:
            return setting
    print_log("SpaceNotificationSetting not found.")

    raise SpaceNotificationSettingNotFoundError(f"Space notification setting '{name}' not found.")


@tool_spec(
    spec={
        'name': 'update_space_notification_settings_for_user',
        'description': 'Updates the space notification setting for a user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Resource name of the space notification setting to update. Format: users/{user}/spaces/{space}/spaceNotificationSetting'
                },
                'updateMask': {
                    'type': 'string',
                    'description': 'Comma-separated list of fields to update. Supported fields: "notification_setting", "mute_setting"'
                },
                'requestBody': {
                    'type': 'object',
                    'description': """ A dictionary representing the SpaceNotificationSetting resource. Only the fields specified in updateMask will be updated.
                    All fields are optional - provide only the fields you want to update:
                    Note: The function will only update fields that are both specified in updateMask and present in requestBody. """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Resource name of the space notification setting.'
                        },
                        'notification_setting': {
                            'type': 'string',
                            'description': 'New notification level. One of "NOTIFICATION_SETTING_UNSPECIFIED", "ALL", "MAIN_CONVERSATIONS", "FOR_YOU", "OFF".'
                        },
                        'mute_setting': {
                            'type': 'string',
                            'description': 'New mute setting. One of "MUTE_SETTING_UNSPECIFIED", "UNMUTED", "MUTED".'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'name',
                'updateMask',
                'requestBody'
            ]
        }
    }
)
def patch(name: str, updateMask: str, requestBody: Dict[str, str]) -> Dict[str, str]:
    """
    Updates the space notification setting for a user.

    Args:
        name (str): Resource name of the space notification setting to update. Format: users/{user}/spaces/{space}/spaceNotificationSetting
        updateMask (str): Comma-separated list of fields to update. Supported fields: "notification_setting", "mute_setting"
        requestBody (Dict[str, str]): A dictionary representing the SpaceNotificationSetting resource. Only the fields specified in updateMask will be updated.
            All fields are optional - provide only the fields you want to update:
            - 'name' (Optional[str]): Resource name of the space notification setting.
            - 'notification_setting' (Optional[str]): New notification level. 
              One of "NOTIFICATION_SETTING_UNSPECIFIED", "ALL", "MAIN_CONVERSATIONS", "FOR_YOU", "OFF".
            - 'mute_setting' (Optional[str]): New mute setting. 
              One of "MUTE_SETTING_UNSPECIFIED", "UNMUTED", "MUTED".
            
            Note: The function will only update fields that are both specified in updateMask and present in requestBody.

    Returns:
        Dict[str, str]: A dictionary representing the updated space notification setting with the following keys:
            - 'name' (str): Resource name of the space notification setting.
            - 'notification_setting' (str): The updated notification level.
            - 'mute_setting' (str): The updated mute setting.
    
    Raises:
        TypeError: If any parameter is not of the expected type.
        ValueError: If any parameter is empty or invalid format.
        ValidationError: If the input validation fails.
        SpaceNotificationSettingNotFoundError: If no matching space notification setting is found.
    """
    # Input validation
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name.strip():
        raise ValueError("Argument 'name' cannot be empty.")
    
    if not isinstance(updateMask, str):
        raise TypeError("Argument 'updateMask' must be a string.")
    
    if not updateMask.strip():
        raise ValueError("Argument 'updateMask' cannot be empty.")
    
    if not isinstance(requestBody, dict):
        raise TypeError("Argument 'requestBody' must be a dictionary.")

    # Validate the input name format using regex
    pattern = r"^users/[^/]+/spaces/[^/]+/spaceNotificationSetting$"
    if not re.match(pattern, name):
        raise ValueError(f"Invalid name format: '{name}'. Expected format: 'users/{{user}}/spaces/{{space}}/spaceNotificationSetting'.")

    try:
        SpaceNotificationSettingPatchModel(
            name=name,
            updateMask=updateMask,
            requestBody=requestBody
        )
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}") from e

    print_log(
        f"SpaceNotificationSetting.patch called with name={name}, updateMask={updateMask}, requestBody={requestBody}"
    )
    target = None
    for setting in DB["SpaceNotificationSetting"]:
        if setting.get("name") == name:
            target = setting
            break
    if not target:
        print_log("SpaceNotificationSetting not found.")
        raise SpaceNotificationSettingNotFoundError(f"Space notification setting '{name}' not found.")

    masks = [m.strip() for m in updateMask.split(",")]
    if "notification_setting" in masks or "*" in masks:
        if "notification_setting" in requestBody:
            target["notification_setting"] = requestBody["notification_setting"]
    if "mute_setting" in masks or "*" in masks:
        if "mute_setting" in requestBody:
            target["mute_setting"] = requestBody["mute_setting"]

    return target