from common_utils.print_log import print_log
# copilot/SimulationEngine/utils.py
import os
import datetime
import re
import fnmatch  # For glob pattern matching
import mimetypes  # For a more robust way to guess if a file is binary
import logging
import inspect
import fnmatch
import json
import common_utils.terminal_filesystem_utils as common_utils

from typing import Dict, List, Optional, Any, Tuple, Union 

# Direct import of the database state
from .db import DB

# --- Logger Setup for this utils.py module ---
logger = logging.getLogger(__name__)

# Import the LLM calling function
from .llm_interface import call_llm

# --- Configuration for File Handling (Hydration) ---
MAX_FILES_FOR_SMALL_WORKSPACE = 20
MAX_LLM_CONTENT_CHARS_PER_FILE = 15000  # Max characters of a file's content to send to LLM
MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE = 50  # Limit processing for very large workspaces
MAX_FILE_SIZE_TO_LOAD_CONTENT_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_TO_LOAD_CONTENT_MB * 1024 * 1024
BINARY_CONTENT_PLACEHOLDER = ["<Binary File - Content Not Loaded>"]
LARGE_FILE_CONTENT_PLACEHOLDER = [
    f"<File Exceeds {MAX_FILE_SIZE_TO_LOAD_CONTENT_MB}MB - Content Not Loaded>"
]
ERROR_READING_CONTENT_PLACEHOLDER = ["<Error Reading File Content>"]

DEFAULT_IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", "build", "dist",
    ".hg", ".svn", "target", "out", "deps", "_build", # Common build/dependency/VCS folders
    "site-packages" , # Python site-packages
    ".DS_Store", # macOS specific
    # IDE specific folders
    ".idea", ".vscode", 
    "coverage", ".pytest_cache", # Testing related
    "docs/_build" # Common for Sphinx docs
}
DEFAULT_IGNORE_FILE_PATTERNS = {
    "*.pyc", "*.pyo", # Python compiled files
    "*.o", "*.so", "*.dll", "*.exe", # Compiled objects and executables
    "*.log", # Log files (can be debatable, but often noisy for semantic search)
    "*.tmp", "*.temp", # Temporary files
    "*.swp", "*.swo", # Vim swap files
}
# Note: For glob patterns like "*.pyc", _is_path_in_ignored_directory would need to handle them,
# or they should be used with fnmatch directly on filenames.
# DEFAULT_IGNORED_DIRECTORY_COMPONENTS is primarily for directory *names*.
# We will add a separate check for filename patterns if needed, or rely on _is_path_in_ignored_directory
# if it's enhanced to understand simple file globs. For now, it's based on path components.


def _log_util_message(level: int, message: str, exc_info: bool = False) -> None:
    """
    Logs a message with information about the function within utils.py that called it.
    """
    log_message = message
    try:
        # Navigates up the call stack to find the frame of the function in utils.py
        # that called this _log_util_message helper.
        frame = inspect.currentframe()
        caller_frame = frame.f_back # Frame of the direct caller within utils.py
        if caller_frame and caller_frame.f_code:
            func_name = caller_frame.f_code.co_name
            line_no = caller_frame.f_lineno
            log_message = f"{func_name}:{line_no} - {message}"
    except Exception: # Fallback if frame inspection fails.
        pass

    # Log using the standard logging levels; default to DEBUG.
    if level == logging.ERROR: logger.error(log_message, exc_info=exc_info)
    elif level == logging.WARNING: logger.warning(log_message, exc_info=exc_info)
    elif level == logging.INFO: logger.info(log_message)
    else: logger.debug(log_message) # Default log level is DEBUG.


# --- ipynb file creation utilities ---

# Helper function to generate minimal .ipynb content
# Defined as a top-level "private" function before the main function.
def _get_minimal_ipynb_content_lines() -> List[str]:
    """Generates the default content for a new, empty Jupyter Notebook as a list of lines."""
    content_dict = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.9"  # Generic Python version
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    
    json_string = json.dumps(content_dict, indent=2)
    lines = [line + '\n' for line in json_string.splitlines()]
    return lines



# --- Path Utilities ---


def get_absolute_path(relative_or_absolute_path: str) -> str:
    """
    Resolves a given path to an absolute path, normalized, within the application's workspace
    as defined in the 'DB' configuration.

    - If the path is already absolute and starts with the 'workspace_root' (from `DB`),
      it's normalized and returned.
    - If the path is absolute but not within the configured 'workspace_root', a ValueError is raised.
    - If the path is relative, it's joined with the 'cwd' (current working directory from `DB`,
      defaulting to 'workspace_root') and then normalized.
    """
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise ValueError(
            "Workspace root is not configured. Check application settings."
        )

    if os.path.isabs(relative_or_absolute_path):
        normalized_path = _normalize_path_for_db(relative_or_absolute_path)
        if not normalized_path.startswith(_normalize_path_for_db(workspace_root)):
            raise ValueError(
                f"Absolute path '{normalized_path}' is outside the configured workspace root '{workspace_root}'."
            )
        return normalized_path
    else:
        cwd = DB.get("cwd", workspace_root)
        # Join and normalize the path
        resolved_path = _normalize_path_for_db(os.path.join(cwd, relative_or_absolute_path))
        
        # Apply path traversal protection (following existing codebase pattern)
        workspace_root_normalized = _normalize_path_for_db(workspace_root)
        
        # Check 1: Basic startswith check
        if not resolved_path.startswith(workspace_root_normalized):
            # Check 2: More robust check using commonpath (following resolve_target_path_for_cd pattern)
            if workspace_root_normalized != resolved_path:
                try:
                    common_path = _normalize_path_for_db(os.path.commonpath([workspace_root_normalized, resolved_path]))
                    if common_path != workspace_root_normalized:
                        raise ValueError(
                            f"Path '{relative_or_absolute_path}' resolves to '{resolved_path}' which is outside the workspace root '{workspace_root}'."
                        )
                except ValueError:
                    # This can happen if paths are on different drives (Windows) or other complex scenarios
                    raise ValueError(
                        f"Path '{relative_or_absolute_path}' resolves to '{resolved_path}' which is outside the workspace root '{workspace_root}'."
                    )
        
        return resolved_path


def get_current_timestamp_iso() -> str:
    """Returns the current time in ISO 8601 format, UTC (suffixed with 'Z')."""
    return (
        datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    )


# --- File System Utilities (DB-Only Operations) ---


def get_file_system_entry(path: str):
    """
    Retrieves a file or directory metadata entry from the in-memory 'DB["file_system"]'.
    The provided path is resolved to an absolute, normalized path before lookup.
    Returns the entry dict or None if not found or if path is invalid.
    """
    try:
        abs_path = get_absolute_path(path)
        return DB.get("file_system", {}).get(abs_path)
    except (
        ValueError
    ):  # Raised by get_absolute_path if path is invalid (e.g., outside workspace)
        return None


def path_exists(path: str) -> bool:
    """
    Checks if a path exists as an entry in the in-memory 'DB["file_system"]'.
    The path is resolved to an absolute path before checking.
    """
    try:
        abs_path = get_absolute_path(path)
        return abs_path in DB.get("file_system", {})
    except ValueError:  # If get_absolute_path raises error
        return False


def is_directory(path: str) -> bool:
    """
    Checks if a given path corresponds to a directory in 'DB["file_system"]'.
    The path is resolved to an absolute path before checking.
    Returns False if the path doesn't exist or is not a directory.
    """
    entry = get_file_system_entry(path)  # get_file_system_entry handles path resolution
    return entry is not None and entry.get("is_directory", False)


def is_file(path: str) -> bool:
    """
    Checks if a given path corresponds to a file in 'DB["file_system"]'.
    The path is resolved to an absolute path before checking.
    Returns False if the path doesn't exist or is not a file.
    """
    entry = get_file_system_entry(path)  # get_file_system_entry handles path resolution
    return entry is not None and not entry.get("is_directory", False)


def calculate_size_bytes(content_lines: list[str]) -> int:
    """Calculates the total size of a list of content lines in bytes (UTF-8 encoded)."""
    return sum(len(line.encode("utf-8")) for line in content_lines)


# --- Edit Utilities ---


def _normalize_lines(line_list: list[str], ensure_trailing_newline=True) -> list[str]:
    """Ensures lines in a list end with a newline, based on the flag."""
    if not line_list:
        return []
    normalized = []
    for i, line_text in enumerate(line_list):
        is_last_line = i == len(line_list) - 1
        if line_text.endswith("\n"):
            normalized.append(line_text)
        elif ensure_trailing_newline or not is_last_line:
            normalized.append(line_text + "\n")
        else:
            normalized.append(line_text)
    return normalized


def _find_unique_context_in_original(
    original_lines: list[str], context_lines: list[str], start_search_idx: int
) -> tuple[int, int]:  # Returns (match_start_idx, len_of_matched_context)
    """
    Finds a unique match for context_lines within original_lines from start_search_idx.
    Tries longer context first (up to 5 lines).
    Raises ValueError if context is not found or if multiple ambiguous matches are found.
    Returns start index of the unique match and length of context that matched.
    """
    if not context_lines or not original_lines:
        raise ValueError(
            "Context lines or original lines are empty, cannot find match."
        )

    max_context_len = min(len(context_lines), 5)  # Try with up to 5 lines of context

    for N in range(max_context_len, 0, -1):  # Try 5 lines, then 4, ..., then 1
        current_context_segment = context_lines[:N]  # For leading context from a hunk

        found_indices = []
        len_segment = len(current_context_segment)

        if len_segment == 0:
            continue  # Skip if context segment becomes empty

        for i in range(start_search_idx, len(original_lines) - len_segment + 1):
            if original_lines[i : i + len_segment] == current_context_segment:
                found_indices.append(i)

        if len(found_indices) == 1:
            return found_indices[0], len_segment  # Unique match found
        elif len(found_indices) > 1:
            raise ValueError(
                f"Ambiguous context: '{current_context_segment[0].strip()}{'...' if N > 1 else ''}' "
                f"matched at multiple locations starting from index {start_search_idx}: {found_indices}."
            )
    # If loop finishes, no context (not even 1 line) was found
    raise ValueError(
        f"Context not found in original lines: '{context_lines[0].strip()}{'...' if len(context_lines) > 1 else ''}' "
        f"starting from index {start_search_idx}."
    )


def _is_delimiter_line(line: str, core_text: str) -> bool:
    """Checks if a line is a delimiter comment line."""
    line_stripped = line.strip()
    # Pattern for common single-line comments followed by the core delimiter text
    # Allows for optional space after comment characters.
    single_line_comment_pattern = r"^\s*(//|#|--|;|REM)\s*" + re.escape(core_text)
    if re.match(
        single_line_comment_pattern, line_stripped, re.IGNORECASE
    ):  # Case insensitive for "existing code"
        return True
    # Basic check for common multi-line comment styles
    if (
        line_stripped.startswith("/*")
        and line_stripped.endswith("*/")
        and core_text in line_stripped
    ):
        return True
    if line_stripped.startswith("") and core_text in line_stripped:
        return True
    # Add more language-specific multi-line comment delimiters if needed
    return False


def apply_code_edit(original_lines_raw: list[str], code_edit_str: str) -> list[str]:
    """
    Applies structured edits to original content lines by matching context
    within provided code segments and preserving original sections indicated by delimiters.

    If no delimiters (e.g., comments containing "... existing code ...") are found,
    `code_edit_str` entirely replaces `original_lines_raw`.

    If delimiters are present, the function parses `code_edit_str` into
    proposed code segments and delimiter markers. It then reconstructs the content:
    - Code segments are taken from `code_edit_str`. Their placement and
      the span of original lines they replace are determined by matching their
      leading and trailing context lines within `original_lines_raw`.
    - Delimiters instruct the function to handle sections of `original_lines_raw`.
      Generally, original lines between the span of one code segment and the start
      of the next code segment's anchor are preserved if a delimiter indicates so
      at the beginning or end of the edit string. Intermediate delimiters imply
      the original lines between the spans of two consecutive code segments are
      replaced/skipped.
    - If `code_edit_str` ends with a delimiter, remaining `original_lines_raw`
      after the last processed code segment are preserved.
    - If `code_edit_str` ends with a code segment, any remaining `original_lines_raw`
      after the section covered by that segment are discarded.

    Args:
        original_lines_raw (list[str]): Original content lines.
        code_edit_str (str): Edit string with proposed code segments, their context,
                             and delimiters.

    Returns:
        list[str]: New content lines after edits, with newlines normalized.

    Raises:
        ValueError: If context provided in `code_edit_str` is ambiguous (multiple
                    matches) or not found in `original_lines_raw` when required.
    """
    original_lines = _normalize_lines(original_lines_raw, ensure_trailing_newline=True)

    raw_edit_lines_with_ends = code_edit_str.splitlines(keepends=True)
    delimiter_core_text = "... existing code ..."
    has_delimiters = any(
        _is_delimiter_line(line, delimiter_core_text)
        for line in raw_edit_lines_with_ends
    )

    if not has_delimiters:  # No delimiters, code_edit_str is the full new content.
        if not code_edit_str:
            return []
        return _normalize_lines(
            code_edit_str.splitlines(), ensure_trailing_newline=True
        )

    result_lines: list[str] = []
    current_original_idx = 0  # Pointer in original_lines

    parsed_segments = []
    current_segment_buffer: list[str] = []
    for line in raw_edit_lines_with_ends:
        if _is_delimiter_line(line, delimiter_core_text):
            if current_segment_buffer:
                parsed_segments.append(list(current_segment_buffer))
            parsed_segments.append(None)
            current_segment_buffer = []
        else:
            current_segment_buffer.append(line)
    if current_segment_buffer:
        parsed_segments.append(list(current_segment_buffer))

    if not any(
        segment for segment in parsed_segments if segment is not None
    ):  # Only delimiters
        return original_lines

    # --- Main Patching Loop ---
    for i, current_segment_data in enumerate(parsed_segments):
        if current_segment_data is None:  # Current item is a Delimiter marker
            # This delimiter indicates that original lines should be copied.
            # The amount to copy is determined by where the *next* code segment anchors.

            is_trailing_delimiter = i == len(parsed_segments) - 1

            if is_trailing_delimiter:
                # Preserve all remaining original lines.
                if current_original_idx < len(original_lines):
                    result_lines.extend(original_lines[current_original_idx:])
                current_original_idx = len(original_lines)
            elif i + 1 < len(parsed_segments) and parsed_segments[i + 1] is not None:
                # Delimiter is followed by another code segment.
                next_code_segment_raw = parsed_segments[i + 1]
                if not next_code_segment_raw:
                    continue  # Next segment is empty.

                next_segment_normalized = _normalize_lines(
                    [line.rstrip("\r\n") for line in next_code_segment_raw]
                )
                leading_context_of_next_segment = next_segment_normalized[
                    : min(len(next_segment_normalized), 5)
                ]

                if leading_context_of_next_segment:
                    # Find where the next segment's context starts in original_lines.
                    match_start_in_original, _ = _find_unique_context_in_original(
                        original_lines,
                        leading_context_of_next_segment,
                        current_original_idx,
                    )
                    # Copy original lines from current_original_idx up to this anchor.
                    if match_start_in_original >= current_original_idx:
                        result_lines.extend(
                            original_lines[current_original_idx:match_start_in_original]
                        )
                    current_original_idx = (
                        match_start_in_original  # Update cursor to the anchor point.
                    )
            # If delimiter is followed by another delimiter, or an empty segment,
            # no original lines are copied by *this* delimiter; current_original_idx remains.

        else:  # Current item is a proposed Code Segment
            proposed_code_lines_raw = current_segment_data
            if not proposed_code_lines_raw:
                continue  # Skip empty segments.

            # This proposed code segment's lines are added to the result.
            result_lines.extend(proposed_code_lines_raw)

            # Now, crucially, advance current_original_idx past the original lines
            # that this proposed segment (with its context) has effectively replaced.
            segment_normalized = _normalize_lines(
                [line.rstrip("\r\n") for line in proposed_code_lines_raw]
            )

            # 1. Determine the start of this segment's span in original_lines
            #    based on its leading context.
            leading_context = segment_normalized[: min(len(segment_normalized), 5)]
            original_segment_span_start_idx = (
                current_original_idx  # Default if no context or not found first
            )
            len_lead_matched = 0
            if leading_context:
                try:
                    # Check if this segment's leading context matches at current_original_idx.
                    # If not, it implies an error or a pure insertion if current_original_idx was 0.
                    # The preceding delimiter should have already positioned current_original_idx correctly.
                    match_idx, len_lead_matched = _find_unique_context_in_original(
                        original_lines, leading_context, current_original_idx
                    )
                    if match_idx != current_original_idx:
                        # If this isn't the very first hunk of a file starting with content,
                        # this indicates a misalignment from the previous delimiter's anchoring.
                        is_first_actual_hunk = True
                        for k_idx in range(i):
                            if parsed_segments[k_idx] is not None:
                                is_first_actual_hunk = False
                                break
                        if not is_first_actual_hunk:
                            raise ValueError(
                                f"Segment context misaligned. Expected at {current_original_idx}, found at {match_idx}."
                            )
                        else:  # First hunk, it defines its own start.
                            original_segment_span_start_idx = match_idx
                    else:
                        original_segment_span_start_idx = match_idx

                except ValueError:
                    # Leading context not found. If this was the first segment with content,
                    # it's a prepend; otherwise, it's an error.
                    is_first_actual_hunk = True
                    for k_idx in range(i):
                        if parsed_segments[k_idx] is not None:
                            is_first_actual_hunk = False
                            break
                    if not is_first_actual_hunk:
                        raise  # Re-raise context not found for intermediate hunks
                    # For a prepend, original_segment_span_start_idx remains current_original_idx (0)
                    # and len_lead_matched remains 0.

            # 2. Determine the end of this segment's span in original_lines
            search_for_trailing_from_idx = (
                original_segment_span_start_idx + len_lead_matched
            )

            # Get the part after leading context
            if len(segment_normalized) > len_lead_matched:
                part_after_leading_context = segment_normalized[len_lead_matched:]
                
                # Try to find trailing context by attempting with smaller context each time
                for trailing_len in range(min(len(part_after_leading_context), 5), 0, -1):
                    trailing_context = part_after_leading_context[-trailing_len:]
                    try:
                        original_trailing_match_start_idx, len_trail_matched = _find_unique_context_in_original(
                            original_lines, trailing_context, search_for_trailing_from_idx
                        )
                        # Found a match, set current_original_idx to after the trailing context
                        current_original_idx = original_trailing_match_start_idx + len_trail_matched
                        break
                    except ValueError:
                        # Continue trying with smaller context
                        continue
                else:
                    # No trailing context found after trying all sizes
                    current_original_idx = original_segment_span_start_idx + len_lead_matched
            else:
                # No distinct content after leading context
                current_original_idx = original_segment_span_start_idx + len_lead_matched
                
    return _normalize_lines(result_lines, ensure_trailing_newline=True)


def propose_code_edits(
    target_file_path_str: str,
    user_edit_instructions: str,
    original_file_content_lines: Optional[List[str]] = None
) -> Dict[str, str]:
    """Generates parameters for the `edit_file` function using an LLM.

    Takes high-level user instructions about a desired code change and the
    target file's context (path and optionally content). It prompts an LLM
    to create a structured edit proposal according to specific formatting rules
    (requiring context lines and delimiters like '// ... existing code ...'
    for patching). It then parses the LLM's response to extract the necessary
    arguments for the `edit_file` function.

    Args:
        target_file_path_str (str): Path of the file to edit or create (can be
            relative to current working directory or absolute within workspace).
        user_edit_instructions (str): User's natural language request describing
            the desired code change or file creation task.
        original_file_content_lines (Optional[List[str]]): Current lines of the
            target file if it exists and is being edited. Providing this improves
            accuracy. If None and the file exists in the internal representation,
            its content will be fetched. Defaults to None.
            Example: `['# Example Python\n', 'def hello():\n', '    return "world"\n']`

    Returns:
        Dict[str, str]: A dictionary containing the parameters generated by the LLM,
        ready for use with the `edit_file` function:
            - 'code_edit' (str): The structured edit string with context, changes,
                and delimiters suitable for the patching mechanism.
            - 'instructions' (str): A concise, first-person sentence generated by
                the LLM summarizing the edit action performed in the 'code_edit'.

    Raises:
        ValueError: If `target_file_path_str` or `user_edit_instructions` are empty.
        RuntimeError: If the underlying LLM call fails or returns an unparsable
                      response format (missing separator or required content).
                      Details are logged internally.
    """
    if not target_file_path_str or not user_edit_instructions:
        _log_util_message(logging.ERROR, "Target file path and user edit instructions are required.")
        raise ValueError("Target file path and user edit instructions are required.")

    # Determine current content for the prompt context.
    current_content_str = ""
    if original_file_content_lines is None:
        try:
            abs_path = get_absolute_path(target_file_path_str) 
            entry = DB.get("file_system", {}).get(abs_path)
            if entry and not entry.get("is_directory"):
                original_file_content_lines = entry.get("content_lines", [])
        except ValueError as e: 
            _log_util_message(logging.WARNING, f"Path resolution error for '{target_file_path_str}': {e}. Assuming new file.")
            original_file_content_lines = []
        except Exception as e: 
            _log_util_message(logging.WARNING, f"Could not fetch original content for {target_file_path_str}: {e}. Assuming new file.")
            original_file_content_lines = [] 
            
    if original_file_content_lines:
        current_content_str = "".join(original_file_content_lines)
    else: 
        current_content_str = "# This is a new file or the existing file is empty.\n"

    # --- Construct the Prompt for the LLM ---
    # This prompt details the edit structure required by the apply_code_edit function.
    prompt = f'''You are an expert coding assistant generating code edits for an automated patching tool.
Produce EXACTLY two parts: an "Instructions String" and a "Code Edit String", separated by "----EDIT_SEPARATOR----".

TARGET FILE: {target_file_path_str}
USER REQUEST: "{user_edit_instructions}"
CURRENT CONTENT:
{current_content_str}

REQUIREMENTS FOR THE OUTPUT:

1.  **Instructions String**: Create a single, concise sentence in the first person summarizing the planned edit (e.g., "I will refactor the data validation logic and add a new logging statement.").

2.  **Code Edit String**: Generate the code for the change, adhering strictly to these rules:
    a.  **Delimiters**: Use a standard comment line `// ... existing code ...` (or language-appropriate equivalent like `# ... existing code ...` for Python) on its own line. This delimiter signals that a segment of the original file is being preserved or skipped *between* the code segments you provide. The phrase "... existing code ..." is the key signal within the comment.
       - IMPORTANT: Only use delimiters when you need to skip multiple lines of unchanged code. DO NOT use delimiters between adjacent lines in the original file.
    b.  **Code Segments**: The blocks of text you provide (which are not delimiter lines) are "code segments" containing your changes and their necessary context.
    c.  **Mandatory Context in Code Segments**: EVERY code segment you provide MUST include 1-5 lines of UNCHANGED original code as **leading context** (immediately before your actual new/modified lines within that segment) AND 1-5 lines of UNCHANGED original code as **trailing context** (immediately after your new/modified lines within that segment). This context MUST uniquely match the original file to anchor the edit correctly.
        - For insertions at the very beginning: your first code segment starts with new lines, followed by 1-5 original lines (trailing context for your new block).
        - For appends at the very end: your last code segment ends with new lines, preceded by 1-5 original lines (leading context for your new block).
        - ⚠️ CRITICAL WARNING: DO NOT add ANY explanatory comments to the code segments, such as "# Leading context", "# Trailing context", "# Original line" etc. These will be treated as literal code changes and will BREAK the context matching. 
        - ⚠️ NEVER add comments like "# Trailing context for X" or "# Leading context for Y" in your actual code edits.
        - NEVER use blank lines alone as context since they are not unique. Always include substantive lines of code with actual content as context.
        - CRITICAL: The same lines of code CANNOT be used as both trailing context of one segment and leading context of the next segment. Each segment must have unique, non-overlapping context.
    d.  **Patching Tool Interpretation**: Delimiters control preservation of original lines *between* the spans of your code segments. Your code segments *replace* the original content spanned by their matched leading and trailing context.
    e.  **New Files**: If creating a new file, the `code_edit` string should be the complete desired content of the new file. No delimiters or context from an "original" file are needed.
    f.  **Class Structure**: When modifying classes, be careful to maintain the complete class structure including any class declaration lines. Don't assume parts of the class definition, always start with the class declaration when changing class content.
    g.  **Usage Examples**: Don't modify usage examples or test code unless specifically requested. Focus your edits on the implementation code.
    h.  **Import Dependencies**: When modifying code, carefully check for ALL dependencies in the code (especially in blocks like main execution). If you add new functionality that uses modules (like json, logging), make sure to add those imports. Most critically, PRESERVE ALL EXISTING IMPORTS that are used anywhere in the file, even in parts you aren't directly modifying.
    i.  **Dependency Analysis**: Before submitting your edit, review the entire code to ensure that any function or module referenced in the code (like os.path.join, sys.argv, sys.exit) has corresponding import statements at the top of the file.
    j.  **About Examples**: Note that the examples below contain comments like "# Leading context from original" or "# Original line kept". These are ONLY for explaining the example format to you. DO NOT include such explanatory comments in your actual Code Edit String.

Output Format:
Provide the "Instructions String" first, followed by the exact separator "----EDIT_SEPARATOR----", then the "Code Edit String".

EXAMPLE 1 (Python: Inserting a new function and modifying an existing one):
Assume original file section related to process_data:
```python
# helpers.py
import os
# Some original comment

# Some other code

def process_data(raw_data):
    # Old validation logic here (e.g., checking if raw_data is None or not a string)
    print(f"Processing: {{raw_data}}")
    processed = raw_data.upper()
    print(f"Done with: {{processed}}")
    return processed
# Another function
```
Instructions String: I will add a new `is_valid_input` function before `process_data`, and then update `process_data` to use it.
----EDIT_SEPARATOR----
# ... existing code ...
import os # Leading context for the new function's insertion point

# Adding is_valid_input function
def is_valid_input(data_item):
    if not data_item or not isinstance(data_item, str):
        return False
    return True
# Some original comment # Trailing context for the new function
# ... existing code ...
def process_data(raw_data): # Leading context from original
    if not is_valid_input(raw_data): # New line
        return "Invalid input provided" # New line
    print(f"Processing: {{raw_data}}") # Original line kept. 
    processed = raw_data.lower() + " (processed)" # Modified line
    print(f"Done with: {{processed}}") # Original line, now acts as trailing context.
    return processed # Original line, also trailing context
# ... existing code ...

EXAMPLE 2 (Python: Modifying start of file and a middle function):
Assume original relevant parts:
```python
# main_app.py
import os
import sys

# ... (other code) ...

    # Some preceding comment
    logger.info("Processing data...")
    result = data * 2
    return result
    # Some subsequent comment
# ... (other code) ...
```
Instructions String: I will add `import logging` at the top, and refactor the data processing calculation.
----EDIT_SEPARATOR----
import os          # Preserved existing import
import sys         # Preserved existing import
import logging     # New import added
# ... existing code ...
    # Some preceding comment                      # Leading context from original for second edit
    logger.info("Processing data...")          # Leading context from original
    # Modified logic below
    result = data * config.get('multiplier', 2) # Changed line
    logger.debug(f"Processed result: {{result}}")  # Added line.
    # Some subsequent comment                   # Trailing context from original
# ... existing code ...

Generate the "Instructions String" and "Code Edit String" for the request regarding "{target_file_path_str}" based on the user request "{user_edit_instructions}" and the current content provided earlier:
''' # End of f-string using triple single quotes

    _log_util_message(logging.INFO, f"Requesting code edit proposal for: {target_file_path_str}")
    try:
        raw_llm_response = call_llm(
            prompt_text=prompt,
            temperature=0.2,
            timeout_seconds=300
        )
    except (RuntimeError, ValueError) as e: 
        _log_util_message(logging.ERROR, f"LLM call failed during propose_code_edits for '{target_file_path_str}': {e}", exc_info=False)
        raise 
    
    separator = "----EDIT_SEPARATOR----"
    if separator not in raw_llm_response:
        msg = f"LLM response format error: Separator '{separator}' not found."
        _log_util_message(logging.ERROR, msg + f" Response snippet: {raw_llm_response[:200]}...")
        raise RuntimeError(msg + " LLM did not provide the expected separator.")

    parts = raw_llm_response.split(separator, 1)
    if len(parts) != 2:
        msg = "LLM response format error: Could not split response into two parts."
        _log_util_message(logging.ERROR, msg + f" Response snippet: {raw_llm_response[:200]}...")
        raise RuntimeError(msg)

    instruction_str_prefix = "Instructions String:"
    generated_instructions_raw = parts[0].strip()
    generated_instructions = generated_instructions_raw[len(instruction_str_prefix):].strip()\
        if generated_instructions_raw.lower().startswith(instruction_str_prefix.lower())\
        else generated_instructions_raw

    code_edit_str_prefix = "Code Edit String:"
    generated_code_edit_raw = parts[1].strip()
    generated_code_edit = generated_code_edit_raw[len(code_edit_str_prefix):].strip()\
        if generated_code_edit_raw.lower().startswith(code_edit_str_prefix.lower())\
        else generated_code_edit_raw
    
    if generated_code_edit.startswith("```") and generated_code_edit.endswith("```"):
        code_lines = generated_code_edit.splitlines(keepends=True)
        if len(code_lines) > 1: 
            generated_code_edit = "".join(code_lines[1:-1]).strip()
        else: 
            generated_code_edit = "" 

    if not generated_instructions and not generated_code_edit:
        _log_util_message(logging.WARNING, f"LLM returned empty for both parts for {target_file_path_str}.")
        
    # --- START PREPROCESSING OF generated_code_edit ---
    # This aims to remove AI-generated helper comments like "# Leading context..."
    # or "# Trailing context..." from the code_edit string, as these are not
    # part of the actual file content and can cause context mismatches in utils.apply_code_edit.
    # The 're' module is imported at the top of this file.
    if generated_code_edit: # Only process if there's content
        processed_lines = []
        for line_content in generated_code_edit.splitlines():
            # More robust patterns to catch variations if any
            leading_context_pattern = r'#\s*Leading\s*context.*$'
            trailing_context_pattern = r'#\s*Trailing\s*context.*$'
            original_line_pattern = r'#\s*Original\s*line.*$' # Adding this based on prompt example analysis
            
            temp_line = line_content
            temp_line = re.sub(leading_context_pattern, '', temp_line).rstrip()
            temp_line = re.sub(trailing_context_pattern, '', temp_line).rstrip()
            final_line = re.sub(original_line_pattern, '', temp_line).rstrip()
            
            processed_lines.append(final_line)
        cleaned_generated_code_edit = "\n".join(processed_lines)
    else:
        cleaned_generated_code_edit = generated_code_edit # Keep as is if empty
    # --- END PREPROCESSING OF generated_code_edit ---

    return {
        "instructions": generated_instructions,
        "code_edit": cleaned_generated_code_edit # Return the cleaned version
    }


# --- Search Utilities (DB-Only Operations) ---


def perform_grep_search(
    file_path: str, query_regex: str, case_sensitive: bool = True
) -> list[tuple[int, str]]:
    """
    Performs a regex search on the 'content_lines' of a specified file
    stored in 'DB["file_system"]'.

    Args:
        file_path: The path to the file (within 'DB') to search.
        query_regex: The regular expression pattern.
        case_sensitive: If the search should be case sensitive. Defaults to True.

    Returns:
        A list of tuples (1-indexed line number, matching line content).
        Empty list if file not found, not a file, or no matches.
    """
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        compiled_regex = re.compile(query_regex, flags)
    except re.error as e:
        print_log(f"Invalid regex pattern encountered: {e}")  # Consider proper logging
        return []

    entry = get_file_system_entry(file_path)
    if entry and not entry.get("is_directory", False):
        content_lines = entry.get("content_lines", [])
        for i, line in enumerate(content_lines):
            if compiled_regex.search(line):
                results.append((i + 1, line.rstrip("\n")))
    return results


def _is_path_in_ignored_directory(file_path_str: str, ignored_components: set) -> bool:
    """
    Checks if the file_path_str is within a directory whose name is in ignored_components,
    or if the file_path_str itself (if it's a directory name) is an ignored component.
    e.g., _is_path_in_ignored_directory("/path/to/.git/file.txt", {".git"}) -> True
          _is_path_in_ignored_directory("/path/to/__pycache__/module.pyc", {"__pycache__"}) -> True
          _is_path_in_ignored_directory("/path/to/project/file.py", {".git"}) -> False
          _is_path_in_ignored_directory("/path/to/.git", {".git"}) -> True
    """
    if not isinstance(file_path_str, str):
        logger.warning(f"Invalid file_path_str type for ignore check: {type(file_path_str)}")
        return True # Or False, depending on how you want to treat invalid paths (True means ignore)

    try:
        # Normalize the path to handle mixed separators (e.g., '/' and '\')
        # and to resolve '..' components, making the component check more reliable.
        normalized_path = os.path.normpath(file_path_str) # Don't use abspath here, as we might be checking relative paths during hydration

        path_parts = normalized_path.split(os.sep)
        for part in path_parts:
            if part in ignored_components:
                return True # Found an ignored component in the path

    except Exception as e:
        logger.error(f"Error during path processing for ignore check on '{file_path_str}': {e}", exc_info=False)
        return False # Default to not ignoring if path processing itself fails
    return False


def is_path_excluded_for_search(
    relative_path: str,
    ignore_dirs: set,
    ignore_file_patterns: set
) -> bool:
    """
    Checks if a given relative path should be excluded from search based on
    ignored directory components or filename patterns.

    Args:
        relative_path (str): The path relative to the workspace root.
        ignore_dirs (set): A set of directory names to ignore.
        ignore_file_patterns (set): A set of glob patterns for filenames to ignore.

    Returns:
        bool: True if the path should be ignored, False otherwise.
    """
    # Normalize for consistent component splitting
    normalized_relative_path = os.path.normpath(relative_path)
    path_components = normalized_relative_path.split(os.sep)

    # Check if any directory component in the path is in ignore_dirs
    for component in path_components:
        if component in ignore_dirs:
            return True

    # Check if the filename matches any of the ignore_file_patterns
    filename = os.path.basename(normalized_relative_path)
    for pattern in ignore_file_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True

    return False

# --- Process Management Utilities ---


def get_next_pid() -> int:
    """
    Retrieves the next available Process ID (PID) from 'DB["_next_pid"]'
    and increments the counter for subsequent calls.
    This is typically used for tracking simulated background processes.
    """
    pid = DB.get("_next_pid", 1)  # Default to 1 if not found
    DB["_next_pid"] = pid + 1
    return pid


# --- Globbing Utility ---


def matches_glob_patterns(
    path_to_check: str,
    include_patterns: list[str] = None,
    exclude_patterns: list[str] = None,
) -> bool:
    """
    Checks if a given path string matches a list of include glob patterns and
    does not match any from a list of exclude glob patterns.
    Patterns can match the full path string or its basename.

    Args:
        path_to_check: The path string to check. This string is used directly
                       for matching against the glob patterns.
        include_patterns: Glob patterns for inclusion.
        exclude_patterns: Glob patterns for exclusion.

    Returns:
        True if the path should be included, False otherwise.
    """
    # For globbing, we typically match against the path string as is,
    # or its basename, rather than a fully resolved filesystem path.
    # Normalization here is for consistent string comparison if patterns might have odd slashes.
    path_for_match = os.path.normpath(path_to_check)
    base_name = os.path.basename(path_for_match)

    if exclude_patterns:
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(path_for_match, pattern) or fnmatch.fnmatch(
                base_name, pattern
            ):
                return False

    if (
        include_patterns
    ):  # If include_patterns is an empty list, it means "match nothing" if this condition is active.
        is_included = False
        for pattern in include_patterns:
            if fnmatch.fnmatch(path_for_match, pattern) or fnmatch.fnmatch(
                base_name, pattern
            ):
                is_included = True
                break
        if not is_included:
            return False
    # If include_patterns is None (not provided), or if it was provided and matched (and not excluded):
    return True


def is_likely_binary_file(filepath, sample_size=1024):
    """
    Heuristic to guess if a file is binary.
    Checks for a significant number of null bytes or non-printable characters
    in a sample of the file. Also uses mimetypes.

    Args:
        filepath (str): Path to the file.
        sample_size (int): Number of bytes to sample from the beginning of the file.

    Returns:
        bool: True if the file is likely binary, False otherwise.
    """
    # Guess MIME type first, as it's often more reliable for known types
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type:
        # Explicitly non-text types
        if not mime_type.startswith("text/") and mime_type not in (
            "application/json",
            "application/xml",
            "application/javascript",
            "application/x-sh",
            "application/x-python",
        ):  # Add other text-based app types
            # Consider 'inode/x-empty' as not binary for content loading
            if mime_type == "inode/x-empty":
                return False
            # application/octet-stream is a strong indicator of binary
            if mime_type == "application/octet-stream":
                return True
            # If it's a known non-text type (e.g. image, audio, video, common binary app types)
            # This helps with .zip, .exe, .pdf, .png etc.
            return True

    # Content-based heuristic (fallback or for ambiguous MIME types)
    try:
        with open(filepath, "rb") as f:
            sample = f.read(sample_size)
        if not sample:  # Empty file is not considered binary for content loading
            return False

        # Presence of null bytes is a strong indicator for many binary formats
        if b"\0" in sample:
            # A simple check for any null byte can be effective
            return True

        # Check for a high proportion of non-printable ASCII characters
        # (excluding common whitespace like tab, newline, carriage return)
        text_characters = "".join(map(chr, range(32, 127))) + "\n\r\t"
        non_printable_count = 0
        for byte_val in sample:  # Iterate over byte values (integers)
            if chr(byte_val) not in text_characters:
                non_printable_count += 1

        # If more than a certain percentage of characters are non-printable
        # This threshold might need tuning.
        if (
            len(sample) > 0 and (non_printable_count / len(sample)) > 0.30
        ):  # 30% non-printable
            logger.debug(
                f"File '{filepath}' deemed binary by content heuristic (non-printable ratio: {non_printable_count / len(sample):.2f})"
            )
            return True

    except (IOError, OSError) as e:
        # If we can't read it for heuristic, log it but don't assume binary.
        # The main read attempt in hydrate_db_from_directory will handle and log the read error.
        logger.debug(
            f"Could not perform content-based binary check for '{filepath}': {e}"
        )
        return False  # Default to not binary if heuristic check fails to read
    return False


def hydrate_db_from_directory(db_instance, directory_path):
    """
    Populates the provided db_instance's 'file_system' by recursively scanning
    a local directory structure. It sets the 'workspace_root' and 'cwd'
    to the normalized path of the scanned directory.

    Args:
        db_instance (dict): The application's database, modified in place.
        directory_path (str): Path to the root directory for hydration.

    Returns:
        bool: True if hydration completed successfully.

    Raises:
        FileNotFoundError: If `directory_path` does not exist or is not a directory.
        RuntimeError: For fatal, unrecoverable errors during hydration.
    """
    try:
        # Validate and Normalize Root Directory Path
        if not os.path.isdir(directory_path):
            msg = f"Root directory for hydration not found or is not a directory: '{directory_path}'"
            logger.error(msg)
            raise FileNotFoundError(msg)

        normalized_root_path = os.path.abspath(directory_path).replace("\\", "/")

        # Update Core DB Properties
        db_instance["workspace_root"] = normalized_root_path
        db_instance["cwd"] = normalized_root_path # Default CWD to workspace root

        # Prepare file_system for New Data
        db_instance["file_system"] = {}

        logger.info(f"Starting hydration from workspace root: {normalized_root_path}")

        # Recursively Scan Directory Structure
        for dirpath, dirnames, filenames in os.walk(directory_path, topdown=True, onerror=logger.warning):
            current_normalized_dirpath = os.path.abspath(dirpath).replace("\\", "/")
            

            logger.debug(f"Processing directory for DB entry: {current_normalized_dirpath}")

            # Process the Current Directory (dirpath) Itself
            # Add current_normalized_dirpath to DB if it hasn't been added (os.walk might yield it multiple times if symlinks involved, though less common here)
            # and it's not an ignored component (already checked above for skipping).
            if current_normalized_dirpath not in db_instance["file_system"]:
                try:
                    mtime_timestamp = os.path.getmtime(dirpath)
                    last_modified_iso = datetime.datetime.fromtimestamp(
                        mtime_timestamp, tz=datetime.timezone.utc
                    ).isoformat().replace("+00:00", "Z")

                    db_instance["file_system"][current_normalized_dirpath] = {
                        "path": current_normalized_dirpath,
                        "is_directory": True,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": last_modified_iso,
                    }
                    logger.debug(f"Added directory entry to DB: {current_normalized_dirpath}")
                except Exception as e:
                    logger.warning(
                        f"Could not process directory metadata for '{current_normalized_dirpath}': {e}"
                    )
                    continue

            # Process Files (filenames) in the Current Directory
            for filename in filenames:
                file_full_path = os.path.join(dirpath, filename)
                normalized_file_path = os.path.abspath(file_full_path).replace("\\", "/")

                logger.debug(f"Processing file for DB entry: {normalized_file_path}")

                content_lines = ERROR_READING_CONTENT_PLACEHOLDER
                size_bytes = 0
                last_modified_iso = get_current_timestamp_iso() # Default

                try:
                    stat_info = os.stat(file_full_path)
                    size_bytes = stat_info.st_size
                    mtime_timestamp = stat_info.st_mtime
                    last_modified_iso = datetime.datetime.fromtimestamp(
                        mtime_timestamp, tz=datetime.timezone.utc
                    ).isoformat().replace("+00:00", "Z")

                    if size_bytes == 0: # Handle empty files explicitly
                        content_lines = []
                        logger.debug(f"File '{normalized_file_path}' is empty. Content set to [].")
                    elif size_bytes > MAX_FILE_SIZE_BYTES:
                        logger.info(
                            f"File '{normalized_file_path}' ({size_bytes / (1024*1024):.2f}MB) exceeds max size {MAX_FILE_SIZE_TO_LOAD_CONTENT_MB}MB. Content not loaded."
                        )
                        content_lines = LARGE_FILE_CONTENT_PLACEHOLDER
                    elif is_likely_binary_file(file_full_path): # Pass full_path for mimetype guessing
                        logger.info(
                            f"File '{normalized_file_path}' detected as binary. Content not loaded."
                        )
                        content_lines = BINARY_CONTENT_PLACEHOLDER
                    else:
                        encodings_to_try = ["utf-8", "latin-1", "cp1252"]
                        read_success = False
                        for encoding in encodings_to_try:
                            try:
                                with open(file_full_path, "r", encoding=encoding) as f:
                                    content_lines = f.readlines() # Read all lines
                                read_success = True
                                logger.debug(
                                    f"Successfully read '{normalized_file_path}' with encoding '{encoding}'."
                                )
                                break
                            except UnicodeDecodeError:
                                logger.debug(
                                    f"Failed to decode '{normalized_file_path}' with encoding '{encoding}'. Trying next."
                                )
                            except Exception as e_read: # Catch other read errors like PermissionError here
                                logger.warning(
                                    f"Could not read file '{normalized_file_path}' with encoding '{encoding}': {e_read}"
                                )
                                content_lines = [
                                    f"Error: Could not read file content. Reason: {type(e_read).__name__}\n"
                                ]
                                break # Stop trying other encodings if a fundamental read error occurs

                        if not read_success and content_lines == ERROR_READING_CONTENT_PLACEHOLDER: # If all decodes failed
                            logger.warning(
                                f"Could not decode file '{normalized_file_path}' with any of the tried encodings ({', '.join(encodings_to_try)})."
                            )
                            content_lines = [
                                f"Error: Could not decode file content with attempted encodings.\n"
                            ]

                    db_instance["file_system"][normalized_file_path] = {
                        "path": normalized_file_path,
                        "is_directory": False,
                        "content_lines": content_lines,
                        "size_bytes": size_bytes,
                        "last_modified": last_modified_iso,
                    }
                    logger.debug(f"Added file entry to DB: {normalized_file_path}")

                except FileNotFoundError: # Should be rare if os.walk yielded it, but good for robustness
                    logger.warning(
                        f"File '{normalized_file_path}' was not found during scan (possibly deleted concurrently). Skipping."
                    )
                except PermissionError as pe:
                    logger.warning(
                        f"Permission denied for accessing file '{normalized_file_path}': {pe}. Storing with minimal info."
                    )
                    db_instance["file_system"][normalized_file_path] = {
                        "path": normalized_file_path, "is_directory": False,
                        "content_lines": [f"Error: Permission denied to read file content.\n"],
                        "size_bytes": 0, "last_modified": get_current_timestamp_iso(), # Use current time as fallback
                    }
                except Exception as e:
                    logger.warning(
                        f"An unexpected error occurred while processing file '{normalized_file_path}': {e}. Storing with minimal info."
                    )
                    db_instance["file_system"][normalized_file_path] = {
                        "path": normalized_file_path, "is_directory": False,
                        "content_lines": [f"Error: Could not process file due to an unexpected error: {type(e).__name__}\n"],
                        "size_bytes": 0, "last_modified": get_current_timestamp_iso(),
                    }

        logger.info(
            f"Hydration complete. Total items in file_system: {len(db_instance['file_system'])}"
        )
        return True

    except FileNotFoundError:
        raise # Re-raise if it's from the root directory check
    except Exception as e:
        msg = f"Fatal error during DB hydration process: {e}"
        logger.critical(msg, exc_info=True)
        db_instance["workspace_root"] = ""
        db_instance["cwd"] = ""
        db_instance["file_system"] = {}
        raise RuntimeError(msg) from e  


def _normalize_path_for_db(path_str: str) -> str:
    if path_str is None:
        return None
    return os.path.normpath(path_str).replace("\\", "/")


def resolve_target_path_for_cd(current_cwd_abs: str, 
                               target_arg: str, 
                               workspace_root_abs: str,
                               file_system_view: Dict[str, Any]) -> Optional[str]:
    """
    Resolves and validates a target path for 'cd'.
    All input paths (current_cwd_abs, workspace_root_abs) should be absolute and normalized.
    target_arg can be relative or absolute (interpreted relative to workspace_root if starting with '/').
    """
    # Normalize inputs (assuming they are already absolute where specified)
    current_cwd_abs = _normalize_path_for_db(current_cwd_abs)
    workspace_root_abs = _normalize_path_for_db(workspace_root_abs)
    target_arg_normalized = _normalize_path_for_db(target_arg) # Normalize arg itself

    if target_arg_normalized.startswith("/"):
        # Path is absolute relative to workspace_root
        # e.g., if workspace_root is C:/ws and target_arg is /foo, new_path is C:/ws/foo
        prospective_path = _normalize_path_for_db(os.path.join(workspace_root_abs, target_arg_normalized.lstrip('/')))
    elif ":" in target_arg_normalized and os.path.isabs(target_arg_normalized): # Full OS path like C:/...
        # If a full OS path is given, it must be within the workspace
        prospective_path = target_arg_normalized
    else:
        # Path is relative to current_cwd_abs
        prospective_path = _normalize_path_for_db(os.path.join(current_cwd_abs, target_arg_normalized))
    
    # Final normalization (e.g., resolves '..', '.', multiple slashes)
    resolved_path_abs = _normalize_path_for_db(os.path.normpath(prospective_path))

    # Validation:
    # 1. Must be within or same as workspace_root
    #    A simple check is that resolved_path_abs must start with workspace_root_abs.
    #    And commonpath should be workspace_root_abs unless resolved_path_abs is workspace_root_abs.
    if not resolved_path_abs.startswith(workspace_root_abs):
        # Check if it went "above" root. e.g. root C:/a/b, resolved C:/a
        # This can happen if workspace_root_abs itself is a/b and resolved path is just a
        # A more robust check involves ensuring original_root is a prefix of new_path
        if workspace_root_abs != resolved_path_abs and not _normalize_path_for_db(os.path.commonpath([workspace_root_abs, resolved_path_abs])) == workspace_root_abs :
            _log_util_message(logging.WARNING, f"cd: Attempt to navigate outside workspace root. Target: '{resolved_path_abs}', Root: '{workspace_root_abs}'")
            return None # Path is outside workspace

    # 2. Must exist in file_system_view and be a directory
    if resolved_path_abs in file_system_view and\
       file_system_view[resolved_path_abs].get("is_directory", False):
        return resolved_path_abs
    else:
        _log_util_message(logging.WARNING, f"cd: Target path '{resolved_path_abs}' is not a valid directory in the DB.")
        return None


def map_temp_path_to_db_key(temp_path: str, temp_root: str, desired_logical_root: str) -> Optional[str]:
    # Normalize physical temporary paths
    normalized_temp_path = _normalize_path_for_db(os.path.abspath(temp_path))
    normalized_temp_root = _normalize_path_for_db(os.path.abspath(temp_root))

    # desired_logical_root is the intended base (e.g., "/test_workspace")
    # Ensure it's also in a canonical form using _normalize_path_for_db
    # This does NOT make it OS-absolute.
    normalized_desired_logical_root = _normalize_path_for_db(desired_logical_root)

    if not normalized_temp_path.startswith(normalized_temp_root):
        _log_util_message(logging.DEBUG, f"Debug map_key: Temp path '{normalized_temp_path}' is not under temp root '{normalized_temp_root}'.")
        return None

    if normalized_temp_path == normalized_temp_root:
        return normalized_desired_logical_root # Path is the root itself

    relative_path = os.path.relpath(normalized_temp_path, normalized_temp_root)

    # If relpath is '.', it means temp_path and temp_root are the same directory.
    if relative_path == '.': 
        return normalized_desired_logical_root

    # Join the desired logical root with the relative path from the temp structure
    final_logical_path = _normalize_path_for_db(os.path.join(normalized_desired_logical_root, relative_path))

    # Hierarchical sanity check:
    # The final_logical_path should start with normalized_desired_logical_root (unless root is just "/")
    # or be equal to it.
    if final_logical_path == normalized_desired_logical_root:
        # This happens if relative_path was effectively empty or "."
        return final_logical_path

    # For non-root logical roots, ensure it starts with "root/"
    # For root ("/"), any absolute path (starting with "/") is fine.
    expected_prefix = normalized_desired_logical_root
    if expected_prefix != "/" and not expected_prefix.endswith("/"):
        expected_prefix += "/"

    if not final_logical_path.startswith(expected_prefix) and final_logical_path != normalized_desired_logical_root :
         # This handles cases like desired_logical_root="/foo", final_logical_path="/foobar" (not under /foo/)
         # or desired_logical_root="/", final_logical_path="bar" (not absolute) - though join should prevent this.
        _log_util_message(logging.ERROR, f"Constructed logical path '{final_logical_path}' "
                                         f"is not hierarchically under desired logical root '{normalized_desired_logical_root}' "
                                         f"(expected prefix '{expected_prefix}'). Relative path was: '{relative_path}'.")
        return None

    return final_logical_path


# --- Dehydrate Function ---
def dehydrate_db_to_directory(db: Dict[str, Any], target_dir: str) -> bool:
    """Writes workspace file system content to a specified target directory.

    Recreates the directory and file structure from the provided 'db' state
    into 'target_dir'. This function also updates the 'workspace_root' and 'cwd'
    in the 'db' object to reflect this new target directory.

    Args:
        db: The database dictionary containing 'workspace_root' and 'file_system'.
            This dictionary is modified in-place.
        target_dir: The path to the directory where the file system content
                    will be written. It will be created if it doesn't exist.

    Returns:
        True if the process completes successfully.

    Raises:
        ValueError: If 'db' is missing 'workspace_root'.
        OSError: If there are issues creating directories or writing files.
        Exception: For other unexpected errors during the process.
    """
    old_root = db.get("workspace_root")
    if not old_root:
        raise ValueError("DB missing 'workspace_root' for dehydration.")

    new_root = os.path.abspath(target_dir).replace("\\", "/") # Standardize new root path
    file_system = db.get("file_system", {})
    new_file_system = {} # To store updated paths for the DB

    _log_util_message(logging.INFO, f"Writing workspace state to disk: {new_root}")

    try:
        os.makedirs(new_root, exist_ok=True) # Create target root if needed

        for old_path, entry in file_system.items():
            # Determine relative path from old root to map to new root
            if old_path == old_root:
                rel_path = '.'
            else:
                 try:
                      rel_path = os.path.relpath(old_path, old_root)
                 except ValueError as e:
                      # Log if a path doesn't seem to belong to the old root
                      _log_util_message(logging.ERROR, f"Path '{old_path}' not relative to workspace root '{old_root}': {e}")
                      continue

            new_path = os.path.normpath(os.path.join(new_root, rel_path)).replace("\\", "/")

            # Prepare new entry for the DB reflecting the new physical path
            new_entry_state = entry.copy()
            new_entry_state["path"] = new_path
            new_file_system[new_path] = new_entry_state

            try:
                if new_entry_state.get("is_directory", False):
                    os.makedirs(new_path, exist_ok=True) # Create directory
                else:
                    # Create parent directory for the file if it doesn't exist
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    content_to_write = entry.get("content_lines", [])

                    # Handle placeholder content without modification
                    if (content_to_write is BINARY_CONTENT_PLACEHOLDER or
                        content_to_write is LARGE_FILE_CONTENT_PLACEHOLDER or
                        content_to_write is ERROR_READING_CONTENT_PLACEHOLDER):
                        _log_util_message(logging.DEBUG, f"Writing placeholder for {old_path} to {new_path}")
                        with open(new_path, "w", encoding="utf-8") as f:
                            f.writelines(content_to_write) # Write placeholder as is
                    else:
                        # For normal text content, ensure lines are properly terminated
                        # This preserves distinct lines when written to the physical file.
                        normalized_content = _normalize_lines(content_to_write, ensure_trailing_newline=True)
                        with open(new_path, "w", encoding="utf-8") as f:
                             f.writelines(normalized_content)

            except OSError as e:
                _log_util_message(logging.ERROR, f"OS error writing to {new_path}: {e}", exc_info=True)
                raise # Re-raise OS errors
            except Exception as e:
                _log_util_message(logging.ERROR, f"Unexpected error writing {new_path}: {e}", exc_info=True)
                raise # Re-raise other unexpected errors

        # Update the DB object to reflect the new physical location
        db["workspace_root"] = new_root
        db["cwd"] = new_root # Assume CWD moves with the root for this operation
        db["file_system"] = new_file_system
        _log_util_message(logging.INFO, f"Workspace state successfully written to {new_root}")

        return True

    except (ValueError, OSError, Exception) as e:
        # Log any failure during the overall process
        _log_util_message(logging.ERROR, f"Failed to write workspace state to disk: {e}", exc_info=True)
        raise e # Re-raise the caught exception


# --- Update Function (Wrapper matching cursor's pattern) ---
def update_db_file_system_from_temp(
        temp_root: str,
        original_state: Dict,
        workspace_root: str,
        preserve_metadata: bool = True,
        command: str = ""
    ):
    return common_utils.update_db_file_system_from_temp(
        DB,
        temp_root,
        original_state,
        workspace_root,
        preserve_metadata,
        command
    )

def _update_db_file_system_from_temp_legacy(temp_dir_path: str,
                                   original_file_system_state: Dict[str, Any],
                                   intended_logical_db_root: str):
    global DB # Assuming DB is a global or accessible module-level variable

    _log_util_message(logging.INFO, f"Updating internal state from temp dir '{temp_dir_path}' to reflect intended logical root '{intended_logical_db_root}'")

    try: # Start of the main try block
        final_logical_root_for_db = _normalize_path_for_db(intended_logical_db_root)
        normalized_temp_root = _normalize_path_for_db(os.path.abspath(temp_dir_path))

        new_file_system = {}
        processed_paths = set()

        for current_fs_root, dirs, files in os.walk(normalized_temp_root, topdown=True):
            current_physical_dir_path = _normalize_path_for_db(os.path.abspath(current_fs_root))
            
            dir_db_key_path = map_temp_path_to_db_key(current_physical_dir_path,
                                                      normalized_temp_root,
                                                      final_logical_root_for_db)

            if dir_db_key_path is None:
                _log_util_message(logging.WARNING, f"Could not map directory temp path '{current_physical_dir_path}' to a logical DB key during DB update.")
                continue

            if dir_db_key_path not in processed_paths:
                old_dir_entry = original_file_system_state.get(dir_db_key_path, {})
                last_modified_val = old_dir_entry.get("last_modified", get_current_timestamp_iso()) # Reuse if possible

                new_file_system[dir_db_key_path] = {
                    "path": dir_db_key_path,
                    "is_directory": True,
                    "content_lines": [], # Directories don't have content lines
                    "size_bytes": 0,     # Directories usually have 0 size in this model
                    "last_modified": last_modified_val
                }
                processed_paths.add(dir_db_key_path)

            for fname in files:
                temp_file_full_path = os.path.join(current_fs_root, fname) # Physical path to the file in temp dir
                file_physical_path = _normalize_path_for_db(os.path.abspath(temp_file_full_path))
                
                file_db_key_path = map_temp_path_to_db_key(file_physical_path,
                                                           normalized_temp_root,
                                                           final_logical_root_for_db)

                if file_db_key_path is None:
                    _log_util_message(logging.WARNING, f"Could not map file temp path '{file_physical_path}' to a logical DB key during DB update.")
                    continue
                
                if file_db_key_path in processed_paths: # Should not happen if logic is correct, but a safeguard.
                    _log_util_message(logging.WARNING, f"File path '{file_db_key_path}' already processed. Skipping duplicate.")
                    continue

                content_lines = ERROR_READING_CONTENT_PLACEHOLDER
                size_bytes = 0
                last_modified = get_current_timestamp_iso() # Default

                try:
                    stat_info = os.stat(temp_file_full_path)
                    size_bytes = stat_info.st_size
                    last_modified = datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")

                    # Reuse old content_lines and metadata if file is unchanged (optional optimization)
                    # For simplicity here, we always re-read, but you could compare with original_file_system_state.get(file_db_key_path)
                    
                    if size_bytes == 0:
                        content_lines = []
                    elif size_bytes > MAX_FILE_SIZE_BYTES: # MAX_FILE_SIZE_BYTES needs to be defined/imported
                        content_lines = LARGE_FILE_CONTENT_PLACEHOLDER # Needs to be defined/imported
                        _log_util_message(logging.INFO, f"File '{file_db_key_path}' too large ({size_bytes} bytes), using placeholder.")
                    elif is_likely_binary_file(temp_file_full_path): # is_likely_binary_file needs to be defined/imported
                        content_lines = BINARY_CONTENT_PLACEHOLDER # Needs to be defined/imported
                        _log_util_message(logging.INFO, f"File '{file_db_key_path}' detected as binary, using placeholder.")
                    else:
                        # Attempt to read with multiple encodings if necessary, similar to hydrate_db_from_directory
                        read_success = False
                        encodings_to_try = ["utf-8", "latin-1", "cp1252"]
                        for encoding in encodings_to_try:
                            try:
                                with open(temp_file_full_path, "r", encoding=encoding) as f:
                                    content_lines = f.readlines()
                                read_success = True
                                break
                            except UnicodeDecodeError:
                                continue # Try next encoding
                            except Exception as e_read_enc: # More specific read errors
                                _log_util_message(logging.WARNING, f"Error reading file '{temp_file_full_path}' with encoding '{encoding}': {e_read_enc}")
                                content_lines = [f"<Error reading file: {type(e_read_enc).__name__}>"]
                                break # Stop trying other encodings
                        if not read_success and content_lines == ERROR_READING_CONTENT_PLACEHOLDER: # If all decodes failed
                             content_lines = [f"<Error: Could not decode file content with attempted encodings.>"]


                except FileNotFoundError:
                    _log_util_message(logging.WARNING, f"File '{temp_file_full_path}' not found during DB update (deleted concurrently?).")
                    content_lines = [f"<Error: File not found during update>"] # Or skip adding it
                except Exception as e_stat:
                    _log_util_message(logging.ERROR, f"Error stating or reading file '{temp_file_full_path}': {e_stat}")
                    content_lines = [f"<Error processing file: {type(e_stat).__name__}>"]

                new_file_system[file_db_key_path] = {
                    "path": file_db_key_path,
                    "is_directory": False,
                    "content_lines": content_lines,
                    "size_bytes": size_bytes,
                    "last_modified": last_modified
                }
                processed_paths.add(file_db_key_path)
        
        # Logic for handling deleted files/directories:
        # Paths in original_file_system_state that are NOT in processed_paths were deleted.
        # new_file_system now contains all existing items.
        original_logical_paths = set(original_file_system_state.keys())
        current_logical_paths_found = processed_paths # More accurate than new_file_system.keys() before assignment
        
        paths_implicitly_deleted = original_logical_paths - current_logical_paths_found
        if paths_implicitly_deleted:
            _log_util_message(logging.INFO, f"Paths removed during command execution: {paths_implicitly_deleted}")

        DB["workspace_root"] = final_logical_root_for_db
        
        # CWD handling (relying on run_terminal_cmd's finally block for most precise restoration)
        # For safety, ensure CWD is at least within the new logical root if it's somehow very off.
        current_logical_cwd = _normalize_path_for_db(DB.get("cwd", final_logical_root_for_db))
        if not current_logical_cwd.startswith(final_logical_root_for_db) and current_logical_cwd != final_logical_root_for_db :
            if final_logical_root_for_db == "/" and current_logical_cwd.startswith("/"): # If root is / and CWD is absolute, it's fine
                pass
            else:
                DB["cwd"] = final_logical_root_for_db # Reset to root if CWD seems invalid relative to new root.
        
        DB["file_system"] = new_file_system

        _log_util_message(logging.INFO, f"Internal state (global DB) updated from temp dir '{temp_dir_path}'. New logical root: '{final_logical_root_for_db}'. Items: {len(new_file_system)}.")

    except Exception as e: # This is the except for the main try block
        _log_util_message(logging.ERROR, f"Update process failed in update_db_file_system_from_temp: {e}", exc_info=True)
        # Depending on desired behavior, you might want to restore DB to a known safe state
        # or re-raise the exception. For now, re-raising.
        raise


def add_line_numbers(content: List[str], start: int = 1) -> List[str]:
    """
    Adds line numbers to each line in a list of code strings, starting from a specified number.
    Args:
        content (List[str]): The list of code lines (each as a string).
        start (int, optional): The starting line number. Defaults to 1.
    Returns:
        List[str]: A new list where each line is prefixed with its line number,
                   preserving indentation and newlines.
    """
    return [f"{i}: {line}" for i, line in enumerate(content, start=start)]


def propose_command(user_objective: str) -> Dict[str, Union[str, bool]]:
    """Proposes a terminal command based on a natural language objective.

    Uses an LLM to generate a likely terminal command, an explanation, and
    a suggestion for background execution, based on the provided objective
    and the current working directory context.

    Args:
        user_objective (str): A natural language description of the desired
                              terminal command's goal.

    Returns:
        Dict[str, Union[str, bool]]: A dictionary containing the proposed command details:
            - 'command' (str): The suggested terminal command string.
            - 'explanation' (str): A brief explanation of the command's purpose.
            - 'is_background' (bool): True if the command is suggested to run
                                       in the background, False otherwise.
            Returns a dictionary with default/error values if LLM call or parsing fails.

    Raises:
        RuntimeError: If the underlying LLM call fails or returns an unparsable response.
                     (This is caught internally and reflected in the return dict).
        ValueError: If the necessary LLM configuration (e.g., API key) is missing.
                     (This is caught internally and reflected in the return dict).
    """
    # Default return structure in case of errors
    error_result = {
        "command": "",
        "explanation": "Failed to generate command.",
        "is_background": False
    }

    try:
        current_cwd = DB.get("cwd", DB.get("workspace_root", "/"))
        workspace_root = DB.get("workspace_root", "/")

        # Construct the prompt for the LLM
        # Using a specific separator for more robust parsing than JSON.
        prompt = f"""You are an expert assistant generating Linux/POSIX terminal commands.
Given the user's objective and current context, generate a single, safe, and effective terminal command.

User Objective: "{user_objective}"
Current Working Directory: "{current_cwd}"
Workspace Root: "{workspace_root}"

Guidelines:
- Ensure the command is appropriate for a standard Linux/POSIX environment.
- Prioritize safety. Avoid destructive commands (like rm -rf) unless the objective explicitly and clearly implies it.
- If the command is interactive or uses a pager (like git diff, less, head, tail, more, viewing logs), append `| cat` to ensure it runs non-interactively.
- If the command seems long-running (like a watch process, server, or build task), suggest running it in the background.
- The generated command string MUST NOT contain any newline characters.

Output Format (exactly three lines separated by '----CMD_SEPARATOR----'):
1. Explanation String: A single concise sentence explaining the command.
----CMD_SEPARATOR----
2. Command String: The proposed command, on a single line.
----CMD_SEPARATOR----
3. Is Background: The word 'true' if background execution is recommended, otherwise 'false'.

Generate the response now:
"""

        _log_util_message(logging.INFO, f"Requesting command proposal for objective: {user_objective}")
        raw_llm_response = call_llm(
            prompt_text=prompt,
            temperature=0.3, # Slightly higher temp for command generation might be okay
            timeout_seconds=60  # Reasonable timeout for command generation
        )

        if not raw_llm_response:
            _log_util_message(logging.ERROR, "LLM returned an empty response for command proposal.")
            error_result["explanation"] = "LLM returned empty response."
            return error_result

        # Parse the response using the separator
        separator = "----CMD_SEPARATOR----"
        parts = raw_llm_response.strip().split(separator)

        if len(parts) != 3:
            msg = f"LLM response format error: Expected 3 parts separated by '{separator}', but got {len(parts)}."
            _log_util_message(logging.ERROR, msg + f" Response: {raw_llm_response[:200]}...")
            error_result["explanation"] = "LLM response format error."
            return error_result

        explanation_str = parts[0].strip()
        command_str = parts[1].strip() # Command should already be single line per prompt
        is_background_str = parts[2].strip().lower()

        # Validate and clean the command string (remove potential residual newlines just in case)
        command_str = command_str.replace('\n', ' ').replace('\r', '')

        if not command_str:
             _log_util_message(logging.WARNING, "LLM proposed an empty command string.")
             error_result["explanation"] = "LLM proposed an empty command."
             # Keep the explanation from the LLM if available
             if explanation_str: error_result["explanation"] += f" (LLM explanation: {explanation_str})"
             return error_result


        # Convert is_background string to boolean
        is_background_bool = is_background_str == 'true'
        if is_background_str not in ['true', 'false']:
            _log_util_message(logging.WARNING, f"LLM returned invalid value for 'Is Background': '{parts[2].strip()}'. Defaulting to False.")
            # Keep is_background_bool as False (default)

        _log_util_message(logging.INFO, f"Proposed command: '{command_str}', Background: {is_background_bool}")
        return {
            "command": command_str,
            "explanation": explanation_str,
            "is_background": is_background_bool
        }

    except (ValueError, RuntimeError) as e:
        # Catch errors from call_llm (e.g., API key missing, API errors)
        _log_util_message(logging.ERROR, f"Failed to propose command due to LLM interface error: {e}")
        error_result["explanation"] = f"Failed to propose command: {e}"
        return error_result
    except Exception as e:
        # Catch any other unexpected errors
        _log_util_message(logging.ERROR, f"Unexpected error during propose_command: {type(e).__name__} - {e}", exc_info=True)
        error_result["explanation"] = f"An unexpected internal error occurred: {e}"
        return error_result


def assess_sufficiency(content: List[str], summary: str, user_instructions: str) -> Dict[str, Any]:
    """
    Analyzes if the provided content is sufficient to apply the user instructions,
    taking into account any additional context from the summary but does not actually apply those instructions/modifications.

    This function uses an LLM to determine if the content contains all necessary
    information to implement the requested changes. It considers both the direct
    content and any relevant context from the summary to make this assessment.

    Args:
        content (List[str]): The list of code lines to be analyzed for sufficiency.
        summary (str): Additional context or summary that might be relevant to the content.
        user_instructions (str): The user's requested changes or instructions to be applied.

    Returns:
        dict: A response containing:
            - is_content_sufficient (bool): Whether the content has sufficiency.
            - description (str): The brief description/reason if the content is not sufficient.

    Note:
        The function uses the LLM to make an informed decision about content sufficiency,
        considering both the direct content and any relevant context from the summary.
    """
    prompt = f"""You are an expert code analyzer. Your task is to determine if the provided content is sufficient to implement the requested changes.

    CONTENT TO ANALYZE:
    {content}
    
    ADDITIONAL CONTEXT/SUMMARY:
    {summary}
    
    USER INSTRUCTIONS:
    {user_instructions}
    
    Please analyze if the content is sufficient to implement the requested changes. Consider:
    1. Does the content contain all necessary code sections that need to be modified?
    2. Are there any dependencies or related code sections that the content should have to implement the user instructions but it is missing?
    3. Is there enough context in the content to understand the code structure and make the requested changes?
    
    Respond with EXACTLY one word: "SUFFICIENT" if the content is enough to implement the changes, or "INSUFFICIENT" along with the brief reason that why the content is insufficient.
    """

    try:
        response = call_llm(prompt_text=prompt)
        is_sufficient = response.strip().upper() == "SUFFICIENT"
        description = '' if is_sufficient else response.split(':')[-1].strip()
        return {
            'is_content_sufficient': is_sufficient,
            'description': description
        }
    except Exception as e:
        _log_util_message(logging.ERROR, f"Error in assess_sufficiency: {e}")
        return {
            'is_content_sufficient': False,
            'description': ''
        }  # Default to insufficient if there's an error


# Helper function to split a string by commas that are not inside nested braces
def _split_comma_outside_braces(s: str) -> List[str]:
    """
    Splits a string by commas, but only if the commas are not enclosed in matching braces.
    This is used to parse the options string within a brace expression.

    Args:
        s (str): The string segment from within a pair of braces.
                 Example: "a,b{c,d},e"

    Returns:
        List[str]: A list of option strings.
                   Example: ["a", "b{c,d}", "e"]
                   Handles empty parts for inputs like "a,,b" -> ["a", "", "b"].
    """
    parts: List[str] = []
    if not s and s != "": # If s is None, though type hint is str. Defensive.
        return []
    # If s is an empty string (e.g. from an option like {opt1,,opt3}),
    # current_segment will remain "" and be appended.

    current_segment = ""
    brace_level = 0
    for char in s:
        if char == ',' and brace_level == 0:
            parts.append(current_segment)
            current_segment = ""
        else:
            current_segment += char
            if char == '{':
                brace_level += 1
            elif char == '}':
                if brace_level > 0: # Only decrement if we are inside braces
                    brace_level -= 1
    parts.append(current_segment) # Add the last segment
    return parts

def _expand_braces_glob_pattern(pattern: str) -> List[str]:
    """
    Expands a glob pattern string with brace expressions {opt1,opt2,...},
    supporting multiple and simple nested brace sets recursively.

    Examples:
        - "**/src/{foo,bar}/*.{js,ts}" expands to:
          ["**/src/foo/*.js", "**/src/foo/*.ts", "**/src/bar/*.js", "**/src/bar/*.ts"]
        - "a{b,c{d,e}}f" expands to:
          ["abf", "acdf", "acef"]
        - "a{b,c{d,e}{f,g}}h" expands to:
          ["abh", "acdfh", "acdgh", "acefh", "acegh"]
        - "{a,b}{c,d}" expands to:
          ["ac", "ad", "bc", "bd"]
        - "foo{,bar}" expands to (empty option is preserved):
          ["foo", "foobar"]
        - "foo{}" (empty braces) is treated as literal "foo{}" as it won't be matched
          by the regex `r'{([^}]+)}'`.

    If no braces are found, the original pattern is returned as a single-element list.
    The expansion logic itself is platform-independent string manipulation.
    The resulting patterns are intended for use with `fnmatch`.

    Args:
        pattern (str): The glob pattern string to expand.

    Returns:
        List[str]: A list of expanded pattern strings.
    """
    # Regex to find the first (leftmost) brace expression.
    # It captures the content within the braces if it's not empty.
    match = re.search(r'{([^}]+)}', pattern)

    if not match:
        # Base case: no more brace expressions in this pattern segment.
        return [pattern]

    prefix = pattern[:match.start()]
    options_str = match.group(1)  # The content within the braces, e.g., "opt1,opt2{suboptA,suboptB}"
    suffix = pattern[match.end():]

    # Split the captured options string by commas that are not inside deeper, nested braces.
    options = _split_comma_outside_braces(options_str)

    expanded_results: List[str] = []
    for option_part in options:
        # For each option, construct a new pattern by substituting this option.
        # Then, recursively call expand on this newly formed pattern.
        # This handles nested braces within the option_part or subsequent braces in the suffix.
        sub_pattern = prefix + option_part + suffix
        expanded_results.extend(_expand_braces_glob_pattern(sub_pattern))

    return expanded_results


def get_mock_timestamp():
    return "2023-01-01T12:00:00Z"


def add_file_to_db(workspace_root: str, relative_path: str, content: str, is_directory: bool = False):
    if not relative_path.startswith("/"):
        relative_path = "/" + relative_path

    full_path = workspace_root + relative_path

    parts = relative_path.strip("/").split("/")
    current_parent_path_in_db = workspace_root

    num_intermediate_dirs = len(parts) - 1 if not is_directory else len(parts)
    if relative_path == "/":
        num_intermediate_dirs = 0

    for i in range(num_intermediate_dirs):
        part = parts[i]
        if not part: continue
        current_parent_path_in_db += "/" + part
        if current_parent_path_in_db not in DB["file_system"]:
            DB["file_system"][current_parent_path_in_db] = {
                "path": current_parent_path_in_db,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": get_mock_timestamp()
            }

    DB["file_system"][full_path] = {
        "path": full_path,
        "is_directory": is_directory,
        "content_lines": content.splitlines(keepends=True) if not is_directory and content is not None else [],
        "size_bytes": len(content.encode('utf-8')) if not is_directory and content is not None else 0,
        "last_modified": get_mock_timestamp()
    }


def list_code_usages_generate_snippet(file_path_str: str, start_line: int, end_line: int) -> str:
    """
    Generates a code snippet from the specified file and line range.
    Assumes start_line and end_line are 1-based inclusive.
    """
    file_entry = get_file_system_entry(file_path_str)

    if not file_entry or file_entry.get("is_directory"):
        # This situation implies an issue with the data source if called with such a path.
        return f"<Error: Snippet generation failed; file not found or is a directory '{file_path_str}'>"

    content_lines = file_entry.get("content_lines")

    # Check for placeholder content which indicates content is not available or suitable
    if content_lines == BINARY_CONTENT_PLACEHOLDER or\
            content_lines == LARGE_FILE_CONTENT_PLACEHOLDER or\
            content_lines == ERROR_READING_CONTENT_PLACEHOLDER:
        return f"<Error: Snippet generation failed; content not available for '{file_path_str}'>"

    if not isinstance(content_lines, list) or not content_lines:  # Handles empty list or non-list types
        return f"<Error: Snippet generation failed; no content lines for '{file_path_str}'>"

    # Adjust line numbers for 0-based indexing and ensure they are within bounds
    # start_line and end_line are 1-based inclusive.
    actual_start_line_0_based = max(0, start_line - 1)
    # For slicing, end index is exclusive. For inclusive 0-based end, it's end_line - 1.
    actual_end_line_0_based_inclusive = min(len(content_lines) - 1, end_line - 1)

    if actual_start_line_0_based > actual_end_line_0_based_inclusive or\
            actual_start_line_0_based >= len(content_lines):
        # If range is invalid, attempt to return just the start_line if it's valid.
        if 0 <= (start_line - 1) < len(content_lines):
            return content_lines[start_line - 1].rstrip('\r\n')  # Return single line
        return f"<Error: Snippet generation failed; invalid line range {start_line}-{end_line} for '{file_path_str}'>"

    # Extract lines; content_lines elements usually end with '\n'
    # Slice up to actual_end_line_0_based_inclusive + 1 because Python slicing is exclusive at the end.
    snippet_lines_with_newlines = content_lines[actual_start_line_0_based: actual_end_line_0_based_inclusive + 1]

    # Join them. If they already have newlines, this preserves them.
    return "".join(snippet_lines_with_newlines)


# Helper function to check for placeholder content, making the main function cleaner.
# This is specific to this function's logic for determining editability.
def _is_content_uneditable_placeholder(content_lines: List[str]) -> Optional[str]:
    """
    Checks if the content_lines represent an uneditable placeholder.
    Returns a string reason if uneditable, None otherwise.
    """
    if not content_lines: # Empty content is editable
        return None

    # Direct placeholder list comparison
    if content_lines == BINARY_CONTENT_PLACEHOLDER:
        return "is binary and content not loaded"
    if content_lines == LARGE_FILE_CONTENT_PLACEHOLDER:
        # utils.MAX_FILE_SIZE_TO_LOAD_CONTENT_MB should be accessible if defined in utils
        # For a more robust message, it's better if utils provides a way to get this constant or format the message
        try:
            max_size_mb = MAX_FILE_SIZE_TO_LOAD_CONTENT_MB
            return f"exceeds maximum size ({max_size_mb}MB) and content not loaded"
        except AttributeError: # Fallback if the constant is not exposed directly
            return "exceeds maximum size and content not loaded"
    
    # Check for error messages stored in content_lines by hydration logic
    # These typically are single-line lists.
    first_line = content_lines[0] # Assumes content_lines is not empty, checked by initial `if not content_lines:`
    
    # Check against specific placeholder values defined in utils
    # Ensure these placeholder variables are actually lists if comparing list equality,
    # or compare string content if they are strings.
    # utils.ERROR_READING_CONTENT_PLACEHOLDER is defined as a list: ["<Error Reading File Content>"]
    if ERROR_READING_CONTENT_PLACEHOLDER and\
       content_lines == ERROR_READING_CONTENT_PLACEHOLDER:
         return "could not be read (placeholder indicates error)"
    
    # Check for specific error message strings that might be stored as content
    if first_line.startswith("Error: Could not read file content."): # General read error from hydrate
        return "could not be read (error during hydration)"
    if first_line.startswith("Error: Could not decode file content"): # Decode error from hydrate
        return "could not be decoded (error during hydration)"
    if first_line.startswith("Error: Permission denied to read file content."): # Permission error from hydrate
        return "could not be read due to permissions (error during hydration)"
    
    return None

def strip_code_fences_from_llm(text_content: str) -> str:
    if not text_content:
        return ""
    text_content = text_content.strip()

    # Try to match a pattern with an optional language hint followed by a newline, then content
    # ```lang\ncontent\n``` or ```\ncontent\n```
    match1 = re.match(r"^\s*```(?:[a-zA-Z]*)\s*\n(.*?)\n\s*```\s*$", text_content, re.DOTALL | re.MULTILINE)
    if match1:
        return match1.group(1).strip()

    # Try to match a pattern with just fences around content (no lang hint, no required internal newlines for structure)
    # ```content```
    match2 = re.match(r"^\s*```\s*(.*?)\s*```\s*$", text_content, re.DOTALL | re.MULTILINE)
    if match2:
        # If after this stripping, the content looks like it was just a language hint, return ""
        # e.g. original was ```python``` or ```python\n```
        content_candidate = match2.group(1).strip()
        if "\n" not in content_candidate and re.fullmatch(r"[a-zA-Z]*", content_candidate):
             # Check if the original text_content (between initial fences) was just this hint possibly with a newline
            original_between_fences = text_content[text_content.find("```")+3 : text_content.rfind("```")].strip()
            if original_between_fences == content_candidate or original_between_fences == content_candidate + '\n':
                return ""
        return content_candidate

    return text_content # Return original (stripped) if no patterns match


def _create_error_entry(file_path_str: str, line_num: int, msg: str, severity: str,
                        col_num: Optional[int] = None, code: Optional[str] = None,
                        source: Optional[str] = None) -> Dict[str, Any]:
    """Creates a structured error dictionary."""
    return {
        "file_path": file_path_str,
        "line_number": line_num,
        "column_number": col_num,
        "message": msg,
        "severity": severity,
        "code": code,
        "source": source
    }


# --- Mock error generation logic for specific file types ---
# These functions are defined before the main get_errors function that uses them.

def _get_mock_python_errors(file_path_abs: str, content_lines: List[str]) -> List[Dict[str, Any]]:
    """Generates mock Python lint/compile errors."""
    errors: List[Dict[str, Any]] = []
    for i, line_content in enumerate(content_lines):
        line_num = i + 1
        stripped_line = line_content.strip()
        
        # Skip comment lines completely
        if stripped_line.startswith("#"):
            continue

        # Rule: Python 2 print statement (basic check)
        if stripped_line.startswith("print ") and\
                ('(' not in stripped_line or stripped_line.find('(') > stripped_line.find('print ') + 6):
            col = line_content.find("print ") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "SyntaxError: Missing parentheses in call to 'print'. Did you mean print(...)?",
                "error", col_num=col, code="PY-SYNTAX-PRINT", source="compiler:mock-python"
            ))

        # Rule: Import error for non-existent modules
        if re.match(r'\s*import\s+(a_highly_unlikely_module_name\w*|totally_made_up_module_xyz\d*|osz)', stripped_line):
            module_match = re.search(r'import\s+([a-zA-Z0-9_]+)', stripped_line)
            if module_match:
                module_name = module_match.group(1)
                col = line_content.find("import") + 1
                errors.append(_create_error_entry(
                    file_path_abs, line_num,
                    f"ImportError: No module named '{module_name}'",
                    "error", col_num=col, code="E0401", source="compiler:mock-python"
                ))
        
        # Rule: ImportError from non-existent submodule
        from_match = re.search(r'from\s+(\w+)\s+import\s+(imaginary_function_that_does_not_exist)', stripped_line)
        if from_match:
            module_name = from_match.group(1)
            function_name = from_match.group(2)
            col = line_content.find("import") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                f"ImportError: cannot import name '{function_name}' from '{module_name}'",
                "error", col_num=col, code="E0611", source="compiler:mock-python"
            ))
            
        # Rule: Syntax error for 'defin' instead of 'def'
        if stripped_line.startswith("defin "):
            col = line_content.find("defin") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "SyntaxError: invalid syntax (expected 'def')",
                "error", col_num=col, code="PY-SYNTAX-DEF", source="compiler:mock-python"
            ))
            
        # Rule: Missing colon in function definition
        missing_colon_match = re.search(r'def\s+(\w+)\(\)(\s*)$', stripped_line)
        if missing_colon_match:
            col = line_content.rfind(")") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "SyntaxError: expected ':'",
                "error", col_num=col, code="PY-SYNTAX-COLON", source="compiler:mock-python"
            ))
            
        # Rule: Indentation error (extra indentation)
        if re.match(r'^\s{2,}\S', line_content) and "# Extra indentation" in line_content:
            col = 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "IndentationError: unexpected indent",
                "error", col_num=col, code="E0001", source="compiler:mock-python"
            ))
            
        # Rule: Zero division error
        if "10 / 0" in stripped_line or "np.divide(1.0, 0.0)" in stripped_line:
            col = line_content.find("/ 0") + 1 if "/ 0" in line_content else line_content.find("divide") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "ZeroDivisionError: division by zero",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: Invalid literal for int()
        if "int(\"not_a_number\")" in stripped_line:
            col = line_content.find("int(") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "ValueError: invalid literal for int() with base 10: 'not_a_number'",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: Undefined variable
        if "undefined_variable" in stripped_line and "print" in stripped_line:
            col = line_content.find("undefined_variable") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "NameError: name 'undefined_variable' is not defined",
                "error", col_num=col, code="E0602", source="compiler:mock-python"
            ))
            
        # Rule: Type error (str + int)
        if "\"string\" + 42" in stripped_line:
            col = line_content.find("+") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "TypeError: can only concatenate str (not \"int\") to str",
                "error", col_num=col, code="E1138", source="compiler:mock-python"
            ))
            
        # Rule: Non-existent method
        if "non_existent_method" in stripped_line:
            col = line_content.find("non_existent_method") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "AttributeError: 'int' object has no attribute 'non_existent_method'",
                "error", col_num=col, code="E1101", source="compiler:mock-python"
            ))
            
        # Rule: Index error
        if "my_list[10]" in stripped_line:
            col = line_content.find("[10]") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "IndexError: list index out of range",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: Key error
        if "my_dict[\"z\"]" in stripped_line:
            col = line_content.find("[\"z\"]") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "KeyError: 'z'",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: File not found
        if "file_that_does_not_exist.txt" in stripped_line:
            col = line_content.find("open(") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "FileNotFoundError: [Errno 2] No such file or directory: 'file_that_does_not_exist.txt'",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: Tab error
        if "\tx = 10" in line_content and "# Line with tab indentation" in line_content:
            col = 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "TabError: inconsistent use of tabs and spaces in indentation",
                "error", col_num=col, code="E101", source="compiler:mock-python"
            ))
            
        # Rule: Assertion error
        if "assert False" in stripped_line:
            col = line_content.find("assert") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "AssertionError: This assertion will always fail",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: Incomplete expression (EOFError)
        if "eval(\"(1, 2, \")" in stripped_line or "eval(\"[(1, 2]\")" in stripped_line:
            col = line_content.find("eval(") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "SyntaxError: unexpected EOF while parsing",
                "error", col_num=col, code="E0001", source="compiler:mock-python"
            ))
            
        # Rule: Infinite recursion error detection
        if "return infinite_recursion()" in stripped_line:
            col = line_content.find("infinite_recursion") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "RecursionError: maximum recursion depth exceeded",
                "error", col_num=col, code="F0002", source="compiler:mock-python"
            ))
            
        # Rule: UnboundLocalError detection
        if "print(x)  # x is referenced before assignment" in stripped_line:
            col = line_content.find("print(x)") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "UnboundLocalError: local variable 'x' referenced before assignment",
                "error", col_num=col, code="E0601", source="compiler:mock-python"
            ))
            
        # Rule: OverflowError detection
        if "for i in range(1000000):  # This would cause overflow" in stripped_line:
            col = line_content.find("range") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "OverflowError: Python int too large to convert to C int",
                "error", col_num=col, code="E1120", source="compiler:mock-python"
            ))
            
        # Rule: FloatingPointError detection
        if "np.seterr(all='raise')" in stripped_line:
            col = line_content.find("np.seterr") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "FloatingPointError: invalid value encountered in divide",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: UnicodeDecodeError
        if "bad_bytes.decode('utf-8')" in stripped_line:
            col = line_content.find("decode") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: MemoryError 
        if "huge_list = [1] * (10**10)" in stripped_line:
            col = line_content.find("[1]") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "MemoryError: not enough memory to create list of this size",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: GeneratorExit
        if "next(gen)  # Raises StopIteration" in stripped_line:
            col = line_content.find("next") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "StopIteration: generator already exhausted",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: SystemExit
        if "sys.exit(" in stripped_line:
            col = line_content.find("sys.exit") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "SystemExit: Exiting the script",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: TimeoutError
        if "raise TimeoutError(" in stripped_line:
            col = line_content.find("TimeoutError") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "TimeoutError: Task timed out",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: IsADirectoryError
        if "with open(os.getcwd(), 'r')" in stripped_line:
            col = line_content.find("open") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "IsADirectoryError: [Errno 21] Is a directory",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: NotADirectoryError
        if "os.listdir(\"not_a_directory.txt/some_subfolder\")" in stripped_line:
            col = line_content.find("os.listdir") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "NotADirectoryError: [Errno 20] Not a directory",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: PermissionError
        if "with open(\"/root/forbidden.txt\", \"w\")" in stripped_line:
            col = line_content.find("open") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "PermissionError: [Errno 13] Permission denied",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: BrokenPipeError
        if "os.write(w, b\"hello\")" in stripped_line:
            col = line_content.find("os.write") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "BrokenPipeError: [Errno 32] Broken pipe",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: RuntimeWarning
        if "warnings.warn(\"This is a runtime warning\", RuntimeWarning)" in stripped_line:
            col = line_content.find("warnings.warn") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "RuntimeWarning: This is a runtime warning",
                "warning", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: DeprecationWarning
        if "warnings.warn(\"Deprecated feature\", DeprecationWarning)" in stripped_line:
            col = line_content.find("warnings.warn") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "DeprecationWarning: Deprecated feature",
                "warning", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: Assignment in conditional
        if re.search(r'if\s+\w+\s*=\s*\d+:', stripped_line):
            col = line_content.find("=") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "SyntaxError: invalid syntax (use == for comparison)",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: Double function definition
        if stripped_line.startswith("def double_definition():  # Re-declared"):
            col = line_content.find("def") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "SyntaxError: function already defined",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: StopIteration in generator
        if "return 1" in stripped_line and i > 0 and "def broken_gen():" in content_lines[i-1]:
            col = line_content.find("return") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "RuntimeError: generator raised StopIteration",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))
            
        # Rule: KeyboardInterrupt
        if "raise KeyboardInterrupt(" in stripped_line:
            col = line_content.find("KeyboardInterrupt") + 1
            errors.append(_create_error_entry(
                file_path_abs, line_num,
                "KeyboardInterrupt: Simulated Ctrl+C",
                "error", col_num=col, code="E1136", source="compiler:mock-python"
            ))

        # Rule: Line too long
        pattern = '\n\r'
        if len(line_content.rstrip(pattern)) > 120:
            errors.append(_create_error_entry(
                file_path_abs, line_num, f"Line too long ({len(line_content.rstrip(pattern))}/120)",
                "warning", col_num=121, code="C0301", source="linter:mock-pylint"
            ))

        # Rule: TODO_ERROR comment
        if "TODO_ERROR:" in line_content:
            msg_start = line_content.find("TODO_ERROR:") + len("TODO_ERROR:")
            custom_msg = line_content[msg_start:].strip()
            errors.append(_create_error_entry(
                file_path_abs, line_num, f"User-flagged error: {custom_msg}",
                "error", col_num=line_content.find("TODO_ERROR:") + 1, code="USER-TODO-ERR", source="linter:mock-custom"
            ))

        # Rule: Use of 'eval('
        if "eval(" in line_content:
            errors.append(_create_error_entry(
                file_path_abs, line_num, "Security warning: Use of 'eval()' is dangerous.",
                "warning", col_num=line_content.find("eval(") + 1, code="S307", source="linter:mock-bandit"
            ))

        # Rule: Placeholder for unused variable (mocked by a comment pattern)
        if "# unused_variable_mock" in line_content:
            var_name_match = re.search(r"(\w+)\s*=\s*.*# unused_variable_mock", line_content)
            var_name = var_name_match.group(1) if var_name_match else "variable"
            col_num_var = line_content.find(var_name) + 1 if var_name_match and var_name in line_content else None
            errors.append(_create_error_entry(
                file_path_abs, line_num, f"Unused variable '{var_name}'.",
                "warning", col_num=col_num_var,
                code="F841", source="linter:mock-flake8"
            ))
    return errors


def _get_mock_javascript_errors(file_path_abs: str, content_lines: List[str]) -> List[Dict[str, Any]]:
    """Generates mock JavaScript lint errors."""
    errors: List[Dict[str, Any]] = []
    for i, line_content in enumerate(content_lines):
        line_num = i + 1
        stripped_line = line_content.strip()
        is_comment_line = stripped_line.startswith("//") or stripped_line.startswith("/*")

        # Rule: Use of 'var' instead of 'let' or 'const'
        if "var " in line_content and not is_comment_line:
            errors.append(_create_error_entry(
                file_path_abs, line_num, "Usage of 'var' is discouraged; use 'let' or 'const' instead.",
                "warning", col_num=line_content.find("var ") + 1, code="eslint(no-var)", source="linter:mock-eslint"
            ))

        # Rule: console.log statement
        if "console.log(" in line_content and not is_comment_line:
            errors.append(_create_error_entry(
                file_path_abs, line_num, "Unexpected console statement.",
                "warning", col_num=line_content.find("console.log(") + 1, code="eslint(no-console)",
                source="linter:mock-eslint"
            ))

        # Rule: Missing semicolon (very basic heuristic)
        if stripped_line and not stripped_line.endswith(";") and\
                not stripped_line.endswith("{") and not stripped_line.endswith("}") and\
                not is_comment_line and (
                "=" in stripped_line or " let " in line_content or " const " in line_content or " var " in line_content):
            # Heuristic: likely an assignment or declaration statement needing a semicolon
            errors.append(_create_error_entry(
                file_path_abs, line_num, "Missing semicolon.",
                "error", col_num=len(line_content.rstrip('\n\r')), code="eslint(semi)", source="linter:mock-eslint"
            ))

    return errors


def _get_mock_typescript_errors(file_path_abs: str, content_lines: List[str]) -> List[Dict[str, Any]]:
    """Generates mock TypeScript lint/compile errors."""
    errors: List[Dict[str, Any]] = []
    for i, line_content in enumerate(content_lines):
        line_num = i + 1
        is_comment_line = line_content.strip().startswith("//")

        # Rule: Explicit 'any' type
        if ": any" in line_content and not is_comment_line:
            errors.append(_create_error_entry(
                file_path_abs, line_num, "Type 'any' is not recommended. Add a more specific type.",
                "warning", col_num=line_content.find(": any") + 1,
                code="typescript-eslint(@typescript-eslint/no-explicit-any)", source="linter:mock-eslint-typescript"
            ))
        # Rule: Property does not exist (mocked by a comment)
        if "// MOCK_TS_ERROR_PROPERTY_DOES_NOT_EXIST" in line_content:
            errors.append(_create_error_entry(
                file_path_abs, line_num, "Property 'mockProperty' does not exist on type 'MockType'.",
                "error", col_num=1, code="TS2339", source="compiler:mock-tsc"
            ))
    return errors


def _get_mock_json_errors(file_path_abs: str, content_lines: List[str]) -> List[Dict[str, Any]]:
    """Generates mock JSON syntax errors by trying to parse the content."""
    errors_found: List[Dict[str, Any]] = []
    full_content = "".join(content_lines)

    if not full_content.strip():  # Empty or whitespace-only JSON
        errors_found.append(_create_error_entry(
            file_path_abs, 1, "JSON error: Document is empty or contains only whitespace.",
            "error", col_num=1, code="JSON-EMPTY", source="linter:mock-json-parser"
        ))
        return errors_found

    try:
        json.loads(full_content)
    except json.JSONDecodeError as e:
        errors_found.append(_create_error_entry(
            file_path_abs, e.lineno, f"JSON parse error: {e.msg}",
            "error", col_num=e.colno, code="JSON-SYNTAX", source="linter:mock-json-parser"
        ))

    # Rule: Trailing comma (simplistic check, as json.loads might catch some cases depending on Python version)
    # This focuses on commas at the end of lines before a closing brace/bracket on a subsequent line.
    for i, line_content in enumerate(content_lines):
        stripped_line = line_content.strip()
        if stripped_line.endswith(","):
            # Check if next non-empty line starts with } or ]
            for j in range(i + 1, len(content_lines)):
                next_stripped_line = content_lines[j].strip()
                if next_stripped_line:  # Found next non-empty line
                    if next_stripped_line.startswith("}") or next_stripped_line.startswith("]"):
                        # Avoid duplicate if json.loads already reported a syntax error at this exact spot for a trailing comma
                        is_duplicate = False
                        for err in errors_found:
                            if err["line_number"] == (i + 1) and\
                                    err["message"].lower().startswith("json parse error: trailing comma"):
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            errors_found.append(_create_error_entry(
                                file_path_abs, i + 1, "JSON error: Trailing comma.",
                                "error", col_num=len(line_content.rstrip('\n\r')), code="JSON-TRAILING-COMMA",
                                source="linter:mock-json-parser"
                            ))
                    break  # Stop checking subsequent lines for this specific comma

    # Basic deduplication for JSON errors based on line, column, and message.
    # This is simple; real systems have more advanced deduplication.
    final_errors: List[Dict[str, Any]] = []
    seen_error_signatures = set()
    for err in errors_found:
        signature = (err["line_number"], err.get("column_number"), err["message"])
        if signature not in seen_error_signatures:
            final_errors.append(err)
            seen_error_signatures.add(signature)
    return final_errors

def extract_module_details(filename: str) -> Dict[str, Any]:
    """
    Extracts base module name, extension, and test pattern info from a filename.
    Example: "test_mymodule.py" -> base_module_name="mymodule", is_test_by_name=True
             "utils.test.js" -> base_module_name="utils", is_test_by_name=True
             "main.py" -> base_module_name="main", is_test_by_name=False
             "test_framework_core.py" -> base_module_name="test_framework_core", is_test_by_name=False (specific rule)
             "test_test_framework_core.py" -> base_module_name="test_framework_core", is_test_by_name=True (specific rule)
    """
    name_no_ext_from_splitext, ext_from_splitext = os.path.splitext(filename)

    details = {
        "original_filename": filename,
        "name_no_ext": name_no_ext_from_splitext,
        "ext": ext_from_splitext.lower(),
        "base_module_name": name_no_ext_from_splitext,  # Default, refined below
        "is_test_by_name": False,
        "test_pattern_type": None
    }

    # 0. Specific override for known source files starting with "test_"
    #    These are source files, and their tests are typically "test_" + their own name.
    if details["name_no_ext"] in {"test_framework_core"}:
        # details["base_module_name"] is already name_no_ext_from_splitext (e.g., "test_framework_core")
        details["is_test_by_name"] = False
        # test_pattern_type remains None as it's not a test by this rule.
        return details  # Early exit for these special cases

    # Test pattern rules. Order can be important.
    # 1. `test_test_` prefix (e.g., test_test_foo.py is test for test_foo.py)
    if details["name_no_ext"].startswith("test_test_"):
        # Base module is the part after the first "test_", e.g., "test_foo" from "test_test_foo"
        details["base_module_name"] = details["name_no_ext"][5:]
        details["is_test_by_name"] = True
        details["test_pattern_type"] = "prefix_double_test"
    # 2. Infix `.spec` (e.g., component.spec.js is test for component.js)
    elif details["name_no_ext"].endswith(".spec"):
        details["base_module_name"] = details["name_no_ext"][:-5]  # Remove ".spec"
        details["is_test_by_name"] = True
        details["test_pattern_type"] = "infix_spec"
    # 3. Infix `.test` (e.g., component.test.js is test for component.js)
    elif details["name_no_ext"].endswith(".test"):
        details["base_module_name"] = details["name_no_ext"][:-5]  # Remove ".test"
        details["is_test_by_name"] = True
        details["test_pattern_type"] = "infix_test"
    # 4. Suffix `_test` (e.g., module_test.py is test for module.py)
    elif details["name_no_ext"].endswith("_test"):
        details["base_module_name"] = details["name_no_ext"][:-5]  # Remove "_test"
        details["is_test_by_name"] = True
        details["test_pattern_type"] = "suffix"  # Kept as "suffix" to match original code style
    # 5. General `test_` prefix (e.g., test_foo.py is test for foo.py)
    elif details["name_no_ext"].startswith("test_"):
        base = details["name_no_ext"][5:]  # "test_foo" -> "foo"
        if base:  # Avoids "test_" -> "" resulting in empty base_module_name
            details["base_module_name"] = base
            details["is_test_by_name"] = True
            details["test_pattern_type"] = "prefix_test"
        # else: if name_no_ext is just "test_", base_module_name remains "test_", is_test_by_name is False by default.

    # This check handles cases where stripping a test pattern results in an empty base module name.
    # E.g. if filename was "_test.py", base_module_name becomes "" after stripping "_test".
    if not details["base_module_name"] and details["is_test_by_name"]:
        # Consider this not a valid pattern match for these rules.
        details["is_test_by_name"] = False
        details["test_pattern_type"] = None
        details["base_module_name"] = details["name_no_ext"]  # Restore original name_no_ext

    return details


def is_in_test_dir(file_dir_abs: str, workspace_root_abs: str) -> bool:
    """Checks if a file directory is likely a dedicated test directory."""
    # Normalize paths at the beginning for consistent processing
    norm_file_dir_abs = os.path.normpath(file_dir_abs)
    norm_workspace_root_abs = os.path.normpath(workspace_root_abs)

    if not norm_file_dir_abs.startswith(norm_workspace_root_abs):
        return False

    if norm_file_dir_abs == norm_workspace_root_abs:
        return False  # File is in the workspace root, not considered a "test dir" by this rule

    try:
        relative_dir = os.path.relpath(norm_file_dir_abs, norm_workspace_root_abs)
    except ValueError:
        return False  # Should not happen if startswith check passed and paths are valid

    path_components = relative_dir.split(os.sep)
    # Common test directory names
    test_dir_names = {"tests", "test", "spec", "__tests__"}

    for component in path_components:
        if component.lower() in test_dir_names:
            return True
    return False


def generate_related_file_candidates(
        current_file_dir_abs: str,
        module_name: str,
        ext: str,
        is_searching_for_test_file: bool,
        workspace_root_abs: str  # Expect normalized path
) -> List[Tuple[str, float]]:
    """Generates a list of (candidate_abs_path, confidence_score) tuples."""
    candidates: List[Tuple[str, float]] = []

    # Ensure module_name is not empty before prepending/appending test markers
    if not module_name:
        return []

    norm_current_file_dir_abs = _normalize_path_for_db(current_file_dir_abs)

    # --- Strategy 1: Same Directory ---
    if is_searching_for_test_file:
        # Source -> Test
        patterns = [
            (f"test_{module_name}{ext}", 0.95),
            (f"{module_name}_test{ext}", 0.90),
            (f"{module_name}.test{ext}", 0.90),
            (f"{module_name}.spec{ext}", 0.90),
        ]
        # Handle cases like test_framework_core.py (source) -> test_test_framework_core.py (test)
        # If module_name itself starts with "test_", its test might be "test_" + module_name
        if module_name.startswith("test_"):  # e.g. module_name is "test_framework_core"
            patterns.append((f"test_{module_name}{ext}", 0.95))  # Generates "test_test_framework_core.py"

        for fname_pattern, conf in patterns:
            candidate_path = _normalize_path_for_db(os.path.join(norm_current_file_dir_abs, fname_pattern))
            candidates.append((candidate_path, conf))
    else:
        # Example: module_name="app", ext=".py" -> "app.py"
        # Example: module_name="test_framework_core", ext=".py" -> "test_framework_core.py"
        fname_pattern = f"{module_name}{ext}"
        candidate_path = _normalize_path_for_db(os.path.join(norm_current_file_dir_abs, fname_pattern))
        candidates.append((candidate_path, 0.95))

    # --- Strategy 2: Parallel Directory Structure (e.g., src/ vs tests/) ---
    structure_map_source_to_test = {
        "src": ["tests", "test", "__tests__"],
        "app": ["tests", "test", "__tests__"],
        "lib": ["tests", "test", "__tests__"],
    }
    structure_map_test_to_source = {
        "tests": ["src", "app", "lib"],
        "test": ["src", "app", "lib"],
        "__tests__": ["src", "app", "lib"],
        "spec": ["src", "app", "lib"],
    }

    if not norm_current_file_dir_abs.startswith(workspace_root_abs):
        return candidates

    # Convert to OS-specific paths for relpath calculation, then back to forward slashes
    os_current_file_dir = norm_current_file_dir_abs.replace('/', os.sep)
    os_workspace_root = workspace_root_abs.replace('/', os.sep)
    current_relative_to_workspace = os.path.relpath(os_current_file_dir, os_workspace_root)
    
    path_parts_from_workspace = []
    if current_relative_to_workspace != '.':
        # Use forward slash for consistent path splitting since our DB paths use forward slashes
        normalized_relative = current_relative_to_workspace.replace(os.sep, '/')
        path_parts_from_workspace = normalized_relative.split('/')

    for i, part in enumerate(path_parts_from_workspace):
        current_map = structure_map_source_to_test if is_searching_for_test_file else structure_map_test_to_source

        if part.lower() in current_map:
            target_dir_options = current_map[part.lower()]
            base_path_parts = path_parts_from_workspace[:i]
            sub_path_parts = path_parts_from_workspace[i + 1:]

            for target_replacement_dir_name in target_dir_options:
                new_path_parts_from_workspace = base_path_parts + [target_replacement_dir_name] + sub_path_parts

                target_base_dir_abs = workspace_root_abs
                for p_part in new_path_parts_from_workspace:
                    target_base_dir_abs = os.path.join(target_base_dir_abs, p_part)
                target_base_dir_abs = _normalize_path_for_db(target_base_dir_abs)

                if is_searching_for_test_file:
                    sub_patterns = [
                        (f"test_{module_name}{ext}", 0.85),
                        (f"{module_name}_test{ext}", 0.80),
                        (f"{module_name}.test{ext}", 0.80),
                        (f"{module_name}.spec{ext}", 0.80),
                    ]
                    if module_name.startswith("test_"):
                        sub_patterns.append((f"test_{module_name}{ext}", 0.85))

                    for fname_pattern, conf in sub_patterns:
                        candidate_path = _normalize_path_for_db(os.path.join(target_base_dir_abs, fname_pattern))
                        candidates.append((candidate_path, conf))
                else:
                    fname_pattern = f"{module_name}{ext}"
                    candidate_path = _normalize_path_for_db(os.path.join(target_base_dir_abs, fname_pattern))
                    candidates.append((candidate_path, 0.85))
            break
    return candidates


_PROJECT_SETUP_DATA: Dict[tuple[str, str], Dict[str, Any]] = {
    ("typescript_server", "typescript"): {
        "recommended_extensions": [
            {"id": "dbaeumer.vscode-eslint", "name": "ESLint", "reason": "Integrates ESLint into VS Code for code quality and style checking."},
            {"id": "esbenp.prettier-vscode", "name": "Prettier - Code formatter", "reason": "Automatically formats TypeScript code for consistency."},
            {"id": "ms-vscode.vscode-typescript-next", "name": "JavaScript and TypeScript Nightly", "reason": "Provides latest TypeScript language support."},
            {"id": "orta.vscode-jest", "name": "Jest", "reason": "For running and debugging Jest tests."},
            {"id": "VisualStudioExptTeam.vscodeintellicode", "name": "IntelliCode", "reason": "AI-assisted IntelliSense for TypeScript."},
        ],
        "key_configuration_files": [
            {"file_name_pattern": "tsconfig.json", "purpose": "TypeScript compiler configuration.",
             "example_content_snippet": '''{
  "compilerOptions": {
    "target": "es2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "**/*.spec.ts"]
}'''},
            {"file_name_pattern": "package.json", "purpose": "Project metadata, dependencies, and scripts.",
             "example_content_snippet": '''{
  "name": "my-typescript-server",
  "version": "1.0.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "nodemon --watch 'src/**/*.ts' --exec 'ts-node' src/index.ts",
    "test": "jest"
  },
  "dependencies": {},
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0",
    "nodemon": "^3.0.0",
    "ts-node": "^10.9.0",
    "jest": "^29.0.0",
    "@types/jest": "^29.0.0",
    "ts-jest": "^29.0.0"
  }
}'''},
            {"file_name_pattern": ".eslintrc.json", "purpose": "ESLint configuration.",
             "example_content_snippet": '''{
  "root": true,
  "parser": "@typescript-eslint/parser",
  "plugins": [
    "@typescript-eslint"
  ],
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {}
}'''},
            {"file_name_pattern": ".vscode/launch.json", "purpose": "VS Code debugger configurations.",
             "example_content_snippet": '''{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Launch TypeScript Server",
      "skipFiles": [
        "<node_internals>/**"
      ],
      "program": "${workspaceFolder}/src/index.ts",
      "preLaunchTask": "npm: build",
      "outFiles": [
        "${workspaceFolder}/dist/**/*.js"
      ],
      "sourceMaps": true,
      "smartStep": true,
      "internalConsoleOptions": "openOnSessionStart",
      "console": "integratedTerminal"
    }
  ]
}'''},
        ],
        "common_tasks": [
            {"name": "Install Dependencies", "command_suggestion": "npm install (or yarn install)"},
            {"name": "Build Project", "command_suggestion": "npm run build (or yarn build)"},
            {"name": "Run Unit Tests", "command_suggestion": "npm test (or yarn test)"},
            {"name": "Start Development Server (with auto-reload)", "command_suggestion": "npm run dev (or yarn dev)"},
            {"name": "Start Production Server", "command_suggestion": "npm start (or yarn start)"},
            {"name": "Start Debug Server (VS Code)", "command_suggestion": "Select 'Launch TypeScript Server' from the Run and Debug view (usually F5)."},
        ],
        "debugging_tips": [
            "Ensure 'sourceMap': true in your tsconfig.json compilerOptions for effective debugging of .ts files.",
            "Use breakpoints directly in your .ts files.",
            "Verify your launch.json configuration points to the correct entry file and that `outFiles` matches your compiled JavaScript output directory.",
            "Check the 'Debug Console' in VS Code for logs and errors during debugging.",
        ],
    },
    ("python_datascience", "python"): {
        "recommended_extensions": [
            {"id": "ms-python.python", "name": "Python", "reason": "Core Python language support, linting, debugging, IntelliSense, etc."},
            {"id": "ms-toolsai.jupyter", "name": "Jupyter", "reason": "Enables working with Jupyter notebooks (.ipynb files) directly in VS Code."},
            {"id": "ms-python.vscode-pylance", "name": "Pylance", "reason": "High-performance language server for Python, offering rich type information, autocompletion, and code analysis."},
            {"id": "njpwerner.autodocstring", "name": "autoDocstring - Python Docstring Generator", "reason": "Simplifies generating Python docstrings in various formats."},
            {"id": "donjayamanne.githistory", "name": "GitLens  Git supercharged", "reason": "Enhances Git capabilities within VS Code, useful for tracking changes."},
            {"id": "visualstudioexptteam.vscodeintellicode", "name": "IntelliCode", "reason": "AI-assisted IntelliSense, providing context-aware code completion suggestions."},
        ],
        "key_configuration_files": [
            {"file_name_pattern": "requirements.txt", "purpose": "Defines Python package dependencies for pip-based environments.",
             "example_content_snippet": "# Example requirements.txt:\npandas>=1.3.0\nnumpy>=1.20.0\nscikit-learn>=1.0.0\nmatplotlib>=3.4.0\nseaborn>=0.11.0\njupyterlab>=3.0.0\nipykernel>=6.0.0"},
            {"file_name_pattern": "environment.yml", "purpose": "Defines Python package dependencies and channels for Conda environments.",
             "example_content_snippet": '''name: mydatascience-env
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - pandas
  - numpy
  - scikit-learn
  - matplotlib
  - seaborn
  - jupyterlab
  - ipykernel'''},
            {"file_name_pattern": ".vscode/settings.json", "purpose": "Workspace-specific VS Code settings, e.g., Python interpreter path, linter/formatter preferences.",
             "example_content_snippet": '''{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "jupyter.jupyterServerType": "local"
}'''},
            {"file_name_pattern": ".vscode/launch.json", "purpose": "VS Code debugger configurations for Python scripts.",
             "example_content_snippet": '''{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}'''},
            {"file_name_pattern": "notebooks/*.ipynb", "purpose": "Jupyter notebooks for data exploration, analysis, visualization, and model training.", "example_content_snippet": None},
            {"file_name_pattern": "src/data_processing.py", "purpose": "Example of a Python module for data cleaning and transformation logic.", "example_content_snippet": "# src/data_processing.py\nimport pandas as pd\n\ndef load_data(file_path: str) -> pd.DataFrame:\n    return pd.read_csv(file_path)\n\ndef clean_data(df: pd.DataFrame) -> pd.DataFrame:\n    df.dropna(inplace=True)\n    return df"},
        ],
        "common_tasks": [
            {"name": "Create/Activate Virtual Environment (venv)", "command_suggestion": "python -m venv .venv && source .venv/bin/activate (Linux/macOS) or .venv\\Scripts\\activate (Windows)"},
            {"name": "Create/Activate Virtual Environment (Conda)", "command_suggestion": "conda create --name mydatascience-env python=3.9 && conda activate mydatascience-env"},
            {"name": "Install Dependencies (pip)", "command_suggestion": "pip install -r requirements.txt"},
            {"name": "Install Dependencies (Conda)", "command_suggestion": "conda env update --file environment.yml --prune"},
            {"name": "Run Jupyter Notebook/Lab Server", "command_suggestion": "jupyter notebook (or jupyter lab)"},
            {"name": "Run Python Script", "command_suggestion": "python path/to/your_script.py"},
            {"name": "Debug Python Script (VS Code)", "command_suggestion": "Set breakpoints, select 'Python: Current File' from Run and Debug view, and press F5."},
            {"name": "Format Code (Black)", "command_suggestion": "black ."},
            {"name": "Lint Code (Flake8)", "command_suggestion": "flake8 ."},
        ],
        "debugging_tips": [
            "Ensure your Python interpreter (venv or Conda env) is correctly selected in VS Code (Ctrl+Shift+P > 'Python: Select Interpreter').",
            "For Jupyter notebooks, use VS Code's interactive window, cell-by-cell execution, and the built-in variable explorer and data viewer.",
            "Utilize the 'Run and Debug' view (Ctrl+Shift+D) to manage configurations and launch debugging sessions for .py files.",
            "Inspect variables, set conditional breakpoints, and watch expressions in the 'VARIABLES' and 'WATCH' panes of the debug sidebar.",
        ],
    },
    ("vscode_extension", "typescript"): {
        "recommended_extensions": [
            {"id": "dbaeumer.vscode-eslint", "name": "ESLint", "reason": "Ensures code quality and consistency for TypeScript code in your extension."},
            {"id": "esbenp.prettier-vscode", "name": "Prettier - Code formatter", "reason": "Automatically formats TypeScript code, maintaining a clean codebase."},
            {"id": "ms-vscode.vsce", "name": "vsce", "reason": "The official command-line tool for packaging, publishing, and managing VS Code extensions."},
            {"id": "ms-vscode.vscode-extension-test-runner", "name": "VS Code Extension Test Runner", "reason": "Provides support for running integration and unit tests for your extension."},
            {"id": "VisualStudioExptTeam.vscodeintellicode", "name": "IntelliCode", "reason": "AI-assisted IntelliSense for TypeScript, improving development speed."},
        ],
        "key_configuration_files": [
            {"file_name_pattern": "package.json", "purpose": "The extension manifest file. Defines metadata, activation events, contributions, dependencies, and scripts.",
             "example_content_snippet": '''{
  "name": "my-vscode-extension",
  "displayName": "My Awesome VS Code Extension",
  "description": "A brief description of what your extension does.",
  "version": "0.0.1",
  "publisher": "your-publisher-name",
  "engines": {
    "vscode": "^1.80.0"
  },
  "categories": [
    "Other"
  ],
  "activationEvents": [
    "onCommand:myExtension.sayHello"
  ],
  "main": "./out/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "myExtension.sayHello",
        "title": "Say Hello"
      }
    ],
    "configuration": {
      "title": "My Extension Settings",
      "properties": {
        "myExtension.greeting": {
          "type": "string",
          "default": "Hello",
          "description": "The greeting message to show."
        }
      }
    }
  },
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./",
    "lint": "eslint src --ext ts",
    "test": "vscode-test"
  },
  "devDependencies": {
    "@types/vscode": "^1.80.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "@typescript-eslint/parser": "^5.0.0",
    "@typescript-eslint/eslint-plugin": "^5.0.0",
    "@vscode/test-electron": "^2.3.0"
  }
}'''},
            {"file_name_pattern": "src/extension.ts", "purpose": "The main TypeScript file containing the extension's activation and deactivation logic.",
             "example_content_snippet": '''import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Congratulations, your extension "my-vscode-extension" is now active!');

    let disposable = vscode.commands.registerCommand('myExtension.sayHello', () => {
        const greeting = vscode.workspace.getConfiguration('myExtension').get<string>('greeting');
        vscode.window.showInformationMessage(`${greeting} from My VS Code Extension!`);
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {
    console.log('Your extension "my-vscode-extension" is now deactivated.');
}'''},
            {"file_name_pattern": "tsconfig.json", "purpose": "TypeScript compiler options for building the extension.",
             "example_content_snippet": '''{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2020",
    "outDir": "out",
    "lib": [
      "ES2020"
    ],
    "sourceMap": true,
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": [
    "src/**/*.ts"
  ],
  "exclude": [
    "node_modules",
    ".vscode-test"
  ]
}'''},
            {"file_name_pattern": ".vscode/launch.json", "purpose": "VS Code debugger configuration for running and debugging the extension.",
             "example_content_snippet": '''{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}"
      ],
      "outFiles": [
        "${workspaceFolder}/out/**/*.js"
      ],
      "preLaunchTask": "npm: watch"
    },
    {
      "name": "Extension Tests",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}",
        "--extensionTestsPath=${workspaceFolder}/out/test/suite/index"
      ],
      "outFiles": [
        "${workspaceFolder}/out/test/**/*.js"
      ],
      "preLaunchTask": "npm: watch"
    }
  ]
}'''},
        ],
        "common_tasks": [
            {"name": "Install Dependencies", "command_suggestion": "npm install (or yarn install)"},
            {"name": "Compile Extension (once)", "command_suggestion": "npm run compile (or yarn compile)"},
            {"name": "Watch for Changes & Compile", "command_suggestion": "npm run watch (or yarn watch)"},
            {"name": "Lint Code", "command_suggestion": "npm run lint (or yarn lint)"},
            {"name": "Run Extension in Development Host", "command_suggestion": "Press F5 in VS Code (uses 'Run Extension' launch configuration)."},
            {"name": "Run Extension Tests", "command_suggestion": "Select 'Extension Tests' launch configuration and press F5, or run `npm test`."},
            {"name": "Package Extension (.vsix file)", "command_suggestion": "vsce package"},
        ],
        "debugging_tips": [
            "Use the 'Run Extension' (F5) launch configuration to start an 'Extension Development Host' window with your extension loaded.",
            "Set breakpoints in your `src/**/*.ts` files.",
            "`console.log()` output from your extension appears in the Debug Console of the main VS Code window (not the Extension Development Host).",
            "Use the `Developer: Inspect Context Keys` and `Developer: Toggle Developer Tools` commands in the Extension Development Host for advanced debugging.",
        ],
    },
}


def quote_path_if_needed(path: str) -> str:
    """
    Quotes a path if it contains spaces and is not already quoted.
    This is to ensure correct parsing by shell or git commands when the path is part of a command string.
    """
    if " " in path:
        # Check if already quoted with single or double quotes
        if not ((path.startswith('"') and path.endswith('"')) or
                (path.startswith("'") and path.endswith("'"))):
            return f'"{path}"'  # Use double quotes as a common convention
    return path


def collect_pre_command_metadata_state(
    file_system: Dict[str, Any],
    exec_env_root: str,
    workspace_root: str,
) -> Dict[str, Dict[str, Any]]:
    return common_utils.collect_pre_command_metadata_state(
        file_system,
        exec_env_root,
        workspace_root,
    )


def collect_post_command_metadata_state(
    file_system: Dict[str, Any],
    exec_env_root: str,
    workspace_root: str,
) -> Dict[str, Dict[str, Any]]:
    return common_utils.collect_post_command_metadata_state(
        file_system,
        exec_env_root,
        workspace_root,
    )


def preserve_unchanged_change_times(
    db_file_system: Dict[str, Any],
    pre_command_state: Dict[str, Dict[str, Any]],
    post_command_state: Dict[str, Dict[str, Any]],
    original_filesystem_state: Dict[str, Any],
    current_workspace_root_norm: str,
    exec_env_root: str
) -> None:
    return common_utils.preserve_unchanged_change_times(
        db_file_system,
        pre_command_state,
        post_command_state,
        original_filesystem_state,
        current_workspace_root_norm,
        exec_env_root
    )


def _apply_file_metadata(
    target_path: str,
    metadata: Dict[str, Any],
    strict_mode: bool = False
) -> None:
    return common_utils._apply_file_metadata(target_path, metadata, strict_mode)


def _extract_last_unquoted_redirection_target(command: str) -> Optional[str]:
    return common_utils._extract_last_unquoted_redirection_target(command)


def detect_and_fix_tar_command(command: str, cwd: str) -> str:
    return common_utils.detect_and_fix_tar_command(command, cwd)

