from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class FileSystemEntry(BaseModel):
    """Represents a file or directory in the file system."""
    path: str
    is_directory: bool
    content_lines: List[str] = Field(default_factory=list)
    size_bytes: int = 0
    last_modified: str = ""
    metadata: Optional[Dict[str, Any]] = None


class EditParams(BaseModel):
    """Parameters for the last code modification operation."""
    target_file: str
    code_edit: str
    instructions: str
    explanation: str


class PullRequest(BaseModel):
    """Mock pull request data."""
    title: str
    author: str
    description: str
    diff: str


class Commit(BaseModel):
    """Mock commit data."""
    author: str
    message: str
    diff: str


class KnowledgeEntry(BaseModel):
    """Knowledge base entry."""
    title: str
    knowledge_to_store: str


class CursorDB(BaseModel):
    """Main database model for the cursor API."""
    workspace_root: str = ""
    cwd: str = ""
    file_system: Dict[str, FileSystemEntry] = Field(default_factory=dict)
    last_edit_params: Optional[EditParams] = None
    background_processes: Dict[str, str] = Field(default_factory=dict)
    available_instructions: Dict[str, str] = Field(default_factory=dict)
    _next_pid: int = 1
    pull_requests: Dict[str, PullRequest] = Field(default_factory=dict)
    commits: Dict[str, Commit] = Field(default_factory=dict)
    knowledge_base: Dict[str, KnowledgeEntry] = Field(default_factory=dict)
    _next_knowledge_id: int = 2
