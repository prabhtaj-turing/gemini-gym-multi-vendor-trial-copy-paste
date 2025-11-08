"""Gemini-CLI file-system tool implementations (stub).

Each function will be fleshed out incrementally.  For now they simply raise
NotImplementedError so the import machinery works while development is in
progress.
"""
from __future__ import annotations
from common_utils.tool_spec_decorator import tool_spec

from typing import Dict, Any, List, Optional  # CRITICAL: mandated import order

import datetime
import os
import re
import fnmatch
import mimetypes
import datetime

from .SimulationEngine.db import DB
from common_utils.log_complexity import log_complexity
from .SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotAvailableError
from .SimulationEngine.file_utils import (
    _is_within_workspace,
    _should_ignore,
    _is_ignored as _fs_is_ignored,
    detect_file_type,
    apply_replacement,
    correct_string_issues,
    glob_match,
    filter_gitignore,
)
from .SimulationEngine.utils import resolve_workspace_path
from .SimulationEngine.utils import conditional_common_file_system_wrapper

@log_complexity  # type: ignore[attr-defined]
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'list_directory',
        'description': 'List the direct children of a workspace directory.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': """ Directory path to list. Can be absolute or relative to workspace root.
                    Empty string or '.' refers to the workspace root itself. Leading slashes are stripped. """
                },
                'ignore': {
                    'type': 'array',
                    'description': """ Glob patterns to exclude from the
                    listing, for example ['*.log', 'node_modules']. Defaults to None. """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'path'
            ]
        }
    }
)
def list_directory(
    path: str,
    *,
    ignore: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """List the direct children of a workspace directory.

    Args:
        path (str): Directory path to list. Can be absolute or relative to workspace root.
            Empty string or '.' refers to the workspace root itself. Leading slashes are stripped.
        ignore (Optional[List[str]]): Glob patterns to exclude from the
            listing, for example ['*.log', 'node_modules']. Defaults to None.

    Returns:
        List[Dict[str, Any]]: Each dictionary has these keys: name, path, is_directory, size, modifiedTime.

    Raises:
        InvalidInputError: If path is invalid type or outside the workspace root.
        WorkspaceNotAvailableError: If workspace_root is not configured.
        FileNotFoundError: If path does not exist in the DB.
        NotADirectoryError: If path points to a file instead of a directory.
    """

    # ---------------- Validation ----------------
    if not isinstance(path, str):
        raise InvalidInputError("'path' must be a string")

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # Resolve path with respect to the workspace (supports relative paths, empty string, and ".")
    resolved_path = resolve_workspace_path(path, workspace_root)

    if not os.path.isabs(resolved_path):
        raise InvalidInputError("Resolved path must be absolute")

    if not _is_within_workspace(resolved_path, workspace_root):
        raise InvalidInputError("Path resolves outside workspace root")

    # Validate ignore patterns
    if ignore is not None:
        if not isinstance(ignore, list):
            raise InvalidInputError("'ignore' must be a list of glob pattern strings or None")
        for pat in ignore:
            if not isinstance(pat, str):
                raise InvalidInputError("All items in 'ignore' must be strings")

    fs = DB.setdefault("file_system", {})
    entry = fs.get(resolved_path)
    if not entry:
        raise FileNotFoundError(resolved_path)
    if not entry.get("is_directory", False):
        raise NotADirectoryError(resolved_path)

    # ---------------- Listing ----------------
    results: List[Dict[str, Any]] = []
    for abs_child, meta in fs.items():
        if abs_child == resolved_path:
            continue
        if os.path.dirname(os.path.normpath(abs_child)) != os.path.normpath(resolved_path):
            continue
        name = os.path.basename(abs_child)
        if _should_ignore(name, ignore):
            continue
        results.append(
            {
                "name": name,
                "path": meta.get("path", abs_child),
                "is_directory": meta.get("is_directory", False),
                "size": meta.get("size_bytes", 0),
                "modifiedTime": meta.get("last_modified"),
            }
        )

    # Directories first, then alphabetical
    results.sort(key=lambda d: (not d["is_directory"], d["name"].lower()))
    return results


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------


@log_complexity  # type: ignore[attr-defined]
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'read_file',
        'description': """ Read content from a file in the workspace.
        
        Reads and returns the content of a specified file from the local filesystem.
        Handles text, images (PNG, JPG, GIF, WEBP, SVG, BMP), and PDF files. For text 
        files, it can read specific line ranges with pagination support. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': """ Path of the file to read. Can be absolute or relative to workspace root.
                    Must be located under the configured workspace_root and not be ignored by .geminiignore patterns. """
                },
                'offset': {
                    'type': 'integer',
                    'description': """ For text files only, the 0-based line number to start 
                    reading from. Requires 'limit' to be set. Use for paginating through large files. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ For text files only, maximum number of lines to read. 
                    Use with 'offset' to paginate through large files. If omitted, reads up to 
                    2000 lines by default. Also enforces a per-line length cap of 2000 characters. """
                }
            },
            'required': [
                'path'
            ]
        }
    }
)
def read_file(
    path: str,
    *,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:  # pragma: no cover
    """Read content from a file in the workspace.

    Reads and returns the content of a specified file from the local filesystem.
    Handles text, images (PNG, JPG, GIF, WEBP, SVG, BMP), and PDF files. For text 
    files, it can read specific line ranges with pagination support.

    Args:
        path (str): Path of the file to read. Can be absolute or relative to workspace root.
            Must be located under the configured workspace_root and not be ignored by .geminiignore patterns.
        offset (Optional[int]): For text files only, the 0-based line number to start 
            reading from. Requires 'limit' to be set. Use for paginating through large files.
        limit (Optional[int]): For text files only, maximum number of lines to read. 
            Use with 'offset' to paginate through large files. If omitted, reads up to 
            2000 lines by default. Also enforces a per-line length cap of 2000 characters.

    Returns:
        Dict[str, Any]: Object describing the retrieved content with the following structure:
        
        Required parameters (all file types):
            - size_bytes (int): Size of the file in bytes.
        
        # Optional parameters:
            - content (str): For text and SVG files, the plain text content. May include 
              truncation notices if the file was sliced due to offset/limit or line length limits.
            - inlineData (Dict[str, str]): For binary, image, audio, video and PDF files.
              Contains 'data' (base64-encoded payload) and 'mimeType' (detected MIME type 
              or 'application/octet-stream' as fallback).
            - encoding (str): Set to "base64" for binary files, included for backward compatibility.
            - start_line (int): For text files only, 1-based starting line number of the returned slice.
            - end_line (int): For text files only, 1-based ending line number (inclusive) of the 
              returned slice. Returns 0 when the file is empty.
            - total_lines (int): For text files only, total number of lines in the complete file.
            - is_truncated (bool): For text files only, True when the response was truncated 
              due to offset/limit values or per-line length limits.

    Raises:
        InvalidInputError: On type/format issues with parameters, paths outside 
            workspace, or files ignored by .geminiignore patterns.
        WorkspaceNotAvailableError: If the workspace is not configured.
        FileNotFoundError: If the path does not exist.
        IsADirectoryError: If the path points to a directory, not a file.
        ValueError: If file size exceeds 20 MB limit.
        RuntimeError: If the DB entry is malformed.

    """

    # ---------------- Validation ----------------
    if not isinstance(path, str):
        raise InvalidInputError("'path' must be a string")

    if offset is not None and (not isinstance(offset, int) or offset < 0):
        raise InvalidInputError("'offset' must be a non-negative integer if provided")

    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise InvalidInputError("'limit' must be a positive integer if provided")

    # Default values
    start_line_zero_idx: int = offset or 0
    max_lines: int = limit or 2000

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # Resolve path with respect to the workspace (supports relative paths)
    resolved_path = resolve_workspace_path(path, workspace_root)

    if not os.path.isabs(resolved_path):
        raise InvalidInputError("Resolved path must be absolute")

    if not _is_within_workspace(resolved_path, workspace_root):
        raise InvalidInputError("Path resolves outside workspace root")

    # ---------------- .geminiignore handling ----------------
    if _fs_is_ignored(resolved_path, workspace_root, DB["file_system"]):
        short_path = os.path.relpath(resolved_path, workspace_root).replace(os.sep, "/")
        raise InvalidInputError(f"File path '{short_path}' is ignored by .geminiignore pattern(s).")

    fs = DB.setdefault("file_system", {})
    entry = fs.get(resolved_path)
    if not entry:
        raise FileNotFoundError(resolved_path)
    if entry.get("is_directory", False):
        raise IsADirectoryError(resolved_path)

    size_bytes = entry.get("size_bytes", 0)
    MAX_BYTES = 20 * 1024 * 1024  # 20 MB
    if size_bytes > MAX_BYTES:
        raise ValueError("File exceeds 20 MB size limit")

    # Detect file type via helper (fallback text)

    file_type = detect_file_type(resolved_path)

    # If binary/image/pdf etc. we expect base64 content field in DB or we fake
    if file_type != "text" and file_type != "svg":
        # Attempt to read base64 content from DB or placeholder
        data_b64 = entry.get("content_b64", "")
        mime_type, _ = mimetypes.guess_type(resolved_path)
        return {
            "size_bytes": size_bytes,
            "inlineData": {
                "data": data_b64,
                "mimeType": mime_type or "application/octet-stream",
            },
            "encoding": "base64",
        }

    # -------- Text/SVG processing --------
    content_lines = entry.get("content_lines")
    if not isinstance(content_lines, list):
        raise RuntimeError(f"File entry for {path} is malformed: 'content_lines' is not a list.")

    total_lines = len(content_lines)

    if total_lines == 0 and start_line_zero_idx > 0:
        raise InvalidInputError(
            f"Offset ({start_line_zero_idx}) is beyond the total number of lines (0) in file: {path}."
        )

    if start_line_zero_idx >= total_lines and total_lines > 0:
        raise InvalidInputError(
            f"Offset ({start_line_zero_idx}) is beyond the total number of lines ({total_lines}) in file: {path}."
        )

    end_idx_exclusive = min(start_line_zero_idx + max_lines, total_lines)

    MAX_LINE_LENGTH = 2000
    truncated_in_length = False
    selected_lines: List[str] = []
    for line in content_lines[start_line_zero_idx:end_idx_exclusive]:
        if len(line) > MAX_LINE_LENGTH:
            truncated_in_length = True
            selected_lines.append(line[:MAX_LINE_LENGTH] + "... [truncated]\n")
        else:
            selected_lines.append(line)

    is_truncated = truncated_in_length or start_line_zero_idx > 0 or end_idx_exclusive < total_lines

    # Prepend notice if truncated
    if is_truncated:
        header = (
            f"[File content truncated: showing lines {start_line_zero_idx + 1}-{end_idx_exclusive} "
            f"of {total_lines} total lines. Use offset/limit to view more.]\n"
        )
    else:
        header = ""

    content_str = header + "".join(selected_lines)

    return {
        "size_bytes": size_bytes,
        "content": content_str,
        "start_line": start_line_zero_idx + 1,
        "end_line": end_idx_exclusive if total_lines > 0 else 0,
        "total_lines": total_lines,
        "is_truncated": is_truncated,
    }

# ---------------------------------------------------------------------------
# replace
# ---------------------------------------------------------------------------


@log_complexity  # type: ignore[attr-defined]
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'replace',
        'description': """ Perform surgical string replacement with multi-stage self-correction.
        
        This function implements a sophisticated replacement workflow: checkpoint → diff → write.
        It performs exact string matching and replacement with intelligent error correction,
        validation of expected replacement counts, and comprehensive error handling.
        
        The function can create new files (when old_string is empty) or perform precise
        replacements in existing files. It includes multi-stage self-correction to handle
        common issues like string escaping problems or whitespace mismatches. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': """ Path to the file to modify. Can be absolute or relative to workspace root.
                    Must be within workspace. """
                },
                'old_string': {
                    'type': 'string',
                    'description': """ Exact literal text to replace. Must include sufficient context
                    (3+ lines before/after) for unique identification. Use empty string to create new file. """
                },
                'new_string': {
                    'type': 'string',
                    'description': """ Exact literal text to replace old_string with. Must be the
                    complete replacement text with correct whitespace and formatting. """
                },
                'expected_replacements': {
                    'type': 'integer',
                    'description': """ Number of replacements expected. Defaults to 1.
                    Use when replacing multiple occurrences of the same string. """
                },
                'modified_by_user': {
                    'type': 'boolean',
                    'description': """ Whether the edit was modified manually by the user.
                    Used for tracking user modifications. Defaults to None. """
                }
            },
            'required': [
                'file_path',
                'old_string',
                'new_string'
            ]
        }
    }
)
def replace(
    file_path: str,
    old_string: str,
    new_string: str,
    *,
    expected_replacements: Optional[int] = None,
    modified_by_user: Optional[bool] = None,
) -> Dict[str, Any]:
    """Perform surgical string replacement with multi-stage self-correction.

    This function implements a sophisticated replacement workflow: checkpoint → diff → write.
    It performs exact string matching and replacement with intelligent error correction,
    validation of expected replacement counts, and comprehensive error handling.

    The function can create new files (when old_string is empty) or perform precise
    replacements in existing files. It includes multi-stage self-correction to handle
    common issues like string escaping problems or whitespace mismatches.

    Args:
        file_path (str): Path to the file to modify. Can be absolute or relative to workspace root.
            Must be within workspace.
        old_string (str): Exact literal text to replace. Must include sufficient context
            (3+ lines before/after) for unique identification. Use empty string to create new file.
        new_string (str): Exact literal text to replace old_string with. Must be the
            complete replacement text with correct whitespace and formatting.
        expected_replacements (Optional[int]): Number of replacements expected. Defaults to 1.
            Use when replacing multiple occurrences of the same string.
        modified_by_user (Optional[bool]): Whether the edit was modified manually by the user.
            Used for tracking user modifications. Defaults to None.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'success' (bool): True if replacement completed successfully
            - 'message' (str): Human-readable result message
            - 'file_path' (str): Absolute path of the modified file
            - 'replacements_made' (int): Number of replacements actually performed
            - 'is_new_file' (bool): True if a new file was created
            - 'content_preview' (str): First 200 characters of new content for verification
            - 'modified_by_user' (bool): Whether the content was modified by user

    Raises:
        InvalidInputError: If parameters are invalid (non-string, empty file_path, etc.)
        WorkspaceNotAvailableError: If workspace_root is not configured in DB
        ValueError: If file_path is outside workspace boundaries
        FileNotFoundError: If trying to edit non-existent file (and old_string is not empty)
        FileExistsError: If trying to create a file that already exists (old_string is empty)
        IsADirectoryError: If file_path points to a directory
        RuntimeError: If replacement count doesn't match expected_replacements
    """
    # ================ Phase 1: Checkpoint - Validation ================
    if not isinstance(file_path, str):
        raise InvalidInputError("'file_path' must be a string")
    if not file_path or file_path.strip() == "":
        raise InvalidInputError("'file_path' must be a non-empty string")
    if not isinstance(old_string, str):
        raise InvalidInputError("'old_string' must be a string")
    if not isinstance(new_string, str):
        raise InvalidInputError("'new_string' must be a string")
    if expected_replacements is not None and (not isinstance(expected_replacements, int) or expected_replacements < 1):
        raise InvalidInputError("'expected_replacements' must be a positive integer or None")
    if modified_by_user is not None and not isinstance(modified_by_user, bool):
        raise InvalidInputError("'modified_by_user' must be a boolean or None")

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # Resolve path (supports relative paths)
    resolved_path = resolve_workspace_path(file_path, workspace_root)

    if not os.path.isabs(resolved_path):
        raise InvalidInputError("Resolved path must be absolute")

    if not _is_within_workspace(resolved_path, workspace_root):
        raise ValueError(f"File path '{resolved_path}' is outside workspace boundaries")

    expected_replacements = expected_replacements or 1
    fs = DB.setdefault("file_system", {})
    
    # ================ Phase 2: Calculate Edit - Read & Analyze ================
    entry = fs.get(resolved_path)
    current_content = None
    is_new_file = False
    
    if entry:
        if entry.get("is_directory", False):
            raise IsADirectoryError(f"Path '{resolved_path}' is a directory, not a file")
        
        # File exists - check if we're trying to create it
        if old_string == "":
            raise FileExistsError(f"File '{resolved_path}' already exists. Cannot create existing file.")
        
        current_content = "".join(entry.get("content_lines", []))
    else:
        # File doesn't exist
        if old_string == "":
            # Creating new file
            is_new_file = True
            current_content = ""
        else:
            raise FileNotFoundError(f"File '{resolved_path}' not found. Use empty old_string to create new file.")

    # ================ Phase 3: Multi-stage Self-correction ================
    if is_new_file:
        final_old_string = old_string
        final_new_string = new_string
        occurrences = 0
        new_content = new_string
    else:
        # Apply correction logic for existing files
        correction_result = correct_string_issues(current_content, old_string, new_string, expected_replacements)
        final_old_string = correction_result["old_string"]
        final_new_string = correction_result["new_string"]
        occurrences = correction_result["occurrences"]
        
        # Validate replacement count
        if occurrences != expected_replacements:
            occurrence_term = "occurrence" if expected_replacements == 1 else "occurrences"
            raise RuntimeError(
                f"Expected {expected_replacements} {occurrence_term} but found {occurrences} "
                f"for old_string in '{file_path}'"
            )
        
        # Apply replacement
        new_content = apply_replacement(current_content, final_old_string, final_new_string)

    # ================ Phase 4: Write - Apply Changes ================
    # Create parent directories if needed
    parent_dir = os.path.dirname(resolved_path)
    parent_entry = fs.get(parent_dir)
    if not parent_entry:
        # Create parent directory entry
        fs[parent_dir] = {
            "path": parent_dir,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": datetime.datetime.now().isoformat() + "Z",
        }

    # Prepare new content lines
    # Use exact literal content as provided (no automatic newline addition)
    new_content_lines = new_content.splitlines(keepends=True)
    
    # Calculate file size
    content_size = sum(len(line.encode('utf-8')) for line in new_content_lines)
    
    # Update or create file entry
    fs[resolved_path] = {
        "path": resolved_path,
        "is_directory": False,
        "content_lines": new_content_lines,
        "size_bytes": content_size,
        "last_modified": datetime.datetime.now().isoformat() + "Z",
    }

    # ================ Phase 5: Result ================
    action = "Created" if is_new_file else "Modified"
    message = f"{action} file '{os.path.basename(resolved_path)}'"
    if not is_new_file:
        message += f" ({occurrences} replacements)"
    
    # Add user modification notice if applicable
    if modified_by_user:
        message += f". User modified the new_string content to be: {new_string}"

    return {
        "success": True,
        "message": message,
        "file_path": resolved_path,
        "replacements_made": occurrences,
        "is_new_file": is_new_file,
        "content_preview": new_content[:200] + ("..." if len(new_content) > 200 else ""),
        "modified_by_user": modified_by_user or False,
    }


@log_complexity  # type: ignore[attr-defined]
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'write_file',
        'description': """ Write content to a specified file, creating parent directories if needed.
        
        This function writes the provided content to the specified file path. If the file
        already exists, it will be overwritten. If the file doesn't exist, it (and any
        necessary parent directories) will be created. The operation executes immediately
        without user approval or confirmation prompts. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': """ The path to the file to write to. Can be absolute or relative to workspace root.
                    Must be within the workspace root. """
                },
                'content': {
                    'type': 'string',
                    'description': """ The content to write to the file. This will completely replace
                    any existing content in the file. """
                },
                'modified_by_user': {
                    'type': 'boolean',
                    'description': """ Whether the proposed content was modified
                    by the user. Defaults to None. """
                }
            },
            'required': [
                'file_path',
                'content'
            ]
        }
    }
)
def write_file(
    file_path: str,
    content: str,
    *,
    modified_by_user: Optional[bool] = None,
) -> Dict[str, Any]:
    """Write content to a specified file, creating parent directories if needed.

    This function writes the provided content to the specified file path. If the file
    already exists, it will be overwritten. If the file doesn't exist, it (and any
    necessary parent directories) will be created. The operation executes immediately
    without user approval or confirmation prompts.

    Args:
        file_path (str): The path to the file to write to. Can be absolute or relative to workspace root.
            Must be within the workspace root.
        content (str): The content to write to the file. This will completely replace
            any existing content in the file.
        modified_by_user (Optional[bool]): Whether the proposed content was modified
            by the user. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing the operation result with keys:
            - success (bool): Whether the write operation succeeded
            - message (str): Success message describing the operation
            - file_path (str): The absolute path of the written file
            - is_new_file (bool): Whether this was a new file creation
            - size_bytes (int): The size of the written content in bytes
            - lines_count (int): The number of lines in the written content

    Raises:
        InvalidInputError: If file_path is not a string or outside the workspace root, 
            or the file_path component is a file, not a directory, or the file_path already exists and is a directory
            or if content is not a string.
        WorkspaceNotAvailableError: If workspace_root is not configured.
    """
        # ================== Parameter Validation ==================
    if not isinstance(file_path, str):
        raise InvalidInputError("'file_path' must be a string")
    
    if not file_path or file_path.strip() == "":
        raise InvalidInputError("'file_path' must be a non-empty string")

    if not isinstance(content, str):
        raise InvalidInputError("'content' must be a string")

    if modified_by_user is not None and not isinstance(modified_by_user, bool):
        raise InvalidInputError("'modified_by_user' must be a boolean or None")

    # ================== Security & Workspace Validation ==================
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # Resolve path (supports relative paths)
    resolved_path = resolve_workspace_path(file_path, workspace_root)

    if not _is_within_workspace(resolved_path, workspace_root):
        raise InvalidInputError(f"File path must be within the root directory ({workspace_root}): {resolved_path}")

    # ================== File System State Check ==================
    fs = DB.setdefault("file_system", {})
    
    # Check if file exists and validate it's not a directory
    existing_entry = fs.get(resolved_path)
    is_new_file = existing_entry is None
    
    if existing_entry and existing_entry.get("is_directory", False):
        raise InvalidInputError(f"Path is a directory, not a file: {resolved_path}")
    
    # ================== Content Processing ==================
    # Keep original content as-is, just split into lines for storage
    if content == "":
        content_lines = []  # Empty content = empty list, no newline
    else:
        content_lines = content.splitlines(keepends=True)
        # If content doesn't end with newline, the last line won't have one
        # Keep it as-is to preserve original content
    
    # Calculate file metrics
    size_bytes = len(content.encode('utf-8'))
    lines_count = len(content_lines) if content_lines else 0
    
    # ================== Create Parent Directories ==================
    parent_dir = os.path.dirname(resolved_path)
    if parent_dir != workspace_root:
        # Ensure all parent directories exist in the DB
        current_path = workspace_root
        path_parts = os.path.relpath(parent_dir, workspace_root).split(os.sep)
        
        for part in path_parts:
            if part == "." or part == "":
                continue
            current_path = os.path.join(current_path, part).replace(os.sep, '/')
            
            existing_entry = fs.get(current_path)
            if existing_entry:
                # Validate that existing path component is a directory
                if not existing_entry.get("is_directory", False):
                    raise InvalidInputError(f"Cannot create directory '{current_path}': path exists as a file")
            else:
                # Create new directory entry with metadata
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                fs[current_path] = {
                    "path": current_path,
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": timestamp,
                    "metadata": {
                        "timestamps": {
                            "access_time": timestamp,
                            "modify_time": timestamp,
                            "change_time": timestamp
                        },
                        "attributes": {
                            "is_symlink": False,
                            "symlink_target": None,
                            "is_hidden": False,
                            "is_readonly": False
                        },
                        "permissions": {
                            "mode": 493,
                            "uid": 1000,
                            "gid": 1000
                        }
                    }
                }
    
    # ================== Write File to Database ==================
    # Use timezone-aware datetime
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if is_new_file or 'metadata' not in existing_entry:
        metadata = {
            "attributes": {
                "is_symlink": False,
                "symlink_target": None,
                "is_hidden": False,
                "is_readonly": False
            },
            "permissions": {
                "mode": 493,
                "uid": 1000,
                "gid": 1000
            },
            "timestamps": {}
        }
    else:
        metadata = existing_entry.get("metadata")

    metadata["timestamps"]["access_time"] = timestamp
    metadata["timestamps"]["modify_time"] = timestamp
    metadata["timestamps"]["change_time"] = timestamp
    
    fs[resolved_path] = {
        "path": resolved_path,
        "is_directory": False,
        "content_lines": content_lines,
        "size_bytes": size_bytes,
        "last_modified": timestamp,
        "metadata": metadata
    }
    
    # ================== Store Last Edit Parameters ==================
    DB["last_edit_params"] = {
        "tool": "write_file",
        "file_path": resolved_path,
        "content": content,
        "modified_by_user": modified_by_user,
        "timestamp": timestamp
    }
    
    # ================== Build Success Response ==================
    # Match TypeScript implementation success message format
    success_message_parts = []
    if is_new_file:
        success_message_parts.append(f"Successfully created and wrote to new file: {resolved_path}.")
    else:
        success_message_parts.append(f"Successfully overwrote file: {resolved_path}.")
    
    if modified_by_user:
        success_message_parts.append(f"User modified the `content` to be: {content}")
    
    return {
        "success": True,
        "message": " ".join(success_message_parts),
        "file_path": resolved_path,
        "is_new_file": is_new_file,
        "size_bytes": size_bytes,
        "lines_count": lines_count,
    }



@log_complexity  # type: ignore[attr-defined]
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'glob',
        'description': """ Find files matching a glob pattern, sorted by modification time (newest first).
        
        This function searches for files matching the specified glob pattern within the
        given directory (or workspace root if not specified). Results are sorted with
        recently modified files (within 24 hours) appearing first by modification time,
        followed by older files sorted alphabetically. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': """ The glob pattern to match files against. Supports wildcards
                    like '*.py', '**/*.md', 'src/**/*.ts', etc. """
                },
                'path': {
                    'type': 'string',
                    'description': """ The path to the directory to search within. Can be absolute 
                    or relative to workspace root. If not provided, searches the workspace root. 
                    Must be within workspace. """
                },
                'case_sensitive': {
                    'type': 'boolean',
                    'description': """ Whether the pattern matching should be
                    case-sensitive. Defaults to False for case-insensitive matching. """
                },
                'respect_git_ignore': {
                    'type': 'boolean',
                    'description': """ Whether to respect .gitignore patterns
                    when finding files. Only applies if in a git repository. Defaults to True. """
                }
            },
            'required': [
                'pattern'
            ]
        }
    }
)
def glob(
    pattern: str,
    *,
    path: Optional[str] = None,
    case_sensitive: Optional[bool] = None,
    respect_git_ignore: Optional[bool] = None,
) -> List[str]:
    """Find files matching a glob pattern, sorted by modification time (newest first).

    This function searches for files matching the specified glob pattern within the
    given directory (or workspace root if not specified). Results are sorted with
    recently modified files (within 24 hours) appearing first by modification time,
    followed by older files sorted alphabetically.

    Args:
        pattern (str): The glob pattern to match files against. Supports wildcards
            like '*.py', '**/*.md', 'src/**/*.ts', etc.
        path (Optional[str]): The path to the directory to search within. Can be absolute 
            or relative to workspace root. If not provided, searches the workspace root. 
            Must be within workspace.
        case_sensitive (Optional[bool]): Whether the pattern matching should be
            case-sensitive. Defaults to False for case-insensitive matching.
        respect_git_ignore (Optional[bool]): Whether to respect .gitignore patterns
            when finding files. Only applies if in a git repository. Defaults to True.

    Returns:
        List[str]: A list of absolute file paths matching the pattern, sorted by
            modification time (newest first for recent files, then alphabetically
            for older files).

    Raises:
        InvalidInputError: If pattern is not a string, empty, or if path is 
            outside the workspace root.
        WorkspaceNotAvailableError: If workspace_root is not configured.
        FileNotFoundError: If the specified path does not exist.
        NotADirectoryError: If the specified path is not a directory.
    """
    # -------------------- Input Validation --------------------
    if not isinstance(pattern, str) or pattern.strip() == "":
        raise InvalidInputError("'pattern' must be a non-empty string")
    
    if path is not None:
        if not isinstance(path, str):
            raise InvalidInputError("'path' must be a string or None")
    
    if case_sensitive is not None and not isinstance(case_sensitive, bool):
        raise InvalidInputError("'case_sensitive' must be a boolean or None")
    
    if respect_git_ignore is not None and not isinstance(respect_git_ignore, bool):
        raise InvalidInputError("'respect_git_ignore' must be a boolean or None")

    # -------------------- Workspace and Path Validation --------------------
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # Resolve provided path; None means workspace root. Also allow "/" to map to root
    if path is None:
        search_path = workspace_root
    else:
        search_path = resolve_workspace_path(path, workspace_root)
    
    if not _is_within_workspace(search_path, workspace_root):
        raise InvalidInputError("'path' must be within the workspace root")

    # Check if search path exists and is a directory
    fs = DB.setdefault("file_system", {})
    search_entry = fs.get(search_path)
    if not search_entry:
        raise FileNotFoundError(f"Search path does not exist: {search_path}")
    if not search_entry.get("is_directory", False):
        raise NotADirectoryError(f"Search path is not a directory: {search_path}")

    # -------------------- Set Defaults --------------------
    case_sensitive_flag = case_sensitive if case_sensitive is not None else False
    respect_git_ignore_flag = respect_git_ignore if respect_git_ignore is not None else True

    # -------------------- Find Matching Files --------------------
    matching_files = []
    
    for file_path, file_meta in fs.items():
        # Skip directories
        if file_meta.get("is_directory", False):
            continue
        
        # Check if file is within search path
        if not file_path.startswith(search_path):
            continue
        
        # Get relative path from search directory for pattern matching
        if search_path == workspace_root:
            relative_path = os.path.relpath(file_path, workspace_root)
        else:
            relative_path = os.path.relpath(file_path, search_path)
        
        # Check if file matches the glob pattern
        if glob_match(relative_path, pattern, case_sensitive_flag):
            matching_files.append((file_path, file_meta))
    
    # -------------------- Apply Git Ignore Filtering --------------------
    if respect_git_ignore_flag:
        matching_files = filter_gitignore(matching_files, workspace_root)
    
    # -------------------- Sort by Modification Time --------------------
    if not matching_files:
        return []
    
    # Sort files by modification time (newest first for recent, alphabetical for older)
    now = datetime.datetime.utcnow()
    one_day_ago = now - datetime.timedelta(days=1)
    
    def sort_key(file_tuple):
        file_path, file_meta = file_tuple
        last_modified_str = file_meta.get("last_modified", "1970-01-01T00:00:00Z")
        
        try:
            # Parse ISO format timestamp
            last_modified = datetime.datetime.fromisoformat(last_modified_str.replace('Z', '+00:00'))
            last_modified = last_modified.replace(tzinfo=None)  # Remove timezone for comparison
        except (ValueError, AttributeError):
            # Fallback to epoch if parsing fails
            last_modified = datetime.datetime(1970, 1, 1)
        
        is_recent = last_modified >= one_day_ago
        
        if is_recent:
            # Recent files: sort by modification time (newest first)
            return (0, -last_modified.timestamp())
        else:
            # Older files: sort alphabetically
            return (1, file_path.lower())
    
    matching_files.sort(key=sort_key)
    
    # Return just the file paths
    return [file_path for file_path, _ in matching_files]


@log_complexity  # type: ignore[attr-defined]
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'search_file_content',
        'description': """ Searches for a regular expression pattern within the content of files in a specified directory. 
        
        This function searches for the specified regex pattern within the content of files
        in the given directory (or workspace root if not specified). It uses a pure Python
        implementation to search through text files and returns matches with line numbers
        and content. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': """ The regular expression pattern to search for within file contents.
                    Must be a valid regex pattern (e.g., 'function\\s+myFunction', 'import\\s+\\{.*\\}'). """
                },
                'path': {
                    'type': 'string',
                    'description': """ The path to the directory to search within. Can be absolute
                    or relative to workspace root. If not provided, searches the workspace root. 
                    Must be within workspace. """
                },
                'include': {
                    'type': 'string',
                    'description': """ A glob pattern to filter which files are searched
                    (e.g., '*.js', '*.{ts,tsx}', 'src/**'). If not provided, searches all files
                    (respecting common ignore patterns). """
                }
            },
            'required': [
                'pattern'
            ]
        }
    }
)
def grep_search(
    pattern: str,
    *,
    path: Optional[str] = None,
    include: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Searches for a regular expression pattern within the content of files in a specified directory. 

    This function searches for the specified regex pattern within the content of files
    in the given directory (or workspace root if not specified). It uses a pure Python
    implementation to search through text files and returns matches with line numbers
    and content.

    Args:
        pattern (str): The regular expression pattern to search for within file contents.
            Must be a valid regex pattern (e.g., 'function\\s+myFunction', 'import\\s+\\{.*\\}').
        path (Optional[str]): The path to the directory to search within. Can be absolute
            or relative to workspace root. If not provided, searches the workspace root. 
            Must be within workspace.
        include (Optional[str]): A glob pattern to filter which files are searched
            (e.g., '*.js', '*.{ts,tsx}', 'src/**'). If not provided, searches all files
            (respecting common ignore patterns).

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing match information.
            Each dictionary contains the following fields:
            - filePath: str - Relative path to the file from workspace root
            - lineNumber: int - Line number (1-based)
            - line: str - The matching line content
            Results are sorted by file path, then by line number.

    Raises:
        InvalidInputError: If pattern is not a valid regex, empty string, or if path
            is outside the workspace root.
        WorkspaceNotAvailableError: If workspace_root is not configured.
        FileNotFoundError: If the specified path does not exist.
        NotADirectoryError: If the specified path is not a directory.
    """
    # -------------------- Input Validation --------------------
    if not isinstance(pattern, str) or pattern.strip() == "":
        raise InvalidInputError("'pattern' must be a non-empty string")
    
    # Validate regex pattern
    try:
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise InvalidInputError(f"Invalid regular expression pattern: {pattern}. Error: {str(e)}")
    
    if path is not None:
        if not isinstance(path, str):
            raise InvalidInputError("'path' must be a string or None")
    
    if include is not None:
        if not isinstance(include, str) or include.strip() == "":
            raise InvalidInputError("'include' must be a non-empty string or None")

    # -------------------- Workspace and Path Validation --------------------
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # Resolve provided path; None means workspace root, "/" maps to root
    if path is None:
        search_path = workspace_root
    else:
        search_path = resolve_workspace_path(path, workspace_root)
        if not os.path.isabs(search_path):
            raise InvalidInputError("'path' must be an absolute path")

    if not _is_within_workspace(search_path, workspace_root):
        raise InvalidInputError("'path' must be within the workspace root")

    # Check if search path exists and is a directory
    fs = DB.setdefault("file_system", {})
    search_entry = fs.get(search_path)
    if not search_entry:
        raise FileNotFoundError(f"Search path does not exist: {search_path}")
    if not search_entry.get("is_directory", False):
        raise NotADirectoryError(f"Search path is not a directory: {search_path}")

    # -------------------- Perform Search --------------------
    # Use direct Python implementation
    matches = []
    
    # Get file system from DB
    fs = DB.setdefault("file_system", {})
    
    # Common directories to ignore
    ignore_dirs = {'.git', 'node_modules', 'bower_components', '.svn', '.hg', '__pycache__'}
    
    # Process include pattern
    include_patterns = []
    if include:
        # Handle brace expansion like "*.{ts,tsx}"
        if '{' in include and '}' in include:
            # Simple brace expansion
            start = include.find('{')
            end = include.find('}', start)
            if start != -1 and end != -1:
                prefix = include[:start]
                suffix = include[end+1:]
                extensions = include[start+1:end].split(',')
                for ext in extensions:
                    include_patterns.append(prefix + ext.strip() + suffix)
            else:
                include_patterns.append(include)
        else:
            include_patterns.append(include)
    
    # Search through all files
    for file_path, file_meta in fs.items():
        # Skip directories
        if file_meta.get("is_directory", False):
            continue
        
        # Check if file is within search path
        if not file_path.startswith(search_path):
            continue
        
        # Skip ignored directories
        relative_path_for_filtering = os.path.relpath(file_path, search_path)
        path_parts = relative_path_for_filtering.split(os.sep)
        if any(part in ignore_dirs for part in path_parts):
            continue
        
        # Apply include filter
        if include_patterns:
            matches_include = False
            for pattern_filter in include_patterns:
                if fnmatch.fnmatch(os.path.basename(file_path), pattern_filter) or fnmatch.fnmatch(relative_path_for_filtering, pattern_filter):
                    matches_include = True
                    break
            if not matches_include:
                continue
        
        # Skip binary files (basic heuristic)
        file_ext = os.path.splitext(file_path)[1].lower()
        binary_extensions = {'.exe', '.dll', '.so', '.dylib', '.bin', '.zip', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.mp3', '.mp4', '.avi'}
        if file_ext in binary_extensions:
            continue
        
        # Read file content and search
        try:
            # Assemble file content from stored content_lines (authoritative field)
            content_lines = file_meta.get("content_lines")
            if not isinstance(content_lines, list):
                continue

            # Join without introducing extra newlines because lines already contain linebreaks
            content_str = "".join(content_lines)
            if content_str == "":
                continue

            lines = content_str.splitlines()
            for line_num, line in enumerate(lines, 1):
                if compiled_pattern.search(line):
                    # Always use workspace-relative path for consistency in results
                    workspace_relative_path = os.path.relpath(file_path, workspace_root)
                    matches.append({
                        'filePath': workspace_relative_path,
                        'lineNumber': line_num,
                        'line': line
                    })
        except Exception:
            # Skip files that can't be read
            continue
    
    # -------------------- Sort and Return Results --------------------
    # Sort by file path, then by line number
    matches.sort(key=lambda x: (x['filePath'], x['lineNumber']))
    
    return matches