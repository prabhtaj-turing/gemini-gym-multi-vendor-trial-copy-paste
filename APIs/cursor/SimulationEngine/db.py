
# cursor/SimulationEngine/db.py
import json
import logging
import os
from common_utils.print_log import print_log
from common_utils.utils import get_minified_data
import datetime # Required for potentially generating default timestamps if needed
from common_utils.terminal_filesystem_utils import find_binary_files
from .custom_errors import WorkspaceNotHydratedError
from .models import CursorDB
from pydantic import ValidationError

# Initial application state and file system representation.
# This dictionary serves as the in-memory database for the application.
# It is modified by API functions and can be persisted to/loaded from a file.
DB = {}


def save_state(filepath: str) -> None:
    """
    Persists the current state of the in-memory 'DB' to a JSON file.

    This function is typically used for saving the application's state for later retrieval,
    effectively creating a snapshot of the workspace and its contents.

    Args:
        filepath (str): The path to the file where the state should be saved.
                        The file will be overwritten if it already exists.
    """
    # In a concurrent environment, appropriate file locking mechanisms might be needed.
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(DB, f, indent=2) # Use indent for human-readable JSON output
        # print(f"Application state successfully saved to {filepath}") # Optional logging
    except IOError as e:
        # Handle potential I/O errors during file writing (e.g., permissions, disk full)
        # print(f"Error saving state to {filepath}: {e}") # Optional logging
        raise # Re-raise the exception if the caller needs to handle it


def load_state(filepath: str) -> None:
    """
    Loads the application state from a specified JSON file, replacing the
    current in-memory 'DB'.

    This is typically used at application startup to restore a previously saved state.
    If the file is not found or cannot be decoded, the existing in-memory 'DB'
    (which might be the default initial state) is preserved, and a warning is issued.

    Args:
        filepath (str): The path to the JSON file from which to load the state.
    """
    global DB # Declare intent to modify the global DB object
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            loaded_state = json.load(f)
        DB.clear() # Remove all items from the current DB
        DB.update(loaded_state) # Populate DB with the loaded state
        # print(f"Application state successfully loaded from {filepath}") # Optional logging
    except FileNotFoundError:
        # It's often acceptable to start with a default/empty state if no save file exists.
        print_log(f"Warning: State file '{filepath}' not found. Using current or default DB state.")
    except json.JSONDecodeError as e:
        # This indicates a corrupted or invalid JSON file.
        print_log(f"Error: Could not decode JSON from '{filepath}'. DB state may be invalid or outdated. Details: {e}")
    except Exception as e:
        # Catch any other unexpected errors during loading.
        print_log(f"An unexpected error occurred while loading state from '{filepath}': {e}")


def validate_workspace_hydration() -> None:
    """
    Validates that the workspace is properly hydrated before performing file-system operations.
    
    Raises:
        WorkspaceNotHydratedError: If workspace_root is empty or file_system is empty
    """
    global DB
    if not DB.get("workspace_root") or not DB.get("file_system"):
        raise WorkspaceNotHydratedError(
            "Workspace is not hydrated. Please initialize the workspace with proper "
            "workspace_root and file_system content before performing file system operations."
        )

def _validate_db_state(db_obj):
    """Validate the database state against the Pydantic model."""
    try:
        CursorDB.model_validate(db_obj)
    except ValidationError as e:
        logger = logging.getLogger(__name__)
        logger.error("Database validation failed: %s", e)
        raise


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    blacklist = [
        # $.. means "match this field recursively at any depth in the JSON"
        "$..timestamps",  # remove all "metadata" blocks
        "$..last_modified"  # remove last_modified
        # "$..size_bytes",  # remove size_bytes
    ]

    file_system = DB.get("file_system", {})
    binary_files = find_binary_files(file_system)
    # get_minified_data expects JSONPath, not Python-style dotted keys.
    # Each file path must be quoted as a key in JSONPath, e.g. file_system["/content/workspace/binary_file.bin"].content_lines[1:]
    blacklist.extend([
        f'file_system["{file}"].content_lines[1:]' for file in binary_files
    ])
    minified_data = get_minified_data(DB, blacklist)
    return minified_data


def reset_db():
    """Reset database to its initial valid, empty state."""
    global DB
    
    # Create an empty CursorDB instance with default values
    empty_db = CursorDB()
    
    # Clear the current DB and update with the empty structure
    DB.clear()
    DB.update(empty_db.model_dump())
    
    # Validate the reset state
    _validate_db_state(DB)


# Load default data if available

def load_default_data():
    """Load default database from DBs directory"""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "DBs",
        "CursorDefaultDB.json"
    )

    if os.path.exists(db_path):
        load_state(db_path)


# Initialize with default data
load_default_data()  # Commented out - call explicitly when needed
