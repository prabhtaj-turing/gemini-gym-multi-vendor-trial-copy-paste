import json
from typing import Any, Dict, Literal
import datetime
import os

# Define type aliases for clarity
DbType = Dict[str, Any]
DbFormat = Literal["cursor", "copilot", "gemini", "terminal"]

# --- Helper Functions ---

def _strip_file_system_metadata(file_system: DbType, key_to_strip: str) -> DbType:
    """Helper to remove a specific metadata key from all file system entries."""
    new_fs = {}
    for path, data in file_system.items():
        new_data = data.copy()
        new_data.pop(key_to_strip, None)
        new_fs[path] = new_data
    return new_fs

def _add_terminal_metadata(file_system: DbType) -> DbType:
    """Helper to add default terminal-specific metadata to file system entries."""
    new_fs = {}
    for path, data in file_system.items():
        new_data = data.copy()
        if "metadata" not in new_data:
            new_data["metadata"] = {
                "timestamps": {
                    "access_time": data.get("last_modified", "2025-01-01T00:00:00Z"),
                    "modify_time": data.get("last_modified", "2025-01-01T00:00:00Z"),
                    "change_time": data.get("last_modified", "2025-01-01T00:00:00Z"),
                },
                "attributes": {"is_symlink": False, "symlink_target": None, "is_hidden": False, "is_readonly": False},
                "permissions": {"mode": 420, "uid": 1000, "gid": 1000},
            }
            if new_data.get("is_directory"):
                new_data["metadata"]["permissions"]["mode"] = 493
        new_fs[path] = new_data
    return new_fs

# --- Translation Logic Functions ---

def _cursor_to_gemini(db: DbType) -> DbType:
    gemini_db = {
        "workspace_root": db.get("workspace_root"),
        "cwd": db.get("cwd"),
        "file_system": _strip_file_system_metadata(db.get("file_system", {}), "git_blame"),
        "last_edit_params": db.get("last_edit_params"),
        "background_processes": db.get("background_processes", {}),
        "tool_metrics": {},
        "_created": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
    }
    gitignore_file = db.get("file_system", {}).get(f"{db.get('workspace_root')}/.gitignore")
    gemini_db["gitignore_patterns"] = [line.strip() for line in gitignore_file.get("content_lines", [])] if gitignore_file else []
    return gemini_db

def _gemini_to_cursor(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"),
        "cwd": db.get("cwd"),
        "file_system": db.get("file_system", {}),
        "last_edit_params": db.get("last_edit_params"),
        "background_processes": db.get("background_processes", {}),
        "available_instructions": {}, "pull_requests": {}, "commits": {}, "knowledge_base": {},
        "_next_knowledge_id": 1, "_next_pid": 1,
    }

def _cursor_to_copilot(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": _strip_file_system_metadata(db.get("file_system", {}), "git_blame"),
        "background_processes": db.get("background_processes", {}), "_next_pid": db.get("_next_pid", 1),
    }

def _copilot_to_cursor(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": db.get("file_system", {}), "background_processes": db.get("background_processes", {}),
        "_next_pid": db.get("_next_pid", 1), "last_edit_params": None, "available_instructions": {},
        "pull_requests": {}, "commits": {}, "knowledge_base": {}, "_next_knowledge_id": 1,
    }

def _gemini_to_copilot(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": db.get("file_system", {}), "background_processes": db.get("background_processes", {}),
        "_next_pid": 1,
    }

def _copilot_to_gemini(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": db.get("file_system", {}), "background_processes": db.get("background_processes", {}),
        "last_edit_params": None, "tool_metrics": {}, "gitignore_patterns": [],
        "_created": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
    }

def _terminal_to_cursor(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        # Preserve existing metadata; synthesize if missing to match Cursor schema
        "file_system": _add_terminal_metadata(db.get("file_system", {})),
        "background_processes": db.get("background_processes", {}), "_next_pid": db.get("_next_pid", 1),
        "last_edit_params": None, "available_instructions": {}, "pull_requests": {},
        "commits": {}, "knowledge_base": {}, "_next_knowledge_id": 1,
    }

def _cursor_to_terminal(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": _add_terminal_metadata(_strip_file_system_metadata(db.get("file_system", {}), "git_blame")),
        "environment": {"system": {}, "workspace": {}, "session": {}},
        "background_processes": db.get("background_processes", {}), "_next_pid": db.get("_next_pid", 1),
    }

def _terminal_to_gemini(db: DbType) -> DbType:
    # Preserve metadata if present; synthesize defaults when missing (same behavior as gemini -> terminal)
    gemini_db = {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": _add_terminal_metadata(db.get("file_system", {})),
        "last_edit_params": None, "background_processes": db.get("background_processes", {}),
        "tool_metrics": {}, "_created": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
    }
    gitignore_file = db.get("file_system", {}).get(f"{db.get('workspace_root')}/.gitignore")
    gemini_db["gitignore_patterns"] = [line.strip() for line in gitignore_file.get("content_lines", [])] if gitignore_file else []
    return gemini_db

def _gemini_to_terminal(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": _add_terminal_metadata(db.get("file_system", {})),
        "environment": {"system": {}, "workspace": {}, "session": {}},
        "background_processes": db.get("background_processes", {}), "_next_pid": 1,
    }

def _terminal_to_copilot(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": _strip_file_system_metadata(db.get("file_system", {}), "metadata"),
        "background_processes": db.get("background_processes", {}), "_next_pid": db.get("_next_pid", 1),
    }

def _copilot_to_terminal(db: DbType) -> DbType:
    return {
        "workspace_root": db.get("workspace_root"), "cwd": db.get("cwd"),
        "file_system": _add_terminal_metadata(db.get("file_system", {})),
        "environment": {"system": {}, "workspace": {}, "session": {}},
        "background_processes": db.get("background_processes", {}), "_next_pid": db.get("_next_pid", 1),
    }

# --- Main Translator ---

def translate_and_save(source_path: str, target_path: str, source_format: DbFormat, target_format: DbFormat):
    """
    Translates a DB from a source format to a target format and saves it to a file.
    """
    if source_format == target_format:
        return

    translation_map = {
        ("cursor", "gemini"): _cursor_to_gemini, ("gemini", "cursor"): _gemini_to_cursor,
        ("cursor", "copilot"): _cursor_to_copilot, ("copilot", "cursor"): _copilot_to_cursor,
        ("gemini", "copilot"): _gemini_to_copilot, ("copilot", "gemini"): _copilot_to_gemini,
        ("terminal", "cursor"): _terminal_to_cursor, ("cursor", "terminal"): _cursor_to_terminal,
        ("terminal", "gemini"): _terminal_to_gemini, ("gemini", "terminal"): _gemini_to_terminal,
        ("terminal", "copilot"): _terminal_to_copilot, ("copilot", "terminal"): _copilot_to_terminal,
    }

    handler = translation_map.get((source_format, target_format))
    if not handler:
        raise NotImplementedError(f"Translation from '{source_format}' to '{target_format}' is not supported.")

    print(f"Translating {source_format.upper()} ({os.path.basename(source_path)}) -> {target_format.upper()} ({os.path.basename(target_path)})")
    
    with open(source_path, "r") as f:
        source_db = json.load(f)
    
    translated_db = handler(source_db)
    
    with open(target_path, "w") as f:
        json.dump(translated_db, f, indent=2)
