from common_utils.tool_spec_decorator import tool_spec 
from typing import Dict, List, Optional, Any, TypedDict, Set
from .SimulationEngine.custom_errors import ContentNotFoundError, ContentStatusMismatchError, \
    InvalidInputError, FileAttachmentError, LabelNotFoundError, ValidationError, \
    MissingCommentAncestorsError, AncestorContentNotFoundError, SpaceNotFoundError, \
    MissingTitleForPageError
from .SimulationEngine.models import UpdateContentBodyInputModel
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.utils import get_iso_timestamp
from .SimulationEngine.custom_errors import InvalidPaginationValueError, InvalidParameterValueError, InvalidPaginationValueError, AncestorContentNotFoundError

from .SimulationEngine.db import DB
from .SimulationEngine.models import ContentInputModel
from .SimulationEngine.utils import _evaluate_cql_tree, _collect_descendants, _preprocess_cql_functions, cascade_delete_content_data
import re
import copy
import os
from datetime import datetime, timezone

@tool_spec(
    spec={
        'name': 'create_content',
        'description': """ Creates new content.
        
        This function creates a new content item (page, blogpost, comment, etc.) with the specified
        details and stores it in the database. It handles both basic content creation and special
        cases like comments with ancestor relationships. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': 'The complete specification for the new content item to be created, containing all necessary properties like type, title, and space key.',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': "Content type (e.g., 'page', 'blogpost', 'comment')"
                        },
                        'title': {
                            'type': 'string',
                            'description': 'Content title'
                        },
                        'spaceKey': {
                            'type': 'string',
                            'description': 'Space key where content will be created'
                        },
                        'status': {
                            'type': 'string',
                            'description': "Content status (default: 'current'). It must be one of the following values: 'current', 'draft', 'archived', 'trashed'."
                        },
                        'version': {
                            'type': 'object',
                            'description': "Content version object with 'number' and 'minorEdit' keys",
                            'properties': {
                                'number': {
                                    'type': 'integer',
                                    'description': 'Version number (default: 1)'
                                },
                                'minorEdit': {
                                    'type': 'boolean',
                                    'description': 'Flag indicating a minor edit (default: False)'
                                }
                            },
                            'required': [
                                'number',
                                'minorEdit'
                            ]
                        },
                        'body': {
                            'type': 'object',
                            'description': 'Content body with storage format, structured as:',
                            'properties': {
                                'storage': {
                                    'type': 'object',
                                    'description': "An object representing the storage format, containing the content's value and representation type:",
                                    'properties': {
                                        'value': {
                                            'type': 'string',
                                            'description': 'The content value in storage format.'
                                        },
                                        'representation': {
                                            'type': 'string',
                                            'description': 'The representation type (e.g., "storage")'
                                        }
                                    },
                                    'required': [
                                        'value',
                                        'representation'
                                    ]
                                }
                            },
                            'required': [
                                'storage'
                            ]
                        },
                        'postingDay': {
                            'type': 'string',
                            'description': 'Posting day for blog posts in "YYYY-MM-DD" format. Required when type is \'blogpost\'. For other content types, this field is optional and will be ignored if provided.'
                        },
                        'ancestors': {
                            'type': 'array',
                            'description': "List of ancestor content IDs. Required (must be a non-empty list) when type is 'comment'. For other content types, this field is optional and will be ignored if provided.",
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': [
                        'type',
                        'title',
                        'spaceKey'
                    ]
                }
            },
            'required': [
                'body'
            ]
        }
    }
)
def create_content(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates new content.

    This function creates a new content item (page, blogpost, comment, etc.) with the specified
    details and stores it in the database. It handles both basic content creation and special
    cases like comments with ancestor relationships.

    Args:
        body (Dict[str, Any]): The complete specification for the new content item to be created, containing all necessary properties like type, title, and space key.
                - type (str): Content type (e.g., 'page', 'blogpost', 'comment')
                - title (str): Content title
                - spaceKey (str): Space key where content will be created
                - status (Optional[str]): Content status (default: 'current'). It must be one of the following values: 'current', 'draft', 'archived', 'trashed'.
                - version (Optional[Dict]): Content version object with 'number' and 'minorEdit' keys
                    - number (int): Version number (default: 1)
                    - minorEdit (bool): Flag indicating a minor edit (default: False)
                - body (Optional[Dict]): Content body with storage format, structured as:
                      - storage (Dict): An object representing the storage format, containing the content's value and representation type:
                            - value (str): The content value in storage format.
                            - representation (str): The representation type (e.g., "storage")
                - postingDay (Optional[str]): Posting day for blog posts in "YYYY-MM-DD" format. Required when type is 'blogpost'. For other content types, this field is optional and will be ignored if provided.
                - ancestors (Optional[List[str]]): List of ancestor content IDs. Required (must be a non-empty list) when type is 'comment'. For other content types, this field is optional and will be ignored if provided.

    Returns:
        Dict[str, Any]: A dictionary containing the created content details with keys:
            - id (str): Unique identifier for the content.
            - type (str): Content type ('page', 'blogpost', 'comment', 'attachment').
            - title (str): Content title.
            - spaceKey (str): Space key.
            - status (str): Content status ('current', 'draft', 'archived', 'trashed').
            - body (Dict[str, Any]): Content body with storage format:
                - storage (Dict[str, str]): Storage format object containing:
                    - value (str): The content value in storage format.
                    - representation (str): The representation type (e.g., "storage").
            - version (Dict[str, Any]): Version information:
                - number (int): Version number (always 1 for new content).
                - minorEdit (bool): Minor edit flag (always False for new content).
            - history (Dict[str, Any]): History information:
                - latest (bool): Whether this is the latest version.
                - createdBy (Dict[str, str]): Creator information:
                    - type (str): User type ('known').
                    - username (str): Username of the creator.
                    - displayName (str): Display name of the creator.
                - createdDate (str): ISO 8601 timestamp when the content was created.
            - ancestors (Optional[List[Dict[str, str]]]): List of ancestor objects (only for comments):
                - Each ancestor contains:
                    - id (str): ID of the parent content item.
            - postingDay (Optional[str]): Posting day for blog posts (only if provided).
            - _links (Dict[str, str]): API navigation links:
                - self (str): Self-reference URL for the content.

    Raises:
        ValidationError: If the input body dictionary does not conform to the expected structure
                        (missing required fields, invalid types, invalid enum values)
        SpaceNotFoundError: If the specified space key does not exist in the database
        MissingCommentAncestorsError: If type is 'comment' and ancestors list is missing or empty
        AncestorContentNotFoundError: If a parent content ID specified in ancestors for a comment
                                    is not found in the database
    """
    # Use Pydantic validation for input structure
    try:
        validated_body = ContentInputModel(**body)
    except Exception as e:
        raise ValidationError(f"Invalid request body: {str(e)}")
    
    # Extract validated fields
    content_type = validated_body.type.value  # Get string value from enum
    title = validated_body.title
    space_key = validated_body.effective_space_key

    # Validate that the spaceKey exists in the database
    if space_key not in DB["spaces"]:
        raise SpaceNotFoundError(f"Space with key='{space_key}' not found")

    # Generate new ID
    new_id = str(DB["content_counter"])
    DB["content_counter"] += 1

    # Get current timestamp
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # Build content structure following official API
    new_content = {
        "id": new_id,
        "type": content_type,
        "title": title,
        "spaceKey": space_key,
        "status": validated_body.status.value,
        "body": validated_body.body.model_dump(mode="json") if validated_body.body else {
            "storage": {
                "value": "",
                "representation": "storage"
            }
        },
        "version": {
            "number": 1,
            "minorEdit": False
        },
        "history": {
            "latest": True,
            "createdBy": {
                "type": "known",
                "username": "system",
                "displayName": "System User"
            },
            "createdDate": current_time
        },
        "_links": {
            "self": f"/wiki/rest/api/content/{new_id}"
        }
    }
    
    # Add postingDay for blog posts if provided
    if content_type == "blogpost" and validated_body.postingDay:
        new_content["postingDay"] = validated_body.postingDay

    # Handle ancestors for comments (following official API specification)
    if content_type == "comment":
        ancestors_input = validated_body.ancestors or []
        if not ancestors_input:
            raise MissingCommentAncestorsError("For content type 'comment', ancestors are required")
        
        # Validate that all ancestor IDs exist in the database
        validated_ancestors = []
        for ancestor_id in ancestors_input:
            if not isinstance(ancestor_id, str):
                raise ValidationError("Ancestor ID must be a string")
            
            ancestor_content = DB["contents"].get(ancestor_id)
            if not ancestor_content:
                raise AncestorContentNotFoundError(f"Ancestor content with ID '{ancestor_id}' not found")
            
            # Add to validated list
            validated_ancestors.append({"id": ancestor_id})
        
        # Store ancestor references
        new_content["ancestors"] = validated_ancestors

    # Save new content in DB
    DB["contents"][new_id] = new_content
    
    # Initialize content history tracking
    if "history" not in DB:
        DB["history"] = {}
    
    # Store initial history record
    DB["history"][new_id] = [{
        "version": 1,
        "when": current_time,
        "by": {
            "type": "known",
            "username": "system",
            "displayName": "System User"
        },
        "message": "Initial version",
        "minorEdit": False
    }]
    
    return new_content

@tool_spec(
    spec={
        'name': 'get_content_details',
        'description': """ Retrieves content by its unique identifier.
        
        This function fetches a content item from the database using its ID. It can optionally
        filter the content by its status to ensure the content matches the expected state. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content to retrieve. Must be a non-empty string.'
                },
                'status': {
                    'type': 'string',
                    'description': """ The expected status of the content. If provided,
                    the function will verify that the content's status matches this value.
                    If set to "any", the status check is bypassed. Must be a string if provided. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content(
        id: str,
        status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves content by its unique identifier.

    This function fetches a content item from the database using its ID. It can optionally
    filter the content by its status to ensure the content matches the expected state.

    Args:
        id (str): The unique identifier of the content to retrieve. Must be a non-empty string.
        status (Optional[str]): The expected status of the content. If provided,
            the function will verify that the content's status matches this value.
            If set to "any", the status check is bypassed. Must be a string if provided.

    Returns:
        Dict[str, Any]: A dictionary containing the content details with keys:
            - id (str): Content identifier.
            - type (str): Content type ('page', 'blogpost', 'comment', 'attachment').
            - title (str): Content title.
            - spaceKey (str): Internal space key.
            - status (str): Content status ('current', 'draft', 'archived', 'trashed').
            - version (Dict[str, Any]): Content version object:
                - number (int): Version number.
                - minorEdit (bool): Flag indicating a minor edit.
            - body (Dict[str, Any]): Content body with storage format:
                - storage (Dict[str, str]): Storage format object containing:
                    - value (str): The content value in storage format.
                    - representation (str): The representation type (e.g., "storage").
            - history (Dict[str, Any]): History information:
                - latest (bool): Whether this is the latest version.
                - createdBy (Dict[str, str]): Creator information:
                    - type (str): User type.
                    - username (str): Username of the creator.
                    - displayName (str): Display name of the creator.
                - createdDate (str): ISO 8601 timestamp when content was created.
            - ancestors (Optional[List[Dict[str, str]]]): List of ancestor objects (for comments):
                - Each ancestor contains:
                    - id (str): ID of the parent content item.
            - postingDay (Optional[str]): Posting day for blog posts (if applicable).
            - _links (Dict[str, str]): API navigation links:
                - self (str): Self-reference URL for the content.

    Raises:
        TypeError: If 'id' is not a string, or if 'status', 'version', or 'expand'
                   are provided but are not of their expected types (str, int, str respectively).
        InvalidInputError: If 'id' is an empty string.
        ContentNotFoundError: If the content with the specified ID is not found.
        ContentStatusMismatchError: If the content's status does not match the expected status.
    """
    # --- Input Validation ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    # Use trimmed ID for database lookup
    id = id.strip()

    if status is not None and not isinstance(status, str):
        raise TypeError("Argument 'status' must be a string if provided.")
    if status is not None and not status.strip():
        raise InvalidInputError("Argument 'status' cannot be an empty string if provided.")

    content = DB["contents"].get(id)
    if not content:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")

    if status and status != "any":  # "any" is a special value to bypass status check
        status = status.strip()
        current_content_status = content.get("status")
        if current_content_status != status:
            raise ContentStatusMismatchError(
                f"Content status mismatch for id='{id}'. Expected: '{status}', Actual: '{current_content_status}'."
            )
    
    return content


@tool_spec(
    spec={
        'name': 'update_content',
        'description': """ Updates existing content.
        
        This function updates an existing content item with new values.
        Versioning is managed automatically: the version is incremented by one (defaulting to 1 if no version is set).
        The update payload should not include a version object (any provided version data is ignored).
        
        Special behavior:
          - **Restoring a trashed page:**
            To restore content that is "trashed", the update request must set its status to "current". In that case,
            only the version is incremented and the status updated to "current". No other fields are modified.
          - **Deleting a draft:**
            If the update is intended to delete a draft (signaled by `query_status="draft"`), then the draft is removed and
            the content's body is replaced with the provided body. (Updating a draft is not supported.)
          - **Partial body updates:**
            When updating the body, if only 'value' is provided in body.storage, the existing 'representation' 
            is preserved. Both fields can be updated by providing both in the request. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'ID of the content to update.'
                },
                'body': {
                    'type': 'object',
                    'description': """ A payload with the fields to be updated for the content item.
                    All fields are optional - provide only the fields you need to update: """,
                    'properties': {
                        'title': {
                            'type': 'string',
                            'description': 'New content title.'
                        },
                        'status': {
                            'type': 'string',
                            'description': 'New content status.'
                        },
                        'body': {
                            'type': 'object',
                            'description': 'New content body object with:',
                            'properties': {
                                'storage': {
                                    'type': 'object',
                                    'description': 'Storage representation with:',
                                    'properties': {
                                        'value': {
                                            'type': 'string',
                                            'description': 'Markup content.'
                                        },
                                        'representation': {
                                            'type': 'string',
                                            'description': 'Markup type (e.g., "storage").'
                                        }
                                    },
                                    'required': [
                                        'value'
                                    ]
                                }
                            },
                            'required': [
                                'storage'
                            ]
                        },
                        'spaceKey': {
                            'type': 'string',
                            'description': 'New space key.'
                        },
                        'ancestors': {
                            'type': 'array',
                            'description': 'List of ancestor IDs.',
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'id',
                'body'
            ]
        }
    }
)
def update_content(id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates existing content.

    This function updates an existing content item with new values.
    Versioning is managed automatically: the version is incremented by one (defaulting to 1 if no version is set).
    The update payload should not include a version object (any provided version data is ignored).

    Special behavior:
      - **Restoring a trashed page:**
        To restore content that is "trashed", the update request must set its status to "current". In that case,
        only the version is incremented and the status updated to "current". No other fields are modified.
      - **Deleting a draft:**
        If the update is intended to delete a draft (signaled by `query_status="draft"`), then the draft is removed and
        the content's body is replaced with the provided body. (Updating a draft is not supported.)
      - **Partial body updates:**
        When updating the body, only the provided fields within body.storage are updated.
        For example, if only 'value' is provided, the existing 'representation' is preserved.

    Args:
        id (str): ID of the content to update.
        body (Dict[str, Any]): A payload with the fields to be updated for the content item.
            All fields are optional - provide only the fields you need to update:
            - title (str, optional): New content title.
            - status (str, optional): New content status.
            - body (Dict[str, Any], optional): New content body object with:
                - storage (Dict[str, Any], required if body is provided): Storage representation with:
                    - value (str, required): Markup content. This field is required if storage is provided.
                    - representation (str, optional): Markup type (e.g., "storage", "view", "editor").
                      If not provided, the existing representation value is preserved.
            - spaceKey (str, optional): New space key.
            - ancestors (List[str], optional): List of ancestor IDs.

    Returns:
        Dict[str, Any]: Updated content details with keys:
            - id (str): Unique identifier of the content.
            - type (str): Content type (e.g., "page", "blogpost", "comment").
            - title (str): Updated content title.
            - spaceKey (str): Space key.
            - status (str): Updated content status.
            - version (Dict[str, Any]): Version object containing:
                    - number (int): Updated version number.
                    - minorEdit (bool): Indicates if the update is a minor edit.
            - body (Dict[str, Any]): Updated content body.
            - link (str): Link to the content.

    Raises:
        TypeError: If `id` is not a string or `body` is not a dictionary.
        ValidationError: If the `body` argument does not conform to the expected structure.
                         This includes:
                         - Missing required field 'storage' when 'body' is provided
                         - Missing required field 'value' when 'storage' is provided
                         - Invalid types for fields like 'title', 'spaceKey', 'ancestors'
                         - Invalid status values (must be one of: 'current', 'archived', 'draft', 'trashed')
                         - Empty or whitespace-only strings for 'title' or 'spaceKey'
        ValueError: If the specified spaceKey does not exist in the database.
        ContentNotFoundError: If the content with the specified `id` doesn't exist.
        InvalidInputError: If `id` is an empty string or `body` is empty, or if validation fails for specific fields
                            or if the content is a draft and the status is not set to 'current' when updating it
                            or if the content is a trashed page and update request is not to set its status to 'current'.
    """
    # --- Input Validation Start ---
    if not isinstance(id, str):
        raise TypeError(f"Argument 'id' must be a string, got {type(id).__name__}.")
    
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")

    if not isinstance(body, dict):
        raise TypeError(f"Argument 'body' must be a dictionary, got {type(body).__name__}.")
    
    if not body:
        raise InvalidInputError("Argument 'body' cannot be an empty dictionary.")

    # Validate body structure using Pydantic model
    try:
        validated_body_model = UpdateContentBodyInputModel(**body).model_dump(mode="json")
    except PydanticValidationError as e:
        raise ValidationError(f"Input validation failed")
    # --- Input Validation End ---

    # Check if content exists
    content = DB["contents"].get(id)
    if not content:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")

    # Get current status and new status
    current_status = content.get("status", "")
    new_status = validated_body_model.get("status")
    
    # SPECIAL CASE 1: Restoring a trashed page
    # If content is trashed and status is being set to 'current', ONLY update status and version
    if current_status == "trashed" :
        if len(body.keys()) > 1 or new_status != "current":
            raise InvalidInputError("Cannot update other fields of a trashed page without setting its status to 'current' first.")
    
    # SPECIAL CASE 2: Deleting a draft
    # Check if this is a draft deletion (status is 'draft' in current content)
    if current_status == "draft" and new_status != "current":
        raise InvalidInputError("Drafts cannot be updated while remaining as drafts. To publish the draft, set status to 'current' in the update body.")
        
    # NORMAL UPDATE: Update all provided fields
    
    # Update status if provided
    if new_status:
        content["status"] = new_status

    # Update title if provided (validation done by Pydantic)
    if "title" in body:
        content["title"] = validated_body_model.get("title")

    # Update content body if provided (merge strategy: only update provided fields)
    if "body" in body:
        if "body" not in content:
            content["body"] = {}
        if "storage" not in content["body"]:
            content["body"]["storage"] = {}
        
        # Get the validated body from Pydantic
        validated_body = validated_body_model.get("body")
        
        # Merge storage fields: only update what's provided in the request
        if validated_body and "storage" in validated_body:
            validated_storage = validated_body["storage"]
            
            # Always update value if provided (it's required by validation)
            if "value" in validated_storage:
                content["body"]["storage"]["value"] = validated_storage["value"]
            
            # Only update representation if explicitly provided in the original request
            if "representation" in body.get("body", {}).get("storage", {}):
                content["body"]["storage"]["representation"] = validated_storage["representation"]
            # Note: If representation is not provided, keep the existing value unchanged
    
    # Update space if provided
    if "spaceKey" in body:
        new_space_key = validated_body_model.get("spaceKey")
        if new_space_key:
            # Validate that the new spaceKey exists in the database
            if new_space_key not in DB["spaces"]:
                raise ValueError(f"Space with key='{new_space_key}' not found.")
            content["spaceKey"] = new_space_key
    
    # Update ancestors if provided (for comments)
    if "ancestors" in body:
        ancestors = validated_body_model.get("ancestors")
        if ancestors is not None:
            # Validate that all ancestor IDs exist in the database
            for ancestor_id in ancestors:
                if not DB["contents"].get(ancestor_id):
                    raise ContentNotFoundError(f"Ancestor content with id='{ancestor_id}' not found.")
            content["ancestors"] = ancestors

    # Update version number
    current_version = content.get("version", {}).get("number", 0)
    if "version" not in content:
        content["version"] = {}
    content["version"]["number"] = current_version + 1
    content["version"]["minorEdit"] = False

    # Update content history
    if "history" not in DB:
        DB["history"] = {}
    
    if id not in DB["history"]:
        DB["history"][id] = []
    
    # Get current timestamp for update
    update_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    # Add new history record
    DB["history"][id].append({
        "version": content["version"]["number"],
        "when": update_time,
        "by": {
            "type": "known",
            "username": "system",
            "displayName": "System User"
        },
        "message": "Content updated",
        "minorEdit": content["version"]["minorEdit"]
    })

    # Save updated content
    DB["contents"][id] = content
    content["link"] = content.get("_links", {}).get("self", "")
    if "_links" in content:
        del content["_links"]

    return content


@tool_spec(
    spec={
        'name': 'delete_content',
        'description': """ Deletes a content item from the system.
        
        This function provides the deletion of a content item based on its type and status,
        following these cases:
          1. If the status of the content is "current":
             The content is trashed by updating its status to "trashed"  (a soft delete).
          2. If the status of the content is "trashed", and the query parameter "status"
             is set to "trashed":
             The content is purged (permanently deleted) from the database.
          3. If the content is not trashable (historical, draft, archived):
             The content is immediately deleted permanently regardless of its status.
        
        When content is permanently deleted (cases 2 and 3), all associated data is also removed:
        - Content properties from DB["content_properties"]
        - Content labels from DB["content_labels"]
        - Content history from DB["history"] """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content to delete.'
                },
                'status': {
                    'type': 'string',
                    'description': """ The query parameter "status" from the request.
                    When set to "trashed" in the purge scenario, indicates that the content should be
                    permanently deleted. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete_content(id: str, status: Optional[str] = None) -> None:
    """
    Deletes a content item from the system.

    This function provides the deletion of a content item based on its type and status,
    following these cases:
      1. If the status of the content is "current":
         The content is trashed by updating its status to "trashed"  (a soft delete).
      2. If the status of the content is "trashed", and the query parameter "status"
         is set to "trashed":
         The content is purged (permanently deleted) from the database.
      3. If the content is not trashable (historical, draft, archived):
         The content is immediately deleted permanently regardless of its status.
    
    When content is permanently deleted (cases 2 and 3), all associated data is also removed:
    - Content properties from DB["content_properties"]
    - Content labels from DB["content_labels"]
    - Content history from DB["history"]

    Args:
        id (str): The unique identifier of the content to delete.
        status (Optional[str]): The query parameter "status" from the request.
            When set to "trashed" in the purge scenario, indicates that the content should be
            permanently deleted.

    Returns:
        None

    Raises:
        TypeError: If 'id' is not a string, or if 'status' is provided and is not a string.
        ValueError: If there is no content with the given id (propagated from core logic).
    """
    # Input Validation
    if not isinstance(id, str):
        raise TypeError(f"id must be a string, got {type(id).__name__}.")
    if status is not None and not isinstance(status, str):
        raise TypeError(f"status must be a string if provided, got {type(status).__name__}.")

    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id={id} not found.")

    if "status" not in content:
        raise ValueError(f"Content with id={id} does not have a status field.")
    current_status_in_db = content["status"]

    # Case 3: If the content is not trashable (historical, draft, archived) - delete immediately regardless of status
    if current_status_in_db in ["historical", "draft", "archived"]:
        del DB["contents"][id]
        cascade_delete_content_data(id)  # Cascade delete associated data
    # Case 1: If the status of the content is "current" - trash it
    elif current_status_in_db == "current":
        content["status"] = "trashed"
        DB["contents"][id] = content
    # Case 2: If the status of the content is "trashed", and the query parameter "status" is set to "trashed" - purge it
    elif current_status_in_db == "trashed" and status == "trashed":
        del DB["contents"][id]
        cascade_delete_content_data(id)  # Cascade delete associated data
    # Otherwise, do nothing (e.g., content is trashed but status parameter is not "trashed")
    else:
        pass


@tool_spec(
    spec={
        'name': 'search_content_cql',
        'description': """ Search for content based on a CQL (Confluence Query Language) query.
        
        This function performs a comprehensive search across all content items using the provided CQL query.
        It supports complex queries with logical operators, field comparisons, and returns paginated results
        with optional field expansion. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'cql': {
                    'type': 'string',
                    'description': """ The CQL query string. Supported syntax:
                    - Field operators: = (equals), != (not equals), ~ (contains), !~ (does not contain),
                      >, <, >=, <= (numeric/date comparison)
                    - Logical operators: AND, OR, NOT (case-insensitive)
                    - Grouping: Use parentheses () for complex expressions
                    - Value types: Strings ('value' or "value"), Numbers (123 or 45.67), Keywords (null, true, false), Functions (now())
                    - Supported fields: type, space, spaceKey, title, status, id, text, created, postingDay, label
                    - Field mappings:
                        * type: Content type ('page', 'blogpost', 'comment', 'attachment')
                        * space/spaceKey: The key of the space containing this content
                        * title: The title/name of the content item
                        * status: Content status
                        * id: Unique identifier for the content item
                        * text: Master field that searches across title, content body, and labels (supports ~ and !~ operators)
                        * created: Maps to history.createdDate (supports date comparison operators)
                        * postingDay: Direct field on blogpost content (YYYY-MM-DD format, supports date comparison)
                        * label: Searches content labels directly (supports =, != operators for exact match)
                        - Examples:
                          * "type='page' AND spaceKey='DOC'"
                          * "type='page' AND space='DOC'"
                          * "title~'meeting' OR title~'notes'"
                          * "status='current' AND NOT type='comment'"
                          * "text~'marketing' AND type='page'"
                          * "created>='2024-01-01T00:00:00.000Z'"
                          * "type='blogpost' AND postingDay>='2024-01-01'"
                          * "label='finished' AND type='page'"
                          * "label!='draft' OR type='blogpost'"
                          * "id = 1" (unquoted number)
                          * "postingDay = null" (null keyword for fields without values)
                          * "postingDay != null" (fields that have values)
                    - CQL Functions:
                      * now(): Current timestamp
                      * now("-4w"): 4 weeks ago
                      * now("+1d"): 1 day from now
                      * Supported units: d/day, w/week, m/month, y/year, h/hour, min/minute
                    - Function Examples:
                      * "created > now('-4w')" - Content created in last 4 weeks
                      * "title~'project launch' and created > now('-4w')" - Project launch content from last 4 weeks
                    - Note: space field is used for CQL queries, expand='space' returns structured objects """
                },
                'expand': {
                    'type': 'string',
                    'description': """ Comma-separated list of properties to expand in results.
                    Supported values:
                    - space: Include detailed space information (object with 'key', 'name', 'description' fields)
                    - version: Include version information (enhanced object format)
                    - body: Include content body with proper storage structure (may affect pagination limits)
                    - body.storage: Include only the storage representation of the body
                    - body.view: Include only the view representation of the body
                    - metadata: Include content metadata (labels and properties)
                    - metadata.labels: Include only the labels from metadata
                    - history: Include content history information (integrated with ContentAPI)
                    - ancestors: Include ancestor content references
                    - container: Include the same information as the space field """
                },
                'start': {
                    'type': 'integer',
                    'description': 'Starting index for pagination (default: 0, must be non-negative)'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of results to return (default: 25, range: 1-1000)'
                }
            },
            'required': [
                'cql'
            ]
        }
    }
)
def search_content(
    cql: str, expand: Optional[str] = None, start: Optional[int] = 0, limit: Optional[int] = 25
) -> List[Dict[str, Any]]:
    """
    Search for content based on a CQL (Confluence Query Language) query.

    This function performs a comprehensive search across all content items using the provided CQL query.
    It supports complex queries with logical operators, field comparisons, and returns paginated results
    with optional field expansion.

    Args:
        cql (str): The CQL query string. Supported syntax:
            - Field operators: = (equals), != (not equals), ~ (contains), !~ (does not contain),
              >, <, >=, <= (numeric/date comparison)
            - Logical operators: AND, OR, NOT (case-insensitive)
            - Grouping: Use parentheses () for complex expressions
            - Value types: Strings ('value' or "value"), Numbers (123 or 45.67), Keywords (null, true, false), Functions (now())
            - Supported fields: type, space, spaceKey, title, status, id, text, created, postingDay, label
            - Field mappings:
                * type: Content type ('page', 'blogpost', 'comment', 'attachment')
                * space/spaceKey: The key of the space containing this content
                * title: The title/name of the content item
                * status: Content status
                * id: Unique identifier for the content item
                * text: Master field that searches across title, content body, and labels (supports ~ and !~ operators)
                * created: Maps to history.createdDate (supports date comparison operators)
                * postingDay: Direct field on blogpost content (YYYY-MM-DD format, supports date comparison)
                * label: Searches content labels directly (supports =, != operators for exact match)
                - Examples:
                  * "type='page' AND spaceKey='DOC'"
                  * "type='page' AND space='DOC'"
                  * "title~'meeting' OR title~'notes'"
                  * "status='current' AND NOT type='comment'"
                  * "text~'marketing' AND type='page'"
                  * "created>='2024-01-01T00:00:00.000Z'"
                  * "type='blogpost' AND postingDay>='2024-01-01'"
                  * "label='finished' AND type='page'"
                  * "label!='draft' OR type='blogpost'"
                  * "id = 1" (unquoted number)
                  * "postingDay = null" (null keyword for fields without values)
                  * "postingDay != null" (fields that have values)
            - CQL Functions:
              * now(): Current timestamp
              * now("-4w"): 4 weeks ago
              * now("+1d"): 1 day from now
              * Supported units: d/day, w/week, m/month, y/year, h/hour, min/minute
            - Function Examples:
              * "created > now('-4w')" - Content created in last 4 weeks
              * "title~'project launch' and created > now('-4w')" - Project launch content from last 4 weeks
            - Note: space field is used for CQL queries, expand='space' returns structured objects
        
        expand (Optional[str]): Comma-separated list of properties to expand in results.
            Supported values:
            - space: Include detailed space information (object with 'key', 'name', 'description' fields)
            - version: Include version information (enhanced object format)
            - body: Include content body with proper storage structure (may affect pagination limits)
            - body.storage: Include only the storage representation of the body
            - body.view: Include only the view representation of the body
            - metadata: Include content metadata (labels and properties)
            - metadata.labels: Include only the labels from metadata
            - history: Include content history information (integrated with ContentAPI)
            - ancestors: Include ancestor content references
            - container: Include the same information as the space field
        
        start (Optional[int]): Starting index for pagination (default: 0, must be non-negative)
        limit (Optional[int]): Maximum number of results to return (default: 25, range: 1-1000)

    Returns:
        List[Dict[str, Any]]: List of content items matching the search criteria. Base fields include:
            - id (str): Unique identifier for the content item
            - type (str): Content type ('page', 'blogpost', 'comment', 'attachment')
            - spaceKey (str): The key of the space containing this content
            - title (str): The title/name of the content item
            - status (str): Content status
            - body (Dict[str, str]): Content body with nested structure:
                - storage (str): The actual content in Confluence storage format
            - postingDay (Optional[str]): Publication date for blogposts (YYYY-MM-DD format), null for pages
            
        Additional fields are included based on the expand parameter:
            - space: Structured space object with 'key', 'name', and 'description' fields (modern format)
            - version: Version information array format (consistent with ContentAPI)
            - body: Content body with proper storage structure
            - body.storage: Only the storage representation of the body
            - body.view: Only the view representation of the body (converted from storage)
            - metadata: Additional content properties and labels
            - metadata.labels: Only the labels from metadata
            - history: Creation and modification history (integrated with ContentAPI)
            - ancestors: References to ancestor content items
            - container: The same information as the space field

    Raises:
        TypeError: If 'cql' is not a string, or 'start'/'limit' are not integers.
        InvalidPaginationValueError: If 'start' is negative or 'limit' is outside valid range (1-1000).
        InvalidParameterValueError: If 'expand' contains unsupported field names.
        ValueError: If the CQL query is missing, empty, or contains invalid syntax.
        
    """
    # Input validation
    if not isinstance(cql, str):
        raise TypeError("Argument 'cql' must be a string.")
    if expand is not None and not isinstance(expand, str):
        raise TypeError("Argument 'expand' must be a string if provided.")
    if not isinstance(start, int):
        raise TypeError("Argument 'start' must be an integer.")
    if not isinstance(limit, int):
        raise TypeError("Argument 'limit' must be an integer.")

    if start < 0:
        raise InvalidPaginationValueError("Argument 'start' must be non-negative.")
    if not (1 <= limit <= 1000):
        raise InvalidPaginationValueError("Argument 'limit' must be between 1 and 1000.")

    if not cql.strip():
        raise ValueError("CQL query is missing.")
    
    # Preprocess CQL functions (like now()) before tokenizing
    try:
        cql = _preprocess_cql_functions(cql)
    except ValueError as e:
        raise ValueError(f"CQL function error: {str(e)}")
        
    # Validate expand parameter
    expand_fields = []
    if expand and expand.strip():
        ALLOWED_EXPAND_FIELDS = {
            "space", "version", "body", "metadata", "history",
            "ancestors", "container"
        }
        ALLOWED_NESTED_EXPAND_FIELDS = {
            "body.storage", "body.view", "metadata.labels"
        }
        ALL_ALLOWED_FIELDS = ALLOWED_EXPAND_FIELDS | ALLOWED_NESTED_EXPAND_FIELDS
        
        fields = [field.strip() for field in expand.split(',')]
        for field in fields:
            if not field:  # Handle cases like "space,,version"
                raise InvalidParameterValueError("Argument 'expand' contains an empty field name.")
            if field not in ALL_ALLOWED_FIELDS:
                raise InvalidParameterValueError(
                    f"Argument 'expand' contains an invalid field '{field}'. "
                    f"Allowed fields are: {', '.join(sorted(ALL_ALLOWED_FIELDS))}."
                )
        expand_fields = fields

    # Get all contents from database
    all_contents = list(DB["contents"].values())

    # Enhanced tokenizer regex with support for quoted strings, numbers, keywords, and functions
    tokenizer_regex = r"""
        \b(?:and|or|not)\b|                 # Match 'and', 'or', 'not' as whole words
        \(|\)|                              # Match '(' or ')'
        \w+\s*(?:>=|<=|!=|!~|>|<|=|~)\s*   # Match field name and operator part
        (?:                                 # Non-capturing group for value types
            '[^']*'|                        # Match single-quoted string
            \"[^\"]*\"|                     # Match double-quoted string
            \w+\([^)]*\)|                   # Match function calls like now()
            \b(?:null|true|false)\b|        # Match keywords (case-insensitive)
            \d+(?:\.\d+)?                   # Match numbers (integers and decimals)
        )
    """
    tokens = re.findall(tokenizer_regex, cql, re.IGNORECASE | re.VERBOSE)
    
    # Enhanced validation with better error messages
    untokenized_remains = re.sub(tokenizer_regex, "", cql, flags=re.IGNORECASE | re.VERBOSE)
    if untokenized_remains.strip():
        # Provide more specific error messages for common issues
        remaining = untokenized_remains.strip()
        
        # Check for common syntax errors with improved detection
        if re.search(r'==', remaining):  # Check for == operator first
            raise ValueError(
                "CQL query is invalid: Unsupported operator detected. "
                "Found '==' operator. Use single '=' for equality. "
                "Supported operators: =, !=, >, <, >=, <=, ~, !~"
            )
        elif re.search(r'\w+\s*[>=<!~]+\s*\w+(?!["\'])', remaining):
            raise ValueError(
                "CQL query is invalid: String values must be quoted. "
                f"Found unquoted value in: '{remaining}'. "
                "Use single or double quotes around string values."
            )
        elif re.search(r'["\'][^"\'\n]*$', remaining):  # Unclosed quote
            raise ValueError(
                "CQL query is invalid: Unclosed quote detected. "
                "Ensure all quoted strings are properly closed."
            )
        elif re.search(r'\w+\s*[^>=<!~\s\'"()]+', remaining):  # Improved unsupported operator detection
            raise ValueError(
                "CQL query is invalid: Unsupported operator detected. "
                "Supported operators: =, !=, >, <, >=, <=, ~, !~"
            )
        else:
            raise ValueError(
                f"CQL query is invalid: Unrecognized syntax '{remaining}'. "
                "Check field names, operators, and quote usage."
            )

    # Validate field names in tokens for better error reporting
    supported_fields = {"type", "space", "spaceKey", "title", "status", "id", "text", "created", "postingday", "label"}
    supported_fields_lower = {field.lower() for field in supported_fields}
    for token in tokens:
        token_lower = token.lower().strip()
        if token_lower not in {"and", "or", "not", "(", ")"}:
            # Check if it's a field expression
            field_match = re.match(r'(\w+)\s*[>=<!~]+', token, re.IGNORECASE)
            if field_match:
                field_name = field_match.group(1).lower()
                if field_name not in supported_fields_lower:
                    raise ValueError(
                        f"CQL query contains unsupported field '{field_match.group(1)}'. "
                        f"Supported fields are: {', '.join(sorted(supported_fields))}."
                    )

    # Filter contents based on the CQL query with enhanced error handling
    try:
        filtered_contents = [
            content for content in all_contents if _evaluate_cql_tree(content, tokens)
        ]
    except ValueError as e:
        # Re-raise ValueError with CQL context
        raise ValueError(f"CQL evaluation error: {str(e)}")
    except Exception as e:
        # Provide more informative error for unexpected issues
        raise ValueError(
            f"CQL query processing failed: {str(e)}. "
            "Please check your query syntax and try again."
        )

    # Apply pagination
    paginated_results = filtered_contents[start : start + limit]
    
    # Apply expand functionality if requested
    if expand_fields:
        expanded_results = []
        for content in paginated_results:
            expanded_content = content.copy()
            
            for field in expand_fields:
                if field == "space" or field == "container":
                    # Fetch space data from DB.spaces and append
                    space_key = content.get("spaceKey")
                    
                    if space_key and space_key in DB.get("spaces", {}):
                        space_data = DB["spaces"][space_key]
                        if field == "container":
                            expanded_content["container"] = space_data
                        else:
                            expanded_content["space"] = space_data
                        
                
                elif field == "version":
                    # Version returns information about the most recent update of the content,
                    # including who updated it and when it was updated
                    existing_version = content.get("version", {})
                    
                    # Get most recent update information from history
                    if "history" in content:
                        enhanced_version = existing_version.copy()
                        
                        # Add when (most recent update time)
                        if "lastUpdated" in content["history"]:
                            enhanced_version["when"] = content["history"]["lastUpdated"]
                        elif "createdDate" in content["history"]:
                            enhanced_version["when"] = content["history"]["createdDate"]
                        
                        # Add by (most recent updater)
                        if "lastUpdatedBy" in content["history"]:
                            enhanced_version["by"] = content["history"]["lastUpdatedBy"]
                        elif "createdBy" in content["history"]:
                            enhanced_version["by"] = content["history"]["createdBy"]
                        
                        expanded_content["version"] = enhanced_version
                    else:
                        # No history available, keep existing version as is
                        expanded_content["version"] = existing_version
                    
                elif field == "body":
                    # Body is already included in base content, ensure it's properly structured
                    body = expanded_content.get("body")
                    if not body or (isinstance(body, dict) and not body):  # Handle missing or empty body
                        expanded_content["body"] = {"storage": {"value": "", "representation": "storage"}}
                    elif isinstance(body, dict) and "storage" in body:
                        # Ensure proper structure for existing body
                        storage = body["storage"]
                        if isinstance(storage, str):
                            expanded_content["body"]["storage"] = {"value": storage, "representation": "storage"}
                        elif isinstance(storage, dict) and "representation" not in storage:
                            storage["representation"] = "storage"
                    else:
                        # Body exists but doesn't have storage structure, create it
                        expanded_content["body"] = {"storage": {"value": "", "representation": "storage"}}
                            
                elif field == "metadata":
                    # Add metadata including labels and properties
                    content_id = content.get("id")
                    metadata = {}
                    
                    # Add labels if available
                    if content_id and content_id in DB.get("content_labels", {}):
                        metadata["labels"] = {
                            "results": [{"name": label} for label in DB["content_labels"][content_id]],
                            "size": len(DB["content_labels"][content_id])
                        }
                    else:
                        metadata["labels"] = {"results": [], "size": 0}
                        
                    # Add properties if available
                    if content_id and content_id in DB.get("content_properties", {}):
                        prop = DB["content_properties"][content_id]
                        metadata["properties"] = {
                            "results": [prop],
                            "size": 1
                        }
                    else:
                        metadata["properties"] = {"results": [], "size": 0}
                        
                    expanded_content["metadata"] = metadata
                    
                elif field == "history":
                    # Keep existing history as-is (official API doesn't specify additional fields)
                    existing_history = content.get("history", {})
                    
                    # Simply use the existing history data as per official API
                    expanded_content["history"] = existing_history
                    
                elif field == "children":
                    # Add children information (simplified - no actual child traversal in current DB structure)
                    expanded_content["children"] = {
                        "results": [],
                        "size": 0
                    }
                    
                elif field == "ancestors":
                    # Enhance existing ancestors with full details (simple array as per official API)
                    existing_ancestors = content.get("ancestors", [])
                    if existing_ancestors:
                        enhanced_ancestors = []
                        for ancestor in existing_ancestors:
                            if isinstance(ancestor, dict) and "id" in ancestor:
                                ancestor_id = ancestor["id"]
                                ancestor_content = DB["contents"].get(ancestor_id)
                                if ancestor_content:
                                    # Add full ancestor details
                                    ancestor_space_key = ancestor_content.get("spaceKey")
                                    ancestor_space = {}
                                    if ancestor_space_key and ancestor_space_key in DB.get("spaces", {}):
                                        ancestor_space = DB["spaces"][ancestor_space_key]
                                    
                                    enhanced_ancestor = {
                                        "id": ancestor_id,
                                        "type": ancestor_content.get("type", "page"),
                                        "title": ancestor_content.get("title", ""),
                                        "status": ancestor_content.get("status", "current"),
                                        "space": ancestor_space,
                                        "_links": ancestor_content.get("_links", {})
                                    }
                                    enhanced_ancestors.append(enhanced_ancestor)
                                else:
                                    # Keep original if ancestor not found
                                    enhanced_ancestors.append(ancestor)
                            else:
                                # Keep original format if not expected structure
                                enhanced_ancestors.append(ancestor)
                        
                        # Simple array format as per official API (not results/size structure)
                        expanded_content["ancestors"] = enhanced_ancestors
                    else:
                        # No ancestors exist - empty array
                        expanded_content["ancestors"] = []
                

                # Handle nested expand fields
                elif field == "body.storage":
                    # Add only storage representation of body
                    if "body" not in expanded_content:
                        expanded_content["body"] = {}
                    
                    body = expanded_content.get("body", {})
                    if isinstance(body, dict) and "storage" in body:
                        storage_value = body["storage"]
                        if isinstance(storage_value, str):
                            expanded_content["body"]["storage"] = {"value": storage_value, "representation": "storage"}
                        elif isinstance(storage_value, dict):
                            expanded_content["body"]["storage"] = {
                                "value": storage_value.get("value", ""),
                                "representation": "storage"
                            }
                    else:
                        expanded_content["body"]["storage"] = {"value": "", "representation": "storage"}
                
                elif field == "body.view":
                    # Add view representation of body (converted from storage)
                    if "body" not in expanded_content:
                        expanded_content["body"] = {}
                    
                    body = expanded_content.get("body", {})
                    storage_content = ""
                    if isinstance(body, dict) and "storage" in body:
                        storage = body["storage"]
                        if isinstance(storage, str):
                            storage_content = storage
                        elif isinstance(storage, dict):
                            storage_content = storage.get("value", "")
                    
                    # Convert storage format to view format (simplified)
                    view_content = storage_content.replace("<p>", "").replace("</p>", "\n").strip()
                    expanded_content["body"]["view"] = {"value": view_content, "representation": "view"}
                
                elif field == "metadata.labels":
                    # Add only labels from metadata
                    if "metadata" not in expanded_content:
                        expanded_content["metadata"] = {}
                    
                    content_id = content.get("id")
                    if content_id and content_id in DB.get("content_labels", {}):
                        expanded_content["metadata"]["labels"] = {
                            "results": [{"name": label} for label in DB["content_labels"][content_id]],
                            "size": len(DB["content_labels"][content_id])
                        }
                    else:
                        expanded_content["metadata"]["labels"] = {"results": [], "size": 0} 
            expanded_results.append(expanded_content)
        return expanded_results
    
    return paginated_results


@tool_spec(
    spec={
        'name': 'get_content_list',
        'description': """ Returns a paginated list of content filtered by the specified parameters.
        
        This function retrieves all content from the database and applies filters based
        on the provided arguments. The results are paginated using the start and limit parameters. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'type': {
                    'type': 'string',
                    'description': """ The type of content (e.g., "page", "blogpost", "comment").
                    Only content matching this type is returned. If None, no filtering is applied. """
                },
                'spaceKey': {
                    'type': 'string',
                    'description': """ The key of the space in which the content is located.
                    Only content in the specified space is returned. If provided, must not be an empty string or only whitespace. """
                },
                'title': {
                    'type': 'string',
                    'description': 'The title of the content. Filters to content with a matching title. Required if type is "page".'
                },
                'status': {
                    'type': 'string',
                    'description': """ The status of the content (e.g., "current", "trashed", or "any").
                    Defaults to "current". If explicitly set to None, it's treated like "current" by the core logic.
                    If "any", the status filter is ignored. """
                },
                'postingDay': {
                    'type': 'string',
                    'description': """ The posting day of the content. This filter is only applied
                    if the content type is "blogpost". Format: yyyy-mm-dd. Example: "2024-01-01". """
                },
                'expand': {
                    'type': 'string',
                    'description': """ A comma-separated list of additional fields to include in the
                    returned content objects. Supported values:
                    - space: Expands the space field with space key
                    - version: Expands the version information
                    - history: Expands the content history """
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination. Defaults to 0.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of results to return. Defaults to 25.'
                }
            },
            'required': []
        }
    }
)
def get_content_list(
    type: Optional[str] = None,
    spaceKey: Optional[str] = None,
    title: Optional[str] = None,
    status: Optional[str] = "current",
    postingDay: Optional[str] = None,
    expand: Optional[str] = None,
    start: int = 0,
    limit: int = 25
) -> List[Dict[str, Any]]:
    """
    Returns a paginated list of content filtered by the specified parameters.

    This function retrieves all content from the database and applies filters based
    on the provided arguments. The results are paginated using the start and limit parameters.

    Args:
        type (Optional[str]): The type of content (e.g., "page", "blogpost", "comment").
            Only content matching this type is returned. If None, no filtering is applied.
        spaceKey (Optional[str]): The key of the space in which the content is located.
            Only content in the specified space is returned. If provided, must not be an empty string or only whitespace.
        title (Optional[str]): The title of the content. Filters to content with a matching title. Required if type is "page".
        status (Optional[str]): The status of the content (e.g., "current", "trashed", or "any").
            Defaults to "current". If explicitly set to None, it's treated like "current" by the core logic.
            If "any", the status filter is ignored.
        postingDay (Optional[str]): The posting day of the content. This filter is only applied
            if the content type is "blogpost". Format: yyyy-mm-dd. Example: "2024-01-01".
        expand (Optional[str]): A comma-separated list of additional fields to include in the
            returned content objects. Supported values:
            - space: Expands the space field with space key
            - version: Expands the version information
            - history: Expands the content history
        start (int): The starting index for pagination. Defaults to 0.
        limit (int): The maximum number of results to return. Defaults to 25.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the filtered content.
            Each dictionary contains the following keys:
            - id (str): Unique identifier for the content.
            - type (str): Content type.
            - spaceKey (str): Key of the space where the content is located.
            - title (str): Title of the content.
            - status (str): Current status of the content.
            - body (Dict): Content body data.
            - postingDay (Optional[str]): Posting day for blog posts.
            - link (str): URL path to the content.
            - children (Optional[List[Dict[str, Any]]]): List of child content items.
            - ancestors (Optional[List[Dict[str, Any]]]): List of ancestor content items.
            Plus any expanded fields specified in the expand parameter.

    Raises:
        TypeError: If any argument has an incorrect type (e.g., 'type' is not a string, 'start' is not an int).
        InvalidInputError: If 'spaceKey' is an empty string or contains only whitespace.
        InvalidParameterValueError: If 'status' has an unsupported value (and is not None), 
            'postingDay' has an invalid format, 'expand' contains unsupported fields, 
            or 'start'/'limit' are negative.
        MissingTitleForPageError: If 'type' is "page" and 'title' is not provided or is an empty string.
        ValueError: Propagated if errors occur during 'expand' processing for 'history' 
                    (e.g., from an internal `get_content_history` call).
    """
    # --- Input Validation Start ---

    # 1. Standard Type Validation for non-dictionary arguments
    if type is not None and not isinstance(type, str):
        raise TypeError("Argument 'type' must be a string or None.")
    if spaceKey is not None and not isinstance(spaceKey, str):
        raise TypeError("Argument 'spaceKey' must be a string or None.")
    
    # Validation for spaceKey - check for empty or whitespace-only values
    if spaceKey is not None and not spaceKey.strip():
        raise InvalidInputError("Argument 'spaceKey' cannot be an empty string or only whitespace.")
    
    if title is not None and not isinstance(title, str):
        raise TypeError("Argument 'title' must be a string or None.")
    
    # Validation for 'status' (type then value)
    # 'status' default is "current". If status=None is passed, it is None here.
    if status is not None:
        if not isinstance(status, str):
            raise TypeError("Argument 'status' must be a string if provided (i.e., not None).")
        VALID_STATUSES = ["current", "trashed", "any"]
        if status not in VALID_STATUSES:
            raise InvalidParameterValueError(
                f"Argument 'status' must be one of {VALID_STATUSES} if provided. Got '{status}'."
            )
    # If status is None, it's valid at this stage; core logic will effectively treat it as 'current'.

    if postingDay is not None and not isinstance(postingDay, str):
        raise TypeError("Argument 'postingDay' must be a string or None.")
    if expand is not None and not isinstance(expand, str):
        raise TypeError("Argument 'expand' must be a string or None.")
    
    if not isinstance(start, int):
        raise TypeError("Argument 'start' must be an integer.")
    if not isinstance(limit, int):
        raise TypeError("Argument 'limit' must be an integer.")

    if postingDay:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', postingDay):
            raise InvalidParameterValueError("Argument 'postingDay' must be in yyyy-mm-dd format (e.g., '2024-01-01').")

    if expand and expand.strip(): # Process only if expand is not None and not effectively empty
        ALLOWED_EXPAND_FIELDS = {"space", "version", "history"}
        fields = [field.strip() for field in expand.split(',')]
        for f_val in fields:
            if not f_val: # Handles cases like "space,,history" which results in an empty string field
                raise InvalidParameterValueError("Argument 'expand' contains an empty field name, which is invalid.")
            if f_val not in ALLOWED_EXPAND_FIELDS:
                raise InvalidParameterValueError(
                    f"Argument 'expand' contains an invalid field '{f_val}'. "
                    f"Allowed fields are: {', '.join(ALLOWED_EXPAND_FIELDS)}."
                )

    if start < 0:
        raise InvalidParameterValueError("Argument 'start' must be non-negative.")
    if limit < 0:
        raise InvalidParameterValueError("Argument 'limit' must be non-negative.")
    
    # Validate title requirement for pages
    if type == "page" and (title is None or not title.strip()):
        raise MissingTitleForPageError("Argument 'title' is required when type is 'page'.")
        
    # --- Input Validation End ---
    # Collect all content
    all_contents = list(DB["contents"].values())

    # Filter
    if type:
        all_contents = [c for c in all_contents if c.get("type") == type]
    if spaceKey is not None:
        # Validate that the spaceKey exists
        if spaceKey not in DB["spaces"]:
            raise ValueError(f"Space with key='{spaceKey}' not found.")
        all_contents = [c for c in all_contents if c.get("spaceKey") == spaceKey]
    if title:
        all_contents = [c for c in all_contents if c.get("title") == title]
    if postingDay and type == "blogpost":
        # Simulate a postingDay check
        all_contents = [
            c for c in all_contents
            if c.get("postingDay") == postingDay
        ]
    if status and status != "any":
        # "current" or "trashed"
        all_contents = [c for c in all_contents if c.get("status") == status]
    elif status == "any":
        #No filter for status
        pass
    else:
        # Default to "current" if not specified
        all_contents = [c for c in all_contents if c.get("status") == "current"]

    # Apply pagination
    paginated = all_contents[start:start + limit]
    
    # Process expanded fields if requested
    if expand:
        expanded_results = []
        for content in paginated:
            expanded_content = content.copy()
            for field in expand.split(','):
                field = field.strip()
                if field == "space":
                    # Get space information
                    space_key = content.get("spaceKey")
                    if space_key:
                        space = DB.get("spaces", {}).get(space_key)
                        if space:
                            expanded_content["space"] = {
                                "key": space["spaceKey"],
                                "name": space["name"],
                                "description": space.get("description", "")
                            }
                elif field == "version":
                    # Get version information directly from content object
                    version_info = content.get("version", {})
                    version_number = version_info.get("number", 1)
                    expanded_content["version"] = [{"version": version_number}]
                elif field == "history":
                    # Get content history (ValueError will propagate if content not found)
                    content_id = content.get("id")
                    if content_id:
                        history = get_content_history(content_id)
                        if history:
                            expanded_content["history"] = history
            expanded_results.append(expanded_content)
        return expanded_results
    
    return paginated


@tool_spec(
    spec={
        'name': 'get_content_history',
        'description': """ Returns the history of a piece of content.
        
        This method returns the metadata regarding creation and versioning for the content item
        identified by the given id. It uses a global history store (DB["history"]) that is updated
        whenever content is created or updated. Each history record includes the version number,
        createdBy, createdDate, and lastUpdated timestamp. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Unique identifier of the content.'
                },
                'expand': {
                    'type': 'string',
                    'description': """ A comma-separated list of additional fields to expand
                    (e.g., "previousVersion,nextVersion,lastUpdated"). """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_history(id: str, expand: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns the history of a piece of content.

    This method returns the metadata regarding creation and versioning for the content item
    identified by the given id. It uses a global history store (DB["history"]) that is updated
    whenever content is created or updated. Each history record includes the version number,
    createdBy, createdDate, and lastUpdated timestamp.

    Args:
        id (str): Unique identifier of the content.
        expand (Optional[str], optional): A comma-separated list of additional fields to expand
                                          (e.g., "previousVersion,nextVersion,lastUpdated").

    Returns:
        Dict[str, Any]: A dictionary representing the content's history with the following structure:
            - id (str): The unique identifier of the content.
            - latest (bool): Indicating whether this is the latest version of the content.
            - createdBy (Dict[str, str]): Creator information:
                - type (str): User type.
                - username (str): Username of the creator.
                - displayName (str): Display name of the creator.
            - createdDate (str): The ISO timestamp when the content was created.
            - previousVersion (Optional[Dict[str, Any]]): The previous version record, if available.
            - nextVersion (Optional[Dict[str, Any]]): The next version record, if available.

    Raises:
        ValueError: If no content with the specified id is found or if the id is an empty string.
        TypeError: If the arguments are not of the correct type.
    """
    # --- Input Validation Start ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    
    if not id.strip():
        raise ValueError("Argument 'id' cannot be an empty string.")

    if expand is not None and not isinstance(expand, str):
        raise TypeError("Argument 'expand' must be a string or None.")
    # --- Input Validation End ---

    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id={id} not found.")
    
    # Initialize history if it doesn't exist
    if "history" not in DB:
        DB["history"] = {}
    
    # Get history records for this content
    history_records = DB["history"].get(id, [])
    
    if not history_records:
        # If no history records exist, create one from the content's current state
        content_history = content.get("history", {})
        created_date = content_history.get("createdDate", get_iso_timestamp())
        created_by = content_history.get("createdBy", {
            "type": "known",
            "username": "system",
            "displayName": "System User"
        })
        
        # Create initial history record
        history_record = {
            "version": content.get("version", {}).get("number", 1),
            "when": created_date,
            "by": created_by,
            "message": "Initial version",
            "minorEdit": False
        }
        
        # Store it for future use
        DB["history"][id] = [history_record]
        history_records = [history_record]
    
    # Get the latest version (last record)
    latest_record = history_records[-1] if history_records else None
    
    # Build the history response
    history = {
        "id": id,
        "latest": True,
        "createdBy": latest_record["by"] if latest_record else {
            "type": "known",
            "username": "system",
            "displayName": "System User"
        },
        "createdDate": history_records[0]["when"] if history_records else get_iso_timestamp(),
    }
    
    # Always include previousVersion and nextVersion fields
    history["previousVersion"] = None
    history["nextVersion"] = None
    
    # Handle expand parameter
    if expand and expand.strip():
        expand_fields = [field.strip().lower() for field in expand.split(",") if field.strip()]
        
        if "previousversion" in expand_fields and len(history_records) > 1:
            # Get the previous version record
            previous_record = history_records[-2]
            history["previousVersion"] = {
                "number": previous_record["version"],
                "when": previous_record["when"],
                "by": previous_record["by"],
                "message": previous_record["message"],
                "minorEdit": previous_record["minorEdit"]
            }
            
        if "nextversion" in expand_fields:
            # In this simulation, there's no "next" version since we always work with latest
            history["nextVersion"] = None
            
        if "lastupdated" in expand_fields and latest_record:
            history["lastUpdated"] = {
                "when": latest_record["when"],
                "by": latest_record["by"],
                "message": latest_record["message"],
                "version": latest_record["version"],
                "minorEdit": latest_record["minorEdit"]
            }
    
    return history


@tool_spec(
    spec={
        'name': 'get_content_children',
        'description': """ Returns a mapping of direct children content grouped by type.
        
        This function retrieves all direct children of a content item by searching for content
        that has the specified item as their immediate parent (ancestor). Results are grouped
        by content type for easy access. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Unique identifier of the parent content item. Must be a non-empty string.'
                },
                'expand': {
                    'type': 'string',
                    'description': """ A comma-separated list of additional fields to include in the response.
                    Supported values: 'space', 'version', 'history', 'body', 'metadata'. Defaults to None. """
                },
                'parentVersion': {
                    'type': 'integer',
                    'description': """ The version number of the parent content to consider.
                    Used for version-specific child queries. Defaults to 0 (latest version). """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_children(
    id: str, expand: Optional[str] = None, parentVersion: int = 0
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a mapping of direct children content grouped by type.

    This function retrieves all direct children of a content item by searching for content
    that has the specified item as their immediate parent (ancestor). Results are grouped
    by content type for easy access.

    Args:
        id (str): Unique identifier of the parent content item. Must be a non-empty string.
        expand (Optional[str]): A comma-separated list of additional fields to include in the response.
            Supported values: 'space', 'version', 'history', 'body', 'metadata'. Defaults to None.
        parentVersion (int): The version number of the parent content to consider.
            Used for version-specific child queries. Defaults to 0 (latest version).

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary where each key represents a content type
            ('page', 'blogpost', 'comment', 'attachment') and the corresponding value is a list
            of direct child content dictionaries. Each child content dictionary contains:
                - id (str): Unique identifier for the content
                - type (str): Content type ('page', 'blogpost', 'comment', 'attachment')
                - title (str): Title of the content
                - spaceKey (str): Key of the space where the content is located.
                - status (str): Current status of the content ('current', 'draft', 'archived', 'trashed')
                - body (Dict[str, Any]): Content body data with storage format
                - version (Dict[str, Any]): Version information with number and minorEdit
                - history (Dict[str, Any]): History information with createdBy and createdDate
                - ancestors (List[Dict[str, str]]): List of ancestor objects (for comments)
                - _links (Dict[str, str]): API navigation links

    Raises:
        TypeError: If 'id' is not a string, 'expand' is not a string (when provided),
                   or 'parentVersion' is not an integer.
        ValueError: If 'id' is an empty string or the parent content with the specified id is not found.
        InvalidParameterValueError: If 'parentVersion' is negative.
    """
    # --- Input Validation Start ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    
    if not id.strip():
        raise ValueError("Argument 'id' cannot be an empty string.")
    
    if expand is not None and not isinstance(expand, str):
        raise TypeError("Argument 'expand' must be a string or None.")
    
    if not isinstance(parentVersion, int):
        raise TypeError("Argument 'parentVersion' must be an integer.")
    
    if parentVersion < 0:
        raise InvalidParameterValueError("Argument 'parentVersion' must be non-negative.")
    # --- Input Validation End ---
    
    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id={id} not found.")
    
    # Initialize result dictionary with empty lists for each content type
    children_by_type: Dict[str, List[Dict[str, Any]]] = {"page": [], "blogpost": [], "comment": [], "attachment": []}

    # Find direct children by searching for content that has this item as immediate parent
    for potential_child_id, potential_child in DB["contents"].items():
        ancestors = potential_child.get("ancestors", [])
        
        # Check if this content is a direct child (has current content as immediate ancestor)
        if ancestors:
            # For direct children, the immediate parent is the last (or only) ancestor
            immediate_parent = ancestors[-1] if isinstance(ancestors[-1], dict) else {"id": ancestors[-1]}
            if immediate_parent.get("id") == id:
                child_type = potential_child.get("type")
                if child_type in children_by_type:
                    children_by_type[child_type].append(potential_child)

    return children_by_type


@tool_spec(
    spec={
        'name': 'get_content_children_by_type',
        'description': 'Returns direct children content of a specified type.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Unique identifier of the parent content.'
                },
                'child_type': {
                    'type': 'string',
                    'description': 'The type of child content to retrieve (e.g., "page", "blogpost", "comment", "attachment").'
                },
                'expand': {
                    'type': 'string',
                    'description': 'Additional fields to include in the result. Defaults to None.'
                },
                'parentVersion': {
                    'type': 'integer',
                    'description': """ The version of the parent content. Provided for potential future use; not used
                    in this simulation. Defaults to 0. """
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination. Defaults to 0.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of child content items to return. Defaults to 25.'
                }
            },
            'required': [
                'id',
                'child_type'
            ]
        }
    }
)
def get_content_children_of_type(
    id: str,
    child_type: str,
    expand: Optional[str] = None,
    parentVersion: int = 0,
    start: int = 0,
    limit: int = 25,
) -> Dict[str, Dict[str, Any]]:
    """
    Returns direct children content of a specified type.

    Args:
        id (str): Unique identifier of the parent content.
        child_type (str): The type of child content to retrieve (e.g., "page", "blogpost", "comment", "attachment").
        expand (Optional[str], optional): Additional fields to include in the result. Defaults to None.
        parentVersion (int): The version of the parent content. Provided for potential future use; not used
            in this simulation. Defaults to 0.
        start (int): The starting index for pagination. Defaults to 0.
        limit (int): The maximum number of child content items to return. Defaults to 25.

    Returns:
        Dict[str, Dict[str, Any]]: A JSON map representing ordered collections of content children, keyed by content type.
            The structure contains:
            - {child_type} (Dict[str, Any]): A dictionary with keys:
                - results (List[Dict[str, Any]]): Paginated list of child content items, each containing:
                    - id (str): Unique identifier for the content
                    - type (str): Content type (e.g., "page", "blogpost", "comment", "attachment")
                    - title (str): Title of the content
                    - spaceKey (str): Key of the space where the content is located
                    - status (str): Current status of the content (e.g., "current", "trashed")
                    - body (Dict[str, Any]): Content body data with storage format
                    - version (Dict[str, Any]): Content version information
                    - ancestors (Optional[List[Dict[str, Any]]]): List of ancestor content items
                    - children (Optional[List[Dict[str, Any]]]): List of child content items
                    - descendants (Optional[List[Dict[str, Any]]]): List of descendant content items
                    - postingDay (Optional[str]): Posting day for blog posts
                    - link (str): URL path to the content
                - size (int): Number of items in the results array

    Raises:
        TypeError: If 'id' is not a string, 'child_type' is not a string, 'expand' is not a string (when provided),
                   'parentVersion' is not an integer, 'start' is not an integer, or 'limit' is not an integer.
        InvalidInputError: If 'id' is an empty string, 'child_type' is an empty string, or 'expand' is an empty string.
        InvalidParameterValueError: If 'child_type' has an unsupported value, 'start' is negative, or 'limit' is not positive.
        ContentNotFoundError: If the parent content with the given id is not found.
    """
    # --- Input Validation Start ---
    
    # Validate id parameter
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    # Validate child_type parameter
    if not isinstance(child_type, str):
        raise TypeError("Argument 'child_type' must be a string.")
    if not child_type.strip():
        raise InvalidInputError("Argument 'child_type' cannot be an empty string.")
    
    # Validate supported child types
    VALID_CHILD_TYPES = ["page", "blogpost", "comment", "attachment"]
    if child_type not in VALID_CHILD_TYPES:
        raise InvalidParameterValueError(
            f"Argument 'child_type' must be one of {VALID_CHILD_TYPES}. Got '{child_type}'."
        )
    
    # Validate expand parameter
    if expand is not None:
        if not isinstance(expand, str):
            raise TypeError("Argument 'expand' must be a string if provided.")
        if not expand.strip():
            raise InvalidInputError("Argument 'expand' cannot be an empty string if provided.")
    
    # Validate parentVersion parameter
    if not isinstance(parentVersion, int):
        raise TypeError("Argument 'parentVersion' must be an integer.")
    if parentVersion < 0:
        raise InvalidParameterValueError("Argument 'parentVersion' must be non-negative.")
    
    # Validate start parameter
    if not isinstance(start, int):
        raise TypeError("Argument 'start' must be an integer.")
    if start < 0:
        raise InvalidParameterValueError("Argument 'start' must be non-negative.")
    
    # Validate limit parameter
    if not isinstance(limit, int):
        raise TypeError("Argument 'limit' must be an integer.")
    if limit <= 0:
        raise InvalidParameterValueError("Argument 'limit' must be positive.")
    
    # --- Input Validation End ---
    
    # Check if parent content exists
    parent = DB["contents"].get(id)
    if not parent:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")

    children = parent.get("children", [])
    filtered_children = []
    for child in children:
        if child and child.get("type") == child_type:
            filtered_children.append(child)

    # Apply pagination
    paginated_results = filtered_children[start : start + limit]
    
    return {
        child_type: {
            "results": paginated_results,
            "size": len(paginated_results)
        }
    }


@tool_spec(
    spec={
        'name': 'get_content_comments',
        'description': 'Returns the comments associated with a specific content item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the parent content.'
                },
                'expand': {
                    'type': 'string',
                    'description': """ A comma-separated list of additional fields to include in the
                    returned comment objects. Defaults to None. """
                },
                'parentVersion': {
                    'type': 'integer',
                    'description': 'The version of the parent content. Defaults to 0.'
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination. Defaults to 0.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of comment objects to return. Defaults to 25.'
                },
                'location': {
                    'type': 'string',
                    'description': """ An optional parameter to specify a location filter within the
                    content hierarchy. Defaults to None. """
                },
                'depth': {
                    'type': 'string',
                    'description': 'An optional parameter to control the depth of comment retrieval. Defaults to None.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_comments(
    id: str,
    expand: Optional[str] = None,
    parentVersion: int = 0,
    start: int = 0,
    limit: int = 25,
    location: Optional[str] = None,
    depth: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns the comments associated with a specific content item.

    Args:
        id (str): The unique identifier of the parent content.
        expand (Optional[str]): A comma-separated list of additional fields to include in the
            returned comment objects. Defaults to None.
        parentVersion (int): The version of the parent content. Defaults to 0.
        start (int): The starting index for pagination. Defaults to 0.
        limit (int): The maximum number of comment objects to return. Defaults to 25.
        location (Optional[str]): An optional parameter to specify a location filter within the
            content hierarchy. Defaults to None.
        depth (Optional[str]): An optional parameter to control the depth of comment retrieval. Defaults to None.

    Returns:
        Dict[str, Any]: A JSON map representing ordered collections of comment children, keyed by content type.
            The structure contains:
            - comment (Dict[str, Any]): A dictionary with keys:
                - results (List[Dict[str, Any]]): Paginated list of comment content items, each containing:
                    - id (str): Unique identifier for the content
                    - type (str): Content type (e.g., "comment")
                    - title (str): Title of the content
                    - spaceKey (str): Key of the space where the content is located
                    - status (str): Current status of the content (e.g., "current", "trashed")
                    - body (Dict[str, Any]): Content body data with storage format
                    - version (Dict[str, Any]): Content version information
                    - ancestors (Optional[List[Dict[str, Any]]]): List of ancestor content items
                    - children (Optional[List[Dict[str, Any]]]): List of child content items
                    - descendants (Optional[List[Dict[str, Any]]]): List of descendant content items
                    - postingDay (Optional[str]): Posting day for blog posts
                    - link (str): URL path to the content
                - size (int): Number of items in the results array

    Raises:
        TypeError: If 'id' is not a string, 'expand' is not a string (when provided),
                   'parentVersion' is not an integer, 'start' is not an integer, or 'limit' is not an integer.
        InvalidInputError: If 'id' is an empty string, or 'expand' is an empty string.
        InvalidParameterValueError: If 'start' is negative, or 'limit' is not positive.
        ContentNotFoundError: If the parent content with the given id is not found.
    """
    # --- Input Validation Start ---
    
    # Validate id parameter
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    # Validate expand parameter
    if expand is not None:
        if not isinstance(expand, str):
            raise TypeError("Argument 'expand' must be a string if provided.")
        if not expand.strip():
            raise InvalidInputError("Argument 'expand' cannot be an empty string if provided.")
    
    # Validate parentVersion parameter
    if not isinstance(parentVersion, int):
        raise TypeError("Argument 'parentVersion' must be an integer.")
    if parentVersion < 0:
        raise InvalidParameterValueError("Argument 'parentVersion' must be non-negative.")
    
    # Validate start parameter
    if not isinstance(start, int):
        raise TypeError("Argument 'start' must be an integer.")
    if start < 0:
        raise InvalidParameterValueError("Argument 'start' must be non-negative.")
    
    # Validate limit parameter
    if not isinstance(limit, int):
        raise TypeError("Argument 'limit' must be an integer.")
    if limit <= 0:
        raise InvalidParameterValueError("Argument 'limit' must be positive.")
    
    # --- Input Validation End ---
    
    # Check if parent content exists
    parent = DB["contents"].get(id)
    if not parent:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")

    children = parent.get("children", [])
    comments = []
    for child in children:
        if child and child.get("type") == "comment":
            comments.append(child)

    # Apply pagination
    paginated_results = comments[start : start + limit]
    
    return {
        "comment": {
            "results": paginated_results,
            "size": len(paginated_results)
        }
    }


@tool_spec(
    spec={
        'name': 'get_content_attachments',
        'description': 'Returns attachments for a specific content item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the parent content.'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of additional fields to include. Defaults to None.'
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination. Defaults to 0.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of attachments to return. Defaults to 50.'
                },
                'filename': {
                    'type': 'string',
                    'description': 'Filter attachments by filename. Defaults to None.'
                },
                'mediaType': {
                    'type': 'string',
                    'description': 'Filter attachments by media type. Defaults to None.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_attachments(
    id: str,
    expand: Optional[str] = None,
    start: int = 0,
    limit: int = 50,
    filename: Optional[str] = None,
    mediaType: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns attachments for a specific content item.

    Args:
        id (str): The unique identifier of the parent content.
        expand (Optional[str]): A comma-separated list of additional fields to include. Defaults to None.
        start (int): The starting index for pagination. Defaults to 0.
        limit (int): The maximum number of attachments to return. Defaults to 50.
        filename (Optional[str]): Filter attachments by filename. Defaults to None.
        mediaType (Optional[str]): Filter attachments by media type. Defaults to None.

    Returns:
        Dict[str, Any]: A JSON representation of a list of attachment Content entities with structure:
            - results (List[Dict[str, Any]]): Paginated list of attachment content items, each containing:
                - id (str): Unique identifier for the attachment
                - type (str): Content type (always "attachment")
                - title (str): Attachment filename/title
                - version (Dict[str, Any]): Version information with keys:
                    - by (Dict[str, Any]): User who created the version
                    - when (str): ISO timestamp of version creation
                    - message (str): Version change message
                    - number (int): Version number
                    - minorEdit (bool): Whether this was a minor edit
                - container (Dict[str, Any]): Parent content information
                - metadata (Dict[str, Any]): Attachment metadata with keys:
                    - comment (str): Attachment comment/description
                    - mediaType (str): MIME type of the attachment
                - _links (Dict[str, str]): API links
                - _expandable (Dict[str, str]): Expandable fields
            - size (int): Number of items in the results array
            - _links (Dict[str, str]): API base links

    Raises:
        TypeError: If 'id' is not a string, 'expand' is not a string (when provided), 
                   'start' or 'limit' are not integers, 'filename' or 'mediaType' are not strings (when provided).
        InvalidInputError: If 'id' is an empty string, or 'expand', 'filename', or 'mediaType' are empty strings (when provided).
        InvalidParameterValueError: If 'start' is negative, 'limit' is not positive, or 'limit' exceeds maximum value.
        ContentNotFoundError: If the parent content with the given id is not found.
    """
    # --- Input Validation Start ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    if expand is not None:
        if not isinstance(expand, str):
            raise TypeError("Argument 'expand' must be a string if provided.")
        if not expand.strip():
            raise InvalidInputError("Argument 'expand' cannot be an empty string if provided.")
    
    if not isinstance(start, int):
        raise TypeError("Argument 'start' must be an integer.")
    if start < 0:
        raise InvalidParameterValueError("Argument 'start' must be non-negative.")
    
    if not isinstance(limit, int):
        raise TypeError("Argument 'limit' must be an integer.")
    if limit <= 0:
        raise InvalidParameterValueError("Argument 'limit' must be positive.")
    if limit > 1000:  # Reasonable maximum limit
        raise InvalidParameterValueError("Argument 'limit' cannot exceed 1000.")
    
    if filename is not None:
        if not isinstance(filename, str):
            raise TypeError("Argument 'filename' must be a string if provided.")
        if not filename.strip():
            raise InvalidInputError("Argument 'filename' cannot be an empty string if provided.")
    
    if mediaType is not None:
        if not isinstance(mediaType, str):
            raise TypeError("Argument 'mediaType' must be a string if provided.")
        if not mediaType.strip():
            raise InvalidInputError("Argument 'mediaType' cannot be an empty string if provided.")
    # --- Input Validation End ---
    
    # Check if parent content exists
    parent = DB["contents"].get(id)
    if not parent:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")
    
    # Get children and filter for attachments
    children = parent.get("children", [])
    attachments = []
    
    for child in children:
        if child and child.get("type") == "attachment":
            # Apply filename filter if provided
            if filename and child.get("title") != filename:
                continue
            
            # Apply mediaType filter if provided
            if mediaType and child.get("metadata", {}).get("mediaType") != mediaType:
                continue
            
            attachments.append(child)
    
    # Apply pagination
    paginated_attachments = attachments[start : start + limit]
    
    # Return in the expected API format
    return {
        "results": paginated_attachments,
        "size": len(paginated_attachments),
        "_links": {
            "base": "http://example.com",
            "context": "/confluence"
        }
    }


@tool_spec(
    spec={
        'name': 'create_content_attachments',
        'description': """ Adds an attachment to a piece of content. If the attachment already exists for the content, 
        
        then the attachment is updated (i.e. a new version of the attachment is created). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'Required. The ID of the content to add the attachment to.'
                },
                'file': {
                    'type': 'string',
                    'description': 'Required. The relative location and name of the attachment to be added to the content.'
                },
                'minorEdit': {
                    'type': 'string',
                    'description': """ Required. If minorEdits is set to 'true', no notification email or activity 
                    stream will be generated when the attachment is added to the content. """
                },
                'comment': {
                    'type': 'string',
                    'description': """ The comment for the attachment that is being added. 
                    If you specify a comment, then every file must have a comment 
                    and the comments must be in the same order as the files. 
                    Alternatively, don't specify any comments. Defaults to None. """
                },
                'status': {
                    'type': 'string',
                    'description': """ The status of the content that the attachment is being added to. 
                    This should always be set to 'current'.
                    Valid values: current, draft. Defaults to "current". """
                }
            },
            'required': [
                'id',
                'file',
                'minorEdit'
            ]
        }
    }
)
def create_attachments(
    id: str, file: str, minorEdit: str, comment: Optional[str] = None, status: Optional[str] = "current"
) -> Dict[str, Any]:
    """
    Adds an attachment to a piece of content. If the attachment already exists for the content, 
    then the attachment is updated (i.e. a new version of the attachment is created).
    
    Args:
        id (str): Required. The ID of the content to add the attachment to.
        file (str): Required. The relative location and name of the attachment to be added to the content.
        minorEdit (str): Required. If minorEdits is set to 'true', no notification email or activity 
                        stream will be generated when the attachment is added to the content.
        comment (Optional[str]): The comment for the attachment that is being added. 
                                If you specify a comment, then every file must have a comment 
                                and the comments must be in the same order as the files. 
                                Alternatively, don't specify any comments. Defaults to None.
        status (Optional[str]): The status of the content that the attachment is being added to. 
                     This should always be set to 'current'.
                     Valid values: current, draft. Defaults to "current".

    Returns:
        Dict[str, Any]: A dictionary containing information about the created attachment:
            - attachmentId (str): The unique identifier of the attachment.
            - fileName (str): The name of the attached file.
            - comment (Optional[str]): The comment describing the attachment.
            - minorEdit (str): Whether this was a minor edit ("true" or "false").

    Raises:
        TypeError: If 'id' is not a string, 'file' is not a string, 'minorEdit' is not a string,
                   'comment' is not a string (when provided), or 'status' is not a string (when provided).
        InvalidInputError: If 'id' is an empty string, 'minorEdit' is not 'true' or 'false', 
                          or 'status' is not one of 'current', 'draft', 'archived', or 'trashed'.
        FileAttachmentError: If 'file' is an empty string.
        ContentNotFoundError: If the parent content with the given id is not found.
    """
    # --- Input Validation Start ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    if not isinstance(file, str):
        raise TypeError("Argument 'file' must be a string.")
    if not file.strip():
        raise FileAttachmentError("Argument 'file' cannot be an empty string.")
    
    if not isinstance(minorEdit, str):
        raise TypeError("Argument 'minorEdit' must be a string.")
    if minorEdit not in ["true", "false"]:
        raise InvalidInputError("Argument 'minorEdit' must be either 'true' or 'false'.")
    
    if comment is not None and not isinstance(comment, str):
        raise TypeError("Argument 'comment' must be a string if provided.")
    
    if status is not None and not isinstance(status, str):
        raise TypeError("Argument 'status' must be a string if provided.")
    if status is not None and status not in ["current", "draft", "archived", "trashed"]:
        raise InvalidInputError("Argument 'status' must be one of 'current', 'draft', 'archived', or 'trashed'.")
    
    # Set default if None
    if status is None:
        status = "current"
    # --- Input Validation End ---
    
    # Check if parent content exists
    content = DB["contents"].get(id)
    if not content:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")
    
    # Fake an "attachment" record
    return {
        "attachmentId": "1",
        "fileName": file,
        "comment": comment,
        "minorEdit": minorEdit,
    }


@tool_spec(
    spec={
        'name': 'update_attachment_metadata',
        'description': 'Updates the metadata of an existing attachment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the parent content.'
                },
                'attachmentId': {
                    'type': 'string',
                    'description': 'The unique identifier of the attachment to update.'
                },
                'body': {
                    'type': 'object',
                    'description': 'The updated metadata for the attachment.',
                    'properties': {
                        'comment': {
                            'type': 'string',
                            'description': 'Attachment comment/description.'
                        },
                        'mediaType': {
                            'type': 'string',
                            'description': 'MIME type (e.g., "text/plain", "application/pdf").'
                        },
                        'title': {
                            'type': 'string',
                            'description': 'New display name for the attachment.'
                        },
                        'labels': {
                            'type': 'array',
                            'description': 'Labels to associate with the attachment.',
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'id',
                'attachmentId',
                'body'
            ]
        }
    }
)
def update_attachment(
    id: str, attachmentId: str, body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Updates the metadata of an existing attachment.

    Args:
        id (str): The unique identifier of the parent content.
        attachmentId (str): The unique identifier of the attachment to update.
        body (Dict[str, Any]): The updated metadata for the attachment.
            - comment (Optional[str]): Attachment comment/description.
            - mediaType (Optional[str]): MIME type (e.g., "text/plain", "application/pdf").
            - title (Optional[str]): New display name for the attachment.
            - labels (Optional[List[str]]): Labels to associate with the attachment.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - attachmentId (str): The unique identifier of the attachment.
            - updatedFields (Dict[str, Any]): A dictionary of the fields that were updated.

    Raises:
        ValueError: If the parent content or attachment is not found.
    """
    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id={id} not found.")
    return {"attachmentId": attachmentId, "updatedFields": body}


@tool_spec(
    spec={
        'name': 'update_attachment_data',
        'description': 'Updates the binary data of an existing attachment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the parent content.'
                },
                'attachmentId': {
                    'type': 'string',
                    'description': 'The unique identifier of the attachment to update.'
                },
                'file': {
                    'type': 'object',
                    'description': """ The new file object to replace the existing attachment. Expected to be a file-like object.
                    Commonly accepted shapes:
                    - File-like object with a 'name' attribute (e.g., file.name) used for reporting.
                    - Byte stream or file handle is accepted; if 'name' is missing, 'unknown' is used in response. """,
                    'properties': {},
                    'required': []
                },
                'comment': {
                    'type': 'string',
                    'description': 'A comment describing the update.'
                },
                'minorEdit': {
                    'type': 'boolean',
                    'description': 'Whether this is a minor edit.'
                }
            },
            'required': [
                'id',
                'attachmentId',
                'file'
            ]
        }
    }
)
def update_attachment_data(
    id: str,
    attachmentId: str,
    file: Any,
    comment: Optional[str] = None,
    minorEdit: bool = False,
) -> Dict[str, Any]:
    """
    Updates the binary data of an existing attachment.

    Args:
        id (str): The unique identifier of the parent content.
        attachmentId (str): The unique identifier of the attachment to update.
        file (Any): The new file object to replace the existing attachment. Expected to be a file-like object.
            Commonly accepted shapes:
            - File-like object with a 'name' attribute (e.g., file.name) used for reporting.
            - Byte stream or file handle is accepted; if 'name' is missing, 'unknown' is used in response.
        comment (Optional[str]): A comment describing the update.
        minorEdit (bool): Whether this is a minor edit.

    Returns:
        Dict[str, Any]: A dictionary containing information about the updated attachment:
            - attachmentId (str): The unique identifier of the attachment.
            - updatedFile (str): The name of the updated file.
            - comment (Optional[str]): The comment describing the update.
            - minorEdit (bool): Whether this was a minor edit.

    Raises:
        TypeError: If 'id' is not a string, 'attachmentId' is not a string,
                   'comment' is not a string (when provided), or 'minorEdit' is not a boolean.
        InvalidInputError: If 'id' or 'attachmentId' is an empty string.
        FileAttachmentError: If 'file' is None or invalid.
        ContentNotFoundError: If the parent content with the given id is not found.
    """
    # --- Input Validation Start ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    if not isinstance(attachmentId, str):
        raise TypeError("Argument 'attachmentId' must be a string.")
    if not attachmentId.strip():
        raise InvalidInputError("Argument 'attachmentId' cannot be an empty string.")
    
    if file is None:
        raise FileAttachmentError("Argument 'file' cannot be None.")
    
    if comment is not None and not isinstance(comment, str):
        raise TypeError("Argument 'comment' must be a string if provided.")
    
    if not isinstance(minorEdit, bool):
        raise TypeError("Argument 'minorEdit' must be a boolean.")
    # --- Input Validation End ---
    
    content = DB["contents"].get(id)
    if not content:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")
    
    return {
        "attachmentId": attachmentId,
        "updatedFile": getattr(file, "name", "unknown"),
        "comment": comment,
        "minorEdit": minorEdit,
    }


@tool_spec(
    spec={
        'name': 'get_content_descendants',
        'description': 'Returns all descendants of a content item, grouped by type.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the parent content.'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of additional fields to include.'
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of descendants to return per type.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_descendants(
    id: str, expand: Optional[str] = None, start: int = 0, limit: int = 25
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns all descendants of a content item, grouped by type.

    Args:
        id (str): The unique identifier of the parent content.
        expand (Optional[str]): A comma-separated list of additional fields to include.
        start (int): The starting index for pagination.
        limit (int): The maximum number of descendants to return per type.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary mapping content types to lists of descendant content.
            Each Dict[str, Any] contains:
                - id (str): Unique identifier for the content.
                - type (str): Content type (e.g., "page", "blogpost", "comment", "attachment").
                - title (str): Title of the content.
                - spaceKey (str): Key of the space where the content is located.
                - status (str): Current status of the content (e.g., "current", "trashed").
                - body (Dict[str, Any]): Content body data.
                - postingDay (Optional[str]): Posting day for blog posts.
                - link (str): URL path to the content.
                - children (Optional[List[Dict[str, Any]]]): List of child content.
                - ancestors (Optional[List[Dict[str, Any]]]): List of ancestor content.

    Raises:
        TypeError: 
            If 'id' is not a string.
            If 'start' or 'limit' is not an integer.
        InvalidInputError: 
            If 'id' is an empty string.
            If 'start' is negative or 'limit' is negative or zero.
        ValueError: If the parent content with the given id is not found.
    """
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    
    id = id.strip()
    if not id:
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    parent = DB["contents"].get(id)
    if not parent:
        raise ValueError(f"Content with id={id} not found.")

    if not isinstance(start, int) or isinstance(start, bool):
        raise TypeError("Argument 'start' must be an integer.")
    
    if start and start < 0:
        raise InvalidInputError("Argument 'start' must be non-negative.")
    
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise TypeError("Argument 'limit' must be an integer.")
    
    if limit and limit <= 0:
        raise InvalidInputError("Argument 'limit' must be non-negative.")

    # Initialize the result dictionary with empty lists for each content type
    descendants: Dict[str, List[Dict[str, Any]]] = {"page": [], "blogpost": [], "comment": [], "attachment": []}

    # Collect all descendants
    all_descendants = _collect_descendants(parent)

    # Group descendants by type
    for descendant in all_descendants:
        descendant_type = descendant.get("type")
        if descendant_type in descendants:
            descendants[descendant_type].append(descendant)

    # Apply pagination to each type's list
    for content_type in descendants:
        descendants[content_type] = descendants[content_type][start : start + limit]

    return descendants


@tool_spec(
    spec={
        'name': 'get_content_descendants_by_type',
        'description': 'Returns descendants of a specific type for a content item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the parent content.'
                },
                'type': {
                    'type': 'string',
                    'description': 'The type of descendants to retrieve (e.g., "page", "blogpost", "comment", "attachment").'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of additional fields to include.'
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of descendants to return.'
                }
            },
            'required': [
                'id',
                'type'
            ]
        }
    }
)
def get_content_descendants_of_type(
    id: str, type: str, expand: Optional[str] = None, start: int = 0, limit: int = 25
) -> List[Dict[str, Any]]:
    """
    Returns descendants of a specific type for a content item.

    Args:
        id (str): The unique identifier of the parent content.
        type (str): The type of descendants to retrieve (e.g., "page", "blogpost", "comment", "attachment").
        expand (Optional[str]): A comma-separated list of additional fields to include.
        start (int): The starting index for pagination.
        limit (int): The maximum number of descendants to return.

    Returns:
        List[Dict[str, Any]]: A paginated list of descendant content dictionaries of the specified type.
            Each Dict[str, Any] contains:
                - id (str): Unique identifier for the content.
                - type (str): Content type (e.g., "page", "blogpost", "comment", "attachment").
                - title (str): Title of the content.
                - spaceKey (str): Key of the space where the content is located.
                - status (str): Current status of the content (e.g., "current", "trashed").
                - body (Dict[str, Any]): Content body data.
                - postingDay (Optional[str]): Posting day for blog posts.
                - link (str): URL path to the content.
                - children (Optional[List[Dict[str, Any]]]): List of child content.
                - ancestors (Optional[List[Dict[str, Any]]]): List of ancestor content.

    Raises:
        TypeError: 
            If 'id' is not a string.
            If 'type' is not a string.
            If 'start' or 'limit' is not an integer.
        InvalidInputError: 
            If 'id' is an empty string.
            If 'type' is an empty string.
            If 'start' is negative or 'limit' is negative or zero.
        ValueError: If the parent content with the given id is not found.
    """
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")

    id = id.strip()
    if not id:
        raise InvalidInputError("Argument 'id' cannot be an empty string.")

    if not isinstance(type, str):
        raise TypeError("Argument 'type' must be a string.")

    type = type.strip()
    if not type:
        raise InvalidInputError("Argument 'type' cannot be an empty string.")

    if not isinstance(start, int) or isinstance(start, bool):
        raise TypeError("Argument 'start' must be an integer.")
    
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise TypeError("Argument 'limit' must be an integer.")

    if start and start < 0:
        raise InvalidInputError("Argument 'start' must be non-negative.")
    
    if limit and limit <= 0:
        raise InvalidInputError("Argument 'limit' must be non-negative.")

    parent = DB["contents"].get(id)
    if not parent:
        raise ValueError(f"Content with id={id} not found.")

    # Collect descendants of the specified type
    type_descendants = _collect_descendants(parent, type)

    # Apply pagination
    return type_descendants[start : start + limit]


@tool_spec(
    spec={
        'name': 'get_content_labels',
        'description': """ Returns a paginated list of content labels. If a prefix is provided,
        
        it filters labels that start with the given prefix. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The ID of the content to get labels for.'
                },
                'prefix': {
                    'type': 'string',
                    'description': 'Optional prefix to filter labels by.'
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination. Must be non-negative.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of labels to return. Must be positive.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_labels(
        id: str, prefix: Optional[str] = None, start: int = 0, limit: int = 200
) -> List[Dict[str, Any]]:  # Corrected return type annotation based on implementation
    """
    Returns a paginated list of content labels. If a prefix is provided,
    it filters labels that start with the given prefix.

    Args:
        id (str): The ID of the content to get labels for.
        prefix (Optional[str]): Optional prefix to filter labels by.
        start (int): The starting index for pagination. Must be non-negative.
        limit (int): The maximum number of labels to return. Must be positive.

    Returns:
        List[Dict[str, Any]]: List of label objects in the format
            -   label (str): The label name.

    Raises:
        TypeError: If 'id' is not a string, 'prefix' is not a string or None,
                   'start' is not an integer, or 'limit' is not an integer.
        ValueError: If 'start' is negative, 'limit' is not positive,
                    or if the content with the given id is not found (propagated from original logic).
    """
    # Input validation
    if not isinstance(id, str):
        raise TypeError("Parameter 'id' must be a string.")
    if prefix is not None and not isinstance(prefix, str):
        raise TypeError("Parameter 'prefix' must be a string or None.")
    if not isinstance(start, int):
        raise TypeError("Parameter 'start' must be an integer.")
    if start < 0:
        raise ValueError("Parameter 'start' must be non-negative.")
    if not isinstance(limit, int):
        raise TypeError("Parameter 'limit' must be an integer.")
    if limit <= 0:
        raise ValueError("Parameter 'limit' must be positive.")


    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id={id} not found.")

    # Retrieve labels or return empty list if none exist
    labels = DB["content_labels"].get(id, [])

    # Apply prefix filter if provided
    if prefix:
        labels = [label for label in labels if label.startswith(prefix)]

    # Apply pagination
    paginated_labels = labels[start: start + limit]

    # Return in expected response format
    return [{"label": label} for label in paginated_labels]


@tool_spec(
    spec={
        'name': 'add_content_labels',
        'description': """ Adds labels to a content item. If the content does not have existing labels,
        
        a new entry is created. Returns the updated list of labels. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The ID of the content to add labels to.'
                },
                'labels': {
                    'type': 'array',
                    'description': 'List of labels to add.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id',
                'labels'
            ]
        }
    }
)
def add_content_labels(id: str, labels: List[str]) -> List[Dict[str, Any]]:
    """
    Adds labels to a content item. If the content does not have existing labels,
    a new entry is created. Returns the updated list of labels.

    Args:
        id (str): The ID of the content to add labels to.
        labels (List[str]): List of labels to add.

    Returns:
        List[Dict[str, Any]]: List of updated label objects in the format
            - label (str): The label name.

    Raises:
        TypeError: If 'id' is not a string.
        TypeError: If 'labels' is not a list or contains non-string elements.
        ValueError: If the content with the given id is not found (from core logic).
    """
    # --- Input Validation ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")

    if not isinstance(labels, list):
        raise TypeError("Argument 'labels' must be a list.")

    for label_item in labels:
        if not isinstance(label_item, str):
            raise TypeError("All elements in 'labels' list must be strings.")
    # --- End Input Validation ---

    # --- Original Core Logic ---
    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id='{id}' not found.")

    # Ensure the content has an entry in the labels dictionary
    if id not in DB["content_labels"]:
        DB["content_labels"][id] = []

    # Add new labels, avoiding duplicates
    existing_labels = set(DB["content_labels"][id])
    new_labels_to_add = set(labels) # Renamed to avoid conflict with outer scope 'labels' if it were mutable and modified
    DB["content_labels"][id] = sorted(list(existing_labels.union(new_labels_to_add))) # sorted for predictable output

    # Return updated label list in expected response format
    return [{"label": label} for label in DB["content_labels"][id]]


@tool_spec(
    spec={
        'name': 'delete_content_labels',
        'description': """ Deletes labels from a content item. If a specific label is provided,
        
        only that label is deleted. Otherwise, all labels are deleted. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The ID of the content from which labels should be deleted.'
                },
                'label': {
                    'type': 'string',
                    'description': 'Optional specific label to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete_content_labels(id: str, label: Optional[str] = None) -> None:
    """
    Deletes labels from a content item. If a specific label is provided,
    only that label is deleted. Otherwise, all labels are deleted.

    Args:
        id (str): The ID of the content from which labels should be deleted.
        label (Optional[str]): Optional specific label to delete.

    Raises:
        TypeError: If 'id' is not a string, or if 'label' is not a string (when provided).
        InvalidInputError: If 'id' is an empty string.
        ContentNotFoundError: If the content with the given id is not found.
        LabelNotFoundError: If the content has no labels, or if the specified label is not found.
    """
    # --- Input Validation Start ---
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    if label is not None and not isinstance(label, str):
        raise TypeError("Argument 'label' must be a string if provided.")
    # --- Input Validation End ---
    
    content = DB["contents"].get(id)
    if not content:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")

    if id not in DB["content_labels"]:
        raise LabelNotFoundError(f"Content with id='{id}' has no labels.")

    if label:
        # Delete the specific label if it exists.
        if label in DB["content_labels"][id]:
            DB["content_labels"][id].remove(label)
            # Remove the key if no labels remain.
            if not DB["content_labels"][id]:
                del DB["content_labels"][id]
        else:
            raise LabelNotFoundError(f"Label {label} not found for content with id='{id}'.")
    else:
        # Delete all labels.
        del DB["content_labels"][id]


@tool_spec(
    spec={
        'name': 'get_content_properties',
        'description': 'Returns a paginated list of content properties for the specified content.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of properties to expand'
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of properties to return'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_properties(
    id: str, expand: Optional[str] = None, start: int = 0, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Returns a paginated list of content properties for the specified content.

    Args:
        id (str): The unique identifier of the content
        expand (Optional[str]): A comma-separated list of properties to expand
        start (int): The starting index for pagination
        limit (int): The maximum number of properties to return

    Returns:
        List[Dict[str, Any]]: A list of content property objects, where each property has:
            - key (str): The property key
            - value (Dict[str, Any]): The property value (can include any key-value pairs)
            - version (int): The property version number

    Raises:
        ValueError: If no properties for the specified content are found.
        TypeError: 
            If 'id' is not a string
            If 'start' or 'limit' is not an integer
        InvalidInputError: 
            If 'id' is an empty string, 
            If 'start' is negative, or 'limit' is negative or zero.
    """
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")

    id = id.strip()
    if not id:
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    if not isinstance(start, int) or isinstance(start, bool):
        raise TypeError("Argument 'start' must be an integer.")
    
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise TypeError("Argument 'limit' must be an integer.")
    
    if start and start < 0:
        raise InvalidInputError("Argument 'start' must be non-negative.")
    
    if isinstance(limit, int) and limit <= 0:
        raise InvalidInputError("Argument 'limit' must be positive.")
    
    # Get all properties for this content
    all_properties = []
    for prop_id, prop_data in DB["content_properties"].items():
        # Handle both formats: "content_id:key" and direct "content_id" 
        if prop_id.startswith(f"{id}:"):
            # Format: "content_id:key"
            key = prop_id.split(":", 1)[1]
            property_obj = {
                "key": key,
                "value": prop_data.get("value", {}),
                "version": prop_data.get("version", 1)
            }
            all_properties.append(property_obj)
        elif prop_id == id:
            # Direct format: content_id
            if prop_data is not None:
                property_obj = {
                    "key": prop_data.get("key", "default"),
                    "value": prop_data.get("value", {}),
                    "version": prop_data.get("version", 1)
                }
                all_properties.append(property_obj)
        elif prop_id.startswith(f"{id}_"):
            # Format: "content_id_prop_name" (another test format)
            key = prop_id.replace(f"{id}_", "")
            property_obj = {
                "key": key,
                "value": prop_data.get("value", {}),
                "version": prop_data.get("version", 1)
            }
            all_properties.append(property_obj)
    
    if not all_properties:
        raise ValueError(f"No properties found for content with id='{id}'")  # Restore original behavior for tests

    return all_properties[start : start + limit]


@tool_spec(
    spec={
        'name': 'create_content_property',
        'description': 'Creates a new property for a specified content item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content'
                },
                'body': {
                    'type': 'object',
                    'description': 'A dictionary representing the new content property to be created for the content item.',
                    'properties': {
                        'key': {
                            'type': 'string',
                            'description': 'The property key'
                        },
                        'value': {
                            'type': 'object',
                            'description': 'The property value, any key-value pair ({<key> : <value>})',
                            'properties': {},
                            'required': []
                        }
                    },
                    'required': [
                        'key',
                        'value'
                    ]
                }
            },
            'required': [
                'id',
                'body'
            ]
        }
    }
)
def create_content_property(id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new property for a specified content item.

    Args:
        id (str): The unique identifier of the content
        body (Dict[str, Any]): A dictionary representing the new content property to be created for the content item.
            - key (str): The property key
            - value (Dict[str, Any]): The property value, any key-value pair ({<key> : <value>})

    Returns:
        Dict[str, Any]: The newly created content property object with:
            - key (str): The property key
            - value (Dict[str, Any]): The property value
            - version (int): The property version number (starts at 1)

    Raises:
        TypeError: If 'id' is not a string or 'body' is not a dictionary.
        InvalidInputError: If 'id' is an empty string or 'key' is missing/empty.
        ContentNotFoundError: If the content with the specified ID is not found.
    """
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string.")
    
    if not isinstance(body, dict):
        raise TypeError("Argument 'body' must be a dictionary.")
    
    # Validate that key exists and is not empty
    key = body.get("key")
    if key is None:
        raise InvalidInputError("Missing required property 'key' in body.")
    if not isinstance(key, str):
        raise TypeError("Property 'key' must be a string.")
    if not key.strip():
        raise InvalidInputError("Property 'key' cannot be an empty string.")
    
    # Check if content exists
    content = DB["contents"].get(id)
    if not content:
        raise ContentNotFoundError(f"Content with id='{id}' not found.")
    
    # Extract value (can be any type, defaulting to empty dict)
    value = body.get("value", {})
    version = 1
    prop_key = f"{id}:{key}"
    DB["content_properties"][prop_key] = {
        "key": key,
        "value": value,
        "version": version,
    }
    return DB["content_properties"][prop_key]





@tool_spec(
    spec={
        'name': 'get_content_property_details',
        'description': 'Retrieves a specific property of a content item by its key.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content'
                },
                'key': {
                    'type': 'string',
                    'description': 'The key of the property to retrieve'
                },
                'expand': {
                    'type': 'string',
                    'description': """ A comma-separated list to expand property details.
                    Supported values: 'version', 'content' """
                }
            },
            'required': [
                'id',
                'key'
            ]
        }
    }
)
def get_content_property(
    id: str, key: str, expand: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves a specific property of a content item by its key.

    Args:
        id (str): The unique identifier of the content
        key (str): The key of the property to retrieve
        expand (Optional[str]): A comma-separated list to expand property details.
            Supported values: 'version', 'content'

    Returns:
        Dict[str, Any]: The content property object with:
            - key (str): The property key
            - value (Dict[str, Any]): The property value
            - version (int): The property version number
            If expand includes 'content', also includes:
            - content: The associated content object
            If expand includes 'version', also includes:
            - version: Detailed version information

    Raises:
        TypeError: If id or key are not strings
        ValueError:
            - If id or key are empty strings
            - If the content with the specified ID is not found
            - If the property with the specified key is not found
    """
    # Input validation
    if not isinstance(id, str):
        raise TypeError(f"id must be a string, but got {type(id).__name__}")
    if not isinstance(key, str):
        raise TypeError(f"key must be a string, but got {type(key).__name__}")
    if not id.strip():
        raise ValueError("id must not be empty")
    if not key.strip():
        raise ValueError("key must not be empty")
    
    # Expand validation
    if expand:
        valid_expand_values = {"content", "version"}
        expand_fields = [field.strip() for field in expand.split(",")]
        invalid_fields = set(expand_fields) - valid_expand_values
        if invalid_fields:
            raise ValueError(f"Invalid expand values: {invalid_fields}. Valid values are: {valid_expand_values}")
    
    # Check if content exists first
    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id={id} not found.")

    # Get property
    prop_key = f"{id}:{key}"
    prop = DB["content_properties"].get(prop_key)
    if not prop:
        raise ValueError(f"Property '{key}' not found for content {id}.")

    # Create a copy of the property to avoid modifying the stored version
    result = prop.copy()

    # Handle expand parameter
    if expand:
        expand_fields = [field.strip() for field in expand.split(",")]
        if "content" in expand_fields:
            result["content"] = content
        if "version" in expand_fields:
            version_number = result["version"]  # Store the original version number
            result["version"] = {
                "number": version_number,
                "when": get_iso_timestamp(),
                "message": prop.get("version_message", "Property version information"),
                "by": prop.get("last_modified_by", "system")
            }

    return result


@tool_spec(
    spec={
        'name': 'update_content_property',
        'description': 'Updates an existing content property with a new value and an incremented version.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content'
                },
                'key': {
                    'type': 'string',
                    'description': 'The key of the property to update'
                },
                'body': {
                    'type': 'object',
                    'description': 'Property update payload with:',
                    'properties': {
                        'value': {
                            'type': 'object',
                            'description': 'New property value payload (arbitrary JSON structure).',
                            'properties': {},
                            'required': []
                        },
                        'version': {
                            'type': 'object',
                            'description': 'Version object with:',
                            'properties': {
                                'number': {
                                    'type': 'integer',
                                    'description': 'New version number to apply (typically current+1).'
                                }
                            },
                            'required': [
                                'number'
                            ]
                        }
                    },
                    'required': [
                        'value',
                        'version'
                    ]
                }
            },
            'required': [
                'id',
                'key',
                'body'
            ]
        }
    }
)
def update_content_property(id: str, key: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing content property with a new value and an incremented version.

    Args:
        id (str): The unique identifier of the content
        key (str): The key of the property to update
        body (Dict[str, Any]): Property update payload with:
            - value (Dict[str, Any]): New property value payload (arbitrary JSON structure).
            - version (Dict[str, Any]): Version object with:
                - number (int): New version number to apply (typically current+1).

    Returns:
        Dict[str, Any]: The updated content property object with:
            - key (str): The property key
            - value (Dict[str, Any]): The updated property value
            - version (int): The incremented version number

    Raises:
        ValueError: If the content with the specified ID is not found; if the property with the specified key is not found.
    """
    prop_key = f"{id}:{key}"
    prop = DB["content_properties"].get(prop_key)
    if not prop:
        raise ValueError(f"Property '{key}' not found for content {id}.")
    new_version = body.get("version", {}).get("number", prop["version"] + 1)
    value = body.get("value", prop["value"])
    updated = {"key": key, "value": value, "version": new_version}
    DB["content_properties"][prop_key] = updated
    return updated


@tool_spec(
    spec={
        'name': 'delete_content_property',
        'description': 'Deletes a property from a content item identified by its key.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content.'
                },
                'key': {
                    'type': 'string',
                    'description': 'The key of the property to delete'
                }
            },
            'required': [
                'id',
                'key'
            ]
        }
    }
)
def delete_content_property(id: str, key: str) -> None:
    """
    Deletes a property from a content item identified by its key.

    Args:
        id (str): The unique identifier of the content.
        key (str): The key of the property to delete

    Raises:
        TypeError: If 'id' or 'key' is not a string.
        InvalidInputError: If 'id' or 'key' is an empty string or only whitespace.
        ValueError: If the property with the specified key for the given content ID is not found.
    """
    # Input validation
    if not isinstance(id, str):
        raise TypeError("Argument 'id' must be a string.")
    if not id.strip():
        raise InvalidInputError("Argument 'id' cannot be an empty string or only whitespace.")
    if not isinstance(key, str):
        raise TypeError("Argument 'key' must be a string.")
    if not key.strip():
        raise InvalidInputError("Argument 'key' cannot be an empty string or only whitespace.")

    prop_key = f"{id}:{key}"
    if prop_key in DB["content_properties"]:
        del DB["content_properties"][prop_key]
    else:
        raise ValueError(f"Property '{key}' not found for content {id}.")


@tool_spec(
    spec={
        'name': 'create_content_property_for_key',
        'description': 'Creates a new content property for a specified key when the version is 1.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the content.'
                },
                'key': {
                    'type': 'string',
                    'description': 'The key for the property.'
                },
                'body': {
                    'type': 'object',
                    'description': 'Property payload object with fields:',
                    'properties': {
                        'value': {
                            'type': 'object',
                            'description': 'JSON-serializable payload to store(arbitrary structure).',
                            'properties': {},
                            'required': []
                        },
                        'version': {
                            'type': 'object',
                            'description': 'Version object with:',
                            'properties': {
                                'number': {
                                    'type': 'integer',
                                    'description': 'Version number. Must be 1 for creation.'
                                }
                            },
                            'required': [
                                'number'
                            ]
                        }
                    },
                    'required': [
                        'value',
                        'version'
                    ]
                }
            },
            'required': [
                'id',
                'key',
                'body'
            ]
        }
    }
)
def create_content_property_for_key(
    id: str, key: str, body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates a new content property for a specified key when the version is 1.

    Args:
        id (str): The unique identifier of the content.
        key (str): The key for the property.
        body (Dict[str, Any]): Property payload object with fields:
            - value (Dict[str, Any]): JSON-serializable payload to store(arbitrary structure).
            - version (Dict[str, Any]): Version object with:
                - number (int): Version number. Must be 1 for creation.

    Returns:
        Dict[str, Any]: The created content property object with:
            - key (str): The property key
            - value (Dict[str, Any]): The property value
            - version (int): The property version number (must be 1)

    Raises:
        ValueError: If the content with the specified ID is not found.
    """
    # We'll treat it similarly to create_content_property but with the key param
    content = DB["contents"].get(id)
    if not content:
        raise ValueError(f"Content with id={id} not found.")
    version = body.get("version", {}).get("number", 1)
    value = body.get("value", {})
    prop_key = f"{id}:{key}"
    DB["content_properties"][prop_key] = {
        "key": key,
        "value": value,
        "version": version,
    }
    return DB["content_properties"][prop_key]


@tool_spec(
    spec={
        'name': 'get_content_restrictions_by_operation',
        'description': 'Retrieves all restrictions for a content item, grouped by operation type.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The ID of the content item.'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of additional fields to include. Defaults to None.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_content_restrictions_by_operation(
    id: str, expand: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves all restrictions for a content item, grouped by operation type.

    Args:
        id (str): The ID of the content item.
        expand (Optional[str]): A comma-separated list of additional fields to include. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing restrictions grouped by operation type.
            The structure is:
            - read (Dict[str, Any]):
                - restrictions (Dict[str, Any]):
                    - user (List[str]): List of usernames with read access.
                    - group (List[str]): List of group names with read access.
            - update (Dict[str, Any]):
                - restrictions (Dict[str, Any]):
                    - user (List[str]): List of usernames with update access.
                    - group (List[str]): List of group names with update access.

    Raises:
        ValueError: If the content with the specified ID is not found.
    """
    if id not in DB["contents"]:
        raise ValueError(f"Content with id={id} not found.")
    return {
        "read": {"restrictions": {"user": [], "group": []}},
        "update": {"restrictions": {"user": [], "group": []}},
    }


@tool_spec(
    spec={
        'name': 'get_content_restrictions_for_operation',
        'description': 'Retrieves restrictions for a specific operation on a content item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The ID of the content item.'
                },
                'operationKey': {
                    'type': 'string',
                    'description': 'The operation type (e.g., "read" or "update").'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of additional fields to include. Defaults to None.'
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting index for pagination. Defaults to 0.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of results to return. Defaults to 100.'
                }
            },
            'required': [
                'id',
                'operationKey'
            ]
        }
    }
)
def get_content_restrictions_for_operation(
    id: str,
    operationKey: str,
    expand: Optional[str] = None,
    start: Optional[int] = 0,
    limit: Optional[int] = 100,
) -> Dict[str, Any]:
    """
    Retrieves restrictions for a specific operation on a content item.

    Args:
        id (str): The ID of the content item.
        operationKey (str): The operation type (e.g., "read" or "update").
        expand (Optional[str]): A comma-separated list of additional fields to include. Defaults to None.
        start (Optional[int]): The starting index for pagination. Defaults to 0.
        limit (Optional[int]): The maximum number of results to return. Defaults to 100.

    Returns:
        Dict[str, Any]: A dictionary representing the restrictions for the specified operation with the structure:
            - operationKey (str): The operation type ("read" or "update").
            - restrictions (Dict[str, Any]): A dictionary containing restrictions for the specified operation with the structure:
                - user (List[str]): A list of usernames with access.
                - group (List[str]): A list of group names with access.

    Raises:
        ValueError: If the content with the specified ID is not found; if the operation key is invalid.
    """
    if id not in DB["contents"]:
        raise ValueError(f"Content with id={id} not found.")
    if operationKey not in ["read", "update"]:
        raise ValueError(f"OperationKey '{operationKey}' not supported.")
    return {"operationKey": operationKey, "restrictions": {"user": [], "group": []}}
