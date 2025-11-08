from common_utils.tool_spec_decorator import tool_spec
# APIs/salesforce/Task.py
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import uuid
import re
from salesforce.SimulationEngine.models import GetUpdatedInput, RetrieveTaskInput, TaskCreateModel, TaskCriteriaModel, TaskUpsertModel, UndeleteTaskOutput, GetDeletedResult, DeletedRecord, GetDeletedInput, TaskUpdateModel
from salesforce.SimulationEngine.custom_errors import (
    TaskNotFoundError, InvalidDateFormatError, InvalidDateTypeError, 
    InvalidReplicationDateError, ExceededIdLimitError, InvalidSObjectTypeError, 
    UnsupportedSObjectTypeError
)
from salesforce.SimulationEngine.db import DB
from pydantic import ValidationError
from salesforce.SimulationEngine import custom_errors
"""
Represents the Task resource in the API.
"""

@tool_spec(
    spec={
        'name': 'create_task',
        'description': """ Creates a new task with all standard Salesforce Task fields and comprehensive validation.
        
        This function implements strict validation including semantic consistency checks,
        input sanitization, referential integrity validation, and prevention of contradictory states. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'Priority': {
                    'type': 'string',
                    'description': 'Priority of the task (required). Must be one of: "High", "Medium", "Low".'
                },
                'Status': {
                    'type': 'string',
                    'description': 'Status of the task (required). Must be one of: "Not Started", "In Progress", "Completed", "Waiting", "Deferred", "Open", "Closed".'
                },
                'Id': {
                    'type': 'string',
                    'description': 'Custom ID for the task. Must be 15-18 alphanumeric characters if provided. If not provided, a UUID will be generated.'
                },
                'Name': {
                    'type': 'string',
                    'description': 'The name of the task. Maximum length: 80 characters.'
                },
                'Subject': {
                    'type': 'string',
                    'description': 'The subject of the task. Maximum length: 255 characters.'
                },
                'Description': {
                    'type': 'string',
                    'description': 'Description of the task. Maximum length: 32,000 characters.'
                },
                'ActivityDate': {
                    'type': 'string',
                    'description': 'Due date of the task in ISO format (YYYY-MM-DD).'
                },
                'DueDate': {
                    'type': 'string',
                    'description': 'Alternative field for task due date in ISO format (YYYY-MM-DD).'
                },
                'OwnerId': {
                    'type': 'string',
                    'description': 'ID of the task owner. Must be 15-18 alphanumeric characters if provided.'
                },
                'WhoId': {
                    'type': 'string',
                    'description': 'ID of the related contact. Must be 15-18 alphanumeric characters if provided. Referential integrity checked.'
                },
                'WhatId': {
                    'type': 'string',
                    'description': 'ID of the related record. Must be 15-18 alphanumeric characters if provided. Referential integrity checked.'
                },
                'IsReminderSet': {
                    'type': 'boolean',
                    'description': 'Whether reminder is set.'
                },
                'ReminderDateTime': {
                    'type': 'string',
                    'description': 'Reminder date and time in ISO format (YYYY-MM-DDTHH:MM:SS).'
                },
                'CallDurationInSeconds': {
                    'type': 'integer',
                    'description': 'Duration of call in seconds. Must be non-negative.'
                },
                'CallType': {
                    'type': 'string',
                    'description': 'Type of call.'
                },
                'CallObject': {
                    'type': 'string',
                    'description': 'Call object identifier.'
                },
                'CallDisposition': {
                    'type': 'string',
                    'description': 'Call disposition.'
                },
                'IsRecurrence': {
                    'type': 'boolean',
                    'description': 'Whether task is recurring.'
                },
                'RecurrenceType': {
                    'type': 'string',
                    'description': 'Type of recurrence. Required if IsRecurrence is True.'
                },
                'RecurrenceInterval': {
                    'type': 'integer',
                    'description': 'Recurrence interval. Must be positive if provided.'
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
                'CompletedDateTime': {
                    'type': 'string',
                    'description': 'Date and time when task was completed. Must be consistent with Status.'
                },
                'IsClosed': {
                    'type': 'boolean',
                    'description': 'Whether the task is closed. Must be consistent with Status.'
                },
                'IsHighPriority': {
                    'type': 'boolean',
                    'description': 'Whether the task is high priority. Must be consistent with Priority.'
                },
                'IsArchived': {
                    'type': 'boolean',
                    'description': 'Whether the task is archived.'
                },
                'TaskSubtype': {
                    'type': 'string',
                    'description': 'Subtype of the task.'
                }
            },
            'required': [
                'Priority',
                'Status'
            ]
        }
    }
)
def create(
    Status: str,  # Required per Salesforce docs
    Priority: str,  # Required per Salesforce docs
    Id: Optional[str] = None,
    Name: Optional[str] = None,
    Subject: Optional[str] = None,
    Description: Optional[str] = None,
    ActivityDate: Optional[str] = None,
    DueDate: Optional[str] = None,
    OwnerId: Optional[str] = None,
    WhoId: Optional[str] = None,
    WhatId: Optional[str] = None,
    IsReminderSet: Optional[bool] = None,
    ReminderDateTime: Optional[str] = None,
    # Call-related fields
    CallDurationInSeconds: Optional[int] = None,
    CallType: Optional[str] = None,
    CallObject: Optional[str] = None,
    CallDisposition: Optional[str] = None,
    # Recurrence fields
    IsRecurrence: Optional[bool] = None,
    RecurrenceType: Optional[str] = None,
    RecurrenceInterval: Optional[int] = None,
    RecurrenceEndDateOnly: Optional[str] = None,
    RecurrenceMonthOfYear: Optional[int] = None,
    RecurrenceDayOfWeekMask: Optional[int] = None,
    RecurrenceDayOfMonth: Optional[int] = None,
    RecurrenceInstance: Optional[str] = None,
    # Status and completion fields
    CompletedDateTime: Optional[str] = None,
    IsClosed: Optional[bool] = None,
    IsHighPriority: Optional[bool] = None,
    IsArchived: Optional[bool] = None,
    TaskSubtype: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a new task with all standard Salesforce Task fields and comprehensive validation.

    This function implements strict validation including semantic consistency checks,
    input sanitization, referential integrity validation, and prevention of contradictory states.

    Args:
        Priority (str): Priority of the task (required). Must be one of: "High", "Medium", "Low".
        Status (str): Status of the task (required). Must be one of: "Not Started", "In Progress", "Completed", "Waiting", "Deferred", "Open", "Closed".
        Id (Optional[str]): Custom ID for the task. Must be 15-18 alphanumeric characters if provided. If not provided, a UUID will be generated.
        Name (Optional[str]): The name of the task. Maximum length: 80 characters.
        Subject (Optional[str]): The subject of the task. Maximum length: 255 characters.
        Description (Optional[str]): Description of the task. Maximum length: 32,000 characters.
        ActivityDate (Optional[str]): Due date of the task in ISO format (YYYY-MM-DD).
        DueDate (Optional[str]): Alternative field for task due date in ISO format (YYYY-MM-DD).
        OwnerId (Optional[str]): ID of the task owner. Must be 15-18 alphanumeric characters if provided.
        WhoId (Optional[str]): ID of the related contact. Must be 15-18 alphanumeric characters if provided. Referential integrity checked.
        WhatId (Optional[str]): ID of the related record. Must be 15-18 alphanumeric characters if provided. Referential integrity checked.
        IsReminderSet (Optional[bool]): Whether reminder is set.
        ReminderDateTime (Optional[str]): Reminder date and time in ISO format (YYYY-MM-DDTHH:MM:SS).
        CallDurationInSeconds (Optional[int]): Duration of call in seconds. Must be non-negative.
        CallType (Optional[str]): Type of call.
        CallObject (Optional[str]): Call object identifier.
        CallDisposition (Optional[str]): Call disposition.
        IsRecurrence (Optional[bool]): Whether task is recurring.
        RecurrenceType (Optional[str]): Type of recurrence. Required if IsRecurrence is True.
        RecurrenceInterval (Optional[int]): Recurrence interval. Must be positive if provided.
        RecurrenceEndDateOnly (Optional[str]): End date for recurrence.
        RecurrenceMonthOfYear (Optional[int]): Month of year for recurrence (1-12).
        RecurrenceDayOfWeekMask (Optional[int]): Day of week mask for recurrence.
        RecurrenceDayOfMonth (Optional[int]): Day of month for recurrence (1-31).
        RecurrenceInstance (Optional[str]): Recurrence instance.
        CompletedDateTime (Optional[str]): Date and time when task was completed. Must be consistent with Status.
        IsClosed (Optional[bool]): Whether the task is closed. Must be consistent with Status.
        IsHighPriority (Optional[bool]): Whether the task is high priority. Must be consistent with Priority.
        IsArchived (Optional[bool]): Whether the task is archived.
        TaskSubtype (Optional[str]): Subtype of the task.

    Returns:
        Dict[str, Any]: The created task object containing the following fields:
            Id (str): Unique identifier for the task (either provided or auto-generated)
            CreatedDate (str): ISO format timestamp of creation
            IsDeleted (bool): Whether the task is deleted (always False for new tasks)
            SystemModstamp (str): Last modified timestamp (same as CreatedDate for new tasks)
            Priority (str): Priority of the task
            Status (str): Status of the task
            Name (Optional[str]): The name of the task, if provided
            Subject (Optional[str]): The subject of the task, if provided
            Description (Optional[str]): Description of the task, if provided
            ActivityDate (Optional[str]): Due date of the task in ISO format (YYYY-MM-DD), if provided
            DueDate (Optional[str]): Alternative due date field in ISO format (YYYY-MM-DD), if provided
            OwnerId (Optional[str]): ID of the task owner, if provided
            WhoId (Optional[str]): ID of the related contact, if provided
            WhatId (Optional[str]): ID of the related record, if provided
            IsReminderSet (Optional[bool]): Whether reminder is set, if provided
            ReminderDateTime (Optional[str]): Reminder date and time in ISO format (YYYY-MM-DDTHH:MM:SS), if provided
            CallDurationInSeconds (Optional[int]): Duration of call in seconds, if provided
            CallType (Optional[str]): Type of call, if provided
            CallObject (Optional[str]): Call object identifier, if provided
            CallDisposition (Optional[str]): Call disposition, if provided
            IsRecurrence (Optional[bool]): Whether task is recurring, if provided
            RecurrenceType (Optional[str]): Type of recurrence, if provided
            RecurrenceInterval (Optional[int]): Recurrence interval, if provided
            RecurrenceEndDateOnly (Optional[str]): End date for recurrence, if provided
            RecurrenceMonthOfYear (Optional[int]): Month of year for recurrence (1-12), if provided
            RecurrenceDayOfWeekMask (Optional[int]): Day of week mask for recurrence, if provided
            RecurrenceDayOfMonth (Optional[int]): Day of month for recurrence (1-31), if provided
            RecurrenceInstance (Optional[str]): Recurrence instance, if provided
            CompletedDateTime (Optional[str]): Date and time when task was completed, if provided
            IsClosed (Optional[bool]): Whether the task is closed, if provided
            IsHighPriority (Optional[bool]): Whether the task is high priority, if provided
            IsArchived (Optional[bool]): Whether the task is archived, if provided
            TaskSubtype (Optional[str]): Subtype of the task, if provided

    Raises:
        TaskDuplicateIdError: If attempting to create a task with an ID that already exists.
        TaskSemanticValidationError: If the task data is logically inconsistent (e.g., completed task with future reminder).
        TaskContradictoryStateError: If the task contains contradictory field values (e.g., Low priority with IsHighPriority=True).
        TaskInputSanitizationError: If input contains potentially harmful content that cannot be sanitized.
        TaskNumericValidationError: If numeric fields have invalid values (e.g., negative CallDurationInSeconds).
        TaskReferentialIntegrityError: If WhatId or WhoId point to non-existent records.
        ValueError: If basic field validation fails (format, length, required fields, etc.).
            - If Priority is None, empty string, or not one of the allowed values ("High", "Medium", "Low").
            - If Status is None, empty string, or not one of the allowed values ("Not Started", "In Progress", "Completed", "Waiting", "Deferred", "Open", "Closed").
            - If ActivityDate is not in the correct ISO format (YYYY-MM-DD) or represents an invalid date.
            - If DueDate is not in the correct ISO format (YYYY-MM-DD) or represents an invalid date.
            - If ReminderDateTime is not in the correct ISO format (YYYY-MM-DDTHH:MM:SS) or represents an invalid datetime.
            - If Id is not 15-18 alphanumeric characters.
            - If OwnerId is not 15-18 alphanumeric characters.
            - If WhoId is not 15-18 alphanumeric characters.
            - If WhatId is not 15-18 alphanumeric characters.
            - If Name exceeds the maximum length of 80 characters.
            - If Subject exceeds the maximum length of 255 characters.
            - If Description exceeds the maximum length of 32,000 characters.
        ValidationError: If Pydantic model validation fails.
    """
    # Create task data for Pydantic validation
    task_data = {
        "Priority": Priority,
        "Status": Status,
        "Id": Id,
        "Name": Name,
        "Subject": Subject,
        "Description": Description,
        "ActivityDate": ActivityDate,
        "DueDate": DueDate,
        "OwnerId": OwnerId,
        "WhoId": WhoId,
        "WhatId": WhatId,
        "IsReminderSet": IsReminderSet,
        "ReminderDateTime": ReminderDateTime,
        "CallDurationInSeconds": CallDurationInSeconds,
        "CallType": CallType,
        "CallObject": CallObject,
        "CallDisposition": CallDisposition,
        "IsRecurrence": IsRecurrence,
        "RecurrenceType": RecurrenceType,
        "RecurrenceInterval": RecurrenceInterval,
        "RecurrenceEndDateOnly": RecurrenceEndDateOnly,
        "RecurrenceMonthOfYear": RecurrenceMonthOfYear,
        "RecurrenceDayOfWeekMask": RecurrenceDayOfWeekMask,
        "RecurrenceDayOfMonth": RecurrenceDayOfMonth,
        "RecurrenceInstance": RecurrenceInstance,
        "CompletedDateTime": CompletedDateTime,
        "IsClosed": IsClosed,
        "IsHighPriority": IsHighPriority,
        "IsArchived": IsArchived,
        "TaskSubtype": TaskSubtype
    }
    
    # Remove None values for Pydantic validation
    task_data = {k: v for k, v in task_data.items() if v is not None}

    # Handle ID generation and duplicate checking
    if Id is not None:
        TaskCreateModel.check_duplicate_id(Id)
    else:
        Id = TaskCreateModel.generate_unique_id()
        task_data["Id"] = Id

    # Perform referential integrity checks
    if WhatId is not None:
        TaskCreateModel.check_referential_integrity(WhatId, "WhatId")
    if WhoId is not None:
        TaskCreateModel.check_referential_integrity(WhoId, "WhoId")
    
    # Comprehensive validation using the model
    validated_task = TaskCreateModel.create_and_validate(**task_data)

    # Create task object with validated data
    validated_data = validated_task.model_dump()

    # Create the new task
    new_task = {
        "Id": Id if Id is not None else str(uuid.uuid4()),
        "CreatedDate": datetime.now().isoformat(),
        "IsDeleted": False,
        "SystemModstamp": datetime.now().isoformat()
    }

    # Add all validated fields to the task, excluding None values
    for field, value in validated_task.model_dump(exclude_none=True).items():
        new_task[field] = value

    DB.setdefault("Task", {})
    DB["Task"][new_task["Id"]] = new_task

    return new_task


@tool_spec(
    spec={
        'name': 'delete_task',
        'description': 'Deletes a task.',
        'parameters': {
            'type': 'object',
            'properties': {
                'task_id': {
                    'type': 'string',
                    'description': 'The ID of the task to delete.'
                }
            },
            'required': [
                'task_id'
            ]
        }
    }
)
def delete(task_id: str) -> None:
    """
    Deletes a task.

    Args:
        task_id (str): The ID of the task to delete.

    Returns:
        None: No return value on success.
    
    Raises:
        InvalidParameterException: If task_id is not a string or is empty/whitespace.
        TaskNotFoundError: If the task is not found.
    """
    # Validate task_id type and check for empty/whitespace
    if not isinstance(task_id, str):
        raise custom_errors.InvalidParameterException("task_id must be a string")
    
    if not task_id or not task_id.strip():
        raise custom_errors.InvalidParameterException("task_id cannot be empty or whitespace")
    
    if "Task" in DB and task_id in DB["Task"]:
        DB["Task"][task_id]["IsDeleted"] = True
        # Update the SystemModstamp field to the current date and time
        DB["Task"][task_id]["SystemModstamp"] = datetime.utcnow().isoformat() + "Z"

        # Store the task in DeletedTasks collection with deletion timestamp
        deleted_task = DB["Task"][task_id].copy()
        deleted_task["deletedDate"] = datetime.utcnow().isoformat() + "Z"
        
        # Initialize DeletedTasks collection if it doesn't exist
        if "DeletedTasks" not in DB:
            DB["DeletedTasks"] = {}
        
        DB["DeletedTasks"][task_id] = deleted_task
        
        # Remove from active tasks
        del DB["Task"][task_id]
    else:
        raise custom_errors.TaskNotFoundError("Task not found")


@tool_spec(
    spec={
        'name': 'describe_task_layout',
        'description': """ Describes the layout of a specific Task.
        
        This function is used to describe the layout of a specific Task.
        It is used to get the layout of a specific Task. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'layout_id': {
                    'type': 'string',
                    'description': 'The ID of the Task layout to describe.'
                }
            },
            'required': [
                'layout_id'
            ]
        }
    }
)
def describeLayout(layout_id: str) -> Dict[str, Any]:
    """
    Describes the layout of a specific Task.

    This function is used to describe the layout of a specific Task.
    It is used to get the layout of a specific Task.

    Args:
        layout_id (str): The ID of the Task layout to describe.
    Returns:
        Dict[str, Any]: Task layout description with structure:
            - layout (dict(str, Any)): Task layout description with structure:
                - description (str): Description of the Task layout
                - id (str): The ID of the Task layout
                - name (str): The name of the Task layout
                - label (str): The label of the Task layout
                - editLayoutSections (list[dict(str, Any)]): List of edit layout sections with structure:
                    - heading (str): The heading of the edit layout section
                    - columns (int): The number of columns in the edit layout section
                    - useFfPage (bool): Whether the edit layout section uses a custom page
                    - rows (list[list[dict(str, Any)]]): List of rows in the edit layout section with structure:
                        - [list[dict(str, Any)]]: Row with structure:
                            - [dict(str, Any)]: Field with structure:
                                - behavior (str): The behavior of the field
                                - editable (bool): Whether the field is editable
                                - label (str): The label of the field
                                - readable (bool): Whether the field is readable
                                - required (bool): Whether the field is required
                                - field (str): The field name
                - detailLayoutSections (list[dict(str, Any)]): List of detail layout sections with structure:
                    - heading (str): The heading of the detail layout section
                    - columns (int): The number of columns in the detail layout section
                    - useFfPage (bool): Whether the detail layout section uses a custom page
                    - rows (list[list[dict(str, Any)]]): List of rows in the detail layout section with structure:
                        - [list[dict(str, Any)]]: Row with structure:
                            - [dict(str, Any)]: Field with structure:
                                - behavior (str): The behavior of the field
                                - editable (bool): Whether the field is editable
                                - label (str): The label of the field
                                - readable (bool): Whether the field is readable
                                - required (bool): Whether the field is required
                                - field (str): The field name
                    - standardButtons (list[str]): List of standard buttons:
                    - layoutAssignments (list[dict(str, Any)]): List of layout assignments with structure:
                        - layoutId (str): The ID of the layout
                        - recordTypeId (str): The ID of the record type
                        - profileId (str): The ID of the profile
    Raises:
        ValueError: If layout ID is not provided.
        LayoutNotFound: If layout ID is not found.
    """

    if not layout_id or not isinstance(layout_id, str):
        raise ValueError("Layout ID is required")

    layouts = DB["Task"]["layouts"]
    for layout in layouts:
        if layout.get("id") == layout_id:
            return {
                "layout": layout
            }
    
    # If no layout found, raise LayoutNotFound exception
    raise custom_errors.LayoutNotFound(f"Layout {layout_id} not found")


@tool_spec(
    spec={
        'name': 'describe_task_object',
        'description': """ Describes Task SObjects.
        
        Return all the fields of the Task's SObject Metadata. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def describeSObjects() -> List[Dict[str, Any]]:
    """
    Describes Task SObjects.

    Return all the fields of the Task's SObject Metadata.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing the Task sObject description, containing the following keys:
            - activateable (bool): Reserved for future use.
            - associateEntityType (Optional[str]): The type of association to a parent object, such as "History". Null otherwise.
            - associateParentEntity (Optional[str]): The parent object this object is associated with. Null otherwise.
            - childRelationships (List[Dict[str, Any]]): An array of child relationships.
                - cascadeDelete (bool): Indicates if deleting the parent record cascades to child records.
                - childSObject (str): The name of the child sObject.
                - deprecatedAndHidden (bool): Reserved for future use.
                - field (str): The API name of the foreign key field in the child sObject.
                - junctionIdListNames (List[str]): The names of the lists of junction IDs.
                - junctionReferenceTo (List[str]): A collection of object names that can be referenced.
                - relationshipName (str): The name of the relationship, usually the plural of the child sObject name.
                - restrictedDelete (bool): Indicates if parent deletion is restricted by a child record.
            - actionOverrides (List[Dict[str, Any]]): An array of action overrides for the object.
                - formFactor (str): The environment to which the override applies (e.g., "Large", "Small").
                - isAvailableInTouch (bool): Indicates if the override is available in the Salesforce mobile app.
                - name (str): The name of the action that overrides the default action (e.g., "New", "Edit").
                - pageId (str): The ID of the page (e.g., Visualforce or Lightning page) for the action override.
                - url (Optional[str]): The URL of the item used for the action override. Returns null for Lightning page overrides.
            - compactLayoutable (bool): Indicates if the object can be used in describeCompactLayouts().
            - createable (bool): Indicates if records can be created for this sObject via the create() call.
            - custom (bool): Indicates if the object is a custom object.
            - customSetting (bool): Indicates if the object is a custom setting.
            - dataTranslationEnabled (bool): Indicates if data translation is enabled for the object.
            - deepCloneable (bool): Reserved for future use.
            - defaultImplementation (Optional[str]): Reserved for future use.
            - deletable (bool): Indicates if records can be deleted for this sObject via the delete() call.
            - deprecatedAndHidden (bool): Reserved for future use.
            - extendedBy (Optional[str]): Reserved for future use.
            - extendsInterfaces (Optional[str]): Reserved for future use.
            - feedEnabled (bool): Indicates if Chatter feeds are enabled for the object.
            - fields (List[Dict[str, Any]]): An array of field definitions for the object.
                - byteLength (int): The maximum size of the field in bytes.
                - calculated (bool): Indicates if the field is a custom formula field.
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
                    - validFor (Optional[str]): A base64-encoded bitmap indicating validity for dependent picklists.
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
            - implementedBy (Optional[str]): Reserved for future use.
            - implementsInterfaces (Optional[str]): Reserved for future use.
            - isInterface (bool): Reserved for future use.
            - keyPrefix (str): The three-character prefix for the object's record IDs (e.g., "00T" for Task).
            - label (str): The display label for the object (e.g., "Task").
            - labelPlural (str): The plural display label for the object (e.g., "Tasks").
            - layoutable (bool): Indicates if the object supports the describeLayout() call.
            - mergeable (bool): Indicates if records of this object type can be merged.
            - mruEnabled (bool): Indicates if the Most Recently Used list is enabled for this object.
            - name (str): The API name of the object (e.g., "Task").
            - namedLayoutInfos (List[Dict[str, str]]): An array of named layouts available for the object.
              - name (str): The name of the layout.
            - networkScopeFieldName (Optional[str]): The API name of the field that scopes the entity to an Experience Cloud site.
            - queryable (bool): Indicates if the object can be queried via the query() call.
            - recordTypeInfos (List[Dict[str, Any]]): An array of record types available for this object.
                - available (bool): Indicates if the record type is available to the current user.
                - defaultRecordTypeMapping (bool): Indicates if this is the default record type.
                - developerName (str): The API name of the record type.
                - master (bool): Indicates if this is the master record type.
                - name (str): The display name of the record type.
                - recordTypeId (str): The ID of the record type.
                - urls (Dict[str, str]): A dictionary containing URLs for the record type.
                    - layout (str): The URL to the layout for the record type.
            - replicateable (bool): Indicates if the object can be replicated via getUpdated() and getDeleted().
            - retrieveable (bool): Indicates if records can be retrieved via the retrieve() call.
            - searchable (bool): Indicates if the object can be searched via the search() call.
            - searchLayoutable (bool): Indicates if search layouts can be described.
            - supportedScopes (List[Dict[str, str]]): The list of supported scopes for the object (e.g., "mine", "team").
                - label (str): The label of the scope.
                - name (str): The name of the scope.
            - triggerable (bool): Indicates if the object supports Apex triggers.
            - undeletable (bool): Indicates if records can be undeleted via the undelete() call.
            - updateable (bool): Indicates if records can be updated via the update() call.
            - urlDetail (str): The URL template to the read-only detail page for a record.
            - urlEdit (str): The URL template to the edit page for a record.
            - urlNew (str): The URL to the new/create page for the object.
    
    Raises:
        custom_errors.SObjectNotFoundError: If the Task SObject is not found in the database.
    """

    if 'TaskSObject' not in DB:
            raise custom_errors.SObjectNotFoundError("sObject 'Task' not found in DB.")

    return DB['TaskSObject']


@tool_spec(
    spec={
        'name': 'get_deleted_tasks',
        'description': """ Retrieves the list of individual records that have been deleted within the given timespan for the specified object.
        
        This function implements Salesforce API getDeleted() for data replication applications to retrieve a list 
        of records that have been deleted from your organization's data within the specified timespan. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'sObjectType': {
                    'type': 'string',
                    'description': 'The type of object to retrieve deleted records for (e.g., "Task", "Account", "Contact").'
                },
                'start_date': {
                    'type': 'string',
                    'description': """ Starting date/time (UTC) of the timespan for which to retrieve the data.
                    Format: ISO 8601 (e.g., "2024-01-01T00:00:00Z").
                    The API ignores the seconds portion of the specified dateTime value.
                    If None, no start date filter is applied. """
                },
                'end_date': {
                    'type': 'string',
                    'description': """ Ending date/time (UTC) of the timespan for which to retrieve the data.
                    Format: ISO 8601 (e.g., "2024-01-31T23:59:00Z").
                    The API ignores the seconds portion of the specified dateTime value.
                    If None, no end date filter is applied. """
                }
            },
            'required': [
                'sObjectType'
            ]
        }
    }
)
def getDeleted(sObjectType: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves the list of individual records that have been deleted within the given timespan for the specified object.
    
    This function implements Salesforce API getDeleted() for data replication applications to retrieve a list 
    of records that have been deleted from your organization's data within the specified timespan.

    Args:
        sObjectType (str): The type of object to retrieve deleted records for (e.g., "Task", "Account", "Contact").
        start_date (Optional[str]): Starting date/time (UTC) of the timespan for which to retrieve the data.
                                   Format: ISO 8601 (e.g., "2024-01-01T00:00:00Z").
                                   The API ignores the seconds portion of the specified dateTime value.
                                   If None, no start date filter is applied.
        end_date (Optional[str]): Ending date/time (UTC) of the timespan for which to retrieve the data.
                                 Format: ISO 8601 (e.g., "2024-01-31T23:59:00Z").
                                 The API ignores the seconds portion of the specified dateTime value.
                                 If None, no end date filter is applied.

    Returns:
        Dict[str, Any]: A GetDeletedResult object containing:
            - earliestDateAvailable (Optional[str]): Timestamp of the last physically deleted object
            - deletedRecords (List[Dict[str, str]]): Array of deleted records with id and deletedDate
            - latestDateCovered (Optional[str]): Timestamp of the last date covered in the call

    Raises:
        InvalidSObjectTypeError: If sObjectType is not a string or is empty.
        UnsupportedSObjectTypeError: If sObjectType is not supported by this module (only "Task" is supported).
        InvalidDateTypeError: If start_date or end_date are not strings or None.
        InvalidDateFormatError: If start_date or end_date are provided but not in valid ISO 8601 format.
        InvalidReplicationDateError: If date validation rules are violated:
            - startDate must precede endDate by more than one minute
        ExceededIdLimitError: If too many results are returned (API limit exceeded).
    """
    # Input validation using Pydantic model
    try:
        validated_input = GetDeletedInput(sObjectType=sObjectType, start_date=start_date, end_date=end_date)
    except ValidationError as e:
        # Convert Pydantic validation errors to custom errors
        for error in e.errors():
            field_name = error['loc'][0]
            if field_name == 'sObjectType':
                if error['type'] == 'string_type':
                    raise InvalidSObjectTypeError("sObjectType must be a string")
                elif 'cannot be empty' in error['msg']:
                    raise InvalidSObjectTypeError("sObjectType cannot be empty")
            elif field_name in ['start_date', 'end_date']:
                if error['type'] == 'string_type':
                    raise InvalidDateTypeError(f"{field_name} must be a string or None")
                elif error['type'] == 'value_error':
                    if 'Date must be in valid ISO 8601 format' in error['msg']:
                        raise InvalidDateFormatError(f"{field_name} must be in valid ISO 8601 format")
                    elif 'startDate must chronologically precede endDate' in error['msg']:
                        raise InvalidReplicationDateError("startDate must chronologically precede endDate by more than one minute")
        # Re-raise if it's an unexpected validation error
        raise e

    # For this Task module, we only support "Task" sObjectType
    if validated_input.sObjectType != "Task":
        raise UnsupportedSObjectTypeError(f"sObjectType '{validated_input.sObjectType}' is not supported. Only 'Task' is supported in this module.")

    # Initialize DeletedTasks collection if it doesn't exist
    if "DeletedTasks" not in DB:
        DB["DeletedTasks"] = {}

    deleted_records = []
    earliest_date = None
    latest_date = None
    
    # Process dates (ignore seconds as per Salesforce spec)
    start_dt = None
    end_dt = None
    
    if validated_input.start_date:
        start_dt = datetime.fromisoformat(validated_input.start_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
    if validated_input.end_date:
        end_dt = datetime.fromisoformat(validated_input.end_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
    
    for task_id, deleted_task in DB["DeletedTasks"].items():
        deleted_date = deleted_task.get("deletedDate")
        if not deleted_date:
            continue
            
        # Parse deleted date and ignore seconds
        try:
            task_deleted_date = datetime.fromisoformat(deleted_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
        except ValueError:
            # Skip records with invalid dates
            continue
            
        # Apply date filtering if dates are provided
        if start_dt and task_deleted_date < start_dt:
            continue
        if end_dt and task_deleted_date > end_dt:
            continue
        
        # Create deleted record dictionary
        deleted_record = {
            "id": task_id,
            "deletedDate": deleted_date
        }
        deleted_records.append(deleted_record)
        
        # Track earliest and latest dates
        if earliest_date is None or deleted_date < earliest_date:
            earliest_date = deleted_date
        if latest_date is None or deleted_date > latest_date:
            latest_date = deleted_date

    # Check ID limit (Salesforce API limit - typically 2000 records)
    MAX_RECORDS_LIMIT = 2000
    if len(deleted_records) > MAX_RECORDS_LIMIT:
        raise ExceededIdLimitError(f"Too many results returned. Limit is {MAX_RECORDS_LIMIT} records.")

    # Create result dictionary
    result = {
        "earliestDateAvailable": earliest_date,
        "deletedRecords": deleted_records,
        "latestDateCovered": latest_date
    }
    
    return result


@tool_spec(
    spec={
        'name': 'get_updated_tasks',
        'description': """ Retrieves the list of individual records that have been updated (added or changed) within the given timespan for the specified object.
        
        This function is used to get the list of individual records that have been updated (added or changed) within the given timespan for the specified object. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'sObjectType': {
                    'type': 'string',
                    'description': 'The type of object to retrieve updated records for (e.g., "Task").'
                },
                'start_date': {
                    'type': 'string',
                    'description': 'Starting date/time (UTC) of the timespan for which to retrieve the data. ISO 8601 format. Seconds are ignored.'
                },
                'end_date': {
                    'type': 'string',
                    'description': 'Ending date/time (UTC) of the timespan for which to retrieve the data. ISO 8601 format. Seconds are ignored.'
                }
            },
            'required': [
                'sObjectType'
            ]
        }
    }
)
def getUpdated(sObjectType: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves the list of individual records that have been updated (added or changed) within the given timespan for the specified object.

    This function is used to get the list of individual records that have been updated (added or changed) within the given timespan for the specified object.

    Args:
        sObjectType (str): The type of object to retrieve updated records for (e.g., "Task").
        start_date (Optional[str]): Starting date/time (UTC) of the timespan for which to retrieve the data. ISO 8601 format. Seconds are ignored.
        end_date (Optional[str]): Ending date/time (UTC) of the timespan for which to retrieve the data. ISO 8601 format. Seconds are ignored.

    Returns:
        Dict[str, Any]: A GetUpdatedResult object containing:
            - ids (List[str]): Array of IDs of updated/created records
            - latestDateCovered (Optional[str]): Timestamp of the last date covered in the call

    Raises:
        InvalidSObjectTypeError: If sObjectType is not a string or is empty.
        UnsupportedSObjectTypeError: If sObjectType is not supported by this module (only "Task" is supported).
        InvalidDateTypeError: If start_date or end_date are not strings or None.
        InvalidDateFormatError: If start_date or end_date are provided but not in valid ISO 8601 format.
        InvalidReplicationDateError: If date validation rules are violated:
            - startDate must precede endDate by more than one minute
        ExceededIdLimitError: If too many results are returned (API limit exceeded).
    """
    

    # Input validation using Pydantic model
    try:
        validated_input = GetUpdatedInput(sObjectType=sObjectType, start_date=start_date, end_date=end_date)
    except ValidationError as e:
        for error in e.errors():
            field_name = error['loc'][0]
            if field_name == 'sObjectType':
                if error['type'] == 'string_type':
                    raise custom_errors.InvalidSObjectTypeError("sObjectType must be a string")
                elif 'cannot be empty' in error['msg']:
                    raise custom_errors.InvalidSObjectTypeError("sObjectType cannot be empty")
            elif field_name in ['start_date', 'end_date']:
                if error['type'] == 'string_type':
                    raise custom_errors.InvalidDateTypeError(f"{field_name} must be a string or None")
                elif error['type'] == 'value_error':
                    if 'Date must be in valid ISO 8601 format' in error['msg']:
                        raise custom_errors.InvalidDateFormatError(f"{field_name} must be in valid ISO 8601 format")
                    elif 'startDate must chronologically precede endDate' in error['msg']:
                        raise custom_errors.InvalidReplicationDateError("startDate must chronologically precede endDate by more than one minute")
        raise e

    # Only support 'Task' sObjectType
    if validated_input.sObjectType != "Task":
        raise custom_errors.UnsupportedSObjectTypeError(f"sObjectType '{validated_input.sObjectType}' is not supported. Only 'Task' is supported in this module.")

    # 30-day window enforcement (Salesforce rule)
    if validated_input.start_date and validated_input.end_date:
        start_dt = datetime.fromisoformat(validated_input.start_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
        end_dt = datetime.fromisoformat(validated_input.end_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
        if (end_dt - start_dt).days > 30:
            raise custom_errors.InvalidReplicationDateError("The specified date range cannot exceed 30 days.")
    else:
        start_dt = None
        end_dt = None
        if validated_input.start_date:
            start_dt = datetime.fromisoformat(validated_input.start_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
        if validated_input.end_date:
            end_dt = datetime.fromisoformat(validated_input.end_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)

    # Gather updated/created tasks
    ids = []
    latest_date = None
    if "Task" in DB and isinstance(DB["Task"], dict):
        for task_id, task in DB["Task"].items():
            # Use SystemModstamp, LastModifiedDate, or CreatedDate (in that order of preference)
            mod_fields = [
                task.get("SystemModstamp"),
                task.get("LastModifiedDate"),
                task.get("CreatedDate"),
            ]
            mod_date = next((d for d in mod_fields if d), None)
            if not mod_date:
                continue
            try:
                mod_dt = datetime.fromisoformat(mod_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
            except Exception:
                continue
            # Date filtering
            if start_dt and mod_dt < start_dt:
                continue
            if end_dt and mod_dt > end_dt:
                continue
            ids.append(task_id)
            # Track latest date
            if latest_date is None or mod_date > latest_date:
                latest_date = mod_date

    # Enforce 600,000 ID limit
    MAX_IDS_LIMIT = 600000
    if len(ids) > MAX_IDS_LIMIT:
        raise custom_errors.ExceededIdLimitError(f"Too many results returned. Limit is {MAX_IDS_LIMIT} records.")

    result = {
        "ids": ids,
        "latestDateCovered": latest_date
    }
    return result


@tool_spec(
    spec={
        'name': 'query_tasks',
        'description': 'Queries tasks based on specified criteria.',
        'parameters': {
            'type': 'object',
            'properties': {
                'criteria': {
                    'type': 'object',
                    'description': """ A dictionary of search criteria for filtering tasks.
                    If provided, the dictionary structure is validated. Contains the following optional keys:
                    All keys within the criteria dictionary are optional.
                    If not provided (i.e., None), all tasks in the database will be returned. """,
                    'properties': {
                        'Subject': {
                            'type': 'string',
                            'description': 'The subject of the task.'
                        },
                        'Priority': {
                            'type': 'string',
                            'description': 'The priority of the task.'
                        },
                        'Status': {
                            'type': 'string',
                            'description': 'The status of the task.'
                        },
                        'ActivityDate': {
                            'type': 'string',
                            'description': 'The due date of the task. Format: "YYYY-MM-DD".'
                        },
                        'Name': {
                            'type': 'string',
                            'description': 'The name of the task.'
                        },
                        'Description': {
                            'type': 'string',
                            'description': 'Description of the task.'
                        },
                        'DueDate': {
                            'type': 'string',
                            'description': 'Due date of the task.'
                        },
                        'OwnerId': {
                            'type': 'string',
                            'description': 'ID of the task owner.'
                        },
                        'WhoId': {
                            'type': 'string',
                            'description': 'ID of the related contact.'
                        },
                        'WhatId': {
                            'type': 'string',
                            'description': 'ID of the related record.'
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
            },
            'required': []
        }
    }
)
def query(criteria: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Queries tasks based on specified criteria.

    Args:
        criteria (Optional[Dict[str, Any]]): A dictionary of search criteria for filtering tasks.
            If provided, the dictionary structure is validated. Contains the following optional keys:
                - Subject (Optional[str]): The subject of the task.
                - Priority (Optional[str]): The priority of the task.
                - Status (Optional[str]): The status of the task.
                - ActivityDate (Optional[str]): The due date of the task. Format: "YYYY-MM-DD".
                - Name (Optional[str]): The name of the task.
                - Description (Optional[str]): Description of the task.
                - DueDate (Optional[str]): Due date of the task.
                - OwnerId (Optional[str]): ID of the task owner.
                - WhoId (Optional[str]): ID of the related contact.
                - WhatId (Optional[str]): ID of the related record.
                - IsReminderSet (Optional[bool]): Whether reminder is set.
                - ReminderDateTime (Optional[str]): Reminder date and time.
            All keys within the criteria dictionary are optional.
            If not provided (i.e., None), all tasks in the database will be returned.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing a list of
            non-deleted task objects matching the criteria under the key 'results'. 

    Raises:
        ValidationError: If 'criteria' is provided but does not conform
            to the expected structure or types (e.g., non-string value for Subject).
        TypeError: If criteria is not None and not a dictionary.
    """
    # --- Input Validation ---
    if criteria is not None:
        if not isinstance(criteria, dict):
            raise TypeError("Argument 'criteria' must be a dictionary or None.")
        try:
            TaskCriteriaModel(**criteria)
        except ValidationError as e:
            raise e

    # --- Core Logic ---
    results = []

    # Handle empty DB cases
    if "Task" not in DB or not DB["Task"]:
        return {"results": []}

    for task_id, task in DB["Task"].items():
        # Ensure the task itself is a dictionary before proceeding
        if not isinstance(task, dict):
            continue

        # Skip deleted tasks
        if task.get("IsDeleted", False):
            continue

        if criteria is None:
            results.append(task)
        else:
            match = True
            for key, value in criteria.items():
                # Check if key exists in task and if the value matches
                if key not in task or task.get(key) != value:
                    match = False
                    break
            if match:
                results.append(task)

    return {"results": results}


@tool_spec(
    spec={
        'name': 'retrieve_task_details',
        'description': 'Retrieves details of a specific task by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'task_id': {
                    'type': 'string',
                    'description': 'The ID of the task to retrieve.'
                }
            },
            'required': [
                'task_id'
            ]
        }
    }
)
def retrieve(task_id: str) -> Dict[str, Any]:
    """
    Retrieves details of a specific task by its ID.

    Args:
        task_id (str): The ID of the task to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing the details of the task with the following keys:
            Id (str): The unique identifier of the task.
            Name (str): The name or title of the task.
            Priority (str): The priority level of the task (e.g., "High", "Medium", "Low").
            Status (str): The current status of the task (e.g., "In Progress", "Completed").
            DueDate (str): The due date of the task in YYYY-MM-DD format.
            CreatedDate (str): The timestamp when the task was created, in ISO 8601 UTC format.
            IsDeleted (bool): A boolean flag indicating whether the task has been marked as deleted.
            SystemModstamp (str): The last modified timestamp of the task in ISO 8601 UTC format.

    Raises:
        ValueError: If the input data is invalid.
        TaskNotFoundError: If the task does not exist in the database.
    """
    try:
        RetrieveTaskInput(task_id=task_id)
    except ValidationError as e:
        raise e

    if "Task" not in DB or task_id not in DB["Task"]:
        raise custom_errors.TaskNotFoundError("Task not found")

    response = DB["Task"][task_id]
    return response


@tool_spec(
    spec={
        'name': 'search_tasks',
        'description': 'Searches for tasks based on specified search criteria.',
        'parameters': {
            'type': 'object',
            'properties': {
                'search_term': {
                    'type': 'string',
                    'description': """ The term to search for in task fields. If empty or contains only whitespace, 
                    returns all non-deleted tasks. Maximum length limit is 32,000 characters. """
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
    Searches for tasks based on specified search criteria.

    Args:
        search_term (str): The term to search for in task fields. If empty or contains only whitespace, 
                          returns all non-deleted tasks. Maximum length limit is 32,000 characters.

    Returns:
        Dict[str, List[Dict[str, Any]]]: List of tasks containing the search term with structure:
            - results (list): List of task objects containing the search term, or all non-deleted tasks 
                             if search_term is empty or contains only whitespace

    Raises:
        TypeError: If search_term is not a string
        ValueError: If search_term exceeds the maximum length limit (32,000 characters)
    """
    if not isinstance(search_term, str):
        raise TypeError("search_term must be a string.")
    
    # Check for input length limit (32k characters)
    MAX_SEARCH_TERM_LENGTH = 32000
    if len(search_term) > MAX_SEARCH_TERM_LENGTH:
        raise ValueError(f"search_term exceeds maximum length limit of {MAX_SEARCH_TERM_LENGTH} characters")

    results: List[Dict[str, Any]] = []
    if "Task" in DB and isinstance(DB["Task"], dict):
        # If search term is empty or only whitespace, return all non-deleted tasks
        if not search_term.strip():
            for task in DB["Task"].values():
                # Ensure task is a dictionary before proceeding
                if not isinstance(task, dict):
                    continue
                # Skip deleted tasks
                if not task.get("IsDeleted", False):
                    results.append(task)
        else:
            search_term_lower = search_term.lower()
            for task in DB["Task"].values():
                # Ensure task is a dictionary before proceeding
                if not isinstance(task, dict):
                    continue
                # Skip deleted tasks
                if task.get("IsDeleted", False):
                    continue
                    
                # Convert all values to strings and search case-insensitively
                task_values = []
                for value in task.values():
                    if isinstance(value, (str, int, float, bool)):
                        task_values.append(str(value).lower())
                    elif value is not None:
                        task_values.append(str(value).lower())
                task_str = " ".join(task_values)
                if search_term_lower in task_str:
                    results.append(task)
    return {"results": results}


@tool_spec(
    spec={
        'name': 'undelete_task',
        'description': 'Restores a deleted task.',
        'parameters': {
            'type': 'object',
            'properties': {
                'task_id': {
                    'type': 'string',
                    'description': 'The ID of the task to undelete.'
                }
            },
            'required': [
                'task_id'
            ]
        }
    }
)
def undelete(task_id: str) -> Dict[str, Any]:
    """
    Restores a deleted task.

    Args:
        task_id (str): The ID of the task to undelete.

    Returns:
        Dict[str, Any]: The task object if found, or error dict with structure:
            - task_id (str): Error message if task not found
            - success (bool): True if the task is undeleted, False otherwise

    Raises:
        InvalidParameterException: If the task_id is not a string.
        TaskNotFoundError: If the task is not found.
    """

    if not isinstance(task_id, str):
        raise custom_errors.InvalidParameterException("task_id must be a string")
    
    if not task_id or not task_id.strip():
        raise custom_errors.InvalidParameterException("task_id cannot be empty or whitespace")

    if "DeletedTasks" in DB and task_id in DB["DeletedTasks"]:
        # Pop the task from the DeletedTasks collection
        task_to_restore = DB["DeletedTasks"].pop(task_id)
        # Update the IsDeleted field to False
        task_to_restore["IsDeleted"] = False
        # Remove the deletedDate field
        task_to_restore.pop("deletedDate", None)

        # Initialize the Task collection if it doesn't exist
        if "Task" not in DB:
            DB["Task"] = {}
        # Add the task to the Task collection
        DB["Task"][task_id] = task_to_restore

        response = UndeleteTaskOutput(task_id=task_id, success=True)
        return response.model_dump()
    else:
        raise TaskNotFoundError("Task not found")

@tool_spec(
    spec={
        'name': 'update_task',
        'description': 'Updates an existing task.',
        'parameters': {
            'type': 'object',
            'properties': {
                'task_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the task to be updated.'
                },
                'Name': {
                    'type': 'string',
                    'description': 'The name/title of the task.'
                },
                'Subject': {
                    'type': 'string',
                    'description': 'The subject of the task.'
                },
                'Priority': {
                    'type': 'string',
                    'description': 'The priority level of the task.'
                },
                'Status': {
                    'type': 'string',
                    'description': 'The current status of the task.'
                },
                'Description': {
                    'type': 'string',
                    'description': 'A brief description of the task.'
                },
                'ActivityDate': {
                    'type': 'string',
                    'description': 'The due date of the task (ISO 8601 format recommended).'
                },
                'OwnerId': {
                    'type': 'string',
                    'description': 'The ID of the task owner.'
                },
                'WhoId': {
                    'type': 'string',
                    'description': 'The ID of the contact related to the task.'
                },
                'WhatId': {
                    'type': 'string',
                    'description': 'The ID of the related record.'
                },
                'IsReminderSet': {
                    'type': 'boolean',
                    'description': 'Whether a reminder is set for the task.'
                },
                'ReminderDateTime': {
                    'type': 'string',
                    'description': 'The date and time of the reminder (ISO 8601 format recommended).'
                }
            },
            'required': [
                'task_id'
            ]
        }
    }
)
def update(
    task_id: str,
    Name: Optional[str] = None,
    Subject: Optional[str] = None,
    Priority: Optional[str] = None,
    Status: Optional[str] = None,
    Description: Optional[str] = None,
    ActivityDate: Optional[str] = None,
    OwnerId: Optional[str] = None,
    WhoId: Optional[str] = None,
    WhatId: Optional[str] = None,
    IsReminderSet: Optional[bool] = None,
    ReminderDateTime: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates an existing task.

    Args:
        task_id (str): The unique identifier of the task to be updated.
        Name (Optional[str]): The name/title of the task.
        Subject (Optional[str]): The subject of the task.
        Priority (Optional[str]): The priority level of the task.
        Status (Optional[str]): The current status of the task.
        Description (Optional[str]): A brief description of the task.
        ActivityDate (Optional[str]): The due date of the task (ISO 8601 format recommended).
        OwnerId (Optional[str]): The ID of the task owner.
        WhoId (Optional[str]): The ID of the contact related to the task.
        WhatId (Optional[str]): The ID of the related record.
        IsReminderSet (Optional[bool]): Whether a reminder is set for the task.
        ReminderDateTime (Optional[str]): The date and time of the reminder (ISO 8601 format recommended).

    Returns:
        Dict[str, Any]: The updated task object if found, or error dict with structure:
            - error (str): Error message if task not found
            If successful, returns the task object with the following fields:
            - Id (str): Unique identifier for the task
            - CreatedDate (str): ISO format timestamp of creation
            - IsDeleted (bool): Whether the task is deleted
            - SystemModstamp (str): Last modified timestamp
            - Name (Optional[str]): The name of the task, if provided
            - Subject (Optional[str]): The subject of the task, if provided
            - Priority (Optional[str]): Priority of the task, if provided
            - Status (Optional[str]): Status of the task, if provided
            - Description (Optional[str]): Description of the task, if provided
            - ActivityDate (Optional[str]): Due date of the task, if provided
            - OwnerId (Optional[str]): ID of the task owner, if provided
            - WhoId (Optional[str]): ID of the related contact, if provided
            - WhatId (Optional[str]): ID of the related record, if provided
            - IsReminderSet (Optional[bool]): Whether reminder is set, if provided
            - ReminderDateTime (Optional[str]): Reminder date and time, if provided

    Raises:
        ValueError: If provided data fails validation.
        TaskNotFoundError: If the task ID does not exist in the database.
    """
    
    # Collect all inputs into a dictionary
    update_data = {
        "task_id": task_id,
        "Name": Name,
        "Subject": Subject,
        "Priority": Priority,
        "Status": Status,
        "Description": Description,
        "ActivityDate": ActivityDate,
        "OwnerId": OwnerId,
        "WhoId": WhoId,
        "WhatId": WhatId,
        "IsReminderSet": IsReminderSet,
        "ReminderDateTime": ReminderDateTime,
    }

    # Remove None values to allow partial updates, but keep task_id
    clean_update_data = {k: v for k, v in update_data.items() if v is not None}

    # Validate using Pydantic model before any database operations
    try:
        validated_update = TaskUpdateModel(**clean_update_data)
    except ValidationError as e:
        raise e

    # Now that inputs are validated, check for task existence
    if "Task" not in DB or validated_update.task_id not in DB["Task"]:
        raise custom_errors.TaskNotFoundError("Task not found.")

    # Retrieve existing task
    task = DB["Task"][validated_update.task_id]

    # Apply the validated updates
    for field, value in validated_update.model_dump(exclude_none=True, exclude={'task_id'}).items():
        task[field] = value

    # Update system modstamp
    task["SystemModstamp"] = datetime.now().isoformat()

    return task


@tool_spec(
    spec={
        'name': 'upsert_task',
        'description': 'Creates or updates a task.',
        'parameters': {
            'type': 'object',
            'properties': {
                'Id': {
                    'type': 'string',
                    'description': 'Task ID (required for update).'
                },
                'Name': {
                    'type': 'string',
                    'description': 'The name of the task.'
                },
                'Subject': {
                    'type': 'string',
                    'description': 'The subject of the task.'
                },
                'Priority': {
                    'type': 'string',
                    'description': 'Priority of the task.'
                },
                'Status': {
                    'type': 'string',
                    'description': 'Status of the task.'
                },
                'Description': {
                    'type': 'string',
                    'description': 'Description of the task.'
                },
                'ActivityDate': {
                    'type': 'string',
                    'description': "Due date of the task in ISO format (e.g., '2024-01-01T10:00:00Z')."
                },
                'OwnerId': {
                    'type': 'string',
                    'description': 'ID of the task owner.'
                },
                'WhoId': {
                    'type': 'string',
                    'description': 'ID of the related contact.'
                },
                'WhatId': {
                    'type': 'string',
                    'description': 'ID of the related record.'
                },
                'IsReminderSet': {
                    'type': 'boolean',
                    'description': 'Whether reminder is set.'
                },
                'ReminderDateTime': {
                    'type': 'string',
                    'description': "Reminder date and time in ISO format (e.g., '2024-01-01T10:00:00Z')."
                }
            },
            'required': []
        }
    }
)
def upsert(
    Id: Optional[str] = None,
    Name: Optional[str] = None,
    Subject: Optional[str] = None,
    Priority: Optional[str] = None,
    Status: Optional[str] = None,
    Description: Optional[str] = None,
    ActivityDate: Optional[str] = None,
    OwnerId: Optional[str] = None,
    WhoId: Optional[str] = None,
    WhatId: Optional[str] = None,
    IsReminderSet: Optional[bool] = None,
    ReminderDateTime: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates or updates a task.

    Args:
        Id (Optional[str]): Task ID (required for update).
        Name (Optional[str]): The name of the task.
        Subject (Optional[str]): The subject of the task.
        Priority (Optional[str]): Priority of the task.
        Status (Optional[str]): Status of the task.
        Description (Optional[str]): Description of the task.
        ActivityDate (Optional[str]): Due date of the task in ISO format (e.g., '2024-01-01T10:00:00Z').
        OwnerId (Optional[str]): ID of the task owner.
        WhoId (Optional[str]): ID of the related contact.
        WhatId (Optional[str]): ID of the related record.
        IsReminderSet (Optional[bool]): Whether reminder is set.
        ReminderDateTime (Optional[str]): Reminder date and time in ISO format (e.g., '2024-01-01T10:00:00Z').

    Returns:
        Dict[str, Any]: The created or updated task object with the following fields:
            - Id (str): Unique identifier for the task
            - CreatedDate (str): Created Date in ISO format (e.g., '2024-01-01T10:00:00Z').
            - IsDeleted (bool): Whether the task is deleted
            - SystemModstamp (str): Last modified timestamp
            - Name (Optional[str]): The name of the task, if provided
            - Subject (Optional[str]): The subject of the task, if provided
            - Priority (Optional[str]): Priority of the task, if provided
            - Status (Optional[str]): Status of the task, if provided
            - Description (Optional[str]): Description of the task, if provided
            - ActivityDate (Optional[str]): Due date of the task in ISO format (e.g., '2024-01-01T10:00:00Z').
            - OwnerId (Optional[str]): ID of the task owner, if provided
            - WhoId (Optional[str]): ID of the related contact, if provided
            - WhatId (Optional[str]): ID of the related record, if provided
            - IsReminderSet (Optional[bool]): Whether reminder is set, if provided
            - ReminderDateTime (Optional[str]): Reminder date and time in ISO format (e.g., '2024-01-01T10:00:00Z').
        Raises:
            ValueError:
                - If any field fails validation according to the TaskUpsertModel rules
                (e.g., wrong type, invalid format, or failing business rules).
                Example messages include:
                    * "Name must be a string if provided."
                    * "ActivityDate must be a string in ISO 8601 format."
                    * "ActivityDate must be a valid ISO 8601 datetime string."
                    * "IsReminderSet must be a boolean if provided."

    """
    upsert_data = {
        "Id":Id,
        "Name":Name,
        "Subject":Subject,
        "Priority":Priority,
        "Status":Status,
        "Description": Description,
        "ActivityDate":ActivityDate,
        "OwnerId":OwnerId,
        "WhoId":WhoId,
        "WhatId":WhatId,
        "IsReminderSet":IsReminderSet,
        "ReminderDateTime":ReminderDateTime,
    }
    try:
        TaskUpsertModel(**upsert_data)
    except ValidationError as e:
        if e.errors():
            raise ValueError(e.errors()[0]["msg"])
        raise ValueError(str(e))

    if Id is not None and Id in DB.get("Task", {}):
        return update(
            Id,
            Name=Name,
            Subject=Subject,
            Priority=Priority,
            Status=Status,
            Description=Description,
            ActivityDate=ActivityDate,
            OwnerId=OwnerId,
            WhoId=WhoId,
            WhatId=WhatId,
            IsReminderSet=IsReminderSet,
            ReminderDateTime=ReminderDateTime,
        )
    else:
        # For creating a new task, Status and Priority are required
        if Status is None:
            raise ValueError("Status is required for creating a new task.")
        if Priority is None:
            raise ValueError("Priority is required for creating a new task.")
        return create(
            Status=Status,
            Name=Name,
            Priority=Priority,
            Id=Id,
            Subject=Subject,
            Description=Description,
            ActivityDate=ActivityDate,
            OwnerId=OwnerId,
            WhoId=WhoId,
            WhatId=WhatId,
            IsReminderSet=IsReminderSet,
            ReminderDateTime=ReminderDateTime,
        )