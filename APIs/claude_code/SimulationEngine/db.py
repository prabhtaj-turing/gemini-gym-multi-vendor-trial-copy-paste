from __future__ import annotations

import json
import os
import datetime
from typing import Dict, Any

from common_utils.utils import get_minified_data
from common_utils.terminal_filesystem_utils import find_binary_files

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "DBs",
    "ClaudeCodeDefaultDB.json",
)

_FALLBACK_DB: Dict[str, Any] = {
    "workspace_root": "/home/user/project",
    "cwd": "/home/user/project",
    "file_system": {},
    "memory_storage": {},
    "last_edit_params": None,
    "background_processes": {},
    "tool_metrics": {},
    "_created": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
}


def _load_default_state() -> Dict[str, Any]:
    try:
        with open(_DEFAULT_DB_PATH, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except FileNotFoundError:
        state = _FALLBACK_DB.copy()

    if "memory_storage" not in state:
        state["memory_storage"] = {}

    return state


DB: Dict[str, Any] = _load_default_state()


def save_state(filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(DB, fh, indent=2)


def load_state(filepath: str) -> None:
    global DB
    with open(filepath, "r", encoding="utf-8") as fh:
        new_state = json.load(fh)

    if "memory_storage" not in new_state:
        new_state["memory_storage"] = {}

    DB.clear()
    DB.update(new_state)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    
    This function removes metadata that can be large or frequently changing:
    - All "timestamps" metadata recursively
    - All "last_modified" fields recursively  
    - Binary file content (keeping only first line as marker)
    
    Returns:
        dict: Minified version of the DB state with reduced data size
    """
    global DB
    blacklist = [
        # $.. means "match this field recursively at any depth in the JSON"
        "$..timestamps",       # remove all "timestamps" metadata blocks
        "$..last_modified"     # remove last_modified fields
        # "$..size_bytes",     # keep size_bytes for now (could be removed if needed)
    ]

    file_system = DB.get("file_system", {})
    binary_files = find_binary_files(file_system)
    
    # Add binary file content exclusion (keep only first line which contains the marker)
    # get_minified_data expects JSONPath format like: file_system["/path/to/file"].content_lines[1:]
    blacklist.extend([
        f'file_system["{file_path}"].content_lines[1:]' for file_path in binary_files
    ])
    
    minified_data = get_minified_data(DB, blacklist)
    return minified_data

def reset_db():
    """Reset database to initial state"""
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()