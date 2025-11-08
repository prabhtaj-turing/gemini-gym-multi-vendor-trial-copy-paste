import datetime as dt
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# ---------------------------
# Internal Storage Models
# ---------------------------

class PermissionsStorage(BaseModel):
    """Internal storage model for file system permissions."""
    mode: Optional[int] = Field(None, description="The permission mode of the file or directory.")
    uid: Optional[int] = Field(None, description="The user ID of the owner.")
    gid: Optional[int] = Field(None, description="The group ID of the owner.")

class AttributesStorage(BaseModel):
    """Internal storage model for file system attributes."""
    is_symlink: bool = Field(..., description="Indicates if the file is a symbolic link.")
    symlink_target: Optional[str] = Field(None, description="The target of the symbolic link, if it is one.")
    is_hidden: bool = Field(..., description="Indicates if the file is hidden.")
    is_readonly: Optional[bool] = Field(None, description="Indicates if the file is read-only.")

class TimestampsStorage(BaseModel):
    """Internal storage model for file system timestamps."""
    access_time: Optional[dt.datetime] = Field(None, description="The last access time.")
    modify_time: Optional[dt.datetime] = Field(None, description="The last modification time.")
    change_time: Optional[dt.datetime] = Field(None, description="The last status change time.")

class MetadataStorage(BaseModel):
    """Internal storage model for file system metadata."""
    timestamps: TimestampsStorage = Field(..., description="Timestamp information for the file or directory.")
    attributes: AttributesStorage = Field(..., description="Attribute information for the file or directory.")
    permissions: PermissionsStorage = Field(..., description="Permission information for the file or directory.")

class FileSystemNodeStorage(BaseModel):
    """Internal storage model for a node in the file system (a file or directory)."""
    path: str = Field(..., description="The absolute path of the file or directory.", min_length=1)
    is_directory: bool = Field(..., description="Indicates if the node is a directory.")
    content_lines: Optional[List[str]] = Field(None, description="The content of the file, as a list of strings.")
    size_bytes: Optional[int] = Field(None, description="The size of the file in bytes.")
    last_modified: Optional[dt.datetime] = Field(None, description="The last modified timestamp.")
    metadata: Optional[MetadataStorage] = Field(None, description="Detailed metadata for the file or directory.")

class EnvironmentStorage(BaseModel):
    """Internal storage model for environment variables."""
    system: Dict[str, str] = Field(default_factory=dict, description="System-level environment variables.")
    workspace: Dict[str, str] = Field(default_factory=dict, description="Workspace-level environment variables.")
    session: Dict[str, str] = Field(default_factory=dict, description="Session-level environment variables.")

# ---------------------------
# Root Database Model
# ---------------------------

class TerminalDB(BaseModel):
    """Root model that validates the entire Terminal database structure."""
    workspace_root: Optional[str] = Field(None, description="The root directory of the workspace.", min_length=1)
    cwd: Optional[str] = Field(None, description="The current working directory.", min_length=1)
    file_system: Dict[str, FileSystemNodeStorage] = Field(
        default_factory=dict,
        description="A dictionary representing the file system, keyed by absolute path."
    )
    environment: EnvironmentStorage = Field(
        default_factory=EnvironmentStorage,
        description="The environment variables for the terminal session."
    )
    background_processes: Dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary of running background processes, keyed by PID."
    )
    next_pid: Optional[int] = Field(None, alias="_next_pid")

    class Config:
        str_strip_whitespace = True
        populate_by_name = True
