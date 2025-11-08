from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
"""
Code Quality and Version Control module for Copilot API.
Provides functions for code quality and version control operations.
"""
import os
from typing import Any
from typing import Dict, List

from copilot.SimulationEngine import custom_errors, utils
from copilot.SimulationEngine.utils import (_get_mock_python_errors, _get_mock_javascript_errors,
                                            _get_mock_typescript_errors, _get_mock_json_errors)
from copilot.command_line import run_in_terminal
from .SimulationEngine.utils import quote_path_if_needed


@tool_spec(
    spec={
        'name': 'get_errors',
        'description': """ Get any compile or lint errors in a code file.
        
        If a user mentions errors or problems in a file, they may be referring to
        these compile or lint errors. This function allows seeing the same errors
        that the user is seeing. It is also used after editing a file to validate
        the change. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The path to the code file to analyze for errors.'
                }
            },
            'required': [
                'file_path'
            ]
        }
    }
)
def get_errors(file_path: str) -> List[Dict[str, Any]]:
    """Get any compile or lint errors in a code file.

    If a user mentions errors or problems in a file, they may be referring to
    these compile or lint errors. This function allows seeing the same errors
    that the user is seeing. It is also used after editing a file to validate
    the change.

    Args:
        file_path (str): The path to the code file to analyze for errors.

    Returns:
        List[Dict[str, Any]]: A list of compile or lint errors found in the
            specified code file. Each dictionary in the list represents an
            error and contains the following keys:
            file_path (str): The path to the file where the error occurred.
            line_number (int): The line number (1-based) where the error
                is located.
            column_number (Optional[int]): The column number (1-based) where
                the error starts, if available.
            message (str): The descriptive error message provided by the
                compiler or linter.
            severity (str): The severity of the issue (e.g., 'error',
                'warning', 'info').
            code (Optional[str]): An optional error code or identifier
                (e.g., 'E0425', 'eslint(no-unused-vars)').
            source (Optional[str]): The source of the error (e.g., 'compiler',
                'linter:eslint', 'typescript-language-server').

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        ToolConfigurationError: If the linter, compiler, or language server
            required to get errors is not configured correctly, not found,
            or fails to run.
        AnalysisFailedError: If analysis of the file could not be completed
            for other reasons.
        ValidationError: If input arguments fail validation.
    """
    # Validate input type early for better error messages
    if not isinstance(file_path, str):
        raise custom_errors.ValidationError("File path must be a string.")

    if not file_path:
        raise custom_errors.ValidationError("File path cannot be empty.")

    try:
        file_path_abs = utils.get_absolute_path(file_path)
    except ValueError as e:
        # Path is outside workspace or otherwise invalid for get_absolute_path
        raise custom_errors.FileNotFoundError(
            f"File path is invalid or outside the workspace: {file_path}. Detail: {e}")

    file_entry = utils.get_file_system_entry(file_path_abs)

    if file_entry is None:
        # This will catch cases where get_absolute_path succeeds but the file isn't in DB
        raise custom_errors.FileNotFoundError(f"File not found: {file_path_abs}")

    if file_entry.get("is_directory", False):
        raise custom_errors.AnalysisFailedError(f"Path is a directory, not a file: {file_path_abs}")

    content_lines = file_entry.get("content_lines", [])

    # Check if content is a placeholder indicating it's unanalyzable
    # The utils._is_content_uneditable_placeholder helper checks for binary, large file, or read error placeholders.
    uneditable_reason = utils._is_content_uneditable_placeholder(content_lines)
    if uneditable_reason is not None:
        raise custom_errors.AnalysisFailedError(
            f"Cannot analyze file {file_path}: content {uneditable_reason}."
        )

    # --- START FIX: Prioritize simulated_diagnostics from DB ---
    # If simulated_diagnostics exist for this file, return them directly.
    # This allows tests to pre-define errors without triggering mock generation.
    simulated_diagnostics = file_entry.get("simulated_diagnostics")
    if simulated_diagnostics is not None:
        if simulated_diagnostics == "TOOL_CONFIG_ERROR":
            raise custom_errors.ToolConfigurationError(
                f"Tool configuration error for file: {file_path_abs}"
            )
        elif simulated_diagnostics == "ANALYSIS_FAILED_ERROR":
            raise custom_errors.AnalysisFailedError(
                f"Analysis failed for file: {file_path_abs}"
            )
        return simulated_diagnostics

    errors: List[Dict[str, Any]] = []
    _, file_ext_lower = os.path.splitext(file_path_abs)
    file_ext_lower = file_ext_lower.lower()

    # Dispatch to specific mock error generators based on file extension
    try:
        if file_ext_lower == ".py":
            py_errors = _get_mock_python_errors(file_path_abs, content_lines)
            if py_errors is not None:  # Make sure errors list is not None
                errors.extend(py_errors)
        elif file_ext_lower == ".js":
            js_errors = _get_mock_javascript_errors(file_path_abs, content_lines)
            if js_errors is not None:  # Make sure errors list is not None
                errors.extend(js_errors)
        elif file_ext_lower == ".ts":
            ts_errors = _get_mock_typescript_errors(file_path_abs, content_lines)
            if ts_errors is not None:  # Make sure errors list is not None
                errors.extend(ts_errors)
        elif file_ext_lower == ".json":
            json_errors = _get_mock_json_errors(file_path_abs, content_lines)
            if json_errors is not None:  # Make sure errors list is not None
                errors.extend(json_errors)
        else:
            # For extensions not explicitly handled, check if they are known code/lintable types
            # for which a tool might be expected.
            general_lintable_extensions = {
                ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rb", ".php", ".swift", ".kt",
                ".xml", ".yaml", ".yml", ".html", ".htm", ".css", ".scss", ".less", ".md",
                ".sh", ".bash", ".ps1", ".R", ".sql", ".pl", ".lua"
            }
            # Extensions for which we have specific handlers above
            handled_extensions = {".py", ".js", ".ts", ".json"}

            if file_ext_lower in general_lintable_extensions and file_ext_lower not in handled_extensions:
                # Don't catch this specific error - let it propagate to the caller
                raise custom_errors.ToolConfigurationError(
                    f"No linter or compiler is configured in this environment for file type '{file_ext_lower}'."
                )
    except custom_errors.ToolConfigurationError:
        # Re-raise ToolConfigurationError to ensure it's properly propagated
        raise
    except Exception as e:
        # If any other error happens during error detection, log it but return what we have so far
        # This ensures the function is resilient against internal errors
        print_log(f"Warning: Error occurred during error detection: {str(e)}")
    
    # Always return a list (empty or with errors)
    return errors


@tool_spec(
    spec={
        'name': 'get_changed_files',
        'description': """ Get git diffs of current file changes in the active git repository.
        
        This function retrieves git diffs for current file changes within the
        active git repository. For each changed file, it provides its path,
        status (e.g., 'modified', 'added', 'deleted', 'renamed', 'copied'),
        the diff output in unified format, and the original path if the file
        was renamed or copied. It is also noted that `run_in_terminal` can be
        used to execute git commands. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_changed_files() -> List[Dict[str, Any]]:
    """Get git diffs of current file changes in the active git repository.

    This function retrieves git diffs for current file changes within the
    active git repository. For each changed file, it provides its path,
    status (e.g., 'modified', 'added', 'deleted', 'renamed', 'copied'),
    the diff output in unified format, and the original path if the file
    was renamed or copied. It is also noted that `run_in_terminal` can be
    used to execute git commands.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
            represents a changed file in the active git repository and its
            diff. Each dictionary includes the following keys:
            file_path (str): The path to the changed file relative to the
                repository root.
            status (str): The status of the file (e.g., 'modified', 'added',
                'deleted', 'renamed', 'copied').
            diff_hunks (str): The diff output for the file in unified diff
                format, showing changes. Empty for added binary files or if
                diff is not applicable.
            old_file_path (Optional[str]): If the file was renamed or copied,
                this is the original path. Null otherwise.

    Raises:
        GitRepositoryNotFoundError: If the current workspace is not a git
            repository, or git command is not found.
        GitCommandError: If there is an error executing the underlying git
            diff command (e.g., due to merge conflicts, corrupted
            repository).
    """
    # 1. Check if it's a git repository and git is available
    try:
        rev_parse_cmd = "git rev-parse --is-inside-work-tree"
        rev_parse_result = run_in_terminal(rev_parse_cmd)
    except custom_errors.CommandExecutionError:
        raise custom_errors.GitRepositoryNotFoundError(
            "Git command not found or failed to execute. Ensure git is installed and in PATH."
        )

    if rev_parse_result['exit_code'] != 0:
        # stderr might contain useful info, e.g., "fatal: not a git repository"
        error_detail = rev_parse_result['stderr'].strip()
        raise custom_errors.GitRepositoryNotFoundError(
            f"Failed to confirm git repository status. Git command error: {error_detail if error_detail else 'Unknown error'}"
        )

    if rev_parse_result['stdout'].strip().lower() != "true":
        raise custom_errors.GitRepositoryNotFoundError("The current workspace is not a git repository.")

    name_status_cmd = "git diff --name-status --unified=0 HEAD"
    try:
        status_result = run_in_terminal(name_status_cmd)
    except custom_errors.CommandExecutionError:
        # This exception from run_in_terminal implies the command could not be started.
        raise custom_errors.GitCommandError(
            f"Error executing '{name_status_cmd}': Git command failed to start, though previously available."
        )

    if status_result['exit_code'] != 0:
        raise custom_errors.GitCommandError(
            f"Error executing '{name_status_cmd}': {status_result['stderr'].strip()}"
        )

    changed_files_intermediate = []
    status_output_lines = status_result['stdout'].splitlines()

    for line in status_output_lines:
        if not line.strip():
            continue

        parts = line.split('\t')
        if not parts:
            continue

        status_code_full = parts[0]
        if not status_code_full:
            continue
        status_char = status_code_full[0]  # e.g., 'R' from 'R085', 'M' from 'M'

        file_path_details = {'file_path': None, 'old_file_path': None, 'status': None}

        if status_char == 'M':
            if len(parts) >= 2:
                file_path_details['status'] = 'modified'
                file_path_details['file_path'] = parts[1]
        elif status_char == 'A':
            if len(parts) >= 2:
                file_path_details['status'] = 'added'
                file_path_details['file_path'] = parts[1]
        elif status_char == 'D':
            if len(parts) >= 2:
                file_path_details['status'] = 'deleted'
                file_path_details['file_path'] = parts[1]
        elif status_char == 'R':  # Renamed
            if len(parts) >= 3:
                file_path_details['status'] = 'renamed'
                file_path_details['old_file_path'] = parts[1]
                file_path_details['file_path'] = parts[2]
        elif status_char == 'C':  # Copied
            if len(parts) >= 3:
                file_path_details['status'] = 'copied'
                file_path_details['old_file_path'] = parts[1]
                file_path_details['file_path'] = parts[2]
        # Other statuses like 'T' (type change), 'U' (unmerged) are ignored as per current handling.

        if file_path_details['status'] and file_path_details['file_path']:
            changed_files_intermediate.append(file_path_details)

    # 3. Get diffs for each identified file
    result_list: List[Dict[str, Any]] = []
    for entry in changed_files_intermediate:
        # Path for diff command is the new path for R/C, or the path for M/A/D.
        # For deleted files, this is the path that was deleted.
        path_for_diff_command = entry['file_path']
        quoted_path_for_cmd = quote_path_if_needed(path_for_diff_command)

        diff_cmd = f"git diff --unified=0 HEAD -- {quoted_path_for_cmd}"

        try:
            diff_result = run_in_terminal(diff_cmd)
        except custom_errors.CommandExecutionError:
            # This exception from run_in_terminal implies the command could not be started.
            raise custom_errors.GitCommandError(
                f"Error executing '{diff_cmd}': Git command failed to start."
            )

        if diff_result['exit_code'] not in [0, 1]:
            raise custom_errors.GitCommandError(
                f"Error executing '{diff_cmd}': {diff_result['stderr'].strip()}"
            )

        diff_hunks_str = diff_result['stdout']

        if diff_hunks_str.startswith("Binary files ") and diff_hunks_str.endswith(" differ\n"):
            diff_hunks_str = ""

        result_list.append({
            "file_path": entry['file_path'],
            "status": entry['status'],
            "diff_hunks": diff_hunks_str,
            "old_file_path": entry['old_file_path']
        })

    return result_list
