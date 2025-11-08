"""
File System module for Copilot API.
Provides functions for file system operations.
"""
from common_utils.tool_spec_decorator import tool_spec
import logging
import re
import os
import re
import fnmatch

from typing import Dict, Any, Optional, List

from .SimulationEngine.db import DB
from .SimulationEngine import utils
from .SimulationEngine import models
from .SimulationEngine import custom_errors
from .SimulationEngine.llm_interface import call_llm

logger = logging.getLogger(__name__)


# This specific marker for permission denied content is based on its construction
# in the provided utils.hydrate_db_from_directory function.
_PERMISSION_DENIED_MARKER = ["Error: Permission denied to read file content.\n"]


@tool_spec(
    spec={
        'name': 'file_search',
        'description': """ Search for files in the workspace by glob pattern.
        
        This function searches for files in the workspace using a glob pattern. It returns a list of
        file paths relative to the workspace root that match the pattern.
        The search is limited to 20 results. This tool is suitable when the filename pattern
        for the desired files is known. Glob patterns are matched starting from the root of the
        workspace folder. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'glob_pattern': {
                    'type': 'string',
                    'description': 'The glob pattern to search for files.'
                }
            },
            'required': [
                'glob_pattern'
            ]
        }
    }
)
def file_search(glob_pattern: str) -> List[str]:
    """Search for files in the workspace by glob pattern.

    This function searches for files in the workspace using a glob pattern. It returns a list of
    file paths relative to the workspace root that match the pattern.
    The search is limited to 20 results. This tool is suitable when the filename pattern
    for the desired files is known. Glob patterns are matched starting from the root of the
    workspace folder.

    Examples:
    - '**/*.{js,ts}' to match all js/ts files in the workspace.
    - 'src/**' to match all files under the top-level src folder.
    - '**/foo/**/*.js' to match all js files under any foo folder in the workspace.

    Args:
        glob_pattern (str): The glob pattern to search for files.

    Returns:
        List[str]: A list of file paths (strings), relative to the workspace root,
                   that match the provided glob pattern. Max 20 results.

    Raises:
        InvalidInputError: If 'glob_pattern' is not a string or is empty.
        InvalidGlobPatternError: If the provided glob pattern has invalid syntax for fnmatch.
        WorkspaceNotAvailableError: If the user's workspace cannot be accessed or is invalid.
    """
    if not isinstance(glob_pattern, str):
        raise custom_errors.InvalidInputError("Input 'glob_pattern' must be a string.")
    if not glob_pattern:
        raise custom_errors.InvalidInputError("Input 'glob_pattern' cannot be empty.")

    # Check for malformed glob pattern (e.g., unclosed brackets like '[')
    try:
        fnmatch.translate(glob_pattern)
    except re.error as e:
        # This catches errors if the glob pattern translates to an invalid regex.
        raise custom_errors.InvalidGlobPatternError(f"Invalid glob pattern syntax: '{glob_pattern}'. Error: {e}")

    # 2. Access Workspace
    workspace_root = DB.get("workspace_root")
    if workspace_root is None or not isinstance(workspace_root, str) or not workspace_root.strip():
        raise custom_errors.WorkspaceNotAvailableError("Workspace root is not configured or available.")

    file_system = DB.get("file_system")
    if file_system is None: # Check specifically for None, as {} is a valid empty file system
        raise custom_errors.WorkspaceNotAvailableError("File system data is not available in the workspace.")

    # Normalize workspace_root once for consistent path operations.
    # Paths in DB are expected to use forward slashes.
    normalized_workspace_root = os.path.normpath(workspace_root).replace("\\", "/")
    # Additional check for an effectively empty or invalid root after normalization
    if normalized_workspace_root == '.' or not normalized_workspace_root.startswith('/'): # Assuming Unix-like absolute paths for DB keys
        raise custom_errors.WorkspaceNotAvailableError(f"Normalized workspace root '{normalized_workspace_root}' is invalid.")

    # Expand braces in the glob pattern, e.g., "*.{txt,log}" -> ["*.txt", "*.log"]
    patterns_to_match = utils._expand_braces_glob_pattern(glob_pattern)
    # 3. Iterate and Match
    matching_files: List[str] = []
    
    # Sorting keys for deterministic results, helpful for testing.
    sorted_db_file_paths = sorted(file_system.keys())

    for abs_path_str in sorted_db_file_paths:
        entry = file_system.get(abs_path_str)
        
        # Ensure entry exists and is a file
        if not entry or entry.get("is_directory", True): # Default to is_directory=True to skip if key missing or malformed
            continue

        # Paths in DB are absolute. Normalize for reliable comparison and relpath.
        normalized_abs_path = os.path.normpath(abs_path_str).replace("\\", "/")
        
        # Ensure the file path is actually within the workspace_root.
        # Check 1: Common path must be the workspace root.
        common_prefix_check = os.path.commonpath([normalized_abs_path, normalized_workspace_root])
        normalized_common_prefix_check = os.path.normpath(common_prefix_check).replace("\\", "/")

        if normalized_common_prefix_check != normalized_workspace_root:
            continue
        
        # Check 2: Path must be strictly longer than root if they are different,
        # or exactly the same. This prevents matching files outside by tricky relative paths.
        # And relpath calculation needs this.
        if normalized_abs_path != normalized_workspace_root and \
           not normalized_abs_path.startswith(normalized_workspace_root + '/'):
            # This handles cases like workspace_root="/foo" and path="/foobar" (not under /foo/)
            # Only relevant if commonpath check isn't sufficient (e.g. root is "/")
            if normalized_workspace_root == '/' and normalized_abs_path.startswith('/'):
                 pass # Path is under root if root is "/"
            else:
                 continue


        relative_path_for_glob: str
        try:
            relative_path_for_glob = os.path.relpath(normalized_abs_path, normalized_workspace_root)
            # Ensure forward slashes, as fnmatch expects them.
            relative_path_for_glob = relative_path_for_glob.replace(os.sep, '/')
            
            if relative_path_for_glob == ".":
                # This means normalized_abs_path is same as normalized_workspace_root.
                # Since we skip directories, this would only be if workspace_root itself is a file.
                # A file named "." is not a typical glob target, so skip.
                continue
        except ValueError:
            # This can happen if paths are on different drives (Windows) or other complex scenarios,
            # though our commonpath check should mitigate this for valid workspace setups.
            continue

        for p_item in patterns_to_match:
            matched = False
            # Primary match attempt
            if fnmatch.fnmatchcase(relative_path_for_glob, p_item):
                matched = True

            elif (p_item.startswith('**/') and '/' not in relative_path_for_glob):
                # Attempt to match against the pattern part after '**/'
                if fnmatch.fnmatchcase(relative_path_for_glob, p_item[3:]):
                    matched = True
            elif (p_item == '**' and '/' not in relative_path_for_glob):

                pass # Let the main `if` handle `p_item == '**'`

            if matched:
                matching_files.append(relative_path_for_glob)
                break
        
        if len(matching_files) >= 20:
            break
            
    return matching_files


@tool_spec(
    spec={
        'name': 'read_file',
        'description': """ Read the contents of a file.
        
        This function reads a specified range of lines from a file. If the requested
        range is part of a larger file, an outline of the file structure may be
        provided. If the returned content is insufficient, this function can be
        called again to retrieve more content. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The path to the file to be read.'
                },
                'start_line': {
                    'type': 'integer',
                    'description': 'The 1-based starting line number of the content to retrieve.'
                },
                'end_line': {
                    'type': 'integer',
                    'description': 'The 1-based ending line number of the content to retrieve.'
                }
            },
            'required': [
                'file_path',
                'start_line',
                'end_line'
            ]
        }
    }
)
def read_file(file_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
    """Read the contents of a file.

    This function reads a specified range of lines from a file. If the requested
    range is part of a larger file, an outline of the file structure may be
    provided. If the returned content is insufficient, this function can be
    called again to retrieve more content.

    Args:
        file_path (str): The path to the file to be read.
        start_line (int): The 1-based starting line number of the content to retrieve.
        end_line (int): The 1-based ending line number of the content to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing a single key "file_details",
                        which in turn holds an object with the content of the
                        requested file segment and related metadata:
            file_details (Dict[str, Any]):
                file_path (str): The path of the file that was read.
                content (str): The content of the requested line range of the file.
                start_line (int): The starting line number (1-based) of the returned content.
                end_line (int): The ending line number (1-based) of the returned content.
                total_lines (int): The total number of lines in the file.
                is_truncated_at_top (bool): True if the returned content does not start from the
                                            beginning of the file due to the requested range.
                is_truncated_at_bottom (bool): True if the returned content does not reach the end
                                               of the file due to the requested range or size limits.
                outline (Optional[List[Dict[str, Any]]]): An optional outline of the file,
                                                          typically provided for larger files or when
                                                          a specific range is not fully covering.
                                                          Each dictionary in the list describes a
                                                          structural element and has the following keys:
                    name (str): Name of the symbol or section (e.g., function name,
                                class name, heading).
                    kind (str): Type of symbol or section (e.g., 'function', 'class',
                                'module', 'section').
                    start_line (int): Start line of the symbol/section in the file.
                    end_line (int): End line of the symbol/section in the file.

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        InvalidLineRangeError: If the specified line range is invalid (e.g., start_line >
                               end_line, or lines are out of bounds for the file).
        PermissionDeniedError: If there is no permission to read the specified file.
        InvalidInputError: If input arguments fail validation.
        RuntimeError: If the file entry in the internal database is malformed.
    """

    # 1. Initial Input Validation
    if not isinstance(file_path, str) or not file_path:
        raise custom_errors.InvalidInputError("File path must be a non-empty string.")
    if not isinstance(start_line, int) or start_line < 1:
        raise custom_errors.InvalidInputError(
            f"Start line must be a positive integer, got {start_line}."
        )
    if not isinstance(end_line, int) or end_line < 1:
        raise custom_errors.InvalidInputError(
            f"End line must be a positive integer, got {end_line}."
        )
    if start_line > end_line:
        raise custom_errors.InvalidLineRangeError(
            f"Start line ({start_line}) cannot be greater than end line ({end_line})."
        )

    # 2. Path Resolution and File Check
    try:
        abs_path = utils.get_absolute_path(file_path)
    except ValueError as e:
        # This occurs if path is outside workspace or malformed (per utils.get_absolute_path)
        raise FileNotFoundError(f"Invalid file path: {file_path}. Original error: {e}")

    file_system = DB.get("file_system", {})
    entry = file_system.get(abs_path)

    if not entry:
        raise FileNotFoundError(f"File not found at resolved path: {abs_path} (from input: {file_path})")
    if entry.get("is_directory", False):
        raise FileNotFoundError(f"Specified path is a directory, not a file: {abs_path}")

    # 3. Content and Permission Check
    content_lines = entry.get("content_lines")

    if not isinstance(content_lines, list):
        # This indicates an unexpected state in the DB; hydrate_db should ensure content_lines is a list.
        # Raising an error for unexpected DB state.
        raise RuntimeError(f"File entry for {abs_path} is malformed: 'content_lines' is not a list.")

    if content_lines == _PERMISSION_DENIED_MARKER:
        raise custom_errors.PermissionDeniedError(f"Permission denied to read file: {file_path}")

    # 4. Total Lines and Further Range Validation
    total_lines_in_file = len(content_lines)

    if start_line > total_lines_in_file and total_lines_in_file > 0 : # Allow start_line=1 for empty file if end_line is also 1 (or 0 effectively)
         raise custom_errors.InvalidLineRangeError(
            f"Start line ({start_line}) is beyond the total number of lines ({total_lines_in_file}) in file: {file_path}."
        )
    if start_line > total_lines_in_file and total_lines_in_file == 0 and start_line > 1: # Explicitly disallow start_line > 1 for empty file
        raise custom_errors.InvalidLineRangeError(
            f"Start line ({start_line}) is beyond the total number of lines (0) in file: {file_path}."
        )


    # 5. Determine Actual Slice and Content
    # Validations ensure: 1 <= start_line (conditionally for empty files), and start_line <= end_line.

    effective_1_based_start_line = start_line
    # For an empty file (total_lines_in_file == 0), if start_line is 1,
    # effective_1_based_end_line should become 0 to produce empty content.
    if total_lines_in_file == 0 and start_line == 1:
        effective_1_based_end_line = 0
    else:
        effective_1_based_end_line = min(end_line, total_lines_in_file)
        # Ensure start_line is not greater than the effective end line after clamping to total_lines.
        if effective_1_based_start_line > effective_1_based_end_line and total_lines_in_file > 0 :
             raise custom_errors.InvalidLineRangeError(
                f"Calculated start line ({effective_1_based_start_line}) is greater than effective end line ({effective_1_based_end_line}) after bounds check for file: {file_path}."
            )

    # Adjust slice indices for 0-based list access
    slice_idx_start = effective_1_based_start_line - 1
    slice_idx_end = effective_1_based_end_line

    selected_lines_list = []
    if slice_idx_start < slice_idx_end :
        selected_lines_list = content_lines[slice_idx_start:slice_idx_end]
    actual_content_str = "".join(selected_lines_list)

    # 6. Determine Returned `start_line`, `end_line` for the response
    response_actual_start_line = effective_1_based_start_line
    
    if not selected_lines_list :
        # If no lines were selected (e.g. empty file, or start_line > total_lines correctly handled now)
        # schema implies start_line/end_line should reflect what was effectively read.
        # If start_line was 1 for an empty file, end_line should be 0.
        response_actual_end_line = effective_1_based_start_line -1 if total_lines_in_file > 0 else 0
    else:
        response_actual_end_line = response_actual_start_line + len(selected_lines_list) - 1

    # 7. Truncation Flags
    is_truncated_at_top = (response_actual_start_line > 1)
    is_truncated_at_bottom = (response_actual_end_line < total_lines_in_file)

    # 8. Outline (Optional)
    # Attempt to retrieve outline if it exists in the file entry.
    outline_data = entry.get("outline")

    file_details = {
        "file_path": abs_path,
            "content": actual_content_str,
            "start_line": response_actual_start_line,
            "end_line": response_actual_end_line,
            "total_lines": total_lines_in_file,
            "is_truncated_at_top": is_truncated_at_top,
            "is_truncated_at_bottom": is_truncated_at_bottom,
            "outline": outline_data,
    }
    serialized_file_details = models.ReadFileResponse(**file_details).model_dump()
    return {
        "file_details": serialized_file_details
    }


@tool_spec(
    spec={
        'name': 'list_dir',
        'description': """ List the contents of a directory. Result will have the name of the child. If the name ends in /, it's a folder, otherwise a file.
        
        This function lists the contents of a specified directory. For each entry
        found, which represents a child item, its name is provided. A trailing
        slash ('/') in an entry's name indicates that the entry is a folder;
        otherwise, the entry is considered a file. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the directory whose contents are to be listed.'
                }
            },
            'required': [
                'path'
            ]
        }
    }
)
def list_dir(path: str) -> List[Dict[str, Any]]:
    """List the contents of a directory. Result will have the name of the child. If the name ends in /, it's a folder, otherwise a file.

    This function lists the contents of a specified directory. For each entry
    found, which represents a child item, its name is provided. A trailing
    slash ('/') in an entry's name indicates that the entry is a folder;
    otherwise, the entry is considered a file.

    Args:
        path (str): The path to the directory whose contents are to be listed.

    Returns:
        List[Dict[str, Any]]: A list of items found in the specified directory. Each item is a
            dictionary detailing a file or directory entry and includes the following
            keys:
            name (str): The name of the file or subdirectory. Directory names end
                with a '/' suffix.
            type (str): The type of the entry, either 'file' or 'directory'.
            path (str): The full path to the file or directory entry.

    Raises:
        DirectoryNotFoundError: If the specified directory path does not exist or is not a directory.
        InvalidInputError: If input arguments fail validation or path is invalid.
    """
    if not isinstance(path, str):
        # Validate that the input path is a string.
        raise custom_errors.InvalidInputError("Input path must be a string.")
    
    # Check for null bytes and other invalid characters in the path
    if '\x00' in path:
        raise custom_errors.InvalidInputError("Path contains null bytes, which are not allowed.")
    
    # Check for obvious path traversal attempts
    if '..' in path and path.count('..') > 2:  # Allow reasonable use of .. but block excessive traversal
        raise custom_errors.InvalidInputError("Path traversal attempt detected. Access denied.")

    try:
        # Resolve the input path to an absolute, normalized path.
        # This utility also checks if the path is within the configured workspace
        # and if the workspace itself is properly configured.
        abs_path = utils.get_absolute_path(path)
    except ValueError as e:
        error_message_str = str(e)
        # Map ValueErrors from get_absolute_path to appropriate error types
        if "outside the configured workspace root" in error_message_str:
            # Path traversal or access outside workspace should be InvalidInputError
            raise custom_errors.InvalidInputError(error_message_str) from e
        elif "Workspace root is not configured" in error_message_str:
            # This specific message is from the original code, maintain if no test contradicts.
            raise custom_errors.DirectoryNotFoundError(
                f"Cannot list directory: Workspace root is not configured."
            ) from e
        else:
            # Catch-all for other path resolution ValueErrors.
            raise custom_errors.DirectoryNotFoundError(
                 f"Invalid path '{path}': {error_message_str}" # Or simply str(e) if tests expect that
            ) from e

    # Check if the resolved path exists in the simulated file system.
    if not utils.path_exists(abs_path):
        raise custom_errors.DirectoryNotFoundError(
            f"Directory '{abs_path}' not found or is not a directory."
        )

    # Check if the resolved path points to a directory.
    if not utils.is_directory(abs_path):
        raise custom_errors.DirectoryNotFoundError(
            f"Path '{path}' (resolved to '{abs_path}') is not a directory."
        )

    # If all checks pass, proceed to list the directory contents.
    results: List[Dict[str, Any]] = []
    file_system_view = DB.get("file_system", {})

    for item_full_path, item_entry_data in file_system_view.items():
        if item_full_path == abs_path:
            # Do not include the directory itself in its list of children.
            continue

        # A file system entry is a direct child if its parent directory is abs_path.
        # os.path.dirname is used on normalized paths.
        if os.path.dirname(item_full_path) == abs_path:
            base_name = os.path.basename(item_full_path)
            is_directory_type = item_entry_data.get("is_directory", False)
            
            entry_type_str = "directory" if is_directory_type else "file"
            # Append a trailing slash to directory names as per requirements.
            display_name = base_name + "/" if is_directory_type else base_name
            
            results.append(models.DirectoryEntry(
                name=display_name,
                type=entry_type_str,
                path=item_full_path
            ).model_dump())
            
    # Sort the results by name for a consistent and predictable listing order.
    results.sort(key=lambda entry: entry["name"])
            
    return results


@tool_spec(
    spec={
        'name': 'insert_edit_into_file',
        'description': """ Insert new code into an existing file in the workspace.
        
        Inserts new code into an existing file in the workspace. This function is used
        once per file that needs modification, even if there are multiple changes for
        that file. The `explanation` property should be generated first. The system
        intelligently applies edits based on minimal hints. It is important to avoid
        repeating existing code in the `edit_instructions`; instead, comments
        (e.g., `// ...existing code...`) represent regions of unchanged code,
        aiming for conciseness. For example:
        // ...existing code...
        { changed code }
        // ...existing code...
        { changed code }
        // ...existing code...
        
        An example of how to format an edit to an existing `Person` class:
        class Person {
            // ...existing code...
            age: number;
            // ...existing code...
            getAge() {
                return this.age;
            }
        } """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The path of the file within the workspace that needs to be modified.'
                },
                'edit_instructions': {
                    'type': 'string',
                    'description': "The content representing the changes to be applied to the file. Follow the concise diff-like format: use comments (e.g., '// ...existing code...') to represent regions of unchanged code and provide only the new or modified code blocks."
                },
                'explanation': {
                    'type': 'string',
                    'description': 'A natural language explanation of the changes being made in this edit. This should be generated first.'
                }
            },
            'required': [
                'file_path',
                'edit_instructions',
                'explanation'
            ]
        }
    }
)
def insert_edit_into_file(file_path: str, edit_instructions: str, explanation: str) -> Dict[str, Any]: 
    """Insert new code into an existing file in the workspace.

    Inserts new code into an existing file in the workspace. This function is used
    once per file that needs modification, even if there are multiple changes for
    that file. The `explanation` property should be generated first. The system
    intelligently applies edits based on minimal hints. It is important to avoid
    repeating existing code in the `edit_instructions`; instead, comments
    (e.g., `// ...existing code...`) represent regions of unchanged code,
    aiming for conciseness. For example:
    // ...existing code...
    { changed code }
    // ...existing code...
    { changed code }
    // ...existing code...

    An example of how to format an edit to an existing `Person` class:
    class Person {
        // ...existing code...
        age: number;
        // ...existing code...
        getAge() {
            return this.age;
        }
    }

    Args:
        file_path (str): The path of the file within the workspace that needs to be modified.
        edit_instructions (str): The content representing the changes to be applied to the file. Follow the concise diff-like format: use comments (e.g., '// ...existing code...') to represent regions of unchanged code and provide only the new or modified code blocks.
        explanation (str): A natural language explanation of the changes being made in this edit. This should be generated first.

    Returns:
        Dict[str, Any]: A dictionary containing the result, with keys:
            file_path (str): The absolute path of the file that was targeted.
            status (str): Status of the edit operation (e.g., 'success', 'failed_to_apply', 'file_not_found').
            message (Optional[str]): Details of the operation or error.

    Raises:
        EditConflictError: If the target path is a directory, or content is an uneditable placeholder.
        PermissionDeniedError: If the file is marked read-only.
        InvalidEditFormatError: Conditions for this are less direct with LLM-based rewrite.
                                It might be raised if, hypothetically, an LLM output format was strictly defined
                                and not met in a way that other errors don't cover. Currently, LLM content
                                issues are typically mapped to 'failed_to_apply' or are part of a 'success'
                                if the content is merely low quality but technically applied.
    """
    original_input_file_path = file_path

    # 1. Input Validation
    if not file_path or not isinstance(file_path, str):
        return models.EditFileResult(
            file_path=str(original_input_file_path),
            status="failed_to_apply",
            message="Input Validation Error: file_path must be a non-empty string."
        ).model_dump()
    if not isinstance(edit_instructions, str):
        return models.EditFileResult(
            file_path=original_input_file_path,
            status="failed_to_apply",
            message="Input Validation Error: edit_instructions must be a string."
        ).model_dump()
    if not explanation or not isinstance(explanation, str):
        return models.EditFileResult(
            file_path=original_input_file_path,
            status="failed_to_apply",
            message="Input Validation Error: explanation must be a non-empty string."
        ).model_dump()

    abs_path: str
    try:
        abs_path = utils.get_absolute_path(file_path)
    except ValueError as e:
        return models.EditFileResult(
            file_path=original_input_file_path,
            status="failed_to_apply",
            message=f"Input Validation Error: Invalid file_path '{original_input_file_path}': {str(e)}"
        ).model_dump()

    # 2. File System Checks
    if not utils.path_exists(abs_path):
        return models.EditFileResult(
            file_path=abs_path,
            status="file_not_found",
            message=f"Target file '{file_path}' (resolved to '{abs_path}') not found."
        ).model_dump()

    file_entry = utils.get_file_system_entry(abs_path)
    if not file_entry:
        return models.EditFileResult(
            file_path=abs_path,
            status="file_not_found",
            message=f"Internal error: File entry for '{abs_path}' not found after existence check."
        ).model_dump()

    if file_entry.get("is_directory", False):
        raise custom_errors.EditConflictError(
            f"Target path '{file_path}' (resolved to '{abs_path}') is a directory, not a file."
        )

    if file_entry.get("is_readonly", False):
        raise custom_errors.PermissionDeniedError(
            f"File '{file_path}' (resolved to '{abs_path}') is read-only."
        )

    original_content_lines: list[str] = file_entry.get("content_lines", [])
    uneditable_reason = utils._is_content_uneditable_placeholder(original_content_lines)
    if uneditable_reason:
        raise custom_errors.EditConflictError(
            f"Cannot edit file '{file_path}' (resolved to '{abs_path}'): existing content is unreadable or a placeholder ({uneditable_reason})."
        )
    
    original_content_str = "".join(original_content_lines)

    # 3. Construct LLM Prompt for Full File Rewrite
    prompt = f"""You are an expert AI code editor. Your task is to rewrite the entire content of a file based on its original content and a set of instructions.

Original file path: '{abs_path}'

---BEGIN ORIGINAL FILE CONTENT---
{original_content_str}
---END ORIGINAL FILE CONTENT---

Apply the following changes:

Explanation of desired changes:
{explanation}

Detailed edit instructions/hints (interpret these to achieve the changes described in the explanation):
---BEGIN EDIT INSTRUCTIONS---
{edit_instructions}
---END EDIT INSTRUCTIONS---

Your goal is to generate the complete, new file content after applying all specified changes.
- Ensure that parts of the file not affected by the explanation or edit instructions are preserved perfectly.
- Pay close attention to maintaining correct syntax, indentation, and overall code quality or file structure.
- If the request implies deleting all content (e.g., "make the file empty"), output an empty response. If the request is to delete the file itself, that's a different operation; for this task, output empty content if the file should become empty.

Output ONLY the complete new file content. Do not include any preamble, additional explanations, comments about your changes, markdown code fences, or diff formats.
"""
    logger.debug(f"LLM prompt for file rewrite of '{abs_path}': First 500 chars: {prompt[:500]}...")


    # 4. Call LLM
    new_full_content_str: str
    try:
        new_full_content_str = call_llm(
            prompt_text=prompt,
            model_name="gemini-2.5-flash",
            temperature=0.1,
            timeout_seconds=300
        )
        if new_full_content_str is not None:
            new_full_content_str = utils.strip_code_fences_from_llm(new_full_content_str)
        else: 
            new_full_content_str = "" # Should ideally be caught by RuntimeError from call_llm if no usable text

        logger.info(f"LLM generated new content for '{abs_path}'. Length: {len(new_full_content_str)}. Preview: '{new_full_content_str[:200]}...'")

    except ValueError as e: 
        logger.error(f"LLM configuration error for '{abs_path}': {str(e)}")
        return models.EditFileResult(
            file_path=abs_path,
            status="failed_to_apply",
            message=f"Failed to apply edit: LLM interface configuration error - {str(e)}"
        ).model_dump()
    except RuntimeError as e: 
        logger.error(f"LLM call failed for '{abs_path}': {str(e)}")
        return models.EditFileResult(
            file_path=abs_path,
            status="failed_to_apply",
            message=f"Failed to apply edit: LLM generation failed - {str(e)}"
        ).model_dump()
    except Exception as e: 
        logger.error(f"Unexpected error during LLM processing for '{abs_path}': {str(e)}", exc_info=True)
        return models.EditFileResult(
            file_path=abs_path,
            status="failed_to_apply",
            message=f"Failed to apply edit: An unexpected error occurred during LLM interaction - {str(e)}"
        ).model_dump()

    # 5. Normalize lines from LLM output (which is now a string)
    if not new_full_content_str: 
        new_content_lines = []
    else:
        temp_lines = new_full_content_str.splitlines()
        new_content_lines = utils._normalize_lines(temp_lines, ensure_trailing_newline=True)

    # 6. Update File in DB
    file_entry["content_lines"] = new_content_lines
    file_entry["size_bytes"] = utils.calculate_size_bytes(new_content_lines)
    file_entry["last_modified"] = utils.get_current_timestamp_iso()
    
    return models.EditFileResult(
        file_path=abs_path, 
        status="success",
        message=f"LLM successfully rewrote file '{file_path}' (resolved to '{abs_path}'). Explanation: {explanation}"
    ).model_dump()