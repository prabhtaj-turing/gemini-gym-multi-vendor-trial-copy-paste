# File: whatsapp_api/SimulationEngine/models.py

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum
from datetime import datetime, timezone
from typing import Annotated
import re

# --- Enums (Derived from API descriptions) ---

class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"

# --- send_message ---
class ContactJIDSuffix(str, Enum):
    CONTACT = "@s.whatsapp.net"
    GROUP = "@g.us"

    
class PhoneNumberRegex(str, Enum):
    PHONE_NUMBER = r"^\d+$"  # Matches strings containing only digits

    
class WhatsappJIDRegex(str, Enum):
    WHATSAPP_JID = r"^\S+@(s\.whatsapp\.net|g\.us)$" # Matches WhatsApp JIDs

    
class PhoneNumberLength(int, Enum):
    MIN_LENGTH = 7
    MAX_LENGTH = 15    

class FunctionName(str, Enum):
    """The name of the API."""
    SEARCH_CONTACTS = "search_contacts"
    GET_CONTACT_CHATS = "get_contact_chats"
    LIST_CHATS = "list_chats"
    GET_CHAT = "get_chat"
    GET_DIRECT_CHAT_BY_CONTACT = "get_direct_chat_by_contact"
    GET_LAST_INTERACTION = "get_last_interaction"
    SEND_MESSAGE = "send_message"
    LIST_MESSAGES = "list_messages"
    GET_MESSAGE_CONTEXT = "get_message_context"
    SENT_MESSAGE = "sent_message"
    SEND_FILE = "send_file"
    SEND_AUDIO_MESSAGE = "send_audio_message"
    DOWNLOAD_MEDIA = "download_media"
    
class Action(BaseModel):
    """An action record."""
    action_type: FunctionName
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# --- Core Data Models ---

# Model for the specific WhatsApp details of a contact
class WhatsappContact(BaseModel):
    jid: str  # e.g., "19876543210@s.whatsapp.net"
    name_in_address_book: Optional[str] = None
    profile_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_whatsapp_user: bool = True
    
    @field_validator("jid")
    @classmethod
    def validate_jid(cls, v):
        """Validate WhatsApp JID format."""
        if not v or not v.strip():
            raise ValueError('JID cannot be empty')
        jid_pattern = r'^\S+@(s\.whatsapp\.net|g\.us)$'
        if not re.match(jid_pattern, v.strip()):
            raise ValueError('Invalid WhatsApp JID format (expected @s.whatsapp.net or @g.us)')
        return v.strip()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        if v is not None and v.strip():
            # Validate phone number format - allow digits-only or E.164 format
            cleaned = re.sub(r'[-\s\(\)\.]', '', v.strip())
            # More flexible: allow leading 0 or +, then digits
            phone_pattern = r'^\+?\d{7,15}$'
            if not re.match(phone_pattern, cleaned):
                raise ValueError('Invalid phone number format (expected digits or E.164 format)')
            return v.strip()
        return v

# --- NEW Models for the Google People API-like Structure ---

class Name(BaseModel):
    givenName: Optional[str] = None
    familyName: Optional[str] = None

class PhoneNumber(BaseModel):
    value: str
    type: Optional[str] = None
    primary: bool = False

class EmailAddress(BaseModel):
    value: str
    type: Optional[str] = None
    primary: bool = False
    
class Organization(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    primary: bool = False

# This is the main new model for a contact in the DB
class PersonContact(BaseModel):
    resourceName: str # e.g., "people/c12345678901234567"
    etag: Optional[str] = None
    names: List[Name] = Field(default_factory=list)
    emailAddresses: List[EmailAddress] = Field(default_factory=list)
    phoneNumbers: List[PhoneNumber] = Field(default_factory=list)
    organizations: List[Organization] = Field(default_factory=list)
    isWorkspaceUser: bool = False
    # The original WhatsApp-specific info is now nested
    whatsapp: Optional[WhatsappContact] = None
      
class MediaInfo(BaseModel):
    media_type: MediaType
    file_name: Optional[str] = None
    caption: Optional[str] = None
    mime_type: Optional[str] = None
    # For simulation, we can add a local path to the media file
    simulated_local_path: Optional[str] = None
    simulated_file_size_bytes: Optional[int] = None

      
class QuotedMessageInfo(BaseModel):
    quoted_message_id: str
    quoted_sender_jid: str
    quoted_text_preview: Optional[str] = None

      
class Message(BaseModel):
    message_id: str # Unique message ID
    chat_jid: str   # JID of the chat this message belongs to
    sender_jid: str # JID of the message sender
    sender_name: Optional[str] = None # Display name of the sender
    timestamp: str  # ISO-8601 formatted timestamp
    text_content: Optional[str] = None
    is_outgoing: bool
    media_info: Optional[MediaInfo] = None
    quoted_message_info: Optional[QuotedMessageInfo] = None
    reaction: Optional[str] = None # Emoji reaction
    status: Optional[str] = None # From get_message_context e.g., 'sent', 'delivered', 'read'
    forwarded: Optional[bool] = None # From get_message_context

      
class LastMessagePreview(BaseModel):
    message_id: str
    text_snippet: Optional[str] = None # Snippet or placeholder like "Photo"
    sender_name: Optional[str] = None
    timestamp: str
    is_outgoing: bool

      
class GroupParticipant(BaseModel):
    jid: str
    name_in_address_book: Optional[str] = None
    profile_name: Optional[str] = None
    is_admin: bool = False

      
class GroupMetadata(BaseModel):
    group_description: Optional[str] = None
    creation_timestamp: Optional[str] = None # ISO-8601 timestamp
    owner_jid: Optional[str] = None
    participants_count: int
    participants: List[GroupParticipant] = Field(default_factory=list)

      
class Chat(BaseModel):
    chat_jid: str
    name: Optional[str] = None # Contact name or group subject
    is_group: bool
    last_active_timestamp: Optional[str] = None # ISO-8601 timestamp
    unread_count: Optional[int] = 0
    is_archived: bool = False
    is_pinned: bool = False
    is_muted_until: Optional[str] = None # ISO-8601 timestamp or 'indefinitely'
    group_metadata: Optional[GroupMetadata] = None
    # All messages for a chat are stored within the chat object to keep them contained
    messages: List[Message] = Field(default_factory=list)

      
class DownloadMediaArguments(BaseModel):
    """
    Pydantic model for validating the input arguments of the download_media function.
    """
    message_id: str
    chat_jid: str

class SendAudioMessageArguments(BaseModel):
    """
    Pydantic model for validating arguments to the send_audio_message function.
    Corresponds to the 'inputSchema' in the function's documentation.
    """
    recipient: Annotated[str, Field(
        strip_whitespace=True, 
        min_length=1,
        title="Recipient",
        description="The recipient - either a phone number or a JID."
    )]
    media_path: Annotated[str, Field(
        strip_whitespace=True,
        min_length=1,
        title="Media Path",
        description="The absolute path to the audio file to send."
    )]

    model_config = ConfigDict(
        title="send_audio_messageArguments"
    )

class SendAudioMessageResponse(BaseModel):
    """
    Pydantic model for the return type of the send_audio_message function.
    """
    success: bool
    status_message: str
    message_id: Optional[str] = None
    timestamp: Optional[str] = None  # ISO-8601 formatted timestamp

class DownloadMediaResult(BaseModel):
    """
    Pydantic model for the return type of the download_media function.
    Details the outcome of a media download operation.
    """
    success: bool
    status_message: str
    file_path: Optional[str] = None
    original_file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None


class GetContactChatsArgs(BaseModel):
    """
    Pydantic v2 model for validating arguments of the get_contact_chats function.
    """
    # Field 'pattern' replaces v1's 'regex'
    jid: Annotated[str, Field(pattern=WhatsappJIDRegex.WHATSAPP_JID.value)]
    # 'gt' and 'ge' constraints work the same in Field
    limit: Annotated[int, Field(gt=0)] = 20
    page:  Annotated[int, Field(ge=0)] = 0

    # v2 uses model_config with ConfigDict instead of class Config
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    
class ContactChatInfo(BaseModel):
    """
    Represents a single chat involving a contact, as returned by get_contact_chats.
    """
    chat_jid: str
    name: Optional[str] = None
    is_group: bool
    last_active_timestamp: Optional[str] = None  # ISO-8601 formatted timestamp
    unread_count: Optional[int] = None
    last_message_preview: Optional[LastMessagePreview] = None


class ContactChatsResponse(BaseModel):
    """
    Defines the structure of the return dictionary for the get_contact_chats function.
    """
    chats: List[ContactChatInfo]
    total_chats: int
    page: int
    limit: int
    
    
class SearchContactsArguments(BaseModel):
    """
    Pydantic model for validating the arguments of the search_contacts function.
    This model is based on the inputSchema provided in the function's documentation.
    """
    query: str = Field(
        ..., # Ellipsis indicates that 'query' is a required field.
        title="Query", # Matches the 'title' in the inputSchema.
        description="Search term to match against contact names or phone numbers", # Matches description.
        min_length=1 # Add minimum length validation
        # Pydantic automatically validates that 'query' is a string.
    )

    @field_validator('query')
    @classmethod
    def validate_query_not_whitespace(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or contain only whitespace')
        return v

      
class GetChatArguments(BaseModel):
    chat_jid: str
    include_last_message: bool = True

      
class ChatDetails(BaseModel):
    """
    Represents the detailed information about a chat, as returned by the
    get_chat function. This model is specific to the function's return
    structure.
    """
    chat_jid: str
    name: Optional[str] = None
    is_group: bool
    # Using forward reference if EngineGroupMetadata is not defined/imported directly here
    group_metadata: Optional[Dict[str, Any]] = None # Simplified from Optional['EngineGroupMetadata']
    unread_count: Optional[int] = None
    is_archived: bool
    is_muted_until: Optional[str] = None # ISO-8601 timestamp or 'indefinitely'
    # Using forward reference if EngineMessage is not defined/imported directly here
    last_message: Optional[Dict[str, Any]] = None   # Simplified from Optional['EngineMessage']

   
class SendMessageArgs(BaseModel):
    recipient: str
    message: str
    reply_to_message_id: Optional[str] = None

      
class SendMessageResponse(BaseModel):
    """
    Pydantic model for the return type of the send_message function.
    Confirms the message send operation.
    """
    success: bool = Field(..., description="True if the message was successfully queued for sending, False otherwise.")
    status_message: str = Field(..., description="A human-readable message describing the outcome.")
    message_id: Optional[str] = Field(None, description="The server-assigned ID of the sent message, if successful and available.")
    timestamp: Optional[str] = Field(None, description="ISO-8601 formatted timestamp of when the server acknowledged the send request.")

      
class ListChatsFunctionArgs(BaseModel):
    """
    Pydantic model for validating arguments passed to the list_chats function.
    Corresponds to the inputSchema provided in the function's documentation.
    """
    query: Optional[str] = None
    limit: int = Field(default=20, ge=0)
    page: int = Field(default=0, ge=0)
    include_last_message: bool = True
    sort_by: str = "last_active"

    model_config = ConfigDict(
        extra='forbid'
    )

        
class ChatListItem(BaseModel):
    """Represents a single chat item in the list_chats response."""
    chat_jid: str
    name: Optional[str] = None
    is_group: bool
    last_active_timestamp: Optional[str] = None # ISO-8601 formatted timestamp
    unread_count: Optional[int] = None
    is_archived: bool
    is_pinned: bool
    last_message_preview: Optional[LastMessagePreview] = None # Use the imported Pydantic model

      
class ListChatsResponse(BaseModel):
    """Represents the overall response structure for the list_chats function."""
    chats: List[ChatListItem]
    total_chats: int
    page: int
    limit: int

      
class ListMessagesArgs(BaseModel):
    after: Optional[str] = None
    before: Optional[str] = None
    sender_phone_number: Optional[str] = None
    chat_jid: Optional[str] = None
    query: Optional[str] = None
    limit: int = Field(default=20, ge=0)
    page: int = Field(default=0, ge=0)
    include_context: bool = True
    context_before: int = Field(default=1, ge=0)
    context_after: int = Field(default=1, ge=0)

    model_config = ConfigDict(
        extra='forbid'
    )

        
class MessageWithContext(BaseModel):
    """
    Represents a matched message along with its surrounding context messages.
    """
    matched_message: Message
    context_before: Optional[List[Message]] = None
    context_after: Optional[List[Message]] = None

      
class ListMessagesResponse(BaseModel):
    """
    Defines the structure of the dictionary returned by the list_messages function.
    """
    results: Union[List[Message], List[MessageWithContext]]
    total_matches: int
    page: int
    limit: int


# --- Main Database Model ---

class whatsappDB(BaseModel):
    """
    Root Pydantic model for the WhatsApp API simulation database.
    """
    # Using dictionaries keyed by JID for efficient lookup
    contacts: Dict[str, PersonContact] = Field(default_factory=dict)
    chats: Dict[str, Chat] = Field(default_factory=dict)
    current_user_jid: Optional[str] = None

      
class DirectChatMetadata(BaseModel):
    """
    Metadata for a direct WhatsApp chat.
    """
    chat_jid: str
    contact_jid: str
    name: Optional[str] = None
    is_group: bool # Should always be False for direct chats
    unread_count: Optional[int] = None
    is_archived: bool
    is_muted_until: Optional[str] = None # ISO-8601 timestamp or 'indefinitely'
    last_message: Optional[Message] = None # Using the existing Message model

class SendFileResponse(BaseModel):
    """
    Pydantic model for the return type of the send_file function.
    Confirms the file send operation.
    """
    success: bool = Field(..., description="True if the file was successfully queued for sending, false otherwise.")
    status_message: str = Field(..., description="A human-readable message describing the outcome.")
    message_id: Optional[str] = Field(default=None, description="The server-assigned ID of the sent media message, if successful.")
    timestamp: Optional[str] = Field(default=None, description="ISO-8601 formatted timestamp of server acknowledgement.")

class MaxContextMessages(int,Enum):
    max_context_messages = 100

class ContextMessage(BaseModel):
    """
    Represents a message object as described in the get_message_context function's return type.
    """
    id: str
    timestamp: int  # UNIX timestamp
    sender_id: str
    chat_id: str
    content_type: str  # e.g., 'text', 'image', 'audio', 'video', 'document', 'sticker', 'location'
    text_content: Optional[str] = None
    media_caption: Optional[str] = None
    is_sent_by_me: bool
    status: str  # e.g., 'sent', 'delivered', 'read', 'failed'
    replied_to_message_id: Optional[str] = None
    forwarded: Optional[bool] = None

class MessageContextResponse(BaseModel):
    """
    Represents the overall structure returned by the get_message_context function.
    """
    target_message: ContextMessage
    messages_before: List[ContextMessage]
    messages_after: List[ContextMessage]

class RecipientEndpointModel(BaseModel):
    """
    Represents a single endpoint for a recipient. Corresponds to the
    'Endpoint' schema in the OpenAPI specification.
    """
    endpoint_type: Literal["PHONE_NUMBER"] = Field(default="PHONE_NUMBER", description="Type of endpoint")
    endpoint_value: str = Field(..., description="The endpoint value (e.g., phone number)")
    endpoint_label: Optional[str] = Field(None, description="Label for the endpoint")

class RecipientModel(BaseModel):
    """
    Represents the recipient of a phone call. Corresponds to the
    'Recipient' schema specification.
    """
    contact_id: Optional[str] = Field(None, description="Unique identifier for the contact")
    contact_name: Optional[str] = Field(None, description="Name of the contact")
    contact_endpoints: Optional[List[RecipientEndpointModel]] = Field(None,
                                                                      description="List of endpoints for the contact")
    contact_photo_url: Optional[str] = Field(None, description="URL to the contact's profile photo")
    recipient_type: Optional[Literal["CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL"]] = Field(
        None, description="Type of recipient"
    )
    address: Optional[str] = Field(None, description="Address of the recipient")
    distance: Optional[str] = Field(None, description="Distance to the recipient")
    confidence_level: Optional[Literal["LOW", "MEDIUM", "HIGH"]] = Field(None, description="Confidence level of the recipient match")

    @field_validator('contact_name')
    @classmethod
    def validate_contact_name(cls, v):
        """Ensure contact_name is not empty string if provided."""
        if v is not None and v.strip() == "":
            raise ValueError("contact_name cannot be empty string")
        return v

    @field_validator('contact_endpoints')
    @classmethod
    def validate_contact_endpoints(cls, v):
        """Ensure contact_endpoints is not empty list if provided."""
        if v is not None and len(v) == 0:
            raise ValueError("contact_endpoints cannot be empty list")
        return v
