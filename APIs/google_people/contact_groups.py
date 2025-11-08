"""
Google People API - Contact Groups Resource

This module provides simulation of the Google People API contact groups resource methods.
It handles contact group management, creation, updates, and deletion.

The Google People API Contact Groups allow you to:
- Get, create, update, and delete contact groups
- List all contact groups owned by the authenticated user
- Modify group membership (add/remove contacts)
- Organize contacts into logical groups for easier management

Contact groups can be of two types:
- USER_CONTACT_GROUP: Groups created by the user
- SYSTEM_CONTACT_GROUP: System-created groups (like "My Contacts", "Starred", etc.)

For more information, see: https://developers.google.com/people/api/rest/v1/contactGroups
"""
from common_utils.tool_spec_decorator import tool_spec
import builtins
import logging
from datetime import datetime
from typing import Dict, Optional, Any

from .SimulationEngine.db import DB
from .SimulationEngine.utils import generate_id
from google_people.SimulationEngine.models import (
    GetContactGroupRequest, CreateContactGroupRequest, UpdateContactGroupRequest, DeleteContactGroupRequest,
    ListContactGroupsRequest, ModifyMembersRequest,
    ContactGroup, GetContactGroupResponse, CreateContactGroupResponse, UpdateContactGroupResponse,
    DeleteContactGroupResponse, ListContactGroupsResponse, ModifyMembersResponse
)

logger = logging.getLogger(__name__)


@tool_spec(
    spec={
        'name': 'get_contact_group',
        'description': """ Get a single contact group by resource name.
        
        This method retrieves a specific contact group from the user's Google Contacts.
        The resource name is a unique identifier that follows the format "contactGroups/{groupId}". """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the contact group to retrieve. Must start with "contactGroups/".
                    Example: "contactGroups/family" """
                },
                'max_members': {
                    'type': 'integer',
                    'description': """ The maximum number of members to return per group.
                    Must be between 1 and 1000. If not specified, all members are returned. """
                },
                'group_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of group fields to include in the response.
                    Valid fields: name, groupType, memberResourceNames, memberCount,
                    resourceName, etag, created, updated. If not specified, all fields are returned. """
                }
            },
            'required': [
                'resource_name'
            ]
        }
    }
)
def get(resource_name: str, max_members: Optional[int] = None,
        group_fields: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a single contact group by resource name.
    
    This method retrieves a specific contact group from the user's Google Contacts.
    The resource name is a unique identifier that follows the format "contactGroups/{groupId}".
    
    Args:
        resource_name (str): The resource name of the contact group to retrieve. Must start with "contactGroups/".
                            Example: "contactGroups/family"
        max_members (Optional[int]): The maximum number of members to return per group.
                                   Must be between 1 and 1000. If not specified, all members are returned.
        group_fields (Optional[str]): Comma-separated list of group fields to include in the response.
                                     Valid fields: name, groupType, memberResourceNames, memberCount,
                                     resourceName, etag, created, updated. If not specified, all fields are returned.
    
    Returns:
        Dict[str, Any]: A dictionary containing the contact group data with the following structure:
            {
                "resourceName": "contactGroups/family",
                "etag": "etag_family_group",
                "name": "Family",
                "groupType": "USER_CONTACT_GROUP",
                "memberResourceNames": ["people/123456789", "people/987654321"],
                "memberCount": 2,
                "created": "2023-01-20T08:00:00Z",
                "updated": "2024-01-10T16:30:00Z"
            }
    
    Raises:
        ValueError: If the resource name is invalid or the contact group is not found.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = GetContactGroupRequest(
        resource_name=resource_name,
        max_members=max_members,
        group_fields=group_fields
    )
    
    logger.info(f"Getting contact group with resource name: {request.resource_name}")

    db = DB
    contact_groups_data = db.get("contactGroups", {})

    if request.resource_name not in contact_groups_data:
        raise ValueError(f"Contact group with resource name '{request.resource_name}' not found")

    contact_group = contact_groups_data[request.resource_name].copy()

    # Limit members if max_members is specified
    if request.max_members and "memberResourceNames" in contact_group:
        contact_group["memberResourceNames"] = contact_group["memberResourceNames"][:request.max_members]

    # Filter by group_fields if specified
    if request.group_fields:
        field_list = [field.strip() for field in request.group_fields.split(",")]
        filtered_group = {}
        for field in field_list:
            if field in contact_group:
                filtered_group[field] = contact_group[field]
        contact_group = filtered_group

    response_data = {
        "resourceName": request.resource_name,
        "etag": contact_group.get("etag", "etag123"),
        **contact_group
    }
    
    # Validate response using Pydantic model
    return response_data


@tool_spec(
    spec={
        'name': 'create_contact_group',
        'description': """ Create a new contact group.
        
        This method creates a new contact group in the user's Google Contacts.
        The contact group must have a name. The resource name is automatically generated. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'contact_group_data': {
                    'type': 'object',
                    'description': 'Dictionary representing the contact group to be created, including its name and initial members." or "Details for the new contact group, specifying its name, type, and members.:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The name of the contact group (required)'
                        },
                        'groupType': {
                            'type': 'string',
                            'description': """ The type of contact group. Defaults to "USER_CONTACT_GROUP".
                                               Valid values: "USER_CONTACT_GROUP", "SYSTEM_CONTACT_GROUP" """
                        },
                        'memberResourceNames': {
                            'type': 'array',
                            'description': """ List of resource names of contacts to add to the group.
                                                               Each resource name must start with "people/". """,
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': [
                        'name'
                    ]
                }
            },
            'required': [
                'contact_group_data'
            ]
        }
    }
)
def create(contact_group_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new contact group.
    
    This method creates a new contact group in the user's Google Contacts.
    The contact group must have a name. The resource name is automatically generated.
    
    Args:
        contact_group_data (Dict[str, Any]): Dictionary representing the contact group to be created, including its name and initial members." or "Details for the new contact group, specifying its name, type, and members.:
            - name (str): The name of the contact group (required)
            - groupType (Optional[str]): The type of contact group. Defaults to "USER_CONTACT_GROUP".
                              Valid values: "USER_CONTACT_GROUP", "SYSTEM_CONTACT_GROUP"
            - memberResourceNames (Optional[List[str]]): List of resource names of contacts to add to the group.
                                              Each resource name must start with "people/".
    
    Returns:
        Dict[str, Any]: A dictionary containing the created contact group data with the following structure:
            {
                "resourceName": "contactGroups/123456789",
                "etag": "etag_123456789",
                "name": "Family",
                "groupType": "USER_CONTACT_GROUP",
                "memberResourceNames": ["people/123456789", "people/987654321"],
                "memberCount": 2,
                "created": "2024-01-15T10:30:00Z",
                "updated": "2024-01-15T10:30:00Z"
            }
    
    Raises:
        ValueError: If required fields are missing or invalid.
        ValidationError: If the input data fails validation.
    

    """
    # Validate input using Pydantic model
    contact_group = ContactGroup(**contact_group_data)
    request = CreateContactGroupRequest(contact_group_data=contact_group)
    
    logger.info("Creating new contact group")

    db = DB
    contact_groups_data = db.get("contactGroups", {})

    # Generate resource name
    resource_name = f"contactGroups/{generate_id()}"

    # Create contact group object
    contact_group_obj = {
        "resourceName": resource_name,
        "etag": f"etag_{generate_id()}",
        "name": request.contact_group_data.name,
        "groupType": request.contact_group_data.group_type or "USER_CONTACT_GROUP",
        "memberResourceNames": request.contact_group_data.member_resource_names or [],
        "memberCount": len(request.contact_group_data.member_resource_names or []),
        "created": datetime.now().isoformat() + "Z",
        "updated": datetime.now().isoformat() + "Z"
    }
    response = CreateContactGroupResponse(**contact_group_obj).model_dump(by_alias=True)
    contact_groups_data[resource_name] = response
    db.set("contactGroups", contact_groups_data)
    logger.info(f"Created contact group with resource name: {resource_name}")

    return response


@tool_spec(
    spec={
        'name': 'update_contact_group',
        'description': """ Update an existing contact group.
        
        This method updates an existing contact group in the user's Google Contacts.
        You can update all fields or specify only certain fields to update using the update_group_fields parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the contact group to update. Must start with "contactGroups/".
                    Example: "contactGroups/family" """
                },
                'contact_group_data': {
                    'type': 'object',
                    'description': """ Dictionary containing updated contact group information.
                    Only the fields you want to update need to be included.
                    Properties: """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The name of the contact group.'
                        },
                        'groupType': {
                            'type': 'string',
                            'description': """ The type of contact group.
                               Valid values: "USER_CONTACT_GROUP", "SYSTEM_CONTACT_GROUP". """
                        },
                        'memberResourceNames': {
                            'type': 'array',
                            'description': """ Resource names of contacts
                               in the group. Each must start with "people/". """,
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': []
                },
                'update_group_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of group fields to update.
                    If specified, only these fields will be updated.
                    If not specified, all provided fields will be updated.
                    Valid fields: name, groupType, memberResourceNames """
                }
            },
            'required': [
                'resource_name',
                'contact_group_data'
            ]
        }
    }
)
def update(resource_name: str, contact_group_data: Dict[str, Any],
           update_group_fields: Optional[str] = None) -> Dict[str, Any]:
    """
    Update an existing contact group.
    
    This method updates an existing contact group in the user's Google Contacts.
    You can update all fields or specify only certain fields to update using the update_group_fields parameter.
    
    Args:
        resource_name (str): The resource name of the contact group to update. Must start with "contactGroups/".
                            Example: "contactGroups/family"
        contact_group_data (Dict[str, Any]): Dictionary containing updated contact group information.
                                            Only the fields you want to update need to be included.
                                            Properties:
                                            - name (Optional[str]): The name of the contact group.
                                            - groupType (Optional[str]): The type of contact group.
                                              Valid values: "USER_CONTACT_GROUP", "SYSTEM_CONTACT_GROUP".
                                            - memberResourceNames (Optional[List[str]]): Resource names of contacts
                                              in the group. Each must start with "people/".
        update_group_fields (Optional[str]): Comma-separated list of group fields to update.
                                            If specified, only these fields will be updated.
                                            If not specified, all provided fields will be updated.
                                            Valid fields: name, groupType, memberResourceNames
    
    Returns:
        Dict[str, Any]: Updated contact group data with the following keys:
            - resourceName (str): Resource name of the contact group.
            - etag (str): Updated ETag for the group.
            - name (Optional[str]): Updated group name, if provided.
            - groupType (Optional[str]): Updated group type, if provided.
            - memberResourceNames (Optional[List[str]]): Updated member resource names, if provided.
            - memberCount (Optional[int]): Updated number of members, if applicable.
            - created (Optional[str]): Original creation timestamp, if present.
            - updated (str): Last update timestamp after this operation.
    
    Raises:
        ValueError: If the resource name is invalid or the contact group is not found.
        ValidationError: If the input parameters fail validation.
    
    Example:
        >>> update_data = {
        ...     "name": "Extended Family",
        ...     "memberResourceNames": ["people/123456789", "people/987654321", "people/555666777"]
        ... }
        >>> update("contactGroups/family", update_data, "name,memberResourceNames")
        {
            "resourceName": "contactGroups/family",
            "etag": "etag_updated_family",
            "name": "Extended Family",
            "groupType": "USER_CONTACT_GROUP",
            "memberResourceNames": ["people/123456789", "people/987654321", "people/555666777"],
            "memberCount": 3,
            "updated": "2024-01-15T14:20:00Z"
        }
    """
    # Validate input using Pydantic model
    contact_group = ContactGroup(**contact_group_data)
    request = UpdateContactGroupRequest(
        resource_name=resource_name,
        contact_group_data=contact_group,
        update_group_fields=update_group_fields
    )
    
    logger.info(f"Updating contact group with resource name: {request.resource_name}")

    db = DB
    contact_groups_data = db.get("contactGroups", {})

    if request.resource_name not in contact_groups_data:
        raise ValueError(f"Contact group with resource name '{request.resource_name}' not found")

    existing_group = contact_groups_data[request.resource_name]

    # Update only specified fields if update_group_fields is provided
    if request.update_group_fields:
        field_list = [field.strip() for field in request.update_group_fields.split(",")]
        for field in field_list:
            if hasattr(request.contact_group_data, field):
                field_value = getattr(request.contact_group_data, field)
                if field_value is not None:
                    existing_group[field] = field_value
    else:
        # Update all provided fields
        group_dict = request.contact_group_data.dict(exclude_unset=True, by_alias=True)
        existing_group.update(group_dict)

    # Update member count if memberResourceNames changed
    if request.contact_group_data.member_resource_names is not None:
        existing_group["memberCount"] = len(request.contact_group_data.member_resource_names)

    # Update timestamp
    existing_group["updated"] = datetime.now().isoformat() + "Z"
    existing_group["etag"] = f"etag_{generate_id()}"

    # Save to database
    contact_groups_data[request.resource_name] = existing_group
    db.set("contactGroups", contact_groups_data)

    logger.info(f"Updated contact group with resource name: {request.resource_name}")
    
    # Validate response using Pydantic model
    response = UpdateContactGroupResponse(**existing_group)
    return response.dict(by_alias=True)


@tool_spec(
    spec={
        'name': 'delete_contact_group',
        'description': """ Delete a contact group.
        
        This method permanently deletes a contact group from the user's Google Contacts.
        Optionally, it can also delete all contacts that are members of the group.
        The deletion cannot be undone. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the contact group to delete. Must start with "contactGroups/".
                    Example: "contactGroups/family" """
                },
                'delete_contacts': {
                    'type': 'boolean',
                    'description': """ Whether to delete the contacts in the group.
                    If True, all contacts that are members of the group will be deleted.
                    If False or None, only the group is deleted, contacts remain.
                    Defaults to False. """
                }
            },
            'required': [
                'resource_name'
            ]
        }
    }
)
def delete(resource_name: str, delete_contacts: Optional[bool] = None) -> Dict[str, Any]:
    """
    Delete a contact group.
    
    This method permanently deletes a contact group from the user's Google Contacts.
    Optionally, it can also delete all contacts that are members of the group.
    The deletion cannot be undone.
    
    Args:
        resource_name (str): The resource name of the contact group to delete. Must start with "contactGroups/".
                            Example: "contactGroups/family"
        delete_contacts (Optional[bool]): Whether to delete the contacts in the group.
                                        If True, all contacts that are members of the group will be deleted.
                                        If False or None, only the group is deleted, contacts remain.
                                        Defaults to False.
    
    Returns:
        Dict[str, Any]: A dictionary containing deletion confirmation with the following structure:
            {
                "success": True,
                "deletedResourceName": "contactGroups/family",
                "message": "Contact group deleted successfully",
                "deletedContacts": False
            }
    
    Raises:
        ValueError: If the resource name is invalid or the contact group is not found.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = DeleteContactGroupRequest(
        resource_name=resource_name,
        delete_contacts=delete_contacts
    )
    
    logger.info(f"Deleting contact group with resource name: {request.resource_name}")

    db = DB
    contact_groups_data = db.get("contactGroups", {})

    if request.resource_name not in contact_groups_data:
        raise ValueError(f"Contact group with resource name '{request.resource_name}' not found")

    contact_group = contact_groups_data[request.resource_name]

    # Delete contacts if requested
    if request.delete_contacts:
        people_data = db.get("people", {})
        for member_resource_name in contact_group.get("memberResourceNames", []):
            if member_resource_name in people_data:
                people_data.pop(member_resource_name)
        db.set("people", people_data)
        logger.info(f"Deleted {len(contact_group.get('memberResourceNames', []))} contacts from group")

    # Remove from database
    deleted_group = contact_groups_data.pop(request.resource_name)
    db.set("contactGroups", contact_groups_data)

    logger.info(f"Deleted contact group with resource name: {request.resource_name}")
    
    response_data = {
        "success": True,
        "deletedResourceName": request.resource_name,
        "message": "Contact group deleted successfully",
        "deletedContacts": request.delete_contacts or False
    }
    
    # Validate response using Pydantic model
    response = DeleteContactGroupResponse(**response_data)
    return response.dict(by_alias=True)


@tool_spec(
    spec={
        'name': 'list_contact_groups',
        'description': """ List all contact groups owned by the authenticated user.
        
        This method retrieves a list of all contact groups that the authenticated user owns.
        The response can be paginated and supports field filtering. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'page_size': {
                    'type': 'integer',
                    'description': """ The number of contact groups to include in the response.
                    Must be between 1 and 1000. Defaults to 100. """
                },
                'page_token': {
                    'type': 'string',
                    'description': """ A page token, received from a previous response.
                    Used for pagination. """
                },
                'sync_token': {
                    'type': 'string',
                    'description': """ A sync token, received from a previous response.
                    Used for incremental sync. """
                },
                'group_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of group fields to include in the response.
                    Valid fields: name, groupType, memberResourceNames, memberCount,
                    resourceName, etag, created, updated. If not specified, all fields are returned. """
                }
            },
            'required': []
        }
    }
)
def list(page_size: Optional[int] = None, page_token: Optional[str] = None,
         sync_token: Optional[str] = None, group_fields: Optional[str] = None) -> Dict[str, Any]:
    """
    List all contact groups owned by the authenticated user.
    
    This method retrieves a list of all contact groups that the authenticated user owns.
    The response can be paginated and supports field filtering.
    
    Args:
        page_size (Optional[int]): The number of contact groups to include in the response.
                                  Must be between 1 and 1000. Defaults to 100.
        page_token (Optional[str]): A page token, received from a previous response.
                                   Used for pagination.
        sync_token (Optional[str]): A sync token, received from a previous response.
                                   Used for incremental sync.
        group_fields (Optional[str]): Comma-separated list of group fields to include in the response.
                                     Valid fields: name, groupType, memberResourceNames, memberCount,
                                     resourceName, etag, created, updated. If not specified, all fields are returned.
    
    Returns:
        Dict[str, Any]: A dictionary containing the list of contact groups with the following structure:
            {
                "contactGroups": [
                    {
                        "resourceName": "contactGroups/family",
                        "etag": "etag_family_group",
                        "name": "Family",
                        "groupType": "USER_CONTACT_GROUP",
                        "memberResourceNames": ["people/123456789"],
                        "memberCount": 1,
                        "created": "2023-01-20T08:00:00Z",
                        "updated": "2024-01-10T16:30:00Z"
                    }
                ],
                "nextPageToken": "next_page_token_string",
                "nextSyncToken": "sync_token_string",
                "totalItems": 3
            }
    
    Raises:
        ValueError: If parameters are invalid.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = ListContactGroupsRequest(
        page_size=page_size,
        page_token=page_token,
        sync_token=sync_token,
        group_fields=group_fields
    )
    
    logger.info("Listing contact groups")

    db = DB
    contact_groups_data = db.get("contactGroups", {})

    # Convert to list
    groups = builtins.list(contact_groups_data.values())

    # Filter by group_fields if specified
    if request.group_fields:
        field_list = [field.strip() for field in request.group_fields.split(",")]
        filtered_groups = []
        for group in groups:
            filtered_group = {}
            for field in field_list:
                if field in group:
                    filtered_group[field] = group[field]
            filtered_groups.append(filtered_group)
        groups = filtered_groups

    # Apply pagination
    if request.page_size:
        start_index = 0
        if request.page_token:
            try:
                start_index = int(request.page_token)
            except ValueError:
                start_index = 0

        end_index = start_index + request.page_size
        groups = groups[start_index:end_index]

        next_page_token = str(end_index) if end_index < len(contact_groups_data) else None
    else:
        next_page_token = None

    response_data = {
        "contactGroups": groups,
        "nextPageToken": next_page_token,
        "nextSyncToken": f"sync_{generate_id()}",
        "totalItems": len(groups)
    }
    
    # Validate response using Pydantic model
    response = ListContactGroupsResponse(**response_data)
    return response.dict(by_alias=True)


@tool_spec(
    spec={
        'name': 'modify_contact_group_members',
        'description': """ Modify the members of a contact group.
        
        This method allows you to add or remove contacts from a contact group.
        You can specify which contacts to add and/or remove in a single request. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the contact group to modify. Must start with "contactGroups/".
                    Example: "contactGroups/family" """
                },
                'request_data': {
                    'type': 'object',
                    'description': """ Modification payload specifying which members to add or remove.
                    Properties: """,
                    'properties': {
                        'resourceNamesToAdd': {
                            'type': 'array',
                            'description': """ Resource names to add to the group. Each must start with "people/".
                               Example: ["people/123456789", "people/987654321"] """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'resourceNamesToRemove': {
                            'type': 'array',
                            'description': 'Resource names to remove from the group. Each must start with "people/".',
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'resource_name',
                'request_data'
            ]
        }
    }
)
def modify_members(resource_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modify the members of a contact group.
    
    This method allows you to add or remove contacts from a contact group.
    You can specify which contacts to add and/or remove in a single request.
    
    Args:
        resource_name (str): The resource name of the contact group to modify. Must start with "contactGroups/".
                            Example: "contactGroups/family"
        request_data (Dict[str, Any]): Modification payload specifying which members to add or remove.
            Properties:
            - resourceNamesToAdd (Optional[List[str]]): Resource names to add to the group. Each must start with "people/".
              Example: ["people/123456789", "people/987654321"]
            - resourceNamesToRemove (Optional[List[str]]): Resource names to remove from the group. Each must start with "people/".
    
    Returns:
        Dict[str, Any]: Modification result with the following keys:
            - resourceName (str): Resource name of the modified contact group.
            - etag (str): Updated ETag for the group.
            - memberCount (int): Number of members in the group after the modification.
            - notFoundResourceNames (List[str]): Resource names from resourceNamesToAdd that were not found.
    
    Raises:
        ValueError: If the resource name is invalid or the contact group is not found.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = ModifyMembersRequest(
        resource_name=resource_name,
        request_data=request_data
    )
    
    logger.info(f"Modifying members of contact group: {request.resource_name}")

    db = DB
    contact_groups_data = db.get("contactGroups", {})

    if request.resource_name not in contact_groups_data:
        raise ValueError(f"Contact group with resource name '{request.resource_name}' not found")

    contact_group = contact_groups_data[request.resource_name]

    # Get current members
    current_members = contact_group.get("memberResourceNames", [])

    # Apply modifications based on request_data
    not_found_resource_names = []
    
    # Add new members
    if "resourceNamesToAdd" in request.request_data:
        new_members = request.request_data["resourceNamesToAdd"]
        # Validate that the contacts exist
        people_data = db.get("people", {})
        for member in new_members:
            if member not in people_data:
                not_found_resource_names.append(member)
            elif member not in current_members:
                current_members.append(member)
        current_members = builtins.list(set(current_members))  # Remove duplicates

    # Remove members
    if "resourceNamesToRemove" in request.request_data:
        members_to_remove = request.request_data["resourceNamesToRemove"]
        current_members = [member for member in current_members if member not in members_to_remove]

    # Update the contact group
    contact_group["memberResourceNames"] = current_members
    contact_group["memberCount"] = len(current_members)
    contact_group["updated"] = datetime.now().isoformat() + "Z"
    contact_group["etag"] = f"etag_{generate_id()}"

    # Save to database
    contact_groups_data[request.resource_name] = contact_group
    db.set("contactGroups", contact_groups_data)

    logger.info(f"Modified contact group {request.resource_name} with {len(current_members)} members")
    
    response_data = {
        "resourceName": request.resource_name,
        "etag": contact_group["etag"],
        "memberCount": len(current_members),
        "notFoundResourceNames": not_found_resource_names
    }
    
    # Validate response using Pydantic model
    response = ModifyMembersResponse(**response_data)
    return response.dict(by_alias=True)
