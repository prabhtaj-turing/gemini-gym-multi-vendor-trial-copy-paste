from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
import re
from common_utils.utils import validate_email_util
from common_utils.phone_utils import is_phone_number_valid, normalize_phone_number

# Shared Models
class TicketFieldItem(BaseModel):
    id: int
    value: Union[str, int, List[str]]

class SharedTicketAuditMetadata(BaseModel):
    system: Optional[Dict[str, Any]] = None
    custom: Optional[Dict[str, Any]] = None

# --- Models for Users API ---

class UserPhoto(BaseModel):
    """Model for user profile picture attachment."""
    content_type: Optional[str] = Field(None, description="MIME type of the image")
    content_url: Optional[str] = Field(None, description="URL to the image")
    filename: Optional[str] = Field(None, description="Original filename")
    size: Optional[int] = Field(None, ge=0, description="File size in bytes")

class UserCustomFields(BaseModel):
    """Model for custom user fields."""
    department: Optional[str] = Field(None, description="User's department")
    employee_id: Optional[str] = Field(None, description="Employee ID")
    hire_date: Optional[str] = Field(None, description="Date of hire (YYYY-MM-DD)")
    manager: Optional[str] = Field(None, description="User's manager")
    location: Optional[str] = Field(None, description="User's location")
    
    @field_validator('hire_date')
    @classmethod
    def validate_hire_date(cls, v):
        if v is not None:
            try:
                # Use centralized datetime validation and return normalized value
                from common_utils.datetime_utils import validate_zendesk_datetime, InvalidDateTimeFormatError
                return validate_zendesk_datetime(v)
            except InvalidDateTimeFormatError as e:
                # Convert to Zendesk's local InvalidDateTimeFormatError
                from .custom_errors import InvalidDateTimeFormatError as ZendeskInvalidDateTimeFormatError
                raise ZendeskInvalidDateTimeFormatError(f'Invalid hire_date format: {str(e)}')
        return v

class UserCreateInputData(BaseModel):
    """Defines the structure and validation rules for user creation parameters."""
    
    # Mandatory fields
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's primary email address")
    role: Literal["end-user", "agent", "admin"] = Field("end-user", description="User's role in the system")
    
    # Optional fields
    organization_id: Optional[int] = Field(None, gt=0, description="ID of the user's organization")
    tags: Optional[List[str]] = Field(None, description="User's tags for categorization")
    photo: Optional[UserPhoto] = Field(None, description="User's profile picture")
    details: Optional[str] = Field(None, max_length=1000, description="Additional details about the user")
    default_group_id: Optional[int] = Field(None, gt=0, description="ID of the user's default group")
    alias: Optional[str] = Field(None, min_length=1, max_length=100, description="Display alias for the user")
    custom_role_id: Optional[int] = Field(None, gt=0, description="Custom role ID for Enterprise plan agents")
    external_id: Optional[str] = Field(None, min_length=1, max_length=255, description="External system identifier")
    locale: Optional[str] = Field(None, description="User's locale (BCP-47 format)")
    locale_id: Optional[int] = Field(None, gt=0, description="User's language identifier")
    moderator: Optional[bool] = Field(None, description="Whether user has forum moderation capabilities")
    notes: Optional[str] = Field(None, max_length=1000, description="Internal notes about the user")
    only_private_comments: Optional[bool] = Field(None, description="Whether user can only create private comments")
    phone: Optional[str] = Field(None, description="User's primary phone number")
    remote_photo_url: Optional[str] = Field(None, description="URL to user's profile picture")
    restricted_agent: Optional[bool] = Field(None, description="Whether agent has access restrictions")
    shared_phone_number: Optional[bool] = Field(None, description="Whether phone number is shared")
    signature: Optional[str] = Field(None, max_length=1000, description="User's email signature")
    suspended: Optional[bool] = Field(None, description="Whether user account is suspended")
    ticket_restriction: Optional[Literal["organization", "groups", "assigned", "requested"]] = Field(
        None, description="Which tickets the user can access"
    )
    time_zone: Optional[str] = Field(None, description="User's time zone")
    verified: Optional[bool] = Field(None, description="Whether user identity is verified")
    user_fields: Optional[UserCustomFields] = Field(None, description="Custom field values")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v.strip() == "":
            raise ValueError('Name cannot be empty')
        return v.strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            # Basic phone number validation - allows various formats
            phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
            if not re.match(phone_pattern, re.sub(r'[\s\-\(\)]', '', v)):
                raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 50:  # Limit number of tags
                raise ValueError('Maximum 50 tags allowed')
            for tag in v:
                if not tag or len(tag) > 50:
                    raise ValueError('Tags must be non-empty and under 50 characters')
        return v
    
    @field_validator('external_id')
    @classmethod
    def validate_external_id(cls, v):
        if v is not None:
            # External ID should be alphanumeric with optional hyphens/underscores
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('External ID must contain only letters, numbers, hyphens, and underscores')
        return v


class UserUpdateInputData(BaseModel):
    """Defines the structure and validation rules for user update parameters.
    
    All fields are optional for updates except user_id which identifies the user.
    This allows partial updates where only specified fields are modified.
    """

    # Required field for identification
    user_id: int = Field(..., gt=0, description="Unique identifier for the user to update")

    # All other fields are optional for updates
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's primary email address")
    role: Optional[Literal["end-user", "agent", "admin"]] = Field(None, description="User's role in the system")
    organization_id: Optional[int] = Field(None, gt=0, description="ID of the user's organization")
    tags: Optional[List[str]] = Field(None, description="User's tags for categorization")
    photo: Optional[Dict[str, Any]] = Field(None, description="User's profile picture")
    details: Optional[str] = Field(None, max_length=1000, description="Additional details about the user")
    default_group_id: Optional[int] = Field(None, gt=0, description="ID of the user's default group")
    alias: Optional[str] = Field(None, min_length=1, max_length=100, description="Display alias for the user")
    custom_role_id: Optional[int] = Field(None, gt=0, description="Custom role ID for Enterprise plan agents")
    external_id: Optional[str] = Field(None, min_length=1, max_length=255, description="External system identifier")
    locale: Optional[str] = Field(None, description="User's locale (BCP-47 format)")
    locale_id: Optional[int] = Field(None, gt=0, description="User's language identifier")
    moderator: Optional[bool] = Field(None, description="Whether user has forum moderation capabilities")
    notes: Optional[str] = Field(None, max_length=1000, description="Internal notes about the user")
    only_private_comments: Optional[bool] = Field(None, description="Whether user can only create private comments")
    phone: Optional[str] = Field(None, description="User's primary phone number")
    remote_photo_url: Optional[str] = Field(None, description="URL to user's profile picture")
    restricted_agent: Optional[bool] = Field(None, description="Whether agent has access restrictions")
    shared_phone_number: Optional[bool] = Field(None, description="Whether phone number is shared")
    signature: Optional[str] = Field(None, max_length=1000, description="User's email signature")
    suspended: Optional[bool] = Field(None, description="Whether user account is suspended")
    ticket_restriction: Optional[Literal["organization", "groups", "assigned", "requested"]] = Field(
        None, description="Which tickets the user can access"
    )
    time_zone: Optional[str] = Field(None, description="User's time zone")
    verified: Optional[bool] = Field(None, description="Whether user identity is verified")
    user_fields: Optional[Dict[str, Any]] = Field(None, description="Custom field values")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            # Basic phone number validation - allows various formats
            phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
            if not re.match(phone_pattern, re.sub(r'[\s\-\(\)]', '', v)):
                raise ValueError('Invalid phone number format')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 50:  # Limit number of tags
                raise ValueError('Maximum 50 tags allowed')
            for tag in v:
                if not tag or len(tag) > 50:
                    raise ValueError('Tags must be non-empty and under 50 characters')
        return v

    @field_validator('external_id')
    @classmethod
    def validate_external_id(cls, v):
        if v is not None:
            # External ID should be alphanumeric with optional hyphens/underscores
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('External ID must contain only letters, numbers, hyphens, and underscores')
        return v


class UserResponseData(BaseModel):
    """Defines the structure of user response data."""
    id: int
    name: str
    email: str
    role: str
    active: bool
    created_at: str
    updated_at: str
    url: str
    organization_id: Optional[int] = None
    tags: Optional[List[str]] = None
    photo: Optional[UserPhoto] = None
    details: Optional[str] = None
    default_group_id: Optional[int] = None
    alias: Optional[str] = None
    custom_role_id: Optional[int] = None
    external_id: Optional[str] = None
    locale: Optional[str] = None
    locale_id: Optional[int] = None
    moderator: Optional[bool] = None
    notes: Optional[str] = None
    only_private_comments: Optional[bool] = None
    phone: Optional[str] = None
    remote_photo_url: Optional[str] = None
    restricted_agent: Optional[bool] = None
    shared_phone_number: Optional[bool] = None
    signature: Optional[str] = None
    suspended: Optional[bool] = None
    ticket_restriction: Optional[str] = None
    time_zone: Optional[str] = None
    verified: Optional[bool] = None
    user_fields: Optional[UserCustomFields] = None

# --- Models for update_ticket arguments ---

class TicketUpdateInputData(BaseModel):
    """Defines the structure and validation rules for ticket update parameters."""
    assignee_id: Optional[int] = Field(None, description="ID of the agent assigned to the ticket.")
    assignee_email: Optional[EmailStr] = Field(None, description="Email of the agent assigned to the ticket.")
    subject: Optional[str] = Field(None, min_length=1, description="Subject of the ticket. Must be non-empty if provided.")
    comment_body: Optional[str] = Field(None, min_length=1, description="Comment body. Must be non-empty if provided.")
    priority: Optional[Literal["urgent", "high", "normal", "low"]] = Field(None, description="Priority level of the ticket.")
    ticket_type: Optional[Literal["problem", "incident", "question", "task"]] = Field(None, description="Type of the ticket.")
    status: Optional[Literal["new", "open", "pending", "hold", "solved", "closed"]] = Field(None, description="Status of the ticket.")
    # New fields for ticket updates
    attribute_value_ids: Optional[List[int]] = Field(None, description="List of attribute value IDs for the ticket.")
    custom_status_id: Optional[int] = Field(None, description="ID of the custom status for the ticket.")
    requester: Optional[str] = Field(None, description="Email or name of the requester.")
    safe_update: Optional[bool] = Field(None, description="Whether to perform a safe update.")
    ticket_form_id: Optional[int] = Field(None, ge=0, description="ID of the ticket form.")
    updated_stamp: Optional[str] = Field(None, description="Timestamp for when the ticket was last updated.")
    via_followup_source_id: Optional[int] = Field(None, ge=0, description="ID of the via followup source.")
    via_id: Optional[int] = Field(None, description="ID of the via channel.")
    voice_comment: Optional[Dict[str, Union[str, int]]] = Field(None, description="Voice comment data for the ticket.")

    @field_validator('voice_comment')
    @classmethod
    def validate_voice_comment(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('Voice comment data must be a dictionary')
            if "from" in v:
                if not isinstance(v["from"], str) or v['from'].strip() == "":
                    raise ValueError('From must be a non-empty string')
                if not is_phone_number_valid(v["from"]):
                    raise ValueError('From must be a valid phone number')
                v["from"] = normalize_phone_number(v["from"])
            if "to" in v:
                if not isinstance(v["to"], str) or v['to'].strip() == "":
                    raise ValueError('To must be a non-empty string')
                if not is_phone_number_valid(v["to"]):
                    raise ValueError('To must be a valid phone number')
                v["to"] = normalize_phone_number(v["to"])
            if "recording_url" in v:
                if not isinstance(v["recording_url"], str) or v['recording_url'].strip() == "":
                    raise ValueError('Recording URL must be a non-empty string')
            if "started_at" in v:
                if not isinstance(v["started_at"], str) or v['started_at'].strip() == "":
                    raise ValueError('Started at must be a non-empty string')
            if "ended_at" in v:
                if not isinstance(v["ended_at"], str) or v['ended_at'].strip() == "":
                    raise ValueError('Ended at must be a non-empty string')
            if "call_duration" in v:
                if not isinstance(v["call_duration"], int) or v['call_duration'] <= 0:
                    raise ValueError('Call duration must be a positive integer')
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v):
        if v is not None:
            if v.strip() == "":
                raise ValueError('Subject cannot be empty')
        return v.strip()

    @field_validator('requester')
    @classmethod
    def validate_requester(cls, v):
        if "@" in v:
            validate_email_util(v, "requester")
        return v

# --- Models for create_ticket arguments ---

class TicketCollaboratorInput(BaseModel):
    user_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None # Docstring specifies str; EmailStr could be used for validation

class TicketCommentInput(BaseModel):
    body: str
    html_body: Optional[str] = None
    public: Optional[bool] = True
    uploads: Optional[List[str]] = None
    author_id: Optional[int] = None

class TicketUserActionInput(BaseModel):
    user_id: Optional[int] = None
    user_email: Optional[EmailStr] = None # Docstring specifies str; EmailStr could be used
    action: Optional[Literal["put", "delete"]] = None

class TicketViaSourceInput(BaseModel):
    rel: Optional[str] = None
    # If via.source on input can have more fields, consider Dict[str, Any]
    # or add `model_config = {"extra": "allow"}` if using Pydantic v2
    # or `class Config: extra = "allow"` for Pydantic v1

class TicketViaInput(BaseModel):
    channel: Optional[str] = None
    source: Optional[TicketViaSourceInput] = None

class TicketCreateInputData(BaseModel):
    """Defines the structure of the 'ticket' object within the input dictionary argument."""
    requester_id: int # Based on docstring: "This dictionary must contain 'requester_id'..."
    comment: TicketCommentInput # Based on docstring: "...and 'comment' keys."

    assignee_email: Optional[EmailStr] = None
    assignee_id: Optional[int] = None
    brand_id: Optional[int] = None
    collaborator_ids: Optional[List[int]] = None
    collaborators: Optional[List[TicketCollaboratorInput]] = None
    custom_fields: Optional[List[TicketFieldItem]] = None
    due_at: Optional[str] = None # ISO 8601 format
    email_cc_ids: Optional[List[int]] = None
    email_ccs: Optional[List[TicketUserActionInput]] = None
    external_id: Optional[str] = None
    follower_ids: Optional[List[int]] = None
    followers: Optional[List[TicketUserActionInput]] = None
    group_id: Optional[int] = None
    macro_id: Optional[int] = None
    macro_ids: Optional[List[int]] = None
    metadata: Optional[SharedTicketAuditMetadata] = None
    organization_id: Optional[int] = None
    priority: Optional[Literal["urgent", "high", "normal", "low"]] = None
    problem_id: Optional[int] = None
    raw_subject: Optional[str] = None
    recipient: Optional[str] = None
    sharing_agreement_ids: Optional[List[int]] = None
    status: Optional[Literal["new", "open", "pending", "hold", "solved", "closed"]] = None
    subject: Optional[str] = None
    submitter_id: Optional[int] = None
    tags: Optional[List[str]] = None
    type: Optional[Literal["problem", "incident", "question", "task"]] = None
    via: Optional[TicketViaInput] = None
    # New fields for ticket creation
    attribute_value_ids: Optional[List[int]] = Field(None, description="List of attribute value IDs for the ticket.")
    custom_status_id: Optional[int] = Field(None, description="ID of the custom status for the ticket.")
    requester: Optional[str] = Field(None, description="Email or name of the requester.")
    safe_update: Optional[bool] = Field(None, description="Whether to perform a safe update.")
    ticket_form_id: Optional[int] = Field(None, description="ID of the ticket form.")
    updated_stamp: Optional[str] = Field(None, description="Timestamp for when the ticket was last updated.")
    via_followup_source_id: Optional[int] = Field(None, description="ID of the via followup source.")
    via_id: Optional[int] = Field(None, description="ID of the via channel.")
    voice_comment: Optional[Dict[str, Any]] = Field(None, description="Voice comment data for the ticket.")

    @field_validator('requester')
    @classmethod
    def validate_requester(cls, v):
        if "@" in v:
            validate_email_util(v, "requester")
        return v

class OrganizationCreateInputData(BaseModel):
    """Defines the structure of the 'organization' object within the input dictionary argument."""
    name: str
    domain_names: Optional[List[str]] = []
    industry: Optional[str] = None
    location: Optional[str] = None
    external_id: Optional[str] = None
    group_id: Optional[int] = None
    notes: Optional[str] = None
    details: Optional[str] = None
    shared_tickets: Optional[bool] = None
    shared_comments: Optional[bool] = None
    tags: Optional[List[str]] = []
    organization_fields: Optional[Dict[str, Any]] = {}


# =============================================================================
# NEW MODELS FOR ENHANCED API FUNCTIONALITY
# =============================================================================

# -----------------------------------------------------------------------------
# Common/Shared Models
# -----------------------------------------------------------------------------

class PaginationMeta(BaseModel):
    """Standard pagination metadata for all list endpoints"""
    page: int
    per_page: int
    total: int
    pages: int

class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=100, ge=1, le=100)

class SortingParams(BaseModel):
    """Standard sorting parameters"""
    sort_by: Optional[str] = None
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")

# -----------------------------------------------------------------------------
# Comment Models (for list_ticket_comments)
# -----------------------------------------------------------------------------

class CommentOutput(BaseModel):
    """Output model for ticket comments"""
    id: int
    ticket_id: int
    author_id: int
    body: str
    html_body: Optional[str] = None
    public: bool = True
    type: str = "Comment"
    audit_id: Optional[int] = None
    attachments: List[int] = []  # Array of attachment IDs
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None
    via: Optional[Dict[str, Any]] = None

class CommentListParams(BaseModel):
    """Parameters for list_ticket_comments"""
    ticket_id: int
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=100, ge=1, le=100)
    sort_by: str = Field(default="created_at", pattern="^(created_at|updated_at)$")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")
    include_attachments: bool = False

class CommentListResponse(BaseModel):
    """Response model for list_ticket_comments"""
    comments: List[CommentOutput]
    pagination: PaginationMeta

# -----------------------------------------------------------------------------
# Audit Models (for get_ticket_audit, list_ticket_audits)
# -----------------------------------------------------------------------------

class AuditEventOutput(BaseModel):
    """Output model for audit events"""
    id: int
    type: str  # "Create", "Comment", "Change"
    author_id: int
    body: Optional[str] = None  # For Comment events
    html_body: Optional[str] = None  # For Comment events
    public: Optional[bool] = None  # For Comment events
    attachments: Optional[List[int]] = None  # For Comment events
    field_name: Optional[str] = None  # For Change events
    value: Optional[Any] = None  # For Change events
    previous_value: Optional[Any] = None  # For Change events
    via: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class AuditOutput(BaseModel):
    """Output model for ticket audits"""
    id: int
    ticket_id: int
    created_at: str
    author_id: int
    events: List[AuditEventOutput]
    metadata: Optional[Dict[str, Any]] = None
    via: Optional[Dict[str, Any]] = None

class AuditListParams(BaseModel):
    """Parameters for list_ticket_audits"""
    ticket_id: int
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=100, ge=1, le=100)
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")

class AuditListResponse(BaseModel):
    """Response model for list_ticket_audits"""
    audits: List[AuditOutput]
    pagination: PaginationMeta

# -----------------------------------------------------------------------------
# Attachment Models (for upload_file, get_attachment, delete_upload)
# -----------------------------------------------------------------------------

class AttachmentOutput(BaseModel):
    """Output model for attachments"""
    id: int
    file_name: str
    content_type: str
    content_url: str
    size: int
    width: Optional[str] = None
    height: Optional[str] = None
    inline: bool = False
    deleted: bool = False
    thumbnails: List[Dict[str, Any]] = []
    url: str  # API URL for this attachment
    mapped_content_url: Optional[str] = None
    upload_token: Optional[str] = None
    created_at: str

class UploadFileParams(BaseModel):
    """Parameters for upload_file"""
    filename: str
    token: Optional[str] = None
    content_type: Optional[str] = None
    file_size: int = 1024

class UploadResponse(BaseModel):
    """Response model for upload_file"""
    upload: Dict[str, Any]  # Contains token, attachment, attachments

# -----------------------------------------------------------------------------
# Search Models (for search_resources)
# -----------------------------------------------------------------------------

class SearchResultItem(BaseModel):
    """Output model for search result items"""
    id: int
    result_type: str  # "ticket", "user", "organization"
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    url: Optional[str] = None
    # Additional fields vary by result_type
    subject: Optional[str] = None  # For tickets
    email: Optional[str] = None    # For users
    industry: Optional[str] = None # For organizations
    priority: Optional[str] = None # For tickets
    status: Optional[str] = None   # For tickets
    relevance_score: Optional[int] = None  # Internal scoring

class SearchParams(BaseModel):
    """Parameters for search_resources"""
    query: str
    type: Optional[str] = Field(default=None, pattern="^(ticket|user|organization)$")
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=25, ge=1, le=100)
    sort_by: str = Field(default="relevance", pattern="^(created_at|updated_at|relevance)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class SearchResponse(BaseModel):
    """Response model for search_resources"""
    results: List[SearchResultItem]
    count: int
    pagination: PaginationMeta

# -----------------------------------------------------------------------------
# Enhanced Output Models (for existing functions with new fields)
# -----------------------------------------------------------------------------

class UserOutput(BaseModel):
    """Enhanced output model for users with all Zendesk API fields"""
    id: int
    name: str
    email: str
    role: str = "end-user"
    organization_id: Optional[int] = None
    tags: List[str] = []
    external_id: Optional[str] = None
    active: bool = True
    created_at: str
    updated_at: str
    # Additional fields that could be added in future
    phone: Optional[str] = None
    time_zone: Optional[str] = None
    locale: Optional[str] = None

class OrganizationOutput(BaseModel):
    """Enhanced output model for organizations with all Zendesk API fields"""
    id: int
    name: str
    domain_names: List[str] = []
    external_id: Optional[str] = None
    group_id: Optional[int] = None
    notes: Optional[str] = None
    details: Optional[str] = None
    shared_tickets: Optional[bool] = None
    shared_comments: Optional[bool] = None
    tags: List[str] = []
    organization_fields: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    url: str
    # Existing fields
    industry: Optional[str] = None
    location: Optional[str] = None

class TicketOutput(BaseModel):
    """Enhanced output model for tickets with all Zendesk API fields"""
    id: int
    subject: Optional[str] = None
    description: str
    priority: str = "normal"
    status: str = "new"
    type: str = "question"
    requester_id: int
    submitter_id: int
    assignee_id: Optional[int] = None
    organization_id: Optional[int] = None
    tags: List[str] = []
    created_at: str
    updated_at: str
    # Additional enhanced fields
    external_id: Optional[str] = None
    encoded_id: Optional[str] = None
    url: Optional[str] = None
    raw_subject: Optional[str] = None
    recipient: Optional[str] = None
    collaborator_ids: List[int] = []
    follower_ids: List[int] = []
    email_cc_ids: List[int] = []
    custom_fields: List[TicketFieldItem] = []
    via: Optional[Dict[str, Any]] = None

# -----------------------------------------------------------------------------
# Mock Configuration Models (for testing and development)
# -----------------------------------------------------------------------------

class MockAttachmentConfig(BaseModel):
    """Configuration for generating mock attachments"""
    file_name: str
    content_type: Optional[str] = None
    size: int = 1024
    is_image: bool = False
    width: Optional[int] = None
    height: Optional[int] = None

class MockSearchConfig(BaseModel):
    """Configuration for mock search results"""
    query: str
    resource_types: List[str] = ["ticket", "user", "organization"]
    max_results_per_type: int = 10