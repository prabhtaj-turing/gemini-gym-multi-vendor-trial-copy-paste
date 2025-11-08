from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/PermissionSchemeApi.py
from .SimulationEngine.db import DB
from typing import Dict, List, Any, Union


@tool_spec(
    spec={
        'name': 'get_all_permission_schemes',
        'description': """ Get all permission schemes.
        
        This method returns all permission schemes in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_permission_schemes() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all permission schemes.

    This method returns all permission schemes in the system.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing:
            - schemes (List[Dict[str, Any]]): The permission schemes in the system.
              Returns an empty list if no permission schemes exist in the database.
                - id (str): The id of the permission scheme
                - name (str): The name of the permission scheme
                - permissions (List[str]): The permissions in the permission scheme
    """
    return {"schemes": list(DB["permission_schemes"].values())}


@tool_spec(
    spec={
        'name': 'get_permission_scheme_by_id',
        'description': """ Get a permission scheme by id.
        
        This method returns a permission scheme by id from the database. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'scheme_id': {
                    'type': 'string',
                    'description': 'The id of the permission scheme to get'
                }
            },
            'required': [
                'scheme_id'
            ]
        }
    }
)
def get_permission_scheme(scheme_id: str) -> Dict[str, Union[str, List[str]]]:
    """
    Get a permission scheme by id.

    This method returns a permission scheme by id from the database.

    Args:
        scheme_id (str): The id of the permission scheme to get

    Returns:
        Dict[str, Union[str, List[str]]]: The permission scheme with keys:
            - id (str): The id of the permission scheme
            - name (str): The name of the permission scheme
            - permissions (List[str]): The permissions in the permission scheme

    Raises:
        TypeError: If scheme_id is not a string
        ValueError: If scheme_id is empty or the permission scheme is not found
    """
    # Type validation
    if not isinstance(scheme_id, str):
        raise TypeError("scheme_id must be a string")
    
    # Empty field validation
    if not scheme_id or not scheme_id.strip():
        raise ValueError("scheme_id cannot be empty")
    
    # Get scheme from database
    scheme = DB["permission_schemes"].get(scheme_id)
    if not scheme:
        raise ValueError(f"Permission scheme '{scheme_id}' not found.")
    
    return scheme
