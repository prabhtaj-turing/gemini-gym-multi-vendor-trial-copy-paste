from common_utils.tool_spec_decorator import tool_spec
#APIs/JiraAPISimulation/IssueLinkTypeApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import MissingRequiredFieldError
from typing import Dict, List


@tool_spec(
    spec={
        'name': 'get_all_issue_link_types',
        'description': """ Retrieve all issue link types from Jira.
        
        This method returns a list of all issue link types defined in the system.
        Issue link types are used to categorize and manage relationships between issues. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_issue_link_types() -> Dict[str, List[Dict[str, str]]]:
    """
    Retrieve all issue link types from Jira.

    This method returns a list of all issue link types defined in the system.
    Issue link types are used to categorize and manage relationships between issues.

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary containing:
            - issueLinkTypes (List[Dict[str, str]]): A list of issue link type objects, where each type contains:
                - id (str): The unique identifier for the issue link type
                - name (str): The display name of the issue link type

    """
    return {"issueLinkTypes": list(DB.get("issue_link_types", {}).values())}


@tool_spec(
    spec={
        'name': 'get_issue_link_type_by_id',
        'description': """ Retrieve a specific issue link type by its ID.
        
        This method returns detailed information about a specific issue link type
        identified by its unique ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'link_type_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the issue link type to retrieve'
                }
            },
            'required': [
                'link_type_id'
            ]
        }
    }
)
def get_issue_link_type(link_type_id: str) -> Dict[str, Dict[str, str]]:
    """
    Retrieve a specific issue link type by its ID.

    This method returns detailed information about a specific issue link type
    identified by its unique ID.

    Args:
        link_type_id (str): The unique identifier of the issue link type to retrieve

    Returns:
        Dict[str, Dict[str, str]]: A dictionary containing:
            - issueLinkType (Dict[str, str]): The issue link type object
                - id (str): The unique identifier for the issue link type
                - name (str): The display name of the issue link type
    
    Raises:
        MissingRequiredFieldError: If the link_type_id is empty
        TypeError: If the link_type_id is not a string
        ValueError: If the link_type_id is not found in the database
    """
    if not link_type_id:
        raise MissingRequiredFieldError("link_type_id is required")
    if not isinstance(link_type_id, str):
        raise TypeError(f"link_type_id must be a string")

    if link_type_id not in DB["issue_link_types"]:
        raise ValueError(f"Link type '{link_type_id}' not found.")

    lt = DB["issue_link_types"].get(link_type_id)
    return {"issueLinkType": lt}