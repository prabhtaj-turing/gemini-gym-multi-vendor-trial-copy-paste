from pydantic import BaseModel, ConfigDict, ValidationError, Field, Extra, field_validator, RootModel, field_validator, validator
from typing import Optional, Any, Dict, List, Union # Added List, Dict for completeness, though
from salesforce.SimulationEngine import custom_errors
import datetime
import re
import uuid
import html
from enum import Enum

# ConditionsListModel for Query validation
class ConditionsListModel(RootModel[List[str]]):
    """Pydantic model for validating a list of condition strings."""
    root: List[str]
    
    @field_validator('root')
    @classmethod
    def validate_conditions_list(cls, v):
        if not isinstance(v, list):
            raise ValueError("Input should be a valid list")
        if len(v) == 0:
            raise ValueError("Conditions list cannot be empty")
        for condition in v:
            if not isinstance(condition, str):
                raise ValueError("Input should be a valid string")
            if not condition.strip():
                raise ValueError("Condition cannot be empty or whitespace only")
        return v

# Define valid values for Priority and Status
class TaskPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class TaskStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    WAITING = "Waiting"
    DEFERRED = "Deferred"
    OPEN = "Open"
    CLOSED = "Closed"

class DeletedRecord(BaseModel):
    """
    Pydantic model for a deleted record in GetDeletedResult.
    Represents a single deleted record with its ID and deletion timestamp.
    """
    id: str
    deletedDate: str  # dateTime in ISO 8601 format

    class Config:
        extra = 'forbid'


class GetDeletedResult(BaseModel):
    """
    Pydantic model for the result of getDeleted() call.
    Contains metadata about the deletion query and an array of deleted records.
    """
    earliestDateAvailable: Optional[str] = None  # dateTime in ISO 8601 format
    deletedRecords: List[DeletedRecord]
    latestDateCovered: Optional[str] = None  # dateTime in ISO 8601 format

    class Config:
        extra = 'forbid'


class GetDeletedInput(BaseModel):
    """
    Pydantic model for validating getDeleted() function parameters.
    Implements Salesforce API validation rules for data replication.
    """
    sObjectType: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @field_validator("sObjectType")
    def validate_sObjectType(cls, v):
        if not isinstance(v, str):
            raise ValueError("sObjectType must be a string")
        if not v.strip():
            raise ValueError("sObjectType cannot be empty")
        return v

    @field_validator("start_date", "end_date")
    def validate_date_format(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Date must be a string")
            try:
                # Parse the date and ignore seconds portion as per Salesforce spec
                dt = datetime.datetime.fromisoformat(v.replace('Z', '+00:00'))
                # Round down to the nearest minute (ignore seconds)
                dt = dt.replace(second=0, microsecond=0)
            except ValueError:
                raise ValueError("Date must be in valid ISO 8601 format")
        return v

    @field_validator("end_date")
    def validate_date_range(cls, v, info):
        start_date = info.data.get("start_date")
        if start_date is not None and v is not None:
            # Parse dates and ignore seconds
            start_dt = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
            end_dt = datetime.datetime.fromisoformat(v.replace('Z', '+00:00')).replace(second=0, microsecond=0)
            
            # Check if startDate precedes endDate by more than one minute
            if start_dt >= end_dt:
                raise ValueError("startDate must chronologically precede endDate by more than one minute")

        return v

    class Config:
        extra = 'forbid'


class EventUpdateKwargsModel(BaseModel):
    """
    Pydantic model for validating the keyword arguments passed to the update function.
    All fields are optional, reflecting that any subset of these can be provided for an update.
    """
    Name: Optional[str] = None
    Subject: Optional[str] = None
    StartDateTime: Optional[str] = None
    EndDateTime: Optional[str] = None
    Description: Optional[str] = None
    Location: Optional[str] = None
    IsAllDayEvent: Optional[bool] = None
    OwnerId: Optional[str] = None
    WhoId: Optional[str] = None
    WhatId: Optional[str] = None

    model_config = ConfigDict(extra='ignore')


# Define the Pydantic model for the 'criteria' dictionary
class TaskCriteriaModel(BaseModel):
    """
    Pydantic model for validating the structure of the 'criteria' dictionary
    used for filtering tasks. All fields are optional for flexible filtering.
    """
    Subject: Optional[str] = None
    Priority: Optional[str] = None
    Status: Optional[str] = None
    ActivityDate: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    DueDate: Optional[str] = None
    OwnerId: Optional[str] = None
    WhoId: Optional[str] = None
    WhatId: Optional[str] = None
    IsReminderSet: Optional[bool] = None
    ReminderDateTime: Optional[str] = None

    # Configuration to allow extra fields if the intention is just to validate
    # the known ones but permit others (mimicking flexible dictionary use).
    # If only the defined fields should be allowed, use extra = 'forbid'.
    # If extra fields should be ignored, use extra = 'ignore'.
    # Default Pydantic V2 behavior is 'ignore', which fits well here.
    # model_config = ConfigDict(extra = 'allow') # Or 'ignore' or 'forbid' depending on desired strictness


class EventInputModel(BaseModel):
    Name: Optional[str] = None
    Subject: Optional[str] = None
    StartDateTime: Optional[str] = None
    EndDateTime: Optional[str] = None
    
    # Additional optional fields
    Description: Optional[str] = None
    Location: Optional[str] = None
    IsAllDayEvent: Optional[bool] = None
    OwnerId: Optional[str] = None
    WhoId: Optional[str] = None
    WhatId: Optional[str] = None
    # Additional standard Event fields
    ActivityDate: Optional[str] = None
    ActivityDateTime: Optional[str] = None
    DurationInMinutes: Optional[int] = None
    IsPrivate: Optional[bool] = None
    ShowAs: Optional[str] = None
    Type: Optional[str] = None
    IsChild: Optional[bool] = None
    IsGroupEvent: Optional[bool] = None
    GroupEventType: Optional[str] = None
    IsRecurrence: Optional[bool] = None
    RecurrenceType: Optional[str] = None
    RecurrenceInterval: Optional[int] = None
    RecurrenceEndDateOnly: Optional[str] = None
    RecurrenceMonthOfYear: Optional[int] = None
    RecurrenceDayOfWeekMask: Optional[int] = None
    RecurrenceDayOfMonth: Optional[int] = None
    RecurrenceInstance: Optional[str] = None
    IsReminderSet: Optional[bool] = None
    ReminderDateTime: Optional[str] = None

    @field_validator("StartDateTime", "EndDateTime")
    @classmethod
    def validate_datetime_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate datetime fields using centralized validation."""
        if v is not None:
            from common_utils.datetime_utils import validate_salesforce_datetime, InvalidDateTimeFormatError
            try:
                return validate_salesforce_datetime(v)
            except InvalidDateTimeFormatError as e:
                raise ValueError("Input should be a valid datetime")
        return v

    model_config = ConfigDict(extra='forbid')


# Salesforce DB Pydantic Model for validation
class SalesforceDBModel(BaseModel):
    """
    Pydantic model for validating the entire Salesforce database structure.
    Ensures that the database contains the required collections with proper structure.
    """
    Event: Dict[str, Any] = Field(default_factory=dict, description="Event collection containing event records")
    Task: Dict[str, Any] = Field(default_factory=dict, description="Task collection containing task records and layouts")
    DeletedTasks: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Deleted tasks collection")
    DeletedEvents: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Deleted events collection")

    @field_validator('Event', 'Task')
    @classmethod
    def validate_collections(cls, v):
        """Validate that collections are dictionaries."""
        if not isinstance(v, dict):
            raise ValueError("Collection must be a dictionary")
        return v

    @field_validator('Task')
    @classmethod
    def validate_task_structure(cls, v):
        """Validate that Task collection has expected structure."""
        if not isinstance(v, dict):
            raise ValueError("Task collection must be a dictionary")
        
        # Check for required keys in Task collection
        expected_keys = ['layouts', 'tasks', 'deletedTasks']
        for key in expected_keys:
            if key not in v:
                # Initialize missing keys with default empty structures
                if key == 'layouts':
                    v[key] = []
                elif key == 'tasks':
                    v[key] = []
                elif key == 'deletedTasks':
                    v[key] = []
        
        return v

    model_config = ConfigDict(
        extra='allow',  # Allow additional fields for flexibility
        validate_assignment=True,  # Validate on assignment
        str_strip_whitespace=True  # Strip whitespace from strings
    )


class TaskRecordModel(BaseModel):
    """
    Pydantic model for validating individual Task records in the database.
    Based on Salesforce Task object standard fields.
    """
    Id: str = Field(..., description="Unique identifier for the task")
    Subject: Optional[str] = Field(None, max_length=255, description="Subject of the task")
    Status: str = Field(..., description="Status of the task")
    Priority: str = Field(..., description="Priority of the task")  
    ActivityDate: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    Description: Optional[str] = Field(None, max_length=32000, description="Task description")
    OwnerId: Optional[str] = Field(None, description="ID of the task owner")
    WhoId: Optional[str] = Field(None, description="ID of the related contact or lead")
    WhatId: Optional[str] = Field(None, description="ID of the related account, opportunity, etc.")
    IsDeleted: Optional[bool] = Field(False, description="Whether the task is deleted")
    CreatedDate: Optional[str] = Field(None, description="Creation timestamp")
    SystemModstamp: Optional[str] = Field(None, description="Last modification timestamp")
    IsReminderSet: Optional[bool] = Field(None, description="Whether reminder is set")
    ReminderDateTime: Optional[str] = Field(None, description="Reminder date and time")
    CallDurationInSeconds: Optional[int] = Field(None, description="Duration of call in seconds")
    CallType: Optional[str] = Field(None, description="Type of call")
    CallObject: Optional[str] = Field(None, description="Call object identifier")
    CallDisposition: Optional[str] = Field(None, description="Call disposition")
    IsRecurrence: Optional[bool] = Field(None, description="Whether task is recurring")
    RecurrenceType: Optional[str] = Field(None, description="Type of recurrence")
    RecurrenceInterval: Optional[int] = Field(None, description="Recurrence interval")
    RecurrenceEndDateOnly: Optional[str] = Field(None, description="End date for recurrence")
    RecurrenceMonthOfYear: Optional[int] = Field(None, description="Month of year for recurrence")
    RecurrenceDayOfWeekMask: Optional[int] = Field(None, description="Day of week mask for recurrence")
    RecurrenceDayOfMonth: Optional[int] = Field(None, description="Day of month for recurrence")
    RecurrenceInstance: Optional[str] = Field(None, description="Recurrence instance")
    CompletedDateTime: Optional[str] = Field(None, description="Date and time when task was completed")
    IsClosed: Optional[bool] = Field(None, description="Whether the task is closed")
    IsHighPriority: Optional[bool] = Field(None, description="Whether the task is high priority")
    IsArchived: Optional[bool] = Field(None, description="Whether the task is archived")
    TaskSubtype: Optional[str] = Field(None, description="Subtype of the task")

    @field_validator('Priority')
    @classmethod
    def validate_priority(cls, v):
        if v and v not in ["High", "Medium", "Low", "Normal"]:
            raise ValueError(f"Priority must be one of: High, Medium, Low, Normal")
        return v

    @field_validator('Status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["Not Started", "In Progress", "Completed", "Waiting", "Deferred", "Open", "Closed"]
        if v and v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v

    @field_validator('Id')
    @classmethod
    def validate_id_format(cls, v):
        """Validate Salesforce ID format (15 or 18 characters)."""
        if v and (len(v) not in [15, 18] or not v.isalnum()):
            raise ValueError("ID must be 15 or 18 alphanumeric characters")
        return v

    model_config = ConfigDict(extra='forbid')


class EventRecordModel(BaseModel):
    """
    Pydantic model for validating individual Event records in the database.
    Based on Salesforce Event object standard fields.
    """
    Id: str = Field(..., description="Unique identifier for the event")
    Subject: Optional[str] = Field(None, max_length=255, description="Subject of the event")
    StartDateTime: Optional[str] = Field(None, description="Start date and time")
    EndDateTime: Optional[str] = Field(None, description="End date and time")
    Description: Optional[str] = Field(None, max_length=32000, description="Event description")
    Location: Optional[str] = Field(None, max_length=255, description="Event location")
    IsAllDayEvent: Optional[bool] = Field(False, description="Whether the event is all day")
    OwnerId: Optional[str] = Field(None, description="ID of the event owner")
    WhoId: Optional[str] = Field(None, description="ID of the related contact or lead")
    WhatId: Optional[str] = Field(None, description="ID of the related account, opportunity, etc.")
    IsDeleted: Optional[bool] = Field(False, description="Whether the event is deleted")
    CreatedDate: Optional[str] = Field(None, description="Creation timestamp")
    SystemModstamp: Optional[str] = Field(None, description="Last modification timestamp")
    ActivityDate: Optional[str] = Field(None, description="Date of the activity")
    ActivityDateTime: Optional[str] = Field(None, description="Date and time of the activity")
    DurationInMinutes: Optional[int] = Field(None, description="Duration of the event in minutes")
    IsPrivate: Optional[bool] = Field(None, description="Whether the event is private")
    ShowAs: Optional[str] = Field(None, description="How the event appears in calendar")
    Type: Optional[str] = Field(None, description="Type of the event")
    IsChild: Optional[bool] = Field(None, description="Whether this is a child event")
    IsGroupEvent: Optional[bool] = Field(None, description="Whether this is a group event")
    GroupEventType: Optional[str] = Field(None, description="Type of group event")
    IsRecurrence: Optional[bool] = Field(None, description="Whether the event is recurring")
    RecurrenceType: Optional[str] = Field(None, description="Type of recurrence")
    RecurrenceInterval: Optional[int] = Field(None, description="Recurrence interval")
    RecurrenceEndDateOnly: Optional[str] = Field(None, description="End date for recurrence")
    RecurrenceMonthOfYear: Optional[int] = Field(None, description="Month of year for recurrence")
    RecurrenceDayOfWeekMask: Optional[int] = Field(None, description="Day of week mask for recurrence")
    RecurrenceDayOfMonth: Optional[int] = Field(None, description="Day of month for recurrence")
    RecurrenceInstance: Optional[str] = Field(None, description="Recurrence instance")
    IsReminderSet: Optional[bool] = Field(None, description="Whether reminder is set")
    ReminderDateTime: Optional[str] = Field(None, description="Reminder date and time")

    @field_validator('Id')
    @classmethod
    def validate_id_format(cls, v):
        """Validate Salesforce ID format (15 or 18 characters)."""
        if v and (len(v) not in [15, 18] or not v.isalnum()):
            raise ValueError("ID must be 15 or 18 alphanumeric characters")
        return v

    @field_validator('ShowAs')
    @classmethod
    def validate_show_as(cls, v):
        """Validate ShowAs field values."""
        if v and v not in ["Busy", "Free", "OutOfOffice", "Tentative"]:
            raise ValueError("ShowAs must be one of: Busy, Free, OutOfOffice, Tentative")
        return v

    model_config = ConfigDict(extra='forbid')


class QueryCriteriaModel(BaseModel):
    """
    Pydantic model for validating the 'criteria' dictionary.
    Known keys like 'Subject', 'IsAllDayEvent', and 'StartDateTime'
    are validated for their types if present. Additional keys are allowed.
    """
    Subject: Optional[str] = None
    IsAllDayEvent: Optional[bool] = None
    StartDateTime: Optional[str] = None
    EndDateTime: Optional[str] = None
    Description: Optional[str] = None
    Location: Optional[str] = None
    OwnerId: Optional[str] = None

    model_config = ConfigDict(extra="allow")  # Allow other keys not explicitly defined in the model

class TaskCreateModel(BaseModel):
    """
    Pydantic model for validating the input keyword arguments for task creation.
    
    Validation rules:
    - Required fields (Priority, Status) cannot be None or empty strings
    - Optional string fields (Name, Subject, Description) reject empty strings if provided
    - All string fields are automatically stripped of whitespace
    """
    # Required fields
    Priority: str = Field(..., min_length=1, description="Priority of the task")
    Status: str = Field(..., min_length=1, description="Status of the task")

    # Optional fields - use min_length=1 to reject empty strings when provided
    Id: Optional[str] = Field(None, description="Custom ID for the task")
    Name: Optional[str] = Field(None, min_length=1, max_length=80, description="The name of the task")
    Subject: Optional[str] = Field(None, min_length=1, max_length=255, description="The subject of the task")
    Description: Optional[str] = Field(None, min_length=1, max_length=32000, description="Description of the task")
    ActivityDate: Optional[str] = Field(None, description="Due date of the task in ISO format (YYYY-MM-DD)")
    DueDate: Optional[str] = Field(None, description="Alternative due date field in ISO format (YYYY-MM-DD)")
    OwnerId: Optional[str] = Field(None, min_length=1, description="ID of the task owner")
    WhoId: Optional[str] = Field(None, min_length=1, description="ID of the related contact")
    WhatId: Optional[str] = Field(None, min_length=1, description="ID of the related record")
    IsReminderSet: Optional[bool] = Field(None, description="Whether reminder is set")
    ReminderDateTime: Optional[str] = Field(None, description="Reminder date and time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    CallDurationInSeconds: Optional[int] = Field(None, description="Duration of call in seconds")
    CallType: Optional[str] = Field(None, description="Type of call")
    CallObject: Optional[str] = Field(None, description="Call object identifier")
    CallDisposition: Optional[str] = Field(None, description="Call disposition")
    IsRecurrence: Optional[bool] = Field(None, description="Whether task is recurring")
    RecurrenceType: Optional[str] = Field(None, description="Type of recurrence")
    RecurrenceInterval: Optional[int] = Field(None, description="Recurrence interval")
    RecurrenceEndDateOnly: Optional[str] = Field(None, description="End date for recurrence")
    RecurrenceMonthOfYear: Optional[int] = Field(None, description="Month of year for recurrence (1-12)")
    RecurrenceDayOfWeekMask: Optional[int] = Field(None, description="Day of week mask for recurrence")
    RecurrenceDayOfMonth: Optional[int] = Field(None, description="Day of month for recurrence (1-31)")
    RecurrenceInstance: Optional[str] = Field(None, description="Recurrence instance")
    CompletedDateTime: Optional[str] = Field(None, description="Date and time when task was completed")
    IsClosed: Optional[bool] = Field(None, description="Whether the task is closed")
    IsHighPriority: Optional[bool] = Field(None, description="Whether the task is high priority")
    IsArchived: Optional[bool] = Field(None, description="Whether the task is archived")
    TaskSubtype: Optional[str] = Field(None, description="Subtype of the task")

    @field_validator('Priority')
    @classmethod
    def validate_priority(cls, v):
        valid_priorities = ["High", "Medium", "Low"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v

    @field_validator('Status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["Not Started", "In Progress", "Completed", "Waiting", "Deferred", "Open", "Closed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v

    @field_validator('Id')
    @classmethod
    def validate_id(cls, v):
        if v is not None:
            if v.strip() == "":
                raise ValueError("Id cannot be an empty string")
            if not re.match(r'^[a-zA-Z0-9]{15,18}$', v):
                raise ValueError("Id must be 15-18 alphanumeric characters")
        return v

    @field_validator('ActivityDate', 'DueDate')
    @classmethod
    def validate_date_fields(cls, v):
        if v is not None:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError("Date must be in ISO format (YYYY-MM-DD)")
            try:
                datetime.datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Date must be a valid date")
        return v

    @field_validator('ReminderDateTime', 'CompletedDateTime')
    @classmethod
    def validate_datetime_fields(cls, v):
        if v is not None:
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', v):
                raise ValueError("DateTime must be in ISO format (YYYY-MM-DDTHH:MM:SS)")
            try:
                datetime.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise ValueError("DateTime must be a valid datetime")
        return v

    @field_validator('OwnerId', 'WhoId', 'WhatId')
    @classmethod
    def validate_id_format(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9]{15,18}$', v):
                raise ValueError("ID must be 15-18 alphanumeric characters")
        return v

    @field_validator('CallDurationInSeconds')
    @classmethod
    def validate_call_duration(cls, v):
        if v is not None:
            if not isinstance(v, int) or v < 0:
                from salesforce.SimulationEngine.custom_errors import TaskNumericValidationError
                raise TaskNumericValidationError("CallDurationInSeconds must be a non-negative integer")
        return v

    @field_validator('RecurrenceInterval')
    @classmethod
    def validate_recurrence_interval(cls, v):
        if v is not None:
            if not isinstance(v, int) or v <= 0:
                from salesforce.SimulationEngine.custom_errors import TaskNumericValidationError
                raise TaskNumericValidationError("RecurrenceInterval must be a positive integer")
        return v

    @field_validator('RecurrenceMonthOfYear')
    @classmethod
    def validate_recurrence_month(cls, v):
        if v is not None:
            if not isinstance(v, int) or not (1 <= v <= 12):
                from salesforce.SimulationEngine.custom_errors import TaskNumericValidationError
                raise TaskNumericValidationError("RecurrenceMonthOfYear must be an integer between 1 and 12")
        return v

    @field_validator('RecurrenceDayOfMonth')
    @classmethod
    def validate_recurrence_day(cls, v):
        if v is not None:
            if not isinstance(v, int) or not (1 <= v <= 31):
                from salesforce.SimulationEngine.custom_errors import TaskNumericValidationError
                raise TaskNumericValidationError("RecurrenceDayOfMonth must be an integer between 1 and 31")
        return v

    @classmethod
    def validate_contradictory_states(cls, values):
        """Validate contradictory states after all field validation."""
        from salesforce.SimulationEngine.custom_errors import TaskContradictoryStateError

        priority = values.get('Priority')
        is_high_priority = values.get('IsHighPriority')
        status = values.get('Status')
        is_closed = values.get('IsClosed')
        is_recurrence = values.get('IsRecurrence')
        recurrence_type = values.get('RecurrenceType')

        # Check Priority vs IsHighPriority consistency
        if is_high_priority is not None and priority:
            if is_high_priority and priority != "High":
                raise TaskContradictoryStateError(
                    f"Contradictory priority settings: Priority='{priority}' but IsHighPriority=True. "
                    "IsHighPriority should only be True when Priority is 'High'."
                )
            elif not is_high_priority and priority == "High":
                raise TaskContradictoryStateError(
                    f"Contradictory priority settings: Priority='High' but IsHighPriority=False. "
                    "IsHighPriority should be True when Priority is 'High'."
                )

        # Check recurrence consistency
        if is_recurrence is not None:
            has_recurrence_details = any([
                values.get('RecurrenceType'), values.get('RecurrenceInterval'), 
                values.get('RecurrenceEndDateOnly'), values.get('RecurrenceMonthOfYear'),
                values.get('RecurrenceDayOfWeekMask'), values.get('RecurrenceDayOfMonth'), 
                values.get('RecurrenceInstance')
            ])

            if not is_recurrence and has_recurrence_details:
                raise TaskContradictoryStateError(
                    "Contradictory recurrence settings: IsRecurrence=False but recurrence details are provided. "
                    "Either set IsRecurrence=True or remove recurrence details."
                )
            elif is_recurrence and not recurrence_type:
                raise TaskContradictoryStateError(
                    "Contradictory recurrence settings: IsRecurrence=True but RecurrenceType is not provided. "
                    "RecurrenceType is required when IsRecurrence=True."
                )

        # Check Status vs IsClosed consistency
        if is_closed is not None and status:
            closed_statuses = ["Completed", "Closed"]
            if is_closed and status not in closed_statuses:
                raise TaskContradictoryStateError(
                    f"Contradictory status settings: Status='{status}' but IsClosed=True. "
                    f"IsClosed should only be True when Status is one of: {closed_statuses}."
                )
            elif not is_closed and status in closed_statuses:
                raise TaskContradictoryStateError(
                    f"Contradictory status settings: Status='{status}' but IsClosed=False. "
                    f"IsClosed should be True when Status is '{status}'."
                )

        return values

    @classmethod
    def validate_semantic_consistency(cls, values):
        """Validate semantic consistency of the task data."""
        from salesforce.SimulationEngine.custom_errors import TaskSemanticValidationError

        status = values.get('Status')
        is_closed = values.get('IsClosed')
        reminder_datetime_str = values.get('ReminderDateTime')

        if reminder_datetime_str:
            try:
                reminder_datetime = datetime.datetime.strptime(reminder_datetime_str, '%Y-%m-%dT%H:%M:%S')
                current_time = datetime.datetime.now()

                # Check completed task with future reminder
                if status in ["Completed", "Closed"] and reminder_datetime > current_time:
                    raise TaskSemanticValidationError(
                        f"Semantic inconsistency: Task has Status '{status}' but has a future reminder set for "
                        f"{reminder_datetime_str}. Completed or closed tasks should not have future reminders."
                    )

                # Check closed task with future reminder
                if is_closed and reminder_datetime > current_time:
                    raise TaskSemanticValidationError(
                        f"Semantic inconsistency: Task is marked as closed (IsClosed=True) but has a future reminder "
                        f"set for {reminder_datetime_str}. Closed tasks should not have future reminders."
                    )
            except ValueError:
                pass  # Invalid datetime format will be caught by field validator

        return values

    @classmethod
    def create_and_validate(cls, **kwargs):
        """Create and validate a task with all validation checks."""
        # First create the instance with field validation
        instance = cls(**kwargs)

        # Then run additional validation methods
        values = instance.model_dump()
        values = cls.validate_contradictory_states(values)
        values = cls.validate_semantic_consistency(values)

        return instance

    @staticmethod
    def check_duplicate_id(task_id: str):
        """Check if a task ID already exists in the database."""
        if task_id:
            from salesforce.SimulationEngine.db import DB
            from salesforce.SimulationEngine.custom_errors import TaskDuplicateIdError

            if "Task" in DB and task_id in DB["Task"]:
                raise TaskDuplicateIdError(f"Task with ID '{task_id}' already exists. Cannot create duplicate task.")

    @staticmethod
    def generate_unique_id():
        """Generate a unique task ID."""
        return str(uuid.uuid4()).replace('-', '')[:18]  # Ensure it's 18 characters

    @staticmethod
    def check_referential_integrity(ref_id: str, field_name: str):
        """Check if referenced IDs actually exist in the database."""
        if ref_id is None:
            return

        from salesforce.SimulationEngine.db import DB
        from salesforce.SimulationEngine.custom_errors import TaskReferentialIntegrityError

        # Check in various collections based on typical Salesforce ID patterns
        # This is a simplified check - in real Salesforce, this would be more sophisticated
        found = False

        # Check Task collection
        if "Task" in DB and ref_id in DB["Task"]:
            found = True
        # Check Event collection  
        elif "Event" in DB and ref_id in DB["Event"]:
            found = True
        # For WhoId, typically points to Contact or Lead (we'll assume it exists if it has proper format)
        # For WhatId, typically points to Account, Opportunity, etc. (we'll assume it exists if it has proper format)
        elif field_name in ["WhoId", "WhatId"]:
            # In a real implementation, we'd check Contact, Lead, Account, Opportunity collections
            # For now, we'll just validate the format was already checked above
            found = True

        if not found and field_name not in ["WhoId", "WhatId"]:
            raise TaskReferentialIntegrityError(f"{field_name} '{ref_id}' does not reference an existing record.")

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

class EventUpsertModel(BaseModel):
    """
    Pydantic model for validating the parameters passed to the upsert function.
    All fields are optional, reflecting that any subset of these can be provided for upsert.
    """
    Name: Optional[str] = None
    Id: Optional[str] = None
    Subject: Optional[str] = None
    StartDateTime: Optional[str] = None
    EndDateTime: Optional[str] = None
    Description: Optional[str] = None
    Location: Optional[str] = None
    IsAllDayEvent: Optional[bool] = None
    OwnerId: Optional[str] = None
    WhoId: Optional[str] = None
    WhatId: Optional[str] = None

    class Config:
        extra = 'ignore'


class RetrieveEventInput(BaseModel):
    event_id: str

    @field_validator("event_id", mode="before")
    def validate_event_id(cls, v):
        if not v:
            raise ValueError("event_id is required")
        if not isinstance(v, str):
            raise ValueError("event_id must be a string")
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

class SearchTermModel(BaseModel):
    """
    Pydantic model for validating search term input.
    Allows empty or whitespace-only search terms which will return all events.
    """
    search_term: str = Field(description="Search term to find in event fields")
    
    @classmethod
    def validate_search_term(cls, search_term: str) -> str:
        """
        Validates and normalizes the search term.
        
        Args:
            search_term (str): The search term to validate
            
        Returns:
            str: Normalized search term (stripped and converted to lowercase)
            
        Raises:
            ValueError: If search_term is None
            TypeError: If search_term is not a string
        """
        if search_term is None:
            raise ValueError("search_term cannot be None")
        
        if not isinstance(search_term, str):
            raise TypeError("search_term must be a string")
        
        # Allow empty or whitespace-only search terms (return all events)
        return search_term.strip().lower()

class RetrieveTaskInput(BaseModel):
    task_id: str

    @field_validator("task_id", mode="before")
    def validate_task_id(cls, v):
        if not v:
            raise ValueError("task_id is required")
        if not isinstance(v, str):
            raise ValueError("task_id must be a string")
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

class TaskUpsertModel(BaseModel):
    """
    Pydantic model for validating the parameters passed to the Task.upsert function.
    All fields are optional to allow partial upserts.
    """

    Id: Optional[str] = None
    Name: Optional[str] = None
    Subject: Optional[str] = None
    Priority: Optional[str] = None
    Status: Optional[str] = None
    Description: Optional[str] = None
    ActivityDate: Optional[str] = None
    OwnerId: Optional[str] = None
    WhoId: Optional[str] = None
    WhatId: Optional[str] = None
    IsReminderSet: Optional[bool] = None
    ReminderDateTime: Optional[str] = None

    @field_validator("Id", "Name", "Subject", "Priority", "Status", 
                     "Description", "OwnerId", "WhoId", "WhatId", mode="before")
    def validate_string_fields(cls, v, info):
        if v is not None and not isinstance(v, str):
            raise ValueError(f"{info.field_name} must be a string if provided.")
        return v

    @field_validator("ActivityDate", "ReminderDateTime", mode="before")
    def validate_datetime_fields(cls, v, info):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError(f"{info.field_name} must be a string in ISO 8601 format.")
            try:
                # Allow only valid ISO 8601 date/datetime
                datetime.datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"{info.field_name} must be a valid ISO 8601 datetime string.")
        return v

    @field_validator("IsReminderSet", mode="before")
    def validate_boolean_field(cls, v, info):
        if v is not None and not isinstance(v, bool):
            raise ValueError(f"{info.field_name} must be a boolean if provided.")
        return v

    model_config = ConfigDict(
        extra="forbid",  # No unexpected fields allowed
        strict=True
    )
class GetUpdatedInput(BaseModel):
    """
    Pydantic model for validating getUpdated() function parameters.
    Implements Salesforce API validation rules for data replication.
    """
    sObjectType: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @field_validator("sObjectType")
    def validate_sObjectType(cls, v):
        if not isinstance(v, str):
            raise ValueError("sObjectType must be a string")
        if not v.strip():
            raise ValueError("sObjectType cannot be empty")
        return v

    @field_validator("start_date", "end_date")
    def validate_date_format(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Date must be a string")
            try:
                # Parse the date and ignore seconds portion as per Salesforce spec
                dt = datetime.datetime.fromisoformat(v.replace('Z', '+00:00'))
                dt = dt.replace(second=0, microsecond=0)
            except ValueError:
                raise ValueError("Date must be in valid ISO 8601 format")
        return v

    @field_validator("end_date")
    def validate_date_range(cls, v, info):
        start_date = info.data.get("start_date")
        if start_date is not None and v is not None:
            start_dt = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00')).replace(second=0, microsecond=0)
            end_dt = datetime.datetime.fromisoformat(v.replace('Z', '+00:00')).replace(second=0, microsecond=0)
            if start_dt >= end_dt:
                raise ValueError("startDate must chronologically precede endDate by more than one minute")
        return v

    class Config:
        extra = 'forbid'

class GetUpdatedResult(BaseModel):
    """
    Pydantic model for the result of getUpdated() call.
    Contains metadata about the update query and an array of updated record IDs.
    """
    ids: list
    latestDateCovered: Optional[str] = None

    class Config:
        extra = 'forbid'

class UndeleteTaskOutput(BaseModel):
    task_id: str
    success: bool

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )


class UndeleteEventOutput(BaseModel):
    Id: str
    success: bool

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

class TaskUpdateModel(BaseModel):
    task_id: str
    Name: Optional[str] = None
    Subject: Optional[str] = None
    Priority: Optional[str] = None
    Status: Optional[str] = None
    Description: Optional[str] = None
    ActivityDate: Optional[str] = None
    OwnerId: Optional[str] = None
    WhoId: Optional[str] = None
    WhatId: Optional[str] = None
    IsReminderSet: Optional[bool] = None
    ReminderDateTime: Optional[str] = None

    @field_validator("task_id", mode="before")
    def validate_task_id(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("task_id must be a non-empty string.")
        return v

    @field_validator("Name", "Subject", "Priority", "Status", "Description",
                     "OwnerId", "WhoId", "WhatId", mode="before")
    def validate_optional_string_fields(cls, v, info):
        if v is not None and not isinstance(v, str):
            raise ValueError(f"{info.field_name} must be a string if provided.")
        return v

    @field_validator("ActivityDate", "ReminderDateTime", mode="before")
    def validate_iso_datetime(cls, v, info):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError(f"{info.field_name} must be a string in ISO 8601 format.")
        try:
            datetime.datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"{info.field_name} must be a valid ISO 8601 datetime string.")
        return v

    @field_validator("IsReminderSet", mode="before")
    def validate_boolean(cls, v, info):
        if v is not None and not isinstance(v, bool):
            raise ValueError(f"{info.field_name} must be a boolean if provided.")
        return v

    model_config = ConfigDict(
        extra="forbid",  # Disallow unexpected fields
        strict=True
    )
    
class ConditionStringModel(BaseModel):
    """
    Pydantic model for validating individual condition strings.
    """
    condition: str = Field(..., description="A single condition string to validate")
    
    @field_validator('condition')
    @classmethod
    def validate_condition_format(cls, v: str) -> str:
        """Validate that the condition string has a valid format."""
        if not isinstance(v, str):
            raise ValueError("Condition must be a string")
        
        if not v.strip():
            raise ValueError("Condition cannot be empty or whitespace only")
        
        # Check for supported operators
        supported_operators = ['=', 'IN', 'LIKE', 'CONTAINS', '>', '<']

        has_supported_operator = any(re.search(rf'(^|\s){operator}($|\s|\.)', v, re.IGNORECASE) for operator in supported_operators)
        
        if not has_supported_operator:
            raise custom_errors.UnsupportedOperatorError(f"Condition must contain one of the supported operators: {', '.join(supported_operators)}")
        
        return v.strip()


class ConditionsListModel(RootModel[List[str]]):
    """
    Pydantic model for validating a list of condition strings.
    """
    
    @field_validator('root')
    @classmethod
    def validate_conditions_list(cls, v: List[str]) -> List[str]:
        """Validate that the input is a list of valid condition strings."""
        if not isinstance(v, list):
            raise ValueError("Conditions must be a list")
        
        if not v:
            raise ValueError("Conditions list cannot be empty")
        
        # Validate each condition string
        validated_conditions = []
        for i, condition in enumerate(v):
            try:
                validated_condition = ConditionStringModel(condition=condition).condition
                validated_conditions.append(validated_condition)
            except ValidationError as e:
                raise ValueError(f"Invalid condition at index {i}: {e}")
        
        return validated_conditions

