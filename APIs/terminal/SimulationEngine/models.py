"""Pydantic models for terminal database validation."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Import custom errors for datetime validation
from .custom_errors import InvalidDateTimeFormatError


# --- Reusable Validation Functions ---

def validate_iso_8601_string(v: Any) -> Optional[str]:
    """
    Reusable validator function to ensure a value is a valid ISO 8601 string.
    - If the value is None, it's returned as is (for optional fields).
    - If the value is a valid ISO 8601 string, it's returned as is.
    - Raises InvalidDateTimeFormatError for invalid string formats or non-string types.
    
    This follows the same standard as the GitHub API models.
    """
    if v is None:
        return None
    if isinstance(v, str):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise InvalidDateTimeFormatError(f"Invalid datetime format: {v}")
    else:
        # Only strings (and None) are allowed
        raise InvalidDateTimeFormatError(f"Datetime fields must be ISO 8601 strings, got {type(v).__name__}: {v}")


class FileSystemEntry(BaseModel):
    """Model for individual file system entries."""
    path: str
    is_directory: bool
    content_lines: List[str] = Field(default_factory=list)
    size_bytes: int = 0
    last_modified: str
    
    class Config:
        extra = "forbid"


class TerminalDB(BaseModel):
    """Comprehensive Pydantic model for validating the Terminal API DB structure."""
    
    workspace_root: str
    cwd: str
    file_system: Dict[str, Any]  # Use Any to avoid recursive validation issues
    environment: Dict[str, Any] = Field(default_factory=dict)
    background_processes: Dict[str, Any] = Field(default_factory=dict)
    next_pid: int = Field(default=1, alias='_next_pid')
    
    class Config:
        extra = "forbid"
        allow_population_by_field_name = True
    
    @validator('file_system')
    def validate_file_system_entries(cls, v):
        """Validate that file system entries match their path keys."""
        for path_key, entry_data in v.items():
            if isinstance(entry_data, dict):
                # Basic validation of entry structure
                if 'path' not in entry_data:
                    raise ValueError(f"File system entry missing 'path' field: {path_key}")
                if entry_data['path'] != path_key:
                    raise ValueError(f"Path key '{path_key}' doesn't match entry path '{entry_data['path']}'")
                # Validate required fields
                required_fields = ['is_directory', 'content_lines', 'size_bytes', 'last_modified']
                for field in required_fields:
                    if field not in entry_data:
                        raise ValueError(f"File system entry missing required field '{field}': {path_key}")
        return v
    
    @validator('workspace_root', 'cwd')
    def validate_paths(cls, v):
        """Validate that paths are non-empty strings."""
        if not v or not isinstance(v, str):
            raise ValueError("Path must be a non-empty string")
        return v


class DatabaseFileSystemEntry(BaseModel):
    """Pydantic model for validating file system entries as stored in the database."""
    
    # Core file/directory attributes
    path: str
    is_directory: bool
    content_lines: List[str] = Field(default_factory=list)
    size_bytes: int = 0
    last_modified: str
    
    class Config:
        extra = "forbid"
    
    @validator('path')
    def validate_path(cls, v):
        """Validate path is a non-empty string."""
        if not v or not isinstance(v, str):
            raise ValueError("Path must be a non-empty string")
        return v
    
    @validator('content_lines')
    def validate_content_lines(cls, v, values):
        """Validate content_lines consistency with is_directory."""
        is_directory = values.get('is_directory', False)
        if is_directory and v:
            raise ValueError("Directories should have empty content_lines")
        return v
    
    @validator('size_bytes')
    def validate_size_bytes(cls, v):
        """Validate size_bytes is non-negative."""
        if v < 0:
            raise ValueError("size_bytes must be non-negative")
        return v
    
    @validator('last_modified')
    def validate_last_modified(cls, v):
        """Validate last_modified is a valid ISO 8601 timestamp."""
        return validate_iso_8601_string(v)
