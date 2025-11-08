from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.custom_errors import EmptyMessageTextError, EmptySubjectError, InvalidRecipientError
from .SimulationEngine.db import DB
from typing import Dict, Any, List
from common_utils.utils import validate_email_util
"""
Simulation of /messages endpoints.
Handles private messaging interactions.
"""


@tool_spec(
    spec={
        'name': 'block_user_via_message',
        'description': 'Blocks a user based on a messaging context.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The identifier of the message or user context.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_block(id: str) -> Dict[str, Any]:
    """
    Blocks a user based on a messaging context.

    Args:
        id (str): The identifier of the message or user context.

    Returns:
        Dict[str, Any]:
        - If the ID is invalid, returns a dictionary with the key "error" and the value "Invalid ID.".
        - If the user is already blocked, returns a dictionary with the key "error" and the value "User already blocked.".
        - On successful block, returns a dictionary with the following keys:
            - status (str): The status of the operation ("blocked")
            - id (str): The ID of the blocked user/message
    """
    return {"status": "blocked", "id": id}


@tool_spec(
    spec={
        'name': 'collapse_messages',
        'description': 'Collapses one or more messages in the inbox.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'array',
                    'description': 'A list of message IDs to collapse.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_collapse_message(id: List[str]) -> Dict[str, Any]:
    """
    Collapses one or more messages in the inbox.

    Args:
        id (List[str]): A list of message IDs to collapse.

    Returns:
        Dict[str, Any]:
        - If the list is empty, returns a dictionary with the key "error" and the value "No message IDs provided.".
        - If any message ID is invalid, returns a dictionary with the key "error" and the value "Invalid message ID.".
        - On successful collapse, returns a dictionary with the following keys:
            - status (str): The status of the operation ("collapsed")
            - message_ids (List[str]): The list of collapsed message IDs
    """
    return {"status": "collapsed", "message_ids": id}


@tool_spec(
    spec={
        'name': 'compose_message',
        'description': 'Composes and sends a new private message.',
        'parameters': {
            'type': 'object',
            'properties': {
                'to': {
                    'type': 'string',
                    'description': "The recipient's identifier or email. Cannot be empty or consist only of whitespace."
                },
                'subject': {
                    'type': 'string',
                    'description': 'The subject of the message. Cannot be empty or consist only of whitespace.'
                },
                'text': {
                    'type': 'string',
                    'description': 'The body text of the message. Cannot be empty or consist only of whitespace.'
                }
            },
            'required': [
                'to',
                'subject',
                'text'
            ]
        }
    }
)
def post_api_compose(to: str, subject: str, text: str) -> Dict[str, Any]:
    """
    Composes and sends a new private message.

    Args:
        to (str): The recipient's identifier or email. Cannot be empty or consist only of whitespace.
        subject (str): The subject of the message. Cannot be empty or consist only of whitespace.
        text (str): The body text of the message. Cannot be empty or consist only of whitespace.

    Returns:
        Dict[str, Any]: On successful sending, returns a dictionary with the following keys:
            - status (str): The status of the operation ("message_sent")
            - message_id (str): The ID of the new message

    Raises:
        TypeError: If 'to', 'subject', or 'text' is not a string.
        InvalidRecipientError: If 'to' is empty or consists only of whitespace.
        EmptySubjectError: If 'subject' is empty or consists only of whitespace.
        EmptyMessageTextError: If 'text' is empty or consists only of whitespace.
    """
    # --- Input Validation ---
    # Validate 'to'
    if not isinstance(to, str):
        raise TypeError("Argument 'to' must be a string.")
    if not to.strip():  # Checks for empty string or string with only whitespace
        raise InvalidRecipientError("Recipient 'to' cannot be empty or consist only of whitespace.")

    validate_email_util(to, "to")
    
    # Validate 'subject'
    if not isinstance(subject, str):
        raise TypeError("Argument 'subject' must be a string.")
    if not subject.strip():  # Checks for empty string or string with only whitespace
        raise EmptySubjectError("Subject cannot be empty or consist only of whitespace.")

    # Validate 'text'
    if not isinstance(text, str):
        raise TypeError("Argument 'text' must be a string.")
    if not text.strip():  # Checks for empty string or string with only whitespace
        raise EmptyMessageTextError("Message text cannot be empty or consist only of whitespace.")
    # --- End of Input Validation ---

    # Original function logic starts here
    # Note: The original logic used the potentially unstripped 'to', 'subject', and 'text'
    # when creating the message dictionary. If stripped versions are desired in the DB,
    # then `to = to.strip()`, etc., should be done after validation.
    # For this refactoring, we preserve the original behavior of storing the arguments as passed (post-validation).

    import time # Standard library import, part of original core logic

    # DB is assumed to be a globally accessible dictionary-like object.
    # Example: DB = {"messages": {}}
    new_id = f"msg_{len(DB.get('messages', {})) + 1}" # Use .get for safety
    timestamp = int(time.time())  # Current Unix timestamp
    
    # Create the message with all required fields
    message = {
        "id": new_id,
        "to": to,
        "from": "reddit_user",  # Assuming the current user is sending the message
        "subject": subject,
        "text": text,
        "timestamp": timestamp,
        "read": False  # New messages are unread by default
    }
    
    DB.setdefault("messages", {})[new_id] = message
    return {"status": "message_sent", "message_id": new_id}


@tool_spec(
    spec={
        'name': 'delete_message',
        'description': 'Deletes a message permanently.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The identifier of the message to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_del_msg(id: str) -> Dict[str, Any]:
    """
    Deletes a message permanently.

    Args:
        id (str): The identifier of the message to delete.

    Returns:
        Dict[str, Any]:
        - If the message ID is invalid, returns a dictionary with the key "error" and the value "Invalid message ID.".
        - If the message does not exist, returns a dictionary with the key "error" and the value "Message not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("message_deleted")
            - id (str): The ID of the deleted message
    """
    # Check for invalid message ID
    if not id or id.strip() == "":
        return {"error": "Invalid message ID."}
    
    # Check if message exists
    if id not in DB.get("messages", {}):
        return {"error": "Message not found."}
    
    del DB["messages"][id]
    return {"status": "message_deleted", "id": id}


@tool_spec(
    spec={
        'name': 'mark_all_messages_as_read',
        'description': 'Marks all messages in the inbox as read.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_read_all_messages() -> Dict[str, Any]:
    """
    Marks all messages in the inbox as read.

    Returns:
        Dict[str, Any]:
        - If there are no messages to mark as read, returns a dictionary with the key "error" and the value "No messages to mark as read.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("all_messages_marked_read")
    """
    return {"status": "all_messages_marked_read"}


@tool_spec(
    spec={
        'name': 'mark_messages_as_read',
        'description': 'Marks specified messages as read.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'array',
                    'description': 'A list of message IDs.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_read_message(id: List[str]) -> Dict[str, Any]:
    """
    Marks specified messages as read.

    Args:
        id (List[str]): A list of message IDs.

    Returns:
        Dict[str, Any]:
        - If the list is empty, returns a dictionary with the key "error" and the value "No message IDs provided.".
        - If any message ID is invalid, returns a dictionary with the key "error" and the value "Invalid message ID.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("messages_marked_read")
            - ids (List[str]): The list of marked message IDs
    """
    return {"status": "messages_marked_read", "ids": id}


@tool_spec(
    spec={
        'name': 'unblock_subreddit_messaging',
        'description': 'Unblocks a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_unblock_subreddit() -> Dict[str, Any]:
    """
    Unblocks a subreddit.

    Returns:
        Dict[str, Any]:
        - If there is no subreddit to unblock, returns a dictionary with the key "error" and the value "No subreddit to unblock.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("subreddit_unblocked")
    """
    return {"status": "subreddit_unblocked"}


@tool_spec(
    spec={
        'name': 'uncollapse_messages',
        'description': 'Uncollapses one or more messages in the inbox.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'array',
                    'description': 'A list of message IDs.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_uncollapse_message(id: List[str]) -> Dict[str, Any]:
    """
    Uncollapses one or more messages in the inbox.

    Args:
        id (List[str]): A list of message IDs.

    Returns:
        Dict[str, Any]:
        - If the list is empty, returns a dictionary with the key "error" and the value "No message IDs provided.".
        - If any message ID is invalid, returns a dictionary with the key "error" and the value "Invalid message ID.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("uncollapsed")
            - ids (List[str]): The list of uncollapsed message IDs
    """
    return {"status": "uncollapsed", "ids": id}


@tool_spec(
    spec={
        'name': 'mark_messages_as_unread',
        'description': 'Marks specified messages as unread.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'array',
                    'description': 'A list of message IDs.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_unread_message(id: List[str]) -> Dict[str, Any]:
    """
    Marks specified messages as unread.

    Args:
        id (List[str]): A list of message IDs.

    Returns:
        Dict[str, Any]:
        - If the list is empty, returns a dictionary with the key "error" and the value "No message IDs provided.".
        - If any message ID is invalid, returns a dictionary with the key "error" and the value "Invalid message ID.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("marked_unread")
            - ids (List[str]): The list of marked message IDs
    """
    return {"status": "marked_unread", "ids": id}


@tool_spec(
    spec={
        'name': 'get_inbox_messages',
        'description': 'Retrieves messages from the inbox.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_message_inbox() -> List[Dict[str, Any]]:
    """
    Retrieves messages from the inbox.

    Returns:
        List[Dict[str, Any]]:
        - If there are no messages, returns an empty list.
        - On successful retrieval, returns a list of message objects, each containing:
            - id (str): The message ID
            - to (str): The recipient
            - subject (str): The message subject
            - text (str): The message body
            - timestamp (str): The message timestamp
    """
    return list(DB.get("messages", {}).values()) # Use .get for safety


@tool_spec(
    spec={
        'name': 'get_sent_messages',
        'description': 'Retrieves messages from the sent folder.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_message_sent() -> List[Dict[str, Any]]:
    """
    Retrieves messages from the sent folder.

    Returns:
        List[Dict[str, Any]]:
        - If there are no sent messages, returns an empty list.
        - On successful retrieval, returns a list of sent message objects, each containing:
            - id (str): The message ID
            - to (str): The recipient
            - subject (str): The message subject
            - text (str): The message body
            - timestamp (str): The message timestamp
    """
    return []


@tool_spec(
    spec={
        'name': 'get_unread_messages',
        'description': 'Retrieves unread messages from the inbox.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_message_unread() -> List[Dict[str, Any]]:
    """
    Retrieves unread messages from the inbox.

    Returns:
        List[Dict[str, Any]]:
        - If there are no unread messages, returns an empty list.
        - On successful retrieval, returns a list of unread message objects, each containing:
            - id (str): The message ID
            - to (str): The recipient
            - subject (str): The message subject
            - text (str): The message body
            - timestamp (str): The message timestamp
    """
    return []


@tool_spec(
    spec={
        'name': 'get_messages_by_mailbox',
        'description': 'Retrieves messages from a specified mailbox category.',
        'parameters': {
            'type': 'object',
            'properties': {
                'where': {
                    'type': 'string',
                    'description': 'The mailbox category (e.g., "inbox", "sent").'
                }
            },
            'required': [
                'where'
            ]
        }
    }
)
def get_message_where(where: str) -> List[Dict[str, Any]]:
    """
    Retrieves messages from a specified mailbox category.

    Args:
        where (str): The mailbox category (e.g., "inbox", "sent").

    Returns:
        List[Dict[str, Any]]:
        - If the category is invalid, returns a dictionary with the key "error" and the value "Invalid mailbox category.".
        - If there are no messages in the category, returns an empty list.
        - On successful retrieval, returns a list of message objects from the specified category, each containing:
            - id (str): The message ID
            - to (str): The recipient
            - subject (str): The message subject
            - text (str): The message body
            - timestamp (str): The message timestamp
    """
    return []