from common_utils.print_log import print_log
from common_utils.utils import get_minified_data
from common_utils.terminal_filesystem_utils import find_binary_files
# terminal/SimulationEngine/db.py
import json
import datetime # Required for potentially generating default timestamps if needed

# Initial application state and file system representation.
# This dictionary serves as the in-memory database for the application.
# It is modified by API functions and can be persisted to/loaded from a file.
DB = {
  "workspace_root": "/home/user/project",
  "cwd": "/home/user/project/src", # Current working directory within the workspace
  "file_system": {
    # Each key is an absolute path within the workspace.
    # 'is_directory': Python boolean True for directories, False for files.
    # 'content_lines': List of strings for file content; empty for directories.
    # 'size_bytes': Integer size; calculated for files, 0 for directories.
    # 'last_modified': ISO 8601 timestamp string.
    "/home/user/project": {
      "path": "/home/user/project",
      "is_directory": True,
      "content_lines": [],
      "size_bytes": 0,
      "last_modified": "2025-05-06T12:24:00Z" # Example timestamp
    },
    "/home/user/project/README.md": {
      "path": "/home/user/project/README.md",
      "is_directory": False,
      "content_lines": [
        "# My Project\n",
        "\n",
        "This project does amazing things.\n"
      ],
      "size_bytes": 56, # Example size, should match content_lines
      "last_modified": "2025-05-06T12:24:10Z"
    },
    "/home/user/project/src": {
      "path": "/home/user/project/src",
      "is_directory": True,
      "content_lines": [],
      "size_bytes": 0,
      "last_modified": "2025-05-06T12:24:05Z"
    },
    "/home/user/project/src/main.py": {
      "path": "/home/user/project/src/main.py",
      "is_directory": False,
      "content_lines": [
        "import utils\n",
        "\n",
        "def main():\n",
        "    print(\"Starting application...\")\n",
        "    utils.helper_function()\n",
        "\n",
        "if __name__ == \"__main__\":\n",
        "    main()\n"
      ],
      "size_bytes": 174, # Example size
      "last_modified": "2025-05-06T12:24:45Z"
    },
    "/home/user/project/src/utils.py": {
      "path": "/home/user/project/src/utils.py",
      "is_directory": False,
      "content_lines": [
        "def helper_function():\n",
        "    print(\"Executing helper function.\")\n"
      ],
      "size_bytes": 68, # Example size
      "last_modified": "2025-05-06T12:24:00Z",
    }
  },

  # Tracks currently running background processes initiated by the application.
  # Keys are process IDs (PIDs), values are the command strings.
  "background_processes": {
    # "1": "npm run watch",
    # "2": "python -m http.server 8080"
  },

  # Counter for generating the next knowledge ID.
  "_next_knowledge_id": 2
}


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