"""
This module provides functionality for managing attachments in the Workday Strategic Sourcing system.
It supports operations for creating, retrieving, updating, and deleting attachments using both
internal IDs and external IDs.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any, Optional, Union
from .SimulationEngine import db
from .SimulationEngine import models
from .SimulationEngine.custom_errors import NotFoundError
from .SimulationEngine import custom_errors
from .SimulationEngine.custom_errors import DuplicateExternalIdError
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.models import AttachmentInput

@tool_spec(
    spec={
        'name': 'list_attachments_by_ids',
        'description': """ Retrieve a filtered list of attachments based on specified IDs.
        
        This function returns a list of attachments matching the provided IDs, with a maximum
        limit of 50 attachments per request. The result is limited to 50 attachments regardless of the number of IDs provided. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter_id_equals': {
                    'type': 'string',
                    'description': 'Comma-separated string of attachment IDs to filter by.'
                }
            },
            'required': [
                'filter_id_equals'
            ]
        }
    }
)
def get(filter_id_equals: str) -> List[Dict[str, Any]]:
    """
    Retrieve a filtered list of attachments based on specified IDs.

    This function returns a list of attachments matching the provided IDs, with a maximum
    limit of 50 attachments per request. The result is limited to 50 attachments regardless of the number of IDs provided.

    Args:
        filter_id_equals (str): Comma-separated string of attachment IDs to filter by.

    Returns:
        List[Dict[str, Any]]: A list of attachment dictionaries, where each attachment contains:
            - id (int): Attachment identifier string.
            - name (str): Attachment file name.
            - type (str): Object type, should always be attachments.
            - uploaded_by (str): Email or Identifier of the uploader.
            - external_id (str): Attachment external identifier.
            - attributes (dict): Attachment attributes. May contain the following keys:
                - title (str): Attachment title.
                - size (str): Attachment file size in bytes.
                - external_id (str): Attachment external identifier.
                - download_url (str): Attachment download URL.
                - download_url_expires_at (datetime): Download URL expiration time.
                - uploaded_at (datetime): Time of upload.
            - Any other attachment-specific attributes as defined in the system.

    Raises:
        InvalidInputError: If 'filter_id_equals' is not a string.
    """
    # 1. Validate that the input is a string
    if not isinstance(filter_id_equals, str):
        raise custom_errors.InvalidInputError(
            "Filter input must be a string. Received a non-string value."
        )

    if not filter_id_equals.strip():
        return []

    # 3. Split the input string into a list of valid, non-empty IDs.
    #    This handles cases with empty items like "id1,,id2" by skipping them.
    validated_ids = [
        item.strip() for item in filter_id_equals.split(',') if item.strip()
    ]

    # 4. Main logic with robust data access and filtering
    result = []
    # Use .get() to safely access the attachments dictionary, preventing a KeyError
    for attachment_id, attachment in db.DB.get("attachments", {}).items():
        if str(attachment_id) in validated_ids:
            result.append(attachment)
        # Enforce the 50-item limit
        if len(result) >= 50:
            break
            
    return result

@tool_spec(
    spec={
        'name': 'create_attachment',
        'description': """ Create a new attachment in the system.
        
        This function creates a new attachment with the provided data. It checks for duplicate
        external IDs and generates a new unique internal ID for the attachment. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'data': {
                    'type': 'object',
                    'description': 'A dictionary representing the properties of a new attachment. :',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be attachments.'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Attachment file name.'
                        },
                        'uploaded_by': {
                            'type': 'string',
                            'description': 'Email/identifier of uploader'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'Attachment external identifier. Maximum length is 255 characters.'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Attachment attributes which may contain any of the following keys:',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'Attachment title. Maximum length is 255 characters.'
                                },
                                'size': {
                                    'type': 'string',
                                    'description': 'Attachment file size in bytes.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Attachment external identifier. Maximum length is 255 characters.'
                                },
                                'download_url': {
                                    'type': 'string',
                                    'description': 'Attachment download URL.'
                                },
                                'download_url_expires_at': {
                                    'type': 'string',
                                    'description': 'Download URL expiration timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).'
                                },
                                'uploaded_at': {
                                    'type': 'string',
                                    'description': 'Upload timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).'
                                }
                            },
                            'required': []
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'One of Contract, Event, Project, or Supplier Company containing:',
                            'properties': {
                                'type': {
                                    'type': 'string',
                                    'description': 'Object type.'
                                },
                                'id': {
                                    'type': 'string',
                                    'description': 'Object identifier string.'
                                }
                            },
                            'required': [
                                'type',
                                'id'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'name'
                    ]
                }
            },
            'required': [
                'data'
            ]
        }
    }
)
def post(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new attachment in the system.

    This function creates a new attachment with the provided data. It checks for duplicate
    external IDs and generates a new unique internal ID for the attachment.

    Args:
        data (Dict[str, Any]): A dictionary representing the properties of a new attachment. :
            - type (str, required): Object type, should always be attachments.
            - name (str, required): Attachment file name.
            - uploaded_by (Optional[str]): Email/identifier of uploader
            - external_id (Optional[str]): Attachment external identifier. Maximum length is 255 characters.
            - attributes (Optional[Dict[str, Any]]): Attachment attributes which may contain any of the following keys:
                - title (Optional[str]): Attachment title. Maximum length is 255 characters.
                - size (Optional[str]): Attachment file size in bytes.
                - external_id (Optional[str]): Attachment external identifier. Maximum length is 255 characters.
                - download_url (Optional[str]): Attachment download URL.
                - download_url_expires_at (Optional[str]): Download URL expiration timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
                - uploaded_at (Optional[str]): Upload timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
            - relationships (Optional[Dict[str, Any]]): One of Contract, Event, Project, or Supplier Company containing:
                - type (str): Object type.
                - id (str): Object identifier string.

    Returns:
        Dict[str, Any]: A dictionary containing the attachment data.
            - If an attachment with the provided external_id already exists, returns a dictionary with:
                - "error" (str): "Attachment with this external_id already exists."
            - On successful creation, returns a dictionary with the following keys:
                - "id" (int): Auto-generated unique identifier for the attachment
                - "type" (str): Object type, should be "attachments"
                - "name" (str): Attachment file name
                - "uploaded_by" (str): Email/identifier of uploader
                - "external_id" (str): Attachment external identifier.
                - "attributes" (dict): Attachment attributes. May contain any of the following keys:
                    - title (str): Title (max 255 chars)
                    - size (str): File size in bytes
                    - external_id (str): External identifier (max 255 chars)
                    - download_url (str): Download URL
                    - download_url_expires_at (datetime): URL expiration time
                    - uploaded_at (datetime): Upload timestamp
                - Any other attachment-specific attributes as defined.
    Raises:
        PydanticValidationError: If the input data fails validation against the `AttachmentInput` model
                         (e.g., missing required fields, wrong data types, etc.).
        DuplicateExternalIdError: If an attachment with the provided `external_id` already exists.
        ValueError: If a non-integer key is found in the database during ID generation,
                    indicating data corruption.
    """
    try:
        # 1. Validate input data using the Pydantic model. This now handles all
        #    structural validation for the simplified relationship object.
        attachment_data = AttachmentInput.model_validate(data)
    except PydanticValidationError as e:
        # Re-raise Pydantic's validation error to be handled by a higher-level error handler
        raise e

    # 2. Check for duplicate external_id
    if attachment_data.external_id and any(
        att.get("external_id") == attachment_data.external_id 
        for att in db.DB["attachments"].values()
    ):
        raise DuplicateExternalIdError(
            f"Attachment with external_id '{attachment_data.external_id}' already exists."
        )

    # 3. Generate a new, unique internal ID robustly
    try:
        max_id = max([0] + [int(k) for k in db.DB["attachments"].keys()])
        attachment_id = max_id + 1
    except (ValueError, TypeError) as e:
        raise ValueError(f"Could not generate a new attachment ID due to corrupted data in DB: {e}")

    # 4. Prepare and save the new attachment data
    # Convert the Pydantic model to a dictionary for storing in the mock DB
    new_attachment = attachment_data.model_dump(by_alias=True)
    new_attachment["id"] = attachment_id
    
    db.DB["attachments"][str(attachment_id)] = new_attachment
    
    return new_attachment

@tool_spec(
    spec={
        'name': 'list_all_attachments_with_filter',
        'description': """ Returns a filtered list of attachments based on the `filter[id_equals]` param.
        
        The result is limited to 50 attachments. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter_id_equals': {
                    'type': 'string',
                    'description': """ Comma-separated string of attachment IDs to filter by. Defaults to None.
                    If None, all attachments are returned (up to the limit). """
                }
            },
            'required': []
        }
    }
)
def list_attachments(filter_id_equals: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns a filtered list of attachments based on the `filter[id_equals]` param.
    The result is limited to 50 attachments.

    Args:
        filter_id_equals (Optional[str]): Comma-separated string of attachment IDs to filter by. Defaults to None.
            If None, all attachments are returned (up to the limit).

    Returns:
        Dict[str, Any]: A dictionary containing:
            - data (List[Dict[str, Any]]): List of attachment objects containing any of the following keys:
                - id (int): Identifier for the attachment
                - type (str): Object type, should be "attachments"
                - name (str): Attachment file name
                - uploaded_by (str): Email/identifier of uploader
                - external_id (str): Attachment external identifier.
                - attributes (dict): Attachment attributes containing any of the following keys:
                    - title (str): Title (max 255 chars)
                    - size (str): File size in bytes
                    - external_id (str): External identifier (max 255 chars)
                    - download_url (str): Download URL
                    - download_url_expires_at (datetime): URL expiration time
                    - uploaded_at (datetime): Upload timestamp
                - Any other attachment-specific attributes as defined in the system.
            - links (Dict[str, str]): Resource links
            - meta (Dict[str, int]): Metadata containing the total count of the results

    Note:
        The result is limited to 50 attachments per request.
    """
    # Input validation
    if filter_id_equals is not None and not isinstance(filter_id_equals, str):
        raise custom_errors.ValidationError("filter_id_equals must be a string")
    if filter_id_equals is not None and not filter_id_equals:
        raise custom_errors.ValidationError("filter_id_equals must be a non-empty string")
    if filter_id_equals is not None and not filter_id_equals.strip():
        raise custom_errors.ValidationError("filter_id_equals cannot contain only whitespace")
    
    attachments = list(db.DB["attachments"].values())
    if filter_id_equals:
        ids = filter_id_equals.split(",")
        attachments = [
            attachment
            for attachment in attachments
            if str(attachment.get("id")) in ids
        ]
    return {
        "data": attachments[:50],
        "links": {
            "self": "services/attachments/v1/attachments"
        },
        "meta": {"count": len(attachments[:50])},
    }

@tool_spec(
    spec={
        'name': 'get_attachment_by_id',
        'description': """ Retrieve a specific attachment by its internal ID.
        
        This function retrieves an attachment by its internal ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal ID of the attachment to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_attachment_by_id(id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific attachment by its internal ID.

    This function retrieves an attachment by its internal ID.

    Args:
        id (int): The internal ID of the attachment to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The attachment object if found.
            The object contains any of the following keys:
                - "id" (int): Identifier for the attachment
                - "type" (Optional[str]): Object type, should be "attachments"
                - "name" (Optional[str]): Attachment file name
                - "uploaded_by" (Optional[str]): Email/identifier of uploader
                - "external_id" (Optional[str]): Attachment external identifier.
                - "attributes" (Optional[Dict[str, Any]]): Attachment attributes containing any of the following keys:
                    - title (Optional[str]): Title (max 255 chars)
                    - size (Optional[str]): File size in bytes
                    - external_id (Optional[str]): External identifier (max 255 chars)
                    - download_url (Optional[str]): Download URL
                    - download_url_expires_at (Optional[datetime]): URL expiration time
                    - uploaded_at (Optional[datetime]): Upload timestamp
    
    Raises:
        ValueError: If the id is not an integer or is not a positive integer.
        NotFoundError: If the attachment is not found.
    """
    # Input Validation
    if not isinstance(id, int):
        raise ValueError("id must be an integer")
    if id <= 0:
        raise ValueError("id must be a positive integer")
    
    # Get the attachment
    if str(id) not in db.DB["attachments"]:
        raise NotFoundError(f"Attachment with id {id} not found")
        
    return db.DB["attachments"][str(id)]

@tool_spec(
    spec={
        'name': 'update_attachment_by_id',
        'description': """ Update an existing attachment by its internal ID.
        
        This function updates an existing attachment by its internal ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal ID of the attachment to update.'
                },
                'data': {
                    'type': 'object',
                    'description': 'Dictionary containing the fields to update with their new values. Possible keys:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "attachments".'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Attachment identifier string.'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Attachment attributes.',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'Attachment title. Max 255 characters.'
                                },
                                'file_name': {
                                    'type': 'string',
                                    'description': 'Attachment file name.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Attachment external identifier. Max 255 characters.'
                                }
                            },
                            'required': [
                                'title',
                                'external_id'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'id'
                    ]
                }
            },
            'required': [
                'id',
                'data'
            ]
        }
    }
)
def patch_attachment_by_id(id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update an existing attachment by its internal ID.

    This function updates an existing attachment by its internal ID.

    Args:
        id (int): The internal ID of the attachment to update.
        data (Dict[str, Any]): Dictionary containing the fields to update with their new values. Possible keys:
            - type (str): Object type, should always be "attachments".
            - id (int): Attachment identifier string.
            - attributes (Optional[dict]): Attachment attributes.
                - title (str): Attachment title. Max 255 characters.
                - file_name (Optional[str]): Attachment file name.
                - external_id (str): Attachment external identifier. Max 255 characters.


    Returns:
        Optional[Dict[str, Any]]: The updated attachment object if found and updated.
        The object contains any of the following keys:
            - id (int): Identifier for the attachment
            - type (Optional[str]): Object type, should be "attachments"
            - name (Optional[str]): Attachment file name
            - uploaded_by (Optional[str]): Email/identifier of uploader
            - external_id (Optional[str]): Attachment external identifier.
            - attributes (Optional[Dict[Any, Any]]): Attachment attributes. May contain any of the following keys:
                - title (Optional[str]): Title (max 255 chars)
                - size (Optional[str]): File size in bytes
                - external_id (Optional[str]): External identifier (max 255 chars)
                - download_url (Optional[str]): Download URL
                - download_url_expires_at (Optional[datetime]): URL expiration time
                - uploaded_at (Optional[datetime]): Upload timestamp
    
    Raises:
        ValueError: If the id is not an integer or is not a positive integer.
        NotFoundError: If the attachment is not found.
    """
    # Input Validation
    if not isinstance(id, int):
        raise ValueError("id must be an integer")
    if id <= 0:
        raise ValueError("id must be a positive integer")
    if not isinstance(data, dict):
        raise ValueError("Input 'data' must be a dictionary.")
    try:
        models.AttachmentModel(**data)
    except:
        raise ValueError(f"Input 'data' is invalid.")
    
    # Update the attachment
    if str(id) not in db.DB["attachments"]:
        raise NotFoundError(f"Attachment with id {id} not found")
    
    db.DB["attachments"][str(id)].update(data)
    db.DB["attachments"][str(id)]["id"] = id
    return db.DB["attachments"][str(id)]

@tool_spec(
    spec={
        'name': 'delete_attachment_by_id',
        'description': """ Delete an attachment by its internal ID.
        
        This function deletes the attachment from the database. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal ID of the attachment to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete_attachment_by_id(id: int) -> bool:
    """
    Delete an attachment by its internal ID.

    This function deletes the attachment from the database.

    Args:
        id (int): The internal ID of the attachment to delete.

    Returns:
        bool: True if the attachment was successfully deleted.
    
    Raises:
        ValueError: If the id is not an integer.
        NotFoundError: If the attachment does not exist.
    """
    # Input Validation
    if not isinstance(id, int):
        raise ValueError("id must be an integer")
    if id <= 0:
        raise ValueError("id must be a positive integer")
    
    # Delete the attachment
    if str(id) not in db.DB["attachments"]:
        raise NotFoundError(f"Attachment with id {id} not found")
        
    del db.DB["attachments"][str(id)]
    return True

@tool_spec(
    spec={
        'name': 'get_attachment_by_external_id',
        'description': """ Retrieve a specific attachment by its external ID.
        
        This function retrieves the attachment from the database by its external ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external ID of the attachment to retrieve.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get_attachment_by_external_id(external_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific attachment by its external ID.

    This function retrieves the attachment from the database by its external ID.

    Args:
        external_id (str): The external ID of the attachment to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The attachment object if found.
            The object contains any of the following keys:
                - id (Optional[int]): Identifier for the attachment
                - type (Optional[str]): Object type, should be "attachments"
                - name (Optional[str]): Attachment file name
                - uploaded_by (Optional[str]): Email/identifier of uploader
                - attributes (Optional[Dict[Any, Any]]): Attachment attributes. May contain any of the following keys:
                    - title (Optional[str]): Title (max 255 chars)
                    - size (Optional[str]): File size in bytes
                    - external_id (Optional[str]): External identifier (max 255 chars)
                    - download_url (Optional[str]): Download URL
                    - download_url_expires_at (Optional[datetime]): URL expiration time
                    - uploaded_at (Optional[datetime]): Upload timestamp

    Raises:
        ValueError: If the external_id is not a string or if multiple attachments are found with the same external_id.
        NotFoundError: If the attachment does not exist.
    """
    # Input Validation
    if not isinstance(external_id, str):
        raise ValueError("external_id must be a string")
    
    # Retrieve the attachment
    attachments = [attachment for attachment in db.DB["attachments"].values() if attachment.get("external_id") == external_id]
    if len(attachments) == 0:
        raise NotFoundError(f"Attachment with external_id {external_id} not found")
    if len(attachments) > 1:
        raise ValueError(f"Multiple attachments found with external_id {external_id}")
    return attachments[0]

@tool_spec(
    spec={
        'name': 'update_attachment_by_external_id',
        'description': 'Update an existing attachment by its external ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external ID of the attachment to update.'
                },
                'data': {
                    'type': 'object',
                    'description': 'Dictionary containing the fields to update with their new values. Possible keys:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "attachments".'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Attachment identifier string.'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Attachment attributes.',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'Attachment title. Max 255 characters.'
                                },
                                'file_name': {
                                    'type': 'string',
                                    'description': 'Attachment file name.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Attachment external identifier. Max 255 characters.'
                                }
                            },
                            'required': [
                                'title',
                                'external_id'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'id'
                    ]
                }
            },
            'required': [
                'external_id',
                'data'
            ]
        }
    }
)
def patch_attachment_by_external_id(external_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update an existing attachment by its external ID.

    Args:
        external_id (str): The external ID of the attachment to update.
        data (Dict[str, Any]): Dictionary containing the fields to update with their new values. Possible keys:
            - type (str): Object type, should always be "attachments".
            - id (int): Attachment identifier string.
            - attributes (Optional[dict]): Attachment attributes.
                - title (str): Attachment title. Max 255 characters.
                - file_name (Optional[str]): Attachment file name.
                - external_id (str): Attachment external identifier. Max 255 characters.

    Returns:
        Optional[Dict[str, Any]]: The updated attachment object if found and updated,
            None if the attachment does not exist.
            The object contains any of the following keys:
                - "id" (int): Identifier for the attachment
                - "type" (str): Object type, should be "attachments"
                - "name" (str): Attachment file name
                - "uploaded_by" (str): Email/identifier of uploader
                - external_id (str): Attachment external identifier.
                - "attributes" (dict): Attachment attributes. May contain any of the following keys:
                    - title (str): Title (max 255 chars)
                    - size (str): File size in bytes
                    - external_id (str): External identifier (max 255 chars)
                    - download_url (str): Download URL
                    - download_url_expires_at (datetime): URL expiration time
                    - uploaded_at (datetime): Upload timestamp
                - Any other attachment-specific attributes as defined in the system.

    Note:
        The external_id field in the data dictionary will be ignored and replaced with
        the provided external_id.
    """
    for attachment_id, attachment in db.DB["attachments"].items():
        if attachment.get("external_id") == external_id:
            db.DB["attachments"][attachment_id].update(data)
            db.DB["attachments"][attachment_id]["external_id"] = external_id
            return db.DB["attachments"][attachment_id]
    return None

@tool_spec(
    spec={
        'name': 'delete_attachment_by_external_id',
        'description': """ Delete an attachment by its external ID.
        
        This function deletes the attachment from the database by its external ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external ID of the attachment to delete.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete_attachment_by_external_id(external_id: str) -> bool:
    """
    Delete an attachment by its external ID.

    This function deletes the attachment from the database by its external ID.

    Args:
        external_id (str): The external ID of the attachment to delete.

    Returns:
        bool: True if the attachment was successfully deleted.
    
    Raises:
        ValueError: If the external_id is not a string.
        NotFoundError: If the attachment does not exist.
    """
    # Input Validation
    if not isinstance(external_id, str):
        raise ValueError("external_id must be a string")
    
    # Delete the attachment
    attachments = [(attachment_id, attachment) for attachment_id, attachment in db.DB["attachments"].items() if attachment.get("external_id") == external_id]
    if len(attachments) == 0:
        raise NotFoundError(f"Attachment with external_id {external_id} not found")
    if len(attachments) > 1:
        raise ValueError(f"Multiple attachments found with external_id {external_id}")

    attachment_id, _ = attachments[0]
    del db.DB["attachments"][attachment_id]
    return True
