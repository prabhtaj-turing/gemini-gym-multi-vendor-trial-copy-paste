from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator, HttpUrl, root_validator
from enum import Enum

# --- Enum Types ---

class DesignPresetType(str, Enum):
    DOC = "doc"
    WHITEBOARD = "whiteboard"
    PRESENTATION = "presentation"
    CANVAS = "canvas"
    BANNER = "banner"
    FLYER = "flyer"
    SOCIAL = "social"
    VIDEO = "video"
    INFOGRAPHIC = "infographic"
    POSTER = "poster"

class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"

class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ThreadType(str, Enum):
    GENERAL = "general"
    TASK = "task"
    FEEDBACK = "feedback"
    COMMENT = "comment"

class DesignTypeEnum(str, Enum):
    PRESET = "preset"


# --- User Models ---

class UserProfileModel(BaseModel):
    """User profile information."""
    display_name: str = Field(..., description="User's display name", min_length=1)

class UserModel(BaseModel):
    """Complete user model."""
    user_id: str = Field(..., description="User ID")
    team_id: str = Field(..., description="Team ID")
    profile: UserProfileModel = Field(default_factory=UserProfileModel)

# --- Design Models ---

class DesignTypeModel(BaseModel):
    """Design type information."""
    type: Optional[DesignTypeEnum] = Field(None, description="Design type")
    name: Optional[DesignPresetType] = Field(None, description="Design name")

class OwnerModel(BaseModel):
    """Owner information."""
    user_id: Optional[str] = Field(None, description="Owner user ID")
    team_id: Optional[str] = Field(None, description="Owner team ID")

class ThumbnailModel(BaseModel):
    """Thumbnail information."""
    width: int = Field(..., ge=0, description="Thumbnail width")
    height: int = Field(..., ge=0, description="Thumbnail height")
    url: HttpUrl = Field(..., description="Thumbnail URL")

class UrlsModel(BaseModel):
    """URL information."""
    edit_url: Optional[HttpUrl] = Field(None, description="Edit URL")
    view_url: Optional[HttpUrl] = Field(None, description="View URL")

class PageModel(BaseModel):
    """Page information."""
    index: int = Field(..., ge=0, description="Page index")
    thumbnail: ThumbnailModel = Field(default_factory=ThumbnailModel)

class MentionUserModel(BaseModel):
    """User information within mentions."""
    user_id: str = Field(..., description="User ID")
    team_id: str = Field(..., description="Team ID")
    display_name: str = Field(..., description="Display name")

class MentionModel(BaseModel):
    """Mention information."""
    tag: str = Field(..., description="Mention tag")
    user: MentionUserModel = Field(default_factory=MentionUserModel)

class ContentModel(BaseModel):
    """Content information."""
    plaintext: str = Field(..., description="Plain text content")
    markdown: str = Field(..., description="Markdown content")

class AuthorModel(BaseModel):
    """Author information."""
    id: str = Field(..., description="Author ID")
    display_name: str = Field(..., description="Author display name")

class AssigneeModel(BaseModel):
    """Assignee information."""
    id: str = Field(..., description="Assignee ID")
    display_name: str = Field(..., description="Assignee display name")

class ThreadTypeModel(BaseModel):
    """Thread type information."""
    type: ThreadType = Field(..., description="Thread type")    
    content: ContentModel = Field(default_factory=ContentModel)
    mentions: Dict[str, MentionModel] = Field(default_factory=dict)
    assignee: AssigneeModel = Field(default_factory=AssigneeModel)
    resolver: AssigneeModel = Field(default_factory=AssigneeModel)

class ReplyModel(BaseModel):
    """Comment reply model."""
    id: str = Field(..., description="Reply ID")
    design_id: str = Field(..., description="Design ID")
    thread_id: str = Field(..., description="Thread ID")
    author: AuthorModel = Field(default_factory=AuthorModel)
    content: ContentModel = Field(default_factory=ContentModel)
    mentions: Dict[str, MentionModel] = Field(default_factory=dict)
    created_at: int = Field(..., ge=0, description="Creation timestamp")
    updated_at: int = Field(..., ge=0, description="Update timestamp")

class CommentThreadModel(BaseModel):
    """Comment thread model."""
    id: str = Field(..., description="Thread ID")
    design_id: str = Field(..., description="Design ID")
    thread_type: ThreadTypeModel = Field(default_factory=ThreadTypeModel)
    author: AuthorModel = Field(default_factory=AuthorModel)
    created_at: int = Field(..., ge=0, description="Creation timestamp")
    updated_at: int = Field(..., ge=0, description="Update timestamp")
    replies: Dict[str, ReplyModel] = Field(default_factory=dict)


class CommentsModel(BaseModel):
    """Comments container model."""
    threads: Dict[str, CommentThreadModel] = Field(default_factory=dict)


class DesignModel(BaseModel):
    """Complete design model."""
    id: str = Field(..., description="Design ID")
    title: str = Field(..., description="Design title", min_length=1)
    design_type: Optional[DesignTypeModel] = Field(default={}, description="Design type")
    owner: Optional[OwnerModel] = Field(default={}, description="Owner")
    thumbnail: Optional[ThumbnailModel] = Field(default={}, description="Thumbnail")
    urls: Optional[UrlsModel] = Field(default={}, description="URLs")
    created_at: int = Field(..., ge=0, description="Creation timestamp")
    updated_at: int = Field(..., ge=0, description="Update timestamp")
    page_count: Optional[int] = Field(None, ge=0, description="Number of pages")
    pages: Dict[str, PageModel] = Field(default_factory=dict)
    comments: CommentsModel = Field(default_factory=CommentsModel)

# --- Brand Template Models ---

class BrandTemplateModel(BaseModel):
    """Brand template model."""
    id: str = Field(..., description="Brand template ID")
    title: str = Field(..., description="Brand template title", min_length=1)
    design_type: DesignTypeModel = Field(default_factory=DesignTypeModel)
    view_url: HttpUrl = Field(..., description="View URL")
    create_url: HttpUrl = Field(..., description="Create URL")
    thumbnail: ThumbnailModel = Field(default_factory=ThumbnailModel)
    created_at: int = Field(..., ge=0, description="Creation timestamp")
    updated_at: int = Field(..., ge=0, description="Update timestamp")
    datasets: Dict[str, Dict[str, str]] = Field(default_factory=dict, description="Dataset information")

# --- Job Models ---

class JobThumbnailModel(BaseModel):
    """Job thumbnail model."""
    url: HttpUrl = Field(..., description="Thumbnail URL")

class AssetUploadJobModel(BaseModel):
    """Asset upload job model."""
    id: str = Field(..., description="Job ID")
    name: str = Field(..., description="Asset name", min_length=1)
    tags: List[str] = Field(default_factory=list, description="Asset tags")
    thumbnail: JobThumbnailModel = Field(default_factory=JobThumbnailModel)
    status: JobStatus = Field(..., description="Job status")
    created_at: int = Field(..., ge=0, description="Creation timestamp")

# --- Asset Models ---

class AssetModel(BaseModel):
    """Asset model."""
    type: AssetType = Field(..., description="Asset type")
    id: str = Field(..., description="Asset ID")
    name: str = Field(..., description="Asset name", min_length=1)
    tags: List[str] = Field(default_factory=list, description="Asset tags")
    created_at: int = Field(..., ge=0, description="Creation timestamp")
    updated_at: int = Field(..., ge=0, description="Update timestamp")
    thumbnail: ThumbnailModel = Field(default_factory=ThumbnailModel)
# --- Folder Models ---

class FolderThumbnailModel(BaseModel):
    """Folder thumbnail model."""
    width: int = Field(..., ge=0, description="Thumbnail width")
    height: int = Field(..., ge=0, description="Thumbnail height") 
    url: HttpUrl = Field(..., description="Thumbnail URL")

class FolderInfoModel(BaseModel):
    """Folder information model."""
    id: str = Field(..., description="Folder ID")
    name: str = Field(..., description="Folder name", min_length=1)
    created_at: int = Field(..., ge=0, description="Creation timestamp")
    updated_at: int = Field(..., ge=0, description="Update timestamp")
    parent_id: str = Field(..., description="Parent folder ID")
    thumbnail: FolderThumbnailModel = Field(default_factory=FolderThumbnailModel)


class FolderModel(BaseModel):
    """Complete folder model."""
    assets: List[str] = Field(default_factory=list, description="Asset IDs in folder")
    Designs: List[str] = Field(default_factory=list, description="Design IDs in folder")
    folders: List[str] = Field(default_factory=list, description="Subfolder IDs")
    folder: FolderInfoModel = Field(default_factory=FolderInfoModel)


# --- Additional Job Models ---

class AutofillJobModel(BaseModel):
    """Autofill job model."""
    id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    created_at: int = Field(..., ge=0, description="Creation timestamp")

class ExportJobModel(BaseModel):
    """Export job model."""
    id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    created_at: int = Field(..., ge=0, description="Creation timestamp")

class DesignImportJobModel(BaseModel):
    """Design import job model."""
    id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    created_at: int = Field(..., ge=0, description="Creation timestamp")

class URLImportJobModel(BaseModel):
    """URL import job model."""
    id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    created_at: int = Field(..., ge=0, description="Creation timestamp")


# --- Main Database Model ---

class CanvaDB(BaseModel):
    """
    Comprehensive Pydantic model for the complete Canva database structure.
    This validates the entire database to ensure data integrity.
    """
    
    Users: Dict[str, UserModel] = Field(
        default_factory=dict, 
        description="Dictionary of user objects keyed by user ID"
    )
    
    Designs: Dict[str, DesignModel] = Field(
        default_factory=dict,
        description="Dictionary of design objects keyed by design ID"
    )

    brand_templates: Dict[str, BrandTemplateModel] = Field(
        default_factory=dict,
        description="Dictionary of brand template objects keyed by template ID"
    )
    
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
    
    assets: Dict[str, AssetModel] = Field(
        default_factory=dict,
        description="Dictionary of asset objects keyed by asset ID"
    )
    
    folders: Dict[str, FolderModel] = Field(
        default_factory=dict,
        description="Dictionary of folder objects keyed by folder ID"
    )

    class Config:
        str_strip_whitespace = True
