from common_utils.tool_spec_decorator import tool_spec
# APIs/salesforce/Event.py
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid
import re
from APIs.common_utils.error_handling import handle_api_errors
from salesforce.SimulationEngine.custom_errors import EventNotFoundError
from salesforce.SimulationEngine.db import DB
from salesforce.SimulationEngine import custom_errors
from pydantic import ValidationError
from salesforce.SimulationEngine.models import (
    EventUpdateKwargsModel,
    EventInputModel,
    EventUpsertModel,
    QueryCriteriaModel,
    RetrieveEventInput,
    SearchTermModel,
    UndeleteEventOutput,
)

from salesforce.SimulationEngine import custom_errors

"""
    Represents the Event resource in the API.
"""


@tool_spec(
    spec={
        'name': 'create_event',
        'description': 'Creates a new event with all standard Salesforce Event fields.',
        'parameters': {
            'type': 'object',
            'properties': {
                'Name': {
                    'type': 'string',
                    'description': 'The name of the event.'
                },
                'Subject': {
                    'type': 'string',
                    'description': 'The subject of the event.'
                },
                'StartDateTime': {
                    'type': 'string',
                    'description': 'Start time of the event.'
                },
                'EndDateTime': {
                    'type': 'string',
                    'description': 'End time of the event.'
                },
                'Description': {
                    'type': 'string',
                    'description': 'Description of the event.'
                },
                'Location': {
                    'type': 'string',
                    'description': 'Location of the event.'
                },
                'IsAllDayEvent': {
                    'type': 'boolean',
                    'description': 'Whether the event is all day.'
                },
                'OwnerId': {
                    'type': 'string',
                    'description': 'ID of the event owner.'
                },
                'WhoId': {
                    'type': 'string',
                    'description': 'ID of the related contact.'
                },
                'WhatId': {
                    'type': 'string',
                    'description': 'ID of the related record.'
                },
                'ActivityDate': {
                    'type': 'string',
                    'description': 'Date of the activity.'
                },
                'ActivityDateTime': {
                    'type': 'string',
                    'description': 'Date and time of the activity.'
                },
                'DurationInMinutes': {
                    'type': 'integer',
                    'description': 'Duration of the event in minutes.'
                },
                'IsPrivate': {
                    'type': 'boolean',
                    'description': 'Whether the event is private.'
                },
                'ShowAs': {
                    'type': 'string',
                    'description': 'How the event appears in calendar (Busy, Free, etc.).'
                },
                'Type': {
                    'type': 'string',
                    'description': 'Type of the event.'
                },
                'IsChild': {
                    'type': 'boolean',
                    'description': 'Whether this is a child event.'
                },
                'IsGroupEvent': {
                    'type': 'boolean',
                    'description': 'Whether this is a group event.'
                },
                'GroupEventType': {
                    'type': 'string',
                    'description': 'Type of group event.'
                },
                'IsRecurrence': {
                    'type': 'boolean',
                    'description': 'Whether the event is recurring.'
                },
                'RecurrenceType': {
                    'type': 'string',
                    'description': 'Type of recurrence (RecursDaily, RecursWeekly, etc.).'
                },
                'RecurrenceInterval': {
                    'type': 'integer',
                    'description': 'Recurrence interval.'
                },
                'RecurrenceEndDateOnly': {
                    'type': 'string',
                    'description': 'End date for recurrence.'
                },
                'RecurrenceMonthOfYear': {
                    'type': 'integer',
                    'description': 'Month of year for recurrence (1-12).'
                },
                'RecurrenceDayOfWeekMask': {
                    'type': 'integer',
                    'description': 'Day of week mask for recurrence.'
                },
                'RecurrenceDayOfMonth': {
                    'type': 'integer',
                    'description': 'Day of month for recurrence (1-31).'
                },
                'RecurrenceInstance': {
                    'type': 'string',
                    'description': 'Recurrence instance.'
                },
                'IsReminderSet': {
                    'type': 'boolean',
                    'description': 'Whether reminder is set.'
                },
                'ReminderDateTime': {
                    'type': 'string',
                    'description': 'Reminder date and time.'
                }
            },
            'required': []
        }
    }
)
def create(
    Name: Optional[str] = None,
    Subject: Optional[str] = None,
    StartDateTime: Optional[str] = None,
    EndDateTime: Optional[str] = None,
    Description: Optional[str] = None,
    Location: Optional[str] = None,
    IsAllDayEvent: Optional[bool] = None,
    OwnerId: Optional[str] = None,
    WhoId: Optional[str] = None,
    WhatId: Optional[str] = None,
    # Additional standard Event fields
    ActivityDate: Optional[str] = None,
    ActivityDateTime: Optional[str] = None,
    DurationInMinutes: Optional[int] = None,
    IsPrivate: Optional[bool] = None,
    ShowAs: Optional[str] = None,
    Type: Optional[str] = None,
    IsChild: Optional[bool] = None,
    IsGroupEvent: Optional[bool] = None,
    GroupEventType: Optional[str] = None,
    IsRecurrence: Optional[bool] = None,
    RecurrenceType: Optional[str] = None,
    RecurrenceInterval: Optional[int] = None,
    RecurrenceEndDateOnly: Optional[str] = None,
    RecurrenceMonthOfYear: Optional[int] = None,
    RecurrenceDayOfWeekMask: Optional[int] = None,
    RecurrenceDayOfMonth: Optional[int] = None,
    RecurrenceInstance: Optional[str] = None,
    IsReminderSet: Optional[bool] = None,
    ReminderDateTime: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a new event with all standard Salesforce Event fields.

    Args:
        Name (Optional[str]): The name of the event.
        Subject (Optional[str]): The subject of the event.
        StartDateTime (Optional[str]): Start time of the event.
        EndDateTime (Optional[str]): End time of the event.
        Description (Optional[str]): Description of the event.
        Location (Optional[str]): Location of the event.
        IsAllDayEvent (Optional[bool]): Whether the event is all day.
        OwnerId (Optional[str]): ID of the event owner.
        WhoId (Optional[str]): ID of the related contact.
        WhatId (Optional[str]): ID of the related record.
        ActivityDate (Optional[str]): Date of the activity.
        ActivityDateTime (Optional[str]): Date and time of the activity.
        DurationInMinutes (Optional[int]): Duration of the event in minutes.
        IsPrivate (Optional[bool]): Whether the event is private.
        ShowAs (Optional[str]): How the event appears in calendar (Busy, Free, etc.).
        Type (Optional[str]): Type of the event.
        IsChild (Optional[bool]): Whether this is a child event.
        IsGroupEvent (Optional[bool]): Whether this is a group event.
        GroupEventType (Optional[str]): Type of group event.
        IsRecurrence (Optional[bool]): Whether the event is recurring.
        RecurrenceType (Optional[str]): Type of recurrence (RecursDaily, RecursWeekly, etc.).
        RecurrenceInterval (Optional[int]): Recurrence interval.
        RecurrenceEndDateOnly (Optional[str]): End date for recurrence.
        RecurrenceMonthOfYear (Optional[int]): Month of year for recurrence (1-12).
        RecurrenceDayOfWeekMask (Optional[int]): Day of week mask for recurrence.
        RecurrenceDayOfMonth (Optional[int]): Day of month for recurrence (1-31).
        RecurrenceInstance (Optional[str]): Recurrence instance.
        IsReminderSet (Optional[bool]): Whether reminder is set.
        ReminderDateTime (Optional[str]): Reminder date and time.

    Returns:
        Dict[str, Any]: The created event object with the following fields:
            - Id (str): Unique identifier for the event
            - CreatedDate (str): ISO format timestamp of creation
            - IsDeleted (bool): Whether the event is deleted
            - SystemModstamp (str): Last modified timestamp
            - Name (Optional[str]): The name of the event, if provided
            - Subject (Optional[str]): The subject of the event, if provided
            - StartDateTime (Optional[str]): Start time of the event, if provided
            - EndDateTime (Optional[str]): End time of the event, if provided
            - Description (Optional[str]): Description of the event, if provided
            - Location (Optional[str]): Location of the event, if provided
            - IsAllDayEvent (Optional[bool]): Whether the event is all day, if provided
            - OwnerId (Optional[str]): ID of the event owner, if provided
            - WhoId (Optional[str]): ID of the related contact, if provided
            - WhatId (Optional[str]): ID of the related record, if provided
            - ActivityDate (Optional[str]): Date of the activity, if provided
            - ActivityDateTime (Optional[str]): Date and time of the activity, if provided
            - DurationInMinutes (Optional[int]): Duration of the event in minutes, if provided
            - IsPrivate (Optional[bool]): Whether the event is private, if provided
            - ShowAs (Optional[str]): How the event appears in calendar, if provided
            - Type (Optional[str]): Type of the event, if provided
            - IsChild (Optional[bool]): Whether this is a child event, if provided
            - IsGroupEvent (Optional[bool]): Whether this is a group event, if provided
            - GroupEventType (Optional[str]): Type of group event, if provided
            - IsRecurrence (Optional[bool]): Whether the event is recurring, if provided
            - RecurrenceType (Optional[str]): Type of recurrence, if provided
            - RecurrenceInterval (Optional[int]): Recurrence interval, if provided
            - RecurrenceEndDateOnly (Optional[str]): End date for recurrence, if provided
            - RecurrenceMonthOfYear (Optional[int]): Month of year for recurrence, if provided
            - RecurrenceDayOfWeekMask (Optional[int]): Day of week mask for recurrence, if provided
            - RecurrenceDayOfMonth (Optional[int]): Day of month for recurrence, if provided
            - RecurrenceInstance (Optional[str]): Recurrence instance, if provided
            - IsReminderSet (Optional[bool]): Whether reminder is set, if provided
            - ReminderDateTime (Optional[str]): Reminder date and time, if provided

    Raises:
        ValidationError: If event attributes do not conform to EventInputModel structure.
    """

    # Build event attributes for validation
    event_attributes = {
        "Name": Name,
        "Subject": Subject,
        "StartDateTime": StartDateTime,
        "EndDateTime": EndDateTime,
        "Description": Description,
        "Location": Location,
        "IsAllDayEvent": IsAllDayEvent,
        "OwnerId": OwnerId,
        "WhoId": WhoId,
        "WhatId": WhatId,
        "ActivityDate": ActivityDate,
        "ActivityDateTime": ActivityDateTime,
        "DurationInMinutes": DurationInMinutes,
        "IsPrivate": IsPrivate,
        "ShowAs": ShowAs,
        "Type": Type,
        "IsChild": IsChild,
        "IsGroupEvent": IsGroupEvent,
        "GroupEventType": GroupEventType,
        "IsRecurrence": IsRecurrence,
        "RecurrenceType": RecurrenceType,
        "RecurrenceInterval": RecurrenceInterval,
        "RecurrenceEndDateOnly": RecurrenceEndDateOnly,
        "RecurrenceMonthOfYear": RecurrenceMonthOfYear,
        "RecurrenceDayOfWeekMask": RecurrenceDayOfWeekMask,
        "RecurrenceDayOfMonth": RecurrenceDayOfMonth,
        "RecurrenceInstance": RecurrenceInstance,
        "IsReminderSet": IsReminderSet,
        "ReminderDateTime": ReminderDateTime,
    }

    # Validate using EventInputModel
    validated_event_data = EventInputModel(**event_attributes)

    # Create base event object
    new_event = {
        "Id": str(uuid.uuid4()),  # Generate a unique ID
        "CreatedDate": datetime.now().isoformat(),
        "IsDeleted": False,
        "SystemModstamp": datetime.now().isoformat(),
    }

    # Add all provided fields using validated data
    # model_dump(exclude_none=True) returns only fields that were explicitly set
    validated_fields = validated_event_data.model_dump(exclude_none=True)
    new_event.update(validated_fields)

    DB.setdefault("Event", {})
    DB["Event"][new_event["Id"]] = new_event
    return new_event


@tool_spec(
    spec={
        'name': 'delete_event',
        'description': 'Deletes an event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'string',
                    'description': 'The ID of the event to delete.'
                }
            },
            'required': [
                'event_id'
            ]
        }
    }
)
def delete(event_id: str) -> None:
    """
    Deletes an event.

    Args:
        event_id (str): The ID of the event to delete.

    Returns:
        None: No return value on success.
    
    Raises:
        InvalidParameterException: If event_id is not a string or is empty/whitespace.
        EventNotFoundError: If the event is not found.
    """
    # Validate event_id type and check for empty/whitespace
    if not isinstance(event_id, str):
        raise custom_errors.InvalidParameterException("event_id must be a string")
    
    if not event_id or not event_id.strip():
        raise custom_errors.InvalidParameterException("event_id cannot be empty or whitespace")
    
    if "Event" in DB and event_id in DB["Event"]:
        DB["Event"][event_id]["IsDeleted"] = True
    else:
        raise custom_errors.EventNotFoundError("Event not found")


@tool_spec(
    spec={
        'name': 'describe_event_layout',
        'description': 'Describes the layout of a specific event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'string',
                    'description': 'The ID of the event to describe the layout for.'
                }
            },
            'required': [
                'event_id'
            ]
        }
    }
)
def describeLayout(event_id: str) -> Dict[str, Any]:
    """
    Describes the layout of a specific event.

    Args:
        event_id (str): The ID of the event to describe the layout for.

    Returns:
        Dict[str, Any]: Event layout description with structure:
            - layout (str): Description of the event layout
            - event_id (str): The ID of the event being described
            - fields (list[str]): List of available fields for the event
                - Name (str): The name of the event
                - Subject (str): The subject of the event
                - StartDateTime (str): The start date and time of the event
                - EndDateTime (str): The end date and time of the event
                - Description (str): The description of the event
                - Location (str): The location of the event
                - IsAllDayEvent (bool): Whether the event is all day
                - OwnerId (str): The ID of the event owner
                - WhoId (str): The ID of the related contact
                - WhatId (str): The ID of the related record

    Raises:
        ValueError: If event ID is not provided.
        EventNotFound: If event ID is not found.
    """
    if not event_id:
        raise custom_errors.EventNotFound("Event ID is required")

    # Check if event exists
    if "Event" not in DB or event_id not in DB["Event"]:
        raise custom_errors.EventNotFound({"error": "Event not found"})
    
    # Return layout information for the specific event
    return {
        "layout": f"Event layout description for event {event_id}",
        "event_id": event_id,
        "fields": ["Name", "Subject", "StartDateTime", "EndDateTime", "Description", "Location", "IsAllDayEvent", "OwnerId", "WhoId", "WhatId"]
    }


@tool_spec(
    spec={
        'name': 'describe_event_object',
        'description': 'Describes the object (Event).',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def describeSObjects() -> List[Dict[str, Any]]:
        """
        Describes the object (Event).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing an sObject description. For the Event sObject, the list will contain a single item.
                The dictionary includes keys such as:
                - actionOverrides (List[Dict[str, Any]]): An array of action overrides for the object.
                    - formFactor (str): The environment to which the override applies (e.g., "Large", "Small").
                    - isAvailableInTouch (bool): Indicates if the override is available in the Salesforce mobile app.
                    - name (str): The name of the action that overrides the default action (e.g., "New", "Edit").
                    - pageId (str): The ID of the page (e.g., Visualforce or Lightning page) for the action override.
                    - url (str): The URL of the item used for the action override. Returns null for Lightning page overrides.
                - activateable (bool): Reserved for future use.
                - associateEntityType (str): The type of association to a parent object, such as "History". Null otherwise.
                - associateParentEntity (str): The parent object this object is associated with. Null otherwise.
                - childRelationships (List[Dict[str, Any]]): An array of child relationships.
                    - cascadeDelete (bool): Indicates if deleting the parent record cascades to child records.
                    - childSObject (str): The name of the child sObject.
                    - deprecatedAndHidden (bool): Reserved for future use.
                    - field (str): The API name of the foreign key field in the child sObject.
                    - junctionIdListNames (List[str]): The names of the lists of junction IDs.
                    - junctionReferenceTo (List[str]): A collection of object names that can be referenced.
                    - relationshipName (str): The name of the relationship, usually the plural of the child sObject name.
                    - restrictedDelete (bool): Indicates if parent deletion is restricted by a child record.
                - compactLayoutable (bool): Indicates if the object can be used in describeCompactLayouts().
                - createable (bool): Indicates if records can be created for this sObject via the create() call.
                - custom (bool): Indicates if the object is a custom object.
                - customSetting (bool): Indicates if the object is a custom setting.
                - dataTranslationEnabled (bool): Indicates if data translation is enabled for the object.
                - deepCloneable (bool): Reserved for future use.
                - defaultImplementation (str): Reserved for future use.
                - deletable (bool): Indicates if records can be deleted for this sObject via the delete() call.
                - deprecatedAndHidden (bool): Reserved for future use.
                - extendedBy (str): Reserved for future use.
                - extendsInterfaces (str): Reserved for future use.
                - feedEnabled (bool): Indicates if Chatter feeds are enabled for the object.
                - fields (List[Dict[str, Any]]): An array of field definitions for the object.
                    - autonumber (bool): Indicates if the field is an auto-number field.
                    - byteLength (int): The maximum size of the field in bytes.
                    - calculated (bool): Indicates if the field is a custom formula field.
                    - caseSensitive (bool): Indicates if the field is case-sensitive.
                    - controllerName (str): The name of the controlling field for a dependent picklist.
                    - createable (bool): Indicates if the field can be set during record creation.
                    - custom (bool): Indicates if the field is a custom field.
                    - defaultedOnCreate (bool): Indicates if the field is defaulted on creation.
                    - dependentPicklist (bool): Indicates if the picklist is dependent on another field.
                    - digits (int): For integer fields, the maximum number of digits.
                    - filterable (bool): Indicates if the field can be used in a WHERE clause.
                    - groupable (bool): Indicates if the field can be used in a GROUP BY clause.
                    - idLookup (bool): Indicates if the field can be used in an upsert() call.
                    - inlineHelpText (str): The field-level help hover text.
                    - label (str): The display label for the field.
                    - length (int): The maximum length of the field in Unicode characters.
                    - name (str): The API name of the field.
                    - nameField (bool): Indicates if this is the name field for the object.
                    - nillable (bool): Indicates if the field can have a null value.
                    - permissionable (bool): Indicates if FieldPermissions can be set for the field.
                    - picklistValues (List[Dict[str, Any]]): For picklists, an array of valid values.
                        - active (bool): Indicates if the picklist value is active.
                        - defaultValue (bool): Indicates if this is the default value.
                        - label (str): The display label for the value.
                        - value (str): The API value of the picklist entry.
                        - validFor (str): A base64-encoded bitmap indicating validity for dependent picklists.
                    - polymorphicForeignKey (bool): Indicates if the foreign key can refer to multiple object types.
                    - precision (int): For number fields, the total number of digits.
                    - relationshipName (str): For relationship fields, the name of the relationship.
                    - referenceTo (List[str]): For reference fields, the list of sObjects this field can point to.
                    - restrictedPicklist (bool): Indicates if the picklist's values are restricted to the defined set.
                    - scale (int): For number fields, the number of digits to the right of the decimal point.
                    - soapType (str): The SOAP API data type (e.g., "xsd:string", "tns:ID").
                    - sortable (bool): Indicates if a query can be sorted on this field.
                    - type (str): The data type of the field (e.g., "string", "id", "reference", "picklist").
                    - unique (bool): Indicates if the field value must be unique across all records.
                    - updateable (bool): Indicates if the field can be updated.
                - implementedBy (str): Reserved for future use.
                - implementsInterfaces (str): Reserved for future use.
                - isInterface (bool): Reserved for future use.
                - keyPrefix (str): The three-character prefix for the object's record IDs (e.g., "00U" for Event).
                - label (str): The display label for the object (e.g., "Event").
                - labelPlural (str): The plural display label for the object (e.g., "Events").
                - layoutable (bool): Indicates if the object supports the describeLayout() call.
                - mergeable (bool): Indicates if records of this object type can be merged.
                - mruEnabled (bool): Indicates if the Most Recently Used list is enabled for this object.
                - name (str): The API name of the object (e.g., "Event").
                - namedLayoutInfos (List[Dict[str, str]]): An array of named layouts available for the object.
                - networkScopeFieldName (str): The API name of the field that scopes the entity to an Experience Cloud site.
                - queryable (bool): Indicates if the object can be queried via the query() call.
                - recordTypeInfos (List[Dict[str, Any]]): An array of record types available for this object.
                    - available (bool): Indicates if the record type is available to the current user.
                    - defaultRecordTypeMapping (bool): Indicates if this is the default record type.
                    - developerName (str): The API name of the record type.
                    - master (bool): Indicates if this is the master record type.
                    - name (str): The display name of the record type.
                    - recordTypeId (str): The ID of the record type.
                - replicateable (bool): Indicates if the object can be replicated via getUpdated() and getDeleted().
                - retrieveable (bool): Indicates if records can be retrieved via the retrieve() call.
                - searchable (bool): Indicates if the object can be searched via the search() call.
                - searchLayoutable (bool): Indicates if search layouts can be described.
                - supportedScopes (List[Dict[str, str]]): The list of supported scopes for the object (e.g., "mine", "team").
                - triggerable (bool): Indicates if the object supports Apex triggers.
                - undeletable (bool): Indicates if records can be undeleted via the undelete() call.
                - updateable (bool): Indicates if records can be updated via the update() call.
                - urlDetail (str): The URL template to the read-only detail page for a record.
                - urlEdit (str): The URL template to the edit page for a record.
                - urlNew (str): The URL to the new/create page for the object.

        Raises:
            SObjectNotFoundError: If sObject 'Event' is not found in DB.
        """

        if 'EventSObject' not in DB:
            raise custom_errors.SObjectNotFoundError("sObject 'Event' not found in DB.")
        
        return DB['EventSObject']

@tool_spec(
    spec={
        'name': 'get_deleted_events',
        'description': 'Retrieves deleted events.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def getDeleted() -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves deleted events.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary containing deleted events with structure:
            - deleted: List of deleted event objects
                - Id (str): Unique identifier for the event
                - CreatedDate (str): ISO format timestamp of creation
                - IsDeleted (bool): Whether the event is deleted
                - SystemModstamp (str): Last modified timestamp
                - Name (Optional[str]): The name of the event, if provided
                - Subject (Optional[str]): The subject of the event, if provided
                - StartDateTime (Optional[str]): Start time of the event, if provided
                - EndDateTime (Optional[str]): End time of the event, if provided
                - Description (Optional[str]): Description of the event, if provided
                - Location (Optional[str]): Location of the event, if provided
                - IsAllDayEvent (Optional[bool]): Whether the event is all day, if provided
                - OwnerId (Optional[str]): ID of the event owner, if provided
                - WhoId (Optional[str]): ID of the related contact, if provided
                - WhatId (Optional[str]): ID of the related record, if provided
    """
    deleted_events  = []
    
    for event in DB["Event"].values():
        if event.get("IsDeleted", False):
            deleted_events.append(event)
    
    return {"deleted": deleted_events}


@tool_spec(
    spec={
        'name': 'get_updated_events',
        'description': """ Retrieves updated events between start_date_time and end_date_time.
        
        Retrieves updated events between start_date_time and end_date_time. The events are returned if the property SystemModstamp is between the provided dates on args. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'start_date_time': {
                    'type': 'string',
                    'description': 'Start time to look for updated events in ISO format.'
                },
                'end_date_time': {
                    'type': 'string',
                    'description': 'End time to look for updated events in ISO format.'
                }
            },
            'required': [
                'start_date_time',
                'end_date_time'
            ]
        }
    }
)
def getUpdated(start_date_time: str, end_date_time: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieves updated events between start_date_time and end_date_time.

    Retrieves updated events between start_date_time and end_date_time. The events are returned if the property SystemModstamp is between the provided dates on args.

    Args:
        start_date_time (str): Start time to look for updated events in ISO format.
        end_date_time (str): End time to look for updated events in ISO format.

    Returns:
        Dict[str, List[Dict[str, Any]]]: List of updated events with structure:
            - updated List[Dict[str, Any]]: List of updated event objects
                - Id (str): Unique identifier for the event
                - CreatedDate (str): ISO format timestamp of creation
                - IsDeleted (bool): Whether the event is deleted
                - SystemModstamp (str): Last modified timestamp
                - Name (Optional[str]): The name of the event, if provided
                - Subject (Optional[str]): The subject of the event, if provided
                - StartDateTime (Optional[str]): Start time of the event, if provided
                - EndDateTime (Optional[str]): End time of the event, if provided
                - Description (Optional[str]): Description of the event, if provided
                - Location (Optional[str]): Location of the event, if provided
                - IsAllDayEvent (Optional[bool]): Whether the event is all day, if provided
                - OwnerId (Optional[str]): ID of the event owner, if provided
                - WhoId (Optional[str]): ID of the related contact, if provided
                - WhatId (Optional[str]): ID of the related record, if provided
    """

    updated_events = []

    if "Event" in DB:  # type: ignore
        # Parse the string datetime parameters
        start_dt = datetime.fromisoformat(start_date_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date_time.replace('Z', '+00:00'))
        
        updated_events = [
            event for event in DB["Event"].values()
            if datetime.fromisoformat(event["SystemModstamp"].replace('Z', '+00:00')) >= start_dt and datetime.fromisoformat(event["SystemModstamp"].replace('Z', '+00:00')) <= end_dt
        ]

    return {"updated": updated_events}


@tool_spec(
    spec={
        'name': 'query_events',
        'description': 'Query events based on specified criteria.',
        'parameters': {
            'type': 'object',
            'properties': {
                'criteria': {
                    'type': 'object',
                    'description': 'Key-value pairs to filter events. All keys are optional for flexible filtering:',
                    'properties': {
                        'Subject': {
                            'type': 'string',
                            'description': 'The subject of the event.'
                        },
                        'IsAllDayEvent': {
                            'type': 'boolean',
                            'description': 'Whether the event is all day.'
                        },
                        'StartDateTime': {
                            'type': 'string',
                            'description': 'Start time of the event.'
                        },
                        'EndDateTime': {
                            'type': 'string',
                            'description': 'End time of the event.'
                        },
                        'Description': {
                            'type': 'string',
                            'description': 'Description of the event.'
                        },
                        'Location': {
                            'type': 'string',
                            'description': 'Location of the event.'
                        },
                        'OwnerId': {
                            'type': 'string',
                            'description': 'ID of the event owner.'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def query(criteria: Optional[Dict[str, Union[str, bool]]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Query events based on specified criteria.

    Args:
        criteria (Optional[Dict[str, Union[str, bool]]]): 
            Key-value pairs to filter events. All keys are optional for flexible filtering:
                - Subject (Optional[str]): The subject of the event.
                - IsAllDayEvent (Optional[bool]): Whether the event is all day.
                - StartDateTime (Optional[str]): Start time of the event.
                - EndDateTime (Optional[str]): End time of the event.
                - Description (Optional[str]): Description of the event.
                - Location (Optional[str]): Location of the event.
                - OwnerId (Optional[str]): ID of the event owner.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary with:
            - "results" (List[Dict[str, Any]]): List of event objects matching the criteria.

    Raises:
        ValidationError: If 'criteria' is provided and is not a dictionary,
                                  or if any of its known keys like "Subject",
                                  "IsAllDayEvent", or "StartDateTime"
                                  do not match their expected types.
    """
    # --- Input Validation Logic ---
    if criteria is not None:
        # First validate that criteria is a dictionary
        if not isinstance(criteria, dict):
            raise ValidationError.from_exception_data(
                "QueryCriteriaModel",
                [{"loc": (), "input": criteria, "type": "dict_type"}]
            )
        
        # Validate that all keys are strings
        for key in criteria.keys():
            if not isinstance(key, str):
                raise ValidationError.from_exception_data(
                    "QueryCriteriaModel",
                    [{"loc": (key,), "input": key, "type": "string_type"}]
                )
        
        # Then validate the dictionary contents using Pydantic
        try:
            _ = QueryCriteriaModel(**criteria)
        except ValidationError as e:
            # Re-raise Pydantic's validation error to be handled by the caller.
            raise e
    # --- End of Input Validation Logic ---

    results = []

    if "Event" in DB:  # type: ignore
        for event in DB["Event"].values():  # type: ignore
            # Skip deleted events
            if event.get("IsDeleted", False):
                continue

            if criteria is None:
                results.append(event)
            else:
                match = True
                for key, value in criteria.items():
                    if key not in event:
                        match = False
                        break
                    
                    # Case-insensitive comparison for string values
                    if isinstance(value, str) and isinstance(event[key], str):
                        if event[key].lower() != value.lower():
                            match = False
                            break
                    else:
                        # Direct comparison for non-string values (bool, int, etc.)
                        if event[key] != value:
                            match = False
                            break
                if match:
                    results.append(event)
    
    return {"results": results}

def _event_matches_criteria(event: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
    """
    Check if an event matches the given criteria.
    
    Args:
        event (dict): Event object to check
        criteria (dict): Query criteria
        
    Returns:
        bool: True if event matches all criteria, False otherwise
    """
    # Skip deleted events
    if event.get("IsDeleted", False):
        return False
        
    for field_name, expected_value in criteria.items():
        # Skip if field doesn't exist in event
        if field_name not in event:
            return False
        
        # Skip if values don't match
        actual_value = event[field_name]
        if actual_value != expected_value:
            return False
    
    # All criteria matched
    return True



@tool_spec(
    spec={
        'name': 'retrieve_event_details',
        'description': 'Retrieves details of a specific event by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'string',
                    'description': 'The ID of the event to retrieve.'
                }
            },
            'required': [
                'event_id'
            ]
        }
    }
)
def retrieve(event_id: str) -> Dict[str, Any]:
    """
    Retrieves details of a specific event by its ID.

    Args:
        event_id (str): The ID of the event to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing the details of the event with the following keys:
            - Id (str): Unique identifier for the event
            - CreatedDate (str): ISO format timestamp of creation
            - IsDeleted (bool): Whether the event is deleted
            - SystemModstamp (str): Last modified timestamp
            - Name (Optional[str]): The name of the event, if provided
            - Subject (Optional[str]): The subject of the event, if provided
            - StartDateTime (Optional[str]): Start time of the event, if provided
            - EndDateTime (Optional[str]): End time of the event, if provided
            - Description (Optional[str]): Description of the event, if provided
            - Location (Optional[str]): Location of the event, if provided
            - IsAllDayEvent (Optional[bool]): Whether the event is all day, if provided
            - OwnerId (Optional[str]): ID of the event owner, if provided
            - WhoId (Optional[str]): ID of the related contact, if provided
            - WhatId (Optional[str]): ID of the related record, if provided

    Raises:
        ValueError: If the input data is invalid.
        EventNotFoundError: If the event does not exist in the database.
    """
    try:
        RetrieveEventInput(event_id=event_id)
    except ValidationError as e:
        raise e

    if "Event" not in DB or event_id not in DB["Event"]:
        raise EventNotFoundError("Event not found")

    response = DB["Event"][event_id]
    return response


@handle_api_errors()
@tool_spec(
    spec={
        'name': 'search_events',
        'description': """ Searches for events based on specified search criteria.
        
        This function performs a case-insensitive search across all event fields.
        The search looks for the search term as a substring within any field value.
        If the search term is empty or contains only whitespace, all events are returned. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'search_term': {
                    'type': 'string',
                    'description': """ The term to search for in event fields. If an empty string is provided, 
                    all events will be returned. """
                }
            },
            'required': [
                'search_term'
            ]
        }
    }
)
def search(search_term: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Searches for events based on specified search criteria.
    
    This function performs a case-insensitive search across all event fields.
    The search looks for the search term as a substring within any field value.
    If the search term is empty or contains only whitespace, all events are returned.
    
    Args:
        search_term (str): The term to search for in event fields. If an empty string is provided, 
                          all events will be returned.

    Returns:
        Dict[str, List[Dict[str, Any]]]: List of events containing the search term with structure:
            - results (list): List of event objects containing the search term, or all events if 
                             search_term is empty

    Raises:
        ValueError: If search_term is None
        TypeError: If search_term is not a string
    
    Examples:
        >>> search("meeting")
        {'results': [{'Id': '123', 'Subject': 'Team Meeting', ...}]}
        
        >>> search("")  # Returns all events
        {'results': [{'Id': '123', 'Subject': 'Team Meeting', ...}, ...]}
        
        >>> search("   ")  # Returns all events (whitespace-only)
        {'results': [{'Id': '123', 'Subject': 'Team Meeting', ...}, ...]}
    """
    # Use Pydantic model for input validation
    try:
        validated_search_term = SearchTermModel.validate_search_term(search_term)
    except (ValueError, TypeError) as e:
        # Re-raise validation errors with clear messages
        raise e
    
    results = []
    
    # Check if Event table exists and is properly structured
    if "Event" not in DB or not isinstance(DB["Event"], dict):
        return {"results": results}
    
    # If search term is empty after normalization, return all events
    if not validated_search_term:
        results = list(DB["Event"].values())
    else:
        # Search through events more efficiently
        for event in DB["Event"].values():
            if not isinstance(event, dict):
                continue
                
            # Search through event fields more efficiently
            for field_name, field_value in event.items():
                if field_value is None:
                    continue
                    
                # Convert field value to string and search case-insensitively
                field_value_str = str(field_value).lower()
                if validated_search_term in field_value_str:
                    results.append(event)
                    break  # Found a match, no need to check other fields for this event
    
    return {"results": results}


@tool_spec(
    spec={
        'name': 'undelete_event',
        'description': """ Restores a deleted event.
        
        This function restores a deleted event by setting its IsDeleted flag to False. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'string',
                    'description': 'The ID of the event to undelete.'
                }
            },
            'required': [
                'event_id'
            ]
        }
    }
)
def undelete(event_id: str) -> Dict[str, Any]:
    """
    Restores a deleted event.

    This function restores a deleted event by setting its IsDeleted flag to False.
    
    Args:
        event_id (str): The ID of the event to undelete.

    Returns:
        Dict[str, Any]: The event object if found, or error dict with structure:
            - Id (str): The ID of the event being undeleted
            - success (bool): Indicates whether the undelete was successful (True) or not (False).
    Raises:
        EventNotFoundError: If the event is not found.
        InvalidArgumentError: If the event_id is not a string.
    """
    
    if event_id is None or not isinstance(event_id, str):
        raise custom_errors.InvalidArgumentError("event_id must be a string.")

    if "Event" in DB and event_id in DB["Event"]:
        DB["Event"][event_id]["IsDeleted"] = False
        return UndeleteEventOutput(Id=event_id, success=True)
    else:
        raise custom_errors.EventNotFoundError("Event not found")


@tool_spec(
    spec={
        'name': 'update_event',
        'description': 'Updates an existing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'string',
                    'description': 'The ID of the event to update.'
                },
                'Name': {
                    'type': 'string',
                    'description': 'The name of the event.'
                },
                'Subject': {
                    'type': 'string',
                    'description': 'The subject of the event.'
                },
                'StartDateTime': {
                    'type': 'string',
                    'description': 'Start time of the event.'
                },
                'EndDateTime': {
                    'type': 'string',
                    'description': 'End time of the event.'
                },
                'Description': {
                    'type': 'string',
                    'description': 'Description of the event.'
                },
                'Location': {
                    'type': 'string',
                    'description': 'Location of the event.'
                },
                'IsAllDayEvent': {
                    'type': 'boolean',
                    'description': 'Whether the event is all day.'
                },
                'OwnerId': {
                    'type': 'string',
                    'description': 'ID of the event owner.'
                },
                'WhoId': {
                    'type': 'string',
                    'description': 'ID of the related contact.'
                },
                'WhatId': {
                    'type': 'string',
                    'description': 'ID of the related record.'
                }
            },
            'required': [
                'event_id'
            ]
        }
    }
)
def update(
    event_id: str,
    Name: Optional[str] = None,
    Subject: Optional[str] = None,
    StartDateTime: Optional[str] = None,
    EndDateTime: Optional[str] = None,
    Description: Optional[str] = None,
    Location: Optional[str] = None,
    IsAllDayEvent: Optional[bool] = None,
    OwnerId: Optional[str] = None,
    WhoId: Optional[str] = None,
    WhatId: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates an existing event.

    Args:
        event_id (str): The ID of the event to update.
        Name (Optional[str]): The name of the event.
        Subject (Optional[str]): The subject of the event.
        StartDateTime (Optional[str]): Start time of the event.
        EndDateTime (Optional[str]): End time of the event.
        Description (Optional[str]): Description of the event.
        Location (Optional[str]): Location of the event.
        IsAllDayEvent (Optional[bool]): Whether the event is all day.
        OwnerId (Optional[str]): ID of the event owner.
        WhoId (Optional[str]): ID of the related contact.
        WhatId (Optional[str]): ID of the related record.

    Returns:
        Dict[str, Any]: The updated event object with the following fields:
            - Id (str): Unique identifier for the event
            - CreatedDate (str): ISO format timestamp of creation
            - IsDeleted (bool): Whether the event is deleted
            - SystemModstamp (str): Last modified timestamp (updated to current time)
            - Name (Optional[str]): The name of the event, if provided
            - Subject (Optional[str]): The subject of the event, if provided
            - StartDateTime (Optional[str]): Start time of the event, if provided
            - EndDateTime (Optional[str]): End time of the event, if provided
            - Description (Optional[str]): Description of the event, if provided
            - Location (Optional[str]): Location of the event, if provided
            - IsAllDayEvent (Optional[bool]): Whether the event is all day, if provided
            - OwnerId (Optional[str]): ID of the event owner, if provided
            - WhoId (Optional[str]): ID of the related contact, if provided
            - WhatId (Optional[str]): ID of the related record, if provided

    Raises:
        TypeError: If `event_id` is not a string.
        EventNotFoundError: If the event with the given event_id does not exist.
        ValidationError: If any of the provided fields have invalid data types.
    """
    # 1. Validate non-dictionary arguments
    if not isinstance(event_id, str):
        raise TypeError("event_id must be a string.")

    # 2. Check if event exists
    if "Event" not in DB or event_id not in DB["Event"]:
        raise EventNotFoundError(f"Event with id '{event_id}' not found")

    # 3. Validate dictionary arguments (kwargs) using Pydantic
    update_properties = {
        "Name": Name,
        "Subject": Subject,
        "StartDateTime": StartDateTime,
        "EndDateTime": EndDateTime,
        "Description": Description,
        "Location": Location,
        "IsAllDayEvent": IsAllDayEvent,
        "OwnerId": OwnerId,
        "WhoId": WhoId,
        "WhatId": WhatId
    }
    
    # Validate and get the validated model
    validated_data = EventUpdateKwargsModel(**update_properties)
    
    # Get the event from DB
    event = DB["Event"][event_id]

    # Update only provided fields using validated data
    # model_dump(exclude_none=True) returns only fields that were explicitly set
    updates = validated_data.model_dump(exclude_none=True)
    for field, value in updates.items():
        event[field] = value

    event["SystemModstamp"] = datetime.now().isoformat()
    return event


@tool_spec(
    spec={
        'name': 'upsert_event',
        'description': 'Creates or updates an event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'Name': {
                    'type': 'string',
                    'description': 'The name of the event.'
                },
                'Id': {
                    'type': 'string',
                    'description': 'Event ID (required for update).'
                },
                'Subject': {
                    'type': 'string',
                    'description': 'The subject of the event.'
                },
                'StartDateTime': {
                    'type': 'string',
                    'description': 'Event start date and time in ISO format.'
                },
                'EndDateTime': {
                    'type': 'string',
                    'description': 'Event end date and time in ISO format.'
                },
                'Description': {
                    'type': 'string',
                    'description': 'Description of the event.'
                },
                'Location': {
                    'type': 'string',
                    'description': 'Location of the event.'
                },
                'IsAllDayEvent': {
                    'type': 'boolean',
                    'description': 'Whether the event is all day.'
                },
                'OwnerId': {
                    'type': 'string',
                    'description': 'ID of the event owner.'
                },
                'WhoId': {
                    'type': 'string',
                    'description': 'ID of the related contact.'
                },
                'WhatId': {
                    'type': 'string',
                    'description': 'ID of the related record.'
                }
            },
            'required': []
        }
    }
)
def upsert(
    Name: Optional[str] = None,
    Id: Optional[str] = None,
    Subject: Optional[str] = None,
    StartDateTime: Optional[str] = None,
    EndDateTime: Optional[str] = None,
    Description: Optional[str] = None,
    Location: Optional[str] = None,
    IsAllDayEvent: Optional[bool] = None,
    OwnerId: Optional[str] = None,
    WhoId: Optional[str] = None,
    WhatId: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates or updates an event.

    Args:
        Name (Optional[str]): The name of the event.
        Id (Optional[str]): Event ID (required for update).
        Subject (Optional[str]): The subject of the event.
        StartDateTime (Optional[str]): Event start date and time in ISO format.
        EndDateTime (Optional[str]): Event end date and time in ISO format.
        Description (Optional[str]): Description of the event.
        Location (Optional[str]): Location of the event.
        IsAllDayEvent (Optional[bool]): Whether the event is all day.
        OwnerId (Optional[str]): ID of the event owner.
        WhoId (Optional[str]): ID of the related contact.
        WhatId (Optional[str]): ID of the related record.

    Returns:
        Dict[str, Any]: The created or updated event object with the following fields:
            - Id (str): Unique identifier for the event
            - CreatedDate (str): ISO format timestamp of creation
            - IsDeleted (bool): Whether the event is deleted
            - SystemModstamp (str): Last modified timestamp
            - Name (Optional[str]): The name of the event, if provided
            - Subject (Optional[str]): The subject of the event, if provided
            - StartDateTime (Optional[str]): Start time of the event, if provided
            - EndDateTime (Optional[str]): End time of the event, if provided
            - Description (Optional[str]): Description of the event, if provided
            - Location (Optional[str]): Location of the event, if provided
            - IsAllDayEvent (Optional[bool]): Whether the event is all day, if provided
            - OwnerId (Optional[str]): ID of the event owner, if provided
            - WhoId (Optional[str]): ID of the related contact, if provided
            - WhatId (Optional[str]): ID of the related record, if provided

    Raises:
        pydantic.ValidationError: 
                When updating an Event: If any of the known fields in are provided with an invalid data type.               
                When creating an Event: If event_attributes contain fields not defined in EventInputModel or if provided fields do not match their expected types (e.g., 'Subject' is not a string, 'IsAllDayEvent' is not a boolean).
    """
    # --- Input Validation Start ---
    upsert_attributes = {
        "Name": Name,
        "Id": Id,
        "Subject": Subject,
        "StartDateTime": StartDateTime,
        "EndDateTime": EndDateTime,
        "Description": Description,
        "Location": Location,
        "IsAllDayEvent": IsAllDayEvent,
        "OwnerId": OwnerId,
        "WhoId": WhoId,
        "WhatId": WhatId
    }
    
    EventUpsertModel(**upsert_attributes)

    # --- Input Validation End ---

    if Id is not None and Id in DB.get("Event", {}):
        return update(
            Id,
            Name=Name,
            Subject=Subject,
            StartDateTime=StartDateTime,
            EndDateTime=EndDateTime,
            Description=Description,
            Location=Location,
            IsAllDayEvent=IsAllDayEvent,
            OwnerId=OwnerId,
            WhoId=WhoId,
            WhatId=WhatId,
        )
    else:
        return create(
            Name=Name,
            Subject=Subject,
            StartDateTime=StartDateTime,
            EndDateTime=EndDateTime,
            Description=Description,
            Location=Location,
            IsAllDayEvent=IsAllDayEvent,
            OwnerId=OwnerId,
            WhoId=WhoId,
            WhatId=WhatId,
        )
