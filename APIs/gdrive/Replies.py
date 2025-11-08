from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
"""
Replies resource for Google Drive API simulation.

This module provides methods for managing replies to comments in the Google Drive API simulation.
"""

from typing import Dict, Any, Optional, Union
from .SimulationEngine.db import DB
from .SimulationEngine.models import BodyInputModel
from .SimulationEngine.counters import _next_counter
from pydantic import ValidationError as PydanticValidationError # For catching validation errors
from .SimulationEngine.custom_errors import ValidationError
from datetime import datetime

# BodyInputModel and AuthorModel are defined in the Pydantic Model Definitions section above
# and are assumed to be in scope here.


@tool_spec(
    spec={
        'name': 'create_comment_reply',
        'description': 'Creates a reply to a comment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment.'
                },
                'body': {
                    'type': 'object',
                    'description': 'The resource body for the reply to be created. Must contain:',
                    'properties': {
                        'content': {
                            'type': 'string',
                            'description': 'The content of the reply.'
                        },
                        'author': {
                            'type': 'object',
                            'description': 'Information about the author with:',
                            'properties': {
                                'displayName': {
                                    'type': 'string',
                                    'description': "The author's display name."
                                },
                                'emailAddress': {
                                    'type': 'string',
                                    'description': "The author's email address."
                                },
                                'photoLink': {
                                    'type': 'string',
                                    'description': "A link to the author's profile photo."
                                }
                            },
                            'required': [
                                'displayName',
                                'emailAddress'
                            ]
                        }
                    },
                    'required': [
                        'content'
                    ]
                }
            },
            'required': [
                'fileId',
                'commentId',
                'body'
            ]
        }
    }
)
def create(
    fileId: str,
    commentId: str,
    body: Dict[str, Union[str, Dict[str, str]]],
) -> Dict[str, Union[str, bool, Dict[str, str]]]:
    """Creates a reply to a comment.

    Args:
        fileId (str): The ID of the file.
        commentId (str): The ID of the comment.
        body (Dict[str, Union[str, Dict[str, str]]]): The resource body for the reply to be created. Must contain:
            - content (str): The content of the reply.
            - author (Optional[Dict[str, str]]): Information about the author with:
                - displayName (str): The author's display name.
                - emailAddress (str): The author's email address.
                - photoLink (Optional[str]): A link to the author's profile photo.

    Returns:
        Dict[str, Union[str, bool, Dict[str, str]]]: Dictionary containing the created reply with keys:
            - kind (str): Resource type identifier (e.g., 'drive#reply').
            - id (str): The ID of the reply.
            - fileId (str): The ID of the file.
            - commentId (str): The ID of the comment.
            - content (str): The content of the reply.
            - createdTime (str): The time the reply was created.
            - modifiedTime (str): The time the reply was last modified.
            - author (Dict[str, str]): Information about the author with keys:
                - displayName (str): The author's display name.
                - emailAddress (str): The author's email address.
                - photoLink (str): A link to the author's profile photo.
            - deleted (bool): Whether the reply has been deleted.

    Raises:
        TypeError: If 'fileId' or 'commentId' are not strings, or if 'body' is provided and is not a dictionary.
        ValidationError: If 'body' is provided and does not conform to the expected structure
                                  (e.g., missing 'content' or 'author', or 'author' has incorrect format).
        ValueError: If 'body' is None.
    """
    # --- Input Validation Start ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not isinstance(commentId, str):
        raise TypeError("commentId must be a string.")

    if body is None:
        raise ValueError("Request body is required to create a reply.")
    if not isinstance(body, dict):
        raise TypeError("body must be a dictionary if provided.")

    validated_body_model: Optional[BodyInputModel] = None
    if body is not None:
        if not isinstance(body, dict):
            raise TypeError("body must be a dictionary if provided.")

        try:
            validated_body_model = BodyInputModel(**body)
        except PydanticValidationError as e:
            # Re-raise Pydantic's ValidationError. It contains detailed information.
            raise e
    # --- Input Validation End ---

    # --- Core Logic Start ---
    userId = "me"
    reply_id_num = _next_counter("reply")
    reply_id = f"reply_{reply_id_num}"

    # Generate a dynamic timestamp in RFC3339 format
    current_time = datetime.utcnow().isoformat() + "Z"

    current_content = ""
    author_data = {}

    if validated_body_model:
        current_content = validated_body_model.content
        author_data = (
            validated_body_model.author.model_dump()
            if validated_body_model.author
            else {}
        )

    new_reply = {
        "kind": "drive#reply",
        "id": reply_id,
        "fileId": fileId,
        "commentId": commentId,
        "createdTime": current_time,
        "modifiedTime": current_time,
        "author": author_data,
        "content": current_content,
        "deleted": False,
    }

    DB["users"][userId]["replies"][reply_id] = new_reply

    return new_reply


@tool_spec(
    spec={
        'name': 'delete_comment_reply',
        'description': 'Deletes a reply.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment.'
                },
                'replyId': {
                    'type': 'string',
                    'description': 'The ID of the reply to delete.'
                }
            },
            'required': [
                'fileId',
                'commentId',
                'replyId'
            ]
        }
    }
)
def delete(fileId: str, commentId: str, replyId: str, ) -> None:
    """Deletes a reply.
    
    Args:
        fileId (str): The ID of the file.
        commentId (str): The ID of the comment.
        replyId (str): The ID of the reply to delete.
    """
    
    userId = 'me'  # Assuming 'me' for now
    DB['users'][userId]['replies'].pop(replyId, None)


@tool_spec(
    spec={
        'name': 'get_comment_reply',
        'description': """ Gets a reply by ID from a comment on a file.
        
        This function retrieves a specific reply to a comment on a Google Drive file.
        Deleted replies are excluded by default unless explicitly requested. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment.'
                },
                'replyId': {
                    'type': 'string',
                    'description': 'The ID of the reply to retrieve.'
                },
                'includeDeleted': {
                    'type': 'boolean',
                    'description': """ Whether to include deleted replies in the response.
                    Defaults to False. When False, deleted replies return None. """
                }
            },
            'required': [
                'fileId',
                'commentId',
                'replyId'
            ]
        }
    }
)
def get(fileId: str, commentId: str, replyId: str, includeDeleted: bool = False) -> Optional[Dict[str, Any]]:
    """
    Gets a reply by ID from a comment on a file.
    
    This function retrieves a specific reply to a comment on a Google Drive file.
    Deleted replies are excluded by default unless explicitly requested.
    
    Args:
        fileId (str): The ID of the file.
        commentId (str): The ID of the comment.
        replyId (str): The ID of the reply to retrieve.
        includeDeleted (bool): Whether to include deleted replies in the response.
            Defaults to False. When False, deleted replies return None.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the reply details with keys:
            - 'kind' (str): Resource type identifier ('drive#reply').
            - 'id' (str): The ID of the reply.
            - 'fileId' (str): The ID of the file.
            - 'commentId' (str): The ID of the comment.
            - 'content' (str): The content of the reply.
            - 'createdTime' (str): The time the reply was created (RFC3339 format).
            - 'modifiedTime' (str): The time the reply was last modified (RFC3339 format).
            - 'author' (Dict[str, str]): Information about the author with keys:
                - 'displayName' (str): The author's display name.
                - 'emailAddress' (str): The author's email address.
                - 'photoLink' (str): A link to the author's profile photo.
            - 'deleted' (bool): Whether the reply has been deleted.
        Returns None if the reply doesn't exist or is deleted and includeDeleted is False.
    
    Raises:
        TypeError: If fileId, commentId, or replyId are not strings, or if includeDeleted is not a boolean.
        ValidationError: If fileId, commentId, or replyId are empty strings.
    """

    # --- Input Validation Start ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not fileId:
        raise ValidationError("fileId cannot be empty.")
    
    if not isinstance(commentId, str):
        raise TypeError("commentId must be a string.")
    if not commentId:
        raise ValidationError("commentId cannot be empty.")
        
    if not isinstance(replyId, str):
        raise TypeError("replyId must be a string.")
    if not replyId:
        raise ValidationError("replyId cannot be empty.")
        
    if not isinstance(includeDeleted, bool):
        raise TypeError("includeDeleted must be a boolean.")
    # --- Input Validation End ---
    
    userId = 'me'  # Assuming 'me' for now
    
    # Get the reply from the database
    reply = DB['users'][userId]['replies'].get(replyId)
    print_log(f"DEBUG: Replies.get: Reply: {DB['users'][userId]['replies']}")
    # Check if reply exists
    if not reply:
        print_log(f"DEBUG: Replies.get: No reply found for replyId: {replyId}")
        return None
    
    # Validate that the reply belongs to the specified file and comment
    if reply.get('fileId') != fileId or reply.get('commentId') != commentId:
        print_log(f"DEBUG: Replies.get: Reply {replyId} does not belong to file {fileId} or comment {commentId}")
        return None
    
    # Check if reply is deleted and should be excluded
    if reply.get('deleted') and not includeDeleted:
        print_log(f"DEBUG: Replies.get: Reply {replyId} is deleted and includeDeleted is False")
        return None
        
    return reply

@tool_spec(
    spec={
        'name': 'list_comment_replies',
        'description': "Lists a comment's replies.",
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file. Must not be empty.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment. Must not be empty.'
                },
                'includeDeleted': {
                    'type': 'boolean',
                    'description': 'Whether to include deleted replies. Defaults to False.'
                },
                'pageSize': {
                    'type': 'integer',
                    'description': 'Maximum number of replies to return per page. Must be positive. Defaults to 20.'
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'Token for the next page of results. Defaults to an empty string.'
                }
            },
            'required': [
                'fileId',
                'commentId'
            ]
        }
    }
)
def list(fileId: str,
        commentId: str,
        includeDeleted: Optional[bool] = False,
        pageSize: Optional[int] = 20,
        pageToken: Optional[str] = '',
        ) -> Dict[str, Any]:
    """Lists a comment's replies.

    Args:
        fileId (str): The ID of the file. Must not be empty.
        commentId (str): The ID of the comment. Must not be empty.
        includeDeleted (Optional[bool]): Whether to include deleted replies. Defaults to False.
        pageSize (Optional[int]): Maximum number of replies to return per page. Must be positive. Defaults to 20.
        pageToken (Optional[str]): Token for the next page of results. Defaults to an empty string.

    Returns:
        Dict[str, Any]: Dictionary containing the list of replies with keys:
            - kind (str): Resource type identifier (e.g., 'drive#replyList').
            - replies (List[Dict[str, Any]]): List of reply objects with keys:
                - kind (str): Resource type identifier (e.g., 'drive#reply').
                - id (str): The ID of the reply.
                - fileId (str): The ID of the file.
                - commentId (str): The ID of the comment.
                - content (str): The content of the reply.
                - createdTime (str): The time the reply was created.
                - modifiedTime (str): The time the reply was last modified.
                - author (Dict[str, str]): Information about the author with keys:
                    - displayName (str): The author's display name.
                    - emailAddress (str): The author's email address.
                    - photoLink (str): A link to the author's profile photo.
                    - kind (str): Resource type identifier (e.g., 'drive#user').
                    - me (bool): Whether the author is the current user.
                    - permissionId (str): The ID of the permission associated with the author.
                - deleted (bool): Whether the reply has been deleted.
                - htmlContent (str): The content of the reply with HTML formatting.
                - action (str): The action the reply performed to the parent comment.
            - nextPageToken (str): Token for the next page of results.

    Raises:
        TypeError: If any input is not of the correct type.
        ValidationError: If any input is given invalid values.
    """
    # --- Input Validation Start ---
    if not isinstance(fileId, str):
        raise TypeError("fileId must be a string.")
    if not fileId:
        raise ValidationError("fileId cannot be empty.")
    if not fileId.strip():
        raise ValidationError("fileId cannot have only whitespace.")
    if " " in fileId:
        raise ValidationError("fileId cannot have whitespace.")

    if not isinstance(commentId, str):
        raise TypeError("commentId must be a string.")
    if not commentId:
        raise ValidationError("commentId cannot be empty.")
    if not commentId.strip():
        raise ValidationError("commentId cannot have only whitespace.")
    if " " in commentId:
        raise ValidationError("commentId cannot have whitespace.")

    if not isinstance(includeDeleted, bool):
        raise TypeError("includeDeleted must be a boolean.")

    if not isinstance(pageSize, int):
        raise TypeError("pageSize must be an integer.")
    if pageSize <= 0:
        raise ValidationError("pageSize must be a positive integer.")

    if not isinstance(pageToken, str):
        raise TypeError("pageToken must be a string.")
    # --- Input Validation End ---

    userId = 'me'  # Assuming 'me' for now

    # Fetch all replies for the user
    # This access might raise KeyError if keys are missing
    all_replies_dict = DB['users'][userId].get('replies', {})
    # Use list comprehension instead of the built-in list() function to avoid name collision
    all_replies_list = [r for r in all_replies_dict.values()]

    # Filter replies by fileId and commentId
    filtered_replies = [
        reply for reply in all_replies_list
        if reply.get('fileId') == fileId and reply.get('commentId') == commentId
    ]

    # Filter out deleted replies if includeDeleted is False
    if not includeDeleted:
        filtered_replies = [reply for reply in filtered_replies if not reply.get('deleted', False)]

    # Sort replies by createdTime to ensure consistent pagination
    filtered_replies.sort(key=lambda x: x.get('createdTime', ''))

    # Implement pagination using pageToken
    start_idx = 0
    if pageToken:
        try:
            # Attempt to convert pageToken to an integer if it's a non-empty string
            start_idx = int(pageToken)
            if start_idx < 0: # Page token as an index should not be negative
                start_idx = 0 # Or raise an error, but original code resets to 0
        except ValueError:
            # If pageToken is not a valid integer string, default to start
            start_idx = 0 # Or raise an error

    # Get the paginated slice of replies
    end_idx = start_idx + pageSize
    paginated_replies = filtered_replies[start_idx:end_idx]

    # Generate next page token if there are more replies
    next_page_token_val = str(end_idx) if end_idx < len(filtered_replies) else None

    # Format replies according to API specification
    formatted_replies = []
    for reply_data in paginated_replies:
        author_info = reply_data.get('author')
        if not author_info:
            # Attempt to get default author info if not present in reply_data
            user_about_info = DB['users'][userId].get('about', {}).get('user', {})
            author_info = {
                'displayName': user_about_info.get('displayName', 'Unknown User'),
                'emailAddress': user_about_info.get('emailAddress', ''),
                'photoLink': user_about_info.get('photoLink', ''),
                'kind': 'drive#user',
                'me': user_about_info.get('me', userId == 'me'),
                'permissionId': user_about_info.get('permissionId', '')
            }

        formatted_reply = {
            'kind': 'drive#reply',
            'id': reply_data['id'],
            'createdTime': reply_data['createdTime'],
            'modifiedTime': reply_data.get('modifiedTime', reply_data['createdTime']),
            'content': reply_data['content'],
            'htmlContent': reply_data.get('htmlContent', reply_data['content']),
            'deleted': reply_data.get('deleted', False),
            'action': reply_data.get('action', ''),
            'author': { # Ensure author is always structured as expected
                'displayName': author_info.get('displayName', 'Unknown User'),
                'emailAddress': author_info.get('emailAddress', ''),
                'photoLink': author_info.get('photoLink', ''),
                'kind': 'drive#user',
                'me': author_info.get('me', False), # Default 'me' to False unless specified
                'permissionId': author_info.get('permissionId', '')
            }
        }
        # Ensure fileId and commentId are part of the reply object as per docstring
        # These were missing in the original function's formatted_reply construction.
        formatted_reply['fileId'] = fileId
        formatted_reply['commentId'] = commentId
        formatted_replies.append(formatted_reply)

    return {
        'kind': 'drive#replyList',
        'replies': formatted_replies,
        'nextPageToken': next_page_token_val
    }


@tool_spec(
    spec={
        'name': 'update_comment_reply',
        'description': 'Updates a reply.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fileId': {
                    'type': 'string',
                    'description': 'The ID of the file.'
                },
                'commentId': {
                    'type': 'string',
                    'description': 'The ID of the comment.'
                },
                'replyId': {
                    'type': 'string',
                    'description': 'The ID of the reply to update.'
                },
                'body': {
                    'type': 'object',
                    'description': 'The reply resource with the fields to be updated. Any fields provided will overwrite the existing values.',
                    'properties': {},
                    'required': []
                }
            },
            'required': [
                'fileId',
                'commentId',
                'replyId'
            ]
        }
    }
)
def update(fileId: str,
            commentId: str,
            replyId: str,
            body: Optional[Dict[str, Any]] = None,
            ) -> Optional[Dict[str, Any]]:
    """Updates a reply.
    
    Args:
        fileId (str): The ID of the file.
        commentId (str): The ID of the comment.
        replyId (str): The ID of the reply to update.
        body (Optional[Dict[str, Any]]): The reply resource with the fields to be updated. Any fields provided will overwrite the existing values.
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the updated reply with keys:
            - 'kind' (str): Resource type identifier (e.g., 'drive#reply').
            - 'id' (str): The ID of the reply.
            - 'fileId' (str): The ID of the file.
            - 'commentId' (str): The ID of the comment.
            - 'content' (str): The content of the reply.
            - 'createdTime' (str): The time the reply was created.
            - 'modifiedTime' (str): The time the reply was last modified.
            - 'author' (Dict[str, str]): Information about the author with keys:
                - 'displayName' (str): The author's display name.
                - 'emailAddress' (str): The author's email address.
                - 'photoLink' (str): A link to the author's profile photo.
            - 'deleted' (bool): Whether the reply has been deleted.
    """
    
    userId = 'me'  # Assuming 'me' for now
    if body is None:
        body = {}
    existing = DB['users'][userId]['replies'].get(replyId)
    if not existing:
        return None
    existing.update(body)
    return existing
