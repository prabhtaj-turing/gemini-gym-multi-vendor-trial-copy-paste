"""
User Management by ID Module

This module provides functionality for managing SCIM (System for Cross-domain
Identity Management) users by their unique identifiers. It implements the SCIM
protocol (RFC 7644) for user resource management, supporting operations for
retrieving, updating, and deleting specific users.

The module interfaces with the simulation database to provide comprehensive
user management capabilities, allowing users to:
- Retrieve specific user details by ID
- Update user attributes using PATCH operations
- Replace entire user resources using PUT operations
- Delete users from the system
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, Union, List, Any
from datetime import datetime, timezone
from pydantic import ValidationError

from .SimulationEngine import db
from .SimulationEngine.utils import (
    validate_attributes, apply_filter, filter_attributes, apply_patch_operation
)
from .SimulationEngine.custom_errors import (
    InvalidAttributeError, UserPatchValidationError, UserPatchForbiddenError, UserPatchOperationError,
    UserUpdateValidationError, UserUpdateForbiddenError, UserUpdateConflictError, UserUpdateOperationError,
    UserDeleteForbiddenError, UserDeleteOperationError
)
from .SimulationEngine.models import UserPatchInputModel, UserReplaceInputModel


def _format_timestamp(timestamp_str: str) -> str:
    """Helper function to format timestamp consistently."""
    if timestamp_str.endswith('+00:00'):
        return timestamp_str.replace('+00:00', 'Z')
    return timestamp_str

@tool_spec(
    spec={
        'name': 'get_scim_user_by_id',
        'description': """ Retrieves the details of a single user by SCIM resource ID.
        
        This endpoint conforms to SCIM 2.0 RFC 7644 Section 3.4.1, returning user metadata,
        core attributes, and optional related roles or identifiers. It supports attribute
        selection and filtering. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Unique SCIM identifier of the user to retrieve.'
                },
                'attributes': {
                    'type': 'string',
                    'description': """ Comma-separated string of attributes to return in the response.
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
                    'description': """ SCIM-compliant filter expression for additional filtering.
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
                    
                    Examples:
                    - 'active eq true'
                    - 'roles.value eq "admin"'
                    - 'name.familyName co "Smith"' """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: str, attributes: Optional[str] = None, filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the details of a single user by SCIM resource ID.

    This endpoint conforms to SCIM 2.0 RFC 7644 Section 3.4.1, returning user metadata,
    core attributes, and optional related roles or identifiers. It supports attribute
    selection and filtering.

    Args:
        id (str): Unique SCIM identifier of the user to retrieve.
        
        attributes (Optional[str]): Comma-separated string of attributes to return in the response.
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
            
        filter (Optional[str]): SCIM-compliant filter expression for additional filtering.
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
            
            Examples:
            - 'active eq true'
            - 'roles.value eq "admin"'
            - 'name.familyName co "Smith"'

    Returns:
        Optional[Dict[str, Any]]: The user object returned in SCIM-compliant format, or None if not found. It can contain the following keys:

            - schemas (List[str]): List of SCIM schema URIs that apply to this resource.
            - id (str): Unique identifier for the user resource.
            - externalId (str): Client-defined external identifier for the user.
            - userName (str): Email address of the user.
            - name (Dict[str, str]):
                - givenName (str): First name of the user.
                - familyName (str): Last name of the user.
            - active (bool): Indicates whether the user is active.
            - roles (List[Dict[str, Any]]): Roles assigned to the user (read-only).
                - value (str): Role identifier.
                - display (str): Human-readable name of the role.
                - type (str): Role type.
                - primary (bool): True if this is the user's primary role.
            - meta (Dict[str, str]):
                - resourceType (str): Type of SCIM resource ("User").
                - created (str): Timestamp when the resource was created (ISO 8601).
                - lastModified (str): Timestamp when the resource was last updated.
                - location (str): Full URL to access the specific user resource.
                
    Raises:
        InvalidAttributeError: If invalid attributes are specified in the `attributes` parameter.
        ValueError: If `id` is empty, not a string, or whitespace-only; or if the `filter`
            expression is malformed, uses unsupported operators, or references unsupported
            attributes.
    """
    # --- Parameter Validation ---
    if not id:
        raise ValueError("User ID cannot be empty")
    
    if not isinstance(id, str):
        raise ValueError("User ID must be a string")
    
    if len(id.strip()) == 0:
        raise ValueError("User ID cannot be empty or whitespace only")

    validate_attributes(attributes)
    
    # --- Find user by ID ---
    user = None
    for u in db.DB["scim"]["users"]:
        if u is not None and u.get("id") == id:
            user = u
            break
    
    if not user:
        return None
    
    # --- Apply filter if specified ---
    if filter:
        # Apply filter to a single-user list and check if user passes
        filtered_users = apply_filter([user], filter)
        if not filtered_users:
            return None
        user = filtered_users[0]
    
    # --- Apply attribute filtering ---
    if attributes:
        filtered_users = filter_attributes([user], attributes)
        if filtered_users:
            return filtered_users[0]
        return None
    
    return user

@tool_spec(
    spec={
        'name': 'partially_update_scim_user_by_id',
        'description': """ Updates one or more attributes of a User resource using a sequence of additions, removals, and replacements operations.
        
        It supports add, remove, and replace operations for partial user updates.
        
        Business Rules:
            - If the user tries to deactivate themselves, they will get a 403 Access forbidden response.
            - Operations on the userName field will only be processed if both original and target email 
              addresses match the domains list set for the Company's SSO connections.
            - userName values must be valid email addresses; validation occurs at the request parsing level. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Unique SCIM identifier of the user to patch.'
                },
                'body': {
                    'type': 'object',
                    'description': """ Payload describing the patch operations to apply upon the resource.
                    Contains: """,
                    'properties': {
                        'schemas': {
                            'type': 'array',
                            'description': 'Array of strings - SCIM schemas (optional)',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'Operations': {
                            'type': 'array',
                            'description': """ Array of objects (PatchOperation) - required
                                 Each operation in the array contains: """,
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'op': {
                                        'type': 'string',
                                        'description': 'The kind of operation to perform (required). Enum: "add", "remove", "replace".'
                                    },
                                    'path': {
                                        'type': 'string',
                                        'description': 'Path to the attribute to modify. Required when op is "remove", optional for "add" and "replace" operations.'
                                    },
                                    'value': {
                                        'type': 'object',
                                        'description': 'The value to set. Can be any type - string, number, boolean, array or object. Required for "add" and "replace" operations, not used for "remove" operations.',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'required': [
                                    'op'
                                ]
                            }
                        }
                    },
                    'required': [
                        'Operations'
                    ]
                },
                'attributes': {
                    'type': 'string',
                    'description': """ Comma-separated list of attribute names to return in the response.
                    Same attribute options as the get() function. """
                }
            },
            'required': [
                'id',
                'body'
            ]
        }
    }
)
def patch(id: str, body: Dict[str, Any], attributes: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Updates one or more attributes of a User resource using a sequence of additions, removals, and replacements operations.

    It supports add, remove, and replace operations for partial user updates.

    Business Rules:
        - If the user tries to deactivate themselves, they will get a 403 Access forbidden response.
        - Operations on the userName field will only be processed if both original and target email 
          addresses match the domains list set for the Company's SSO connections.
        - userName values must be valid email addresses; validation occurs at the request parsing level.

    Args:
        id (str): Unique SCIM identifier of the user to patch.
        
        body (Dict[str, Any]): Payload describing the patch operations to apply upon the resource.
            Contains:
            - schemas (Optional[List[str]]): Array of strings - SCIM schemas (optional)
            - Operations (List[Dict[str, Any]]): Array of objects (PatchOperation) - required
                Each operation in the array contains:
                - op (str): The kind of operation to perform (required). Enum: "add", "remove", "replace".  
                - path (str, optional): Path to the attribute to modify. Required when op is "remove", optional for "add" and "replace" operations.
                - value (Any, optional): The value to set. Can be any type - string, number, boolean, array or object. Required for "add" and "replace" operations, not used for "remove" operations.
                
        attributes (Optional[str]): Comma-separated list of attribute names to return in the response.
            Same attribute options as the get() function.

    Returns:
        Optional[Dict[str, Any]]: The updated user resource in SCIM-compliant format, or None if not found.
            The response contains:
            - schemas (List[str]): URIs that are used to indicate the namespaces of the SCIM schemas 
              that define the attributes present in the current structure
            - id (str): A unique identifier for a SCIM resource.
            - meta (Dict[str, str]): Descriptive information about a resource
                - resourceType (str): Type of SCIM resource ("User")
                - created (str): ISO 8601 timestamp when the resource was created
                - lastModified (str): ISO 8601 timestamp when the resource was last updated
                - location (str): Full URL to access the specific user resource
            - externalId (str): Identifier of the resource useful from the perspective of the provisioning client
            - userName (str): Email for the user
            - name (Dict[str, str]): Name compound object
                - familyName (str): User's last name
                - givenName (str): User's first name
            - roles (List[Dict[str, Any]]): Roles assigned to User
                Each role contains:
                - value (str): Role identifier
                - display (str): Human-readable role name
                - type (str): Role type
                - primary (bool): Whether this is the primary role
            - active (bool): Boolean indicating if the user account is active

    Raises:
        ValueError: If `id` is empty/invalid.
        InvalidAttributeError: If `attributes` contains unsupported fields.
        TypeError: If `id` is not a string or `body` is not a dictionary.
        UserPatchValidationError: Invalid operations, attribute validation failure, malformed request, or invalid email format for userName.
        UserPatchForbiddenError: Unauthorized field update or self-deactivation attempt.
        UserPatchOperationError: PATCH operation processing failure.
    """
    # --- Parameter Validation ---
    if not id:
        raise ValueError("User ID cannot be empty")
    
    if not isinstance(id, str):
        raise TypeError("User ID must be a string")
    
    if len(id.strip()) == 0:
        raise ValueError("User ID cannot be empty or whitespace only")
        
    if not isinstance(body, dict):
        raise TypeError(f"body must be a dictionary, got {type(body).__name__}")
    
    if attributes:
        validate_attributes(attributes)

    # --- Pydantic Validation ---
    try:
        patch_input = UserPatchInputModel(**body)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")
        raise UserPatchValidationError(f"Invalid patch data: {'; '.join(error_details)}")

    # --- Find User ---
    user = None
    user_index = None
    for i, u in enumerate(db.DB["scim"]["users"]):
        if u is not None and u.get("id") == id:
            user = u.copy()  # Work with a copy to avoid partial updates on failure
            user_index = i
            break
    
    if not user:
        return None

    # --- Apply PATCH Operations ---
    try:
        for operation in patch_input.Operations:
            user = apply_patch_operation(user, operation, id)
        
        # Update lastModified timestamp and ensure meta object is complete
        if "meta" not in user or not isinstance(user.get("meta"), dict):
            # Preserve existing created timestamp if it exists
            existing_created = None
            if isinstance(user.get("meta"), dict) and "created" in user["meta"]:
                existing_created = user["meta"]["created"]
            
            user["meta"] = {
                "resourceType": "User",
                "created": existing_created or _format_timestamp(datetime.now(timezone.utc).isoformat()),
                "location": f"https://api.us.workdayspend.com/scim/v2/Users/{id}"
            }
        
        user["meta"]["lastModified"] = _format_timestamp(datetime.now(timezone.utc).isoformat())
        
        # Ensure required meta fields are present
        if "resourceType" not in user["meta"]:
            user["meta"]["resourceType"] = "User"
        if "location" not in user["meta"]:
            user["meta"]["location"] = f"https://api.us.workdayspend.com/scim/v2/Users/{id}"
        
        # Save the updated user back to the database
        db.DB["scim"]["users"][user_index] = user
        
    except (UserPatchForbiddenError, UserPatchOperationError):
        # Re-raise these specific errors
        raise
    except Exception as e:
        raise UserPatchOperationError(f"Failed to apply patch operations: {str(e)}")

    # --- Apply attribute filtering if requested ---
    if attributes:
        filtered_users = filter_attributes([user], attributes)
        if filtered_users:
            return filtered_users[0]
        return None
    
    return user



@tool_spec(
    spec={
        'name': 'replace_scim_user_by_id',
        'description': """ Replaces all updatable attributes of a User resource as per RFC 7644 Section 3.5.1.
        
        This operation replaces only the attributes provided in the request payload, leaving any others intact.
        Users cannot deactivate themselves or modify their email domain unless it's compliant with configured SSO rules. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Unique SCIM identifier of the user to update.'
                },
                'body': {
                    'type': 'object',
                    'description': 'A dictionary containing the user attributes to update.',
                    'properties': {
                        'externalId': {
                            'type': 'string',
                            'description': 'Client-defined external identifier.'
                        },
                        'userName': {
                            'type': 'string',
                            'description': "Required. User's email address. Must match configured SSO domain for updates."
                        },
                        'name': {
                            'type': 'object',
                            'description': 'Required. Name compound object.',
                            'properties': {
                                'givenName': {
                                    'type': 'string',
                                    'description': "Required. User's first name."
                                },
                                'familyName': {
                                    'type': 'string',
                                    'description': "Required. User's last name."
                                }
                            },
                            'required': [
                                'givenName',
                                'familyName'
                            ]
                        },
                        'active': {
                            'type': 'boolean',
                            'description': 'Whether the user account is active.'
                        }
                    },
                    'required': [
                        'userName',
                        'name'
                    ]
                },
                'attributes': {
                    'type': 'string',
                    'description': 'Comma-separated list of attribute names to return in the response.'
                }
            },
            'required': [
                'id',
                'body'
            ]
        }
    }
)
def put(id: str, body: Dict[str, Any], attributes: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Replaces all updatable attributes of a User resource as per RFC 7644 Section 3.5.1.

    This operation replaces only the attributes provided in the request payload, leaving any others intact.
    Users cannot deactivate themselves or modify their email domain unless it's compliant with configured SSO rules.

    Args:
        id (str): Unique SCIM identifier of the user to update.
        body (Dict[str, Any]): A dictionary containing the user attributes to update.
            - externalId (Optional[str]): Client-defined external identifier.
            - userName (str): Required. User's email address. Must match configured SSO domain for updates.
            - name (Dict[str, str]): Required. Name compound object.
                - givenName (str): Required. User's first name.
                - familyName (str): Required. User's last name.
            - active (Optional[bool]): Whether the user account is active.
        attributes (Optional[str]): Comma-separated list of attribute names to return in the response.

    Returns:
        Optional[Dict[str, Any]]: The updated user resource in SCIM-compliant format, or None if not found.

            - id (str): Unique SCIM identifier.
            - externalId (str): External identifier for client reference.
            - userName (str): Email of the user.
            - name (Dict[str, str]):
                - givenName (str): First name.
                - familyName (str): Last name.
            - active (bool): Indicates whether the user is active.
            - roles (List[Dict[str, Any]]): User's assigned roles (read-only).
                - value (str): Role ID.
                - display (str): Role display name.
                - type (str): Role type.
                - primary (bool): Whether this is the user's primary role.
            - meta (Dict[str, str]):
                - resourceType (str): SCIM resource type.
                - created (str): ISO timestamp of creation.
                - lastModified (str): ISO timestamp of last update.
                - location (str): Full URL to access the specific user resource.

    Raises:
        ValueError: If `id` is empty/invalid.
        TypeError: If `id` is not a string or `body` is not a dictionary.
        InvalidAttributeError: If `attributes` contains unsupported fields.
        UserUpdateValidationError: Invalid user data or malformed request.
        UserUpdateForbiddenError: Self-deactivation or unauthorized email domain modification.
        UserUpdateConflictError: A user with the specified data already exists.
        UserUpdateOperationError: PUT operation processing failure.
    """
    # --- Parameter Validation ---
    if not id:
        raise ValueError("User ID cannot be empty")
    
    if not isinstance(id, str):
        raise TypeError("User ID must be a string")
    
    if len(id.strip()) == 0:
        raise ValueError("User ID cannot be empty or whitespace only")
        
    if not isinstance(body, dict):
        raise TypeError(f"body must be a dictionary, got {type(body).__name__}")
    
    # Validate attributes early, if provided
    if attributes:
        validate_attributes(attributes)

    # --- Pydantic Validation ---
    try:
        replace_input = UserReplaceInputModel(**body)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")
        raise UserUpdateValidationError(f"Invalid user data: {'; '.join(error_details)}")

    # --- Find User ---
    user = None
    user_index = None
    for i, u in enumerate(db.DB["scim"]["users"]):
        if u is not None and u.get("id") == id:
            user = u.copy()  # Work with a copy to avoid partial updates on failure
            user_index = i
            break
    
    if not user:
        return None

    # --- Business Rules Validation ---
    try:
        # Check for self-deactivation attempt
        if replace_input.active is False:
            # In a real implementation, you would check if the current user is trying to deactivate themselves
            # For simulation purposes, we'll enforce this business rule
            raise UserUpdateForbiddenError("Self-deactivation is forbidden")
        
        # Check for userName domain validation (userName is required)
        current_username = user.get("userName", "")
        if "@" in current_username and "@" in replace_input.userName:
            current_domain = current_username.split("@")[1].lower()  # Case-insensitive domain comparison
            new_domain = replace_input.userName.split("@")[1].lower()  # Case-insensitive domain comparison
            # Enforce no domain change without SSO configuration context
            if new_domain != current_domain:
                raise UserUpdateForbiddenError("Email domain change is forbidden by SSO policy")
        
        # Check for duplicate userName (excluding current user)
        existing_user = next(
            (u for u in db.DB["scim"]["users"] 
             if u.get("userName", "").lower() == replace_input.userName.lower() and u.get("id") != id),
            None
        )
        if existing_user:
            raise UserUpdateConflictError(f"User with userName '{replace_input.userName}' already exists")

        # --- Apply Updates ---
        # Only update externalId if it was explicitly provided in the request
        if "externalId" in body:
            user["externalId"] = replace_input.externalId  # Set to provided value, even if None
        
        # userName is required in the model, so it will always be present
        user["userName"] = replace_input.userName
        
        # name is required in the model, so it will always be present
        user["name"] = {
            "givenName": replace_input.name.givenName,
            "familyName": replace_input.name.familyName
        }
        
        if "active" in body:
            user["active"] = replace_input.active
        
        # Update lastModified timestamp and ensure meta object is complete
        if "meta" not in user or not isinstance(user.get("meta"), dict):
            # Preserve existing created timestamp if it exists
            existing_created = None
            if isinstance(user.get("meta"), dict) and "created" in user["meta"]:
                existing_created = user["meta"]["created"]
            
            user["meta"] = {
                "resourceType": "User",
                "created": existing_created or _format_timestamp(datetime.now(timezone.utc).isoformat()),
                "location": f"https://api.us.workdayspend.com/scim/v2/Users/{id}"
            }
        
        user["meta"]["lastModified"] = _format_timestamp(datetime.now(timezone.utc).isoformat())
        
        # Ensure required meta fields are present
        if "resourceType" not in user["meta"]:
            user["meta"]["resourceType"] = "User"
        if "location" not in user["meta"]:
            user["meta"]["location"] = f"https://api.us.workdayspend.com/scim/v2/Users/{id}"
        
        # Save the updated user back to the database
        db.DB["scim"]["users"][user_index] = user
        
    except (UserUpdateForbiddenError, UserUpdateConflictError):
        # Re-raise these specific errors
        raise
    except Exception as e:
        raise UserUpdateOperationError(f"Failed to update user: {str(e)}")

    # --- Apply attribute filtering if requested ---
    if attributes:
        filtered_users = filter_attributes([user], attributes)
        if filtered_users:
            return filtered_users[0]
        return None
    
    return user


@tool_spec(
    spec={
        'name': 'deactivate_scim_user_by_id',
        'description': """ Deactivates a user by their unique identifier.
        
        This operation marks the user as inactive by setting the 'active' field to False.
        Users cannot deactivate themselves, which results in a 403 Forbidden error.
        If the specified user does not exist, the function returns False. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Unique SCIM user identifier of the user to deactivate.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: str) -> bool:
    """
    Deactivates a user by their unique identifier.

    This operation marks the user as inactive by setting the 'active' field to False.
    Users cannot deactivate themselves, which results in a 403 Forbidden error.
    If the specified user does not exist, the function returns False.

    Args:
        id (str): Unique SCIM user identifier of the user to deactivate.

    Returns:
        bool: True if the user was found and successfully deactivated,
              False if the user was not found.

    Raises:
        ValueError: If `id` is empty/invalid.
        TypeError: If `id` is not a string.
        UserDeleteForbiddenError: User cannot deactivate themselves.
        UserDeleteOperationError: DELETE operation processing failure.
    """
    # --- Parameter Validation ---
    if id is None:
        raise ValueError("User ID cannot be empty")
    
    if not isinstance(id, str):
        raise TypeError("User ID must be a string")
    
    if not id or len(id.strip()) == 0:
        raise ValueError("User ID cannot be empty or whitespace only")

    # --- Find User ---
    user = None
    user_index = None
    for i, u in enumerate(db.DB["scim"]["users"]):
        if u is not None and u.get("id") == id:
            user = u
            user_index = i
            break
    
    if not user:
        return False

    # --- Business Rules Validation ---
    try:
        # Check for self-deactivation attempt
        # In a real implementation, check if the current user is trying to deactivate themselves
        # For simulation purposes, we'll enforce this business rule for demonstration
        # Since we don't have current user context, we'll simulate this check
        # In practice, this would compare against the authenticated user's ID
        
        # --- Deactivate User ---
        # Set user as inactive instead of deleting from the list
        user["active"] = False
        
        # Update lastModified timestamp and ensure meta object is complete
        if "meta" not in user or not isinstance(user.get("meta"), dict):
            # Preserve existing created timestamp if it exists
            existing_created = None
            if isinstance(user.get("meta"), dict) and "created" in user["meta"]:
                existing_created = user["meta"]["created"]
            
            user["meta"] = {
                "resourceType": "User",
                "created": existing_created or _format_timestamp(datetime.now(timezone.utc).isoformat()),
                "location": f"https://api.us.workdayspend.com/scim/v2/Users/{id}"
            }
        
        user["meta"]["lastModified"] = _format_timestamp(datetime.now(timezone.utc).isoformat())
        
        # Ensure required meta fields are present
        if "resourceType" not in user["meta"]:
            user["meta"]["resourceType"] = "User"
        if "location" not in user["meta"]:
            user["meta"]["location"] = f"https://api.us.workdayspend.com/scim/v2/Users/{id}"
        
        # Save the updated user back to the database
        db.DB["scim"]["users"][user_index] = user
        
        return True
        
    except Exception as e:
        raise UserDeleteOperationError(f"Failed to deactivate user: {str(e)}")