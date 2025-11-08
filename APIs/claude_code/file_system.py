"""claude_code file-system tool implementations."""
from __future__ import annotations
from common_utils.tool_spec_decorator import tool_spec

import datetime
import fnmatch
import os
import re
from typing import Any, Dict, List, Optional

from common_utils.log_complexity import log_complexity

from .SimulationEngine.custom_errors import (
    InvalidInputError,
    WorkspaceNotAvailableError,
)
from .SimulationEngine.db import DB
from .SimulationEngine.file_utils import (
    _create_parent_directories,
    _is_ignored,
    _is_within_workspace,
    _should_ignore,
)


@log_complexity
@tool_spec(
    spec={
        'name': 'listFiles',
        'description': 'List the direct children of a workspace directory.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The absolute path to the directory to list.'
                },
                'ignore': {
                    'type': 'array',
                    'description': 'A list of glob patterns to ignore. Defaults to None.',
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
def list_files(
    path: str,
    *,
    ignore: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """List the direct children of a workspace directory.

    Args:
        path (str): The absolute path to the directory to list.
        ignore (Optional[List[str]]): A list of glob patterns to ignore. Defaults to None.

    Returns:
        Dict[str, List[str]]: A dictionary with the following keys:
            - files (List[str]): A list of file and directory names.

    Raises:
        InvalidInputError: If 'path' is not a non-empty absolute string, or if 'ignore' is not a list of strings.
        WorkspaceNotAvailableError: If the workspace root is not configured.
        FileNotFoundError: If the specified path does not exist.
        NotADirectoryError: If the specified path is not a directory.
    """
    if not isinstance(path, str) or path.strip() == "":
        raise InvalidInputError("'path' must be a non-empty string")
    if not os.path.isabs(path):
        raise InvalidInputError("'path' must be absolute")

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    if not _is_within_workspace(path, workspace_root):
        raise InvalidInputError("Path resolves outside workspace root")

    if ignore is not None:
        if not isinstance(ignore, list):
            raise InvalidInputError(
                "'ignore' must be a list of glob pattern strings or None"
            )
        for pat in ignore:
            if not isinstance(pat, str):
                raise InvalidInputError("All items in 'ignore' must be strings")

    fs = DB.setdefault("file_system", {})
    entry = fs.get(path)
    if not entry:
        raise FileNotFoundError(path)
    if not entry.get("is_directory", False):
        raise NotADirectoryError(path)

    files = []
    for item_path, item_info in fs.items():
        if os.path.dirname(item_path) == path and item_path != path:
            # Optionally skip ignored files
            if ignore and _should_ignore(item_path, ignore):
                continue

            files.append(os.path.basename(item_path))

    return {"files": files}


@log_complexity
@tool_spec(
    spec={
        'name': 'readFile',
        'description': 'Read content from a file in the workspace.',
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The absolute path to the file to read.'
                },
                'offset': {
                    'type': 'integer',
                    'description': 'The line number to start reading from (1-indexed). Defaults to 1.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of lines to read. Defaults to 2000.'
                }
            },
            'required': [
                'file_path'
            ]
        }
    }
)
def read_file(
    file_path: str,
    *,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> Dict[str, str]:
    """Read content from a file in the workspace.

    Args:
        file_path (str): The absolute path to the file to read.
        offset (Optional[int]): The line number to start reading from (1-indexed). Defaults to 1.
        limit (Optional[int]): The maximum number of lines to read. Defaults to 2000.

    Returns:
        Dict[str, str]: A dictionary containing the file content with the following key:
            - content (str): The content of the file.

    Raises:
        InvalidInputError: If 'path' is not a non-empty absolute string, or if 'offset' or 'limit' are invalid.
        WorkspaceNotAvailableError: If the workspace root is not configured.
        FileNotFoundError: If the specified path does not exist.
        IsADirectoryError: If the specified path is a directory.
        ValueError: If the file exceeds the 20 MB size limit.
    """
    if not isinstance(file_path, str) or file_path.strip() == "":
        raise InvalidInputError("'path' must be a non-empty string")

    if not os.path.isabs(file_path):
        raise InvalidInputError("'path' must be absolute")

    if offset is not None and (not isinstance(offset, int) or offset < 0):
        raise InvalidInputError("'offset' must be a non-negative integer if provided")

    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise InvalidInputError("'limit' must be a positive integer if provided")

    start_line_zero_idx: int = (offset - 1) if offset else 0
    max_lines: int = limit or 2000

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    if not _is_within_workspace(file_path, workspace_root):
        raise InvalidInputError("Path resolves outside workspace root")

    if _is_ignored(file_path, workspace_root):
        short_path = os.path.relpath(file_path, workspace_root).replace(os.sep, "/")
        raise InvalidInputError(
            f"File path '{short_path}' is ignored by .claudeignore pattern(s)."
        )

    fs = DB.setdefault("file_system", {})
    entry = fs.get(file_path)
    if not entry:
        raise FileNotFoundError(file_path)
    if entry.get("is_directory", False):
        raise IsADirectoryError(file_path)

    size_bytes = entry.get("size_bytes", 0)
    MAX_BYTES = 20 * 1024 * 1024
    if size_bytes > MAX_BYTES:
        raise ValueError("File exceeds 20 MB size limit")

    content_lines = entry.get("content_lines", [])
    total_lines = len(content_lines)

    # Apply slicing for offset and limit
    start_line = start_line_zero_idx
    end_line = min(start_line_zero_idx + max_lines, total_lines)
    sliced_content_lines = content_lines[start_line:end_line]

    content = "".join(sliced_content_lines)

    return { "content": content }


@log_complexity
@tool_spec(
    spec={
        'name': 'editFile',
        'description': 'Create or edit a file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The absolute path to the file to edit.'
                },
                'content': {
                    'type': 'string',
                    'description': 'The new content for the file.'
                },
                'modified_by_user': {
                    'type': 'boolean',
                    'description': 'Whether the edit was modified manually by the user. This is not used in the function logic. Defaults to None.'
                }
            },
            'required': [
                'file_path',
                'content'
            ]
        }
    }
)
def edit_file(
    file_path: str,
    content: str,
    *,
    modified_by_user: Optional[bool] = None,
) -> Dict[str, Any]:
    """Create or edit a file.

    Args:
        file_path (str): The absolute path to the file to edit.
        content (str): The new content for the file.
        modified_by_user (Optional[bool]): Whether the edit was modified manually by the user. This is not used in the function logic. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing a success message with the key "message".

    Raises:
        InvalidInputError: If 'file_path' is not a non-empty absolute string, 'content' is not a string, or if the path points to a directory.
        WorkspaceNotAvailableError: If the workspace root is not configured.
    """
    if not isinstance(file_path, str) or file_path.strip() == "":
        raise InvalidInputError("'file_path' must be a non-empty string")

    if not os.path.isabs(file_path):
        raise InvalidInputError("File path must be absolute")

    if not isinstance(content, str):
        raise InvalidInputError("'content' must be a string")

    if modified_by_user is not None and not isinstance(modified_by_user, bool):
        raise InvalidInputError("'modified_by_user' must be a boolean or None")

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    if not _is_within_workspace(file_path, workspace_root):
        raise InvalidInputError(
            f"File path must be within the root directory ({workspace_root}): {file_path}"
        )

    fs = DB.setdefault("file_system", {})

    existing_entry = fs.get(file_path)

    if existing_entry and existing_entry.get("is_directory", False):
        raise InvalidInputError(f"Path is a directory, not a file: {file_path}")

    if content == "":
        content_lines = []
    else:
        content_lines = content.splitlines(keepends=True)

    size_bytes = len(content.encode("utf-8"))

    parent_dir = os.path.dirname(file_path)
    if parent_dir != workspace_root:
        _create_parent_directories(parent_dir, fs, workspace_root)

    timestamp = datetime.datetime.now().isoformat()

    new_entry = {
        "path": file_path,
        "is_directory": False,
        "content_lines": content_lines,
        "size_bytes": size_bytes,
        "last_modified": timestamp,
        "created": timestamp,
    }

    fs[file_path] = new_entry

    return {"message": f"File '{os.path.basename(file_path)}' written successfully."}

@log_complexity
@tool_spec(
    spec={
        'name': 'searchGlob',
        'description': 'Search for files matching a pattern.',
        'parameters': {
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': 'The glob pattern to match files against.'
                },
                'path': {
                    'type': 'string',
                    'description': 'The directory to search in, relative to the workspace root. If not provided, searches from the workspace root. Defaults to None.'
                }
            },
            'required': [
                'pattern'
            ]
        }
    }
)
def search_glob(
    pattern: str,
    *,
    path: Optional[str] = None,
) -> List[str]:
    """Search for files matching a pattern.

    Args:
        pattern (str): The glob pattern to match files against.
        path (Optional[str]): The directory to search in, relative to the workspace root. If not provided, searches from the workspace root. Defaults to None.

    Returns:
        List[str]: A list of absolute file paths matching the glob pattern.

    Raises:
        WorkspaceNotAvailableError: If the workspace root is not configured.
        InvalidInputError: If the search path is outside of the workspace.
    """
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    search_path = path or workspace_root
    if not os.path.isabs(search_path):
        search_path = os.path.join(workspace_root, search_path)

    if not _is_within_workspace(search_path, workspace_root):
        raise InvalidInputError("Search path is outside of the workspace")

    fs = DB.get("file_system", {})
    results = []
    for item_path in fs.keys():
        if fnmatch.fnmatch(item_path, os.path.join(search_path, pattern)):
            results.append(item_path)
    return results


@log_complexity
@tool_spec(
    spec={
        'name': 'grep',
        'description': 'Search for text in files.',
        'parameters': {
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': 'The regular expression pattern to search for.'
                },
                'path': {
                    'type': 'string',
                    'description': 'The directory to search in, relative to the workspace root. If not provided, searches from the workspace root. Defaults to None.'
                },
                'include': {
                    'type': 'string',
                    'description': 'A file pattern to include in the search (e.g., "*.py"). Defaults to None.'
                }
            },
            'required': [
                'pattern'
            ]
        }
    }
)
def grep(
    pattern: str,
    *,
    path: Optional[str] = None,
    include: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for text in files.

    Args:
        pattern (str): The regular expression pattern to search for.
        path (Optional[str]): The directory to search in, relative to the workspace root. If not provided, searches from the workspace root. Defaults to None.
        include (Optional[str]): A file pattern to include in the search (e.g., "*.py"). Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a match with the following keys:
            - file_path (str): The absolute path to the file containing the match.
            - line_number (int): The line number of the match.
            - line_content (str): The content of the line containing the match.

    Raises:
        WorkspaceNotAvailableError: If the workspace root is not configured.
        InvalidInputError: If the search path is outside of the workspace.
    """
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    search_path = path or workspace_root
    if not os.path.isabs(search_path):
        search_path = os.path.join(workspace_root, search_path)

    if not _is_within_workspace(search_path, workspace_root):
        raise InvalidInputError("Search path is outside of the workspace")

    fs = DB.get("file_system", {})
    results = []
    for item_path, item_info in fs.items():
        if not item_info.get("is_directory") and item_path.startswith(search_path):
            if include and not fnmatch.fnmatch(os.path.basename(item_path), include):
                continue

            for i, line in enumerate(item_info.get("content_lines", [])):
                if re.search(pattern, line):
                    results.append(
                        {
                            "file_path": item_path,
                            "line_number": i + 1,
                            "line_content": line.strip(),
                        }
                    )
    return results
