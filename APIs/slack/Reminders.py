"""
Reminders resource for Slack API simulation.

This module provides functionality for managing reminders in Slack.
It simulates the reminders-related endpoints of the Slack API.
"""

from common_utils.tool_spec_decorator import tool_spec
import uuid
from typing import Dict, Any, Optional

from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    MissingUserIDError, 
    UserNotFoundError,
    InvalidTimestampFormatError,
    MissingReminderIdError,
    ReminderNotFoundError,
    MissingCompleteTimestampError,
    InvalidCompleteTimestampError,
    ReminderAlreadyCompleteError
)


@tool_spec(
    spec={
        'name': 'delete_reminder',
        'description': 'Deletes a reminder.',
        'parameters': {
            'type': 'object',
            'properties': {
                'reminder_id': {
                    'type': 'string',
                    'description': 'The ID of the reminder. Must be a non-empty string.'
                }
            },
            'required': [
                'reminder_id'
            ]
        }
    }
)
def delete(reminder_id: str) -> Dict[str, Any]:
    """
    Deletes a reminder.

    Args:
        reminder_id (str): The ID of the reminder. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Always True for successful deletion

    Raises:
        TypeError: If reminder_id is not a string.
        MissingReminderIdError: If reminder_id is an empty string.
        ReminderNotFoundError: If reminder_id does not exist in the database.
    """
    # Input type validation
    if not isinstance(reminder_id, str):
        raise TypeError("reminder_id must be a string.")
    
    # Input value validation
    if not reminder_id:
        raise MissingReminderIdError("reminder_id cannot be empty.")

    # Check if reminder exists in database
    if "reminders" not in DB:
        DB["reminders"] = {}
    
    if reminder_id not in DB["reminders"]:
        raise ReminderNotFoundError(f"Reminder with ID '{reminder_id}' not found in database.")

    # Delete the reminder
    del DB["reminders"][reminder_id]
    return {"ok": True}


@tool_spec(
    spec={
        'name': 'get_reminder_info',
        'description': 'Gets information about a reminder.',
        'parameters': {
            'type': 'object',
            'properties': {
                'reminder_id': {
                    'type': 'string',
                    'description': 'The ID of the reminder. Must be a non-empty string.'
                }
            },
            'required': [
                'reminder_id'
            ]
        }
    }
)
def info(reminder_id: str) -> Dict[str, Any]:
    """
    Gets information about a reminder.

    Args:
        reminder_id (str): The ID of the reminder. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Always True for successful retrieval
            - reminder (Dict[str, Any]): The reminder data

    Raises:
        TypeError: If reminder_id is not a string.
        MissingReminderIdError: If reminder_id is an empty string.
        ReminderNotFoundError: If reminder_id does not exist in the database.
    """
    # Input type validation
    if not isinstance(reminder_id, str):
        raise TypeError("reminder_id must be a string.")
    
    # Input value validation
    if not reminder_id:
        raise MissingReminderIdError("reminder_id cannot be empty.")

    # Check if reminder exists in database
    if "reminders" not in DB:
        DB["reminders"] = {}
    
    reminder_data = DB["reminders"].get(reminder_id)

    if not reminder_data:
        raise ReminderNotFoundError(f"Reminder with ID '{reminder_id}' not found in database.")

    return {"ok": True, "reminder": reminder_data}


@tool_spec(
    spec={
        'name': 'complete_reminder',
        'description': 'Marks a reminder as complete.',
        'parameters': {
            'type': 'object',
            'properties': {
                'reminder_id': {
                    'type': 'string',
                    'description': 'The ID of the reminder. Must be a non-empty string.'
                },
                'complete_ts': {
                    'type': 'string',
                    'description': 'Timestamp for when it was completed. Must be a non-empty string representing a valid numeric timestamp.'
                }
            },
            'required': [
                'reminder_id',
                'complete_ts'
            ]
        }
    }
)
def complete(reminder_id: str, complete_ts: str) -> Dict[str, Any]:
    """
    Marks a reminder as complete.

    Args:
        reminder_id (str): The ID of the reminder. Must be a non-empty string.
        complete_ts (str): Timestamp for when it was completed. Must be a non-empty string representing a valid numeric timestamp.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Always True for successful completion

    Raises:
        TypeError: If reminder_id or complete_ts is not a string.
        MissingReminderIdError: If reminder_id is an empty string.
        MissingCompleteTimestampError: If complete_ts is an empty string.
        InvalidCompleteTimestampError: If complete_ts cannot be parsed as a valid numeric timestamp.
        ReminderNotFoundError: If reminder_id does not exist in the database.
        ReminderAlreadyCompleteError: If the reminder is already marked as complete.
    """
    # Input type validation
    if not isinstance(reminder_id, str):
        raise TypeError("reminder_id must be a string.")
    if not isinstance(complete_ts, str):
        raise TypeError("complete_ts must be a string.")
    
    # Input value validation
    if not reminder_id:
        raise MissingReminderIdError("reminder_id cannot be empty.")
    if not complete_ts:
        raise MissingCompleteTimestampError("complete_ts cannot be empty.")

    # Validate timestamp format
    try:
        int(float(complete_ts))
    except ValueError:
        raise InvalidCompleteTimestampError(f"complete_ts must be a string representing a valid numeric timestamp, got: '{complete_ts}'")

    # Check if reminder exists in database
    if "reminders" not in DB:
        DB["reminders"] = {}
    
    if reminder_id not in DB["reminders"]:
        raise ReminderNotFoundError(f"Reminder with ID '{reminder_id}' not found in database.")

    # Check if reminder is already complete
    if DB["reminders"][reminder_id]["complete_ts"] is not None:
        raise ReminderAlreadyCompleteError(f"Reminder with ID '{reminder_id}' is already marked as complete.")

    # Mark reminder as complete
    DB["reminders"][reminder_id]["complete_ts"] = complete_ts
    return {"ok": True}


@tool_spec(
    spec={
        'name': 'list_reminders',
        'description': 'Lists all reminders created by or for a given user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID. Must be a non-empty string.'
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def list_reminders(user_id: str) -> Dict[str, Any]:
    """
    Lists all reminders created by or for a given user.

    Args:
        user_id (str): User ID. Must be a non-empty string.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the request was successful.
            - reminders (List[Dict[str, Any]]): List of reminder objects.

    Raises:
        TypeError: If user_id is not a string.
        MissingUserIDError: If user_id is an empty string.
        UserNotFoundError: If user_id is not found in the database.
    """
    # Input Validation
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    if not user_id.strip():
        raise MissingUserIDError("user_id cannot be empty.")

    # Make sure we have the users dictionary
    if "users" not in DB:
        DB["users"] = {}
        
    # Make sure we have the reminders dictionary
    if "reminders" not in DB:
        DB["reminders"] = {}

    # Check if user exists
    if user_id not in DB["users"]:
        raise UserNotFoundError(f"User with ID '{user_id}' not found in database")

    # Find reminders for this user
    reminders = []
    for reminder_id, reminder_data in DB["reminders"].items():
        # This logic matches reminders:
        # 1. Where creator_id equals user_id
        # 2. OR where creator_id is missing, in which case we consider it to match
        if reminder_data.get("creator_id", user_id) == user_id:
            # Create a copy with the ID added
            reminder_copy = dict(reminder_data)
            reminder_copy["id"] = reminder_id
            reminders.append(reminder_copy)

    return {"ok": True, "reminders": reminders}


@tool_spec(
    spec={
        'name': 'add_reminder',
        'description': """ Creates a reminder with comprehensive input validation.
        
        Validation Logic:
            1. Type validation: user_id, text, and ts must be strings; channel_id must be string or None
            2. Empty string validation: user_id and text cannot be empty strings
            3. Timestamp validation: ts cannot be empty and must represent a valid numeric value
            4. User existence validation: user_id must exist in the database """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': 'User ID to remind. Must be a non-empty string.'
                },
                'text': {
                    'type': 'string',
                    'description': 'The content of the reminder. Must be a non-empty string.'
                },
                'ts': {
                    'type': 'string',
                    'description': """ When this reminder should happen (unix timestamp as a string).
                    Must be a non-empty string representing a number (e.g., "1678886400" or "1678886400.5"). """
                },
                'channel_id': {
                    'type': 'string',
                    'description': """ Channel ID to remind in. Defaults to None.
                    If provided as a string, it can be empty (unlike user_id and text). """
                }
            },
            'required': [
                'user_id',
                'text',
                'ts'
            ]
        }
    }
)
def add(user_id: str, text: str, ts: str, channel_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a reminder with comprehensive input validation.

    Validation Logic:
        1. Type validation: user_id, text, and ts must be strings; channel_id must be string or None
        2. Empty string validation: user_id and text cannot be empty strings
        3. Timestamp validation: ts cannot be empty and must represent a valid numeric value
        4. User existence validation: user_id must exist in the database

    Args:
        user_id (str): User ID to remind. Must be a non-empty string.
        text (str): The content of the reminder. Must be a non-empty string.
        ts (str): When this reminder should happen (unix timestamp as a string).
                  Must be a non-empty string representing a number (e.g., "1678886400" or "1678886400.5").
        channel_id (Optional[str]): Channel ID to remind in. Defaults to None.
                                    If provided as a string, it can be empty (unlike user_id and text).

    Returns:
        Dict[str, Any]: A dictionary containing:
            - ok (bool): Whether the request was successful (always True if no exception).
            - reminder (Dict[str, Any]): The created reminder data containing:
                - id (str): Unique reminder ID
                - creator_id (str): ID of user who created the reminder
                - user_id (str): ID of user to be reminded
                - text (str): Reminder content
                - time (str): When reminder should trigger (timestamp)
                - complete_ts (None): Completion timestamp (null until completed)
                - channel_id (Optional[str]): Channel ID if specified

    Raises:
        TypeError: If user_id, text, or ts is not a string, or if channel_id is not string/None.
        ValueError: If user_id or text is an empty string.
        InvalidTimestampFormatError: If ts is empty or cannot be parsed as a numeric timestamp.
        UserNotFoundError: If the user_id does not exist in the database.
    """
    # Input type validation
    if not isinstance(user_id, str):
        raise TypeError("user_id must be a string.")
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    if not isinstance(ts, str):
        raise TypeError("ts must be a string.")
    if channel_id is not None and not isinstance(channel_id, str):
        raise TypeError("channel_id must be a string or None.")
    
    # Input value validation
    if not user_id:
        raise ValueError("user_id cannot be empty.")
    if not text:
        raise ValueError("text cannot be empty.")
    if not ts:
        raise InvalidTimestampFormatError("ts cannot be empty.")
    
    # Validate timestamp format
    try:
        int(float(ts))  # Original logic allowed float strings then converted to int
    except ValueError:
        raise InvalidTimestampFormatError(f"ts must be a string representing a valid numeric timestamp (e.g., '1678886400' or '1678886400.5'), got: '{ts}'")

    # Check if user exists in database
    if "users" not in DB:
        DB["users"] = {}
    
    if user_id not in DB["users"]:
        raise UserNotFoundError(f"User with ID '{user_id}' not found in database.")

    # Generate a new reminder ID
    reminder_id = str(uuid.uuid4())
    
    # Create the reminder dictionary
    reminder = {
        "id": reminder_id,
        "creator_id": user_id,
        "user_id": user_id,  # Remind the specified user
        "text": text,
        "time": ts,          # Store timestamp as a string
        "complete_ts": None,  # Null initially, set when completed
        "channel_id": channel_id,
    }

    # Ensure the "reminders" collection exists in the DB
    if "reminders" not in DB:
        DB["reminders"] = {}
    
    # Store the new reminder
    DB["reminders"][reminder_id] = reminder

    # Return a success response with the created reminder
    return {"ok": True, "reminder": reminder}