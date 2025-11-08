from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
# APIs/google_chat/Users/Spaces/__init__.py

import sys
import os
from typing import Dict, Any
sys.path.append("APIs")

from google_chat.SimulationEngine.db import DB
from pydantic import ValidationError
from google_chat.SimulationEngine.models import UpdateSpaceReadStateInput, GetSpaceReadStateInput
from google_chat.SimulationEngine.custom_errors import SpaceReadStateNotFoundError


@tool_spec(
    spec={
        'name': 'get_space_read_state_for_user',
        'description': 'Retrieves the read state of a user within a space.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. Resource name of the space read state to retrieve.
                    Only supports getting read state for the calling user.
                    To refer to the calling user, set one of the following:
                    - The `me` alias. For example, `users/me/spaces/{space}/spaceReadState`.
                    - Their Workspace email address. For example, `users/user@example.com/spaces/{space}/spaceReadState`.
                    - Their user ID. For example, `users/123456789/spaces/{space}/spaceReadState`.
                    Format: users/{user}/spaces/{space}/spaceReadState """
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def getSpaceReadState(name: str) -> Dict[str, Any]:
    """
    Retrieves the read state of a user within a space.

    Args:
        name (str): Required. Resource name of the space read state to retrieve.
            Only supports getting read state for the calling user.
            To refer to the calling user, set one of the following:
            - The `me` alias. For example, `users/me/spaces/{space}/spaceReadState`.
            - Their Workspace email address. For example, `users/user@example.com/spaces/{space}/spaceReadState`.
            - Their user ID. For example, `users/123456789/spaces/{space}/spaceReadState`.
            Format: users/{user}/spaces/{space}/spaceReadState

    Returns:
        Dict[str, Any]: Dictionary representing the user's space read state with the following keys:
            - 'name' (str): Resource name of the space read state.
            - 'lastReadTime' (str, optional): The time when the user's space read state was updated.

    Raises:
        TypeError: If 'name' is not a string.
        ValueError: If 'name' is empty or invalid format.
        ValidationError: If the input validation fails.
        SpaceReadStateNotFoundError: If no matching space read state is found.
    """
    # Input validation
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name.strip():
        raise ValueError("Argument 'name' cannot be empty.")
    
    try:
        GetSpaceReadStateInput(name=name)
    except ValidationError as e:
        raise ValueError(f"Invalid 'name' parameter: {e}") from e

    print_log(f"getSpaceReadState called with name={name}")
    for state in DB["SpaceReadState"]:
        if state.get("name") == name:
            return state
    
    print_log("SpaceReadState not found.")
    raise SpaceReadStateNotFoundError(f"Space read state '{name}' not found.")


@tool_spec(
    spec={
        'name': 'update_space_read_state_for_user',
        'description': "Updates a user's space read state.",
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Resource name of the space read state to update.
                    Format: users/{user}/spaces/{space}/spaceReadState """
                },
                'updateMask': {
                    'type': 'string',
                    'description': 'Comma-separated list of fields to update.\nCurrently only \"last_read_time\" is supported.'
                },
                'requestBody': {
                    'type': 'object',
                    'description': 'A dictionary representing the SpaceReadState resource with the following key:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': """ Resource name of the space read state.
                                 Format: users/{user}/spaces/{space}/spaceReadState """
                        },
                        'last_read_time': {
                            'type': 'string',
                            'description': "The time when the user's space read state was updated.\nThis corresponds with either the timestamp of the last read message, or a user-specified timestamp."
                        }
                    },
                    'required': [
                        'name'
                    ]
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
def updateSpaceReadState(name: str, updateMask: str, requestBody: Dict[str, str]) -> Dict[str, str]:
    """
    Updates a user's space read state.

    Args:
        name (str): Resource name of the space read state to update.
            Format: users/{user}/spaces/{space}/spaceReadState
        updateMask (str): Comma-separated list of fields to update.
            Currently only "last_read_time" is supported.
        requestBody (Dict[str, str]): A dictionary representing the SpaceReadState resource with the following key:
            - 'name' (str): Resource name of the space read state.
                Format: users/{user}/spaces/{space}/spaceReadState
            - 'last_read_time' (Optional[str]): The time when the user's space read state was updated.
                This corresponds with either the timestamp of the last read message, or a user-specified timestamp.

    Returns:
        Dict[str, str]: A dictionary representing the updated SpaceReadState resource with the following keys:
            - 'name' (str): Resource name of the space read state.
                Format: users/{user}/spaces/{space}/spaceReadState
            - 'lastReadTime' (str): Optional. The updated timestamp of the space read state.

    Raises:
        TypeError: If any parameter is not of the expected type.
        ValueError: If any parameter is empty or invalid format.
        ValidationError: If the input validation fails.
        SpaceReadStateNotFoundError: If no matching space read state is found.
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

    print_log(
        f"updateSpaceReadState called with name={name}, updateMask={updateMask}, requestBody={requestBody}"
    )

    try:
        UpdateSpaceReadStateInput(name=name, updateMask=updateMask, requestBody=requestBody)
    except ValidationError as e:
        raise ValueError(f"Invalid parameters: {e}") from e
    
    # Find the state resource
    state_obj = None
    for state in DB["SpaceReadState"]:
        if state.get("name") == name:
            state_obj = state
            break

    if not state_obj:
        print_log("SpaceReadState not found.")
        raise SpaceReadStateNotFoundError(f"Space read state '{name}' not found.")

    # Parse updateMask; only "lastReadTime" is supported.
    masks = [m.strip() for m in updateMask.split(",")]
    if "lastReadTime" in masks or "*" in masks:
        if "lastReadTime" in requestBody:
            # The new value is coerced to be later than the latest message's create time (not enforced here).
            state_obj["lastReadTime"] = requestBody["lastReadTime"]
        else:
            print_log("lastReadTime not provided in requestBody.")
    else:
        print_log("No supported field in updateMask.")

    return state_obj