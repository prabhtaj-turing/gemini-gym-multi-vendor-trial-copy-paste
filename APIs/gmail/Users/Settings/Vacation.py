from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/Settings/Vacation.py
from typing import Dict, Any, Optional, Union   
from ...SimulationEngine.db import DB
from ...SimulationEngine.utils import _ensure_user


@tool_spec(
    spec={
        'name': 'get_vacation_settings',
        'description': """ Gets the vacation responder settings for the specified user.
        
        Retrieves the current vacation auto-reply configuration associated with the
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
def getVacation(userId: str = "me") -> Dict[str, Any]:
    """Gets the vacation responder settings for the specified user.

    Retrieves the current vacation auto-reply configuration associated with the
    user's account from the database.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: A dictionary containing the user's vacation responder settings with keys:
            - 'enableAutoReply' (bool): Whether the vacation auto-reply is enabled.
            - 'responseSubject' (str): Subject line of the auto-reply message.
            - 'responseBodyHtml' (str): HTML body of the auto-reply message.
            - 'restrictToContacts' (bool): Whether to only send to contacts.
            - 'restrictToDomain' (bool): Whether to only send within domain.
            - 'startTime' (str): Unix timestamp (ms) when auto-reply starts.
            - 'endTime' (str): Unix timestamp (ms) when auto-reply ends.
            - Other vacation settings as defined in the database.

    Raises:
        KeyError: If the specified `userId` or their settings structure does not
                  exist in the database.
    """
    _ensure_user(userId)
    return DB["users"][userId]["settings"]["vacation"]


@tool_spec(
    spec={
        'name': 'update_vacation_settings',
        'description': """ Updates the vacation responder settings for the specified user.
        
        Modifies the vacation auto-reply configuration for the user's account based
        on the provided `vacation_settings`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': "The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'."
                },
                'vacation_settings': {
                    'type': 'object',
                    'description': """ An optional dictionary containing the vacation settings to update.
                    All subfields are optional; only provided keys will be updated. It may include: """,
                    'properties': {
                        'enableAutoReply': {
                            'type': 'boolean',
                            'description': 'Whether to enable vacation auto-reply.'
                        },
                        'responseSubject': {
                            'type': 'string',
                            'description': 'Subject line of the auto-reply message.'
                        },
                        'responseBodyHtml': {
                            'type': 'string',
                            'description': 'HTML body of the auto-reply message.'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def updateVacation(
    userId: str = "me", vacation_settings: Optional[Dict[str, Union[str, bool, int]]] = None
) -> Dict[str, Any]:
    """Updates the vacation responder settings for the specified user.

    Modifies the vacation auto-reply configuration for the user's account based
    on the provided `vacation_settings`.

    Args:
        userId (str): The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'.
        vacation_settings (Optional[Dict[str, Union[str, bool, int]]]): An optional dictionary containing the vacation settings to update.
            All subfields are optional; only provided keys will be updated. It may include:
            - 'enableAutoReply' (Optional[bool]): Whether to enable vacation auto-reply.
            - 'responseSubject' (Optional[str]): Subject line of the auto-reply message.
            - 'responseBodyHtml' (Optional[str]): HTML body of the auto-reply message.

    Returns:
        Dict[str, Any]: A dictionary containing the complete, updated vacation settings for the user with keys:
            - 'enableAutoReply' (bool): Whether the vacation auto-reply is enabled.
            - 'responseSubject' (str): Subject line of the auto-reply message.
            - 'responseBodyHtml' (str): HTML body of the auto-reply message.
            - 'restrictToContacts' (bool): Whether to only send to contacts.
            - 'restrictToDomain' (bool): Whether to only send within domain.
            - 'startTime' (str): Unix timestamp (ms) when auto-reply starts.
            - 'endTime' (str): Unix timestamp (ms) when auto-reply ends.
            - Other vacation settings as defined in the database.

    Raises:
        KeyError: If the specified `userId` or their settings structure does not
                  exist in the database.
    """
    _ensure_user(userId)
    vacation_settings = vacation_settings or {}
    DB["users"][userId]["settings"]["vacation"].update(vacation_settings)
    return DB["users"][userId]["settings"]["vacation"]
