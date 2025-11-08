from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/Settings/Pop.py
from typing import Dict, Any, Optional
from ...SimulationEngine.db import DB
from ...SimulationEngine.utils import _ensure_user


@tool_spec(
    spec={
        'name': 'get_pop_settings',
        'description': """ Gets the POP settings for the specified user.
        
        Retrieves the current POP (Post Office Protocol) configuration associated
        with the user's account from the database. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                }
            },
            'required': []
        }
    }
)
def getPop(userId: str = "me") -> Dict[str, Any]:
    """Gets the POP settings for the specified user.

    Retrieves the current POP (Post Office Protocol) configuration associated
    with the user's account from the database.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: A dictionary containing the user's POP settings with keys:
            - 'accessWindow' (str): The time window for POP access (e.g., 'allMail').
            - 'disposition' (str): How to handle messages after POP access (e.g., 'leaveInInbox').
            - Other POP settings as defined in the database.

    Raises:
        KeyError: If the specified `userId` or their settings structure does not
                  exist in the database.
    """
    _ensure_user(userId)
    return DB["users"][userId]["settings"]["pop"]


@tool_spec(
    spec={
        'name': 'update_pop_settings',
        'description': """ Updates the POP settings for the specified user.
        
        Modifies the POP configuration for the user's account based on the provided
        `pop_settings`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'pop_settings': {
                    'type': 'object',
                    'description': """ An optional dictionary containing the POP settings to update.
                    All subfields are optional; only provided keys will be updated.
                    Defaults to None, resulting in no changes. """,
                    'properties': {
                        'accessWindow': {
                            'type': 'string',
                            'description': """ The range of messages accessible via POP.
                                                   Valid values: 'accessWindowUnspecified', 'disabled', 'fromNowOn', 'allMail' """
                        },
                        'disposition': {
                            'type': 'string',
                            'description': """ How to handle messages after POP access.
                                                  Valid values: 'dispositionUnspecified', 'leaveInInbox', 'archive', 'trash', 'markRead' """
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def updatePop(
    userId: str = "me", pop_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Updates the POP settings for the specified user.

    Modifies the POP configuration for the user's account based on the provided
    `pop_settings`.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        pop_settings (Optional[Dict[str, Any]]): An optional dictionary containing the POP settings to update.
                      All subfields are optional; only provided keys will be updated.
                      - 'accessWindow' (Optional[str]): The range of messages accessible via POP.
                                            Valid values: 'accessWindowUnspecified', 'disabled', 'fromNowOn', 'allMail'
                      - 'disposition' (Optional[str]): How to handle messages after POP access.
                                           Valid values: 'dispositionUnspecified', 'leaveInInbox', 'archive', 'trash', 'markRead'
                      Defaults to None, resulting in no changes.

    Returns:
        Dict[str, Any]: A dictionary containing the complete, updated POP settings for the user with keys:
            - 'accessWindow' (str): The range of messages accessible via POP.
                                  Valid values: 'accessWindowUnspecified', 'disabled', 'fromNowOn', 'allMail'
            - 'disposition' (str): How to handle messages after POP access.
                                 Valid values: 'dispositionUnspecified', 'leaveInInbox', 'archive', 'trash', 'markRead'

    Raises:
        TypeError: If `userId` is not a string or `pop_settings` is not a dictionary or None.
        ValueError: If `userId` is empty, contains only whitespace, or the user does not exist
                   (raised by _ensure_user function).
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    
    if not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    
    if pop_settings is not None and not isinstance(pop_settings, dict):
        raise TypeError(f"pop_settings must be a dictionary or None, but got {type(pop_settings).__name__}.")
    # --- End of Input Validation ---

    _ensure_user(userId)
    pop_settings = pop_settings or {}
    DB["users"][userId]["settings"]["pop"].update(pop_settings)
    return DB["users"][userId]["settings"]["pop"]