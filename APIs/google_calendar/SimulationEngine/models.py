import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator, EmailStr
from typing import Optional, List, Dict, Any, Literal
from pydantic import Field, ValidationError

from APIs.common_utils.datetime_utils import is_datetime_of_format, is_offset_valid, is_timezone_valid, is_date_of_format
from .recurrence_validator import validate_recurrence_rules
from .utils import sanitize_calendar_text_fields, parse_iso_datetime
from .custom_errors import InvalidInputError

class CalendarListResourceInput(BaseModel):
    """
    Pydantic model for validating the 'resource' input dictionary
    for creating a calendar list entry.
    """
    
    model_config = ConfigDict(extra="forbid")
    
    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    timeZone: Optional[str] = "UTC"
    primary: bool = False

    @field_validator('summary')
    @classmethod
    def validate_summary_xss(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize summary field to prevent XSS attacks.
        
        Args:
            v: The summary string to validate
            
        Returns:
            The sanitized summary string or None
            
        Raises:
            ValueError: If the summary contains XSS patterns
        """
        if v is not None:
            v = v.strip()
            if v == "":
                raise ValueError("summary cannot be empty if provided")
            return sanitize_calendar_text_fields(v, "summary")
        return v

    @field_validator('description')
    @classmethod
    def validate_description_xss(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize description field to prevent XSS attacks.
        
        Args:
            v: The description string to validate
            
        Returns:
            The sanitized description string or None
            
        Raises:
            ValueError: If the description contains XSS patterns
        """
        if v is not None:
            # The official API allows empty descriptions, so we should too
            v = v.strip()
            if v == "":
                return ""  # Return empty string instead of raising error
            return sanitize_calendar_text_fields(v, "description")
        return v

    @field_validator('id')
    @classmethod
    def validate_id_security(cls, v: str) -> str:
        """
        Validate that the id field is secure and doesn't contain path traversal patterns.
        
        Args:
            v: The id string to validate
            
        Returns:
            The validated id string
            
        Raises:
            ValueError: If the id contains dangerous patterns
        """
        if not v or not v.strip():
            raise ValueError("id cannot be empty or None")
        
        # Check for path traversal patterns
        dangerous_patterns = [
            '../', '..\\', '/..', '\\..',  # Path traversal
            '..%2f', '..%5c', '%2e%2e%2f', '%2e%2e%5c',  # URL encoded path traversal
            '....//', '....\\\\',  # Double encoded
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"id contains potentially dangerous path traversal pattern: {pattern}")
        
        # Check for other dangerous characters that could be used for injection
        dangerous_chars = ['<', '>', '|', '&', ';', '`', '$', '(', ')', '{', '}']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"id contains potentially dangerous character: {char}")
        
        # Ensure id is reasonable length (Google Calendar IDs are typically much shorter)
        if len(v) > 255:
            raise ValueError("id is too long (maximum 255 characters)")
        
        return v.strip()

    @field_validator('timeZone')
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that timeZone is a valid IANA time zone if provided.

        Args:
            v: The timezone string to validate

        Returns:
            The validated timezone string or None
            
        Raises:
            ValueError: If the timezone is an empty string or not a valid IANA time zone
        """
        if v is not None:
            v = v.strip()
            if v == "":
                raise ValueError("timeZone cannot be empty if provided")
            
            if not is_timezone_valid(v):
                raise ValueError(f"Invalid IANA time zone: '{v}'. Must be a valid IANA time zone (e.g., 'America/New_York', 'Europe/London')")
        return v

class PatchCalendarListResourceInput(BaseModel):
    """
    Pydantic model for validating the 'resource' input dictionary
    for patching a calendar list entry.
    """
    summary: Optional[str] = None
    description: Optional[str] = None
    timeZone: Optional[str] = None

    @field_validator('summary')
    @classmethod
    def validate_summary_xss(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize summary field to prevent XSS attacks.
        
        Args:
            v: The summary string to validate
            
        Returns:
            The sanitized summary string or None
            
        Raises:
            ValueError: If the summary contains XSS patterns
        """
        if v is not None:
            v = v.strip()
            if v == "":
                raise ValueError("summary cannot be empty if provided")
            return sanitize_calendar_text_fields(v, "summary")
        return v

    @field_validator('description')
    @classmethod
    def validate_description_xss(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize description field to prevent XSS attacks.
        
        Args:
            v: The description string to validate
            
        Returns:
            The sanitized description string or None
            
        Raises:
            ValueError: If the description contains XSS patterns
        """
        if v is not None:
            # The official API allows empty descriptions, so we should too
            v = v.strip()
            if v == "":
                return ""  # Return empty string instead of raising error
            return sanitize_calendar_text_fields(v, "description")
        return v

    @field_validator('timeZone')
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that timeZone is a valid IANA time zone and secure against command injection patterns.
        
        Performs comprehensive validation including:
        - IANA timezone format validation using ZoneInfo
        - Security checks for command injection patterns
        - Format validation (letters, underscores, forward slashes only)
        - Length validation (maximum 50 characters)
        
        Args:
            v: The timezone string to validate
            
        Returns:
            The validated timezone string or None
            
        Raises:
            ValueError: If the timezone is empty, invalid IANA format, contains dangerous patterns,
                       has invalid format, or exceeds maximum length
        """
        if v is None:
            return v
            
        v = v.strip()
        if v == "":
            raise ValueError("timeZone cannot be empty if provided")

        # Check for command injection patterns
        dangerous_patterns = [
            ';', '|', '&', '`', '$',  # Command separators and substitution
            '$(', '${', '`',  # Command substitution
            '||', '&&',  # Logical operators
            '<', '>',  # Redirection
            '\\',  # Escape characters
        ]
        
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"timeZone contains potentially dangerous command injection pattern: {pattern}")
        
        # Validate that it looks like a valid timezone format
        # Timezones should be in format like "America/New_York", "UTC", "Europe/London", etc.

        timezone_pattern = r'^[A-Za-z_/]+$'
        if not re.match(timezone_pattern, v):
            raise ValueError("timeZone must contain only letters, underscores, and forward slashes")
        
        # Ensure timezone is reasonable length
        if len(v) > 50:
            raise ValueError("timeZone is too long (maximum 50 characters)")
        
        if not is_timezone_valid(v):
            raise ValueError(f"Invalid IANA time zone: '{v}'. Must be a valid IANA time zone (e.g., 'America/New_York', 'Europe/London')")

        return v

class ConferencePropertiesModel(BaseModel):
    """
    Pydantic model for conference-related properties.
    """
    allowedConferenceSolutionTypes: Optional[List[Literal["eventHangout", "eventNamedHangout", "hangoutsMeet"]]] = None

class CalendarResourceInputModel(BaseModel):
    """
    Pydantic model for the input 'resource' dictionary.
    """
    summary: str = Field(..., description="Title of the calendar (required)")
    id: Optional[str] = None
    description: Optional[str] = None
    timeZone: Optional[str] = "UTC"
    location: Optional[str] = None
    etag: Optional[str] = None
    kind: Optional[Literal["calendar#calendar"]] = None
    conferenceProperties: Optional[ConferencePropertiesModel] = None

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that the id field doesn't contain path traversal patterns or colons.
        
        Args:
            v: The id string to validate
            
        Returns:
            The validated id string
            
        Raises:
            ValueError: If the id contains dangerous patterns
        """
        if v is None:
            return v

        if not v.strip():
            raise ValueError("id cannot be empty if provided")
        
        if ':' in v:
            raise ValueError("id cannot contain colon")
        
        # Check for path traversal patterns
        dangerous_patterns = [
            '../', '..\\', '/..', '\\..',  # Path traversal
            '..%2f', '..%5c', '%2e%2e%2f', '%2e%2e%5c',  # URL encoded path traversal
            '....//', '....\\\\',  # Double encoded
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"id contains potentially dangerous path traversal pattern: {pattern}")
        
        # Check for other dangerous characters that could be used for injection
        dangerous_chars = ['<', '>', '|', '&', ';', '`', '$', '(', ')', '{', '}']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"id contains potentially dangerous character: {char}")
              
        return v.strip()

    @field_validator('summary')
    @classmethod
    def summary_must_not_be_empty(cls, v: str) -> str:
        """Validate that summary is a non-empty string and sanitize for XSS."""
        if not isinstance(v, str):
            raise TypeError("Summary must be a string.")
        if not v.strip():
            raise ValueError("summary cannot be empty")
        return sanitize_calendar_text_fields(v, "summary")
    
    @field_validator('description')
    @classmethod
    def description_sanitize_xss(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description field to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_calendar_text_fields(v, "description")
    
    @field_validator('location')
    @classmethod
    def location_sanitize_xss(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize location field to prevent XSS attacks."""
        if v is None:
            return v
        return sanitize_calendar_text_fields(v, "location")

class UpdateCalendarInputResourceModel(BaseModel):
    """
    Pydantic model for the input 'resource' dictionary with comprehensive security validation.
    """
    model_config = ConfigDict(extra="forbid")  # Prevent mass assignment attacks
    
    summary: str = Field(..., description="Title of the calendar (required)")
    description: Optional[str] = None
    timeZone: Optional[str] = None
    location: Optional[str] = None

    @field_validator('summary')
    @classmethod
    def summary_must_not_be_empty(cls, v: str) -> str:
        """Validate that summary is a non-empty string and sanitize for XSS."""
        if not isinstance(v, str):
            raise TypeError("Summary must be a string.")
        if not v.strip():
            raise ValueError("Summary cannot be empty.")
        return sanitize_calendar_text_fields(v, "summary")
    
    @field_validator('description')
    @classmethod
    def description_sanitize_xss(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description field to prevent XSS attacks."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise TypeError("Description must be a string.")
        return sanitize_calendar_text_fields(v, "description")
    
    @field_validator('timeZone')
    @classmethod
    def validate_timezone_iana(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that timeZone is a valid IANA time zone if provided.
        
        Args:
            v: The timezone string to validate
            
        Returns:
            The validated timezone string or None
            
        Raises:
            ValueError: If the timezone is an empty string or not a valid IANA time zone
        """
        if v is not None:
            if v.strip() == "":
                raise ValueError("timeZone cannot be empty if provided")
            if not is_timezone_valid(v):
                raise ValueError(f"Invalid IANA time zone: '{v}'. Must be a valid IANA time zone (e.g., 'America/New_York', 'Europe/London')")
        return v
    
    @field_validator('location')
    @classmethod
    def location_sanitize_xss(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize location field to prevent XSS attacks."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise TypeError("Location must be a string.")
        return sanitize_calendar_text_fields(v, "location")

    @field_validator('timeZone')
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that timeZone is a valid IANA time zone if provided.
        
        Args:
            v: The timezone string to validate
            
        Returns:
            The validated timezone string or None
            
        Raises:
            ValueError: If the timezone is an empty string or not a valid IANA time zone
        """
        if v is not None:
            if v.strip() == "":
                raise ValueError("timeZone cannot be empty if provided")
            if not is_timezone_valid(v):
                raise ValueError(f"Invalid IANA time zone: '{v}'. Must be a valid IANA time zone (e.g., 'America/New_York', 'Europe/London')")
        return v

class EventDateTimeModel(BaseModel):
    """
    Pydantic model for event start/end times.
    """
    date: Optional[str] = None
    dateTime: Optional[str] = None
    timeZone: Optional[str] = None

    @model_validator(mode='after')
    def validate_datetime_and_timezone(self) -> 'EventDateTimeModel':
        """Validate that date, dateTime and timeZone are valid for Google Calendar."""
        # Import here to avoid circular imports
        from common_utils.datetime_utils import validate_google_calendar_datetime, DateTimeValidationError
        
        try:
            # Use centralized datetime validation and return normalized values
            normalized_date, normalized_datetime, normalized_timezone = validate_google_calendar_datetime(
                date=self.date, dateTime=self.dateTime, timeZone=self.timeZone
            )
            self.date = normalized_date
            self.dateTime = normalized_datetime
            self.timeZone = normalized_timezone
            return self
        except DateTimeValidationError as e:
            # Import here to avoid circular imports
            # Provide context about which field is invalid and the actual values
            field_context = []
            if self.date is not None:
                field_context.append(f"date='{self.date}'")
            if self.dateTime is not None:
                field_context.append(f"dateTime='{self.dateTime}'")
            if self.timeZone is not None:
                field_context.append(f"timeZone='{self.timeZone}'")
            
            context_str = ", ".join(field_context) if field_context else "no fields provided"
            raise DateTimeValidationError(f"Invalid datetime format for Google Calendar ({context_str}): {e}")

    class Config:
        extra = "allow"  # Allow other fields as base type is Dict[str, Any]

class EventDateTimeDBModel(BaseModel):
    """
    Pydantic model for event start/end times in the DB.
    """
    date: Optional[str] = None
    dateTime: Optional[str] = None
    offset: Optional[str] = None
    timeZone: Optional[str] = None

    @model_validator(mode='after')
    def validate_fields(self) -> 'EventDateTimeDBModel':
        """Validate that dateTime, offset, and timeZone are valid for a Google Calendar DB."""
      
        if self.date and not is_date_of_format(self.date, "YYYY-MM-DD"):
            raise ValueError("Invalid date")
        if self.dateTime and not is_datetime_of_format(self.dateTime, "YYYY-MM-DDTHH:MM:SS"):
            raise ValueError("Invalid dateTime")
        if self.offset and not is_offset_valid(self.offset):
            raise ValueError("Invalid offset")
        if self.timeZone and not is_timezone_valid(self.timeZone):
            raise ValueError("Invalid timeZone")
        if self.date and self.dateTime:
            raise ValueError("date and dateTime cannot be provided at the same time")
        if not self.date and not self.dateTime:
            raise ValueError("Either date or dateTime must be provided")
        if self.dateTime and not self.offset:
            raise ValueError("If dateTime is provided, offset must be provided.")        
        return self

    class Config:
        extra = "allow"  # Allow other fields as base type is Dict[str, Any]

class AttendeeModel(BaseModel):
    """Pydantic model for an event attendee."""
    email: Optional[EmailStr] = None
    displayName: Optional[str] = None
    organizer: Optional[bool] = None
    self: Optional[bool] = None # Field name 'self' needs alias for Pydantic model if it conflicts
    resource: Optional[bool] = None
    optional: Optional[bool] = None
    responseStatus: Optional[str] = None
    comment: Optional[str] = None
    additionalGuests: Optional[int] = None

    @field_validator('additionalGuests')
    @classmethod
    def validate_additional_guests(cls, v: Optional[int]) -> Optional[int]:
        """Validate that additionalGuests is a non-negative integer."""
        if v is not None and v < 0:
            raise ValueError("Additional guests must be a non-negative integer.")
        return v

    class Config:
        extra = "allow" # Allow other fields as base type is Dict[str, Any]
        
class ReminderOverrideModel(BaseModel):
    """Pydantic model for reminder overrides."""
    method: Optional[str] = None
    minutes: Optional[int] = None

    class Config:
        extra = "allow"

class RemindersModel(BaseModel):
    """Pydantic model for event reminders."""
    useDefault: Optional[bool] = None
    overrides: Optional[List[ReminderOverrideModel]] = None

    class Config:
        extra = "allow" # Allow other fields as base type is Dict[str, Any]

class AttachmentModel(BaseModel):
    """Pydantic model for an event attachment."""
    fileUrl: str

class ExtendedPropertiesModel(BaseModel):
    """Pydantic model for extended properties."""
    private: Optional[Dict[str, Any]] = None
    shared: Optional[Dict[str, Any]] = None

    class Config:
        extra = "forbid"

class EventResourceInputModel(BaseModel):
    """
    Pydantic model for validating the 'resource' argument of the create_event function.
    """
    id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    start: EventDateTimeModel = Field(..., description="Event start time")
    end: EventDateTimeModel = Field(..., description="Event end time")
    recurrence: Optional[List[str]] = None
    attendees: Optional[List[AttendeeModel]] = None
    reminders: Optional[RemindersModel] = None
    location: Optional[str] = None
    attachments: Optional[List[AttachmentModel]] = None
    extendedProperties: Optional[ExtendedPropertiesModel] = None

    @field_validator('recurrence')
    @classmethod
    def validate_recurrence(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """
        Validates recurrence rules using the RecurrenceValidator.
        
        Args:
            v: List of recurrence rule strings or None
            
        Returns:
            The validated recurrence rules
            
        Raises:
            ValueError: If any rule is invalid
        """
        if v is not None:
            try:
                validate_recurrence_rules(v)
            except Exception as e:
                raise ValueError(str(e))
        return v

    @field_validator('summary')
    @classmethod
    def validate_summary_xss(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize summary field to prevent XSS attacks."""
        if v is not None:
            return sanitize_calendar_text_fields(v, "summary")
        return v

    @field_validator('description')
    @classmethod
    def validate_description_xss(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize description field to prevent XSS attacks."""
        if v is not None:
            return sanitize_calendar_text_fields(v, "description")
        return v

    @field_validator('location')
    @classmethod
    def validate_location_xss(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize location field to prevent XSS attacks."""
        if v is not None:
            return sanitize_calendar_text_fields(v, "location")
        return v

    @model_validator(mode='after')
    def validate_start_end_times(self):
        """Validate that start time is before end time."""
        if self.start.dateTime is not None and self.end.dateTime is not None:
            start_dt = parse_iso_datetime(self.start.dateTime)
            end_dt = parse_iso_datetime(self.end.dateTime)
        elif self.start.date is not None and self.end.date is not None:
            start_dt = parse_iso_datetime(self.start.date)
            end_dt = parse_iso_datetime(self.end.date)
        else:
            return self

        # For all-day events, start and end can be the same date
        if self.start.date is not None and self.end.date is not None:
            # All-day event - only check if end is before start
            if end_dt < start_dt:
                raise InvalidInputError("Start time must be before end time.")
        else:
            # DateTime event - end must be after start
            if start_dt >= end_dt:
                raise InvalidInputError("Start time must be before end time.")

        return self

    class Config:
        extra = "forbid"

class EventResourceDBModel(BaseModel):
    """
    Pydantic model for some event in the DB.
    """
    id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    start: EventDateTimeDBModel = Field(..., description="Event start time")
    end: EventDateTimeDBModel = Field(..., description="Event end time")
    recurrence: Optional[List[str]] = None
    attendees: Optional[List[AttendeeModel]] = None
    reminders: Optional[RemindersModel] = None
    location: Optional[str] = None
    attachments: Optional[List[AttachmentModel]] = None
    extendedProperties: Optional[ExtendedPropertiesModel] = None

    @field_validator('recurrence')
    @classmethod
    def validate_recurrence(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """
        Validates recurrence rules using the RecurrenceValidator.
        
        Args:
            v: List of recurrence rule strings or None
            
        Returns:
            The validated recurrence rules
            
        Raises:
            ValueError: If any rule is invalid
        """
        if v is not None:
            try:
                validate_recurrence_rules(v)
            except Exception as e:
                raise ValueError(str(e))
        return v

    class Config:
        extra = "forbid"

class EventPatchResourceModel(BaseModel):
    """Pydantic model for the 'resource' argument of patch_event."""
    summary: Optional[str] = None
    id: Optional[str] = None
    description: Optional[str] = None
    start: Optional[EventDateTimeModel] = None
    end: Optional[EventDateTimeModel] = None
    attendees: Optional[List[AttendeeModel]] = None
    location: Optional[str] = None
    recurrence: Optional[List[str]] = None
    reminders: Optional[RemindersModel] = None
    attachments: Optional[List[AttachmentModel]] = None

    @model_validator(mode='after')
    def validate_start_end_times(self):
        if self.start is None or self.end is None:
            return self
        
        if self.start.dateTime is not None and self.end.dateTime is not None:
            start_dt = parse_iso_datetime(self.start.dateTime)
            end_dt = parse_iso_datetime(self.end.dateTime)
        elif self.start.date is not None and self.end.date is not None:
            start_dt = parse_iso_datetime(self.start.date)
            end_dt = parse_iso_datetime(self.end.date)

        if start_dt >= end_dt:
            raise InvalidInputError("Start time must be before end time.")

        return self

    @model_validator(mode='after')
    def validate_sanitize_xss_attack(self):
        fields_to_validate = {'summary':self.summary, 'description':self.description, 'location':self.location}
        for field_name, field_value in fields_to_validate.items():
            try:
                field_value = sanitize_calendar_text_fields(field_value, field_name)
            except Exception as e:
                raise e
        return self

    @field_validator('recurrence')
    @classmethod
    def validate_recurrence(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """
        Validates recurrence rules using the RecurrenceValidator.
        
        Args:
            v: List of recurrence rule strings or None
            
        Returns:
            The validated recurrence rules
            
        Raises:
            InvalidInputError: If any rule is invalid
        """
        if v is not None:
            try:
                validate_recurrence_rules(v)
            except Exception as e:
                raise InvalidInputError(str(e))
        return v

    class Config:
        extra = "forbid" # Disallow any fields in 'resource' not defined in this model


class ScopeModel(BaseModel):
    """
    Pydantic model for validating scope in access control rules.
    """
    type: str
    value: Optional[EmailStr] = None  # Use EmailStr for email validation, optional for default type
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if not v or not v.strip():
            raise ValueError("Scope type cannot be empty or whitespace")
        return v.strip()
    
    @model_validator(mode='after')
    def validate_value_required(self):
        # For non-default types, value is required
        if self.type != "default" and self.value is None:
            raise ValueError("Scope value is required for non-default types")
        return self


class AccessControlRuleModel(BaseModel):
    """
    Pydantic model for validating access control rule creation.
    """
    model_config = ConfigDict(extra="forbid")
    
    role: str
    scope: ScopeModel
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if not v or not v.strip():
            raise ValueError("Role cannot be empty or whitespace")
        return v.strip()


class AccessControlRuleUpdateModel(BaseModel):
    """
    Pydantic model for validating access control rule updates.
    """
    model_config = ConfigDict(extra="forbid")
    
    role: Optional[str] = None
    scope: Optional[ScopeModel] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Role cannot be empty or whitespace")
        return v.strip() if v else v
