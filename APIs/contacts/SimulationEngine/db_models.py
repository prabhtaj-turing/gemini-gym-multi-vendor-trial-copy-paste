from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator
import re


class Name(BaseModel):
    """Model for contact name information."""
    model_config = {"populate_by_name": True}
    
    given_name: Optional[str] = Field(None, alias="givenName", description="First name of the contact")
    family_name: Optional[str] = Field(None, alias="familyName", description="Last name of the contact")

    @field_validator("given_name", "family_name")
    @classmethod
    def validate_name_fields(cls, v):
        """Validate name fields."""
        if v is not None and v.strip():
            return v.strip()
        return v


class EmailAddress(BaseModel):
    """Model for contact email address."""
    model_config = {"populate_by_name": True}
    
    value: str = Field(..., description="Email address value")
    type: Optional[str] = Field(None, description="Type of email address (home, work, etc.)")
    primary: Optional[bool] = Field(None, description="Whether this is the primary email")

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
    model_config = {"populate_by_name": True}
    
    value: Optional[str] = Field(None, description="Phone number value")
    type: Optional[str] = Field(None, description="Type of phone number (mobile, work, etc.)")
    primary: Optional[bool] = Field(None, description="Whether this is the primary phone number")

    @field_validator("value")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is not None and v.strip():
            # Basic phone validation - allows various formats including parentheses
            # Remove all non-digit characters except + at the beginning for validation
            cleaned = re.sub(r'[^\d\+]', '', v.strip())
            if not cleaned or len(cleaned) < 7 or len(cleaned) > 16:
                raise ValueError('Invalid phone number format')
            return v.strip()
        return v

    @field_validator("type")
    @classmethod
    def validate_phone_type(cls, v):
        """Validate phone type."""
        if v is not None and v.strip():
            valid_types = ["mobile", "work", "home", "other"]
            if v.strip().lower() not in valid_types:
                raise ValueError(f'Invalid phone type. Must be one of: {", ".join(valid_types)}')
            return v.strip().lower()
        return v


class Organization(BaseModel):
    """Model for contact organization information."""
    model_config = {"populate_by_name": True}
    
    name: Optional[str] = Field(None, description="Organization name")
    title: Optional[str] = Field(None, description="Job title")
    department: Optional[str] = Field(None, description="Department name")
    primary: Optional[bool] = Field(None, description="Whether this is the primary organization")

    @field_validator("name", "title", "department")
    @classmethod
    def validate_organization_fields(cls, v):
        """Validate organization fields."""
        if v is not None and v.strip():
            return v.strip()
        return v


class WhatsAppContact(BaseModel):
    """Model for WhatsApp-specific contact details."""
    model_config = {"populate_by_name": True}
    
    jid: str = Field(..., description="WhatsApp JID identifier")
    name_in_address_book: str = Field(..., description="Name as stored in address book")
    profile_name: str = Field(..., description="WhatsApp profile name")
    phone_number: Optional[str] = Field(None, description="Phone number associated with WhatsApp")
    is_whatsapp_user: bool = Field(..., description="Whether this contact is a WhatsApp user")

    @field_validator("jid")
    @classmethod
    def validate_jid(cls, v):
        """Validate WhatsApp JID format."""
        if not v or not v.strip():
            raise ValueError('JID cannot be empty')
        # Allow both WhatsApp format and custom domain format
        whatsapp_pattern = r'^\d+@s\.whatsapp\.net$'
        custom_pattern = r'^[a-zA-Z0-9_]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not (re.match(whatsapp_pattern, v.strip()) or re.match(custom_pattern, v.strip())):
            raise ValueError('Invalid JID format. Must be WhatsApp format (digits@s.whatsapp.net) or email format')
        return v.strip()

    @field_validator("name_in_address_book", "profile_name")
    @classmethod
    def validate_names(cls, v):
        """Validate name fields."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is not None and v.strip():
            phone_pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$'
            if not re.match(phone_pattern, v.strip()):
                raise ValueError('Invalid phone number format')
            return v.strip()
        return v


class PhoneEndpoint(BaseModel):
    """Model for phone contact endpoint."""
    model_config = {"populate_by_name": True}
    
    endpoint_type: str = Field(..., description="Type of endpoint")
    endpoint_value: str = Field(..., description="Endpoint value")
    endpoint_label: str = Field(..., description="Endpoint label")

    @field_validator("endpoint_type")
    @classmethod
    def validate_endpoint_type(cls, v):
        """Validate endpoint type."""
        if not v or not v.strip():
            raise ValueError('Endpoint type cannot be empty')
        # Based on database analysis, only PHONE_NUMBER is used
        if v.strip().upper() != "PHONE_NUMBER":
            raise ValueError('Endpoint type must be "PHONE_NUMBER"')
        return v.strip().upper()

    @field_validator("endpoint_value", "endpoint_label")
    @classmethod
    def validate_endpoint_fields(cls, v):
        """Validate endpoint fields."""
        if not v or not v.strip():
            raise ValueError('Endpoint field cannot be empty')
        return v.strip()


class PhoneContact(BaseModel):
    """Model for native phone contact details."""
    model_config = {"populate_by_name": True}
    
    contact_id: str = Field(..., description="Unique contact identifier")
    contact_name: str = Field(..., description="Contact display name")
    recipient_type: Optional[str] = Field(None, description="Type of recipient")
    contact_photo_url: Optional[str] = Field(None, description="URL of contact photo")
    contact_endpoints: Optional[List[PhoneEndpoint]] = Field(None, description="List of contact endpoints")

    @field_validator("contact_id", "contact_name")
    @classmethod
    def validate_required_fields(cls, v):
        """Validate required fields."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    @field_validator("recipient_type")
    @classmethod
    def validate_recipient_type(cls, v):
        """Validate recipient type."""
        if v is not None and v.strip():
            # Based on database analysis, only CONTACT is used
            if v.strip().upper() != "CONTACT":
                raise ValueError('Recipient type must be "CONTACT"')
            return v.strip().upper()
        return v

    @field_validator("contact_photo_url")
    @classmethod
    def validate_photo_url(cls, v):
        """Validate photo URL format."""
        if v is not None and v.strip():
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, v.strip()):
                raise ValueError('Invalid photo URL format')
            return v.strip()
        return v
    
    @field_validator("contact_endpoints")
    @classmethod
    def validate_contact_endpoints(cls, v):
        """Validate contact endpoints."""
        if v is not None and not isinstance(v, list):
            raise ValueError('Contact endpoints must be a list')
        return v


class Contact(BaseModel):
    """Model for a single contact in the database."""
    model_config = {"populate_by_name": True}
    
    resource_name: str = Field(..., alias="resourceName", description="Unique resource identifier")
    etag: str = Field(..., description="Entity tag for caching")
    names: Optional[List[Name]] = Field(None, description="List of contact names")
    email_addresses: Optional[List[EmailAddress]] = Field(None, alias="emailAddresses", description="List of email addresses")
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias="phoneNumbers", description="List of phone numbers")
    organizations: Optional[List[Organization]] = Field(None, description="List of organizations")
    is_workspace_user: Optional[bool] = Field(None, alias="isWorkspaceUser", description="Whether this is a workspace user")
    notes: Optional[str] = Field(None, description="Contact notes")
    whatsapp: Optional[WhatsAppContact] = Field(None, description="WhatsApp contact details")
    phone: Optional[PhoneContact] = Field(None, description="Phone contact details")

    @field_validator("resource_name")
    @classmethod
    def validate_resource_name(cls, v):
        """Validate resource name format."""
        if not v or not v.strip():
            raise ValueError('Resource name cannot be empty')
        # Resource name should start with 'people/' or 'otherContacts/'
        if not v.strip().startswith(('people/', 'otherContacts/')):
            raise ValueError('Resource name must start with "people/" or "otherContacts/"')
        return v.strip()

    @field_validator("etag")
    @classmethod
    def validate_etag(cls, v):
        """Validate etag format."""
        if not v or not v.strip():
            raise ValueError('Etag cannot be empty')
        return v.strip()

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v):
        """Validate notes field."""
        if v is not None and v.strip():
            return v.strip()
        return v


class ContactsDB(BaseModel):
    """Main database model for Contacts simulation.
    
    This model validates the exact structure used by the Contacts functions:
    - myContacts: Dict[str, Contact] - matches DB["myContacts"]
    - otherContacts: Dict[str, Contact] - matches DB["otherContacts"] 
    - directory: Dict[str, Contact] - matches DB["directory"]
    """
    model_config = {"populate_by_name": True}
    
    myContacts: Dict[str, Contact] = Field(default_factory=dict, description="Dictionary of my contacts by resource name")
    otherContacts: Dict[str, Contact] = Field(default_factory=dict, description="Dictionary of other contacts by resource name")
    directory: Dict[str, Contact] = Field(default_factory=dict, description="Dictionary of directory contacts by resource name")
