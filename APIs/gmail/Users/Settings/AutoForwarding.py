from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/Settings/AutoForwarding.py
from typing import Dict, Any, Optional
from pydantic import ValidationError

# Use relative imports (go up THREE levels)
from ...SimulationEngine.db import DB
from ...SimulationEngine.utils import _ensure_user
from ...SimulationEngine.models import AutoForwardingSettingsModel


@tool_spec(
    spec={
        'name': 'get_auto_forwarding_settings',
        'description': """ Gets the auto-forwarding setting for the specified user.
        
        Retrieves the current auto-forwarding configuration associated with the
        user's account from the database. """,
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
def getAutoForwarding(userId: str = "me") -> Dict[str, Any]:
    """Gets the auto-forwarding setting for the specified user.

    Retrieves the current auto-forwarding configuration associated with the
    user's account from the database.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: A dictionary containing the user's auto-forwarding settings with keys:
            - 'enabled' (bool): Whether auto-forwarding is enabled.
            - 'emailAddress' (str): The email address to forward messages to.
            - 'disposition' (str): How to handle forwarded messages (e.g., 'leaveInInbox').

    Raises:
        TypeError: If `userId` is not a string.
        ValueError: If `userId` is empty, contains only whitespace, or the user does not exist.
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    
    if not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    # --- End of Input Validation ---

    _ensure_user(userId)
    return DB["users"][userId]["settings"]["autoForwarding"]


@tool_spec(
    spec={
        'name': 'update_auto_forwarding_settings',
        'description': """ Updates the auto-forwarding setting for the specified user.
        
        Modifies the auto-forwarding configuration for the user's account based
        on the provided `auto_forwarding_settings`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'auto_forwarding_settings': {
                    'type': 'object',
                    'description': """ An optional dictionary containing
                    the settings to update. All fields are optional; only provided
                    keys will be updated. It may include:
                    Defaults to None, resulting in no changes. """,
                    'properties': {
                        'enabled': {
                            'type': 'boolean',
                            'description': 'Whether to enable auto-forwarding.'
                        },
                        'emailAddress': {
                            'type': 'string',
                            'description': 'Valid email address to forward messages to.'
                        },
                        'disposition': {
                            'type': 'string',
                            'description': """ How to handle forwarded messages.
                               Valid values: 'dispositionUnspecified', 'leaveInInbox', 'archive', 'trash', 'markRead'. """
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def updateAutoForwarding(
    userId: str = "me", auto_forwarding_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Updates the auto-forwarding setting for the specified user.

    Modifies the auto-forwarding configuration for the user's account based
    on the provided `auto_forwarding_settings`.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        auto_forwarding_settings (Optional[Dict[str, Any]]): An optional dictionary containing
                                  the settings to update. All fields are optional; only provided
                                  keys will be updated. It may include:
                                  - 'enabled' (Optional[bool]): Whether to enable auto-forwarding.
                                  - 'emailAddress' (Optional[str]): Valid email address to forward messages to.
                                  - 'disposition' (Optional[str]): How to handle forwarded messages.
                                    Valid values: 'dispositionUnspecified', 'leaveInInbox', 'archive', 'trash', 'markRead'.
                                  Defaults to None, resulting in no changes.

    Returns:
        Dict[str, Any]: A dictionary containing the complete, updated auto-forwarding settings
        for the user with keys:
            - 'enabled' (bool): Whether auto-forwarding is enabled.
            - 'emailAddress' (str): The email address to forward messages to.
            - 'disposition' (str): How to handle forwarded messages.

    Raises:
        TypeError: If `userId` is not a string or `auto_forwarding_settings` is not a 
                  dictionary or None.
        ValueError: If `userId` is empty, contains only whitespace, or the user does not exist.
        ValidationError: If `auto_forwarding_settings` contains invalid field values or types,
                        such as invalid email format for 'emailAddress' or invalid 'disposition' value.
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    
    if not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    
    if auto_forwarding_settings is not None and not isinstance(auto_forwarding_settings, dict):
        raise TypeError(f"auto_forwarding_settings must be a dictionary or None, but got {type(auto_forwarding_settings).__name__}.")
    
    # --- Pydantic validation for auto_forwarding_settings ---
    if auto_forwarding_settings is not None:
        validated_settings = AutoForwardingSettingsModel(**auto_forwarding_settings)
        # Convert back to dict for database storage, preserving original behavior
        auto_forwarding_settings = validated_settings.model_dump(exclude_none=True)
    # --- End of Input Validation ---

    _ensure_user(userId)
    auto_forwarding_settings = auto_forwarding_settings or {}
    DB["users"][userId]["settings"]["autoForwarding"].update(auto_forwarding_settings)
    return DB["users"][userId]["settings"]["autoForwarding"]
