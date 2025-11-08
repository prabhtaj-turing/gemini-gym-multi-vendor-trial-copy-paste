from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/Settings/Language.py
from typing import Dict, Any, Optional
from ...SimulationEngine.db import DB
from ...SimulationEngine.utils import _ensure_user


@tool_spec(
    spec={
        'name': 'get_language_settings',
        'description': """ Gets the language settings for the specified user.
        
        Retrieves the current language configuration (e.g., display language)
        associated with the user's account from the database. """,
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
def getLanguage(userId: str = "me") -> Dict[str, Any]:
    """Gets the language settings for the specified user.

    Retrieves the current language configuration (e.g., display language)
    associated with the user's account from the database.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: A dictionary containing the user's language settings with keys:
            - 'displayLanguage' (str): The language code for display (e.g., 'en-US' for English).

    Raises:
        TypeError: If `userId` is not a string.
        ValueError: If `userId` is empty, contains only whitespace, or the user does not exist
                   (raised by _ensure_user function).
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    
    if not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    # --- End of Input Validation ---

    _ensure_user(userId)
    return DB["users"][userId]["settings"]["language"]


@tool_spec(
    spec={
        'name': 'update_language_settings',
        'description': """ Updates the language settings for the specified user.
        
        Modifies the language configuration for the user's account based on the
        provided `language_settings`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'language_settings': {
                    'type': 'object',
                    'description': """ An optional dictionary containing the language settings
                    to update. All subfields are optional; only provided keys will be updated.
                    Defaults to None, resulting in no changes. """,
                    'properties': {
                        'displayLanguage': {
                            'type': 'string',
                            'description': "The language code for display (e.g., 'en-US' for English)."
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def updateLanguage(
    userId: str = "me", language_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Updates the language settings for the specified user.

    Modifies the language configuration for the user's account based on the
    provided `language_settings`.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        language_settings (Optional[Dict[str, Any]]): An optional dictionary containing the language settings
                           to update. All subfields are optional; only provided keys will be updated.
                           - 'displayLanguage' (Optional[str]): The language code for display (e.g., 'en-US' for English).
                           Defaults to None, resulting in no changes.

    Returns:
        Dict[str, Any]: A dictionary containing the complete, updated language settings for the user with keys:
            - 'displayLanguage' (str): The language code for display (e.g., 'en-US' for English).

    Raises:
        TypeError: If `userId` is not a string or `language_settings` is not a dictionary or None.
        ValueError: If `userId` is empty, contains only whitespace, or the user does not exist
                   (raised by _ensure_user function).
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    
    if not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    
    if language_settings is not None and not isinstance(language_settings, dict):
        raise TypeError(f"language_settings must be a dictionary or None, but got {type(language_settings).__name__}.")
    # --- End of Input Validation ---

    _ensure_user(userId)
    language_settings = language_settings or {}
    DB["users"][userId]["settings"]["language"].update(language_settings)
    return DB["users"][userId]["settings"]["language"]
