from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
import os  # For path manipulation like basename, dirname
import re
import logging
from typing import Any, Dict, List, Optional, Union  # Common type hints
import tempfile
import subprocess
import shlex
import logging
import inspect
import json
from mermaid import Mermaid
import copy
import shutil

from json_repair import repair_json

# Import the DB object and utility functions
from .SimulationEngine.db import DB, validate_workspace_hydration  # This is the application's in-memory database
from .SimulationEngine import utils, custom_errors  # Utility functions
from .SimulationEngine.llm_interface import call_llm
from .SimulationEngine.utils import with_common_file_system  # Import the decorator

from .SimulationEngine.qdrant_config import QdrantManager, transform_qdrant_results_via_llm
from .SimulationEngine.chunker import chunk_codebase

# Import the environment manager
from common_utils import (
    prepare_command_environment,
    expand_variables,
    handle_env_command
)

# Import the shared session manager
from common_utils import session_manager

# This function requires 'thefuzz' library for fuzzy matching.
from thefuzz import process as fuzzy_process
from .SimulationEngine.utils import add_line_numbers

from .SimulationEngine.custom_errors import (
    InvalidInputError,
    LastEditNotFoundError,
    FileNotInWorkspaceError,
    LintFixingError,
    FailedToApplyLintFixesError,
    MermaidSyntaxError,
    CommandExecutionError,
    LLMGenerationError,
    MetadataError,
)

# --- Logger Setup for this __init__.py module ---
# Get a logger instance specific to this top-level module.
logger = logging.getLogger(__name__) # Will typically be 'cursor' if run as package

def _log_init_message(level: int, message: str, exc_info: bool = False) -> None:
    """Logs a message with caller information from within this module.

    This utility function enhances log messages by automatically adding caller 
    information (function name and line number) to provide better debugging context.
    It uses frame inspection to determine the calling function and formats the 
    message accordingly before logging at the specified level.

    Args:
        level (int): The logging level to use (e.g., logging.ERROR, logging.WARNING, 
            logging.INFO, logging.DEBUG). Defaults to DEBUG for unrecognized levels.
        message (str): The log message to be recorded.
        exc_info (bool): Whether to include exception information in the log entry.
            Only used for ERROR and WARNING level messages. Defaults to False.

    Returns:
        None: This function does not return a value.

    Raises:
        Exception: Frame inspection errors are caught and ignored silently, falling
            back to logging the original message without caller information.
    """
    log_message = message
    try:
        # Get the frame of the function within __init__.py that called this helper.
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        if caller_frame and caller_frame.f_code:
            func_name = caller_frame.f_code.co_name
            line_no = caller_frame.f_lineno
            log_message = f"{func_name}:{line_no} - {message}"
    except Exception: # Fallback if frame inspection fails.
        pass

    # Log using the standard levels; defaults to DEBUG.
    if level == logging.ERROR: logger.error(log_message, exc_info=exc_info)
    elif level == logging.WARNING: logger.warning(log_message, exc_info=exc_info)
    elif level == logging.INFO: logger.info(log_message)
    else: logger.debug(log_message)


def _realpath_or_original(path: str) -> str:
    """Return os.path.realpath(path) when possible, otherwise the original path."""
    try:
        return os.path.realpath(path)
    except (OSError, TypeError):
        return path


def _is_within_directory(path: str, root: str) -> bool:
    """Return True when path is within root (after realpath normalization)."""
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


# --- Function Implementations ---
@with_common_file_system
@tool_spec(
    spec={
        'name': 'list_dir',
        'description': """ Lists the immediate contents of a directory within the configured workspace.
        
        Resolves the provided path relative to the workspace root and queries the
        internal file system representation to find direct children (files and
        subdirectories).
        
        This function is primarily intended for exploring the workspace structure
        and discovering file/directory names at a specific location. It often serves
        as a preliminary step before using more targeted tools like `read_file`,
        `grep_search`, or `codebase_search` on specific items found in the listing. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'relative_workspace_path': {
                    'type': 'string',
                    'description': """ The path of the directory to list,
                    relative to the workspace root. An empty string or '.' refers
                    to the workspace root itself. Leading slashes are stripped. """
                },
                'explanation': {
                    'type': 'string',
                    'description': """ A description of the reason for
                    this operation, potentially used for logging or auditing. Defaults to None. """
                }
            },
            'required': [
                'relative_workspace_path'
            ]
        }
    }
)
def list_dir(
    relative_workspace_path: str, explanation: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists the immediate contents of a directory within the configured workspace.

    Resolves the provided path relative to the workspace root and queries the
    internal file system representation to find direct children (files and
    subdirectories).

    This function is primarily intended for exploring the workspace structure
    and discovering file/directory names at a specific location. It often serves
    as a preliminary step before using more targeted tools like `read_file`,
    `grep_search`, or `codebase_search` on specific items found in the listing.

    Args:
        relative_workspace_path (str): The path of the directory to list,
            relative to the workspace root. An empty string or '.' refers
            to the workspace root itself. Leading slashes are stripped.
        explanation (Optional[str], optional): A description of the reason for
            this operation, potentially used for logging or auditing. Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
        represents a file or subdirectory found within the specified path.
        Each item dictionary contains:
            - 'path' (str): The full, normalized absolute path of the item.
            - 'name' (str): The base name of the item (file or directory name).
            - 'is_directory' (bool): True if the item is a directory, False otherwise.
            - 'size_bytes' (int): The size of the item in bytes. For directories,
              this is typically 0 in this representation.
            - 'last_modified' (str): An ISO 8601 timestamp string indicating
              the last modification time of the item.
        Returns an empty list if the directory exists and is valid but contains no items.

    Raises:
        ValueError: If 'workspace_root' is not configured or the resolved path
            is outside the permitted workspace boundaries.
        FileNotFoundError: If the target directory path does not exist.
        NotADirectoryError: If the path exists but is not a directory.
        InvalidInputError: If input arguments have invalid types.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    if not isinstance(relative_workspace_path, str):
        raise InvalidInputError("Input 'relative_workspace_path' must be a string.")
    if explanation is not None and not isinstance(explanation, str):
        raise InvalidInputError("Input 'explanation' must be a string if provided, or None.")

    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError(
            "Workspace root is not configured in the application settings."
        )

    # Normalize workspace_root once
    normalized_workspace_root = os.path.normpath(workspace_root)

    # Process the relative_workspace_path to ensure it's correctly joined
    if not relative_workspace_path or relative_workspace_path == ".":
        target_dir_abs_path = normalized_workspace_root
    else:
        # Ensure the path is treated as relative by stripping any leading slashes.
        # This prevents os.path.join from treating it as an absolute path.
        path_segment = relative_workspace_path.lstrip("/")
        if not path_segment:  # Input was only slashes (e.g., '/', '///')
            target_dir_abs_path = normalized_workspace_root
        else:
            target_dir_abs_path = os.path.normpath(
                os.path.join(normalized_workspace_root, path_segment)
            )

    # Security check: Ensure the fully resolved target path is within (or is) the workspace root.
    # This prevents directory traversal attacks (e.g., if relative_workspace_path was '../../...').
    if (
        not target_dir_abs_path.startswith(normalized_workspace_root)
        and target_dir_abs_path != normalized_workspace_root
    ):  # Allow listing the root itself
        raise ValueError(
            f"Path '{relative_workspace_path}' resolves to '{target_dir_abs_path}', which is outside the permitted workspace '{normalized_workspace_root}'."
        )

    # Check if the target directory exists in our DB and is actually a directory.
    target_dir_entry = DB.get("file_system", {}).get(target_dir_abs_path)

    if not target_dir_entry:
        raise FileNotFoundError(f"The specified path does not exist: {target_dir_abs_path}")
    if not target_dir_entry.get("is_directory"):
        raise NotADirectoryError(f"The specified path is not a directory: {target_dir_abs_path}")

    # Target path is a valid, existing directory in the DB.
    results: List[Dict[str, Any]] = []
    file_system_entries = DB.get("file_system", {})

    # Iterate through all known file system entries to find direct children.
    for item_path_str, item_entry_data in file_system_entries.items():
        normalized_item_path = os.path.normpath(item_path_str)

        # To be a direct child, the item's parent directory must be the target directory.
        # Also, the item itself must not be the target directory.
        if (
            os.path.normpath(os.path.dirname(normalized_item_path))
            == target_dir_abs_path
            and normalized_item_path != target_dir_abs_path
        ):
            results.append(
                {
                    "path": item_entry_data.get(
                        "path", normalized_item_path
                    ),  # Prefer 'path' from entry
                    "name": os.path.basename(normalized_item_path),
                    "is_directory": item_entry_data.get("is_directory", False),
                    "size_bytes": item_entry_data.get("size_bytes", 0),
                    "last_modified": item_entry_data.get(
                        "last_modified", utils.get_current_timestamp_iso()
                    ),  # Default if missing
                }
            )

    # Sort results by name for consistent and predictable output.
    results.sort(key=lambda x: x["name"])
    return results


@with_common_file_system
@tool_spec(
    spec={
        'name': 'delete_file',
        'description': """ Deletes a specified file from the application's managed file system.
        
        Resolves the provided path relative to the workspace root and attempts to
        remove the corresponding file entry from the application's internal file
        system representation.
        
        This operation raises appropriate errors for failure scenarios: if the file does
        not exist, if the target path refers to a directory, or if path resolution fails.
        Only successful deletions return a success dictionary. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'target_file': {
                    'type': 'string',
                    'description': """ The path of the file to be deleted, relative to the
                    workspace root. Leading slashes are stripped to ensure the path is
                    treated as relative. """
                },
                'explanation': {
                    'type': 'string',
                    'description': """ A description of the reason for
                    this deletion. Not used in the return value but may be utilized for
                    logging or auditing. Defaults to None. """
                }
            },
            'required': [
                'target_file'
            ]
        }
    }
)
def delete_file(target_file: str, explanation: Optional[str] = None) -> Dict[str, Any]:
    """Deletes a specified file from the application's managed file system.

    Resolves the provided path relative to the workspace root and attempts to
    remove the corresponding file entry from the application's internal file
    system representation.

    This operation raises appropriate errors for failure scenarios: if the file does
    not exist, if the target path refers to a directory, or if path resolution fails.
    Only successful deletions return a success dictionary.

    Args:
        target_file (str): The path of the file to be deleted, relative to the
            workspace root. Leading slashes are stripped to ensure the path is
            treated as relative.
        explanation (Optional[str], optional): A description of the reason for
            this deletion. Not used in the return value but may be utilized for
            logging or auditing. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome of the operation.
        It contains:
            - 'success' (bool): True if the file was successfully deleted. This
              function raises exceptions for error cases and does not return False.
            - 'message' (str): A message describing the outcome.
            - 'path_processed' (Optional[str]): The absolute path that was
              processed for deletion.

    Raises:
        ValueError: If 'workspace_root' is not configured, or if the resolved
            path for `target_file` would point outside the configured workspace.
        InvalidInputError: If the target file path is empty, invalid, or arguments have invalid types.
        IsADirectoryError: If the target path refers to a directory.
        FileNotFoundError: If the target file does not exist.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
        RuntimeError: For unexpected errors during the deletion process.
    """
    if not isinstance(target_file, str):
        raise InvalidInputError("Input 'target_file' must be a string.")
    if explanation is not None and not isinstance(explanation, str):
        raise InvalidInputError("Input 'explanation' must be a string if provided, or None.")

    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError("Workspace root is not configured in the application settings.")
    normalized_workspace_root = os.path.normpath(workspace_root)

    if not target_file:
        raise InvalidInputError("Target file path cannot be empty.")

    # Ensure target_file is treated as relative to the workspace_root.
    path_segment = target_file.lstrip("/")
    if not path_segment:
        raise InvalidInputError(f"Target '{target_file}' is not a valid file path for deletion.")
    
    abs_target_path = os.path.normpath(os.path.join(normalized_workspace_root, path_segment))

    # Verify the resolved path is within the workspace boundaries.
    if not abs_target_path.startswith(normalized_workspace_root) and abs_target_path != normalized_workspace_root:
        raise ValueError(f"Path '{target_file}' resolves to '{abs_target_path}', which is outside the permitted workspace '{normalized_workspace_root}'.")

    file_system = DB.get("file_system", {})

    if abs_target_path not in file_system:
        # If the file does not exist, consider the deletion successful (idempotent).
        raise FileNotFoundError(f"File not found at '{abs_target_path}'. No action taken.")

    entry_to_delete = file_system.get(abs_target_path)
    if entry_to_delete.get("is_directory", False):
        raise IsADirectoryError(f"Target '{abs_target_path}' is a directory, not a file. Deletion aborted.")

    # At this point, the target exists and is confirmed to be a file.
    try:
        del file_system[abs_target_path]

        # If the deleted file was noted in 'last_edit_params', clear those params.
        last_edit = DB.get("last_edit_params")
        if last_edit and last_edit.get("target_file") == abs_target_path:
            DB["last_edit_params"] = None

        return {
            "success": True,
            "message": f"File '{abs_target_path}' deleted successfully.",
            "path_processed": abs_target_path,
        }
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while deleting file '{abs_target_path}': {str(e)}") from e

@with_common_file_system
@tool_spec(
    spec={
        'name': 'file_search',
        'description': """ Performs a fuzzy search for files based on matching a query against file paths.
        
        Searches through the file paths within the application's internal file system
        representation using fuzzy matching algorithms. This is useful when part of 
        a file path or name is known, but the exact location is not. It returns a 
        ranked list of file paths (excluding directories) based on similarity to the query.
        
        Results are capped at a maximum of 10 matches; more specific queries will
        yield narrower results. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The string to search for within file paths. Fuzzy matching
                    attempts to account for typos and partial matches. """
                },
                'explanation': {
                    'type': 'string',
                    'description': """ A required sentence explaining the reason for this search,
                    typically for logging or auditing purposes. """
                }
            },
            'required': [
                'query',
                'explanation'
            ]
        }
    }
)
def file_search(
    query: str,
    explanation: str,  # This explanation is required by the function's contract.
) -> List[str]:
    """Performs a fuzzy search for files based on matching a query against file paths.

    Searches through the file paths within the application's internal file system
    representation using fuzzy matching algorithms. This is useful when part of 
    a file path or name is known, but the exact location is not. It returns a 
    ranked list of file paths (excluding directories) based on similarity to the query.

    Results are capped at a maximum of 10 matches; more specific queries will
    yield narrower results.

    Args:
        query (str): The string to search for within file paths. Fuzzy matching
                     attempts to account for typos and partial matches.
        explanation (str): A required sentence explaining the reason for this search,
                           typically for logging or auditing purposes.

    Returns:
        List[str]: A list of absolute, normalized file paths that best match the
                   query, sorted by relevance (highest score first). The list
                   is capped at 10 results. Returns an empty list if no suitable
                   matches are found, the query is empty, or no files exist.

    Raises:
        ImportError: If the required 'thefuzz' library is not installed.
                     (Handled implicitly by the top-level import).
        InvalidInputError: If input arguments have invalid types.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    if not isinstance(query, str):
        raise InvalidInputError("Input 'query' must be a string.")
    if not isinstance(explanation, str):
        raise InvalidInputError("Input 'explanation' must be a string.")

    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()

    if not query:
        return []

    file_system_entries = DB.get("file_system", {})
    candidate_paths = []

    # Collect all valid file paths from the DB's file system representation.
    for path_str, entry_data in file_system_entries.items():
        if not entry_data.get("is_directory", False):
            # Use the canonical path stored in the entry for matching.
            raw_path = entry_data.get("path", path_str)
            normalized = utils.normalize_path(raw_path)
            candidate_paths.append(normalized)

    if not candidate_paths:
        return []  # No files to search within.

    # Normalize the query
    normalized_query = utils.normalize_path(query)

    # --- Fuzzy Matching using thefuzz ---
    # Find the best matches using fuzzy logic.
    # `process.extract` compares the query against all candidate paths.
    # `processor=str.lower` ensures case-insensitive comparison.
    # A limit slightly higher than the final cap allows for score filtering.
    extracted_matches = fuzzy_process.extract(
        normalized_query,
        candidate_paths,
        limit=15,  # Retrieve slightly more candidates for potential score filtering
        processor=str.lower,
    )

    # Define a minimum similarity score (0-100) required to include a result.
    # Adjust this threshold based on desired sensitivity to fuzziness.
    # Values between 60 and 80 are common starting points.
    score_threshold = 55

    # Filter the extracted matches based on the score threshold.
    # `extract` returns tuples of (path, score), sorted by score descending.
    top_matches = [
        match[0] for match in extracted_matches if match[1] >= score_threshold
    ]

    # Return the highest-scoring results, up to the specified cap (10).
    return top_matches[:10]


@with_common_file_system
@tool_spec(
    spec={
        'name': 'grep_search',
        'description': """ Performs a text search using a regular expression across applicable files.
        
        Scans the content of files within the application's internal file system
        representation, optionally filtering by include/exclude glob patterns.
        It searches each line using the provided regex query, respecting case
        sensitivity. This function is optimized for finding exact text matches or
        specific patterns and is generally more precise than semantic search for
        locating known symbols, function names, or literal strings.
        
        The query must be a valid regex pattern; ensure special characters intended
        for literal matching are properly escaped (e.g., '\\.' to match a period).
        Found matches include file path, line number, and content, capped at the
        first 50 matches found across all searched files. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The regular expression pattern to search for. Callers should
                    ensure the pattern is valid and escape special characters if
                    literal matching is intended (e.g., '\\.' for a literal dot). """
                },
                'explanation': {
                    'type': 'string',
                    'description': """ A description of the reason for
                    this search, primarily for logging or auditing. Defaults to None. """
                },
                'case_sensitive': {
                    'type': 'boolean',
                    'description': """ Determines if the regex search respects
                    character case (True) or ignores case (False). Defaults to True. """
                },
                'include_pattern': {
                    'type': 'string',
                    'description': """ A glob pattern (e.g., '*.py', 'src/**')
                    to filter which file paths are included in the search. If omitted,
                    all files passing the exclude filter are considered. Defaults to None. """
                },
                'exclude_pattern': {
                    'type': 'string',
                    'description': """ A glob pattern to filter
                    which file paths are excluded from the search. Exclusions override
                    inclusions. Defaults to None. """
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def grep_search(
    query: str,
    explanation: Optional[str] = None,
    case_sensitive: bool = True,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Performs a text search using a regular expression across applicable files.

    Scans the content of files within the application's internal file system
    representation, optionally filtering by include/exclude glob patterns.
    It searches each line using the provided regex query, respecting case
    sensitivity. This function is optimized for finding exact text matches or
    specific patterns and is generally more precise than semantic search for
    locating known symbols, function names, or literal strings.

    The query must be a valid regex pattern; ensure special characters intended
    for literal matching are properly escaped (e.g., '\\.' to match a period).
    Found matches include file path, line number, and content, capped at the
    first 50 matches found across all searched files.

    Args:
        query (str): The regular expression pattern to search for. Callers should
                     ensure the pattern is valid and escape special characters if
                     literal matching is intended (e.g., '\\.' for a literal dot).
        explanation (Optional[str], optional): A description of the reason for
            this search, primarily for logging or auditing. Defaults to None.
        case_sensitive (bool, optional): Determines if the regex search respects
            character case (True) or ignores case (False). Defaults to True.
        include_pattern (Optional[str], optional): A glob pattern (e.g., '*.py', 'src/**')
            to filter which file paths are included in the search. If omitted,
            all files passing the exclude filter are considered. Defaults to None.
        exclude_pattern (Optional[str], optional): A glob pattern to filter
            which file paths are excluded from the search. Exclusions override
            inclusions. Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries for each regex match found.
        Each dictionary contains:
            - 'file_path' (str): Absolute path of the file with the match.
            - 'line_number' (int): 1-based line number of the match.
            - 'line_content' (str): The text content of the matching line
                                    (trailing newline character removed).
        The list is capped at the first 50 matches found across all searched files.
        Returns an empty list if the query is empty, invalid, or yields no matches.

    Raises:
        ValueError: If the provided regex pattern is invalid.
        InvalidInputError: If input arguments have invalid types.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    if not isinstance(query, str):
        raise InvalidInputError("Input 'query' must be a string.")
    if explanation is not None and not isinstance(explanation, str):
        raise InvalidInputError("Input 'explanation' must be a string if provided, or None.")
    if not isinstance(case_sensitive, bool):
        raise InvalidInputError("Input 'case_sensitive' must be a boolean.")

    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()
    if include_pattern is not None and not isinstance(include_pattern, str):
        raise InvalidInputError("Input 'include_pattern' must be a string if provided, or None.")
    if exclude_pattern is not None and not isinstance(exclude_pattern, str):
        raise InvalidInputError("Input 'exclude_pattern' must be a string if provided, or None.")

    if not query:
        # An empty regex query is ambiguous or invalid in most contexts.
        return []

    # Compile the regular expression for efficiency and validity check.
    regex_flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled_regex = re.compile(query, regex_flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern provided to grep_search: '{query}'. Error: {e}.")

    found_matches: List[Dict[str, Any]] = []
    match_limit = 50
    file_system_entries = DB.get("file_system", {})

    # Prepare patterns for the utility function (needs lists or None)
    include_list = [include_pattern] if include_pattern else None
    exclude_list = [exclude_pattern] if exclude_pattern else None

    # Iterate through file system entries. Sorting keys provides deterministic order.
    sorted_paths = sorted(file_system_entries.keys())

    for path_str in sorted_paths:
        if len(found_matches) >= match_limit:
            break  # Stop searching once the match limit is reached.

        entry_data = file_system_entries[path_str]

        # Only search within files.
        if entry_data.get("is_directory", False):
            continue

        # Use the canonical path from the entry for filtering, if available.
        canonical_path = entry_data.get("path", path_str)

        # Apply include/exclude path filtering.
        if not utils.matches_glob_patterns(
            canonical_path, include_patterns=include_list, exclude_patterns=exclude_list
        ):
            continue

        # Search within the lines of the current file.
        content_lines = entry_data.get("content_lines", [])
        for line_idx, line_content in enumerate(content_lines):
            if compiled_regex.search(line_content):
                # Found a match, record it.
                found_matches.append(
                    {
                        "file_path": canonical_path,
                        "line_number": line_idx + 1,  # Use 1-based indexing for lines.
                        "line_content": line_content.rstrip(
                            "\n"
                        ),  # Remove trailing newline.
                    }
                )
                if len(found_matches) >= match_limit:
                    break  # Stop processing this file and outer loop.

    return found_matches


@with_common_file_system
@tool_spec(
    spec={
        'name': 'edit_file',
        'description': """ Proposes an edit to an existing file or creates a new file.

        This function applies structured edits. Use delimiter comment lines that contain the phrase
        `... existing code ...` to indicate preserved/skipped regions between code segments.
        Accepted delimiter styles include: `//`, `#`, `--`, `;`, `REM`, and `/* ... */`.
        Matching is case-insensitive for the phrase itself.

        Rules:
          - No delimiters present: `code_edit` replaces the entire file.
          - With delimiters: Provide one or more code segments separated by delimiter lines. Each
            code segment should include 1–5 unchanged lines of leading context and 1–5 unchanged
            lines of trailing context from the original file to uniquely anchor the change.
            At file boundaries, you may omit the side that does not exist (prepend: omit leading
            context; append: omit trailing context).
          - Use delimiter lines to preserve original code between segments or at the ends. Ending
            with a delimiter preserves the remainder of the original file after the last segment,
            ending with a segment discards the remainder.
          - Include only minimal unchanged context inside segments; do not repeat large blocks of
            unmodified code. Represent skipped, unchanged regions with delimiter lines.

        Example shape:
        ```
        // ... existing code ...
        FIRST_EDIT
        // ... existing code ...
        SECOND_EDIT
        // ... existing code ...
        THIRD_EDIT
        // ... existing code ...
        ```
        """,
        'parameters': {
            'type': 'object',
            'properties': {
                'target_file': {
                    'type': 'string',
                    'description': 'The target file to modify. This argument is always specified first. Its path can be relative to the workspace or absolute, and an absolute path is preserved.'
                },
                'code_edit': {
                    'type': 'string',
                    'description': 'Contains the precise lines to edit. When using delimiters, include minimal unchanged context (1–5 lines before and after) inside each code segment so the engine can uniquely anchor the change; represent skipped regions with a language-appropriate delimiter comment like `// ... existing code ...`. If no delimiters are present, the entire file content is replaced by `code_edit`.'
                },
                'instructions': {
                    'type': 'string',
                    'description': 'A single sentence instruction describing the change being made in the sketched edit. It assists the less intelligent model in applying the edit by providing a concise summary that avoids repeating information from previous messages and disambiguates any uncertainty in the edit.'
                }
            },
            'required': [
                'target_file',
                'code_edit',
                'instructions'
            ]
        }
    }
)
def edit_file(target_file: str, code_edit: str, instructions: str) -> Dict[str, Any]:
    """Proposes an edit to an existing file or creates a new file.

    This function applies structured edits with optional delimiter comment lines that contain
    the phrase `... existing code ...` to indicate preserved/skipped regions between code segments.
    Accepted delimiter styles include: `//`, `#`, `--`, `;`, `REM`, and `/* ... */`.
    The phrase match is case-insensitive.

    For example:
    ```
    // ... existing code ...
    FIRST_EDIT
    // ... existing code ...
    SECOND_EDIT
    // ... existing code ...
    THIRD_EDIT
    // ... existing code ...
    ```

    Behavior:
      - If no delimiter lines are present in `code_edit`, the provided content fully replaces the
        file.
      - If delimiter lines are present, `code_edit` is interpreted as one or more code segments
        separated by delimiters. Each code segment should include 1–5 unchanged lines of leading
        context and 1–5 unchanged lines of trailing context from the original file to uniquely
        anchor the change. At file boundaries, you may omit the side that does not exist (prepend:
        omit leading context; append: omit trailing context).
      - Delimiters preserve original code between segments or at the ends. Ending with a delimiter
        preserves the remainder of the original file after the last segment; ending with a segment
        discards the remainder.

    Creating a new file involves specifying the entire file content in the `code_edit` field.

    Args:
        target_file (str): The target file to modify. This argument is always specified first. Its path can be relative to the workspace or absolute, and an absolute path is preserved.
        code_edit (str): Contains the precise lines to edit. When using delimiters, include minimal
            unchanged context (1–5 lines before and after) inside each code segment to anchor the
            change; represent skipped regions with language-appropriate delimiter comment lines.
            If no delimiters are present, the entire file content is replaced by `code_edit`.
        instructions (str): A single sentence instruction describing the change being made in the sketched edit. It assists the less intelligent model in applying the edit by providing a concise summary that avoids repeating information from previous messages and disambiguates any uncertainty in the edit.

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome. Contains:
            - 'success' (bool): True if the file was successfully edited or created.
            - 'message' (str): A message describing the outcome.
            - 'file_path' (str): The absolute, normalized path of the file processed.

    Raises:
        ValueError: If path resolution fails, path is outside workspace, or code edit fails due to context matching issues or workspace is not properly initialized.
        IsADirectoryError: If the target path is a directory.
        FileNotFoundError: If a parent directory does not exist for a new file.
        InvalidInputError: If the target file path for creation is invalid or arguments have invalid types.
        RuntimeError: For any other unexpected errors.
    """
    if not isinstance(target_file, str):
        raise InvalidInputError("Input 'target_file' must be a string.")
    if not isinstance(code_edit, str):
        raise InvalidInputError("Input 'code_edit' must be a string.")
    if not isinstance(instructions, str):
        raise InvalidInputError("Input 'instructions' must be a string.")

    try:
        # Step 1: Resolve path using the utility.
        abs_path = utils.get_absolute_path(target_file)

        # Step 2: Explicit boundary check.
        workspace_root_val = DB.get("workspace_root")
        if not workspace_root_val:
            raise ValueError("Workspace root is not configured.")
        normalized_workspace_root = os.path.normpath(workspace_root_val)
        if not abs_path.startswith(normalized_workspace_root) and abs_path != normalized_workspace_root:
            raise ValueError(
                f"Resolved path '{abs_path}' (from target '{target_file}') is outside the permitted workspace '{normalized_workspace_root}'."
            )

        # Step 3: Proceed with file operations.
        existing_entry = utils.get_file_system_entry(abs_path)

        if existing_entry and existing_entry.get("is_directory", False):
            raise IsADirectoryError(f"Target path '{abs_path}' exists but is a directory. Operation aborted.")

        basename_for_explanation = os.path.basename(abs_path)
        params_for_reapply = {
            "target_file": abs_path,
            "code_edit": code_edit,
            "instructions": instructions,
            "explanation": f"Attempted edit for '{basename_for_explanation}' that failed content application.",
        }

        file_system = DB.get("file_system", {})

        if not existing_entry:
            # --- Create New File ---
            parent_dir = os.path.dirname(abs_path)
            if parent_dir == abs_path:
                raise InvalidInputError(f"Invalid target file path for creation: '{abs_path}'. Cannot be its own parent.")

            parent_entry = file_system.get(parent_dir)
            is_parent_ws_root = parent_dir == normalized_workspace_root

            if not (parent_entry and parent_entry.get("is_directory", False)) and not is_parent_ws_root:
                raise FileNotFoundError(f"Parent directory '{parent_dir}' does not exist for new file '{abs_path}'.")

            # Fail-fast: if attempting to create a new file and the first non-empty line
            # of code_edit is a delimiter (e.g., "// ... existing code ..."), provide a
            # clear, actionable error instead of bubbling up a low-level context error.
            try:
                first_non_empty = next((ln for ln in code_edit.splitlines() if ln.strip()), "")
            except Exception:
                first_non_empty = ""
            if first_non_empty:
                delimiter_pattern = r"^\s*(//|#|/\*|;|REM\b).*\.\.\.\s*existing\s+code\s*\.\.\."
                if re.search(delimiter_pattern, first_non_empty, re.IGNORECASE):
                    raise ValueError(
                        f"Cannot apply delimiter-based patch to a new file '{abs_path}' because there is no original content to anchor. "
                        "For new files, provide the full file content without delimiters, or start with a code segment (no leading delimiter)."
                    )

            try:
                new_content_lines = utils.apply_code_edit([], code_edit)
            except ValueError as apply_ve:
                DB["last_edit_params"] = params_for_reapply
                _log_init_message(logging.WARNING, f"File creation failed for '{abs_path}' (ValueError): {apply_ve}. Last edit params stored for reapply.")
                raise ValueError(f"Failed to create new file '{abs_path}': {str(apply_ve)}") from apply_ve

            new_size = utils.calculate_size_bytes(new_content_lines)
            new_timestamp = utils.get_current_timestamp_iso()
            file_system[abs_path] = {
                "path": abs_path,
                "is_directory": False,
                "content_lines": new_content_lines,
                "size_bytes": new_size,
                "last_modified": new_timestamp,
            }
            operation_message = f"File '{abs_path}' created successfully."
        else:
            # --- Edit Existing File ---
            original_lines = existing_entry.get("content_lines", [])
            try:
                new_content_lines = utils.apply_code_edit(original_lines, code_edit)
            except ValueError as apply_ve:
                DB["last_edit_params"] = params_for_reapply
                _log_init_message(logging.WARNING, f"edit failed for existing file '{abs_path}': {apply_ve}. Last edit params stored for reapply.")
                raise ValueError(f"Failed to apply edit to existing file '{abs_path}': {str(apply_ve)}") from apply_ve

            new_size = utils.calculate_size_bytes(new_content_lines)
            new_timestamp = utils.get_current_timestamp_iso()
            existing_entry["content_lines"] = new_content_lines
            existing_entry["size_bytes"] = new_size
            existing_entry["last_modified"] = new_timestamp
            existing_entry["path"] = abs_path
            operation_message = f"File '{abs_path}' updated successfully."

        # --- Immediately reflect DB change into active sandbox (if any) ---
        try:
            sync_result = utils.sync_db_file_to_sandbox(abs_path, create_parents=True)
            if not sync_result.get("success"):
                _log_init_message(logging.INFO, f"Sandbox sync skipped or failed for '{abs_path}': {sync_result.get('message')}")
            else:
                _log_init_message(logging.INFO, f"Sandbox updated for '{abs_path}': {sync_result.get('sandbox_path')}")
        except Exception as e_sync:
            _log_init_message(logging.WARNING, f"Non-fatal: failed to sync DB edit to sandbox for '{abs_path}': {type(e_sync).__name__} - {e_sync}")

        # Update record of the last edit
        DB["last_edit_params"] = {
            "target_file": abs_path,
            "code_edit": code_edit,
            "instructions": instructions,
            "explanation": f"Applied edit for '{basename_for_explanation}' successfully.",
        }
        return {"success": True, "message": operation_message, "file_path": abs_path}

    except (ValueError, IsADirectoryError, FileNotFoundError, InvalidInputError) as e:
        raise e
    except Exception as e:
        print_log(f"Warning: Unexpected internal error during edit_file for '{target_file}': {type(e).__name__} - {e}")
        raise RuntimeError(f"An unexpected internal error occurred: {str(e)}") from e


@with_common_file_system
@tool_spec(
    spec={
        'name': 'read_file',
        'description': """ Read the contents of a file from the application's managed file system.
        
        This function reads a specified range of lines from a file within the workspace and provides the summary of the
        file content outside of that specified range of lines. It can read a specific range of lines or the entire file based on the
        should_read_entire_file parameter. The function handles path resolution, validates the file exists, and ensures the
        requested line range is valid. If the requested `start_line_one_indexed` is out of bounds (greater than the total
        number of lines), the function will instead read up to the last 250 lines of the file.
        
        Guidelines for use:
            - You can view up to 250 lines at a time.
            - After each read, check if you have enough context to proceed with your task.
            - Note any lines that were not shown, and if you suspect important information is outside the viewed range,
              read those lines as well.
            - When unsure, read additional lines to ensure you have the complete context.
            - Avoid reading the entire file unless absolutely necessary as this can be slow and inefficient for large files. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'target_file': {
                    'type': 'string',
                    'description': """ The path of the file to read. Can be relative to the workspace root or absolute.
                    If absolute, it will be used as is. If relative, it will be joined with workspace root. """
                },
                'start_line_one_indexed': {
                    'type': 'integer',
                    'description': """ The one-indexed line number to start reading from (inclusive).
                    Must be >= 1 and <= end_line_one_indexed_inclusive. Defaults to 1. """
                },
                'end_line_one_indexed_inclusive': {
                    'type': 'integer',
                    'description': """ The one-indexed line number to end reading at (inclusive).
                    Must be >= start_line_one_indexed and <= total lines in file. Defaults to 250. """
                },
                'should_read_entire_file': {
                    'type': 'boolean',
                    'description': """ Whether to read the entire file. If True,
                    start_line_one_indexed and end_line_one_indexed_inclusive are ignored. """
                },
                'explanation': {
                    'type': 'string',
                    'description': """ A description of why this operation is being performed.
                    Not used in the return value but may be utilized for logging or auditing.
                    Defaults to None. """
                }
            },
            'required': [
                'target_file'
            ]
        }
    }
)
def read_file(
    target_file: str,
    start_line_one_indexed: int = 1,
    end_line_one_indexed_inclusive: int = 250,
    should_read_entire_file: bool = False,
    explanation: Optional[str] = None,
) -> Dict[str, Any]:
    """Read the contents of a file from the application's managed file system.

    This function reads a specified range of lines from a file within the workspace and provides the summary of the
    file content outside of that specified range of lines. It can read a specific range of lines or the entire file based on the
    should_read_entire_file parameter. The function handles path resolution, validates the file exists, and ensures the
    requested line range is valid. If the requested `start_line_one_indexed` is out of bounds (greater than the total
    number of lines), the function will instead read up to the last 250 lines of the file.

    Guidelines for use:
        - You can view up to 250 lines at a time.
        - After each read, check if you have enough context to proceed with your task.
        - Note any lines that were not shown, and if you suspect important information is outside the viewed range,
          read those lines as well.
        - When unsure, read additional lines to ensure you have the complete context.
        - Avoid reading the entire file unless absolutely necessary as this can be slow and inefficient for large files.

    Args:
        target_file (str): The path of the file to read. Can be relative to the workspace root or absolute.
            If absolute, it will be used as is. If relative, it will be joined with workspace root.
        start_line_one_indexed (int): The one-indexed line number to start reading from (inclusive).
            Must be >= 1 and <= end_line_one_indexed_inclusive. Defaults to 1.
        end_line_one_indexed_inclusive (int): The one-indexed line number to end reading at (inclusive).
            Must be >= start_line_one_indexed and <= total lines in file. Defaults to 250.
        should_read_entire_file (bool): Whether to read the entire file. If True,
            start_line_one_indexed and end_line_one_indexed_inclusive are ignored.
        explanation (Optional[str]): A description of why this operation is being performed.
            Not used in the return value but may be utilized for logging or auditing.
            Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the read-file was successful.
            - start_line (int): The line number of the start line.
            - end_line (int): The line number of the last line returned in 'content'. This may be different from the requested end line if the range was adjusted.
            - content (List[str]): The requested lines from the file, up to a maximum of 250 lines. If the requested range exceeds 250 lines, only the first 250 lines of the range will be returned.
            - total_lines (int): The total number of lines in the file.
            - path_processed (str): The absolute path that was processed.
            - summary_of_truncated_content (Optional[str]): A descriptive summary of the content before the returned 'start_line' and after the returned 'end_line' (which may be less than the requested end line if truncation occurred).
            - message (str): A descriptive message detailing the outcome of the read operation. It will specify if the requested range was adjusted due to file size, being out of bounds, or exceeding the line limit. This field will always be populated.

    Raises:
        ValueError:
            - If the workspace root is not configured in the application settings.
            - If the resolved file path is outside the permitted workspace boundaries.
            - If the start line is greater than the end line.
            - If the start line is less than 1.
            - If the start or end line exceeds the total number of lines in the file (when not reading the entire file).
        InvalidInputError: If the target file path is empty or invalid.
        FileNotFoundError: If the target file does not exist.
        IsADirectoryError: If the target path is a directory.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError("Workspace root is not configured in the application settings.")

    normalized_workspace_root = os.path.normpath(workspace_root)

    if not target_file:
        raise InvalidInputError("Target file path cannot be empty.")

    # Check if the path is absolute
    if os.path.isabs(target_file):
        abs_target_path = os.path.normpath(target_file)
    else:
        # Handle relative path
        path_segment = target_file.lstrip("/")
        if not path_segment:
             raise InvalidInputError(f"Target path '{target_file}' is not a valid file path.")
        abs_target_path = os.path.normpath(
            os.path.join(normalized_workspace_root, path_segment)
        )

    # Verify the resolved path is within the workspace boundaries
    if not abs_target_path.startswith(normalized_workspace_root) and abs_target_path != normalized_workspace_root:
        raise ValueError(
            f"Path '{target_file}' resolves to '{abs_target_path}', "
            f"which is outside the permitted workspace '{normalized_workspace_root}'."
        )

    if start_line_one_indexed > end_line_one_indexed_inclusive:
        raise ValueError(f"Start line {start_line_one_indexed} cannot be greater than end line {end_line_one_indexed_inclusive}.")

    if start_line_one_indexed < 1:
        raise ValueError(f"Start line {start_line_one_indexed} must be 1 or greater.")

    file_system = DB.get("file_system", {})
    file_entry = file_system.get(abs_target_path)

    if not file_entry:
        raise FileNotFoundError(f"File not found at path: {abs_target_path}")

    if file_entry.get("is_directory", False):
        raise IsADirectoryError(f"Target path is a directory, not a file: {abs_target_path}")

    content_lines = file_entry.get("content_lines", [])
    total_lines = len(content_lines)

    original_start_line = start_line_one_indexed
    original_end_line = end_line_one_indexed_inclusive

    # --- Explicit type checks for robustness ---
    if not isinstance(target_file, str):
        raise TypeError("target_file must be a string.")
    if not isinstance(start_line_one_indexed, int):
        raise TypeError("start_line_one_indexed must be an integer.")
    if not isinstance(end_line_one_indexed_inclusive, int):
        raise TypeError("end_line_one_indexed_inclusive must be an integer.")
    if not isinstance(should_read_entire_file, bool):
        raise TypeError("should_read_entire_file must be a boolean.")

    # Special-case: empty file handling to avoid returning start_line=1 and end_line=0
    if total_lines == 0:
        empty_msg = f"File '{os.path.basename(abs_target_path)}' is empty. No content to read."
        return {
            "success": True,
            "start_line": 1,
            "end_line": 1,
            "content": [],
            "total_lines": 0,
            "path_processed": abs_target_path,
            "summary_of_truncated_content": None,
            "message": empty_msg,
        }

    if should_read_entire_file:
        message = f"Successfully read all {total_lines} lines from the file '{os.path.basename(abs_target_path)}'."
        return {
            "success": True,
            "start_line": 1,
            "end_line": total_lines,
            "content": content_lines,
            "total_lines": total_lines,
            "path_processed": abs_target_path,
            "summary_of_truncated_content": None,
            "message": message,
        }

    # --- Handle out-of-bounds and adjust line numbers ---
    start_line_was_out_of_bounds = start_line_one_indexed > total_lines
    if start_line_was_out_of_bounds:
        # If start line is out of bounds, read the last chunk of the file (up to 250 lines).
        chunk_size = 250
        start_line_one_indexed = max(1, total_lines - chunk_size + 1)
        end_line_one_indexed_inclusive = total_lines
    else:
        # Otherwise, just cap the end line to the total number of lines.
        end_line_one_indexed_inclusive = min(end_line_one_indexed_inclusive, total_lines)

    # Convert to 0-based indexing for list slicing
    start_idx = start_line_one_indexed - 1
    end_idx = end_line_one_indexed_inclusive
    chunk_size = 250

    content_subset = content_lines[start_idx:end_idx]
    truncated_content = content_subset[:chunk_size]
    returned_end_line = start_line_one_indexed + len(truncated_content) - 1

    # --- Generate summary for truncated parts of the file ---
    offset = 0
    truncated_content_before = add_line_numbers(content_lines[:start_idx])
    if len(content_subset) > chunk_size:
        offset = len(content_subset) - chunk_size
    truncated_content_after = add_line_numbers(content_lines[end_idx - offset:], start=end_idx - offset + 1)
    summary_content = truncated_content_before + truncated_content_after

    # Format the summary content as contiguous text rather than a Python list literal
    summary_text = "".join(summary_content) if summary_content else ""
    prompt_template = (
        f'I will provide you with a list of code lines, each with line numbers. Please read the code and '
        f'write a brief summary in plain English explaining what the code does, highlighting any '
        f'important details. Group your summary by logical blocks of code, such as functions, and '
        f'specify the line numbers for each block (e.g., "Lines 1–30: ...", "Function from '
        f'lines 31–70: ..."). Make your summary easy to understand for someone with basic programming '
        f'knowledge. Do not include the code itself in your response. '
        f'Here is the code below:\n{summary_text}')

    summary = call_llm(prompt_template)

    # --- Construct the final message ---
    message = ""
    if start_line_was_out_of_bounds:
        message = (
            f"Requested to read lines {original_start_line}-{original_end_line}, but the file only has {total_lines} lines. "
            f"The start line was out of bounds, so returning the last {len(truncated_content)} lines of the file: "
            f"{start_line_one_indexed}-{returned_end_line}."
        )
    else:
        is_end_capped = original_end_line > returned_end_line
        is_truncated = len(content_subset) > chunk_size

        if is_truncated:
            message = (
                f"Requested to read lines {original_start_line}-{original_end_line}, but the request exceeded the {chunk_size}-line limit. "
                f"Returning the first {chunk_size} lines of the requested range: {start_line_one_indexed}-{returned_end_line}."
            )
        elif is_end_capped:
            message = (
                f"Requested to read lines {original_start_line}-{original_end_line}, but the file only has {total_lines} lines. "
                f"Returning lines {start_line_one_indexed}-{returned_end_line}."
            )
        else:
            message = f"Successfully read lines {start_line_one_indexed}-{returned_end_line} from the file."

    return {
        "success": True,
        "start_line": start_line_one_indexed,
        "end_line": returned_end_line,
        "content": truncated_content,
        "total_lines": len(content_lines),
        "path_processed": abs_target_path,
        "summary_of_truncated_content": summary,
        "message": message,
    }


@with_common_file_system
@tool_spec(
    spec={
        'name': 'run_terminal_cmd',
        'description': """ Executes the provided terminal command in the current workspace context.
        
        Use this function to run shell commands. You need to provide the exact
        command string to be executed. Note that commands like 'cd', 'pwd', and
        environment commands ('export', 'unset', 'env') are handled internally;
        other commands are executed externally and may modify the workspace files.
        
        IMPORTANT: For any command that expects user interaction or uses a pager
        (like git diff, git log, less, more, etc.), you MUST append
        ' | cat' to the command string yourself before passing it to this function.
        Failure to do so will cause the command to hang or fail.
        
        For commands that are intended to run for a long time or indefinitely
        (e.g., starting a server, running a watch process), set the
        `is_background` parameter to True. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': """ The exact terminal command string to execute. Remember
                    to append ' | cat' for interactive/pager commands. """
                },
                'explanation': {
                    'type': 'string',
                    'description': """ A brief justification for running this command, which
                    may be shown to the user or used for logging. """
                },
                'is_background': {
                    'type': 'boolean',
                    'description': """ Set to True to run the command as a
                    background process (e.g., for servers or watchers). Defaults to False,
                    running the command in the foreground and waiting for completion. """
                }
            },
            'required': [
                'command'
            ]
        }
    }
)
def run_terminal_cmd(command: str, explanation: Optional[str] = None, is_background: bool = False) -> Dict[str, Any]:
    """Executes the provided terminal command in the current workspace context.

    Use this function to run shell commands. You need to provide the exact
    command string to be executed. Note that commands like 'cd', 'pwd', and
    environment commands ('export', 'unset', 'env') are handled internally;
    other commands are executed externally and may modify the workspace files.
    
    Note: Workspace validation is applied selectively - internal commands like 'cd' and 'pwd'
    require full workspace hydration since they navigate the file system. External commands
    can be used to initialize workspace content and don't require hydration.

    IMPORTANT: For any command that expects user interaction or uses a pager
    (like git diff, git log, less, more, etc.), you MUST append
    ' | cat' to the command string yourself before passing it to this function.
    Failure to do so will cause the command to hang or fail.

    For commands that are intended to run for a long time or indefinitely
    (e.g., starting a server, running a watch process), set the
    `is_background` parameter to True.

    Args:
        command (str): The exact terminal command string to execute. Remember
                       to append ' | cat' for interactive/pager commands.
        explanation (Optional[str]): A brief justification for running this command, which
                           may be shown to the user or used for logging.
        is_background (bool): Set to True to run the command as a
            background process (e.g., for servers or watchers). Defaults to False,
            running the command in the foreground and waiting for completion.

    Returns:
        Dict[str, Any]: A dictionary describing the outcome:
            - success (bool): Indicates if the command launched successfully
                                (background) or completed with exit code 0
                                (foreground).
            - message (str): A status message about the execution.
            - stdout (str): Captured standard output (foreground only).
            - stderr (str): Captured standard error (foreground only).
            - returncode (Optional[int]): The command's exit code
                                           (foreground only).
            - pid (Optional[int]): The process ID if run in the background.

    Raises:
        ValueError: If workspace_root is not configured or the command string is empty/invalid.
        CommandExecutionError: If a command fails to launch, `cd` fails, or a foreground command returns a non-zero exit code. The exception message will include the raw stdout and stderr.
    """
    # Enforce strict boolean for is_background
    if not isinstance(is_background, bool):
        raise ValueError(f"is_background must be a boolean, got {type(is_background).__name__}")

    # Use global DB state and session variables
    global DB, utils, SESSION_SANDBOX_DIR, SESSION_INITIALIZED, _SANDBOX_TEMP_DIR_OBJ
    
    result_dict: Dict[str, Any] = {
        'success': False, 'message': "Initialization error.",
        'stdout': "", 'stderr': "", 'returncode': None, 'pid': None
    }

    # --- Get current workspace root and CWD ---
    current_workspace_root = DB.get("workspace_root")
    if not current_workspace_root:
        result_dict['message'] = "Operation failed: workspace_root is not configured."
        _log_init_message(logging.ERROR, result_dict['message'])
        raise ValueError(result_dict['message'])

    # --- Initialize Persistent Sandbox on First Run ---
    # Use shared session manager to coordinate sandbox across all terminal-like APIs
    shared_session_info = session_manager.get_shared_session_info()
    
    if not shared_session_info["initialized"] or not shared_session_info["exists"]:
        try:
            _log_init_message(logging.INFO, "Initializing shared sandbox session via session_manager...")
            SESSION_SANDBOX_DIR = session_manager.initialize_shared_session(
                api_name="cursor",
                workspace_root=current_workspace_root,
                db_instance=DB,
                dehydrate_func=utils.dehydrate_db_to_directory
            )
            SESSION_INITIALIZED = True
            _log_init_message(logging.INFO, f"Shared sandbox initialized at: {SESSION_SANDBOX_DIR}")
        except Exception as e:
            _log_init_message(logging.ERROR, f"Failed to initialize shared sandbox: {e}", exc_info=True)
            raise CommandExecutionError(f"Failed to set up the execution environment: {e}")
    else:
        # Reuse existing shared sandbox created by another API
        SESSION_SANDBOX_DIR = shared_session_info["sandbox_dir"]
        SESSION_INITIALIZED = True
        _log_init_message(
            logging.INFO, 
            f"Reusing existing sandbox from '{shared_session_info['active_api']}': {SESSION_SANDBOX_DIR}"
        )
    # -------------------------------------------------
    
    # Normalize paths for internal use
    current_workspace_root_norm = utils._normalize_path_for_db(current_workspace_root)
    current_cwd_norm = utils._normalize_path_for_db(DB.get("cwd", current_workspace_root_norm))

    # --- Handle internal commands ---
    stripped_command = command.strip()

    # Handle environment variable commands
    if stripped_command in ('env',) or stripped_command.startswith(('export ', 'unset ')):
        return handle_env_command(stripped_command, DB)

    # --- Prepare for external command execution ---
    if not SESSION_SANDBOX_DIR:
        raise CommandExecutionError("Session sandbox is not initialized. Cannot execute external commands.")

    process_executed_without_launch_error = False
    command_message = ""

    # Preserve current workspace state before potential modifications
    original_filesystem_state = DB.get("file_system", {}).copy()
    # current_workspace_root_norm and current_cwd_norm are already captured

    try:
        exec_env_root = SESSION_SANDBOX_DIR
        _log_init_message(logging.INFO, f"Using persistent sandbox for execution: {exec_env_root}")
        exec_env_root_real = _realpath_or_original(exec_env_root)
        
        # --- DEBUGGING START ---
        # print(f"DEBUG: Preparing to execute command: '{command}'")
        # print(f"DEBUG: Logical CWD for PWD env var: {current_cwd_norm}")
        # print("DEBUG: Listing physical sandbox content before command execution:")
        # os.system(f"ls -lR {exec_env_root}")
        # --- DEBUGGING END ---
        
        # Sync any new files from DB to sandbox before command execution
        # This handles cases where tests add files directly to DB
        for db_path, db_entry in DB.get("file_system", {}).items():
            if db_path.startswith(current_workspace_root_norm):
                rel_path = os.path.relpath(db_path, current_workspace_root_norm) if db_path != current_workspace_root_norm else '.'
                sandbox_path = os.path.join(exec_env_root, rel_path)
                
                # If file exists in DB but not in sandbox, create it
                if not os.path.exists(sandbox_path):
                    try:
                        if db_entry.get("is_directory"):
                            os.makedirs(sandbox_path, exist_ok=True)
                            if "metadata" in db_entry:
                                utils._apply_file_metadata(sandbox_path, db_entry["metadata"], strict_mode=False)
                        else:
                            # Create parent directory if needed
                            parent_dir = os.path.dirname(sandbox_path)
                            if parent_dir and not os.path.exists(parent_dir):
                                os.makedirs(parent_dir, exist_ok=True)
                            
                            # Write file content
                            content_lines = db_entry.get("content_lines", [])
                            with open(sandbox_path, 'w', encoding='utf-8') as f:
                                f.writelines(content_lines)
                            
                            # Apply metadata if available
                            if "metadata" in db_entry:
                                utils._apply_file_metadata(sandbox_path, db_entry["metadata"], strict_mode=False)
                    except Exception as e:
                        _log_shell_message(logging.WARNING, f"Failed to sync {db_path} to sandbox: {e}")
        
        pre_command_state_temp = utils.collect_pre_command_metadata_state(
            DB.get("file_system", {}),
            exec_env_root,
            current_workspace_root_norm
        )

        # Determine the correct CWD within the execution environment
        if current_cwd_norm.startswith(current_workspace_root_norm):
            relative_cwd = os.path.relpath(current_cwd_norm, current_workspace_root_norm)
        else:
            # Fallback if CWD was somehow outside root
            _log_init_message(logging.WARNING, f"Current directory '{current_cwd_norm}' is outside workspace root '{current_workspace_root_norm}'. Using environment root for command.")
            relative_cwd = "."

        # Construct the path for the subprocess CWD
        subprocess_cwd_physical = utils._normalize_path_for_db(os.path.join(exec_env_root, relative_cwd))
        subprocess_cwd_real = _realpath_or_original(subprocess_cwd_physical)

        # Verify the execution CWD exists
        if not os.path.isdir(subprocess_cwd_real):
            _log_init_message(logging.WARNING, f"Execution environment CWD '{subprocess_cwd_physical}' does not exist. Creating directory structure.")
            # Create the missing directory structure
            try:
                os.makedirs(subprocess_cwd_physical, exist_ok=True)
                _log_init_message(logging.INFO, f"Created missing directory: {subprocess_cwd_physical}")
            except Exception as e:
                _log_init_message(logging.ERROR, f"Failed to create directory '{subprocess_cwd_physical}': {e}")
                # Fall back to using the temp directory root
                subprocess_cwd_physical = exec_env_root
                subprocess_cwd_real = _realpath_or_original(subprocess_cwd_physical)
                if not os.path.isdir(subprocess_cwd_real):
                    _log_init_message(logging.ERROR, f"Even temp directory root '{exec_env_root}' does not exist!")
                    raise CommandExecutionError(f"Execution environment setup failed: temp directory '{exec_env_root}' does not exist")

        # Create any missing parent directories for output redirection
        try:
            redir_target = utils._extract_last_unquoted_redirection_target(command.strip())
        except Exception:
            redir_target = None
        if redir_target:
            output_file = redir_target
            # Convert relative path to absolute
            if not os.path.isabs(output_file):
                output_file = os.path.join(subprocess_cwd_physical, output_file)
            # Create parent directory if needed
            parent_dir = os.path.dirname(output_file)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    _log_init_message(logging.INFO, f"Created parent directory for output redirection: {parent_dir}")
                except Exception as e:
                    _log_init_message(logging.ERROR, f"Failed to create parent directory '{parent_dir}': {e}")
                    raise CommandExecutionError(f"Failed to create parent directory for output redirection: {e}")

        _log_init_message(logging.INFO, f"Executing command '{command}' in CWD '{subprocess_cwd_physical}' (Background: {is_background})")

        # Prepare environment and expand variables
        cmd_env = prepare_command_environment(DB, subprocess_cwd_physical, current_cwd_norm)

        # Don't expand variables in the command string, let bash handle it
        expanded_command = command.strip()
        
        # For foreground commands, append a command to get the CWD after execution.
        if not is_background:
            # Using a newline is safer than a semicolon for chaining.
            # Use a unique marker to easily find the path in output.
            pwd_marker = "CURS_PWD_MARKER_V1"
            # Use 'set -e' to exit on first error, and capture exit code of main command
            expanded_command = (
                f"set -e\n"
                f"main_exit_code=0\n"
                f"{command.strip()} || main_exit_code=$?\n"
                f"set +e\n"
                f"echo \"{pwd_marker}:$(pwd)\"\n"
                f"exit $main_exit_code"
            )
        
        # Check for and fix tar commands that create archives in the same directory
        expanded_command = utils.detect_and_fix_tar_command(expanded_command, subprocess_cwd_physical)

        if not expanded_command:
            result_dict['message'] = "Operation failed: Command string is empty."
            _log_init_message(logging.ERROR, result_dict['message'])
            raise ValueError(result_dict['message'])

        # --- Execute the command ---
        process_obj: Union[subprocess.Popen, subprocess.CompletedProcess, None] = None
        if is_background:
            try:
                # Launch background process with environment
                with open(os.devnull, 'wb') as devnull:
                    process_obj = subprocess.Popen(
                        ['/bin/bash', '-c', expanded_command],
                        cwd=subprocess_cwd_physical,
                        stdout=devnull,
                        stderr=devnull,
                        env=cmd_env
                    )
                process_executed_without_launch_error = True
                result_dict['pid'] = process_obj.pid
                result_dict['returncode'] = None
                command_message = f"Command '{command}' launched successfully in background (PID: {process_obj.pid})."
            except FileNotFoundError:
                command_message = f"Launch failed: Command not found."
                _log_init_message(logging.ERROR, command_message)
                result_dict['message'] = command_message; result_dict['returncode'] = 127
                raise CommandExecutionError(result_dict['message'])
            except Exception as e:
                command_message = f"Launch failed for background process '{command}': {type(e).__name__} - {e}"
                _log_init_message(logging.ERROR, command_message, exc_info=True)
                result_dict['message'] = command_message; result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])
        else: # Foreground execution
            try:
                # Run foreground process with environment, inheriting parent Conda environment if present

                # If running inside a Conda environment, propagate CONDA-related variables from parent
                conda_env_vars = ['CONDA_PREFIX', 'CONDA_DEFAULT_ENV', 'CONDA_EXE', 'CONDA_PYTHON_EXE', 'CONDA_SHLVL', 'CONDA_PROMPT_MODIFIER']
                for var in conda_env_vars:
                    if var in os.environ:
                        cmd_env[var] = os.environ[var]

                # Also propagate PATH if in Conda, to ensure correct binaries
                if 'CONDA_PREFIX' in os.environ and 'PATH' in os.environ:
                    cmd_env['PATH'] = os.environ['PATH']

                process_obj = subprocess.run(
                    ['/bin/bash', '-c', expanded_command],
                    cwd=subprocess_cwd_physical,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False,
                    env=cmd_env
                )
                process_executed_without_launch_error = True
                command_message = f"Command completed with exit code {process_obj.returncode}."

                # --- Post-command CWD update ---
                stdout_lines = process_obj.stdout.splitlines()
                new_physical_cwd = None
                pwd_marker = "CURS_PWD_MARKER_V1"

                # Check if the last line is our marker
                if stdout_lines and stdout_lines[-1].startswith(f"{pwd_marker}:"):
                    new_physical_cwd = stdout_lines[-1][len(pwd_marker)+1:]
                    del stdout_lines[-1] # Remove marker line
                
                # Reconstruct stdout
                if not stdout_lines:
                    cleaned_stdout = ""
                else:
                    cleaned_stdout = '\n'.join(stdout_lines)
                    # Heuristic to preserve trailing newline
                    if process_obj.stdout.count('\n') > len(stdout_lines):
                         cleaned_stdout += '\n'
                
                # For pwd command, map physical sandbox path back to logical workspace path in output
                stdout_stripped = cleaned_stdout.strip()
                if stripped_command.strip() == 'pwd' and stdout_stripped:
                    stdout_real = _realpath_or_original(stdout_stripped)
                    if _is_within_directory(stdout_real, exec_env_root_real):
                        relative_path = os.path.relpath(stdout_real, exec_env_root_real)
                        if relative_path == '.':
                            logical_cwd = current_workspace_root_norm
                        else:
                            logical_cwd = os.path.join(current_workspace_root_norm, relative_path)
                        cleaned_stdout = logical_cwd + '\n' if cleaned_stdout.endswith('\n') else logical_cwd
                
                result_dict['stdout'] = cleaned_stdout

                if new_physical_cwd and os.path.isdir(new_physical_cwd):
                    # Convert physical sandbox path back to logical workspace path
                    new_physical_cwd_real = _realpath_or_original(new_physical_cwd)
                    if os.path.isdir(new_physical_cwd_real) and _is_within_directory(new_physical_cwd_real, exec_env_root_real):
                        relative_new_cwd = os.path.relpath(new_physical_cwd_real, exec_env_root_real)
                        
                        if relative_new_cwd == '.':
                            logical_new_cwd = current_workspace_root_norm
                        else:
                            logical_new_cwd = os.path.join(current_workspace_root_norm, relative_new_cwd)
                        
                        normalized_logical_cwd = utils._normalize_path_for_db(logical_new_cwd)
                        if DB.get("cwd") != normalized_logical_cwd:
                           DB["cwd"] = normalized_logical_cwd
                           _log_init_message(logging.INFO, f"run_terminal_cmd updated CWD to: {normalized_logical_cwd}")
                    else:
                        _log_init_message(logging.WARNING, f"Could not map new CWD '{new_physical_cwd}' back to workspace root.")
                # --- End CWD update ---

                result_dict['stderr'] = process_obj.stderr
                result_dict['returncode'] = process_obj.returncode
                if process_obj.returncode != 0:
                    if utils.common_utils.should_treat_nonzero_as_success(command, process_obj.returncode):
                        _log_init_message(logging.INFO, f"Non-zero exit code {process_obj.returncode} treated as success for command '{command}'.")
                    else:
                        # On failure, restore state and raise with full stdout/stderr so callers have full error context
                        # Restore state and raise with full stdout/stderr so callers have full error context
                        _log_init_message(logging.WARNING, f"Command '{command}' failed with exit code {process_obj.returncode}. Restoring pre-execution workspace state.")
                        DB["workspace_root"] = current_workspace_root_norm
                        DB["cwd"] = current_cwd_norm
                        DB["file_system"] = original_filesystem_state
                        stderr_text = process_obj.stderr or ""
                        stdout_text = process_obj.stdout or ""
                                            # Check if this is a cd command and provide a more specific error message
                        if stripped_command.startswith('cd ') or stripped_command == 'cd':
                            detailed_message = f"Failed to change directory: {stripped_command}\nError: {stderr_text}"
                        else:
                            detailed_message = (
                                f"Command failed with exit code {process_obj.returncode}.\n"
                                f"--- STDOUT ---\n{stdout_text}\n"
                                f"--- STDERR ---\n{stderr_text}"
                            )
                        result_dict['message'] = detailed_message
                        raise CommandExecutionError(detailed_message)
                else:
                    pass  # Command succeeded, continue to state update
            except FileNotFoundError:
                command_message = f"Execution failed: Command not found."
                _log_init_message(logging.ERROR, command_message)
                result_dict['message'] = command_message; result_dict['returncode'] = 127
                raise CommandExecutionError(result_dict['message'])
            except CommandExecutionError as ce:
                # Re-raise without wrapping so detailed stdout/stderr is preserved in the message
                raise ce
            except Exception as e:
                command_message = f"Execution failed for foreground process '{command}': {type(e).__name__} - {e}"
                _log_init_message(logging.ERROR, command_message, exc_info=True)
                result_dict['message'] = command_message
                if result_dict.get('returncode') is None: result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])

        # --- Post-execution state update ---
        if process_executed_without_launch_error:
            _log_init_message(logging.INFO, f"Command '{command}' execution finished. Updating workspace state.")
            try:
                post_command_state_temp = utils.collect_post_command_metadata_state(
                    DB.get("file_system", {}),
                    exec_env_root,
                    current_workspace_root_norm
                )
                
                # Update the main workspace state from the execution environment
                utils.update_db_file_system_from_temp(
                    exec_env_root,
                    original_filesystem_state,
                    current_workspace_root_norm,
                    command=command
                )

                # Preserve original change_time for files that didn't actually change during command execution
                utils.preserve_unchanged_change_times(
                    DB.get("file_system", {}),
                    pre_command_state_temp,
                    post_command_state_temp,
                    original_filesystem_state,
                    current_workspace_root_norm,
                    exec_env_root
                )
            except MetadataError as me:
                # Handle metadata operation failures in strict mode
                result_dict['message'] = f"Command failed: {str(me)}"
                result_dict['returncode'] = 1
                raise CommandExecutionError(result_dict['message'])

            # Determine final success status
            if is_background:
                if result_dict['pid'] is not None:
                    result_dict['success'] = True
                    result_dict['message'] = command_message + " Workspace state updated."
            else:
                if result_dict['returncode'] is not None and isinstance(process_obj, subprocess.CompletedProcess):
                    # Success if zero exit or policy allows this non-zero code
                    if process_obj.returncode == 0:
                        result_dict['success'] = True
                    else:
                        result_dict['success'] = utils.common_utils.should_treat_nonzero_as_success(command, process_obj.returncode)
                    result_dict['message'] = command_message + " Workspace state updated."
                    if process_obj.returncode != 0 and not utils.common_utils.should_treat_nonzero_as_success(command, process_obj.returncode):
                        result_dict['message'] += f" (Note: Non-zero exit code {process_obj.returncode})."
        else:
            # Command failed to launch; restore pre-execution state
            _log_init_message(logging.WARNING, f"Command '{command}' failed to launch. Restoring pre-execution workspace state.")
            DB["workspace_root"] = current_workspace_root_norm
            DB["cwd"] = current_cwd_norm
            DB["file_system"] = original_filesystem_state
            result_dict['success'] = False

    except PermissionError as e:
        # Errors related to execution environment setup/cleanup
        _log_init_message(logging.ERROR, f"Execution environment error: {type(e).__name__} - {e}", exc_info=True)
        additional_msg = f" Error managing execution environment ({type(e).__name__})."
        result_dict['message'] = (result_dict.get('message') or f"Operation failed (environment error: {type(e).__name__})") + additional_msg
        if result_dict.get('returncode') is None: result_dict['returncode'] = 1
        raise CommandExecutionError(result_dict['message'])
    except CommandExecutionError as ce:
        # Preserve detailed command outputs without re-wrapping
        raise ce
    except Exception as e:
         # Catch-all for other unexpected errors
        _log_init_message(logging.ERROR, f"Unexpected error during command execution phase for '{command}': {type(e).__name__} - {e}", exc_info=True)
        result_dict['message'] = f"Operation failed unexpectedly: {type(e).__name__} - {e}"
        if result_dict.get('returncode') is None: result_dict['returncode'] = 1

        # Attempt emergency state restoration
        _log_init_message(logging.INFO, "Attempting emergency restoration of workspace state.")
        DB["workspace_root"] = current_workspace_root_norm
        DB["cwd"] = current_cwd_norm
        DB["file_system"] = original_filesystem_state
        raise CommandExecutionError(result_dict['message'])
    finally:
        # Cleanup is now handled by end_session(), so we no longer clean up the temp dir here.
        _log_init_message(logging.DEBUG, "Command execution block finished. Sandbox cleanup is deferred to end_session().")

        _log_init_message(logging.DEBUG, f"run_terminal_cmd finished. Final CWD='{DB.get('cwd')}'")

    # Consistency check
    if result_dict.get('pid') is not None and result_dict.get('returncode') is not None:
        _log_init_message(logging.WARNING, "Result indicates both background (pid) and foreground (returncode) execution.")

    # Add 'success' field for backward compatibility
    # Success is determined by returncode == 0, or allowed non-zero by policy, for foreground commands
    if result_dict.get('returncode') is not None:
        rc = result_dict['returncode']
        result_dict['success'] = (rc == 0) or utils.common_utils.should_treat_nonzero_as_success(command, rc)
    elif result_dict.get('pid') is not None:
        # For background processes, consider them successful if they launched
        result_dict['success'] = True
    else:
        # Default to False if we can't determine success
        result_dict['success'] = False

    return result_dict


@tool_spec(
    spec={
        'name': 'fetch_pull_request',
        'description': """ Looks up a pull request by number or a commit by commit hash and returns the diff.
        
        This function integrates with the git repository to fetch real diffs and commit information.
        It can resolve PR numbers by finding commits that reference them in commit messages, or 
        directly show commit diffs. The function returns comprehensive information including the
        formatted diff, author details, and file changes.
        
        Pull requests and commit hashes related to files can be found via the
        'read_file' and 'codebase_search' tools. You should generally use this
        tool following a 'codebase_search' toolcall rather than making a new
        'codebase_search' or 'read_file' tool call. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'pullNumberOrCommitHash': {
                    'type': 'string',
                    'description': """ The pull request number (without '#' prefix) or 
                    commit hash (full or abbreviated). For PR numbers, the function searches 
                    for commits referencing that PR in their messages. """
                }
            },
            'required': [
                'pullNumberOrCommitHash'
            ]
        }
    }
)
def fetch_pull_request(
    pullNumberOrCommitHash: str
) -> Dict[str, Any]:
    """Looks up a pull request by number or a commit by commit hash and returns the diff.

    This function integrates with the git repository to fetch real diffs and commit information.
    It can resolve PR numbers by finding commits that reference them in commit messages, or 
    directly show commit diffs. The function returns comprehensive information including the
    formatted diff, author details, and file changes.

    Pull requests and commit hashes related to files can be found via the
    'read_file' and 'codebase_search' tools. You should generally use this
    tool following a 'codebase_search' toolcall rather than making a new
    'codebase_search' or 'read_file' tool call.

    Args:
        pullNumberOrCommitHash (str): The pull request number (without '#' prefix) or 
            commit hash (full or abbreviated). For PR numbers, the function searches 
            for commits referencing that PR in their messages.

    Returns:
        Dict[str, Any]: A dictionary containing comprehensive commit and diff information:
            type (str): Either 'pull_request' or 'commit' indicating the source type
            identifier (str): The original input value (PR number or commit hash)
            commit_hash (str): The resolved commit SHA hash used for the diff
            author (str): The commit author's name and email as recorded in git
            message (str): The complete commit message including subject and body
            diff (str): The professionally formatted unified diff with visual enhancements
            files_changed (list): List of file paths that were modified in this commit
            stats (str): Statistical summary of changes (insertions/deletions)

    Raises:
        ValueError: When input is empty, None, invalid format, or workspace root is not configured
        RuntimeError: When git repository is not found, git commands fail, or commit/PR not found
        FileNotFoundError: When git executable is not found in system PATH
        PermissionError: When access to the git repository is denied
    """
    if not pullNumberOrCommitHash or not pullNumberOrCommitHash.strip():
        raise ValueError("Input cannot be empty. Please provide a pull request number or commit hash.")

    pullNumberOrCommitHash = pullNumberOrCommitHash.strip()
    
    # Check if it's all digits first
    try:
        is_all_digits = int(pullNumberOrCommitHash)
        is_all_digits = True
    except ValueError:
        is_all_digits = False
    
    # Check if it contains any hex letters (a-f or A-F)
    has_hex_letters = any(c in 'abcdefABCDEF' for c in pullNumberOrCommitHash)
    
    is_pr_number = is_all_digits and not has_hex_letters
    
    if not is_pr_number:
        # Validate commit hash format
        if not all(c in '0123456789abcdefABCDEF' for c in pullNumberOrCommitHash):
            raise ValueError("Invalid commit hash format - must contain only hexadecimal characters")
        if len(pullNumberOrCommitHash) < 7 or len(pullNumberOrCommitHash) > 40:
            raise ValueError("Invalid commit hash length - must be between 7 and 40 characters")
    else:
        # Validate PR number
        pr_number = int(pullNumberOrCommitHash)
        if pr_number <= 0:
            raise ValueError("Pull request number must be a positive integer")

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError("Workspace root is not configured in the application settings.")

    git_dir = os.path.join(workspace_root, ".git")
    if not os.path.exists(git_dir):
        raise RuntimeError(f"No git repository found in workspace root: {workspace_root}")
    
    try:
        commit_hash = None
        pr_number = None
        
        if is_pr_number:
            pr_number = pullNumberOrCommitHash
            _log_init_message(logging.INFO, f"Resolving PR #{pr_number} to commit hash")
            
            # Try to find commits that reference this PR number
            pr_search_cmd = f'git log --all --format="%H|%s" --grep="#{pr_number}" | head -10'
            try:
                pr_result = run_terminal_cmd(pr_search_cmd, f"Searching for PR #{pr_number} references")
                if not pr_result.get('stdout', '').strip():
                    raise RuntimeError(f"No commits found referencing PR #{pr_number}")
            except Exception as e:
                # Fallback: check mock data for backward compatibility
                mock_pull_requests = DB.get("pull_requests", {})
                if pr_number in mock_pull_requests:
                    _log_init_message(logging.INFO, f"Using mock data for PR #{pr_number}")
                    mock_pr = mock_pull_requests[pr_number]
                    return {
                        'type': 'pull_request',
                        'identifier': pr_number,
                        'commit_hash': 'mock_commit',
                        'author': mock_pr.get('author', 'Unknown'),
                        'message': mock_pr.get('description', ''),
                        'diff': mock_pr.get('diff', ''),
                        'files_changed': utils.extract_files_from_diff(mock_pr.get('diff', '')),
                        'stats': utils.extract_stats_from_diff(mock_pr.get('diff', ''))
                    }
                else:
                    raise RuntimeError(f"Pull request #{pr_number} not found in git history or mock data")
            
            # Parse the first matching commit
            for line in pr_result['stdout'].strip().split('\n'):
                if '|' in line and f"#{pr_number}" in line:
                    commit_hash = line.split('|')[0].strip()
                    break
            
            if not commit_hash:
                raise RuntimeError(f"No commits found referencing PR #{pr_number}")
                
        else:
            # Input is a commit hash
            commit_hash = pullNumberOrCommitHash
            
            # Validate that the commit exists
            validate_cmd = f'git rev-parse --verify {commit_hash}^{{commit}}'
            try:
                validate_result = run_terminal_cmd(validate_cmd, f"Validating commit {commit_hash}")
            except Exception as e:
                # Fallback: check mock data for backward compatibility
                mock_commits = DB.get("commits", {})
                if commit_hash in mock_commits:
                    _log_init_message(logging.INFO, f"Using mock data for commit {commit_hash}")
                    mock_commit = mock_commits[commit_hash]
                    return {
                        'type': 'commit',
                        'identifier': commit_hash,
                        'commit_hash': commit_hash,
                        'author': mock_commit.get('author', 'Unknown'),
                        'message': mock_commit.get('message', ''),
                        'diff': mock_commit.get('diff', ''),
                        'files_changed': utils.extract_files_from_diff(mock_commit.get('diff', '')),
                        'stats': utils.extract_stats_from_diff(mock_commit.get('diff', ''))
                    }
                else:
                    raise RuntimeError(f"Commit {commit_hash} not found in git history or mock data")
            
            # Use the validated/resolved commit hash
            commit_hash = validate_result['stdout'].strip()

        # Now fetch the actual commit details and diff
        _log_init_message(logging.INFO, f"Fetching diff for commit {commit_hash}")
        
        # Get commit information
        commit_info_cmd = f'git show --format="%an|%s|%b" --no-patch {commit_hash}'
        info_result = run_terminal_cmd(commit_info_cmd, f"Getting commit info for {commit_hash}")
        
        # Parse commit info
        info_lines = info_result['stdout'].strip().split('\n')
        if info_lines and '|' in info_lines[0]:
            author, subject, body = info_lines[0].split('|', 2)
            full_message = subject
            if body.strip():
                full_message += f"\n\n{body}"
        else:
            author = "Unknown"
            full_message = "Unable to parse commit message"
        
        # Get the diff
        diff_cmd = f'git show --format="" {commit_hash}'
        diff_result = run_terminal_cmd(diff_cmd, f"Getting diff for {commit_hash}")
        
        if not diff_result.get('success'):
            raise RuntimeError(f"Failed to get diff for {commit_hash}: {diff_result.get('stderr', 'Unknown error')}")
        
        raw_diff = diff_result['stdout']
        
        # Get changed files list
        files_cmd = f'git show --format="" --name-only {commit_hash}'
        files_result = run_terminal_cmd(files_cmd, f"Getting changed files for {commit_hash}")
        
        files_changed = []
        if files_result.get('success') and files_result.get('stdout'):
            files_changed = [f.strip() for f in files_result['stdout'].strip().split('\n') if f.strip()]
        
        # Get stats
        stats_cmd = f'git show --format="" --stat {commit_hash}'
        stats_result = run_terminal_cmd(stats_cmd, f"Getting stats for {commit_hash}")
        
        stats = "No statistics available"
        if stats_result.get('success') and stats_result.get('stdout'):
            stats_lines = stats_result['stdout'].strip().split('\n')
            if stats_lines:
                stats = stats_lines[-1]  # Last line usually contains the summary
        
        # Format the diff nicely
        formatted_diff = utils.format_diff_output(
            raw_diff, 
            commit_hash, 
            author, 
            full_message, 
            pr_number,
            files_changed
        )
        
        return {
            'type': 'pull_request' if pr_number else 'commit',
            'identifier': pr_number or commit_hash,
            'commit_hash': commit_hash,
            'author': author,
            'message': full_message,
            'diff': formatted_diff,
            'files_changed': files_changed,
            'stats': stats
        }
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Git command timed out while processing {pullNumberOrCommitHash}: {e}")
    except FileNotFoundError as e:
        if "git" in str(e).lower():
            raise FileNotFoundError("Git executable not found. Please ensure git is installed and available in PATH.")
        raise
    except PermissionError as e:
        raise PermissionError(f"Permission denied accessing git repository: {e}")
    except Exception as e:
        # Re-raise with more context
        raise RuntimeError(f"Unexpected error while processing {pullNumberOrCommitHash}: {type(e).__name__} - {e}") from e


@tool_spec(
    spec={
        'name': 'add_to_memory',
        'description': """ Makes a suggestion to the user to store a piece of learned knowledge
        
        (e.g., about deprecated functions, new patterns, facts about the codebase)
        into a persistent knowledge base for future reference by the AI.
        User must accept the tool call before the knowledge is stored.
        Especially important things to add to the knowledge base are operational
        knowledge about the codebase that are not obvious from just the code.
        As an example, using 'nvm use' before running terminal commands.
        If the user asks to remember something, for something to be saved,
        or to create a memory, you MUST use this tool. To update existing knowledge,
        provide the existing_knowledge_id parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'knowledge_to_store': {
                    'type': 'string',
                    'description': """ The specific piece of knowledge or fact to be stored.
                    It should be no more than a paragraph in length (max 500 characters). 
                    If the knowledge is an update or contradiction of previous
                    knowledge, do not mention or refer to the previous
                    knowledge. """
                },
                'title': {
                    'type': 'string',
                    'description': """ The title of the knowledge to be stored. This will be used to look
                    up and retrieve the knowledge later. This should be a short title
                    that captures the essence of the knowledge. """
                },
                'existing_knowledge_id': {
                    'type': 'string',
                    'description': """ Optional. The ID of existing knowledge
                    to update instead of creating new
                    knowledge. If provided, the
                    knowledge_to_store and title will
                    replace the existing knowledge entry. """
                }
            },
            'required': [
                'knowledge_to_store',
                'title'
            ]
        }
    }
)
def add_to_memory(
    knowledge_to_store: str,
    title: str,
    existing_knowledge_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Makes a suggestion to the user to store a piece of learned knowledge
    (e.g., about deprecated functions, new patterns, facts about the codebase)
    into a persistent knowledge base for future reference by the AI.
    User must accept the tool call before the knowledge is stored.
    Especially important things to add to the knowledge base are operational
    knowledge about the codebase that are not obvious from just the code.
    As an example, using 'nvm use' before running terminal commands.
    If the user asks to remember something, for something to be saved,
    or to create a memory, you MUST use this tool. To update existing knowledge,
    provide the existing_knowledge_id parameter.

    Args:
        knowledge_to_store (str): The specific piece of knowledge or fact to be stored.
                                  It should be no more than a paragraph in length (max 500 characters). 
                                  If the knowledge is an update or contradiction of previous
                                  knowledge, do not mention or refer to the previous
                                  knowledge.
        title (str): The title of the knowledge to be stored. This will be used to look
                     up and retrieve the knowledge later. This should be a short title
                     that captures the essence of the knowledge.
        existing_knowledge_id (Optional[str]): Optional. The ID of existing knowledge
                                               to update instead of creating new
                                               knowledge. If provided, the
                                               knowledge_to_store and title will
                                               replace the existing knowledge entry.

    Returns:
        Dict[str, str]: A dictionary indicating the outcome of the operation.
        On success, contains:
            - 'message' (str): A confirmation message, which includes the ID
              of the created or updated knowledge.

    Raises:
        ValueError: If `knowledge_to_store` is empty, if `title` is empty,
                    if `knowledge_to_store` exceeds paragraph length,
                    or if an `existing_knowledge_id` is provided but does not exist.
        InvalidInputError: If input parameters are of wrong type.
    """
    # Type checking first
    if not isinstance(knowledge_to_store, str):
        raise InvalidInputError("knowledge_to_store must be a string")
    
    if not isinstance(title, str):
        raise InvalidInputError("title must be a string")

    if existing_knowledge_id is not None:
        if not isinstance(existing_knowledge_id, str):
            raise InvalidInputError("existing_knowledge_id must be a string")
        
        existing_knowledge_id = existing_knowledge_id.strip()
        if not existing_knowledge_id:
            raise ValueError("existing_knowledge_id cannot be empty if provided")

    # Content validation after type checking
    if not knowledge_to_store:
        raise ValueError("knowledge_to_store cannot be empty.")

    if not title:
        raise ValueError("title cannot be empty.")

    # Validate paragraph length (approximately 500 characters for a reasonable paragraph)
    if len(knowledge_to_store) > 500:
        raise ValueError("knowledge_to_store must be no more than a paragraph in length (max 500 characters).")

    knowledge_base = DB.setdefault("knowledge_base", {})

    if existing_knowledge_id:
        if existing_knowledge_id not in knowledge_base:
            raise ValueError(
                f"Knowledge with ID '{existing_knowledge_id}' not found. Cannot update."
            )

        knowledge_base[existing_knowledge_id] = {
            "title": title,
            "knowledge_to_store": knowledge_to_store,
        }
        knowledge_id = existing_knowledge_id
        message = f"Successfully updated knowledge with ID: {knowledge_id}"
    else:
        next_id_counter = DB.setdefault("_next_knowledge_id", 1)
        knowledge_id = f"k_{next_id_counter:03d}"

        while knowledge_id in knowledge_base:
            next_id_counter += 1
            knowledge_id = f"k_{next_id_counter:03d}"

        DB["_next_knowledge_id"] = next_id_counter + 1

        knowledge_base[knowledge_id] = {
            "title": title,
            "knowledge_to_store": knowledge_to_store,
        }
        message = f"Successfully added new knowledge with ID: {knowledge_id}"

    return {"message": message}


@with_common_file_system
@tool_spec(
    spec={
        'name': 'codebase_search',
        'description': """ Finds code snippets semantically relevant to a natural language query,
        
        filtered by target directories if specified.
        
        This function searches the codebase for code segments that match the meaning
        and intent of the user's query, rather than just exact keywords. It also
        searches git repository metadata for additional context related to the query,
        providing both code snippets and relevant git information when available.
        Results include commit hash information for integration with git history tools.
        
        Guidelines for use:
        - To find code related to a specific task, feature description, or conceptual question 
          (e.g., "find how user authentication is handled", "show me data validation logic", 
          "where are API request parsers defined?").
        - When the exact file names or function/class names are unknown.
        - To get an understanding of how certain concepts are implemented across various 
          parts of the codebase. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The natural language search query describing the functionality,
                    concept, or implementation to find. Should be descriptive rather than
                    using exact function or variable names. """
                },
                'explanation': {
                    'type': 'string',
                    'description': """ Optional description of the search purpose
                    for logging and debugging. Used to track search patterns. Defaults to None. """
                },
                'target_directories': {
                    'type': 'array',
                    'description': """ Optional list of glob patterns to
                    restrict search scope to specific directories or file patterns.
                    Examples: ['src/**', 'lib/*.py', 'components/*']. Defaults to None
                    for full codebase search. """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def codebase_search(
    query: str,
    explanation: Optional[str] = None,
    target_directories: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Finds code snippets semantically relevant to a natural language query,
    filtered by target directories if specified.

    This function searches the codebase for code segments that match the meaning
    and intent of the user's query, rather than just exact keywords. It also
    searches git repository metadata for additional context related to the query,
    providing both code snippets and relevant git information when available.
    Results include commit hash information for integration with git history tools.

    Guidelines for use:
    - To find code related to a specific task, feature description, or conceptual question 
      (e.g., "find how user authentication is handled", "show me data validation logic", 
      "where are API request parsers defined?").
    - When the exact file names or function/class names are unknown.
    - To get an understanding of how certain concepts are implemented across various 
      parts of the codebase.

    Args:
        query (str): The natural language search query describing the functionality,
            concept, or implementation to find. Should be descriptive rather than
            using exact function or variable names.
        explanation (Optional[str]): Optional description of the search purpose
            for logging and debugging. Used to track search patterns. Defaults to None.
        target_directories (Optional[List[str]]): Optional list of glob patterns to
            restrict search scope to specific directories or file patterns.
            Examples: ['src/**', 'lib/*.py', 'components/*']. Defaults to None
            for full codebase search.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing matched code snippets
        and git metadata, ordered by relevance. Each dictionary contains:
            file_path (str): Absolute path to the file containing the code snippet
            snippet_bounds (str): A string of the form "start:end" (1-indexed, inclusive)
                indicating the snippet line range within the file
            snippet_content (str): The actual code content of the matched segment
            commit_hash (Optional[str]): The git commit hash associated with the snippet
                (when available, typically derived from blame information)
            is_git_metadata (Optional[bool]): Present and True for git metadata entries
                (commit messages, PR references); omitted for code snippet entries
            git_context (str): For git metadata entries, contains the commit message,
                branch name, or PR information that matched the query

    Raises:
        ValueError: If any of the following conditions are met:
            - The `query` parameter is not a non-empty string.
            - The `target_directories` parameter is provided but is not a list of non-empty strings.
            - The workspace root is not configured in the application settings.
            - The resolved workspace root is invalid.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    # --- Input Validation ---
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The 'query' parameter must be a non-empty string.")

    if target_directories is not None:
        if not isinstance(target_directories, list):
            raise ValueError("The 'target_directories' parameter must be a list of strings if provided.")
        for idx, pattern in enumerate(target_directories):
            if not isinstance(pattern, str) or not pattern.strip():
                raise ValueError(f"Element {idx} in 'target_directories' is not a valid non-empty string: {pattern!r}")
            # Optionally: add a simple glob pattern check here if desired

    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()

    n_initial_results = 20
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError(
            "Workspace root is not configured in the application settings."
        )
    normalized_workspace_root = os.path.normpath(workspace_root)

    all_code_chunks = chunk_codebase(DB)
    chunks_to_index: List[Dict[str, Any]] = []

    # Apply default exclusions first
    filtered_chunks_after_default_exclusion: List[Dict[str, Any]] = []
    for chunk in all_code_chunks:
        chunk_file_abs_path = os.path.normpath(chunk.get("file_path", ""))
        if not chunk_file_abs_path or not chunk_file_abs_path.startswith(normalized_workspace_root):
            # This check is important if chunk_codebase could somehow return paths outside root
            continue

        relative_path_for_chunk = os.path.relpath(chunk_file_abs_path, normalized_workspace_root).replace("\\", "/")

        if utils.is_path_excluded_for_search(
            relative_path_for_chunk,
            utils.DEFAULT_IGNORE_DIRS,
            utils.DEFAULT_IGNORE_FILE_PATTERNS
        ):
            logger.debug(f"Excluding chunk from default ignored path: {relative_path_for_chunk}")
            continue
        filtered_chunks_after_default_exclusion.append(chunk)

    # Now, apply target_directories filtering on the already-default-excluded list
    if target_directories and isinstance(target_directories, list) and len(target_directories) > 0:
        for chunk in filtered_chunks_after_default_exclusion:
            chunk_file_abs_path = os.path.normpath(chunk.get("file_path", ""))
            # This relative path calculation is repeated, can be optimized by storing it in the chunk or passing
            relative_path_for_chunk = os.path.relpath(chunk_file_abs_path, normalized_workspace_root).replace("\\", "/")
            chunk_dir_rel_path = os.path.dirname(relative_path_for_chunk)
            if chunk_dir_rel_path == "" : chunk_dir_rel_path = "." # for files in root

            if utils.matches_glob_patterns(path_to_check=chunk_dir_rel_path, include_patterns=target_directories) or\
            utils.matches_glob_patterns(path_to_check=relative_path_for_chunk, include_patterns=target_directories):
                chunks_to_index.append(chunk)
    else:
        chunks_to_index = filtered_chunks_after_default_exclusion

    if not chunks_to_index:
        logger.info("No chunks to index after default and target directory filtering.")
        return []

    # Initialize QdrantDBManager (in-memory for this function as per original design)
    # For a persistent index, persistent=True and a db_path would be used.
    vector_store = QdrantManager(
        collection_name="code_chunks_collection",
        persistent=False
    )
    # Clearing the in-memory collection if re-using the manager instance
    try:
        vector_store.clear_collection()
    except Exception as e:
        print_log(
            f"Warning: Clearing the in-memory vector store fialied.\n Error: {e}"
        )
        utils._log_util_message(logging.WARNING, f"Clearing the in-memory vector store fialied.\n Error: {e}", False)

    # Add the (filtered) chunks to QdrantDB
    vector_store.add_code_chunks(chunks_to_index)

    # Query QdrantDB, consider how many results are appropriate (n_results)
    raw_qdrant_output = vector_store.query_codebase(query, n_results=n_initial_results)
    final_snippets = transform_qdrant_results_via_llm(raw_qdrant_output, query)

    # Search git metadata for additional context
    try:
        git_metadata = utils.search_git_metadata_for_references(
            query=query, 
            workspace_root=normalized_workspace_root, 
            run_terminal_cmd_func=run_terminal_cmd
        )
        
        # Enhance snippets with git metadata if found
        if git_metadata.get("commit_hashes") or git_metadata.get("pr_numbers"):
            final_snippets = utils.enhance_snippets_with_git_metadata(final_snippets, git_metadata)
            _log_init_message(logging.DEBUG, f"Enhanced search results with {len(git_metadata.get('commit_hashes', []))} commits and {len(git_metadata.get('pr_numbers', []))} PRs")
    except Exception as e:
        # Don't fail the entire search if git metadata search fails
        _log_init_message(logging.WARNING, f"Git metadata search failed for query '{query}': {e}")

    # Add commit hash information to the final snippets
    for snippet in final_snippets:
        # Skip git metadata entries that already have this info
        if snippet.get("is_git_metadata"):
            continue
            
        file_path = snippet.get("file_path")
        if not file_path:
            continue

        file_entry = DB.get("file_system", {}).get(file_path)
        if not file_entry:
            continue

        git_blame_info = file_entry.get("git_blame")
        if not git_blame_info:
            continue

        snippet_bounds = snippet.get("snippet_bounds", '')
        if snippet_bounds == '':
            continue
        start_line_str = snippet_bounds.split(':')[0]
        if start_line_str == '':
            continue
        start_line = int(start_line_str)
    
        start_line_idx = start_line - 1
        if 0 <= start_line_idx < len(git_blame_info):
            # Direct lookup, no parsing needed
            blame_line_data = git_blame_info[start_line_idx]
            snippet["commit_hash"] = blame_line_data.get("commit_hash")

    # Clean up the temporary collection in QdrantDB
    try:
        vector_store.client.delete_collection(collection_name=vector_store.collection_name)
    except Exception as e:
        utils._log_util_message(logging.WARNING, f"Could not delete temporary QdrantDB collection '{vector_store.collection_name}': {e}", False)

    return final_snippets


@with_common_file_system
@tool_spec(
    spec={
        'name': 'reapply',
        'description': """ Re-applies the last attempted edit for a file using enhanced processing.
        
        This function retrieves the instructions and code edit details from the
        previously recorded edit operation for the specified `target_file`. It then
        invokes an LLM, providing the original instructions, the prior edit attempt,
        and the file's current content. The LLM generates the intended complete,
        final content of the file. This new content directly replaces the existing
        content in the application's internal file representation.
        
        Use this function only if a preceding `edit_file` operation produced an
        unexpected or incorrect result. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'target_file': {
                    'type': 'string',
                    'description': """ The path of the file to re-apply the last edit to
                    (relative to CWD or absolute within the workspace). """
                }
            },
            'required': [
                'target_file'
            ]
        }
    }
)
def reapply(target_file: str) -> Dict[str, Any]:
    """Re-applies the last attempted edit for a file using enhanced processing.

    This function retrieves the instructions and code edit details from the
    previously recorded edit operation for the specified `target_file`. It then
    invokes an LLM, providing the original instructions, the prior edit attempt,
    and the file's current content. The LLM generates the intended complete,
    final content of the file. This new content directly replaces the existing
    content in the application's internal file representation.

    Use this function only if a preceding `edit_file` operation produced an
    unexpected or incorrect result.

    Args:
        target_file (str): The path of the file to re-apply the last edit to
                           (relative to CWD or absolute within the workspace).

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome:
            - 'success' (bool): True if the re-application was successful.
            - 'message' (str): A message describing the outcome.
            - 'file_path' (str): The absolute path of the file processed.

    Raises:
        ValueError: If the workspace root is not configured or the file path is invalid.
        FileNotFoundError: If the target file is not found.
        IsADirectoryError: If the target path is a directory.
        LastEditNotFoundError: If no relevant previous edit is found for the file.
        InvalidInputError: If original instructions from the last edit are missing.
        LLMGenerationError: If the LLM fails to generate content for the re-application.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
        RuntimeError: For any other unexpected errors.
    """
    # --- Input Validation ---
    if not isinstance(target_file, str):
        raise TypeError(f"Argument 'target_file' must be a string, but got {type(target_file).__name__}.")
    if not target_file.strip():
        raise ValueError("Argument 'target_file' cannot be empty or contain only whitespace.")
    # --- End Input Validation ---
    
    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()
    
    try:
        # 1. Resolve path and perform initial checks.
        abs_path = utils.get_absolute_path(target_file)
        workspace_root_val = DB.get("workspace_root")
        if not workspace_root_val:
            raise ValueError("Workspace root is not configured.")
        normalized_workspace_root = os.path.normpath(workspace_root_val)
        if not abs_path.startswith(normalized_workspace_root) and abs_path != normalized_workspace_root:
            raise ValueError(f"Resolved path '{abs_path}' is outside permitted workspace.")

        # 2. Get current file content and check if it's a directory.
        existing_entry = utils.get_file_system_entry(abs_path)
        if not existing_entry:
            raise FileNotFoundError(f"Target file '{abs_path}' not found.")
        if existing_entry.get("is_directory"):
            raise IsADirectoryError(f"Target '{abs_path}' is a directory.")

        # 3. Retrieve last edit.
        last_edit = DB.get("last_edit_params")
        if not last_edit or last_edit.get("target_file") != abs_path:
            raise LastEditNotFoundError(f"No relevant previous edit found for '{abs_path}'.")

        original_code_edit = last_edit.get("code_edit", "")
        original_instructions = last_edit.get("instructions", "")
        if not original_instructions:
            raise InvalidInputError("Reapply failed: Original instructions missing from last edit.")

        # 4. Get current file content.
        current_lines = existing_entry.get("content_lines", [])
        current_content_str = "".join(current_lines)

        # 5. Construct prompt.
        prompt = f'''Review the following code edit task which needs re-application.

Original User Instructions:
"{original_instructions}"

Previously Proposed Code Edit String (which may have been flawed or misapplied):
{original_code_edit}

Current Content of File ({abs_path}):
{current_content_str}

Based on the ORIGINAL USER INSTRUCTIONS and the CURRENT FILE CONTENT, generate the **complete and final content** that the file '{abs_path}' should have after correctly applying the instructions.
Do NOT use '... existing code ...' delimiters. Output ONLY the raw, complete file content, without markdown fences or any other explanatory text.

Final File Content:
'''

        # 6. Call LLM.
        new_full_content_str = call_llm(prompt_text=prompt, temperature=0.3, timeout_seconds=180)

        if new_full_content_str is None:
            raise LLMGenerationError("LLM failed to generate content for reapply.")

        raw_llm_response = new_full_content_str
        new_full_content_str = new_full_content_str.strip()

        # 7. Process LLM output into lines.
        final_content_lines = utils._normalize_lines(new_full_content_str.splitlines(), ensure_trailing_newline=True)
        if not final_content_lines and new_full_content_str:
            final_content_lines = ['\n']
        elif not new_full_content_str:
            final_content_lines = []

        # 8. Update the internal state entry.
        new_size = utils.calculate_size_bytes(final_content_lines)
        new_timestamp = utils.get_current_timestamp_iso()
        existing_entry["content_lines"] = final_content_lines
        existing_entry["size_bytes"] = new_size
        existing_entry["last_modified"] = new_timestamp
        existing_entry["path"] = abs_path

        # 9. Update last_edit_params.
        DB["last_edit_params"] = {
            "target_file": abs_path,
            "code_edit": raw_llm_response,
            "instructions": original_instructions,
            "explanation": f"Reapplied edit for '{os.path.basename(abs_path)}' via LLM generation."
        }

        return {"success": True, "message": f"Edit successfully reapplied to '{abs_path}'.", "file_path": abs_path}

    except (ValueError, FileNotFoundError, IsADirectoryError, LastEditNotFoundError, InvalidInputError, LLMGenerationError) as e:
        _log_init_message(logging.WARNING, f"Reapply failed for '{target_file}': {e}")
        raise e
    except Exception as e:
        _log_init_message(logging.ERROR, f"Unexpected error during reapply for '{target_file}': {type(e).__name__} - {e}", exc_info=True)
        raise RuntimeError(f"An unexpected internal error occurred during reapply: {str(e)}") from e


@tool_spec(
    spec={
        'name': 'create_diagram',
        'description': """ Creates a Mermaid diagram that will be rendered in the chat UI. Provide the raw Mermaid DSL string via `content`.
        
        Use <br/> for line breaks, always wrap diagram texts/tags in double quotes, do not use custom colors, do not use :::, and do not use beta features.
        The diagram will be pre-rendered to validate syntax - if there are any Mermaid syntax errors, a MermaidSyntaxError exception will be raised. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'content': {
                    'type': 'string',
                    'description': "Raw Mermaid diagram definition (e.g., 'graph TD; A-->B;')."
                }
            },
            'required': [
                'content'
            ]
        }
    }
)
def create_diagram(content: str) -> str:
    """
    Creates a Mermaid diagram that will be rendered in the chat UI. Provide the raw Mermaid DSL string via `content`.
    Use <br/> for line breaks, always wrap diagram texts/tags in double quotes, do not use custom colors, do not use :::, and do not use beta features.
    The diagram will be pre-rendered to validate syntax - if there are any Mermaid syntax errors, a MermaidSyntaxError exception will be raised.

    Args:
        content (str): Raw Mermaid diagram definition (e.g., 'graph TD; A-->B;').

    Returns:
        str: A confirmation message if the diagram is created successfully.
             Note: The diagram is also rendered and displayed in the chat UI.

    Raises:
        InvalidInputError: Raised when the content is either not a string or is empty.
        MermaidSyntaxError: Raised when the Mermaid syntax is invalid.
        RuntimeError: Raised when diagram creation fails due to internal errors.
    """
    if not isinstance(content, str):
        raise InvalidInputError("Content must be a string.")
    if not content:
        raise InvalidInputError("No content provided.")
    
    # Validate basic Mermaid syntax
    utils.validate_mermaid_syntax(content)
    
    try:
        # Create and validate the Mermaid diagram
        Mermaid(content)
        return "Mermaid diagram created successfully."
        
    except Exception as e:
        # Handle mermaid-py specific errors
        error_message = str(e)
        if "Parse error" in error_message or "syntax" in error_message.lower():
            raise MermaidSyntaxError(f"Mermaid syntax is invalid. Error: {error_message}")
        else:
            raise RuntimeError(f"Failed to create Mermaid diagram: {error_message}")

      
@tool_spec(
    spec={
        'name': 'fix_lints',
        'description': """ Attempts to fix linting errors from the last edit by generating and applying new code edits.
        
        This function should be called if a previous edit introduced linting errors. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'run': {
                    'type': 'boolean',
                    'description': 'A flag to execute the function. Must be True.'
                }
            },
            'required': [
                'run'
            ]
        }
    }
)
def fix_lints(run: bool) -> Dict[str, Any]:
    """
    Attempts to fix linting errors from the last edit by generating and applying new code edits.
    This function should be called if a previous edit introduced linting errors.

    Args:
        run (bool): A flag to execute the function. Must be True.

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome. Contains:
            - 'message' (str): A message describing the outcome.
            - 'file_path' (str): The absolute, normalized path of the file processed.

    Raises:
        InvalidInputError: If `run` is False or if the last edit parameters are invalid.
        LastEditNotFoundError: If no previous edit information is found.
        FileNotInWorkspaceError: If the file from the last edit is not found.
        LintFixingError: If the lint fixing process fails.
        FailedToApplyLintFixesError: If the lint fixes are not applied successfully.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    if not run:
        raise InvalidInputError("fix_lints was called with run=False.")

    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()

    _log_init_message(logging.INFO, "Attempting to fix lints from last edit.")
    last_edit_params = DB.get("last_edit_params")

    if not last_edit_params:
        raise LastEditNotFoundError("Could not fix lints: No previous edit information found.")

    target_file = last_edit_params.get("target_file")
    original_code_edit = last_edit_params.get("code_edit")
    original_instructions = last_edit_params.get("instructions")

    if not all([target_file, original_code_edit, original_instructions]):
        raise InvalidInputError("Could not fix lints: Missing target file, code edit, or instructions from last operation.")

    file_entry = utils.get_file_system_entry(target_file)
    if not file_entry:
        raise FileNotInWorkspaceError(f"Could not fix lints: File '{target_file}' not found in file system.")

    current_content_lines = file_entry.get("content_lines", [])

    lint_fix_instructions = f"""
The file '{os.path.basename(target_file)}' was just modified with the original goal: "{original_instructions}".
The applied `code_edit` was:
---
{original_code_edit}
---
Please act as a linter. Review the `code_edit` that was applied and the current file content.
Your task is to identify and fix any linting errors or style issues that might have been introduced by the original edit.
Generate a new `code_edit` to apply these fixes.
Focus your changes *only* on the parts of the code that were modified by the original edit. Do not modify other parts of the file.
If no changes are needed, return an empty `code_edit`.
"""

    try:
        proposed_edit = utils.propose_code_edits(
            target_file_path_str=target_file,
            user_edit_instructions=lint_fix_instructions,
            original_file_content_lines=current_content_lines,
        )
    except Exception as e:
        _log_init_message(logging.ERROR, f"Error proposing lint fixes for '{target_file}': {e}", exc_info=True)
        raise LintFixingError(f"Failed to generate lint fixes for '{target_file}': {e}") from e

    new_code_edit = proposed_edit.get("code_edit")
    if not new_code_edit:
        return {
            "message": "Lint fixing model proposed no changes.",
            "file_path": target_file,
        }

    _log_init_message(logging.INFO, f"Applying proposed lint fixes to '{target_file}'.")
    
    try:
        # Call edit_file to apply the generated lint fixes.
        edit_result = edit_file(
            target_file=target_file,
            code_edit=new_code_edit,
            instructions=proposed_edit.get("instructions", "Automatically applying lint fixes."),
        )
        return edit_result
    except Exception as e:
        _log_init_message(logging.ERROR, f"Error applying lint fixes to '{target_file}': {e}", exc_info=True)
        raise FailedToApplyLintFixesError(f"Failed to apply lint fixes for '{target_file}': {e}") from e

  
@tool_spec(
    spec={
        'name': 'deep_search',
        'description': """ Ask a specialized search model to find relevant files, code blocks, and other context within the codebase.
        
        This tool is expensive since it requires waiting for a sub-agent to do a full search, so you should try to
        include all the relevant information in the query and avoid doing multiple searches about the same topic. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The search query to ask the search model. The search model will receive NO other context
                    besides this. It should be a broad query that includes as much information as needed about
                    the user's high-level goal, so that the search model can provide a comprehensive answer
                    and you won't need to do additional searching.
                    Must be between 3 and 1000 characters long and contain at least one alphanumeric character. """
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def deep_search(query: str) -> List[Dict[str, Any]]:
    """
    Ask a specialized search model to find relevant files, code blocks, and other context within the codebase.
    This tool is expensive since it requires waiting for a sub-agent to do a full search, so you should try to
    include all the relevant information in the query and avoid doing multiple searches about the same topic.

    Args:
        query (str): The search query to ask the search model. The search model will receive NO other context
                    besides this. It should be a broad query that includes as much information as needed about
                    the user's high-level goal, so that the search model can provide a comprehensive answer
                    and you won't need to do additional searching.
                    Must be between 3 and 1000 characters long and contain at least one alphanumeric character.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing search results, each with:
            - 'file_path': Path to the file
            - 'snippet_bounds': Line numbers of the match
            - 'snippet_content': The matching code snippet
    Raises:
        InvalidInputError: If query is empty, contains only whitespace, is shorter than 3 characters,
                          longer than 1000 characters, or contains only special characters.
        ValueError: If 'workspace_root' is not configured in DB.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    # Input validation
    # Remove leading/trailing whitespace for validation
    query_stripped = query.strip()
    
    if not query_stripped:
        raise InvalidInputError("Query cannot be empty or contain only whitespace")
    
    if len(query_stripped) < 3:
        raise InvalidInputError("Query must be at least 3 characters long")
    
    if len(query_stripped) > 1000:
        raise InvalidInputError("Query must not exceed 1000 characters")
    
    # Check if query contains only special characters or whitespace
    if not any(c.isalnum() for c in query_stripped):
        raise InvalidInputError("Query must contain at least one alphanumeric character")
    
    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()
    
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError(
            "Workspace root is not configured in the application settings."
        )
    # 1. First, do a semantic search using the base codebase_search
    semantic_results = codebase_search(query=query)

    # 2. Extract key terms and concepts from the query using LLM
    prompt = f"""Analyze this search query and extract key technical terms and concepts.
    Query: {query}
    
    Return a JSON object with:
    - key_terms: List of important technical terms (max 5)
    - concepts: List of high-level concepts (max 3)
    - search_context: A brief description of what we're looking for
    
    Format the response as valid JSON only."""

    analysis = call_llm(prompt_text=prompt, temperature=0.1)

    # Clean and validate JSON response
    analysis = analysis.strip()
    analysis = re.sub(r'^```(?:json)?\s*', '', analysis)
    analysis = re.sub(r'\s*```$', '', analysis)

    try:
        analysis_dict = json.loads(analysis)
    except json.JSONDecodeError:
        repaired_json = repair_json(analysis)
        if repaired_json:
            try:
                analysis_dict = json.loads(repaired_json)
            except json.JSONDecodeError:
                analysis_dict = {
                    "key_terms": [],
                    "concepts": [],
                    "search_context": query
                }
        else:
            analysis_dict = {
                "key_terms": [],
                "concepts": [],
                "search_context": query
            }

    # 3. Perform targeted text search for key terms
    text_results = []
    seen_paths = set()

    # Add semantic results to seen paths
    for result in semantic_results:
        seen_paths.add(result.get("file_path"))

    # Text-based search for key terms
    for term in analysis_dict.get("key_terms", []):
        term_results = grep_search(
            query=term,
            case_sensitive=False
        )
        # Only add results from new files
        for result in term_results:
            if result.get("file_path") not in seen_paths:
                seen_paths.add(result.get("file_path"))
                # Get the full file content to create a proper snippet
                file_path = result.get("file_path")
                line_number = result.get("line_number", 1)
                try:
                    file_entry = DB.get("file_system", {}).get(file_path)
                    if file_entry and isinstance(file_entry.get("content_lines"), list):
                        content_lines = file_entry["content_lines"]
                        # Calculate snippet bounds with context (20 lines before and after)
                        start_line = max(1, line_number - 20)
                        end_line = min(len(content_lines), line_number + 20)
                        # Create a proper snippet result
                        text_results.append({
                            "file_path": file_path,
                            "snippet_bounds": [start_line, end_line],
                            "snippet_content": "".join(content_lines[start_line-1:end_line])
                        })
                except Exception:
                    continue

    # 4. Process all results with LLM to generate better snippets
    # Collect all file contents
    all_files_content = {}
    for result in semantic_results + text_results:
        file_path = result.get("file_path")
        if file_path not in all_files_content:
            try:
                file_entry = DB.get("file_system", {}).get(file_path)
                if file_entry and isinstance(file_entry.get("content_lines"), list):
                    all_files_content[file_path] = file_entry["content_lines"]
            except Exception:
                continue

    # Prepare context for LLM
    context = {
        "query": query,
        "search_context": analysis_dict.get("search_context", query),
        "key_terms": analysis_dict.get("key_terms", []),
        "concepts": analysis_dict.get("concepts", []),
        "files": []
    }

    # Add file contents to context
    for file_path, content_lines in all_files_content.items():
        context["files"].append({
            "path": file_path,
            "content": "".join(content_lines)
        })

    # Ask LLM to analyze and create snippets
    prompt = f"""Given the following search context and files, create the most relevant code snippets.

Search Query: {query}
Search Context: {context['search_context']}
Key Terms: {', '.join(context['key_terms'])}
Concepts: {', '.join(context['concepts'])}

Files to analyze:
{json.dumps(context['files'], indent=2)}

Please analyze these files and return a JSON array of the most relevant code snippets. Each snippet should:
1. Include enough context to understand the code.
2. Focus on the most relevant parts related to the query.
3. Include line numbers for the snippet bounds.
4. Be properly formatted and complete.
5. Order the responses by prioritizing those that best match the query contextually and logically, followed by the rest in descending order of relevance.

IMPORTANT: Each snippet MUST include the exact file path from the input files. Do not modify or omit the file paths.

Return the results as a JSON array with each object containing:
- file_path: The exact file path from the input files (REQUIRED)
- snippet_bounds: [start_line, end_line] (REQUIRED)
- snippet_content: The actual code snippet (REQUIRED)

Example of a valid response:
[
  {{
    "file_path": "/exact/path/from/input/file1.py",
    "snippet_bounds": [10, 20],
    "snippet_content": "def example():\n    return True"
  }},
  {{
    "file_path": "/exact/path/from/input/file2.py",
    "snippet_bounds": [5, 15],
    "snippet_content": "class Example:\n    def __init__(self):\n        pass"
  }}
]

Format the response as valid JSON only."""

    try:
        llm_response = call_llm(prompt_text=prompt, temperature=0.1)
        # Clean and parse JSON response
        llm_response = llm_response.strip()
        llm_response = re.sub(r'^```(?:json)?\s*', '', llm_response)
        llm_response = re.sub(r'\s*```$', '', llm_response)

        try:
            final_results = json.loads(llm_response)
            # Validate that all results have required fields
            valid_results = []
            for result in final_results:
                if all(key in result for key in ["file_path", "snippet_bounds", "snippet_content"]):
                    if result["file_path"] in all_files_content:  # Verify file path exists
                        valid_results.append(result)
            final_results = valid_results
        except json.JSONDecodeError:
            repaired_json = repair_json(llm_response)
            if repaired_json:
                try:
                    final_results = json.loads(repaired_json)
                    # Validate repaired results
                    valid_results = []
                    for result in final_results:
                        if all(key in result for key in ["file_path", "snippet_bounds", "snippet_content"]):
                            if result["file_path"] in all_files_content:
                                valid_results.append(result)
                    final_results = valid_results
                except json.JSONDecodeError:
                    final_results = semantic_results + text_results
            else:
                final_results = semantic_results + text_results
    except Exception:
        final_results = semantic_results + text_results

    # Limit to top 10 results
    return final_results[:10]


@tool_spec(
    spec={
        'name': 'fetch_rules',
        'description': """ Fetches rules provided by the user to help with navigating the codebase.
        
        This function fetches rules provided by the user to help with navigating the codebase.
        Rules contain information about the codebase that can be used to help with generating code.
        If a user's request seems like it would benefit from a rule, this tool is used to fetch the rule. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'rule_names': {
                    'type': 'array',
                    'description': """ The names of the rules to fetch. Each string in the list
                    is the name of the rule to fetch. """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'rule_names'
            ]
        }
    }
)
def fetch_rules(rule_names: List[str]) -> Dict[str, Any]:
    """Fetches rules provided by the user to help with navigating the codebase.

    This function fetches rules provided by the user to help with navigating the codebase.
    Rules contain information about the codebase that can be used to help with generating code.
    If a user's request seems like it would benefit from a rule, this tool is used to fetch the rule.

    Args:
        rule_names (List[str]): The names of the rules to fetch. Each string in the list
                                is the name of the rule to fetch.

    Returns:
        Dict[str, Any]: A dictionary containing the function's results.
            - 'rules' (Dict[str, Any]): A dictionary of fetched rules containing:
                - Keys (str): Rule names as specified in the input rule_names list
                - Values (Any): Rule content which can be strings, dictionaries, or other structured data

    Raises:
        ValidationError: If input arguments fail validation:
            - If rule_names is not a list
            - If any element in rule_names is not a string
            - If any rule name is empty or contains only whitespace
            - If any requested rule name is not found in available rules
    """

    if not isinstance(rule_names, list):
        raise custom_errors.ValidationError("Input 'rule_names' must be a list.")

    for name in rule_names:
        if not isinstance(name, str):
            raise custom_errors.ValidationError(
                "All elements in 'rule_names' must be strings. Found an element that is not a string."
            )
        if not name.strip():
            raise custom_errors.ValidationError(
                "Rule names cannot be empty or contain only whitespace."
            )

    available_rules = DB.get("available_instructions") or {}
    unknown_rules_set = set()
    for name in rule_names:
        if name not in available_rules:
            unknown_rules_set.add(name)

    if unknown_rules_set:
        sorted_unknown_rules = sorted(list(unknown_rules_set))
        if not available_rules:
            available_keys_str = "None"
        else:
            available_keys_str = ", ".join(sorted(available_rules.keys()))

        raise custom_errors.ValidationError(
            f"Unknown rule(s) requested: {', '.join(sorted_unknown_rules)}. "
            f"Available rules are: {available_keys_str}."
        )

    fetched_rules: Dict[str, Any] = {}
    for name in rule_names:
        fetched_rules[name] = available_rules[name]

    return {"rules": fetched_rules}


# --- Session State for Persistent Sandbox ---
# Note: Session state is now managed by common_utils.session_manager
# These local variables are kept for backward compatibility but delegate to shared state
SESSION_SANDBOX_DIR: Optional[str] = None
SESSION_INITIALIZED: bool = False
_SANDBOX_TEMP_DIR_OBJ: Optional[tempfile.TemporaryDirectory] = None
# -----------------------------------------


# --- Utility Functions ---
def get_file_content(path: str) -> Dict[str, Any]:
    try:
        # Implement the logic to retrieve file content from the persistent sandbox
        # This is a placeholder implementation
        return {'success': True, 'message': "File content retrieved successfully.", 'content': "This is the content of the file."}
    except Exception as e:
        return {'success': False, 'message': f"An unexpected error occurred: {e}", 'content': None}


def end_session() -> Dict[str, Any]:
    """
    Ends the current terminal session, syncs file changes, and cleans up the sandbox.

    This function should be called when a series of terminal commands is complete.
    It synchronizes any modifications made in the persistent sandbox environment
    back to the in-memory database and then removes the temporary sandbox directory.

    Note: This now delegates to the shared session manager, which coordinates
    cleanup across all terminal-like APIs (cursor, gemini_cli, terminal).

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome of the session cleanup.
    """
    global SESSION_SANDBOX_DIR, SESSION_INITIALIZED, _SANDBOX_TEMP_DIR_OBJ

    _log_init_message(logging.INFO, "Requesting shared session cleanup via session_manager...")
    
    # Delegate to shared session manager
    result = session_manager.end_shared_session(
        api_name="cursor",
        db_instance=DB,
        update_func=utils.update_db_file_system_from_temp,
        normalize_path_func=utils._normalize_path_for_db
    )
    
    # Update local state to reflect shared state
    SESSION_SANDBOX_DIR = None
    SESSION_INITIALIZED = False
    _SANDBOX_TEMP_DIR_OBJ = None
    
    _log_init_message(
        logging.INFO if result['success'] else logging.ERROR,
        f"Session cleanup result: {result['message']}"
    )
    
    return result


@tool_spec(
    spec={
        'name': 'get_cwd',
        'description': """ Returns the current working directory of the workspace.
        
        This function returns the current working directory of the workspace.
        It is useful for debugging and for commands that need to know the current
        directory. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'explanation': {
                    'type': 'string',
                    'description': """ A description of why this operation is being performed.
                    Not used in the return value but may be utilized for logging or auditing.
                    Defaults to None. """
                }
            },
            'required': [
                'explanation'
            ]
        }
    }
)
def get_cwd(explanation: Optional[str] = None) -> Dict[str, Any]:
    """Returns the current working directory of the workspace.

    This function returns the current working directory of the workspace.
    It is useful for debugging and for commands that need to know the current
    directory.

    Args:
        explanation (Optional[str], optional): A description of why this operation is being performed.
            Not used in the return value but may be utilized for logging or auditing.
            Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): True if the operation was successful.
            - cwd (str): The current working directory of the workspace.
            - message (str): A descriptive message about the operation.

    Raises:
        ValueError: If the workspace root is not configured in the application settings.
        WorkspaceNotHydratedError: When the workspace is not properly initialized.
    """
    # Validate workspace is hydrated before performing file system operations
    validate_workspace_hydration()

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError("Workspace root is not configured in the application settings.")

    current_cwd = DB.get("cwd")
    if not current_cwd:
        raise ValueError("Current working directory is not set.")

    return {
        "success": True,
        "cwd": current_cwd,
        "message": f"Current working directory: {current_cwd}"
    }
