from common_utils.tool_spec_decorator import tool_spec
# APIs/google_calendar/CalendarsResource/__init__.py
import uuid
from typing import Dict, Any, Optional, List

from pydantic import ValidationError

from .SimulationEngine.custom_errors import ResourceNotFoundError, InvalidInputError
from .SimulationEngine.models import CalendarResourceInputModel, UpdateCalendarInputResourceModel
from .SimulationEngine.db import DB
from .SimulationEngine.utils import get_primary_calendar_entry

@tool_spec(
    spec={
        'name': 'clear_primary_calendar',
        'description': 'Clears a primary calendar. This operation deletes all events associated with the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': """ The identifier of the calendar.
                    - To retrieve calendar IDs, call the `calendarList.list` method.
                    - Use the keyword "primary" to access the primary calendar of the currently logged-in user. """
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def clear_calendar(calendarId: str) -> Dict[str, Any]:
    """
    Clears a primary calendar. This operation deletes all events associated with the specified calendar.

    Args:
        calendarId (str): The identifier of the calendar.
            - To retrieve calendar IDs, call the `calendarList.list` method.
            - Use the keyword "primary" to access the primary calendar of the currently logged-in user.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether the operation was successful.
            - message (str): A message describing the result of the operation.
    """
    if not isinstance(calendarId, str):
        raise TypeError(f"CalendarId must be a string: {calendarId}")

    if calendarId == "primary":
        calendarId = get_primary_calendar_entry()["id"]

    if calendarId not in DB["calendar_list"]:
        raise ValueError(f"Calendar '{calendarId}' not found.")
    
    to_delete = []
    for key, ev_obj in DB["events"].items():
        cal_id, ev_id = key.split(':', 1)
        if cal_id == calendarId:
            to_delete.append(key)
    for key in to_delete:
        DB["events"].pop(key)
    return {
        "success": True,
        "message": f"All events deleted for calendar '{calendarId}'.",
    }


@tool_spec(
    spec={
        'name': 'delete_secondary_calendar',
        'description': """ Deletes a secondary calendar. This operation removes the calendar from the user's calendar list.
        
        Note: Primary calendars cannot be deleted. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': """ The identifier of the secondary calendar to delete.
                    To retrieve calendar IDs, call the `calendarList.list` method. """
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def delete_calendar(calendarId: str) -> Dict[str, Any]:
    """
    Deletes a secondary calendar. This operation removes the calendar from the user's calendar list
    and cleans up all associated data including events, ACL rules, and notification channels.
    Note: Primary calendars cannot be deleted.

    Args:
        calendarId (str): The identifier of the secondary calendar to delete.
            To retrieve calendar IDs, call the `calendarList.list` method.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether the operation was successful.
            - message (str): A message describing the result of the operation.

    Raises:
        InvalidInputError: If calendarId is not a string, is empty, or contains only whitespace.
        InvalidInputError: If attempting to delete a primary calendar.
        ResourceNotFoundError: If the calendar is not found.
    """
    if not isinstance(calendarId, str):
        raise InvalidInputError(f"CalendarId must be a string: {calendarId}")

    # Upfront validation for fundamentally invalid inputs
    if not calendarId or not calendarId.strip():
        raise InvalidInputError("CalendarId cannot be empty or contain only whitespace.")

    # Check if the calendar exists
    if calendarId not in DB["calendar_list"]:
        raise ResourceNotFoundError(f"Calendar '{calendarId}' not found.")
    
    # Handle the "primary" keyword case first
    if calendarId == "primary" or DB["calendar_list"][calendarId].get("primary"):
        raise InvalidInputError("Cannot delete the primary calendar.")

    # Now proceed with deletion
    del DB["calendar_list"][calendarId]
    if calendarId in DB["calendars"]:
        del DB["calendars"][calendarId]

    # Clean up calendar references from other tables
    
    # 1. Remove all events for this calendar
    events_to_delete = []
    for event_key in DB["events"].keys():
        if event_key.startswith(f"{calendarId}:"):
            events_to_delete.append(event_key)
    for event_key in events_to_delete:
        del DB["events"][event_key]
    
    # 2. Remove ACL rules for this calendar
    acl_rules_to_delete = []
    for rule_id, rule in DB["acl_rules"].items():
        if isinstance(rule, dict) and rule.get('calendarId') == calendarId:
            acl_rules_to_delete.append(rule_id)
    for rule_id in acl_rules_to_delete:
        del DB["acl_rules"][rule_id]
    
    # 3. Remove channels watching this calendar
    channels_to_delete = []
    for channel_id, channel in DB["channels"].items():
        if isinstance(channel, dict) and channel.get('calendarId') == calendarId:
            channels_to_delete.append(channel_id)
    for channel_id in channels_to_delete:
        del DB["channels"][channel_id]

    return {"success": True, "message": f"Calendar '{calendarId}' deleted."}


@tool_spec(
    spec={
        'name': 'get_calendar_metadata',
        'description': 'Retrieves metadata for a specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': """ The identifier of the calendar.
                    - To retrieve calendar IDs, call the `calendarList.list` method.
                    - Use the keyword "primary" to access the primary calendar of the currently logged-in user. """
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def get_calendar(calendarId: str) -> Dict[str, Any]:
    """
    Retrieves metadata for a specified calendar.

    Args:
        calendarId (str): The identifier of the calendar.
            - To retrieve calendar IDs, call the `calendarList.list` method.
            - Use the keyword "primary" to access the primary calendar of the currently logged-in user.

    Returns:
        Dict[str, Any]: A dictionary containing the calendar metadata:
            - id (str): The identifier of the calendar.
            - summary (str): The summary of the calendar.
            - description (str): The description of the calendar.
            - timeZone (str): The time zone of the calendar (e.g. "America/New_York").
            - primary (bool): Whether the calendar is the primary calendar.
    Raises:
        TypeError: If calendarId is not a string.
        InvalidInputError: If calendarId is empty or whitespace.
        ResourceNotFoundError: If the calendar is not found.
    """
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string.")
    if not calendarId:
        raise InvalidInputError("calendarId can not be empty.")
    if calendarId == "primary":
        calendarId = get_primary_calendar_entry()["id"]
    if calendarId not in DB["calendar_list"]:
        raise ResourceNotFoundError(f"Calendar '{calendarId}' not found.")
    return DB["calendar_list"][calendarId]


@tool_spec(
    spec={
        'name': 'create_secondary_calendar',
        'description': 'Creates a secondary calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'resource': {
                    'type': 'object',
                    'description': 'The resource to create the calendar with.',
                    'properties': {
                        'summary': {
                            'type': 'string',
                            'description': 'The title of the calendar.'
                        },
                        'id': {
                            'type': 'string',
                            'description': 'The identifier of the calendar. If not provided, a UUID will be generated.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the calendar.'
                        },
                        'timeZone': {
                            'type': 'string',
                            'description': 'The time zone of the calendar (e.g. "America/New_York"). Defaults to "UTC".'
                        },
                        'location': {
                            'type': 'string',
                            'description': 'Geographic location of the calendar as free-form text.'
                        },
                        'etag': {
                            'type': 'string',
                            'description': 'ETag of the resource. Used for optimistic concurrency control.'
                        },
                        'kind': {
                            'type': 'string',
                            'description': 'Type of the resource ("calendar#calendar").'
                        },
                        'conferenceProperties': {
                            'type': 'object',
                            'description': 'Conference-related properties.',
                            'properties': {
                                'allowedConferenceSolutionTypes': {
                                    'type': 'array',
                                    'description': """ List of conference solution types that are supported for this calendar.
                                             Each string in the list can be one of:
                                            - "eventHangout"
                                            - "eventNamedHangout"
                                            - "hangoutsMeet" """,
                                    'items': {
                                        'type': 'string'
                                    }
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
                        'summary'
                    ]
                }
            },
            'required': [
                'resource'
            ]
        }
    }
)
def create_calendar(resource: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a secondary calendar.

    Args:
        resource (Dict[str, Any]): The resource to create the calendar with.
            - summary (str): The title of the calendar.
            - id (Optional[str]): The identifier of the calendar. If not provided, a UUID will be generated.
            - description (Optional[str]): The description of the calendar.
            - timeZone (Optional[str]): The time zone of the calendar (e.g. "America/New_York"). Defaults to "UTC".
            - location (Optional[str]): Geographic location of the calendar as free-form text.
            - etag (Optional[str]): ETag of the resource. Used for optimistic concurrency control.
            - kind (Optional[str]): Type of the resource ("calendar#calendar").
            - conferenceProperties (Optional[Dict[str, Any]]): Conference-related properties.
                - allowedConferenceSolutionTypes (Optional[List[str]]): List of conference solution types that are supported for this calendar.
                    Each string in the list can be one of:
                    - "eventHangout"
                    - "eventNamedHangout"
                    - "hangoutsMeet"

    Returns:
        Dict[str, Any]: The created calendar.
            - id (str): The identifier of the calendar.
            - summary (str): The title of the calendar.
            - description (Optional[str]): The description of the calendar.
            - timeZone (str): The time zone of the calendar (e.g. "America/New_York").
            - location (Optional[str]): The geographic location of the calendar.
            - etag (Optional[str]): ETag of the resource.
            - kind (Optional[str]): Type of the resource ("calendar#calendar").
            - conferenceProperties (Optional[Dict[str, Any]]): Conference-related properties.
                - allowedConferenceSolutionTypes (Optional[List[str]]): List of conference solution types that are supported for this calendar.
            - primary (bool): Whether the calendar is the primary calendar.
    Raises:
        ValueError: If summary is missing or empty, or if the provided ID already exists.
        TypeError: If resource is not a dictionary.
        ValidationError: If the 'resource' dictionary does not conform to the expected validations.
    """
    # Check if resource is None (even though parameter is required, handle explicit None)
    if resource is None:
        raise ValueError("Resource is required to create a calendar.")
    
    # Check if resource is a dictionary
    if not isinstance(resource, dict):
        raise TypeError("Resource must be a dictionary.")
    
    # Check if summary is provided and not empty
    if not resource.get('summary') or not resource['summary'].strip():
        raise ValueError("Summary is required to create a calendar.")

    # Pydantic validation for the resource dictionary
    try:
        validated_resource_model = CalendarResourceInputModel(**resource)
    except ValidationError as e:
        raise e

    cal_id = validated_resource_model.id or str(uuid.uuid4())
    
    # Check for ID conflicts to prevent data integrity issues
    if validated_resource_model.id:
        # If an explicit ID was provided, check if it already exists
        if cal_id in DB["calendar_list"] or cal_id in DB["calendars"]:
            raise ValueError(f"Calendar with ID '{cal_id}' already exists. Please use a different ID or omit the ID to generate a unique one.")
    
    calendar_data_to_store = validated_resource_model.model_dump(exclude_none=True)
    calendar_data_to_store["id"] = cal_id # Ensure 'id' is set

    # Original database interaction logic (assuming DB is globally available)
    DB["calendar_list"][cal_id] = calendar_data_to_store
    DB["calendars"][cal_id] = calendar_data_to_store
    
    return calendar_data_to_store


@tool_spec(
    spec={
        'name': 'patch_calendar_metadata',
        'description': 'Updates specific fields of an existing calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': """ The identifier of the calendar.
                    - To retrieve calendar IDs, call the `calendarList.list` method.
                    - Use the keyword "primary" to access the primary calendar of the currently logged-in user. """
                },
                'resource': {
                    'type': 'object',
                    'description': 'The resource to patch the calendar with.',
                    'properties': {
                        'summary': {
                            'type': 'string',
                            'description': 'The summary of the calendar.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the calendar.'
                        },
                        'timeZone': {
                            'type': 'string',
                            'description': 'The time zone of the calendar (e.g. "America/New_York").'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def patch_calendar(
    calendarId: str, resource: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Updates specific fields of an existing calendar.

    Args:
        calendarId (str): The identifier of the calendar.
            - To retrieve calendar IDs, call the `calendarList.list` method.
            - Use the keyword "primary" to access the primary calendar of the currently logged-in user.
        resource (Optional[Dict[str, Any]]): The resource to patch the calendar with.
            - summary (Optional[str]): The summary of the calendar.
            - description (Optional[str]): The description of the calendar.
            - timeZone (Optional[str]): The time zone of the calendar (e.g. "America/New_York").

    Returns:
        Dict[str, Any]: The patched calendar.
            - id (str): The identifier of the calendar.
            - summary (str): The summary of the calendar.
            - description (str): The description of the calendar.
            - timeZone (str): The time zone of the calendar (e.g. "America/New_York").
            - primary (bool): Whether the calendar is the primary calendar.
    Raises:
        TypeError: If calendarId is not a string or if resource values have invalid types.
        ValueError: If the calendar is not found or if resource contains invalid fields.
    """
    # Input validation for calendarId
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string.")
    
    # Check if calendar exists
    if calendarId not in DB["calendar_list"]:
        raise ValueError(f"Calendar '{calendarId}' not found.")

    if calendarId == "primary":
        calendarId = get_primary_calendar_entry()["id"]
    
    # Get existing calendar data
    existing = DB["calendar_list"][calendarId]
    
    # If no resource provided, return existing calendar
    if resource is None:
        return existing
    
    # Validate resource parameter
    if not isinstance(resource, dict):
        raise TypeError("resource must be a dictionary.")
    
    # Define allowed fields for patching
    allowed_fields = {"summary", "description", "timeZone"}
    
    # Validate resource fields and types
    for key, value in resource.items():
        # Check if field is allowed
        if key not in allowed_fields:
            raise ValueError(f"Field '{key}' is not allowed for calendar patching. Allowed fields: {', '.join(sorted(allowed_fields))}")
        
        # Type validation for each field
        if value is not None:  # Allow None values to clear fields
            if not isinstance(value, str):
                raise TypeError(f"Field '{key}' must be a string, got {type(value).__name__}.")
            
            # Additional validation for specific fields
            if key == "timeZone" and value.strip() == "":
                raise ValueError("timeZone cannot be an empty string.")
            
            # XSS validation for text fields
            if key in {"summary", "description"}:
                from .SimulationEngine.utils import sanitize_calendar_text_fields
                resource[key] = sanitize_calendar_text_fields(value, key)
    
    # Apply patches to existing calendar
    for key, value in resource.items():
        existing[key] = value
    
    # Update both calendar_list and calendars storage
    DB["calendar_list"][calendarId] = existing
    DB["calendars"][calendarId] = existing
    
    return existing


@tool_spec(
    spec={
        'name': 'update_calendar_metadata',
        'description': 'Replaces an existing calendar with new data.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': """ The identifier of the calendar.
                    - To retrieve calendar IDs, call the `calendarList.list` method.
                    - Use the keyword "primary" to access the primary calendar of the currently logged-in user. """
                },
                'resource': {
                    'type': 'object',
                    'description': 'The resource to update the calendar with.',
                    'properties': {
                        'summary': {
                            'type': 'string',
                            'description': 'The summary of the calendar.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the calendar.'
                        },
                        'timeZone': {
                            'type': 'string',
                            'description': 'The time zone of the calendar (e.g. "America/New_York"). Must be a valid IANA time zone identifier.'
                        },
                        'location': {
                            'type': 'string',
                            'description': 'Geographic location of the calendar as free-form text.'
                        }
                    },
                    'required': [
                        'summary'
                    ]
                }
            },
            'required': [
                'calendarId',
                'resource'
            ]
        }
    }
)
def update_calendar(
    calendarId: str, resource: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Replaces an existing calendar with new data.

    Args:
        calendarId (str): The identifier of the calendar. To retrieve calendar IDs, call the `calendarList.list` method. Use the keyword "primary" to access the primary calendar of the currently logged-in user.
        resource (Dict[str, Any]): The resource to update the calendar with.
            - summary (str): The summary of the calendar.
            - description (Optional[str]): The description of the calendar.
            - timeZone (Optional[str]): The time zone of the calendar (e.g. "America/New_York"). Must be a valid IANA time zone identifier.
            - location (Optional[str]): Geographic location of the calendar as free-form text.

    Returns:
        Dict[str, Any]: The updated calendar.
            - id (str): The identifier of the calendar.
            - summary (str): The summary of the calendar.
            - description (str): The description of the calendar.
            - timeZone (str): The time zone of the calendar (e.g. "America/New_York").
            - primary (bool): Whether the calendar is the primary calendar.
    Raises:
        InvalidInputError: If calendarId is not a non-empty string.
        ResourceNotFoundError: If the calendar is not found.
        TypeError: If resource is not a dictionary.
        ValidationError: If the resource contains:
            - Extra fields not allowed
            - Invalid field types (e.g., non-string values for string fields)
            - Empty summary field
            - Invalid IANA timezone format
    """
    if not isinstance(calendarId, str) or not calendarId.strip():
        raise InvalidInputError("calendarId must be a non-empty string.")

    if calendarId == "primary":
        calendarId = get_primary_calendar_entry()["id"]
    if calendarId not in DB["calendars"]:
        raise ResourceNotFoundError(f"Calendar '{calendarId}' not found.")

    if not isinstance(resource, dict):
        raise TypeError("Resource must be a dictionary.")

    # Validate and sanitize input using Pydantic model (includes all security validations)
    try:
        validated_resource_model = UpdateCalendarInputResourceModel(**resource)
    except ValidationError as e:
        raise e

    # Don't exclude None - allow clearing optional fields by setting them to None
    resource_to_store = validated_resource_model.model_dump(exclude_none=False)
    resource_to_store["id"] = calendarId
    DB["calendar_list"][calendarId].update(resource_to_store)
    DB["calendars"][calendarId].update(resource_to_store)
    return DB["calendars"][calendarId]