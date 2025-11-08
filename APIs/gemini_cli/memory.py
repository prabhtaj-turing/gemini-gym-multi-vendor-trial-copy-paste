"""Gemini-CLI memory tool implementations.

This module provides functionality for saving and managing memories in a persistent
knowledge base
"""
from __future__ import annotations
from common_utils.tool_spec_decorator import tool_spec

from typing import Dict, Any, List, Optional
import os
import json

from .SimulationEngine.db import DB
from common_utils.log_complexity import log_complexity
from .SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotAvailableError
from .SimulationEngine.file_utils import _is_within_workspace
from .SimulationEngine.utils import (
    GEMINI_CONFIG_DIR, 
    MEMORY_SECTION_HEADER,
    get_current_gemini_md_filename,
    _get_global_memory_file_path,
    _ensure_newline_separation,
    _persist_db_state,
    conditional_common_file_system_wrapper
)


def _perform_add_memory_entry(text: str, memory_file_path: str) -> None:
    """Add a memory entry to the separate memory storage (not in file_system).
    
    Args:
        text (str): The memory text to add.
        memory_file_path (str): The logical path to the memory file.
        
    Raises:
        ValueError: If the memory cannot be added due to memory system issues.
    """
    try:
        # Process the text similar to TypeScript implementation
        processed_text = text.strip()
        processed_text = processed_text.lstrip('- ').strip()  # Remove leading hyphens
        new_memory_item = f"- {processed_text}"
        
        # Get the separate memory storage from DB (NOT file_system)
        memory_storage = DB.setdefault("memory_storage", {})
        
        # Ensure the directory exists in memory storage
        dir_path = os.path.dirname(memory_file_path)
        if dir_path not in memory_storage:
            memory_storage[dir_path] = {
                "path": dir_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": "2025-01-01T00:00:00Z"
            }
        
        # Read existing content or create new file in memory storage
        content = ""
        if memory_file_path in memory_storage:
            content_lines = memory_storage[memory_file_path].get("content_lines", [])
            content = "".join(content_lines)
        
        # Find or create the memory section
        header_index = content.find(MEMORY_SECTION_HEADER)
        
        if header_index == -1:
            # Header not found, append header and entry
            separator = _ensure_newline_separation(content)
            content += f"{separator}{MEMORY_SECTION_HEADER}\n{new_memory_item}\n"
        else:
            # Header found, insert the new memory entry
            start_of_section_content = header_index + len(MEMORY_SECTION_HEADER)
            end_of_section_index = content.find('\n## ', start_of_section_content)
            if end_of_section_index == -1:
                end_of_section_index = len(content)
            
            before_section_marker = content[:start_of_section_content].rstrip()
            section_content = content[start_of_section_content:end_of_section_index].rstrip()
            after_section_marker = content[end_of_section_index:]
            
            section_content += f"\n{new_memory_item}"
            content = f"{before_section_marker}\n{section_content.lstrip()}\n{after_section_marker}".rstrip() + '\n'
        
        # Update the memory storage entry (separate from file_system)
        content_lines = content.splitlines(keepends=True)
        if content_lines and not content_lines[-1].endswith('\n'):
            content_lines[-1] += '\n'
        
        memory_storage[memory_file_path] = {
            "path": memory_file_path,
            "is_directory": False,
            "content_lines": content_lines,
            "size_bytes": len(content.encode('utf-8')),
            "last_modified": "2025-01-01T00:00:00Z"
        }
        
    except Exception as error:
        raise ValueError(f"Failed to add memory entry: {str(error)}")



@log_complexity
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'save_memory',
        'description': """ Save a specific piece of information or fact to long-term memory.
        
        Use this function when the user explicitly asks you to remember something,
        or when they state a clear, concise fact that seems important to retain
        for future interactions. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fact': {
                    'type': 'string',
                    'description': """ The specific fact or piece of information to remember.
                    Should be a clear, self-contained statement. """
                }
            },
            'required': [
                'fact'
            ]
        }
    }
)
def save_memory(fact: str) -> Dict[str, Any]:
    """Save a specific piece of information or fact to long-term memory.
    
    Use this function when the user explicitly asks you to remember something,
    or when they state a clear, concise fact that seems important to retain
    for future interactions.
    
    Args:
        fact (str): The specific fact or piece of information to remember.
                   Should be a clear, self-contained statement.
    
    Returns:
        Dict[str, Any]: A dictionary indicating the outcome:
            - 'success' (bool): True if the memory was saved successfully.
            - 'message' (str): A message describing the outcome.
    
    Raises:
        InvalidInputError: If the fact is empty or not a string.
        WorkspaceNotAvailableError: If workspace_root is not configured.
        ValueError: If the memory cannot be saved due to file system issues.
    """
    # Validate input
    if not isinstance(fact, str):
        raise InvalidInputError("Parameter 'fact' must be a string.")
    
    if not fact or not fact.strip():
        raise InvalidInputError("Parameter 'fact' must be a non-empty string.")
    
    # Check workspace configuration
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")
    
    try:
        memory_file_path = _get_global_memory_file_path()
        
        # Ensure the path is within workspace (for security)
        if not _is_within_workspace(memory_file_path, workspace_root):
            # If not within workspace, create it in workspace
            memory_file_path = os.path.join(workspace_root, GEMINI_CONFIG_DIR, get_current_gemini_md_filename())
        
        _perform_add_memory_entry(fact, memory_file_path)
        
        _persist_db_state()
        
        success_message = f"Okay, I've remembered that: \"{fact}\""
        return {
            "success": True,
            "message": success_message
        }
        
    except Exception as error:
        error_message = f"Failed to save memory: {str(error)}"
        return {
            "success": False,
            "message": error_message
        }


 