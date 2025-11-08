from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/__init__.py
# Use relative imports
from pydantic import ValidationError
from ..SimulationEngine.models import ProfileInputModel
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import _ensure_user, get_history_id
from typing import Dict, Any, Optional


@tool_spec(
    spec={
        'name': 'get_user_profile',
        'description': """ Gets the user's Gmail profile information.
        
        Retrieves the profile data associated with the specified user ID from the database. """,
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
def getProfile(userId: str = "me") -> Dict[str, Any]:
    """Gets the user's Gmail profile information.

    Retrieves the profile data associated with the specified user ID from the database.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: A dictionary containing the user's profile information with keys such as:
            - 'emailAddress' (str): The user's email address
            - 'messagesTotal' (int): Total number of messages in the mailbox
            - 'threadsTotal' (int): Total number of threads in the mailbox
            - 'historyId' (str): The current history ID of the mailbox

    Raises:
        TypeError: If `userId` is not a string.
        ValueError: If `userId` is an empty string or does not exist in the database (propagated from database access).
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")
    
    if userId.strip() == "":
        raise ValueError("userId cannot be an empty string.")
    # --- End Input Validation ---

    _ensure_user(userId)
    return DB["users"][userId]["profile"]


@tool_spec(
    spec={
        'name': 'watch_user_mailbox',
        'description': """ Set up or update a watch on the user's mailbox.
        
        Stores the watch request configuration for the specified user. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'request': {
                    'type': 'object',
                    'description': """ An optional dictionary containing the watch request body with keys:
                    Example: {"topicName": "projects/myproject/topics/mytopic", "labelIds": ["INBOX"]} """,
                    'properties': {
                        'topicName': {
                            'type': 'string',
                            'description': 'The Google Cloud Pub/Sub topic name where notifications are published.'
                        },
                        'labelIds': {
                            'type': 'array',
                            'description': 'A list of label IDs to filter notifications.',
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': [
                        'topicName'
                    ]
                }
            },
            'required': []
        }
    }
)
def watch(
    userId: str = "me", request: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Set up or update a watch on the user's mailbox.

    Stores the watch request configuration for the specified user.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        request (Optional[Dict[str, Any]]): An optional dictionary containing the watch request body with keys:
            - topicName (str): The Google Cloud Pub/Sub topic name where notifications are published.
            - labelIds (List[str], optional): A list of label IDs to filter notifications.
            Example: {"topicName": "projects/myproject/topics/mytopic", "labelIds": ["INBOX"]}

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'historyId' (str): The current history ID of the mailbox
            - 'expiration' (str): The expiration timestamp for the watch

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    request = request or {}
    DB["users"][userId]["watch"] = request
    return {
        "historyId": get_history_id(userId),
        "expiration": "9999999999999",
    }


@tool_spec(
    spec={
        'name': 'stop_mailbox_watch',
        'description': """ Stop receiving push notifications for the user's mailbox.
        
        Clears the stored watch configuration for the specified user. """,
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
def stop(userId: str = "me") -> Dict[str, Any]:
    """Stop receiving push notifications for the user's mailbox.

    Clears the stored watch configuration for the specified user.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: An empty dictionary, signifying the successful stop operation.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    DB["users"][userId]["watch"] = {}
    return {}


@tool_spec(
    spec={
        'name': 'check_user_exists',
        'description': 'Checks if a user exists in the database.',
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': 'The ID of the user to check.'
                }
            },
            'required': [
                'userId'
            ]
        }
    }
)
def exists(userId: str) -> bool:
    """Checks if a user exists in the database.

    Args:
        userId (str): The ID of the user to check.

    Returns:
        bool: True if the user exists in the database, False otherwise.

    Raises:
        TypeError: If userId is not a string.
        ValueError: If userId is empty or contains only whitespace.
    """
    # Type validation
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")

    # Value validation
    if not userId or not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")

    # Check existence in database
    return userId in DB["users"]


@tool_spec(
    spec={
        'name': 'create_user',
        'description': """ Creates a new user entry in the database.
        
        Initializes the data structure for a new user, including profile,
        empty containers for drafts, messages, threads, labels, settings, history,
        and watch configuration. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': 'The unique identifier for the new user.'
                },
                'profile': {
                    'type': 'object',
                    'description': """ A dictionary containing the initial profile information with keys:
                    Example: {"emailAddress": "user@example.com", "displayName": "John Doe"} """,
                    'properties': {
                        'emailAddress': {
                            'type': 'string',
                            'description': "The user's primary email address. Required."
                        }
                    },
                    'required': [
                        'emailAddress'
                    ]
                }
            },
            'required': [
                'userId',
                'profile'
            ]
        }
    }
)
def createUser(userId: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new user entry in the database.

    Initializes the data structure for a new user, including profile,
    empty containers for drafts, messages, threads, labels, settings, history,
    and watch configuration.

    Args:
        userId (str): The unique identifier for the new user.
        profile (Dict[str, Any]): A dictionary containing the initial profile information with keys:
            - emailAddress (str): The user's primary email address. Required.
            Example: {"emailAddress": "user@example.com", "displayName": "John Doe"}

    Returns:
        Dict[str, Any]: A dictionary representing the newly created user's data structure with keys:
            - 'profile' (Dict[str, Any]): User profile information
            - 'drafts' (Dict[str, Any]): Empty drafts container
            - 'messages' (Dict[str, Any]): Empty messages container
            - 'threads' (Dict[str, Any]): Empty threads container
            - 'labels' (Dict[str, Any]): Empty labels container
            - 'settings' (Dict[str, Any]): User settings with sub-keys:
                - 'imap' (Dict[str, Any]): IMAP settings
                - 'pop' (Dict[str, Any]): POP settings
                - 'vacation' (Dict[str, Any]): Vacation responder settings
                - 'language' (Dict[str, Any]): Language settings
                - 'autoForwarding' (Dict[str, Any]): Auto-forwarding settings
                - 'sendAs' (Dict[str, Any]): Send-as settings
            - 'history' (List[Any]): Empty history list
            - 'watch' (Dict[str, Any]): Empty watch configuration

    Raises:
        TypeError: If `userId` is not a string or `profile` is not a dict.
        ValidationError: If the `profile` dictionary is invalid (e.g., missing 'emailAddress',
                         or 'emailAddress' is not a valid string email).
    """
    # --- Input Validation ---
    # Validate non-dictionary arguments
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, got {type(userId).__name__}")
    
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dict")
    
    # Validate dictionary arguments using Pydantic
    try:
        validated_profile = ProfileInputModel(**profile)
    except ValidationError as e:
        # Re-raise Pydantic's ValidationError.
        # The error messages from Pydantic are usually descriptive.
        # Example: if 'emailAddress' is missing, it will indicate that.
        # If 'emailAddress' is not a string, it will indicate that.
        raise e
    # --- End of Input Validation ---

    # --- Original Core Functionality ---
    # The global DB variable is assumed to be defined elsewhere in the application.
    # The 'profile' dictionary in the DB will only store 'emailAddress' from the input 'profile',
    # along with other hardcoded default values.
    DB["users"][userId] = {
        "profile": {
            "emailAddress": validated_profile.emailAddress, # Use the validated email address
            "messagesTotal": 0,
            "threadsTotal": 0,
            "historyId": "1",
        },
        "drafts": {},
        "messages": {},
        "threads": {},
        "labels": {},
        "settings": {
            "imap": {},
            "pop": {},
            "vacation": {"enableAutoReply": False},
            "language": {"displayLanguage": "en"},
            "autoForwarding": {"enabled": False},
            "sendAs": {},
        },
        "history": [],
        "watch": {},
    }

    return DB["users"][userId]
