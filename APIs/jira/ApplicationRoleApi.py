from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/ApplicationRoleApi.py

from .SimulationEngine.db import DB
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'get_all_application_roles',
        'description': """ Retrieve all application roles from Jira.
        
        This method returns a list of all application roles defined in the system.
        Application roles are used to control access to specific Jira features and functionality. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_application_roles() -> Dict[str, Any]:
    """
    Retrieve all application roles from Jira.

    This method returns a list of all application roles defined in the system.
    Application roles are used to control access to specific Jira features and functionality.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - roles (List[Dict[str, Any]]): A list of application role objects, where each role contains:
                - key (str): The unique identifier for the role
                - name (str): The display name of the role

    """
    return {"roles": list(DB["application_roles"].values())}


@tool_spec(
    spec={
        'name': 'get_application_role_by_key',
        'description': """ Retrieve a specific application role by its key.
        
        This method returns detailed information about a specific application role
        identified by its unique key. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'key': {
                    'type': 'string',
                    'description': 'The unique identifier of the application role to retrieve'
                }
            },
            'required': [
                'key'
            ]
        }
    }
)
def get_application_role_by_key(key: str) -> Dict[str, Any]:
    """
    Retrieve a specific application role by its key.

    This method returns detailed information about a specific application role
    identified by its unique key.

    Args:
        key (str): The unique identifier of the application role to retrieve

    Returns:
        Dict[str, Any]: A dictionary containing:
            - key (str): The unique identifier for the role
            - name (str): The display name of the role

    Raises:
        TypeError: If key is not a string
        ValueError: If key is empty or the specified role key does not exist
    """
    # Input validation
    if not isinstance(key, str):
        raise TypeError("key parameter must be a string")
    
    if not key:
        raise ValueError("key parameter cannot be empty")
    
    role = DB["application_roles"].get(key)
    if role is None:
        raise ValueError(f"Role '{key}' not found.")
    return role
