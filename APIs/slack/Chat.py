"""
Chat resource for Slack API simulation.

This module provides functionality for sending and managing messages in Slack channels.
It simulates the chat-related endpoints of the Slack API.
"""
from common_utils.tool_spec_decorator import tool_spec
import time
import json
from typing import Dict, Any, List, Optional
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.models import (
    DeleteMessageInput, 
    DeleteScheduledMessageInput, 
    DeleteScheduledMessageResponse, 
    ScheduleMessageInputModel
)
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    InvalidTimestampFormatError,
    InvalidLimitValueError,
    InvalidCursorFormatError,
    CursorOutOfBoundsError,
    MessageNotFoundError,
    MissingRequiredArgumentsError,
    InvalidChannelError,
    InvalidUserError,
    InvalidTextError,
    UserNotInConversationError,
)
from .SimulationEngine.utils import _resolve_channel

@tool_spec(
    spec={
        'name': 'send_me_message',
        'description': 'Share a me message into a channel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID.'
                },
                'channel': {
                    'type': 'string',
                    'description': 'Existing channel ID or channel name (e.g., C1234567890 or #general) to send message to. Channel IDs are recommended. Must be a non-empty string.'
                },
                'text': {
                    'type': 'string',
                    'description': 'Text of the message to send. Must be a non-empty string.'
                }
            },
            'required': [
                'user_id',
                'channel',
                'text'
            ]
        }
    }
)
def meMessage(user_id: str, channel: str, text: str) -> Dict[str, Any]:
    """
    Share a me message into a channel.

    Args:
        user_id (str): User ID.
        channel (str): Existing channel ID or channel name (e.g., C1234567890 or #general) to send message to. Channel IDs are recommended. Must be a non-empty string.
        text (str): Text of the message to send. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - channel (str): The channel ID where the message was sent
            - text (str): The message text
            - ts (str): The timestamp of the message
            - subtype (str): The message subtype ("me_message")

    Raises:
        TypeError: If `user_id`, `channel`, or `text` is not a string.
        InvalidChannelError: If `channel` is an empty string.
        InvalidTextError: If `text` is an empty string.
        UserNotInConversationError: If `user_id` is not in `channel`.
        ChannelNotFoundError: If `channel` is not found.
    """
    # --- Input Validation ---
    if not isinstance(user_id, str):
        raise TypeError(f"argument 'user_id' must be a string, got {type(user_id).__name__.lower()}")
    if not isinstance(channel, str):
        raise TypeError(f"argument 'channel' must be a string, got {type(channel).__name__.lower()}")
    if not isinstance(text, str):
        raise TypeError(f"argument 'text' must be a string, got {type(text).__name__.lower()}")

    if not channel: # Check for empty string after type check
        raise InvalidChannelError("invalid_channel")
    if not text: # Check for empty string after type check
        raise InvalidTextError("invalid_text")
    # --- End of Input Validation ---

    # Handle channel with # prefix
    if channel.startswith("#"):
        # First try with # stripped (for channel names like #general)
        try:
            channel = _resolve_channel(channel[1:])
        except ChannelNotFoundError:
            # If not found, try with original string (for channel IDs like #C123)
            channel = _resolve_channel(channel)
    else:
        # Resolve channel name to channel ID if needed
        channel = _resolve_channel(channel)
    
    # Ensure channel exists (should exist since _resolve_channel found it)
    if "messages" not in DB["channels"][channel]:
        DB["channels"][channel]['messages'] = []
    
    if not DB["channels"][channel]["conversations"]:
        DB["channels"][channel]["conversations"] = {}

    if "members" not in DB["channels"][channel]["conversations"]:
        DB["channels"][channel]["conversations"]["members"] = []

    if user_id not in DB["channels"][channel]["conversations"]["members"]:
        raise UserNotInConversationError(f"User '{user_id}' is not in conversation '{channel}'.")

    # Generate a timestamp
    ts = str(time.time())

    # Store message following the schema
    message_data = {"user": user_id, "text": text, "ts": ts, "subtype": "me_message"}
    DB["channels"][channel]['messages'].append(message_data)

    return {"ok": True, "channel": channel, "text": text, "ts": ts, "subtype": "me_message"}


@tool_spec(
    spec={
        'name': 'delete_chat_message',
        'description': 'Deletes a message from a specified channel by its timestamp.',
        'parameters': {
            'type': 'object',
            'properties': {
                'channel': {
                    'type': 'string',
                    'description': 'The unique identifier of an existing channel containing the message (e.g., C1234567890).'
                },
                'ts': {
                    'type': 'string',
                    'description': 'A Unix timestamp with fractional seconds representing the message to be deleted.'
                }
            },
            'required': [
                'channel',
                'ts'
            ]
        }
    }
)
def delete(channel: str, ts: str) -> Dict[str, Any]:
    """
    Deletes a message from a specified channel by its timestamp.

    Args:
        channel (str): The unique identifier of an existing channel containing the message (e.g., C1234567890).
        ts (str): A Unix timestamp with fractional seconds representing the message to be deleted.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): True if deletion was successful.
            - channel (str) : The channel ID if deletion was successful.
            - ts (str): A Unix timestamp with fractional seconds representing

    Raises:
        ValueError: If any of the required parameters (channel, ts) are missing or invalid.
        ChannelNotFoundError: If the specified channel is not found.
        MessageNotFoundError: If no message exists with the given timestamp.
        PermissionError: If the user does not have permission to delete the message.
    """
    try:
        DeleteMessageInput(channel=channel, ts=ts)
    except ValueError as e:
        raise e

    current_user = DB.get("current_user")
    if not current_user:
        raise PermissionError("User not authenticated")

    if channel not in DB["channels"]:
        raise ChannelNotFoundError("channel_not_found")

    channel_info = DB["channels"][channel]
    messages = channel_info["messages"]
    is_private = channel_info.get("is_private", False)
    is_admin = current_user.get("is_admin", False)

    for i, msg in enumerate(messages):
        if msg["ts"] == ts:
            # Admins must also be members of private channels
            if is_admin:
                if is_private:
                    members = channel_info.get("conversations", {}).get("members", [])
                    if current_user["id"] not in members:
                        raise PermissionError("Admins must be part of private channels to delete messages")
            else:
                # Non-admins can only delete their own messages
                if msg["user"] != current_user["id"]:
                    raise PermissionError("You can only delete your own messages")

            # Authorized: proceed to delete
            del messages[i]
            return {
                "ok": True,
                "channel": channel,
                "ts": ts
            }

    raise MessageNotFoundError("message_not_found")


@tool_spec(
    spec={
        'name': 'delete_scheduled_message',
        'description': 'Deletes a scheduled message from a specified channel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'channel': {
                    'type': 'string',
                    'description': 'The unique identifier of an existing channel containing the scheduled message (e.g., C1234567890).'
                },
                'scheduled_message_id': {
                    'type': 'string',
                    'description': 'The unique ID of the scheduled message.'
                }
            },
            'required': [
                'channel',
                'scheduled_message_id'
            ]
        }
    }
)
def deleteScheduledMessage(
    channel: str, scheduled_message_id: str
) -> Dict[str, Any]:
    """
    Deletes a scheduled message from a specified channel.

    Args:
        channel (str): The unique identifier of an existing channel containing the scheduled message (e.g., C1234567890).
        scheduled_message_id (str): The unique ID of the scheduled message.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): True if deletion was successful.
            - channel (str): The channel ID.
            - scheduled_message_id (str): The ID of the deleted scheduled message.

    Raises:
        ValueError: If any input is invalid.
        PermissionError: If the user is not authenticated or lacks deletion rights.
        ChannelNotFoundError: If the channel doesn't exist.
        MessageNotFoundError: If no matching scheduled message is found.
    """
    try:
        validated_input = DeleteScheduledMessageInput(
            channel=channel, 
            scheduled_message_id=scheduled_message_id, 
        )
    except ValueError as e:
        raise e

    current_user = DB.get("current_user")
    if not current_user:
        raise PermissionError("User not authenticated")

    if validated_input.channel not in DB.get("channels", {}):
        raise ChannelNotFoundError("channel_not_found")

    channel_info = DB["channels"][validated_input.channel]
    is_private = channel_info.get("is_private", False)
    is_admin = current_user.get("is_admin", False)

    scheduled_messages = DB.get("scheduled_messages", [])

    for i, msg in enumerate(scheduled_messages):
        if (
            str(msg.get("message_id")) == validated_input.scheduled_message_id
            and msg.get("channel") == validated_input.channel
        ):
            # Admin permission check
            if is_admin:
                if is_private:
                    members = channel_info.get("conversations", {}).get("members", [])
                    if current_user["id"] not in members:
                        raise PermissionError(
                            "Admins must be part of private channels to delete scheduled messages"
                        )
            else:
                # Non-admins can only delete their own scheduled messages
                if msg.get("user") != current_user["id"]:
                    raise PermissionError("You can only delete your own scheduled messages")

            # Authorized: proceed to delete
            del scheduled_messages[i]
            return DeleteScheduledMessageResponse(
                ok=True,
                channel=validated_input.channel,
                scheduled_message_id=validated_input.scheduled_message_id
            ).model_dump()

    raise MessageNotFoundError("scheduled_message_not_found")


@tool_spec(
    spec={
        'name': 'post_ephemeral_message',
        'description': 'Sends an ephemeral message to a user in a channel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'channel': {
                    'type': 'string',
                    'description': "Existing channel ID or channel name (e.g., C1234567890 or #general) to send the message to. Channel IDs are recommended. Can't be empty."
                },
                'user': {
                    'type': 'string',
                    'description': "User to send the message to. Can't be empty."
                },
                'attachments': {
                    'type': 'string',
                    'description': 'JSON-based array of structured attachments. Must be a string if provided.'
                },
                'blocks': {
                    'type': 'array',
                    'description': 'A JSON-based array of structured blocks. Must be a list if provided.',
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                },
                'text': {
                    'type': 'string',
                    'description': 'Message text. Must be a string if provided.'
                },
                'as_user': {
                    'type': 'boolean',
                    'description': 'Pass true to post the message as the authed user. Must be a boolean if provided.'
                },
                'icon_emoji': {
                    'type': 'string',
                    'description': 'Emoji to use as the icon. Must be a string if provided.'
                },
                'icon_url': {
                    'type': 'string',
                    'description': 'URL to an image to use as the icon. Must be a string if provided.'
                },
                'link_names': {
                    'type': 'boolean',
                    'description': 'Find and link channel names and usernames. Must be a boolean if provided.'
                },
                'markdown_text': {
                    'type': 'string',
                    'description': 'Message text formatted in markdown. Must be a string if provided.'
                },
                'parse': {
                    'type': 'string',
                    'description': 'Change how messages are treated. Must be a string if provided.'
                },
                'thread_ts': {
                    'type': 'string',
                    'description': "Provide another message's ts value to post this message in a thread. Must be a string if provided."
                },
                'username': {
                    'type': 'string',
                    'description': "Set your bot's or your user name. Must be a string if provided."
                }
            },
            'required': [
                'channel',
                'user'
            ]
        }
    }
)
def postEphemeral(
        channel: str,
        user: str,
        attachments: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        text: Optional[str] = None,
        as_user: Optional[bool] = None,
        icon_emoji: Optional[str] = None,
        icon_url: Optional[str] = None,
        link_names: Optional[bool] = None,
        markdown_text: Optional[str] = None,
        parse: Optional[str] = None,
        thread_ts: Optional[str] = None,
        username: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends an ephemeral message to a user in a channel.

    Args:
        channel (str): Existing channel ID or channel name (e.g., C1234567890 or #general) to send the message to. Channel IDs are recommended. Can't be empty.
        user (str): User to send the message to. Can't be empty.
        attachments (Optional[str]): JSON-based array of structured attachments. Must be a string if provided.
        blocks (Optional[List[Dict[str, Any]]]): A JSON-based array of structured blocks. Must be a list if provided.
        text (Optional[str]): Message text. Must be a string if provided.
        as_user (Optional[bool]): Pass true to post the message as the authed user. Must be a boolean if provided.
        icon_emoji (Optional[str]): Emoji to use as the icon. Must be a string if provided.
        icon_url (Optional[str]): URL to an image to use as the icon. Must be a string if provided.
        link_names (Optional[bool]): Find and link channel names and usernames. Must be a boolean if provided.
        markdown_text (Optional[str]): Message text formatted in markdown. Must be a string if provided.
        parse (Optional[str]): Change how messages are treated. Must be a string if provided.
        thread_ts (Optional[str]): Provide another message's ts value to post this message in a thread. Must be a string if provided.
        username (Optional[str]): Set your bot's or your user name. Must be a string if provided.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful (always True)
            - message (dict): The sent ephemeral message object containing:
                - channel (str): The channel ID where the message was sent
                - user (str): The user ID who received the ephemeral message
                - text (Optional[str]): The message text if provided
                - attachments (Optional[str]): JSON attachments if provided
                - blocks (Optional[List[Dict[str, Any]]]): Structured blocks if provided
                - as_user (Optional[bool]): Whether posted as the authed user if provided
                - icon_emoji (Optional[str]): Icon emoji if provided
                - icon_url (Optional[str]): Icon URL if provided
                - link_names (Optional[bool]): Whether to link names if provided
                - markdown_text (Optional[str]): Markdown formatted text if provided
                - parse (Optional[str]): Message parsing mode if provided
                - thread_ts (Optional[str]): Thread timestamp if provided
                - username (Optional[str]): Bot/user name if provided

    Raises:
        MissingRequiredArgumentsError: If 'channel' or 'user' arguments are missing or empty.
        InvalidChannelError: If 'channel' is not a string.
        InvalidUserError: If 'user' is not a string.
        TypeError: If any optional parameter is provided with an incorrect type.
    """
    if not channel:
        raise MissingRequiredArgumentsError("The 'channel' argument is required and cannot be empty.")
    if not isinstance(channel, str):
        raise InvalidChannelError(f"The 'channel' argument must be a string, got {type(channel).__name__}.")

    if not user:
        raise MissingRequiredArgumentsError("The 'user' argument is required and cannot be empty.")
    if not isinstance(user, str):
        raise InvalidUserError(f"The 'user' argument must be a string, got {type(user).__name__}.")

    # Type validation for optional parameters
    if attachments is not None and not isinstance(attachments, str):
        raise TypeError(f"Optional argument 'attachments' must be a string if provided, got {type(attachments).__name__}.")
    if blocks is not None and not isinstance(blocks, list):
        raise TypeError(f"Optional argument 'blocks' must be a list if provided, got {type(blocks).__name__}.")
    if text is not None and not isinstance(text, str):
        raise TypeError(f"Optional argument 'text' must be a string if provided, got {type(text).__name__}.")
    if as_user is not None and not isinstance(as_user, bool):
        raise TypeError(f"Optional argument 'as_user' must be a boolean if provided, got {type(as_user).__name__}.")
    if icon_emoji is not None and not isinstance(icon_emoji, str):
        raise TypeError(f"Optional argument 'icon_emoji' must be a string if provided, got {type(icon_emoji).__name__}.")
    if icon_url is not None and not isinstance(icon_url, str):
        raise TypeError(f"Optional argument 'icon_url' must be a string if provided, got {type(icon_url).__name__}.")
    if link_names is not None and not isinstance(link_names, bool):
        raise TypeError(f"Optional argument 'link_names' must be a boolean if provided, got {type(link_names).__name__}.")
    if markdown_text is not None and not isinstance(markdown_text, str):
        raise TypeError(f"Optional argument 'markdown_text' must be a string if provided, got {type(markdown_text).__name__}.")
    if parse is not None and not isinstance(parse, str):
        raise TypeError(f"Optional argument 'parse' must be a string if provided, got {type(parse).__name__}.")
    if thread_ts is not None and not isinstance(thread_ts, str):
        raise TypeError(f"Optional argument 'thread_ts' must be a string if provided, got {type(thread_ts).__name__}.")
    if username is not None and not isinstance(username, str):
        raise TypeError(f"Optional argument 'username' must be a string if provided, got {type(username).__name__}.")

    # Handle channel with # prefix
    if channel.startswith("#"):
        # First try with # stripped (for channel names like #general)
        try:
            channel = _resolve_channel(channel[1:])
        except ChannelNotFoundError:
            # If not found, try with original string (for channel IDs like #C123)
            channel = _resolve_channel(channel)
    else:
        # Resolve channel name to channel ID if needed
        channel = _resolve_channel(channel)
    
    # Simulate sending the message (store in DB)
    message = {
        "channel": channel,
        "user": user,
        "text": text,
        "attachments": attachments,
        "blocks": blocks,
        "as_user": as_user,
        "icon_emoji": icon_emoji,
        "icon_url": icon_url,
        "link_names": link_names,
        "markdown_text": markdown_text,
        "parse": parse,
        "thread_ts": thread_ts,
        "username": username
    }
    DB["ephemeral_messages"].append(message)  #Store on the correct place

    return {"ok": True, "message": message}


@tool_spec(
    spec={
        'name': 'post_chat_message',
        'description': 'Sends a message to a channel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'channel': {
                    'type': 'string',
                    'description': 'Existing channel ID or channel name (e.g., C1234567890 or #general). Channel IDs are recommended as they remain constant. Must be a non-empty string.'
                },
                'ts': {
                    'type': 'string',
                    'description': 'Message timestamp. Must be a non-empty string if provided.'
                },
                'attachments': {
                    'type': 'string',
                    'description': 'JSON-based array of structured attachments. Must be a non-empty string if provided.'
                },
                'blocks': {
                    'type': 'string',
                    'description': """ JSON-encoded array of Block Kit blocks for rich message formatting. Each block must include a 
                    'type' field specifying its type. Supported types include section, divider, image, actions, context, input, file, header,
                    video, and rich_text. Maximum 50 blocks per message. Optional fields depend on the block type, such as text, accessory,
                    elements, image_url, alt_text, fields, and block_id. Must be valid JSON and a non-empty string if provided. """
                },
                'text': {
                    'type': 'string',
                    'description': 'Message text. Must be a non-empty string if provided.'
                },
                'as_user': {
                    'type': 'boolean',
                    'description': 'Post as user (legacy). Must be a boolean if provided.'
                },
                'icon_emoji': {
                    'type': 'string',
                    'description': 'Emoji to use as the icon. Must be a non-empty string if provided.'
                },
                'icon_url': {
                    'type': 'string',
                    'description': 'URL to an image to use as the icon. Must be a non-empty string if provided.'
                },
                'link_names': {
                    'type': 'boolean',
                    'description': 'Find and link user groups. Must be a boolean if provided.'
                },
                'markdown_text': {
                    'type': 'string',
                    'description': 'Message text formatted in markdown. Must be a non-empty string if provided.'
                },
                'metadata': {
                    'type': 'string',
                    'description': 'JSON object with event_type and event_payload fields. Must be a non-empty string if provided.'
                },
                'mrkdwn': {
                    'type': 'boolean',
                    'description': 'Disable Slack markup parsing. Must be a boolean if provided.'
                },
                'parse': {
                    'type': 'string',
                    'description': 'Change how messages are treated. Must be a non-empty string if provided.'
                },
                'reply_broadcast': {
                    'type': 'boolean',
                    'description': 'Make reply visible to everyone. Must be a boolean if provided.'
                },
                'thread_ts': {
                    'type': 'string',
                    'description': "Provide another message's ts value to make this message a reply. Must be a non-empty string if provided."
                },
                'unfurl_links': {
                    'type': 'boolean',
                    'description': 'Enable unfurling of primarily text-based content. Must be a boolean if provided.'
                },
                'unfurl_media': {
                    'type': 'boolean',
                    'description': 'Disable unfurling of media content. Must be a boolean if provided.'
                },
                'username': {
                    'type': 'string',
                    'description': "Set your bot's user name. Must be a non-empty string if provided."
                }
            },
            'required': [
                'channel'
            ]
        }
    }
)
def postMessage(
        channel: str,
        ts: Optional[str] = None,
        attachments: Optional[str] = None,
        blocks: Optional[str] = None,
        text: Optional[str] = None,
        as_user: Optional[bool] = None,
        icon_emoji: Optional[str] = None,
        icon_url: Optional[str] = None,
        link_names: Optional[bool] = None,
        markdown_text: Optional[str] = None,
        metadata: Optional[str] = None,
        mrkdwn: Optional[bool] = None,
        parse: Optional[str] = None,
        reply_broadcast: Optional[bool] = None,
        thread_ts: Optional[str] = None,
        unfurl_links: Optional[bool] = None,
        unfurl_media: Optional[bool] = None,
        username: Optional[str] = None) -> Dict[str, Any]:
    """
    Sends a message to a channel.

    Args:
        channel (str): Existing channel ID or channel name (e.g., C1234567890 or #general). Channel IDs are recommended as they remain constant. Must be a non-empty string.
        ts (Optional[str]): Message timestamp. Must be a non-empty string if provided.
        attachments (Optional[str]): JSON-based array of structured attachments. Must be a non-empty string if provided.
        blocks (Optional[str]): JSON-encoded array of Block Kit blocks for rich message formatting. Each block must include a 
            'type' field specifying its type. Supported types include section, divider, image, actions, context, input, file, header,
            video, and rich_text. Maximum 50 blocks per message. Optional fields depend on the block type, such as text, accessory,
            elements, image_url, alt_text, fields, and block_id. Must be valid JSON and a non-empty string if provided.
        text (Optional[str]): Message text. Must be a non-empty string if provided.
        as_user (Optional[bool]): Post as user (legacy). Must be a boolean if provided.
        icon_emoji (Optional[str]): Emoji to use as the icon. Must be a non-empty string if provided.
        icon_url (Optional[str]): URL to an image to use as the icon. Must be a non-empty string if provided.
        link_names (Optional[bool]): Find and link user groups. Must be a boolean if provided.
        markdown_text (Optional[str]): Message text formatted in markdown. Must be a non-empty string if provided.
        metadata (Optional[str]): JSON object with event_type and event_payload fields. Must be a non-empty string if provided.
        mrkdwn (Optional[bool]): Disable Slack markup parsing. Must be a boolean if provided.
        parse (Optional[str]): Change how messages are treated. Must be a non-empty string if provided.
        reply_broadcast (Optional[bool]): Make reply visible to everyone. Must be a boolean if provided.
        thread_ts (Optional[str]): Provide another message's ts value to make this message a reply. Must be a non-empty string if provided.
        unfurl_links (Optional[bool]): Enable unfurling of primarily text-based content. Must be a boolean if provided.
        unfurl_media (Optional[bool]): Disable unfurling of media content. Must be a boolean if provided.
        username (Optional[str]): Set your bot's user name. Must be a non-empty string if provided.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - message (Dict[str, Any]): Either:
                1. The sent message object containing:
                    - channel (str): Channel ID
                    - text (str): Message text
                    - attachments (Optional[str]): Message attachments
                    - blocks (Optional[str]): Message blocks
                    - ts (str): Message timestamp
                    - as_user (Optional[bool]): Whether posted as user
                    - icon_emoji (Optional[str]): Icon emoji
                    - icon_url (Optional[str]): Icon URL
                    - link_names (Optional[bool]): Link names setting
                    - markdown_text (Optional[str]): Markdown text
                    - metadata (Optional[str]): Message metadata
                    - mrkdwn (Optional[bool]): Markdown setting
                    - parse (Optional[str]): Parse setting
                    - reply_broadcast (Optional[bool]): Reply broadcast setting
                    - thread_ts (Optional[str]): Thread timestamp
                    - unfurl_links (Optional[bool]): Unfurl links setting
                    - unfurl_media (Optional[bool]): Unfurl media setting
                    - username (Optional[str]): Username
                OR
                2. The parent message object with replies list containing:
                    - All fields from the sent message object above
                    - replies (List[Dict[str, Any]]): List of reply messages, where each reply contains:
                        - channel (str): Channel ID
                        - text (str): Reply text
                        - attachments (Optional[str]): Reply attachments
                        - blocks (Optional[str]): Reply blocks
                        - ts (str): Reply timestamp
                        - as_user (Optional[bool]): Whether posted as user
                        - icon_emoji (Optional[str]): Icon emoji
                        - icon_url (Optional[str]): Icon URL
                        - link_names (Optional[bool]): Link names setting
                        - markdown_text (Optional[str]): Markdown text
                        - metadata (Optional[str]): Reply metadata
                        - mrkdwn (Optional[bool]): Markdown setting
                        - parse (Optional[str]): Parse setting
                        - reply_broadcast (Optional[bool]): Reply broadcast setting
                        - thread_ts (Optional[str]): Thread timestamp
                        - unfurl_links (Optional[bool]): Unfurl links setting
                        - unfurl_media (Optional[bool]): Unfurl media setting
                        - username (Optional[str]): Username

    Raises:
        TypeError: If any argument is of an incorrect type (e.g., 'channel' not a string,
                   'blocks' not a string when provided, 'as_user' not a boolean when provided).
        ValueError: If 'channel' is an empty string or if 'blocks' is not valid JSON.
        ChannelNotFoundError: If the specified channel does not exist in the database.
        MessageNotFoundError: If attempting to reply to a thread that doesn't exist or if the channel has no messages.
    """
    # --- Input Validation Layer ---

    # Validate 'channel'
    if not isinstance(channel, str):
        raise TypeError(f"Argument 'channel' must be a string, got {type(channel).__name__}.")
    if not channel:  # Equivalent to `if channel == ""`
        raise ValueError("Argument 'channel' cannot be an empty string.")

    # Handle channel with # prefix and resolve to channel ID
    if channel.startswith("#"):
        # First try with # stripped (for channel names like #general)
        try:
            channel = _resolve_channel(channel[1:])
        except ChannelNotFoundError:
            # If not found, try with original string (for channel IDs like #C123)
            channel = _resolve_channel(channel)
    else:
        # Resolve channel name to channel ID if needed
        channel = _resolve_channel(channel)
    
    # Validate simple optional string types
    str_optionals = {
        "ts": ts, "attachments": attachments, "text": text,
        "icon_emoji": icon_emoji, "icon_url": icon_url,
        "markdown_text": markdown_text, "metadata": metadata,
        "parse": parse, "thread_ts": thread_ts, "username": username
    }
    for arg_name, arg_val in str_optionals.items():
        if arg_val is not None and not isinstance(arg_val, str):
            raise TypeError(f"Argument '{arg_name}' must be a string or None, got {type(arg_val).__name__}.")

    # Validate simple optional boolean types
    bool_optionals = {
        "as_user": as_user, "link_names": link_names, "mrkdwn": mrkdwn,
        "reply_broadcast": reply_broadcast, "unfurl_links": unfurl_links,
        "unfurl_media": unfurl_media
    }
    for arg_name, arg_val in bool_optionals.items():
        if arg_val is not None and not isinstance(arg_val, bool):
            raise TypeError(f"Argument '{arg_name}' must be a boolean or None, got {type(arg_val).__name__}.")

    # Validate 'blocks' as optional string
    validated_blocks_for_logic: Optional[str] = None
    if blocks is not None:
        if not isinstance(blocks, str):
            raise TypeError(f"Argument 'blocks' must be a string or None, got {type(blocks).__name__}.")
        # Validate that blocks is valid JSON
        try:
            json.loads(blocks)
            validated_blocks_for_logic = blocks
        except json.JSONDecodeError:
            raise ValueError("Argument 'blocks' must be valid JSON string.")
    # --- End of Input Validation Layer ---

    # --- Original Core Functionality (modified to use validated_blocks_for_logic) ---
    message_payload = {
        "channel": channel,
        "text": text,
        "attachments": attachments,
        "blocks": validated_blocks_for_logic,  # Use validated string (can be None or populated)
        "ts": ts if ts else str(time.time()),  # time.time() for consistency if ts not provided
        "as_user": as_user,
        "icon_emoji": icon_emoji,
        "icon_url": icon_url,
        "link_names": link_names,
        "markdown_text": markdown_text,
        "metadata": metadata,
        "mrkdwn": mrkdwn,
        "parse": parse,
        "reply_broadcast": reply_broadcast,
        "thread_ts": thread_ts,
        "unfurl_links": unfurl_links,
        "unfurl_media": unfurl_media,
        "username": username
    }

    # Get channel data using the resolved channel ID
    current_channel_data = DB["channels"][channel]  # type: ignore

    if thread_ts is not None:
        if 'messages' not in current_channel_data:
            raise MessageNotFoundError(f"Message in tread '{thread_ts}' not found.")

        for msg_idx, msg_content in enumerate(current_channel_data['messages']):
            if msg_content["ts"] == thread_ts:
                if 'replies' not in msg_content:
                    current_channel_data['messages'][msg_idx]['replies'] = []
                current_channel_data['messages'][msg_idx]['replies'].append(message_payload)
                updated_msg = current_channel_data['messages'][msg_idx]
                return {"ok": True, "message": updated_msg}
        raise MessageNotFoundError(f"Message in tread '{thread_ts}' not found.")

    if 'messages' not in current_channel_data:
        current_channel_data['messages'] = []
    current_channel_data['messages'].append(message_payload)

    return {"ok": True, "message": message_payload}


post_chat_message = postMessage

@tool_spec(
    spec={
        'name': 'list_scheduled_messages',
        'description': 'Returns a list of scheduled messages.',
        'parameters': {
            'type': 'object',
            'properties': {
                'channel': {
                    'type': 'string',
                    'description': 'The channel of the scheduled messages. Defaults to None.'
                },
                'cursor': {
                    'type': 'string',
                    'description': 'For pagination purposes. Should be a string representing a non-negative integer. Defaults to None.'
                },
                'latest': {
                    'type': 'string',
                    'description': 'A Unix timestamp string (integer or float representation) of the latest value in the time range. Defaults to None.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of original entries to return. Must be a non-negative integer. Defaults to None.'
                },
                'oldest': {
                    'type': 'string',
                    'description': 'A Unix timestamp string (integer or float representation) of the oldest value in the time range. Defaults to None.'
                },
                'team_id': {
                    'type': 'string',
                    'description': 'encoded team id to list channels in, required if org token is used. Defaults to None.'
                }
            },
            'required': []
        }
    }
)
def list_scheduled_Messages(
        channel: Optional[str] = None,
        cursor: Optional[str] = None,
        latest: Optional[str] = None,
        limit: Optional[int] = None,
        oldest: Optional[str] = None,
        team_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns a list of scheduled messages.

    Args:
        channel (Optional[str]): The channel of the scheduled messages. Defaults to None.
        cursor (Optional[str]): For pagination purposes. Should be a string representing a non-negative integer. Defaults to None.
        latest (Optional[str]): A Unix timestamp string (integer or float representation) of the latest value in the time range. Defaults to None.
        limit (Optional[int]): Maximum number of original entries to return. Must be a non-negative integer. Defaults to None.
        oldest (Optional[str]): A Unix timestamp string (integer or float representation) of the oldest value in the time range. Defaults to None.
        team_id (Optional[str]): encoded team id to list channels in, required if org token is used. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful.
            - scheduled_messages (list): List of scheduled message objects.
            - response_metadata (dict): Pagination metadata containing:
                - next_cursor (Optional[str]): Cursor for next page of results.

    Raises:
        TypeError: If any argument is of an incorrect type (e.g., `channel` is not a string, `limit` is not an int).
        InvalidTimestampFormatError: If `latest` or `oldest` is provided but is not a valid numeric string.
        InvalidLimitValueError: If `limit` is provided and is negative.
        InvalidCursorFormatError: If `cursor` is provided but is not a string representing a non-negative integer.
        CursorOutOfBoundsError: If `cursor` is valid format but out of bounds for the current filtered data.
    """
    # --- Input Validation ---
    if channel is not None and not isinstance(channel, str):
        raise TypeError(f"channel must be a string or None, got {type(channel).__name__}")

    if team_id is not None and not isinstance(team_id, str):
        raise TypeError(f"team_id must be a string or None, got {type(team_id).__name__}")

    validated_oldest_int: Optional[int] = None
    if oldest is not None:
        if not isinstance(oldest, str):
            raise TypeError(f"oldest must be a string or None, got {type(oldest).__name__}")
        try:
            validated_oldest_int = int(float(oldest))
        except ValueError:
            raise InvalidTimestampFormatError(f"oldest timestamp '{oldest}' is not a valid numeric string.")

    validated_latest_int: Optional[int] = None
    if latest is not None:
        if not isinstance(latest, str):
            raise TypeError(f"latest must be a string or None, got {type(latest).__name__}")
        try:
            validated_latest_int = int(float(latest))
        except ValueError:
            raise InvalidTimestampFormatError(f"latest timestamp '{latest}' is not a valid numeric string.")

    if limit is not None:
        if type(limit) is not int:
            raise TypeError(f"limit must be an integer or None, got {type(limit).__name__}")
        if limit < 0:
            raise InvalidLimitValueError(f"limit must be a non-negative integer, got {limit}")

    parsed_cursor_index: Optional[int] = None
    if cursor is not None:
        if not isinstance(cursor, str):
            raise TypeError(f"cursor must be a string or None, got {type(cursor).__name__}")
        try:
            parsed_cursor_index = int(cursor)
            if parsed_cursor_index < 0:
                raise InvalidCursorFormatError(f"cursor must represent a non-negative integer, got '{cursor}'")
        except ValueError: # Catches if int(cursor) fails
            raise InvalidCursorFormatError(f"cursor '{cursor}' is not a valid integer string.")

    # --- Core Logic ---
    all_messages: List[Dict[str, Any]] = DB.get("scheduled_messages", [])
    filtered_messages: List[Dict[str, Any]] = list(all_messages) # Work on a copy

    if channel:
        # Assuming 'channel' in the message dict refers to the channel ID/name
        filtered_messages = [msg for msg in filtered_messages if msg.get("channel") == channel]


    if validated_oldest_int is not None:
        filtered_messages = [msg for msg in filtered_messages if msg.get("post_at", 0) >= validated_oldest_int]

    if validated_latest_int is not None:
        filtered_messages = [msg for msg in filtered_messages if msg.get("post_at", 0) <= validated_latest_int]

    # Handle cursor for slicing
    start_index = 0
    if parsed_cursor_index is not None:
        if parsed_cursor_index >= len(filtered_messages):
            raise CursorOutOfBoundsError("invalid_cursor_out_of_bounds")
        
        filtered_messages = filtered_messages[parsed_cursor_index:]
        start_index = parsed_cursor_index

    # Apply limit and determine next_cursor
    next_cursor_val_str: Optional[str] = None
    if limit is not None:
        if len(filtered_messages) > limit:
            next_cursor_val_str = str(start_index + limit)
            filtered_messages = filtered_messages[:limit]

    response = {
        "ok": True,
        "scheduled_messages": filtered_messages,
        "response_metadata": {"next_cursor": next_cursor_val_str},
    }
    return response


@tool_spec(
    spec={
        'name': 'schedule_chat_message',
        'description': 'Schedules a message to be sent to a channel.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID.'
                },
                'channel': {
                    'type': 'string',
                    'description': 'Existing channel ID or channel name (e.g., C1234567890 or #general) to send the message to. Channel IDs are recommended.'
                },
                'post_at': {
                    'type': 'integer',
                    'description': """ Unix timestamp for when to send the message. Must be positive.
                    Can be provided as int, float, or numeric string. """
                },
                'attachments': {
                    'type': 'string',
                    'description': 'JSON-formatted string representing an array of structured attachments.'
                },
                'blocks': {
                    'type': 'array',
                    'description': 'A list of structured block objects (dictionaries).',
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                },
                'text': {
                    'type': 'string',
                    'description': 'Message text.'
                },
                'as_user': {
                    'type': 'boolean',
                    'description': 'Post as the authed user. Defaults to False.'
                },
                'link_names': {
                    'type': 'boolean',
                    'description': 'Find and link user groups. Defaults to False.'
                },
                'markdown_text': {
                    'type': 'string',
                    'description': 'Message text formatted in markdown.'
                },
                'metadata': {
                    'type': 'string',
                    'description': """ JSON-formatted string representing an object with 'event_type' (str)
                    and 'event_payload' (dict) fields. """
                },
                'parse': {
                    'type': 'string',
                    'description': 'Change how messages are treated.'
                },
                'reply_broadcast': {
                    'type': 'boolean',
                    'description': 'Whether reply should be made visible to everyone. Defaults to False.'
                },
                'thread_ts': {
                    'type': 'string',
                    'description': "Provide another message's ts value to make this message a reply."
                },
                'unfurl_links': {
                    'type': 'boolean',
                    'description': 'Enable unfurling of primarily text-based content. Defaults to True.'
                },
                'unfurl_media': {
                    'type': 'boolean',
                    'description': 'Disable unfurling of media content. Defaults to False.'
                }
            },
            'required': [
                'user_id',
                'channel',
                'post_at'
            ]
        }
    }
)
def scheduleMessage(
        user_id :str,
        channel: str,
        post_at: int,
        attachments: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        text: Optional[str] = None,
        as_user: bool = False,
        link_names: bool = False,
        markdown_text: Optional[str] = None,
        metadata: Optional[str] = None,
        parse: Optional[str] = None,
        reply_broadcast: bool = False,
        thread_ts: Optional[str] = None,
        unfurl_links: bool = True,
        unfurl_media: bool = False) -> Dict[str, Any]:
    """
    Schedules a message to be sent to a channel.

    Args:
        user_id (str): User ID.
        channel (str): Existing channel ID or channel name (e.g., C1234567890 or #general) to send the message to. Channel IDs are recommended.
        post_at (int): Unix timestamp for when to send the message. Must be positive.
                       Can be provided as int, float, or numeric string.
        attachments (Optional[str]): JSON-formatted string representing an array of structured attachments.
        blocks (Optional[List[Dict[str, Any]]]): A list of structured block objects (dictionaries).
        text (Optional[str]): Message text.
        as_user (bool): Post as the authed user. Defaults to False.
        link_names (bool): Find and link user groups. Defaults to False.
        markdown_text (Optional[str]): Message text formatted in markdown.
        metadata (Optional[str]): JSON-formatted string representing an object with 'event_type' (str)
                                  and 'event_payload' (dict) fields.
        parse (Optional[str]): Change how messages are treated.
        reply_broadcast (bool): Whether reply should be made visible to everyone. Defaults to False.
        thread_ts (Optional[str]): Provide another message's ts value to make this message a reply.
        unfurl_links (bool): Enable unfurling of primarily text-based content. Defaults to True.
        unfurl_media (bool): Disable unfurling of media content. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - message_id (int): ID of the scheduled message
            - scheduled_message_id (str): String representation of the message ID

    Raises:
        ValidationError: If any input argument fails validation according to
                                  the defined Pydantic model (includes type errors,
                                  missing required fields, or specific validator failures like
                                  invalid JSON structures or non-positive post_at).
        TypeError: If arguments are passed in a way that Pydantic cannot process (e.g., wrong top-level type for an arg not covered by Pydantic model itself - less common with model covering all args).
    """
    try:
        input_args = {
            "user_id": user_id,
            "channel": channel,
            "post_at": post_at,
            "attachments": attachments,
            "blocks": blocks,
            "text": text,
            "as_user": as_user,
            "link_names": link_names,
            "markdown_text": markdown_text,
            "metadata": metadata,
            "parse": parse,
            "reply_broadcast": reply_broadcast,
            "thread_ts": thread_ts,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media,
        }
        validated_args = ScheduleMessageInputModel(**input_args)

    except PydanticValidationError as e:
        raise e

    # Handle channel with # prefix
    if validated_args.channel.startswith("#"):
        # First try with # stripped (for channel names like #general)
        try:
            channel = _resolve_channel(validated_args.channel[1:])
        except ChannelNotFoundError:
            # If not found, try with original string (for channel IDs like #C123)
            channel = _resolve_channel(validated_args.channel)
    else:
        # Resolve channel name to channel ID if needed
        channel = _resolve_channel(validated_args.channel)

    message_id = len(DB["scheduled_messages"]) + 1  # Generate sequential ID
    message = {
        "message_id": message_id,
        "user_id": validated_args.user_id,
        "channel": channel,
        "post_at": validated_args.post_at, # Use validated and coerced value
        "attachments": validated_args.attachments,
        "blocks": validated_args.blocks,
        "text": validated_args.text,
        "as_user": validated_args.as_user,
        "link_names": validated_args.link_names,
        "markdown_text": validated_args.markdown_text,
        "metadata": validated_args.metadata,
        "parse": validated_args.parse,
        "reply_broadcast": validated_args.reply_broadcast,
        "thread_ts": validated_args.thread_ts,
        "unfurl_links": validated_args.unfurl_links,
        "unfurl_media": validated_args.unfurl_media,
    }

    DB["scheduled_messages"].append(message) # Append the message

    return {"ok": True, "message_id": message_id, "scheduled_message_id":str(message_id)}


@tool_spec(
    spec={
        'name': 'update_chat_message',
        'description': 'Updates a message.',
        'parameters': {
            'type': 'object',
            'properties': {
                'channel': {
                    'type': 'string',
                    'description': 'Existing channel ID or channel name (e.g., C1234567890 or #general) containing the message. Channel IDs are recommended.'
                },
                'ts': {
                    'type': 'string',
                    'description': 'Timestamp of the message to be updated.'
                },
                'attachments': {
                    'type': 'string',
                    'description': 'A JSON-based array of structured attachments, presented as a URL-encoded string.'
                },
                'blocks': {
                    'type': 'string',
                    'description': 'A JSON-based array of structured blocks, presented as a URL-encoded string.'
                },
                'text': {
                    'type': 'string',
                    'description': 'The updated message text.'
                },
                'as_user': {
                    'type': 'boolean',
                    'description': 'Update the message as the authed user.'
                },
                'file_ids': {
                    'type': 'array',
                    'description': 'Array of new file ids that will be sent with this message.',
                    'items': {
                        'type': 'string'
                    }
                },
                'link_names': {
                    'type': 'boolean',
                    'description': 'Find and link channel names and usernames.'
                },
                'markdown_text': {
                    'type': 'string',
                    'description': 'Message text formatted in markdown.'
                },
                'parse': {
                    'type': 'string',
                    'description': 'Change how messages are treated.'
                },
                'reply_broadcast': {
                    'type': 'boolean',
                    'description': 'Broadcast an existing thread reply.'
                }
            },
            'required': [
                'channel',
                'ts'
            ]
        }
    }
)
def update(
    channel: str,
    ts: str,
    attachments: Optional[str] = None,
    blocks: Optional[str] = None,
    text: Optional[str] = None,
    as_user: Optional[bool] = None,
    file_ids: Optional[List[str]] = None,
    link_names: Optional[bool] = None,
    markdown_text: Optional[str] = None,
    parse: Optional[str] = None,
    reply_broadcast: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Updates a message.

    Args:
        channel (str): Existing channel ID or channel name (e.g., C1234567890 or #general) containing the message. Channel IDs are recommended.
        ts (str): Timestamp of the message to be updated.
        attachments (Optional[str]): A JSON-based array of structured attachments, presented as a URL-encoded string.
        blocks (Optional[str]): A JSON-based array of structured blocks, presented as a URL-encoded string.
        text (Optional[str]): The updated message text.
        as_user (Optional[bool]): Update the message as the authed user.
        file_ids (Optional[List[str]]): Array of new file ids that will be sent with this message.
        link_names (Optional[bool]): Find and link channel names and usernames.
        markdown_text (Optional[str]): Message text formatted in markdown.
        parse (Optional[str]): Change how messages are treated.
        reply_broadcast (Optional[bool]): Broadcast an existing thread reply.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the operation was successful
            - ts (str): Timestamp of the updated message
            - channel (str): Channel ID
            - message (dict): The updated message object containing:
                - channel (str): Channel ID
                - text (Optional[str]): Message text
                - attachments (Optional[str]): Message attachments
                - blocks (Optional[str]): Message blocks
                - as_user (Optional[bool]): Whether updated as user
                - file_ids (Optional[List[str]]): File IDs
                - link_names (Optional[bool]): Link names setting
                - markdown_text (Optional[str]): Markdown text
                - parse (Optional[str]): Parse setting
                - reply_broadcast (Optional[bool]): Reply broadcast setting
    
    Raises:
        TypeError: If any parameter has an incorrect type.
        ValueError: If at least one of attachments, blocks, or text is not provided.
        ChannelNotFoundError: If the channel is not found or empty.
        InvalidTimestampFormatError: If the timestamp is empty or invalid.
        MessageNotFoundError: If the message with the given timestamp is not found in the channel.
    """
    # Type checking for required parameters
    if not isinstance(channel, str):
        raise TypeError(f"channel must be a string, got {type(channel).__name__}")
    if not isinstance(ts, str):
        raise TypeError(f"ts must be a string, got {type(ts).__name__}")
    
    # Type checking for optional parameters
    if attachments is not None and not isinstance(attachments, str):
        raise TypeError(f"attachments must be a string, got {type(attachments).__name__}")
    if blocks is not None and not isinstance(blocks, str):
        raise TypeError(f"blocks must be a string, got {type(blocks).__name__}")
    if text is not None and not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}")
    if as_user is not None and not isinstance(as_user, bool):
        raise TypeError(f"as_user must be a boolean, got {type(as_user).__name__}")
    if file_ids is not None and not isinstance(file_ids, list):
        raise TypeError(f"file_ids must be a list, got {type(file_ids).__name__}")
    if file_ids is not None:
        for i, file_id in enumerate(file_ids):
            if not isinstance(file_id, str):
                raise TypeError(f"file_ids[{i}] must be a string, got {type(file_id).__name__}")
    if link_names is not None and not isinstance(link_names, bool):
        raise TypeError(f"link_names must be a boolean, got {type(link_names).__name__}")
    if markdown_text is not None and not isinstance(markdown_text, str):
        raise TypeError(f"markdown_text must be a string, got {type(markdown_text).__name__}")
    if parse is not None and not isinstance(parse, str):
        raise TypeError(f"parse must be a string, got {type(parse).__name__}")
    if reply_broadcast is not None and not isinstance(reply_broadcast, bool):
        raise TypeError(f"reply_broadcast must be a boolean, got {type(reply_broadcast).__name__}")
    
    # Input validation
    if not channel:
        raise ChannelNotFoundError("Channel parameter is required")
    if not ts:
        raise InvalidTimestampFormatError("Timestamp parameter is required")

    # Validate that at least one of attachments, blocks, or text is provided
    if attachments is None and blocks is None and text is None:
        raise ValueError("At least one of 'attachments', 'blocks', or 'text' must be provided")

    # Handle channel with # prefix
    if channel.startswith("#"):
        # First try with # stripped (for channel names like #general)
        try:
            channel = _resolve_channel(channel[1:])
        except ChannelNotFoundError:
            # If not found, try with original string (for channel IDs like #C123)
            channel = _resolve_channel(channel)
    else:
        # Resolve channel name to channel ID if needed
        channel = _resolve_channel(channel)

    # Find the message in the correct channel
    message = None
    if "messages" not in DB["channels"][channel]:
        DB["channels"][channel]['messages'] = []
    for i, msg in enumerate(DB["channels"][channel]['messages']):
        if msg["ts"] == ts:
            message = msg
            message_index = i # Store the index for updating.
            break  # Exit loop once found

    if message is None:
        raise MessageNotFoundError(f"Message with timestamp {ts} not found in channel {channel}")

    # Update fields if provided.
    if attachments is not None:
        message["attachments"] = attachments
    if blocks is not None:
        message["blocks"] = blocks
    if text is not None:
        message["text"] = text
    if as_user is not None:
        message["as_user"] = as_user
    if file_ids is not None:
        message["file_ids"] = file_ids
    if link_names is not None:
        message["link_names"] = link_names
    if markdown_text is not None:
        message["markdown_text"] = markdown_text
    if parse is not None:
        message["parse"] = parse
    if reply_broadcast is not None:
        message["reply_broadcast"] = reply_broadcast

    # Update the message directly in the list using the index.
    DB["channels"][channel]['messages'][message_index] = message

    return {
        "ok": True, 
        "ts": ts, 
        "channel": channel, 
        "message": message
    }
