from common_utils.tool_spec_decorator import tool_spec
# APIs/google_calendar/EventsResource/__init__.py
import uuid
import copy
from datetime import datetime, timezone

from pydantic import ValidationError

from .CalendarsResource import get_calendar
from .SimulationEngine.models import EventResourceInputModel
from .SimulationEngine.models import EventPatchResourceModel
from .SimulationEngine.db import DB
from .SimulationEngine.utils import (
    parse_iso_datetime,
    notify_attendees, event_matches_query,
    validate_start_end_times,
    get_primary_calendar_entry
)
from typing import Dict, Any, Optional, List
from .SimulationEngine.custom_errors import InvalidInputError, ResourceNotFoundError, ResourceAlreadyExistsError, PermissionDeniedError
from .SimulationEngine.recurrence_expander import expand_recurring_events
from rfc3339_validator import validate_rfc3339
from common_utils.datetime_utils import is_datetime_of_format, local_to_UTC, is_timezone_valid, UTC_to_local, timezone_to_offset

@tool_spec(
    spec={
        'name': 'delete_event',
        'description': 'Deletes an event from the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar containing the event to delete. If "primary" is provided, the primary calendar will be used.'
                },
                'eventId': {
                    'type': 'string',
                    'description': 'The identifier of the event to delete.'
                },
                'sendUpdates': {
                    'type': 'string',
                    'description': """ Whether to send updates about the deletion.
                    Possible values: "all", "externalOnly", "none". Defaults to None. """
                }
            },
            'required': [
                'calendarId',
                'eventId'
            ]
        }
    }
)
def delete_event(
    calendarId: str,
    eventId: str,
    sendUpdates: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deletes an event from the specified calendar.

    Args:
        calendarId (str): The identifier of the calendar containing the event to delete. If "primary" is provided, the primary calendar will be used.
        eventId (str): The identifier of the event to delete.
        sendUpdates (Optional[str]): Whether to send updates about the deletion.
            Possible values: "all", "externalOnly", "none". Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether the event was successfully deleted.
            - message (str): A message describing the result of the operation.

    Raises:
        TypeError: In the following cases:
            - If `calendarId` is not a string.
            - If `eventId` is not a string.
            - If `sendUpdates` is not a string or None.
        InvalidInputError: In the following cases:
            - If `calendarId` is empty or whitespace.
            - If `eventId` is empty or whitespace.
            - If `sendUpdates` has an invalid value (not "all", "externalOnly", or "none").
        ValueError: If the event is not found in the calendar.
        NotificationError: If sending notifications to attendees fails.
    """
    # --- Input Validation ---
    # Validate calendarId
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string.")
    if not calendarId.strip():
        raise InvalidInputError("calendarId cannot be empty or whitespace.")

    # Validate eventId
    if not isinstance(eventId, str):
        raise TypeError("eventId must be a string.")
    if not eventId.strip():
        raise InvalidInputError("eventId cannot be empty or whitespace.")

    # Validate sendUpdates
    if sendUpdates is not None:
        if not isinstance(sendUpdates, str):
            raise TypeError("sendUpdates must be a string or None.")
        if sendUpdates not in ["all", "externalOnly", "none"]:
            raise InvalidInputError("sendUpdates must be one of: all, externalOnly, none")

    # Map "primary" to the user's primary calendar ID
    if calendarId == "primary":
        # Find the actual primary calendar from the DB
        primary_calendar = None
        if "calendar_list" in DB and DB["calendar_list"]:
            for cal_id, cal_data in DB["calendar_list"].items():
                if cal_data.get("primary") is True:
                    primary_calendar = cal_id
                    break

        if primary_calendar:
            calendarId = primary_calendar

    key = f'{calendarId}:{eventId}'
    if key not in DB["events"]:
        raise ValueError(f"Event '{eventId}' not found in calendar '{calendarId}'.")
    # snapshot for notification
    event_before_delete = DB["events"][key].copy()
    del DB["events"][key]

    notify_attendees(calendarId, event_before_delete, sendUpdates, subject_prefix="Cancelled")
    
    return {
        "success": True,
        "message": f"Event '{eventId}' deleted from calendar '{calendarId}'.",
    }


@tool_spec(
    spec={
        'name': 'get_event',
        'description': 'Retrieves an event from the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'alwaysIncludeEmail': {
                    'type': 'boolean',
                    'description': """ Deprecated. This parameter is ignored as email addresses
                    are always included in the response. Optional. Defaults to False. """
                },
                'calendarId': {
                    'type': 'string',
                    'description': """ The identifier of the calendar. Optional.
                    To retrieve calendar IDs call the calendarList.list method.
                    If you want to access the primary calendar of the currently logged in user,
                    use the "primary" keyword. Defaults to "primary". """
                },
                'eventId': {
                    'type': 'string',
                    'description': 'The identifier of the event to retrieve. Required.'
                },
                'maxAttendees': {
                    'type': 'integer',
                    'description': """ The maximum number of attendees to return (must be non-negative).
                    Defaults to None (return all attendees). """
                },
                'timeZone': {
                    'type': 'string',
                    'description': """ The time zone to use for the response (e.g. "America/New_York").
                    Defaults to the calendar's time zone. """
                }
            },
            'required': []
        }
    }
)
def get_event(
    alwaysIncludeEmail: Optional[bool] = False,
    calendarId: Optional[str] = "primary",
    eventId: str = "",
    maxAttendees: Optional[int] = None,
    timeZone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves an event from the specified calendar.

    Args:
        alwaysIncludeEmail (Optional[bool]): Deprecated. This parameter is ignored as email addresses
            are always included in the response. Optional. Defaults to False.
        calendarId (Optional[str]): The identifier of the calendar. Optional.
            To retrieve calendar IDs call the calendarList.list method.
            If you want to access the primary calendar of the currently logged in user,
            use the "primary" keyword. Defaults to "primary".
        eventId (str): The identifier of the event to retrieve. Required.
        maxAttendees (Optional[int]): The maximum number of attendees to return (must be non-negative).
            Defaults to None (return all attendees).
        timeZone (Optional[str]): The time zone to use for the response, in the format 'Continent/City' (e.g., 'America/New_York').
            An empty string is not allowed. Defaults to the calendar's time zone
    Returns:
        Dict[str, Any]: The event details containing:
            - id (str): The identifier of the event.
            - summary (str): The summary/title of the event.
            - description (str, optional): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - date (str): The date of the start time in format YYYY-MM-DD. Either date or dateTime are present.
                - dateTime (str): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are present.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - date (str): The date of the end time in format YYYY-MM-DD. Either date or dateTime are present.
                - dateTime (str): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are present.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
            - organizer (Dict[str, Any]): The organizer of the event.
                - email (str): The email address of the organizer.
            - creator (Dict[str, Any]): The creator of the event.
                - email (str): The email address of the creator.
            - attendees (List[Dict[str, Any]]): The list of attendees.
                - email (str): The email address of the attendee.

    Raises:
        TypeError: In the following cases:
            - If `eventId` is not a string.
            - If `calendarId` is not a string or None.
            - If `alwaysIncludeEmail` is not a boolean.
            - If `maxAttendees` is not an integer or None.
            - If `timeZone` is not a string or None.
        InvalidInputError: In the following cases:
            - If `eventId` is empty or whitespace.
            - If `calendarId` is empty or whitespace (when provided).
            - If `maxAttendees` is negative.
            - If `timeZone` is empty/whitespace or has invalid format.
        ResourceNotFoundError: If the calendar or event is not found:
            - Calendar with specified ID does not exist.
            - Event with specified ID does not exist in the calendar.
        PermissionDeniedError: If the user does not have permission to access the event.
    """
    # --- Input Validation ---
    # Validate alwaysIncludeEmail (optional parameter)
    if not isinstance(alwaysIncludeEmail, bool):
        raise TypeError("alwaysIncludeEmail must be a boolean.")

    # Validate calendarId (optional parameter)
    if calendarId is not None:
        if not isinstance(calendarId, str):
            raise TypeError("calendarId must be a string or None.")
        if not calendarId.strip():
            raise InvalidInputError("calendarId cannot be empty or whitespace.")

    # Validate eventId (required parameter first)
    if not isinstance(eventId, str):
        raise TypeError("eventId must be a string.")
    if not eventId.strip():
        raise InvalidInputError("eventId cannot be empty or whitespace.")

    # Validate maxAttendees
    if maxAttendees is not None:
        if not isinstance(maxAttendees, int):
            raise TypeError("maxAttendees must be an integer or None.")
        if maxAttendees < 0:
            raise InvalidInputError("maxAttendees cannot be negative.")

    # Validate timeZone
    if timeZone is not None:
        if not isinstance(timeZone, str):
            raise TypeError("timeZone must be a string or None.")
        if not timeZone.strip():
            raise InvalidInputError("timeZone cannot be empty or whitespace.")
        if not is_timezone_valid(timeZone):
            raise InvalidInputError("timeZone must be in IANA format (e.g., 'America/New_York').")

    # --- End Input Validation ---

    # --- Core Logic ---
    effective_calendarId = calendarId
    if effective_calendarId is None or effective_calendarId == "":
        effective_calendarId = "primary"

    # Map "primary" to the user's primary calendar ID
    if effective_calendarId == "primary":
        # Find the actual primary calendar from the DB
        primary_calendar = None
        if "calendar_list" in DB and DB["calendar_list"]:
            for cal_id, cal_data in DB["calendar_list"].items():
                if cal_data.get("primary") is True:
                    primary_calendar = cal_id
                    break
        
        if primary_calendar:
            effective_calendarId = primary_calendar

    # Assume DB exists and has the expected structure
    if "calendar_list" not in DB or effective_calendarId not in DB["calendar_list"]:
        raise ResourceNotFoundError(f"Calendar '{effective_calendarId}' not found.")

    key = f'{effective_calendarId}:{eventId}'
    if "events" not in DB or key not in DB["events"]:
        raise ResourceNotFoundError(f"Event '{eventId}' not found in calendar '{effective_calendarId}'.")

    # Get a copy to avoid modifying the original DB entry directly
    event = DB["events"][key].copy()
    calendar = DB["calendar_list"][effective_calendarId]

    # --- Authorization Check ---
    # Simulate current user (replace with real user context in production)
    user_email = None
    if "me" in DB.get("users", {}):
        user_email = DB["users"]["me"]["about"]["user"]["emailAddress"]
    else:
        user_email = "me@example.com"  # fallback for simulation

    allowed = False
    
    if "users" not in DB or "me" not in DB["users"]:
        allowed = True
    elif "organizer" in event and event["organizer"].get("email") == user_email:
        allowed = True
    elif "creator" in event and event["creator"].get("email") == user_email:
        allowed = True
    elif "attendees" in event and event["attendees"] and any(a.get("email") == user_email for a in event["attendees"]):
        allowed = True
    elif calendar.get("owner") == user_email:
        allowed = True
    # Optionally, allow access if the calendar is public (if you support that)
    if not allowed:
        raise PermissionDeniedError("You do not have permission to access this event.")

    # Handle timeZone parameter
    tz_to_use = timeZone or event.get("start", {}).get("timeZone") or calendar.get("timeZone")
    event_to_convert = event.copy()
    
    if tz_to_use:
        # Convert start
        if "start" in event_to_convert:
            event_to_convert["start"] = UTC_to_local(event_to_convert["start"])
            event_to_convert["start"]["timeZone"] = tz_to_use
        # Convert end
        if "end" in event_to_convert:
            event_to_convert["end"] = UTC_to_local(event_to_convert["end"])
            event_to_convert["end"]["timeZone"] = tz_to_use

    # Handle maxAttendees parameter
    if "attendees" in event_to_convert and maxAttendees is not None:
        if isinstance(event_to_convert.get("attendees"), list):
            event_to_convert["attendees"] = event_to_convert["attendees"][:maxAttendees]

    return event_to_convert


@tool_spec(
    spec={
        'name': 'import_event',
        'description': 'Imports an event into the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar.'
                },
                'conferenceDataVersion': {
                    'type': 'integer',
                    'description': """ The version of the conference data.
                    Defaults to 0. """
                },
                'supportsAttachments': {
                    'type': 'boolean',
                    'description': """ Whether the event supports attachments.
                    Defaults to False. """
                },
                'resource': {
                    'type': 'object',
                    'description': 'The event to import:',
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': """ The identifier of the event. If not provided,
                                 a new UUID will be generated. """
                        },
                        'summary': {
                            'type': 'string',
                            'description': 'The summary/title of the event.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the event.'
                        },
                        'start': {
                            'type': 'object',
                            'description': 'The start time of the event.',
                            'properties': {
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the start time in either YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS format. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored.'
                                }
                            },
                            'required': [
                                'dateTime'
                            ]
                        },
                        'end': {
                            'type': 'object',
                            'description': 'The end time of the event.',
                            'properties': {
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the end time in either YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS format. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored.'
                                }
                            },
                            'required': [
                                'dateTime'
                            ]
                        }
                    },
                    'required': [
                        'start',
                        'end'
                    ]
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def import_event(
    calendarId: str,
    conferenceDataVersion: Optional[int] = 0,
    supportsAttachments: Optional[bool] = False,
    resource: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Imports an event into the specified calendar.

    Args:
        calendarId (str): The identifier of the calendar.
        conferenceDataVersion (Optional[int]): The version of the conference data.
            Defaults to 0.
        supportsAttachments (Optional[bool]): Whether the event supports attachments.
            Defaults to False.
        resource (Optional[Dict[str, Any]]): The event to import:
            - id (Optional[str]): The identifier of the event. If not provided,
                a new UUID will be generated.
            - summary (Optional[str]): The summary/title of the event.
            - description (Optional[str]): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - dateTime (str): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - dateTime (str): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.

    Returns:
        Dict[str, Any]: The imported event.
            - id (str): The identifier of the event.
            - summary (str): The summary of the event.
            - description (str): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - dateTime (str): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - dateTime (str): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.

    Raises:
        ValueError: If the resource is not provided.
        ResourceNotFoundError: If 'calendarId' does not exist in the database or if "primary" is specified but no primary calendar is found.
        ResourceAlreadyExistsError: If an event with the same ID already exists in the calendar.
    """
    if resource is None:
        raise ValueError("Resource is required to import an event.")
    
    # Validation is being performed inside the get_calendar function
    calendar = get_calendar(calendarId)
    validated_calendar_id = calendar["id"]
    
    ev_id = resource.get("id") or str(uuid.uuid4())
    
    # Check for duplicate event ID
    event_key = f'{validated_calendar_id}:{ev_id}'
    if event_key in DB["events"]:
        raise ResourceAlreadyExistsError(f"Event with ID '{ev_id}' already exists in calendar '{validated_calendar_id}'.")
    
    resource["id"] = ev_id

    # Convert the start and end times to UTC timezone
    resource_to_DB = resource.copy()
    if "start" in resource_to_DB:
        resource_to_DB["start"] = local_to_UTC(resource_to_DB["start"])
    if "end" in resource_to_DB:
        resource_to_DB["end"] = local_to_UTC(resource_to_DB["end"])
    DB["events"][f'{validated_calendar_id}:{ev_id}'] = resource_to_DB
    return resource

@tool_spec(
    spec={
        'name': 'create_event',
        'description': 'Creates a new event in the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': "The identifier of the calendar. Defaults to the user's primary calendar."
                },
                'resource': {
                    'type': 'object',
                    'description': 'The event to create:',
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': """ The identifier of the event. If not provided,
                                 a new UUID will be generated. """
                        },
                        'summary': {
                            'type': 'string',
                            'description': 'The summary/title of the event.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the event.'
                        },
                        'start': {
                            'type': 'object',
                            'description': 'The start time of the event.',
                            'properties': {
                                'date': {
                                    'type': 'string',
                                    'description': 'The date of the start time in format YYYY-MM-DD. Either date or dateTime field must be provided and cannot be provided at the same time. Default to None.'
                                },
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. The date and dateTime field cannot be provided at the same time. Default to None.'
                                },
                                'timeZone': {
                                    'type': 'string',
                                    'description': 'The time zone of the start time in IANA format (e.g., "America/New_York"). The timeZone is required if the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS). Defaults to None.'
                                }
                            },
                            'required': [
                            ]
                        },
                        'end': {
                            'type': 'object',
                            'description': 'The end time of the event.',
                            'properties': {
                                'date': {
                                    'type': 'string',
                                    'description': 'The date of the end time in format YYYY-MM-DD. Either date or dateTime field must be provided and cannot be provided at the same time. Default to None.'
                                },
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. The date and dateTime field cannot be provided at the same time. Default to None.'
                                },
                                'timeZone': {
                                    'type': 'string',
                                    'description': 'The time zone of the end time in IANA format (e.g., "America/New_York"). The timeZone is required if the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS). Defaults to None.'
                                }
                            },
                            'required': [
                            ]
                        },
                        'recurrence': {
                            'type': 'array',
                            'description': """ The recurrence rules of the event in RRULE format and exception dates in EXDATE format.
                                 Examples:
                                - Daily for 5 occurrences: ["RRULE:FREQ=DAILY;COUNT=5"]
                                - Weekly on Monday and Wednesday: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
                                - Monthly on the 15th: ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
                                - Yearly on January 1st: ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"]
                                - Every 2 weeks: ["RRULE:FREQ=WEEKLY;INTERVAL=2"]
                                - Until a specific date: ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
                                - With exception dates: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225T120000Z", "EXDATE:20250101T120000Z"]
                                - Multiple exception dates: ["RRULE:FREQ=DAILY;COUNT=10", "EXDATE:20241225T120000Z", "EXDATE:20241226T120000Z"]
                                Supported RRULE parameters:
                                - FREQ: SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY (required)
                                - INTERVAL: Positive integer (default: 1)
                                - COUNT: Positive integer (number of occurrences)
                                - UNTIL: YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS format
                                - BYDAY: SU,MO,TU,WE,TH,FR,SA (with optional ordinal: 1SU, -1MO)
                                - BYMONTH: 1-12
                                - BYMONTHDAY: 1-31
                                - BYYEARDAY: 1-366
                                - BYWEEKNO: 1-53
                                - BYHOUR: 0-23
                                - BYMINUTE: 0-59
                                - BYSECOND: 0-59
                                - BYSETPOS: 1-366 or -366 to -1
                                - WKST: SU,MO,TU,WE,TH,FR,SA (week start)
                                Supported EXDATE format:
                                - EXDATE:YYYYMMDDTHHMMSSZ (UTC timezone)
                                - EXDATE:YYYYMMDDTHHMMSS (floating/local time)
                                - EXDATE:YYYYMMDD (date only for all-day events)
                                - Multiple dates: Use separate EXDATE entries (not comma-separated)
                                Note: TZID parameter not supported in this implementation """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'attendees': {
                            'type': 'array',
                            'description': 'List of event attendees. Each attendee can have:',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'email': {
                                        'type': 'string',
                                        'description': "The attendee's email address"
                                    },
                                    'displayName': {
                                        'type': 'string',
                                        'description': "The attendee's display name"
                                    },
                                    'organizer': {
                                        'type': 'boolean',
                                        'description': 'Whether the attendee is the organizer'
                                    },
                                    'self': {
                                        'type': 'boolean',
                                        'description': 'Whether the attendee is the user'
                                    },
                                    'resource': {
                                        'type': 'boolean',
                                        'description': 'Whether the attendee is a resource'
                                    },
                                    'optional': {
                                        'type': 'boolean',
                                        'description': "Whether the attendee's presence is optional"
                                    },
                                    'responseStatus': {
                                        'type': 'string',
                                        'description': "The attendee's response status"
                                    },
                                    'comment': {
                                        'type': 'string',
                                        'description': "The attendee's comment"
                                    },
                                    'additionalGuests': {
                                        'type': 'integer',
                                        'description': 'Number of additional guests'
                                    }
                                },
                                'required': []
                            }
                        },
                        'reminders': {
                            'type': 'object',
                            'description': 'The reminders of the event.',
                            'properties': {
                                'useDefault': {
                                    'type': 'boolean',
                                    'description': 'Whether to use the default reminders.'
                                },
                                'overrides': {
                                    'type': 'array',
                                    'description': 'The list of overrides.',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'method': {
                                                'type': 'string',
                                                'description': 'The method of the reminder.'
                                            },
                                            'minutes': {
                                                'type': 'integer',
                                                'description': 'The minutes of the reminder.'
                                            }
                                        },
                                        'required': []
                                    }
                                }
                            },
                            'required': []
                        },
                        'location': {
                            'type': 'string',
                            'description': 'The location of the event.'
                        },
                        'attachments': {
                            'type': 'array',
                            'description': 'The attachments list contains the dicts and each dict has the following key:',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'fileUrl': {
                                        'type': 'string',
                                        'description': 'The URL of the attachment'
                                    }
                                },
                                'required': [
                                    'fileUrl'
                                ]
                            }
                        }
                    },
                    'required': [
                        'start',
                        'end'
                    ]
                },
                'sendUpdates': {
                    'type': 'string',
                    'description': """ Whether to send updates about the creation.
                    Possible values: "all", "externalOnly", "none". Defaults to None. """
                }
            },
            'required': []
        }
    }
)
def create_event(calendarId: Optional[str] = "primary", resource: Optional[Dict[str, Any]] = None, sendUpdates: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a new event in the specified calendar.

    Args:
        calendarId (Optional[str]): The identifier of the calendar. Defaults to the user's primary calendar.
        resource (Optional[Dict[str, Any]]): The event to create:
            - id (Optional[str]): The identifier of the event. If not provided,
                a new UUID will be generated.
            - summary (Optional[str]): The summary/title of the event.
            - description (Optional[str]): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - date (Optional[str]): The date of the start time in format YYYY-MM-DD. Either date or dateTime field must be provided and cannot be provided at the same time. Default to None.
                - dateTime (Optional[str]): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. The date and dateTime field cannot be provided at the same time. Default to None.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). The timeZone is required if the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - date (Optional[str]): The date of the end time in format YYYY-MM-DD. Either date or dateTime field must be provided and cannot be provided at the same time. Default to None.
                - dateTime (Optional[str]): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. The date and dateTime field cannot be provided at the same time. Default to None.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
            - recurrence (Optional[List[str]]): The recurrence rules of the event in RRULE format and exception dates in EXDATE format.
                Examples:
                - Daily for 5 occurrences: ["RRULE:FREQ=DAILY;COUNT=5"]
                - Weekly on Monday and Wednesday: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
                - Monthly on the 15th: ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
                - Yearly on January 1st: ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"]
                - Every 2 weeks: ["RRULE:FREQ=WEEKLY;INTERVAL=2"]
                - Until a specific date: ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
                - With exception dates: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225T120000Z", "EXDATE:20250101T120000Z"]
                - Multiple exception dates: ["RRULE:FREQ=DAILY;COUNT=10", "EXDATE:20241225T120000Z", "EXDATE:20241226T120000Z"]
                - All-day event exceptions: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225", "EXDATE:20250101"]
                
                Supported RRULE parameters:
                - FREQ: SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY (required)
                - INTERVAL: Positive integer (default: 1)
                - COUNT: Positive integer (number of occurrences)
                - UNTIL: YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS format
                - BYDAY: SU,MO,TU,WE,TH,FR,SA (with optional ordinal: 1SU, -1MO)
                - BYMONTH: 1-12
                - BYMONTHDAY: 1-31
                - BYYEARDAY: 1-366
                - BYWEEKNO: 1-53
                - BYHOUR: 0-23
                - BYMINUTE: 0-59
                - BYSECOND: 0-59
                - BYSETPOS: 1-366 or -366 to -1
                - WKST: SU,MO,TU,WE,TH,FR,SA (week start)
                
                Supported EXDATE format:
                - EXDATE:YYYYMMDDTHHMMSSZ (UTC timezone)
                - EXDATE:YYYYMMDDTHHMMSS (floating/local time)
                - EXDATE:YYYYMMDD (date only for all-day events)
                - Multiple dates: Use separate EXDATE entries (not comma-separated)
                Note: TZID parameter not supported in this implementation
                
            - attendees (Optional[List[Dict[str, Any]]]): List of event attendees. Each attendee can have:
                - email (Optional[str]): The attendee's email address
                - displayName (Optional[str]): The attendee's display name
                - organizer (Optional[bool]): Whether the attendee is the organizer
                - self (Optional[bool]): Whether the attendee is the user
                - resource (Optional[bool]): Whether the attendee is a resource
                - optional (Optional[bool]): Whether the attendee's presence is optional
                - responseStatus (Optional[str]): The attendee's response status
                - comment (Optional[str]): The attendee's comment
                - additionalGuests (Optional[int]): Number of additional guests

            - reminders (Optional[Dict[str, Any]]): The reminders of the event.
                - useDefault (Optional[bool]): Whether to use the default reminders.
                - overrides (Optional[List[Dict[str, Any]]]): The list of overrides.
                    - method (Optional[str]): The method of the reminder.
                    - minutes (Optional[int]): The minutes of the reminder.
        
            - location (Optional[str]): The location of the event.

            - attachments (Optional[List[Dict[str, Any]]]): The attachments list contains the dicts and each dict has the following key:
                - fileUrl (str): The URL of the attachment

        sendUpdates (Optional[str]): Whether to send updates about the creation.
                                     Possible values: "all", "externalOnly", "none". Defaults to None.

    Returns:
        Dict[str, Any]: The created event.
            - id (str): The identifier of the event.
            - summary (str): The summary of the event.
            - description (str): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - date (Optional[str]): The date of the start time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - date (Optional[str]): The date of the end time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
            - attendees (List[Dict[str, Any]], optional): List of event attendees with their details.
            - recurrence (Optional[List[str]]): The recurrence rules of the event. e.g. ["RRULE:FREQ=DAILY;COUNT=5"]
            - reminders (Optional[Dict[str, Any]]): The reminders of the event.
            - location (Optional[str]): The location of the event.
            - attachments (Optional[List[Dict[str, Any]]]): The attachments list contains the dicts and each dict has the following key:
                -fileUrl (str): The URL of the attachment

    Raises:
        TypeError: If 'calendarId' is not a string or 'sendUpdates' is not a string (if provided).
        ValueError: If 'resource' is not provided (i.e., is None).
        InvalidInputError: If 'sendUpdates' has an invalid value (not one of: "all", "externalOnly", "none") or 'calendarId' is empty or whitespace.
        ResourceNotFoundError: If 'calendarId' does not exist in the database.
        ResourceAlreadyExistsError: If an event with the same ID already exists in the calendar.
        pydantic.ValidationError: If 'resource' is provided but does not conform to the
                                  EventResourceInputModel structure (e.g., missing 'start',
                                  'end', or incorrect types for fields like 'dateTime').
                                  This includes validation errors for recurrence rules.
        DateTimeValidationError: If the date string is invalid; or
                                 the datetime string is invalid; or
                                 timezone is invalid; or
                                 date and datetime are provided at the same time; or
                                 date and datetime are not provided at the same time; or
                                 nor the datetime have timezone info nor the timezone is provided.

    Examples:
        # Create a simple event
        event = create_event("primary", {
            "summary": "Team Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"}
        })
        
        # Create a recurring daily event
        event = create_event("primary", {
            "summary": "Daily Standup",
            "start": {"dateTime": "2024-01-15T09:00:00Z"},
            "end": {"dateTime": "2024-01-15T09:30:00Z"},
            "recurrence": ["RRULE:FREQ=DAILY;COUNT=10"]
        })
        
        # Create a weekly event on specific days
        event = create_event("primary", {
            "summary": "Weekly Review",
            "start": {"dateTime": "2024-01-15T14:00:00Z"},
            "end": {"dateTime": "2024-01-15T15:00:00Z"},
            "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"]
        })

        # Create an event with an attachment
        event = create_event("primary", {
            "summary": "Meeting with attachment",
            "start": {"dateTime": "2024-01-16T10:00:00Z"},
            "end": {"dateTime": "2024-01-16T11:00:00Z"},
            "attachments": [{
                "fileUrl": "https://example.com/mydocument.pdf"
            }]
        })
    """
    # Validate calendarId
    if calendarId is None:
        calendarId = "primary"
    if not isinstance(calendarId, str):
        raise InvalidInputError("calendarId must be a string.")
    if not calendarId.strip():
        raise InvalidInputError("calendarId cannot be empty or whitespace.")

    # Validate resource
    if resource is None:
        raise ValueError("Resource is required to create an event.")
    validated_resource = EventResourceInputModel(**resource)
    if (validated_resource.start.dateTime and not validated_resource.end.dateTime) or (not validated_resource.start.dateTime and validated_resource.end.dateTime) or (validated_resource.start.date and not validated_resource.end.date) or (not validated_resource.start.date and validated_resource.end.date):
        raise InvalidInputError("Start and end times must either both be date or both be dateTime.")

    # Validate sendUpdates
    if sendUpdates is not None:
        if not isinstance(sendUpdates, str):
            raise TypeError("sendUpdates must be a string if provided.")
        valid_send_updates = ["all", "externalOnly", "none"]
        if sendUpdates not in valid_send_updates:
            raise InvalidInputError(f"sendUpdates must be one of: {', '.join(valid_send_updates)}")

    if calendarId == "primary":
        calendarId = get_primary_calendar_entry()["id"]

    if calendarId not in DB["calendar_list"]:
        raise ResourceNotFoundError(f"Calendar '{calendarId}' not found.")

    # Check for duplicate event ID
    ev_id = validated_resource.id or str(uuid.uuid4())
    event_key = f'{calendarId}:{ev_id}'
    if event_key in DB["events"]:
        raise ResourceAlreadyExistsError(f"Event with ID '{ev_id}' already exists in calendar '{calendarId}'.")

    event_dict = validated_resource.model_dump()
    event_dict["id"] = ev_id

    # Convert the start and end times to UTC timezone
    event_dict_to_DB = event_dict.copy()
    if event_dict_to_DB['start']['dateTime']:
        event_dict_to_DB['start'] = local_to_UTC(event_dict_to_DB['start'])
    if event_dict_to_DB['end']['dateTime']:
        event_dict_to_DB['end'] = local_to_UTC(event_dict_to_DB['end'])
    DB["events"][f'{calendarId}:{ev_id}'] = event_dict_to_DB

    # Standardize to return
    event_dict_to_return = event_dict_to_DB.copy()
    if event_dict_to_return['start']['dateTime']:
        event_dict_to_return['start'] = UTC_to_local(event_dict_to_return['start'])
    if event_dict_to_return['end']['dateTime']:
        event_dict_to_return['end'] = UTC_to_local(event_dict_to_return['end'])

    try:
        notify_attendees(
            calendarId, event_dict_to_return, sendUpdates, subject_prefix="Invitation")
    except Exception:
        # Non-fatal in simulation
        pass
    return event_dict_to_return


@tool_spec(
    spec={
        'name': 'list_event_instances',
        'description': """ Returns instances of a specified recurring event.
        
        This is a mock, so we won't actually expand recurrences.
        We'll pretend the event itself is the only instance. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'alwaysIncludeEmail': {
                    'type': 'boolean',
                    'description': """ Whether to include the email address of the event creator.
                    Defaults to False. """
                },
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar. If not provided, defaults to "primary".'
                },
                'eventId': {
                    'type': 'string',
                    'description': 'The identifier of the event.'
                },
                'maxAttendees': {
                    'type': 'integer',
                    'description': """ The maximum number of attendees to return.
                    Must be non-negative. Defaults to None (return all attendees). """
                },
                'maxResults': {
                    'type': 'integer',
                    'description': """ The maximum number of instances to return.
                    Must be a positive integer. Defaults to 250. """
                },
                'originalStart': {
                    'type': 'string',
                    'description': 'The original start time of the instance in ISO 8601 format.'
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'The token for the next page of results.'
                },
                'showDeleted': {
                    'type': 'boolean',
                    'description': """ Whether to include deleted instances.
                    Defaults to False. """
                },
                'timeMax': {
                    'type': 'string',
                    'description': 'The maximum time of the instances to return in ISO 8601(YYYY-MM-DDTHH:MM:SSZ) format.'
                },
                'timeMin': {
                    'type': 'string',
                    'description': 'The minimum time of the instances to return in ISO 8601(YYYY-MM-DDTHH:MM:SSZ) format.'
                },
                'timeZone': {
                    'type': 'string',
                    'description': """ The time zone to use for the response (e.g. "America/New_York").
                    Must be in format 'Continent/City'. Defaults to the calendar's time zone. """
                }
            },
            'required': []
        }
    }
)
def list_event_instances(
    alwaysIncludeEmail: Optional[bool] = False,
    calendarId: Optional[str] = "primary",
    eventId: Optional[str] = None,
    maxAttendees: Optional[int] = None,
    maxResults: Optional[int] = 250,
    originalStart: Optional[str] = None,
    pageToken: Optional[str] = None,
    showDeleted: Optional[bool] = False,
    timeMax: Optional[str] = None,
    timeMin: Optional[str] = None,
    timeZone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns instances of a specified recurring event.
    This is a mock, so we won't actually expand recurrences.
    We'll pretend the event itself is the only instance.

    Args:
        alwaysIncludeEmail (Optional[bool]): Whether to include the email address of the event creator.
            Defaults to False.
        calendarId (Optional[str]): The identifier of the calendar. If not provided, defaults to "primary".
        eventId (Optional[str]): The identifier of the event.
        maxAttendees (Optional[int]): The maximum number of attendees to return.
            Must be non-negative. Defaults to None (return all attendees).
        maxResults (Optional[int]): The maximum number of instances to return.
            Must be a positive integer. Defaults to 250.
        originalStart (Optional[str]): The original start time of the instance in RFC 3339 format.
        pageToken (Optional[str]): The token for the next page of results.
        showDeleted (Optional[bool]): Whether to include deleted instances.
            Defaults to False.
        timeMax (Optional[str]): The maximum time of the instances to return in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ.
        timeMin (Optional[str]): The minimum time of the instances to return in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ.
        timeZone (Optional[str]): The time zone to use for the response (e.g. "America/New_York").
            Must be in format 'Continent/City'. Defaults to the calendar's time zone.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - items (List[Dict[str, Any]]): The list of event instances.
                - id (str): The identifier of the event.
                - summary (str): The summary of the event.
                - description (str): The description of the event.
                - start (Dict[str, Any]): The start time of the event.
                    - date (Optional[str]): The date of the start time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                    - dateTime (Optional[str]): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                    - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
                - end (Dict[str, Any]): The end time of the event.
                    - date (Optional[str]): The date of the end time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                    - dateTime (Optional[str]): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                    - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
                - attendees (List[Dict[str, Any]], optional): List of attendees (limited by maxAttendees).
                - timeZone (str, optional): Applied timezone if timeZone parameter was provided.
            - nextPageToken (str): The next page token. None if there are no more pages.

    Raises:
        TypeError: If any argument has an invalid type.
        InvalidInputError: If any argument has an invalid value or format.
        ResourceNotFoundError: If the calendar or event is not found.
    """
    # --- Input Validation ---
    
    # Validate alwaysIncludeEmail
    if not isinstance(alwaysIncludeEmail, bool):
        raise TypeError("alwaysIncludeEmail must be a boolean")
    
    # Validate calendarId
    if calendarId is not None:
        if not isinstance(calendarId, str):
            raise TypeError("calendarId must be a string")
        if not calendarId.strip():
            raise InvalidInputError("calendarId cannot be empty or whitespace")
    
    # Validate eventId
    if eventId is not None:
        if not isinstance(eventId, str):
            raise TypeError("eventId must be a string")
        if not eventId.strip():
            raise InvalidInputError("eventId cannot be empty or whitespace")
    
    # Validate maxAttendees
    if maxAttendees is not None:
        if not isinstance(maxAttendees, int):
            raise TypeError("maxAttendees must be an integer")
        if maxAttendees < 0:
            raise InvalidInputError("maxAttendees cannot be negative")
    
    # Validate maxResults
    if not isinstance(maxResults, int):
        raise TypeError("maxResults must be an integer")
    if maxResults <= 0:
        raise InvalidInputError("maxResults must be a positive integer")
    
    # Validate originalStart
    if originalStart is not None:
        if not isinstance(originalStart, str):
            raise TypeError("originalStart must be a string")
        if not originalStart.strip():
            raise InvalidInputError("originalStart cannot be empty or whitespace")
        try:
            parsed_start = parse_iso_datetime(originalStart)
            if parsed_start is None:
                raise InvalidInputError("originalStart must be a valid RFC 3339 datetime string.")
        except ValueError as e:
            raise InvalidInputError(f"Invalid originalStart format: {str(e)}. Must be in RFC 3339 format (YYYY-MM-DDTHH:MM:SSZ)")
    
    # Validate pageToken
    if pageToken is not None:
        if not isinstance(pageToken, str):
            raise TypeError("pageToken must be a string")
        if not pageToken.strip():
            raise InvalidInputError("pageToken cannot be empty or whitespace")
    
    # Validate showDeleted
    if not isinstance(showDeleted, bool):
        raise TypeError("showDeleted must be a boolean")
    
    # Validate timeMax
    if timeMax is not None:
        if not isinstance(timeMax, str):
            raise TypeError("timeMax must be a string")
        if not timeMax.strip():
            raise InvalidInputError("timeMax cannot be empty or whitespace")
        try:
            parsed_timeMax = parse_iso_datetime(timeMax)
            if parsed_timeMax is None:
                raise InvalidInputError("timeMax must be a valid RFC 3339 datetime string.")
        except ValueError as e:
            raise InvalidInputError(f"Invalid timeMax format: {str(e)}. Must be in RFC 3339 format (YYYY-MM-DDTHH:MM:SSZ)")
    
    # Validate timeMin
    if timeMin is not None:
        if not isinstance(timeMin, str):
            raise TypeError("timeMin must be a string")
        if not timeMin.strip():
            raise InvalidInputError("timeMin cannot be empty or whitespace")
        try:
            parsed_timeMin = parse_iso_datetime(timeMin)
            if parsed_timeMin is None:
                raise InvalidInputError("timeMin must be a valid RFC 3339 datetime string.")
        except ValueError as e:
            raise InvalidInputError(f"Invalid timeMin format: {str(e)}. Must be in RFC 3339 format (YYYY-MM-DDTHH:MM:SSZ)")
    
    # Validate timeZone
    if timeZone is not None:
        if not isinstance(timeZone, str):
            raise TypeError("timeZone must be a string")
        if not timeZone.strip():
            raise InvalidInputError("timeZone cannot be empty or whitespace")
        # Basic timezone format validation (e.g., "Continent/City")
        if "/" not in timeZone:
            raise InvalidInputError("timeZone must be in format 'Continent/City' (e.g., 'America/New_York')")
    
    # Validate time range consistency
    if timeMin is not None and timeMax is not None:
        try:
            timeMin_dt = parse_iso_datetime(timeMin)
            timeMax_dt = parse_iso_datetime(timeMax)
            if timeMin_dt and timeMax_dt and timeMin_dt >= timeMax_dt:
                raise InvalidInputError("timeMin must be earlier than timeMax")
        except ValueError:
            # Already handled above in individual validations
            pass
    
    # --- End Input Validation ---
    
    # --- Core Logic ---
    
    # Handle calendarId default and primary calendar logic
    effective_calendarId = calendarId
    if effective_calendarId is None or effective_calendarId == "":
        effective_calendarId = "primary"

    # Map "primary" to the user's primary calendar ID
    if effective_calendarId == "primary":
        # Find the actual primary calendar from the DB
        primary_calendar = None
        if "calendar_list" in DB and DB["calendar_list"]:
            for cal_id, cal_data in DB["calendar_list"].items():
                if cal_data.get("primary") is True:
                    primary_calendar = cal_id
                    break
        
        if primary_calendar:
            effective_calendarId = primary_calendar

    # Check if calendar exists
    if "calendar_list" not in DB or effective_calendarId not in DB["calendar_list"]:
        raise ResourceNotFoundError(f"Calendar '{effective_calendarId}' not found.")

    # Check if event exists
    key = f'{effective_calendarId}:{eventId}'
    if "events" not in DB or key not in DB["events"]:
        raise ResourceNotFoundError(f"Event '{eventId}' not found in calendar '{effective_calendarId}'.")
    
    # Get the event
    event = DB["events"][key].copy()
    
    # Apply time filtering if timeMin/timeMax are provided
    if timeMin is not None or timeMax is not None:
        # Check if event has valid start/end times for filtering
        event_start = None
        event_end = None
        
        if "start" in event:
            if "dateTime" in event["start"] and event["start"]["dateTime"] is not None:
                try:
                    event_start = parse_iso_datetime(event["start"]["dateTime"]).replace(tzinfo=timezone.utc)
                except:
                    pass
            elif "date" in event["start"]:
                event_start = parse_iso_datetime(event["start"]["date"])
        
        if "end" in event:
            if "dateTime" in event["end"] and event["end"]["dateTime"] is not None:
                try:
                    event_end = parse_iso_datetime(event["end"]["dateTime"]).replace(tzinfo=timezone.utc)
                except:
                    pass
            elif "date" in event["end"]:
                event_end = parse_iso_datetime(event["end"]["date"])
        
        # Filter by timeMin
        if timeMin is not None and event_start is not None:
            timeMin_dt = parse_iso_datetime(timeMin)
            if timeMin_dt and event_start < timeMin_dt:
                # Event starts before timeMin, exclude it
                return {"items": [], "nextPageToken": None}
        
        # Filter by timeMax
        if timeMax is not None and event_end is not None:
            timeMax_dt = parse_iso_datetime(timeMax)
            if timeMax_dt and event_end > timeMax_dt:
                # Event ends after timeMax, exclude it
                return {"items": [], "nextPageToken": None}
    
    # Apply originalStart filtering if provided
    if originalStart is not None:
        original_start_dt = parse_iso_datetime(originalStart)
        if original_start_dt is not None:
            # In a real implementation, this would filter instances based on originalStart
            # For this mock, we'll just check if the event's start time matches
            if "start" in event and "dateTime" in event["start"]:
                try:
                    event_start = parse_iso_datetime(event["start"]["dateTime"]).replace(tzinfo=timezone.utc)
                    if event_start != original_start_dt:
                        # Event start doesn't match originalStart, exclude it
                        return {"items": [], "nextPageToken": None}
                except ValueError:
                    # If we can't parse the event start time, exclude it
                    return {"items": [], "nextPageToken": None}
    
    # Apply showDeleted filtering
    if not showDeleted and event.get("status") == "cancelled":
        # Event is deleted and showDeleted is False, exclude it
        return {"items": [], "nextPageToken": None}
    
    # Apply timeZone parameter (simulated)
    if timeZone is not None:
        event["timeZone"] = timeZone
    
    # Handle maxAttendees parameter
    if "attendees" in event and maxAttendees is not None:
        if isinstance(event.get("attendees"), list):
            event["attendees"] = event["attendees"][:maxAttendees]
    
    # Apply maxResults (though in this mock we only return 1 item max)
    # In a real implementation, this would limit the number of instances returned
    items = [event]
    if len(items) > maxResults:
        items = items[:maxResults]
    
    # Handle pagination (though in this mock we only return 1 item max)
    # In a real implementation, this would handle pageToken and return nextPageToken
    nextPageToken = None
    if pageToken is not None:
        # In a real implementation, this would validate and use the pageToken
        # For this mock, we'll just ignore it since we only return 1 item
        pass
    
    # Converts to local timeZone and returns the event instances
    for item in items:
        if "start" in item and "dateTime" in item["start"] and item["start"]["dateTime"] is not None:
            if is_datetime_of_format(item["start"]["dateTime"], "YYYY-MM-DDTHH:MM:SS+/-HH:MM"):
                item["start"]["dateTime"] = item["start"]["dateTime"][:-6]
            item["start"] = UTC_to_local(item["start"])
        if "end" in item and "dateTime" in item["end"] and item["end"]["dateTime"] is not None:
            if is_datetime_of_format(item["end"]["dateTime"], "YYYY-MM-DDTHH:MM:SS+/-HH:MM"):
                item["end"]["dateTime"] = item["end"]["dateTime"][:-6]
            item["end"] = UTC_to_local(item["end"])
    return {"items": items, "nextPageToken": nextPageToken}


@tool_spec(
    spec={
        'name': 'list_events',
        'description': 'Lists events from the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar. Defaults to "primary".'
                },
                'maxResults': {
                    'type': 'integer',
                    'description': """ The maximum number of events to return.
                    Must be a positive integer. Defaults to 250. Maximum allowed value is 2500. """
                },
                'timeMin': {
                    'type': 'string',
                    'description': 'The minimum time of the events to return. Must be timezone-aware RFC 3339 datetime string (e.g., "2024-04-01T00:00:00Z" or "2024-04-01T00:00:00+05:00").'
                },
                'timeMax': {
                    'type': 'string',
                    'description': 'The maximum time of the events to return. Must be timezone-aware RFC 3339 datetime string (e.g., "2024-04-01T23:59:59Z" or "2024-04-01T23:59:59-05:00").'
                },
                'q': {
                    'type': 'string',
                    'description': 'The query string to filter events by.'
                },
                'singleEvents': {
                    'type': 'boolean',
                    'description': """ Whether to expand recurring events into individual instances.
                    When True, recurring events are expanded into separate instances within the time range.
                    When False, only the base recurring event is returned. Defaults to False. """
                },
                'orderBy': {
                    'type': 'string',
                    'description': """ The order of the events.
                    Must be one of: "startTime", "updated". Defaults to None. """
                },
                'timeZone': {
                    'type': 'string',
                    'description': """ Time zone used in the response. Optional. The default is the time zone of the calendar. """
                }
            },
            'required': []
        }
    }
)
def list_events(
    calendarId: Optional[str] = "primary",  # Changed from `Optional[str] = None` to `Optional[str] = "primary"`
    maxResults: Optional[int] = 250,
    timeMin: Optional[str] = None,
    timeMax: Optional[str] = None,
    q: Optional[str] = None,
    singleEvents: Optional[bool] = False,
    orderBy: Optional[str] = None,
    timeZone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lists events from the specified calendar.

    Args:
        calendarId (Optional[str]): The identifier of the calendar. Defaults to "primary".
        maxResults (Optional[int]): The maximum number of events to return.
            Must be a positive integer. Defaults to 250. Maximum allowed value is 2500.
        timeMin (Optional[str]): The minimum time of the events to return. Must be timezone-aware 
            RFC 3339 datetime string (e.g., "2024-04-01T00:00:00Z" or "2024-04-01T00:00:00+05:00").
        timeMax (Optional[str]): The maximum time of the events to return. Must be timezone-aware 
            RFC 3339 datetime string (e.g., "2024-04-01T23:59:59Z" or "2024-04-01T23:59:59-05:00").
        q (Optional[str]): The query string to filter events by.
        singleEvents (Optional[bool]): Whether to expand recurring events into individual instances.
            When True, recurring events are expanded into separate instances within the time range.
            When False, only the base recurring event is returned. Defaults to False.
        orderBy (Optional[str]): The order of the events.
            Must be one of: "startTime", "updated". Defaults to None.
        timeZone (Optional[str]): Time zone used in the response. Optional. The default is the time zone of the calendar.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - items (List[Dict[str, Any]]): The list of events.
                - id (str): The identifier of the event.
                - summary (str): The summary of the event.
                - description (str): The description of the event.
                - start (Dict[str, Any]): The start time of the event.
                    - date (Optional[str]): The date of the start time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                    - dateTime (Optional[str]): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                    - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
                - end (Dict[str, Any]): The end time of the event.
                    - date (Optional[str]): The date of the end time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                    - dateTime (Optional[str]): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                    - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
                - recurrence (Optional[List[str]]): The recurrence rules (only present for base recurring events).
                - recurringEventId (Optional[str]): The ID of the parent recurring event (only present for instances).
                - originalStartTime (Optional[Dict[str, Any]]): The original start time of the recurring event.

    Raises:
        TypeError: If `calendarId` is provided and is not a string.
        TypeError: If `maxResults` is not an integer.
        TypeError: If `timeMin` is provided and is not a string.
        TypeError: If `timeMax` is provided and is not a string.
        TypeError: If `q` is provided and is not a string.
        TypeError: If `singleEvents` is not a boolean.
        TypeError: If `orderBy` is provided and is not a string.
        InvalidInputError: If `maxResults` is not a positive integer or exceeds the maximum value of 2500.
        InvalidInputError: If `timeMin` or `timeMax` contains a malformed datetime string that cannot be parsed.
        InvalidInputError: If `orderBy` has an invalid value (not "startTime" or "updated").
        InvalidInputError: If `timeZone` is provided and is not a string in the IANA format (e.g. "America/New_York").
        ResourceNotFoundError: If the specified `calendarId` does not exist in the database.
        ResourceNotFoundError: If `calendarId` is set to "primary" but no primary calendar is found for the user.            
    """
    # --- Input Validation ---
    if calendarId is not None and not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string if provided.")

    if not isinstance(maxResults, int):
        raise TypeError("maxResults must be an integer.")
    if maxResults <= 0:
        raise InvalidInputError("maxResults must be a positive integer.")
    if maxResults > 2500:
        raise InvalidInputError("maxResults can not be greater than 2500 events.")

    timeMin_dt = None
    if timeMin is not None:
        if not isinstance(timeMin, str):
            raise TypeError("timeMin must be a string if provided (RFC 3339 datetime format).")
        if not validate_rfc3339(timeMin):
            raise InvalidInputError("timeMin must be a valid RFC 3339 datetime string.")
        try:
            timeMin_dt = parse_iso_datetime(timeMin)
            if timeMin_dt is None:
                raise InvalidInputError("timeMin must be a valid RFC 3339 datetime string.")
        except ValueError as e:
            raise InvalidInputError(f"Invalid timeMin format: {str(e)}. Must be in RFC 3339 format.")

    timeMax_dt = None
    if timeMax is not None:
        if not isinstance(timeMax, str):
            raise TypeError("timeMax must be a string if provided (RFC 3339 datetime format).")
        if not validate_rfc3339(timeMax):
            raise InvalidInputError("timeMax must be a valid RFC 3339 datetime string.")
        try:
            timeMax_dt = parse_iso_datetime(timeMax)
            if timeMax_dt is None:
                raise InvalidInputError("timeMax must be a valid RFC 3339 datetime string.")
        except ValueError as e:
            raise InvalidInputError(f"Invalid timeMax format: {str(e)}. Must be in RFC 3339 format.")

    if q is not None and not isinstance(q, str):
        raise TypeError("q must be a string if provided.")

    if not isinstance(singleEvents, bool):
        raise TypeError("singleEvents must be a boolean.")

    if orderBy is not None:
        if not isinstance(orderBy, str):
            raise TypeError("orderBy must be a string if provided.")
        valid_order_by = ["startTime", "updated"]
        if orderBy not in valid_order_by:
            raise InvalidInputError(f"orderBy must be one of: {', '.join(valid_order_by)}")

    if timeZone is not None:
        if not isinstance(timeZone, str):
            raise TypeError("timeZone must be a string if provided.")
        if not timeZone.strip():
            raise InvalidInputError("timeZone cannot be empty or whitespace.")
        if not is_timezone_valid(timeZone):
            raise InvalidInputError("timeZone must be in format 'Continent/City' (e.g., 'America/New_York').")

    # --- Core Logic ---
    effective_calendarId = calendarId or "primary"
    
    if effective_calendarId == "primary":
        primary_calendar = next((cal_id for cal_id, cal_data in DB.get("calendar_list", {}).items() if cal_data.get("primary")), None)
        if primary_calendar:
            effective_calendarId = primary_calendar
        else:
            raise ResourceNotFoundError("No primary calendar found for the user.")

    # Validate that the calendar exists in the database
    if effective_calendarId not in DB.get("calendar_list", {}):
        raise ResourceNotFoundError(f"Calendar '{effective_calendarId}' not found.")  
    
    # Parse datetime objects for time range filtering
    timeMin_dt = parse_iso_datetime(timeMin).astimezone(timezone.utc) if timeMin is not None else None
    timeMax_dt = parse_iso_datetime(timeMax).astimezone(timezone.utc) if timeMax is not None else None
    results = []

    if not timeZone:
        if effective_calendarId not in DB.get("calendar_list", {}):
            raise ResourceNotFoundError(f"Calendar with ID '{effective_calendarId}' not found.")
        timeZone = DB["calendar_list"][effective_calendarId].get("timeZone")
        if not timeZone:
            raise InvalidInputError("timeZone not passed as input and not set for the calendar.")

    query_words = q.strip().lower() if q else ''

    base_events = [
        ev_obj
        for key, ev_obj in DB.get("events", {}).items()
        if isinstance(key, str) and key.split(':')[0] == effective_calendarId and event_matches_query(ev_obj, query_words)
    ]

    results = []
    if singleEvents:
        expanded_events = expand_recurring_events(
            base_events, 
            timeMin_dt, 
            timeMax_dt, 
            max_instances_per_event=50
        )

        for event in expanded_events:
            event_start = parse_iso_datetime(event.get("start", {}).get("dateTime")).replace(tzinfo=timezone.utc)
            event_end = parse_iso_datetime(event.get("end", {}).get("dateTime")).replace(tzinfo=timezone.utc)
            
            if timeMin_dt and event_start and event_start < timeMin_dt:
                continue
            
            if timeMax_dt and event_end and event_end > timeMax_dt:
                continue
            
            results.append(event)
    else:
        for event in base_events:
            # Filter by timeMin
            if timeMin is not None: # timeMin_dt would be None if timeMin was None
                if "start" not in event:
                    continue
                if "dateTime" not in event["start"] and "date" not in event["start"]:
                    continue
                if "dateTime" in event["start"] and event["start"]["dateTime"] is not None:
                    event_start = parse_iso_datetime(event["start"]["dateTime"]).replace(tzinfo=timezone.utc)
                elif "date" in event["start"]:
                    event_start = parse_iso_datetime(event["start"]["date"])
                if event_start is None or timeMin_dt is None: # Guard against None from parse_iso_datetime
                    continue
                if event_start < timeMin_dt:
                    continue
            # Filter by timeMax
            if timeMax is not None: # timeMax_dt would be None if timeMax was None
                if "end" not in event:
                    continue
                if "dateTime" not in event["end"] and "date" not in event["end"]:
                    continue
                if "dateTime" in event["end"] and event["end"]["dateTime"] is not None:
                    event_end = parse_iso_datetime(event["end"]["dateTime"]).replace(tzinfo=timezone.utc)
                elif "date" in event["end"]:
                    event_end = parse_iso_datetime(event["end"]["date"])
                if event_end is None or timeMax_dt is None: # Guard against None from parse_iso_datetime
                    continue
                if event_end > timeMax_dt:
                    continue

            if timeMin_dt and (not event_start or event_start < timeMin_dt):
                continue
            if timeMax_dt and (not event_end or event_end > timeMax_dt):
                continue
            results.append(event)
    
    # Sort results if orderBy is specified
    if orderBy == "startTime":
        results.sort(key=lambda x: parse_iso_datetime(x.get("start", {}).get("dateTime")).replace(tzinfo=timezone.utc) or datetime.max)
    elif orderBy == "updated":
        results.sort(key=lambda x: parse_iso_datetime(x.get("updated")) if x.get("updated") else datetime.max, reverse=True)
    
    # Converts to desired timeZone and returns the event instances
    results_to_return = copy.deepcopy(results)
    for item in results_to_return:
        if "start" in item and "dateTime" in item["start"] and item["start"]["dateTime"] is not None:
            # Preserve the original timezone field
            original_timezone = item["start"].get("timeZone")
            if is_datetime_of_format(item["start"]["dateTime"], "YYYY-MM-DDTHH:MM:SS+/-HH:MM"):
                item["start"]["dateTime"] = item["start"]["dateTime"][:-6]
            # Convert to the requested timezone (or calendar's timezone if not specified)
            item['start']['offset'] = timezone_to_offset(item["start"]["dateTime"], timeZone)
            item["start"]["timeZone"] = original_timezone  # Preserve the original timezone field
            item["start"] = UTC_to_local(item["start"])
        if "end" in item and "dateTime" in item["end"] and item["end"]["dateTime"] is not None:
            # Preserve the original timezone field
            original_timezone = item["end"].get("timeZone")
            if is_datetime_of_format(item["end"]["dateTime"], "YYYY-MM-DDTHH:MM:SS+/-HH:MM"):
                item["end"]["dateTime"] = item["end"]["dateTime"][:-6]
            # Convert to the requested timezone (or calendar's timezone if not specified)
            item['end']['offset'] = timezone_to_offset(item["end"]["dateTime"], timeZone)
            item["end"]["timeZone"] = original_timezone  # Preserve the original timezone field
            item["end"] = UTC_to_local(item["end"])
    return {"items": results_to_return[:maxResults]}


@tool_spec(
    spec={
        'name': 'move_event',
        'description': """ Moves an event from one calendar to another. We simulate by removing from old
        
        and creating in new with same ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the source calendar.'
                },
                'eventId': {
                    'type': 'string',
                    'description': 'The identifier of the event to move.'
                },
                'destination': {
                    'type': 'string',
                    'description': 'The identifier of the destination calendar.'
                },
                'sendUpdates': {
                    'type': 'string',
                    'description': """ Whether to send updates about the move.
                    Possible values: "all", "externalOnly", "none". Defaults to None. """
                }
            },
            'required': [
                'calendarId',
                'eventId',
                'destination'
            ]
        }
    }
)
def move_event(
    calendarId: str,
    eventId: str,
    destination: str,
    sendUpdates: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Moves an event from one calendar to another. We simulate by removing from old
    and creating in new with same ID.

    Args:
        calendarId (str): The identifier of the source calendar.
        eventId (str): The identifier of the event to move.
        destination (str): The identifier of the destination calendar.
        sendUpdates (Optional[str]): Whether to send updates about the move.
            Possible values: "all", "externalOnly", "none". Defaults to None.

    Returns:
        Dict[str, Any]: The moved event.
            - id (str): The identifier of the event.
            - summary (str): The summary of the event.
            - description (str): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - date (Optional[str]): The date of the start time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - date (Optional[str]): The date of the end time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.

    Raises:
        TypeError: If any argument has an invalid type (e.g., calendarId is not str).
        InvalidInputError: If any argument has an invalid value:
            - calendarId is empty/whitespace
            - eventId is empty/whitespace
            - destination is empty/whitespace
            - sendUpdates has invalid value (not one of: "all", "externalOnly", "none")
        ResourceNotFoundError: If the event is not found in the calendar.
        ResourceAlreadyExistsError: If the event already exists in the destination calendar.
    """
    # --- Input Validation ---
    # Validate calendarId
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string.")
    if not calendarId.strip():
        raise InvalidInputError("calendarId cannot be empty or whitespace.")

    # Validate eventId
    if not isinstance(eventId, str):
        raise TypeError("eventId must be a string.")
    if not eventId.strip():
        raise InvalidInputError("eventId cannot be empty or whitespace.")

    # Validate destination
    if not isinstance(destination, str):
        raise TypeError("destination must be a string.")
    if not destination.strip():
        raise InvalidInputError("destination cannot be empty or whitespace.")

    # Validate sendUpdates
    if sendUpdates is not None:
        if not isinstance(sendUpdates, str):
            raise TypeError("sendUpdates must be a string if provided.")
        valid_send_updates = ["all", "externalOnly", "none"]
        if sendUpdates not in valid_send_updates:
            raise InvalidInputError(f"sendUpdates must be one of: {', '.join(valid_send_updates)}")

    # --- Core Logic ---
    
    # Map "primary" to the user's primary calendar ID for source calendar
    effective_calendarId = calendarId
    if effective_calendarId == "primary":
        # Find the actual primary calendar from the DB
        primary_calendar = None
        if "calendar_list" in DB and DB["calendar_list"]:
            for cal_id, cal_data in DB["calendar_list"].items():
                if cal_data.get("primary") is True:
                    primary_calendar = cal_id
                    break
        
        if primary_calendar:
            effective_calendarId = primary_calendar
    
    # Map "primary" to the user's primary calendar ID for destination calendar
    effective_destination = destination
    if effective_destination == "primary":
        # Find the actual primary calendar from the DB
        primary_calendar = None
        if "calendar_list" in DB and DB["calendar_list"]:
            for cal_id, cal_data in DB["calendar_list"].items():
                if cal_data.get("primary") is True:
                    primary_calendar = cal_id
                    break
        
        if primary_calendar:
            effective_destination = primary_calendar
    
    old_key = f'{effective_calendarId}:{eventId}'
    if old_key not in DB["events"]:
        raise ResourceNotFoundError(f"Event '{eventId}' not found in calendar '{effective_calendarId}'.")
    
    ev_data = DB["events"].pop(old_key)
    new_key = f'{effective_destination}:{eventId}'
    if new_key in DB["events"]:
        raise ResourceAlreadyExistsError(
            f"Event '{eventId}' already exists in destination calendar '{effective_destination}'."
        )
    DB["events"][new_key] = ev_data

    try:
        notify_attendees(effective_destination, ev_data, sendUpdates, subject_prefix="Moved")
    except Exception:
        pass

    # Converts to local timeZone and returns the event instances
    ev_data_to_return = copy.deepcopy(ev_data)
    if "start" in ev_data_to_return and "dateTime" in ev_data_to_return["start"]:
        if is_datetime_of_format(ev_data_to_return["start"]["dateTime"], "YYYY-MM-DDTHH:MM:SS+/-HH:MM"):
            ev_data_to_return["start"]["dateTime"] = ev_data_to_return["start"]["dateTime"][:-6]
        ev_data_to_return["start"] = UTC_to_local(ev_data_to_return["start"])
    if "end" in ev_data_to_return and "dateTime" in ev_data_to_return["end"]:
        if is_datetime_of_format(ev_data_to_return["end"]["dateTime"], "YYYY-MM-DDTHH:MM:SS+/-HH:MM"):
            ev_data_to_return["end"]["dateTime"] = ev_data_to_return["end"]["dateTime"][:-6]
        ev_data_to_return["end"] = UTC_to_local(ev_data_to_return["end"])
    return ev_data_to_return

# Placeholder for DB if it's to be accessed globally and needs type hint / definition for linters
# DB: Dict[str, Any] = {"events": {}} # This would typically be defined elsewhere


@tool_spec(
    spec={
        'name': 'patch_event',
        'description': """ Updates specific fields of an existing event.
        
        This function allows partial updates to an event by providing only the fields 
        that need to be changed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'eventId': {
                    'type': 'string',
                    'description': 'The identifier of the event to update.'
                },
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar. Defaults to "primary".'
                },
                'resource': {
                    'type': 'object',
                    'description': 'The event to patch. Must contain:',
                    'properties': {
                        'summary': {
                            'type': 'string',
                            'description': 'The summary/title of the event.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the event.'
                        },
                        'start': {
                            'type': 'object',
                            'description': 'The start time of the event.',
                            'properties': {
                                'date': {
                                    'type': 'string',
                                    'description': 'The date of the start time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'timeZone': {
                                    'type': 'string',
                                    'description': 'The time zone of the start time in IANA format (e.g., "America/New_York"). The timeZone is required if the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS). Defaults to None.'
                                }
                            },
                            'required': []
                        },
                        'end': {
                            'type': 'object',
                            'description': 'The end time of the event.',
                            'properties': {
                                'date': {
                                    'type': 'string',
                                    'description': 'The date of the end time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'timeZone': {
                                    'type': 'string',
                                    'description': 'The time zone of the end time in IANA format (e.g., "America/New_York"). The timeZone is required if the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS). Defaults to None.'
                                }
                            },
                            'required': []
                        },
                        'recurrence': {
                            'type': 'array',
                            'description': """ The recurrence rules of the event in RRULE format and exception dates in EXDATE format.
                                 Examples:
                                - Daily for 5 occurrences: ["RRULE:FREQ=DAILY;COUNT=5"]
                                - Weekly on Monday and Wednesday: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
                                - Monthly on the 15th: ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
                                - Yearly on January 1st: ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"]
                                - Every 2 weeks: ["RRULE:FREQ=WEEKLY;INTERVAL=2"]
                                - Until a specific date: ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
                                - With exception dates: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225T120000Z", "EXDATE:20250101T120000Z"]
                                - Multiple exception dates: ["RRULE:FREQ=DAILY;COUNT=10", "EXDATE:20241225T120000Z", "EXDATE:20241226T120000Z"]
                                Supported RRULE parameters:
                                - FREQ: SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY (required)
                                - INTERVAL: Positive integer (default: 1)
                                - COUNT: Positive integer (number of occurrences)
                                - UNTIL: YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS format
                                - BYDAY: SU,MO,TU,WE,TH,FR,SA (with optional ordinal: 1SU, -1MO)
                                - BYMONTH: 1-12
                                - BYMONTHDAY: 1-31
                                - BYYEARDAY: 1-366
                                - BYWEEKNO: 1-53
                                - BYHOUR: 0-23
                                - BYMINUTE: 0-59
                                - BYSECOND: 0-59
                                - BYSETPOS: 1-366 or -366 to -1
                                - WKST: SU,MO,TU,WE,TH,FR,SA (week start)
                                Supported EXDATE format:
                                - EXDATE:YYYYMMDDTHHMMSSZ (UTC timezone)
                                - EXDATE:YYYYMMDDTHHMMSS (floating/local time)
                                - EXDATE:YYYYMMDD (date only for all-day events)
                                - Multiple dates: Use separate EXDATE entries (not comma-separated)
                                Note: TZID parameter not supported in this implementation """,
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': []
                },
                'sendUpdates': {
                    'type': 'string',
                    'description': """ Whether to send updates about the patch.
                    Possible values: "all", "externalOnly", "none". Defaults to None. """
                }
            },
            'required': [
                'eventId'
            ]
        }
    }
)
def patch_event(
    eventId: str,
    calendarId: str = "primary",
    resource: Optional[Dict[str, Any]] = None,
    sendUpdates: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates specific fields of an existing event.

    This function allows partial updates to an event by providing only the fields 
    that need to be changed.
    
    Args:
        eventId (str): The identifier of the event to update.
        calendarId (str): The identifier of the calendar. Defaults to "primary".
        resource (Optional[Dict[str, Any]]): The event to patch. Must contain:
            - summary (Optional[str]): The summary/title of the event.
            - id (Optional[str]): The identifier of the event.
            - description (Optional[str]): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - date (Optional[str]): The date of the start time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - dateTime (Optional[str]): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). The timeZone is required if the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - date (Optional[str]): The date of the end time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - dateTime (Optional[str]): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
            - recurrence (Optional[List[str]]): The recurrence rules of the event in RRULE format and exception dates in EXDATE format.
                Examples:
                - Daily for 5 occurrences: ["RRULE:FREQ=DAILY;COUNT=5"]
                - Weekly on Monday and Wednesday: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
                - Monthly on the 15th: ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
                - Yearly on January 1st: ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"]
                - Every 2 weeks: ["RRULE:FREQ=WEEKLY;INTERVAL=2"]
                - Until a specific date: ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
                - With exception dates: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225T120000Z", "EXDATE:20250101T120000Z"]
                - Multiple exception dates: ["RRULE:FREQ=DAILY;COUNT=10", "EXDATE:20241225T120000Z", "EXDATE:20241226T120000Z"]
                - All-day event exceptions: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225", "EXDATE:20250101"]
                
                Supported RRULE parameters:
                - FREQ: SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY (required)
                - INTERVAL: Positive integer (default: 1)
                - COUNT: Positive integer (number of occurrences)
                - UNTIL: YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS format
                - BYDAY: SU,MO,TU,WE,TH,FR,SA (with optional ordinal: 1SU, -1MO)
                - BYMONTH: 1-12
                - BYMONTHDAY: 1-31
                - BYYEARDAY: 1-366
                - BYWEEKNO: 1-53
                - BYHOUR: 0-23
                - BYMINUTE: 0-59
                - BYSECOND: 0-59
                - BYSETPOS: 1-366 or -366 to -1
                - WKST: SU,MO,TU,WE,TH,FR,SA (week start)
                
                Supported EXDATE format:
                - EXDATE:YYYYMMDDTHHMMSSZ (UTC timezone)
                - EXDATE:YYYYMMDDTHHMMSS (floating/local time)
                - EXDATE:YYYYMMDD (date only for all-day events)
                - Multiple dates: Use separate EXDATE entries (not comma-separated)
                Note: TZID parameter not supported in this implementation
        sendUpdates (Optional[str]): Whether to send updates about the patch.
            Possible values: "all", "externalOnly", "none". Defaults to None.

    Returns:
        Dict[str, Any]: The patched event containing:
            - id (str): The identifier of the event.
            - summary (str): The summary of the event.
            - description (str): The description of the event.
            - start (Optional[Dict[str, Any]]): The start time of the event.
                - date (Optional[str]): The date of the start time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
            - end (Optional[Dict[str, Any]]): The end time of the event.
                - date (Optional[str]): The date of the end time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
            - attendees (Optional[List[Dict[str, Any]]]): List of event attendees containing:
                - email (Optional[str]): The attendee's email address.
                - displayName (Optional[str]): The attendee's name.
                - organizer (Optional[bool]): Whether the attendee is the organizer.
                - self (Optional[bool]): Whether this represents the calendar owner.
                - resource (Optional[bool]): Whether the attendee is a resource.
                - optional (Optional[bool]): Whether this is an optional attendee.
                - responseStatus (Optional[str]): Response status.
                - comment (Optional[str]): The attendee's comment.
                - additionalGuests (Optional[int]): Number of additional guests.
            - location (Optional[str]): The location of the event.
            - recurrence (Optional[List[str]]): The recurrence rules of the event.
            - reminders (Optional[Dict[str, Any]]): The reminders of the event containing:
                - useDefault (Optional[bool]): Whether default calendar reminders are used.
                - overrides (Optional[List[Dict[str, Any]]]): Custom reminder overrides.

    Raises:
        TypeError: In the following cases:
            - If `eventId` is not a string.
            - If `calendarId` is not a string.
            - If `sendUpdates` is not a string or None.
        InvalidInputError: In the following cases:
            - If `eventId` is empty or whitespace.
            - If `calendarId` is empty or whitespace.
            - If `sendUpdates` has an invalid value (not "all", "externalOnly", or "none").
            - If 'resource' does not conform to the expected structure.
        ValueError: If the event is not found in the calendar.
    """    
    # --- Input Validation ---
    # Validate eventId (required parameter first)
    if not isinstance(eventId, str):
        raise TypeError("eventId must be a string.")
    if not eventId.strip():
        raise InvalidInputError("eventId cannot be empty or whitespace.")

    # Validate calendarId (required parameter)
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string.")
    if not calendarId.strip():
        raise InvalidInputError("calendarId cannot be empty or whitespace.")

    # Validate sendUpdates
    if sendUpdates is not None:
        if not isinstance(sendUpdates, str):
            raise TypeError("sendUpdates must be a string or None.")
        if sendUpdates not in ["all", "externalOnly", "none"]:
            raise InvalidInputError("sendUpdates must be one of: all, externalOnly, none")

    # --- Core Logic ---
    if calendarId == "primary":
        calendarId = get_primary_calendar_entry()["id"]

    if calendarId not in DB["calendar_list"]:
        raise ResourceNotFoundError(f"Calendar '{calendarId}' not found.")

    # Validate resource is a dictionary
    if resource is not None:
        if not isinstance(resource, dict):
            raise ValueError("Resource must be a dictionary")

    # Check if event exists in the specified calendar
    key = f'{calendarId}:{eventId}'
    if key not in DB["events"]:
        raise ValueError(f"Event '{eventId}' not found in calendar '{calendarId}'.")
    
    # Get the existing event
    existing = copy.deepcopy(DB["events"][key])
    
    # FIX #1: For PATCH, merge start/end with existing BEFORE Pydantic validation
    validated_resource_data: Dict[str, Any] = {}
    if resource is not None:
        resource_to_validate = resource.copy()
        if 'start' in resource and isinstance(resource['start'], dict):
            merged_start = existing.get('start', {}).copy()
            # Clear opposite field when switching date<->dateTime
            if 'date' in resource['start']:
                merged_start['dateTime'] = None
            if 'dateTime' in resource['start']:
                merged_start['date'] = None
            merged_start.update(resource['start'])
            resource_to_validate['start'] = merged_start
        if 'end' in resource and isinstance(resource['end'], dict):
            merged_end = existing.get('end', {}).copy()
            # Clear opposite field when switching date<->dateTime
            if 'date' in resource['end']:
                merged_end['dateTime'] = None
            if 'dateTime' in resource['end']:
                merged_end['date'] = None
            merged_end.update(resource['end'])
            resource_to_validate['end'] = merged_end
        
        try:
            validated_resource_model = EventPatchResourceModel(**resource_to_validate)
            validated_resource_data = validated_resource_model.model_dump(exclude_unset=True)
        except Exception as e:
            raise InvalidInputError(str(e))
    
    # Use validated_resource_data which contains only the valid fields from the input resource
    for k, v in validated_resource_data.items():
        if k in ['start', 'end'] and isinstance(v, dict) and isinstance(existing.get(k), dict):
            existing[k].update(v)  # Deep merge for start/end using .update()
        else:
            existing[k] = v
    
    if (existing.get("start", {}).get("dateTime") and not existing.get("end", {}).get("dateTime")) or (not existing.get("start", {}).get("dateTime") and existing.get("end", {}).get("dateTime")) or (existing.get("start", {}).get("date") and not existing.get("end", {}).get("date")) or (not existing.get("start", {}).get("date") and existing.get("end", {}).get("date")):
        raise InvalidInputError("Start and end times must either both be date or both be dateTime.")
    
    # Convert to UTC and save the updated event back to the database
    existing_to_DB = existing.copy()
    if "start" in validated_resource_data and "dateTime" in existing_to_DB.get("start", {}) and existing_to_DB["start"]["dateTime"]:
        existing_to_DB["start"] = local_to_UTC(existing_to_DB["start"])
    if "end" in validated_resource_data and "dateTime" in existing_to_DB.get("end", {}) and existing_to_DB["end"]["dateTime"]:
        existing_to_DB["end"] = local_to_UTC(existing_to_DB["end"])
    
    if existing_to_DB.get("start", {}).get("dateTime") and existing_to_DB.get("end", {}).get("dateTime"):
        start_dt = parse_iso_datetime(existing_to_DB.get("start", {}).get("dateTime"))
        end_dt = parse_iso_datetime(existing_to_DB.get("end", {}).get("dateTime"))
        if start_dt > end_dt:
            raise InvalidInputError("Start time must be before end time.")
    if existing_to_DB.get("start", {}).get("date") and existing_to_DB.get("end", {}).get("date"):
        start_dt = parse_iso_datetime(existing_to_DB.get("start", {}).get("date"))
        end_dt = parse_iso_datetime(existing_to_DB.get("end", {}).get("date"))
        if start_dt > end_dt:
            raise InvalidInputError("Start time must be before end time.")

    DB["events"][key] = existing_to_DB

    # Return the updated event with local timezone
    existing_to_return = existing_to_DB.copy()
    if "start" in existing_to_return and "dateTime" in existing_to_return["start"] and existing_to_return["start"]["dateTime"] and existing_to_return["start"]["dateTime"]:
        existing_to_return["start"] = UTC_to_local(existing_to_return["start"])
    if "end" in existing_to_return and "dateTime" in existing_to_return["end"] and existing_to_return["end"]["dateTime"] and existing_to_return["end"]["dateTime"]:
        existing_to_return["end"] = UTC_to_local(existing_to_return["end"])

    try:
        notify_attendees(calendarId, existing, sendUpdates, subject_prefix="Updated")
    except Exception:
        pass

    return existing_to_return


@tool_spec(
    spec={
        'name': 'quick_add_event',
        'description': 'Creates an event based on a simple text string.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar.'
                },
                'text': {
                    'type': 'string',
                    'description': """ The text to parse into an event. This should be a natural language
                    description of the event, such as "Lunch with John at noon tomorrow". """
                },
                'sendUpdates': {
                    'type': 'string',
                    'description': """ Whether to send updates about the creation.
                    Possible values: "all", "externalOnly", "none". Defaults to None. """
                }
            },
            'required': [
                'calendarId',
                'text'
            ]
        }
    }
)
def quick_add_event(
    calendarId: str,
    text: str,
    sendUpdates: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates an event based on a simple text string.

    Args:
        calendarId (str): The identifier of the calendar.
        text (str): The text to parse into an event. This should be a natural language
            description of the event, such as "Lunch with John at noon tomorrow".
        sendUpdates (Optional[str]): Whether to send updates about the creation.
            Possible values: "all", "externalOnly", "none". Defaults to None.

    Returns:
        Dict[str, Any]: The created event.
            - id (str): The identifier of the event.
            - summary (str): The summary of the event. The text provided in the 'text' parameter.
            - description (str): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - dateTime (str): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM format.
            - end (Dict[str, Any]): The end time of the event.
                - dateTime (str): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SS+/-HH:MM format.

    Raises:
        TypeError: If any argument has an invalid type:
            - calendarId is not str
            - sendUpdates is not str (if provided)
            - text is not str
        InvalidInputError: If any argument has an invalid value:
            - calendarId is empty/whitespace
            - text is empty/whitespace
            - sendUpdates has invalid value (not one of: "all", "externalOnly", "none")
        ResourceNotFoundError: If 'calendarId' does not exist in the database or if "primary" is specified but no primary calendar is found.
    """
    # Type validations
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string.")
    if sendUpdates is not None and not isinstance(sendUpdates, str):
        raise TypeError("sendUpdates must be a string if provided.")
    if text is not None and not isinstance(text, str):
        raise TypeError("text must be a string if provided.")

    # Value validations
    if not calendarId.strip():
        raise InvalidInputError("calendarId cannot be empty or whitespace.")
    if not text or not text.strip():
        raise InvalidInputError("text parameter is required and cannot be empty or whitespace.")
    if sendUpdates is not None:
        valid_send_updates = ["all", "externalOnly", "none"]
        if sendUpdates not in valid_send_updates:
            raise InvalidInputError(f"sendUpdates must be one of: {', '.join(valid_send_updates)}")

    # Validation is being performed inside the get_calendar function
    calendar = get_calendar(calendarId)
    validated_calendar_id = calendar["id"]

    # Create event
    ev_id = str(uuid.uuid4())
    resource = {"id": ev_id, "summary": text}
    DB["events"][f'{validated_calendar_id}:{ev_id}'] = resource

    try:
        notify_attendees(validated_calendar_id, resource, sendUpdates, subject_prefix="Invitation")
    except Exception:
        # Non-fatal in simulation
        pass
    return resource

@tool_spec(
    spec={
        'name': 'update_event',
        'description': 'Replaces an existing event with new data.',
        'parameters': {
            'type': 'object',
            'properties': {
                'eventId': {
                    'type': 'string',
                    'description': 'The identifier of the event to update.'
                },
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar. Defaults to "primary".'
                },
                'resource': {
                    'type': 'object',
                    'description': 'The event to update. Must contain:',
                    'properties': {
                        'summary': {
                            'type': 'string',
                            'description': 'The summary/title of the event.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the event.'
                        },
                        'start': {
                            'type': 'object',
                            'description': 'The start time of the event.',
                            'properties': {
                                'date': {
                                    'type': 'string',
                                    'description': 'The date of the start time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS format. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'timeZone': {
                                    'type': 'string',
                                    'description': 'The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.'
                                }
                            },
                            'required': [
                            ]
                        },
                        'end': {
                            'type': 'object',
                            'description': 'The end time of the event.',
                            'properties': {
                                'date': {
                                    'type': 'string',
                                    'description': 'The date of the end time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'dateTime': {
                                    'type': 'string',
                                    'description': 'The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS format. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone should be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.'
                                },
                                'timeZone': {
                                    'type': 'string',
                                    'description': 'The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.'
                                }
                            },
                            'required': [
                            ]
                        },
                        'recurrence': {
                            'type': 'array',
                            'description': """ The recurrence rules of the event in RRULE format and exception dates in EXDATE format.
                                 Examples:
                                - Daily for 5 occurrences: ["RRULE:FREQ=DAILY;COUNT=5"]
                                - Weekly on Monday and Wednesday: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
                                - Monthly on the 15th: ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
                                - Yearly on January 1st: ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"]
                                - Every 2 weeks: ["RRULE:FREQ=WEEKLY;INTERVAL=2"]
                                - Until a specific date: ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
                                - With exception dates: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225T120000Z", "EXDATE:20250101T120000Z"]
                                - Multiple exception dates: ["RRULE:FREQ=DAILY;COUNT=10", "EXDATE:20241225T120000Z", "EXDATE:20241226T120000Z"]
                                Supported RRULE parameters:
                                - FREQ: SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY (required)
                                - INTERVAL: Positive integer (default: 1)
                                - COUNT: Positive integer (number of occurrences)
                                - UNTIL: YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS format
                                - BYDAY: SU,MO,TU,WE,TH,FR,SA (with optional ordinal: 1SU, -1MO)
                                - BYMONTH: 1-12
                                - BYMONTHDAY: 1-31
                                - BYYEARDAY: 1-366
                                - BYWEEKNO: 1-53
                                - BYHOUR: 0-23
                                - BYMINUTE: 0-59
                                - BYSECOND: 0-59
                                - BYSETPOS: 1-366 or -366 to -1
                                - WKST: SU,MO,TU,WE,TH,FR,SA (week start)
                                Supported EXDATE format:
                                - EXDATE:YYYYMMDDTHHMMSSZ (UTC timezone)
                                - EXDATE:YYYYMMDDTHHMMSS (floating/local time)
                                - EXDATE:YYYYMMDD (date only for all-day events)
                                - Multiple dates: Use separate EXDATE entries (not comma-separated)
                                Note: TZID parameter not supported in this implementation """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'attendees': {
                            'type': 'array',
                            'description': 'List of event attendees. Each attendee can have:',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'email': {
                                        'type': 'string',
                                        'description': "The attendee's email address"
                                    },
                                    'displayName': {
                                        'type': 'string',
                                        'description': "The attendee's display name"
                                    },
                                    'organizer': {
                                        'type': 'boolean',
                                        'description': 'Whether the attendee is the organizer'
                                    },
                                    'self': {
                                        'type': 'boolean',
                                        'description': 'Whether the attendee is the user'
                                    },
                                    'resource': {
                                        'type': 'boolean',
                                        'description': 'Whether the attendee is a resource'
                                    },
                                    'optional': {
                                        'type': 'boolean',
                                        'description': "Whether the attendee's presence is optional"
                                    },
                                    'responseStatus': {
                                        'type': 'string',
                                        'description': "The attendee's response status"
                                    },
                                    'comment': {
                                        'type': 'string',
                                        'description': "The attendee's comment"
                                    },
                                    'additionalGuests': {
                                        'type': 'integer',
                                        'description': 'Number of additional guests'
                                    }
                                },
                                'required': []
                            }
                        },
                        'reminders': {
                            'type': 'object',
                            'description': 'The reminders of the event.',
                            'properties': {
                                'useDefault': {
                                    'type': 'boolean',
                                    'description': 'Whether to use the default reminders.'
                                },
                                'overrides': {
                                    'type': 'array',
                                    'description': 'The list of overrides.',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'method': {
                                                'type': 'string',
                                                'description': 'The method of the reminder.'
                                            },
                                            'minutes': {
                                                'type': 'integer',
                                                'description': 'The minutes of the reminder.'
                                            }
                                        },
                                        'required': []
                                    }
                                }
                            },
                            'required': []
                        },
                        'location': {
                            'type': 'string',
                            'description': 'The location of the event.'
                        }
                    },
                    'required': [
                        'start',
                        'end'
                    ]
                },
                'sendUpdates': {
                    'type': 'string',
                    'description': """ Whether to send updates about the update.
                    Possible values: "all", "externalOnly", "none". Defaults to None. """
                }
            },
            'required': [
                'eventId'
            ]
        }
    }
)
def update_event(eventId: str, calendarId: str = "primary", resource: Optional[Dict[str, Any]] = None, sendUpdates: Optional[str] = None) -> Dict[str, Any]:
    """
    Replaces an existing event with new data.

    Args:
        eventId (str): The identifier of the event to update.
        calendarId (str): The identifier of the calendar. Defaults to "primary".
        resource (Optional[Dict[str, Any]]): The event to update. Must contain:
            - summary (Optional[str]): The summary/title of the event.
            - description (Optional[str]): The description of the event.
            - start (Dict[str, Any]): The start time of the event.
                - date (Optional[str]): The date of the start time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - dateTime (Optional[str]): The date and time of the start time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS format. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone MUST be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). The timeZone is required if the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS). Defaults to None.
            - end (Dict[str, Any]): The end time of the event.
                - date (Optional[str]): The date of the end time in format YYYY-MM-DD. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - dateTime (Optional[str]): The date and time of the end time in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS format. If the dateTime string does not contain timezone information (YYYY-MM-DDTHH:MM:SS), then timeZone MUST be provided. If dateTime contains timezone information (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+/-HH:MM), then timeZone is ignored. An event must have either date or dateTime field and cannot have both at the same time. Default to None.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). REQUIRED when dateTime is provided without timezone information (YYYY-MM-DDTHH:MM:SS format). Defaults to None.
            - recurrence (Optional[List[str]]): The recurrence rules of the event in RRULE format and exception dates in EXDATE format.
                Examples:
                - Daily for 5 occurrences: ["RRULE:FREQ=DAILY;COUNT=5"]
                - Weekly on Monday and Wednesday: ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
                - Monthly on the 15th: ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
                - Yearly on January 1st: ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"]
                - Every 2 weeks: ["RRULE:FREQ=WEEKLY;INTERVAL=2"]
                - Until a specific date: ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
                - With exception dates: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225T120000Z", "EXDATE:20250101T120000Z"]
                - Multiple exception dates: ["RRULE:FREQ=DAILY;COUNT=10", "EXDATE:20241225T120000Z", "EXDATE:20241226T120000Z"]
                - All-day event exceptions: ["RRULE:FREQ=WEEKLY;BYDAY=MO", "EXDATE:20241225", "EXDATE:20250101"]
                
                Supported RRULE parameters:
                - FREQ: SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY (required)
                - INTERVAL: Positive integer (default: 1)
                - COUNT: Positive integer (number of occurrences)
                - UNTIL: YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS format
                - BYDAY: SU,MO,TU,WE,TH,FR,SA (with optional ordinal: 1SU, -1MO)
                - BYMONTH: 1-12
                - BYMONTHDAY: 1-31
                - BYYEARDAY: 1-366
                - BYWEEKNO: 1-53
                - BYHOUR: 0-23
                - BYMINUTE: 0-59
                - BYSECOND: 0-59
                - BYSETPOS: 1-366 or -366 to -1
                - WKST: SU,MO,TU,WE,TH,FR,SA (week start)
                
                Supported EXDATE format:
                - EXDATE:YYYYMMDDTHHMMSSZ (UTC timezone)
                - EXDATE:YYYYMMDDTHHMMSS (floating/local time)
                - EXDATE:YYYYMMDD (date only for all-day events)
                - Multiple dates: Use separate EXDATE entries (not comma-separated)
                Note: TZID parameter not supported in this implementation
                
            - attendees (Optional[List[Dict[str, Any]]]): List of event attendees. Each attendee can have:
                - email (Optional[str]): The attendee's email address
                - displayName (Optional[str]): The attendee's display name
                - organizer (Optional[bool]): Whether the attendee is the organizer
                - self (Optional[bool]): Whether the attendee is the user
                - resource (Optional[bool]): Whether the attendee is a resource
                - optional (Optional[bool]): Whether the attendee's presence is optional
                - responseStatus (Optional[str]): The attendee's response status
                - comment (Optional[str]): The attendee's comment
                - additionalGuests (Optional[int]): Number of additional guests
            - reminders (Optional[Dict[str, Any]]): The reminders of the event.
                - useDefault (Optional[bool]): Whether to use the default reminders.
                - overrides (Optional[List[Dict[str, Any]]]): The list of overrides.
                    - method (Optional[str]): The method of the reminder.
                    - minutes (Optional[int]): The minutes of the reminder.
            - location (Optional[str]): The location of the event.
        sendUpdates (Optional[str]): Whether to send updates about the update.
            Possible values: "all", "externalOnly", "none". Defaults to None. 

    Returns:
        Dict[str, Any]: The updated event.
            - id (str): The identifier of the event.
            - summary (Optional[str]): The summary of the event.
            - description (Optional[str]): The description of the event.
            - start (Optional[Dict[str, Any]]): The start time of the event.
                - date (Optional[str]): The date of the start time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time in YYYY-MM-DDTHH:MM:SS+/-HH:MM format. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the start time in IANA format (e.g., "America/New_York"). Defaults to None.
            - end (Optional[Dict[str, Any]]): The end time of the event.
                - date (Optional[str]): The date of the end time in format YYYY-MM-DD. Either date or dateTime are provided. Default to None.
                - dateTime (Optional[str]): The date and time in YYYY-MM-DDTHH:MM:SS+/-HH:MM format. Either date or dateTime are provided. Default to None.
                - timeZone (Optional[str]): The time zone of the end time in IANA format (e.g., "America/New_York"). Defaults to None.
            - attendees (Optional[List[Dict[str, Any]]]): List of event attendees with their details.
            - recurrence (Optional[List[str]]): The recurrence rules of the event in RRULE format.
            - reminders (Optional[Dict[str, Any]]): The reminders of the event.
            - location (Optional[str]): The location of the event.

    Raises:
        TypeError: If calendarId or eventId is provided and not a string, or sendUpdates is not a string (if provided).
        InvalidInputError: If eventId is None, calendarId is empty/whitespace, eventId is empty/whitespace,
            resource is not provided, resource data does not match the expected structure,
            or sendUpdates has an invalid value (not one of: "all", "externalOnly", "none").
            This includes validation errors for recurrence rules and start/end time validation:
            - When updating an event, both start and end times must be provided if either is provided
            - Start and end times must use the same format (both date or both dateTime)
            - If dateTime is provided without timezone information (YYYY-MM-DDTHH:MM:SS format), timeZone MUST be provided
        ResourceNotFoundError: If the event is not found in the calendar.

    Examples:
        # Update an event to be recurring
        event = update_event("event123", "primary", {
            "summary": "Updated Team Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO"]
        })
        
        # Update a recurring event to change its pattern
        event = update_event("event456", "primary", {
            "summary": "Bi-weekly Review",
            "recurrence": ["RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=FR"]
        })
        
        # Update an event with timezone (REQUIRED when dateTime has no timezone info)
        event = update_event("event789", "primary", {
            "summary": "Local Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "America/New_York"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "America/New_York"}
        })
    """
    # --- Input Validation ---
    # Validate calendarId
    if calendarId is not None:
        if not isinstance(calendarId, str):
            raise TypeError("calendarId must be a string if provided.")
        if not calendarId.strip():
            raise InvalidInputError("calendarId cannot be empty or whitespace.")

    # Validate eventId
    if eventId is None:
        raise InvalidInputError("eventId is required for updating an event.")
    if not isinstance(eventId, str):
        raise TypeError("eventId must be a string if provided.")
    if not eventId.strip():
        raise InvalidInputError("eventId cannot be empty or whitespace.")

    # Validate sendUpdates
    if sendUpdates is not None:
        if not isinstance(sendUpdates, str):
            raise TypeError("sendUpdates must be a string if provided.")
        valid_send_updates = ["all", "externalOnly", "none"]
        if sendUpdates not in valid_send_updates:
            raise InvalidInputError(f"sendUpdates must be one of: {', '.join(valid_send_updates)}")

    # Default calendarId if None
    effective_calendarId = calendarId if calendarId is not None else "primary"
    if effective_calendarId == "primary":
        effective_calendarId = get_primary_calendar_entry()["id"]

    # Validate resource
    if resource is None:
        raise InvalidInputError("Resource body is required for full update.")

    # Validate resource structure using Pydantic model
    # This includes validation of recurrence rules through the field validator
    try:
        validated_resource_model = EventResourceInputModel(**resource)
        # Convert back to dict, excluding unset fields
        validated_resource = validated_resource_model.model_dump(exclude_unset=True)
        # Validate start and end times
        validate_start_end_times(validated_resource, "updating")
    except Exception as e:
        raise InvalidInputError(str(e))

    # Check if event exists
    key = f'{effective_calendarId}:{eventId}'
    if key not in DB["events"]:
        raise ResourceNotFoundError(f"Event '{eventId}' not found in calendar '{effective_calendarId}'.")

    # Update with validated data
    validated_resource["id"] = eventId

    # Convert to UTC and save the updated event to the database
    validated_resource_to_DB = validated_resource.copy()
    if "start" in validated_resource_to_DB and "start" in validated_resource:
        # Only convert to UTC if it's a dateTime event (not all-day)
        if "dateTime" in validated_resource_to_DB["start"] and validated_resource_to_DB["start"]["dateTime"]:
            validated_resource_to_DB["start"] = local_to_UTC(validated_resource_to_DB["start"])
    if "end" in validated_resource_to_DB and "end" in validated_resource:
        # Only convert to UTC if it's a dateTime event (not all-day)
        if "dateTime" in validated_resource_to_DB["end"] and validated_resource_to_DB["end"]["dateTime"]:
            validated_resource_to_DB["end"] = local_to_UTC(validated_resource_to_DB["end"])
    DB["events"][key] = validated_resource_to_DB

    # Convert to local and return the updated event
    validated_resource_to_return = validated_resource_to_DB.copy()
    if "start" in validated_resource_to_return:
        # Only convert to local if it's a dateTime event (not all-day)
        if "dateTime" in validated_resource_to_return["start"] and validated_resource_to_return["start"]["dateTime"]:
            validated_resource_to_return["start"] = UTC_to_local(validated_resource_to_return["start"])
    if "end" in validated_resource_to_return:
        # Only convert to local if it's a dateTime event (not all-day)
        if "dateTime" in validated_resource_to_return["end"] and validated_resource_to_return["end"]["dateTime"]:
            validated_resource_to_return["end"] = UTC_to_local(validated_resource_to_return["end"])
    
    try:
        notify_attendees(effective_calendarId, validated_resource_to_return, sendUpdates, subject_prefix="Updated")
    except Exception:
        pass
    return validated_resource_to_return

@tool_spec(
    spec={
        'name': 'watch_event_changes',
        'description': 'Sets up a watch for changes to events in the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The identifier of the calendar. Defaults to "primary".'
                },
                'alwaysIncludeEmail': {
                    'type': 'boolean',
                    'description': """ Whether to always include the email address
                    of the event creator. Defaults to False. """
                },
                'eventTypes': {
                    'type': 'array',
                    'description': """ The types of events to watch for.
                    Must be one or more of: "default", "focusTime", "outOfOffice". """,
                    'items': {
                        'type': 'string'
                    }
                },
                'iCalUID': {
                    'type': 'string',
                    'description': 'The iCalUID of the event to filter by.'
                },
                'maxAttendees': {
                    'type': 'integer',
                    'description': """ The maximum number of attendees to return per event.
                    Must be a positive integer if provided. """
                },
                'maxResults': {
                    'type': 'integer',
                    'description': """ The maximum number of events to return.
                    Must be a positive integer. Defaults to 250. """
                },
                'orderBy': {
                    'type': 'string',
                    'description': """ The order of the events.
                    Must be one of: "startTime", "updated". """
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'Token specifying which result page to return.'
                },
                'privateExtendedProperty': {
                    'type': 'array',
                    'description': """ Private extended property filters
                    in the form "key=value". """,
                    'items': {
                        'type': 'string'
                    }
                },
                'q': {
                    'type': 'string',
                    'description': 'Free text search terms to find events that match.'
                },
                'sharedExtendedProperty': {
                    'type': 'array',
                    'description': """ Shared extended property filters
                    in the form "key=value". """,
                    'items': {
                        'type': 'string'
                    }
                },
                'showDeleted': {
                    'type': 'boolean',
                    'description': """ Whether to include deleted events.
                    Defaults to False. """
                },
                'showHiddenInvitations': {
                    'type': 'boolean',
                    'description': """ Whether to include hidden invitations.
                    Defaults to False. """
                },
                'singleEvents': {
                    'type': 'boolean',
                    'description': """ Whether to expand recurring events into instances.
                    Defaults to False. """
                },
                'syncToken': {
                    'type': 'string',
                    'description': """ Token obtained from the nextSyncToken field returned on the
                    last page of results from the previous list request. """
                },
                'timeMax': {
                    'type': 'string',
                    'description': """ Upper bound (exclusive) for an event's start time in
                    ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). """
                },
                'timeMin': {
                    'type': 'string',
                    'description': """ Lower bound (inclusive) for an event's end time in
                    ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). """
                },
                'timeZone': {
                    'type': 'string',
                    'description': """ Time zone used in the response (e.g. "America/New_York").
                    The default is the calendar's time zone. """
                },
                'updatedMin': {
                    'type': 'string',
                    'description': """ Lower bound for an event's last modification time in
                    ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). """
                },
                'resource': {
                    'type': 'object',
                    'description': 'The watch configuration:',
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': """ The identifier of the watch. If not provided,
                                 a new UUID will be generated. """
                        },
                        'type': {
                            'type': 'string',
                            'description': 'The type of the watch. Defaults to "web_hook".'
                        },
                        'address': {
                            'type': 'string',
                            'description': 'The address to send notifications to.'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def watch_events(
    calendarId: str = "primary",
    alwaysIncludeEmail: Optional[bool] = False,
    eventTypes: Optional[List[str]] = None,
    iCalUID: Optional[str] = None,
    maxAttendees: Optional[int] = None,
    maxResults: Optional[int] = 250,
    orderBy: Optional[str] = None,
    pageToken: Optional[str] = None,
    privateExtendedProperty: Optional[List[str]] = None,
    q: Optional[str] = None,
    sharedExtendedProperty: Optional[List[str]] = None,
    showDeleted: Optional[bool] = False,
    showHiddenInvitations: Optional[bool] = False,
    singleEvents: Optional[bool] = False,
    syncToken: Optional[str] = None,
    timeMax: Optional[str] = None,
    timeMin: Optional[str] = None,
    timeZone: Optional[str] = None,
    updatedMin: Optional[str] = None,
    resource: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Sets up a watch for changes to events in the specified calendar.

    Args:
        calendarId (str): The identifier of the calendar. Defaults to "primary".
        alwaysIncludeEmail (Optional[bool]): Whether to always include the email address
            of the event creator. Defaults to False.
        eventTypes (Optional[List[str]]): The types of events to watch for.
            Must be one or more of: "default", "focusTime", "outOfOffice".
        iCalUID (Optional[str]): The iCalUID of the event to filter by.
        maxAttendees (Optional[int]): The maximum number of attendees to return per event.
            Must be a positive integer if provided.
        maxResults (Optional[int]): The maximum number of events to return.
            Must be a positive integer. Defaults to 250.
        orderBy (Optional[str]): The order of the events.
            Must be one of: "startTime", "updated".
        pageToken (Optional[str]): Token specifying which result page to return.
        privateExtendedProperty (Optional[List[str]]): Private extended property filters
            in the form "key=value".
        q (Optional[str]): Free text search terms to find events that match.
        sharedExtendedProperty (Optional[List[str]]): Shared extended property filters
            in the form "key=value".
        showDeleted (Optional[bool]): Whether to include deleted events.
            Defaults to False.
        showHiddenInvitations (Optional[bool]): Whether to include hidden invitations.
            Defaults to False.
        singleEvents (Optional[bool]): Whether to expand recurring events into instances.
            Defaults to False.
        syncToken (Optional[str]): Token obtained from the nextSyncToken field returned on the
            last page of results from the previous list request.
        timeMax (Optional[str]): Upper bound (exclusive) for an event's start time in
            RFC 3339 format YYYY-MM-DDTHH:MM:SSZ.
        timeMin (Optional[str]): Lower bound (inclusive) for an event's end time in
            RFC 3339 format YYYY-MM-DDTHH:MM:SSZ.
        timeZone (Optional[str]): Time zone used in the response (e.g. "America/New_York").
            The default is the calendar's time zone.
        updatedMin (Optional[str]): Lower bound for an event's last modification time in
            RFC 3339 format YYYY-MM-DDTHH:MM:SSZ.
        resource (Optional[Dict[str, Any]]): The watch configuration:
            - id (Optional[str]): The identifier of the watch. If not provided,
                a new UUID will be generated.
            - type (Optional[str]): The type of the watch. Defaults to "web_hook".
            - address (Optional[str]): The address to send notifications to.

    Returns:
        Dict[str, Any]: The created watch channel:
            - id (str): The identifier of the watch channel.
            - type (str): The type of the watch.
            - calendarId (str): The identifier of the watched calendar.
            - resource (str): The resource being watched.

    Raises:
        TypeError: If any argument has an invalid type:
            - Boolean parameters are not bool
            - String parameters are not str
            - List parameters are not list
            - Integer parameters are not int
            - resource is not a dict
        InvalidInputError: If any argument has an invalid value:
            - maxResults or maxAttendees is not positive
            - eventTypes contains invalid event type
            - orderBy has invalid value
            - timeMax, timeMin, or updatedMin has invalid format
            - timeZone has invalid format
            - resource is missing required 'address' field
            - resource has invalid 'type' value
    """
    # --- Type validations ---
    # Boolean parameters
    if not isinstance(alwaysIncludeEmail, bool):
        raise TypeError("alwaysIncludeEmail must be a boolean.")
    if not isinstance(showDeleted, bool):
        raise TypeError("showDeleted must be a boolean.")
    if not isinstance(showHiddenInvitations, bool):
        raise TypeError("showHiddenInvitations must be a boolean.")
    if not isinstance(singleEvents, bool):
        raise TypeError("singleEvents must be a boolean.")

    # String parameters
    if calendarId is not None and not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string if provided.")
    if iCalUID is not None and not isinstance(iCalUID, str):
        raise TypeError("iCalUID must be a string if provided.")
    if orderBy is not None and not isinstance(orderBy, str):
        raise TypeError("orderBy must be a string if provided.")
    if pageToken is not None and not isinstance(pageToken, str):
        raise TypeError("pageToken must be a string if provided.")
    if q is not None and not isinstance(q, str):
        raise TypeError("q must be a string if provided.")
    if syncToken is not None and not isinstance(syncToken, str):
        raise TypeError("syncToken must be a string if provided.")
    if timeMax is not None and not isinstance(timeMax, str):
        raise TypeError("timeMax must be a string if provided.")
    if timeMin is not None and not isinstance(timeMin, str):
        raise TypeError("timeMin must be a string if provided.")
    if timeZone is not None and not isinstance(timeZone, str):
        raise TypeError("timeZone must be a string if provided.")
    if updatedMin is not None and not isinstance(updatedMin, str):
        raise TypeError("updatedMin must be a string if provided.")

    # Integer parameters
    if maxAttendees is not None and not isinstance(maxAttendees, int):
        raise TypeError("maxAttendees must be an integer if provided.")
    if not isinstance(maxResults, int):
        raise TypeError("maxResults must be an integer.")

    # List parameters
    if eventTypes is not None and not isinstance(eventTypes, list):
        raise TypeError("eventTypes must be a list if provided.")
    if privateExtendedProperty is not None and not isinstance(
        privateExtendedProperty, list
    ):
        raise TypeError("privateExtendedProperty must be a list if provided.")
    if sharedExtendedProperty is not None and not isinstance(
        sharedExtendedProperty, list
    ):
        raise TypeError("sharedExtendedProperty must be a list if provided.")

    # Resource parameter
    if resource is not None and not isinstance(resource, dict):
        raise TypeError("resource must be a dictionary.")

    # --- Value validations ---
    # Numeric value validations
    if maxAttendees is not None and maxAttendees <= 0:
        raise InvalidInputError("maxAttendees must be a positive integer.")
    if maxResults <= 0:
        raise InvalidInputError("maxResults must be a positive integer.")

    # Event types validation
    valid_event_types = {"default", "focusTime", "outOfOffice"}
    if eventTypes is not None:
        invalid_types = [t for t in eventTypes if t not in valid_event_types]
        if invalid_types:
            raise InvalidInputError(
                f"Invalid event types: {', '.join(invalid_types)}. "
                f"Must be one of: {', '.join(valid_event_types)}"
            )

    # Order by validation
    valid_order_by = {"startTime", "updated"}
    if orderBy is not None and orderBy not in valid_order_by:
        raise InvalidInputError(
            f"Invalid orderBy value: {orderBy}. Must be one of: {', '.join(valid_order_by)}"
        )

    # Time format validations
    for time_param, time_value in [
        ("timeMax", timeMax),
        ("timeMin", timeMin),
        ("updatedMin", updatedMin),
    ]:
        if time_value is not None:
            if not is_datetime_of_format(time_value, "YYYY-MM-DDTHH:MM:SSZ") and not is_datetime_of_format(time_value, "YYYY-MM-DDTHH:MM:SS+/-HH:MM") and not is_datetime_of_format(time_value, "YYYY-MM-DDTHH:MM:SS"):
                raise InvalidInputError(
                    f"Invalid {time_param} format: Must be in RFC 3339 format YYYY-MM-DDTHH:MM:SSZ, YYYY-MM-DDTHH:MM:SS+/-HH:MM, or YYYY-MM-DDTHH:MM:SS."
                )

    # Timezone validation
    if timeZone is not None:
        if not timeZone.strip():
            raise InvalidInputError("timeZone cannot be empty or whitespace.")
        # Basic timezone format validation
        if "/" not in timeZone:
            raise InvalidInputError(
                "timeZone must be in format 'Continent/City' (e.g., 'America/New_York')."
            )

    # Resource validation
    if resource is None:
        raise InvalidInputError("Channel resource is required to watch.")

    # Set default calendar ID if not provided
    effective_calendarId = calendarId if calendarId is not None else "primary"

    # Create and store channel
    channel_id = resource.get("id") or str(uuid.uuid4())
    DB["channels"][channel_id] = {
        "id": channel_id,
        "type": resource.get("type", "web_hook"),
        "resource": "events",
        "calendarId": effective_calendarId,
    }
    return DB["channels"][channel_id]
