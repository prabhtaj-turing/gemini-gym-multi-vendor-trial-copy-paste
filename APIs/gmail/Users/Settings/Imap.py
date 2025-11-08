from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/Settings/Imap.py
from typing import Dict, Any, Optional
from ...SimulationEngine.db import DB
from ...SimulationEngine.utils import _ensure_user
from ...SimulationEngine.models import ImapSettingsInputModel
from pydantic import ValidationError


@tool_spec(
    spec={
        'name': 'get_imap_settings',
        'description': """ Gets the IMAP settings for the specified user.
        
        Retrieves the current IMAP configuration associated with the user's account
        from the database. """,
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
def getImap(userId: str = "me") -> Dict[str, Any]:
    """Gets the IMAP settings for the specified user.

    Retrieves the current IMAP configuration associated with the user's account
    from the database.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: A dictionary containing the user's IMAP settings with keys:
            - 'enabled' (bool): Whether IMAP access is enabled for the account.
            - 'autoExpunge' (bool): If this value is true, Gmail will immediately expunge 
              a message when it is marked as deleted in IMAP. Otherwise, Gmail will wait 
              for an update from the client before expunging messages marked as deleted.
            - 'expungeBehavior' (str): The action that will be executed on a message when 
              it is marked as deleted and expunged from the last visible IMAP folder. 
              Valid values: 'archive', 'trash', 'deleteForever'.

    Raises:
        TypeError: If `userId` is not a string.
        ValueError: If `userId` is an empty string or contains only whitespace, 
                   or if the specified `userId` does not exist in the database.
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")
    
    if not userId or not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    # --- End Input Validation ---

    _ensure_user(userId)
    return DB["users"][userId]["settings"]["imap"]


@tool_spec(
    spec={
        'name': 'update_imap_settings',
        'description': """ Updates the IMAP settings for the specified user.
        
        Modifies the IMAP configuration for the user's account based on the provided
        `imap_settings`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'imap_settings': {
                    'type': 'object',
                    'description': """ An optional dictionary containing the IMAP settings to update.
                    All subfields are optional; only provided keys will be updated.
                    Defaults to None, resulting in no changes. """,
                    'properties': {
                        'enabled': {
                            'type': 'boolean',
                            'description': 'Whether to enable IMAP access.'
                        },
                        'autoExpunge': {
                            'type': 'boolean',
                            'description': 'Whether to automatically expunge messages.'
                        },
                        'expungeBehavior': {
                            'type': 'string',
                            'description': 'How to handle expunged messages.'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def updateImap(
    userId: str = "me", imap_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Updates the IMAP settings for the specified user.

    Modifies the IMAP configuration for the user's account based on the provided
    `imap_settings`.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        imap_settings (Optional[Dict[str, Any]]): An optional dictionary containing the IMAP settings to update.
                      All subfields are optional; only provided keys will be updated.
                      - 'enabled' (Optional[bool]): Whether to enable IMAP access.
                      - 'autoExpunge' (Optional[bool]): Whether to automatically expunge messages.
                      - 'expungeBehavior' (Optional[str]): How to handle expunged messages.
                      Defaults to None, resulting in no changes.

    Returns:
        Dict[str, Any]: A dictionary containing the complete, updated IMAP settings for the user with keys:
            - 'enabled' (bool): Whether IMAP access is enabled.
            - 'autoExpunge' (bool): Whether to automatically expunge messages.
            - 'expungeBehavior' (str): How to handle expunged messages.

    Raises:
        TypeError: If userId is not a string or imap_settings is not a dictionary.
        ValueError: If userId is empty or contains only whitespace, or if the specified 
                   userId does not exist in the database.
        ValidationError: If imap_settings contains invalid field types or values.
    """
    # Validate userId
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")
    
    if not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    
    # Validate imap_settings
    if imap_settings is not None and not isinstance(imap_settings, dict):
        raise TypeError("imap_settings must be a dictionary.")
    
    _ensure_user(userId)
    
    # Validate imap_settings structure and types using Pydantic
    if imap_settings is not None:
        try:
            validated_settings = ImapSettingsInputModel(**imap_settings)
            # Convert back to dict, excluding None values to maintain original behavior
            imap_settings = {k: v for k, v in validated_settings.model_dump().items() if v is not None}
        except ValidationError as e:
            raise ValidationError(str(e))
    else:
        imap_settings = {}
    
    DB["users"][userId]["settings"]["imap"].update(imap_settings)
    return DB["users"][userId]["settings"]["imap"]
