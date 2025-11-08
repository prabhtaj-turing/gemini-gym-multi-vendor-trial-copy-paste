from typing import Any, Dict, Optional, List, Literal, Union
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from datetime import datetime
from enum import Enum
import re
from .custom_errors import (
    InvalidRecipientError,
    InvalidEndpointError,
    MessageBodyRequiredError,
    InvalidMediaAttachmentError
)


class APIName(str, Enum):
    """Enumeration of API action types for generic messages."""

    SEND = "send"
    SHOW_MESSAGE_RECIPIENT_CHOICES = "show_message_recipient_choices"
    ASK_FOR_MESSAGE_BODY = "ask_for_message_body"
    SHOW_MESSAGE_RECIPIENT_NOT_FOUND_OR_SPECIFIED = "show_message_recipient_not_found_or_specified"


class Action(BaseModel):
    """An action record for message operations."""

    action_type: APIName = Field(..., description="The type of action performed")
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Input parameters for the action"
    )
    outputs: Dict[str, Any] = Field(
        default_factory=dict, description="Output results from the action"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the action"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When the action occurred",
    )
    message_id: Optional[str] = Field(
        None, description="ID of the message affected by this action"
    )

    @field_validator("timestamp")
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        if v:
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("Timestamp must be in ISO format")
        return v


class Endpoint(BaseModel):
    """
    Represents one single endpoint (phone number or WhatsApp profile) corresponding to a user.
    """
    type: Literal["PHONE_NUMBER", "WHATSAPP_PROFILE"] = Field(
        description="The endpoint type."
    )
    value: str = Field(description="The endpoint value (phone number or WhatsApp ID).")
    label: Optional[str] = Field(
        default=None, 
        description="Label for the endpoint (e.g., 'mobile', 'work')"
    )

    @field_validator('type')
    def validate_endpoint_type(cls, v):
        if v not in ["PHONE_NUMBER", "WHATSAPP_PROFILE"]:
            raise ValueError(
                f"endpoint.type must be 'PHONE_NUMBER' or 'WHATSAPP_PROFILE', got: {v}"
            )
        return v

    @field_validator('value')
    def validate_endpoint_value(cls, v, info):
        if not v or not isinstance(v, str) or not v.strip():
            raise InvalidEndpointError("endpoint.value is required and cannot be empty")
        return v.strip()
    
    @model_validator(mode='after')
    def validate_endpoint_format(self):
        """Validate the endpoint value format based on its type."""
        endpoint_type = self.type
        endpoint_value = self.value
        
        if endpoint_type == "PHONE_NUMBER":
            # E.164 format: starts with +, followed by 1-15 digits
            # Pattern: +[1-9]\d{1,14}
            e164_pattern = r'^\+[1-9]\d{1,14}$'
            if not re.match(e164_pattern, endpoint_value):
                raise InvalidEndpointError(
                    f"Invalid phone number format. Phone numbers must be in E.164 format "
                    f"(e.g., +14155552671). Got: {endpoint_value}"
                )
        
        elif endpoint_type == "WHATSAPP_PROFILE":
            # WhatsApp JID format: {number}@s.whatsapp.net
            # Example: 14155552671@s.whatsapp.net
            whatsapp_pattern = r'^\d+@s\.whatsapp\.net$'
            if not re.match(whatsapp_pattern, endpoint_value):
                raise InvalidEndpointError(
                    f"Invalid WhatsApp profile format. WhatsApp profiles must be in JID format "
                    f"(e.g., 14155552671@s.whatsapp.net). Got: {endpoint_value}"
                )
        
        return self


class Recipient(BaseModel):
    """
    The recipient of the message, representing a contact.
    """
    name: str = Field(
        description="The name of the contact. This is strictly necessary."
    )
    endpoints: List[Endpoint] = Field(
        description="One or more endpoints for the contact."
    )

    @field_validator('name')
    def validate_contact_name(cls, v):
        if not v or not isinstance(v, str) or not v.strip():
            raise InvalidRecipientError("recipient.name is required and cannot be empty")
        return v.strip()

    @field_validator('endpoints')
    def validate_endpoints(cls, v):
        if not v or not isinstance(v, list):
            raise InvalidRecipientError("recipient.endpoints must be a non-empty list")
        if len(v) == 0:
            raise InvalidRecipientError("recipient.endpoints list cannot be empty")
        return v


class MediaAttachment(BaseModel):
    """
    Metadata associated with media payload. Supports images, videos, documents, and audio files.
    Note: For SMS endpoints, all fields (media_id, media_type, source) are required. 
    For WhatsApp endpoints, media_id and media_type are required; source is optional.
    """
    media_id: str = Field(description="File path or URL to the media.")
    media_type: Literal["IMAGE", "VIDEO", "DOCUMENT", "AUDIO"] = Field(
        description="Type of the media. Required for all endpoints."
    )
    source: Optional[Literal["IMAGE_RETRIEVAL", "IMAGE_GENERATION", "IMAGE_UPLOAD", "GOOGLE_PHOTO"]] = Field(
        default=None,
        description="Source of the media. Required for SMS endpoints, optional for WhatsApp endpoints."
    )

    @field_validator('media_id')
    def validate_media_id(cls, v):
        if not v or not isinstance(v, str) or not v.strip():
            raise InvalidMediaAttachmentError("media_attachment.media_id is required and cannot be empty")
        return v.strip()


class Observation(BaseModel):
    """Observation response from generic messaging operations."""
    
    action_card_content_passthrough: Optional[str] = Field(
        default=None,
        description="Base64 JSON field for action card content"
    )
    sent_message_id: Optional[str] = Field(
        default=None,
        description="A unique identifier for the operation associated with this observation"
    )
    status: str = Field(
        description="Whether the operation was successful or not"
    )


def validate_source_for_endpoint(
    endpoint_type: str,
    media_attachments: List[MediaAttachment]
) -> None:
    """Validate that source is provided for SMS endpoints.
    
    Args:
        endpoint_type: The type of endpoint ("PHONE_NUMBER" or "WHATSAPP_PROFILE").
        media_attachments: List of MediaAttachment objects to validate.
        
    Raises:
        InvalidMediaAttachmentError: If source is None for SMS endpoints.
    """
    if endpoint_type == "PHONE_NUMBER":
        for attachment in media_attachments:
            if attachment.source is None:
                raise InvalidMediaAttachmentError(
                    "source is required for SMS endpoints. "
                    "For WhatsApp endpoints, source is optional."
                )


def validate_send(
    contact_name: str,
    endpoint: Dict[str, Any],
    body: Optional[str] = None,
    media_attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Validate the send operation parameters.
    
    Args:
        contact_name: The name of the contact.
        endpoint: The endpoint to send to.
        body: The message body (optional).
        media_attachments: Optional media attachments.
        
    Returns:
        Dict containing validated data.
    """
    # Validate contact_name
    if not isinstance(contact_name, str) or not contact_name.strip():
        raise InvalidRecipientError("contact_name is required and cannot be empty")
    
    # Validate endpoint
    if not isinstance(endpoint, dict):
        raise InvalidEndpointError("endpoint must be a dictionary")
    
    endpoint_obj = Endpoint(**endpoint)
    
    # Validate body - can be None or string
    if body is not None and not isinstance(body, str):
        raise MessageBodyRequiredError("body must be a string or None")
    
    # Validate media_attachments if provided
    media_attachments_objs = []
    if media_attachments is not None:
        if not isinstance(media_attachments, list):
            raise InvalidMediaAttachmentError("media_attachments must be a list")
        for attachment in media_attachments:
            media_attachments_objs.append(MediaAttachment(**attachment))
    
    # Validate source for endpoint-specific requirements
    if media_attachments_objs:
        validate_source_for_endpoint(endpoint_obj.type, media_attachments_objs)
    
    return {
        "contact_name": contact_name.strip(),
        "endpoint": endpoint_obj,
        "body": body,
        "media_attachments": media_attachments_objs
    }


def validate_show_recipient_choices(
    recipients: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Validate the show_recipient_choices operation parameters.
    
    Args:
        recipients: List of recipient dictionaries.
        
    Returns:
        Dict containing validated data.
    """
    if not isinstance(recipients, list):
        raise InvalidRecipientError("recipients must be a list")
    
    if not recipients:
        raise InvalidRecipientError("recipients list cannot be empty")
    
    recipient_objs = []
    for recipient in recipients:
        recipient_objs.append(Recipient(**recipient))
    
    return {
        "recipients": recipient_objs
    }


def validate_ask_for_message_body(
    contact_name: str,
    endpoint: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate the ask_for_message_body operation parameters.
    
    Args:
        contact_name: The name of the contact.
        endpoint: The endpoint.
        
    Returns:
        Dict containing validated data.
    """
    # Validate contact_name
    if not isinstance(contact_name, str) or not contact_name.strip():
        raise InvalidRecipientError("contact_name is required and cannot be empty")
    
    # Validate endpoint
    if not isinstance(endpoint, dict):
        raise InvalidEndpointError("endpoint must be a dictionary")
    
    endpoint_obj = Endpoint(**endpoint)
    
    return {
        "contact_name": contact_name.strip(),
        "endpoint": endpoint_obj
    }

