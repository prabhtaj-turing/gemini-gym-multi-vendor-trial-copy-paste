"""
Database Models for Copilot API Simulation.

This module defines Pydantic models that represent the structure of the Copilot simulation database.
These models provide type safety, validation, and serve as the single source of truth for the database schema.

Reference: DBs/CopilotDefaultDB.json
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from common_utils.datetime_utils import normalize_datetime, InvalidDateTimeFormatError


# --- File System Models ---

class FileSystemItem(BaseModel):
    """Model for a file system item (file or directory)."""
    
    model_config = {"extra": "allow"}  # Allow extra fields like metadata
    
    path: str = Field(..., description="Absolute path of the file or directory")
    is_directory: bool = Field(..., description="Whether this item is a directory (True) or file (False)")
    content_lines: List[str] = Field(default_factory=list, description="List of content lines for files; empty for directories")
    size_bytes: int = Field(0, ge=0, description="Size of the file in bytes; 0 for directories")
    last_modified: str = Field(..., description="Last modified timestamp in ISO 8601 format")
    is_readonly: bool = Field(False, description="Whether the file or directory is read-only")

    @field_validator("last_modified")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """
        Validate and normalize timestamp format.
        
        Accepts various datetime formats and normalizes to ISO 8601 with Z suffix.
        """
        if not v or not v.strip():
            raise ValueError('Timestamp cannot be empty')
        
        normalized = normalize_datetime(v.strip(), "ISO_8601_UTC_Z")
        if not normalized:
            raise InvalidDateTimeFormatError(
                f"Invalid timestamp format: {v}. Expected ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
            )
        return normalized

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate that path is not empty and is absolute."""
        if not v or not v.strip():
            raise ValueError('Path cannot be empty')
        # Basic validation that path looks absolute (starts with /)
        if not v.strip().startswith('/'):
            raise ValueError('Path must be absolute (start with /)')
        return v.strip()

    @model_validator(mode="after")
    def validate_file_constraints(self) -> "FileSystemItem":
        """Validate constraints between fields."""
        # If it's a directory, content_lines should be empty
        if self.is_directory and len(self.content_lines) > 0:
            raise ValueError("Directories should not have content_lines")
        
        # If it's a file with content, size_bytes should be reasonable
        if not self.is_directory and len(self.content_lines) > 0 and self.size_bytes == 0:
            # This is a warning case - files with content should have size > 0
            # But we'll allow it for compatibility
            pass
        
        return self


class BackgroundProcess(BaseModel):
    """Model for a background process."""
    pid: int = Field(..., ge=1, description="Process ID")
    command: str = Field(..., description="The command that was executed")
    exec_dir: str = Field(..., description="The persistent temporary directory where the process runs")
    stdout_path: str = Field(..., description="Path to the stdout log file")
    stderr_path: str = Field(..., description="Path to the stderr log file")
    exitcode_path: str = Field(..., description="Path to the exitcode log file")
    last_stdout_pos: int = Field(0, ge=0, description="Tracks how much of the stdout log has been read")
    last_stderr_pos: int = Field(0, ge=0, description="Tracks how much of the stderr log has been read")

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Validate that command is not empty."""
        if not v or not v.strip():
            raise ValueError('Command cannot be empty')
        return v.strip()

    @field_validator("exec_dir", "stdout_path", "stderr_path", "exitcode_path")
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Validate that paths are not empty."""
        if not v or not v.strip():
            raise ValueError('Path cannot be empty')
        return v.strip()


# --- VS Code Models ---

class VSCodeExtension(BaseModel):
    """Model for a VS Code extension."""
    
    id: Optional[str] = Field(None, description="Unique identifier for the extension")
    name: Optional[str] = Field(None, description="Display name of the extension")
    version: Optional[str] = Field(None, description="Version of the extension")
    description: Optional[str] = Field(None, description="Description of the extension")
    publisher: Optional[str] = Field(None, description="Publisher of the extension")


class VSCodeContext(BaseModel):
    """Model for VS Code context information."""
    
    is_new_workspace_creation: bool = Field(True, description="Whether this is a new workspace creation")


class VSCodeAPIReference(BaseModel):
    """Model for VS Code API reference information."""
    
    api_name: Optional[str] = Field(None, description="Name of the API")
    description: Optional[str] = Field(None, description="Description of the API")
    url: Optional[str] = Field(None, description="URL to the API documentation")


# --- Main Database Model ---

class CopilotDB(BaseModel):
    """Main database model for Copilot simulation."""
    
    model_config = {
        "populate_by_name": True  # Allow both field name and alias
    }
    
    workspace_root: str = Field(..., description="The root directory of the workspace")
    cwd: str = Field(..., description="Current working directory within the workspace")
    file_system: Dict[str, FileSystemItem] = Field(
        default_factory=dict,
        description="File system representation, keyed by absolute path"
    )
    background_processes: Dict[str, BackgroundProcess] = Field(
        default_factory=dict,
        description="Background processes, keyed by PID (as string)"
    )
    vscode_extensions_marketplace: List[Any] = Field(
        default_factory=list,
        description="Available VS Code extensions in the marketplace"
    )
    vscode_context: VSCodeContext = Field(
        default_factory=VSCodeContext,
        description="VS Code context information"
    )
    installed_vscode_extensions: List[Any] = Field(
        default_factory=list,
        description="Installed VS Code extensions"
    )
    vscode_api_references: List[Any] = Field(
        default_factory=list,
        description="VS Code API references"
    )
    next_pid: int = Field(1, ge=1, description="Next available process ID", alias="_next_pid")

    @field_validator("workspace_root", "cwd")
    @classmethod
    def validate_workspace_paths(cls, v: str) -> str:
        """Validate workspace paths."""
        if not v or not v.strip():
            raise ValueError('Workspace path cannot be empty')
        if not v.strip().startswith('/'):
            raise ValueError('Workspace path must be absolute (start with /)')
        return v.strip()

    @model_validator(mode="after")
    def validate_database_structure(self) -> "CopilotDB":
        """Validate the overall database structure."""
        # Ensure workspace_root exists in file_system
        if self.workspace_root not in self.file_system:
            raise ValueError(f"workspace_root '{self.workspace_root}' must exist in file_system")
        
        # Ensure workspace_root is a directory
        workspace_item = self.file_system[self.workspace_root]
        if not workspace_item.is_directory:
            raise ValueError(f"workspace_root '{self.workspace_root}' must be a directory")
        
        # Ensure cwd is within workspace_root or is workspace_root
        if not self.cwd.startswith(self.workspace_root):
            raise ValueError(f"cwd '{self.cwd}' must be within workspace_root '{self.workspace_root}'")
        
        # Validate that all background process PIDs match their keys
        for pid_str, process in self.background_processes.items():
            try:
                pid_int = int(pid_str)
            except ValueError:
                raise ValueError(f"Background process key '{pid_str}' must be a valid integer")
            
            if process.pid != pid_int:
                raise ValueError(f"Background process PID {process.pid} does not match key '{pid_str}'")
        
        return self

    def get_next_pid(self) -> int:
        """
        Get and increment the next available PID.
        
        This method is necessary because it mutates the internal state
        of the next_pid counter and ensures proper PID management.
        """
        current_pid = self.next_pid
        self.next_pid += 1
        return current_pid

