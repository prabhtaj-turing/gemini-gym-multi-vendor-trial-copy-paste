from typing import Optional, Dict, Any, Literal, List, Union
from pydantic import BaseModel, Field, ValidationError, EmailStr, validator, field_validator, TypeAdapter, model_validator
from datetime import datetime as dt
import re

COLOR_REGEX = r"^#[0-9a-fA-F]{6}$"

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


class ColorInputModel(BaseModel):
    """
    Pydantic model for the 'color' dictionary.
    The official Gmail API documentation explicitly states that both textColor and backgroundColor
    are "required in order to set the color of a label."
    """
    textColor: str = Field(..., pattern=COLOR_REGEX, description="The text color of the label, represented as a hex string.")
    backgroundColor: str = Field(..., pattern=COLOR_REGEX, description="The background color represented as a hex string #RRGGBB.")


class AutoForwardingSettingsModel(BaseModel):
    """
    Pydantic model for validating auto-forwarding settings dictionary.
    All fields are optional for update operations.
    """
    enabled: Optional[bool] = Field(None, description="Whether auto-forwarding is enabled.")
    emailAddress: Optional[EmailStr] = Field(None, description="The email address to forward messages to.")
    disposition: Optional[Literal['dispositionUnspecified', 'leaveInInbox', 'archive', 'trash', 'markRead']] = Field(None, description="How to handle forwarded messages.")

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


class MessageBodyModel(BaseModel):
    """
    Pydantic model for the 'body' object within message parts.
    Following the Golden Rule: only mark fields as required if explicitly stated in official docs.
    """
    data: Optional[str] = Field(None, description="Base64 encoded content for text parts.")
    attachmentId: Optional[str] = Field(None, description="Attachment ID reference for file parts.")
    size: Optional[int] = Field(None, description="Size in bytes for attachment parts (max 25MB each).")


class MessagePartModel(BaseModel):
    """
    Pydantic model for individual message parts within the payload.
    Following the Golden Rule: only mark fields as required if explicitly stated in official docs.
    """
    mimeType: Optional[str] = Field(None, description="The MIME type of the part.")
    filename: Optional[str] = Field(None, description="The filename for attachment parts.")
    body: Optional[MessageBodyModel] = Field(None, description="The body content.")


class MessagePayloadStructureModel(BaseModel):
    """
    Pydantic model for the 'payload' object within messages.
    Following the Golden Rule: only mark fields as required if explicitly stated in official docs.
    """
    mimeType: Optional[str] = Field(None, description="The MIME type of the message.")
    parts: Optional[List[MessagePartModel]] = Field(None, description="List of message parts for attachments.")


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
    enabled: bool = Field(False, description="Whether POP is enabled")
    server: Optional[str] = Field(None, description="POP server address")
    port: Optional[int] = Field(None, ge=1, le=65535, description="POP server port")


class VacationSettings(BaseModel):
    """Model for vacation/auto-reply settings."""
    enableAutoReply: bool = Field(False, description="Whether auto-reply is enabled")
    responseBodyPlainText: Optional[str] = Field(None, description="Auto-reply message text")


class LanguageSettings(BaseModel):
    """Model for language settings."""
    displayLanguage: str = Field("en-US", description="Display language code")


class SmimeInfo(BaseModel):
    """Model for S/MIME certificate information."""
    id: str = Field(..., description="S/MIME certificate ID")
    encryptedKey: str = Field(..., description="Encrypted private key")
    default: bool = Field(False, description="Whether this is the default certificate")


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
    pop: PopSettings = Field(default_factory=PopSettings, description="POP settings")
    vacation: VacationSettings = Field(default_factory=VacationSettings, description="Vacation settings")
    language: LanguageSettings = Field(default_factory=LanguageSettings, description="Language settings")
    autoForwarding: AutoForwardingSettingsModel = Field(default_factory=AutoForwardingSettingsModel, description="Auto-forwarding settings")
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
    mimeType: Optional[str] = Field(None, pattern=MIME_TYPE_PATTERN, description="MIME type of the message")
    parts: Optional[List[MessagePart]] = Field(None, description="Message parts for multipart messages")
    headers: Optional[List[MessageHeader]] = Field(None, description="Message headers")
    body: Optional[MessageBodyModel] = Field(None, description="Body data for the part")


class GmailMessage(BaseModel):
    """Model for Gmail message structure as stored in database."""
    model_config = {'extra': 'ignore'}  # Ignore extra fields not in model (e.g., snippet, sizeEstimate, headers from API returns)
    
    # Required fields
    id: str = Field(..., description="Message ID")
    
    # Core message fields (optional with defaults)
    threadId: str = Field(default="", description="Thread ID")
    raw: str = Field(default="", description="Base64 encoded raw message")
    sender: str = Field(default="", description="Sender email address")
    recipient: str = Field(default="", description="Comma-separated TO recipient email addresses")
    cc: str = Field(default="", description="Comma-separated CC recipient email addresses")
    bcc: str = Field(default="", description="Comma-separated BCC recipient email addresses")
    subject: str = Field(default="", description="Message subject")
    body: str = Field(default="", description="Message body text")
    date: str = Field(default="", description="Message date in ISO 8601 format string")
    internalDate: str = Field(default="", description="Internal date as Unix timestamp string in milliseconds (13 digits)")
    isRead: Optional[bool] = Field(default=None, description="Whether the message has been read (computed from labels if not provided)")
    labelIds: List[str] = Field(default_factory=list, description="List of label IDs")
    payload: Optional[MessagePayload] = Field(None, description="Message payload for complex messages")

    @model_validator(mode='before')
    @classmethod
    def sync_isRead_with_labels_validator(cls, data: Any) -> Any:
        """Synchronize isRead field with UNREAD label during validation."""
        if isinstance(data, dict):
            if 'labelIds' not in data or data['labelIds'] is None:
                data['labelIds'] = []
            
            label_ids = {label.upper() for label in data['labelIds']}
            
            # Get isRead value
            is_read = data.get('isRead')
            
            if is_read is not None:
                # isRead is explicitly set, sync labels to match
                if is_read is True:
                    label_ids.discard('UNREAD')
                else:
                    label_ids.add('UNREAD')
            else:
                # isRead not set, compute from labels
                is_read = 'UNREAD' not in label_ids
            
            # Update data
            data['labelIds'] = sorted(list(label_ids))
            data['isRead'] = is_read
        return data

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

    @field_validator('internalDate')
    @classmethod
    def validate_internal_date_milliseconds(cls, v: Optional[str]) -> Optional[str]:
        """Validate that internalDate is in milliseconds (not seconds) if provided.
        Unix timestamps in milliseconds are typically 13 digits (e.g., 1705123456789)."""
        if v is not None and v != '':  # Allow empty strings
            try:
                timestamp = float(v)
                # Check if timestamp is in seconds (9-10 digits) - reject it
                if timestamp < 1000000000000:  # Less than year 2001 in milliseconds
                    raise ValueError(f"internalDate '{v}' appears to be in seconds, but must be in milliseconds. "
                                   f"Expected 13-digit timestamp (e.g., 1705123456789), got {len(str(int(timestamp)))} digits.")
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
    watch: GmailWatch = Field(default_factory=GmailWatch, description="User's watch settings")


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
    class Config:
        str_strip_whitespace = True
