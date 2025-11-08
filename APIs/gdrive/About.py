"""
About resource for Google Drive API.

This module provides methods for retrieving information about the user's Drive account.
"""

import copy
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any
from .SimulationEngine.db import DB

@tool_spec(
    spec={
        'name': 'get_drive_account_info',
        'description': """ Gets information about the user's Drive account.
        
        This function retrieves account information for the authenticated user
        from the Google Drive API. The response can be filtered to include
        only specific fields using the fields parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fields': {
                    'type': 'string',
                    'description': """ A comma-separated list of fields to include in the response.
                    Use '*' to include all fields (default).
                    For partial responses, use comma-separated field names (e.g., 'user,storageQuota').
                    For nested fields, use dot notation (e.g., 'user.displayName,storageQuota.limit').
                    Field names are case-sensitive and whitespace around commas is ignored. """
                }
            },
            'required': []
        }
    }
)
def get(fields: str = '*') -> Dict[str, Any]:
    """Gets information about the user's Drive account.
    
    This function retrieves account information for the authenticated user
    from the Google Drive API. The response can be filtered to include
    only specific fields using the fields parameter.
    
    Args:
        fields (str): A comma-separated list of fields to include in the response.
            Use '*' to include all fields (default).
            For partial responses, use comma-separated field names (e.g., 'user,storageQuota').
            For nested fields, use dot notation (e.g., 'user.displayName,storageQuota.limit').
            Field names are case-sensitive and whitespace around commas is ignored.
        
    Returns:
        Dict[str, Any]: Dictionary containing the user's Drive account information with keys:
            - 'kind' (str): Resource type identifier (always 'drive#about').
            - 'user' (Dict[str, str]): Information about the user with keys:
                - 'displayName' (str): The user's display name.
                - 'emailAddress' (str): The user's email address.
                - 'permissionId' (str): The user's permission ID.
                - 'photoLink' (str): A link to the user's profile photo.
            - 'storageQuota' (Dict[str, str]): Information about the user's storage quota with keys:
                - 'limit' (str): The total storage limit in bytes.
                - 'usage' (str): The total storage used in bytes.
                - 'usageInDrive' (str): The storage used in Drive in bytes.
                - 'usageInDriveTrash' (str): The storage used in Drive trash in bytes.
            - 'maxImportSizes' (Dict[str, str]): Maximum import sizes for different file types.
            - 'maxUploadSize' (str): The maximum upload size in bytes.
            - 'appInstalled' (bool): Whether the Drive app is installed.
            - 'folderColorPalette' (List[str]): List of available folder colors.
            - 'importFormats' (Dict[str, List[str]]): Supported import formats.
            - 'exportFormats' (Dict[str, List[str]]): Supported export formats.
            - 'canCreateDrives' (bool): Whether the user can create shared drives.
            - 'driveThemes' (List[Dict[str, str]]): List of available Drive themes with keys:
                - 'id' (str): The theme ID.
                - 'backgroundImageLink' (str): Link to the background image.
                - 'colorRgb' (str): The theme color in RGB format.

    Raises:
        TypeError: If 'fields' is not a string.
        ValueError: If 'fields' is an empty string, contains only whitespace, or contains null bytes.
        KeyError: If `userId` ('me') is not found in the internal database, or if the 'about'
                  section for the user is missing. This error is propagated from
                  internal data access operations (e.g., DB access).
    """
    # --- Input Validation ---
    if not isinstance(fields, str):
        raise TypeError("Argument 'fields' must be a string.")
    if not fields.strip(): # Check for empty or all-whitespace string
        raise ValueError("Argument 'fields' cannot be an empty string or consist only of whitespace.")
    if '\x00' in fields: # Check for null bytes
        raise ValueError("Argument 'fields' cannot contain null bytes.")
    # --- End of Input Validation ---

    userId = 'me'  # Assuming 'me' for now
    
    # Check if user exists in DB
    if 'users' not in DB or userId not in DB['users']:
        raise KeyError("User 'me' not found in database")
    
    # Check if about data exists for user
    if 'about' not in DB['users'][userId]:
        raise KeyError("'about' data not found for user 'me'")
    
    about_data = DB['users'][userId]['about']
    
    # Create a copy of the data to avoid modifying the original database
    about_data = copy.deepcopy(about_data)
    
    # Ensure folderColorPalette is a list, as per the docstring.
    if 'folderColorPalette' in about_data and isinstance(about_data['folderColorPalette'], str):
        about_data['folderColorPalette'] = [color.strip() for color in about_data['folderColorPalette'].split(',')]
    
    # Parse fields and check for wildcard
    field_list = [f.strip() for f in fields.split(',') if f.strip()]
    
    # If wildcard '*' is present (alone or with other fields), return all fields
    if '*' in field_list:
        return about_data
    filtered_data = {}
    
    for field in field_list:
        # Handle nested fields (e.g., 'user.displayName')
        if '.' in field:
            parts = field.split('.')
            parent = parts[0]
            child = '.'.join(parts[1:])
            
            # If the parent field doesn't exist in the filtered data yet,
            # create it with an empty dict
            if parent not in filtered_data:
                if parent in about_data:
                    filtered_data[parent] = {}
                else:
                    # Parent field doesn't exist in the data
                    continue
            
            # Add the child field to the parent dict if it exists in the original data
            # and the parent is actually a dictionary/object
            if (parent in about_data and 
                isinstance(about_data[parent], dict) and 
                child in about_data[parent]):
                filtered_data[parent][child] = about_data[parent][child]
        
        # Handle top-level fields
        else:
            if field in about_data:
                filtered_data[field] = about_data[field]
    
    # Always include 'kind' if it exists in the original data and wasn't already included
    if 'kind' in about_data and 'kind' not in filtered_data:
        filtered_data['kind'] = about_data['kind']
    
    return filtered_data 