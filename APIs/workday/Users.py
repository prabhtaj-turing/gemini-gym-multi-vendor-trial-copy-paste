"""
SCIM Users Management Module

This module provides functionality for managing SCIM (System for Cross-domain
Identity Management) users in the Workday Strategic Sourcing system. It implements
the SCIM protocol (RFC 7644) for user resource management, supporting operations
for retrieving and creating users.

The module interfaces with the simulation database to provide comprehensive
user management capabilities, allowing users to:
- Retrieve lists of users with filtering, pagination, and sorting
- Create new users in the system
"""
from common_utils.tool_spec_decorator import tool_spec
import uuid
from typing import Optional, List, Dict, Any

from pydantic import ValidationError
from datetime import datetime, timezone

from .SimulationEngine import db
from .SimulationEngine.custom_errors import (ResourceConflictError, UserValidationError, UserCreationError,
                                             InvalidPaginationParameterError, InvalidSortByValueError,
                                             InvalidSortOrderValueError)
from .SimulationEngine.models import UserScimInputModel
from .SimulationEngine.utils import (
    validate_attributes, apply_filter, apply_sorting, filter_attributes
)


@tool_spec(
    spec={
        'name': 'list_scim_users',
        'description': """ Retrieves a list of SCIM users from the Workday Strategic Sourcing system.
        
        This operation is SCIM-compliant and supports filtering, pagination, sorting, and 
        attribute selection. It returns a SCIM ListResponse format with users and metadata. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'attributes': {
                    'type': 'string',
                    'description': """ Comma-separated list of attributes to return in the response.
                    Valid values:
                    - "userName": User's unique identifier (email address)
                    - "name": Complete name object with givenName and familyName
                    - "name.familyName": User's last name only
                    - "name.givenName": User's first name only
                    - "roles": Complete roles array with all role properties
                    - "roles.value": Only the role value field from roles
                    - "roles.display": Only the role display name from roles
                    - "roles.primary": Only the role primary flag from roles
                    - "roles.type": Only the role type field from roles
                    - "externalId": External system identifier for the user
                    - "active": Boolean indicating if user account is active
                    - "meta": Complete meta object with all metadata
                    - "meta.resourceType": Resource type from meta object
                    - "meta.created": ISO 8601 timestamp of creation
                    - "meta.lastModified": ISO 8601 timestamp of last modification
                    - "meta.location": Full URL to access the specific user resource
                    - "id": SCIM resource identifier (UUID)
                    - "schemas": SCIM schemas array """
                },
                'filter': {
                    'type': 'string',
                    'description': """ SCIM-compliant filter expression for searching users.
                    Supported filter attributes:
                    - userName, name, name.familyName, name.givenName, 
                      roles, roles.value, roles.display, roles.primary, roles.type,
                      externalId, active, meta, meta.resourceType, meta.created, meta.lastModified, meta.location, id, schemas
                      
                    Supported operators (case-insensitive):
                    - eq (equal): Exact match comparison
                    - ne (not equal): Non-matching comparison  
                    - co (contains): Substring match
                    - sw (starts with): Prefix match
                    - ew (ends with): Suffix match
                    - pr (present): Attribute has non-empty value
                    - gt (greater than): Lexicographical/chronological/numeric comparison
                    - ge (greater than or equal): Inclusive greater comparison
                    - lt (less than): Lexicographical/chronological/numeric comparison
                    - le (less than or equal): Inclusive lesser comparison
                    
                    Logical operators:
                    - and: Both expressions must be true
                    - or: Either expression must be true
                    - not: Expression must be false
                    
                    Grouping with parentheses () is supported.
                    Examples:
                    - 'userName eq "john.doe@example.com"'
                    - 'active eq true and name.familyName co "Smith"'
                    - 'meta.created gt "2024-01-01T00:00:00Z"'
                    - '(userName sw "admin" or roles.value eq "admin") and active eq true'
                    - 'not active eq false' (users where active is not false, i.e., active is true)
                    - 'not (userName sw "test")' (users whose userName doesn't start with "test") """
                },
                'startIndex': {
                    'type': 'integer',
                    'description': """ 1-based index of the first result to return. 
                    Must be >= 1. Default: 1 """
                },
                'count': {
                    'type': 'integer',
                    'description': 'Number of results to return per page. Must be >= 0. Default: 100'
                },
                'sortBy': {
                    'type': 'string',
                    'description': """ Attribute to sort results by.
                    Valid values:
                    - "id": Sort by SCIM resource identifier
                    - "externalId": Sort by external system identifier """
                },
                'sortOrder': {
                    'type': 'string',
                    'description': """ Sort direction.
                    Valid values:
                    - "ascending": Sort in ascending order (default)
                    - "descending": Sort in descending order """
                }
            },
            'required': []
        }
    }
)
def get(attributes: Optional[str] = None, filter: Optional[str] = None,
        startIndex: Optional[int] = None, count: Optional[int] = None,
        sortBy: Optional[str] = None, sortOrder: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves a list of SCIM users from the Workday Strategic Sourcing system.

    This operation is SCIM-compliant and supports filtering, pagination, sorting, and 
    attribute selection. It returns a SCIM ListResponse format with users and metadata.

    Args:
        attributes (Optional[str]): Comma-separated list of attributes to return in the response.
            Valid values:
            - "userName": User's unique identifier (email address)
            - "name": Complete name object with givenName and familyName
            - "name.familyName": User's last name only
            - "name.givenName": User's first name only
            - "roles": Complete roles array with all role properties
            - "roles.value": Only the role value field from roles
            - "roles.display": Only the role display name from roles
            - "roles.primary": Only the role primary flag from roles
            - "roles.type": Only the role type field from roles
            - "externalId": External system identifier for the user
            - "active": Boolean indicating if user account is active
            - "meta": Complete meta object with all metadata
            - "meta.resourceType": Resource type from meta object
            - "meta.created": ISO 8601 timestamp of creation
            - "meta.lastModified": ISO 8601 timestamp of last modification
            - "meta.location": Full URL to access the specific user resource
            - "id": SCIM resource identifier (UUID)
            - "schemas": SCIM schemas array
            
        filter (Optional[str]): SCIM-compliant filter expression for searching users.
            Supported filter attributes:
            - userName, name, name.familyName, name.givenName, 
              roles, roles.value, roles.display, roles.primary, roles.type,
              externalId, active, meta, meta.resourceType, meta.created, meta.lastModified, meta.location, id, schemas
              
            Supported operators (case-insensitive):
            - eq (equal): Exact match comparison
            - ne (not equal): Non-matching comparison  
            - co (contains): Substring match
            - sw (starts with): Prefix match
            - ew (ends with): Suffix match
            - pr (present): Attribute has non-empty value
            - gt (greater than): Lexicographical/chronological/numeric comparison
            - ge (greater than or equal): Inclusive greater comparison
            - lt (less than): Lexicographical/chronological/numeric comparison
            - le (less than or equal): Inclusive lesser comparison
            
            Logical operators:
            - and: Both expressions must be true
            - or: Either expression must be true
            - not: Expression must be false
            
            Grouping with parentheses () is supported.
            Examples:
            - 'userName eq "john.doe@example.com"'
            - 'active eq true and name.familyName co "Smith"'
            - 'meta.created gt "2024-01-01T00:00:00Z"'
            - '(userName sw "admin" or roles.value eq "admin") and active eq true'
            - 'not active eq false' (users where active is not false, i.e., active is true)
            - 'not (userName sw "test")' (users whose userName doesn't start with "test")
            
        startIndex (Optional[int]): 1-based index of the first result to return. 
            Must be >= 1. Default: 1
            
        count (Optional[int]): Number of results to return per page. Must be >= 0. Default: 100
            
        sortBy (Optional[str]): Attribute to sort results by.
            Valid values:
            - "id": Sort by SCIM resource identifier
            - "externalId": Sort by external system identifier
            
        sortOrder (Optional[str]): Sort direction.
            Valid values:
            - "ascending": Sort in ascending order (default)
            - "descending": Sort in descending order

    Returns:
        Dict[str, Any]: SCIM ListResponse containing the filtered and paginated user results:
            - schemas (List[str]): SCIM schemas, always ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
            - totalResults (int): Total number of users matching the filter criteria
            - startIndex (int): 1-based index of the first result returned in this response
            - itemsPerPage (int): Number of user resources included in this response
            - Resources (List[Dict[str, Any]]): Array of user resources, each containing:
                - schemas (List[str]): SCIM schemas for user, ["urn:ietf:params:scim:schemas:core:2.0:User"]
                - id (str): Unique SCIM resource identifier (UUID)
                - externalId (str): External system identifier for the user
                - userName (str): User's unique identifier, typically an email address
                - name (Dict[str, str]): User's name components.
                    - givenName (str): User's first name.
                    - familyName (str): User's last name.
                - active (bool): User account status (true for active, false for inactive)
                - roles (List[Dict[str, Any]]): User roles.
                    - value (str): Role identifier.
                    - display (str): Human-readable role name.
                    - primary (bool): Whether this is the primary role.
                    - type (str): Role type.
                - meta (Dict[str, str]): Metadata about the user.
                    - resourceType (str): Resource type, always "User".
                    - created (str): ISO 8601 creation timestamp.
                    - lastModified (str): ISO 8601 modification timestamp.
                    - location (str): Full URL to access the specific user resource.

    Raises:
        InvalidAttributeError: If invalid attributes are specified in the attributes parameter.
        InvalidPaginationParameterError: If startIndex < 1 or count < 0.
        InvalidSortByValueError: If sortBy value is not "id" or "externalId".
        InvalidSortOrderValueError: If sortOrder is not "ascending" or "descending".
        ValueError: If filter expression is malformed, uses unsupported operators,
                   or references unsupported attributes.
    """
    # --- Parameter Validation ---
    validate_attributes(attributes)
    # --- Pagination Validation ---
    if startIndex is not None:
        if not isinstance(startIndex, int):
            raise InvalidPaginationParameterError("startIndex must be an integer")
        if startIndex < 1:
            raise InvalidPaginationParameterError("startIndex must be greater than or equal to 1")
    
    if count is not None:
        if not isinstance(count, int):
            raise InvalidPaginationParameterError("count must be an integer")
        if count < 0:
            raise InvalidPaginationParameterError("count must be greater than or equal to 0")
    
    if sortBy is not None:
        if not isinstance(sortBy, str):
            raise InvalidSortByValueError("sortBy must be a string")
        allowed_sort_by = {"id", "externalId"}
        if sortBy not in allowed_sort_by:
            raise InvalidSortByValueError(
                f"Invalid sortBy value: '{sortBy}'. Allowed values: {', '.join(sorted(allowed_sort_by))}"
            )
    
    if sortOrder is not None:
        if not isinstance(sortOrder, str):
            raise InvalidSortOrderValueError("sortOrder must be a string")
        allowed_sort_order = {"ascending", "descending"}
        if sortOrder not in allowed_sort_order:
            raise InvalidSortOrderValueError(
                f"Invalid sortOrder value: '{sortOrder}'. Allowed values: {', '.join(sorted(allowed_sort_order))}"
            )
    
    # --- Get all users from database ---
    all_users = db.DB["scim"]["users"].copy()
    
    # --- Apply filtering ---
    if filter:
        all_users = apply_filter(all_users, filter)
    
    # --- Apply sorting ---
    if sortBy:
        all_users = apply_sorting(all_users, sortBy, sortOrder or "ascending")
    
    # --- Apply pagination ---
    start_idx = (startIndex or 1) - 1  # Convert to 0-based index
    page_size = count if count is not None else 100  # Default page size of 100
    
    if page_size == 0:
        paginated_users = []
    else:
        paginated_users = all_users[start_idx:start_idx + page_size]
    
    # --- Apply attribute filtering ---
    if attributes:
        paginated_users = filter_attributes(paginated_users, attributes)
    
    # --- Build SCIM ListResponse ---
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(all_users),
        "startIndex": startIndex or 1,
        "itemsPerPage": len(paginated_users),
        "Resources": paginated_users
    }


@tool_spec(
    spec={
        'name': 'create_scim_user',
        'description': """ Creates a new SCIM user in the Workday Strategic Sourcing system.
        
        This operation is SCIM-compliant and requires a payload defining the user details.
        It validates the input data using Pydantic models and creates a new user record
        in the Workday Strategic Sourcing database. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': 'The user data to create. Must contain:',
                    'properties': {
                        'userName': {
                            'type': 'string',
                            'description': 'Unique username, typically an email address'
                        },
                        'name': {
                            'type': 'object',
                            'description': "User's name components",
                            'properties': {
                                'givenName': {
                                    'type': 'string',
                                    'description': "User's first name"
                                },
                                'familyName': {
                                    'type': 'string',
                                    'description': "User's last name"
                                }
                            },
                            'required': [
                                'givenName',
                                'familyName'
                            ]
                        },
                        'schemas': {
                            'type': 'array',
                            'description': "SCIM schemas, typically ['urn:ietf:params:scim:schemas:core:2.0:User']",
                            'items': {
                                'type': 'string'
                            }
                        },
                        'externalId': {
                            'type': 'string',
                            'description': 'External identifier for the user'
                        },
                        'active': {
                            'type': 'boolean',
                            'description': 'Whether the user account is active (defaults to True)'
                        },
                        'roles': {
                            'type': 'array',
                            'description': 'Roles assigned to the user',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'value': {
                                        'type': 'string',
                                        'description': 'Role identifier. Required, if the roles is provided.'
                                    },
                                    'display': {
                                        'type': 'string',
                                        'description': 'Human-readable role name.'
                                    },
                                    'primary': {
                                        'type': 'boolean',
                                        'description': 'Whether this is the primary role.'
                                    },
                                    'type': {
                                        'type': 'string',
                                        'description': 'Role type.'
                                    }
                                },
                                'required': [
                                    'value'
                                ]
                            }
                        }
                    },
                    'required': [
                        'userName',
                        'name'
                    ]
                }
            },
            'required': [
                'body'
            ]
        }
    }
)
def post(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new SCIM user in the Workday Strategic Sourcing system.

    This operation is SCIM-compliant and requires a payload defining the user details.
    It validates the input data using Pydantic models and creates a new user record
    in the Workday Strategic Sourcing database.

    Args:
        body (Dict[str, Any]): The user data to create. Must contain:
            - userName (str): Unique username, typically an email address
            - name (Dict[str, str]): User's name components
                - givenName (str): User's first name
                - familyName (str): User's last name
            - schemas (Optional[List[str]]): SCIM schemas, typically ['urn:ietf:params:scim:schemas:core:2.0:User']
            - externalId (Optional[str]): External identifier for the user
            - active (Optional[bool]): Whether the user account is active (defaults to True)
            - roles (Optional[List[Dict[str, Any]]]): Roles assigned to the user
                    - value (str): Role identifier. Required, if the roles is provided.
                    - display (Optional[str]): Human-readable role name.
                    - primary (Optional[bool]): Whether this is the primary role.
                    - type (Optional[str]): Role type.

    Returns:
        Dict[str, Any]: The created user record with generated fields:
            - id (str): Unique SCIM resource identifier
            - externalId (str): Client-specific resource identifier
            - userName (str): User's email address
            - name (Dict[str, str]): User's name components
                - givenName (str): User's first name.
                - familyName (str): User's last name.
            - roles (List[Dict[str, Any]]): Roles assigned to the user
                - value (str): Role identifier.
                - display (str): Human-readable role name.
                - primary (bool): Whether this is the primary role.
                - type (str): Role type.
            - active (bool): User account status
            - meta (Dict[str, str]): Metadata including timestamps
                - resourceType (str): Resource type, always "User".
                - created (str): ISO 8601 creation timestamp.
                - lastModified (str): ISO 8601 modification timestamp.
                - location (str): Full URL to access the specific user resource.
            - schemas (List[str]): SCIM schemas

    Raises:
        TypeError: If body is not a dictionary.
        UserValidationError: If the input data fails Pydantic validation.
        ResourceConflictError: If a user with the same userName already exists.
        UserCreationError: If user creation fails for any other reason.
    """
    # --- Input Type Validation ---
    if not isinstance(body, dict):
        raise TypeError(f"body must be a dictionary, got {type(body).__name__}")

    # --- Pydantic Validation ---
    try:
        user_input = UserScimInputModel(**body)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")
        raise UserValidationError(f"Invalid user data: {'; '.join(error_details)}")

    # --- Business Logic Validation ---
    # Check for duplicate userName (case-insensitive for email addresses)
    existing_user = next(
        (user for user in db.DB["scim"]["users"] if user is not None and user.get("userName", "").lower() == user_input.userName.lower()),
        None
    )
    if existing_user:
        raise ResourceConflictError(f"User with userName '{user_input.userName}' already exists")

    # --- Generate User Record ---
    # Generate unique ID and timestamps
    user_id = str(uuid.uuid4())
    def _format_timestamp(timestamp_str: str) -> str:
        """Helper function to format timestamp consistently."""
        if timestamp_str.endswith('+00:00'):
            return timestamp_str.replace('+00:00', 'Z')
        return timestamp_str
    
    current_time = _format_timestamp(datetime.now(timezone.utc).isoformat())
    # Create the user record
    new_user = {
        "id": user_id,
        "schemas": user_input.schemas or ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "externalId": user_input.externalId,
        "userName": user_input.userName,
        "name": {
            "givenName": user_input.name.givenName,
            "familyName": user_input.name.familyName
        },
        "active": user_input.active if user_input.active is not None else True,
        "roles": [role.model_dump() for role in user_input.roles] if user_input.roles else [],
        "meta": {
            "resourceType": "User",
            "created": current_time,
            "lastModified": current_time,
            "location": f"https://api.us.workdayspend.com/scim/v2/Users/{user_id}"
        }
    }

    # --- Save to Database ---
    try:
        db.DB["scim"]["users"].append(new_user)
    except Exception as e:
        raise UserCreationError(f"Failed to create user in database: {str(e)}")

    return new_user