"""Pydantic models for gemini_cli database validation."""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Import custom errors for datetime validation
from .custom_errors import InvalidDateTimeFormatError

# Import timestamp utilities for validation
from common_utils.timestamp_utils import fix_malformed_timestamp, validate_iso_timestamp


# --- Reusable Validation Functions ---

def validate_iso_8601_string(v: Any) -> Optional[str]:
    """
    Reusable validator function to ensure a value is a valid ISO 8601 string.
    - If the value is None, it's returned as is (for optional fields).
    - If the value is a valid ISO 8601 string, it's returned as is (auto-fixes malformed formats).
    - Raises InvalidDateTimeFormatError for invalid string formats or non-string types.
    
    This follows the same standard as the GitHub API models.
    
    Standard format: YYYY-MM-DDTHH:MM:SS.ffffffZ
    Example: "2025-10-06T21:05:52.510677Z"
    """
    if v is None:
        return None
    
    if not isinstance(v, str):
        raise InvalidDateTimeFormatError(f"Datetime fields must be ISO 8601 strings, got {type(v).__name__}: {v}")
    
    # Auto-fix malformed timestamps (e.g., +00:00Z -> Z)
    fixed_value = fix_malformed_timestamp(v)
    
    # Validate the fixed timestamp
    if not validate_iso_timestamp(fixed_value):
        raise InvalidDateTimeFormatError(f"Invalid datetime format: {v} (after fix attempt: {fixed_value})")
    
    return fixed_value


class FileSystemEntry(BaseModel):
    """Model for individual file system entries."""
    path: str
    is_directory: bool
    content_lines: List[str] = Field(default_factory=list)
    size_bytes: int = 0
    last_modified: str
    
    class Config:
        extra = "forbid"


class GeminiCliDB(BaseModel):
    """Comprehensive Pydantic model for validating the entire GeminiCliDefaultDB.json structure."""
    
    workspace_root: str
    cwd: str
    file_system: Dict[str, Any]  # Use Any to avoid recursive validation issues
    memory_storage: Dict[str, Any] = Field(default_factory=dict)
    shell_config: Dict[str, Any] = Field(default_factory=dict)
    last_edit_params: Optional[Any] = None
    background_processes: Dict[str, Any] = Field(default_factory=dict)
    tool_metrics: Dict[str, Any] = Field(default_factory=dict)
    gitignore_patterns: List[str] = Field(default_factory=list)
    created: str = Field(alias='_created')  # Use alias for the underscore field
    
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
    
    @validator('created')
    def validate_created_timestamp(cls, v):
        """Validate that _created is a valid ISO 8601 timestamp."""
        return validate_iso_8601_string(v)
    
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
