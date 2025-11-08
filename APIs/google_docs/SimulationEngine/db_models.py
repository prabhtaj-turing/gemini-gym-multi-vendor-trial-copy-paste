from typing import Dict, Any, Union, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re



# --- Database Models ---
class UserInfo(BaseModel):
    """Model for user information in Google Docs."""
    displayName: str = Field(..., description="User's display name")
    kind: str = Field(default="drive#user", description="Kind of user object")
    me: bool = Field(default=True, description="Whether this is the current user")
    permissionId: Optional[str] = Field(None, description="User's permission ID (optional for GDrive compatibility)")
    emailAddress: str = Field(..., description="User's email address")


class AboutInfo(BaseModel):
    """Model for about information."""
    kind: str = Field(default="drive#about", description="Kind of about object")
    user: UserInfo = Field(..., description="User information")


# Type alias for role - can be reused across multiple models
RoleType = Literal["owner", "writer", "reader", "commenter", "editor", "viewer", "contributor"]


class DocumentPermission(BaseModel):
    """Model for document permissions."""
    id: Optional[str] = Field(None, description="Permission ID (optional, for GDrive compatibility)")
    role: RoleType = Field(
        ..., 
        description="Permission role (owner, writer, reader, commenter, editor, viewer, contributor)"
    )
    type: str = Field(..., description="Permission type (user, group, domain)")
    emailAddress: str = Field(..., description="Email address of the user/group")


class DocumentContent(BaseModel):
    """Model for document content elements."""
    elementId: str = Field(..., description="Unique identifier for the content element")
    text: str = Field(..., description="Text content of the element")


class DocumentTab(BaseModel):
    """Model for document tabs."""
    tabId: str = Field(..., description="Unique identifier for the tab")
    title: str = Field(..., description="Title of the tab")
    index: int = Field(..., description="Index of the tab")
    parentTabId: Optional[str] = Field(None, description="Parent tab ID")


class GoogleDocument(BaseModel):
    """Model for a Google Document with GDrive interoperability."""
    id: str = Field(..., description="Unique document ID")
    driveId: Optional[str] = Field(default="", description="Drive ID where document is stored (optional for GDrive compatibility)")
    name: str = Field(..., description="Document name")
    mimeType: str = Field(..., description="MIME type of the document")
    createdTime: str = Field(..., description="Document creation timestamp")
    modifiedTime: Optional[str] = Field(default=None, description="Document last modified timestamp (optional for GDrive compatibility)")
    parents: List[str] = Field(default_factory=list, description="Parent folder IDs")
    owners: List[str] = Field(default_factory=list, description="Document owners")
    suggestionsViewMode: str = Field(default="DEFAULT", description="Suggestions view mode")
    includeTabsContent: bool = Field(default=False, description="Whether to include tabs content")
    content: List[DocumentContent] = Field(default_factory=list, description="Document content (structured list)")
    tabs: List[DocumentTab] = Field(default_factory=list, description="Document tabs")
    permissions: List[DocumentPermission] = Field(default_factory=list, description="Document permissions")
    trashed: bool = Field(default=False, description="Whether document is in trash")
    starred: bool = Field(default=False, description="Whether document is starred")
    size: str = Field(default="0", description="Document size in bytes")
    
    # Additional fields for GDrive interoperability (optional)
    revisions: Optional[List[Dict[str, Any]]] = Field(None, description="File revisions (GDrive compatibility)")
    exportFormats: Optional[Dict[str, str]] = Field(None, description="Export formats (GDrive compatibility)")

    @field_validator("createdTime")
    @classmethod
    def validate_created_timestamp(cls, v):
        """Validate timestamp format for createdTime."""
        if not v or not v.strip():
            raise ValueError('Created timestamp cannot be empty')
        # Basic RFC3339 validation (could be enhanced)
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        if not re.match(rfc3339_pattern, v.strip()):
            raise ValueError('Invalid timestamp format (expected RFC3339)')
        return v.strip()
    
    @field_validator("modifiedTime")
    @classmethod
    def validate_modified_timestamp(cls, v):
        """Validate timestamp format for modifiedTime if provided."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError('Modified timestamp cannot be empty if provided')
        # Basic RFC3339 validation (could be enhanced)
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        if not re.match(rfc3339_pattern, v.strip()):
            raise ValueError('Invalid timestamp format (expected RFC3339)')
        return v.strip()
    
    @field_validator("size")
    @classmethod
    def validate_size(cls, v):
        """Validate size format."""
        if not v or not v.strip():
            raise ValueError('Size cannot be empty')
        try:
            int(v.strip())
        except ValueError:
            raise ValueError('Size must be a valid integer')
        return v.strip()


class Drive(BaseModel):
    """Model for a Google Drive."""
    id: str = Field(..., description="Unique drive ID")
    name: str = Field(..., description="Drive name")
    kind: str = Field(..., description="Kind of drive object")
    createdTime: str = Field(..., description="Drive creation timestamp")

    @field_validator("createdTime")
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format (keep as string for consistency)."""
        if isinstance(v, str):
            # Keep as string for interoperability with GDrive
            return v
        return v


class CommentAuthor(BaseModel):
    """Model for comment author."""
    displayName: str = Field(..., description="Author's display name")
    emailAddress: str = Field(..., description="Author's email address")


class Comment(BaseModel):
    """Model for a document comment."""
    id: str = Field(..., description="Unique comment ID")
    fileId: str = Field(..., description="ID of the file this comment belongs to")
    content: str = Field(..., description="Comment content")
    author: CommentAuthor = Field(..., description="Comment author")
    createdTime: str = Field(..., description="Comment creation timestamp")

    @field_validator("createdTime")
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format (keep as string for consistency)."""
        if isinstance(v, str):
            # Keep as string for interoperability with GDrive
            return v
        return v


class Reply(BaseModel):
    """Model for a comment reply."""
    id: str = Field(..., description="Unique reply ID")
    commentId: str = Field(..., description="ID of the parent comment")
    fileId: str = Field(..., description="ID of the file this reply belongs to")
    content: str = Field(..., description="Reply content")
    author: CommentAuthor = Field(..., description="Reply author")
    createdTime: str = Field(..., description="Reply creation timestamp")

    @field_validator("createdTime")
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format (keep as string for consistency)."""
        if isinstance(v, str):
            # Keep as string for interoperability with GDrive
            return v
        return v


class Label(BaseModel):
    """Model for a document label."""
    id: str = Field(..., description="Unique label ID")
    fileId: str = Field(..., description="ID of the file this label belongs to")
    name: str = Field(..., description="Label name")
    color: str = Field(..., description="Label color in hex format")


class AccessProposalRequester(BaseModel):
    """Model for access proposal requester."""
    displayName: str = Field(..., description="Requester's display name")
    emailAddress: str = Field(..., description="Requester's email address")


class AccessProposal(BaseModel):
    """Model for an access proposal."""
    id: str = Field(..., description="Unique proposal ID")
    fileId: str = Field(..., description="ID of the file this proposal is for")
    role: RoleType = Field(..., description="Requested role (owner, writer, reader, commenter, editor, viewer, contributor)")
    state: str = Field(..., description="Proposal state (pending, approved, rejected)")
    requester: AccessProposalRequester = Field(..., description="Proposal requester")
    createdTime: str = Field(..., description="Proposal creation timestamp")

    @field_validator("createdTime")
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format (keep as string for consistency)."""
        if isinstance(v, str):
            # Keep as string for interoperability with GDrive
            return v
        return v


class Counters(BaseModel):
    """Model for various counters."""
    file: int = Field(default=0, ge=0, description="Number of files")
    drive: int = Field(default=0, ge=0, description="Number of drives")
    comment: int = Field(default=0, ge=0, description="Number of comments")
    reply: int = Field(default=0, ge=0, description="Number of replies")
    label: int = Field(default=0, ge=0, description="Number of labels")
    accessproposal: int = Field(default=0, ge=0, description="Number of access proposals")
    revision: int = Field(default=0, ge=0, description="Number of revisions")


class UserData(BaseModel):
    """Model for user-specific data with strict GoogleDocument validation."""
    about: AboutInfo = Field(..., description="User about information")
    files: Dict[str, GoogleDocument] = Field(default_factory=dict, description="User files (must be valid GoogleDocuments)")
    drives: Dict[str, Drive] = Field(default_factory=dict, description="User's drives")
    comments: Dict[str, Comment] = Field(default_factory=dict, description="User's comments")
    replies: Dict[str, Reply] = Field(default_factory=dict, description="User's replies")
    labels: Dict[str, Label] = Field(default_factory=dict, description="User's labels")
    accessproposals: Dict[str, AccessProposal] = Field(default_factory=dict, description="User's access proposals")
    counters: Counters = Field(default_factory=Counters, description="Various counters")


class GoogleDocsDB(BaseModel):
    """Main database model for Google Docs simulation."""
    users: Dict[str, UserData] = Field(default_factory=dict, description="All users and their data")

    @model_validator(mode="after")
    def validate_database_structure(self) -> "GoogleDocsDB":
        """Validate the overall database structure."""
        # Allow empty databases for compatibility with GDrive
        if not self.users:
            return self
        
        # Validate that each user has required fields
        for user_id, user_data in self.users.items():
            if not hasattr(user_data, 'about'):
                raise ValueError(f"User {user_id} must have 'about' information")
            if not hasattr(user_data, 'counters'):
                raise ValueError(f"User {user_id} must have 'counters'")
        
        return self

    def get_user_by_email(self, email: str) -> Optional[UserData]:
        """Get user data by email address."""
        for user_data in self.users.values():
            if user_data.about.user.emailAddress == email:
                return user_data
        return None

    def get_document_by_id(self, document_id: str) -> Optional[GoogleDocument]:
        """Get document by ID across all users."""
        for user_data in self.users.values():
            if document_id in user_data.files:
                return user_data.files[document_id]
        return None

    def get_drive_by_id(self, drive_id: str) -> Optional[Drive]:
        """Get drive by ID across all users."""
        for user_data in self.users.values():
            if drive_id in user_data.drives:
                return user_data.drives[drive_id]
        return None