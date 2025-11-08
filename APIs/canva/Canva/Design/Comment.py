from common_utils.tool_spec_decorator import tool_spec
import uuid
import time
import re
from typing import Optional, Dict, Any, List, Union

from canva.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'create_comment_thread',
        'description': 'Creates a new comment thread on a design.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The ID of the design to add a comment to.'
                },
                'message': {
                    'type': 'string',
                    'description': """ The plaintext body of the comment. User mentions must follow 
                    the format [user_id:team_id]. """
                },
                'assignee_id': {
                    'type': 'string',
                    'description': """ Optional ID of the user to assign the comment to.
                    The user must be mentioned in the comment message. """
                }
            },
            'required': [
                'design_id',
                'message'
            ]
        }
    }
)
def create_thread(
    design_id: str, message: str, assignee_id: Optional[str] = None
) -> Dict[str, Union[str, Dict]]:
    """
    Creates a new comment thread on a design.

    Args:
        design_id (str): The ID of the design to add a comment to.
        message (str): The plaintext body of the comment. User mentions must follow 
            the format [user_id:team_id].
        assignee_id (Optional[str]): Optional ID of the user to assign the comment to.
            The user must be mentioned in the comment message.

    Returns:
        Dict[str, Union[str, Dict]]: Dictionary containing thread data with keys:
            - 'thread' (Dict[str, Union[str, Any]]): The created thread object with fields:
                - 'id' (str): Thread ID.
                - 'design_id' (str): The design ID.
                - 'thread_type' (Dict[str, str]): Type information with 'type' key.
                - 'content' (Dict[str, Union[str, Dict]]): Content information including:
                    - 'plaintext' (str): The message text.
                    - 'mentions' (Dict[str, Union[str, Dict]]): User mentions data.
                - 'assignee' (Optional[Dict[str, str]]): Assigned user metadata.
                - 'resolver' (Optional[Dict[str, str]]): Resolver user metadata.
                - 'author' (Dict[str, str]): Author metadata.
                - 'created_at' (int): Creation timestamp.
                - 'updated_at' (int): Last update timestamp.

    Raises:
        ValueError: If design_id or message is empty, if assignee_id is invalid,
            if design not found, or if assignee is not mentioned in message.
    """
    # Input validation
    if not isinstance(design_id, str) or not design_id:
        raise ValueError("design_id must be a non-empty string")
    if not isinstance(message, str) or not message:
        raise ValueError("message must be a non-empty string")
    if assignee_id is not None and (not isinstance(assignee_id, str) or not assignee_id):
        raise ValueError("assignee_id must be a non-empty string if provided")
    
    # Check if design exists
    if design_id not in DB["Designs"]:
        raise ValueError(f"Design with ID {design_id} not found")
    
    thread_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # Parse mentions from message
    mentions = {}
    mention_pattern = r'\[([^:]+):([^\]]+)\]'
    for match in re.finditer(mention_pattern, message):
        user_id, team_id = match.groups()
        mention_key = f"{user_id}:{team_id}"
        mentions[mention_key] = {
            "tag": f"@{user_id}",
            "user": {
                "user_id": user_id,
                "team_id": team_id,
                "display_name": f"User {user_id}"
            }
        }
    
    # Create assignee object if provided
    assignee = None
    if assignee_id:
        # Check if assignee is mentioned in the message
        assignee_mentioned = any(mention["user"]["user_id"] == assignee_id for mention in mentions.values())
        if not assignee_mentioned:
            raise ValueError("assignee_id must be mentioned in the comment message")
        
        assignee = {
            "user_id": assignee_id,
            "team_id": "default_team",
            "display_name": f"User {assignee_id}"
        }
    
    thread = {
        "id": thread_id,
        "design_id": design_id,
        "thread_type": {"type": "comment"},
        "content": {
            "plaintext": message,
            "mentions": mentions
        },
        "assignee": assignee,
        "resolver": None,
        "author": {
            "user_id": "current_user",
            "team_id": "default_team",
            "display_name": "Current User"
        },
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    # Store in database
    if "CommentThreads" not in DB:
        DB["CommentThreads"] = {}
    DB["CommentThreads"][thread_id] = thread
    
    return {"thread": thread}


@tool_spec(
    spec={
        'name': 'create_comment_reply',
        'description': 'Adds a reply to a comment thread on a design.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The ID of the design the thread belongs to.'
                },
                'thread_id': {
                    'type': 'string',
                    'description': 'The ID of the thread to reply to.'
                },
                'message': {
                    'type': 'string',
                    'description': """ The plaintext message body of the reply. Mentions use 
                    [user_id:team_id] format. """
                }
            },
            'required': [
                'design_id',
                'thread_id',
                'message'
            ]
        }
    }
)
def create_reply(design_id: str, thread_id: str, message: str) -> Dict[str, Union[str, Dict]]:
    """
    Adds a reply to a comment thread on a design.

    Args:
        design_id (str): The ID of the design the thread belongs to.
        thread_id (str): The ID of the thread to reply to.
        message (str): The plaintext message body of the reply. Mentions use 
            [user_id:team_id] format.

    Returns:
        Dict[str, Union[str, Dict]]: Dictionary containing reply data with keys:
            - 'reply' (Dict[str, Union[str, Any]]): The created reply object with fields:
                - 'id' (str): Reply ID.
                - 'design_id' (str): The design ID.
                - 'thread_id' (str): The parent thread ID.
                - 'content' (Dict[str, Union[str, Dict]]): Content information including:
                    - 'plaintext' (str): The reply message.
                    - 'mentions' (Dict[str, Union[str, Dict]]): User mentions data.
                - 'author' (Dict[str, str]): Author metadata.
                - 'created_at' (int): Creation timestamp.
                - 'updated_at' (int): Last update timestamp.

    Raises:
        ValueError: If design_id, thread_id, or message is empty, if design not found,
            if thread not found, or if thread doesn't belong to the design.
    """
    # Input validation
    if not isinstance(design_id, str) or not design_id:
        raise ValueError("design_id must be a non-empty string")
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("thread_id must be a non-empty string")
    if not isinstance(message, str) or not message:
        raise ValueError("message must be a non-empty string")
    
    # Check if design exists
    if design_id not in DB["Designs"]:
        raise ValueError(f"Design with ID {design_id} not found")
    
    # Check if thread exists
    if "CommentThreads" not in DB or thread_id not in DB["CommentThreads"]:
        raise ValueError(f"Thread with ID {thread_id} not found")
    
    # Verify thread belongs to the design
    thread = DB["CommentThreads"][thread_id]
    if thread["design_id"] != design_id:
        raise ValueError(f"Thread {thread_id} does not belong to design {design_id}")
    
    reply_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # Parse mentions from message
    mentions = {}
    mention_pattern = r'\[([^:]+):([^\]]+)\]'
    for match in re.finditer(mention_pattern, message):
        user_id, team_id = match.groups()
        mention_key = f"{user_id}:{team_id}"
        mentions[mention_key] = {
            "tag": f"@{user_id}",
            "user": {
                "user_id": user_id,
                "team_id": team_id,
                "display_name": f"User {user_id}"
            }
        }
    
    reply = {
        "id": reply_id,
        "design_id": design_id,
        "thread_id": thread_id,
        "content": {
            "plaintext": message,
            "mentions": mentions
        },
        "author": {
            "user_id": "current_user",
            "team_id": "default_team",
            "display_name": "Current User"
        },
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    # Store in database
    if "CommentReplies" not in DB:
        DB["CommentReplies"] = {}
    DB["CommentReplies"][reply_id] = reply
    
    return {"reply": reply}


@tool_spec(
    spec={
        'name': 'get_comment_thread',
        'description': 'Retrieves a specific comment thread from a design.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The design ID.'
                },
                'thread_id': {
                    'type': 'string',
                    'description': 'The ID of the thread to retrieve.'
                }
            },
            'required': [
                'design_id',
                'thread_id'
            ]
        }
    }
)
def get_thread(design_id: str, thread_id: str) -> Dict[str, Union[str, Dict]]:
    """
    Retrieves a specific comment thread from a design.

    Args:
        design_id (str): The design ID.
        thread_id (str): The ID of the thread to retrieve.

    Returns:
        Dict[str, Union[str, Dict]]: Dictionary containing thread data with keys:
            - 'thread' (Dict[str, Union[str, Any]]): The thread object with fields:
                - 'id' (str): Thread ID.
                - 'design_id' (str): The design ID.
                - 'thread_type' (Dict[str, str]): Type information.
                - 'content' (Dict[str, Union[str, Dict]]): Content including plaintext and mentions.
                - 'suggested_edits' (Optional[List[Any]]): Edit metadata if applicable.
                - 'assignee' (Optional[Dict[str, str]]): Assignee information.
                - 'resolver' (Optional[Dict[str, str]]): Resolver information.
                - 'author' (Dict[str, str]): Author metadata.
                - 'created_at' (int): Creation timestamp.
                - 'updated_at' (int): Last update timestamp.

    Raises:
        ValueError: If design_id or thread_id is empty, if design not found,
            if thread not found, or if thread doesn't belong to the design.
    """
    # Input validation
    if not isinstance(design_id, str) or not design_id:
        raise ValueError("design_id must be a non-empty string")
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("thread_id must be a non-empty string")
    
    # Check if design exists
    if design_id not in DB["Designs"]:
        raise ValueError(f"Design with ID {design_id} not found")
    
    # Check if thread exists
    if "CommentThreads" not in DB or thread_id not in DB["CommentThreads"]:
        raise ValueError(f"Thread with ID {thread_id} not found")
    
    # Verify thread belongs to the design
    thread = DB["CommentThreads"][thread_id]
    if thread["design_id"] != design_id:
        raise ValueError(f"Thread {thread_id} does not belong to design {design_id}")
    
    return {"thread": thread}


@tool_spec(
    spec={
        'name': 'get_comment_reply',
        'description': 'Retrieves a specific reply from a thread on a design.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The ID of the design.'
                },
                'thread_id': {
                    'type': 'string',
                    'description': 'The ID of the thread the reply belongs to.'
                },
                'reply_id': {
                    'type': 'string',
                    'description': 'The ID of the reply to retrieve.'
                }
            },
            'required': [
                'design_id',
                'thread_id',
                'reply_id'
            ]
        }
    }
)
def get_reply(design_id: str, thread_id: str, reply_id: str) -> Dict[str, Union[str, Dict]]:
    """
    Retrieves a specific reply from a thread on a design.

    Args:
        design_id (str): The ID of the design.
        thread_id (str): The ID of the thread the reply belongs to.
        reply_id (str): The ID of the reply to retrieve.

    Returns:
        Dict[str, Union[str, Dict]]: Dictionary containing reply data with keys:
            - 'reply' (Dict[str, Union[str, Any]]): The reply object with fields:
                - 'id' (str): Reply ID.
                - 'design_id' (str): The design ID.
                - 'thread_id' (str): The parent thread ID.
                - 'content' (Dict[str, Union[str, Dict]]): Content including plaintext and mentions.
                - 'author' (Dict[str, str]): Author metadata.
                - 'created_at' (int): Creation timestamp.
                - 'updated_at' (int): Last update timestamp.

    Raises:
        ValueError: If design_id, thread_id, or reply_id is empty, if design not found,
            if thread not found, if thread doesn't belong to design, if reply not found,
            or if reply doesn't belong to thread.
    """
    # Input validation
    if not isinstance(design_id, str) or not design_id:
        raise ValueError("design_id must be a non-empty string")
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("thread_id must be a non-empty string")
    if not isinstance(reply_id, str) or not reply_id:
        raise ValueError("reply_id must be a non-empty string")
    
    # Check if design exists
    if design_id not in DB["Designs"]:
        raise ValueError(f"Design with ID {design_id} not found")
    
    # Check if thread exists
    if "CommentThreads" not in DB or thread_id not in DB["CommentThreads"]:
        raise ValueError(f"Thread with ID {thread_id} not found")
    
    # Verify thread belongs to the design
    thread = DB["CommentThreads"][thread_id]
    if thread["design_id"] != design_id:
        raise ValueError(f"Thread {thread_id} does not belong to design {design_id}")
    
    # Check if reply exists
    if "CommentReplies" not in DB or reply_id not in DB["CommentReplies"]:
        raise ValueError(f"Reply with ID {reply_id} not found")
    
    # Verify reply belongs to the thread
    reply = DB["CommentReplies"][reply_id]
    if reply["thread_id"] != thread_id:
        raise ValueError(f"Reply {reply_id} does not belong to thread {thread_id}")
    
    return {"reply": reply}


@tool_spec(
    spec={
        'name': 'list_comment_replies',
        'description': 'Lists replies from a specific thread on a design.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The ID of the design.'
                },
                'thread_id': {
                    'type': 'string',
                    'description': 'The ID of the thread.'
                },
                'limit': {
                    'type': 'integer',
                    'description': """ Max number of replies to return. Default is 50,
                    minimum is 1, maximum is 100. """
                },
                'continuation': {
                    'type': 'string',
                    'description': 'Token for paginated results.'
                }
            },
            'required': [
                'design_id',
                'thread_id'
            ]
        }
    }
)
def list_replies(
    design_id: str,
    thread_id: str,
    limit: Optional[int] = 50,
    continuation: Optional[str] = None,
) -> Dict[str, Union[str, List[Dict[str, Union[str, int, Dict]]]]]:
    """
    Lists replies from a specific thread on a design.

    Args:
        design_id (str): The ID of the design.
        thread_id (str): The ID of the thread.
        limit (Optional[int]): Max number of replies to return. Default is 50,
            minimum is 1, maximum is 100.
        continuation (Optional[str]): Token for paginated results.

    Returns:
        Dict[str, Union[str, List[Dict[str, Union[str, int, Dict]]]]]: Dictionary containing reply list with keys:
            - 'items' (List[Dict[str, Union[str, int, Dict]]]): List of reply objects, each containing:
                - 'id' (str): Reply ID.
                - 'design_id' (str): The design ID.
                - 'thread_id' (str): The parent thread ID.
                - 'content' (Dict[str, Union[str, Dict]]): Content including plaintext and mentions.
                - 'author' (Dict[str, str]): Author metadata.
                - 'created_at' (int): Creation timestamp.
                - 'updated_at' (int): Last update timestamp.
            - 'continuation' (Optional[str]): Token for fetching next results.

    Raises:
        ValueError: If design_id or thread_id is empty, if limit is not between 1-100,
            if continuation is invalid, if design not found, if thread not found,
            or if thread doesn't belong to design.
    """
    # Input validation
    if not isinstance(design_id, str) or not design_id:
        raise ValueError("design_id must be a non-empty string")
    if not isinstance(thread_id, str) or not thread_id:
        raise ValueError("thread_id must be a non-empty string")
    if limit is not None and (not isinstance(limit, int) or limit < 1 or limit > 100):
        raise ValueError("limit must be an integer between 1 and 100")
    if continuation is not None and (not isinstance(continuation, str) or not continuation):
        raise ValueError("continuation must be a non-empty string if provided")
    
    # Set default limit
    if limit is None:
        limit = 50
    
    # Check if design exists
    if design_id not in DB["Designs"]:
        raise ValueError(f"Design with ID {design_id} not found")
    
    # Check if thread exists
    if "CommentThreads" not in DB or thread_id not in DB["CommentThreads"]:
        raise ValueError(f"Thread with ID {thread_id} not found")
    
    # Verify thread belongs to the design
    thread = DB["CommentThreads"][thread_id]
    if thread["design_id"] != design_id:
        raise ValueError(f"Thread {thread_id} does not belong to design {design_id}")
    
    # Get all replies for this thread
    if "CommentReplies" not in DB:
        return {"items": []}
    
    all_replies = [reply for reply in DB["CommentReplies"].values() 
                   if reply["thread_id"] == thread_id]
    
    # Sort by created_at (oldest first)
    all_replies.sort(key=lambda x: x["created_at"])
    
    # Handle pagination with continuation token
    start_index = 0
    if continuation:
        # Find the index of the reply with the continuation ID
        try:
            start_index = next(i for i, reply in enumerate(all_replies) 
                             if reply["id"] == continuation) + 1
        except StopIteration:
            raise ValueError(f"Invalid continuation token: {continuation}")
    
    # Get the page of results
    replies_page = all_replies[start_index:start_index + limit]
    
    # Prepare response
    response = {"items": replies_page}
    
    # Add continuation token if there are more results
    if start_index + limit < len(all_replies):
        response["continuation"] = replies_page[-1]["id"] if replies_page else None
    
    return response
