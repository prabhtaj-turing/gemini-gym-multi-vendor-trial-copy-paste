from typing import Optional, List, Dict, Any
from pydantic import (
    BaseModel, 
    ConfigDict, 
    Field, 
    validator, 
    ValidationError, 
    field_validator, 
    EmailStr, 
    TypeAdapter
)
import json
from datetime import datetime
from .custom_errors import InvalidTimestampFormatError
validate_email = lambda email: TypeAdapter(EmailStr).validate_python(email)


class AddReminderInput(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID to remind. Cannot be empty.")
    text: str = Field(..., min_length=1, description="The content of the reminder. Cannot be empty.")
    ts: str = Field(..., min_length=1, description="When this reminder should happen (unix timestamp as string). Cannot be empty.")
    channel_id: Optional[str] = Field(None, description="Channel ID to remind in. Can be None. If a string is provided, it can be empty.")

    @validator("ts")
    def validate_timestamp_format(cls, value: str) -> str:
        """Validates timestamp using centralized validation."""
        from common_utils.datetime_utils import validate_slack_timestamp, InvalidDateTimeFormatError
        try:
            return validate_slack_timestamp(value)
        except InvalidDateTimeFormatError as e:
            raise InvalidTimestampFormatError(f"Invalid timestamp format: {e}")
        except Exception as e:
            raise ValueError("must be a string representing a valid numeric timestamp (e.g., '1678886400' or '1678886400.5')")

class ParsedMetadataModel(BaseModel):
    """
    Represents the expected structure of the parsed 'metadata' JSON string.
    """
    event_type: str
    event_payload: Dict[str, Any]

class ScheduleMessageInputModel(BaseModel):
    """
    Pydantic model for validating the input arguments of the scheduleMessage function.
    """
    user_id: str = Field(..., min_length=1, description="User ID, cannot be empty.")
    channel: str = Field(..., min_length=1, description="Channel to send the message to, cannot be empty.")
    post_at: int # Validated by a custom validator to match original logic and ensure it's positive.

    attachments: Optional[str] = None
    blocks: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None
    as_user: bool = False
    link_names: bool = False
    markdown_text: Optional[str] = None
    metadata: Optional[str] = None # Custom validator will parse and check internal structure.
    parse: Optional[str] = None
    reply_broadcast: bool = False
    thread_ts: Optional[str] = None
    unfurl_links: bool = True
    unfurl_media: bool = False

    @validator('post_at', pre=True, always=True)
    def validate_and_coerce_post_at(cls, v):
        if v is None:
            raise ValueError("Invalid format or value for post_at: None")

        if isinstance(v, (int, float)) and v <= 0:
             raise ValueError("post_at must be a positive timestamp")

        try:
            # Handle numeric inputs directly
            if isinstance(v, str):
                # First try centralized validation for well-formed timestamps
                from common_utils.datetime_utils import validate_slack_timestamp, InvalidDateTimeFormatError
                try:
                    validated_str = validate_slack_timestamp(v)
                    return int(validated_str)
                except InvalidDateTimeFormatError:
                    # If centralized validation fails, try original logic for compatibility
                    val_float = float(v)
                    val_int = int(val_float)
                    if val_int <= 0:
                        raise ValueError("post_at must be a positive timestamp")
                    return val_int
            else:
                # Handle numeric inputs
                val_float = float(v)
                val_int = int(val_float)
                if val_int <= 0:
                    raise ValueError("post_at must be a positive timestamp")
                return val_int
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid format or value for post_at: {v}")


    @validator('attachments')
    def validate_attachments_string_is_json_array_of_objects(cls, v: Optional[str]):
        if v is not None:
            try:
                data = json.loads(v)
                if not isinstance(data, list):
                    raise ValueError("Attachments JSON string must decode to an array")
                for item in data:
                    if not isinstance(item, dict):
                        raise ValueError("Each item in the attachments array must be an object")
                # If AttachmentItemModel had specific fields, validation would be:
                # [AttachmentItemModel(**item) for item in data]
            except json.JSONDecodeError as e:
                raise ValueError("Attachments string is not valid JSON")
            # ValidationError would be caught if AttachmentItemModel was used and failed
        return v

    @validator('metadata')
    def validate_metadata_string_is_json_object_with_structure(cls, v: Optional[str]):
        if v is not None:
            try:
                data = json.loads(v)
                if not isinstance(data, dict): # Ensure it's an object, not array/scalar
                    raise ValueError("Metadata JSON string must decode to an object")
                # Use a try-except to get a simpler error message format
                try:
                    ParsedMetadataModel(**data) # Validate against the specific structure
                except ValidationError:
                    raise ValueError("Metadata JSON structure is invalid")
            except json.JSONDecodeError as e:
                raise ValueError("Metadata string is not valid JSON")
        return v

    # Add validators for user_id and channel to provide simple error messages
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v:  # Empty string check (min_length should handle this, but for clarity)
            raise ValueError("String should have at least 1 character")
        return v

    @validator('channel')
    def validate_channel(cls, v):
        if not v:  # Empty string check (min_length should handle this, but for clarity)
            raise ValueError("String should have at least 1 character")
        return v

    @validator('blocks', each_item=True)
    def validate_blocks_items(cls, v):
        if not isinstance(v, dict):
            # Use manual error message to match test expectations
            raise ValueError("Input should be a valid dictionary")
        return v

    class Config:
        # Fail if extra fields are passed that are not defined in the model
        extra = "forbid"
        # This makes error messages simpler, matching test expectations better
        error_msg_templates = {
            "string_too_short": "String should have at least 1 character"
        }

class BlockItemStructure(BaseModel):
    """
    Represents the expected structure for an individual item within the 'blocks' list.
    As the specific structure of a block is not detailed in the original docstring,
    this model is configured to allow any fields. A more specific application
    might define concrete fields like 'type: str', 'text: dict', etc.
    """

    class Config:
        # For Pydantic V1:
        extra = "allow"
        # For Pydantic V2, you would use:
        # from pydantic import ConfigDict
        # model_config = ConfigDict(extra='allow')



class DeleteMessageInput(BaseModel):
    channel: str
    ts: str

    @field_validator("channel", mode="before")
    def validate_channel(cls, v):
        if not v:
            raise ValueError("channel is required")
        if not isinstance(v, str):
            raise ValueError("channel must be a string")
        return v

    @field_validator("ts", mode="before")
    def validate_ts(cls, v):
        if not v:
            raise ValueError("ts is required")
        if not isinstance(v, str):
            raise ValueError("ts must be a string")
        
        try:
            ts_float = float(v)
        except ValueError:
            raise ValueError("ts must be a string representing a number")

        if ts_float < 0:
            raise ValueError("ts must be a positive Unix timestamp")

        try:
            datetime.fromtimestamp(ts_float)  # Validates it is a valid timestamp
        except (OverflowError, OSError):
            raise ValueError("ts is not a valid Unix timestamp")

        return v

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",  # Forbid unexpected fields
    )



class DeleteMessageResponse(BaseModel):
    ok: bool
    channel: Optional[str] = None
    ts: Optional[str] = None

    model_config = ConfigDict(
        strict=True,
        use_enum_values=True,
        extra="forbid",
    )


class DeleteScheduledMessageInput(BaseModel):
    channel: str
    scheduled_message_id: str

    @field_validator("channel", mode="before")
    def validate_channel(cls, v):
        if not v:
            raise ValueError("channel is required")
        if not isinstance(v, str):
            raise ValueError("channel must be a string")
        return v

    @field_validator("scheduled_message_id", mode="before")
    def validate_scheduled_message_id(cls, v):
        if not v:
            raise ValueError("scheduled_message_id is required")
        if not isinstance(v, str):
            raise ValueError("scheduled_message_id must be a string")
        return v
    

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )


class DeleteScheduledMessageResponse(BaseModel):
    ok: bool
    channel: Optional[str] = None
    scheduled_message_id: Optional[str] = None

    model_config = ConfigDict(
        strict=True,
        use_enum_values=True,
        extra="forbid",
    )


class UserProfile(BaseModel):
    """Model for user profile data."""
    display_name: Optional[str] = Field(None, description="The user's display name")
    real_name: Optional[str] = Field(None, description="The user's real name")
    email: Optional[EmailStr] = Field(None, description="The user's email address")
    phone: Optional[str] = Field(None, description="The user's phone number")
    status_emoji: Optional[str] = Field(None, description="The user's status emoji")
    status_text: Optional[str] = Field(None, description="The user's status text")
    title: Optional[str] = Field(None, description="The user's title")
    team: Optional[str] = Field(None, description="The user's team")
    skype: Optional[str] = Field(None, description="The user's Skype handle")
    first_name: Optional[str] = Field(None, description="The user's first name")
    last_name: Optional[str] = Field(None, description="The user's last name")

    class Config:
        extra = "forbid"  # Reject extra fields

    @validator('email')
    def validate_email(cls, v):
        if v is not None and '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v

class FileInfo(BaseModel):
    """Pydantic model for file information in finish_external_upload requests."""
    id: str = Field(..., description="The ID of the file")
    title: Optional[str] = Field(None, description="The title of the file")
    # Add other optional fields as needed

class FinishExternalUploadRequest(BaseModel):
    """Pydantic model for finish_external_upload request parameters."""
    files: List[FileInfo] = Field(..., description="List of file objects to upload")
    channel_id: Optional[str] = Field(None, description="Channel ID where the file will be shared")
    initial_comment: Optional[str] = Field(None, description="Initial comment for the file")
    thread_ts: Optional[str] = Field(None, description="Parent message timestamp for threading")

class SlackMessageForSearch(BaseModel):
    """Model for Slack messages adapted for search indexing."""
    ts: str
    text: str
    user: str
    channel: str
    channel_name: Optional[str] = None
    reactions: Optional[List[Dict[str, Any]]] = None
    is_starred: Optional[bool] = False
    links: Optional[List[str]] = None
    
    class Config:
        extra = "allow"


class SlackFileForSearch(BaseModel):
    """Model for Slack files adapted for search indexing."""
    id: str
    name: str
    title: Optional[str] = None
    filetype: str
    channels: List[str]
    is_starred: Optional[bool] = False
    
    class Config:
        extra = "allow"


# Database Models for Validation
class DBCurrentUser(BaseModel):
    """Database model for current user in the Slack database."""
    id: str = Field(..., description="User ID")
    is_admin: bool = Field(..., description="Whether the user is an admin")

class DBUserProfile(BaseModel):
    """Database model for user profile data."""
    email: Optional[str] = Field(None, description="User's email address")
    display_name: Optional[str] = Field(None, description="User's display name")
    image: Optional[str] = Field(None, description="User's profile image (base64 or URL)")
    image_crop_x: Optional[int] = Field(None, description="Image crop X coordinate")
    image_crop_y: Optional[int] = Field(None, description="Image crop Y coordinate")
    image_crop_w: Optional[int] = Field(None, description="Image crop width")
    title: Optional[str] = Field(None, description="User's job title")

class DBUser(BaseModel):
    """Database model for user data in the Slack database."""
    id: str = Field(..., description="User ID")
    team_id: Optional[str] = Field(None, description="Team ID")
    name: str = Field(..., description="Username")
    real_name: Optional[str] = Field(None, description="Real name")
    profile: Optional[DBUserProfile] = Field(None, description="User profile")
    is_admin: bool = Field(False, description="Whether user is admin")
    is_bot: bool = Field(False, description="Whether user is a bot")
    deleted: bool = Field(False, description="Whether user is deleted")
    presence: Optional[str] = Field(None, description="User presence status")

class DBMessageReaction(BaseModel):
    """Database model for message reactions."""
    name: str = Field(..., description="Reaction emoji name")
    users: List[str] = Field(..., description="List of user IDs who reacted")
    count: int = Field(..., description="Number of reactions")

class DBMessage(BaseModel):
    """Database model for Slack messages."""
    ts: str = Field(..., description="Message timestamp")
    user: str = Field(..., description="User ID who sent the message")
    text: str = Field(..., description="Message text")
    reactions: List[DBMessageReaction] = Field(default_factory=list, description="Message reactions")

class DBChannel(BaseModel):
    """Database model for Slack channels."""
    id: str = Field(..., description="Channel ID")
    name: str = Field(..., description="Channel name")
    messages: List[DBMessage] = Field(default_factory=list, description="Channel messages")
    conversations: Dict[str, Any] = Field(default_factory=dict, description="Channel conversations")
    is_private: bool = Field(False, description="Whether channel is private")
    team_id: Optional[str] = Field(None, description="Team ID")
    files: Dict[str, bool] = Field(default_factory=dict, description="Files in channel")

class DBFileComment(BaseModel):
    """Database model for file comments."""
    user: str = Field(..., description="User ID who commented")
    comment: str = Field(..., description="Comment text")
    timestamp: int = Field(..., description="Comment timestamp")

class DBFile(BaseModel):
    """Database model for Slack files."""
    id: str = Field(..., description="File ID")
    created: int = Field(..., description="Creation timestamp")
    timestamp: int = Field(..., description="File timestamp")
    name: str = Field(..., description="File name")
    title: str = Field(..., description="File title")
    mimetype: str = Field(..., description="MIME type")
    filetype: str = Field(..., description="File type")
    user: str = Field(..., description="User ID who uploaded the file")
    size: int = Field(..., description="File size in bytes")
    url_private: str = Field(..., description="Private URL")
    permalink: str = Field(..., description="Permalink to file")
    comments: List[DBFileComment] = Field(default_factory=list, description="File comments")
    channels: List[str] = Field(default_factory=list, description="Channels where file is shared")

class DBReminder(BaseModel):
    """Database model for Slack reminders."""
    id: str = Field(..., description="Reminder ID")
    creator_id: str = Field(..., description="Creator user ID")
    user_id: str = Field(..., description="Target user ID")
    text: str = Field(..., description="Reminder text")
    time: int = Field(..., description="Reminder time (Unix timestamp)")
    complete_ts: Optional[int] = Field(None, description="Completion timestamp")
    channel_id: Optional[str] = Field(None, description="Channel ID")

class DBUsergroupPrefs(BaseModel):
    """Database model for usergroup preferences."""
    channels: List[str] = Field(default_factory=list, description="Associated channels")
    groups: List[str] = Field(default_factory=list, description="Associated groups")

class DBUsergroup(BaseModel):
    """Database model for Slack usergroups."""
    id: str = Field(..., description="Usergroup ID")
    team_id: str = Field(..., description="Team ID")
    is_usergroup: bool = Field(True, description="Whether this is a usergroup")
    name: str = Field(..., description="Usergroup name")
    handle: str = Field(..., description="Usergroup handle")
    description: str = Field(..., description="Usergroup description")
    date_create: int = Field(..., description="Creation date (Unix timestamp)")
    date_update: int = Field(..., description="Last update date (Unix timestamp)")
    date_delete: int = Field(0, description="Deletion date (Unix timestamp)")
    auto_type: Optional[str] = Field(None, description="Auto type")
    created_by: str = Field(..., description="Creator user ID")
    updated_by: str = Field(..., description="Last updater user ID")
    deleted_by: Optional[str] = Field(None, description="Deleter user ID")
    prefs: DBUsergroupPrefs = Field(..., description="Usergroup preferences")
    users: List[str] = Field(default_factory=list, description="User IDs in group")
    user_count: int = Field(0, description="Number of users in group")
    disabled: bool = Field(False, description="Whether usergroup is disabled")

class SlackDB(BaseModel):
    """Complete Slack database model for validation."""
    current_user: DBCurrentUser = Field(..., description="Current user information")
    users: Dict[str, DBUser] = Field(default_factory=dict, description="All users")
    channels: Dict[str, DBChannel] = Field(default_factory=dict, description="All channels")
    files: Dict[str, DBFile] = Field(default_factory=dict, description="All files")
    reminders: Dict[str, DBReminder] = Field(default_factory=dict, description="All reminders")
    usergroups: Dict[str, DBUsergroup] = Field(default_factory=dict, description="All usergroups")
    scheduled_messages: List[Dict[str, Any]] = Field(default_factory=list, description="Scheduled messages")
    ephemeral_messages: List[Dict[str, Any]] = Field(default_factory=list, description="Ephemeral messages")

    class Config:
        extra = "forbid"
