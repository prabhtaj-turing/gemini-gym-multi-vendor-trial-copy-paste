"""
Database module for Copilot API simulation.
Provides in-memory database functionality and state management.
"""

import json
import datetime
from typing import Dict, Any
from pydantic import ValidationError
from common_utils.print_log import print_log
from common_utils.utils import get_minified_data
from common_utils.terminal_filesystem_utils import find_binary_files
from .db_models import CopilotDB

# Initial application state and file system representation.
# This dictionary serves as the in-memory database for the application.
# It is modified by API functions and can be persisted to/loaded from a file.
DB = {
    "workspace_root": "/home/user/project",
    "cwd": "/home/user/project/src",  # Current working directory within the workspace
    "environment": {
        "system": {},      # System-level environment variables
        "workspace": {},   # Workspace-level environment variables
        "session": {}      # Session-level environment variables (export, unset)
    },
    "file_system": {
        # Each key is an absolute path within the workspace.
        # 'is_directory': Python boolean True for directories, False for files.
        # 'content_lines': List of strings for file content; empty for directories.
        # 'size_bytes': Integer size; calculated for files, 0 for directories.
        # 'last_modified': ISO 8601 timestamp string.
        "/home/user/project": {
            "path": "/home/user/project",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-03-19T12:00:00Z",
            "is_readonly": False,

        },
        "/home/user/project/src": {
            "path": "/home/user/project/src",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-03-19T12:00:00Z",
            "is_readonly": True,
        }
    },
    "background_processes": {
        "12345": {
            "pid": 12345,
            "command": "sleep 10 && echo 'done'",
            "exec_dir": "/tmp/cmd_exec_abc123", # The persistent temporary directory
            "stdout_path": "/tmp/cmd_exec_abc123/stdout.log",
            "stderr_path": "/tmp/cmd_exec_abc123/stderr.log",
            "exitcode_path": "/tmp/cmd_exec_abc123/exitcode.log",
            "last_stdout_pos": 0, # Tracks how much of the stdout log has been read
            "last_stderr_pos": 0, # Tracks how much of the stderr log has been read
        }
    },
    "vscode_extensions_marketplace": [],
    "vscode_context": {"is_new_workspace_creation": True},
    "installed_vscode_extensions":[],
    "vscode_api_references": [],
    "_next_pid": 1
}


def get_database() -> CopilotDB:
    """
    Get the current database as a validated Pydantic model.
    
    This function returns the current in-memory DB as a CopilotDB Pydantic model,
    ensuring type safety and validation for all database access.
    
    Returns:
        CopilotDB: The current database as a validated Pydantic model
        
    Raises:
        ValidationError: If the current DB state is invalid
    """
    global DB
    try:
        return CopilotDB.model_validate(DB)
    except ValidationError as e:
        print_log(f"Error: Current DB state is invalid: {e}")
        raise


def load_database(db_data: Dict[str, Any]) -> None:
    """
    Load and validate database data, then update the global DB state.
    
    This function validates the input data against the CopilotDB schema before
    updating the global DB. This ensures that all database modifications go through
    Pydantic validation.
    
    Args:
        db_data (Dict[str, Any]): The database data to load and validate
        
    Raises:
        ValidationError: If the input data does not match the CopilotDB schema
    """
    global DB
    
    # Validate the input data against the Pydantic schema
    # Removing for now
    # try:
    #     validated_db = CopilotDB.model_validate(db_data)
    # except ValidationError as e:
    #     print_log(f"Error: Database validation failed: {e}")
    #     raise
    
    # Convert back to dict with aliases for storage
    # exclude_unset=True prevents adding default values for fields that weren't in the input
    #validated_dict = validated_db.model_dump(by_alias=True, exclude_unset=True)
    
    # Update the global DB
    DB.clear()
    DB.update(db_data)
    
    print_log("Database loaded and validated successfully.")


def save_state(filepath: str) -> None:
    """
    Persists the current state of the in-memory 'DB' to a JSON file.

    This function is typically used for saving the application's state for later retrieval,
    effectively creating a snapshot of the workspace and its contents.

    Args:
        filepath (str): The path to the file where the state should be saved.
                        The file will be overwritten if it already exists.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(DB, f, indent=2)  # Use indent for human-readable JSON output
    except IOError as e:
        raise  # Re-raise the exception if the caller needs to handle it

def load_state(filepath: str) -> None:
    """
    Loads the application state from a specified JSON file, replacing the
    current in-memory 'DB'.

    This function loads and validates the state against the CopilotDB schema
    before updating the database. This is typically used at application startup
    to restore a previously saved state.
    
    If the file is not found or cannot be decoded, the existing in-memory 'DB'
    (which might be the default initial state) is preserved, and a warning is issued.

    Args:
        filepath (str): The path to the JSON file from which to load the state.
        
    Raises:
        ValidationError: If the loaded state does not match the CopilotDB schema
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            loaded_state = json.load(f)
        
        # Use load_database for validation
        load_database(loaded_state)
        
    except FileNotFoundError:
        print_log(f"Warning: State file '{filepath}' not found. Using current or default DB state.")
    except json.JSONDecodeError as e:
        print_log(f"Error: Could not decode JSON from '{filepath}'. DB state may be invalid or outdated. Details: {e}")
    except ValidationError as e:
        print_log(f"Error: Loaded state does not match database schema: {e}")
        raise
    except Exception as e:
        print_log(f"An unexpected error occurred while loading state from '{filepath}': {e}") 

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    blacklist = [
        # $.. means "match this field recursively at any depth in the JSON"
        "$..timestamps",  # remove all "metadata" blocks
        "$..last_modified"  # remove last_modified
        # "$..size_bytes",  # remove size_bytes
    ]

    file_system = DB.get("file_system", {})
    binary_files = find_binary_files(file_system)
    # get_minified_data expects JSONPath, not Python-style dotted keys.
    # Each file path must be quoted as a key in JSONPath, e.g. file_system["/content/workspace/binary_file.bin"].content_lines[1:]
    blacklist.extend([
        f'file_system["{file}"].content_lines[1:]' for file in binary_files
    ])
    minified_data = get_minified_data(DB, blacklist)
    return minified_data