"""
Code Intelligence module for Copilot API.
Provides functions for code search and analysis.
"""

from common_utils.tool_spec_decorator import tool_spec
import logging
import os
import re
from typing import List, Dict, Any

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine import utils
from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine.utils import (MAX_FILES_FOR_SMALL_WORKSPACE, MAX_FILE_SIZE_BYTES,
                                            MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE,
                                            MAX_LLM_CONTENT_CHARS_PER_FILE)


@tool_spec(
    spec={
        'name': 'semantic_search',
        'description': """ Run a natural language search for relevant code or documentation comments from the user's current workspace.
        
        This function runs a natural language search for relevant code or documentation comments
        from the user's current workspace. It returns relevant code snippets from the
        user's current workspace if it is large, or the full contents of the workspace
        if it is small. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The natural language query string to search for.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def semantic_search(query: str) -> List[Dict[str, Any]]:
    """Run a natural language search for relevant code or documentation comments from the user's current workspace.

    This function runs a natural language search for relevant code or documentation comments
    from the user's current workspace. It returns relevant code snippets from the
    user's current workspace if it is large, or the full contents of the workspace
    if it is small.

    Args:
        query (str): The natural language query string to search for.

    Returns:
        List[Dict[str, Any]]: A list of relevant code snippets or documentation segments
            from the user's workspace.
            If the workspace is determined to be small, this list may represent the
            full content of all files, with each file treated as a single snippet.
            Each dictionary in the list represents a search result and contains the
            following keys:
            file_path (str): The path to the file containing the relevant snippet.
            snippet (str): The relevant code or documentation snippet.
            start_line (int): The starting line number of the snippet in the file (1-indexed).
            end_line (int): The ending line number of the snippet in the file (inclusive).
            relevance_score (Optional[float]): A score indicating the relevance of the
                snippet (e.g., from a vector search). This may not be available or
                applicable for all results, especially if returning full file contents
                from a small workspace.

    Raises:
        WorkspaceNotAvailableError: If the user's workspace cannot be accessed or is not yet indexed.
        SearchFailedError: If the search operation fails for an unexpected reason.
        ValidationError: If input arguments fail validation.
    """
    if not query or not isinstance(query, str):
        raise custom_errors.ValidationError("Query must be a non-empty string.")

    file_system = DB.get("file_system")
    workspace_root = DB.get("workspace_root")

    if not workspace_root:
        raise custom_errors.WorkspaceNotAvailableError(
            "Workspace root is not configured. Workspace may not be initialized."
        )
    if not file_system:  # Catches None or empty dictionary
        raise custom_errors.WorkspaceNotAvailableError(
            "Workspace file system is not available or empty. Workspace may not be indexed."
        )

    eligible_files_metadata = []
    total_content_size_bytes = 0
    num_text_files = 0

    for path, entry in file_system.items():
        if entry.get("is_directory", False):
            continue

        try:
            if not os.path.isabs(path):
                utils._log_util_message(logging.WARNING, f"File path '{path}' in DB is not absolute. Skipping.")
                continue
            if not path.startswith(workspace_root):  # Basic check
                utils._log_util_message(logging.WARNING,
                                        f"File path '{path}' seems outside workspace root '{workspace_root}'. Skipping.")
                continue
            relative_path = os.path.relpath(path, workspace_root)
        except ValueError:
            utils._log_util_message(logging.WARNING,
                                    f"Could not determine relative path for '{path}' against root '{workspace_root}'. Skipping.")
            continue

        if utils.is_path_excluded_for_search(
                relative_path,
                utils.DEFAULT_IGNORE_DIRS,
                utils.DEFAULT_IGNORE_FILE_PATTERNS
        ):
            continue

        content_lines = entry.get("content_lines", [])
        if (content_lines == utils.BINARY_CONTENT_PLACEHOLDER or
                content_lines == utils.LARGE_FILE_CONTENT_PLACEHOLDER or
                content_lines == utils.ERROR_READING_CONTENT_PLACEHOLDER):
            continue

        if content_lines is None:
            content_lines = []

        num_text_files += 1
        total_content_size_bytes += entry.get("size_bytes", utils.calculate_size_bytes(content_lines))
        eligible_files_metadata.append(entry)

    is_small_workspace = (num_text_files < MAX_FILES_FOR_SMALL_WORKSPACE and
                          total_content_size_bytes < MAX_FILE_SIZE_BYTES)

    results: List[Dict[str, Any]] = []

    if is_small_workspace:
        utils._log_util_message(logging.INFO,
                                "Workspace determined as small. Returning full file contents for eligible files.")
        for entry in eligible_files_metadata:
            content_lines = entry.get("content_lines", [])
            if not content_lines:
                continue  # Skip empty files

            snippet_text = "".join(content_lines)
            num_lines = len(content_lines)

            results.append({
                "file_path": entry["path"],
                "snippet": snippet_text,
                "start_line": 1,
                "end_line": num_lines,
                "relevance_score": None
            })
    else:
        utils._log_util_message(logging.INFO,
                                f"Workspace determined as large ({num_text_files} files, {total_content_size_bytes} bytes). Performing LLM-based snippet search.")

        files_to_process = eligible_files_metadata
        if len(eligible_files_metadata) > MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE:
            utils._log_util_message(logging.WARNING,
                                    f"Workspace has {len(eligible_files_metadata)} eligible files. "
                                    f"Processing up to {MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE} for semantic search due to size."
                                    )

            files_to_process = eligible_files_metadata[:MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE]

        for entry in files_to_process:
            original_full_content_lines = entry.get("content_lines", [])
            if not original_full_content_lines:
                continue

            file_content_full = "".join(original_full_content_lines)
            if not file_content_full.strip():  # Skip if file is effectively empty (only whitespace)
                continue

            if len(file_content_full) > MAX_LLM_CONTENT_CHARS_PER_FILE:
                content_for_llm_str = file_content_full[:MAX_LLM_CONTENT_CHARS_PER_FILE] + "\n... [CONTENT TRUNCATED]"
            else:
                content_for_llm_str = file_content_full

            numbered_content_list = utils.add_line_numbers(content_for_llm_str.splitlines(keepends=True))
            numbered_content_for_llm = "".join(numbered_content_list)

            prompt = f"""You are a code analysis assistant.
            User Query: "{query}"
            File Path: "{entry['path']}"
            
            File Content (with 1-indexed line numbers shown):
            ---
            {numbered_content_for_llm}
            ---
            
            Analyze the provided File Content based on the User Query.
            If the File Content is relevant to the User Query, identify the start line and end line (inclusive, 1-indexed, relative to the original file lines as represented in the provided content) of the single most relevant continuous code or documentation snippet. Also provide a relevance score between 0.0 (not relevant at all) and 1.0 (highly relevant).
            If multiple snippets are equally relevant, choose the first one that appears in the file.
            The snippet should be concise yet informative. Aim for snippets of approximately 5-15 lines, but adjust as necessary to capture a meaningful segment.
            
            Respond in one of the following formats ONLY:
            1. If relevant: RELEVANT: START_LINE,END_LINE,SCORE
               Example: RELEVANT: 15,25,0.85
            2. If not relevant: NOT_RELEVANT
            
            Your response:"""

            try:
                llm_response_raw = utils.call_llm(prompt, temperature=0.1, timeout_seconds=45)
                response_text = llm_response_raw.strip().upper()

                if response_text == "NOT_RELEVANT":
                    continue

                if response_text.startswith("RELEVANT:"):
                    parts_str = response_text[len("RELEVANT:"):].strip()
                    try:
                        start_line_str, end_line_str, score_str = parts_str.split(',')
                        start_line = int(start_line_str.strip())
                        end_line = int(end_line_str.strip())
                        relevance_score = float(score_str.strip())

                        if not (0.0 <= relevance_score <= 1.0):
                            utils._log_util_message(logging.WARNING,
                                                    f"LLM returned invalid relevance score {relevance_score} for {entry['path']}. Response: '{llm_response_raw}'. Skipping.")
                            continue
                        if start_line <= 0 or end_line < start_line:
                            utils._log_util_message(logging.WARNING,
                                                    f"LLM returned invalid line numbers ({start_line}-{end_line}) for {entry['path']}. Response: '{llm_response_raw}'. Skipping.")
                            continue

                        max_lines_in_file = len(original_full_content_lines)
                        if start_line > max_lines_in_file:
                            utils._log_util_message(logging.WARNING,
                                                    f"LLM returned start_line {start_line} > max_lines {max_lines_in_file} for {entry['path']}. Response: '{llm_response_raw}'. Skipping.")
                            continue

                        end_line = min(end_line, max_lines_in_file)
                        if start_line > end_line:  # Re-check after end_line adjustment
                            utils._log_util_message(logging.WARNING,
                                                    f"LLM returned/adjusted to invalid line range ({start_line}-{end_line}) for {entry['path']}. Response: '{llm_response_raw}'. Skipping.")
                            continue

                        snippet_lines = original_full_content_lines[start_line - 1:end_line]
                        snippet_text = "".join(snippet_lines)

                        results.append({
                            "file_path": entry["path"],
                            "snippet": snippet_text,
                            "start_line": start_line,
                            "end_line": end_line,
                            "relevance_score": relevance_score
                        })

                    except ValueError:  # Catch errors from int(), float(), or split(',')
                        utils._log_util_message(logging.WARNING,
                                                f"Could not parse LLM 'RELEVANT' response: '{llm_response_raw}' for file {entry['path']}. Skipping.")
                        continue
                else:
                    utils._log_util_message(logging.WARNING,
                                            f"Unexpected LLM response format: '{llm_response_raw}' for file {entry['path']}. Skipping.")

            except RuntimeError as e:
                utils._log_util_message(logging.WARNING,
                                        f"LLM call failed for file {entry['path']} during semantic search: {e}. Skipping this file.")
            except Exception as e:
                utils._log_util_message(logging.ERROR,
                                        f"Unexpected error processing file {entry['path']} for semantic search: {e}",
                                        exc_info=True)
                raise custom_errors.SearchFailedError(
                    f"Unexpected error during semantic search for file {entry['path']}: {str(e)}")

        if results:
            results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)

    return results


@tool_spec(
    spec={
        'name': 'list_code_usages',
        'description': """ Requests to list all usages (references, definitions, implementations etc) of a function, class, method, variable etc.
        
        This function lists all usages (e.g., references, definitions, implementations) of a specified code symbol such as a function, class, method, or variable.
        It is used for purposes such as:
        1. Looking for a sample implementation of an interface or class.
        2. Checking how a function is used throughout the codebase.
        3. Including and updating all usages when changing a function, method, or constructor. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The absolute path to the file containing the symbol for which usages are to be found.'
                },
                'line_number': {
                    'type': 'integer',
                    'description': "The 1-based line number in the specified file where the symbol is located. This typically refers to the start of the symbol's identifier."
                },
                'column_number': {
                    'type': 'integer',
                    'description': "The 1-based column number (character offset) on the line in the specified file where the symbol is located. This typically refers to the start of the symbol's identifier."
                }
            },
            'required': [
                'file_path',
                'line_number',
                'column_number'
            ]
        }
    }
)
def list_code_usages(file_path: str, line_number: int, column_number: int) -> List[Dict[str, Any]]:
    """Requests to list all usages (references, definitions, implementations etc) of a function, class, method, variable etc.

    This function lists all usages (e.g., references, definitions, implementations) of a specified code symbol such as a function, class, method, or variable.
    It is used for purposes such as:
    1. Looking for a sample implementation of an interface or class.
    2. Checking how a function is used throughout the codebase.
    3. Including and updating all usages when changing a function, method, or constructor.

    Args:
        file_path (str): The absolute path to the file containing the symbol for which usages are to be found.
        line_number (int): The 1-based line number in the specified file where the symbol is located. This typically refers to the start of the symbol's identifier.
        column_number (int): The 1-based column number (character offset) on the line in the specified file where the symbol is located. This typically refers to the start of the symbol's identifier.

    Returns:
        List[Dict[str, Any]]: A list of code usages found for the specified symbol. Each dictionary in the list represents a single usage and includes the following keys:
            file_path (str): The path to the file where the usage is found.
            start_line (int): The 1-based starting line number of the usage in the file.
            end_line (int): The 1-based ending line number of the usage in the file.
            start_column (Optional[int]): The 1-based starting column number (character offset) of the usage. Null if this information is not available or not applicable.
            end_column (Optional[int]): The 1-based ending column number (character offset) of the usage. Null if this information is not available or not applicable.
            usage_type (str): The type of code usage (e.g., 'reference', 'definition', 'implementation').
            snippet (str): A short code snippet (typically one or a few lines) illustrating the usage in its context.

    Raises:
        SymbolNotFoundError: If no symbol is found at the specified 'file_path', 'line_number', and 'column_number', or if the identified element is not a symbol for which usages can be determined (e.g., a comment).
        IndexingNotCompleteError: If the codebase is not yet fully indexed, preventing usage lookups. The client may retry after a delay.
        InvalidInputError: If 'file_path', 'line_number', or 'column_number' are missing, malformed (e.g., non-existent file path, non-positive line/column numbers), or point to a location outside the bounds of the file content.
        ProjectConfigurationError: If there is an issue with the project configuration that prevents resolving the file path.
    """
    # 1. Initial Input Validation
    if not file_path:
        raise custom_errors.InvalidInputError("File path cannot be empty.")
    if not isinstance(line_number, int) or line_number <= 0:
        raise custom_errors.InvalidInputError("Line number must be positive.")
    if not isinstance(column_number, int) or column_number <= 0:
        raise custom_errors.InvalidInputError("Column number must be positive.")

    # 1.5 Check for relative path when cwd is not configured
    if not os.path.isabs(file_path) and 'cwd' not in DB:
        raise custom_errors.InvalidInputError("Current working directory is not configured.")

    # 2. Path Normalization and File Existence/Type Validation
    try:
        abs_file_path = utils.get_absolute_path(file_path)
    except ValueError as e:
        raise custom_errors.ProjectConfigurationError(str(e)) from e

    file_entry = utils.get_file_system_entry(abs_file_path)
    if not file_entry:
        raise custom_errors.InvalidInputError(f"File not found: {abs_file_path}")
    if file_entry.get("is_directory", False):
        raise custom_errors.InvalidInputError(f"Path is a directory, not a file: {abs_file_path}")

    content_lines = file_entry.get("content_lines", [])
    if not isinstance(content_lines, list):
        raise custom_errors.InvalidInputError(f"File content is not in expected format: {abs_file_path}")

    # 3. Validate line and column numbers
    num_lines = len(content_lines)
    if num_lines == 0:
        raise custom_errors.InvalidInputError(
            f"Line number {line_number} is out of bounds for file {abs_file_path} (0 lines).")
    if line_number > num_lines:
        raise custom_errors.InvalidInputError(
            f"Line number {line_number} is out of bounds for file {abs_file_path} ({num_lines} lines).")

    line_content = content_lines[line_number - 1]
    line_length = len(line_content.rstrip('\n'))
    if column_number > line_length:
        raise custom_errors.InvalidInputError(
            f"Column number {column_number} is out of bounds for line {line_number} in file {abs_file_path} (length {line_length}).")

    # 4. Check Indexing Status
    if DB.get('code_indexing_status') != 'complete':
        raise custom_errors.IndexingNotCompleteError("Codebase indexing is not yet complete. Please try again later.")

    # 5. Get symbol usages from index
    code_symbols_index = DB.get('code_symbols_index', {})
    if abs_file_path not in code_symbols_index:
        raise custom_errors.SymbolNotFoundError(f"No symbol data available for file {abs_file_path}.")

    # 6. Find the symbol at the given location
    symbol_key = f"{line_number}:{column_number}"
    if symbol_key not in code_symbols_index[abs_file_path]:
        # Check if the location is a comment or whitespace
        line_content = content_lines[line_number - 1]
        if line_content.strip().startswith('#'):
            raise custom_errors.SymbolNotFoundError(
                f"Element at {abs_file_path}:{line_number}:{column_number} is not a symbol (e.g., comment or whitespace).")
        if not line_content.strip():
            raise custom_errors.SymbolNotFoundError(
                f"Element at {abs_file_path}:{line_number}:{column_number} is not a symbol (e.g., comment or whitespace).")
        raise custom_errors.SymbolNotFoundError(f"No symbol found at {abs_file_path}:{line_number}:{column_number}.")

    # 7. Return the usages
    symbol_data = code_symbols_index[abs_file_path][symbol_key]
    return symbol_data.get("usages", [])


@tool_spec(
    spec={
        'name': 'grep_search',
        'description': """ Do a text search in the workspace.
        
        This function performs a text search within the user's workspace. It is
        limited to 20 results and is intended for use when the exact string or
        regular expression to search for is known. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'search_pattern': {
                    'type': 'string',
                    'description': """ The exact string or regular expression to search
                    for in the workspace. """
                }
            },
            'required': [
                'search_pattern'
            ]
        }
    }
)
def grep_search(search_pattern: str) -> List[Dict[str, Any]]:
    """Do a text search in the workspace.

    This function performs a text search within the user's workspace. It is
    limited to 20 results and is intended for use when the exact string or
    regular expression to search for is known.

    Args:
        search_pattern (str): The exact string or regular expression to search
            for in the workspace.

    Returns:
        List[Dict[str, Any]]: A list of text search matches. Limited to 20
            results. Each dictionary in the list represents a match and
            includes the following keys:
            file_path (str): The path to the file containing the match.
            line_number (int): The line number where the match was found.
            line_content (str): The full content of the line containing the
                match.
            match_start_column (int): The starting column index of the match
                within the line (0-based).
            match_end_column (int): The ending column index (exclusive) of the
                match within the line.

    Raises:
        InvalidSearchPatternError: If the search string or pattern is invalid
            (e.g., an invalid regular expression or contains command-line
            argument patterns).
        WorkspaceNotAvailableError: If the user's workspace cannot be accessed
            for searching.
        ValidationError: If input arguments fail validation.
    """
    if not isinstance(search_pattern, str):
        raise custom_errors.ValidationError("search_pattern must be a string.")
    if not search_pattern:
        raise custom_errors.ValidationError("Search pattern cannot be empty.")

    workspace_root = DB.get("workspace_root")
    file_system = DB.get("file_system")

    if not (file_system and workspace_root):
        raise custom_errors.WorkspaceNotAvailableError(
            "Workspace is not available or not initialized."
        )
    
    # Security validation: Check for patterns that look like command-line arguments
    # Based on bug report example: "-f /etc/passwd"
    if search_pattern.startswith('-f ') or search_pattern.startswith('--file='):
        raise custom_errors.InvalidSearchPatternError(
            f"Search pattern contains potentially dangerous characters that resemble command-line arguments: '{search_pattern}'"
        )

    try:
        compiled_regex = re.compile(search_pattern)
    except re.error as e:
        raise custom_errors.InvalidSearchPatternError(f"Invalid search pattern: {e}")

    results: List[Dict[str, Any]] = []
    sorted_file_paths = sorted(file_system.keys())

    for path in sorted_file_paths:
        if len(results) >= 20:
            break

        entry = file_system[path]

        if entry.get("is_directory"):
            continue  # Skip directories.

        try:
            relative_path = os.path.relpath(path, workspace_root)
        except ValueError:
            continue

        if utils.is_path_excluded_for_search(
                relative_path,
                utils.DEFAULT_IGNORE_DIRS,
                utils.DEFAULT_IGNORE_FILE_PATTERNS
        ):
            continue

        content_lines = entry.get("content_lines")

        if (content_lines is None or
                not isinstance(content_lines, list) or
                content_lines == utils.BINARY_CONTENT_PLACEHOLDER or
                content_lines == utils.LARGE_FILE_CONTENT_PLACEHOLDER or
                content_lines == utils.ERROR_READING_CONTENT_PLACEHOLDER):
            continue

        for line_idx, line_text in enumerate(content_lines):
            if len(results) >= 20:
                break

            for match_obj in compiled_regex.finditer(line_text):
                if len(results) >= 20:
                    break

                file_path_to_report = entry.get("path")
                line_number = line_idx + 1

                full_line_content = line_text.rstrip('\r\n')
                match_start_column = match_obj.start()
                match_end_column = match_obj.end()

                result_item = {
                    "file_path": file_path_to_report,
                    "line_number": line_number,
                    "line_content": full_line_content,
                    "match_start_column": match_start_column,
                    "match_end_column": match_end_column,
                }
                results.append(result_item)

    return results
