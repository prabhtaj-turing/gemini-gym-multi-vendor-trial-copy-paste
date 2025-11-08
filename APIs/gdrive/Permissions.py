"""
Permissions resource for Google Drive API simulation.

This module provides methods for managing permissions in the Google Drive API simulation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional

from pydantic import ValidationError

from .SimulationEngine.utils import _ensure_file, _ensure_user, _user_can_grant_permissions, _validate_permission_request_security, _map_ui_role_to_api_role
from .SimulationEngine.counters import _next_counter
from .SimulationEngine.db import DB

from .SimulationEngine.custom_errors import ResourceNotFoundError, PermissionDeniedError, LastOwnerDeletionError, NotFoundError
from .SimulationEngine.models import PermissionBodyUpdateModel, PermissionBodyModel, PermissionListModel


@tool_spec(
    spec={
        'name': 'create_permission',
        'description': 'Creates a permission for a file or shared drive.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file or shared drive.'
                },
                'body': {
                    'type': 'object',
                    'description': 'A permission resource to be created, specifying the grantee and their level of access.',
                    'properties': {
                        'role': {
                            'type': 'string',
                            'description': """ The role granted by this permission, defaults to 'reader'. Supports both API and UI role names (case-insensitive):
                                - 'reader'/'viewer': Can view the file
                                - 'writer'/'editor': Can view, comment, and edit the file
                                - 'commenter'/'commenter': Can view and comment on the file
                                - 'owner'/'owner': Has full control over the file
                                - 'organizer'/'manager': Can manage content and users in shared drives
                                - 'fileOrganizer'/'content manager': Can manage content in shared drives
                                - 'writer'/'contributor': Can view, comment, and edit files in shared drives """
                        },
                        'type': {
                            'type': 'string',
                            'description': """ The type of the grantee, defaults to 'user'. Possible values:
                                 - 'user': Permission granted to a specific user
                                - 'group': Permission granted to a group
                                - 'domain': Permission granted to a domain
                                - 'anyone': Permission granted to anyone with the link """
                        },
                        'emailAddress': {
                            'type': 'string',
                            'description': 'The email address of the user or group to grant the permission to. This will be normalized to lowercase.'
                        },
                        'domain': {
                            'type': 'string',
                            'description': "The domain name (e.g. 'example.com') of the entity this permission refers to. Required when type='domain'."
                        },
                        'allowFileDiscovery': {
                            'type': 'boolean',
                            'description': 'Whether the permission allows the file to be discovered through search, defaults to False.'
                        },
                        'expirationTime': {
                            'type': 'string',
                            'description': "The time at which this permission will expire, in RFC 3339 format. Example: `'2025-06-30T12:00:00Z'` (UTC) or `'2025-06-30T08:00:00-04:00'`."
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
# The `PermissionBodyModel` Pydantic model allows the role 'organizer', but this role is not defined in the `function_calling_schema` or the function's docstring. This allows undocumented data to be saved, which can cause issues for API consumers who rely on the public schema.
def create(fileId: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Creates a permission for a file or shared drive.

    Args:
        fileId (str): The ID of the file or shared drive.
        body (Optional[Dict[str, Any]]): A permission resource to be created, specifying the grantee and their level of access.
            - 'role'(Optional[str]): The role granted by this permission, defaults to 'reader'. Supports both API and UI role names (case-insensitive):
                - 'reader'/'viewer': Can view the file
                - 'writer'/'editor': Can view, comment, and edit the file
                - 'commenter'/'commenter': Can view and comment on the file
                - 'owner'/'owner': Has full control over the file
                - 'organizer'/'manager': Can manage content and users in shared drives
                - 'fileOrganizer'/'content manager': Can manage content in shared drives
                - 'writer'/'contributor': Can view, comment, and edit files in shared drives
            - 'type'(Optional[str]): The type of the grantee, defaults to 'user'. Possible values:
                - 'user': Permission granted to a specific user
                - 'group': Permission granted to a group
                - 'domain': Permission granted to a domain
                - 'anyone': Permission granted to anyone with the link
            - 'emailAddress'(Optional[str]): The email address of the user or group to grant the permission to. This will be normalized to lowercase.
            - 'domain'(Optional[str]): The domain name (e.g. 'example.com') of the entity this permission refers to. Required when type='domain'.
            - 'allowFileDiscovery'(Optional[bool]): Whether the permission allows the file to be discovered through search, defaults to False.
            - 'expirationTime'(Optional[str]): The time at which this permission will expire, in RFC 3339 format. Example: `'2025-06-30T12:00:00Z'` (UTC) or `'2025-06-30T08:00:00-04:00'`.

    Returns:
        Dict[str, Any]: Dictionary containing the created permission with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#permission').
            - 'id' (str): Permission ID.
            - 'role' (str): The role granted by this permission.
            - 'type' (str): The type of the grantee.
            - 'emailAddress' (str): The email address of the user or group.
            - 'domain' (str): The domain name of the entity this permission refers to.
            - 'allowFileDiscovery' (bool): Whether the permission allows the file to be discovered through search.
            - 'expirationTime' (str): The time at which this permission will expire, in RFC 3339 format.

    Raises:
        TypeError: If `fileId` is not a string.
        ValueError: If `fileId` is an empty string.
        ResourceNotFoundError: If `fileId` is not found in user's files or shared drives.
        ValidationError: If `body` is provided and does not conform to the
            required structure (e.g., invalid 'role' or 'type' values,
            incorrect data type for 'allowFileDiscovery', missing 'domain' field when type='domain').
        PermissionDeniedError: If the user does not have permission to grant the requested permission type.
    """
    # --- Start of Added Validation Logic ---
    # Validate 'fileId'
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not fileId.strip():  # Ensure fileId is not empty or just whitespace
        raise ValueError("fileId cannot be an empty string.")

    # Validate 'body' using Pydantic model if it's provided
    if body is not None:
        try:
            PermissionBodyModel(**body)
        except ValidationError as e:
            raise e
    # --- End of Added Validation Logic ---

    userId = 'me'  # Assuming 'me' for now

    # --- SECURITY: Authorization Checks ---
    target_container = None
    target_resource = None
    
    if fileId in DB['users'][userId]['files']:
        target_container = DB['users'][userId]['files']
        target_resource = target_container[fileId]
    elif fileId in DB['users'][userId]['drives']:
        target_container = DB['users'][userId]['drives']
        target_resource = target_container[fileId]
    else:
        raise ResourceNotFoundError(f"Resource with ID '{fileId}' not found.")

    # SECURITY CHECK 1: Verify user has permission to grant permissions on this resource
    if not _user_can_grant_permissions(userId, target_resource):
        raise PermissionDeniedError(f"User '{userId}' does not have permission to grant permissions on resource '{fileId}'.")

    # SECURITY CHECK 2: Validate permission request against security policies
    if body is not None:
        _validate_permission_request_security(userId, body, target_resource)

    _processed_body = body if body is not None else {}

    permission_id_num = _next_counter('permission')
    permission_id = f"permission_{permission_id_num}"

    # Map UI roles to API roles if needed
    role = _processed_body.get('role', 'reader')
    # mapped_role = _map_ui_role_to_api_role(role)
    
    # normalize email address
    email_address = _processed_body.get('emailAddress', '')
    if email_address:
        email_address = email_address.lower().strip()

    new_permission = {
        'kind': 'drive#permission',
        'id': permission_id,
        # 'role': mapped_role,
        'role': role,
        'type': _processed_body.get('type', 'user'),
        'emailAddress': email_address,
        'domain': _processed_body.get('domain', ''),
        'allowFileDiscovery': _processed_body.get('allowFileDiscovery', False),
        'expirationTime': _processed_body.get('expirationTime', '')
    }

    # Save the permission
    if 'permissions' not in target_container[fileId]:
        target_container[fileId]['permissions'] = []
    target_container[fileId]['permissions'].append(new_permission)

    # If granting owner permission, add to owners list
    if new_permission['role'] == 'owner' and new_permission['type'] == 'user' and new_permission['emailAddress']:
        if 'owners' not in target_container[fileId]:
            target_container[fileId]['owners'] = []
        if new_permission['emailAddress'] not in target_container[fileId]['owners']:
            target_container[fileId]['owners'].append(new_permission['emailAddress'])

    return new_permission

@tool_spec(
    spec={
        'name': 'delete_permission',
        'description': 'Deletes a permission.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file or shared drive.'
                },
                'permissionId': {
                    'type': 'string',
                    'description': 'The ID of the permission to delete.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support all drives. Defaults to False.'
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support team drives. Defaults to False.'
                },
                'useDomainAdminAccess': {
                    'type': 'boolean',
                    'description': 'Whether to use domain admin access. Defaults to False.'
                }
            },
            'required': [
                'fileId',
                'permissionId'
            ]
        }
    }
)
def delete(fileId: str,
          permissionId: str,
          supportsAllDrives: Optional[bool] = False,
          supportsTeamDrives: Optional[bool] = False,
          useDomainAdminAccess: Optional[bool] = False) -> Dict[str, str]:
    """Deletes a permission.

    Args:
        fileId (str): The ID of the file or shared drive.
        permissionId (str): The ID of the permission to delete.
        supportsAllDrives (Optional[bool]): Whether to support all drives. Defaults to False.
        supportsTeamDrives (Optional[bool]): Whether to support team drives. Defaults to False.
        useDomainAdminAccess (Optional[bool]): Whether to use domain admin access. Defaults to False.

    Returns:
        Dict[str, str]: Dictionary containing:
            - 'status' (str): Success status indicator
            - 'message' (str): Confirmation message
    
    Raises:
        TypeError: If `fileId` or `permissionId` is not a string, or if any of
                   the boolean flags are not booleans.
        ValueError: If `fileId` or `permissionId` is an empty or whitespace-only string.
        ResourceNotFoundError: If the specified `fileId` or `permissionId` cannot be found.
        PermissionDeniedError: If the user lacks sufficient permissions. For shared drive
                               items, 'organizer' role is required. For other items,
                               'owner' or 'editor' (writer) is required, though editors
                               cannot remove owners.
        LastOwnerDeletionError: If an attempt is made to delete the permission of the
                                last owner of a file.        
    """
    # --- Input Validation ---
    if not isinstance(fileId, str):
        raise TypeError("Argument 'fileId' must be a string.")
    if not fileId.strip():
        raise ValueError("Argument 'fileId' cannot be an empty string.")
    if not isinstance(permissionId, str):
        raise TypeError("Argument 'permissionId' must be a string.")
    if not permissionId.strip():
        raise ValueError("Argument 'permissionId' cannot be an empty string.")
    if not isinstance(supportsAllDrives, bool):
        raise TypeError("Argument 'supportsAllDrives' must be a boolean.")
    if not isinstance(supportsTeamDrives, bool):
        raise TypeError("Argument 'supportsTeamDrives' must be a boolean.")
    if not isinstance(useDomainAdminAccess, bool):
        raise TypeError("Argument 'useDomainAdminAccess' must be a boolean.")

    # --- Core Logic ---
    userId = 'me'
    user_email = DB['users'][userId]['about']['user']['emailAddress']

    # Locate the target file or drive
    target_resource = None
    is_in_shared_drive = False
    if (supportsAllDrives or supportsTeamDrives) and fileId in DB['users'][userId].get('drives', {}):
        target_resource = DB['users'][userId]['drives'][fileId]
        is_in_shared_drive = True
    elif fileId in DB['users'][userId]['files']:
        target_resource = DB['users'][userId]['files'][fileId]
        # Check if the file is in a shared drive via its properties
        if target_resource.get('driveId'):
            is_in_shared_drive = True
    else:
        raise ResourceNotFoundError(f"File or drive with ID '{fileId}' not found.")

    # Find the permission to delete
    permissions = target_resource.get('permissions', [])
    permission_to_delete = None
    permission_index = -1
    for i, p in enumerate(permissions):
        if p.get('id') == permissionId:
            permission_to_delete = p
            permission_index = i
            break

    if not permission_to_delete:
        raise ResourceNotFoundError(f"Permission with ID '{permissionId}' not found on file '{fileId}'.")

    # --- Authorization and Business Rule Checks ---

    # 1. Check if the user has the authority to delete the permission
    can_delete = False
    
    # For shared drives, check permissions directly (no owners concept)
    if is_in_shared_drive and 'owners' not in target_resource:
        # Shared drives don't have owners, only permissions
        user_permission = next((p for p in permissions if p.get('emailAddress') == user_email), None)
        user_role = user_permission.get('role') if user_permission else None
        
        # In shared drives, only organizers can manage permissions
        if user_role == 'organizer':
            can_delete = True
    else:
        # For files, check both ownership and permissions
        is_owner = any(
            (owner.get('emailAddress') if isinstance(owner, dict) else owner) == user_email
            for owner in target_resource.get('owners', [])
        )
        
        user_permission = next((p for p in permissions if p.get('emailAddress') == user_email), None)
        user_role = user_permission.get('role') if user_permission else None
        
        # In "My Drive", owners can delete anyone. Editors can delete non-owners.
        if is_owner:
            can_delete = True
        elif user_role in ['editor', 'writer'] and permission_to_delete.get('role') != 'owner':
            can_delete = True

    if useDomainAdminAccess:
        can_delete = True
            
    if not can_delete:
        raise PermissionDeniedError(f"User '{user_email}' does not have sufficient permissions to modify permissions on file '{fileId}'.")

    # 2. Prevent deletion of the last owner (this check is always important)
    if permission_to_delete.get('role') == 'owner':
        owner_permissions = [p for p in permissions if p.get('role') == 'owner']
        if len(owner_permissions) == 1:
            raise LastOwnerDeletionError(
                "Cannot remove the last owner of a file. Transfer ownership first."
            )

    # --- Perform Deletion ---
    del target_resource['permissions'][permission_index]

    return {"status": "success", "message": "Permission has been deleted."}

@tool_spec(
    spec={
        'name': 'get_permission',
        'description': """ Gets a permission by ID.
        
        Retrieves a specific permission by its ID for the specified file. The function
        supports various access patterns including shared drives and domain admin access. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file or shared drive. Must be a non-empty string.'
                },
                'permissionId': {
                    'type': 'string',
                    'description': 'The ID of the permission to retrieve. Must be a non-empty string.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether the requesting application supports both My Drives 
                    and shared drives. Defaults to False. """
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': """ Whether to support team drives. Deprecated - use 
                    supportsAllDrives instead. Defaults to False. """
                },
                'useDomainAdminAccess': {
                    'type': 'boolean',
                    'description': """ Issue the request as a domain administrator. If set to 
                    true, grants access if the file ID refers to a shared drive and the requester 
                    is an administrator of the domain to which the shared drive belongs. Defaults to False. """
                }
            },
            'required': [
                'fileId',
                'permissionId'
            ]
        }
    }
)
def get(fileId: str,
       permissionId: str,
       supportsAllDrives: bool = False,
       supportsTeamDrives: bool = False,
       useDomainAdminAccess: bool = False,
       ) -> Optional[Dict[str, Any]]:
    """Gets a permission by ID.
    
    Retrieves a specific permission by its ID for the specified file. The function
    supports various access patterns including shared drives and domain admin access.
    
    Args:
        fileId (str): The ID of the file or shared drive. Must be a non-empty string.
        permissionId (str): The ID of the permission to retrieve. Must be a non-empty string.
        supportsAllDrives (bool): Whether the requesting application supports both My Drives 
            and shared drives. Defaults to False.
        supportsTeamDrives (bool): Whether to support team drives. Deprecated - use 
            supportsAllDrives instead. Defaults to False.
        useDomainAdminAccess (bool): Issue the request as a domain administrator. If set to 
            true, grants access if the file ID refers to a shared drive and the requester 
            is an administrator of the domain to which the shared drive belongs. Defaults to False.
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the permission with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#permission').
            - 'id' (str): Permission ID.
            - 'role' (str): The role granted by this permission.
            - 'type' (str): The type of the grantee.
            - 'emailAddress' (str): The email address of the user or group.
            - 'domain' (str): The domain name of the entity this permission refers to.
            - 'allowFileDiscovery' (bool): Whether the permission allows the file to be discovered through search.
            - 'expirationTime' (str): The time at which this permission will expire.
            
    Raises:
        TypeError: If any parameter is not of the expected type.
        ValueError: If fileId or permissionId is empty or invalid.
    """
    # --- Input Validation ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not isinstance(permissionId, str):
        raise TypeError("permissionId must be a string.")
    if not isinstance(supportsAllDrives, bool):
        raise TypeError("supportsAllDrives must be a boolean.")
    if not isinstance(supportsTeamDrives, bool):
        raise TypeError("supportsTeamDrives must be a boolean.")
    if not isinstance(useDomainAdminAccess, bool):
        raise TypeError("useDomainAdminAccess must be a boolean.")
        
    if not fileId.strip():
        raise ValueError("fileId cannot be empty or whitespace.")
    if not permissionId.strip():
        raise ValueError("permissionId cannot be empty or whitespace.")
    
    userId = 'me'  # Assuming 'me' for now
    
    # Ensure the file exists
    _ensure_file(userId, fileId)
    
    # Get the file entry
    file_entry = DB['users'][userId]['files'][fileId]
    
    # Search for the permission in the current user's file permissions
    for permission in file_entry.get('permissions', []):
        if permission['id'] == permissionId:
            return permission
    
    # If supportsAllDrives or supportsTeamDrives is True, search across shared drives
    if supportsAllDrives or supportsTeamDrives:
        # Search in current user's shared drives
        if 'drives' in DB['users'][userId]:
            for drive_id, drive_data in DB['users'][userId]['drives'].items():
                if fileId in drive_data.get('files', {}):
                    for permission in drive_data['files'][fileId].get('permissions', []):
                        if permission['id'] == permissionId:
                            return permission
        
        # If domain admin access is enabled, search across all users
        if useDomainAdminAccess:
            for user_id, user_data in DB['users'].items():
                if user_id != userId:  # Skip current user (already searched above)
                    # Search in other users' regular files
                    if fileId in user_data.get('files', {}):
                        for permission in user_data['files'][fileId].get('permissions', []):
                            if permission['id'] == permissionId:
                                return permission
                    
                    # Search in other users' shared drives
                    if 'drives' in user_data:
                        for drive_id, drive_data in user_data['drives'].items():
                            if fileId in drive_data.get('files', {}):
                                for permission in drive_data['files'][fileId].get('permissions', []):
                                    if permission['id'] == permissionId:
                                        return permission
    
    return None

@tool_spec(
    spec={
        'name': 'list_permissions',
        'description': "Lists a file's or shared drive's permissions.",
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file or shared drive.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support all drives. If True, includes permissions from all drives. Defaults to False.'
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support team drives. If True, includes team drive specific permissions. Defaults to False.'
                },
                'useDomainAdminAccess': {
                    'type': 'boolean',
                    'description': 'Whether to use domain admin access. If True, includes domain-wide permissions. Defaults to False.'
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def list(fileId: str,
        supportsAllDrives: Optional[bool] = False,
        supportsTeamDrives: Optional[bool] = False,
        useDomainAdminAccess: Optional[bool] = False,
        ) -> Dict[str, Any]:
    """Lists a file's or shared drive's permissions.
    
    Args:
        fileId (str): The ID of the file or shared drive.
        supportsAllDrives (Optional[bool]): Whether to support all drives. If True, includes permissions from all drives. Defaults to False.
        supportsTeamDrives (Optional[bool]): Whether to support team drives. If True, includes team drive specific permissions. Defaults to False.
        useDomainAdminAccess (Optional[bool]): Whether to use domain admin access. If True, includes domain-wide permissions. Defaults to False.
        
    Returns:
        Dict[str, Any]: Dictionary containing the list of permissions with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#permissionList').
            - 'permissions' (List[PermissionResourceModel]): List of permission objects, each with the following keys:
                - 'kind' (str): Identifies the resource as 'drive#permission'.
                - 'id' (str): The unique ID for this permission.
                - 'role' (str): The role granted by this permission (e.g., 'owner', 'editor', 'reader').
                - 'type' (str): The type of the grantee (e.g., 'user', 'group', 'domain', 'anyone').
                - 'emailAddress' (Optional[str]): The email address of the user or group this permission refers to.
    Raises:
        TypeError: If any of the input arguments do not match their expected types
                   (e.g., if fileId is not a string, or boolean flags are not booleans).
        NotFoundError: If no file matching `fileId` exists for the current user.
    """

    # --- Input Validation ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not isinstance(supportsAllDrives, bool):
        raise TypeError("supportsAllDrives must be a boolean.")
    if not isinstance(supportsTeamDrives, bool):
        raise TypeError("supportsTeamDrives must be a boolean.")
    if not isinstance(useDomainAdminAccess, bool):
        raise TypeError("useDomainAdminAccess must be a boolean.")
    # --- End of Input Validation ---

    userId = 'me'  # Assuming 'me' for now

    files = DB['users'][userId]['files']
    if fileId not in files:
        raise NotFoundError(f"Given fileId {fileId!r} not found in user {userId!r} files")

    # Get base permissions (make a copy so we don’t mutate the DB)
    permissions = DB['users'][userId]['files'][fileId].get('permissions', [])[:]

    # If supportsAllDrives is True, include permissions from all drives
    if supportsAllDrives:
        all_drives_permissions = []
        for user_id, user_data in DB['users'].items():
            if user_id != userId:  # Skip current user as we already have their permissions
                if fileId in user_data.get('files', {}):
                    all_drives_permissions.extend(user_data['files'][fileId].get('permissions', []))
        permissions.extend(all_drives_permissions)

    # If supportsTeamDrives is True, include team drive specific permissions
    if supportsTeamDrives:
        team_drive_permissions = []
        # look under "drives" (shared/team drives)
        for user_data in DB['users'].values():
            for drive_data in user_data.get('drives', {}).values():
                if fileId in user_data.get('files', {}) and drive_data.get("id") == user_data['files'][fileId].get('driveId', None):
                    team_drive_permissions.extend(
                        user_data['files'][fileId].get('permissions', [])
                    )
        permissions.extend(team_drive_permissions)

    # If useDomainAdminAccess is True, include domain-wide permissions
    if useDomainAdminAccess:
        domain_permissions = []
        for user_id, user_data in DB['users'].items():
            if 'domain_permissions' in user_data:
                if fileId in user_data['domain_permissions']:
                    domain_permissions.extend(user_data['domain_permissions'][fileId])
        permissions.extend(domain_permissions)

    return PermissionListModel(**{
        'kind': 'drive#permissionList',
        'permissions': permissions
    }).model_dump()

@tool_spec(
    spec={
        'name': 'update_permission',
        'description': 'Updates a permission with patch semantics.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file or shared drive.'
                },
                'permissionId': {
                    'type': 'string',
                    'description': 'The ID of the permission to update.'
                },
                'body': {
                    'type': 'object',
                    'description': 'A permission resource body containing the fields to update.',
                    'properties': {
                        'role': {
                            'type': 'string',
                            'description': """ The role granted by this permission. Supports both API and UI role names (case-insensitive):
                                 - 'reader'/'Viewer': Can view the file
                                - 'writer'/'editor': Can view, comment, and edit the file
                                - 'commenter'/'commenter': Can view and comment on the file
                                - 'owner'/'owner': Has full control over the file
                                - 'organizer'/'manager': Can manage content and users in shared drives
                                - 'fileOrganizer'/'content manager': Can manage content in shared drives
                                - 'writer'/'contributor': Can view, comment, and edit files in shared drives """
                        },
                        'type': {
                            'type': 'string',
                            'description': """ The type of the grantee. Possible values:
                                 - 'user': Permission granted to a specific user
                                - 'group': Permission granted to a group
                                - 'domain': Permission granted to a domain
                                - 'anyone': Permission granted to anyone with the link """
                        },
                        'emailAddress': {
                            'type': 'string',
                            'description': 'The email address of the user or group.'
                        },
                        'domain': {
                            'type': 'string',
                            'description': 'The domain name of the entity this permission refers to.'
                        },
                        'allowFileDiscovery': {
                            'type': 'boolean',
                            'description': 'Whether the permission allows the file to be discovered through search.'
                        },
                        'expirationTime': {
                            'type': 'string',
                            'description': 'The time at which this permission will expire.'
                        }
                    },
                    'required': []
                },
                'transferOwnership': {
                    'type': 'boolean',
                    'description': 'Whether to transfer ownership to the specified user and downgrade the current owner to a writer.'
                }
            },
            'required': [
                'fileId',
                'permissionId'
            ]
        }
    }
)
def update(fileId: str,
          permissionId: str,
          body: Optional[Dict[str, Any]] = None,
          transferOwnership: bool = False
          ) -> Dict[str, Any]:
    """Updates a permission with patch semantics.

    Args:
        fileId (str): The ID of the file or shared drive.
        permissionId (str): The ID of the permission to update.
        body (Optional[Dict[str, Any]]): A permission resource body containing the fields to update.
            - 'role' (Optional[str]): The role granted by this permission. Supports both API and UI role names (case-insensitive):
                - 'reader'/'Viewer': Can view the file
                - 'writer'/'editor': Can view, comment, and edit the file
                - 'commenter'/'commenter': Can view and comment on the file
                - 'owner'/'owner': Has full control over the file
                - 'organizer'/'manager': Can manage content and users in shared drives
                - 'fileOrganizer'/'content manager': Can manage content in shared drives
                - 'writer'/'contributor': Can view, comment, and edit files in shared drives
            - 'type' (Optional[str]): The type of the grantee. Possible values:
                - 'user': Permission granted to a specific user
                - 'group': Permission granted to a group
                - 'domain': Permission granted to a domain
                - 'anyone': Permission granted to anyone with the link
            - 'emailAddress' (Optional[str]): The email address of the user or group.
            - 'domain' (Optional[str]): The domain name of the entity this permission refers to.
            - 'allowFileDiscovery' (Optional[bool]): Whether the permission allows the file to be discovered through search.
            - 'expirationTime' (Optional[str]): The time at which this permission will expire.
        transferOwnership (bool): Whether to transfer ownership to the specified user and downgrade the current owner to a writer.

    Returns:
        Dict[str, Any]: Dictionary containing the updated permission with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#permission').
            - 'id' (str): Permission ID.
            - 'role' (str): The role granted by this permission.
            - 'type' (str): The type of the grantee.
            - 'emailAddress' (str): The email address of the user or group.
            - 'domain' (str): The domain name of the entity this permission refers to.
            - 'allowFileDiscovery' (bool): Whether the permission allows the file to be discovered through search.
            - 'expirationTime' (str): The time at which this permission will expire.

    Raises:
        TypeError: If 'fileId' or 'permissionId' are not strings, or
                   if 'transferOwnership' is not a boolean.
        ValidationError: If 'body' is provided and does not conform to the expected structure.
        LookupError: If the specified 'permissionId' is not found (both for standard updates and ownership transfers),
                    or if the file with the given 'fileId' could not be found or created.
        ValueError: If attempting to transfer ownership to a permission lacking an email address, 
                    or if trying to set 'role' to 'owner' without 'transferOwnership=True'.
    """
    # --- Input Validation ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not isinstance(permissionId, str):
        raise TypeError("permissionId must be a string.")
    if not isinstance(transferOwnership, bool):
        raise TypeError("transferOwnership must be a boolean.")

    validated_body_model: Optional[PermissionBodyUpdateModel] = None
    if body is not None:
        try:
            # Pydantic will raise ValidationError if 'body' does not match the model
            validated_body_model = PermissionBodyUpdateModel(**body)
        except ValidationError as e:
            # Re-raise Pydantic's validation error.
            raise e

    # Prepare the body data for use in the core logic.
    # If body was None, it effectively becomes {}. If body was provided, use its validated form.
    body_data_for_logic: Dict[str, Any]
    if validated_body_model:
        body_data_for_logic = validated_body_model.model_dump(exclude_none=True, by_alias=True)
    else:
        body_data_for_logic = {}
    # --- End of Input Validation ---

    userId = 'me'
    
    # First, ensure the file record and its permissions list exist.
    _ensure_file(userId, fileId) 
    
    # Then, retrieve the file entry from the database.
    file_entry = DB['users'][userId]['files'].get(fileId)

    # A check for robustness, although _ensure_file should prevent this.
    if not file_entry:
        raise LookupError(f"File with ID '{fileId}' could not be found or created.")

    permissions = file_entry.get('permissions', [])
    
    if transferOwnership:
        # --- Ownership Transfer Logic ---
        # The user to be promoted is now identified by permissionId, not the body.
        permission_to_promote = next((p for p in permissions if p.get('id') == permissionId), None)

        if not permission_to_promote:
            raise LookupError(f"Permission with ID '{permissionId}' not found, cannot transfer ownership.")

        new_owner_email = permission_to_promote.get('emailAddress')
        if not new_owner_email:
            raise ValueError("Ownership can only be transferred to a permission with a valid email address.")

        # Demote all existing owners who are not the new owner
        for perm in permissions:
            if perm.get('role') == 'owner' and perm.get('id') != permissionId:
                perm['role'] = 'writer'
        
        # Apply any other updates from the body first
        permission_to_promote.update(body_data_for_logic)
        # Then, ensure the role is set to owner
        permission_to_promote['role'] = 'owner'

        # Update the top-level owners list on the file entry
        file_entry['owners'] = [new_owner_email]
        
        return permission_to_promote
    
    else:
        # --- Standard Permission Update Logic ---
        if body_data_for_logic.get('role') == 'owner':
            raise ValueError("Cannot set role to 'owner' directly. Use the transferOwnership=True flag.")

        permission_to_update = next((p for p in permissions if p.get('id') == permissionId), None)

        if permission_to_update:
            # Map UI roles to API roles if needed before updating
            if 'role' in body_data_for_logic:
                body_data_for_logic['role'] = _map_ui_role_to_api_role(body_data_for_logic['role'])
            # if 'role' in body_data_for_logic:
                # body_data_for_logic['role'] = _map_ui_role_to_api_role(body_data_for_logic['role'])
            permission_to_update.update(body_data_for_logic)
            return permission_to_update

        raise LookupError(f"Permission with ID '{permissionId}' not found on file '{fileId}'.")
