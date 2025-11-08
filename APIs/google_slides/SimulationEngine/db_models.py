"""
Database models for Google Slides API simulation with GDrive interoperability.

This module defines Pydantic models for the database schema, reusing common models
from gdrive for consistency and modularity across all Google Workspace APIs.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union

# Import common models from gdrive for interoperability
from gdrive.SimulationEngine.db_models import (
    UserAboutModel,
    FilePermissionModel,
    CountersModel,
    DriveModel,
    CommentModel,
    ReplyModel,
    LabelModel,
    AccessProposalModel,
)

# Import Slides-specific models
from google_slides.SimulationEngine.models import (
    PageModel,
    Size,
)


class SlidesFile(BaseModel):
    """
    Model for a Google Slides presentation stored as a Drive file.
    
    This model extends the standard Drive file structure with Slides-specific
    fields for full interoperability with Google Drive.
    """
    # Standard Drive file fields
    id: str = Field(..., description="Unique file identifier")
    driveId: Optional[str] = Field(default="", description="Shared drive ID (empty for My Drive)")
    name: str = Field(..., description="File name")
    mimeType: Optional[str] = Field(default="application/vnd.google-apps.presentation", description="MIME type (application/vnd.google-apps.presentation)")
    createdTime: str = Field(..., description="Creation timestamp (ISO 8601)")
    modifiedTime: Optional[str] = Field(default=None, description="Last modification timestamp (ISO 8601)")
    trashed: Optional[bool] = Field(default=False, description="Whether file is in trash")
    starred: Optional[bool] = Field(default=False, description="Whether file is starred")
    parents: List[str] = Field(default_factory=list, description="Parent folder IDs")
    owners: List[str] = Field(default_factory=list, description="Owner email addresses")
    size: Optional[str] = Field(default="0", description="File size in bytes")
    permissions: List[FilePermissionModel] = Field(default_factory=list, description="File access permissions")
    
    # Google Slides specific fields
    presentationId: Optional[str] = Field(None, description="Presentation unique identifier")
    title: Optional[str] = Field(None, description="Presentation title")
    slides: List[PageModel] = Field(default_factory=list, description="Presentation slide pages")
    masters: List[PageModel] = Field(default_factory=list, description="Master slide templates")
    layouts: List[PageModel] = Field(default_factory=list, description="Layout templates")
    notesMaster: Optional[PageModel] = Field(None, description="Notes master template")
    pageSize: Optional[Size] = Field(None, description="Slide dimensions")
    locale: Optional[str] = Field(None, description="Presentation locale (e.g., 'en-US')")
    revisionId: Optional[str] = Field(None, description="Current revision identifier")
    
    @field_validator('notesMaster', mode='before')
    @classmethod
    def handle_notes_master(cls, v):
        """Handle notesMaster field which can be a single PageModel, or None."""
        if v is None:
            return None
        if isinstance(v, dict):
            return v if v else None
        # If it's a single PageModel, return it
        return v

    def to_presentation_dict(self) -> Dict[str, Any]:
        """
        Convert SlidesFile to a presentation dictionary for API compatibility.
        
        Returns:
            Dict containing presentation data in API format.
        """
        return {
            'presentationId': self.presentationId or self.id,
            'title': self.title,
            'pageSize': self.pageSize.model_dump(exclude_none=True) if self.pageSize else None,
            'slides': [slide.model_dump(exclude_none=True) for slide in self.slides],
            'masters': [master.model_dump(exclude_none=True) for master in self.masters],
            'layouts': [layout.model_dump(exclude_none=True) for layout in self.layouts],
            'notesMaster': self.notesMaster.model_dump(exclude_none=True) if self.notesMaster else None,
            'locale': self.locale,
            'revisionId': self.revisionId
        }


class SlidesUserData(BaseModel):
    """
    Model for user-specific data in the Slides database.
    
    Reuses common models from gdrive for consistency across Google Workspace APIs.
    Uses Union type for files to support both presentations and other file types for interoperability.
    """
    about: UserAboutModel = Field(..., description="User account and Drive metadata (required)")
    files: Dict[str, SlidesFile] = Field(default_factory=dict, description="User files (must be valid SlidesFiles)")
    drives: Dict[str, DriveModel] = Field(default_factory=dict, description="Shared drives accessible to user")
    comments: Dict[str, CommentModel] = Field(default_factory=dict, description="Comments on user's files")
    replies: Dict[str, ReplyModel] = Field(default_factory=dict, description="Replies to comments")
    labels: Dict[str, LabelModel] = Field(default_factory=dict, description="Metadata labels for files")
    accessproposals: Dict[str, AccessProposalModel] = Field(default_factory=dict, description="Access permission proposals")
    counters: CountersModel = Field(default_factory=CountersModel, description="ID generation counters")


class GoogleSlidesDB(BaseModel):
    """
    Main database model for Google Slides simulation.
    
    This model represents the entire database structure, organized by users.
    Each user has their own set of files (presentations), drives, comments, etc.
    
    Uses common models from gdrive.SimulationEngine.db_models for consistency
    and interoperability across all Google Workspace APIs.
    """
    users: Dict[str, SlidesUserData] = Field(
        default_factory=dict, 
        description="User data indexed by user ID"
    )

    def get_user_presentation(self, user_id: str, presentation_id: str) -> Optional[SlidesFile]:
        """
        Get a specific presentation for a user.
        
        Args:
            user_id: The user ID
            presentation_id: The presentation ID
            
        Returns:
            The presentation SlidesFile if found, None otherwise
        """
        if user_id not in self.users:
            return None
        return self.users[user_id].files.get(presentation_id)
    
    def get_all_presentations(self, user_id: str) -> Dict[str, SlidesFile]:
        """
        Get all presentations for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary of presentation_id -> SlidesFile
        """
        if user_id not in self.users:
            return {}
        return self.users[user_id].files
