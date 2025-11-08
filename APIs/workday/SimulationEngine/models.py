from typing import Optional, List, Dict, Any, Literal, ClassVar, Union
from enum import Enum, auto
import datetime
from pydantic import ConfigDict, field_validator, AnyUrl
from pydantic import BaseModel, ValidationError, Field, conint, RootModel, \
      ConfigDict, field_validator
from pydantic import ValidationError as PydanticValidationError

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, conint
from pydantic import field_validator, model_validator, EmailStr
from pydantic.config import ConfigDict
from datetime import datetime, date
from pydantic import constr, conint
import re

from pydantic import (
    BaseModel,
    ValidationError as PydanticValidationError,
    Field,
    AnyUrl,
    constr,
    conint,
    field_validator,
    ConfigDict
)

# Try to import EmailStr, fallback to str with custom validation if not available
try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # Fallback to str, we'll add custom email validation

# Pagination constants
class PaginationConstants:
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1

# Bid status enum
class BidStatus(str, Enum):
    AWARD_RETRACTED = "award_retracted"
    AWARDED = "awarded"
    DRAFT = "draft"
    REJECTED = "rejected"
    REJECTION_RETRACTED = "rejection_retracted"
    RESUBMITTED = "resubmitted"
    REVISING = "revising"
    SUBMITTED = "submitted"
    UNCLAIMED = "unclaimed"
    UPDATE_REQUESTED = "update_requested"

# Include resources enum for EventBids
class IncludeResource(str, Enum):
    EVENT = "event"
    SUPPLIER_COMPANY = "supplier_company"

SUPPORTED_INCLUDES = {"supplier_company", "worksheet"}

class ProjectAttributes(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    name: str
    description: Optional[str] = None
    state: Optional[Literal["draft", "requested", "planned", "active", "completed", "canceled", "on_hold"]] = None
    target_start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_spend_amount: Optional[float] = None
    approved_spend_amount: Optional[float] = None
    estimated_savings_amount: Optional[float] = None
    estimated_spend_amount: Optional[float] = None
    canceled_note: Optional[str] = None
    canceled_reason: Optional[str] = None
    on_hold_note: Optional[str] = None
    on_hold_reason: Optional[str] = None
    needs_attention: Optional[bool] = None
    marked_as_needs_attention_at: Optional[datetime] = None
    needs_attention_note: Optional[str] = None
    needs_attention_reason: Optional[str] = None

    model_config = ConfigDict(extra='forbid')

class ProjectRelationships(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    attachments: Optional[List[Dict[str, Any]]] = None
    creator: Optional[Dict[str, Any]] = None
    requester: Optional[Dict[str, Any]] = None
    owner: Optional[Dict[str, Any]] = None
    project_type: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra='forbid')

class ProjectInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    type_id: Optional[str] = "projects" # Defaulting as per common practice, but can be overridden
    id: Optional[str] = None
    external_id: Optional[str] = None
    supplier_companies: Optional[List[Dict[str, Any]]] = None
    supplier_contacts: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    attributes: ProjectAttributes  # 'attributes' object itself is required
    relationships: Optional[ProjectRelationships] = None

    model_config = ConfigDict(extra='forbid')
        

class ScimNameModel(BaseModel):
    """Pydantic model for a user's name components."""
    givenName: str = Field(..., min_length=1)
    familyName: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')
        
    @field_validator('givenName')
    def validate_given_name(cls, v: str):
        """Validate givenName field."""
        if not isinstance(v, str):
            raise ValueError("givenName must be a string")
        if not v or not v.strip():
            raise ValueError("givenName cannot be empty")
        return v
        
    @field_validator('familyName')
    def validate_family_name(cls, v: str):
        """Validate familyName field."""
        if not isinstance(v, str):
            raise ValueError("familyName must be a string")
        if not v or not v.strip():
            raise ValueError("familyName cannot be empty")
        return v


class RoleModel(BaseModel):
    """SCIM Role sub-attribute object for Users.

    - value: required
    - display, type, primary: optional
    """
    value: str
    display: Optional[str] = None
    type: Optional[str] = None
    primary: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')
        
    @field_validator('value')
    def validate_value(cls, v: str):
        """Validate value field."""
        if not isinstance(v, str):
            raise ValueError("value must be a string")
        if not v or not v.strip():
            raise ValueError("value cannot be empty")
        return v
        
    @field_validator('display')
    def validate_display(cls, v: Optional[str]):
        """Validate display field."""
        if v is not None and not isinstance(v, str):
            raise ValueError("display must be a string")
        return v
        
    @field_validator('type')
    def validate_type(cls, v: Optional[str]):
        """Validate type field."""
        if v is not None and not isinstance(v, str):
            raise ValueError("type must be a string")
        return v
        
    @field_validator('primary', mode='before')
    def validate_primary(cls, v: Optional[bool]):
        """Validate primary field."""
        if v is not None and not isinstance(v, bool):
            raise ValueError("primary must be a boolean")
        return v


class UserScimInputModel(BaseModel):
    """Pydantic model for validating the SCIM user creation request body.

    Matches Workday Strategic Sourcing SCIM 2.0 Create User input. The server generates
    response-only fields like id and meta.
    """
    schemas: Optional[List[str]] = Field(None, description="SCIM schemas, typically ['urn:ietf:params:scim:schemas:core:2.0:User']")
    externalId: Optional[str] = Field(None, description="External identifier for the user")
    userName: EmailStr = Field(..., description="Unique username, typically an email address")
    name: ScimNameModel = Field(..., description="User's name components")
    active: Optional[bool] = Field(True, description="Whether the user account is active")
    roles: Optional[List[RoleModel]] = Field(None, description="Roles assigned to the user")

    model_config = ConfigDict(extra='forbid')
        
    @field_validator('schemas')
    def validate_schemas(cls, v: Optional[List[str]]):
        """Validate that schemas include the required SCIM User schema if provided."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("schemas must be a list")
            if len(v) == 0:
                raise ValueError("schemas cannot be empty")
            for schema in v:
                if not isinstance(schema, str):
                    raise ValueError("All schema items must be strings")
            required_schema = "urn:ietf:params:scim:schemas:core:2.0:User"
            if required_schema not in v:
                raise ValueError(f"schemas must include '{required_schema}'")
        return v

    @field_validator('active', mode='before')
    def validate_active(cls, v: Optional[bool]):
        """Validate active field."""
        if v is not None and not isinstance(v, bool):
            raise ValueError("active must be a boolean")
        return v
        
    @field_validator('externalId')
    def validate_external_id(cls, v: Optional[str]):
        """Validate externalId field."""
        if v is not None and not isinstance(v, str):
            raise ValueError("externalId must be a string")
        return v
        
    @field_validator('roles')
    def validate_roles(cls, v: Optional[List[RoleModel]]):
        """Validate roles field."""
        if v is not None and not isinstance(v, list):
            raise ValueError("roles must be a list")
        return v

# Define Literal types for Enums described in the docstring
EventTypeLiteral = Literal[
    "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT",
    "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT",
    "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT"
]

EventStateLiteral = Literal[
    "draft", "scheduled", "published", "live_editing", "closed", "canceled"
]

EventDuplicationStateLiteral = Literal[
    "scheduled", "started", "finished", "failed"
]

class EventAttributesInputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    title: Optional[str] = None
    event_type: Optional[EventTypeLiteral] = None
    state: Optional[EventStateLiteral] = None
    duplication_state: Optional[EventDuplicationStateLiteral] = None
    spend_amount: Optional[float] = None
    request_type: Optional[str] = None
    late_bids: Optional[bool] = None
    revise_bids: Optional[bool] = None
    instant_notifications: Optional[bool] = None
    supplier_rsvp_deadline: Optional[str] = None
    supplier_question_deadline: Optional[str] = None
    bid_submission_deadline: Optional[str] = None
    created_at: Optional[str] = None
    closed_at: Optional[str] = None
    published_at: Optional[str] = None
    external_id: Optional[str] = None
    is_public: Optional[bool] = None
    restricted: Optional[bool] = None
    custom_fields: Optional[List[Any]] = None # Docstring implies list, type of items not specified

    model_config = ConfigDict(extra='forbid')

class EventRelationshipsInputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    attachments: Optional[List[Any]] = None # Type of items not specified
    project: Optional[Dict[str, Any]] = None # Structure not detailed, allowing a dictionary
    spend_category: Optional[Dict[str, Any]] = None # Structure not detailed
    event_template: Optional[Dict[str, Any]] = None # Structure not detailed
    commodity_codes: Optional[List[Any]] = None # Type of items not specified

    model_config = ConfigDict(extra='forbid')

class EventInputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    external_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[EventTypeLiteral] = None
    suppliers: Optional[List[Any]] = None # Type of items not specified
    supplier_contacts: Optional[List[Any]] = None # Type of items not specified
    attributes: Optional[EventAttributesInputModel] = None
    relationships: Optional[EventRelationshipsInputModel] = None

    model_config = ConfigDict(extra='forbid')

class EventOutputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: int
    duplication_state: EventDuplicationStateLiteral
    external_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[EventTypeLiteral] = None
    suppliers: Optional[List[Any]] = None
    supplier_contacts: Optional[List[Any]] = None
    attributes: Optional[EventAttributesInputModel] = None
    relationships: Optional[EventRelationshipsInputModel] = None

# Define Literals for enum-like fields to enforce specific string values
VALID_EVENT_STATES = Literal[
    "draft", "scheduled", "published", "live_editing", "closed", "canceled"
]
VALID_EVENT_TYPES = Literal[
    "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT",
    "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT",
    "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT"
]

class EventFilterModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    updated_at_from: Optional[str] = None
    updated_at_to: Optional[str] = None
    title_contains: Optional[str] = None
    title_not_contains: Optional[str] = None
    spend_category_id_equals: Optional[List[int]] = None
    state_equals: Optional[List[VALID_EVENT_STATES]] = None
    event_type_equals: Optional[List[VALID_EVENT_TYPES]] = None
    request_type_equals: Optional[List[str]] = None
    supplier_rsvp_deadline_from: Optional[str] = None
    supplier_rsvp_deadline_to: Optional[str] = None
    supplier_rsvp_deadline_empty: Optional[bool] = None
    supplier_rsvp_deadline_not_empty: Optional[bool] = None
    supplier_question_deadline_from: Optional[str] = None
    supplier_question_deadline_to: Optional[str] = None
    supplier_question_deadline_empty: Optional[bool] = None
    supplier_question_deadline_not_empty: Optional[bool] = None
    bid_submission_deadline_from: Optional[str] = None
    bid_submission_deadline_to: Optional[str] = None
    bid_submission_deadline_empty: Optional[bool] = None
    bid_submission_deadline_not_empty: Optional[bool] = None
    created_at_from: Optional[str] = None
    created_at_to: Optional[str] = None
    published_at_from: Optional[str] = None
    published_at_to: Optional[str] = None
    published_at_empty: Optional[bool] = None
    published_at_not_empty: Optional[bool] = None
    closed_at_from: Optional[str] = None
    closed_at_to: Optional[str] = None
    closed_at_empty: Optional[bool] = None
    closed_at_not_empty: Optional[bool] = None
    spend_amount_from: Optional[float] = None
    spend_amount_to: Optional[float] = None
    spend_amount_empty: Optional[bool] = None
    spend_amount_not_empty: Optional[bool] = None
    external_id_empty: Optional[bool] = None
    external_id_not_empty: Optional[bool] = None
    external_id_equals: Optional[str] = None
    external_id_not_equals: Optional[str] = None

    model_config = ConfigDict(extra='forbid')

class AttachmentRelationshipObject(BaseModel):
    """Defines the structure for a relationship object, requiring type and id."""
    model_config = ConfigDict(extra='forbid')
    
    type: str # One of Contract, Event, Project, or Supplier Company
    id: int # The ID of the object


class AttachmentAttributes(BaseModel):
    """Pydantic model for validating the 'attributes' of an attachment."""
    model_config = ConfigDict(extra='forbid')
    
    title: Optional[str] = Field(None, max_length=255)
    size: Optional[int] = Field(None, ge=0) # Size in bytes, must be non-negative
    download_url: Optional[str] = None
    download_url_expires_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
        
class AttachmentAttributesModel(BaseModel):
    """Represents the attributes of an attachment."""
    model_config = ConfigDict(extra='forbid')
    
    title: Optional[str] = Field(None, max_length=255)
    size: Optional[str] = None
    external_id: Optional[str] = Field(None, max_length=255)
    download_url: Optional[AnyUrl] = None
    download_url_expires_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None

class EventSupplierInput(BaseModel):
    """Pydantic model for validating the 'add suppliers to event' request body."""
    supplier_ids: List[int] = Field(..., description="List of supplier IDs, must be positive integers")
    type: Literal["supplier_companies"]

    model_config = ConfigDict(extra='forbid')
    
    @field_validator("supplier_ids")
    @classmethod
    def validate_supplier_ids(cls, v):
        if not all(supplier_id > 0 for supplier_id in v):
            raise ValueError("All supplier IDs must be positive integers")
        return v

class AttachmentModel(BaseModel):
    """Represents an attachment."""
    model_config = ConfigDict(extra='forbid')

    id: Optional[int] = Field(default=None, ge=0)
    type: Optional[str] = Field(default="attachments")
    name: Optional[str] = Field(default=None)
    uploaded_by: Optional[str] = Field(default=None)
    external_id: Optional[str] = Field(default=None)
    attributes: Optional[AttachmentAttributesModel] = Field(default=None)

class AttachmentInput(BaseModel):
    """Pydantic model for validating a new attachment creation request."""
    model_config = ConfigDict(extra='forbid')
    
    type: Literal["attachments"]
    name: str = Field(..., min_length=1) # Name is required and cannot be empty
    uploaded_by: Optional[str] = None
    external_id: Optional[str] = Field(None, max_length=255)
    attributes: Optional[AttachmentAttributes] = None
    relationships: Optional[AttachmentRelationshipObject] = None

class SupplierContactInput(BaseModel):
    """
    Pydantic model for validating the input to add supplier contacts to an event.
    """
    model_config = ConfigDict(extra='forbid')

    supplier_contact_external_ids: List[str] = Field(
        ..., 
        description="A list of non-empty supplier contact external IDs."
    )
    type: Literal["supplier_contacts"]
    @field_validator("supplier_contact_external_ids")
    @classmethod
    def _validate_ids(cls, v: List[str]) -> List[str]:
        # 1. strip & non-empty
        stripped = [s.strip() for s in v]
        if not all(stripped):
            raise ValueError("All supplier contact external IDs must be non-empty strings after stripping whitespace")
        return stripped

class FieldOptionId(BaseModel):
    """
    Pydantic model for validating field option IDs.
    Field option IDs must be alphanumeric strings that may include hyphens and underscores.
    """
    model_config = ConfigDict(extra='forbid')

    id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', min_length=1, max_length=50)
    
    @classmethod
    def validate(cls, id_value: str) -> bool:
        """
        Validate if the provided ID conforms to the expected format.
        
        Args:
            id_value (str): The ID to validate
            
        Returns:
            bool: True if the ID is valid, False otherwise
        """
        try:
            cls(id=id_value)
            return True
        except ValidationError:
            return False

class ContactTypePatchInput(BaseModel):
    """
    Pydantic model for validating contact type patch operations.
    """
    model_config = ConfigDict(extra='forbid')
    
    id: int = Field(..., gt=0, description="Contact type identifier (must be positive integer)")
    type: Optional[Literal["contact_types"]] = Field(default=None, description="Object type, must be 'contact_types' if provided")
    external_id: Optional[str] = Field(default=None, max_length=255, description="Contact type external identifier (max 255 characters)")
    name: Optional[str] = Field(default=None, max_length=255, description="Contact type name (max 255 characters)")

class FieldIdModel(BaseModel):
    """Pydantic model for validating field IDs.
    
    Attributes:
        field_id (str): A non-empty string representing the field identifier.
            Must follow the expected format for field identifiers.
    """
    field_id: str = Field(
        ...,
        description="A unique identifier for a field.",
        max_length=100,
        strip_whitespace=True
    )
    
    @field_validator('field_id')
    @classmethod
    def validate_field_id_format(cls, v):
        """Validate that field_id follows the expected format.
        
        Typically, field IDs should be alphanumeric with possible underscores
        or dashes. This validator ensures that field_id follows this pattern.
        """
        if not isinstance(v, str):
            raise ValueError("field_id must be a string")
            
        if not v:
            raise ValueError("field_id cannot be empty")
            
        # Field ID should consist of alphanumeric characters, underscores, or dashes
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                "field_id must contain only alphanumeric characters, underscores, or dashes"
            )
            
        return v

class FieldOptionItem(BaseModel):
    """Pydantic model for validating individual field option items."""
    model_config = ConfigDict(extra='forbid')

    value: str = Field(..., min_length=1, description="Option value must not be empty")
    label: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = False

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        """Validate value is not just whitespace."""
        if v.strip() == "":
            raise ValueError("Option value cannot be empty or only whitespace")
        return v

class FieldOptionsModel(BaseModel):
    """Pydantic model for validating field options input."""
    model_config = ConfigDict(extra='forbid')

    field_id: str = Field(..., min_length=1, description="Field ID must not be empty")
    options: Optional[List[str]] = Field(
        default=None,
        description="List of string option values"
    )

    @field_validator('field_id')
    @classmethod
    def validate_field_id(cls, v):
        """Validate field_id is a valid string."""
        if not isinstance(v, str):
            raise ValueError("Field ID must be a string")
        if v.strip() == "":
            raise ValueError("Field ID cannot be empty or only whitespace")
        return v



# Define allowed states for project state filtering
ALLOWED_PROJECT_STATES = {
    "draft", "requested", "planned", "active", "completed", "canceled", "on_hold"
}
class ProjectFilterModel(BaseModel):
    # Timestamps
    updated_at_from: Optional[datetime] = None
    updated_at_to: Optional[datetime] = None
    marked_as_needs_attention_at_from: Optional[datetime] = None
    marked_as_needs_attention_at_to: Optional[datetime] = None

    # Numeric fields
    number_from: Optional[int] = Field(default=None, ge=0)
    number_to: Optional[int] = Field(default=None, ge=0)

    # String contains/not_contains fields
    title_contains: Optional[str] = None
    title_not_contains: Optional[str] = None
    description_contains: Optional[str] = None
    description_not_contains: Optional[str] = None
    canceled_note_contains: Optional[str] = None
    canceled_note_not_contains: Optional[str] = None
    canceled_reason_contains: Optional[str] = None
    canceled_reason_not_contains: Optional[str] = None
    on_hold_note_contains: Optional[str] = None
    on_hold_note_not_contains: Optional[str] = None
    on_hold_reason_contains: Optional[str] = None
    on_hold_reason_not_contains: Optional[str] = None
    needs_attention_note_contains: Optional[str] = None
    needs_attention_note_not_contains: Optional[str] = None
    needs_attention_reason_contains: Optional[str] = None
    needs_attention_reason_not_contains: Optional[str] = None
    
    # External ID fields
    external_id_empty: Optional[bool] = None
    external_id_not_empty: Optional[bool] = None
    external_id_equals: Optional[str] = None
    external_id_not_equals: Optional[str] = None
    external_id: Optional[str] = None

    # Date fields
    actual_start_date_from: Optional[date] = None
    actual_start_date_to: Optional[date] = None
    actual_end_date_from: Optional[date] = None
    actual_end_date_to: Optional[date] = None
    target_start_date_from: Optional[date] = None
    target_start_date_to: Optional[date] = None
    target_end_date_from: Optional[date] = None
    target_end_date_to: Optional[date] = None

    # Amount fields (float)
    actual_spend_amount_from: Optional[float] = Field(default=None, ge=0)
    actual_spend_amount_to: Optional[float] = Field(default=None, ge=0)
    approved_spend_amount_from: Optional[float] = Field(default=None, ge=0)
    approved_spend_amount_to: Optional[float] = Field(default=None, ge=0)
    estimated_savings_amount_from: Optional[float] = Field(default=None) # Savings can be negative
    estimated_savings_amount_to: Optional[float] = Field(default=None)   # Savings can be negative
    estimated_spend_amount_from: Optional[float] = Field(default=None, ge=0)
    estimated_spend_amount_to: Optional[float] = Field(default=None, ge=0)

    # Boolean-like flags (assumed to be boolean despite (str) in original doc for some)
    canceled_note_empty: Optional[bool] = None
    canceled_note_not_empty: Optional[bool] = None
    canceled_reason_empty: Optional[bool] = None
    canceled_reason_not_empty: Optional[bool] = None
    on_hold_note_empty: Optional[bool] = None
    on_hold_note_not_empty: Optional[bool] = None
    on_hold_reason_empty: Optional[bool] = None
    on_hold_reason_not_empty: Optional[bool] = None
    needs_attention_note_empty: Optional[bool] = None
    needs_attention_note_not_empty: Optional[bool] = None
    needs_attention_reason_empty: Optional[bool] = None
    needs_attention_reason_not_empty: Optional[bool] = None
    
    needs_attention_equals: Optional[bool] = None
    needs_attention_not_equals: Optional[bool] = None # Potentially redundant with needs_attention_equals

    # List of strings for state
    state_equals: Optional[List[str]] = None

    @field_validator("state_equals")
    @classmethod
    def check_state_value(cls, v: List[str]) -> List[str]:
        if v is not None:
            for state in v:
                if state not in ALLOWED_PROJECT_STATES:
                    raise ValueError(f"State '{state}' is not a valid project state. Allowed states are: {ALLOWED_PROJECT_STATES}")
        return v

    model_config = ConfigDict(extra="forbid")  # Disallow any fields not defined in the model

class PageArgumentModel(BaseModel):
    model_config = ConfigDict(extra="forbid") # Disallow other keys like "offset"
    
    size: Optional[int] = Field(default=None, gt=0, le=100) # Must be > 0 and <= 100


class ProjectAttributesInputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Optional[str] = None
    description: Optional[str] = None
    state: Optional[Literal["draft", "requested", "planned", "active", "completed", "canceled", "on_hold"]] = None
    target_start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    actual_spend_amount: Optional[float] = None
    approved_spend_amount: Optional[float] = None
    estimated_savings_amount: Optional[float] = None
    estimated_spend_amount: Optional[float] = None
    canceled_note: Optional[str] = None
    canceled_reason: Optional[str] = None
    on_hold_note: Optional[str] = None
    on_hold_reason: Optional[str] = None
    needs_attention: Optional[bool] = None
    marked_as_needs_attention_at: Optional[datetime] = None
    needs_attention_note: Optional[str] = None
    needs_attention_reason: Optional[str] = None

class ProjectRelationshipsInputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    attachments: Optional[List[Dict[str, Any]]] = None
    creator: Optional[Dict[str, Any]] = None
    requester: Optional[Dict[str, Any]] = None
    owner: Optional[Dict[str, Any]] = None
    project_type: Optional[Dict[str, Any]] = None

class ProjectDataInputModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    type_id: Optional[str] = None
    id: str  # Project identifier string, to be compared with the path `id`
    external_id: Optional[str] = None
    supplier_companies: Optional[List[Dict[str, Any]]] = None
    supplier_contacts: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    attributes: Optional[ProjectAttributesInputModel] = None
    relationships: Optional[ProjectRelationshipsInputModel] = None


class ProjectIdModel(BaseModel):
    """Pydantic model for validating project ID parameters."""
    model_config = ConfigDict(extra='forbid')
    id: int = Field(gt=0)  # Project ID must be a positive integer (greater than 0)

class BidIdModel(BaseModel):
    """Pydantic model for validating bid ID parameters with comprehensive validation."""
    model_config = ConfigDict(extra='forbid')
    
    id: int = Field(
        ..., 
        gt=0, 
        le=999999999,  # Reasonable upper limit for bid IDs
        description="Bid ID must be a positive integer between 1 and 999,999,999"
    )
    
    @field_validator('id')
    @classmethod
    def validate_bid_id(cls, v: int) -> int:
        """Enhanced validation for bid ID with detailed error messages."""
        if not isinstance(v, int):
            raise ValueError(f"Bid ID must be an integer, got {type(v).__name__}")
        
        if v <= 0:
            raise ValueError(f"Bid ID must be a positive integer (greater than 0), got {v}")
        
        if v > 999999999:
            raise ValueError(f"Bid ID must be less than or equal to 999,999,999, got {v}")
        
        return v

class BidIncludeModel(BaseModel):
    """Pydantic model for validating _include parameter with comprehensive validation."""
    model_config = ConfigDict(extra='forbid')
    
    include: Optional[str] = Field(
        default=None,
        max_length=500,  # Reasonable limit for include string
        description="Comma-separated string of related resources to include"
    )
    
    # Define valid include options based on the docstring
    VALID_INCLUDE_OPTIONS: ClassVar[set[str]] = {
        'event', 'supplier_company', 'supplier_companies', 'events'
    }
    
    @field_validator('include')
    @classmethod
    def validate_include_parameter(cls, v: Optional[str]) -> Optional[str]:
        """Enhanced validation for _include parameter with detailed error messages."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError(f"_include parameter must be a string or None, got {type(v).__name__}")
        
        # Check for empty or whitespace-only strings
        if not v.strip():
            raise ValueError("_include parameter cannot be empty or contain only whitespace")
        
        # Check length limit
        if len(v) > 500:
            raise ValueError(f"_include parameter is too long (max 500 characters), got {len(v)} characters")
        
        # Validate individual include options
        include_options = [option.strip().lower() for option in v.split(',') if option.strip()]
        
        for option in include_options:
            if option not in cls.VALID_INCLUDE_OPTIONS:
                raise ValueError(
                    f"Invalid include option '{option}'. Valid options are: {', '.join(sorted(cls.VALID_INCLUDE_OPTIONS))}"
                )
        
        # Check for duplicate options
        if len(include_options) != len(set(include_options)):
            raise ValueError("_include parameter contains duplicate options")
        
        return v

class ContractTypeUpdate(BaseModel):
    """Model for contract type updates"""
    model_config = ConfigDict(extra='forbid')
    
    id: int = Field(..., gt=0, description="Contract type identifier, must be a positive integer")
    type: str = Field(..., description="Object type, should always be 'contract_types'")
    name: Optional[str] = None
    external_id: Optional[str] = None
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v != "contract_types":
            raise ValueError("type must be 'contract_types'")
        return v
    
class PaginationModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    size: Optional[int] = Field(default=None, ge=1, le=100, description="Value must be between 1 and 100, inclusive. Optional.")

class LineItemCellData(BaseModel):
    data_identifier: str
    value: Any

class LineItemAttributesInput(BaseModel):
    data: Dict[str, LineItemCellData]

class WorksheetRelationshipData(BaseModel):
    type: Literal["worksheets"]
    id: conint(gt=0)

class LineItemRelationshipsInput(BaseModel):
    worksheet: WorksheetRelationshipData

class SupplierContactData(BaseModel):
    """Pydantic model for validating supplier contact data"""
    model_config = ConfigDict(extra='forbid')

    supplier_contact_ids: List[int] = Field(..., description="List of supplier contact IDs to be added to the event")
    type: str = Field(..., description="Object type, should always be 'supplier_contacts'")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v != "supplier_contacts":
            raise ValueError(f"'type' must be 'supplier_contacts', got '{v}'")
        return v

SpendCategoryUsageLiteral = Literal["procurement", "expense", "ad_hoc_payment", "supplier_invoice"]

class SpendCategoryUpdateModel(BaseModel):
    """Pydantic model for validating spend category update data."""
    model_config = ConfigDict(extra='forbid')

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    new_external_id: Optional[str] = Field(default=None, min_length=1, max_length=255)
    usages: Optional[List[SpendCategoryUsageLiteral]] = Field(default=None, min_length=1)

class ContractReportEntry(BaseModel):
    id: str
    contract_id: str
    summary: str

class ContractTypeCreateModel(BaseModel):
    """
    Defines the data required to CREATE a contract type.
    Pydantic automatically validates this structure.
    """
    # The '...' means the field is required.
    # We add validation rules directly to the fields.
    name: str = Field(..., min_length=1, description="The name of the contract type.")
    
    # The pattern ensures the 'type' field can only be "contract_types".
    type: str = Field(..., pattern="^contract_types$", description="The object type, must be 'contract_types'.")
    
    # This field is optional and can be None.
    external_id: Optional[str] = None


class ContractTypeResponseModel(ContractTypeCreateModel):
    """
    Defines the final object structure that is RETURNED to the user.
    It includes all fields from the creation model, plus the generated ID.
    """
    id: int

# Contract Models
class ContractAttributesInputModel(BaseModel):
    title: str = Field(..., max_length=255, description="Contract title (max 255 characters)")
    description: Optional[str] = None
    state: Literal["draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated"]
    state_label: Optional[str] = None
    external_id: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    actual_spend_amount: Optional[float] = None
    auto_renewal: Optional[Literal["yes", "no", "evergreen"]] = None
    marked_as_needs_attention_at: Optional[str] = None
    needs_attention: Optional[bool] = None
    needs_attention_note: Optional[str] = None
    needs_attention_reason: Optional[str] = None
    renew_number_of_times: Optional[int] = None
    renewal_term_unit: Optional[Literal["days", "weeks", "months", "years"]] = None
    renewal_term_value: Optional[int] = None
    renewal_termination_notice_unit: Optional[Literal["days", "weeks", "months", "years"]] = None
    renewal_termination_notice_value: Optional[int] = None
    renewal_termination_reminder_unit: Optional[Literal["days", "weeks", "months", "years"]] = None
    renewal_termination_reminder_value: Optional[int] = None
    terminated_note: Optional[str] = None
    terminated_reason: Optional[str] = None
    custom_fields: Optional[List[Any]] = None
    approval_rounds: Optional[int] = None
    public: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')

class ContractRelationshipReference(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    type: str
    id: int

class ContractRelationshipsInputModel(BaseModel):
    owner: Optional[ContractRelationshipReference] = None
    supplier_company: Optional[ContractRelationshipReference] = None
    contract_type: Optional[ContractRelationshipReference] = None
    spend_category: Optional[ContractRelationshipReference] = None
    payment_currency: Optional[ContractRelationshipReference] = None

    model_config = ConfigDict(extra='forbid')

class ContractInputModel(BaseModel):
    type: str = Field(default="contracts", description="Contract type")
    supplier_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    external_id: Optional[str] = None
    attributes: Optional[ContractAttributesInputModel] = None
    relationships: Optional[ContractRelationshipsInputModel] = None

    model_config = ConfigDict(extra='allow')

# Define allowed states for contract state filtering
ALLOWED_CONTRACT_STATES = {
    "draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated"
}

# Define allowed auto-renewal modes
ALLOWED_AUTO_RENEWAL_MODES = {"yes", "no", "evergreen"}

class ContractFilterModel(BaseModel):
    """Pydantic model for validating contract filter parameters"""
    model_config = ConfigDict(extra='allow')
    
    # Timestamps
    updated_at_from: Optional[str] = None
    updated_at_to: Optional[str] = None
    marked_as_needs_attention_at_from: Optional[str] = None
    marked_as_needs_attention_at_to: Optional[str] = None
    
    # Numeric fields
    number_from: Optional[str] = None
    number_to: Optional[str] = None
    renew_number_of_times_from: Optional[int] = Field(default=None, ge=0)
    renew_number_of_times_to: Optional[int] = Field(default=None, ge=0)
    contract_type_id_equals: Optional[int] = Field(default=None, gt=0)
    contract_type_id_not_equals: Optional[int] = Field(default=None, gt=0)
    
    # String contains/not_contains fields
    title_contains: Optional[str] = None
    title_not_contains: Optional[str] = None
    description_contains: Optional[str] = None
    description_not_contains: Optional[str] = None
    terminated_note_contains: Optional[str] = None
    terminated_note_not_contains: Optional[str] = None
    terminated_reason_contains: Optional[str] = None
    terminated_reason_not_contains: Optional[str] = None
    needs_attention_note_contains: Optional[str] = None
    needs_attention_note_not_contains: Optional[str] = None
    needs_attention_reason_contains: Optional[str] = None
    needs_attention_reason_not_contains: Optional[str] = None
    
    # External ID fields
    external_id_empty: Optional[bool] = None
    external_id_not_empty: Optional[bool] = None
    external_id_equals: Optional[str] = None
    external_id_not_equals: Optional[str] = None
    
    # Date fields
    actual_start_date_from: Optional[str] = None
    actual_start_date_to: Optional[str] = None
    actual_end_date_from: Optional[str] = None
    actual_end_date_to: Optional[str] = None
    renewal_termination_notice_date_from: Optional[str] = None
    renewal_termination_notice_date_to: Optional[str] = None
    renewal_termination_reminder_date_from: Optional[str] = None
    renewal_termination_reminder_date_to: Optional[str] = None
    
    # Amount fields
    actual_spend_amount_from: Optional[float] = Field(default=None, ge=0)
    actual_spend_amount_to: Optional[float] = Field(default=None, ge=0)
    
    # Boolean fields
    needs_attention_equals: Optional[bool] = None
    needs_attention_not_equals: Optional[bool] = None
    terminated_note_empty: Optional[str] = None
    terminated_note_not_empty: Optional[str] = None
    terminated_reason_empty: Optional[str] = None
    terminated_reason_not_empty: Optional[str] = None
    needs_attention_note_empty: Optional[str] = None
    needs_attention_note_not_empty: Optional[str] = None
    needs_attention_reason_empty: Optional[str] = None
    needs_attention_reason_not_empty: Optional[str] = None
    
    # List fields
    auto_renewal: Optional[List[str]] = None
    state_equals: Optional[List[str]] = None
    spend_category_id_equals: Optional[List[int]] = Field(default=None)
    
    @field_validator("state_equals")
    @classmethod
    def check_state_value(cls, v: List[str]) -> List[str]:
        if v is not None:
            for state in v:
                if state not in ALLOWED_CONTRACT_STATES:
                    raise ValueError(f"State '{state}' is not a valid contract state. Allowed states are: {ALLOWED_CONTRACT_STATES}")
        return v
    
    @field_validator("auto_renewal")
    @classmethod
    def check_auto_renewal_value(cls, v: List[str]) -> List[str]:
        if v is not None:
            for mode in v:
                if mode not in ALLOWED_AUTO_RENEWAL_MODES:
                    raise ValueError(f"Auto-renewal mode '{mode}' is not valid. Allowed modes are: {ALLOWED_AUTO_RENEWAL_MODES}")
        return v
    
    @field_validator("spend_category_id_equals")
    @classmethod
    def check_spend_category_ids(cls, v: List[int]) -> List[int]:
        if v is not None:
            for category_id in v:
                if category_id <= 0:
                    raise ValueError(f"Spend category ID must be a positive integer, got {category_id}")
        return v
      
class ContractPageModel(BaseModel):
    """Pydantic model for validating contract pagination parameters"""
    model_config = ConfigDict(extra='forbid')
    size: Optional[int] = Field(default=10, gt=0, le=100, description="Number of results per page (default: 10, max: 100)")

class ExternalIdValidator(BaseModel):
    external_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="External ID must be a non-empty string up to 255 characters."
    )
    size: Optional[int] = Field(default=None, ge=1, le=100, description="Value must be between 1 and 100, inclusive. Optional.")

class EventIdModel(BaseModel):
    id: int = Field(..., gt=0)
    
# EventBids models for input validation
class EventBidPaginationModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    size: Optional[int] = Field(
        default=PaginationConstants.DEFAULT_PAGE_SIZE,
        ge=PaginationConstants.MIN_PAGE_SIZE,
        le=PaginationConstants.MAX_PAGE_SIZE,
        description="Number of results per page (1-100)"
    )

class EventBidFilterModel(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    id_equals: Optional[int] = None
    intend_to_bid_equals: Optional[bool] = None
    intend_to_bid_not_equals: Optional[bool] = None
    intend_to_bid_answered_at_from: Optional[str] = None
    intend_to_bid_answered_at_to: Optional[str] = None
    submitted_at_from: Optional[str] = None
    submitted_at_to: Optional[str] = None
    resubmitted_at_from: Optional[str] = None
    resubmitted_at_to: Optional[str] = None
    status_equals: Optional[List[str]] = None
    supplier_company_id_equals: Optional[int] = None
    supplier_company_external_id_equals: Optional[str] = None
    
    @field_validator('status_equals')
    @classmethod
    def validate_status_equals(cls, v):
        if v is not None:
            for status in v:
                if status not in [s.value for s in BidStatus]:
                    raise ValueError(f"Invalid status: {status}. Valid statuses: {[s.value for s in BidStatus]}")
        return v
    
    @field_validator('intend_to_bid_answered_at_from', 'intend_to_bid_answered_at_to', 
                    'submitted_at_from', 'submitted_at_to',
                    'resubmitted_at_from', 'resubmitted_at_to')
    @classmethod
    def validate_timestamp(cls, v):
        if v is not None:
            # Simple validation that it's a properly formatted ISO timestamp
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}. Expected ISO format.")
        return v

class EventBidIncludeModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    include_resources: List[IncludeResource] = Field(default_factory=list)
    
    @classmethod
    def from_include_string(cls, include_str: Optional[str]) -> 'EventBidIncludeModel':
        """Create an include model from a comma-separated include string."""
        if not include_str:
            return cls()
        
        resources = []
        for item in include_str.split(','):
            item = item.strip()
            try:
                resources.append(IncludeResource(item))
            except ValueError:
                valid_values = [e.value for e in IncludeResource]
                raise ValueError(f"Invalid include resource: {item}. Valid values: {valid_values}")
        
        return cls(include_resources=resources)

class LineItemInput(BaseModel):
    """
    Represents the input structure for a line item.
    """
    type: Literal["line_items"]
    attributes: LineItemAttributesInput
    relationships: LineItemRelationshipsInput
    model_config = ConfigDict(extra='forbid')

class BidLineItemsListGetInput(BaseModel):
    filter: Optional[Dict[str, Any]] = Field(
        None,
        description="Dictionary of allowed filter fields: bid_id (int), status (str), event_id (int). Validation of allowed fields is performed in the function."
    )

# Event response models
class EventResponseAttributes(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    title: str
    event_type: Literal["type1", "type2"]  # Replace with actual EventTypeLiteral
    state: Literal["active", "inactive"]   # Replace with actual EventStateLiteral
    duplication_state: Literal["original", "duplicate"]  # Replace with actual EventDuplicationStateLiteral
    # ... all other attributes
    custom_fields: Optional[List[Any]] = None

class EventResponseRelationships(BaseModel):
    model_config = ConfigDict(extra='forbid')
    attachments: Optional[List[Dict[str, Any]]] = None
    supplier_contacts: Optional[List[Any]] = None

class EventResponseLinks(BaseModel):
    model_config = ConfigDict(extra='forbid')
    self: AnyUrl

class EventResponseModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: int = Field(..., gt=0)
    type: Literal["events"]
    attributes: EventResponseAttributes
    relationships: EventResponseRelationships
    links: EventResponseLinks

# Supplier company update model
class SupplierCompanyUpdateModel(BaseModel):
    """Pydantic model used to validate payloads for updating a supplier company via its external ID.

    The model is intentionally flexible because most update operations are partial updates.
    Only the ``id`` field is strictly required – it **must** equal the ``external_id`` in the URL
    according to the Workday Strategic Sourcing API contract. All other keys are optional to
    support PATCH-semantics (partial updates). Extra keys are allowed so that previously unknown
    fields do **not** cause validation to fail – they will simply be passed through to the
    persistence layer. This mirrors the loose JSON:API patch behaviour while still enforcing
    basic structure and preventing obviously malformed payloads (e.g. ``id`` not being a string).
    """

    # Required fields
    id: str = Field(..., description="Must match the external_id path parameter.")

    # Common optional top-level fields
    type: Optional[str] = Field(
        None,
        description="Resource type – must be 'supplier_companies' if supplied.",
    )
    attributes: Optional[Dict[str, Any]] = Field(
        None,
        description="Dictionary of attributes to update on the supplier company.",
    )
    relationships: Optional[Dict[str, Any]] = Field(
        None,
        description="Dictionary describing relationship updates.",
    )

    # Frequently patched simple keys (e.g. tests send them at the root level)
    name: Optional[str] = Field(
        None, max_length=255, description="Convenience field for simple name update."
    )
 
    model_config = ConfigDict(extra="allow")  # Allow unknown fields so we don't block forward-compat fields 


class SegmentationStatus(str, Enum):
    """Valid segmentation status values."""
    NOT_APPROVED = "not_approved"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    OUT_OF_COMPLIANCE = "out_of_compliance"
    BLACKLISTED = "blacklisted"

class OnboardingStatus(str, Enum):
    """Valid onboarding form completion status values."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class IncludeOptions(str, Enum):
    """Valid include options for related resources."""
    ATTACHMENTS = "attachments"
    SUPPLIER_CATEGORY = "supplier_category"
    SUPPLIER_GROUPS = "supplier_groups"
    DEFAULT_PAYMENT_TERM = "default_payment_term"
    PAYMENT_TYPES = "payment_types"
    DEFAULT_PAYMENT_TYPE = "default_payment_type"
    PAYMENT_CURRENCIES = "payment_currencies"
    DEFAULT_PAYMENT_CURRENCY = "default_payment_currency"
    SUPPLIER_CLASSIFICATION_VALUES = "supplier_classification_values"

class CustomField(BaseModel):
    """Model for custom field data."""
    name: str = Field(..., description="Field name")
    value: Any = Field(..., description="Field value")

class SupplierCompanyCreate(BaseModel):
    """Model for creating a new supplier company."""
    name: str = Field(..., min_length=1, max_length=255, description="Supplier company name")
    description: Optional[str] = Field(None, max_length=1000, description="Company description")
    is_suggested: Optional[bool] = Field(False, description="True if user-suggested, not yet approved")
    public: Optional[bool] = Field(False, description="True if publicly listed")
    risk: Optional[str] = Field(None, max_length=100, description="Risk slug from predefined values")
    segmentation: Optional[str] = Field(None, max_length=100, description="Segmentation slug")
    segmentation_status: Optional[SegmentationStatus] = Field(None, description="Segmentation status")
    segmentation_notes: Optional[str] = Field(None, max_length=1000, description="Notes related to segmentation")
    tags: Optional[List[str]] = Field(None, description="Tags associated with the supplier")
    url: Optional[str] = Field(None, max_length=500, description="Website URL")
    duns_number: Optional[str] = Field(None, max_length=20, description="D-U-N-S® identifier")
    external_id: Optional[str] = Field(None, max_length=100, description="External system identifier")
    self_registered: Optional[bool] = Field(False, description="True if registered by the supplier")
    onboarding_form_completion_status: Optional[OnboardingStatus] = Field(None, description="Onboarding progress")
    accept_all_currencies: Optional[bool] = Field(False, description="True if accepts all currencies")
    custom_fields: Optional[List[CustomField]] = Field(None, description="List of custom fields")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if v is not None and v:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
        return v

    @field_validator('duns_number')
    @classmethod
    def validate_duns_number(cls, v):
        if v is not None and v:
            if not v.isdigit() or len(v) != 9:
                raise ValueError('D-U-N-S number must be exactly 9 digits')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError('Maximum 50 tags allowed')
            for tag in v:
                if len(tag) > 50:
                    raise ValueError('Each tag must be 50 characters or less')
        return v

class SupplierCompanyResponse(BaseModel):
    """Model for supplier company response."""
    id: int = Field(..., description="Supplier company ID")
    type: str = Field("supplier_companies", description="Resource type")
    attributes: Dict[str, Any] = Field(..., description="Core attributes of the company")
    relationships: Optional[Dict[str, Any]] = Field(None, description="Related entities")

class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str = Field(..., description="Error message") 

class PatchOperationModel(BaseModel):
    """SCIM PATCH operation model for individual patch operations."""
    op: Literal["add", "remove", "replace"] = Field(..., description="The kind of operation to perform")
    path: Optional[str] = Field(None, description="Required when op is remove, optional otherwise")
    value: Optional[Union[str, int, float, bool, Dict[str, Any], List[Any]]] = Field(None, description="Can be any value - string, number, boolean, array or object")

    model_config = ConfigDict(extra='forbid')

    @model_validator(mode='after')
    def validate_remove_requires_path(self):
        """Validate that path is required when op is remove."""
        if self.op == 'remove' and not self.path:
            raise ValueError("path is required when op is 'remove'")
        return self
    
    @model_validator(mode='after')
    def validate_username_email_format(self):
        """Validate that userName values are valid email addresses."""
        if (self.path == 'userName' and 
            self.value is not None and 
            self.op in ['add', 'replace']):
            
            # Ensure value is a string
            if not isinstance(self.value, str):
                raise ValueError("userName value must be a string")
            
            # Validate email format using EmailStr
            try:
                EmailStr._validate(self.value)
            except Exception as e:
                raise ValueError(f"userName must be a valid email address: {str(e)}")
        
        return self

    @model_validator(mode='after')
    def validate_username_email_format(self):
        """Validate that userName values are valid email addresses."""
        if (self.path == 'userName' and 
            self.value is not None and 
            self.op in ['add', 'replace']):

            # Ensure value is a string
            if not isinstance(self.value, str):
                raise ValueError("userName value must be a string")

            # Validate email format using EmailStr
            try:
                EmailStr._validate(self.value)
            except Exception as e:
                raise ValueError(f"userName must be a valid email address: {str(e)}")

        return self


class UserPatchInputModel(BaseModel):
    """Pydantic model for validating SCIM PATCH user request body."""
    schemas: Optional[List[str]] = Field(None, description="Array of strings - SCIM schemas")
    Operations: List[PatchOperationModel] = Field(..., description="Array of objects (PatchOperation) - required")

    model_config = ConfigDict(extra='forbid')


class UserReplaceInputModel(BaseModel):
    """Pydantic model for validating SCIM PUT user request body.
    
    For PUT operations, only provided attributes are replaced. Missing attributes remain unchanged.
    """
    externalId: Optional[str] = Field(default=None, description="External identifier for the user")
    userName: EmailStr = Field(..., description="Unique username, typically an email address")
    name: ScimNameModel = Field(..., description="Required. User's name components")
    active: Optional[bool] = Field(default=None, description="Whether the user account is active")

    model_config = ConfigDict(extra='forbid')
        
    @field_validator('active', mode='before')
    def validate_active(cls, v: Optional[bool]):
        """Validate active field."""
        if v is not None and not isinstance(v, bool):
            raise ValueError("active must be a boolean")
        return v
        
    @field_validator('externalId')
    def validate_external_id(cls, v: Optional[str]):
        """Validate externalId field."""
        if v is not None and not isinstance(v, str):
            raise ValueError("externalId must be a string")
        return v


# =============================================================================
# Database Structure Validation Models
# =============================================================================

class AttachmentsDBModel(BaseModel):
    """Validation model for attachments section of DB"""
    model_config = ConfigDict(extra='allow')  # Allow additional fields for attachments


class AwardsDBModel(BaseModel):
    """Validation model for awards section of DB"""
    award_line_items: List[Any] = Field(default_factory=list)
    awards: List[Any] = Field(default_factory=list)
    model_config = ConfigDict(extra='forbid')


class ContractsDBModel(BaseModel):
    """Validation model for contracts section of DB"""
    award_line_items: List[Any] = Field(default_factory=list)
    awards: Dict[str, Any] = Field(default_factory=dict)
    contract_types: Dict[str, Any] = Field(default_factory=dict)
    contracts: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra='forbid')


class EventsDBModel(BaseModel):
    """Validation model for events section of DB"""
    bid_line_items: Dict[str, Any] = Field(default_factory=dict)
    bids: Dict[str, Any] = Field(default_factory=dict)
    event_templates: Dict[str, Any] = Field(default_factory=dict)
    events: Dict[str, Any] = Field(default_factory=dict)
    line_items: Dict[str, Any] = Field(default_factory=dict)
    worksheets: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra='forbid')


class FieldsDBModel(BaseModel):
    """Validation model for fields section of DB"""
    field_groups: Dict[str, Any] = Field(default_factory=dict)
    field_options: Dict[str, Any] = Field(default_factory=dict)
    fields: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra='forbid')


class PaymentsDBModel(BaseModel):
    """Validation model for payments section of DB"""
    payment_currencies: List[Any] = Field(default_factory=list)
    payment_currency_id_counter: str = ""
    payment_term_id_counter: str = ""
    payment_terms: List[Any] = Field(default_factory=list)
    payment_type_id_counter: str = ""
    payment_types: List[Any] = Field(default_factory=list)
    model_config = ConfigDict(extra='forbid')


class ProjectsDBModel(BaseModel):
    """Validation model for projects section of DB"""
    project_types: Dict[str, Any] = Field(default_factory=dict)
    projects: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra='forbid')


class ReportsDBModel(BaseModel):
    """Validation model for reports section of DB"""
    contract_milestone_reports_entries: List[Any] = Field(default_factory=list)
    contract_milestone_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    contract_reports_entries: List[Any] = Field(default_factory=list)
    contract_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    event_reports: List[Any] = Field(default_factory=list)
    event_reports_1_entries: List[Any] = Field(default_factory=list)
    event_reports_entries: List[Any] = Field(default_factory=list)
    event_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    performance_review_answer_reports_entries: List[Any] = Field(default_factory=list)
    performance_review_answer_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    performance_review_reports_entries: List[Any] = Field(default_factory=list)
    performance_review_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    project_milestone_reports_entries: List[Any] = Field(default_factory=list)
    project_milestone_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    project_reports_1_entries: List[Any] = Field(default_factory=list)
    project_reports_entries: List[Any] = Field(default_factory=list)
    project_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    savings_reports_entries: List[Any] = Field(default_factory=list)
    savings_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    supplier_reports_entries: List[Any] = Field(default_factory=list)
    supplier_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    supplier_review_reports_entries: List[Any] = Field(default_factory=list)
    supplier_review_reports_schema: Dict[str, Any] = Field(default_factory=dict)
    suppliers: List[Any] = Field(default_factory=list)
    model_config = ConfigDict(extra='forbid')


class SCIMDBModel(BaseModel):
    """Validation model for SCIM section of DB"""
    resource_types: List[Any] = Field(default_factory=list)
    schemas: List[Any] = Field(default_factory=list)
    service_provider_config: Dict[str, Any] = Field(default_factory=dict)
    users: List[Any] = Field(default_factory=list)
    model_config = ConfigDict(extra='forbid')


class SuppliersDBModel(BaseModel):
    """Validation model for suppliers section of DB"""
    contact_types: Dict[str, Any] = Field(default_factory=dict)
    supplier_companies: Dict[str, Any] = Field(default_factory=dict)
    supplier_company_segmentations: Dict[str, Any] = Field(default_factory=dict)
    supplier_contacts: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra='forbid')


class WorkdayDBModel(BaseModel):
    """Complete validation model for the entire Workday DB structure"""
    attachments: Dict[str, Any] = Field(default_factory=dict)
    awards: AwardsDBModel = Field(default_factory=AwardsDBModel)
    contracts: ContractsDBModel = Field(default_factory=ContractsDBModel)
    events: EventsDBModel = Field(default_factory=EventsDBModel)
    fields: FieldsDBModel = Field(default_factory=FieldsDBModel)
    payments: PaymentsDBModel = Field(default_factory=PaymentsDBModel)
    projects: ProjectsDBModel = Field(default_factory=ProjectsDBModel)
    reports: ReportsDBModel = Field(default_factory=ReportsDBModel)
    scim: SCIMDBModel = Field(default_factory=SCIMDBModel)
    spend_categories: Dict[str, Any] = Field(default_factory=dict)
    suppliers: SuppliersDBModel = Field(default_factory=SuppliersDBModel)
    model_config = ConfigDict(extra='forbid')


# =============================================================================
# Data Validation Models  
# =============================================================================

class UserValidationModel(BaseModel):
    """Validation model for user data"""
    id: str = Field(..., description="User ID")
    userName: str = Field(..., description="Username/email")
    name: Dict[str, str] = Field(..., description="Name object with givenName and familyName")
    active: bool = Field(default=True, description="Whether user is active")
    externalId: Optional[str] = Field(None, description="External ID")
    schemas: List[str] = Field(default_factory=lambda: ["urn:ietf:params:scim:schemas:core:2.0:User"])
    roles: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Optional[Dict[str, Any]] = Field(None)
    model_config = ConfigDict(extra='forbid')

    @field_validator('name')
    def validate_name_structure(cls, v):
        """Validate that name has required structure"""
        if not isinstance(v, dict):
            raise ValueError("Name must be a dictionary")
        if 'givenName' not in v or 'familyName' not in v:
            raise ValueError("Name must contain givenName and familyName")
        return v

    @field_validator('userName')
    def validate_username(cls, v):
        """Validate username format"""
        if not v or not isinstance(v, str) or '@' not in v:
            raise ValueError("Username must be a valid email address")
        return v


class AttachmentValidationModel(BaseModel):
    """Validation model for attachment data"""
    id: str = Field(..., description="Attachment ID")
    name: str = Field(..., description="Attachment name")
    external_id: Optional[str] = Field(None, description="External ID")
    model_config = ConfigDict(extra='forbid')


class SupplierValidationModel(BaseModel):
    """Validation model for supplier data"""
    name: str = Field(..., description="Supplier name")
    status: str = Field(..., description="Supplier status")
    model_config = ConfigDict(extra='forbid')
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate supplier status values"""
        valid_statuses = ['active', 'inactive', 'pending', 'approved', 'rejected']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class ContractValidationModel(BaseModel):
    """Validation model for contract data"""
    id: str = Field(..., description="Contract ID")
    status: str = Field(..., description="Contract status")
    model_config = ConfigDict(extra='forbid')

    @field_validator('status')
    def validate_status(cls, v):
        """Validate contract status values"""
        valid_statuses = ['draft', 'active', 'expired', 'cancelled', 'pending']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class EventValidationModel(BaseModel):
    """Validation model for event data"""
    name: str = Field(..., description="Event name")
    type: Optional[str] = Field(None, description="Event type")
    model_config = ConfigDict(extra='forbid')
      
class AwardsGetInputModel(BaseModel):
    """Pydantic model for validating Awards.get function input parameters."""
    model_config = ConfigDict(extra='forbid')

    filter_state_equals: Optional[List[str]] = Field(
        default=None,
        description="List of states to filter awards by"
    )
    filter_updated_at_from: Optional[str] = Field(
        default=None,
        description="Return awards updated on or after the specified timestamp"
    )
    filter_updated_at_to: Optional[str] = Field(
        default=None,
        description="Return awards updated on or before the specified timestamp"
    )

    # Valid award states according to the real API
    VALID_AWARD_STATES: ClassVar[set[str]] = {"draft", "confirmed", "awaiting_requisition_sync", "requisition_created"}

    @field_validator('filter_state_equals')
    @classmethod
    def validate_state_equals(cls, v):
        """Validate that all states in filter_state_equals are valid."""
        if v is not None:
            for state in v:
                if state not in cls.VALID_AWARD_STATES:
                    raise ValueError(
                        f"Invalid award state '{state}'. Valid states are: {', '.join(sorted(cls.VALID_AWARD_STATES))}"
                    )
        return v

    @field_validator('filter_updated_at_from', 'filter_updated_at_to')
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format if provided."""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Timestamp must be a string")
            if not v.strip():
                raise ValueError("Timestamp cannot be empty or only whitespace")
            # Simple validation for ISO format timestamp
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}. Expected ISO format.")
        return v 
      
class ExternalIdModel(BaseModel):
    """Pydantic model for validating external_id parameters with comprehensive validation."""
    model_config = ConfigDict(extra='forbid')

    external_id: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="External identifier must be a non-empty string between 1-255 characters"
    )

    @field_validator('external_id')
    @classmethod
    def validate_external_id_format(cls, v: str) -> str:
        """Validate external_id contains only alphanumeric characters, hyphens, and underscores."""
        if not all(c.isalnum() or c in ['-', '_'] for c in v):
            raise ValueError("external_id must contain only alphanumeric characters, hyphens, and underscores")
        return v 

# Contract-related models
ContractStateLiteral = Literal[
    "draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated"
]

AutoRenewalLiteral = Literal["yes", "no", "evergreen"]

RenewalTermUnitLiteral = Literal["days", "weeks", "months", "years"]

class ContractAttributesModel(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Contract title (max 255 characters)")
    description: Optional[str] = None
    state: Optional[ContractStateLiteral] = None
    state_label: Optional[str] = None
    number: Optional[int] = None
    external_id: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    actual_spend_amount: Optional[float] = None
    auto_renewal: Optional[AutoRenewalLiteral] = None
    marked_as_needs_attention_at: Optional[str] = None
    needs_attention: Optional[bool] = None
    needs_attention_note: Optional[str] = None
    needs_attention_reason: Optional[str] = None
    renew_number_of_times: Optional[int] = None
    renewal_term_unit: Optional[RenewalTermUnitLiteral] = None
    renewal_term_value: Optional[int] = None
    renewal_termination_notice_date: Optional[str] = None
    renewal_termination_notice_unit: Optional[RenewalTermUnitLiteral] = None
    renewal_termination_notice_value: Optional[int] = None
    renewal_termination_reminder_date: Optional[str] = None
    renewal_termination_reminder_unit: Optional[RenewalTermUnitLiteral] = None
    renewal_termination_reminder_value: Optional[int] = None
    terminated_note: Optional[str] = None
    terminated_reason: Optional[str] = None
    updated_at: Optional[str] = None
    custom_fields: Optional[List[Any]] = None
    approved_at: Optional[str] = None
    approval_rounds: Optional[int] = None
    first_sent_for_approval_at: Optional[str] = None
    sent_for_approval_at: Optional[str] = None
    public: Optional[bool] = None

    class Config:
        extra = 'forbid'

class ContractRelationshipsModel(BaseModel):
    attachments: Optional[List[Dict[str, Any]]] = None
    supplier_company: Optional[Dict[str, Any]] = None
    creator: Optional[Dict[str, Any]] = None
    owner: Optional[Dict[str, Any]] = None
    docusign_envelopes: Optional[List[Dict[str, Any]]] = None
    adobe_sign_agreements: Optional[List[Dict[str, Any]]] = None
    contract_type: Optional[Dict[str, Any]] = None
    spend_category: Optional[Dict[str, Any]] = None

    class Config:
        extra = 'forbid'

class ContractPatchByExternalIdInputModel(BaseModel):
    type: str = Field(..., description="Object type")
    id: int = Field(..., description="Contract identifier")
    supplier_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    external_id: str = Field(..., description="External contract identifier")
    attributes: Optional[ContractAttributesModel] = None
    relationships: Optional[ContractRelationshipsModel] = None

    class Config:
        extra = 'forbid'
