from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/IssueLinkApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.models import IssueLinkCreationInput
from .SimulationEngine.custom_errors import IssueNotFoundError
from typing import Dict, Any
from pydantic import ValidationError
import re


@tool_spec(
    spec={
        'name': 'create_issue_link',
        'description': """ Create a new issue link in Jira.
        
        This method creates a new issue link between two issues. The link will be
        assigned a unique ID and stored in the system. Both issues must exist in
        the database for the link to be created successfully. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'type': {
                    'type': 'string',
                    'description': """ The type of issue link to create. Must be a non-empty string. 
                    Valid types are: 'Blocks', 'Duplicates'. """
                },
                'inwardIssue': {
                    'type': 'object',
                    'description': 'The inward issue reference containing:',
                    'properties': {
                        'key': {
                            'type': 'string',
                            'description': 'The key of the inward issue. Must be a non-empty string.'
                        }
                    },
                    'required': [
                        'key'
                    ]
                },
                'outwardIssue': {
                    'type': 'object',
                    'description': 'The outward issue reference containing:',
                    'properties': {
                        'key': {
                            'type': 'string',
                            'description': 'The key of the outward issue. Must be a non-empty string.'
                        }
                    },
                    'required': [
                        'key'
                    ]
                }
            },
            'required': [
                'type',
                'inwardIssue',
                'outwardIssue'
            ]
        }
    }
)
def create_issue_link(type: str, inwardIssue: Dict[str, Any], outwardIssue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new issue link in Jira.
    This method creates a new issue link between two issues. The link will be
    assigned a unique ID and stored in the system. Both issues must exist in
    the database for the link to be created successfully.

    Args:
        type (str): The type of issue link to create. Must be a non-empty string. 
            Valid types are: 'Blocks', 'Duplicates'.
        inwardIssue (Dict[str, Any]): The inward issue reference containing:
            - key (str): The key of the inward issue. Must be a non-empty string.
        outwardIssue (Dict[str, Any]): The outward issue reference containing:
            - key (str): The key of the outward issue. Must be a non-empty string.
    Returns:
        Dict[str, Any]: A dictionary containing the created issue link:
            - created (bool): Always True for successful creation
            - issueLink (Dict[str, Any]): The created issue link containing:
                - id (str): The unique ID of the issue link
                - type (str): The type of issue link
                - inwardIssue (Dict[str, Any]): The inward issue reference
                    - key (str): The key of the inward issue
                - outwardIssue (Dict[str, Any]): The outward issue reference
                    - key (str): The key of the outward issue
    Raises:
        ValidationError: If the input data structure is invalid according to the Pydantic model.
        ValueError: If the provided link type is not valid in the database.
        IssueNotFoundError: If either the inward or outward issue does not exist in the database.
        
    """
    # Input validation using Pydantic model
    try:
        validated_input = IssueLinkCreationInput(
        type=type,
        inwardIssue=inwardIssue,
        outwardIssue=outwardIssue
        )
    except ValidationError as e:
        raise e

    # Validate link type exists in database
    if validated_input.type not in DB.get("issue_link_types", {}):
        raise ValueError(f"Link type '{validated_input.type}' is not valid. Available types: {list(DB.get('issue_link_types', {}).keys())}")

    # Check if issues exist in the database
    inward_key = validated_input.inwardIssue.key
    outward_key = validated_input.outwardIssue.key

    if inward_key not in DB.get("issues", {}):
        raise IssueNotFoundError(f"Inward issue with key '{inward_key}' not found in database.")

    if outward_key not in DB.get("issues", {}):
        raise IssueNotFoundError(f"Outward issue with key '{outward_key}' not found in database.")

    # Generate unique link ID by finding max existing ID
    existing_links = DB.get('issue_links', [])
    max_id = 0
    for link in existing_links:
        match = re.match(r'LINK-(\d+)', link.get('id', ''))
        if match:
            max_id = max(max_id, int(match.group(1)))
    
    link_id = f"LINK-{max_id + 1}"

    # Create link data
    link_data = {
        "id": link_id,
        "type": validated_input.type,
        "inwardIssue": {"key": inward_key},
        "outwardIssue": {"key": outward_key},
    }

    # Ensure issue_links collection exists
    if "issue_links" not in DB:
        DB["issue_links"] = []

    # Store the link in the database
    DB["issue_links"].append(link_data)

    return {"created": True, "issueLink": link_data}