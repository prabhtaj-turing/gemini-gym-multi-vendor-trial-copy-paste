from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
import re


class DocumentElementModel(BaseModel):
    """
    Model representing a single document element with ID and text content.
    Used for Google Docs structured content.
    
    Attributes:
        elementId: Unique identifier for the document element
        text: Text content of the element
    """
    elementId: str = Field(..., description="Unique identifier for the document element")
    text: str = Field(..., description="Text content of the element")
    
    @field_validator('elementId')
    @classmethod
    def validate_element_id(cls, v):
        """Validate element ID format."""
        if not v or not v.strip():
            raise ValueError('Element ID cannot be empty')
        return v.strip()
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        """Validate text content."""
        if v is None:
            return ""
        return v


class FileContentModel(BaseModel):
    """
    Model representing file content with metadata.
    
    Attributes:
        data: Encoded content data
        encoding: Content encoding (typically 'base64')
        checksum: SHA256 checksum for integrity verification
        version: Content version
        lastContentUpdate: Timestamp of last content update
    """
    data: str = Field(..., description="Encoded content data")
    encoding: str = Field(default="base64", description="Content encoding")
    checksum: str = Field(..., description="SHA256 checksum for integrity")
    version: str = Field(default="1.0", description="Content version")
    lastContentUpdate: str = Field(..., description="Timestamp of last content update")
    
    @field_validator('data', 'encoding')
    @classmethod
    def validate_data(cls, v, w):
        """Validate base64 data format only when encoding is 'base64'."""
        if w != 'base64':
            return v
        if not v or not v.strip():
            raise ValueError('Content data cannot be empty')
        # Basic base64 validation (could be enhanced)
        import base64
        try:
            # Remove padding if present for validation
            data_to_validate = v.rstrip('=')
            base64.b64decode(data_to_validate + '=' * (-len(data_to_validate) % 4))
        except Exception:
            raise ValueError('Invalid base64 data format')
        return v
    
    @field_validator('encoding')
    @classmethod
    def validate_encoding(cls, v):
        """Validate encoding format."""
        if not v or not v.strip():
            raise ValueError('Encoding cannot be empty')
        return v.strip()
    
    @field_validator('checksum', 'encoding')
    @classmethod
    def validate_checksum(cls, v, w):
        """Validate checksum format."""
        if w != 'base64':
            return v
        if not v or not v.strip():
            raise ValueError('Checksum cannot be empty')
        # Basic SHA256 format validation
        if not v.startswith('sha256:'):
            raise ValueError('Checksum must start with "sha256:"')
        if len(v) < 8:  # sha256: + at least 1 character
            raise ValueError('Invalid checksum format')
        return v
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        """Validate version format."""
        if not v or not v.strip():
            raise ValueError('Version cannot be empty')
        return v.strip()
    
    @field_validator('lastContentUpdate')
    @classmethod
    def validate_last_content_update(cls, v):
        """Validate timestamp format."""
        if not v or not v.strip():
            raise ValueError('Last content update timestamp cannot be empty')
        # Basic RFC3339 validation (could be enhanced)
        import re
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        if not re.match(rfc3339_pattern, v.strip()):
            raise ValueError('Invalid timestamp format (expected RFC3339)')
        return v.strip()


# Union type for file content - supports both formats
FileContentUnion = Union[FileContentModel, List[DocumentElementModel]]


class RevisionContentModel(BaseModel):
    """
    Model representing revision content with minimal metadata.
    This is a simplified version of FileContentModel for revision storage.
    
    Attributes:
        data: Base64 encoded content data
        encoding: Content encoding (typically 'base64')
        checksum: SHA256 checksum for integrity verification
    """
    data: str = Field(..., description="Base64 encoded content data")
    encoding: str = Field(default="base64", description="Content encoding")
    checksum: str = Field(..., description="SHA256 checksum for integrity")
    
    @field_validator('data', 'encoding')
    @classmethod
    def validate_data(cls, v, w):
        """Validate base64 data format only when encoding is 'base64'."""
        if w != 'base64':
            return v
        if not v or not v.strip():
            raise ValueError('Content data cannot be empty')
        # Basic base64 validation (could be enhanced)
        import base64
        try:
            # Remove padding if present for validation
            data_to_validate = v.rstrip('=')
            base64.b64decode(data_to_validate + '=' * (-len(data_to_validate) % 4))
        except Exception:
            raise ValueError('Invalid base64 data format')
        return v
    
    @field_validator('encoding')
    @classmethod
    def validate_encoding(cls, v):
        """Validate encoding format."""
        if not v or not v.strip():
            raise ValueError('Encoding cannot be empty')
        return v.strip()
    
    @field_validator('checksum')
    @classmethod
    def validate_checksum(cls, v):
        """Validate checksum format."""
        if not v or not v.strip():
            raise ValueError('Checksum cannot be empty')
        # Basic SHA256 format validation
        if not v.startswith('sha256:'):
            raise ValueError('Checksum must start with "sha256:"')
        if len(v) < 8:  # sha256: + at least 1 character
            raise ValueError('Invalid checksum format')
        return v


class RevisionModel(BaseModel):
    """
    Model representing a file revision.
    
    Attributes:
        id: Unique revision identifier
        mimeType: MIME type of the revision
        modifiedTime: When the revision was created
        keepForever: Whether to keep this revision forever
        originalFilename: Original filename
        size: File size in bytes
        content: Revision content with metadata
    """
    id: str = Field(..., description="Unique revision identifier")
    mimeType: str = Field(..., description="MIME type of the revision")
    modifiedTime: str = Field(..., description="When the revision was created")
    keepForever: bool = Field(default=False, description="Whether to keep this revision forever")
    originalFilename: str = Field(..., description="Original filename")
    size: str = Field(..., description="File size in bytes")
    content: RevisionContentModel = Field(..., description="Revision content with metadata")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate revision ID format."""
        if not v or not v.strip():
            raise ValueError('Revision ID cannot be empty')
        return v.strip()
    
    @field_validator('mimeType')
    @classmethod
    def validate_mime_type(cls, v):
        """Validate MIME type format."""
        if not v or not v.strip():
            raise ValueError('MIME type cannot be empty')
        # Basic MIME type validation (type/subtype)
        mime_pattern = r'^[a-zA-Z][a-zA-Z0-9][a-zA-Z0-9\-]*\/[a-zA-Z0-9][a-zA-Z0-9\-\.]*$'
        if not re.match(mime_pattern, v.strip()):
            raise ValueError('Invalid MIME type format')
        return v.strip()
    
    @field_validator('modifiedTime')
    @classmethod
    def validate_modified_time(cls, v):
        """Validate timestamp format."""
        if not v or not v.strip():
            raise ValueError('Modified time cannot be empty')
        # Basic RFC3339 validation (could be enhanced)
        import re
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        if not re.match(rfc3339_pattern, v.strip()):
            raise ValueError('Invalid timestamp format (expected RFC3339)')
        return v.strip()
    
    @field_validator('originalFilename')
    @classmethod
    def validate_original_filename(cls, v):
        """Validate original filename."""
        if not v or not v.strip():
            raise ValueError('Original filename cannot be empty')
        return v.strip()
    
    @field_validator('size')
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


class ExportFormatsModel(BaseModel):
    """
    Model representing export formats for a file.
    
    This model accepts any MIME type as a key and validates that the value
    is a valid base64 encoded string.
    """
    
    @field_validator('*')
    @classmethod
    def validate_export_format_value(cls, v):
        """Validate that any export format value is valid base64."""
        if v is not None:
            if not v.strip():
                raise ValueError('Export format data cannot be empty if provided')
            # Basic base64 validation
            import base64
            try:
                data_to_validate = v.rstrip('=')
                base64.b64decode(data_to_validate + '=' * (-len(data_to_validate) % 4))
            except Exception:
                raise ValueError('Invalid base64 data format for export format')
        return v
    
    model_config = {
        "extra": "allow",  # Allow any MIME type keys
        "validate_assignment": True  # Validate when values are assigned
    }
    
    def __init__(self, **data):
        # Validate all values before calling parent constructor
        for key, value in data.items():
            if value is not None:
                if not value.strip():
                    raise ValueError(f'Export format data for {key} cannot be empty if provided')
                # Basic base64 validation
                import base64
                try:
                    data_to_validate = value.rstrip('=')
                    base64.b64decode(data_to_validate + '=' * (-len(data_to_validate) % 4))
                except Exception:
                    raise ValueError(f'Invalid base64 data format for export format {key}')
        super().__init__(**data)


class FileWithContentModel(BaseModel):
    """
    Extended file model that includes content, revisions, and export formats.
    This extends the basic file structure with the new content schema.
    Designed for interoperability between GDrive and Docs APIs.
    """
    # Basic file properties (from existing models)
    id: str = Field(..., description="File ID")
    driveId: Optional[str] = Field(default="", description="Drive ID (optional for Docs compatibility)")
    name: str = Field(..., description="File name")
    mimeType: str = Field(..., description="MIME type")
    createdTime: str = Field(..., description="Creation timestamp")
    modifiedTime: Optional[str] = Field(..., description="Modification timestamp")
    trashed: bool = Field(default=False, description="Whether file is trashed")
    starred: bool = Field(default=False, description="Whether file is starred")
    parents: List[str] = Field(default_factory=list, description="Parent folder IDs")
    owners: List[str] = Field(default_factory=list, description="File owners")
    size: str = Field(default="0", description="File size")
    permissions: List[Dict[str, Any]] = Field(default_factory=list, description="File permissions")
    
    # New content schema properties
    content: Optional[FileContentUnion] = Field(None, description="File content with metadata or document elements")
    revisions: List[RevisionModel] = Field(default_factory=list, description="File revisions")
    exportFormats: Optional[Dict[str, str]] = Field(None, description="Export formats")
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate file ID format."""
        if not v or not v.strip():
            raise ValueError('File ID cannot be empty')
        return v.strip()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate file name."""
        if not v or not v.strip():
            raise ValueError('File name cannot be empty')
        return v.strip()
    
    @field_validator('mimeType')
    @classmethod
    def validate_mime_type(cls, v):
        """Validate MIME type format."""
        if not v or not v.strip():
            raise ValueError('MIME type cannot be empty')
        # Basic MIME type validation (type/subtype)
        mime_pattern = r'^[a-zA-Z][a-zA-Z0-9][a-zA-Z0-9\-]*\/[a-zA-Z0-9][a-zA-Z0-9\-\.]*$'
        if not re.match(mime_pattern, v.strip()):
            raise ValueError('Invalid MIME type format')
        return v.strip()
    
    @field_validator('createdTime', 'modifiedTime')
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        if not v or not v.strip():
            raise ValueError('Timestamp cannot be empty')
        # Basic RFC3339 validation (could be enhanced)
        import re
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        if not re.match(rfc3339_pattern, v.strip()):
            raise ValueError('Invalid timestamp format (expected RFC3339)')
        return v.strip()
    
    @field_validator('size')
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
    
    model_config = {
        "extra": "allow"  # Allow additional fields for flexibility
    }


class StorageQuotaModel(BaseModel):
    """Model for storage quota information."""
    limit: str = Field(..., description="Storage limit in bytes")
    usageInDrive: Optional[str] = Field(default="0", description="Storage usage in Drive in bytes")
    usageInDriveTrash: Optional[str] = Field(default="0", description="Storage usage in Drive trash in bytes")
    usage: str = Field(..., description="Total storage usage in bytes")

class DriveThemeModel(BaseModel):
    """Model for a drive theme."""
    id: str = Field(..., description="Theme ID")
    backgroundImageLink: Optional[str] = Field(None, description="Background image link")
    colorRgb: Optional[str] = Field(None, description="Color RGB")

class UserInfoModel(BaseModel):
    """Model for user information in the about section."""
    displayName: str = Field(..., description="User display name")
    kind: str = Field(default="drive#user", description="API kind identifier")
    me: Optional[bool] = Field(default=True, description="Whether this is the current user")
    permissionId: Optional[str] = Field(None, description="User permission ID")
    emailAddress: str = Field(..., description="User email address")


class UserAboutModel(BaseModel):
    """Model for the 'about' section in user data."""
    kind: str = Field(default="drive#about", description="API kind identifier")
    storageQuota: Optional[StorageQuotaModel] = Field(None, description="Storage quota information (optional for Docs compatibility)")
    driveThemes: Optional[List[DriveThemeModel]] = Field(None, description="List of available drive themes (optional for Docs compatibility)")
    canCreateDrives: Optional[bool] = Field(None, description="Whether user can create drives (optional for Docs compatibility)")
    importFormats: Optional[Dict[str, List[str]]] = Field(None, description="Supported import formats (optional for Docs compatibility)")
    exportFormats: Optional[Dict[str, List[str]]] = Field(None, description="Supported export formats (optional for Docs compatibility)")
    appInstalled: Optional[bool] = Field(None, description="Whether apps are installed (optional for Docs compatibility)")
    user: UserInfoModel = Field(..., description="User information")
    folderColorPalette: Optional[str] = Field(None, description="Folder color palette (optional for Docs compatibility)")
    maxImportSizes: Optional[Dict[str, str]] = Field(None, description="Maximum import sizes (optional for Docs compatibility)")
    maxUploadSize: Optional[str] = Field(None, description="Maximum upload size (optional for Docs compatibility)")


class FilePermissionModel(BaseModel):
    """Model for file permissions as stored in the JSON."""
    id: Optional[str] = Field(None, description="Permission ID (optional for Docs interoperability)")
    role: str = Field(..., description="Permission role")
    type: str = Field(..., description="Permission type")
    emailAddress: str = Field(..., description="Email address")


class FileContentJSONModel(BaseModel):
    """Model for file content as stored in the JSON."""
    data: str = Field(..., description="Base64 encoded content")
    encoding: str = Field(..., description="Content encoding")
    checksum: str = Field(..., description="Content checksum")
    version: str = Field(..., description="Content version")
    lastContentUpdate: str = Field(..., description="Last content update timestamp")


class FileRevisionModel(BaseModel):
    """Model for file revisions as stored in the JSON."""
    id: str = Field(..., description="Revision ID")
    mimeType: str = Field(..., description="MIME type")
    modifiedTime: str = Field(..., description="Modification time")
    keepForever: bool = Field(..., description="Whether to keep forever")
    originalFilename: str = Field(..., description="Original filename")
    size: str = Field(..., description="File size")
    content: Optional[RevisionContentModel] = Field(None, description="Revision content")


class FileModel(BaseModel):
    """Model for files as stored in the JSON.
    
    This is the base model for Drive files. API-specific files (Slides, Sheets, Docs)
    with additional fields are validated as Dict[str, Any] in the Union type.
    """
    id: str = Field(..., description="File ID")
    driveId: Optional[str] = Field(default="", description="Drive ID")
    name: str = Field(..., description="File name")
    mimeType: str = Field(..., description="MIME type")
    createdTime: str = Field(..., description="Creation time")
    modifiedTime: Optional[str] = Field(default=None, description="Modification time")
    trashed: bool = Field(default=False, description="Whether trashed")
    starred: bool = Field(default=False, description="Whether starred")
    parents: List[str] = Field(default_factory=list, description="Parent folders")
    owners: List[str] = Field(default_factory=list, description="File owners")
    size: str = Field(default="0", description="File size")
    permissions: List[FilePermissionModel] = Field(default_factory=list, description="File permissions")
    
    # Document/Drive-specific fields (for Docs, generic files)
    content: Optional[Union[FileContentJSONModel, List[Dict[str, str]]]] = Field(None, description="File content (supports both base64 and document elements)")
    revisions: Optional[List[FileRevisionModel]] = Field(default_factory=list, description="File revisions")
    exportFormats: Optional[Dict[str, str]] = Field(None, description="Export formats")
    
    # Sheets-specific fields (for Spreadsheets - note: 'sheets' is the spreadsheet tabs)
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Spreadsheet properties")
    sheets: Optional[List[Dict[str, Any]]] = Field(default=None, description="Spreadsheet sheets/tabs (for Sheets API)")
    data: Optional[Dict[str, List[List[Any]]]] = Field(default_factory=dict, description="Spreadsheet cell data")
    
    # Slides-specific fields (for Presentations - note: 'slides' is the presentation pages)  
    presentationId: Optional[str] = Field(None, description="Presentation unique identifier")
    title: Optional[str] = Field(None, description="Presentation title")
    slides: Optional[List[Dict[str, Any]]] = Field(default=None, description="Presentation slides/pages (for Slides API)")
    masters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Master slide templates")
    layouts: Optional[List[Dict[str, Any]]] = Field(default=None, description="Layout templates")
    notesMaster: Optional[List[Dict[str, Any]]] = Field(None, description="Notes master template")
    pageSize: Optional[Dict[str, Any]] = Field(None, description="Slide dimensions")
    locale: Optional[str] = Field(None, description="Presentation locale")
    revisionId: Optional[str] = Field(None, description="Current revision identifier")
    
    # Docs-specific fields (for Documents)
    suggestionsViewMode: Optional[str] = Field(None, description="Suggestions view mode")
    includeTabsContent: Optional[bool] = Field(None, description="Whether to include tabs content")
    tabs: Optional[List[Dict[str, Any]]] = Field(None, description="Document tabs")


class DriveModel(BaseModel):
    """Model for drives as stored in the JSON."""
    id: str = Field(..., description="Drive ID")
    name: str = Field(..., description="Drive name")
    kind: str = Field(..., description="API kind")
    createdTime: str = Field(..., description="Creation time")
    owners: List[str] = Field(default_factory=list, description="Drive owners")
    permissions: List[FilePermissionModel] = Field(default_factory=list, description="File permissions")

class CommentAuthorModel(BaseModel):
    """Model for comment author."""
    displayName: str = Field(..., description="Display name")
    emailAddress: str = Field(..., description="Email address")
    photoLink: Optional[str] = Field(None, description="Photo link")


class CommentModel(BaseModel):
    """Model for comments as stored in the JSON."""
    id: str = Field(..., description="Comment ID")
    fileId: str = Field(..., description="File ID")
    content: str = Field(..., description="Comment content")
    author: CommentAuthorModel = Field(..., description="Comment author")
    createdTime: str = Field(..., description="Creation time")
    modifiedTime: Optional[str] = Field(None, description="Modification time")
    deleted: Optional[bool] = Field(None, description="Whether the comment is deleted")


class ReplyModel(BaseModel):
    """Model for replies as stored in the JSON."""
    id: str = Field(..., description="Reply ID")
    commentId: str = Field(..., description="Comment ID")
    fileId: str = Field(..., description="File ID")
    content: str = Field(..., description="Reply content")
    author: CommentAuthorModel = Field(..., description="Reply author")
    createdTime: str = Field(..., description="Creation time")
    modifiedTime: Optional[str] = Field(None, description="Modification time")
    deleted: Optional[bool] = Field(None, description="Whether the reply is deleted")


class LabelModel(BaseModel):
    """Model for labels as stored in the JSON."""
    id: str = Field(..., description="Label ID")
    fileId: str = Field(..., description="File ID")
    name: str = Field(..., description="Label name")
    color: Optional[str] = Field(default="white", description="Label color")


class AccessProposalRequesterModel(BaseModel):
    """Model for access proposal requester."""
    displayName: str = Field(..., description="Display name")
    emailAddress: str = Field(..., description="Email address")


class AccessProposalModel(BaseModel):
    """Model for access proposals as stored in the JSON."""
    id: str = Field(..., description="Proposal ID")
    fileId: str = Field(..., description="File ID")
    role: str = Field(..., description="Requested role")
    state: str = Field(..., description="Proposal state")
    requester: AccessProposalRequesterModel = Field(..., description="Requester")
    createdTime: str = Field(..., description="Creation time")


class CountersModel(BaseModel):
    """Model for counters as stored in the JSON."""
    file: int = Field(default=0, description="File count")
    drive: int = Field(default=0, description="Drive count")
    comment: int = Field(default=0, description="Comment count")
    reply: int = Field(default=0, description="Reply count")
    label: int = Field(default=0, description="Label count")
    accessproposal: int = Field(default=0, description="Access proposal count")
    revision: int = Field(default=0, description="Revision count")
    spreadsheet: Optional[int] = Field(default=0, description="Spreadsheet count")
    document: Optional[int] = Field(default=0, description="Document count")


class UserDataModel(BaseModel):
    """Model for the nested user data structure."""
    about: UserAboutModel = Field(..., description="User about information")
    files: Dict[str, Union[FileModel, Dict[str, Any]]] = Field(default_factory=dict, description="User files (FileModel for pure Drive files, Dict for API-specific extensions)")
    drives: Dict[str, DriveModel] = Field(default_factory=dict, description="User drives")
    comments: Dict[str, CommentModel] = Field(default_factory=dict, description="User comments")
    replies: Dict[str, ReplyModel] = Field(default_factory=dict, description="User replies")
    labels: Dict[str, LabelModel] = Field(default_factory=dict, description="User labels")
    accessproposals: Dict[str, AccessProposalModel] = Field(default_factory=dict, description="User access proposals")
    counters: CountersModel = Field(default_factory=CountersModel, description="User counters")


class GdriveDB(BaseModel):
    """
    Main database model for Google Drive API simulation.
    This model represents the overall structure of the JSON database.
    
    The database organizes user data under users[userId], which stores:
    - 'about': User account metadata and Drive information
    - 'files': File metadata and content
    - 'drives': Shared drive information
    - 'comments': Comments on files
    - 'replies': Replies to comments
    - 'labels': Metadata labels for files
    - 'accessproposals': Access permission proposals
    - 'counters': Numeric counters for generating unique IDs
    """
    users: Dict[str, UserDataModel] = Field(default_factory=dict, description="Users data with nested structure")