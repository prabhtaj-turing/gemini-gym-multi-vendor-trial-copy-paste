"""
Comments resource for Google Drive API.

This module provides methods for managing comments in the Google Drive API.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.custom_errors import (PageSizeOutOfBoundsError, MalformedPageTokenError, \
    InvalidTimestampFormatError, NotFoundError, ValidationError, FileNotFoundError, PermissionDeniedError)
from .SimulationEngine.db import DB
from .SimulationEngine.models import CommentCreateInput, CommentUpdateBodyModel
from .SimulationEngine.counters import _next_counter


@tool_spec(
    spec={
        'name': 'create_file_comment',
        'description': """ Creates a body on a file.
        
        This function creates a new body on the specified Google Drive file with
        input validation and error handling. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to comment on.'
                },
                'body': {
                    'type': 'object',
                    'description': """ Dictionary containing comment properties. Supported keys: """,
                    'properties': {
                        'content': {
                            'type': 'string',
                            'description': 'The plain text content of the comment.'
                        },
                        'author': {
                            'type': 'object',
                            'description': 'Author information with keys:',
                            'properties': {
                                'displayName': {
                                    'type': 'string',
                                    'description': 'Display name of the author.'
                                },
                                'emailAddress': {
                                    'type': 'string',
                                    'description': 'Valid email address of the author.'
                                }
                            },
                            'required': [
                                'displayName',
                                'emailAddress'
                            ]
                        },
                        'quotedFileContent': {
                            'type': 'object',
                            'description': 'Quoted content with keys:',
                            'properties': {
                                'value': {
                                    'type': 'string',
                                    'description': 'The quoted content text (required if quotedFileContent provided).'
                                },
                                'mimeType': {
                                    'type': 'string',
                                    'description': 'MIME type of the quoted content (required if quotedFileContent provided).'
                                }
                            },
                            'required': [
                                'value',
                                'mimeType'
                            ]
                        },
                        'anchor': {
                            'type': 'string',
                            'description': 'Anchor point for the comment.'
                        },
                        'resolved': {
                            'type': 'boolean',
                            'description': 'Whether the comment is resolved (defaults to False).'
                        }
                    },
                    'required': [
                        'content'
                    ]
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def create(fileId: str,
          body: Dict[str, Any],
          ) -> Dict[str, Any]:
    """Creates a body on a file.
    
    This function creates a new body on the specified Google Drive file with
    input validation and error handling.
    
    Args:
        fileId (str): The ID of the file to comment on.
        body (Dict[str, Any]): Dictionary containing comment properties. Supported keys:
            - 'content' (str): The plain text content of the comment.
            - 'author' (Optional[Dict[str, Any]]): Author information with keys:
                - 'displayName' (str): Display name of the author.
                - 'emailAddress' (str): Valid email address of the author.
            - 'quotedFileContent' (Optional[Dict[str, Any]]): Quoted content with keys:
                - 'value' (str): The quoted content text (required if quotedFileContent provided).
                - 'mimeType' (str): MIME type of the quoted content (required if quotedFileContent provided).
            - 'anchor' (Optional[str]): Anchor point for the comment.
            - 'resolved' (Optional[bool]): Whether the comment is resolved (defaults to False).
    
    Returns:
        Dict[str, Any]: Dictionary containing the created comment with the following keys:
            - 'kind' (str): Resource type identifier ('drive#comment').
            - 'id' (str): Unique comment identifier.
            - 'fileId' (str): The ID of the file this comment belongs to.
            - 'content' (str): The plain text content of the comment.
            - 'htmlContent' (str): HTML-formatted content (same as content for plain text).
            - 'author' (Dict[str, Any]): Author information dictionary containing:
                {'kind': 'drive#user', 'displayName': str, 'emailAddress': str, 'me': bool, 'permissionId': str}
            - 'createdTime' (str): RFC 3339 timestamp when the comment was created.
            - 'modifiedTime' (str): RFC 3339 timestamp when the comment was last modified.
            - 'resolved' (bool): Whether the comment has been resolved.
            - 'deleted' (bool): Whether the comment has been deleted (always False for new comments).
            - 'replies' (List): Empty list of replies for new comments.
            - 'quotedFileContent' (Optional[Dict[str, Any]]): Quoted file content dictionary containing:
                {'value': str, 'mimeType': str} (only present if quoted content provided).
            - 'anchor' (Optional[str]): JSON string anchor point (only present if anchor provided).
    
    Raises:
        ValidationError: If any input parameter fails validation.
        FileNotFoundError: If the specified file does not exist.
        PermissionDeniedError: If the user lacks permission to comment on the file.
    """
    if not isinstance(body, dict):
        raise TypeError("body must be a dictionary.")
    
    # Prepare input data for validation
    validation_data = {
        'fileId': fileId,
        **body  # Include all other body fields
    }
    
    # Validate input using Pydantic model
    try:
        validated_input = CommentCreateInput(**validation_data)
    except PydanticValidationError as e:
        # Convert Pydantic validation errors to custom ValidationError
        error_messages = []
        for error in e.errors():
            field_name = '.'.join(str(loc) for loc in error['loc'])
            error_messages.append(f"{field_name}: {error['msg']}")
        raise ValidationError(f"Validation failed: {'; '.join(error_messages)}")
    
    # Ensure user exists
    userId = 'me'
    
    # Check if file exists - raise error if not found
    if fileId not in DB['users'][userId]['files']:
        raise FileNotFoundError(f"File not found: {fileId}")
    
    # Get file data for permission checking
    file_data = DB['users'][userId]['files'][fileId]
    
    # Get user email for permission checking
    user_email = DB['users'][userId]['about']['user'].get('emailAddress', '')
    
    # Check if user has permission to comment on this file
    can_comment = False
    
    # Check if user is in the owners list
    file_owners = file_data.get('owners', [])
    if user_email in file_owners:
        can_comment = True
    
    # Check permissions array for user's role
    if not can_comment:
        file_permissions = file_data.get('permissions', [])
        for permission in file_permissions:
            if permission.get('emailAddress') == user_email:
                user_role = permission.get('role', '')
                # Google Drive roles that allow commenting: commenter, editor, owner, writer
                if user_role in ['commenter', 'editor', 'owner', 'writer']:
                    can_comment = True
                    break
    
    # Enforce permission check - only allow commenting if user has proper permissions
    if not can_comment:
        raise PermissionDeniedError("User does not have permission to create comments on this file")
    
    # Generate unique comment ID
    comment_id_num = _next_counter('comment')
    comment_id = f"comment_{comment_id_num}"
    
    # Get current timestamp in RFC 3339 format
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    # Prepare author information - use provided author or default user info  
    author_info = {
        'kind': 'drive#user',
        'displayName': validated_input.author.displayName if validated_input.author else DB['users'][userId]['about']['user']['displayName'],
        'emailAddress': str(validated_input.author.emailAddress) if validated_input.author else DB['users'][userId]['about']['user']['emailAddress'],
        'me': True,
        'permissionId': 'me'
    }
    
    # Create the comment object
    new_comment = {
        'kind': 'drive#comment',
        'id': comment_id,
        'fileId': validated_input.fileId,
        'content': validated_input.content,
        'htmlContent': validated_input.content,
        'author': author_info,
        'createdTime': current_time,
        'modifiedTime': current_time,
        'resolved': validated_input.resolved or False,
        'deleted': False,
        'replies': []  # Empty replies list for new comments
    }
    
    # Add optional fields if provided
    if validated_input.quotedFileContent:
        new_comment['quotedFileContent'] = {
            'value': validated_input.quotedFileContent.value,
            'mimeType': validated_input.quotedFileContent.mimeType
        }
    
    if validated_input.anchor:
        new_comment['anchor'] = validated_input.anchor
    
    # Store the comment in the database
    if 'comments' not in DB['users'][userId]:
        DB['users'][userId]['comments'] = {}
    
    DB['users'][userId]['comments'][comment_id] = new_comment
    
    return new_comment

@tool_spec(
    spec={
        'name': 'get_file_comment',
        'description': 'Gets a comment by ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file the comment belongs to.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment to get.'
                },
                'includeDeleted': {
                    'type': 'boolean',
                    'description': 'Whether to include deleted comments.'
                }
            },
            'required': [
                'fileId',
                'commentId'
            ]
        }
    }
)
def get(fileId: str,
        commentId: str,
        includeDeleted: bool = False,
        ) -> Optional[Dict[str, Any]]:
    """Gets a comment by ID.
    
    Args:
        fileId (str): The ID of the file the comment belongs to.
        commentId (str): The ID of the comment to get.
        includeDeleted (bool): Whether to include deleted comments.
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the comment with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#comment').
            - 'id' (str): Comment ID.
            - 'fileId' (str): The ID of the file this comment belongs to.
            - 'content' (str): The content of the comment.
            - 'author' (Dict[str, Any]): Dictionary of author information.
            - 'quotedFileContent' (Dict[str, Any]): Dictionary of quoted content.
            - 'anchor' (str): The anchor point of the comment.
            - 'resolved' (bool): Whether the comment has been resolved.
            - 'createdTime' (str): The time at which the comment was created.
            - 'modifiedTime' (str): The time at which the comment was last modified.
            - 'deleted' (bool): Whether the comment has been deleted.
    """
    userId = 'me'
    comment = DB['users'][userId]['comments'].get(commentId)

    if comment and comment['fileId'] == fileId:
        return comment
    return None

@tool_spec(
    spec={
        'name': 'list_comments',
        'description': 'Lists comments for a file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file to list comments for. Cannot be empty.'
                },
                'includeDeleted': {
                    'type': 'boolean',
                    'description': """ Whether to include deleted comments.
                    If False, deleted comments are excluded from the response. Defaults to False. """
                },
                'pageSize': {
                    'type': 'integer',
                    'description': """ Maximum number of comments to return per page.
                    Must be between 1 and 100, inclusive. Defaults to 20. """
                },
                'pageToken': {
                    'type': 'string',
                    'description': """ Page token for continuing a previous list request.
                    Provides the starting point for pagination. Expected to be an integer string if provided.
                    Defaults to an empty string. """
                },
                'startModifiedTime': {
                    'type': 'string',
                    'description': """ The start time to filter comments by.
                    Only comments modified on or after this timestamp are returned.
                    Format: RFC 3339 timestamp (e.g., '2023-01-01T00:00:00Z').
                    Defaults to an empty string (no time filter). """
                }
            },
            'required': [
                'fileId'
            ]
        }
    }
)
def list(fileId: str,
         includeDeleted: Optional[bool] = False,
         pageSize: Optional[int] = 20,
         pageToken: Optional[str] = '',
         startModifiedTime: Optional[str] = '',
         ) -> Dict[str, Any]:
    """Lists comments for a file.

    Args:
        fileId (str): The ID of the file to list comments for. Cannot be empty.
        includeDeleted (Optional[bool]): Whether to include deleted comments.
            If False, deleted comments are excluded from the response. Defaults to False.
        pageSize (Optional[int]): Maximum number of comments to return per page.
            Must be between 1 and 100, inclusive. Defaults to 20.
        pageToken (Optional[str]): Page token for continuing a previous list request.
            Provides the starting point for pagination. Expected to be an integer string if provided.
            Defaults to an empty string.
        startModifiedTime (Optional[str]): The start time to filter comments by.
            Only comments modified on or after this timestamp are returned.
            Format: RFC 3339 timestamp (e.g., '2023-01-01T00:00:00Z').
            Defaults to an empty string (no time filter).

    Returns:
        Dict[str, Any]: Dictionary containing the list of comments with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#commentList').
            - 'nextPageToken' (str or None): Page token for the next page of results.
            - 'comments' (List[Dict[str, Any]]): List of comment objects. Each comment dictionary contains fields such as:
                - 'kind' (str): Resource type identifier (e.g., 'drive#comment').
                - 'id' (str): Comment ID.
                - 'fileId' (str): The ID of the file this comment belongs to.
                - 'content' (str): The content of the comment.
                - 'author' (Dict[str, Any]): Dictionary of author information.
                - 'quotedFileContent' (Dict[str, Any]): Dictionary of quoted content.
                - 'anchor' (str): The anchor point of the comment.
                - 'resolved' (bool): Whether the comment has been resolved.
                - 'createdTime' (str): The time at which the comment was created.
                - 'modifiedTime' (str): The time at which the comment was last modified.

    Raises:
        TypeError: If `fileId` is not a string, `includeDeleted` is not a boolean,
                   `pageSize` is not an integer, `pageToken` is not a string,
                   or `startModifiedTime` is not a string.
        ValueError: If `fileId` is an empty string.
        PageSizeOutOfBoundsError: If `pageSize` is not within the range [1, 100].
        MalformedPageTokenError: If `pageToken` is provided and is not a valid integer string.
        InvalidTimestampFormatError: If `startModifiedTime` is provided and is not a
                                     valid RFC 3339 timestamp string.
        ValueError: Propagated if the user 'me' (implicit userId for operations)
                  does not exist in the database.
    """
    # --- Input Validation ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    
    if not fileId.strip():
        raise ValueError("fileId cannot be an empty string.")

    if not isinstance(includeDeleted, bool):
        raise TypeError("includeDeleted must be a boolean.")

    if not isinstance(pageSize, int):
        raise TypeError("pageSize must be an integer.")
    if not (1 <= pageSize <= 100):
        raise PageSizeOutOfBoundsError(f"pageSize must be between 1 and 100, inclusive. Got: {pageSize}")

    if not isinstance(pageToken, str):
        raise TypeError("pageToken must be a string.")
    if pageToken:  # If not empty, validate its expected format (integer string)
        try:
            int(pageToken)
        except ValueError:
            raise MalformedPageTokenError(
                f"pageToken '{pageToken}' is not in the expected format (integer string)."
            )

    if not isinstance(startModifiedTime, str):
        raise TypeError("startModifiedTime must be a string.")
    if startModifiedTime:  # If not empty, validate format
        try:
            # Attempt to parse to validate format; the actual object is created later if needed.
            datetime.fromisoformat(startModifiedTime.replace('Z', '+00:00'))
        except ValueError as e:
            raise InvalidTimestampFormatError(
                f"startModifiedTime '{startModifiedTime}' is not a valid RFC 3339 timestamp. Error: {e}"
            )
    # --- End Input Validation ---

    userId = 'me'

    # Filter comments by file ID first
    comments_list = [
        comment for comment in DB['users'][userId]['comments'].values()
        if comment['fileId'] == fileId
    ]

    # Apply includeDeleted filter if specified
    if not includeDeleted:
        comments_list = [comment for comment in comments_list if not comment.get('deleted', False)]

    # Apply startModifiedTime filter if specified
    if startModifiedTime:
        # Validation ensures startModifiedTime is a valid RFC 3339 string if non-empty.
        start_time = datetime.fromisoformat(startModifiedTime.replace('Z', '+00:00'))
        comments_list = [
            comment for comment in comments_list
            if 'modifiedTime' in comment and
               datetime.fromisoformat(comment['modifiedTime'].replace('Z', '+00:00')) >= start_time
        ]

    # Sort comments by modifiedTime (or createdTime if not modified) in descending order (newest first)
    # Use createdTime as fallback to avoid defaulting to epoch for newly created comments
    comments_list.sort(
        key=lambda comment: comment.get('modifiedTime') or comment.get('createdTime'),
        reverse=True
    )

    # Implement pagination
    start_index = 0

    if pageToken:
        start_index = int(pageToken)

    end_index = start_index + pageSize

    page_comments = comments_list[start_index:end_index]

    next_page_token_val = str(end_index) if end_index < len(comments_list) else None

    return {
        'kind': 'drive#commentList',
        'comments': page_comments,
        'nextPageToken': next_page_token_val
    }


@tool_spec(
    spec={
        'name': 'update_file_comment',
        'description': 'Updates a comment with patch semantics.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file the comment belongs to.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment to update.'
                },
                'body': {
                    'type': 'object',
                    'description': """ The set of comment fields to be updated. Any fields provided 
                    in this dictionary will overwrite the existing values on 
                    the comment. Fields include: """,
                    'properties': {
                        'content': {
                            'type': 'string',
                            'description': 'The content of the comment.'
                        },
                        'author': {
                            'type': 'object',
                            'description': 'Dictionary of author information.',
                            'properties': {
                                'displayName': {
                                    'type': 'string',
                                    'description': 'The display name of the author.'
                                },
                                'emailAddress': {
                                    'type': 'string',
                                    'description': 'The email address of the author.'
                                }
                            },
                            'required': []
                        },
                        'quotedFileContent': {
                            'type': 'object',
                            'description': 'Dictionary of quoted content.',
                            'properties': {
                                'value': {
                                    'type': 'string',
                                    'description': 'The quoted content.'
                                },
                                'mimeType': {
                                    'type': 'string',
                                    'description': 'The MIME type of the quoted content.'
                                }
                            },
                            'required': []
                        },
                        'anchor': {
                            'type': 'string',
                            'description': 'The anchor point of the comment.'
                        },
                        'resolved': {
                            'type': 'boolean',
                            'description': 'Whether the comment has been resolved.'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'fileId',
                'commentId'
            ]
        }
    }
)
def update(
    fileId: str,
    commentId: str,
    body: Optional[Dict[str, Union[str, bool, Dict[str, Union[str, None]]]]] = None,
) -> Optional[Dict[str, Union[str, bool, Dict[str, Union[str, None]]]]]:
    """Updates a comment with patch semantics.

    Args:
        fileId (str): The ID of the file the comment belongs to.
        commentId (str): The ID of the comment to update.
        body (Optional[Dict[str, Union[str, bool, Dict[str, Union[str, None]]]]]): 
            The set of comment fields to be updated. Any fields provided 
            in this dictionary will overwrite the existing values on 
            the comment. Fields include:
            
            - content (Optional[str]): The content of the comment.
            - author (Optional[dict]): Dictionary of author information.
                - displayName (Optional[str]): The display name of the author.
                - emailAddress (Optional[str]): The email address of the author.
            - quotedFileContent (Optional[dict]): Dictionary of quoted content.
                - value (Optional[str]): The quoted content.
                - mimeType (Optional[str]): The MIME type of the quoted content.
            - anchor (Optional[str]): The anchor point of the comment.
            - resolved (Optional[bool]): Whether the comment has been resolved.

    Returns:
        Optional[Dict[str, Union[str, bool, Dict[str, Union[str, None]]]]]: 
        Dictionary containing the updated comment. Fields include:

            - kind (str): Resource type identifier (e.g., 'drive#comment').
            - id (str): Comment ID.
            - fileId (str): The ID of the file this comment belongs to.
            - content (Optional[str]): The content of the comment.
            - author (Optional[dict]): Dictionary of author information.
            - quotedFileContent (Optional[dict]): Dictionary of quoted content.
            - anchor (Optional[str]): The anchor point of the comment.
            - resolved (Optional[bool]): Whether the comment has been resolved.
            - createdTime (str): The time at which the comment was created.
            - modifiedTime (str): The time at which the comment was last modified.

    Raises:
        ValidationError: If the provided body data does not conform to the expected structure,
                        including invalid email addresses in the author field.
    """
    userId = 'me'

    if body is None:
        body = {}

    # Validate the body using Pydantic model for email validation
    try:
        validated_body = CommentUpdateBodyModel(**body)
        body = validated_body.model_dump(exclude_unset=True)
    except PydanticValidationError as e:
        raise ValidationError(f"Invalid comment update data: {e}")

    comment = DB['users'][userId]['comments'].get(commentId)

    if not comment or comment['fileId'] != fileId:
        return None

    comment.update(body)
    comment['modifiedTime'] = '2023-10-27T12:00:01.000Z'  # Updated time
    return comment

@tool_spec(
    spec={
        'name': 'delete_file_comment',
        'description': """ Deletes a comment from a file in Google Drive.
        
        This function permanently removes a comment from a file. The comment is
        identified by its `commentId` and the `fileId` of the file it is associated
        with. If the comment does not exist or the provided IDs are incorrect, an error will be raised. 
        It also deletes all associated replies to maintain referential integrity. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file the comment belongs to.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment to delete.'
                }
            },
            'required': [
                'fileId',
                'commentId'
            ]
        }
    }
)
def delete(fileId: str,
          commentId: str) -> Dict[str, str]:
    """Deletes a comment from a file in Google Drive.

    This function permanently removes a comment from a file. The comment is
    identified by its `commentId` and the `fileId` of the file it is associated
    with. If the comment does not exist or the provided IDs are incorrect, an error will be raised. 
    It also deletes all associated replies to maintain referential integrity.

    Args:
        fileId (str): The ID of the file the comment belongs to.
        commentId (str): The ID of the comment to delete.

    Returns:
        Dict[str, str]: Dictionary containing:
            - 'status' (str): Success status indicator
            - 'message' (str): Confirmation message

    Raises:
        TypeError: If `fileId` or `commentId` is not a string.
        ValueError: If `fileId` or `commentId` is an empty string.
        NotFoundError: If the comment is not found.
    """
    # --- Input Validation Start ---
    if not isinstance(fileId, str):
        raise TypeError(f"Argument 'fileId' must be a string, got {type(fileId).__name__}.")

    if not fileId.strip():
        raise ValueError(f"Argument 'fileId' must be a non-empty string.")

    if not isinstance(commentId, str):
        raise TypeError(f"Argument 'commentId' must be a string, got {type(commentId).__name__}.")

    if not commentId.strip():
        raise ValueError(f"Argument 'commentId' must be a non-empty string.")
    # --- Input Validation End ---

    userId = 'me'

    comment = DB['users'][userId]['comments'].get(commentId)

    if not comment or comment['fileId'] != fileId:
        raise NotFoundError(f"Comment with ID '{commentId}' not found on file '{fileId}'.")
    
    # Cascade delete: Remove all replies associated with this comment
    # Find all reply IDs that reference this commentId
    replies_to_delete = [
        reply_id for reply_id, reply_data in DB['users'][userId]['replies'].items()
        if reply_data.get('commentId') == commentId
    ]
    
    # Delete each reply
    for reply_id in replies_to_delete:
        DB['users'][userId]['replies'].pop(reply_id, None)
    
    # Now delete the comment itself
    DB['users'][userId]['comments'].pop(commentId, None)

    return {"status": "success", "message": "Comment was successfully deleted."}