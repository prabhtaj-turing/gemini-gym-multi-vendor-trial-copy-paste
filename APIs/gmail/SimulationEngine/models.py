from typing import Optional, Dict, Any, Literal, List, Union
from pydantic import BaseModel, Field, ValidationError, EmailStr, validator, field_validator, TypeAdapter
from datetime import datetime
import re


def parse_email_list(email_string: Optional[str]) -> List[str]:
    """
    Parse comma-separated email string into list of valid emails.
    
    Args:
        email_string: Comma-separated email addresses string
        
    Returns:
        List of valid email addresses
        
    Examples:
        >>> parse_email_list("user1@example.com, user2@example.com")
        ['user1@example.com', 'user2@example.com']
        >>> parse_email_list("user1@example.com,invalid-email,user2@example.com")
        ['user1@example.com', 'user2@example.com']
        >>> parse_email_list("")
        []
        >>> parse_email_list(None)
        []
    """
    if not email_string or not email_string.strip():
        return []
    
    # Split by comma and clean up whitespace
    emails = [email.strip() for email in email_string.split(',')]
    
    # Filter out empty strings and validate emails
    valid_emails = []
    for email in emails:
        if email:  # Not empty after stripping
            try:
                # Validate email format using Pydantic's EmailStr
                validated = TypeAdapter(EmailStr).validate_python(email)
                valid_emails.append(str(validated))
            except ValidationError:
                # Skip invalid emails - they will be filtered out
                # This allows graceful handling of mixed valid/invalid email lists
                continue
    
    return valid_emails


def normalize_email_field_for_storage(value: Optional[str]) -> str:
    """
    Normalize email field for storage in database.
    
    Args:
        value: Email field value (could be None, non-string, or string)
        
    Returns:
        Normalized string value for storage
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        return ""
    return value.strip()



class MessageUpdateModel(BaseModel):
    """
    Pydantic model for the 'message' part of the draft update.
    All fields are optional as this model represents an update payload.
    Supports CC/BCC fields and multiple recipients.
    """
    id: Optional[str] = None
    threadId: Optional[str] = None
    raw: Optional[str] = None
    labelIds: Optional[List[str]] = None
    snippet: Optional[str] = None
    historyId: Optional[str] = None
    internalDate: Optional[str] = None  # Expected as a string Unix timestamp in milliseconds if provided
    payload: Optional[Dict[str, Any]] = None
    sizeEstimate: Optional[int] = None
    # Compatibility fields
    sender: Optional[Union[EmailStr, Literal['me']]] = None
    recipient: Optional[str] = None  # Comma-separated TO recipients
    cc: Optional[str] = None  # Comma-separated CC recipients
    bcc: Optional[str] = None  # Comma-separated BCC recipients
    subject: Optional[str] = None
    body: Optional[str] = None
    isRead: Optional[bool] = None
    
    @property
    def computed_isRead(self) -> bool:
        """Compute isRead based on labelIds. Returns True if 'UNREAD' is not in labelIds."""
        if self.labelIds is None:
            return True  # Default to read if no labels
        return "UNREAD" not in [label.upper() for label in self.labelIds]

    @field_validator('internalDate')
    @classmethod
    def validate_internal_date_milliseconds(cls, v: Optional[str]) -> Optional[str]:
        """Validate that internalDate is in milliseconds (not seconds) if provided."""
        if v is not None:
            try:
                timestamp = float(v)
                # Check if the timestamp is likely in seconds instead of milliseconds
                # Unix timestamps in seconds are typically 10 digits (e.g., 1705123456)
                # Unix timestamps in milliseconds are typically 13 digits (e.g., 1705123456789)
                # We'll use a threshold to determine if it's likely seconds
                if timestamp < 1000000000000:  # Less than year 2001 in milliseconds
                    raise ValueError(f"internalDate '{v}' appears to be in seconds, but must be in milliseconds. "
                                   f"Expected a 13-digit timestamp (e.g., 1705123456789), got {len(str(int(timestamp)))} digits.")
            except ValueError as e:
                if "appears to be in seconds" in str(e):
                    raise e
                raise ValueError(f"internalDate '{v}' must be a valid numeric timestamp in milliseconds")
        return v

COLOR_REGEX = r"^#[0-9a-fA-F]{6}$"
class ColorInputModel(BaseModel):
    """
    Pydantic model for the 'color' dictionary.
    The official Gmail API documentation explicitly states that both textColor and backgroundColor
    are "required in order to set the color of a label."
    """
    textColor: str = Field(..., pattern=COLOR_REGEX, description="The text color of the label, represented as a hex string.")
    backgroundColor: str = Field(..., pattern=COLOR_REGEX, description="The background color represented as a hex string #RRGGBB.")

class LabelInputModel(BaseModel):
    """
    Pydantic model for the 'label' input dictionary.
    Only allows 'user' type since:
    - Custom labels can only be created as 'user' type
    - System labels are read-only and cannot be updated
    """
    name: Optional[str] = None
    messageListVisibility: Literal['show', 'hide'] = 'show'
    labelListVisibility: Literal['labelShow', 'labelShowIfUnread', 'labelHide'] = 'labelShow'
    type: Literal['user'] = 'user'
    color: Optional[ColorInputModel] = None
    

class ProfileInputModel(BaseModel):
    """
    Pydantic model for validating the 'profile' argument of createUser.
    Ensures 'emailAddress' is present and is a valid email string.
    Other fields in the input 'profile' dictionary will be ignored (Pydantic's default behavior).
    """
    emailAddress: EmailStr

class AttachmentModel(BaseModel):
    """
    Pydantic model for validating attachment objects in messages and drafts.
    Represents the enhanced attachment schema with embedded file content.
    """
    attachmentId: str = Field(..., description="Unique identifier for the attachment")
    filename: str = Field(..., description="Name of the attached file")
    fileSize: int = Field(..., ge=0, description="Size of the file in bytes")
    mimeType: str = Field(..., description="MIME type of the file")
    data: str = Field(..., description="Base64-encoded file content")
    checksum: str = Field(..., pattern=r"^sha256:[a-fA-F0-9]{64}$", description="SHA256 checksum of the file")
    uploadDate: str = Field(..., description="ISO 8601 formatted upload timestamp")
    encoding: Literal["base64"] = Field(default="base64", description="Encoding format for the data field")
    
    @validator('mimeType')
    def validate_mime_type(cls, v):
        """Validate MIME type format"""
        mime_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_.]*$'
        if not re.match(mime_pattern, v):
            raise ValueError(f'Invalid MIME type format: {v}')
        return v
    
    @validator('uploadDate')
    def validate_upload_date(cls, v):
        """Validate ISO 8601 date format using centralized validation"""
        from common_utils.datetime_utils import validate_gmail_datetime, InvalidDateTimeFormatError
        try:
            return validate_gmail_datetime(v)
        except InvalidDateTimeFormatError as e:
            from gmail.SimulationEngine.custom_errors import InvalidDateTimeFormatError as GmailInvalidDateTimeFormatError
            raise GmailInvalidDateTimeFormatError(f"Invalid upload date format: {e}")
        except Exception as e:
            raise ValueError(f'Invalid ISO 8601 date format: {v}')
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename doesn't contain invalid characters"""
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in v for char in invalid_chars):
            raise ValueError(f'Filename contains invalid characters: {v}')
        if not v.strip():
            raise ValueError('Filename cannot be empty or whitespace only')
        return v.strip()

    class Config:
        extra = 'forbid'  # Don't allow extra fields


class LegacyAttachmentModel(BaseModel):
    """
    Pydantic model for legacy attachment objects (filename only).
    Used for backward compatibility with existing simple attachment structure.
    """
    filename: str = Field(..., description="Name of the attached file")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename is not empty"""
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        return v.strip()

    class Config:
        extra = 'allow'  # Allow extra fields for flexibility


class MessageContentModel(BaseModel):
    """
    Pydantic model for the 'message' object within the draft input.
    Fields are derived from the docstring's description of 'draft.message'
    and supplemented by fields observed in the original function's logic
    accessing 'message_input'.
    Supports CC/BCC fields and multiple recipients.
    """
    threadId: Optional[str] = None
    raw: Optional[str] = None
    internalDate: Optional[str] = None  # Expected as a string Unix timestamp in milliseconds if provided
    labelIds: Optional[List[str]] = Field(default_factory=list) # Docstring: "List[str]", original code: .get('labelIds', [])
    snippet: Optional[str] = None  # Docstring: "str, optional"
    historyId: Optional[str] = None # Docstring: "str, optional"
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict) # Docstring: "Dict[str, Any], optional", original code: .get('payload', {})
    sizeEstimate: Optional[int] = None # Docstring: "int, optional", original code: .get('sizeEstimate', 0)
    sender: Optional[Union[EmailStr, Literal['me']]] = None
    recipient: Optional[str] = None  # Changed from EmailStr to str to support comma-separated
    cc: Optional[str] = None  # Comma-separated CC recipients
    bcc: Optional[str] = None  # Comma-separated BCC recipients
    subject: Optional[str] = None
    body: Optional[str] = None
    isRead: Optional[bool] = None # Original code: .get('isRead', False)
    date: Optional[str] = None   # Original code: .get('date', '')
    
    @property
    def computed_isRead(self) -> bool:
        """Compute isRead based on labelIds. Returns True if 'UNREAD' is not in labelIds."""
        if self.labelIds is None:
            return True  # Default to read if no labels
        return "UNREAD" not in [label.upper() for label in self.labelIds]

    @field_validator('internalDate')
    @classmethod
    def validate_internal_date_milliseconds(cls, v: Optional[str]) -> Optional[str]:
        """Validate that internalDate is in milliseconds (not seconds) if provided."""
        if v is not None:
            try:
                timestamp = float(v)
                # Check if the timestamp is likely in seconds instead of milliseconds
                # Unix timestamps in seconds are typically 10 digits (e.g., 1705123456)
                # Unix timestamps in milliseconds are typically 13 digits (e.g., 1705123456789)
                # We'll use a threshold to determine if it's likely seconds
                if timestamp < 1000000000000:  # Less than year 2001 in milliseconds
                    raise ValueError(f"internalDate '{v}' appears to be in seconds, but must be in milliseconds. "
                                   f"Expected a 13-digit timestamp (e.g., 1705123456789), got {len(str(int(timestamp)))} digits.")
            except ValueError as e:
                if "appears to be in seconds" in str(e):
                    raise e
                raise ValueError(f"internalDate '{v}' must be a valid numeric timestamp in milliseconds")
        return v


class MessageContentForDraftModel(MessageContentModel):
    """
    Draft-specific message model that relaxes recipient validation.
    - recipient, cc, bcc are optional strings instead of EmailStr
    - invalid recipient values are coerced to empty string instead of raising
    - supports comma-separated recipients in all fields
    """
    recipient: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    sender: Optional[str] = None

    @field_validator('recipient', 'cc', 'bcc', 'sender', mode='before')
    @classmethod
    def normalize_email_field(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalize email fields for drafts with relaxed validation.
        For single emails, validate and convert invalid ones to empty string.
        For comma-separated emails, keep as-is for parsing later.
        """
        if v is None:
            return None
        if not isinstance(v, str):
            return ''
        s = v.strip()
        if not s:
            return ''
        
        # For drafts, validate single emails and convert invalid ones to empty string
        # This maintains backward compatibility with existing tests
        if ',' not in s:
            # Single email - validate it
            try:
                validated_email = TypeAdapter(EmailStr).validate_python(s)
                return str(validated_email)
            except ValidationError:
                return ''  # Convert invalid single emails to empty string
        else:
            # Comma-separated emails - keep as-is for parsing in properties
            return s

class MessageBodyModel(BaseModel):
    """
    Pydantic model for the 'body' object within message parts.
    Following the Golden Rule: only mark fields as required if explicitly stated in official docs.
    """
    data: Optional[str] = None  # Base64 encoded content for text parts
    attachmentId: Optional[str] = None  # Attachment ID reference for file parts
    size: Optional[int] = None  # Size in bytes for attachment parts (max 25MB each)


class MessagePartModel(BaseModel):
    """
    Pydantic model for individual message parts within the payload.
    Following the Golden Rule: only mark fields as required if explicitly stated in official docs.
    """
    mimeType: Optional[str] = None  # The MIME type of the part
    filename: Optional[str] = None  # The filename for attachment parts
    body: Optional[MessageBodyModel] = None  # The body content


class MessagePayloadStructureModel(BaseModel):
    """
    Pydantic model for the 'payload' object within messages.
    Following the Golden Rule: only mark fields as required if explicitly stated in official docs.
    """
    mimeType: Optional[str] = None  # The MIME type of the message
    parts: Optional[List[MessagePartModel]] = None  # List of message parts for attachments


class MessagePayloadModel(BaseModel):
    """
    Pydantic model for validating the 'msg' dictionary structure.
    All fields are optional, reflecting that they may or may not be present
    in the input `msg` dictionary.
    Supports CC/BCC fields and multiple recipients.
    """
    threadId: Optional[str] = None
    raw: Optional[str] = None
    sender: Optional[Union[EmailStr, Literal['me']]] = None
    recipient: Optional[str] = None  # Changed from EmailStr to str to support comma-separated
    cc: Optional[str] = None  # Comma-separated CC recipients
    bcc: Optional[str] = None  # Comma-separated BCC recipients
    subject: Optional[str] = None
    body: Optional[str] = None
    date: Optional[str] = None  # Expected as ISO 8601 string if provided
    internalDate: Optional[str] = None  # Expected as a string Unix timestamp in milliseconds if provided
    isRead: Optional[bool] = None  # Boolean indicating if message has been read
    labelIds: Optional[List[str]] = None
    
    @property
    def recipients(self) -> List[str]:
        """Get parsed TO recipient list."""
        return parse_email_list(self.recipient)
    
    @property
    def cc_recipients(self) -> List[str]:
        """Get parsed CC recipient list."""
        return parse_email_list(self.cc)
    
    @property
    def bcc_recipients(self) -> List[str]:
        """Get parsed BCC recipient list."""
        return parse_email_list(self.bcc)
    
    @property
    def computed_isRead(self) -> bool:
        """Compute isRead based on labelIds. Returns True if 'UNREAD' is not in labelIds."""
        if self.labelIds is None:
            return True  # Default to read if no labels
        return "UNREAD" not in [label.upper() for label in self.labelIds]

    @field_validator('internalDate')
    @classmethod
    def validate_internal_date_milliseconds(cls, v: Optional[str]) -> Optional[str]:
        """Validate that internalDate is in milliseconds (not seconds) if provided."""
        if v is not None:
            try:
                timestamp = float(v)
                # Check if the timestamp is likely in seconds instead of milliseconds
                # Unix timestamps in seconds are typically 10 digits (e.g., 1705123456)
                # Unix timestamps in milliseconds are typically 13 digits (e.g., 1705123456789)
                # We'll use a threshold to determine if it's likely seconds
                if timestamp < 1000000000000:  # Less than year 2001 in milliseconds
                    raise ValueError(f"internalDate '{v}' appears to be in seconds, but must be in milliseconds. "
                                   f"Expected a 13-digit timestamp (e.g., 1705123456789), got {len(str(int(timestamp)))} digits.")
            except ValueError as e:
                if "appears to be in seconds" in str(e):
                    raise e
                raise ValueError(f"internalDate '{v}' must be a valid numeric timestamp in milliseconds")
        return v

    class Config:
        extra = 'forbid' # Forbid any extra fields not defined in the model

        
class GetFunctionArgsModel(BaseModel):
    """Pydantic model for validating arguments passed to the 'get' function."""
    userId: str
    id: str
    # Using 'format_param' as field name because 'format' can conflict with method names.
    # The alias 'format' allows the function to be called with 'format' as the keyword argument.
    format_param: str = Field(alias="format")
    metadata_headers: Optional[List[str]] = None

    @validator('format_param')
    def format_param_must_be_valid(cls, value: str) -> str:
        """Validates the 'format' parameter against allowed values."""
        allowed_formats = ['minimal', 'full', 'raw', 'metadata']
        if value not in allowed_formats:
            raise ValueError(f"format must be one of: {', '.join(allowed_formats)}")
        return value

    @validator('metadata_headers',  always=True)
    def check_metadata_headers_elements(cls, v: Optional[List[Any]]) -> Optional[List[str]]:
        """Validates that all elements in metadata_headers are strings, if the list is provided."""
        if v is None:
            return None
        if not isinstance(v, list):
            # This case should ideally be caught by Pydantic's list type check first,
            # but an explicit check can provide a more specific error if needed.
            raise TypeError("metadata_headers must be a list of strings or None.")
        for item in v:
            if not isinstance(item, str):
                raise ValueError("All elements in metadata_headers must be strings.")
        return v

    class Config:
        # Allow Pydantic to work with parameter names like 'format' by using aliases.
        allow_population_by_field_name = True
        # Forbid extra fields not defined in the model
        extra = 'forbid'


class DraftInputPydanticModel(BaseModel):
    """
    Pydantic model for the main 'draft' input dictionary.
    Following the Golden Rule: only mark fields as required if explicitly stated in official docs.
    The official Gmail API documentation doesn't explicitly mark 'message' as required.
    """
    # Field explicitly described in docstring for draft input
    id: Optional[str] = None  # Docstring: "'id' (str, optional)"

    # Field 'message' is optional since the official documentation doesn't explicitly mark it as required
    # Use relaxed draft-specific message model for permissive recipient handling
    message: Optional[MessageContentForDraftModel] = None


class DraftUpdateInputModel(BaseModel):
    """
    Pydantic model for the 'draft' input dictionary.
    """
    message: Optional[MessageUpdateModel] = None
    class Config:
        extra = "allow"
        

class MessageSendPayloadModel(BaseModel):
    """
    Pydantic model for validating the 'msg' dictionary in the send function.
    The 'raw' field is optional since the official documentation doesn't explicitly mark it as required.
    Other fields are optional.
    Supports CC/BCC fields and multiple recipients.
    """
    threadId: Optional[str] = None
    raw: Optional[str] = None  # Optional since not explicitly marked as required in official docs
    sender: Optional[Union[EmailStr, Literal['me']]] = None
    recipient: Optional[str] = None  # Changed from EmailStr to str to support comma-separated
    cc: Optional[str] = None  # Comma-separated CC recipients
    bcc: Optional[str] = None  # Comma-separated BCC recipients
    subject: Optional[str] = None
    body: Optional[str] = None
    date: Optional[str] = None
    internalDate: Optional[str] = None  # Expected as a string Unix timestamp in milliseconds if provided
    isRead: Optional[bool] = None
    labelIds: Optional[List[str]] = None
    
    @property
    def recipients(self) -> List[str]:
        """Get parsed TO recipient list."""
        return parse_email_list(self.recipient)
    
    @property
    def cc_recipients(self) -> List[str]:
        """Get parsed CC recipient list."""
        return parse_email_list(self.cc)
    
    @property
    def bcc_recipients(self) -> List[str]:
        """Get parsed BCC recipient list."""
        return parse_email_list(self.bcc)
    
    @property
    def computed_isRead(self) -> bool:
        """Compute isRead based on labelIds. Returns True if 'UNREAD' is not in labelIds."""
        if self.labelIds is None:
            return True  # Default to read if no labels
        return "UNREAD" not in [label.upper() for label in self.labelIds]

    @field_validator('internalDate')
    @classmethod
    def validate_internal_date_milliseconds(cls, v: Optional[str]) -> Optional[str]:
        """Validate that internalDate is in milliseconds (not seconds) if provided."""
        if v is not None:
            try:
                timestamp = float(v)
                # Check if the timestamp is likely in seconds instead of milliseconds
                # Unix timestamps in seconds are typically 10 digits (e.g., 1705123456)
                # Unix timestamps in milliseconds are typically 13 digits (e.g., 1705123456789)
                # We'll use a threshold to determine if it's likely seconds
                if timestamp < 1000000000000:  # Less than year 2001 in milliseconds
                    raise ValueError(f"internalDate '{v}' appears to be in seconds, but must be in milliseconds. "
                                   f"Expected a 13-digit timestamp (e.g., 1705123456789), got {len(str(timestamp))} digits.")
            except ValueError as e:
                if "appears to be in seconds" in str(e):
                    raise e
                raise ValueError(f"internalDate '{v}' must be a valid numeric timestamp in milliseconds")
        return v

    class Config:
        extra = 'allow' # Allow extra fields as the original function uses .get() for known fields        

class GmailMessageForSearch(BaseModel):
    id: Optional[str] = None
    userId: Optional[str] = None
    threadId: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    labelIds: Optional[List[str]] = None

class GmailMessageForDraftSearch(BaseModel):
    id: Optional[str] = None
    threadId: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    labelIds: Optional[List[str]] = None

class GmailDraftForSearch(BaseModel):
    id: Optional[str] = None
    userId: Optional[str] = None
    message: GmailMessageForDraftSearch

class SendAsCreatePayloadModel(BaseModel):
    """
    Pydantic model for validating the 'send_as' dictionary in SendAs create function.
    All fields are optional, aligning with the original function's .get() usage.
    """
    sendAsEmail: Optional[EmailStr] = None
    displayName: Optional[str] = None
    replyToAddress: Optional[EmailStr] = None
    signature: Optional[str] = None
    
    @validator('displayName', 'signature')
    def validate_string_fields(cls, v):
        if v is not None and not isinstance(v, str):
            raise ValueError('Field must be a string')
        return v

    class Config:
        extra = 'allow' # Allow extra fields for future extensibility


class ImapSettingsInputModel(BaseModel):
    """
    Pydantic model for validating the 'imap_settings' dictionary in updateImap function.
    All fields are optional as this is for updating existing settings.
    """
    enabled: Optional[bool] = None
    autoExpunge: Optional[bool] = None
    expungeBehavior: Optional[str] = None
    
    @validator('expungeBehavior')
    def validate_expunge_behavior(cls, v):
        if v is not None:
            allowed_behaviors = ['expungeBehaviorUnspecified', 'archive', 'trash', 'deleteForever']
            if v not in allowed_behaviors:
                raise ValueError(f'expungeBehavior must be one of: {", ".join(allowed_behaviors)}')
        return v

    class Config:
        extra = 'forbid'  # No extra parameters allowed in the dict

class AutoForwardingSettingsModel(BaseModel):
    """
    Pydantic model for validating auto-forwarding settings dictionary.
    All fields are optional for update operations.
    """
    enabled: Optional[bool] = None
    emailAddress: Optional[EmailStr] = None
    disposition: Optional[Literal['dispositionUnspecified', 'leaveInInbox', 'archive', 'trash', 'markRead']] = None

    @field_validator('enabled', mode='before')
    @classmethod
    def validate_enabled(cls, v):
        if v is not None and not isinstance(v, bool):
            raise ValueError('enabled must be a boolean value')
        return v

    @validator('emailAddress')
    def validate_email_address(cls, v):
        if v is not None and not v.strip():
            raise ValueError('emailAddress cannot be empty or contain only whitespace')
        return v

    class Config:
        extra = 'forbid'  # Only allow defined fields



# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

LabelType = Literal[
    'user',
    'system'
]

LabelListVisibilityType = Literal[
    'labelShow',
    'labelShowIfUnread',
    'labelHide'
]

MessageListVisibilityType = Literal[
    'show',
    'hide'
]

ExpungeBehaviorType = Literal[
    'expungeBehaviorUnspecified',
    'archive',
    'trash',
    'deleteForever'
]

AutoForwardingDispositionType = Literal[
    'dispositionUnspecified',
    'leaveInInbox',
    'archive',
    'trash',
    'markRead'
]

MessageFormatType = Literal[
    'minimal',
    'full',
    'raw',
    'metadata'
]

VerificationStatusType = Literal[
    'accepted',
    'pending',
    'rejected'
]


# =============================================================================
# CONSTANTS AND PATTERNS
# =============================================================================

# Common field definitions for reuse
LABEL_TYPE_FIELD = Field(
    ...,
    json_schema_extra={"enum": ['user', 'system']}
)

LABEL_LIST_VISIBILITY_FIELD = Field(
    ...,
    json_schema_extra={"enum": ['labelShow', 'labelShowIfUnread', 'labelHide']}
)

MESSAGE_LIST_VISIBILITY_FIELD = Field(
    ...,
    json_schema_extra={"enum": ['show', 'hide']}
)

MESSAGE_FORMAT_FIELD = Field(
    ...,
    json_schema_extra={"enum": ['minimal', 'full', 'raw', 'metadata']}
)

VERIFICATION_STATUS_FIELD = Field(
    ...,
    json_schema_extra={"enum": ['accepted', 'pending', 'rejected']}
)

# Helper Regex Patterns
HEX_COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"  # For label colors
MIME_TYPE_PATTERN = r'^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_.]*$'  # For MIME types
SHA256_CHECKSUM_PATTERN = r"^sha256:[a-fA-F0-9]{64}$"  # For file checksums
ISO_8601_DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})$'  # For ISO 8601 dates



# =============================================================================
# SETTINGS MODELS
# =============================================================================

class UserProfile(BaseModel):
    """Model for user profile information."""
    emailAddress: EmailStr = Field(..., description="User's email address")
    messagesTotal: int = Field(..., ge=0, description="Total number of messages")
    threadsTotal: int = Field(..., ge=0, description="Total number of threads")
    historyId: str = Field(..., description="Current history ID")


class ImapSettings(BaseModel):
    """Model for IMAP settings."""
    enabled: bool = Field(..., description="Whether IMAP is enabled")
    server: Optional[str] = Field(None, description="IMAP server address")
    port: Optional[int] = Field(None, ge=1, le=65535, description="IMAP server port")


class PopSettings(BaseModel):
    """Model for POP settings."""
    enabled: bool = Field(default=False, description="Whether POP is enabled")
    server: Optional[str] = Field(None, description="POP server address")
    port: Optional[int] = Field(None, ge=1, le=65535, description="POP server port")


class VacationSettings(BaseModel):
    """Model for vacation/auto-reply settings."""
    enableAutoReply: bool = Field(default=False, description="Whether auto-reply is enabled")
    responseBodyPlainText: Optional[str] = Field(None, description="Auto-reply message text")


class LanguageSettings(BaseModel):
    """Model for language settings."""
    displayLanguage: str = Field(default="en-US", description="Display language code")


class SmimeInfo(BaseModel):
    """Model for S/MIME certificate information."""
    id: str = Field(..., description="S/MIME certificate ID")
    encryptedKey: str = Field(..., description="Encrypted private key")
    default: bool = Field(default=False, description="Whether this is the default certificate")


class SendAsSettings(BaseModel):
    """Model for send-as settings."""
    sendAsEmail: EmailStr = Field(..., description="Email address to send as")
    displayName: Optional[str] = Field(None, description="Display name for the send-as address")
    replyToAddress: Optional[EmailStr] = Field(None, description="Reply-to address")
    signature: Optional[str] = Field(None, description="Email signature")
    verificationStatus: VerificationStatusType = Field(..., description="Verification status (accepted, pending, etc.)")
    smimeInfo: Optional[Dict[str, SmimeInfo]] = Field(default_factory=dict, description="S/MIME certificates")


class UserSettings(BaseModel):
    """Model for user settings."""
    imap: ImapSettings = Field(..., description="IMAP settings")
    pop: PopSettings = Field(default_factory=lambda: PopSettings(), description="POP settings")
    vacation: VacationSettings = Field(default_factory=lambda: VacationSettings(), description="Vacation settings")
    language: LanguageSettings = Field(default_factory=lambda: LanguageSettings(), description="Language settings")
    autoForwarding: AutoForwardingSettingsModel = Field(default_factory=lambda: AutoForwardingSettingsModel(), description="Auto-forwarding settings")
    sendAs: Dict[str, SendAsSettings] = Field(default_factory=dict, description="Send-as settings")


class HistoryItem(BaseModel):
    """Model for history items."""
    id: str = Field(..., description="History item ID")
    messages: Optional[List[str]] = Field(None, description="List of message IDs in this history item")
    labelsAdded: Optional[List[str]] = Field(None, description="List of label IDs added in this history item")
    labelsRemoved: Optional[List[str]] = Field(None, description="List of label IDs removed in this history item")


class WatchSettings(BaseModel):
    """Model for watch settings."""
    labelFilterAction: Optional[str] = Field(None, description="Label filter action (include/exclude)")
    labelIds: Optional[List[str]] = Field(None, description="List of label IDs to watch")


# =============================================================================
# DATABASE STRUCTURE MODELS
# =============================================================================

class MessagePart(BaseModel):
    """Model for message parts in payload."""
    mimeType: str = Field(..., pattern=MIME_TYPE_PATTERN, description="MIME type of the part")
    filename: Optional[str] = Field(None, description="Filename if this is an attachment")
    body: Dict[str, Any] = Field(..., description="Body data for the part")


class MessageHeader(BaseModel):
    """Model for message headers."""
    name: str = Field(..., description="Header name (e.g., 'From', 'To', 'Subject')")
    value: str = Field(..., description="Header value")


class MessagePayload(BaseModel):
    """Model for message payload structure."""
    mimeType: str = Field(..., pattern=MIME_TYPE_PATTERN, description="MIME type of the message")
    parts: Optional[List[MessagePart]] = Field(None, description="Message parts for multipart messages")
    headers: Optional[List[MessageHeader]] = Field(None, description="Message headers")


class GmailMessage(BaseModel):
    """Model for Gmail message structure as stored in database."""
    id: str = Field(..., description="Message ID")
    threadId: str = Field(..., description="Thread ID")
    raw: str = Field(..., description="Base64 encoded raw message")
    sender: str = Field(..., description="Sender email address")
    recipient: str = Field(..., description="Comma-separated TO recipient email addresses")
    cc: str = Field(default="", description="Comma-separated CC recipient email addresses")
    bcc: str = Field(default="", description="Comma-separated BCC recipient email addresses")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message body text")
    date: str = Field(..., description="Message date in ISO 8601 format")
    internalDate: str = Field(..., description="Internal date as Unix timestamp string")
    isRead: bool = Field(..., description="Whether the message has been read")
    labelIds: List[str] = Field(default_factory=list, description="List of label IDs")
    payload: Optional[MessagePayload] = Field(None, description="Message payload for complex messages")
    
    @property
    def recipients(self) -> List[str]:
        """Get parsed TO recipient list."""
        return parse_email_list(self.recipient)
    
    @property
    def cc_recipients(self) -> List[str]:
        """Get parsed CC recipient list."""
        return parse_email_list(self.cc)
    
    @property
    def bcc_recipients(self) -> List[str]:
        """Get parsed BCC recipient list."""
        return parse_email_list(self.bcc)

    @property
    def computed_isRead(self) -> bool:
        """Compute isRead based on labelIds. Returns True if 'UNREAD' is not in labelIds."""
        if self.labelIds is None:
            return True  # Default to read if no labels
        return "UNREAD" not in [label.upper() for label in self.labelIds]

    @field_validator('internalDate')
    @classmethod
    def validate_internal_date_milliseconds(cls, v: Optional[str]) -> Optional[str]:
        """Validate that internalDate is in milliseconds (not seconds) if provided."""
        if v is not None:
            try:
                timestamp = float(v)
                # Check if the timestamp is likely in seconds instead of milliseconds
                # Unix timestamps in seconds are typically 10 digits (e.g., 1705123456)
                # Unix timestamps in milliseconds are typically 13 digits (e.g., 1705123456789)
                # We'll use a threshold to determine if it's likely seconds
                if timestamp < 1000000000000:  # Less than year 2001 in milliseconds
                    raise ValueError(f"internalDate '{v}' appears to be in seconds, but must be in milliseconds. "
                                   f"Expected a 13-digit timestamp (e.g., 1705123456789), got {len(str(int(timestamp)))} digits.")
            except ValueError as e:
                if "appears to be in seconds" in str(e):
                    raise e
                raise ValueError(f"internalDate '{v}' must be a valid numeric timestamp in milliseconds")
        return v

class GmailDraft(BaseModel):
    """Model for Gmail draft structure as stored in database."""
    id: str = Field(..., description="Draft ID")
    message: GmailMessage = Field(..., description="Draft message content")


class GmailThread(BaseModel):
    """Model for Gmail thread structure as stored in database."""
    id: str = Field(..., description="Thread ID")
    messageIds: List[str] = Field(default_factory=list, description="List of message IDs in this thread")


class GmailLabel(BaseModel):
    """Model for Gmail label structure as stored in database."""
    id: str = Field(..., description="Label ID")
    name: str = Field(..., description="Label name")
    type: LabelType = Field(..., description="Label type (user or system)")
    labelListVisibility: LabelListVisibilityType = Field(..., description="Label list visibility setting")
    messageListVisibility: MessageListVisibilityType = Field(..., description="Message list visibility setting")
    color: Optional[ColorInputModel] = Field(None, description="Label color (optional)")


class GmailAttachment(BaseModel):
    """Model for Gmail attachment structure as stored in database."""
    attachmentId: str = Field(..., description="Unique attachment ID")
    filename: str = Field(..., description="Attachment filename")
    size: int = Field(..., ge=0, description="Attachment size in bytes")
    mimeType: str = Field(..., pattern=MIME_TYPE_PATTERN, description="MIME type of the attachment")
    data: str = Field(..., description="Base64 encoded attachment data")


class GmailHistoryItem(BaseModel):
    """Model for Gmail history item structure as stored in database."""
    id: str = Field(..., description="History item ID")
    messages: Optional[List[str]] = Field(None, description="List of message IDs in this history item")
    labelsAdded: Optional[List[str]] = Field(None, description="List of label IDs added in this history item")
    labelsRemoved: Optional[List[str]] = Field(None, description="List of label IDs removed in this history item")


class GmailWatch(BaseModel):
    """Model for Gmail watch settings structure as stored in database."""
    labelFilterAction: Optional[str] = Field(None, description="Label filter action (include/exclude)")
    labelIds: Optional[List[str]] = Field(None, description="List of label IDs to watch")


class UserData(BaseModel):
    """Model for complete user data structure."""
    profile: UserProfile = Field(..., description="User profile information")
    drafts: Dict[str, GmailDraft] = Field(default_factory=dict, description="User's drafts")
    messages: Dict[str, GmailMessage] = Field(default_factory=dict, description="User's messages")
    threads: Dict[str, GmailThread] = Field(default_factory=dict, description="User's threads")
    labels: Dict[str, GmailLabel] = Field(default_factory=dict, description="User's labels")
    settings: UserSettings = Field(..., description="User's settings")
    history: List[GmailHistoryItem] = Field(default_factory=list, description="User's history")
    watch: GmailWatch = Field(default_factory=lambda: GmailWatch(), description="User's watch settings")


# =============================================================================
# MAIN DATABASE MODEL
# =============================================================================

class GmailDB(BaseModel):
    """
    Main database model for Gmail API simulation.
    Represents the overall structure of the Gmail JSON database.
    """
    users: Dict[str, UserData] = Field(
        default_factory=dict,
        description="Dictionary of users, where each user has profile, drafts, messages, threads, labels, settings, history, and watch data"
    )
    attachments: Dict[str, GmailAttachment] = Field(
        default_factory=dict,
        description="Dictionary of attachments with attachmentId as key and attachment details as value"
    )
    counters: Dict[str, int] = Field(
        default_factory=dict,
        description="Counters for various entities like messages, threads, drafts, labels, history, smime, and attachments"
    )
