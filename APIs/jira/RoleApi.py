from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/RoleApi.py
from typing import Dict, Any, List
from .SimulationEngine.db import DB
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'get_all_roles',
        'description': """ Get all roles.
        
        This method returns all roles in the system. If no roles exist, 
        an empty list is returned. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_roles() -> Dict[str, Any]:
    """
    Get all roles.

    This method returns all roles in the system. If no roles exist, 
    an empty list is returned.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - roles (List[Dict[str, Any]]): A list of roles
                - id (str): The id of the role
                - name (str): The name of the role

    Example:
        >>> result = get_roles()
        >>> print(result)
        {
            "roles": [
                {
                    "id": "R-1",
                    "name": "Developer"
                }
            ]
        }
    """
    # Handle case where roles key might not exist in DB
    roles = DB.get("roles", {})
    return {"roles": list(roles.values())}


@tool_spec(
    spec={
        'name': 'get_role_by_id',
        'description': """ Get a role by id.
        
        This method returns a role by id. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'role_id': {
                    'type': 'string',
                    'description': 'The id of the role. Cannot be empty or None.'
                }
            },
            'required': [
                'role_id'
            ]
        }
    }
)
def get_role(role_id: str) -> Dict[str, Any]:
    """
    Get a role by id.

    This method returns a role by id.

    Args:
        role_id (str): The id of the role. Cannot be empty or None.

    Returns:
        Dict[str, Any]: The role dictionary containing:
            - id (str): The id of the role
            - name (str): The name of the role

    Raises:
        TypeError: If role_id is not a string
        ValueError: If role_id is empty, consists only of whitespace, or the role is not found

    Example:
        >>> result = get_role("R-1")
        >>> print(result)
        {
            "id": "R-1",
            "name": "Developer"
        }
    """
    # Input validation
    if not isinstance(role_id, str):
        raise TypeError(f"role_id must be a string, got {type(role_id).__name__}")
    
    if not role_id or not role_id.strip():
        raise ValueError("role_id cannot be empty or consist only of whitespace")
    
    # Handle case where roles key might not exist in DB
    roles = DB.get("roles", {})
    r = roles.get(role_id)
    
    if not r:
        raise ValueError(f"Role '{role_id}' not found")
    
    return r
