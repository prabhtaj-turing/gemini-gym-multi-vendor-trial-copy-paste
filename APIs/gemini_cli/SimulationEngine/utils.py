from common_utils.print_log import print_log
"""Utility helpers for the gemini_cli SimulationEngine."""

import mimetypes
from typing import Dict, Any, List, Optional
import os
import re
import datetime
import shutil
import logging
import time  # Added for hydration helpers
import inspect
import stat  # For file permission constants
import subprocess
import base64  # Added for base64 encoding of binary archive content

from .db import DB
from common_utils.log_complexity import log_complexity
from functools import wraps
from .custom_errors import InvalidInputError, MetadataError, WorkspaceNotAvailableError
from .file_utils import _is_within_workspace
from common_utils import terminal_filesystem_utils as common_utils



try:
    from _stat import *
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Constants matching the TypeScript implementation
GEMINI_CONFIG_DIR = ".gemini"
DEFAULT_CONTEXT_FILENAME = "GEMINI.md"
MEMORY_SECTION_HEADER = "## Gemini Added Memories"
ENABLE_COMMON_FILE_SYSTEM = False

# Access time behavior configuration (mirrors real filesystem mount options)
ACCESS_TIME_MODE = "relatime"  # Options: "atime", "noatime", "relatime"
# - "atime": Update on every access (performance heavy, like traditional Unix)
# - "noatime": Never update access time (modern performance optimization)
# - "relatime": Update only if atime is older than mtime/ctime (modern default)

# Global variable to hold the currently configured filename
_current_gemini_md_filename = DEFAULT_CONTEXT_FILENAME

DEFAULT_IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "coverage",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

DEFAULT_IGNORE_FILE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.o",
    "*.so",
    "*.dll",
    "*.exe",
    "*.log",
    "*.tmp",
    "*.temp",
    "*.swp",
    "*.swo",
}

MAX_FILE_SIZE_TO_LOAD_CONTENT_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_TO_LOAD_CONTENT_MB * 1024 * 1024

BINARY_CONTENT_PLACEHOLDER = ["<Binary File - Content Not Loaded>"]
LARGE_FILE_CONTENT_PLACEHOLDER = [
    f"<File Exceeds {MAX_FILE_SIZE_TO_LOAD_CONTENT_MB}MB - Content Not Loaded>"
]

ERROR_READING_CONTENT_PLACEHOLDER = ["<Error Reading File Content>"]

# Archive file extensions that should have their binary content preserved
# These files need to be accessible as actual binary data for archive operations
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"}

# Maximum size for archive files to preserve binary content (smaller than general binary limit)
MAX_ARCHIVE_SIZE_MB = 10
MAX_ARCHIVE_SIZE_BYTES = MAX_ARCHIVE_SIZE_MB * 1024 * 1024

# Common file system configuration
common_directory = '/content'  # Must be set explicitly when using gemini_cli

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


def update_common_directory(new_directory: str) -> None:
    """Update the common directory path and immediately hydrate DB from it.

    Args:
        new_directory (str): The new absolute path for the common directory.

    Raises:
        InvalidInputError: If the path is not absolute, invalid, or doesn't exist.
        RuntimeError: If hydration fails after setting the directory.
    """
    global common_directory
    if not isinstance(new_directory, str) or not new_directory.strip():
        raise InvalidInputError("Common directory path must be a non-empty string")

    # NORMALIZE the path first
    normalized_directory = _normalize_path_for_db(new_directory.strip())
    
    if not os.path.isabs(normalized_directory):
        raise InvalidInputError("Common directory must be an absolute path")

    # Validate that the directory exists - don't auto-create
    if not os.path.exists(normalized_directory):
        raise InvalidInputError(f"Common directory '{normalized_directory}' does not exist")

    if not os.path.isdir(normalized_directory):
        raise InvalidInputError(f"Common directory '{normalized_directory}' is not a directory")

    # Validate that the directory is writable
    if not os.access(normalized_directory, os.W_OK):
        raise InvalidInputError(f"Common directory '{normalized_directory}' is not writable")

    # Update common directory with normalized path
    old_common_directory = common_directory
    common_directory = normalized_directory

    # CRITICAL: Update DB workspace_root and cwd to match normalized common_directory
    DB["workspace_root"] = normalized_directory
    DB["cwd"] = normalized_directory

    logger.info(f"Common directory updated from '{old_common_directory}' to: {normalized_directory}")
    logger.info(f"DB workspace_root and cwd synced to: {normalized_directory}")

    # IMMEDIATELY HYDRATE DB FROM THE NEW COMMON DIRECTORY
    try:
        logger.info(f"Immediately hydrating DB from new common directory: {normalized_directory}")
        hydrate_file_system_from_common_directory()
        logger.info("DB successfully hydrated from new common directory")
        
        # Log what was loaded
        file_system = DB.get("file_system", {})
        git_paths = [path for path in file_system.keys() if "/.git" in path or path.endswith("/.git")]
        
        if git_paths:
            logger.info(f"Loaded {len(file_system)} items including {len(git_paths)} .git paths")
        else:
            logger.info(f"Loaded {len(file_system)} items (no .git repository found)")
            
    except FileNotFoundError as e:
        # If hydration fails due to directory issues, revert the common directory
        common_directory = old_common_directory
        if old_common_directory:
            DB["workspace_root"] = old_common_directory
            DB["cwd"] = old_common_directory
        else:
            # Clear DB if no previous directory
            DB["workspace_root"] = ""
            DB["cwd"] = ""
            DB["file_system"] = {}
        
        error_msg = f"Failed to hydrate DB from new common directory '{normalized_directory}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
        
    except Exception as e:
        # For other hydration errors, also revert
        common_directory = old_common_directory
        if old_common_directory:
            DB["workspace_root"] = old_common_directory  
            DB["cwd"] = old_common_directory
        else:
            DB["workspace_root"] = ""
            DB["cwd"] = ""
            DB["file_system"] = {}
            
        error_msg = f"Failed to hydrate DB from new common directory '{normalized_directory}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


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
        hydrate_db_from_directory(DB, current_common_dir)

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
        logger.info(f"Workspace_root and cwd correctly aligned with common directory")
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
        dehydrate_db_to_directory(temp_db, current_common_dir)

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
        logger.info(f"Workspace_root and cwd maintained alignment with common directory")
        logger.info(f"Git repository preserved safely during dehydration")

    except Exception as e:
        raise RuntimeError(
            f"Failed to dehydrate file system to common directory '{current_common_dir}': {e}"
        ) from e


def with_common_file_system(func):
    """Decorator to sync file_system with common directory before/after operations.

    This decorator ensures that:
    1. Before the function executes, the DB's file_system is hydrated from the common directory
    2. The original function is executed with the current state
    3. After the function executes, the DB's file_system is dehydrated back to the common directory

    Only the 'file_system' part of the DB is synced, other data remains unchanged.

    Args:
        func: The function to wrap with common file system synchronization.

    Returns:
        The wrapped function that automatically syncs file_system with common directory.

    Raises:
        FileNotFoundError: If common directory is unavailable during hydration.
        RuntimeError: If hydration or dehydration fails.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ENABLE_COMMON_FILE_SYSTEM:
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
            _log_util_message(
                logging.ERROR,
                f"Error in common file system sync for {func.__name__}: {e}",
            )
            raise e

    # Preserve function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    # Preserve tool spec attribute if present
    try:
        wrapper.spec = getattr(func, "spec")
    except Exception:
        pass

    return wrapper


def _log_util_message(level: int, message: str, exc_info: bool = False) -> None:
    """
    Logs a message with information about the function within utils.py that called it.
    """
    log_message = message
    try:
        # Navigates up the call stack to find the frame of the function in utils.py
        # that called this _log_util_message helper.
        frame = inspect.currentframe()
        caller_frame = frame.f_back  # Frame of the direct caller within utils.py
        if caller_frame and caller_frame.f_code:
            func_name = caller_frame.f_code.co_name
            line_no = caller_frame.f_lineno
            log_message = f"{func_name}:{line_no} - {message}"
    except Exception:  # Fallback if frame inspection fails.
        pass

    # Log using the standard logging levels; default to DEBUG.
    if level == logging.ERROR:
        logger.error(log_message, exc_info=exc_info)
    elif level == logging.WARNING:
        logger.warning(log_message, exc_info=exc_info)
    elif level == logging.INFO:
        logger.info(log_message)
    else:
        logger.debug(log_message)  # Default log level is DEBUG.


def set_gemini_md_filename(new_filename: str) -> None:
    """Set the filename for the GEMINI.md context file.

    Args:
        new_filename (str): The new filename to use for the context file.
    """
    global _current_gemini_md_filename
    if new_filename and new_filename.strip():
        _current_gemini_md_filename = new_filename.strip()


def get_current_gemini_md_filename() -> str:
    """Get the current GEMINI.md filename.

    Returns:
        str: The current filename for the context file.
    """
    return _current_gemini_md_filename


def _get_home_directory() -> str:
    """Get the home directory from the workspace or use a default.

    Returns:
        str: The home directory path.
    """
    workspace_root = DB.get("workspace_root")
    if workspace_root:
        # In simulation, use the workspace root as the base for home directory
        return workspace_root
    return "/home/user"


def _get_global_memory_file_path() -> str:
    """Get the full path to the global memory file.

    Returns:
        str: The absolute path to the memory file.
    """
    home_dir = _get_home_directory()
    return os.path.join(home_dir, GEMINI_CONFIG_DIR, get_current_gemini_md_filename())


def _ensure_newline_separation(current_content: str) -> str:
    """Ensure proper newline separation before appending content.

    Args:
        current_content (str): The current content of the file.

    Returns:
        str: The appropriate separator string.
    """
    if not current_content:
        return ""
    if current_content.endswith("\n\n") or current_content.endswith("\r\n\r\n"):
        return ""
    if current_content.endswith("\n") or current_content.endswith("\r\n"):
        return "\n"
    return "\n\n"


def _persist_db_state():
    """Persist the current DB state to the default JSON file."""
    # Skip persistence during testing to avoid modifying the real database
    if _is_test_environment():
        return

    try:
        from .db import save_state, _DEFAULT_DB_PATH

        save_state(_DEFAULT_DB_PATH)
    except Exception as e:
        # Log the error but don't break the main functionality
        print_log(f"Warning: Could not persist DB state: {e}")


def _is_test_environment() -> bool:
    """Check if we're running in a test environment."""
    import sys
    import os

    # Check for common test runners
    if (
        "pytest" in sys.modules
        or "unittest" in sys.modules
        or "nose" in sys.modules
        or "nose2" in sys.modules
    ):
        return True

    # Check for test environment variables
    if (
        os.getenv("TESTING")
        or os.getenv("TEST_MODE")
        or os.getenv("PYTEST_CURRENT_TEST")
    ):
        return True

    # Check if running via pytest command
    if any("pytest" in arg or "test" in arg for arg in sys.argv):
        return True

    return False


def _is_common_file_system_enabled():
    """Check if common file system is enabled via environment variable.

    Returns True unless explicitly disabled by setting GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM to 'false'.
    """
    env_value = os.environ.get("GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM")
    if env_value is None:
        return True  # Default enabled when variable doesn't exist
    return env_value.lower() != "false"  # Disabled only when explicitly set to 'false'


def conditional_common_file_system_wrapper(func):
    """Wrapper that conditionally applies common file system based on runtime environment variable."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if _is_common_file_system_enabled():
            # Apply the common file system wrapper at runtime
            wrapped_func = with_common_file_system(func)
            return wrapped_func(*args, **kwargs)
        else:
            # Call the original function directly
            return func(*args, **kwargs)

    # Preserve function metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    # Preserve tool spec attribute if present
    try:
        wrapper.spec = getattr(func, "spec")
    except Exception:
        pass
    return wrapper


@log_complexity
def get_memories(limit: Optional[int] = None) -> Dict[str, Any]:
    """Retrieve saved memories from the memory file.

    Args:
        limit (Optional[int]): Maximum number of memories to retrieve.
                              If None, returns all memories.

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome:
            - 'success' (bool): True if the memories were retrieved successfully.
            - 'memories' (List[str]): List of retrieved memory items.
            - 'message' (str): A message describing the outcome.

    Raises:
        InvalidInputError: If limit is not a positive integer.
        WorkspaceNotAvailableError: If workspace_root is not configured.
    """
    # Validate input
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise InvalidInputError("Parameter 'limit' must be a positive integer or None.")

    # Check workspace configuration
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    try:
        memory_file_path = _get_global_memory_file_path()
        memory_storage = DB.get("memory_storage", {})

        # Check if memory file exists
        if memory_file_path not in memory_storage:
            return {
                "success": True,
                "memories": [],
                "message": "No memories found. Memory file does not exist.",
            }

        # Read the memory file
        content_lines = memory_storage[memory_file_path].get("content_lines", [])
        content = "".join(content_lines)

        # Extract memories from the content
        memories = []
        header_index = content.find(MEMORY_SECTION_HEADER)

        if header_index != -1:
            start_of_section_content = header_index + len(MEMORY_SECTION_HEADER)
            end_of_section_index = content.find("\n## ", start_of_section_content)
            if end_of_section_index == -1:
                end_of_section_index = len(content)

            section_content = content[start_of_section_content:end_of_section_index]

            # Parse memory items (lines starting with '- ')
            for line in section_content.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    memory_text = line[2:].strip()  # Remove '- ' prefix
                    if memory_text:
                        memories.append(memory_text)

        # Apply limit if specified
        if limit is not None:
            memories = memories[:limit]

        return {
            "success": True,
            "memories": memories,
            "message": f"Retrieved {len(memories)} memories.",
        }

    except Exception as error:
        error_message = f"Failed to retrieve memories: {str(error)}"
        return {"success": False, "memories": [], "message": error_message}


@log_complexity
def clear_memories() -> Dict[str, Any]:
    """Clear all saved memories by removing the memory section.

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome:
            - 'success' (bool): True if the memories were cleared successfully.
            - 'message' (str): A message describing the outcome.

    Raises:
        WorkspaceNotAvailableError: If workspace_root is not configured.
    """
    # Check workspace configuration
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    try:
        memory_file_path = _get_global_memory_file_path()
        memory_storage = DB.get("memory_storage", {})

        # Check if memory file exists
        if memory_file_path not in memory_storage:
            return {
                "success": True,
                "message": "No memories to clear. Memory file does not exist.",
            }

        # Read the memory file
        content_lines = memory_storage[memory_file_path].get("content_lines", [])
        content = "".join(content_lines)

        # Remove the memory section
        header_index = content.find(MEMORY_SECTION_HEADER)

        if header_index != -1:
            start_of_section = header_index
            end_of_section_index = content.find(
                "\n## ", header_index + len(MEMORY_SECTION_HEADER)
            )
            if end_of_section_index == -1:
                end_of_section_index = len(content)

            # Remove the entire memory section
            new_content = content[:start_of_section] + content[end_of_section_index:]
            new_content = new_content.rstrip() + "\n" if new_content.strip() else ""

            # Update the memory storage entry
            if new_content.strip():
                content_lines = new_content.splitlines(keepends=True)
                if content_lines and not content_lines[-1].endswith("\n"):
                    content_lines[-1] += "\n"

                memory_storage[memory_file_path]["content_lines"] = content_lines
                memory_storage[memory_file_path]["size_bytes"] = len(
                    new_content.encode("utf-8")
                )
                memory_storage[memory_file_path][
                    "last_modified"
                ] = "2025-01-01T00:00:00Z"
            else:
                # If file is empty, remove it
                del memory_storage[memory_file_path]

            _persist_db_state()

            return {"success": True, "message": "All memories have been cleared."}
        else:
            return {"success": True, "message": "No memories found to clear."}

    except Exception as error:
        error_message = f"Failed to clear memories: {str(error)}"
        return {"success": False, "message": error_message}


@log_complexity
def update_memory_by_content(old_fact: str, new_fact: str) -> Dict[str, Any]:
    """Update a specific memory by replacing old content with new content.

    Args:
        old_fact (str): The existing fact to replace.
        new_fact (str): The new fact to replace it with.

    Returns:
        Dict[str, Any]: A dictionary indicating the outcome:
            - 'success' (bool): True if the memory was updated successfully.
            - 'message' (str): A message describing the outcome.

    Raises:
        InvalidInputError: If either fact is empty or not a string.
        WorkspaceNotAvailableError: If workspace_root is not configured.
    """
    # Validate input
    if not isinstance(old_fact, str) or not old_fact.strip():
        raise InvalidInputError("Parameter 'old_fact' must be a non-empty string.")

    if not isinstance(new_fact, str) or not new_fact.strip():
        raise InvalidInputError("Parameter 'new_fact' must be a non-empty string.")

    # Check workspace configuration
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    try:
        memory_file_path = _get_global_memory_file_path()
        memory_storage = DB.get("memory_storage", {})

        # Check if memory file exists
        if memory_file_path not in memory_storage:
            return {
                "success": False,
                "message": "No memories found. Memory file does not exist.",
            }

        # Read the memory file
        content_lines = memory_storage[memory_file_path].get("content_lines", [])
        content = "".join(content_lines)

        # Find and replace the specific memory
        old_memory_item = f"- {old_fact.strip()}"
        new_memory_item = f"- {new_fact.strip()}"

        if old_memory_item in content:
            updated_content = content.replace(old_memory_item, new_memory_item)

            # Update the memory storage entry
            content_lines = updated_content.splitlines(keepends=True)
            if content_lines and not content_lines[-1].endswith("\n"):
                content_lines[-1] += "\n"

            memory_storage[memory_file_path]["content_lines"] = content_lines
            memory_storage[memory_file_path]["size_bytes"] = len(
                updated_content.encode("utf-8")
            )
            memory_storage[memory_file_path]["last_modified"] = "2025-01-01T00:00:00Z"

            _persist_db_state()

            return {
                "success": True,
                "message": f'Memory updated successfully: "{old_fact}" -> "{new_fact}"',
            }
        else:
            return {"success": False, "message": f'Memory not found: "{old_fact}"'}

    except Exception as error:
        error_message = f"Failed to update memory: {str(error)}"
        return {"success": False, "message": error_message}

# Shell utility functions
def validate_command_security(command: str) -> None:
    """Validate command for security issues.

    Args:
        command (str): The shell command to validate.

    Raises:
        ShellSecurityError: If the command contains security risks.
        InvalidInputError: If the command is invalid.
    """
    from .custom_errors import ShellSecurityError

    if not isinstance(command, str):
        raise InvalidInputError("Command must be a string")

    if not command.strip():
        raise InvalidInputError("Command cannot be empty")
    
    
    # Block potentially dangerous patterns from DB configuration
    shell_config = DB.get("shell_config", {})
    dangerous_patterns = shell_config.get("dangerous_patterns", [])
    
    if dangerous_patterns:
        # Normalize whitespace for better pattern matching
        command_normalized = re.sub(r"\s+", " ", command.lower().strip())

        for pattern in dangerous_patterns:
            pattern_normalized = re.sub(r"\s+", " ", pattern.lower().strip())
            if pattern_normalized in command_normalized:
                raise ShellSecurityError(f"Command contains dangerous pattern: {pattern}")


def get_command_restrictions() -> Dict[str, List[str]]:
    """Get command restrictions from database configuration.

    Returns:
        Dict[str, List[str]]: Dictionary with 'allowed' and 'blocked' command lists.
    """
    shell_config = DB.get("shell_config", {})
    return {
        "allowed": shell_config.get("allowed_commands", []),
        "blocked": shell_config.get("blocked_commands", []),
    }


def update_dangerous_patterns(patterns: List[str]) -> Dict[str, Any]:
    """Update dangerous patterns in the shell configuration.
    
    Args:
        patterns (List[str]): List of dangerous patterns to block.
                             Empty list means no patterns will be blocked.
    
    Returns:
        Dict[str, Any]: A dictionary indicating the outcome:
            - 'success' (bool): True if patterns were updated successfully.
            - 'message' (str): A message describing the outcome.
            - 'patterns' (List[str]): The updated patterns list.
    
    Raises:
        InvalidInputError: If patterns is not a list or contains invalid items.
    """
    if not isinstance(patterns, list):
        raise InvalidInputError("Parameter 'patterns' must be a list")
    
    # Validate each pattern is a string
    for i, pattern in enumerate(patterns):
        if not isinstance(pattern, str):
            raise InvalidInputError(f"Pattern at index {i} must be a string, got {type(pattern).__name__}")
        if not pattern.strip():
            raise InvalidInputError(f"Pattern at index {i} cannot be empty")
    
    try:
        # Get current shell config or create if it doesn't exist
        shell_config = DB.get("shell_config", {})
        
        # Update dangerous patterns
        shell_config["dangerous_patterns"] = patterns.copy()
        
        # Update DB
        DB["shell_config"] = shell_config
        
        _log_util_message(logging.INFO, f"Updated dangerous patterns: {patterns}")
        
        return {
            "success": True,
            "message": f"Successfully updated {len(patterns)} dangerous patterns",
            "patterns": patterns.copy()
        }
        
    except Exception as e:
        error_message = f"Failed to update dangerous patterns: {str(e)}"
        _log_util_message(logging.ERROR, error_message)
        return {
            "success": False,
            "message": error_message,
            "patterns": []
        }


def get_dangerous_patterns() -> List[str]:
    """Get current dangerous patterns from shell configuration.
    
    Returns:
        List[str]: List of currently configured dangerous patterns.
    """
    shell_config = DB.get("shell_config", {})
    return shell_config.get("dangerous_patterns", []).copy()


def setup_execution_environment(target_directory: Optional[str] = None) -> str:
    """Set up a temporary execution environment with workspace contents.

    Args:
        target_directory (Optional[str]): Target directory for execution.

    Returns:
        str: Path to the temporary execution environment.

    Raises:
        WorkspaceNotAvailableError: If workspace setup fails.
    """
    import tempfile
    import shutil

    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="gemini_shell_")

    try:
        # Copy workspace contents to temp directory
        file_system = DB.get("file_system", {})

        for file_path, file_info in file_system.items():
            if not _is_within_workspace(file_path, workspace_root):
                continue

            relative_path = os.path.relpath(file_path, workspace_root)
            temp_file_path = os.path.join(temp_dir, relative_path)

            if file_info.get("is_directory", False):
                os.makedirs(temp_file_path, exist_ok=True)
            else:
                # Create parent directories
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

                # Write file content
                content_lines = file_info.get("content_lines", [])
                content = "".join(content_lines)

                with open(temp_file_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(content)

        return temp_dir

    except Exception as e:
        # Cleanup on failure
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise WorkspaceNotAvailableError(f"Failed to setup execution environment: {e}")


def update_workspace_from_temp(temp_dir: str) -> None:
    """Update the workspace file system from temporary execution environment.

    Args:
        temp_dir (str): Path to the temporary execution environment.

    Raises:
        WorkspaceNotAvailableError: If workspace update fails.
    """
    import time

    workspace_root = DB.get("workspace_root", "")
    if not workspace_root:
        raise WorkspaceNotAvailableError("workspace_root not configured in DB")

    file_system = DB.setdefault("file_system", {})

    try:
        # Walk through temp directory and update file system
        for root, dirs, files in os.walk(temp_dir):
            for name in dirs + files:
                temp_path = os.path.join(root, name)
                relative_path = os.path.relpath(temp_path, temp_dir)

                # Convert back to absolute workspace path
                workspace_path = os.path.normpath(
                    os.path.join(workspace_root, relative_path)
                )

                # Only update files within workspace
                if not _is_within_workspace(workspace_path, workspace_root):
                    continue

                if os.path.isdir(temp_path):
                    file_system[workspace_path] = {
                        "path": workspace_path,
                        "is_directory": True,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                else:
                    try:
                        with open(
                            temp_path, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()

                        content_lines = [line + "\n" for line in content.splitlines()]
                        if content and not content.endswith("\n"):
                            content_lines[-1] = content_lines[-1].rstrip("\n")

                        file_system[workspace_path] = {
                            "path": workspace_path,
                            "is_directory": False,
                            "content_lines": content_lines,
                            "size_bytes": len(content.encode("utf-8")),
                            "last_modified": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }

                    except Exception as e:
                        # Log the error but continue with other files
                        print_log(f"Warning: Could not update file {workspace_path}: {e}")
                        continue

        # Persist the updated state
        _persist_db_state()

    except Exception as e:
        raise WorkspaceNotAvailableError(
            f"Failed to update workspace from temp directory: {e}"
        )


# Environment functions are now in env_manager.py


def get_shell_command(command: str) -> List[str]:
    """Get the appropriate shell command based on platform."""
    import platform

    if platform.system() == "Windows":
        return ["cmd.exe", "/c", command]
    else:
        return ["bash", "-c", command]


# ---------------------------------------------------------------------------
# Workspace ↔️ DB Hydration Helpers (mirrors terminal implementation)
# ---------------------------------------------------------------------------


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
    return common_utils._collect_file_metadata(file_path)


def _apply_file_metadata(
    file_path: str, metadata: Dict[str, Any], strict_mode: bool = False
) -> None:
    """Helper function to apply file metadata.

    Args:
        file_path (str): Path to the file to apply metadata to
        metadata (Dict[str, Any]): Metadata to apply
        strict_mode (bool): Whether to raise errors on metadata application failures
    """
    return common_utils._apply_file_metadata(file_path, metadata, strict_mode)


def get_current_timestamp_iso() -> str:
    """Returns the current time in ISO 8601 format, UTC (suffixed with 'Z')."""
    return common_utils.get_current_timestamp_iso()

def get_file_system_entry(path: str):
    """
    Retrieves a file or directory metadata entry from the in-memory 'DB["file_system"]'.
    The provided path is resolved to an absolute, normalized path before lookup.
    Returns the entry dict or None if not found or if path is invalid.
    """
    return common_utils.get_file_system_entry(DB, path)

def path_exists(path: str) -> bool:
    """
    Checks if a path exists as an entry in the in-memory 'DB["file_system"]'.
    The path is resolved to an absolute path before checking.
    """
    return common_utils.path_exists(DB, path)

def _is_archive_file(filepath: str) -> bool:
    """
    Check if a file is an archive that should have its binary content preserved.

    Args:
        filepath (str): Path to the file

    Returns:
        bool: True if the file is an archive that should preserve binary content
    """
    return common_utils._is_archive_file(filepath)


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
    return common_utils.is_likely_binary_file(filepath, sample_size)


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
    return common_utils.hydrate_db_from_directory(db_instance, directory_path)


def _normalize_path_for_db(path_str: str) -> str:
    return common_utils._normalize_path_for_db(path_str)


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


def map_temp_path_to_db_key(
    temp_path: str, temp_root: str, desired_logical_root: str
) -> Optional[str]:
    # Normalize physical temporary paths
    return common_utils.map_temp_path_to_db_key(temp_path, temp_root, desired_logical_root)


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
    return common_utils.dehydrate_db_to_directory(db, target_dir)


def _should_update_access_time(command: str) -> bool:
    """
    Determine if a command should update access time based on realistic filesystem behavior.

    Args:
        command: The command being executed

    Returns:
        bool: True if the command should update access time
    """
    return common_utils._should_update_access_time(command)


def collect_pre_command_metadata_state(
    file_system: Dict[str, Any],
    exec_env_root: str,
    workspace_root: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Collect file metadata state from the PHYSICAL SANDBOX before command execution.
    """
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
    """
    Collect file metadata state from the PHYSICAL SANDBOX after command execution.
    """
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
    """
    Preserve original change_time for files that didn't actually change during command execution.
    
    Args:
        db_file_system: The current DB file system state to update
        pre_command_state: File metadata state before command execution
        post_command_state: File metadata state after command execution  
        original_filesystem_state: The original workspace state before command
        current_workspace_root_norm: Normalized workspace root path
        exec_env_root: Execution environment root path
    """
    return common_utils.preserve_unchanged_change_times(
        db_file_system,
        pre_command_state,
        post_command_state,
        original_filesystem_state,
        current_workspace_root_norm,
        exec_env_root
    )


def calculate_size_bytes(content_lines: list[str]) -> int:
    """
    Calculate the size in bytes for a list of content lines.
    
    Args:
        content_lines: List of content lines
        
    Returns:
        int: Size in bytes
    """
    return common_utils.calculate_size_bytes(content_lines)


def _extract_file_paths_from_command(
    command: str, workspace_root: str, current_cwd: str = None
) -> set:
    """
    Extract file paths that might be accessed by the command.

    Args:
        command: The command string
        workspace_root: The workspace root path
        current_cwd: The current working directory (optional, defaults to workspace_root)

    Returns:
        set: Set of absolute file paths that might be accessed by the command
    """
    return common_utils._extract_file_paths_from_command(command, workspace_root, current_cwd)


def _extract_last_unquoted_redirection_target(command: str) -> Optional[str]:
    """
    Extract the last unquoted redirection target from a command.
    
    Args:
        command: The command string to analyze
        
    Returns:
        Optional[str]: The redirection target filename if found, None otherwise
    """
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


def resolve_target_path_for_cd(
    current_cwd_abs: str,
    target_arg: str,
    workspace_root_abs: str,
    file_system_view: Dict[str, Any],
) -> Optional[str]:
    """
    Resolves and validates a target path for 'cd'.
    All input paths (current_cwd_abs, workspace_root_abs) should be absolute and normalized.
    target_arg can be relative or absolute (interpreted relative to workspace_root if starting with '/').
    """
    return common_utils.resolve_target_path_for_cd(current_cwd_abs, target_arg, workspace_root_abs, file_system_view)


# --- Update Function ---
def update_db_file_system_from_temp(
    db: Dict[str, Any],
    temp_root: str,
    original_state: Dict,
    workspace_root: str,
    preserve_metadata: bool = True,
    command: str = "",
):
    """Update function with metadata preservation and archive file support"""
    return common_utils.update_db_file_system_from_temp(db, temp_root, original_state, workspace_root, preserve_metadata, command)