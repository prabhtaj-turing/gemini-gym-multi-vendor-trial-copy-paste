"""
Google People API - People Resource

This module provides simulation of the Google People API people resource methods.
It handles contact management, profile operations, and contact information.

The Google People API allows you to:
- Get, create, update, and delete people contacts
- List and search through connections
- Batch retrieve multiple people
- Access directory people (for Google Workspace domains)
- Manage contact information including names, emails, phone numbers, addresses, etc.

For more information, see: https://developers.google.com/people/api/rest/v1/people
"""

from common_utils.tool_spec_decorator import tool_spec
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from .SimulationEngine.db import DB
from .SimulationEngine.utils import generate_id, sanitize_data_for_serialization
from google_people.SimulationEngine.models import (
    GetContactRequest, CreateContactRequest, UpdateContactRequest, DeleteContactRequest,
    ListConnectionsRequest, SearchPeopleRequest, BatchGetRequest,
    GetDirectoryPersonRequest, ListDirectoryPeopleRequest, SearchDirectoryPeopleRequest,
    Person, GetContactResponse, CreateContactResponse, UpdateContactResponse, DeleteContactResponse,
    ListConnectionsResponse, SearchPeopleResponse, BatchGetResponse,
    ListDirectoryPeopleResponse, SearchDirectoryPeopleResponse, PhoneType
)
from common_utils.phone_utils import normalize_phone_number

logger = logging.getLogger(__name__)


@tool_spec(
    spec={
        'name': 'get_contact',
        'description': """ Get a single person by resource name.
        
        This method retrieves a specific person from the user's contacts using their resource name.
        The resource name is a unique identifier that follows the format "people/{personId}". """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the person to retrieve. Must start with "people/".
                    Example: "people/123456789" """
                },
                'person_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of person fields to include in the response.
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
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
def get_contact(resource_name: str, person_fields: Optional[str] = None,
                sources: Optional[List[str]] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    Get a single person by resource name.
    
    This method retrieves a specific person from the user's contacts using their resource name.
    The resource name is a unique identifier that follows the format "people/{personId}".
    
    Args:
        resource_name (str): The resource name of the person to retrieve. Must start with "people/".
                            Example: "people/123456789"
        person_fields (Optional[str]): Comma-separated list of person fields to include in the response.
                                      Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                                      organizations, birthdays, photos, urls, userDefined, resourceName,
                                      etag, created, updated. If not specified, all fields are returned.
        sources (Optional[List[str]]): List of sources to retrieve data from. Valid sources include
                                      "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                                      "READ_SOURCE_TYPE_DOMAIN_PROFILE", "READ_SOURCE_TYPE_DIRECTORY".
    
    Returns:
        Dict[str, Union[str, List, Dict]]: Created person data with the following keys:
            - resourceName (str): Resource name of the newly created person (e.g., "people/123456789").
            - etag (str): ETag for the person record for versioning.
            - names (List[Dict]): List of name objects, each containing:
                - displayName (Optional[str]): Full display name
                - displayNameLastFirst (Optional[str]): Display name in last, first format
                - givenName (Optional[str]): First name
                - familyName (Optional[str]): Last name
                - middleName (Optional[str]): Middle name
                - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                - phoneticGivenName (Optional[str]): Phonetic first name
                - phoneticFamilyName (Optional[str]): Phonetic last name
                - phoneticMiddleName (Optional[str]): Phonetic middle name
                - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                - unstructuredName (Optional[str]): Unstructured name
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                - value (str): The nickname value
                - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - emailAddresses (List[Dict]): List of email address objects, each containing:
                - value (str): The email address
                - type (Optional[str]): Email type - "home", "work", "other"
                - displayName (Optional[str]): Display name for the email
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                - value (str): The phone number
                - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                - formattedType (Optional[str]): Human-readable type description
                - canonicalForm (Optional[str]): Canonical form of the phone number
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - addresses (Optional[List[Dict]]): List of address objects, each containing:
                - type (Optional[str]): Address type - "home", "work", "other"
                - formattedValue (Optional[str]): Full formatted address string
                - streetAddress (Optional[str]): Street address line
                - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                - city (Optional[str]): City name
                - region (Optional[str]): State/region name
                - postalCode (Optional[str]): ZIP/postal code
                - country (Optional[str]): Country name
                - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                - type (Optional[str]): Organization type - "work", "school", "other"
                - name (Optional[str]): Organization name
                - title (Optional[str]): Job title
                - department (Optional[str]): Department name
                - location (Optional[str]): Office location
                - jobDescription (Optional[str]): Job description
                - symbol (Optional[str]): Organization symbol/ticker
                - domain (Optional[str]): Organization domain
                - costCenter (Optional[str]): Cost center identifier
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                - date (Optional[Dict]): Date components with year, month, day keys
                    - year (Optional[int]): Year
                    - month (Optional[int]): Month (1-12)
                    - day (Optional[int]): Day (1-31)
                - text (Optional[str]): Text representation of birthday
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - photos (Optional[List[Dict]]): List of photo objects, each containing:
                - url (Optional[str]): URL of the photo
                - default (Optional[bool]): Whether this is the default photo
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - urls (Optional[List[Dict]]): List of URL objects, each containing:
                - value (str): The URL
                - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                - key (str): Field key/name
                - value (str): Field value
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - created (str): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z").
            - updated (str): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z").
    
    
    Raises:
        ValueError: If the resource name is invalid or the person is not found.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = GetContactRequest(
        resource_name=resource_name,
        person_fields=person_fields,
        sources=sources
    )
    
    logger.info(f"Getting person with resource name: {request.resource_name}")

    db = DB
    people_data = db.get("people", {})

    if request.resource_name not in people_data:
        raise ValueError(f"Person with resource name '{request.resource_name}' not found")

    person = people_data[request.resource_name].copy()

    # Filter by person_fields if specified
    if request.person_fields:
        field_list = [field.strip() for field in request.person_fields.split(",")]
        filtered_person = {}
        for field in field_list:
            if field in person:
                filtered_person[field] = person[field]
        person = filtered_person

    response_data = {
        "resourceName": request.resource_name,
        "etag": person.get("etag", "etag123"),
        **person
    }
    
    # Validate response using Pydantic model
    return response_data


@tool_spec(
    spec={
        'name': 'create_contact',
        'description': """ Create a new person contact.
        
        This method creates a new contact in the user's Google Contacts. The contact must have
        at least one name and one email address. The resource name is automatically generated. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'person_data': {
                    'type': 'object',
                    'description': 'Dictionary containing person information. Must include:',
                    'properties': {
                        'names': {
                            'type': 'array',
                            'description': 'At least one name object with displayName, givenName, or familyName',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'displayName': {'type': 'string', 'description': 'Full display name'},
                                    'displayNameLastFirst': {'type': 'string', 'description': 'Display name in last, first format'},
                                    'givenName': {'type': 'string', 'description': 'First name'},
                                    'familyName': {'type': 'string', 'description': 'Last name'},
                                    'middleName': {'type': 'string', 'description': 'Middle name'},
                                    'honorificPrefix': {'type': 'string', 'description': 'Title prefix (e.g., "Dr.", "Mr.")'},
                                    'honorificSuffix': {'type': 'string', 'description': 'Title suffix (e.g., "Jr.", "Sr.")'},
                                    'phoneticGivenName': {'type': 'string', 'description': 'Phonetic first name'},
                                    'phoneticFamilyName': {'type': 'string', 'description': 'Phonetic last name'},
                                    'phoneticMiddleName': {'type': 'string', 'description': 'Phonetic middle name'},
                                    'phoneticHonorificPrefix': {'type': 'string', 'description': 'Phonetic title prefix'},
                                    'phoneticHonorificSuffix': {'type': 'string', 'description': 'Phonetic title suffix'},
                                    'unstructuredName': {'type': 'string', 'description': 'Unstructured name'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'nicknames': {
                            'type': 'array',
                            'description': """ Nickname objects. Each item should include
                                            fields such as "value" and may include "type". """,
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {
                                        'type': 'string',
                                        'description': 'The nickname value'
                                    },
                                    'type': {
                                        'type': 'string',
                                        'description': 'The type of nickname (e.g., "DEFAULT", "ALTERNATE_NAME")'
                                    },
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': ['value']
                            }
                        },
                        'emailAddresses': {
                            'type': 'array',
                            'description': 'At least one email address object with value',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {'type': 'string', 'description': 'The email address (required)'},
                                    'type': {'type': 'string', 'description': 'Email type', 'enum': ['home', 'work', 'other']},
                                    'displayName': {'type': 'string', 'description': 'Display name for the email'},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': ['value']
                            }
                        },
                        'phoneNumbers': {
                            'type': 'array',
                            'description': 'List of phone number objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {'type': 'string', 'description': 'The phone number (required)'},
                                    'type': {'type': 'string', 'description': 'Phone type', 'enum': ['home', 'work', 'mobile', 'homeFax', 'workFax', 'otherFax', 'pager', 'workMobile', 'workPager', 'main', 'googleVoice', 'other']},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'canonicalForm': {'type': 'string', 'description': 'Canonical form of the phone number'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': ['value']
                            }
                        },
                        'addresses': {
                            'type': 'array',
                            'description': 'List of address objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'type': {'type': 'string', 'description': 'Address type', 'enum': ['home', 'work', 'other']},
                                    'formattedValue': {'type': 'string', 'description': 'Full formatted address string'},
                                    'streetAddress': {'type': 'string', 'description': 'Street address line'},
                                    'extendedAddress': {'type': 'string', 'description': 'Extended address (apartment, suite, etc.)'},
                                    'city': {'type': 'string', 'description': 'City name'},
                                    'region': {'type': 'string', 'description': 'State/region name'},
                                    'postalCode': {'type': 'string', 'description': 'ZIP/postal code'},
                                    'country': {'type': 'string', 'description': 'Country name'},
                                    'countryCode': {'type': 'string', 'description': 'Country code (e.g., "US", "CA")'},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'organizations': {
                            'type': 'array',
                            'description': 'List of organization objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'type': {'type': 'string', 'description': 'Organization type', 'enum': ['work', 'school', 'other']},
                                    'name': {'type': 'string', 'description': 'Organization name'},
                                    'title': {'type': 'string', 'description': 'Job title'},
                                    'department': {'type': 'string', 'description': 'Department name'},
                                    'location': {'type': 'string', 'description': 'Office location'},
                                    'jobDescription': {'type': 'string', 'description': 'Job description'},
                                    'symbol': {'type': 'string', 'description': 'Organization symbol/ticker'},
                                    'domain': {'type': 'string', 'description': 'Organization domain'},
                                    'costCenter': {'type': 'string', 'description': 'Cost center identifier'},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'birthdays': {
                            'type': 'array',
                            'description': 'List of birthday objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'date': {
                                        'type': 'object',
                                        'description': 'Date components with year, month, day keys',
                                        'properties': {
                                            'year': {'type': 'integer', 'description': 'Year'},
                                            'month': {'type': 'integer', 'description': 'Month (1-12)'},
                                            'day': {'type': 'integer', 'description': 'Day (1-31)'}
                                        },
                                        'required': []
                                    },
                                    'text': {'type': 'string', 'description': 'Text representation of birthday'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'photos': {
                            'type': 'array',
                            'description': 'List of photo objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'url': {'type': 'string', 'description': 'URL of the photo'},
                                    'default': {'type': 'boolean', 'description': 'Whether this is the default photo'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'urls': {
                            'type': 'array',
                            'description': 'List of URL objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {'type': 'string', 'description': 'The URL (required)'},
                                    'type': {'type': 'string', 'description': 'URL type', 'enum': ['home', 'work', 'blog', 'profile', 'homePage', 'ftp', 'reserved', 'other']},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': ['value']
                            }
                        },
                        'userDefined': {
                            'type': 'array',
                            'description': 'List of user-defined field objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'key': {'type': 'string', 'description': 'Field key/name (required)'},
                                    'value': {'type': 'string', 'description': 'Field value (required)'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': ['key', 'value']
                            }
                        }
                    },
                    'required': [
                        'names',
                        'emailAddresses'
                    ]
                }
            },
            'required': [
                'person_data'
            ]
        }
    }
)
def create_contact(person_data: Dict[str, Union[str, List, Dict]]) -> Dict[str, Union[str, List, Dict]]:
    """
    Create a new person contact.
    
    This method creates a new contact in the user's Google Contacts. The contact must have
    at least one name and one email address. The resource name is automatically generated.
    
    Args:
        person_data (Dict[str, Union[str, List, Dict]]): Dictionary containing person information. Must include:
            - names (List[Dict]): At least one name object with displayName, givenName, or familyName. Each name object may contain:
                - displayName (Optional[str]): Full display name
                - displayNameLastFirst (Optional[str]): Display name in last, first format
                - givenName (Optional[str]): First name
                - familyName (Optional[str]): Last name
                - middleName (Optional[str]): Middle name
                - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                - phoneticGivenName (Optional[str]): Phonetic first name
                - phoneticFamilyName (Optional[str]): Phonetic last name
                - phoneticMiddleName (Optional[str]): Phonetic middle name
                - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                - unstructuredName (Optional[str]): Unstructured name
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - emailAddresses (List[Dict]): At least one email address object with value. Each email object may contain:
                - value (str): The email address (required)
                - type (Optional[str]): Email type - "home", "work", "other"
                - displayName (Optional[str]): Display name for the email
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - phoneNumbers (Optional[List[Dict]]): List of phone number objects. Each phone object may contain:
                - value (str): The phone number (required)
                - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                - formattedType (Optional[str]): Human-readable type description
                - canonicalForm (Optional[str]): Canonical form of the phone number
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                - value (str): The nickname value
                - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - addresses (Optional[List[Dict]]): List of address objects. Each address object may contain:
                - type (Optional[str]): Address type - "home", "work", "other"
                - formattedValue (Optional[str]): Full formatted address string
                - streetAddress (Optional[str]): Street address line
                - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                - city (Optional[str]): City name
                - region (Optional[str]): State/region name
                - postalCode (Optional[str]): ZIP/postal code
                - country (Optional[str]): Country name
                - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - organizations (Optional[List[Dict]]): List of organization objects. Each organization object may contain:
                - type (Optional[str]): Organization type - "work", "school", "other"
                - name (Optional[str]): Organization name
                - title (Optional[str]): Job title
                - department (Optional[str]): Department name
                - location (Optional[str]): Office location
                - jobDescription (Optional[str]): Job description
                - symbol (Optional[str]): Organization symbol/ticker
                - domain (Optional[str]): Organization domain
                - costCenter (Optional[str]): Cost center identifier
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - birthdays (Optional[List[Dict]]): List of birthday objects. Each birthday object may contain:
                - date (Optional[Dict]): Date components with year, month, day keys
                    - year (Optional[int]): Year
                    - month (Optional[int]): Month (1-12)
                    - day (Optional[int]): Day (1-31)
                - text (Optional[str]): Text representation of birthday
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - photos (Optional[List[Dict]]): List of photo objects. Each photo object may contain:
                - url (Optional[str]): URL of the photo
                - default (Optional[bool]): Whether this is the default photo
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - urls (Optional[List[Dict]]): List of URL objects. Each URL object may contain:
                - value (str): The URL (required)
                - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - userDefined (Optional[List[Dict]]): List of user-defined field objects. Each object may contain:
                - key (str): Field key/name (required)
                - value (str): Field value (required)
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
    
    Returns:
        Dict[str, Union[str, List, Dict]]: Created person data with the following keys:
            - resourceName (str): Resource name of the newly created person (e.g., "people/123456789").
            - etag (str): ETag for the person record for versioning.
            - names (List[Dict]): List of name objects, each containing:
                - displayName (Optional[str]): Full display name
                - displayNameLastFirst (Optional[str]): Display name in last, first format
                - givenName (Optional[str]): First name
                - familyName (Optional[str]): Last name
                - middleName (Optional[str]): Middle name
                - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                - phoneticGivenName (Optional[str]): Phonetic first name
                - phoneticFamilyName (Optional[str]): Phonetic last name
                - phoneticMiddleName (Optional[str]): Phonetic middle name
                - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                - unstructuredName (Optional[str]): Unstructured name
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                - value (str): The nickname value
                - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - emailAddresses (List[Dict]): List of email address objects, each containing:
                - value (str): The email address
                - type (Optional[str]): Email type - "home", "work", "other"
                - displayName (Optional[str]): Display name for the email
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                - value (str): The phone number
                - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                - formattedType (Optional[str]): Human-readable type description
                - canonicalForm (Optional[str]): Canonical form of the phone number
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - addresses (Optional[List[Dict]]): List of address objects, each containing:
                - type (Optional[str]): Address type - "home", "work", "other"
                - formattedValue (Optional[str]): Full formatted address string
                - streetAddress (Optional[str]): Street address line
                - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                - city (Optional[str]): City name
                - region (Optional[str]): State/region name
                - postalCode (Optional[str]): ZIP/postal code
                - country (Optional[str]): Country name
                - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                - type (Optional[str]): Organization type - "work", "school", "other"
                - name (Optional[str]): Organization name
                - title (Optional[str]): Job title
                - department (Optional[str]): Department name
                - location (Optional[str]): Office location
                - jobDescription (Optional[str]): Job description
                - symbol (Optional[str]): Organization symbol/ticker
                - domain (Optional[str]): Organization domain
                - costCenter (Optional[str]): Cost center identifier
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                - date (Optional[Dict]): Date components with year, month, day keys
                    - year (Optional[int]): Year
                    - month (Optional[int]): Month (1-12)
                    - day (Optional[int]): Day (1-31)
                - text (Optional[str]): Text representation of birthday
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - photos (Optional[List[Dict]]): List of photo objects, each containing:
                - url (Optional[str]): URL of the photo
                - default (Optional[bool]): Whether this is the default photo
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - urls (Optional[List[Dict]]): List of URL objects, each containing:
                - value (str): The URL
                - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                - key (str): Field key/name
                - value (str): Field value
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - created (str): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z").
            - updated (str): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z").
    
    Raises:
        ValueError: If required fields are missing or invalid.
        ValidationError: If the input data fails validation.
    

    """
    # Validate input using Pydantic model
    person = Person(**person_data)
    request = CreateContactRequest(person_data=person)
    
    logger.info("Creating new person contact")

    # Normalize phone numbers
    if request.person_data.phone_numbers:
        for phone_number in request.person_data.phone_numbers:
            if phone_number.value:
                normalized = normalize_phone_number(phone_number.value)
                if normalized:
                    phone_number.value = normalized
                else:
                    raise ValueError(f"Invalid phone number format: {phone_number.value}")

    db = DB
    people_data = db.get("people", {})

    # Generate resource name
    resource_name = f"people/{generate_id()}"

    # Create person object - serialize the person data properly
    person_dict = person.model_dump(mode='json', by_alias=True, exclude_unset=True)
    person_obj = {
        "resourceName": resource_name,
        "etag": f"etag_{generate_id()}",
        "names": person_dict.get("names", []),
        "nicknames": person_dict.get("nicknames", []),
        "emailAddresses": person_dict.get("emailAddresses", []),
        "phoneNumbers": person_dict.get("phoneNumbers", []),
        "addresses": person_dict.get("addresses", []),
        "organizations": person_dict.get("organizations", []),
        "birthdays": person_dict.get("birthdays", []),
        "photos": person_dict.get("photos", []),
        "urls": person_dict.get("urls", []),
        "userDefined": person_dict.get("userDefined", []),
        "created": datetime.now().isoformat() + "Z",
        "updated": datetime.now().isoformat() + "Z"
    }

    # response = CreateContactResponse(**person_obj).model_dump(by_alias=True)
    people_data[resource_name] = person_obj
    db.set("people", people_data)
    logger.info(f"Created person with resource name: {resource_name}")

    return person_obj


@tool_spec(
    spec={
        'name': 'update_contact',
        'description': """ Update an existing person contact.
        
        This method updates an existing contact in the user's Google Contacts. You can update
        all fields or specify only certain fields to update using the update_person_fields parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the person to update. Must start with "people/".
                    Example: "people/123456789" """
                },
                'person_data': {
                    'type': 'object',
                    'description': 'Dictionary containing updated person information. Only the fields you want to update need to be included.',
                    'properties': {
                        'names': {
                            'type': 'array',
                            'description': 'Person name objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'displayName': {'type': 'string', 'description': 'Full display name'},
                                    'displayNameLastFirst': {'type': 'string', 'description': 'Display name in last, first format'},
                                    'givenName': {'type': 'string', 'description': 'First name'},
                                    'familyName': {'type': 'string', 'description': 'Last name'},
                                    'middleName': {'type': 'string', 'description': 'Middle name'},
                                    'honorificPrefix': {'type': 'string', 'description': 'Title prefix (e.g., "Dr.", "Mr.")'},
                                    'honorificSuffix': {'type': 'string', 'description': 'Title suffix (e.g., "Jr.", "Sr.")'},
                                    'phoneticGivenName': {'type': 'string', 'description': 'Phonetic first name'},
                                    'phoneticFamilyName': {'type': 'string', 'description': 'Phonetic last name'},
                                    'phoneticMiddleName': {'type': 'string', 'description': 'Phonetic middle name'},
                                    'phoneticHonorificPrefix': {'type': 'string', 'description': 'Phonetic title prefix'},
                                    'phoneticHonorificSuffix': {'type': 'string', 'description': 'Phonetic title suffix'},
                                    'unstructuredName': {'type': 'string', 'description': 'Unstructured name'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'nicknames': {
                            'type': 'array',
                            'description': """ Nickname objects. Each item should include
                                            fields such as "value" and may include "type". """,
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {
                                        'type': 'string',
                                        'description': 'The nickname value'
                                    },
                                    'type': {
                                        'type': 'string',
                                        'description': 'The type of nickname (e.g., "DEFAULT", "ALTERNATE_NAME")'
                                    },
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': ['value']
                            }
                        },
                        'emailAddresses': {
                            'type': 'array',
                            'description': 'Email address objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {'type': 'string', 'description': 'The email address'},
                                    'type': {'type': 'string', 'description': 'Email type', 'enum': ['home', 'work', 'other']},
                                    'displayName': {'type': 'string', 'description': 'Display name for the email'},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'phoneNumbers': {
                            'type': 'array',
                            'description': 'Phone number objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {'type': 'string', 'description': 'The phone number'},
                                    'type': {'type': 'string', 'description': 'Phone type', 'enum': ['home', 'work', 'mobile', 'homeFax', 'workFax', 'otherFax', 'pager', 'workMobile', 'workPager', 'main', 'googleVoice', 'other']},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'canonicalForm': {'type': 'string', 'description': 'Canonical form of the phone number'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'addresses': {
                            'type': 'array',
                            'description': 'Address objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'type': {'type': 'string', 'description': 'Address type', 'enum': ['home', 'work', 'other']},
                                    'formattedValue': {'type': 'string', 'description': 'Full formatted address string'},
                                    'streetAddress': {'type': 'string', 'description': 'Street address line'},
                                    'extendedAddress': {'type': 'string', 'description': 'Extended address (apartment, suite, etc.)'},
                                    'city': {'type': 'string', 'description': 'City name'},
                                    'region': {'type': 'string', 'description': 'State/region name'},
                                    'postalCode': {'type': 'string', 'description': 'ZIP/postal code'},
                                    'country': {'type': 'string', 'description': 'Country name'},
                                    'countryCode': {'type': 'string', 'description': 'Country code (e.g., "US", "CA")'},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'organizations': {
                            'type': 'array',
                            'description': 'Organization objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'type': {'type': 'string', 'description': 'Organization type', 'enum': ['work', 'school', 'other']},
                                    'name': {'type': 'string', 'description': 'Organization name'},
                                    'title': {'type': 'string', 'description': 'Job title'},
                                    'department': {'type': 'string', 'description': 'Department name'},
                                    'location': {'type': 'string', 'description': 'Office location'},
                                    'jobDescription': {'type': 'string', 'description': 'Job description'},
                                    'symbol': {'type': 'string', 'description': 'Organization symbol/ticker'},
                                    'domain': {'type': 'string', 'description': 'Organization domain'},
                                    'costCenter': {'type': 'string', 'description': 'Cost center identifier'},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'birthdays': {
                            'type': 'array',
                            'description': 'Birthday objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'date': {
                                        'type': 'object',
                                        'description': 'Date components with year, month, day keys',
                                        'properties': {
                                            'year': {'type': 'integer', 'description': 'Year'},
                                            'month': {'type': 'integer', 'description': 'Month (1-12)'},
                                            'day': {'type': 'integer', 'description': 'Day (1-31)'}
                                        },
                                        'required': []
                                    },
                                    'text': {'type': 'string', 'description': 'Text representation of birthday'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'photos': {
                            'type': 'array',
                            'description': 'Photo objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'url': {'type': 'string', 'description': 'URL of the photo'},
                                    'default': {'type': 'boolean', 'description': 'Whether this is the default photo'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'urls': {
                            'type': 'array',
                            'description': 'URL objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {'type': 'string', 'description': 'The URL'},
                                    'type': {'type': 'string', 'description': 'URL type', 'enum': ['home', 'work', 'blog', 'profile', 'homePage', 'ftp', 'reserved', 'other']},
                                    'formattedType': {'type': 'string', 'description': 'Human-readable type description'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'userDefined': {
                            'type': 'array',
                            'description': 'User-defined field objects',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'key': {'type': 'string', 'description': 'Field key/name'},
                                    'value': {'type': 'string', 'description': 'Field value'},
                                    'metadata': {
                                        'type': 'object',
                                        'description': 'Field metadata',
                                        'properties': {
                                            'primary': {'type': 'boolean', 'description': 'Whether this is the primary field'},
                                            'source': {
                                                'type': 'object', 
                                                'description': 'Source information',
                                                'properties': {
                                                    'type': {'type': 'string', 'description': 'Source type', 'enum': ['SOURCE_TYPE_UNSPECIFIED', 'ACCOUNT', 'PROFILE', 'DOMAIN_PROFILE', 'CONTACT', 'OTHER_CONTACT', 'DOMAIN_CONTACT']},
                                                    'id': {'type': 'string', 'description': 'Unique identifier within the source type'},
                                                    'etag': {'type': 'string', 'description': 'HTTP entity tag of the source'},
                                                    'updateTime': {'type': 'string', 'description': 'Last update timestamp in RFC3339 UTC format'}
                                                },
                                                'required': []
                                            },
                                            'sourcePrimary': {'type': 'boolean', 'description': 'Whether the source is primary'},
                                            'verified': {'type': 'boolean', 'description': 'Whether the field is verified'}
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        }
                    },
                    'required': []
                },
                'update_person_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of person fields to update.
                    If specified, only these fields will be updated.
                    If not specified, all provided fields will be updated.
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers,
                    addresses, organizations, birthdays, photos, urls, userDefined """
                }
            },
            'required': [
                'resource_name',
                'person_data'
            ]
        }
    }
)
def update_contact(resource_name: str, person_data: Dict[str, Union[str, List, Dict]], update_person_fields: Optional[str] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    Update an existing person contact.
    
    This method updates an existing contact in the user's Google Contacts. You can update
    all fields or specify only certain fields to update using the update_person_fields parameter.
    
    Args:
        resource_name (str): The resource name of the person to update. Must start with "people/".
                            Example: "people/123456789"
        person_data (Dict[str, Union[str, List, Dict]]): Dictionary containing updated person information. Only the fields you want to update need to be included:
            - names (Optional[List[Dict]]): Person name objects, each containing:
                - displayName (Optional[str]): Full display name
                - displayNameLastFirst (Optional[str]): Display name in last, first format
                - givenName (Optional[str]): First name
                - familyName (Optional[str]): Last name
                - middleName (Optional[str]): Middle name
                - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                - phoneticGivenName (Optional[str]): Phonetic first name
                - phoneticFamilyName (Optional[str]): Phonetic last name
                - phoneticMiddleName (Optional[str]): Phonetic middle name
                - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                - unstructuredName (Optional[str]): Unstructured name
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                - value (str): The nickname value
                - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - emailAddresses (Optional[List[Dict]]): Email address objects, each containing:
                - value (str): The email address
                - type (Optional[str]): Email type - "home", "work", "other"
                - displayName (Optional[str]): Display name for the email
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - phoneNumbers (Optional[List[Dict]]): Phone number objects, each containing:
                - value (str): The phone number
                - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                - formattedType (Optional[str]): Human-readable type description
                - canonicalForm (Optional[str]): Canonical form of the phone number
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - addresses (Optional[List[Dict]]): Address objects, each containing:
                - type (Optional[str]): Address type - "home", "work", "other"
                - formattedValue (Optional[str]): Full formatted address string
                - streetAddress (Optional[str]): Street address line
                - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                - city (Optional[str]): City name
                - region (Optional[str]): State/region name
                - postalCode (Optional[str]): ZIP/postal code
                - country (Optional[str]): Country name
                - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - organizations (Optional[List[Dict]]): Organization objects, each containing:
                - type (Optional[str]): Organization type - "work", "school", "other"
                - name (Optional[str]): Organization name
                - title (Optional[str]): Job title
                - department (Optional[str]): Department name
                - location (Optional[str]): Office location
                - jobDescription (Optional[str]): Job description
                - symbol (Optional[str]): Organization symbol/ticker
                - domain (Optional[str]): Organization domain
                - costCenter (Optional[str]): Cost center identifier
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - birthdays (Optional[List[Dict]]): Birthday objects, each containing:
                - date (Optional[Dict]): Date components with year, month, day keys
                    - year (Optional[int]): Year
                    - month (Optional[int]): Month (1-12)
                    - day (Optional[int]): Day (1-31)
                - text (Optional[str]): Text representation of birthday
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - photos (Optional[List[Dict]]): Photo objects, each containing:
                - url (Optional[str]): URL of the photo
                - default (Optional[bool]): Whether this is the default photo
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - urls (Optional[List[Dict]]): URL objects, each containing:
                - value (str): The URL
                - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - userDefined (Optional[List[Dict]]): User-defined field objects, each containing:
                - key (str): Field key/name
                - value (str): Field value
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
        update_person_fields (Optional[str]): Comma-separated list of person fields to update.
                                             If specified, only these fields will be updated.
                                             If not specified, all provided fields will be updated.
                                             Valid fields: names, nicknames, emailAddresses, phoneNumbers,
                                             addresses, organizations, birthdays, photos, urls, userDefined
    
    Returns:
        Dict[str, Union[str, List, Dict]]: Created person data with the following keys:
            - resourceName (str): Resource name of the newly created person (e.g., "people/123456789").
            - etag (str): ETag for the person record for versioning.
            - names (List[Dict]): List of name objects, each containing:
                - displayName (Optional[str]): Full display name
                - displayNameLastFirst (Optional[str]): Display name in last, first format
                - givenName (Optional[str]): First name
                - familyName (Optional[str]): Last name
                - middleName (Optional[str]): Middle name
                - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                - phoneticGivenName (Optional[str]): Phonetic first name
                - phoneticFamilyName (Optional[str]): Phonetic last name
                - phoneticMiddleName (Optional[str]): Phonetic middle name
                - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                - unstructuredName (Optional[str]): Unstructured name
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                - value (str): The nickname value
                - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - emailAddresses (List[Dict]): List of email address objects, each containing:
                - value (str): The email address
                - type (Optional[str]): Email type - "home", "work", "other"
                - displayName (Optional[str]): Display name for the email
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                - value (str): The phone number
                - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                - formattedType (Optional[str]): Human-readable type description
                - canonicalForm (Optional[str]): Canonical form of the phone number
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - addresses (Optional[List[Dict]]): List of address objects, each containing:
                - type (Optional[str]): Address type - "home", "work", "other"
                - formattedValue (Optional[str]): Full formatted address string
                - streetAddress (Optional[str]): Street address line
                - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                - city (Optional[str]): City name
                - region (Optional[str]): State/region name
                - postalCode (Optional[str]): ZIP/postal code
                - country (Optional[str]): Country name
                - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                - type (Optional[str]): Organization type - "work", "school", "other"
                - name (Optional[str]): Organization name
                - title (Optional[str]): Job title
                - department (Optional[str]): Department name
                - location (Optional[str]): Office location
                - jobDescription (Optional[str]): Job description
                - symbol (Optional[str]): Organization symbol/ticker
                - domain (Optional[str]): Organization domain
                - costCenter (Optional[str]): Cost center identifier
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                - date (Optional[Dict]): Date components with year, month, day keys
                    - year (Optional[int]): Year
                    - month (Optional[int]): Month (1-12)
                    - day (Optional[int]): Day (1-31)
                - text (Optional[str]): Text representation of birthday
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - photos (Optional[List[Dict]]): List of photo objects, each containing:
                - url (Optional[str]): URL of the photo
                - default (Optional[bool]): Whether this is the default photo
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - urls (Optional[List[Dict]]): List of URL objects, each containing:
                - value (str): The URL
                - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                - formattedType (Optional[str]): Human-readable type description
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                - key (str): Field key/name
                - value (str): Field value
                - metadata (Optional[Dict]): Field metadata containing:
                    - primary (Optional[bool]): Whether this is the primary field
                    - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                    - sourcePrimary (Optional[bool]): Whether the source is primary
                    - verified (Optional[bool]): Whether the field is verified
            - created (str): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z").
            - updated (str): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z").
    
    Raises:
        ValueError: If the resource name is invalid or the person is not found.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    person = Person(**person_data)
    request = UpdateContactRequest(
        resource_name=resource_name,
        person_data=person,
        update_person_fields=update_person_fields
    )
    
    logger.info(f"Updating person with resource name: {request.resource_name}")

    # Normalize phone numbers
    if request.person_data.phone_numbers:
        for phone_number in request.person_data.phone_numbers:
            if phone_number.value:
                normalized = normalize_phone_number(phone_number.value)
                if normalized:
                    phone_number.value = normalized
                else:
                    raise ValueError(f"Invalid phone number format: {phone_number.value}")

    db = DB
    people_data = db.get("people", {})

    if request.resource_name not in people_data:
        raise ValueError(f"Person with resource name '{request.resource_name}' not found")

    existing_person = people_data[request.resource_name]

    # Update only specified fields if update_person_fields is provided
    if request.update_person_fields:
        field_list = [field.strip() for field in request.update_person_fields.split(",")]
        for field in field_list:
            if hasattr(request.person_data, field):
                field_value = getattr(request.person_data, field)
                if field_value is not None:
                    existing_person[field] = field_value
    else:
        # Update all provided fields
        person_dict = request.person_data.dict(exclude_unset=True, by_alias=True)
        existing_person.update(person_dict)

    # Update timestamp
    existing_person["updated"] = datetime.now().isoformat() + "Z"
    existing_person["etag"] = f"etag_{generate_id()}"

    # Save to database
    people_data[request.resource_name] = existing_person
    db.set("people", people_data)

    logger.info(f"Updated person with resource name: {request.resource_name}")

    return existing_person


@tool_spec(
    spec={
        'name': 'delete_contact',
        'description': """ Delete a person contact.
        
        This method permanently deletes a contact from the user's Google Contacts.
        The deletion cannot be undone. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the person to delete. Must start with "people/".
                    Example: "people/123456789" """
                }
            },
            'required': [
                'resource_name'
            ]
        }
    }
)
def delete_contact(resource_name: str) -> Dict[str, Union[bool, str]]:
    """
    Delete a person contact.
    
    This method permanently deletes a contact from the user's Google Contacts.
    The deletion cannot be undone.
    
    Args:
        resource_name (str): The resource name of the person to delete. Must start with "people/".
                            Example: "people/123456789"
    
    Returns:
        Dict[str, Union[bool, str]]: A dictionary containing deletion confirmation with the following structure:
            - success (bool): Whether the contact was deleted successfully
            - deletedResourceName (str): The resource name of the person that was deleted
            - message (str): A human-readable summary of the action taken
    
    Raises:
        ValueError: If the resource name is invalid or the person is not found.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = DeleteContactRequest(resource_name=resource_name)
    
    logger.info(f"Deleting person with resource name: {request.resource_name}")

    db = DB
    people_data = db.get("people", {})

    if request.resource_name not in people_data:
        raise ValueError(f"Person with resource name '{request.resource_name}' not found")

    # Remove from database
    deleted_person = people_data.pop(request.resource_name)
    db.set("people", people_data)

    logger.info(f"Deleted person with resource name: {request.resource_name}")
    
    response_data = {
        "success": True,
        "deletedResourceName": request.resource_name,
        "message": "Person deleted successfully"
    }
    
    # Validate response using Pydantic model
    response = DeleteContactResponse(**response_data)
    return response.dict(by_alias=True)


@tool_spec(
    spec={
        'name': 'list_connections',
        'description': """ List people in the authenticated user's contacts (connections).
        
        This method retrieves a list of people in the authenticated user's contacts.
        The response can be paginated and supports various sorting options. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name to return connections for.
                    Defaults to "people/me" (the authenticated user).
                    Must start with "people/". """
                },
                'person_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of person fields to include in the response.
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. """
                },
                'page_size': {
                    'type': 'integer',
                    'description': """ The number of connections to include in the response.
                    Must be between 1 and 1000. Defaults to 100. """
                },
                'page_token': {
                    'type': 'string',
                    'description': """ A page token, received from a previous response.
                    Used for pagination. """
                },
                'sort_order': {
                    'type': 'string',
                    'description': """ The order in which the connections should be sorted.
                    Valid values: "LAST_MODIFIED_ASCENDING", "LAST_MODIFIED_DESCENDING",
                    "FIRST_NAME_ASCENDING", "LAST_NAME_ASCENDING". """
                },
                'sync_token': {
                    'type': 'string',
                    'description': """ A sync token, returned by a previous call.
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
def list_connections(resource_name: str = "people/me", person_fields: Optional[str] = None,
                     page_size: Optional[int] = None, page_token: Optional[str] = None,
                     sort_order: Optional[str] = None, sync_token: Optional[str] = None,
                     request_sync_token: Optional[bool] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    List people in the authenticated user's contacts (connections).
    
    This method retrieves a list of people in the authenticated user's contacts.
    The response can be paginated and supports various sorting options.
    
    Args:
        resource_name (str, optional): The resource name to return connections for.
                                      Defaults to "people/me" (the authenticated user).
                                      Must start with "people/".
        person_fields (Optional[str]): Comma-separated list of person fields to include in the response.
                                      Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                                      organizations, birthdays, photos, urls, userDefined, resourceName,
                                      etag, created, updated.
        page_size (Optional[int]): The number of connections to include in the response.
                                  Must be between 1 and 1000. Defaults to 100.
        page_token (Optional[str]): A page token, received from a previous response.
                                   Used for pagination.
        sort_order (Optional[str]): The order in which the connections should be sorted.
                                   Valid values: "LAST_MODIFIED_ASCENDING", "LAST_MODIFIED_DESCENDING",
                                   "FIRST_NAME_ASCENDING", "LAST_NAME_ASCENDING".
        sync_token (Optional[str]): A sync token, returned by a previous call.
                                   Used for incremental sync.
        request_sync_token (Optional[bool]): Whether the response should include a sync token.
                                            Defaults to False.
    
    Returns:
        Dict[str, Union[str, List, Dict]]: A dictionary containing the list of connections with the following keys:
            - connections (List[Dict]): List of person objects, each containing:
                - resourceName (str): Resource name of the person (e.g., "people/123456789")
                - etag (str): ETag for the person record for versioning
                - names (Optional[List[Dict]]): List of name objects, each containing:
                    - displayName (Optional[str]): Full display name
                    - displayNameLastFirst (Optional[str]): Display name in last, first format
                    - givenName (Optional[str]): First name
                    - familyName (Optional[str]): Last name
                    - middleName (Optional[str]): Middle name
                    - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                    - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                    - phoneticGivenName (Optional[str]): Phonetic first name
                    - phoneticFamilyName (Optional[str]): Phonetic last name
                    - phoneticMiddleName (Optional[str]): Phonetic middle name
                    - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                    - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                    - unstructuredName (Optional[str]): Unstructured name
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                    - value (str): The nickname value
                    - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - emailAddresses (Optional[List[Dict]]): List of email address objects, each containing:
                    - value (str): The email address
                    - type (Optional[str]): Email type - "home", "work", "other"
                    - displayName (Optional[str]): Display name for the email
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                    - value (str): The phone number
                    - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - canonicalForm (Optional[str]): Canonical form of the phone number
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - addresses (Optional[List[Dict]]): List of address objects, each containing:
                    - type (Optional[str]): Address type - "home", "work", "other"
                    - formattedValue (Optional[str]): Full formatted address string
                    - streetAddress (Optional[str]): Street address line
                    - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                    - city (Optional[str]): City name
                    - region (Optional[str]): State/region name
                    - postalCode (Optional[str]): ZIP/postal code
                    - country (Optional[str]): Country name
                    - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                    - type (Optional[str]): Organization type - "work", "school", "other"
                    - name (Optional[str]): Organization name
                    - title (Optional[str]): Job title
                    - department (Optional[str]): Department name
                    - location (Optional[str]): Office location
                    - jobDescription (Optional[str]): Job description
                    - symbol (Optional[str]): Organization symbol/ticker
                    - domain (Optional[str]): Organization domain
                    - costCenter (Optional[str]): Cost center identifier
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                    - date (Optional[Dict]): Date components with year, month, day keys
                        - year (Optional[int]): Year
                        - month (Optional[int]): Month (1-12)
                        - day (Optional[int]): Day (1-31)
                    - text (Optional[str]): Text representation of birthday
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - photos (Optional[List[Dict]]): List of photo objects, each containing:
                    - url (Optional[str]): URL of the photo
                    - default (Optional[bool]): Whether this is the default photo
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - urls (Optional[List[Dict]]): List of URL objects, each containing:
                    - value (str): The URL
                    - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                    - key (str): Field key/name
                    - value (str): Field value
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - created (Optional[str]): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
                - updated (Optional[str]): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
            - nextPageToken (Optional[str]): Token for retrieving the next page of results
            - totalItems (Optional[int]): Total number of connections available
            - nextSyncToken (Optional[str]): Token for incremental synchronization
    
    Raises:
        ValueError: If the resource name is invalid or parameters are invalid.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = ListConnectionsRequest(
        resource_name=resource_name,
        person_fields=person_fields,
        page_size=page_size,
        page_token=page_token,
        sort_order=sort_order,
        sync_token=sync_token,
        request_sync_token=request_sync_token
    )
    
    logger.info(f"Listing connections for resource: {request.resource_name}")

    db = DB
    people_data = db.get("people", {})

    # Filter people based on resource_name (simplified logic)
    connections = []
    for person_id, person in people_data.items():
        if person_id != request.resource_name:  # Exclude the requesting user
            # Convert Pydantic model instances to dictionaries if needed
            if hasattr(person, 'model_dump'):
                person_dict = person.model_dump(by_alias=True)
            else:
                person_dict = person
            connections.append(person_dict)

    # Apply sorting if specified
    if request.sort_order:
        if request.sort_order == "FIRST_NAME_ASCENDING":
            connections.sort(key=lambda x: x.get("names", [{}])[0].get("givenName", ""))
        elif request.sort_order == "LAST_NAME_ASCENDING":
            connections.sort(key=lambda x: x.get("names", [{}])[0].get("familyName", ""))
        elif request.sort_order == "LAST_MODIFIED_DESCENDING":
            connections.sort(key=lambda x: x.get("updated", ""), reverse=True)
        elif request.sort_order == "LAST_MODIFIED_ASCENDING":
            connections.sort(key=lambda x: x.get("updated", ""))

    # Apply pagination
    if request.page_size:
        start_index = 0
        if request.page_token:
            try:
                start_index = int(request.page_token)
            except ValueError:
                start_index = 0

        end_index = start_index + request.page_size
        connections = connections[start_index:end_index]

        next_page_token = str(end_index) if end_index < len(people_data) else None
    else:
        next_page_token = None

    # Filter by person_fields if specified
    if request.person_fields:
        field_list = [field.strip() for field in request.person_fields.split(",")]
        filtered_connections = []
        for person in connections:
            filtered_person = {}
            for field in field_list:
                if field in person:
                    filtered_person[field] = person[field]
            filtered_connections.append(filtered_person)
        connections = filtered_connections

    response_data = {
        "connections": connections,
        "nextPageToken": next_page_token,
        "totalItems": len(connections)
    }

    # Add sync token if requested
    if request.request_sync_token:
        response_data["nextSyncToken"] = f"sync_{generate_id()}"

    # Return the response directly as a dictionary (as per docstring)
    # The function should return Dict[str, Union[str, List, Dict]] not a Pydantic model
    return response_data


@tool_spec(
    spec={
        'name': 'search_people',
        'description': """ Search for people in the authenticated user's contacts.
        
        This method searches through the authenticated user's contacts using a plain-text query.
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
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. """
                },
                'sources': {
                    'type': 'array',
                    'description': """ List of sources to retrieve data from. Valid sources include
                    "READ_SOURCE_TYPE_UNSPECIFIED", "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                    "READ_SOURCE_TYPE_DOMAIN_CONTACT", "READ_SOURCE_TYPE_OTHER_CONTACT". """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'query',
                'read_mask'
            ]
        }
    }
)
def search_people(query: str, read_mask: str,
                  sources: Optional[List[str]] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    Search for people in the authenticated user's contacts.
    
    This method searches through the authenticated user's contacts using a plain-text query.
    The search is performed across names, email addresses, and other contact information.
    
    Args:
        query (str): The plain-text query for the request. Must not be empty and cannot exceed 1000 characters.
                     The search is case-insensitive and performs partial matching.
        read_mask (str): Required. A field mask to restrict which fields on each person are returned.
                         Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                         organizations, birthdays, photos, urls, userDefined, resourceName,
                         etag, created, updated.
        sources (Optional[List[str]]): List of sources to retrieve data from. Valid sources include
                                      "READ_SOURCE_TYPE_UNSPECIFIED", "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                                      "READ_SOURCE_TYPE_DOMAIN_CONTACT", "READ_SOURCE_TYPE_OTHER_CONTACT".
    
    Returns:
        Dict[str, Union[str, List, Dict]]: A dictionary containing the search results with the following keys:
            - results (List[Dict]): List of person objects matching the search query, each containing:
                - resourceName (str): Resource name of the person (e.g., "people/123456789")
                - etag (str): ETag for the person record for versioning
                - names (Optional[List[Dict]]): List of name objects, each containing:
                    - displayName (Optional[str]): Full display name
                    - displayNameLastFirst (Optional[str]): Display name in last, first format
                    - givenName (Optional[str]): First name
                    - familyName (Optional[str]): Last name
                    - middleName (Optional[str]): Middle name
                    - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                    - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                    - phoneticGivenName (Optional[str]): Phonetic first name
                    - phoneticFamilyName (Optional[str]): Phonetic last name
                    - phoneticMiddleName (Optional[str]): Phonetic middle name
                    - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                    - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                    - unstructuredName (Optional[str]): Unstructured name
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                    - value (str): The nickname value
                    - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - emailAddresses (Optional[List[Dict]]): List of email address objects, each containing:
                    - value (str): The email address
                    - type (Optional[str]): Email type - "home", "work", "other"
                    - displayName (Optional[str]): Display name for the email
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                    - value (str): The phone number
                    - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - canonicalForm (Optional[str]): Canonical form of the phone number
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - addresses (Optional[List[Dict]]): List of address objects, each containing:
                    - type (Optional[str]): Address type - "home", "work", "other"
                    - formattedValue (Optional[str]): Full formatted address string
                    - streetAddress (Optional[str]): Street address line
                    - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                    - city (Optional[str]): City name
                    - region (Optional[str]): State/region name
                    - postalCode (Optional[str]): ZIP/postal code
                    - country (Optional[str]): Country name
                    - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                    - type (Optional[str]): Organization type - "work", "school", "other"
                    - name (Optional[str]): Organization name
                    - title (Optional[str]): Job title
                    - department (Optional[str]): Department name
                    - location (Optional[str]): Office location
                    - jobDescription (Optional[str]): Job description
                    - symbol (Optional[str]): Organization symbol/ticker
                    - domain (Optional[str]): Organization domain
                    - costCenter (Optional[str]): Cost center identifier
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                    - date (Optional[Dict]): Date components with year, month, day keys
                        - year (Optional[int]): Year
                        - month (Optional[int]): Month (1-12)
                        - day (Optional[int]): Day (1-31)
                    - text (Optional[str]): Text representation of birthday
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - photos (Optional[List[Dict]]): List of photo objects, each containing:
                    - url (Optional[str]): URL of the photo
                    - default (Optional[bool]): Whether this is the default photo
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - urls (Optional[List[Dict]]): List of URL objects, each containing:
                    - value (str): The URL
                    - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                    - key (str): Field key/name
                    - value (str): Field value
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - created (Optional[str]): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
                - updated (Optional[str]): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
            - totalItems (int): Total number of search results found
    
    Raises:
        ValueError: If the query is empty or invalid.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = SearchPeopleRequest(
        query=query,
        read_mask=read_mask,
        sources=sources
    )
    
    logger.info(f"Searching people with query: {request.query}")


    db = DB
    
    # Determine which collections to search based on sources parameter
    collections_to_search = []
    
    if request.sources is None:
        # If no sources specified, search all collections
        collections_to_search = [
            ("people", "people"),
            ("directoryPeople", "directoryPeople"),
            ("otherContacts", "otherContacts")
        ]
    else:
        # Map source types to database collections
        source_to_collection = {
            "READ_SOURCE_TYPE_PROFILE": "people",
            "READ_SOURCE_TYPE_CONTACT": "people", 
            "READ_SOURCE_TYPE_DOMAIN_CONTACT": "directoryPeople",
            "READ_SOURCE_TYPE_OTHER_CONTACT": "otherContacts"
        }
        
        for source in request.sources:
            if source in source_to_collection:
                collection_name = source_to_collection[source]
                collections_to_search.append((collection_name, collection_name))
            else:
                logger.warning(f"Unknown source type: {source}")

    # Simple search implementation
    results = []
    query_lower = request.query.lower()

    # Pre-compute a normalized version of the query for phone matching
    normalized_query_for_phone = normalize_phone_number(request.query)

    # Search in each specified collection
    for collection_name, collection_key in collections_to_search:
        collection_data = db.get(collection_key, {})
        
        for person_id, person in collection_data.items():
            person_matched = False
            
            # Search in names
            if not person_matched:
                names = person.get("names")
                if names is not None:
                    for name in names:
                        if name is not None:
                            display_name = (name.get("displayName") or "").lower()
                            given_name = (name.get("givenName") or "").lower()
                            family_name = (name.get("familyName") or "").lower()
                            if (query_lower in display_name or 
                                query_lower in given_name or 
                                query_lower in family_name):
                                results.append(person)
                                person_matched = True
                                break

            # Search in email addresses
            if not person_matched:
                emails = person.get("emailAddresses")
                if emails is not None:
                    for email in emails:
                        if email is not None:
                            email_value = (email.get("value") or "").lower()
                            if query_lower in email_value:
                                results.append(person)
                                person_matched = True
                                break

            # Search in organizations
            if not person_matched:
                orgs = person.get("organizations")
                if orgs is not None:
                    for org in orgs:
                        if org is not None:
                            org_name = (org.get("name") or "").lower()
                            org_title = (org.get("title") or "").lower()
                            if query_lower in org_name or query_lower in org_title:
                                results.append(person)
                                person_matched = True
                                break

            # Search in phone numbers (normalized substring matching)
            if not person_matched and normalized_query_for_phone:
                for phone in person.get("phoneNumbers", []):
                    raw_phone_value = phone.get("value", "")
                    normalized_phone_value = normalize_phone_number(raw_phone_value)
                    if normalized_phone_value and normalized_query_for_phone in normalized_phone_value:
                        results.append(person)
                        person_matched = True
                        break

            # Search in nicknames
            if not person_matched:
                nickname_entries = []
                if isinstance(person.get("nicknames"), list):
                    nickname_entries.extend(person.get("nicknames", []))
                for entry in nickname_entries:
                    if isinstance(entry, dict):
                        nickname_value = str(entry.get("value", "")).lower()
                        if query_lower in nickname_value:
                            results.append(person)
                            person_matched = True
                            break

    # Remove duplicates
    unique_results = []
    seen_ids = set()
    for person in results:
        if person["resourceName"] not in seen_ids:
            unique_results.append(person)
            seen_ids.add(person["resourceName"])

    # Filter by read_mask (required for search_people)
    mask_fields = {field.strip() for field in request.read_mask.split(",")}
    mandatory_fields = {"resourceName", "etag"}
    all_fields = mandatory_fields | mask_fields

    filtered_results = [
        {field: person[field] for field in all_fields if field in person}
        for person in unique_results
    ]

    unique_results = filtered_results

    # Safety net: Sanitize data to prevent serialization failures
    sanitized_results = sanitize_data_for_serialization(unique_results)
    
    response_data = {
        "results": sanitized_results,
        "totalItems": len(sanitized_results)
    }

    # Validate response using Pydantic model
    response = SearchPeopleResponse(**response_data)
    
    return response.model_dump(mode='json', by_alias=True, exclude_unset=True)


@tool_spec(
    spec={
        'name': 'get_batch_get',
        'description': """ Get a collection of people by resource names.
        
        This method retrieves multiple people from the user's contacts in a single request.
        This is more efficient than making multiple individual get_contact calls. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_names': {
                    'type': 'array',
                    'description': """ List of resource names of the people to retrieve.
                    Must contain between 1 and 50 resource names.
                    Each resource name must start with "people/".
                    Example: ["people/123456789", "people/987654321"] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'person_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of person fields to include in the response.
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. """
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
                'resource_names'
            ]
        }
    }
)
def get_batch_get(resource_names: List[str], person_fields: Optional[str] = None,
                  sources: Optional[List[str]] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    Get a collection of people by resource names.
    
    This method retrieves multiple people from the user's contacts in a single request.
    This is more efficient than making multiple individual get_contact calls.
    
    Args:
        resource_names (List[str]): List of resource names of the people to retrieve.
                                   Must contain between 1 and 50 resource names.
                                   Each resource name must start with "people/".
                                   Example: ["people/123456789", "people/987654321"]
        person_fields (Optional[str]): Comma-separated list of person fields to include in the response.
                                      Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                                      organizations, birthdays, photos, urls, userDefined, resourceName,
                                      etag, created, updated.
        sources (Optional[List[str]]): List of sources to retrieve data from. Valid sources include
                                      "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                                      "READ_SOURCE_TYPE_DOMAIN_PROFILE", "READ_SOURCE_TYPE_DIRECTORY".
    
    Returns:
        Dict[str, Union[str, List, Dict]]: A dictionary containing the batch of people with the following keys:
            - responses (List[Dict]): List of person objects that were found, each containing:
                - resourceName (str): Resource name of the person (e.g., "people/123456789")
                - etag (str): ETag for the person record for versioning
                - names (Optional[List[Dict]]): List of name objects, each containing:
                    - displayName (Optional[str]): Full display name
                    - displayNameLastFirst (Optional[str]): Display name in last, first format
                    - givenName (Optional[str]): First name
                    - familyName (Optional[str]): Last name
                    - middleName (Optional[str]): Middle name
                    - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                    - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                    - phoneticGivenName (Optional[str]): Phonetic first name
                    - phoneticFamilyName (Optional[str]): Phonetic last name
                    - phoneticMiddleName (Optional[str]): Phonetic middle name
                    - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                    - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                    - unstructuredName (Optional[str]): Unstructured name
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                    - value (str): The nickname value
                    - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - emailAddresses (Optional[List[Dict]]): List of email address objects, each containing:
                    - value (str): The email address
                    - type (Optional[str]): Email type - "home", "work", "other"
                    - displayName (Optional[str]): Display name for the email
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                    - value (str): The phone number
                    - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - canonicalForm (Optional[str]): Canonical form of the phone number
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - addresses (Optional[List[Dict]]): List of address objects, each containing:
                    - type (Optional[str]): Address type - "home", "work", "other"
                    - formattedValue (Optional[str]): Full formatted address string
                    - streetAddress (Optional[str]): Street address line
                    - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                    - city (Optional[str]): City name
                    - region (Optional[str]): State/region name
                    - postalCode (Optional[str]): ZIP/postal code
                    - country (Optional[str]): Country name
                    - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                    - type (Optional[str]): Organization type - "work", "school", "other"
                    - name (Optional[str]): Organization name
                    - title (Optional[str]): Job title
                    - department (Optional[str]): Department name
                    - location (Optional[str]): Office location
                    - jobDescription (Optional[str]): Job description
                    - symbol (Optional[str]): Organization symbol/ticker
                    - domain (Optional[str]): Organization domain
                    - costCenter (Optional[str]): Cost center identifier
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                    - date (Optional[Dict]): Date components with year, month, day keys
                        - year (Optional[int]): Year
                        - month (Optional[int]): Month (1-12)
                        - day (Optional[int]): Day (1-31)
                    - text (Optional[str]): Text representation of birthday
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - photos (Optional[List[Dict]]): List of photo objects, each containing:
                    - url (Optional[str]): URL of the photo
                    - default (Optional[bool]): Whether this is the default photo
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - urls (Optional[List[Dict]]): List of URL objects, each containing:
                    - value (str): The URL
                    - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                    - key (str): Field key/name
                    - value (str): Field value
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - created (Optional[str]): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
                - updated (Optional[str]): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
            - notFound (List[str]): List of resource names that could not be found
            - totalItems (int): Total number of people requested (found + not found)
    
    Raises:
        ValueError: If resource_names is empty or contains invalid resource names.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = BatchGetRequest(
        resource_names=resource_names,
        person_fields=person_fields,
        sources=sources
    )
    
    logger.info(f"Getting batch of people: {request.resource_names}")

    db = DB
    people_data = db.get("people", {})

    results = []
    not_found = []

    for resource_name in request.resource_names:
        if resource_name in people_data:
            person = people_data[resource_name].copy()

            # Filter by person_fields if specified
            if request.person_fields:
                field_list = [field.strip() for field in request.person_fields.split(",")]
                filtered_person = {}
                for field in field_list:
                    if field in person:
                        filtered_person[field] = person[field]
                person = filtered_person

            results.append(person)
        else:
            not_found.append(resource_name)

    response_data = {
        "responses": results,
        "notFound": not_found,
        "totalItems": len(results)
    }

    # Validate response using Pydantic model
    response = BatchGetResponse(**response_data)
    return response.dict(by_alias=True)


@tool_spec(
    spec={
        'name': 'get_directory_person',
        'description': """ Get a single directory person by resource name.
        
        This method retrieves a specific person from the Google Workspace directory.
        Directory people are users in your organization's Google Workspace domain. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': """ The resource name of the directory person to retrieve.
                    Must start with "directoryPeople/".
                    Example: "directoryPeople/123456789" """
                },
                'read_mask': {
                    'type': 'string',
                    'description': """ A field mask to restrict which fields on each person are returned.
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. """
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
def get_directory_person(resource_name: str, read_mask: Optional[str] = None,
                         sources: Optional[List[str]] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    Get a single directory person by resource name.
    
    This method retrieves a specific person from the Google Workspace directory.
    Directory people are users in your organization's Google Workspace domain.
    
    Args:
        resource_name (str): The resource name of the directory person to retrieve.
                            Must start with "directoryPeople/".
                            Example: "directoryPeople/123456789"
        read_mask (Optional[str]): A field mask to restrict which fields on each person are returned.
                                  Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                                  organizations, birthdays, photos, urls, userDefined, resourceName,
                                  etag, created, updated.
        sources (Optional[List[str]]): List of sources to retrieve data from. Valid sources include
                                      "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                                      "READ_SOURCE_TYPE_DOMAIN_PROFILE", "READ_SOURCE_TYPE_DIRECTORY".
    
    Returns:
        Dict[str, Union[str, List, Dict]]: A dictionary containing the directory person data with the same structure
                       as a regular person, but sourced from the directory.
    
    Raises:
        ValueError: If the resource name is invalid or the directory person is not found.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = GetDirectoryPersonRequest(
        resource_name=resource_name,
        read_mask=read_mask,
        sources=sources
    )
    
    logger.info(f"Getting directory person with resource name: {request.resource_name}")

    db = DB
    directory_people_data = db.get("directoryPeople", {})

    if request.resource_name not in directory_people_data:
        raise ValueError(f"Directory person with resource name '{request.resource_name}' not found")

    directory_person = directory_people_data[request.resource_name].copy()

    # Filter by read_mask if specified
    if request.read_mask:
        mask_fields = [field.strip() for field in request.read_mask.split(",")]
        filtered_person = {}
        for field in mask_fields:
            if field in directory_person:
                filtered_person[field] = directory_person[field]
        directory_person = filtered_person

    response_data = {
        "resourceName": request.resource_name,
        "etag": directory_person.get("etag", "etag123"),
        **directory_person
    }

    return response_data


@tool_spec(
    spec={
        'name': 'list_directory_people',
        'description': """ List directory people in the organization.
        
        This method retrieves a list of people from the Google Workspace directory.
        Directory people are users in your organization's Google Workspace domain. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'read_mask': {
                    'type': 'string',
                    'description': """ A field mask to restrict which fields on each person are returned.
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. """
                },
                'page_size': {
                    'type': 'integer',
                    'description': """ The number of directory people to include in the response.
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
def list_directory_people(read_mask: Optional[str] = None, page_size: Optional[int] = None,
                          page_token: Optional[str] = None, sync_token: Optional[str] = None,
                          request_sync_token: Optional[bool] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    List directory people in the organization.
    
    This method retrieves a list of people from the Google Workspace directory.
    Directory people are users in your organization's Google Workspace domain.
    
    Args:
        read_mask (Optional[str]): A field mask to restrict which fields on each person are returned.
                                  Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                                  organizations, birthdays, photos, urls, userDefined, resourceName,
                                  etag, created, updated.
        page_size (Optional[int]): The number of directory people to include in the response.
                                  Must be between 1 and 1000. Defaults to 100.
        page_token (Optional[str]): A page token, received from a previous response.
                                   Used for pagination.
        sync_token (Optional[str]): A sync token, received from a previous response.
                                   Used for incremental sync.
        request_sync_token (Optional[bool]): Whether the response should include a sync token.
                                            Defaults to False.
    
    Returns:
        Dict[str, Union[str, List, Dict]]: A dictionary containing the list of directory people with the following keys:
            - people (List[Dict]): List of directory person objects, each containing:
                - resourceName (str): Resource name of the directory person (e.g., "directoryPeople/123456789")
                - etag (str): ETag for the directory person record for versioning
                - names (Optional[List[Dict]]): List of name objects, each containing:
                    - displayName (Optional[str]): Full display name
                    - displayNameLastFirst (Optional[str]): Display name in last, first format
                    - givenName (Optional[str]): First name
                    - familyName (Optional[str]): Last name
                    - middleName (Optional[str]): Middle name
                    - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                    - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                    - phoneticGivenName (Optional[str]): Phonetic first name
                    - phoneticFamilyName (Optional[str]): Phonetic last name
                    - phoneticMiddleName (Optional[str]): Phonetic middle name
                    - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                    - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                    - unstructuredName (Optional[str]): Unstructured name
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                    - value (str): The nickname value
                    - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - emailAddresses (Optional[List[Dict]]): List of email address objects, each containing:
                    - value (str): The email address
                    - type (Optional[str]): Email type - "home", "work", "other"
                    - displayName (Optional[str]): Display name for the email
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                    - value (str): The phone number
                    - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - canonicalForm (Optional[str]): Canonical form of the phone number
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - addresses (Optional[List[Dict]]): List of address objects, each containing:
                    - type (Optional[str]): Address type - "home", "work", "other"
                    - formattedValue (Optional[str]): Full formatted address string
                    - streetAddress (Optional[str]): Street address line
                    - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                    - city (Optional[str]): City name
                    - region (Optional[str]): State/region name
                    - postalCode (Optional[str]): ZIP/postal code
                    - country (Optional[str]): Country name
                    - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                    - type (Optional[str]): Organization type - "work", "school", "other"
                    - name (Optional[str]): Organization name
                    - title (Optional[str]): Job title
                    - department (Optional[str]): Department name
                    - location (Optional[str]): Office location
                    - jobDescription (Optional[str]): Job description
                    - symbol (Optional[str]): Organization symbol/ticker
                    - domain (Optional[str]): Organization domain
                    - costCenter (Optional[str]): Cost center identifier
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                    - date (Optional[Dict]): Date components with year, month, day keys
                        - year (Optional[int]): Year
                        - month (Optional[int]): Month (1-12)
                        - day (Optional[int]): Day (1-31)
                    - text (Optional[str]): Text representation of birthday
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - photos (Optional[List[Dict]]): List of photo objects, each containing:
                    - url (Optional[str]): URL of the photo
                    - default (Optional[bool]): Whether this is the default photo
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - urls (Optional[List[Dict]]): List of URL objects, each containing:
                    - value (str): The URL
                    - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                    - key (str): Field key/name
                    - value (str): Field value
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - created (Optional[str]): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
                - updated (Optional[str]): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
            - nextPageToken (Optional[str]): Token for retrieving the next page of results
            - totalItems (Optional[int]): Total number of directory people available
            - nextSyncToken (Optional[str]): Token for incremental synchronization
    
    Raises:
        ValueError: If read_mask is not provided or parameters are invalid.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = ListDirectoryPeopleRequest(
        read_mask=read_mask,
        page_size=page_size,
        page_token=page_token,
        sync_token=sync_token,
        request_sync_token=request_sync_token
    )
    
    logger.info("Listing directory people")

    if not request.read_mask:
        raise ValueError("read_mask is required for list_directory_people")

    db = DB
    directory_people_data = db.get("directoryPeople", {})

    # Convert to list
    people = list(directory_people_data.values())

    # Filter by read_mask
    mask_fields = [field.strip() for field in request.read_mask.split(",")]
    filtered_people = []
    for person in people:
        filtered_person = {}
        for field in mask_fields:
            if field in person:
                filtered_person[field] = person[field]
        filtered_people.append(filtered_person)

    # Apply pagination
    if request.page_size:
        start_index = 0
        if request.page_token:
            try:
                start_index = int(request.page_token)
            except ValueError:
                start_index = 0

        end_index = start_index + request.page_size
        filtered_people = filtered_people[start_index:end_index]

        next_page_token = str(end_index) if end_index < len(directory_people_data) else None
    else:
        next_page_token = None

    response_data = {
        "people": filtered_people,
        "nextPageToken": next_page_token,
        "totalItems": len(filtered_people)
    }

    # Add sync token if requested
    if request.request_sync_token:
        response_data["nextSyncToken"] = f"sync_{generate_id()}"

    # Validate response using Pydantic model
    response = ListDirectoryPeopleResponse(**response_data)
    return response.dict(by_alias=True)


@tool_spec(
    spec={
        'name': 'search_directory_people',
        'description': """ Search for directory people in the organization.
        
        This method searches through the Google Workspace directory using a plain-text query.
        The search is performed across names, email addresses, and organization information. """,
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
                    Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                    organizations, birthdays, photos, urls, userDefined, resourceName,
                    etag, created, updated. """
                },
                'page_size': {
                    'type': 'integer',
                    'description': """ The number of directory people to include in the response.
                    Must be between 1 and 1000. Defaults to 100. """
                },
                'page_token': {
                    'type': 'string',
                    'description': """ A page token, received from a previous response.
                    Used for pagination. """
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
                'query'
            ]
        }
    }
)
def search_directory_people(query: str, read_mask: Optional[str] = None,
                            page_size: Optional[int] = None, page_token: Optional[str] = None,
                            sources: Optional[List[str]] = None) -> Dict[str, Union[str, List, Dict]]:
    """
    Search for directory people in the organization.
    
    This method searches through the Google Workspace directory using a plain-text query.
    The search is performed across names, email addresses, and organization information.
    
    Args:
        query (str): The plain-text query for the request. Must not be empty and cannot exceed 1000 characters.
                     The search is case-insensitive and performs partial matching.
        read_mask (Optional[str]): A field mask to restrict which fields on each person are returned.
                                  Valid fields: names, nicknames, emailAddresses, phoneNumbers, addresses,
                                  organizations, birthdays, photos, urls, userDefined, resourceName,
                                  etag, created, updated.
        page_size (Optional[int]): The number of directory people to include in the response.
                                  Must be between 1 and 1000. Defaults to 100.
        page_token (Optional[str]): A page token, received from a previous response.
                                   Used for pagination.
        sources (Optional[List[str]]): List of sources to retrieve data from. Valid sources include
                                      "READ_SOURCE_TYPE_PROFILE", "READ_SOURCE_TYPE_CONTACT",
                                      "READ_SOURCE_TYPE_DOMAIN_PROFILE", "READ_SOURCE_TYPE_DIRECTORY".
    
    Returns:
        Dict[str, Union[str, List, Dict]]: A dictionary containing the search results with the following keys:
            - results (List[Dict]): List of directory person objects matching the search query, each containing:
                - resourceName (str): Resource name of the directory person (e.g., "directoryPeople/123456789")
                - etag (str): ETag for the directory person record for versioning
                - names (Optional[List[Dict]]): List of name objects, each containing:
                    - displayName (Optional[str]): Full display name
                    - displayNameLastFirst (Optional[str]): Display name in last, first format
                    - givenName (Optional[str]): First name
                    - familyName (Optional[str]): Last name
                    - middleName (Optional[str]): Middle name
                    - honorificPrefix (Optional[str]): Title prefix (e.g., "Dr.", "Mr.")
                    - honorificSuffix (Optional[str]): Title suffix (e.g., "Jr.", "Sr.")
                    - phoneticGivenName (Optional[str]): Phonetic first name
                    - phoneticFamilyName (Optional[str]): Phonetic last name
                    - phoneticMiddleName (Optional[str]): Phonetic middle name
                    - phoneticHonorificPrefix (Optional[str]): Phonetic title prefix
                    - phoneticHonorificSuffix (Optional[str]): Phonetic title suffix
                    - unstructuredName (Optional[str]): Unstructured name
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - nicknames (Optional[List[Dict]]): List of nickname objects. Each nickname may contain:
                    - value (str): The nickname value
                    - type (Optional[str]): Nickname type - "DEFAULT", "ALTERNATE_NAME"
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - emailAddresses (Optional[List[Dict]]): List of email address objects, each containing:
                    - value (str): The email address
                    - type (Optional[str]): Email type - "home", "work", "other"
                    - displayName (Optional[str]): Display name for the email
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - phoneNumbers (Optional[List[Dict]]): List of phone number objects, each containing:
                    - value (str): The phone number
                    - type (Optional[str]): Phone type - "home", "work", "mobile", "homeFax", "workFax", "otherFax", "pager", "workMobile", "workPager", "main", "googleVoice", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - canonicalForm (Optional[str]): Canonical form of the phone number
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - addresses (Optional[List[Dict]]): List of address objects, each containing:
                    - type (Optional[str]): Address type - "home", "work", "other"
                    - formattedValue (Optional[str]): Full formatted address string
                    - streetAddress (Optional[str]): Street address line
                    - extendedAddress (Optional[str]): Extended address (apartment, suite, etc.)
                    - city (Optional[str]): City name
                    - region (Optional[str]): State/region name
                    - postalCode (Optional[str]): ZIP/postal code
                    - country (Optional[str]): Country name
                    - countryCode (Optional[str]): Country code (e.g., "US", "CA")
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - organizations (Optional[List[Dict]]): List of organization objects, each containing:
                    - type (Optional[str]): Organization type - "work", "school", "other"
                    - name (Optional[str]): Organization name
                    - title (Optional[str]): Job title
                    - department (Optional[str]): Department name
                    - location (Optional[str]): Office location
                    - jobDescription (Optional[str]): Job description
                    - symbol (Optional[str]): Organization symbol/ticker
                    - domain (Optional[str]): Organization domain
                    - costCenter (Optional[str]): Cost center identifier
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - birthdays (Optional[List[Dict]]): List of birthday objects, each containing:
                    - date (Optional[Dict]): Date components with year, month, day keys
                        - year (Optional[int]): Year
                        - month (Optional[int]): Month (1-12)
                        - day (Optional[int]): Day (1-31)
                    - text (Optional[str]): Text representation of birthday
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - photos (Optional[List[Dict]]): List of photo objects, each containing:
                    - url (Optional[str]): URL of the photo
                    - default (Optional[bool]): Whether this is the default photo
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - urls (Optional[List[Dict]]): List of URL objects, each containing:
                    - value (str): The URL
                    - type (Optional[str]): URL type - "home", "work", "blog", "profile", "homePage", "ftp", "reserved", "other"
                    - formattedType (Optional[str]): Human-readable type description
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - userDefined (Optional[List[Dict]]): List of user-defined field objects, each containing:
                    - key (str): Field key/name
                    - value (str): Field value
                    - metadata (Optional[Dict]): Field metadata containing:
                        - primary (Optional[bool]): Whether this is the primary field
                        - source (Optional[Dict]): Source information containing:
                        - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                        - id (Optional[str]): Unique identifier within the source type generated by the server
                        - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                        - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format containing:
                            - type (str): Source type - "SOURCE_TYPE_UNSPECIFIED", "ACCOUNT", "PROFILE", "DOMAIN_PROFILE", "CONTACT", "OTHER_CONTACT", "DOMAIN_CONTACT"
                            - id (Optional[str]): Unique identifier within the source type generated by the server
                            - etag (Optional[str]): HTTP entity tag of the source for web cache validation
                            - updateTime (Optional[str]): Last update timestamp in RFC3339 UTC format
                        - sourcePrimary (Optional[bool]): Whether the source is primary
                        - verified (Optional[bool]): Whether the field is verified
                - created (Optional[str]): Creation timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
                - updated (Optional[str]): Last update timestamp in ISO format (e.g., "2024-01-15T10:30:00Z")
            - nextPageToken (Optional[str]): Token for retrieving the next page of results
            - totalItems (int): Total number of search results found
    
    Raises:
        ValueError: If the query is empty or read_mask is not provided.
        ValidationError: If the input parameters fail validation.
    

    """
    # Validate input using Pydantic model
    request = SearchDirectoryPeopleRequest(
        query=query,
        read_mask=read_mask,
        page_size=page_size,
        page_token=page_token,
        sources=sources
    )
    
    logger.info(f"Searching directory people with query: {request.query}")

    if not request.read_mask:
        raise ValueError("read_mask is required for search_directory_people")

    db = DB
    directory_people_data = db.get("directoryPeople", {})

    # Simple search implementation
    results = []
    query_lower = request.query.lower()

    for person_id, person in directory_people_data.items():
        # Search in names
        names = person.get("names")
        if names is not None:
            for name in names:
                if name is not None:
                    display_name = (name.get("displayName") or "").lower()
                    given_name = (name.get("givenName") or "").lower()
                    family_name = (name.get("familyName") or "").lower()
                    if (query_lower in display_name or 
                        query_lower in given_name or 
                        query_lower in family_name):
                        results.append(person)
                        break

        # Search in email addresses
        emails = person.get("emailAddresses")
        if emails is not None:
            for email in emails:
                if email is not None:
                    email_value = (email.get("value") or "").lower()
                    if query_lower in email_value:
                        results.append(person)
                        break

        # Search in organizations
        orgs = person.get("organizations")
        if orgs is not None:
            for org in orgs:
                if org is not None:
                    org_name = (org.get("name") or "").lower()
                    org_title = (org.get("title") or "").lower()
                    if query_lower in org_name or query_lower in org_title:
                        results.append(person)
                        break

    # Remove duplicates
    unique_results = []
    seen_ids = set()
    for person in results:
        if person["resourceName"] not in seen_ids:
            unique_results.append(person)
            seen_ids.add(person["resourceName"])

    # Filter by read_mask
    mask_fields = [field.strip() for field in request.read_mask.split(",")]
    filtered_results = []
    for person in unique_results:
        filtered_person = {}
        for field in mask_fields:
            if field in person:
                filtered_person[field] = person[field]
        filtered_results.append(filtered_person)

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
    response = SearchDirectoryPeopleResponse(**response_data)
    return response.dict(by_alias=True)
