"""
Apps resource for Google Drive API simulation.

This module provides methods for managing apps in the Google Drive API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
import builtins #using this because of the name conflict with the built-in function 'list'
from typing import Dict, Any, Optional
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _ensure_apps

@tool_spec(
    spec={
        'name': 'get_app_details',
        'description': 'Gets a specific app.',
        'parameters': {
            'type': 'object',
            'properties': {
                'appId': {
                    'type': 'string',
                    'description': 'The ID of the app to retrieve.'
                }
            },
            'required': [
                'appId'
            ]
        }
    }
)
def get(appId: str) -> Optional[Dict[str, Any]]:
    """Gets a specific app.
    
    Args:
        appId (str): The ID of the app to retrieve.
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the app details if found, or None if the app with the specified ID does not exist. The dictionary contains keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#app').
            - 'id' (str): The ID of the app.
            - 'name' (str): The name of the app.
            - 'objectType' (str): The type of object this app works with.
            - 'supportsCreate' (bool): Whether the app supports creating new objects.
            - 'supportsImport' (bool): Whether the app supports importing objects.
            - 'installed' (bool): Whether the app is installed.
            - 'authorized' (bool): Whether the app is authorized.
            - 'useByDefault' (bool): Whether the app is used by default.
            - 'productUrl' (str): The URL of the product.
            - 'primaryMimeTypes' (List[str]): The primary MIME types supported by the app.
            - 'secondaryMimeTypes' (List[str]): The secondary MIME types supported by the app.
            - 'primaryFileExtensions' (List[str]): The primary file extensions supported by the app.
            - 'secondaryFileExtensions' (List[str]): The secondary file extensions supported by the app.
            - 'icons' (List[Dict[str, str]]): List of icon dictionaries with keys:
                - 'category' (str): The category of the icon.
                - 'iconUrl' (str): The URL of the icon.
                - 'size' (int): The size of the icon.

    Raises:
        TypeError: If appId is not a string.
        ValueError: If appId is empty or contains only whitespace.
    """
    # Input validation
    if not isinstance(appId, str):
        raise TypeError("appId must be a string.")

    if not appId or not appId.strip():
        raise ValueError("appId cannot be empty or contain only whitespace.")
    
    userId = 'me'  # Assuming 'me' for now
    _ensure_apps(userId)
    return DB['users'][userId]['apps'].get(appId)

@tool_spec(
    spec={
        'name': 'list_installed_apps',
        'description': """ Lists a user's installed apps.
        
        This function retrieves all installed apps for the current user and applies
        optional filtering based on file extensions and MIME types. The languageCode
        parameter is accepted for API compatibility but does not affect the current
        implementation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'appFilterExtensions': {
                    'type': 'string',
                    'description': """ A comma-separated list of file extensions 
                    to filter by (e.g., "pdf,txt,docx"). Only apps that support these extensions
                    will be returned. Defaults to '' (no filtering). """
                },
                'appFilterMimeTypes': {
                    'type': 'string',
                    'description': """ A comma-separated list of MIME types to 
                    filter by (e.g., "text/plain,application/pdf"). Only apps that support 
                    these MIME types will be returned. Defaults to '' (no filtering). """
                },
                'languageCode': {
                    'type': 'string',
                    'description': """ The language code to use for localized strings.
                    Currently unused but accepted for API compatibility. Defaults to ''. """
                }
            },
            'required': []
        }
    }
)
def list(appFilterExtensions: str = '',
         appFilterMimeTypes: str = '',
         languageCode: str = '',
         ) -> Dict[str, Any]:
    """Lists a user's installed apps.
    
    This function retrieves all installed apps for the current user and applies
    optional filtering based on file extensions and MIME types. The languageCode
    parameter is accepted for API compatibility but does not affect the current
    implementation.
    
    Args:
        appFilterExtensions (str, optional): A comma-separated list of file extensions 
            to filter by (e.g., "pdf,txt,docx"). Only apps that support these extensions
            will be returned. Defaults to '' (no filtering).
        appFilterMimeTypes (str, optional): A comma-separated list of MIME types to 
            filter by (e.g., "text/plain,application/pdf"). Only apps that support 
            these MIME types will be returned. Defaults to '' (no filtering).
        languageCode (str, optional): The language code to use for localized strings.
            Currently unused but accepted for API compatibility. Defaults to ''.
        
    Returns:
        Dict[str, Any]: Dictionary containing the list of apps with keys:
            - 'kind' (str): Resource type identifier ('drive#appList').
            - 'items' (List[Dict[str, Any]]): List of app objects with keys:
                - 'kind' (str): Resource type identifier ('drive#app').
                - 'id' (str): The ID of the app.
                - 'name' (str): The name of the app.
                - 'objectType' (str): The type of object this app works with.
                - 'supportsCreate' (bool): Whether the app supports creating new objects.
                - 'supportsImport' (bool): Whether the app supports importing objects.
                - 'installed' (bool): Whether the app is installed.
                - 'authorized' (bool): Whether the app is authorized.
                - 'useByDefault' (bool): Whether the app is used by default.
                - 'productUrl' (str): The URL of the product.
                - 'primaryMimeTypes' (List[str]): The primary MIME types supported by the app.
                - 'secondaryMimeTypes' (List[str]): The secondary MIME types supported by the app.
                - 'primaryFileExtensions' (List[str]): The primary file extensions supported by the app.
                - 'secondaryFileExtensions' (List[str]): The secondary file extensions supported by the app.
                - 'icons' (List[Dict[str, str]]): List of icon dictionaries with keys:
                    - 'category' (str): The category of the icon.
                    - 'iconUrl' (str): The URL of the icon.
                    - 'size' (int): The size of the icon.
    
    Raises:
        TypeError: If any parameter is not a string.
        ValueError: If appFilterExtensions or appFilterMimeTypes contains invalid format.
    """
    # Input validation
    if not isinstance(appFilterExtensions, str):
        raise TypeError("Argument 'appFilterExtensions' must be a string.")
    if not isinstance(appFilterMimeTypes, str):
        raise TypeError("Argument 'appFilterMimeTypes' must be a string.")
    if not isinstance(languageCode, str):
        raise TypeError("Argument 'languageCode' must be a string.")
    
    # Validate filter formats
    if appFilterExtensions:
        extensions = [ext.strip() for ext in appFilterExtensions.split(',')]
        for ext in extensions:
            if not ext:
                raise ValueError("appFilterExtensions cannot contain empty extensions.")
            if not ext.replace('.', '').replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Invalid file extension format: '{ext}'. Extensions must contain only alphanumeric characters, dots, hyphens, and underscores.")
    
    if appFilterMimeTypes:
        mime_types = [mime.strip() for mime in appFilterMimeTypes.split(',')]
        for mime in mime_types:
            if not mime:
                raise ValueError("appFilterMimeTypes cannot contain empty MIME types.")
            if '/' not in mime or mime.count('/') != 1:
                raise ValueError(f"Invalid MIME type format: '{mime}'. MIME types must be in format 'type/subtype'.")
            type_part, subtype_part = mime.split('/')
            if not type_part or not subtype_part:
                raise ValueError(f"Invalid MIME type format: '{mime}'. Both type and subtype must be non-empty.")
    
    userId = 'me'  # Assuming 'me' for now
    _ensure_apps(userId)
    
    # Get all apps
    apps_list = builtins.list(DB['users'][userId]['apps'].values())
    
    # Apply filtering
    filtered_apps = apps_list
    
    # Filter by extensions if specified
    if appFilterExtensions:
        extensions = [ext.strip().lower() for ext in appFilterExtensions.split(',')]
        filtered_apps = []
        for app in apps_list:
            app_extensions = []
            # Collect all extensions from primary and secondary
            if 'primaryFileExtensions' in app:
                app_extensions.extend([ext.lower() for ext in app['primaryFileExtensions']])
            if 'secondaryFileExtensions' in app:
                app_extensions.extend([ext.lower() for ext in app['secondaryFileExtensions']])
            
            # Check if any requested extension is supported by this app
            if any(ext in app_extensions for ext in extensions):
                filtered_apps.append(app)
    
    # Filter by MIME types if specified
    if appFilterMimeTypes:
        mime_types = [mime.strip().lower() for mime in appFilterMimeTypes.split(',')]
        if appFilterExtensions:
            # Further filter the already filtered list
            apps_to_filter = filtered_apps
        else:
            apps_to_filter = apps_list
        
        filtered_apps = []
        for app in apps_to_filter:
            app_mime_types = []
            # Collect all MIME types from primary and secondary
            if 'primaryMimeTypes' in app:
                app_mime_types.extend([mime.lower() for mime in app['primaryMimeTypes']])
            if 'secondaryMimeTypes' in app:
                app_mime_types.extend([mime.lower() for mime in app['secondaryMimeTypes']])
            
            # Check if any requested MIME type is supported by this app
            if any(mime in app_mime_types for mime in mime_types):
                filtered_apps.append(app)
    
    return {
        'kind': 'drive#appList',
        'items': filtered_apps
    } 