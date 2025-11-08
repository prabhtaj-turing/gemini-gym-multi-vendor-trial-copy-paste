from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/StatusApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import MissingRequiredFieldError
from typing import Dict, Any

@tool_spec(
    spec={
        'name': 'get_all_statuses',
        'description': """ Get all statuses.
        
        This method returns all statuses in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_statuses() -> Dict[str, Any]:
    """
    Get all statuses.

    This method returns all statuses in the system.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - statuses (List[Dict[str, Any]]): A list of statuses.
                Each status dictionary has:
                - id (str): The id of the status.
                - name (str): The name of the status.
                - description (str): The description of the status.
                - statusCategory (str): The category of the status.
    """
    if "statuses" not in DB:
        DB["statuses"] = {}  # Initialize the statuses dictionary
    return {"statuses": list(DB["statuses"].values())}


@tool_spec(
    spec={
        'name': 'get_status_by_id',
        'description': """ Get a status by id.
        
        This method returns a status by id. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'status_id': {
                    'type': 'string',
                    'description': 'The id of the status'
                }
            },
            'required': [
                'status_id'
            ]
        }
    }
)
def get_status(status_id: str) -> Dict[str, Any]:
    """
    Get a status by id.

    This method returns a status by id.

    Args:
        status_id (str): The id of the status

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status (Dict[str, Any]): The status
                - id (str): The id of the status
                - name (str): The name of the status
                - description (str): The description of the status
                - statusCategory (str): The category of the status.

    Raises:
        MissingRequiredFieldError: If status_id is not provided.
        TypeError: If status_id is not a string.
        ValueError: If the status is not found.
    """
    if not status_id:
        raise MissingRequiredFieldError(field_name="status_id")
    if not isinstance(status_id, str):
        raise TypeError("status_id must be a string")
    
    if "statuses" not in DB:
        DB["statuses"] = {}
    
    if status_id not in DB["statuses"]:
        raise ValueError(f"Status '{status_id}' not found.")
    
    return DB["statuses"][status_id]    
