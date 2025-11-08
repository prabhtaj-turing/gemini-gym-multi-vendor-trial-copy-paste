from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/SecurityLevelApi.py
from typing import Dict, Any, List
from .SimulationEngine.db import DB
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'get_all_security_levels',
        'description': """ Get all security levels.
        
        This method returns all security levels in the system. If no security levels
        exist, an empty list is returned. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_security_levels() -> Dict[str, Any]:
    """
    Get all security levels.

    This method returns all security levels in the system. If no security levels
    exist, an empty list is returned.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - securityLevels (List[Dict[str, Any]]): A list of security levels
                - id (str): The id of the security level
                - name (str): The name of the security level  
                - description (str): The description of the security level

    Example:
        >>> result = get_security_levels()
        >>> print(result)
        {
            "securityLevels": [
                {
                    "id": "SL-1",
                    "name": "Confidential", 
                    "description": "Sensitive issues"
                }
            ]
        }
    """
    security_levels = DB.get("security_levels", {})
    return {"securityLevels": list(security_levels.values())}


@tool_spec(
    spec={
        'name': 'get_security_level_by_id',
        'description': """ Get a security level by id.
        
        This method returns a security level by id. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'sec_id': {
                    'type': 'string',
                    'description': 'The id of the security level. Cannot be empty or None.'
                }
            },
            'required': [
                'sec_id'
            ]
        }
    }
)
def get_security_level(sec_id: str) -> Dict[str, Any]:
    """
    Get a security level by id.

    This method returns a security level by id.

    Args:
        sec_id (str): The id of the security level. Cannot be empty or None.

    Returns:
        Dict[str, Any]: The security level dictionary containing:
            - id (str): The id of the security level
            - name (str): The name of the security level
            - description (str): The description of the security level

    Raises:
        TypeError: If sec_id is not a string
        ValueError: If sec_id is empty or the security level is not found

    Example:
        >>> result = get_security_level("SL-1")
        >>> print(result)
        {
            "id": "SL-1",
            "name": "Confidential",
            "description": "Sensitive issues"
        }
    """
    # Input validation
    if not isinstance(sec_id, str):
        raise TypeError(f"sec_id must be a string, got {type(sec_id).__name__}")
    
    if not sec_id or not sec_id.strip():
        raise ValueError("sec_id cannot be empty or consist only of whitespace")
    
    # Handle case where security_levels key might not exist in DB
    security_levels = DB.get("security_levels", {})
    lvl = security_levels.get(sec_id)
    
    if not lvl:
        raise ValueError(f"Security level '{sec_id}' not found")
    
    return lvl
