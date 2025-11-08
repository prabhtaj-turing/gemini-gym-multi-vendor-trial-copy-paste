from typing import Optional, List, Dict, Any 
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from enum import Enum
from confluence.SimulationEngine.custom_errors import MissingCommentAncestorsError

# ==================== ENUMS ====================

class ContentType(str, Enum):
    PAGE = "page"
    BLOGPOST = "blogpost"
    COMMENT = "comment"
    ATTACHMENT = "attachment"

class ContentStatus(str, Enum):
    CURRENT = "current"
    DRAFT = "draft"
    ARCHIVED = "archived"
    TRASHED = "trashed"

class RepresentationType(str, Enum):
    STORAGE = "storage"
    VIEW = "view"
    EXPORT_VIEW = "export_view"
    STYLED_VIEW = "styled_view"
    EDITOR = "editor"

# ==================== BASE MODELS ====================

class VersionModel(BaseModel):
    number: int = 1
    minorEdit: bool = False

class SpaceInputModel(BaseModel):
    """
    Pydantic model for the 'space' object within the update body.
    """
    key: str

    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        if not v or not v.strip():
            raise ValueError("key cannot be empty or whitespace-only")
        return v.strip()

# ==================== BODY-RELATED MODELS ====================

class StorageModel(BaseModel):
    value: str
    representation: RepresentationType = RepresentationType.STORAGE

class ContentBodyPayloadModel(BaseModel):
    """For the nested 'body' key's structure"""
    storage: StorageModel

# ==================== CONTENT MODELS ====================

class UpdateContentBodyInputModel(BaseModel):
    """
    Pydantic model for the 'body' argument of the update_content function.
    """
    title: Optional[str] = Field(None, description="Content title")
    status: Optional[str] = Field(None, description="Content status")
    # The 'body' field within the input 'body' dictionary
    body: Optional[ContentBodyPayloadModel] = Field(None, description="Content body data")
    spaceKey: Optional[str] = Field(None, description="Space key")
    ancestors: Optional[List[str]] = Field(None, description="List of ancestor content IDs")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace-only")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["current", "archived", "draft", "trashed"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator('spaceKey')
    @classmethod
    def validate_space_key(cls, v):
        if v is not None and not v.strip():
            raise ValueError("spaceKey cannot be empty or whitespace-only")
        return v.strip() if v else v

    @field_validator('ancestors')
    @classmethod
    def validate_ancestors(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Ancestors must be a list")
            for ancestor_id in v:
                if not isinstance(ancestor_id, str) or not ancestor_id.strip():
                    raise ValueError("Each ancestor ID must be a non-empty string")
        return v

    class Config:
        extra = 'allow' # Allow other fields not defined, as original func might use them

class ContentInputModel(BaseModel):
    type: ContentType
    title: str
    spaceKey: str
    status: ContentStatus = ContentStatus.CURRENT
    version: VersionModel = Field(default_factory=VersionModel)
    # Using alias to map the input key "body" to this field "body_payload"
    # to avoid confusion with the main argument `body` of the function.
    body: Optional[ContentBodyPayloadModel] = Field(default=None, alias="body")
    createdBy: str = "unknown"
    postingDay: Optional[str] = Field(default=None)  # Pattern validation moved to model_validator
    ancestors: Optional[List[str]] = None  # List of parent IDs (strings)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace-only")
        return v.strip()

    @computed_field
    @property
    def effective_space_key(self) -> str:
        """Return the spaceKey value."""
        return self.spaceKey

    @field_validator('spaceKey')
    @classmethod
    def validate_space_key(cls, v):
        if not v or not v.strip():
            raise ValueError("spaceKey cannot be empty or whitespace-only")
        return v.strip()

    @field_validator('ancestors')
    @classmethod
    def validate_ancestors(cls, v):
        # Only validate that ancestors is a list at this stage
        # Content-type specific validation (non-empty strings) is done in model_validator
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Ancestors must be a list")
            # Filter out empty strings for non-comment types (will be ignored anyway)
            # For comments, empty string validation happens in model_validator
        return v

    @model_validator(mode='after')
    def validate_content_type_specific_fields(self) -> 'ContentInputModel':
        """Validate fields based on content type."""
        import re
        
        # Validate postingDay for blogpost type
        if self.type == ContentType.BLOGPOST:
            # postingDay is required for blogpost
            if not self.postingDay or not self.postingDay.strip():
                raise ValueError("postingDay is required for blogpost type")
            # Validate format
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', self.postingDay):
                raise ValueError("postingDay must be in YYYY-MM-DD format for blogpost type")
        else:
            # For non-blogpost types, ignore postingDay even if provided
            # (it will be stored but not used)
            pass
        
        # Validate ancestors for comment type
        if self.type == ContentType.COMMENT:
            if not self.ancestors or len(self.ancestors) == 0:
                raise MissingCommentAncestorsError(
                    "For content type 'comment', the 'ancestors' field (a list of parent IDs) is required and cannot be empty."
                )
            # Validate that each ancestor ID is a non-empty string for comments
            for ancestor_id in self.ancestors:
                if not isinstance(ancestor_id, str) or not ancestor_id.strip():
                    raise ValueError("Each ancestor ID must be a non-empty string for comment type")
        else:
            # For non-comment types, ancestors are ignored (as documented)
            # No validation needed - they will be ignored in the create_content logic
            pass
        
        return self

    class Config:
        model_config = {
            "populate_by_name": True
        }

# ==================== SPACE MODELS ====================

class SpaceBodyInputModel(BaseModel):
    """
    Pydantic model for validating the 'body' argument of the create_space function.
    - 'name' is required (string)
    - 'key' is required if 'alias' is not provided (string) 
    - 'alias' is optional (string) - used as identifier in Confluence page URLs
    - 'description' is optional (string)
    """
    name: str = Field(..., description="The name of the space (required)")
    key: Optional[str] = Field(None, description="The key of the space (required if alias is not provided)")
    alias: Optional[str] = Field(None, description="The alias of the space (used as identifier in URLs)")
    description: Optional[str] = Field(None, description="The description of the space")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name is required and cannot be empty or whitespace-only")
        return v.strip()

    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Key cannot be empty or whitespace-only if provided")
        return v.strip() if v else None

    @field_validator('alias')
    @classmethod
    def validate_alias(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Alias cannot be empty or whitespace-only if provided")
        return v.strip() if v else None

    @model_validator(mode='after')
    def validate_key_or_alias_required(self):
        """Validate that either key or alias is provided."""
        if not self.key and not self.alias:
            raise ValueError("Either 'key' or 'alias' must be provided")
        return self

    class Config:
        extra = 'forbid'  # Don't allow additional fields not defined in the model
