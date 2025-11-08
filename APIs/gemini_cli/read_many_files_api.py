"""Gemini-CLI read-many-files tool implementation.

This tool reads content from multiple files specified by paths or glob patterns,
concatenating text files and handling images/PDFs as base64 when explicitly requested.
"""
from __future__ import annotations
from common_utils.tool_spec_decorator import tool_spec

from typing import Dict, Any, List, Optional
import os
import pathlib

from .SimulationEngine.db import DB
from common_utils.log_complexity import log_complexity
from .SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotAvailableError
from .SimulationEngine.file_utils import (
    detect_file_type,
    process_single_file_content,
    expand_glob_patterns,
    filter_gitignore,
    DEFAULT_OUTPUT_SEPARATOR_FORMAT,
    DEFAULT_EXCLUDES
)
from .SimulationEngine.utils import conditional_common_file_system_wrapper

@log_complexity  # type: ignore[attr-defined]
@conditional_common_file_system_wrapper
@tool_spec(
    spec={
        'name': 'read_many_files',
        'description': """ Read content from multiple files specified by paths or glob patterns.
        
        This function reads and concatenates content from multiple files. For text files,
        it concatenates their content with separators. For image/PDF files explicitly
        requested, it returns them as base64-encoded data. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'paths': {
                    'type': 'array',
                    'description': """ Required. Array of glob patterns or paths relative to the
                    workspace root. Examples: ['src/**/*.py'], ['README.md', 'docs/'] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'include': {
                    'type': 'array',
                    'description': """ Additional glob patterns to include. These are
                    merged with `paths`. Example: ["*.test.py"] to add test files. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'exclude': {
                    'type': 'array',
                    'description': """ Glob patterns for files/directories to exclude.
                    Added to default excludes if useDefaultExcludes is True. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'recursive': {
                    'type': 'boolean',
                    'description': """ Whether to search recursively. Primarily controlled
                    by `**` in glob patterns. Defaults to True. """
                },
                'useDefaultExcludes': {
                    'type': 'boolean',
                    'description': """ Whether to apply default exclusion patterns
                    (e.g., node_modules, .git, binary files). Defaults to True. """
                },
                'respect_git_ignore': {
                    'type': 'boolean',
                    'description': """ Whether to respect .gitignore patterns.
                    Defaults to True. """
                }
            },
            'required': [
                'paths'
            ]
        }
    }
)
def read_many_files(
    paths: List[str],
    *,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    recursive: Optional[bool] = True,
    useDefaultExcludes: Optional[bool] = True,
    respect_git_ignore: Optional[bool] = True,
) -> Dict[str, Any]:
    """Read content from multiple files specified by paths or glob patterns.

    This function reads and concatenates content from multiple files. For text files,
    it concatenates their content with separators. For image/PDF files explicitly
    requested, it returns them as base64-encoded data.

    Args:
        paths (List[str]): Required. Array of glob patterns or paths relative to the
            workspace root. Examples: ['src/**/*.py'], ['README.md', 'docs/']
        include (Optional[List[str]]): Additional glob patterns to include. These are
            merged with `paths`. Example: ["*.test.py"] to add test files.
        exclude (Optional[List[str]]): Glob patterns for files/directories to exclude.
            Added to default excludes if useDefaultExcludes is True.
        recursive (Optional[bool]): Whether to search recursively. Primarily controlled
            by `**` in glob patterns. Defaults to True.
        useDefaultExcludes (Optional[bool]): Whether to apply default exclusion patterns
            (e.g., node_modules, .git, binary files). Defaults to True.
        respect_git_ignore (Optional[bool]): Whether to respect .gitignore patterns.
            Defaults to True.

    Returns:
        Dict[str, Any]: A dictionary containing the operation result with keys:
            - success (bool): Whether the operation succeeded
            - message (str): Success/status message
            - content_parts (List): List of content parts (strings for text, objects for media)
            - processed_files (List[str]): List of successfully processed file paths
            - skipped_files (List[Dict]): List of skipped files with reasons
            - total_files_found (int): Total number of files discovered
            - total_files_processed (int): Number of files successfully processed

    Raises:
        InvalidInputError: If paths is empty, not a list, or contains invalid patterns.
        WorkspaceNotAvailableError: If workspace_root is not configured.
    """
    # ================== Parameter Validation ==================
    if not isinstance(paths, list) or len(paths) == 0:
        raise InvalidInputError("'paths' must be a non-empty list of strings")
    
    for path_item in paths:
        if not isinstance(path_item, str) or path_item.strip() == "":
            raise InvalidInputError("All items in 'paths' must be non-empty strings")
    
    if include is not None:
        if not isinstance(include, list):
            raise InvalidInputError("'include' must be a list of strings or None")
        for item in include:
            if not isinstance(item, str):
                raise InvalidInputError("All items in 'include' must be strings")
    
    if exclude is not None:
        if not isinstance(exclude, list):
            raise InvalidInputError("'exclude' must be a list of strings or None")
        for item in exclude:
            if not isinstance(item, str):
                raise InvalidInputError("All items in 'exclude' must be strings")
    
    if recursive is not None and not isinstance(recursive, bool):
        raise InvalidInputError("'recursive' must be a boolean or None")
    
    if useDefaultExcludes is not None and not isinstance(useDefaultExcludes, bool):
        raise InvalidInputError("'useDefaultExcludes' must be a boolean or None")
    
    if respect_git_ignore is not None and not isinstance(respect_git_ignore, bool):
        raise InvalidInputError("'respect_git_ignore' must be a boolean or None")

    # ================== Workspace Validation ==================
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # ================== Set Default Values ==================
    include = include or []
    exclude = exclude or []
    recursive = recursive if recursive is not None else True
    useDefaultExcludes = useDefaultExcludes if useDefaultExcludes is not None else True
    respect_git_ignore = respect_git_ignore if respect_git_ignore is not None else True

    # ================== Build Search Patterns ==================
    search_patterns = paths + include
    
    # Build exclusion patterns
    effective_excludes = exclude[:]
    if useDefaultExcludes:
        effective_excludes.extend(DEFAULT_EXCLUDES)
    
    # ================== File Discovery ==================
    try:
        files_to_consider = expand_glob_patterns(
            search_patterns, 
            workspace_root, 
            effective_excludes, 
            recursive
        )
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during file search: {str(e)}",
            "content_parts": [],
            "processed_files": [],
            "skipped_files": [],
            "total_files_found": 0,
            "total_files_processed": 0,
        }

    # ================== Apply Git Ignore Filtering ==================
    if respect_git_ignore:
        try:
            # Convert file paths to (file_path, file_meta) tuples for filter_gitignore
            file_system = DB.get("file_system", {})
            files_with_meta = [(file_path, file_system.get(file_path, {})) for file_path in files_to_consider]
            
            # Apply gitignore filtering
            filtered_files_with_meta = filter_gitignore(files_with_meta, workspace_root)
            
            # Extract just the file paths
            files_to_consider = [file_path for file_path, _ in filtered_files_with_meta]
        except Exception as e:
            return {
                "success": False,
                "message": f"Error during gitignore filtering: {str(e)}",
                "content_parts": [],
                "processed_files": [],
                "skipped_files": [],
                "total_files_found": 0,
                "total_files_processed": 0,
            }

    # ================== Process Files ==================
    content_parts = []
    processed_files = []
    skipped_files = []
    
    for file_path in files_to_consider:
        relative_path = os.path.relpath(file_path, workspace_root).replace("\\", "/")
        
        # Check if image/PDF files are explicitly requested
        file_type = detect_file_type(file_path)
        if file_type in ["image", "pdf"]:
            file_extension = pathlib.Path(file_path).suffix.lower()
            file_name_without_ext = pathlib.Path(file_path).stem
            
            requested_explicitly = any(
                file_extension in pattern.lower() or file_name_without_ext in pattern
                for pattern in search_patterns
            )
            
            if not requested_explicitly:
                skipped_files.append({
                    "path": relative_path,
                    "reason": "asset file (image/pdf) was not explicitly requested by name or extension"
                })
                continue
        
        # Process the file
        file_result = process_single_file_content(file_path, workspace_root)
        
        if file_result.get("error"):
            skipped_files.append({
                "path": relative_path,
                "reason": f"Read error: {file_result['error']}"
            })
        else:
            llm_content = file_result["llm_content"]
            
            if isinstance(llm_content, str):
                # Text content - add separator
                separator = DEFAULT_OUTPUT_SEPARATOR_FORMAT.format(filePath=relative_path)
                content_parts.append(f"{separator}\n\n{llm_content}\n\n")
            else:
                # Binary content (image/PDF) - add as-is
                content_parts.append(llm_content)
            
            processed_files.append(relative_path)

    # ================== Build Response ==================
    total_files_found = len(files_to_consider)
    total_files_processed = len(processed_files)
    
    if total_files_processed > 0:
        message = f"Successfully read and concatenated content from {total_files_processed} file(s)"
        if skipped_files:
            message += f". Skipped {len(skipped_files)} file(s)"
    elif skipped_files:
        message = f"No files were processed. Skipped {len(skipped_files)} file(s)"
    else:
        message = "No files matching the criteria were found"
    
    if not content_parts:
        content_parts = ["No files matching the criteria were found or all were skipped."]
    
    return {
        "success": True,
        "message": message,
        "content_parts": content_parts,
        "processed_files": processed_files,
        "skipped_files": skipped_files,
        "total_files_found": total_files_found,
        "total_files_processed": total_files_processed,
    } 