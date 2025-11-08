from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from enum import Enum

class FunctionName(str, Enum):
    """The name of the API."""
    MAKE_CALL = "make_call"
    PREPARE_CALL = "prepare_call"
    SHOW_CALL_RECIPIENT_CHOICES = "show_call_recipient_choices"
    SHOW_CALL_RECIPIENT_NOT_FOUND_OR_SPECIFIED = "show_call_recipient_not_found_or_specified"

class Action(BaseModel):
    """An action record."""
    action_type: FunctionName
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RecipientEndpointModel(BaseModel):
    """
    Represents a single endpoint for a recipient. Corresponds to the
    'Endpoint' schema in the OpenAPI specification.
    """
    endpoint_type: Optional[Literal["PHONE_NUMBER"]] = Field(default="PHONE_NUMBER", description="Type of endpoint")
    endpoint_value: str = Field(..., description="The endpoint value (e.g., phone number)")
    endpoint_label: Optional[str] = Field(None, description="Label for the endpoint")


class RecipientModel(BaseModel):
    """
    Base recipient model with required contact_endpoints.
    Used for show_call_recipient_choices where endpoints are needed to show choices.
    """
    contact_id: Optional[str] = Field(None, description="Unique identifier for the contact")
    contact_name: Optional[str] = Field(None, description="Name of the contact")
    contact_endpoints: List[RecipientEndpointModel] = Field(..., description="List of endpoints for the contact")
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


class RecipientModelOptionalEndpoints(BaseModel):
    """
    Recipient model with optional contact_endpoints.
    Used for make_call and prepare_call where endpoints might be searched for.
    """
    contact_id: Optional[str] = Field(None, description="Unique identifier for the contact")
    contact_name: Optional[str] = Field(None, description="Name of the contact")
    contact_endpoints: Optional[List[RecipientEndpointModel]] = Field(None, description="List of endpoints for the contact")
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


# New models for Google People API-like structure

class NameModel(BaseModel):
    """Represents a name in Google People API format."""
    givenName: Optional[str] = Field(None, description="Given name")
    familyName: Optional[str] = Field(None, description="Family name")


class PhoneNumberModel(BaseModel):
    """Represents a phone number in Google People API format."""
    value: str = Field(..., description="Phone number value")
    type: Optional[str] = Field(None, description="Type of phone number (e.g., mobile, work)")
    primary: Optional[bool] = Field(None, description="Whether this is the primary phone number")


class EmailModel(BaseModel):
    """Represents an email address in Google People API format."""
    value: str = Field(..., description="Email address value")
    type: Optional[str] = Field(None, description="Type of email (e.g., work, personal)")
    primary: Optional[bool] = Field(None, description="Whether this is the primary email")


class OrganizationModel(BaseModel):
    """Represents an organization in Google People API format."""
    name: Optional[str] = Field(None, description="Organization name")
    title: Optional[str] = Field(None, description="Job title")
    department: Optional[str] = Field(None, description="Department")
    primary: Optional[bool] = Field(None, description="Whether this is the primary organization")


class ContactModel(BaseModel):
    """
    Represents a complete contact with both Google People API and phone-specific data.
    This is the new structure for contacts in the DB.
    """
    resourceName: str = Field(..., description="Google People API resource name")
    etag: str = Field(..., description="Google People API etag")
    names: List[NameModel] = Field(..., description="List of names")
    phoneNumbers: List[PhoneNumberModel] = Field(..., description="List of phone numbers")
    emailAddresses: List[EmailModel] = Field(default_factory=list, description="List of email addresses")
    organizations: List[OrganizationModel] = Field(default_factory=list, description="List of organizations")
    isWorkspaceUser: bool = Field(..., description="Whether this is a workspace user")
    phone: RecipientModel = Field(..., description="Phone-specific data")


class ChoiceEndpointModel(BaseModel):
    """Represents a single endpoint in a choice."""
    type: Literal["PHONE_NUMBER"] = Field(..., description="Type of endpoint")
    value: str = Field(..., description="The endpoint value (e.g., phone number)")
    label: Optional[str] = Field(None, description="Label for the endpoint")


class SingleEndpointChoiceModel(BaseModel):
    """Represents a choice with a single endpoint (for recipients with one endpoint)."""
    contact_name: Optional[str] = Field(None, description="Name of the contact")
    contact_photo_url: Optional[str] = Field(None, description="URL to the contact's profile photo")
    recipient_type: Optional[Literal["CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL"]] = Field(None, description="Type of recipient")
    address: Optional[str] = Field(None, description="Address of the recipient")
    distance: Optional[str] = Field(None, description="Distance to the recipient")
    endpoints: List[ChoiceEndpointModel] = Field(..., description="List of endpoints for the contact")
    
    @field_validator('endpoints')
    @classmethod
    def validate_endpoints(cls, v):
        """Ensure endpoints list is not empty."""
        if not v:
            raise ValueError("endpoints cannot be empty")
        return v


class MultipleEndpointChoiceModel(BaseModel):
    """Represents a choice with a single endpoint (for recipients with multiple endpoints)."""
    contact_name: Optional[str] = Field(None, description="Name of the contact")
    contact_photo_url: Optional[str] = Field(None, description="URL to the contact's profile photo")
    recipient_type: Optional[Literal["CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL"]] = Field(None, description="Type of recipient")
    address: Optional[str] = Field(None, description="Address of the recipient")
    distance: Optional[str] = Field(None, description="Distance to the recipient")
    endpoint: ChoiceEndpointModel = Field(..., description="Single endpoint for this choice")


ChoiceModel = Union[SingleEndpointChoiceModel, MultipleEndpointChoiceModel]


class PhoneAPIResponseModel(BaseModel):
    """Base model for phone API responses."""
    status: Literal["success", "error"] = Field(..., description="Status of the operation")
    call_id: str = Field(..., description="Unique identifier for the call")
    emitted_action_count: int = Field(..., description="Number of actions generated")
    templated_tts: str = Field(..., description="Text-to-speech message")
    action_card_content_passthrough: str = Field(..., description="Content for action card")
    
    @field_validator('call_id')
    @classmethod
    def validate_call_id(cls, v):
        """Ensure call_id is not empty."""
        if not v or v.strip() == "":
            raise ValueError("call_id cannot be empty")
        return v
    
    @field_validator('emitted_action_count')
    @classmethod
    def validate_emitted_action_count(cls, v):
        """Ensure emitted_action_count is non-negative."""
        if v < 0:
            raise ValueError("emitted_action_count cannot be negative")
        return v


class ShowChoicesResponseModel(PhoneAPIResponseModel):
    """Model for show_call_recipient_choices response."""
    choices: List[ChoiceModel] = Field(..., description="List of choices for the user")
    
    @field_validator('choices')
    @classmethod
    def validate_choices(cls, v):
        """Ensure choices list is not empty."""
        if not v:
            raise ValueError("choices cannot be empty")
        return v

class CallHistoryEntry(BaseModel):
    call_id: str = Field(alias='call_id')
    timestamp: float
    phone_number: str = Field(alias='phone_number')
    recipient_name: str = Field(alias='recipient_name')
    recipient_photo_url: Optional[str] = Field(None, alias='recipient_photo_url')
    on_speakerphone: bool = Field(alias='on_speakerphone')
    status: Literal['completed']

    @field_validator('call_id')
    @classmethod
    def validate_call_id(cls, v):
        """Ensure call_id is not empty."""
        if not v or v.strip() == "":
            raise ValueError("call_id cannot be empty")
        return v

class PhoneDB(BaseModel):
    contacts: Dict[str, ContactModel]
    businesses: Dict[str, RecipientModel]
    special_contacts: Dict[str, RecipientModel] = Field(alias='special_contacts')
    call_history: Dict[str, CallHistoryEntry] = Field(alias='call_history')
    prepared_calls: Dict[str, Any] = Field(alias='prepared_calls')
    recipient_choices: Dict[str, Any] = Field(alias='recipient_choices')
    not_found_records: Dict[str, Any] = Field(alias='not_found_records')
