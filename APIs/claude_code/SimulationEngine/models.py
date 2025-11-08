# APIs/claude_code/SimulationEngine/models.py

from pydantic import BaseModel
from typing import List, Optional

class BashRequest(BaseModel):
    command: str
    timeout: int = 600000

class ReadFileRequest(BaseModel):
    file_path: str
    offset: int = 0
    limit: int = -1

class ListFilesRequest(BaseModel):
    path: str

class SearchGlobRequest(BaseModel):
    pattern: str
    path: Optional[str] = None

class GrepRequest(BaseModel):
    pattern: str
    path: Optional[str] = None
    include: Optional[str] = None

class EditFileRequest(BaseModel):
    file_path: str
    content: str
    
class TodoItem(BaseModel):
    id: str
    content: str
    status: str

class TodoWriteRequest(BaseModel):
    merge: bool
    todos: List[TodoItem]

class WebFetchRequest(BaseModel):
    url: str

class TaskRequest(BaseModel):
    description: str
    prompt: str
    subagent_type: str
