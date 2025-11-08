from APIs.common_utils.datetime_utils import is_offset_valid, is_datetime_of_format, is_timezone_valid
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Dict, Literal
from pydantic import Field
from .recurrence_validator import validate_recurrence_rules

# --- Shared Models ---
class RoleModel(BaseModel):
    """
    Model representing a role assignment.
    Used for ACL rules and calendar permissions.
    
    Attributes:
        role: The role value (owner, writer, reader, etc.)
    """
    role: Literal['owner', 'writer', 'reader', 'editor', 'commenter', 'organizer', 'viewer', 'freeBusyReader'] = Field(
        ..., 
        description="Role assigned to the user or entity"
    )
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role value."""
        valid_roles = ['owner', 'writer', 'reader', 'editor', 'commenter', 'organizer', 'viewer', 'freeBusyReader']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v


class EventDateTimeModel(BaseModel):
    """
    Pydantic model for event start/end times.
    """
    dateTime: Optional[str] = None
    offset: Optional[str] = None
    timeZone: Optional[str] = None

    @field_validator('dateTime')
    @classmethod
    def validate_datetime(cls, v: Optional[str]) -> Optional[str]:
        """Validate datetime using centralized validation."""
        if v is not None:
            if not is_datetime_of_format(v, "YYYY-MM-DDTHH:MM:SS"):
                raise ValueError(f"Invalid datetime format: {v}")
        return v

    @field_validator('timeZone')
    @classmethod
    def validate_timeZone(cls, v: Optional[str]) -> Optional[str]:
        """Validate timeZone using centralized validation."""
        if v is not None:
            if not is_timezone_valid(v):
                raise ValueError(f"Invalid timezone: {v}")
        return v
    
    @field_validator('offset')
    @classmethod
    def validate_offset(cls, v: Optional[str]) -> Optional[str]:
        """Validate offset using centralized validation."""
        if v is not None:
            try:
                if not is_offset_valid(v):
                    raise ValueError(f"Invalid offset format: {v}")
            except Exception as e:
                raise ValueError(f"Invalid offset format: {e}")
        return v

class AttendeeModel(BaseModel):
    """Pydantic model for an event attendee."""
    email: Optional[str] = None
    displayName: Optional[str] = None
    organizer: Optional[bool] = None
    self: Optional[bool] = None # Field name 'self' needs alias for Pydantic model if it conflicts
    resource: Optional[bool] = None
    optional: Optional[bool] = None
    responseStatus: Optional[str] = None
    comment: Optional[str] = None
    additionalGuests: Optional[int] = None

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

# --- Database Models (for database structure) ---

class AclScopeModel(BaseModel):
    """Pydantic model for ACL scope."""
    type: str = Field(..., description="Type of scope (user, domain, group, etc.)")
    value: str = Field(..., description="Value of the scope")

class AclRuleModel(BaseModel):
    """Pydantic model for ACL rules."""
    ruleId: str = Field(..., description="Unique identifier for the ACL rule")
    calendarId: str = Field(..., description="ID of the calendar this rule applies to")
    scope: AclScopeModel = Field(..., description="Scope of the ACL rule")
    role: Literal['owner', 'writer', 'reader', 'editor', 'commenter', 'organizer', 'viewer', 'freeBusyReader'] = Field(
        ..., 
        description="Role assigned (owner, writer, reader, etc.)"
    )

class CalendarModel(BaseModel):
    """
    Pydantic model for calendars.
    Used for both calendar_list and calendars in the database.
    """
    id: str = Field(..., description="Unique identifier for the calendar")
    summary: str = Field(..., description="Summary/name of the calendar")
    description: Optional[str] = Field(None, description="Description of the calendar")
    timeZone: Optional[str] = Field(None, description="Time zone of the calendar")
    primary: bool = Field(False, description="Whether this is the primary calendar")

class ChannelModel(BaseModel):
    """Pydantic model for channels (webhooks)."""
    id: str = Field(..., description="Unique identifier for the channel")
    type: str = Field(..., description="Type of channel (e.g., web_hook)")
    resource: str = Field(..., description="Resource type this channel monitors")
    calendarId: Optional[str] = Field(None, description="ID of the calendar this channel is associated with")

class ColorModel(BaseModel):
    """Pydantic model for color definitions."""
    background: str = Field(..., description="Background color in hex format")
    foreground: str = Field(..., description="Foreground color in hex format")

class ColorsModel(BaseModel):
    """Pydantic model for color collections."""
    calendar: Dict[str, ColorModel] = Field(default_factory=dict, description="Calendar colors")
    event: Dict[str, ColorModel] = Field(default_factory=dict, description="Event colors")

class AttachmentModel(BaseModel):
    """Pydantic model for event attachments."""
    fileUrl: str = Field(..., description="URL of the attached file")
    
    class Config:
        extra = "allow"


class EventModel(BaseModel):
    """Pydantic model for calendar events."""
    id: str = Field(..., description="Unique identifier for the event")
    summary: str = Field(..., description="Summary/title of the event")
    description: Optional[str] = Field(None, description="Description of the event")
    start: EventDateTimeModel = Field(..., description="Start time of the event")
    end: EventDateTimeModel = Field(..., description="End time of the event")
    attendees: Optional[List[AttendeeModel]] = Field(None, description="List of event attendees")
    attachments: Optional[List[AttachmentModel]] = Field(None, description="List of event attachments")
    location: Optional[str] = Field(None, description="Location of the event")
    recurrence: Optional[List[str]] = Field(None, description="Recurrence rules")
    reminders: Optional[RemindersModel] = Field(None, description="Event reminders")
 
    @field_validator('recurrence')
    @classmethod
    def validate_recurrence(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate recurrence using centralized validation."""
        if v is not None:
            try:
                validate_recurrence_rules(v)
            except Exception as e:
                raise ValueError(str(e))
        return v
    
    class Config:
        extra = "allow"

class GoogleCalendarDB(BaseModel):
    """
    Main database model for Google Calendar API.
    Represents the complete structure of the Google Calendar database.
    """
    # ACL Rules - Access Control List rules for calendars
    acl_rules: Dict[str, AclRuleModel] = Field(
        default_factory=dict, 
        description="Access Control List rules for calendar permissions"
    )
    
    # Calendar List - User's list of calendars (uses same model as calendars)
    calendar_list: Dict[str, CalendarModel] = Field(
        default_factory=dict, 
        description="User's calendar list entries"
    )
    
    # Calendars - Actual calendar objects
    calendars: Dict[str, CalendarModel] = Field(
        default_factory=dict, 
        description="Calendar objects"
    )
    
    # Channels - Webhook channels for notifications
    channels: Dict[str, ChannelModel] = Field(
        default_factory=dict, 
        description="Webhook channels for calendar notifications"
    )
    
    # Colors - Color definitions for calendars and events
    colors: ColorsModel = Field(
        default_factory=ColorsModel, 
        description="Color definitions for calendars and events"
    )
    
    # Events - Calendar events
    events: Dict[str, EventModel] = Field(
        default_factory=dict, 
        description="Calendar events (key format: calendarId:eventId)"
    )

    class Config:
        extra = "forbid" # Disallow any fields not defined in this model