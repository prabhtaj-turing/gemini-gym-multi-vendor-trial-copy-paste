"""
Reactions resource for Slack API simulation.

This module provides functionality for managing reactions in Slack.
It simulates the reactions-related endpoints of the Slack API.
"""
from common_utils.tool_spec_decorator import tool_spec
# import time
from typing import Dict, Any, Optional

from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    ChannelNotFoundError, 
    MessageNotFoundError, 
    AlreadyReactionError, 
    InvalidCursorValueError,
    MissingRequiredArgumentsError,
    NoReactionsOnMessageError,
    ReactionNotFoundError,
    UserHasNotReactedError
)

from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'get_message_reactions',
        'description': """ Gets reactions for a specific message in a channel.
        
        This function is used to get reactions for a specific message in a channel.
        It can return either a summary of the reactions or all the reaction details.
        If full is True, it returns all the reaction details.
        If full is False, it returns a summary of the reactions. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'channel_id': {
                    'type': 'string',
                    'description': 'ID of the channel. Cannot be empty.'
                },
                'message_ts': {
                    'type': 'string',
                    'description': """ The timestamp of the message to get reactions for.
                    This should be a string representation of a Unix timestamp with
                    up to 6 decimal places for microsecond precision. Cannot be empty. """
                },
                'full': {
                    'type': 'boolean',
                    'description': 'If true, return all reaction details. Defaults to False.'
                }
            },
            'required': [
                'channel_id',
                'message_ts'
            ]
        }
    }
)
def get(channel_id: str, message_ts: str, full: bool = False) -> Dict[str, Any]:
    """
    Gets reactions for a specific message in a channel.

    This function is used to get reactions for a specific message in a channel.
    It can return either a summary of the reactions or all the reaction details.
    If full is True, it returns all the reaction details.
    If full is False, it returns a summary of the reactions.

    Args:
        channel_id (str): ID of the channel. Cannot be empty.
        message_ts (str): The timestamp of the message to get reactions for.
            This should be a string representation of a Unix timestamp with
            up to 6 decimal places for microsecond precision. Cannot be empty.
        full (bool): If true, return all reaction details. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing the status of the operation and
            the requested reaction data.
            - ok (bool): Indicates if the request was successful.
            - reactions (Union[List[Dict[str, Any]], Dict[str, int]]):
                If `full` is True, a list of reaction objects with the
                following keys:
                    - name (str): The name of the reaction emoji.
                    - users (List[str]): A list of user IDs who have
                      used this reaction on this specific message.
                    - count (int): The total number of users who have
                      used this reaction on this message.
                If `full` is False, a dictionary mapping each reaction
                name (str) to the total count of all users who have
                used it on this message (int).

    Raises:
        TypeError: If `channel_id` or `message_ts` is not a string, or if `full` is not a boolean.
        ValueError: If `channel_id` or `message_ts` is an empty string.
        ChannelNotFoundError: If the specified `channel_id` does not exist in the database.
        MessageNotFoundError: If the specified `message_ts` does not correspond to a message
            within the given `channel_id`.
    """
    # Input validation for non-dictionary types
    if not isinstance(channel_id, str):
        raise TypeError("channel_id must be a string.")
    if not channel_id:
        raise ValueError("channel_id cannot be empty.")

    if not isinstance(message_ts, str):
        raise TypeError("message_ts must be a string.")
    if not message_ts:
        raise ValueError("message_ts cannot be empty.")

    if not isinstance(full, bool):
        raise TypeError("full must be a boolean.")

    # Core logic, adapted to raise custom exceptions
    # DB is assumed to be defined in the global scope or accessible.
    if channel_id not in DB.get("channels", {}):
        raise ChannelNotFoundError(f"Channel with ID '{channel_id}' not found.")

    messages = DB["channels"][channel_id].get("messages", [])
    message_data = None
    for msg in messages:
        # Direct comparison - only matches if ts exists and equals message_ts
        if msg.get("ts") == message_ts:
            message_data = msg
            break

    if not message_data:
        raise MessageNotFoundError(f"Message with timestamp '{message_ts}' not found in channel '{channel_id}'.")

    reactions_data = message_data.get("reactions", [])

    if full:
        return {"ok": True, "reactions": reactions_data}
    else:
        summary = {}
        for reaction in reactions_data:
            name = reaction["name"]
            summary[name] = summary.get(name, 0) + reaction.get("count", 0) # Prefer count from reaction obj
        return {"ok": True, "reactions": summary}


@tool_spec(
    spec={
        'name': 'add_reaction_to_message',
        'description': 'Adds a reaction to a message.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID. Must be a non-empty string.'
                },
                'channel_id': {
                    'type': 'string',
                    'description': 'ID of the channel. Must be a non-empty string.'
                },
                'name': {
                    'type': 'string',
                    'description': 'Reaction (emoji) name. Must be a non-empty string.'
                },
                'message_ts': {
                    'type': 'string',
                    'description': """ Timestamp of the message. This should be a string
                    representation of a Unix timestamp with up to 6 decimal places
                    for microsecond precision. Must be a non-empty string. """
                }
            },
            'required': [
                'user_id',
                'channel_id',
                'name',
                'message_ts'
            ]
        }
    }
)
def add(user_id: str, channel_id: str, name: str, message_ts: str) -> Dict[str, Any]:
    """
    Adds a reaction to a message.

    Args:
        user_id (str): User ID. Must be a non-empty string.
        channel_id (str): ID of the channel. Must be a non-empty string.
        name (str): Reaction (emoji) name. Must be a non-empty string.
        message_ts (str): Timestamp of the message. This should be a string
            representation of a Unix timestamp with up to 6 decimal places
            for microsecond precision. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the request was successful.
            - message ([Dict[str, Any]): The updated message object if successful
              with the following keys:
                - ts (str): The timestamp of the message.
                - user (str): The ID of the user who posted the message.
                - text (str): The text content of the message.
                - reactions (List[Dict[str, Any]]): A list of reaction objects.
                    - name (str): The name of the reaction emoji.
                    - users (List[str]): A list of user IDs who have used this reaction.
                    - count (int): The total number of users who have used this reaction.

    Raises:
        TypeError: If user_id, channel_id, name, or message_ts is not a string.
        ValueError: If user_id, channel_id, name, or message_ts is an empty string or just whitespace.
        ChannelNotFoundError: If the specified channel does not exist.
        MessageNotFoundError: If the specified message does not exist in the channel.
        AlreadyReactionError: If the user has already reacted with this emoji.
    """
    # Input Validation
    if not isinstance(user_id, str):
        raise TypeError(f"user_id must be a string, got {type(user_id).__name__}")
    if not user_id or not user_id.strip():
        raise ValueError("user_id cannot be empty or just whitespace")

    if not isinstance(channel_id, str):
        raise TypeError(f"channel_id must be a string, got {type(channel_id).__name__}")
    if not channel_id or not channel_id.strip():
        raise ValueError("channel_id cannot be empty or just whitespace")

    if not isinstance(name, str):
        raise TypeError(f"name must be a string, got {type(name).__name__}")
    if not name or not name.strip():
        raise ValueError("name cannot be empty or just whitespace")

    if not isinstance(message_ts, str):
        raise TypeError(f"message_ts must be a string, got {type(message_ts).__name__}")
    if not message_ts or not message_ts.strip():
        raise ValueError("message_ts cannot be empty or just whitespace")

    # --- Original Core Logic ---
    if channel_id not in DB["channels"]:
        raise ChannelNotFoundError(f"channel not found.")

    messages = DB["channels"][channel_id].get("messages", [])
    message = next((msg for msg in messages if msg["ts"] == message_ts), None)

    if not message:
        raise MessageNotFoundError('message not found.')

    if "reactions" not in message:
        message["reactions"] = []

    # Check if the user already reacted with this emoji
    for reaction in message["reactions"]:
        if reaction["name"] == name and user_id in reaction["users"]:
            raise AlreadyReactionError('user has already reacted with this emoji.')

    # Add the reaction (or update existing)
    found = False
    for reaction in message["reactions"]:
        if reaction["name"] == name:
            reaction["users"].append(user_id)
            reaction["count"] += 1
            found = True
            break

    if not found:
        message["reactions"].append({
            "name": name,
            "users": [user_id],
            "count": 1
        })

    return {"ok": True, "message": message}


@tool_spec(
    spec={
        'name': 'list_user_reactions',
        'description': 'Lists reactions made by a user (or all users if user_id is None).',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': """ Show reactions made by this user. Defaults to None (all users).
                    If provided, must be a non-empty string. """
                },
                'full': {
                    'type': 'boolean',
                    'description': 'If true, return all reaction details. Defaults to False.'
                },
                'cursor': {
                    'type': 'string',
                    'description': """ Parameter for pagination. Defaults to None.
                    If provided, must be a string that can be parsed as a non-negative integer. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of items to return. Defaults to 100.
                    Must be a positive integer. """
                }
            },
            'required': []
        }
    }
)
def list(user_id: Optional[str] = None, full: bool = False, cursor: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Lists reactions made by a user (or all users if user_id is None).

    Args:
        user_id (Optional[str]): Show reactions made by this user. Defaults to None (all users).
            If provided, must be a non-empty string.
        full (bool): If true, return all reaction details. Defaults to False.
        cursor (Optional[str]): Parameter for pagination. Defaults to None.
            If provided, must be a string that can be parsed as a non-negative integer.
        limit (int): The maximum number of items to return. Defaults to 100.
            Must be a positive integer.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Always True for successful retrieval
            - reactions (List[Dict[str, Any]]): List of reaction objects, each containing:
                - channel (str): Channel ID
                - message_ts (str): Message timestamp
                - name (str): Reaction name
                - count (int): Number of users who reacted
                - users (Optional[List[str]]): List of user IDs who reacted (only if full=True)
            - response_metadata (Dict[str, Any]): Pagination information
                - next_cursor (Optional[str]): Cursor for next page of results

    Raises:
        TypeError: If user_id is not a string or None, if full is not a boolean, 
                  if cursor is not a string or None, or if limit is not an integer.
        ValueError: If user_id is an empty string, if limit is not positive,
                   or if cursor is an empty string.
        InvalidCursorValueError: If cursor cannot be parsed as a non-negative integer.
    """
    # Input type validation
    if user_id is not None and not isinstance(user_id, str):
        raise TypeError("user_id must be a string or None.")
    if not isinstance(full, bool):
        raise TypeError("full must be a boolean.")
    if cursor is not None and not isinstance(cursor, str):
        raise TypeError("cursor must be a string or None.")
    if type(limit) is not int:
        raise TypeError("limit must be an integer.")
    
    # Input value validation
    if user_id is not None and not user_id:
        raise ValueError("user_id cannot be empty.")
    if cursor is not None and not cursor:
        raise ValueError("cursor cannot be empty.")
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")

    # Cursor validation
    start_index = 0
    if cursor:
        try:
            start_index = int(cursor)
            if start_index < 0:
                raise InvalidCursorValueError("cursor must represent a non-negative integer.")
        except ValueError:
            raise InvalidCursorValueError(f"cursor must be a string representing a valid integer, got: '{cursor}'")

    # Core logic - collect all reactions
    all_reactions = []
    for channel_id, channel_data in DB["channels"].items():
        for message in channel_data.get("messages", []):
            for reaction in message.get("reactions", []):
                if user_id is None or (user_id in reaction["users"]):
                    reaction_info = {
                        "channel": channel_id,
                        "message_ts": message["ts"],
                        "name": reaction["name"],
                        "count": reaction["count"],
                        "users": reaction["users"] if full else None,
                    }
                    all_reactions.append(reaction_info)

    # Pagination
    end_index = min(start_index + limit, len(all_reactions))
    paginated_reactions = all_reactions[start_index:end_index]

    next_cursor = str(end_index) if end_index < len(all_reactions) else None

    return {
        "ok": True,
        "reactions": paginated_reactions,
        "response_metadata": {"next_cursor": next_cursor}
    }


@tool_spec(
    spec={
        'name': 'remove_reaction_from_message',
        'description': 'Removes a reaction from a message.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID. Must be a non-empty string.'
                },
                'name': {
                    'type': 'string',
                    'description': 'Reaction (emoji) name. Must be a non-empty string.'
                },
                'channel_id': {
                    'type': 'string',
                    'description': 'ID of the channel. Must be a non-empty string.'
                },
                'message_ts': {
                    'type': 'string',
                    'description': 'Timestamp of the message. Must be a non-empty string.'
                }
            },
            'required': [
                'user_id',
                'name',
                'channel_id',
                'message_ts'
            ]
        }
    }
)
def remove(user_id: str, name: str, channel_id: str, message_ts: str) -> Dict[str, Any]:
    """
    Removes a reaction from a message.

    Args:
        user_id (str): User ID. Must be a non-empty string.
        name (str): Reaction (emoji) name. Must be a non-empty string.
        channel_id (str): ID of the channel. Must be a non-empty string.
        message_ts (str): Timestamp of the message. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Always True for successful removal

    Raises:
        TypeError: If user_id, name, channel_id, or message_ts is not a string.
        MissingRequiredArgumentsError: If any of the required arguments is an empty string.
        ChannelNotFoundError: If the specified channel does not exist.
        MessageNotFoundError: If the specified message does not exist in the channel.
        NoReactionsOnMessageError: If the message has no reactions.
        ReactionNotFoundError: If the specified reaction is not found on the message.
        UserHasNotReactedError: If the user has not reacted with this emoji.
    """
    # Input type validation
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    if not isinstance(name, str):
        raise TypeError("name must be a string.")
    if not isinstance(channel_id, str):
        raise TypeError("channel_id must be a string.")
    if not isinstance(message_ts, str):
        raise TypeError("message_ts must be a string.")
    
    # Input value validation
    if not all([user_id, name, channel_id, message_ts]):
        missing_args = []
        if not user_id:
            missing_args.append("user_id")
        if not name:
            missing_args.append("name")
        if not channel_id:
            missing_args.append("channel_id")
        if not message_ts:
            missing_args.append("message_ts")
        raise MissingRequiredArgumentsError(f"Required arguments cannot be empty: {', '.join(missing_args)}")

    # Check if channel exists
    if channel_id not in DB["channels"]:
        raise ChannelNotFoundError(f"Channel with ID '{channel_id}' not found.")

    # Check if message exists
    messages = DB["channels"][channel_id].get("messages", [])
    message = next((msg for msg in messages if msg["ts"] == message_ts), None)

    if not message:
        raise MessageNotFoundError(f"Message with timestamp '{message_ts}' not found in channel '{channel_id}'.")

    # Check if message has reactions
    if "reactions" not in message:
        raise NoReactionsOnMessageError(f"Message with timestamp '{message_ts}' has no reactions.")

    reactions = message.get("reactions", [])
    reaction_index = next((i for i, r in enumerate(reactions) if r["name"] == name), None)

    # Check if reaction exists
    if reaction_index is None:
        raise ReactionNotFoundError(f"Reaction '{name}' not found on message with timestamp '{message_ts}'.")

    # Check if user has reacted
    if user_id not in reactions[reaction_index]["users"]:
        raise UserHasNotReactedError(f"User '{user_id}' has not reacted with '{name}' on this message.")

    # Remove the user from the reaction
    reactions[reaction_index]["users"].remove(user_id)
    reactions[reaction_index]["count"] -= 1

    # Update the message
    message["reactions"] = reactions

    # If no users are left, remove the entire reaction
    if reactions[reaction_index]["count"] == 0:
        del message["reactions"][reaction_index]

    # Update the DB
    for i, msg in enumerate(DB["channels"][channel_id]["messages"]):
        if msg["ts"] == message_ts:
            DB["channels"][channel_id]["messages"][i] = message
            break

    return {"ok": True}