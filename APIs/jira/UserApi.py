from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/UserApi.py
from pydantic import ValidationError
from .SimulationEngine.custom_errors import MissingUserIdentifierError, UserNotFoundError
from .SimulationEngine.db import DB
from .SimulationEngine.models import UserCreationPayload
from typing import Any, Dict, List, Optional
import warnings
import uuid


@tool_spec(
    spec={
        'name': 'get_user_by_username_or_account_id',
        'description': """ Get a user by username or account_id(key).
        
        This function retrieves a single user from the database. It prioritizes
        the `account_id` if both identifiers are provided. If no user is found
        matching the given criteria, it will raise a `UserNotFoundError`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The username of the user to retrieve.'
                },
                'account_id': {
                    'type': 'string',
                    'description': 'The account ID (key) of the user to retrieve.'
                }
            },
            'required': []
        }
    }
)
def get_user(username: Optional[str] = None, account_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a user by username or account_id(key).

    This function retrieves a single user from the database. It prioritizes
    the `account_id` if both identifiers are provided. If no user is found
    matching the given criteria, it will raise a `UserNotFoundError`.

    Args:
        username (Optional[str]): The username of the user to retrieve.
        account_id (Optional[str]): The account ID (key) of the user to retrieve.

    Returns:
        Dict[str, Any]: The user object dictionary if a user is found. It contains:
            - name (str): The username of the user.
            - key (str): The unique identifier (account ID) for the user.
            - active (bool): The user's active status.
            - emailAddress (str): The user's primary email address.
            - displayName (str): The user's display name.
            - profile (Optional[Dict[str, Any]]): A dictionary containing `bio` and `joined` date, if available.
                - bio (Optional[str]): The user's biography.
                - joined (Optional[str]): The date the user joined.
            - groups (Optional[List[str]]): A list of group names the user belongs to, if available.
            - labels (Optional[List[str]]): A list of labels associated with the user, if available.
            - settings (Optional[Dict[str, Any]]): A dictionary of user-specific settings, if available,
                - theme (Optional[str]): The user's theme preference.
                - notifications (Optional[bool]): The user's notification preference.
            - history (Optional[List[Dict[str, Any]]]): A list of the user's activity history, if available.
                - action (Optional[str]): The action performed.
                - timestamp (Optional[str]): The timestamp of the action.
            - watch (Optional[List[str]]): A list of items the user is watching, if available.
    Raises:
        TypeError: If username is provided and is not a string.
        TypeError: If account_id is provided and is not a string.
        MissingUserIdentifierError: If neither username nor account_id is provided.
        UserNotFoundError: If the user is not found.
    """
    # Input Validation
    if username is not None and not isinstance(username, str):
        raise TypeError("username must be a string if provided.")

    if account_id is not None and not isinstance(account_id, str):
        raise TypeError("account_id must be a string if provided.")

    if username is None and account_id is None:
        raise MissingUserIdentifierError("Either username or account_id must be provided.")

    if account_id:
        user = DB.get("users", {}).get(account_id)
        if user:
            return user

    if username:
        users_map = DB.get("users", {})
        for u in users_map.values():
            if u.get("name") == username:
                return u

    raise UserNotFoundError("User not found.")


@tool_spec(
    spec={
        'name': 'create_user',
        'description': """ Create a new user with all required fields.
        
        This function validates the input payload to ensure it contains the necessary
        user details and that the email is not already in use. On success, it
        populates a user object with a mix of provided data and sensible defaults. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'payload': {
                    'type': 'object',
                    'description': "A dictionary containing the user's details.",
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The username for the new user. (Required)'
                        },
                        'emailAddress': {
                            'type': 'string',
                            'description': "The user's primary email address. (Required)"
                        },
                        'displayName': {
                            'type': 'string',
                            'description': 'The name to display in the UI. If not provided, defaults to the username.'
                        },
                        'profile': {
                            'type': 'object',
                            'description': 'A dictionary for profile info.',
                            'properties': {
                                'bio': {
                                    'type': 'string',
                                    'description': "The user's biography."
                                },
                                'joined': {
                                    'type': 'string',
                                    'description': 'The date the user joined.'
                                }
                            },
                            'required': []
                        },
                        'groups': {
                            'type': 'array',
                            'description': 'A list of group names.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'labels': {
                            'type': 'array',
                            'description': 'A list of label strings.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'settings': {
                            'type': 'object',
                            'description': 'A dictionary for user settings.',
                            'properties': {
                                'theme': {
                                    'type': 'string',
                                    'description': "The user's theme preference (defaults to 'light')."
                                },
                                'notifications': {
                                    'type': 'boolean',
                                    'description': "The user's notification preference (defaults to True)."
                                }
                            },
                            'required': []
                        },
                        'history': {
                            'type': 'array',
                            'description': """ A list of history event objects.
                                 - Each object is a dict with the keys: """,
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'action': {
                                        'type': 'string',
                                        'description': 'The action performed.'
                                    },
                                    'timestamp': {
                                        'type': 'string',
                                        'description': 'The timestamp of the action.'
                                    }
                                },
                                'required': []
                            }
                        },
                        'watch': {
                            'type': 'array',
                            'description': 'A list of watched item IDs.',
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': [
                        'name',
                        'emailAddress'
                    ]
                }
            },
            'required': [
                'payload'
            ]
        }
    }
)
def create_user(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new user with all required fields.

    This function validates the input payload to ensure it contains the necessary
    user details and that the email is not already in use. On success, it
    populates a user object with a mix of provided data and sensible defaults.

    Args:
        payload (Dict[str, Any]): A dictionary containing the user's details.
            - name (str): The username for the new user. (Required)
            - emailAddress (str): The user's primary email address. (Required)
            - displayName (Optional[str]): The name to display in the UI. If not provided, defaults to the username.
            - profile (Optional[Dict[str, Any]]): A dictionary for profile info.
                - bio (Optional[str]): The user's biography.
                - joined (Optional[str]): The date the user joined.
            - groups (Optional[List[str]]): A list of group names.
            - labels (Optional[List[str]]): A list of label strings.
            - settings (Optional[Dict[str, Any]]): A dictionary for user settings.
                - theme (Optional[str]): The user's theme preference (defaults to 'light').
                - notifications (Optional[bool]): The user's notification preference (defaults to True).
            - history (Optional[List[Dict[str, Any]]]): A list of history event objects.
                - Each object is a dict with the keys:
                    - action (Optional[str]): The action performed.
                    - timestamp (Optional[str]): The timestamp of the action.
            - watch (Optional[List[str]]): A list of watched item IDs.

    Returns:
        Dict[str, Any]: A dictionary containing a 'created' flag and the new 'user'
            object. The user object's structure is detailed below.

            - created (bool): Always True on success.
            - user (Dict[str, Any]): The newly created user object, containing:
                - name (str): The username of the user.
                - key (str): The unique identifier for the user.
                - active (bool): User status, always True on creation.
                - emailAddress (str): The user's primary email address.
                - displayName (str): The user's display name.
                - profile (Dict[str, Any]): Contains user profile information.
                    - bio (Optional[str]): The user's biography.
                    - joined (Optional[str]): The date the user joined.
                - groups (List[str]): A list of group names the user belongs to.
                - labels (List[str]): A list of strings representing labels.
                - settings (Dict[str, Any]): User-specific settings.
                    - theme (str): The user's selected theme (defaults to 'light').
                    - notifications (bool): The user's notification preference (defaults to True).
                - history (List[Dict[str, Any]]): A list of the user's activity history objects. Each object is a dict with the keys:
                    - action (Optional[str]): The action performed (e.g., 'login').
                    - timestamp (Optional[str]): The timestamp of the action.
                - watch (List[str]): A list of strings representing watched item IDs.

    Raises:
        TypeError: If the `payload` argument is not a dictionary.
        ValidationError: If the payload fails validation (e.g.,
                                  missing required fields, invalid email format).
    """
    # --- Input Validation ---
    if not isinstance(payload, dict):
        raise TypeError(f"Expected payload to be a dict, got {type(payload).__name__}")

    try:
        validated_payload = UserCreationPayload(**payload)
    except ValidationError as e:
        raise e
    # --- End Input Validation ---

    # Use validated fields from Pydantic model for defined attributes
    uname = validated_payload.name
    email = validated_payload.emailAddress # This is an EmailStr object, but behaves like a str
    display_name = validated_payload.displayName or uname  # Use username as default if displayName not provided

    user_key = str(uuid.uuid4())
    while user_key in DB["users"]:
        user_key = str(uuid.uuid4())

    # Build profile from validated data
    if validated_payload.profile is not None:
        # If a field was provided in the original payload (even as None), use the validated value
        # If not provided, use empty string as default
        raw_profile = payload.get("profile", {})
        if raw_profile is not None and not isinstance(raw_profile, dict):
            raw_profile = {}
        
        # For bio: use validated value if provided in payload, else empty string
        if "bio" in (raw_profile or {}):
            profile_bio = validated_payload.profile.bio
        else:
            profile_bio = ""
        
        # For joined: use validated value if provided in payload, else empty string
        if "joined" in (raw_profile or {}):
            profile_joined = validated_payload.profile.joined
        else:
            profile_joined = ""
        
        profile_data = {
            "bio": profile_bio,
            "joined": profile_joined,
        }
    else:
        profile_data = {"bio": "", "joined": ""}
    
    # Build settings from validated data
    if validated_payload.settings is not None:
        # Settings have defaults in Pydantic model, so we can use the validated values directly
        settings_data = {
            "theme": validated_payload.settings.theme,
            "notifications": validated_payload.settings.notifications,
        }
    else:
        settings_data = {"theme": "light", "notifications": True}
    
    # Build history from validated data
    if validated_payload.history is not None:
        history_data = [h.model_dump() for h in validated_payload.history]
    else:
        history_data = []

    user_defaults = {
        "name": uname,
        "key": user_key,
        "active": True,
        "emailAddress": str(email), # Ensure it's a plain string if EmailStr causes issues downstream
        "displayName": display_name,
        "profile": profile_data,
        "groups": validated_payload.groups or [],
        "labels": validated_payload.labels or [],
        "settings": settings_data,
        "history": history_data,
        "watch": validated_payload.watch or [],
    }

    DB["users"][user_key] = user_defaults
    return {"created": True, "user": DB["users"][user_key]}

@tool_spec(
    spec={
        'name': 'delete_user_by_username_or_key',
        'description': 'Delete a user by username or key. Either username or key must be provided.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The username of the user to delete. This cannot be an empty string if provided.'
                },
                'key': {
                    'type': 'string',
                    'description': 'The key of the user to delete. This cannot be an empty string if provided.'
                }
            },
            'required': []
        }
    }
)
def delete_user(username: Optional[str] = None, key: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a user by username or key. Either username or key must be provided.

    Args:
        username (Optional[str]): The username of the user to delete. This cannot be an empty string if provided.
        key (Optional[str]): The key of the user to delete. This cannot be an empty string if provided.

    Returns:
        Dict[str, Any]: A dictionary containing the user's information.
            - deleted (str): The key of the user that was deleted.
    Raises:
        TypeError: If username or key is not a string.
        MissingUserIdentifierError: If neither username nor key is provided.
        UserNotFoundError: If the user is not found.
    """
    # input validation
    if username is not None and not isinstance(username, str):
        raise TypeError("username must be a string if provided.")
    if key is not None and not isinstance(key, str):
        raise TypeError("key must be a string if provided.")
    
    # Check if both are falsy (None, empty string, etc.) - at least one must be truthy
    if not username and not key:
        raise MissingUserIdentifierError("Either username or key must be provided.")

    if username:
        for u in DB["users"].values():
            if u["name"] == username:
                key = u["key"]
                break
        else:
            raise UserNotFoundError("User not found.")
        
    if key:
        if key not in DB["users"]:
            raise UserNotFoundError("User not found.")
        del DB["users"][key]
    return {"deleted": key}



@tool_spec(
    spec={
        'name': 'find_users',
        'description': """ Finds users by a string search against their name, display name, and email.
        
        This function provides a general-purpose search for users and supports
        pagination and filtering by active status. The search is case-insensitive. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'search_string': {
                    'type': 'string',
                    'description': 'The search string to match against user fields name, display name, and email. Empty or whitespace-only strings are invalid.'
                },
                'startAt': {
                    'type': 'integer',
                    'description': 'The index of the first user to return. Defaults to 0.'
                },
                'maxResults': {
                    'type': 'integer',
                    'description': """ The maximum number of users to return. Defaults to 50 (maximum allowed value is 1000). 
                    If you specify a value that is higher than 1000, your search results will be truncated. """
                },
                'includeActive': {
                    'type': 'boolean',
                    'description': 'If True, active users are included. Defaults to True.'
                },
                'includeInactive': {
                    'type': 'boolean',
                    'description': 'If True, inactive users are included. Defaults to False.'
                }
            },
            'required': [
                'search_string'
            ]
        }
    }
)
def find_users(
    search_string: str,
    startAt: Optional[int] = 0,
    maxResults: Optional[int] = 50,
    includeActive: Optional[bool] = True,
    includeInactive: Optional[bool] = False,
) -> List[Dict[str, Any]]:
    """
    Finds users by a string search against their name, display name, and email.

    This function provides a general-purpose search for users and supports
    pagination and filtering by active status. The search is case-insensitive.

    Args:
        search_string (str): The search string to match against user fields name, display name, and email. Empty or whitespace-only strings are invalid.
        startAt (Optional[int]): The index of the first user to return. Defaults to 0.
        maxResults (Optional[int]): The maximum number of users to return. Defaults to 50 (maximum allowed value is 1000). 
                If you specify a value that is higher than 1000, your search results will be truncated.
        includeActive (Optional[bool]): If True, active users are included. Defaults to True.
        includeInactive (Optional[bool]): If True, inactive users are included. Defaults to False.

    Returns:
        List[Dict[str, Any]]: A list of user objects matching the criteria.
            Each user object contains:
            - name (str): The username of the user.
            - key (str): The unique identifier (account ID) for the user.
            - active (bool): The user's active status.
            - emailAddress (str): The user's primary email address.
            - displayName (str): The user's display name.
            - profile (Optional[Dict[str, Any]]): User profile information, if available.
                - bio (Optional[str]): The user's biography.
                - joined (Optional[str]): The date the user joined.
            - groups (Optional[List[str]]): A list of group names the user belongs to, if available.
            - labels (Optional[List[str]]): A list of label strings, if available.
            - settings (Optional[Dict[str, Any]]): User-specific settings, if available.
                - theme (Optional[str]): The user's theme preference.
                - notifications (Optional[bool]): The user's notification preference.
            - history (Optional[List[Dict[str, Any]]]): A list of history event objects, if available.
                - action (Optional[str]): The action performed.
                - timestamp (Optional[str]): The timestamp of the action.
            - watch (Optional[List[str]]): A list of watched item IDs, if available.

    Raises:
        TypeError: If 'search_string' is not a string,
                   'startAt' or 'maxResults' are not integers,
                   or 'includeActive' or 'includeInactive' are not booleans.
        ValueError: If 'search_string' is an empty string (after stripping whitespace),
                    'startAt' is negative,
                    or 'maxResults' is not a positive integer.
    """
    # --- Input Validation Start ---
    if not isinstance(search_string, str):
        raise TypeError("search_string must be a string.")
    if not search_string.strip():
        raise ValueError("search_string cannot be empty.")

    if not isinstance(startAt, int):
        raise TypeError("startAt must be an integer.")
    if startAt < 0:
        raise ValueError("startAt must be a non-negative integer.")

    if not isinstance(maxResults, int):
        raise TypeError("maxResults must be an integer.")
    if maxResults <= 0:
        raise ValueError("maxResults must be a positive integer.")

    if not isinstance(includeActive, bool):
        raise TypeError("includeActive must be a boolean.")
    if not isinstance(includeInactive, bool):
        raise TypeError("includeInactive must be a boolean.")
    # --- Input Validation End ---

    query_lower = search_string.lower()
    users = [
        user
        for user in DB["users"].values() # Assuming DB is a global or accessible dictionary
        if query_lower in user["name"].lower()
        or query_lower in user["emailAddress"].lower()
        or query_lower in user["displayName"].lower()
    ]
    # Filter based on active/inactive status
    
    # A user is included if their active status matches the corresponding flag.
    # This elegantly handles all four cases (active, inactive, both, or neither).
    filtered_users = [
        user for user in users
        if (user.get("active", True) and includeActive) or \
           (not user.get("active", True) and includeInactive)
    ]
    
    # Paging
    end_index = startAt + min(maxResults, 1000)
    paged_users = filtered_users[startAt:end_index]

    return paged_users