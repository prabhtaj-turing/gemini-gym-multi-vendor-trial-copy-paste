# terminal/SimulationEngine/utils.py
import os
import logging
import datetime
import tempfile
import re
import fnmatch  # For glob pattern matching
import mimetypes  # For a more robust way to guess if a file is binary
import inspect
import fnmatch
import sys
import shutil
import subprocess
import time
import stat  # For file permission constants
import base64 # Added for base64 encoding of binary archive content
import shlex  # For command tokenization
from functools import wraps
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, TypeVar


# --- Logger Setup for this utils.py module ---
logger = logging.getLogger(__name__)

class MetadataError(Exception):
    """Exception raised when metadata operations fail in strict mode."""
    pass



# --- Configuration for File Handling (Hydration) ---
MAX_FILE_SIZE_TO_LOAD_CONTENT_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_TO_LOAD_CONTENT_MB * 1024 * 1024
BINARY_CONTENT_PLACEHOLDER = ["<Binary File - Content Not Loaded>"]
LARGE_FILE_CONTENT_PLACEHOLDER = [
    f"<File Exceeds {MAX_FILE_SIZE_TO_LOAD_CONTENT_MB}MB - Content Not Loaded>"
]
ERROR_READING_CONTENT_PLACEHOLDER = ["<Error Reading File Content>"]
BINARY_FILE_MARKER = "# BINARY_ARCHIVE_BASE64_ENCODED"

# Archive file extensions that should have their binary content preserved
# These files need to be accessible as actual binary data for archive operations
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar'}

# Ensure Markdown is recognized as text by mimetypes on all systems
mimetypes.add_type("text/markdown", ".md")
mimetypes.add_type("text/markdown", ".markdown")

# Whitelist of extensions that should always be treated as text (never binary)
TEXT_FILE_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".mdx",
    ".rst",
}

# Maximum size for archive files to preserve binary content (smaller than general binary limit)
MAX_ARCHIVE_SIZE_MB = 10
MAX_ARCHIVE_SIZE_BYTES = MAX_ARCHIVE_SIZE_MB * 1024 * 1024

# Access time behavior configuration (mirrors real filesystem mount options)
ACCESS_TIME_MODE = "relatime"  # Options: "atime", "noatime", "relatime"
# - "atime": Update on every access (performance heavy, like traditional Unix)
# - "noatime": Never update access time (modern performance optimization)  
# - "relatime": Update only if atime is older than mtime/ctime (modern default)

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


# --- Path Utilities ---


def get_absolute_path(db, relative_or_absolute_path: str) -> str:
    """
    Resolves a given path to an absolute path, normalized, within the application's workspace
    as defined in the 'db' configuration.

    - If the path is already absolute and starts with the 'workspace_root' (from `db`),
      it's normalized and returned.
    - If the path is absolute but not within the configured 'workspace_root', a ValueError is raised.
    - If the path is relative, it's joined with the 'cwd' (current working directory from `db`,
      defaulting to 'workspace_root') and then normalized.
    """
    workspace_root = db.get("workspace_root")
    if not workspace_root:
        raise ValueError(
            "Workspace root is not configured. Check application settings."
        )

    if os.path.isabs(relative_or_absolute_path):
        normalized_path = os.path.normpath(relative_or_absolute_path)
        if not normalized_path.startswith(os.path.normpath(workspace_root)):
            raise ValueError(
                f"Absolute path '{normalized_path}' is outside the configured workspace root '{workspace_root}'."
            )
        return normalized_path
    else:
        cwd = db.get("cwd", workspace_root)
        return os.path.normpath(os.path.join(cwd, relative_or_absolute_path))

# --- File System Utilities (DB-Only Operations) ---

def get_file_system_entry(db, path: str):
    """
    Retrieves a file or directory metadata entry from the in-memory 'db["file_system"]'.
    The provided path is resolved to an absolute, normalized path before lookup.
    Returns the entry dict or None if not found or if path is invalid.
    """
    try:
        abs_path = get_absolute_path(db, path)
        return db.get("file_system", {}).get(abs_path)
    except ValueError:
        return None

def path_exists(db, path: str) -> bool:
    """
    Checks if a path exists as an entry in the in-memory 'db["file_system"]'.
    The path is resolved to an absolute path before checking.
    """
    try:
        abs_path = get_absolute_path(db, path)
        return abs_path in db.get("file_system", {})
    except ValueError:
        return False

def is_directory(db, path: str) -> bool:
    """
    Checks if a given path corresponds to a directory in 'db["file_system"]'.
    The path is resolved to an absolute path before checking.
    Returns False if the path doesn't exist or is not a directory.
    """
    entry = get_file_system_entry(db, path)
    return entry is not None and entry.get("is_directory", False)

def is_file(db, path: str) -> bool:
    """
    Checks if a given path corresponds to a file in 'db["file_system"]'.
    The path is resolved to an absolute path before checking.
    Returns False if the path doesn't exist or is not a file.
    """
    entry = get_file_system_entry(db, path)
    return entry is not None and not entry.get("is_directory", False)

def calculate_size_bytes(content_lines: list[str]) -> int:
    """Calculates the total size of a list of content lines in bytes (UTF-8 encoded)."""
    return sum(len(line.encode("utf-8")) for line in content_lines)

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

def get_current_timestamp_iso() -> str:
    """Returns the current time in ISO 8601 format, UTC (suffixed with 'Z')."""
    return (
        datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    )


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



def _is_archive_file(filepath: str) -> bool:
    """
    Check if a file is an archive that should have its binary content preserved.
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        bool: True if the file is an archive that should preserve binary content
    """
    if not filepath:
        return False
    
    # Get file extension
    _, ext = os.path.splitext(filepath.lower())
    
    # Handle compound extensions like .tar.gz, .tar.bz2, etc.
    if ext in {'.gz', '.bz2', '.xz'} and filepath.lower().endswith('.tar' + ext):
        return True
    
    return ext in ARCHIVE_EXTENSIONS


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
    # Always treat known text extensions as text
    try:
        _, _ext = os.path.splitext(filepath)
        ext = _ext.lower()
    except Exception:
        ext = ""
    if ext in TEXT_FILE_EXTENSIONS:
        return False

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

                    # Collect metadata for directory
                    dir_metadata = _collect_file_metadata(dirpath)

                    db_instance["file_system"][current_normalized_dirpath] = {
                        "path": current_normalized_dirpath,
                        "is_directory": True,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": last_modified_iso,
                        "metadata": dir_metadata  # Add metadata for directory
                    }
                    logger.debug(f"Added directory entry with metadata to DB: {current_normalized_dirpath}")
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

                    # Collect metadata for file
                    file_metadata = _collect_file_metadata(file_full_path)

                    if size_bytes == 0: # Handle empty files explicitly
                        content_lines = []
                        logger.debug(f"File '{normalized_file_path}' is empty. Content set to [].")
                    elif size_bytes > MAX_FILE_SIZE_BYTES:
                        logger.info(
                            f"File '{normalized_file_path}' ({size_bytes / (1024*1024):.2f}MB) exceeds max size {MAX_FILE_SIZE_TO_LOAD_CONTENT_MB}MB. Content not loaded."
                        )
                        content_lines = LARGE_FILE_CONTENT_PLACEHOLDER
                    elif _is_archive_file(file_full_path) and size_bytes <= MAX_ARCHIVE_SIZE_BYTES:
                        # Special handling for archive files - store actual binary content
                        logger.info(
                            f"File '{normalized_file_path}' detected as archive. Storing binary content."
                        )
                        try:
                            with open(file_full_path, "rb") as f:
                                binary_content = f.read()
                            
                            # Store binary content as base64-encoded strings to preserve it exactly
                            encoded_content = base64.b64encode(binary_content).decode('ascii')
                            # Split into chunks to avoid extremely long lines
                            chunk_size = 76  # Standard base64 line length
                            content_lines = [encoded_content[i:i+chunk_size] + '\n' 
                                           for i in range(0, len(encoded_content), chunk_size)]
                            if content_lines and not content_lines[-1].endswith('\n'):
                                content_lines[-1] += '\n'
                            
                            # Mark this as base64-encoded binary content
                            content_lines.insert(0, f"{BINARY_FILE_MARKER}\n")
                            
                        except Exception as e_read:
                            logger.warning(f"Error reading archive file '{normalized_file_path}': {e_read}")
                            content_lines = BINARY_CONTENT_PLACEHOLDER
                    elif is_likely_binary_file(file_full_path):
                        logger.info(
                            f"File '{normalized_file_path}' detected as binary. Storing base64 encoded content."
                        )
                        try:
                            with open(file_full_path, "rb") as f:
                                binary_content = f.read()
                            
                            encoded_content = base64.b64encode(binary_content).decode('ascii')
                            chunk_size = 76
                            content_lines = [encoded_content[i:i+chunk_size] + '\n' 
                                           for i in range(0, len(encoded_content), chunk_size)]
                            if content_lines and not content_lines[-1].endswith('\n'):
                                content_lines[-1] += '\n'
                            
                            content_lines.insert(0, f"{BINARY_FILE_MARKER}\n")
                            
                        except Exception as e_read:
                            logger.warning(f"Error reading binary file '{normalized_file_path}': {e_read}")
                            content_lines = BINARY_CONTENT_PLACEHOLDER
                    else:
                        # Read ALL text files in binary mode to preserve exact line endings (like real Linux)
                        try:
                            with open(file_full_path, "rb") as f:
                                binary_content = f.read()
                            
                            # Try to decode as text, preserving exact line endings
                            read_success = False
                            for encoding in ["utf-8", "latin-1", "cp1252"]:
                                try:
                                    text_content = binary_content.decode(encoding)
                                    content_lines = text_content.splitlines(keepends=True)
                                    if not content_lines and text_content:
                                        content_lines = [text_content]
                                    read_success = True
                                    logger.debug(f"Successfully read file '{normalized_file_path}' with encoding '{encoding}' preserving exact line endings.")
                                    break
                                except UnicodeDecodeError:
                                    logger.debug(f"Failed to decode '{normalized_file_path}' with encoding '{encoding}'. Trying next.")
                                    continue
                            
                            if not read_success:
                                logger.warning(f"Could not decode file '{normalized_file_path}' with any encoding, treating as binary.")
                                content_lines = BINARY_CONTENT_PLACEHOLDER
                                
                        except Exception as e_read:
                            logger.warning(f"Error reading file '{normalized_file_path}': {e_read}")
                            content_lines = [f"Error: Could not read file content. Reason: {type(e_read).__name__}\n"]

                    db_instance["file_system"][normalized_file_path] = {
                        "path": normalized_file_path,
                        "is_directory": False,
                        "content_lines": content_lines,
                        "size_bytes": size_bytes,
                        "last_modified": last_modified_iso,
                        "metadata": file_metadata  # Add metadata for file
                    }
                    logger.debug(f"Added file entry with metadata to DB: {normalized_file_path}")

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

    if not final_logical_path.startswith(expected_prefix) and final_logical_path != normalized_desired_logical_root:
        # Create any missing parent directories
        parent_dir = os.path.dirname(final_logical_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

    return final_logical_path


# --- Dehydrate Function ---
def dehydrate_db_to_directory(db: Dict[str, Any], target_dir: str) -> bool:
    """Writes workspace file system content to a specified target directory."""
    

    old_root = db.get("workspace_root")
    if not old_root:
        raise ValueError("DB missing 'workspace_root' for dehydration.")

    new_root = os.path.abspath(target_dir).replace("\\", "/") # Standardize new root path
    file_system = db.get("file_system", {})
    new_file_system = {} # To store updated paths for the DB

    _log_util_message(logging.INFO, f"Writing workspace state to disk: {new_root}")

    try:
        os.makedirs(new_root, exist_ok=True) # Create target root if needed

        for old_path, entry in sorted(file_system.items(), key=lambda x: len(x[0]), reverse=True):
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


            try:
                if entry.get("is_directory", False):
                    os.makedirs(new_path, exist_ok=True) # Create directory
                    if "metadata" in entry:
                        _apply_file_metadata(new_path, entry["metadata"], strict_mode=False)
                else:
                    # Create parent directory for the file if it doesn't exist
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)

                    # Check if this is a symlink
                    is_symlink = entry.get("metadata", {}).get("attributes", {}).get("is_symlink", False)
                    symlink_target = entry.get("metadata", {}).get("attributes", {}).get("symlink_target")

                    if is_symlink and symlink_target:
                        # For symlinks, create a new symlink pointing to the target
                        # First remove any existing file/link
                        if os.path.exists(new_path) or os.path.islink(new_path):
                            os.unlink(new_path)
                        # Create the symlink with the original target
                        os.symlink(symlink_target, new_path)
                    else:
                        # Write ALL files exactly as they were read - no line ending conversion
                        # This preserves the original line endings (CRLF will show as ^M in Linux terminals)
                        content_to_write = entry.get("content_lines", [])
                        
                        # Check if this is a base64-encoded archive file
                        if (content_to_write and 
                            len(content_to_write) > 0 and 
                            content_to_write[0].strip() == BINARY_FILE_MARKER):
                            
                            # This is a base64-encoded archive file - decode it back to binary
                            try:
                                # Remove the header and join all base64 content
                                base64_content = ''.join(line.rstrip('\n') for line in content_to_write[1:])
                                binary_content = base64.b64decode(base64_content)
                                
                                # Write as binary file
                                with open(new_path, "wb") as f:
                                    f.write(binary_content)
                                _log_util_message(logging.INFO, f"Restored binary archive content for: {new_path}")
                                
                            except Exception as e:
                                _log_util_message(logging.ERROR, f"Failed to decode archive file '{new_path}': {e}")
                                # Fall back to writing as text (will be broken but won't crash)
                                with open(new_path, "w", encoding="utf-8") as f:
                                    f.writelines(content_to_write)
                        else:
                            # Regular text file - write as before
                            if os.path.exists(new_path):
                                current_mode = os.stat(new_path).st_mode
                                os.chmod(new_path, current_mode | 0o200)

                            # Write the file
                            with open(new_path, "w", encoding="utf-8") as f:
                                f.writelines(content_to_write)

                            # Restore original permissions if they exist
                            if "metadata" in entry and "permissions" in entry["metadata"]:
                                original_mode = entry["metadata"]["permissions"].get("mode")
                                if original_mode is not None:
                                    os.chmod(new_path, original_mode)
                    
                    # Apply metadata right after writing the file
                    if "metadata" in entry:
                        _apply_file_metadata(new_path, entry["metadata"], strict_mode=False)

                # Apply metadata if available
                if "metadata" in entry:
                    _apply_file_metadata(new_path, entry["metadata"], strict_mode=False)

            except OSError as e:
                _log_util_message(logging.ERROR, f"OS error writing to {new_path}: {e}", exc_info=True)
                raise # Re-raise OS errors
            except Exception as e:
                _log_util_message(logging.ERROR, f"Unexpected error writing {new_path}: {e}", exc_info=True)
                raise # Re-raise other unexpected errors


        # The DB object should NOT be updated here. This function's purpose in the new
        # architecture is only to write the DB's state to a physical directory.
        # The DB's internal state should always reflect the logical workspace paths.
        _log_util_message(logging.INFO, f"Workspace state successfully written to {new_root}")

        return True

    except (ValueError, OSError, Exception) as e:
        # Log any failure during the overall process
        _log_util_message(logging.ERROR, f"Failed to write workspace state to disk: {e}", exc_info=True)
        raise e # Re-raise the caught exception

# --- Update Function ---
def update_db_file_system_from_temp(
        db: Dict[str, Any],
        temp_root: str,
        original_state: Dict,
        workspace_root: str,
        preserve_metadata: bool = True,
        command: str = ""
    ):
    """Update function with metadata preservation"""
    try: # Start of the main try block
        final_logical_root_for_db = _normalize_path_for_db(workspace_root)
        normalized_temp_root = _normalize_path_for_db(os.path.abspath(temp_root))
        
        # Check if this is a metadata-modifying command
        is_metadata_command = command.strip().startswith(("chmod", "chown"))
        
        # Check if this is a touch command (updates timestamps without changing content)
        is_touch_command = command.strip().split()[0] == "touch" if command.strip().split() else False
        
        # Determine which files should have their access time updated
        should_update_atime = _should_update_access_time(command)
        # Use logical workspace path for file resolution, not physical temp path
        logical_cwd = db.get("cwd", workspace_root)
        # Convert physical temp path back to logical path if needed
        if logical_cwd.startswith(temp_root):
            # Map from physical temp path to logical workspace path
            relative_to_temp = os.path.relpath(logical_cwd, temp_root)
            logical_cwd = os.path.join(workspace_root, relative_to_temp) if relative_to_temp != '.' else workspace_root
        accessed_files = _extract_file_paths_from_command(command, workspace_root, logical_cwd) if should_update_atime else set()

        new_file_system = {}
        processed_paths = set()

        for current_fs_root, dirs, files in os.walk(normalized_temp_root, topdown=True):
            current_physical_dir_path = _normalize_path_for_db(os.path.abspath(current_fs_root))
            
            dir_db_key_path = map_temp_path_to_db_key(current_physical_dir_path,
                                                      normalized_temp_root,
                                                      final_logical_root_for_db)

            if dir_db_key_path is None:
                _log_util_message(logging.WARNING, f"Could not map directory temp path '{current_physical_dir_path}' to a logical db key during db update.")
                continue

            if dir_db_key_path not in processed_paths:
                # Always read the ground truth metadata from the sandbox directory.
                dir_metadata = _collect_file_metadata(current_physical_dir_path)
                last_modified_val = dir_metadata.get("timestamps", {}).get("modify_time", get_current_timestamp_iso())
                
                # For metadata commands, apply in strict mode
                if is_metadata_command:
                    try:
                        _apply_file_metadata(current_physical_dir_path, dir_metadata, strict_mode=True)
                    except Exception as e:
                        raise MetadataError(f"Failed to apply metadata in strict mode: {str(e)}") from e

                new_file_system[dir_db_key_path] = {
                    "path": dir_db_key_path,
                    "is_directory": True,
                    "content_lines": [], # Directories don't have content lines
                    "size_bytes": 0,     # Directories usually have 0 size in this model
                    "last_modified": last_modified_val,
                    "metadata": dir_metadata
                }
                processed_paths.add(dir_db_key_path)

            for fname in files:
                temp_file_full_path = os.path.join(current_fs_root, fname) # Physical path to the file in temp dir
                file_physical_path = _normalize_path_for_db(os.path.abspath(temp_file_full_path))
                
                file_db_key_path = map_temp_path_to_db_key(file_physical_path,
                                                           normalized_temp_root,
                                                           final_logical_root_for_db)

                if file_db_key_path is None:
                    _log_util_message(logging.WARNING, f"Could not map file temp path '{file_physical_path}' to a logical db key during db update.")
                    continue
                
                if file_db_key_path in processed_paths: # Should not happen if logic is correct, but a safeguard.
                    _log_util_message(logging.WARNING, f"File path '{file_db_key_path}' already processed. Skipping duplicate.")
                    continue

                content_lines = ERROR_READING_CONTENT_PLACEHOLDER
                size_bytes = 0
                last_modified = get_current_timestamp_iso() # Default
                file_metadata = None  # Initialize metadata variable

                try:
                    # Check if the file is a symlink first
                    is_symlink = os.path.islink(temp_file_full_path)
                    if is_symlink:
                        # For symlinks, we need special handling
                        symlink_target = os.readlink(temp_file_full_path)
                        # Check if this specific symlink should have its access time updated
                        symlink_should_update_atime = should_update_atime and file_db_key_path in accessed_files
                        
                        if not symlink_should_update_atime:
                            # Create fresh symlink metadata but preserve access time
                            file_metadata = {
                                "attributes": {
                                    "is_symlink": True,
                                    "symlink_target": symlink_target,
                                    "is_hidden": os.path.basename(temp_file_full_path).startswith('.')
                                },
                                "timestamps": {
                                    "access_time": get_current_timestamp_iso(),
                                    "modify_time": get_current_timestamp_iso(),
                                    "change_time": get_current_timestamp_iso()
                                }
                            }
                            
                            # Preserve original access time if available
                            original_entry = original_state.get(file_db_key_path, {})
                            original_metadata = original_entry.get("metadata", {})
                            if original_metadata and "timestamps" in original_metadata and "access_time" in original_metadata["timestamps"]:
                                file_metadata["timestamps"]["access_time"] = original_metadata["timestamps"]["access_time"]
                        else:
                            # This symlink was accessed, create fresh metadata with updated access time
                            file_metadata = {
                                "attributes": {
                                    "is_symlink": True,
                                    "symlink_target": symlink_target,
                                    "is_hidden": os.path.basename(temp_file_full_path).startswith('.')
                                },
                                "timestamps": {
                                    "access_time": get_current_timestamp_iso(),  # Updated access time
                                    "modify_time": get_current_timestamp_iso(),
                                    "change_time": get_current_timestamp_iso()
                                }
                            }
                        content_lines = []  # Symlinks don't have content
                        size_bytes = len(symlink_target)  # Size is the length of the target path
                    else:
                        # Regular file handling
                        stat_info = os.stat(temp_file_full_path)
                        size_bytes = stat_info.st_size
                        last_modified = datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")

                        original_entry = original_state.get(file_db_key_path, {})
                        original_size = original_entry.get("size_bytes", -1)
                        original_last_modified = original_entry.get("last_modified")

                        # Check if file actually changed by comparing size first (fast check)
                        # Exception: touch command always updates timestamps even if content unchanged
                        file_actually_changed = (size_bytes != original_size) or is_touch_command
                        
                        if not file_actually_changed and original_last_modified:
                            # Size is same and not touch command, use original last_modified to preserve exact timestamp
                            last_modified = original_last_modified
                            
                            # For metadata commands, apply in strict mode
                            if is_metadata_command:
                                try:
                                    file_metadata = _collect_file_metadata(temp_file_full_path)
                                    _apply_file_metadata(temp_file_full_path, file_metadata, strict_mode=True)
                                except Exception as e:
                                    raise MetadataError(f"Failed to apply metadata in strict mode: {str(e)}") from e
                        elif file_actually_changed:
                            # File content has changed.
                            # We need a full refresh of all metadata from the disk.
                            # For metadata commands, apply in strict mode
                            if is_metadata_command:
                                try:
                                    file_metadata = _collect_file_metadata(temp_file_full_path)
                                    _apply_file_metadata(temp_file_full_path, file_metadata, strict_mode=True)
                                except Exception as e:
                                    raise MetadataError(f"Failed to apply metadata in strict mode: {str(e)}") from e

                    # Reuse old content_lines and metadata if file is unchanged (optional optimization)
                    # For simplicity here, we always re-read, but you could compare with original_file_system_state.get(file_db_key_path)
                    
                    if size_bytes == 0:
                        content_lines = []
                    elif size_bytes > MAX_FILE_SIZE_BYTES: # MAX_FILE_SIZE_BYTES needs to be defined/imported
                        content_lines = LARGE_FILE_CONTENT_PLACEHOLDER # Needs to be defined/imported
                        _log_util_message(logging.INFO, f"File '{file_db_key_path}' too large ({size_bytes} bytes), using placeholder.")
                    elif is_likely_binary_file(temp_file_full_path):
                        logger.info(
                            f"File '{file_db_key_path}' detected as binary. Storing base64 encoded content."
                        )
                        try:
                            with open(temp_file_full_path, "rb") as f:
                                binary_content = f.read()
                            
                            encoded_content = base64.b64encode(binary_content).decode('ascii')
                            chunk_size = 76
                            content_lines = [encoded_content[i:i+chunk_size] + '\n' 
                                           for i in range(0, len(encoded_content), chunk_size)]
                            if content_lines and not content_lines[-1].endswith('\n'):
                                content_lines[-1] += '\n'
                            
                            content_lines.insert(0, f"{BINARY_FILE_MARKER}\n")
                            
                        except Exception as e_read:
                            _log_util_message(logging.WARNING, f"Error reading binary file '{file_db_key_path}': {e_read}")
                            content_lines = BINARY_CONTENT_PLACEHOLDER
                    else:
                        # Read ALL text files in binary mode to preserve exact line endings (like real Linux)
                        try:
                            with open(temp_file_full_path, "rb") as f:
                                binary_content = f.read()
                            
                            # Try to decode as text, preserving exact line endings
                            read_success = False
                            for encoding in ["utf-8", "latin-1", "cp1252"]:
                                try:
                                    text_content = binary_content.decode(encoding)
                                    content_lines = text_content.splitlines(keepends=True)
                                    if not content_lines and text_content:
                                        content_lines = [text_content]
                                    read_success = True
                                    logger.debug(f"Successfully read file '{file_db_key_path}' with encoding '{encoding}' preserving exact line endings.")
                                    break
                                except UnicodeDecodeError:
                                    logger.debug(f"Failed to decode '{file_db_key_path}' with encoding '{encoding}'. Trying next.")
                                    continue
                            
                            if not read_success:
                                logger.warning(f"Could not decode file '{file_db_key_path}' with any encoding, treating as binary.")
                                content_lines = BINARY_CONTENT_PLACEHOLDER
                                
                        except Exception as e_read:
                            logger.warning(f"Error reading file '{file_db_key_path}': {e_read}")
                            content_lines = [f"Error: Could not read file content. Reason: {type(e_read).__name__}\n"]


                except MetadataError:
                    # Re-raise MetadataError to be caught by outer try block
                    raise
                except FileNotFoundError:
                    _log_util_message(logging.WARNING, f"File '{temp_file_full_path}' not found during db update (deleted concurrently?).")
                    content_lines = [f"<Error: File not found during update>"] # Or skip adding it
                except Exception as e_stat:
                    _log_util_message(logging.ERROR, f"Error stating or reading file '{temp_file_full_path}': {e_stat}")
                    content_lines = [f"<Error processing file: {type(e_stat).__name__}>"]

                # Ensure we have metadata even in error cases
                if file_metadata is None:
                    original_entry = original_state.get(file_db_key_path, {})
                    
                    # Determine if THIS SPECIFIC FILE's access time should be updated
                    this_file_accessed = should_update_atime and file_db_key_path in accessed_files
                    
                    if not file_actually_changed and original_entry.get("metadata"):
                        # File didn't change - use original metadata as base
                        file_metadata = original_entry["metadata"].copy()
                        
                        # If this file was specifically accessed, update its access_time from sandbox
                        if this_file_accessed:
                            fresh_metadata = _collect_file_metadata(temp_file_full_path)
                            if fresh_metadata and "timestamps" in fresh_metadata:
                                file_metadata["timestamps"]["access_time"] = fresh_metadata["timestamps"]["access_time"]
                    else:
                        # File changed or no original metadata - collect fresh metadata from sandbox
                        file_metadata = _collect_file_metadata(temp_file_full_path)
                    
                    # If still no metadata after collection attempt:
                    if not file_metadata:
                        # Check if this specific file should have its access time updated (even in error case)
                        error_case_should_update_atime = should_update_atime and file_db_key_path in accessed_files
                        
                        if not error_case_should_update_atime:
                            # Create default metadata but preserve access time
                            file_metadata = {
                                "attributes": {
                                    "is_symlink": False,
                                    "is_hidden": False,
                                    "is_readonly": False,
                                    "symlink_target": None  # Initialize to None in error case
                                },
                                "timestamps": {
                                    "access_time": get_current_timestamp_iso(),
                                    "modify_time": get_current_timestamp_iso(),
                                    "change_time": get_current_timestamp_iso()
                                }
                            }
                            
                            # Preserve original access time if available
                            original_metadata = original_entry.get("metadata", {})
                            if original_metadata and "timestamps" in original_metadata and "access_time" in original_metadata["timestamps"]:
                                file_metadata["timestamps"]["access_time"] = original_metadata["timestamps"]["access_time"]
                        else:
                            # This file was accessed, create fresh metadata with updated access time
                            file_metadata = {
                                "attributes": {
                                    "is_symlink": False,
                                    "is_hidden": False,
                                    "is_readonly": False,
                                    "symlink_target": None  # Initialize to None in error case
                                },
                                "timestamps": {
                                    "access_time": get_current_timestamp_iso(),  # Updated access time
                                    "modify_time": get_current_timestamp_iso(),
                                    "change_time": get_current_timestamp_iso()
                                }
                            }

                new_file_system[file_db_key_path] = {
                    "path": file_db_key_path,
                    "is_directory": False,
                    "content_lines": content_lines,
                    "size_bytes": size_bytes,
                    "last_modified": last_modified,
                    "metadata": file_metadata  # Add metadata for file
                }
                processed_paths.add(file_db_key_path)
        
        # Logic for handling deleted files/directories:
        # Paths in original_file_system_state that are NOT in processed_paths were deleted.
        # new_file_system now contains all existing items.
        original_logical_paths = set(original_state.keys())
        current_logical_paths_found = processed_paths # More accurate than new_file_system.keys() before assignment
        
        paths_implicitly_deleted = original_logical_paths - current_logical_paths_found
        if paths_implicitly_deleted:
            _log_util_message(logging.INFO, f"Paths removed during command execution: {paths_implicitly_deleted}")

        db["workspace_root"] = final_logical_root_for_db
        
        # CWD handling (relying on run_terminal_cmd's finally block for most precise restoration)
        # For safety, ensure CWD is at least within the new logical root if it's somehow very off.
        current_logical_cwd = _normalize_path_for_db(db.get("cwd", final_logical_root_for_db))
        if not current_logical_cwd.startswith(final_logical_root_for_db) and current_logical_cwd != final_logical_root_for_db :
            if final_logical_root_for_db == "/" and current_logical_cwd.startswith("/"): # If root is / and CWD is absolute, it's fine
                pass
            else:
                db["cwd"] = final_logical_root_for_db # Reset to root if CWD seems invalid relative to new root.
        
        db["file_system"] = new_file_system

        # Access time handling is now done in the main collection loop above

        _log_util_message(logging.INFO, f"Internal state (global db) updated from temp dir '{temp_root}'. New logical root: '{final_logical_root_for_db}'. Items: {len(new_file_system)}.")

        # --- PATCH: Always restore .git if it was present in the original workspace but missing after update ---
        original_git_dir = os.path.join(final_logical_root_for_db, ".git")
        temp_git_backup = None
        # Check if .git was present in the original state but is missing now
        had_git = any(
            k for k in original_state.keys()
            if os.path.normpath(k) == os.path.normpath(original_git_dir) or os.path.normpath(k).startswith(os.path.normpath(original_git_dir + os.sep))
        )
        has_git_now = os.path.exists(original_git_dir) and os.path.isdir(original_git_dir)
        if had_git and not has_git_now:
            # Try to restore .git from a backup if it exists in the temp dir
            # Or, if it still exists in the temp_root, move it back
            temp_git_dir = os.path.join(normalized_temp_root, ".git")
            if os.path.exists(temp_git_dir):
                shutil.move(temp_git_dir, original_git_dir)
                _log_util_message(logging.INFO, f"Restored .git directory to {original_git_dir} from temp dir.")
            else:
                _log_util_message(logging.WARNING, f".git directory was present before command but is missing after update. Manual restoration may be required.")

    except MetadataError as me:
        _log_util_message(logging.ERROR, f"Metadata operation failed in strict mode: {me}", exc_info=True)
        raise  # Re-raise to be caught by run_command
    except Exception as e:
        _log_util_message(logging.ERROR, f"Update process failed in update_db_file_system_from_temp: {e}", exc_info=True)
        raise

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

def _collect_file_metadata(file_path: str) -> Dict[str, Any]:
    """Helper function to collect file metadata.
    
    Args:
        file_path (str): Path to the file to collect metadata from
        
    Returns:
        Dict[str, Any]: Dictionary containing the file's metadata
        
    Note:
        change_time (ctime) is collected for informational purposes but cannot be
        restored via _apply_file_metadata since it's managed by the filesystem kernel.
        Only access_time and modify_time can be set via os.utime().
    """
    try:
        stat_info = os.stat(file_path, follow_symlinks=False)
        
        # Get timestamps
        access_time = datetime.datetime.fromtimestamp(stat_info.st_atime, tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        modify_time = datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        change_time = datetime.datetime.fromtimestamp(stat_info.st_ctime, tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")  # Cannot be restored, kernel-managed
        
        # Get file attributes
        is_symlink = os.path.islink(file_path)
        is_hidden = os.path.basename(file_path).startswith('.')
        
        metadata = {
            "attributes": {
                "is_symlink": is_symlink,
                "is_hidden": is_hidden,
                "is_readonly": not os.access(file_path, os.W_OK),
                "symlink_target": None  # Initialize to None by default
            },
            "timestamps": {
                "access_time": access_time,
                "modify_time": modify_time,
                "change_time": change_time
            },
            "permissions": {
                "mode": stat_info.st_mode & 0o777,
                "uid": stat_info.st_uid,
                "gid": stat_info.st_gid
            }
        }
        
        # Add symlink target if it's a symlink
        if is_symlink:
            metadata["attributes"]["symlink_target"] = os.readlink(file_path)
            
        return metadata
        
    except (OSError, IOError) as e:
        logger.warning(f"Error collecting metadata for '{file_path}': {e}")
        return {
            "attributes": {
                "is_symlink": False,
                "is_hidden": False,
                "is_readonly": False,
                "symlink_target": None  # Initialize to None in error case
            },
            "timestamps": {
                "access_time": get_current_timestamp_iso(),
                "modify_time": get_current_timestamp_iso(),
                "change_time": get_current_timestamp_iso()
            },
            "permissions": {
                "mode": 0o644,
                "uid": os.getuid() if hasattr(os, 'getuid') else 1000,
                "gid": os.getgid() if hasattr(os, 'getgid') else 1000
            }
        }

def _apply_file_metadata(file_path: str, metadata: Dict[str, Any], strict_mode: bool = False) -> None:
    """Helper function to apply file metadata.
    
    Args:
        file_path (str): Path to the file to apply metadata to
        metadata (Dict[str, Any]): Metadata to apply
        strict_mode (bool): Whether to raise errors on metadata application failures
    """
    try:
        # Apply permissions (mode, uid, gid) if present
        permissions = metadata.get("permissions", {})
        if permissions and os.path.exists(file_path) and not os.path.islink(file_path):
            mode = permissions.get("mode")
            uid = permissions.get("uid")
            gid = permissions.get("gid")
            try:
                if mode is not None:
                    os.chmod(file_path, mode)
            except Exception as e:
                logger.warning(f"Could not set mode for '{file_path}': {e}")
            try:
                if uid is not None and gid is not None:
                    os.chown(file_path, uid, gid)
            except Exception as e:
                logger.warning(f"Could not set ownership for '{file_path}': {e}")
        # Apply timestamps - restore access_time and modify_time normally during hydration
        timestamps = metadata.get("timestamps", {})
        if timestamps:
            current_time = time.time()
            
            # Restore modify_time if available
            mtime = current_time
            if "modify_time" in timestamps:
                try:
                    mtime = datetime.datetime.fromisoformat(timestamps["modify_time"].replace("Z", "+00:00")).timestamp()
                except Exception:
                    pass
            
            # Restore access_time if available
            atime = current_time
            if "access_time" in timestamps:
                try:
                    atime = datetime.datetime.fromisoformat(timestamps["access_time"].replace("Z", "+00:00")).timestamp()
                except Exception:
                    atime = mtime  # Fallback to mtime
            else:
                atime = mtime
            
            # Apply the timestamps normally
            os.utime(file_path, (atime, mtime), follow_symlinks=False)

        # Apply read-only attribute
        attrs = metadata.get("attributes", {})
        if os.path.exists(file_path) and not os.path.islink(file_path):
            is_readonly = attrs.get("is_readonly", False)
            mode = os.stat(file_path).st_mode
            if is_readonly:
                # Remove write permissions for owner, group, others
                new_mode = mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH
                os.chmod(file_path, new_mode)
            else:
                # Add write permissions for owner (at least)
                new_mode = mode | stat.S_IWUSR
                os.chmod(file_path, new_mode)

        # Apply hidden attribute (Unix: ensure dot prefix)
        is_hidden = attrs.get("is_hidden", False)
        base = os.path.basename(file_path)
        dir_ = os.path.dirname(file_path)
        if is_hidden and not base.startswith('.') and os.path.exists(file_path):
            # Rename to add dot prefix
            new_path = os.path.join(dir_, '.' + base)
            if not os.path.exists(new_path):
                os.rename(file_path, new_path)
        elif not is_hidden and base.startswith('.') and os.path.exists(file_path):
            # Optionally, rename to remove dot (not always safe, so skip)
            pass

    except (OSError, IOError) as e:
        msg = f"Error applying metadata to '{file_path}': {e}"
        if strict_mode:
            raise MetadataError(msg)
        else:
            logger.warning(msg)

def _should_update_access_time(command: str) -> bool:
    """
    Determine if a command should update access time based on realistic filesystem behavior.
    
    Args:
        command: The command being executed
        
    Returns:
        bool: True if the command should update access time
    """
    import sys
    # Fix the double import issue by checking both possible module names
    access_time_mode = ACCESS_TIME_MODE  # Default to current module's variable
    
    # Check if the APIs.common_utils.terminal_filesystem_utils module exists and use its variable
    apis_module_name = 'APIs.common_utils.terminal_filesystem_utils'
    if apis_module_name in sys.modules:
        apis_module = sys.modules[apis_module_name]
        if hasattr(apis_module, 'ACCESS_TIME_MODE'):
            access_time_mode = apis_module.ACCESS_TIME_MODE
    
    if access_time_mode == "noatime":
        return False
    
    if access_time_mode == "atime":
        return True
    
    # For "relatime" mode, be more selective about what updates atime
    command = command.strip().split()[0] if command.strip() else ""
    
    # Commands that typically read file content (should update atime in relatime)
    content_reading_commands = {
        'cat', 'less', 'more', 'head', 'tail', 'grep', 'awk', 'sed',
        'sort', 'uniq', 'wc', 'diff', 'cmp', 'file', 'strings',
        'hexdump', 'od', 'xxd', 'vim', 'nano', 'emacs'
    }
    
    # Commands that only read metadata or directory listings (shouldn't update atime in relatime)
    metadata_only_commands = {
        'ls', 'stat', 'find', 'du', 'df', 'tree', 'locate',
        'which', 'whereis', 'pwd', 'dirname', 'basename'
    }
    
    if command in content_reading_commands:
        return True
    elif command in metadata_only_commands:
        return False
    else:
        # For unknown commands, be conservative and update atime
        return True

def collect_pre_command_metadata_state(
    file_system: Dict[str, Any],
    exec_env_root: str,
    workspace_root: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Collect file metadata state from the PHYSICAL SANDBOX before command execution,
    but key the results by LOGICAL path for consistent comparison.
    """
    state = {}
    normalized_workspace_root = _normalize_path_for_db(workspace_root)

    for logical_path in file_system.keys():
        try:
            normalized_logical_path = _normalize_path_for_db(logical_path)
            
            if normalized_logical_path == normalized_workspace_root:
                rel_path = '.'
            else:
                if not normalized_logical_path.startswith(normalized_workspace_root):
                    continue
                rel_path = os.path.relpath(normalized_logical_path, normalized_workspace_root)
            
            physical_path = _normalize_path_for_db(os.path.join(exec_env_root, rel_path))

            if os.path.exists(physical_path) or os.path.islink(physical_path):
                 # Use the logical path as the key
                 state[normalized_logical_path] = {"metadata": _collect_file_metadata(physical_path)}

        except (ValueError, TypeError) as e:
            logger.warning(f"Could not process path {logical_path} during pre-command state collection: {e}")
            continue
    return state


def collect_post_command_metadata_state(
    file_system: Dict[str, Any],
    exec_env_root: str,
    workspace_root: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Collect file metadata state from the PHYSICAL SANDBOX after command execution,
    but key the results by LOGICAL path for consistent comparison.
    """
    state = {}
    normalized_workspace_root = _normalize_path_for_db(workspace_root)

    for logical_path in file_system.keys():
        try:
            normalized_logical_path = _normalize_path_for_db(logical_path)
            
            if normalized_logical_path == normalized_workspace_root:
                rel_path = '.'
            else:
                if not normalized_logical_path.startswith(normalized_workspace_root):
                    continue
                rel_path = os.path.relpath(normalized_logical_path, normalized_workspace_root)
            
            physical_path = _normalize_path_for_db(os.path.join(exec_env_root, rel_path))

            if os.path.exists(physical_path) or os.path.islink(physical_path):
                 # Use the logical path as the key
                 state[normalized_logical_path] = {"metadata": _collect_file_metadata(physical_path)}

        except (ValueError, TypeError) as e:
            logger.warning(f"Could not process path {logical_path} during post-command state collection: {e}")
            continue
    return state


def preserve_unchanged_change_times(
    db_file_system: Dict[str, Any],
    pre_command_state: Dict[str, Dict[str, Any]],
    post_command_state: Dict[str, Dict[str, Any]],
    original_filesystem_state: Dict[str, Any],
    current_workspace_root_norm: str,
    exec_env_root: str
) -> None:
    """
    Preserve original change_time for files that didn't actually change during command execution.
    
    NOTE: This function should ONLY preserve change_time (ctime), not access_time or modify_time.
    Access_time and modify_time are already handled correctly in update_db_file_system_from_temp.
    """
    for path, file_info in db_file_system.items():
        # The path is the LOGICAL path, which is now the key for all dictionaries.
        
        pre_metadata = pre_command_state.get(path, {}).get("metadata", {}).get("timestamps", {}) or {}
        post_metadata = post_command_state.get(path, {}).get("metadata", {}).get("timestamps", {}) or {}

        pre_modify_time = pre_metadata.get("modify_time")
        post_modify_time = post_metadata.get("modify_time")

        # If mtime is different, content was modified. Let all timestamps update (including ctime).
        if pre_modify_time != post_modify_time:
            continue

        # If mtime is the same, content wasn't modified.
        # Preserve the original ctime to prevent `ls` etc. from marking file as "changed".
        # But DO NOT touch access_time here - it's already correctly set in update_db_file_system_from_temp
        original_change_time = original_filesystem_state.get(path, {}).get("metadata", {}).get("timestamps", {}).get("change_time")
        if original_change_time and "metadata" in file_info and "timestamps" in file_info["metadata"]:
            file_info["metadata"]["timestamps"]["change_time"] = original_change_time

def _extract_file_paths_from_command(command: str, workspace_root: str, current_cwd: str = None) -> set:
    """
    Extract file paths that might be accessed by the command.
    
    Args:
        command: The command string
        workspace_root: The workspace root path
        current_cwd: The current working directory (optional, defaults to workspace_root)
        
    Returns:
        set: Set of absolute file paths that might be accessed by the command
    """
    if not command or not command.strip():
        return set()
    
    # In noatime mode, no commands should update access time
    import sys
    access_time_mode = ACCESS_TIME_MODE  # Default to current module's variable
    
    # Check if the APIs.common_utils.terminal_filesystem_utils module exists and use its variable
    apis_module_name = 'APIs.common_utils.terminal_filesystem_utils'
    if apis_module_name in sys.modules:
        apis_module = sys.modules[apis_module_name]
        if hasattr(apis_module, 'ACCESS_TIME_MODE'):
            access_time_mode = apis_module.ACCESS_TIME_MODE
    
    if access_time_mode == "noatime":
        return set()
    
    parts = command.strip().split()
    if not parts:
        return set()
    
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    accessed_files = set()
    
    # Commands that typically access files mentioned as arguments
    file_reading_commands = {
        'cat', 'less', 'more', 'head', 'tail', 'grep', 'awk', 'sed',
        'sort', 'uniq', 'wc', 'diff', 'cmp', 'file', 'strings',
        'hexdump', 'od', 'xxd', 'vim', 'nano', 'emacs', 'cp', 'mv'
    }
    
    # In "atime" mode, even metadata commands should be considered as accessing files
    metadata_commands = {
        'ls', 'stat', 'find', 'du', 'df', 'tree', 'locate',
        'which', 'whereis'
    }
    
    # Determine which commands to process based on ACCESS_TIME_MODE
    commands_to_process = set()
    if access_time_mode == "atime":
        # In atime mode, both content and metadata commands update access time
        commands_to_process = file_reading_commands | metadata_commands
    elif access_time_mode == "relatime":
        # In relatime mode, only content-reading commands matter
        commands_to_process = file_reading_commands
    # In noatime mode, no commands should update access time (handled above)
    
    # Special handling for commands with redirection (even if cmd is not in commands_to_process)
    # Commands like "echo content >> file.txt" should update access time of file.txt
    redirection_operators = ['>', '>>', '<']
    has_redirection = any(op in args for op in redirection_operators)
    
    if cmd in commands_to_process or has_redirection:
        # Use provided current working directory or default to workspace_root
        if current_cwd is None:
            current_cwd = workspace_root
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            # Skip flags (arguments starting with -)
            if arg.startswith('-'):
                i += 1
                continue
                
            # Handle redirection operators
            if arg in redirection_operators:
                # The next argument after redirection operator is the file being accessed
                if i + 1 < len(args):
                    file_arg = args[i + 1]
                    try:
                        if os.path.isabs(file_arg):
                            abs_path = _normalize_path_for_db(file_arg)
                        else:
                            abs_path = _normalize_path_for_db(os.path.join(current_cwd, file_arg))
                        
                        if abs_path.startswith(workspace_root):
                            accessed_files.add(abs_path)
                    except:
                        pass
                    i += 2  # Skip both the operator and the file argument
                    continue
                else:
                    i += 1
                    continue
            
            # Skip other shell constructs
            if arg in ['|', '&&', '||', ';']:
                i += 1
                continue
            
            # For file-reading commands, also process direct file arguments
            if cmd in commands_to_process:
                try:
                    if os.path.isabs(arg):
                        abs_path = _normalize_path_for_db(arg)
                    else:
                        abs_path = _normalize_path_for_db(os.path.join(current_cwd, arg))
                    
                    if abs_path.startswith(workspace_root):
                        accessed_files.add(abs_path)
                except:
                    pass
            
            i += 1
    
    return accessed_files

def _extract_last_unquoted_redirection_target(command: str) -> Optional[str]:
    """
    Helper: detect the last unquoted redirection target (>, >>, n>), ignoring content inside quotes
    and here-doc bodies embedded within quoted strings (e.g., bash/sh -c "cat << 'EOF' > file ...").
    Returns the filename token if found, otherwise None.
    """
    in_single = False
    in_double = False
    i = 0
    last_target: Optional[str] = None

    # If this is a bash/sh -c invocation, try to extract the inner command.
    lowered = command.lower()
    scan_str = command

    try:
        # Very light-weight parse for: (bash|sh) -c "..."  or  (bash|sh) -c '...'
        if ("bash" in lowered or "sh" in lowered) and " -c " in lowered:
            # Find the -c occurrence
            c_index = lowered.find(" -c ")
            # Find the opening quote after -c
            j = c_index + 4
            while j < len(command) and command[j].isspace():
                j += 1
            if j < len(command) and command[j] in ['"', "'"]:
                quote = command[j]
                j += 1
                start = j
                while j < len(command) and command[j] != quote:
                    # support simple escaping of the same quote with \\
                    if command[j] == '\\' and j + 1 < len(command) and command[j+1] == quote:
                        j += 2
                        continue
                    j += 1
                inner = command[start:j]
                scan_str = inner
    except Exception:
        # Fall back to scanning the full command
        scan_str = command

    # Skip parsing if a here-doc is present; body may contain arbitrary '>' characters.
    if "<<" in scan_str:
        return None

    # Scan for unquoted '>' operators in the scan_str
    i = 0
    in_single = False
    in_double = False
    while i < len(scan_str):
        ch = scan_str[i]
        if ch == "'" and not in_double:
            in_single = not in_single
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue
        if ch == '>' and not in_single and not in_double:
            j = i + 1
            # Skip additional '>' (for >>) and optional spaces
            while j < len(scan_str) and scan_str[j] in ['>', ' ', '\t']:
                j += 1
            # Capture quoted or unquoted filename token
            if j < len(scan_str):
                if scan_str[j] in ['"', "'"]:
                    quote = scan_str[j]
                    j += 1
                    start = j
                    while j < len(scan_str) and scan_str[j] != quote:
                        j += 1
                    token = scan_str[start:j]
                else:
                    start = j
                    # Stop at whitespace or shell metacharacters
                    metachars = set([' ', '\t', '\n', '&', '|', ';', '<', '>'])
                    while j < len(scan_str) and scan_str[j] not in metachars:
                        j += 1
                    token = scan_str[start:j]
                if token:
                    last_target = token
            i = j
            continue
        i += 1

    return last_target

def find_binary_files(file_system: Dict[str, Any]) -> List[str]:
    """
    Find all binary files in the file system.
    """
    binary_files = []
    
    for path, file_info in file_system.items():
        content_lines = file_info.get("content_lines", [])
        first_line = content_lines[0] if content_lines else None
        if first_line and first_line.strip() == BINARY_FILE_MARKER:
            binary_files.append(path)
    return binary_files


def detect_and_fix_tar_command(command: str, execution_cwd: str) -> str:
    """Detects tar commands that try to create archives in the same directory they're archiving.
    
    This function addresses the issue where tar commands like 'tar -czf ./project_backup.tar.gz .'
    fail in temporary directories because they try to include the backup file they're creating
    in the archive itself, causing "file changed as we read it" errors.
    
    Args:
        command (str): The original command string
        execution_cwd (str): The current working directory where the command will be executed
        
    Returns:
        str: The modified command string if tar issue was detected and fixed, otherwise the original command
    """
    # Pattern to match tar commands with relative output files in current directory
    tar_pattern = r'(tar\s+[a-zA-Z0-9\-]*[czf])\s+([^\s]+)\s+\.'
    
    match = re.search(tar_pattern, command.strip())
    if not match:
        return command
    
    # Normalize whitespace in tar flags (e.g., "tar   -czf" -> "tar -czf")
    tar_flags = re.sub(r'\s+', ' ', match.group(1))
    output_file = match.group(2)
    
    # Check if output file is in current directory (starts with ./ or is just a filename)
    if output_file.startswith('./') or not os.path.isabs(output_file) and '/' not in output_file:
        # Extract just the filename
        filename = os.path.basename(output_file)
        
        # Create a modified command that creates the archive in parent directory then moves it back
        parent_dir = os.path.dirname(execution_cwd)
        temp_archive = os.path.join(parent_dir, filename)
        
        # Create a command that:
        # 1. Creates the archive in parent directory
        # 2. Moves it to the desired location
        modified_command = f"{tar_flags} {temp_archive} . && mv {temp_archive} {output_file}"
        
        _log_util_message(logging.INFO, f"Detected tar command creating archive in same directory. Modified command: {modified_command}")
        return modified_command
    
    return command


def _extract_last_pipeline_segment(command: str) -> str:
    """Return the last pipeline segment of a shell command string."""
    try:
        parts = command.split('|')
        if not parts:
            return command.strip()
        return parts[-1].strip()
    except Exception:
        return command.strip()


def _extract_last_simple_command(command: str) -> str:
    """Return the last simple command by trimming shell separators ;, &&, || before pipelines.

    This helps identify the command that determines the final exit code of a compound statement.
    """
    try:
        segment = command
        # Trim trailing whitespace
        segment = segment.strip()
        # Split by ';' and take last
        if ';' in segment:
            segment = segment.rsplit(';', 1)[-1].strip()
        # Split by logical AND/OR and take last
        # Note: order matters; use rsplit to take the last split if present
        for sep in ('&&', '||'):
            if sep in segment:
                segment = segment.rsplit(sep, 1)[-1].strip()
        # Finally, keep only the last pipeline segment
        segment = _extract_last_pipeline_segment(segment)
        return segment
    except Exception:
        return command.strip()


def identify_primary_command(command: str) -> str:
    """Identify the canonical primary command for policy lookup.

    Examples:
      - "grep -R foo ." -> "grep"
      - "git diff --exit-code" -> "git diff"
      - "diff a b" -> "diff"
      - "cmp -s a b" -> "cmp"
      - "test -f file" -> "test"
    """
    try:
        last = _extract_last_simple_command(command)
        tokens = shlex.split(last)
        if not tokens:
            return ""
        if tokens[0] == 'git' and len(tokens) > 1:
            # Return canonical form 'git <subcmd>' for policy mapping
            return f"git {tokens[1]}"
        if tokens[0] == 'ssh-keygen' and any(t == '-F' for t in tokens[1:]):
            return 'ssh-keygen -F'
        if tokens[0] == 'jq' and any(t == '-e' for t in tokens[1:]):
            return 'jq -e'
        if tokens[0] == 'nc' and any(t == '-z' for t in tokens[1:]):
            return 'nc -z'
        if tokens[0] == 'rpm' and any(t == '-q' for t in tokens[1:]):
            return 'rpm -q'
        if tokens[0] == 'dpkg' and any(t == '-s' for t in tokens[1:]):
            return 'dpkg -s'
        if tokens[0] == 'dpkg-query' and any(t == '-W' for t in tokens[1:]):
            return 'dpkg-query -W'
        if tokens[0] == 'apk' and len(tokens) > 1 and tokens[1] == 'info':
            if any(t == '-e' for t in tokens[2:]):
                return 'apk info -e'
            return 'apk info'
        if tokens[0] == 'pacman' and any(t == '-Qi' for t in tokens[1:]):
            return 'pacman -Qi'
        if tokens[0] in ('pip', 'pip3') and any(t == 'show' for t in tokens[1:2]):
            return f"{tokens[0]} show"
        if tokens[0] == 'helm' and len(tokens) > 1 and tokens[1] == 'status':
            return 'helm status'
        if tokens[0] == 'supervisorctl' and len(tokens) > 1 and tokens[1] == 'status':
            return 'supervisorctl status'
        return tokens[0]
    except Exception:
        return ""


def get_allowed_nonzero_exit_codes(primary_command: str) -> set:
    """Return allowed non-zero exit codes for known commands that use codes to signal conditions.

    By default, many Unix tools use 1 to represent a meaningful condition rather than an error.
    """
    policy = {
        # Searchers
        'grep': {1},          # 1 = no matches
        'egrep': {1},         # legacy grep -E
        'fgrep': {1},         # legacy grep -F
        'rg': {1},            # ripgrep: 1 = no matches
        'ag': {1},            # the silver searcher: 1 = no matches
        'ack': {1},           # ack: 1 = no matches
        'git grep': {1},      # git grep: 1 = no matches

        # File comparison/merge tools
        'diff': {1},          # 1 = files differ
        'sdiff': {1},         # 1 = files differ (side-by-side)
        'cmp': {1},           # 1 = files differ
        'diff3': {1},         # 1 = conflicts found (non-fatal condition)

        # Condition evaluation
        'test': {1},          # 1 = condition false
        '[': {1},             # shell builtin-style test
        'false': {1},         # returns 1 by definition (logical false)
        'expr': {1},          # 1 = expression false/empty; 2 = error

        # Process queries
        'pgrep': {1},         # 1 = no processes matched
        'pkill': {1},         # 1 = no processes matched
        'pidof': {1},         # 1 = program not running

        # Git subcommands
        'git diff': {1},      # 1 = changes present with --exit-code/--quiet

        # Timeouts (GNU coreutils)
        'timeout': {124},     # 124 = command timed out

        # Which/where lookups
        'which': {1},         # 1 = not found

        # Mount checks
        'mountpoint': {1, 32},    # 1 = not a mountpoint, 32 = environment-related error (treated as non-fatal here)

        # Checksums (verification mode)
        'md5sum': {1},        # 1 = at least one file failed verification (-c)
        'sha1sum': {1},
        'sha256sum': {1},

        # Infrastructure tools
        'terraform': {2},     # 2 = changes present (with -detailed-exitcode)
        'rsync': {24},        # 24 = partial transfer due to vanished files (often non-fatal)

        # Systemd status probes
        'systemctl': {1, 3, 4},  # 1 (e.g., is-enabled disabled), 3 inactive, 4 unknown

        # Networking/tools with conditional semantics
        'ping': {1},          # 1 = no reply received
        'fuser': {1},         # 1 = no process is using the file/socket
        'lsof': {1},          # 1 = no open files match criteria

        # Scheduling
        'crontab': {1},       # 1 = no crontab for user (crontab -l)

        # Firewall check existence
        'iptables': {1},      # 1 = rule not present (e.g., -C check)
        'ip6tables': {1},

        # Directory services / lookups and network name resolution
        'locate': {1},        # 1 = no matches
        'getent': {1},        # 1 = not found; 2 invalid DB
        'host': {1},          # 1 = not found/NXDOMAIN
        'nslookup': {1},      # 1 = query failure (varies by implementation)
        'ssh-keygen -F': {1}, # 1 = host not present in known_hosts
        'jq -e': {1},         # 1 = filter false/null
        'nc -z': {1},         # 1 = port closed
        'umount': {32},       # 32 = not mounted/target busy (probe contexts)
        'service': {1, 3, 4}, # LSB status codes: not running/inactive/unknown
        'supervisorctl status': {1}, # 1 = not running/not found

        # Package managers / presence
        'rpm -q': {1},
        'dpkg -s': {1},
        'dpkg-query -W': {1},
        'apk info': {1},
        'apk info -e': {1},
        'pacman -Qi': {1},
        'pip show': {1},
        'pip3 show': {1},
        'helm status': {1},

        # Git object/presence probes
        'git check-ignore': {1},
        'git ls-files': {1},          # with --error-unmatch
        'git cat-file': {1},          # -e <obj> not found
    }
    return policy.get(primary_command, set())


def should_treat_nonzero_as_success(command: str, returncode: int) -> bool:
    """Determine whether a non-zero exit code should be considered a successful outcome.

    This does not change the return code; it informs callers to NOT raise/rollback and proceed
    as a successful execution, returning the result with the original returncode.
    """
    if returncode == 0:
        return True
    primary = identify_primary_command(command)
    allowed = get_allowed_nonzero_exit_codes(primary)
    return returncode in allowed


def prepare_command_environment(db: Dict[str, Any], physical_cwd: str, logical_cwd: str) -> Dict[str, str]:
    """
    Prepare an isolated environment dictionary for command execution.
    
    This is the centralized implementation used by all terminal-like APIs
    (cursor, terminal, gemini_cli) to ensure consistent environment setup.
    
    Args:
        db: The database dictionary containing environment configuration
        physical_cwd: The physical temporary directory path for command execution.
        logical_cwd: The logical workspace path that the shell should believe it is in.
    
    Returns:
        Dict[str, str]: The prepared environment dictionary
    """
    # Initialize with base environment variables
    # Inherit PATH from parent to allow access to system tools (Java, Maven, Node, etc.)
    env: Dict[str, str] = {
        'PWD': logical_cwd,
        'SHELL': '/bin/bash',
        'USER': 'user',
        'HOME': '/home/user',
        'PATH': os.environ.get('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
        'TERM': 'xterm-256color',
        'LANG': 'en_US.UTF-8',
        'LC_ALL': 'en_US.UTF-8',
        'HOSTNAME': 'isolated-env',
        'TZ': 'UTC'
    }
    
    # Add workspace environment variables (overriding base vars)
    workspace_env = db.get('environment', {}).get('workspace', {})
    env.update(workspace_env)
    
    # Add session environment variables (overriding workspace and base vars)
    session_env = db.get('environment', {}).get('session', {})
    env.update(session_env)
    
    return env

def expand_variables(command: str, env: Dict[str, str]) -> str:
    """
    Expand environment variables in the command string.
    
    Args:
        command: The command string potentially containing environment variables
        env: The environment dictionary to use for expansion
    
    Returns:
        str: The command with environment variables expanded
    """
    result = []
    i = 0
    in_single_quotes = False
    in_double_quotes = False
    
    while i < len(command):
        char = command[i]
        
        # Handle quotes
        if char == "'" and not in_double_quotes:
            in_single_quotes = not in_single_quotes
            result.append(char)
            i += 1
            continue
        elif char == '"' and not in_single_quotes:
            in_double_quotes = not in_double_quotes
            result.append(char)
            i += 1
            continue
        
        # Handle variable expansion
        if char == '$' and not in_single_quotes:
            if i + 1 < len(command):
                next_char = command[i + 1]
                if next_char == '{':
                    # ${VAR} format
                    end_brace = command.find('}', i)
                    if end_brace != -1:
                        var_name = command[i+2:end_brace]
                        if var_name in env:
                            result.append(env[var_name])
                        else:
                            result.append('')  # Unset variables expand to empty string
                        i = end_brace + 1
                        continue
                elif next_char.isalpha() or next_char == '_':
                    # $VAR format
                    j = i + 1
                    while j < len(command) and (command[j].isalnum() or command[j] == '_'):
                        j += 1
                    var_name = command[i+1:j]
                    if var_name in env:
                        result.append(env[var_name])
                    else:
                        result.append('')  # Unset variables expand to empty string
                    i = j
                    continue
                else:
                    # Preserve $ if not followed by a valid variable name
                    result.append(char)
                    i += 1
                    continue
            else:
                # Preserve $ at end of string
                result.append(char)
                i += 1
                continue
        
        result.append(char)
        i += 1
    
    return ''.join(result)

def handle_env_command(command: str, db: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle environment variable commands (export, unset, env).
    
    Args:
        command: The command string to handle
        db: The database dictionary containing environment configuration
    
    Returns:
        Dict[str, Any]: Command execution result with all required keys
    """
    # Initialize environment if not present
    if 'environment' not in db:
        db['environment'] = {'system': {}, 'workspace': {}, 'session': {}}
    
    # Get current directory for result
    current_cwd = db.get("cwd", db.get("workspace_root", "/tmp"))
    
    if command.startswith('export '):
        # Handle export VAR=value
        var_assignment = command[7:].strip()
        if '=' not in var_assignment:
            return {
                'command': command,
                'directory': current_cwd,
                'stdout': '',
                'stderr': 'export: Invalid syntax. Use: export VAR=value\n',
                'returncode': 1,
                'pid': None,
                'process_group_id': None,
                'signal': None,
                'message': 'Export command failed: Invalid syntax'
            }
        
        key, value = var_assignment.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Remove quotes if present
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
            # Don't expand variables if the value was in single quotes
            if not value.startswith("'"):
                env = prepare_command_environment(db, '/tmp', current_cwd)  # temp dir not important for expansion
                value = expand_variables(value, env)
        else:
            # Expand variables in unquoted values
            env = prepare_command_environment(db, '/tmp', current_cwd)  # temp dir not important for expansion
            value = expand_variables(value, env)
        
        # Store the value in the session environment
        db['environment']['session'][key] = value
        return {
            'command': command,
            'directory': current_cwd,
            'stdout': '',
            'stderr': '',
            'returncode': 0,
            'pid': None,
            'process_group_id': None,
            'signal': None,
            'message': f'Exported {key}={value}'
        }
    
    elif command.startswith('unset '):
        # Handle unset VAR
        var = command[6:].strip()
        session_env = db['environment']['session']
        workspace_env = db['environment']['workspace']
        
        if var in session_env:
            del session_env[var]
            return {
                'command': command,
                'directory': current_cwd,
                'stdout': '',
                'stderr': '',
                'returncode': 0,
                'pid': None,
                'process_group_id': None,
                'signal': None,
                'message': f'Unset {var} from session environment'
            }
        elif var in workspace_env:
            del workspace_env[var]
            return {
                'command': command,
                'directory': current_cwd,
                'stdout': '',
                'stderr': '',
                'returncode': 0,
                'pid': None,
                'process_group_id': None,
                'signal': None,
                'message': f'Unset {var} from workspace environment'
            }
        else:
            return {
                'command': command,
                'directory': current_cwd,
                'stdout': '',
                'stderr': '',
                'returncode': 0,
                'pid': None,
                'process_group_id': None,
                'signal': None,
                'message': f'Variable {var} was not set'
            }
    
    elif command == 'env':
        # Show all environment variables
        env = prepare_command_environment(db, '/tmp', current_cwd)  # temp dir not important for listing
        output_lines = [f'{k}={v}' for k, v in sorted(env.items())]
        return {
            'command': command,
            'directory': current_cwd,
            'stdout': '\n'.join(output_lines) + '\n',
            'stderr': '',
            'returncode': 0,
            'pid': None,
            'process_group_id': None,
            'signal': None,
            'message': 'Environment variables listed'
        }
    
    return {
        'command': command,
        'directory': current_cwd,
        'stdout': '',
        'stderr': f'Unknown environment command: {command}\n',
        'returncode': 1,
        'pid': None,
        'process_group_id': None,
        'signal': None,
        'message': 'Invalid environment command'
    }
