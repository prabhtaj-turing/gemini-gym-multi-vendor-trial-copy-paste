from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

def utc_now_iso() -> str:
    """Helper function to get current UTC time as ISO format string"""
    return datetime.utcnow().isoformat() + "Z"

class ListItem(BaseModel):
    """Represents an individual item within a list"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    completed: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

    @validator('content', pre=True)
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("List item content cannot be empty")
        return v

class Note(BaseModel):
    """Represents a text note with content history"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    content: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    content_history: List[str] = Field(default_factory=list)

    @validator('title', pre=True, always=True)
    def set_default_title(cls, v, values):
        if not v and 'content' in values and values['content']:
            return values['content'][:50] + ("..." if len(values['content']) > 50 else "")
        return v

class ListModel(BaseModel):
    """Represents a collection of list items"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    items: Dict[str, ListItem] = Field(default_factory=dict)  # item_id -> ListItem
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    item_history: Dict[str, List[str]] = Field(default_factory=dict)  # item_id -> content history

    @validator('title', pre=True, always=True)
    def set_default_title(cls, v, values):
        if not v and 'items' in values and values['items']:
            first_item = next(iter(values['items'].values()))
            return f"List: {first_item.content[:30]}..."
        return v


class OperationLog(BaseModel):
    """Tracks operations for undo functionality"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str
    target_id: str  # ID of note/list/item affected
    parameters: dict
    timestamp: str = Field(default_factory=utc_now_iso)
    snapshot: Optional[Union[Note, ListModel, ListItem, dict]] = None # State before operation

class NotesAndListsDB(BaseModel):
    """In-memory database schema for NotesAndLists simulation"""
    notes: Dict[str, Note] = Field(default_factory=dict)       # note_id -> Note
    lists: Dict[str, ListModel] = Field(default_factory=dict)        # list_id -> ListModel
    operation_log: Dict[str, OperationLog] = Field(default_factory=dict)  # op_id -> OperationLog
    title_index: Dict[str, List[str]] = Field(default_factory=dict)       # title -> [item_ids]
    content_index: Dict[str, List[str]] = Field(default_factory=dict)     # content -> [item_ids]

    def search(self, query: str, hint: Optional[str] = None) -> Dict[str, Union[Note, ListModel]]:
        """Search notes and lists by title/content using fuzzy search engine"""
        results = {}
        
        try:
            # Use fuzzy search engine
            from .utils import find_items_by_search
            found_notes, found_lists = find_items_by_search(query)
            
            # Add found notes to results
            if hint in (None, "NOTE", "ANY"):
                for note_id in found_notes:
                    if note_id in self.notes:
                        results[note_id] = self.notes[note_id]
            
            # Add found lists to results
            if hint in (None, "LIST", "ANY"):
                for list_id in found_lists:
                    if list_id in self.lists:
                        results[list_id] = self.lists[list_id]
            
            # If fuzzy search returned no results, fall back to simple search
            if not results:
                # Fallback to simple text search
                # Search notes
                if hint in (None, "NOTE", "ANY"):
                    for note_id, note in self.notes.items():
                        if (query.lower() in (note.title or "").lower() or 
                            query.lower() in note.content.lower()):
                            results[note_id] = note
                
                # Search lists
                if hint in (None, "LIST", "ANY"):
                    for list_id, lst in self.lists.items():
                        if (query.lower() in (lst.title or "").lower() or 
                            any(query.lower() in item.content.lower() for item in lst.items.values())):
                            results[list_id] = lst
                        
        except Exception as e:
            # Fallback to simple text search
            # Search notes
            if hint in (None, "NOTE", "ANY"):
                for note_id, note in self.notes.items():
                    if (query.lower() in (note.title or "").lower() or 
                        query.lower() in note.content.lower()):
                        results[note_id] = note
            
            # Search lists
            if hint in (None, "LIST", "ANY"):
                for list_id, lst in self.lists.items():
                    if (query.lower() in (lst.title or "").lower() or 
                        any(query.lower() in item.content.lower() for item in lst.items.values())):
                        results[list_id] = lst
        
        return results

    def get_item(self, item_id: str) -> Optional[Union[Note, ListModel, ListItem]]:
        """Retrieve any item by ID (note, list, or list item)"""
        if item_id in self.notes:
            return self.notes[item_id]
        if item_id in self.lists:
            return self.lists[item_id]
        
        # Search for list items
        for lst in self.lists.values():
            if item_id in lst.items:
                return lst.items[item_id]
        
        return None

    def log_operation(
        self,
        operation_type: str,
        target_id: str,
        parameters: dict,
        snapshot: Union[Note, ListModel, ListItem]
    ) -> str:
        """Record an operation in the log"""
        op_log = OperationLog(
            operation_type=operation_type,
            target_id=target_id,
            parameters=parameters,
            snapshot=snapshot
        )
        self.operation_log[op_log.id] = op_log
        return op_log.id