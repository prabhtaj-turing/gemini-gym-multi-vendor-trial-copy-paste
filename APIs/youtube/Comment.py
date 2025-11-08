from typing import Dict, List, Optional, Union
import re
import copy
from common_utils.tool_spec_decorator import tool_spec
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id
from youtube.SimulationEngine.models import CommentUpdateModel, CommentSnippetModel, CommentInsertModel
from pydantic import ValidationError
from youtube.SimulationEngine.custom_errors import InvalidCommentIdError, InvalidModerationStatusError, InvalidBanAuthorError, InvalidCommentInsertError


"""
    Handles YouTube Comment API operations.
    
    This class provides methods to manage comments on YouTube videos,
    including creating, updating, deleting, and moderating comments.
"""


@tool_spec(
    spec={
    "name": "set_comment_moderation_status",
    "description": "Sets the moderation status of a comment. This function allows channel or video owners to moderate comments by setting their moderation status. The moderation status determines whether a comment is visible to the public, held for review, or rejected.",
    "parameters": {
        "type": "object",
        "properties": {
            "comment_id": {
                "type": "string",
                "description": "The ID of the comment to moderate. Must be a non-empty string that uniquely identifies an existing comment in the database."
            },
            "moderation_status": {
                "type": "string",
                "description": "The new moderation status for the comment. Valid values are: - \"heldForReview\": Marks a comment as awaiting review by a moderator - \"published\": Clears a comment for public display - \"rejected\": Rejects a comment as being unfit for display"
            },
            "ban_author": {
                "type": "boolean",
                "description": "If True, bans the author of the comment when rejecting it. This parameter is only effective when moderation_status is \"rejected\". Defaults to None."
            }
        },
        "required": [
            "comment_id",
            "moderation_status"
        ]
    }
}
)
def set_moderation_status(
    comment_id: str, moderation_status: str, ban_author: Optional[bool] = None
) -> Dict[str, Union[bool, str, Dict[str, Union[str, bool, Dict[str, str]]]]]:
    """
    Sets the moderation status of a comment.

    This function allows channel or video owners to moderate comments by setting their
    moderation status. The moderation status determines whether a comment is visible
    to the public, held for review, or rejected.

    Args:
        comment_id (str): The ID of the comment to moderate. Must be a non-empty string
                         that uniquely identifies an existing comment in the database.
        moderation_status (str): The new moderation status for the comment. 
                               Valid values are:
                               - "heldForReview": Marks a comment as awaiting review by a moderator
                               - "published": Clears a comment for public display
                               - "rejected": Rejects a comment as being unfit for display
        ban_author (Optional[bool]): If True, bans the author of the comment when rejecting it.
                                    This parameter is only effective when moderation_status is "rejected".
                                    Defaults to None.


    Returns:
        Dict[str, Union[bool, str, Dict[str, Union[str, bool, Dict[str, str]]]]]: A dictionary containing the operation result:
            - If the comment is found and updated successfully:
                - success (bool): True
                - comment (Dict[str, Union[str, bool, Dict[str, str]]]): The updated comment object containing:
                    - id (str): The comment ID
                    - snippet (Dict[str, str]): The comment snippet data
                        - videoId (str): The ID of the video that the comment is on.
                        - parentId (Optional[str]): The ID of the parent comment, if this is a reply.
                    - moderationStatus (str): The new moderation status
                    - bannedAuthor (bool): Whether the author is banned
            - If the comment is not found:
                - error (str): "Comment not found"

    Raises:
        InvalidCommentIdError: If comment_id is not a string, is empty, or contains only whitespace.
        InvalidModerationStatusError: If moderation_status is not a string or not one of the valid values.
        InvalidBanAuthorError: If ban_author is not a boolean or None.
    """
    # Inline validation for input parameters
    if not isinstance(comment_id, str) or not comment_id.strip():
        raise InvalidCommentIdError("comment_id must be a non-empty string")

    valid_statuses = {"heldForReview", "published", "rejected"}
    if not isinstance(moderation_status, str) or moderation_status not in valid_statuses:
        raise InvalidModerationStatusError("moderation_status must be one of 'heldForReview', 'published', 'rejected'")

    if ban_author is not None and not isinstance(ban_author, bool):
        raise InvalidBanAuthorError("ban_author must be a boolean or None")

    # Check if comment exists in database
    if comment_id not in DB.get("comments", {}):
        return {"error": "Comment not found"}

    # Update the comment's moderation status
    DB["comments"][comment_id]["moderationStatus"] = moderation_status

    # Ban author if requested and status is rejected
    if ban_author and moderation_status == "rejected":
        DB["comments"][comment_id]["bannedAuthor"] = True

    return {"success": True, "comment": DB["comments"][comment_id]}



@tool_spec(
    spec={
    "name": "delete_comment",
    "description": "Deletes a comment.",
    "parameters": {
        "type": "object",
        "properties": {
            "comment_id": {
                "type": "string",
                "description": "The ID of the comment to delete."
            }
        },
        "required": [
            "comment_id"
        ]
    }
}
)
def delete(comment_id: str) -> Dict[str, Union[bool, str]]:
    """
    Deletes a comment.

    Args:
        comment_id (str): The ID of the comment to delete.

    Returns:
        Dict[str, Union[bool, str]]: A dictionary containing:
            - If the comment is successfully deleted:
                - success (bool): True
            - If the comment is not found:
                - error (str): Error message

    Raises:
        InvalidCommentIdError: Raised if comment_id is not a string, is empty, or contains only whitespace. 
    """
    if not isinstance(comment_id, str):
        raise InvalidCommentIdError("Comment ID must be a string.")
    if not comment_id.strip():
        raise InvalidCommentIdError("Comment ID cannot be empty or contain only whitespace.")

    if comment_id not in DB["comments"]:
        return {"error": "Comment not found"}

    del DB["comments"][comment_id]
    return {"success": True}


@tool_spec(
    spec={
    "name": "add_comment",
    "description": "Inserts a new comment. This function creates a new comment with the specified properties and adds it to the database. The comment is assigned a unique ID and stored with the provided metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be a non-empty string."
            },
            "snippet": {
                "type": "object",
                "description": "The snippet object contains details about the comment. Defaults to None. Contains the following fields:",
                "properties": {
                    "videoId": {
                        "type": "string",
                        "description": "The ID of the video that the comment is on."
                    },
                    "parentId": {
                        "type": "string",
                        "description": "The ID of the parent comment, if this is a reply."
                    }
                },
                "required": []
            },
            "moderation_status": {
                "type": "string",
                "description": "The initial moderation status for the comment. Defaults to \"published\". Must be one of: - \"heldForReview\": Comment is held for review - \"published\": Comment is published and visible (default) - \"rejected\": Comment is rejected and hidden"
            },
            "banned_author": {
                "type": "boolean",
                "description": "Whether the author of the comment is banned. Defaults to False."
            }
        },
        "required": [
            "part"
        ]
    }
}
)
def insert(
    part: str,
    snippet: Optional[Dict[str, str]] = None,
    moderation_status: str = "published",
    banned_author: bool = False,
) -> Dict[str, Union[bool, str, Dict[str, Union[str, bool, Dict[str, str]]]]]:
    """
    Inserts a new comment.

    This function creates a new comment with the specified properties and adds it to the database.
    The comment is assigned a unique ID and stored with the provided metadata.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include.
                   Must be a non-empty string.
        snippet (Optional[Dict[str, str]]): The snippet object contains details about the comment. Defaults to None. Contains the following fields:
                                - videoId (Optional[str]): The ID of the video that the comment is on.
                                - parentId (Optional[str]): The ID of the parent comment, if this is a reply.
        moderation_status (str): The initial moderation status for the comment. Defaults to "published". Must be one of:
                               - "heldForReview": Comment is held for review
                               - "published": Comment is published and visible (default)
                               - "rejected": Comment is rejected and hidden
        banned_author (bool): Whether the author of the comment is banned. Defaults to False.


    Returns:
        Dict[str, Union[bool, str, Dict[str, Union[str, bool, Dict[str, str]]]]]: A dictionary containing one of the following structures:
            - If insertion is successful:
                - success (bool): True indicating successful insertion
                - comment (Dict[str, Union[str, bool, Dict[str, str]]]): The newly created comment object with keys:
                    - id (str): Unique comment identifier
                    - snippet (Dict[str, str]): Comment details and metadata containing the fields
                        - videoId (Optional[str]): The ID of the video that the comment is on.
                        - parentId (Optional[str]): The ID of the parent comment, if this is a reply.
                    - moderationStatus (str): Current moderation status ("heldForReview", "published", or "rejected")
                    - bannedAuthor (bool): Whether the author is banned
            - If an error occurs:
                - error (str): Detailed error message explaining the validation failure

    Raises:
        InvalidCommentInsertError: If input parameters fail validation including:
                                 - Invalid types (e.g., part is not a string, snippet is not a dictionary)
                                 - Invalid values (e.g., empty part parameter, invalid moderation status)
                                 - Malformed data or constraint violations
                                 - Pydantic validation failures
    """
    # Input validation using Pydantic model
    try:
        # Validate snippet separately if provided
        validated_snippet = None
        if snippet is not None:
            if not isinstance(snippet, dict):
                raise InvalidCommentInsertError("snippet must be a dictionary")
            validated_snippet = CommentSnippetModel(**snippet)

        # Validate all input parameters using Pydantic model
        validated_data = CommentInsertModel(
            part=part,
            snippet=validated_snippet,
            moderation_status=moderation_status,
            banned_author=banned_author
        )
    except (ValidationError, TypeError, ValueError) as e:
        raise InvalidCommentInsertError(str(e))

    # Initialize database structure if needed
    if "comments" not in DB:
        DB["comments"] = {}

    new_id = str(len(DB["comments"]) + 1)
    
    # Use validated snippet data, defaulting to empty dict if None
    snippet_data = {}
    if validated_snippet:
        snippet_data = validated_snippet.model_dump(exclude_none=True)
    elif snippet:
        snippet_data = snippet

    # Create new comment object
    new_comment = {
        "id": new_id,
        "snippet": snippet_data,
        "moderationStatus": validated_data.moderation_status,
        "bannedAuthor": validated_data.banned_author,
    }

    # Store comment in database
    DB["comments"][new_id] = new_comment
    
    return {"success": True, "comment": new_comment}


@tool_spec(
    spec={
    "name": "list_comments",
    "description": "Retrieves a list of comments with optional filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Cannot be empty."
            },
            "comment_id": {
                "type": "string",
                "description": "The id parameter specifies a comma-separated list of comment IDs for the resources that are being retrieved. Defaults to None."
            },
            "parent_id": {
                "type": "string",
                "description": "The parentId parameter specifies the ID of the comment for which replies should be retrieved. Defaults to None."
            },
            "max_results": {
                "type": "integer",
                "description": "The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to None."
            },
            "page_token": {
                "type": "string",
                "description": "The pageToken parameter identifies a specific page in the result set that should be returned. Defaults to None."
            },
            "text_format": {
                "type": "string",
                "description": "The textFormat parameter specifies the format of the text in the comment. Valid values are \"html\" (default) and \"plainText\". Defaults to None."
            }
        },
        "required": [
            "part"
        ]
    }
}
)
def list(
    part: str,
    comment_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    text_format: Optional[str] = None,
) -> Dict[str, Union[List[Dict[str, Union[str, bool, Dict[str, str]]]], str]]:
    """
    Retrieves a list of comments with optional filters.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Cannot be empty.
        comment_id (Optional[str]): The id parameter specifies a comma-separated list of comment IDs for the resources that are being retrieved. Defaults to None.
        parent_id (Optional[str]): The parentId parameter specifies the ID of the comment for which replies should be retrieved. Defaults to None.
        max_results (Optional[int]): The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to None.
        page_token (Optional[str]): The pageToken parameter identifies a specific page in the result set that should be returned. Defaults to None.
        text_format (Optional[str]): The textFormat parameter specifies the format of the text in the comment. Valid values are "html" (default) and "plainText". Defaults to None.

    Returns:
        Dict[str, Union[List[Dict[str, Union[str, bool, Dict[str, str]]]], str]]: A dictionary containing:
        - If successful:
            - items (List[Dict[str, Union[str, bool, Dict[str, str]]]]): A list of comment resources matching the filters:
                - id (str) - unique comment identifier
                - snippet (Dict[str, str]): A dictionary containing details about the comment.
                    - videoId (str): The ID of the video that the comment is on.
                    - parentId (Optional[str]): The ID of the parent comment, if it is a reply.
                - moderationStatus (str) - moderation status of the comment
                - bannedAuthor (bool) - whether the author is banned
        - If an error occurs:
            - error (str): Error message

    Raises:
        None: This function returns error messages in the response dictionary instead of raising exceptions.
    """
    # Validate required parameters
    if not part:
        return {"error": "Part parameter is required and cannot be empty"}

    if not isinstance(part, str):
        return {"error": "Part parameter must be a string"}

    # Parse and validate part parameter
    valid_parts = ["id", "snippet", "moderationStatus", "bannedAuthor"]
    requested_parts = [p.strip() for p in part.split(",")]

    for requested_part in requested_parts:
        if requested_part not in valid_parts:
            return {
                "error": f"Invalid part parameter: {requested_part}. Valid values are: {', '.join(valid_parts)}"
            }

    # Validate optional parameters
    if comment_id is not None and not isinstance(comment_id, str):
        return {"error": "comment_id parameter must be a string"}

    if parent_id is not None and not isinstance(parent_id, str):
        return {"error": "parent_id parameter must be a string"}

    if max_results is not None:
        if not isinstance(max_results, int):
            return {"error": "max_results parameter must be an integer"}
        if max_results <= 0:
            return {"error": "max_results parameter must be a positive integer"}

    if page_token is not None and not isinstance(page_token, str):
        return {"error": "page_token parameter must be a string"}

    if text_format is not None:
        if not isinstance(text_format, str):
            return {"error": "text_format parameter must be a string"}
        if text_format not in ["html", "plainText"]:
            return {"error": "text_format parameter must be 'html' or 'plainText'"}

    # Parse comment IDs if provided (comma-separated)
    comment_ids = []
    if comment_id:
        comment_ids = [id.strip() for id in comment_id.split(",")]

    # Access comments from DB
    comments_dict = dict(DB.get("comments", {}))
    filtered_comments = []

    # Convert dictionary values to list and apply filters
    for comment_key, comment_data in comments_dict.items():
        # Filter by specific comment IDs (comma-separated list)
        if comment_ids and comment_data["id"] not in comment_ids:
            continue

        # Filter by parent ID for replies
        if parent_id and comment_data.get("snippet", {}).get("parentId") != parent_id:
            continue

        # Apply text format transformation if specified
        if text_format == "plainText":
            # Create a copy to avoid modifying the original data
            comment_copy = comment_data.copy()
            snippet = comment_copy.get("snippet", {})
            if "textDisplay" in snippet:
                # Simple HTML to plain text conversion (basic implementation)
                snippet["textDisplay"] = (
                    snippet["textDisplay"].replace("<br>", "\n").replace("<br/>", "\n")
                )
                # Remove other HTML tags (basic implementation)
                snippet["textDisplay"] = re.sub(r"<[^>]+>", "", snippet["textDisplay"])
            comment_data = comment_copy

        # Filter response properties based on part parameter
        filtered_comment = {}

        if "id" in requested_parts:
            filtered_comment["id"] = comment_data.get("id")

        if "snippet" in requested_parts:
            filtered_comment["snippet"] = comment_data.get("snippet", {})

        # Only include additional properties if explicitly requested
        if "moderationStatus" in requested_parts and "moderationStatus" in comment_data:
            filtered_comment["moderationStatus"] = comment_data["moderationStatus"]

        if "bannedAuthor" in requested_parts and "bannedAuthor" in comment_data:
            filtered_comment["bannedAuthor"] = comment_data["bannedAuthor"]

        filtered_comments.append(filtered_comment)

    # Apply pagination logic
    if page_token:
        # Basic pagination implementation (simplified)
        # In a real implementation, you'd parse the token to determine the starting position
        try:
            start_index = int(page_token)
            filtered_comments = filtered_comments[start_index:]
        except (ValueError, TypeError):
            return {"error": "Invalid page_token format"}

    # Apply max_results limit
    if max_results:
        filtered_comments = filtered_comments[:max_results]

    return {"items": filtered_comments}


@tool_spec(
    spec={
    "name": "mark_comment_as_spam",
    "description": "Marks a comment as spam.",
    "parameters": {
        "type": "object",
        "properties": {
            "comment_id": {
                "type": "string",
                "description": "The ID of the comment to mark as spam. Must be a non-empty string that uniquely identifies an existing comment in the database."
            }
        },
        "required": [
            "comment_id"
        ]
    }
}
)
def mark_as_spam(comment_id: str) -> Dict[str, Union[bool, Dict[str, Union[str, bool, Dict[str, str]]]]]:
    """
    Marks a comment as spam.

    Args:
        comment_id (str): The ID of the comment to mark as spam. Must be a non-empty string that uniquely identifies an existing comment in the database.

    Returns:
        Dict[str, Union[bool, Dict[str, Union[str, bool, Dict[str, str]]]]]: A dictionary containing:
                - success (bool): True
                - comment (Dict[str, Union[str, bool, Dict[str, str]]]): The updated comment object
                    - id (str): Unique comment identifier
                    - snippet (Dict[str, str]): Comment details and metadata containing the fields
                        - videoId (Optional[str]): The ID of the video that the comment is on.
                        - parentId (Optional[str]): The ID of the parent comment, if this is a reply.
                    - moderationStatus (str): Current moderation status ("heldForReview", "published", or "rejected")
                    - bannedAuthor (bool): Whether the author is banned

    Raises:
        ValueError: If comment_id is None,
                    or if comment_id is empty or contains only whitespace.
        TypeError: If comment_id is not a string.
        InvalidCommentIdError: If comment_id is not found in the database.
    """
    if comment_id is None:
        raise ValueError("comment_id is required")
    if not isinstance(comment_id, str):
        raise TypeError("comment_id must be a non-empty string")
    if not comment_id.strip():
        raise ValueError("comment_id cannot be empty or contain only whitespace")
    if comment_id not in DB.get("comments", {}):
        raise InvalidCommentIdError("Comment not found in the database.")

    DB["comments"][comment_id]["moderationStatus"] = "heldForReview"
    return {"success": True, "comment": DB["comments"][comment_id]}


@tool_spec(
    spec={
    "name": "update_comment",
    "description": "Updates an existing comment.",
    "parameters": {
        "type": "object",
        "properties": {
            "comment_id": {
                "type": "string",
                "description": "The ID of the comment to update. Must be a non-empty string."
            },
            "snippet": {
                "type": "object",
                "description": "The comment snippet object with fields to update. Defaults to None. Contains the following fields:",
                "properties": {
                    "videoId": {
                        "type": "string",
                        "description": "ID of the associated video."
                    },
                    "parentId": {
                        "type": "string",
                        "description": "ID of the parent comment for replies; None for top-level comments."
                    }
                },
                "required": []
            },
            "moderation_status": {
                "type": "string",
                "description": "The new moderation status to set. Defaults to None. Valid values: - \"heldForReview\": Comment is held for review - \"published\": Comment is published and visible - \"rejected\": Comment is rejected and hidden"
            },
            "banned_author": {
                "type": "boolean",
                "description": "Whether the author of the comment is banned. Defaults to None."
            }
        },
        "required": [
            "comment_id"
        ]
    }
}
)
def update(
    comment_id: str,
    snippet: Optional[Dict[str, str]] = None,
    moderation_status: Optional[str] = None,
    banned_author: Optional[bool] = None,
) -> Dict[str, str]:
    """
    Updates an existing comment.

    Args:
        comment_id (str): The ID of the comment to update. Must be a non-empty string.
        snippet (Optional[Dict[str, str]]): The comment snippet object with fields to update. Defaults to None. Contains the following fields:
            - videoId (Optional[str]): ID of the associated video.
            - parentId (Optional[str]): ID of the parent comment for replies; None for top-level comments.
        moderation_status (Optional[str]): The new moderation status to set. Defaults to None. Valid values:
            - "heldForReview": Comment is held for review
            - "published": Comment is published and visible
            - "rejected": Comment is rejected and hidden
        banned_author (Optional[bool]): Whether the author of the comment is banned. Defaults to None.

    Returns:
        Dict[str, str]: A dictionary containing:
            - If successful:
                - success (str): A success message with comment ID.
            - If comment not found or no fields provided:
                - error (str): Error message.

    Raises:
        ValueError:
            - If no update parameters (snippet, moderation_status, banned_author) are provided
            - If comment_id is empty or contains only whitespace
            - If moderation_status is not one of the valid values: "heldForReview", "published", "rejected"
        KeyError: If the specified comment_id does not exist in DB["comments"]
        ValidationError: If the input parameters fail Pydantic validation (invalid types, malformed data)
    """
    try:
        # Validate snippet separately if provided
        validated_snippet = None
        if snippet is not None:
            if not isinstance(snippet, dict):
                return {"error": "Validation error: snippet must be a dictionary"}
            validated_snippet = CommentSnippetModel(**snippet)

        # Validate input using Pydantic model
        validated_data = CommentUpdateModel(
            comment_id=comment_id,
            snippet=validated_snippet,
            moderation_status=moderation_status,
            banned_author=banned_author,
        )
    except ValidationError as e:
        return {"error": f"Validation error: {str(e)}"}
    except (TypeError, ValueError) as e:
        return {"error": f"Validation error: {str(e)}"}

    if not any(
        [snippet is not None, moderation_status is not None, banned_author is not None]
    ):
        return {"error": "No update parameters provided"}

    if comment_id not in DB.get("comments", {}):
        return {"error": f"Comment ID: {comment_id} not found in the database."}

    if snippet is not None:
        DB["comments"][comment_id]["snippet"] = snippet
    if moderation_status is not None:
        DB["comments"][comment_id]["moderationStatus"] = moderation_status
    if banned_author is not None:
        DB["comments"][comment_id]["bannedAuthor"] = banned_author

    return {"success": f"Comment ID: {comment_id} updated successfully."}
