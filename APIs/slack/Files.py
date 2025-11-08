"""
Files resource for Slack API simulation.

This module provides functionality for managing files in Slack.
It simulates the files-related endpoints of the Slack API.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List
import time
import threading

from .SimulationEngine.db import DB
from .SimulationEngine.utils import _generate_slack_file_id, _check_and_delete_pending_file, _resolve_channel
from .SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    InvalidCursorFormatError,
    UserNotFoundError,
    CursorOutOfBoundsError,
    FileSizeLimitExceededError,
    InvalidChannelIdError,
    MissingContentOrFilePathError,
    FileReadError
)
from .SimulationEngine.models import FinishExternalUploadRequest
from .SimulationEngine.file_utils import (
    read_file, is_binary_file, get_mime_type,
    text_to_base64
)
import os



@tool_spec(
    spec={
        'name': 'get_file_info',
        'description': 'Get information about a file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to get info for. Must be a non-empty string.'
                },
                'cursor': {
                    'type': 'string',
                    'description': 'Pagination cursor for comments. Must be a string representing a non-negative integer. Defaults to None.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of comments to return. Must be a positive integer. Defaults to 100.'
                }
            },
            'required': [
                'file_id'
            ]
        }
    }
)
def get_file_info(
    file_id: str,
    cursor: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get information about a file.

    Args:
        file_id (str): The ID of the file to get info for. Must be a non-empty string.
        cursor (Optional[str]): Pagination cursor for comments. Must be a string representing a non-negative integer. Defaults to None.
        limit (int): Maximum number of comments to return. Must be a positive integer. Defaults to 100.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Always True (exceptions are raised on errors)
            - file (dict): File information containing:
                - id (str): File ID
                - name (str): File name
                - title (str): File title
                - filetype (str): File type/extension
                - mimetype (str): MIME type of the file
                - size (int): File size in bytes
                - channels (list): List of channel IDs where file is shared
                - comments (list): Paginated list of comments on the file
            - response_metadata (dict): Pagination metadata containing:
                - next_cursor (str): Cursor for next page of comments, or None if no more pages

    Raises:
        TypeError: If file_id is not a string, cursor is not a string or None, or limit is not an integer.
        ValueError: If file_id is empty, or limit is not positive.
        FileNotFoundError: If the specified file_id does not exist.
        InvalidCursorFormatError: If cursor cannot be parsed as a non-negative integer.
        CursorOutOfBoundsError: If cursor exceeds the length of available comments.
    """

    if not isinstance(file_id, str):
        raise TypeError("file_id must be a string.")
    
    if not file_id or not file_id.strip():
        raise ValueError("file_id is required.")
    
    if cursor is not None and not isinstance(cursor, str):
        raise TypeError("cursor must be a string or None.")
    
    if type(limit) is not int:
        raise TypeError("limit must be an integer.")
    
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")
    
    if file_id not in DB.get("files", {}):
        raise FileNotFoundError(f"File '{file_id}' not found.")

    file_data = DB["files"][file_id]

    # Simulate pagination for comments
    comments = file_data.get("comments", [])
    start_index = 0
    if cursor:
        try:
            start_index = int(cursor)
        except ValueError:
            raise InvalidCursorFormatError("Invalid cursor format. Must be a string representing an integer.")
        
        if start_index < 0:
            raise InvalidCursorFormatError("Cursor must represent a non-negative integer.")
        
        if start_index >= len(comments):
            raise CursorOutOfBoundsError(f"Cursor {cursor} exceeds available data length ({len(comments)})")

    end_index = min(start_index + limit, len(comments))
    paginated_comments = comments[start_index:end_index]

    next_cursor = str(end_index) if end_index < len(comments) else None

    # Construct the 'channels' list based on channel IDs
    channel_ids = []
    if "channels" in DB:
        for channel_id, channel_data in DB["channels"].items():
            channel_files = channel_data.get("files", {})
            if file_id in channel_files:
                channel_ids.append(channel_id)

    response = {
        "ok": True,
        "file": {
            "id": file_data.get("id", file_id),  # Fallback to provided file_id if missing
            "name": file_data.get("filename"),
            "title": file_data.get("title"),
            "filetype": file_data.get("filetype"),
            "mimetype": file_data.get("mimetype"),
            "size": file_data.get("size"),
            "channels": channel_ids,  # List of channel IDs where the file is shared
            "comments": paginated_comments,
        },
        "response_metadata": {"next_cursor": next_cursor},
    }
    return response


@tool_spec(
    spec={
        'name': 'share_file',
        'description': """ Shares an existing file into specified channels.
        
        This function allows sharing a file that already exists in the Slack workspace
        to one or more channels. The file must exist in the files database and all
        specified channels must be valid. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to share. Must be a non-empty string.'
                },
                'channel_ids': {
                    'type': 'string',
                    'description': """ Comma-separated list of channel IDs to share the file with.
                    Must be a non-empty string with valid channel IDs. """
                }
            },
            'required': [
                'file_id',
                'channel_ids'
            ]
        }
    }
)
def share_file(
    file_id: str,
    channel_ids: str
) -> Dict[str, Any]:
    """
    Shares an existing file into specified channels.

    This function allows sharing a file that already exists in the Slack workspace
    to one or more channels. The file must exist in the files database and all
    specified channels must be valid.

    Args:
        file_id (str): The ID of the file to share. Must be a non-empty string.
        channel_ids (str): Comma-separated list of channel IDs to share the file with.
            Must be a non-empty string with valid channel IDs.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - file_id (str): ID of the shared file
            - shared_to_channels (list): List of channel IDs where file was shared
            - file (dict): Updated file information with channel associations

    Raises:
        TypeError: If file_id or channel_ids is not a string.
        ValueError: If file_id or channel_ids is empty or contains only whitespace.
        FileNotFoundError: If the specified file_id does not exist.
        InvalidChannelIdError: If any of the specified channel IDs is invalid.
    """
    # Input validation
    if not isinstance(file_id, str):
        raise TypeError("file_id must be a string.")
    
    if not isinstance(channel_ids, str):
        raise TypeError("channel_ids must be a string.")
    
    if not file_id or not file_id.strip():
        raise ValueError("file_id is required and cannot be empty.")
    
    if not channel_ids or not channel_ids.strip():
        raise ValueError("channel_ids is required and cannot be empty.")

    # Check if file exists
    if file_id not in DB.get("files", {}):
        raise FileNotFoundError(f"File '{file_id}' not found.")

    # Parse and validate channel IDs
    channel_id_list = [ch.strip() for ch in channel_ids.split(",") if ch.strip()]
    if not channel_id_list:
        raise ValueError("channel_ids must contain at least one valid channel ID.")

    for channel_id in channel_id_list:
        if channel_id not in DB.get("channels", {}):
            raise InvalidChannelIdError(f"Invalid channel ID: '{channel_id}'")

    # Add file to each channel's files
    for channel_id in channel_id_list:
        if "files" not in DB["channels"][channel_id]:
            DB["channels"][channel_id]["files"] = {}
        DB["channels"][channel_id]["files"][file_id] = True

    # Get updated file information
    file_data = DB["files"][file_id].copy()
    
    # Update channels list in file data (combine existing with new)
    existing_channels = file_data.get("channels", [])
    if isinstance(existing_channels, str):
        existing_channels = existing_channels.split(",") if existing_channels else []
    
    # Merge channel lists and remove duplicates
    all_channels = list(set(existing_channels + channel_id_list))
    file_data["channels"] = all_channels

    # Update the file record in database
    DB["files"][file_id]["channels"] = all_channels

    return {
        "ok": True,
        "file_id": file_id,
        "shared_to_channels": channel_id_list,
        "file": file_data
    }


@tool_spec(
    spec={
        'name': 'add_remote_file',
        'description': """ Add a remote file to the Slack workspace.
        
        This function registers an external file in Slack's database, allowing it to be referenced
        and shared within the Slack workspace. The file itself remains hosted externally. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ A unique identifier for the file in the external system.
                    Must be a non-empty string. """
                },
                'external_url': {
                    'type': 'string',
                    'description': """ The URL where the file can be accessed.
                    Must be a non-empty string. """
                },
                'title': {
                    'type': 'string',
                    'description': """ The display title for the file in Slack.
                    Must be a non-empty string. """
                },
                'filetype': {
                    'type': 'string',
                    'description': """ The type/extension of the file (e.g., "pdf", "docx").
                    Must be a non-empty string if provided. Defaults to None. """
                },
                'indexable_file_contents': {
                    'type': 'string',
                    'description': """ Text content that can be indexed for search.
                    Must be a non-empty string if provided. Defaults to None. """
                }
            },
            'required': [
                'external_id',
                'external_url',
                'title'
            ]
        }
    }
)
def add_remote_file(
    external_id: str,
    external_url: str,
    title: str,
    filetype: Optional[str] = None,
    indexable_file_contents: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a remote file to the Slack workspace.
    
    This function registers an external file in Slack's database, allowing it to be referenced
    and shared within the Slack workspace. The file itself remains hosted externally.

    Args:
        external_id (str): A unique identifier for the file in the external system.
            Must be a non-empty string.
        external_url (str): The URL where the file can be accessed.
            Must be a non-empty string.
        title (str): The display title for the file in Slack.
            Must be a non-empty string.
        filetype (Optional[str]): The type/extension of the file (e.g., "pdf", "docx").
            Must be a non-empty string if provided. Defaults to None.
        indexable_file_contents (Optional[str]): Text content that can be indexed for search.
            Must be a non-empty string if provided. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'ok' (bool): Always True (exceptions are raised on errors).
            - 'file' (Dict[str, Any]): File information with keys:
                - 'id' (str): Unique Slack file ID.
                - 'external_id' (str): The provided external ID.
                - 'external_url' (str): The provided external URL.
                - 'title' (str): The provided title.
                - 'filetype' (Optional[str]): The provided filetype if any.
                - 'indexable_file_contents' (Optional[str]): The provided indexable content if any.
                - 'comments' (List[Dict[str, Any]]): Empty list of comments (initially).

    Raises:
        TypeError: If external_id, external_url, or title is not a string, or if 
            filetype or indexable_file_contents is not a string or None.
        ValueError: If required parameters (external_id, external_url, or title) are 
            empty strings, or if optional string parameters are provided as empty strings.
    """

    # Type validation for required parameters
    if not isinstance(external_id, str):
        raise TypeError("external_id must be a string")
    if not isinstance(external_url, str):
        raise TypeError("external_url must be a string")
    if not isinstance(title, str):
        raise TypeError("title must be a string")
    
    # Type validation for optional parameters
    if filetype is not None and not isinstance(filetype, str):
        raise TypeError("filetype must be a string or None")
    if indexable_file_contents is not None and not isinstance(indexable_file_contents, str):
        raise TypeError("indexable_file_contents must be a string or None")
    
    # Empty string validation for required parameters
    if external_id.strip() == "":
        raise ValueError("external_id cannot be empty")
    if external_url.strip() == "":
        raise ValueError("external_url cannot be empty")
    if title.strip() == "":
        raise ValueError("title cannot be empty")
    
    # Empty string validation for optional parameters (if provided)
    if filetype is not None and filetype.strip() == "":
        raise ValueError("filetype cannot be empty string")
    if indexable_file_contents is not None and indexable_file_contents.strip() == "":
        raise ValueError("indexable_file_contents cannot be empty string")

    file_id = _generate_slack_file_id()  # Generate unique file ID

    new_file = {
        "id": file_id,
        "external_id": external_id,
        "external_url": external_url,
        "title": title,
        "filetype": filetype,
        "indexable_file_contents": indexable_file_contents,
        "comments": []  # Initialize comments
    }

    if 'files' not in DB:
        DB['files'] = {}  # Use a dictionary for files, keyed by file_id
    DB['files'][file_id] = new_file

    # Return the response with just ok and the complete file object
    return {"ok": True, "file": new_file}


@tool_spec(
    spec={
        'name': 'delete_file',
        'description': """ Deletes a file from the Slack workspace.
        
        This function permanently removes a file from the Slack workspace, including
        from all channels where it was shared. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_id': {
                    'type': 'string',
                    'description': 'The ID of the file to delete. Must be a non-empty string.'
                }
            },
            'required': [
                'file_id'
            ]
        }
    }
)
def delete_file(file_id: str) -> Dict[str, Any]:
    """
    Deletes a file from the Slack workspace.

    This function permanently removes a file from the Slack workspace, including
    from all channels where it was shared.

    Args:
        file_id (str): The ID of the file to delete. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Status True if file is deleted, False otherwise.

    Raises:
        TypeError: If file_id is not a string.
        ValueError: If file_id is empty or contains only whitespace.
        FileNotFoundError: If the specified file_id does not exist.
    """

    # Input validation
    if not isinstance(file_id, str):
        raise TypeError("file_id must be a string.")
    
    if not file_id or not file_id.strip():
        raise ValueError("file_id cannot be empty or contain only whitespace.")

    if file_id not in DB.get("files", {}):
        raise FileNotFoundError(f"File '{file_id}' not found.")

    # Remove from main files dictionary
    del DB["files"][file_id]

    # Remove file_id from all channels
    for channel_id in DB["channels"]:
        if "files" in DB["channels"][channel_id] and file_id in DB["channels"][channel_id]["files"]:
            del DB["channels"][channel_id]["files"][file_id]

    return {"ok": True}


@tool_spec(
    spec={
        'name': 'upload_file',
        'description': """ Upload a file to Slack.
        
        It supports uploading files either by providing content directly or by specifying a file path.
        The function automatically detects file types, MIME types, and handles both text and binary files.
        Files are subject to a 50MB size limit. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'channels': {
                    'type': 'string',
                    'description': """ Comma-separated list of channel IDs or names where the file will be shared.
                    Must be valid channel IDs or names if provided. """
                },
                'content': {
                    'type': 'string',
                    'description': """ File contents as a string. If both content and file_path are provided,
                    content takes precedence. Subject to 50MB size limit. This should be used only for text files. """
                },
                'file_path': {
                    'type': 'string',
                    'description': """ Path to a local file to upload. The file will be read and its
                    content will be processed based on the file type (text or binary). Subject to 50MB size limit. It is required for binary files and can also be used for text files. """
                },
                'filename': {
                    'type': 'string',
                    'description': """ Name of the file. If not provided and file_path is given,
                    the filename will be extracted from the file path. """
                },
                'filetype': {
                    'type': 'string',
                    'description': """ File type identifier (e.g., 'pdf', 'txt', 'jpg').
                    If not provided, it will be auto-detected from the filename or file path. """
                },
                'initial_comment': {
                    'type': 'string',
                    'description': 'Initial comment to add with the file.'
                },
                'thread_ts': {
                    'type': 'string',
                    'description': 'Timestamp of parent message to reply to in a thread.'
                },
                'title': {
                    'type': 'string',
                    'description': 'Title of the file. If not provided, defaults to filename.'
                }
            },
            'required': []
        }
    }
)
def upload_file(
    channels: Optional[str] = None,
    content: Optional[str] = None,
    file_path: Optional[str] = None,
    filename: Optional[str] = None,
    filetype: Optional[str] = None,
    initial_comment: Optional[str] = None,
    thread_ts: Optional[str] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a file to Slack.

    It supports uploading files either by providing content directly or by specifying a file path.
    The function automatically detects file types, MIME types, and handles both text and binary files.
    Files are subject to a 50MB size limit.

    Args:
        channels (Optional[str]): Comma-separated list of channel IDs or or names where the file will be shared.
            Must be valid channel IDs or names if provided.
        content (Optional[str]): File contents as a string. If both content and file_path are provided,
            content takes precedence. Subject to 50MB size limit. This should be used only for text files.
        file_path (Optional[str]): Path to a local file to upload. The file will be read and its
            content will be processed based on the file type (text or binary). Subject to 50MB size limit. It is required for binary files and can also be used for text files.
        filename (Optional[str]): Name of the file. If not provided and file_path is given,
            the filename will be extracted from the file path.
        filetype (Optional[str]): File type identifier (e.g., 'pdf', 'txt', 'jpg').
            If not provided, it will be auto-detected from the filename or file path.
        initial_comment (Optional[str]): Initial comment to add with the file.
        thread_ts (Optional[str]): Timestamp of parent message to reply to in a thread.
        title (Optional[str]): Title of the file. If not provided, defaults to filename.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - file (dict): Uploaded file information containing:
                - id (str): Unique file ID
                - name (str): File name
                - title (str): File title
                - filetype (str): File type
                - mimetype (str): MIME type of the file
                - size (int): File size in bytes
                - content (str): File content (base64 encoded for binary files)
                - channels (list): List of channel IDs where file is shared
                - initial_comment (str): Initial comment if provided
                - thread_ts (str): Thread timestamp if provided
                - created (int): Unix timestamp of file creation
                - user (str): User ID who uploaded the file (from current_user)

    Raises:
        TypeError: If parameter types are incorrect
        MissingContentOrFilePathError: If neither content nor file_path is provided
        InvalidChannelIdError: If any provided channel ID is invalid
        FileSizeLimitExceededError: If file size exceeds 50MB limit
        FileReadError: If file cannot be read from the specified path
        FileNotFoundError: If specified file path does not exist
    """
    # Input validation
    if channels is not None and not isinstance(channels, str):
        raise TypeError("channels must be a string or None.")
    if content is not None and not isinstance(content, str):
        raise TypeError("content must be a string or None.")
    if file_path is not None and not isinstance(file_path, str):
        raise TypeError("file_path must be a string or None.")
    if filename is not None and not isinstance(filename, str):
        raise TypeError("filename must be a string or None.")
    if filetype is not None and not isinstance(filetype, str):
        raise TypeError("filetype must be a string or None.")
    if initial_comment is not None and not isinstance(initial_comment, str):
        raise TypeError("initial_comment must be a string or None.")
    if thread_ts is not None and not isinstance(thread_ts, str):
        raise TypeError("thread_ts must be a string or None.")
    if title is not None and not isinstance(title, str):
        raise TypeError("title must be a string or None.")

    # Must provide either content or file_path
    if not content and not file_path:
        raise MissingContentOrFilePathError("Either content or file_path must be provided")

    # Validate channels exist
    channel_list = []
    if channels:
        raw_channels = channels.split(",")
        for channel in raw_channels:
            channel = channel.strip()
            # Skip empty channels
            if not channel:
                continue
            try:
                resolved_channel = _resolve_channel(channel)
                channel_list.append(resolved_channel)
                if resolved_channel not in DB.get("channels", {}):
                    raise InvalidChannelIdError(f"Invalid channel ID: {resolved_channel}")
            except ChannelNotFoundError:
                raise InvalidChannelIdError(f"Invalid channel ID: {channel}")

    # Initialize file data
    file_content = None
    file_size = 0
    detected_mimetype = "text/plain"
    detected_filetype = "txt"
    final_filename = filename or "untitled"

    # Handle file upload
    if content:
        # Direct content provided
        max_size_bytes = 50 * 1024 * 1024  # 50MB limit
        
        # Validate original content size
        original_size = len(content.encode('utf-8'))
        if original_size > max_size_bytes:
            raise FileSizeLimitExceededError(f"Content too large: {original_size} bytes (max: {max_size_bytes})")
        
        # Content parameter is always treated as text content
        # Binary files should be handled via file_path parameter, not by encoding text content
        final_filename = filename or "untitled"
        file_content = content
        file_size = original_size
        
        if filename:
            detected_mimetype = get_mime_type(filename)
            detected_filetype = os.path.splitext(filename)[1].lower().lstrip('.') or "txt"
        else:
            detected_mimetype = "text/plain"
            detected_filetype = "txt"
        
    elif file_path:
        # File path provided - read the file with size validation (50MB limit)
        try:
            file_data = read_file(file_path, 50)  # 50MB limit
            file_content = file_data['content']
            file_size = file_data['size_bytes']
            detected_mimetype = file_data['mime_type']
            
            # Extract filename from path if not provided
            if not filename:
                final_filename = os.path.basename(file_path)
            else:
                final_filename = filename
                
            # Extract filetype from filename
            detected_filetype = os.path.splitext(final_filename)[1].lower().lstrip('.') or "unknown"
            
        except FileNotFoundError:
            # Re-raise FileNotFoundError as documented
            raise
        except ValueError as e:
            # Check if it's a file size error and convert to FileSizeLimitExceededError
            error_msg = str(e)
            if "File too large" in error_msg or "too large" in error_msg.lower():
                raise FileSizeLimitExceededError(error_msg)
            # Otherwise wrap in FileReadError
            raise FileReadError(f"Failed to read file '{file_path}': {error_msg}")
        except Exception as e:
            # Wrap any other unexpected errors
            raise FileReadError(f"Failed to read file '{file_path}': {str(e)}")

    # Use provided filetype or detected one
    final_filetype = filetype or detected_filetype
    
    # Generate file ID and create file record
    file_id = _generate_slack_file_id()
    current_time = int(time.time())
    current_user_id = DB.get("current_user", {}).get("id", "U_UNKNOWN")
    
    file_data = {
        "id": file_id,
        "name": final_filename,
        "title": title or final_filename,
        "filetype": final_filetype,
        "mimetype": detected_mimetype,
        "size": file_size,
        "content": file_content,
        "channels": channel_list,
        "initial_comment": initial_comment,
        "thread_ts": thread_ts,
        "created": current_time,
        "user": current_user_id
    }

    # Store file in database
    if "files" not in DB:
        DB["files"] = {}
    DB["files"][file_id] = file_data

    # Associate file with channels
    if channels:
        for channel_id in channel_list:
            if "files" not in DB["channels"][channel_id]:
                DB["channels"][channel_id]["files"] = {}
            DB["channels"][channel_id]["files"][file_id] = True

    return {
        "ok": True,
        "file": file_data
    }

@tool_spec(
    spec={
        'name': 'get_external_upload_url',
        'description': """ Generates a URL for uploading an external file to Slack.
        
        This function initiates the file upload process by providing a secure,
        temporary URL to which the file data can be sent. It takes basic file
        information, such as its name and size, and returns a unique file ID
        and the corresponding upload URL. It also starts a 1-minute timer to
        automatically delete the file record if the upload is not completed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filename': {
                    'type': 'string',
                    'description': 'The name of the file to be uploaded.'
                },
                'length': {
                    'type': 'integer',
                    'description': 'The size of the file in bytes.'
                },
                'alt_txt': {
                    'type': 'string',
                    'description': """ A description of the file used for
                    accessibility purposes (e.g., by screen readers). """
                },
                'snippet_type': {
                    'type': 'string',
                    'description': """ The specific type of snippet, which
                    can be used to influence how the file is displayed. """
                }
            },
            'required': [
                'filename',
                'length'
            ]
        }
    }
)
def get_external_upload_url(
    filename: str,
    length: int,
    alt_txt: Optional[str] = None,
    snippet_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a URL for uploading an external file to Slack.

    This function initiates the file upload process by providing a secure,
    temporary URL to which the file data can be sent. It takes basic file
    information, such as its name and size, and returns a unique file ID
    and the corresponding upload URL. It also starts a 1-minute timer to
    automatically delete the file record if the upload is not completed.

    Args:
        filename (str): The name of the file to be uploaded.
        length (int): The size of the file in bytes.
        alt_txt (Optional[str]): A description of the file used for
            accessibility purposes (e.g., by screen readers).
        snippet_type (Optional[str]): The specific type of snippet, which
            can be used to influence how the file is displayed.

    Returns:
        Dict[str, Any]: A dictionary containing the details for the upload,
            which includes the following keys:
            - ok (bool): Always `True` to indicate success.
            - upload_url (str): A temporary, unique URL where the file
              should be uploaded.
            - file_id (str): A unique, Slack-generated ID that will be
              associated with the uploaded file.

    Raises:
        TypeError: If `filename`, `alt_txt`, or `snippet_type` are provided
            but are not strings, or if `length` is not an integer.
        ValueError: If `filename` is an empty string, if `length` is less
            than or equal to zero, or if `alt_txt` exceeds 1000 characters.
        FileSizeLimitExceededError: If `length` exceeds 50 MB (52_428_800 bytes).
    """
    if not isinstance(filename, str):
        raise TypeError("filename must be a string.")
    if not filename:
        raise ValueError("filename cannot be an empty string.")

    if not isinstance(length, int):
        raise TypeError("length must be an integer.")
    if length <= 0:
        raise ValueError("length must be a positive integer.")

    # Enforce 50 MB (52_428_800 bytes) size restriction for all uploads
    MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
    if length > MAX_SIZE_BYTES:
        raise FileSizeLimitExceededError("File size exceeds the 50 MB limit.")

    if alt_txt is not None and not isinstance(alt_txt, str):
        raise TypeError("alt_txt must be a string.")

    # alt_txt length restriction (max 1000 characters)
    if isinstance(alt_txt, str) and len(alt_txt) > 1000:
        raise ValueError("alt_txt cannot exceed 1000 characters.")

    if snippet_type is not None and not isinstance(snippet_type, str):
        raise TypeError("snippet_type must be a string.")

    file_id = _generate_slack_file_id()
    current_time = int(time.time())

    if "files" not in DB:
        DB["files"] = {}

    DB["files"][file_id] = {
        "id": file_id,
        "created": current_time,
        "status": "pending_upload",
        "filename": filename,
        "length": length,
        "alt_txt": alt_txt,
        "snippet_type": snippet_type,
    }

    # Start a timer to clean up the file if it's not finalized in 5 minutes
    timer = threading.Timer(60.0, _check_and_delete_pending_file, args=[file_id])
    timer.daemon = True  # Allows the main program to exit even if timers are active
    timer.start()

    upload_url = f"https://example.com/upload/{file_id}"

    return {"ok": True, "upload_url": upload_url, "file_id": file_id}

@tool_spec(
    spec={
        'name': 'finish_external_file_upload',
        'description': 'Finishes an external file upload started with `get_external_upload_url()`.',
        'parameters': {
            'type': 'object',
            'properties': {
                'files': {
                    'type': 'array',
                    'description': 'List of file object dictionaries. Each dictionary must contain:',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {
                                'type': 'string',
                                'description': 'Required. The ID of the file to update.'
                            },
                            'title': {
                                'type': 'string',
                                'description': 'Optional. The new title for the file.'
                            }
                        },
                        'required': [
                            'id'
                        ]
                    }
                },
                'channel_id': {
                    'type': 'string',
                    'description': 'Channel ID where the file will be shared.'
                },
                'initial_comment': {
                    'type': 'string',
                    'description': 'Initial comment for the file.'
                },
                'thread_ts': {
                    'type': 'string',
                    'description': 'Parent message timestamp for threading.'
                }
            },
            'required': [
                'files'
            ]
        }
    }
)
def finish_external_upload(
    files: List[Dict[str, Any]],
    channel_id: Optional[str] = None,
    initial_comment: Optional[str] = None,
    thread_ts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Finishes an external file upload started with `get_external_upload_url()`.

    Args:
        files (List[Dict[str, Any]]): List of file object dictionaries. Each dictionary must contain:
            - id (str): Required. The ID of the file to update.
            - title (Optional[str]): Optional. The new title for the file.
        channel_id (Optional[str]): Channel ID where the file will be shared.
        initial_comment (Optional[str]): Initial comment for the file.
        thread_ts (Optional[str]): Parent message timestamp for threading.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful

    Raises:
        TypeError: If files is not a list, or if channel_id, initial_comment, or thread_ts is not a string or None.
        ValueError: If files list is empty, or if file objects are malformed (missing 'id' field or not dictionaries).
        ChannelNotFoundError: If the specified channel_id does not exist.
        FileNotFoundError: If any file_id in the files list does not exist.
    """
    # Input validation - manual checks first to match expected error messages
    if not isinstance(files, list):
        raise TypeError("files must be a list.")

    if channel_id is not None and not isinstance(channel_id, str):
        raise TypeError("channel_id must be a string or None.")

    if initial_comment is not None and not isinstance(initial_comment, str):
        raise TypeError("initial_comment must be a string or None.")

    if thread_ts is not None and not isinstance(thread_ts, str):
        raise TypeError("thread_ts must be a string or None.")

    if not files:
        raise ValueError("files list cannot be empty.")

    # Validate each file object
    for file_info in files:
        if not isinstance(file_info, dict):
            raise ValueError("Each file object must be a dictionary.")

        if "id" not in file_info:
            raise ValueError("Each file object must contain an 'id' field.")

    # Channel validation
    if channel_id and channel_id not in DB.get("channels", {}):
        raise ChannelNotFoundError(f"Channel '{channel_id}' not found.")

    # Now use Pydantic for additional validation and structured data
    try:
        request = FinishExternalUploadRequest(
            files=files,
            channel_id=channel_id,
            initial_comment=initial_comment,
            thread_ts=thread_ts
        )
    except Exception as e:
        # We've already handled the basic validation cases above,
        # so this would be an unexpected validation error
        raise ValueError(f"Invalid input format: {str(e)}")

    # Process each file
    for file_info in request.files:
        # Check if file exists
        if file_info.id not in DB.get("files", {}):
            raise FileNotFoundError(f"File '{file_info.id}' not found.")

        # Update existing file
        update_data = {}
        if file_info.title is not None:
            update_data["title"] = file_info.title
        if request.initial_comment is not None:
            update_data["initial_comment"] = request.initial_comment
        if request.thread_ts is not None:
            update_data["thread_ts"] = request.thread_ts

        DB["files"][file_info.id].update(update_data)

        # Associate with channel if provided
        if request.channel_id:
            if "files" not in DB["channels"][request.channel_id]:
                DB["channels"][request.channel_id]["files"] = {}
            DB["channels"][request.channel_id]["files"][file_info.id] = True

    return {"ok": True}


@tool_spec(
    spec={
        'name': 'list_files',
        'description': """ Lists files, optionally filtered by channel, user, and time.
        
        This function retrieves files from the Slack workspace with optional filtering capabilities.
        Files can be filtered by channel, user, timestamp range, and file types. Results are paginated
        for efficient data retrieval. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'channel_id': {
                    'type': 'string',
                    'description': 'Filter files shared in a specific channel. Must be a valid channel ID if provided.'
                },
                'user_id': {
                    'type': 'string',
                    'description': 'Filter files uploaded by a specific user. Must be a valid user ID if provided.'
                },
                'ts_from': {
                    'type': 'string',
                    'description': 'Filter files created after this timestamp (inclusive). Must be a Unix timestamp string if provided.'
                },
                'ts_to': {
                    'type': 'string',
                    'description': 'Filter files created before this timestamp (inclusive). Must be a Unix timestamp string if provided.'
                },
                'types': {
                    'type': 'string',
                    'description': 'Comma-separated list of file types to filter by (e.g., "pdf,docx,jpg").'
                },
                'cursor': {
                    'type': 'string',
                    'description': 'Pagination cursor for retrieving additional results. Must be a string representing a non-negative integer.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of files to return per page. Must be a positive integer. Defaults to 100.'
                }
            },
            'required': []
        }
    }
)
def list_files(
    channel_id: Optional[str] = None,
    user_id: Optional[str] = None,
    ts_from: Optional[str] = None,
    ts_to: Optional[str] = None,
    types: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Lists files, optionally filtered by channel, user, and time.

    This function retrieves files from the Slack workspace with optional filtering capabilities.
    Files can be filtered by channel, user, timestamp range, and file types. Results are paginated
    for efficient data retrieval.

    Args:
        channel_id (Optional[str]): Filter files shared in a specific channel. Must be a valid channel ID if provided.
        user_id (Optional[str]): Filter files uploaded by a specific user. Must be a valid user ID if provided.
        ts_from (Optional[str]): Filter files created after this timestamp (inclusive). Must be a Unix timestamp string if provided.
        ts_to (Optional[str]): Filter files created before this timestamp (inclusive). Must be a Unix timestamp string if provided.
        types (Optional[str]): Comma-separated list of file types to filter by (e.g., "pdf,docx,jpg").
        cursor (Optional[str]): Pagination cursor for retrieving additional results. Must be a string representing a non-negative integer.
        limit (int): Maximum number of files to return per page. Must be a positive integer. Defaults to 100.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - files (list): List of file objects matching the filter criteria
            - response_metadata (dict): Pagination metadata containing:
                - next_cursor (str): Cursor for next page of results, or None if no more pages

    Raises:
        TypeError: If any argument is of an incorrect type.
        ValueError: If limit is not a positive integer, or if timestamp strings cannot be parsed.
        ChannelNotFoundError: If the specified channel_id does not exist.
        UserNotFoundError: If the specified user_id does not exist.
        InvalidCursorFormatError: If cursor is provided but cannot be parsed as a non-negative integer.
        CursorOutOfBoundsError: If cursor exceeds the length of available data.
    """
    # Input validation
    if channel_id is not None and not isinstance(channel_id, str):
        raise TypeError("channel_id must be a string or None.")
    
    if user_id is not None and not isinstance(user_id, str):
        raise TypeError("user_id must be a string or None.")
    
    if ts_from is not None and not isinstance(ts_from, str):
        raise TypeError("ts_from must be a string or None.")
    
    if ts_to is not None and not isinstance(ts_to, str):
        raise TypeError("ts_to must be a string or None.")
    
    if types is not None and not isinstance(types, str):
        raise TypeError("types must be a string or None.")
    
    if cursor is not None and not isinstance(cursor, str):
        raise TypeError("cursor must be a string or None.")

    # Handle empty string values
    if isinstance(channel_id, str) and not channel_id.strip():
        channel_id = None

    if isinstance(user_id, str) and not user_id.strip():
        user_id = None

    if isinstance(ts_from, str) and not ts_from.strip():
        ts_from = None

    if isinstance(ts_to, str) and not ts_to.strip():
        ts_to = None

    if isinstance(types, str) and not types.strip():
        types = None

    if isinstance(cursor, str) and not cursor.strip():
        cursor = None

    if type(limit) is not int:
        raise TypeError("limit must be an integer.")
    
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")
    
    # Validate user exists if user_id is provided
    if user_id and user_id not in DB.get("users", {}):
        raise UserNotFoundError(f"User '{user_id}' not found.")
    
    # Validate channel exists if channel_id is provided
    if channel_id and channel_id not in DB.get("channels", {}):
        raise ChannelNotFoundError(f"Channel '{channel_id}' not found.")

    # Get files based on channel filter
    if channel_id:
        # Get file IDs for the specified channel
        channel_files = DB["channels"][channel_id].get("files", {})
        file_ids = list(channel_files.keys())
        # Retrieve file details from the main files dictionary
        filtered_files = [DB["files"][file_id] for file_id in file_ids if file_id in DB.get("files", {})]
    else:
        # Get all files if no channel filter is provided
        filtered_files = list(DB.get("files", {}).values())

    # Apply additional filters (can be combined with any primary filter)
    if user_id:
        filtered_files = [f for f in filtered_files if f.get("user") == user_id]
    
    # Validate user input timestamps first (before processing database data)
    ts_from_int = None
    ts_to_int = None
    
    if ts_from:
        try:
            ts_from_int = int(ts_from)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid ts_from format: {ts_from}. Must be a Unix timestamp string.")
    
    if ts_to:
        try:
            ts_to_int = int(ts_to)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid ts_to format: {ts_to}. Must be a Unix timestamp string.")
    
    # Validate that ts_to >= ts_from when both are provided
    if ts_from_int is not None and ts_to_int is not None:
        if ts_to_int < ts_from_int:
            raise ValueError("ts_to must be greater than or equal to ts_from.")
    
    # Apply timestamp filters (assumes database timestamps are well-formed integers)
    if ts_from_int is not None:
        filtered_files = [f for f in filtered_files if int(f.get("created", 0)) >= ts_from_int]
    
    if ts_to_int is not None:
        filtered_files = [f for f in filtered_files if int(f.get("created", 0)) <= ts_to_int]
    
    if types:
        types_list = [t.strip() for t in types.split(",") if t.strip()]
        if types_list:  # Only apply filter if there are valid types
            filtered_files = [f for f in filtered_files if f.get("filetype") in types_list]

    # Handle pagination
    start_index = 0
    if cursor:
        try:
            start_index = int(cursor)
        except ValueError:
            raise InvalidCursorFormatError("Invalid cursor format. Must be a string representing an integer.")
        
        if start_index < 0:
            raise InvalidCursorFormatError("Cursor must represent a non-negative integer.")
        
        if start_index >= len(filtered_files):
            raise CursorOutOfBoundsError(f"Cursor {cursor} exceeds available data length ({len(filtered_files)})")

    end_index = min(start_index + limit, len(filtered_files))
    paginated_files = filtered_files[start_index:end_index]
    next_cursor = str(end_index) if end_index < len(filtered_files) else None

    return {
        "ok": True,
        "files": paginated_files,
        "response_metadata": {"next_cursor": next_cursor}
    }


@tool_spec(
    spec={
        'name': 'remove_remote_file',
        'description': """ Remove a remote file and clean up all of its references.
        
        Exactly **one** identifier must be supplied – either a Slack-generated
        ``file_id`` *or* the external ``external_id`` that was provided when the
        file was first registered.  When the target is found the file record is
        deleted from the workspace's internal storage and its identifier is
        removed from every channel that had access to the file. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_id': {
                    'type': 'string',
                    'description': 'The unique Slack-generated ID of the file to remove.'
                },
                'external_id': {
                    'type': 'string',
                    'description': """ The creator-defined GUID that was supplied when the remote file
                    was added via :pyfunc:`add_remote_file` or the external upload
                    flow. """
                }
            },
            'required': []
        }
    }
)
def remove_remote_file(
    file_id: Optional[str] = None,
    external_id: Optional[str] = None
) -> Dict[str, Any]:
    """Remove a remote file and clean up all of its references.

    Exactly **one** identifier must be supplied – either a Slack-generated
    ``file_id`` *or* the external ``external_id`` that was provided when the
    file was first registered.  When the target is found the file record is
    deleted from the workspace's internal storage and its identifier is
    removed from every channel that had access to the file.

    Args:
        file_id (Optional[str]):
            The unique Slack-generated ID of the file to remove.
        external_id (Optional[str]):
            The creator-defined GUID that was supplied when the remote file
            was added via :pyfunc:`add_remote_file` or the external upload
            flow.

    Returns:
        Dict[str, Any]: A dictionary confirming the success of the operation,
            in the format ``{"ok": True}``.

    Raises:
        TypeError: If *file_id* or *external_id* is provided but is **not** a
            ``str``.
        ValueError: If **neither** identifier is supplied, **both** are
            supplied, or any supplied identifier is an empty/whitespace-only
            string.
        FileNotFoundError: If no file matches the supplied identifier.
    """

    # ------------------------------------------------------------------
    # 1. Basic type checks
    # ------------------------------------------------------------------
    if file_id is not None and not isinstance(file_id, str):
        raise TypeError("file_id must be a string.")
    if external_id is not None and not isinstance(external_id, str):
        raise TypeError("external_id must be a string.")

    # ------------------------------------------------------------------
    # 2. Presence / exclusivity checks
    # ------------------------------------------------------------------
    provided_ids = [("file_id", file_id), ("external_id", external_id)]
    provided_count = sum(1 for _name, _val in provided_ids if _val is not None)

    if provided_count == 0:
        raise ValueError("Either file_id or external_id must be provided.")
    if provided_count > 1:
        raise ValueError("Provide *either* file_id *or* external_id, not both (too_many_ids).")

    # ------------------------------------------------------------------
    # 3. Empty-string validation
    # ------------------------------------------------------------------
    if file_id is not None and not file_id.strip():
        raise ValueError("file_id cannot be an empty string.")
    if external_id is not None and not external_id.strip():
        raise ValueError("external_id cannot be an empty string.")

    # ------------------------------------------------------------------
    # 4. Locate the file to remove
    # ------------------------------------------------------------------
    file_to_remove: Optional[str] = None
    files_db = DB.get("files", {})

    if file_id is not None:
        if file_id in files_db:
            file_to_remove = file_id
    else:  # external_id path – we have already ensured exclusivity
        for f_id, file_data in files_db.items():
            if file_data.get("external_id") == external_id:
                file_to_remove = f_id
                break

    if file_to_remove is None:
        raise FileNotFoundError("File not found.")

    # ------------------------------------------------------------------
    # 5. Delete from main repository
    # ------------------------------------------------------------------
    del DB["files"][file_to_remove]

    # ------------------------------------------------------------------
    # 6. Purge references from every channel
    # ------------------------------------------------------------------
    for channel_data in DB.get("channels", {}).values():
        # Some channels may not yet contain a 'files' key
        if "files" in channel_data and file_to_remove in channel_data["files"]:
            del channel_data["files"][file_to_remove]

    # ------------------------------------------------------------------
    # 7. Done.
    # ------------------------------------------------------------------
    return {"ok": True}
