from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
# APIs/google_chat/Spaces/Messages/__init__.py

import sys
import os
import builtins
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import re
from google_chat.SimulationEngine.models import ListMessagesInputModel
from pydantic import BaseModel, Field, validator

sys.path.append("APIs")

from google_chat.SimulationEngine.db import DB, CURRENT_USER_ID
from google_chat.SimulationEngine.custom_errors import (
    MissingThreadDataError, 
    UserNotMemberError, DuplicateRequestIdError, InvalidMessageNameFormatError, 
    MessageNotFoundError, MessageHasRepliesError, InvalidFilterError, SpaceNotFoundError
)

from google_chat.SimulationEngine.custom_errors import MissingThreadDataError, UserNotMemberError, DuplicateRequestIdError
from google_chat.SimulationEngine.models import MessageBodyInput, MessageUpdateInput, GetSpaceMessagesInput, CreateMessageInput, MessageUpdateBodyInput
from pydantic import ValidationError



def matches_filter(msg_obj: Dict[str, Any], filter_segments: List[str]) -> bool:
    """
    Determines if a Chat message passes the provided filter expressions.

    If a segment references any other field, the function immediately returns ``False``,
    excluding the message from query results.

    The function is deliberately fault-tolerant: whenever it encounters malformed
    data or unexpected errors it returns ``False`` instead of raising, making it safe
    to use inside list comprehensions.

    Args:
        msg_obj (Dict[str, Any]): A message resource dictionary. Typical keys include:
            - 'name' (str)
            - 'sender' (dict):
                - 'name' (str)
                - 'displayName' (str)
                - 'domainId' (str)
                - 'type' (str)
                - 'isAnonymous' (bool)
            - 'createTime' (str)
            - 'lastUpdateTime' (str)
            - 'deleteTime' (str)
            - 'text' (str)
            - 'formattedText' (str)
            - 'cards' (List[dict])
            - 'cardsV2' (List[dict])
            - 'annotations' (List[dict])
            - 'thread' (dict):
                - 'name' (str)
                - 'threadKey' (str)
            - 'space' (dict):
                - 'name' (str)
                - 'type' (str)
                - 'spaceType' (str)
            - 'fallbackText' (str)
            - 'actionResponse' (dict)
            - 'argumentText' (str)
            - 'slashCommand' (dict)
            - 'attachment' (List[dict]):
                - 'name' (str)
                - 'contentName' (str)
                - 'contentType' (str)
                - 'attachmentDataRef' (dict)
                - 'driveDataRef' (dict)
                - 'thumbnailUri' (str)
                - 'downloadUri' (str)
                - 'source' (str)
            - 'matchedUrl' (dict)
            - 'threadReply' (bool)
            - 'clientAssignedMessageId' (str)
            - 'emojiReactionSummaries' (List[dict])
            - 'privateMessageViewer' (dict):
                - 'name' (str)
                - 'displayName' (str)
                - 'domainId' (str)
                - 'type' (str)
                - 'isAnonymous' (bool)
            - 'deletionMetadata' (dict)
            - 'quotedMessageMetadata' (dict)
            - 'attachedGifs' (List[dict])
            - 'accessoryWidgets' (List[dict])

            Only 'thread.name' and 'createTime' are examined when evaluating the filter.
        filter_segments (List[str]): A list of individual filter expressions joined with
            an implicit logical **AND**. Supported segment formats:
            - 'thread.name = "spaces/{space}/threads/{thread}"'
            - 'create_time > "YYYY-MM-DDThh:mm:ssZ"'
            - 'create_time < "YYYY-MM-DDThh:mm:ssZ"'
            - 'create_time >= "YYYY-MM-DDThh:mm:ssZ"'
            - 'create_time <= "YYYY-MM-DDThh:mm:ssZ"'

            An empty list disables filtering entirely.

    Returns:
        bool: ``True`` if the message satisfies every segment in ``filter_segments``;
              ``False`` otherwise. The function also returns ``False`` whenever either
              input is malformed or an internal error occurs.
    """
    # Handle malformed inputs gracefully - return False instead of raising exceptions
    if not isinstance(msg_obj, dict) or not isinstance(filter_segments, builtins.list):
        return False
    
    # Handle empty filter segments (no filtering)
    if not filter_segments:
        return True
    
    # --- Core Logic ---
    try:
        for seg in filter_segments:
            # Skip non-string segments gracefully
            if not isinstance(seg, str):
                continue
                
            seg_str = seg.strip()
            seg_lower = seg_str.lower()
            
            # Skip empty segments
            if not seg_str:
                continue

            # Check for create_time filter by parsing the left-hand side of the operator
            if any(op in seg_str for op in [">=", "<=", ">", "<"]):
                # Handle create_time filtering
                possible_ops = [">=", "<=", ">", "<"]  # Order matters for parsing
                chosen_op = None
                for op in possible_ops:
                    if op in seg_str:
                        chosen_op = op
                        break
                
                if not chosen_op:
                    return False  # No valid operator found, message doesn't match

                try:
                    lhs_field_part = seg_str.split(chosen_op, 1)[0].strip().lower()
                    if lhs_field_part != "create_time":
                        return False  # Wrong field, message doesn't match

                    _, rhs = seg_str.split(chosen_op, 1)
                    compare_time = rhs.strip().strip('"')
                    msg_time = msg_obj.get("createTime", "")

                    if not msg_time:
                        return False  # Message has no createTime to compare

                    # Perform time comparison
                    if chosen_op == ">":
                        if not (msg_time > compare_time):
                            return False
                    elif chosen_op == "<":
                        if not (msg_time < compare_time):
                            return False
                    elif chosen_op == ">=":
                        if not (msg_time >= compare_time):
                            return False
                    elif chosen_op == "<=":
                        if not (msg_time <= compare_time):
                            return False
                except (ValueError, AttributeError, TypeError):
                    return False  # Parsing or comparison error, message doesn't match
            
            # Check for thread.name filter by parsing the left-hand side of the operator
            elif "=" in seg_str:
                try:
                    lhs, rhs = seg_str.split("=", 1)
                    lhs_field = lhs.strip().lower()
                    
                    # Only process if the field name is exactly "thread.name"
                    if lhs_field == "thread.name":
                        rhs_val = rhs.strip().strip('"').strip("'")  # Support both single and double quoted values
                        
                        # Safely extract thread name from message
                        thread_info = msg_obj.get("thread")
                        if not isinstance(thread_info, dict):
                            actual_thread_name = ""
                        else:
                            actual_thread_name = thread_info.get("name", "")
                        
                        if actual_thread_name != rhs_val:
                            return False
                    else:
                        # Field name is not "thread.name" - this is an invalid filter
                        return False
                except (ValueError, AttributeError):
                    return False  # Parsing error, message doesn't match
            else:
                # Unknown filter field - treat as non-matching rather than error
                return False
                
        return True  # All filters matched
        
    except Exception:
        # Catch-all for any unexpected errors - return False to avoid crashing the list comprehension
        return False

@tool_spec(
    spec={
        'name': 'create_message',
        'description': """ Creates a message in a space.
        
        The space is identified by `parent`, for example, "spaces/AAA". The caller must be a member
        of "spaces/{space}/members/{CURRENT_USER_ID}" to create a message. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': """ Required. Resource name of the space to create the message in.
                    Format: "spaces/{space}". """
                },
                'message_body': {
                    'type': 'object',
                    'description': """ Required. A dictionary representing the message resource object. Based on the
                    MessageBodyInput model, the following core fields are supported:
                    Additional fields are accepted due to the model's extra='allow' configuration, which may include:
                    - cards, cardsV2, annotations, accessoryWidgets, and other message content fields.
                    These will be passed through but are not explicitly validated by the MessageBodyInput model. """,
                    'properties': {
                        'text': {
                            'type': 'string',
                            'description': 'Plain-text body of the message.'
                        },
                        'thread': {
                            'type': 'object',
                            'description': 'Thread information based on ThreadDetailInput model:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Resource name of the thread (e.g., "spaces/AAA/threads/BBB").'
                                }
                            },
                            'required': []
                        },
                        'attachment': {
                            'type': 'array',
                            'description': 'List of message attachments (defaults to empty list):',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'name': {
                                        'type': 'string',
                                        'description': 'Attachment resource name.'
                                    },
                                    'contentName': {
                                        'type': 'string',
                                        'description': 'File name.'
                                    },
                                    'contentType': {
                                        'type': 'string',
                                        'description': 'MIME type.'
                                    },
                                    'thumbnailUri': {
                                        'type': 'string',
                                        'description': 'Thumbnail preview image.'
                                    },
                                    'downloadUri': {
                                        'type': 'string',
                                        'description': 'Direct download URL.'
                                    },
                                    'source': {
                                        'type': 'string',
                                        'description': 'One of "DRIVE_FILE", "UPLOADED_CONTENT".'
                                    },
                                    'attachmentDataRef': {
                                        'type': 'object',
                                        'description': 'For uploading files:',
                                        'properties': {
                                            'resourceName': {
                                                'type': 'string',
                                                'description': 'Reference to the media.'
                                            },
                                            'attachmentUploadToken': {
                                                'type': 'string',
                                                'description': 'Token for uploaded content.'
                                            }
                                        },
                                        'required': [
                                            'resourceName',
                                            'attachmentUploadToken'
                                        ]
                                    },
                                    'driveDataRef': {
                                        'type': 'object',
                                        'description': 'Drive file metadata:',
                                        'properties': {
                                            'driveFileId': {
                                                'type': 'string',
                                                'description': 'ID of the file in Google Drive.'
                                            }
                                        },
                                        'required': [
                                            'driveFileId'
                                        ]
                                    }
                                },
                                'required': [
                                    'name',
                                    'contentName',
                                    'contentType',
                                    'source'
                                ]
                            }
                        }
                    },
                    'required': []
                },
                'requestId': {
                    'type': 'string',
                    'description': """ A unique request ID for this message. Specifying an existing request ID 
                    returns the message created with that ID instead of creating a new message. If a message with 
                    that request_id exists in the database, the existing message is returned. If no message exists 
                    with that request_id, a new message is created with the provided request_id. """
                },
                'messageReplyOption': {
                    'type': 'string',
                    'description': """ Controls whether the message starts a new thread or replies
                    to an existing one. Valid values:
                    - 'MESSAGE_REPLY_OPTION_UNSPECIFIED': Default behavior
                    - 'REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD': Reply to existing thread if specified, otherwise create new thread
                    - 'REPLY_MESSAGE_OR_FAIL': Reply to existing thread if specified, otherwise fail
                    - 'NEW_THREAD': Always create a new thread """
                },
                'messageId': {
                    'type': 'string',
                    'description': """ A custom ID that must start with "client-". Included in the message's
                    resource name if provided. """
                }
            },
            'required': [
                'parent',
                'message_body'
            ]
        }
    }
)
def create(
    parent: str,
    message_body: Dict[str, Union[str, List, Dict, Optional[str]]], # Changed from Optional to Required as per docstring
    requestId: Optional[str] = None,
    messageReplyOption: str = "MESSAGE_REPLY_OPTION_UNSPECIFIED",
    messageId: Optional[str] = None,
) -> Dict[str, Union[str, List, Dict, Optional[str]]]:
    """
    Creates a message in a space.

    The space is identified by `parent`, for example, "spaces/AAA". The caller must be a member
    of "spaces/{space}/members/{CURRENT_USER_ID}" to create a message.

    Args:
        parent (str): Required. Resource name of the space to create the message in.
            Format: "spaces/{space}".
        message_body (Dict[str, Union[str, List, Dict, Optional[str]]]): Required. A dictionary representing the message resource object. Based on the
            MessageBodyInput model, the following core fields are supported:
            - text (Optional[str]): Plain-text body of the message.
            - thread (Optional[Dict[str, Any]]): Thread information based on ThreadDetailInput model:
                - name (Optional[str]): Resource name of the thread (e.g., "spaces/AAA/threads/BBB").
            - attachment (Optional[List[Dict[str, Any]]]): List of message attachments (defaults to empty list):
                - name (str): Attachment resource name.
                - contentName (str): File name.
                - contentType (str): MIME type.
                - thumbnailUri (Optional[str]): Thumbnail preview image.
                - downloadUri (Optional[str]): Direct download URL.
                - source (str): One of "DRIVE_FILE", "UPLOADED_CONTENT".
                - attachmentDataRef (Optional[Dict[str, Any]]): For uploading files:
                    - resourceName (str): Reference to the media.
                    - attachmentUploadToken (str): Token for uploaded content.
                - driveDataRef (Optional[Dict[str, Any]]): Drive file metadata:
                    - driveFileId (str): ID of the file in Google Drive.
            
            Additional fields are accepted due to the model's extra='allow' configuration, which may include:
            - cards, cardsV2, annotations, accessoryWidgets, and other message content fields.
            These will be passed through but are not explicitly validated by the MessageBodyInput model.
        requestId (Optional[str]): A unique request ID for this message. Specifying an existing request ID 
            returns the message created with that ID instead of creating a new message. If a message with 
            that request_id exists in the database, the existing message is returned. If no message exists 
            with that request_id, a new message is created with the provided request_id.
        messageReplyOption (str): Controls whether the message starts a new thread or replies
            to an existing one. Valid values:
            - 'MESSAGE_REPLY_OPTION_UNSPECIFIED': Default behavior
            - 'REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD': Reply to existing thread if specified, otherwise create new thread
            - 'REPLY_MESSAGE_OR_FAIL': Reply to existing thread if specified, otherwise fail
            - 'NEW_THREAD': Always create a new thread
        messageId (Optional[str]): A custom ID that must start with "client-". Included in the message's
            resource name if provided.

    Returns:
        Dict[str, Union[str, List, Dict, Optional[str]]]: A dictionary representing the created or existing message resource. The function creates
            and returns a message object with the following core fields:
            - name (str): Resource name of the message. Format: "spaces/{space}/messages/{message}".
            - text (str): Plain-text body of the message from MessageBodyInput.text (defaults to empty string).
            - attachment (List[Dict[str, Union[str, Optional[str], Dict[str, str]]]]): List of message attachments from MessageBodyInput.attachment 
                (defaults to empty array if not provided).
            - createTime (str): RFC-3339 timestamp when the message was created (set by function).
            - thread (Dict[str, Optional[str]]): Thread information determined by messageReplyOption and MessageBodyInput.thread:
                - name (str): Resource name of the thread (can be empty string).
                - Additional thread fields as determined by the thread resolution logic.
            - requestId (Optional[str]): The request ID that was used to create this message (if provided).
            - sender (Dict[str, str]): Information about the user who sent the message (set by function):
                - name (str): Resource name of the sender from CURRENT_USER_ID.
                - type (str): Type of user, defaults to "HUMAN".
            - clientAssignedMessageId (str): Custom ID assigned to the message (only present if messageId was provided).
            
            Additional fields may be present if they were included in the message_body input and processed
            by the MessageBodyInput model's extra='allow' configuration.

    Raises:
        pydantic.ValidationError:
         If `message_body` is not a valid dictionary or does not conform to the expected structure 
         If `parent` is empty or does not conform to the expected format "spaces/{space}"
         If `messageId` is provided but does not start with "client-".
         If `messageReplyOption` is not one of the valid values.
        SpaceNotFoundError: If the specified space does not exist.
        UserNotMemberError: If the current user is not a member of the specified space.
        MissingThreadDataError: If `messageReplyOption` is 'REPLY_MESSAGE_OR_FAIL' and thread information is missing.
    """
    # Use a Pydantic model for input validation

    try:
        # Validate inputs using the Pydantic model
        validated_input = CreateMessageInput(
            parent=parent,
            message_body=message_body,
            requestId=requestId,
            messageReplyOption=messageReplyOption,
            messageId=messageId,
        )
        parent = validated_input.parent
        message_body = validated_input.message_body
        requestId = validated_input.requestId
        messageReplyOption = validated_input.messageReplyOption
        messageId = validated_input.messageId

        validated_message_body = MessageBodyInput(**message_body)

    except ValidationError as e:
        # Re-raise Pydantic validation errors to be handled by the caller
        print(f"Pydantic validation error: {e}")
        raise e

    # --- Core Logic (original logic adapted for new error handling) ---

    # Check for duplicate requestId - if a message with this requestId already exists, return it
    if requestId:
        for msg in DB.get("Message", []):
            if msg.get("requestId") == requestId:
                # A message with this requestId already exists, return the existing message
                # This ensures idempotent message creation as per Google Chat API specification
                return msg

    # 1) First check if the space exists
    space_exists = any(space.get("name") == parent for space in DB.get("Space", []))
    if not space_exists:
        raise SpaceNotFoundError(
            f"Space '{parent}' does not exist. Please check the space name and try again."
        )
    
    # 2) Then verify membership => name = "spaces/{parent}/members/{CURRENT_USER_ID}"
    membership_name = f"{parent}/members/{CURRENT_USER_ID.get('id')}"
    is_member = any(m.get("name") == membership_name for m in DB.get("Membership", []))
    if not is_member:
        raise UserNotMemberError(
            f"User {CURRENT_USER_ID.get('id')} is not a member of space '{parent}'. Please join the space first."
        )

    if messageId:
        # Validation for messageId format (startswith('client-')) already done above.
        new_msg_name = f"{parent}/messages/{messageId}"
    else:
        # generate a numeric ID
        new_msg_name = f"{parent}/messages/{len(DB.get('Message', [])) + 1}"

    # 3) Handle messageReplyOption
    thread_info_from_body = validated_message_body.thread.model_dump(exclude_none=True) if validated_message_body.thread else {}
    
    final_thread_info = {} # This will hold the thread info for the new message

    if messageReplyOption != "MESSAGE_REPLY_OPTION_UNSPECIFIED":
        if messageReplyOption == "NEW_THREAD":
            # Always create a new thread
            final_thread_info = {"name": f"{parent}/threads/{len(DB.get('Message', [])) + 1000}"} # Use a different counter to avoid ID clashes with messages
        elif messageReplyOption in [
            "REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD",
            "REPLY_MESSAGE_OR_FAIL",
        ]:
            # Check if thread info is provided in message_body
            if not thread_info_from_body or not thread_info_from_body.get("name"):
                if messageReplyOption == "REPLY_MESSAGE_OR_FAIL":
                    raise MissingThreadDataError(
                        "Thread information (thread.name) is required in 'message_body' "
                        "when 'messageReplyOption' is 'REPLY_MESSAGE_OR_FAIL'."
                    )
                else: # REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD
                    # Create new thread as fallback
                    final_thread_info = {"name": f"{parent}/threads/{len(DB.get('Message', [])) + 1000}"}
            else:
                # Use provided thread info
                final_thread_info = thread_info_from_body
    else: # MESSAGE_REPLY_OPTION_UNSPECIFIED
        # If thread info is in message_body, use it. Otherwise, no specific thread (message starts a new logical thread implicitly or is standalone)
        final_thread_info = thread_info_from_body if thread_info_from_body else {}


    # 4) Build the new message object
    new_message = {
        "name": new_msg_name,
        "text": validated_message_body.text or "",
        "attachment": validated_message_body.attachment if validated_message_body.attachment is not None else [],
        "createTime": datetime.now().isoformat() + "Z",
        "thread": final_thread_info, # Use the determined thread_info
        # "messageReplyOption": messageReplyOption, # This is usually not part of the stored message resource itself

        # The sender is set from the user ID (in reality, the server would do this)
        "sender": {"name": CURRENT_USER_ID.get("id"), "type": "HUMAN"}, # Assuming type based on typical user
    }
    
    # Only include requestId if it has a value
    if requestId is not None:
        new_message["requestId"] = requestId
    
    # Add other fields from validated_message_body if they were allowed by extra='allow'
    # and are meant to be part of the message.
    # For example, if cardsV2 were passed in message_body and defined in Pydantic model:
    # if validated_message_body.cardsV2:
    #    new_message["cardsV2"] = validated_message_body.cardsV2


    # If messageId is set, store it as clientAssignedMessageId
    if messageId:
        new_message["clientAssignedMessageId"] = messageId

    # 5) Insert into DB
    if "Message" not in DB: # Ensure 'Message' key exists
        DB["Message"] = []
    DB["Message"].append(new_message)
    # print(f"Message {new_msg_name} created successfully.") # Original print

    return new_message


@tool_spec(
    spec={
        'name': 'list_messages',
        'description': """ Lists messages in a space where the caller is a member.
        
        The space is identified by `parent`, e.g., "spaces/AAA". The caller must be a member of the specified space to retrieve messages. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': 'Required. The resource name of the space to list messages from. Format: `spaces/{space}`.'
                },
                'pageSize': {
                    'type': 'integer',
                    'description': """ The maximum number of messages to return. 
                    Defaults to None (internally defaults to 25). Maximum is 1000. Negative values raise an error. """
                },
                'pageToken': {
                    'type': 'string',
                    'description': """ Token for fetching the next page of results. Should be passed unchanged to retrieve paginated data.
                    Defaults to None. """
                },
                'filter': {
                    'type': 'string',
                    'description': """ A query string for filtering messages by `create_time` and/or `thread.name`. Examples:
                    - create_time > "2023-04-21T11:30:00-04:00"
                    - create_time > "2023-04-21T11:30:00-04:00" AND thread.name = spaces/AAA/threads/123
                    Defaults to None. """
                },
                'orderBy': {
                    'type': 'string',
                    'description': """ Order of the returned messages. Valid values:
                    - "createTime desc": Sort by createTime in descending order (newest first)
                    - "createTime asc": Sort by createTime in ascending order (oldest first)
                    Defaults to None (internally defaults to "createTime desc"). """
                },
                'showDeleted': {
                    'type': 'boolean',
                    'description': """ Whether to include deleted messages. If False, messages with `deleteTime` are excluded.
                    Defaults to None. """
                }
            },
            'required': [
                'parent'
            ]
        }
    }
)
def list(
    parent: str,
    pageSize: Optional[int] = None,
    pageToken: Optional[str] = None,
    filter: Optional[str] = None,
    orderBy: Optional[str] = None,
    showDeleted: Optional[bool] = None,
) -> Dict[str, Union[List[Dict[str, Union[str, bool, int, List[Dict[str, Union[str, int, bool]]], Dict[str, Union[str, bool, int]], None]]], str, None]]:
    """
    Lists messages in a space where the caller is a member.

    The space is identified by `parent`, e.g., "spaces/AAA". The caller must be a member of the specified space to retrieve messages.

    Args:
        parent (str): Required. The resource name of the space to list messages from. Format: `spaces/{space}`.
        pageSize (Optional[int]): The maximum number of messages to return. 
            Defaults to None (internally defaults to 25). Maximum is 1000. Negative values raise an error.
        pageToken (Optional[str]): Token for fetching the next page of results. Should be passed unchanged to retrieve paginated data.
            Defaults to None.
        filter (Optional[str]): A query string for filtering messages by `create_time` and/or `thread.name`. Examples:
            - create_time > "2023-04-21T11:30:00-04:00"
            - create_time > "2023-04-21T11:30:00-04:00" AND thread.name = spaces/AAA/threads/123
            Defaults to None.
        orderBy (Optional[str]): Order of the returned messages. Valid values:
            - "createTime desc": Sort by createTime in descending order (newest first)
            - "createTime asc": Sort by createTime in ascending order (oldest first)
            Defaults to None (internally defaults to "createTime desc").
        showDeleted (Optional[bool]): Whether to include deleted messages. If False, messages with `deleteTime` are excluded.
            Defaults to None.

    Returns:
        Dict[str, Union[List[Dict[str, Union[str, bool, int, List[Dict[str, Union[str, int, bool]]], Dict[str, Union[str, bool, int]], None]]], str, None]]: A dictionary representing the response with the following structure:
            - messages (List[Dict[str, Union[str, bool, int, List[Dict[str, Union[str, int, bool]]], Dict[str, Union[str, bool, int]], None]]]): A list of message objects. Each message includes:
                - name (str): Resource name of the message. Format: "spaces/{space}/messages/{message}".
                - createTime (str): RFC-3339 timestamp when the message was created.
                - lastUpdateTime (str): RFC-3339 timestamp of last message update.
                - deleteTime (str): RFC-3339 timestamp when the message was deleted, if applicable.
                - text (str): Plain-text body of the message.
                - formattedText (str): Message text with markup formatting.
                - fallbackText (str): Fallback text for cards.
                - argumentText (str): Message text with app mentions stripped out.
                - threadReply (bool): Indicates if the message is a reply in a thread.
                - clientAssignedMessageId (str): Custom ID assigned to the message, if provided.
                - sender (Dict[str, Union[str, bool]]):
                    - name (str): Resource name of the sender, e.g., "users/123".
                    - displayName (str): Display name of the sender.
                    - domainId (str): Google Workspace domain ID.
                    - type (str): Type of user. One of:
                        - "TYPE_UNSPECIFIED"
                        - "HUMAN"
                        - "BOT"
                    - isAnonymous (bool): Indicates if the sender is deleted or hidden.
                - thread (Dict[str, str]):
                    - name (str): Resource name of the thread.
                    - threadKey (str): Thread key used to create the thread.
                - space (Dict[str, Union[str, bool, int, Dict[str, Union[str, int]]]]):
                    - name (str): Resource name of the space.
                    - type (str): Deprecated. Use `spaceType` instead.
                    - spaceType (str): Type of space. One of:
                        - "SPACE"
                        - "GROUP_CHAT"
                        - "DIRECT_MESSAGE"
                    - displayName (str): Optional display name of the space.
                    - externalUserAllowed (bool): Whether external users are allowed.
                    - spaceThreadingState (str): Threading behavior. One of:
                        - "SPACE_THREADING_STATE_UNSPECIFIED"
                        - "THREADED_MESSAGES"
                        - "GROUPED_MESSAGES"
                        - "UNTHREADED_MESSAGES"
                    - spaceHistoryState (str): History configuration. One of:
                        - "HISTORY_STATE_UNSPECIFIED"
                        - "HISTORY_OFF"
                        - "HISTORY_ON"
                    - createTime (str): RFC-3339 timestamp when the space was created.
                    - lastActiveTime (str): RFC-3339 timestamp of last message activity.
                    - importMode (bool): Whether the space was created in import mode.
                    - adminInstalled (bool): Whether the space was created by an admin.
                    - spaceUri (str): Direct URL to open the space.
                    - singleUserBotDm (bool): Whether it's a bot-human direct message.
                    - predefinedPermissionSettings (str): Optional predefined permissions. One of:
                        - "PREDEFINED_PERMISSION_SETTINGS_UNSPECIFIED"
                        - "COLLABORATION_SPACE"
                        - "ANNOUNCEMENT_SPACE"
                    - spaceDetails (Dict[str, str]):
                        - description (str): Description of the space.
                        - guidelines (str): Rules and expectations.
                    - membershipCount (Dict[str, int]):
                        - joinedDirectHumanUserCount (int): Count of joined human users.
                        - joinedGroupCount (int): Count of joined groups.
                    - accessSettings (Dict[str, str]):
                        - accessState (str): One of:
                            - "ACCESS_STATE_UNSPECIFIED"
                            - "PRIVATE"
                            - "DISCOVERABLE"
                        - audience (str): Resource name of discoverable audience, e.g., "audiences/default".
            - annotations (List[Dict[str, Union[str, int, Dict[str, Union[str, bool, List[Dict[str, str]]]]]]]): Rich annotations (e.g., mentions, emojis).
                - type (str): Annotation type. One of: "USER_MENTION", "SLASH_COMMAND", "RICH_LINK", "CUSTOM_EMOJI".
                - startIndex (int): Start position in the message text.
                - length (int): Length of the annotated segment.
                - userMention (Dict[str, str]): Info about mentioned user.
                    - type (str): Mention type. One of: "ADD", "MENTION".
                - slashCommand (Dict[str, Union[str, bool]]): Slash command metadata.
                    - type (str): Command interaction type.
                    - commandName (str): Command name.
                    - commandId (str): Unique command ID.
                    - triggersDialog (bool): If it opens a dialog.
                - richLinkMetadata (Dict[str, Union[str, Dict[str, str]]]): Rich preview link data.
                    - uri (str): URL.
                    - richLinkType (str): E.g., "DRIVE_FILE", "CHAT_SPACE".
                    - driveLinkData.mimeType (str): File type for drive links.
                    - chatSpaceLinkData (Dict[str, str]): Chat space linking info.
                        - space (str): Space name.
                        - thread (str): Thread name.
                        - message (str): Message name.
                - customEmojiMetadata (Dict[str, Dict[str, str]]): Custom emoji info.
                    - customEmoji (Dict[str, str]):
                        - name (str): Server-assigned name (e.g., `customEmojis/emoji_id`).
                        - uid (str): Unique ID.
                        - emojiName (str): Emoji name, e.g., `:fire_emoji:`.
                        - temporaryImageUri (str): Temporary image URL.
            - cards (List[Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]]): Legacy UI cards shown in Chat messages.

                - name (str): Identifier for the card.
                - header (Dict[str, str]): Optional card header.
                    - title (str): Required. Title text.
                    - subtitle (str): Optional subtitle text.
                    - imageUrl (str): Optional header image URL.
                    - imageStyle (str): "IMAGE" or "AVATAR".
                - sections (List[Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]]): Content sections within the card.
                    - header (str): Optional section header.
                    - widgets (List[Dict[str, Union[str, int, bool]]]): List of visual elements such as text, buttons, images.
                        - textParagraph (Dict[str, str]): A block of text.
                            - text (str): The paragraph content.
                        - keyValue (Dict[str, str]): Key-value styled layout.
                            - topLabel (str): Top label.
                            - content (str): Content.
                            - bottomLabel (str): Bottom label.
                            - icon (str): Icon.
                            - iconUrl (str): Icon URL.
                        - image (Dict[str, Union[str, float]]): Standalone image.
                            - imageUrl (str): Image URL.
                            - aspectRatio (float): Aspect ratio.
                        - buttons (List[Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]]]): Button elements for interaction.
                            - textButton (Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]]): A button with text and `onclick` action..
                                - text (str): Text.
                                - onClick (Dict[str, Dict[str, Union[str, List[Dict[str, str]]]]]): Action handler.
                                    - openLink (Dict[str, str]): URL to open.
                                        - url (str): URL to open.
                                    - action (Dict[str, List[Dict[str, str]]]): Invokes a defined method.
                                        - actionMethodName (str): The method name is used to identify which part of the form triggered the form submission. This information is echoed back to the Chat app as part of the card click event. You can use the same method name for several elements that trigger a common behavior.
                                        - parameters (List[Dict[str, str]]): List of action parameters
                                            - key (str): The key of the parameter.
                                            - value (str): The value of the parameter.
                            - imageButton (Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]]): A button with an image and `onclick` action.
                                - icon (str): The icon specified by an `enum` that indices to an icon provided by Chat API. Possible values:
                                    - ICON_UNSPECIFIED
                                    - AIRPLANE
                                    - BOOKMARK
                                    - BUS
                                    - CAR
                                    - CLOCK
                                    - CONFIRMATION_NUMBER_ICON
                                    - DOLLAR
                                    - DESCRIPTION
                                    - EMAIL
                                    - EVENT_PERFORMER
                                    - EVENT_SEAT
                                    - FLIGHT_ARRIVAL
                                    - FLIGHT_DEPARTURE
                                    - HOTEL
                                    - HOTEL_ROOM_TYPE
                                    - INVITE
                                    - MAP_PIN
                                    - MEMBERSHIP
                                    - MULTIPLE_PEOPLE
                                    - OFFER
                                    - PERSON
                                    - PHONE
                                    - RESTAURANT_ICON
                                    - SHOPPING_CART
                                    - STAR
                                    - STORE
                                    - TICKET
                                    - TRAIN
                                    - VIDEO_CAMERA
                                    - VIDEO_PLAY
                                - iconUrl (str): Icon URL.
                                - onClick (Dict[str, Dict[str, Union[str, List[Dict[str, str]]]]]): Action handler.
                                    - openLink (Dict[str, str]): URL to open.
                                        - url (str): URL to open.
                                    - action (Dict[str, List[Dict[str, str]]]): Invokes a defined method.
                                        - actionMethodName (str): The method name is used to identify which part of the form triggered the form submission. This information is echoed back to the Chat app as part of the card click event. You can use the same method name for several elements that trigger a common behavior.
                                        - parameters (List[Dict[str, str]]): List of action parameters
                                            - key (str): The key of the parameter.
                                            - value (str): The value of the parameter.
                                - name (str): The name of this `image_button` that's used for accessibility. Default value is provided if this name isn't specified.
                - cardActions (List[Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]]]): Actions at the bottom of the card.
                    - actionLabel (str): Text shown for the action.
                    - onClick (Dict[str, Dict[str, Union[str, List[Dict[str, str]]]]]): Action handler.
                                    - openLink (Dict[str, str]): URL to open.
                                        - url (str): URL to open.
                                    - action (Dict[str, List[Dict[str, str]]]): Invokes a defined method.
                                        - actionMethodName (str): The method name is used to identify which part of the form triggered the form submission. This information is echoed back to the Chat app as part of the card click event. You can use the same method name for several elements that trigger a common behavior.
                                        - parameters (List[Dict[str, str]]): List of action parameters
                                            - key (str): The key of the parameter.
                                            - value (str): The value of the parameter.
                - fixedFooter (Dict[str, Dict[str, Union[str, bool]]]): Optional persistent footer.
                    - primaryButton (Dict[str, Union[str, bool]]): Button element.
                        - text (str): Text.
                        - disabled (bool): Disabled.
                        - altText (str): Alt text.
                        - type (str): Type.
            - cardsV2 (List[Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]]]]): New generation cards with structured layouts.
                - cardId (str): Identifier used to update this card.
                - card (Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]): Complete structure including headers, sections, actions, and footers.
            - attachment (List[Dict[str, Union[str, Dict[str, str]]]]): Message attachments, such as files.
                - name (str): Attachment resource name.
                - contentName (str): File name.
                - contentType (str): MIME type.
                - thumbnailUri (str): Thumbnail preview image.
                - downloadUri (str): Direct download URL.
                - source (str): One of: "DRIVE_FILE", "UPLOADED_CONTENT".
                - attachmentDataRef (Dict[str, str]): For uploading files.
                    - resourceName (str): Reference to the media.
                    - attachmentUploadToken (str): Token for uploaded content.
                - driveDataRef (Dict[str, str]): Drive file metadata.
                    - driveFileId (str): ID of the file in Google Drive.
            - matchedUrl (Dict[str, str]): Metadata for previewable URLs.
                - url (str): The matched link.
            - emojiReactionSummaries (List[Dict[str, Union[int, Dict[str, str]]]]): Summary of emoji reactions.
                - reactionCount (int): Total count of reactions.
                - emoji (Dict[str, str]):
                    - unicode (str): The emoji used.
            - deletionMetadata (Dict[str, str]): Deletion details.
                - deletionType (str): Who deleted it. One of: "CREATOR", "ADMIN", etc.
            - quotedMessageMetadata (Dict[str, str]): Metadata of quoted messages.
                - name (str): Quoted message resource name.
                - lastUpdateTime (str): Timestamp of last update.
            - attachedGifs (List[Dict[str, str]]): List of attached GIF previews.
                - uri (str): URL to the GIF image.
            - actionResponse (Dict[str, Union[str, Dict[str, Dict[str, str]]]]): Data returned by Chat app message interactions.
                - type (str): Response type, e.g., "NEW_MESSAGE", "UPDATE_MESSAGE".
                - url (str): URL for configuration.
                - dialogAction (Dict[str, Dict[str, str]]):
                    - actionStatus (Dict[str, str]):
                        - statusCode (str): Action result status.
                        - userFacingMessage (str): Optional message for the user.
            - accessoryWidgets (List[Dict[str, Union[str, List[Dict[str, str]]]]]): Additional UI elements below the main card or message.
                - decoratedText (Dict[str, Union[str, Dict[str, str]]]):
                    - text (str): Content shown.
                    - startIcon (Dict[str, str]):
                        - iconUrl (str): URL for the icon image.
            - nextPageToken (Optional[str]): Token for retrieving the next page of results.
        
        Returns an empty dictionary `{"messages": []}` if no messages match or the user has no access.

    Raises:
        TypeError: If any argument is of an incorrect type (e.g., parent is not a string, pageSize is not an int).
        ValueError: If 'parent' is an empty string or does not conform to the expected format "spaces/{space}",
                    'pageSize' is negative or exceeds 1000, 'pageToken' cannot be converted to a valid integer,
                    or 'orderBy' is provided with an invalid format or value.
    """
    # --- Input Validation using Pydantic ---    
    
    # Validate input using Pydantic model
    validated_input = ListMessagesInputModel(
        parent=parent,
        pageSize=pageSize,
        pageToken=pageToken,
        filter=filter,
        orderBy=orderBy,
        showDeleted=showDeleted
    )
    
    # Extract validated values
    parent = validated_input.parent
    pageSize = validated_input.pageSize
    pageToken = validated_input.pageToken
    filter = validated_input.filter
    orderBy = validated_input.orderBy
    showDeleted = validated_input.showDeleted

    # --- Original Core Logic (adapted where validation now handles errors) ---

    # 1) Check membership
    #    Assumes CURRENT_USER_ID and DB are available in the scope.
    membership_name = f"{parent}/members/{CURRENT_USER_ID.get('id')}" # type: ignore
    user_is_member = any(mem.get("name") == membership_name for mem in DB["Membership"]) # type: ignore
    if not user_is_member:
        # In real usage, you'd raise an error (403). We'll return empty for demonstration.
        return {"messages": []}

    # 2) Default pageSize
    effective_pageSize = pageSize
    if effective_pageSize is None:
        effective_pageSize = 25

    # 3) Convert pageToken to offset
    offset = 0
    if pageToken:
        try:
            offset_val = int(pageToken)
            if offset_val >= 0:
                offset = offset_val
        except ValueError:
            pass

    # 4) Gather messages that belong to 'parent'
    all_msgs = []
    for msg in DB["Message"]: # type: ignore
        if msg.get("name", "").startswith(parent + "/messages/"):
            all_msgs.append(msg)

    # 5) If showDeleted != True, skip messages that have a non-empty deleteTime
    if not showDeleted:
        filtered_msgs = []
        for m in all_msgs:
            if not m.get("deleteTime"):
                filtered_msgs.append(m)
        all_msgs = filtered_msgs

    # 6) Filter parse
    if filter:
        segments = filter.split("AND")
        filtered_msgs = [m for m in all_msgs if matches_filter(m, segments)]
        all_msgs = filtered_msgs

    # 7) Apply ordering based on orderBy parameter
    if orderBy:
        parts = orderBy.lower().split()
        field = "createTime" # parts[0] is "createtime"
        direction = parts[1] # parts[1] is "asc" or "desc"
        all_msgs.sort(key=lambda x: x.get(field, ""), reverse=(direction == "desc"))
    else:
        all_msgs.sort(key=lambda x: x.get("createTime", ""), reverse=True) # Default sort

    # 8) Apply offset + pageSize
    total = len(all_msgs)
    page_end = offset + effective_pageSize
    page_items = all_msgs[offset:page_end]
    next_token = None
    if page_end < total:
        next_token = str(page_end)

    # 9) Build the response
    response = {"messages": page_items}
    if next_token:
        response["nextPageToken"] = next_token

    return response


@tool_spec(
    spec={
        'name': 'get_message',
        'description': """ Returns details about a message by name.
        
        The `name` should follow the format: "spaces/{space}/messages/{message}".
        This function performs the following steps:
            1. Parses the space portion from the name.
            2. Checks if the current user is a member of the space.
            3. Finds the message in DB["Message"].
            4. Returns the message if found and authorized, else returns {}. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. Resource name of the message.
                    Format: "spaces/{space}/messages/{message}" or
                    "spaces/{space}/messages/client-custom-id". """
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def get(name: str) -> Dict[str, Union[str, bool, int, List[Dict[str, Union[str, int, bool]]], Dict[str, Union[str, bool, int]], None]]:
    """
    Retrieves a message by its resource name.

    The `name` should follow the format: "spaces/{space}/messages/{message}".
    This function performs the following steps:
        1. Parses the space portion from the name.
        2. Checks if the current user is a member of the space.
        3. Finds the message in DB["Message"].
        4. Returns the message if found and authorized, else returns {}.

    Args:
        name (str): Required. Resource name of the message.
            Format: "spaces/{space}/messages/{message}" or
            "spaces/{space}/messages/client-custom-id".

    Returns:
        Dict[str, Union[str, bool, int, List[Dict[str, Union[str, int, bool]]], Dict[str, Union[str, bool, int]], None]]: A dictionary representing the message resource.
        Returns an empty dictionary `{}` if no messages match or the user has no access.

            - messages (List[Dict[str, Union[str, bool, int]]]): A list of message objects. Each message includes:
                - name (str): Resource name of the message. Format: "spaces/{space}/messages/{message}".
                - createTime (str): RFC-3339 timestamp when the message was created.
                - lastUpdateTime (str): RFC-3339 timestamp of last message update.
                - deleteTime (str): RFC-3339 timestamp when the message was deleted, if applicable.
                - text (str): Plain-text body of the message.
                - formattedText (str): Message text with markup formatting.
                - fallbackText (str): Fallback text for cards.
                - argumentText (str): Message text with app mentions stripped out.
                - threadReply (bool): Indicates if the message is a reply in a thread.
                - clientAssignedMessageId (str): Custom ID assigned to the message, if provided.
                - sender (Dict[str, Union[str, bool]]):
                    - name (str): Resource name of the sender, e.g., "users/123".
                    - displayName (str): Display name of the sender.
                    - domainId (str): Google Workspace domain ID.
                    - type (str): Type of user. One of:
                        - "TYPE_UNSPECIFIED"
                        - "HUMAN"
                        - "BOT"
                    - isAnonymous (bool): Indicates if the sender is deleted or hidden.
                - thread (Dict[str, str]):
                    - name (str): Resource name of the thread.
                    - threadKey (str): Thread key used to create the thread.
                - space (Dict[str, Union[str, bool, int, Dict[str, Union[str, int]]]]):
                    - name (str): Resource name of the space.
                    - type (str): Deprecated. Use `spaceType` instead.
                    - spaceType (str): Type of space. One of:
                        - "SPACE"
                        - "GROUP_CHAT"
                        - "DIRECT_MESSAGE"
                    - displayName (str): Optional display name of the space.
                    - externalUserAllowed (bool): Whether external users are allowed.
                    - spaceThreadingState (str): Threading behavior. One of:
                        - "SPACE_THREADING_STATE_UNSPECIFIED"
                        - "THREADED_MESSAGES"
                        - "GROUPED_MESSAGES"
                        - "UNTHREADED_MESSAGES"
                    - spaceHistoryState (str): History configuration. One of:
                        - "HISTORY_STATE_UNSPECIFIED"
                        - "HISTORY_OFF"
                        - "HISTORY_ON"
                    - createTime (str): RFC-3339 timestamp when the space was created.
                    - lastActiveTime (str): RFC-3339 timestamp of last message activity.
                    - importMode (bool): Whether the space was created in import mode.
                    - adminInstalled (bool): Whether the space was created by an admin.
                    - spaceUri (str): Direct URL to open the space.
                    - singleUserBotDm (bool): Whether it's a bot-human direct message.
                    - predefinedPermissionSettings (str): Optional predefined permissions. One of:
                        - "PREDEFINED_PERMISSION_SETTINGS_UNSPECIFIED"
                        - "COLLABORATION_SPACE"
                        - "ANNOUNCEMENT_SPACE"
                    - spaceDetails (Dict[str, str]):
                        - description (str): Description of the space.
                        - guidelines (str): Rules and expectations.
                    - membershipCount (Dict[str, int]):
                        - joinedDirectHumanUserCount (int): Count of joined human users.
                        - joinedGroupCount (int): Count of joined groups.
                    - accessSettings (Dict[str, str]):
                        - accessState (str): One of:
                            - "ACCESS_STATE_UNSPECIFIED"
                            - "PRIVATE"
                            - "DISCOVERABLE"
                        - audience (str): Resource name of discoverable audience, e.g., "audiences/default".
            - annotations (List[Dict[str, Union[str, int, Dict[str, Union[str, bool, List[Dict[str, str]]]]]]]): Rich annotations (e.g., mentions, emojis).
                - type (str): Annotation type. One of: "USER_MENTION", "SLASH_COMMAND", "RICH_LINK", "CUSTOM_EMOJI".
                - startIndex (int): Start position in the message text.
                - length (int): Length of the annotated segment.
                - userMention (Dict[str, str]): Info about mentioned user.
                    - type (str): Mention type. One of: "ADD", "MENTION".
                - slashCommand (Dict[str, Union[str, bool]]): Slash command metadata.
                    - type (str): Command interaction type.
                    - commandName (str): Command name.
                    - commandId (str): Unique command ID.
                    - triggersDialog (bool): If it opens a dialog.
                - richLinkMetadata (Dict[str, Union[str, Dict[str, str]]]): Rich preview link data.
                    - uri (str): URL.
                    - richLinkType (str): E.g., "DRIVE_FILE", "CHAT_SPACE".
                    - driveLinkData.mimeType (str): File type for drive links.
                    - chatSpaceLinkData (Dict[str, str]): Chat space linking info.
                        - space (str): Space name.
                        - thread (str): Thread name.
                        - message (str): Message name.
                - customEmojiMetadata (Dict[str, Dict[str, str]]): Custom emoji info.
                    - customEmoji (Dict[str, str]):
                        - name (str): Server-assigned name (e.g., `customEmojis/emoji_id`).
                        - uid (str): Unique ID.
                        - emojiName (str): Emoji name, e.g., `:fire_emoji:`.
                        - temporaryImageUri (str): Temporary image URL.

            - cards (List[Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]]): Legacy UI cards shown in Chat messages.

                - name (str): Identifier for the card.
                - header (Dict[str, str]): Optional card header.
                    - title (str): Required. Title text.
                    - subtitle (str): Optional subtitle text.
                    - imageUrl (str): Optional header image URL.
                    - imageStyle (str): "IMAGE" or "AVATAR".
                - sections (List[Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]]): Content sections within the card.
                    - header (str): Optional section header.
                    - widgets (List[Dict[str, Union[str, int, bool]]]): List of visual elements such as text, buttons, images.
                        - textParagraph (Dict[str, str]): A block of text.
                            - text (str): The paragraph content.
                        - keyValue (Dict[str, str]): Key-value styled layout.
                            - topLabel (str): Top label.
                            - content (str): Content.
                            - bottomLabel (str): Bottom label.
                            - icon (str): Icon.
                            - iconUrl (str): Icon URL.
                        - image (Dict[str, Union[str, int]]): Standalone image.
                            - imageUrl (str): Image URL.
                            - aspectRatio (int): Aspect ratio.
                        - buttons (List[Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]]]): Button elements for interaction.
                - cardActions (List[Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, str]]]]]]]): Actions at the bottom of the card.
                    - actionLabel (str): Text shown for the action.
                    - onClick (Dict[str, Dict[str, Union[str, List[Dict[str, str]]]]]): Action handler.
                        - openLink (Dict[str, str]): URL to open.
                        - action (Dict[str, List[Dict[str, str]]]): Invokes a defined method.
                - fixedFooter (Dict[str, Dict[str, Union[str, bool]]]): Optional persistent footer.
                    - primaryButton (Dict[str, Union[str, bool]]): Button element.
                        - text (str): Text.
                        - disabled (bool): Disabled.
                        - altText (str): Alt text.
                        - type (str): Type.
            - cardsV2 (List[Dict[str, Union[str, Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]]]]): New generation cards with structured layouts.

                - cardId (str): Identifier used to update this card.
                - card (Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]): Complete structure including headers, sections, actions, and footers.


            - attachment (List[Dict[str, Union[str, Dict[str, str]]]]): Message attachments, such as files.
                - name (str): Attachment resource name.
                - contentName (str): File name.
                - contentType (str): MIME type.
                - thumbnailUri (str): Thumbnail preview image.
                - downloadUri (str): Direct download URL.
                - source (str): One of: "DRIVE_FILE", "UPLOADED_CONTENT".
                - attachmentDataRef (Dict[str, str]): For uploading files.
                    - resourceName (str): Reference to the media.
                    - attachmentUploadToken (str): Token for uploaded content.
                - driveDataRef (Dict[str, str]): Drive file metadata.
                    - driveFileId (str): ID of the file in Google Drive.

            - matchedUrl (Dict[str, str]): Metadata for previewable URLs.
                - url (str): The matched link.

            - emojiReactionSummaries (List[Dict[str, Union[int, Dict[str, str]]]]): Summary of emoji reactions.
                - reactionCount (int): Total count of reactions.
                - emoji (Dict[str, str]):
                    - unicode (str): The emoji used.

            - deletionMetadata (Dict[str, str]): Deletion details.
                - deletionType (str): Who deleted it. One of: "CREATOR", "ADMIN", etc.

            - quotedMessageMetadata (Dict[str, str]): Metadata of quoted messages.
                - name (str): Quoted message resource name.
                - lastUpdateTime (str): Timestamp of last update.

            - attachedGifs (List[Dict[str, str]]): List of attached GIF previews.
                - uri (str): URL to the GIF image.

            - actionResponse (Dict[str, Union[str, Dict[str, Dict[str, str]]]]): Data returned by Chat app message interactions.
                - type (str): Response type, e.g., "NEW_MESSAGE", "UPDATE_MESSAGE".
                - url (str): URL for configuration.
                - dialogAction (Dict[str, Dict[str, str]]):
                    - actionStatus (Dict[str, str]):
                        - statusCode (str): Action result status.
                        - userFacingMessage (str): Optional message for the user.
            - accessoryWidgets (List[Dict[str, Union[str, List[Dict[str, str]]]]]): Additional UI elements below the main card or message.
            - decoratedText (Dict[str, Union[str, Dict[str, str]]]):
                    - text (str): Content shown.
                    - startIcon (Dict[str, str]):
                        - iconUrl (str): URL for the icon image.

            - privateMessageViewer (Dict[str, str]): Viewer for private messages.
                - name (str): User resource name who can view the message (e.g., "users/123").

            - slashCommand (Dict[str, str]): Slash command info when used to create a message.
                - commandId (str): ID of the executed slash command.

            - nextPageToken (Optional[str]): Token for retrieving the next page of results.

        Returns an empty dictionary `{}` if no messages match or the user has no access.
    Raises:
        TypeError: If 'name' is not a string.
        ValueError: If 'name' is empty or has an invalid format.
    """
    print_log(
        f"get_message called with name={name}, CURRENT_USER_ID={CURRENT_USER_ID.get('id')}"
    )

    # --- Input Validation ---
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    if not name.strip():
        raise ValueError("Argument 'name' cannot be empty.")
        
    try:
        GetSpaceMessagesInput(name=name)
    except ValidationError:
        raise ValueError("Invalid message name format")

    # 1) Parse out the space portion from name => "spaces/AAA" is the first 2 segments

    # expected: ["spaces", "AAA", "messages", "MESSAGE_ID"]
    # so the space name is e.g. "spaces/AAA" from the first 2 elements

    parts = name.split("/")
    space_name = "/".join(parts[:2])  # => "spaces/AAA"

    # 2) Check membership => "spaces/AAA/members/{CURRENT_USER_ID}"
    membership_name = f"{space_name}/members/{CURRENT_USER_ID.get('id')}"
    is_member = any(m.get("name") == membership_name for m in DB["Membership"])
    if not is_member:
        print_log(
            f"Caller {CURRENT_USER_ID.get('id')} is not a member of {space_name} => no permission."
        )
        return {}

    # 3) Find the message
    found_msg = None
    for msg in DB["Message"]:
        if msg.get("name") == name:
            found_msg = msg
            break

    # 4) Return the message or {}
    if not found_msg:
        print_log(f"No message found with name={name}")
        return {}

    print_log(f"Found message: {found_msg}")
    return found_msg

@tool_spec(
    spec={
        'name': 'update_message',
        'description': 'Updates a message in a Google Chat space or creates a new one if allowed.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. Resource name of the message to update. Format:
                    `spaces/{space}/messages/{message}`. If using a client-assigned ID,
                    use `spaces/{space}/messages/client-{custom_id}`. """
                },
                'updateMask': {
                    'type': 'string',
                    'description': """ Required. Comma-separated list of fields to update. Use `"*"` to update all fields.
                    Valid fields: "text", "attachment", "cards", "cards_v2", "accessory_widgets". """
                },
                'allowMissing': {
                    'type': 'boolean',
                    'description': """ If True and the message is not found, creates a new message
                    (only allowed with a client-assigned message ID). """
                },
                'body': {
                    'type': 'object',
                    'description': 'Required. The message fields to apply updates to. May include any of the following keys:',
                    'properties': {
                        'text': {
                            'type': 'string',
                            'description': 'The plain-text message body.'
                        },
                        'attachment': {
                            'type': 'array',
                            'description': 'List of attachments.',
                            'items': {
                                'type': 'object',
                                'properties': {},
                                'required': []
                            }
                        },
                        'cards': {
                            'type': 'array',
                            'description': 'Legacy UI card structure.',
                            'items': {
                                'type': 'object',
                                'properties': {},
                                'required': []
                            }
                        },
                        'cardsV2': {
                            'type': 'array',
                            'description': 'Enhanced modern card structure.',
                            'items': {
                                'type': 'object',
                                'properties': {},
                                'required': []
                            }
                        },
                        'accessoryWidgets': {
                            'type': 'array',
                            'description': 'Interactive widgets shown below the message.',
                            'items': {
                                'type': 'object',
                                'properties': {},
                                'required': []
                            }
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'name',
                'updateMask',
                'allowMissing',
                'body'
            ]
        }
    }
)
def update(name: str, updateMask: str, allowMissing: bool, body: Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]], None]]) -> Dict[str, Union[str, bool, Dict[str, Union[str, bool, int]], List[Dict[str, Union[str, int, bool]]], None]]:
    """
    Updates a message in a Google Chat space or creates a new one if allowed.

    Args:
        name (str): Required. Resource name of the message to update. Format:
            `spaces/{space}/messages/{message}`. If using a client-assigned ID,
            use `spaces/{space}/messages/client-{custom_id}`.
        updateMask (str): Required. Comma-separated list of fields to update. Use `"*"` to update all fields.
            Valid fields: "text", "attachment", "cards", "cards_v2", "accessory_widgets".
        allowMissing (bool): If True and the message is not found, creates a new message
            (only allowed with a client-assigned message ID).
        body (Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]], None]]): Required. The message fields to apply updates to. May include any of the following keys:
            - text (Optional[str]): The plain-text message body.
            - attachment (Optional[List[dict]]): List of attachments.
            - cards (Optional[List[dict]]): Legacy UI card structure.
            - cardsV2 (Optional[List[dict]]): Enhanced modern card structure.
            - accessoryWidgets (Optional[List[dict]]): Interactive widgets shown below the message.

    Returns:
        Dict[str, Union[str, bool, Dict[str, Union[str, bool, int]], List[Dict[str, Union[str, int, bool]]], None]]: The updated or newly created message resource. Fields include:

            - name (str)
            - createTime (str)
            - lastUpdateTime (str)
            - deleteTime (str)
            - text (str)
            - formattedText (str)
            - fallbackText (str)
            - argumentText (str)
            - threadReply (bool)
            - clientAssignedMessageId (str)
            - sender (dict):
                - name (str)
                - displayName (str)
                - domainId (str)
                - type (str): One of "HUMAN", "BOT"
                - isAnonymous (bool)
            - annotations (List[dict]):
                - type (str)
                - startIndex (int)
                - length (int)
                - userMention, slashCommand, richLinkMetadata, customEmojiMetadata (dicts with respective subfields)
            - cards (List[dict]):
                - header (dict): title, subtitle, imageStyle, imageUrl
                - sections (List[dict]):
                    - header (str)
                    - widgets (List[dict]): textParagraph, image, keyValue, buttons
                - cardActions (List[dict])
            - cardsV2 (List[dict]):
                - cardId (str)
                - card (dict):
                    - name (str)
                    - displayStyle (str)
                    - header (dict): title, subtitle, imageType, imageUrl, imageAltText
                    - sectionDividerStyle (str)
                    - sections (List[dict]):
                        - header (str)
                        - collapsible (bool)
                        - uncollapsibleWidgetsCount (int)
                        - widgets (List[dict]): textParagraph, image, decoratedText, keyValue, grid, columns,
                            chipList, selectionInput, textInput, dateTimePicker, divider, carousel
                    - cardActions (List[dict]): openLink, action, overflowMenu
                    - fixedFooter (dict):
                        - primaryButton (dict): text, disabled, altText, type, icon, color
            - attachment (List[dict]):
                - name (str)
                - contentName (str)
                - contentType (str)
                - thumbnailUri (str)
                - downloadUri (str)
                - source (str)
                - attachmentDataRef (dict): resourceName, attachmentUploadToken
                - driveDataRef (dict): driveFileId
            - matchedUrl (dict): url (str)
            - emojiReactionSummaries (List[dict]):
                - reactionCount (int)
                - emoji (dict): unicode (str)
            - deletionMetadata (dict): deletionType (str)
            - quotedMessageMetadata (dict):
                - name (str)
                - lastUpdateTime (str)
            - attachedGifs (List[dict]): uri (str)
            - actionResponse (dict):
                - type (str)
                - url (str)
                - updatedWidget (dict): widget (str), suggestions (dict with items)
                - dialogAction (dict): actionStatus (dict): statusCode, userFacingMessage
            - accessoryWidgets (List[dict]):
                - buttonList (dict): buttons (List[dict])
            - privateMessageViewer (dict): name (str)
            - slashCommand (dict): commandId (str)
            - thread (dict):
                - name (str)
                - threadKey (str)
            - space (dict):
                - name (str)
                - type (str) [Deprecated]
                - spaceType (str)
                - singleUserBotDm (bool)
                - threaded (bool) [Deprecated]
                - displayName (str)
                - externalUserAllowed (bool)
                - spaceThreadingState (str)
                - spaceHistoryState (str)
                - importMode (bool)
                - createTime (str)
                - lastActiveTime (str)
                - adminInstalled (bool)
                - spaceUri (str)
                - predefinedPermissionSettings (str)
                - spaceDetails (dict): description, guidelines
                - membershipCount (dict): joinedDirectHumanUserCount, joinedGroupCount
                - accessSettings (dict): accessState, audience

    Raises:
        ValidationError: if message has anything not upto the MessageUpdateBodyInput model.
    """
    # Input validation
    if name is None:
        return {}
    if not isinstance(name, str):
        return {}
    if not name.strip():
        return {}
    
    if updateMask is None:
        return {}
    if not isinstance(updateMask, str):
        return {}
    if not updateMask.strip():
        return {}
    
    if allowMissing is None:
        return {}
    if not isinstance(allowMissing, bool):
        return {}
    
    if body is None:
        return {}
    if not isinstance(body, dict):
        return {}
    
    # Validate body structure using Pydantic
    try:
        validated_body = MessageUpdateInput(**body)
    except ValidationError:
        return {}

    print_log(
        f"update_message called: name={name}, updateMask={updateMask}, allowMissing={allowMissing}"
    )

    # Parse name format
    parts = name.split("/")
    if len(parts) < 4 or parts[0] != "spaces" or parts[2] != "messages":
        print("Invalid name format.")
        return {}
    
    msg_id = parts[3]

    # Look for existing message
    existing = None
    for msg in DB["Message"]:
        if msg.get("name") == name:
            existing = msg
            break

    # Handle missing message
    if not existing:
        if allowMissing:
            # The doc: "If `true` and the message isn't found, a new message is created and `updateMask` is ignored.
            #           The specified message ID must be client-assigned or the request fails."
            # So we check if the last path segment starts with "client-"
            parts = name.split("/")
            if len(parts) < 4 or parts[2] != "messages":
                print_log("Invalid name format.")
                return {}
            msg_id = parts[3]  # e.g. "client-xyz"

            if not msg_id.startswith("client-"):
                print_log("Not found, allowMissing=True but ID isn't client- => fail.")
                return {}

            print_log("Message not found => create new with client ID.")
            # create minimal new message
            existing = {
                "name": name,
                "text": "",
                "attachment": [],
            }
            DB["Message"].append(existing)
        else:
            print_log("Message not found, allowMissing=False => can't update.")
            return {}

    # Parse updateMask
    valid_fields = ["text", "attachment", "cards", "cards_v2", "accessory_widgets"]
    if updateMask.strip() == "*":
        fields_to_update = valid_fields
    else:
        fields_to_update = [f.strip() for f in updateMask.split(",")]

    # Apply updates from validated body
    field_mapping = {
        "text": "text",
        "attachment": "attachment", 
        "cards": "cards",
        "cards_v2": "cardsV2",
        "accessory_widgets": "accessoryWidgets"
    }
    
    for field in fields_to_update:
        if field not in valid_fields:
            print_log(f"Skipping unknown or unsupported field '{field}'.")
            continue

        internal_field = field_mapping[field]
        
        # Get value from validated body
        if hasattr(validated_body, internal_field):
            new_val = getattr(validated_body, internal_field)
            if new_val is not None:
                existing[internal_field] = new_val

    print_log(f"Updated message => {existing}")
    return existing


@tool_spec(
    spec={
        'name': 'patch_message',
        'description': """ Updates an existing message resource using the PATCH method.
        
        This method updates the fields of a Chat message identified by its resource
        name. It supports partial updates via the `updateMask` parameter. If the message
        is not found and `allowMissing` is True, a new message is created (requires a
        client-assigned message ID). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': """ Required. Resource name of the message to update.
                    Format: `spaces/{space}/messages/{message}`.
                    Examples:
                    - `spaces/AAA/messages/BBB.CCC`
                    - `spaces/AAA/messages/client-custom-name`
                    See: https://developers.google.com/workspace/chat/create-messages#name_a_created_message """
                },
                'updateMask': {
                    'type': 'string',
                    'description': """ Required. Comma-separated list of fields to update, or `*` for all.
                    Supported values include:
                    - `text`
                    - `attachment`
                    - `cards`
                    - `cards_v2`
                    - `accessory_widgets` """
                },
                'allowMissing': {
                    'type': 'boolean',
                    'description': 'If True, creates the message if not found (requires a client-assigned ID). Ignores `updateMask` in that case. default is None.'
                },
                'message': {
                    'type': 'object',
                    'description': 'A dictionary representing the fields of the message to update. Possible keys include:',
                    'properties': {
                        'text': {
                            'type': 'string',
                            'description': 'Plain-text body of the message.'
                        },
                        'fallbackText': {
                            'type': 'string',
                            'description': 'Fallback text for message cards.'
                        },
                        'cards': {
                            'type': 'array',
                            'description': 'A card is a UI element that can contain UI widgets such as text and images.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'header': {
                                        'type': 'object',
                                        'description': 'The card header contains details about the card like title, subtitle, image.',
                                        'properties': {
                                            'title': {
                                                'type': 'string',
                                                'description': 'The title of the card header'
                                            },
                                            'subtitle': {
                                                'type': 'string',
                                                'description': 'The subtitle of the card header.'
                                            },
                                            'imageStyle': {
                                                'type': 'string',
                                                'description': "The image's type (for example, square border or circular border)."
                                            },
                                            'imageUrl': {
                                                'type': 'string',
                                                'description': 'The URL of the image in the card header.'
                                            }
                                        },
                                        'required': [
                                            'title',
                                            'subtitle',
                                            'imageStyle',
                                            'imageUrl'
                                        ]
                                    },
                                    'sections': {
                                        'type': 'array',
                                        'description': "A section contains a collection of widgets that are rendered (vertically) in the order that they are specified. Across all platforms, cards have a narrow fixed width, so there's currently no need for layout properties (for example, float).",
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'header': {
                                                    'type': 'string',
                                                    'description': 'The header of the section. Formatted text is supported.'
                                                },
                                                'widgets': {
                                                    'type': 'array',
                                                    'description': 'A widget is a UI element that presents text and images.',
                                                    'items': {
                                                        'type': 'object',
                                                        'properties': {},
                                                        'required': []
                                                    }
                                                }
                                            },
                                            'required': [
                                                'header',
                                                'widgets'
                                            ]
                                        }
                                    },
                                    'cardActions': {
                                        'type': 'array',
                                        'description': 'A card action is the action associated with the card. For an invoice card, a typical action would be: delete invoice, email invoice or open the invoice in browser.',
                                        'items': {
                                            'type': 'object',
                                            'properties': {},
                                            'required': []
                                        }
                                    }
                                },
                                'required': [
                                    'header',
                                    'sections',
                                    'cardActions'
                                ]
                            }
                        },
                        'cards_v2': {
                            'type': 'array',
                            'description': 'A card interface displayed in a Google Chat message or Google Workspace add-on.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'cardId': {
                                        'type': 'string',
                                        'description': 'A Unique ID for card.'
                                    },
                                    'card': {
                                        'type': 'object',
                                        'description': 'A card is a UI element that can contain UI widgets such as text and images.',
                                        'properties': {
                                            'name': {
                                                'type': 'string',
                                                'description': 'Name of the card. Used as a card identifier in card navigation.'
                                            },
                                            'displayStyle': {
                                                'type': 'string',
                                                'description': 'In Google Workspace add-ons, sets the display properties of the peekCardHeader.'
                                            },
                                            'header': {
                                                'type': 'object',
                                                'description': 'The header of the card. A header usually contains a leading image and a title. Headers always appear at the top of a card.',
                                                'properties': {},
                                                'required': []
                                            },
                                            'sectionDividerStyle': {
                                                'type': 'string',
                                                'description': 'The divider style between the header, sections and footer.'
                                            },
                                            'sections': {
                                                'type': 'array',
                                                'description': 'Contains a collection of widgets. Each section has its own, optional header. Sections are visually separated by a line divider.',
                                                'items': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'header': {
                                                            'type': 'string',
                                                            'description': 'Text that appears at the top of a section. Supports simple HTML formatted text.'
                                                        },
                                                        'collapsible': {
                                                            'type': 'boolean',
                                                            'description': 'Indicates whether this section is collapsible.'
                                                        },
                                                        'uncollapsibleWidgetsCount': {
                                                            'type': 'integer',
                                                            'description': 'The number of uncollapsible widgets which remain visible even when a section is collapsed.'
                                                        },
                                                        'widgets': {
                                                            'type': 'array',
                                                            'description': 'All the widgets in the section. Must contain at least one widget.',
                                                            'items': {
                                                                'type': 'object',
                                                                'properties': {},
                                                                'required': []
                                                            }
                                                        }
                                                    },
                                                    'required': [
                                                        'header',
                                                        'collapsible',
                                                        'uncollapsibleWidgetsCount',
                                                        'widgets'
                                                    ]
                                                }
                                            },
                                            'cardActions': {
                                                'type': 'array',
                                                'description': 'A card action is the action associated with the card. For example, an invoice card might include actions such as delete invoice, email invoice, or open the invoice in a browser.',
                                                'items': {
                                                    'type': 'object',
                                                    'properties': {},
                                                    'required': []
                                                }
                                            },
                                            'fixedFooter': {
                                                'type': 'object',
                                                'description': 'A persistent (sticky) footer that that appears at the bottom of the card.',
                                                'properties': {
                                                    'primaryButton': {
                                                        'type': 'object',
                                                        'description': 'The primary button of the fixed footer. The button must be a text button with text and color set.',
                                                        'properties': {},
                                                        'required': []
                                                    },
                                                    'secondaryButton': {
                                                        'type': 'object',
                                                        'description': 'The secondary button of the fixed footer. The button must be a text button with text and color set. If secondaryButton is set, you must also set primaryButton.',
                                                        'properties': {},
                                                        'required': []
                                                    }
                                                },
                                                'required': [
                                                    'primaryButton',
                                                    'secondaryButton'
                                                ]
                                            }
                                        },
                                        'required': [
                                            'name',
                                            'displayStyle',
                                            'header',
                                            'sectionDividerStyle',
                                            'sections',
                                            'cardActions',
                                            'fixedFooter'
                                        ]
                                    }
                                },
                                'required': [
                                    'cardId',
                                    'card'
                                ]
                            }
                        },
                        'attachment': {
                            'type': 'array',
                            'description': 'An attachment in Google Chat.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'name': {
                                        'type': 'string',
                                        'description': 'Resource name of the attachment, in the form'
                                    },
                                    'attachmentDataRef': {
                                        'type': 'object',
                                        'description': 'A reference to the attachment data. This field is used to create or update messages with attachments, or with the media API to download the attachment data.',
                                        'properties': {
                                            'resourceName': {
                                                'type': 'string',
                                                'description': 'The resource name of the attachment data. This field is used with the media API to download the attachment data.'
                                            },
                                            'attachmentUploadToken': {
                                                'type': 'string',
                                                'description': 'Opaque token containing a reference to an uploaded attachment. Treated by clients as an opaque string and used to create or update Chat messages with attachments.'
                                            }
                                        },
                                        'required': []
                                    }
                                },
                                'required': []
                            }
                        },
                        'thread': {
                            'type': 'object',
                            'description': 'Thread information for routing/replying. Properties:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': """ Resource name of the thread to reply in.
                                             Format: `spaces/{space}/threads/{thread}`. Use this when replying to an
                                            existing thread by its server-assigned name. """
                                },
                                'threadKey': {
                                    'type': 'string',
                                    'description': """ Client-assigned thread key used to create or identify a
                                           thread. Messages sent with the same `threadKey` in the same space are routed to
                                          the same thread. Provide this when you want the server to create/route to a
                                          thread by key rather than by `name`. """
                                }
                            },
                            'required': [
                                'name'
                            ]
                        },
                        'clientAssignedMessageId': {
                            'type': 'string',
                            'description': 'custom ID to identify the message.'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'name',
                'updateMask'
            ]
        }
    }
)
def patch(
    name: str, updateMask: str, allowMissing: Optional[bool] = None,         message: Optional[Dict[str, Union[str, list, dict]]] = None
) -> Dict[str, Union[str, bool, list, dict]]:
    """
    Updates an existing message resource using the PATCH method.

    This method updates the fields of a Chat message identified by its resource
    name. It supports partial updates via the `updateMask` parameter. If the message
    is not found and `allowMissing` is True, a new message is created (requires a
    client-assigned message ID).

    Args:
        name (str): Required. Resource name of the message to update.
            Format: `spaces/{space}/messages/{message}`.
            Examples:
            - `spaces/AAA/messages/BBB.CCC`
            - `spaces/AAA/messages/client-custom-name`
            See: https://developers.google.com/workspace/chat/create-messages#name_a_created_message
        updateMask (str): Required. Comma-separated list of fields to update, or `*` for all.
            Supported values include:
            - `text`
            - `attachment`
            - `cards`
            - `cards_v2`
            - `accessory_widgets`
        allowMissing (Optional[bool]): If True, creates the message if not found (requires a 
            client-assigned ID). Ignores `updateMask` in that case. default is None.
        message (Optional[Dict[str, Union[str, list, dict]]]): A dictionary representing the fields of the message to update.
            Possible keys include:
            - `text` (str): Plain-text body of the message.
            - `fallbackText` (str): Fallback text for message cards.
            - `cards` (list): List of cards to include in the message.
            - `cards_v2` (list): List of version 2 cards (advanced formatting).
            - `attachment` (list): Attachments such as files or media.
            - `thread` (Dict[str, str]): Thread information object.
                - `name` (str): Resource name of the thread, for example `spaces/AAA/threads/BBB`.
                - `threadKey` (str): Optional developer-assigned key used to create or locate a thread.
            - `annotations` (list): Annotations like user mentions, rich links, etc.
            - `clientAssignedMessageId` (str): Optional custom ID to identify the message.

    Returns:
        Dict[str, Union[str, bool, list, dict]]: A dictionary representing the updated message resource, or an empty dict `{}` if the operation fails.
        
        Success case - Returns a message resource dictionary that may include:
            - `name` (str): Resource name of the message.
            - `text` (str): Updated plain-text body of the message.
            - `createTime` (str): Time at which the message was created.
            - `lastUpdateTime` (str): Time at which the message was last edited.
            - `deleteTime` (str): Time at which the message was deleted.
            - `formattedText` (str): Text with formatting markup.
            - `fallbackText` (str): Fallback plain-text for message cards.
            - `argumentText` (str): Message text without mentions.
            - `threadReply` (bool): Whether this is a reply in a thread.
            - `clientAssignedMessageId` (str): Custom ID for the message.
            - `sender` (Dict[str, Union[str, bool]]): Information about the user who sent the message:
                - `name` (str)
                - `displayName` (str)
                - `domainId` (str)
                - `type` (str)
                - `isAnonymous` (bool)
            - `cards` ([List[dict[str, Union[str, List, Dict]]]]): List of legacy card widgets.
            - `cardsV2` (List[dict[str, Union[str, Dict]]]): List of enhanced card widgets with layout and interaction.
            - `annotations` (List[Dict[str, Union[str, Dict, int]]]): Metadata like mentions, emojis, rich links.
            - `thread` (Dict[str, str]): Thread information such as:
                - `name` (str)
                - `threadKey` (str)
            - `space` (Dict[str, Union[str, bool, Dict]]): Space info:
                - `name` (str)
                - `type` (str)
                - `spaceType` (str)
                - `displayName` (str)
                - `threaded` (bool)
                - `spaceHistoryState` (str)
                - `externalUserAllowed` (bool)
                - `adminInstalled` (bool)
                - `spaceUri` (str)
                - and other space-level configuration and metadata
            - `attachment` (List[Dict[str, Union[str, Dict]]]): Attachments such as files or Drive links.
            - `emojiReactionSummaries` (List[Dict[str, Union[Dict, int]]]): List of emoji reaction metadata.
            - `quotedMessageMetadata` (Dict[str, str]): Info about quoted messages.
            - `matchedUrl` (Dict[str, str]): URLs detected in the message.
            - `actionResponse` (Dict[str, Union[str, Dict]]): App-level response types, URLs, or dialog triggers.
            - `deletionMetadata` (Dict[str, str]): Who deleted the message and how.
            - `accessoryWidgets` (List[Dict[str, Dict]]): Optional accessory widgets for enhanced display.
            - Other fields may be present depending on usage and configuration.

        Error cases - Returns empty dict `{}` when:
            - Invalid input parameters (None values, wrong types, empty strings)
            - Invalid message name format (not matching `spaces/{space}/messages/{message}`)
            - Message validation fails (invalid message structure)
            - Message not found and `allowMissing` is False
            - Message not found, `allowMissing` is True, but message ID doesn't start with "client-"

        For complete field definitions, see:
        https://developers.google.com/workspace/chat/api/reference/rest/v1/spaces.messages/patch

    """
    # Input validation
    if name is None:
        return {}
    if not isinstance(name, str):
        return {}
    if not name.strip():
        return {}
    
    if updateMask is None:
        return {}
    if not isinstance(updateMask, str):
        return {}
    if not updateMask.strip():
        return {}
    
    if allowMissing is None:
        allowMissing = False
    if not isinstance(allowMissing, bool):
        return {}
    
    if message is None:
        message = {}
    if not isinstance(message, dict):
        return {}
    
    # Validate message structure using Pydantic
    try:
        validated_message = MessageUpdateInput(**message)
    except ValidationError:
        return {}
        
    print_log(
        f"Patching message {name} with updateMask={updateMask}, "
        f"allowMissing={allowMissing}, message={message}"
    )
    
    # Parse name format
    parts = name.split("/")
    if len(parts) < 4 or parts[0] != "spaces" or parts[2] != "messages":
        print("Invalid name format.")
        return {}
    
    msg_id = parts[3]

    # Look for existing message
    existing = None
    for msg in DB["Message"]:
        if msg.get("name") == name:
            existing = msg  # Reference to actual DB object - modifications auto-save
            break

    # Handle missing message
    if not existing:
        if allowMissing:
            if not msg_id.startswith("client-"):
                print("Not found, allowMissing=True but ID isn't client- => fail.")
                return {}
            
            print("Message not found => create new with client ID.")
            existing = {
                "name": name,
                "text": "",
                "attachment": [],
                "createTime": datetime.now().isoformat() + "Z",
                "sender": {"name": CURRENT_USER_ID.get("id"), "type": "HUMAN"},
            }
            DB["Message"].append(existing)
        else:
            print("Message not found, allowMissing=False => can't update.")
            return {}

    # Parse updateMask
    valid_fields = ["text", "attachment", "cards", "cards_v2", "accessory_widgets"]
    if updateMask.strip() == "*":
        fields_to_update = valid_fields
    else:
        fields_to_update = [f.strip() for f in updateMask.split(",")]

    # Apply updates from validated message
    field_mapping = {
        "text": "text",
        "attachment": "attachment", 
        "cards": "cards",
        "cards_v2": "cardsV2",
        "accessory_widgets": "accessoryWidgets"
    }
    
    for field in fields_to_update:
        if field not in valid_fields:
            print(f"Skipping unknown or unsupported field '{field}'.")
            continue

        internal_field = field_mapping[field]
        
        # Get value from validated message
        if hasattr(validated_message, internal_field):
            new_val = getattr(validated_message, internal_field)
            if new_val is not None:
                existing[internal_field] = new_val
    
    # Update lastUpdateTime for PATCH operations
    existing["lastUpdateTime"] = datetime.now().isoformat() + "Z"
    
    # Note: For existing messages, changes are auto-saved via object reference
    # For new messages (allowMissing=True), they were explicitly added to DB above

    print(f"Patched message => {existing}")
    return existing


@tool_spec(
    spec={
        "name": "delete_message",
        "description": "Deletes a message.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Required. Resource name of the message.\nFormat: `spaces/{space}/messages/{message}`.\nIf you've set a custom ID for your message, you can use the value from\nthe `clientAssignedMessageId` field for `{message}`. For details, see\nhttps://developers.google.com/workspace/chat/create-messages#name_a_created_message"
                },
                "force": {
                    "type": "boolean",
                    "description": "When `true`, deleting a message also deletes its threaded\nreplies. When `false`, if the message has threaded replies, deletion fails.\nOnly applies when authenticating as a user. Has no effect when authenticating\nas a Chat app. Defaults to None."
                }
            },
            "required": [
                "name"
            ]
        }
    }
)
def delete(name: str, force: Optional[bool]=None) -> None:
    """
    Deletes a message.
    
    Args:
        name (str): Required. Resource name of the message.
            Format: `spaces/{space}/messages/{message}`.
            If you've set a custom ID for your message, you can use the value from
            the `clientAssignedMessageId` field for `{message}`. For details, see
            https://developers.google.com/workspace/chat/create-messages#name_a_created_message
        force (Optional[bool]): When `true`, deleting a message also deletes its threaded
            replies. When `false`, if the message has threaded replies, deletion fails.
            Only applies when authenticating as a user. Has no effect when authenticating
            as a Chat app. Defaults to None.

    Returns:
        None: This method does not return a value. If successful, the response body is empty, 
        which indicates that the message is deleted.

    Raises:
        TypeError: If `name` is not a string or `force` is not a boolean or None.
        ValueError: If `name` is empty.
        InvalidMessageNameFormatError: If `name` does not follow the required format.
        UserNotMemberError: If the current user is not a member of the space.
        MessageNotFoundError: If the message is not found.
        MessageHasRepliesError: If the message has replies and `force` is not True.
    """
    # --- Input Validation ---
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    
    if not name:
        raise ValueError("Argument 'name' cannot be empty.")
    
    # Validate message name format: spaces/{space}/messages/{message}
    message_name_pattern = r'^spaces/[^/]+/messages/[^/]+$'
    if not re.match(message_name_pattern, name):
        raise InvalidMessageNameFormatError(
            f"Argument 'name' ('{name}') is not in the expected format 'spaces/{{space}}/messages/{{message}}'."
        )
    
    if force is not None and not isinstance(force, bool):
        raise TypeError("Argument 'force' must be a boolean or None.")
    
    # --- Authorization Check ---
    # Extract space name from message name (e.g., "spaces/AAA/messages/BBB" -> "spaces/AAA")
    name_parts = name.split("/")
    space_name = f"{name_parts[0]}/{name_parts[1]}"
    
    # Check if current user is a member of the space
    if CURRENT_USER_ID and CURRENT_USER_ID.get("id"):
        membership_name = f"{space_name}/members/{CURRENT_USER_ID.get('id')}"
        is_member = any(m.get("name") == membership_name for m in DB.get("Membership", []))
        
        if not is_member:
            raise UserNotMemberError(
                f"User {CURRENT_USER_ID.get('id')} is not a member of {space_name}."
            )
    
    # --- Core Logic ---

    print_log(f"delete_message called with name={name}, force={force}")

    # 1) Locate the message
    target_msg = None
    for m in DB.get("Message", []):
        if m.get("name") == name:
            target_msg = m
            break
    
    if not target_msg:
        raise MessageNotFoundError(f"Message '{name}' not found.")
    
    # 2) Check for threaded replies
    # A reply is any message whose thread references the same thread as our target message
    target_thread_name = target_msg.get("thread", {}).get("name", "")
    replies = []
    
    if target_thread_name:
        for m in DB.get("Message", []):
            thread = m.get("thread", {})
            if (thread.get("name") == target_thread_name and 
                m.get("name") != name):  # Don't count the target message itself
                replies.append(m)
    
    # 3) Handle replies based on force parameter
    if replies:
        if not force:
            raise MessageHasRepliesError(
                f"Message '{name}' has {len(replies)} threaded replies. Set force=True to delete them."
            )
        else:
            # force=True => remove the replies too
            for reply in replies:
                DB["Message"].remove(reply)
    
    # 4) Remove the target message
    DB["Message"].remove(target_msg)

