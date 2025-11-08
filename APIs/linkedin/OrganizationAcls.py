from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, Union, List
from .SimulationEngine.db import DB
from .SimulationEngine.models import GetOrganizationAclsParams, OrganizationAcl, \
OrganizationAclDataModel, AclIdModel
from .SimulationEngine.custom_errors import (
    InvalidAclIdError,
    InvalidAclDataError,
    AclNotFoundError,
    GetAclsValidationError,
    InvalidQueryFieldError,
)
from pydantic import ValidationError

"""
API simulation for the '/organizationAcls' resource.
"""


@tool_spec(
    spec={
        'name': 'get_organization_acls_by_role_assignee',
        'description': 'Retrieves ACL records by roleAssignee URN with optional field projection and pagination. Retrieve information about the roles and permissions that a specific LinkedIn member (the "role assignee") has within one or more organizations on LinkedIn',
        'parameters': {
            'type': 'object',
            'properties': {
                'query_field': {
                    'type': 'string',
                    'description': "Query parameter expected to be 'roleAssignee'."
                },
                'role_assignee': {
                    'type': 'string',
                    'description': 'URN of the person whose ACL records are requested.'
                },
                'projection': {
                    'type': 'string',
                    'description': """ Field projection syntax for controlling which fields to return.
                    The projection string should consist of comma-separated field names and may optionally
                    be enclosed in parentheses. Defaults to None. """
                },
                'start': {
                    'type': 'integer',
                    'description': 'Starting index for pagination. Defaults to 0.'
                },
                'count': {
                    'type': 'integer',
                    'description': 'Number of items to return. Defaults to 10.'
                }
            },
            'required': [
                'query_field',
                'role_assignee'
            ]
        }
    }
)
def get_organization_acls_by_role_assignee(query_field: str,
                                            role_assignee: str,
                                            projection: Optional[str] = None,
                                            start: Optional[int] = 0,
                                            count: Optional[int] = 10) -> Dict[str, Any]:
    """
    Retrieves ACL records by roleAssignee URN with optional field projection and pagination. Retrieve information about the roles and permissions that a specific LinkedIn member (the "role assignee") has within one or more organizations on LinkedIn

    Args:
        query_field (str): Query parameter expected to be 'roleAssignee'.
        role_assignee (str): URN of the person whose ACL records are requested.
        projection (Optional[str]): Field projection syntax for controlling which fields to return.
            The projection string should consist of comma-separated field names and may optionally
            be enclosed in parentheses. Defaults to None.
        start (Optional[int]): Starting index for pagination. Defaults to 0.
        count (Optional[int]): Number of items to return. Defaults to 10.

    Returns:
        Dict[str, Any]:
        - On successful retrieval, returns a dictionary with the following keys and value types:
            - 'data' (List[Dict[str, Any]]): List of ACL record dictionaries with keys:
                - 'aclId' (str): ACL record's unique identifier.
                - 'roleAssignee' (str): URN of the person assigned the role (e.g., 'urn:li:person:1').
                - 'role' (str): Role assigned to the person (one of 'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER', 'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST', 'CURATOR', 'CONTENT_ADMINISTRATOR').
                - 'organization' (str): URN of the organization (e.g., 'urn:li:organization:1').
                - 'state' (str): Current state of the ACL (one of 'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED').

    Raises:
        InvalidQueryFieldError: If the query_field is not 'roleAssignee'.
        GetAclsValidationError: If any of the other input parameters are invalid.
    """
    if query_field != "roleAssignee":
        raise InvalidQueryFieldError("Invalid query parameter. Expected 'roleAssignee'.")
    try:
        params = GetOrganizationAclsParams(
            query_field=query_field,
            role_assignee=role_assignee,
            projection=projection,
            start=start,
            count=count,
        )
    except ValidationError as e:
        raise GetAclsValidationError(str(e))

    results = [
        OrganizationAcl(**acl)
        for acl in DB["organizationAcls"].values()
        if acl.get("roleAssignee") == params.role_assignee
    ]

    projected_results: List[Dict[str, Any]] = []
    if params.projection:
        fields_to_include = {
            field.strip()
            for field in params.projection.replace("(", "").replace(")", "").split(",")
        }
        for result in results:
            projected_result = result.model_dump(include=fields_to_include)
            projected_results.append(projected_result)
    else:
        projected_results = [result.model_dump() for result in results]

    paginated = projected_results[params.start : params.start + params.count]
    return {"data": paginated}

@tool_spec(
    spec={
        'name': 'create_organization_acl',
        'description': 'Creates a new organization ACL record in the database.',
        'parameters': {
            'type': 'object',
            'properties': {
                'acl_data': {
                    'type': 'object',
                    'description': 'Dictionary for the new organization ACL record, including details about the role, assignee, and initial state. It should include the following keys:',
                    'properties': {
                        'roleAssignee': {
                            'type': 'string',
                            'description': "URN of the person to assign the role to (e.g., 'urn:li:person:1')."
                        },
                        'role': {
                            'type': 'string',
                            'description': "Role to assign to the person (one of 'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER', 'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST', 'CURATOR', 'CONTENT_ADMINISTRATOR')."
                        },
                        'organization': {
                            'type': 'string',
                            'description': "URN of the organization (e.g., 'urn:li:organization:1')."
                        },
                        'state': {
                            'type': 'string',
                            'description': "Initial state of the ACL (one of 'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED')."
                        }
                    },
                    'required': [
                        'roleAssignee',
                        'role',
                        'organization',
                        'state'
                    ]
                }
            },
            'required': [
                'acl_data'
            ]
        }
    }
)
def create_organization_acl(acl_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new organization ACL record in the database.

    Args:
        acl_data (Dict[str, Any]): Dictionary for the new organization ACL record, including details about the role, assignee, and initial state. It should include the following keys:
            - 'roleAssignee' (str): URN of the person to assign the role to (e.g., 'urn:li:person:1').
            - 'role' (str): Role to assign to the person (one of 'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER', 'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST', 'CURATOR', 'CONTENT_ADMINISTRATOR').
            - 'organization' (str): URN of the organization (e.g., 'urn:li:organization:1').
            - 'state' (str): Initial state of the ACL (one of 'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED').

    Returns:
        Dict[str, Any]:
        - On successful creation, returns a dictionary with the following keys and value types:
            - 'data' (Dict[str, Any]): Dictionary representing the new ACL record to be created in the database.:
                - 'aclId' (str): Newly assigned unique identifier.
                - 'roleAssignee' (str): URN of the person assigned the role (e.g., 'urn:li:person:1').
                - 'role' (str): Role assigned to the person (one of 'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER', 'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST', 'CURATOR', 'CONTENT_ADMINISTRATOR').
                - 'organization' (str): URN of the organization (e.g., 'urn:li:organization:1').
                - 'state' (str): Current state of the ACL (one of 'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED').

    Raises:
        InvalidAclDataError: If input validation fails.
    """
    if not isinstance(acl_data, dict):
        raise InvalidAclDataError("Invalid ACL data provided: Input should be a valid dictionary")
    try:
        validated_data = OrganizationAclDataModel(**acl_data)
    except (ValidationError, TypeError) as e:
        raise InvalidAclDataError(f"Invalid ACL data provided: {e}")

    acl_id = str(DB["next_acl_id"])
    DB["next_acl_id"] += 1
    
    # Create a new dictionary instead of modifying the input parameter
    acl_data_with_id = validated_data.model_dump()
    acl_data_with_id["aclId"] = acl_id
    
    DB["organizationAcls"][acl_id] = acl_data_with_id
    return {"data": acl_data_with_id}

@tool_spec(
    spec={
        'name': 'update_organization_acl',
        'description': 'Updates an existing organization ACL record in the database.',
        'parameters': {
            'type': 'object',
            'properties': {
                'acl_id': {
                    'type': 'string',
                    'description': 'Unique identifier of the ACL record to update.'
                },
                'acl_data': {
                    'type': 'object',
                    'description': 'Dictionary representing the updated ACL record to be updated in the database:',
                    'properties': {
                        'roleAssignee': {
                            'type': 'string',
                            'description': "Updated URN of the person assigned the role (e.g., 'urn:li:person:1')."
                        },
                        'role': {
                            'type': 'string',
                            'description': "Updated role assigned to the person (one of 'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER', 'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST', 'CURATOR', 'CONTENT_ADMINISTRATOR')."
                        },
                        'organization': {
                            'type': 'string',
                            'description': "Updated URN of the organization (e.g., 'urn:li:organization:1')."
                        },
                        'state': {
                            'type': 'string',
                            'description': "Updated state of the ACL (one of 'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED')."
                        }
                    },
                    'required': [
                        'roleAssignee',
                        'role',
                        'organization',
                        'state'
                    ]
                }
            },
            'required': [
                'acl_id',
                'acl_data'
            ]
        }
    }
)
def update_organization_acl(acl_id: str,
                            acl_data: Dict[str, str]) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Updates an existing organization ACL record in the database.

    Args:
        acl_id (str): Unique identifier of the ACL record to update. Must be non-empty string.
        acl_data (Dict[str, str]):  Dictionary representing the updated ACL record to be updated in the database:
            - 'roleAssignee' (str): Updated URN of the person assigned the role (e.g., 'urn:li:person:1').
            - 'role' (str): Updated role assigned to the person (one of 'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER', 'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST', 'CURATOR', 'CONTENT_ADMINISTRATOR').
            - 'organization' (str): Updated URN of the organization (e.g., 'urn:li:organization:1').
            - 'state' (str): Updated state of the ACL (one of 'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED').

    Returns:
        Dict[str, Union[str, Dict[str, str]]]:
        - On successful update, returns a dictionary with the following keys and value types:
            - 'data' (Dict[str, str]): Dictionary of updated ACL record with keys:
                - 'aclId' (str): ACL record's unique identifier.
                - 'roleAssignee' (str): Updated URN of the person assigned the role (e.g., 'urn:li:person:1').
                - 'role' (str): Updated role assigned to the person (one of 'ADMINISTRATOR', 'DIRECT_SPONSORED_CONTENT_POSTER', 'RECRUITING_POSTER', 'LEAD_CAPTURE_ADMINISTRATOR', 'LEAD_GEN_FORMS_MANAGER', 'ANALYST', 'CURATOR', 'CONTENT_ADMINISTRATOR').
                - 'organization' (str): Updated URN of the organization (e.g., 'urn:li:organization:1').
                - 'state' (str): Updated state of the ACL (one of 'ACTIVE', 'REQUESTED', 'REJECTED', 'REVOKED').

    Raises:
        InvalidAclIdError: If the ACL ID is invalid (empty, whitespace, or wrong type).
        InvalidAclDataError: If the ACL data validation fails
        AclNotFoundError: If the ACL record is not found in the database.
        
    """
    # Validate acl_id
    try:
        validated_acl_id = AclIdModel(acl_id=acl_id)
        acl_id = validated_acl_id.acl_id
    except ValidationError as e:
        raise InvalidAclIdError(f"Invalid ACL ID: {e}")
    
    # Validate acl_data
    try:
        validated_acl_data = OrganizationAclDataModel(**acl_data)
    except (ValidationError, TypeError) as e:
        raise InvalidAclDataError(f"Invalid ACL data: {e}")
    
    # Check if ACL record exists
    if acl_id not in DB["organizationAcls"]:
        raise AclNotFoundError("ACL record not found.")
    
    # Convert validated data back to dict and add acl_id
    acl_data_dict = validated_acl_data.model_dump()
    acl_data_dict["aclId"] = acl_id
    
    # Update the record in database
    DB["organizationAcls"][acl_id] = acl_data_dict
    
    return {"data": acl_data_dict}

@tool_spec(
    spec={
        'name': 'delete_organization_acl',
        'description': 'Deletes an organization ACL record from the database.',
        'parameters': {
            'type': 'object',
            'properties': {
                'acl_id': {
                    'type': 'string',
                    'description': 'Unique identifier of the ACL record to delete.'
                }
            },
            'required': [
                'acl_id'
            ]
        }
    }
)
def delete_organization_acl(acl_id: str) -> Dict[str, Any]:
    """
    Deletes an organization ACL record from the database.

    Args:
        acl_id (str): Unique identifier of the ACL record to delete. Must be a non-empty string.

    Returns:
        Dict[str, Any]:
        - On successful deletion, returns a dictionary with the following keys and value types:
            - 'status' (str): Success message confirming deletion of the ACL record.

    Raises:
        InvalidAclIdError: If 'acl_id' is not a non-empty string.
        AclNotFoundError: If the ACL record is not found in the database.
    """
    # --- Input Validation Start ---
    if not isinstance(acl_id, str) or not acl_id.strip():
        raise InvalidAclIdError(f"Argument 'acl_id' must be a non-empty string, but got {type(acl_id).__name__}.")
    # --- Input Validation End ---
    
    if acl_id not in DB["organizationAcls"]:
        raise AclNotFoundError(f"ACL record with ID {acl_id} not found.")
    del DB["organizationAcls"][acl_id]
    return {"status": f"ACL {acl_id} deleted."}