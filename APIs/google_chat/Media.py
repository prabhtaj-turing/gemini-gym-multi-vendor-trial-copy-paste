from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
# APIs/google_chat/Media.py

import re
from typing import Any, Dict, Union
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    InvalidParentFormatError, 
)
from .SimulationEngine.models import AttachmentRequestModel, UploadArguments
from pydantic import ValidationError


@tool_spec(
    spec={
        'name': 'download_media',
        'description': 'Downloads media using the specified resource name.',
        'parameters': {
            'type': 'object',
            'properties': {
                'resourceName': {
                    'type': 'string',
                    'description': "Name of the media to download.\nSee ReadRequest.resource_name."
                }
            },
            'required': [
                'resourceName'
            ]
        }
    }
)
def download(resourceName: str) -> Dict[str, Union[Dict, str]]:
    """
    Downloads media using the specified resource name.

    Args:
        resourceName (str): Name of the media to download.
            See ReadRequest.resource_name.

    Returns:
        Dict[str, Union[Dict, str]]: A dictionary containing the downloaded attachment metadata with keys:
            - name (str): The resource name of the attachment.
            - contentName (str): Original filename of the attachment.
            - contentType (str): MIME type of the attachment.
            - attachmentDataRef (Dict): Reference to attachment data.
            - driveDataRef (Dict): Reference to Google Drive data if applicable.
            - thumbnailUri (str): URI for thumbnail image.
            - downloadUri (str): URI for downloading the content.
            - source (str): Source of the attachment (e.g., "UPLOADED_CONTENT").

    Raises:
        TypeError: If resourceName is not a string.
        ValueError: If resourceName is empty, None, or has invalid format.
        FileNotFoundError: If the specified attachment resource is not found in the database.
    """
    # Input validation
    if not isinstance(resourceName, str):
        raise TypeError("resourceName must be a string.")
    
    if not resourceName or not resourceName.strip():
        raise ValueError("resourceName cannot be empty or None.")
    
    resourceName = resourceName.strip()
    
    # Validate resource name format
    # Support both direct attachment paths and message attachment paths
    attachment_pattern = r'^spaces/[^/]+/attachments/[^/]+$'
    message_attachment_pattern = r'^spaces/[^/]+/messages/[^/]+/attachments/[^/]+$'
    
    if not (re.match(attachment_pattern, resourceName) or 
            re.match(message_attachment_pattern, resourceName)):
        raise ValueError(
            f"Invalid resourceName format: '{resourceName}'. "
            "Expected format: 'spaces/{{space}}/attachments/{{attachment}}' or "
            "'spaces/{{space}}/messages/{{message}}/attachments/{{attachment}}'."
        )
    
    # Initialize database if needed
    if "Attachment" not in DB:
        DB["Attachment"] = []
    
    # Search for the attachment in the database
    for attachment in DB["Attachment"]:
        if attachment.get("name") == resourceName:
            print(f"Successfully downloaded media: {resourceName}")
            return attachment.copy()  # Return a copy to prevent external modifications
    
    # Attachment not found
    raise FileNotFoundError(
        f"Attachment with resource name '{resourceName}' not found. "
        "Please verify the resource name is correct and the attachment exists."
    )


@tool_spec(
    spec={
        'name': 'upload_media',
        'description': 'Uploads an attachment to the specified Chat space.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': 'Required. Resource name of the Chat space in which the attachment is uploaded. Format "spaces/{space}".'
                },
                'attachment_request': {
                    'type': 'object',
                    'description': 'A dictionary representing the metadata for the attachment being uploaded.:',
                    'properties': {
                        'contentName': {
                            'type': 'string',
                            'description': 'The original filename of the attachment.'
                        },
                        'contentType': {
                            'type': 'string',
                            'description': 'The MIME type of the attachment.'
                        }
                    },
                    'required': [
                        'contentName',
                        'contentType'
                    ]
                }
            },
            'required': [
                'parent',
                'attachment_request'
            ]
        }
    }
)
def upload(parent: str, attachment_request: Dict[str, Union[str, str]]) -> Dict[str, Union[str, Dict]]:
    """
    Uploads an attachment to the specified Chat space.

    Args:
        parent (str): Required. Resource name of the Chat space in which the attachment is uploaded. Format "spaces/{space}".
        attachment_request (Dict[str, Union[str, str]]): A dictionary representing the metadata for the attachment being uploaded.:
            - contentName (str): The original filename of the attachment.
            - contentType (str): The MIME type of the attachment.

    Returns:
        Dict[str, Union[str, Dict]]: A dictionary containing references to the uploaded attachment.
            - name (str): Resource name of the attachment
            - contentName (str): Original filename of the content
            - contentType (str): MIME type of the file
            - attachmentDataRef (Dict): Empty dictionary for attachment data reference. It contains no keys.
            - driveDataRef (Dict): Empty dictionary for drive data reference. It contains no keys.
            - thumbnailUri (str): Empty string for thumbnail URI
            - downloadUri (str): Empty string for download URI
            - source (str): Source type, always "UPLOADED_CONTENT"

    Raises:
        TypeError: If 'parent' is not a string or 'attachment_request' is not a dictionary.
        ValueError: If 'parent' is an empty string.
        pydantic.ValidationError: If 'attachment_request' is not a valid dictionary.
        InvalidParentFormatError: If 'parent' does not follow the required format "spaces/{space}".
    """
    # --- Input Validation ---
    try:
        UploadArguments(parent=parent, attachment_request=attachment_request)
    except ValidationError as e:
        # Pydantic wraps the original exception. We extract and re-raise it.
        original_error = e.errors()[0]
        if 'ctx' in original_error and 'error' in original_error['ctx']:
            raise original_error['ctx']['error']
        
        # Handle Pydantic's internal validation errors
        field = original_error['loc'][0]
        if 'string' in original_error['type']:
            raise TypeError(f"{field} must be a string")
        if 'dict' in original_error['type']:
            raise TypeError(f"{field} must be a dictionary")
        
        raise e  # Re-raise original for any other validation error

    # --- End Input Validation ---

    # Validate attachment_request using Pydantic model
    validated_request = AttachmentRequestModel(**attachment_request)
    

    # Generate a new attachment ID based on the current count in DB["Attachment"]
    new_id = str(len(DB.get("Attachment", [])) + 1)
    resource_name = f"{parent}/attachments/{new_id}"

    # Build the new attachment object based on the schema.
    attachment = {
        "name": resource_name,
        "contentName": validated_request.contentName,
        "contentType": validated_request.contentType,
        "attachmentDataRef": {},
        "driveDataRef": {},
        "thumbnailUri": "",
        "downloadUri": "",
        "source": "UPLOADED_CONTENT",
    }

    # Ensure DB["Attachment"] exists.
    if "Attachment" not in DB:
        DB["Attachment"] = []
    DB["Attachment"].append(attachment)
    return attachment
