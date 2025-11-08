from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/IssueTypeApi.py
from .SimulationEngine.utils import _generate_id
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import EmptyFieldError, IssueTypeNotFoundError
from typing import Dict, Any
import builtins

@tool_spec(
    spec={
        'name': 'get_all_issue_types',
        'description': """ Retrieve all issue types from Jira.
        
        This method returns a list of all issue types defined in the system.
        Issue types are used to categorize and manage issues in Jira. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_issue_types() -> Dict[str, Any]:
    """
    Retrieve all issue types from Jira.

    This method returns a list of all issue types defined in the system.
    Issue types are used to categorize and manage issues in Jira.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - issueTypes (List[Dict[str, Any]]): A list of issue type objects, where each type contains:
                - id (str): The unique identifier for the issue type
                - name (str): The display name of the issue type
                - description (Optional[str]): The description of the issue type
                - subtask (bool): Whether the issue type is a subtask

    """
    return {"issueTypes": list(DB["issue_types"].values())}


@tool_spec(
    spec={
        'name': 'get_issue_type_by_id',
        'description': """ Retrieve a specific issue type by its ID.
        
        This method returns detailed information about a specific issue type
        identified by its unique ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'type_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the issue type to retrieve. Must be a non-empty string.'
                }
            },
            'required': [
                'type_id'
            ]
        }
    }
)
def get_issue_type(type_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific issue type by its ID.

    This method returns detailed information about a specific issue type
    identified by its unique ID.

    Args:
        type_id (str): The unique identifier of the issue type to retrieve. Must be a non-empty string.

    Returns:
        Dict[str, Any]: The issue type object containing:
            - id (str): The unique identifier for the issue type
            - name (str): The display name of the issue type
            - description (str): The description of the issue type
            - subtask (bool): Whether the issue type is a subtask

    Raises:
        TypeError: If type_id is not a string.
        ValueError: If type_id is an empty string.
        IssueTypeNotFoundError: If the issue type with the given ID is not found in the database.
    """
    # Input type validation
    if not isinstance(type_id, str):
        raise TypeError(f"type_id must be a string, got {type(type_id).__name__}.")
    
    # Input value validation
    if not type_id:
        raise ValueError("type_id cannot be empty.")

    # Check if issue type exists in database
    issue_type = DB["issue_types"].get(type_id)
    if not issue_type:
        raise IssueTypeNotFoundError(f"Issue type with ID '{type_id}' not found in database.")
    
    return issue_type


@tool_spec(
    spec={
        'name': 'create_issue_type',
        'description': """ Create a new issue type in Jira.
        
        This method creates a new issue type with the specified name and description.
        The issue type will be assigned a unique ID and stored in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the issue type. Cannot be empty.'
                },
                'description': {
                    'type': 'string',
                    'description': 'The description of the issue type. Cannot be empty.'
                },
                'type': {
                    'type': 'string',
                    'description': """ The type of issue type to create (default is "standard").
                    Expected values are "standard" or "subtask". 
                    Any other value provided is treated as "standard" by the code. """
                }
            },
            'required': [
                'name',
                'description'
            ]
        }
    }
)
def create_issue_type(name: str, description: str, type: str = "standard") -> Dict[str, Any]:
    """
    Create a new issue type in Jira.

    This method creates a new issue type with the specified name and description.
    The issue type will be assigned a unique ID and stored in the system.

    Args:
        name (str): The name of the issue type. Cannot be empty.
        description (str): The description of the issue type. Cannot be empty.
        type (str): The type of issue type to create (default is "standard").
                    Expected values are "standard" or "subtask". 
                    Any other value provided is treated as "standard" by the code.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - created (bool): Whether the issue type was created successfully
            - issueType (Dict[str, Any]): The created issue type object
                - id (str): The unique identifier for the issue type
                - name (str): The display name of the issue type
                - description (str): The description of the issue type
                - subtask (bool): Whether the issue type is a subtask

    Raises:
        TypeError: If 'name', 'description', or 'type' is not a string.
        EmptyFieldError: If 'name' or 'description' is an empty string.
    """
    # Validate 'name'
    if not isinstance(name, str):
        raise TypeError(f"Argument 'name' must be a string, not {builtins.type(name).__name__}.")
    if not name:
        raise EmptyFieldError("name")

    # Validate 'description'
    if not isinstance(description, str):
        raise TypeError(f"Argument 'description' must be a string, not {builtins.type(description).__name__}.")
    if not description:
        raise EmptyFieldError("description")

    # Validate 'type'
    if not isinstance(type, str):
        raise TypeError(f"Argument 'type' must be a string, not {builtins.type(type).__name__}.")

    issue_type_id = _generate_id("ISSUETYPE", DB["issue_types"])
    issue_type = {
        "id": issue_type_id,
        "name": name,
        "description": description,
        "subtask": type == "subtask",
    }
    DB["issue_types"][issue_type_id] = issue_type
    return {"created": True, "issueType": issue_type}
