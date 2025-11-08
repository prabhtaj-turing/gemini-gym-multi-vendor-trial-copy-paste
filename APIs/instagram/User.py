import re
from common_utils.tool_spec_decorator import tool_spec
# instagram/User.py
from .SimulationEngine.custom_errors import EmptyUsernameError
from .SimulationEngine.custom_errors import UserAlreadyExistsError
from .SimulationEngine.custom_errors import UserNotFoundError
from .SimulationEngine.db import DB
from .SimulationEngine.utils import validate_user_id_format
from typing import Dict, Any, List

"""Handles user-related operations."""


@tool_spec(
    spec={
        'name': 'create_user',
        'description': 'Creates a new user with a given ID, name, and username. Leading/trailing whitespace is trimmed from user_id and username.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The unique identifier for the user. Leading/trailing whitespace is trimmed.Can only contain letters, numbers, periods, and underscores'
                },
                'name': {
                    'type': 'string',
                    'description': 'The name of the user.'
                },
                'username': {
                    'type': 'string',
                    'description': 'The username of the user. Leading/trailing whitespace is trimmed.'
                }
            },
            'required': [
                'user_id',
                'name',
                'username'
            ]
        }
    }
)
def create_user(user_id: str, name: str, username: str) -> Dict[str, str]:
    """
    Creates a new user with a given ID, name, and username. Leading/trailing whitespace is trimmed from user_id and username.
    
    Args:
        user_id (str): The unique identifier for the user. Leading/trailing whitespace is trimmed. Can only contain letters, numbers, periods, and underscores.
        name (str): The name of the user.
        username (str): The username of the user. Leading/trailing whitespace is trimmed.

    Returns:
        Dict[str, str]: On successful creation, a dictionary containing the user's details:
            - "id" (str): The user's unique identifier.
            - "name" (str): The user's name.
            - "username" (str): The user's username.

    Raises:
        TypeError: If `user_id` is not a string.
        TypeError: If `name` is not a string.
        TypeError: If `username` is not a string.
        ValueError: If `user_id` is an empty string or only whitespace.
        ValueError: If `name` is an empty string or only whitespace.
        ValueError: If `username` is an empty string or only whitespace.
        ValueError: If user_id contains invalid characters (only letters, numbers, periods, and underscores are allowed).
        UserAlreadyExistsError: If a user with the given `user_id` already exists.
    """
    # Input validation for non-dictionary arguments
    if not isinstance(user_id, str):
        raise TypeError("Argument user_id must be a string.")
    if not user_id.strip():  # Check for empty string
        raise ValueError("Field user_id cannot be empty.")
    
    if not isinstance(name, str):
        raise TypeError("Argument name must be a string.")
    if not name.strip():  # Check for empty string
        raise ValueError("Field name cannot be empty.")

    if not isinstance(username, str):
        raise TypeError("Argument username must be a string.")
    if not username.strip():  # Check for empty string
        raise ValueError("Field username cannot be empty.")
    
    # Strip whitespace from user_id and username before saving
    user_id = user_id.strip()
    username = username.strip()
    
    # Add character format validation after stripping
    validate_user_id_format(user_id)

    # Core logic of the function (preserved)
    # DB is assumed to be an accessible dictionary-like structure.
    if user_id in DB["users"]:
        raise UserAlreadyExistsError(f"User with ID '{user_id}' already exists.")

    DB["users"][user_id] = {"name": name, "username": username}
    return {"id": user_id, "name": name, "username": username}


@tool_spec(
    spec={
        'name': 'get_user_details',
        'description': 'Retrieves information about a specific user. Leading/trailing whitespace is trimmed from user_id.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the user to retrieve. Leading/trailing whitespace is trimmed. Cannot be empty. Can only contain letters, numbers, periods, and underscores.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def get_user(user_id: str) -> Dict[str, str]:
    """
    Retrieves information about a specific user. Leading/trailing whitespace is trimmed from user_id.
    
    Args:
        user_id (str): The unique identifier of the user to retrieve. Leading/trailing whitespace is trimmed. Cannot be empty Can only contain letters, numbers, periods, and underscore.

    Returns:
        Dict[str, str]:
        - If the user does not exist (after passing input validation), throws UserNotFoundError.
        - On successful retrieval, returns a dictionary with the following keys and value types:
            - id (str): The user's unique identifier
            - name (str): The user's name
            - username (str): The user's username

    Raises:
        TypeError: If user_id is not a string.
        ValueError: If user_id is an empty string.
        ValueError: If user_id contains invalid characters (only letters, numbers, periods, and underscores are allowed).
        UserNotFoundError: If the user with the given user_id does not exist.
    """
    # --- Input Validation ---
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    if not user_id.strip():  # Checks for empty string
        raise ValueError("Field user_id cannot be empty.")
    
    # Strip whitespace before validation and use
    user_id = user_id.strip()
    
    # Add character format validation
    validate_user_id_format(user_id)
    # --- End of Input Validation ---

    # --- Original Core Logic ---
    # DB is assumed to be an existing global or accessible dictionary-like structure.
    if user_id in DB["users"]:
        user_data = DB["users"][user_id]
        return {
            "id": user_id,
            "name": user_data.get("name"),
            "username": user_data.get("username")
        }
    else:
        raise UserNotFoundError(f"User with ID '{user_id}' does not exist.")

@tool_spec(
    spec={
        'name': 'list_all_users',
        'description': 'Lists all users in the system.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_users() -> List[Dict[str, str]]:
    """
    Lists all users in the system.
    Returns:
        List[Dict[str, str]]: A list of dictionaries, where each dictionary contains:
            - id (str): The user's unique identifier
            - name (str): The user's name
            - username (str): The user's username
    """
    return [{"id": user_id, **info} for user_id, info in DB["users"].items()]


@tool_spec(
    spec={
        'name': 'delete_user',
        'description': 'Deletes a specified user from the system. Leading/trailing whitespace is trimmed from user_id.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the user to delete. Leading/trailing whitespace is trimmed. Can only contain letters, numbers, periods, and underscores.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def delete_user(user_id: str) -> Dict[str, Any]:
    """
    Deletes a specified user from the system. Leading/trailing whitespace is trimmed from user_id.

    Args:
        user_id (str): The unique identifier of the user to delete. Leading/trailing whitespace is trimmed. Can only contain letters, numbers, periods, and underscores.

    Returns:
        Dict[str, Any]:
        - If user_id is missing or empty, returns a dictionary with the key "error" and the value "Field user_id cannot be empty."
        - If the user does not exist, returns a dictionary with the key "error" and the value "User not found."
        - On successful deletion, returns a dictionary with the key "success" and the value True.

    Raises:
        TypeError: If user_id is not a string.
        ValueError: If user_id is an empty string.
        ValueError: If user_id contains invalid characters (only letters, numbers, periods, and underscores are allowed).
        UserNotFoundError: If the user with the given user_id does not exist.
    """
    # Input validation
    if not isinstance(user_id, str):
        raise TypeError("Argument user_id must be a string.")

    if not user_id or user_id.isspace():  # Check for empty string or whitespace-only
        raise ValueError("Field user_id cannot be empty.")
    
    # Strip whitespace before validation and use
    user_id = user_id.strip()
    
    # Add character format validation
    validate_user_id_format(user_id)

    # Core logic
    if user_id in DB["users"]:
        del DB["users"][user_id]
        return {"success": True}
    else:
        raise UserNotFoundError(f"User with ID '{user_id}' does not exist.")


@tool_spec(
    spec={
        'name': 'get_user_id_by_username',
        'description': 'Searches for a user by their username and returns the corresponding user ID. Leading/trailing whitespace is trimmed from username.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': """The username to look up in the system. The search is case-insensitive. using casefold() for robust Unicode case-folding comparison. Leading/trailing whitespace is trimmed. This field cannot be an empty string or contain only whitespace."""
                }
            },
            'required': [
                'username'
            ]
        }
    }
)
def get_user_id_by_username(username: str) -> str:
    """
    Searches for a user by their username and returns the corresponding user ID. Leading/trailing whitespace is trimmed from username.
    
    Args:
        username (str): The username to look up in the system. The search is case-insensitive.
                        using casefold() for robust Unicode case-folding comparison.
                        Leading/trailing whitespace is trimmed. This field cannot be an empty string or contain only whitespace.

    Returns:
        str: The user ID as a string if a user with the given username is found.

    Raises:
        TypeError: If 'username' is not a string.
        EmptyUsernameError: If 'username' is an empty string or consists only of whitespace.
        UserNotFoundError: If the user with the given username does not exist.
    """
    # --- Start of Input Validation ---
    if not isinstance(username, str):
        raise TypeError("Username must be a string.")

    # Check if username is empty or contains only whitespace characters
    # This validation is derived from the original docstring's requirement:
    # "If username is missing, returns a dictionary with the key "error" and the value "Field username cannot be empty."
    # which is now handled by raising EmptyUsernameError.
    if not username or username.isspace():
        raise EmptyUsernameError("Field username cannot be empty.")
    
    # --- End of Input Validation ---
    # Strip whitespace before comparison (as documented in the docstring and spec)
    original_username = username  # Preserve original for error message
    username = username.strip()

    # Normalize the input username: convert to lowercase 
    normalized_input = username.casefold()

    # Original core functionality (preserved)
    # The DB variable is assumed to be defined and accessible in this scope.
    for user_id, user in DB["users"].items():
        # Normalize stored username: convert to lowercase AND strip whitespace
        stored_username = user.get("username", "").strip().casefold()
        
        # Compare normalized usernames
        if stored_username == normalized_input:
            return user_id

    # This return statement is part of the original function's logic.
    # The original docstring incorrectly stated this would be a dictionary error.
    # The original code (and this refactored version) returns a string.
    raise UserNotFoundError(f"User with username '{original_username}' does not exist.")
