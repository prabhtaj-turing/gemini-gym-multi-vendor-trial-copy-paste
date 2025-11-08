"""File utilities for Gemini-CLI simulation engine."""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Union
import os
import glob as glob_module
import base64
import mimetypes

from .custom_errors import InvalidInputError

# Constants for read_many_files functionality
DEFAULT_OUTPUT_SEPARATOR_FORMAT = "--- {filePath} ---"
DEFAULT_MAX_LINES_TEXT_FILE = 2000
MAX_LINE_LENGTH_TEXT_FILE = 8000
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB

# Default exclusion patterns (matches TypeScript implementation)
DEFAULT_EXCLUDES = [
    "**/node_modules/**",
    "**/.git/**", 
    "**/.vscode/**",
    "**/.idea/**",
    "**/dist/**",
    "**/build/**",
    "**/coverage/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.bin",
    "**/*.exe",
    "**/*.dll",
    "**/*.so",
    "**/*.dylib",
    "**/*.class",
    "**/*.jar",
    "**/*.war",
    "**/*.zip",
    "**/*.tar",
    "**/*.gz",
    "**/*.bz2", 
    "**/*.rar",
    "**/*.7z",
    "**/*.doc",
    "**/*.docx",
    "**/*.xls",
    "**/*.xlsx",
    "**/*.ppt",
    "**/*.pptx",
    "**/*.odt",
    "**/*.ods",
    "**/*.odp",
    "**/.DS_Store",
    "**/.env",
]

# ---------------------------------------------------------------------------
# Standard library imports (grouped & alphabetized)
# ---------------------------------------------------------------------------
import fnmatch
import os
import re
import pathlib

# ---------------------------------------------------------------------------
# Gemini-specific overrides / additions
# ---------------------------------------------------------------------------

# SVG upper size limit (bytes) mirroring Gemini-CLI
SVG_MAX_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB


# ---------------------------------------------------------------------------
# Stand-alone `detect_file_type` implementation
# ---------------------------------------------------------------------------


_IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".ico", ".cur",
}
_AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"}
_VIDEO_EXTS = {
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".mkv",
    ".m4v",
    ".3gp",
    ".mpg",
    ".mpeg",
    ".ts",
    ".mts",
    ".m2ts",
}


def detect_file_type(file_path: str) -> str:  # type: ignore[override]
    """Classify *file_path* into a coarse content category.

    The function relies solely on the file-name extension; no I/O is performed
    because the Gemini-CLI simulation works with an in-memory snapshot of the
    filesystem.

    Returns one of:
        'text' | 'image' | 'pdf' | 'audio' | 'video' | 'binary' | 'svg'
    """

    ext = pathlib.Path(file_path).suffix.lower()

    if ext == ".svg":
        return "svg"

    if ext == ".pdf":
        return "pdf"

    if ext in TEXT_EXTENSIONS or ext == ".ts":  # treat TypeScript as plain text
        return "text"

    if ext in _IMAGE_EXTS:
        return "image"

    if ext in _AUDIO_EXTS:
        return "audio"

    if ext in _VIDEO_EXTS:
        return "video"

    return "binary"


# Expose new implementation publicly
globals()["detect_file_type"] = detect_file_type

# ---------------------------------------------------------------------------
# Convenience helpers largely copied from the Copilot simulation so callers
# can work with base-64 and plain-text in a single place.  They do not
# interfere with the higher-level `process_single_file_content()` pipeline
# imported from the shared implementation.
# ---------------------------------------------------------------------------

TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
    '.html', '.htm', '.xml', '.xhtml', '.svg', '.css', '.scss', '.sass', '.less', '.jsx', '.tsx',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config', '.env', '.properties',
    '.csv', '.tsv', '.txt', '.md', '.rst', '.adoc', '.tex', '.latex', '.bib', '.log',
    '.sql', '.graphql', '.gql', '.proto', '.thrift', '.avro', '.parquet', '.feather', '.arrow',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.rc', '.profile', '.bashrc', '.zshrc',
}

BINARY_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.ico', '.cur',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.rtf',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.lzma', '.lz4', '.zstd',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.mp4', '.avi', '.mov', '.wmv',
    '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpg', '.mpeg', '.ts', '.mts', '.m2ts',
    '.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.deb', '.rpm', '.msi', '.pkg',
    '.apk', '.ipa', '.jar', '.war', '.ear', '.class', '.pyc', '.pyo', '.pyd',
    '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.fdb', '.odb',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.obj', '.fbx', '.dae', '.3ds', '.max', '.blend', '.ma', '.mb', '.c4d', '.stl',
}


def is_text_file(file_path: str) -> bool:
    """Naïve extension-based text file check (used by generic helpers)."""
    return pathlib.Path(file_path).suffix.lower() in TEXT_EXTENSIONS


def is_binary_file_ext(file_path: str) -> bool:
    """Extension-based binary classification (complements heuristics)."""
    return pathlib.Path(file_path).suffix.lower() in BINARY_EXTENSIONS


def encode_to_base64(content: Union[str, bytes]) -> str:
    if isinstance(content, str):
        content = content.encode('utf-8')
    return base64.b64encode(content).decode('utf-8')


def decode_from_base64(b64: str) -> bytes:
    return base64.b64decode(b64)


def text_to_base64(text: str) -> str:
    return encode_to_base64(text)


def base64_to_text(b64: str) -> str:
    return decode_from_base64(b64).decode('utf-8', errors='replace')


def file_to_base64(file_path: str) -> str:
    with open(file_path, 'rb') as fh:
        return encode_to_base64(fh.read())


def base64_to_file(b64: str, file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as fh:
        fh.write(decode_from_base64(b64))


# Generic read/write helpers – thin wrappers around the functions above.

def read_file_generic(file_path: str, max_size_mb: int = 50) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    size = os.path.getsize(file_path)
    if size > max_size_mb * 1024 * 1024:
        raise ValueError("File too large")
    if is_text_file(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='replace') as fh:
            content = fh.read()
        return {"content": content, "encoding": "text", "size_bytes": size}
    with open(file_path, 'rb') as fh:
        return {
            "content": encode_to_base64(fh.read()),
            "encoding": "base64",
            "size_bytes": size,
        }


def write_file_generic(file_path: str, content: Union[str, bytes], encoding: str = 'text') -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if encoding == 'base64':
        data = decode_from_base64(content if isinstance(content, str) else content.decode())
        mode, payload = 'wb', data
    else:
        payload = content if isinstance(content, str) else content.decode('utf-8', errors='replace')
        mode = 'w'
    with open(file_path, mode) as fh:
        fh.write(payload)

# ---------------------------------------------------------------------------
# Workspace-level helper utilities
# ---------------------------------------------------------------------------


def _is_within_workspace(abs_path: str, root: str) -> bool:  # noqa: D401
    """Return ``True`` when *abs_path* is located inside *root*.

    The check normalises both paths with :pyfunc:`os.path.normpath` and then
    verifies that *abs_path* is either the workspace root itself or a
    descendant directory/file of it.  The comparison is strictly
    case-sensitive; call-sites must handle any OS-specific case rules if
    necessary.

    Args:
        abs_path (str): Absolute path to test.
        root (str): Absolute workspace root directory path.

    Returns:
        bool: ``True`` if *abs_path* == *root* or is nested under *root*.

    Raises:
        InvalidInputError: If either argument is not a non-empty ``str`` or
            *abs_path* is not absolute.
    """

    if not isinstance(abs_path, str) or not abs_path:
        raise InvalidInputError("'abs_path' must be a non-empty string")
    if not isinstance(root, str) or not root:
        raise InvalidInputError("'root' must be a non-empty string")
    if not os.path.isabs(abs_path):
        raise InvalidInputError("'abs_path' must be an absolute path")

    root_norm = os.path.normpath(root)
    path_norm = os.path.normpath(abs_path)
    return path_norm == root_norm or path_norm.startswith(root_norm + os.sep)


def _should_ignore(name: str, patterns: Optional[List[str]]) -> bool:  # noqa: D401
    """Return ``True`` when *name* matches any glob in *patterns*.

    Args:
        name (str): Basename of the file or directory to evaluate
            (no path separators).
        patterns (Optional[List[str]]): Sequence of glob expressions.  When
            ``None`` or empty the call always returns ``False``.

    Returns:
        bool: ``True`` if *name* matches at least one glob in *patterns*.

    Raises:
        InvalidInputError: If *name* is not a string or *patterns* contains a
            non-string item.
    """

    if not isinstance(name, str):
        raise InvalidInputError("'name' must be a string")
    if not patterns:
        return False
    for pat in patterns:
        if not isinstance(pat, str):
            raise InvalidInputError("All ignore patterns must be strings")
        if fnmatch.fnmatchcase(name, pat):
            return True
    return False


def glob_match(path: str, pattern: str, case_sensitive: bool = False) -> bool:
    """Enhanced glob pattern matching with proper ** support and case sensitivity.
    
    Args:
        path (str): The file path to match against.
        pattern (str): The glob pattern.
        case_sensitive (bool): Whether to use case-sensitive matching.
        
    Returns:
        bool: True if the path matches the pattern, False otherwise.
        
    Raises:
        InvalidInputError: If path or pattern is not a string.
    """
    if not isinstance(path, str):
        raise InvalidInputError("'path' must be a string")
    if not isinstance(pattern, str):
        raise InvalidInputError("'pattern' must be a string")
    
    # Choose appropriate matching function based on case sensitivity
    if case_sensitive:
        match_func = fnmatch.fnmatchcase
    else:
        # For case-insensitive matching, convert both to lowercase
        def match_func(name, pattern):
            return fnmatch.fnmatch(name.lower(), pattern.lower())
    
    # Handle special case of ** recursive wildcard
    if '**' in pattern:
        # Convert ** patterns to handle recursive matching
        pattern_parts = pattern.split('**')
        
        if len(pattern_parts) == 2:
            prefix, suffix = pattern_parts
            prefix = prefix.rstrip('/')
            suffix = suffix.lstrip('/')
            
            # If pattern is just "**" or "**/*", match everything
            if not prefix and (not suffix or suffix == '*'):
                return True
            
            # If pattern is "**/*.ext", match any file ending with .ext
            if not prefix and suffix:
                # For patterns like "**/*.py", match any .py file at any depth
                return match_func(path, suffix) or match_func(os.path.basename(path), suffix)
            
            # If pattern is "dir/**", match anything under dir/
            if prefix and not suffix:
                return path.startswith(prefix + '/') or path == prefix
            
            # If pattern is "dir/**/*.ext", match .ext files under dir/
            if prefix and suffix:
                if path.startswith(prefix + '/'):
                    remaining_path = path[len(prefix) + 1:]
                    return match_func(remaining_path, suffix) or match_func(os.path.basename(remaining_path), suffix)
                return False
    
    # For non-** patterns, use standard fnmatch
    return match_func(path, pattern)


def filter_gitignore(files: List[tuple], workspace_root: str) -> List[tuple]:
    """Filter files based on gitignore patterns from the database.
    
    Args:
        files (List[tuple]): List of (file_path, file_meta) tuples.
        workspace_root (str): The workspace root directory.
        
    Returns:
        List[tuple]: Filtered list of (file_path, file_meta) tuples.
        
    Raises:
        InvalidInputError: If files is not a list or workspace_root is not a string.
    """
    if not isinstance(files, list):
        raise InvalidInputError("'files' must be a list")
    if not isinstance(workspace_root, str):
        raise InvalidInputError("'workspace_root' must be a string")
    
    # Import here to avoid circular imports
    from .db import DB
    
    # Get gitignore patterns from database
    gitignore_patterns = DB.get("gitignore_patterns", [])
    
    filtered_files = []
    
    for file_path, file_meta in files:
        # Get relative path from workspace root
        relative_path = os.path.relpath(file_path, workspace_root)
        
        # Check if file matches any gitignore pattern
        should_ignore = False
        for pattern in gitignore_patterns:
            if pattern.endswith('/'):
                # Directory pattern
                if f"/{pattern}" in f"/{relative_path}/" or relative_path.startswith(pattern):
                    should_ignore = True
                    break
            else:
                if fnmatch.fnmatch(relative_path.lower(), pattern.lower()):
                    should_ignore = True
                    break
        
        if not should_ignore:
            filtered_files.append((file_path, file_meta))
    
    return filtered_files


# ---------------------------------------------------------------------------
# String replacement helper utilities
# ---------------------------------------------------------------------------

def count_occurrences(text: str, substr: str) -> int:
    """Count the number of occurrences of substr in text.
    
    Args:
        text (str): The text to search in
        substr (str): The substring to count
        
    Returns:
        int: Number of occurrences found
    """
    if not substr:
        return 0
    return text.count(substr)


def apply_replacement(content: str, old_string: str, new_string: str) -> str:
    """Apply string replacement to content.
    
    This function handles both regular string replacement and normalized content
    replacement when the strings have been corrected through normalization.
    Preserves original whitespace outside of replaced sections.
    
    Args:
        content (str): The content to modify
        old_string (str): The string to replace
        new_string (str): The replacement string
        
    Returns:
        str: Modified content with replacements applied
    """
    if not old_string:
        return content
    
    # First try direct replacement
    if old_string in content:
        return content.replace(old_string, new_string)
    
    # If direct replacement fails, try with normalized content
    # This handles cases where correction logic normalized the strings
    normalized_content = _normalize_whitespace(content)
    normalized_old = _normalize_whitespace(old_string)
    
    if normalized_old in normalized_content:
        # Find the original text that corresponds to the normalized match
        # We need to be surgical and only replace the matching section,
        # not corrupt the entire file's whitespace
        
        # Split content into lines to preserve structure
        content_lines = content.splitlines(keepends=True)
        normalized_lines = normalized_content.splitlines(keepends=True)
        
        # Find the normalized match position
        norm_start_idx = normalized_content.find(normalized_old)
        if norm_start_idx == -1:
            # Fallback to original replacement
            return content.replace(old_string, new_string)
        
        # Convert character position to line/column position in normalized content
        norm_prefix = normalized_content[:norm_start_idx]
        norm_start_line = norm_prefix.count('\n')
        norm_start_col = len(norm_prefix) - norm_prefix.rfind('\n') - 1 if '\n' in norm_prefix else len(norm_prefix)
        
        norm_end_idx = norm_start_idx + len(normalized_old)
        norm_prefix_end = normalized_content[:norm_end_idx]
        norm_end_line = norm_prefix_end.count('\n')
        norm_end_col = len(norm_prefix_end) - norm_prefix_end.rfind('\n') - 1 if '\n' in norm_prefix_end else len(norm_prefix_end)
        
        # Now find the corresponding position in the original content
        # This is approximate but preserves most whitespace
        if norm_start_line < len(content_lines) and norm_end_line < len(content_lines):
            # Extract the original text that matches the normalized pattern
            if norm_start_line == norm_end_line:
                # Single line replacement
                original_line = content_lines[norm_start_line]
                if len(original_line) > norm_start_col:
                    # Replace within the line bounds
                    before = original_line[:min(norm_start_col, len(original_line))]
                    after = original_line[min(norm_end_col, len(original_line)):]
                    content_lines[norm_start_line] = before + new_string + after
            else:
                # Multi-line replacement
                # Replace from start position to end position
                before_lines = content_lines[:norm_start_line]
                after_lines = content_lines[norm_end_line + 1:]
                
                # Handle partial first and last lines
                first_line = content_lines[norm_start_line]
                last_line = content_lines[norm_end_line] if norm_end_line < len(content_lines) else ""
                
                before_text = first_line[:min(norm_start_col, len(first_line))]
                after_text = last_line[min(norm_end_col, len(last_line)):]
                
                # Reconstruct content
                result_lines = before_lines + [before_text + new_string + after_text] + after_lines
                return ''.join(result_lines)
            
            return ''.join(content_lines)
        
        # Fallback: if we can't map positions precisely, do normalized replacement
        # but warn that this may affect whitespace
        return normalized_content.replace(normalized_old, new_string)
    
    # Fallback to original replacement
    return content.replace(old_string, new_string)


def validate_replacement(content: str, old_string: str, expected_count: int) -> bool:
    """Validate that the expected number of replacements would be made.
    
    Args:
        content (str): The content to check
        old_string (str): The string to search for
        expected_count (int): Expected number of occurrences
        
    Returns:
        bool: True if the count matches expectations
    """
    actual_count = count_occurrences(content, old_string)
    return actual_count == expected_count


def _unescape_string_basic(text: str) -> str:
    """Basic string unescaping for common escape sequences.
    
    This handles common escape sequences that might appear in strings
    due to over-escaping or JSON serialization issues.
    
    Args:
        text (str): The text to unescape
        
    Returns:
        str: Text with basic escape sequences resolved
    """
    # Handle common escape sequences
    escape_map = {
        '\\n': '\n',
        '\\t': '\t',
        '\\r': '\r',
        '\\"': '"',
        "\\'": "'",
        '\\\\': '\\',
    }
    
    result = text
    for escaped, unescaped in escape_map.items():
        result = result.replace(escaped, unescaped)
    
    return result


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text for better matching.
    
    This function handles common whitespace inconsistencies:
    - Converts different line endings to \n
    - Converts tabs to spaces
    - Normalizes multiple spaces to single spaces (except at line start for indentation)
    - Preserves relative indentation structure
    
    Args:
        text (str): The text to normalize
        
    Returns:
        str: Text with normalized whitespace
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Handle tabs and spaces line by line to preserve indentation structure
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Convert tabs to spaces (4 spaces per tab)
        expanded_line = line.expandtabs(4)
        
        # For non-empty lines, normalize internal whitespace while preserving leading whitespace
        if expanded_line.strip():
            # Find leading whitespace
            leading_whitespace = len(expanded_line) - len(expanded_line.lstrip(' '))
            leading_part = expanded_line[:leading_whitespace]
            content_part = expanded_line[leading_whitespace:]
            
            # Normalize internal whitespace (multiple spaces to single space)
            # but preserve single spaces that are meaningful
            import re
            normalized_content = re.sub(r'  +', ' ', content_part)  # Multiple spaces to single space
            normalized_content = re.sub(r'\t+', ' ', normalized_content)  # Tabs to single space
            
            normalized_line = leading_part + normalized_content
        else:
            normalized_line = expanded_line
        
        normalized_lines.append(normalized_line)
    
    return '\n'.join(normalized_lines)


def correct_string_issues(
    content: str, 
    old_string: str, 
    new_string: str, 
    expected_replacements: int
) -> Dict[str, Any]:
    """Apply multi-stage self-correction for string matching issues.
    
    This function implements a progressive correction strategy:
    1. Try the original strings as-is
    2. Try basic unescaping if no matches found
    3. Try whitespace normalization if still no matches
    4. Try both unescaping and normalization together
    
    Args:
        content (str): The file content to search in
        old_string (str): The original old string to find
        new_string (str): The original new string to replace with
        expected_replacements (int): Expected number of replacements
        
    Returns:
        Dict[str, Any]: Dictionary with corrected strings and occurrence count:
            - 'old_string' (str): The corrected old string that matches
            - 'new_string' (str): The corrected new string to use
            - 'occurrences' (int): Number of occurrences found
    """
    # Stage 1: Try original strings
    occurrences = count_occurrences(content, old_string)
    if occurrences == expected_replacements:
        return {
            'old_string': old_string,
            'new_string': new_string,
            'occurrences': occurrences
        }
    
    # Stage 2: Try basic unescaping
    if occurrences == 0:
        unescaped_old = _unescape_string_basic(old_string)
        unescaped_new = _unescape_string_basic(new_string)
        
        occurrences = count_occurrences(content, unescaped_old)
        if occurrences == expected_replacements:
            return {
                'old_string': unescaped_old,
                'new_string': unescaped_new,
                'occurrences': occurrences
            }
    
    # Stage 3: Try whitespace normalization
    if occurrences == 0:
        normalized_content = _normalize_whitespace(content)
        normalized_old = _normalize_whitespace(old_string)
        normalized_new = _normalize_whitespace(new_string)
        
        occurrences = count_occurrences(normalized_content, normalized_old)
        if occurrences == expected_replacements:
            # Return the normalized old_string that matches the content
            return {
                'old_string': normalized_old,
                'new_string': normalized_new,
                'occurrences': occurrences
            }
    
    # Stage 4: Try both unescaping and normalization
    if occurrences == 0:
        combined_old = _normalize_whitespace(_unescape_string_basic(old_string))
        combined_new = _normalize_whitespace(_unescape_string_basic(new_string))
        combined_content = _normalize_whitespace(content)
        
        occurrences = count_occurrences(combined_content, combined_old)
        if occurrences == expected_replacements:
            return {
                'old_string': combined_old,
                'new_string': combined_new,
                'occurrences': occurrences
            }
    
    # Stage 5: Try finding best match in normalized content but return original format strings
    # This handles the case where we need to update the content but want to preserve the original strings
    if occurrences == 0:
        normalized_content = _normalize_whitespace(content)
        normalized_old = _normalize_whitespace(old_string)
        
        # Check if the normalized version would match
        norm_occurrences = count_occurrences(normalized_content, normalized_old)
        if norm_occurrences == expected_replacements:
            # Find the actual string in content that corresponds to the normalized match
            # This is a more complex case - for now, we'll use the normalized version
            return {
                'old_string': normalized_old,
                'new_string': _normalize_whitespace(new_string),
                'occurrences': norm_occurrences
            }
    
    # If all corrections fail, return original with actual count
    final_occurrences = count_occurrences(content, old_string)
    return {
        'old_string': old_string,
        'new_string': new_string,
        'occurrences': final_occurrences
    }


# ---------------------------------------------------------------------------
# Read Many Files Helper Functions
# ---------------------------------------------------------------------------


def matches_patterns(file_path: str, patterns: List[str]) -> bool:
    """Check if a file path matches any of the given glob patterns.
    
    Args:
        file_path (str): The file path to check against patterns.
        patterns (List[str]): List of glob patterns to match against.
        
    Returns:
        bool: True if the file path matches any pattern, False otherwise.
        
    Raises:
        InvalidInputError: If file_path is not a string or patterns contains non-string items.
    """
    if not isinstance(file_path, str):
        raise InvalidInputError("'file_path' must be a string")
    
    if not isinstance(patterns, list):
        raise InvalidInputError("'patterns' must be a list")
    
    for pattern in patterns:
        if not isinstance(pattern, str):
            raise InvalidInputError("All patterns must be strings")
        if matches_glob_pattern(file_path, pattern):
            return True
    return False


def matches_glob_pattern(file_path: str, pattern: str) -> bool:
    """Check if a file path matches a specific glob pattern.
    
    Handles various glob pattern formats including recursive patterns with **.
    
    Args:
        file_path (str): The file path to check.
        pattern (str): The glob pattern to match against.
        
    Returns:
        bool: True if the file path matches the pattern, False otherwise.
        
    Raises:
        InvalidInputError: If file_path or pattern is not a string.
    """
    if not isinstance(file_path, str):
        raise InvalidInputError("'file_path' must be a string")
    
    if not isinstance(pattern, str):
        raise InvalidInputError("'pattern' must be a string")
    
    # Normalize path separators for cross-platform compatibility
    file_path = file_path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    
    # Handle ** recursive patterns
    if "**" in pattern:
        # Convert ** pattern to proper glob pattern
        # Replace ** with proper glob pattern
        glob_pattern = pattern.replace("**/", "*/")
        
        # Use pathlib for proper glob matching
        import pathlib
        try:
            # Create a Path object for the file
            file_path_obj = pathlib.Path(file_path)
            
            # For patterns like **/*.py, we need to check if the file matches
            # the pattern when considering the full path
            
            # Simple implementation: check if the file ends with the pattern after **
            if pattern.startswith("**/"):
                suffix_pattern = pattern[3:]  # Remove "**/"
                # Check if file path ends with the suffix pattern
                if file_path_obj.match(suffix_pattern):
                    return True
                # Also check if any parent directory + filename matches
                for parent in file_path_obj.parents:
                    try:
                        relative_path = file_path_obj.relative_to(parent)
                        if relative_path.match(suffix_pattern):
                            return True
                    except ValueError:
                        continue
            
            # For patterns like src/**/*.py
            elif "**/" in pattern:
                parts = pattern.split("**/")
                if len(parts) == 2:
                    prefix = parts[0]
                    suffix = parts[1]
                    
                    # Check if file path contains the prefix and matches suffix
                    if prefix and prefix not in file_path:
                        return False
                    
                    # Check if the remaining part matches the suffix
                    if suffix:
                        return file_path_obj.match(f"*{suffix}") or file_path_obj.name.endswith(suffix.lstrip("*."))
                    
                    return True
            
            # For other ** patterns, use fnmatch with simpler pattern
            else:
                simple_pattern = pattern.replace("**", "*")
                return glob_module.fnmatch.fnmatch(file_path, simple_pattern)
        
        except Exception:
            # Fall back to simple string matching
            simple_pattern = pattern.replace("**", "*")
            return glob_module.fnmatch.fnmatch(file_path, simple_pattern)
    
    # Use fnmatch for simple patterns
    return (glob_module.fnmatch.fnmatch(file_path, pattern) or 
            glob_module.fnmatch.fnmatch(os.path.basename(file_path), pattern))


def process_single_file_content(
    file_path: str, 
    workspace_root: str,
    offset: Optional[int] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Process a single file's content for read_many_files operation.
    
    Reads file content from the simulated file system and processes it according
    to file type. Handles text files with pagination, binary files as base64,
    and provides appropriate error handling.
    
    Args:
        file_path (str): Absolute path to the file to process.
        workspace_root (str): Absolute path to the workspace root directory.
        offset (Optional[int]): For text files, 0-based line number to start reading from.
        limit (Optional[int]): For text files, maximum number of lines to read.
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - llm_content: The processed file content (str for text, dict for binary)
            - return_display: User-friendly display message
            - error (optional): Error message if processing failed
            - is_truncated (optional): Whether content was truncated for text files
            - original_line_count (optional): Total lines in text file
            - lines_shown (optional): Range of lines shown for text files
            
    Raises:
        InvalidInputError: If file_path or workspace_root is not a string,
            or if offset/limit values are invalid.
    """
    if not isinstance(file_path, str):
        raise InvalidInputError("'file_path' must be a string")
    
    if not isinstance(workspace_root, str):
        raise InvalidInputError("'workspace_root' must be a string")
    
    if offset is not None and (not isinstance(offset, int) or offset < 0):
        raise InvalidInputError("'offset' must be a non-negative integer or None")
    
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise InvalidInputError("'limit' must be a positive integer or None")
    
    from .db import DB
    
    try:
        # Get file info from simulated file system
        file_system = DB.get("file_system", {})
        file_info = file_system.get(file_path)
        
        if not file_info:
            return {
                "llm_content": "",
                "return_display": "File not found.",
                "error": f"File not found: {file_path}",
            }
        
        if file_info.get("is_directory", False):
            return {
                "llm_content": "",
                "return_display": "Path is a directory.",
                "error": f"Path is a directory, not a file: {file_path}",
            }
        
        file_size = file_info.get("size_bytes", 0)
        if file_size > MAX_FILE_SIZE_BYTES:
            return {
                "llm_content": "",
                "return_display": f"File too large (>{MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB).",
                "error": f"File size exceeds the 20MB limit: {file_path} ({file_size / (1024*1024):.2f}MB)",
            }
        
        file_type = detect_file_type(file_path)
        relative_path = os.path.relpath(file_path, workspace_root).replace("\\", "/")
        
        if file_type == "binary":
            return {
                "llm_content": f"Cannot display content of binary file: {relative_path}",
                "return_display": f"Skipped binary file: {relative_path}",
            }
        
        elif file_type == "svg":
            if file_size > SVG_MAX_SIZE_BYTES:
                return {
                    "llm_content": f"Cannot display content of SVG file larger than 1MB: {relative_path}",
                    "return_display": f"Skipped large SVG file (>1MB): {relative_path}",
                }
            # Get content from simulated file system
            content_lines = file_info.get("content_lines", [])
            content = "".join(content_lines)
            return {
                "llm_content": content,
                "return_display": f"Read SVG as text: {relative_path}",
            }
        
        elif file_type == "text":
            # Get content from simulated file system
            content_lines = file_info.get("content_lines", [])
            content = "".join(content_lines)
            
            lines = content.split('\n')
            original_line_count = len(lines)
            
            start_line = offset or 0
            effective_limit = limit if limit is not None else DEFAULT_MAX_LINES_TEXT_FILE
            end_line = min(start_line + effective_limit, original_line_count)
            actual_start_line = min(start_line, original_line_count)
            
            selected_lines = lines[actual_start_line:end_line]
            
            # Handle line length truncation
            lines_were_truncated_in_length = False
            formatted_lines = []
            for line in selected_lines:
                if len(line) > MAX_LINE_LENGTH_TEXT_FILE:
                    lines_were_truncated_in_length = True
                    formatted_lines.append(line[:MAX_LINE_LENGTH_TEXT_FILE] + "... [truncated]")
                else:
                    formatted_lines.append(line)
            
            content_range_truncated = end_line < original_line_count
            is_truncated = content_range_truncated or lines_were_truncated_in_length
            
            llm_text_content = ""
            if content_range_truncated:
                llm_text_content += f"[File content truncated: showing lines {actual_start_line + 1}-{end_line} of {original_line_count} total lines. Use offset/limit parameters to view more.]\n"
            elif lines_were_truncated_in_length:
                llm_text_content += f"[File content partially truncated: some lines exceeded maximum length of {MAX_LINE_LENGTH_TEXT_FILE} characters.]\n"
            
            llm_text_content += '\n'.join(formatted_lines)
            
            return {
                "llm_content": llm_text_content,
                "return_display": "(truncated)" if is_truncated else "",
                "is_truncated": is_truncated,
                "original_line_count": original_line_count,
                "lines_shown": [actual_start_line + 1, end_line],
            }
        
        elif file_type in ["image", "pdf", "audio", "video"]:
            # For simulated file system, create mock base64 data
            content_lines = file_info.get("content_lines", [])
            content = "".join(content_lines)
            
            # Convert to base64 (for simulation, we'll use the content as-is)
            base64_data = base64.b64encode(content.encode('utf-8')).decode('ascii')
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"
            
            return {
                "llm_content": {
                    "inlineData": {
                        "data": base64_data,
                        "mimeType": mime_type,
                    }
                },
                "return_display": f"Read {file_type} file: {relative_path}",
            }
        
        else:
            return {
                "llm_content": f"Unhandled file type: {file_type}",
                "return_display": f"Skipped unhandled file type: {relative_path}",
                "error": f"Unhandled file type for {file_path}",
            }
    
    except Exception as e:
        relative_path = os.path.relpath(file_path, workspace_root).replace("\\", "/")
        error_message = str(e)
        return {
            "llm_content": f"Error reading file {relative_path}: {error_message}",
            "return_display": f"Error reading file {relative_path}: {error_message}",
            "error": f"Error reading file {file_path}: {error_message}",
        }


def expand_glob_patterns(
    patterns: List[str], 
    workspace_root: str,
    exclude_patterns: List[str],
    recursive: bool = True
) -> List[str]:
    """Expand glob patterns to find matching files using simulated file system.
    
    Searches the simulated file system for files matching the given glob patterns,
    applying exclusion filters and workspace boundary checks.
    
    Args:
        patterns (List[str]): List of glob patterns to search for.
        workspace_root (str): Absolute path to the workspace root directory.
        exclude_patterns (List[str]): List of glob patterns for files to exclude.
        recursive (bool): Whether to search recursively (primarily controlled by ** in patterns).
        
    Returns:
        List[str]: Sorted list of absolute file paths that match the criteria.
        
    Raises:
        InvalidInputError: If parameters are not of the expected types.
        Exception: If there are errors accessing the simulated file system.
    """
    if not isinstance(patterns, list):
        raise InvalidInputError("'patterns' must be a list")
    
    if not isinstance(workspace_root, str):
        raise InvalidInputError("'workspace_root' must be a string")
    
    if not isinstance(exclude_patterns, list):
        raise InvalidInputError("'exclude_patterns' must be a list")
    
    if not isinstance(recursive, bool):
        raise InvalidInputError("'recursive' must be a boolean")
    
    for pattern in patterns:
        if not isinstance(pattern, str):
            raise InvalidInputError("All patterns must be strings")
    
    for pattern in exclude_patterns:
        if not isinstance(pattern, str):
            raise InvalidInputError("All exclude patterns must be strings")
    
    from .db import DB
    
    all_files = set()
    
    # Get all files from simulated file system
    file_system = DB.get("file_system", {})
    
    for pattern in patterns:
        # Handle absolute vs relative patterns
        if os.path.isabs(pattern):
            if not _is_within_workspace(pattern, workspace_root):
                continue
            search_pattern = pattern
        else:
            # Convert relative pattern to absolute for matching
            search_pattern = os.path.join(workspace_root, pattern)
        
        # Match against all files in the simulated file system
        for file_path, file_info in file_system.items():
            # Skip directories
            if file_info.get("is_directory", False):
                continue
            
            # Check if file matches the pattern
            if matches_glob_pattern(file_path, search_pattern):
                # Security check
                if _is_within_workspace(file_path, workspace_root):
                    all_files.add(file_path)
    
    # Filter out excluded files
    filtered_files = []
    for file_path in all_files:
        relative_path = os.path.relpath(file_path, workspace_root)
        # Check exclusion patterns against both absolute and relative paths
        if not (matches_patterns(file_path, exclude_patterns) or 
                matches_patterns(relative_path, exclude_patterns)):
            filtered_files.append(file_path)
    
    return sorted(filtered_files)

# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__: list[str] = [
    *(globals().keys()),  # export everything we imported
    "SVG_MAX_SIZE_BYTES",
    "detect_file_type",
]

# ---------------------------------------------------------------------------
# .geminiignore helper utilities
# ---------------------------------------------------------------------------

def _load_geminiignore_patterns(file_system: Dict[str, Any], root: str) -> List[str]:  # noqa: D401
    """Return glob patterns defined in a ``.geminiignore`` file.

    Args:
        file_system (Dict[str, Any]): The ``file_system`` section of the
            in-memory DB (mapping absolute paths to metadata dictionaries).
        root (str): Absolute workspace root directory.

    Returns:
        List[str]: Cleaned, non-comment, non-empty pattern strings. Returns an
        empty list if the ignore file is absent or malformed.
    """

    if not isinstance(root, str) or not root:
        raise InvalidInputError("'root' must be a non-empty string")

    ignore_path = os.path.join(root, ".geminiignore")
    entry = file_system.get(ignore_path)
    if not entry or entry.get("is_directory", False):
        return []

    lines = entry.get("content_lines", [])
    if not isinstance(lines, list):
        return []

    patterns: List[str] = []
    for raw in lines:
        if not isinstance(raw, str):
            continue
        stripped = raw.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def _is_ignored(abs_path: str, root: str, file_system: Dict[str, Any]) -> bool:  # noqa: D401
    """Check if *abs_path* matches any pattern in ``.geminiignore``.

    Args:
        abs_path (str): Absolute file path to evaluate.
        root (str): Workspace root directory.
        file_system (Dict[str, Any]): DB file-system mapping.

    Returns:
        bool: ``True`` when the path should be ignored.
    """

    if not isinstance(abs_path, str) or not os.path.isabs(abs_path):
        raise InvalidInputError("'abs_path' must be an absolute path string")

    patterns = _load_geminiignore_patterns(file_system, root)
    if not patterns:
        return False

    rel = os.path.relpath(abs_path, root).replace(os.sep, "/")
    return any(fnmatch.fnmatchcase(rel, pat) for pat in patterns)


__all__.extend([
    "_is_ignored",
    "count_occurrences", 
    "apply_replacement", 
    "validate_replacement", 
    "correct_string_issues",
    "_load_geminiignore_patterns",
    "_is_within_workspace",
    "_should_ignore",
    "glob_match",
    "filter_gitignore",
    "try_git_grep",
    "try_system_grep",
    "python_grep_fallback"
])
