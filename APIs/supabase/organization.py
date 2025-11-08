"""Defines Supabase organization-related functions."""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any

from .SimulationEngine.db import DB
from .SimulationEngine import models
from .SimulationEngine import utils
from .SimulationEngine import custom_errors
from pydantic import ValidationError as PydanticValidationError


@tool_spec(
    spec={
        'name': 'list_organizations',
        'description': """ Lists all organizations that the user is a member of.
        
        This function retrieves a list of all organizations of which the user is a member. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_organizations() -> List[Dict[str, str]]:
    """Lists all organizations that the user is a member of.

    This function retrieves a list of all organizations of which the user is a member.

    Returns:
        List[Dict[str, str]]: A list of dictionaries,
            where each dictionary represents an organization the user is a member of.
            Each organization dictionary contains the following keys:
            id (str): The unique identifier for the organization.
            name (str): The name of the organization.
    """
    # Retrieve the list of organization dictionaries from the DB.
    # If 'organizations' key is not found in DB, default to an empty list.
    organizations_from_db: List[Dict[str, Any]] = DB.get('organizations', [])

    result_org_list: List[Dict[str, Any]] = []
    for org_in_db in organizations_from_db:
        # Extract only the required fields from each organization dictionary
        result_org_list.append({
            "id": org_in_db["id"],
            "name": org_in_db["name"]
        })

    return result_org_list

@tool_spec(
    spec={
        'name': 'get_organization',
        'description': """ Gets details for an organization. Includes subscription plan.
        
        Gets details for an organization. Includes subscription plan. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The organization ID.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_organization(id: str) -> Dict[str, Any]:
    """Gets details for an organization. Includes subscription plan.

    Gets details for an organization. Includes subscription plan.

    Args:
        id (str): The organization ID.

    Returns:
        Dict[str, Any]: Organization details including:
            id (str): The unique identifier for the organization.
            name (str): The name of the organization.
            created_at (str): ISO 8601 timestamp of when the organization was created.
            plan (str): The plan of the organization.
            opt_in_tags (List[str]): The opt-in tags of the organization.
            allowed_release_channels (List[str]): The allowed release channels of the organization.

    Raises:
        NotFoundError: If the organization with the specified ID does not exist.
        ValidationError: If input arguments fail validation.
    """
    if not id:
        raise custom_errors.ValidationError('The id parameter can not be null or empty')

    if not isinstance(id, str):
        raise custom_errors.ValidationError('id must be string type')
    
    organizations = utils.get_main_entities(DB, "organizations")
    organization = utils.get_entity_by_id(organizations, id)
    
    if not organization:
        raise custom_errors.NotFoundError(f"No organization found against this id: {id}")
    
    try: 
        organization_details_response = organization.copy()
        organization_details_response = models.Organization(**organization_details_response).model_dump()
    except PydanticValidationError as e: 
        raise custom_errors.ValidationError(f"Invalid Structure for return data: {e}")
    
    return organization_details_response
