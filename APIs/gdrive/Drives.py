"""
Drives resource for Google Drive API simulation.

This module provides methods for managing shared drives in the Google Drive API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
import base64
import time
import json
import re

import datetime
from typing import Dict, Any, Optional, Union, List

from pydantic import ValidationError # To catch Pydantic validation errors

from .SimulationEngine.utils import _parse_query, _apply_query_filter, create_quote_replacer
from .SimulationEngine.counters import _next_counter
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import NotFoundError
from .SimulationEngine.models import DriveUpdateBodyModel, CreateDriveBodyInputModel
from .SimulationEngine.custom_errors import NotFoundError
from .SimulationEngine.custom_errors import InvalidQueryError


@tool_spec(
    spec={
        'name': 'create_shared_drive',
        'description': """ Creates a shared drive. If requestId is provided, it's used as the drive's ID and for idempotency.
        
        Otherwise, an internal ID is generated. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'requestId': {
                    'type': 'string',
                    'description': """ An ID, such as a random UUID. If provided, this ID is used
                    as the drive's ID. If a drive with this ID already exists,
                    it is returned. If None or empty, an internal ID is
                    generated for a new drive. """
                },
                'body': {
                    'type': 'object',
                    'description': 'Dictionary of drive properties. Valid keys:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The name of the shared drive.'
                        },
                        'restrictions': {
                            'type': 'object',
                            'description': 'A dictionary of restrictions to apply to the drive, with keys:',
                            'properties': {
                                'adminManagedRestrictions': {
                                    'type': 'boolean',
                                    'description': 'Whether administrative privileges on this shared drive are required to modify restrictions.'
                                },
                                'copyRequiresWriterPermission': {
                                    'type': 'boolean',
                                    'description': 'Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters.'
                                },
                                'domainUsersOnly': {
                                    'type': 'boolean',
                                    'description': 'Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs.'
                                },
                                'driveMembersOnly': {
                                    'type': 'boolean',
                                    'description': 'Whether access to items inside this shared drive is restricted to its members.'
                                }
                            },
                            'required': []
                        },
                        'hidden': {
                            'type': 'boolean',
                            'description': 'Whether the shared drive is hidden from default view.'
                        },
                        'themeId': {
                            'type': 'string',
                            'description': 'The ID of the theme to apply to this shared drive.'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def create(requestId: Optional[str] = None,
           body: Optional[Dict[str, Union[str, bool, Dict[str, bool]]]] = None,
           ) -> Dict[str, Union[str, bool, Dict[str, bool]]]:
    """Creates a shared drive. If requestId is provided, it's used as the drive's ID and for idempotency.
    Otherwise, an internal ID is generated.

    Args:
        requestId (Optional[str]): An ID, such as a random UUID. If provided, this ID is used
                                   as the drive's ID. If a drive with this ID already exists,
                                   it is returned. If None or empty, an internal ID is
                                   generated for a new drive.
        body (Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]): Dictionary of drive properties. Valid keys:
            - 'name' (Optional[str]): The name of the shared drive.
            - 'restrictions' (Optional[Dict[str, bool]]): A dictionary of restrictions to apply to the drive. All restriction fields are optional and default to False when not provided. Valid keys:
                - 'adminManagedRestrictions' (Optional[bool]): Whether administrative privileges on this shared drive are required to modify restrictions. Defaults to False.
                - 'copyRequiresWriterPermission' (Optional[bool]): Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters. Defaults to False.
                - 'domainUsersOnly' (Optional[bool]): Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs. Defaults to False.
                - 'driveMembersOnly' (Optional[bool]): Whether access to items inside this shared drive is restricted to its members. Defaults to False.
            - 'hidden' (Optional[bool]): Whether the shared drive is hidden from default view.
            - 'themeId' (Optional[str]): The ID of the theme to apply to this shared drive.

    Returns:
        Dict[str, Union[str, bool, Dict[str, bool]]]:  A dictionary representing the created or existing shared or existing drive, containing the following keys::
            - 'kind' (str): Resource type identifier (e.g., 'drive#drive').
            - 'id' (str): Drive ID (this will be the requestId if provided, otherwise an internally generated ID).
            - 'name' (str): The name of the shared drive.
            - 'restrictions' (Dict[str, Union[str, bool, Dict[str, bool]]]): Dictionary of restrictions. All fields are optional and default to False when not provided. Contains keys:
                - 'adminManagedRestrictions' (bool): Whether administrative privileges on this shared drive are required to modify restrictions. Defaults to False.
                - 'copyRequiresWriterPermission' (bool): Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters. Defaults to False.
                - 'domainUsersOnly' (bool): Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs. Defaults to False.
                - 'driveMembersOnly' (bool): Whether access to items inside this shared drive is restricted to its members. Defaults to False.
            - 'hidden' (bool): Whether the shared drive is hidden from default view.
            - 'themeId' (str): The ID of the theme applied to this shared drive.
            - 'createdTime' (str): The time at which the shared drive was created.
            - 'owners' (List[str]): List of email addresses of the drive owners.
            - 'permissions' (List[Dict[str, Any]]): List of permissions for the drive, each with keys:
                - 'id' (str): Permission ID.
                - 'role' (str): Permission role.
                - 'type' (str): Permission type.
                - 'emailAddress' (str): Email address of the permission.


    Raises:
        TypeError: If 'requestId' is provided and is not a string.
        ValidationError: If 'body' is provided and does not conform to the expected structure.
        """
    # --- Input Validation Start ---
    if requestId is not None and not isinstance(requestId, str):
        raise TypeError("requestId must be a string if provided.")

    if body is not None and not isinstance(body, dict):
        raise TypeError("body must be a dictionary.")
    
    # Pydantic validation for the 'body' dictionary argument
    validated_body_model: Optional[CreateDriveBodyInputModel] = None
    if body is not None:
        try:
            validated_body_model = CreateDriveBodyInputModel(**body)
        except ValidationError as e:
            # Just re-raise the original error
            raise
    # --- Input Validation End ---

    userId = 'me'

    actual_drive_id: str
    drive_name_default_suffix: str

    if requestId:  # If requestId is provided (not None and not empty string)
        # Check for idempotency: if a drive with this ID (requestId) already exists, return it.
        if requestId in DB['users'][userId]['drives']:
            return DB['users'][userId]['drives'][requestId]

        actual_drive_id = requestId
        drive_name_default_suffix = requestId
    else:  # requestId is None or empty
        drive_id_num = _next_counter('drive')  # Assume this function exists
        actual_drive_id = f"drive_{drive_id_num}"
        drive_name_default_suffix = str(drive_id_num)

    if body is None:
        body = {}

    # Use validated data if available, otherwise fall back to original body
    validated_data = validated_body_model.model_dump(exclude_unset=True) if validated_body_model else body

    # Determine the name for the new drive
    # Default name is based on the drive ID suffix
    now = datetime.datetime.now(datetime.UTC).isoformat() + 'Z'
    
    # Handle restrictions with proper defaults as per official API
    restrictions = validated_data.get('restrictions', {})
    if restrictions:
        # Ensure all restriction fields have proper boolean defaults (False if not provided)
        default_restrictions = {
            'adminManagedRestrictions': False,
            'copyRequiresWriterPermission': False,
            'domainUsersOnly': False,
            'driveMembersOnly': False
        }
        # Merge provided restrictions with defaults
        restrictions = {**default_restrictions, **restrictions}
    
    # Define user email
    user_email = DB['users'][userId]['about'].get('user', {}).get('emailAddress', 'user@example.com')

    # Add default owner permission
    permissions = [{
        'id': 'permission_' + actual_drive_id,
        'role': 'owner',
        'type': 'user',
        'emailAddress': user_email
    }]
    
    # Create base drive structure
    new_drive = {
        'kind': 'drive#drive',
        'id': actual_drive_id, 
        'name': validated_data.get('name', f'Drive_{drive_name_default_suffix}'),
        'hidden': validated_data.get('hidden', False),
        'themeId': validated_data.get('themeId', None),
        'restrictions': restrictions,
        'createdTime': now,
        'owners': [user_email],
        'permissions': permissions
    }

    # Store in DB and return
    if 'drives' not in DB['users'][userId]:
        DB['users'][userId]['drives'] = {}
    DB['users'][userId]['drives'][actual_drive_id] = new_drive
    return new_drive

@tool_spec(
    spec={
        'name': 'delete_shared_drive',
        'description': """ Permanently deletes a shared drive for which the user is an organizer.
        
        This function permanently removes a shared drive from the user's account. The drive
        must be identified by its unique `driveId`. For the operation to succeed, the user
        must have the appropriate permissions (e.g., be an organizer) for the specified drive.
        Once deleted, the drive and all of its contents are irretrievably lost. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The unique identifier of the shared drive to be deleted.'
                }
            },
            'required': [
                'driveId'
            ]
        }
    }
)
def delete(driveId: str) -> None:
    """Permanently deletes a shared drive for which the user is an organizer.
    
    This function permanently removes a shared drive from the user's account. The drive
    must be identified by its unique `driveId`. For the operation to succeed, the user
    must have the appropriate permissions (e.g., be an organizer) for the specified drive.
    Once deleted, the drive and all of its contents are irretrievably lost.

    Args:
        driveId (str): The unique identifier of the shared drive to be deleted.

    Returns:
        None

    Raises:
        TypeError: If driveId is not a string.
        NotFoundError: If no drive with the specified `driveId` is found.
    """
    userId = 'me'

    # Input validation
    if not isinstance(driveId, str) or not driveId.strip():
        raise TypeError("driveId must be a non-empty string.")
    
    if driveId not in DB.get('users', {}).get(userId, {}).get('drives', {}):
        raise NotFoundError(f"Drive with ID '{driveId}' not found.")

    DB['users'][userId]['drives'].pop(driveId, None)

    return None

@tool_spec(
    spec={
        'name': 'get_shared_drive_metadata',
        'description': "Gets a shared drive's metadata by ID.",
        'parameters': {
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The ID of the shared drive.'
                }
            },
            'required': [
                'driveId'
            ]
        }
    }
)
def get(driveId: str) -> Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]:
    """Gets a shared drive's metadata by ID.
    
    Args:
        driveId (str): The ID of the shared drive.
        
    Returns:
        Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]: Dictionary containing the drive metadata with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#drive').
            - 'id' (str): Drive ID.
            - 'name' (str): The name of the shared drive.
            - 'restrictions' (Dict[str, bool]): Dictionary of restrictions with keys:
                - 'adminManagedRestrictions' (bool): Whether administrative privileges on this shared drive are required to modify restrictions.
                - 'copyRequiresWriterPermission' (bool): Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters.
                - 'domainUsersOnly' (bool): Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs.
                - 'driveMembersOnly' (bool): Whether access to items inside this shared drive is restricted to its members.
            - 'hidden' (bool): Whether the shared drive is hidden from default view.
            - 'themeId' (str): The ID of the theme applied to this shared drive.
            - 'createdTime' (str): The time at which the shared drive was created.
        Returns None if the drive with the specified ID is not found.

    Raises:
        TypeError: If driveId is not a string or is empty.
    """
    # --- Input Validation Start ---
    if not isinstance(driveId, str):
        raise TypeError("driveId must be a string.")
    
    if not driveId.strip():
        raise TypeError("driveId must be a non-empty string.")
    # --- Input Validation End ---
    
    userId = 'me'  # Assuming 'me' for now
    return DB['users'][userId]['drives'].get(driveId)

@tool_spec(
    spec={
        'name': 'hide_shared_drive',
        'description': 'Hides a shared drive from the default view.',
        'parameters': {
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The ID of the shared drive to hide. Must be a non-empty string.'
                }
            },
            'required': [
                'driveId'
            ]
        }
    }
)
def hide(driveId: str,
        ) -> Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]:
    """Hides a shared drive from the default view.
    
    Args:
        driveId (str): The ID of the shared drive to hide. Must be a non-empty string.
        
    Returns:
        Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]: The hidden drive resource object if successful, or None if the drive doesn't exist.
            If successful, the dictionary contains:
            - 'kind' (str): Resource type identifier ('drive#drive').
            - 'id' (str): Drive ID.
            - 'name' (str): The name of the shared drive.
            - 'restrictions' (Dict[str, bool]): Dictionary of restrictions (if present).
                - 'adminManagedRestrictions' (bool): Whether administrative privileges on this shared drive are required to modify restrictions.
                - 'copyRequiresWriterPermission' (bool): Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters.
                - 'domainUsersOnly' (bool): Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs.
                - 'driveMembersOnly' (bool): Whether access to items inside this shared drive is restricted to its members.
            - 'hidden' (bool): Always True after successful hide operation.
            - 'themeId' (str): The ID of the theme applied to this shared drive (if present).
            - 'createdTime' (str): The time at which the shared drive was created (if present).
            
    Raises:
        ValueError: If driveId is None, empty, or not a string.
    """
    # Input validation
    if not isinstance(driveId, str):
        raise ValueError("driveId must be a string")
    if not driveId or not driveId.strip():
        raise ValueError("driveId cannot be empty or whitespace")

    # Normalize driveId by stripping whitespace
    driveId = driveId.strip()

    userId = 'me'  # Assuming 'me' for now

    # Retrieve the drive from the database
    drive = DB['users'][userId]['drives'].get(driveId)

    if drive is None:
        # Drive doesn't exist - return None
        return None

    # Set the hidden flag
    drive['hidden'] = True

    return drive

@tool_spec(
    spec={
        'name': 'list_user_shared_drives',
        'description': """ Lists the user's shared drives.
        
        This function returns a list of shared drives that the user is a member of.
        It supports filtering by drive properties through the `q` parameter
        and allows for pagination using `pageSize` and `pageToken`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'pageSize': {
                    'type': 'integer',
                    'description': """ Maximum number of shared drives to return per page.
                    Must be an integer between 1 and 100. """
                },
                'q': {
                    'type': 'string',
                    'description': """ Query string for searching shared drives. 
                 The query supports any field present in the drive resource object, like:
                    - 'id' (str): The ID of the shared drive.
                    - 'name' (str): The name of the shared drive. Only supports the following operators: contains, =, !=
                    - 'createdTime' (str): The time at which the shared drive was created (e.g., `'2024-01-01T00:00:00Z'`). Only supports the following operators: <=, <, =, !=, >, >=.
                    - 'hidden' (bool): Whether the shared drive is hidden from default view.
                 Operators: =, !=, <, <=, >, >=, contains, in
                 You can combine conditions with 'and', 'or', and 'not'.
                 `not` operator is always used in the first position of the term, for instance,
                 `not name = 'My Drive'` is valid, but `name not = 'My Drive' is not valid.
                 Parentheses are supported for explicitly grouping conditions (e.g., `(name = 'My Drive' or name = 'Our Drive') and hidden =  false`,
                 `(name = 'My Drive' and hidden = false) or (name = 'Our Drive' and hidden = false)`).
                 String values must be quoted. Example queries:
                     - "name = 'My Drive'"
                     - "name contains 'Project' and hidden = false"
                     - "createdTime >= '2023-01-01T00:00:00Z'"
                     - "name = 'Team Drive' or hidden = false"
                 Note:
                       - The contains operator only performs prefix matching for a name term. For example, suppose you have a name of HelloWorld. A query of name contains 'Hello' returns a result, but a query of name contains 'World' doesn't.
                       - The contains operator only performs matching on entire string tokens for the fullText term. For example, if the full text of a document contains the string "HelloWorld", only the query fullText contains 'HelloWorld' returns a result.
                       - The contains operator matches on an exact alphanumeric phrase if the right operand is surrounded by double quotes. For example, if the fullText of a document contains the string "Hello there world", then the query fullText contains "Hello there" returns a result, but the query fullText contains "Hello world" doesn't. Furthermore, since the search is alphanumeric, if the full text of a document contains the string "Hello_world", then the query fullText contains "Hello world" returns a result. """
                },
                'pageToken': {
                    'type': 'string',
                    'description': """ (Optional) A base64-encoded token for pagination. The token encodes a JSON object with:
                    - 'last_row_time' (str): The unix timestamp (as a string) when the last page was generated.
                    - 'offset' (int): The offset (index) to start the next page from. """
                },
                'useDomainAdminAccess': {
                    'type': 'boolean',
                    'description': """ (Optional) Issue the request as a domain administrator; 
                    if set to true, then all shared drives of the domain in which the 
                    requester is an administrator are returned. Default is false. """
                }
            },
            'required': []
        }
    }
)
def list(pageSize: int = 10, q: str = '', pageToken: str = '', useDomainAdminAccess: bool = False) -> Dict[str, Union[str, List[Dict[str, Union[str, bool]]]]]:
    """Lists the user's shared drives.

    This function returns a list of shared drives that the user is a member of.
    It supports filtering by drive properties through the `q` parameter
    and allows for pagination using `pageSize` and `pageToken`.

    Args:
        pageSize (int): Maximum number of shared drives to return per page.
                        Must be an integer between 1 and 100.
        q (str): Query string for searching shared drives. 
                 The query supports any field present in the drive resource object, like:
                    - 'id' (str): The ID of the shared drive.
                    - 'name' (str): The name of the shared drive. Only supports the following operators: contains, =, !=
                    - 'createdTime' (str): The time at which the shared drive was created (e.g., `'2024-01-01T00:00:00Z'`). Only supports the following operators: <=, <, =, !=, >, >=.
                    - 'hidden' (bool): Whether the shared drive is hidden from default view.
                 Operators: =, !=, <, <=, >, >=, contains, in
                 You can combine conditions with 'and', 'or', and 'not'.
                 `not` operator is always used in the first position of the term, for instance,
                 `not name = 'My Drive'` is valid, but `name not = 'My Drive' is not valid.
                 Parentheses are supported for explicitly grouping conditions (e.g., `(name = 'My Drive' or name = 'Our Drive') and hidden =  false`,
                 `(name = 'My Drive' and hidden = false) or (name = 'Our Drive' and hidden = false)`).
                 String values must be quoted. Example queries:
                     - "name = 'My Drive'"
                     - "name contains 'Project' and hidden = false"
                     - "createdTime >= '2023-01-01T00:00:00Z'"
                     - "name = 'Team Drive' or hidden = false"
                 Note:
                       - The contains operator only performs prefix matching for a name term. For example, suppose you have a name of HelloWorld. A query of name contains 'Hello' returns a result, but a query of name contains 'World' doesn't.
                       - The contains operator only performs matching on entire string tokens for the fullText term. For example, if the full text of a document contains the string "HelloWorld", only the query fullText contains 'HelloWorld' returns a result.
                       - The contains operator matches on an exact alphanumeric phrase if the right operand is surrounded by double quotes. For example, if the fullText of a document contains the string "Hello there world", then the query fullText contains "Hello there" returns a result, but the query fullText contains "Hello world" doesn't. Furthermore, since the search is alphanumeric, if the full text of a document contains the string "Hello_world", then the query fullText contains "Hello world" returns a result.
        pageToken (str): (Optional) A base64-encoded token for pagination. The token encodes a JSON object with:
            - 'last_row_time' (str): The unix timestamp (as a string) when the last page was generated.
            - 'offset' (int): The offset (index) to start the next page from.
        useDomainAdminAccess (bool): (Optional) Issue the request as a domain administrator; 
                                     if set to true, then all shared drives of the domain in which the 
                                     requester is an administrator are returned. Default is false.


    Returns:
        Dict[str, Union[str, List[Dict[str, Union[str, bool]]]]]: Dictionary containing the list of shared drives with keys:
            - 'drives' (List[Dict[str, Union[str, bool]]]): List of shared drive objects, each with keys:
                - 'id' (str): Drive ID.
                - 'name' (str): The name of the shared drive.
                - 'kind' (str): API kind.
                - 'createdTime' (str): The time at which the shared drive was created.
                - 'hidden' (bool): Whether the shared drive is hidden from default view.
            - 'kind' (str): Resource type identifier (e.g., 'drive#driveList').
            - 'nextPageToken' (str): Page token for the next page of results.

    
    Raises:
        TypeError: If `pageSize` is not an integer or `q` is not a string.
        ValueError: If `pageSize` is negative or greater than 100.
        InvalidQueryError: If `q` is provided and is not a valid query string.
    """
    userId = 'me'

    # --- Input Validation ---
    if not isinstance(pageSize, int):
        raise TypeError("pageSize must be an integer.")
    
    if pageSize <= 0 or pageSize > 100:
        raise ValueError("pageSize must be an integer between 1 and 100.")

    if not isinstance(q, str):
        raise TypeError("q must be a string.")
    if not isinstance(pageToken, str):
        raise TypeError("pageToken must be a string.")
    if not isinstance(useDomainAdminAccess, bool):
        raise TypeError("useDomainAdminAccess must be a boolean.")
    # --- End of Input Validation ---
    # TODO: Implement logic for useDomainAdminAccess.
    # This would require accessing drives outside of the current user's scope.
    # For now, we proceed with the user's drives.


    # Get all drives for the user
    drives_list = [x for x in DB['users'][userId]['drives'].values()]

    # Apply query filtering if q is provided
    if q:
        # Create a quote replacement callback and placeholder map
        replace_quotes, placeholder_map = create_quote_replacer()
        
        # Find and replace all quoted strings (both single and double quotes)
        protected_q = re.sub(r"(['\"])(?:(?=(\\?))\2.)*?\1", replace_quotes, q)
        
        # Use placeholders to avoid conflicts between operators (e.g., = and !=)
        operator_map = {
            '!=': ' __NE__ ',
            '<=': ' __LE__ ',
            '>=': ' __GE__ ',
            '=': ' __EQ__ ',
            '<': ' __LT__ ',
            '>': ' __GT__ '
        }
        
        # Replace operators in the protected query (without quotes)
        for op, placeholder in operator_map.items():
            protected_q = protected_q.replace(op, placeholder).replace("  "," ")
        
        # Restore operators with proper spacing
        for placeholder, op in {v: k for k, v in operator_map.items()}.items():
            protected_q = protected_q.replace(placeholder, f' {op} ')
        
        # Restore the quoted strings using the placeholder map
        for placeholder, original_quote in placeholder_map.items():
            protected_q = protected_q.replace(placeholder, original_quote)
        
        # Use the protected query
        q = protected_q
        
        # Check for balanced quotes
        quote_count = q.count("'") + q.count('"')
        if quote_count % 2 != 0:
            raise ValueError("Query string contains unbalanced quotes")

        try:
            conditions = _parse_query(q)  # This returns a list of condition groups
            drives_list = _apply_query_filter(drives_list, conditions, resource_type='drive')
        except Exception as e:
            raise InvalidQueryError(f"Invalid query string: '{q}' with error: {e}")

    # Pagination logic
    offset = 0
    if pageToken:
        try:
            decoded = base64.urlsafe_b64decode(pageToken.encode('utf-8')).decode('utf-8')
            token_data = json.loads(decoded)
            offset = int(token_data.get('offset', 0))
        except Exception:
            offset = 0  # fallback to 0 if token is invalid

    paged_drives = drives_list[offset:offset + pageSize]
    next_offset = offset + pageSize

    if next_offset < len(drives_list):
        next_token_data = {
            "last_row_time": str(int(time.time())),
            "offset": next_offset
        }
        nextPageToken = base64.urlsafe_b64encode(json.dumps(next_token_data).encode('utf-8')).decode('utf-8')
    else:
        nextPageToken = None

    return {
        'kind': 'drive#driveList',
        'nextPageToken': nextPageToken,
        'drives': paged_drives
    }

@tool_spec(
    spec={
        'name': 'unhide_shared_drive',
        'description': 'Restores a shared drive to the default view.',
        'parameters': {
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The ID of the shared drive.'
                }
            },
            'required': [
                'driveId'
            ]
        }
    }
)
def unhide(driveId: str,
          ) -> Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]:
    """Restores a shared drive to the default view.
    
    Args:
        driveId (str): The ID of the shared drive.
        
    Returns:
        Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]: Dictionary containing the unhidden drive with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#drive').
            - 'id' (str): Drive ID.
            - 'name' (str): The name of the shared drive.
            - 'restrictions' (Dict[str, bool]): Dictionary of restrictions with keys:
                - 'adminManagedRestrictions' (bool): Whether administrative privileges on this shared drive are required to modify restrictions.
                - 'copyRequiresWriterPermission' (bool): Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters.
                - 'domainUsersOnly' (bool): Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs.
                - 'driveMembersOnly' (bool): Whether access to items inside this shared drive is restricted to its members.
            - 'hidden' (bool): Whether the shared drive is hidden from default view.
            - 'themeId' (str): The ID of the theme applied to this shared drive.
            - 'createdTime' (str): The time at which the shared drive was created.
        Returns None if the drive with the specified ID is not found.

    Raises:
        TypeError: If driveId is not a string or is empty.
    """
    # --- Input Validation Start ---
    if not isinstance(driveId, str):
        raise TypeError("driveId must be a string.")
    
    if not driveId.strip():
        raise TypeError("driveId must be a non-empty string.")
    # --- Input Validation End ---
    
    userId = 'me'  # Assuming 'me' for now
    drive = DB['users'][userId]['drives'].get(driveId)
    if drive and drive.get('hidden'):
        drive['hidden'] = False
    return drive

@tool_spec(
    spec={
        'name': 'update_shared_drive_metadata',
        'description': """ Updates the metadata for a shared drive.
        
        This function modifies an existing shared drive's metadata based on the
        provided `body`. The drive is identified by its `driveId`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The ID of the shared drive.'
                },
                'body': {
                    'type': 'object',
                    'description': 'A dictionary representing the metadata fields to be updated on the shared drive.',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The name of the shared drive.'
                        },
                        'restrictions': {
                            'type': 'object',
                            'description': 'Dictionary of restrictions with keys:',
                            'properties': {
                                'adminManagedRestrictions': {
                                    'type': 'boolean',
                                    'description': 'Whether administrative privileges on this shared drive are required to modify restrictions.'
                                },
                                'copyRequiresWriterPermission': {
                                    'type': 'boolean',
                                    'description': 'Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters.'
                                },
                                'domainUsersOnly': {
                                    'type': 'boolean',
                                    'description': 'Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs.'
                                },
                                'driveMembersOnly': {
                                    'type': 'boolean',
                                    'description': 'Whether access to items inside this shared drive is restricted to its members.'
                                }
                            },
                            'required': []
                        },
                        'hidden': {
                            'type': 'boolean',
                            'description': 'Whether the shared drive is hidden from default view.'
                        },
                        'themeId': {
                            'type': 'string',
                            'description': 'The ID of the theme to apply to this shared drive.'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'driveId'
            ]
        }
    }
)
def update(driveId: str,
          body: Optional[Dict[str, Union[str, bool, Dict[str, bool]]]] = None,
          ) -> Dict[str, Union[str, bool, Dict[str, bool]]]:
    """Updates the metadata for a shared drive.

    This function modifies an existing shared drive's metadata based on the
    provided `body`. The drive is identified by its `driveId`.
    
    Args:
        driveId (str): The ID of the shared drive.
        body (Optional[Dict[str, Union[str, bool, Dict[str, bool]]]]): A dictionary representing the metadata fields to be updated on the shared drive.
            - 'name' (Optional[str]): The name of the shared drive.
            - 'restrictions' (Optional[Dict[str, bool]]): Dictionary of restrictions with keys:
                - 'adminManagedRestrictions' (Optional[bool]): Whether administrative privileges on this shared drive are required to modify restrictions.
                - 'copyRequiresWriterPermission' (Optional[bool]): Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters.
                - 'domainUsersOnly' (Optional[bool]): Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs.
                - 'driveMembersOnly' (Optional[bool]): Whether access to items inside this shared drive is restricted to its members.
            - 'hidden' (Optional[bool]): Whether the shared drive is hidden from default view.
            - 'themeId' (Optional[str]): The ID of the theme to apply to this shared drive.

    Returns:
        Dict[str, Union[str, bool, Dict[str, bool]]]: Dictionary containing the updated drive with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#drive').
            - 'id' (str): Drive ID.
            - 'name' (str): The name of the shared drive.
            - 'restrictions' (Dict[str, bool]): Dictionary of restrictions with keys:
                - 'adminManagedRestrictions' (bool): Whether administrative privileges on this shared drive are required to modify restrictions.
                - 'copyRequiresWriterPermission' (bool): Whether the options to copy, print, or download files inside this shared drive, should be disabled for readers and commenters.
                - 'domainUsersOnly' (bool): Whether access to this shared drive and items inside this shared drive is restricted to users of the domain to which this shared drive belongs.
                - 'driveMembersOnly' (bool): Whether access to items inside this shared drive is restricted to its members.
            - 'hidden' (bool): Whether the shared drive is hidden from default view.
            - 'themeId' (str): The ID of the theme applied to this shared drive.
            - 'createdTime' (str): The time at which the shared drive was created.
            Note:
                Some fields in the returned drive data (e.g., 'restrictions') may be present as empty dictionaries (`{}`)
                if they were empty before the update and the update request does not assign a non-empty value to them.

    Raises:
        TypeError: If 'driveId' is not a non-empty string or 'body' is not a dictionary.
        ValidationError: If 'body' is provided and does not conform to the DriveUpdateBodyModel structure
                                  (e.g., incorrect types for fields, disallowed extra fields).
        NotFoundError: If no drive with the specified `driveId` is found.

    """
    # --- Input Validation Start ---
    userId = 'me'  # Define userId for DB access

    # Standard type validation for non-dictionary arguments
    if not isinstance(driveId, str) or not driveId.strip():
        raise TypeError(f"driveId must be a non-empty string")

    # Pydantic validation for the 'body' dictionary argument
    validated_body = {}
    if body is not None:
        if not isinstance(body, dict):
            raise TypeError(f"body must be a dictionary or None, but got {type(body).__name__}")
        
        try:
            # Validate the structure of the 'body' dictionary using Pydantic
            # The model will handle checking for extra fields since it has model_config = {"extra": "forbid"}
            parsed_body_model = DriveUpdateBodyModel(**body)
            # Get a dictionary of fields that were actually provided in the input,
            # excluding those not set. This is suitable for PATCH-like updates.
            validated_body = parsed_body_model.model_dump(exclude_unset=True)
        except ValidationError as e:
            # Simply pass the Pydantic validation error through our custom ValidationError
            raise e
    
    # --- Input Validation End ---

    existing = DB['users'][userId]['drives'].get(driveId)
    if not existing:
        raise NotFoundError(f"Drive with ID '{driveId}' not found.")

    # Handle restrictions separately to merge instead of replace
    if 'restrictions' in validated_body:
        # Get existing restrictions or initialize empty dict
        existing_restrictions = existing.get('restrictions', {})
        # Merge new restrictions with existing ones (new values override existing)
        merged_restrictions = {**existing_restrictions, **validated_body['restrictions']}
        # Remove restrictions from validated_body to handle it separately
        validated_body_without_restrictions = {k: v for k, v in validated_body.items() if k != 'restrictions'}
        # Update all other fields
        existing.update(validated_body_without_restrictions)
        # Update restrictions with merged values
        existing['restrictions'] = merged_restrictions
    else:
        # Use the validated_body_data for the update operation
        existing.update(validated_body)

    return existing