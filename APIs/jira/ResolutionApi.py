from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/ResolutionApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import ResolutionNotFoundError
from typing import Dict, Any, List


@tool_spec(
    spec={
        'name': 'get_all_resolutions',
        'description': """ Get all resolutions.
        
        This method returns all resolutions in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_resolutions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all resolutions.

    This method returns all resolutions in the system.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing:
            - resolutions (List[Dict[str, Any]]): A list of resolutions
                - id (str): The id of the resolution
                - name (str): The name of the resolution
    """
    return {"resolutions": list(DB["resolutions"].values())}


@tool_spec(
    spec={
        'name': 'get_resolution_by_id',
        'description': """ Get a resolution by id.
        
        This method returns a resolution by id. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'res_id': {
                    'type': 'string',
                    'description': 'The id of the resolution. Must be a non-empty string.'
                }
            },
            'required': [
                'res_id'
            ]
        }
    }
)
def get_resolution(res_id: str) -> Dict[str, Any]:
    """
    Get a resolution by id.

    This method returns a resolution by id.

    Args:
        res_id (str): The id of the resolution. Must be a non-empty string.

    Returns:
        Dict[str, Any]: The resolution object containing:
            - id (str): The id of the resolution
            - name (str): The name of the resolution

    Raises:
        TypeError: If res_id is not a string.
        ValueError: If res_id is an empty string.
        ResolutionNotFoundError: If the resolution with the given ID is not found in the database.
    """
    # Input type validation
    if not isinstance(res_id, str):
        raise TypeError(f"res_id must be a string, got {type(res_id).__name__}.")
    
    # Input value validation
    if not res_id:
        raise ValueError("res_id cannot be empty.")

    # Check if resolution exists in database
    resolution = DB["resolutions"].get(res_id)
    if not resolution:
        raise ResolutionNotFoundError(f"Resolution with ID '{res_id}' not found in database.")
    
    return resolution
