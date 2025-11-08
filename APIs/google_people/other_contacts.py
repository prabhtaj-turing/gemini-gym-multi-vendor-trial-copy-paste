"""
Google People API - Other Contacts Resource

This module provides simulation of the Google People API other contacts resource methods.
It handles other contacts (non-Google contacts) management and operations.

The Google People API Other Contacts allow you to:
- Get individual other contacts by resource name
- List all other contacts in the authenticated user's contacts
- Search through other contacts using plain-text queries
- Access contact information from non-Google sources

Other contacts are contacts that are not stored in Google's contact system but are
accessible through the user's account (e.g., from email clients, imported contacts, etc.).

For more information, see: https://developers.google.com/people/api/rest/v1/otherContacts
"""

from common_utils.tool_spec_decorator import tool_spec
import logging
from typing import Dict, List, Optional, Any

from .SimulationEngine.db import DB
from .SimulationEngine.utils import generate_id
from google_people.SimulationEngine.models import (
    GetOtherContactRequest, ListOtherContactsRequest, SearchOtherContactsRequest,
    GetOtherContactResponse, ListOtherContactsResponse, SearchOtherContactsResponse
)

logger = logging.getLogger(__name__)


@tool_spec(
    spec={
        'name': 'get_other_contact',
        'description': """ Get a single other contact by resource name.
        
        This method retrieves a specific other contact from the user's contacts using their resource name.
        Other contacts are contacts that are not stored in Google's contact system but are accessible
        through the user's account (e.g., from email clients, imported contacts, etc.). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the other contact to retrieve. Must start with "otherContacts/".
                    Example: "otherContacts/123456789" """
                },
                'read_mask': {
                    'type': 'string',
                    'description': """ A field mask to restrict which fields on each person are returned.
                    Valid fields: names, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. If not specified, all fields are returned. """
                },
                'sources': {
                    'type': 'array',
                    'description': """ List of sources to retrieve data from. Valid sources include
                    "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                    "READ_SOURCE_TYPE_DOMAIN_PROFILE", "READ_SOURCE_TYPE_DIRECTORY". """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'resource_name'
            ]
        }
    }
)
def get_other_contact(resource_name: str, read_mask: Optional[str] = None,
                      sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get a single other contact by resource name.
    
    This method retrieves a specific other contact from the user's contacts using their resource name.
    Other contacts are contacts that are not stored in Google's contact system but are accessible
    through the user's account (e.g., from email clients, imported contacts, etc.).
    
    Args:
        resource_name (str): The resource name of the other contact to retrieve. Must start with "otherContacts/".
                            Example: "otherContacts/123456789"
        read_mask (Optional[str]): A field mask to restrict which fields on each person are returned.
                                  Valid fields: names, emailAddresses, phoneNumbers, addresses,
                                  organizations, birthdays, photos, urls, userDefined, resourceName,
                                  etag, created, updated. If not specified, all fields are returned.
        sources (Optional[List[str]]): List of sources to retrieve data from. Valid sources include
                                      "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                                      "READ_SOURCE_TYPE_DOMAIN_PROFILE", "READ_SOURCE_TYPE_DIRECTORY".
    
    Returns:
        Dict[str, Any]: A dictionary containing the other contact data with the following structure:
            {
                "resourceName": "otherContacts/123456789",
                "etag": "etag_123456789",
                "names": [...],
                "emailAddresses": [...],
                "phoneNumbers": [...],
                "addresses": [...],
                "organizations": [...],
                "birthdays": [...],
                "photos": [...],
                "urls": [...],
                "userDefined": [...],
                "created": "2023-01-15T10:30:00Z",
                "updated": "2024-01-15T14:20:00Z"
            }
    
    Raises:
        ValueError: If the resource name is invalid or the other contact is not found.
    

    """
    # Validate input using Pydantic model
    request = GetOtherContactRequest(
        resource_name=resource_name,
        read_mask=read_mask,
        sources=sources
    )
    
    logger.info(f"Getting other contact with resource name: {request.resource_name}")

    db = DB
    other_contacts_data = db.get("otherContacts", {})

    if request.resource_name not in other_contacts_data:
        raise ValueError(f"Other contact with resource name '{request.resource_name}' not found")

    other_contact = other_contacts_data[request.resource_name].copy()

    # Filter by read_mask if specified
    if request.read_mask:
        mask_fields = [field.strip() for field in request.read_mask.split(",")]
        filtered_contact = {}
        for field in mask_fields:
            if field in other_contact:
                filtered_contact[field] = other_contact[field]
        other_contact = filtered_contact

    response_data = {
        "resourceName": request.resource_name,
        "etag": other_contact.get("etag", "etag123"),
        **other_contact
    }
    
    return response_data


@tool_spec(
    spec={
        'name': 'list_other_contacts',
        'description': """ List other contacts in the authenticated user's contacts.
        
        This method retrieves a list of all other contacts in the authenticated user's contacts.
        Other contacts are contacts that are not stored in Google's contact system but are accessible
        through the user's account (e.g., from email clients, imported contacts, etc.).
        The response can be paginated and supports field filtering. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'read_mask': {
                    'type': 'string',
                    'description': """ A field mask to restrict which fields on each person are returned.
                    Valid fields: names, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. If not specified, all fields are returned. """
                },
                'page_size': {
                    'type': 'integer',
                    'description': """ The number of other contacts to include in the response.
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
                'request_sync_token': {
                    'type': 'boolean',
                    'description': """ Whether the response should include a sync token.
                    Defaults to False. """
                }
            },
            'required': []
        }
    }
)
def list_other_contacts(read_mask: Optional[str] = None, page_size: Optional[int] = None,
                        page_token: Optional[str] = None, sync_token: Optional[str] = None,
                        request_sync_token: Optional[bool] = None) -> Dict[str, Any]:
    """
    List other contacts in the authenticated user's contacts.
    
    This method retrieves a list of all other contacts in the authenticated user's contacts.
    Other contacts are contacts that are not stored in Google's contact system but are accessible
    through the user's account (e.g., from email clients, imported contacts, etc.).
    The response can be paginated and supports field filtering.
    
    Args:
        read_mask (Optional[str]): A field mask to restrict which fields on each person are returned.
                                  Valid fields: names, emailAddresses, phoneNumbers, addresses,
                                  organizations, birthdays, photos, urls, userDefined, resourceName,
                                  etag, created, updated. If not specified, all fields are returned.
        page_size (Optional[int]): The number of other contacts to include in the response.
                                  Must be between 1 and 1000. Defaults to 100.
        page_token (Optional[str]): A page token, received from a previous response.
                                   Used for pagination.
        sync_token (Optional[str]): A sync token, received from a previous response.
                                   Used for incremental sync.
        request_sync_token (Optional[bool]): Whether the response should include a sync token.
                                            Defaults to False.
    
    Returns:
        Dict[str, Any]: A dictionary containing the list of other contacts with the following structure:
            {
                "otherContacts": [
                    {
                        "resourceName": "otherContacts/123456789",
                        "etag": "etag_123456789",
                        "names": [...],
                        "emailAddresses": [...],
                        "phoneNumbers": [...],
                        "addresses": [...],
                        "organizations": [...],
                        "birthdays": [...],
                        "photos": [...],
                        "urls": [...],
                        "userDefined": [...],
                        "created": "2023-01-15T10:30:00Z",
                        "updated": "2024-01-15T14:20:00Z"
                    }
                ],
                "nextPageToken": "next_page_token_string",
                "totalItems": 50,
                "nextSyncToken": "sync_token_string"
            }
    
    Raises:
        ValueError: If read_mask is not provided or parameters are invalid.
    

    """
    # Validate input using Pydantic model
    request = ListOtherContactsRequest(
        read_mask=read_mask,
        page_size=page_size,
        page_token=page_token,
        sync_token=sync_token,
        request_sync_token=request_sync_token
    )
    
    logger.info("Listing other contacts")

    if not request.read_mask:
        raise ValueError("read_mask is required for list_other_contacts")

    db = DB
    other_contacts_data = db.get("otherContacts", {})

    # Convert to list
    contacts = list(other_contacts_data.values())

    # Filter by read_mask
    mask_fields = [field.strip() for field in request.read_mask.split(",")]
    filtered_contacts = []
    for contact in contacts:
        filtered_contact = {}
        for field in mask_fields:
            if field in contact:
                filtered_contact[field] = contact[field]
        filtered_contacts.append(filtered_contact)

    # Apply pagination
    if request.page_size:
        start_index = 0
        if request.page_token:
            try:
                start_index = int(request.page_token)
            except ValueError:
                start_index = 0

        end_index = start_index + request.page_size
        filtered_contacts = filtered_contacts[start_index:end_index]

        next_page_token = str(end_index) if end_index < len(other_contacts_data) else None
    else:
        next_page_token = None

    response_data = {
        "otherContacts": filtered_contacts,
        "nextPageToken": next_page_token,
        "totalItems": len(filtered_contacts)
    }

    # Add sync token if requested
    if request.request_sync_token:
        response_data["nextSyncToken"] = f"sync_{generate_id()}"

    # Validate response using Pydantic model
    response = ListOtherContactsResponse(**response_data)
    return response.dict(by_alias=True)


@tool_spec(
    spec={
        'name': 'search_other_contacts',
        'description': """ Search for other contacts in the authenticated user's contacts.
        
        This method searches through the authenticated user's other contacts using a plain-text query.
        Other contacts are contacts that are not stored in Google's contact system but are accessible
        through the user's account (e.g., from email clients, imported contacts, etc.).
        The search is performed across names, email addresses, and other contact information. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The plain-text query for the request. Must not be empty and cannot exceed 1000 characters.
                    The search is case-insensitive and performs partial matching. """
                },
                'read_mask': {
                    'type': 'string',
                    'description': """ A field mask to restrict which fields on each person are returned.
                    Valid fields: names, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. If not specified, all fields are returned. """
                },
                'page_size': {
                    'type': 'integer',
                    'description': """ The number of other contacts to include in the response.
                    Must be between 1 and 1000. Defaults to 100. """
                },
                'page_token': {
                    'type': 'string',
                    'description': """ A page token, received from a previous response.
                    Used for pagination. """
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_other_contacts(query: str, read_mask: Optional[str] = None,
                          page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for other contacts in the authenticated user's contacts.
    
    This method searches through the authenticated user's other contacts using a plain-text query.
    Other contacts are contacts that are not stored in Google's contact system but are accessible
    through the user's account (e.g., from email clients, imported contacts, etc.).
    The search is performed across names, email addresses, and other contact information.
    
    Args:
        query (str): The plain-text query for the request. Must not be empty and cannot exceed 1000 characters.
                     The search is case-insensitive and performs partial matching.
        read_mask (Optional[str]): A field mask to restrict which fields on each person are returned.
                                  Valid fields: names, emailAddresses, phoneNumbers, addresses,
                                  organizations, birthdays, photos, urls, userDefined, resourceName,
                                  etag, created, updated. If not specified, all fields are returned.
        page_size (Optional[int]): The number of other contacts to include in the response.
                                  Must be between 1 and 1000. Defaults to 100.
        page_token (Optional[str]): A page token, received from a previous response.
                                   Used for pagination.
    
    Returns:
        Dict[str, Any]: A dictionary containing the search results with the following structure:
            {
                "results": [
                    {
                        "resourceName": "otherContacts/123456789",
                        "etag": "etag_123456789",
                        "names": [...],
                        "emailAddresses": [...],
                        "phoneNumbers": [...],
                        "addresses": [...],
                        "organizations": [...],
                        "birthdays": [...],
                        "photos": [...],
                        "urls": [...],
                        "userDefined": [...],
                        "created": "2023-01-15T10:30:00Z",
                        "updated": "2024-01-15T14:20:00Z"
                    }
                ],
                "nextPageToken": "next_page_token_string",
                "totalItems": 5
            }
    
    Raises:
        ValueError: If the query is empty or read_mask is not provided.
    

    """
    # Validate input using Pydantic model
    request = SearchOtherContactsRequest(
        query=query,
        read_mask=read_mask,
        page_size=page_size,
        page_token=page_token
    )
    
    logger.info(f"Searching other contacts with query: {request.query}")

    if not request.read_mask:
        raise ValueError("read_mask is required for search_other_contacts")

    db = DB
    other_contacts_data = db.get("otherContacts", {})

    # Simple search implementation
    results = []
    query_lower = request.query.lower()

    for contact_id, contact in other_contacts_data.items():
        # Search in names
        for name in contact.get("names", []):
            display_name = name.get("displayName", "").lower()
            given_name = name.get("givenName", "").lower()
            family_name = name.get("familyName", "").lower()
            if (query_lower in display_name or 
                query_lower in given_name or 
                query_lower in family_name):
                results.append(contact)
                break

        # Search in email addresses
        for email in contact.get("emailAddresses", []):
            email_value = email.get("value", "").lower()
            if query_lower in email_value:
                results.append(contact)
                break

        # Search in organizations
        for org in contact.get("organizations", []):
            org_name = org.get("name", "").lower()
            org_title = org.get("title", "").lower()
            if query_lower in org_name or query_lower in org_title:
                results.append(contact)
                break

    # Remove duplicates
    unique_results = []
    seen_ids = set()
    for contact in results:
        if contact["resourceName"] not in seen_ids:
            unique_results.append(contact)
            seen_ids.add(contact["resourceName"])

    # Filter by read_mask
    mask_fields = [field.strip() for field in request.read_mask.split(",")]
    filtered_results = []
    for contact in unique_results:
        filtered_contact = {}
        for field in mask_fields:
            if field in contact:
                filtered_contact[field] = contact[field]
        filtered_results.append(filtered_contact)

    # Apply pagination
    if request.page_size:
        start_index = 0
        if request.page_token:
            try:
                start_index = int(request.page_token)
            except ValueError:
                start_index = 0

        end_index = start_index + request.page_size
        filtered_results = filtered_results[start_index:end_index]

        next_page_token = str(end_index) if end_index < len(unique_results) else None
    else:
        next_page_token = None

    response_data = {
        "results": filtered_results,
        "nextPageToken": next_page_token,
        "totalItems": len(filtered_results)
    }

    # Validate response using Pydantic model
    response = SearchOtherContactsResponse(**response_data)
    return response.dict(by_alias=True)
