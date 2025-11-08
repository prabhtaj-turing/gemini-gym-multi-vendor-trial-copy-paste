from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator
import re
import uuid
from datetime import datetime, timezone
from enum import Enum


class MediaType(str, Enum):
    """Enum for media types in WhatsApp."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"


class Name(BaseModel):
    """Model for contact name information."""
    given_name: Optional[str] = Field(None, alias="givenName", description="First name of the contact")
    family_name: Optional[str] = Field(None, alias="familyName", description="Last name of the contact")

    model_config = {"populate_by_name": True}

    @field_validator("given_name", "family_name")
    @classmethod
    def validate_name_fields(cls, v):
        """Validate name fields."""
        if v is not None and v.strip():
            return v.strip()
        return v


class EmailAddress(BaseModel):
    """Model for contact email address."""
    value: str = Field(..., description="Email address value")
    type: Optional[str] = Field(None, description="Type of email address (home, work, etc.)")
    primary: bool = Field(False, description="Whether this is the primary email")

    model_config = {"populate_by_name": True}

    @field_validator("value")
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        if not v or not v.strip():
            raise ValueError('Email value cannot be empty')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError('Invalid email format')
        return v.strip().lower()

    @field_validator("type")
    @classmethod
    def validate_email_type(cls, v):
        """Validate email type."""
        if v is not None and v.strip():
            valid_types = ["home", "work", "other"]
            if v.strip().lower() not in valid_types:
                raise ValueError(f'Invalid email type. Must be one of: {", ".join(valid_types)}')
            return v.strip().lower()
        return v


class PhoneNumber(BaseModel):
    """Model for contact phone number."""
    value: str = Field(..., description="Phone number value")
    type: Optional[str] = Field(None, description="Type of phone number (e.g., mobile, work)")
    primary: bool = Field(False, description="Whether this is the primary phone number")

    model_config = {"populate_by_name": True}

    @field_validator("value")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if not v or not v.strip():
            raise ValueError('Phone number value cannot be empty')
        # More flexible phone number pattern that accepts various formats
        # Remove common separators and spaces
        cleaned = re.sub(r'[-\s\(\)\.]', '', v.strip())
        # Basic international phone number pattern
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, cleaned):
            raise ValueError('Invalid phone number format (expected E.164 or similar)')
        return cleaned

    @field_validator("type")
    @classmethod
    def validate_phone_type(cls, v):
        """Validate phone type."""
        if v is not None and v.strip():
            valid_types = ["mobile", "work", "home", "main", "other"]
            if v.strip().lower() not in valid_types:
                raise ValueError(f'Invalid phone type. Must be one of: {", ".join(valid_types)}')
            return v.strip().lower()
        return v


class Organization(BaseModel):
    """Model for contact organization information."""
    name: Optional[str] = Field(None, description="Name of the organization")
    title: Optional[str] = Field(None, description="Job title within the organization")
    department: Optional[str] = Field(None, description="Department within the organization")
    primary: bool = Field(False, description="Whether this is the primary organization")

    @field_validator("name", "title", "department")
    @classmethod
    def validate_org_fields(cls, v):
        """Validate organization fields."""
        if v is not None and v.strip():
            return v.strip()
        return v


class WhatsAppContact(BaseModel):
    """Model for WhatsApp-specific contact details."""
    jid: str = Field(..., description="WhatsApp JID (e.g., 19876543210@s.whatsapp.net)")
    name_in_address_book: Optional[str] = Field(None, description="Name as stored in address book")
    profile_name: Optional[str] = Field(None, description="WhatsApp profile name")
    phone_number: Optional[str] = Field(None, description="Phone number associated with WhatsApp")
    is_whatsapp_user: bool = Field(True, description="Whether this contact is a WhatsApp user")

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
            return PhoneNumber.validate_phone(v)
        return v


class PhoneContact(BaseModel):
    """Model for phone-specific contact data."""
    contact_id: Optional[str] = Field(None, description="Contact ID")
    contact_name: Optional[str] = Field(None, description="Contact name")
    contact_photo_url: Optional[str] = Field(None, description="Contact photo URL")
    contact_endpoints: Optional[List[Dict[str, Any]]] = Field(None, description="Contact endpoints")

    @field_validator("contact_endpoints")
    @classmethod
    def validate_contact_endpoints(cls, v):
        """Validate contact endpoints."""
        if v is not None and not isinstance(v, list):
            raise ValueError('Contact endpoints must be a list')
        return v


class Contact(BaseModel):
    """
    Pydantic model for a single contact, combining Google People API-like structure
    with WhatsApp-specific data and phone data.
    """
    resource_name: str = Field(..., alias="resourceName", description="Unique identifier for the contact (Google People API format)")
    etag: Optional[str] = Field(None, description="Entity tag for the resource, used for caching")
    names: List[Name] = Field(default_factory=list, description="List of name objects")
    email_addresses: List[EmailAddress] = Field(default_factory=list, alias="emailAddresses", description="List of email objects")
    phone_numbers: List[PhoneNumber] = Field(default_factory=list, alias="phoneNumbers", description="List of phone number objects")
    organizations: List[Organization] = Field(default_factory=list, description="List of organization objects")
    is_workspace_user: bool = Field(False, alias="isWorkspaceUser", description="Whether this contact is a workspace user")
    whatsapp: Optional[WhatsAppContact] = Field(None, description="WhatsApp-specific data for the contact")
    phone: Optional[PhoneContact] = Field(None, description="Phone-specific data for the contact")

    model_config = {"populate_by_name": True}

    @field_validator("resource_name")
    @classmethod
    def validate_resource_name(cls, v):
        """Validate resource name format."""
        if not v or not v.strip():
            raise ValueError('Resource name cannot be empty')
        # Example: people/c1a2b3c4-d5e6-f7a8-b9c0-d1e2f3a4b5c6 or people/19876543210@s.whatsapp.net
        if not re.match(r'^(people|otherContacts)/[a-zA-Z0-9@._-]+$', v.strip()):
            raise ValueError('Invalid resource name format (expected people/ or otherContacts/ prefix)')
        return v.strip()

    @field_validator("names", "email_addresses", "phone_numbers", "organizations")
    @classmethod
    def validate_list_fields(cls, v):
        """Ensure list fields are not empty if provided and contain valid items."""
        if v is not None and not isinstance(v, list):
            raise ValueError('Must be a list')
        return v


class MediaInfo(BaseModel):
    """Model for media information in messages."""
    media_type: MediaType = Field(..., description="Type of media")
    file_name: Optional[str] = Field(None, description="Original file name")
    caption: Optional[str] = Field(None, description="Caption for the media")
    mime_type: Optional[str] = Field(None, description="MIME type of the media")
    simulated_local_path: Optional[str] = Field(None, description="Local path to the media file")
    simulated_file_size_bytes: Optional[int] = Field(None, description="File size in bytes")

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v):
        """Validate file name."""
        if v is not None and v.strip():
            return v.strip()
        return v

    @field_validator("caption")
    @classmethod
    def validate_caption(cls, v):
        """Validate caption."""
        if v is not None and v.strip():
            return v.strip()
        return v

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v):
        """Validate MIME type format."""
        if v is not None and v.strip():
            mime_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*$'
            if not re.match(mime_pattern, v.strip()):
                raise ValueError('Invalid MIME type format')
            return v.strip().lower()
        return v


class QuotedMessageInfo(BaseModel):
    """Model for quoted message information."""
    quoted_message_id: str = Field(..., description="ID of the quoted message")
    quoted_sender_jid: str = Field(..., description="JID of the quoted message sender")
    quoted_text_preview: Optional[str] = Field(None, description="Preview of the quoted text")

    @field_validator("quoted_message_id")
    @classmethod
    def validate_quoted_message_id(cls, v):
        """Validate quoted message ID."""
        if not v or not v.strip():
            raise ValueError('Quoted message ID cannot be empty')
        return v.strip()

    @field_validator("quoted_sender_jid")
    @classmethod
    def validate_quoted_sender_jid(cls, v):
        """Validate quoted sender JID."""
        return WhatsAppContact.validate_jid(v)

    @field_validator("quoted_text_preview")
    @classmethod
    def validate_quoted_text_preview(cls, v):
        """Validate quoted text preview."""
        if v is not None and v.strip():
            return v.strip()
        return v


class Message(BaseModel):
    """Model for a single message in a chat."""
    message_id: str = Field(..., description="Unique message ID")
    chat_jid: str = Field(..., description="JID of the chat this message belongs to")
    sender_jid: str = Field(..., description="JID of the message sender")
    sender_name: Optional[str] = Field(None, description="Display name of the sender")
    timestamp: str = Field(..., description="ISO-8601 formatted timestamp")
    text_content: Optional[str] = Field(None, description="Text content of the message")
    is_outgoing: bool = Field(..., description="Whether this message was sent by the current user")
    media_info: Optional[MediaInfo] = Field(None, description="Media information if this is a media message")
    quoted_message_info: Optional[QuotedMessageInfo] = Field(None, description="Information about quoted message")
    reaction: Optional[str] = Field(None, description="Emoji reaction to the message")
    status: Optional[str] = Field(None, description="Message status (sent, delivered, read)")
    forwarded: Optional[bool] = Field(None, description="Whether this message was forwarded")

    @field_validator("message_id")
    @classmethod
    def validate_message_id(cls, v):
        """Validate message ID format."""
        if not v or not v.strip():
            raise ValueError('Message ID cannot be empty')
        return v.strip()

    @field_validator("chat_jid", "sender_jid")
    @classmethod
    def validate_jid_fields(cls, v):
        """Validate JID fields."""
        return WhatsAppContact.validate_jid(v)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        if not v or not v.strip():
            raise ValueError('Timestamp cannot be empty')
        try:
            datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
            return v.strip()
        except ValueError:
            raise ValueError('Invalid timestamp format (expected ISO-8601)')

    @field_validator("text_content")
    @classmethod
    def validate_text_content(cls, v):
        """Validate text content."""
        if v is not None and v.strip():
            return v.strip()
        return v

    @field_validator("sender_name")
    @classmethod
    def validate_sender_name(cls, v):
        """Validate sender name."""
        if v is not None and v.strip():
            return v.strip()
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate message status."""
        if v is not None and v.strip():
            valid_statuses = ["sent", "delivered", "read", "failed"]
            if v.strip().lower() not in valid_statuses:
                raise ValueError(f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
            return v.strip().lower()
        return v


class LastMessagePreview(BaseModel):
    """Model for last message preview in chat list."""
    message_id: str = Field(..., description="ID of the last message")
    text_snippet: Optional[str] = Field(None, description="Text snippet or placeholder")
    sender_name: Optional[str] = Field(None, description="Name of the sender")
    timestamp: str = Field(..., description="ISO-8601 formatted timestamp")
    is_outgoing: bool = Field(..., description="Whether the message was sent by current user")

    @field_validator("message_id")
    @classmethod
    def validate_message_id(cls, v):
        """Validate message ID format."""
        if not v or not v.strip():
            raise ValueError('Message ID cannot be empty')
        return v.strip()

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        if not v or not v.strip():
            raise ValueError('Timestamp cannot be empty')
        try:
            datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
            return v.strip()
        except ValueError:
            raise ValueError('Invalid timestamp format (expected ISO-8601)')


class GroupParticipant(BaseModel):
    """Model for a group participant."""
    jid: str = Field(..., description="JID of the participant")
    name_in_address_book: Optional[str] = Field(None, description="Name in address book")
    profile_name: Optional[str] = Field(None, description="WhatsApp profile name")
    is_admin: bool = Field(False, description="Whether this participant is an admin")

    @field_validator("jid")
    @classmethod
    def validate_jid(cls, v):
        """Validate JID format."""
        return WhatsAppContact.validate_jid(v)

    @field_validator("name_in_address_book", "profile_name")
    @classmethod
    def validate_name_fields(cls, v):
        """Validate name fields."""
        if v is not None and v.strip():
            return v.strip()
        return v


class GroupMetadata(BaseModel):
    """Model for group metadata."""
    group_description: Optional[str] = Field(None, description="Description of the group")
    creation_timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp of group creation")
    owner_jid: Optional[str] = Field(None, description="JID of the group owner")
    participants_count: int = Field(..., description="Number of participants in the group")
    participants: List[GroupParticipant] = Field(default_factory=list, description="List of group participants")

    @field_validator("group_description")
    @classmethod
    def validate_group_description(cls, v):
        """Validate group description."""
        if v is not None and v.strip():
            return v.strip()
        return v

    @field_validator("creation_timestamp")
    @classmethod
    def validate_creation_timestamp(cls, v):
        """Validate creation timestamp format."""
        if v is not None and v.strip():
            try:
                datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
                return v.strip()
            except ValueError:
                raise ValueError('Invalid timestamp format (expected ISO-8601)')
        return v

    @field_validator("owner_jid")
    @classmethod
    def validate_owner_jid(cls, v):
        """Validate owner JID format."""
        if v is not None and v.strip():
            return WhatsAppContact.validate_jid(v)
        return v

    @field_validator("participants_count")
    @classmethod
    def validate_participants_count(cls, v):
        """Validate participants count."""
        if v < 0:
            raise ValueError('Participants count cannot be negative')
        return v


class Chat(BaseModel):
    """Model for a chat (individual or group)."""
    chat_jid: str = Field(..., description="JID of the chat")
    name: Optional[str] = Field(None, description="Name of the chat (contact name or group subject)")
    is_group: bool = Field(..., description="Whether this is a group chat")
    last_active_timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp of last activity")
    unread_count: Optional[int] = Field(0, description="Number of unread messages")
    is_archived: bool = Field(False, description="Whether this chat is archived")
    is_pinned: bool = Field(False, description="Whether this chat is pinned")
    is_muted_until: Optional[str] = Field(None, description="ISO-8601 timestamp until muted or 'indefinitely'")
    group_metadata: Optional[GroupMetadata] = Field(None, description="Group metadata if this is a group chat")
    messages: List[Message] = Field(default_factory=list, description="List of messages in this chat")

    @field_validator("chat_jid")
    @classmethod
    def validate_chat_jid(cls, v):
        """Validate chat JID format."""
        return WhatsAppContact.validate_jid(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate chat name."""
        if v is not None and v.strip():
            return v.strip()
        return v

    @field_validator("last_active_timestamp")
    @classmethod
    def validate_last_active_timestamp(cls, v):
        """Validate last active timestamp format."""
        if v is not None and v.strip():
            try:
                datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
                return v.strip()
            except ValueError:
                raise ValueError('Invalid timestamp format (expected ISO-8601)')
        return v

    @field_validator("unread_count")
    @classmethod
    def validate_unread_count(cls, v):
        """Validate unread count."""
        if v < 0:
            raise ValueError('Unread count cannot be negative')
        return v

    @field_validator("is_muted_until")
    @classmethod
    def validate_is_muted_until(cls, v):
        """Validate muted until timestamp."""
        if v is not None and v.strip():
            if v.strip().lower() == "indefinitely":
                return "indefinitely"
            try:
                datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
                return v.strip()
            except ValueError:
                raise ValueError('Invalid timestamp format (expected ISO-8601 or "indefinitely")')
        return v


class WhatsAppDB(BaseModel):
    """Main database model for WhatsApp service simulation.

    This model validates the exact structure used by the WhatsApp functions:
    - current_user_jid: str - Current user's WhatsApp JID
    - contacts: Dict[str, Contact] - matches DB.get("contacts", {})
    - chats: Dict[str, Chat] - matches DB.get("chats", {})
    """
    current_user_jid: str = Field(..., description="Current user's WhatsApp JID")
    contacts: Dict[str, Contact] = Field(default_factory=dict, description="Dictionary of contacts by resource name")
    chats: Dict[str, Chat] = Field(default_factory=dict, description="Dictionary of chats by chat JID")

    model_config = {"populate_by_name": True}

    @field_validator('contacts', mode='before')
    @classmethod
    def validate_contacts(cls, v):
        """Convert contacts dictionary to Contact instances."""
        if isinstance(v, dict):
            return {k: Contact(**contact_data) if isinstance(contact_data, dict) else contact_data 
                   for k, contact_data in v.items()}
        return v

    @field_validator('chats', mode='before')
    @classmethod
    def validate_chats(cls, v):
        """Convert chats dictionary to Chat instances."""
        if isinstance(v, dict):
            return {k: Chat(**chat_data) if isinstance(chat_data, dict) else chat_data 
                   for k, chat_data in v.items()}
        return v

    @field_validator("current_user_jid")
    @classmethod
    def validate_current_user_jid(cls, v):
        """Validate current user JID format."""
        return WhatsAppContact.validate_jid(v)

    def get_all_contacts(self) -> Dict[str, Contact]:
        """Retrieve all contacts from the WhatsApp database."""
        return self.contacts

    def get_contact_by_jid(self, jid: str) -> Optional[Contact]:
        """Retrieve a specific contact by JID from the WhatsApp database."""
        for resource_name, contact in self.contacts.items():
            if contact.whatsapp and contact.whatsapp.jid == jid:
                return contact
        return None

    def search_contacts(self, query: str) -> List[Contact]:
        """Search for contacts by query (name, phone, or JID) in the WhatsApp database."""
        matches = []
        query_lower = query.lower()
        
        for resource_name, contact in self.contacts.items():
            # Search in WhatsApp data
            if contact.whatsapp:
                if (contact.whatsapp.name_in_address_book and 
                    query_lower in contact.whatsapp.name_in_address_book.lower()):
                    matches.append(contact)
                    continue
                if (contact.whatsapp.profile_name and 
                    query_lower in contact.whatsapp.profile_name.lower()):
                    matches.append(contact)
                    continue
                if (contact.whatsapp.phone_number and 
                    query_lower in contact.whatsapp.phone_number):
                    matches.append(contact)
                    continue
                if query_lower in contact.whatsapp.jid.lower():
                    matches.append(contact)
                    continue
            
            # Search in names
            for name_obj in contact.names:
                given_name = name_obj.given_name or ""
                family_name = name_obj.family_name or ""
                full_name = f"{given_name} {family_name}".strip()
                if full_name and query_lower in full_name.lower():
                    matches.append(contact)
                    break
            
            # Search in phone numbers
            for phone_obj in contact.phone_numbers:
                if phone_obj.value and query_lower in phone_obj.value:
                    matches.append(contact)
                    break
        
        return matches

    def add_contact(self, contact: Contact) -> None:
        """Add a contact to the WhatsApp database."""
        self.contacts[contact.resource_name] = contact

    def get_all_chats(self) -> Dict[str, Chat]:
        """Retrieve all chats from the WhatsApp database."""
        return self.chats

    def get_chat_by_jid(self, chat_jid: str) -> Optional[Chat]:
        """Retrieve a specific chat by JID from the WhatsApp database."""
        return self.chats.get(chat_jid)

    def add_chat(self, chat: Chat) -> None:
        """Add a chat to the WhatsApp database."""
        self.chats[chat.chat_jid] = chat

    def get_message(self, chat_jid: str, message_id: str) -> Optional[Message]:
        """Get a specific message from a chat."""
        chat = self.get_chat_by_jid(chat_jid)
        if not chat:
            return None
        
        for message in chat.messages:
            if message.message_id == message_id:
                return message
        return None

    def add_message_to_chat(self, chat_jid: str, message: Message) -> None:
        """Add a message to a specific chat."""
        chat = self.get_chat_by_jid(chat_jid)
        if chat:
            chat.messages.append(message)
            chat.last_active_timestamp = message.timestamp

    def get_contact_display_name(self, contact: Contact, fallback_jid: str) -> str:
        """Get display name for a contact with fallback."""
        if contact.whatsapp:
            if contact.whatsapp.name_in_address_book:
                return contact.whatsapp.name_in_address_book
            if contact.whatsapp.profile_name:
                return contact.whatsapp.profile_name
        
        # Fallback to names
        for name_obj in contact.names:
            given_name = name_obj.given_name or ""
            family_name = name_obj.family_name or ""
            full_name = f"{given_name} {family_name}".strip()
            if full_name:
                return full_name
        
        return fallback_jid

    def get_last_message_preview(self, chat: Chat) -> Optional[LastMessagePreview]:
        """Get last message preview for a chat."""
        if not chat.messages:
            return None
        
        # Sort messages by timestamp and get the latest
        sorted_messages = sorted(chat.messages, key=lambda m: m.timestamp, reverse=True)
        last_message = sorted_messages[0]
        
        # Generate snippet
        snippet = None
        if last_message.text_content:
            snippet = last_message.text_content
        elif last_message.media_info:
            if last_message.media_info.caption:
                snippet = last_message.media_info.caption
            else:
                snippet = last_message.media_info.media_type.value.title()
        
        return LastMessagePreview(
            message_id=last_message.message_id,
            text_snippet=snippet,
            sender_name=last_message.sender_name,
            timestamp=last_message.timestamp,
            is_outgoing=last_message.is_outgoing
        )
