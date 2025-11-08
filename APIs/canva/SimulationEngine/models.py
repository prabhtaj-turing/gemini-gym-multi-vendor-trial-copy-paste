from typing import Optional, Literal, Dict, List, Any
from pydantic import BaseModel, Field

CANVA_DESIGN_ID_PATTERN = r"^[a-zA-Z0-9]{11}$"

class DesignTypeInputModel(BaseModel):
    """
    Pydantic model for validating the 'design_type' dictionary.
    Accepts the format {"type": "preset", "name": "doc"} where:
    - type: The category of design creation method (currently only 'preset' is supported)
    - name: The specific preset template category (e.g., 'doc', 'presentation', 'social')
    Both fields are optional, allowing 'design_type' to be an empty dictionary ({}).
    """
    type: Optional[Literal['preset']] = None
    name: Optional[
        Literal[
            'doc', 
            'whiteboard', 
            'presentation', 
        ]
    ] = None
    
    class Config:
        extra = "forbid"  # Reject any extra fields not defined in the model


# --- Database Validation Models ---

class CanvaBaseModel(BaseModel):
    """Base model with common validation logic for Canva entities."""

    class Config:
        # Forbid extra fields to ensure strict validation
        extra = "forbid"
        # Validate assignment to catch errors early
        validate_assignment = True


# --- User Models ---

class UserProfileModel(CanvaBaseModel):
    """User profile information."""
    display_name: str = Field("", description="User's display name")


class UserModel(CanvaBaseModel):
    """Complete user model."""
    user_id: str = Field("", description="User ID")
    team_id: str = Field("", description="Team ID")
    profile: UserProfileModel = Field(default_factory=UserProfileModel)


# --- Design Models ---

class DesignTypeModel(CanvaBaseModel):
    """Design type information."""
    type: Optional[str] = Field(None, description="Design type")
    name: Optional[str] = Field(None, description="Design name")


class OwnerModel(CanvaBaseModel):
    """Owner information."""
    user_id: str = Field("", description="Owner user ID")
    team_id: str = Field("", description="Owner team ID")


class ThumbnailModel(CanvaBaseModel):
    """Thumbnail information."""
    width: int = Field(0, description="Thumbnail width")
    height: int = Field(0, description="Thumbnail height")
    url: str = Field("", description="Thumbnail URL")


class UrlsModel(CanvaBaseModel):
    """URL information."""
    edit_url: str = Field("", description="Edit URL")
    view_url: str = Field("", description="View URL")


class PageModel(CanvaBaseModel):
    """Page information."""
    index: int = Field(0, description="Page index")
    thumbnail: ThumbnailModel = Field(default_factory=ThumbnailModel)


class MentionUserModel(CanvaBaseModel):
    """User information within mentions."""
    user_id: str = Field("", description="User ID")
    team_id: str = Field("", description="Team ID")
    display_name: str = Field("", description="Display name")


class MentionModel(CanvaBaseModel):
    """Mention information."""
    tag: str = Field("", description="Mention tag")
    user: MentionUserModel = Field(default_factory=MentionUserModel)


class ContentModel(CanvaBaseModel):
    """Content information."""
    plaintext: str = Field("", description="Plain text content")
    markdown: str = Field("", description="Markdown content")


class AuthorModel(CanvaBaseModel):
    """Author information."""
    id: str = Field("", description="Author ID")
    display_name: str = Field("", description="Author display name")


class AssigneeModel(CanvaBaseModel):
    """Assignee information."""
    id: str = Field("", description="Assignee ID")
    display_name: str = Field("", description="Assignee display name")


class ThreadTypeModel(CanvaBaseModel):
    """Thread type information."""
    type: str = Field("", description="Thread type")
    content: ContentModel = Field(default_factory=ContentModel)
    mentions: Dict[str, MentionModel] = Field(default_factory=dict)
    assignee: AssigneeModel = Field(default_factory=AssigneeModel)
    resolver: AssigneeModel = Field(default_factory=AssigneeModel)


class ReplyModel(CanvaBaseModel):
    """Comment reply model."""
    id: str = Field("", description="Reply ID")
    design_id: str = Field("", description="Design ID")
    thread_id: str = Field("", description="Thread ID")
    author: AuthorModel = Field(default_factory=AuthorModel)
    content: ContentModel = Field(default_factory=ContentModel)
    mentions: Dict[str, MentionModel] = Field(default_factory=dict)
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Update timestamp")


class CommentThreadModel(CanvaBaseModel):
    """Comment thread model."""
    id: str = Field("", description="Thread ID")
    design_id: str = Field("", description="Design ID")
    thread_type: ThreadTypeModel = Field(default_factory=ThreadTypeModel)
    author: AuthorModel = Field(default_factory=AuthorModel)
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Update timestamp")
    replies: Dict[str, ReplyModel] = Field(default_factory=dict)


class CommentsModel(CanvaBaseModel):
    """Comments container model."""
    threads: Dict[str, CommentThreadModel] = Field(default_factory=dict)


class DesignModel(CanvaBaseModel):
    """Complete design model."""
    id: str = Field('', description="Design ID (11 characters, alphanumeric)", min_length=11, max_length=11, pattern=CANVA_DESIGN_ID_PATTERN)
    title: str = Field("", description="Design title")
    design_type: DesignTypeModel = Field(default_factory=DesignTypeModel)
    owner: OwnerModel = Field(default_factory=OwnerModel)
    thumbnail: ThumbnailModel = Field(default_factory=ThumbnailModel)
    urls: UrlsModel = Field(default_factory=UrlsModel)
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Update timestamp")
    page_count: int = Field(0, description="Number of pages")
    pages: Dict[str, PageModel] = Field(default_factory=dict)
    comments: CommentsModel = Field(default_factory=CommentsModel)
    asset_id: Optional[str] = Field(None, description="Asset ID")

    class Config:
        extra = "forbid"


# --- Brand Template Models ---

class BrandTemplateModel(CanvaBaseModel):
    """Brand template model."""
    id: str = Field("", description="Brand template ID")
    title: str = Field("", description="Brand template title")
    design_type: DesignTypeModel = Field(default_factory=DesignTypeModel)
    view_url: str = Field("", description="View URL")
    create_url: str = Field("", description="Create URL")
    thumbnail: ThumbnailModel = Field(default_factory=ThumbnailModel)
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Update timestamp")
    datasets: Dict[str, Any] = Field(default_factory=dict, description="Dataset information")


# --- Job Models ---

class JobThumbnailModel(CanvaBaseModel):
    """Job thumbnail model."""
    url: str = Field("", description="Thumbnail URL")


class AssetUploadJobModel(CanvaBaseModel):
    """Asset upload job model."""
    id: str = Field("", description="Job ID")
    name: str = Field("", description="Asset name")
    tags: List[str] = Field(default_factory=list, description="Asset tags")
    thumbnail: JobThumbnailModel = Field(default_factory=JobThumbnailModel)
    status: str = Field("", description="Job status")
    created_at: int = Field(0, description="Creation timestamp")


# --- Asset Models ---

class AssetModel(CanvaBaseModel):
    """Asset model."""
    type: str = Field("", description="Asset type")
    id: str = Field("", description="Asset ID")
    name: str = Field("", description="Asset name")
    tags: List[str] = Field(default_factory=list, description="Asset tags")
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Update timestamp")
    thumbnail: ThumbnailModel = Field(default_factory=ThumbnailModel)


# --- Folder Models ---

class FolderThumbnailModel(CanvaBaseModel):
    """Folder thumbnail model."""
    width: int = Field(0, description="Thumbnail width")
    height: int = Field(0, description="Thumbnail height") 
    url: str = Field("", description="Thumbnail URL")


class FolderInfoModel(CanvaBaseModel):
    """Folder information model."""
    id: str = Field("", description="Folder ID")
    name: str = Field("", description="Folder name")
    created_at: int = Field(0, description="Creation timestamp")
    updated_at: int = Field(0, description="Update timestamp")
    parent_id: str = Field("", description="Parent folder ID")
    thumbnail: FolderThumbnailModel = Field(default_factory=FolderThumbnailModel)


class FolderModel(CanvaBaseModel):
    """Complete folder model."""
    assets: List[str] = Field(default_factory=list, description="Asset IDs in folder")
    Designs: List[str] = Field(default_factory=list, description="Design IDs in folder")  # Note: Capital D to match DB
    folders: List[str] = Field(default_factory=list, description="Subfolder IDs")
    folder: FolderInfoModel = Field(default_factory=FolderInfoModel)


# --- Additional Job Models ---

class AutofillJobModel(CanvaBaseModel):
    """Autofill job model."""
    id: str = Field("", description="Job ID")
    status: str = Field("", description="Job status")
    created_at: int = Field(0, description="Creation timestamp")


class ExportJobModel(CanvaBaseModel):
    """Export job model."""
    id: str = Field("", description="Job ID")
    status: str = Field("", description="Job status")
    created_at: int = Field(0, description="Creation timestamp")


class DesignImportJobModel(CanvaBaseModel):
    """Design import job model."""
    id: str = Field("", description="Job ID")
    status: str = Field("", description="Job status")
    created_at: int = Field(0, description="Creation timestamp")


class URLImportJobModel(CanvaBaseModel):
    """URL import job model."""
    id: str = Field("", description="Job ID")
    status: str = Field("", description="Job status")
    created_at: int = Field(0, description="Creation timestamp")


# --- Main Database Model ---

class CanvaDB(CanvaBaseModel):
    """
    Comprehensive Pydantic model for the complete Canva database structure.
    This validates the entire database to ensure data integrity.
    """
    
    # User management
    Users: Dict[str, UserModel] = Field(
        default_factory=dict, 
        description="Dictionary of user objects keyed by user ID"
    )
    
    # Design management
    Designs: Dict[str, DesignModel] = Field(
        default_factory=dict,
        description="Dictionary of design objects keyed by design ID"
    )
    
    # Template management
    brand_templates: Dict[str, BrandTemplateModel] = Field(
        default_factory=dict,
        description="Dictionary of brand template objects keyed by template ID"
    )
    
    # Job management
    autofill_jobs: Dict[str, AutofillJobModel] = Field(
        default_factory=dict,
        description="Dictionary of autofill job objects keyed by job ID"
    )
    
    asset_upload_jobs: Dict[str, AssetUploadJobModel] = Field(
        default_factory=dict,
        description="Dictionary of asset upload job objects keyed by job ID"
    )
    
    design_export_jobs: Dict[str, ExportJobModel] = Field(
        default_factory=dict,
        description="Dictionary of design export job objects keyed by job ID"
    )
    
    design_import_jobs: Dict[str, DesignImportJobModel] = Field(
        default_factory=dict,
        description="Dictionary of design import job objects keyed by job ID"
    )
    
    url_import_jobs: Dict[str, URLImportJobModel] = Field(
        default_factory=dict,
        description="Dictionary of URL import job objects keyed by job ID"
    )
    
    # Asset management
    assets: Dict[str, AssetModel] = Field(
        default_factory=dict,
        description="Dictionary of asset objects keyed by asset ID"
    )
    
    # Folder management
    folders: Dict[str, FolderModel] = Field(
        default_factory=dict,
        description="Dictionary of folder objects keyed by folder ID"
    )

    class Config:
        validate_assignment = True
        extra = "forbid"


# --- Helper Functions ---

def validate_canva_db(db_data: Dict[str, Any]) -> CanvaDB:
    """
    Validate the entire Canva database structure.
    
    Args:
        db_data: Raw database data to validate
        
    Returns:
        CanvaDB: Validated database object
        
    Raises:
        ValidationError: If the database structure is invalid
    """
    return CanvaDB(**db_data)


def validate_db_integrity(db_instance: Dict[str, Any]) -> bool:
    """
    Check if the current database instance has valid structure.
    
    Args:
        db_instance: The database instance to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        validate_canva_db(db_instance)
        return True
    except Exception:
        return False
