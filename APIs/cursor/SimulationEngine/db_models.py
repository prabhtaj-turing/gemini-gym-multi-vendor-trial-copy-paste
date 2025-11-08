from typing import Dict, Optional, List
from pydantic import BaseModel, Field


# ---------------------------
# Internal Storage Models
# ---------------------------

class FileSystemEntry(BaseModel):
    """Represents a file or directory in the file system."""
    path: str = Field(..., description="Absolute or workspace-relative path of the entry.")
    is_directory: bool = Field(..., description="True if the entry is a directory.")
    content_lines: List[str] = Field(
        default_factory=list,
        description="File content as list of lines; empty for directories."
    )
    size_bytes: int = Field(0, description="Size of the entry in bytes.")
    last_modified: str = Field(
        "",
        description="ISO 8601 timestamp of the last modification (e.g., '2024-01-01T12:00:00Z')."
    )

class PullRequest(BaseModel):
    """Represents a simplified pull request entry."""
    title: str = Field(..., description="PR title.")
    author: str = Field(..., description="PR author username.")
    description: str = Field(..., description="PR description, may contain markdown.")
    diff: str = Field(..., description="Unified diff for the PR.")


class Commit(BaseModel):
    """Represents a simplified commit entry."""
    author: str = Field(..., description="Commit author username.")
    message: str = Field(..., description="Commit message.")
    diff: str = Field(..., description="Unified diff for the commit.")


class KnowledgeItem(BaseModel):
    """Represents a knowledge base item stored in Cursor state."""
    title: str = Field(..., description="Knowledge item title.")
    knowledge_to_store: str = Field(..., description="Knowledge body to store.")


class LastEditParams(BaseModel):
    """Parameters captured from the last edit_file call."""
    target_file: str = Field(..., description="Target file path of the edit.")
    code_edit: str = Field(..., description="Edit diff payload applied to the file.")
    instructions: str = Field(..., description="High-level instruction describing the edit.")
    explanation: Optional[str] = Field(None, description="Optional explanation text.")


# ---------------------------
# Root Database Model
# ---------------------------

class CursorDB(BaseModel):
    """Root model that validates the entire Cursor default database structure."""
    workspace_root: str = Field(..., description="Workspace root path.")
    cwd: str = Field(..., description="Current working directory.")
    file_system: Dict[str, FileSystemEntry] = Field(
        default_factory=dict,
        description="Map of file paths to structured file entries (metadata, content, etc).",
    )
    last_edit_params: Optional[LastEditParams] = Field(
        None, description="Parameters of the last edit operation, if any."
    )
    background_processes: Dict[str, str] = Field(
        default_factory=dict, description="Map of PID (string) to command string."
    )
    available_instructions: Dict[str, str] = Field(
        default_factory=dict, description="Named instruction text snippets."
    )
    next_pid: int = Field(
        ..., description="Next process id to allocate.", ge=1, validation_alias="_next_pid"
    )
    pull_requests: Dict[str, PullRequest] = Field(
        default_factory=dict, description="Map of PR id to pull request entries."
    )
    commits: Dict[str, Commit] = Field(
        default_factory=dict, description="Map of commit hash to commit entries."
    )
    knowledge_base: Dict[str, KnowledgeItem] = Field(
        default_factory=dict, description="Map of knowledge id to knowledge items."
    )
    next_knowledge_id: int = Field(
        ..., description="Next knowledge id to allocate.", ge=0, validation_alias="_next_knowledge_id"
    )

    class Config:
        str_strip_whitespace = True
        allow_population_by_field_name = True


