from common_utils.tool_spec_decorator import tool_spec
# APIs/hubspot/MarketingEvents.py
from typing import Optional, Dict, Any, List, Union
import uuid

from hubspot.SimulationEngine.db import DB
from hubspot.SimulationEngine.models import GetEventsParams
import hashlib
from hubspot.SimulationEngine.custom_errors import (
    EmptyExternalEventIdError,
    EmptyAttendeeIdError,
    EmptyExternalAccountIdError,
    MarketingEventNotFoundError,
    EventAttendeesNotFoundError,
    AttendeeNotFoundError,
    InvalidExternalAccountIdError,
)
from hubspot.SimulationEngine.utils import is_iso_datetime_format
from hubspot.SimulationEngine.models import UpdateEventCustomProperties, CreateEventRequest, CancelMarketingEventRequest, DeleteAttendeeRequest
from pydantic import ValidationError
from datetime import datetime, timezone

from common_utils.utils import validate_email_util
from common_utils.custom_errors import InvalidEmailError


@tool_spec(
    spec={
        'name': 'get_marketing_events',
        'description': 'Get all marketing events with optional filtering and pagination.',
        'parameters': {
            'type': 'object',
            'properties': {
                'occurredAfter': {
                    'type': 'string',
                    'description': 'ISO 8601 timestamp to filter events that occurred after this time. ISO 8601 timestamp.'
                },
                'occurredBefore': {
                    'type': 'string',
                    'description': 'ISO 8601 timestamp to filter events that occurred before this time. ISO 8601 timestamp.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of events to return (1-100). Defaults to 10.'
                },
                'after': {
                    'type': 'string',
                    'description': 'A cursor for pagination, used to fetch the next set of results.'
                }
            },
            'required': []
        }
    }
)
def get_events(
    occurredAfter: Optional[str] = None,
    occurredBefore: Optional[str] = None,
    limit: Optional[int] = 10,
    after: Optional[str] = None,
) -> Dict[str, List[Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]]]:
    """Get all marketing events with optional filtering and pagination.

    Args:
        occurredAfter (Optional[str]): ISO 8601 timestamp to filter events that occurred after this time. Defaults to None.
        occurredBefore (Optional[str]): ISO 8601 timestamp to filter events that occurred before this time. Defaults to None.
        limit (Optional[int]): The maximum number of events to return (1-100). Defaults to 10.
        after (Optional[str]): A cursor for pagination, used to fetch the next set of results. Defaults to None.

    Returns:
        Dict[str, List[Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]]]: A dictionary containing a list of marketing events under the 'results' key.
            The results list contains dictionaries with the following structure:
            - registrants (int): The number of HubSpot contacts that registered for this marketing event.
            - eventOrganizer (str): The name of the organizer of the marketing event.
            - eventUrl (str): A URL in the external event application where the marketing event can be managed.
            - attendees (int): The number of HubSpot contacts that attended this marketing event.
            - eventType (str): The type of the marketing event.
            - eventCompleted (bool): Whether the event is completed.
            - endDateTime (str): The end date and time of the marketing event.
            - noShows (int): The number of HubSpot contacts that registered for this marketing event, but did not attend. This field only has a value when the event is over.
            - cancellations (int): The number of HubSpot contacts that registered for this marketing event, but later cancelled their registration.
            - createdAt (str): Creation timestamp.
            - startDateTime (str): The start date and time of the marketing event.
            - customProperties (List[Dict[str, Union[str, int, bool]]]): Custom properties associated with the event.
                - sourceId (str): Source identifier.
                - selectedByUser (bool): Whether the property was selected by the user.
                - sourceLabel (str): Label of the source.
                - source (str): Source of the property.
                - updatedByUserId (int): ID of the user who last updated the property.
                - persistenceTimestamp (int): Timestamp for persistence.
                - sourceMetadata (str): Source metadata encoded as a base64 string.
                - dataSensitivity (str): Data sensitivity level.
                - unit (str): Unit of measurement.
                - requestId (str): Request identifier.
                - isEncrypted (bool): Whether the value is encrypted.
                - name (str): Property name.
                - useTimestampAsPersistenceTimestamp (bool): Whether to use timestamp as persistence timestamp.
                - value (str): Property value.
                - selectedByUserTimestamp (int): Timestamp when selected by user.
                - timestamp (int): Property timestamp.
                - isLargeValue (bool): Whether the value is large.
            - eventCancelled (bool): Indicates if the marketing event has been cancelled.
            - externalEventId (str): The id of the marketing event in the external event application.
            - eventDescription (str): The description of the marketing event.
            - eventName (str): The name of the marketing event.
            - id (str): Internal ID of the event.
            - objectId (str): Object ID.
            - updatedAt (str): Last update timestamp.

    Raises:
        ValidationError: If any of the input parameters are invalid.
    """
    params = GetEventsParams(
        occurredAfter=occurredAfter,
        occurredBefore=occurredBefore,
        limit=limit,
        after=after
    )

    all_events = sorted(DB["marketing_events"].values(), key=lambda x: x.get('createdAt', ''))

    if params.occurredAfter:
        all_events = [e for e in all_events if e.get('createdAt') and datetime.fromisoformat(e['createdAt'].replace('Z', '+00:00')) > params.occurredAfter]

    if params.occurredBefore:
        all_events = [e for e in all_events if e.get('createdAt') and datetime.fromisoformat(e['createdAt'].replace('Z', '+00:00')) < params.occurredBefore]

    start_index = 0
    if params.after:
        try:
            start_index = next(i for i, event in enumerate(all_events) if event['id'] == params.after) + 1
        except StopIteration:
            return {"results": [], "paging": None} # After cursor not found

    end_index = start_index + params.limit
    paginated_events = all_events[start_index:end_index]

    next_after = None
    if end_index < len(all_events):
        next_after = paginated_events[-1]['id']

    paging_info = None
    if next_after:
        paging_info = {
            "next": {
                "after": next_after,
                "link": f"/marketing/v3/events?after={next_after}&limit={params.limit}"
            }
        }

    return {"results": paginated_events, "paging": paging_info}


@tool_spec(
    spec={
        'name': 'create_marketing_event',
        'description': 'Create a marketing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'externalAccountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the account(external system) where the event was created.'
                },
                'event_name': {
                    'type': 'string',
                    'description': 'The name of the marketing event.'
                },
                'event_type': {
                    'type': 'string',
                    'description': 'The type of the marketing event.'
                },
                'event_organizer': {
                    'type': 'string',
                    'description': 'The organizer of the marketing event.'
                },
                'start_date_time': {
                    'type': 'string',
                    'description': 'The start date and time of the marketing event in ISO 8601 format.'
                },
                'end_date_time': {
                    'type': 'string',
                    'description': 'The end date and time of the marketing event in ISO 8601 format.'
                },
                'event_description': {
                    'type': 'string',
                    'description': 'A description of the marketing event.'
                },
                'event_url': {
                    'type': 'string',
                    'description': 'A URL for more information about the marketing event.'
                },
                'custom_properties': {
                    'type': 'array',
                    'description': 'Custom properties associated with the marketing event.\ncustom_properties is a field you can use to add custom data to a marketing event.\nEach property is a dictionary with the following structure:\n- key: The key of the custom property of string type.\n- value: The value of the custom property.',
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            },
            'required': [
                'externalEventId',
                'externalAccountId',
                'event_name',
                'event_type',
                'event_organizer'
            ]
        }
    }
)

def create_event(
    externalEventId: str,
    externalAccountId: str,
    event_name: str,
    event_type: str,
    event_organizer: str,
    start_date_time: Optional[str] = None,
    end_date_time: Optional[str] = None,
    event_description: Optional[str] = None,
    event_url: Optional[str] = None,
    custom_properties: Optional[List[Dict[str, Union[str, int, bool]]]] = None,
) -> Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]:
    """Create a marketing event.
    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        externalAccountId (str): The unique identifier for the account(external system) where the event was created.
        event_name (str): The name of the marketing event.
        event_type (str): The type of the marketing event.
        event_organizer (str): The organizer of the marketing event.
        start_date_time (Optional[str]): The start date and time of the marketing event in ISO 8601 format. Defaults to None.
        end_date_time (Optional[str]): The end date and time of the marketing event in ISO 8601 format. Defaults to None.
        event_description (Optional[str]): A description of the marketing event. Defaults to None.
        event_url (Optional[str]): A URL for more information about the marketing event. Defaults to None.
        custom_properties (Optional[List[Dict[str, Union[str, int, bool]]]]): Custom properties associated with the marketing event.
            custom_properties is a field you can use to add custom data to a marketing event.
            Each property is a dictionary with the following structure:
            - key: The key of the custom property of string type.
            - value: The value of the custom property.
            Defaults to None.

    Returns:
        Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]: A dictionary representing the created marketing event with the following structure:
            - registrants (int): The number of HubSpot contacts that registered for this marketing event.
            - eventOrganizer (str): The name of the organizer of the marketing event.
            - eventUrl (str): A URL in the external event application where the marketing event can be managed.
            - attendees (int): The number of HubSpot contacts that attended this marketing event.
            - eventType (str): The type of the marketing event.
            - eventCompleted (bool): Whether the event is completed.
            - endDateTime (str): The end date and time of the marketing event.
            - noShows (int): The number of HubSpot contacts that registered for this marketing event, but did not attend. This field only has a value when the event is over.
            - cancellations (int): The number of HubSpot contacts that registered for this marketing event, but later cancelled their registration.
            - createdAt (str): Creation timestamp.
            - startDateTime (str): The start date and time of the marketing event.
            - customProperties (List[Dict[str, Any]]): Custom properties associated with the event.
                Each property is a dictionary with the following structure:
                - key: The key of the custom property of string type.
                - value: The value of the custom property of Any type.
            - eventCancelled (bool): Indicates if the marketing event has been cancelled.
            - externalEventId (str): The id of the marketing event in the external event application.
            - eventDescription (str): The description of the marketing event.
            - eventName (str): The name of the marketing event.
            - id (str): Internal ID of the event.
            - objectId (str): Object ID.
            - updatedAt (str): Last update timestamp.

    Raises:
        EmptyExternalEventIdError: If externalEventId is empty or not provided.
        EmptyExternalAccountIdError: If externalAccountId is empty or not provided.
        ValueError: If any of the required input parameters are invalid.
    """
    # Input validation for required parameters (needed for test compatibility)
    if not externalEventId or not externalEventId.strip():
        raise EmptyExternalEventIdError("External Event ID is required and must be a non-empty string.")
    
    if not externalAccountId or not externalAccountId.strip():
        raise EmptyExternalAccountIdError("External Account ID is required and must be a non-empty string.")
    
    if not event_name or not event_name.strip():
        raise ValueError("Field event_name cannot be empty.")
    
    if not event_type or not event_type.strip():
        raise ValueError("Field event_type cannot be empty.")
    
    if not event_organizer or not event_organizer.strip():
        raise ValueError("Field event_organizer cannot be empty.")

    request_data = {
        "externalEventId": externalEventId,
        "externalAccountId": externalAccountId,
        "eventName": event_name,
        "eventType": event_type,
        "eventOrganizer": event_organizer,
        "startDateTime": start_date_time,
        "endDateTime": end_date_time,
        "eventDescription": event_description,
        "eventUrl": event_url,
        "customProperties": custom_properties,
    }
    validated_data = CreateEventRequest(**{k: v for k, v in request_data.items() if v is not None}).model_dump(exclude_none=True)

    event_id = validated_data["externalEventId"]
    now = datetime.now(timezone.utc).isoformat()

    event = {
        "id": str(uuid.uuid4()),
        "objectId": str(uuid.uuid4()),
        "createdAt": now,
        "updatedAt": now,
        "registrants": 0,
        "attendees": {},
        "noShows": 0,
        "cancellations": 0,
        "eventCompleted": False,
        "eventCancelled": False,
        **validated_data
    }
    
    if 'startDateTime' in event and isinstance(event['startDateTime'], datetime):
        event['startDateTime'] = event['startDateTime'].isoformat()
    if 'endDateTime' in event and isinstance(event['endDateTime'], datetime):
        event['endDateTime'] = event['endDateTime'].isoformat()
    if 'eventUrl' in event:
        event['eventUrl'] = str(event['eventUrl'])

    DB["marketing_events"][event_id] = event
    return event

@tool_spec(
    spec={
        'name': 'get_marketing_event_by_id',
        'description': 'Get a marketing event by its external ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'externalAccountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the account where the event was created.'
                }
            },
            'required': [
                'externalEventId',
                'externalAccountId'
            ]
        }
    }
)
def get_event(externalEventId: str, externalAccountId: str) -> Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]:
    """Get a marketing event by its external ID.

    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        externalAccountId (str): The unique identifier for the account where the event was created.

    Returns:
        Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]: A dictionary containing the marketing event data with the following structure:
            - registrants (int): The number of HubSpot contacts that registered for this marketing event.
            - eventOrganizer (str): The name of the organizer of the marketing event.
            - eventUrl (str): A URL in the external event application where the marketing event can be managed.
            - attendees (int): The number of HubSpot contacts that attended this marketing event.
            - eventType (str): The type of the marketing event.
            - eventCompleted (bool): Whether the event is completed.
            - endDateTime (str): The end date and time of the marketing event.
            - noShows (int): The number of HubSpot contacts that registered for this marketing event, but did not attend. This field only has a value when the event is over.
            - cancellations (int): The number of HubSpot contacts that registered for this marketing event, but later cancelled their registration.
            - createdAt (str): Creation timestamp.
            - startDateTime (str): The start date and time of the marketing event.
            - customProperties (List[Dict[str, Any]]): Custom properties associated with the event.
                - sourceId (str): Source identifier.
                - selectedByUser (bool): Whether the property was selected by the user.
                - sourceLabel (str): Label of the source.
                - source (str): Source of the property.
                - updatedByUserId (int): ID of the user who last updated the property.
                - persistenceTimestamp (int): Timestamp for persistence.
                - sourceMetadata (str): Source metadata encoded as a base64 string.
                - dataSensitivity (str): Data sensitivity level.
                - unit (str): Unit of measurement.
                - requestId (str): Request identifier.
                - isEncrypted (bool): Whether the value is encrypted.
                - name (str): Property name.
                - useTimestampAsPersistenceTimestamp (bool): Whether to use timestamp as persistence timestamp.
                - value (str): Property value.
                - selectedByUserTimestamp (int): Timestamp when selected by user.
                - timestamp (int): Property timestamp.
                - isLargeValue (bool): Whether the value is large.
            - eventCancelled (bool): Indicates if the marketing event has been cancelled.
            - externalEventId (str): The id of the marketing event in the external event application.
            - eventDescription (str): The description of the marketing event.
            - eventName (str): The name of the marketing event.
            - id (str): Internal ID of the event.
            - objectId (str): Object ID.
            - updatedAt (str): Last update timestamp.
    
    Raises:
        TypeError: If externalEventId or externalAccountId is not a string.
        ValueError: If externalEventId or externalAccountId is empty or None
                    or if event is not found in DB or does not belong to the account.
    """
    if externalEventId is None:
        raise ValueError("External Event ID is required.")
    if externalAccountId is None:
        raise ValueError("External Account ID is required.")
    if not isinstance(externalEventId, str):
        raise TypeError("External Event ID must be a string.")
    if not isinstance(externalAccountId, str):
        raise TypeError("External Account ID must be a string.")
    if not externalEventId.strip():
        raise ValueError("External Event ID cannot be empty.")
    if not externalAccountId.strip():
        raise ValueError("External Account ID cannot be empty.")

    marketing_events = DB.get("marketing_events", {})

    if externalEventId not in marketing_events:
        raise ValueError("Event not found in DB.")
    if DB["marketing_events"][externalEventId].get("externalAccountId","") != externalAccountId:
        raise ValueError("Event does not belong to the account.")
    
    return DB["marketing_events"][externalEventId]


@tool_spec(
    spec={
        'name': 'delete_marketing_event',
        'description': 'Delete a marketing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'externalAccountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the account where the event was created.'
                }
            },
            'required': [
                'externalEventId',
                'externalAccountId'
            ]
        }
    }
)
def delete_event(externalEventId: str, externalAccountId: str) -> None:
    """Delete a marketing event.

    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        externalAccountId (str): The unique identifier for the account where the event was created.

    Raises:
        TypeError: If externalEventId or externalAccountId is not a string.
        ValueError: If externalEventId or externalAccountId is empty or None
                    or if event is not found in DB or does not belong to the account.
    """
    if externalEventId is None:
        raise ValueError("External Event ID is required.")
    if externalAccountId is None:
        raise ValueError("External Account ID is required.")
    if not isinstance(externalEventId, str):
        raise TypeError("External Event ID must be a string.")
    if not isinstance(externalAccountId, str):
        raise TypeError("External Account ID must be a string.")
    if not externalEventId.strip():
        raise ValueError("External Event ID cannot be empty.")
    if not externalAccountId.strip():
        raise ValueError("External Account ID cannot be empty.")

    if externalEventId not in DB["marketing_events"]:
        raise ValueError("Event not found in DB.")
    if DB["marketing_events"][externalEventId]["externalAccountId"] != externalAccountId:
        raise ValueError("Event does not belong to the account.")

    del DB["marketing_events"][externalEventId]

@tool_spec(
    spec={
        'name': 'update_marketing_event',
        'description': 'Update a marketing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'externalAccountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the account where the event was created.'
                },
                'registrants': {
                    'type': 'integer',
                    'description': 'The number of HubSpot contacts that registered for this marketing event.'
                },
                'event_name': {
                    'type': 'string',
                    'description': 'The name of the marketing event.'
                },
                'event_type': {
                    'type': 'string',
                    'description': 'The type of the marketing event.'
                },
                'start_date_time': {
                    'type': 'string',
                    'description': 'The start date and time of the marketing event. Must be in valid format (YYYY-MM-DDTHH:MM:SS).' 
                },
                'end_date_time': {
                    'type': 'string',
                    'description': 'The end date and time of the marketing event. Must be in valid format (YYYY-MM-DDTHH:MM:SS).' 
                },
                'event_organizer': {
                    'type': 'string',
                    'description': 'The organizer of the marketing event.'
                },
                'event_description': {
                    'type': 'string',
                    'description': 'A description of the marketing event.'
                },
                'event_url': {
                    'type': 'string',
                    'description': 'A URL for more information about the marketing event.'
                },
                'attendees': {
                    'type': 'integer',
                    'description': 'The number of HubSpot contacts that attended this marketing event. Must be a positive integer.'
                },
                'no_shows': {
                    'type': 'integer',
                    'description': 'The number of HubSpot contacts that registered for this marketing event, but did not attend. This field only has a value when the event is over. Must be a positive integer.'
                },
                'event_completed': {
                    'type': 'boolean',
                    'description': 'Whether the event is completed.'
                },
                'custom_properties': {
                    'type': 'array',
                    'description': 'Custom properties associated with the marketing event.\ncustom_properties is a field you can use to add custom data to a marketing event.\nEach property is a dictionary with the following structure:\n- key: The key of the custom property of string type.\n- value: The value of the custom property (string, number, or boolean).',
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            },
            'required': [
                'externalEventId',
                'externalAccountId'
            ]
        }
    }
)
def update_event(
    externalEventId: str,
    externalAccountId: str,
    registrants: Optional[int] = None,
    event_name: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date_time: Optional[str] = None,
    end_date_time: Optional[str] = None,
    event_organizer: Optional[str] = None,
    event_description: Optional[str] = None,
    event_url: Optional[str] = None,
    attendees: Optional[int] = None,
    no_shows: Optional[int] = None,
    event_completed: Optional[bool] = None,
    custom_properties: Optional[List[Dict[str, Union[str, int, bool, float]]]] = None,
) -> Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]:
    """Update a marketing event.

    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        externalAccountId (str): The unique identifier for the account where the event was created.
        registrants (Optional[int]): The number of HubSpot contacts that registered for this marketing event. Defaults to None.
        event_name (Optional[str]): The name of the marketing event. Defaults to None.
        event_type (Optional[str]): The type of the marketing event. Defaults to None.
        start_date_time (Optional[str]): The start date and time of the marketing event. Must be in valid format (YYYY-MM-DDTHH:MM:SS). Defaults to None.
        end_date_time (Optional[str]): The end date and time of the marketing event. Must be in valid format (YYYY-MM-DDTHH:MM:SS). Defaults to None.
        event_organizer (Optional[str]): The organizer of the marketing event. Defaults to None.
        event_description (Optional[str]): A description of the marketing event. Defaults to None.
        event_url (Optional[str]): A URL for more information about the marketing event. Defaults to None.
        attendees (Optional[int]): The number of HubSpot contacts that attended this marketing event. Must be a positive integer. Defaults to None.
        no_shows (Optional[int]): The number of HubSpot contacts that registered for this marketing event, but did not attend. This field only has a value when the event is over. Must be a positive integer. Defaults to None.
        event_completed (Optional[bool]): Whether the event is completed. Defaults to None.
        custom_properties (Optional[List[Dict[str, Union[str, int, bool, float]]]]): Custom properties associated with the marketing event.
            custom_properties is a field you can use to add custom data to a marketing event.
            Each property is a dictionary with the following structure:
            - key: The key of the custom property of string type.
            - value: The value of the custom property (string, number, or boolean).
            Defaults to None.

    Returns:
        Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]: A dictionary representing the updated marketing event with the following structure:
            - registrants (int): The number of HubSpot contacts that registered for this marketing event.
            - eventOrganizer (str): The name of the organizer of the marketing event.
            - eventUrl (str): A URL in the external event application where the marketing event can be managed.
            - attendees (int): The number of HubSpot contacts that attended this marketing event.
            - eventType (str): The type of the marketing event.
            - eventCompleted (bool): Whether the event is completed.
            - endDateTime (str): The end date and time of the marketing event.
            - noShows (int): The number of HubSpot contacts that registered for this marketing event, but did not attend. This field only has a value when the event is over.
            - cancellations (int): The number of HubSpot contacts that registered for this marketing event, but later cancelled their registration.
            - createdAt (str): Creation timestamp.
            - startDateTime (str): The start date and time of the marketing event.
            - customProperties (List[Dict[str, Union[str, int, bool]]]): Custom properties associated with the event.
                - sourceId (str): Source identifier.
                - selectedByUser (bool): Whether the property was selected by the user.
                - sourceLabel (str): Label of the source.
                - source (str): Source of the property.
                - updatedByUserId (int): ID of the user who last updated the property.
                - persistenceTimestamp (int): Timestamp for persistence.
                - sourceMetadata (str): Source metadata encoded as a base64 string.
                - dataSensitivity (str): Data sensitivity level.
                - unit (str): Unit of measurement.
                - requestId (str): Request identifier.
                - isEncrypted (bool): Whether the value is encrypted.
                - name (str): Property name.
                - useTimestampAsPersistenceTimestamp (bool): Whether to use timestamp as persistence timestamp.
                - value (str): Property value.
                - selectedByUserTimestamp (int): Timestamp when selected by user.
                - timestamp (int): Property timestamp.
                - isLargeValue (bool): Whether the value is large.
            - eventCancelled (bool): Indicates if the marketing event has been cancelled.
            - externalEventId (str): The id of the marketing event in the external event application.
            - eventDescription (str): The description of the marketing event.
            - eventName (str): The name of the marketing event.
            - id (str): Internal ID of the event.
            - objectId (str): Object ID.
            - updatedAt (str): Last update timestamp.

    Raises:
        TypeError: If the type of the input is not correct.
        ValueError: If the required input is not provided or empty
                    or if optional string parameters are provided but empty
                    or if no_shows or attendees or registrants are provided and they are negative
                    or if start_date_time or end_date_time are provided and they are not in valid format (YYYY-MM-DDTHH:MM:SS)
                    or if start_date_time is after end_date_time
                    or if externalEventId is not found in the DB
                    or if externalEventId does not belong to the account
                    or if no_shows is provided and the event is not over. 
        ValidationError: If the custom_properties is not in the correct structure.                   
    """
    if externalEventId is None:
        raise ValueError("External Event ID is required.")
    if externalAccountId is None:
        raise ValueError("External Account ID is required.")
    if not isinstance(externalEventId, str):
        raise TypeError("External Event ID must be a string.")
    if not isinstance(externalAccountId, str):
        raise TypeError("External Account ID must be a string.")
    if not externalEventId.strip():
        raise ValueError("External Event ID cannot be empty.")
    if not externalAccountId.strip():
        raise ValueError("External Account ID cannot be empty.")

    marketing_events = DB.get("marketing_events", {})

    if externalEventId not in marketing_events:
        raise ValueError("Event not found in DB.")
    if DB["marketing_events"][externalEventId].get("externalAccountId","") != externalAccountId:
        raise ValueError("Event does not belong to the account.")

    event = DB["marketing_events"][externalEventId]
    if registrants is not None:
        if not isinstance(registrants, int):
            raise TypeError("Registrants must be an integer.")
        if registrants < 0:
            raise ValueError("Registrants must be a positive integer.")
        event["registrants"] = registrants
    if event_organizer is not None:
        if not isinstance(event_organizer, str):
            raise TypeError("Event organizer must be a string.")
        if not event_organizer.strip():
            raise ValueError("Event organizer cannot be empty.")
        event["eventOrganizer"] = event_organizer
    if event_url is not None:
        if not isinstance(event_url, str):
            raise TypeError("Event URL must be a string.")
        if not event_url.strip():
            raise ValueError("Event URL cannot be empty.")
        event["eventUrl"] = event_url
    if attendees is not None:
        if not isinstance(attendees, int):
            raise TypeError("Attendees must be an integer.")
        if attendees < 0:
            raise ValueError("Attendees must be a positive integer.")
        event["attendees"] = attendees
    if event_type is not None:
        if not isinstance(event_type, str):
            raise TypeError("Event type must be a string.")
        if not event_type.strip():
            raise ValueError("Event type cannot be empty.")
        event["eventType"] = event_type
    if event_completed is not None:
        if not isinstance(event_completed, bool):
            raise TypeError("Event completed must be a boolean.")
        event["eventCompleted"] = event_completed
    if start_date_time is not None:
        if not isinstance(start_date_time, str):
            raise TypeError("Start date time must be a string.")
        if not start_date_time.strip():
            raise ValueError("Start date time cannot be empty.")
        if not is_iso_datetime_format(start_date_time):
            raise ValueError("Start date time must be in valid format.")
        event["startDateTime"] = start_date_time
    if end_date_time is not None:
        if not isinstance(end_date_time, str):
            raise TypeError("End date time must be a string.")
        if not end_date_time.strip():
            raise ValueError("End date time cannot be empty.")
        if not is_iso_datetime_format(end_date_time):
            raise ValueError("End date time must be in valid format.")
        event["endDateTime"] = end_date_time
    # Fixed: Use .get() instead of direct access to avoid KeyError
    if event.get("startDateTime") is not None and event.get("endDateTime") is not None:
        if datetime.strptime(event["startDateTime"], "%Y-%m-%dT%H:%M:%S") > datetime.strptime(event["endDateTime"], "%Y-%m-%dT%H:%M:%S"):
            raise ValueError("Start date time must be before end date time.")
    if event_description is not None:
        if not isinstance(event_description, str):
            raise TypeError("Event description must be a string.")
        if not event_description.strip():
            raise ValueError("Event description cannot be empty.")
        event["eventDescription"] = event_description
    if event_name is not None:
        if not isinstance(event_name, str):
            raise TypeError("Event name must be a string.")
        if not event_name.strip():
            raise ValueError("Event name cannot be empty.")
        event["eventName"] = event_name
    if no_shows is not None:
        if not isinstance(no_shows, int):
            raise TypeError("No shows must be an integer.")
        if no_shows < 0:
            raise ValueError("No shows must be a positive integer.")
        if event.get("eventCompleted",False) is False:
            raise ValueError("No shows can only be set when the event is over.")
        event["noShows"] = no_shows
    if custom_properties is not None:
        if not isinstance(custom_properties,list):
            raise TypeError("Custom properties must be a list.")
        for property in custom_properties:
            try:
                UpdateEventCustomProperties(**property)
            except ValidationError as e:
                raise 
        event["customProperties"] = custom_properties
    event["updatedAt"] = datetime.now(timezone.utc).isoformat()

    DB["marketing_events"][externalEventId] = event
    return event

@tool_spec(
    spec={
        'name': 'cancel_marketing_event',
        'description': 'Marks an event as cancelled.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'externalAccountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the account where the event was created.'
                }
            },
            'required': [
                'externalEventId',
                'externalAccountId'
            ]
        }
    }
)
def cancel_event(externalEventId: str, externalAccountId: str) -> Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]:
    """Marks an event as cancelled.

    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        externalAccountId (str): The unique identifier for the account where the event was created.

    Returns:
        Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, bool]]]]]: A dictionary representing the cancelled marketing event with the following structure:
            - registrants (int): The number of HubSpot contacts that registered for this marketing event.
            - eventOrganizer (str): The name of the organizer of the marketing event.
            - eventUrl (str): A URL in the external event application where the marketing event can be managed.
            - attendees (int): The number of HubSpot contacts that attended this marketing event.
            - eventType (str): The type of the marketing event.
            - eventCompleted (bool): Whether the event is completed.
            - endDateTime (str): The end date and time of the marketing event.
            - noShows (int): The number of HubSpot contacts that registered for this marketing event, but did not attend. This field only has a value when the event is over.
            - cancellations (int): The number of HubSpot contacts that registered for this marketing event, but later cancelled their registration.
            - createdAt (str): Creation timestamp.
            - startDateTime (str): The start date and time of the marketing event.
            - customProperties (List[Dict[str, Union[str, int, bool]]]): Custom properties associated with the event.
                - sourceId (str): Source identifier.
                - selectedByUser (bool): Whether the property was selected by the user.
                - sourceLabel (str): Label of the source.
                - source (str): Source of the property.
                - updatedByUserId (int): ID of the user who last updated the property.
                - persistenceTimestamp (int): Timestamp for persistence.
                - sourceMetadata (str): Source metadata encoded as a base64 string.
                - dataSensitivity (str): Data sensitivity level.
                - unit (str): Unit of measurement.
                - requestId (str): Request identifier.
                - isEncrypted (bool): Whether the value is encrypted.
                - name (str): Property name.
                - useTimestampAsPersistenceTimestamp (bool): Whether to use timestamp as persistence timestamp.
                - value (str): Property value.
                - selectedByUserTimestamp (int): Timestamp when selected by user.
                - timestamp (int): Property timestamp.
                - isLargeValue (bool): Whether the value is large.
            - eventCancelled (bool): Indicates if the marketing event has been cancelled.
            - externalEventId (str): The id of the marketing event in the external event application.
            - eventDescription (str): The description of the marketing event.
            - eventName (str): The name of the marketing event.
            - id (str): Internal ID of the event.
            - objectId (str): Object ID.
            - updatedAt (str): Last update timestamp.
     Raises:
        ValueError: If event is not found in DB or does not belong to the account
                    or if event is already canceled.
    """
    # Input validation using Pydantic model
    
    request_data = CancelMarketingEventRequest(
        externalEventId=externalEventId,
        externalAccountId=externalAccountId
    )
    
    # Extract validated values
    externalEventId = request_data.externalEventId
    externalAccountId = request_data.externalAccountId

    marketing_events = DB.get("marketing_events", {})

    if externalEventId not in marketing_events:
        raise ValueError("Event not found in DB.")
    if DB["marketing_events"][externalEventId].get("externalAccountId","") != externalAccountId:
        raise ValueError("Event does not belong to the account.")
    if DB["marketing_events"][externalEventId].get("eventCancelled", None):
        raise ValueError("Event is already canceled.")
    DB["marketing_events"][externalEventId]["eventCancelled"] = True
    return DB["marketing_events"][externalEventId]

@tool_spec(
    spec={
        'name': 'create_or_update_marketing_event_attendee',
        'description': 'Create or update an attendee for a marketing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'externalAccountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the account where the event was created.'
                },
                'email': {
                    'type': 'string',
                    'description': 'The email address of the attendee.'
                },
                'joinedAt': {
                    'type': 'string',
                    'description': 'The date and time when the attendee joined the event (ISO 8601 format).'
                },
                'leftAt': {
                    'type': 'string',
                    'description': 'The date and time when the attendee left the event (ISO 8601 format).'
                }
            },
            'required': [
                'externalEventId',
                'externalAccountId',
                'email'
            ]
        }
    }
)
def create_or_update_attendee(
    externalEventId: str,
    externalAccountId: str,
    email: str,
    joinedAt: Optional[str] = None,
    leftAt: Optional[str] = None,
) -> Dict[str, str]:
    """Create or update an attendee for a marketing event.

    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        externalAccountId (str): The unique identifier for the account where the event was created.
        email (str): The email address of the attendee.
        joinedAt (Optional[str]): The date and time when the attendee joined the event (ISO 8601 format).
        leftAt (Optional[str]): The date and time when the attendee left the event (ISO 8601 format).

    Returns:
        Dict[str, str]: A dictionary representing the attendee with the following structure:
            - attendeeId (str): The unique identifier for the attendee.
            - email (str): The email address of the attendee.
            - eventId (str): The external event ID that the attendee is associated with.
            - externalAccountId (str): The external account ID where the event was created.
            - joinedAt (str): The date and time when the attendee joined the event (ISO 8601 format).
            - leftAt (str): The date and time when the attendee left the event (ISO 8601 format).

    Raises:
        EmptyExternalEventIdError: If externalEventId is empty or not provided.
        EmptyExternalAccountIdError: If externalAccountId is empty or not provided.
        MarketingEventNotFoundError: If a marketing event with the given external event ID is not found.
        InvalidExternalAccountIdError: If the external account ID does not match the event's account ID.
        ValueError: If email, joinedAt, or leftAt parameters are empty, invalid, or not in ISO 8601 format.
    """
    # Input validation with proper type checking
    if not isinstance(externalEventId, str) or not externalEventId.strip():
        raise EmptyExternalEventIdError(
            "External Event ID is required and must be a non-empty string."
        )

    if not isinstance(externalAccountId, str) or not externalAccountId.strip():
        raise EmptyExternalAccountIdError(
            "External Account ID is required and must be a non-empty string."
        )

    if not isinstance(email, str) or not email.strip():
        raise ValueError("Email is required and must be a non-empty string.")

    # Validate ISO 8601 datetime format for joinedAt
    if joinedAt:
        try:
            datetime.fromisoformat(joinedAt.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"joinedAt must be in ISO 8601 format, got: {joinedAt}")
    validate_email_util(email, "email")

    # Validate ISO 8601 datetime format for leftAt
    if leftAt:
        try:
            datetime.fromisoformat(leftAt.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"leftAt must be in ISO 8601 format, got: {leftAt}")

    # Check if event exists
    if externalEventId not in DB["marketing_events"]:
        raise MarketingEventNotFoundError(
            f"Marketing event with ID '{externalEventId}' not found."
        )

    # Verify external account ID matches
    if (
        DB["marketing_events"][externalEventId]["externalAccountId"]
        != externalAccountId
    ):
        raise InvalidExternalAccountIdError(
            f"External account ID '{externalAccountId}' does not match the event's account ID."
        )

    # Initialize attendees section if it doesn't exist
    if "attendees" not in DB["marketing_events"][externalEventId]:
        DB["marketing_events"][externalEventId]["attendees"] = {}

    # Check if attendee already exists and update
    for attendee in DB["marketing_events"][externalEventId]["attendees"].values():
        if attendee["email"] == email:
            attendee["joinedAt"] = joinedAt
            attendee["leftAt"] = leftAt
            return attendee

    # Create new attendee
    attendee_id = hashlib.sha256(f"{externalEventId}-{email}".encode()).hexdigest()[:8]
    attendee = {
        "attendeeId": attendee_id,
        "email": email,
        "eventId": externalEventId,
        "externalAccountId": externalAccountId,
        "joinedAt": joinedAt,
        "leftAt": leftAt,
    }

    DB["marketing_events"][externalEventId]["attendees"][attendee_id] = attendee
    return attendee


@tool_spec(
    spec={
        'name': 'get_marketing_event_attendees',
        'description': 'Get attendees of a marketing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of attendees to return. Defaults to 10. The maximum is 100.'
                },
                'after': {
                    'type': 'string',
                    'description': 'A cursor for pagination.'
                }
            },
            'required': [
                'externalEventId'
            ]
        }
    }
)
def get_attendees(
    externalEventId: str, limit: int = 10, after: Optional[str] = None
) -> Dict[str, List[Dict[str, str]]]:
    """Get attendees of a marketing event.

    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        limit (int, optional): The maximum number of attendees to return. Defaults to 10. The maximum is 100.
        after (Optional[str]): A cursor for pagination. Defaults to None.

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary containing a list of attendees under the 'results' key.
            Each attendee is a dictionary with the following structure:
            - attendeeId (str): The unique identifier for the attendee.
            - email (str): The email address of the attendee.
            - eventId (str): The external event ID that the attendee is associated with.
            - externalAccountId (str): The external account ID where the event was created.
            - joinedAt (str): The date and time when the attendee joined the event (ISO 8601 format).
            - leftAt (str): The date and time when the attendee left the event (ISO 8601 format).

    Raises:
        EmptyExternalEventIdError: If externalEventId is empty or not provided.
        TypeError: If externalEventId is not a string, limit is not an integer, or after is not a string when provided.
        MarketingEventNotFoundError: If a marketing event with the given external event ID is not found.
        ValueError: If limit is not between 1 and 100.
    """
    # Validate externalEventId datatype and value
    if not isinstance(externalEventId, str):
        raise TypeError("External Event ID must be a string.")
    if not externalEventId.strip():
        raise EmptyExternalEventIdError(
            "External Event ID is required and must be a non-empty string."
        )
    
    # Validate limit datatype and value
    if not isinstance(limit, int):
        raise TypeError("Limit must be an integer.")
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")
    
    # Validate after datatype when provided
    if after is not None and not isinstance(after, str):
        raise TypeError("After parameter must be a string when provided.")

    if externalEventId not in DB["marketing_events"]:
        raise MarketingEventNotFoundError(
            f"Marketing event with ID '{externalEventId}' not found."
        )

    attendees_dict = DB["marketing_events"][externalEventId].get("attendees", {})
    if not attendees_dict:
        return {"results": []}

    all_attendees = sorted(
        list(attendees_dict.values()), key=lambda x: x.get("email", "")
    )

    start_index = 0
    if after:
        try:
            start_index = (
                next(
                    i
                    for i, attendee in enumerate(all_attendees)
                    if attendee["attendeeId"] == after
                )
                + 1
            )
        except StopIteration:
            return {"results": []}

    paginated_attendees = all_attendees[start_index : start_index + limit]
    return {"results": paginated_attendees}

@tool_spec(
    spec={
        'name': 'delete_marketing_event_attendee',
        'description': 'Remove an attendee from a marketing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'externalEventId': {
                    'type': 'string',
                    'description': 'The unique identifier for the marketing event as per the external system where the event was created.'
                },
                'attendeeId': {
                    'type': 'string',
                    'description': 'The unique identifier for the attendee.'
                },
                'externalAccountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the account where the event was created.'
                }
            },
            'required': [
                'externalEventId',
                'attendeeId',
                'externalAccountId'
            ]
        }
    }
)
def delete_attendee(
    externalEventId: str, attendeeId: str, externalAccountId: str
) -> None:
    """Remove an attendee from a marketing event.

    Args:
        externalEventId (str): The unique identifier for the marketing event as per the external system where the event was created.
        attendeeId (str): The unique identifier for the attendee.
        externalAccountId (str): The unique identifier for the account where the event was created.

    Returns:
        None

    Raises:
        ValidationError: If any of the input parameters are invalid.
        MarketingEventNotFoundError: If a marketing event with the given external event ID is not found.
        EventAttendeesNotFoundError: If the attendees section is not found for the marketing event.
        AttendeeNotFoundError: If an attendee with the given ID is not found in the specified event.
        InvalidExternalAccountIdError: If the external account ID does not match the event's account ID.
    """
    # Input validation using Pydantic model
    request_data = DeleteAttendeeRequest(
        externalEventId=externalEventId,
        attendeeId=attendeeId,
        externalAccountId=externalAccountId
    )
    
    externalEventId = request_data.externalEventId
    attendeeId = request_data.attendeeId
    externalAccountId = request_data.externalAccountId

    # Check if event exists
    if externalEventId not in DB["marketing_events"]:
        raise MarketingEventNotFoundError(f"Marketing event with ID '{externalEventId}' not found.")

    # Verify external account ID matches
    if DB["marketing_events"][externalEventId]["externalAccountId"] != externalAccountId:
        raise InvalidExternalAccountIdError(f"External account ID '{externalAccountId}' does not match the event's account ID.")

    # Check if event has attendees section
    if "attendees" not in DB["marketing_events"][externalEventId]:
        raise EventAttendeesNotFoundError(f"No attendees section found for marketing event '{externalEventId}'.")

    # Check if attendee exists in the event
    if attendeeId not in DB["marketing_events"][externalEventId]["attendees"]:
        raise AttendeeNotFoundError(f"Attendee with ID '{attendeeId}' not found in marketing event '{externalEventId}'.")

    # Remove the attendee
    DB["marketing_events"][externalEventId]["attendees"].pop(attendeeId, None)
