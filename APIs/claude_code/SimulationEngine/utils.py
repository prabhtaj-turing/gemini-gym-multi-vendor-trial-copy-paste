"""Utility helpers for the claude_code SimulationEngine."""

import os
import logging
import inspect
import datetime
import shutil
from typing import Dict, Any, Callable, TypeVar, Optional
from functools import wraps
from common_utils.print_log import print_log
from common_utils import terminal_filesystem_utils as common_utils

from .db import DB
from .custom_errors import InvalidInputError
from .file_utils import _is_within_workspace


logger = logging.getLogger(__name__)

# Type variable for the decorator
T = TypeVar('T')

# Common file system configuration
COMMON_DIRECTORY = '/content'  # Default common directory
DEFAULT_WORKSPACE = os.path.expanduser('~/content/workspace')
ENABLE_COMMON_FILE_SYSTEM = False

# Common file system configuration
common_directory = '/content'  # Must be set explicitly when using claude_code

def _log_util_message(level: int, message: str, exc_info: bool = False) -> None:
    """
    Logs a message with information about the function within utils.py that called it.

    Args:
        level (int): The logging level.
        message (str): The message to log.
        exc_info (bool): Whether to include exception information.
    """
    log_message = message
    try:
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        if caller_frame and caller_frame.f_code:
            func_name = caller_frame.f_code.co_name
            line_no = caller_frame.f_lineno
            log_message = f"{func_name}:{line_no} - {message}"
    except Exception:
        pass

    if level == logging.ERROR:
        logger.error(log_message, exc_info=exc_info)
    elif level == logging.WARNING:
        logger.warning(log_message, exc_info=exc_info)
    elif level == logging.INFO:
        logger.info(log_message)
    else:
        logger.debug(log_message)

def _get_home_directory() -> str:
    """Get the home directory from the workspace or use a default."""
    workspace_root = DB.get("workspace_root")
    if workspace_root:
        return workspace_root
    return "/home/user"

def _persist_db_state():
    """Persist the current DB state to the default JSON file."""
    if _is_test_environment():
        return

    try:
        from .db import save_state, _DEFAULT_DB_PATH

        save_state(_DEFAULT_DB_PATH)
    except Exception as e:
        print_log(f"Warning: Could not persist DB state: {e}")

def _is_test_environment() -> bool:
    """Check if we're running in a test environment."""
    import sys
    import os

    if (
        "pytest" in sys.modules
        or "unittest" in sys.modules
    ):
        return True

    if (
        os.getenv("TESTING")
        or os.getenv("TEST_MODE")
        or os.getenv("PYTEST_CURRENT_TEST")
    ):
        return True

    if any("pytest" in arg or "test" in arg for arg in sys.argv):
        return True

    return False

def _normalize_path_for_db(path_str: str) -> str:
    """Normalize a path string for the DB.

    Args:
        path_str (str): The path string to normalize.

    Returns:
        str: The normalized path string.
    """

    if path_str is None:
        return None
    return os.path.normpath(path_str).replace("\\\\", "/")


def resolve_workspace_path(path: str, workspace_root: str) -> str:
    """Resolve a user-supplied path with respect to the workspace root.

    Behavior:
      - If path is exactly "/" or empty string or ".", return workspace_root.
      - If path is absolute and already within workspace_root, return it normalized.
      - If path is relative, join it with workspace_root and return normalized result.
      - Otherwise, return the input path unchanged so callers can apply their own validation.

    This updated behavior supports both relative and absolute paths like the cursor API,
    while maintaining backward compatibility for existing absolute path validation.

    Args:
        path (str): Path supplied by caller (can be relative or absolute).
        workspace_root (str): Absolute workspace root path.

    Returns:
        str: Resolved path following the rules above.

    Raises:
        InvalidInputError: If inputs are invalid types/values.
    """
    if not isinstance(path, str):
        raise InvalidInputError("'path' must be a string")
    if not isinstance(workspace_root, str) or workspace_root.strip() == "":
        raise InvalidInputError("'workspace_root' must be a non-empty string")
    if not os.path.isabs(workspace_root):
        raise InvalidInputError("'workspace_root' must be an absolute path")

    # Normalize workspace root
    workspace_root_norm = os.path.normpath(workspace_root)
    
    # Handle empty string, ".", or just "/" - all map to workspace root
    if not path or path.strip() == "" or path == "." or path == os.path.sep:
        return workspace_root_norm
    
    # Check if this is an absolute path that starts with the workspace root
    # These should be preserved as absolute paths
    if os.path.isabs(path):
        path_norm = os.path.normpath(path)
        try:
            if _is_within_workspace(path_norm, workspace_root_norm):
                return path_norm
        except Exception:
            # Fall through to treat as relative if validation fails
            pass
    
    # For all other cases (relative paths and paths with leading slashes),
    # strip leading slashes and treat as relative (like cursor does)
    path_segment = path.lstrip("/")
    if not path_segment:  # Input was only slashes (e.g., '/', '///')
        return workspace_root_norm
    
    resolved_path = os.path.normpath(os.path.join(workspace_root_norm, path_segment))
    return resolved_path


def _collect_file_metadata(file_path: str) -> Dict[str, Any]:
    """Helper function to collect file metadata for timestamp optimization.
    
    Args:
        file_path (str): Path to the file to collect metadata from
        
    Returns:
        Dict[str, Any]: Dictionary containing the file's metadata
        
    Note:
        This is a simplified version for the simulated environment.
        In real implementation, would use os.stat() to get actual file metadata.
    """
    # In simulation environment, we don't have real files, so create default metadata
    current_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    metadata = {
        "attributes": {
            "is_symlink": False,
            "is_hidden": os.path.basename(file_path).startswith('.'),
            "is_readonly": False,
            "symlink_target": None
        },
        "timestamps": {
            "access_time": current_timestamp,
            "modify_time": current_timestamp,
            "change_time": current_timestamp
        }
    }
    
    return metadata


def collect_pre_command_metadata_state(file_system: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Collect file metadata state before command execution.
    
    Args:
        file_system (Dict[str, Any]): The current file system state from DB
        
    Returns:
        Dict[str, Dict[str, Any]]: Mapping file paths to their metadata state
    """
    return {
        path: {"metadata": _collect_file_metadata(path)}
        for path, _ in file_system.items()
    }


def collect_post_command_metadata_state(file_system: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Collect file metadata state after command execution.
    
    Args:
        file_system (Dict[str, Any]): The current file system state from DB
        
    Returns:
        Dict[str, Dict[str, Any]]: Mapping file paths to their metadata state
    """
    return {
        path: {"metadata": _collect_file_metadata(path)}
        for path, _ in file_system.items()
    }


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
    
    This function prevents unnecessary timestamp updates for metadata-only commands like 'ls' or 'pwd'.
    Only files whose change_time actually changed during execution will keep their new timestamps.
    
    Args:
        db_file_system (Dict[str, Any]): The current DB file system state to update
        pre_command_state (Dict[str, Dict[str, Any]]): File metadata state before command execution
        post_command_state (Dict[str, Dict[str, Any]]): File metadata state after command execution  
        original_filesystem_state (Dict[str, Any]): The original workspace state before command
        current_workspace_root_norm (str): Normalized workspace root path
        exec_env_root (str): Execution environment root path
    """
    for path, file_info in db_file_system.items():
        # Safely construct the corresponding path inside the execution environment.
        # Use realpath/commonpath to avoid ValueError from Path.relative_to when roots differ
        try:
            real_path = os.path.realpath(path)
            real_ws_root = os.path.realpath(current_workspace_root_norm)

            # Only attempt mapping if the file is within the logical workspace root
            if os.path.commonpath([real_path, real_ws_root]) != real_ws_root:
                continue

            rel_from_ws = os.path.relpath(real_path, start=real_ws_root)
            tmp_path = _normalize_path_for_db(os.path.join(exec_env_root, rel_from_ws))
        except Exception:
            # If anything goes wrong, skip mapping for this file
            continue

        pre_change_time = pre_command_state.get(tmp_path, {}).get("metadata", {}).get("timestamps", {}).get("change_time")
        post_change_time = post_command_state.get(tmp_path, {}).get("metadata", {}).get("timestamps", {}).get("change_time")
        
        # If change_time didn't actually change during command execution, restore the original
        if pre_change_time == post_change_time:
            original_change_time = original_filesystem_state.get(path, {}).get("metadata", {}).get("timestamps", {}).get("change_time")
            if original_change_time and "metadata" in file_info and "timestamps" in file_info["metadata"]:
                file_info["metadata"]["timestamps"]["change_time"] = original_change_time


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


def update_common_directory(new_directory: Optional[str] = None) -> None:
    """Update the common directory path.
    
    Args:
        new_directory (Optional[str]): New common directory path. If None, uses default.
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
    if common_directory is None:
        raise RuntimeError(
            "No common directory has been set. Call update_common_directory() first."
        )
    return common_directory

def hydrate_file_system_from_common_directory() -> None:
    """Hydrate only file_system from the common directory, preserve workspace_root/cwd alignment.

    This function:
    1. Loads only the file system state from the common directory using existing hydrate function
    2. Ensures workspace_root and cwd remain aligned with common_directory (not contradictory)
    3. Preserves other DB data (memory_storage, tool_metrics, etc.)
    4. Removes unused background_processes if present

    Raises:
        FileNotFoundError: If the common directory doesn't exist.
        RuntimeError: For other errors during hydration.
    """
    current_common_dir = get_common_directory()
    if not os.path.exists(current_common_dir):
        raise FileNotFoundError(f"Common directory not found: {current_common_dir}")

    if not os.path.isdir(current_common_dir):
        raise FileNotFoundError(
            f"Common directory path is not a directory: {current_common_dir}"
        )

    try:
        # Store non-file-system data to preserve it
        preserved_data = {}
        for key in DB.keys():
            if key not in [
                "file_system",
                "workspace_root",
                "cwd",
                "background_processes",
            ]:
                preserved_data[key] = DB[key]

        # Use existing hydrate function to load file system
        # This will set workspace_root and cwd to common_directory automatically
        common_utils.hydrate_db_from_directory(DB, current_common_dir)

        # Verify that workspace_root and cwd are correctly set to common_directory
        if DB.get("workspace_root") != current_common_dir:
            raise RuntimeError(
                f"Hydration set workspace_root to {DB.get('workspace_root')} instead of {current_common_dir}"
            )
        if DB.get("cwd") != current_common_dir:
            raise RuntimeError(
                f"Hydration set cwd to {DB.get('cwd')} instead of {current_common_dir}"
            )

        # Restore preserved data (memory_storage, tool_metrics, etc.)
        for key, value in preserved_data.items():
            DB[key] = value

        # Remove background_processes if it exists (cleanup)
        if "background_processes" in DB:
            del DB["background_processes"]

        logger.info(f"File system hydrated from common directory: {current_common_dir}")
        logger.info("Workspace_root and cwd correctly aligned with common directory")
        logger.info(f"Preserved non-file-system data: {list(preserved_data.keys())}")

    except Exception as e:
        raise RuntimeError(
            f"Failed to hydrate file system from common directory '{current_common_dir}': {e}"
        ) from e


def dehydrate_file_system_to_common_directory() -> None:
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
        common_utils.dehydrate_db_to_directory(temp_db, current_common_dir)

        # CRITICAL: Ensure the main DB workspace_root and cwd remain aligned with common_directory
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
        logger.info("Workspace_root and cwd maintained alignment with common directory")
        logger.info("Git repository preserved safely during dehydration")

    except Exception as e:
        raise RuntimeError(
            f"Failed to dehydrate file system to common directory '{current_common_dir}': {e}"
        ) from e

def with_common_file_system(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to enable common file system integration.
    
    This is a simplified version that provides the decorator interface
    without the complex hydration/dehydration logic. It can be enhanced
    later if needed.
    
    Args:
        func: The function to wrap with common file system support
        
    Returns:
        func: The wrapped function that automatically syncs file_system with common directory.

    Raises:
        FileNotFoundError: If common directory is unavailable during hydration.
        RuntimeError: If hydration or dehydration fails.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        if not ENABLE_COMMON_FILE_SYSTEM:
            # When disabled, just call the original function
            return func(*args, **kwargs)
        
        try:
            # Hydrate file_system from common directory before operation
            _log_util_message(
                logging.DEBUG,
                f"Hydrating file_system from common directory before {func.__name__}",
            )
            hydrate_file_system_from_common_directory()

            # Execute the original function
            result = func(*args, **kwargs)

            # Dehydrate file_system to common directory after operation
            _log_util_message(
                logging.DEBUG,
                f"Dehydrating file_system to common directory after {func.__name__}",
            )
            dehydrate_file_system_to_common_directory()

            return result
        
        except FileNotFoundError as e:
            # Re-raise FileNotFoundError to skip function execution
            _log_util_message(
                logging.ERROR, f"Common directory unavailable for {func.__name__}: {e}"
            )
            raise e
        
        except Exception as e:
            # Log other errors but still re-raise
            _log_util_message(logging.ERROR, f"Error in common file system wrapper for {func.__name__}: {e}")
            raise e
        
    # Preserve function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__

    return wrapper