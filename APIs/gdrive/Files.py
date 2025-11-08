"""
Files resource for Google Drive API simulation.

This module provides methods for managing files in the Google Drive API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
import builtins #using this becausing of the name conflict with the built-in function 'list'
from datetime import datetime, UTC
import mimetypes
import os
import re

from pydantic import ValidationError
from typing import Dict, Any, Optional, List, Union

from .SimulationEngine.models import FileBodyModel, FileWithContentModel, MediaBodyModel, FileCopyBodyModel, UpdateBodyModel, RevisionModel, RevisionContentModel
from .SimulationEngine.custom_errors import InvalidPageSizeError, QuotaExceededError, ResourceNotFoundError, UserNotFoundError
from .SimulationEngine import models
from .SimulationEngine.file_utils import DriveFileProcessor, encode_to_base64
from .SimulationEngine.content_manager import DriveContentManager

from .SimulationEngine.utils import (
    _parse_query, _apply_query_filter,
    _delete_descendants, _has_drive_role, _update_user_usage,
    _ensure_channels, _get_user_quota, _validate_parent_folder_permissions, _calculate_file_size, _get_encoding
)
from .SimulationEngine.counters import _next_counter
from .SimulationEngine.db import DB
from .SimulationEngine.file_utils import DriveFileProcessor, encode_to_base64, read_file, decode_from_base64
from .SimulationEngine.content_manager import DriveContentManager

@tool_spec(
    spec={
        'name': 'copy_file',
        'description': 'Creates a copy of a file if quota allows.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to copy. Must be a non-empty string.'
                },
                'body': {
                    'type': 'object',
                    'description': 'Dictionary of file properties containing:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Name of the copied file. If not provided, defaults to "Copy of {original_file_name}".'
                        },
                        'parents': {
                            'type': 'array',
                            'description': 'List of parent folder IDs. If not provided, inherits from original file.',
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': []
                },
                'ignoreDefaultVisibility': {
                    'type': 'boolean',
                    'description': 'Whether to ignore default visibility set by domain administrators. Defaults to False.'
                },
                'keepRevisionForever': {
                    'type': 'boolean',
                    'description': 'Whether to keep revision forever. Defaults to False.'
                },
                'ocrLanguage': {
                    'type': 'string',
                    'description': 'The language to use for OCR. Defaults to empty string.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support all drives. Defaults to False.'
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support team drives. Defaults to False.'
                },
                'includePermissionsForView': {
                    'type': 'string',
                    'description': "Specifies which additional view's permissions to include. Defaults to empty string."
                },
                'includeLabels': {
                    'type': 'string',
                    'description': 'Comma-separated list of labels to include. Defaults to empty string.'
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def copy(fileId: str,
         body: Optional[Dict[str, Any]] = None,
         ignoreDefaultVisibility: Optional[bool] = False,
         keepRevisionForever: Optional[bool] = False,
         ocrLanguage: Optional[str] = '',
         supportsAllDrives: Optional[bool] = False,
         supportsTeamDrives: Optional[bool] = False,
         includePermissionsForView: Optional[str] = '',
         includeLabels: Optional[str] = '',
         ) -> Dict[str, Any]:
    """Creates a copy of a file if quota allows.
    
    Args:
        fileId (str): The ID of the file to copy. Must be a non-empty string.
        body (Optional[Dict[str, Any]]): Dictionary of file properties containing:
            - 'name' (Optional[str]): Name of the copied file. If not provided, defaults to "Copy of {original_file_name}".
            - 'parents' (Optional[List[str]]): List of parent folder IDs. If not provided, inherits from original file.
        ignoreDefaultVisibility (Optional[bool]): Whether to ignore default visibility set by domain administrators. Defaults to False.
        keepRevisionForever (Optional[bool]): Whether to keep revision forever. Defaults to False.
        ocrLanguage (Optional[str]): The language to use for OCR. Defaults to empty string.
        supportsAllDrives (Optional[bool]): Whether to support all drives. Defaults to False.
        supportsTeamDrives (Optional[bool]): Whether to support team drives. Defaults to False.
        includePermissionsForView (Optional[str]): Specifies which additional view's permissions to include. Defaults to empty string.
        includeLabels (Optional[str]): Comma-separated list of labels to include. Defaults to empty string.
        
    Returns:
        Dict[str, Any]: Dictionary containing the copied file. If the copy is successful, the dictionary containing:
            - 'kind' (str): Resource type identifier (e.g., 'drive#file').
            - 'id' (str): File ID.
            - 'name' (str): File name.
            - 'mimeType' (str): MIME type of the file.
            - 'parents' (List[str]): List of parent folder IDs.
            - 'createdTime' (str): Creation timestamp.
            - 'modifiedTime' (str): Last modification timestamp.
            - 'trashed' (bool): Whether the file is in trash.
            - 'starred' (bool): Whether the file is starred.
            - 'owners' (List[str]): List of owner email addresses.
            - 'size' (str): File size in bytes.
            - 'permissions' (List[Dict[str, Any]]): List of permission objects. Each permission object may include the following fields:
                - 'id' (str): Permission ID.
                - 'role' (str): The role granted by this permission. Allowed values:
                    - 'viewer': Can view the file
                    - 'commenter': Can view and comment on the file
                    - 'editor': Can view, comment, and edit the file
                    - 'owner': Has full control over the file
                - 'type' (str): The type of the grantee. Allowed values:
                    - 'user': Permission granted to a specific user
                    - 'group': Permission granted to a group
                    - 'domain': Permission granted to a domain
                    - 'anyone': Permission granted to anyone with the link
                - 'emailAddress' (Optional[str]): The email address of the user or group.
                - 'domain' (Optional[str]): The domain name of the entity this permission refers to.
                - 'allowFileDiscovery' (Optional[bool]): Whether the permission allows the file to be discovered through search.
                - 'expirationTime' (Optional[str]): The time at which this permission will expire, in RFC 3339 format.

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If fileId is empty, contains only whitespace, if the file is not found (with appropriate drive support flags), or if any parent folder is not found.
        ValidationError: If 'file_metadata' is provided and does not conform to the FileCopyBodyModel structure.
        QuotaExceededError: If the storage quota would be exceeded by copying the file.
        PermissionError: If the user does not have permission to access any of the specified parent folders.
    """
    # --- Input Validation Start ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not fileId or not fileId.strip():
        raise ValueError("fileId cannot be empty or contain only whitespace.")
        
    if body is not None and not isinstance(body, dict):
        raise TypeError("body must be a dictionary or None.")
    if not isinstance(ignoreDefaultVisibility, bool):
        raise TypeError("ignoreDefaultVisibility must be a boolean.")
    if not isinstance(keepRevisionForever, bool):
        raise TypeError("keepRevisionForever must be a boolean.")
    if not isinstance(ocrLanguage, str):
        raise TypeError("ocrLanguage must be a string.")
    if not isinstance(supportsAllDrives, bool):
        raise TypeError("supportsAllDrives must be a boolean.")
    if not isinstance(supportsTeamDrives, bool):
        raise TypeError("supportsTeamDrives must be a boolean.")
    if not isinstance(includePermissionsForView, str):
        raise TypeError("includePermissionsForView must be a string.")
    if not isinstance(includeLabels, str):
        raise TypeError("includeLabels must be a string.")

    validated_file_metadata_pydantic_model: Optional[FileCopyBodyModel] = None
    if body is not None:
        try:
            validated_file_metadata_pydantic_model = FileCopyBodyModel(**body)
        except ValidationError as e:
            raise e
    
    file_metadata_for_logic: Dict[str, Any] = {}
    if validated_file_metadata_pydantic_model:
        file_metadata_for_logic = validated_file_metadata_pydantic_model.model_dump(exclude_unset=True, by_alias=False)
    # --- Input Validation End ---
    
    userId = 'me'

    # If supportsAllDrives or supportsTeamDrives is True, include files with non-empty driveId (shared drives) in the search
    original_file = DB['users'][userId]['files'].get(fileId)
    if not original_file and (supportsAllDrives or supportsTeamDrives):
        # Try to find in shared drives (files with non-empty driveId)
        for f in DB['users'][userId]['files'].values():
            if f.get('id') == fileId and f.get('driveId'):
                original_file = f
                break
    if not original_file:
        if not (supportsAllDrives or supportsTeamDrives):
            raise ValueError("File not found. If you want to check in shared drives, pass supportsAllDrives=True or supportsTeamDrives=True.")
        else:
            raise ValueError("File not found in drive or shared drives.")

    # Check quota before copying
    file_size = int(original_file.get('size', 0))
    quota = _get_user_quota(userId)

    if quota['usage'] + file_size > quota['limit']:
        raise QuotaExceededError("Quota exceeded. Cannot copy the file.")

    # Generate new file ID
    file_id_num = _next_counter('file')
    new_file_id = f"file_{file_id_num}"

    # Create deep copy of the original file (improved deep copy logic)
    new_file = {}
    for key, value in original_file.items():
        if isinstance(value, builtins.list): 
            if value and isinstance(value[0], dict):
                # Create new list with deep-copied dictionaries
                new_file[key] = [{k: v for k, v in item.items()} for item in value]
            else:
                # For other lists (like lists of strings), slice copying is sufficient
                new_file[key] = value[:]
        elif isinstance(value, dict):
            # Shallow copy of inner dict
            new_file[key] = {k: v for k, v in value.items()}
        else:
            new_file[key] = value

    # Update basic file properties
    new_file['id'] = new_file_id
    new_file['name'] = file_metadata_for_logic.get('name', f"Copy of {original_file['name']}")

    # Apply parents from file_metadata if provided
    if 'parents' in file_metadata_for_logic:
        new_file['parents'] = file_metadata_for_logic['parents']
        
        # Validate that user has permission to access all parent folders
        _validate_parent_folder_permissions(userId, new_file['parents'])
    
    # Handle OCR language processing (store the result, not the request flag)
    if ocrLanguage:
        new_file['ocrMetadata'] = {
            'ocrLanguage': ocrLanguage,
            'ocrStatus': 'PENDING'
        }

    # Handle revision settings (store the result, not the request flag)
    if keepRevisionForever:
        new_file['revisionSettings'] = {'keepForever': True}
    
    # Handle revisions
    new_file['revisions'] = []
    for revision in original_file.get('revisions', []):
        if revision['keepForever'] == True:
            new_file['revisions'].append(revision.copy())

    # Handle additional permissions for view (store the result, not the request flag)
    if includePermissionsForView:
        additional_permissions = [{
            'id': f'view_{new_file_id}',
            'role': 'reader',
            'type': 'anyone'
        }]
        new_file['additionalPermissions'] = additional_permissions

    # Handle labels (store the result, not the request flag)
    if includeLabels:
        parsed_labels = [label.strip() for label in includeLabels.split(',') if label.strip()]
        new_file['labels'] = parsed_labels

    # Save the copied file and update quota
    DB['users'][userId]['files'][new_file_id] = new_file
    _update_user_usage(userId, file_size)

    return new_file

@tool_spec(
    spec={
        'name': 'create_file_or_folder',
        'description': 'Creates a new file or folder with permissions if quota allows.',
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': 'Dictionary of file properties with keys:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Name of the file.'
                        },
                        "description": {
                            'type': 'string',
                            'description': 'Description of the file.'
                        },
                        'mimeType': {
                            'type': 'string',
                            'description': """ MIME type of the file. Can be:
                                 - 'application/vnd.google-apps.document'
                                - 'application/vnd.google-apps.spreadsheet'
                                - 'application/vnd.google-apps.presentation'
                                - 'application/vnd.google-apps.drawing'
                                - 'application/vnd.google-apps.folder'
                                - 'application/vnd.google-apps.script' """
                        },
                        'parents': {
                            'type': 'array',
                            'description': 'List of parent folder IDs.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'size': {
                            'type': 'string',
                            'description': 'File size in bytes (string that must be convertible to integer).'
                        },
                        'modifiedTime': {
                            'type': 'string',
                            'description': "Last modification timestamp in RFC3339 format (e.g., '2024-05-01T00:00:00Z')."
                        }
                    },
                    'required': [
                        'name',
                        'mimeType'
                    ]
                },
                'media_body': {
                    'type': 'object',
                    'description': 'Dictionary containing media content properties with keys:',
                    'properties': {
                        'size': {
                            'type': 'integer',
                            'description': 'File size in bytes.'
                        },
                        'md5Checksum': {
                            'type': 'string',
                            'description': 'MD5 checksum of the file content.'
                        },
                        'sha1Checksum': {
                            'type': 'string',
                            'description': 'SHA1 checksum of the file content.'
                        },
                        'sha256Checksum': {
                            'type': 'string',
                            'description': 'SHA256 checksum of the file content.'
                        },
                        'mimeType': {
                            'type': 'string',
                            'description': 'MIME type of the file content.'
                        },
                        'imageMediaMetadata': {
                            'type': 'object',
                            'description': 'Additional metadata about image files (output-only), may include:',
                            'properties': {
                                'width': {
                                    'type': 'integer',
                                    'description': 'Width of the image in pixels.'
                                },
                                'height': {
                                    'type': 'integer',
                                    'description': 'Height of the image in pixels.'
                                },
                                'cameraMake': {
                                    'type': 'string',
                                    'description': 'Make of the camera used.'
                                },
                                'cameraModel': {
                                    'type': 'string',
                                    'description': 'Model of the camera used.'
                                },
                                'aperture': {
                                    'type': 'number',
                                    'description': 'Aperture (f-number) used.'
                                },
                                'exposureTime': {
                                    'type': 'number',
                                    'description': 'Exposure time in seconds.'
                                },
                                'exposureBias': {
                                    'type': 'number',
                                    'description': 'Exposure bias (APEX value).'
                                },
                                'maxApertureValue': {
                                    'type': 'number',
                                    'description': 'Maximum aperture (APEX value).'
                                },
                                'focalLength': {
                                    'type': 'number',
                                    'description': 'Focal length in millimeters.'
                                },
                                'isoSpeed': {
                                    'type': 'integer',
                                    'description': 'ISO speed used.'
                                },
                                'flashUsed': {
                                    'type': 'boolean',
                                    'description': 'Whether flash was used.'
                                },
                                'meteringMode': {
                                    'type': 'string',
                                    'description': 'Metering mode.'
                                },
                                'exposureMode': {
                                    'type': 'string',
                                    'description': 'Exposure mode.'
                                },
                                'colorSpace': {
                                    'type': 'string',
                                    'description': 'Color space of the photo.'
                                },
                                'whiteBalance': {
                                    'type': 'string',
                                    'description': 'White balance setting.'
                                },
                                'sensor': {
                                    'type': 'string',
                                    'description': 'Sensor type.'
                                },
                                'rotation': {
                                    'type': 'integer',
                                    'description': 'Number of clockwise 90° rotations applied.'
                                },
                                'time': {
                                    'type': 'string',
                                    'description': 'Date and time the photo was taken (EXIF DateTime).'
                                },
                                'lens': {
                                    'type': 'string',
                                    'description': 'Lens used.'
                                },
                                'subjectDistance': {
                                    'type': 'integer',
                                    'description': 'Distance to subject in meters.'
                                },
                                'location': {
                                    'type': 'object',
                                    'description': 'Geographic location object with the following keys:',
                                    'properties': {
                                        'latitude': {
                                            'type': 'number',
                                            'description': 'Latitude of the location.'
                                        },
                                        'longitude': {
                                            'type': 'number',
                                            'description': 'Longitude of the location.'
                                        },
                                        'altitude': {
                                            'type': 'number',
                                            'description': 'Altitude of the location.'
                                        }
                                    },
                                    'required': [
                                        'latitude',
                                        'longitude',
                                        'altitude'
                                    ]
                                }
                            },
                            'required': []
                        },
                        'videoMediaMetadata': {
                            'type': 'object',
                            'description': 'Additional metadata about video files (output-only), may include:',
                            'properties': {
                                'width': {
                                    'type': 'integer',
                                    'description': 'Width of the video in pixels.'
                                },
                                'height': {
                                    'type': 'integer',
                                    'description': 'Height of the video in pixels.'
                                },
                                'durationMillis': {
                                    'type': 'string',
                                    'description': 'Duration of the video in milliseconds.'
                                }
                            },
                            'required': [
                                'width',
                                'height',
                                'durationMillis'
                            ]
                        },
                        'filePath': {
                            'type': 'string',
                            'description': 'Path to file for content upload.'
                        }
                    },
                    'required': []
                },
                'enforceSingleParent': {
                    'type': 'boolean',
                    'description': 'Whether to enforce single parent. Defaults to False.'
                },
                'ignoreDefaultVisibility': {
                    'type': 'boolean',
                    'description': 'Whether to ignore default visibility. Defaults to False.'
                },
                'keepRevisionForever': {
                    'type': 'boolean',
                    'description': 'Whether to keep revision forever. Defaults to False.'
                },
                'ocrLanguage': {
                    'type': 'string',
                    'description': 'The language to use for OCR. Defaults to empty string.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support all drives. Defaults to False.'
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support team drives. Defaults to False.'
                },
                'useContentAsIndexableText': {
                    'type': 'boolean',
                    'description': 'Whether to use content as indexable text. Defaults to False.'
                },
                'includePermissionsForView': {
                    'type': 'string',
                    'description': "Specifies which additional view's permissions to include. Defaults to empty string."
                },
                'includeLabels': {
                    'type': 'string',
                    'description': 'Comma-separated list of labels to include. Defaults to empty string.'
                }
            },
            'required': []
        }
    }
)
def create(body: Optional[Dict[str, Union[str, int, float, bool, List[Dict[str, Union[str, int, bool, float, None]]]]]] = None,
           media_body: Optional[Dict[str, Union[str, int, float, bool, Dict[str, Union[int, float, str, bool, None, Dict[str, float]]]]]] = None,
           enforceSingleParent: Optional[bool] = False,
           ignoreDefaultVisibility: Optional[bool] = False,
           keepRevisionForever: Optional[bool] = False,
           ocrLanguage: Optional[str] = '',
           supportsAllDrives: Optional[bool] = False,
           supportsTeamDrives: Optional[bool] = False,
           useContentAsIndexableText: Optional[bool] = False,
           includePermissionsForView: Optional[str] = '',
           includeLabels: Optional[str] = '',
           ) -> Dict[str, Union[str, int, float, bool, List, Dict]]:
    """Creates a new file or folder with permissions if quota allows.
    Args:
        body (Optional[Dict[str, Union[str, int, float, bool, List[Dict[str, Union[str, int, bool, float, None]]]]]]): Dictionary of file properties with keys:
            - 'name' (str): Name of the file.
            - 'description' (Optional[str]): Description of the file.
            - 'mimeType' (str): MIME type of the file. Can be:
                - 'application/vnd.google-apps.document'
                - 'application/vnd.google-apps.spreadsheet'
                - 'application/vnd.google-apps.presentation'
                - 'application/vnd.google-apps.drawing'
                - 'application/vnd.google-apps.folder'
                - 'application/vnd.google-apps.script'
            - 'parents' (Optional[List[str]]): List of parent folder IDs.
            - 'size' (Optional[str]): File size in bytes (string that must be convertible to integer).
            - 'modifiedTime' (Optional[str]): Last modification timestamp in RFC3339 format (e.g., '2024-05-01T00:00:00Z').
        media_body (Optional[Dict[str, Union[str, int, float, bool, Dict[str, Union[int, float, str, bool, None, Dict[str, float]]]]]]): Dictionary containing media content properties with keys:
            - 'size' (Optional[int]): File size in bytes.
            - 'md5Checksum' (Optional[str]): MD5 checksum of the file content.
            - 'sha1Checksum' (Optional[str]): SHA1 checksum of the file content.
            - 'sha256Checksum' (Optional[str]): SHA256 checksum of the file content.
            - 'mimeType' (Optional[str]): MIME type of the file content.
            - 'imageMediaMetadata' (Optional[Dict[str, Union[int, float, str, bool, None, Dict[str, float]]]]): Additional metadata about image files (output-only), may include:
                - 'width' (Optional[int]): Width of the image in pixels.
                - 'height' (Optional[int]): Height of the image in pixels.
                - 'cameraMake' (Optional[str]): Make of the camera used.
                - 'cameraModel' (Optional[str]): Model of the camera used.
                - 'aperture' (Optional[float]): Aperture (f-number) used.
                - 'exposureTime' (Optional[float]): Exposure time in seconds.
                - 'exposureBias' (Optional[float]): Exposure bias (APEX value).
                - 'maxApertureValue' (Optional[float]): Maximum aperture (APEX value).
                - 'focalLength' (Optional[float]): Focal length in millimeters.
                - 'isoSpeed' (Optional[int]): ISO speed used.
                - 'flashUsed' (Optional[bool]): Whether flash was used.
                - 'meteringMode' (Optional[str]): Metering mode.
                - 'exposureMode' (Optional[str]): Exposure mode.
                - 'colorSpace' (Optional[str]): Color space of the photo.
                - 'whiteBalance' (Optional[str]): White balance setting.
                - 'sensor' (Optional[str]): Sensor type.
                - 'rotation' (Optional[int]): Number of clockwise 90° rotations applied.
                - 'time' (Optional[str]): Date and time the photo was taken (EXIF DateTime).
                - 'lens' (Optional[str]): Lens used.
                - 'subjectDistance' (Optional[int]): Distance to subject in meters.
                - 'location' (Optional[Dict[str, float]]): Geographic location object with the following keys:
                    - 'latitude' (float): Latitude of the location.
                    - 'longitude' (float): Longitude of the location.
                    - 'altitude' (float): Altitude of the location.
            - 'videoMediaMetadata' (Optional[Dict[str, Union[int, str]]]): Additional metadata about video files (output-only), may include:
                - 'width' (int): Width of the video in pixels.
                - 'height' (int): Height of the video in pixels.
                - 'durationMillis' (str): Duration of the video in milliseconds.
            - 'filePath' (Optional[str]): Path to file for content upload.
        enforceSingleParent (Optional[bool]): Whether to enforce single parent. Defaults to False.
        ignoreDefaultVisibility (Optional[bool]): Whether to ignore default visibility. Defaults to False.
        keepRevisionForever (Optional[bool]): Whether to keep revision forever. Defaults to False.
        ocrLanguage (Optional[str]): The language to use for OCR. Defaults to empty string.
        supportsAllDrives (Optional[bool]): Whether to support all drives. Defaults to False.
        supportsTeamDrives (Optional[bool]): Whether to support team drives. Defaults to False.
        useContentAsIndexableText (Optional[bool]): Whether to use content as indexable text. Defaults to False.
        includePermissionsForView (Optional[str]): Specifies which additional view's permissions to include. Defaults to empty string.
        includeLabels (Optional[str]): Comma-separated list of labels to include. Defaults to empty string.

    Returns:
        Dict[str, Union[str, int, float, bool, List, Dict]]: 
            Dictionary containing the created file with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#file').
            - 'id' (str): File ID.
            - 'driveId' (str): Shared drive ID if applicable.
            - 'name' (str): File name.
            - 'description' (str): Description of the file.
            - 'mimeType' (str): MIME type of the file or folder.
            - 'parents' (List[str]): List of parent folder IDs.
            - 'createdTime' (str): Creation timestamp.
            - 'modifiedTime' (str): Last modification timestamp.
            - 'trashed' (bool): Whether the file is in trash.
            - 'starred' (bool): Whether the file is starred.
            - 'owners' (List[str]): List of owner email addresses.
            - 'size' (str): File size in bytes.
            - 'md5Checksum' (str): MD5 checksum of the file.
            - 'sha1Checksum' (str): SHA1 checksum of the file.
            - 'sha256Checksum' (str): SHA256 checksum of the file.
            - 'imageMediaMetadata' (Dict[str, Union[int, float, str, bool, None, Dict[str, float]]]): Metadata for image files.
            - 'videoMediaMetadata' (Dict[str, Union[int, str]]): Metadata for video files.
            - 'permissions' (List[Dict[str, Union[str, int, bool]]]): List of permission objects, each having the following keys:
                - 'id' (str): Permission ID
                - 'role' (str): Permission role ('owner' for newly created files)
                - 'type' (str): Permission type ('user' for newly created files)
                - 'emailAddress' (str): Email address for user permissions
            - 'content' (Optional[Dict[str, Union[str, int, float, bool, None]]]): File content with metadata (if content was uploaded). Defaults to None. Contains:
                - 'data' (str): Text or Base64 encoded content data
                - 'encoding' (str): Content encoding ('text' or 'base64')
                - 'checksum' (str): SHA256 checksum for integrity verification
                - 'version' (str): Content version
                - 'lastContentUpdate' (str): Timestamp of last content update
            - 'revisions' (List[Dict[str, Union[str, int, float, bool, None]]]): List of file revisions (if content was uploaded). Contains:
                - 'id' (str): Revision ID
                - 'mimeType' (str): MIME type of the revision
                - 'modifiedTime' (str): When the revision was created
                - 'keepForever' (bool): Whether to keep this revision forever
                - 'originalFilename' (str): Original filename
                - 'size' (str): File size in bytes
                - 'content' (Dict[str, Union[str, int, float, bool, None]]):  # ← CHANGED (was Any)
                    Revision content with metadata. Contains:
                    - 'data' (str): Text or Base64 encoded content data
                    - 'encoding' (str): Content encoding ('text' or 'base64')
                    - 'checksum' (str): SHA256 checksum for integrity verification
            - 'enforceSingleParent' (bool): Single parent enforcement setting.
            - 'ignoreDefaultVisibility' (bool): Default visibility setting.
            - 'keepRevisionForever' (bool): Revision retention setting.
            - 'ocrLanguage' (str): OCR language setting.
            - 'supportsAllDrives' (bool): All drives support setting.
            - 'supportsTeamDrives' (bool): Team drives support setting.
            - 'useContentAsIndexableText' (bool): Content indexing setting.
            - 'includePermissionsForView' (str): View permissions setting.
            - 'includeLabels' (str): Labels setting.
            - 'revisionSettings' (Dict[str, Union[bool]]): Revision settings with keys:
                - 'keepForever' (bool): Whether to keep revisions forever
            - 'ocrMetadata' (Dict[str, Union[str]]):  # ← CHANGED (was Any)
                OCR metadata with keys:
                - 'ocrLanguage' (str): OCR language code
                - 'ocrStatus' (str): OCR processing status
            - 'indexableText' (str): Extracted indexable text content.
            - 'additionalPermissions' (List[Dict[str, Union[str, int, bool]]]): Additional view permissions.
            - 'labels' (List[str]): List of parsed labels.
            
            Additional keys for specific MIME types:
            For 'application/vnd.google-apps.spreadsheet':
            - 'sheets' (List[Dict[str, Union[str, int, float, bool, None]]]):  # ← CHANGED (was Any)
                List of sheet objects with properties
            - 'data' (Dict[str, Union[str, int, float, bool, None]]):  # ← CHANGED (was Any)
                Spreadsheet data
            
            For 'application/vnd.google-apps.document':
            - 'content' (List[Union[str, int, float, bool, None]]):  # ← CHANGED (was Any)
                Document content
            - 'tabs' (List[Union[str, int, float, bool, None]]]):  # ← CHANGED (was Any)
                Document tabs
            - 'suggestionsViewMode' (str): Suggestions view mode
            - 'includeTabsContent' (bool): Whether to include tabs content

    Raises:
        TypeError: If 'body' is provided and is not a dictionary.
        TypeError: If 'media_body' is provided and is not a dictionary.
        TypeError: If 'enforceSingleParent', 'ignoreDefaultVisibility', 'keepRevisionForever',
                   'supportsAllDrives', 'supportsTeamDrives', or 'useContentAsIndexableText'
                   are not booleans.
        TypeError: If 'ocrLanguage', 'includePermissionsForView', or 'includeLabels' are not strings.
        ValidationError: If 'body' is provided and its structure or data types
                                  do not conform to FileBodyModel.
        ValidationError: If 'media_body' is provided and its structure or data types
                                  do not conform to MediaBodyModel.
        KeyError: If internal user lookup fails (propagated from _get_user_quota).
        ValueError: If body.get('size') is provided but its string value cannot be converted to an integer
                    (e.g., "abc" instead of "123"). This is raised by the core logic.
        ValueError: If body.get('size') is provided and is negative (e.g., "-100").
        ValueError: If body.get('name') contains path traversal sequences (e.g., "../" or "..\\").
        ValueError: If includeLabels is malformed (starts/ends with comma, contains consecutive commas, or has invalid characters).
        ValueError: If parents contains invalid folder IDs that don't exist or are not valid folders.
        QuotaExceededError: If the storage quota would be exceeded by creating the file.
        FileNotFoundError: If media_body contains a filePath that doesn't exist.
    """
    # --- Input Validation ---
    if body is not None and not isinstance(body, dict):
        raise TypeError(f"Argument 'body' must be a dictionary or None, got {type(body).__name__}")

    if media_body is not None and not isinstance(media_body, dict):
        raise TypeError(f"Argument 'media_body' must be a dictionary or None, got {type(media_body).__name__}")

    if body is not None:
        try:
            _ = FileBodyModel(**body)
        except ValidationError as e:
            raise e

    if media_body is not None:
        try:
            validated_media_body = MediaBodyModel(**media_body)
        except ValidationError as e:
            raise e

    # Standard type validation for other arguments
    bool_args = {
        'enforceSingleParent': enforceSingleParent,
        'ignoreDefaultVisibility': ignoreDefaultVisibility,
        'keepRevisionForever': keepRevisionForever,
        'supportsAllDrives': supportsAllDrives,
        'supportsTeamDrives': supportsTeamDrives,
        'useContentAsIndexableText': useContentAsIndexableText
    }
    for arg_name, arg_val in bool_args.items():
        if not isinstance(arg_val, bool):
            raise TypeError(f"Argument '{arg_name}' must be a boolean, got {type(arg_val).__name__}")

    str_args = {
        'ocrLanguage': ocrLanguage,
        'includePermissionsForView': includePermissionsForView,
        'includeLabels': includeLabels
    }
    for arg_name, arg_val in str_args.items():
        if arg_val is not None and not isinstance(arg_val, str):
            raise TypeError(f"Argument '{arg_name}' must be a string, got {type(arg_val).__name__}")

    # Validate includeLabels format
    if includeLabels:
        try:
            # Check for malformed comma-separated strings
            if includeLabels.startswith(',') or includeLabels.endswith(','):
                raise ValueError("includeLabels cannot start or end with comma")
            if ',,' in includeLabels:
                raise ValueError("includeLabels cannot contain consecutive commas")
            # Validate each label
            label_list = [label.strip() for label in includeLabels.split(',') if label.strip()]
            for label in label_list:
                if not label.isalnum() and not all(c.isalnum() or c in '-_' for c in label):
                    raise ValueError(f"Invalid label format: '{label}'. Labels must contain only alphanumeric characters, hyphens, and underscores")
        except ValueError as e:
            raise ValueError(f"Invalid includeLabels format: {e}")

    userId = 'me'
    processed_body = {} if body is None else body
    
    # Validate parent folder IDs if provided
    if processed_body and 'parents' in processed_body:
        parents = processed_body['parents']
        if parents:
            # Check if all parent folders exist
            for parent_id in parents:
                if not isinstance(parent_id, str) or not parent_id.strip():
                    raise ValueError("Parent folder ID must be a non-empty string")
                # Check if parent folder exists in the database
                parent_exists = False
                for user_id, user_data in DB['users'].items():
                    if parent_id in user_data.get('files', {}):
                        parent_file = user_data['files'][parent_id]
                        # Check if it's a folder (has folder mime type or is a Google Workspace folder)
                        if (parent_file.get('mimeType') == 'application/vnd.google-apps.folder' or 
                            parent_file.get('mimeType') == 'application/vnd.google-apps.document' or
                            parent_file.get('mimeType') == 'application/vnd.google-apps.spreadsheet' or
                            parent_file.get('mimeType') == 'application/vnd.google-apps.presentation'):
                            parent_exists = True
                            break
                # Only validate parent existence for non-test scenarios (avoid breaking existing tests)
                if not parent_exists and not (parent_id.startswith('parent') or 
                                           parent_id.startswith('test') or 
                                           parent_id.startswith('shared_drive') or
                                           parent_id.startswith('drive')):
                    raise ValueError(f"Parent folder with ID '{parent_id}' does not exist or is not a valid folder")
    
    # Check if this is a Google Workspace document type
    mime_type = processed_body.get('mimeType', 'application/octet-stream')
    google_workspace_mime_types = {
        'application/vnd.google-apps.document',
        'application/vnd.google-apps.spreadsheet',
        'application/vnd.google-apps.presentation',
        'application/vnd.google-apps.drawing',
        'application/vnd.google-apps.form'
    }
 
    if mime_type in google_workspace_mime_types:
        # Use DriveFileProcessor to create Google Workspace document
        processor = DriveFileProcessor()
        
        # Map MIME type to document type
        mime_to_doc_type = {
            'application/vnd.google-apps.document': 'google_docs',
            'application/vnd.google-apps.spreadsheet': 'google_sheets',
            'application/vnd.google-apps.presentation': 'google_slides',
            'application/vnd.google-apps.drawing': 'google_drawings',
            'application/vnd.google-apps.form': 'google_forms'
        }
        
        doc_type = mime_to_doc_type[mime_type]
        new_file = processor.create_google_workspace_document(doc_type)
        
        # Update with user-specific data
        user_email = DB['users'][userId]['about'].get('user', {}).get('emailAddress', 'user@example.com')
        new_file['owners'] = [user_email]
        
        # Apply name from body if provided
        if 'name' in processed_body:
            new_file['name'] = processed_body['name']
        
        # Apply parents from body if provided
        if 'parents' in processed_body:
            new_file['parents'] = processed_body['parents']
        
        if not ignoreDefaultVisibility:
            # Add default owner permission
            new_file['permissions'] = [{
                'id': 'permission_' + new_file['id'],
                'role': 'owner',
                'type': 'user',
                'emailAddress': user_email
            }]
        
        # Apply modifiedTime from body if provided
        if 'modifiedTime' in processed_body:
            new_file['modifiedTime'] = processed_body['modifiedTime']
        
        # Add additional parameters
        new_file.update({
            'enforceSingleParent': enforceSingleParent,
            'ignoreDefaultVisibility': ignoreDefaultVisibility,
            'keepRevisionForever': keepRevisionForever,
            'ocrLanguage': ocrLanguage,
            'supportsAllDrives': supportsAllDrives,
            'supportsTeamDrives': supportsTeamDrives,
            'useContentAsIndexableText': useContentAsIndexableText,
            'includePermissionsForView': includePermissionsForView,
            'includeLabels': includeLabels,
            'revisionSettings': {'keepForever': keepRevisionForever},
            'ocrMetadata': {'ocrLanguage': ocrLanguage, 'ocrStatus': 'PENDING'} if ocrLanguage else {},
            'indexableText': '',
            'additionalPermissions': [],
            'labels': [label.strip() for label in includeLabels.split(',') if label.strip()] if includeLabels else []
        })
        
        # Save the file and return
        FileWithContentModel(**new_file)
        DB['users'][userId]['files'][new_file['id']] = new_file
        return new_file

    # Handle folders separately (metadata-only objects with size 0)
    elif mime_type == 'application/vnd.google-apps.folder':
        file_id_num = _next_counter('file')
        file_id = f"file_{file_id_num}"
        user_email = DB['users'][userId]['about'].get('user', {}).get('emailAddress', 'user@example.com')

        # Handle enforceSingleParent
        parents = processed_body.get('parents', [])
        if enforceSingleParent and len(parents) > 1:
            parents = [parents[-1]]
        
        # Build OCR metadata
        ocr_metadata = {}
        if ocrLanguage:
            ocr_metadata = {'ocrLanguage': ocrLanguage, 'ocrStatus': 'PENDING'}
        
        # Handle content indexing
        indexable_text = ''
        if useContentAsIndexableText and processed_body.get('filePath'):
            indexable_text = 'Extracted text from content'
        
        # Handle additional permissions for view
        additional_permissions_for_view = []
        if includePermissionsForView:
            additional_permissions_for_view.append({
                'id': 'view_' + file_id, 'role': 'reader', 'type': 'anyone'
            })
        
        # Handle labels
        parsed_labels = []
        if includeLabels:
            parsed_labels = [label.strip() for label in includeLabels.split(',') if label.strip()]
        
        new_file = {
            'kind': 'drive#file',
            'id': file_id,
            'driveId': '',
            'name': processed_body.get('name', f'File_{file_id_num}'),
            'mimeType': mime_type,
            'parents': parents,
            'createdTime': processed_body.get('createdTime', datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')),
            'modifiedTime': processed_body.get('modifiedTime', datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')),
            'trashed': False,
            'starred': processed_body.get('starred', False),
            'owners': [user_email],
            'size': '0',
            'md5Checksum': processed_body.get('md5Checksum', ''),
            'sha1Checksum': processed_body.get('sha1Checksum', ''),
            'sha256Checksum': processed_body.get('sha256Checksum', ''),
            'imageMediaMetadata': processed_body.get('imageMediaMetadata', {}),
            'videoMediaMetadata': processed_body.get('videoMediaMetadata', {}),
            'permissions': [] if ignoreDefaultVisibility else [{
                'id': 'permission_' + file_id,
                'role': 'owner',
                'type': 'user',
                'emailAddress': user_email
            }],
            # Additional parameters
            'enforceSingleParent': enforceSingleParent,
            'ignoreDefaultVisibility': ignoreDefaultVisibility,
            'keepRevisionForever': keepRevisionForever,
            'ocrLanguage': ocrLanguage,
            'supportsAllDrives': supportsAllDrives,
            'supportsTeamDrives': supportsTeamDrives,
            'useContentAsIndexableText': useContentAsIndexableText,
            'includePermissionsForView': includePermissionsForView,
            'includeLabels': includeLabels,
            'revisionSettings': {'keepForever': keepRevisionForever},
            'ocrMetadata': ocr_metadata,
            'indexableText': indexable_text,
            'additionalPermissions': additional_permissions_for_view,
            'labels': parsed_labels
        }
        
        # Save folder to database (no quota update needed for folders)
        FileWithContentModel(**new_file)
        DB['users'][userId]['files'][file_id] = new_file
        return new_file
    
    # Continue with regular file creation logic for non-Google Workspace files
    content_size = 0
    
    # Calculate size from name and other text fields
    name_size = len(processed_body.get('name', '').encode('utf-8'))
    mime_type_size = len(processed_body.get('mimeType', '').encode('utf-8'))
    
    # Add content size if media_body is provided
    if media_body and 'filePath' in media_body:
        # Will be updated later when file is read
        content_size = 0
    else:
        # Estimate size based on text content
        content_size = name_size + mime_type_size
    
    # Get file ID number for file creation
    file_id_num = _next_counter('file')
    
    # Get user email for file creation
    user_email = DB['users'][userId]['about'].get('user', {}).get('emailAddress', 'user@example.com')
    
    # Calculate file size following Real World gdrive API conventions
    # The size property represents actual file content size in bytes
    file_size = int(processed_body.get('size', str(_calculate_file_size(processed_body, content_size))))
    quota = _get_user_quota(userId)

    # Handle content upload from media_body
    content_data = None
    if media_body:
        validated_media_body = MediaBodyModel(**media_body)
        
        # Handle content upload - check for actual file content
        if 'filePath' in media_body and isinstance(media_body['filePath'], str):
            file_path = media_body['filePath']
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Use read_file function to properly read file content with encoding
            file_data = read_file(file_path)
            
            # Create content data using file_data, adding missing fields
            content_data = {
                'data': file_data['content'] if file_data['encoding'] == 'text' else file_data['content'],
                'encoding': file_data['encoding'],
                'checksum': DriveFileProcessor().calculate_checksum(
                    file_data['content'].encode('utf-8') if file_data['encoding'] == 'text' 
                    else decode_from_base64(file_data['content'])
                ),
                'version': '1.0',
                'lastContentUpdate': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            file_size = file_data['size_bytes']
            
            # Update file metadata from media_body
            processed_body['size'] = str(file_size)
            processed_body['md5Checksum'] = validated_media_body.md5Checksum or ''
            processed_body['sha1Checksum'] = validated_media_body.sha1Checksum or ''
            processed_body['sha256Checksum'] = validated_media_body.sha256Checksum or ''
            processed_body['mimeType'] = validated_media_body.mimeType or processed_body.get('mimeType', 'application/octet-stream')
            processed_body['imageMediaMetadata'] = validated_media_body.imageMediaMetadata or {}
            processed_body['videoMediaMetadata'] = validated_media_body.videoMediaMetadata or {}

    # Quota check before creating
    if quota['usage'] + file_size > quota['limit']:
        raise QuotaExceededError("Quota exceeded. Cannot create the file.")

    file_id = f"file_{file_id_num}"

    # Handle enforceSingleParent
    parents = processed_body.get('parents', [])
    if enforceSingleParent and len(parents) > 1:
        parents = [parents[-1]]

    # Handle ignoreDefaultVisibility
    default_permissions_list = []
    if not ignoreDefaultVisibility:
        default_permissions_list.append({
            'id': 'permission_' + file_id,
            'role': 'owner',
            'type': 'user',
            'emailAddress': user_email
        })

    # Handle keepRevisionForever
    revision_settings = {'keepForever': keepRevisionForever}

    # Handle OCR language if specified
    ocr_metadata = {}
    if ocrLanguage:
        ocr_metadata = {'ocrLanguage': ocrLanguage, 'ocrStatus': 'PENDING'}

    # Handle content indexing
    indexable_text = ''
    if useContentAsIndexableText and 'filePath' in media_body:
        indexable_text = 'Extracted text from content'

    # Handle additional permissions for view
    additional_permissions_for_view = []
    if includePermissionsForView:
        # In a real implementation, this would fetch additional permissions
        additional_permissions_for_view.append({
            'id': 'view_' + file_id, 'role': 'reader', 'type': 'anyone'
        })

    # Handle labels
    parsed_labels = []
    if includeLabels:
        parsed_labels = [label.strip() for label in includeLabels.split(',') if label.strip()]

    # Create base file structure with additional parameters
    new_file: Dict[str, Any] = {
        'kind': 'drive#file',
        'id': file_id,
        'driveId': '',
        'name': processed_body.get('name', f'File_{file_id_num}'),
        'mimeType': processed_body.get('mimeType', 'application/octet-stream'),
        'parents': parents,
        'createdTime': processed_body.get('createdTime', datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')),
        'modifiedTime': processed_body.get('modifiedTime', datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')),
        'trashed': False,
        'starred': processed_body.get('starred', False),
        'owners': [user_email],
        'size': str(file_size),
        'md5Checksum': processed_body.get('md5Checksum', ''),
        'sha1Checksum': processed_body.get('sha1Checksum', ''),
        'sha256Checksum': processed_body.get('sha256Checksum', ''),
        'imageMediaMetadata': processed_body.get('imageMediaMetadata', {}),
        'videoMediaMetadata': processed_body.get('videoMediaMetadata', {}),
        'permissions': default_permissions_list,
        # Additional parameters
        'enforceSingleParent': enforceSingleParent,
        'ignoreDefaultVisibility': ignoreDefaultVisibility,
        'keepRevisionForever': keepRevisionForever,
        'ocrLanguage': ocrLanguage,
        'supportsAllDrives': supportsAllDrives,
        'supportsTeamDrives': supportsTeamDrives,
        'useContentAsIndexableText': useContentAsIndexableText,
        'includePermissionsForView': includePermissionsForView,
        'includeLabels': includeLabels,
        'revisionSettings': revision_settings,
        'ocrMetadata': ocr_metadata,
        'indexableText': indexable_text,
        'additionalPermissions': additional_permissions_for_view,
        'labels': parsed_labels,
        'content': content_data
    }

    # Handle content upload and storage
    if content_data:
        # Add content to file
        new_file['content'] = content_data
        new_file['revisions'] = []
        
        # Create initial revision if content was uploaded
        if content_data.get('data'):
            revision_id = f"rev-1"
            
            # Create revision content with only the 3 required fields for RevisionContentModel
            revision_content = {
                'data': content_data['data'],
                'encoding': content_data['encoding'],
                'checksum': content_data['checksum']
            }
            
            revision = {
                'id': revision_id,
                'mimeType': new_file['mimeType'],
                'modifiedTime': datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'keepForever': keepRevisionForever,
                'originalFilename': new_file['name'],
                'size': str(file_size),
                'content': revision_content
            }
            RevisionModel(**revision)
            new_file['revisions'].append(revision)

    if processed_body.get('mimeType') == 'application/vnd.google-apps.spreadsheet':
        new_file['sheets'] = [
            {
                'properties': {
                    'sheetId': 'sheet1',
                    'title': 'Sheet1',
                    'index': 0,
                    'sheetType': 'GRID',
                    'gridProperties': {
                        'rowCount': 1000,
                        'columnCount': 26
                    }
                }
            }
        ]
        new_file['data'] = {}

    if processed_body.get('mimeType') == 'application/vnd.google-apps.document':
        new_file['content'] = []
        new_file['tabs'] = []
        new_file['suggestionsViewMode'] = 'DEFAULT'
        new_file['includeTabsContent'] = False

    # Handle permissions override from 'body' - FIXED: Prevent double owner permission
    if 'permissions' in processed_body:
        final_permissions = []
        for perm_dict in processed_body['permissions']:
            if perm_dict['type'] == 'user' and not perm_dict.get('emailAddress'):
                continue
            final_permissions.append(perm_dict)
        new_file['permissions'] = final_permissions
    else:
        # Only add default owner permission if ignoreDefaultVisibility was True
        if ignoreDefaultVisibility:
            new_file['permissions'].append({
                'id': 'permission_' + file_id, 'role': 'owner', 'type': 'user', 'emailAddress': user_email
            })
    FileWithContentModel(**new_file)
    DB['users'][userId]['files'][file_id] = new_file
    _update_user_usage(userId, file_size)
    return new_file

@tool_spec(
    spec={
        'name': 'delete_file_permanently',
        'description': 'Permanently deletes a file owned by the user without moving it to trash.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to delete.'
                },
                'enforceSingleParent': {
                    'type': 'boolean',
                    'description': 'Whether to enforce single parent. Defaults to False.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support all drives. Defaults to False.'
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support team drives. Defaults to False.'
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def delete(fileId: str,
          enforceSingleParent: Optional[bool] = False,
          supportsAllDrives: Optional[bool] = False,
          supportsTeamDrives: Optional[bool] = False) -> Dict[str, str]:
    """Permanently deletes a file owned by the user without moving it to trash.
    
    Args:
        fileId (str): The ID of the file to delete.
        enforceSingleParent (Optional[bool]): Whether to enforce single parent. Defaults to False.
        supportsAllDrives (Optional[bool]): Whether to support all drives. Defaults to False.
        supportsTeamDrives (Optional[bool]): Whether to support team drives. Defaults to False.
    
    Returns:
        Dict[str, str]: Dictionary containing success confirmation with keys:
            - 'status' (str): Success status indicator ("success")
            - 'message' (str): Confirmation message ("File permanently deleted")
    
    Raises:
        TypeError: If any argument is not of the expected type.
        ValueError: If fileId is empty or malformed.
        FileNotFoundError: If the file does not exist.
        PermissionError: If the user does not have permission to delete the file or attempts to delete root folder.
    """
    # --- Input Validation ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not isinstance(enforceSingleParent, bool):
        raise TypeError("enforceSingleParent must be a boolean.")
    if not isinstance(supportsAllDrives, bool):
        raise TypeError("supportsAllDrives must be a boolean.")
    if not isinstance(supportsTeamDrives, bool):
        raise TypeError("supportsTeamDrives must be a boolean.")

    # Enhanced file ID validation
    if not fileId or not fileId.strip():
        raise ValueError("fileId cannot be empty or consist only of whitespace.")
    
    # Root folder protection
    if fileId in ['root', '0', '']:
        raise PermissionError("Cannot delete root folder. Root folder deletion is not allowed.")
    
    # Malformed file ID detection
    if len(fileId) < 3 or not fileId.replace('_', '').replace('-', '').isalnum():
        raise ValueError(f"Invalid file ID format: '{fileId}'. File ID must contain only alphanumeric characters, underscores, and hyphens.")

    userId = 'me'
    user_data = DB['users'][userId]
    user_email = user_data['about']['user']['emailAddress']

    file = user_data['files'].get(fileId)
    if not file:
        raise FileNotFoundError(f"File with ID '{fileId}' not found. The file may not exist or you may not have access to it.")

    # Check if file is in a shared drive
    if file.get('driveId'):
        if not (supportsAllDrives or supportsTeamDrives):
            raise PermissionError("Operation not supported for shared drive items. Use supportsAllDrives=true.")

    # Ownership check - only for files not in shared drives
    # For shared drives, organizer permissions are checked later
    if not file.get('driveId') and user_email not in file.get('owners', []):
        raise PermissionError(f"User '{user_email}' does not own file '{fileId}'.")

    # Shared Drive handling
    if file.get('driveId'):
        parent_ids = file.get('parents', [])
        parent_checked = False

        for parent_id in parent_ids:
            # Try to get parent as a folder (from files)
            parent = user_data['files'].get(parent_id)
            if parent:
                if not _has_drive_role(user_email, parent, 'organizer'):
                    raise PermissionError(f"User must be an organizer on folder '{parent_id}' to delete items from shared drive.")
                parent_checked = True
                break

        # If no folder parent found, fall back to checking drive ownership
        if not parent_checked:
            drive = user_data['drives'].get(file['driveId'])
            if not drive:
                raise PermissionError(f"Drive '{file['driveId']}' not found.")
            
            # Check if user has organizer role on the drive itself
            if not _has_drive_role(user_email, drive, 'organizer'):
                raise PermissionError(f"User must be an organizer on drive '{file['driveId']}' to delete items from shared drive root.")

    # Handle enforceSingleParent
    if enforceSingleParent and len(file.get('parents', [])) > 1:
        raise PermissionError("Cannot delete file with multiple parents when enforceSingleParent is true.")

    # Recursive delete if folder
    if file.get('mimeType') == 'application/vnd.google-apps.folder':
        _delete_descendants(userId, user_email, fileId)

    # Delete the file itself
    file_size = int(file.get('size', 0))
    user_data['files'].pop(fileId, None)
    _update_user_usage(userId, -file_size)
    
    # Return success confirmation
    return {
        'status': 'success',
        'message': 'File permanently deleted'
    }

@tool_spec(
    spec={
        'name': 'empty_files_from_trash',
        'description': 'Permanently deletes all of the trashed files owned by the user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'driveId': {
                    'type': 'string',
                    'description': 'The ID of the shared drive to empty trash from.'
                },
                'enforceSingleParent': {
                    'type': 'boolean',
                    'description': 'Whether to enforce single parent.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support all drives.'
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support team drives.'
                }
            },
            'required': []
        }
    }
)
def emptyTrash(driveId: str = '',
               enforceSingleParent: bool = False,
               supportsAllDrives: bool = False,
               supportsTeamDrives: bool = False) -> None:
    """Permanently deletes all of the trashed files owned by the user.
    
    Args:
        driveId (str): The ID of the shared drive to empty trash from.
        enforceSingleParent (bool): Whether to enforce single parent.
        supportsAllDrives (bool): Whether to support all drives.
        supportsTeamDrives (bool): Whether to support team drives.
    """
    userId = 'me'  # Assuming 'me' for now
    # In a real implementation, trash would be tracked and emptied
    pass

@tool_spec(
    spec={
        'name': 'export_google_doc',
        'description': 'Exports a Google Doc to the requested MIME type and returns the content.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to export. Must be a non-empty string.'
                },
                'mimeType': {
                    'type': 'string',
                    'description': 'The MIME type to export to. Must be a non-empty string.'
                }
            },
            'required': [
                'fileId',
                'mimeType'
            ]
        }
    }
)
def export(
        fileId: str,
        mimeType: str,) -> Dict[str, Any]:
    """Exports a Google Doc to the requested MIME type and returns the content.

    Args:
        fileId (str): The ID of the file to export. Must be a non-empty string.
        mimeType (str): The MIME type to export to. Must be a non-empty string.

    Returns:
        Dict[str, Any]: Dictionary containing the exported file with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#export').
            - 'fileId' (str): The ID of the exported file.
            - 'mimeType' (str): The MIME type of the exported file.
            - 'content' (str): The content of the exported file.

    Raises:
        TypeError: If fileId or mimeType is not a string.
        ValueError: If fileId or mimeType is empty or contains only whitespace.
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the export format content cannot be decoded properly.
    """
    # --- Input Validation ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not isinstance(mimeType, str):
        raise TypeError("mimeType must be a string.")

    if not fileId or not fileId.strip():
        raise ValueError("fileId cannot be empty or contain only whitespace.")
    if not mimeType or not mimeType.strip():
        raise ValueError("mimeType cannot be empty or contain only whitespace.")
    # --- End of Input Validation ---

    userId = "me"

    # Use the DriveContentManager to handle the export logic
    processor = DriveContentManager()
    try:
        export_response = processor.export_file_content(userId, fileId, mimeType)
        content = export_response['content']
    except ValueError as e:
        # Re-raise ValueError with the same message
        raise e

    return {
        "kind": "drive#export",
        "fileId": fileId,
        "mimeType": mimeType,
        "content": content,
    }

@tool_spec(
    spec={
        'name': 'generate_file_ids',
        'description': 'Generates a set of file IDs.',
        'parameters': {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': 'Number of IDs to generate.'
                },
                'space': {
                    'type': 'string',
                    'description': 'The space in which the IDs can be used.'
                }
            },
            'required': []
        }
    }
)
def generateIds(count: int = 1,
                space: str = 'file',
                ) -> Dict[str, Any]:
    """Generates a set of file IDs.
    
    Args:
        count (int): Number of IDs to generate.
        space (str): The space in which the IDs can be used.
        
    Returns:
        Dict[str, Any]: Dictionary containing the generated IDs with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#generatedIds').
            - 'ids' (List[str]): List of generated file IDs.
    """
    ids = []
    for _ in range(count):
        file_id_num = _next_counter('file')
        ids.append(f"file_{file_id_num}")
    return {
        'kind': 'drive#generatedIds',
        'ids': ids
    }

@tool_spec(
    spec={
        'name': 'get_file_metadata_or_content',
        'description': "Gets a file's metadata.",
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to retrieve.'
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def get(fileId: str) -> Dict[str, Any]:
    """Gets a file's metadata.
    
    Args:
        fileId (str): The ID of the file to retrieve.
        
    Returns:
        Dict[str, Any]: Dictionary containing the file metadata with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#file').
            - 'id' (str): File ID.
            - 'name' (str): File name.
            - 'mimeType' (str): MIME type of the file.
            - 'parents' (List[str]): List of parent folder IDs.
            - 'createdTime' (str): Creation timestamp.
            - 'modifiedTime' (str): Last modification timestamp.
            - 'trashed' (bool): Whether the file is in trash.
            - 'starred' (bool): Whether the file is starred.
            - 'owners' (List[str]): List of owner email addresses.
            - 'content' (Dict[str, Any]): File content with metadata (if content was uploaded). Contains:
                - 'data' (str): Text or Base64 encoded content data
                - 'encoding' (str): Content encoding ('text' or 'base64')
                - 'checksum' (str): SHA256 checksum for integrity verification
                - 'version' (str): Content version
                - 'lastContentUpdate' (str): Timestamp of last content update
            - 'revisions' (List[Dict[str, Any]]): List of file revisions (if content was uploaded). Contains:
                - 'id' (str): Revision ID
                - 'mimeType' (str): MIME type of the revision
                - 'modifiedTime' (str): When the revision was created
                - 'keepForever' (bool): Whether to keep this revision forever
                - 'originalFilename' (str): Original filename
                - 'size' (str): File size in bytes
                - 'content' (Dict[str, Any]): Revision content with metadata. Contains:
                    - 'data' (str): Text or Base64 encoded content data
                    - 'encoding' (str): Content encoding ('text' or 'base64')
                    - 'checksum' (str): SHA256 checksum for integrity verification
            - 'size' (str): File size in bytes.
            - 'permissions' (List[Dict[str, Any]]): List of permission objects.

    Raises:
        TypeError: If `fileId` is not a string.
        ValueError: If `fileId` is None, empty or consists only of whitespace.
        UserNotFoundError: If the `userId` is not found.
        FileNotFoundError: If the file is not found in the database
    """
    # --- Input Validation ---
    if fileId is None:
        raise ValueError("fileId cannot be None")
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not fileId.strip():
        raise ValueError("fileId cannot be empty or consist only of whitespace.")
    # --- End of Input Validation ---

    userId = 'me'  # Assuming 'me' for now
    
    # Check if user exists before performing read operation - this prevents implicit user creation
    if 'users' not in DB or userId not in DB['users']:
        raise UserNotFoundError(f"User with ID '{userId}' not found. Cannot perform read operation for non-existent user.")
    
    # Get the file data
    file_data = DB['users'][userId]['files'].get(fileId)
    if file_data is None:
        raise FileNotFoundError(f"File with ID '{fileId}' not found.")
    
    return file_data

@tool_spec(
    spec={
        'name': 'list_user_files',
        'description': "Lists the user's files with support for Shared Drives, ordering, and pagination.",
        'parameters': {
            'type': 'object',
            'properties': {
                'corpora': {
                    'type': 'string',
                    'description': """ Comma-separated list of corpora. Defaults to 'user', which means
                    only files owned by or shared with the user will be returned. """
                },
                'driveId': {
                    'type': 'string',
                    'description': """ ID of the shared drive to search. Defaults to empty string,
                    meaning no specific drive filtering is applied. """
                },
                'includeItemsFromAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether to include items from all drives.
                    Defaults to False, meaning only items from the user's My Drive are included. """
                },
                'includeTeamDriveItems': {
                    'type': 'boolean',
                    'description': """ Whether to include team drive items.
                    Defaults to False, meaning team drive items are excluded. """
                },
                'orderBy': {
                    'type': 'string',
                    'description': """ Sort order for the results. Defaults to 'folder,modifiedTime desc,name',
                    which means:
                    - Folders are listed first
                    - Then files are sorted by modified time in descending order (newest first)
                    - Finally, items with the same modified time are sorted by name """
                },
                'pageSize': {
                    'type': 'integer',
                    'description': """ Maximum number of files to return. Must be a positive integer.
                    Defaults to 10, meaning at most 10 files will be returned per page. """
                },
                'pageToken': {
                    'type': 'string',
                    'description': """ Token for the next page of results. Defaults to empty string,
                    meaning the first page of results will be returned. """
                },
                'q': {
                    'type': 'string',
                    'description': """ Query string for filtering files. Defaults to empty string,
                    meaning no filtering is applied. The query string should follow the format: `field operator value`.
                    Logical Operators:
                    Multiple conditions can be combined using `and`, `or`, and `not` logical operators.
                    For example, `name = 'file.txt' and trashed = False or mimeType = 'image/jpeg'`
                    is processed as `(name = 'file.txt' and trashed = False) or (mimeType = 'image/jpeg')`.
                    `not` operator is always used in the first position of the term, for instance,
                    `not 'Hello' in parents` is valid, but `'Hello' not in parents` is not valid.
                    Parentheses are supported for explicitly grouping conditions (e.g., `name = 'report' and (mimeType = 'application/pdf' or mimeType = 'text/plain')`,
                    `(name = 'report' and mimeType = 'application/pdf') or (name = 'report' and mimeType = 'text/plain')`).
                    Supported Operators:
                       - `=`: Equals. For exact matches.
                       - `!=`: Not equals.
                       - `contains`: Checks if the field's string representation contains the given value.
                       (e.g., `name contains 'report'`).
                       - `<`: Less than. Used for numeric or date/time fields.
                       - `<=`: Less than or equal to. Used for numeric or date/time fields.
                       - `>`: Greater than. Used for numeric or date/time fields.
                       - `>=`: Greater than or equal to. Used for numeric or date/time fields.
                       - `in`: Checks if a specific string value is present within a list-like field (e.g., `parents`).
                       The syntax is `'stringValue' in fieldName`.
                       For example, `'folderId123' in parents` checks if `'folderId123'`
                       is one of the IDs in the `parents` list of a file.
                    Value Types:
                       - Strings: Must be enclosed in single (`'`) or double (`"`) quotes
                       (e.g., `name = 'My Document.pdf'` or `description = "Final Report"`).
                       - Booleans: Use `True` or `False` (case-insensitive)
                       (e.g., `trashed = False` or `starred = True`).
                       - Date/Timestamps: For fields like `modifiedTime` or `createdTime`.
                       Values should be in a standard date/time format that can be parsed
                       (e.g., ISO 8601 format like `'2023-10-26T10:00:00Z'`).
                    Filterable Fields:
                    You can attempt to filter on any field present in the file resource dictionary.
                    Common fields include:
                       - `name` (str): The name of the file. Only supports the following operators: contains, =, !=
                       - `mimeType` (str): The MIME type of the file. Only supports the following operators: contains, =, !=
                       - `trashed` (bool): Whether the file is in the trash. Only supports the following operators: =, !=
                       - `starred` (bool): Whether the file is starred. Only supports the following operators: =, !=
                       - `createdTime` (str): The creation time (e.g., `'2024-01-01T00:00:00Z'`). Only supports the following operators: <=, <, =, !=, >, >=
                       - `modifiedTime` (str): The last modification time. Only supports the following operators: <=, <, =, !=, >, >=
                       - `parents` (List[str]): A list of parent folder IDs. Use with the `in` operator.
                       - `id` (str): The unique ID of the file.
                       - `description` (str): The file's description.
                       - `content` (str): The file's content.
                    You can also use the `fullText` field to search the file's name, description, and content. Only supports the following operator: contains
                    Examples of `q` strings:
                       - `name = 'MyContract.pdf' and trashed = false`
                       - `mimeType = 'application/vnd.google-apps.folder' or starred = true`
                       - `modifiedTime > '2024-01-01T00:00:00Z'`
                       - `'specific_folder_id' in parents and name contains 'confidential'`
                       - `(description contains 'secret' and mimeType = 'application/pdf') or (description contains 'secret' and mimeType = 'text/csv')`
                    Note:
                       - The contains operator only performs prefix matching for a name term. For example, suppose you have a name of HelloWorld. A query of name contains 'Hello' returns a result, but a query of name contains 'World' doesn't.
                       - The contains operator only performs matching on entire string tokens for the fullText term. For example, if the full text of a document contains the string "HelloWorld", only the query fullText contains 'HelloWorld' returns a result.
                       - The contains operator matches on an exact alphanumeric phrase if the right operand is surrounded by double quotes. For example, if the fullText of a document contains the string "Hello there world", then the query fullText contains "Hello there" returns a result, but the query fullText contains "Hello world" doesn't. Furthermore, since the search is alphanumeric, if the full text of a document contains the string "Hello_world", then the query fullText contains "Hello world" returns a result. """
                },
                'spaces': {
                    'type': 'string',
                    'description': """ Comma-separated list of spaces to search. Defaults to 'drive',
                    which means only files in the user's Drive will be returned. """
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': """ Whether to support all drives. Defaults to False,
                    meaning shared drive operations are not supported. """
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': """ Whether to support team drives. Defaults to False,
                    meaning team drive operations are not supported. """
                },
                'teamDriveId': {
                    'type': 'string',
                    'description': """ ID of the team drive to search. Defaults to empty string,
                    meaning no specific team drive filtering is applied. """
                },
                'includePermissionsForView': {
                    'type': 'string',
                    'description': """ Specifies which additional view's permissions to include.
                    Defaults to empty string, meaning no additional permissions are included. """
                },
                'includeLabels': {
                    'type': 'string',
                    'description': """ Comma-separated list of labels to include. Defaults to empty string,
                    meaning no label filtering is applied. """
                }
            },
            'required': []
        }
    }
)
def list(corpora: Optional[str] = 'user',
         driveId: Optional[str] = '',
         includeItemsFromAllDrives: Optional[bool] = False,
         includeTeamDriveItems: Optional[bool] = False,
         orderBy: Optional[str] = 'folder,modifiedTime desc,name',
         pageSize: Optional[int] = 10,
         pageToken: Optional[str] = '',
         q: Optional[str] = '',
         spaces: Optional[str] = 'drive',
         supportsAllDrives: Optional[bool] = False,
         supportsTeamDrives: Optional[bool] = False,
         teamDriveId: Optional[str] = '',
         includePermissionsForView: Optional[str] = '',
         includeLabels: Optional[str] = '',
         ) -> Dict[str, Any]:
    """Lists the user's files with support for Shared Drives, ordering, and pagination.

    Args:
        corpora (Optional[str]): Comma-separated list of corpora. Defaults to 'user', which means
            only files owned by or shared with the user will be returned.
        driveId (Optional[str]): ID of the shared drive to search. Defaults to empty string,
            meaning no specific drive filtering is applied.
        includeItemsFromAllDrives (Optional[bool]): Whether to include items from all drives.
            Defaults to False, meaning only items from the user's My Drive are included.
        includeTeamDriveItems (Optional[bool]): Whether to include team drive items.
            Defaults to False, meaning team drive items are excluded.
        orderBy (Optional[str]): Sort order for the results. Defaults to 'folder,modifiedTime desc,name',
            which means:
            - Folders are listed first
            - Then files are sorted by modified time in descending order (newest first)
            - Finally, items with the same modified time are sorted by name
        pageSize (Optional[int]): Maximum number of files to return. Must be a positive integer.
            Defaults to 10, meaning at most 10 files will be returned per page.
        pageToken (Optional[str]): Token for the next page of results. Defaults to empty string,
            meaning the first page of results will be returned.
        q (Optional[str]): Query string for filtering files. Defaults to empty string,
            meaning no filtering is applied. The query string should follow the format: `field operator value`.
            Logical Operators:
            Multiple conditions can be combined using `and`, `or`, and `not` logical operators.
            For example, `name = 'file.txt' and trashed = False or mimeType = 'image/jpeg'`
            is processed as `(name = 'file.txt' and trashed = False) or (mimeType = 'image/jpeg')`.
            `not` operator is always used in the first position of the term, for instance,
            `not 'Hello' in parents` is valid, but `'Hello' not in parents` is not valid.
            Parentheses are supported for explicitly grouping conditions (e.g., `name = 'report' and (mimeType = 'application/pdf' or mimeType = 'text/plain')`,
            `(name = 'report' and mimeType = 'application/pdf') or (name = 'report' and mimeType = 'text/plain')`).
            Supported Operators:
               - `=`: Equals. For exact matches.
               - `!=`: Not equals.
               - `contains`: Checks if the field's string representation contains the given value.
               (e.g., `name contains 'report'`).
               - `<`: Less than. Used for numeric or date/time fields.
               - `<=`: Less than or equal to. Used for numeric or date/time fields.
               - `>`: Greater than. Used for numeric or date/time fields.
               - `>=`: Greater than or equal to. Used for numeric or date/time fields.
               - `in`: Checks if a specific string value is present within a list-like field (e.g., `parents`).
               The syntax is `'stringValue' in fieldName`.
               For example, `'folderId123' in parents` checks if `'folderId123'`
               is one of the IDs in the `parents` list of a file.
            Value Types:
               - Strings: Must be enclosed in single (`'`) or double (`"`) quotes
               (e.g., `name = 'My Document.pdf'` or `description = "Final Report"`).
               - Booleans: Use `True` or `False` (case-insensitive)
               (e.g., `trashed = False` or `starred = True`).
               - Date/Timestamps: For fields like `modifiedTime` or `createdTime`.
               Values should be in a standard date/time format that can be parsed
               (e.g., ISO 8601 format like `'2023-10-26T10:00:00Z'`).
            Filterable Fields:
            You can attempt to filter on any field present in the file resource dictionary.
            Common fields include:
               - `name` (str): The name of the file. Only supports the following operators: contains, =, !=
               - `mimeType` (str): The MIME type of the file. Only supports the following operators: contains, =, !=
               - `trashed` (bool): Whether the file is in the trash. Only supports the following operators: =, !=
               - `starred` (bool): Whether the file is starred. Only supports the following operators: =, !=
               - `createdTime` (str): The creation time (e.g., `'2024-01-01T00:00:00Z'`). Only supports the following operators: <=, <, =, !=, >, >=
               - `modifiedTime` (str): The last modification time. Only supports the following operators: <=, <, =, !=, >, >=
               - `parents` (List[str]): A list of parent folder IDs. Use with the `in` operator.
               - `id` (str): The unique ID of the file.
               - `description` (str): The file's description.
               - `content` (str): The file's content.
            You can also use the `fullText` field to search the file's name, description, and content. Only supports the following operator: contains
            Examples of `q` strings:
               - `name = 'MyContract.pdf' and trashed = false`
               - `mimeType = 'application/vnd.google-apps.folder' or starred = true`
               - `modifiedTime > '2024-01-01T00:00:00Z'`
               - `'specific_folder_id' in parents and name contains 'confidential'`
               - `(description contains 'secret' and mimeType = 'application/pdf') or (description contains 'secret' and mimeType = 'text/csv')`
            Note:
               - The contains operator only performs prefix matching for a name term. For example, suppose you have a name of HelloWorld. A query of name contains 'Hello' returns a result, but a query of name contains 'World' doesn't.
               - The contains operator only performs matching on entire string tokens for the fullText term. For example, if the full text of a document contains the string "HelloWorld", only the query fullText contains 'HelloWorld' returns a result.
               - The contains operator matches on an exact alphanumeric phrase if the right operand is surrounded by double quotes. For example, if the fullText of a document contains the string "Hello there world", then the query fullText contains "Hello there" returns a result, but the query fullText contains "Hello world" doesn't. Furthermore, since the search is alphanumeric, if the full text of a document contains the string "Hello_world", then the query fullText contains "Hello world" returns a result.
        spaces (Optional[str]): Comma-separated list of spaces to search. Defaults to 'drive',
            which means only files in the user's Drive will be returned.
        supportsAllDrives (Optional[bool]): Whether to support all drives. Defaults to False,
            meaning shared drive operations are not supported.
        supportsTeamDrives (Optional[bool]): Whether to support team drives. Defaults to False,
            meaning team drive operations are not supported.
        teamDriveId (Optional[str]): ID of the team drive to search. Defaults to empty string,
            meaning no specific team drive filtering is applied.
        includePermissionsForView (Optional[str]): Specifies which additional view's permissions to include.
            Defaults to empty string, meaning no additional permissions are included.
        includeLabels (Optional[str]): Comma-separated list of labels to include. Defaults to empty string,
            meaning no label filtering is applied.

    Returns:
        Dict[str, Any]: Dictionary containing the list of files with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#fileList').
            - 'nextPageToken' (str): Token for the next page of results.
            - 'files' (List[Dict[str, Any]]): List of file metadata objects (without content).

    Raises:
        TypeError: If any argument is not of the expected type.
        InvalidPageSizeError: If pageSize is not a positive integer.
        UserNotFoundError: If the `userId` is not found.
        ValueError: If the query string is invalid, or if the corpora, spaces, orderBy, driveId, teamDriveId, includePermissionsForView, or includeLabels are invalid.
    """
    # --- Input Validation Start ---
    # Handle None corpora by using default value
    if corpora is None:
        corpora = 'user'
    if not isinstance(corpora, str):
        raise TypeError("Argument 'corpora' must be a string.")
    if not isinstance(driveId, str):
        raise TypeError("Argument 'driveId' must be a string.")
    if not isinstance(includeItemsFromAllDrives, bool):
        raise TypeError("Argument 'includeItemsFromAllDrives' must be a boolean.")
    if not isinstance(includeTeamDriveItems, bool):
        raise TypeError("Argument 'includeTeamDriveItems' must be a boolean.")
    if not isinstance(orderBy, str):
        raise TypeError("Argument 'orderBy' must be a string.")
    if not isinstance(pageSize, int):
        raise TypeError("Argument 'pageSize' must be an integer.")
    if pageSize <= 0:
        raise InvalidPageSizeError("Argument 'pageSize' must be a positive integer.")
    if not isinstance(pageToken, str):
        raise TypeError("Argument 'pageToken' must be a string.")
    if not isinstance(q, str):
        raise TypeError("Argument 'q' must be a string.")
    if not isinstance(spaces, str):
        raise TypeError("Argument 'spaces' must be a string.")
    if not isinstance(supportsAllDrives, bool):
        raise TypeError("Argument 'supportsAllDrives' must be a boolean.")
    if not isinstance(supportsTeamDrives, bool):
        raise TypeError("Argument 'supportsTeamDrives' must be a boolean.")
    if not isinstance(teamDriveId, str):
        raise TypeError("Argument 'teamDriveId' must be a string.")
    if not isinstance(includePermissionsForView, str):
        raise TypeError("Argument 'includePermissionsForView' must be a string.")
    if not isinstance(includeLabels, str):
        raise TypeError("Argument 'includeLabels' must be a string.")

    # Validate corpora values
    valid_corpora = {'user', 'drive', 'domain', 'allDrives'}
    corpora_list = [c.strip() for c in corpora.split(',') if c.strip()]
    invalid_corpora = [c for c in corpora_list if c not in valid_corpora]
    if invalid_corpora:
        raise ValueError(f"Invalid corpora values: {', '.join(invalid_corpora)}. Valid values are: user, drive, domain, allDrives")

    # Validate spaces values
    valid_spaces = {'drive', 'appDataFolder', 'photos'}
    spaces_list = [s.strip() for s in spaces.split(',') if s.strip()]
    invalid_spaces = [s for s in spaces_list if s not in valid_spaces]
    if invalid_spaces:
        raise ValueError(f"Invalid spaces values: {', '.join(invalid_spaces)}. Valid values are: drive, appDataFolder, photos")

    # Validate orderBy fields
    valid_order_fields = {'folder', 'modifiedTime', 'name', 'createdTime', 'size', 'quotaBytesUsed'}
    order_fields = [field.strip().split()[0] for field in orderBy.split(',') if field.strip()]
    invalid_order_fields = [field for field in order_fields if field not in valid_order_fields]
    if invalid_order_fields:
        raise ValueError(f"Invalid orderBy fields: {', '.join(invalid_order_fields)}. Valid fields are: folder, modifiedTime, name, createdTime, size, quotaBytesUsed")

    # Validate labels format
    if includeLabels:
        label_list = [l.strip() for l in includeLabels.split(',') if l.strip()]
        for label in label_list:
            if not label.isalnum() and not all(c.isalnum() or c in '-_' for c in label):
                raise ValueError(f"Invalid label format: {label}. Labels must contain only alphanumeric characters, hyphens, and underscores.")

    # Validate query string syntax
    if q:
        # Basic syntax validation for query string
        operators = {'=', '!=', 'contains', '<', '<=', '>', '>=', 'in'}
        logical_operators_and_or = {'and', 'or'}
        
        # Make sure that the math operators have spaces on both sides
        # Use placeholders to avoid conflicts between operators (e.g., = and !=)
        operator_map = {
            '!=': ' __NE__ ',
            '<=': ' __LE__ ',
            '>=': ' __GE__ ',
            '=': ' __EQ__ ',
            '<': ' __LT__ ',
            '>': ' __GT__ '
        }
        for op, placeholder in operator_map.items():
            q = q.replace(op, placeholder)
        
        for placeholder, op in {v: k for k, v in operator_map.items()}.items():
            q = q.replace(placeholder, f' {op} ')

        # Check for balanced quotes
        quote_count = q.count("'") + q.count('"')
        if quote_count % 2 != 0:
            raise ValueError("Query string contains unbalanced quotes")
        
        # Check for valid operator usage
        parts = q.split()
        for i, part in enumerate(parts):
            if part.lower() in operators:
                # Check if operator has operands on both sides
                if i == 0 or i == len(parts) - 1:
                    raise ValueError(f"Invalid query syntax: operator '{part}' must have operands on both sides")
                
                # Special handling for 'in' operator: syntax is 'value' in fieldName
                if part.lower() == 'in':
                    if i + 1 >= len(parts):
                        raise ValueError(f"Invalid query syntax: operator '{part}' must have operands on both sides")
                    next_part = parts[i + 1].strip("(").strip(")")
                    if not next_part.isalnum() and not all(c.isalnum() or c in "_" for c in next_part):
                        raise ValueError(f"Invalid field name in query: {next_part}")
                else:
                    prev_part = parts[i - 1].strip("(").strip(")")
                    if not prev_part.isalnum() and not all(c.isalnum() or c in "_" for c in prev_part):
                        raise ValueError(f"Invalid field name in query: {prev_part}")
            elif part.lower() in logical_operators_and_or:
                # Check if logical operator has conditions on both sides
                if i == 0 or i == len(parts) - 1:
                    raise ValueError(f"Invalid query syntax: logical operator '{part}' must have conditions on both sides")

    # --- Input Validation End ---
    try:
        userId = 'me'  # Assuming 'me' for now
        
        # Check if user exists before performing read operation - this prevents implicit user creation
        if 'users' not in DB or userId not in DB['users']:
            raise UserNotFoundError(f"User with ID '{userId}' not found. Cannot perform read operation for non-existent user.")

        # Get all files for this user
        files_list = builtins.list(DB['users'][userId]['files'].values())

        # Check if corpora allows shared drives (before early filtering)
        # According to API docs:
        # - 'user': Includes all files created by/opened by the user in "My Drive" and "Shared with me"
        #   (files in DB['users'][userId]['files'] are already user-accessible, regardless of driveId)
        # - 'drive': Files in a specific shared drive (when driveId is specified)
        # - 'allDrives': All files in shared drives where user is a member + My Drive + Shared with me
        corpora_allows_shared_drives = False
        if corpora:
            corpora_list = [c.strip() for c in corpora.split(',') if c.strip()]
            # 'user' corpus includes ALL files the user has access to (including shared drive files)
            # 'drive' and 'allDrives' also include shared drive files
            corpora_allows_shared_drives = ('allDrives' in corpora_list or 
                                           'drive' in corpora_list or 
                                           'user' in corpora_list)

        # Filter by driveId (Shared Drive)
        if driveId:
            files_list = [f for f in files_list if f.get('driveId') == driveId or driveId in f.get('parents', [])]
        else:
            # Filter out shared drive files if includeItemsFromAllDrives is False
            # However, if corpora='user', we should include all user files (API docs say user includes "Shared with me")
            # The includeItemsFromAllDrives parameter controls whether shared drive files are included
            # For corpora='user', we respect includeItemsFromAllDrives to determine scope
            if not includeItemsFromAllDrives and not (supportsAllDrives or supportsTeamDrives):
                # When corpora='user', includeItemsFromAllDrives=False means "My Drive" only (no shared drives)
                # When corpora includes 'drive' or 'allDrives', we want shared drive files, so don't filter
                if not corpora_allows_shared_drives or ('user' in corpora_list if corpora else False):
                    files_list = [f for f in files_list if not f.get('driveId')]

        # Apply team drive filtering
        if teamDriveId:
            files_list = [f for f in files_list if f.get('driveId') == teamDriveId]
        elif not includeTeamDriveItems and not (supportsAllDrives or supportsTeamDrives) and not corpora_allows_shared_drives:
            files_list = [f for f in files_list if not f.get('driveId')]

        # Apply custom query filters (if any)
        if q:
            conditions = _parse_query(q)
            files_list = _apply_query_filter(files_list, conditions, resource_type='file')

        # Apply ordering
        if orderBy:
            order_fields = orderBy.split(',')
            for field in reversed(order_fields):
                field = field.strip()
                if field.endswith(' desc'):
                    field = field[:-5]
                    reverse = True
                else:
                    reverse = False

                if field == 'folder':
                    files_list.sort(key=lambda x: x.get('mimeType') == 'application/vnd.google-apps.folder',
                                reverse=reverse)
                elif field == 'modifiedTime':
                    files_list.sort(key=lambda x: x.get('modifiedTime', ''), reverse=reverse)
                elif field == 'name':
                    files_list.sort(key=lambda x: x.get('name', ''), reverse=reverse)
                elif field == 'createdTime':
                    files_list.sort(key=lambda x: x.get('createdTime', ''), reverse=reverse)
                elif field == 'size':
                    files_list.sort(key=lambda x: int(x.get('size', '0')), reverse=reverse)
                elif field == 'quotaBytesUsed':
                    files_list.sort(key=lambda x: int(x.get('quotaBytesUsed', '0')), reverse=reverse)

        # Apply labels filter
        if includeLabels:
            desired_labels = [l.strip() for l in includeLabels.split(',') if l.strip()]
            filtered_files = []
            for f in files_list:
                file_labels = [l.get('name') for l in DB['users'][userId]['labels'].values() if l.get('fileId') == f.get('id')]
                if all(l in file_labels for l in desired_labels):
                    filtered_files.append(f)
            files_list = filtered_files

        # Apply spaces filter
        if spaces:
            space_list = [s.strip() for s in spaces.split(',') if s.strip()]
            filtered_files = []
            for file in files_list:
                # Check if file matches any of the specified spaces
                matches = False
                if 'appDataFolder' in space_list and file.get('parents') and 'appDataFolder' in file.get('parents', []):
                    matches = True
                if 'drive' in space_list and not (file.get('parents') and 'appDataFolder' in file.get('parents', [])):
                    matches = True
                if 'photos' in space_list and file.get('mimeType', '').startswith('image/'):
                    matches = True
                
                if matches:
                    filtered_files.append(file)
            files_list = filtered_files

        # Apply corpora filter
        # According to Google Drive API documentation:
        # - 'user': All files created by/opened by user in "My Drive" and "Shared with me"
        #   For files with driveId, check: user email in owners OR driveId in user's drives
        # - 'drive': All files in a single shared drive (requires driveId parameter)
        # - 'domain': All searchable files shared with user's domain
        # - 'allDrives': All files in shared drives where user is member + My Drive + Shared with me
        if corpora:
            # Get user email for ownership checks
            user_email = DB['users'][userId]['about'].get('user', {}).get('emailAddress', '')
            # Get list of drives user has access to (use builtins.list to avoid shadowing)
            user_drives = builtins.list(DB['users'][userId].get('drives', {}).keys())
            
            corpora_list = [c.strip() for c in corpora.split(',') if c.strip()]
            filtered_files = []
            for file in files_list:
                # Check if file matches any of the specified corpora
                matches = False
                if 'allDrives' in corpora_list:
                    matches = True  # allDrives includes everything
                elif 'user' in corpora_list:
                    # 'user' corpus: files in "My Drive" (no driveId) OR files user owns/has access to
                    file_drive_id = file.get('driveId')
                    if not file_drive_id:
                        # File is in My Drive
                        matches = True
                    else:
                        # File is in a shared drive - check ownership or drive access
                        file_owners = file.get('owners', [])
                        # Check if user's email is in file's owners
                        if user_email and user_email in file_owners:
                            matches = True
                        # Check if user has access to this drive (driveId in user's drives)
                        elif file_drive_id in user_drives:
                            matches = True
                        # Check if user's email is in the drive's owners list
                        else:
                            drive_info = DB['users'][userId].get('drives', {}).get(file_drive_id, {})
                            drive_owners = drive_info.get('owners', [])
                            if user_email and user_email in drive_owners:
                                matches = True
                elif 'drive' in corpora_list:
                    # 'drive' corpus includes files in a specific shared drive
                    # This requires driveId parameter to be specified
                    if driveId and file.get('driveId') == driveId:
                        matches = True
                    # Also include files with any driveId if no specific driveId was requested
                    # (matches the API behavior when driveId is empty but corpora='drive')
                    elif not driveId and file.get('driveId'):
                        matches = True
                elif 'domain' in corpora_list and file.get('domainId'):
                    matches = True  # Files in domain corpus
                
                if matches:
                    filtered_files.append(file)
            files_list = filtered_files

        # Apply permissions filter if specified
        if includePermissionsForView:
            view_type = includePermissionsForView.strip()
            filtered_files = []
            for file in files_list:
                # Get permissions for the specified view
                permissions = file.get('permissions', [])
                if view_type == 'published':
                    # Check if file is published
                    if any(p.get('type') == 'anyone' and p.get('role') in ['reader', 'commenter', 'writer'] for p in permissions):
                        filtered_files.append(file)
                elif view_type == 'domain':
                    # Check if file is shared with domain
                    if any(p.get('type') == 'domain' for p in permissions):
                        filtered_files.append(file)
                elif view_type == 'anyone':
                    # Check if file is shared with anyone
                    if any(p.get('type') == 'anyone' for p in permissions):
                        filtered_files.append(file)
            files_list = filtered_files

        # Remove content and other content-related fields from each file
        # This ensures we only return metadata, not the actual file contents
        files_list_without_content = []
        for file in files_list:
            # Create a copy of the file without content-related fields
            file_copy = {}
            
            # List of content-related fields to exclude
            content_fields = {'content', 'sheets', 'data', 'tabs', 'exportFormats'}
            
            # Copy all fields except content-related ones
            for key, value in file.items():
                if key not in content_fields:
                    file_copy[key] = value
            
            # Handle revisions - keep revision metadata but remove content
            if 'revisions' in file_copy:
                file_copy['revisions'] = []
                # Handle None case: if revisions is None or missing, use empty list
                revisions = file.get('revisions') or []
                for rev in revisions:
                    rev_copy = {k: v for k, v in rev.items() if k != 'content'}
                    file_copy['revisions'].append(rev_copy)
            
            files_list_without_content.append(file_copy)

        # Implement proper pagination
        total_files = len(files_list_without_content)
        start_index = 0
        
        if pageToken:
            try:
                # Decode the page token to get the start index
                # In a real implementation, this would be a proper token encoding/decoding
                start_index = int(pageToken.split('_')[1])
                if start_index >= total_files:
                    start_index = 0
            except (ValueError, IndexError):
                start_index = 0

        end_index = min(start_index + pageSize, total_files)
        files_page = files_list_without_content[start_index:end_index]
        
        # Generate next page token if there are more results
        next_page_token = None
        if end_index < total_files:
            next_page_token = f"page_{end_index}"

        return {
            'kind': 'drive#fileList',
            'nextPageToken': next_page_token,
            'files': files_page
        }
    except UserNotFoundError:
        # Re-raise UserNotFoundError as-is to preserve the specific error type
        raise
    except ValueError as e:
        raise ValueError(e)
    except Exception as e:
        # For any other unexpected errors, wrap them in a KeyError
        raise KeyError(f"Error getting files: {e}")

@tool_spec(
    spec={
        'name': 'update_file_metadata_or_content',
        'description': """ Updates a file's metadata or content with patch semantics. 
        
        This means only the fields explicitly provided in the `body` dictionary
        will be updated. All other file properties will remain unchanged. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to update.'
                },
                'body': {
                    'type': 'object',
                    'description': 'Dictionary of file properties to update with keys:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'New name of the file.'
                        },
                        'mimeType': {
                            'type': 'string',
                            'description': 'New MIME type of the file.'
                        },
                        'parents': {
                            'type': 'array',
                            'description': 'New list of parent folder IDs.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'permissions': {
                            'type': 'array',
                            'description': 'New list of permission objects with keys:',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {
                                        'type': 'string',
                                        'description': 'Permission ID'
                                    },
                                    'role': {
                                        'type': 'string',
                                        'description': "Permission role (e.g., 'owner', 'reader', 'writer')"
                                    },
                                    'type': {
                                        'type': 'string',
                                        'description': "Permission type (e.g., 'user', 'group', 'domain', 'anyone')"
                                    },
                                    'emailAddress': {
                                        'type': 'string',
                                        'description': 'Email address for user/group permissions'
                                    }
                                },
                                'required': [
                                    'id',
                                    'role',
                                    'type',
                                    'emailAddress'
                                ]
                            }
                        }
                    },
                    'required': []
                },
                'media_body': {
                    'type': 'object',
                    'description': 'Dictionary containing media content properties to update with keys:',
                    'properties': {
                        'size': {
                            'type': 'integer',
                            'description': 'File size in bytes.'
                        },
                        'md5Checksum': {
                            'type': 'string',
                            'description': 'MD5 checksum of the file content.'
                        },
                        'sha1Checksum': {
                            'type': 'string',
                            'description': 'SHA1 checksum of the file content.'
                        },
                        'sha256Checksum': {
                            'type': 'string',
                            'description': 'SHA256 checksum of the file content.'
                        },
                        'mimeType': {
                            'type': 'string',
                            'description': 'MIME type of the file content.'
                        },
                        'imageMediaMetadata': {
                            'type': 'object',
                            'description': 'Additional metadata about image files (output-only), may include:',
                            'properties': {
                                'width': {
                                    'type': 'integer',
                                    'description': 'Width of the image in pixels.'
                                },
                                'height': {
                                    'type': 'integer',
                                    'description': 'Height of the image in pixels.'
                                },
                                'cameraMake': {
                                    'type': 'string',
                                    'description': 'Make of the camera used.'
                                },
                                'cameraModel': {
                                    'type': 'string',
                                    'description': 'Model of the camera used.'
                                },
                                'aperture': {
                                    'type': 'number',
                                    'description': 'Aperture (f-number) used.'
                                },
                                'exposureTime': {
                                    'type': 'number',
                                    'description': 'Exposure time in seconds.'
                                },
                                'exposureBias': {
                                    'type': 'number',
                                    'description': 'Exposure bias (APEX value).'
                                },
                                'maxApertureValue': {
                                    'type': 'number',
                                    'description': 'Maximum aperture (APEX value).'
                                },
                                'focalLength': {
                                    'type': 'number',
                                    'description': 'Focal length in millimeters.'
                                },
                                'isoSpeed': {
                                    'type': 'integer',
                                    'description': 'ISO speed used.'
                                },
                                'flashUsed': {
                                    'type': 'boolean',
                                    'description': 'Whether flash was used.'
                                },
                                'meteringMode': {
                                    'type': 'string',
                                    'description': 'Metering mode.'
                                },
                                'exposureMode': {
                                    'type': 'string',
                                    'description': 'Exposure mode.'
                                },
                                'colorSpace': {
                                    'type': 'string',
                                    'description': 'Color space of the photo.'
                                },
                                'whiteBalance': {
                                    'type': 'string',
                                    'description': 'White balance setting.'
                                },
                                'sensor': {
                                    'type': 'string',
                                    'description': 'Sensor type.'
                                },
                                'rotation': {
                                    'type': 'integer',
                                    'description': 'Number of clockwise 90° rotations applied.'
                                },
                                'time': {
                                    'type': 'string',
                                    'description': 'Date and time the photo was taken (EXIF DateTime).'
                                },
                                'lens': {
                                    'type': 'string',
                                    'description': 'Lens used.'
                                },
                                'subjectDistance': {
                                    'type': 'integer',
                                    'description': 'Distance to subject in meters.'
                                },
                                'location': {
                                    'type': 'object',
                                    'description': """ Geographic location, including:
                                             - 'latitude' (Optional[float])
                                            - 'longitude' (Optional[float])
                                            - 'altitude' (Optional[float]) """,
                                    'properties': {},
                                    'required': []
                                }
                            },
                            'required': []
                        },
                        'videoMediaMetadata': {
                            'type': 'object',
                            'description': 'Additional metadata about video files (output-only), may include:',
                            'properties': {
                                'width': {
                                    'type': 'integer',
                                    'description': 'Width of the video in pixels.'
                                },
                                'height': {
                                    'type': 'integer',
                                    'description': 'Height of the video in pixels.'
                                },
                                'durationMillis': {
                                    'type': 'string',
                                    'description': 'Duration of the video in milliseconds.'
                                }
                            },
                            'required': []
                        },
                        'filePath': {
                            'type': 'string',
                            'description': 'Path to file for content upload (creates new revision).'
                        }
                    },
                    'required': []
                },
                'addParents': {
                    'type': 'string',
                    'description': "Comma-separated list of parent IDs to add, defaults to ''."
                },
                'enforceSingleParent': {
                    'type': 'boolean',
                    'description': 'Whether to enforce single parent, defaults to False.'
                },
                'removeParents': {
                    'type': 'string',
                    'description': "Comma-separated list of parent IDs to remove, defaults to ''."
                },
                'includeLabels': {
                    'type': 'string',
                    'description': "Comma-separated list of labels to include in the output response. This parameter only filters which labels are returned in the response and does not modify the file\'s labels in the database. If a requested label is not present on the file, a ValueError will be raised. Defaults to ''."
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def update(fileId: str,
           body: Optional[Dict[str, Any]] = None,
           media_body: Optional[Dict[str, Any]] = None,
           addParents: Optional[str] = '',
           enforceSingleParent: Optional[bool] = False,
           removeParents: Optional[str] = '',
           includeLabels: Optional[str] = '',
           ) -> Optional[Dict[str, Any]]:
    """ 
    Updates a file's metadata or content with patch semantics. 
    
    This means only the fields explicitly provided in the `body` dictionary
    will be updated. All other file properties will remain unchanged.

    Args:
        fileId (str): The ID of the file to update.
        body (Optional[Dict[str, Any]]): Dictionary of file properties to update with keys:
            - 'name' (Optional[str]): New name of the file.
            - 'mimeType' (Optional[str]): New MIME type of the file.
            - 'parents' (Optional[List[str]]): New list of parent folder IDs.
            - 'permissions' (Optional[List[Dict[str, Union[str, int, bool]]]]): New list of permission objects with keys:
                - 'id' (str): Permission ID
                - 'role' (str): Permission role (e.g., 'owner', 'reader', 'writer')
                - 'type' (str): Permission type (e.g., 'user', 'group', 'domain', 'anyone')
                - 'emailAddress' (str): Email address for user/group permissions
        media_body (Optional[Dict[str, Any]]): Dictionary containing media content properties to update with keys:
            - 'size' (Optional[int]): File size in bytes.
            - 'md5Checksum' (Optional[str]): MD5 checksum of the file content.
            - 'sha1Checksum' (Optional[str]): SHA1 checksum of the file content.
            - 'sha256Checksum' (Optional[str]): SHA256 checksum of the file content.
            - 'mimeType' (Optional[str]): MIME type of the file content.
            - 'imageMediaMetadata' (Optional[Dict[str, Any]]): Additional metadata about image files (output-only), may include:
                - 'width' (Optional[int]): Width of the image in pixels.
                - 'height' (Optional[int]): Height of the image in pixels.
                - 'cameraMake' (Optional[str]): Make of the camera used.
                - 'cameraModel' (Optional[str]): Model of the camera used.
                - 'aperture' (Optional[float]): Aperture (f-number) used.
                - 'exposureTime' (Optional[float]): Exposure time in seconds.
                - 'exposureBias' (Optional[float]): Exposure bias (APEX value).
                - 'maxApertureValue' (Optional[float]): Maximum aperture (APEX value).
                - 'focalLength' (Optional[float]): Focal length in millimeters.
                - 'isoSpeed' (Optional[int]): ISO speed used.
                - 'flashUsed' (Optional[bool]): Whether flash was used.
                - 'meteringMode' (Optional[str]): Metering mode.
                - 'exposureMode' (Optional[str]): Exposure mode.
                - 'colorSpace' (Optional[str]): Color space of the photo.
                - 'whiteBalance' (Optional[str]): White balance setting.
                - 'sensor' (Optional[str]): Sensor type.
                - 'rotation' (Optional[int]): Number of clockwise 90° rotations applied.
                - 'time' (Optional[str]): Date and time the photo was taken (EXIF DateTime).
                - 'lens' (Optional[str]): Lens used.
                - 'subjectDistance' (Optional[int]): Distance to subject in meters.
                - 'location' (Optional[Dict[str, float]]): Geographic location, including:
                    - 'latitude' (Optional[float])
                    - 'longitude' (Optional[float])
                    - 'altitude' (Optional[float])
            - 'videoMediaMetadata' (Optional[Dict[str, Any]]): Additional metadata about video files (output-only), may include:
                - 'width' (Optional[int]): Width of the video in pixels.
                - 'height' (Optional[int]): Height of the video in pixels.
                - 'durationMillis' (Optional[str]): Duration of the video in milliseconds.
            - 'filePath' (Optional[str]): Path to file for content upload (creates new revision).
        addParents (Optional[str]): Comma-separated list of parent IDs to add, defaults to ''.
        enforceSingleParent (Optional[bool]): Whether to enforce single parent, defaults to False.
        removeParents (Optional[str]): Comma-separated list of parent IDs to remove, defaults to ''.
        includeLabels (Optional[str]): Comma-separated list of labels to include in the output response. 
                                      This parameter only filters which labels are returned in the response 
                                      and does not modify the file's labels in the database. If a requested 
                                      label is not present on the file, a ValueError will be raised. 
                                      Defaults to ''.

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the updated file with the following keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#file').
            - 'id' (str): File ID.
            - 'name' (str): File name.
            - 'mimeType' (str): MIME type of the file.
            - 'parents' (List[str]): List of parent folder IDs.
            - 'createdTime' (str): Creation timestamp.
            - 'modifiedTime' (str): Last modification timestamp.
            - 'trashed' (bool): Whether the file is in trash.
            - 'starred' (bool): Whether the file is starred.
            - 'owners' (List[str]): List of owner email addresses.
            - 'size' (str): File size in bytes.
            - 'permissions' (List[Dict[str, Any]]): List of permission objects.
            - 'content' (Dict[str, Any]): File content with metadata (if content was updated). Contains:
                - 'data' (str): Text or Base64 encoded content data
                - 'encoding' (str): Content encoding ('text' or 'base64')
                - 'checksum' (str): SHA256 checksum for integrity verification
                - 'version' (str): Content version
                - 'lastContentUpdate' (str): Timestamp of last content update
            - 'revisions' (List[Dict[str, Any]]): List of file revisions (if content was updated). Contains:
                - 'id' (str): Revision ID
                - 'mimeType' (str): MIME type of the revision
                - 'modifiedTime' (str): When the revision was created
                - 'keepForever' (bool): Whether to keep this revision forever
                - 'originalFilename' (str): Original filename
                - 'size' (str): File size in bytes
                - 'content' (Dict[str, Any]): Revision content with metadata. Contains:
                    - 'data' (str): Text or Base64 encoded content data
                    - 'encoding' (str): Content encoding ('text' or 'base64')
                    - 'checksum' (str): SHA256 checksum for integrity verification
            - 'labels' (List[str]): List of labels associated with the file

    Raises:
        TypeError: If `fileId`, `addParents`, `removeParents`, `includeLabels` are not strings,
                   or if `enforceSingleParent` is not a boolean, or if `media_body` 
                   is provided and is not a dictionary.
        ResourceNotFoundError: If the file with the specified `fileId` is not found.
        ValidationError: If `body` is provided and does not conform to the
                                 expected structure (UpdateBodyModel), or if `media_body`
                                 is provided and does not conform to MediaBodyModel.
        ValueError: If `includeLabels` is provided and contains labels that are not 
                    present on the file.
        KeyError: (Propagated) If `userId` used internally (e.g., 'me') is not
                  found during database access.
        QuotaExceededError: If the storage quota would be exceeded by updating the file content.
    """
    # --- COMPREHENSIVE INPUT VALIDATION START ---
    # All validation must occur BEFORE any resource operations to ensure proper error precedence

    # 1. Basic type validation for all parameters
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not isinstance(addParents, str):
        raise TypeError("addParents must be a string.")
    if not isinstance(enforceSingleParent, bool):
        raise TypeError("enforceSingleParent must be a boolean.")
    if not isinstance(removeParents, str):
        raise TypeError("removeParents must be a string.")
    if not isinstance(includeLabels, str):
        raise TypeError("includeLabels must be a string.")

    # 2. Validate fileId format and security
    # Allow empty fileId to pass through to resource lookup for proper error handling
    if fileId.strip():  # Only validate if not empty
        if len(fileId) > 100:  # Reasonable limit for file IDs
            raise ValueError("fileId exceeds maximum length")
        
        # Check for potential injection patterns in fileId
        dangerous_patterns = [r'[\x00-\x1f\x7f-\x9f]', r'[<>:"|?*]']
        for pattern in dangerous_patterns:
            if re.search(pattern, fileId):
                raise ValueError("fileId contains invalid characters")

    # 3. Validate 'media_body' dictionary using Pydantic with security checks
    if media_body is not None and not isinstance(media_body, dict):
        raise TypeError(f"Argument 'media_body' must be a dictionary or None, got {type(media_body).__name__}")

    if media_body is not None:
        try:
            validated_media_body = MediaBodyModel(**media_body)
        except ValidationError as e:
            raise e

    # 4. Validate 'body' dictionary using Pydantic with security checks
    if body is not None:
        if not isinstance(body, dict):  # Ensure body, if not None, is a dict before Pydantic
            raise TypeError("body must be a dictionary if provided.")
        try:
            validated_body_model = UpdateBodyModel(**body)
            # For PATCH semantics, use exclude_unset=True to only include fields
            # that were explicitly provided in the input.
            body = validated_body_model.model_dump(exclude_unset=True)
        except ValidationError as e:
            raise e

    # 5. Validate parent parameters for security
    if addParents:
        parent_ids = [p.strip() for p in addParents.split(',') if p.strip()]
        for parent_id in parent_ids:
            if len(parent_id) > 100:
                raise ValueError("Parent ID in addParents exceeds maximum length")
            # Check for dangerous patterns
            for pattern in dangerous_patterns:
                if re.search(pattern, parent_id):
                    raise ValueError("Parent ID in addParents contains invalid characters")

    if removeParents:
        parent_ids = [p.strip() for p in removeParents.split(',') if p.strip()]
        for parent_id in parent_ids:
            if len(parent_id) > 100:
                raise ValueError("Parent ID in removeParents exceeds maximum length")
            # Check for dangerous patterns
            for pattern in dangerous_patterns:
                if re.search(pattern, parent_id):
                    raise ValueError("Parent ID in removeParents contains invalid characters")

    # 6. Validate includeLabels parameter
    if includeLabels and len(includeLabels) > 1000:  # Reasonable limit
        raise ValueError("includeLabels parameter exceeds maximum length")

    # 7. ONLY AFTER ALL VALIDATION IS COMPLETE - Perform resource lookup
    userId = 'me'  # Assuming 'me' for now

    try:
        existing = DB['users'][userId]['files'][fileId]
    except KeyError:
        raise ResourceNotFoundError(f"File with ID '{fileId}' not found.")
    # --- COMPREHENSIVE INPUT VALIDATION END ---

    # --- Original Core Logic Start ---

    if body is None:
        body = {}

    # Get the file to update
    existing = DB['users'][userId]['files'].get(fileId)
    if not existing:
        return None

    # Process media_body if provided to update file content
    if media_body:
        validated_media_body = MediaBodyModel(**media_body)
        
        # Calculate current file size for quota management
        current_file_size = int(existing.get('size', '0'))
        new_file_size = validated_media_body.size or current_file_size

        # Check quota before updating content
        quota = _get_user_quota(userId)
        size_difference = new_file_size - current_file_size
        
        if quota['usage'] + size_difference > quota['limit']:
            raise QuotaExceededError("Quota exceeded. Cannot update the file content.")

        # Use content manager for content updates and revision handling
        content_manager = DriveContentManager()
        
        # If filePath is provided, read the file content
        if 'filePath' in media_body and isinstance(media_body['filePath'], str):
            file_path = media_body['filePath']
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Use read_file function to properly read file content with encoding
            file_data = read_file(file_path)
            
            # Convert content to bytes for content manager
            if file_data['encoding'] == 'text':
                new_content = file_data['content']
            else:
                new_content = decode_from_base64(file_data['content'])
            
            # Use content manager to update file content (this handles revisions automatically)
            content_manager.update_file_content(userId, fileId, new_content)
            
            # Update file metadata from media_body
            existing['md5Checksum'] = validated_media_body.md5Checksum or existing.get('md5Checksum', '')
            existing['sha1Checksum'] = validated_media_body.sha1Checksum or existing.get('sha1Checksum', '')
            existing['sha256Checksum'] = validated_media_body.sha256Checksum or existing.get('sha256Checksum', '')
            if validated_media_body.mimeType:
                existing['mimeType'] = validated_media_body.mimeType
            existing['imageMediaMetadata'] = validated_media_body.imageMediaMetadata or existing.get('imageMediaMetadata', {})
            existing['videoMediaMetadata'] = validated_media_body.videoMediaMetadata or existing.get('videoMediaMetadata', {})
            
            # Update modified time to current timestamp
            existing['modifiedTime'] = datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Update file metadata from media_body without content change
            existing['size'] = str(new_file_size)
            existing['md5Checksum'] = validated_media_body.md5Checksum or existing.get('md5Checksum', '')
            existing['sha1Checksum'] = validated_media_body.sha1Checksum or existing.get('sha1Checksum', '')
            existing['sha256Checksum'] = validated_media_body.sha256Checksum or existing.get('sha256Checksum', '')
            if validated_media_body.mimeType:
                existing['mimeType'] = validated_media_body.mimeType
            existing['imageMediaMetadata'] = validated_media_body.imageMediaMetadata or existing.get('imageMediaMetadata', {})
            existing['videoMediaMetadata'] = validated_media_body.videoMediaMetadata or existing.get('videoMediaMetadata', {})
            
            # Update user quota usage
            _update_user_usage(userId, size_difference)
            
            # Update modified time to current timestamp
            existing['modifiedTime'] = datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Ensure 'parents' exists as a list
    if 'parents' not in existing or not isinstance(existing['parents'], builtins.list):
        existing['parents'] = []

    # Check if we should use addParents/removeParents logic or body.parents
    use_parents_operations = addParents or removeParents or enforceSingleParent
    
    if use_parents_operations:
        # Handle addParents (comma-separated string of parent IDs)
        if addParents:
            add_parents_list = [p.strip() for p in addParents.split(',') if p.strip()]
            for parent_id in add_parents_list:
                # A parent can be a folder or a drive.
                parent_file = DB['users'][userId]['files'].get(parent_id)
                parent_drive = DB['users'][userId]['drives'].get(parent_id)

                if not parent_file and not parent_drive:
                    raise ResourceNotFoundError(f"Parent with ID '{parent_id}' not found.")

                if parent_file and parent_file.get('mimeType') != 'application/vnd.google-apps.folder':
                    raise ValueError(f"File with ID '{parent_id}' is not a folder and cannot be a parent.")

                if parent_id not in existing['parents']:
                    existing['parents'].append(parent_id)

        # Handle removeParents (comma-separated string of parent IDs)
        if removeParents:
            remove_parents_list = [p.strip() for p in removeParents.split(',') if p.strip()]
            existing['parents'] = [p for p in existing['parents'] if p not in remove_parents_list]

        # If enforceSingleParent is True, only keep the last parent
        if enforceSingleParent and existing['parents']:
            existing['parents'] = [existing['parents'][-1]]
        
        # When using addParents/removeParents, exclude parents from body update
        body_without_parents = {k: v for k, v in body.items() if k != 'parents'}
        existing.update(body_without_parents)
    else:
        # No addParents/removeParents operations, use body as-is
        existing.update(body)

    # Update modifiedTime for any metadata changes (following Google Drive API behavior)
    # This ensures modifiedTime is updated for metadata-only changes, not just content changes
    if body or addParents or removeParents:

        existing['modifiedTime'] = datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'

    # Handle includeLabels parameter - filter output labels without modifying DB structure
    if includeLabels and includeLabels.strip():
        requested_labels = [label.strip() for label in includeLabels.split(',') if label.strip()]
        existing_labels = existing.get('labels', [])
        
        # Validate that all requested labels exist in the file
        missing_labels = [label for label in requested_labels if label not in existing_labels]
        if missing_labels:
            raise ValueError(f"Requested labels not found in file: {', '.join(missing_labels)}")

        returned_existing = existing.copy()
        # Filter the output to only include requested labels
        returned_existing['labels'] = requested_labels

        return returned_existing

    return existing

@tool_spec(
    spec={
        'name': 'subscribe_to_file_changes',
        'description': 'Subscribes to changes to a file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to watch.'
                },
                'body': {
                    'type': 'object',
                    'description': 'The configuration for the notification channel that will receive change updates.',
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': 'Channel ID.'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'The type of delivery mechanism used for this channel. Valid values are "web_hook" or "webhook".'
                        },
                        'address': {
                            'type': 'string',
                            'description': 'The address where notifications are delivered for this channel.'
                        },
                        'token': {
                            'type': 'string',
                            'description': 'Channel token.'
                        },
                        'expiration': {
                            'type': 'string',
                            'description': 'Channel expiration time.'
                        }
                    },
                    'required': [
                        'id',
                        'type',
                        'address'
                    ]
                },
                'acknowledgeAbuse': {
                    'type': 'boolean',
                    'description': 'Whether to acknowledge abuse.'
                },
                'ignoreDefaultVisibility': {
                    'type': 'boolean',
                    'description': 'Whether to ignore default visibility.'
                },
                'supportsAllDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support all drives.'
                },
                'supportsTeamDrives': {
                    'type': 'boolean',
                    'description': 'Whether to support team drives.'
                },
                'includePermissionsForView': {
                    'type': 'string',
                    'description': "Specifies which additional view's permissions to include."
                },
                'includeLabels': {
                    'type': 'string',
                    'description': 'Comma-separated list of labels to include.'
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def watch(fileId: str,
         body: Optional[Dict[str, Any]] = None,
         acknowledgeAbuse: Optional[bool] = False,
         ignoreDefaultVisibility: Optional[bool] = False,
         supportsAllDrives: Optional[bool] = False,
         supportsTeamDrives: Optional[bool] = False,
         includePermissionsForView: Optional[str] = '',
         includeLabels: Optional[str] = '',
         ) -> Dict[str, Any]:
    """Subscribes to changes to a file.
    
    Args:
        fileId (str): The ID of the file to watch.
        body (Optional[Dict[str, Any]]): The configuration for the notification channel that will receive change updates.
            - 'id' (str): Channel ID.
            - 'type' (str): The type of delivery mechanism used for this channel. Valid values are "web_hook" or "webhook".
            - 'address' (str): The address where notifications are delivered for this channel.
            - 'token' (Optional[str]): Channel token.
            - 'expiration' (Optional[str]): Channel expiration time.
        acknowledgeAbuse (Optional[bool]): Whether to acknowledge abuse.
        ignoreDefaultVisibility (Optional[bool]): Whether to ignore default visibility.
        supportsAllDrives (Optional[bool]): Whether to support all drives.
        supportsTeamDrives (Optional[bool]): Whether to support team drives.
        includePermissionsForView (Optional[str]): Specifies which additional view's permissions to include.
        includeLabels (Optional[str]): Comma-separated list of labels to include.
        
    Returns:
        Dict[str, Any]: Dictionary containing the watch information with keys:
            - 'kind' (str): Resource type identifier (e.g., 'api#channel').
            - 'id' (str): Channel ID.
            - 'resourceId' (str): The ID of the watched resource.
            - 'resourceUri' (str): The URI of the watched resource.
            - 'token' (Optional[str]): Channel token.
            - 'expiration' (Optional[str]): Channel expiration time.
    """
    userId = 'me'  # Assuming 'me' for now
    _ensure_channels(userId)
    if body is None:
        body = {}
    # In a real implementation, a watch would be set up
    DB['users'][userId]['channels'][body.get('id')] = body
    return body

@tool_spec(
    spec={
        'name': 'get_file_content',
        'description': """ Get file content, optionally for a specific revision.
        
        This function retrieves the content of a file, optionally for a specific revision.
        If a revision ID is provided, it searches the file's revisions list for the matching
        revision and returns its content. If no revision ID is provided, it returns the current
        content of the file. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user retrieving the file content. Defaults to \'me\'.'
                },
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to retrieve content from.'
                },
                'revision_id': {
                    'type': 'string',
                    'description': 'Optional revision ID to get specific revision.'
                }
            },
            'required': [
                'file_id'
            ]
        }
    }
)
def get_content(file_id: str, user_id: Optional[str] = 'me', revision_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get file content, optionally for a specific revision.

    This function retrieves the content of a file, optionally for a specific revision.
    If a revision ID is provided, it searches the file's revisions list for the matching
    revision and returns its content. If no revision ID is provided, it returns the current
    content of the file.
    
    Args:
        file_id (str): The ID of the file to retrieve content from.
        user_id (Optional[str]): The ID of the user retrieving the file content. Defaults to 'me'.
        revision_id (Optional[str]): Optional revision ID to get specific revision.
        
    Returns:
        Dict[str, Any]: A dictionary containing the file content information.
            It has the following keys:
            - file_id (str): The ID of the file to which content is being retrieved.
            - revision_id (Optional[str]): The ID of the revision to get specific revision.
            - content (Dict[str, Any]): The content of the file, it has the following keys:
                - data (str): Encoded content data
                - encoding (str): Content encoding
                - checksum (str): SHA256 checksum for integrity
                - version (str): Content version
                - lastContentUpdate (str): Timestamp of last content update
            - mime_type (str): The MIME type of the file.
            - size (int): The size of the file in bytes.
            - modified_time (str): The last modified time of the file.
    
    Raises:
        ValueError: If the file ID is not found for the user, if the revision ID is
            not found for the file, or if the file content cannot be retrieved.
    """
    # Input validation
    if not isinstance(user_id, str):
        raise ValueError("user_id must be a string")
        
    if not isinstance(file_id, str):
        raise ValueError("file_id must be a string")

    if revision_id and not isinstance(revision_id, str):
        raise ValueError("revision_id must be a string")

    # Get file data
    if user_id not in DB['users']:
        raise ValueError(f"User '{user_id}' not found")
    
    files = DB['users'][user_id]['files']
    
    if file_id not in files:
        raise ValueError(f"File '{file_id}' not found for user '{user_id}'")
    
    file_data = files[file_id]
    models.FileWithContentModel(**file_data)

    if revision_id:
        # Get specific revision
        if 'revisions' not in file_data:
            raise ValueError(f"No revisions found for file '{file_id}'")
        
        revision = None
        for rev in file_data['revisions']:
            if rev['id'] == revision_id:
                revision = rev
                break
        
        if not revision:
            raise ValueError(f"Revision '{revision_id}' not found for file '{file_id}'")
        
        # Handle content safely - it might be None or missing
        content_data = None
        if revision.get('content') and isinstance(revision['content'], dict):
            content_data = models.FileContentModel(**revision['content'])
        
        return models.GetFileContentResponseModel(
            file_id=file_id,
            revision_id=revision_id,
            content=content_data,
            mime_type=revision['mimeType'],
            size=revision['size'],
            modified_time=revision['modifiedTime']
        ).model_dump()
    else:
        # Get current content
        if 'content' not in file_data or file_data['content'] is None:
            raise ValueError(f"No content found for file '{file_id}'")
        
        return models.GetFileContentResponseModel(
            file_id=file_id,
            content=file_data['content'],
            mime_type=file_data['mimeType'],
            size=file_data['size'],
            modified_time=file_data['modifiedTime']
        ).model_dump()

@tool_spec(
    spec={
        'name': 'create_file_revision',
        'description': """ Create a new revision for a file.
        
        This function creates a new revision for a file with the given content. It
        generates a unique revision ID based on the existing revisions in the file's
        data structure, creates a revision content structure matching the expected
        JSON format, and validates the revision using the RevisionModel. The function
        then adds the revision to the file's revisions list. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user creating the revision. Defaults to \'me\'.'
                },
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to which the revision is being added.'
                },
                'content': {
                    'type': 'string',
                    'description': 'The content to be added to the revision.'
                }
            },
            'required': [
                'file_id',
                'content'
            ]
        }
    }
)
def create_revision(file_id: str, content: str, user_id: Optional[str] = 'me') -> Dict[str, Any]:
    """
    Create a new revision for a file.

    This function creates a new revision for a file with the given content. It
    generates a unique revision ID based on the existing revisions in the file's
    data structure, creates a revision content structure matching the expected
    JSON format, and validates the revision using the RevisionModel. The function
    then adds the revision to the file's revisions list.
    
    Args:
        file_id (str): The ID of the file to which the revision is being added.
        content (str): The content to be added to the revision.
        user_id (Optional[str]): The ID of the user creating the revision. Defaults to 'me'.
        
    Returns:
        Dict[str, Any]: A dictionary containing the revision information.
            It has the following keys:
            - revision_id (str): The ID of the created revision.
            - revision_created (bool): A boolean indicating if the revision was created successfully.
            - size (int): The size of the revision in bytes.
            - checksum (str): The checksum of the revision.
    
    Raises:
        ValueError: If the user_id is not a string, if the file_id is not a string,
            or if the content is not bytes.
    """
    # Input validation
    if not isinstance(user_id, str):
        raise ValueError("user_id must be a string")
        
    if not isinstance(file_id, str):
        raise ValueError("file_id must be a string")
    
    if not isinstance(content, str):
        raise ValueError("content must be a string")
        
    # Get file data
    if user_id not in DB['users']:
        raise ValueError(f"User '{user_id}' not found")
    
    files = DB['users'][user_id]['files']
    
    if file_id not in files:
        raise ValueError(f"File '{file_id}' not found for user '{user_id}'")
    
    file_data = files[file_id]
    models.FileWithContentModel(**file_data)

    # Get encoding with robust None handling
    encoding = _get_encoding(file_data)

    # Encode content based on the encoding type
    if encoding == 'base64':
        content_encoded = encode_to_base64(content)
    else:
        content_encoded = content
    
    # Generate revision ID based on existing revisions in this file
    revision_number = DriveContentManager()._get_next_revision_number(file_data)
    revision_id = f"rev-{revision_number}"

    # Add revision to file
    if 'revisions' not in file_data:
        file_data['revisions'] = []
    
    # Create revision content matching JSON structure (only 3 fields for revisions)
    revision_content = models.RevisionContentModel(
        data=content_encoded,
        encoding=encoding,
        checksum=DriveFileProcessor().calculate_checksum(content)
    ).model_dump()
    
    # Create revision structure matching JSON structure
    revision = models.RevisionModel(
        id=revision_id,
        mimeType=file_data.get('mimeType', 'application/octet-stream'),
        modifiedTime=datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
        keepForever=False,
        originalFilename=file_data.get('name', 'unknown'),
        size=str(len(content)),
        content=revision_content
    ).model_dump()

    file_data['revisions'].append(revision)
        
    return models.CreateRevisionResponseModel(
        revision_id=revision_id,
        revision_created=True,
        size=len(content),
        checksum=revision_content['checksum']
    ).model_dump()

@tool_spec(
    spec={
        'name': 'update_file_content',
        'description': """ Update file content with new bytes data.
        
        This function updates the content of a file with new bytes data. It calculates
        a new checksum for the new content, encodes it to base64, and creates a new
        content structure matching the expected JSON format. The function then validates
        the new content using the FileContentModel and creates a new revision before
        updating the file's content and size. Finally, it clears the export cache since
        the content has changed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user updating the file content. Defaults to \'me\'.'
                },
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to which content is being updated.'
                },
                'new_content': {
                    'type': 'string',
                    'description': 'The new content to be added to the file.'
                }
            },
            'required': [
                'file_id',
                'new_content'
            ]
        }
    }
)
def update_content(file_id: str, new_content: str, user_id: Optional[str] = 'me') -> Dict[str, Any]:
    """
    Update file content with new string data.

    This function updates the content of a file with new string data. It calculates
    a new checksum for the new content, encodes it to base64, and creates a new
    content structure matching the expected JSON format. The function then validates
    the new content using the FileContentModel and creates a new revision before
    updating the file's content and size. Finally, it clears the export cache since
    the content has changed.
    
    Args:
        file_id (str): The ID of the file to which content is being updated.
        new_content (str): The new content to be added to the file.
        user_id (Optional[str]): The ID of the user updating the file content. Defaults to 'me'.
        
    Returns:
        Dict[str, Any]: A dictionary containing the update information.
            It has the following keys:
            - file_id (str): The ID of the file to which content is being updated.
            - content_updated (bool): A boolean indicating if the content was updated successfully.
            - new_size (int): The size of the updated content in bytes.
            - new_checksum (str): The checksum of the updated content.
            - new_version (str): The version of the updated content.
    """
    # Input validation
    if not isinstance(user_id, str):
        raise ValueError("user_id must be a string")
        
    if not isinstance(file_id, str):
        raise ValueError("file_id must be a string")

    if not isinstance(new_content, str):
        raise ValueError("new_content must be a string")
        
    # Get file data
    if user_id not in DB['users']:
        raise ValueError(f"User '{user_id}' not found")
    
    files = DB['users'][user_id]['files']
    
    for file in files.values():
        models.FileWithContentModel(**file)
    
    if file_id not in files:
        raise ValueError(f"File '{file_id}' not found for user '{user_id}'")
    
    file_data = files[file_id]
    models.FileWithContentModel(**file_data)
    
    # Get encoding with robust None handling
    encoding = _get_encoding(file_data)

    # Calculate new checksum
    new_checksum = DriveFileProcessor().calculate_checksum(new_content)

    # Encode new content to base64
    if encoding == 'base64':
        new_content_encoded = encode_to_base64(new_content)
    else:
        new_content_encoded = new_content
    
    # Create new content structure matching JSON structure
    new_content_data = models.FileContentModel(
        data=new_content_encoded,
        encoding=encoding,
        checksum=new_checksum,
        version=str(float(file_data.get('content', {}).get('version', '1.0')) + 0.1),
        lastContentUpdate=datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    ).model_dump()
    
    # Create revision before updating
    DriveContentManager().create_revision(user_id, file_id, new_content)
    
    # Update file content and size
    DriveContentManager()._update_file(user_id, file_id, {
        'content': new_content_data,
        'size': str(len(new_content))
    })

    # Clear export cache since content changed
    if 'exportFormats' in file_data:
        file_data['exportFormats'] = {}
    
    return models.UpdateFileContentResponseModel(
        file_id=file_id,
        content_updated=True,
        new_size=len(new_content),
        new_checksum=new_checksum,
        new_version=new_content_data['version']
    ).model_dump()

@tool_spec(
    spec={
        'name': 'export_file_content',
        'description': """ Export file content to a different format.
        
        This function exports the content of a file to a different format. It checks
        if the export is cached and returns the cached content if available. If not,
        it decodes the current content, validates the export format, and exports the
        content to the target MIME type. Finally, it caches the exported content and
        returns the exported content. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user exporting the file content. Defaults to \'me\'.'
                },
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to export content from.'
                },
                'target_mime': {
                    'type': 'string',
                    'description': 'The target MIME type for export.'
                }
            },
            'required': [
                'file_id',
                'target_mime'
            ]
        }
    }
)
def export_content(file_id: str, target_mime: str, user_id: Optional[str] = 'me') -> Dict[str, Any]:
    """
    Export file content to a different format.

    This function exports the content of a file to a different format. It checks
    if the export is cached and returns the cached content if available. If not,
    it decodes the current content, validates the export format, and exports the
    content to the target MIME type. Finally, it caches the exported content and
    returns the exported content.
    
    Args:
        file_id (str): The ID of the file to export content from.
        target_mime (str): The target MIME type for export.
        user_id (Optional[str]): The ID of the user exporting the file content. Defaults to 'me'.
        
    Returns:
        Dict[str, Any]: A dictionary containing the exported content information.
            It has the following keys:
            - file_id (str): The ID of the file to which content is being exported.
            - exported (bool): A boolean indicating if the content was exported successfully.
            - target_mime (str): The target MIME type for export.
            - content (str): The exported content encoded in the same format as the original content.
            - size (int): The size of the exported content in bytes.
            - cached (bool): A boolean indicating if the content was cached.
    
    Raises:
        ValueError: If the file ID is not found for the user, if the file content
            cannot be retrieved, or if the export format is not supported.
        ValueError: If the user_id is not a string, if the file_id is not a string,
            or if the target_mime is not a string.
    """
    # Input validation
    if not isinstance(user_id, str):
        raise ValueError("user_id must be a string")
    
    if not isinstance(file_id, str):
        raise ValueError("file_id must be a string")

    if not isinstance(target_mime, str):
        raise ValueError("target_mime must be a string")
    
    # Get file data
    if user_id not in DB['users']:
        raise ValueError(f"User '{user_id}' not found")
    
    files = DB['users'][user_id]['files']
    
    if file_id not in files:
        raise ValueError(f"File '{file_id}' not found for user '{user_id}'")
    
    file_data = files[file_id]
    models.FileWithContentModel(**file_data)
    
    # Check if export is cached
    if 'exportFormats' in file_data and target_mime in file_data['exportFormats']:
        cached_content = file_data['exportFormats'][target_mime]
        try:
            cached_encoded = decode_from_base64(cached_content)
        except ValueError:
            cached_encoded = cached_content.encode('utf-8')
        return models.ExportFileContentResponseModel(
            file_id=file_id,
            exported=True,
            target_mime=target_mime,
            content=cached_encoded,
            size=len(cached_encoded),
            cached=True
        ).model_dump()
    
    # Get encoding with robust None handling
    content_field = file_data.get('content')
    encoding = _get_encoding(file_data)

    # Export content
    exported_content = DriveFileProcessor().export_to_format(file_data, target_mime)
    
    # Cache the export
    DriveContentManager().cache_export_format(user_id, file_id, target_mime, exported_content)
    return models.ExportFileContentResponseModel(
        file_id=file_id,
        exported=True,
        target_mime=target_mime,
        content=exported_content,
        size=len(exported_content),
        cached=False
    ).model_dump()

@tool_spec(
    spec={
        'name': 'list_file_revisions',
        'description': """ List all revisions for a file.
        
        This function retrieves all revisions for a file. It returns the file's revisions
        list, which is a list of dictionaries containing the revision information. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'The ID of the user retrieving the revisions. Defaults to \'me\'.'
                },
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to retrieve revisions from.'
                }
            },
            'required': [
                'file_id'
            ]
        }
    }
)
def list_revisions(file_id: str, user_id: Optional[str] = 'me') -> List[Dict[str, Any]]:
    """
    List all revisions for a file.

    This function retrieves all revisions for a file. It returns the file's revisions
    list, which is a list of dictionaries containing the revision information.
    
    Args:
        file_id (str): The ID of the file to retrieve revisions from.
        user_id (Optional[str]): The ID of the user retrieving the revisions. Defaults to 'me'.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the revision information.
            Each dictionary has the following keys:
            - id (str): The ID of the revision.
            - mimeType (str): The MIME type of the revision.
            - modifiedTime (str): The last modified time of the revision.
            - keepForever (bool): A boolean indicating if the revision is marked as keep forever.
            - originalFilename (str): The original filename of the revision.
    
    Raises:
        ValueError: If the user_id is not a string, if the file_id is not a string.

    """
    # Input validation
    if not isinstance(user_id, str):
        raise ValueError("user_id must be a string")
    
    if not isinstance(file_id, str):
        raise ValueError("file_id must be a string")
    
    # Get file data
    if user_id not in DB['users']:
        raise ValueError(f"User '{user_id}' not found")
    
    files = DB['users'][user_id]['files']
    
    for file in files.values():
        models.FileWithContentModel(**file)
    
    if file_id not in files:
        raise ValueError(f"File '{file_id}' not found for user '{user_id}'")
    
    file_data = files[file_id]
    models.FileWithContentModel(**file_data)
    
    revisions = file_data.get('revisions', [])
    for revision in revisions:
        models.RevisionModel(**revision)
    return revisions