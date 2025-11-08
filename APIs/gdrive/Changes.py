"""
Changes resource for Google Drive API.

This module provides methods for managing changes in the Google Drive API.
"""
from common_utils.tool_spec_decorator import tool_spec
import builtins # Using this because of a name conflict with the built-in function 'list'
import warnings
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _ensure_changes, _ensure_channels
from .SimulationEngine.counters import _next_counter
from .SimulationEngine.custom_errors import ValidationError, InvalidRequestError
# from .SimulationEngine.utils import _ensure_changes, _ensure_channels, _next_counter


@tool_spec(
    spec={
        'name': 'get_changes_start_page_token',
        'description': """ Gets the starting pageToken for listing future changes.
        
        This method retrieves a starting page token that can be used to list changes
        to files in a user's Drive or a shared drive. The page token doesn't expire
        and should be stored for subsequent change tracking operations. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': """ The ID of the shared drive for which the starting 
                    pageToken for listing future changes will be returned. Must be a valid 
                    shared drive ID if provided. Defaults to empty string (user's My Drive). """
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether the requesting application 
                    supports both My Drives and shared drives. When True, enables access 
                    to shared drive content. Defaults to False. """
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': """ **DEPRECATED** - Use supportsAllDrives 
                    instead. This parameter will be removed in a future version. Defaults to False. """
                },
                'teamDriveId': {
                    'type': 'string',
                    'description': """ **DEPRECATED** - Use driveId instead. 
                    This parameter will be removed in a future version. Defaults to empty string. """
                }
            },
            'required': []
        }
    }
)
def getStartPageToken(driveId: Optional[str] = '',
                      supportsAllDrives: Optional[bool] = False,
                      supportsTeamDrives: Optional[bool] = False,
                      teamDriveId: Optional[str] = ''
                      ) -> Dict[str, Any]:
    """Gets the starting pageToken for listing future changes.
    
    This method retrieves a starting page token that can be used to list changes
    to files in a user's Drive or a shared drive. The page token doesn't expire
    and should be stored for subsequent change tracking operations.
    
    Args:
        driveId (Optional[str]): The ID of the shared drive for which the starting 
            pageToken for listing future changes will be returned. Must be a valid 
            shared drive ID if provided. Defaults to empty string (user's My Drive).
        supportsAllDrives (Optional[bool]): Whether the requesting application 
            supports both My Drives and shared drives. When True, enables access 
            to shared drive content. Defaults to False.
        supportsTeamDrives (Optional[bool]): **DEPRECATED** - Use supportsAllDrives 
            instead. This parameter will be removed in a future version. Defaults to False.
        teamDriveId (Optional[str]): **DEPRECATED** - Use driveId instead. 
            This parameter will be removed in a future version. Defaults to empty string.
        
    Returns:
        Dict[str, Any]: Dictionary containing the start page token with keys:
            - 'kind' (str): Resource type identifier ('drive#startPageToken').
            - 'startPageToken' (str): The starting page token for listing changes.
                This is an opaque string that can be used in subsequent calls to
                changes.list() to retrieve changes from this point forward.
    
    Raises:
        ValidationError: If input parameters are invalid (e.g., invalid driveId format).
        InvalidRequestError: If the request is malformed or contains conflicting parameters.
    """
    # Input validation
    if not isinstance(driveId, str):
        raise ValidationError("driveId must be a string.")

    if not isinstance(supportsAllDrives, bool):
        raise ValidationError("supportsAllDrives must be a boolean.")

    if not isinstance(supportsTeamDrives, bool):
        raise ValidationError("supportsTeamDrives must be a boolean.")

    if not isinstance(teamDriveId, str):
        raise ValidationError("teamDriveId must be a string.")

    # Handle deprecated parameters with warnings
    if supportsTeamDrives:
        warnings.warn(
            "Parameter 'supportsTeamDrives' is deprecated. Use 'supportsAllDrives' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # If supportsTeamDrives is True but supportsAllDrives is False, 
        # automatically enable supportsAllDrives for backward compatibility
        if not supportsAllDrives:
            supportsAllDrives = True

    if teamDriveId:
        warnings.warn(
            "Parameter 'teamDriveId' is deprecated. Use 'driveId' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # If teamDriveId is provided but driveId is empty, use teamDriveId for backward compatibility
        if not driveId:
            driveId = teamDriveId
        elif driveId != teamDriveId:
            raise InvalidRequestError(
                "Conflicting drive IDs: both 'driveId' and deprecated 'teamDriveId' "
                "are provided with different values. Use only 'driveId'."
            )

    # Validate driveId format if provided
    if driveId:
        if len(driveId.strip()) == 0:
            raise ValidationError("driveId cannot be empty or whitespace-only.")

        # For shared drives, supportsAllDrives must be True
        if not supportsAllDrives:
            raise InvalidRequestError(
                "When accessing shared drives (driveId provided), "
                "supportsAllDrives must be set to True."
            )

    # Initialize database structures
    userId = 'me'  # Assuming 'me' for now
    _ensure_changes(userId)

    # Generate or retrieve start page token
    try:
        start_page_token = DB['users'][userId]['changes'].get('startPageToken')
        if not start_page_token:
            start_page_token = str(_next_counter('change_token'))
            DB['users'][userId]['changes']['startPageToken'] = start_page_token

        return {
            'kind': 'drive#startPageToken',
            'startPageToken': start_page_token
        }
    except Exception as e:
        raise InvalidRequestError(f"Failed to generate start page token: {str(e)}")

@tool_spec(
    spec={
        'name': 'list_changes',
        'description': """ Lists the changes for a user or shared drive.
        
        This method retrieves a list of changes that have occurred since the specified 
        page token. Changes include file additions, modifications, deletions, and 
        permission changes. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'pageToken': {
                    'type': 'string',
                    'description': """ The token for continuing a previous list request on the next page.
                    This token is obtained from a previous changes.list request or from 
                    changes.getStartPageToken(). If not provided or empty, will call getStartPageToken() to get the starting token.
                    Defaults to empty string. """
                },
                'driveId': {
                    'type': 'string',
                    'description': """ The ID of the shared drive for which changes are returned.
                    Only changes to files within this shared drive will be returned.
                    Defaults to empty string (user's My Drive). """
                },
                'includeCorpusRemovals': {
                    'type': 'boolean',
                    'description': """ Whether changes should include the file resource 
                    if the file is still accessible by the user at the time of the request.
                    Defaults to False. """
                },
                'includeItemsFromAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether both My Drive and shared drive items 
                    should be included in results. Defaults to False. """
                },
                'includeRemoved': {
                    'type': 'boolean',
                    'description': """ Whether to include changes indicating that items have 
                    been removed from the list of changes. Defaults to True. """
                },
                'includeTeamDriveItems': {
                    'type': 'boolean',
                    'description': """ **DEPRECATED** - Use includeItemsFromAllDrives 
                    instead. Whether to include changes for team drive items. Defaults to False. """
                },
                'pageSize': {
                    'type': 'integer',
                    'description': """ Maximum number of changes to return per page. Must be between 
                    1 and 1000 inclusive. Defaults to 100. """
                },
                'restrictToMyDrive': {
                    'type': 'boolean',
                    'description': """ Whether to restrict the results to changes inside 
                    the My Drive hierarchy. This cannot be used together with teamDriveId or driveId.
                    Defaults to False. """
                },
                'spaces': {
                    'type': 'string',
                    'description': """ A comma-separated list of spaces to query within the user corpus.
                    Supported values are 'drive', 'appDataFolder', and 'photos'. Defaults to 'drive'. """
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether the requesting application supports both 
                    My Drives and shared drives. Defaults to False. """
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': """ **DEPRECATED** - Use supportsAllDrives instead.
                    Whether the requesting application supports Team Drives. Defaults to False. """
                },
                'teamDriveId': {
                    'type': 'string',
                    'description': """ **DEPRECATED** - Use driveId instead. The ID of the Team Drive 
                    for which changes will be returned. Defaults to empty string. """
                },
                'includePermissionsForView': {
                    'type': 'string',
                    'description': """ Specifies which additional view's permissions 
                    to include in the response. Only 'published' is supported. Defaults to empty string. """
                },
                'includeLabels': {
                    'type': 'string',
                    'description': """ A comma-separated list of IDs of labels to include in 
                    the labelInfo part of the response. Defaults to empty string. """
                }
            },
            'required': []
        }
    }
)
def list(pageToken: str = '',
         driveId: str = '',
         includeCorpusRemovals: bool = False,
         includeItemsFromAllDrives: bool = False,
         includeRemoved: bool = True,
         includeTeamDriveItems: bool = False,
         pageSize: int = 100,
         restrictToMyDrive: bool = False,
         spaces: str = 'drive',
         supportsAllDrives: bool = False,
         supportsTeamDrives: bool = False,
         teamDriveId: str = '',
         includePermissionsForView: str = '',
         includeLabels: str = ''
         ) -> Dict[str, Any]:
    """Lists the changes for a user or shared drive.
    
    This method retrieves a list of changes that have occurred since the specified 
    page token. Changes include file additions, modifications, deletions, and 
    permission changes.
    
    Args:
        pageToken (str): The token for continuing a previous list request on the next page.
            This token is obtained from a previous changes.list request or from 
            changes.getStartPageToken(). If not provided or empty, will call getStartPageToken() to get the starting token.
            Defaults to empty string.
        driveId (str): The ID of the shared drive for which changes are returned.
            Only changes to files within this shared drive will be returned.
            Defaults to empty string (user's My Drive).
        includeCorpusRemovals (bool): Whether changes should include the file resource 
            if the file is still accessible by the user at the time of the request.
            Defaults to False.
        includeItemsFromAllDrives (bool): Whether both My Drive and shared drive items 
            should be included in results. Defaults to False.
        includeRemoved (bool): Whether to include changes indicating that items have 
            been removed from the list of changes. Defaults to True.
        includeTeamDriveItems (bool): **DEPRECATED** - Use includeItemsFromAllDrives 
            instead. Whether to include changes for team drive items. Defaults to False.
        pageSize (int): Maximum number of changes to return per page. Must be between 
            1 and 1000 inclusive. Defaults to 100.
        restrictToMyDrive (bool): Whether to restrict the results to changes inside 
            the My Drive hierarchy. This cannot be used together with teamDriveId or driveId.
            Defaults to False.
        spaces (str): A comma-separated list of spaces to query within the user corpus.
            Supported values are 'drive', 'appDataFolder', and 'photos'. Defaults to 'drive'.
        supportsAllDrives (bool): Whether the requesting application supports both 
            My Drives and shared drives. Defaults to False.
        supportsTeamDrives (bool): **DEPRECATED** - Use supportsAllDrives instead.
            Whether the requesting application supports Team Drives. Defaults to False.
        teamDriveId (str): **DEPRECATED** - Use driveId instead. The ID of the Team Drive 
            for which changes will be returned. Defaults to empty string.
        includePermissionsForView (str): Specifies which additional view's permissions 
            to include in the response. Only 'published' is supported. Defaults to empty string.
        includeLabels (str): A comma-separated list of IDs of labels to include in 
            the labelInfo part of the response. Defaults to empty string.
        
    Returns:
        Dict[str, Any]: Dictionary containing the list of changes with keys:
            - 'kind' (str): Resource type identifier ('drive#changeList').
            - 'nextPageToken' (str): The page token for the next page of changes, 
                or None if there are no more changes.
            - 'newStartPageToken' (str): The starting page token for future changes.
                This token can be used for subsequent changes.list() calls.
            - 'changes' (List[Dict[str, Any]]): List of change objects, each with keys:
                - 'kind' (str): Resource type identifier ('drive#change').
                - 'type' (str): The type of the change ('file' or 'drive').
                - 'changeType' (str): The type of change ('file' for file changes).
                - 'time' (str): The time of this change in RFC 3339 format.
                - 'removed' (bool): Whether the file or shared drive has been removed.
                - 'fileId' (str): The ID of the file which has changed (if type is 'file').
                - 'file' (Dict[str, Any]): The updated state of the file (if type is 'file').
                - 'driveId' (str): The ID of the shared drive the file belongs to.
    
    Raises:
        ValidationError: If input parameters are invalid (e.g., 
            invalid pageSize range, invalid spaces format).
        InvalidRequestError: If the request contains conflicting parameters or 
            if the pageToken is malformed.
    """
    # Input validation
    if not isinstance(pageToken, str):
        raise ValidationError("pageToken must be a string.")
    
    if not isinstance(driveId, str):
        raise ValidationError("driveId must be a string.")
    
    if not isinstance(includeCorpusRemovals, bool):
        raise ValidationError("includeCorpusRemovals must be a boolean.")
    
    if not isinstance(includeItemsFromAllDrives, bool):
        raise ValidationError("includeItemsFromAllDrives must be a boolean.")
    
    if not isinstance(includeRemoved, bool):
        raise ValidationError("includeRemoved must be a boolean.")
    
    if not isinstance(includeTeamDriveItems, bool):
        raise ValidationError("includeTeamDriveItems must be a boolean.")
    
    if not isinstance(pageSize, int):
        raise ValidationError("pageSize must be an integer.")
    
    if pageSize < 1 or pageSize > 1000:
        raise ValidationError("pageSize must be between 1 and 1000, inclusive.")
    
    if not isinstance(restrictToMyDrive, bool):
        raise ValidationError("restrictToMyDrive must be a boolean.")
    
    if not isinstance(spaces, str):
        raise ValidationError("spaces must be a string.")
    
    if not isinstance(supportsAllDrives, bool):
        raise ValidationError("supportsAllDrives must be a boolean.")
    
    if not isinstance(supportsTeamDrives, bool):
        raise ValidationError("supportsTeamDrives must be a boolean.")
    
    if not isinstance(teamDriveId, str):
        raise ValidationError("teamDriveId must be a string.")
    
    if not isinstance(includePermissionsForView, str):
        raise ValidationError("includePermissionsForView must be a string.")
    
    if not isinstance(includeLabels, str):
        raise ValidationError("includeLabels must be a string.")

    # Handle deprecated parameters with warnings
    if supportsTeamDrives:
        warnings.warn(
            "Parameter 'supportsTeamDrives' is deprecated. Use 'supportsAllDrives' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not supportsAllDrives:
            supportsAllDrives = True

    if includeTeamDriveItems:
        warnings.warn(
            "Parameter 'includeTeamDriveItems' is deprecated. Use 'includeItemsFromAllDrives' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not includeItemsFromAllDrives:
            includeItemsFromAllDrives = True

    if teamDriveId:
        warnings.warn(
            "Parameter 'teamDriveId' is deprecated. Use 'driveId' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not driveId:
            driveId = teamDriveId
        elif driveId != teamDriveId:
            raise InvalidRequestError(
                "Conflicting drive IDs: both 'driveId' and deprecated 'teamDriveId' "
                "are provided with different values. Use only 'driveId'."
            )

    # Validate spaces parameter
    valid_spaces = ['drive', 'appDataFolder', 'photos']
    if spaces:
        space_list = [s.strip() for s in spaces.split(',')]
        for space in space_list:
            if space not in valid_spaces:
                raise ValidationError(f"Invalid space '{space}'. Valid spaces are: {', '.join(valid_spaces)}")

    # Validate includePermissionsForView
    if includePermissionsForView and includePermissionsForView != 'published':
        raise ValidationError("includePermissionsForView only supports 'published' value.")

    # Validate driveId constraints
    if driveId:
        if len(driveId.strip()) == 0:
            raise ValidationError("driveId cannot be empty or whitespace-only.")
        
        # For shared drives, supportsAllDrives must be True
        if not supportsAllDrives:
            raise InvalidRequestError(
                "When accessing shared drives (driveId provided), "
                "supportsAllDrives must be set to True."
            )

    # Check conflicting parameters
    if restrictToMyDrive and (driveId or teamDriveId):
        raise InvalidRequestError(
            "restrictToMyDrive cannot be used together with driveId or teamDriveId."
        )

    # Initialize database structures
    userId = 'me'
    _ensure_changes(userId)

    # Handle pageToken default value
    if not pageToken or pageToken.strip() == '':
        # Get the start page token from getStartPageToken()
        start_token_result = getStartPageToken(driveId, supportsAllDrives, supportsTeamDrives, teamDriveId)
        pageToken = start_token_result['startPageToken']
    
    # Get changes from the page token
    try:
        # Parse page token (simple integer)
        token_value = int(pageToken)
    except ValueError:
        raise InvalidRequestError(f"Invalid page token format: {pageToken}")

    # Get all changes from database
    all_changes = DB['users'][userId]['changes'].get('changes', [])
    
    # Apply filtering based on parameters
    filtered_changes = []
    
    for change in all_changes:
        # Skip if not included based on parameters
        if not includeRemoved and change.get('removed', False):
            continue
            
        # Filter by drive if specified
        if driveId and change.get('driveId') != driveId:
            continue
            
        # Restrict to My Drive if specified
        if restrictToMyDrive and change.get('driveId'):
            continue
            
        # Filter by spaces
        if spaces != 'drive':
            space_list = [s.strip() for s in spaces.split(',')]
            # Handle case where change.get('file') might be None
            file_obj = change.get('file')
            if file_obj is not None:
                change_space = file_obj.get('spaces', ['drive'])
                if not any(space in change_space for space in space_list):
                    continue
            else:
                # If file is None, skip this change for space filtering
                continue
        
        filtered_changes.append(change)

    # Apply pagination
    start_index = max(0, token_value - 1)  # Convert 1-based token to 0-based index
    end_index = start_index + pageSize
    page_changes = filtered_changes[start_index:end_index]

    # Generate next page token
    next_page_token = None
    if end_index < len(filtered_changes):
        next_page_token = str(end_index + 1)  # Convert back to 1-based token

    # Generate new start page token for future changes
    new_start_page_token = str(_next_counter('change_token'))
    DB['users'][userId]['changes']['startPageToken'] = new_start_page_token

    return {
        'kind': 'drive#changeList',
        'nextPageToken': next_page_token,
        'newStartPageToken': new_start_page_token,
        'changes': page_changes
    }

@tool_spec(
    spec={
        'name': 'watch_changes',
        'description': """ Creates a notification channel for watching changes in Google Drive.
        
        This function sets up a watch channel for changes to files in 
        a user's Drive or shared drive. It stores the channel 
        configuration and validates the watch parameters, but does not establish 
        actual real-time notifications. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'pageToken': {
                    'type': 'string',
                    'description': """ The token for the initial page of changes to watch from.
                    This token is obtained from changes.getStartPageToken() or a previous 
                    changes.list request. If not provided or empty, will call getStartPageToken() to get the starting token.
                    Defaults to empty string. """
                },
                'resource': {
                    'type': 'object',
                    'description': """ Dictionary of notification channel 
                    properties. If None, a minimal channel will be created. Expected keys: """,
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': 'Required. Unique identifier for the channel.'
                        },
                        'type': {
                            'type': 'string',
                            'description': "Required. Channel type, typically 'web_hook'."
                        },
                        'address': {
                            'type': 'string',
                            'description': 'Required. URL where notifications are delivered.'
                        },
                        'resourceId': {
                            'type': 'string',
                            'description': 'ID of the resource being watched.'
                        },
                        'resourceUri': {
                            'type': 'string',
                            'description': 'URI of the resource being watched.'
                        },
                        'token': {
                            'type': 'string',
                            'description': 'Token for authenticating the channel.'
                        },
                        'expiration': {
                            'type': 'string',
                            'description': 'Expiration time in RFC 3339 format.'
                        },
                        'payload': {
                            'type': 'boolean',
                            'description': 'Whether to include payload in notifications.'
                        },
                        'params': {
                            'type': 'object',
                            'description': """ Additional channel parameters.
                               channel behavior. Each parameter is declared by name as a key-value pair.
                              Example: {"a_key": "A String"} declares a new parameter by name. """,
                            'properties': {},
                            'required': []
                        }
                    },
                    'required': [
                        'id',
                        'type',
                        'address'
                    ]
                },
                'driveId': {
                    'type': 'string',
                    'description': """ The ID of the shared drive for which changes are watched.
                    Only changes to files within this shared drive will trigger notifications.
                    Defaults to empty string (user's My Drive). """
                },
                'includeCorpusRemovals': {
                    'type': 'boolean',
                    'description': """ Whether the watch should include notifications 
                    for files that are removed from the corpus but still accessible.
                    Defaults to False. """
                },
                'includeItemsFromAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether to watch changes in both My Drive 
                    and shared drives. Defaults to False. """
                },
                'includeRemoved': {
                    'type': 'boolean',
                    'description': """ Whether to include notifications for removed items.
                    Defaults to True. """
                },
                'includeTeamDriveItems': {
                    'type': 'boolean',
                    'description': """ **DEPRECATED** - Use includeItemsFromAllDrives 
                    instead. Whether to include changes for team drive items. Defaults to False. """
                },
                'pageSize': {
                    'type': 'integer',
                    'description': """ Maximum number of changes to return per notification. 
                    Must be between 1 and 1000 inclusive. Defaults to 100. """
                },
                'restrictToMyDrive': {
                    'type': 'boolean',
                    'description': """ Whether to restrict notifications to changes 
                    inside the My Drive hierarchy only. Cannot be used with driveId or teamDriveId.
                    Defaults to False. """
                },
                'spaces': {
                    'type': 'string',
                    'description': """ A comma-separated list of spaces to watch for changes.
                    Supported values are 'drive', 'appDataFolder', and 'photos'. Defaults to 'drive'. """
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether the requesting application supports both 
                    My Drives and shared drives. Required when driveId is specified. Defaults to False. """
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': """ **DEPRECATED** - Use supportsAllDrives instead.
                    Whether the application supports Team Drives. Defaults to False. """
                },
                'teamDriveId': {
                    'type': 'string',
                    'description': """ **DEPRECATED** - Use driveId instead. The ID of the Team Drive 
                    to watch for changes. Defaults to empty string. """
                },
                'includePermissionsForView': {
                    'type': 'string',
                    'description': """ Specifies which additional view's permissions 
                    to include in change notifications. Only 'published' is supported. 
                    Defaults to empty string. """
                },
                'includeLabels': {
                    'type': 'string',
                    'description': """ A comma-separated list of label IDs to include in 
                    the labelInfo part of change notifications. Defaults to empty string. """
                }
            },
            'required': []
        }
    }
)
def watch(pageToken: str = '',
          resource: Optional[Dict[str, Any]] = None,
          driveId: str = '',
          includeCorpusRemovals: bool = False,
          includeItemsFromAllDrives: bool = False,
          includeRemoved: bool = True,
          includeTeamDriveItems: bool = False,
          pageSize: int = 100,
          restrictToMyDrive: bool = False,
          spaces: str = 'drive',
          supportsAllDrives: bool = False,
          supportsTeamDrives: bool = False,
          teamDriveId: str = '',
          includePermissionsForView: str = '',
          includeLabels: str = ''
          ) -> Dict[str, Any]:
    """Creates a notification channel for watching changes in Google Drive.
    
    This function sets up a watch channel for changes to files in 
    a user's Drive or shared drive. It stores the channel 
    configuration and validates the watch parameters, but does not establish 
    actual real-time notifications.
    
    Args:
        pageToken (str): The token for the initial page of changes to watch from.
            This token is obtained from changes.getStartPageToken() or a previous 
            changes.list request. If not provided or empty, will call getStartPageToken() to get the starting token.
            Defaults to empty string.
        resource (Optional[Dict[str, Any]]): Dictionary of notification channel 
            properties. If None, a minimal channel will be created. Expected keys:
            - id (str): Required. Unique identifier for the channel.
            - type (str): Required. Channel type, typically 'web_hook'.
            - address (str): Required. URL where notifications are delivered.
            - resourceId (Optional[str]): ID of the resource being watched.
            - resourceUri (Optional[str]): URI of the resource being watched.
            - token (Optional[str]): Token for authenticating the channel.
            - expiration (Optional[str]): Expiration time in RFC 3339 format.
            - payload (Optional[bool]): Whether to include payload in notifications.
            - params (Optional[Dict[str, Any]]): Additional channel parameters.
              channel behavior. Each parameter is declared by name as a key-value pair.
              Example: {"a_key": "A String"} declares a new parameter by name.
        driveId (str): The ID of the shared drive for which changes are watched.
            Only changes to files within this shared drive will trigger notifications.
            Defaults to empty string (user's My Drive).
        includeCorpusRemovals (bool): Whether the watch should include notifications 
            for files that are removed from the corpus but still accessible.
            Defaults to False.
        includeItemsFromAllDrives (bool): Whether to watch changes in both My Drive 
            and shared drives. Defaults to False.
        includeRemoved (bool): Whether to include notifications for removed items.
            Defaults to True.
        includeTeamDriveItems (bool): **DEPRECATED** - Use includeItemsFromAllDrives 
            instead. Whether to include changes for team drive items. Defaults to False.
        pageSize (int): Maximum number of changes to return per notification. 
            Must be between 1 and 1000 inclusive. Defaults to 100.
        restrictToMyDrive (bool): Whether to restrict notifications to changes 
            inside the My Drive hierarchy only. Cannot be used with driveId or teamDriveId.
            Defaults to False.
        spaces (str): A comma-separated list of spaces to watch for changes.
            Supported values are 'drive', 'appDataFolder', and 'photos'. Defaults to 'drive'.
        supportsAllDrives (bool): Whether the requesting application supports both 
            My Drives and shared drives. Required when driveId is specified. Defaults to False.
        supportsTeamDrives (bool): **DEPRECATED** - Use supportsAllDrives instead.
            Whether the application supports Team Drives. Defaults to False.
        teamDriveId (str): **DEPRECATED** - Use driveId instead. The ID of the Team Drive 
            to watch for changes. Defaults to empty string.
        includePermissionsForView (str): Specifies which additional view's permissions 
            to include in change notifications. Only 'published' is supported. 
            Defaults to empty string.
        includeLabels (str): A comma-separated list of label IDs to include in 
            the labelInfo part of change notifications. Defaults to empty string.
        
    Returns:
        Dict[str, Any]: Dictionary containing the created channel resource with keys:
            - 'kind' (str): Resource type identifier ('api#channel').
            - 'id' (str): The unique ID of the channel.
            - 'resourceId' (str): ID of the resource being watched (from input or auto-generated).
            - 'resourceUri' (str): URI of the resource being watched (from input or empty string).
            - 'token' (str): Authentication token for the channel.
            - 'expiration' (str): Channel expiration time in RFC 3339 format.
            - 'type' (str): The type of the channel (e.g., 'web_hook').
            - 'address' (str): URL where notifications are delivered.
            - 'payload' (bool): Whether notifications include payload.
            - 'params' (Dict[str, Any]): Additional channel parameters.
            - 'watchConfig' (Dict[str, Any]): Configuration for what changes to watch.
    
    Raises:
        ValidationError: If input parameters are invalid (e.g., 
            invalid pageSize range, missing required channel properties, invalid spaces format).
        InvalidRequestError: If the request contains conflicting parameters, 
            malformed pageToken, or invalid channel configuration.
    """
    # Input validation
    if not isinstance(pageToken, str):
        raise ValidationError("pageToken must be a string.")
    
    # Handle pageToken default value
    if not pageToken or pageToken.strip() == '':
        # Get the start page token from getStartPageToken()
        start_token_result = getStartPageToken(driveId, supportsAllDrives, supportsTeamDrives, teamDriveId)
        pageToken = start_token_result['startPageToken']
    
    if resource is not None and not isinstance(resource, dict):
        raise ValidationError("resource must be a dictionary or None.")
    
    if not isinstance(driveId, str):
        raise ValidationError("driveId must be a string.")
    
    if not isinstance(includeCorpusRemovals, bool):
        raise ValidationError("includeCorpusRemovals must be a boolean.")
    
    if not isinstance(includeItemsFromAllDrives, bool):
        raise ValidationError("includeItemsFromAllDrives must be a boolean.")
    
    if not isinstance(includeRemoved, bool):
        raise ValidationError("includeRemoved must be a boolean.")
    
    if not isinstance(includeTeamDriveItems, bool):
        raise ValidationError("includeTeamDriveItems must be a boolean.")
    
    if not isinstance(pageSize, int):
        raise ValidationError("pageSize must be an integer.")
    
    if pageSize < 1 or pageSize > 1000:
        raise ValidationError("pageSize must be between 1 and 1000, inclusive.")
    
    if not isinstance(restrictToMyDrive, bool):
        raise ValidationError("restrictToMyDrive must be a boolean.")
    
    if not isinstance(spaces, str):
        raise ValidationError("spaces must be a string.")
    
    if not isinstance(supportsAllDrives, bool):
        raise ValidationError("supportsAllDrives must be a boolean.")
    
    if not isinstance(supportsTeamDrives, bool):
        raise ValidationError("supportsTeamDrives must be a boolean.")
    
    if not isinstance(teamDriveId, str):
        raise ValidationError("teamDriveId must be a string.")
    
    if not isinstance(includePermissionsForView, str):
        raise ValidationError("includePermissionsForView must be a string.")
    
    if not isinstance(includeLabels, str):
        raise ValidationError("includeLabels must be a string.")

    # Handle deprecated parameters with warnings
    if supportsTeamDrives:
        warnings.warn(
            "Parameter 'supportsTeamDrives' is deprecated. Use 'supportsAllDrives' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not supportsAllDrives:
            supportsAllDrives = True

    if includeTeamDriveItems:
        warnings.warn(
            "Parameter 'includeTeamDriveItems' is deprecated. Use 'includeItemsFromAllDrives' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not includeItemsFromAllDrives:
            includeItemsFromAllDrives = True

    if teamDriveId:
        warnings.warn(
            "Parameter 'teamDriveId' is deprecated. Use 'driveId' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if not driveId:
            driveId = teamDriveId
        elif driveId != teamDriveId:
            raise InvalidRequestError(
                "Conflicting drive IDs: both 'driveId' and deprecated 'teamDriveId' "
                "are provided with different values. Use only 'driveId'."
            )

    # Validate spaces parameter
    valid_spaces = ['drive', 'appDataFolder', 'photos']
    if spaces:
        space_list = [s.strip() for s in spaces.split(',')]
        for space in space_list:
            if space not in valid_spaces:
                raise ValidationError(f"Invalid space '{space}'. Valid spaces are: {', '.join(valid_spaces)}")

    # Validate includePermissionsForView
    if includePermissionsForView and includePermissionsForView != 'published':
        raise ValidationError("includePermissionsForView only supports 'published' value.")

    # Validate driveId constraints
    if driveId:
        if len(driveId.strip()) == 0:
            raise ValidationError("driveId cannot be empty or whitespace-only.")
        
        # For shared drives, supportsAllDrives must be True
        if not supportsAllDrives:
            raise InvalidRequestError(
                "When accessing shared drives (driveId provided), "
                "supportsAllDrives must be set to True."
            )

    # Check conflicting parameters
    if restrictToMyDrive and (driveId or teamDriveId):
        raise InvalidRequestError(
            "restrictToMyDrive cannot be used together with driveId or teamDriveId."
        )

    # Validate page token format
    try:
        # Parse page token (simple integer)
        int(pageToken)
    except ValueError:
        raise InvalidRequestError(f"Invalid page token format: {pageToken}")

    # Process and validate resource/channel configuration
    if resource is None:
        resource = {}

    # Validate required channel properties
    channel_id = resource.get('id')
    if channel_id is None or channel_id == '':
        # Generate a unique channel ID if not provided or empty
        channel_id = f"channel_{_next_counter('channel')}"
    elif not isinstance(channel_id, str) or not channel_id.strip():
        raise ValidationError("Channel ID must be a non-empty string.")

    channel_type = resource.get('type', 'web_hook')
    if not isinstance(channel_type, str) or not channel_type.strip():
        raise ValidationError("Channel type must be a non-empty string.")

    address = resource.get('address')
    if address is None:
        raise ValidationError("Channel address is required for notifications.")
    if not isinstance(address, str) or not address.strip():
        raise ValidationError("Channel address must be a non-empty string.")

    # Validate optional channel properties
    token = resource.get('token', '')
    if token is not None and not isinstance(token, str):
        raise ValidationError("Channel token must be a string.")

    expiration = resource.get('expiration')
    if expiration is not None and not isinstance(expiration, str):
        raise ValidationError("Channel expiration must be a string.")

    payload = resource.get('payload', True)
    if not isinstance(payload, bool):
        raise ValidationError("Channel payload must be a boolean.")

    params = resource.get('params', {})
    if not isinstance(params, dict):
        raise ValidationError("Channel params must be a dictionary.")

    # Initialize database structures
    userId = 'me'
    _ensure_changes(userId)
    _ensure_channels(userId)

    # Create watch configuration
    watch_config = {
        'pageToken': pageToken,
        'driveId': driveId,
        'includeCorpusRemovals': includeCorpusRemovals,
        'includeItemsFromAllDrives': includeItemsFromAllDrives,
        'includeRemoved': includeRemoved,
        'pageSize': pageSize,
        'restrictToMyDrive': restrictToMyDrive,
        'spaces': spaces,
        'supportsAllDrives': supportsAllDrives,
        'includePermissionsForView': includePermissionsForView,
        'includeLabels': includeLabels
    }

    # Generate resource information
    resource_id = resource.get('resourceId', str(uuid.uuid4()))
    resource_uri = resource.get('resourceUri', '')
    
    # Default expiration to 24 hours from now if not provided
    if not expiration:
        future_time = datetime.utcnow() + timedelta(hours=24)
        expiration = future_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    # Create complete channel resource
    channel = {
        'kind': 'api#channel',
        'id': channel_id,
        'resourceId': resource_id,
        'resourceUri': resource_uri,
        'token': token,
        'expiration': expiration,
        'type': channel_type,
        'address': address,
        'payload': payload,
        'params': params,
        'watchConfig': watch_config
    }

    # Store the channel in the database
    try:
        DB['users'][userId]['channels'][channel_id] = channel
    except Exception as e:
        raise InvalidRequestError(f"Failed to create watch channel: {str(e)}")

    return channel 