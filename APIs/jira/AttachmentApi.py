from common_utils.tool_spec_decorator import tool_spec
# jira/AttachmentApi.py
import base64
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import os

from .SimulationEngine.db import DB
from .SimulationEngine.file_utils import (
    read_file, write_file
)
from .SimulationEngine.custom_errors import ValidationError, NotFoundError

@tool_spec(
    spec={
        'name': 'get_attachment_metadata',
        'description': """ Get attachment metadata without file content.
        
        Returns metadata information for an attachment.
        This is useful for getting file information (name, size, type, etc.) """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': """ The unique identifier of the attachment. Must be a positive 
                    integer or a string representation of a positive integer. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_attachment_metadata(id: Union[str, int]) -> Dict[str, Any]:
    """Get attachment metadata without file content.
    
    Returns metadata information for an attachment.
    This is useful for getting file information (name, size, type, etc.) 
    
    Args:
        id (Union[str, int]): The unique identifier of the attachment. Must be a positive 
            integer or a string representation of a positive integer.
        
    Returns:
        Dict[str, Any]: A dictionary containing the attachment metadata with keys:
            - id (int): The unique attachment identifier
            - filename (str): Original filename of the attachment
            - fileSize (int): File size in bytes
            - mimeType (str): MIME type of the file (e.g., 'text/plain', 'image/png')
            - created (str): ISO 8601 timestamp when attachment was uploaded
            - checksum (str): SHA256 checksum for file integrity verification
            - parentId (str): The ID of the issue this attachment belongs to
            
    Raises:
        TypeError: If id is not a string or integer type.
        ValidationError: If id is empty, not a valid integer, 
            zero, or negative.
        NotFoundError: If no attachment exists with the specified id.
        ValueError: If there are issues getting the attachment content.
    
    """
    # Input validation - type checking
    if not isinstance(id, (str, int)):
        raise TypeError(f"id must be string or integer, got {type(id).__name__}")
    
    # Convert string id to integer and validate
    try:
        if isinstance(id, str):
            # Check for empty string
            if not id.strip():
                raise ValidationError("id cannot be empty string")
            attachment_id = int(id)
        else:
            attachment_id = id
    except (ValueError, TypeError):
        raise ValidationError("id must be a valid integer or string representation of integer")
    
    # Validate attachment ID range
    if attachment_id <= 0:
        raise ValidationError("id must be a positive integer")
    
    # Check if attachments section exists in database
    if "attachments" not in DB:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    # Check if specific attachment exists
    attachment_key = str(attachment_id)
    if attachment_key not in DB["attachments"]:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    attachment = DB["attachments"][attachment_key]
    
    # Return attachment metadata (without the actual data content)
    return {
        "id": attachment["id"],
        "filename": attachment["filename"],
        "fileSize": attachment["fileSize"],
        "mimeType": attachment["mimeType"],
        "created": attachment["created"],
        "checksum": attachment["checksum"],
        "parentId": attachment["parentId"]
    }


@tool_spec(
    spec={
        'name': 'delete_attachment',
        'description': """ Delete an attachment and remove all references from issues.
        
        Permanently removes an attachment from the system, including the file data 
        and all references to it from issues. This operation cannot be undone.
        The function performs a complete cleanup by removing both the attachment 
        record and all issue references to ensure data consistency. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': """ The unique identifier of the attachment to delete.
                    Must be a positive integer or a string representation of a positive integer. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete_attachment(id: Union[str, int]) -> bool:
    """Delete an attachment and remove all references from issues.
    
    Permanently removes an attachment from the system, including the file data 
    and all references to it from issues. This operation cannot be undone.
    The function performs a complete cleanup by removing both the attachment 
    record and all issue references to ensure data consistency.
    
    Args:
        id (Union[str, int]): The unique identifier of the attachment to delete.
            Must be a positive integer or a string representation of a positive integer.
        
    Returns:
        bool: Always returns True upon successful deletion. The function raises 
            exceptions for any error conditions rather than returning False.
        
    Raises:
        TypeError: If id is not a string or integer type.
        ValidationError: If id is empty, not a valid integer,
            zero, or negative.
        NotFoundError: If no attachment exists with the specified id.

    """
    # Input validation - type checking
    if not isinstance(id, (str, int)):
        raise TypeError(f"id must be string or integer, got {type(id).__name__}")
    
    # Convert string id to integer and validate
    try:
        if isinstance(id, str):
            # Check for empty string
            if not id.strip():
                raise ValidationError("id cannot be empty string")
            attachment_id = int(id)
        else:
            attachment_id = id
    except (ValueError, TypeError):
        raise ValidationError("id must be a valid integer or string representation of integer")
    
    # Validate attachment ID range
    if attachment_id <= 0:
        raise ValidationError("id must be a positive integer")
    
    # Check if attachments section exists in database
    if "attachments" not in DB:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    # Check if specific attachment exists
    attachment_key = str(attachment_id)
    if attachment_key not in DB["attachments"]:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    # Remove attachment from database
    del DB["attachments"][attachment_key]
    
    # Remove attachment reference from all issues
    for issue_id, issue_data in DB.get("issues", {}).items():
        attachment_ids = issue_data.get("fields", {}).get("attachmentIds", [])
        new_attachment_ids = [attachment for attachment in attachment_ids if attachment != attachment_id]     
        DB["issues"][issue_id]["fields"]["attachmentIds"] = new_attachment_ids
   
    return True


@tool_spec(
    spec={
        'name': 'add_attachment',
        'description': """ Add an attachment to an issue from a file path.
        
        Creates a new attachment associated with the specified issue by reading
        a file from the filesystem. Automatically handles MIME type detection,
        file size validation, encoding, and checksum generation. The attachment
        is stored in the database with full metadata and the issue is updated
        to reference the new attachment. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issue_id_or_key': {
                    'type': 'string',
                    'description': """ The unique identifier or key of the target issue.
                    Must be a non-empty string that exists in the database. """
                },
                'file_path': {
                    'type': 'string',
                    'description': """ Filesystem path to the file to attach. The file will
                    be read from disk and the filename will be extracted from the path. """
                }
            },
            'required': [
                'issue_id_or_key',
                'file_path'
            ]
        }
    }
)
def add_attachment(issue_id_or_key: str, file_path: str) -> List[Dict[str, Any]]:
    """Add an attachment to an issue from a file path.
    
    Creates a new attachment associated with the specified issue by reading
    a file from the filesystem. Automatically handles MIME type detection,
    file size validation, encoding, and checksum generation. The attachment
    is stored in the database with full metadata and the issue is updated
    to reference the new attachment.
    
    Args:
        issue_id_or_key (str): The unique identifier or key of the target issue.
            Must be a non-empty string that exists in the database.
        file_path (str): Filesystem path to the file to attach. The file will
            be read from disk and the filename will be extracted from the path.
        
    Returns:
        List[Dict[str, Any]]: A list containing one dictionary with the created attachment
            metadata. The dictionary contains:
            - id (int): The unique attachment identifier
            - filename (str): The attachment filename (extracted from file_path)
            - fileSize (int): File size in bytes (limit 25MB)
            - mimeType (str): Detected MIME type (e.g., 'text/plain', 'image/png')
            - created (str): ISO 8601 timestamp when attachment was created
            - content (str): Data of the attachment
            - parentId (str): The ID of the issue this attachment belongs to
            - checksum (str): SHA256 checksum for file integrity verification
        
    Raises:
        TypeError: If issue_id_or_key or file_path is not a string.
        ValidationError: If:
            - issue_id_or_key is empty or whitespace-only
            - file_path is empty or whitespace-only
            - File processing fails (encoding, size limits, etc.)
        NotFoundError: If the specified issue does not exist in the database.
        FileNotFoundError: If the file at file_path does not exist.
    
    """
    # Input validation - type checking
    if not isinstance(issue_id_or_key, str):
        raise TypeError("issue_id_or_key must be a string")
    
    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string")
    
    # Validate issue_id_or_key content
    if not issue_id_or_key.strip():
        raise ValidationError("issue_id_or_key cannot be empty")
    
    # Validate file_path content
    if not file_path.strip():
        raise ValidationError("file_path cannot be empty")
    
    # Check if issue exists in database
    if "issues" not in DB:
        raise NotFoundError(f"Issue {issue_id_or_key} not found")
    
    if issue_id_or_key not in DB["issues"]:
        raise NotFoundError(f"Issue {issue_id_or_key} not found")
    
    # Process file from path
    try:
        filename = os.path.basename(file_path)
        # Use comprehensive read_file() approach with all validations
        file_info = read_file(file_path, max_size_mb=25)  # 25MB limit like Jira
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except ValueError as e:
        raise ValidationError(f"File processing error: {str(e)}")
    
    # Generate new attachment ID
    attachment_id = DB.get("counters", {}).get("attachment", 1000) + 1
    DB.setdefault("counters", {})["attachment"] = attachment_id

    if "attachmentIds" not in DB["issues"][issue_id_or_key]["fields"]:
        DB["issues"][issue_id_or_key]["fields"]["attachmentIds"] = []
    DB["issues"][issue_id_or_key]["fields"]["attachmentIds"].append(attachment_id)
    
    # Create attachment record
    attachment = {
        "id": attachment_id,
        "filename": filename,
        "fileSize": file_info['size_bytes'],
        "mimeType": file_info['mime_type'],
        "content": file_info['content'],
        "encoding": file_info['encoding'],
        "created": datetime.now().isoformat() + "Z",
        "checksum": f"sha256:{hashlib.sha256(file_info['content'].encode()).hexdigest()}",
        "parentId": issue_id_or_key
    }
    
    # Store attachment in database
    DB.setdefault("attachments", {})[str(attachment_id)] = attachment
    
    # Add attachment reference to issue
    issue = DB["issues"][issue_id_or_key]
    
    # Return attachment metadata in API format
    return [{
        "id": attachment_id,
        "filename": attachment["filename"],
        "fileSize": attachment["fileSize"],
        "mimeType": attachment["mimeType"],
        "created": attachment["created"],
        "content": attachment["content"],
        "parentId": attachment["parentId"],
        "checksum": attachment["checksum"]
    }]


@tool_spec(
    spec={
        'name': 'list_issue_attachments',
        'description': """ List all attachments associated with an issue.
        
        Retrieves metadata for all attachments that are currently associated with the
        specified issue. The function automatically handles orphaned references by
        skipping attachments that were deleted but still have references in the issue.
        Returns an empty list if the issue has no attachments. The attachments are
        returned in the order they appear in the issue's attachment list. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issue_id_or_key': {
                    'type': 'string',
                    'description': """ The unique identifier or key of the issue to query.
                    Must be a non-empty string that exists in the database. """
                }
            },
            'required': [
                'issue_id_or_key'
            ]
        }
    }
)
def list_issue_attachments(issue_id_or_key: str) -> List[Dict[str, Any]]:
    """List all attachments associated with an issue.
    
    Retrieves metadata for all attachments that are currently associated with the
    specified issue. The function automatically handles orphaned references by
    skipping attachments that were deleted but still have references in the issue.
    Returns an empty list if the issue has no attachments. The attachments are
    returned in the order they appear in the issue's attachment list.
    
    Args:
        issue_id_or_key (str): The unique identifier or key of the issue to query.
            Must be a non-empty string that exists in the database.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing attachment metadata.
            Each dictionary contains:
            - id (int): The unique attachment identifier
            - filename (str): Original filename of the attachment
            - fileSize (int): File size in bytes
            - mimeType (str): MIME type of the file (e.g., 'text/plain', 'image/png')
            - created (str): ISO 8601 timestamp when attachment was uploaded
            - checksum (str): SHA256 checksum for file integrity verification
            - parentId (str): The ID of the issue this attachment belongs to
            
            Returns an empty list if the issue has no attachments or if all
            attachment references point to deleted attachments.
        
    Raises:
        TypeError: If issue_id_or_key is not a string type.
        ValidationError: If issue_id_or_key is empty or whitespace-only.
        NotFoundError: If no issue exists with the specified identifier.
    
    """
    # Input validation - type checking
    if not isinstance(issue_id_or_key, str):
        raise TypeError("issue_id_or_key must be a string")
    
    # Validate issue_id_or_key content
    if not issue_id_or_key.strip():
        raise ValidationError("issue_id_or_key cannot be empty")
    
    # Check if issues section exists in database
    if "issues" not in DB:
        raise NotFoundError(f"Issue {issue_id_or_key} not found")
    
    # Check if specific issue exists
    if issue_id_or_key not in DB["issues"]:
        raise NotFoundError(f"Issue {issue_id_or_key} not found")
    
    # Get attachment IDs from issue
    issue = DB["issues"][issue_id_or_key]
    attachment_ids = issue.get("fields", {}).get("attachmentIds", [])
    
    # Get attachment metadata for each ID
    attachments = []
    for attachment_id in attachment_ids:
        try:
            attachment_metadata = get_attachment_metadata(attachment_id)
            attachments.append(attachment_metadata)
        except NotFoundError:
            # Skip if attachment was deleted but reference still exists
            # This handles orphaned references gracefully
            continue
    
    return attachments


@tool_spec(
    spec={
        'name': 'download_attachment',
        'description': """ Download attachment content to a local file in the current directory.
        
        Downloads the specified attachment and saves it to the current directory using
        the attachment's original filename. This function handles both binary and text 
        attachments, automatically detecting the appropriate encoding and writing method 
        based on the attachment's stored encoding format.
        
        The function retrieves the attachment data directly from the database and
        then processes it according to its encoding:
        - Base64 encoded attachments are decoded and written as binary files
        - Text attachments are written directly as UTF-8 text files """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': """ The unique identifier of the attachment to download.
                    Can be provided as an integer or string representation of the attachment ID.
                    Must be a positive integer that exists in the database. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def download_attachment(id: Union[str, int]) -> bool:
    """Download attachment content to a local file in the current directory.
    
    Downloads the specified attachment and saves it to the current directory using
    the attachment's original filename. This function handles both binary and text 
    attachments, automatically detecting the appropriate encoding and writing method 
    based on the attachment's stored encoding format.
    
    The function retrieves the attachment data directly from the database and
    then processes it according to its encoding:
    - Base64 encoded attachments are decoded and written as binary files
    - Text attachments are written directly as UTF-8 text files
    
    Args:
        id (Union[str, int]): The unique identifier of the attachment to download.
            Can be provided as an integer or string representation of the attachment ID.
            Must be a positive integer that exists in the database.
        
    Returns:
        bool: Always returns True upon successful completion. The function raises
            exceptions for any error conditions rather than returning False.
        
    Raises:
        TypeError: If id is not a string or integer.
        ValidationError: If id cannot be converted to a positive integer
            or if id is empty string/whitespace.
        NotFoundError: If no attachment exists with the specified ID.
        OSError: If there are filesystem permission issues or disk space problems
            when writing the file.
        IOError: If there are issues reading attachment data or writing to the output file.
    
    """
    # Input validation - type checking
    if not isinstance(id, (str, int)):
        raise TypeError(f"id must be string or integer, got {type(id).__name__}")
    
    # Convert string id to integer and validate
    try:
        if isinstance(id, str):
            # Check for empty string
            if not id.strip():
                raise ValidationError("id cannot be empty string")
            attachment_id = int(id)
        else:
            attachment_id = id
    except (ValueError, TypeError):
        raise ValidationError("id must be a valid integer or string representation of integer")
    
    # Validate attachment ID range
    if attachment_id <= 0:
        raise ValidationError("id must be a positive integer")
    
    # Check if attachments section exists in database
    if "attachments" not in DB:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    # Check if specific attachment exists
    attachment_key = str(attachment_id)
    if attachment_key not in DB["attachments"]:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    attachment = DB["attachments"][attachment_key]
    
    # Use attachment's filename in current directory
    output_path = attachment["filename"]
    
    # Write file using unified write_file function
    write_file(output_path, attachment["content"], attachment["encoding"])
    
    return True


@tool_spec(
    spec={
        'name': 'get_attachment_content',
        'description': """ Get attachment content as binary data.
        
        Retrieves the raw binary content of an attachment without saving it to disk.
        This function decodes the stored attachment data and returns it as binary content.
        The content is returned as bytes that can be used directly by applications for processing, 
        streaming, or further manipulation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': """ The unique identifier of the attachment to retrieve.
                    Can be provided as an integer or string representation of the attachment ID.
                    Must be a positive integer that exists in the database. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_attachment_content(id: Union[str, int]) -> Dict[str, Any]:
    """Get attachment content as binary data.
    
    Retrieves the raw binary content of an attachment without saving it to disk.
    This function decodes the stored attachment data and returns it as binary content.
    The content is returned as bytes that can be used directly by applications for processing, 
    streaming, or further manipulation.
    
    Args:
        id (Union[str, int]): The unique identifier of the attachment to retrieve.
            Can be provided as an integer or string representation of the attachment ID.
            Must be a positive integer that exists in the database.
        
    Returns:
        Dict[str, Any]: A dictionary containing the attachment content with keys:
            - content (bytes): The raw binary content of the attachment. For base64
              encoded attachments, this is the decoded binary data. For text attachments,
              this is the content encoded as UTF-8 bytes.
        
    Raises:
        TypeError: If id is not a string or integer.
        ValidationError: If id cannot be converted to a positive integer
            or if id is empty string/whitespace.
        NotFoundError: If no attachment exists with the specified ID.
        ValueError: If there are issues decoding the attachment data (e.g., invalid base64).
    
    """
    # Input validation - type checking
    if not isinstance(id, (str, int)):
        raise TypeError(f"id must be string or integer, got {type(id).__name__}")
    
    # Convert string id to integer and validate
    try:
        if isinstance(id, str):
            # Check for empty string
            if not id.strip():
                raise ValidationError("id cannot be empty string")
            attachment_id = int(id)
        else:
            attachment_id = id
    except (ValueError, TypeError):
        raise ValidationError("id must be a valid integer or string representation of integer")
    
    # Validate attachment ID range
    if attachment_id <= 0:
        raise ValidationError("id must be a positive integer")
    
    # Check if attachments section exists in database
    if "attachments" not in DB:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    # Check if specific attachment exists
    attachment_key = str(attachment_id)
    if attachment_key not in DB["attachments"]:
        raise NotFoundError(f"Attachment with id {attachment_id} not found")
    
    attachment = DB["attachments"][attachment_key]
    
    # Decode content based on encoding
    try:
        if attachment["encoding"] == "base64":
            # Decode base64 to get raw binary content
            content = base64.b64decode(attachment["content"])
        else:
            # For text content, encode as UTF-8 bytes
            content = attachment["content"].encode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decode attachment content: {str(e)}")
    
    return {
        "content": content
    } 