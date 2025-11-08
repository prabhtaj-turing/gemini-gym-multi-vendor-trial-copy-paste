# terminal/SimulationEngine/utils.py
import os
import logging

import inspect

import shutil
import subprocess
import time
import copy
import stat  # For file permission constants
import base64 # Added for base64 encoding of binary archive content
from functools import wraps
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, TypeVar

# Direct import of the database state
from .db import DB
from common_utils import terminal_filesystem_utils as common_utils

# --- Logger Setup for this utils.py module ---
logger = logging.getLogger(__name__)

# --- Common Directory Configuration ---
T = TypeVar('T')  # Type variable for the decorator
COMMON_DIRECTORY = '/content'  # Will be set by update_common_directory
DEFAULT_WORKSPACE = os.path.expanduser('~/content/workspace')  # Default path
ENABLE_COMMON_FILE_SYSTEM = False
_db_initialized = False

def set_enable_common_file_system(enable: bool) -> None:
    """Sets the enable_common_file_system flag.
    
    Args:
        enable (bool): Whether to enable the common file system.
        
    Raises:
        ValueError: If enable is not a boolean.
    """
    global ENABLE_COMMON_FILE_SYSTEM
    if not isinstance(enable, bool):
        raise ValueError("enable must be a boolean")
    ENABLE_COMMON_FILE_SYSTEM = enable

def update_common_directory(new_directory: str = None) -> None:
    """Updates the common directory path with validation.
    
    Args:
        new_directory (str, optional): Path to set as common directory. 
            If None, uses DEFAULT_WORKSPACE.
    """
    global COMMON_DIRECTORY
    directory_to_use = new_directory if new_directory else DEFAULT_WORKSPACE
    
    if not directory_to_use:
        raise ValueError("Common directory path cannot be empty")
    directory_to_use = os.path.expanduser(directory_to_use)
    if not os.path.isabs(directory_to_use):
        raise ValueError("Common directory must be an absolute path")
    os.makedirs(directory_to_use, exist_ok=True)
    COMMON_DIRECTORY = _normalize_path_for_db(directory_to_use)
    _log_util_message(logging.INFO, f"Common directory updated to: {COMMON_DIRECTORY}")

def get_common_directory() -> str:
    """Get the current common directory path.

    Returns:
        str: The current common directory path.

    Raises:
        RuntimeError: If no common directory has been set.
    """
    if COMMON_DIRECTORY is None:
        raise RuntimeError(
            "No common directory has been set. Call update_common_directory() first."
        )
    return COMMON_DIRECTORY

def hydrate_db_from_common_directory() -> bool:
    """Loads file system state from common directory."""
    global _db_initialized
    try:
        if not COMMON_DIRECTORY:
            raise ValueError("Common directory not set. Call update_common_directory first.")
        if not os.path.exists(COMMON_DIRECTORY):
            raise FileNotFoundError(f"Common directory not found: {COMMON_DIRECTORY}")
        success = hydrate_db_from_directory(DB, COMMON_DIRECTORY)
        _db_initialized = success
        return success
    except Exception as e:
        _log_util_message(logging.ERROR, f"Failed to hydrate DB from common directory: {e}")
        raise

def dehydrate_db_to_common_directory() -> None:
    """Dehydrate only file_system to the common directory, maintain workspace_root/cwd alignment.

    This function:
    1. Saves only the file system state to the common directory using safe dehydrate function
    2. Ensures workspace_root and cwd remain aligned with common directory after dehydration
    3. Does NOT save memory_storage or other non-file-system data
    4. Safely handles git repositories without destructive operations

    Raises:
        RuntimeError: If dehydration fails.
    """
    try:
        current_common_dir = get_common_directory()

        # CLEAN-AND-RECREATE: Remove existing directory contents first
        # This ensures deleted files are actually removed from the common directory
        if os.path.exists(current_common_dir):
            # Remove all contents but preserve the directory itself
            # EXCEPT preserve .git directory if it exists
            for item in os.listdir(current_common_dir):
                item_path = os.path.join(current_common_dir, item)
                
                # Skip .git directory to preserve git history
                if item == ".git":
                    _log_util_message(logging.INFO, f"Preserving .git directory during cleanup: {item_path}")
                    continue
                    
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

        # Create a temporary DB with only file_system data for dehydration
        temp_db = {
            "workspace_root": current_common_dir,
            "cwd": current_common_dir,
            "file_system": DB.get("file_system", {})
        }

        # Use SAFE dehydrate function with clean file_system-only data
        # This handles all the complexity of writing files correctly AND preserves git safely
        dehydrate_db_to_directory(temp_db, current_common_dir)

        # CRITICAL: Ensure the main DB workspace_root and cwd remain aligned with common_directory
        # The dehydrate function might have modified temp_db, but we need main DB to stay consistent
        DB["workspace_root"] = current_common_dir
        DB["cwd"] = current_common_dir

        # Verify alignment
        if DB.get("workspace_root") != current_common_dir:
            raise RuntimeError(
                f"After dehydration, workspace_root is {DB.get('workspace_root')} instead of {current_common_dir}"
            )
        if DB.get("cwd") != current_common_dir:
            raise RuntimeError(
                f"After dehydration, cwd is {DB.get('cwd')} instead of {current_common_dir}"
            )

        logger.info(f"File system safely dehydrated to common directory: {current_common_dir}")
        logger.info(f"Workspace_root and cwd maintained alignment with common directory")
        logger.info(f"Git repository preserved safely during dehydration")

    except Exception as e:
        raise RuntimeError(
            f"Failed to dehydrate file system to common directory '{current_common_dir}': {e}"
        ) from e


def with_common_file_system(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to ensure file system operations use common directory."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        if not ENABLE_COMMON_FILE_SYSTEM:
            return func(*args, **kwargs)
        if not COMMON_DIRECTORY:
            raise ValueError("Common directory not set. Call update_common_directory first.")
        if not os.path.exists(COMMON_DIRECTORY):
            raise FileNotFoundError(f"Common directory not found: {COMMON_DIRECTORY}")
            
        try:
            # Always hydrate before executing
            hydrate_db_from_directory(DB, COMMON_DIRECTORY)
            result = func(*args, **kwargs)
            # Always dehydrate after executing
            dehydrate_db_to_directory(DB, COMMON_DIRECTORY)
            return result
        except Exception as e:
            try:
                # Attempt to dehydrate even on error
                dehydrate_db_to_directory(DB, COMMON_DIRECTORY)
            except Exception as de:
                _log_util_message(logging.ERROR, f"Failed to dehydrate after error: {de}")
            raise e
    return wrapper

# --- Configuration for File Handling (Hydration) ---
MAX_FILE_SIZE_TO_LOAD_CONTENT_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_TO_LOAD_CONTENT_MB * 1024 * 1024
BINARY_CONTENT_PLACEHOLDER = ["<Binary File - Content Not Loaded>"]
LARGE_FILE_CONTENT_PLACEHOLDER = [
    f"<File Exceeds {MAX_FILE_SIZE_TO_LOAD_CONTENT_MB}MB - Content Not Loaded>"
]
ERROR_READING_CONTENT_PLACEHOLDER = ["<Error Reading File Content>"]

# Archive file extensions that should have their binary content preserved
# These files need to be accessible as actual binary data for archive operations
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar'}

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


def get_absolute_path(relative_or_absolute_path: str) -> str:
    return common_utils.get_absolute_path(DB, relative_or_absolute_path)


def get_current_timestamp_iso() -> str:
    """Returns the current time in ISO 8601 format, UTC (suffixed with 'Z')."""
    return common_utils.get_current_timestamp_iso()


# --- File System Utilities (DB-Only Operations) ---


def get_file_system_entry(path: str):
    return common_utils.get_file_system_entry(DB, path)


def path_exists(path: str) -> bool:
    return common_utils.path_exists(DB, path)


def is_directory(path: str) -> bool:
    return common_utils.is_directory(DB, path)


def is_file(path: str) -> bool:
    return common_utils.is_file(DB, path)


def calculate_size_bytes(content_lines: list[str]) -> int:
    return common_utils.calculate_size_bytes(content_lines)


# --- Edit Utilities ---


def _normalize_lines(line_list: list[str], ensure_trailing_newline=True) -> list[str]:
    return common_utils._normalize_lines(line_list, ensure_trailing_newline)



def _is_archive_file(filepath: str) -> bool:
    return common_utils._is_archive_file(filepath)


def is_likely_binary_file(filepath, sample_size=1024):
    return common_utils.is_likely_binary_file(filepath, sample_size)


def hydrate_db_from_directory(db_instance, directory_path):
    return common_utils.hydrate_db_from_directory(db_instance, directory_path)


def _normalize_path_for_db(path_str: str) -> str:
    return common_utils._normalize_path_for_db(path_str)


def map_temp_path_to_db_key(temp_path: str, temp_root: str, desired_logical_root: str) -> Optional[str]:
    return common_utils.map_temp_path_to_db_key(temp_path, temp_root, desired_logical_root)


# --- Dehydrate Function ---
def dehydrate_db_to_directory(db: Dict[str, Any], target_dir: str) -> bool:
    return common_utils.dehydrate_db_to_directory(db, target_dir)

# --- Update Function ---
def update_db_file_system_from_temp(
        temp_root: str,
        original_state: Dict,
        workspace_root: str,
        preserve_metadata: bool = True,
        command: str = ""
    ):
    return common_utils.update_db_file_system_from_temp(DB, temp_root, original_state, workspace_root, preserve_metadata, command)

def resolve_target_path_for_cd(current_cwd_abs: str, 
                               target_arg: str, 
                               workspace_root_abs: str,
                               file_system_view: Dict[str, Any]) -> Optional[str]:
    return common_utils.resolve_target_path_for_cd(current_cwd_abs, target_arg, workspace_root_abs, file_system_view)

def _collect_file_metadata(file_path: str) -> Dict[str, Any]:
    return common_utils._collect_file_metadata(file_path)

def _apply_file_metadata(file_path: str, metadata: Dict[str, Any], strict_mode: bool = False) -> None:
    return common_utils._apply_file_metadata(file_path, metadata, strict_mode)

def _should_update_access_time(command: str) -> bool:
    return common_utils._should_update_access_time(command)
    

def collect_pre_command_metadata_state(
    file_system: Dict[str, Any],
    exec_env_root: str,
    workspace_root: str
) -> Dict[str, Dict[str, Any]]:
    return common_utils.collect_pre_command_metadata_state(file_system, exec_env_root, workspace_root)


def collect_post_command_metadata_state(
    file_system: Dict[str, Any],
    exec_env_root: str,
    workspace_root: str
) -> Dict[str, Dict[str, Any]]:
    return common_utils.collect_post_command_metadata_state(file_system, exec_env_root, workspace_root)


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


def _extract_file_paths_from_command(command: str, workspace_root: str, current_cwd: str = None) -> set:
    return common_utils._extract_file_paths_from_command(command, workspace_root, current_cwd)


def _extract_last_unquoted_redirection_target(command: str) -> Optional[str]:
    return common_utils._extract_last_unquoted_redirection_target(command)


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
    return common_utils.detect_and_fix_tar_command(command, execution_cwd)


def sync_db_file_to_sandbox(abs_path: str, create_parents: bool = True) -> dict:
    """Proxy to common_utils.sync_db_file_to_sandbox for Terminal API.

    Args:
        abs_path (str): Absolute logical file path within the workspace.
        create_parents (bool): Whether to create missing parent directories in sandbox.

    Returns:
        dict: Result with keys success, message, sandbox_path
    """
    return common_utils.sync_db_file_to_sandbox(DB, abs_path, create_parents)