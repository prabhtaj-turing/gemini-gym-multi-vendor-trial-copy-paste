from typing import List, Optional, Literal, Union, Dict
from pydantic import BaseModel, Field

# --- Existing Models (with minor adjustments if necessary) ---

class Name(BaseModel):
    """Pydantic model for a contact's name."""
    givenName: Optional[str] = None
    familyName: Optional[str] = None

class EmailAddress(BaseModel):
    """Pydantic model for a contact's email address."""
    value: str
    type: Optional[str] = None
    primary: Optional[bool] = None

class PhoneNumber(BaseModel):
    """Pydantic model for a contact's phone number."""
    value: Optional[str] = None
    type: Optional[str] = None
    primary: Optional[bool] = None

class Organization(BaseModel):
    """Pydantic model for a contact's organization."""
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    primary: Optional[bool] = None

# --- New Models for Integrated Services ---

class WhatsAppContact(BaseModel):
    """Pydantic model for WhatsApp-specific contact details."""
    jid: str
    name_in_address_book: str
    profile_name: str
    phone_number: Optional[str]
    is_whatsapp_user: bool

class PhoneEndpoint(BaseModel):
    """Pydantic model for a phone contact's endpoint."""
    endpoint_type: str
    endpoint_value: str
    endpoint_label: str

class PhoneContact(BaseModel):
    """Pydantic model for native phone contact details."""
    contact_id: str
    contact_name: str
    recipient_type: Optional[str] = None
    contact_photo_url: Optional[str] = None
    contact_endpoints: Optional[List[PhoneEndpoint]] = None

# --- Updated Core Contact Model ---

class Contact(BaseModel):
    """
    Pydantic model for a single contact, accommodating various sources.
    """
    resourceName: str
    etag: str
    names: Optional[List[Name]] = None
    emailAddresses: Optional[List[EmailAddress]] = None
    phoneNumbers: Optional[List[PhoneNumber]] = None
    organizations: Optional[List[Organization]] = None
    isWorkspaceUser: Optional[bool] = None
    notes: Optional[str] = None
    whatsapp: Optional[WhatsAppContact] = None
    phone: Optional[PhoneContact] = None

# --- Top-Level Database Structure Models ---

class MyContacts(BaseModel):
    """Pydantic model for the 'myContacts' section of the database."""
    myContacts: Dict[str, Contact]

class OtherContacts(BaseModel):
    """Pydantic model for the 'otherContacts' section of the database."""
    otherContacts: Dict[str, Contact]

class Directory(BaseModel):
    """Pydantic model for the 'directory' section of the database."""
    directory: Dict[str, Contact]

class FullContactDB(BaseModel):
    """
    Pydantic model representing the entire contact database structure.
    """
    myContacts: Dict[str, Contact]
    otherContacts: Dict[str, Contact]
    directory: Dict[str, Contact]

# --- Response Models (Maintained for API validation) ---

class ContactListResponse(BaseModel):
    """
    Pydantic model for a list of contacts response.
    """
    contacts: List[Contact]

class WorkspaceUser(BaseModel):
    """
    Pydantic model for a single Google Workspace user.

    Ensures that the essential fields are present and that the user
    is correctly flagged as a workspace user.
    """
    resourceName: str
    etag: str
    isWorkspaceUser: Literal[True]  # Enforces that this field must be True
    names: List[Name]               # A user is expected to have a name
    emailAddresses: List[EmailAddress]  # A user is expected to have an email
    organizations: Optional[List[Organization]] = None

class WorkspaceUserListResponse(BaseModel):
    """
    Pydantic model for validating the final structure of the
    list_workspace_users function's response.
    """
    users: List[WorkspaceUser]

class DirectorySearchResponse(BaseModel):
    """
    Pydantic model for validating the list of directory search results.
    """
    directory_users: List[WorkspaceUser]