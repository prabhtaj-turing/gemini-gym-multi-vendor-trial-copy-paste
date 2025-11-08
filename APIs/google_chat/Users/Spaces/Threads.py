from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
# APIs/google_chat/Users/Spaces/Threads.py

import sys
import os
from pydantic import ValidationError
from google_chat.SimulationEngine.models import GetThreadReadStateInput
from google_chat.SimulationEngine.custom_errors import InvalidSpaceNameFormatError, ThreadReadStateNotFoundError

from typing import Dict, Any

sys.path.append("APIs")

from google_chat.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_thread_read_state_for_user',
        'description': 'Retrieves the read state of a user within a thread.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. Resource name of the thread read state to retrieve.
                    Only supports getting read state for the calling user.
                    To refer to the calling user, set one of the following:
                    - The `me` alias. For example: users/me/spaces/{space}/threads/{thread}/threadReadState
                    - Their Workspace email address. For example: users/user@example.com/spaces/{space}/threads/{thread}/threadReadState
                    - Their user ID. For example: users/123456789/spaces/{space}/threads/{thread}/threadReadState
                    Format: users/{user}/spaces/{space}/threads/{thread}/threadReadState """
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def getThreadReadState(name: str) -> Dict[str, Any]:
    """
    Retrieves the read state of a user within a thread.

    Args:
        name (str): Required. Resource name of the thread read state to retrieve.
            Only supports getting read state for the calling user.
            To refer to the calling user, set one of the following:
            - The `me` alias. For example: users/me/spaces/{space}/threads/{thread}/threadReadState
            - Their Workspace email address. For example: users/user@example.com/spaces/{space}/threads/{thread}/threadReadState
            - Their user ID. For example: users/123456789/spaces/{space}/threads/{thread}/threadReadState
            Format: users/{user}/spaces/{space}/threads/{thread}/threadReadState

    Returns:
        Dict[str, Any]: A dictionary representing the user's thread read state with the following structure:
            - 'name' (str): Resource name of the thread read state in format 'users/{user}/spaces/{space}/threads/{thread}/threadReadState'.
            - 'lastReadTime' (str): RFC-3339 timestamp indicating when the user's thread read state was last updated.

        Raises ThreadReadStateNotFoundError if no matching read state is found (does not return empty dictionary).

    Raises:
        TypeError: If 'name' is not a string.
        ValueError: If 'name' is empty or invalid format.
        ValidationError: If the input validation fails.
        ThreadReadStateNotFoundError: If no matching thread read state is found.
    """
    # Input validation
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name.strip():
        raise ValueError("Argument 'name' cannot be empty.")
    
    try:
        GetThreadReadStateInput(name=name)
    except ValidationError as e:
        raise ValueError(f"Invalid 'name' parameter: {e}") from e

    print_log(f"getThreadReadState called with name={name}")
    for state in DB["ThreadReadState"]:
        if state.get("name") == name:
            return state
    
    print_log("ThreadReadState not found.")
    raise ThreadReadStateNotFoundError(f"Thread read state '{name}' not found.")
